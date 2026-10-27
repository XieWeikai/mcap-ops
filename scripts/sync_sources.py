#!/usr/bin/env python3
"""Synchronize repository-relative source paths without flattening directories.

This transfers source only. It never copies .git, deletes files, or runs tests.
Git publication is a separate guarded bundle/fast-forward operation.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile
import json
import shlex
from remote_config import execution_target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host")
    parser.add_argument("--destination")
    args = parser.parse_args()
    args.host, args.destination = execution_target(args.host, args.destination)
    root = Path(__file__).resolve().parents[1]
    receipt = root / '.artifacts/rsi/sync-receipt.json'
    if receipt.exists():
        previous = json.loads(receipt.read_text())
        target = {'host': args.host, 'destination': args.destination}
        if previous.get('target', target) != target:
            raise RuntimeError('execution target differs from the last publication receipt; inspect it first')
        expected = previous['head']
        actual = subprocess.check_output(['ssh', args.host, shlex.join(['git', '-C', args.destination, 'rev-parse', 'HEAD'])], text=True).strip()
        if actual != expected:
            raise RuntimeError('remote HEAD changed since the last verified publication; inspect it before synchronizing')
    entries = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
    ).split(b"\0")
    names = sorted({entry for entry in entries if entry and (root / entry.decode()).is_file()})
    if any(name.startswith((b".git/", b".tools/", b".artifacts/")) for name in names):
        raise RuntimeError("private paths unexpectedly included in source manifest")
    with tempfile.NamedTemporaryFile() as manifest:
        manifest.write(b"\0".join(names) + b"\0")
        manifest.flush()
        subprocess.run([
            "rsync", "-az", "--from0", "--files-from=" + manifest.name,
            str(root) + "/", f"{args.host}:{args.destination}/",
        ], check=True)
    print(f"Synchronized {len(names)} exact repository-relative paths")


if __name__ == "__main__":
    main()
