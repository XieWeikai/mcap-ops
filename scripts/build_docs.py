#!/usr/bin/env python3
"""Build bilingual guides and compiler-generated Rust references on Linux."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE_URL = "https://xieweikai.github.io/mcap-ops/"
REPO_URL = "https://github.com/XieWeikai/mcap-ops"
OUTPUT = ROOT / ".artifacts/docs"


def document_map(root=ROOT):
    """Only maintained guides enter the site; historical evidence stays in Git."""
    result = {}
    for section in ("docs", "RSI"):
        for source in sorted((root / section).rglob("*.md")):
            relative = source.relative_to(root / section)
            if relative.parts[0] == "performance":
                continue
            language = "zh" if relative.parts[0] == "zh" else "en"
            if language == "zh":
                relative = Path(*relative.parts[1:])
            if section == "RSI":
                relative = Path("rsi") / relative
                if relative.name == "README.md":
                    relative = relative.with_name("index.md")
            elif relative == Path("README.md"):
                relative = Path("handbook.md")
            result[source] = Path(language) / relative
    return result


def rewrite_markdown(text, source, documents, revision, root=ROOT):
    # The theme switches locale while preserving the page; Git keeps language links.
    text = re.sub(r"^\*\*(?:Language: English|语言：中文).*?\*\*\n", "", text, flags=re.M)
    destination = documents[source]

    def replace(match):
        prefix, link, suffix = match.groups()
        parsed = urlsplit(link)
        if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.startswith("/"):
            return match.group()
        target = (source.parent / unquote(parsed.path)).resolve()
        if not target.is_relative_to(root):
            raise ValueError(f"link escapes repository: {source}: {link}")
        if not target.exists():
            raise ValueError(f"missing link: {source}: {link}")
        if target in documents:
            mapped = documents[target]
            if mapped.parts[0] != destination.parts[0]:
                route = mapped.relative_to(mapped.parts[0])
                route = route.with_suffix("").as_posix()
                if route == "index":
                    route = ""
                elif route.endswith("/index"):
                    route = route[:-5]
                else:
                    route += "/"
                url = SITE_URL + ("zh/" if mapped.parts[0] == "zh" else "") + route
            else:
                url = Path(os.path.relpath(mapped, destination.parent)).as_posix()
        elif target.is_relative_to(root / "docs/assets"):
            url = urlsplit(SITE_URL).path + "assets/" + quote(
                target.relative_to(root / "docs/assets").as_posix()
            )
        else:
            kind = "tree" if target.is_dir() else "blob"
            url = f"{REPO_URL}/{kind}/{revision}/{quote(target.relative_to(root).as_posix())}"
        if parsed.query:
            url += "?" + parsed.query
        if parsed.fragment:
            url += "#" + parsed.fragment
        return prefix + url + suffix

    # Code examples are literal. Source guides use inline Markdown links.
    blocks = re.split(r"(```.*?```)", text, flags=re.S)
    for i in range(0, len(blocks), 2):
        blocks[i] = re.sub(r"(!?\[[^\]]*\]\()([^)\s]+)(\))", replace, blocks[i])
    return "".join(blocks)


def main():
    if sys.platform != "linux":
        raise SystemExit("Build in the configured Linux execution checkout; see AGENTS.md.")
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    staging = OUTPUT / "source"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    documents = document_map()
    for source, destination in documents.items():
        path = staging / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rewrite_markdown(source.read_text(), source, documents, revision))
    shutil.copytree(ROOT / "docs/assets", staging / "assets")
    subprocess.run([sys.executable, "-m", "mkdocs", "build", "--strict"], cwd=ROOT, check=True)
    env = os.environ.copy()
    env["CARGO_TARGET_DIR"] = str(OUTPUT / "cargo")
    env["RUSTDOCFLAGS"] = "-D warnings"
    subprocess.run(
        ["cargo", "doc", "--locked", "--no-deps", "-p", "mcap-ops-core", "-p", "mcap-ops-io"],
        cwd=ROOT, env=env, check=True,
    )
    site = OUTPUT / "site"
    shutil.copytree(OUTPUT / "cargo/doc", site / "rustdoc")
    (site / "rustdoc/index.html").write_text("""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MCAP Ops Rust API</title></head><body>
<main><h1>MCAP Ops Rust API</h1>
<p>Compiler-generated reference for the same source revision as the guides.</p>
<ul><li><a href="mcap_ops_core/index.html">mcap-ops-core</a>: file-independent operators</li>
<li><a href="mcap_ops_io/index.html">mcap-ops-io</a>: MCAP and media adapters</li></ul>
<p><a href="../reference/rust/">English guide</a> |
<a href="../zh/reference/rust/">Chinese guide</a></p></main></body></html>
""")
    (site / ".nojekyll").touch()
    (site / "build.json").write_text(json.dumps({
        "source_revision": revision, "dirty": dirty, "version": "0.1.0",
        "maintained_pages": len(documents), "languages": ["en", "zh"],
    }, indent=2) + "\n")
    for path in site.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            if any(value.encode() in data for value in (str(ROOT), str(Path.home()))):
                raise ValueError(f"Deployment path found in {path.relative_to(site)}")
    print(f"Built {len(documents)} maintained pages and Rust API documentation in {site}")


if __name__ == "__main__":
    main()
