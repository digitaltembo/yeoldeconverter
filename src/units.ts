import type { Precision, Unit, UnitCategory, UnitData } from "./types.ts";
import { buildIndex, lookup, normalize, preferExact } from "./text.ts";
import { AmbiguousError, IncompatibleUnitsError, NotFoundError } from "./errors.ts";

const PRECISION_ORDER: Precision[] = ["exact", "approximate", "uncertain"];

function worse(a: Precision, b: Precision): Precision {
  return PRECISION_ORDER[Math.max(PRECISION_ORDER.indexOf(a), PRECISION_ORDER.indexOf(b))]!;
}

export interface UnitConversion {
  value: number;
  /** Plausible range, combining the uncertainty of both units. Equal to `value` for exact units. */
  low: number;
  high: number;
  precision: Precision;
  from: Unit;
  to: Unit;
}

export interface DefinitionStep {
  unit: Unit;
  /** How `unit` is defined: "220 × yard", "square of ken", or a base value. */
  text: string;
  /** Value of `unit` in base units at this step. */
  si: number;
}

export interface SearchOptions {
  category?: UnitCategory;
  /** Substring match on the unit's system, e.g. "Roman", "Japanese". */
  system?: string;
}

export class UnitLibrary {
  readonly data: UnitData;
  private readonly byId: Map<string, Unit>;
  private readonly index: Map<string, Unit[]>;

  constructor(data: UnitData) {
    this.data = data;
    this.byId = new Map(data.units.map((u) => [u.id, u]));
    this.index = buildIndex(data.units, (u) => [u.id, u.name, ...u.aliases]);
  }

  /** All units, optionally of one category. */
  list(category?: UnitCategory): Unit[] {
    return category ? this.data.units.filter((u) => u.category === category) : this.data.units;
  }

  /** Units matching an id, name or alias (plural forms accepted), optionally filtered. */
  find(query: string, options: SearchOptions = {}): Unit[] {
    const exact = this.byId.get(query);
    const hits = exact ? [exact] : lookup(this.index, query);
    return hits.filter((u) => matches(u, options));
  }

  /** Exactly one unit by id, name or alias; throws NotFoundError / AmbiguousError (e.g. "cubit"). */
  get(query: string | Unit, options: SearchOptions = {}): Unit {
    if (typeof query !== "string") return query;
    const found = preferExact(this.find(query, options), query, (u) => [u.id, u.name, ...u.aliases]);
    if (found.length === 0) throw new NotFoundError("unit", query);
    if (found.length > 1) throw new AmbiguousError("unit", query, found.map((u) => u.id));
    return found[0]!;
  }

  /** Free-text search over names, aliases, systems, regions, notes and source works. */
  search(text: string, options: SearchOptions = {}): Unit[] {
    const q = normalize(text);
    return this.data.units.filter(
      (u) => matches(u, options) && [u.id, u.name, u.system, u.region ?? "", u.notes ?? "", u.work ?? "", ...u.aliases].some((s) => normalize(s).includes(q)),
    );
  }

  /** Convert `amount` of one unit to another unit of the same category. */
  convert(amount: number, from: string | Unit, to: string | Unit): UnitConversion {
    const f = this.get(from);
    const t = this.get(to);
    if (f.category !== t.category) throw new IncompatibleUnitsError(f.id, f.category, t.id, t.category);
    return {
      value: (amount * f.si) / t.si,
      low: (amount * (f.low ?? f.si)) / (t.high ?? t.si),
      high: (amount * (f.high ?? f.si)) / (t.low ?? t.si),
      precision: worse(f.precision, t.precision),
      from: f,
      to: t,
    };
  }

  /** How many `b` make one `a` — e.g. ratio("furlong", "chain") = 10. */
  ratio(a: string | Unit, b: string | Unit): number {
    return this.convert(1, a, b).value;
  }

  /** The chain of definitions from a unit down to its base value, e.g. furlong → yard → foot → inch → 0.0254 m. */
  definitionChain(unit: string | Unit): DefinitionStep[] {
    const steps: DefinitionStep[] = [];
    let u: Unit | undefined = this.get(unit);
    const seen = new Set<string>();
    while (u && !seen.has(u.id)) {
      seen.add(u.id);
      const d = u.definition;
      const base = this.data.baseUnits[u.category];
      let text: string;
      let next: Unit | undefined;
      if (d.type === "base") {
        text = `${fmt(u.si)} ${base}`;
      } else {
        next = this.byId.get(d.of);
        const name = next?.name ?? d.of;
        text = d.type === "multiple" ? `${fmtFactor(d.factor)} × ${name}` : `${d.type === "square" ? "square" : "cube"} of ${name}`;
      }
      steps.push({ unit: u, text, si: u.si });
      u = next;
    }
    return steps;
  }

  /** A one-line explanation, e.g. "Furlong = 220 × Yard = 201.168 m (exact)". */
  explain(unit: string | Unit): string {
    const u = this.get(unit);
    const [first] = this.definitionChain(u);
    const base = this.data.baseUnits[u.category];
    const range = u.precision === "uncertain" && u.low !== undefined ? ` (range ${fmt(u.low)}–${fmt(u.high!)} ${base})` : "";
    const def = first && u.definition.type !== "base" ? ` = ${first.text}` : "";
    return `${u.name}${def} = ${fmt(u.si)} ${base}, ${u.precision}${range}`;
  }

  /** Express `amount` of a unit in several other units (default: every unit of the category in the same system). */
  equivalents(amount: number, unit: string | Unit, targets?: (string | Unit)[]): UnitConversion[] {
    const u = this.get(unit);
    const ts = targets ? targets.map((t) => this.get(t)) : this.list(u.category).filter((o) => o.system === u.system && o.id !== u.id);
    return ts.map((t) => this.convert(amount, u, t));
  }
}

function matches(u: Unit, o: SearchOptions): boolean {
  if (o.category && u.category !== o.category) return false;
  if (o.system && !normalize(u.system).includes(normalize(o.system))) return false;
  return true;
}

function fmt(x: number): string {
  return Number(x.toPrecision(6)).toString();
}

function fmtFactor(f: number): string {
  if (f >= 1) return fmt(f);
  const inv = 1 / f;
  return Math.abs(inv - Math.round(inv)) < 1e-9 ? `1/${Math.round(inv)}` : fmt(f);
}
