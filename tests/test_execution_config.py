"""Execution target and publication guards, using temporary local repositories."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import remote_config
import publish_remote
import history_revision


@pytest.fixture
def configured(tmp_path, monkeypatch):
    monkeypatch.setattr(remote_config, "ROOT", tmp_path)
    monkeypatch.delenv("MCAP_OPS_TEST_HOST", raising=False)
    monkeypatch.delenv("MCAP_OPS_TEST_ROOT", raising=False)
    (tmp_path / ".mcap-ops.local.json").write_text(json.dumps({
        "host": "test-runner", "destination": "/work/project",
    }))
    return tmp_path


def test_target_precedence(configured, monkeypatch):
    assert remote_config.execution_target() == ("test-runner", "/work/project")
    monkeypatch.setenv("MCAP_OPS_TEST_HOST", "env-runner")
    monkeypatch.setenv("MCAP_OPS_TEST_ROOT", "/work/environment/")
    assert remote_config.execution_target() == ("env-runner", "/work/environment")
    assert remote_config.execution_target("explicit", "/work/explicit") == ("explicit", "/work/explicit")


def test_missing_target_fails_without_network(configured):
    (configured / ".mcap-ops.local.json").unlink()
    with pytest.raises(ValueError, match="MCAP_OPS_TEST_HOST"):
        remote_config.execution_target()


def test_archived_revision_resolution(tmp_path, monkeypatch):
    monkeypatch.setattr(history_revision, "ROOT", tmp_path)
    assert history_revision.resolve_revision("old") == "old"
    path = tmp_path / "docs/performance/publication/commit-map.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({"commits": {"abc123": "new-one", "abc456": "new-two"}}))
    assert history_revision.resolve_revision("abc123") == "new-one"
    assert history_revision.resolve_revision("unknown") == "unknown"
    with pytest.raises(ValueError, match="ambiguous"):
        history_revision.resolve_revision("abc")


@pytest.mark.parametrize("host,destination", [
    ("-oProxyCommand=bad", "/work/project"),
    ("bad host", "/work/project"),
    ("runner", "relative/path"),
    ("runner", "/"),
    ("runner", "/work/../other"),
    ("runner", "/work/has space"),
    ("runner", "/work/$(command)"),
])
def test_unsafe_targets_fail(configured, host, destination):
    with pytest.raises(ValueError):
        remote_config.execution_target(host, destination)


@pytest.mark.parametrize("dirty", [False, True])
def test_publication_backs_up_only_unchanged_committed_deletions(tmp_path, dirty):
    def git(path, *args):
        return subprocess.check_output(["git", *args], cwd=path, text=True).strip()

    author = tmp_path / "author"
    author.mkdir()
    git(author, "init", "-q", "-b", "main")
    git(author, "config", "user.name", "fixture")
    git(author, "config", "user.email", "fixture@example.invalid")
    git(author, "config", "commit.gpgsign", "false")
    (author / "old.txt").write_text("original\n")
    (author / ".gitignore").write_text(".artifacts/\n")
    git(author, "add", ".")
    git(author, "commit", "-qm", "initial")
    old = git(author, "rev-parse", "HEAD")
    destination = tmp_path / "execution"
    git(tmp_path, "clone", "-q", str(author), str(destination))
    git(author, "rm", "old.txt")
    git(author, "commit", "-qm", "remove old source")
    head = git(author, "rev-parse", "HEAD")
    bundle = tmp_path / "source.bundle"
    git(author, "bundle", "create", str(bundle), "main")
    if dirty:
        (destination / "old.txt").write_text("unrelated edit\n")
    import hashlib
    payload = {
        "destination": str(destination), "bundle": str(bundle), "head": head,
        "superseded": {}, "target": {"host": "fixture", "destination": str(destination)},
        "files": {".gitignore": hashlib.sha256((author / ".gitignore").read_bytes()).hexdigest()},
    }
    result = subprocess.run(
        [sys.executable, "-c", publish_remote.RECEIVE],
        input=json.dumps(payload), text=True, capture_output=True,
    )
    if dirty:
        assert result.returncode != 0
        assert (destination / "old.txt").read_text() == "unrelated edit\n"
        assert git(destination, "rev-parse", "HEAD") == old
    else:
        assert result.returncode == 0, result.stderr
        assert not (destination / "old.txt").exists()
        assert (destination / ".artifacts/rsi/superseded" / old / "old.txt").read_text() == "original\n"
        assert git(destination, "rev-parse", "HEAD") == head
        assert git(destination, "status", "--porcelain") == ""
