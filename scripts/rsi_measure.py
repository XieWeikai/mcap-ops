#!/usr/bin/env python3
"""Run paired binaries on the test host; never accepts based on a single timing."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import statistics
import subprocess


def identity(path):
    root=Path(path).resolve()
    files=[root] if root.is_file() else [root/"mcap_ops/__init__.py",*sorted((root/"mcap_ops").glob("_native*.so"))]
    return [{"path":str(file),"bytes":file.stat().st_size,
             "sha256":hashlib.sha256(file.read_bytes()).hexdigest()} for file in files]


def run(binary, cpu, samples, millis, cases):
    env = dict(os.environ, RSI_SAMPLES=str(samples), RSI_MILLIS=str(millis))
    root = Path(binary).resolve()
    if root.is_dir():
        env.update(PYTHONPATH=str(root), RSI_PYTHON_ROOT=str(root))
        command = [".venv/bin/python", "scripts/python_benchmark.py"]
    else:
        command = [str(root)]
    if cases:
        command += ["--case", cases]
    result = subprocess.run(
        ["taskset", "-c", str(cpu), *command],
        check=False, capture_output=True, text=True, env=env,
    )
    if result.returncode:
        raise RuntimeError(f"benchmark failed ({result.returncode}): {result.stderr[-6000:]}")
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    if not rows or any("samples_ns" not in row for row in rows):
        raise RuntimeError("benchmark did not produce successful timing records")
    return {row["case"]: row for row in rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--cpu", type=int, default=12)
    parser.add_argument("--blocks", type=int, default=4)
    parser.add_argument("--samples", type=int, default=7)
    parser.add_argument("--millis", type=float, default=20)
    parser.add_argument("--cases")
    args = parser.parse_args()
    if args.blocks < 2:
        parser.error("at least two paired blocks required")
    runs = []
    for block in range(args.blocks):
        order = ["before", "after"] if block % 2 == 0 else ["after", "before"]
        current = {"block": block, "order": order}
        for label in order:
            current[label] = run(getattr(args, label), args.cpu, args.samples, args.millis, args.cases)
            print(f"completed block={block} side={label}", flush=True)
        if set(current["before"]) != set(current["after"]):
            raise RuntimeError("before/after benchmark coverage differs")
        runs.append(current)
    summary = {}
    for case in runs[0]["before"]:
        before = [block["before"][case]["median_ns"] for block in runs]
        after = [block["after"][case]["median_ns"] for block in runs]
        ratios = [a / b for a, b in zip(after, before)]
        summary[case] = {
            "before_ns": statistics.median(before),
            "after_ns": statistics.median(after),
            "latency_reduction_pct": 100 * (1 - statistics.median(ratios)),
            "paired_ratios": ratios,
            "worst_paired_reduction_pct": 100 * (1 - max(ratios)),
        }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "schema": "mcap-ops-rsi-paired-v1",
        "machine": platform.node(),
        "platform": platform.platform(),
        "before_artifacts": identity(args.before),
        "after_artifacts": identity(args.after),
        "cpu": args.cpu,
        "samples_per_block": args.samples,
        "target_millis_per_sample": args.millis,
        "runs": runs,
        "summary": summary,
    }, indent=2) + "\n")
    for case, record in summary.items():
        print(f"{case:34} {record['latency_reduction_pct']:8.2f}% "
              f"{record['before_ns']:.1f} -> {record['after_ns']:.1f} ns")


if __name__ == "__main__":
    main()
