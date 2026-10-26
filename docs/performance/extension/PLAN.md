# Twenty further RSI experiments

Baseline: `bc58f81bb2c3dc43676450ee6685d8015fb99081` (the complete first 60 decisions).
Requested 2026-10-26, Asia/Shanghai. This series contains **twenty additional
candidate experiments in total**, numbered 1–20, rather than twenty per operator.

The original records, failed patches, and timings remain immutable. Every new
recipe in `benchmarks/candidates_extension.py` states the earlier lesson it uses.
The accepted implementation is the next experiment's baseline; rejected changes
are restored. The unchanged acceptance gate requires 8% latency reduction in
every one of four AB/BA aggregate blocks, no per-case median regression over 3%,
all correctness checks passing, and a small, reviewable implementation.

All builds, tests, profiles and benchmarks execute on reference-linux with project-local
tools. CPU affinity, build flags, fixture generation, calibration and numerical
tolerances follow [the existing protocol](../RSI.md). Native candidates retain
both before/after Callgrind profiles, Python candidates cProfile snapshots.
Profiler timing is not benchmark evidence. No real recordings or services are used.

The 20 candidate hypotheses, in execution order:

1. FIR checked support slices instead of repeated row slicing.
2. FIR channel planes for contiguous dot products, preserving summation order.
3. Monotone Hampel window bounds instead of repeated binary searches.
4. Merge absolute deviations from sorted values instead of a second sort.
5. Bounded row iteration for channel statistics, preserving Welford arithmetic.
6. Zipped Laplacian stencil rows with the same operation order.
7. Exact 8-bit luminance contribution tables.
8. Conditional disjoint-prefix search for interval intersection.
9. Merge intervals inside their owned input allocation.
10. Zip alignment outputs to remove separate output indexing.
11. Compute exact bounded grid capacity.
12. Checked narrow clock-drift correction with wide fallback and exact ties.
13. Branchless reduction of timestamp order violations.
14. Checked batch expansion inside a copied offsets buffer.
15. Sort history requests by time without redundant destination tie keys.
16. Guard FIR channel-plane preparation by kernel length and complete support.
17. Fuse EMA input finite checks and updates.
18. Move owned Signal buffers into NumPy rather than clone them.
19. Partial selection for nonuniform time quantiles.
20. Zip input and accumulated rows during angle unwrapping.

Each accepted experiment gets its own performance commit with before/after
numbers, method, prior lesson and correctness evidence. Rejections retain their
patches and measurements without changing production code. Final combined
benchmarks include unchanged paths, so cumulative regressions cannot be hidden.

After round 15, the independent sensitivity suite exposed short-kernel and
invalid-support regressions in round 2. Its acceptance was withdrawn; original
evidence remains in `history/`. Round 16 was adapted from the not-yet-executed
SLERP reciprocal hypothesis to a guarded FIR hypothesis with an additional
no-regression sensitivity gate. This is still twenty candidate experiments.
