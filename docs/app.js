// Interfaccia: mappa, partenza, cursori, mete colorate, scheda del percorso, finestre.

const URL_RETE = "data/rete.json";
const URL_NOVITA = "CHANGELOG.md";
const URL_TRENITALIA = "https://www.lefrecce.it/Channels.Website.WEB/";
const URL_TRENORD = "https://www.trenord.it/";
const CHIAVE_MEMORIA = "dove_arrivo_stato";
const CENTRO_INIZIALE = [45.05, 7.9];
const ORE_MAX = 12; // fondo scala del cursore "Ore max" (anche in index.html)
// Gradini del cursore "abitanti min": irregolari, così anche le soglie piccole si scelgono bene.
const SOGLIE_ABITANTI = [0, 1000, 2000, 5000, 10000, 20000, 50000, 100000, 250000, 500000];
const ZOOM_INIZIALE = 8;

const stato = {
  rete: null,
  indice: null,
  perId: new Map(),
  tracciati: new Map(),
  servite: new Set(), // stazioni servite da almeno un treno delle aziende accese
  origine: null,
  meta: null,
  mete: new Map(),
  maxCambi: 1,
  maxOre: 2,
  soglia: 0, // indice in SOGLIE_ABITANTI
  imp: { ricorda: true, linee: true, spente: [] }, // spente = aziende da non mostrare né usare
};
let mappa = null;
const pallini = new Map();
let stratoLinee = null;
let stratoPercorso = null;
let rendererStazioni = null;
let anelliCambio = [];

// ---------------------------------------------------------------- funzioni pure

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

// Pallini più piccoli quando si vede tutta Italia, così non si ammassano.
function raggioStazione(zoom) {
  return zoom >= 12 ? 6 : zoom >= 10 ? 4.5 : zoom >= 8 ? 3.5 : zoom >= 7 ? 2.8 : 2.2;
}

// Il perimetro "Italia" comprende tutte le regioni: fuori restano solo le stazioni estere.
function nelPerimetro(stazione, perimetro) {
  return perimetro === "Italia" ? stazione.regione !== "Estero" : stazione.regione === perimetro;
}

function testoSoglia(abitanti) {
  return abitanti ? abitanti.toLocaleString("it-IT") : "tutti";
}

// Le stazioni di comuni sotto soglia spariscono; restano quelle senza dato (all'estero)
// e la partenza scelta.
function stazioneVisibile(stazione, abitantiMin, origine) {
  return stazione.id === origine || stazione.abitanti === undefined || stazione.abitanti >= abitantiMin;
}

// Quante corse dirette fa una tratta e a che ora partono; con meno di
// SOGLIA_TRATTA_RARA corse avvisa. Oltre 12 orari l'elenco si apre a richiesta.
function htmlDiretti(diretti, giorniTipo) {
  if (!diretti || !diretti.orari.length) return "";
  const n = diretti.orari.length;
  const orari = diretti.orari.map(formattaOrario).join(", ");
  const quando = `<span class="quando">orari di mercoledì ${formattaData(giorniTipo[diretti.giorno]).slice(0, 5)}</span>`;
  const titolo = `${n} ${n === 1 ? "diretto" : "diretti"} al giorno`;
  if (n < SOGLIA_TRATTA_RARA) {
    return `<span class="diretti rara"><span class="avviso" aria-hidden="true">⚠</span> ${titolo}: ${orari} ${quando}` +
      `<span class="nota-rara">Pochi treni: controlla l'orario prima di partire</span></span>`;
  }
  if (n > 12) {
    return `<details class="diretti"><summary>${titolo} · vedi orari</summary>${orari} ${quando}</details>`;
  }
  return `<span class="diretti">${titolo}: ${orari} ${quando}</span>`;
}

// Fonte (meta.fonti) di un operatore, per sapere se il suo orario è scaduto.
function fonteDi(rete, operatore) {
  return ((rete.meta && rete.meta.fonti) || []).find((f) => f.nome === operatore) || null;
}

// Elenco delle fonti per "Informazioni": nome, validità, avviso se scaduta.
function htmlFonti(meta) {
  if (!meta.fonti) return escapeHtml(meta.fonte || "—");
  const righe = meta.fonti.map((f) => {
    const scaduta = f.scaduta ? ` <strong class="scaduta">orario scaduto: dati vecchi</strong>` : "";
    return `<li><strong>${escapeHtml(f.nome)}</strong>: ${f.treni} treni, orario valido dal ` +
      `${formattaData(f.validita_dal)} al ${formattaData(f.validita_al)}${scaduta}</li>`;
  });
  return `<ul class="fonti">${righe.join("")}</ul><p class="attribuzioni">${escapeHtml(meta.fonte || "")}</p>`;
}

// Filtro aziende: un treno senza operatore (dati vecchi) è sempre ammesso.
function aziendaAmmessa(treno, spente) {
  return !treno.operatore || !spente.includes(treno.operatore);
}

function stazioniServite(rete, ammesso) {
  const servite = new Set();
  for (const treno of rete.treni) if (ammesso(treno)) for (const f of treno.fermate) servite.add(f.stazione);
  return servite;
}

function testoCambi(n) {
  return n === 0 ? "diretto" : n === 1 ? "1 cambio" : `${n} cambi`;
}

// ---------------------------------------------------------------- memoria locale

function leggiMemoria() {
  try {
    return JSON.parse(localStorage.getItem(CHIAVE_MEMORIA)) || {};
  } catch (e) {
    return {};
  }
}

function salvaMemoria() {
  const dati = { imp: stato.imp };
  if (stato.imp.ricorda) {
    Object.assign(dati, { origine: stato.origine, maxCambi: stato.maxCambi, maxOre: stato.maxOre, soglia: stato.soglia });
  }
  try {
    localStorage.setItem(CHIAVE_MEMORIA, JSON.stringify(dati));
  } catch (e) {
    // memoria non disponibile (navigazione privata): si continua senza
  }
}

// ---------------------------------------------------------------- mappa

function colore(nome) {
  return getComputedStyle(document.documentElement).getPropertyValue(nome).trim();
}

function mostraStato(titolo, testo) {
  document.getElementById("stato-titolo").textContent = titolo;
  document.getElementById("stato-testo").textContent = testo;
  document.getElementById("stato").hidden = false;
}

function creaMappa() {
  mappa = L.map("mappa", { zoomSnap: 0.5 }).setView(CENTRO_INIZIALE, ZOOM_INIZIALE);
  // Tile OpenStreetMap (libere, senza chiave), scurite via CSS in .mappa-scura (style.css).
  // CARTO dark dal 2026 chiede una chiave API.
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    className: "mappa-scura",
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(mappa);
  // Livelli separati: linee della rete sotto, percorso evidenziato in mezzo, stazioni sopra.
  [["linee", 410], ["percorso", 420], ["stazioni", 430]].forEach(([nome, z]) => {
    mappa.createPane(nome).style.zIndex = z;
  });
}

function coordinate(id) {
  const s = stato.perId.get(id);
  return [s.lat, s.lon];
}

function lineeRete() {
  const treni = stato.rete.treni.filter((t) => aziendaAmmessa(t, stato.imp.spente));
  return segmentiUnici({ treni }).map(([a, b]) => lineaFermate([a, b], coordinate, stato.tracciati));
}

// Ricostruisce indice, stazioni servite e linee dopo un cambio del filtro aziende.
function applicaAziende() {
  const ammesso = (t) => aziendaAmmessa(t, stato.imp.spente);
  stato.indice = creaIndice(stato.rete, ammesso);
  stato.servite = stazioniServite(stato.rete, ammesso);
  if (stratoLinee) stratoLinee.setLatLngs(lineeRete());
  if (stato.origine && !stato.servite.has(stato.origine)) {
    stato.origine = null; // la partenza era servita solo dalle aziende spente
    chiudiScheda();
    aggiornaRicerca();
  }
}

// Visibile = servita dalle aziende accese e sopra la soglia di abitanti (vedi stazioneVisibile).
function visibileOra(stazione, origine = stato.origine) {
  return stato.servite.has(stazione.id) && stazioneVisibile(stazione, SOGLIE_ABITANTI[stato.soglia], origine);
}

function disegnaRete() {
  const rete = stato.rete;
  stratoLinee = L.polyline(lineeRete(), {
    pane: "linee",
    renderer: L.canvas({ pane: "linee" }),
    color: colore("--linea"),
    weight: 1.6,
    opacity: 0.6,
    interactive: false,
  });
  if (stato.imp.linee) stratoLinee.addTo(mappa);
  stratoPercorso = L.layerGroup().addTo(mappa);

  rendererStazioni = L.canvas({ pane: "stazioni", tolerance: 6 });
  for (const s of rete.stazioni) {
    const pallino = L.circleMarker([s.lat, s.lon], { pane: "stazioni", renderer: rendererStazioni, weight: 1, fillOpacity: 1 });
    pallino.bindTooltip(escapeHtml(s.nome), { className: "nome-stazione", direction: "top", offset: [0, -6] });
    pallino.on("click", () => tocca(s.id));
    pallini.set(s.id, pallino.addTo(mappa));
  }
  mappa.on("zoomend", colora);
  // Vista iniziale sulle sole stazioni del perimetro (non quelle estere a fine linea).
  const dentro = rete.stazioni.filter((s) => nelPerimetro(s, rete.meta.perimetro));
  const daInquadrare = dentro.length ? dentro : rete.stazioni;
  if (daInquadrare.length) {
    mappa.fitBounds(L.latLngBounds(daInquadrare.map((s) => [s.lat, s.lon])), { padding: [20, 20] });
  }
}

function colora() {
  const r = raggioStazione(mappa.getZoom());
  const sfondo = colore("--sfondo");
  for (const [id, pallino] of pallini) {
    const s = stato.perId.get(id);
    if (!visibileOra(s)) {
      if (mappa.hasLayer(pallino)) pallino.remove();
      continue;
    }
    if (!mappa.hasLayer(pallino)) pallino.addTo(mappa);
    let stile;
    if (id === stato.origine) {
      stile = { radius: r + 3, color: "#ffffff", weight: 2, fillColor: colore("--origine") };
    } else if (!stato.origine) {
      const dentro = nelPerimetro(s, stato.rete.meta.perimetro);
      stile = { radius: r, color: sfondo, weight: 1, fillColor: colore(dentro ? "--stazione" : "--stazione-fuori") };
    } else if (stato.mete.has(id)) {
      const fascia_ = fascia(stato.mete.get(id).minuti);
      stile = { radius: r, color: sfondo, weight: 1, fillColor: colore(`--${fascia_}`) };
    } else {
      stile = { radius: Math.max(r - 1, 2.5), color: sfondo, weight: 1, fillColor: colore("--spento") };
    }
    if (id === stato.meta) Object.assign(stile, { radius: r + 3, color: "#ffffff", weight: 2 });
    pallino.setStyle(stile);
  }
  if (stato.meta && mappa.hasLayer(pallini.get(stato.meta))) pallini.get(stato.meta).bringToFront();
  if (stato.origine) pallini.get(stato.origine).bringToFront();
  anelliCambio.forEach((anello) => anello.setRadius(r + 5).bringToFront());
}

function disegnaPercorso(etichetta) {
  stratoPercorso.clearLayers();
  anelliCambio = [];
  document.getElementById("legenda-cambio").hidden = true;
  if (!etichetta) return;
  const rete = stato.rete;
  const renderer = L.canvas({ pane: "percorso" });
  const opzioni = { pane: "percorso", renderer, interactive: false };
  const tratti = etichetta.tratte.map((t) => lineaFermate(fermateTratta(rete, t), coordinate, stato.tracciati));
  // Prosecuzione tratteggiata di ogni treno usato, dalla stazione dove lo si lascia.
  for (const t of etichetta.tratte) {
    const resto = [rete.treni[t.treno].fermate[t.a].stazione, ...restoTratta(rete, t)];
    if (resto.length > 1) {
      L.polyline(lineaFermate(resto, coordinate, stato.tracciati), { ...opzioni, color: colore("--percorso"), weight: 2.5, opacity: 0.75, dashArray: "4 8" }).addTo(stratoPercorso);
    }
  }
  L.polyline(tratti, { ...opzioni, color: colore("--sfondo"), weight: 8, opacity: 0.7 }).addTo(stratoPercorso);
  L.polyline(tratti, { ...opzioni, color: colore("--percorso"), weight: 4 }).addTo(stratoPercorso);
  // Anelli sulle stazioni di cambio, sopra i pallini (stesso livello delle stazioni).
  const r = raggioStazione(mappa.getZoom()) + 5;
  for (const id of stazioniCambio(rete, etichetta)) {
    const anello = L.circleMarker(coordinate(id), {
      pane: "stazioni", renderer: rendererStazioni, interactive: false,
      radius: r, color: colore("--cambio"), weight: 3, fill: false,
    });
    anelliCambio.push(anello.addTo(stratoPercorso));
  }
  document.getElementById("legenda-cambio").hidden = !anelliCambio.length;
  inquadra(L.latLngBounds(tratti.flat()));
}

// Porta il percorso in vista se esce dalla parte di mappa non coperta dalla scheda
// (in basso su telefono, a destra su schermi larghi), oppure se è così piccolo
// rispetto alla vista (es. Torino-Racconigi vedendo tutta Italia) che non si distingue.
const ZOOM_MAX_PERCORSO = 10;
const SCARTO_ZOOM_PER_AVVICINARE = 2;

function inquadra(limiti) {
  const scheda = document.getElementById("scheda");
  const largo = window.matchMedia("(min-width: 760px)").matches;
  const margineBasso = largo ? 30 : scheda.offsetHeight + 30;
  const margineDestro = largo ? scheda.offsetWidth + 30 : 30;
  const dimensioni = mappa.getSize();
  const visibile = L.latLngBounds(
    mappa.containerPointToLatLng([30, 50]),
    mappa.containerPointToLatLng([dimensioni.x - margineDestro, dimensioni.y - margineBasso])
  );
  const margini = L.point(30 + margineDestro, 50 + margineBasso);
  const zoomAdatto = Math.min(mappa.getBoundsZoom(limiti, false, margini), ZOOM_MAX_PERCORSO);
  const troppoPiccolo = zoomAdatto - mappa.getZoom() >= SCARTO_ZOOM_PER_AVVICINARE;
  if (visibile.contains(limiti) && !troppoPiccolo) return;
  mappa.fitBounds(limiti, {
    paddingTopLeft: [30, 50],
    paddingBottomRight: [margineDestro, margineBasso],
    maxZoom: Math.max(mappa.getZoom(), ZOOM_MAX_PERCORSO),
  });
}

// ---------------------------------------------------------------- stato e calcolo

function ricalcola() {
  stato.mete = stato.origine
    ? calcolaMete(stato.indice, stato.origine, stato.maxCambi, stato.maxOre * 60)
    : new Map();
  colora();
  aggiornaSuggerimento();
  if (stato.meta && !visibileOra(stato.perId.get(stato.meta))) {
    chiudiScheda(); // la meta aperta è sparita col filtro abitanti o aziende
  } else if (stato.meta) {
    mostraScheda(stato.meta);
  }
  salvaMemoria();
}

function meteVisibili() {
  let n = 0;
  for (const id of stato.mete.keys()) if (visibileOra(stato.perId.get(id))) n++;
  return n;
}

function aggiornaSuggerimento() {
  const box = document.getElementById("suggerimento");
  if (!stato.origine) {
    box.textContent = "Tocca una stazione o cercala in alto per scegliere la partenza";
  } else if (!stato.mete.size) {
    box.textContent = "Nessuna meta raggiungibile con questi limiti: prova ad aumentare cambi o ore";
  } else if (!meteVisibili()) {
    box.textContent = "Nessuna meta sopra la soglia di abitanti: prova ad abbassarla";
  } else {
    const n = meteVisibili();
    box.textContent = `${n} ${n === 1 ? "meta raggiungibile" : "mete raggiungibili"} · tocca una meta per il percorso`;
  }
  box.hidden = false;
}

function impostaOrigine(id) {
  stato.origine = id;
  stato.meta = null;
  chiudiScheda();
  aggiornaRicerca();
  ricalcola();
}

function togliOrigine() {
  impostaOrigine(null);
}

function tocca(id) {
  if (!stato.origine) {
    impostaOrigine(id);
  } else if (id === stato.origine) {
    chiudiScheda();
  } else {
    mostraScheda(id);
  }
}

// ---------------------------------------------------------------- scheda della meta

function mostraScheda(id) {
  stato.meta = id;
  const rete = stato.rete;
  const nome = (sid) => escapeHtml(stato.perId.get(sid).nome);
  const etichetta = stato.mete.get(id);
  const stazione = stato.perId.get(id);
  document.getElementById("scheda-titolo").textContent = stazione.nome;
  const corpo = document.getElementById("scheda-corpo");
  const comune = stazione.abitanti !== undefined
    ? `<p class="comune">Comune di ${escapeHtml(stazione.comune)} · ${stazione.abitanti.toLocaleString("it-IT")} abitanti</p>`
    : "";
  const partiDaQui = `<button type="button" class="bottone" data-azione="parti">Parti da qui</button>`;

  if (!etichetta) {
    const cambi = stato.maxCambi === 0 ? "senza cambi" : `con al massimo ${testoCambi(stato.maxCambi)}`;
    corpo.innerHTML = comune +
      `<p class="totale">Non raggiungibile da ${nome(stato.origine)} ${cambi} ` +
      `e ${formattaDurata(stato.maxOre * 60)} di treno.</p>` +
      `<div class="azioni">${partiDaQui}</div>`;
  } else {
    const righe = [];
    etichetta.tratte.forEach((t, k) => {
      const treno = rete.treni[t.treno];
      const fermate = treno.fermate;
      if (k > 0) righe.push(`<li class="cambio"><i class="anello" aria-hidden="true"></i> Cambio a ${nome(fermate[t.da].stazione)}</li>`);
      const resto = restoTratta(rete, t);
      const prosegue = (treno.operatore ? `${escapeHtml(treno.operatore)} · ` : "") + (resto.length
        ? `prosegue per ${nome(resto[resto.length - 1])}` +
          (resto.length > 1 ? ` (altre ${resto.length} fermate)` : "")
        : "termina qui");
      const fonte = fonteDi(rete, treno.operatore);
      const scaduta = fonte && fonte.scaduta
        ? `<span class="diretti rara"><span class="avviso" aria-hidden="true">⚠</span> Orario ${escapeHtml(fonte.nome)} ` +
          `scaduto il ${formattaData(fonte.validita_al)}: questi dati sono vecchi, controlla l'orario nuovo</span>`
        : "";
      righe.push(
        `<li class="tratta"><span class="treno">${escapeHtml(treno.categoria)} ${escapeHtml(treno.numero)}</span>` +
          `<span class="da-a">${nome(fermate[t.da].stazione)} → ${nome(fermate[t.a].stazione)}</span>` +
          `<span class="durata">${formattaDurata(minutiTratta(rete, t))}</span>` +
          `<span class="prosegue">${prosegue}</span>` +
          htmlDiretti(direttiTratta(stato.indice, fermate[t.da].stazione, fermate[t.a].stazione), rete.meta.giorni_tipo) +
          scaduta +
          `</li>`
      );
    });
    const conTrenord = etichetta.tratte.some((t) => rete.treni[t.treno].operatore === "Trenord");
    corpo.innerHTML = comune +
      `<p class="totale"><strong>${formattaDurata(etichetta.minuti)}</strong> ${testoCambi(etichetta.tratte.length - 1)}</p>` +
      `<ol class="tratte">${righe.join("")}</ol>` +
      `<div class="azioni">` +
      `<a class="bottone primario" href="${URL_TRENITALIA}" target="_blank" rel="noopener">Verifica prezzo</a>` +
      (conTrenord ? `<a class="bottone" href="${URL_TRENORD}" target="_blank" rel="noopener">Sito Trenord</a>` : "") +
      partiDaQui +
      `</div>` +
      `<p class="nota">Su Trenitalia cerca da <strong>${nome(stato.origine)}</strong> a <strong>${nome(id)}</strong>` +
      (conTrenord ? ` (per i treni Trenord anche sul sito Trenord)` : "") + `. ` +
      `Il tempo conta solo i minuti sui treni, senza le attese ai cambi.</p>`;
  }
  corpo.querySelector('[data-azione="parti"]').addEventListener("click", () => impostaOrigine(id));
  document.getElementById("scheda").hidden = false;
  document.getElementById("suggerimento").hidden = true; // con la scheda aperta non serve e coprirebbe la mappa
  colora();
  disegnaPercorso(etichetta);
}

function chiudiScheda() {
  stato.meta = null;
  document.getElementById("scheda").hidden = true;
  if (stratoPercorso) disegnaPercorso(null);
  if (mappa) colora();
  if (stato.rete) aggiornaSuggerimento();
}

// ---------------------------------------------------------------- ricerca della partenza

function aggiornaRicerca() {
  const campo = document.getElementById("cerca");
  campo.value = stato.origine ? stato.perId.get(stato.origine).nome : "";
  document.getElementById("togli-partenza").hidden = !stato.origine;
}

function preparaRicerca() {
  const campo = document.getElementById("cerca");
  const lista = document.getElementById("risultati");
  let trovate = [];
  let attiva = 0;

  const chiudi = () => {
    lista.hidden = true;
    campo.setAttribute("aria-expanded", "false");
    campo.removeAttribute("aria-activedescendant");
  };
  const disegna = () => {
    lista.innerHTML = trovate.length
      ? trovate
          .map((s, i) => {
            const perimetro = stato.rete.meta.perimetro;
            const mostra = perimetro === "Italia" || s.regione !== perimetro;
            const regione = mostra ? `<span class="regione">${escapeHtml(s.regione)}</span>` : "";
            return `<li id="risultato-${i}" role="option" aria-selected="${i === attiva}" data-id="${escapeHtml(s.id)}">${escapeHtml(s.nome)}${regione}</li>`;
          })
          .join("")
      : `<li role="option" aria-disabled="true">Nessuna stazione con questo nome</li>`;
    lista.hidden = false;
    campo.setAttribute("aria-expanded", "true");
    if (trovate.length) campo.setAttribute("aria-activedescendant", `risultato-${attiva}`);
  };
  const scegli = (id) => {
    chiudi();
    campo.blur();
    impostaOrigine(id);
    const punto = L.latLng(coordinate(id));
    if (!mappa.getBounds().contains(punto)) mappa.panTo(punto);
  };

  campo.addEventListener("focus", () => campo.select());
  campo.addEventListener("input", () => {
    trovate = cercaStazioni(stato.rete.stazioni.filter((s) => visibileOra(s, null)), campo.value);
    attiva = 0;
    campo.value.trim() ? disegna() : chiudi();
  });
  campo.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!trovate.length) return;
      e.preventDefault();
      attiva = (attiva + (e.key === "ArrowDown" ? 1 : trovate.length - 1)) % trovate.length;
      disegna();
    } else if (e.key === "Enter") {
      if (trovate.length && !lista.hidden) scegli(trovate[attiva].id);
    } else if (e.key === "Escape") {
      chiudi();
      aggiornaRicerca();
      campo.blur();
    }
  });
  // mousedown (non click): arriva prima che il campo perda il fuoco e chiuda la lista
  lista.addEventListener("mousedown", (e) => {
    const voce = e.target.closest("li[data-id]");
    if (!voce) return;
    e.preventDefault();
    scegli(voce.dataset.id);
  });
  campo.addEventListener("blur", () => {
    setTimeout(() => {
      chiudi();
      aggiornaRicerca();
    }, 150);
  });
  document.getElementById("togli-partenza").addEventListener("click", togliOrigine);
}

// ---------------------------------------------------------------- cursori e impostazioni

function preparaCursori() {
  const cambi = document.getElementById("cambi");
  const ore = document.getElementById("ore");
  const abitanti = document.getElementById("abitanti");
  const mostra = () => {
    document.getElementById("val-cambi").textContent = stato.maxCambi;
    document.getElementById("val-ore").textContent = formattaDurata(stato.maxOre * 60);
    document.getElementById("val-abitanti").textContent = testoSoglia(SOGLIE_ABITANTI[stato.soglia]);
  };
  cambi.value = stato.maxCambi;
  ore.value = stato.maxOre;
  abitanti.max = SOGLIE_ABITANTI.length - 1;
  abitanti.value = stato.soglia;
  abitanti.addEventListener("input", () => {
    stato.soglia = Number(abitanti.value);
    mostra();
    ricalcola();
  });
  mostra();
  cambi.addEventListener("input", () => {
    stato.maxCambi = Number(cambi.value);
    mostra();
    ricalcola();
  });
  ore.addEventListener("input", () => {
    stato.maxOre = Number(ore.value);
    mostra();
    ricalcola();
  });
}

function preparaImpostazioni() {
  const ricorda = document.getElementById("imp-ricorda");
  const linee = document.getElementById("imp-linee");
  ricorda.checked = stato.imp.ricorda;
  linee.checked = stato.imp.linee;
  ricorda.addEventListener("change", () => {
    stato.imp.ricorda = ricorda.checked;
    salvaMemoria();
  });
  linee.addEventListener("change", () => {
    stato.imp.linee = linee.checked;
    if (stratoLinee) linee.checked ? stratoLinee.addTo(mappa) : stratoLinee.remove();
    salvaMemoria();
  });
}

// Caselle "Aziende" nelle impostazioni, una per fonte dei dati. Almeno una resta accesa.
function preparaAziende() {
  const fonti = (stato.rete.meta.fonti || []).map((f) => f.nome);
  const box = document.getElementById("imp-aziende");
  if (fonti.length < 2) return; // con una sola azienda non c'è niente da scegliere
  box.hidden = false;
  box.insertAdjacentHTML("beforeend", fonti.map((nome) =>
    `<label class="scelta"><input type="checkbox" value="${escapeHtml(nome)}"${stato.imp.spente.includes(nome) ? "" : " checked"}>` +
    `<span>${escapeHtml(nome)}</span></label>`).join(""));
  const caselle = [...box.querySelectorAll("input")];
  const aggiornaBlocchi = () => {
    const accese = caselle.filter((c) => c.checked);
    caselle.forEach((c) => { c.disabled = accese.length === 1 && c.checked; });
  };
  caselle.forEach((casella) => casella.addEventListener("change", () => {
    stato.imp.spente = caselle.filter((c) => !c.checked).map((c) => c.value);
    aggiornaBlocchi();
    applicaAziende();
    ricalcola();
  }));
  aggiornaBlocchi();
}

// ---------------------------------------------------------------- finestre

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
  document.getElementById("chiudi-scheda").addEventListener("click", chiudiScheda);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !document.querySelector("dialog[open]") && !document.getElementById("scheda").hidden) chiudiScheda();
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
  document.getElementById("info-fonti").innerHTML = htmlFonti(m);
}

// ---------------------------------------------------------------- avvio

async function avvia() {
  document.getElementById("versione").textContent = VERSIONE;
  const dataDati = document.getElementById("data-dati");
  const memoria = leggiMemoria();
  Object.assign(stato.imp, memoria.imp || {});
  if (!Array.isArray(stato.imp.spente)) stato.imp.spente = [];
  if (stato.imp.ricorda) {
    if ([0, 1, 2, 3].includes(memoria.maxCambi)) stato.maxCambi = memoria.maxCambi;
    if (typeof memoria.maxOre === "number" && memoria.maxOre >= 0.5 && memoria.maxOre <= ORE_MAX) stato.maxOre = memoria.maxOre;
    if (Number.isInteger(memoria.soglia) && memoria.soglia >= 0 && memoria.soglia < SOGLIE_ABITANTI.length) stato.soglia = memoria.soglia;
  }
  preparaFinestre();
  preparaImpostazioni();

  if (typeof L === "undefined") {
    dataDati.textContent = "";
    mostraStato("Mappa non disponibile", "non è stato possibile caricare la mappa. Controlla la connessione e ricarica la pagina.");
    compilaInformazioni(null);
    return;
  }
  creaMappa();

  let rete;
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
  stato.rete = rete;
  stato.perId = new Map(rete.stazioni.map((s) => [s.id, s]));
  stato.tracciati = indiceTracciati(rete);
  const aziende = (rete.meta.fonti || []).map((f) => f.nome);
  stato.imp.spente = stato.imp.spente.filter((nome) => aziende.includes(nome));
  if (stato.imp.spente.length >= aziende.length) stato.imp.spente = []; // mai tutte spente
  applicaAziende();
  if (stato.imp.ricorda && stato.servite.has(memoria.origine)) stato.origine = memoria.origine;

  disegnaRete();
  preparaAziende();
  preparaRicerca();
  preparaCursori();
  aggiornaRicerca();
  ricalcola();
}

if (typeof document !== "undefined") {
  avvia();
}

if (typeof module !== "undefined") {
  module.exports = {
    changelogInHtml, escapeHtml, raggioStazione, aziendaAmmessa, stazioniServite, ORE_MAX, htmlDiretti, htmlFonti, fonteDi, testoCambi, nelPerimetro, stazioneVisibile, testoSoglia, SOGLIE_ABITANTI,
  };
}
