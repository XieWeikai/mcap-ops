# Campaign: <unique-series>

**Language: English | [Chinese](../zh/templates/campaign.md)**

Status: planned | running | completed | stopped

## Frozen scope

- Request/date and owner:
- Baseline commit and tree:
- Immutable correctness reference:
- Operator units / requested decisions / stop condition:
- Public callers, contracts and owned source paths:
- Prior successes, failures and counterexamples consulted:
- Non-goals and limits:

## Environment and workloads

- CPU model/topology / affinity / OS / opaque run ID:
- Rust / Cargo.lock hash / build flags:
- Python / NumPy / FFmpeg / profile tools:
- Benchmark harness commit / fixture hashes and seeds:
- Fixed cases (include small, common, large, gapped and adversarial):
- Timing boundary, allocations and output destruction:
- Cold/warm IO, temporary memory and output-size budget:
- Baseline binary / extension SHA-256 and retained location:

## Gates (do not weaken after observing results)

- >=4 alternating AB/BA blocks; >=7 calibrated samples per side.
- Every block geometric-mean latency reduction >=8%.
- Every representative case paired median reduction >=-3%.
- Public correctness and explicit float tolerances:
- Complexity budget and prohibited semantic changes:
- PNG candidates: identical decoded pixels, largest measured size ratio <=1.25.
- One independent eight-block confirmation rule and trigger, if applicable:

## Final delivery

- Rebuild baseline with final identical harness:
- Full native / Python comparison:
- Installed release wheel validation and matching timed binary:
- Results / rejected patches / history / profile identities / lessons:
- Accepted commit list / local-remote tree agreement:
- Untested scope and known limitations:
