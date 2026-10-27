# Changelog

Le versioni sono in ordine dalla più recente. I soli aggiornamenti dei dati
(`data: aggiornamento rete GG/MM/AAAA`) non compaiono qui.

## 0.8.0 — 27/10/2026
- Le linee sulla mappa seguono i binari: tra due fermate passano per le
  stazioni dove il treno non si ferma (tracciato dell'orario Trenitalia),
  invece di andare dritte. Vale per la rete, per il percorso evidenziato e
  per le prosecuzioni tratteggiate.
- I pezzi di tracciato con punti fuori posto restano dritti.
- Le linee Trenord restano dritte: il loro orario non ha il tracciato.

## 0.7.0 — 27/10/2026
- Arrivano i treni **Trenord**: Lombardia, Malpensa Express, linee ex
  Ferrovienord e linee verso la Svizzera. 343 treni e 384 stazioni nuove
  (la Lombardia passa da 43 a 393 stazioni).
- Le stazioni servite da entrambe le aziende sono un solo pallino e ci si
  può cambiare (es. Milano Centrale, Brescia, Novara e Novara Nord).
- Nella scheda di ogni treno c'è scritto chi lo gestisce; se il viaggio usa
  un treno Trenord compare anche il pulsante "Sito Trenord".
- In "Informazioni" le fonti con le date di validità dei loro orari. Se
  l'orario di un'azienda scade, i suoi treni restano con i dati vecchi e la
  scheda lo segnala.
- L'orario Trenord attuale vale fino al 12/12/2026.

## 0.6.0 — 27/10/2026
- Per ogni treno del percorso la scheda dice quanti treni diretti ci sono al
  giorno su quella tratta e a che ora partono (contando tutti i treni che
  vanno da A a B senza cambi, non solo quello più veloce). Si usa il
  mercoledì tipo con più corse, così i lavori di un giorno non falsano.
- Tratte con meno di 6 diretti al giorno: avviso ⚠ "Pochi treni: controlla
  l'orario". Esempio: Torino Porta Nuova → Racconigi, solo 5 diretti
  (06:41, 07:20, 17:55, 18:55, 19:55).
- Toccando una meta vicina la mappa si avvicina al percorso, che prima a
  scala nazionale non si distingueva.
- Il calcolo dei percorsi non cambia.

## 0.5.0 — 27/10/2026
- Nuovo cursore "Abitanti min": mostra solo le stazioni dei comuni sopra la
  soglia scelta (da tutti fino a 500.000 abitanti); le altre spariscono dalla
  mappa, dalle mete e dalla ricerca. I treni ci passano comunque e ci si può
  cambiare: in quel caso l'anello viola resta visibile.
- La scheda di una meta indica comune e abitanti.
- Dati: comune e abitanti di ogni stazione italiana (ISTAT, popolazione al
  1° gennaio 2026).

## 0.4.0 — 27/10/2026
- Tutta Italia: 2082 treni regionali Trenitalia e 1714 stazioni (prima solo
  il Piemonte). Il calcolo resta istantaneo anche con 3 cambi e 6 ore.
- La ricerca mostra la regione accanto a ogni stazione.
- Pallini più piccoli quando si guarda tutta Italia; vista iniziale
  sull'Italia senza le stazioni estere a fine linea.
- "Bologna C.Le" diventa "Bologna Centrale".
- Nell'Aiuto: quali treni mancano (Trenord, Trenitalia Tper, ferrovie locali).

## 0.3.1 — 26/10/2026
- Per ogni treno del percorso, non solo l'ultimo, la scheda dice dove
  prosegue (o se termina) e la mappa ne mostra la prosecuzione tratteggiata.
- Le stazioni di cambio sono segnate sulla mappa con un anello viola, anche
  in legenda.
- Un percorso con un cambio in più ora viene proposto solo se fa risparmiare
  almeno 15 minuti per cambio (prima 10).

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
