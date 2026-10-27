"""Scansione completa: python -m scanner [--solo-scansione]"""
import datetime
import sys
from pathlib import Path

from . import comuni, costruisci, fonti, gtfs, pubblica, regioni, rete, scarica

RADICE = Path(__file__).resolve().parent.parent
FILE_DATI = RADICE / "docs" / "data" / "rete.json"

PERIMETRO = costruisci.ITALIA  # oppure il nome di una regione, es. "Piemonte"

REGIONI_URL = "https://raw.githubusercontent.com/openpolis/geojson-italy/master/geojson/limits_IT_regions.geojson"
FONTE_TERRITORIO = (
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


def prepara_orari(avvisi):
    fase(1, "Orari: controllo se ce ne sono di nuovi e li scarico")
    percorsi = []
    for fonte in fonti.FONTI:
        percorso = fonti.prepara(fonte, avvisi, barra)
        if percorso:
            percorsi.append((fonte, percorso))
    return percorsi


def prepara_regioni():
    fase(2, "Confini delle regioni")
    file = scarica.CACHE / "regioni.geojson"
    if file.exists():
        print("    già scaricati in precedenza")
    else:
        scarica.scarica_file(REGIONI_URL, file.name, barra)
    return regioni.carica_regioni(file)


def prepara_comuni(oggi):
    """Restituisce (funzione stazione -> (comune, abitanti) o None, anno della popolazione)."""
    fase(3, "Comuni e abitanti (ISTAT)")
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


def stampa_riepilogo(nuova, diff, avvisi, abbinamenti=None):
    """abbinamenti = {nome fonte: info della lettura con "abbinamenti" e "nuove"}."""
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
    for f in m.get("fonti", []):
        dal, al = (datetime.date.fromisoformat(f[k]) for k in ("validita_dal", "validita_al"))
        print(f"\n  {f['nome'].upper()}")
        print(f"    treni nella rete: {f['treni']}")
        print(f"    orario valido:    dal {dal:%d/%m/%Y} al {al:%d/%m/%Y}")
        if f["scaduta"]:
            print("    !!! ORARIO SCADUTO: si usano i suoi dati vecchi finché non ne esce uno nuovo !!!")
        extra = (abbinamenti or {}).get(f["nome"], {})
        if "abbinamenti" in extra:
            modi = ", ".join(f"{modo} {n}" for modo, n in sorted(extra["abbinamenti"].items()) if modo != "nuova")
            print(f"    stazioni abbinate a Trenitalia: {modi or 'nessuna'}")
            nuove = extra["nuove"]
            print(f"    stazioni nuove (non abbinate): {len(nuove)}"
                  + (f" - es. {', '.join(nuove[:8])}{' ...' if len(nuove) > 8 else ''}" if nuove else ""))

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
    percorsi = prepara_orari(avvisi)
    elenco_regioni = prepara_regioni()
    comune_di, anno_popolazione = prepara_comuni(oggi)

    fase(4, "Lettura delle corse regionali dei giorni tipo")
    principale = percorsi[0][1]  # Trenitalia: i giorni tipo si scelgono sulla sua validità
    inizio, fine = gtfs.validita(gtfs.apri(principale))
    giorni = gtfs.scegli_giorni_tipo(oggi, inizio, fine)
    print(f"    giorni tipo: mercoledì {', '.join(f'{g:%d/%m/%Y}' for g in giorni)}")
    lette = []
    for fonte, percorso in percorsi:
        print(f"    {fonte.nome}:")
        letta = fonti.leggi(fonte, percorso, giorni, oggi, avvisi, barra)
        print(f"    {fonte.nome}: {len(letta.corse)} corse")
        lette.append(letta)

    fase(5, "Unione delle fonti (stazioni in comune)")
    corse, stazioni = fonti.unisci(lette, avvisi)
    for letta in lette[1:]:
        print(f"    {letta.fonte.nome}: {letta.info['abbinamenti']}")

    fase(6, f"Costruzione della rete ({PERIMETRO}) e confronto con la precedente")
    attribuzioni = " ".join([letta.fonte.attribuzione for letta in lette] + [FONTE_TERRITORIO.format(anno=anno_popolazione)])
    nuova = costruisci.costruisci_rete(
        corse, stazioni,
        lambda s: regioni.regione_di(s.lat, s.lon, s.uic, elenco_regioni),
        PERIMETRO, oggi, giorni, attribuzioni, comune_di,
        [{k: letta.info[k] for k in ("nome", "validita_dal", "validita_al", "scaduta", "attribuzione")} for letta in lette],
        {k: v for letta in lette for k, v in letta.forme.items()},
    )
    senza = [s["nome"] for s in nuova["stazioni"] if s["regione"] != regioni.ESTERO and "abitanti" not in s]
    if senza:
        avvisi.append(f"{len(senza)} stazioni italiane senza comune trovato: {', '.join(senza[:10])}{' ...' if len(senza) > 10 else ''}")
    try:
        vecchia = rete.leggi_rete(FILE_DATI)
    except rete.ErroreFormato as errore:
        avvisi.append(f"il file dati precedente non è leggibile e verrà sostituito: {errore}")
        vecchia = None
    stampa_riepilogo(nuova, rete.differenze(vecchia, nuova), avvisi, {letta.fonte.nome: letta.info for letta in lette})

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
