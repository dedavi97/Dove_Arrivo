// Calcolo delle mete raggiungibili, a "giri".
// Giro 1 = stazioni raggiungibili con un solo treno; giro k = da ogni stazione
// migliorata al giro k-1 si prende un altro treno. Giri massimi = cambi + 1.
// Si va solo avanti lungo le fermate di un treno; il tempo è la somma dei
// minuti passati sui treni (attese ai cambi escluse).

// ammesso(treno) permette di escludere dei treni (es. le aziende spente nelle impostazioni):
// gli esclusi non entrano nell'indice, ma gli indici t restano quelli di rete.treni.
function creaIndice(rete, ammesso = () => true) {
  const passaggi = new Map(); // id stazione -> [{ t: indice treno, i: indice fermata }]
  rete.treni.forEach((treno, t) => {
    if (!ammesso(treno)) return;
    treno.fermate.forEach((f, i) => {
      if (!passaggi.has(f.stazione)) passaggi.set(f.stazione, []);
      passaggi.get(f.stazione).push({ t, i });
    });
  });
  return { rete, passaggi };
}

// Un percorso con un cambio in più si preferisce solo se fa risparmiare almeno
// questi minuti per ogni cambio aggiunto (es. Torino-Asti: niente cambio a
// Lingotto per guadagnare 1 minuto sul diretto). Il tempo mostrato resta quello vero.
const SOGLIA_CAMBIO_MINUTI = 15; // valore scelto da Davide il 26/10/2026

// Restituisce Map id stazione -> { minuti, tratte: [{ treno, da, a }] } (origine esclusa).
// treno = indice in rete.treni, da/a = indici delle fermate di quel treno.
function calcolaMete(indice, origine, maxCambi, maxMinuti) {
  const { rete, passaggi } = indice;
  // migliori: per ogni stazione il tempo minimo trovato finora (guida l'esplorazione);
  // candidati: tutte le etichette migliorate, giro per giro (una per numero di treni).
  const migliori = new Map([[origine, { minuti: 0, tratte: [] }]]);
  const candidati = new Map();
  let frontiera = [origine];

  for (let giro = 1; giro <= maxCambi + 1 && frontiera.length; giro++) {
    // Si parte dalle etichette del giro precedente: un treno in più per giro.
    const partenze = frontiera.map((s) => [s, migliori.get(s)]);
    const nuovi = new Map();
    for (const [stazione, base] of partenze) {
      const ultima = base.tratte[base.tratte.length - 1];
      for (const { t, i } of passaggi.get(stazione) || []) {
        if (ultima && ultima.treno === t) continue; // restare sullo stesso treno non è un cambio
        const fermate = rete.treni[t].fermate;
        for (let j = i + 1; j < fermate.length; j++) {
          const minuti = base.minuti + fermate[j].minuti_dalla_partenza - fermate[i].minuti_dalla_partenza;
          if (minuti > maxMinuti) break;
          const arrivo = fermate[j].stazione;
          const attuale = nuovi.get(arrivo) || migliori.get(arrivo);
          if (attuale && attuale.minuti <= minuti) continue;
          nuovi.set(arrivo, { minuti, tratte: [...base.tratte, { treno: t, da: i, a: j }] });
        }
      }
    }
    for (const [s, etichetta] of nuovi) {
      migliori.set(s, etichetta);
      if (!candidati.has(s)) candidati.set(s, []);
      candidati.get(s).push(etichetta);
    }
    frontiera = [...nuovi.keys()];
  }

  const mete = new Map();
  for (const [s, lista] of candidati) {
    let scelta = lista[0]; // meno treni; le successive sono via via più veloci
    for (const etichetta of lista.slice(1)) {
      const cambiInPiu = etichetta.tratte.length - scelta.tratte.length;
      if (scelta.minuti - etichetta.minuti >= SOGLIA_CAMBIO_MINUTI * cambiInPiu) scelta = etichetta;
    }
    mete.set(s, scelta);
  }
  return mete;
}

// Fermate dell'ultimo treno usato dopo la meta (id stazione), per la "prosecuzione".
function restoTratta(rete, tratta) {
  return rete.treni[tratta.treno].fermate.slice(tratta.a + 1).map((f) => f.stazione);
}

// Fermate del treno prima di quella in cui si sale (id stazione), per la "provenienza".
function provenienzaTratta(rete, tratta) {
  return rete.treni[tratta.treno].fermate.slice(0, tratta.da).map((f) => f.stazione);
}

// Fermate percorse in una tratta, meta inclusa (id stazione).
function fermateTratta(rete, tratta) {
  return rete.treni[tratta.treno].fermate.slice(tratta.da, tratta.a + 1).map((f) => f.stazione);
}

// Stazioni dove si cambia treno (id), in ordine di viaggio.
function stazioniCambio(rete, etichetta) {
  return etichetta.tratte.slice(1).map((t) => rete.treni[t.treno].fermate[t.da].stazione);
}

function minutiTratta(rete, tratta) {
  const f = rete.treni[tratta.treno].fermate;
  return f[tratta.a].minuti_dalla_partenza - f[tratta.da].minuti_dalla_partenza;
}

// Una tratta con meno di queste corse dirette al giorno è "rara": la scheda avvisa.
const SOGLIA_TRATTA_RARA = 6;

// Tutti i treni che vanno da A a B senza cambi, qualunque sia la loro sequenza di
// fermate (es. RV + SFM). Per ogni giorno tipo si raccolgono gli orari di partenza
// da A e si sceglie il giorno con più corse, così i lavori di un giorno non falsano.
// Restituisce { giorno: indice in meta.giorni_tipo, orari: [minuti dalla mezzanotte] }
// oppure null se il file dati non ha gli orari (versioni precedenti alla 0.6.0).
function direttiTratta(indice, a, b) {
  const { rete, passaggi } = indice;
  const nGiorni = ((rete.meta && rete.meta.giorni_tipo) || []).length;
  if (!nGiorni) return null;
  const perGiorno = Array.from({ length: nGiorni }, () => new Set());
  let conOrari = false;
  for (const { t, i } of passaggi.get(a) || []) {
    const treno = rete.treni[t];
    if (!treno.corse) continue;
    conOrari = true;
    if (!treno.fermate.some((f, k) => k > i && f.stazione === b)) continue;
    for (const [inizio, profilo, giorni] of treno.corse) {
      const partenza = inizio + treno.profili[profilo][i];
      for (let g = 0; g < nGiorni; g++) if (giorni & (1 << g)) perGiorno[g].add(partenza);
    }
  }
  if (!conOrari) return null;
  let giorno = 0;
  perGiorno.forEach((orari, g) => {
    if (orari.size > perGiorno[giorno].size) giorno = g;
  });
  return { giorno, orari: [...perGiorno[giorno]].sort((x, y) => x - y) };
}

// Percorso alternativo per le ore in cui le tratte dirette "rare" (meno di
// SOGLIA_TRATTA_RARA corse) non ci sono: si tolgono tutti i treni che vanno direttamente
// da A a B per ogni tratta rara [A, B] e si ricalcola. ammesso(treno) = filtro aziende.
// Restituisce l'etichetta { minuti, tratte } come calcolaMete, o null.
function percorsoAlternativo(rete, ammesso, origine, meta, rare, maxCambi, maxMinuti) {
  const base = creaIndice(rete, ammesso);
  const esclusi = new Set();
  for (const [a, b] of rare) {
    for (const { t, i } of base.passaggi.get(a) || []) {
      if (rete.treni[t].fermate.some((f, k) => k > i && f.stazione === b)) esclusi.add(rete.treni[t]);
    }
  }
  const indice = creaIndice(rete, (treno) => ammesso(treno) && !esclusi.has(treno));
  return calcolaMete(indice, origine, maxCambi, maxMinuti).get(meta) || null;
}

// 401 -> "06:41"; le corse dopo mezzanotte (es. 1450) tornano a "00:10"
function formattaOrario(minuti) {
  const m = ((minuti % 1440) + 1440) % 1440;
  return `${String(Math.floor(m / 60)).padStart(2, "0")}:${String(m % 60).padStart(2, "0")}`;
}

// <1h verde, 1-2h giallo, >2h rosso
function fascia(minuti) {
  return minuti < 60 ? "verde" : minuti <= 120 ? "giallo" : "rosso";
}

function formattaDurata(minuti) {
  if (minuti < 60) return `${minuti} min`;
  const ore = Math.floor(minuti / 60);
  const resto = minuti % 60;
  return resto ? `${ore} h ${String(resto).padStart(2, "0")}` : `${ore} h`;
}

if (typeof module !== "undefined") {
  module.exports = {
    SOGLIA_CAMBIO_MINUTI, SOGLIA_TRATTA_RARA, creaIndice, calcolaMete, restoTratta, provenienzaTratta, fermateTratta, stazioniCambio,
    minutiTratta, direttiTratta, percorsoAlternativo, formattaOrario, fascia, formattaDurata,
  };
}
