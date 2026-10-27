# Dove_Arrivo

Mappa scura della rete dei treni regionali di tutta Italia (Trenitalia e Trenord). Scegli una stazione di partenza,
quanti cambi al massimo e quante ore al massimo: la mappa colora le mete
raggiungibili in base al tempo di viaggio. Cliccando una meta vedi il percorso,
quanti treni diretti ci sono al giorno su ogni tratta e a che ora partono.

Niente prezzi: il pulsante "Verifica prezzo" apre il sito Trenitalia.

## Come si usa
- **Avvia_Locale.bat** — apre il sito sul tuo computer.
- **Aggiorna_Dati.bat** — scarica gli orari, ricostruisce la rete e,
  se confermi, pubblica il nuovo file dati.

## Com'è fatto
- `scanner/` — programma Python che costruisce la rete dei treni da più fonti
  (`scanner/fonti.py`). Le stazioni che non si riescono ad abbinare da sole tra
  due aziende si aggiungono a mano in `scanner/abbinamenti_manuali.csv`.
- `docs/` — il sito (pubblicato con GitHub Pages); `docs/data/rete.json` è l'unico file dati.
- `tests/` — test automatici (vedi `tests/README.md`).

Stato attuale: vedi `STATUS_REPORT.md`. Cose da fare: `BACKLOG.md`.
