# Prior Experiments and Evidence

**Language: English | [Chinese](zh/evidence.md)**

[Overview](README.md) · [Workflow](workflow.md)

## Three preserved campaigns

| Series | Baseline | Decisions | Final accepted / rejected | Report |
| --- | --- | ---: | ---: | --- |
| initial | 66248dac | 60 | 27 / 33 | [Initial results](../docs/performance/RESULTS.md) |
| extension | bc58f81b | 20 | 7 / 13 | [Follow-up results](../docs/performance/extension/RESULTS.md) |
| per-op10 | 9de19ead | 300 | 23 / 277 | [Ten rounds per unit](../docs/performance/per-op10/RESULTS.md) |

The 30 implementation units include interval methods, IO, and the Python bridge;
they are not 30 Python functions. There are 380 completed decisions. Interrupted
runs, compile repairs, confirmations, and integration corrections are not extra
candidate rounds. Per-candidate percentages cannot be added together.

Archived IDs resolve through the [publication mapping](../docs/publication.md).
Published logs have redacted deployment metadata and corresponding updated hashes;
measurements and decisions are unchanged.

## Lessons for the next experiment

| Lesson | Evidence / counterexample |
| --- | --- |
| Eliminate repeated work before changing syntax | Hampel reused ordered windows/deviations; see per-op10 results |
| Skip irrelevant prefixes in ordered data | Sparse matching improved, but dense cases must remain guards |
| Account for small-input cache overhead | Reader cache hurt singleton topics; [requalification](../docs/performance/per-op10/final/raw-reader-requalification.json) |
| Aggregate wins cannot hide common-case losses | Clock drift improved while offset-only regressed; [extension 12](../docs/performance/extension/results/extension-12-map-clock.json) |
| Preparation belongs inside call cost | FIR transposition helped long kernels but lost on short/gapped inputs; [history](../docs/performance/extension/history) |
| Branchless/iterator/in-place is not automatically faster | Rejected patches preserve failed loop and representation alternatives |
| Reuse established ownership | Move output buffers and handle strided arrays without losing snapshots or logical order |
| Mature media-library tuning often misses the gate | Failed image/video candidates remain recorded; output growth is not a free speed tradeoff |
| Time the delivered artifact | [Full native](../docs/performance/per-op10/final/native.json), [release Python](../docs/performance/per-op10/final/python.json) |

The singleton-topic regression appeared in integration and an independent repeat.
A one-predicate correction kept direct matching for zero/one topic and caching
for multiple topics. Original regressions remain in final/integration-*; commit
f2813d9 requalified the retained optimization rather than inventing another round.

## Evidence layout

```text
docs/performance/<series>/
  PLAN.md              Frozen scope, environment, gates
  RESULTS.md           Decisions and integrated comparison
  LESSONS.md           Successes, failures, withdrawals, applicability
  results/<label>.json Decision, hotspot, complexity, baseline, hashes
  data/<label>.json    Raw samples per block/side/case and paired statistics
  rejected/*.patch    Implementations not retained
  history/             Earlier decisions, confirmations, counterevidence
  evidence/            Validation logs, profile summaries and identities
  final/               Integration, artifact/source identities, limitations

.artifacts/rsi/trials/<label>/    Working artifacts, excluded from Git
  before/                       Owned-path baseline snapshots
  candidate.patch               Validated candidate diff
  before.callgrind / *.prof      Large original profiles
  measurement.json / audit.json Timing and machine gate
  validation.log                Complete validation output
  attempts/                     Interrupted/failed attempts
  commit-message.txt            Prepared acceptance commit message
```

Initial results/data live directly under docs/performance; later series use
subdirectories. A profile hash is not the profile itself. Cloning gives archived
summaries and identities; complete large profiles require the artifact store or
regeneration. New evidence uses repository-relative locations, not deployment paths.

## Scripts and limitations

| Tool | Where it runs | Responsibility / limitation |
| --- | --- | --- |
| sync_sources.py | Authoring checkout | Relative-path sync; inspect remote worktree first |
| rsi_trial.py | Authoring, dispatch to execution | Snapshot, correctness, profile, paired timing, audit; new series supported |
| rsi_decide.py | Authoring | Decision; accepted commit text or guarded owned-path restore |
| rsi_measure.py | Execution | Timing and artifact identity; not complete acceptance review |
| prepare_reference.py | Execution | Immutable-reference workspace from fixed history |
| check_python_equivalence.py | Execution | Public interfaces of two real package snapshots |
| archive_extension_evidence.py | Authoring | Logs/profile identities for new series; legacy initial layout differs |
| Historical batch runners | Authoring | Fixed candidate lists, not generic campaign definitions |
| report_rsi / report_extension / report_per_operator | Execution audit | Fixed historical baselines/counts; write their report files |
| verify_extension.sh / verify_per_operator.sh | Execution | Historical final checks; do not overwrite old evidence for new work |
| publish_remote.py | Authoring | Configured-target Git bundle, hashes, fast-forward publication |

Candidate definitions live in [benchmarks/ten_rounds](../benchmarks/ten_rounds);
[coverage.json](../docs/performance/per-op10/coverage.json) records all 300 decisions.
Use trial/decide/archive for new series. New bulk scheduling/reporting must define
its own baseline and scope rather than editing historical targets to claim completion.

## Acceptance commit contents

```text
perf(operator): concrete change [RSI series round N]

Profile: measured hotspot and source profile
Change: redundant work removed
Complexity: branches, memory, dependencies, maintenance
Environment: CPU / OS / toolchain / flags / fixture identity
Paired blocks: count, samples per side, order
Aggregate reduction: median and worst block
case: before ns/op -> after ns/op; paired reduction
Correctness: exact commands, outcomes, tolerances
Resources: measured or bounded costs; PNG ratio if applicable
Decision: why every gate passes
Evidence: results/<label>.json and data/<label>.json
```

Each commit binds its own evidence; add final commit hashes to the report.
Scaffolding, documentation, correctness fixes, and integration requalification
are distinct from a new optimization candidate.
