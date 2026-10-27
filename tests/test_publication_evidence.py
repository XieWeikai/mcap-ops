"""Validate published identities without rewriting historical reports."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from history_revision import resolve_revision


def test_published_decisions_still_match_their_measurements_and_logs():
    counts = []
    for suffix, expected in [("", (60, 27)), ("extension", (20, 7)), ("per-op10", (300, 23))]:
        directory = ROOT / "docs/performance" / suffix
        records = [json.loads(path.read_text()) for path in (directory / "results").glob("*.json")]
        assert (len(records), sum(row["decision"] == "accepted" for row in records)) == expected
        for row in records:
            data = directory / "data" / (row["label"] + ".json")
            assert hashlib.sha256(data.read_bytes()).hexdigest() == row["measurement_sha256"]
            log = directory / "evidence" / (row["label"] + ".log")
            if log.exists():
                assert hashlib.sha256(log.read_bytes()).hexdigest() == row["validation_sha256"]
            if "sensitivity_sha256" in row:
                sensitivity = directory / "data" / (row["label"] + "-sensitivity.json")
                assert hashlib.sha256(sensitivity.read_bytes()).hexdigest() == row["sensitivity_sha256"]
        counts.append(len(records))
    assert sum(counts) == 380


def test_publication_map_resolves_all_commits_and_reference_sources():
    path = ROOT / "docs/performance/publication/commit-map.json"
    if not path.exists():
        return
    mapping = json.loads(path.read_text())["commits"]
    assert len(mapping) == 89 and len(set(mapping.values())) == 89
    for revision in mapping.values():
        subprocess.run(["git", "cat-file", "-e", revision + "^{commit}"], cwd=ROOT, check=True)
    source = json.loads((ROOT / "docs/performance/per-op10/final/baseline-manifest.json").read_text())
    revision = resolve_revision(source["source_commit"])
    for name, digest in source["source_sha256"].items():
        content = subprocess.check_output(["git", "show", f"{revision}:{name}"], cwd=ROOT)
        assert hashlib.sha256(content).hexdigest() == digest, name


def test_production_sources_match_the_measured_release():
    report = ROOT / "docs/performance/per-op10/final/verification.json"
    for name, digest in json.loads(report.read_text())["source_sha256"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
