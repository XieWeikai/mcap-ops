# RSI results

Completed: **30 implementation units x 2 rounds = 60 final decisions**. Accepted 27; rejected 33.

Reference: `66248dacb608859d2cbd0f9f27227c65013a8027`. All builds, profiles, tests and timing runs execute on reference-linux (i9-14900K, CPU 12 affinity, Rust 1.90, release).

Production source changes: 10 files, 358 added lines and 178 removed lines (net +180). Runtime dependencies and public operator signatures are unchanged.

Each percentage is paired geometric-mean **latency reduction** across that operator's fixed cases, relative to the previously accepted implementation. A negative number means slower. An accepted round must clear 8% in every aggregate paired block, pass correctness, and avoid a representative-case regression greater than 3%.

Uniform-grid and wide-Hampel candidates with contradictory initial timing receive one independent eight-block confirmation. Original observations remain in `history/` and `data/`; this is a repeat measurement of the same candidate, not an extra code round.

| Operator | Round 1 | Round 2 | Accepted commits |
| --- | --- | --- | --- |
| `align_timestamps` | [rejected -9.61%](results/align-timestamps-r1.json) | [rejected -1.16%](results/align-timestamps-r2.json) | - |
| `ema` | [accepted +17.41%](results/ema-r1.json) | [accepted +36.74%](results/ema-r2.json) | `1e54c52c`, `2c74abb1` |
| `expand_batch_timestamps` | [rejected +0.35%](results/expand-batch-timestamps-r1.json) | [rejected -21.50%](results/expand-batch-timestamps-r2.json) | - |
| `fir` | [rejected -26.75%](results/fir-r1.json) | [rejected -26.42%](results/fir-r2.json) | - |
| `gate` | [accepted +17.60%](results/gate-r1.json) | [rejected -17.27%](results/gate-r2.json) | `fb9eb335` |
| `history_windows` | [accepted +28.73%](results/history-windows-r1.json) | [accepted +16.03%](results/history-windows-r2.json) | `e8bdffe8`, `fe9bcaee` |
| `image_decode` | [rejected -0.21%](results/image-decode-r1.json) | [rejected -0.25%](results/image-decode-r2.json) | - |
| `image_quality` | [accepted +25.30%](results/image-quality-r1.json) | [accepted +23.03%](results/image-quality-r2.json) | `06d3a446`, `9db705be` |
| `image_transform` | [rejected +5.20%](results/image-transform-r1.json) | [rejected +1.79%](results/image-transform-r2.json) | - |
| `inspect_signal` | [accepted +31.26%](results/inspect-signal-r1.json) | [rejected +19.18%](results/inspect-signal-r2-confirm.json) | `c27fcfd6` |
| `inspect_time` | [rejected +0.09%](results/inspect-time-r1.json) | [accepted +35.00%](results/inspect-time-r2.json) | `337d96ed` |
| `interval_affected_centers` | [accepted +15.00%](results/interval-affected-centers-r1.json) | [accepted +49.09%](results/interval-affected-centers-r2.json) | `cd09b796`, `aff99421` |
| `interval_contains` | [accepted +17.33%](results/interval-contains-r1.json) | [rejected +2.00%](results/interval-contains-r2.json) | `832dc378` |
| `interval_difference` | [accepted +99.68%](results/interval-difference-r1.json) | [accepted +10.55%](results/interval-difference-r2.json) | `7a1efc75`, `3f93cb66` |
| `interval_intersection` | [rejected -7.46%](results/interval-intersection-r1.json) | [rejected +87.54%](results/interval-intersection-r2.json) | - |
| `interval_mask` | [accepted +67.27%](results/interval-mask-r1.json) | [rejected +4.87%](results/interval-mask-r2.json) | `b887a199` |
| `interval_new` | [rejected +4.01%](results/interval-new-r1.json) | [rejected -3.73%](results/interval-new-r2.json) | - |
| `json_decode` | [accepted +28.42%](results/json-decode-r1.json) | [rejected +2.17%](results/json-decode-r2.json) | `6a5e5603` |
| `lowpass_taps` | [accepted +12.06%](results/lowpass-taps-r1.json) | [accepted +39.42%](results/lowpass-taps-r2.json) | `9fb2df8e`, `6922813b` |
| `map_clock` | [rejected +0.07%](results/map-clock-r1.json) | [accepted +58.89%](results/map-clock-r2.json) | `7669197d` |
| `mcap_inspect` | [rejected +1.45%](results/mcap-inspect-r1.json) | [rejected -1.08%](results/mcap-inspect-r2.json) | - |
| `mcap_read_signal` | [rejected +0.15%](results/mcap-read-signal-r1.json) | [rejected -0.03%](results/mcap-read-signal-r2.json) | - |
| `python_bridge` | [accepted +77.76%](results/python-bridge-r1.json) | [accepted +15.55%](results/python-bridge-r2.json) | `b54b55f7`, `84c4feed` |
| `raw_reader` | [rejected +1.08%](results/raw-reader-r1.json) | [rejected -15.43%](results/raw-reader-r2.json) | - |
| `require_strict` | [accepted +18.50%](results/require-strict-r1.json) | [rejected -2.37%](results/require-strict-r2.json) | `c40714e8` |
| `resample` | [rejected +10.45%](results/resample-r1.json) | [accepted +22.71%](results/resample-r2.json) | `e5e9c238` |
| `uniform_grid` | [rejected +0.40%](results/uniform-grid-r1.json) | [accepted +19.28%](results/uniform-grid-r2-confirm.json) | `160b5354` |
| `unwrap_angles` | [accepted +21.21%](results/unwrap-angles-r1.json) | [accepted +47.95%](results/unwrap-angles-r2.json) | `418988ea`, `7bdfd25c` |
| `video_probe` | [accepted +16.30%](results/video-probe-r1.json) | [rejected +0.26%](results/video-probe-r2.json) | `2fe85a7a` |
| `video_validate` | [rejected +1.35%](results/video-validate-r1.json) | [rejected -0.14%](results/video-validate-r2.json) | - |

## Evidence

- `results/`: final decisions, method, hotspot, complexity, per-case before/after timings and measurement hashes.
- `data/`: all paired samples and calibration counts; accepted commits contain their corresponding records.
- `rejected/`: candidate patches, including historical rejections that were later confirmed.
- `history/`: superseded unstable observations, kept without altering the raw data.
- reference-linux `.artifacts/rsi/trials/`: complete validation logs and Callgrind/cProfile output.

## Correctness

Every decision follows rustfmt, Clippy, 36 Rust tests, immutable-reference differential checks and 5 Python smoke tests. The differential suite exercises 180 randomized core scenarios, generated MCAP fixtures, PNG/JPEG, RGBA and 16-bit PNG. Integer timestamps, indices, masks and decisions match exactly; numeric comparisons use explicit f64 tolerances. Image transforms preserve decoded pixels. The Python bridge additionally passes 236 public-interface comparisons including dictionary order, empty shapes, strided values, NaN/Inf handling, errors and output ownership.

The host's perf permission prevents hardware-counter sampling. Profiling uses a project-local Callgrind installation and cProfile; profiler times are excluded from wall-clock measurements. Fixtures are synthetic and repeatable. Results describe these workloads on this shared host, not an unmeasured end-to-end robotics dataset pipeline.

## Final native comparison

Initial pre-RSI implementation versus the complete accepted state.

| Case | Before (us) | After (us) | Paired latency reduction |
| --- | ---: | ---: | ---: |
| `align_timestamps.nearest` | 100.198 | 101.283 | -1.67% |
| `align_timestamps.previous` | 61.497 | 62.669 | -1.37% |
| `ema.jitter` | 822.109 | 479.991 | +41.31% |
| `ema.uniform` | 822.377 | 374.339 | +54.37% |
| `expand_batch_timestamps` | 29.485 | 29.974 | -0.91% |
| `fir.scalar` | 421.897 | 448.729 | -5.28% |
| `fir.vector` | 1805.391 | 1889.869 | -5.44% |
| `gate.fail` | 0.044 | 0.031 | +29.56% |
| `gate.pass` | 0.009 | 0.009 | +2.10% |
| `history_windows.overlap` | 884.500 | 277.094 | +68.71% |
| `history_windows.separate` | 783.731 | 153.949 | +80.36% |
| `image_decode.jpeg` | 575.394 | 590.485 | -2.64% |
| `image_decode.png` | 1463.446 | 1485.618 | -0.48% |
| `image_quality.gradient` | 4359.547 | 2918.818 | +32.92% |
| `image_quality.noise` | 2989.671 | 1468.506 | +51.08% |
| `image_transform.gradient` | 5632.025 | 5588.114 | +0.11% |
| `image_transform.noise` | 4172.526 | 4167.406 | +0.12% |
| `inspect_signal.basic` | 3001.301 | 1461.175 | +51.24% |
| `inspect_signal.hampel` | 8354.645 | 6545.537 | +20.90% |
| `inspect_signal.wide_hampel` | 40010.588 | 36357.221 | +9.06% |
| `inspect_time.jitter` | 87.213 | 87.204 | +0.36% |
| `inspect_time.uniform` | 59.343 | 24.811 | +58.12% |
| `interval_affected_centers` | 13.369 | 5.674 | +57.77% |
| `interval_contains` | 298.011 | 247.334 | +17.44% |
| `interval_difference` | 3544.638 | 10.082 | +99.72% |
| `interval_intersection.dense` | 26.245 | 27.526 | -4.45% |
| `interval_intersection.late` | 12.778 | 12.772 | +0.03% |
| `interval_mask.ordered` | 277.781 | 25.475 | +90.89% |
| `interval_mask.shuffled` | 315.495 | 264.027 | +16.52% |
| `interval_new` | 8.519 | 8.588 | -0.56% |
| `json_decode` | 0.303 | 0.211 | +30.63% |
| `lowpass_taps` | 0.703 | 0.386 | +45.42% |
| `map_clock.drift` | 155.911 | 154.935 | +1.21% |
| `map_clock.offset` | 155.902 | 26.890 | +82.75% |
| `mcap_inspect` | 1762.891 | 1777.808 | +0.32% |
| `mcap_read_signal` | 7949.351 | 6168.488 | +22.86% |
| `raw_reader.chunked` | 1327.643 | 1316.979 | -0.57% |
| `raw_reader.linear` | 1652.953 | 1652.505 | +0.41% |
| `raw_reader.topics` | 1554.605 | 1449.242 | +6.81% |
| `require_strict` | 11.210 | 9.059 | +19.19% |
| `resample.linear` | 418.725 | 412.205 | +1.86% |
| `resample.nearest` | 337.393 | 248.240 | +26.86% |
| `resample.previous` | 330.083 | 218.205 | +34.20% |
| `resample.slerp` | 608.367 | 554.286 | +8.66% |
| `uniform_grid.integer` | 91.035 | 72.558 | +19.91% |
| `uniform_grid.rational` | 2.732 | 2.299 | +16.47% |
| `unwrap_angles` | 1023.879 | 416.128 | +59.36% |
| `video_probe` | 33999.961 | 27319.585 | +19.67% |
| `video_validate` | 68005.096 | 59232.217 | +12.90% |

## Final python comparison

Initial pre-RSI implementation versus the complete accepted state.

| Case | Before (us) | After (us) | Paired latency reduction |
| --- | ---: | ---: | ---: |
| `python.align_timestamps` | 1200.371 | 29.959 | +97.48% |
| `python.ema` | 30921.793 | 1378.313 | +95.56% |
| `python.fir` | 32840.124 | 3741.401 | +88.50% |
| `python.history_windows` | 20986.965 | 1083.551 | +94.85% |
| `python.image_quality` | 753.978 | 394.983 | +47.12% |
| `python.inspect_mcap` | 659.371 | 683.532 | -4.25% |
| `python.inspect_signal` | 2105.009 | 933.101 | +55.28% |
| `python.lowpass_taps` | 1.028 | 0.736 | +28.17% |
| `python.read_json_signal` | 2761.451 | 918.122 | +67.05% |
| `python.resample.linear` | 13037.479 | 240.654 | +98.15% |
| `python.resample.previous` | 12943.168 | 163.499 | +98.73% |
| `python.transform_image` | 974.855 | 987.411 | -0.76% |
| `python.uniform_grid` | 174.534 | 168.988 | +4.25% |
| `python.unwrap_angles` | 30093.930 | 1293.246 | +95.69% |
| `python.validate_video` | 67992.362 | 59113.221 | +13.06% |

## Unchanged-path follow-up

The combined build shows approximately 4-6% slower native FIR and dense interval intersection cases in both the full run and an eight-block focused repeat. Their operator bodies were retained because both direct optimization candidates were rejected. The cause of this combined-build difference is not established; it must not be described as a speedup or silently omitted. Python MCAP inspection returned to +1.7% in the focused repeat after -4.25% in the full run.

See `final/unchanged-native.json` and `final/unchanged-python.json` for every sample, and `final/unchanged-source.json` for the identical function-body hashes. These validation observations are not additional optimization candidates.

## Installed wheel

The wheel `mcap_ops-0.1.0-cp310-abi3-manylinux_2_39_x86_64.whl` passed five tests in a fresh environment and 236 public-interface comparisons. It targets Linux x86-64 / glibc 2.39+ with CPython abi3 (3.10+); execution was verified with CPython 3.12.3 and NumPy 2.5.4. See `final/verification.json` for the artifact SHA-256 and environment details.
