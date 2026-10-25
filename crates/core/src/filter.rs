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
    for (i, is_valid) in valid.iter_mut().enumerate() {
        if signal.row(i).iter().any(|v| !v.is_finite()) {
            previous = None;
            continue;
        }
        let prior = previous.filter(|&p| {
            i128::from(signal.timestamps()[i]) - i128::from(signal.timestamps()[p])
                <= i128::from(max_gap_ns)
        });
        let weight = prior
            .map(|p| {
                let dt = (i128::from(signal.timestamps()[i]) - i128::from(signal.timestamps()[p]))
                    as f64
                    / 1e9;
                -(-dt / tau_seconds).exp_m1()
            })
            .unwrap_or(1.0);
        let d = signal.channels();
        let (past, tail) = values.split_at_mut(i * d);
        let row = &mut tail[..d];
        match prior {
            Some(p) => {
                for ((value, &old), &current) in row
                    .iter_mut()
                    .zip(&past[p * d..(p + 1) * d])
                    .zip(signal.row(i))
                {
                    *value = (1.0 - weight) * old + weight * current;
                }
            }
            None => row.copy_from_slice(signal.row(i)),
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
    let middle = (taps - 1) as f64 / 2.0;
    let mut result: Vec<_> = (0..taps)
        .map(|i| {
            let n = i as f64 - middle;
            let sinc = if n == 0.0 {
                2.0 * fc
            } else {
                (2.0 * std::f64::consts::PI * fc * n).sin() / (std::f64::consts::PI * n)
            };
            sinc * (0.54 - 0.46 * (2.0 * std::f64::consts::PI * i as f64 / (taps - 1) as f64).cos())
        })
        .collect();
    let sum: f64 = result.iter().sum();
    for x in &mut result {
        *x /= sum;
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
    let mut bad_prefix = vec![0usize; signal.len() + 1];
    for i in 0..signal.len() {
        let bad_row = signal.row(i).iter().any(|v| !v.is_finite());
        bad_prefix[i + 1] = bad_prefix[i] + usize::from(bad_row);
    }
    let mut gap_prefix = vec![0usize; signal.len() + 1];
    for i in 1..signal.len() {
        let delta = i128::from(signal.timestamps()[i]) - i128::from(signal.timestamps()[i - 1]);
        gap_prefix[i + 1] = gap_prefix[i]
            + usize::from((delta - i128::from(period_ns)).abs() > i128::from(tolerance_ns));
    }
    let lookahead = if mode == FilterMode::Centered {
        taps.len() / 2
    } else {
        0
    };
    for (i, is_valid) in valid.iter_mut().enumerate() {
        let Some(end) = i.checked_add(lookahead) else {
            continue;
        };
        if end >= signal.len() || end + 1 < taps.len() {
            continue;
        }
        let start = end + 1 - taps.len();
        if bad_prefix[end + 1] != bad_prefix[start] || gap_prefix[end + 1] != gap_prefix[start + 1]
        {
            continue;
        }
        for c in 0..signal.channels() {
            let value = taps
                .iter()
                .enumerate()
                .map(|(k, w)| w * signal.row(end - k)[c])
                .sum::<f64>();
            values[i * signal.channels() + c] = value;
        }
        *is_valid = values[i * signal.channels()..(i + 1) * signal.channels()]
            .iter()
            .all(|v| v.is_finite());
        if !*is_valid {
            values[i * signal.channels()..(i + 1) * signal.channels()].fill(f64::NAN);
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
    for c in 0..signal.channels() {
        for i in 1..signal.len() {
            let (a, b) = (signal.row(i - 1)[c], signal.row(i)[c]);
            if !a.is_finite()
                || !b.is_finite()
                || i128::from(signal.timestamps()[i]) - i128::from(signal.timestamps()[i - 1])
                    > i128::from(max_gap_ns)
            {
                continue;
            }
            let delta = b - a;
            let wrapped = (delta + period / 2.0).rem_euclid(period) - period / 2.0;
            let adjusted = if wrapped == -period / 2.0 && delta > 0.0 {
                period / 2.0
            } else {
                wrapped
            };
            values[i * signal.channels() + c] = values[(i - 1) * signal.channels() + c] + adjusted;
        }
    }
    Signal::new(signal.timestamps().to_vec(), values, signal.channels())
}
