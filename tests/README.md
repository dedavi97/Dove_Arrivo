# Test

Due gruppi di test, da lanciare dalla cartella principale del progetto:

- **Scanner (Python):** `python -m pytest tests`
- **Sito / calcolo percorsi (JavaScript):** `node --test "tests/**/*.test.js"`

Entrambi devono essere verdi prima di ogni commit di tappa.

- `test_scanner.py` usa un piccolo orario finto (creato al volo) e prova:
  calendari ed eccezioni, minuti dopo mezzanotte, scelta del giorno tipo,
  nomi, riduzione delle corse, regioni (anche costa ed estero), lettura e
  scrittura di rete.json, confronto, pubblicazione del solo file dati su un
  repository git di prova, comuni e abitanti (riga totale ISTAT, abbinamento
  dei codici sardi per nome, stazioni sulla costa). Non usa internet.
- `sito.test.js`: lettura e controllo di rete.json (anche quello pubblicato),
  date, segmenti della mappa, novità, e che `docs/CHANGELOG.md` sia uguale a `CHANGELOG.md`.
- `percorsi.test.js`: calcolo delle mete a giri (cambi, tempo massimo, solo
  in avanti, soglia per i cambi), tratte, colori, treni diretti per tratta;
  più controlli sulla rete reale (Torino Porta Nuova → Asti diretto,
  Torino Porta Nuova → Racconigi con i suoi 5 orari).
- `test_fonti.py`: più fonti — abbinamento delle stazioni (codice solo se
  vicino, nome, tabella manuale), linee e numeri Trenord, orario senza
  calendar.txt, fonte scaduta (dati vecchi tenuti + avviso), fonte non
  scaricabile (copia vecchia o avviso), niente download se la versione è uguale.
- `test_versione.py` / `versione.test.js`: la versione è coerente col changelog.

Ambiente verificato il 26/10/2026: Python 3.12.10 + pytest 9.1.1, Node 24.14.0.
