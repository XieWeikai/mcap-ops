use crate::{invalid, Error, Result, Signal};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Method {
    Previous,
    Nearest,
    Linear,
    Slerp,
}

#[derive(Clone, Copy, Debug)]
pub struct SampleOptions {
    pub method: Method,
    pub max_gap_ns: i64,
    pub max_age_ns: i64,
    pub allow_future: bool,
}
impl SampleOptions {
    fn validate(self) -> Result<()> {
        if self.max_gap_ns < 0 || self.max_age_ns < 0 {
            return Err(invalid("gap and age limits must be nonnegative"));
        }
        Ok(())
    }
}

/// Stable codes shared with Python.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
#[repr(u8)]
pub enum Status {
    Valid = 0,
    Missing = 1,
    Gap = 2,
    Stale = 3,
    NonFinite = 4,
    Future = 5,
    InvalidQuaternion = 6,
}

#[derive(Clone, Debug)]
pub struct Sampled {
    pub timestamps: Vec<i64>,
    pub values: Vec<f64>,
    pub channels: usize,
    pub status: Vec<u8>,
    pub source_left: Vec<i64>,
    pub source_right: Vec<i64>,
    pub alpha: Vec<f64>,
    pub uses_future: Vec<bool>,
}
impl Sampled {
    pub fn valid(&self) -> Vec<bool> {
        self.status
            .iter()
            .map(|&s| s == Status::Valid as u8)
            .collect()
    }
    fn empty(target: &[i64], channels: usize) -> Result<Self> {
        let size = target.len().checked_mul(channels).ok_or(Error::Overflow)?;
        Ok(Self {
            timestamps: target.to_vec(),
            values: vec![f64::NAN; size],
            channels,
            status: vec![Status::Missing as u8; target.len()],
            source_left: vec![-1; target.len()],
            source_right: vec![-1; target.len()],
            alpha: vec![f64::NAN; target.len()],
            uses_future: vec![false; target.len()],
        })
    }
}

/// Ordered target grids use a monotone cursor: O(N + M + M*channels).
pub fn resample(signal: &Signal, target: &[i64], options: SampleOptions) -> Result<Sampled> {
    options.validate()?;
    signal.require_ordered()?;
    if target.windows(2).any(|w| w[1] < w[0]) {
        return Err(invalid("target must be nondecreasing"));
    }
    if options.method == Method::Slerp && signal.channels() != 4 {
        return Err(invalid("SLERP requires four xyzw channels"));
    }
    let times = signal.timestamps();
    let mut out = Sampled::empty(target, signal.channels())?;
    let mut right = 0;
    for (i, &t) in target.iter().enumerate() {
        while right < times.len() && times[right] < t {
            right += 1;
        }
        let exact = right < times.len() && times[right] == t;
        let before = if exact {
            Some(right)
        } else {
            right.checked_sub(1)
        };
        let after = (right < times.len()).then_some(right);
        let support = if exact {
            Some((right, right, 0.0))
        } else {
            match options.method {
                Method::Previous => before.map(|j| (j, j, 0.0)),
                Method::Nearest => {
                    let chosen = match (before, after) {
                        (Some(a), Some(b)) if options.allow_future => Some(
                            if i128::from(t) - i128::from(times[a])
                                <= i128::from(times[b]) - i128::from(t)
                            {
                                a
                            } else {
                                b
                            },
                        ),
                        (Some(a), _) => Some(a),
                        (None, Some(b)) if options.allow_future => Some(b),
                        _ => None,
                    };
                    chosen.map(|j| (j, j, 0.0))
                }
                Method::Linear | Method::Slerp => before.zip(after).map(|(a, b)| {
                    let dt = (i128::from(times[b]) - i128::from(times[a])) as f64;
                    (a, b, (i128::from(t) - i128::from(times[a])) as f64 / dt)
                }),
            }
        };
        let Some((a, b, alpha)) = support else {
            continue;
        };
        let future = times[b] > t;
        let failure = if future && !options.allow_future {
            Some(Status::Future)
        } else if a != b
            && i128::from(times[b]) - i128::from(times[a]) > i128::from(options.max_gap_ns)
        {
            Some(Status::Gap)
        } else if a == b
            && (i128::from(t) - i128::from(times[a])).abs() > i128::from(options.max_age_ns)
        {
            Some(Status::Stale)
        } else {
            None
        };
        if let Some(status) = failure {
            out.status[i] = status as u8;
            continue;
        }
        let left = signal.row(a);
        let right_values = signal.row(b);
        let values = &mut out.values[i * signal.channels()..(i + 1) * signal.channels()];
        let mut all_finite = true;
        if options.method == Method::Slerp {
            if left.iter().chain(right_values).any(|v| !v.is_finite()) {
                out.status[i] = Status::NonFinite as u8;
                continue;
            }
            match slerp(left, right_values, alpha) {
                Some(value) => values.copy_from_slice(&value),
                None => {
                    out.status[i] = Status::InvalidQuaternion as u8;
                    continue;
                }
            }
            all_finite = values.iter().all(|v| v.is_finite());
        } else if a == b {
            values.copy_from_slice(left);
            all_finite = values.iter().all(|v| v.is_finite());
        } else {
            for ((value, &x), &y) in values.iter_mut().zip(left).zip(right_values) {
                *value = (1.0 - alpha) * x + alpha * y;
                all_finite &= x.is_finite() & y.is_finite() & value.is_finite();
            }
        }
        if !all_finite {
            values.fill(f64::NAN);
            out.status[i] = Status::NonFinite as u8;
            continue;
        }
        out.status[i] = Status::Valid as u8;
        out.source_left[i] = a as i64;
        out.source_right[i] = b as i64;
        out.alpha[i] = alpha;
        out.uses_future[i] = future;
    }
    Ok(out)
}

fn slerp(a: &[f64], b: &[f64], alpha: f64) -> Option<[f64; 4]> {
    let norm = |q: &[f64]| q.iter().map(|v| v * v).sum::<f64>().sqrt();
    let (na, nb) = (norm(a), norm(b));
    if (na - 1.0).abs() > 0.01 || (nb - 1.0).abs() > 0.01 {
        return None;
    }
    let mut qa = [0.0; 4];
    let mut qb = [0.0; 4];
    for j in 0..4 {
        qa[j] = a[j] / na;
        qb[j] = b[j] / nb;
    }
    let mut dot = qa.iter().zip(qb).map(|(x, y)| x * y).sum::<f64>();
    if dot < 0.0 {
        dot = -dot;
        for v in &mut qb {
            *v = -*v;
        }
    }
    let (wa, wb) = if dot > 0.9995 {
        (1.0 - alpha, alpha)
    } else {
        let theta = dot.clamp(-1.0, 1.0).acos();
        (
            ((1.0 - alpha) * theta).sin() / theta.sin(),
            (alpha * theta).sin() / theta.sin(),
        )
    };
    let mut q = [0.0; 4];
    for j in 0..4 {
        q[j] = wa * qa[j] + wb * qb[j];
    }
    let n = norm(&q);
    for v in &mut q {
        *v /= n;
    }
    Some(q)
}

#[derive(Clone, Debug)]
pub struct Windowed {
    pub centers: Vec<i64>,
    pub offsets: Vec<i64>,
    /// Flattened step-major, then window-sample-major provenance and values.
    pub samples: Sampled,
}

pub fn history_windows(
    signal: &Signal,
    centers: &[i64],
    offsets: &[i64],
    options: SampleOptions,
) -> Result<Windowed> {
    if offsets.is_empty()
        || offsets.windows(2).any(|w| w[1] <= w[0])
        || offsets.iter().any(|&t| t > 0)
    {
        return Err(invalid(
            "history offsets must be nonempty, strictly increasing and nonpositive",
        ));
    }
    crate::time::require_strict(centers)?;
    let size = centers
        .len()
        .checked_mul(offsets.len())
        .ok_or(Error::Overflow)?;
    if centers.windows(2).all(|w| {
        i128::from(w[0]) + i128::from(*offsets.last().unwrap())
            <= i128::from(w[1]) + i128::from(offsets[0])
    }) {
        let mut target = Vec::with_capacity(size);
        for &center in centers {
            for &offset in offsets {
                target.push(center.checked_add(offset).ok_or(Error::Overflow)?);
            }
        }
        return Ok(Windowed {
            centers: centers.to_vec(),
            offsets: offsets.to_vec(),
            samples: resample(signal, &target, options)?,
        });
    }
    let mut requests = Vec::with_capacity(size);
    for (i, &center) in centers.iter().enumerate() {
        for (j, &offset) in offsets.iter().enumerate() {
            requests.push((
                center.checked_add(offset).ok_or(Error::Overflow)?,
                i * offsets.len() + j,
            ));
        }
    }
    requests.sort_unstable_by_key(|&(t, index)| (t, index));
    let sorted: Vec<_> = requests.iter().map(|r| r.0).collect();
    let sampled = resample(signal, &sorted, options)?;
    let mut result = Sampled::empty(&vec![0; size], signal.channels())?;
    for (index, &(time, dest)) in requests.iter().enumerate() {
        result.timestamps[dest] = time;
        result.status[dest] = sampled.status[index];
        result.source_left[dest] = sampled.source_left[index];
        result.source_right[dest] = sampled.source_right[index];
        result.alpha[dest] = sampled.alpha[index];
        result.uses_future[dest] = sampled.uses_future[index];
        result.values[dest * signal.channels()..(dest + 1) * signal.channels()].copy_from_slice(
            &sampled.values[index * signal.channels()..(index + 1) * signal.channels()],
        );
    }
    Ok(Windowed {
        centers: centers.to_vec(),
        offsets: offsets.to_vec(),
        samples: result,
    })
}
