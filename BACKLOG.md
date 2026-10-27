# Backlog

## Tappe
- [x] 0.0.1 Setup repo + verifica fonti dati e link Trenitalia
- [x] 0.1.0 Scanner Piemonte → `rete.json` + `Aggiorna_Dati.bat`
- [x] 0.2.0 Sito: mappa con stazioni e linee, data aggiornamento, footer (+ `Avvia_Locale.bat`)
- [x] 0.3.0 Partenza, cursori, calcolo percorsi, pannello meta, Verifica prezzo
- [x] 0.4.0 Estensione a tutta Italia (solo Trenitalia)
- [x] 0.5.0 Filtro stazioni per abitanti del comune (cursore, le altre spariscono)
- [x] 0.6.0 Frequenza dei treni diretti nella scheda (N al giorno + orari, avviso tratte rare)
- [x] 0.7.0 Trenord (GTFS Regione Lombardia): scanner a più fonti, stazioni unite, fonte scaduta
- [x] Indagine prezzi (solo report, nessun codice nell'app) — vedi CLAUDE.md
- [ ] Pulsante "Prezzo" nella scheda: chiede a Le Frecce il prezzo vero del
  biglietto unico per partenza e meta scelte (richiesta di Davide 27/10/2026).
  Ostacolo: Le Frecce non permette chiamate dal browser di altri siti (niente
  CORS). Strade da decidere con Davide: (1) piccolo "ponte" gratuito online
  (es. Cloudflare Workers) = un pezzo di server, da creare sul suo account;
  (2) solo in locale, con Avvia_Locale.bat che fa da ponte sul suo PC.
- [x] 0.8.0 Linee che passano per le stazioni intermedie (shapes.txt)
- [x] 0.8.1 Versione nei nomi dei file del sito + server locale senza cache
- [x] 0.9.0 Cursore "Ore max" fino a 12 ore
- [x] 0.9.0 Impostazioni: scegliere quali aziende mostrare e usare nel calcolo
- [x] 0.9.1 Provenienza del treno (scheda + linea a puntini sulla mappa)
- [x] 0.10.0 Percorsi alternativi quando il diretto ha poche corse ("Negli altri orari")
- [ ] Modalità "real time" (scelta di Davide 27/10/2026, per il futuro): per la meta
  scelta, tutte le soluzioni reali della giornata con orari di partenza e arrivo
  e attese ai cambi, calcolate dagli orari delle corse già in rete.json. Si
  potrebbe partire da un orario futuro scelto dall'utente. Motivo: senza attese
  Torino→Racconigi sembra meglio via Carmagnola (28 min di treno), ma con gli
  orari veri vince via Cavallermaggiore (arrivo :56, SFM :12 → 16 min di
  attesa contro 48 a Carmagnola). La mappa resterebbe senza attese.

## In attesa
- Niente al momento.

## Idee per dopo
- Filtro fascia oraria ("parto tra le 9 e le 12"): calcolo solo con i treni in
  quella fascia. Cambia la regola sugli orari: da decidere.
- Prezzi e filtro "Max €": dopo l'indagine prezzi (solo prezzo totale del
  biglietto unico; filtro/colori solo se il sistema è affidabile).
- Alleggerire l'interfaccia.
- Trenitalia Tper (Emilia-Romagna): Davide sta indagando sulle fonti.
- Altri operatori regionali: Trenitalia Tper (Emilia-Romagna, Davide sta
  indagando), poi ferrovie locali (GTT, Circumvesuviana, FSE, ARST…). Con lo
  scanner a più fonti basta aggiungere una `Fonte` in scanner/fonti.py.
- Dopo il 13/12/2026: scaricare il nuovo orario Trenord appena la Regione lo
  pubblica (fino ad allora l'app usa i dati vecchi e lo segnala).
- Frecce / Intercity: sono già nell'orario Trenitalia, possibile opzione futura.
- Autobus sostitutivi Trenitalia (es. Ivrea–Aosta chiusa per lavori): oggi esclusi.
- "Verifica prezzo": nessun link precompilato possibile; aprire la ricerca
  Trenitalia mostrando partenza/arrivo da copiare.
