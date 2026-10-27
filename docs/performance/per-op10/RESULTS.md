# Ten rounds per operator

**300/300 measured decisions; 23 accepted, 277 rejected.**

Baseline source: `9de19ead5df7444a9074c71028129b88970ba6ba`. Builds, profiles, tests and timing run only on Linux execution environment. Results use generated fixtures, CPU 12 affinity, four AB/BA paired blocks and seven calibrated samples per side.

Acceptance requires >=8% latency reduction in every aggregate block, no representative case slower by >3%, correctness and complexity checks passing. PNG encoder choices additionally preserve decoded pixels and cap measured output growth at 1.25x.

Retained production diff: 7 files, +242/-102 lines (net +140); pending candidates are excluded.

| Operator | Completed | Accepted |
| --- | ---: | ---: |
| `align_timestamps` | 10/10 | 1 |
| `ema` | 10/10 | 1 |
| `expand_batch_timestamps` | 10/10 | 0 |
| `fir` | 10/10 | 1 |
| `gate` | 10/10 | 1 |
| `history_windows` | 10/10 | 0 |
| `image_decode` | 10/10 | 0 |
| `image_quality` | 10/10 | 0 |
| `image_transform` | 10/10 | 0 |
| `inspect_signal` | 10/10 | 2 |
| `inspect_time` | 10/10 | 0 |
| `interval_affected_centers` | 10/10 | 2 |
| `interval_contains` | 10/10 | 0 |
| `interval_difference` | 10/10 | 1 |
| `interval_intersection` | 10/10 | 0 |
| `interval_mask` | 10/10 | 2 |
| `interval_new` | 10/10 | 2 |
| `json_decode` | 10/10 | 1 |
| `lowpass_taps` | 10/10 | 2 |
| `map_clock` | 10/10 | 1 |
| `mcap_inspect` | 10/10 | 0 |
| `mcap_read_signal` | 10/10 | 0 |
| `python_bridge` | 10/10 | 1 |
| `raw_reader` | 10/10 | 1 |
| `require_strict` | 10/10 | 2 |
| `resample` | 10/10 | 1 |
| `uniform_grid` | 10/10 | 1 |
| `unwrap_angles` | 10/10 | 0 |
| `video_probe` | 10/10 | 0 |
| `video_validate` | 10/10 | 0 |

Percentages below compare with each round's previously accepted state. They are medians of paired ratios, not ratios of separately displayed median timings. A parameter sweep is reported as a parameter sweep, not as distinct algorithms.

## align_timestamps

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | start alignment at the first relevant source prefix | [accepted](results/ten-align-timestamps-01.json) | +16.30% | +14.73% | `27f036a6` |
| 2 | binary-search only highly sparse target grids | [rejected](results/ten-align-timestamps-02.json) | -6.72% | -14.80% | `-` |
| 3 | reuse alignment results for repeated targets | [rejected](results/ten-align-timestamps-03.json) | -38.23% | -38.51% | `-` |
| 4 | carry candidate distances through alignment selection | [rejected](results/ten-align-timestamps-04.json) | +0.24% | +0.04% | `-` |
| 5 | use checked narrow differences for tolerance rejection | [rejected](results/ten-align-timestamps-05.json) | -0.33% | -0.97% | `-` |
| 6 | cast only offsets proven within signed tolerance | [rejected](results/ten-align-timestamps-06.json) | +5.92% | +5.25% | `-` |
| 7 | use the slice sortedness primitive for target validation | [rejected](results/ten-align-timestamps-07.json) | -5.26% | -5.74% | `-` |
| 8 | measure always inlining for align_timestamps | [rejected](results/ten-align-timestamps-08.json) | -0.85% | -1.52% | `-` |
| 9 | measure never inlining for align_timestamps | [rejected](results/ten-align-timestamps-09.json) | -0.51% | -1.15% | `-` |
| 10 | advance alignment with a sliced lookahead iterator | [rejected](results/ten-align-timestamps-10.json) | -7.53% | -9.29% | `-` |

## ema

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | initialize EMA storage through zeroed allocation | [rejected](results/ten-ema-01.json) | +2.84% | +0.40% | `-` |
| 2 | initialize EMA storage from the input snapshot | [rejected](results/ten-ema-02.json) | -6.66% | -7.91% | `-` |
| 3 | store EMA cache validity in an impossible negative delta | [rejected](results/ten-ema-03.json) | +1.34% | -0.58% | `-` |
| 4 | cache 2 exact EMA delta weights | [accepted](results/ten-ema-04.json) | +17.93% | +14.90% | `6172f7e8` |
| 5 | cache 4 exact EMA delta weights | [rejected](results/ten-ema-05.json) | -1.03% | -1.14% | `-` |
| 6 | cache 8 exact EMA delta weights | [rejected](results/ten-ema-06.json) | -1.69% | -2.84% | `-` |
| 7 | compare finite EMA inputs against the maximum finite magnitude | [rejected](results/ten-ema-07.json) | +3.82% | +2.87% | `-` |
| 8 | measure always inlining for ema | [rejected](results/ten-ema-08.json) | -8.92% | -10.00% | `-` |
| 9 | measure never inlining for ema | [rejected](results/ten-ema-09.json) | -0.38% | -1.98% | `-` |
| 10 | reuse a finite reciprocal time constant | [rejected](results/ten-ema-10.json) | +1.47% | -3.05% | `-` |

## expand_batch_timestamps

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | unroll checked batch addition by 4 | [rejected](results/ten-expand-batch-timestamps-01.json) | +6.29% | +5.78% | `-` |
| 2 | unroll checked batch addition by 8 | [rejected](results/ten-expand-batch-timestamps-02.json) | +7.19% | +5.59% | `-` |
| 3 | specialize batches with a common positive width | [rejected](results/ten-expand-batch-timestamps-03.json) | +6.79% | +6.36% | `-` |
| 4 | split the output tail once per batch | [rejected](results/ten-expand-batch-timestamps-04.json) | +1.68% | +1.61% | `-` |
| 5 | fallibly iterate each batch slice | [rejected](results/ten-expand-batch-timestamps-05.json) | +0.71% | +0.04% | `-` |
| 6 | accumulate batch overflow flags while adding | [rejected](results/ten-expand-batch-timestamps-06.json) | -12.66% | -14.26% | `-` |
| 7 | skip additions for zero-origin message batches | [rejected](results/ten-expand-batch-timestamps-07.json) | +1.95% | +1.16% | `-` |
| 8 | measure always inlining for expand_batch_timestamps | [rejected](results/ten-expand-batch-timestamps-08.json) | +0.10% | -1.11% | `-` |
| 9 | measure never inlining for expand_batch_timestamps | [rejected](results/ten-expand-batch-timestamps-09.json) | +1.70% | +1.31% | `-` |
| 10 | zip original offsets with batch output slices | [rejected](results/ten-expand-batch-timestamps-10.json) | +0.46% | -0.62% | `-` |

## fir

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | index FIR support directly in the flat signal buffer | [rejected](results/ten-fir-01.json) | +3.88% | +3.34% | `-` |
| 2 | iterate FIR support as reversed row chunks | [rejected](results/ten-fir-02.json) | +13.11% | +12.87% | `-` |
| 3 | construct row and gap support prefixes in one pass | [rejected](results/ten-fir-03.json) | -3.47% | -5.58% | `-` |
| 4 | track consecutive support while retaining channel-outer convolution | [accepted](results/ten-fir-04.json) | +11.67% | +11.24% | `f2981781` |
| 5 | specialize finite one-tap FIR windows | [rejected](results/ten-fir-05.json) | -12.25% | -13.34% | `-` |
| 6 | unroll ordered FIR accumulation by 2 coefficients | [rejected](results/ten-fir-06.json) | -13.50% | -14.38% | `-` |
| 7 | unroll ordered FIR accumulation by 4 coefficients | [rejected](results/ten-fir-07.json) | -5.37% | -5.99% | `-` |
| 8 | measure always inlining for fir | [rejected](results/ten-fir-08.json) | +5.85% | +5.79% | `-` |
| 9 | measure never inlining for fir | [rejected](results/ten-fir-09.json) | -0.30% | -0.40% | `-` |
| 10 | specialize common FIR lengths without transposing data | [rejected](results/ten-fir-10.json) | -9.40% | -9.89% | `-` |

## gate

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | skip code-policy iteration for issue-free reports | [rejected](results/ten-gate-01.json) | +0.79% | -0.66% | `-` |
| 2 | index present quality codes with a stack bitmap | [rejected](results/ten-gate-02.json) | +2.43% | +0.96% | `-` |
| 3 | index present quality codes with a bit mask | [rejected](results/ten-gate-03.json) | +1.49% | +0.30% | `-` |
| 4 | reserve the exact number of rejection reasons | [rejected](results/ten-gate-04.json) | -11.34% | -14.27% | `-` |
| 5 | reserve a bounded estimate only for likely rejection reasons | [rejected](results/ten-gate-05.json) | -2.37% | -3.90% | `-` |
| 6 | look up static issue names by their enum discriminant | [rejected](results/ten-gate-06.json) | -2.72% | -4.89% | `-` |
| 7 | return an empty decision immediately for fully passing policies | [accepted](results/ten-gate-07.json) | +16.73% | +15.33% | `4d628840` |
| 8 | measure always inlining for gate | [rejected](results/ten-gate-08.json) | -3.48% | -4.93% | `-` |
| 9 | measure never inlining for gate | [rejected](results/ten-gate-09.json) | -0.03% | -0.51% | `-` |
| 10 | collect ordered rejection reasons through chained iterators | [rejected](results/ten-gate-10.json) | -9.40% | -10.70% | `-` |

## history_windows

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | stably merge-sort history request timestamps | [rejected](results/ten-history-windows-01.json) | -5.10% | -5.58% | `-` |
| 2 | merge sorted history offset streams with a bounded heap | [rejected](results/ten-history-windows-02.json) | +1.75% | +0.41% | `-` |
| 3 | merge history streams by scanning their current heads | [rejected](results/ten-history-windows-03.json) | +7.94% | +6.32% | `-` |
| 4 | scatter history samples with a monotone unique index | [rejected](results/ten-history-windows-04.json) | +1.36% | +0.12% | `-` |
| 5 | sort unique history times and index requests by hash | [rejected](results/ten-history-windows-05.json) | -16.19% | -17.61% | `-` |
| 6 | compare history separation using unsigned spans | [rejected](results/ten-history-windows-06.json) | -1.52% | -1.97% | `-` |
| 7 | derive flat history destinations from request length | [rejected](results/ten-history-windows-07.json) | +0.71% | -3.40% | `-` |
| 8 | measure always inlining for history_windows | [rejected](results/ten-history-windows-08.json) | -1.36% | -2.44% | `-` |
| 9 | measure never inlining for history_windows | [rejected](results/ten-history-windows-09.json) | +0.87% | -1.84% | `-` |
| 10 | move the history timestamp buffer into empty sampled storage | [rejected](results/ten-history-windows-10.json) | -0.36% | -2.60% | `-` |

## image_decode

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | measure a 1024-byte bounded image input buffer | [rejected](results/ten-image-decode-01.json) | -1.71% | -2.65% | `-` |
| 2 | measure a 2048-byte bounded image input buffer | [rejected](results/ten-image-decode-02.json) | -1.77% | -3.71% | `-` |
| 3 | measure a 4096-byte bounded image input buffer | [rejected](results/ten-image-decode-03.json) | -0.91% | -2.86% | `-` |
| 4 | measure a 16384-byte bounded image input buffer | [rejected](results/ten-image-decode-04.json) | -1.65% | -2.14% | `-` |
| 5 | measure a 32768-byte bounded image input buffer | [rejected](results/ten-image-decode-05.json) | +0.05% | -1.67% | `-` |
| 6 | measure a 65536-byte bounded image input buffer | [rejected](results/ten-image-decode-06.json) | +0.30% | -0.37% | `-` |
| 7 | measure a 131072-byte bounded image input buffer | [rejected](results/ten-image-decode-07.json) | -0.27% | -0.92% | `-` |
| 8 | measure a 262144-byte bounded image input buffer | [rejected](results/ten-image-decode-08.json) | -0.77% | -2.49% | `-` |
| 9 | measure always inlining for image_decode | [rejected](results/ten-image-decode-09.json) | +0.81% | +0.18% | `-` |
| 10 | measure never inlining for image_decode | [rejected](results/ten-image-decode-10.json) | +0.33% | -0.16% | `-` |

## image_quality

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | aggregate luminance moments in blocks of 64 | [rejected](results/ten-image-quality-01.json) | +2.19% | +2.15% | `-` |
| 2 | aggregate luminance moments in blocks of 128 | [rejected](results/ten-image-quality-02.json) | +2.87% | +2.52% | `-` |
| 3 | aggregate luminance moments in blocks of 512 | [rejected](results/ten-image-quality-03.json) | -2.13% | -2.69% | `-` |
| 4 | aggregate luminance moments in blocks of 1024 | [rejected](results/ten-image-quality-04.json) | -1.28% | -3.64% | `-` |
| 5 | reuse computed Laplacians during the variance pass | [rejected](results/ten-image-quality-05.json) | -31.61% | -32.54% | `-` |
| 6 | compute the Laplacian mean from telescoping image boundaries | [rejected](results/ten-image-quality-06.json) | +7.51% | +6.52% | `-` |
| 7 | use 4 independent luminance reduction lanes | [rejected](results/ten-image-quality-07.json) | +4.56% | +3.98% | `-` |
| 8 | use 8 independent luminance reduction lanes | [rejected](results/ten-image-quality-08.json) | +5.67% | +4.60% | `-` |
| 9 | measure always inlining for image_quality | [rejected](results/ten-image-quality-09.json) | -2.18% | -4.07% | `-` |
| 10 | measure never inlining for image_quality | [rejected](results/ten-image-quality-10.json) | +0.50% | -0.13% | `-` |

## image_transform

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | encode lossless PNG with Fast compression and Up filtering | [rejected](results/ten-image-transform-01.json) | +2.63% | +1.84% | `-` |
| 2 | encode lossless PNG with Fast compression and Avg filtering | [rejected](results/ten-image-transform-02.json) | +1.58% | +0.28% | `-` |
| 3 | encode lossless PNG with Fast compression and Paeth filtering | [rejected](results/ten-image-transform-03.json) | +1.14% | +0.79% | `-` |
| 4 | encode lossless PNG with Fast compression and NoFilter filtering | [rejected](results/ten-image-transform-04.json) | +2.89% | +1.08% | `-` |
| 5 | encode lossless PNG with Default compression and Adaptive filtering | [rejected](results/ten-image-transform-05.json) | -38.88% | -40.58% | `-` |
| 6 | encode lossless PNG with Default compression and Sub filtering | [rejected](results/ten-image-transform-06.json) | -56.84% | -59.55% | `-` |
| 7 | encode lossless PNG with Default compression and Paeth filtering | [rejected](results/ten-image-transform-07.json) | -39.55% | -41.67% | `-` |
| 8 | encode lossless PNG with Best compression and Adaptive filtering | [rejected](results/ten-image-transform-08.json) | -44.66% | -46.61% | `-` |
| 9 | measure always inlining for image_transform | [rejected](results/ten-image-transform-09.json) | -0.39% | -0.96% | `-` |
| 10 | measure never inlining for image_transform | [rejected](results/ten-image-transform-10.json) | -0.32% | -1.07% | `-` |

## inspect_signal

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | binary-select MAD across the two ordered deviation halves | [accepted](results/ten-inspect-signal-01.json) | +9.81% | +9.44% | `274e3383` |
| 2 | bypass sorting for already ordered finite Hampel samples | [rejected](results/ten-inspect-signal-02.json) | +0.22% | -0.04% | `-` |
| 3 | merge MAD deviations with explicit exhausted-side checks | [rejected](results/ten-inspect-signal-03.json) | -12.52% | -13.58% | `-` |
| 4 | cache each MAD frontier deviation in peekable iterators | [rejected](results/ten-inspect-signal-04.json) | -15.54% | -16.83% | `-` |
| 5 | maintain a sorted Hampel window by insertion and removal | [accepted](results/ten-inspect-signal-05.json) | +44.00% | +43.97% | `52093013` |
| 6 | restrict Hampel boundary searches to unconsumed suffixes | [rejected](results/ten-inspect-signal-06.json) | +12.08% | +11.87% | `-` |
| 7 | extract only active Hampel channels into contiguous scratch | [rejected](results/ten-inspect-signal-07.json) | -0.40% | -0.65% | `-` |
| 8 | measure always inlining for inspect_signal | [rejected](results/ten-inspect-signal-08.json) | -0.60% | -0.98% | `-` |
| 9 | measure never inlining for inspect_signal | [rejected](results/ten-inspect-signal-09.json) | -0.06% | -1.00% | `-` |
| 10 | mark singleton quality spans by direct index | [rejected](results/ten-inspect-signal-10.json) | +0.22% | -0.01% | `-` |

## inspect_time

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | reserve the maximum positive-interval count | [rejected](results/ten-inspect-time-01.json) | +0.27% | +0.17% | `-` |
| 2 | summarize two-valued interval distributions without sorting | [rejected](results/ten-inspect-time-02.json) | -10.80% | -11.49% | `-` |
| 3 | skip fallback sorting when intervals are already ordered | [rejected](results/ten-inspect-time-03.json) | -6.68% | -7.24% | `-` |
| 4 | zip the uniform-clock comparison pass | [rejected](results/ten-inspect-time-04.json) | +3.57% | +3.40% | `-` |
| 5 | zip interval statistics input pairs | [rejected](results/ten-inspect-time-05.json) | -2.46% | -3.41% | `-` |
| 6 | compare stable adaptive sorting for jitter statistics | [rejected](results/ten-inspect-time-06.json) | -5.11% | -8.14% | `-` |
| 7 | fill a bounded interval buffer then truncate it | [rejected](results/ten-inspect-time-07.json) | -3.36% | -4.36% | `-` |
| 8 | measure always inlining for inspect_time | [rejected](results/ten-inspect-time-08.json) | -0.89% | -1.46% | `-` |
| 9 | measure never inlining for inspect_time | [rejected](results/ten-inspect-time-09.json) | -0.22% | -0.32% | `-` |
| 10 | specialize the exact median quantile index | [rejected](results/ten-inspect-time-10.json) | -0.41% | -1.28% | `-` |

## interval_affected_centers

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | return unchanged intervals for zero context | [accepted](results/ten-interval-affected-centers-01.json) | +26.00% | +25.26% | `7d0cb4e4` |
| 2 | prevalidate context arithmetic against global extrema | [rejected](results/ten-interval-affected-centers-02.json) | -16.58% | -18.20% | `-` |
| 3 | compact expanded intervals in the cloned input buffer | [rejected](results/ten-interval-affected-centers-03.json) | -47.93% | -49.93% | `-` |
| 4 | keep the expanding merge frontier in a local slot | [accepted](results/ten-interval-affected-centers-04.json) | +19.11% | +17.40% | `f1cfec74` |
| 5 | check context endpoints with wide arithmetic | [rejected](results/ten-interval-affected-centers-05.json) | -81.67% | -83.08% | `-` |
| 6 | reserve 16 intervals when the first expanded pair overlaps | [rejected](results/ten-interval-affected-centers-06.json) | +2.64% | +1.22% | `-` |
| 7 | reserve 256 intervals when the first expanded pair overlaps | [rejected](results/ten-interval-affected-centers-07.json) | +2.13% | -1.41% | `-` |
| 8 | measure always inlining for interval_affected_centers | [rejected](results/ten-interval-affected-centers-08.json) | -0.11% | -1.45% | `-` |
| 9 | measure never inlining for interval_affected_centers | [rejected](results/ten-interval-affected-centers-09.json) | -0.30% | -4.32% | `-` |
| 10 | merge context expansion through a fallible fold | [rejected](results/ten-interval-affected-centers-10.json) | -64.40% | -66.61% | `-` |

## interval_contains

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | use binary search on interval start keys | [rejected](results/ten-interval-contains-01.json) | +1.22% | -0.69% | `-` |
| 2 | walk binary-search bounds explicitly | [rejected](results/ten-interval-contains-02.json) | -50.54% | -52.08% | `-` |
| 3 | partition interval end times before checking the start | [rejected](results/ten-interval-contains-03.json) | -1.77% | -4.49% | `-` |
| 4 | unroll interval binary search by 2 steps | [rejected](results/ten-interval-contains-04.json) | -35.17% | -35.94% | `-` |
| 5 | unroll interval binary search by 4 steps | [rejected](results/ten-interval-contains-05.json) | -123.37% | -128.44% | `-` |
| 6 | binary-search by complete interval containment | [rejected](results/ten-interval-contains-06.json) | +1.40% | +1.29% | `-` |
| 7 | linearly search small interval sets after extent rejection | [rejected](results/ten-interval-contains-07.json) | +5.70% | +4.69% | `-` |
| 8 | measure always inlining for interval_contains | [rejected](results/ten-interval-contains-08.json) | +0.07% | -1.30% | `-` |
| 9 | measure never inlining for interval_contains | [rejected](results/ten-interval-contains-09.json) | -44.87% | -46.18% | `-` |
| 10 | load outer interval bounds together | [rejected](results/ten-interval-contains-10.json) | -16.63% | -17.24% | `-` |

## interval_difference

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | clone the input when exclusions are empty | [accepted](results/ten-interval-difference-01.json) | +51.29% | +50.16% | `c23981d6` |
| 2 | clone globally disjoint interval differences | [rejected](results/ten-interval-difference-02.json) | -6.32% | -9.19% | `-` |
| 3 | seed the exclusion cursor by prefix search | [rejected](results/ten-interval-difference-03.json) | -4.99% | -6.21% | `-` |
| 4 | combine exclusion bounds checks and interval access | [rejected](results/ten-interval-difference-04.json) | -1.17% | -2.60% | `-` |
| 5 | reserve difference storage with exclusion fraction 0 | [rejected](results/ten-interval-difference-05.json) | -0.88% | -1.43% | `-` |
| 6 | reserve difference storage with exclusion fraction 0.5 | [rejected](results/ten-interval-difference-06.json) | +0.59% | -0.70% | `-` |
| 7 | reserve difference storage with exclusion fraction 0.25 | [rejected](results/ten-interval-difference-07.json) | +0.61% | -1.15% | `-` |
| 8 | measure always inlining for interval_difference | [rejected](results/ten-interval-difference-08.json) | -0.25% | -1.28% | `-` |
| 9 | measure never inlining for interval_difference | [rejected](results/ten-interval-difference-09.json) | +0.92% | -2.14% | `-` |
| 10 | use one persistent exclusion iterator for differences | [rejected](results/ten-interval-difference-10.json) | -198.10% | -200.78% | `-` |

## interval_intersection

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | skip disjoint interior prefixes beyond 4 intervals | [rejected](results/ten-interval-intersection-01.json) | -33.43% | -34.14% | `-` |
| 2 | skip disjoint interior prefixes beyond 16 intervals | [rejected](results/ten-interval-intersection-02.json) | -29.81% | -31.40% | `-` |
| 3 | skip disjoint interior prefixes beyond 64 intervals | [rejected](results/ten-interval-intersection-03.json) | -32.29% | -34.37% | `-` |
| 4 | advance both intersection cursors at equal ends | [rejected](results/ten-interval-intersection-04.json) | -0.32% | -0.84% | `-` |
| 5 | bound initial intersection output capacity at 64 | [rejected](results/ten-interval-intersection-05.json) | +2.90% | +2.36% | `-` |
| 6 | bound initial intersection output capacity at 512 | [rejected](results/ten-interval-intersection-06.json) | +0.44% | -0.61% | `-` |
| 7 | return immediately for globally disjoint sets | [rejected](results/ten-interval-intersection-07.json) | +2.08% | +1.93% | `-` |
| 8 | measure always inlining for interval_intersection | [rejected](results/ten-interval-intersection-08.json) | -0.48% | -0.62% | `-` |
| 9 | measure never inlining for interval_intersection | [rejected](results/ten-interval-intersection-09.json) | -1.10% | -1.64% | `-` |
| 10 | merge intersection tails through peekable iterators | [rejected](results/ten-interval-intersection-10.json) | -0.41% | -0.77% | `-` |

## interval_mask

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | seed the mask cursor with a prefix search | [rejected](results/ten-interval-mask-01.json) | +2.40% | -1.07% | `-` |
| 2 | collect ordered masks through an exact-size iterator | [rejected](results/ten-interval-mask-02.json) | +18.21% | +16.98% | `-` |
| 3 | recognize empty interval masks before ordering checks | [accepted](results/ten-interval-mask-03.json) | +72.35% | +72.11% | `7e4ad1c5` |
| 4 | use the slice sortedness primitive for mask dispatch | [rejected](results/ten-interval-mask-04.json) | +8.36% | +7.18% | `-` |
| 5 | fill interval-aligned runs in the mask output | [rejected](results/ten-interval-mask-05.json) | -261.45% | -276.14% | `-` |
| 6 | reuse consecutive unordered duplicate membership queries | [rejected](results/ten-interval-mask-06.json) | -1.60% | -2.01% | `-` |
| 7 | reuse repeated ordered mask answers | [rejected](results/ten-interval-mask-07.json) | -50.10% | -51.63% | `-` |
| 8 | measure always inlining for interval_mask | [rejected](results/ten-interval-mask-08.json) | -1.34% | -3.84% | `-` |
| 9 | measure never inlining for interval_mask | [rejected](results/ten-interval-mask-09.json) | -0.40% | -3.45% | `-` |
| 10 | walk mask intervals with a peekable iterator | [accepted](results/ten-interval-mask-10.json) | +9.62% | +8.61% | `7a893c11` |

## interval_new

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | coalesce intervals with Vec deduplication | [accepted](results/ten-interval-new-01.json) | +43.67% | +42.75% | `bf27051a` |
| 2 | order equal-start intervals by their ends | [rejected](results/ten-interval-new-02.json) | -33.51% | -34.69% | `-` |
| 3 | use stable adaptive interval sorting | [rejected](results/ten-interval-new-03.json) | -1.28% | -4.06% | `-` |
| 4 | bound initial merge capacity to 128 intervals | [rejected](results/ten-interval-new-04.json) | -75.08% | -75.95% | `-` |
| 5 | bound initial merge capacity to 512 intervals | [rejected](results/ten-interval-new-05.json) | -75.41% | -77.05% | `-` |
| 6 | bound initial merge capacity to 2048 intervals | [rejected](results/ten-interval-new-06.json) | -73.80% | -76.15% | `-` |
| 7 | return already canonical interval buffers without copying | [accepted](results/ten-interval-new-07.json) | +22.99% | +22.75% | `2e7a32f3` |
| 8 | measure always inlining for interval_new | [rejected](results/ten-interval-new-08.json) | -2.45% | -3.37% | `-` |
| 9 | measure never inlining for interval_new | [rejected](results/ten-interval-new-09.json) | +0.46% | -0.38% | `-` |
| 10 | keep the active merge interval in a local slot | [rejected](results/ten-interval-new-10.json) | -128.08% | -143.60% | `-` |

## json_decode

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | traverse unescaped JSON pointer segments without allocating strings | [accepted](results/ten-json-decode-01.json) | +11.70% | +8.66% | `c20a2b9b` |
| 2 | reserve each resolved numeric array before flattening it | [rejected](results/ten-json-decode-02.json) | +2.54% | +0.36% | `-` |
| 3 | parse known UTF-8 JSON through the string parser | [rejected](results/ten-json-decode-03.json) | +1.75% | -0.61% | `-` |
| 4 | collect a single correctly sized numeric array directly | [rejected](results/ten-json-decode-04.json) | -0.82% | -2.38% | `-` |
| 5 | cap initial decoded-field capacity at 8 | [rejected](results/ten-json-decode-05.json) | +2.46% | -0.17% | `-` |
| 6 | cap initial decoded-field capacity at 16 | [rejected](results/ten-json-decode-06.json) | +2.95% | +2.23% | `-` |
| 7 | cap initial decoded-field capacity at 64 | [rejected](results/ten-json-decode-07.json) | +5.45% | +2.54% | `-` |
| 8 | measure always inlining for json_decode | [rejected](results/ten-json-decode-08.json) | -2.01% | -4.93% | `-` |
| 9 | measure never inlining for json_decode | [rejected](results/ten-json-decode-09.json) | +1.28% | -1.46% | `-` |
| 10 | detect reserved JSON pointer characters with byte searches | [rejected](results/ten-json-decode-10.json) | -10.25% | -11.97% | `-` |

## lowpass_taps

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | advance sinc phases by trigonometric recurrence | [rejected](results/ten-lowpass-taps-01.json) | +18.63% | +17.42% | `-` |
| 2 | advance Hamming phases by trigonometric recurrence | [accepted](results/ten-lowpass-taps-02.json) | +26.85% | +26.07% | `54e45b70` |
| 3 | advance both phases by trigonometric recurrence | [rejected](results/ten-lowpass-taps-03.json) | +34.63% | +34.06% | `-` |
| 4 | factor the sinc denominator into a reciprocal pi | [rejected](results/ten-lowpass-taps-04.json) | +0.18% | -0.92% | `-` |
| 5 | normalize coefficients with a guarded reciprocal sum | [rejected](results/ten-lowpass-taps-05.json) | +5.80% | +4.67% | `-` |
| 6 | set the center coefficient outside the symmetric loop | [rejected](results/ten-lowpass-taps-06.json) | +6.64% | +4.49% | `-` |
| 7 | specialize three-tap coefficient construction | [accepted](results/ten-lowpass-taps-07.json) | +21.21% | +20.82% | `c52eceae` |
| 8 | measure always inlining for lowpass_taps | [rejected](results/ten-lowpass-taps-08.json) | +0.43% | -1.60% | `-` |
| 9 | measure never inlining for lowpass_taps | [rejected](results/ten-lowpass-taps-09.json) | -0.54% | -1.93% | `-` |
| 10 | append the symmetric coefficient half without zero filling | [rejected](results/ten-lowpass-taps-10.json) | -4.04% | -6.59% | `-` |

## map_clock

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | copy clock-identity inputs directly | [accepted](results/ten-map-clock-01.json) | +43.11% | +39.38% | `24b5da70` |
| 2 | apply pure clock offsets in a cloned output buffer | [rejected](results/ten-map-clock-02.json) | -15.92% | -17.89% | `-` |
| 3 | validate offset extrema once before vectorizable addition | [rejected](results/ten-map-clock-03.json) | -77.58% | -90.39% | `-` |
| 4 | reserve and push nonzero-drift clock outputs | [rejected](results/ten-map-clock-04.json) | -67.51% | -68.67% | `-` |
| 5 | isolate wide drift arithmetic from the offset fast path | [rejected](results/ten-map-clock-05.json) | -63.76% | -68.67% | `-` |
| 6 | hoist the clock output origin and offset sum | [rejected](results/ten-map-clock-06.json) | -65.97% | -110.20% | `-` |
| 7 | divide representable drift magnitudes as unsigned integers | [rejected](results/ten-map-clock-07.json) | -84.73% | -97.17% | `-` |
| 8 | measure always inlining for map_clock | [rejected](results/ten-map-clock-08.json) | -79.12% | -79.23% | `-` |
| 9 | measure never inlining for map_clock | [rejected](results/ten-map-clock-09.json) | -92.36% | -101.58% | `-` |
| 10 | unroll pure offset updates in four-element blocks | [rejected](results/ten-map-clock-10.json) | +5.07% | -6.43% | `-` |

## mcap_inspect

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | accumulate per-channel clocks in a hash map | [rejected](results/ten-mcap-inspect-01.json) | -8.98% | -9.49% | `-` |
| 2 | store channel accumulators in a sorted compact vector | [rejected](results/ten-mcap-inspect-02.json) | -2.35% | -3.09% | `-` |
| 3 | materialize a publish-clock vector only after it differs | [rejected](results/ten-mcap-inspect-03.json) | +2.72% | +1.06% | `-` |
| 4 | reserve 8 clock points for each observed channel | [rejected](results/ten-mcap-inspect-04.json) | -0.06% | -0.72% | `-` |
| 5 | reserve 32 clock points for each observed channel | [rejected](results/ten-mcap-inspect-05.json) | +0.77% | -0.49% | `-` |
| 6 | group complete channel lookups in blocks of 8 | [rejected](results/ten-mcap-inspect-06.json) | -2.76% | -5.05% | `-` |
| 7 | group complete channel lookups in blocks of 32 | [rejected](results/ten-mcap-inspect-07.json) | -3.93% | -4.95% | `-` |
| 8 | measure always inlining for mcap_inspect | [rejected](results/ten-mcap-inspect-08.json) | -1.66% | -1.93% | `-` |
| 9 | measure never inlining for mcap_inspect | [rejected](results/ten-mcap-inspect-09.json) | +0.06% | -1.79% | `-` |
| 10 | reserve report storage for observed channel count | [rejected](results/ten-mcap-inspect-10.json) | -0.27% | -2.10% | `-` |

## mcap_read_signal

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | bound initial decoded signal capacity to 512 samples | [rejected](results/ten-mcap-read-signal-01.json) | +0.75% | -0.47% | `-` |
| 2 | bound initial decoded signal capacity to 1024 samples | [rejected](results/ten-mcap-read-signal-02.json) | +1.41% | -0.41% | `-` |
| 3 | bound initial decoded signal capacity to 8192 samples | [rejected](results/ten-mcap-read-signal-03.json) | -0.03% | -0.40% | `-` |
| 4 | copy decoded row slices into accumulated values | [rejected](results/ten-mcap-read-signal-04.json) | +1.42% | -0.10% | `-` |
| 5 | reuse the first decoded value vector as output storage | [rejected](results/ten-mcap-read-signal-05.json) | -0.34% | -1.62% | `-` |
| 6 | reserve bounded space for each decoded message batch | [rejected](results/ten-mcap-read-signal-06.json) | -0.46% | -0.66% | `-` |
| 7 | consume decoded messages through a borrowed cursor iterator | [rejected](results/ten-mcap-read-signal-07.json) | +0.68% | +0.02% | `-` |
| 8 | measure always inlining for mcap_read_signal | [rejected](results/ten-mcap-read-signal-08.json) | -0.06% | -1.21% | `-` |
| 9 | measure never inlining for mcap_read_signal | [rejected](results/ten-mcap-read-signal-09.json) | +0.92% | -2.19% | `-` |
| 10 | accumulate decoded samples through a fallible fold | [rejected](results/ten-mcap-read-signal-10.json) | -2.29% | -3.07% | `-` |

## python_bridge

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | write canonical non-finite outputs with branchless selection | [rejected](results/ten-python-bridge-01.json) | +1.02% | +0.59% | `-` |
| 2 | sanitize NumPy output values in 4-element blocks | [rejected](results/ten-python-bridge-02.json) | +1.39% | +1.08% | `-` |
| 3 | sanitize NumPy output values in 8-element blocks | [rejected](results/ten-python-bridge-03.json) | +0.88% | +0.51% | `-` |
| 4 | bypass the sanitizing write pass for all-finite outputs | [rejected](results/ten-python-bridge-04.json) | +1.33% | +1.21% | `-` |
| 5 | use static Python filter-mode names instead of formatting | [rejected](results/ten-python-bridge-05.json) | +1.28% | +0.46% | `-` |
| 6 | intern fixed Python result-dictionary keys | [rejected](results/ten-python-bridge-06.json) | +3.01% | +2.68% | `-` |
| 7 | copy strided inputs through ndarray standard-layout ownership | [accepted](results/ten-python-bridge-07.json) | +9.55% | +8.68% | `7f3ffd76` |
| 8 | measure always inlining for python_bridge | [rejected](results/ten-python-bridge-08.json) | -1.49% | -2.16% | `-` |
| 9 | measure never inlining for python_bridge | [rejected](results/ten-python-bridge-09.json) | +0.15% | -0.07% | `-` |
| 10 | reuse the NumPy module binding across public wrapper calls | [rejected](results/ten-python-bridge-10.json) | +1.18% | +0.12% | `-` |

## raw_reader

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | read MCAP through a 4096-byte buffer | [rejected](results/ten-raw-reader-01.json) | +0.06% | -0.39% | `-` |
| 2 | read MCAP through a 16384-byte buffer | [rejected](results/ten-raw-reader-02.json) | -0.74% | -5.33% | `-` |
| 3 | read MCAP through a 32768-byte buffer | [rejected](results/ten-raw-reader-03.json) | -0.55% | -1.58% | `-` |
| 4 | read MCAP through a 131072-byte buffer | [rejected](results/ten-raw-reader-04.json) | -0.20% | -1.43% | `-` |
| 5 | cache topic selection for the last immutable channel | [rejected](results/ten-raw-reader-05.json) | +1.85% | +1.08% | `-` |
| 6 | cache topic selection by channel identity in a small ordered map | [accepted](results/ten-raw-reader-06.json) | +10.87% | +9.62% | `725bf9c5` |
| 7 | cache topic selection for the last exact topic string | [rejected](results/ten-raw-reader-07.json) | -11.29% | -14.50% | `-` |
| 8 | hash long exact-topic filters once per reader | [rejected](results/ten-raw-reader-08.json) | -7.99% | -11.63% | `-` |
| 9 | measure always inlining for raw_reader | [rejected](results/ten-raw-reader-09.json) | +2.28% | +0.50% | `-` |
| 10 | measure never inlining for raw_reader | [rejected](results/ten-raw-reader-10.json) | -0.83% | -2.02% | `-` |

## require_strict

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | check timestamp order in 4-pair early-exit blocks | [accepted](results/ten-require-strict-01.json) | +24.98% | +16.75% | `f7b9cc07` |
| 2 | check timestamp order in 8-pair early-exit blocks | [accepted](results/ten-require-strict-02.json) | +25.31% | +17.46% | `5c408c46` |
| 3 | check timestamp order in 16-pair early-exit blocks | [rejected](results/ten-require-strict-03.json) | +5.45% | -26.11% | `-` |
| 4 | scan adjacent timestamp pairs in reverse order | [rejected](results/ten-require-strict-04.json) | -107.70% | -138.00% | `-` |
| 5 | locate the first invalid timestamp pair explicitly | [rejected](results/ten-require-strict-05.json) | -77.02% | -77.40% | `-` |
| 6 | check order with a scalar cursor | [rejected](results/ten-require-strict-06.json) | -97.01% | -97.55% | `-` |
| 7 | use a fallible fold for timestamp order validation | [rejected](results/ten-require-strict-07.json) | -79.04% | -79.69% | `-` |
| 8 | measure always inlining for require_strict | [rejected](results/ten-require-strict-08.json) | -75.98% | -133.55% | `-` |
| 9 | measure never inlining for require_strict | [rejected](results/ten-require-strict-09.json) | -82.04% | -82.92% | `-` |
| 10 | zip offset timestamp slices after a short-input guard | [rejected](results/ten-require-strict-10.json) | -77.69% | -135.21% | `-` |

## resample

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | seed resampling at the first target support prefix | [accepted](results/ten-resample-01.json) | +12.90% | +12.26% | `06d455cd` |
| 2 | reuse sampled values and provenance for duplicate targets | [rejected](results/ten-resample-02.json) | +3.57% | +3.09% | `-` |
| 3 | normalize exact quaternion samples without duplicating endpoint work | [rejected](results/ten-resample-03.json) | -3.48% | -4.40% | `-` |
| 4 | reuse bounded quaternion normalization reciprocals | [rejected](results/ten-resample-04.json) | +1.99% | +1.63% | `-` |
| 5 | infer interpolation input finiteness from the computed output | [rejected](results/ten-resample-05.json) | +3.17% | +1.69% | `-` |
| 6 | use unsigned support distances on ordered resampling brackets | [rejected](results/ten-resample-06.json) | +3.94% | +3.62% | `-` |
| 7 | allocate sampled values as zeroed storage and fill only invalid rows with NaNs | [rejected](results/ten-resample-07.json) | -0.90% | -1.50% | `-` |
| 8 | measure always inlining for resample | [rejected](results/ten-resample-08.json) | -0.67% | -1.06% | `-` |
| 9 | measure never inlining for resample | [rejected](results/ten-resample-09.json) | +0.68% | +0.31% | `-` |
| 10 | zip target timestamps with mutable sample statuses | [rejected](results/ten-resample-10.json) | -15.97% | -16.42% | `-` |

## uniform_grid

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | bound initial grid capacity at 256 points | [rejected](results/ten-uniform-grid-01.json) | +0.43% | +0.39% | `-` |
| 2 | bound initial grid capacity at 1024 points | [rejected](results/ten-uniform-grid-02.json) | +0.75% | +0.67% | `-` |
| 3 | bound initial grid capacity at 4096 points | [rejected](results/ten-uniform-grid-03.json) | +0.96% | +0.82% | `-` |
| 4 | keep rational-grid residual arithmetic in u64 | [accepted](results/ten-uniform-grid-04.json) | +33.38% | +33.09% | `73adddf4` |
| 5 | advance the grid with a branchless rational carry | [rejected](results/ten-uniform-grid-05.json) | -50.25% | -50.66% | `-` |
| 6 | specialize integer-period grids before the recurrence | [rejected](results/ten-uniform-grid-06.json) | -2.04% | -2.10% | `-` |
| 7 | fill an exactly sized grid buffer without push checks | [rejected](results/ten-uniform-grid-07.json) | -39.27% | -39.37% | `-` |
| 8 | measure always inlining for uniform_grid | [rejected](results/ten-uniform-grid-08.json) | -25.39% | -25.40% | `-` |
| 9 | measure never inlining for uniform_grid | [rejected](results/ten-uniform-grid-09.json) | -50.17% | -50.40% | `-` |
| 10 | terminate grid generation from output length and endpoint | [rejected](results/ten-uniform-grid-10.json) | -34.04% | -34.37% | `-` |

## unwrap_angles

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | hoist the angle half-period explicitly | [rejected](results/ten-unwrap-angles-01.json) | -1.81% | -2.24% | `-` |
| 2 | compare angle finiteness through finite magnitudes | [rejected](results/ten-unwrap-angles-02.json) | +3.85% | +3.09% | `-` |
| 3 | skip repeated gap arithmetic after a gap-free preflight | [rejected](results/ten-unwrap-angles-03.json) | -1.21% | -2.50% | `-` |
| 4 | iterate adjacent original angle rows as chunks | [rejected](results/ten-unwrap-angles-04.json) | +2.43% | +1.12% | `-` |
| 5 | expand positive-period Euclidean remainder explicitly | [rejected](results/ten-unwrap-angles-05.json) | +0.82% | -0.78% | `-` |
| 6 | handle single-turn angle remainders by exact subtraction | [rejected](results/ten-unwrap-angles-06.json) | +4.05% | +3.33% | `-` |
| 7 | compare ordered angle gaps as unsigned distances | [rejected](results/ten-unwrap-angles-07.json) | +4.62% | +1.98% | `-` |
| 8 | measure always inlining for unwrap_angles | [rejected](results/ten-unwrap-angles-08.json) | -5.54% | -7.46% | `-` |
| 9 | measure never inlining for unwrap_angles | [rejected](results/ten-unwrap-angles-09.json) | -1.12% | -2.15% | `-` |
| 10 | copy each angle row immediately before transforming it | [rejected](results/ten-unwrap-angles-10.json) | +7.88% | +5.57% | `-` |

## video_probe

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | poll media completion every 250 microseconds | [rejected](results/ten-video-probe-01.json) | +1.07% | -1.79% | `-` |
| 2 | poll media completion every 500 microseconds | [rejected](results/ten-video-probe-02.json) | +0.36% | -1.39% | `-` |
| 3 | poll media completion every 2000 microseconds | [rejected](results/ten-video-probe-03.json) | -1.76% | -2.54% | `-` |
| 4 | bound the final media sleep by the remaining timeout | [rejected](results/ten-video-probe-04.json) | -0.05% | -1.16% | `-` |
| 5 | move valid UTF-8 media output into Strings without copying | [rejected](results/ten-video-probe-05.json) | +1.30% | -0.33% | `-` |
| 6 | reserve the validated media output length before reading | [rejected](results/ten-video-probe-06.json) | +0.15% | -1.39% | `-` |
| 7 | append borrowed media arguments individually | [rejected](results/ten-video-probe-07.json) | +0.51% | -0.08% | `-` |
| 8 | measure always inlining for video_probe | [rejected](results/ten-video-probe-08.json) | +0.81% | -1.11% | `-` |
| 9 | measure never inlining for video_probe | [rejected](results/ten-video-probe-09.json) | -1.04% | -3.73% | `-` |
| 10 | compare media deadlines directly during polling | [rejected](results/ten-video-probe-10.json) | +0.11% | -0.86% | `-` |

## video_validate

| Round | Method | Decision | Gain | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | limit FFmpeg decoding to 1 threads | [rejected](results/ten-video-validate-01.json) | -0.39% | -2.09% | `-` |
| 2 | limit FFmpeg decoding to 2 threads | [rejected](results/ten-video-validate-02.json) | -1.63% | -3.17% | `-` |
| 3 | limit FFmpeg decoding to 4 threads | [rejected](results/ten-video-validate-03.json) | -4.25% | -5.21% | `-` |
| 4 | limit FFmpeg decoding to 8 threads | [rejected](results/ten-video-validate-04.json) | -8.51% | -9.48% | `-` |
| 5 | limit FFmpeg filter workers to 1 | [rejected](results/ten-video-validate-05.json) | -1.64% | -2.28% | `-` |
| 6 | limit FFmpeg filter workers to 2 | [rejected](results/ten-video-validate-06.json) | -1.60% | -3.52% | `-` |
| 7 | limit FFmpeg filter workers to 4 | [rejected](results/ten-video-validate-07.json) | -0.86% | -6.35% | `-` |
| 8 | limit FFmpeg filter workers to 8 | [rejected](results/ten-video-validate-08.json) | +0.46% | -1.12% | `-` |
| 9 | use one decoder and one filter worker together | [rejected](results/ten-video-validate-09.json) | +1.51% | +0.33% | `-` |
| 10 | emit periodic FFmpeg progress every two seconds | [rejected](results/ten-video-validate-10.json) | +1.27% | +0.11% | `-` |

## Final native comparison

Both source states use the completed benchmark harness. Negative values are regressions.

| Case | Before us | After us | Paired reduction |
| --- | ---: | ---: | ---: |
| `align_timestamps.nearest` | 100.799 | 94.158 | +6.53% |
| `align_timestamps.previous` | 63.090 | 55.973 | +11.64% |
| `align_timestamps.repeated` | 113.866 | 106.132 | +6.78% |
| `align_timestamps.sparse` | 19.244 | 5.346 | +72.17% |
| `ema.jitter` | 427.928 | 300.627 | +29.59% |
| `ema.uniform` | 313.373 | 300.732 | +4.66% |
| `expand_batch_timestamps` | 20.282 | 20.332 | -0.75% |
| `fir.gapped` | 122.836 | 104.214 | +14.68% |
| `fir.scalar` | 340.358 | 322.937 | +5.97% |
| `fir.short_scalar` | 140.340 | 112.697 | +19.66% |
| `fir.short_vector` | 353.436 | 314.460 | +11.03% |
| `fir.single` | 272.877 | 234.448 | +13.96% |
| `fir.small_scalar` | 0.268 | 0.210 | +22.10% |
| `fir.small_vector` | 0.450 | 0.403 | +10.12% |
| `fir.vector` | 1562.058 | 1538.253 | +1.69% |
| `fir.wide` | 6628.425 | 6425.513 | +2.63% |
| `gate.fail` | 0.030 | 0.029 | +3.59% |
| `gate.pass` | 0.009 | 0.006 | +29.46% |
| `history_windows.overlap` | 276.923 | 274.978 | +1.26% |
| `history_windows.separate` | 157.061 | 154.330 | +1.99% |
| `image_decode.jpeg` | 576.968 | 579.438 | -0.50% |
| `image_decode.png` | 1478.911 | 1453.642 | +1.59% |
| `image_quality.gradient` | 2723.398 | 2719.548 | +0.79% |
| `image_quality.noise` | 1256.800 | 1259.383 | -0.27% |
| `image_transform.gradient` | 5522.823 | 5511.450 | +0.54% |
| `image_transform.noise` | 4134.944 | 4128.069 | +0.56% |
| `inspect_signal.basic` | 1449.216 | 1415.347 | +2.68% |
| `inspect_signal.constant_hampel` | 1624.008 | 828.593 | +48.81% |
| `inspect_signal.hampel` | 3616.404 | 2708.421 | +25.86% |
| `inspect_signal.issues` | 1474.929 | 1499.344 | -2.30% |
| `inspect_signal.random_hampel` | 10577.738 | 1035.811 | +90.21% |
| `inspect_signal.wide_hampel` | 12791.839 | 5407.889 | +57.73% |
| `inspect_time.jitter` | 87.536 | 86.618 | +0.82% |
| `inspect_time.uniform` | 25.238 | 25.134 | +0.24% |
| `interval_affected_centers` | 5.646 | 5.094 | +9.55% |
| `interval_affected_centers.merged` | 8.328 | 3.280 | +60.61% |
| `interval_contains` | 245.489 | 246.578 | -0.42% |
| `interval_contains.small` | 16.581 | 16.537 | +0.26% |
| `interval_difference` | 9.934 | 9.873 | +0.68% |
| `interval_difference.empty` | 5.105 | 1.272 | +75.08% |
| `interval_intersection.dense` | 28.544 | 27.412 | +3.91% |
| `interval_intersection.late` | 0.168 | 0.170 | -1.34% |
| `interval_mask.empty` | 19.041 | 0.110 | +99.42% |
| `interval_mask.late` | 20.117 | 16.950 | +15.99% |
| `interval_mask.ordered` | 25.271 | 21.012 | +16.69% |
| `interval_mask.shuffled` | 269.827 | 268.857 | +0.55% |
| `interval_new` | 9.008 | 3.972 | +55.72% |
| `json_decode` | 0.212 | 0.210 | +1.52% |
| `json_decode.deep` | 0.341 | 0.228 | +33.20% |
| `json_decode.wide` | 0.886 | 0.901 | -1.70% |
| `lowpass_taps` | 0.385 | 0.258 | +33.00% |
| `lowpass_taps.long` | 24.688 | 15.728 | +36.29% |
| `lowpass_taps.short` | 0.033 | 0.015 | +55.28% |
| `map_clock.drift` | 153.910 | 154.366 | -0.16% |
| `map_clock.identity` | 26.412 | 5.352 | +79.73% |
| `map_clock.offset` | 26.184 | 26.386 | -0.86% |
| `mcap_inspect` | 1717.714 | 1730.588 | -0.74% |
| `mcap_inspect.many` | 2015.167 | 2009.680 | +0.27% |
| `mcap_read_signal` | 5950.383 | 6097.522 | -2.68% |
| `mcap_read_signal.many` | 1214.643 | 1227.768 | -0.95% |
| `raw_reader.chunked` | 1311.943 | 1321.464 | -0.90% |
| `raw_reader.linear` | 1669.051 | 1640.625 | +1.50% |
| `raw_reader.mixed_topics` | 1756.025 | 1331.834 | +23.86% |
| `raw_reader.topics` | 1554.960 | 1310.488 | +15.41% |
| `require_strict` | 9.177 | 5.195 | +43.39% |
| `resample.exact_slerp` | 414.036 | 424.470 | -2.32% |
| `resample.linear` | 409.727 | 398.861 | +2.85% |
| `resample.nearest` | 249.189 | 231.005 | +7.30% |
| `resample.previous` | 221.261 | 218.814 | +0.78% |
| `resample.repeated` | 167.756 | 156.699 | +6.86% |
| `resample.slerp` | 561.503 | 577.627 | -2.91% |
| `resample.sparse_linear` | 18.872 | 5.537 | +70.54% |
| `uniform_grid.integer` | 71.727 | 49.825 | +30.36% |
| `uniform_grid.rational` | 2.232 | 1.607 | +27.97% |
| `unwrap_angles` | 372.223 | 363.735 | +2.28% |
| `unwrap_angles.wraps` | 434.921 | 419.621 | +3.45% |
| `video_probe` | 25907.544 | 25489.022 | +1.72% |
| `video_validate` | 55878.239 | 55169.163 | +1.49% |

## Final python comparison

Both source states use the completed benchmark harness. Negative values are regressions.

| Case | Before us | After us | Paired reduction |
| --- | ---: | ---: | ---: |
| `python.align_timestamps` | 28.356 | 24.590 | +13.19% |
| `python.ema` | 928.708 | 917.502 | +1.15% |
| `python.ema.small` | 2.483 | 2.466 | -0.19% |
| `python.fir` | 3351.536 | 3066.559 | +8.49% |
| `python.fir.small` | 5.494 | 5.084 | +7.57% |
| `python.history_windows` | 1035.084 | 1035.169 | +0.14% |
| `python.history_windows.small` | 5.389 | 5.350 | +1.02% |
| `python.image_quality` | 343.284 | 343.208 | +0.33% |
| `python.inspect_mcap` | 645.892 | 648.071 | -0.28% |
| `python.inspect_signal` | 924.918 | 899.838 | +2.59% |
| `python.lowpass_taps` | 0.737 | 0.595 | +18.38% |
| `python.read_json_signal` | 937.694 | 923.618 | +1.50% |
| `python.resample.linear` | 242.891 | 235.664 | +2.84% |
| `python.resample.previous` | 161.708 | 158.335 | +1.70% |
| `python.resample.small` | 3.953 | 3.892 | +2.03% |
| `python.resample.strided` | 2092.438 | 653.433 | +68.75% |
| `python.transform_image` | 989.201 | 975.214 | +1.91% |
| `python.uniform_grid` | 170.018 | 162.279 | +4.29% |
| `python.unwrap_angles` | 837.989 | 845.355 | -0.84% |
| `python.unwrap_angles.small` | 1.749 | 1.749 | -0.04% |
| `python.validate_video` | 55402.866 | 55609.379 | -0.42% |

## Verification and limitations

All thirty implementation units completed ten measured candidate rounds. The
final decision count is 23 accepted and 277 rejected; earlier 60- and 20-round
campaigns remain separate and unchanged. Compiler repairs and interrupted runs
were preserved and resumed, not counted as additional completed rounds.

Final validation passed on Linux execution environment: rustfmt, Clippy, 36 Rust tests, five Python smoke
tests, 291 public-interface comparisons, and the immutable-reference oracle.
The oracle covers 180 randomized core scenarios; clock, grid, Hampel and SLERP
edge cases; 6 coefficient extremes; 16 gapped FIR cases; 15 image fixtures and
two MCAP fixtures. PNG outputs are compared by decoded pixels and encoded sizes.
The installed wheel independently passed five tests and 291 interface comparisons.

The full comparison uses 78 native and 21 Python workloads. The original source
at `9de19ea` was rebuilt with the completed native harness, preserving the same
Rust toolchain, thin LTO, one codegen unit and flags on both sides. Python final
timings compare two release wheels with debug information disabled; native
timings retain line tables on both sides. `baseline-manifest.json` records the
immutable source and harness hashes.

Initial integration showed approximately 8% slower previous resampling and
singleton-topic MCAP reading. An independent eight-block repeat found previous
resampling +2.01%, while singleton filtering remained -6.60%. Restricting the
existing topic cache to multiple-topic filters fixes that overhead with one
predicate change. This is a requalification of the retained optimization, not
an extra candidate round. The four raw-reader workloads still clear the gate:
10.78% aggregate latency reduction, 10.26% in the worst paired block; the added
singleton guard measures -0.95%, within the 3% tolerance. See
`raw-reader-requalification.json` and the preserved `integration-*` observations.

The final full run has no native case slower by more than 3%; its lowest result
is SLERP at -2.91%. The lowest Python result is angle unwrapping at -0.84%.
These are measured variations, not speedup claims. Positive results vary by
workload: the sparse alignment and random-Hampel cases benefit much more than
already cheap dense or constant-input paths.

The release wheel targets Linux x86-64 / glibc 2.39+ with CPython abi3 (3.10+),
and was executed with CPython 3.12.3 / NumPy 2.5.4. Source and wheel hashes are
recorded in `verification.json`. No runtime dependencies, public processing
signatures, source-data transformations or relaxed validation checks were added.

Limits: all data was generated. No real recording, upstream LeTools/providers
pipeline, GPU path, multi-worker throughput or non-Linux execution environment platform was benchmarked.
The Python bindings still hold the GIL. Callgrind/cProfile supplied profiling
evidence; their instrumented times were not used as benchmark results.
