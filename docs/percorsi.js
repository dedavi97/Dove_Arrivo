// Calcolo delle mete raggiungibili, a "giri".
// Giro 1 = stazioni raggiungibili con un solo treno; giro k = da ogni stazione
// migliorata al giro k-1 si prende un altro treno. Giri massimi = cambi + 1.
// Si va solo avanti lungo le fermate di un treno; il tempo è la somma dei
// minuti passati sui treni (attese ai cambi escluse).

function creaIndice(rete) {
  const passaggi = new Map(); // id stazione -> [{ t: indice treno, i: indice fermata }]
  rete.treni.forEach((treno, t) => {
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
const SOGLIA_CAMBIO_MINUTI = 10;

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

// Fermate percorse in una tratta, meta inclusa (id stazione).
function fermateTratta(rete, tratta) {
  return rete.treni[tratta.treno].fermate.slice(tratta.da, tratta.a + 1).map((f) => f.stazione);
}

function minutiTratta(rete, tratta) {
  const f = rete.treni[tratta.treno].fermate;
  return f[tratta.a].minuti_dalla_partenza - f[tratta.da].minuti_dalla_partenza;
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
  module.exports = { SOGLIA_CAMBIO_MINUTI, creaIndice, calcolaMete, restoTratta, fermateTratta, minutiTratta, fascia, formattaDurata };
}
