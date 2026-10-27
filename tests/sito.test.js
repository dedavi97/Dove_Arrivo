const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const { validaRete, formattaData, segmentiUnici, ErroreRete } = require("../docs/rete.js");
const { changelogInHtml, escapeHtml, raggioStazione } = require("../docs/app.js");

const RADICE = path.join(__dirname, "..");

function rete(extra = {}) {
  return {
    meta: { tipo: "Dove_Arrivo_Rete", formato_versione: 1, data_aggiornamento: "2026-10-26", perimetro: "Piemonte" },
    stazioni: [],
    treni: [],
    ...extra,
  };
}

test("validaRete accetta una rete corretta", () => {
  const r = rete();
  assert.strictEqual(validaRete(r), r);
});

test("validaRete rifiuta tipo sconosciuto con messaggio chiaro", () => {
  assert.throws(() => validaRete({ meta: { tipo: "Altro" } }), (e) => e instanceof ErroreRete && /non riconosciuto/.test(e.titolo));
  assert.throws(() => validaRete(null), ErroreRete);
  assert.throws(() => validaRete("testo"), ErroreRete);
});

test("validaRete rifiuta un'altra versione di formato, senza convertire", () => {
  const r = rete();
  r.meta.formato_versione = 2;
  assert.throws(() => validaRete(r), (e) => /formato 2/.test(e.dettaglio) && /solo il formato 1/.test(e.dettaglio));
});

test("validaRete rifiuta file senza stazioni o treni", () => {
  assert.throws(() => validaRete({ meta: rete().meta }), /incompleto/);
});

test("formattaData", () => {
  assert.strictEqual(formattaData("2026-10-26"), "26/10/2026");
  assert.strictEqual(formattaData(undefined), "data sconosciuta");
});

test("segmentiUnici conta una sola volta A-B e B-A", () => {
  const f = (...ids) => ids.map((stazione, i) => ({ stazione, minuti_dalla_partenza: i * 10 }));
  const r = rete({
    treni: [
      { numero: "1", categoria: "REG", fermate: f("A", "B", "C") },
      { numero: "2", categoria: "REG", fermate: f("C", "B", "A") },
      { numero: "3", categoria: "RV", fermate: f("A", "C") },
    ],
  });
  assert.deepStrictEqual(segmentiUnici(r), [["A", "B"], ["B", "C"], ["A", "C"]]);
});

test("changelogInHtml: titoli, voci su più righe, codice, niente HTML iniettato", () => {
  const md = "# Changelog\n\nIntro.\n\n## 0.2.0 — 26/10/2026\n- Prima voce\n  che continua\n- Usa `rete.json` <b>\n\n## 0.1.0 — 25/10/2026\n- Altra\n";
  assert.strictEqual(
    changelogInHtml(md),
    "<h4>0.2.0 — 26/10/2026</h4><ul><li>Prima voce che continua</li><li>Usa <code>rete.json</code> &lt;b&gt;</li></ul>" +
      "<h4>0.1.0 — 25/10/2026</h4><ul><li>Altra</li></ul>"
  );
});

test("escapeHtml", () => {
  assert.strictEqual(escapeHtml(`Castello d'Annone <&>`), "Castello d&#39;Annone &lt;&amp;&gt;");
});

test("raggioStazione cresce con lo zoom", () => {
  assert.ok(raggioStazione(6) < raggioStazione(7));
  assert.ok(raggioStazione(7) < raggioStazione(8));
  assert.ok(raggioStazione(8) < raggioStazione(10));
  assert.ok(raggioStazione(10) < raggioStazione(12));
});

test("il rete.json pubblicato è valido e coerente", () => {
  const dati = JSON.parse(fs.readFileSync(path.join(RADICE, "docs", "data", "rete.json"), "utf8"));
  validaRete(dati);
  const ids = new Set(dati.stazioni.map((s) => s.id));
  assert.strictEqual(dati.meta.conteggi.stazioni, dati.stazioni.length);
  assert.strictEqual(dati.meta.conteggi.treni, dati.treni.length);
  for (const t of dati.treni) {
    for (const f of t.fermate) assert.ok(ids.has(f.stazione), `treno ${t.numero}: stazione ${f.stazione} mancante`);
  }
});

test("le novità mostrate dal sito coincidono con CHANGELOG.md", () => {
  const radice = fs.readFileSync(path.join(RADICE, "CHANGELOG.md"), "utf8");
  const sito = fs.readFileSync(path.join(RADICE, "docs", "CHANGELOG.md"), "utf8");
  assert.strictEqual(sito, radice, "copia CHANGELOG.md in docs/CHANGELOG.md");
});

test("filtro abitanti: visibilità e testo della soglia", () => {
  const { stazioneVisibile, testoSoglia, SOGLIE_ABITANTI } = require("../docs/app.js");
  assert.strictEqual(SOGLIE_ABITANTI[0], 0);
  assert.ok(SOGLIE_ABITANTI.every((v, i) => i === 0 || v > SOGLIE_ABITANTI[i - 1]));
  assert.ok(stazioneVisibile({ id: "a", abitanti: 5000 }, 5000, null));
  assert.ok(!stazioneVisibile({ id: "a", abitanti: 4999 }, 5000, null));
  assert.ok(stazioneVisibile({ id: "a", abitanti: 10 }, 5000, "a"), "la partenza resta visibile");
  assert.ok(stazioneVisibile({ id: "x" }, 500000, null), "senza dato (estero) resta visibile");
  assert.strictEqual(testoSoglia(0), "tutti");
  assert.strictEqual(testoSoglia(20000), "20.000");
});

test("cercaStazioni: accenti, punteggiatura e ordine dei risultati", () => {
  const { cercaStazioni, normalizzaNome } = require("../docs/rete.js");
  const stazioni = ["Asti", "Isola d'Asti", "Castello d'Annone", "S.Damiano d'Asti", "Pastìcceria"].map((nome, i) => ({ id: String(i), nome }));
  assert.strictEqual(normalizzaNome("S.Damiano d'Asti"), "s damiano d asti");
  assert.deepStrictEqual(cercaStazioni(stazioni, "asti").map((s) => s.nome), ["Asti", "Isola d'Asti", "S.Damiano d'Asti", "Pastìcceria"]);
  assert.deepStrictEqual(cercaStazioni(stazioni, "d asti").map((s) => s.nome), ["Isola d'Asti", "S.Damiano d'Asti"]);
  assert.deepStrictEqual(cercaStazioni(stazioni, "   "), []);
  assert.strictEqual(cercaStazioni(stazioni, "a", 2).length, 2);
});

test("nelPerimetro: Italia esclude solo l'estero, una regione solo sé stessa", () => {
  const { nelPerimetro } = require("../docs/app.js");
  assert.ok(nelPerimetro({ regione: "Sicilia" }, "Italia"));
  assert.ok(!nelPerimetro({ regione: "Estero" }, "Italia"));
  assert.ok(nelPerimetro({ regione: "Piemonte" }, "Piemonte"));
  assert.ok(!nelPerimetro({ regione: "Liguria" }, "Piemonte"));
});

test("htmlDiretti: tratta rara con avviso, normale, molti orari a scomparsa", () => {
  global.formattaOrario = require("../docs/percorsi.js").formattaOrario;
  global.SOGLIA_TRATTA_RARA = require("../docs/percorsi.js").SOGLIA_TRATTA_RARA;
  global.formattaData = require("../docs/rete.js").formattaData;
  const { htmlDiretti } = require("../docs/app.js");
  const giorni = ["2026-11-04", "2026-11-25"];
  const rara = htmlDiretti({ giorno: 1, orari: [401, 440, 1075, 1135, 1195] }, giorni);
  assert.match(rara, /⚠/);
  assert.match(rara, /5 diretti al giorno: 06:41, 07:20, 17:55, 18:55, 19:55/);
  assert.match(rara, /Pochi treni: controlla l'orario/);
  assert.match(rara, /mercoledì 25\/11/);
  const normale = htmlDiretti({ giorno: 0, orari: [360, 420, 480, 540, 600, 660] }, giorni);
  assert.doesNotMatch(normale, /⚠|<details/);
  const molti = htmlDiretti({ giorno: 0, orari: Array.from({ length: 20 }, (_, i) => 300 + 30 * i) }, giorni);
  assert.match(molti, /<details/);
  assert.strictEqual(htmlDiretti(null, giorni), "");
});

test("fonti: elenco con validità, avviso se scaduta, operatore per nome", () => {
  global.formattaData = require("../docs/rete.js").formattaData;
  const { htmlFonti, fonteDi } = require("../docs/app.js");
  const meta = {
    fonte: "Orario Trenord: Regione Lombardia <CC-BY>",
    fonti: [
      { nome: "Trenitalia", treni: 2082, validita_dal: "2026-10-24", validita_al: "2027-12-11", scaduta: false },
      { nome: "Trenord", treni: 343, validita_dal: "2026-07-26", validita_al: "2026-12-12", scaduta: true },
    ],
  };
  const html = htmlFonti(meta);
  assert.match(html, /Trenitalia<\/strong>: 2082 treni, orario valido dal 24\/10\/2026 al 11\/12\/2027<\/li>/);
  assert.match(html, /Trenord<\/strong>: 343 treni.*orario scaduto/);
  assert.match(html, /&lt;CC-BY&gt;/);
  assert.strictEqual(htmlFonti({ fonte: "solo testo" }), "solo testo");
  assert.strictEqual(fonteDi({ meta }, "Trenord").scaduta, true);
  assert.strictEqual(fonteDi({ meta }, undefined), null);
});

test("lineaFermate: segue i tracciati nei due versi, dritta dove mancano", () => {
  const { indiceTracciati, lineaFermate } = require("../docs/rete.js");
  const coord = { A: [0, 0], B: [0, 10], C: [0, 20] };
  const tracciati = indiceTracciati({ tracciati: [["A", "B", [[1, 3], [1, 6]]]] });
  const c = (id) => coord[id];
  assert.deepStrictEqual(lineaFermate(["A", "B", "C"], c, tracciati), [[0, 0], [1, 3], [1, 6], [0, 10], [0, 20]]);
  assert.deepStrictEqual(lineaFermate(["B", "A"], c, tracciati), [[0, 10], [1, 6], [1, 3], [0, 0]]);
  assert.deepStrictEqual(lineaFermate(["C"], c, tracciati), [[0, 20]]);
  assert.strictEqual(indiceTracciati({}).size, 0);
});

test("filtro aziende: treni ammessi e stazioni servite", () => {
  const { aziendaAmmessa, stazioniServite, ORE_MAX } = require("../docs/app.js");
  const f = (...ids) => ids.map((stazione) => ({ stazione, minuti_dalla_partenza: 0 }));
  const rete = {
    treni: [
      { operatore: "Trenitalia", fermate: f("A", "B") },
      { operatore: "Trenord", fermate: f("B", "C") },
      { fermate: f("D", "E") }, // dati vecchi senza operatore: sempre ammesso
    ],
  };
  assert.ok(aziendaAmmessa(rete.treni[0], ["Trenord"]));
  assert.ok(!aziendaAmmessa(rete.treni[1], ["Trenord"]));
  assert.ok(aziendaAmmessa(rete.treni[2], ["Trenord", "Trenitalia"]));
  assert.deepStrictEqual([...stazioniServite(rete, (t) => aziendaAmmessa(t, ["Trenord"]))].sort(), ["A", "B", "D", "E"]);
  assert.strictEqual(ORE_MAX, 12);
  const html = fs.readFileSync(path.join(RADICE, "docs", "index.html"), "utf8");
  assert.match(html, /id="ore" type="range" min="0.5" max="12"/, "il cursore arriva a ORE_MAX");
});
