use crate::time::{inspect_time, TimeStats};
use crate::{invalid, Result, Signal};
use serde::{Deserialize, Serialize};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum IssueCode {
    NonFinite,
    BelowRange,
    AboveRange,
    ClockReversal,
    DuplicateTime,
    Gap,
    Rate,
    Acceleration,
    Spike,
    Flatline,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(default)]
pub struct QualityConfig {
    pub max_gap_ns: i64,
    pub lower: Option<Vec<f64>>,
    pub upper: Option<Vec<f64>>,
    pub max_rate: Option<Vec<f64>>,
    pub max_acceleration: Option<Vec<f64>>,
    pub hampel_window_ns: Option<i64>,
    pub hampel_sigma: f64,
    pub hampel_min_deviation: f64,
    pub max_hampel_samples: usize,
    pub flatline_duration_ns: Option<i64>,
    pub flatline_tolerance: f64,
    pub max_issues: usize,
}
impl Default for QualityConfig {
    fn default() -> Self {
        Self {
            max_gap_ns: i64::MAX,
            lower: None,
            upper: None,
            max_rate: None,
            max_acceleration: None,
            hampel_window_ns: None,
            hampel_sigma: 3.0,
            hampel_min_deviation: 0.0,
            max_hampel_samples: 4096,
            flatline_duration_ns: None,
            flatline_tolerance: 0.0,
            max_issues: 10_000,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Issue {
    pub code: IssueCode,
    pub channel: Option<usize>,
    pub start_index: usize,
    pub end_index_exclusive: usize,
    pub start_ns: i64,
    /// Inclusive source timestamp, not an IntervalSet endpoint.
    pub last_ns: i64,
    pub metric: Option<f64>,
    pub threshold: Option<f64>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ChannelStats {
    pub finite: usize,
    pub nonfinite: usize,
    pub min: Option<f64>,
    pub max: Option<f64>,
    pub mean: Option<f64>,
    pub std: Option<f64>,
    pub statistics_overflow: bool,
}

#[derive(Clone, Debug, Serialize)]
pub struct QualityReport {
    pub time: TimeStats,
    pub channels: Vec<ChannelStats>,
    pub issues: Vec<Issue>,
    pub total_issues: usize,
    pub issues_truncated: bool,
    pub dynamic_checks_completed: bool,
    pub flagged_sample_count: usize,
    #[serde(skip)]
    pub flagged_samples: Vec<bool>,
    #[serde(skip)]
    pub all_codes: Vec<IssueCode>,
}

fn finite(v: f64) -> Option<f64> {
    v.is_finite().then_some(v)
}

fn validate(config: &QualityConfig, channels: usize) -> Result<()> {
    if config.max_gap_ns < 0 || config.max_issues == 0 || config.max_hampel_samples < 3 {
        return Err(invalid(
            "nonnegative gap, positive issue cap and Hampel cap >= 3 required",
        ));
    }
    for array in [
        &config.lower,
        &config.upper,
        &config.max_rate,
        &config.max_acceleration,
    ]
    .into_iter()
    .flatten()
    {
        if array.len() != channels || array.iter().any(|v| !v.is_finite()) {
            return Err(invalid(
                "threshold arrays must be finite and match channels",
            ));
        }
    }
    for array in [&config.max_rate, &config.max_acceleration]
        .into_iter()
        .flatten()
    {
        if array.iter().any(|&v| v < 0.0) {
            return Err(invalid("rate thresholds must be nonnegative"));
        }
    }
    if let (Some(a), Some(b)) = (&config.lower, &config.upper) {
        if a.iter().zip(b).any(|(x, y)| x > y) {
            return Err(invalid("lower exceeds upper"));
        }
    }
    if config.hampel_window_ns.is_some_and(|v| v <= 0)
        || config.flatline_duration_ns.is_some_and(|v| v <= 0)
        || [
            config.hampel_sigma,
            config.hampel_min_deviation,
            config.flatline_tolerance,
        ]
        .iter()
        .any(|v| !v.is_finite() || *v < 0.0)
    {
        return Err(invalid(
            "windows must be positive and numeric tolerances finite/nonnegative",
        ));
    }
    Ok(())
}

fn emit(
    report: &mut QualityReport,
    signal: &Signal,
    config: &QualityConfig,
    code: IssueCode,
    channel: Option<usize>,
    span: (usize, usize),
    evidence: (Option<f64>, Option<f64>),
) {
    let (start, end) = span;
    report.total_issues += 1;
    if !report.all_codes.contains(&code) {
        report.all_codes.push(code);
    }
    report.flagged_samples[start..end].fill(true);
    if report.issues.len() < config.max_issues {
        report.issues.push(Issue {
            code,
            channel,
            start_index: start,
            end_index_exclusive: end,
            start_ns: signal.timestamps()[start],
            last_ns: signal.timestamps()[end - 1],
            metric: evidence.0.filter(|v| v.is_finite()),
            threshold: evidence.1,
        });
    }
}

/// O(ND) basic checks. Optional Hampel is bounded by max_hampel_samples per window.
pub fn inspect_signal(signal: &Signal, config: &QualityConfig) -> Result<QualityReport> {
    validate(config, signal.channels())?;
    let mut report = QualityReport {
        time: inspect_time(signal.timestamps(), config.max_gap_ns)?,
        channels: Vec::new(),
        issues: Vec::new(),
        total_issues: 0,
        issues_truncated: false,
        dynamic_checks_completed: false,
        flagged_sample_count: 0,
        flagged_samples: vec![false; signal.len()],
        all_codes: Vec::new(),
    };
    let times = signal.timestamps();
    for i in 1..signal.len() {
        let dt = i128::from(times[i]) - i128::from(times[i - 1]);
        let code = if dt < 0 {
            Some(IssueCode::ClockReversal)
        } else if dt == 0 {
            Some(IssueCode::DuplicateTime)
        } else if dt > i128::from(config.max_gap_ns) {
            Some(IssueCode::Gap)
        } else {
            None
        };
        if let Some(code) = code {
            emit(
                &mut report,
                signal,
                config,
                code,
                None,
                (i - 1, i + 1),
                (Some(dt as f64), Some(config.max_gap_ns as f64)),
            );
        }
    }
    let ordered = report.time.reversals == 0 && report.time.duplicates == 0;
    for channel in 0..signal.channels() {
        let (mut n, mut min, mut max, mut mean, mut m2) =
            (0usize, f64::INFINITY, f64::NEG_INFINITY, 0.0, 0.0);
        for i in 0..signal.len() {
            let v = signal.row(i)[channel];
            if !v.is_finite() {
                emit(
                    &mut report,
                    signal,
                    config,
                    IssueCode::NonFinite,
                    Some(channel),
                    (i, i + 1),
                    (None, None),
                );
                continue;
            }
            n += 1;
            min = min.min(v);
            max = max.max(v);
            let delta = v - mean;
            mean += delta / n as f64;
            m2 += delta * (v - mean);
            if let Some(low) = &config.lower {
                if v < low[channel] {
                    emit(
                        &mut report,
                        signal,
                        config,
                        IssueCode::BelowRange,
                        Some(channel),
                        (i, i + 1),
                        (Some(v), Some(low[channel])),
                    );
                }
            }
            if let Some(high) = &config.upper {
                if v > high[channel] {
                    emit(
                        &mut report,
                        signal,
                        config,
                        IssueCode::AboveRange,
                        Some(channel),
                        (i, i + 1),
                        (Some(v), Some(high[channel])),
                    );
                }
            }
        }
        report.channels.push(ChannelStats {
            finite: n,
            nonfinite: signal.len() - n,
            min: (n > 0).then_some(min),
            max: (n > 0).then_some(max),
            mean: if n > 0 { finite(mean) } else { None },
            std: if n > 0 {
                finite((m2 / n as f64).max(0.0).sqrt())
            } else {
                None
            },
            statistics_overflow: n > 0 && (!mean.is_finite() || !m2.is_finite()),
        });
        if !ordered {
            continue;
        }
        if config.max_rate.is_some() || config.max_acceleration.is_some() {
            let mut previous_velocity: Option<(f64, f64)> = None;
            for i in 1..signal.len() {
                let dt_ns = i128::from(times[i]) - i128::from(times[i - 1]);
                let (a, b) = (signal.row(i - 1)[channel], signal.row(i)[channel]);
                if dt_ns > i128::from(config.max_gap_ns) || !a.is_finite() || !b.is_finite() {
                    previous_velocity = None;
                    continue;
                }
                let dt = dt_ns as f64 / 1e9;
                let velocity = (b - a) / dt;
                if let Some(limits) = &config.max_rate {
                    if velocity.abs() > limits[channel] {
                        emit(
                            &mut report,
                            signal,
                            config,
                            IssueCode::Rate,
                            Some(channel),
                            (i - 1, i + 1),
                            (finite(velocity.abs()), Some(limits[channel])),
                        );
                    }
                }
                if let (Some((prior, prior_dt)), Some(limits)) =
                    (previous_velocity, &config.max_acceleration)
                {
                    let acceleration = (velocity - prior) / ((prior_dt + dt) / 2.0);
                    if acceleration.abs() > limits[channel] {
                        emit(
                            &mut report,
                            signal,
                            config,
                            IssueCode::Acceleration,
                            Some(channel),
                            (i - 2, i + 1),
                            (finite(acceleration.abs()), Some(limits[channel])),
                        );
                    }
                }
                previous_velocity = velocity.is_finite().then_some((velocity, dt));
            }
        }
        if let Some(window) = config.hampel_window_ns {
            let mut start = 0;
            let mut values: Vec<f64> = Vec::new();
            while start < signal.len() {
                let mut end = start + 1;
                while end < signal.len()
                    && i128::from(times[end]) - i128::from(times[end - 1])
                        <= i128::from(config.max_gap_ns)
                {
                    end += 1;
                }
                values.clear();
                let (mut loaded_a, mut loaded_b) = (start, start);
                for i in start..end {
                    let value = signal.row(i)[channel];
                    if !value.is_finite() {
                        continue;
                    }
                    let low = i128::from(times[i]) - i128::from(window);
                    let high = i128::from(times[i]) + i128::from(window);
                    let a = start + times[start..end].partition_point(|&t| i128::from(t) < low);
                    let b = start + times[start..end].partition_point(|&t| i128::from(t) <= high);
                    if b - a > config.max_hampel_samples {
                        return Err(invalid("Hampel window exceeds max_hampel_samples"));
                    }
                    for j in loaded_a..a.min(loaded_b) {
                        let old = signal.row(j)[channel];
                        if old.is_finite() {
                            let index = values
                                .binary_search_by(|v| v.total_cmp(&old))
                                .expect("tracked finite sample");
                            values.remove(index);
                        }
                    }
                    for j in loaded_b.max(a)..b {
                        let value = signal.row(j)[channel];
                        if value.is_finite() {
                            let index = values.partition_point(|v| v.total_cmp(&value).is_lt());
                            values.insert(index, value);
                        }
                    }
                    loaded_a = a;
                    loaded_b = b;
                    if values.len() < 3 {
                        continue;
                    }
                    let center = median(&mut values);
                    let threshold = (config.hampel_sigma * 1.4826 * sorted_mad(&values, center))
                        .max(config.hampel_min_deviation);
                    if (value - center).abs() > threshold {
                        emit(
                            &mut report,
                            signal,
                            config,
                            IssueCode::Spike,
                            Some(channel),
                            (i, i + 1),
                            (finite((value - center).abs()), finite(threshold)),
                        );
                    }
                }
                start = end;
            }
        }
        if let Some(duration) = config.flatline_duration_ns {
            let mut start = 0;
            while start < signal.len() {
                if !signal.row(start)[channel].is_finite() {
                    start += 1;
                    continue;
                }
                let (mut low, mut high) = (signal.row(start)[channel], signal.row(start)[channel]);
                let mut end = start + 1;
                while end < signal.len() {
                    let v = signal.row(end)[channel];
                    if !v.is_finite()
                        || i128::from(times[end]) - i128::from(times[end - 1])
                            > i128::from(config.max_gap_ns)
                    {
                        break;
                    }
                    let (next_low, next_high) = (low.min(v), high.max(v));
                    if next_high - next_low > config.flatline_tolerance {
                        break;
                    }
                    low = next_low;
                    high = next_high;
                    end += 1;
                }
                let elapsed = i128::from(times[end - 1]) - i128::from(times[start]);
                if end - start >= 2 && elapsed >= i128::from(duration) {
                    emit(
                        &mut report,
                        signal,
                        config,
                        IssueCode::Flatline,
                        Some(channel),
                        (start, end),
                        (Some(elapsed as f64), Some(duration as f64)),
                    );
                }
                start = end;
            }
        }
    }
    report.dynamic_checks_completed = ordered;
    report.issues_truncated = report.total_issues > report.issues.len();
    report.flagged_sample_count = report.flagged_samples.iter().filter(|&&v| v).count();
    Ok(report)
}

fn median(values: &mut [f64]) -> f64 {
    values.sort_unstable_by(f64::total_cmp);
    let n = values.len();
    if n.is_multiple_of(2) {
        values[n / 2 - 1] / 2.0 + values[n / 2] / 2.0
    } else {
        values[n / 2]
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GatePolicy {
    pub reject_codes: Vec<IssueCode>,
    pub max_flagged_fraction: f64,
    pub min_samples: usize,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct GateDecision {
    pub passed: bool,
    pub reasons: Vec<String>,
    pub flagged_fraction: f64,
}
pub fn gate(report: &QualityReport, policy: &GatePolicy) -> Result<GateDecision> {
    if !policy.max_flagged_fraction.is_finite()
        || !(0.0..=1.0).contains(&policy.max_flagged_fraction)
    {
        return Err(invalid("max_flagged_fraction must be in [0,1]"));
    }
    let fraction = if report.time.samples == 0 {
        0.0
    } else {
        report.flagged_sample_count as f64 / report.time.samples as f64
    };
    if report.time.samples >= policy.min_samples
        && fraction <= policy.max_flagged_fraction
        && policy
            .reject_codes
            .iter()
            .all(|code| !report.all_codes.contains(code))
    {
        return Ok(GateDecision {
            passed: true,
            reasons: Vec::new(),
            flagged_fraction: fraction,
        });
    }
    let mut reasons = Vec::new();
    if report.time.samples < policy.min_samples {
        reasons.push("too_few_samples".into());
    }
    if fraction > policy.max_flagged_fraction {
        reasons.push("flagged_fraction".into());
    }
    for code in &policy.reject_codes {
        if report.all_codes.contains(code) {
            reasons.push(
                match code {
                    IssueCode::NonFinite => "NonFinite",
                    IssueCode::BelowRange => "BelowRange",
                    IssueCode::AboveRange => "AboveRange",
                    IssueCode::ClockReversal => "ClockReversal",
                    IssueCode::DuplicateTime => "DuplicateTime",
                    IssueCode::Gap => "Gap",
                    IssueCode::Rate => "Rate",
                    IssueCode::Acceleration => "Acceleration",
                    IssueCode::Spike => "Spike",
                    IssueCode::Flatline => "Flatline",
                }
                .to_owned(),
            );
        }
    }
    Ok(GateDecision {
        passed: reasons.is_empty(),
        reasons,
        flagged_fraction: fraction,
    })
}

// median() has already sorted the finite values. Absolute deviations are two
// monotone sequences on either side of center; merge only through their median.
fn sorted_mad(sorted: &[f64], center: f64) -> f64 {
    let split = sorted.partition_point(|&v| v <= center);
    let left = |i: usize| (sorted[split - 1 - i] - center).abs();
    let right = |i: usize| (sorted[split + i] - center).abs();
    let kth = |k: usize| {
        let (mut low, mut high) = (
            (k + 1).saturating_sub(sorted.len() - split),
            (k + 1).min(split),
        );
        loop {
            let i = low + (high - low) / 2;
            let j = k + 1 - i;
            let al = if i > 0 {
                left(i - 1)
            } else {
                f64::NEG_INFINITY
            };
            let ar = if i < split { left(i) } else { f64::INFINITY };
            let bl = if j > 0 {
                right(j - 1)
            } else {
                f64::NEG_INFINITY
            };
            let br = if j < sorted.len() - split {
                right(j)
            } else {
                f64::INFINITY
            };
            if al > br {
                high = i - 1;
            } else if bl > ar {
                low = i + 1;
            } else {
                return al.max(bl);
            }
        }
    };
    let n = sorted.len();
    if n.is_multiple_of(2) {
        kth(n / 2 - 1) / 2.0 + kth(n / 2) / 2.0
    } else {
        kth(n / 2)
    }
}
