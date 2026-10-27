"""Sito in locale per Avvia_Locale.bat: python -m scanner.servi_locale [porta]

Come `python -m http.server --directory docs`, ma dice al browser di ricontrollare sempre i
file (Cache-Control: no-cache): così dopo un aggiornamento non mescola pezzi vecchi e nuovi.
"""
import functools
import http.server
import sys
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"
PORTA = 8765


class SenzaCache(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else PORTA
    gestore = functools.partial(SenzaCache, directory=str(DOCS))
    with http.server.ThreadingHTTPServer(("127.0.0.1", porta), gestore) as server:
        print(f"Sito in locale su http://localhost:{porta} (chiudi questa finestra per fermarlo)")
        server.serve_forever()


if __name__ == "__main__":
    main()
