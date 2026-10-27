# Documentation

**Language: English | [Chinese](zh/README.md)**

[Project overview](../README.md) · [RSI playbook](../RSI/README.md)

## Use the library

| Guide | What it covers |
| --- | --- |
| [Getting started](getting-started.md) | Installation, platform requirements, runnable examples, Rust dependencies |
| [Multi-signal pipeline](guides/pipeline.md) | Inspection, synchronization, history windows, model inputs |
| [MCAP and media](guides/media.md) | JSON extraction, schema adapters, images, video validation |
| [Python API](python.md) | All 14 processing functions, signatures, return types, defaults, errors |
| [Rust API](rust.md) | Modules, types, quality gates, intervals, decoder extension points |
| [Operator catalog](operators.md) | Implemented capabilities and Python/Rust availability |

## Understand or extend it

| Guide | What it covers |
| --- | --- |
| [Architecture](architecture.md) | Design principles, dependencies, ownership, upstream responsibilities |
| [Data contracts](concepts.md) | Signals, clocks, quality evidence, shapes, validity, causality, provenance |
| [Contributing](contributing.md) | Separate authoring/execution environments, tests, examples, synchronization |
| [Performance evidence](performance.md) | Benchmark environment, acceptance criteria, interpreting the archive |
| [RSI workflow](../RSI/workflow.md) | Exploration through profiling, verification, measurement, and commit |

Every maintained guide and RSI template has a matching Chinese page, linked at
the top. Raw measurements, patches, logs, and generated historical reports are
shared evidence, not separate language-dependent datasets. The bilingual
[performance guide](performance.md) and [RSI evidence index](../RSI/evidence.md)
explain how to read them.

## Historical campaigns

| Campaign | Decisions | Accepted / rejected | Evidence |
| --- | ---: | ---: | --- |
| Initial two rounds per unit | 60 | 27 / 33 | [Report](performance/RESULTS.md) |
| Twenty follow-up experiments | 20 | 7 / 13 | [Report](performance/extension/RESULTS.md) |
| Ten more rounds per unit | 300 | 23 / 277 | [Report](performance/per-op10/RESULTS.md) |

There are 380 recorded decisions. Counts use the final decisions; read
`history/` and `final/` for withdrawals, independent repeats, and integration
corrections. Do not add individual percentages to estimate total speedup.

These guides describe the actual 0.1.0 interface. New experiments use new
records. Large raw profiles are kept in the experiment artifact store; Git
contains logs, summaries, identities, and evidence references.
