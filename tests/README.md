# Test

Due gruppi di test, da lanciare dalla cartella principale del progetto:

- **Scanner (Python):** `python -m pytest tests`
- **Sito / calcolo percorsi (JavaScript):** `node --test "tests/**/*.test.js"`

Entrambi devono essere verdi prima di ogni commit di tappa.

- `test_scanner.py` usa un piccolo orario finto (creato al volo) e prova:
  calendari ed eccezioni, minuti dopo mezzanotte, scelta del giorno tipo,
  nomi, riduzione delle corse, regioni (anche costa ed estero), lettura e
  scrittura di rete.json, confronto, pubblicazione del solo file dati su un
  repository git di prova. Non usa internet.
- `sito.test.js`: lettura e controllo di rete.json (anche quello pubblicato),
  date, segmenti della mappa, novità, e che `docs/CHANGELOG.md` sia uguale a `CHANGELOG.md`.
- `test_versione.py` / `versione.test.js`: la versione è coerente col changelog.

Ambiente verificato il 26/10/2026: Python 3.12.10 + pytest 9.1.1, Node 24.14.0.
