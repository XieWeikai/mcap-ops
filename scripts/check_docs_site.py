#!/usr/bin/env python3
"""Check generated internal URLs, anchors, required routes, and build identity."""
import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

SITE_URL = "https://xieweikai.github.io/mcap-ops/"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        for key in ("href", "src"):
            if attributes.get(key):
                self.links.append(attributes[key])


def check(site):
    site = site.resolve()
    documents = {}
    for path in site.rglob("*.html"):
        parser = Links()
        parser.feed(path.read_text())
        documents[path] = parser
    checked = 0
    for path, parser in documents.items():
        for link in parser.links:
            if link.startswith(SITE_URL):
                link = "/" + link[len(SITE_URL):]
            elif link.startswith("/mcap-ops/"):
                link = "/" + link[len("/mcap-ops/"):]
            parsed = urlsplit(link)
            if parsed.scheme or parsed.netloc:
                continue
            target = (
                site / unquote(parsed.path).lstrip("/") if parsed.path.startswith("/")
                else path.parent / unquote(parsed.path) if parsed.path else path
            ).resolve()
            if target.is_dir():
                target = target / "index.html"
            assert target.is_relative_to(site), (path, link, "escapes site")
            assert target.is_file(), (path.relative_to(site), link, "missing target")
            fragment = unquote(parsed.fragment)
            if fragment and target in documents:
                ids = documents[target].ids
                source_range = (
                    target.is_relative_to(site / "rustdoc/src")
                    and re.fullmatch(r"\d+-\d+", fragment)
                    and all(line in ids for line in fragment.split("-"))
                )
                assert fragment in ids or parsed.fragment in ids or source_range, (
                    path.relative_to(site), link, "missing anchor"
                )
            checked += 1
    metadata = json.loads((site / "build.json").read_text())
    for locale in ("", "zh/"):
        for route in ("", "tutorials/", "reference/", "rsi/", "reference/python/resample/"):
            assert (site / locale / route / "index.html").is_file(), (locale, route)
    assert (site / "rustdoc/mcap_ops_core/struct.Signal.html").is_file()
    assert (site / "rustdoc/mcap_ops_io/mcap_ops/trait.SignalDecoder.html").is_file()
    print(f"Checked {len(documents)} HTML pages, {checked} internal URLs/anchors; "
          f"source {metadata['source_revision'][:12]}, dirty={metadata['dirty']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("site", nargs="?", type=Path, default=Path(".artifacts/docs/site"))
    check(parser.parse_args().site)
