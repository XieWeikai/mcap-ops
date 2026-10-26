#!/usr/bin/env python3
"""Record an RSI decision; restore only this candidate's owned paths on rejection."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("label")
    parser.add_argument("--operator", required=True)
    parser.add_argument("--round", type=int, choices=[1, 2], required=True)
    parser.add_argument("--accept", action="store_true")
    parser.add_argument("--method", required=True)
    parser.add_argument("--hotspot", required=True)
    parser.add_argument("--complexity", required=True)
    parser.add_argument("--reason", required=True)
    args = parser.parse_args()
    trial = ROOT / ".artifacts/rsi/trials" / args.label
    audit = json.loads((trial / "audit.json").read_text())
    if args.accept and not audit["performance_gate"]:
        raise RuntimeError("cannot accept a candidate that failed the performance gate")
    measurement = json.loads((trial / "measurement.json").read_text())
    record = {
        **audit,
        "operator": args.operator,
        "round": args.round,
        "decision": "accepted" if args.accept else "rejected",
        "method": args.method,
        "profile_hotspot": args.hotspot,
        "complexity_review": args.complexity,
        "reason": args.reason,
        "case_results": measurement["summary"],
        "profile_remote_path": f"./.artifacts/rsi/trials/{args.label}",
        "validation_sha256": hashlib.sha256((trial / "validation.log").read_bytes()).hexdigest(),
    }
    output = ROOT / "docs/performance/results" / f"{args.label}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(record, indent=2) + "\n")
    data = ROOT / "docs/performance/data" / f"{args.label}.json"
    data.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(trial / "measurement.json", data)
    if args.accept:
        body = [
            f"perf({args.operator}): {args.method} [RSI round {args.round}]",
            "",
            f"Profile: {args.hotspot}",
            f"Change: {args.method}",
            f"Complexity: {args.complexity}",
            "",
            "reference-linux / i9-14900K / CPU 12 / Rust 1.90 / release, unchanged build flags.",
            f"{len(measurement['runs'])} paired AB/BA blocks; seven calibrated samples per side.",
            f"Geometric paired latency reduction: {audit['geomean_latency_reduction_pct']:.2f}%; "
            f"worst block: {audit['worst_block_reduction_pct']:.2f}%.",
        ]
        body += [
            f"{name}: {row['before_ns']:.2f} -> {row['after_ns']:.2f} ns/op; "
            f"latency reduction {row['latency_reduction_pct']:.2f}%."
            for name, row in measurement["summary"].items()
        ]
        body += ["", f"Correctness: {audit['correctness']}.",
                 f"Decision: {args.reason}", f"Evidence: {output.relative_to(ROOT)}",
                 f"Raw samples: {data.relative_to(ROOT)}", ""]
        (trial / "commit-message.txt").write_text("\n".join(body))
    else:
        patch = ROOT / "docs/performance/rejected" / f"{args.label}.patch"
        patch.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(trial / "candidate.patch", patch)
        for name in audit["paths"]:
            (ROOT / name).write_bytes((trial / "before" / name).read_bytes())
    print(record["decision"], args.label, f"{audit['geomean_latency_reduction_pct']:.2f}%")


if __name__ == "__main__":
    main()
