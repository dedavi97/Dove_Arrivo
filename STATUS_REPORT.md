# Stato del progetto

**Versione:** 0.1.0 — 26/10/2026
**Tappa conclusa:** 0.1.0 (programma di aggiornamento dati)
**Prossima tappa:** 0.2.0 — il sito con la mappa

## Cosa funziona
- `Aggiorna_Dati.bat` scarica l'orario ufficiale Trenitalia (solo se ce n'è
  uno nuovo), costruisce la rete e mostra un riepilogo con le differenze
  rispetto alla volta precedente. Poi chiede "Pubblico? S/N".
- Ci mette circa 5 secondi. Si può interrompere in qualsiasi momento: il
  file dati resta com'era e al giro dopo non si riscarica nulla.
- Rete attuale: 214 treni regionali, 317 stazioni (212 in Piemonte, 72 in
  Liguria, 27 in Lombardia, 6 in Francia sulla Cuneo–Ventimiglia).
  Giorno tipo: mercoledì 04/11/2026.

## Da sapere
- La Valle d'Aosta non compare: la Ivrea–Aosta in questo periodo è servita
  solo da autobus sostitutivi (linea chiusa per lavori).
- Mancano gli altri operatori (es. Trenord), come già noto.
- Pubblicazione: non ancora possibile, il repo su GitHub non esiste ancora.
