"""Extract the price-index and exchange-rate series used by build_currencies.py.

Usage: python3 scripts/extract_series.py sources data/source-series.json

The downloaded files live in sources/ (gitignored), under these names:
  boe-millennium.xlsx    Bank of England, "A millennium of macroeconomic data for the UK" v3.1
                         https://www.bankofengland.co.uk/-/media/boe/files/statistics/research-datasets/a-millennium-of-macroeconomic-data-for-the-uk.xlsx
  ons-d7bt.csv           ONS series D7BT (CPI all items, 2015=100)
                         https://www.ons.gov.uk/generator?format=csv&uri=/economy/inflationandpriceindices/timeseries/d7bt/mm23
  minneapolis-fed-cpi.html  Minneapolis Fed, "Consumer Price Index, 1800-"
                         https://www.minneapolisfed.org/about-us/monetary-policy/inflation-calculator/consumer-price-index-1800-
  measuringworth-exchange.html  MeasuringWorth, "Exchange Rates Between the United States Dollar and Forty-one Currencies":
                         the result page of a POST to https://www.measuringworth.com/datasets/exchangeglobal/result.php
                         with year_source=1791, year_result=2025 and countryE[]=<country> for every country on the form
  measuringworth-gold.html  MeasuringWorth, "The Price of Gold, 1257-Present": the result page of a POST to
                         https://www.measuringworth.com/datasets/gold/result.php with goldsilver=on, year_source=1257, year_result=2025
  jst-macrohistory-r6.dta  Jordà-Schularick-Taylor Macrohistory Database, release 6. The download is a Stata file despite its name:
                         https://www.macrohistory.net/app/download/9834512469/JSTdatasetR6.xlsx
  pwt-10.01.xlsx         Penn World Table 10.01, https://dataverse.nl/api/access/datafile/354095
  fred/<series id>.csv   FRED annual exchange rates, https://fred.stlouisfed.org/graph/fredgraph.csv?id=<series id>
                         for each series in FRED_SERIES
Output: data/source-series.json. Every exchange rate in it is foreign currency per US dollar, by calendar year.
"""
import csv, json, os, re, sys, statistics
import openpyxl
import pandas as pd

sources_dir, out_path = sys.argv[1:3]
inp = lambda name: os.path.join(sources_dir, name)
boe_path, ons_path, mpls_path = inp("boe-millennium.xlsx"), inp("ons-d7bt.csv"), inp("minneapolis-fed-cpi.html")
mw_fx_path, mw_gold_path = inp("measuringworth-exchange.html"), inp("measuringworth-gold.html")
jst_path, pwt_path, fred_dir = inp("jst-macrohistory-r6.dta"), inp("pwt-10.01.xlsx"), inp("fred")
wb = openpyxl.load_workbook(boe_path, read_only=True, data_only=True)

def col(sheet, c, first_row=8):
    out = {}
    for r in wb[sheet].iter_rows(min_row=first_row, values_only=True):
        y, v = r[0], r[c] if c < len(r) else None
        if isinstance(y, (int, float)) and isinstance(v, (int, float)):
            out[int(y)] = float(v)
    return out

uk_cpi = col("A1. Headline series", 40)          # 2015=100, 1209-2016
for row in csv.reader(open(ons_path)):
    if len(row) == 2 and re.fullmatch(r"\d{4}", row[0]) and row[1]:
        y = int(row[0])
        if y >= 2017:
            uk_cpi[y] = float(row[1])

usd_per_gbp = col("A33. Exchange rate data", 1, 4)  # 1791-2016
ffr_per_gbp_1938 = col("A33. Exchange rate data", 21, 4)

# M14: monthly sterling bilaterals 1963+, averaged to calendar years
m14_names = {1: "CAD", 3: "EUR", 5: "FRF", 6: "DEM", 8: "ITL", 9: "JPY",
             11: "ESP", 12: "SEK", 13: "CHF", 14: "USD"}
monthly = {k: {} for k in m14_names.values()}
for r in wb["M14. Mthly Exchange rates 1963+"].iter_rows(min_row=7, values_only=True):
    d = r[0]
    if not hasattr(d, "year"):
        continue
    for c, code in m14_names.items():
        v = r[c] if c < len(r) else None
        if isinstance(v, (int, float)) and v:
            monthly[code].setdefault(d.year, []).append(float(v))
per_gbp_annual = {code: {y: statistics.mean(vs) for y, vs in ys.items() if len(vs) == 12}
                  for code, ys in monthly.items()}

t = open(mpls_path, encoding="utf-8", errors="ignore").read()
cells = [re.sub(r"<[^>]+>|&nbsp;", "", c).strip() for c in re.findall(r"<td[^>]*>(.*?)</td>", t, re.S)]
us_cpi = {}
for i in range(0, len(cells) - 1):
    if re.fullmatch(r"\d{4}", cells[i]) and re.fullmatch(r"[\d.]+", cells[i + 1]):
        us_cpi[int(cells[i])] = float(cells[i + 1])

# MeasuringWorth: one table per country ("<b>Canada, 1913 - 2025</b>"), rows "<year> <rate> <unit>".
# Units change with redenominations, so each (country, unit) maps to one of our currency codes; others are skipped.
MW_UNITS = {("Canada", "Canadian Dollar"): "CAD",
            ("Mexico", "Old Pesos"): "MXP", ("Mexico", "Pesos"): "MXN", ("Mexico", "Peso"): "MXN",
            ("France", "Old Francs"): "FRF", ("France", "Francs"): "FRF_NEW",
            ("Germany", "Mark"): "MARK", ("Germany", "Reichsmark"): "RM", ("Germany", "Deutsche mark"): "DEM",
            ("Italy", "Lire"): "ITL", ("Netherlands", "Guilder"): "NLG", ("Japan", "Yen"): "JPY",
            ("China", "(New People's Currency) Yuan"): "CNY", ("India", "Rupee"): "INR",
            ("Switzerland", "Franc"): "CHF", ("Sweden", "Kronor"): "SEK", ("Spain", "Peseta"): "ESP",
            ("United Kingdom", "British Pound"): "GBP"}
html = open(mw_fx_path, encoding="utf-8", errors="ignore").read()
mw_per_usd = {}
for country, body in re.findall(r"<b>([A-Za-z ]+), \d{4} - \d{4}</b>(.*?)</table>", html, re.S):
    for y, v, unit in re.findall(r"<td[^>]*>(\d{4})</td><td>([\d.,]+) ([^<]+)</td>", body):
        code = MW_UNITS.get((country, unit.strip()))
        if code:
            mw_per_usd.setdefault(code, {})[int(y)] = float(v.replace(",", ""))
assert set(MW_UNITS.values()) <= set(mw_per_usd), set(MW_UNITS.values()) - set(mw_per_usd)

# MeasuringWorth gold/silver price ratio (ounces of silver per ounce of gold), 1687-
html = open(mw_gold_path, encoding="utf-8", errors="ignore").read()
gold_silver_ratio = {int(y): float(v.replace(",", "")) for y, v in
                     re.findall(r"<tr[^>]*>\s*<td[^>]*>\s*(\d{4})\s*</td>\s*<td>([\d.,]+)</td>", html)}

# Jordà-Schularick-Taylor 'xrusd' (local currency per US dollar), used for years before MeasuringWorth's tables start.
# Before 1879 the US dollar here is the greenback, as in the BoE $/£ series, so the two can be crossed.
JST_CODES = {"JPN": "JPY", "ITA": "ITL", "GBR": "GBP", "CHE": "CHF", "SWE": "SEK", "ESP": "ESP", "CAN": "CAD"}
jst = pd.read_stata(jst_path)
jst_per_usd = {code: {int(y): float(v) for y, v in jst[jst.iso == iso][["year", "xrusd"]].itertuples(index=False)
                      if v == v and v > 0}
               for iso, code in JST_CODES.items()}

# Penn World Table 'xr' (national currency per US dollar, market + estimated). PWT states euro-area countries in euros
# for every year, so those are converted back to the old currency at its fixed euro conversion rate.
PWT_CODES = {"CHN": ("CNY", 1), "JPN": ("JPY", 1), "ITA": ("ITL", 1936.27), "ESP": ("ESP", 166.386)}
pwt = pd.read_excel(pwt_path, sheet_name="Data", usecols=["countrycode", "currency_unit", "year", "xr"])
pwt_per_usd = {}
for iso, (code, per_euro) in PWT_CODES.items():
    rows = pwt[pwt.countrycode == iso]
    assert (rows.currency_unit == "Euro").all() == (per_euro != 1), (iso, set(rows.currency_unit))
    pwt_per_usd[code] = {int(y): float(v) * per_euro for y, v in rows[["year", "xr"]].itertuples(index=False) if v == v}

# FRED annual spot rates (Federal Reserve G.5A). AEXUSUK and AEXUSEU are quoted as US dollars per unit, so they are inverted.
FRED_SERIES = {"CAD": "AEXCAUS", "MXN": "AEXMXUS", "GBP": "AEXUSUK", "EUR": "AEXUSEU", "JPY": "AEXJPUS",
               "CNY": "AEXCHUS", "INR": "AEXINUS", "CHF": "AEXSZUS", "SEK": "AEXSDUS"}
FRED_USD_PER_UNIT = {"AEXUSUK", "AEXUSEU"}
fred_per_usd = {}
for code, series_id in FRED_SERIES.items():
    for row in csv.DictReader(open(os.path.join(fred_dir, series_id + ".csv"))):
        if row[series_id] not in ("", "."):
            v = float(row[series_id])
            fred_per_usd.setdefault(code, {})[int(row["observation_date"][:4])] = 1 / v if series_id in FRED_USD_PER_UNIT else v

json.dump({"uk_cpi": uk_cpi, "us_cpi": us_cpi, "usd_per_gbp": usd_per_gbp,
           "ffr_per_gbp_1938_1960": ffr_per_gbp_1938, "per_gbp_annual_m14": per_gbp_annual,
           "mw_per_usd": mw_per_usd, "fred_per_usd": fred_per_usd, "jst_per_usd": jst_per_usd,
           "pwt_per_usd": pwt_per_usd, "gold_silver_ratio": gold_silver_ratio},
          open(out_path, "w"), indent=1, sort_keys=True)
print("uk_cpi", min(uk_cpi), max(uk_cpi), "us_cpi", min(us_cpi), max(us_cpi),
      "usd_per_gbp", min(usd_per_gbp), max(usd_per_gbp))
for code, ys in per_gbp_annual.items():
    print(code, min(ys) if ys else None, max(ys) if ys else None)
print({y: ffr_per_gbp_1938[y] for y in sorted(ffr_per_gbp_1938)})
print("gold_silver_ratio", min(gold_silver_ratio), max(gold_silver_ratio))
for name, table in (("measuringworth", mw_per_usd), ("fred", fred_per_usd), ("jst", jst_per_usd), ("pwt", pwt_per_usd)):
    for code, ys in table.items():
        print(name, code, min(ys), max(ys))
