use crate::{invalid, Error, Result};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct Interval {
    pub start_ns: i64,
    pub end_ns: i64,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize)]
pub struct IntervalSet {
    intervals: Vec<Interval>,
}
impl IntervalSet {
    pub fn new(mut intervals: Vec<Interval>) -> Result<Self> {
        if intervals.iter().any(|v| v.start_ns >= v.end_ns) {
            return Err(invalid("intervals must be nonempty [start,end)"));
        }
        if intervals.windows(2).all(|w| w[0].end_ns < w[1].start_ns) {
            return Ok(Self { intervals });
        }
        intervals.sort_unstable_by_key(|v| v.start_ns);
        intervals.dedup_by(|current, previous| {
            if current.start_ns <= previous.end_ns {
                previous.end_ns = previous.end_ns.max(current.end_ns);
                true
            } else {
                false
            }
        });
        Ok(Self { intervals })
    }
    pub fn intervals(&self) -> &[Interval] {
        &self.intervals
    }
    pub fn contains(&self, t: i64) -> bool {
        if self.intervals.first().is_none_or(|v| t < v.start_ns)
            || self.intervals.last().is_some_and(|v| t >= v.end_ns)
        {
            return false;
        }
        let i = self.intervals.partition_point(|v| v.start_ns <= t);
        i > 0 && t < self.intervals[i - 1].end_ns
    }
    pub fn mask(&self, times: &[i64]) -> Vec<bool> {
        if self.intervals.is_empty() {
            return vec![false; times.len()];
        }
        if times.windows(2).any(|w| w[1] < w[0]) {
            return times.iter().map(|&t| self.contains(t)).collect();
        }
        let mut intervals = self.intervals.iter().peekable();
        times
            .iter()
            .map(|&t| {
                while intervals.peek().is_some_and(|v| v.end_ns <= t) {
                    intervals.next();
                }
                intervals.peek().is_some_and(|v| v.start_ns <= t)
            })
            .collect()
    }
    pub fn intersection(&self, other: &Self) -> Self {
        let (mut i, mut j) = (0, 0);
        // Pay for a binary search only when the first pair is disjoint.
        if let (Some(a), Some(b)) = (self.intervals.first(), other.intervals.first()) {
            if a.end_ns <= b.start_ns {
                i = self.intervals.partition_point(|v| v.end_ns <= b.start_ns);
            } else if b.end_ns <= a.start_ns {
                j = other.intervals.partition_point(|v| v.end_ns <= a.start_ns);
            }
        }
        let mut result = Vec::new();
        while i < self.intervals.len() && j < other.intervals.len() {
            let a = self.intervals[i];
            let b = other.intervals[j];
            let (start_ns, end_ns) = (a.start_ns.max(b.start_ns), a.end_ns.min(b.end_ns));
            if start_ns < end_ns {
                result.push(Interval { start_ns, end_ns });
            }
            if a.end_ns < b.end_ns {
                i += 1;
            } else {
                j += 1;
            }
        }
        Self { intervals: result }
    }
    pub fn difference(&self, other: &Self) -> Self {
        if other.intervals.is_empty() {
            return self.clone();
        }
        let mut result = Vec::with_capacity(self.intervals.len() + other.intervals.len());
        let mut j = 0;
        for a in &self.intervals {
            while j < other.intervals.len() && other.intervals[j].end_ns <= a.start_ns {
                j += 1;
            }
            let mut cursor = a.start_ns;
            let mut k = j;
            while k < other.intervals.len() && other.intervals[k].start_ns < a.end_ns {
                let b = other.intervals[k];
                if cursor < b.start_ns {
                    result.push(Interval {
                        start_ns: cursor,
                        end_ns: b.start_ns,
                    });
                }
                cursor = cursor.max(b.end_ns);
                if cursor >= a.end_ns {
                    break;
                }
                k += 1;
            }
            if cursor < a.end_ns {
                result.push(Interval {
                    start_ns: cursor,
                    end_ns: a.end_ns,
                });
            }
            j = k;
        }
        Self { intervals: result }
    }
    /// Expand bad intervals to all target centers whose context overlaps them.
    pub fn affected_centers(&self, history_ns: i64, future_ns: i64) -> Result<Self> {
        if history_ns < 0 || future_ns < 0 {
            return Err(invalid("context lengths must be nonnegative"));
        }
        if history_ns == 0 && future_ns == 0 {
            return Ok(self.clone());
        }
        let mut merged = Vec::with_capacity(self.intervals.len());
        let mut pending: Option<Interval> = None;
        for v in &self.intervals {
            let interval = Interval {
                start_ns: v.start_ns.checked_sub(future_ns).ok_or(Error::Overflow)?,
                end_ns: v.end_ns.checked_add(history_ns).ok_or(Error::Overflow)?,
            };
            match pending.as_mut() {
                Some(last) if interval.start_ns <= last.end_ns => {
                    last.end_ns = last.end_ns.max(interval.end_ns)
                }
                _ => {
                    if let Some(last) = pending.replace(interval) {
                        merged.push(last);
                    }
                }
            }
        }
        if let Some(last) = pending {
            merged.push(last);
        }
        Ok(Self { intervals: merged })
    }
}

/// Half-open row bounds around motion relative to endpoint-window medians.
/// None means no usable motion interval. Thresholds use each input channel's units.
pub fn motion_bounds(
    signal: &crate::Signal,
    thresholds: &[f64],
    edge_ns: i64,
) -> crate::Result<Option<(usize, usize)>> {
    signal.require_ordered()?;
    if edge_ns < 0
        || thresholds.len() != signal.channels()
        || thresholds.iter().any(|&v| !v.is_finite() || v < 0.0)
        || signal.values().iter().any(|v| !v.is_finite())
    {
        return Err(crate::invalid("finite values, one finite nonnegative threshold per channel, and nonnegative edge_ns required"));
    }
    let t = signal.timestamps();
    if t.len() < 2 {
        return Ok(None);
    }
    let head = t.partition_point(|v| v.abs_diff(t[0]) <= edge_ns as u64);
    let tail = t.partition_point(|v| v.abs_diff(t[t.len() - 1]) > edge_ns as u64);
    let medians = |range: std::ops::Range<usize>| -> Vec<f64> {
        (0..signal.channels())
            .map(|c| {
                let mut x: Vec<_> = range.clone().map(|i| signal.row(i)[c]).collect();
                x.sort_unstable_by(f64::total_cmp);
                let m = x.len() / 2;
                if x.len() % 2 == 0 {
                    (x[m - 1] + x[m]) * 0.5
                } else {
                    x[m]
                }
            })
            .collect()
    };
    let first = medians(0..head);
    let last = medians(tail..t.len());
    let differs = |row: &[f64], reference: &[f64]| {
        row.iter()
            .zip(reference)
            .zip(thresholds)
            .any(|((&x, &y), &limit)| (x - y).abs() > limit)
    };
    let a = (0..t.len()).find(|&i| differs(signal.row(i), &first));
    let b = (0..t.len()).rfind(|&i| differs(signal.row(i), &last));
    Ok(a.zip(b).and_then(|(a, b)| {
        let bounds = (a.saturating_sub(1), (b + 2).min(t.len()));
        (bounds.1.saturating_sub(bounds.0) >= 2).then_some(bounds)
    }))
}
