"""Lettura dell'orario Trenitalia in formato GTFS (file zip)."""
import csv
import datetime
import io
import zipfile
from dataclasses import dataclass, field

GIORNI = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")

# Festivi fissi italiani (mese, giorno): il giorno tipo non deve cadere qui.
FESTIVI = {(1, 1), (1, 6), (4, 25), (5, 1), (6, 2), (8, 15), (11, 1), (12, 8), (12, 25), (12, 26)}


@dataclass
class Stazione:
    id: str
    nome: str
    lat: float
    lon: float


@dataclass
class Corsa:
    numero: str
    categoria: str
    fermate: list = field(default_factory=list)  # [(id stazione, minuti dalla partenza)] - arrivi, per il calcolo
    giorni: int = 0  # bit k acceso = circola nel k-esimo giorno tipo
    inizio: int = 0  # minuti dalla mezzanotte della partenza dalla prima fermata (può superare 1440)
    partenze: list = field(default_factory=list)  # minuti dopo `inizio` della partenza da ogni fermata


class _ContaByte(io.RawIOBase):
    """Avvolge lo stream del file nello zip per sapere quanto se n'è letto."""

    def __init__(self, stream, totale, avanzamento):
        self.stream, self.totale, self.avanzamento, self.letti = stream, totale, avanzamento, 0

    def readable(self):
        return True

    def readinto(self, buffer):
        dati = self.stream.read(len(buffer))
        buffer[:len(dati)] = dati
        self.letti += len(dati)
        if self.avanzamento and self.totale:
            self.avanzamento(self.letti / self.totale)
        return len(dati)


def _righe(archivio, nome, avanzamento=None):
    info = archivio.getinfo(nome)
    with archivio.open(info) as grezzo:
        stream = io.BufferedReader(_ContaByte(grezzo, info.file_size, avanzamento), 1024 * 1024)
        yield from csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"))


def _minuti(orario):
    ore, minuti, _ = orario.split(":")  # le ore possono superare 24 (corse dopo mezzanotte)
    return int(ore) * 60 + int(minuti)


def _data(testo):
    return datetime.date(int(testo[:4]), int(testo[4:6]), int(testo[6:]))


def validita(archivio):
    info = next(_righe(archivio, "feed_info.txt"))
    return _data(info["feed_start_date"]), _data(info["feed_end_date"])


def _primo_mercoledi_feriale(da, fine):
    """Primo mercoledì da `da` in poi, entro `fine`, non festivo e fuori dalle feste natalizie."""
    giorno = da
    while giorno <= fine:
        natale = (giorno.month == 12 and giorno.day >= 20) or (giorno.month == 1 and giorno.day <= 7)
        if giorno.weekday() == 2 and (giorno.month, giorno.day) not in FESTIVI and not natale:
            return giorno
        giorno += datetime.timedelta(days=1)
    return None


def scegli_giorni_tipo(oggi, inizio, fine, quanti=4, settimane_tra_giorni=3):
    """Alcuni mercoledì feriali distribuiti nel tempo, dal primo tra una settimana in poi.

    Un solo giorno può cadere durante lavori sulla linea (es. Torino-Asti il 04/11/2026
    servita solo da autobus): unendo più giorni l'interruzione non fa sparire la linea.
    """
    giorni = []
    da = max(oggi + datetime.timedelta(days=7), inizio)
    while len(giorni) < quanti:
        giorno = _primo_mercoledi_feriale(da, fine)
        if giorno is None:
            break
        giorni.append(giorno)
        da = giorno + datetime.timedelta(weeks=settimane_tra_giorni)
    if not giorni:
        raise ValueError(f"nessun mercoledì feriale valido tra {inizio} e {fine}")
    return giorni


def servizi_attivi(archivio, giorni):
    """Servizi attivi in almeno uno dei giorni."""
    return set().union(*servizi_per_giorno(archivio, giorni))


def servizi_per_giorno(archivio, giorni):
    """Per ogni giorno (stesso ordine), l'insieme dei servizi attivi."""
    testi = {g.strftime("%Y%m%d"): GIORNI[g.weekday()] for g in giorni}
    attivi = {testo: set() for testo in testi}
    for c in _righe(archivio, "calendar.txt"):
        for testo, colonna in testi.items():
            if c[colonna] == "1" and c["start_date"] <= testo <= c["end_date"]:
                attivi[testo].add(c["service_id"])
    for d in _righe(archivio, "calendar_dates.txt"):
        if d["date"] in attivi:
            if d["exception_type"] == "1":
                attivi[d["date"]].add(d["service_id"])
            else:
                attivi[d["date"]].discard(d["service_id"])
    return list(attivi.values())


def leggi_stazioni(archivio):
    """Stazioni (StopPlace) indicizzate per stop_id di ogni loro punto di fermata."""
    righe = list(_righe(archivio, "stops.txt"))
    per_id = {r["stop_id"]: r for r in righe}
    stazioni, da_fermata = {}, {}
    for r in righe:
        madre = per_id.get(r["parent_station"]) or r
        codice = madre["stop_code"]
        if codice not in stazioni:
            stazioni[codice] = Stazione(codice, madre["stop_name"].strip(), float(madre["stop_lat"]), float(madre["stop_lon"]))
        da_fermata[r["stop_id"]] = codice
    return stazioni, da_fermata


def leggi_corse(archivio, giorni, categorie, avanzamento=None):
    """Corse attive in almeno uno dei giorni, delle sole categorie volute. Restituisce (corse, stazioni, avvisi)."""
    categoria_di = {r["route_id"]: r["route_short_name"].split("_")[-1] for r in _righe(archivio, "routes.txt")}
    per_giorno = servizi_per_giorno(archivio, giorni)
    viaggi = {}
    for t in _righe(archivio, "trips.txt"):
        categoria = categoria_di.get(t["route_id"])
        maschera = sum(1 << k for k, attivi in enumerate(per_giorno) if t["service_id"] in attivi)
        if categoria in categorie and maschera:
            viaggi[t["trip_id"]] = Corsa(t["trip_short_name"], categoria, giorni=maschera)

    stazioni, da_fermata = leggi_stazioni(archivio)
    orari = {}
    for st in _righe(archivio, "stop_times.txt", avanzamento):
        if st["trip_id"] in viaggi:
            orari.setdefault(st["trip_id"], []).append(st)

    corse, avvisi = [], []
    for trip_id, righe in orari.items():
        corsa = viaggi[trip_id]
        righe.sort(key=lambda r: int(r["stop_sequence"]))
        partenza = _minuti(righe[0]["departure_time"] or righe[0]["arrival_time"])
        corsa.inizio = partenza
        precedente = 0
        for i, r in enumerate(righe):
            # Si usa l'arrivo in ogni fermata (la partenza per la prima): A→B = arrivo B − arrivo A.
            orario = r["departure_time"] if i == 0 else (r["arrival_time"] or r["departure_time"])
            minuti = _minuti(orario) - partenza
            if minuti < precedente:
                avvisi.append(f"treno {corsa.numero}: orari che tornano indietro a {stazioni[da_fermata[r['stop_id']]].nome}, scartato")
                break
            corsa.fermate.append((da_fermata[r["stop_id"]], minuti))
            corsa.partenze.append(_minuti(r["departure_time"] or r["arrival_time"]) - partenza)
            precedente = minuti
        else:
            if len(corsa.fermate) >= 2:
                corse.append(corsa)
    return corse, stazioni, avvisi


def apri(percorso):
    return zipfile.ZipFile(percorso)
