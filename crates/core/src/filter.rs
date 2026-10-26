use crate::{invalid, Result, Signal};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum FilterMode {
    Causal,
    Centered,
}

#[derive(Clone, Debug)]
pub struct Filtered {
    pub signal: Signal,
    pub valid: Vec<bool>,
    pub mode: FilterMode,
    pub lookahead_samples: usize,
    pub group_delay_samples: Option<f64>,
}

/// Time-aware causal EMA. A gap or non-finite row resets the filter state.
pub fn ema(signal: &Signal, tau_seconds: f64, max_gap_ns: i64) -> Result<Filtered> {
    signal.require_ordered()?;
    if !tau_seconds.is_finite() || tau_seconds <= 0.0 || max_gap_ns < 0 {
        return Err(invalid(
            "positive finite tau and nonnegative max gap required",
        ));
    }
    let mut values = vec![f64::NAN; signal.values().len()];
    let mut valid = vec![false; signal.len()];
    let mut previous: Option<usize> = None;
    let mut cache = [(-1i128, 0.0f64); 2];
    let mut next_cache = 0;
    for (i, is_valid) in valid.iter_mut().enumerate() {
        let prior = previous.filter(|&p| {
            i128::from(signal.timestamps()[i]) - i128::from(signal.timestamps()[p])
                <= i128::from(max_gap_ns)
        });
        let weight = prior
            .map(|p| {
                let dt_ns = i128::from(signal.timestamps()[i]) - i128::from(signal.timestamps()[p]);
                if let Some(&(_, weight)) = cache.iter().find(|&&(dt, _)| dt == dt_ns) {
                    return weight;
                }
                let dt = dt_ns as f64 / 1e9;
                let weight = -(-dt / tau_seconds).exp_m1();
                cache[next_cache] = (dt_ns, weight);
                next_cache = (next_cache + 1) % 2;
                weight
            })
            .unwrap_or(1.0);
        let d = signal.channels();
        let (past, tail) = values.split_at_mut(i * d);
        let row = &mut tail[..d];
        let mut finite = true;
        match prior {
            Some(p) => {
                for ((value, &old), &current) in row
                    .iter_mut()
                    .zip(&past[p * d..(p + 1) * d])
                    .zip(signal.row(i))
                {
                    finite &= current.is_finite();
                    *value = (1.0 - weight) * old + weight * current;
                }
            }
            None => {
                row.copy_from_slice(signal.row(i));
                finite = row.iter().all(|v| v.is_finite());
            }
        }
        if !finite {
            row.fill(f64::NAN);
            previous = None;
            continue;
        }
        *is_valid = true;
        previous = Some(i);
    }
    Ok(Filtered {
        signal: Signal::new(signal.timestamps().to_vec(), values, signal.channels())?,
        valid,
        mode: FilterMode::Causal,
        lookahead_samples: 0,
        group_delay_samples: None,
    })
}

/// Windowed-sinc FIR. Cutoff and rate are in Hz, odd taps >= 3 required.
pub fn lowpass_taps(sample_rate_hz: f64, cutoff_hz: f64, taps: usize) -> Result<Vec<f64>> {
    if !sample_rate_hz.is_finite()
        || !cutoff_hz.is_finite()
        || cutoff_hz <= 0.0
        || cutoff_hz >= sample_rate_hz / 2.0
        || taps < 3
        || taps.is_multiple_of(2)
        || taps > 4095
    {
        return Err(invalid(
            "0 < cutoff < Nyquist and odd taps in [3,4095] required",
        ));
    }
    let fc = cutoff_hz / sample_rate_hz;
    if taps == 3 {
        let a = (2.0 * std::f64::consts::PI * fc).sin() / std::f64::consts::PI * (0.54 - 0.46);
        let b = 2.0 * fc;
        let sum = a + b + a;
        return Ok(vec![a / sum, b / sum, a / sum]);
    }
    let middle = (taps - 1) as f64 / 2.0;
    let mut result = vec![0.0; taps];
    let (mut sw, mut cw) = (0.0f64, 1.0f64);
    let (swd, cwd) = (2.0 * std::f64::consts::PI / (taps - 1) as f64).sin_cos();
    for i in 0..=taps / 2 {
        let n = i as f64 - middle;
        let sinc = if n == 0.0 {
            2.0 * fc
        } else {
            (2.0 * std::f64::consts::PI * fc * n).sin() / (std::f64::consts::PI * n)
        };
        let value = sinc * (0.54 - 0.46 * cw);
        result[i] = value;
        result[taps - 1 - i] = value;
        (sw, cw) = (sw * cwd + cw * swd, cw * cwd - sw * swd);
    }
    let sum: f64 = result.iter().sum();
    for value in &mut result {
        *value /= sum;
    }
    Ok(result)
}

/// FIR on a regular grid. Gaps invalidate full support; edges are not padded.
pub fn fir(
    signal: &Signal,
    taps: &[f64],
    mode: FilterMode,
    period_ns: i64,
    tolerance_ns: i64,
) -> Result<Filtered> {
    signal.require_ordered()?;
    if taps.is_empty()
        || taps.len() > 4095
        || taps.iter().any(|v| !v.is_finite())
        || period_ns <= 0
        || tolerance_ns < 0
        || tolerance_ns >= period_ns
    {
        return Err(invalid(
            "finite taps, positive period and 0 <= tolerance < period required",
        ));
    }
    if mode == FilterMode::Centered && taps.len().is_multiple_of(2) {
        return Err(invalid("centered FIR requires odd taps"));
    }
    let mut values = vec![f64::NAN; signal.values().len()];
    let mut valid = vec![false; signal.len()];
    let lookahead = if mode == FilterMode::Centered {
        taps.len() / 2
    } else {
        0
    };
    let mut supported = 0;
    for end in 0..signal.len() {
        if signal.row(end).iter().any(|v| !v.is_finite()) {
            supported = 0;
            continue;
        }
        let regular = end == 0
            || (i128::from(signal.timestamps()[end])
                - i128::from(signal.timestamps()[end - 1])
                - i128::from(period_ns))
            .abs()
                <= i128::from(tolerance_ns);
        supported = if regular { supported + 1 } else { 1 };
        if supported < taps.len() {
            continue;
        }
        let i = end - lookahead;
        for c in 0..signal.channels() {
            values[i * signal.channels() + c] = taps
                .iter()
                .enumerate()
                .map(|(k, w)| w * signal.row(end - k)[c])
                .sum::<f64>();
        }
        let row = &mut values[i * signal.channels()..(i + 1) * signal.channels()];
        valid[i] = row.iter().all(|v| v.is_finite());
        if !valid[i] {
            row.fill(f64::NAN);
        }
    }
    let symmetric = taps
        .iter()
        .zip(taps.iter().rev())
        .all(|(a, b)| (a - b).abs() <= 1e-12);
    let delay = if mode == FilterMode::Centered {
        Some(0.0)
    } else if symmetric {
        Some((taps.len() - 1) as f64 / 2.0)
    } else {
        None
    };
    Ok(Filtered {
        signal: Signal::new(signal.timestamps().to_vec(), values, signal.channels())?,
        valid,
        mode,
        lookahead_samples: lookahead,
        group_delay_samples: delay,
    })
}

/// Explicit periodic-angle unwrapping; non-finite values and gaps reset support.
pub fn unwrap_angles(signal: &Signal, period: f64, max_gap_ns: i64) -> Result<Signal> {
    signal.require_ordered()?;
    if !period.is_finite() || period <= 0.0 || max_gap_ns < 0 {
        return Err(invalid("positive period and nonnegative gap required"));
    }
    let mut values = signal.values().to_vec();
    for i in 1..signal.len() {
        if i128::from(signal.timestamps()[i]) - i128::from(signal.timestamps()[i - 1])
            > i128::from(max_gap_ns)
        {
            continue;
        }
        let d = signal.channels();
        let (past, current) = values.split_at_mut(i * d);
        for (((&a, &b), &old), output) in signal
            .row(i - 1)
            .iter()
            .zip(signal.row(i))
            .zip(&past[(i - 1) * d..])
            .zip(&mut current[..d])
        {
            if !a.is_finite() || !b.is_finite() {
                continue;
            }
            let delta = b - a;
            let adjusted = if delta.abs() < period / 2.0 {
                delta
            } else {
                let wrapped = (delta + period / 2.0).rem_euclid(period) - period / 2.0;
                if wrapped == -period / 2.0 && delta > 0.0 {
                    period / 2.0
                } else {
                    wrapped
                }
            };
            *output = old + adjusted;
        }
    }
    Signal::new(signal.timestamps().to_vec(), values, signal.channels())
}
