import { test } from "node:test";
import assert from "node:assert/strict";
import { AmbiguousError, CurrencyLibrary, NotFoundError, currencies as C } from "../src/index.ts";

const close = (a: number, b: number, rel = 1e-9) => assert.ok(Math.abs(a - b) <= Math.abs(b) * rel, `${a} ≉ ${b}`);

test("lookup by id, name, alias and plural", () => {
  assert.equal(C.get("gbp").id, "gbp");
  assert.equal(C.get("sterling").id, "gbp");
  assert.equal(C.get("dollars").id, "usd");
  assert.equal(C.get("Venetian ducat (zecchino)").id, "ducat_ve");
  assert.throws(() => C.get("franc"), AmbiguousError);
  assert.throws(() => C.get("zorkmid"), NotFoundError);
});

test("findDenominations answers 'what's a florin?' across currencies", () => {
  const ids = C.findDenominations("florin").map((x) => `${x.currency.id}:${x.denomination.id}`);
  for (const id of ["gbp:florin", "florin_fl:florin", "nlg:guilder", "aut_gulden:gulden"]) assert.ok(ids.includes(id), id);
});

test("valueAt returns data points exactly and interpolates log-linearly between them", () => {
  const s = C.get("gbp").series;
  const p1800 = s.find((p) => p.year === 1800)!;
  const p1805 = s.find((p) => p.year === 1805)!;
  const exact = C.valueAt("gbp", 1800);
  assert.equal(exact.usd2025, p1800.usd2025);
  assert.equal(exact.interpolated, false);
  const mid = C.valueAt("gbp", 1802);
  assert.equal(mid.interpolated, true);
  close(mid.usd2025, Math.exp(Math.log(p1800.usd2025) + (Math.log(p1805.usd2025) - Math.log(p1800.usd2025)) * 0.4));
  assert.equal(mid.points.length, 2);
  assert.ok(mid.sources.length > 0);
});

test("out-of-range years throw unless clamped", () => {
  assert.throws(() => C.valueAt("usd", 1700), RangeError);
  const v = C.valueAt("usd", 1700, { outOfRange: "clamp" });
  assert.equal(v.clamped, true);
  assert.equal(v.usd2025, C.get("usd").series[0]!.usd2025);
});

test("time-varying denominations use the period containing the year", () => {
  close(C.denominationValue("gbp", "guinea", 1695), 1.4);
  close(C.denominationValue("gbp", "guinea", 1800), 1.05);
  close(C.denominationValue("livre", "louis", 1750), 24);
  close(C.denominationValue("livre", "louis", 1650), 10);
});

test("ambiguous denomination names are resolved by year", () => {
  assert.equal(C.denomination("gbp", "pence", 1850).id, "penny");
  assert.equal(C.denomination("gbp", "pence", 1990).id, "new_penny");
  assert.equal(C.denomination("gbp", "new_penny").id, "new_penny");
});

test("parseAmount handles £sd notations and spelled-out sums", () => {
  close(C.parseAmount("£3 4s 6d", "gbp", 1800).base, 3.225);
  close(C.parseAmount("3l. 4s. 6d.", "gbp", 1800).base, 3.225);
  close(C.parseAmount("5 shillings and 6 pence", "gbp", 1800).base, 66 / 240);
  close(C.parseAmount("2 guineas", "gbp", 1800).base, 2.1);
  close(C.parseAmount("1 half-crown", "gbp", 1800).base, 0.125);
  close(C.parseAmount("10 livres 5 sous", "livre", 1750).base, 10.25);
  close(C.parseAmount("1,000 ducats", "ducat_ve", 1600).base, 1000);
  close(C.parseAmount("30 pieces of eight", "spd", 1700).base, 30);
  close(C.parseAmount("½ crown", "gbp", 1800).base, 0.125);
  assert.throws(() => C.parseAmount("thirty pounds", "gbp", 1800));
});

test("convert goes through 2025 USD and combines ranges", () => {
  const r = C.convert(100, { currency: "livre", year: 1780 }, { currency: "gbp", year: 1780 });
  const f = C.valueAt("livre", 1780);
  const t = C.valueAt("gbp", 1780);
  close(r.amount, (100 * f.usd2025) / t.usd2025);
  close(r.low, (100 * f.low) / t.high);
  close(r.high, (100 * f.high) / t.low);
  assert.ok(r.low < r.amount && r.amount < r.high);
  assert.equal(r.confidence, "medium");
});

test("toUSD2025 applies the denomination value", () => {
  const guinea = C.toUSD2025(1, { currency: "gbp", year: 1800, denomination: "guinea" });
  close(guinea.amount, C.valueAt("gbp", 1800).usd2025 * 1.05);
  close(C.toUSD2025(1, { currency: "usd", year: 2025 }).amount, 1);
});

test("describeDenomination gives equivalents and dollar value", () => {
  const f = C.describeDenomination("gbp", "florin", 1900);
  close(f.valueInBase, 0.1);
  assert.equal(f.inUse, true);
  const shillings = f.equivalents.find((e) => e.denomination.id === "shilling")!;
  close(shillings.count, 2);
  close(f.usd2025!.perDenomination, C.valueAt("gbp", 1900).usd2025 * 0.1);
  assert.equal(C.describeDenomination("gbp", "florin", 1700).inUse, false);
});

test("breakdown and formatLsd", () => {
  const parts = C.breakdown(1.0375, "gbp", 1800, ["penny", "pound", "shilling"]);
  assert.deepEqual(parts.map((p) => [p.denomination.id, p.count]), [["pound", 1], ["shilling", 0], ["penny", 9]]);
  assert.equal(CurrencyLibrary.formatLsd(3.225), "£3 4s 6d");
  assert.equal(CurrencyLibrary.formatLsd(1 / 480), "£0 0s 0½d");
});

test("every currency's data is usable", () => {
  for (const c of C.list()) {
    const [first, last] = C.coverage(c);
    assert.ok(first <= last, c.id);
    for (const p of c.series) assert.ok(p.low <= p.usd2025 && p.usd2025 <= p.high && p.sources.length > 0, `${c.id} ${p.year}`);
    assert.ok(C.valueAt(c, Math.round((first + last) / 2)).usd2025 > 0, c.id);
    for (const d of c.denominations) assert.ok(C.denominationValue(c, d, first) > 0, `${c.id}:${d.id}`);
  }
});
