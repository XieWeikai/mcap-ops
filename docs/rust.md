# Rust Interfaces and Extensions

**Language: English | [Chinese](zh/rust.md)**

[Documentation](README.md) · [Installation](getting-started.md) · [Contracts](concepts.md)

## Use core directly

The complete asserted example is [quality_pipeline.rs](../crates/core/examples/quality_pipeline.rs).
Run in the repository root of the configured execution environment:

```bash
cargo run --locked --release -p mcap-ops-core --example quality_pipeline
```

```rust
use mcap_ops_core::{Signal, sampling::{resample, Method, SampleOptions}};

fn main() -> mcap_ops_core::Result<()> {
    let input = Signal::new(vec![0, 10], vec![0.0, 1.0], 1)?;
    let output = resample(&input, &[5], SampleOptions {
        method: Method::Linear,
        max_gap_ns: 10,
        max_age_ns: 10,
        allow_future: true,
    })?;
    assert_eq!(output.values, vec![0.5]);
    assert_eq!(output.source_left, vec![0]);
    Ok(())
}
```

The small timestamps are still nanoseconds; do not mix milliseconds or seconds.

## Core modules

| Module | Public types and functions |
| --- | --- |
| crate root | Signal, SignalSpec, SignalKind, Error, Result<T> |
| time | require_strict, uniform_grid, map_clock, inspect_time, align_timestamps, expand_batch_timestamps, TimeStats, TimeAlignment |
| quality | QualityConfig, QualityReport, Issue, IssueCode, ChannelStats, inspect_signal, GatePolicy, GateDecision, gate |
| sampling | Method, SampleOptions, Status, Sampled, Windowed, resample, history_windows |
| selection | Interval, IntervalSet |
| filter | FilterMode, Filtered, ema, lowpass_taps, fir, unwrap_angles |

Signal getters borrow data; into_parts() consumes it and transfers
`(Vec<i64>, Vec<f64>, usize)`. Rust Sampled/Windowed values and masks are flat
Vecs; interpret shape using channels, centers, and offsets.

## Explicit gating and selection

```rust
use mcap_ops_core::quality::{gate, GatePolicy, IssueCode};
use mcap_ops_core::selection::{Interval, IntervalSet};

// report comes from inspect_signal; policy is an explicit caller choice.
let decision = gate(&report, &GatePolicy {
    reject_codes: vec![IssueCode::NonFinite, IssueCode::ClockReversal],
    max_flagged_fraction: 0.01,
    min_samples: 100,
})?;

let keep = IntervalSet::new(vec![Interval { start_ns: 0, end_ns: 1_000_000_000 }])?;
let bad = IntervalSet::new(vec![Interval { start_ns: 200_000_000, end_ns: 300_000_000 }])?;
let clean = keep.difference(&bad);
let selected = clean.mask(&target_times);
```

This fragment expects caller-provided report and target_times. new() merges
overlapping/adjacent intervals; intersection/difference return new sets; mask
also accepts unordered times. affected_centers(history_ns,future_ns) expands
bad intervals to centers whose context touches them. Issue.last_ns is inclusive,
so converting it into a half-open interval requires an explicit discrete-sample
coverage policy and overflow handling.

## IO and decoders

```rust
use mcap_ops_io::mcap_ops::{RawReader, MessageFilter, ReadLimits};

for message in RawReader::open("example.mcap", MessageFilter::default(), ReadLimits::default())? {
    let message = message?;
    println!("{} {}", message.channel.topic, message.log_time);
}
```

RawReader preserves file order. Breaking early does not validate the whole file;
CRC/EOF/source-identity checks require their corresponding read stages. Do not
modify or truncate a source while reading it.

The decoder boundary is:

```rust
pub trait SignalDecoder {
    fn channels(&self) -> usize;
    fn decode(&self, message: &mcap::Message<'_>)
        -> mcap_ops_io::Result<Vec<mcap_ops_io::mcap_ops::DecodedSample>>;
}
```

Adapters match topic/schema, decode fields, define clock and units, expand
batched samples, and return the declared channel count. Unrelated messages
return an empty Vec; malformed relevant messages return an error, not a silent
skip. Custom adapters referring directly to mcap types need a compatible
`mcap = "0.26"` dependency.

Call `read_signal(path, filter, limits, &decoder, max_samples)` to collect a
Signal. Built-in JsonSignalSpec contains topic, fields, channels,
timestamp_pointer, and publish_clock. CDR/Protobuf adapters are not built in.
If upstream already has arrays, bypass IO entirely.

## Generated API docs and errors

Run in the execution environment:

```bash
cargo doc --locked --workspace --no-deps
```

Output is under target/doc. Core errors are Invalid(String) and Overflow.
IO retains IO/MCAP/core/JSON/image errors and adds Invalid. Propagate failures
with `?`; a benchmark must measure successful work, not an early Err path.

When extending an operator, update callers, fixtures, public tests, Python exports
if applicable, and documentation. See [contributing](contributing.md).
