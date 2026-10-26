#!/usr/bin/env python3
"""Audit the twenty new decisions without rewriting the original RSI report."""
import hashlib
import json
import math
from pathlib import Path
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "docs/performance/extension"
BASE = "bc58f81bb2c3dc43676450ee6685d8015fb99081"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def main():
    rows = []
    for path in sorted((REPORT / "results").glob("*.json")):
        row = json.loads(path.read_text())
        data_path = REPORT / "data" / path.name
        assert hashlib.sha256(data_path.read_bytes()).hexdigest() == row["measurement_sha256"]
        data = json.loads(data_path.read_text())
        assert len(data["runs"]) >= 4 and data["cpu"] == 12
        assert set(row["cases"]) == set(data["summary"])
        aggregate = []
        for block in data["runs"]:
            assert set(block["before"]) == set(block["after"]) == set(row["cases"])
            aggregate.append(math.exp(statistics.mean(math.log(
                block["after"][case]["median_ns"] / block["before"][case]["median_ns"])
                for case in row["cases"])))
        worst = 100 * (1 - max(aggregate))
        improvement = 100 * (1 - statistics.median(aggregate))
        assert abs(worst - row["worst_block_reduction_pct"]) < 1e-9
        assert abs(improvement - row["geomean_latency_reduction_pct"]) < 1e-9
        assert row["series"] == "extension"
        if "sensitivity_sha256" in row:
            sensitivity_path = data_path.with_name(row["label"] + "-sensitivity.json")
            assert hashlib.sha256(sensitivity_path.read_bytes()).hexdigest() == row["sensitivity_sha256"]
            sensitivity = json.loads(sensitivity_path.read_text())
            if row["decision"] == "accepted":
                assert min(item["latency_reduction_pct"] for item in sensitivity["summary"].values()) >= -3
        row["record_path"] = str(path.relative_to(ROOT))
        if row["decision"] == "accepted":
            assert worst >= 8 and improvement >= 8
            assert min(x["latency_reduction_pct"] for x in data["summary"].values()) >= -3
            marker = f"[RSI extension round {row['round']}]"
            commits = [line.split("\t")[0] for line in git("log", "--format=%H%x09%s").splitlines()
                       if marker in line and f"perf({row['operator']}):" in line]
            assert len(commits) == 1, commits
            row["commit"] = commits[0]
            body = git("show", "-s", "--format=%B", row["commit"])
            assert row["record_path"] in body and "ns/op" in body and "Correctness:" in body
        else:
            assert (REPORT / "rejected" / f"{row['label']}.patch").is_file()
        rows.append(row)
    assert len(rows) == 20 and {row["round"] for row in rows} == set(range(1, 21))
    assert not git("diff", BASE, "--", "docs/performance/results", "docs/performance/data",
                   "docs/performance/rejected", "docs/performance/history"), "original evidence changed"
    accepted = sum(row["decision"] == "accepted" for row in rows)
    diff = [line.split("\t", 2) for line in git("diff", "--numstat", BASE, "--",
        "crates/core/src", "crates/io/src", "crates/python/src", "python/mcap_ops").splitlines()]
    added, removed = sum(int(x[0]) for x in diff), sum(int(x[1]) for x in diff)
    text = ["# Twenty additional RSI experiments", "",
        f"Completed **20/20**: **{accepted} accepted**, **{20-accepted} rejected**. "
        "The original 60 decisions are preserved, for 80 total experiments.", "",
        f"Baseline: `{BASE}`. All execution on reference-linux, i9-14900K, CPU 12, Rust 1.90, "
        "release with unchanged flags. Every trial used generated inputs, before/after profiles, "
        "four alternating AB/BA blocks, and seven calibrated samples per side.", "",
        "Acceptance: every block's geometric-mean latency reduction >=8%, no case's median "
        "regression >3%, correctness passed, and bounded implementation complexity. "
        "Percentages below compare with the previously accepted state, not the initial repo.", "",
        f"Production diff for this extension: {len(diff)} files, +{added}/-{removed} lines "
        f"(net {added-removed:+d}). No runtime dependency or build-flag changes.", "",
        "| Round | Operator and hypothesis | Decision | Paired reduction | Worst block | Commit |",
        "| ---: | --- | --- | ---: | ---: | --- |"]
    for row in rows:
        text.append(f"| {row['round']} | `{row['operator']}`: {row['method']} | "
                    f"[{row['decision']}](results/{row['label']}.json) | "
                    f"{row['geomean_latency_reduction_pct']:+.2f}% | "
                    f"{row['worst_block_reduction_pct']:+.2f}% | `{row.get('commit','-')[:8]}` |")
    text += ["", "## Prior experience and decisions", ""]
    for row in rows:
        text += [f"**{row['round']}. {row['method']}** — {row['reason']}", ""]
    text += ["## Correctness and costs", "",
        "Each candidate passes rustfmt, Clippy, 36 Rust tests, the immutable-reference "
        "differential suite (180 randomized core scenarios, 13 image fixtures, two MCAP "
        "fixtures), and five Python tests before timing. The extended oracle adds 3630 "
        "clock arithmetic cases, 168 grid cases, 75 Hampel cases and 50 SLERP cases; it "
        "was introduced during round 4 and rerun on the final accepted tree. Python bridge "
        "changes additionally compare 236 public-interface cases, including output types, "
        "dictionary order, strided arrays, errors and non-finite values.", "",
        "The unconditional FIR channel-plane candidate was withdrawn after additional "
        "workloads revealed regressions, even though its original fixed-case gate passed. "
        "Its initial acceptance and counterevidence remain in `history/`. The guarded "
        "follow-up must pass the extra sensitivity gate; channel planes, when used, need "
        "an additional 8*N*D bytes of temporary memory. "
        "Sorted MAD adds a small private merge helper and preserves window boundaries, "
        "exact medians, issue ordering and overflow behavior. No unsafe buffers, reduced "
        "precision, discarded checks, source modifications or external services are involved.", "",
        "Raw timing samples live in `data/`; rejected patches in `rejected/`. Complete "
        "validation logs and before/after profiles live on reference-linux at "
        "`.artifacts/rsi/trials/extension-*`. This series uses Callgrind/cProfile because "
        "perf_event_paranoid remains 4. Profiler times are excluded from benchmark claims.", ""]
    for name in ("native", "python", "sensitivity"):
        path = REPORT / "final" / f"{name}.json"
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        text += [f"## Final {name} comparison", "",
            "Extension baseline versus the complete accepted extension; negative values are regressions.", "",
            "| Case | Before (us) | After (us) | Paired reduction |",
            "| --- | ---: | ---: | ---: |"]
        for case, item in sorted(data["summary"].items()):
            text.append(f"| `{case}` | {item['before_ns']/1000:.3f} | {item['after_ns']/1000:.3f} | {item['latency_reduction_pct']:+.2f}% |")
        text.append("")
    caveats = REPORT / "final" / "notes.md"
    if caveats.exists():
        text += ["## Final verification notes", "", caveats.read_text().strip(), ""]
    (REPORT / "RESULTS.md").write_text("\n".join(text))
    (REPORT / "coverage.json").write_text(json.dumps({"baseline": BASE, "rounds": 20,
        "accepted": accepted, "rejected": 20-accepted, "decisions": rows}, indent=2) + "\n")
    print(f"Audited 20 new decisions: {accepted} accepted, {20-accepted} rejected")


if __name__ == "__main__":
    main()
