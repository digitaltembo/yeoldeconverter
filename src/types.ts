// Shapes of data/currencies.json and data/units.json.

export interface Source {
  title: string;
  url: string;
  reasoning: string;
}

// ---------------------------------------------------------------- currencies

export type Confidence = "high" | "medium" | "low" | "very low";

export interface DenominationPeriod {
  from: number;
  to: number;
  /** Value in base units of the currency during [from, to] (inclusive). */
  value: number;
}

export interface Denomination {
  id: string;
  name: string;
  symbol?: string;
  /** Value in base units of the currency (absent when `periods` is given). */
  value?: number;
  periods?: DenominationPeriod[];
  validFrom?: number;
  validTo?: number;
  aliases?: string[];
  notes?: string;
}

export interface DataPoint {
  year: number;
  usd2025: number;
  low: number;
  high: number;
  confidence: Confidence;
  method: string;
  provenance: "computed" | "compiled";
  sources: Source[];
}

export interface Currency {
  id: string;
  name: string;
  region: string;
  /** [first year, last year]; null = still in use. */
  era: [number, number | null];
  baseUnit: string;
  aliases: string[];
  notes: string;
  denominations: Denomination[];
  series: DataPoint[];
  successor?: string;
}

export interface CurrencyData {
  schemaVersion: number;
  title: string;
  baseYear: number;
  unit: string;
  generated: string;
  methodology: Record<string, unknown>;
  currencies: Currency[];
}

// ---------------------------------------------------------------- units

export type UnitCategory = "length" | "area" | "volume" | "mass" | "count";
export type Precision = "exact" | "approximate" | "uncertain";

export type UnitDefinition =
  | { type: "base" }
  | { type: "multiple"; factor: number; of: string }
  | { type: "square"; of: string }
  | { type: "cube"; of: string };

export interface Unit {
  id: string;
  name: string;
  category: UnitCategory;
  subcategory?: "liquid" | "dry";
  system: string;
  region: string;
  era: [number | null, number | null];
  aliases: string[];
  /** Value in the category's base unit (m, m², L, kg, each). */
  si: number;
  siUnit: string;
  precision: Precision;
  low?: number;
  high?: number;
  definition: UnitDefinition;
  notes?: string;
  sources: Source[];
}

export interface UnitData {
  schemaVersion: number;
  title: string;
  generated: string;
  baseUnits: Record<UnitCategory, string>;
  notes: string[];
  units: Unit[];
}
