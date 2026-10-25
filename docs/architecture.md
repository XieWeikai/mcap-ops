# Architecture and first-release contract

Status: design accepted for implementation in this repository. Capability and
test results will be updated after remote verification.

## Ownership

The local checkout is the authoring repository. `.`
on SSH host `reference-linux` is its test checkout. Changes are committed locally and
transferred without force-updating divergent remote history. Neither checkout
contains the third-party Xpark demonstration in its tracked tree.

All compilation, Rust tests, Python integration tests, wheel verification and
benchmarks run on reference-linux. No robotics services or existing upstream repositories
are modified.

## Three deep modules

```text
upstream Rust / LeTools / providers / arbitrary Python caller
                         |
             Python bindings (optional)
                         |
      +------------------+-------------------+
      |                                      |
 core: numeric arrays and time          io: MCAP / image / video
      |                                      |
 quality -> selection -> transform      schema-specific Decoder seam
      |                                      |
 values + validity + source support     original-order messages / signals
```

The core has no filesystem, Python, ROS, FFmpeg, MCAP, or dataset-format
dependency. An upstream provider can decode its own CDR/Protobuf and pass arrays
directly. The IO module provides raw-message access and an initial explicit JSON
field decoder. Unknown payload encodings fail explicitly when numeric decoding
is requested; they remain inspectable as MCAP channels and raw messages.

The first real decoder seam has two paths: built-in JSON extraction and an
upstream-supplied Rust `SignalDecoder`. There is no speculative plugin registry
or dynamic code execution.

## Numeric representation

- Absolute timestamps are signed 64-bit integer nanoseconds. MCAP u64 times
  outside that range are rejected when converting to a numeric Signal.
- `Signal` owns row-major f64 values of shape `(samples, channels)`. It validates
  shape, not quality, so original out-of-order timestamps and NaN/Inf remain
  available to inspection. Transformations validate their stricter preconditions.
- Sampling requires strictly increasing source timestamps. Duplicate resolution
  is an explicit upstream choice; neither sorting nor deduplication is silent.
- The initial core does not guess units, frames, joint order, or action meaning.
  Callers retain a `SignalSpec` alongside the arrays for those contracts.
- Python copies input NumPy arrays into an immutable owned snapshot once. Rust
  work can release the GIL without concurrently reading mutable Python buffers.
  Output arrays transfer owned allocations where supported. This is not a claim
  of end-to-end zero-copy input.

## Time and sampling

- Interval selection uses half-open `[start, end)` nanosecond intervals.
- Rational-rate grids use integer arithmetic and bounded point counts.
- Clock mapping is explicit offset plus rate correction around a given origin.
  It never estimates clock corrections from robot response latency.
- Previous sampling is causal and age-limited. Nearest can use future samples
  only when configured. Linear and SLERP require valid bracketing support and a
  maximum gap. Exact original samples remain valid at gap endpoints.
- No extrapolation or silent zero-fill. Invalid outputs contain NaN, a status,
  and invalid source indices. Provenance records support indices, interpolation
  weights and future use.
- History windows preserve `(steps, window_samples, channels)` and per-sample
  provenance. Offsets must be nonpositive for causal history.
- Filtering is separate from sampling. A causal filter and an offline centered
  filter advertise different latency/lookahead. Filters never cross outages.
- Orientation uses normalized xyzw quaternions and shortest-path SLERP. Ordinary
  angle unwrapping is explicit, not applied to every numeric signal.

## Detection, selection and transformation

Quality operators report evidence, including sample/channel location, time
range, code, severity and measurements. They do not delete or repair input.
Numeric checks cover finite/range, rate/acceleration, robust local spikes,
flatline candidates and summary statistics. Flatlines and spikes are candidates,
not proof of a hardware fault or bad demonstration.

Selection uses an explicit policy and interval operations. It does not concatenate
disjoint intervals and pretend that time is continuous. An upstream writer owns
episode splitting, train splits and observation/action label semantics.

## IO and media

MCAP inspection preserves file order, reports channel-specific clock reversals,
and supports topic/time selection. All files are opened read-only. The initial
reader may map the file; this avoids copying the whole container but decompressed
chunks and selected decoded values still consume memory. Callers must not modify
or truncate an input while it is open.

Images support bounded PNG/JPEG decode, quality metrics, crop and resize.
Video probing and complete decode validation use caller-installed FFmpeg tools
from Rust with argument arrays, timeouts, bounded diagnostic reads and explicit
errors. This first release does not infer video packet timestamps from an unknown
MCAP schema. Upstream adapters supply the media mapping.

## Execution and extensibility

Start with contiguous data, integer timestamps, fused loops and batched Python
calls. Do not initialize a global Rayon/thread pool or claim that a GPU makes
these mostly CPU/IO operations faster. Episode-level concurrency belongs to the
upstream scheduler initially. Future SIMD/parallel paths must preserve the same
numeric, validity and provenance contract and be justified by benchmarks.

Dataset writing, web UI, robot-specific fallback rules, automatic clock fitting,
physical calibration, Ego perception and learned anomaly detectors are outside
the first release. Add them through upstream modules or explicit optional
adapters, not hidden policy in a generic resampler.

## Acceptance

1. Rust formatting, Clippy and workspace tests on reference-linux.
2. Boundary/property tests for timestamp overflow, gaps, non-finite values,
   quaternions, causality, provenance and interval selection.
3. Generated MCAP fixtures through actual writer/reader APIs, including malformed
   inputs, original write ordering and explicit schema decoding.
4. Real PNG/JPEG and generated video fixtures through actual media code.
5. Build an installable wheel; test installed NumPy interfaces and upstream-style
   usage in an isolated remote environment.
6. Record measured benchmark conditions without claiming universal speedups.
7. Local and remote Git HEAD and tracked file contents agree; no user dataset is
   needed or changed.
