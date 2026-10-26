const test = require("node:test");
const assert = require("node:assert");
const { VERSIONE } = require("../docs/versione.js");

test("la versione ha formato X.Y.Z", () => {
  assert.match(VERSIONE, /^\d+\.\d+\.\d+$/);
});
