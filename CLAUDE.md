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

### Link precompilato Trenitalia: NON esiste
- trenitalia.com rimanda la ricerca a lefrecce.it, app a pagina singola con
  route nell'hash, es. `https://www.lefrecce.it/Channels.Website.WEB/#/?tab=biglietto`.
- Prova di Davide (26/10/2026): dopo una ricerca l'URL è
  `.../#/search-results?cid=...&handoff=true&referrer=...` → **nessuna stazione
  nell'URL**. Il pulsante "Verifica prezzo" aprirà la ricerca e mostrerà
  partenza/arrivo da copiare.

## Decisioni del 26/10/2026 (Davide)
- Fonte dati = orario Trenitalia GTFS (deryclem). ViaggiaTreno abbandonato.
  Altri operatori (Trenord, GTT, TILO…): da valutare più avanti.
- Categorie regionali: REG, RV, SFM (metropolitano Torino), MET (passante
  di Napoli, linea 2). Esclusi BUS e tutte le Frecce/IC/EC/EN/EXP.
- Le Frecce sono nel GTFS: possibile funzione futura, non prioritaria.

## Scanner (dalla 0.1.0)
- `python -m scanner` (lo lancia `Aggiorna_Dati.bat`); `--solo-scansione`
  non chiede di pubblicare. Tutto il giro richiede ~5 s.
- Moduli: `scarica` (download con cache in `scanner/cache/`, file `.part`,
  3 nuovi tentativi), `gtfs` (lettura zip, giorno tipo, corse), `regioni`
  (punto-in-poligono sui confini ISTAT), `costruisci` (perimetro, riduzione,
  nomi), `rete` (UNICO punto di lettura/scrittura di rete.json + confronto),
  `pubblica` (git add/commit --only/push del solo file dati).
- Il GTFS si riscarica solo se `.last_publication_timestamp` è cambiato.
- Giorno tipo: primo mercoledì da oggi+7 giorni, dentro la validità, non
  festivo, fuori dal 20/12–07/01.
- Minuti: partenza alla prima fermata, poi l'arrivo in ogni fermata
  (A→B = arrivo B − arrivo A, include la sosta in A). Corse con orari che
  tornano indietro: scartate e segnalate.
- Riduzione: tra corse con identica sequenza di fermate si tiene la più
  veloce (a parità il numero più basso). 869 corse → 214 treni, 317 stazioni.
- Perimetro: treni con almeno una fermata in Piemonte, presi interi fino al capolinea.
- Regione: le stazioni con codice non `83…` sono "Estero". Fuori da tutti i
  poligoni: entro 1 km → regione più vicina (stazioni costiere, max 0,32 km),
  oltre → "Estero" (stazioni francesi della Cuneo–Ventimiglia con codice
  italiano: Tenda, Breil, La Brigue, Fontan, St-Dalmas, Vievola, ≥3,9 km).
- Nomi: tutti maiuscoli nel GTFS → resi "Torino Porta Nuova", "Castello d'Annone".
- rete.json: una stazione/un treno per riga (diff git leggibili). Campi extra
  in meta: `giorno_tipo`, `corse_considerate`, `fonte` (attribuzioni CC-BY).
- Nov 2026: la Ivrea–Aosta è servita solo da BUS sostitutivi → Valle d'Aosta
  assente dalla rete (corretto, non è un errore).
- Node 24: `node --test tests` NON funziona (lo prende come file):
  usare `node --test "tests/**/*.test.js"`.

## Sito (dalla 0.2.0)
- File: `docs/index.html`, `style.css`, `versione.js` (VERSIONE), `rete.js`
  (UNICO punto JS che legge rete.json: `caricaRete`, `validaRete`,
  `formattaData`, `segmentiUnici`), `app.js` (interfaccia). Script classici,
  niente build; per i test Node ogni file esporta con
  `if (typeof module !== "undefined") module.exports = …` e `app.js` avvia
  l'interfaccia solo se esiste `document`.
- Leaflet 1.9.4 da cdnjs con integrity SRI (hash in index.html).
- **CARTO dark (basemaps.cartocdn.com) dal 2026 mostra "API KEY REQUIRED"**:
  si usano le tile OpenStreetMap (`tile.openstreetmap.org`, senza chiave,
  attribuzione obbligatoria) scurite con filtro CSS `.mappa-scura`.
- Le novità in "Informazioni" vengono da `docs/CHANGELOG.md`, **copia esatta**
  di `CHANGELOG.md` (GitHub Pages serve solo `docs/`). Un test verifica che
  siano identici: dopo ogni modifica del changelog `cp CHANGELOG.md docs/CHANGELOG.md`.
- GitHub Pages: va configurato su branch `main`, cartella `/docs`
  (Settings → Pages). URL atteso: https://dedavi97.github.io/Dove_Arrivo/
- Remote `origin` = https://github.com/dedavi97/Dove_Arrivo.git (aggiunto il
  26/10/2026, repo vuoto a quella data).
- Verifica visiva senza browser interattivo: Edge headless
  (`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe --headless=new
  --screenshot=… --window-size=1440,900 --virtual-time-budget=10000 URL`).
  Sotto ~500 px di larghezza la finestra headless non si restringe: per il
  formato telefono mettere il sito in un `<iframe>` largo 390 px servito dalla
  stessa origine (copia di docs/ nello scratchpad + pagina di prova).
- `Avvia_Locale.bat`: `python -m http.server 8765 --bind 127.0.0.1 --directory docs`.
