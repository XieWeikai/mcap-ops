"""CLI safety checks run only on reference-linux, using isolated temporary Git repositories."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def trial(tmp_path):
    (tmp_path / "scripts").mkdir()
    shutil.copy2(ROOT / "scripts/rsi_decide.py", tmp_path / "scripts")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    for key, value in [("user.name", "RSI fixture"), ("user.email", "fixture@example.invalid")]:
        subprocess.run(["git", "config", key, value], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=tmp_path, check=True)
    source = tmp_path / "operator.rs"
    source.write_text("baseline\n")
    subprocess.run(["git", "add", "operator.rs"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture baseline"], cwd=tmp_path, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    source.write_text("candidate\n")
    artifact = tmp_path / ".artifacts/rsi/trials/new-op-01"
    (artifact / "before").mkdir(parents=True)
    (artifact / "before/operator.rs").write_text("baseline\n")
    (artifact / "candidate.patch").write_bytes(
        subprocess.check_output(["git", "diff", "HEAD", "--", "operator.rs"], cwd=tmp_path)
    )
    (artifact / "audit.json").write_text(json.dumps({
        "label": "new-op-01", "base_commit": head, "paths": ["operator.rs"],
        "performance_gate": False, "geomean_latency_reduction_pct": 1.0,
    }))
    (artifact / "measurement.json").write_text(json.dumps({"summary": {}, "runs": []}))
    (artifact / "validation.log").write_text("fixture validation\n")
    command = [
        sys.executable, str(tmp_path / "scripts/rsi_decide.py"), "new-op-01",
        "--series", "next-campaign", "--operator", "operator", "--round", "1",
        "--method", "fixture change", "--hotspot", "fixture", "--complexity", "small",
        "--reason", "below gate",
    ]
    return tmp_path, source, artifact, command


def test_rejection_archives_and_restores_only_owned_source(trial):
    root, source, _, command = trial
    unrelated = root / "unrelated.txt"
    unrelated.write_text("leave intact\n")
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert source.read_text() == "baseline\n"
    assert unrelated.read_text() == "leave intact\n"
    record = root / "docs/performance/next-campaign/results/new-op-01.json"
    original = record.read_bytes()
    assert json.loads(original)["decision"] == "rejected"
    assert (record.parent.parent / "rejected/new-op-01.patch").is_file()
    assert subprocess.run(command, cwd=root, capture_output=True).returncode != 0
    assert record.read_bytes() == original


@pytest.mark.parametrize("change", ["candidate", "baseline", "snapshot"])
def test_stale_decision_never_overwrites_work(trial, change):
    root, source, artifact, command = trial
    if change == "candidate":
        source.write_text("new user edit\n")
    elif change == "baseline":
        subprocess.run(["git", "commit", "--allow-empty", "-qm", "new baseline"], cwd=root, check=True)
    else:
        (artifact / "before/operator.rs").write_text("wrong snapshot\n")
    before = source.read_bytes()
    assert subprocess.run(command, cwd=root, capture_output=True).returncode != 0
    assert source.read_bytes() == before
    assert not (root / "docs").exists()


def test_failed_performance_gate_cannot_be_accepted(trial):
    root, source, _, command = trial
    result = subprocess.run([*command, "--accept"], cwd=root, capture_output=True, text=True)
    assert result.returncode != 0
    assert "failed the performance gate" in result.stderr
    assert source.read_text() == "candidate\n"
    assert not (root / "docs").exists()


def test_acceptance_prepares_commit_message_without_committing(trial):
    root, source, artifact, command = trial
    audit = json.loads((artifact / "audit.json").read_text())
    audit.update(performance_gate=True, geomean_latency_reduction_pct=10.0,
                 worst_block_reduction_pct=9.0, correctness="fixture checks passed")
    (artifact / "audit.json").write_text(json.dumps(audit))
    (artifact / "measurement.json").write_text(json.dumps({
        "runs": [{}, {}, {}, {}],
        "summary": {"fixture": {"before_ns": 100.0, "after_ns": 90.0, "latency_reduction_pct": 10.0}},
    }))
    result = subprocess.run([*command, "--accept"], cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert source.read_text() == "candidate\n"
    assert "100.00 -> 90.00 ns/op" in (artifact / "commit-message.txt").read_text()
    assert subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip() == audit["base_commit"]


@pytest.mark.parametrize("script,args", [
    ("rsi_decide.py", ["../escape", "--series", "next", "--operator", "x", "--round", "1",
                       "--method", "x", "--hotspot", "x", "--complexity", "x", "--reason", "x"]),
    ("rsi_trial.py", ["trial", "--series", "../escape", "--cases", "x", "--paths", "x"]),
    ("rsi_trial.py", ["trial", "--blocks", "2", "--cases", "x", "--paths", "x"]),
    ("archive_extension_evidence.py", ["--series", "../escape"]),
    ("archive_extension_evidence.py", ["--series", "missing-fixture-series"]),
])
def test_invalid_workflow_arguments_are_rejected_before_execution(script, args):
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], capture_output=True)
    assert result.returncode == 2
