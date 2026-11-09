// Shapes of data/currencies.json and data/units.json.
// The slim files (*.slim.json) have the same shape with the descriptive fields marked "omitted in slim data" left out.

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
  /** Omitted in slim data. */
  notes?: string;
}

export interface DataPoint {
  year: number;
  usd2025: number;
  low: number;
  high: number;
  confidence: Confidence;
  /** Omitted in slim data. */
  method?: string;
  /** Omitted in slim data. */
  provenance?: "computed" | "compiled";
  /** Omitted in slim data. */
  sources?: Source[];
}

export interface Currency {
  id: string;
  name: string;
  region: string;
  /** [first year, last year]; null = still in use. */
  era: [number, number | null];
  baseUnit: string;
  aliases: string[];
  /** Omitted in slim data. */
  notes?: string;
  denominations: Denomination[];
  /** Value of one base unit over time. Empty for fictional currencies with no defensible real-world value. */
  series: DataPoint[];
  successor?: string;
  /** True for currencies from novels, films and games; their value (if any) does not depend on the year. */
  fictional?: boolean;
  /** The work a fictional currency comes from. */
  work?: string;
  /** Sources for a fictional currency's denominations and exchange rates. Omitted in slim data. */
  sources?: Source[];
}

export interface CurrencyData {
  schemaVersion: number;
  title: string;
  baseYear: number;
  unit: string;
  generated: string;
  /** True for the slim file. */
  slim?: boolean;
  /** Omitted in slim data. */
  methodology?: Record<string, unknown>;
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
  /** Omitted in slim data. */
  region?: string;
  /** Omitted in slim data. */
  era?: [number | null, number | null];
  aliases: string[];
  /** Value in the category's base unit (m, m², L, kg, each). */
  si: number;
  /** Omitted in slim data (it is `baseUnits[category]`). */
  siUnit?: string;
  precision: Precision;
  low?: number;
  high?: number;
  definition: UnitDefinition;
  /** Omitted in slim data. */
  notes?: string;
  /** Omitted in slim data. */
  sources?: Source[];
  /** True for units from novels and films. */
  fictional?: boolean;
  /** The work a fictional unit comes from. Omitted in slim data. */
  work?: string;
}

export interface UnitData {
  schemaVersion: number;
  title: string;
  generated: string;
  /** True for the slim file. */
  slim?: boolean;
  baseUnits: Record<UnitCategory, string>;
  /** Omitted in slim data. */
  notes?: string[];
  units: Unit[];
}
