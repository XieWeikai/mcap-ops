# Rust Symbol Index

**Language: English | [Chinese](../zh/reference/rust.md)**

These links open rustdoc built from the same source revision as this site: exact signatures, fields, methods, trait implementations, and source. This bilingual index explains purpose; compiler-generated Rust syntax and source comments share one English reference.

[mcap-ops-core](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/index.html) · [mcap-ops-io](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/index.html)

## How to look things up

Open a type and use **Fields / Implementations / Trait Implementations**. Find Signal construction/ownership methods, IntervalSet intersection/difference/context methods, and RawReader Iterator there. Rustdoc search looks up symbols and types; fields and methods have direct anchors.

## mcap_ops_core

| Symbol | Kind | Purpose |
| --- | --- | --- |
| [Error](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/enum.Error.html) | enum | Typed validation and processing errors |
| [Result](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/type.Result.html) | type | Crate-specific result alias |
| [Signal](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/struct.Signal.html) | struct | Owned row-major numeric signal |
| [SignalSpec](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/struct.SignalSpec.html) | struct | Descriptive units, frame, clock and kind |
| [SignalKind](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/enum.SignalKind.html) | enum | Continuous, quaternion, command, discrete, event |

## mcap_ops_core::filter

| Symbol | Kind | Purpose |
| --- | --- | --- |
| [FilterMode](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/enum.FilterMode.html) | enum | Causal or centered support |
| [Filtered](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/struct.Filtered.html) | struct | Signal, mask, lookahead and group delay |
| [ema](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/fn.ema.html) | fn | Time-aware causal smoothing |
| [lowpass_taps](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/fn.lowpass_taps.html) | fn | Normalized windowed-sinc coefficients |
| [fir](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/fn.fir.html) | fn | Regular-grid finite impulse response |
| [unwrap_angles](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/filter/fn.unwrap_angles.html) | fn | Periodic values with gap resets |

## mcap_ops_core::quality

| Symbol | Kind | Purpose |
| --- | --- | --- |
| [IssueCode](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/enum.IssueCode.html) | enum | Stable quality issue categories |
| [QualityConfig](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.QualityConfig.html) | struct | Thresholds and detection resource caps |
| [Issue](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.Issue.html) | struct | Source span, metric, and threshold |
| [ChannelStats](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.ChannelStats.html) | struct | Finite-value statistics and overflow indication |
| [QualityReport](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.QualityReport.html) | struct | Bounded issue details with complete counts |
| [inspect_signal](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/fn.inspect_signal.html) | fn | Time, range, rate, spike and flatline inspection |
| [GatePolicy](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.GatePolicy.html) | struct | Explicit rejection policy |
| [GateDecision](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/struct.GateDecision.html) | struct | Pass result and rejection reasons |
| [gate](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/quality/fn.gate.html) | fn | Evaluate policy against complete evidence |

## mcap_ops_core::sampling

| Symbol | Kind | Purpose |
| --- | --- | --- |
| [Method](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/enum.Method.html) | enum | Previous, Nearest, Linear, Slerp |
| [SampleOptions](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/struct.SampleOptions.html) | struct | Method, gap, age, future permission |
| [Status](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/enum.Status.html) | enum | Stable 0-6 sample validity codes |
| [Sampled](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/struct.Sampled.html) | struct | Values with source support and status |
| [resample](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/fn.resample.html) | fn | Sample onto an ordered target timeline |
| [Windowed](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/struct.Windowed.html) | struct | Centers, offsets, and flat Sampled buffers |
| [history_windows](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/sampling/fn.history_windows.html) | fn | Sample explicit past offsets at each center |

## mcap_ops_core::selection

| Symbol | Kind | Purpose |
| --- | --- | --- |
| [Interval](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/selection/struct.Interval.html) | struct | Half-open nanosecond interval |
| [IntervalSet](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/selection/struct.IntervalSet.html) | struct | Normalized interval algebra and context expansion |

## mcap_ops_core::time

| Symbol | Kind | Purpose |
| --- | --- | --- |
| [require_strict](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.require_strict.html) | fn | Reject duplicates and clock reversals |
| [uniform_grid](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.uniform_grid.html) | fn | Rounded rational-rate grid in [start,end) |
| [map_clock](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.map_clock.html) | fn | Explicit offset and ppb scale about an origin |
| [TimeStats](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/struct.TimeStats.html) | struct | Clock quality and positive-interval statistics |
| [inspect_time](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.inspect_time.html) | fn | Original-order timing statistics |
| [TimeAlignment](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/struct.TimeAlignment.html) | struct | Indices, signed offsets, and validity |
| [align_timestamps](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.align_timestamps.html) | fn | Bounded past/nearest index matching |
| [expand_batch_timestamps](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_core/time/fn.expand_batch_timestamps.html) | fn | Expand message times using explicit sample offsets |

## mcap_ops_io

| Symbol | Kind | Purpose |
| --- | --- | --- |
| [Error](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/enum.Error.html) | enum | Typed validation and processing errors |
| [Result](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/type.Result.html) | type | Crate-specific result alias |

## mcap_ops_io::image_ops

| Symbol | Kind | Purpose |
| --- | --- | --- |
| [ImageOptions](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/struct.ImageOptions.html) | struct | Image limits and exposure thresholds |
| [decode](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/fn.decode.html) | fn | Bounded PNG/JPEG decoder |
| [ImageQuality](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/struct.ImageQuality.html) | struct | Image metrics and decoded RGB hash |
| [image_quality](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/fn.image_quality.html) | fn | Compute exposure and sharpness metrics |
| [ResizeFilter](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/enum.ResizeFilter.html) | enum | Nearest, Triangle, Lanczos3 |
| [transform_image](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/image_ops/fn.transform_image.html) | fn | Crop then resize, return encoded PNG |

## mcap_ops_io::mcap_ops

| Symbol | Kind | Purpose |
| --- | --- | --- |
| [MessageFilter](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.MessageFilter.html) | struct | Topic and MCAP-clock selection |
| [ReadLimits](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.ReadLimits.html) | struct | Record size and scanned-message caps |
| [RawReader](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.RawReader.html) | struct | Fallible original-order MCAP iterator |
| [ChannelReport](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.ChannelReport.html) | struct | Channel/schema identity and both clocks |
| [McapReport](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.McapReport.html) | struct | Complete container scan report |
| [inspect_mcap](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/fn.inspect_mcap.html) | fn | Validate and summarize a container |
| [DecodedSample](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.DecodedSample.html) | struct | Decoder output: timestamp_ns and values |
| [SignalDecoder](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/trait.SignalDecoder.html) | trait | Schema-specific payload-to-signal trait |
| [JsonSignalSpec](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/struct.JsonSignalSpec.html) | struct | Explicit RFC 6901 field decoder |
| [read_signal](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/mcap_ops/fn.read_signal.html) | fn | Collect bounded decoder output into Signal |

## mcap_ops_io::video

| Symbol | Kind | Purpose |
| --- | --- | --- |
| [probe_video](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/video/fn.probe_video.html) | fn | Read video-stream metadata with a timeout |
| [VideoValidation](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/video/struct.VideoValidation.html) | struct | Full-decode completion report |
| [validate_video](https://xieweikai.github.io/mcap-ops/rustdoc/mcap_ops_io/video/fn.validate_video.html) | fn | Probe and completely decode first video stream |

## Rust-only interfaces

`gate`, `IntervalSet`, `map_clock`, `inspect_time`, `expand_batch_timestamps`, `RawReader`, `SignalDecoder`, and standalone `probe_video` have no Python export. `map_clock` applies caller-provided parameters; it does not fit clocks.

| Interface | Inputs and output | Behavior and errors |
| --- | --- | --- |
| `require_strict` | `&[i64] -> Result<()>` | Empty/singleton input passes; duplicates or reversals return Invalid |
| `inspect_time` | times, nonnegative max_gap_ns -> `TimeStats` | Inspect original order; summarize only positive intervals, with interpolated median/p95; estimated_hz is 1e9/median; unavailable statistics are None |
| `map_clock` | times, origin, offset (ns), rate_ppb -> `Vec<i64>` | Apply `origin + round((t-origin)*(1+rate_ppb/1e9)) + offset`; scale must be positive; half ties round away from zero; checked int64 output |
| `expand_batch_timestamps` | message_times, counts, flat offsets (ns) -> `Vec<i64>` | One count per message; sum(counts) equals offsets.len(); add each message time to its offsets with checked arithmetic |
| `gate` | `&QualityReport`, `&GatePolicy` -> `GateDecision` | Reject too few samples, excess flagged fraction, or any rejected code; full internal flags survive detail truncation; fraction is 0 for empty input |
| `IntervalSet` | normalized half-open intervals -> sets / masks | See [method contracts](types.md#interval-and-intervalset); invalid spans or overflowing context expansion fail |
| `RawReader::open` | path, filter, limits -> fallible message iterator | Preserve file order and CRC/error handling; early termination does not validate EOF or the complete source |
| `read_signal` | path, filter, limits, `&dyn SignalDecoder`, max_samples -> `Signal` | Collect decoded samples within a positive cap; validate channels; retain order; malformed relevant messages or no decoded samples fail |
| `decode` | PNG/JPEG bytes, `&ImageOptions` -> `image::DynamicImage` | Check format, dimensions, pixels and allocation limits before returning a decoded image |
| `probe_video` | local path, ffprobe executable, `Duration` -> `serde_json::Value` | Require video streams and clean tool completion within a bounded timeout; no frame decoding or quality certification |

`map_clock` returns new timestamps; it does not overwrite source clocks, sort,
deduplicate, or guarantee that rounding preserves strict ordering. Store the
mapping parameters and retain original times. Batch expansion likewise does not
guess sampling frequency or enforce global ordering.

For a complete asserted quality-gate, interval-selection, and resampling example,
see [quality_pipeline.rs](../../crates/core/examples/quality_pipeline.rs).
Implementing `SignalDecoder` is explained in the [Rust extension guide](../rust.md).

[Types and contracts](types.md) · [Rust usage and extensions](../rust.md) · [Python API](index.md)
