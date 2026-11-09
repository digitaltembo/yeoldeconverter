import type { Confidence, Currency, CurrencyData, DataPoint, Denomination, Source } from "./types.ts";
import { buildIndex, lookup, normalize, preferExact } from "./text.ts";
import { AmbiguousError, NotFoundError } from "./errors.ts";

const CONFIDENCE_ORDER: Confidence[] = ["high", "medium", "low", "very low"];

function worse(a: Confidence, b: Confidence): Confidence {
  return CONFIDENCE_ORDER[Math.max(CONFIDENCE_ORDER.indexOf(a), CONFIDENCE_ORDER.indexOf(b))]!;
}

function logLerp(a: number, b: number, t: number): number {
  return Math.exp(Math.log(a) + (Math.log(b) - Math.log(a)) * t);
}

export type OutOfRange = "throw" | "clamp";

export interface ValueOptions {
  /** What to do for a year outside the currency's data: throw (default) or use the nearest data point. */
  outOfRange?: OutOfRange;
}

/** Value of one base unit of a currency in a given year, in 2025 US dollars. */
export interface CurrencyValue {
  currency: string;
  year: number;
  usd2025: number;
  low: number;
  high: number;
  confidence: Confidence;
  /** True when `year` falls between data points and the value was interpolated (log-linear). */
  interpolated: boolean;
  /** True when `year` was outside the data and the nearest point was used. */
  clamped: boolean;
  /** The data point(s) the value was derived from. */
  points: DataPoint[];
  sources: Source[];
}

export interface MoneyRef {
  currency: string;
  year: number;
  /** Denomination id/name (defaults to the base unit). */
  denomination?: string;
}

export interface Conversion {
  amount: number;
  low: number;
  high: number;
  confidence: Confidence;
  /** The intermediate value in 2025 US dollars. */
  usd2025: number;
  from: CurrencyValue;
  to: CurrencyValue;
}

export interface DenominationInfo {
  currency: Currency;
  denomination: Denomination;
  year: number;
  /** Value in base units of the currency in that year. */
  valueInBase: number;
  /** Whether the coin/unit was in use in that year (as far as the data says). */
  inUse: boolean;
  /** How many of each other denomination (with a value that year) this one is worth. */
  equivalents: { denomination: Denomination; count: number }[];
  /** Value in 2025 USD, if the currency has data covering the year. */
  usd2025?: CurrencyValue & { perDenomination: number; lowPerDenomination: number; highPerDenomination: number };
}

export interface ParsedAmount {
  currency: string;
  year: number;
  /** Total in base units. */
  base: number;
  parts: { amount: number; denomination: Denomination; base: number }[];
}

export interface BreakdownPart {
  denomination: Denomination;
  count: number;
}

export class CurrencyLibrary {
  readonly data: CurrencyData;
  readonly baseYear: number;
  private readonly byId: Map<string, Currency>;
  private readonly index: Map<string, Currency[]>;
  private readonly denomIndex: Map<string, { currency: Currency; denomination: Denomination }[]>;
  private readonly perCurrencyDenomIndex = new Map<string, Map<string, Denomination[]>>();

  constructor(data: CurrencyData) {
    this.data = data;
    this.baseYear = data.baseYear;
    this.byId = new Map(data.currencies.map((c) => [c.id, c]));
    this.index = buildIndex(data.currencies, (c) => [c.id, c.name, c.baseUnit, ...c.aliases]);
    const pairs = data.currencies.flatMap((currency) => currency.denominations.map((denomination) => ({ currency, denomination })));
    this.denomIndex = buildIndex(pairs, ({ denomination: d }) => [d.name, d.id, ...(d.aliases ?? [])]);
  }

  // ------------------------------------------------------------ lookup

  /** All currencies. */
  list(): Currency[] {
    return this.data.currencies;
  }

  /** Currencies matching an id, name, base-unit name or alias (plural forms accepted). */
  find(query: string): Currency[] {
    const exact = this.byId.get(query);
    return exact ? [exact] : lookup(this.index, query);
  }

  /** Exactly one currency by id, name or alias (real currencies win over fictional ones); throws NotFoundError / AmbiguousError. */
  get(query: string | Currency): Currency {
    if (typeof query !== "string") return query;
    let found = preferExact(this.find(query), query, (c) => [c.id, c.name, c.baseUnit, ...c.aliases]);
    if (found.length > 1 && found.some((c) => !c.fictional)) found = found.filter((c) => !c.fictional);
    if (found.length === 0) throw new NotFoundError("currency", query);
    if (found.length > 1) throw new AmbiguousError("currency", query, found.map((c) => c.id));
    return found[0]!;
  }

  /** Free-text search over currency names, aliases, regions, source works and denomination names. */
  search(text: string): Currency[] {
    const q = normalize(text);
    return this.data.currencies.filter((c) =>
      [c.id, c.name, c.region, c.baseUnit, c.work ?? "", ...c.aliases, ...c.denominations.flatMap((d) => [d.name, ...(d.aliases ?? [])])]
        .some((s) => normalize(s).includes(q)),
    );
  }

  /** Every currency that has a denomination by this name — e.g. "florin" or "crown". */
  findDenominations(query: string): { currency: Currency; denomination: Denomination }[] {
    return lookup(this.denomIndex, query);
  }

  /**
   * A denomination of one currency, by id, name, symbol or alias. The base unit is always available.
   * When a name fits several denominations (e.g. "penny" = old or decimal penny), an exact id wins,
   * then the one in use in `year`.
   */
  denomination(currency: string | Currency, query?: string, year?: number): Denomination {
    const c = this.get(currency);
    if (query === undefined) return this.baseDenomination(c);
    const byId = c.denominations.find((d) => d.id === query);
    if (byId) return byId;
    let hits = preferExact(lookup(this.currencyDenomIndex(c), query), query, (d) => [d.id, d.name, d.symbol, ...(d.aliases ?? [])]);
    if (hits.length === 0) throw new NotFoundError(`${c.id} denomination`, query);
    if (hits.length > 1 && year !== undefined) {
      const inUse = hits.filter((d) => this.denominationInUse(c, d, year));
      if (inUse.length > 0) hits = inUse;
    }
    if (hits.length > 1) throw new AmbiguousError(`${c.id} denomination`, query, hits.map((d) => d.id));
    return hits[0]!;
  }

  private baseDenomination(c: Currency): Denomination {
    return c.denominations.find((d) => d.value === 1 && !d.periods) ?? { id: c.baseUnit, name: c.baseUnit, value: 1 };
  }

  private currencyDenomIndex(c: Currency): Map<string, Denomination[]> {
    let idx = this.perCurrencyDenomIndex.get(c.id);
    if (!idx) {
      const base = this.baseDenomination(c);
      idx = buildIndex(c.denominations, (d) => [d.id, d.name, d.symbol, ...(d.aliases ?? [])]);
      for (const name of [c.baseUnit, ...c.aliases]) {
        const k = normalize(name);
        if (k && !idx.has(k)) idx.set(k, [base]);
      }
      this.perCurrencyDenomIndex.set(c.id, idx);
    }
    return idx;
  }

  /** Value of a denomination in base units of its currency in a given year. */
  denominationValue(currency: string | Currency, denomination: string | Denomination, year: number): number {
    const d = typeof denomination === "string" ? this.denomination(currency, denomination, year) : denomination;
    if (d.value !== undefined) return d.value;
    const periods = d.periods ?? [];
    if (periods.length === 0) throw new Error(`Denomination ${d.id} has no value`);
    const inside = periods.find((p) => p.from <= year && year <= p.to);
    if (inside) return inside.value;
    // Outside every period: use the nearest one.
    let best = periods[0]!;
    for (const p of periods) {
      const dist = year < p.from ? p.from - year : year - p.to;
      const bestDist = year < best.from ? best.from - year : year - best.to;
      if (dist < bestDist) best = p;
    }
    return best.value;
  }

  private denominationInUse(c: Currency, d: Denomination, year: number): boolean {
    if (d.validFrom !== undefined && year < d.validFrom) return false;
    if (d.validTo !== undefined && year > d.validTo) return false;
    if (d.periods && !d.periods.some((p) => p.from <= year && year <= p.to)) return false;
    if (c.fictional) return true;
    const [from, to] = c.era;
    return year >= from - 50 && (to === null || year <= to + 50);
  }

  /** Whether the currency has a real-world (2025 USD) value. False for some fictional currencies. */
  hasValue(currency: string | Currency): boolean {
    return this.get(currency).series.length > 0;
  }

  /** First and last year with data. Throws RangeError for a currency with no real-world value. */
  coverage(currency: string | Currency): [number, number] {
    const c = this.get(currency);
    const s = c.series;
    if (s.length === 0) throw noValue(c);
    return [s[0]!.year, s[s.length - 1]!.year];
  }

  // ------------------------------------------------------------ valuation

  /** Value of one base unit in `year`, in 2025 USD (log-linear interpolation between data points). */
  valueAt(currency: string | Currency, year: number, options: ValueOptions = {}): CurrencyValue {
    const c = this.get(currency);
    const s = c.series;
    if (s.length === 0) throw noValue(c);
    const first = s[0]!;
    const last = s[s.length - 1]!;
    const make = (p: DataPoint, clamped: boolean): CurrencyValue => ({
      currency: c.id, year, usd2025: p.usd2025, low: p.low, high: p.high, confidence: p.confidence,
      interpolated: false, clamped, points: [p], sources: p.sources ?? [],
    });
    // a fictional currency's single estimate is timeless
    if (c.fictional) return make(first, false);
    if (year < first.year || year > last.year) {
      if (options.outOfRange !== "clamp") {
        throw new RangeError(`${c.name}: no data for ${year} (data covers ${first.year}–${last.year})`);
      }
      return make(year < first.year ? first : last, true);
    }
    let i = 0;
    while (i < s.length - 1 && s[i + 1]!.year <= year) i++;
    const a = s[i]!;
    if (a.year === year || i === s.length - 1) return make(a, false);
    const b = s[i + 1]!;
    const t = (year - a.year) / (b.year - a.year);
    return {
      currency: c.id, year,
      usd2025: logLerp(a.usd2025, b.usd2025, t),
      low: logLerp(a.low, b.low, t),
      high: logLerp(a.high, b.high, t),
      confidence: worse(a.confidence, b.confidence),
      interpolated: true, clamped: false, points: [a, b],
      sources: [...(a.sources ?? []), ...(b.sources ?? [])],
    };
  }

  /** Value of `amount` of a denomination (default: base unit) in `year`, in 2025 USD. */
  toUSD2025(amount: number, ref: MoneyRef, options: ValueOptions = {}): Conversion {
    return this.convert(amount, ref, { currency: "usd", year: this.baseYear }, options);
  }

  /**
   * Convert an amount between currencies/years by equal purchasing power:
   * `amount` of `from` → 2025 USD → the equivalent amount of `to` in its year.
   * The low/high range combines the uncertainty of both ends.
   */
  convert(amount: number, from: MoneyRef, to: MoneyRef, options: ValueOptions = {}): Conversion {
    const fc = this.get(from.currency);
    const tc = this.get(to.currency);
    const fv = this.valueAt(fc, from.year, options);
    const tv = this.valueAt(tc, to.year, options);
    const fd = this.denominationValue(fc, this.denomination(fc, from.denomination, from.year), from.year);
    const td = this.denominationValue(tc, this.denomination(tc, to.denomination, to.year), to.year);
    const base = amount * fd;
    return {
      amount: (base * fv.usd2025) / (tv.usd2025 * td),
      low: (base * fv.low) / (tv.high * td),
      high: (base * fv.high) / (tv.low * td),
      confidence: worse(fv.confidence, tv.confidence),
      usd2025: base * fv.usd2025,
      from: fv,
      to: tv,
    };
  }

  // ------------------------------------------------------------ denominations

  /** What a denomination is worth in a year, relative to the others and in 2025 USD — "what's a florin?" */
  describeDenomination(currency: string | Currency, denomination: string, year: number): DenominationInfo {
    const c = this.get(currency);
    const d = this.denomination(c, denomination, year);
    const valueInBase = this.denominationValue(c, d, year);
    const equivalents = c.denominations
      .filter((o) => o.id !== d.id && this.denominationInUse(c, o, year))
      .map((o) => ({ denomination: o, count: valueInBase / this.denominationValue(c, o, year) }));
    const info: DenominationInfo = { currency: c, denomination: d, year, valueInBase, inUse: this.denominationInUse(c, d, year), equivalents };
    const covered = this.hasValue(c) && (c.fictional || (year >= this.coverage(c)[0] && year <= this.coverage(c)[1]));
    if (covered) {
      const v = this.valueAt(c, year);
      info.usd2025 = { ...v, perDenomination: v.usd2025 * valueInBase, lowPerDenomination: v.low * valueInBase, highPerDenomination: v.high * valueInBase };
    }
    return info;
  }

  /**
   * Parse a written sum such as "£3 4s 6d", "3l. 4s. 6d.", "5 shillings and 6 pence",
   * "2 guineas", "10 livres 5 sous" or "½ crown" into base units of `currency`.
   */
  parseAmount(text: string, currency: string | Currency, year: number): ParsedAmount {
    const c = this.get(currency);
    const idx = this.currencyDenomIndex(c);
    const parts: ParsedAmount["parts"] = [];
    const re = /([£$€¥ƒ])?\s*(\d+\s*\/\s*\d+|(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:\s*[½¼¾])?|[½¼¾])\s*([^\d£$€¥ƒ½¼¾]*)/gu;
    for (const m of text.matchAll(re)) {
      const [, symbol, num = "", rest = ""] = m;
      const amount = parseNumber(num);
      let d: Denomination | undefined;
      if (symbol) {
        d = this.pickInUse(c, lookup(idx, symbol), year);
        if (!d) throw new NotFoundError(`${c.id} denomination`, symbol);
      }
      const unitText = rest.replace(/[,;]/g, " ").trim().replace(/\s+(and|&)$/i, "").replace(/^(of|in)\s+/i, "");
      if (!d) {
        d = this.longestDenominationPrefix(c, idx, unitText, year);
        if (!d) throw new NotFoundError(`${c.id} denomination`, unitText || text);
      }
      const base = amount * this.denominationValue(c, d, year);
      parts.push({ amount, denomination: d, base });
    }
    if (parts.length === 0) throw new Error(`No amount found in "${text}"`);
    return { currency: c.id, year, base: parts.reduce((s, p) => s + p.base, 0), parts };
  }

  private longestDenominationPrefix(c: Currency, idx: Map<string, Denomination[]>, unitText: string, year: number): Denomination | undefined {
    const words = unitText.split(/\s+/).filter(Boolean);
    for (let n = words.length; n > 0; n--) {
      const hit = this.pickInUse(c, lookup(idx, words.slice(0, n).join(" ")), year);
      if (hit) return hit;
    }
    return undefined;
  }

  private pickInUse(c: Currency, hits: Denomination[], year: number): Denomination | undefined {
    return hits.find((d) => this.denominationInUse(c, d, year)) ?? hits[0];
  }

  /**
   * Split an amount (in base units) into whole counts of the given denominations, largest first,
   * e.g. 1.0375 pounds → [1 pound, 0 shillings, 9 pence] for ["pound", "shilling", "penny"].
   * The smallest denomination absorbs any remainder (and may be fractional).
   */
  breakdown(amountBase: number, currency: string | Currency, year: number, denominations: string[]): BreakdownPart[] {
    const c = this.get(currency);
    const ds = denominations
      .map((q) => this.denomination(c, q, year))
      .map((d) => ({ d, v: this.denominationValue(c, d, year) }))
      .sort((a, b) => b.v - a.v);
    let rest = amountBase;
    return ds.map(({ d, v }, i) => {
      const lastOne = i === ds.length - 1;
      const raw = rest / v;
      const count = lastOne ? Math.round(raw * 1e6) / 1e6 : Math.floor(raw + 1e-9);
      rest -= count * v;
      return { denomination: d, count };
    });
  }

  /** Format pounds as "£L Ns Nd" (pre-decimal sterling style; works for any £sd-structured currency). */
  static formatLsd(pounds: number): string {
    const totalPence = Math.round(pounds * 240 * 4) / 4;
    const l = Math.floor(totalPence / 240);
    const s = Math.floor((totalPence - l * 240) / 12);
    const d = totalPence - l * 240 - s * 12;
    const whole = Math.floor(d);
    const frac = { 0: "", 0.25: "¼", 0.5: "½", 0.75: "¾" }[d - whole] ?? "";
    return `£${l} ${s}s ${whole}${frac}d`;
  }
}

function parseNumber(s: string): number {
  const fractions: Record<string, number> = { "½": 0.5, "¼": 0.25, "¾": 0.75 };
  const t = s.replace(/\s+/g, "");
  if (t.includes("/")) {
    const [a, b] = t.split("/");
    return Number(a) / Number(b);
  }
  const last = t.slice(-1);
  if (last in fractions) return (t.length > 1 ? Number(t.slice(0, -1)) : 0) + fractions[last]!;
  return Number(t.replace(/,/g, ""));
}

function noValue(c: Currency): RangeError {
  return new RangeError(`${c.name} has no established real-world value${c.work ? ` (${c.work})` : ""}`);
}
