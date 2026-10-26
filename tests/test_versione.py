import re
from pathlib import Path

RADICE = Path(__file__).resolve().parent.parent


def leggi_versione():
    testo = (RADICE / "docs" / "versione.js").read_text(encoding="utf-8")
    return re.search(r'const VERSIONE = "([^"]+)"', testo).group(1)


def test_versione_formato():
    assert re.fullmatch(r"\d+\.\d+\.\d+", leggi_versione())


def test_versione_coincide_con_changelog():
    changelog = (RADICE / "CHANGELOG.md").read_text(encoding="utf-8")
    prima = re.search(r"^## (\d+\.\d+\.\d+)", changelog, re.M).group(1)
    assert prima == leggi_versione()
