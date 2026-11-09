// Same API as index.ts, preloaded with the slim data files (no sources, notes or other descriptive fields).
import currencyJson from "../data/currencies.slim.json" with { type: "json" };
import unitJson from "../data/units.slim.json" with { type: "json" };
import type { CurrencyData, UnitData } from "./types.ts";
import { CurrencyLibrary } from "./currencies.ts";
import { UnitLibrary } from "./units.ts";

export * from "./api.ts";

/** Library preloaded with data/currencies.slim.json. */
export const currencies = new CurrencyLibrary(currencyJson as unknown as CurrencyData);

/** Library preloaded with data/units.slim.json. */
export const units = new UnitLibrary(unitJson as unknown as UnitData);
