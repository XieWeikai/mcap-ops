#!/usr/bin/env python3
"""Run exactly twenty follow-up experiments; preserve the initial 60 decisions."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("extension", ROOT / "benchmarks/candidates_extension.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def run(*args):
    subprocess.run(list(args), cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-round", type=int, default=1)
    parser.add_argument("--through", type=int, default=20)
    parser.add_argument("--retry", action="store_true")
    args = parser.parse_args()
    assert len(module.RECIPES) == 20
    for number, recipe in enumerate(module.RECIPES, 1):
        if not args.from_round <= number <= args.through:
            continue
        label = f"extension-{number:02d}-{recipe['operator'].replace('_', '-')}"
        result_root = ROOT / "docs/performance/extension"
        if (result_root / "results" / f"{label}.json").exists():
            print("SKIP completed", label, flush=True)
            continue
        trial = ROOT / ".artifacts/rsi/trials" / label
        print("BEGIN", label, recipe["method"], flush=True)
        print("LEARNING", recipe["lesson"], flush=True)
        if not trial.exists():
            sources = {name: (ROOT / name).read_text() for name in recipe["paths"]}
            originals = dict(sources)
            if len(sources) == 1:
                name = recipe["paths"][0]
                source = sources[name]
                function = recipe["function"]
                start, end = (0, len(source)) if function is None else module.function_span(source, function)
                sources[name] = source[:start] + recipe["change"](source[start:end]) + source[end:]
            else:
                recipe["change"](sources)
            assert sources != originals
            for name, source in sources.items():
                (ROOT / name).write_text(source)
        elif not args.retry:
            raise RuntimeError(f"unfinished candidate requires --retry: {label}")
        command = [sys.executable, "scripts/rsi_trial.py", label, "--series", "extension",
                   "--cases", recipe["cases"], "--paths", *recipe["paths"]]
        if args.retry:
            command.append("--retry")
        if recipe.get("python"):
            command.append("--python")
        if recipe.get("sensitivity"):
            command.append("--sensitivity")
        run(*command)
        audit = json.loads((trial / "audit.json").read_text())
        accepted = audit["performance_gate"]
        decision = [sys.executable, "scripts/rsi_decide.py", label, "--series", "extension",
                    "--operator", recipe["operator"], "--round", str(number),
                    "--method", recipe["method"], "--hotspot", recipe["hotspot"],
                    "--complexity", "Bounded safe-Rust local change; no new runtime dependencies. " + recipe["lesson"],
                    "--reason", ("All paired blocks clear 8%, no case regresses more than 3%, correctness passes. "
                                 if accepted else "Performance gate failed; restore previous accepted implementation. ") + recipe["lesson"]]
        if accepted:
            decision.append("--accept")
        run(*decision)
        if accepted:
            run("git", "add", *recipe["paths"],
                f"docs/performance/extension/results/{label}.json",
                *[str(path.relative_to(ROOT)) for path in sorted((result_root / "data").glob(f"{label}*.json"))])
            run("git", "commit", "-F", str(trial / "commit-message.txt"))
            run("ssh", "reference-linux", f"cd . && "
                f"cp .artifacts/rsi/bin/{label} .artifacts/rsi/bin/accepted && "
                "cp python/mcap_ops/_native.abi3.so .artifacts/rsi/python/accepted/mcap_ops/_native.abi3.so && "
                "cp python/mcap_ops/__init__.py .artifacts/rsi/python/accepted/mcap_ops/__init__.py")
        print("END", label, "accepted" if accepted else "rejected", flush=True)


if __name__ == "__main__":
    main()
