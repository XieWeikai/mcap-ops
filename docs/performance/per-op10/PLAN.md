# Ten new rounds per operator

Requested 2026-10-26 (Asia/Shanghai). Baseline source `9de19ea`.
Thirty existing implementation units each receive ten new candidate experiments:
**300 additional decisions**, independent of the prior 80 records.

Each round is a small implementation change measured against the most recently
accepted state. Compatible transformations reuse accepted changes; incompatible
algorithm/parameter alternatives start from the frozen operator body. Unrelated
operators retain their accepted changes. Alternatives include algorithms,
buffer capacities, loop blocking, library interface choices and inlining policy.
Parameter sweeps are identified as such; they are not claimed as ten distinct
algorithms. Identical source changes and prior failed patches are not replayed.

All source authoring is local; builds, profiles, correctness tests and timings
run only on reference-linux with project-local tools. Benchmarks are serial on CPU 12.
The Cargo release settings remain thin LTO and one codegen unit. Expanded FIR,
Hampel, alignment and identity-clock workloads use the same benchmark executable
and build settings on both sides, avoiding a separate performance-reference crate.

The existing gate remains: >=8% geometric-mean latency reduction in every one of
four alternating paired blocks, no representative case slower by >3%, correctness
and complexity review passing. Preserve all masks, errors, provenance, limits,
CRC checks, timestamps, shapes and source data. No runtime dependency is added.
PNG encoder alternatives also preserve decoded pixels exactly and may not grow
the largest per-fixture output ratio beyond 1.25x; faster CPU encoding must not
silently impose a large storage/bandwidth cost. Size pairs are recorded with each
encoder decision. Python comparisons include reversed strided views.
Representative fixtures for later operator groups are frozen before those groups
begin. Existing time-group inputs remain unchanged; final whole-campaign comparisons
will rebuild the original source with the completed harness so both sides use
identical fixture and benchmark code.
Each accepted round gets its own commit with exact measurements; rejections keep
their patches and logs. A failed compilation is repaired before timing, not
presented as a measured optimization. Final full-suite and installed-wheel checks
follow the 300 decisions, with local/remote history and file hashes reconciled.
