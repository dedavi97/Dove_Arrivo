# Backlog

## Tappe
- [x] 0.0.1 Setup repo + verifica fonti dati e link Trenitalia
- [x] 0.1.0 Scanner Piemonte → `rete.json` + `Aggiorna_Dati.bat`
- [x] 0.2.0 Sito: mappa con stazioni e linee, data aggiornamento, footer (+ `Avvia_Locale.bat`)
- [x] 0.3.0 Partenza, cursori, calcolo percorsi, pannello meta, Verifica prezzo
- [x] 0.4.0 Estensione a tutta Italia (solo Trenitalia)
- [x] 0.5.0 Filtro stazioni per abitanti del comune (cursore, le altre spariscono)
- [x] 0.6.0 Frequenza dei treni diretti nella scheda (N al giorno + orari, avviso tratte rare)
- [ ] 0.7.0 Trenord (GTFS Regione Lombardia): prima indagine e report a Davide, poi codice
- [ ] Indagine prezzi (solo report, nessun codice nell'app)
- [ ] 0.8.0 Linee che passano per le stazioni intermedie (shapes.txt)
- [ ] Cursore "Ore max" fino a 12 ore (oggi arriva a 6).

## In attesa
- Niente al momento.

## Idee per dopo
- Filtro fascia oraria ("parto tra le 9 e le 12"): calcolo solo con i treni in
  quella fascia. Cambia la regola sugli orari: da decidere.
- Prezzi e filtro "Max €": dopo l'indagine prezzi (solo prezzo totale del
  biglietto unico; filtro/colori solo se il sistema è affidabile).
- Alleggerire l'interfaccia.
- Trenitalia Tper (Emilia-Romagna): Davide sta indagando sulle fonti.
- Numero di versione nei nomi dei file del sito (es. `app.js?v=0.6.0`), così
  dopo un aggiornamento il browser non mescola pezzi vecchi e nuovi.
- Altri operatori regionali non presenti nell'orario Trenitalia: priorità
  Trenord (Lombardia) e Trenitalia Tper (Emilia-Romagna), poi ferrovie locali
  (GTT, FNM, Circumvesuviana, FSE, ARST…). Capire quanto ha senso spingersi
  e se pubblicano un GTFS aperto.
- Frecce / Intercity: sono già nell'orario Trenitalia, possibile opzione futura.
- Autobus sostitutivi Trenitalia (es. Ivrea–Aosta chiusa per lavori): oggi esclusi.
- "Verifica prezzo": nessun link precompilato possibile; aprire la ricerca
  Trenitalia mostrando partenza/arrivo da copiare.
