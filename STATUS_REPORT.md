# Stato del progetto

**Versione:** 0.9.0 — 27/10/2026
**Ultima tappa:** linee che seguono i binari
**Prossimo passo:** da scegliere con Davide nel backlog (provenienza del treno, percorsi alternativi, pulsante prezzo)

## Cosa funziona
- **Sito** (https://dedavi97.github.io/Dove_Arrivo/): tutta Italia, 2103
  stazioni e 2425 treni regionali (Trenitalia 2082, Trenord 343). Scegli la
  partenza toccando una stazione o cercandola per nome; cursori per cambi
  (0–3), ore (30 min – 12 h) e abitanti minimi del comune. Mete colorate per
  tempo, legenda sempre visibile.
- Toccando una meta: comune e abitanti, treni con il loro operatore, cambi,
  tempo totale, dove prosegue ogni treno, quanti diretti al giorno su ogni
  tratta e a che ora (⚠ se meno di 6); percorso evidenziato, cambi con anello
  viola; "Verifica prezzo" (Trenitalia), "Sito Trenord" se serve, "Parti da qui".
- Impostazioni (anche quali aziende usare), Aiuto, Informazioni (fonti con le date di validità).
- `Aggiorna_Dati.bat` aggiorna i dati da entrambe le aziende in ~12 secondi;
  il riepilogo è diviso per fonte e segnala orari scaduti o in scadenza.
- Le linee seguono i binari (tracciato Trenitalia); quelle Trenord sono dritte.
- File dati: 2,5 MB (circa 305 KB scaricati, compressi).

## Regole del calcolo
- Un percorso con un cambio in più viene proposto solo se fa risparmiare
  almeno 15 minuti per cambio (decisione di Davide).

## Da sapere
- **L'orario Trenord scade il 12/12/2026** (cambio orario del 13/12). Dopo,
  finché la Regione non pubblica il nuovo, il sito usa i dati vecchi e lo dice.
- Mancano Trenitalia Tper (Emilia-Romagna) e le ferrovie locali.
- Le linee Domodossola–Milano di Trenord (R23, RE4) oggi risultano autobus:
  non compaiono.
- La Valle d'Aosta non compare (Ivrea–Aosta servita solo da autobus).
