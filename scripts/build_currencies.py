"""Build data/currencies.json: historical currencies valued in 2025 US dollars.

Usage: python3 scripts/build_currencies.py data/source-series.json data/currencies.json

Method (see "methodology" in the output for the long version):
  * Each currency, at each year, is first expressed in a contemporary "anchor"
    money: pounds sterling for years <= 1910, US dollars for years >= 1915.
    The bridge is a metal content (silver/gold grams), a legal parity, or an
    exchange rate, whichever is appropriate for the period.
  * The anchor amount is carried to 2025 with a consumer price index
    (UK: Bank of England millennium dataset + ONS D7BT; US: Minneapolis Fed).
  * Pounds are converted to dollars at the 2025 average rate (Fed G.5A).
  * Ancient currencies and the Edo-period ryo have no usable price index, so
    they are estimated from commodity prices and wages, with wide ranges.
"""
import json, math, sys

series_path, out_path = sys.argv[1], sys.argv[2]
S = json.load(open(series_path))
UK_CPI = {int(k): v for k, v in S["uk_cpi"].items()}
US_CPI = {int(k): v for k, v in S["us_cpi"].items()}
USD_PER_GBP = {int(k): v for k, v in S["usd_per_gbp"].items()}
M14 = {c: {int(y): v for y, v in ys.items()} for c, ys in S["per_gbp_annual_m14"].items()}
FFR_1938 = {int(k): v for k, v in S["ffr_per_gbp_1938_1960"].items()}

BASE_YEAR = 2025
# Fed G.5A annual averages (foreign currency per USD, except GBP/EUR/AUD which are USD per unit)
G5A = {
    2015: {"GBP": 1.5284, "EUR": 1.1096, "JPY": 121.05, "CNY": 6.2827, "INR": 64.11},
    2020: {"GBP": 1.2829, "EUR": 1.1410, "JPY": 106.7754, "CNY": 6.9042, "INR": 74.1429,
           "CHF": 0.9389, "SEK": 9.2167, "CAD": 1.3422},
    2025: {"GBP": 1.3192, "EUR": 1.1306, "JPY": 149.5686, "CNY": 7.1875, "INR": 87.1468,
           "CHF": 0.8305, "SEK": 9.8060, "CAD": 1.3973},
}
GBP_USD_2025 = G5A[2025]["GBP"]
EURO_FIXED = {"FRF": 6.55957, "DEM": 1.95583, "ITL": 1936.27, "ESP": 166.386, "NLG": 2.20371}

# ---------------------------------------------------------------- sources
BOE_XLSX = ("https://www.bankofengland.co.uk/-/media/boe/files/statistics/research-datasets/"
            "a-millennium-of-macroeconomic-data-for-the-uk.xlsx")
WP = "https://en.wikipedia.org/wiki/"
SRC = {
    "boe_cpi": ("Bank of England, 'A millennium of macroeconomic data for the UK' v3.1 — "
                "sheet A1/A47 'Consumer price index' (2015=100, 1209-2016)", BOE_XLSX),
    "boe_fx": ("Bank of England, 'A millennium of macroeconomic data for the UK' v3.1 — "
               "sheet A33 '$/£ exchange rate' (1791-2016; source Officer 1996 / Federal Reserve)", BOE_XLSX),
    "boe_m14": ("Bank of England, 'A millennium of macroeconomic data for the UK' v3.1 — "
                "sheet M14 'Monthly bilateral exchange rates' (1963-2016), averaged to calendar years", BOE_XLSX),
    "boe_a33ffr": ("Bank of England, 'A millennium of macroeconomic data for the UK' v3.1 — "
                   "sheet A33 'FFr/£' column (1938-1960, from Mitchell)", BOE_XLSX),
    "ons_cpi": ("Office for National Statistics, CPI index 00: all items, 2015=100 (series D7BT), annual",
                "https://www.ons.gov.uk/economy/inflationandpriceindices/timeseries/d7bt/mm23"),
    "mpls_cpi": ("Federal Reserve Bank of Minneapolis, 'Consumer Price Index, 1800-' (annual averages)",
                 "https://www.minneapolisfed.org/about-us/monetary-policy/inflation-calculator/consumer-price-index-1800-"),
    "g5a_2025": ("Federal Reserve Board, G.5A Foreign Exchange Rates (Annual), release of 5 Jan 2026",
                 "https://www.federalreserve.gov/releases/g5a/current/default.htm"),
    "g5a_2020": ("Federal Reserve Board, G.5A Foreign Exchange Rates (Annual), release of 4 Jan 2021",
                 "https://www.federalreserve.gov/releases/g5a/20210104/default.htm"),
    "g5a_2015": ("Federal Reserve Board, G.5A Foreign Exchange Rates (Annual), release of 4 Jan 2016",
                 "https://www.federalreserve.gov/releases/g5a/20160104/"),
    "mw_fx": ("Lawrence H. Officer, 'Exchange Rates Between the United States Dollar and Forty-one "
              "Currencies', MeasuringWorth", "https://www.measuringworth.com/datasets/exchangeglobal/"),
    "mw_gsr": ("Lawrence H. Officer & Samuel H. Williamson, 'The Price of Gold, 1257-present' and "
               "gold/silver price ratio, MeasuringWorth", "https://www.measuringworth.com/datasets/gold/"),
    "wp_penny": ("Wikipedia, 'Penny (English coin)' — mint weights and fineness by reign", WP + "Penny_(English_coin)"),
    "wp_ster": ("Wikipedia, '£sd' — pounds, shillings and pence", WP + "%C2%A3sd"),
    "wp_guinea": ("Wikipedia, 'Guinea (coin)'", WP + "Guinea_(coin)"),
    "wp_gold_std": ("Wikipedia, 'Gold standard' — mint parities 1717-1914 (£1 = 7.3224 g fine gold)", WP + "Gold_standard"),
    "wp_bimet": ("Wikipedia, 'Bimetallism' — 15.5:1 French ratio; post-1873 silver collapse", WP + "Bimetallism"),
    "wp_scots": ("Wikipedia, 'Pound Scots' — depreciation against sterling, fixed 12:1 from 1603", WP + "Pound_Scots"),
    "gemmill": ("Elizabeth Gemmill & Nicholas Mayhew, 'Changing Values in Medieval Scotland' (Cambridge UP, 1995)",
                "https://ideas.repec.org/b/cup/cbooks/9780521473859.html"),
    "wp_irish": ("Wikipedia, 'Irish pound' — pre-1826 Irish currency at 13 Irish = 12 sterling", WP + "Irish_pound"),
    "wp_spdollar": ("Wikipedia, 'Spanish dollar' — weight/fineness standards 1497, 1728, 1772", WP + "Spanish_dollar"),
    "newton1717": ("Isaac Newton, letter concerning the state of the gold and silver coins (21 Sept 1717) — "
                   "The Newton Project catalogue", "https://newtonproject.ox.ac.uk/catalogue/record/MINT01000"),
    "wp_livre": ("Wikipedia, 'Livre tournois' — 80.88 g silver (1266), 4.505 g (1726), 4.45 g (1785)", WP + "Livre_tournois"),
    "wp_ecu": ("Wikipedia, 'Écu' and 'Louis d'or' — official valuations in livres", WP + "Louis_d%27or"),
    "spooner": ("Frank C. Spooner, 'The International Economy and Monetary Movements in France, 1493-1725' "
                "(Harvard Economic Studies 138, 1972) — livre tournois silver equivalents (library record)", "https://buscador.unsam.edu.ar/Record/23851"),
    "wp_franc": ("Wikipedia, 'French franc' — germinal franc 4.5 g silver; 1928 Poincaré franc; 1960 new franc", WP + "French_franc"),
    "wp_lmu": ("Wikipedia, 'Latin Monetary Union' — franc/lira/Swiss franc parity, 25.22 per £", WP + "Latin_Monetary_Union"),
    "wp_thaler": ("Wikipedia, 'Prussian thaler' — Graumann 14-thaler standard (16.704 g fine silver)", WP + "Prussian_thaler"),
    "wp_vthaler": ("Wikipedia, 'Vereinsthaler' and 'South German gulden' — 1857 standard; 1 thaler = 1¾ gulden", WP + "Vereinsthaler"),
    "wp_goldmark": ("Wikipedia, 'German gold mark' — 1 mark = 0.358423 g fine gold; 20.43 per £", WP + "German_gold_mark"),
    "wp_papiermark": ("Wikipedia, 'German Papiermark' — wartime and 1919-1923 depreciation", WP + "German_Papiermark"),
    "wp_reichsmark": ("Wikipedia, 'Reichsmark' — 4.20 RM per US dollar parity", WP + "Reichsmark"),
    "wp_dm": ("Wikipedia, 'Deutsche Mark' — 4.20 DM/$ (1949), revaluations 1961, 1969", WP + "Deutsche_Mark"),
    "wp_augulden": ("Wikipedia, 'Austro-Hungarian gulden' — Conventionsfuß (11.69 g) and 1857 (11.11 g) standards", WP + "Austro-Hungarian_gulden"),
    "wp_krone": ("Wikipedia, 'Austro-Hungarian krone' — 1 krone = 0.304878 g gold", WP + "Austro-Hungarian_krone"),
    "wp_florin": ("Wikipedia, 'Florin (Italian coin)' — 3.54 g of 24-carat gold, 1252-1533", WP + "Florin_(Italian_coin)"),
    "wp_ducat": ("Wikipedia, 'Ducat' — Venetian zecchino, 3.545 g of .997 gold, 1284-1797", WP + "Ducat"),
    "spufford": ("Peter Spufford, 'Handbook of Medieval Exchange' (Royal Historical Society, 1986) — "
                 "Florentine and Venetian money-of-account rates (library record)", "https://ci.nii.ac.jp/ncid/BA00272230?l=en"),
    "wp_guilder": ("Wikipedia, 'Dutch guilder' — 1681 (9.613 g silver), 1840, and 1875 gold standards", WP + "Dutch_guilder"),
    "wp_ruble": ("Wikipedia, 'Russian ruble' — 1704 ruble, 1764 (18 g) standard, assignats, 1897 Witte gold reform", WP + "Russian_ruble"),
    "wp_assign": ("Wikipedia, 'Russian assignation ruble' — discount of paper to silver, 1769-1843", WP + "Russian_assignation_ruble"),
    "wp_ryo": ("Wikipedia, 'Ryō' and 'Koban (coin)' — gold content of successive koban issues", WP + "Ry%C5%8D"),
    "boj_ryo": ("Bank of Japan Institute for Monetary and Economic Studies, Currency Museum FAQ "
                "'江戸時代の1両は今のいくら？' (How much was one ryō worth in today's money?)",
                "https://www.imes.boj.or.jp/cm/history/historyfaq/answer.html"),
    "wp_yen": ("Wikipedia, 'Japanese yen' — 1871 yen (24.26 g silver), 1897 gold yen (0.75 g), 360/$ (1949-71)", WP + "Japanese_yen"),
    "wp_tael": ("Wikipedia, 'Tael' — Kuping/Haikwan tael ≈ 37.3-37.8 g of silver", WP + "Tael"),
    "wp_cash": ("Wikipedia, 'Cash (Chinese coin)' — strings of 1000 cash; market cash/silver rates", WP + "Cash_(Chinese_coin)"),
    "wp_rmb": ("Wikipedia, 'Renminbi' — 2.46/$ (1955-71), unification 1994", WP + "Renminbi"),
    "wp_rupee": ("Wikipedia, 'Indian rupee' — 1835 Company rupee (165 grains fine), 1s 4d (1899), 1s 6d (1927)", WP + "Indian_rupee"),
    "wp_rupee_hist": ("Wikipedia, 'History of the rupee' — Mughal rupiya ~178 grains", WP + "History_of_the_rupee"),
    "wp_akce": ("Wikipedia, 'Akçe' — silver content 1450-1800 (after Malanima 2009); 120 akçe = 1 kuruş", WP + "Ak%C3%A7e"),
    "pamuk": ("Şevket Pamuk, 'A Monetary History of the Ottoman Empire' (Cambridge UP, 2000)", "https://doi.org/10.1017/CBO9780511497452"),
    "wp_kurus": ("Wikipedia, 'Kuruş' and 'Ottoman lira' — 1844 reform: 100 kuruş = 1 lira = 6.614 g gold", WP + "Kuru%C5%9F"),
    "wp_moidore": ("Wikipedia, 'Moidore' — 4800 réis; current in Britain at 27s", WP + "Moidore"),
    "wp_real_pt": ("Wikipedia, 'Portuguese real' — milréis; 1854 gold standard (£1 = 4500 réis)", WP + "Portuguese_real"),
    "wp_lira": ("Wikipedia, 'Italian lira' — LMU parity, 1927 'quota 90', 625/$ (1949-71)", WP + "Italian_lira"),
    "wp_peseta": ("Wikipedia, 'Spanish peseta'", WP + "Spanish_peseta"),
    "wp_chf": ("Wikipedia, 'Swiss franc'", WP + "Swiss_franc"),
    "wp_sek": ("Wikipedia, 'Swedish krona' — Scandinavian Monetary Union, 18.16 per £", WP + "Swedish_krona"),
    "wp_euro": ("Wikipedia, 'Euro' — irrevocable conversion rates of 1999", WP + "Euro"),
    "wp_usd": ("Wikipedia, 'United States dollar' — Coinage Act of 1792; dollar based on Spanish dollar", WP + "United_States_dollar"),
    "wp_bretton": ("Wikipedia, 'Bretton Woods system' — fixed parities 1945-1971", WP + "Bretton_Woods_system"),
    "wp_denarius": ("Wikipedia, 'Denarius' and 'Roman currency' — denominations and debasement", WP + "Roman_currency"),
    "wp_edict": ("Wikipedia, 'Edict on Maximum Prices' (301 AD) — wheat 100 denarii per modius castrensis", WP + "Edict_on_Maximum_Prices"),
    "scheidel": ("Walter Scheidel, 'Real wages in early economies: evidence for living standards from "
                 "1800 BCE to 1300 CE', Journal of the Economic and Social History of the Orient 53 (2010) 425-462",
                 "https://doi.org/10.1163/156852010X506038"),
    "matthew": ("Matthew 20:1-16 — a day's wage for a vineyard labourer is one denarius", "https://www.biblegateway.com/passage/?search=Matthew+20%3A1-16&version=NRSVUE"),
    "wp_solidus": ("Wikipedia, 'Solidus (coin)' — 1/72 Roman pound of gold (~4.5 g) from 309 AD", WP + "Solidus_(coin)"),
    "wp_greek": ("Wikipedia, 'Ancient Greek coinage' and 'Attic talent' — 6 obols = 1 drachma, 6000 drachmae = 1 talent", WP + "Ancient_Greek_coinage"),
    "loomis": ("William T. Loomis, 'Wages, Welfare Costs and Inflation in Classical Athens' (University of Michigan Press, 1998)",
               "https://press.umich.edu/Books/W/Wages-Welfare-Costs-and-Inflation-in-Classical-Athens"),
    "wp_shekel": ("Wikipedia, 'Shekel' — ~11 g silver; gerah, beka, mina, talent", WP + "Shekel"),
    "hammurabi": ("Code of Hammurabi, §§273-274 (hired labourer's daily wage in grains of silver) — Avalon Project translation",
                  "https://avalon.law.yale.edu/ancient/hamframe.asp"),
    "usda_ers": ("For modern comparison prices of grain/flour/bread: US Bureau of Labor Statistics, Average Price Data (CPI-AP)",
                 "https://www.bls.gov/cpi/factsheets/average-prices.htm"),
    "srd51": ("Wizards of the Coast, D&D 5th Edition System Reference Document 5.1 — 'Coins' and 'Selling Treasure' (coin rates; "
              "'a silver piece buys a laborer's work for half a day'; artisan earns 1 gp/day; 50 coins weigh a pound)",
              "https://media.wizards.com/2016/downloads/DND/SRD-OGL_V5.1.pdf"),
    "awoiaf_coin": ("A Wiki of Ice and Fire, 'Coin' — Westerosi denominations; exchange table from Green Ronin's "
                    "'A Song of Ice and Fire Roleplaying' (semi-canon; not stated in the novels)", "https://awoiaf.westeros.org/index.php/Coin"),
    "sw_wupiupi": ("Wookieepedia (Legends, mirrored at archivum.wiki), 'Wupiupi' — ≈ 0.625 credits; 16 wupiupi = 1 trugut",
                   "https://starwars.archivum.wiki/article/wupiupi"),
    "sw_trugut": ("Wookieepedia (Legends, mirrored at archivum.wiki), 'Trugut' — 10 credits or 16 wupiupi", "https://starwars.archivum.wiki/article/Trugut"),
    "sw_peggat": ("Wookieepedia (Legends, mirrored at archivum.wiki), 'Peggat' — 4 truguts, 64 wupiupi, ≈ 40 credits",
                  "https://starwars.archivum.wiki/article/Peggat"),
    "st_latinum": ("StarTrek.com, 'Star Trek 101: Latinum' — gold-pressed latinum comes in slips, strips, bars and bricks",
                   "https://www.startrek.com/news/star-trek-101-latinum"),
    "sto_latinum": ("Star Trek Online Wiki, 'Latinum' — 100 slips = 1 strip; 20 strips = 1 bar; bar-to-brick rate unknown",
                    "https://sto.fandom.com/wiki/Latinum"),
    "lspace_currency": ("The L-Space Web wiki, 'Currency' — Ankh-Morpork dollar = 20 shillings; shilling = 12 pence; down to mites "
                        "and elims; 'Going Postal': a senior official earns $20 a week", "https://wiki.lspace.org/Currency"),
    "hhgg_book": ("Douglas Adams, 'The Hitch Hiker's Guide to the Galaxy' (1979) — Open Library record", "https://openlibrary.org/books/OL7506950M/The_Hitch_Hiker%27s_Guide_to_the_Galaxy"),
    "hhgg_quote": ("Forum quotation of the Guide's passage on the Triganic Pu (eight Ningis to one Pu; the Ningi a triangular rubber "
                   "coin 6,800 miles along each side)", "https://coppercoins.com/forum/viewtopic.php?p=11292"),
    "bls_wage": ("For modern comparison wages: US Bureau of Labor Statistics, Occupational Employment and Wage Statistics",
                 "https://www.bls.gov/oes/"),
}


def src(key, reasoning):
    title, url = SRC[key]
    return {"title": title, "url": url, "reasoning": reasoning}


def sig(x, n=4):
    if x == 0:
        return 0
    return round(x, -int(math.floor(math.log10(abs(x)))) + (n - 1))


def lsd(gbp):
    """Format a sterling amount as £ s d."""
    d_total = gbp * 240
    L = int(d_total // 240)
    s = int((d_total - L * 240) // 12)
    d = d_total - L * 240 - s * 12
    dd = f"{d:.2f}".rstrip("0").rstrip(".")
    return f"£{L} {s}s {dd}d"


# ------------------------------------------------------- anchor money -> 2025 USD
def uk_cpi_sources(y):
    m = UK_CPI[BASE_YEAR] / UK_CPI[y]
    out = []
    if y <= 2016:
        out.append(src("boe_cpi", f"UK consumer price index for {y} = {UK_CPI[y]:.5g} (2015=100)."))
    out.append(src("ons_cpi", f"UK CPI {BASE_YEAR} = {UK_CPI[BASE_YEAR]} (2015=100)"
                   + (f"; {y} = {UK_CPI[y]}" if y > 2016 else
                      "; the BoE series shares the 2015=100 base (BoE 2016 = 100.66 vs ONS 100.7), so the two splice directly")
                   + f". Ratio {BASE_YEAR}/{y} = {m:.5g}: £1 in {y} bought what £{m:.4g} bought in {BASE_YEAR}."))
    out.append(src("g5a_2025", f"{BASE_YEAR} annual average exchange rate ${GBP_USD_2025} per £1, used to express {BASE_YEAR} pounds in {BASE_YEAR} dollars."))
    return out


def us_cpi_sources(y):
    m = US_CPI[BASE_YEAR] / US_CPI[y]
    return [src("mpls_cpi", f"US CPI {y} = {US_CPI[y]} vs {BASE_YEAR} = {US_CPI[BASE_YEAR]}; "
                f"$1 in {y} bought what ${m:.4g} bought in {BASE_YEAR}.")]


def gbp_to_usd2025(y, gbp):
    return gbp * UK_CPI[BASE_YEAR] / UK_CPI[y] * GBP_USD_2025


def usd_to_usd2025(y, usd):
    return usd * US_CPI[BASE_YEAR] / US_CPI[y]


# --------------------------------------------------- English mint standards
# grams of fine silver in one English penny (1d), by mint indenture
PENNY_SILVER = [  # (from_year, grams fine, note)
    (1158, 1.349, "22.5 grains sterling (.925)"),
    (1279, 1.331, "22.2 grains sterling (Edward I recoinage)"),
    (1344, 1.214, "20.25 grains sterling"),
    (1351, 1.079, "18 grains sterling"),
    (1412, 0.899, "15 grains sterling"),
    (1464, 0.719, "12 grains sterling"),
    (1526, 0.640, "10.67 grains sterling (Wolsey's recoinage)"),
    # Great Debasement: the nominal content fell to ~0.2 g, but sterling's market value (Antwerp exchange) fell only
    # ~40%, so these rows use the effective silver value of a penny rather than the coin's nominal content.
    (1542, 0.580, "effective value during the Great Debasement (coins 10 grains at .833)"),
    (1544, 0.500, "effective value during the Great Debasement (coins at .750-.500 fine)"),
    (1546, 0.400, "effective value during the Great Debasement (coins at .333-.250 fine; sterling ~40% down on the Antwerp exchange)"),
    (1552, 0.4795, "8 grains sterling (Elizabethan standard, 60s per lb)"),
    (1601, 0.464, "7.74 grains sterling (62s per troy lb, 1601-1816)"),
]
# gold:silver ratio (by weight) used before Britain's de facto gold standard of 1717
RATIO_PRE1717 = [(1200, 10.0), (1300, 11.0), (1350, 11.5), (1400, 11.0), (1500, 10.75),
                 (1550, 11.3), (1600, 12.25), (1650, 14.0), (1700, 15.0), (1717, 15.2)]
# market gold:silver ratio after 1717 (approximate annual values)
RATIO_POST1717 = [(1717, 15.2), (1750, 14.6), (1775, 14.6), (1800, 15.7), (1850, 15.7), (1870, 15.6),
                  (1875, 16.6), (1880, 18.0), (1885, 19.4), (1890, 19.8), (1895, 31.6), (1900, 33.3),
                  (1905, 31.6), (1910, 38.2), (1915, 39.8), (1920, 19.8), (1925, 29.4), (1930, 53.3), (1935, 54.0)]
GOLD_G_PER_GBP = 7.3224  # 1717-1914 (guinea of 21s / sovereign of 1817)


def interp(table, y):
    if y <= table[0][0]:
        return table[0][1]
    for (y0, v0), (y1, v1) in zip(table, table[1:]):
        if y0 <= y <= y1:
            return v0 + (v1 - v0) * (y - y0) / (y1 - y0)
    return table[-1][1]


def step(table, y):
    cur = table[0]
    for row in table:
        if row[0] <= y:
            cur = row
    return cur


def silver_gbp_per_g(y):
    """(GBP per gram of fine silver in year y, [(source key, reasoning), ...])."""
    if y < 1717:
        _, g, note = step(PENNY_SILVER, y)
        return 1 / (g * 240), [("wp_penny", f"In {y} the English penny contained {g} g fine silver ({note}), "
                                            f"so 1 g of silver = {1/g:.3f}d.")]
    r = interp(RATIO_POST1717, y)
    per_g = 1 / GOLD_G_PER_GBP / r
    return per_g, [("wp_gold_std", f"Britain was on a gold standard: £1 = {GOLD_G_PER_GBP} g fine gold."),
                   ("mw_gsr", f"Market gold:silver price ratio in {y} ≈ {r:.1f}:1, so 1 g of silver ≈ {per_g*240:.3f}d.")]


def gold_gbp_per_g(y):
    if y >= 1717:
        return 1 / GOLD_G_PER_GBP, [("wp_gold_std", f"Under the British gold standard £1 = {GOLD_G_PER_GBP} g fine gold.")]
    s, why = silver_gbp_per_g(y)
    r = interp(RATIO_PRE1717, y)
    return s * r, why + [("mw_gsr", f"Gold:silver value ratio in {y} ≈ {r:.2f}:1 (interpolated), so 1 g gold ≈ {s*r*240:.1f}d."),
                         ("wp_bimet", "Background on bimetallic ratios: ~10-12:1 in the late Middle Ages, rising to ~15:1 by 1700.")]


# ----------------------------------------------------------------- framework
BAND = {"high": 1.1, "medium": 1.35, "low": 2.0, "very low": 3.0}


def point(y, value, confidence, sources, method, low=None, high=None, provenance="computed"):
    f = BAND[confidence]
    return {"year": y, "usd2025": sig(value), "low": sig(low if low is not None else value / f),
            "high": sig(high if high is not None else value * f), "confidence": confidence,
            "method": method, "provenance": provenance, "sources": sources}


def via_gbp(y, gbp, confidence, bridge_sources, method, provenance="computed"):
    return point(y, gbp_to_usd2025(y, gbp), confidence, bridge_sources + uk_cpi_sources(y), method,
                 provenance=provenance)


def via_usd(y, usd, confidence, bridge_sources, method, provenance="computed"):
    return point(y, usd_to_usd2025(y, usd), confidence, bridge_sources + us_cpi_sources(y), method,
                 provenance=provenance)


def metal_point(y, grams, metal, unit, confidence, coin_src):
    fn = silver_gbp_per_g if metal == "silver" else gold_gbp_per_g
    per_g, why = fn(y)
    gbp = grams * per_g
    srcs = [coin_src(y, grams)] + [src(k, r) for k, r in why]
    srcs[-1]["reasoning"] += f" Hence 1 {unit} ({grams:.4g} g fine {metal}) ≈ {lsd(gbp)} sterling."
    return via_gbp(y, gbp, confidence, srcs, f"{metal} content → sterling → UK CPI")


def conf_by_year(y, cuts):
    """cuts: [(min_year, confidence), ...] ascending."""
    c = cuts[0][1]
    for yy, cc in cuts:
        if y >= yy:
            c = cc
    return c


def years(a, b, stepn=5):
    return list(range(a, b + 1, stepn))


def usd_per_unit_modern(code, y):
    """USD per unit for M14/G.5A-covered currencies, with sources."""
    if y in G5A and code in G5A[y]:
        key = {2025: "g5a_2025", 2020: "g5a_2020", 2015: "g5a_2015"}[y]
        r = G5A[y][code]
        if code in ("GBP", "EUR"):
            return r, src(key, f"{y} annual average: ${r} per {code}.")
        return 1 / r, src(key, f"{y} annual average: {r} {code} per US dollar → ${1/r:.5g} per {code}.")
    if code in EURO_FIXED and y >= 1999:
        eur = M14["USD"][y] / M14["EUR"][y]
        r = EURO_FIXED[code]
        return eur / r, src("boe_m14", f"{y}: euro averaged ${eur:.4f} (from $/£ {M14['USD'][y]:.4f} ÷ €/£ {M14['EUR'][y]:.4f}); "
                                       f"legacy {code} fixed at {r} per euro → ${eur/r:.5g} per {code}.")
    usd_gbp, x_gbp = M14["USD"][y], M14[code][y]
    v = usd_gbp / x_gbp
    return v, src("boe_m14", f"{y} annual averages: ${usd_gbp:.4f} per £ and {x_gbp:.5g} {code} per £ → "
                             f"cross rate ${v:.5g} per {code}.")


def modern_point(code, y, unit, confidence="high", extra=None):
    v, s = usd_per_unit_modern(code, y)
    return via_usd(y, v, confidence, [s] + (extra or []), "exchange rate → US CPI")


def compiled_usd_point(y, usd, unit, confidence, key, note, extra=None):
    s = src(key, f"{note} Approximate {y} value: ${usd:.5g} per {unit}.")
    return via_usd(y, usd, confidence, [s] + (extra or []), "exchange rate → US CPI", provenance="compiled")


def compiled_gbp_point(y, gbp, unit, confidence, keys_notes):
    srcs = [src(k, n + f" Hence 1 {unit} ≈ {lsd(gbp)} sterling in {y}.") for k, n in keys_notes]
    return via_gbp(y, gbp, confidence, srcs, "parity/exchange rate → sterling → UK CPI", provenance="compiled")


def den(id_, name, value=None, periods=None, symbol=None, valid=None, notes=None, aliases=None):
    d = {"id": id_, "name": name}
    if symbol:
        d["symbol"] = symbol
    if value is not None:
        d["value"] = value
    if periods:
        d["periods"] = [{"from": a, "to": b, "value": v} for a, b, v in periods]
    if valid:
        d["validFrom"], d["validTo"] = valid
    if aliases:
        d["aliases"] = aliases
    if notes:
        d["notes"] = notes
    return d


CURRENCIES = []


def currency(id_, name, region, era, base, denominations, series, notes, successor=None, aliases=None, work=None):
    c = {"id": id_, "name": name, "region": region, "era": era, "baseUnit": base,
         "aliases": aliases or [], "notes": notes, "denominations": denominations, "series": series}
    if work:
        c["fictional"] = True
        c["work"] = work
    if successor:
        c["successor"] = successor
    CURRENCIES.append(c)


# ============================================================ BRITISH ISLES
gbp_conf = [(1209, "low"), (1500, "medium"), (1870, "high")]
gbp_series = [via_gbp(y, 1.0, conf_by_year(y, gbp_conf),
                      [src("wp_ster", "The pound sterling is the anchor unit itself (1 £ = 20s = 240d before 1971, 100p after).")],
                      "UK CPI") for y in years(1210, 2025)]
currency("gbp", "Pound sterling", "England / Great Britain / United Kingdom", [1209, None], "pound", [
    den("pound", "Pound (sovereign/quid)", 1, symbol="£", aliases=["quid", "l.", "pound sterling", "sovereign"],
        notes="Before 1971: £1 = 20 shillings = 240 pence. 'l.' (libra) was often used for pounds."),
    den("mark", "Mark (money of account)", 2 / 3, valid=(1100, 1700), notes="13s 4d; an accounting unit, not a coin."),
    den("noble", "Noble", 1 / 3, valid=(1344, 1464), notes="Gold coin of 6s 8d."),
    den("angel", "Angel", periods=[(1465, 1525, 1 / 3), (1526, 1543, 0.375), (1544, 1550, 0.4), (1551, 1611, 0.5), (1612, 1642, 0.55)],
        notes="Gold coin; 6s 8d at issue, later raised to 7s 6d, 8s, 10s and 11s."),
    den("sovereign_tudor", "Sovereign (Tudor)", periods=[(1489, 1525, 1.0), (1526, 1550, 1.125), (1551, 1603, 1.5)],
        notes="Large gold coin: 20s, then 22s 6d, then 30s (the 'fine sovereign')."),
    den("guinea", "Guinea", periods=[(1663, 1679, 1.05), (1680, 1693, 1.075), (1694, 1696, 1.4), (1697, 1716, 1.075), (1717, 2100, 1.05)],
        notes="Gold coin 1663-1814. Floated in value (peaking ~30s in 1694-96) until fixed at 21s in 1717; "
              "thereafter 21s and used as an accounting unit (professional fees, horses, art) long after the coin ceased."),
    den("sovereign", "Sovereign", 1.0, valid=(1817, 2100), notes="Gold £1 coin from 1817 (7.32 g fine gold)."),
    den("half_sovereign", "Half sovereign", 0.5, valid=(1817, 2100)),
    den("crown", "Crown", 0.25, valid=(1526, 1965), notes="5 shillings."),
    den("half_crown", "Half-crown", 0.125, valid=(1549, 1970), aliases=["half a crown", "half a dollar (slang)"], notes="2s 6d."),
    den("florin", "Florin", 0.1, valid=(1849, 1971), aliases=["two-bob bit"],
        notes="2 shillings; introduced 1849 as a step toward decimalisation; continued as the 10p coin."),
    den("shilling", "Shilling", 0.05, symbol="s", valid=(1200, 1971), aliases=["bob", "s."],
        notes="12 pence. Coin from 1504; before that a unit of account. After 1971 = 5p."),
    den("sixpence", "Sixpence", 1 / 40, valid=(1551, 1971), aliases=["tanner"]),
    den("groat", "Groat", 1 / 60, valid=(1279, 1662), notes="4 pence."),
    den("threepence", "Threepence", 1 / 80, valid=(1551, 1971), aliases=["thruppence", "threepenny bit"]),
    den("twopence", "Twopence", 1 / 120, aliases=["tuppence"]),
    den("penny", "Penny (old)", 1 / 240, symbol="d", valid=(700, 1971), aliases=["d.", "denarius", "copper"],
        notes="'d' for denarius. 240 to the pound."),
    den("halfpenny", "Halfpenny", 1 / 480, aliases=["ha'penny"]),
    den("farthing", "Farthing", 1 / 960, valid=(1279, 1960), notes="Quarter penny."),
    den("new_penny", "Penny (decimal)", 0.01, symbol="p", valid=(1971, 2100), aliases=["new penny", "pence"]),
], gbp_series, "Values are UK consumer-price equivalents (what the money would buy in goods), converted to "
                "dollars at the 2025 exchange rate. Pre-1500 index values rest on few commodity prices; "
                "for wages or social status the 'feel' of a sum can be several times larger.",
         aliases=["sterling", "pounds, shillings and pence", "£sd", "LSD"])

# --- Pound Scots
SCOTS_RATIO = [(1370, 1.2), (1390, 2.0), (1425, 2.5), (1450, 2.5), (1475, 3.0), (1500, 3.5), (1525, 4.0),
               (1550, 4.5), (1560, 5.0), (1575, 6.0), (1585, 8.0), (1595, 10.0), (1600, 12.0), (1707, 12.0)]
scots_series = []
for y in years(1370, 1705):
    r = interp(SCOTS_RATIO, y)
    scots_series.append(compiled_gbp_point(y, 1 / r, "pound Scots", "medium" if y >= 1600 else "low", [
        ("wp_scots", f"The pound Scots parted from sterling after c.1367 and was worth about £{r:.2g} Scots per £1 sterling "
                     f"in {y}" + (" (fixed at 12:1 from the Union of the Crowns, 1603)." if y >= 1600 else
                                   " (interpolated between attested ratios).")),
        ("gemmill", "Gemmill & Mayhew document the Scots/sterling exchange through the medieval period.")]))
currency("scots", "Pound Scots", "Scotland", [1370, 1707], "pound Scots", [
    den("pound", "Pound Scots", 1, aliases=["£ Scots"]),
    den("merk", "Merk", 2 / 3, notes="13s 4d Scots; a common unit for rents and dowries."),
    den("shilling", "Shilling Scots", 0.05),
    den("bawbee", "Bawbee", 1 / 40, valid=(1538, 1707), notes="6 pence Scots (= ½d sterling after 1603)."),
    den("plack", "Plack", 1 / 60, notes="4 pence Scots."),
    den("bodle", "Bodle / turner", 1 / 120, notes="2 pence Scots."),
    den("penny", "Penny Scots", 1 / 240),
], scots_series, "After 1603 £12 Scots = £1 sterling, so '100 merks' ≈ £5 11s sterling. Abolished by the Acts of Union 1707 "
                 "but used in Scottish accounts well into the 18th century.", successor="gbp")

irish_series = [compiled_gbp_point(y, 12 / 13, "Irish pound", "medium", [
    ("wp_irish", "Irish currency was rated at £13 Irish = £12 sterling (an Irish shilling = 13 Irish pence = 12d sterling).")])
    for y in years(1705, 1825)]
currency("iep_old", "Irish pound (pre-1826)", "Ireland", [1701, 1826], "Irish pound", [
    den("pound", "Pound (Irish)", 1), den("shilling", "Shilling (Irish)", 0.05),
    den("penny", "Penny (Irish)", 1 / 240), den("guinea", "Guinea (in Ireland)", 22.75 / 20, notes="Passed for £1 2s 9d Irish."),
], irish_series, "Same £sd structure as sterling but at a 1/13 discount. Assimilated to sterling in 1826.", successor="gbp")

# ============================================================ UNITED STATES
usd_series = []
for y in years(1795, 2025):
    if y < 1800:
        r = USD_PER_GBP[y]
        usd_series.append(via_gbp(y, 1 / r, "medium", [
            src("boe_fx", f"{y} average exchange rate ${r:.3f} per £, so $1 = {lsd(1/r)}."),
            src("wp_usd", "The early dollar was defined by the Spanish milled dollar (≈ 4s 6d sterling).")],
            "exchange rate → sterling → UK CPI (US CPI series starts 1800)"))
    else:
        usd_series.append(via_usd(y, 1.0, "high" if y >= 1850 else "medium",
                                  [src("wp_usd", "The US dollar is the anchor unit itself.")], "US CPI"))
currency("usd", "United States dollar", "United States", [1792, None], "dollar", [
    den("dollar", "Dollar", 1, symbol="$", aliases=["buck", "greenback", "piece of eight (early)"]),
    den("eagle", "Eagle", 10, valid=(1795, 1933), notes="Gold $10 coin."),
    den("double_eagle", "Double eagle", 20, valid=(1850, 1933)),
    den("half_eagle", "Half eagle", 5, valid=(1795, 1929)),
    den("quarter_eagle", "Quarter eagle", 2.5, valid=(1796, 1929)),
    den("half_dollar", "Half dollar", 0.5, aliases=["four bits"]),
    den("quarter", "Quarter", 0.25, aliases=["two bits"]),
    den("bit", "Bit", 0.125, notes="One Spanish real; survives in 'two bits' = 25¢."),
    den("dime", "Dime", 0.1),
    den("nickel", "Nickel / half dime", 0.05),
    den("cent", "Cent", 0.01, symbol="¢", aliases=["penny", "copper"]),
    den("mill", "Mill", 0.001, notes="Accounting unit, 1/10 cent (used in tax rates)."),
], usd_series, "Pre-1800 values use the sterling route because the US CPI series begins in 1800. Before 1857 Spanish/Mexican "
               "silver dollars and reales circulated legally alongside US coin; colonial 'pounds' (e.g. Massachusetts lawful "
               "money, 6s = $1; New York money, 8s = $1) are not modelled here.",
         aliases=["US dollar", "American dollar"])

# ============================================================ SPANISH DOLLAR
SPD_SILVER = [(1497, 25.56, "27.47 g at .931 fine (1497 standard)"), (1728, 24.82, "27.07 g at .917 (1728)"),
              (1772, 24.43, "27.07 g at .903 (1772)")]


def spd_src(y, g):
    note = step(SPD_SILVER, y)[2]
    return src("wp_spdollar", f"The 8-real piece in {y} contained {g} g fine silver: {note}.")


spd_series = []
for y in years(1575, 1850):
    g = step(SPD_SILVER, y)[1]
    p = metal_point(y, g, "silver", "Spanish dollar", "medium", spd_src)
    if y == 1715 or y == 1720:
        p["sources"].append(src("newton1717", "Newton's 1717 report found Spain's gold:silver valuation in line with Britain's, so silver-content valuation of the "
                                              "piece of eight is appropriate; the result (~4s 7d) matches the conventional 4s 6d rating."))
    spd_series.append(p)
currency("spd", "Spanish dollar (peso, real de a ocho)", "Spain, Spanish America; global trade coin", [1497, 1869],
         "dollar (8 reales)", [
             den("dollar", "Dollar / peso / piece of eight", 1, aliases=["piece of eight", "peso", "real de a ocho", "pillar dollar", "Mexican dollar"]),
             den("real", "Real (silver)", 1 / 8, aliases=["bit"]),
             den("half_real", "Half real (medio)", 1 / 16, aliases=["picayune", "fip"]),
             den("maravedi", "Maravedí", 1 / 272, notes="34 maravedís to the real (money of account)."),
             den("escudo", "Escudo (gold)", 2, notes="Gold; roughly 2 dollars (16 reales) in the 18th century."),
             den("pistole", "Pistole (2 escudos)", 4, aliases=["doblón", "doubloon (2-escudo)"],
                 notes="Two-escudo gold piece, ≈ 16-17s sterling; called a 'pistole' in English and French."),
             den("doubloon", "Doubloon (8 escudos / onza)", 16, aliases=["onza", "doblón de a ocho"],
                 notes="'Doubloon' in English usually means the 8-escudo onza (≈ £3 6s sterling); it could also mean the 2-escudo piece."),
         ], spd_series, "Valued by its silver content against English silver coinage (to 1716) or the gold standard with market "
                        "gold:silver ratios (from 1717). The Mexican peso (1821-) continued the same coin and is effectively this currency.",
         successor="usd")

# ============================================================ FRANCE
LIVRE_SILVER = [(1270, 80.9), (1290, 75), (1300, 40), (1310, 55), (1330, 50), (1340, 30), (1350, 22), (1360, 18),
                (1370, 25), (1400, 22), (1420, 12), (1430, 20), (1450, 24), (1475, 22), (1500, 21), (1525, 18),
                (1550, 17), (1575, 14), (1600, 11.7), (1625, 9.8), (1641, 8.4), (1675, 8.3), (1690, 7.5),
                (1700, 7.0), (1710, 5.6), (1715, 5.6), (1720, 3.0), (1725, 4.505), (1785, 4.505), (1786, 4.45), (1795, 4.45)]


def livre_src(y, g):
    exact = y in (1270, 1725, 1730) or y >= 1726
    return src("wp_livre" if exact else "spooner",
               f"The livre tournois in {y} represented about {g:.3g} g fine silver"
               + (" (attested standard)." if exact else
                  " (interpolated from the silver equivalents of coin issues; medieval values fluctuated sharply with royal mutations)."))


livre_series = [metal_point(y, interp(LIVRE_SILVER, y), "silver", "livre", "medium" if y >= 1550 else "low", livre_src)
                for y in years(1270, 1795)]
currency("livre", "Livre tournois", "France", [1262, 1795], "livre", [
    den("livre", "Livre (tournois)", 1, aliases=["franc (as money of account)", "pound (French)"],
        notes="Money of account: 1 livre = 20 sous = 240 deniers. 'Franc' was a common synonym."),
    den("sou", "Sou / sol", 0.05, aliases=["sol"]),
    den("denier", "Denier", 1 / 240),
    den("liard", "Liard", 1 / 80, notes="3 deniers."),
    den("gros_tournois", "Gros tournois", 0.05, valid=(1266, 1300), notes="Silver coin worth 1 sou at issue."),
    den("ecu_or", "Écu d'or", periods=[(1385, 1420, 1.125), (1421, 1474, 1.375), (1475, 1515, 1.8), (1516, 1560, 2.25),
                                       (1561, 1600, 3.0), (1601, 1640, 3.5)],
        notes="Gold écu; its value in livres rose as the livre was debased (fixed at 60 sous in 1577)."),
    den("ecu", "Écu (silver, 'écu blanc')", periods=[(1641, 1688, 3), (1689, 1708, 3.5), (1709, 1725, 5), (1726, 1795, 6)],
        notes="Large silver coin; 6 livres from 1726. The 'petit écu' was half that."),
    den("louis", "Louis d'or", periods=[(1640, 1688, 10), (1689, 1708, 12), (1709, 1725, 20), (1726, 1795, 24)],
        notes="Gold coin; 24 livres from 1726 (until the 1785 recoinage kept it at 24 with less gold)."),
    den("pistole", "Pistole (accounting)", 10, notes="10 livres; also the name for Spanish 2-escudo pieces."),
], livre_series, "Values follow the silver content of the livre. Low confidence before c.1550: medieval France saw "
                 "frequent royal debasements and recoinages not captured at 5-year resolution. John Law's paper system "
                 "(1719-20) makes 1720 especially uncertain.", successor="frf")

FRF_GBP = {1915: 26.4, 1920: 52.6, 1925: 102.4, 1930: 123.9, 1935: 74.6}
frf_series = []
for y in years(1800, 1955):
    if y <= 1910:
        frf_series.append(metal_point(y, 4.5, "silver", "franc", "high",
                                      lambda y, g: src("wp_franc", "The germinal franc (1803) contained 4.5 g fine silver; "
                                                                   "gold napoléon of 20 fr. = 5.806 g fine gold (ratio 15.5).")) if y < 1870 else
                          compiled_gbp_point(y, 1 / 25.2215, "franc", "high", [
                              ("wp_lmu", "Under the gold standard / Latin Monetary Union, £1 = 25.2215 French francs (mint parity).")]))
    elif y in FRF_GBP:
        r = FRF_GBP[y]
        usd = USD_PER_GBP[y] / r
        frf_series.append(via_usd(y, usd, "medium", [
            src("mw_fx", f"{y} average ≈ {r} francs per £ (wartime/post-war float; Poincaré stabilisation 1926-28 at 124.21/£)."),
            src("boe_fx", f"{y} average ${USD_PER_GBP[y]:.4f} per £ → ${usd:.4g} per franc.")],
            "exchange rate → US CPI", provenance="compiled"))
    elif y == 1940:
        frf_series.append(compiled_usd_point(y, 1 / 43.8, "franc", "low", "mw_fx",
                                             "1940 rate ≈ 43.8 francs per US dollar before occupation (rates then administered)."))
    else:
        r = FFR_1938[y]
        usd = USD_PER_GBP[y] / r
        frf_series.append(via_usd(y, usd, "medium", [
            src("boe_a33ffr", f"{y}: {r} francs per £."),
            src("boe_fx", f"{y}: ${USD_PER_GBP[y]:.4f} per £ → ${usd:.4g} per franc.")], "exchange rate → US CPI"))
currency("frf", "French franc (1795-1959)", "France", [1795, 1959], "franc", [
    den("franc", "Franc", 1, symbol="F", aliases=["livre (colloquial, early 19th c.)"]),
    den("centime", "Centime", 0.01),
    den("decime", "Décime", 0.1),
    den("sou", "Sou", 0.05, notes="Colloquial for 5 centimes; '100 sous' = 5 francs."),
    den("ecu", "Écu / pièce de cent sous", 5, notes="Silver 5-franc piece."),
    den("napoleon", "Napoléon / louis", 20, valid=(1803, 1914), aliases=["louis", "louis d'or (19th c.)"],
        notes="Gold 20-franc coin; often still called a 'louis' in fiction."),
], frf_series, "1795 francs exchanged at 81 livres = 80 francs. Pre-1870 values via silver; 1870-1910 via gold parity; "
               "1915+ via exchange rates and US CPI. Wartime and occupation years are uncertain.", successor="frf_new")

nf_series = []
for y in years(1960, 2000):
    if y == 1960:
        r = FFR_1938[1960]
        nf_series.append(via_usd(y, USD_PER_GBP[y] / r, "high", [src("boe_a33ffr", f"1960: {r} new francs per £."),
                                                                   src("boe_fx", f"1960: ${USD_PER_GBP[y]:.4f} per £.")],
                                 "exchange rate → US CPI"))
    else:
        nf_series.append(modern_point("FRF", y, "franc"))
currency("frf_new", "French new franc (1960-2001)", "France", [1960, 2001], "franc", [
    den("franc", "Franc", 1, symbol="F", aliases=["nouveau franc", "NF"]),
    den("centime", "Centime", 0.01),
    den("old_franc", "Ancien franc", 0.01, notes="Many French people kept counting in old francs for decades; 1 NF = 100 old francs."),
], nf_series, "Replaced by the euro at 6.55957 francs per euro.", successor="eur")

# ============================================================ GERMAN LANDS
thaler_series = [metal_point(y, 16.704, "silver", "Prussian thaler", "medium",
                             lambda y, g: src("wp_thaler", "Graumann standard of 1750: 14 thalers per Cologne mark of fine silver = 16.704 g; "
                                                           "the 1857 Vereinsthaler (16.667 g) was essentially identical."))
                 for y in years(1750, 1870)]
currency("thaler", "Prussian / North German thaler", "Prussia and North Germany", [1750, 1873], "thaler", [
    den("thaler", "Thaler", 1, aliases=["Reichsthaler", "Taler", "Vereinsthaler", "rix-dollar"]),
    den("gute_groschen", "Gute Groschen", 1 / 24, valid=(1750, 1821)),
    den("silbergroschen", "Silbergroschen", 1 / 30, valid=(1821, 1873), aliases=["Sgr", "groschen"]),
    den("pfennig", "Pfennig", periods=[(1750, 1820, 1 / 288), (1821, 1873, 1 / 360)]),
    den("friedrich_dor", "Friedrich d'or", 5, notes="Gold pistole nominally 5 thalers (traded at a premium, ~5⅔)."),
    den("gulden_sd", "South German gulden", 4 / 7, valid=(1837, 1875), aliases=["florin (south German)"],
        notes="Bavaria, Württemberg, Baden, Frankfurt: 1¾ gulden = 1 thaler; 1 gulden = 60 kreuzer."),
    den("kreuzer_sd", "Kreuzer (south German)", 4 / 420),
    den("mark", "Mark (1873 conversion)", 1 / 3, notes="1 thaler = 3 marks at the 1873 conversion."),
], thaler_series, "Valued by silver content. Other German states used thalers and gulden of similar silver standards.",
         successor="mark")

MARK_USD = {1915: (1 / 4.92, "medium", "1915 average ≈ 4.9 marks per $ (par 4.198)."),
            1920: (1 / 57.0, "low", "1920 average ≈ 57 paper marks per $ (rate swung between ~39 and ~99 during the year).")}
mark_series = []
for y in years(1875, 1920):
    if y <= 1910:
        mark_series.append(compiled_gbp_point(y, 1 / 20.43, "mark", "high", [
            ("wp_goldmark", "Gold mark: 1 mark = 0.358423 g fine gold, so £1 = 20.43 marks.")]))
    else:
        v, c, n = MARK_USD[y]
        mark_series.append(compiled_usd_point(y, v, "mark", c, "wp_papiermark", n, [src("mw_fx", "Annual average dollar rate of the mark.")]))
currency("mark", "German mark (Goldmark / Papiermark)", "German Empire", [1873, 1923], "mark", [
    den("mark", "Mark", 1, symbol="M", aliases=["Goldmark", "Papiermark", "Reichsmark (loosely)"]),
    den("pfennig", "Pfennig", 0.01),
    den("thaler", "Thaler (coin, still current to 1907)", 3),
    den("krone", "Krone (gold 10 marks)", 10),
    den("doppelkrone", "Doppelkrone (gold 20 marks)", 20),
], mark_series, "Hyperinflation: by November 1923 a US dollar cost 4.2 trillion marks; the Rentenmark replaced it at 1 per "
                "1,000,000,000,000 marks. Years 1921-1924 are deliberately omitted.", successor="reichsmark")

RM_USD = {1925: (1 / 4.20, "high", "Reichsmark parity 4.20 RM per $."), 1930: (1 / 4.20, "high", "Reichsmark parity 4.20 RM per $."),
          1935: (1 / 2.49, "medium", "After the 1934 dollar devaluation, ≈ 2.49 RM per $ (exchange controls)."),
          1940: (1 / 2.50, "low", "Official ≈ 2.50 RM per $; currency inconvertible under exchange control.")}
rm_series = [compiled_usd_point(y, v, "Reichsmark", c, "wp_reichsmark", n) for y, (v, c, n) in RM_USD.items()]
currency("reichsmark", "Reichsmark", "Germany", [1924, 1948], "Reichsmark", [
    den("rm", "Reichsmark", 1, symbol="RM", aliases=["Rentenmark"]), den("rpf", "Reichspfennig", 0.01),
], rm_series, "1945 omitted: no meaningful exchange rate (occupation rate 10 RM/$; black-market cigarette economy).",
         successor="dem")

dem_series = []
for y in years(1950, 2000):
    if y < 1965:
        r = {1950: 4.20, 1955: 4.20, 1960: 4.17}[y]
        dem_series.append(compiled_usd_point(y, 1 / r, "Deutsche Mark", "high", "wp_dm", f"{y} parity ≈ {r} DM per $ (Bretton Woods)."))
    else:
        dem_series.append(modern_point("DEM", y, "Deutsche Mark"))
currency("dem", "Deutsche Mark", "West Germany / Germany", [1948, 2001], "Deutsche Mark", [
    den("dm", "Deutsche Mark", 1, symbol="DM", aliases=["D-Mark", "Mark"]), den("pf", "Pfennig", 0.01),
    den("groschen", "Groschen (colloquial)", 0.1), den("heiermann", "Heiermann (slang)", 5),
], dem_series, "Replaced by the euro at 1.95583 DM per euro.", successor="eur")

# ============================================================ AUSTRIA
AUG_SILVER = [(1760, 11.69, "Conventionsfuß of 1753: 20 gulden per Cologne mark = 11.69 g"),
              (1858, 11.11, "Austrian standard of 1857: 45 gulden per Zollpfund = 11.11 g")]
aug_series = [metal_point(y, step(AUG_SILVER, y)[1], "silver", "gulden", "medium",
                          lambda y, g: src("wp_augulden", f"{step(AUG_SILVER, y)[2]}. Paper gulden often traded at a discount "
                                                          "to silver (severely c.1800-1816 and 1848-1878)."))
              for y in years(1760, 1890)]
currency("aut_gulden", "Austrian gulden (florin)", "Habsburg monarchy", [1754, 1892], "gulden", [
    den("gulden", "Gulden / florin", 1, symbol="fl.", aliases=["florin", "fl."]),
    den("kreuzer", "Kreuzer", periods=[(1754, 1857, 1 / 60), (1858, 1892, 1 / 100)], aliases=["kr."]),
    den("conventionsthaler", "Conventionsthaler / Maria Theresa thaler", 2),
    den("ducat", "Ducat (Austrian gold)", 4.5, notes="Approximate; market rate varied."),
    den("krone", "Krone (1892 conversion)", 0.5),
], aug_series, "Valued at the silver standard; paper money traded below silver in war periods, so these are upper values for those years.",
         successor="aut_krone")
krone_series = [compiled_gbp_point(y, 1 / 24.02, "krone", "high", [
    ("wp_krone", "1 krone = 0.304878 g fine gold, giving £1 = 24.02 kronen.")]) for y in years(1895, 1910)]
currency("aut_krone", "Austro-Hungarian krone", "Austria-Hungary", [1892, 1918], "krone", [
    den("krone", "Krone / korona", 1, symbol="K"), den("heller", "Heller / fillér", 0.01), den("gulden", "Gulden (old)", 2),
], krone_series, "Lost most of its value during and after WWI; post-1914 values not modelled.")

# ============================================================ ITALY
FLORENCE_LIRA = [(1252, 1252, 1.0), (1253, 1299, 2.0), (1300, 1349, 3.0), (1350, 1399, 3.5), (1400, 1449, 4.0),
                 (1450, 1474, 4.8), (1475, 1499, 5.8), (1500, 1533, 7.0)]
florin_series = [metal_point(y, 3.53, "gold", "florin", "low" if y < 1400 else "medium",
                             lambda y, g: src("wp_florin", "The florin was struck at 3.54 g of (nearly) pure gold throughout 1252-1533."))
                 for y in years(1255, 1530)]
currency("florin_fl", "Florentine florin", "Florence; international trade coin", [1252, 1533], "florin", [
    den("florin", "Florin (fiorino d'oro)", 1, aliases=["fiorino", "gold florin"]),
    den("lira", "Lira (di piccioli, Florentine)", periods=[(a, b, 1 / v) for a, b, v in FLORENCE_LIRA],
        notes="Silver-based money of account; the florin rose from 1 lira (1252) to ~7 lire (c.1500) — Spufford's Handbook."),
    den("soldo", "Soldo", periods=[(a, b, 1 / v / 20) for a, b, v in FLORENCE_LIRA]),
    den("denaro", "Denaro", periods=[(a, b, 1 / v / 240) for a, b, v in FLORENCE_LIRA]),
], florin_series, "Valued by gold content via English mint gold:silver ratios. 'Florin' elsewhere means the British 2s coin, "
                  "the Dutch guilder, or the Austrian gulden — see those entries.")

VENICE_LIRA = [(1284, 1349, 3.0), (1350, 1399, 3.9), (1400, 1449, 4.6), (1450, 1499, 5.5), (1500, 1549, 6.5),
               (1550, 1599, 8.5), (1600, 1649, 12.0), (1650, 1699, 17.0), (1700, 1749, 19.0), (1750, 1797, 22.0)]
ducat_series = [metal_point(y, 3.53, "gold", "ducat", "low" if y < 1400 else "medium",
                            lambda y, g: src("wp_ducat", "The Venetian ducat (zecchino) was 3.545 g of .997 gold (≈3.53 g fine), unchanged 1284-1797."))
                for y in years(1285, 1795)]
currency("ducat_ve", "Venetian ducat (zecchino)", "Venice; Mediterranean / Levant trade coin", [1284, 1797], "ducat", [
    den("ducat", "Ducat / zecchino / sequin", 1, aliases=["zecchino", "sequin", "chequin", "ducat of gold"]),
    den("lira", "Lira di piccoli", periods=[(a, b, 1 / v) for a, b, v in VENICE_LIRA],
        notes="Approximate lire per gold ducat; Spufford's Handbook of Medieval Exchange for medieval rates."),
    den("soldo", "Soldo", periods=[(a, b, 1 / v / 20) for a, b, v in VENICE_LIRA]),
    den("grosso", "Grosso", 1 / 24, valid=(1284, 1380), notes="Ducat originally = 24 grossi."),
    den("ducato_conto", "Ducat of account (6 lire 4 soldi)", periods=[(a, b, 6.2 / v) for a, b, v in VENICE_LIRA if a >= 1500],
        notes="From c.1517 the 'ducat' in accounts meant 6.2 lire, diverging from the gold zecchino."),
], ducat_series, "'Ducat' also names gold coins of Hungary, Holland, Austria etc. of similar weight (~3.4-3.5 g), "
                 "so this series is a reasonable proxy for any 'ducat' in European literature.",
         aliases=["sequin", "zecchino"])

ITL_AGIO = {1865: 1.0, 1870: 1.05, 1875: 1.10, 1880: 1.07, 1885: 1.0, 1890: 1.01, 1895: 1.06, 1900: 1.06, 1905: 1.0, 1910: 1.0}
ITL_USD = {1915: (0.165, "medium", "1915 ≈ 6.1 lire per $ (wartime depreciation from par 5.18)."),
           1920: (0.0500, "medium", "1920 ≈ 20 lire per $."), 1925: (0.0397, "medium", "1925 ≈ 25.2 lire per $."),
           1930: (0.0524, "high", "1927-36 'quota 90' parity ≈ 19.08 lire per $."),
           1935: (0.0814, "medium", "1935 ≈ 12.3 lire per $ (after dollar devaluation)."),
           1940: (0.0505, "low", "1940 official ≈ 19.8 lire per $."), 1945: (0.01, "very low", "1945 ≈ 100 lire per $ (Allied military rate)."),
           1950: (1 / 625, "high", "Bretton Woods parity 625 lire per $ (1949-71)."), 1955: (1 / 625, "high", "Parity 625 lire per $."),
           1960: (1 / 621, "high", "≈ 621 lire per $.")}
lira_series = []
for y in years(1865, 2000):
    if y <= 1910:
        a = ITL_AGIO[y]
        lira_series.append(compiled_gbp_point(y, 1 / 25.2215 / a, "lira", "medium", [
            ("wp_lmu", "LMU parity: 1 lira = 1 franc = 1/25.2215 £."),
            ("wp_lira", f"Inconvertible paper lira traded at ≈ {a:.2f} lire per gold lira in {y} (agio)." if a != 1 else
             f"Lira at or near gold parity in {y}.")]))
    elif y in ITL_USD:
        v, c, n = ITL_USD[y]
        lira_series.append(compiled_usd_point(y, v, "lira", c, "wp_lira", n, [src("mw_fx", "Annual average dollar rate.")]))
    else:
        lira_series.append(modern_point("ITL", y, "lira"))
currency("itl", "Italian lira", "Italy", [1861, 2001], "lira", [
    den("lira", "Lira", 1, symbol="L."), den("centesimo", "Centesimo", 0.01),
    den("soldo", "Soldo (colloquial)", 0.05), den("scudo", "Scudo (5 lire silver)", 5),
], lira_series, "Replaced by the euro at 1936.27 lire per euro. Pre-unification Italian states had their own lire, scudi and ducats.",
         successor="eur")

# ============================================================ NETHERLANDS
NLG_SILVER = [(1600, 10.4), (1620, 10.0), (1660, 9.613), (1840, 9.613), (1841, 9.45), (1874, 9.45)]
NLG_USD = {1915: 0.405, 1920: 0.33, 1925: 0.401, 1930: 0.402, 1935: 0.677, 1940: 0.532, 1945: 0.377,
           1950: 0.263, 1955: 0.263, 1960: 0.265}
nlg_series = []
for y in years(1600, 2000):
    if y <= 1870:
        nlg_series.append(metal_point(y, interp(NLG_SILVER, y), "silver", "guilder", "medium",
                                      lambda y, g: src("wp_guilder", f"Guilder of {y} ≈ {g:.4g} g fine silver "
                                                                     "(1681 standard 9.613 g; 1840 reduced to 9.45 g; pre-1681 interpolated).")))
    elif y <= 1910:
        nlg_series.append(compiled_gbp_point(y, 1 / 12.107, "guilder", "high", [("wp_guilder", "Gold standard from 1875: £1 = 12.107 guilders.")]))
    elif y in NLG_USD:
        v = NLG_USD[y]
        nlg_series.append(compiled_usd_point(y, v, "guilder", "high" if y >= 1950 else "medium", "mw_fx",
                                             f"Approximate annual average ({1/v:.3g} guilders per $)."))
    elif y == 2000:
        nlg_series.append(modern_point("NLG", y, "guilder"))
    else:
        nlg_rates = {1965: 3.60, 1970: 3.60, 1975: 2.53, 1980: 1.99, 1985: 3.32, 1990: 1.82, 1995: 1.61}
        nlg_series.append(compiled_usd_point(y, 1 / nlg_rates[y], "guilder", "high", "mw_fx",
                                             f"{y} annual average ≈ {nlg_rates[y]} guilders per $."))
currency("nlg", "Dutch guilder", "Dutch Republic / Netherlands", [1575, 2001], "guilder", [
    den("guilder", "Guilder / gulden", 1, symbol="ƒ", aliases=["gulden", "florin", "fl."]),
    den("stuiver", "Stuiver", 0.05, aliases=["stiver"]),
    den("duit", "Duit", 1 / 160, aliases=["doit"], notes="8 duiten to the stuiver; English 'not worth a doit'."),
    den("schelling", "Schelling", 0.3, notes="6 stuivers."),
    den("daalder", "Daalder", 1.5, notes="30 stuivers."),
    den("rijksdaalder", "Rijksdaalder", 2.5, aliases=["rixdollar"]),
    den("ducaton", "Ducaton (silver rider)", 3.15, notes="63 stuivers."),
    den("cent", "Cent", 0.01, valid=(1817, 2001)),
    den("dubbeltje", "Dubbeltje", 0.1, valid=(1817, 2001)),
    den("kwartje", "Kwartje", 0.25, valid=(1817, 2001)),
    den("tientje", "Gouden tientje", 10, valid=(1875, 1933)),
], nlg_series, "Replaced by the euro at 2.20371 guilders per euro.", successor="eur")

# ============================================================ PORTUGAL
milreis_series = []
for y in years(1725, 1890):
    if y < 1855:
        milreis_series.append(metal_point(y, 2.053, "gold", "milréis", "medium",
                                          lambda y, g: src("wp_moidore", "Gold peça/johannes of 6,400 réis held ≈ 13.14 g fine gold "
                                                                         "(moidore of 4,800 réis passed at 27s in Britain) → 2.053 g gold per 1,000 réis.")))
    else:
        milreis_series.append(compiled_gbp_point(y, 1 / 4.5, "milréis", "high",
                                                 [("wp_real_pt", "Gold standard of 1854: £1 = 4,500 réis.")]))
currency("pte_real", "Portuguese real / milréis", "Portugal, Brazil (colonial)", [1500, 1911], "milréis (1,000 réis)", [
    den("milreis", "Milréis (1,000 réis)", 1, symbol="1$000", aliases=["mil réis"]),
    den("real", "Real (pl. réis)", 0.001, aliases=["rei", "réis"]),
    den("vintem", "Vintém", 0.02, notes="20 réis."),
    den("tostao", "Tostão", 0.1, notes="100 réis."),
    den("cruzado", "Cruzado", 0.4, notes="400 réis (later 480)."),
    den("moidore", "Moidore (moeda d'ouro)", 4.8, aliases=["moeda"], notes="Gold 4,800 réis; current in England and its colonies at 27s."),
    den("johannes", "Johannes / joe / peça", 6.4, aliases=["joe", "half-joe (3.2)"], notes="Gold 6,400 réis; ≈ 36s sterling."),
    den("conto", "Conto (de réis)", 1000, notes="1,000,000 réis."),
], milreis_series, "The moidore and johannes were widely used in British America and the Caribbean. "
                   "Post-1891 depreciation and the 1911 escudo (= 1,000 réis) not modelled.")

# ============================================================ RUSSIA
RUB_SILVER = [(1705, 24.0), (1718, 20.7), (1763, 20.7), (1764, 18.0), (1840, 18.0)]
RUB_PENCE = {1845: 38.0, 1850: 38.0, 1855: 37.0, 1860: 37.0, 1865: 30.0, 1870: 30.0, 1875: 31.0, 1880: 25.0,
             1885: 24.0, 1890: 27.0, 1895: 25.4, 1900: 25.38, 1905: 25.38, 1910: 25.38}
rub_series = []
for y in years(1705, 1915):
    if y <= 1840:
        rub_series.append(metal_point(y, interp(RUB_SILVER, y), "silver", "silver ruble", "medium",
                                      lambda y, g: src("wp_ruble", f"Silver ruble of {y} ≈ {g:.3g} g fine silver "
                                                                   "(Peter I's coinage reduced to 1718; Catherine II's 1764 standard of 18 g held to 1885).")))
    elif y <= 1910:
        p = RUB_PENCE[y]
        notes = [("wp_ruble", f"{y}: ruble ≈ {p}d sterling" + (" (Witte gold standard: £1 = 9.457 rubles)." if y >= 1900 else
                                                                  " (credit-ruble exchange rate in London; paper inconvertible 1858-1897)."))]
        rub_series.append(compiled_gbp_point(y, p / 240, "ruble", "high" if y >= 1900 else "medium", notes))
    else:
        rub_series.append(compiled_usd_point(y, 0.33, "ruble", "low", "wp_ruble", "1915 ≈ 3 rubles per $ (par 1.94) as wartime inflation began."))
currency("rub_imp", "Russian ruble (imperial)", "Russian Empire", [1704, 1917], "ruble", [
    den("ruble", "Ruble (rouble)", 1, symbol="руб.", aliases=["rouble", "silver ruble", "credit ruble"]),
    den("kopek", "Kopek (kopeck)", 0.01),
    den("denga", "Denga / denezhka", 0.005, notes="½ kopek."),
    den("polushka", "Polushka", 0.0025, notes="¼ kopek."),
    den("altyn", "Altyn", 0.03, notes="3 kopeks."),
    den("grivennik", "Grivennik / grivna", 0.1, notes="10 kopeks."),
    den("pyatialtynny", "Piatialtynnyi", 0.15, notes="15 kopeks."),
    den("chetvertak", "Chetvertak / polupoltina", 0.25),
    den("poltina", "Poltina / poltinnik", 0.5),
    den("imperial", "Imperial (gold)", periods=[(1755, 1896, 10), (1897, 1917, 15)], notes="Gold 10-ruble coin, revalued to 15 in 1897."),
    den("half_imperial", "Half-imperial", periods=[(1755, 1896, 5), (1897, 1917, 7.5)]),
    den("assignat", "Assignat ruble (paper)", periods=[(1769, 1786, 1.0), (1787, 1795, 0.8), (1796, 1805, 0.7), (1806, 1809, 0.5),
                                                       (1810, 1823, 0.26), (1824, 1838, 0.28), (1839, 1843, 1 / 3.5)],
        notes="Paper ruble in silver-ruble terms. Many prices in Pushkin- and Gogol-era fiction are in assignats; 1839 fixed at 3.5 assignats = 1 silver ruble."),
], rub_series, "Base unit is the silver ruble to 1840, then the circulating credit ruble (inconvertible, valued at London exchange) "
               "and from 1897 the gold-backed ruble.")

# ============================================================ JAPAN
# BoJ Currency Museum guidance (rice-price basis, c.2000s-2010s yen): early Edo ≈ ¥100,000/ryō; mid-late ≈ ¥40,000-60,000;
# bakumatsu ≈ ¥4,000-10,000. Wage basis (carpenters' pay) ≈ ¥300,000-400,000.
JP_CPI_FACTOR = 1.12  # Japanese CPI rose ~12% between the 2010s reference period and 2025
RYO_YEN = [(1605, 100000), (1690, 100000), (1700, 75000), (1710, 55000), (1835, 50000), (1840, 40000), (1855, 40000),
           (1860, 15000), (1865, 6000)]
ryo_series = []
for y in years(1605, 1865):
    yen = interp(RYO_YEN, y)
    usd = yen * JP_CPI_FACTOR / G5A[2025]["JPY"]
    ryo_series.append(point(y, usd, "very low", [
        src("boj_ryo", f"Rice-price basis: the Bank of Japan Currency Museum puts one ryō at ≈ ¥100,000 in early Edo, ¥40,000-60,000 in "
                       f"mid-to-late Edo and ¥4,000-10,000 in the bakumatsu inflation; interpolated ≈ ¥{yen:,.0f} for {y}, "
                       f"×{JP_CPI_FACTOR} for Japanese inflation to 2025."),
        src("wp_ryo", "Koban gold content fell from ≈15 g (Keichō 1601) to ≈1.9 g (Man'en 1860), the main driver of the declining value."),
        src("g5a_2025", f"Converted at the 2025 average of {G5A[2025]['JPY']} yen per dollar."),
        src("boj_ryo", f"Wage basis (a carpenter's pay) gives ¥300,000-400,000 per ryō, used as the upper bound.")],
        "commodity (rice) price equivalence → 2025 yen → USD", low=usd / 3,
        high=max(usd * 3, 350000 * JP_CPI_FACTOR / G5A[2025]["JPY"]) if y < 1860 else usd * 6, provenance="compiled"))
currency("ryo", "Ryō (Tokugawa coinage)", "Japan", [1601, 1871], "ryō", [
    den("ryo", "Ryō (koban)", 1, symbol="両", aliases=["koban", "oban (=10 ryō nominal, ceremonial)"]),
    den("bu", "Bu (ichibu)", 0.25, symbol="分"),
    den("shu", "Shu (isshu)", 1 / 16, symbol="朱"),
    den("mon", "Mon (copper)", periods=[(1601, 1700, 1 / 4000), (1701, 1800, 1 / 4500), (1801, 1850, 1 / 6500), (1851, 1871, 1 / 8000)],
        symbol="文", notes="Official rate 4,000 mon per ryō (1700); market rates drifted to 6,000-10,000 by the 19th century."),
    den("kanmon", "Kan (kanmon, string of 1,000 mon)", periods=[(1601, 1700, 0.25), (1701, 1800, 1000 / 4500), (1801, 1850, 1000 / 6500), (1851, 1871, 0.125)]),
    den("monme", "Monme (of silver)", 1 / 60, symbol="匁", notes="Silver by weight (3.75 g); official 60 monme per ryō from 1700, market 55-70."),
    den("kanme", "Kanme (1,000 monme of silver)", 1000 / 60),
], ryo_series, "No price index exists: values follow the Bank of Japan's rice-price rule of thumb (low end) — wage-based "
               "figures are 3-8× higher. Converted 1 ryō = 1 yen in 1871.", successor="jpy")

JPY_USD = {1915: 0.495, 1920: 0.495, 1925: 0.41, 1930: 0.494, 1935: 0.287, 1940: 0.234, 1950: 1 / 360, 1955: 1 / 360,
           1960: 1 / 360}
jpy_series = []
for y in years(1870, 2025):
    if y <= 1895:
        jpy_series.append(metal_point(y, 24.26, "silver", "yen", "medium",
                                      lambda y, g: src("wp_yen", "Silver yen (trade-dollar standard) of 1871: 26.96 g at .900 = 24.26 g fine silver; "
                                                                 "Japan was de facto on silver until 1897.")))
    elif y <= 1910:
        jpy_series.append(compiled_gbp_point(y, 1 / 9.763, "yen", "high", [("wp_yen", "Gold yen of 1897 (0.75 g fine gold): £1 = 9.763 yen, $1 = 2.006 yen.")]))
    elif y == 1945:
        continue
    elif y in JPY_USD:
        v = JPY_USD[y]
        jpy_series.append(compiled_usd_point(y, v, "yen", "high" if y >= 1950 else "medium", "mw_fx",
                                             f"Approximate annual average ({1/v:.4g} yen per $)." + (" Fixed 360/$ 1949-71." if y >= 1950 else "")))
    else:
        jpy_series.append(modern_point("JPY", y, "yen"))
currency("jpy", "Japanese yen", "Japan", [1871, None], "yen", [
    den("yen", "Yen", 1, symbol="¥", aliases=["en", "円"]), den("sen", "Sen", 0.01, valid=(1871, 1953)),
    den("rin", "Rin", 0.001, valid=(1871, 1953)), den("ryo", "Ryō (at 1871 conversion)", 1),
], jpy_series, "1945 omitted (no meaningful rate). Post-war inflation 1945-49 cut the yen's value by ~99%.")

# ============================================================ CHINA
TAEL_USD = {1915: 0.62, 1920: 1.24, 1925: 0.84, 1930: 0.46}
CASH_PER_TAEL = [(1650, 1700, 800), (1701, 1780, 850), (1781, 1810, 1050), (1811, 1835, 1350), (1836, 1855, 2000),
                 (1856, 1880, 1600), (1881, 1935, 1400)]
tael_series = []
for y in years(1650, 1930):
    if y <= 1910:
        tael_series.append(metal_point(y, 36.0, "silver", "tael", "medium",
                                       lambda y, g: src("wp_tael", "A tael (liang) of silver: Kuping ≈ 37.3 g, Haikwan ≈ 37.8 g; "
                                                                   "treated here as ≈ 36 g fine silver after typical sycee fineness.")))
    else:
        v = TAEL_USD[y]
        tael_series.append(compiled_usd_point(y, v, "Haikwan tael", "medium", "mw_fx",
                                              "Chinese Maritime Customs annual Haikwan tael value in dollars (followed world silver prices)."))
currency("tael", "Chinese silver tael (liang)", "China (Qing and Republic)", [1644, 1933], "tael", [
    den("tael", "Tael / liang", 1, symbol="两", aliases=["liang", "Haikwan tael", "Kuping tael"]),
    den("mace", "Mace / qian", 0.1, symbol="钱"),
    den("candareen", "Candareen / fen", 0.01, symbol="分"),
    den("li", "Li / cash (weight)", 0.001, symbol="厘"),
    den("cash", "Cash (wen, copper coin)", periods=[(a, b, 1 / v) for a, b, v in CASH_PER_TAEL], symbol="文",
        notes="Market rate of copper cash to silver; nominally 1,000 per tael."),
    den("string", "String of cash (diao/chuan)", periods=[(a, b, 1000 / v) for a, b, v in CASH_PER_TAEL],
        notes="Nominally 1,000 cash (often fewer coins in practice)."),
    den("dollar", "Silver dollar / yuan (1889-)", 0.72, aliases=["Mexican dollar (in China)", "yuan", "dollar"],
        notes="Mexican and Chinese silver dollars passed at ≈ 0.72 tael."),
    den("sycee", "Sycee ingot (yuanbao)", 50, notes="Standard large ingot ≈ 50 taels."),
], tael_series, "Silver value via the sterling route. Abolished 1933 in favour of the silver yuan.", successor="cny")

CNY_RATES = {1955: 2.46, 1960: 2.46, 1965: 2.46, 1970: 2.46, 1975: 1.86, 1980: 1.50, 1985: 2.94, 1990: 4.78,
             1995: 8.35, 2000: 8.28, 2005: 8.19, 2010: 6.77}
cny_series = []
for y in years(1955, 2025):
    if y in CNY_RATES:
        r = CNY_RATES[y]
        cny_series.append(compiled_usd_point(y, 1 / r, "yuan", "low" if y < 1980 else "medium" if y < 1995 else "high", "wp_rmb",
                                             f"{y} official rate ≈ {r} yuan per $" + (" (non-convertible currency; official rate only)." if y < 1995 else "."),
                                             [src("mw_fx", "Annual average official rate.")]))
    else:
        cny_series.append(modern_point("CNY", y, "yuan"))
currency("cny", "Renminbi (yuan)", "People's Republic of China", [1949, None], "yuan", [
    den("yuan", "Yuan", 1, symbol="¥", aliases=["renminbi", "RMB", "kuai", "元"]),
    den("jiao", "Jiao", 0.1, aliases=["mao"]), den("fen", "Fen", 0.01),
], cny_series, "1955 redenomination: 1 new yuan = 10,000 old. Pre-1980 official rates overstate what foreigners could do with the money.")

# ============================================================ INDIA
INR_SILVER = [(1600, 11.0), (1835, 11.0), (1836, 10.69)]
INR_USD = {1915: 0.324, 1920: 0.335, 1925: 0.362, 1930: 0.364, 1935: 0.369, 1940: 0.302, 1945: 0.302,
           1950: 1 / 4.762, 1955: 1 / 4.762, 1960: 1 / 4.762, 1965: 1 / 4.762, 1970: 1 / 7.5, 1975: 1 / 8.38,
           1980: 1 / 7.86, 1985: 1 / 12.37, 1990: 1 / 17.5, 1995: 1 / 32.4, 2000: 1 / 44.9, 2005: 1 / 44.1, 2010: 1 / 45.7}
inr_series = []
for y in years(1600, 2025):
    if y <= 1895:
        inr_series.append(metal_point(y, interp(INR_SILVER, y), "silver", "rupee", "medium",
                                      lambda y, g: src("wp_rupee_hist" if y < 1836 else "wp_rupee",
                                                       f"Rupee of {y} ≈ {g:.4g} g fine silver" + (" (Mughal/early Company rupees ~178 grains, ~96% fine)." if y < 1836 else
                                                                                                    " (Company rupee of 1835: 180 grains at 11/12 fine). Its sterling value fell with silver after 1873."))))
    elif y <= 1910:
        inr_series.append(compiled_gbp_point(y, 1 / 15, "rupee", "high", [("wp_rupee", "Fixed at 1s 4d (15 rupees = £1) from 1899.")]))
    elif y in INR_USD:
        v = INR_USD[y]
        inr_series.append(compiled_usd_point(y, v, "rupee", "high" if y >= 1950 else "medium", "wp_rupee",
                                             f"{y} ≈ {1/v:.4g} rupees per $ (1927-66 pegged at 1s 6d sterling; 4.76/$ 1949-66; 7.5/$ 1966-71).",
                                             [src("mw_fx", "Annual average dollar rate.")]))
    else:
        inr_series.append(modern_point("INR", y, "rupee"))
currency("inr", "Indian rupee", "Mughal India, British India, Republic of India", [1540, None], "rupee", [
    den("rupee", "Rupee / rupiya", 1, symbol="Rs", aliases=["rupiya", "₹"]),
    den("anna", "Anna", 1 / 16, valid=(1600, 1957)),
    den("pice", "Pice / paisa (old)", 1 / 64, valid=(1600, 1957)),
    den("pie", "Pie", 1 / 192, valid=(1835, 1957)),
    den("naya_paisa", "Naya paisa / paisa", 0.01, valid=(1957, 2100)),
    den("mohur", "Mohur (gold)", 15, notes="Gold coin, nominally 15 rupees (market 14-17)."),
    den("pagoda", "Star pagoda (Madras)", 3.5, valid=(1600, 1818), notes="South Indian gold coin ≈ 3½ rupees."),
    den("lakh", "Lakh", 100000), den("crore", "Crore", 10000000),
], inr_series, "Pre-1895 values via silver content; the rupee's sterling value halved between 1873 and 1894 as silver fell.")

# ============================================================ OTTOMAN
AKCE_SILVER = [(1330, 1.15), (1400, 1.0), (1455, 0.85), (1495, 0.68), (1580, 0.6), (1590, 0.38), (1600, 0.29),
               (1650, 0.25), (1685, 0.15)]
akce_series = [metal_point(y, interp(AKCE_SILVER, y), "silver", "akçe", "low",
                           lambda y, g: src("wp_akce", f"Akçe of {y} ≈ {g:.3g} g silver (Malanima/Pamuk series, interpolated; "
                                                       "1585-86 debasement halved it)."))
               for y in years(1330, 1685)]
currency("akce", "Ottoman akçe (asper)", "Ottoman Empire", [1326, 1687], "akçe", [
    den("akce", "Akçe / asper", 1, aliases=["asper", "aspre"]),
    den("para", "Para", 3, valid=(1620, 1687)),
    den("kurus", "Kuruş (when introduced)", 120),
    den("sultani", "Sultani / altın (gold)", periods=[(1478, 1550, 55), (1551, 1584, 60), (1585, 1600, 120), (1601, 1687, 230)],
        notes="Gold coin of ducat weight; rate in akçe rose with debasement."),
], akce_series, "Main Ottoman silver coin for three and a half centuries; replaced by the kuruş as unit of account after 1687.",
         successor="kurus")

KURUS_SILVER = [(1690, 17.0), (1700, 15.6), (1720, 14.0), (1750, 11.5), (1780, 9.0), (1800, 5.8), (1810, 4.5), (1820, 3.2),
                (1830, 1.5), (1840, 1.0)]
kurus_series = []
for y in years(1690, 1910):
    if y < 1845:
        kurus_series.append(metal_point(y, interp(KURUS_SILVER, y), "silver", "kuruş", "low",
                                        lambda y, g: src("pamuk", f"Kuruş of {y} ≈ {g:.3g} g fine silver (Pamuk ch. 9-11; 120 akçe = 1 kuruş, "
                                                                  "repeated debasements especially under Mahmud II, 1808-39).")))
    else:
        kurus_series.append(compiled_gbp_point(y, 0.9033 / 100, "kuruş", "medium", [
            ("wp_kurus", "1844 reform: gold lira of 6.614 g fine gold = 100 kuruş, so 1 lira ≈ 18s 1d and 1 kuruş ≈ 2.17d.")]))
currency("kurus", "Ottoman kuruş (piastre)", "Ottoman Empire; Egypt, Levant", [1687, 1923], "kuruş", [
    den("kurus", "Kuruş / piastre", 1, aliases=["piastre", "piaster", "qirsh", "ghirsh"]),
    den("para", "Para", 1 / 40), den("akce", "Akçe", 1 / 120),
    den("mecidiye", "Mecidiye (silver)", 20, valid=(1844, 1923)),
    den("lira", "Lira (gold) / Turkish pound", 100, valid=(1844, 1923), aliases=["Turkish pound", "£T"]),
    den("purse", "Purse (kese)", 500, notes="Accounting unit of 500 kuruş."),
], kurus_series, "Egyptian piastres (1834-) were a different, sterling-linked unit (£E1 = 100 piastres ≈ £1 0s 6d).",
         successor=None)

# ============================================================ MODERN EUROPE
eur_series = [modern_point("EUR", y, "euro") for y in years(2000, 2025)]
currency("eur", "Euro", "Eurozone", [1999, None], "euro", [
    den("euro", "Euro", 1, symbol="€"), den("cent", "Cent", 0.01),
], eur_series, "Fixed conversion rates: 6.55957 FRF, 1.95583 DEM, 1936.27 ITL, 166.386 ESP, 2.20371 NLG, 13.7603 ATS, 0.787564 IEP.")

CHF_USD = {1915: 0.19, 1920: 0.168, 1925: 0.193, 1930: 0.194, 1935: 0.325, 1940: 0.229, 1945: 0.233, 1950: 0.229,
           1955: 0.233, 1960: 0.231}
chf_series = []
for y in years(1850, 2025):
    if y <= 1910:
        chf_series.append(compiled_gbp_point(y, 1 / 25.2215, "Swiss franc", "high",
                                             [("wp_lmu", "Swiss franc = French franc (Latin Monetary Union / same silver and gold standard).")]))
    elif y in CHF_USD:
        v = CHF_USD[y]
        chf_series.append(compiled_usd_point(y, v, "Swiss franc", "high" if y >= 1950 else "medium", "mw_fx",
                                             f"Approximate annual average ({1/v:.3g} francs per $)."))
    else:
        chf_series.append(modern_point("CHF", y, "Swiss franc"))
currency("chf", "Swiss franc", "Switzerland", [1850, None], "franc", [
    den("franc", "Franc / Franken", 1, symbol="Fr.", aliases=["Franken", "CHF"]),
    den("rappen", "Rappen / centime", 0.01), den("batzen", "Batzen (colloquial 10 Rp.)", 0.1),
], chf_series, "")

SEK_USD = {1915: 0.27, 1920: 0.21, 1925: 0.268, 1930: 0.268, 1935: 0.253, 1940: 0.238, 1945: 0.238, 1950: 0.193,
           1955: 0.193, 1960: 0.193}
sek_series = []
for y in years(1875, 2025):
    if y <= 1910:
        sek_series.append(compiled_gbp_point(y, 1 / 18.159, "krona", "high", [("wp_sek", "Scandinavian Monetary Union gold standard: £1 = 18.16 kronor.")]))
    elif y in SEK_USD:
        v = SEK_USD[y]
        sek_series.append(compiled_usd_point(y, v, "krona", "high" if y >= 1950 else "medium", "mw_fx",
                                             f"Approximate annual average ({1/v:.3g} kronor per $)."))
    else:
        sek_series.append(modern_point("SEK", y, "krona"))
currency("sek", "Swedish krona", "Sweden (Danish and Norwegian kroner were at par until 1914)", [1873, None], "krona", [
    den("krona", "Krona", 1, symbol="kr", aliases=["krone (Danish/Norwegian, pre-1914)", "riksdaler riksmynt (1:1 in 1873)"]),
    den("ore", "Öre", 0.01),
], sek_series, "Before 1914 the Danish and Norwegian krone were interchangeable with the Swedish krona.")

ESP_GBP = {1870: 25.6, 1875: 26.0, 1880: 26.0, 1885: 26.3, 1890: 26.9, 1895: 30.0, 1900: 32.9, 1905: 32.6, 1910: 27.0}
ESP_USD = {1915: 0.19, 1920: 0.15, 1925: 0.14, 1930: 0.11, 1935: 0.137, 1940: 0.091, 1945: 0.091, 1950: 1 / 40,
           1955: 1 / 42, 1960: 1 / 60, 1965: 1 / 60, 1970: 1 / 70}
esp_series = []
for y in years(1870, 2000):
    if y in ESP_GBP:
        r = ESP_GBP[y]
        esp_series.append(compiled_gbp_point(y, 1 / r, "peseta", "medium", [
            ("wp_peseta", f"Peseta nominally at LMU parity (25.22/£) but on an inconvertible paper/silver basis; London rate ≈ {r} per £ in {y}.")]))
    elif y in ESP_USD:
        v = ESP_USD[y]
        esp_series.append(compiled_usd_point(y, v, "peseta", "low" if 1935 < y < 1960 else "medium", "mw_fx",
                                             f"Approximate annual average ({1/v:.3g} pesetas per $)" + (
                                                 "; multiple official rates under Franco." if 1935 < y < 1960 else ".")))
    else:
        esp_series.append(modern_point("ESP", y, "peseta"))
currency("esp", "Spanish peseta", "Spain", [1868, 2001], "peseta", [
    den("peseta", "Peseta", 1, symbol="Pta"), den("centimo", "Céntimo", 0.01),
    den("duro", "Duro", 5), den("real", "Real (colloquial)", 0.25),
], esp_series, "Replaced by the euro at 166.386 pesetas per euro.", successor="eur")

# ============================================================ ANTIQUITY
FLOUR_NOTE = ("Goods basis: ancient prices are matched to a modern price of ≈ $4 per kg of wheat-equivalent "
              "(between retail flour at ~$1.5/kg and bread at ~$6/kg).")


def ancient(y, usd, low, high, sources, method):
    return point(y, usd, "very low", sources, method, low=low, high=high, provenance="compiled")


DEN = [(-200, 35), (-150, 35), (-100, 35), (-50, 30), (1, 30), (50, 30), (100, 28), (150, 25), (200, 15), (250, 6),
       (275, 1.5), (301, 0.3)]
den_series = []
for y, v in DEN:
    srcs = [src("wp_denarius", "Denarius: ≈4.5 g silver (211 BC) → 3.9 g (Augustus) → heavily debased in the 3rd century; "
                               "1 denarius = 4 sestertii = 16 asses."),
            src("usda_ers", FLOUR_NOTE)]
    if y <= 150:
        srcs.append(src("scheidel", f"{y}: wheat at Rome/Italy typically ~3-4 sestertii per modius (6.5 kg) — about ⅘-1 denarius — "
                                    f"so 1 denarius ≈ 7-8 kg of wheat → ≈ ${v} on the goods basis."))
        srcs.append(src("matthew", "A labourer's daily wage of one denarius (1st century) — on a wage basis a denarius ≈ a modern day's "
                                   "unskilled pay, $100-130, the upper bound."))
        srcs.append(src("bls_wage", "Upper bound uses a modern US unskilled day's pay (~$15-16/hour × 8)."))
    elif y < 301:
        srcs.append(src("scheidel", f"{y}: Egyptian papyri show wheat prices rising several-fold during the 3rd-century debasement; "
                                    f"value scaled down accordingly to ≈ ${v}."))
    else:
        srcs.append(src("wp_edict", "Diocletian's Edict (301 AD): wheat 100 denarii per modius castrensis (~10 kg), unskilled labourer "
                                    "25 denarii/day + food — the denarius had become a small unit of account; ≈ $0.3-0.4 on the goods basis."))
    hi = 130 if y <= 150 else v * 4
    den_series.append(ancient(y, v, v / 2.5, hi, srcs, "commodity (wheat) price equivalence; wage basis as upper bound"))
currency("denarius", "Roman denarius", "Roman Republic and Empire", [-211, 301], "denarius", [
    den("denarius", "Denarius", 1, aliases=["penny (in older Bible translations)", "denarii"]),
    den("aureus", "Aureus (gold)", 25),
    den("antoninianus", "Antoninianus", 2, valid=(215, 294), notes="Nominally 2 denarii; heavily debased."),
    den("quinarius", "Quinarius", 0.5),
    den("sestertius", "Sestertius", 0.25, symbol="HS", aliases=["sesterce", "HS"]),
    den("dupondius", "Dupondius", 0.125),
    den("as", "As", periods=[(-211, -141, 0.1), (-140, 301, 1 / 16)], notes="10 to the denarius until c.141 BC, then 16."),
    den("semis", "Semis", periods=[(-211, -141, 0.05), (-140, 301, 1 / 32)]),
    den("quadrans", "Quadrans", periods=[(-211, -141, 0.025), (-140, 301, 1 / 64)], aliases=["farthing (KJV)"]),
], den_series, "Very approximate. Goods-based value is shown; the range's top is the wage-based value (one denarius ≈ a day's pay). "
               "Large Roman sums are usually quoted in sestertii (HS).", successor="solidus")

sol_series = []
for y in years(325, 1050, 25):
    srcs = [src("wp_solidus", "Constantine's solidus: 1/72 Roman pound of gold (≈4.5 g), kept at full weight and fineness until the 1040s."),
            src("scheidel", "Late-antique Egypt: ≈ 10-12 artabas (300-360 kg) of wheat per solidus in normal years; an unskilled "
                            "worker earned ≈ 8-12 solidi/year."),
            src("usda_ers", FLOUR_NOTE + " 300 kg × ~$3.5 ≈ $1,000."),
            src("bls_wage", "Wage basis: ~1/10 of a modern unskilled annual wage (~$32,000) ≈ $3,000, the upper bound.")]
    sol_series.append(ancient(y, 1000, 400, 3000, srcs, "commodity (wheat) price equivalence; wage basis as upper bound"))
currency("solidus", "Solidus / nomisma (Late Roman & Byzantine)", "Late Roman Empire, Byzantium", [309, 1092], "solidus", [
    den("solidus", "Solidus / nomisma / bezant", 1, aliases=["nomisma", "bezant", "besant"]),
    den("semissis", "Semissis", 0.5), den("tremissis", "Tremissis", 1 / 3),
    den("miliaresion", "Miliaresion (silver)", 1 / 12),
    den("siliqua", "Siliqua / keration", 1 / 24),
    den("follis", "Follis (bronze)", 1 / 288, valid=(498, 1092), notes="Rate varied; ≈ 288 per solidus in the 6th century."),
    den("litra", "Pound of gold (litra)", 72),
    den("kentenarion", "Kentenarion", 7200, notes="100 pounds of gold."),
], sol_series, "Remarkably stable for 700 years ('the dollar of the Middle Ages'). Replaced by the hyperpyron in 1092 after debasement.")

DR = [(-450, 60), (-400, 50), (-350, 35), (-300, 28)]
dr_series = []
for y, v in DR:
    srcs = [src("wp_greek", "Attic drachma ≈ 4.3 g silver; 6 obols = 1 drachma, 100 drachmae = 1 mina, 6,000 = 1 talent."),
            src("loomis", f"{y}: wheat ≈ {'3' if y >= -400 else '5-6'} drachmae per medimnos (≈40 kg); skilled day wage ≈ 1 drachma "
                          "(Erechtheion accounts, 409-407 BC), rising to 2-2½ in the 4th century."),
            src("usda_ers", FLOUR_NOTE + f" → ≈ ${v} per drachma."),
            src("bls_wage", "Upper bound: a drachma as a skilled day's pay, ≈ $150-250 today.")]
    dr_series.append(ancient(y, v, v / 2.5, 200, srcs, "commodity (wheat) price equivalence; wage basis as upper bound"))
currency("drachma_att", "Athenian drachma", "Classical Athens / Greek world", [-510, -50], "drachma", [
    den("drachma", "Drachma", 1, aliases=["drachm"]),
    den("obol", "Obol", 1 / 6), den("hemiobol", "Hemiobol", 1 / 12), den("chalkous", "Chalkous", 1 / 48),
    den("didrachm", "Didrachm / stater", 2), den("tetradrachm", "Tetradrachm ('owl')", 4),
    den("mina", "Mina", 100), den("talent", "Talent", 6000),
], dr_series, "A trireme rower or juror earned 3 obols-1 drachma a day. A talent was a fortune (≈ 16 years of skilled wages).")

shk_series = [
    ancient(-1750, 400, 150, 3000, [
        src("wp_shekel", "Mesopotamian shekel ≈ 8.3 g of silver; 60 shekels = 1 mina."),
        src("hammurabi", "Laws §273: a hired labourer earned 6 grains (še) of silver per day; 180 grains = 1 shekel → ≈ 30 days' wages. "
                         "Standard grain price ≈ 1 gur (~300 L, ~190 kg) of barley per shekel."),
        src("scheidel", "Old Babylonian wages and barley prices; 190 kg barley at ~$2/kg ≈ $400 (goods basis)."),
        src("bls_wage", "Wage basis: 30 unskilled days ≈ $3,000, the upper bound.")],
        "commodity (barley) price equivalence; wage basis as upper bound"),
    ancient(30, 120, 50, 500, [
        src("wp_shekel", "The Tyrian shekel (≈14 g silver) was the Temple coin of 1st-century Judea; 1 shekel = 4 drachmae/denarii."),
        src("matthew", "Daily wage of one denarius → a shekel ≈ 4 days' wages (upper bound ≈ $500)."),
        src("scheidel", "Goods basis follows the Roman denarius (≈ $30) × 4 ≈ $120.")],
        "derived from the Roman denarius (1 shekel = 4 denarii)"),
]
currency("shekel", "Shekel (ancient Near East / biblical)", "Mesopotamia, Israel/Judea, Phoenicia", [-2500, 70], "shekel", [
    den("shekel", "Shekel", 1, aliases=["sheqel", "Tyrian shekel"]),
    den("gerah", "Gerah", 1 / 20), den("beka", "Beka (half-shekel)", 0.5),
    den("mina", "Mina / maneh", periods=[(-2500, -1000, 60), (-999, 70, 50)], notes="60 shekels in Mesopotamia; 50 in the Hebrew Bible (Ezekiel 45:12 varies)."),
    den("talent", "Talent / kikkar", 3000, notes="3,000 shekels in Hebrew usage (3,600 in Mesopotamia)."),
    den("drachma", "Drachma (1st c.)", 0.25), den("denarius", "Denarius (1st c.)", 0.25),
    den("thirty_pieces", "Thirty pieces of silver", 30, notes="Matthew 26:15 — usually taken as 30 Tyrian shekels."),
], shk_series, "The shekel was a weight of silver long before it was a coin; values are only indicative.")

# ============================================================ FICTIONAL
# Fictional currencies carry no year-based series. Where the work gives enough to estimate a real-world value
# (prices or wages), a single undated estimate is stored as a one-point series; otherwise the series is empty.
def fictional_point(year, usd, low, high, sources, method):
    return point(year, usd, "very low", sources, method, low=low, high=high, provenance="compiled")


dnd_series = [fictional_point(2014, 250, 100, 600, [
    src("srd51", "1 gp = 10 sp = 100 cp; 'a silver piece buys a laborer's work for half a day, a flask of lamp oil, or a night's "
                 "rest in a poor inn'; 'a single copper piece buys a candle, a torch, or a piece of chalk'; a skilled artisan "
                 "earns 1 gp a day."),
    src("usda_ers", "Goods basis: a candle or torch (1 cp) ≈ $1-2 and a cheap night's lodging (1 sp) ≈ $20-40 today put 1 gp at "
                    "≈ $100-400."),
    src("bls_wage", "Wage basis: an unskilled day (2 sp) ≈ $120 → 1 gp ≈ $600; a skilled artisan's day (1 gp) ≈ $250. "
                    "Central estimate $250, range $100 (goods) to $600 (unskilled wages).")],
    "in-world prices and wages → modern equivalents")]
currency("dnd", "Dungeons & Dragons coinage", "Dungeons & Dragons (5th edition rules)", [1974, None], "gold piece", [
    den("gp", "Gold piece", 1, symbol="gp", aliases=["gold", "gold coin"]),
    den("pp", "Platinum piece", 10, symbol="pp", aliases=["platinum"]),
    den("ep", "Electrum piece", 0.5, symbol="ep", aliases=["electrum"]),
    den("sp", "Silver piece", 0.1, symbol="sp", aliases=["silver"]),
    den("cp", "Copper piece", 0.01, symbol="cp", aliases=["copper"]),
], dnd_series, "Rates from the 5th-edition SRD (earlier editions differ: e.g. 1st edition had 20 sp to the gp). "
               "The dollar value is a rough estimate from in-world prices and wages, not an official figure.",
         work="Dungeons & Dragons (TSR / Wizards of the Coast, 1974–)")

currency("westeros", "Westerosi coinage", "Westeros (A Song of Ice and Fire / Game of Thrones)", [1996, None], "gold dragon", [
    den("dragon", "Gold dragon", 1, aliases=["dragon", "golden dragon"]),
    den("moon", "Silver moon", 1 / 30, aliases=["moon"], notes="Only in the roleplaying game, not the novels."),
    den("stag", "Silver stag", 1 / 210, aliases=["stag"]),
    den("star", "Copper star", 1 / 1470, aliases=["star"]),
    den("half_groat", "Half-groat", 1 / 5880),
    den("groat", "Groat", 1 / 2940),
    den("penny", "Copper penny", 1 / 11760, aliases=["penny", "pennies"]),
    den("halfpenny", "Halfpenny", 1 / 23520),
], [], "Rates are not given in George R. R. Martin's novels; they come from the licensed roleplaying game and are "
       "semi-canon (the game's authors call them a rule of thumb). No real-world value is established.",
         work="A Song of Ice and Fire (George R. R. Martin, 1996–)")

currency("sw_credit", "Galactic credit (with Hutt coinage)", "Star Wars galaxy", [1977, None], "credit", [
    den("credit", "Credit", 1, aliases=["Galactic credit", "Republic credit", "Imperial credit", "Republic dataries", "cred"]),
    den("wupiupi", "Wupiupi", 0.625, notes="Small Hutt coin used on Tatooine (Legends)."),
    den("trugut", "Trugut", 10, notes="16 wupiupi (Legends)."),
    den("peggat", "Peggat", 40, notes="4 truguts, 64 wupiupi (Legends). Watto deals in Hutt money in The Phantom Menace."),
], [], "Hutt-coin rates are from Legends-era sources (the Expanded Universe), not the current canon. No real-world value is established.",
         work="Star Wars (Lucasfilm, 1977–)")

currency("latinum", "Gold-pressed latinum", "Star Trek (Ferengi Alliance and beyond)", [1993, None], "bar", [
    den("bar", "Bar", 1, aliases=["bar of latinum"]),
    den("strip", "Strip", 1 / 20, aliases=["strip of latinum"]),
    den("slip", "Slip", 1 / 2000, aliases=["slip of latinum"]),
], [], "Liquid latinum suspended in worthless gold, since gold can be replicated. 100 slips = 1 strip, 20 strips = 1 bar "
       "(Deep Space Nine). Bricks are larger than bars, but the bar-to-brick rate has never been stated. The Federation itself "
       "is said to have no money. No real-world value is established.",
         work="Star Trek (Paramount, Deep Space Nine 1993–1999)")

currency("ankh_morpork", "Ankh-Morpork dollar", "Discworld (Terry Pratchett)", [1983, None], "dollar", [
    den("dollar", "Dollar", 1, symbol="$AM", aliases=["AM$", "Ankh-Morpork dollar"]),
    den("guinea", "Guinea", 21 / 20, notes="21 shillings; 'falling from use'."),
    den("crown", "Crown", 0.25), den("half_crown", "Half-crown", 0.125),
    den("shilling", "Shilling", 1 / 20), den("sixpence", "Sixpence", 1 / 40),
    den("groat", "Groat", 1 / 60, notes="4 pence — the Assassins' fee for killing Foul Ole Ron."),
    den("thruppence", "Thruppeny bit", 1 / 80), den("penny", "Penny", 1 / 240, aliases=["pence"]),
    den("halfpenny", "Halfpenny", 1 / 480), den("farthing", "Farthing", 1 / 960),
    den("mite", "Mite", 1 / 1920, notes="Costs sixpence to make, 'on account of being so small and having the hole in the middle' (Making Money)."),
    den("elim", "Elim", 1 / 3840, notes="Costs a shilling to make (Making Money)."),
], [fictional_point(2004, 100, 50, 170, [
    src("lspace_currency", "Going Postal: a senior government official earns $20 a week; Guards! Guards!: five extra dollars a month "
                           "is a respectable raise. The dollar is 20 shillings of 12 pence."),
    src("bls_wage", "Wage basis: a senior official's modern weekly pay of roughly $2,000-3,300 ÷ $20 → ≈ $100-165 per dollar; "
                    "a 'respectable raise' of $5/month vs a modern raise of a few hundred dollars suggests ≈ $50-60. "
                    "Central estimate $100.")],
    "in-world wages → modern equivalents")],
    "The L-Space wiki gives the £sd-style system used here; some fan sources treat the dollar as 100 pence, and the books "
    "are not fully consistent. The famously debased dollar is 'theoretically gold' but contains less gold than sea water.",
         work="Discworld (Terry Pratchett, 1983–2015)")

currency("triganic_pu", "Triganic Pu", "The Hitchhiker's Guide to the Galaxy", [1978, None], "Pu", [
    den("pu", "Pu", 1, aliases=["Triganic Pu"]),
    den("ningi", "Ningi", 1 / 8, notes="A triangular rubber coin 6,800 miles along each side — so no one has ever collected enough to own one Pu."),
], [], "Eight Ningis to one Pu. The Guide adds that Ningis are not negotiable currency, because the Galactibanks refuse to "
       "deal in fiddling small change. No real-world value is established.",
         work="The Hitchhiker's Guide to the Galaxy (Douglas Adams, 1978–)")

# per-source citations for fictional currencies without a value series
FICTION_SOURCES = {
    "westeros": ["awoiaf_coin"], "sw_credit": ["sw_wupiupi", "sw_trugut", "sw_peggat"],
    "latinum": ["st_latinum", "sto_latinum"], "triganic_pu": ["hhgg_book", "hhgg_quote"],
    "dnd": ["srd51"], "ankh_morpork": ["lspace_currency"],
}
for c in CURRENCIES:
    if c.get("fictional"):
        c["sources"] = [{"title": SRC[k][0], "url": SRC[k][1],
                         "reasoning": "Source for the denominations and their exchange rates."} for k in FICTION_SOURCES[c["id"]]]

# ============================================================ assemble
cur_ids = {c["id"] for c in CURRENCIES}
for c in CURRENCIES:
    c["series"].sort(key=lambda p: p["year"])
    assert not c.get("successor") or c["successor"] in cur_ids, c["id"]

doc = {
    "schemaVersion": 1,
    "title": "Historical currency values in 2025 US dollars",
    "baseYear": BASE_YEAR,
    "unit": "USD2025",
    "generated": "2026-10-08",
    "methodology": {
        "summary": ("Each value answers: 'how many 2025 US dollars buy the same basket of consumer goods that one base unit of this "
                    "currency bought in that year?' (a CPI / 'real price' comparison)."),
        "steps": [
            "Express the currency in a contemporary anchor money: pounds sterling for years up to 1910 (via metal content, legal "
            "parity, or exchange rate), US dollars for years from 1915 (via exchange rate).",
            "Carry the anchor amount to 2025 with a consumer price index: UK — Bank of England millennium dataset (1209-2016) spliced "
            "to ONS CPI D7BT (2017-2025); US — Minneapolis Fed CPI (1800-2025).",
            f"Convert 2025 pounds to dollars at the 2025 annual average (${GBP_USD_2025}/£, Federal Reserve G.5A).",
            "Before 1717 gold coins are valued through English silver coinage using an estimated gold:silver ratio; from 1717 through "
            "the British gold standard (£1 = 7.3224 g fine gold) and market gold:silver ratios.",
            "Antiquity and Edo-period Japan have no price index: values are commodity-price equivalences (wheat, barley, rice), with "
            "the wage-based equivalent given as the upper end of the range.",
        ],
        "caveats": [
            "CPI comparisons understate how 'big' a sum felt: before c.1900 a day's wage bought far fewer goods, so a wage- or "
            "income-share comparison can be 3-10× higher than the CPI value. Use the 'high' end of the range for social context.",
            "The sterling-route and dollar-route for the same moment can differ by tens of percent because US and UK prices "
            "moved differently (purchasing-power-parity gaps).",
            "Exchange rates in wartime, under exchange controls, or for inconvertible currencies are official rates and may "
            "not reflect what the money could actually buy.",
            "'low' and 'high' are judgement-based bands (high ±10%, medium ×/÷1.35, low ×/÷2, very low ×/÷3 or explicit "
            "goods-vs-wage bounds), not statistical confidence intervals.",
        ],
        "provenance": {
            "computed": "Calculated directly from downloaded datasets (BoE, ONS, Minneapolis Fed, Fed G.5A) plus a metal content or parity.",
            "compiled": "Uses an exchange rate, parity, or estimate entered by hand from the cited reference; verify against the source before relying on it.",
        },
        "interpolation": "Between data points, interpolate linearly in log(usd2025). Do not extrapolate beyond a currency's first or last point.",
        "fictional": ("Currencies with 'fictional': true come from novels, films and games ('work' names the source). Their "
                      "'series' is empty when no real-world value can be justified, or holds a single undated estimate "
                      "(stored at the year of the cited work) derived from in-world prices and wages. 'sources' at the "
                      "currency level cite the exchange rates between denominations."),
        "denominations": ("Each denomination's 'value' is in base units of its currency. When 'periods' is present, use the period "
                          "containing the year (inclusive bounds). Years are astronomical-ish integers; negative = BCE."),
    },
    "currencies": CURRENCIES,
}
json.dump(doc, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n = sum(len(c["series"]) for c in CURRENCIES)
print(f"{len(CURRENCIES)} currencies, {n} data points")

# ------------------------------------------------------------ slim copy
# Only what lookups and conversions need: no sources, reasoning, methods or notes. Same shape, fields omitted.
SLIM_CURRENCY = ["id", "name", "region", "era", "baseUnit", "aliases", "denominations", "series", "successor", "fictional", "work"]
SLIM_DENOMINATION = ["id", "name", "symbol", "value", "periods", "validFrom", "validTo", "aliases"]
SLIM_POINT = ["year", "usd2025", "low", "high", "confidence"]


def pick(d, keys):
    return {k: d[k] for k in keys if k in d}


slim = {k: doc[k] for k in ("schemaVersion", "title", "baseYear", "unit", "generated")}
slim["slim"] = True
slim["currencies"] = [
    {**pick(c, SLIM_CURRENCY),
     "denominations": [pick(d, SLIM_DENOMINATION) for d in c["denominations"]],
     "series": [pick(p, SLIM_POINT) for p in c["series"]]}
    for c in CURRENCIES]
slim_path = out_path[:-5] + ".slim.json" if out_path.endswith(".json") else out_path + ".slim"
json.dump(slim, open(slim_path, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"slim copy: {slim_path}")
