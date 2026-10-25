#!/usr/bin/env python3
"""Synchronize repository-relative source paths without flattening directories.

This transfers source only. It never copies .git, deletes files, or runs tests.
Git publication is a separate guarded bundle/fast-forward operation.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="reference-linux")
    parser.add_argument("--destination", default=".")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
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
