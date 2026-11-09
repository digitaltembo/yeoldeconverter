import { test } from "node:test";
import assert from "node:assert/strict";
import { CurrencyLibrary, UnitLibrary, currencies as fullC, units as fullU } from "../src/index.ts";
import type { CurrencyData, UnitData } from "../src/index.ts";
import slimCurrencies from "../data/currencies.slim.json" with { type: "json" };
import slimUnits from "../data/units.slim.json" with { type: "json" };
import * as slimEntry from "../src/slim.ts";

const C = new CurrencyLibrary(slimCurrencies as CurrencyData);
const U = new UnitLibrary(slimUnits as UnitData);

test("slim data drops sources and descriptive fields", () => {
  const text = JSON.stringify(slimCurrencies) + JSON.stringify(slimUnits);
  for (const key of ['"sources"', '"reasoning"', '"method"', '"notes"', '"methodology"']) assert.ok(!text.includes(key), key);
  assert.equal(C.data.slim, true);
  assert.equal(U.data.slim, true);
});

test("slim data converts exactly like the full data", () => {
  for (const c of fullC.list()) {
    assert.deepEqual(C.get(c.id).denominations.map((d) => d.id), c.denominations.map((d) => d.id), c.id);
    for (const p of c.series) {
      const a = C.valueAt(c.id, p.year);
      const b = fullC.valueAt(c.id, p.year);
      assert.deepEqual([a.usd2025, a.low, a.high, a.confidence], [b.usd2025, b.low, b.high, b.confidence], `${c.id} ${p.year}`);
    }
  }
  const slim = C.convert(100, { currency: "livre", year: 1780 }, { currency: "gbp", year: 1780 });
  const full = fullC.convert(100, { currency: "livre", year: 1780 }, { currency: "gbp", year: 1780 });
  assert.deepEqual([slim.amount, slim.low, slim.high], [full.amount, full.low, full.high]);
  assert.equal(slim.from.sources.length, 0);
  assert.equal(C.parseAmount("£3 4s 6d", "gbp", 1800).base, 3.225);

  for (const u of fullU.list()) {
    const s = U.get(u.id);
    assert.deepEqual([s.si, s.low, s.high, s.precision], [u.si, u.low, u.high, u.precision], u.id);
  }
  assert.equal(U.convert(1, "furlong", "chain").value, fullU.convert(1, "furlong", "chain").value);
  assert.deepEqual(U.definitionChain("furlong").map((s) => s.text), fullU.definitionChain("furlong").map((s) => s.text));
});

test("the slim entry point preloads the slim data with the same API", () => {
  assert.equal(slimEntry.currencies.data.slim, true);
  assert.equal(slimEntry.units.data.slim, true);
  assert.equal(slimEntry.CurrencyLibrary, CurrencyLibrary);
  assert.equal(slimEntry.units.ratio("furlong", "chain"), 10);
});
