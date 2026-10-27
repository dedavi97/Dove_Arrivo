"""Le fonti degli orari: dove scaricarle, come capire se sono cambiate, come leggerle e unirle.

Ogni fonte si legge a parte; poi le stazioni delle fonti secondarie si abbinano a quelle
della principale (Trenitalia) e le corse si uniscono. Una fonte scaduta o non scaricabile
non sparisce in silenzio: si tengono i suoi dati già scaricati e il riepilogo lo segnala.
"""
import datetime
import json
import re
from dataclasses import dataclass, field
from typing import Callable, Optional

from . import abbina, gtfs, scarica

AVVISO_SCADENZA_GIORNI = 30


@dataclass
class Fonte:
    nome: str
    url: str
    url_versione: str                     # una risorsa piccola che cambia a ogni nuova pubblicazione
    leggi_versione: Callable[[str], str]  # testo scaricato -> versione
    file: str                             # nome del file nella cache
    categoria: Callable                   # riga di routes.txt -> categoria da mostrare, o None per escluderla
    attribuzione: str
    obbligatoria: bool = False            # senza la fonte principale non si costruisce nulla
    prefisso_id: str = ""                 # per gli id delle stazioni nuove (non abbinate)
    codice_base: Optional[Callable[[str], str]] = None  # id nella fonte -> id Trenitalia da provare
    codici_uic: bool = True               # gli id sono codici UIC ("83..." = Italia)?


def categoria_trenord(route):
    """route_type 2 = treno (3 = autobus, escluso). La categoria è la linea: "S5", "RE4", "R23"."""
    if route["route_type"] != "2":
        return None
    nome = route["route_short_name"].replace("_", "")
    return nome if re.fullmatch(r"[A-Z]+\d*", nome) else "R"  # "Trenord (linea non specificata)"


def codice_trenord(id_fonte):
    """Trenord "S00219" -> Trenitalia "830000219" (da verificare con la distanza, vedi abbina)."""
    return "8300" + id_fonte[1:] if re.fullmatch(r"S\d{5}", id_fonte) else None


TRENITALIA = Fonte(
    nome="Trenitalia",
    url="https://github.com/deryclem/trenitalia-gtfs/raw/main/gtfs-trenitalia.zip",
    url_versione="https://raw.githubusercontent.com/deryclem/trenitalia-gtfs/main/.last_publication_timestamp",
    leggi_versione=str.strip,
    file="gtfs-trenitalia.zip",
    categoria=gtfs.categorie_trenitalia({"REG", "RV", "SFM", "MET"}),
    attribuzione="Orario Trenitalia: Trenitalia S.p.A. / CCISS MMTIS (NAP), conversione GTFS di Clément Desouche, CC-BY-4.0.",
    obbligatoria=True,
)

TRENORD = Fonte(
    nome="Trenord",
    url="https://www.dati.lombardia.it/download/3z4k-mxz9/application%2Fzip",
    url_versione="https://www.dati.lombardia.it/api/views/3z4k-mxz9.json",
    leggi_versione=lambda testo: str(json.loads(testo).get("viewLastModified")),
    file="trenord.zip",
    categoria=categoria_trenord,
    attribuzione="Orario Trenord: Regione Lombardia (dati.lombardia.it) / Trenord, CC-BY-4.0.",
    prefisso_id="TN-",
    codice_base=codice_trenord,
    codici_uic=False,
)

FONTI = [TRENITALIA, TRENORD]


@dataclass
class Letta:
    fonte: Fonte
    corse: list
    stazioni: dict
    info: dict = field(default_factory=dict)
    forme: dict = field(default_factory=dict)  # {(operatore, shape_id): [(lat, lon), ...]}


def prepara(fonte, avvisi, barra=None):
    """Percorso dell'orario nella cache, riscaricato solo se è cambiato. None se la fonte
    (non obbligatoria) non è disponibile e non è mai stata scaricata."""
    cache = scarica.CACHE / fonte.file
    timbro = cache.with_suffix(".data")
    try:
        versione = fonte.leggi_versione(scarica.scarica_testo(fonte.url_versione))
    except (ConnectionError, FileNotFoundError, ValueError) as errore:
        versione = None
        problema = errore
    gia = timbro.read_text(encoding="utf-8").strip() if timbro.exists() else None
    if cache.exists() and (versione is None or versione == gia):
        if versione is None:
            avvisi.append(f"{fonte.nome}: impossibile controllare se c'è un orario nuovo, uso quello già scaricato ({problema})")
        print(f"    {fonte.nome}: orario già scaricato e ancora attuale")
        return cache
    try:
        print(f"    {fonte.nome}: scarico l'orario")
        scarica.scarica_file(fonte.url, fonte.file, barra)
        timbro.write_text(versione or "", encoding="utf-8")
        return cache
    except (ConnectionError, FileNotFoundError) as errore:
        if cache.exists():
            avvisi.append(f"ATTENZIONE {fonte.nome}: orario nuovo non scaricabile, uso la copia già scaricata ({errore})")
            return cache
        if fonte.obbligatoria:
            raise
        avvisi.append(f"ATTENZIONE {fonte.nome}: orario non scaricabile e mai scaricato prima: i suoi treni MANCANO ({errore})")
        return None


def leggi(fonte, percorso, giorni, oggi, avvisi, barra=None):
    """Corse della fonte nei giorni tipo. Se l'orario è scaduto (nessun giorno tipo dentro la
    sua validità) si usano i suoi ultimi mercoledì validi: i dati vecchi restano e si segnala."""
    archivio = gtfs.apri(percorso)
    inizio, fine = gtfs.validita(archivio)
    scaduta = not any(inizio <= g <= fine for g in giorni)
    giorni_fonte = giorni
    if scaduta:
        giorni_fonte = gtfs.scegli_giorni_finali(inizio, fine, len(giorni))
        avvisi.append(
            f"ATTENZIONE {fonte.nome}: orario SCADUTO il {fine:%d/%m/%Y}. Tengo i suoi dati vecchi "
            f"(mercoledì {', '.join(f'{g:%d/%m}' for g in giorni_fonte)}) finché non ne esce uno nuovo."
        )
    elif fine < oggi + datetime.timedelta(days=AVVISO_SCADENZA_GIORNI):
        avvisi.append(f"{fonte.nome}: l'orario scade il {fine:%d/%m/%Y}, dopo servirà quello nuovo")
    corse, stazioni, avvisi_lettura = gtfs.leggi_corse(archivio, giorni_fonte, fonte.categoria, barra, fonte.nome)
    avvisi += [f"{fonte.nome}: {a}" for a in avvisi_lettura]
    if not fonte.codici_uic:
        for s in stazioni.values():
            s.uic = None
    info = {
        "nome": fonte.nome,
        "validita_dal": inizio.isoformat(),
        "validita_al": fine.isoformat(),
        "scaduta": scaduta,
        "attribuzione": fonte.attribuzione,
    }
    forme = gtfs.leggi_forme(archivio, {c.forma for c in corse if c.forma})
    return Letta(fonte, corse, stazioni, info, {(fonte.nome, f): p for f, p in forme.items()})


def unisci(lette, avvisi, manuali=None):
    """Unisce le fonti lette (la prima è la principale). Le stazioni delle altre fonti abbinate
    alla principale prendono il suo id; le nuove un id col prefisso della fonte.
    Restituisce (corse, stazioni); in ogni Letta.info aggiunge gli abbinamenti."""
    base = lette[0]
    stazioni = dict(base.stazioni)
    corse = list(base.corse)
    manuali = abbina.carica_manuali() if manuali is None else manuali
    for (nome_fonte, id_fonte), id_base in manuali.items():
        if id_base not in base.stazioni:
            avvisi.append(f"tabella abbinamenti: {nome_fonte} {id_fonte} -> {id_base}, ma {id_base} non esiste in {base.fonte.nome}")
    for letta in lette[1:]:
        usate = {s for c in letta.corse for s, _ in c.fermate}
        abbinamenti, conteggi = abbina.abbina(
            {i: letta.stazioni[i] for i in usate}, base.stazioni, letta.fonte.nome, letta.fonte.codice_base, manuali,
        )
        nuovo_id = {}
        for i in usate:
            if abbinamenti[i]:
                nuovo_id[i] = abbinamenti[i]
            else:
                s = letta.stazioni[i]
                nuovo_id[i] = letta.fonte.prefisso_id + i
                stazioni[nuovo_id[i]] = gtfs.Stazione(nuovo_id[i], s.nome, s.lat, s.lon, s.uic)
        for c in letta.corse:
            c.fermate = [(nuovo_id[s], m) for s, m in c.fermate]
        corse += letta.corse
        letta.info["abbinamenti"] = dict(conteggi)
        letta.info["nuove"] = sorted(letta.stazioni[i].nome for i in usate if not abbinamenti[i])
    return corse, stazioni
