"""Resolve archived commit identities after a documented publication rewrite."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def resolve_revision(revision):
    path = ROOT / "docs/performance/publication/commit-map.json"
    if not path.exists():
        return revision
    mapping = json.loads(path.read_text())["commits"]
    matches = [new for old, new in mapping.items() if old.startswith(revision)]
    if len(matches) > 1:
        raise ValueError("ambiguous archived commit prefix")
    return matches[0] if matches else revision
