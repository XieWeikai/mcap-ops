#!/bin/sh
# Invoke only through SSH in the configured Linux test environment, after all twenty source decisions are final.
set -eu
cd -- "$(dirname -- "$0")/.."
export CARGO_HOME="$PWD/.tools/cargo" RUSTUP_HOME="$PWD/.tools/rustup"
export PATH="$CARGO_HOME/bin:$PATH" VIRTUAL_ENV="$PWD/.venv"
export CARGO_PROFILE_RELEASE_DEBUG=1 CARGO_BUILD_JOBS=12
mkdir -p docs/performance/extension/final .artifacts/rsi/extension/final-python .artifacts/rsi/extension/wheel
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --locked -j 12
python3 scripts/prepare_reference.py
CARGO_PROFILE_RELEASE_DEBUG=0 CARGO_TARGET_DIR="$PWD/target/reference" cargo run --offline --release --manifest-path .artifacts/rsi/validation/Cargo.toml -j 12
.venv/bin/maturin develop --release --locked
.venv/bin/python -m pytest -q tests
cargo build --locked --release -p mcap-ops-io --example operator_benchmark -j 12
cp target/release/examples/operator_benchmark .artifacts/rsi/extension/final-native
cp -r python/mcap_ops .artifacts/rsi/extension/final-python/
.venv/bin/python scripts/check_python_equivalence.py --before .artifacts/rsi/extension/python-base --after .artifacts/rsi/extension/final-python
python3 scripts/rsi_measure.py --before .artifacts/rsi/extension/base --after .artifacts/rsi/extension/final-native --output docs/performance/extension/final/native.json
python3 scripts/rsi_measure.py --before .artifacts/rsi/extension/python-base --after .artifacts/rsi/extension/final-python --output docs/performance/extension/final/python.json
python3 scripts/prepare_sensitivity.py
CARGO_TARGET_DIR="$PWD/target/reference" cargo build --offline --release --manifest-path .artifacts/rsi/extension/sensitivity/Cargo.toml -j 12
python3 scripts/rsi_measure.py --before .artifacts/rsi/extension/sensitivity/before --after .artifacts/rsi/extension/sensitivity/after --output docs/performance/extension/final/sensitivity.json
CARGO_PROFILE_RELEASE_DEBUG=0 .venv/bin/maturin build --release --locked --out .artifacts/rsi/extension/wheel
.tools/wheel-check/bin/python -m pip install --force-reinstall --no-deps .artifacts/rsi/extension/wheel/*.whl
.tools/wheel-check/bin/python -m pytest -q tests
WHEEL_SITE=$(.tools/wheel-check/bin/python -c 'import mcap_ops,pathlib; print(pathlib.Path(mcap_ops.__file__).parent.parent)')
.venv/bin/python scripts/check_python_equivalence.py --before .artifacts/rsi/extension/python-base --after "$WHEEL_SITE"
.venv/bin/python - <<'PY'
import hashlib,json,pathlib,platform,subprocess
import numpy
root=pathlib.Path.cwd()
wheel=next((root/'.artifacts/rsi/extension/wheel').glob('*.whl'))
files=sorted(p for folder in ['crates/core/src','crates/io/src','crates/python/src','python/mcap_ops']
             for p in (root/folder).glob('*') if p.suffix in ['.rs','.py'])
record={'baseline':'bc58f81bb2c3dc43676450ee6685d8015fb99081','environment':'Linux x86-64 reference environment',
        'platform':platform.platform(),'python':platform.python_version(),'numpy':numpy.__version__,
        'rustc':subprocess.check_output(['rustc','--version'],text=True).strip(),
        'rust_tests':36,'python_tests':5,'public_comparisons':236,
        'random_core_scenarios':180,'clock_edge_cases':3630,'grid_edge_cases':168,
        'hampel_edge_cases':75,'slerp_edge_cases':50,'image_fixtures':13,'mcap_fixtures':2,
        'wheel':{'path':str(wheel.relative_to(root)),'bytes':wheel.stat().st_size,'sha256':hashlib.sha256(wheel.read_bytes()).hexdigest(),
                 'tests':5,'public_comparisons':236},
        'source_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(root/'docs/performance/extension/final/verification.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
PY
