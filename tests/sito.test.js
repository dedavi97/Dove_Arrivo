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

test("cercaStazioni: accenti, punteggiatura e ordine dei risultati", () => {
  const { cercaStazioni, normalizzaNome } = require("../docs/rete.js");
  const stazioni = ["Asti", "Isola d'Asti", "Castello d'Annone", "S.Damiano d'Asti", "Pastìcceria"].map((nome, i) => ({ id: String(i), nome }));
  assert.strictEqual(normalizzaNome("S.Damiano d'Asti"), "s damiano d asti");
  assert.deepStrictEqual(cercaStazioni(stazioni, "asti").map((s) => s.nome), ["Asti", "Isola d'Asti", "S.Damiano d'Asti", "Pastìcceria"]);
  assert.deepStrictEqual(cercaStazioni(stazioni, "d asti").map((s) => s.nome), ["Isola d'Asti", "S.Damiano d'Asti"]);
  assert.deepStrictEqual(cercaStazioni(stazioni, "   "), []);
  assert.strictEqual(cercaStazioni(stazioni, "a", 2).length, 2);
});
