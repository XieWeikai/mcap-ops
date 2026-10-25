# mcap-ops

An independent Rust library and NumPy-compatible Python package for MCAP quality
inspection, signal selection, temporal alignment, resampling, and media checks.
No ROS installation, robot controller, dataset writer, cloud service, or GPU is
required for the numeric operators.

The public layers are:

- `mcap-ops-core`: arrays, timestamps, quality events, sampling and provenance.
- `mcap-ops-io`: MCAP and media adapters, separate from numeric semantics.
- `mcap_ops`: Python bindings to the same Rust implementation.

See [architecture](docs/architecture.md) for the contracts and implementation
plan. The first release is being implemented and validated on `reference-linux`; no
operation should be assumed implemented until listed in the operator reference.

Existing third-party showcase material in this directory is ignored by Git and
is not part of this project's source, license, or distribution.
