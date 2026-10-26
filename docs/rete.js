// Unico punto del codice JS che legge rete.json.
// Formato sconosciuto o versione diversa: messaggio chiaro, nessuna conversione.

const RETE_TIPO = "Dove_Arrivo_Rete";
const RETE_FORMATO_VERSIONE = 1;

class ErroreRete extends Error {
  constructor(titolo, dettaglio) {
    super(`${titolo}: ${dettaglio}`);
    this.titolo = titolo;
    this.dettaglio = dettaglio;
  }
}

function validaRete(dati) {
  const meta = dati && typeof dati === "object" ? dati.meta : null;
  if (!meta || meta.tipo !== RETE_TIPO) {
    throw new ErroreRete("File dati non riconosciuto", "il file non è un file dati di Dove_Arrivo.");
  }
  if (meta.formato_versione !== RETE_FORMATO_VERSIONE) {
    throw new ErroreRete(
      "Versione del file dati diversa",
      `il file è in formato ${meta.formato_versione}, questo sito legge solo il formato ${RETE_FORMATO_VERSIONE}. ` +
        "Aggiorna il sito o rigenera i dati con Aggiorna_Dati.bat."
    );
  }
  if (!Array.isArray(dati.stazioni) || !Array.isArray(dati.treni)) {
    throw new ErroreRete("File dati incompleto", "mancano le stazioni o i treni.");
  }
  return dati;
}

async function caricaRete(url) {
  let risposta;
  try {
    risposta = await fetch(url, { cache: "no-cache" });
  } catch (e) {
    throw new ErroreRete("Dati non raggiungibili", "controlla la connessione e ricarica la pagina.");
  }
  if (risposta.status === 404) {
    throw new ErroreRete("Nessun dato", "il file della rete non c'è ancora. Lancia Aggiorna_Dati.bat per crearlo.");
  }
  if (!risposta.ok) {
    throw new ErroreRete("Dati non raggiungibili", `il server ha risposto ${risposta.status}. Riprova più tardi.`);
  }
  let dati;
  try {
    dati = await risposta.json();
  } catch (e) {
    throw new ErroreRete("File dati danneggiato", "il file della rete non è leggibile. Rigeneralo con Aggiorna_Dati.bat.");
  }
  return validaRete(dati);
}

// "2026-10-26" -> "26/10/2026"
function formattaData(iso) {
  const [anno, mese, giorno] = String(iso).split("-");
  return giorno && mese && anno ? `${giorno}/${mese}/${anno}` : "data sconosciuta";
}

// Coppie di stazioni consecutive, una sola volta per coppia (A-B e B-A sono lo stesso segmento).
function segmentiUnici(rete) {
  const visti = new Map();
  for (const treno of rete.treni) {
    const f = treno.fermate;
    for (let i = 1; i < f.length; i++) {
      const a = f[i - 1].stazione;
      const b = f[i].stazione;
      const chiave = a < b ? `${a}|${b}` : `${b}|${a}`;
      if (!visti.has(chiave)) visti.set(chiave, a < b ? [a, b] : [b, a]);
    }
  }
  return [...visti.values()];
}

if (typeof module !== "undefined") {
  module.exports = { ErroreRete, validaRete, caricaRete, formattaData, segmentiUnici, RETE_FORMATO_VERSIONE };
}
