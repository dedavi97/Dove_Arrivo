# Stato del progetto

**Versione:** 0.2.1 — 26/10/2026
**Tappa conclusa:** 0.2.1 (correzione: più giorni tipo)
**Prossima tappa:** 0.3.0 — partenza, cursori, calcolo delle mete

## Cosa funziona
- **Sito:** mappa scura con le 328 stazioni e le linee dei treni regionali
  (segmenti dritti tra fermate consecutive). Le stazioni fuori dal Piemonte
  sono un po' più spente. Toccando una stazione se ne legge il nome.
  In alto "Dati al GG/MM/AAAA", in basso versione, Aiuto e Informazioni
  (fonti dei dati e novità). Messaggi chiari se i dati mancano.
  Provato in formato computer e telefono.
- `Avvia_Locale.bat` apre il sito sul computer.
- `Aggiorna_Dati.bat` aggiorna i dati in ~5 secondi e chiede se pubblicare.
  Usa gli orari di 4 mercoledì, così i lavori su una linea in un giorno
  non la fanno sparire.

## Da sapere
- Sfondo mappa: OpenStreetMap scurito (CARTO ora chiede una chiave a pagamento).
- La Valle d'Aosta non compare: la Ivrea–Aosta è servita solo da autobus
  sostitutivi in tutti e 4 i giorni considerati.
- Mancano gli altri operatori (es. Trenord).
- Sito pubblico: https://dedavi97.github.io/Dove_Arrivo/ (si aggiorna a ogni push).
