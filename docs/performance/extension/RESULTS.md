# Twenty additional RSI experiments

Completed **20/20**: **7 accepted**, **13 rejected**. The original 60 decisions are preserved, for 80 total experiments.

Baseline: `bc58f81bb2c3dc43676450ee6685d8015fb99081`. All execution on reference-linux, i9-14900K, CPU 12, Rust 1.90, release with unchanged flags. Every trial used generated inputs, before/after profiles, four alternating AB/BA blocks, and seven calibrated samples per side.

Acceptance: every block's geometric-mean latency reduction >=8%, no case's median regression >3%, correctness passed, and bounded implementation complexity. Percentages below compare with the previously accepted state, not the initial repo.

Production diff for this extension: 7 files, +98/-27 lines (net +71). No runtime dependency or build-flag changes.

| Round | Operator and hypothesis | Decision | Paired reduction | Worst block | Commit |
| ---: | --- | --- | ---: | ---: | --- |
| 1 | `fir`: dot FIR taps against checked strided support slices | [rejected](results/extension-01-fir.json) | -461.25% | -480.17% | `-` |
| 2 | `fir`: transpose FIR input once into contiguous channel planes | [rejected](results/extension-02-fir.json) | +33.96% | +32.45% | `-` |
| 3 | `inspect_signal`: advance Hampel window bounds with monotone cursors | [rejected](results/extension-03-inspect-signal.json) | +7.72% | +7.49% | `-` |
| 4 | `inspect_signal`: merge ordered absolute deviations through their median | [accepted](results/extension-04-inspect-signal.json) | +41.08% | +40.95% | `ec10cbff` |
| 5 | `inspect_signal`: iterate bounded signal rows for channel statistics | [rejected](results/extension-05-inspect-signal.json) | +2.57% | +2.36% | `-` |
| 6 | `image_quality`: zip bounded image rows for Laplacian stencils | [accepted](results/extension-06-image-quality.json) | +10.25% | +9.54% | `c8094d1b` |
| 7 | `image_quality`: tabulate exact eight-bit luminance contributions | [rejected](results/extension-07-image-quality.json) | +2.31% | +1.07% | `-` |
| 8 | `interval_intersection`: skip disjoint initial interval prefixes conditionally | [accepted](results/extension-08-interval-intersection.json) | +88.29% | +86.08% | `3965a5f6` |
| 9 | `interval_new`: merge sorted intervals in their owned input allocation | [rejected](results/extension-09-interval-new.json) | -6.41% | -7.08% | `-` |
| 10 | `align_timestamps`: zip alignment output buffers with target timestamps | [rejected](results/extension-10-align-timestamps.json) | +3.78% | +2.54% | `-` |
| 11 | `uniform_grid`: derive exact bounded grid capacity before generation | [rejected](results/extension-11-uniform-grid.json) | +2.62% | +2.58% | `-` |
| 12 | `map_clock`: round clock drift using checked narrow correction arithmetic | [rejected](results/extension-12-map-clock.json) | +7.43% | -1.84% | `-` |
| 13 | `require_strict`: reduce timestamp order violations without early branches | [rejected](results/extension-13-require-strict.json) | -68.42% | -87.44% | `-` |
| 14 | `expand_batch_timestamps`: update copied batch offsets through mutable slices | [accepted](results/extension-14-expand-batch-timestamps.json) | +33.96% | +33.31% | `527209d0` |
| 15 | `history_windows`: sort history requests by timestamp without redundant tie keys | [rejected](results/extension-15-history-windows.json) | +2.73% | +2.17% | `-` |
| 16 | `fir`: transpose only long FIR kernels with complete regular support | [rejected](results/extension-16-fir.json) | +32.07% | +31.32% | `-` |
| 17 | `ema`: fuse EMA finite-input checks into output updates | [accepted](results/extension-17-ema.json) | +15.07% | +14.65% | `c703007c` |
| 18 | `python_bridge`: move owned signal buffers into NumPy without cloning | [accepted](results/extension-18-python-bridge.json) | +15.21% | +15.02% | `37b2a7a2` |
| 19 | `inspect_time`: select clock quantiles without fully sorting intervals | [rejected](results/extension-19-inspect-time.json) | -35.13% | -35.79% | `-` |
| 20 | `unwrap_angles`: zip disjoint angle rows and accumulated outputs | [accepted](results/extension-20-unwrap-angles.json) | +11.07% | +9.91% | `4cbe3eeb` |

## Prior experience and decisions

**1. dot FIR taps against checked strided support slices** — Performance gate failed; restore previous accepted implementation. Earlier channel-inner accumulation regressed 26%; retain channel-outer summation and remove repeated row slicing instead.

**2. transpose FIR input once into contiguous channel planes** — WITHDRAWN after sensitivity validation: short scalar -24.37%, short vector -115.44%, gapped -33.67%; original fixed-case gain did not generalize. Initial acceptance and samples retained in history/extension-02-initial.json and history/sensitivity-initial.json. Restore the prior implementation.

**3. advance Hampel window bounds with monotone cursors** — Performance gate failed; restore previous accepted implementation. Scratch reuse helped; wide quickselect was unstable. Remove two binary searches per sample without changing the median algorithm.

**4. merge ordered absolute deviations through their median** — All paired blocks clear 8%, no case regresses more than 3%, correctness passes. The first median sorts already; exploit that order instead of repeating the previously rejected quickselect hypothesis.

**5. iterate bounded signal rows for channel statistics** — Performance gate failed; restore previous accepted implementation. Keep Welford arithmetic and issue order; scratch and disabled-check work already removed.

**6. zip bounded image rows for Laplacian stencils** — All paired blocks clear 8%, no case regresses more than 3%, correctness passes. Two-pass moments helped; preserve those arithmetic orders while reducing per-pixel stencil indexing.

**7. tabulate exact eight-bit luminance contributions** — Performance gate failed; restore previous accepted implementation. Avoid reduced precision or approximate statistics; each 256-entry table uses the same f64 multiply as the old pixel loop.

**8. skip disjoint initial interval prefixes conditionally** — All paired blocks clear 8%, no case regresses more than 3%, correctness passes. Unconditional prefix search improved late overlap but regressed dense overlap 13%; guard searches on disjoint first pairs.

**9. merge sorted intervals in their owned input allocation** — Performance gate failed; restore previous accepted implementation. Reserve and sortedness precheck both failed; avoid the second vector altogether.

**10. zip alignment output buffers with target timestamps** — Performance gate failed; restore previous accepted implementation. Push-based outputs and abs_diff both failed; keep zero-initialized buffers and exact i128 tolerance logic.

**11. derive exact bounded grid capacity before generation** — Performance gate failed; restore previous accepted implementation. Quotient/remainder recurrence was accepted; now remove geometric vector growth without allocating max_points.

**12. round clock drift using checked narrow correction arithmetic** — Performance gate failed; restore previous accepted implementation. Zero-drift fast path helped; preserve wide fallback and away-from-zero tie semantics for actual drift.

**13. reduce timestamp order violations without early branches** — Performance gate failed; restore previous accepted implementation. Zipped adjacency beat windows; keep it and allow SIMD through a non-short-circuit boolean reduction.

**14. update copied batch offsets through mutable slices** — All paired blocks clear 8%, no case regresses more than 3%, correctness passes. Iterator spelling and min/max prescans failed; retain per-element checked addition while removing Vec push bookkeeping.

**15. sort history requests by timestamp without redundant tie keys** — Performance gate failed; restore previous accepted implementation. Deduplication helped; equal-time requests already share one sampled result, so destination tie ordering is unobservable.

**16. transpose only long FIR kernels with complete regular support** — Performance gate failed; restore previous accepted implementation. Round 2 was withdrawn after short-kernel and invalid-support regressions. Preserve the original path for those inputs and require an additional eight-case sensitivity gate.

**17. fuse EMA finite-input checks into output updates** — All paired blocks clear 8%, no case regresses more than 3%, correctness passes. Weight caching and zipped rows succeeded; remove the remaining duplicate input scan while preserving invalid-row reset.

**18. move owned signal buffers into NumPy without cloning** — All paired blocks clear 8%, no case regresses more than 3%, correctness passes. Direct NumPy outputs succeeded; Signal-backed results still clone their owned buffers before transfer. Public result types stay unchanged.

**19. select clock quantiles without fully sorting intervals** — Performance gate failed; restore previous accepted implementation. Uniform fast path helped and is retained; only nonuniform intervals need partial selection.

**20. zip disjoint angle rows and accumulated outputs** — All paired blocks clear 8%, no case regresses more than 3%, correctness passes. Row-major order and modulo bypass helped; retain those and remove repeated channel-index arithmetic.

## Correctness and costs

Each candidate passes rustfmt, Clippy, 36 Rust tests, the immutable-reference differential suite (180 randomized core scenarios, 13 image fixtures, two MCAP fixtures), and five Python tests before timing. The extended oracle adds 3630 clock arithmetic cases, 168 grid cases, 75 Hampel cases and 50 SLERP cases; it was introduced during round 4 and rerun on the final accepted tree. Python bridge changes additionally compare 236 public-interface cases, including output types, dictionary order, strided arrays, errors and non-finite values.

The unconditional FIR channel-plane candidate was withdrawn after additional workloads revealed regressions, even though its original fixed-case gate passed. Its initial acceptance and counterevidence remain in `history/`. The guarded follow-up must pass the extra sensitivity gate; channel planes, when used, need an additional 8*N*D bytes of temporary memory. Sorted MAD adds a small private merge helper and preserves window boundaries, exact medians, issue ordering and overflow behavior. No unsafe buffers, reduced precision, discarded checks, source modifications or external services are involved.

Raw timing samples live in `data/`; rejected patches in `rejected/`. Complete validation logs and before/after profiles live on reference-linux at `.artifacts/rsi/trials/extension-*`. This series uses Callgrind/cProfile because perf_event_paranoid remains 4. Profiler times are excluded from benchmark claims.

## Final native comparison

Extension baseline versus the complete accepted extension; negative values are regressions.

| Case | Before (us) | After (us) | Paired reduction |
| --- | ---: | ---: | ---: |
| `align_timestamps.nearest` | 98.068 | 97.869 | +0.20% |
| `align_timestamps.previous` | 61.038 | 60.632 | +0.39% |
| `ema.jitter` | 469.859 | 411.231 | +12.44% |
| `ema.uniform` | 359.103 | 299.975 | +16.05% |
| `expand_batch_timestamps` | 29.189 | 19.191 | +34.37% |
| `fir.scalar` | 444.940 | 332.792 | +25.20% |
| `fir.vector` | 1858.801 | 1529.320 | +17.65% |
| `gate.fail` | 0.029 | 0.029 | +0.01% |
| `gate.pass` | 0.009 | 0.009 | -1.00% |
| `history_windows.overlap` | 266.901 | 266.948 | +0.18% |
| `history_windows.separate` | 147.886 | 149.804 | -1.36% |
| `image_decode.jpeg` | 575.942 | 566.041 | +1.51% |
| `image_decode.png` | 1442.539 | 1442.541 | -0.05% |
| `image_quality.gradient` | 2843.063 | 2659.753 | +6.46% |
| `image_quality.noise` | 1419.118 | 1232.675 | +13.14% |
| `image_transform.gradient` | 5374.039 | 5374.298 | +0.02% |
| `image_transform.noise` | 3999.249 | 4003.413 | -0.06% |
| `inspect_signal.basic` | 1432.259 | 1434.382 | -0.15% |
| `inspect_signal.hampel` | 6420.407 | 3511.449 | +45.31% |
| `inspect_signal.wide_hampel` | 34862.882 | 12428.945 | +64.36% |
| `inspect_time.jitter` | 84.573 | 84.634 | -0.05% |
| `inspect_time.uniform` | 24.197 | 24.184 | +0.05% |
| `interval_affected_centers` | 5.535 | 5.525 | +0.04% |
| `interval_contains` | 239.578 | 239.379 | +0.11% |
| `interval_difference` | 9.660 | 9.647 | +0.36% |
| `interval_intersection.dense` | 26.928 | 27.737 | -2.99% |
| `interval_intersection.late` | 12.454 | 0.165 | +98.68% |
| `interval_mask.ordered` | 24.599 | 24.733 | -0.58% |
| `interval_mask.shuffled` | 257.833 | 258.780 | -0.55% |
| `interval_new` | 8.348 | 8.462 | -1.26% |
| `json_decode` | 0.203 | 0.204 | -0.39% |
| `lowpass_taps` | 0.375 | 0.374 | +0.04% |
| `map_clock.drift` | 150.024 | 149.902 | +0.05% |
| `map_clock.offset` | 31.836 | 37.553 | -21.90% |
| `mcap_inspect` | 1674.668 | 1679.954 | -0.55% |
| `mcap_read_signal` | 5768.385 | 5875.245 | -2.14% |
| `raw_reader.chunked` | 1279.619 | 1279.677 | +0.06% |
| `raw_reader.linear` | 1606.562 | 1600.891 | +0.19% |
| `raw_reader.topics` | 1402.267 | 1502.114 | -7.28% |
| `require_strict` | 11.616 | 11.615 | -0.03% |
| `resample.linear` | 394.204 | 395.926 | -0.28% |
| `resample.nearest` | 236.375 | 239.104 | -0.88% |
| `resample.previous` | 207.209 | 211.713 | -1.41% |
| `resample.slerp` | 539.512 | 540.141 | -0.12% |
| `uniform_grid.integer` | 70.522 | 70.492 | +0.03% |
| `uniform_grid.rational` | 2.190 | 2.190 | -0.02% |
| `unwrap_angles` | 399.201 | 355.554 | +10.77% |
| `video_probe` | 22866.707 | 23071.778 | -1.40% |
| `video_validate` | 49269.170 | 49012.027 | +0.55% |

## Final python comparison

Extension baseline versus the complete accepted extension; negative values are regressions.

| Case | Before (us) | After (us) | Paired reduction |
| --- | ---: | ---: | ---: |
| `python.align_timestamps` | 28.958 | 27.475 | +5.13% |
| `python.ema` | 834.186 | 363.877 | +56.47% |
| `python.fir` | 3072.412 | 3070.440 | +0.07% |
| `python.history_windows` | 383.393 | 383.107 | +0.23% |
| `python.image_quality` | 383.963 | 334.869 | +12.95% |
| `python.inspect_mcap` | 638.584 | 637.461 | +0.18% |
| `python.inspect_signal` | 904.361 | 907.603 | -0.31% |
| `python.lowpass_taps` | 0.719 | 0.705 | +1.76% |
| `python.read_json_signal` | 889.161 | 899.867 | -1.18% |
| `python.resample.linear` | 223.479 | 225.540 | -0.97% |
| `python.resample.previous` | 153.912 | 149.464 | +2.98% |
| `python.transform_image` | 951.364 | 951.265 | -0.03% |
| `python.uniform_grid` | 163.854 | 165.337 | -0.96% |
| `python.unwrap_angles` | 800.395 | 296.976 | +62.93% |
| `python.validate_video` | 48978.330 | 48907.715 | +0.30% |

## Final sensitivity comparison

Extension baseline versus the complete accepted extension; negative values are regressions.

| Case | Before (us) | After (us) | Paired reduction |
| --- | ---: | ---: | ---: |
| `sensitivity.fir.gapped` | 112.620 | 118.385 | -5.35% |
| `sensitivity.fir.short.scalar` | 178.091 | 175.959 | +1.23% |
| `sensitivity.fir.short.vector` | 328.541 | 372.452 | -13.69% |
| `sensitivity.fir.small.scalar` | 0.261 | 0.254 | +2.30% |
| `sensitivity.fir.small.vector` | 0.432 | 0.462 | -7.08% |
| `sensitivity.fir.wide` | 6143.631 | 6166.177 | -0.28% |
| `sensitivity.hampel.constant` | 1891.003 | 1676.837 | +11.41% |
| `sensitivity.hampel.random` | 15757.984 | 10609.203 | +32.65% |

## Final verification notes

All final checks passed on reference-linux: rustfmt, Clippy, 36 Rust tests, 180 randomized
core scenarios, 13 image fixtures, two MCAP fixtures, 3630 clock edge cases,
168 grid cases, 75 Hampel cases, 50 SLERP cases, five Python smoke tests and
236 public-interface comparisons. The installed release wheel separately passed
five tests and 236 interface comparisons. Its SHA-256 is recorded in
`verification.json`; the local download was independently hash-checked.

The final whole-suite timings are not identical to isolated trial timings.
An independent eight-block repeat (`focused-native.json`) found clock offset
effectively unchanged (-0.07%) after -21.90% in the full run. Dense interval
intersection measured -2.59% in that repeat, within the 3% per-case gate; late
intersection remained +98.68%.

**Remaining performance limitations:** raw MCAP topic selection measured
-7.28% in the full run and -8.15% in the focused repeat. Additional FIR workload
checks measured short-vector -13.69%, small-vector -7.08% and invalid-support
-5.35%, although the FIR operator body was restored exactly. The full-suite
31-tap FIR cases went in the opposite direction (+25.20%/+17.65%). No FIR
transposition optimization remains in production.

`unchanged-source.json` verifies that the FIR and map_clock function bodies,
and the entire MCAP adapter source, are byte-identical to the extension baseline.
The eight-block identical-source control (`sensitivity-control.json`) measured
short-vector FIR +0.57% and invalid-support FIR -0.20%; it therefore does not
explain away the final differences. Their cause is not established. They must
remain visible rather than being attributed to an unimplemented FIR optimization
or described as universal speedups. Final acceptance records refer to their
stated operator workloads and gates, not a guarantee across every input shape
or combined binary layout.

The first unconditional FIR acceptance was explicitly withdrawn in commit
`2c913ba`, and its guarded follow-up failed the expanded gate. Original evidence
and the rejected patches are retained. These diagnostic repeats and controls
are validation of the same twenty candidates, not extra optimization rounds.

The wheel targets Linux x86-64 / glibc 2.39+ with CPython abi3 (3.10+).
Execution was verified with CPython 3.12.3 and NumPy 2.5.4. No package was published
to an external registry.
