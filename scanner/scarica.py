"""Download dei file sorgente, con cache su disco e nuovi tentativi."""
import time
import urllib.error
import urllib.request
from pathlib import Path

CACHE = Path(__file__).resolve().parent / "cache"
ATTESE_TRA_TENTATIVI = (5, 15, 45)  # secondi
AGENTE = "Dove_Arrivo-scanner (https://github.com/dedavi97/Dove_Arrivo)"


def _con_tentativi(funzione, descrizione):
    for tentativo, attesa in enumerate((0,) + ATTESE_TRA_TENTATIVI):
        if attesa:
            print(f"    nuovo tentativo tra {attesa} s...")
            time.sleep(attesa)
        try:
            return funzione()
        except urllib.error.HTTPError as errore:
            if errore.code == 404:  # il file non esiste: riprovare non serve
                raise FileNotFoundError(f"{descrizione}: file non trovato (404)") from errore
            ultimo = errore
            print(f"    {descrizione}: non riuscito ({errore})")
        except OSError as errore:
            ultimo = errore
            print(f"    {descrizione}: non riuscito ({errore})")
    raise ConnectionError(f"{descrizione}: impossibile dopo {tentativo + 1} tentativi ({ultimo})")


def scarica_testo(url):
    def leggi():
        richiesta = urllib.request.Request(url, headers={"User-Agent": AGENTE})
        with urllib.request.urlopen(richiesta, timeout=30) as risposta:
            return risposta.read().decode("utf-8").strip()
    return _con_tentativi(leggi, f"lettura di {url}")


def scarica_file(url, nome, avanzamento=None):
    """Scarica url in CACHE/nome passando da un file .part: se interrotto, il vecchio file resta intatto."""
    CACHE.mkdir(exist_ok=True)
    destinazione = CACHE / nome
    parziale = CACHE / (nome + ".part")

    def scarica():
        richiesta = urllib.request.Request(url, headers={"User-Agent": AGENTE})
        with urllib.request.urlopen(richiesta, timeout=60) as risposta, open(parziale, "wb") as file:
            totale = int(risposta.headers.get("Content-Length") or 0)
            fatti = 0
            while blocco := risposta.read(256 * 1024):
                file.write(blocco)
                fatti += len(blocco)
                if avanzamento and totale:
                    avanzamento(fatti / totale)
        parziale.replace(destinazione)
        return destinazione
    return _con_tentativi(scarica, f"download di {nome}")
