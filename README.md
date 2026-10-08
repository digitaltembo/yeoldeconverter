# Ye Olde Converter

`data/currencies.json` gives approximate values in **2025 US dollars** for 35 historical and modern currencies, plus how their denominations relate to each other (what's a florin, a groat, a moidore?). It's meant to help make sense of sums of money in historical books. Each value answers one question: *how many 2025 dollars buy the same consumer goods that one unit of this currency bought in that year?*

Data points are spaced 5 years apart where the evidence supports it, and further apart for medieval and ancient currencies. Each data point has its own list of sources, and each source comes with a link and the reasoning for that step of the calculation.

## Files

| Path | What it is |
|---|---|
| `data/currencies.json` | The dataset |
| `data/source-series.json` | Price-index and exchange-rate series pulled from the downloaded datasets |
| `scripts/extract_series.py` | Rebuilds `source-series.json` from the raw downloads (BoE workbook, ONS CSV, Minneapolis Fed page) |
| `scripts/build_currencies.py` | Builds `currencies.json`. All hand-compiled rates, metal contents and denominations live here |
| `data/units.json` | 341 historical and modern units of length, area, volume, mass and count (see [Units of measurement](#units-of-measurement)) |
| `scripts/build_units.py` | Builds `units.json` from unit definitions |
| `src/` | TypeScript library for converting and looking up currencies and units (see [TypeScript library](#typescript-library)) |
| `test/` | Tests for the library (`node:test`) |
| `example/index.html` | Browser demo using the minified bundle (see [Example page](#example-page)) |

To rebuild after editing:

```sh
python3 scripts/build_currencies.py data/source-series.json data/currencies.json
python3 scripts/build_units.py data/units.json
```

## TypeScript library

`src/` is a small library over the two JSON files. It has no runtime dependencies and works in Node 22.6+ or with any bundler that supports JSON imports.

```sh
npm install
npm test          # runs test/*.test.ts directly (Node's built-in TypeScript type stripping)
npm run build     # compiles to dist/ (JS + .d.ts, with the JSON copied alongside)
npm run bundle    # single minified files with the data inlined (see below)
```

### Single-file bundles

`npm run bundle` uses esbuild to produce two self-contained, minified files, with both datasets inlined:

| File | Format | Use |
|---|---|---|
| `dist/yeoldeconverter.min.js` | ES module | `import { currencies, units } from "./yeoldeconverter.min.js"`, or the package subpath `yeoldeconverter/bundle` |
| `dist/yeoldeconverter.iife.min.js` | Classic script | `<script src="yeoldeconverter.iife.min.js"></script>`, then `YeOldeConverter.currencies` / `YeOldeConverter.units` |

Each file is about 2.5 MB, or about 140 KB gzipped, since servers compress the repetitive source text very well. Almost all of that is the per-data-point source citations. The bundles target ES2020.

### Example page

`example/index.html` is a self-contained demo built on the IIFE bundle. Run `npm run bundle`, then open the file in a browser; no server is needed. It has two tabs:

- **Money**
  - Pick a currency and year, then type a sum the way a book writes it (`£3 4s 6d`, `2 guineas`, `30 denarii`, `3 bu`) or a plain number plus a coin.
  - It shows the 2025-dollar value and its plausible range, what the confidence level means, a plain-language explanation, and a chart of the currency's value over time.
  - The method and the sources (with reasoning) for the data points used appear below the result.
  - A comparison panel converts the sum to another currency or year.
  - A table lists the currency's coins for that year, with their value in the base unit and in today's dollars. Click a row to value that coin.
- **Measures**
  - Pick a kind of measure and two units, grouped by measuring system.
  - It shows the converted value (with a range for uncertain units), the precision level and what it means, and the equivalent in familiar modern units.
  - A card for each unit gives its definition chain, region, era, notes and sources.

```ts
import { currencies, units, CurrencyLibrary } from "yeoldeconverter";

// What is a sum worth today?
const sum = currencies.parseAmount("£3 4s 6d", "gbp", 1815);   // → base: 3.225 (pounds)
currencies.toUSD2025(sum.base, { currency: "gbp", year: 1815 });
// → { amount, low, high, confidence, from: { points, sources, ... }, ... }

// Equal purchasing power between currencies and years
currencies.convert(100, { currency: "livre", year: 1780 }, { currency: "gbp", year: 1780 });
currencies.convert(1, { currency: "gbp", year: 1850, denomination: "guinea" }, { currency: "usd", year: 1850 });

// "What's a florin?"
currencies.findDenominations("florin");             // British 2s coin, Florentine florin, Dutch guilder, Austrian gulden…
currencies.describeDenomination("gbp", "florin", 1900);
// → valueInBase 0.1, equivalents [2 shillings, 24 pence, …], usd2025.perDenomination ≈ $16

currencies.breakdown(1.0375, "gbp", 1800, ["pound", "shilling", "penny"]); // 1 pound, 0 shillings, 9 pence
CurrencyLibrary.formatLsd(3.225);                  // "£3 4s 6d"

// Units
units.convert(3, "league", "kilometre");          // { value: 14.48, low, high, precision: "exact" }
units.convert(10, "cubit_bib", "foot");           // { value: 14.99, low: 14.57, high: 15.75, precision: "uncertain" }
units.ratio("furlong", "chain");                  // 10
units.definitionChain("furlong").map((s) => s.text); // ["220 × Yard", "3 × Foot", "12 × Inch", "0.0254 m"]
units.explain("hogshead_wine");                   // "Hogshead (wine) = 63 × Gallon (US / wine / Queen Anne) = 238.481 L, exact"
units.search("roman", { category: "length" });
units.get("talent", { system: "Greek" });
```

### Behaviour worth knowing

- **Lookups** accept ids, names, aliases and plurals ("pence", "denarii", "pieces of eight", "stadia", "square feet"). `get` returns exactly one match. It throws `NotFoundError` when nothing matches, or `AmbiguousError` (with `candidates`) when a name is genuinely ambiguous, such as "gallon" (US or imperial), "cubit" or "franc"; in that case use an id or a `system`/`category` filter. A name that matches exactly beats a looser match, so "pound" is the avoirdupois pound rather than "Pound (troy)". `find` returns every match.
- **Denominations depend on the year.** A guinea is 21s from 1717 but about 30s in 1695. "Pence" means old pence before 1971 and decimal pence after. A louis d'or is 10, 12, 20 or 24 livres depending on the year.
- **Currency values between data points** are interpolated linearly in log space, and the confidence used is the worse of the two neighbouring points. Years outside a currency's data throw a `RangeError`, unless you pass `{ outOfRange: "clamp" }` to use the nearest point.
- **Ranges:** `low`/`high` on conversions combine the uncertainty of both ends (for example the source's low against the target's high). Every result keeps the underlying data points and their sources, so a UI can show them.
- **`parseAmount`** reads £sd notation (`£3 4s 6d`, `3l. 4s. 6d.`), spelled-out sums (`5 shillings and 6 pence`, `2 guineas`), thousands separators and ½/¼/¾. It does not read amounts written as words ("thirty pounds").
- **Your own data:** `currencies` and `units` come preloaded with the bundled JSON. You can also construct `new CurrencyLibrary(data)` or `new UnitLibrary(data)` with other data.

## Currencies covered

| Region | Currencies |
|---|---|
| British Isles | Pound sterling (1210–2025), pound Scots (1370–1705), Irish pound (1705–1825) |
| Americas | US dollar (1795–2025), Spanish dollar / piece of eight (1575–1850) |
| France | Livre tournois (1270–1795), franc (1800–1955), new franc (1960–2000) |
| German lands | Prussian thaler (1750–1870), mark (1875–1920), Reichsmark (1925–1940), Deutsche Mark (1950–2000) |
| Austria | Gulden (1760–1890), krone (1895–1910) |
| Italy | Florentine florin (1255–1530), Venetian ducat (1285–1795), Italian lira (1865–2000) |
| Rest of Europe | Dutch guilder (1600–2000), Portuguese milréis (1725–1890), Russian ruble (1705–1915), Swiss franc, Swedish krona, Spanish peseta, euro |
| Asia | Ryō (1605–1865), yen (1870–2025), Chinese silver tael (1650–1930), renminbi (1955–2025), Indian rupee (1600–2025) |
| Ottoman | Akçe (1330–1685), kuruş/piastre (1690–1910) |
| Antiquity | Roman denarius, Late Roman/Byzantine solidus, Athenian drachma, shekel |

## How values are derived

1. **Express the currency in pounds or dollars of its own time.**
   - Up to 1910 the reference money is the **pound sterling**. Other currencies are converted using:
     - their silver or gold content, valued against English coinage. Before 1717 that means the silver in the English penny plus an estimated gold:silver ratio. From 1717 it means Britain's gold standard, £1 = 7.3224 g of gold, plus market gold:silver ratios.
     - or a legal parity, such as the gold-standard rates (£1 = 20.43 marks = 25.22 francs) or the Latin Monetary Union.
     - or a known exchange rate.
   - From 1915 the reference money is the **US dollar**, reached through annual exchange rates. Wartime and controlled rates are marked with lower confidence.
2. **Adjust for inflation to 2025** using consumer price indexes.
   - UK: the Bank of England's millennium dataset (1209–2016), joined to the ONS CPI series D7BT (2017–2025). Both use 2015 = 100, so they join directly.
   - US: the Minneapolis Fed CPI series (1800–2025).
3. **Convert 2025 pounds to dollars** at the 2025 annual average, $1.3192 per £ (Federal Reserve G.5A).
4. **Where no price index exists** (antiquity, Edo Japan), values are estimated from what the money bought in staple goods: wheat, barley or rice. For antiquity, ancient grain prices are compared with a modern price of about $4/kg of wheat-equivalent. For the ryō, the Bank of Japan's rice-price rule of thumb is used. In both cases the **wage-based** value is given as the top of the range.

### Reading a data point

```json
{ "year": 1600, "usd2025": 124.7, "low": 92.38, "high": 168.4,
  "confidence": "medium", "method": "gold content → sterling → UK CPI",
  "provenance": "computed", "sources": [ { "title", "url", "reasoning" }, ... ] }
```

- `usd2025` is the value of **one base unit** of the currency (for example one ducat or one livre).
- `low`/`high` is a range based on judgement, not a statistical interval. Its width depends on `confidence`: high is ±10%, medium is ×/÷1.35, low is ×/÷2, and very low is ×/÷3 or explicit goods-versus-wage bounds.
- `provenance`:
  - `computed`: calculated from the downloaded datasets.
  - `compiled`: uses a rate, parity or estimate entered by hand from the cited reference. Check these before relying on them.
- Denominations give a `value` in base units, or `periods` when the value changed over time (for example the guinea, the louis d'or, or lire per florin).
- Between data points, interpolate in log space. Don't extrapolate past a currency's first or last point.

### Caveats

- **Prices understate how big a sum felt.** Before about 1900 a day's wage bought far fewer goods, so comparing against wages or income can give 3–10× the price-based value. For a sense of social standing, use the `high` end.
- **The pound and dollar routes don't always agree.** US and UK prices moved differently, so converting through one or the other can give results that differ by tens of percent. For example, the US dollar uses the UK route in 1795 and the US CPI from 1800, which causes a step between those years.
- **Medieval values are rough.** The livre tournois, Florentine and Venetian lire, pound Scots, akçe and kuruş values before about 1550 are interpolated from a few attested standards. Medieval debasements happened faster than 5-year steps can show.
- **Some periods are left out on purpose:** German hyperinflation (1921–24), 1945 for the Reichsmark and yen, Soviet rubles, colonial American pounds, and Portuguese currency after 1890.

## Sources

### Price indexes and exchange-rate datasets (downloaded)

- **Bank of England, *A millennium of macroeconomic data for the UK* (v3.1).**
  - Sheet A1/A47: UK consumer price index 1209–2016.
  - Sheet A33: $/£ 1791–2016, and FFr/£ 1938–1960.
  - Sheet M14: monthly sterling exchange rates 1963–2016, averaged to calendar years.
  - Link: <https://www.bankofengland.co.uk/-/media/boe/files/statistics/research-datasets/a-millennium-of-macroeconomic-data-for-the-uk.xlsx>
- **ONS, CPI index 00: all items, 2015=100 (D7BT).** UK CPI 2017–2025. <https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23>
- **Federal Reserve Bank of Minneapolis, *Consumer Price Index, 1800–*.** US CPI. <https://www.minneapolisfed.org/about-us/monetary-policy/inflation-calculator/consumer-price-index-1800->
- **Federal Reserve Board, G.5A annual exchange rates.** 2025 conversion rate and 2012–2025 annual averages.
  - <https://www.federalreserve.gov/releases/g5a/current/default.htm> (5 Jan 2026 release; this "current" link will show newer data after the next annual release)
  - <https://www.federalreserve.gov/releases/g5a/20210104/default.htm>
  - <https://www.federalreserve.gov/releases/g5a/20160104/>

### Exchange rates, metal prices and monetary history

- **Lawrence H. Officer, *Exchange Rates Between the United States Dollar and Forty-one Currencies*, MeasuringWorth.** Source for the hand-compiled 20th-century rates. <https://www.measuringworth.com/datasets/exchangeglobal/>
- **Officer & Williamson, *The Price of Gold, 1257–present* and the gold/silver ratio, MeasuringWorth.** <https://www.measuringworth.com/datasets/gold/>
- **Isaac Newton, letter on the state of the gold and silver coins (1717).** Supports the valuation of the piece of eight. <https://newtonproject.ox.ac.uk/catalogue/record/MINT01000>
- **Gemmill & Mayhew, *Changing Values in Medieval Scotland* (CUP, 1995).** Pound Scots against sterling. <https://ideas.repec.org/b/cup/cbooks/9780521473859.html>
- **F. C. Spooner, *The International Economy and Monetary Movements in France, 1493–1725* (Harvard, 1972).** Silver equivalents of the livre. <https://buscador.unsam.edu.ar/Record/23851>
- **Şevket Pamuk, *A Monetary History of the Ottoman Empire* (CUP, 2000).** Silver content of the kuruş. <https://doi.org/10.1017/CBO9780511497452>
- **Bank of Japan Currency Museum FAQ, "江戸時代の1両は今のいくら？"** Value of a ryō on a rice basis and a wage basis. <https://www.imes.boj.or.jp/cm/history/historyfaq/answer.html>

### Antiquity

- **Walter Scheidel, "Real wages in early economies: 1800 BCE to 1300 CE," *JESHO* 53 (2010).** Ancient wheat and barley prices and wages. <https://doi.org/10.1163/156852010X506038>
- **W. T. Loomis, *Wages, Welfare Costs and Inflation in Classical Athens* (1998).** Athenian wages and wheat prices. <https://press.umich.edu/Books/W/Wages-Welfare-Costs-and-Inflation-in-Classical-Athens>
- **Code of Hammurabi §§273–274 (Avalon Project).** Old Babylonian labourer's wage in silver. <https://avalon.law.yale.edu/ancient/hamframe.asp>
- **Matthew 20:1–16.** A denarius as a day's wage. <https://www.biblegateway.com/passage/?search=Matthew+20%3A1-16&version=NRSVUE>
- **US BLS Average Price Data.** Modern grain, flour and bread prices for comparison. <https://www.bls.gov/cpi/factsheets/average-prices.htm>
- **US BLS Occupational Employment and Wage Statistics.** Modern unskilled wages for the upper bounds. <https://www.bls.gov/oes/>

### Coin standards and parities (Wikipedia)

Used for coin weights, fineness, legal parities and denomination structures. The original scholarship is cited in each article.

| Topic | Supports |
|---|---|
| [£sd](https://en.wikipedia.org/wiki/%C2%A3sd) | Structure of pounds, shillings and pence |
| [Penny (English coin)](https://en.wikipedia.org/wiki/Penny_(English_coin)) | Silver in the English penny by reign, the basis for valuing every pre-1717 coin |
| [Gold standard](https://en.wikipedia.org/wiki/Gold_standard) | £1 = 7.3224 g fine gold (1717–1914) |
| [Bimetallism](https://en.wikipedia.org/wiki/Bimetallism) | Historical gold:silver ratios |
| [Pound Scots](https://en.wikipedia.org/wiki/Pound_Scots) | Scots/sterling ratio; 12:1 from 1603 |
| [Irish pound](https://en.wikipedia.org/wiki/Irish_pound) | 13 Irish = 12 sterling |
| [United States dollar](https://en.wikipedia.org/wiki/United_States_dollar) | Early dollar based on the Spanish dollar |
| [Spanish dollar](https://en.wikipedia.org/wiki/Spanish_dollar) | 1497/1728/1772 silver standards |
| [Livre tournois](https://en.wikipedia.org/wiki/Livre_tournois) | 80.88 g (1266), 4.505 g (1726), 4.45 g (1785) silver |
| [French franc](https://en.wikipedia.org/wiki/French_franc) | Germinal franc of 4.5 g silver; later reforms |
| [Latin Monetary Union](https://en.wikipedia.org/wiki/Latin_Monetary_Union) | Franc/lira/Swiss franc at 25.22 per £ |
| [Prussian thaler](https://en.wikipedia.org/wiki/Prussian_thaler) | 16.704 g silver (1750 standard) |
| [German gold mark](https://en.wikipedia.org/wiki/German_gold_mark) | 20.43 marks per £ |
| [German Papiermark](https://en.wikipedia.org/wiki/German_Papiermark) | WWI and post-war depreciation |
| [Reichsmark](https://en.wikipedia.org/wiki/Reichsmark) | 4.20 RM per $ |
| [Deutsche Mark](https://en.wikipedia.org/wiki/Deutsche_Mark) | Bretton Woods parities |
| [Austro-Hungarian gulden](https://en.wikipedia.org/wiki/Austro-Hungarian_gulden) | 11.69 g and 11.11 g silver standards |
| [Austro-Hungarian krone](https://en.wikipedia.org/wiki/Austro-Hungarian_krone) | 0.304878 g gold |
| [Florin (Italian coin)](https://en.wikipedia.org/wiki/Florin_(Italian_coin)) | 3.54 g gold |
| [Ducat](https://en.wikipedia.org/wiki/Ducat) | Venetian zecchino, 3.545 g of .997 gold |
| [Italian lira](https://en.wikipedia.org/wiki/Italian_lira) | Discount on paper lire; "quota 90"; 625/$ |
| [Dutch guilder](https://en.wikipedia.org/wiki/Dutch_guilder) | Silver standards; 12.107 per £ |
| [Moidore](https://en.wikipedia.org/wiki/Moidore), [Portuguese real](https://en.wikipedia.org/wiki/Portuguese_real) | Portuguese gold coins; 4,500 réis per £ |
| [Russian ruble](https://en.wikipedia.org/wiki/Russian_ruble) | Silver ruble standards; 1897 gold reform |
| [Ryō](https://en.wikipedia.org/wiki/Ry%C5%8D) | Gold content of the koban |
| [Japanese yen](https://en.wikipedia.org/wiki/Japanese_yen) | 1871 silver yen; 1897 gold yen; 360/$ |
| [Tael](https://en.wikipedia.org/wiki/Tael) | Weight of the silver tael |
| [Renminbi](https://en.wikipedia.org/wiki/Renminbi) | Official rates 1955–1994 |
| [Indian rupee](https://en.wikipedia.org/wiki/Indian_rupee), [History of the rupee](https://en.wikipedia.org/wiki/History_of_the_rupee) | Rupee silver content; 1s 4d and 1s 6d pegs |
| [Akçe](https://en.wikipedia.org/wiki/Ak%C3%A7e) | Akçe silver 1450–1800 (after Malanima) |
| [Kuruş](https://en.wikipedia.org/wiki/Kuru%C5%9F) | 1844 reform: 100 kuruş = 1 lira = 6.614 g gold |
| [Swedish krona](https://en.wikipedia.org/wiki/Swedish_krona) | 18.16 kronor per £ |
| [Spanish peseta](https://en.wikipedia.org/wiki/Spanish_peseta) | Peseta exchange history |
| [Roman currency](https://en.wikipedia.org/wiki/Roman_currency) | Roman denominations and debasement |
| [Edict on Maximum Prices](https://en.wikipedia.org/wiki/Edict_on_Maximum_Prices) | Prices in Diocletian's edict of 301 AD |
| [Solidus (coin)](https://en.wikipedia.org/wiki/Solidus_(coin)) | 1/72 Roman pound of gold |
| [Ancient Greek coinage](https://en.wikipedia.org/wiki/Ancient_Greek_coinage) | Obol/drachma/mina/talent |
| [Shekel](https://en.wikipedia.org/wiki/Shekel) | Shekel weights and units |

---

## Units of measurement

`data/units.json` holds 341 units of measurement: 105 of length, 45 of area, 95 of volume, 85 of mass and 11 counting units. They come from these systems:

| System | Examples |
|---|---|
| English / Imperial / US | Inch to league, furlong, chain, rod, fathom, hand, ell, nautical mile, cable; acre, rood, hide, virgate, oxgang, section; wine and ale gallons, hogshead, butt, tun, firkin, Winchester bushel, chaldron; avoirdupois, troy, apothecaries' and wool weights |
| Scottish, Irish | Scots ell, mile, acre, pint, boll; Irish perch, mile, acre |
| French (pre-metric) | Pied du roi, toise, aune, lieue, arpent, pinte, boisseau, setier, muid, livre, marc |
| German, Austrian | Rheinfuß, Rute, Meile, Elle, Klafter, Morgen, Joch, Scheffel, Maß, Cologne mark, Zollpfund, Zentner |
| Russian | Arshin, vershok, sazhen, verst, desyatina, vedro, chetvert, funt, pud, zolotnik |
| Spanish, Portuguese, Ottoman | Vara, legua, fanega, arroba, libra; arrátel; arşın, dönüm, kile, okka, kantar |
| Japanese, Chinese, Indian | Shaku, ken, ri, tsubo, koku, monme, kan; chi, li, mu, catty, picul, tael; gaz, kos, bigha, tola, seer, maund |
| Roman, Greek, Persian | Pes, passus, Roman mile, jugerum, amphora, modius, libra; pous, stadion, medimnos, metretes, talent; parasang |
| Egyptian, Mesopotamian, biblical | Royal cubit, khet, setat, deben; kuš, shekel, mina, talent; cubit, reed, Sabbath day's journey, bath, ephah, homer, hin, gerah |
| Counting | Dozen, baker's dozen, score, long hundred, gross, great gross, quire, ream |

### How unit values are derived

- **Each unit is defined in one of three ways:**
  - directly, as a base value (for example 1 inch = 0.0254 m, or the Roman pes measured as about 0.296 m)
  - as a multiple of another unit (1 furlong = 220 yards, 1 hogshead = 63 wine gallons)
  - as the square or cube of a length (1 tsubo = 1 ken², 1 Roman amphora = 1 cubic pes)
- **The builder works out each unit's value (`si`) from its definition**, so units stay consistent with each other. The base unit for each category is metres, square metres, litres, kilograms, or "each" for counts. Every unit's first source states the full calculation, for example "63 × Gallon (US / wine / Queen Anne) (3.78541 L) = 238.481 L".
- **`precision` says how trustworthy the value is:**
  - `exact`: fixed by law or definition, such as the 1959 international yard and pound, the imperial gallon (UK Weights and Measures Act 1985), the shaku (10/33 m) and the koku. Units derived from exact units are exact too.
  - `approximate`: a well-measured historical standard that isn't an exact legal definition, such as the pied du roi or the Prussian Elle.
  - `uncertain`: reconstructed or regionally variable, such as ancient cubits, the hide, bigha, bath or tron pound. These give a plausible `low`/`high` range, which carries through to any unit derived from them.
- **To convert** a quantity between two units of the same category, use `amount × from.si / to.si`. Volume units are tagged `liquid` or `dry` where the distinction matters. US and imperial gallons and bushels differ, and so did pre-1824 English wine and ale gallons.
- **`era`** is the approximate first and last year a unit was in common use (negative years are BCE; `null` means still in use).

### Caveats

- Before standardisation, many units varied from town to town and from commodity to commodity. For example, a stone of meat was 8 lb, and leagues, morgens, bighas, kantars and fanegas varied widely. The value given is the most widely cited standard; the notes and ranges flag the spread.
- Ancient units are modern reconstructions from surviving measuring rods, weights and buildings, so they carry real uncertainty.

### Sources for units

**Statutes and standards**

- **International yard and pound agreement (1959).** 1 yd = 0.9144 m and 1 lb = 0.45359237 kg exactly. <https://en.wikipedia.org/wiki/International_yard_and_pound>
- **UK Weights and Measures Act 1985, Schedule 1.** Legal definitions of the imperial units. <https://www.legislation.gov.uk/ukpga/1985/72/schedule/1>
- **NIST Special Publication 811, Appendix B.8.** US conversion factors. <https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8>
- **BIPM, the SI Brochure.** Metric base units. <https://www.bipm.org/en/publications/si-brochure>

**Reference articles (Wikipedia)**

Each article cites the primary metrological literature behind it.

| Topic | Supports |
|---|---|
| [English units](https://en.wikipedia.org/wiki/English_units), [Imperial units](https://en.wikipedia.org/wiki/Imperial_units), [US customary units](https://en.wikipedia.org/wiki/United_States_customary_units) | English, imperial and US measures, including wool weights |
| [Foot (unit)](https://en.wikipedia.org/wiki/Foot_(unit)) | US survey foot |
| [Nautical mile](https://en.wikipedia.org/wiki/Nautical_mile), [Cable length](https://en.wikipedia.org/wiki/Cable_length), [League (unit)](https://en.wikipedia.org/wiki/League_(unit)) | Nautical units; leagues and lieues |
| [Point (typography)](https://en.wikipedia.org/wiki/Point_(typography)) | Point and pica |
| [Cubit](https://en.wikipedia.org/wiki/Cubit), [Ell](https://en.wikipedia.org/wiki/Ell) | Cubits and ells across cultures |
| [Acre](https://en.wikipedia.org/wiki/Acre), [Hide](https://en.wikipedia.org/wiki/Hide_(unit)), [Carucate](https://en.wikipedia.org/wiki/Carucate), [Virgate](https://en.wikipedia.org/wiki/Virgate), [Oxgang](https://en.wikipedia.org/wiki/Oxgang), [Section](https://en.wikipedia.org/wiki/Section_(United_States_land_surveying)) | Land measures |
| [Gallon](https://en.wikipedia.org/wiki/Gallon), [English wine cask units](https://en.wikipedia.org/wiki/English_wine_cask_units), [Barrel (unit)](https://en.wikipedia.org/wiki/Barrel_(unit)), [Bushel](https://en.wikipedia.org/wiki/Bushel), [Chaldron](https://en.wikipedia.org/wiki/Chaldron) | Liquid and dry volumes |
| [Avoirdupois](https://en.wikipedia.org/wiki/Avoirdupois), [Troy weight](https://en.wikipedia.org/wiki/Troy_weight), [Apothecaries' system](https://en.wikipedia.org/wiki/Apothecaries%27_system), [Carat (mass)](https://en.wikipedia.org/wiki/Carat_(mass)) | Weight systems; Tower and merchants' pounds |
| [Scottish units](https://en.wikipedia.org/wiki/Scottish_units), [Irish measure](https://en.wikipedia.org/wiki/Irish_measure) | Scottish and Irish units |
| [Traditional French units](https://en.wikipedia.org/wiki/Traditional_French_units_of_measurement), [Arpent](https://en.wikipedia.org/wiki/Arpent) | Pre-metric French units |
| [German units](https://en.wikipedia.org/wiki/German_units_of_measurement), [Klafter](https://en.wikipedia.org/wiki/Klafter), [Morgen](https://en.wikipedia.org/wiki/Morgen), [Mark (unit)](https://en.wikipedia.org/wiki/Mark_(unit)) | Prussian, Austrian, Bavarian and Dutch units; Cologne mark |
| [Historical Russian units](https://en.wikipedia.org/wiki/Historical_Russian_units_of_measurement), [Desiatina](https://en.wikipedia.org/wiki/Desiatina) | Russian units (1835 definitions) |
| [Spanish units](https://en.wikipedia.org/wiki/Spanish_units_of_measurement), [Portuguese units](https://en.wikipedia.org/wiki/Portuguese_units_of_measurement) | Iberian units |
| [Ottoman units](https://en.wikipedia.org/wiki/Ottoman_units_of_measurement), [Dunam](https://en.wikipedia.org/wiki/Dunam) | Ottoman units |
| [Japanese units](https://en.wikipedia.org/wiki/Japanese_units_of_measurement) | Shaku-kan system |
| [Chinese units](https://en.wikipedia.org/wiki/Chinese_units_of_measurement), [Jin (mass)](https://en.wikipedia.org/wiki/Jin_(mass)) | Qing, Hong Kong and modern shì units |
| [Indian units](https://en.wikipedia.org/wiki/Indian_units_of_measurement), [Maund](https://en.wikipedia.org/wiki/Maund), [Tola](https://en.wikipedia.org/wiki/Tola_(unit)), [Bigha](https://en.wikipedia.org/wiki/Bigha) | South Asian units |
| [Ancient Roman units](https://en.wikipedia.org/wiki/Ancient_Roman_units_of_measurement), [Ancient Greek units](https://en.wikipedia.org/wiki/Ancient_Greek_units_of_measurement), [Parasang](https://en.wikipedia.org/wiki/Parasang) | Classical units |
| [Ancient Egyptian units](https://en.wikipedia.org/wiki/Ancient_Egyptian_units_of_measurement), [Ancient Mesopotamian units](https://en.wikipedia.org/wiki/Ancient_Mesopotamian_units_of_measurement) | Egyptian and Mesopotamian units |
| [Biblical and Talmudic units](https://en.wikipedia.org/wiki/Biblical_and_Talmudic_units_of_measurement), [Shekel](https://en.wikipedia.org/wiki/Shekel) | Biblical units |
| [Dozen](https://en.wikipedia.org/wiki/Dozen), [Gross](https://en.wikipedia.org/wiki/Gross_(unit)), [Long hundred](https://en.wikipedia.org/wiki/Long_hundred), [Ream](https://en.wikipedia.org/wiki/Ream) | Counting units |
