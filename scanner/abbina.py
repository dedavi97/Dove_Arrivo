"""Unione delle stazioni di più fonti: quali stazioni di una fonte (es. Trenord) sono le
stesse della fonte principale (Trenitalia), così diventano un solo pallino e ci si cambia."""
import csv
import math
import re
import unicodedata
from collections import Counter
from pathlib import Path

SOGLIA_METRI = 300
TABELLA_MANUALE = Path(__file__).resolve().parent / "abbinamenti_manuali.csv"


def distanza_metri(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a.lat, a.lon, b.lat, b.lon))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371000 * 2 * math.asin(math.sqrt(h))


def _parole(nome):
    senza_accenti = unicodedata.normalize("NFD", nome).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", senza_accenti).split()


def stesso_nome(a, b):
    """Uguali, o uno è l'inizio dell'altro parola per parola: "Novara" e "Novara Nord",
    "Rovato" e "Rovato Fn", "Milano Porta Garibaldi" e "... Passante"."""
    pa, pb = _parole(a), _parole(b)
    corto, lungo = sorted((pa, pb), key=len)
    return bool(corto) and lungo[:len(corto)] == corto


def carica_manuali(percorso=TABELLA_MANUALE):
    """{(fonte, id nella fonte): id Trenitalia} dalla tabella manuale del repo."""
    if not percorso.exists():
        return {}
    with open(percorso, encoding="utf-8", newline="") as f:
        return {(r["fonte"], r["id_fonte"]): r["id_trenitalia"] for r in csv.DictReader(f)}


def abbina(stazioni_fonte, stazioni_base, nome_fonte, codice_base=None, manuali=None):
    """Per ogni stazione della fonte, l'id della stessa stazione nella base, o None se è nuova.

    Ordine: tabella manuale; stesso codice (codice_base(id) -> id nella base) ma solo entro
    SOGLIA_METRI, perché alcuni codici coincidono per caso (es. Lugano Paradiso e
    Buttapietra); stesso nome entro SOGLIA_METRI. Restituisce (abbinamenti, conteggi).
    """
    manuali = manuali or {}
    abbinamenti, conteggi = {}, Counter()
    for id_fonte, s in stazioni_fonte.items():
        scelta, modo = None, "nuova"
        manuale = manuali.get((nome_fonte, id_fonte))
        if manuale in stazioni_base:
            scelta, modo = manuale, "tabella manuale"
        else:
            codice = codice_base(id_fonte) if codice_base else None
            if codice in stazioni_base and distanza_metri(s, stazioni_base[codice]) <= SOGLIA_METRI:
                scelta, modo = codice, "codice"
            else:
                vicine = [
                    (distanza_metri(s, b), b.id) for b in stazioni_base.values()
                    if abs(b.lat - s.lat) < 0.01 and stesso_nome(s.nome, b.nome)
                ]
                vicine = [v for v in vicine if v[0] <= SOGLIA_METRI]
                if vicine:
                    scelta, modo = min(vicine)[1], "nome e distanza"
        abbinamenti[id_fonte] = scelta
        conteggi[modo] += 1
    return abbinamenti, conteggi
