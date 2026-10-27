#!/usr/bin/env python3
"""Publish a verified static build to gh-pages without building locally."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / ".artifacts/docs/site"


def git(*args, cwd=ROOT):
    return subprocess.check_output(
        ["git", "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential", *args],
        cwd=cwd, text=True,
    ).strip()


def validate_build(site, head):
    metadata = json.loads((site / "build.json").read_text())
    if metadata["source_revision"] != head or metadata["dirty"]:
        raise ValueError("Build must come from the clean, current source revision")
    for name in ("index.html", "zh/index.html", ".nojekyll",
                 "rustdoc/mcap_ops_core/index.html", "rustdoc/mcap_ops_io/index.html"):
        if not (site / name).is_file():
            raise ValueError(f"Incomplete site: missing {name}")
    if any(path.is_symlink() for path in site.rglob("*")):
        raise ValueError("Static publication must not contain symbolic links")


def main():
    if git("status", "--porcelain") or git("branch", "--show-current") != "main":
        raise SystemExit("Publish only from a clean main checkout")
    head = git("rev-parse", "HEAD")
    validate_build(SITE, head)
    origin = git("remote", "get-url", "origin")
    if git("ls-remote", origin, "refs/heads/main").split()[0] != head:
        raise SystemExit("Push the source main revision before publishing its documentation")
    existing = git("ls-remote", origin, "refs/heads/gh-pages")
    with tempfile.TemporaryDirectory(prefix="publish-", dir=ROOT / ".artifacts/docs") as temp:
        checkout = Path(temp)
        if existing:
            git("clone", "--quiet", "--single-branch", "--branch", "gh-pages", origin, temp)
        else:
            git("init", "--quiet", "--initial-branch=gh-pages", cwd=checkout)
            git("remote", "add", "origin", origin, cwd=checkout)
        git("config", "user.name", git("config", "user.name"), cwd=checkout)
        git("config", "user.email", git("config", "user.email"), cwd=checkout)
        # Replace only our disposable clone, never the author's working tree.
        for path in checkout.iterdir():
            if path.name == ".git":
                continue
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
        shutil.copytree(SITE, checkout, dirs_exist_ok=True)
        git("add", "--all", cwd=checkout)
        if git("status", "--porcelain", cwd=checkout):
            git("commit", "-m", f"docs: publish site for {head[:12]}", cwd=checkout)
            git("push", "origin", "HEAD:gh-pages", cwd=checkout)
        print(f"Published static documentation for {head}; GitHub Pages deployment follows.")


if __name__ == "__main__":
    main()
