"""Scansione completa: python -m scanner [--solo-scansione]"""
import datetime
import sys
from pathlib import Path

from . import comuni, costruisci, gtfs, pubblica, regioni, rete, scarica

RADICE = Path(__file__).resolve().parent.parent
FILE_DATI = RADICE / "docs" / "data" / "rete.json"

PERIMETRO = costruisci.ITALIA  # oppure il nome di una regione, es. "Piemonte"
CATEGORIE_REGIONALI = {"REG", "RV", "SFM", "MET"}

GTFS_URL = "https://github.com/deryclem/trenitalia-gtfs/raw/main/gtfs-trenitalia.zip"
GTFS_DATA_URL = "https://raw.githubusercontent.com/deryclem/trenitalia-gtfs/main/.last_publication_timestamp"
REGIONI_URL = "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson"
FONTE = (
    "Orario: Trenitalia S.p.A. / CCISS MMTIS (NAP), conversione GTFS di Clément Desouche, CC-BY-4.0. "
    "Confini regionali e comunali: ISTAT via openpolis/geojson-italy, CC-BY-4.0. "
    "Abitanti: ISTAT, popolazione residente al 1° gennaio {anno}, CC-BY-4.0."
)
FASI = 6


def fase(numero, testo):
    print(f"\n[{numero}/{FASI}] {testo}")


def barra(frazione):
    piene = int(frazione * 30)
    print(f"\r    [{'#' * piene}{'.' * (30 - piene)}] {frazione:4.0%}", end="", flush=True)
    if frazione >= 1:
        print()


def prepara_orario(avvisi):
    fase(1, "Controllo se c'è un orario Trenitalia più recente")
    cache_zip = scarica.CACHE / "gtfs-trenitalia.zip"
    cache_data = scarica.CACHE / "gtfs-trenitalia.data"
    try:
        pubblicato = scarica.scarica_testo(GTFS_DATA_URL)
    except ConnectionError as errore:
        if not cache_zip.exists():
            raise
        avvisi.append(f"impossibile controllare gli aggiornamenti, uso l'orario già scaricato ({errore})")
        pubblicato = None
    print(f"    orario pubblicato il: {pubblicato or 'sconosciuto'}")

    fase(2, "Download dell'orario (circa 6,5 MB)")
    gia_scaricato = cache_data.read_text(encoding="utf-8").strip() if cache_data.exists() else None
    if cache_zip.exists() and (pubblicato is None or pubblicato == gia_scaricato):
        print("    già scaricato in precedenza, salto il download")
    else:
        scarica.scarica_file(GTFS_URL, cache_zip.name, barra)
        cache_data.write_text(pubblicato, encoding="utf-8")
    return cache_zip


def prepara_regioni():
    fase(3, "Confini delle regioni")
    file = scarica.CACHE / "regioni.geojson"
    if file.exists():
        print("    già scaricati in precedenza")
    else:
        scarica.scarica_file(REGIONI_URL, file.name, barra)
    return regioni.carica_regioni(file)


def prepara_comuni(oggi):
    """Restituisce (funzione stazione -> (comune, abitanti) o None, anno della popolazione)."""
    fase(4, "Comuni e abitanti (ISTAT)")
    confini = scarica.CACHE / "comuni.geojson"
    if confini.exists():
        print("    confini dei comuni già scaricati in precedenza")
    else:
        print("    download dei confini dei comuni (circa 36 MB, solo la prima volta)")
        scarica.scarica_file(comuni.COMUNI_URL, confini.name, barra)
    # La popolazione dell'anno in corso esce in primavera: fino ad allora si usa quella dell'anno prima.
    for anno in (oggi.year, oggi.year - 1):
        file = scarica.CACHE / f"popolazione_{anno}.zip"
        if not file.exists():
            try:
                scarica.scarica_file(comuni.POPOLAZIONE_URL.format(anno=anno), file.name, barra)
            except FileNotFoundError:
                continue
        break
    else:
        raise ValueError(f"popolazione ISTAT non trovata né per il {oggi.year} né per il {oggi.year - 1}")
    elenco = comuni.carica_comuni(confini)
    abitanti, senza = comuni.abbina_popolazione(elenco, comuni.carica_popolazione(file))
    print(f"    {len(elenco)} comuni, abitanti al 1° gennaio {anno}")
    if senza:
        print(f"    {len(senza)} comuni senza abitanti abbinati: {', '.join(senza[:10])}")

    def comune_di(stazione):
        c = comuni.comune_di(stazione.lat, stazione.lon, elenco)
        return (c.nome, abitanti[c.codice]) if c and c.codice in abitanti else None
    return comune_di, anno


def stampa_riepilogo(nuova, diff, avvisi):
    m = nuova["meta"]
    print("\n" + "=" * 60)
    print("RIEPILOGO")
    print("=" * 60)
    print(f"  Perimetro:          {m['perimetro']} (con i treni fino al capolinea)")
    giorni = ", ".join(f"{datetime.date.fromisoformat(g):%d/%m}" for g in m["giorni_tipo"])
    print(f"  Giorni tipo usati:  mercoledì {giorni}")
    print(f"  Corse regionali:    {m['corse_considerate']} in quei giorni")
    print(f"  Treni nella rete:   {m['conteggi']['treni']} (le corse ripetute sono ridotte alla più veloce)")
    print(f"  Stazioni:           {m['conteggi']['stazioni']}")
    con_comune = sum(1 for s in nuova["stazioni"] if "abitanti" in s)
    print(f"  Con comune/abitanti: {con_comune} (le altre sono all'estero o senza comune trovato)")

    if diff is None:
        print("\n  Prima scansione: nessun confronto possibile.")
    else:
        prima = diff["data_precedente"]
        print(f"\n  Differenze rispetto alla scansione del {datetime.date.fromisoformat(prima):%d/%m/%Y}:" if prima else "\n  Differenze:")
        print(f"    treni: {diff['treni_prima']} -> {diff['treni_ora']}")
        for chiave, titolo in [("stazioni_nuove", "stazioni nuove"), ("stazioni_sparite", "stazioni sparite")]:
            if diff[chiave]:
                print(f"    {titolo} ({len(diff[chiave])}): {', '.join(diff[chiave][:15])}{' ...' if len(diff[chiave]) > 15 else ''}")
        for chiave, titolo in [("collegamenti_nuovi", "collegamenti diretti nuovi"), ("collegamenti_spariti", "collegamenti diretti spariti")]:
            if diff[chiave]:
                esempi = ", ".join(f"{a} -> {b}" for a, b in diff[chiave][:8])
                print(f"    {titolo} ({len(diff[chiave])}): {esempi}{' ...' if len(diff[chiave]) > 8 else ''}")

    print(f"\n  Segnalazioni: {len(avvisi) or 'nessuna'}")
    for a in avvisi:
        print(f"    - {a}")


def esegui(solo_scansione):
    avvisi = []
    oggi = datetime.date.today()
    archivio = gtfs.apri(prepara_orario(avvisi))
    elenco_regioni = prepara_regioni()
    comune_di, anno_popolazione = prepara_comuni(oggi)

    fase(5, "Lettura delle corse regionali dei giorni tipo")
    inizio, fine = gtfs.validita(archivio)
    giorni = gtfs.scegli_giorni_tipo(oggi, inizio, fine)
    print(f"    orario valido dal {inizio:%d/%m/%Y} al {fine:%d/%m/%Y}")
    print(f"    giorni tipo: mercoledì {', '.join(f'{g:%d/%m/%Y}' for g in giorni)}")
    corse, stazioni, avvisi_lettura = gtfs.leggi_corse(archivio, giorni, CATEGORIE_REGIONALI, barra)
    avvisi += avvisi_lettura
    print(f"    {len(corse)} corse regionali in tutta Italia in quei giorni")

    fase(6, f"Costruzione della rete ({PERIMETRO}) e confronto con la precedente")
    nuova = costruisci.costruisci_rete(
        corse, stazioni,
        lambda s: regioni.regione_di(s.lat, s.lon, s.id, elenco_regioni),
        PERIMETRO, oggi, giorni, FONTE.format(anno=anno_popolazione), comune_di,
    )
    senza = [s["nome"] for s in nuova["stazioni"] if s["regione"] != regioni.ESTERO and "abitanti" not in s]
    if senza:
        avvisi.append(f"{len(senza)} stazioni italiane senza comune trovato: {', '.join(senza[:10])}{' ...' if len(senza) > 10 else ''}")
    try:
        vecchia = rete.leggi_rete(FILE_DATI)
    except rete.ErroreFormato as errore:
        avvisi.append(f"il file dati precedente non è leggibile e verrà sostituito: {errore}")
        vecchia = None
    stampa_riepilogo(nuova, rete.differenze(vecchia, nuova), avvisi)

    if rete.contenuto_uguale(vecchia, nuova):
        print("\nLa rete è identica a quella già presente: niente da salvare né da pubblicare.")
        return
    rete.scrivi_rete(FILE_DATI, nuova)
    print(f"\nFile dati aggiornato: {FILE_DATI.relative_to(RADICE)}")
    if solo_scansione:
        return

    risposta = input("\nPubblico? S/N ").strip().upper()
    if risposta != "S":
        print("Non pubblicato. Il file aggiornato resta solo sul computer.")
        return
    riuscito, spiegazione = pubblica.pubblica(RADICE, FILE_DATI, oggi)
    print(("Fatto: " if riuscito else "ATTENZIONE, pubblicazione non riuscita: ") + spiegazione)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("Dove_Arrivo - aggiornamento della rete dei treni regionali")
    try:
        esegui("--solo-scansione" in sys.argv[1:])
    except KeyboardInterrupt:
        print("\n\nInterrotto. Il file dati non è stato toccato.")
        print("Rilancia quando vuoi: i file già scaricati vengono riusati, non si riparte da zero.")
        return 1
    except (ConnectionError, ValueError, OSError) as errore:
        print(f"\n\nERRORE: {errore}")
        print("Il file dati non è stato toccato.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
