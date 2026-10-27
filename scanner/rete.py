"""Unico punto del codice Python che legge e scrive rete.json."""
import json

TIPO = "Dove_Arrivo_Rete"
FORMATO_VERSIONE = 1


class ErroreFormato(Exception):
    pass


def leggi_rete(percorso):
    """Legge rete.json. Restituisce None se il file non esiste ancora."""
    if not percorso.exists():
        return None
    try:
        rete = json.loads(percorso.read_text(encoding="utf-8"))
    except json.JSONDecodeError as errore:
        raise ErroreFormato(f"{percorso.name} non è un file JSON valido ({errore})")
    meta = rete.get("meta", {}) if isinstance(rete, dict) else {}
    if meta.get("tipo") != TIPO:
        raise ErroreFormato(f"{percorso.name} non è un file dati di Dove_Arrivo")
    if meta.get("formato_versione") != FORMATO_VERSIONE:
        raise ErroreFormato(
            f"{percorso.name} ha formato versione {meta.get('formato_versione')}, "
            f"questo programma conosce solo la {FORMATO_VERSIONE}"
        )
    return rete


def scrivi_rete(percorso, rete):
    """Scrive una stazione o un treno per riga, così le differenze in git restano leggibili."""
    def riga(oggetto):
        return json.dumps(oggetto, ensure_ascii=False, separators=(",", ":"))

    parti = [
        "{",
        f'"meta":{riga(rete["meta"])},',
        '"stazioni":[',
        ",\n".join(riga(s) for s in rete["stazioni"]),
        "],",
        '"treni":[',
        ",\n".join(riga(t) for t in rete["treni"]),
        "]",
    ]
    if "tracciati" in rete:
        parti[-1] += ","
        parti += ['"tracciati":[', ",\n".join(riga(t) for t in rete["tracciati"]), "]"]
    parti.append("}")
    temporaneo = percorso.with_suffix(".tmp")
    percorso.parent.mkdir(parents=True, exist_ok=True)
    temporaneo.write_text("\n".join(parti) + "\n", encoding="utf-8")
    temporaneo.replace(percorso)


def _collegamenti(rete):
    nomi = {s["id"]: s["nome"] for s in rete["stazioni"]}
    coppie = set()
    for t in rete["treni"]:
        f = t["fermate"]
        for a, b in zip(f, f[1:]):
            coppie.add((nomi[a["stazione"]], nomi[b["stazione"]]))
    return coppie


def differenze(vecchia, nuova):
    """Confronto leggibile tra due reti. vecchia può essere None (prima scansione)."""
    if vecchia is None:
        return None
    nomi_v = {s["nome"] for s in vecchia["stazioni"]}
    nomi_n = {s["nome"] for s in nuova["stazioni"]}
    coll_v, coll_n = _collegamenti(vecchia), _collegamenti(nuova)
    return {
        "stazioni_nuove": sorted(nomi_n - nomi_v),
        "stazioni_sparite": sorted(nomi_v - nomi_n),
        "treni_prima": len(vecchia["treni"]),
        "treni_ora": len(nuova["treni"]),
        "collegamenti_nuovi": sorted(coll_n - coll_v),
        "collegamenti_spariti": sorted(coll_v - coll_n),
        "data_precedente": vecchia["meta"].get("data_aggiornamento"),
    }


def contenuto_uguale(vecchia, nuova):
    """Vero se stazioni, treni e tracciati sono identici (la data di aggiornamento non conta)."""
    return (vecchia is not None and vecchia["stazioni"] == nuova["stazioni"] and vecchia["treni"] == nuova["treni"]
            and vecchia.get("tracciati") == nuova.get("tracciati"))
