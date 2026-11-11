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
# foreign currency per US dollar, by year (see scripts/extract_series.py for each dataset)
per_usd = lambda key: {c: {int(y): v for y, v in ys.items()} for c, ys in S[key].items()}
MW_PER_USD, FRED_PER_USD = per_usd("mw_per_usd"), per_usd("fred_per_usd")
JST_PER_USD, PWT_PER_USD = per_usd("jst_per_usd"), per_usd("pwt_per_usd")
GSR = {int(k): v for k, v in S["gold_silver_ratio"].items()}  # ounces of silver per ounce of gold, 1687-
FRED_IDS = {"CAD": "AEXCAUS", "MXN": "AEXMXUS", "GBP": "AEXUSUK", "EUR": "AEXUSEU", "JPY": "AEXJPUS",
            "CNY": "AEXCHUS", "INR": "AEXINUS", "CHF": "AEXSZUS", "SEK": "AEXSDUS"}

BASE_YEAR = 2025
GBP_USD_2025 = round(1 / FRED_PER_USD["GBP"][BASE_YEAR], 4)
EURO_FIXED = {"FRF": 6.55957, "DEM": 1.95583, "ITL": 1936.27, "ESP": 166.386, "NLG": 2.20371}
EURO_FIXED_QUOTE = {"FRF": ("wp_franc", "ERM_fixed_rate = 6.55957 F"), "DEM": ("wp_dm", "ERM_fixed_rate = DM 1.95583"),
                    "ITL": ("wp_lira", "The conversion rate was Lit 1,936.27 to the euro"),
                    "ESP": ("wp_peseta", "ERM_fixed_rate = Pts 166.386"), "NLG": ("wp_guilder", "ERM_fixed_rate = ƒ2.20371")}

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
    "jst": ("Òscar Jordà, Moritz Schularick & Alan M. Taylor, Macrohistory Database, release 6 — 'xrusd' (local currency per US dollar)",
            "https://www.macrohistory.net/database/"),
    "pwt": ("Robert C. Feenstra, Robert Inklaar & Marcel P. Timmer, Penn World Table 10.01 — 'xr' (national currency per US dollar)",
            "https://www.rug.nl/ggdc/productivity/pwt/"),
    "mw_fx": ("Lawrence H. Officer, 'Exchange Rates Between the United States Dollar and Forty-one "
              "Currencies', MeasuringWorth", "https://www.measuringworth.com/datasets/exchangeglobal/"),
    "mw_gsr": ("Lawrence H. Officer & Samuel H. Williamson, 'The Price of Gold, 1257-Present', MeasuringWorth — "
               "gold/silver price ratio (1687-)", "https://www.measuringworth.com/datasets/gold/"),
    "ratio_pre1687": ("Estimated gold:silver value ratio before 1687 (no dataset; background in Wikipedia, 'Bimetallism')",
                      WP + "Bimetallism"),
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
    "wp_livre": ("Wikipedia, 'Livre tournois' — 80.88 g silver (1262), 4.50516 g (1726)", WP + "Livre_tournois"),
    "wp_ecu": ("Wikipedia, 'Écu' and 'Louis d'or' — official valuations in livres", WP + "Louis_d%27or"),
    "spooner": ("Frank C. Spooner, 'The International Economy and Monetary Movements in France, 1493-1725' "
                "(Harvard Economic Studies 138, 1972) — livre tournois silver equivalents (library record)", "https://buscador.unsam.edu.ar/Record/23851"),
    "wp_franc": ("Wikipedia, 'French franc' — germinal franc 4.5 g silver; 1928 Poincaré franc; 1960 new franc", WP + "French_franc"),
    "wp_lmu": ("Wikipedia, 'Latin Monetary Union' — the LMU franc of 4.5 g silver or 0.290322 g gold", WP + "Latin_Monetary_Union"),
    "wp_thaler": ("Wikipedia, 'Prussian thaler' — Graumann 14-thaler standard (16.704 g fine silver)", WP + "Prussian_thaler"),
    "wp_vthaler": ("Wikipedia, 'Vereinsthaler' — introduced 1857", WP + "Vereinsthaler"),
    "wp_goldmark": ("Wikipedia, 'German mark (1871)' — 2790 marks per kg of gold; 20.43 marks per £", WP + "German_mark_(1871)"),
    "wp_papiermark": ("Wikipedia, 'Papiermark' — wartime and 1919-1923 depreciation", WP + "Papiermark"),
    "wp_reichsmark": ("Wikipedia, 'Reichsmark' — 4.20 RM per US dollar parity", WP + "Reichsmark"),
    "wp_dm": ("Wikipedia, 'Deutsche Mark'", WP + "Deutsche_Mark"),
    "wp_augulden": ("Wikipedia, 'Austro-Hungarian gulden' — Conventionsfuß (11.69 g) and 1857 (11.11 g) standards", WP + "Austro-Hungarian_gulden"),
    "wp_krone": ("Wikipedia, 'Austro-Hungarian krone' — 3280 kronen per kg of gold (1892)", WP + "Austro-Hungarian_krone"),
    "wp_florin": ("Wikipedia, 'Florin' — 3.54 g of nominally pure gold, 1252-1533", WP + "Florin"),
    "wp_ducat": ("Wikipedia, 'Ducat' — Venetian ducat, 3.545 g of 99.47% fine gold, from 1284", WP + "Ducat"),
    "spufford": ("Peter Spufford, 'Handbook of Medieval Exchange' (Royal Historical Society, 1986) — "
                 "Florentine and Venetian money-of-account rates (library record)", "https://ci.nii.ac.jp/ncid/BA00272230?l=en"),
    "wp_guilder": ("Wikipedia, 'Dutch guilder' — silver content by period (table 'Value of gulden, grams'); 1875 gold standard", WP + "Dutch_guilder"),
    "wp_ruble": ("Wikipedia, 'Russian ruble' — 1704 decimal ruble; 1897 gold ruble of 0.77424 g", WP + "Russian_ruble"),
    "wp_assign": ("Wikipedia, 'Russian assignation ruble' — discount of paper to silver, 1769-1843", WP + "Russian_assignation_ruble"),
    "wp_ryo": ("Wikipedia, 'Ryō' and 'Koban (coin)' — gold content of successive koban issues", WP + "Ry%C5%8D"),
    "boj_ryo": ("Bank of Japan Institute for Monetary and Economic Studies, Currency Museum FAQ "
                "'江戸時代の1両は今のいくら？' (How much was one ryō worth in today's money?)",
                "https://www.imes.boj.or.jp/cm/history/historyfaq/answer.html"),
    "wp_yen": ("Wikipedia, 'Japanese yen' — 1871 yen (24.26 g silver), 1897 gold yen (0.75 g), 360/$ (1949-71)", WP + "Japanese_yen"),
    "wp_tael": ("Wikipedia, 'Liang (mass)' — the tael (liang) of 37.301 g", WP + "Liang_(mass)"),
    "wp_cash": ("Wikipedia, 'Cash (Chinese coin)' — strings of 1000 cash; market cash/silver rates", WP + "Cash_(Chinese_coin)"),
    "wp_rmb": ("Wikipedia, 'Renminbi'", WP + "Renminbi"),
    "wp_rupee": ("Wikipedia, 'Indian rupee' — silver rupee exchange rate in pence, 1850-1900", WP + "Indian_rupee"),
    "wp_icc": ("Wikipedia, 'Indian Currency Committee' — 15 rupees per sovereign (1s 4d per rupee) from 1899", WP + "Indian_Currency_Committee"),
    "wp_rupee_hist": ("Wikipedia, 'History of the rupee' — Mughal rupiya ~178 grains", WP + "History_of_the_rupee"),
    "wp_akce": ("Wikipedia, 'Akçe' — silver content 1450-1800 (after Malanima 2009); 120 akçe = 1 kuruş", WP + "Ak%C3%A7e"),
    "pamuk": ("Şevket Pamuk, 'A Monetary History of the Ottoman Empire' (Cambridge UP, 2000)", "https://doi.org/10.1017/CBO9780511497452"),
    "wp_kurus": ("Wikipedia, 'Kuruş' — 100 kuruş to the gold lira of 1844", WP + "Kuru%C5%9F"),
    "wp_ottoman_lira": ("Wikipedia, 'Ottoman lira' — LT 1 = 6.61519 g pure gold (1844-1881 bimetallic, then gold)", WP + "Ottoman_lira"),
    "wp_moidore": ("Wikipedia, 'Moidore' — 4,800 réis (1688-1800); single moidore ≈ 13s 5½d, double ≈ 27s in England", WP + "Moidore"),
    "wp_real_pt": ("Wikipedia, 'Portuguese real' — gold peça of 13.145 g revalued 1826, 1837, 1854; 1854 milréis = 1.62585 g gold", WP + "Portuguese_real"),
    "wp_lira": ("Wikipedia, 'Italian lira' — LMU parity, 1927 'quota 90', 625/$ (1949-71)", WP + "Italian_lira"),
    "wp_peseta": ("Wikipedia, 'Spanish peseta'", WP + "Spanish_peseta"),
    "wp_chf": ("Wikipedia, 'Swiss franc'", WP + "Swiss_franc"),
    "wp_sek": ("Wikipedia, 'Swedish krona' — Scandinavian Monetary Union: krona = 1/2480 kg of gold", WP + "Swedish_krona"),
    "wp_euro": ("Wikipedia, 'Euro' — irrevocable conversion rates of 1999", WP + "Euro"),
    "wp_cad": ("Wikipedia, 'Canadian dollar' — gold sovereign legal tender at £1 = $4.86⅔", WP + "Canadian_dollar"),
    "wp_mxn": ("Wikipedia, 'Mexican peso' — 1863 silver peso (24.44 g fine), 1905 gold reform, 1993 new peso", WP + "Mexican_peso"),
    "wp_usd": ("Wikipedia, 'United States dollar' — Coinage Act of 1792; dollar based on Spanish dollar", WP + "United_States_dollar"),
    "wp_bretton": ("Wikipedia, 'Bretton Woods system' — fixed parities 1945-1971", WP + "Bretton_Woods_system"),
    "wp_denarius": ("Wikipedia, 'Denarius' and 'Roman currency' — denominations and debasement", WP + "Roman_currency"),
    "wp_edict": ("Wikipedia, 'Edict on Maximum Prices' (301 AD) — wheat 100 denarii per modius castrensis", WP + "Edict_on_Maximum_Prices"),
    "scheidel": ("Walter Scheidel, 'Real wages in early economies: evidence for living standards from "
                 "1800 BCE to 1300 CE', Journal of the Economic and Social History of the Orient 53 (2010) 425-462",
                 "https://doi.org/10.1163/156852010X506038"),
    "matthew": ("Matthew 20:1-16 — a day's wage for a vineyard labourer is one denarius", "https://www.biblegateway.com/passage/?search=Matthew+20%3A1-16&version=NRSVUE"),
    "wp_solidus": ("Wikipedia, 'Solidus' — 1/72 Roman pound of gold (~4.5 g) from 309 AD", WP + "Solidus"),
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


for _code, _sid in FRED_IDS.items():
    SRC[f"fred_{_code.lower()}"] = (f"Federal Reserve Bank of St. Louis, FRED series {_sid} (annual averages from Federal Reserve "
                                    f"G.5A, {min(FRED_PER_USD[_code])}-)", f"https://fred.stlouisfed.org/series/{_sid}")


def src(key, reasoning, quote=None):
    """A citation. `quote` is text copied from the source that states the value used (checked when the source was read)."""
    title, url = SRC[key]
    s = {"title": title, "url": url, "reasoning": reasoning}
    if quote:
        s["quote"] = quote
    return s


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
    out.append(src("fred_gbp", f"{BASE_YEAR} annual average exchange rate ${GBP_USD_2025} per £1, used to express {BASE_YEAR} pounds in {BASE_YEAR} dollars."))
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
# grams of fine silver in one English penny (1d), by mint indenture. Only the 1601 standard is stated on the cited page;
# the earlier rows are not, so points that depend on them are labelled estimates.
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
    (1601, 0.464, "one troy ounce of sterling (.925) per 62 pence, 1601-1816"),
]
PENNY_QUOTE = {1601: "the silver content of British coinage was defined to be one troy ounce of sterling silver for 62 pence"}
# gold:silver value ratio before MeasuringWorth's series begins (1687); an estimate
RATIO_PRE1687 = [(1200, 10.0), (1300, 11.0), (1350, 11.5), (1400, 11.0), (1500, 10.75),
                 (1550, 11.3), (1600, 12.25), (1650, 14.0), (1687, 15.0)]
GOLD_G_PER_GBP = 7.32238  # 1717-1914 (guinea of 21s / sovereign of 1817)
GOLD_STD_QUOTE = "the 20-shilling gold sovereign, or £1 coin, which contained 7.32238 g fine gold"


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


def gold_std_src(note=""):
    return src("wp_gold_std", f"Britain's gold standard: £1 = {GOLD_G_PER_GBP} g fine gold.{note}", GOLD_STD_QUOTE)


def gold_silver_ratio(y):
    """(ratio, source, from a dataset?)"""
    if y in GSR:
        return GSR[y], src("mw_gsr", f"Gold/silver price ratio in {y}: {GSR[y]}:1."), True
    r = interp(RATIO_PRE1687, y)
    return r, src("ratio_pre1687", f"Estimated gold:silver ratio in {y} ≈ {r:.2f}:1 (interpolated; the dataset starts in 1687)."), False


def silver_gbp_per_g(y):
    """(GBP per gram of fine silver in year y, [sources], whether every step is a dataset or a checked standard)."""
    if y < 1717:
        y0, g, note = step(PENNY_SILVER, y)
        return 1 / (g * 240), [src("wp_penny", f"In {y} the English penny contained {g} g fine silver ({note}), "
                                               f"so 1 g of silver = {1/g:.3f}d.", PENNY_QUOTE.get(y0))], y0 in PENNY_QUOTE
    r, rs, _ = gold_silver_ratio(y)
    per_g = 1 / GOLD_G_PER_GBP / r
    rs["reasoning"] += f" So 1 g of silver ≈ {per_g*240:.3f}d."
    return per_g, [gold_std_src(), rs], True


def gold_gbp_per_g(y):
    if y >= 1717:
        return 1 / GOLD_G_PER_GBP, [gold_std_src()], True
    s, why, ok = silver_gbp_per_g(y)
    r, rs, from_data = gold_silver_ratio(y)
    rs["reasoning"] += f" So 1 g gold ≈ {s*r*240:.1f}d."
    return s * r, why + [rs], ok and from_data


# ----------------------------------------------------------------- framework
BAND = {"high": 1.1, "medium": 1.35, "low": 2.0, "very low": 3.0}
# provenance: what the weakest number behind a point is
#   dataset  — exchange rates and price indexes all read from downloaded datasets
#   quoted   — also uses a parity, coin standard or rate quoted from the cited source (see each source's 'quote')
#   estimate — uses at least one number that is neither: an interpolation, a reconstruction or a judgement


def point(y, value, confidence, sources, method, low=None, high=None, provenance="dataset"):
    f = BAND[confidence]
    return {"year": y, "usd2025": sig(value), "low": sig(low if low is not None else value / f),
            "high": sig(high if high is not None else value * f), "confidence": confidence,
            "method": method, "provenance": provenance, "sources": sources}


def via_gbp(y, gbp, confidence, bridge_sources, method, provenance="dataset"):
    return point(y, gbp_to_usd2025(y, gbp), confidence, bridge_sources + uk_cpi_sources(y), method,
                 provenance=provenance)


def via_usd(y, usd, confidence, bridge_sources, method, provenance="dataset"):
    return point(y, usd_to_usd2025(y, usd), confidence, bridge_sources + us_cpi_sources(y), method,
                 provenance=provenance)


def metal_point(y, grams, metal, unit, confidence, coin_src, checked):
    """`checked`: whether the coin's metal content is quoted from its source (coin_src should then carry the quote)."""
    fn = silver_gbp_per_g if metal == "silver" else gold_gbp_per_g
    per_g, why, route_ok = fn(y)
    gbp = grams * per_g
    srcs = [coin_src(y, grams)] + why
    srcs[-1]["reasoning"] += f" Hence 1 {unit} ({grams:.4g} g fine {metal}) ≈ {lsd(gbp)} sterling."
    return via_gbp(y, gbp, confidence, srcs, f"{metal} content → sterling → UK CPI",
                   provenance="quoted" if checked and route_ok else "estimate")


def gold_parity_point(y, gold_g, unit, confidence, coin_src):
    """A unit defined in gold under the gold standard: its sterling value is its gold content ÷ the sovereign's."""
    gbp = gold_g / GOLD_G_PER_GBP
    return via_gbp(y, gbp, confidence, [coin_src, gold_std_src(f" Hence 1 {unit} ({gold_g:.6g} g) = £{gbp:.5g} ≈ {lsd(gbp)}; "
                                                               f"£1 = {1/gbp:.5g} {unit}s.")],
                   "gold parity → sterling → UK CPI", provenance="quoted")


def standard_gbp_point(y, gbp, unit, confidence, srcs):
    """A legal rate against sterling, quoted from its source."""
    srcs[-1]["reasoning"] += f" Hence 1 {unit} ≈ {lsd(gbp)} sterling in {y}."
    return via_gbp(y, gbp, confidence, srcs, "legal rate → sterling → UK CPI", provenance="quoted")


def estimate_gbp_point(y, gbp, unit, confidence, srcs):
    srcs[-1]["reasoning"] += f" Hence 1 {unit} ≈ {lsd(gbp)} sterling in {y}."
    return via_gbp(y, gbp, confidence, srcs, "estimated rate → sterling → UK CPI", provenance="estimate")


def conf_by_year(y, cuts):
    """cuts: [(min_year, confidence), ...] ascending."""
    c = cuts[0][1]
    for yy, cc in cuts:
        if y >= yy:
            c = cc
    return c


def years(a, b, stepn=5):
    return list(range(a, b + 1, stepn))


def has_fx(code, y):
    return any(y in t.get(code, {}) for t in (FRED_PER_USD, MW_PER_USD, JST_PER_USD, PWT_PER_USD))


def per_usd_rate(code, y):
    """(units per US dollar, source key, dataset name), preferring FRED, then MeasuringWorth, PWT, JST.
    JST comes last: for 1945-1960 it often gives free-market rather than official rates."""
    for table, key, name in ((FRED_PER_USD, f"fred_{code.lower()}", "FRED"), (MW_PER_USD, "mw_fx", "MeasuringWorth"),
                             (PWT_PER_USD, "pwt", "PWT"), (JST_PER_USD, "jst", "JST")):
        if y in table.get(code, {}):
            return table[code][y], key, name
    raise KeyError((code, y))


def fx_point(code, y, unit, confidence="high", note=""):
    """Point from a downloaded US-dollar exchange rate."""
    r, key, _ = per_usd_rate(code, y)
    s = src(key, f"{y} annual average: {r:,.5g} {unit}s per US dollar → ${1/r:.5g} per {unit}." + (f" {note}" if note else ""))
    return via_usd(y, 1 / r, confidence, [s], "exchange rate → US CPI")


def fx_gbp_point(code, y, unit, confidence="high", note=""):
    """Point for years up to 1910 (sterling anchor): the currency's and sterling's dollar rates from the same dataset, crossed."""
    for table, key in ((MW_PER_USD, "mw_fx"), (JST_PER_USD, "jst")):
        if y in table.get(code, {}) and y in table["GBP"]:
            r, g = table[code][y], table["GBP"][y]
            per_gbp = r / g
            s = src(key, f"{y}: {r:.5g} {unit}s and £{g:.5g} per US dollar, so £1 = {per_gbp:.4g} {unit}s"
                         f" and 1 {unit} ≈ {lsd(1 / per_gbp)}." + (f" {note}" if note else ""))
            return via_gbp(y, 1 / per_gbp, confidence, [s], "exchange rate → sterling → UK CPI")
    raise KeyError((code, y))


def usd_per_unit_modern(code, y):
    """USD per unit from FRED, euro conversion rates, or BoE M14 cross rates, with sources."""
    if code in FRED_PER_USD and y in FRED_PER_USD[code]:
        r = FRED_PER_USD[code][y]
        return 1 / r, src(f"fred_{code.lower()}", f"{y} annual average: {r:.5g} {code} per US dollar → ${1/r:.5g} per {code}.")
    if code in EURO_FIXED and y >= 1999:
        eur = 1 / FRED_PER_USD["EUR"][y]
        r = EURO_FIXED[code]
        k, q = EURO_FIXED_QUOTE[code]
        return eur / r, src("fred_eur", f"{y}: euro averaged ${eur:.4f}; with {code} fixed at {r} per euro "
                                         f"→ ${eur/r:.5g} per {code}."), src(k, f"{code} conversion rate: {r} per euro.", q)
    usd_gbp, x_gbp = M14["USD"][y], M14[code][y]
    v = usd_gbp / x_gbp
    return v, src("boe_m14", f"{y} annual averages: ${usd_gbp:.4f} per £ and {x_gbp:.5g} {code} per £ → "
                             f"cross rate ${v:.5g} per {code}.")


def modern_point(code, y, unit, confidence="high", extra=None):
    v, *srcs = usd_per_unit_modern(code, y)
    return via_usd(y, v, confidence, srcs + (extra or []), "exchange rate → US CPI",
                   provenance="quoted" if len(srcs) > 1 else "dataset")


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
               (1550, 4.5), (1560, 5.0), (1575, 6.0), (1585, 8.0), (1595, 10.0), (1603, 12.0), (1707, 12.0)]
scots_series = []
for y in years(1370, 1705):
    if y >= 1603:
        scots_series.append(standard_gbp_point(y, 1 / 12, "pound Scots", "high", [src(
            "wp_scots", "From the Union of the Crowns, £12 Scots = £1 sterling.",
            "From 1603, the exchange rate was fixed at £12 Scots to £1 sterling.")]))
    elif y == 1560:
        scots_series.append(standard_gbp_point(y, 1 / 5, "pound Scots", "medium", [src(
            "wp_scots", "£5 Scots = £1 sterling in 1560.", "By 1560, the exchange relationship had reached £5 Scots to £1 sterling.")]))
    else:
        r = interp(SCOTS_RATIO, y)
        scots_series.append(estimate_gbp_point(y, 1 / r, "pound Scots", "low", [
            src("wp_scots", "The pound Scots fell against sterling from the later 14th century; the cited page gives only the 1560 "
                            "(5:1) and 1603 (12:1) rates."),
            src("gemmill", f"Estimate: ≈ £{r:.2g} Scots per £1 sterling in {y}, interpolated between assumed ratios.")]))
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

irish_series = [standard_gbp_point(y, 12 / 13, "Irish pound", "high", [src(
    "wp_irish", "An English shilling passed for 13 Irish pence, so £13 Irish = £12 sterling.",
    "In 1701, a proclamation stated one English shilling was equal to 1s. 1d. in Irish")])
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

# ============================================================ CANADA
# context for years when the market or official rate is a weaker guide to purchasing power
CAD_NOTES = {1920: ("medium", "Canada had suspended gold convertibility in 1914; the dollar was at a post-war discount."),
             1945: ("medium", "Wartime exchange controls; MeasuringWorth has no figures for 1942-45, so this is the JST rate."),
             1940: ("medium", "Wartime exchange controls fixed an official rate of 1.10 per $, well below this average, so the year is uncertain.")}
cad_series = []
for y in years(1860, 2025):
    if y <= 1910:
        cad_series.append(standard_gbp_point(y, 1 / (4.86 + 2 / 300), "Canadian dollar", "high", [src(
            "wp_cad", "The sovereign was legal tender at £1 = $4.86⅔ Canadian.",
            "the British gold sovereign continued to remain legal tender at the rate of £1 = Can$4.86⅔")]))
    elif has_fx("CAD", y):
        c, n = CAD_NOTES.get(y, ("high", ""))
        cad_series.append(fx_point("CAD", y, "Canadian dollar", c, n))
currency("cad", "Canadian dollar", "Canada", [1858, None], "Canadian dollar", [
    den("dollar", "Dollar", 1, symbol="$", aliases=["C$", "CA$", "buck", "loonie"],
        notes="'Loonie' after the $1 coin of 1987, which shows a loon."),
    den("toonie", "Toonie", 2, valid=(1996, 2100), aliases=["twonie"], notes="$2 coin from 1996."),
    den("half_dollar", "Fifty-cent piece", 0.5),
    den("quarter", "Quarter", 0.25),
    den("dime", "Dime", 0.1),
    den("nickel", "Nickel", 0.05),
    den("cent", "Cent", 0.01, symbol="¢", valid=(1858, 2013), aliases=["penny"],
        notes="Minting ended in 2012; cash sums are rounded to the nearest 5¢ since 2013."),
], cad_series, "Before 1858 the Province of Canada kept accounts in 'Halifax currency' pounds (£1 = $4 Canadian), "
               "which are not modelled here. Newfoundland had its own dollar until 1949.",
         aliases=["CAD", "loonie"])

# ============================================================ MEXICO
MXP_SILVER_G = 24.44  # silver peso: 27.07 g at .903 fine, the old 8-real standard
MXP_GOLD_G = 0.75     # 1905 monetary reform: peso = 75 cg fine gold (= 50 US cents)
MXP_NOTES = {1985: ("medium", "Debt crisis: Mexico ran several official rates alongside the market rate.")}


def mxp_src(y, g):
    return src("wp_mxn", f"The Mexican silver peso contained {g} g fine silver, the old 8-real standard.",
               "The post-independence silver peso contained 27.07 grams of 90.3% fine silver (24.44 g fine)")


mxp_series = []
for y in years(1865, 1990) + [1921]:  # 1921 is MeasuringWorth's first year for Mexico
    if y <= 1900:
        mxp_series.append(metal_point(y, MXP_SILVER_G, "silver", "peso", "medium", mxp_src, True))
    elif y <= 1910:
        mxp_series.append(gold_parity_point(y, MXP_GOLD_G, "peso", "high", src(
            "wp_mxn", f"The 1905 reform put the peso on gold at {MXP_GOLD_G} g fine gold.",
            "In 1905 the peso was solely defined as 0.75 g fine gold.")))
    elif y in MW_PER_USD["MXP"]:
        c, n = MXP_NOTES.get(y, ("high", ""))
        mxp_series.append(fx_point("MXP", y, "peso", c, n))
currency("mxp", "Mexican peso (1863-1992)", "Mexico", [1863, 1992], "peso", [
    den("peso", "Peso", 1, symbol="$", aliases=["Mex$", "peso fuerte", "Mexican dollar"],
        notes="The silver peso circulated widely in East Asia and the Americas as the 'Mexican dollar'."),
    den("centavo", "Centavo", 0.01, symbol="¢"),
    den("real", "Real (colloquial)", 0.125, valid=(1863, 1910), notes="Old 1/8 peso, still used in speech after decimalisation."),
    den("toston", "Tostón", 0.5, notes="50 centavos."),
    den("hidalgo", "Hidalgo (gold)", 10, valid=(1905, 1931), notes="Gold 10-peso coin."),
    den("centenario", "Centenario (gold)", 50, valid=(1921, 1947), notes="Gold 50-peso coin (37.5 g fine gold); later a bullion coin."),
], mxp_series, "1865-1900 values via the silver content; 1905-1910 via the gold peso; 1920+ via exchange rates and US CPI. "
               "Revolution-era paper money (1913-1916) is not modelled. Before 1863 see the Spanish dollar. "
               "Replaced in 1993 by the new peso at 1,000 to 1.", successor="mxn",
         aliases=["old Mexican peso", "MXP"])

mxn_series = [fx_point("MXN", y, "peso") for y in [1993] + years(1995, 2025)]
currency("mxn", "Mexican peso", "Mexico", [1993, None], "peso", [
    den("peso", "Peso", 1, symbol="$", aliases=["Mex$", "MX$", "nuevo peso", "N$"],
        notes="Called the 'nuevo peso' in 1993-1995; 1 new peso = 1,000 old pesos."),
    den("centavo", "Centavo", 0.01, symbol="¢"),
    den("old_peso", "Old peso (1863-1992)", 0.001, notes="The 1993 redenomination: 1,000 old pesos = 1 new peso."),
], mxn_series, "", aliases=["MXN"])

# ============================================================ SPANISH DOLLAR
SPD_SILVER = [(1497, 25.561, "1497 standard, 0.9306 fine", "0.9306 fine (25.561 g fine silver"),
              (1728, 24.809, "1728 standard, 0.9167 fine", "0.9167 fine (24.809 g fine silver"),
              (1772, 24.443, "1772 standard, 0.9028 fine (actual fineness 1772-1821 may have been lower)",
               "0.9028 fine (24.443 g fine silver")]


def spd_src(y, g):
    _, _, note, quote = step(SPD_SILVER, y)
    return src("wp_spdollar", f"The 8-real piece in {y} contained {g} g fine silver ({note}).", quote)


spd_series = []
for y in years(1575, 1850):
    g = step(SPD_SILVER, y)[1]
    p = metal_point(y, g, "silver", "Spanish dollar", "medium", spd_src, True)
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
LIVRE_SILVER = [(1270, 80.88), (1290, 75), (1300, 40), (1310, 55), (1330, 50), (1340, 30), (1350, 22), (1360, 18),
                (1370, 25), (1400, 22), (1420, 12), (1430, 20), (1450, 24), (1475, 22), (1500, 21), (1525, 18),
                (1550, 17), (1575, 14), (1600, 11.7), (1625, 9.8), (1641, 8.4), (1675, 8.3), (1690, 7.5),
                (1700, 7.0), (1710, 5.6), (1715, 5.6), (1720, 3.0), (1726, 4.50516), (1795, 4.50516)]
LIVRE_QUOTE = {1270: "established the livre tournois as 20 sous tournois, or 80.88 grams of fine silver",
               1726: "in 1726, in a devaluation under Louis XV, as 4.50516 grams of fine silver"}


def livre_quote(y):
    return LIVRE_QUOTE[1270] if y == 1270 else LIVRE_QUOTE[1726] if y >= 1726 else None


def livre_src(y, g):
    q = livre_quote(y)
    return src("wp_livre" if q else "spooner",
               f"The livre tournois in {y} represented {g:.6g} g fine silver." if q else
               f"Estimate: the livre tournois in {y} represented about {g:.3g} g fine silver, interpolated between assumed values "
               "(medieval values fluctuated sharply with royal mutations).", q)


livre_series = [metal_point(y, interp(LIVRE_SILVER, y), "silver", "livre", "medium" if y >= 1550 else "low", livre_src,
                            livre_quote(y) is not None)
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

frf_series = []
for y in years(1800, 1955):
    if y < 1870:
        frf_series.append(metal_point(y, 4.5, "silver", "franc", "high",
                                      lambda y, g: src("wp_franc", "The germinal franc contained 4.5 g fine silver.",
                                                       "worth 4.5 g silver or 9/31 g = 0.29032 g gold (ratio 15.5)"), True))
    elif y <= 1910:
        frf_series.append(gold_parity_point(y, 0.290322, "franc", "high", src(
            "wp_lmu", "Under the Latin Monetary Union the franc was 0.290322 g fine gold.", "One LMU franc represented 4.5 g of fine silver or 0.290322 g of fine gold.")))
    elif y <= 1940:
        frf_series.append(fx_point("FRF", y, "franc", "low" if y == 1940 else "medium",
                                   "Occupation from June 1940; later rates were administered." if y == 1940 else ""))
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
                             lambda y, g: src("wp_thaler", "Graumann standard of 1750: 14 thalers per Cologne mark of fine silver.",
                                              "with 14 thalers issued to a Cologne Mark of fine silver, or 16.704 g per thaler"), True)
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

mark_series = []
for y in years(1875, 1920):
    if y <= 1910:
        mark_series.append(gold_parity_point(y, 1 / 2.79, "mark", "high", src(
            "wp_goldmark", "The mark was defined as 1/2790 kg of fine gold.", "with 2790 marks equal to 1 kilogram of pure gold")))
    else:
        mark_series.append(fx_point("MARK", y, "mark", "low" if y == 1920 else "medium",
                                    "Paper marks; the rate swung widely during the year." if y == 1920 else
                                    "Wartime paper mark (gold convertibility suspended)."))
currency("mark", "German mark (Goldmark / Papiermark)", "German Empire", [1873, 1923], "mark", [
    den("mark", "Mark", 1, symbol="M", aliases=["Goldmark", "Papiermark", "Reichsmark (loosely)"]),
    den("pfennig", "Pfennig", 0.01),
    den("thaler", "Thaler (coin, still current to 1907)", 3),
    den("krone", "Krone (gold 10 marks)", 10),
    den("doppelkrone", "Doppelkrone (gold 20 marks)", 20),
], mark_series, "Hyperinflation: by November 1923 a US dollar cost 4.2 trillion marks; the Rentenmark replaced it at 1 per "
                "1,000,000,000,000 marks. Years 1921-1924 are deliberately omitted.", successor="reichsmark")

RM_NOTES = {1935: ("medium", "Under exchange controls."), 1940: ("low", "Inconvertible under exchange controls.")}
rm_series = [fx_point("RM", y, "Reichsmark", *RM_NOTES.get(y, ("high", ""))) for y in years(1925, 1940)]
currency("reichsmark", "Reichsmark", "Germany", [1924, 1948], "Reichsmark", [
    den("rm", "Reichsmark", 1, symbol="RM", aliases=["Rentenmark"]), den("rpf", "Reichspfennig", 0.01),
], rm_series, "1945 omitted: no meaningful exchange rate (occupation rate 10 RM/$; black-market cigarette economy).",
         successor="dem")

dem_series = []
for y in years(1950, 2000):
    if y < 1965:
        dem_series.append(fx_point("DEM", y, "Deutsche Mark"))
    else:
        dem_series.append(modern_point("DEM", y, "Deutsche Mark"))
currency("dem", "Deutsche Mark", "West Germany / Germany", [1948, 2001], "Deutsche Mark", [
    den("dm", "Deutsche Mark", 1, symbol="DM", aliases=["D-Mark", "Mark"]), den("pf", "Pfennig", 0.01),
    den("groschen", "Groschen (colloquial)", 0.1), den("heiermann", "Heiermann (slang)", 5),
], dem_series, "Replaced by the euro at 1.95583 DM per euro.", successor="eur")

# ============================================================ AUSTRIA
AUG_SILVER = [(1760, 11.6928, "Conventionsfuß of 1753: 1/20 Cologne mark of silver",
               "equivalent to 1/20 of a Cologne mark of silver, or 11.6928 g"),
              (1858, 11.111, "Austrian standard of 1857",
               "1857: Vereinsthaler = 1.5 Fl. | 9.524 g || silver | 11.111 g || silver")]
aug_series = [metal_point(y, step(AUG_SILVER, y)[1], "silver", "gulden", "medium",
                          lambda y, g: src("wp_augulden", f"{step(AUG_SILVER, y)[2]}: {g} g fine silver. Paper gulden often traded "
                                                          "at a discount to silver (severely c.1800-1816 and 1848-1878).", step(AUG_SILVER, y)[3]), True)
              for y in years(1760, 1890)]
currency("aut_gulden", "Austrian gulden (florin)", "Habsburg monarchy", [1754, 1892], "gulden", [
    den("gulden", "Gulden / florin", 1, symbol="fl.", aliases=["florin", "fl."]),
    den("kreuzer", "Kreuzer", periods=[(1754, 1857, 1 / 60), (1858, 1892, 1 / 100)], aliases=["kr."]),
    den("conventionsthaler", "Conventionsthaler / Maria Theresa thaler", 2),
    den("ducat", "Ducat (Austrian gold)", 4.5, notes="Approximate; market rate varied."),
    den("krone", "Krone (1892 conversion)", 0.5),
], aug_series, "Valued at the silver standard; paper money traded below silver in war periods, so these are upper values for those years.",
         successor="aut_krone")
krone_series = [gold_parity_point(y, 1 / 3.28, "krone", "high", src(
    "wp_krone", "The krone was defined as 1/3280 kg of fine gold.", "1 kg gold = 3280 Kr.")) for y in years(1895, 1910)]
currency("aut_krone", "Austro-Hungarian krone", "Austria-Hungary", [1892, 1918], "krone", [
    den("krone", "Krone / korona", 1, symbol="K"), den("heller", "Heller / fillér", 0.01), den("gulden", "Gulden (old)", 2),
], krone_series, "Lost most of its value during and after WWI; post-1914 values not modelled.")

# ============================================================ ITALY
FLORENCE_LIRA = [(1252, 1252, 1.0), (1253, 1299, 2.0), (1300, 1349, 3.0), (1350, 1399, 3.5), (1400, 1449, 4.0),
                 (1450, 1474, 4.8), (1475, 1499, 5.8), (1500, 1533, 7.0)]
florin_series = [metal_point(y, 54 * 0.06479891, "gold", "florin", "low" if y < 1400 else "medium",
                             lambda y, g: src("wp_florin", f"The florin held 54 grains ({g:.4g} g) of nominally pure gold, unchanged 1252-1533.",
                                              "It had 54 grains"), True)
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
ducat_series = [metal_point(y, 3.545 * 0.9947, "gold", "ducat", "low" if y < 1400 else "medium",
                            lambda y, g: src("wp_ducat", f"The Venetian ducat (zecchino) held 3.545 g of 99.47% gold ({g:.4g} g fine).",
                                             "The Venetian ducat contained 3.545 grams of 99.47% fine gold"), True)
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

lira_series = []
for y in years(1865, 2000):
    if y == 1865:
        lira_series.append(gold_parity_point(y, 0.290322, "lira", "high", src(
            "wp_lmu", "Italy joined the Latin Monetary Union in 1865: 1 lira = 1 franc = 0.290322 g fine gold.", "One LMU franc represented 4.5 g of fine silver or 0.290322 g of fine gold.")))
    elif y <= 1910:
        lira_series.append(fx_gbp_point("ITL", y, "lira", "medium",
                                        "Paper lira inconvertible from 1866 (corso forzoso), so it traded below gold parity in some years."))
    elif y == 1945:
        continue  # no dataset has an official 1945 rate (MeasuringWorth starts again in 1946)
    elif y < 1965:
        lira_series.append(fx_point("ITL", y, "lira", "low" if y == 1940 else "high" if y >= 1950 else "medium"))
    else:
        lira_series.append(modern_point("ITL", y, "lira"))
currency("itl", "Italian lira", "Italy", [1861, 2001], "lira", [
    den("lira", "Lira", 1, symbol="L."), den("centesimo", "Centesimo", 0.01),
    den("soldo", "Soldo (colloquial)", 0.05), den("scudo", "Scudo (5 lire silver)", 5),
], lira_series, "Replaced by the euro at 1936.27 lire per euro. 1945 omitted (no reliable official rate). Pre-unification "
                "Italian states had their own lire, scudi and ducats.",
         successor="eur")

# ============================================================ NETHERLANDS
# (from year, g fine silver, quote from the cited table or text; None = not stated there)
NLG_SILVER = [(1600, 10.4, None), (1618, 10.16, "| 1618 || 10.16"), (1659, 9.67, "| 1659–1800 || 9.67"),
              (1801, 9.67, None), (1817, 9.613, "redefined the Gulden as either 9.613 g silver or 0.60561 g gold"),
              (1840, 9.45, "in 1840 by reducing the gulden to 9.45 g fine silver")]
nlg_series = []
for y in years(1600, 2000):
    if y <= 1870:
        _, g, q = step(NLG_SILVER, y)
        nlg_series.append(metal_point(y, g, "silver", "guilder", "medium",
                                      lambda y, g, q=q: src("wp_guilder", f"Guilder of {y}: {g:.4g} g fine silver." if q else
                                                            f"Estimate: guilder of {y} ≈ {g:.4g} g fine silver (no standard stated "
                                                            "for these years on the cited page).", q), q is not None))
    elif y <= 1910:
        nlg_series.append(gold_parity_point(y, 0.6048, "guilder", "high", src(
            "wp_guilder", "Gold standard from 1875: 1 guilder = 0.6048 g fine gold.", "| 1875 || 0.6048 g gold")))
    elif y < 2000:
        if has_fx("NLG", y):
            nlg_series.append(fx_point("NLG", y, "guilder", "medium" if y in (1940, 1945) else "high"))
    else:
        nlg_series.append(modern_point("NLG", y, "guilder"))
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
        reis = 6.4 if y < 1826 else 7.5 if y < 1837 else 8.0
        milreis_series.append(metal_point(y, 13.145 / reis, "gold", "milréis", "medium",
                                          lambda y, g, reis=reis: src("wp_real_pt", f"The gold peça of 13.145 g fine gold passed for "
                                                                      f"{reis * 1000:,.0f} réis in {y}, so 1 milréis = {g:.4g} g gold.",
                                                                      "peça of 13.145 g fine gold was raised in value from 6$400 to 7$500 "
                                                                      "in 1826, 8$000 in 1837, and 8$085 in 1854"), True))
    else:
        milreis_series.append(gold_parity_point(y, 1.62585, "milréis", "high", src(
            "wp_real_pt", "Gold standard of 1854: 1 milréis = 1.62585 g fine gold.",
            "In 1854, Portugal adopted a gold standard with the milréis equal to 1.62585 g")))
currency("pte_real", "Portuguese real / milréis", "Portugal, Brazil (colonial)", [1500, 1911], "milréis (1,000 réis)", [
    den("milreis", "Milréis (1,000 réis)", 1, symbol="1$000", aliases=["mil réis"]),
    den("real", "Real (pl. réis)", 0.001, aliases=["rei", "réis"]),
    den("vintem", "Vintém", 0.02, notes="20 réis."),
    den("tostao", "Tostão", 0.1, notes="100 réis."),
    den("cruzado", "Cruzado", 0.4, notes="400 réis (later 480)."),
    den("moidore", "Moidore (moeda d'ouro)", 4.8, aliases=["moeda"],
        notes="Gold 4,800 réis (1688-1800), ≈ 13s 5½d in England; the coin usually called a 'moidore' there was the double, ≈ 27s."),
    den("johannes", "Johannes / joe / peça", 6.4, aliases=["joe", "half-joe (3.2)"], notes="Gold 6,400 réis; ≈ 36s sterling."),
    den("conto", "Conto (de réis)", 1000, notes="1,000,000 réis."),
], milreis_series, "The moidore and johannes were widely used in British America and the Caribbean. "
                   "Post-1891 depreciation and the 1911 escudo (= 1,000 réis) not modelled.")

# ============================================================ RUSSIA
RUB_SILVER = [(1705, 24.0), (1718, 20.7), (1763, 20.7), (1764, 18.0), (1840, 18.0)]
RUB_PENCE = {1845: 38.0, 1850: 38.0, 1855: 37.0, 1860: 37.0, 1865: 30.0, 1870: 30.0, 1875: 31.0, 1880: 25.0,
             1885: 24.0, 1890: 27.0, 1895: 25.4}
rub_series = []
for y in years(1705, 1915):
    if y <= 1840:
        rub_series.append(metal_point(y, interp(RUB_SILVER, y), "silver", "silver ruble", "medium",
                                      lambda y, g: src("wp_ruble", f"Estimate: silver ruble of {y} ≈ {g:.3g} g fine silver (these "
                                                                   "standards are not stated on the cited page)."), False))
    elif y < 1900:
        p = RUB_PENCE[y]
        rub_series.append(estimate_gbp_point(y, p / 240, "ruble", "medium", [src(
            "wp_ruble", f"Estimate: credit ruble ≈ {p}d sterling in {y} (paper inconvertible 1858-1897; this rate is not stated "
                        "on the cited page).")]))
    elif y <= 1910:
        rub_series.append(gold_parity_point(y, 0.77424, "ruble", "high", src(
            "wp_ruble", "Witte's 1897 gold ruble: 0.77424 g fine gold.", "(17.424 dolya or 0.77424 g fine gold)")))
    else:
        rub_series.append(via_usd(y, 0.33, "low", [src("wp_ruble", "Estimate: ≈ 3 rubles per $ in 1915 (gold parity ≈ 1.94) as "
                                                                   "wartime inflation began; no dataset covers this year.")],
                                  "estimated rate → US CPI", provenance="estimate"))
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
    usd = yen * JP_CPI_FACTOR / FRED_PER_USD["JPY"][2025]
    ryo_series.append(point(y, usd, "very low", [
        src("boj_ryo", f"Rice-price basis: the Bank of Japan Currency Museum puts one ryō at ≈ ¥100,000 in early Edo, ¥40,000-60,000 in "
                       f"mid-to-late Edo and ¥4,000-10,000 in the bakumatsu inflation; interpolated ≈ ¥{yen:,.0f} for {y}, "
                       f"×{JP_CPI_FACTOR} for Japanese inflation to 2025."),
        src("wp_ryo", "Koban gold content fell from ≈15 g (Keichō 1601) to ≈1.9 g (Man'en 1860), the main driver of the declining value."),
        src("fred_jpy", f"Converted at the 2025 average of {FRED_PER_USD['JPY'][2025]} yen per dollar."),
        src("boj_ryo", f"Wage basis (a carpenter's pay) gives ¥300,000-400,000 per ryō, used as the upper bound.")],
        "commodity (rice) price equivalence → 2025 yen → USD", low=usd / 3,
        high=max(usd * 3, 350000 * JP_CPI_FACTOR / FRED_PER_USD["JPY"][2025]) if y < 1860 else usd * 6, provenance="estimate"))
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

jpy_series = []
for y in years(1870, 2025):
    if y <= 1895:
        jpy_series.append(metal_point(y, 24.26, "silver", "yen", "medium",
                                      lambda y, g: src("wp_yen", "The 1871 yen was 24.26 g of silver; Japan was de facto on silver until 1897.",
                                                       "with the yen defined as 1.5 g of gold, or 24.26 g of silver"), True))
    elif y <= 1910:
        jpy_series.append(gold_parity_point(y, 0.75, "yen", "high", src(
            "wp_yen", "Gold exchange standard from 1897: 1 yen = 0.75 g fine gold.", "defining the yen as 0.75g fine gold")))
    elif y == 1945:
        continue
    elif y < 1965:
        jpy_series.append(fx_point("JPY", y, "yen", "high" if y >= 1950 else "medium"))
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
                                       lambda y, g: src("wp_tael", "Estimate: the tael weighed about 37.3 g; silver taels are taken as ≈ 36 g "
                                                                   "fine silver after typical sycee fineness, which the page does not state."), False))
    else:
        v = TAEL_USD[y]
        tael_series.append(via_usd(y, v, "medium", [src("wp_tael", f"Estimate: Haikwan tael ≈ ${v} in {y} (it followed world silver "
                                                                   "prices); no dataset covers it.")],
                                   "estimated rate → US CPI", provenance="estimate"))
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

cny_series = []
for y in years(1955, 2025):
    cny_series.append(fx_point("CNY", y, "yuan", "low" if y < 1980 else "medium" if y < 1995 else "high",
                               "Official rate of a non-convertible currency." if y < 1995 else ""))
currency("cny", "Renminbi (yuan)", "People's Republic of China", [1949, None], "yuan", [
    den("yuan", "Yuan", 1, symbol="¥", aliases=["renminbi", "RMB", "kuai", "元"]),
    den("jiao", "Jiao", 0.1, aliases=["mao"]), den("fen", "Fen", 0.01),
], cny_series, "1955 redenomination: 1 new yuan = 10,000 old. Pre-1980 official rates overstate what foreigners could do with the money.")

# ============================================================ INDIA
INR_SILVER = [(1600, 11.0), (1835, 11.0), (1836, 10.69)]
# pence per rupee, from the table 'Indian silver rupee value (1820-1900)' on the cited page
INR_PENCE = {1850: 24.3, 1855: 24.2, 1860: 26.0, 1865: 23.8, 1870: 22.5, 1875: 21.6, 1880: 19.9, 1885: 18.2,
             1890: 18.0, 1895: 13.6}
inr_series = []
for y in years(1600, 2025):
    if y < 1850:
        inr_series.append(metal_point(y, interp(INR_SILVER, y), "silver", "rupee", "medium",
                                      lambda y, g: src("wp_rupee_hist",
                                                       f"Estimate: rupee of {y} ≈ {g:.4g} g fine silver. The page gives the rupiya's weight "
                                                       "(178 grains, 11.53 g) but not its fineness or later standards.", "weighing 178 grains"),
                                      False))
    elif y in INR_PENCE:
        d = INR_PENCE[y]
        inr_series.append(standard_gbp_point(y, d / 240, "rupee", "high", [src(
            "wp_rupee", f"Exchange rate in {y}: {d}d per rupee.", f"| {y}||{d}||")]))
    elif y <= 1915:
        icc = src("wp_icc", "Gold-exchange standard from 1899: 15 rupees per sovereign.",
                  "the official exchange rate of the rupee be established at 15 rupees per British sovereign, or 1 shilling and 4 pence per rupee")
        if y <= 1910:
            inr_series.append(standard_gbp_point(y, 1 / 15, "rupee", "high", [icc]))
        else:  # from 1915 values go through the dollar; MeasuringWorth's rupee series starts in 1916
            usd = USD_PER_GBP[y] / 15
            inr_series.append(via_usd(y, usd, "medium", [icc, src("boe_fx", f"{y}: ${USD_PER_GBP[y]:.4f} per £ → ${usd:.4g} per rupee.")],
                                      "legal rate → US CPI", provenance="quoted"))
    else:
        inr_series.append(fx_point("INR", y, "rupee", "high" if y >= 1950 else "medium"))
currency("inr", "Indian rupee", "Mughal India, British India, Republic of India", [1540, None], "rupee", [
    den("rupee", "Rupee / rupiya", 1, symbol="Rs", aliases=["rupiya", "₹"]),
    den("anna", "Anna", 1 / 16, valid=(1600, 1957)),
    den("pice", "Pice / paisa (old)", 1 / 64, valid=(1600, 1957)),
    den("pie", "Pie", 1 / 192, valid=(1835, 1957)),
    den("naya_paisa", "Naya paisa / paisa", 0.01, valid=(1957, 2100)),
    den("mohur", "Mohur (gold)", 15, notes="Gold coin, nominally 15 rupees (market 14-17)."),
    den("pagoda", "Star pagoda (Madras)", 3.5, valid=(1600, 1818), notes="South Indian gold coin ≈ 3½ rupees."),
    den("lakh", "Lakh", 100000), den("crore", "Crore", 10000000),
], inr_series, "Before 1850 values via an estimated silver content; 1850-1895 from the rupee's sterling exchange rate, which "
                "halved between 1873 and 1894 as silver fell.")

# ============================================================ OTTOMAN
AKCE_SILVER = [(1330, 1.15), (1400, 1.0), (1455, 0.85), (1495, 0.68), (1580, 0.6), (1590, 0.38), (1600, 0.29),
               (1650, 0.25), (1685, 0.15)]
akce_series = [metal_point(y, interp(AKCE_SILVER, y), "silver", "akçe", "low", checked=False, coin_src=
                           lambda y, g: src("wp_akce", f"Estimate: akçe of {y} ≈ {g:.3g} g silver (after the Malanima/Pamuk series, interpolated; "
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
                                        lambda y, g: src("pamuk", f"Estimate: kuruş of {y} ≈ {g:.3g} g fine silver (after Pamuk ch. 9-11, "
                                                                  "interpolated; repeated debasements especially under Mahmud II, 1808-39)."), False))
    else:
        kurus_series.append(gold_parity_point(y, 6.61519 / 100, "kuruş", "medium", src(
            "wp_ottoman_lira", "1844 reform: the gold lira of 6.61519 g = 100 kuruş.", "LT 1 = 6.61519 grams pure gold")))
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

chf_series = []
for y in years(1850, 2025):
    if y <= 1910:
        chf_series.append(gold_parity_point(y, 0.29032, "Swiss franc", "high", src(
            "wp_chf", "Introduced at par with the French franc: 0.29032 g fine gold.",
            "The Swiss franc was introduced at par with the French franc, at 4.5 g fine silver or 9/31 g = 0.29032 g fine gold")))
    elif y < 1965:
        chf_series.append(fx_point("CHF", y, "Swiss franc", "high" if y >= 1950 else "medium"))
    else:
        chf_series.append(modern_point("CHF", y, "Swiss franc"))
currency("chf", "Swiss franc", "Switzerland", [1850, None], "franc", [
    den("franc", "Franc / Franken", 1, symbol="Fr.", aliases=["Franken", "CHF"]),
    den("rappen", "Rappen / centime", 0.01), den("batzen", "Batzen (colloquial 10 Rp.)", 0.1),
], chf_series, "")

sek_series = []
for y in years(1875, 2025):
    if y <= 1910:
        sek_series.append(gold_parity_point(y, 1 / 2.48, "krona", "high", src(
            "wp_sek", "Scandinavian Monetary Union: 1 krona = 1/2480 kg fine gold.",
            "with the krona/krone defined as 1/2480 of a kilogram of pure gold")))
    elif y < 1965:
        sek_series.append(fx_point("SEK", y, "krona", "high" if y >= 1950 else "medium"))
    else:
        sek_series.append(modern_point("SEK", y, "krona"))
currency("sek", "Swedish krona", "Sweden (Danish and Norwegian kroner were at par until 1914)", [1873, None], "krona", [
    den("krona", "Krona", 1, symbol="kr", aliases=["krone (Danish/Norwegian, pre-1914)", "riksdaler riksmynt (1:1 in 1873)"]),
    den("ore", "Öre", 0.01),
], sek_series, "Before 1914 the Danish and Norwegian krone were interchangeable with the Swedish krona.")

esp_series = []
for y in years(1870, 2000):
    if y <= 1910:
        esp_series.append(fx_gbp_point("ESP", y, "peseta", "medium",
                                       "The peseta was nominally at Latin Monetary Union parity but inconvertible, so it traded below it."))
    elif y < 1975:
        esp_series.append(fx_point("ESP", y, "peseta", "low" if 1935 < y < 1960 else "medium",
                                   "Multiple official rates under Franco." if 1935 < y < 1960 else ""))
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
    return point(y, usd, "very low", sources, method, low=low, high=high, provenance="estimate")


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
    return point(year, usd, "very low", sources, method, low=low, high=high, provenance="estimate")


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
            "dataset": ("Every exchange rate and price index behind the value was read from a downloaded dataset (Bank of England, "
                        "ONS, Minneapolis Fed, FRED, MeasuringWorth, Jordà-Schularick-Taylor, Penn World Table)."),
            "quoted": ("Also uses a parity, coin standard or rate that is quoted from the cited source; the source's 'quote' "
                       "field holds the text."),
            "estimate": ("Uses at least one number that is neither downloaded nor quoted: an interpolation, a reconstruction "
                         "or a judgement (including all ancient, Edo-period and fictional values)."),
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
