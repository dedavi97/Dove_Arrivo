import datetime
import json
import subprocess
import zipfile

import pytest

from scanner import costruisci, gtfs, pubblica, regioni, rete
from scanner.gtfs import Corsa, Stazione

# --- orario GTFS finto -------------------------------------------------------

TABELLE = {
    "feed_info.txt": "feed_start_date,feed_end_date\n20261024,20271211\n",
    "routes.txt": "route_id,route_short_name\nr1,0083_REG\nr2,0083_FR\nr3,0083_BUS\n",
    "calendar.txt": (
        "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        "feriale,1,1,1,1,1,0,0,20261024,20271211\n"
        "festivo,0,0,0,0,0,1,1,20261024,20271211\n"
        "soppresso,1,1,1,1,1,0,0,20261024,20271211\n"
    ),
    "calendar_dates.txt": (
        "service_id,date,exception_type\n"
        "soppresso,20261104,2\n"
        "festivo,20261104,1\n"
    ),
    "trips.txt": (
        "route_id,service_id,trip_id,trip_short_name\n"
        "r1,feriale,t1,100\n"
        "r1,festivo,t2,200\n"
        "r1,soppresso,t3,300\n"
        "r2,feriale,t4,9000\n"
        "r3,feriale,t5,BUS1\n"
        "r1,feriale,t6,400\n"
    ),
    "stops.txt": (
        "stop_id,stop_code,stop_name,stop_lat,stop_lon,location_type,parent_station\n"
        "SPA,830000001,STAZIONE A,45.0,7.5,1,\n"
        "SSA,830000001,STAZIONE A,45.0,7.5,0,SPA\n"
        "SPB,830000002,STAZIONE B,45.1,7.6,1,\n"
        "SSB,830000002,STAZIONE B,45.1,7.6,0,SPB\n"
        "SPC,830000003,STAZIONE C,45.2,7.7,1,\n"
        "SSC,830000003,STAZIONE C,45.2,7.7,0,SPC\n"
    ),
    "stop_times.txt": (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "t1,23:50:00,23:50:00,SSA,1\n"
        "t1,24:05:00,24:06:00,SSB,2\n"
        "t1,24:20:00,24:20:00,SSC,3\n"
        "t2,10:00:00,10:00:00,SSA,1\n"
        "t2,10:30:00,10:30:00,SSB,2\n"
        "t3,10:00:00,10:00:00,SSA,1\n"
        "t3,10:30:00,10:30:00,SSB,2\n"
        "t4,10:00:00,10:00:00,SSA,1\n"
        "t4,10:10:00,10:10:00,SSC,2\n"
        "t5,10:00:00,10:00:00,SSA,1\n"
        "t5,10:10:00,10:10:00,SSB,2\n"
        "t6,10:00:00,10:00:00,SSA,1\n"
        "t6,09:50:00,09:50:00,SSB,2\n"
    ),
}


@pytest.fixture
def archivio(tmp_path):
    percorso = tmp_path / "gtfs.zip"
    with zipfile.ZipFile(percorso, "w") as z:
        for nome, testo in TABELLE.items():
            z.writestr(nome, testo)
    return gtfs.apri(percorso)


MERCOLEDI = datetime.date(2026, 11, 4)


def test_validita(archivio):
    assert gtfs.validita(archivio) == (datetime.date(2026, 10, 24), datetime.date(2027, 12, 11))


def test_servizi_attivi_con_eccezioni(archivio):
    assert gtfs.servizi_attivi(archivio, [MERCOLEDI]) == {"feriale", "festivo"}


def test_servizi_attivi_unione_di_piu_giorni(archivio):
    # il 04/11 "soppresso" non circola, l'11/11 sì: l'unione lo include
    assert gtfs.servizi_attivi(archivio, [MERCOLEDI, datetime.date(2026, 11, 11)]) == {"feriale", "festivo", "soppresso"}


def test_leggi_corse(archivio):
    corse, stazioni, avvisi = gtfs.leggi_corse(archivio, [MERCOLEDI], {"REG"})
    per_numero = {c.numero: c for c in corse}
    assert set(per_numero) == {"100", "200"}  # 300 soppresso, 9000 Freccia, BUS1 autobus, 400 scartato
    # dopo mezzanotte (24:xx) e con l'arrivo come riferimento
    assert per_numero["100"].fermate == [("830000001", 0), ("830000002", 15), ("830000003", 30)]
    assert stazioni["830000002"].nome == "STAZIONE B"
    assert len(avvisi) == 1 and "400" in avvisi[0]


def test_avanzamento_arriva_al_cento(archivio):
    valori = []
    gtfs.leggi_corse(archivio, [MERCOLEDI], {"REG"}, valori.append)
    assert valori and valori[-1] == pytest.approx(1.0)


def _d(testo):
    return datetime.date.fromisoformat(testo)


@pytest.mark.parametrize("oggi, attesi", [
    # almeno una settimana dopo, poi ogni 3 settimane
    ("2026-10-26", ["2026-11-04", "2026-11-25", "2026-12-16", "2027-01-13"]),  # salta le feste natalizie
    ("2027-11-14", ["2027-11-24", "2027-12-15", "2028-01-12", "2028-02-02"]),  # salta l'8/12 (mercoledì festivo)
])
def test_scegli_giorni_tipo(oggi, attesi):
    giorni = gtfs.scegli_giorni_tipo(_d(oggi), _d("2026-10-24"), _d("2028-06-30"))
    assert giorni == [_d(g) for g in attesi]


def test_scegli_giorni_tipo_a_fine_validita():
    assert gtfs.scegli_giorni_tipo(_d("2026-10-26"), _d("2026-10-24"), _d("2026-11-30")) == [_d("2026-11-04"), _d("2026-11-25")]


def test_scegli_giorni_tipo_fuori_validita():
    with pytest.raises(ValueError):
        gtfs.scegli_giorni_tipo(_d("2026-10-26"), _d("2026-10-01"), _d("2026-10-30"))


# --- nomi e riduzione corse ---------------------------------------------------

@pytest.mark.parametrize("grezzo, bello", [
    ("TORINO PORTA NUOVA", "Torino Porta Nuova"),
    ("REGGIO DI CALABRIA S.CATERINA", "Reggio di Calabria S.Caterina"),
    ("CASTELLO D'ANNONE", "Castello d'Annone"),
    ("VERBANIA-PALLANZA", "Verbania-Pallanza"),
    ("BOLOGNA C.LE", "Bologna Centrale"),
    ("DI QUALCOSA", "Di Qualcosa"),
    ("Torino Aeroporto di Caselle", "Torino Aeroporto di Caselle"),
])
def test_bel_nome(grezzo, bello):
    assert costruisci.bel_nome(grezzo) == bello


def test_tieni_piu_veloci():
    lenta = Corsa("10", "REG", [("A", 0), ("B", 40)])
    veloce = Corsa("12", "REG", [("A", 0), ("B", 30)])
    pari = Corsa("8", "REG", [("A", 0), ("B", 30)])
    altra = Corsa("20", "RV", [("A", 0), ("C", 50)])
    tenute = costruisci.tieni_piu_veloci([lenta, veloce, pari, altra])
    assert sorted(c.numero for c in tenute) == ["20", "8"]


def test_costruisci_rete_italia_esclude_solo_estero():
    stazioni = {i: Stazione(i, n, 45.0, 7.0) for i, n in [("1", "A"), ("2", "B"), ("3", "C"), ("4", "D")]}
    regione = {"1": "Piemonte", "2": "Sicilia", "3": "Estero", "4": "Estero"}
    corse = [
        Corsa("1", "REG", [("1", 0), ("2", 10)]),
        Corsa("2", "REG", [("2", 0), ("3", 10)]),
        Corsa("3", "REG", [("3", 0), ("4", 10)]),
    ]
    r = costruisci.costruisci_rete(
        corse, stazioni, lambda s: regione[s.id], costruisci.ITALIA,
        datetime.date(2026, 10, 26), [MERCOLEDI], "test",
    )
    assert [t["numero"] for t in r["treni"]] == ["1", "2"]


def test_costruisci_rete_perimetro():
    stazioni = {
        "1": Stazione("1", "TORINO", 45.0, 7.6),
        "2": Stazione("2", "MILANO", 45.4, 9.1),
        "3": Stazione("3", "BERGAMO", 45.7, 9.6),
    }
    regione = {"1": "Piemonte", "2": "Lombardia", "3": "Lombardia"}
    corse = [
        Corsa("1", "RV", [("1", 0), ("2", 100)]),
        Corsa("2", "REG", [("2", 0), ("3", 50)]),
    ]
    r = costruisci.costruisci_rete(
        corse, stazioni, lambda s: regione[s.id], "Piemonte",
        datetime.date(2026, 10, 26), [MERCOLEDI], "test",
    )
    assert [t["numero"] for t in r["treni"]] == ["1"]
    assert [s["nome"] for s in r["stazioni"]] == ["Milano", "Torino"]
    assert r["meta"]["conteggi"] == {"stazioni": 2, "treni": 1}
    assert r["treni"][0]["fermate"][1] == {"stazione": "2", "minuti_dalla_partenza": 100}


# --- regioni -----------------------------------------------------------------

def _quadrato(x0, y0, lato):
    return [(x0, y0), (x0 + lato, y0), (x0 + lato, y0 + lato), (x0, y0 + lato), (x0, y0)]


@pytest.fixture
def elenco_regioni():
    # "Alfa" è un quadrato 0..1 con un buco 0.4..0.6; "Beta" sta a destra.
    alfa = regioni.Regione("Alfa", [[_quadrato(0, 0, 1), _quadrato(0.4, 0.4, 0.2)]])
    beta = regioni.Regione("Beta/Bêta", [[_quadrato(1, 0, 1)]])
    return [alfa, beta]


def test_regione_dentro_e_buco(elenco_regioni):
    assert regioni.regione_di(0.2, 0.2, "830000001", elenco_regioni) == "Alfa"
    assert regioni.regione_di(0.2, 1.5, "830000001", elenco_regioni) == "Beta"
    assert regioni.regione_di(0.5, 0.5, "830000001", elenco_regioni) == "Estero"  # nel buco, a ~11 km dal bordo


def test_regione_costa_ed_estero(elenco_regioni):
    assert regioni.regione_di(-0.005, 0.5, "830000001", elenco_regioni) == "Alfa"     # ~0,55 km fuori: costa
    assert regioni.regione_di(-0.05, 0.5, "830000001", elenco_regioni) == "Estero"    # ~5,5 km fuori
    assert regioni.regione_di(0.2, 0.2, "850000001", elenco_regioni) == "Estero"      # codice straniero


def test_carica_regioni(tmp_path):
    geo = {"type": "FeatureCollection", "features": [
        {"properties": {"reg_name": "Uno"}, "geometry": {"type": "Polygon", "coordinates": [_quadrato(0, 0, 1)]}},
        {"properties": {"reg_name": "Due"}, "geometry": {"type": "MultiPolygon", "coordinates": [[_quadrato(2, 0, 1)], [_quadrato(4, 0, 1)]]}},
    ]}
    percorso = tmp_path / "r.geojson"
    percorso.write_text(json.dumps(geo), encoding="utf-8")
    caricate = regioni.carica_regioni(percorso)
    assert regioni.regione_di(0.5, 4.5, "83", caricate) == "Due"


# --- rete.json -----------------------------------------------------------------

def _rete(treni=None):
    return {
        "meta": {"tipo": rete.TIPO, "formato_versione": rete.FORMATO_VERSIONE, "data_aggiornamento": "2026-10-26"},
        "stazioni": [
            {"id": "1", "nome": "Àlfa", "lat": 45.0, "lon": 7.0, "regione": "Piemonte"},
            {"id": "2", "nome": "Beta", "lat": 45.1, "lon": 7.1, "regione": "Piemonte"},
        ],
        "treni": treni if treni is not None else [
            {"numero": "1", "categoria": "REG", "fermate": [
                {"stazione": "1", "minuti_dalla_partenza": 0}, {"stazione": "2", "minuti_dalla_partenza": 10}]},
        ],
    }


def test_scrivi_e_leggi(tmp_path):
    percorso = tmp_path / "data" / "rete.json"
    rete.scrivi_rete(percorso, _rete())
    assert rete.leggi_rete(percorso) == _rete()
    assert "Àlfa" in percorso.read_text(encoding="utf-8")


def test_leggi_file_assente(tmp_path):
    assert rete.leggi_rete(tmp_path / "manca.json") is None


@pytest.mark.parametrize("contenuto, frammento", [
    ("non json", "non è un file JSON"),
    ('{"meta": {"tipo": "Altro"}}', "non è un file dati"),
    ('{"meta": {"tipo": "Dove_Arrivo_Rete", "formato_versione": 2}}', "formato versione 2"),
])
def test_formato_sconosciuto(tmp_path, contenuto, frammento):
    percorso = tmp_path / "rete.json"
    percorso.write_text(contenuto, encoding="utf-8")
    with pytest.raises(rete.ErroreFormato, match=frammento):
        rete.leggi_rete(percorso)


def test_differenze():
    vecchia = _rete()
    nuova = _rete(treni=[])
    nuova["stazioni"].append({"id": "3", "nome": "Gamma", "lat": 0, "lon": 0, "regione": "Piemonte"})
    d = rete.differenze(vecchia, nuova)
    assert d["stazioni_nuove"] == ["Gamma"]
    assert d["collegamenti_spariti"] == [("Àlfa", "Beta")]
    assert (d["treni_prima"], d["treni_ora"]) == (1, 0)
    assert rete.differenze(None, nuova) is None


def test_contenuto_uguale_ignora_data():
    altra = _rete()
    altra["meta"]["data_aggiornamento"] = "2030-01-01"
    assert rete.contenuto_uguale(_rete(), altra)
    assert not rete.contenuto_uguale(None, altra)
    assert not rete.contenuto_uguale(_rete(), _rete(treni=[]))


# --- pubblicazione ---------------------------------------------------------------

def test_messaggio_commit():
    assert pubblica.messaggio_commit(datetime.date(2026, 3, 5)) == "data: aggiornamento rete 05/03/2026"


def test_pubblica_senza_github(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    file_dati = tmp_path / "docs" / "data" / "rete.json"
    rete.scrivi_rete(file_dati, _rete())
    riuscito, spiegazione = pubblica.pubblica(tmp_path, file_dati, datetime.date(2026, 10, 26))
    assert not riuscito and "origin" in spiegazione


def test_pubblica_solo_il_file_dati(tmp_path):
    remoto = tmp_path / "remoto.git"
    locale = tmp_path / "locale"
    subprocess.run(["git", "init", "-q", "--bare", str(remoto)], check=True)
    subprocess.run(["git", "init", "-q", "-b", "main", str(locale)], check=True)
    git = lambda *a: subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *a], cwd=locale, check=True, capture_output=True)
    (locale / "altro.txt").write_text("x")
    git("add", "altro.txt")
    git("commit", "-q", "-m", "inizio")
    git("remote", "add", "origin", str(remoto))
    git("push", "-q", "-u", "origin", "main")
    (locale / "altro.txt").write_text("modificato, non va pubblicato")
    file_dati = locale / "docs" / "data" / "rete.json"
    rete.scrivi_rete(file_dati, _rete())

    subprocess.run(["git", "config", "user.name", "t"], cwd=locale, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=locale, check=True)
    riuscito, spiegazione = pubblica.pubblica(locale, file_dati, datetime.date(2026, 10, 26))
    assert riuscito, spiegazione
    ultimo = subprocess.run(["git", "log", "-1", "--name-only", "--format=%s", "origin/main"], cwd=locale, capture_output=True, text=True).stdout.split()
    assert " ".join(ultimo[:4]) == "data: aggiornamento rete 26/10/2026"
    assert ultimo[4:] == ["docs/data/rete.json"]


# --- comuni e abitanti -------------------------------------------------------

from scanner import comuni


def _zip_popolazione(tmp_path, righe):
    percorso = tmp_path / "pop.zip"
    testo = '﻿"Popolazione residente per età e sesso al 1° gennaio 2026 (stima)"\n'
    testo += '"Codice comune";"Comune";"Et�";"Totale maschi";"Totale femmine";"Totale"\n'
    testo += "\n".join(righe) + "\n\n"
    with zipfile.ZipFile(percorso, "w") as z:
        z.writestr("POSAS.csv", testo.encode("utf-8"))
    return percorso


def test_carica_popolazione_usa_la_riga_totale(tmp_path):
    percorso = _zip_popolazione(tmp_path, [
        '"001272";"Torino";0;10;10;20',
        '"001272";"Torino";999;400;455;855',
        '"090003";"Alghero";999;20;20;40',
    ])
    assert comuni.carica_popolazione(percorso) == {"001272": ("Torino", 855), "090003": ("Alghero", 40)}


def test_abbina_popolazione_per_codice_e_per_nome():
    elenco = [
        regioni.Regione("Torino", [[_quadrato(0, 0, 1)]], "001272"),
        regioni.Regione("Alghero", [[_quadrato(2, 0, 1)]], "112001"),     # codice sardo nuovo
        regioni.Regione("Sconosciuto", [[_quadrato(4, 0, 1)]], "999999"),
    ]
    popolazione = {"001272": ("Torino", 855), "090003": ("Alghero", 40), "001001": ("Altro", 5)}
    abbinati, senza = comuni.abbina_popolazione(elenco, popolazione)
    assert abbinati == {"001272": 855, "112001": 40}
    assert senza == ["Sconosciuto"]


def test_abbina_per_nome_non_confonde_omonimi_gia_abbinati():
    # "Samone" esiste in due regioni: quello con codice giusto non deve finire nei ripieghi
    elenco = [regioni.Regione("Samone", [[_quadrato(0, 0, 1)]], "001234"), regioni.Regione("Samone", [[_quadrato(2, 0, 1)]], "022999")]
    popolazione = {"001234": ("Samone", 1600), "022165": ("Samone", 550)}
    abbinati, _ = comuni.abbina_popolazione(elenco, popolazione)
    assert abbinati == {"001234": 1600, "022999": 550}


def test_comune_di_dentro_costa_e_lontano():
    elenco = [regioni.Regione("Alfa", [[_quadrato(0, 0, 1)]], "1"), regioni.Regione("Beta", [[_quadrato(1, 0, 1)]], "2")]
    assert comuni.comune_di(0.5, 1.5, elenco).nome == "Beta"
    assert comuni.comune_di(-0.005, 0.5, elenco).nome == "Alfa"   # ~0,55 km fuori: costa
    assert comuni.comune_di(-0.05, 0.5, elenco) is None            # ~5,5 km fuori
    assert comuni.comune_di(30, 30, elenco) is None


def test_costruisci_rete_aggiunge_comune_e_abitanti():
    stazioni = {"1": Stazione("1", "TORINO", 45.0, 7.6), "2": Stazione("2", "MODANE", 45.2, 6.7)}
    regione = {"1": "Piemonte", "2": "Estero"}
    r = costruisci.costruisci_rete(
        [Corsa("1", "REG", [("1", 0), ("2", 60)])], stazioni, lambda s: regione[s.id], "Piemonte",
        datetime.date(2026, 10, 26), [MERCOLEDI], "test", lambda s: ("Torino", 855654),
    )
    torino, modane = sorted(r["stazioni"], key=lambda s: s["id"])
    assert (torino["comune"], torino["abitanti"]) == ("Torino", 855654)
    assert "abitanti" not in modane   # all'estero non si cerca il comune


# --- orari delle corse (frequenze, 0.6.0) -----------------------------------------

def test_leggi_corse_tiene_giorni_inizio_e_partenze(archivio):
    undici_nov = datetime.date(2026, 11, 11)
    corse, _, _ = gtfs.leggi_corse(archivio, [MERCOLEDI, undici_nov], {"REG"})
    per_numero = {c.numero: c for c in corse}
    # "feriale" circola entrambi i giorni, "festivo" solo il 04/11 (eccezione), "soppresso" solo l'11/11
    assert per_numero["100"].giorni == 0b11
    assert per_numero["200"].giorni == 0b01
    assert per_numero["300"].giorni == 0b10
    assert per_numero["100"].inizio == 23 * 60 + 50
    assert per_numero["100"].partenze == [0, 16, 30]   # riparte da B alle 24:06


def test_orari_gruppo_profili_distinti_e_giorni_uniti():
    def corsa(inizio, partenze, giorni):
        return Corsa("1", "REG", [("A", 0), ("B", partenze[-1])], giorni=giorni, inizio=inizio, partenze=partenze)

    gruppo = [corsa(600, [0, 30], 0b01), corsa(600, [0, 30], 0b10), corsa(540, [0, 35], 0b11), corsa(660, [0, 30], 0b01)]
    profili, righe = costruisci.orari_gruppo(gruppo)
    assert profili == [[0, 30], [0, 35]]
    assert righe == [[540, 1, 0b11], [600, 0, 0b11], [660, 0, 0b01]]


def test_costruisci_rete_scrive_profili_e_corse():
    stazioni = {"1": Stazione("1", "A", 45.0, 7.0), "2": Stazione("2", "B", 45.1, 7.1)}
    corse = [
        Corsa("10", "REG", [("1", 0), ("2", 30)], giorni=1, inizio=600, partenze=[0, 30]),
        Corsa("12", "REG", [("1", 0), ("2", 25)], giorni=1, inizio=700, partenze=[0, 25]),
    ]
    r = costruisci.costruisci_rete(corse, stazioni, lambda s: "Piemonte", "Piemonte",
                                   datetime.date(2026, 10, 27), [MERCOLEDI], "test")
    (treno,) = r["treni"]
    assert treno["numero"] == "12"                                   # il più veloce per il calcolo
    assert treno["corse"] == [[600, 0, 1], [700, 1, 1]]              # ma tutte le corse negli orari


# --- tracciati (0.8.0) ------------------------------------------------------------

def test_togli_punte():
    # dritto verso est con una punta a sud a metà strada
    percorso = [(45.0, 7.0), (45.0, 7.1), (44.8, 7.15), (45.0, 7.2), (45.0, 7.3)]
    assert costruisci.togli_punte(percorso) == [(45.0, 7.0), (45.0, 7.1), (45.0, 7.2), (45.0, 7.3)]
    curva = [(45.0, 7.0), (45.1, 7.1), (45.0, 7.2)]   # curva vera, non una punta
    assert costruisci.togli_punte(curva) == curva


def test_punti_intermedi_tratto_dubbio_resta_dritto():
    fermate = [(45.0, 7.0), (45.0, 7.2), (45.0, 7.4)]
    punti = [(45.0, 7.0), (45.01, 7.1), (45.0, 7.2), (46.0, 7.3), (45.0, 7.4)]   # secondo tratto: giro enorme
    assert costruisci.punti_intermedi(fermate, punti) == [[(45.01, 7.1)], []]


def test_costruisci_rete_tracciati():
    stazioni = {"1": Stazione("1", "A", 45.0, 7.0), "2": Stazione("2", "B", 45.0, 7.2)}
    corse = [Corsa("9", "REG", [("2", 0), ("1", 20)], giorni=1, inizio=600, partenze=[0, 20],
                   operatore="Trenitalia", forma="f")]
    forme = {("Trenitalia", "f"): [(45.0, 7.2), (45.02, 7.15), (45.01, 7.05), (45.0, 7.0)]}
    r = costruisci.costruisci_rete(corse, stazioni, lambda s: "Piemonte", "Piemonte",
                                   datetime.date(2026, 10, 27), [MERCOLEDI], "test", forme=forme)
    # salvato da "1" verso "2", quindi punti al contrario rispetto al treno
    assert r["tracciati"] == [["1", "2", [[45.01, 7.05], [45.02, 7.15]]]]


def test_scrivi_e_leggi_con_tracciati(tmp_path):
    dati = _rete()
    dati["tracciati"] = [["1", "2", [[45.05, 7.05]]]]
    percorso = tmp_path / "rete.json"
    rete.scrivi_rete(percorso, dati)
    assert rete.leggi_rete(percorso) == dati
    assert not rete.contenuto_uguale(_rete(), dati)
