# mcap-ops

An independent Rust library and NumPy-compatible Python package for MCAP quality
inspection, signal selection, temporal alignment, resampling, and media checks.
No ROS installation, robot controller, dataset writer, cloud service, or GPU is
required for the numeric operators.

The public layers are:

- `mcap-ops-core`: arrays, timestamps, quality events, sampling and provenance.
- `mcap-ops-io`: MCAP and media adapters, separate from numeric semantics.
- `mcap_ops`: Python bindings to the same Rust implementation.

See [architecture](docs/architecture.md) for the contracts,
[operators](docs/operators.md) for implemented Rust functionality, and
[Python interface](docs/python.md) for the exported Python functions.

The first release is validated on `reference-linux`. The
[RSI report](docs/performance/RESULTS.md) covers two candidate rounds for every
processing operator, accepted optimization commits, rejected patches, paired
measurements and correctness evidence. Benchmarks use generated fixtures.
The [twenty-round follow-up](docs/performance/extension/RESULTS.md) builds on that
evidence, includes workload sensitivity checks, and preserves withdrawn results.

All builds and tests run on reference-linux. Synchronize source paths with
`python3 scripts/sync_sources.py`; after committing a reviewed tree, use
`python3 scripts/publish_remote.py` to publish its verified fast-forward Git bundle.
The publication tool checks every tracked file hash before advancing the remote
branch and preserves divergent history by refusing to overwrite it.

Existing third-party showcase material in this directory is ignored by Git and
is not part of this project's source, license, or distribution.
