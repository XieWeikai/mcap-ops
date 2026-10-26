use crate::{invalid, Error, Result};
use serde::{Deserialize, Serialize};

pub fn require_strict(times: &[i64]) -> Result<()> {
    let bad = if times.len() < 2 {
        false
    } else {
        let mut left = times[..times.len() - 1].chunks_exact(8);
        let mut right = times[1..].chunks_exact(8);
        let mut bad = false;
        for (a, b) in left.by_ref().zip(right.by_ref()) {
            if (a[0] >= b[0])
                | (a[1] >= b[1])
                | (a[2] >= b[2])
                | (a[3] >= b[3])
                | (a[4] >= b[4])
                | (a[5] >= b[5])
                | (a[6] >= b[6])
                | (a[7] >= b[7])
            {
                bad = true;
                break;
            }
        }
        bad || left
            .remainder()
            .iter()
            .zip(right.remainder())
            .any(|(a, b)| a >= b)
    };
    if bad {
        return Err(invalid("source timestamps must be strictly increasing; inspect before resolving duplicates or reversals"));
    }
    Ok(())
}

/// Rounded rational-rate grid in [start, end), with no epoch float conversion.
pub fn uniform_grid(
    start: i64,
    end: i64,
    rate_num: u32,
    rate_den: u32,
    max_points: usize,
) -> Result<Vec<i64>> {
    if start > end || rate_num == 0 || rate_den == 0 || max_points == 0 {
        return Err(invalid(
            "ordered bounds, positive rational rate and max_points required",
        ));
    }
    let period_num = 1_000_000_000i128 * i128::from(rate_den);
    let rate = i128::from(rate_num);
    if period_num < rate {
        return Err(invalid("rate exceeds nanosecond resolution"));
    }
    let mut result = Vec::new();
    let whole = period_num / rate;
    let fraction = (period_num % rate) as u64;
    let rate = u64::from(rate_num);
    let mut residual = rate / 2;
    let mut t = i128::from(start);
    for i in 0..=max_points {
        if t >= i128::from(end) {
            return Ok(result);
        }
        if i == max_points {
            return Err(invalid("grid exceeds max_points"));
        }
        result.push(i64::try_from(t).map_err(|_| Error::Overflow)?);
        t += whole;
        residual += fraction;
        if residual >= rate {
            t += 1;
            residual -= rate;
        }
    }
    unreachable!()
}

/// Explicit ppb correction around `origin`, then offset. Never estimates clocks.
pub fn map_clock(times: &[i64], origin: i64, offset: i64, rate_ppb: i64) -> Result<Vec<i64>> {
    if rate_ppb == 0 && offset == 0 {
        return Ok(times.to_vec());
    }
    if rate_ppb == 0 {
        return times
            .iter()
            .map(|&t| t.checked_add(offset).ok_or(Error::Overflow))
            .collect();
    }
    let scale = 1_000_000_000i128 + i128::from(rate_ppb);
    if scale <= 0 {
        return Err(invalid("clock scale must be positive"));
    }
    times
        .iter()
        .map(|&t| {
            let delta = (i128::from(t) - i128::from(origin)) * scale;
            let rounded = if delta >= 0 {
                (delta + 500_000_000) / 1_000_000_000
            } else {
                -((-delta + 500_000_000) / 1_000_000_000)
            };
            i64::try_from(i128::from(origin) + rounded + i128::from(offset))
                .map_err(|_| Error::Overflow)
        })
        .collect()
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TimeStats {
    pub samples: usize,
    pub first_ns: Option<i64>,
    pub last_ns: Option<i64>,
    pub reversals: usize,
    pub duplicates: usize,
    pub gaps: usize,
    pub positive_interval_min_ns: Option<i64>,
    pub positive_interval_median_ns: Option<f64>,
    pub positive_interval_p95_ns: Option<f64>,
    pub positive_interval_max_ns: Option<i64>,
    pub estimated_hz: Option<f64>,
}

/// Inspect original order; positive-interval summaries never hide reversals.
pub fn inspect_time(times: &[i64], max_gap_ns: i64) -> Result<TimeStats> {
    if max_gap_ns < 0 {
        return Err(invalid("max_gap_ns must be nonnegative"));
    }
    if times.len() >= 2 {
        let dt = i128::from(times[1]) - i128::from(times[0]);
        if dt > 0
            && times
                .windows(2)
                .all(|w| i128::from(w[1]) - i128::from(w[0]) == dt)
        {
            let dt = i64::try_from(dt).map_err(|_| Error::Overflow)?;
            return Ok(TimeStats {
                samples: times.len(),
                first_ns: times.first().copied(),
                last_ns: times.last().copied(),
                reversals: 0,
                duplicates: 0,
                gaps: if dt > max_gap_ns { times.len() - 1 } else { 0 },
                positive_interval_min_ns: Some(dt),
                positive_interval_median_ns: Some(dt as f64),
                positive_interval_p95_ns: Some(dt as f64),
                positive_interval_max_ns: Some(dt),
                estimated_hz: Some(1e9 / dt as f64),
            });
        }
    }
    let mut positive = Vec::new();
    let (mut reversals, mut duplicates, mut gaps) = (0, 0, 0);
    for pair in times.windows(2) {
        let dt = i128::from(pair[1]) - i128::from(pair[0]);
        if dt < 0 {
            reversals += 1;
        } else if dt == 0 {
            duplicates += 1;
        } else {
            if dt > i128::from(max_gap_ns) {
                gaps += 1;
            }
            positive.push(i64::try_from(dt).map_err(|_| Error::Overflow)?);
        }
    }
    positive.sort_unstable();
    let median = quantile(&positive, 0.5);
    Ok(TimeStats {
        samples: times.len(),
        first_ns: times.first().copied(),
        last_ns: times.last().copied(),
        reversals,
        duplicates,
        gaps,
        positive_interval_min_ns: positive.first().copied(),
        positive_interval_median_ns: median,
        positive_interval_p95_ns: quantile(&positive, 0.95),
        positive_interval_max_ns: positive.last().copied(),
        estimated_hz: median.map(|dt| 1e9 / dt),
    })
}

fn quantile(sorted: &[i64], q: f64) -> Option<f64> {
    if sorted.is_empty() {
        return None;
    }
    let index = (sorted.len() - 1) as f64 * q;
    let a = index.floor() as usize;
    let b = index.ceil() as usize;
    Some(sorted[a] as f64 + (sorted[b] as f64 - sorted[a] as f64) * (index - a as f64))
}

#[derive(Clone, Debug)]
pub struct TimeAlignment {
    pub indices: Vec<i64>,
    /// Signed source minus target. Zero is only meaningful when valid=true.
    pub offsets_ns: Vec<i64>,
    pub valid: Vec<bool>,
}

pub fn align_timestamps(
    source: &[i64],
    target: &[i64],
    nearest: bool,
    max_past_ns: i64,
    max_future_ns: i64,
) -> Result<TimeAlignment> {
    require_strict(source)?;
    if max_past_ns < 0 || max_future_ns < 0 || target.windows(2).any(|w| w[1] < w[0]) {
        return Err(invalid(
            "nonnegative tolerances and ordered target required",
        ));
    }
    let mut result = TimeAlignment {
        indices: vec![-1; target.len()],
        offsets_ns: vec![0; target.len()],
        valid: vec![false; target.len()],
    };
    let mut next = 0;
    for (i, &t) in target.iter().enumerate() {
        while next < source.len() && source[next] <= t {
            next += 1;
        }
        let past = next
            .checked_sub(1)
            .filter(|&j| i128::from(t) - i128::from(source[j]) <= i128::from(max_past_ns));
        let future = (nearest && next < source.len())
            .then_some(next)
            .filter(|&j| i128::from(source[j]) - i128::from(t) <= i128::from(max_future_ns));
        let chosen = match (past, future) {
            (Some(a), Some(b)) => Some(
                if i128::from(t) - i128::from(source[a]) <= i128::from(source[b]) - i128::from(t) {
                    a
                } else {
                    b
                },
            ),
            (a, None) => a,
            (None, b) => b,
        };
        if let Some(index) = chosen {
            result.indices[i] = index as i64;
            result.offsets_ns[i] = i64::try_from(i128::from(source[index]) - i128::from(t))
                .map_err(|_| Error::Overflow)?;
            result.valid[i] = true;
        }
    }
    Ok(result)
}

/// Expand nested samples using explicit nanosecond offsets, without guessing fields.
pub fn expand_batch_timestamps(
    message_times: &[i64],
    counts: &[usize],
    offsets: &[i64],
) -> Result<Vec<i64>> {
    let count = counts
        .iter()
        .try_fold(0usize, |sum, &n| sum.checked_add(n).ok_or(Error::Overflow))?;
    if message_times.len() != counts.len() || count != offsets.len() {
        return Err(invalid("batch counts do not match timestamps and offsets"));
    }
    let mut result = offsets.to_vec();
    let mut index = 0;
    for (&time, &count) in message_times.iter().zip(counts) {
        for value in &mut result[index..index + count] {
            *value = time.checked_add(*value).ok_or(Error::Overflow)?;
        }
        index += count;
    }
    Ok(result)
}
