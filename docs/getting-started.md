# Getting Started

**Language: English | [Chinese](zh/getting-started.md)**

[Documentation](README.md) · [Python API](python.md) · [Rust API](rust.md)

## Environment

| Component | Requirement or verified scope |
| --- | --- |
| Python | Package requirement: >=3.10; verified with CPython 3.12.3 |
| NumPy | Package requirement: >=1.24; final campaign used 2.5.4 |
| Rust | 1.90.0, pinned in `rust-toolchain.toml` |
| Python build | maturin >=1.9,<2; a working native compiler/linker |
| MCAP and images | Implemented through Rust dependencies; ROS is not required |
| Video | Caller-installed `ffmpeg` and `ffprobe`; explicit executable paths are supported |
| Verified wheel | Linux x86-64 / glibc 2.39+, `cp310-abi3`; macOS/Windows are not verified |

No package has been published to PyPI or crates.io. Do not assume a similarly
named registry package is this implementation. Keep full Git history when
cloning: the RSI reference oracle materializes an older commit.

Maintainers author locally and execute builds/tests in a separate configured
Linux environment, using project-local tools. The commands below run at the
repository root on the chosen build environment; external users can build in
their own controlled environment.

## Python from source

Make Rust 1.90.0 available, then run:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install "maturin>=1.9,<2" "numpy>=1.24" "pytest>=8"
.venv/bin/maturin develop --release --locked
.venv/bin/python examples/quickstart.py
.venv/bin/python -m pytest -q tests
```

Expected example output:

```text
linear: [0.0, 0.5, 1.0, 1.5, 2.0]
previous: [0.0, 0.0, 1.0, 1.0, 2.0]
quality: [('above_range', 1)]
history shape: (1, 3, 1)
```

The [example](../examples/quickstart.py) uses generated arrays and assertions;
it does not read recordings or start services.

## Build and install a wheel

```bash
.venv/bin/maturin build --release --locked --out dist
python3 -m venv .tools/consumer
.tools/consumer/bin/python -m pip install dist/*.whl
.tools/consumer/bin/python examples/quickstart.py
```

Keep only the intended wheel in `dist/`. The platform tag depends on the build
environment. The historical verified wheel is retained in the artifact store
under `.artifacts/rsi/per-op10/wheel/`; it is not tracked by Git and has not been
published as a release attachment.

## Rust dependencies

In the consuming project's `Cargo.toml`, adapt these paths to your checkout:

```toml
[dependencies]
mcap-ops-core = { path = "../mcap-ops/crates/core" }
mcap-ops-io = { path = "../mcap-ops/crates/io" }
```

Array-only applications need only core. Run the complete repository example:

```bash
cargo run --locked --release -p mcap-ops-core --example quality_pipeline
```

It combines inspection, gating, interval selection, and resampling through
public interfaces. See the [Rust guide](rust.md) and
[example source](../crates/core/examples/quality_pipeline.rs).

## Troubleshooting

| Symptom | Check |
| --- | --- |
| `No module named mcap_ops._native` | Build/install the native extension into the interpreter you are running |
| dtype error | Use `np.int64` timestamps and `np.float64` values; input dtypes are not implicitly converted |
| Noncontiguous timestamps | Use `np.ascontiguousarray(times, dtype=np.int64)`; values may be strided |
| Mostly invalid outputs | Verify units, clock source, age/gap limits, and future-support policy |
| Source timestamps must be strictly increasing | Inspect first; resolve duplicates/reversals through an explicit upstream policy |
| Unknown CDR/Protobuf encoding | Supply a schema adapter; container inspection does not imply numeric decoding |
| FFmpeg missing or failing | Check executable availability and decoding; an unavailable tool is not a quality pass |
| Linux wheel rejected on macOS | Build and verify for the target platform; the existing wheel is Linux-specific |

Next: [prepare a multi-signal pipeline](guides/pipeline.md).
