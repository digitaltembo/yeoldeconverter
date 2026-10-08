"""Extract the price-index and exchange-rate series used by build_currencies.py.

Inputs (downloaded files, paths passed as args):
  boe.xlsx   Bank of England, "A millennium of macroeconomic data for the UK" v3.1
  ons.csv    ONS series D7BT (CPI all items, 2015=100)
  mpls.html  Minneapolis Fed, "Consumer Price Index, 1800-"
Output: data/source-series.json
"""
import csv, json, re, sys, statistics
import openpyxl

boe_path, ons_path, mpls_path, out_path = sys.argv[1:5]
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

json.dump({"uk_cpi": uk_cpi, "us_cpi": us_cpi, "usd_per_gbp": usd_per_gbp,
           "ffr_per_gbp_1938_1960": ffr_per_gbp_1938, "per_gbp_annual_m14": per_gbp_annual},
          open(out_path, "w"), indent=1, sort_keys=True)
print("uk_cpi", min(uk_cpi), max(uk_cpi), "us_cpi", min(us_cpi), max(us_cpi),
      "usd_per_gbp", min(usd_per_gbp), max(usd_per_gbp))
for code, ys in per_gbp_annual.items():
    print(code, min(ys) if ys else None, max(ys) if ys else None)
print({y: ffr_per_gbp_1938[y] for y in sorted(ffr_per_gbp_1938)})
