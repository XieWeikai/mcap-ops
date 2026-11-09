//! Offline, centered FIR on a single complete, uniformly sampled run.
use crate::{invalid, Error, Result};

/// Output row j is centered on input position j * down / up; no delay or clock shift.
/// Taps must be an odd centered filter designed at the reduced upsampled rate.
/// Beyond either end use the line through the first and last input samples.
pub fn polyphase_fir(
    values: &[f64],
    channels: usize,
    up: u32,
    down: u32,
    taps: &[f64],
) -> Result<Vec<f64>> {
    if channels == 0
        || !values.len().is_multiple_of(channels)
        || values.len() / channels < 2
        || up == 0
        || down == 0
        || taps.is_empty()
        || taps.len().is_multiple_of(2)
        || taps.iter().chain(values).any(|v| !v.is_finite())
    {
        return Err(invalid("finite matrix with at least two rows, positive rates and finite odd-length FIR required"));
    }
    let (mut a, mut b) = (up, down);
    while b != 0 {
        (a, b) = (b, a % b);
    }
    let up = i128::from(up / a);
    let down = i128::from(down / a);
    let n = (values.len() / channels) as i128;
    let m = usize::try_from((n * up + down - 1) / down).map_err(|_| Error::Overflow)?;
    let size = m.checked_mul(channels).ok_or(Error::Overflow)?;
    let mut out = Vec::new();
    out.try_reserve_exact(size)
        .map_err(|_| invalid("output too large"))?;
    out.resize(size, 0.0);
    let half = (taps.len() / 2) as i128;
    for j in 0..m {
        let last = (j as i128 * down + half).div_euclid(up);
        let first = -(half - j as i128 * down).div_euclid(up);
        for i in first..=last {
            let h = taps[(half + j as i128 * down - i * up) as usize] * up as f64;
            for c in 0..channels {
                let x = if (0..n).contains(&i) {
                    values[i as usize * channels + c]
                } else {
                    let left = values[c];
                    let right = values[(n as usize - 1) * channels + c];
                    let slope = (right - left) / (n - 1) as f64;
                    if i < 0 {
                        left + i as f64 * slope
                    } else {
                        right + (i - n + 1) as f64 * slope
                    }
                };
                out[j * channels + c] += x * h;
            }
        }
    }
    Ok(out)
}
