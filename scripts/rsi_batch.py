#!/usr/bin/env python3
"""Execute the bounded, pre-reviewed candidate list. Each accepted round commits."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rsi_candidates", ROOT / "benchmarks/candidates.py")
candidates = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidates)
extra_spec = importlib.util.spec_from_file_location("rsi_candidates_extra", ROOT / "benchmarks/candidates_extra.py")
if extra_spec and Path(extra_spec.origin).exists():
    extra = importlib.util.module_from_spec(extra_spec)
    extra_spec.loader.exec_module(extra)
    candidates.RECIPES.extend(extra.RECIPES)


def function_span(source, name):
    # Mask comments and ordinary Rust strings without changing byte positions.
    masked = re.sub(
        r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])\'',
        lambda match: " " * len(match.group()), source, flags=re.DOTALL,
    )
    matches = list(re.finditer(r"\b(?:pub\s+)?fn\s+" + re.escape(name) + r"\s*[\(<]", masked))
    if len(matches) != 1:
        raise RuntimeError(f"expected unique function {name}")
    start = matches[0].start()
    opening = masked.index("{", matches[0].end())
    depth = 0
    for i in range(opening, len(masked)):
        depth += (masked[i] == "{") - (masked[i] == "}")
        if depth == 0:
            return start, i + 1
    raise RuntimeError("unclosed function")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only")
    parser.add_argument("--round", choices=["1", "2", "both"], default="both")
    parser.add_argument("--retry", action="store_true")
    args = parser.parse_args()
    for recipe in candidates.RECIPES:
        op = recipe["operator"]
        if args.only and op not in args.only.split(","):
            continue
        for round_number in [1, 2] if args.round == "both" else [int(args.round)]:
            label = f"{op.replace('_','-')}-r{round_number}"
            decision = ROOT / "docs/performance/results" / f"{label}.json"
            if decision.exists():
                print("already recorded", label, flush=True)
                continue
            path = ROOT / recipe["path"]
            trial = ROOT / ".artifacts/rsi/trials" / label
            print("BEGIN", label, recipe["methods"][round_number - 1], flush=True)
            if not trial.exists():
                source = path.read_text()
                function = recipe["function"]
                if isinstance(function, list):
                    function = function[round_number - 1]
                start, end = function_span(source, function)
                revised = recipe["rounds"][round_number - 1](source[start:end])
                if revised == source[start:end]:
                    raise RuntimeError("candidate made no implementation change")
                path.write_text(source[:start] + revised + source[end:])
            elif not args.retry:
                raise RuntimeError(f"unfinished trial requires --retry: {label}")
            command = [sys.executable, "scripts/rsi_trial.py", label, "--cases",
                       recipe["cases"], "--paths", recipe["path"]]
            if args.retry:
                command.append("--retry")
            subprocess.run(command, cwd=ROOT, check=True)
            audit = json.loads((trial / "audit.json").read_text())
            accepted = audit["performance_gate"]
            reason = ("All paired aggregate blocks clear 8%, no representative-case regression "
                      "above 3%, differential correctness passes, and the pre-reviewed local "
                      "change adds no unsafe code or dependencies.") if accepted else (
                      "Rejected by paired performance gate: insufficient stable 8% gain or "
                      "a representative-case regression. Restore previous accepted implementation.")
            decision_cmd = [sys.executable, "scripts/rsi_decide.py", label, "--operator", op,
                "--round", str(round_number), "--method", recipe["methods"][round_number-1],
                "--hotspot", recipe["hotspot"], "--complexity", recipe["complexity"],
                "--reason", reason]
            if accepted:
                decision_cmd.append("--accept")
            subprocess.run(decision_cmd, cwd=ROOT, check=True)
            if accepted:
                subprocess.run(["git", "add", recipe["path"],
                    f"docs/performance/results/{label}.json",
                    f"docs/performance/data/{label}.json"], cwd=ROOT, check=True)
                subprocess.run(["git", "commit", "-F", str(trial / "commit-message.txt")], cwd=ROOT, check=True)
                subprocess.run(["ssh", "reference-linux",
                    f"cd . && "
                    f"cp .artifacts/rsi/bin/{label} .artifacts/rsi/bin/accepted && "
                    "cp python/mcap_ops/_native.abi3.so .artifacts/rsi/python/accepted/mcap_ops/_native.abi3.so"],
                    check=True)
            print("END", label, "accepted" if accepted else "rejected", flush=True)


if __name__ == "__main__":
    main()
