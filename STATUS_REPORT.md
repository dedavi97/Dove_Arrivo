# Stato del progetto

**Versione:** 0.3.1 — 26/10/2026
**Tappa conclusa:** 0.3.0 (partenza, cursori, mete, percorso)
**Prossima tappa:** 0.4.0 — estensione a tutta Italia

## Cosa funziona
- **Sito** (https://dedavi97.github.io/Dove_Arrivo/): scegli la partenza
  toccando una stazione o cercandola per nome; due cursori per cambi massimi
  (0–3) e ore massime (30 min – 6 h). Le mete si colorano per tempo (verde,
  giallo, rosso), le altre si spengono; legenda sempre visibile.
- Toccando una meta: treni, cambi, tempo totale, fin dove prosegue l'ultimo
  treno usato; percorso evidenziato, prosecuzioni tratteggiate, cambi
  segnati con un anello viola;
  "Verifica prezzo" apre Trenitalia, "Parti da qui" cambia partenza.
- Impostazioni (ricorda partenza e limiti, mostra linee), Aiuto, Informazioni.
- Provato in formato telefono e computer.
- `Aggiorna_Dati.bat` aggiorna i dati in ~5 secondi (4 mercoledì tipo).

## Da decidere
- Soglia per i cambi: un percorso con un cambio in più viene proposto solo
  se fa risparmiare almeno 10 minuti per cambio. Valore da confermare.

## Da sapere
- La Valle d'Aosta non compare (Ivrea–Aosta servita solo da autobus).
- Mancano gli altri operatori (es. Trenord).
