# Python API · 0.1.0

**Language: English | [Chinese](zh/python.md)**

[Documentation](README.md) · [Installation](getting-started.md) · [Runnable example](../examples/quickstart.py)

Import `mcap_ops as ops`. This reference follows the actual
[wrapper](../python/mcap_ops/__init__.py) and [bindings](../crates/python/src/lib.rs).
Do not depend on private `_native` entry points.

## Common inputs and outputs

- Timestamps, targets, centers, offsets: contiguous one-dimensional `np.int64`, in ns.
- Values: one- or two-dimensional `np.float64`; two-dimensional shape is `(N,D)`.
  Strided and reversed value views are supported.
- Inputs are copied into Rust-owned snapshots; outputs do not alias or modify caller buffers.
- Signal results contain timestamps (`int64` array), values (`float64` array), and channels (int).
- Diagnostic reports are dictionaries. Some interfaces return lists, as documented below.
- Bindings hold the GIL; episode-level process scheduling belongs upstream.

## 1. inspect_signal

```python
ops.inspect_signal(timestamps, values, config=None) -> dict
```

| Configuration field | Default | Units / meaning |
| --- | --- | --- |
| max_gap_ns | int64 maximum | Threshold for positive time gaps |
| lower, upper | None | D finite thresholds in value units |
| max_rate | None | D nonnegative thresholds in value-units/second |
| max_acceleration | None | D nonnegative thresholds in value-units/second squared |
| hampel_window_ns | None | Positive time radius on each side; may use future samples |
| hampel_sigma | 3.0 | MAD multiplier |
| hampel_min_deviation | 0.0 | Minimum absolute deviation in value units |
| max_hampel_samples | 4096 | Per-window sample cap, at least 3 |
| flatline_duration_ns | None | Flatline candidate duration |
| flatline_tolerance | 0.0 | Numeric tolerance for flatline checks |
| max_issues | 10000 | Stored issue-detail cap; total count remains available |

Returns time/channel statistics, issues, total_issues, issues_truncated,
flagged_sample_count, and dynamic_checks_completed. Codes are non_finite,
below_range, above_range, clock_reversal, duplicate_time, gap, rate,
acceleration, spike, and flatline. Threshold arrays must match D; scalars are
not broadcast. The operator does not repair or delete data.

## 2. uniform_grid

```python
ops.uniform_grid(start_ns, end_ns, rate_num, rate_den, max_points) -> list[int]
```

Constructs a half-open `[start,end)` integer-nanosecond grid at
`rate_num/rate_den` Hz, including rates such as 30000/1001. Convert the returned
list with `np.asarray(..., dtype=np.int64)` before passing it to numeric APIs.
Invalid bounds/rates, excessive point counts, or rates beyond nanosecond
resolution fail explicitly.

## 3. align_timestamps

```python
ops.align_timestamps(source, target, *, nearest=False,
                     max_past_ns=0, max_future_ns=0) -> dict
```

Matches timestamps without interpolating values. Source must be strictly
increasing and target nondecreasing. Returns indices (`int64[M]`), offsets_ns
(`int64[M]`, source minus target), and valid (`bool[M]`). By default only past
samples are considered; nearest=True permits future candidates within their
separate tolerance. Ties prefer the past. Invalid indices are -1; zero invalid
offsets do not mean an actual match.

## 4. resample

```python
ops.resample(timestamps, values, target, *, method="previous",
             max_gap_ns=0, max_age_ns=0, allow_future=False) -> dict
```

Methods: previous, nearest, linear, slerp. See [contracts](concepts.md).

| Field | Type / shape |
| --- | --- |
| timestamps | int64 `(M,)` |
| values | float64 `(M,D)` |
| channels | Python int |
| status | uint8 `(M,)`; 0 is valid, codes 1–6 describe failure |
| valid | bool `(M,)`, status==0 |
| source_left, source_right | int64 `(M,)`; -1 when invalid |
| alpha | float64 `(M,)` |
| uses_future | bool `(M,)` |

Source must be strictly increasing; target nondecreasing. Interpolation checks
max_gap, while single-sample support checks max_age. Exact matches need no future
support. Missing support is not zero-filled. SLERP requires D=4 in xyzw order,
with input norm within 0.01 of one.

## 5. history_windows

```python
ops.history_windows(timestamps, values, centers, offsets, *, method="previous",
                    max_gap_ns=0, max_age_ns=0, allow_future=False) -> dict
```

Requests `centers[i] + offsets[j]`. Centers must be strictly increasing; offsets
nonempty, strictly increasing, and nonpositive. Adds centers and offsets to the
resample fields. Values have shape `(T,W,D)` and timestamps `(T,W)`;
**valid/status/source/alpha/uses_future remain flat `(T*W,)`**. Reshape explicitly,
for example `result["valid"].reshape(T,W)`.

## 6–9. Filters and angles

```python
ops.ema(timestamps, values, tau_seconds, max_gap_ns) -> dict
ops.lowpass_taps(sample_rate_hz, cutoff_hz, taps) -> list[float]
ops.fir(timestamps, values, taps, *, mode="causal",
        period_ns=1, tolerance_ns=0) -> dict
ops.unwrap_angles(timestamps, values, *, period=2*np.pi, max_gap_ns=0) -> dict
```

EMA/FIR return Signal fields plus valid (`list[bool]`), mode,
lookahead_samples, and group_delay_samples (float or None). Unwrapping returns
only Signal fields, without valid.

lowpass_taps requires an odd tap count in [3,4095] and
`0 < cutoff < sample_rate/2`. FIR accepts a contiguous one-dimensional float64
tap array of length 1–4095; centered mode additionally requires odd length.
Require `period_ns>0` and `0<=tolerance_ns<period_ns`. Unsupported edges remain
NaN rather than being padded.

```python
coefficients = np.asarray(ops.lowpass_taps(200.0, 20.0, 31), dtype=np.float64)
# t200/x200 are caller-provided regular 200 Hz arrays.
filtered = ops.fir(t200, x200, coefficients, period_ns=5_000_000)
valid = np.asarray(filtered["valid"], dtype=bool)
# Symmetric causal 31-tap FIR: 15-sample delay; first 30 samples lack support.
```

## 10–11. MCAP

```python
ops.inspect_mcap(path, *, filter=None, limits=None, max_gap_ns=0) -> dict
ops.read_json_signal(path, topic, fields, channels, *, filter=None, limits=None,
                     timestamp_pointer=None, publish_clock=False,
                     max_samples=10_000_000) -> dict
```

path is a string. fields is a list of RFC 6901 JSON pointers resolving to numbers
or flat numeric arrays. Values flatten in field order and must total channels.
The default output clock is log_time. An explicit timestamp_pointer must resolve
to int64 nanoseconds; otherwise publish_clock selects the MCAP clock.

| Configuration | Fields and defaults |
| --- | --- |
| filter | topics=[] (all), start_ns=None, end_ns=None, publish_clock=False |
| limits | max_record_bytes=67108864, max_messages=10000000 |

filter.publish_clock independently selects the clock used for filtering. Choosing
a payload timestamp does not change that filter clock. Read limits apply to the
scan, not just selected messages; a large chunk can exceed the record limit.
These limits are not total RSS bounds.

inspect_mcap returns source, file_bytes, scanned_messages, selected_messages,
complete, crc_validation, filter, and channels. Channel entries contain topic,
schema metadata/hash, and both clock statistics. The default gap threshold of
zero counts every positive interval as a gap: set an appropriate threshold.
Absent CRCs are not successful CRC checks; full-file completion requires EOF.

read_json_signal returns Signal fields. It does not decode CDR/Protobuf.

## 12–13. Images

```python
ops.image_quality(data, options=None) -> dict
ops.transform_image(bytes, options_json=None, crop=None,
                    resize=None, filter="lanczos3") -> list[int]
```

data/bytes are compressed PNG/JPEG Python bytes. image_quality accepts an options
dictionary; **transform_image currently takes an options_json string**, such as
`json.dumps(options)`. crop is `[x,y,width,height]`; resize is `[width,height]`.
Filters: nearest, triangle, lanczos3. Output is a PNG integer list; use bytes()
before saving or passing it on.

Default image options: max_width=16384, max_height=16384, max_pixels=64000000,
dark_threshold=10, bright_threshold=245. Dimensions/limits must be valid and
dark<bright. Metrics include dimensions, pixels, luminance_mean/std,
dark_fraction, bright_fraction, laplacian_variance, and rgb_sha256. Laplacian
variance is None for images smaller than 3×3. See [media examples](guides/media.md).

## 14. Video

```python
ops.validate_video(path, *, ffmpeg="ffmpeg", ffprobe="ffprobe",
                   timeout_seconds=600.0) -> dict
```

Probes a local file, then completely decodes the first video stream. Returns
complete, decoded, decoded_frames, elapsed_seconds, and probe. The total timeout
budget is in (0,86400] seconds; each tool has a 2 MiB diagnostic limit. Missing
tools, timeout, error diagnostics, empty video, or incomplete decoding fail.
Standalone probe_video is not exported to Python.

## Rust-only interfaces and version

`gate`, `IntervalSet`, `map_clock`, `inspect_time`, `expand_batch_timestamps`,
`RawReader`, `SignalDecoder`, and standalone `probe_video` remain Rust-only.
Python can obtain time-quality summaries through inspect_signal/inspect_mcap.
`ops.__version__` is a version string, not a processing operator.
