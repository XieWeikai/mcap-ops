#!/bin/sh
# Run in the configured Linux test environment after all 300 decisions and the final source review.
set -eu
cd -- "$(dirname -- "$0")/.."
MCAP_TASK_ROOT="$PWD"
export CARGO_HOME="$PWD/.tools/cargo" RUSTUP_HOME="$PWD/.tools/rustup"
export PATH="$CARGO_HOME/bin:$PATH" VIRTUAL_ENV="$PWD/.venv"
export CARGO_PROFILE_RELEASE_DEBUG=1 CARGO_BUILD_JOBS=12
python3 scripts/report_per_operator.py
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --locked -j 12
python3 scripts/prepare_reference.py
CARGO_PROFILE_RELEASE_DEBUG=0 CARGO_TARGET_DIR="$PWD/target/reference" cargo run --offline --release --manifest-path .artifacts/rsi/validation/Cargo.toml -j 12
.venv/bin/maturin develop --release --locked
.venv/bin/python -m pytest -q tests
mkdir -p docs/performance/per-op10/final .artifacts/rsi/per-op10/baseline-wheel .artifacts/rsi/per-op10/wheel
python3 scripts/prepare_campaign_baseline.py
CARGO_TARGET_DIR="$PWD/target/campaign-baseline" cargo build --locked --release --manifest-path .artifacts/rsi/per-op10/baseline/Cargo.toml -p mcap-ops-io --example operator_benchmark -j 12
cp target/campaign-baseline/release/examples/operator_benchmark .artifacts/rsi/per-op10/final-before
cargo build --locked --release -p mcap-ops-io --example operator_benchmark -j 12
cp target/release/examples/operator_benchmark .artifacts/rsi/per-op10/final-after
python3 scripts/rsi_measure.py --before .artifacts/rsi/per-op10/final-before --after .artifacts/rsi/per-op10/final-after --output docs/performance/per-op10/final/native.json
(
    cd .artifacts/rsi/per-op10/baseline
    CARGO_PROFILE_RELEASE_DEBUG=0 CARGO_TARGET_DIR="$MCAP_TASK_ROOT/target/campaign-baseline" "$MCAP_TASK_ROOT/.venv/bin/maturin" build --release --locked --out "$MCAP_TASK_ROOT/.artifacts/rsi/per-op10/baseline-wheel"
)
CARGO_PROFILE_RELEASE_DEBUG=0 .venv/bin/maturin build --release --locked --out .artifacts/rsi/per-op10/wheel
.venv/bin/python - <<'PY'
from pathlib import Path
import zipfile
root=Path('.artifacts/rsi/per-op10')
for folder,output in [('baseline-wheel','final-python-before'),('wheel','final-python-after')]:
    wheels=list((root/folder).glob('*.whl'));assert len(wheels)==1,wheels
    with zipfile.ZipFile(wheels[0]) as archive:archive.extractall(root/output)
PY
.venv/bin/python scripts/check_python_equivalence.py --before .artifacts/rsi/per-op10/final-python-before --after .artifacts/rsi/per-op10/final-python-after
python3 scripts/rsi_measure.py --before .artifacts/rsi/per-op10/final-python-before --after .artifacts/rsi/per-op10/final-python-after --output docs/performance/per-op10/final/python.json
.tools/wheel-check/bin/python -m pip install --force-reinstall --no-deps .artifacts/rsi/per-op10/wheel/*.whl
.tools/wheel-check/bin/python -m pytest -q tests
.venv/bin/python scripts/check_python_equivalence.py --before .artifacts/rsi/per-op10/final-python-before --after .tools/wheel-check/lib/python3.12/site-packages
.venv/bin/python - <<'PY'
import hashlib,json,pathlib,platform,subprocess
import numpy
root=pathlib.Path.cwd();wheel=next((root/'.artifacts/rsi/per-op10/wheel').glob('*.whl'))
paths=subprocess.check_output(['git','ls-files','crates/core/src','crates/io/src','crates/python/src','python/mcap_ops'],text=True).splitlines()
report={'baseline':'9de19ead5df7444a9074c71028129b88970ba6ba','environment':'Linux x86-64 reference environment','platform':platform.platform(),
 'python':platform.python_version(),'numpy':numpy.__version__,'rustc':subprocess.check_output(['rustc','--version'],text=True).strip(),
 'rust_tests':36,'python_tests':5,'public_interface_comparisons':291,
 'reference_oracle':'180 randomized core scenarios, original image/MCAP fixtures, clock/grid/Hampel/SLERP edges, coefficient extremes, gapped FIR and large images',
 'native_profile':'release, thin LTO, one codegen unit, debug line tables on both sides',
 'python_profile':'release wheels, thin LTO, one codegen unit, debug disabled on both sides',
 'wheel':{'path':str(wheel.relative_to(root)),'bytes':wheel.stat().st_size,'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest()},
 'source_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in paths}}
(root/'docs/performance/per-op10/final/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
PY
