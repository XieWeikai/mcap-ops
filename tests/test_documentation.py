"""Keep maintained guides bilingual without duplicating historical measurements."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_readme_is_english_and_guides_have_language_pairs():
    assert not re.search(r"[\u3400-\u9fff]", (ROOT / "README.md").read_text())
    for section, subdirs in [("docs", ["", "guides"]), ("RSI", ["", "templates"])]:
        for subdir in subdirs:
            for english in (ROOT / section / subdir).glob("*.md"):
                chinese = ROOT / section / "zh" / subdir / english.name
                assert chinese.is_file(), str(chinese)
                assert "Language: English" in english.read_text(), str(english)
                assert "语言：中文" in chinese.read_text(), str(chinese)
                assert not re.search(r"[\u3400-\u9fff]", english.read_text()), str(english)
