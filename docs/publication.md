# Public History and Evidence Identity

**Language: English | [Chinese](zh/publication.md)**

[Documentation](README.md) · [Performance evidence](performance.md)

## Publication migration

Before public release, deployment-specific identifiers were removed from the
reachable history: execution aliases, account-specific workspace paths, and
operating-system boot identifiers. Documentation describes Linux hardware,
software, and measurement conditions instead. Execution coordinates now come
from ignored local configuration or environment variables.

This is a publication migration, not another optimization campaign. It preserves
all 89 pre-migration commits and their parent relationships, all 380 recorded
decisions, measured samples, performance summaries, and acceptance conclusions.
The production operator source trees are byte-identical at every mapped commit.

## Commit references

Rewriting metadata and documentation changes Git commit IDs. The checked-in
[commit map](performance/publication/commit-map.json) maps each archived ID to
its public equivalent. Historical reports retain their original IDs as stable
archive identifiers; use the map to find their public Git revisions.

Reference preparation and historical candidate helpers use
`scripts/history_revision.py` to resolve archived IDs automatically. Full Git
history is still required. The mapping is not an extra branch containing private
history, and a numeric implementation has not changed merely because its
containing commit was rewritten.

## What a hash means after redaction

- Measurement samples, iteration counts, decisions, numeric results, and
  production source/extension/wheel hashes are unchanged.
- Text logs and JSON metadata may have different bytes after identifiers and
  absolute paths are removed. References to those files use hashes of the
  published, redacted bytes.
- A hash of an untracked raw profile or binary still identifies the original
  artifact. It does not imply that artifact is included in Git.
- An original private recovery bundle is retained outside the published tree;
  it is not a public release asset.

Do not describe redacted logs as byte-identical originals, or a metadata migration
as a newly executed benchmark. Original measurements remain the basis of the
reported performance claims.

## Existing clones

Publication history is intentionally rewritten. For an old clone, preserve local
work first and prefer a fresh clone of the public repository. Do not merge old
private history back into public main. New contributions and releases should use
the public commit IDs.
