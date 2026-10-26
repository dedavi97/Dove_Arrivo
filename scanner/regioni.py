"""Regione di una stazione, ricavata dalle coordinate (confini ISTAT in GeoJSON)."""
import json
import math

ESTERO = "Estero"
SOGLIA_COSTA_KM = 1.0


class Regione:
    def __init__(self, nome, poligoni):
        # Nomi bilingui ("Valle d'Aosta/Vallée d'Aoste"): si tiene la parte italiana.
        self.nome = nome.split("/")[0]
        self.poligoni = poligoni  # [[anello esterno, buco, buco...], ...]; anello = [(lon, lat), ...]
        punti = [p for poligono in poligoni for p in poligono[0]]
        self.lon_min = min(p[0] for p in punti)
        self.lon_max = max(p[0] for p in punti)
        self.lat_min = min(p[1] for p in punti)
        self.lat_max = max(p[1] for p in punti)

    def contiene(self, lat, lon):
        if not (self.lat_min <= lat <= self.lat_max and self.lon_min <= lon <= self.lon_max):
            return False
        for esterno, *buchi in self.poligoni:
            if _dentro_anello(lon, lat, esterno) and not any(_dentro_anello(lon, lat, b) for b in buchi):
                return True
        return False

    def distanza_km(self, lat, lon):
        """Distanza approssimata dal confine (segmento più vicino)."""
        scala = math.cos(math.radians(lat))
        migliore = math.inf
        for poligono in self.poligoni:
            for anello in poligono:
                for (x1, y1), (x2, y2) in zip(anello, anello[1:]):
                    ax, ay = (x1 - lon) * scala, y1 - lat
                    dx, dy = (x2 - x1) * scala, y2 - y1
                    lunghezza = dx * dx + dy * dy
                    t = 0 if lunghezza == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / lunghezza))
                    migliore = min(migliore, math.hypot(ax + t * dx, ay + t * dy))
        return 111.2 * migliore


def _dentro_anello(x, y, anello):
    dentro = False
    j = len(anello) - 1
    for i in range(len(anello)):
        xi, yi = anello[i][0], anello[i][1]
        xj, yj = anello[j][0], anello[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            dentro = not dentro
        j = i
    return dentro


def carica_regioni(percorso):
    dati = json.loads(percorso.read_text(encoding="utf-8"))
    regioni = []
    for f in dati["features"]:
        g = f["geometry"]
        poligoni = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        regioni.append(Regione(f["properties"]["reg_name"], poligoni))
    return regioni


def regione_di(lat, lon, codice, regioni):
    """I codici stazione italiani iniziano per 83, ma anche alcune stazioni francesi
    della Cuneo-Ventimiglia (Tenda, Breil...) li hanno: decide la posizione.

    I confini sono semplificati: le stazioni sulla costa cadono fino a ~0,3 km fuori
    e vanno alla regione più vicina; quelle francesi distano almeno ~4 km.
    """
    if not codice.startswith("83"):
        return ESTERO
    for r in regioni:
        if r.contiene(lat, lon):
            return r.nome
    distanza, nome = min((r.distanza_km(lat, lon), r.nome) for r in regioni)
    return nome if distanza <= SOGLIA_COSTA_KM else ESTERO
