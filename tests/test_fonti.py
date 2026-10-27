"""Più fonti di orari (0.7.0): abbinamento delle stazioni, fonte scaduta, fonte non scaricabile."""
import datetime
import zipfile

import pytest

from scanner import abbina, fonti, gtfs, regioni, scarica
from scanner.gtfs import Corsa, Stazione


def _st(id_, nome, lat, lon, uic=None):
    return Stazione(id_, nome, lat, lon, uic)


# --- abbinamento ------------------------------------------------------------------

BASE = {
    "830000248": _st("830000248", "NOVARA", 45.4510, 8.6240, "830000248"),
    "830005301": _st("830005301", "BUTTAPIETRA", 45.3380, 10.9880, "830005301"),
    "830001037": _st("830001037", "Rho Fiera Milano", 45.5200, 9.0880, "830001037"),
    "830004513": _st("830004513", "Andora", 43.9520, 8.1393, "830004513"),
}


@pytest.mark.parametrize("a, b, uguale", [
    ("Novara Nord", "NOVARA", True),
    ("Rovato Fn", "ROVATO", True),
    ("Milano Porta Garibaldi Passante", "MILANO PORTA GARIBALDI", True),
    ("Milano Repubblica", "MILANO CENTRALE", False),
    ("Rho", "Rho Fiera Milano", True),
    ("Novara", "Novate Milanese", False),
])
def test_stesso_nome(a, b, uguale):
    assert abbina.stesso_nome(a, b) is uguale


def test_abbina_codice_solo_se_vicino_poi_nome_poi_tabella():
    fonte = {
        "S00248": _st("S00248", "Novara FS", 45.4512, 8.6242),          # codice giusto e vicino
        "S05301": _st("S05301", "Lugano Paradiso", 45.9890, 8.9450),   # codice uguale a Buttapietra, 174 km
        "S00023": _st("S00023", "Novara Nord", 45.4519, 8.6250),       # nome + 106 m
        "S04525": _st("S04525", "Andora", 43.9609, 8.1394),            # ~1 km: solo da tabella
        "S01037": _st("S01037", "Rho", 45.5280, 9.0420),               # nome simile ma a 3,5 km: nuova
    }
    abbinamenti, conteggi = abbina.abbina(
        fonte, BASE, "Trenord", fonti.codice_trenord, {("Trenord", "S04525"): "830004513"},
    )
    assert abbinamenti == {
        "S00248": "830000248",
        "S05301": None,
        "S00023": "830000248",
        "S04525": "830004513",
        "S01037": None,
    }
    assert conteggi == {"codice": 1, "nome e distanza": 1, "tabella manuale": 1, "nuova": 2}


def test_tabella_manuale_del_repo_si_legge():
    manuali = abbina.carica_manuali()
    assert manuali[("Trenord", "S04525")] == "830004513"


def test_codice_trenord():
    assert fonti.codice_trenord("S00219") == "830000219"
    assert fonti.codice_trenord("XYZ") is None


@pytest.mark.parametrize("route, categoria", [
    ({"route_type": "2", "route_short_name": "RE_11"}, "RE11"),
    ({"route_type": "2", "route_short_name": "S5"}, "S5"),
    ({"route_type": "2", "route_short_name": "Trenord (linea non specificata)"}, "R"),
    ({"route_type": "3", "route_short_name": "R23"}, None),   # autobus
])
def test_categoria_trenord(route, categoria):
    assert fonti.categoria_trenord(route) == categoria


def test_regione_senza_codice_uic_non_usa_la_tolleranza_della_costa():
    quadrato = [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]
    elenco = [regioni.Regione("Alfa", [[quadrato]])]
    assert regioni.regione_di(-0.005, 0.5, "830000001", elenco) == "Alfa"   # costa, con codice italiano
    assert regioni.regione_di(-0.005, 0.5, None, elenco) == "Estero"        # es. Chiasso, senza codice


def test_unisci_rinomina_le_stazioni():
    principale = fonti.Letta(fonti.TRENITALIA, [Corsa("1", "REG", [("830000248", 0), ("830001037", 30)], operatore="Trenitalia")], dict(BASE))
    trenord = fonti.Letta(
        fonti.TRENORD,
        [Corsa("2", "S5", [("S00023", 0), ("S01037", 20)], operatore="Trenord")],
        {"S00023": _st("S00023", "Novara Nord", 45.4519, 8.6250), "S01037": _st("S01037", "Rho", 45.5280, 9.0420)},
    )
    corse, stazioni = fonti.unisci([principale, trenord], [], manuali={})
    assert corse[1].fermate == [("830000248", 0), ("TN-S01037", 20)]
    assert stazioni["TN-S01037"].nome == "Rho" and stazioni["TN-S01037"].uic is None
    assert trenord.info["nuove"] == ["Rho"]


# --- orario GTFS senza calendar.txt e scadenza --------------------------------------

def _gtfs_trenord(tmp_path, date):
    percorso = tmp_path / "trenord.zip"
    with zipfile.ZipFile(percorso, "w") as z:
        z.writestr("feed_info.txt", "feed_publisher_name,feed_publisher_url,feed_lang\nTrenord,https://trenord.it/,it-IT\n")
        z.writestr("routes.txt", "route_id,agency_id,route_short_name,route_long_name,route_type\nS5,1,S5,Varese-Treviglio,2\nTN_Bus,1,TN Bus,Bus,3\n")
        z.writestr("trips.txt", "trip_id,route_id,trip_short_name,service_id\nt1,S5,S5 - 24512,srv\nb1,TN_Bus,1001A,srv\n")
        z.writestr("stops.txt", "stop_id,stop_name,stop_lat,stop_lon\nS01000,Varese,45.81,8.83\nS01001,Gallarate,45.66,8.79\n")
        z.writestr("stop_times.txt", "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
                   "t1,08:00:00,08:00:00,S01000,1\nt1,08:20:00,08:21:00,S01001,2\n"
                   "b1,09:00:00,09:00:00,S01000,1\nb1,09:30:00,09:30:00,S01001,2\n")
        z.writestr("calendar_dates.txt", "service_id,date,exception_type\n" + "".join(f"srv,{d},1\n" for d in date))
    return percorso


def test_validita_dai_calendar_dates(tmp_path):
    percorso = _gtfs_trenord(tmp_path, ["20261104", "20261125", "20261209"])
    assert gtfs.validita(gtfs.apri(percorso)) == (datetime.date(2026, 11, 4), datetime.date(2026, 12, 9))


def test_leggi_fonte_valida_numero_e_autobus_escluso(tmp_path):
    percorso = _gtfs_trenord(tmp_path, ["20261104", "20261125"])
    avvisi = []
    letta = fonti.leggi(fonti.TRENORD, percorso, [datetime.date(2026, 11, 4), datetime.date(2026, 11, 25)],
                        datetime.date(2026, 10, 1), avvisi)   # scadenza oltre 30 giorni: nessun avviso
    assert [(c.numero, c.categoria, c.operatore, c.giorni) for c in letta.corse] == [("24512", "S5", "Trenord", 0b11)]
    assert letta.info["scaduta"] is False and not avvisi
    assert all(s.uic is None for s in letta.stazioni.values())


def test_leggi_fonte_scaduta_tiene_i_dati_vecchi_e_avvisa(tmp_path):
    percorso = _gtfs_trenord(tmp_path, ["20261104", "20261125", "20261209"])
    avvisi = []
    giorni_nuovi = [datetime.date(2027, 1, 13), datetime.date(2027, 2, 3)]
    letta = fonti.leggi(fonti.TRENORD, percorso, giorni_nuovi, datetime.date(2027, 1, 5), avvisi)
    assert letta.info["scaduta"] is True
    assert len(letta.corse) == 1, "i treni della fonte scaduta restano"
    assert any("SCADUTO" in a and "09/12/2026" in a for a in avvisi)


def test_leggi_fonte_in_scadenza_avvisa(tmp_path):
    percorso = _gtfs_trenord(tmp_path, ["20261104", "20261125", "20261209"])
    avvisi = []
    fonti.leggi(fonti.TRENORD, percorso, [datetime.date(2026, 11, 25)], datetime.date(2026, 11, 20), avvisi)
    assert any("scade il 09/12/2026" in a for a in avvisi)


def test_scegli_giorni_finali():
    giorni = gtfs.scegli_giorni_finali(datetime.date(2026, 7, 26), datetime.date(2026, 12, 12))
    # l'ultimo mercoledì prima del 12/12 è il 9/12, poi indietro di 3 settimane
    assert giorni == [datetime.date(2026, 10, 7), datetime.date(2026, 10, 28), datetime.date(2026, 11, 18), datetime.date(2026, 12, 9)]


# --- fonte non scaricabile ----------------------------------------------------------

def test_prepara_usa_la_copia_vecchia_se_il_download_fallisce(tmp_path, monkeypatch):
    monkeypatch.setattr(scarica, "CACHE", tmp_path)
    (tmp_path / "trenord.zip").write_bytes(b"vecchio")
    (tmp_path / "trenord.data").write_text("versione-1", encoding="utf-8")

    def versione(url):
        return '{"viewLastModified": 2}'

    def scarica_ko(*a, **k):
        raise ConnectionError("rete giù")
    monkeypatch.setattr(scarica, "scarica_testo", versione)
    monkeypatch.setattr(scarica, "scarica_file", scarica_ko)
    avvisi = []
    assert fonti.prepara(fonti.TRENORD, avvisi) == tmp_path / "trenord.zip"
    assert any("ATTENZIONE Trenord" in a and "copia già scaricata" in a for a in avvisi)


def test_prepara_fonte_mai_scaricata_e_non_disponibile(tmp_path, monkeypatch):
    monkeypatch.setattr(scarica, "CACHE", tmp_path)

    def ko(*a, **k):
        raise ConnectionError("rete giù")
    monkeypatch.setattr(scarica, "scarica_testo", ko)
    monkeypatch.setattr(scarica, "scarica_file", ko)
    avvisi = []
    assert fonti.prepara(fonti.TRENORD, avvisi) is None
    assert any("MANCANO" in a for a in avvisi)
    with pytest.raises(ConnectionError):
        fonti.prepara(fonti.TRENITALIA, [])   # la fonte principale è obbligatoria


def test_prepara_non_riscarica_se_la_versione_e_uguale(tmp_path, monkeypatch):
    monkeypatch.setattr(scarica, "CACHE", tmp_path)
    (tmp_path / "trenord.zip").write_bytes(b"x")
    (tmp_path / "trenord.data").write_text("7", encoding="utf-8")
    monkeypatch.setattr(scarica, "scarica_testo", lambda url: '{"viewLastModified": 7}')
    monkeypatch.setattr(scarica, "scarica_file", lambda *a, **k: pytest.fail("non doveva riscaricare"))
    assert fonti.prepara(fonti.TRENORD, []) == tmp_path / "trenord.zip"
