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
import shutil

ROOT = Path(__file__).resolve().parents[1]
REMOTE = "."


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label")
    parser.add_argument("--cases", required=True)
    parser.add_argument("--paths", nargs="+", required=True)
    parser.add_argument("--python", action="store_true")
    parser.add_argument("--retry", action="store_true")
    parser.add_argument("--blocks", type=int, default=4)
    parser.add_argument("--series", choices=["initial", "extension", "per-op10"], default="initial")
    parser.add_argument("--sensitivity", action="store_true")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z0-9_.-]+", args.label):
        parser.error("label must be a simple identifier")
    report_root = ROOT / "docs/performance"
    if args.series != "initial":
        report_root /= args.series
    if (report_root / "results" / f"{args.label}.json").exists():
        parser.error("trial already has a decision; preserve its evidence and use a new label")
    destination = ROOT / ".artifacts/rsi/trials" / args.label
    destination.mkdir(parents=True, exist_ok=args.retry)
    if args.retry and (destination / "validation.log").exists():
        attempts = destination / "attempts"
        attempts.mkdir(exist_ok=True)
        previous = attempts / f"{len(list(attempts.iterdir())) + 1:03d}"
        previous.mkdir()
        for path in destination.iterdir():
            if path.is_file():
                shutil.copyfile(path, previous / path.name)
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
"""
    if args.series != "initial" and not args.python:
        setup += f"""
VALGRIND_LIB="$PWD/.tools/valgrind/root/usr/libexec/valgrind" .tools/valgrind/root/usr/bin/valgrind --tool=callgrind --collect-atstart=no --toggle-collect='operator_benchmark::Runner::bench*' --callgrind-out-file=.artifacts/rsi/trials/{label}/before.callgrind .artifacts/rsi/bin/accepted --case {cases} --profile
.tools/valgrind/root/usr/bin/callgrind_annotate --auto=no --inclusive=yes --threshold=98 .artifacts/rsi/trials/{label}/before.callgrind > .artifacts/rsi/trials/{label}/before-profile.txt
"""
    if args.series != "initial" and args.python:
        setup += f"""
PYTHONPATH="$PWD/.artifacts/rsi/python/accepted" RSI_PYTHON_ROOT="$PWD/.artifacts/rsi/python/accepted" .venv/bin/python scripts/python_benchmark.py --case {cases} --profile .artifacts/rsi/trials/{label}/before.prof
"""
    setup += f"""
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
        profile_cases = cases if args.series != "initial" else "python.resample.linear"
        setup += f"""
mkdir -p .artifacts/rsi/python/{label}
cp -r python/mcap_ops .artifacts/rsi/python/{label}/
.venv/bin/python scripts/check_python_equivalence.py --before .artifacts/rsi/python/accepted --after .artifacts/rsi/python/{label}
PYTHONPATH="$PWD/.artifacts/rsi/python/{label}" RSI_PYTHON_ROOT="$PWD/.artifacts/rsi/python/{label}" .venv/bin/python scripts/python_benchmark.py --case {profile_cases} --profile .artifacts/rsi/trials/{label}/profile.prof
python3 scripts/rsi_measure.py --before .artifacts/rsi/python/accepted --after .artifacts/rsi/python/{label} --cases {cases} --blocks {args.blocks} --output .artifacts/rsi/trials/{label}/measurement.json
"""
    else:
        setup += f"""
VALGRIND_LIB="$PWD/.tools/valgrind/root/usr/libexec/valgrind" .tools/valgrind/root/usr/bin/valgrind --tool=callgrind --collect-atstart=no --toggle-collect='operator_benchmark::Runner::bench*' --callgrind-out-file=.artifacts/rsi/trials/{label}/profile.callgrind .artifacts/rsi/bin/{label} --case {cases} --profile
.tools/valgrind/root/usr/bin/callgrind_annotate --auto=no --inclusive=yes --threshold=100 .artifacts/rsi/trials/{label}/profile.callgrind > .artifacts/rsi/trials/{label}/profile.txt
python3 scripts/rsi_measure.py --before .artifacts/rsi/bin/accepted --after .artifacts/rsi/bin/{label} --cases {cases} --blocks {args.blocks} --output .artifacts/rsi/trials/{label}/measurement.json
"""
    if args.sensitivity:
        setup += f"""
python3 scripts/prepare_sensitivity.py
CARGO_TARGET_DIR="$PWD/target/reference" cargo build --offline --release --manifest-path .artifacts/rsi/extension/sensitivity/Cargo.toml -j 12
python3 scripts/rsi_measure.py --before .artifacts/rsi/extension/sensitivity/before --after .artifacts/rsi/extension/sensitivity/after --output .artifacts/rsi/trials/{label}/sensitivity.json
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
    if args.sensitivity:
        sensitivity = json.loads((destination / "sensitivity.json").read_text())
        worst_case = min(item["latency_reduction_pct"] for item in sensitivity["summary"].values())
        audit["sensitivity_worst_case_pct"] = worst_case
        audit["sensitivity_sha256"] = hashlib.sha256((destination / "sensitivity.json").read_bytes()).hexdigest()
        audit["performance_gate"] &= worst_case >= -3
    if args.series == "per-op10" and args.label.startswith("ten-image-transform-"):
        sizes = [tuple(map(int, pair)) for pair in re.findall(
            r"(?m)^resource_png (\d+) (\d+)$", (destination / "validation.log").read_text())]
        if not sizes:
            raise RuntimeError("missing PNG size evidence")
        audit["png_size_pairs"] = sizes
        audit["png_max_growth_ratio"] = max(after / before for before, after in sizes)
        audit["performance_gate"] &= audit["png_max_growth_ratio"] <= 1.25
    (destination / "audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    (destination / "candidate.patch").write_bytes(subprocess.check_output(
        ["git", "diff", "HEAD", "--", *args.paths], cwd=ROOT))
    print(json.dumps(audit, indent=2))
    for case, record in result["summary"].items():
        print(case, f"{record['before_ns']:.2f} -> {record['after_ns']:.2f} ns",
              f"{record['latency_reduction_pct']:.2f}%")


if __name__ == "__main__":
    main()
