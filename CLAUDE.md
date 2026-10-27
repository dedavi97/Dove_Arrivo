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
  **A ogni cambio di versione aggiornare anche `?v=X.Y.Z` in `docs/index.html`**
  (style.css e i 4 script; c'è un test): senza, il browser mescola file
  vecchi (in cache) e nuovi e la mappa resta vuota (successo con la 0.8.0).

## Formato rete.json (formato_versione 1)
- `meta`: tipo `"Dove_Arrivo_Rete"`, `formato_versione` 1, `data_aggiornamento`,
  `perimetro`, `conteggi` (stazioni, treni).
- `stazioni`: id, nome, lat, lon, regione; dalla 0.5.0 anche `comune` e
  `abitanti` (solo stazioni italiane: le estere non li hanno). Campi aggiunti
  senza cambiare `formato_versione` (chi non li conosce li ignora).
- `treni`: numero, categoria, fermate in ordine `[{stazione, minuti_dalla_partenza}]`.
  Dalla 0.6.0 anche `profili` e `corse` (orari di tutte le corse con quella
  sequenza di fermate, vedi "Frequenze"). Sempre `formato_versione` 1.
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

## Decisioni del 27/10/2026 (Davide, handoff unico)
- Prezzi: in futuro SOLO il prezzo totale del biglietto unico per il viaggio
  intero. Niente confronto con la somma delle tratte.
- Filtro/colori per prezzo solo se si trova un sistema affidabile.
- Linee sui binari: solo versione semplice (passare per le stazioni
  intermedie del tracciato GTFS, shapes.txt). Niente curve da OpenStreetMap.
- La regola "si ignorano orari e attese" resta, ma la scheda deve dire
  QUANTI treni diretti ci sono e A CHE ORA (fatto nella 0.6.0).
- Più avanti: alleggerire l'interfaccia (non ora).
- Piano: 0.6.0 frequenze → 0.7.0 Trenord (prima indagine + report, poi ok)
  → indagine prezzi (solo report) → 0.8.0 linee sulle stazioni intermedie.

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
- Giorni tipo (dalla 0.2.1): 4 mercoledì, il primo da oggi+7 giorni, poi
  ogni 3 settimane; dentro la validità, non festivi, fuori dal 20/12–07/01.
  Si uniscono le corse di tutti e 4 i giorni. Motivo: con un solo giorno
  (04/11/2026) mancavano Torino–Asti e Cuneo–Limone, interrotte per lavori
  quel giorno (solo BUS). Con 4 giorni: 1611 corse → 237 treni, 328 stazioni.
- Minuti: partenza alla prima fermata, poi l'arrivo in ogni fermata
  (A→B = arrivo B − arrivo A, include la sosta in A). Corse con orari che
  tornano indietro: scartate e segnalate.
- Riduzione: tra corse con identica sequenza di fermate si tiene la più
  veloce (a parità il numero più basso).
- Perimetro: treni con almeno una fermata in Piemonte, presi interi fino al capolinea.
- Regione: le stazioni con codice non `83…` sono "Estero". Fuori da tutti i
  poligoni: entro 1 km → regione più vicina (stazioni costiere, max 0,32 km),
  oltre → "Estero" (stazioni francesi della Cuneo–Ventimiglia con codice
  italiano: Tenda, Breil, La Brigue, Fontan, St-Dalmas, Vievola, ≥3,9 km).
- Nomi: tutti maiuscoli nel GTFS → resi "Torino Porta Nuova", "Castello d'Annone".
- rete.json: una stazione/un treno per riga (diff git leggibili). Campi extra
  in meta: `giorni_tipo` (lista), `corse_considerate`, `fonte` (attribuzioni CC-BY).
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
- GitHub Pages: ATTIVO dal 26/10/2026 su branch `main`, cartella `/docs`
  (Settings → Pages). URL atteso: https://dedavi97.github.io/Dove_Arrivo/
- Remote `origin` = https://github.com/dedavi97/Dove_Arrivo.git (aggiunto il
  26/10/2026, repo vuoto a quella data).
- Verifica visiva senza browser interattivo: Edge headless
  (`C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe --headless=new
  --screenshot=… --window-size=1440,900 --virtual-time-budget=10000 URL`).
  Sotto ~500 px di larghezza la finestra headless non si restringe: per il
  formato telefono mettere il sito in un `<iframe>` largo 390 px servito dalla
  stessa origine (copia di docs/ nello scratchpad + pagina di prova).
- `Avvia_Locale.bat` (dalla 0.8.1): `python -m scanner.servi_locale 8765` =
  http.server su docs/ con `Cache-Control: no-cache` (prima `python -m
  http.server`, che manda solo Last-Modified: i browser tenevano i file vecchi).

## Tutta Italia (dalla 0.4.0)
- `PERIMETRO = costruisci.ITALIA` ("Italia"): si tengono i treni con almeno
  una fermata non "Estero". Il sito usa `nelPerimetro()` per lo stesso criterio.
- 27/10/2026: 10139 corse → 2082 treni, 1714 stazioni; rete.json 1,6 MB
  (≈140 KB compresso, GitHub Pages lo serve in gzip). Scansione ~2,5 s.
- Calcolo nel browser (Node, rete reale): indice 2 ms; da Milano/Roma con
  3 cambi e 6 h ≈5 ms. Nessun problema di prestazioni.
- **Copertura**: solo Trenitalia. Lombardia (43 stazioni: Trenord) ed
  Emilia-Romagna (60: Trenitalia Tper è un'azienda a parte) quasi scoperte;
  mancano es. Bergamo, Como, Varese, Ravenna. Nomi strani presenti
  nell'orario: "Venezia Mestre Binario 1 Giardino", "Firenze Binario S.Marco Vecchio".
- `bel_nome`: `ABBREVIAZIONI` per fine nome (`C.Le` → `Centrale`).
- `raggioStazione`: 2,2 px sotto zoom 7, 2,8 a 7, 3,5 da 8.

## Comuni e abitanti (dalla 0.5.0)
- `scanner/comuni.py`. Confini comunali: openpolis
  `geojson/limits_IT_municipalities.geojson` (≈36 MB, 7896 comuni, ISTAT
  1/1/2026, proprietà `name`, `com_istat_code`), scaricato una volta in cache.
- Popolazione: `https://demo.istat.it/data/posas/POSAS_{anno}_it_Comuni.zip`
  (≈4,5 MB). CSV con `;`, riga di titolo + intestazione, colonne codice,
  comune, età, maschi, femmine, totale; **la riga con età `999` è il totale**.
  Nel file alcune lettere accentate sono già rovinate (U+FFFD) e c'è una riga
  vuota finale. Si prova l'anno in corso, poi il precedente (404 = non ancora
  pubblicato: `scarica` non ritenta i 404, alza FileNotFoundError).
- **Sardegna 2026**: nuove province, 377 comuni con codici diversi tra confini
  (es. Alghero 112001) e popolazione (090003). `abbina_popolazione` li abbina
  per nome solo tra i codici rimasti spaiati. Risultato 27/10/2026: tutti i
  7896 comuni abbinati, 1701 stazioni italiane su 1701 con comune e abitanti.
- Stazione → comune: punto nel poligono (bbox + margine 0,02°), altrimenti
  il comune più vicino entro 1 km (costa).
- Sito: cursore `abitanti` = indice in `SOGLIE_ABITANTI` (0, 1k, 2k, 5k, 10k,
  20k, 50k, 100k, 250k, 500k). `stazioneVisibile()`: visibili se senza dato
  (estero), se partenza, o se abitanti ≥ soglia. Le nascoste: pallino rimosso
  dalla mappa, escluse da mete, conteggio e ricerca; restano nel calcolo
  (cambi possibili) con anello viola se servono.
- Stazioni visibili per soglia (27/10/2026): 5k → 1244, 20k → 648,
  100k → 239, 500k → 108.

## Frequenze dei diretti (dalla 0.6.0)
- Lo scanner tiene, per ogni corsa: `giorni` (bit k = circola nel k-esimo
  giorno tipo), `inizio` (minuti dalla mezzanotte alla prima fermata, anche
  > 1440) e `partenze` (minuti dopo l'inizio della PARTENZA da ogni fermata;
  `fermate` resta sugli arrivi per il calcolo).
- Per ogni treno di rete.json (= una sequenza di fermate, col tempo del più
  veloce): `profili` = liste distinte di partenze; `corse` = `[inizio,
  indice profilo, giorni]` ordinate per inizio; la stessa corsa in più giorni
  è una riga sola (bit uniti). `costruisci.orari_gruppo()`.
- Peso: rete.json 1,62 → 1,98 MB (gzip ≈140 → 240 KB).
- Sito: `direttiTratta(indice, A, B)` in percorsi.js raccoglie TUTTI i treni
  con A prima di B (qualsiasi sequenza: es. RV + SFM), orari di partenza da A
  per giorno tipo, sceglie il giorno con più corse. `SOGLIA_TRATTA_RARA = 6`:
  sotto, avviso ⚠ "Pochi treni". >12 orari: elenco a scomparsa (`<details>`).
- Verifica sul GTFS (27/10/2026): Torino PN → Racconigi 5 diretti in tutti e 4
  i mercoledì: 06:41 (SFM 26755), 07:20 (RV 3215), 17:55 (RV 3207),
  18:55 (RV 3107), 19:55 (RV 3109). C'è un test sul file reale.
- `inquadra()`: oltre a quando il percorso esce dalla vista, avvicina la mappa
  se lo zoom adatto al percorso supera quello attuale di ≥2 (max zoom 10).
  Motivo: sul telefono l'Italia intera è a zoom 5 e Torino–Racconigi non si vedeva.
- Prove: Edge headless con `--dump-dom` + pagina di prova che scrive in un
  `<pre>` valori letti con `iframe.contentWindow.eval("mappa")` (misure di
  zoom/dimensioni). Il `--screenshot` diretto di una finestra di 1440 px può
  mostrare la mappa più rimpicciolita (la finestra headless cambia misura dopo
  il caricamento): per foto affidabili usare sempre l'iframe a misura fissa.

## Trenord — indagine 0.7.0 (27/10/2026, prima del codice)
- Fonte: Regione Lombardia, dataset "Orario Ferroviario Regionale Gtfs"
  (id 3z4k-mxz9). Download dal PC OK (302 → 200, `trenord_gtfs.zip`, 1,66 MB):
  `https://www.dati.lombardia.it/download/3z4k-mxz9/application%2Fzip`.
- Licenza **CC-BY 4.0**, attribuzione "Trenord" (da
  `https://www.dati.lombardia.it/api/views/3z4k-mxz9.json`: `license`,
  `attribution`). Descrizione: "Servizio Trenord e Malpensa Express".
- Data di pubblicazione: nello zip `feed_info.txt` NON ha date né versione.
  Indicatori utili: `viewLastModified` dell'API (24/10/2026; la voce
  "Data ultima modifica" nei metadati), header `ETag` del download, data dei
  file nello zip (03/08/2026). Per riscaricare solo se cambia: confrontare
  l'ETag (o viewLastModified).
- File: agency, stops, routes, trips, stop_times, calendar_dates, feed_info.
  **Niente calendar.txt** (solo calendar_dates, exception_type 1) e **niente
  shapes.txt**. stops senza location_type né parent_station; `stop_id` tipo
  `S00023` (nessuno stop_code).
- Validità (calendar_dates): 26/07/2026 → 12/12/2026. Dei 4 mercoledì tipo
  coperti solo 04/11 e 25/11 (2891 corse ciascuno, di cui 2482 treni il
  04/11). **Scade col cambio orario del 13/12/2026.**
- routes: 63, `route_type` 2 = treno (60), 3 = bus (3: `TN_Bus` sostitutivi,
  e al 27/10 anche `R23` Domodossola–Arona–Gallarate–Milano e `RE_4`
  Domodossola–Milano, segnate come bus). Trip treno 6745 (bus 1725), 595
  sequenze di fermate distinte nell'intero file. Ci sono Malpensa Express
  (RE51, RE54), le linee ex Ferrovienord (S3, S4, R16 Asso, R17, R22, RE1
  Laveno, RE7, R27 Novara–Saronno, R3/RE3/S31/R9 Brescia–Iseo–Edolo) e TILO
  verso la Svizzera (S10, S30, S40, S50, RE80).
- Stazioni usate dai treni: 494.
  - Codice: `S` + 5 cifre ↔ Trenitalia `8300` + 5 cifre. 96 coincidenze, ma
    il codice NON basta: le svizzere collidono con stazioni italiane diverse
    (S05301 Lugano Paradiso ↔ Buttapietra 174 km, S05302 Melide, S05417
    Minusio) → accettare l'abbinamento per codice solo se distanza < 300 m.
    Buone per codice e < 300 m: 92 (quasi tutte già nella rete).
  - Nome + distanza < 300 m: 6 (Novara Nord↔Novara 106 m, Milano Porta
    Garibaldi Passante↔Milano Porta Garibaldi 68 m, Rovato Fn↔Rovato 122 m,
    Bellinzona, Lugano, Brescia S09999).
  - Da tabella manuale (stessa stazione, coordinate a ~1 km): Andora (991 m),
    Viareggio (987 m) — treni stagionali "del mare". Milano Repubblica ↔
    Milano Centrale (831 m) sono stazioni DIVERSE.
  - Nuove (> 1 km da ogni stazione Trenitalia): 393 (Lombardia 353, estero
    27, Emilia-Romagna 9, Piemonte 3, Liguria 1) + Milano Repubblica.
- Nessun numero treno in comune con le corse Trenitalia del 04/11: niente doppioni.

## Più fonti (dalla 0.7.0)
- `scanner/fonti.py`: `Fonte` (url, url_versione + leggi_versione per sapere se
  riscaricare, file in cache, categoria per riga di routes.txt, attribuzione,
  obbligatoria, prefisso_id, codice_base, codici_uic). `FONTI = [TRENITALIA,
  TRENORD]`, la prima è la principale (giorni tipo scelti sulla sua validità).
  Versione Trenitalia = `.last_publication_timestamp`; Trenord =
  `viewLastModified` dell'API dati.lombardia.it. Timbro in cache `<file>.data`.
- `prepara()`: se la versione non si legge o il download fallisce si usa la
  copia in cache con avviso "ATTENZIONE"; fonte non obbligatoria mai scaricata
  → avviso "i suoi treni MANCANO", la scansione continua; Trenitalia
  mancante → errore.
- `leggi()`: se nessun giorno tipo cade nella validità della fonte → SCADUTA:
  si usano i suoi ultimi mercoledì validi (`gtfs.scegli_giorni_finali`, bit
  mappati per indice sui giorni tipo), avviso evidente, `scaduta: true` in
  `meta.fonti`. Avviso anche se scade entro 30 giorni.
- `unisci()` + `scanner/abbina.py`: ordine tabella manuale
  (`scanner/abbinamenti_manuali.csv`, colonne fonte,id_fonte,nome_fonte,
  id_trenitalia,nome_trenitalia,nota) → codice (`8300`+cifre) entro 300 m →
  nome (uno inizio dell'altro, parola per parola) entro 300 m → nuova con id
  `TN-<stop_id>`. Le stazioni nuove hanno `uic = None`: regione solo dai
  poligoni, senza tolleranza costa (Chiasso, Stabio sono in Svizzera).
- gtfs.py generico: niente calendar.txt ok; `validita()` da feed_info o dai
  calendari; `leggi_corse(..., categoria_di_route, ..., operatore)`;
  numero treno = parte dopo " - " (Trenord: "RE_11 - 2153" → "2153").
- Trenord: categoria = linea ("S5", "RE4", "R23"; non specificata → "R"),
  route_type 3 escluso. Treni raggruppati per (operatore, sequenza).
- rete.json: `treni[].operatore`; `meta.fonti` = [{nome, validita_dal,
  validita_al, scaduta, attribuzione, treni}]; `meta.fonte` = tutte le
  attribuzioni. Sempre formato_versione 1.
- 27/10/2026: Trenitalia 10139 corse + Trenord 2482 → 2425 treni (343
  Trenord), 2103 stazioni (Lombardia 393). Stazioni Trenord dei giorni tipo:
  54 per codice, 5 per nome, 384 nuove (i due manuali, Andora e Viareggio,
  sono treni estivi assenti a novembre). rete.json 2,38 MB (gzip ≈285 KB).
  Scansione ~12 s. Calcolo da Milano con 3 cambi e 6 h ≈6 ms.
- Il primo download Trenord è fallito una volta con "WinError 5 Accesso
  negato" sul rename del `.part` (file appena copiato in cache, probabilmente
  antivirus): il nuovo tentativo dopo 5 s è riuscito.
- Sito: `fonteDi()`, `htmlFonti()` in app.js; operatore nella riga
  "prosegue"; avviso ⚠ per i treni di fonti scadute; pulsante "Sito Trenord"
  (https://www.trenord.it/) se il viaggio usa Trenord.

## Indagine prezzi (27/10/2026, solo report — nessun codice nell'app)
- `app.lefrecce.it/Channels.AppApi/...` (vecchia API dell'app) → 302 verso una
  pagina di cortesia: dismessa.
- API del sito Le Frecce, **risponde dal PC senza blocchi anti-bot** (richieste
  con User-Agent onesto "Dove_Arrivo-indagine", 1 ogni 2 s):
  - `GET https://www.lefrecce.it/Channels.Website.BFF.WEB/website/locations/search?name=<testo>&limit=5`
    → `[{id, name, displayName, multistation, centroidId}]`. **id = codice
    stazione del GTFS Trenitalia** (Torino Porta Nuova 830000219). Trova anche
    stazioni Trenord/FN (es. Milano Cadorna).
  - `POST .../website/ticket/solutions` con JSON `{departureLocationId,
    arrivalLocationId, departureTime:"AAAA-MM-GGTHH:MM:00.000", adults:1,
    children:0, criteria:{frecceOnly:false, regionalOnly:true,
    intercityOnly:false, tourismOnly:false, noChanges:false,
    order:"DEPARTURE_DATE", offset:0, limit:10}, advancedSearchRequest:{bestFare:false,
    bikeFilter:false, forwardDiscountCodes:[]}}` → `solutions[].solution`
    con `trains[]` (acronym, name), `nodes[]` (tratte, `bdoOrigin` "S00219"),
    `price.amount` = **prezzo del biglietto unico per tutto il viaggio**
    (2ª classe "ORDINARIA"), `status` "SALEABLE". Niente km nella risposta.
- Vende anche viaggi su treni Trenord (Milano Cadorna→Como Lago 5,40 €,
  Milano Centrale→Bergamo 6,30 €) e viaggi tra regioni.
- Il prezzo dipende dal percorso: stessa coppia, percorsi diversi → prezzi
  diversi (Torino→Racconigi 5,10 diretto / 6,50 altro giro; il 04/11 un giro
  via Milano per Asti 21,55 €).
- Piemonte, 25/11/2026, diretto, km misurati lungo shapes.txt Trenitalia:
  7,7 e 12,6 km → 2,80 · 24,5–29,6 → 4,40 · 31–33 → 4,70 · 37 → 5,10 ·
  50–54 → 6,50 · 61–63 → 7,10 · 82 (Vercelli) → 7,80 · 83–91 (Bardonecchia,
  Cuneo, Domodossola) → 8,60 · 86 (Alessandria) → 9,60 · 104 (Novara) → 10,70.
  Fasce coerenti, ma i km dallo shape sono imprecisi (punti ogni ~5 km:
  sottostima sulle linee di montagna; Alessandria e Bardonecchia invertite).
  Servirebbero i km tariffari ufficiali.
- Tra regioni il prezzo non segue la tabella piemontese: Torino→Milano 12,90,
  Torino→Genova 14,65, Alessandria→Genova 8,40 (68 km), Novara→Milano 6,30.
  (Il km Torino→Milano da shape è uscito 242: abbinamento al tracciato sbagliato.)
- Dati grezzi dell'indagine: nello scratchpad della sessione, non nel repo.

## Linee sui binari (dalla 0.8.0)
- Fonte: shapes.txt Trenitalia (3720 tracciati, ~44 punti l'uno, 1 punto
  ogni ~5 km, quasi sempre su stazioni; tutti i trip hanno shape_id).
  Trenord non ha shapes.txt → linee dritte.
- Scanner: `Corsa.forma` = shape_id; `gtfs.leggi_forme()`; `Letta.forme`
  `{(operatore, shape_id): punti}`; `costruisci.tracciati()` sul treno più
  veloce di ogni gruppo: per ogni coppia di fermate consecutive i punti tra
  le due (`punti_intermedi`), poi `togli_punte` (punto dove si va e si torna:
  vicini < 0,4 × andata). Tratto dubbio → [] = dritto, il resto del treno
  resta: fermata a > 0,5 km dal tracciato, oppure percorso > 1,8 × linea
  d'aria + 1 km (nel GTFS ci sono punti fuori posto: Firenze Campo Marte →
  S.M. Novella 2,4 km in linea d'aria e 48 km di tracciato, Roma Tiburtina
  → Termini, Jesi → Falconara). Con soglia 2,5 e scarto dell'intero treno
  si perdevano 196 treni su 2082.
- rete.json: `tracciati` = [[A, B, [[lat, lon], ...]]] con A < B (confronto
  di stringhe, uguale in Python e JS) e punti da A verso B, solo i tratti con
  punti intermedi; scritto una riga per tratto. `contenuto_uguale` li confronta.
- 27/10/2026: 1262 tratti, ~3000 punti; rete.json 2,38 → 2,48 MB (gzip 284 →
  304 KB). Nel browser: caricamento ≈0,4 s, scelta partenza + ricolore ≈7 ms.
- Sito: `indiceTracciati()` e `lineaFermate(ids, coordinate, tracciati)` in
  rete.js, usati per rete, percorso e prosecuzioni.
- La "V" ad Arezzo (Firenze→Arezzo + Arezzo→Foligno) è vera: la linea lenta
  dal Valdarno entra ad Arezzo da sud-ovest (Ponticino).

## Filtro aziende e ore (dalla 0.9.0)
- `ORE_MAX = 12` in app.js e `max="12"` del cursore in index.html (test).
  3 cambi e 12 h da Milano/Roma: ≈8–9 ms, ~1600–1850 mete.
- `stato.imp.spente` = aziende spente (in localStorage con le impostazioni,
  ripulito se un'azienda non c'è più; mai tutte spente). `applicaAziende()`
  ricostruisce `creaIndice(rete, ammesso)` (i treni esclusi non entrano
  nell'indice, gli indici t restano quelli di rete.treni), `stato.servite`
  (stazioni servite dalle aziende accese) e le linee della rete; se la
  partenza resta senza treni viene tolta. `visibileOra(s)` = servita +
  sopra soglia abitanti: usata da mappa, mete, conteggio, ricerca.
- Caselle generate da `meta.fonti` in `#imp-aziende` (nascosto se c'è una
  sola azienda); l'ultima accesa è disabilitata.
- Pagina di prova: con il file dati da 2,5 MB aspettare ~3,5 s dopo il load
  dell'iframe prima di simulare tocchi (con 1,5 s la ricerca/filtro partiva
  prima che la rete fosse caricata).

## Provenienza del treno (dalla 0.9.1)
- `provenienzaTratta(rete, tratta)` in percorsi.js = fermate prima di `da`.
  Scheda: "arriva da X (N fermate prima)" / "parte da qui" nella riga
  dell'operatore; mappa: linea a puntini (`dashArray "1 6"`, opacità 0,45)
  dalla prima fermata a quella in cui si sale.
- Attenzione: il treno mostrato è il più veloce della sua sequenza di fermate.
  Se un treno ha varianti (es. RV 2115 che nei giorni di lavori parte da Asti
  invece che da Torino) la provenienza è quella della variante usata.

## Percorsi alternativi (dalla 0.10.0)
- `percorsiAlternativi(rete, ammesso, origine, meta, rare, maxCambi, maxMinuti)`
  in percorsi.js: toglie TUTTI i treni che vanno direttamente da A a B per
  ogni tratta rara [A, B] (meno di `SOGLIA_TRATTA_RARA` diretti) e ricalcola;
  poi ripete vietando il cambio (`calcolaMete(..., cambiVietati)`) nelle
  stazioni di cambio trovate e in tutte le fermate prima della meta del loro
  ultimo treno (senza questo uscivano 3 varianti dello stesso SFM: via
  Carmagnola, Trofarello, Villastellone). Max 3 alternative, al massimo 30 min
  più lunghe della prima. `percorsoAlternativo` = la prima.
- Scelta di Davide (27/10/2026): alternative SENZA attese (strada 1); gli
  orari veri con attese sono rimandati alla futura modalità "real time".
- app.js: `tratteRare()`, `percorsoQuandoManca()` (cambi = max(cursore, n.
  treni del percorso), cioè fino a un cambio in più, max 3; stesse ore max;
  filtro aziende rispettato), `htmlTratte()` (righe delle tratte, usata da
  percorso e alternative), `htmlAlternativa()` (sezione "Negli altri orari":
  una `<details>` per alternativa, "Via X · tempo · cambi", la prima aperta;
  oppure "nessuna alternativa entro i limiti").
- Le alternative NON si disegnano da sole (richiesta di Davide: mappa troppo
  caotica): ogni riquadro ha il tasto "Mostra sulla mappa" (`data-alternativa`,
  `aria-pressed`); `stato.alternative` e `stato.altMostrate` (indici accesi),
  azzerati cambiando meta o chiudendo la scheda; `alternativeMostrate()`.
- Mappa: alternativa in `--alternativa` (#5fd4e8) disegnata SOPRA il
  percorso, più sottile (spesso corre sugli stessi binari: sotto non si
  vedeva); anelli dei suoi cambi azzurri; voce "altri orari" in legenda.
- Caso reale: Torino PN → Racconigi 27 min diretto (5/giorno); negli altri
  orari via Carmagnola 28 min (RV 22/giorno + SFM 21/giorno) o via
  Cavallermaggiore 36 min. Con gli orari veri via Cavallermaggiore è ~25 min
  più veloce (attese 16 vs 48 min). Test su entrambe.

## Calcolo e interfaccia (dalla 0.3.0)
- `docs/percorsi.js` (funzioni pure, testate in Node): `creaIndice`,
  `calcolaMete(indice, origine, maxCambi, maxMinuti)` a giri come da
  specifica, `fermateTratta`, `restoTratta`, `minutiTratta`, `fascia`
  (<60 verde, 60–120 giallo, >120 rosso), `formattaDurata`.
- **Soglia cambi** `SOGLIA_CAMBIO_MINUTI = 15` (introdotta a 10 il 26/10/2026,
  portata a 15 da Davide lo stesso giorno): tra i percorsi trovati per una meta (uno per
  numero di treni, sempre più veloci) se ne sceglie uno con più cambi solo se
  risparmia ≥15 min per ogni cambio in più. Motivo: senza, Torino PN→Asti
  usciva "34 min, cambio a Lingotto" invece del diretto da 35. L'esplorazione
  resta sul tempo minimo puro; i minuti mostrati sono quelli veri.
- `cercaStazioni` / `normalizzaNome` in `rete.js` (accenti e punteggiatura ignorati).
- `app.js`: stato in un oggetto `stato` (const, quindi NON è `window.stato`:
  nelle pagine di prova usare `iframe.contentWindow.eval("stato")`).
  Livelli Leaflet: pane `linee` (410) < `percorso` (420) < `stazioni` (430),
  ognuno con il suo renderer canvas.
- Scheda della meta: in basso su telefono, a destra da 760 px. `inquadra()`
  sposta la mappa solo se il percorso esce dall'area non coperta dalla scheda.
- Cambi (0.3.1): `stazioniCambio()` in percorsi.js; anelli viola (`--cambio`)
  disegnati nel pane `stazioni` con lo stesso renderer dei pallini (sopra di
  loro, non interattivi), voce "cambio" in legenda visibile solo se servono.
  Prosecuzione tratteggiata e testo "prosegue per… / termina qui" per ogni tratta.
- "Verifica prezzo": apre https://www.lefrecce.it/Channels.Website.WEB/ e la
  scheda dice cosa cercare (nessun link precompilato possibile).
- Memoria locale (`localStorage`, chiave `dove_arrivo_stato`, sempre in
  try/catch): impostazioni + partenza/cambi/ore se "Ricorda" è attivo.
- Prove visive: pagina `prova.html` con iframe in una copia di docs/ nello
  scratchpad; parametri `s=partenza|meta|cambio|irraggiungibile|ricerca`,
  `a=<nome meta>`, `cambi`, `ore`, `w`, `h`. Nei comandi bash usare percorsi
  `cygpath -m` (con `/`): con `\$1` il nome file non si espande.
