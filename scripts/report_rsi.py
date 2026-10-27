#!/usr/bin/env python3
"""Audit two decisions per implementation unit and render the review report."""
import hashlib
import json
from pathlib import Path
import subprocess
from history_revision import resolve_revision

ROOT=Path(__file__).resolve().parents[1]
EXPECTED={
    "require_strict","uniform_grid","map_clock","inspect_time","align_timestamps",
    "expand_batch_timestamps","resample","history_windows","inspect_signal","gate",
    "ema","lowpass_taps","fir","unwrap_angles","interval_new","interval_contains",
    "interval_mask","interval_intersection","interval_difference","interval_affected_centers",
    "raw_reader","mcap_inspect","json_decode","mcap_read_signal","image_decode",
    "image_quality","image_transform","video_probe","video_validate","python_bridge",
}


def main():
    rows=[]
    for path in sorted((ROOT/"docs/performance/results").glob("*.json")):
        row=json.loads(path.read_text());row["record_path"]=str(path.relative_to(ROOT));rows.append(row)
        data=ROOT/"docs/performance/data"/(row["label"]+".json")
        assert hashlib.sha256(data.read_bytes()).hexdigest()==row["measurement_sha256"],row["label"]
        measured=json.loads(data.read_text())
        assert len(measured["runs"])>=4 and measured["cpu"]==12
        assert set(row["cases"])==set(measured["summary"])
        if row["decision"]=="accepted":
            assert row["performance_gate"] and row["geomean_latency_reduction_pct"]>=8
            assert row["worst_block_reduction_pct"]>=8 and row["worst_case_reduction_pct"]>=-3
            assert row["complexity_review"]!="pending human-agent review"
    grouped={}
    for row in rows:
        key=(row["operator"],row["round"])
        assert key not in grouped,f"duplicate final decision: {key}"
        grouped[key]=row
    assert set(grouped)=={(op,r) for op in EXPECTED for r in (1,2)},"incomplete two-round coverage"
    history=subprocess.check_output(["git","log","--format=%H%x09%s"],cwd=ROOT,text=True).splitlines()
    for row in rows:
        if row["decision"]!="accepted":continue
        marker=f"[RSI round {row['round']}]"
        matches=[line.split("\t",1)[0] for line in history if f"perf({row['operator']}):" in line and marker in line]
        assert len(matches)==1,(row["label"],matches)
        row["commit"]=matches[0]
        body=subprocess.check_output(["git","show","-s","--format=%B",matches[0]],cwd=ROOT,text=True)
        assert row["record_path"] in body and "ns/op" in body and "Correctness:" in body
    accepted=sum(r["decision"]=="accepted" for r in rows)
    stats=subprocess.check_output(["git","diff","--numstat",resolve_revision("66248da"),"--",
        "crates/core/src","crates/io/src","crates/python/src","python/mcap_ops"],cwd=ROOT,text=True)
    changes=[line.split("\t",2) for line in stats.splitlines()]
    added=sum(int(row[0]) for row in changes);removed=sum(int(row[1]) for row in changes)
    report=["# RSI results", "",f"Completed: **30 implementation units x 2 rounds = 60 final decisions**. "
            f"Accepted {accepted}; rejected {60-accepted}.","",
            "Reference: `66248dacb608859d2cbd0f9f27227c65013a8027`. All builds, profiles, "
            "tests and timing runs execute in the reference Linux environment (i9-14900K, CPU 12 affinity, Rust 1.90, release).", "",
            f"Production source changes: {len(changes)} files, {added} added lines and {removed} removed "
            f"lines (net {added-removed:+d}). Runtime dependencies and public operator signatures are unchanged.", "",
            "Each percentage is paired geometric-mean **latency reduction** across that operator's "
            "fixed cases, relative to the previously accepted implementation. A negative number "
            "means slower. An accepted round must clear 8% in every aggregate paired block, pass "
            "correctness, and avoid a representative-case regression greater than 3%.","",
            "Uniform-grid and wide-Hampel candidates with contradictory initial timing receive "
            "one independent eight-block confirmation. Original observations remain in `history/` "
            "and `data/`; this is a repeat measurement of the same candidate, not an extra code round.","",
            "| Operator | Round 1 | Round 2 | Accepted commits |",
            "| --- | --- | --- | --- |"]
    for op in sorted(EXPECTED):
        cells=[];commits=[]
        for rnd in (1,2):
            row=grouped[(op,rnd)]
            cells.append(f"[{row['decision']} {row['geomean_latency_reduction_pct']:+.2f}%](results/{row['label']}.json)")
            if row.get("commit"):commits.append(f"`{row['commit'][:8]}`")
        report.append(f"| `{op}` | {cells[0]} | {cells[1]} | {', '.join(commits) or '-'} |")
    report += ["", "## Evidence", "",
        "- `results/`: final decisions, method, hotspot, complexity, per-case before/after timings and measurement hashes.",
        "- `data/`: all paired samples and calibration counts; accepted commits contain their corresponding records.",
        "- `rejected/`: candidate patches, including historical rejections that were later confirmed.",
        "- `history/`: superseded unstable observations, kept without altering the raw data.",
        "- Execution environment `.artifacts/rsi/trials/`: complete validation logs and Callgrind/cProfile output.",
        "", "## Correctness", "",
        "Every decision follows rustfmt, Clippy, 36 Rust tests, immutable-reference differential "
        "checks and 5 Python smoke tests. The differential suite exercises 180 randomized core "
        "scenarios, generated MCAP fixtures, PNG/JPEG, RGBA and 16-bit PNG. Integer timestamps, "
        "indices, masks and decisions match exactly; numeric comparisons use explicit f64 tolerances. "
        "Image transforms preserve decoded pixels. The Python bridge additionally passes 236 "
        "public-interface comparisons including dictionary order, empty shapes, strided values, "
        "NaN/Inf handling, errors and output ownership.", "",
        "The host's perf permission prevents hardware-counter sampling. Profiling uses a project-local "
        "Callgrind installation and cProfile; profiler times are excluded from wall-clock measurements. "
        "Fixtures are synthetic and repeatable. Results describe these workloads on this shared host, "
        "not an unmeasured end-to-end robotics dataset pipeline.", ""]
    final=ROOT/"docs/performance/final"
    for name in ("native","python"):
        path=final/f"{name}.json"
        if path.exists():
            data=json.loads(path.read_text())
            report += [f"## Final {name} comparison", "", "Initial pre-RSI implementation versus the complete accepted state.","",
                       "| Case | Before (us) | After (us) | Paired latency reduction |",
                       "| --- | ---: | ---: | ---: |"]
            for case,record in sorted(data["summary"].items()):
                report.append(f"| `{case}` | {record['before_ns']/1000:.3f} | {record['after_ns']/1000:.3f} | {record['latency_reduction_pct']:+.2f}% |")
            report.append("")
    if (final/"unchanged-native.json").exists():
        report += ["## Unchanged-path follow-up", "",
            "The combined build shows approximately 4-6% slower native FIR and dense interval "
            "intersection cases in both the full run and an eight-block focused repeat. Their "
            "operator bodies were retained because both direct optimization candidates were "
            "rejected. The cause of this combined-build difference is not established; it must "
            "not be described as a speedup or silently omitted. Python MCAP inspection returned "
            "to +1.7% in the focused repeat after -4.25% in the full run.", "",
            "See `final/unchanged-native.json` and `final/unchanged-python.json` for every sample, "
            "and `final/unchanged-source.json` for the identical function-body hashes. "
            "These validation observations are not additional optimization candidates.", ""]
    verification=final/"verification.json"
    if verification.exists():
        v=json.loads(verification.read_text())
        report += ["## Installed wheel", "",
            f"The wheel `{Path(v['wheel']['path']).name}` passed five tests in a fresh environment "
            f"and {v['wheel'].get('public_interface_comparisons',0)} public-interface comparisons. "
            f"It targets Linux x86-64 / glibc 2.39+ with CPython abi3 (3.10+); execution was verified "
            f"with CPython {v['python']} and NumPy {v['numpy']}. See `final/verification.json` for "
            "the artifact SHA-256 and environment details.", ""]
    (ROOT/"docs/performance/RESULTS.md").write_text("\n".join(report))
    (ROOT/"docs/performance/coverage.json").write_text(json.dumps({"operators":30,"rounds":60,
        "accepted":accepted,"rejected":60-accepted,"decisions":rows},indent=2)+"\n")
    print(f"Audited 60 decisions: {accepted} accepted, {60-accepted} rejected")


if __name__=="__main__":main()
