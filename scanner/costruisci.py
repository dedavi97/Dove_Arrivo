"""Dalle corse del giorno tipo alla rete pubblicata in rete.json."""
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


def tieni_piu_veloci(corse):
    """Tra le corse con la stessa identica sequenza di fermate tiene la più veloce.

    Le ripetizioni nell'arco della giornata (stesso percorso ogni ora) non aggiungono
    informazioni: conta solo il tempo minimo. A parità vince il numero più basso.
    """
    migliori = {}
    for c in corse:
        chiave = tuple(s for s, _ in c.fermate)
        attuale = migliori.get(chiave)
        if attuale is None or (c.fermate[-1][1], _numero(c)) < (attuale.fermate[-1][1], _numero(attuale)):
            migliori[chiave] = c
    return list(migliori.values())


def _numero(corsa):
    return int(corsa.numero) if corsa.numero.isdigit() else float("inf")


def costruisci_rete(corse, stazioni, regione_di, perimetro, data_aggiornamento, giorni_tipo, fonte, comune_di=None):
    """regione_di(stazione) -> nome regione; comune_di(stazione) -> (comune, abitanti) oppure None."""
    regioni = {i: regione_di(stazioni[i]) for i in {s for c in corse for s, _ in c.fermate}}
    dentro = (lambda r: r != ESTERO) if perimetro == ITALIA else (lambda r: r == perimetro)
    nel_perimetro = [c for c in corse if any(dentro(regioni[s]) for s, _ in c.fermate)]
    scelte = sorted(tieni_piu_veloci(nel_perimetro), key=lambda c: (_numero(c), c.numero))
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
        "treni": [
            {
                "numero": c.numero,
                "categoria": c.categoria,
                "fermate": [{"stazione": s, "minuti_dalla_partenza": m} for s, m in c.fermate],
            }
            for c in scelte
        ],
    }
    return rete


def _stazione(s, regione, comune_di):
    dati = {"id": s.id, "nome": bel_nome(s.nome), "lat": round(s.lat, 5), "lon": round(s.lon, 5), "regione": regione}
    trovato = comune_di(s) if comune_di and regione != ESTERO else None
    if trovato:
        dati["comune"], dati["abitanti"] = trovato
    return dati
