# Performance Environment and Evidence

**Language: English | [Chinese](zh/performance.md)**

[Documentation](README.md) · [RSI protocol](../RSI/README.md)

## Reference environment, not a deployment address

| Dimension | Recorded benchmark condition |
| --- | --- |
| Architecture / OS | Linux x86-64, kernel 6.11, glibc 2.39 |
| CPU | Intel Core i9-14900K, 32 logical threads |
| Affinity | One fixed performance-core logical CPU; historical runs used CPU index 12 |
| Rust | 1.90.0, release, thin LTO, one codegen unit, unchanged lockfile/flags |
| Python / NumPy | CPython 3.12.3 / NumPy 2.5.4 |
| Native profiles | Release artifacts retaining debug line tables on both sides |
| Final Python timing | Two release wheels with debug information disabled on both sides |
| Profiling | Callgrind and cProfile; instrumented times excluded from timing claims |
| Data | Generated fixtures; repeated file reads are not a cold-storage throughput claim |
| Scheduling | Serial trials, no competing benchmark on the pinned CPU |

CPU indices are not portable topology labels. Check the target CPU topology
before choosing affinity. No GPU acceleration was used. Hardware counters were
restricted in the reference environment; the workflow did not change global
permissions to obtain them.

## Reading the results

| Campaign | Decisions | Accepted / rejected | Detailed record |
| --- | ---: | ---: | --- |
| Initial | 60 | 27 / 33 | [Results](performance/RESULTS.md) |
| Follow-up | 20 | 7 / 13 | [Results](performance/extension/RESULTS.md) |
| Per-operator ten rounds | 300 | 23 / 277 | [Results](performance/per-op10/RESULTS.md) |

Results express paired latency reduction, not throughput gain. Each candidate
compares with the last accepted state. Final campaign comparisons rebuild the
starting implementation with the same completed harness. Do not add candidate
percentages or mix baselines.

Each acceptance requires at least four alternating AB/BA blocks, seven calibrated
samples per side, at least 8% geometric-mean latency reduction in every block,
no representative-case median regression above 3%, and passing correctness,
resource, and complexity review. PNG candidates additionally preserve decoded
pixels and cap measured output growth at 1.25x.

## Counterexamples are part of the result

The follow-up campaign withdrew FIR transposition after short kernels and gaps
revealed regressions. The later campaign discovered singleton-topic overhead in
a reader cache, then requalified a bounded fix. The archive retains initial
observations, independent repeats, rejected patches, and final conclusions.
See the bilingual [evidence index](../RSI/evidence.md) rather than reading only
positive headline numbers.

The latest full comparison covers 78 native and 21 Python workloads. Its lowest
native reduction is -2.91%, and lowest Python reduction is about -0.84%.
These are measured variations, not improvements. The final installed wheel
passed five API smoke tests and 291 interface comparisons; subsequent workflow
tests do not retroactively change that historical count.

## Shared evidence and limitations

Raw JSON, patches, logs, and generated reports are shared artifacts, not
independent English/Chinese measurements. Both language guides point to the
same numbers and hashes. Historical reports retain original baselines and
experiment identities. Translated narrative must not invent additional runs.

Large profiles and wheels remain in the artifact store, not the Git checkout.
The final wheel targets Linux x86-64 / glibc 2.39+ with CPython abi3 3.10+;
execution was verified on Python 3.12. No real recording, upstream pipeline,
GPU path, multi-worker scaling, or other-platform performance was established.
Python bindings still hold the GIL.
