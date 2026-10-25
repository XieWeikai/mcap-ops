#!/usr/bin/env python3
"""Validate, profile and measure one candidate on reference-linux. Never commits code."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label")
    parser.add_argument("--cases", required=True)
    parser.add_argument("--paths", nargs="+", required=True)
    parser.add_argument("--python", action="store_true")
    parser.add_argument("--retry", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9_.-]+", args.label):
        parser.error("label must be a simple identifier")
    destination = ROOT / ".artifacts/rsi/trials" / args.label
    destination.mkdir(parents=True, exist_ok=args.retry)
    base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    (destination / "candidate.patch").write_bytes(subprocess.check_output(
        ["git", "diff", "HEAD", "--", *args.paths], cwd=ROOT))
    for name in args.paths:
        before = destination / "before" / name
        before.parent.mkdir(parents=True, exist_ok=True)
        before.write_bytes(subprocess.check_output(["git", "show", f"HEAD:{name}"], cwd=ROOT))
    subprocess.run(["python3", str(ROOT / "scripts/sync_sources.py")], cwd=ROOT, check=True)
    label = shlex.quote(args.label)
    cases = shlex.quote(args.cases)
    setup = f"""set -eu
cd {REMOTE}
export CARGO_HOME="$PWD/.tools/cargo" RUSTUP_HOME="$PWD/.tools/rustup"
export PATH="$CARGO_HOME/bin:$PATH" VIRTUAL_ENV="$PWD/.venv"
export CARGO_PROFILE_RELEASE_DEBUG=1 CARGO_BUILD_JOBS=12
mkdir -p .artifacts/rsi/trials/{label}
cargo fmt --all
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace --locked -j 12
python3 scripts/prepare_reference.py
CARGO_PROFILE_RELEASE_DEBUG=0 CARGO_TARGET_DIR="$PWD/target/reference" cargo run --offline --manifest-path .artifacts/rsi/validation/Cargo.toml --release -j 12
.venv/bin/maturin develop --release --locked
.venv/bin/python -m pytest -q tests
cargo build --locked --release -p mcap-ops-io --example operator_benchmark -j 12
cp target/release/examples/operator_benchmark .artifacts/rsi/bin/{label}
"""
    if args.python:
        setup += f"""
mkdir -p .artifacts/rsi/python/{label}
cp -r python/mcap_ops .artifacts/rsi/python/{label}/
.venv/bin/python scripts/check_python_equivalence.py --before .artifacts/rsi/python/accepted --after .artifacts/rsi/python/{label}
PYTHONPATH="$PWD/.artifacts/rsi/python/{label}" RSI_PYTHON_ROOT="$PWD/.artifacts/rsi/python/{label}" .venv/bin/python scripts/python_benchmark.py --case python.resample.linear --profile .artifacts/rsi/trials/{label}/profile.prof
python3 scripts/rsi_measure.py --before .artifacts/rsi/python/accepted --after .artifacts/rsi/python/{label} --cases {cases} --output .artifacts/rsi/trials/{label}/measurement.json
"""
    else:
        setup += f"""
VALGRIND_LIB="$PWD/.tools/valgrind/root/usr/libexec/valgrind" .tools/valgrind/root/usr/bin/valgrind --tool=callgrind --collect-atstart=no --toggle-collect='operator_benchmark::Runner::bench*' --callgrind-out-file=.artifacts/rsi/trials/{label}/profile.callgrind .artifacts/rsi/bin/{label} --case {cases} --profile
.tools/valgrind/root/usr/bin/callgrind_annotate --auto=no --inclusive=yes --threshold=100 .artifacts/rsi/trials/{label}/profile.callgrind > .artifacts/rsi/trials/{label}/profile.txt
python3 scripts/rsi_measure.py --before .artifacts/rsi/bin/accepted --after .artifacts/rsi/bin/{label} --cases {cases} --output .artifacts/rsi/trials/{label}/measurement.json
"""
    with (destination / "validation.log").open("w") as log:
        result = subprocess.run(["ssh", "reference-linux", setup], stdout=log, stderr=subprocess.STDOUT)
    # Formatting is an expected output of this trial; fetch only explicitly owned paths.
    for name in args.paths:
        subprocess.run(["rsync", "-az", f"reference-linux:{REMOTE}/{name}", str(ROOT / name)], check=True)
    if result.returncode:
        print((destination / "validation.log").read_text()[-9000:])
        raise SystemExit(result.returncode)
    subprocess.run(["rsync", "-az", f"reference-linux:{REMOTE}/.artifacts/rsi/trials/{args.label}/", str(destination) + "/"], check=True)
    result = json.loads((destination / "measurement.json").read_text())
    block_ratios = []
    for block in result["runs"]:
        ratios = [block["after"][case]["median_ns"] / block["before"][case]["median_ns"]
                  for case in result["summary"]]
        block_ratios.append(math.exp(statistics.mean(math.log(x) for x in ratios)))
    improvement = 100 * (1 - statistics.median(block_ratios))
    worst = 100 * (1 - max(block_ratios))
    regression = min(record["latency_reduction_pct"] for record in result["summary"].values())
    audit = {
        "label": args.label, "base_commit": base, "cases": args.cases.split(","),
        "geomean_latency_reduction_pct": improvement,
        "worst_block_reduction_pct": worst,
        "worst_case_reduction_pct": regression,
        "performance_gate": improvement >= 8 and worst >= 8 and regression >= -3,
        "correctness": "fmt, Clippy, workspace tests, reference differential and Python tests passed",
        "complexity_review": "pending human-agent review",
        "paths": args.paths,
        "measurement_sha256": hashlib.sha256((destination / "measurement.json").read_bytes()).hexdigest(),
    }
    (destination / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (destination / "candidate.patch").write_bytes(subprocess.check_output(
        ["git", "diff", "HEAD", "--", *args.paths], cwd=ROOT))
    print(json.dumps(audit, indent=2))
    for case, record in result["summary"].items():
        print(case, f"{record['before_ns']:.2f} -> {record['after_ns']:.2f} ns",
              f"{record['latency_reduction_pct']:.2f}%")


if __name__ == "__main__":
    main()
