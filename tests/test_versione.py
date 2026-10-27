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


def test_file_del_sito_con_la_versione_nel_nome():
    """index.html chiama style.css e gli script con ?v=VERSIONE: dopo un aggiornamento il
    browser non mescola file vecchi e nuovi. Va aggiornato insieme a VERSIONE."""
    html = (RADICE / "docs" / "index.html").read_text(encoding="utf-8")
    locali = re.findall(r'(?:src|href)="((?!https?:)[^"]+\.(?:js|css)[^"]*)"', html)
    assert len(locali) == 5
    for riferimento in locali:
        assert riferimento.endswith(f"?v={leggi_versione()}"), riferimento
