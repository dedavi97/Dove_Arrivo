"""Comune e abitanti di una stazione: confini comunali ISTAT (GeoJSON) + popolazione ISTAT."""
import csv
import io
import json
import re
import unicodedata
import zipfile

from .regioni import SOGLIA_COSTA_KM, Regione

# Popolazione residente per età al 1° gennaio (stima ISTAT); la riga con età "999" è il totale.
POPOLAZIONE_URL = "https://demo.istat.it/data/posas/POSAS_{anno}_it_Comuni.zip"
COMUNI_URL = "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_municipalities.geojson"
ETA_TOTALE = "999"
MARGINE_GRADI = 0.02  # ~2 km: comuni candidati per una stazione appena fuori dai confini


def carica_popolazione(percorso_zip):
    """{codice ISTAT comune (6 cifre): (nome, abitanti)}.

    Il CSV ha una riga di titolo, una di intestazione e colonne
    "Codice comune";"Comune";"Età";"Totale maschi";"Totale femmine";"Totale".
    Alcuni caratteri accentati sono già rovinati nel file: il nome serve solo come ripiego
    per abbinare i comuni sardi (vedi abbina_popolazione).
    """
    with zipfile.ZipFile(percorso_zip) as archivio:
        testo = archivio.read(archivio.namelist()[0]).decode("utf-8", "replace")
    abitanti = {}
    for riga in csv.reader(io.StringIO(testo), delimiter=";"):
        if len(riga) >= 6 and riga[2].strip() == ETA_TOTALE:
            abitanti[riga[0]] = (riga[1], int(riga[5]))
    return abitanti


def _chiave_nome(nome):
    """'Sant'Antioco' -> 'santantioco': solo lettere a-z senza accenti (nel CSV ISTAT le
    accentate sono rovinate, quindi un nome con accenti può non abbinarsi)."""
    senza_accenti = unicodedata.normalize("NFD", nome).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", senza_accenti.lower())


def abbina_popolazione(comuni, popolazione):
    """{codice del comune nei confini: abitanti}.

    Di norma i codici coincidono. Nel 2026 la Sardegna ha cambiato province e codici
    (es. Alghero 112001 nei confini, 090003 nella popolazione): i comuni rimasti
    senza codice corrispondente si abbinano per nome, solo tra loro (niente omonimi
    di altre regioni). Restituisce anche i nomi dei comuni rimasti senza abitanti.
    """
    abbinati = {c.codice: popolazione[c.codice][1] for c in comuni if c.codice in popolazione}
    codici = {c.codice for c in comuni}
    spaiati = {_chiave_nome(nome): n for codice, (nome, n) in popolazione.items() if codice not in codici}
    senza = []
    for c in comuni:
        if c.codice not in abbinati:
            n = spaiati.get(_chiave_nome(c.nome))
            if n is None:
                senza.append(c.nome)
            else:
                abbinati[c.codice] = n
    return abbinati, senza


def carica_comuni(percorso_geojson):
    dati = json.loads(percorso_geojson.read_text(encoding="utf-8"))
    comuni = []
    for f in dati["features"]:
        g = f["geometry"]
        poligoni = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        comuni.append(Regione(f["properties"]["name"], poligoni, f["properties"]["com_istat_code"]))
    return comuni


def comune_di(lat, lon, comuni):
    """Il comune che contiene il punto; se il punto cade appena fuori (costa, confini
    semplificati) il più vicino entro SOGLIA_COSTA_KM; altrimenti None."""
    vicini = []
    for c in comuni:
        if (c.lat_min - MARGINE_GRADI <= lat <= c.lat_max + MARGINE_GRADI
                and c.lon_min - MARGINE_GRADI <= lon <= c.lon_max + MARGINE_GRADI):
            if c.contiene(lat, lon):
                return c
            vicini.append(c)
    if not vicini:
        return None
    distanza, indice = min((c.distanza_km(lat, lon), i) for i, c in enumerate(vicini))
    return vicini[indice] if distanza <= SOGLIA_COSTA_KM else None
