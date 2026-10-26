# CLAUDE.md — Dove_Arrivo

Web tool statico (GitHub Pages, repo `dedavi97/Dove_Arrivo`): mappa scura dei
treni regionali, partenza → mete raggiungibili colorate per tempo, percorso
della meta scelta, pulsante "Verifica prezzo" verso Trenitalia. Niente prezzi.

**Davide non è uno sviluppatore: ogni report va scritto in parole semplici, in italiano.**

## Decisioni prese da Davide (non ridiscutere)
- Solo treni regionali (REG, RV e simili). Niente Frecce, Italo, IC.
- Si ignorano date e attese ai cambi. Tempo di viaggio = somma dei minuti sui treni.
- Per ogni tratta si usa il regionale più veloce di un giorno feriale tipo.
- Il ritorno è dato per uguale all'andata.
- Perimetro: prima Piemonte (inclusi i treni che escono dalla regione fino al
  capolinea), poi Italia.
- Architettura: scanner Python locale → file dati; sito statico vanilla JS che lo legge. Nessun server.
- Linee sulla mappa: segmenti dritti tra fermate consecutive.
- Aggiornamento: `Aggiorna_Dati.bat` → scansione → riepilogo → "Pubblico? S/N" →
  se S, commit + push del solo `docs/data/rete.json`.
- Commit di soli dati NON alzano la versione. Messaggio: `data: aggiornamento rete GG/MM/AAAA`.

## Regole di lavoro
- Tappe una alla volta: ognuna col suo commit, test verdi, tag `vX.Y.Z`.
- Push solo dopo conferma esplicita di Davide.
- Mai `git add -A`: aggiungere solo i file voluti.
- Tutto ciò che si scopre su ambiente e API va in questo file.
- Versione: unica costante `VERSIONE` in `docs/versione.js`, mostrata nel footer.
  Deve coincidere con la prima voce di `CHANGELOG.md` (c'è un test).

## Formato rete.json (formato_versione 1)
- `meta`: tipo `"Dove_Arrivo_Rete"`, `formato_versione` 1, `data_aggiornamento`,
  `perimetro`, `conteggi` (stazioni, treni).
- `stazioni`: id, nome, lat, lon, regione.
- `treni`: numero, categoria, fermate in ordine `[{stazione, minuti_dalla_partenza}]`.
- Un solo punto del codice legge/scrive il file (uno in Python, uno in JS).
  Formato sconosciuto o versione diversa → messaggio chiaro, nessuna conversione.

## Calcolo percorsi (browser)
Ricerca a giri: giro 1 = stazioni raggiungibili con un solo treno; giro k = da
ogni stazione raggiunta prendi un altro treno. Giri max = cambi + 1. Solo in
avanti lungo le fermate. Per ogni meta il percorso più breve in minuti.
"Resto della tratta" = fermate successive dell'ultimo treno usato.

## Ambiente (verificato 26/10/2026)
- Windows 11, Git 2.55, Python 3.12.10 (`python` e `py`), pytest 9.1.1,
  requests 2.32.3, Node 24.14.0, npm 11.9.0.
- `gh` (GitHub CLI) NON installato.
- Git globale: user.name `dedavi97`, email `dedavi97@gmail.com`.
- Il repo remoto `github.com/dedavi97/Dove_Arrivo` al 26/10/2026 NON esiste
  (o è privato): va creato da Davide prima del primo push.
- Test: `python -m pytest tests` e `node --test "tests/**/*.test.js"`.

## Fonti dati — risultati tappa 0.0.1

### ViaggiaTreno: BLOCCATO
- Base `http://www.viaggiatreno.it/infomobilita/resteasy/viaggiatreno/`.
- Da questo PC ogni richiesta (`elencoStazioni/1`, `autocompletaStazione/…`,
  `regione/S00219`, `dettaglioStazione/…`, perfino la home page
  `https://www.viaggiatreno.it/infomobilita/index.jsp`) risponde
  **403 "Access Denied" di Akamai** (firewall anti-bot). Google e trenitalia.com rispondono.
- Non va aggirato fingendosi un browser (è aggirare un controllo anti-bot).

### Alternativa trovata: orario ufficiale Trenitalia (NeTEx/GTFS)
- **Fonte ufficiale**: Punto di Accesso Nazionale (NAP, CCISS/MIT),
  dataset "OAP Trenitalia - NeTEx Livello 1":
  https://www.cciss.it/nap/mmtis/public/en/catalog/Dataset/1077621
  Download diretto, senza login (verificato 200 OK, `IT-IT-TRENITALIA_L1.xml.gz`):
  `https://www.cciss.it/nap/mmtis/public/api/v1/download/blob/Asset/1080596/checkedResource`
  (licenza non indicata nella pagina).
- **Conversione GTFS pronta** (terze parti, CC-BY-4.0, aggiornata ogni lunedì
  da GitHub Actions): https://github.com/deryclem/trenitalia-gtfs
  Download: `https://github.com/deryclem/trenitalia-gtfs/raw/main/gtfs-trenitalia.zip`
  (~6,5 MB). Data pubblicazione: `.last_publication_timestamp` nel repo
  (al 26/10/2026: 2026-10-22T14:15:47Z; validità 24/10/2026 → 11/12/2027).
  Attribuzione richiesta: Trenitalia / CCISS MMTIS + Clément Desouche.
- Contenuto GTFS verificato:
  - `stops.txt`: 1927 stazioni (location_type 1) + 1927 punti di fermata (0),
    **tutte con coordinate**. Codice = `83` + codice ViaggiaTreno a 7 cifre
    (es. TORINO PORTA NUOVA `830000219` ↔ ViaggiaTreno `S00219`).
    I `stop_times` puntano ai ScheduledStopPoint (location_type 0), col
    `parent_station` alla StopPlace.
  - **Manca la regione** della stazione: va ricavata dalle coordinate
    (confini regionali ISTAT) o da un'altra tabella.
  - `routes.txt`: una riga per categoria, `route_short_name` = `0083_<CAT>`:
    REG, RV, SFM, MET, BUS, IC, ICN, EC, EN, FR, FA, FB, EXP.
  - `trips.txt`: `trip_short_name` = numero treno. Calendari in
    `calendar.txt` + `calendar_dates.txt`.
  - Mercoledì 04/11/2026: 7788 corse attive (REG 4682, RV 765, SFM 295, MET 199,
    BUS 1385, FR 282, IC 94, …). Regionali (REG/RV/SFM/MET) che toccano un
    riquadro grezzo del Piemonte: 1049, su 370 stazioni. Nessun numero treno
    duplicato nello stesso giorno.
  - Lettura completa dello zip con Python standard (csv + zipfile): ~1 s.
- Limite: contiene solo Trenitalia. Altri operatori regionali (es. Trenord su
  Novara/Domodossola, GTT, TILO) non ci sono.

### Link precompilato Trenitalia: NON documentato
- trenitalia.com rimanda la ricerca a lefrecce.it, app a pagina singola con
  route nell'hash, es. `https://www.lefrecce.it/Channels.Website.WEB/#/?tab=biglietto`.
- Nessun parametro partenza/arrivo documentato; non verificabile senza browser.
  Da provare a mano (Davide fa una ricerca e copia l'URL risultante).
