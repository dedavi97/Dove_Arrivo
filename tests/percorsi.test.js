const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");
const P = require("../docs/percorsi.js");

// Rete di prova:
//   treno 0 (REG 1): A 0 → B 20 → C 50 → D 80
//   treno 1 (RV 2):  A 0 → C 30            (più veloce di REG 1 fino a C)
//   treno 2 (REG 3): C 0 → E 25 → F 60
//   treno 3 (REG 4): F 0 → G 10
//   treno 4 (REG 5): D 0 → C 30            (verso opposto: da C non si va a D)
function treno(numero, ...fermate) {
  return {
    numero,
    categoria: "REG",
    fermate: fermate.map(([stazione, minuti_dalla_partenza]) => ({ stazione, minuti_dalla_partenza })),
  };
}
const RETE = {
  stazioni: [],
  treni: [
    treno("1", ["A", 0], ["B", 20], ["C", 50], ["D", 80]),
    treno("2", ["A", 0], ["C", 30]),
    treno("3", ["C", 0], ["E", 25], ["F", 60]),
    treno("4", ["F", 0], ["G", 10]),
    treno("5", ["D", 0], ["C", 30]),
  ],
};
const indice = P.creaIndice(RETE);
const minuti = (mete) => Object.fromEntries([...mete].map(([s, e]) => [s, e.minuti]));

test("senza cambi: solo stazioni sullo stesso treno, il più veloce", () => {
  assert.deepStrictEqual(minuti(P.calcolaMete(indice, "A", 0, 600)), { B: 20, C: 30, D: 80 });
});

test("un cambio aggiunge le stazioni del secondo treno", () => {
  const mete = P.calcolaMete(indice, "A", 1, 600);
  // D: A→C col treno veloce (30) + cambio sul REG 1 fino a D (30) = 60, meglio del diretto (80)
  assert.deepStrictEqual(minuti(mete), { B: 20, C: 30, D: 60, E: 55, F: 90 });
  assert.deepStrictEqual(mete.get("F").tratte, [
    { treno: 1, da: 0, a: 1 },
    { treno: 2, da: 0, a: 2 },
  ]);
});

test("i cambi massimi limitano i giri", () => {
  assert.ok(!P.calcolaMete(indice, "A", 1, 600).has("G"));
  assert.strictEqual(P.calcolaMete(indice, "A", 2, 600).get("G").minuti, 100);
});

test("il tempo massimo esclude le mete troppo lontane", () => {
  assert.deepStrictEqual(minuti(P.calcolaMete(indice, "A", 3, 59)), { B: 20, C: 30, E: 55 });
  assert.strictEqual(P.calcolaMete(indice, "A", 3, 60).get("D").minuti, 60);
});

test("si va solo avanti lungo il treno", () => {
  assert.deepStrictEqual(minuti(P.calcolaMete(indice, "C", 0, 600)), { D: 30, E: 25, F: 60 });
  assert.ok(!P.calcolaMete(indice, "B", 0, 600).has("A"));
});

test("a parità di tempo vince il percorso con meno cambi", () => {
  const rete = { stazioni: [], treni: [treno("1", ["A", 0], ["B", 10], ["C", 20]), treno("2", ["B", 0], ["C", 10])] };
  const mete = P.calcolaMete(P.creaIndice(rete), "A", 3, 600);
  assert.strictEqual(mete.get("C").tratte.length, 1);
});

test("un percorso con cambio più veloce batte il diretto lento", () => {
  const rete = {
    stazioni: [],
    treni: [treno("1", ["A", 0], ["X", 100]), treno("2", ["A", 0], ["B", 10]), treno("3", ["B", 0], ["X", 20])],
  };
  assert.strictEqual(P.calcolaMete(P.creaIndice(rete), "A", 0, 600).get("X").minuti, 100);
  assert.strictEqual(P.calcolaMete(P.creaIndice(rete), "A", 1, 600).get("X").minuti, 30);
});

test("un cambio che fa risparmiare meno della soglia non batte il diretto", () => {
  const S = P.SOGLIA_CAMBIO_MINUTI;
  const rete = (diretto) => ({
    stazioni: [],
    treni: [treno("1", ["A", 0], ["X", diretto]), treno("2", ["A", 0], ["B", 5]), treno("3", ["B", 0], ["X", 25])],
  });
  // con cambio: 30 minuti
  const lento = P.calcolaMete(P.creaIndice(rete(30 + S - 1)), "A", 1, 600).get("X");
  assert.deepStrictEqual([lento.minuti, lento.tratte.length], [30 + S - 1, 1]);
  const moltoLento = P.calcolaMete(P.creaIndice(rete(30 + S)), "A", 1, 600).get("X");
  assert.deepStrictEqual([moltoLento.minuti, moltoLento.tratte.length], [30, 2]);
});

test("la soglia vale per ogni cambio in più", () => {
  // diretto 100; 1 cambio 95 (risparmio 5: no); 2 cambi 75 (risparmio 25 ≥ 2×10: sì)
  const rete = {
    stazioni: [],
    treni: [
      treno("1", ["A", 0], ["X", 100]),
      treno("2", ["A", 0], ["B", 45]), treno("3", ["B", 0], ["X", 50]),
      treno("4", ["A", 0], ["C", 25]), treno("5", ["C", 0], ["D", 25]), treno("6", ["D", 0], ["X", 25]),
    ],
  };
  const x = P.calcolaMete(P.creaIndice(rete), "A", 2, 600).get("X");
  assert.deepStrictEqual([x.minuti, x.tratte.length], [75, 3]);
  const conUnCambio = P.calcolaMete(P.creaIndice(rete), "A", 1, 600).get("X");
  assert.deepStrictEqual([conUnCambio.minuti, conUnCambio.tratte.length], [100, 1]);
});

test("l'origine non è tra le mete e una stazione sconosciuta non dà mete", () => {
  assert.ok(!P.calcolaMete(indice, "A", 3, 600).has("A"));
  assert.strictEqual(P.calcolaMete(indice, "ZZZ", 3, 600).size, 0);
});

test("tratte: fermate, minuti e resto della tratta", () => {
  const tratta = { treno: 0, da: 0, a: 1 };
  assert.deepStrictEqual(P.fermateTratta(RETE, tratta), ["A", "B"]);
  assert.strictEqual(P.minutiTratta(RETE, tratta), 20);
  assert.deepStrictEqual(P.restoTratta(RETE, tratta), ["C", "D"]);
  assert.deepStrictEqual(P.restoTratta(RETE, { treno: 0, da: 0, a: 3 }), []);
});

test("fasce di colore", () => {
  assert.strictEqual(P.fascia(59), "verde");
  assert.strictEqual(P.fascia(60), "giallo");
  assert.strictEqual(P.fascia(120), "giallo");
  assert.strictEqual(P.fascia(121), "rosso");
});

test("formattaDurata", () => {
  assert.strictEqual(P.formattaDurata(35), "35 min");
  assert.strictEqual(P.formattaDurata(60), "1 h");
  assert.strictEqual(P.formattaDurata(125), "2 h 05");
});

test("rete reale: Torino Porta Nuova → Asti diretto in meno di un'ora", () => {
  const rete = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "docs", "data", "rete.json"), "utf8"));
  const id = (nome) => rete.stazioni.find((s) => s.nome === nome).id;
  for (const cambi of [0, 1, 3]) {
    const asti = P.calcolaMete(P.creaIndice(rete), id("Torino Porta Nuova"), cambi, 360).get(id("Asti"));
    assert.ok(asti && asti.minuti < 60 && asti.tratte.length === 1, `con ${cambi} cambi`);
  }
});

test("stazioni di cambio", () => {
  assert.deepStrictEqual(P.stazioniCambio(RETE, P.calcolaMete(indice, "A", 2, 600).get("G")), ["C", "F"]);
  assert.deepStrictEqual(P.stazioniCambio(RETE, P.calcolaMete(indice, "A", 2, 600).get("B")), []);
});
