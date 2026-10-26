# Operator reference (0.1)

This is the first generic operator set. Operators are grouped by dependency,
not by robot product. Every operation is read-only unless its name says it
returns a new value; it never modifies an input MCAP or input array in place.

## Time and signal operators

| Operator | Input | Output and contract |
| --- | --- | --- |
| `uniform_grid` | integer `start_ns`, half-open `end_ns`, rational rate | integer-nanosecond grid; bounded by `max_points`, no float epoch conversion |
| `inspect_time` | original-order timestamps | reversals, duplicates, gaps, interval quantiles and estimated rate |
| `align_timestamps` | ordered source/target timestamps and past/future tolerances | source index, signed source-minus-target offset and valid mask |
| `map_clock` | timestamps, explicit origin/offset/rate correction | corrected timestamps; never estimates a clock mapping |
| `expand_batch_timestamps` | message times, per-message counts, sample offsets | per-sample timestamps; overflow and count mismatch are errors |
| `resample` | `Signal`, target grid, `previous`/`nearest`/`linear`/`slerp` | values plus status, source indices, interpolation alpha and future-use flag |
| `history_windows` | signal, strictly increasing centers, nonpositive offsets | `(steps, window, channels)` semantics with per-sample provenance |

`previous` is causal and age-limited. `nearest` may use a future value only when
requested. `linear` and `slerp` require valid bracketing samples and reject
unsupported gaps. `slerp` accepts normalized xyzw quaternions only.

## Quality and selection operators

| Operator | Input | Output and contract |
| --- | --- | --- |
| `inspect_signal` | signal and `QualityConfig` | summary statistics and point/interval `Issue` evidence |
| `gate` | report and explicit `GatePolicy` | pass/fail decision and reasons; does not repair or delete data |
| `IntervalSet` | half-open intervals | merged mask, intersection, difference and context expansion |
| `ema` | ordered signal, time constant, maximum gap | causal filtered signal; resets at invalid/outage and advertises no lookahead |
| `lowpass_taps` | rate, cutoff, odd tap count | normalized windowed-sinc coefficients |
| `fir` | regular-grid signal, taps, causal/centered mode | filtered signal, valid mask, lookahead and group-delay metadata |
| `unwrap_angles` | periodic numeric signal and gap limit | explicitly unwrapped angles, reset across invalid/outage |

`inspect_signal` detects non-finite values, ranges, time issues, rate,
acceleration, robust local spikes, and flatline candidates. A spike or flatline
is evidence, not an automatic rejection. Issue detail is capped for memory, but
the report retains total issue count and whether details were truncated.

## MCAP and media adapters

| Adapter | Input | Output and contract |
| --- | --- | --- |
| `RawReader` | local MCAP path, topic/time filter, byte/message limits | original-order raw messages; read-only, source fingerprint checked at EOF |
| `inspect_mcap` | MCAP path and limits | channel/schema inventory, per-channel clocks, payload bytes and CRC-validated completion |
| `JsonSignalSpec` / `read_signal` | explicit topic, JSON pointers and channel count | decoded `Signal`; unknown CDR/Protobuf is an explicit adapter responsibility |
| `image_quality` | bounded PNG/JPEG bytes | dimensions, exposure fractions, luminance and Laplacian variance |
| `transform_image` | bounded image plus crop/resize | new PNG bytes; source is unchanged |
| `probe_video` / `validate_video` | local video and explicit FFmpeg executables | stream metadata and complete first-video-stream decode result |

The media adapter uses argument arrays, bounded diagnostics and a timeout; it
does not invoke a shell. FFmpeg availability is an environment capability, not
a data-quality pass.

## Python surface

The Python exports are enumerated in [python.md](python.md) and
`python/mcap_ops/__init__.py`. Numeric results are returned as dictionaries
containing NumPy arrays; diagnostic reports are ordinary dictionaries. Some
lower-level interfaces (including interval selection and clock mapping) remain
Rust-only. The native extension is built with `abi3` for Python 3.10+; remote
integration verification currently uses CPython 3.12.
