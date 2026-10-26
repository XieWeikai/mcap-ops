# Ten rounds per operator

**160/300 measured decisions; 16 accepted, 144 rejected.**

Baseline source: `9de19ead5df7444a9074c71028129b88970ba6ba`. Builds, profiles, tests and timing run only on reference-linux. Results use generated fixtures, CPU 12 affinity, four AB/BA paired blocks and seven calibrated samples per side.

Acceptance requires >=8% latency reduction in every aggregate block, no representative case slower by >3%, correctness and complexity checks passing. PNG encoder choices additionally preserve decoded pixels and cap measured output growth at 1.25x.

Retained production diff: 3 files, +112/-62 lines (net +50); pending candidates are excluded.

| Operator | Completed | Accepted |
| --- | ---: | ---: |
| `align_timestamps` | 10/10 | 1 |
| `ema` | 10/10 | 1 |
| `expand_batch_timestamps` | 10/10 | 0 |
| `fir` | 10/10 | 1 |
| `gate` | 0/10 | 0 |
| `history_windows` | 0/10 | 0 |
| `image_decode` | 0/10 | 0 |
| `image_quality` | 0/10 | 0 |
| `image_transform` | 0/10 | 0 |
| `inspect_signal` | 0/10 | 0 |
| `inspect_time` | 10/10 | 0 |
| `interval_affected_centers` | 10/10 | 2 |
| `interval_contains` | 10/10 | 0 |
| `interval_difference` | 10/10 | 1 |
| `interval_intersection` | 10/10 | 0 |
| `interval_mask` | 10/10 | 2 |
| `interval_new` | 10/10 | 2 |
| `json_decode` | 0/10 | 0 |
| `lowpass_taps` | 10/10 | 2 |
| `map_clock` | 10/10 | 1 |
| `mcap_inspect` | 0/10 | 0 |
| `mcap_read_signal` | 0/10 | 0 |
| `python_bridge` | 0/10 | 0 |
| `raw_reader` | 0/10 | 0 |
| `require_strict` | 10/10 | 2 |
| `resample` | 0/10 | 0 |
| `uniform_grid` | 10/10 | 1 |
| `unwrap_angles` | 10/10 | 0 |
| `video_probe` | 0/10 | 0 |
| `video_validate` | 0/10 | 0 |

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
