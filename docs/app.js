// Interfaccia: mappa, stati vuoti, finestre Aiuto e Informazioni.

const URL_RETE = "data/rete.json";
const URL_NOVITA = "CHANGELOG.md";
const CENTRO_INIZIALE = [45.05, 7.9];
const ZOOM_INIZIALE = 8;

function escapeHtml(testo) {
  return String(testo).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

// Trasforma il CHANGELOG (solo "## versione" e voci "- ...", anche su più righe) in HTML.
function changelogInHtml(markdown) {
  const inline = (t) => escapeHtml(t).replace(/`([^`]+)`/g, "<code>$1</code>");
  const parti = [];
  let voce = null;
  const chiudiVoce = () => {
    if (voce !== null) parti.push(`<li>${inline(voce)}</li>`);
    voce = null;
  };
  let inLista = false;
  for (const riga of markdown.split(/\r?\n/)) {
    if (riga.startsWith("## ")) {
      chiudiVoce();
      if (inLista) parti.push("</ul>");
      parti.push(`<h4>${inline(riga.slice(3).trim())}</h4><ul>`);
      inLista = true;
    } else if (inLista && riga.startsWith("- ")) {
      chiudiVoce();
      voce = riga.slice(2).trim();
    } else if (inLista && voce !== null && /^\s+\S/.test(riga)) {
      voce += " " + riga.trim();
    }
  }
  chiudiVoce();
  if (inLista) parti.push("</ul>");
  return parti.join("");
}

function raggioStazione(zoom) {
  return zoom >= 12 ? 6 : zoom >= 10 ? 4.5 : 3.5;
}

function mostraStato(titolo, testo) {
  document.getElementById("stato-titolo").textContent = titolo;
  document.getElementById("stato-testo").textContent = testo;
  document.getElementById("stato").hidden = false;
}

function creaMappa() {
  const mappa = L.map("mappa", { preferCanvas: true, zoomSnap: 0.5 }).setView(CENTRO_INIZIALE, ZOOM_INIZIALE);
  // Tile OpenStreetMap (libere, senza chiave), scurite via CSS in .mappa-scura (style.css).
  // CARTO dark dal 2026 chiede una chiave API.
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    className: "mappa-scura",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(mappa);
  return mappa;
}

function disegnaRete(mappa, rete) {
  const stile = getComputedStyle(document.documentElement);
  const colore = (nome) => stile.getPropertyValue(nome).trim();
  const perId = new Map(rete.stazioni.map((s) => [s.id, s]));

  const linee = segmentiUnici(rete).map(([a, b]) => [
    [perId.get(a).lat, perId.get(a).lon],
    [perId.get(b).lat, perId.get(b).lon],
  ]);
  L.polyline(linee, { color: colore("--linea"), weight: 1.6, opacity: 0.75, interactive: false }).addTo(mappa);

  const pallini = rete.stazioni.map((s) => {
    const dentro = s.regione === rete.meta.perimetro;
    const pallino = L.circleMarker([s.lat, s.lon], {
      radius: raggioStazione(mappa.getZoom()),
      color: colore("--sfondo"),
      weight: 1,
      fillColor: colore(dentro ? "--stazione" : "--stazione-fuori"),
      fillOpacity: 1,
    });
    pallino.bindTooltip(escapeHtml(s.nome), { className: "nome-stazione", direction: "top", offset: [0, -6] });
    pallino.on("click", () => pallino.openTooltip());
    return pallino.addTo(mappa);
  });
  mappa.on("zoomend", () => {
    const r = raggioStazione(mappa.getZoom());
    pallini.forEach((p) => p.setRadius(r));
  });

  if (rete.stazioni.length) {
    mappa.fitBounds(L.latLngBounds(rete.stazioni.map((s) => [s.lat, s.lon])), { padding: [20, 20] });
  }
}

let novitaCaricate = false;

async function caricaNovita() {
  if (novitaCaricate) return;
  const box = document.getElementById("novita");
  try {
    const risposta = await fetch(URL_NOVITA, { cache: "no-cache" });
    if (!risposta.ok) throw new Error(risposta.status);
    box.innerHTML = changelogInHtml(await risposta.text());
    novitaCaricate = true;
  } catch (errore) {
    box.textContent = "Elenco delle novità non disponibile al momento.";
  }
}

function preparaFinestre() {
  document.querySelectorAll("[data-apri]").forEach((bottone) => {
    bottone.addEventListener("click", () => {
      document.getElementById(bottone.dataset.apri).showModal();
      if (bottone.dataset.apri === "info") caricaNovita();
    });
  });
  document.querySelectorAll("dialog").forEach((finestra) => {
    finestra.querySelector("[data-chiudi]").addEventListener("click", () => finestra.close());
    // clic fuori dalla finestra = chiudi
    finestra.addEventListener("click", (e) => { if (e.target === finestra) finestra.close(); });
  });
}

function compilaInformazioni(rete) {
  document.getElementById("info-versione").textContent = VERSIONE;
  if (!rete) return;
  const m = rete.meta;
  document.getElementById("info-dati").textContent =
    `aggiornati il ${formattaData(m.data_aggiornamento)} · ${m.perimetro} · ` +
    `${m.conteggi.stazioni} stazioni, ${m.conteggi.treni} treni` +
    (m.giorni_tipo ? ` · orari dei mercoledì ${m.giorni_tipo.map(formattaData).join(", ")}` : "");
  document.getElementById("info-fonti").textContent = m.fonte || "—";
}

async function avvia() {
  document.getElementById("versione").textContent = VERSIONE;
  const dataDati = document.getElementById("data-dati");
  let rete = null;
  preparaFinestre();

  if (typeof L === "undefined") {
    dataDati.textContent = "";
    mostraStato("Mappa non disponibile", "non è stato possibile caricare la mappa. Controlla la connessione e ricarica la pagina.");
    compilaInformazioni(null);
    return;
  }
  const mappa = creaMappa();

  try {
    rete = await caricaRete(URL_RETE);
  } catch (errore) {
    dataDati.textContent = "Nessun dato";
    mostraStato(errore.titolo || "Errore", errore.dettaglio || errore.message);
    compilaInformazioni(null);
    return;
  }

  dataDati.textContent = `Dati al ${formattaData(rete.meta.data_aggiornamento)}`;
  compilaInformazioni(rete);
  if (!rete.stazioni.length) {
    mostraStato("Rete vuota", "il file dati non contiene stazioni. Rigeneralo con Aggiorna_Dati.bat.");
    return;
  }
  disegnaRete(mappa, rete);
  const conteggi = document.getElementById("conteggi");
  conteggi.textContent = `${rete.meta.conteggi.stazioni} stazioni · ${rete.meta.conteggi.treni} treni`;
  conteggi.hidden = false;
}

if (typeof document !== "undefined") {
  avvia();
}

if (typeof module !== "undefined") {
  module.exports = { changelogInHtml, escapeHtml, raggioStazione };
}
