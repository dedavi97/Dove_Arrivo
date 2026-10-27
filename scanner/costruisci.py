"""Dalle corse del giorno tipo alla rete pubblicata in rete.json."""
import math
import re

from . import rete as formato
from .regioni import ESTERO

ITALIA = "Italia"  # perimetro speciale: tutte le regioni

ABBREVIAZIONI = {"C.Le": "Centrale"}  # es. "BOLOGNA C.LE"
PAROLE_MINUSCOLE = {"d", "di", "del", "della", "dei", "delle", "da", "in", "sul", "sulla", "al", "alla", "e"}


def bel_nome(nome):
    """'REGGIO DI CALABRIA S.CATERINA' -> 'Reggio di Calabria S.Caterina'. I nomi già misti restano come sono."""
    if nome != nome.upper():
        return nome
    parti = re.split(r"([ .'\-/()])", nome.lower())
    risultato = []
    for i, p in enumerate(parti):
        if p and p[0].isalpha() and not (i > 0 and p in PAROLE_MINUSCOLE):
            p = p[0].upper() + p[1:]
        risultato.append(p)
    bello = "".join(risultato)
    for breve, esteso in ABBREVIAZIONI.items():
        bello = re.sub(rf"\b{re.escape(breve)}$", esteso, bello)
    return bello


def raggruppa_per_sequenza(corse):
    """{(operatore, sequenza di fermate): [corse con quella sequenza]}."""
    gruppi = {}
    for c in corse:
        gruppi.setdefault((c.operatore, tuple(s for s, _ in c.fermate)), []).append(c)
    return gruppi


def piu_veloce(gruppo):
    """Per il calcolo dei percorsi conta solo il tempo minimo. A parità vince il numero più basso."""
    return min(gruppo, key=lambda c: (c.fermate[-1][1], _numero(c)))


def tieni_piu_veloci(corse):
    """Tra le corse con la stessa identica sequenza di fermate tiene la più veloce."""
    return [piu_veloce(g) for g in raggruppa_per_sequenza(corse).values()]


def orari_gruppo(gruppo):
    """Orari di tutte le corse con la stessa sequenza, in forma compatta: (profili, corse).

    profili = liste distinte di "minuti dopo la partenza" in cui si riparte da ogni fermata;
    corse = [inizio (minuti dalla mezzanotte), indice del profilo, giorni (bit per giorno tipo)],
    ordinate per inizio. La stessa corsa in giorni diversi diventa una riga sola (bit uniti).
    """
    profili, indice_profilo, giorni_di = [], {}, {}
    for c in gruppo:
        chiave = tuple(c.partenze)
        if chiave not in indice_profilo:
            indice_profilo[chiave] = len(profili)
            profili.append(list(chiave))
        riga = (c.inizio, indice_profilo[chiave])
        giorni_di[riga] = giorni_di.get(riga, 0) | c.giorni
    return profili, [[inizio, p, g] for (inizio, p), g in sorted(giorni_di.items())]


# Linee che seguono i binari (0.8.0): tra due fermate consecutive si passa per i punti del
# tracciato GTFS (in gran parte stazioni dove il treno non ferma). Tracciati dubbi: linea dritta.
MAX_SCOSTAMENTO_FERMATA_KM = 0.5   # il tracciato deve passare vicino a ogni fermata
MIN_DISTANZA_DA_FERMATA_KM = 0.2   # punti attaccati alle fermate non servono
# Tra due fermate il tracciato può essere al massimo 1,8 volte la linea dritta (+1 km): nel GTFS
# Trenitalia ci sono punti fuori posto (es. Firenze Campo Marte -> S.M. Novella: 2,4 km in linea
# d'aria, 48 km di "tracciato"); le ferrovie vere, anche di montagna, restano sotto.
MAX_ALLUNGAMENTO = 1.8
MARGINE_ALLUNGAMENTO_KM = 1.0


def _km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def togli_punte(percorso):
    """Toglie i punti dove la linea va e torna indietro (una "V" stretta): sono punti fuori posto
    nel tracciato. Un punto è una punta se i suoi vicini sono molto più vicini tra loro che a lui."""
    punti = list(percorso)
    cambiato = True
    while cambiato and len(punti) > 2:
        cambiato = False
        for k in range(1, len(punti) - 1):
            andata = _km(punti[k - 1], punti[k]) + _km(punti[k], punti[k + 1])
            if andata > 0.5 and _km(punti[k - 1], punti[k + 1]) < 0.4 * andata:
                del punti[k]
                cambiato = True
                break
    return punti


def punti_intermedi(fermate, punti):
    """Per ogni coppia di fermate consecutive (coordinate) i punti del tracciato tra le due.
    Un tratto dubbio (fermata lontana dal tracciato, giro troppo lungo) dà [] = linea dritta,
    senza buttare via il resto del treno."""
    i = min(range(len(punti)), key=lambda k: _km(punti[k], fermate[0]))
    risultato = []
    for a, b in zip(fermate, fermate[1:]):
        j = min(range(i, len(punti)), key=lambda k: _km(punti[k], b))
        if _km(punti[j], b) > MAX_SCOSTAMENTO_FERMATA_KM or _km(punti[i], a) > MAX_SCOSTAMENTO_FERMATA_KM:
            risultato.append([])
            if _km(punti[j], b) <= MAX_SCOSTAMENTO_FERMATA_KM:
                i = j
            continue
        tra = [p for p in punti[i + 1:j] if min(_km(p, a), _km(p, b)) > MIN_DISTANZA_DA_FERMATA_KM]
        tra = togli_punte([a, *tra, b])[1:-1]
        percorso = [a, *tra, b]
        lunghezza = sum(_km(p, q) for p, q in zip(percorso, percorso[1:]))
        risultato.append(tra if lunghezza <= MAX_ALLUNGAMENTO * _km(a, b) + MARGINE_ALLUNGAMENTO_KM else [])
        i = j
    return risultato


def tracciati(gruppi, stazioni, forme):
    """[[id A, id B, [[lat, lon], ...]]] con A < B e i punti da A verso B; solo i tratti con
    punti intermedi. Se più treni passano tra A e B si tiene il tracciato più dettagliato."""
    migliori = {}
    for gruppo in gruppi:
        c = piu_veloce(gruppo)
        punti = forme.get((c.operatore, c.forma))
        if not punti:
            continue
        ids = [s for s, _ in c.fermate]
        intermedi = punti_intermedi([(stazioni[s].lat, stazioni[s].lon) for s in ids], punti)
        for a, b, tra in zip(ids, ids[1:], intermedi):
            if not tra:
                continue
            chiave, tra = ((a, b), tra) if a < b else ((b, a), tra[::-1])
            if len(tra) > len(migliori.get(chiave, [])):
                migliori[chiave] = tra
    return [[a, b, [[round(la, 5), round(lo, 5)] for la, lo in tra]] for (a, b), tra in sorted(migliori.items())]


def _numero(corsa):
    return int(corsa.numero) if corsa.numero.isdigit() else float("inf")


def costruisci_rete(corse, stazioni, regione_di, perimetro, data_aggiornamento, giorni_tipo, fonte, comune_di=None, fonti=None,
                    forme=None):
    """regione_di(stazione) -> nome regione; comune_di(stazione) -> (comune, abitanti) oppure None;
    fonti = riepilogo di ogni fonte (nome, validità, scaduta, attribuzione...) da mettere in meta."""
    regioni = {i: regione_di(stazioni[i]) for i in {s for c in corse for s, _ in c.fermate}}
    dentro = (lambda r: r != ESTERO) if perimetro == ITALIA else (lambda r: r == perimetro)
    nel_perimetro = [c for c in corse if any(dentro(regioni[s]) for s, _ in c.fermate)]
    gruppi = list(raggruppa_per_sequenza(nel_perimetro).values())
    gruppi.sort(key=lambda g: (_numero(piu_veloce(g)), piu_veloce(g).numero))
    scelte = [piu_veloce(g) for g in gruppi]
    usate = sorted({s for c in scelte for s, _ in c.fermate}, key=lambda i: bel_nome(stazioni[i].nome))

    rete = {
        "meta": {
            "tipo": formato.TIPO,
            "formato_versione": formato.FORMATO_VERSIONE,
            "data_aggiornamento": data_aggiornamento.isoformat(),
            "perimetro": perimetro,
            "conteggi": {"stazioni": len(usate), "treni": len(scelte)},
            "giorni_tipo": [g.isoformat() for g in giorni_tipo],
            "corse_considerate": len(nel_perimetro),
            "fonte": fonte,
        },
        "stazioni": [_stazione(stazioni[i], regioni[i], comune_di) for i in usate],
        "treni": [_treno(g) for g in gruppi],
    }
    if forme:
        rete["tracciati"] = tracciati(gruppi, stazioni, forme)
    if fonti is not None:
        for f in fonti:
            f["treni"] = sum(1 for g in gruppi if piu_veloce(g).operatore == f["nome"])
        rete["meta"]["fonti"] = fonti
    return rete


def _treno(gruppo):
    c = piu_veloce(gruppo)
    profili, corse = orari_gruppo(gruppo)
    treno = {
        "numero": c.numero,
        "categoria": c.categoria,
        "fermate": [{"stazione": s, "minuti_dalla_partenza": m} for s, m in c.fermate],
        "profili": profili,
        "corse": corse,
    }
    if c.operatore:
        treno["operatore"] = c.operatore
    return treno


def _stazione(s, regione, comune_di):
    dati = {"id": s.id, "nome": bel_nome(s.nome), "lat": round(s.lat, 5), "lon": round(s.lon, 5), "regione": regione}
    trovato = comune_di(s) if comune_di and regione != ESTERO else None
    if trovato:
        dati["comune"], dati["abitanti"] = trovato
    return dati
