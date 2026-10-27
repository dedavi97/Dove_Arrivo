# Stato del progetto

**Versione:** 0.6.0 — 27/10/2026
**Ultima funzione:** frequenza dei treni diretti nella scheda
**Prossimo passo:** 0.7.0 Trenord — prima indagine e report a Davide

## Cosa funziona
- **Sito** (https://dedavi97.github.io/Dove_Arrivo/): tutta Italia, 1714
  stazioni e 2082 treni regionali Trenitalia. Scegli la partenza toccando
  una stazione o cercandola per nome (con la regione accanto); cursori per
  cambi massimi (0–3), ore massime (30 min – 6 h) e abitanti minimi del
  comune (le stazioni sotto soglia spariscono). Mete colorate per tempo
  (verde, giallo, rosso), le altre spente; legenda sempre visibile.
- Toccando una meta: comune e abitanti, treni, cambi, tempo totale, dove
  prosegue ogni treno, quanti diretti ci sono al giorno su ogni tratta e a
  che ora (avviso ⚠ se sono meno di 6); percorso evidenziato, prosecuzioni tratteggiate, cambi
  segnati con un anello viola; "Verifica prezzo" apre Trenitalia, "Parti da qui".
- Impostazioni (ricorda partenza e limiti, mostra linee), Aiuto, Informazioni.
- Provato in formato telefono e computer.
- File dati: 2,0 MB (circa 240 KB scaricati, compressi).
- `Aggiorna_Dati.bat` aggiorna i dati in ~8 secondi (la prima volta scarica
  anche i confini dei comuni, ~36 MB).

## Regole del calcolo
- Un percorso con un cambio in più viene proposto solo se fa risparmiare
  almeno 15 minuti per cambio (decisione di Davide).

## Da sapere
- Solo treni Trenitalia: Lombardia (Trenord) ed Emilia-Romagna (Trenitalia
  Tper) sono quasi scoperte, mancano le ferrovie locali.
- La Valle d'Aosta non compare (Ivrea–Aosta servita solo da autobus).
