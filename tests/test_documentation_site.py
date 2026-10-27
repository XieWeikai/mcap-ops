"""Check public signatures/examples and the source-to-site publication boundary."""
import inspect
import json
from pathlib import Path
import re
import sys

import mcap_ops as ops
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_docs import document_map, rewrite_markdown
from check_docs_site import check
from publish_docs import validate_build


OPERATORS = [name for name in ops.__all__ if callable(getattr(ops, name))]


@pytest.mark.parametrize("language", ["", "zh"])
@pytest.mark.parametrize("name", OPERATORS)
def test_operator_reference_matches_installed_interface_and_runs(name, language):
    path = ROOT / "docs" / language / "reference/python" / f"{name}.md"
    text = path.read_text()
    blocks = re.findall(r"```python\n(.*?)```", text, re.S)
    assert len(blocks) == 2, path
    declaration = blocks[0].strip().replace("mcap_ops.", "def ", 1) + ":\n    pass"
    namespace = {}
    exec(declaration, namespace)
    assert inspect.signature(namespace[name]) == inspect.signature(getattr(ops, name)), path
    exec(compile(blocks[1], str(path), "exec"), {})


@pytest.mark.parametrize("language", ["", "zh"])
@pytest.mark.parametrize("page", ["first-pipeline", "quality"])
def test_tutorial_examples(language, page):
    path = ROOT / "docs" / language / "tutorials" / f"{page}.md"
    for block in re.findall(r"```python\n(.*?)```", path.read_text(), re.S):
        exec(compile(block, str(path), "exec"), {})


def test_every_export_has_a_reference_and_every_guide_link_resolves():
    assert {p.stem for p in (ROOT / "docs/reference/python").glob("*.md")} == set(OPERATORS)
    documents = document_map()
    assert not any("performance" in p.relative_to(ROOT).parts for p in documents)
    assert documents[ROOT / "RSI/zh/README.md"] == Path("zh/rsi/index.md")
    for source in documents:
        text = rewrite_markdown(source.read_text(), source, documents, "test-revision")
        assert "Language: English" not in text
        assert "语言：中文" not in text
    source = ROOT / "docs/README.md"
    text = rewrite_markdown(source.read_text(), source, documents, "test-revision")
    assert "../RSI/" not in text
    assert "test-revision/docs/performance/" in text


def test_publication_rejects_dirty_stale_incomplete_or_linked_builds(tmp_path):
    def metadata(revision="current", dirty=False):
        (tmp_path / "build.json").write_text(json.dumps({
            "source_revision": revision, "dirty": dirty,
        }))
    metadata(dirty=True)
    with pytest.raises(ValueError, match="clean"):
        validate_build(tmp_path, "current")
    metadata("old")
    with pytest.raises(ValueError, match="current"):
        validate_build(tmp_path, "current")
    metadata()
    with pytest.raises(ValueError, match="Incomplete"):
        validate_build(tmp_path, "current")
    for name in ("index.html", "zh/index.html", ".nojekyll",
                 "rustdoc/mcap_ops_core/index.html", "rustdoc/mcap_ops_io/index.html"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
    validate_build(tmp_path, "current")
    (tmp_path / "linked").symlink_to(tmp_path / "index.html")
    with pytest.raises(ValueError, match="symbolic"):
        validate_build(tmp_path, "current")


def test_rust_symbol_index_covers_public_items():
    for language in ("", "zh"):
        text = (ROOT / "docs" / language / "reference/rust.md").read_text()
        for crate in ("core", "io"):
            for source in (ROOT / "crates" / crate / "src").glob("*.rs"):
                module = "" if source.stem == "lib" else source.stem + "/"
                for kind, name in re.findall(r"^pub (struct|enum|trait|type|fn) (\w+)",
                                            source.read_text(), re.M):
                    assert f"mcap_ops_{crate}/{module}{kind}.{name}.html" in text


def test_site_links_accept_rustdoc_fragments_and_reject_missing_lines(tmp_path):
    required = [
        "rustdoc/mcap_ops_core/struct.Signal.html",
        "rustdoc/mcap_ops_io/mcap_ops/trait.SignalDecoder.html",
    ]
    for locale in ("", "zh/"):
        for route in ("", "tutorials/", "reference/", "rsi/", "reference/python/resample/"):
            required.append(locale + route + "index.html")
    for name in required:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("<html></html>")
    (tmp_path / "build.json").write_text(json.dumps({"source_revision": "current", "dirty": False}))
    source = tmp_path / "rustdoc/src/lib.rs.html"
    source.parent.mkdir(parents=True)
    source.write_text('<a id="7"></a><a id="20"></a><a id="impl-From%3CError%3E"></a>')
    (tmp_path / "index.html").write_text(
        '<a href="rustdoc/src/lib.rs.html#7-20">lines</a>'
        '<a href="rustdoc/src/lib.rs.html#impl-From%3CError%3E">impl</a>'
    )
    check(tmp_path)
    source.write_text('<a id="7"></a>')
    with pytest.raises(AssertionError, match="missing anchor"):
        check(tmp_path)
