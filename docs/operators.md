# Operator Catalog · 0.1.0

**Language: English | [Chinese](zh/operators.md)**

[Documentation](README.md) · [Python signatures](python.md) · [Rust interfaces](rust.md)

Sources are read-only. Transformations return new results without modifying an
input MCAP or array in place. The Python column describes the actual public
surface, not every capability available in Rust.

## 1. Time and alignment

| Rust interface | Input → output | Python |
| --- | --- | --- |
| require_strict | Timestamps → strict-order validation or error | Internal validation, not separately exported |
| uniform_grid | Bounds, rational rate, point cap → half-open target grid | Same name; returns list |
| inspect_time | Original-order timestamps, gap threshold → clock/interval statistics | Available through inspect_signal.time |
| align_timestamps | Ordered source/target, tolerances → indices, offsets, validity | Same name |
| map_clock | Time, origin, offset, ppb → corrected timestamps | Rust-only |
| expand_batch_timestamps | Message times, counts, offsets → sample times | Rust-only |

## 2. Quality inspection

| Rust interface | Input → output | Python |
| --- | --- | --- |
| inspect_signal | Signal, QualityConfig → statistics and Issue evidence | Same name; NumPy inputs |

Checks include non-finite values, ranges, clock reversals/duplicates/gaps,
rate, acceleration, local Hampel spikes, and flatline candidates. Total counts
survive detail truncation. Disorder marks dynamic checks incomplete instead of
silently repairing time. Hampel's window is a radius on both sides and can
consume future samples; it is an offline quality check.

## 3. Policy and intervals

| Rust interface | Input → output | Python |
| --- | --- | --- |
| gate | QualityReport, GatePolicy → passed, reasons, flagged_fraction | Rust-only |
| IntervalSet::new | Half-open intervals → sorted/merged set | Rust-only |
| contains / mask | Time point/array → membership/mask | Rust-only |
| intersection / difference | Two sets → intersection/difference | Rust-only |
| affected_centers | Bad intervals, context lengths → affected centers | Rust-only |

## 4. Sampling and filtering

| Rust interface | Input → output | Python |
| --- | --- | --- |
| resample | Signal, target, SampleOptions → Sampled | Same name |
| history_windows | Signal, centers, nonpositive offsets → Windowed | Values are 3-D; masks remain flat |
| ema | Ordered Signal, tau seconds, gap → Filtered | Same name |
| lowpass_taps | Rate/cutoff Hz, odd tap count → normalized coefficients | Same name; returns list |
| fir | Regular signal, taps, mode, period/tolerance → Filtered | Same name; valid is a list |
| unwrap_angles | Periodic signal, period, gap → unwrapped Signal | Same name |

Sampling supports previous, nearest, linear, and SLERP. Previous is causal and
age-limited. Nearest may use future values only when allowed. Linear/SLERP require
valid bracketing support within the gap limit. There is no automatic anti-aliasing.
SLERP uses shortest-path xyzw interpolation with input norm within 0.01 of one.
Filters do not bridge unsupported gaps.

## 5. MCAP and decoding

| Rust interface | Input → output | Python |
| --- | --- | --- |
| RawReader | Path, MessageFilter, ReadLimits → original-order message iterator | Rust-only |
| inspect_mcap | Path, filter, limits, gap → channel/schema/clock/completion report | Same name |
| JsonSignalSpec::decode | JSON message and field/clock specification → samples | Through read_json_signal |
| read_signal / SignalDecoder | Path and explicit decoder → Signal | Built-in JSON path via read_json_signal |

Unknown CDR/Protobuf payloads need upstream adapters. Container readability does
not establish payload support. Only present CRCs can be checked, and early
iterator termination is not full-file validation. Source identity is checked at
EOF; callers must keep the source unchanged during reading.

## 6. Images and video

| Rust interface | Input → output | Python |
| --- | --- | --- |
| image_ops::decode | Bounded PNG/JPEG bytes → DynamicImage | Not separately exported |
| image_quality | Image bytes, limits → dimensions/exposure/luminance/Laplacian/hash | Same name |
| transform_image | Image, crop/resize/filter → new PNG bytes | Same name; returns list[int] |
| probe_video | Local video, executable, timeout → metadata | Rust-only; used by validate_video |
| validate_video | Video, executables, timeout → complete first-stream decode report | Same name |

Metrics are not learned quality judgments. Video decoding does not establish
semantic validity. FFmpeg uses argument arrays, timeout, and bounded diagnostics;
an unavailable tool is not a quality pass.

## Counting operators versus experiments

Public functions, type methods, and implementation units are different counts.
Python exports 14 processing functions. RSI covers 30 implementation units,
including interval methods, decoding, and the bridge. Ten candidates do not
create ten new operators; see the [evidence index](../RSI/evidence.md).
