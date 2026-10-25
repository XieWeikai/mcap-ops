# RSI protocol

Reference implementation: `66248dacb608859d2cbd0f9f27227c65013a8027`.
All execution is on reference-linux. Input recordings are generated, not user data.

## Coverage

Thirty implementation units are evaluated twice: strict time validation, grid,
clock mapping, time inspection, alignment, batch expansion, resampling (four
methods), history windows, signal inspection (basic and two Hampel windows),
quality gate, EMA, lowpass coefficients, FIR, unwrap, interval construction,
membership, mask, intersection, difference, context expansion, raw MCAP reader,
MCAP inspection, JSON decoder, decoded signal reading, image decode (PNG/JPEG),
image quality, image transform, video probe, video validation, and Python bridge.
Trivial field getters and package version are not processing operators.

## Measurement

- Release build, unchanged Rust toolchain and lockfile, debug line tables for
  profiling, no target-cpu or fast-math changes.
- Pin benchmark process to CPU 12, a performance core of the i9-14900K.
- Generate fixtures outside timing. Require successful results, not Result::Err.
- Black-box inputs and outputs. Calibrate iteration counts, then collect seven
  samples; compare medians within each paired block.
- Run at least four before/after blocks, alternating AB and BA order. Preserve
  raw samples, versions and per-case results.
- Use geometric mean of paired latency ratios across an operator's fixed cases.
  Acceptance requires at least 8% latency reduction (stricter than 8% throughput
  gain), all correctness checks passing and modest code complexity. Investigate
  representative-case regressions or unstable timing before acceptance.
- Round two compares with round one's accepted state; rejected candidates do not
  become baselines.

## Profiling

Hardware perf counters are unavailable (`perf_event_paranoid=4`). A project-local
Valgrind/Callgrind installation supplies user-space call-graph/instruction
profiles without changing system permissions. Python uses cProfile for bridge
cost attribution. Profiler timings are never used as wall-clock benchmark data.

## Correctness and audit

Keep CRC validation, original order, limits, error behavior, invalid masks,
provenance, timestamps and shapes. No removed checks, skipped records, silent
sampling, lossy encoding, unsafe buffers, or fake successful results.

Retain generated fixture tests, randomized contract tests, and reference/candidate
differential tests. Integer/index/mask/text outputs must match. Floating-point
changes require explicitly checked tolerances; images must match decoded pixels.

Each accepted optimization commit records its round, hotspot, change, before/after
performance, correctness evidence, complexity assessment and report paths.
Rejected candidates have a record and patch, not a production-code commit.
Benchmark/test scaffolding is identified separately from performance changes.

## Exploratory run

An initial split of the four resampling methods was rejected: previous sampling
became faster, but linear sampling regressed and code duplication grew. Initial
MCAP timings measured an error because a fixture chunk exceeded its configured
limit; these numbers are invalid and excluded. The corrected harness unwraps
success, precomputes gate reports, and uses off-grid interpolation inputs.
