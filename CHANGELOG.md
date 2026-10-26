# Changelog

Le versioni sono in ordine dalla più recente. I soli aggiornamenti dei dati
(`data: aggiornamento rete GG/MM/AAAA`) non compaiono qui.

## 0.3.0 — 26/10/2026
- Scegli la stazione di partenza toccandola sulla mappa o cercandola per nome.
- Cursori per i cambi massimi (0–3) e le ore massime di viaggio (da 30 min a 6 h).
- Le mete si colorano per tempo di viaggio: verde sotto 1 ora, giallo 1–2 ore,
  rosso oltre 2 ore; spente quelle non raggiungibili. Legenda sempre visibile.
- Tocca una meta: treni da prendere, dove cambiare, tempo totale, fin dove
  prosegue l'ultimo treno; percorso evidenziato sulla mappa, prosecuzione
  tratteggiata. Pulsante "Verifica prezzo" verso Trenitalia e "Parti da qui".
- Un percorso con un cambio in più viene proposto solo se fa risparmiare
  almeno 10 minuti per cambio.
- Impostazioni: ricordare partenza e limiti, mostrare o nascondere le linee.

## 0.2.1 — 26/10/2026
- I dati ora uniscono gli orari di 4 mercoledì distribuiti su due mesi e
  mezzo, invece di uno solo: una linea chiusa per lavori in un giorno non
  sparisce più dalla mappa. Tornate la Torino–Asti e la Cuneo–Limone.
- Rete: 237 treni, 328 stazioni.

## 0.2.0 — 26/10/2026
- Il sito: mappa scura con tutte le stazioni e le linee dei treni regionali.
  Tocca una stazione per leggerne il nome.
- In alto la data dei dati, in basso la versione con Aiuto e Informazioni
  (fonti dei dati ed elenco delle novità).
- Messaggi chiari se i dati mancano o non sono leggibili.
- `Avvia_Locale.bat` apre il sito sul computer.

## 0.1.0 — 26/10/2026
- Nuovo programma di aggiornamento dati (`Aggiorna_Dati.bat`): scarica
  l'orario ufficiale Trenitalia, costruisce la rete dei treni regionali del
  Piemonte (con i treni che escono dalla regione fino al capolinea), mostra
  avanzamento, riepilogo, segnalazioni e differenze con la volta precedente,
  poi chiede se pubblicare.
- Primo file dati: 214 treni regionali (REG, RV, SFM), 317 stazioni.

## 0.0.1 — 26/10/2026
- Creazione del progetto: cartelle, documentazione, costante di versione.
- Verifica delle fonti dati: ViaggiaTreno blocca i programmi automatici;
  trovata come alternativa l'orario ufficiale Trenitalia in formato aperto.
