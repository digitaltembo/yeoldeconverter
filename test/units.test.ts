import { test } from "node:test";
import assert from "node:assert/strict";
import { AmbiguousError, IncompatibleUnitsError, NotFoundError, units as U } from "../src/index.ts";

const close = (a: number, b: number, rel = 1e-9) => assert.ok(Math.abs(a - b) <= Math.abs(b) * rel, `${a} ≉ ${b}`);

test("lookup by id, name, alias and plural; exact names win", () => {
  assert.equal(U.get("feet").id, "foot");
  assert.equal(U.get("square feet").id, "sq_foot");
  assert.equal(U.get("pood").id, "pud");
  assert.equal(U.get("pound").id, "lb");
  assert.equal(U.get("stadia").id, "stadion");
  assert.equal(U.get("furlong").id, "furlong");
  assert.throws(() => U.get("cubit"), AmbiguousError);
  assert.throws(() => U.get("gallon"), AmbiguousError);
  assert.throws(() => U.get("zorkmid"), NotFoundError);
  assert.equal(U.get("talent", { system: "Greek" }).id, "talent_att");
});

test("exact conversions match legal definitions", () => {
  close(U.convert(1, "mile", "metre").value, 1609.344);
  close(U.convert(1, "acre", "sq_metre").value, 4046.8564224);
  close(U.convert(1, "gal_us", "litre").value, 3.785411784);
  close(U.convert(1, "gal_imp", "litre").value, 4.54609);
  close(U.convert(1, "oz_troy", "grain").value, 480);
  close(U.convert(1, "stone", "kilogram").value, 6.35029318);
  assert.equal(U.ratio("furlong", "chain"), 10);
  assert.equal(U.ratio("hogshead_wine", "gal_us"), 63);
  assert.equal(U.convert(1, "mile", "foot").precision, "exact");
});

test("uncertain units carry a range through conversion", () => {
  const r = U.convert(10, "cubit_bib", "foot");
  assert.equal(r.precision, "uncertain");
  assert.ok(r.low < r.value && r.value < r.high);
  close(r.low, (10 * 0.444) / 0.3048);
});

test("cannot convert across categories", () => {
  assert.throws(() => U.convert(1, "acre", "foot"), IncompatibleUnitsError);
});

test("definitionChain walks to the base value", () => {
  assert.deepEqual(U.definitionChain("furlong").map((s) => s.text), ["220 × Yard", "3 × Foot", "12 × Inch", "0.0254 m"]);
  assert.deepEqual(U.definitionChain("tsubo").map((s) => s.unit.id), ["tsubo", "ken", "shaku"]);
  assert.match(U.explain("hogshead_wine"), /63 × Gallon .* = 238\.481 L, exact/);
});

test("search and equivalents", () => {
  assert.ok(U.search("roman", { category: "length" }).some((u) => u.id === "pes"));
  const eq = U.equivalents(1, "mile", ["furlong", "chain", "yard"]);
  assert.deepEqual(eq.map((e) => e.value), [8, 80, 1760]);
});

test("astronomical, atomic, novelty and Planck units", () => {
  close(U.convert(1, "parsec", "au").value, 648000 / Math.PI);
  close(U.convert(1, "parsec", "light_year").value, 3.26156, 1e-5);
  close(U.convert(1, "loghqam", "light_year").value, 1.25);
  close(U.convert(364.4, "smoot", "metre").value, 620.14, 1e-4);
  assert.equal(U.get("angstroms").id, "angstrom");
  assert.equal(U.get("Å").id, "angstrom");
  close(U.convert(5000, "angstrom", "metre").value, 5e-7);
  close(U.convert(1, "planck_area", "sq_metre").value, 1.616255e-35 ** 2, 1e-12);
  close(U.convert(1, "planck_mass", "kilogram").value, 2.176434e-8);
  assert.equal(U.get("parsecs").precision, "exact");
});

test("fictional units", () => {
  close(U.convert(70, "glumgluff", "foot").value, 6);
  close(U.convert(1, "lar", "yard").value, 190000 / 36);
  assert.equal(U.get("kellicam").precision, "uncertain");
  assert.ok(U.search("tolkien").some((u) => u.id === "ranga"));
  assert.ok(U.list().filter((u) => u.fictional).every((u) => u.work && u.precision !== "exact"));
});

test("every unit resolves and has sources", () => {
  for (const u of U.list()) {
    assert.ok(u.si > 0 && u.sources.length > 0, u.id);
    if (u.precision === "uncertain") assert.ok(u.low! <= u.si && u.si <= u.high!, u.id);
    assert.ok(U.definitionChain(u).length >= 1, u.id);
  }
});
