use mcap_ops_core::{
    quality::{gate, inspect_signal, GatePolicy, IssueCode, QualityConfig},
    sampling::{resample, Method, SampleOptions},
    selection::{Interval, IntervalSet},
    time::uniform_grid,
    Signal,
};

fn main() -> mcap_ops_core::Result<()> {
    let signal = Signal::new(vec![0, 10_000_000, 20_000_000], vec![0.0, 1.0, 2.0], 1)?;
    let report = inspect_signal(
        &signal,
        &QualityConfig {
            lower: Some(vec![-5.0]),
            upper: Some(vec![5.0]),
            max_gap_ns: 15_000_000,
            ..QualityConfig::default()
        },
    )?;
    let decision = gate(
        &report,
        &GatePolicy {
            reject_codes: vec![IssueCode::NonFinite, IssueCode::ClockReversal],
            max_flagged_fraction: 0.0,
            min_samples: 3,
        },
    )?;
    assert!(decision.passed);

    let target = uniform_grid(0, 25_000_000, 200, 1, 100)?;
    let out = resample(
        &signal,
        &target,
        SampleOptions {
            method: Method::Linear,
            max_gap_ns: 15_000_000,
            max_age_ns: 15_000_000,
            allow_future: true,
        },
    )?;
    assert_eq!(out.values, vec![0.0, 0.5, 1.0, 1.5, 2.0]);
    assert!(out.valid().iter().all(|&valid| valid));

    let selected = IntervalSet::new(vec![Interval {
        start_ns: 5_000_000,
        end_ns: 20_000_000,
    }])?;
    assert_eq!(selected.mask(&target), vec![false, true, true, true, false]);
    println!(
        "values: {:?}; selected: {:?}",
        out.values,
        selected.mask(&target)
    );
    Ok(())
}
