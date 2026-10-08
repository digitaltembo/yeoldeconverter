import currencyJson from "../data/currencies.json" with { type: "json" };
import unitJson from "../data/units.json" with { type: "json" };
import type { CurrencyData, UnitData } from "./types.ts";
import { CurrencyLibrary } from "./currencies.ts";
import { UnitLibrary } from "./units.ts";

export * from "./types.ts";
export * from "./errors.ts";
export { CurrencyLibrary } from "./currencies.ts";
export type { BreakdownPart, Conversion, CurrencyValue, DenominationInfo, MoneyRef, OutOfRange, ParsedAmount, ValueOptions } from "./currencies.ts";
export { UnitLibrary } from "./units.ts";
export type { DefinitionStep, SearchOptions, UnitConversion } from "./units.ts";

/** Library preloaded with data/currencies.json. */
export const currencies = new CurrencyLibrary(currencyJson as unknown as CurrencyData);

/** Library preloaded with data/units.json. */
export const units = new UnitLibrary(unitJson as unknown as UnitData);
