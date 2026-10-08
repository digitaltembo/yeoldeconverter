"""Build data/units.json: historical and contemporary units of length, area, volume, mass and count.

Usage: python3 scripts/build_units.py data/units.json

Each unit is defined either directly in SI terms or as a multiple of another unit
(or as the square/cube of a length unit); SI values are resolved from those
definitions so derived units stay consistent with their parents.
Base units: length m, area m², volume L, mass kg, count each.
"""
import json, math, sys

out_path = sys.argv[1]
WP = "https://en.wikipedia.org/wiki/"
SRC = {
    "intl_yard": ("Wikipedia, 'International yard and pound' — 1959 agreement: 1 yd = 0.9144 m, 1 lb = 0.45359237 kg exactly",
                  WP + "International_yard_and_pound"),
    "nist811": ("NIST Special Publication 811, Appendix B.8 — factors for units listed alphabetically",
                "https://www.nist.gov/pml/special-publication-811/nist-guide-si-appendix-b-conversion-factors/nist-guide-si-appendix-b8"),
    "uk_wma": ("UK Weights and Measures Act 1985, Schedule 1 — definitions of imperial units",
               "https://www.legislation.gov.uk/ukpga/1985/72/schedule/1"),
    "wp_english": ("Wikipedia, 'English units' — medieval and early-modern English measures", WP + "English_units"),
    "wp_imperial": ("Wikipedia, 'Imperial units' — 1824 Weights and Measures Act system", WP + "Imperial_units"),
    "wp_uscust": ("Wikipedia, 'United States customary units'", WP + "United_States_customary_units"),
    "wp_survey": ("Wikipedia, 'Foot (unit)' — US survey foot = 1200/3937 m (retired 2022)", WP + "Foot_(unit)"),
    "wp_nmi": ("Wikipedia, 'Nautical mile' — 1852 m (international, 1929); Admiralty mile 6080 ft", WP + "Nautical_mile"),
    "wp_cable": ("Wikipedia, 'Cable length'", WP + "Cable_length"),
    "wp_league": ("Wikipedia, 'League (unit)'", WP + "League_(unit)"),
    "wp_typo": ("Wikipedia, 'Point (typography)' — DTP point = 1/72 inch", WP + "Point_(typography)"),
    "wp_ell": ("Wikipedia, 'Ell' — English ell of 45 inches; continental ells", WP + "Ell"),
    "wp_cubit": ("Wikipedia, 'Cubit' — Egyptian, Mesopotamian, biblical and English cubits", WP + "Cubit"),
    "wp_scots": ("Wikipedia, 'Scottish units' — Scots ell, fall, mile, acre, pint, boll, pounds", WP + "Scottish_units"),
    "wp_irish": ("Wikipedia, 'Irish measure' — Irish perch of 7 yards; Irish mile and acre", WP + "Irish_measure"),
    "wp_roman": ("Wikipedia, 'Ancient Roman units of measurement'", WP + "Ancient_Roman_units_of_measurement"),
    "wp_greek": ("Wikipedia, 'Ancient Greek units of measurement'", WP + "Ancient_Greek_units_of_measurement"),
    "wp_parasang": ("Wikipedia, 'Parasang' — Persian unit, ≈ 30 stadia (≈ 5-6 km)", WP + "Parasang"),
    "wp_egypt": ("Wikipedia, 'Ancient Egyptian units of measurement' — royal cubit ≈ 523-529 mm", WP + "Ancient_Egyptian_units_of_measurement"),
    "wp_meso": ("Wikipedia, 'Ancient Mesopotamian units of measurement'", WP + "Ancient_Mesopotamian_units_of_measurement"),
    "wp_bible": ("Wikipedia, 'Biblical and Talmudic units of measurement'", WP + "Biblical_and_Talmudic_units_of_measurement"),
    "wp_france": ("Wikipedia, 'Traditional French units of measurement' — pied du roi 324.84 mm, "
                  "livre 489.5 g, Paris pinte, boisseau", WP + "Traditional_French_units_of_measurement"),
    "wp_lieue": ("Wikipedia, 'League (unit)' — lieue de poste (2000 toises), lieue commune (1/25 degree)", WP + "League_(unit)"),
    "wp_arpent": ("Wikipedia, 'Arpent' — Paris arpent ≈ 3419 m², length ≈ 58.47 m", WP + "Arpent"),
    "wp_german": ("Wikipedia, 'German units of measurement' — Prussian, Austrian, Bavarian units", WP + "German_units_of_measurement"),
    "wp_morgen": ("Wikipedia, 'Morgen' — Prussian ≈ 0.2553 ha; Dutch/Rhineland ≈ 0.8516 ha", WP + "Morgen"),
    "wp_klafter": ("Wikipedia, 'Klafter' — Viennese Klafter 1.8965 m", WP + "Klafter"),
    "wp_joch": ("Wikipedia, 'German units of measurement' — Austrian Joch 5754.64 m²", WP + "German_units_of_measurement"),
    "wp_russia": ("Wikipedia, 'Historical Russian units of measurement' — 1835 definitions tied to the English foot and pound",
                  WP + "Historical_Russian_units_of_measurement"),
    "wp_spain": ("Wikipedia, 'Spanish units of measurement' — vara de Burgos 835.9 mm, libra 460 g, fanega", WP + "Spanish_units_of_measurement"),
    "wp_portugal": ("Wikipedia, 'Portuguese units of measurement' — arrátel ≈ 459 g, arroba = 32 arráteis", WP + "Portuguese_units_of_measurement"),
    "wp_japan": ("Wikipedia, 'Japanese units of measurement' — shaku = 10/33 m, koku ≈ 180.39 L, kan = 3.75 kg", WP + "Japanese_units_of_measurement"),
    "wp_china": ("Wikipedia, 'Chinese units of measurement' — Qing and modern (shì) definitions", WP + "Chinese_units_of_measurement"),
    "wp_catty": ("Wikipedia, 'Jin (mass)' (catty) — Hong Kong legal catty 604.79 g; modern jin 500 g", WP + "Jin_(mass)"),
    "wp_india": ("Wikipedia, 'Indian units of measurement' — tola, seer, maund, gaz, kos", WP + "Indian_units_of_measurement"),
    "wp_maund": ("Wikipedia, 'Maund' — Indian government maund 37.324 kg (1833); Bengal factory maund", WP + "Maund"),
    "wp_tola": ("Wikipedia, 'Tola (unit)' — 180 grains troy = 11.6638 g", WP + "Tola_(unit)"),
    "wp_bigha": ("Wikipedia, 'Bigha' — varies by region, 1/3 acre (Bengal) to ~2/3 acre", WP + "Bigha"),
    "wp_ottoman": ("Wikipedia, 'Ottoman units of measurement' — okka 1.2829 kg, arşın, dönüm, kile", WP + "Ottoman_units_of_measurement"),
    "wp_dunam": ("Wikipedia, 'Dunam' — Ottoman dönüm ≈ 919 m²; metric dunam 1000 m²", WP + "Dunam"),
    "wp_acre": ("Wikipedia, 'Acre' — 4840 sq yd; Scottish and Irish acres", WP + "Acre"),
    "wp_hide": ("Wikipedia, 'Hide (unit)' — nominally 120 acres, often 40-120 in practice", WP + "Hide_(unit)"),
    "wp_virgate": ("Wikipedia, 'Virgate' — a quarter hide, typically 30 acres", WP + "Virgate"),
    "wp_oxgang": ("Wikipedia, 'Oxgang' — ⅛ carucate, typically 15 acres (10-20)", WP + "Oxgang"),
    "wp_carucate": ("Wikipedia, 'Carucate' — Danelaw equivalent of the hide, ~120 acres", WP + "Carucate"),
    "wp_section": ("Wikipedia, 'Section (United States land surveying)' — 1 sq mi; township = 36 sections",
                   WP + "Section_(United_States_land_surveying)"),
    "wp_desyatina": ("Wikipedia, 'Desiatina' — 2400 square sazhens ≈ 1.0925 ha", WP + "Desiatina"),
    "wp_gallon": ("Wikipedia, 'Gallon' — wine (231 in³), ale (282 in³), imperial (4.54609 L) gallons", WP + "Gallon"),
    "wp_casks": ("Wikipedia, 'English wine cask units' — tun, pipe/butt, puncheon, hogshead, tierce, barrel, rundlet",
                 WP + "English_wine_cask_units"),
    "wp_beer": ("Wikipedia, 'Barrel (unit)' — beer/ale barrel, kilderkin, firkin, pin; 42 US gal oil barrel", WP + "Barrel_(unit)"),
    "wp_bushel": ("Wikipedia, 'Bushel' — Winchester bushel 2150.42 in³; imperial bushel 8 imp gal", WP + "Bushel"),
    "wp_chaldron": ("Wikipedia, 'Chaldron' — 36 bushels (London coal)", WP + "Chaldron"),
    "wp_avdp": ("Wikipedia, 'Avoirdupois'", WP + "Avoirdupois"),
    "wp_troy": ("Wikipedia, 'Troy weight' — troy pound 5760 grains; Tower pound 5400 grains", WP + "Troy_weight"),
    "wp_apoth": ("Wikipedia, 'Apothecaries' system'", WP + "Apothecaries%27_system"),
    "wp_wool": ("Wikipedia, 'English units' (wool weights) — clove 7 lb, tod 28 lb, sack 364 lb", WP + "English_units#Weight"),
    "wp_carat": ("Wikipedia, 'Carat (mass)' — metric carat 200 mg (1907)", WP + "Carat_(mass)"),
    "wp_cologne": ("Wikipedia, 'Mark (unit)' — Cologne mark ≈ 233.856 g", WP + "Mark_(unit)"),
    "wp_dozen": ("Wikipedia, 'Dozen', 'Gross (unit)' and 'Long hundred'", WP + "Dozen"),
    "wp_gross": ("Wikipedia, 'Gross (unit)'", WP + "Gross_(unit)"),
    "wp_longhundred": ("Wikipedia, 'Long hundred' — 120", WP + "Long_hundred"),
    "wp_ream": ("Wikipedia, 'Ream' and 'Quire (paper)' — 480/500 sheets; 24/25 sheets", WP + "Ream"),
    "wp_shekel": ("Wikipedia, 'Shekel' — ≈ 11 g (Hebrew) vs ≈ 8.3 g (Mesopotamian)", WP + "Shekel"),
    "si": ("BIPM, 'The International System of Units (SI)' brochure", "https://www.bipm.org/en/publications/si-brochure"),
}

UNITS = []


def U(id_, name, cat, system, region, era, defn, srcs, aliases=None, notes=None, low=None, high=None, sub=None):
    UNITS.append(dict(id=id_, name=name, category=cat, subcategory=sub, system=system, region=region, era=era,
                      defn=defn, srcs=srcs, aliases=aliases or [], notes=notes, low=low, high=high))


L, A, V, M, C = "length", "area", "volume", "mass", "count"
EN = "English / Imperial / US customary"
NOW = None

# ================================================================ LENGTH
U("metre", "Metre", L, "Metric (SI)", "International", [1799, NOW], ("si", 1), ["si"], aliases=["meter", "m"])
U("kilometre", "Kilometre", L, "Metric (SI)", "International", [1799, NOW], (1000, "metre"), ["si"], aliases=["km"])
U("inch", "Inch", L, EN, "Britain, US, Commonwealth", [1100, NOW], ("si", 0.0254), ["intl_yard", "nist811"], aliases=["in", '"'],
  notes="Exactly 25.4 mm since 1959; pre-1959 British and US inches differed by ~2 parts per million.")
U("foot", "Foot", L, EN, "Britain, US", [1100, NOW], (12, "inch"), ["intl_yard", "uk_wma"], aliases=["ft", "'", "feet"])
U("yard", "Yard", L, EN, "Britain, US", [1100, NOW], (3, "foot"), ["intl_yard", "uk_wma"], aliases=["yd"])
U("mile", "Mile (statute)", L, EN, "Britain, US", [1593, NOW], (1760, "yard"), ["uk_wma", "wp_english"], aliases=["mi", "statute mile"],
  notes="Fixed at 8 furlongs (5280 ft) by statute in 1593.")
U("furlong", "Furlong", L, EN, "Britain, US", [900, NOW], (220, "yard"), ["wp_english"], notes="'Furrow long'; ⅛ mile, 10 chains.")
U("chain", "Chain (Gunter's)", L, EN, "Britain, US", [1620, NOW], (22, "yard"), ["wp_english", "nist811"],
  notes="Surveyor's chain of 100 links; 10 square chains = 1 acre. A cricket pitch is 1 chain.")
U("link", "Link", L, EN, "Britain, US", [1620, NOW], (0.01, "chain"), ["wp_english"])
U("rod", "Rod / pole / perch", L, EN, "Britain, US", [1100, NOW], (5.5, "yard"), ["wp_english", "uk_wma"], aliases=["pole", "perch", "rood (length)"])
U("fathom", "Fathom", L, EN, "Britain, US (nautical)", [1000, NOW], (2, "yard"), ["wp_english", "nist811"],
  notes="Depth of water; originally the span of outstretched arms.")
U("hand", "Hand", L, EN, "Britain, US", [1500, NOW], (4, "inch"), ["wp_english"], notes="Used for the height of horses.")
U("span", "Span", L, EN, "Britain", [1100, 1900], (9, "inch"), ["wp_english"], notes="Thumb to little finger, spread.")
U("nail", "Nail (cloth)", L, EN, "Britain", [1400, 1900], (2.25, "inch"), ["wp_english"], notes="1/16 yard; cloth measure.")
U("barleycorn", "Barleycorn", L, EN, "Britain", [1100, NOW], (1 / 3, "inch"), ["wp_english"], notes="Still the step between shoe sizes.")
U("line", "Line", L, EN, "Britain", [1600, 1900], (1 / 12, "inch"), ["wp_english"], notes="Also the button-size 'ligne' (1/40 in) in trade.")
U("thou", "Thou / mil", L, EN, "Britain, US", [1850, NOW], (0.001, "inch"), ["nist811"], aliases=["mil"])
U("point_dtp", "Point (typographic)", L, EN, "International printing", [1985, NOW], (1 / 72, "inch"), ["wp_typo"],
  notes="Older Anglo-American printer's point was 0.013837 in.")
U("pica", "Pica", L, EN, "International printing", [1985, NOW], (12, "point_dtp"), ["wp_typo"])
U("cubit_en", "Cubit (English)", L, EN, "Britain", [1100, 1800], (18, "inch"), ["wp_cubit"], notes="KJV-era English reckoning of the cubit.")
U("ell_en", "Ell (English)", L, EN, "England", [1300, 1850], (45, "inch"), ["wp_ell"], notes="Cloth measure; Flemish ell 27 in, French ell ~47 in.")
U("league", "League (land)", L, EN, "Britain, US", [1300, 1900], (3, "mile"), ["wp_league"],
  notes="Roughly an hour's walk; marine league = 3 nautical miles. 'Twenty Thousand Leagues' uses the French lieue.")
U("nautical_mile", "Nautical mile", L, "Nautical", "International", [1929, NOW], ("si", 1852), ["wp_nmi", "nist811"], aliases=["nmi", "sea mile"],
  notes="Originally one minute of latitude.")
U("admiralty_mile", "Admiralty mile", L, "Nautical", "Britain", [1850, 1970], (6080, "foot"), ["wp_nmi"], notes="British nautical mile before 1970.")
U("cable_rn", "Cable (Royal Navy)", L, "Nautical", "Britain", [1600, NOW], (0.1, "admiralty_mile"), ["wp_cable"], aliases=["cable length"])
U("cable_us", "Cable (US Navy)", L, "Nautical", "US", [1800, NOW], (720, "foot"), ["wp_cable"], notes="120 fathoms.")
U("league_marine", "League (marine)", L, "Nautical", "International", [1600, 1950], (3, "nautical_mile"), ["wp_league"])
U("survey_foot", "US survey foot", L, EN, "US", [1893, 2022], ("si", 1200 / 3937), ["wp_survey", "nist811"],
  notes="Used in US land surveys until 2022; 2 ppm longer than the international foot.")
# Scotland / Ireland
U("ell_scots", "Ell (Scots)", L, "Scottish", "Scotland", [1400, 1824], ("si", 0.941), ["wp_scots"], notes="37 Scots inches ≈ 37.06 imperial inches.")
U("fall_scots", "Fall (Scots)", L, "Scottish", "Scotland", [1400, 1824], (6, "ell_scots"), ["wp_scots"])
U("mile_scots", "Mile (Scots)", L, "Scottish", "Scotland", [1400, 1824], (320, "fall_scots"), ["wp_scots"], notes="≈ 1.13 statute miles.")
U("perch_irish", "Perch (Irish)", L, "Irish", "Ireland", [1600, 1826], (7, "yard"), ["wp_irish"])
U("mile_irish", "Mile (Irish)", L, "Irish", "Ireland", [1600, 1826], (320, "perch_irish"), ["wp_irish"], notes="≈ 1.27 statute miles.")
# Rome
ROM = "Ancient Roman"
U("pes", "Pes (Roman foot)", L, ROM, "Roman world", [-500, 500], ("si", 0.296), ["wp_roman"], low=0.294, high=0.2963, aliases=["Roman foot"],
  notes="Usually reconstructed as 295.7-296.2 mm; the pes Drusianus of Germania was ≈ 333 mm.")
U("digitus", "Digitus", L, ROM, "Roman world", [-500, 500], (1 / 16, "pes"), ["wp_roman"])
U("uncia_len", "Uncia (Roman inch)", L, ROM, "Roman world", [-500, 500], (1 / 12, "pes"), ["wp_roman"])
U("palmus", "Palmus", L, ROM, "Roman world", [-500, 500], (0.25, "pes"), ["wp_roman"])
U("cubitus", "Cubitus", L, ROM, "Roman world", [-500, 500], (1.5, "pes"), ["wp_roman"])
U("gradus", "Gradus (step)", L, ROM, "Roman world", [-500, 500], (2.5, "pes"), ["wp_roman"])
U("passus", "Passus (pace)", L, ROM, "Roman world", [-500, 500], (5, "pes"), ["wp_roman"], notes="A double step.")
U("actus", "Actus", L, ROM, "Roman world", [-500, 500], (120, "pes"), ["wp_roman"])
U("stadium_rom", "Stadium (Roman)", L, ROM, "Roman world", [-200, 500], (625, "pes"), ["wp_roman"], notes="⅛ Roman mile.")
U("mille_passus", "Roman mile (mille passus)", L, ROM, "Roman world", [-300, 500], (1000, "passus"), ["wp_roman"], aliases=["mille passuum", "Roman mile"])
U("leuga", "Leuga (Gallic league)", L, ROM, "Roman Gaul, Germania", [100, 700], (7500, "pes"), ["wp_roman", "wp_league"])
# Greece / Persia
GRK = "Ancient Greek"
U("pous", "Pous (Greek foot)", L, GRK, "Greek world", [-700, 300], ("si", 0.308), ["wp_greek"], low=0.296, high=0.3205,
  notes="Regional values vary: Attic ≈ 296-308 mm, Olympic ≈ 320.5 mm.")
U("daktylos", "Daktylos", L, GRK, "Greek world", [-700, 300], (1 / 16, "pous"), ["wp_greek"])
U("pechys", "Pechys (Greek cubit)", L, GRK, "Greek world", [-700, 300], (1.5, "pous"), ["wp_greek"])
U("orguia", "Orguia (Greek fathom)", L, GRK, "Greek world", [-700, 300], (6, "pous"), ["wp_greek"])
U("plethron", "Plethron", L, GRK, "Greek world", [-700, 300], (100, "pous"), ["wp_greek"])
U("stadion", "Stadion", L, GRK, "Greek world", [-700, 300], (600, "pous"), ["wp_greek"], aliases=["stade", "furlong (KJV)"],
  notes="Length of a stadium race; 177-192 m depending on the foot used.")
U("parasang", "Parasang", L, "Ancient Persian", "Persia, Near East", [-500, 1900], ("si", 5600), ["wp_parasang"], low=4800, high=6400,
  aliases=["farsakh", "fersah", "farsang"], notes="Distance walked in about an hour; Herodotus gives 30 stadia.")
# Egypt / Mesopotamia / Bible
U("royal_cubit", "Royal cubit (meh niswt)", L, "Ancient Egyptian", "Egypt", [-2700, -300], ("si", 0.5236), ["wp_egypt", "wp_cubit"], low=0.523, high=0.529,
  notes="Measured from surviving cubit rods and the Great Pyramid; 7 palms = 28 digits.")
U("egypt_palm", "Palm (shesep)", L, "Ancient Egyptian", "Egypt", [-2700, -300], (1 / 7, "royal_cubit"), ["wp_egypt"])
U("egypt_digit", "Digit (djeba)", L, "Ancient Egyptian", "Egypt", [-2700, -300], (1 / 28, "royal_cubit"), ["wp_egypt"])
U("khet", "Khet", L, "Ancient Egyptian", "Egypt", [-2700, -300], (100, "royal_cubit"), ["wp_egypt"])
U("iteru", "Iteru (river measure)", L, "Ancient Egyptian", "Egypt", [-2700, -300], (20000, "royal_cubit"), ["wp_egypt"])
U("kus", "Kuš (Mesopotamian cubit)", L, "Mesopotamian", "Sumer, Babylonia", [-2500, -500], ("si", 0.497), ["wp_meso", "wp_cubit"], low=0.49, high=0.52)
U("cubit_bib", "Cubit (biblical, common)", L, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], ("si", 0.457), ["wp_bible", "wp_cubit"],
  low=0.444, high=0.48, aliases=["ammah", "amah"], notes="The 'cubit of a man' ≈ 18 in; Talmudic estimates 48-58 cm exist.")
U("cubit_bib_long", "Cubit (long / royal, Ezekiel)", L, "Biblical / Talmudic", "Israel, Judea", [-600, 500], ("si", 0.523), ["wp_bible", "wp_cubit"],
  low=0.51, high=0.53, notes="'A cubit and a handbreadth' (Ezekiel 40:5).")
U("span_bib", "Span (zeret)", L, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (0.5, "cubit_bib"), ["wp_bible"])
U("handbreadth", "Handbreadth (tefah)", L, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (1 / 6, "cubit_bib"), ["wp_bible"])
U("finger_bib", "Finger (etzba)", L, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (1 / 24, "cubit_bib"), ["wp_bible"])
U("reed", "Reed (qaneh)", L, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (6, "cubit_bib"), ["wp_bible"])
U("sabbath_journey", "Sabbath day's journey", L, "Biblical / Talmudic", "Judea", [-200, 500], (2000, "cubit_bib"), ["wp_bible"])
# France
FR = "French (pre-metric)"
U("pied_du_roi", "Pied du roi (French foot)", L, FR, "France, Quebec", [1668, 1840], ("si", 0.324839), ["wp_france"], aliases=["pied", "Paris foot"])
U("pouce", "Pouce (French inch)", L, FR, "France", [1668, 1840], (1 / 12, "pied_du_roi"), ["wp_france"])
U("ligne", "Ligne", L, FR, "France", [1668, 1840], (1 / 12, "pouce"), ["wp_france"])
U("toise", "Toise", L, FR, "France", [1668, 1840], (6, "pied_du_roi"), ["wp_france"], notes="The French fathom.")
U("perche_paris", "Perche (de Paris)", L, FR, "France", [1600, 1840], (18, "pied_du_roi"), ["wp_france", "wp_arpent"])
U("arpent_len", "Arpent (length)", L, FR, "France, Quebec, Louisiana", [1600, 1900], (10, "perche_paris"), ["wp_arpent"])
U("aune", "Aune (de Paris)", L, FR, "France", [1550, 1840], ("si", 1.188), ["wp_france", "wp_ell"], aliases=["French ell"])
U("lieue_poste", "Lieue de poste", L, FR, "France", [1737, 1840], (2000, "toise"), ["wp_lieue"])
U("lieue_commune", "Lieue commune (1/25°)", L, FR, "France", [1700, 1900], ("si", 4444.44), ["wp_lieue"],
  notes="Jules Verne's 'lieues' are usually the 4 km metric lieue or this.")
# German lands
DE = "German (pre-metric)"
U("rheinfuss", "Rheinfuß (Prussian foot)", L, DE, "Prussia, Rhineland, Denmark", [1755, 1872], ("si", 0.31385), ["wp_german"], aliases=["Rhineland foot", "Fuß"])
U("rute_pr", "Rute (Prussian)", L, DE, "Prussia", [1816, 1872], (12, "rheinfuss"), ["wp_german"])
U("meile_pr", "Meile (Prussian mile)", L, DE, "Prussia", [1816, 1872], (2000, "rute_pr"), ["wp_german"], notes="≈ 4.68 statute miles.")
U("elle_pr", "Elle (Prussian)", L, DE, "Prussia", [1816, 1872], ("si", 0.66694), ["wp_german", "wp_ell"])
U("fuss_wien", "Fuß (Viennese)", L, DE, "Austria", [1756, 1876], ("si", 0.316081), ["wp_german", "wp_klafter"])
U("klafter", "Klafter (Viennese)", L, DE, "Austria", [1756, 1876], (6, "fuss_wien"), ["wp_klafter"])
U("meile_at", "Meile (Austrian post mile)", L, DE, "Austria", [1756, 1876], (4000, "klafter"), ["wp_german"])
U("geo_mile", "Geographic mile (German)", L, DE, "Central Europe", [1700, 1900], ("si", 7420.4), ["wp_german"], notes="1/15 of a degree of the equator.")
# Russia
RU = "Russian (pre-1924)"
U("arshin", "Arshin", L, RU, "Russian Empire", [1700, 1924], (28, "inch"), ["wp_russia"])
U("vershok", "Vershok", L, RU, "Russian Empire", [1700, 1924], (1 / 16, "arshin"), ["wp_russia"])
U("sazhen", "Sazhen", L, RU, "Russian Empire", [1700, 1924], (3, "arshin"), ["wp_russia"], notes="7 English feet.")
U("verst", "Verst", L, RU, "Russian Empire", [1700, 1924], (500, "sazhen"), ["wp_russia"], aliases=["versta"], notes="≈ 0.66 statute miles.")
# Spain / Ottoman / Asia
U("vara", "Vara (de Burgos)", L, "Spanish customary", "Spain, Spanish America", [1568, 1880], ("si", 0.835905), ["wp_spain"],
  notes="Values in the Americas varied (Texas 33⅓ in; Mexico 838 mm).")
U("pie_es", "Pie (Castilian foot)", L, "Spanish customary", "Spain, Spanish America", [1568, 1880], (1 / 3, "vara"), ["wp_spain"])
U("legua_es", "Legua (legal)", L, "Spanish customary", "Spain, Spanish America", [1568, 1880], (5000, "vara"), ["wp_spain", "wp_league"],
  notes="Many other leguas (≈ 4.2-6.7 km) were in use.")
U("arsin", "Arşın (architect's)", L, "Ottoman", "Ottoman Empire", [1500, 1933], ("si", 0.758), ["wp_ottoman"], low=0.65, high=0.758,
  notes="Cloth arşın (endaze) ≈ 0.65 m.")
U("shaku", "Shaku", L, "Japanese", "Japan", [700, 1958], ("si", 10 / 33), ["wp_japan"], notes="Fixed at 10/33 m in 1891.")
U("sun", "Sun", L, "Japanese", "Japan", [700, 1958], (0.1, "shaku"), ["wp_japan"])
U("ken", "Ken", L, "Japanese", "Japan", [1600, 1958], (6, "shaku"), ["wp_japan"], notes="Spacing of building pillars.")
U("jo", "Jō", L, "Japanese", "Japan", [700, 1958], (10, "shaku"), ["wp_japan"])
U("cho_len", "Chō (length)", L, "Japanese", "Japan", [1600, 1958], (60, "ken"), ["wp_japan"])
U("ri_jp", "Ri (Japanese)", L, "Japanese", "Japan", [1600, 1958], (36, "cho_len"), ["wp_japan"], notes="≈ 3.93 km.")
U("chi_qing", "Chi (Qing)", L, "Chinese", "China", [1644, 1929], ("si", 0.32), ["wp_china"], low=0.31, high=0.3555,
  notes="Builder's chi ≈ 320 mm; other trades used different chi.")
U("cun_qing", "Cun (Qing)", L, "Chinese", "China", [1644, 1929], (0.1, "chi_qing"), ["wp_china"])
U("zhang_qing", "Zhang (Qing)", L, "Chinese", "China", [1644, 1929], (10, "chi_qing"), ["wp_china"])
U("li_qing", "Li (Qing)", L, "Chinese", "China", [1644, 1929], (1800, "chi_qing"), ["wp_china"])
U("chi_shi", "Chi (shì, modern)", L, "Chinese", "China", [1929, NOW], ("si", 1 / 3), ["wp_china"])
U("li_shi", "Li (shì, modern)", L, "Chinese", "China", [1929, NOW], ("si", 500), ["wp_china"])
U("gaz_ilahi", "Gaz (Ilahi, Mughal)", L, "Indian", "Mughal India", [1586, 1850], ("si", 0.83), ["wp_india"], low=0.79, high=0.84)
U("gaz_brit", "Gaz (British India)", L, "Indian", "British India", [1833, 1956], (1, "yard"), ["wp_india"])
U("hath", "Hath (Indian cubit)", L, "Indian", "India", [1500, 1956], (18, "inch"), ["wp_india"])
U("kos", "Kos (koss)", L, "Indian", "India", [1500, 1956], ("si", 3200), ["wp_india"], low=2500, high=4000, notes="Varied regionally; Mughal kos ≈ 3.2 km.")

# ================================================================ AREA
U("sq_metre", "Square metre", A, "Metric (SI)", "International", [1799, NOW], ("sq", "metre"), ["si"], aliases=["m²"])
U("are", "Are", A, "Metric", "International", [1795, NOW], (100, "sq_metre"), ["si"])
U("hectare", "Hectare", A, "Metric", "International", [1795, NOW], (100, "are"), ["si"], aliases=["ha"])
U("sq_foot", "Square foot", A, EN, "Britain, US", [1600, NOW], ("sq", "foot"), ["intl_yard"], aliases=["sq ft", "ft²"])
U("sq_yard", "Square yard", A, EN, "Britain, US", [1600, NOW], ("sq", "yard"), ["intl_yard"])
U("sq_rod", "Square rod / perch", A, EN, "Britain, US", [1300, NOW], ("sq", "rod"), ["wp_english"], aliases=["perch (area)", "pole (area)"])
U("rood", "Rood", A, EN, "Britain", [1300, 1985], (40, "sq_rod"), ["wp_english", "wp_acre"], notes="¼ acre.")
U("acre", "Acre", A, EN, "Britain, US", [1300, NOW], (4840, "sq_yard"), ["wp_acre", "uk_wma"], notes="A strip 1 furlong × 1 chain — a day's ploughing.")
U("square_roof", "Square (roofing)", A, EN, "US, Britain", [1850, NOW], (100, "sq_foot"), ["nist811"])
U("sq_mile", "Square mile", A, EN, "Britain, US", [1600, NOW], ("sq", "mile"), ["intl_yard"])
U("section", "Section", A, EN, "US", [1785, NOW], (1, "sq_mile"), ["wp_section"], notes="640 acres; a 'quarter section' (160 acres) was the Homestead Act claim.")
U("quarter_section", "Quarter section", A, EN, "US", [1785, NOW], (0.25, "section"), ["wp_section"])
U("township", "Township (survey)", A, EN, "US", [1785, NOW], (36, "section"), ["wp_section"])
U("hide", "Hide", A, "Anglo-Saxon / medieval English", "England", [600, 1300], (120, "acre"), ["wp_hide"], low=40 * 4046.86, high=120 * 4046.86,
  notes="Land to support one household; a tax unit. Nominally 120 acres, often much less in practice.")
U("carucate", "Carucate / ploughland", A, "Anglo-Saxon / medieval English", "Danelaw England", [900, 1300], (120, "acre"), ["wp_carucate"],
  low=60 * 4046.86, high=180 * 4046.86)
U("virgate", "Virgate / yardland", A, "Medieval English", "England", [1000, 1500], (0.25, "hide"), ["wp_virgate"], low=15 * 4046.86, high=40 * 4046.86)
U("oxgang", "Oxgang / bovate", A, "Medieval English", "Northern England, Scotland", [1000, 1500], (15, "acre"), ["wp_oxgang"],
  low=10 * 4046.86, high=20 * 4046.86, notes="⅛ of a carucate — the land one ox could plough.")
U("acre_scots", "Acre (Scots)", A, "Scottish", "Scotland", [1400, 1824], ("si", 5067), ["wp_scots", "wp_acre"], notes="≈ 1.26 English acres.")
U("acre_irish", "Acre (Irish / plantation)", A, "Irish", "Ireland", [1600, 1900], (160, "sq_perch_irish"), ["wp_irish", "wp_acre"], notes="≈ 1.62 English acres.")
U("sq_perch_irish", "Square perch (Irish)", A, "Irish", "Ireland", [1600, 1900], ("sq", "perch_irish"), ["wp_irish"])
U("jugerum", "Jugerum", A, ROM, "Roman world", [-500, 500], (28800, "sq_pes"), ["wp_roman"], aliases=["iugerum"],
  notes="2 square actus — what a yoke of oxen could plough in a day; ≈ ⅝ acre.")
U("sq_pes", "Square pes", A, ROM, "Roman world", [-500, 500], ("sq", "pes"), ["wp_roman"])
U("heredium", "Heredium", A, ROM, "Roman world", [-500, 500], (2, "jugerum"), ["wp_roman"])
U("centuria", "Centuria (land)", A, ROM, "Roman world", [-200, 500], (200, "jugerum"), ["wp_roman"])
U("plethron_sq", "Plethron (area)", A, GRK, "Greek world", [-700, 300], ("sq", "plethron"), ["wp_greek"])
U("setat", "Setat / aroura", A, "Ancient Egyptian", "Egypt", [-2700, 300], ("sq", "khet"), ["wp_egypt"], aliases=["aroura", "arura"])
U("arpent", "Arpent (de Paris)", A, FR, "France, Quebec, Louisiana", [1600, 1900], ("sq", "arpent_len"), ["wp_arpent"], notes="≈ 0.85 acre.")
U("arpent_ordonnance", "Arpent d'ordonnance (des eaux et forêts)", A, FR, "France", [1669, 1840], ("si", 5107.2), ["wp_arpent"])
U("morgen_pr", "Morgen (Prussian)", A, DE, "Prussia", [1816, 1872], ("si", 2553.22), ["wp_morgen"], notes="Varied enormously elsewhere (0.25-1 ha).")
U("morgen_nl", "Morgen (Dutch / Rhineland)", A, "Dutch", "Netherlands, Cape Colony, New Netherland", [1600, 1900], ("si", 8516), ["wp_morgen"])
U("joch", "Joch (Austrian)", A, DE, "Austria-Hungary", [1756, 1876], ("si", 5754.64), ["wp_joch"], aliases=["Katastraljoch", "hold (Hungarian)"])
U("desyatina", "Desyatina", A, RU, "Russian Empire", [1753, 1927], (2400, "sq_sazhen"), ["wp_desyatina"], notes="≈ 2.7 acres.")
U("sq_sazhen", "Square sazhen", A, RU, "Russian Empire", [1700, 1924], ("sq", "sazhen"), ["wp_russia"])
U("fanega_land", "Fanega (land, Castile)", A, "Spanish customary", "Spain", [1500, 1880], ("si", 6439.6), ["wp_spain"], low=3000, high=7000,
  notes="Land sown with a fanega of grain; varied by region.")
U("tsubo", "Tsubo", A, "Japanese", "Japan", [1600, NOW], ("sq", "ken"), ["wp_japan"], notes="Still used for floor areas in Japan.")
U("se", "Se", A, "Japanese", "Japan", [1600, 1958], (30, "tsubo"), ["wp_japan"])
U("tan", "Tan", A, "Japanese", "Japan", [1600, 1958], (300, "tsubo"), ["wp_japan"])
U("cho_area", "Chō (area)", A, "Japanese", "Japan", [1600, 1958], (3000, "tsubo"), ["wp_japan"], notes="≈ 1 hectare.")
U("mu_qing", "Mu (Qing)", A, "Chinese", "China", [1644, 1929], (6000, "sq_chi_qing"), ["wp_china"], notes="240 square bu of 5 chi.")
U("sq_chi_qing", "Square chi (Qing)", A, "Chinese", "China", [1644, 1929], ("sq", "chi_qing"), ["wp_china"])
U("mu_shi", "Mu (shì, modern)", A, "Chinese", "China", [1929, NOW], ("si", 2000 / 3), ["wp_china"], aliases=["mou"])
U("qing_area", "Qing (area)", A, "Chinese", "China", [1644, NOW], (100, "mu_shi"), ["wp_china"])
U("donum", "Dönüm (Ottoman)", A, "Ottoman", "Ottoman Empire", [1400, 1928], ("si", 919.3), ["wp_dunam", "wp_ottoman"], low=900, high=1000,
  aliases=["dunam", "dunum", "donum"])
U("dunam_metric", "Dunam (metric)", A, "Metric-derived", "Israel, Palestine, Turkey, Levant", [1928, NOW], ("si", 1000), ["wp_dunam"])
U("bigha", "Bigha", A, "Indian", "South Asia", [1500, NOW], ("si", 1337.8), ["wp_bigha"], low=1000, high=2700,
  notes="Bengal standard 1600 sq yd (⅓ acre); other regions differ widely.")

# ================================================================ VOLUME (litres)
U("litre", "Litre", V, "Metric", "International", [1795, NOW], ("si", 1), ["si"], aliases=["liter", "L"])
U("cu_inch", "Cubic inch", V, EN, "Britain, US", [1600, NOW], ("cu", "inch"), ["intl_yard"])
U("cu_foot", "Cubic foot", V, EN, "Britain, US", [1600, NOW], ("cu", "foot"), ["intl_yard"])
# US / wine
U("gal_us", "Gallon (US / wine / Queen Anne)", V, EN, "US; England (wine) 1707-1824", [1707, NOW], (231, "cu_inch"), ["wp_gallon", "nist811"],
  aliases=["wine gallon", "Queen Anne gallon"], sub="liquid")
U("qt_us", "Quart (US liquid)", V, EN, "US", [1707, NOW], (0.25, "gal_us"), ["wp_uscust"], sub="liquid")
U("pt_us", "Pint (US liquid)", V, EN, "US", [1707, NOW], (0.5, "qt_us"), ["wp_uscust"], sub="liquid")
U("cup_us", "Cup (US)", V, EN, "US", [1850, NOW], (0.5, "pt_us"), ["wp_uscust"], sub="liquid")
U("gill_us", "Gill (US)", V, EN, "US", [1707, NOW], (0.25, "pt_us"), ["wp_uscust"], sub="liquid")
U("floz_us", "Fluid ounce (US)", V, EN, "US", [1707, NOW], (1 / 128, "gal_us"), ["wp_uscust", "nist811"], sub="liquid")
U("tbsp_us", "Tablespoon (US)", V, EN, "US", [1850, NOW], (0.5, "floz_us"), ["wp_uscust"], sub="liquid")
U("tsp_us", "Teaspoon (US)", V, EN, "US", [1850, NOW], (1 / 3, "tbsp_us"), ["wp_uscust"], sub="liquid")
U("barrel_oil", "Barrel (petroleum)", V, EN, "International", [1866, NOW], (42, "gal_us"), ["wp_beer", "nist811"], aliases=["bbl"], sub="liquid")
U("tun", "Tun (wine)", V, EN, "England", [1300, 1824], (252, "gal_us"), ["wp_casks"], sub="liquid")
U("pipe", "Pipe / butt (wine)", V, EN, "England", [1300, 1824], (126, "gal_us"), ["wp_casks"], aliases=["butt"], sub="liquid",
  notes="A butt of sack/malmsey (e.g. Clarence's death in Richard III).")
U("puncheon", "Puncheon (wine)", V, EN, "England, Caribbean (rum)", [1400, 1824], (84, "gal_us"), ["wp_casks"], sub="liquid")
U("hogshead_wine", "Hogshead (wine)", V, EN, "England, colonies", [1400, 1824], (63, "gal_us"), ["wp_casks"], sub="liquid")
U("tierce", "Tierce", V, EN, "England", [1400, 1824], (42, "gal_us"), ["wp_casks"], sub="liquid")
U("barrel_wine", "Barrel (wine)", V, EN, "England", [1400, 1824], (31.5, "gal_us"), ["wp_casks"], sub="liquid")
U("rundlet", "Rundlet", V, EN, "England", [1400, 1824], (18, "gal_us"), ["wp_casks"], sub="liquid")
# ale / imperial
U("gal_ale", "Gallon (ale, pre-1824)", V, EN, "England", [1688, 1824], (282, "cu_inch"), ["wp_gallon"], sub="liquid")
U("gal_imp", "Gallon (imperial)", V, EN, "Britain, Commonwealth", [1824, NOW], ("si", 4.54609), ["uk_wma", "wp_gallon"], sub="liquid",
  notes="Defined as exactly 4.54609 L since 1985 (10 lb of water originally).")
U("qt_imp", "Quart (imperial)", V, EN, "Britain", [1824, NOW], (0.25, "gal_imp"), ["uk_wma"], sub="liquid")
U("pt_imp", "Pint (imperial)", V, EN, "Britain", [1824, NOW], (0.5, "qt_imp"), ["uk_wma"], sub="liquid", notes="Still the legal measure for draught beer in the UK.")
U("gill_imp", "Gill (imperial)", V, EN, "Britain", [1824, NOW], (0.25, "pt_imp"), ["uk_wma"], sub="liquid")
U("floz_imp", "Fluid ounce (imperial)", V, EN, "Britain", [1824, NOW], (1 / 160, "gal_imp"), ["uk_wma", "nist811"], sub="liquid")
U("fldr_imp", "Fluid drachm (imperial)", V, EN, "Britain (apothecary)", [1824, 1971], (1 / 8, "floz_imp"), ["wp_apoth"], sub="liquid", aliases=["fluid dram"])
U("minim_imp", "Minim (imperial)", V, EN, "Britain (apothecary)", [1824, 1971], (1 / 60, "fldr_imp"), ["wp_apoth"], sub="liquid", notes="About one drop.")
U("barrel_beer", "Barrel (beer, imperial)", V, EN, "Britain", [1824, NOW], (36, "gal_imp"), ["wp_beer"], sub="liquid")
U("hogshead_beer", "Hogshead (beer)", V, EN, "Britain", [1824, NOW], (54, "gal_imp"), ["wp_beer"], sub="liquid")
U("kilderkin", "Kilderkin", V, EN, "Britain", [1500, NOW], (18, "gal_imp"), ["wp_beer"], sub="liquid")
U("firkin", "Firkin (beer)", V, EN, "Britain", [1500, NOW], (9, "gal_imp"), ["wp_beer"], sub="liquid", notes="Also a butter weight of 56 lb.")
U("pin", "Pin", V, EN, "Britain", [1500, NOW], (4.5, "gal_imp"), ["wp_beer"], sub="liquid")
# dry
U("bu_us", "Bushel (Winchester / US)", V, EN, "England 1696-1824; US", [1696, NOW], (2150.42, "cu_inch"), ["wp_bushel", "nist811"], sub="dry")
U("pk_us", "Peck (US)", V, EN, "US", [1696, NOW], (0.25, "bu_us"), ["wp_bushel"], sub="dry")
U("galdry_us", "Gallon (US dry)", V, EN, "US", [1696, NOW], (0.125, "bu_us"), ["wp_gallon"], sub="dry")
U("qtdry_us", "Quart (US dry)", V, EN, "US", [1696, NOW], (0.25, "galdry_us"), ["wp_uscust"], sub="dry")
U("bu_imp", "Bushel (imperial)", V, EN, "Britain", [1824, 1985], (8, "gal_imp"), ["wp_bushel", "uk_wma"], sub="dry")
U("pk_imp", "Peck (imperial)", V, EN, "Britain", [1824, 1985], (2, "gal_imp"), ["wp_bushel"], sub="dry")
U("quarter_vol", "Quarter (grain)", V, EN, "Britain", [1200, 1985], (8, "bu_imp"), ["wp_english"], sub="dry", notes="Grain prices were quoted per quarter.")
U("chaldron", "Chaldron (coal)", V, EN, "Britain", [1600, 1835], (36, "bu_imp"), ["wp_chaldron"], sub="dry")
U("pint_scots", "Pint (Scots)", V, "Scottish", "Scotland", [1400, 1824], ("si", 1.696), ["wp_scots"], sub="liquid", aliases=["joug"], notes="≈ 3 imperial pints.")
U("boll", "Boll (Scots, wheat)", V, "Scottish", "Scotland", [1400, 1824], ("si", 145.4), ["wp_scots"], low=140, high=211, sub="dry",
  notes="Wheat/peas boll; the barley/oat boll was ≈ 211 L.")
U("firlot", "Firlot (Scots, wheat)", V, "Scottish", "Scotland", [1400, 1824], (0.25, "boll"), ["wp_scots"], sub="dry")
# Rome / Greece / Bible
U("amphora_rom", "Amphora (quadrantal)", V, ROM, "Roman world", [-300, 500], ("cu", "pes"), ["wp_roman"], sub="liquid", notes="One cubic Roman foot.")
U("culleus", "Culleus", V, ROM, "Roman world", [-300, 500], (20, "amphora_rom"), ["wp_roman"], sub="liquid")
U("congius", "Congius", V, ROM, "Roman world", [-300, 500], (1 / 8, "amphora_rom"), ["wp_roman"], sub="liquid")
U("sextarius", "Sextarius", V, ROM, "Roman world", [-300, 500], (1 / 6, "congius"), ["wp_roman"], sub="liquid", notes="Roughly an imperial pint.")
U("hemina", "Hemina", V, ROM, "Roman world", [-300, 500], (0.5, "sextarius"), ["wp_roman"], sub="liquid")
U("cyathus", "Cyathus", V, ROM, "Roman world", [-300, 500], (1 / 12, "sextarius"), ["wp_roman"], sub="liquid")
U("modius", "Modius", V, ROM, "Roman world", [-300, 500], (16, "sextarius"), ["wp_roman"], sub="dry", notes="Standard grain measure (≈ 6.5 kg wheat).")
U("metretes", "Metretes (Attic)", V, GRK, "Greek world", [-600, 300], ("si", 39.4), ["wp_greek"], low=38, high=40, sub="liquid", aliases=["amphora (Greek)"])
U("chous", "Chous", V, GRK, "Greek world", [-600, 300], (1 / 12, "metretes"), ["wp_greek"], sub="liquid")
U("kotyle", "Kotyle", V, GRK, "Greek world", [-600, 300], (1 / 12, "chous"), ["wp_greek"], sub="liquid")
U("kyathos", "Kyathos", V, GRK, "Greek world", [-600, 300], (1 / 6, "kotyle"), ["wp_greek"], sub="liquid")
U("medimnos", "Medimnos (Attic)", V, GRK, "Greek world", [-600, 300], ("si", 52.5), ["wp_greek"], low=51, high=59, sub="dry",
  notes="≈ 40 kg of wheat; Athenian grain prices are per medimnos.")
U("choinix", "Choinix", V, GRK, "Greek world", [-600, 300], (1 / 48, "medimnos"), ["wp_greek"], sub="dry", notes="A man's daily grain ration.")
U("bath", "Bath", V, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], ("si", 22), ["wp_bible"], low=21, high=39, sub="liquid",
  notes="Archaeological estimates ≈ 21-23 L; Josephus implies ≈ 39 L.")
U("ephah", "Ephah", V, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (1, "bath"), ["wp_bible"], sub="dry", notes="Dry equivalent of the bath (Ezekiel 45:11).")
U("homer", "Homer / kor", V, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (10, "bath"), ["wp_bible"], aliases=["kor", "cor"], sub="dry")
U("seah", "Seah", V, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (1 / 3, "ephah"), ["wp_bible"], sub="dry", aliases=["measure (KJV)"])
U("omer", "Omer", V, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (0.1, "ephah"), ["wp_bible"], sub="dry")
U("kab", "Kab / cab", V, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (1 / 6, "seah"), ["wp_bible"], sub="dry")
U("hin", "Hin", V, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (1 / 6, "bath"), ["wp_bible"], sub="liquid")
U("log", "Log", V, "Biblical / Talmudic", "Israel, Judea", [-1000, 500], (1 / 12, "hin"), ["wp_bible"], sub="liquid")
# France
U("pinte", "Pinte (de Paris)", V, FR, "France", [1600, 1840], ("si", 0.931389), ["wp_france"], sub="liquid")
U("chopine", "Chopine", V, FR, "France", [1600, 1840], (0.5, "pinte"), ["wp_france"], sub="liquid")
U("velte", "Velte", V, FR, "France", [1600, 1840], (8, "pinte"), ["wp_france"], sub="liquid")
U("muid_vin", "Muid (wine, Paris)", V, FR, "France", [1600, 1840], (288, "pinte"), ["wp_france"], sub="liquid")
U("boisseau", "Boisseau (de Paris)", V, FR, "France", [1600, 1840], ("si", 13.008), ["wp_france"], sub="dry")
U("minot", "Minot", V, FR, "France", [1600, 1840], (3, "boisseau"), ["wp_france"], sub="dry")
U("setier", "Setier (grain, Paris)", V, FR, "France", [1600, 1840], (12, "boisseau"), ["wp_france"], sub="dry")
U("muid_grain", "Muid (grain, Paris)", V, FR, "France", [1600, 1840], (12, "setier"), ["wp_france"], sub="dry")
# German / Russian / Spanish / Ottoman / Asia
U("quart_pr", "Quart (Prussian)", V, DE, "Prussia", [1816, 1872], ("si", 1.145), ["wp_german"], sub="liquid")
U("eimer_pr", "Eimer (Prussian)", V, DE, "Prussia", [1816, 1872], (60, "quart_pr"), ["wp_german"], sub="liquid")
U("scheffel_pr", "Scheffel (Prussian)", V, DE, "Prussia", [1816, 1872], ("si", 54.96), ["wp_german"], sub="dry")
U("mass_at", "Maß (Austrian)", V, DE, "Austria", [1756, 1876], ("si", 1.415), ["wp_german"], sub="liquid", aliases=["Mass"])
U("mass_by", "Maß (Bavarian)", V, DE, "Bavaria", [1811, 1871], ("si", 1.069), ["wp_german"], sub="liquid", notes="The Oktoberfest 'Maß' is now 1 L.")
U("vedro", "Vedro", V, RU, "Russian Empire", [1700, 1924], ("si", 12.29941), ["wp_russia"], sub="liquid", notes="'Bucket'.")
U("shtof", "Shtof", V, RU, "Russian Empire", [1700, 1924], (0.1, "vedro"), ["wp_russia"], sub="liquid", notes="A standard vodka bottle.")
U("charka", "Charka", V, RU, "Russian Empire", [1700, 1924], (0.01, "vedro"), ["wp_russia"], sub="liquid")
U("bochka", "Bochka", V, RU, "Russian Empire", [1700, 1924], (40, "vedro"), ["wp_russia"], sub="liquid")
U("chetvert", "Chetvert (dry)", V, RU, "Russian Empire", [1700, 1924], ("si", 209.91), ["wp_russia"], sub="dry")
U("chetverik", "Chetverik", V, RU, "Russian Empire", [1700, 1924], (1 / 8, "chetvert"), ["wp_russia"], sub="dry")
U("fanega", "Fanega (dry, Castile)", V, "Spanish customary", "Spain, Spanish America", [1500, 1880], ("si", 55.5), ["wp_spain"], sub="dry")
U("celemin", "Celemín", V, "Spanish customary", "Spain", [1500, 1880], (1 / 12, "fanega"), ["wp_spain"], sub="dry")
U("cantara", "Cántara / arroba (wine)", V, "Spanish customary", "Spain", [1500, 1880], ("si", 16.133), ["wp_spain"], sub="liquid")
U("azumbre", "Azumbre", V, "Spanish customary", "Spain", [1500, 1880], (1 / 8, "cantara"), ["wp_spain"], sub="liquid")
U("kile", "Kile (Istanbul)", V, "Ottoman", "Ottoman Empire", [1500, 1933], ("si", 37), ["wp_ottoman"], low=35, high=37, sub="dry")
U("koku", "Koku", V, "Japanese", "Japan", [1600, 1958], ("si", 240100 / 1331), ["wp_japan"], sub="dry",
  notes="Rice to feed one person for a year; domain wealth was ranked in koku.")
U("to_jp", "To", V, "Japanese", "Japan", [1600, 1958], (0.1, "koku"), ["wp_japan"], sub="dry")
U("sho", "Shō", V, "Japanese", "Japan", [1600, NOW], (0.01, "koku"), ["wp_japan"], notes="Sake bottles are still 1 shō (isshōbin).")
U("go", "Gō", V, "Japanese", "Japan", [1600, NOW], (0.001, "koku"), ["wp_japan"], notes="Rice-cup measure.")
U("sheng_qing", "Sheng (Qing)", V, "Chinese", "China", [1644, 1929], ("si", 1.0355), ["wp_china"], sub="dry")
U("dou_qing", "Dou (Qing)", V, "Chinese", "China", [1644, 1929], (10, "sheng_qing"), ["wp_china"], sub="dry", aliases=["peck (Chinese)"])
U("shi_vol", "Shi / dan (volume, Qing)", V, "Chinese", "China", [1644, 1929], (100, "sheng_qing"), ["wp_china"], sub="dry")

# ================================================================ MASS (kg)
U("kilogram", "Kilogram", M, "Metric (SI)", "International", [1799, NOW], ("si", 1), ["si"], aliases=["kg"])
U("lb", "Pound (avoirdupois)", M, EN, "Britain, US", [1300, NOW], ("si", 0.45359237), ["intl_yard", "uk_wma"], aliases=["lb", "pound"])
U("oz", "Ounce (avoirdupois)", M, EN, "Britain, US", [1300, NOW], (1 / 16, "lb"), ["wp_avdp"], aliases=["oz"])
U("dram_avdp", "Dram (avoirdupois)", M, EN, "Britain, US", [1300, NOW], (1 / 16, "oz"), ["wp_avdp"], aliases=["dr"])
U("grain", "Grain", M, EN, "Britain, US", [1100, NOW], (1 / 7000, "lb"), ["wp_avdp", "uk_wma"], aliases=["gr"],
  notes="Same grain in avoirdupois, troy and apothecaries' systems.")
U("stone", "Stone", M, EN, "Britain, Ireland", [1300, NOW], (14, "lb"), ["uk_wma"], aliases=["st"], notes="Varied by commodity before 1835 (e.g. 8 lb for meat).")
U("quarter_mass", "Quarter (weight)", M, EN, "Britain", [1300, NOW], (28, "lb"), ["wp_avdp"])
U("cwt_long", "Hundredweight (long)", M, EN, "Britain", [1300, NOW], (112, "lb"), ["uk_wma"], aliases=["cwt"])
U("cwt_short", "Hundredweight (short)", M, EN, "US", [1800, NOW], (100, "lb"), ["wp_uscust"])
U("ton_long", "Ton (long)", M, EN, "Britain", [1300, NOW], (2240, "lb"), ["uk_wma"], aliases=["imperial ton"], notes="A ship's 'tons burthen' is volume, not weight.")
U("ton_short", "Ton (short)", M, EN, "US", [1800, NOW], (2000, "lb"), ["wp_uscust"])
U("tonne", "Tonne (metric ton)", M, "Metric", "International", [1799, NOW], (1000, "kilogram"), ["si"])
U("clove", "Clove (wool)", M, EN, "England", [1300, 1850], (7, "lb"), ["wp_wool"])
U("tod", "Tod (wool)", M, EN, "England", [1300, 1850], (28, "lb"), ["wp_wool"])
U("sack_wool", "Sack (wool)", M, EN, "England", [1300, 1850], (364, "lb"), ["wp_wool"])
U("lb_troy", "Pound (troy)", M, EN, "Britain, US (precious metals)", [1527, 1879], (5760, "grain"), ["wp_troy"])
U("oz_troy", "Ounce (troy)", M, EN, "International (precious metals)", [1400, NOW], (480, "grain"), ["wp_troy", "nist811"], aliases=["ozt"])
U("dwt", "Pennyweight", M, EN, "Britain, US (precious metals)", [1100, NOW], (24, "grain"), ["wp_troy"], aliases=["dwt"])
U("lb_tower", "Tower pound", M, EN, "England (mint)", [800, 1527], (5400, "grain"), ["wp_troy"], notes="Mint pound before 1527; 240 pennies were struck from it.")
U("lb_merchant", "Merchants' pound", M, EN, "England", [1270, 1400], (6750, "grain"), ["wp_troy"], notes="15 Tower ounces.")
U("scruple", "Scruple (apothecaries')", M, EN, "Britain, US (pharmacy)", [1500, 1971], (20, "grain"), ["wp_apoth"])
U("drachm_ap", "Drachm (apothecaries')", M, EN, "Britain, US (pharmacy)", [1500, 1971], (60, "grain"), ["wp_apoth"], aliases=["dram (apothecaries')"])
U("carat", "Carat (metric)", M, "Metric", "International (gems)", [1907, NOW], ("si", 0.0002), ["wp_carat"], aliases=["ct"],
  notes="Pre-1907 carats ranged ≈ 188-215 mg.")
U("lb_scots_troy", "Pound (Scots troy)", M, "Scottish", "Scotland", [1618, 1824], ("si", 0.4944), ["wp_scots"])
U("lb_tron", "Tron pound (Scots)", M, "Scottish", "Scotland", [1400, 1824], ("si", 0.6), ["wp_scots"], low=0.55, high=0.68, notes="Varied by burgh and commodity.")
U("livre_poids", "Livre (poids de marc)", M, FR, "France", [1350, 1840], ("si", 0.4895058), ["wp_france"])
U("marc_fr", "Marc (French)", M, FR, "France", [1350, 1840], (0.5, "livre_poids"), ["wp_france"])
U("once_fr", "Once (French)", M, FR, "France", [1350, 1840], (1 / 16, "livre_poids"), ["wp_france"])
U("gros_fr", "Gros", M, FR, "France", [1350, 1840], (1 / 8, "once_fr"), ["wp_france"])
U("grain_fr", "Grain (French)", M, FR, "France", [1350, 1840], (1 / 72, "gros_fr"), ["wp_france"])
U("quintal_fr", "Quintal (French, old)", M, FR, "France", [1350, 1840], (100, "livre_poids"), ["wp_france"], notes="The metric quintal (1800s-) is 100 kg.")
U("cologne_mark", "Cologne mark", M, DE, "Holy Roman Empire, Germany", [1300, 1857], ("si", 0.233856), ["wp_cologne"],
  notes="Standard weight for minting silver; coin standards are given as 'n thalers per Cologne mark'.")
U("pfund_pr", "Pfund (Prussian, 1816)", M, DE, "Prussia", [1816, 1857], ("si", 0.467711), ["wp_german"])
U("lot_pr", "Lot (Prussian)", M, DE, "Prussia", [1816, 1857], (1 / 32, "pfund_pr"), ["wp_german"])
U("zollpfund", "Zollpfund", M, DE, "German Customs Union", [1858, 1884], ("si", 0.5), ["wp_german"], notes="Colloquial 'Pfund' = 500 g to this day.")
U("zentner", "Zentner", M, DE, "Germany", [1858, NOW], (100, "zollpfund"), ["wp_german"], aliases=["hundredweight (German)"])
U("pfund_wien", "Pfund (Viennese)", M, DE, "Austria", [1761, 1876], ("si", 0.56006), ["wp_german"])
U("funt", "Funt", M, RU, "Russian Empire", [1700, 1924], ("si", 0.40951241), ["wp_russia"], aliases=["Russian pound"])
U("pud", "Pud", M, RU, "Russian Empire", [1700, 1924], (40, "funt"), ["wp_russia"], aliases=["pood"])
U("berkovets", "Berkovets", M, RU, "Russian Empire", [1700, 1924], (10, "pud"), ["wp_russia"])
U("lot_ru", "Lot (Russian)", M, RU, "Russian Empire", [1700, 1924], (1 / 32, "funt"), ["wp_russia"])
U("zolotnik", "Zolotnik", M, RU, "Russian Empire", [1700, 1924], (1 / 96, "funt"), ["wp_russia"])
U("dolya", "Dolya", M, RU, "Russian Empire", [1700, 1924], (1 / 96, "zolotnik"), ["wp_russia"])
U("libra_es", "Libra (Castilian)", M, "Spanish customary", "Spain, Spanish America", [1500, 1880], ("si", 0.4601), ["wp_spain"])
U("onza_es", "Onza", M, "Spanish customary", "Spain, Spanish America", [1500, 1880], (1 / 16, "libra_es"), ["wp_spain"])
U("arroba_es", "Arroba (Castilian)", M, "Spanish customary", "Spain, Spanish America", [1500, 1880], (25, "libra_es"), ["wp_spain"])
U("quintal_es", "Quintal (Castilian)", M, "Spanish customary", "Spain, Spanish America", [1500, 1880], (100, "libra_es"), ["wp_spain"])
U("arratel", "Arrátel", M, "Portuguese customary", "Portugal, Brazil", [1500, 1872], ("si", 0.459), ["wp_portugal"])
U("arroba_pt", "Arroba (Portuguese)", M, "Portuguese customary", "Portugal, Brazil", [1500, 1872], (32, "arratel"), ["wp_portugal"])
U("okka", "Okka / oka", M, "Ottoman", "Ottoman Empire, Balkans, Egypt", [1500, 1934], ("si", 1.2829), ["wp_ottoman"], aliases=["oke", "oka"])
U("dirhem", "Dirhem", M, "Ottoman", "Ottoman Empire", [1500, 1934], (1 / 400, "okka"), ["wp_ottoman"])
U("kantar", "Kantar / qintar", M, "Ottoman", "Ottoman Empire, Levant", [1500, 1934], (44, "okka"), ["wp_ottoman"], notes="Varied by place and commodity.")
U("monme", "Monme", M, "Japanese", "Japan", [1600, NOW], ("si", 0.00375), ["wp_japan"], notes="Still used for pearls ('mom').")
U("kin", "Kin", M, "Japanese", "Japan", [1600, 1958], (160, "monme"), ["wp_japan"], aliases=["catty (Japanese)"])
U("kan", "Kan / kanme", M, "Japanese", "Japan", [1600, 1958], (1000, "monme"), ["wp_japan"])
U("liang_qing", "Liang / tael (Qing)", M, "Chinese", "China", [1644, 1929], ("si", 0.0373), ["wp_china", "wp_catty"], aliases=["tael"])
U("qian_qing", "Qian / mace (Qing)", M, "Chinese", "China", [1644, 1929], (0.1, "liang_qing"), ["wp_china"])
U("jin_qing", "Jin / catty (Qing)", M, "Chinese", "China", [1644, 1929], (16, "liang_qing"), ["wp_china", "wp_catty"], aliases=["catty"])
U("picul", "Dan / picul", M, "Chinese", "China, SE Asia", [1644, 1929], (100, "jin_qing"), ["wp_china"], notes="A shoulder-pole load.")
U("catty_hk", "Catty (Hong Kong legal)", M, "Chinese", "Hong Kong, Malaya, Singapore", [1844, NOW], ("si", 0.60478982), ["wp_catty"], notes="1⅓ lb avoirdupois.")
U("jin_shi", "Jin (shì, modern)", M, "Chinese", "China", [1929, NOW], ("si", 0.5), ["wp_catty"])
U("tola", "Tola", M, "Indian", "South Asia", [1500, NOW], (180, "grain"), ["wp_tola"], notes="Still used for gold in South Asia and the Gulf.")
U("ratti", "Ratti", M, "Indian", "South Asia", [1000, NOW], (1 / 96, "tola"), ["wp_india"], notes="A seed weight; varied ≈ 0.12-0.18 g.")
U("seer", "Seer", M, "Indian", "British India", [1833, 1956], (80, "tola"), ["wp_india", "wp_maund"])
U("maund", "Maund (Indian government)", M, "Indian", "British India", [1833, 1956], (40, "seer"), ["wp_maund"], aliases=["mun"])
U("maund_bengal", "Maund (Bengal factory)", M, "Indian", "Bengal (East India Company)", [1700, 1833], ("si", 33.8688), ["wp_maund"])
U("libra_rom", "Libra (Roman pound)", M, ROM, "Roman world", [-300, 500], ("si", 0.3275), ["wp_roman"], low=0.322, high=0.329)
U("uncia_mass", "Uncia (Roman ounce)", M, ROM, "Roman world", [-300, 500], (1 / 12, "libra_rom"), ["wp_roman"])
U("scripulum", "Scripulum", M, ROM, "Roman world", [-300, 500], (1 / 288, "libra_rom"), ["wp_roman"])
U("siliqua", "Siliqua", M, ROM, "Roman world", [-300, 500], (1 / 6, "scripulum"), ["wp_roman"], notes="Carob seed; origin of 'carat'.")
U("mina_att", "Mina (Attic)", M, GRK, "Greek world", [-600, 300], ("si", 0.431), ["wp_greek"], low=0.425, high=0.437)
U("drachma_mass", "Drachma (weight)", M, GRK, "Greek world", [-600, 300], (0.01, "mina_att"), ["wp_greek"])
U("obol_mass", "Obol (weight)", M, GRK, "Greek world", [-600, 300], (1 / 6, "drachma_mass"), ["wp_greek"])
U("talent_att", "Talent (Attic)", M, GRK, "Greek world", [-600, 300], (60, "mina_att"), ["wp_greek"], notes="≈ the load one man could carry.")
U("shekel_bib", "Shekel (biblical)", M, "Biblical / Talmudic", "Israel, Judea", [-1000, 100], ("si", 0.0114), ["wp_bible", "wp_shekel"], low=0.010, high=0.013)
U("gerah", "Gerah", M, "Biblical / Talmudic", "Israel, Judea", [-1000, 100], (1 / 20, "shekel_bib"), ["wp_bible"])
U("beka", "Beka", M, "Biblical / Talmudic", "Israel, Judea", [-1000, 100], (0.5, "shekel_bib"), ["wp_bible"])
U("mina_bib", "Mina / maneh (biblical)", M, "Biblical / Talmudic", "Israel, Judea", [-1000, 100], (50, "shekel_bib"), ["wp_bible"])
U("talent_bib", "Talent / kikkar (biblical)", M, "Biblical / Talmudic", "Israel, Judea", [-1000, 100], (3000, "shekel_bib"), ["wp_bible"])
U("shekel_meso", "Shekel (Mesopotamian)", M, "Mesopotamian", "Sumer, Babylonia, Assyria", [-2500, -500], ("si", 0.00833), ["wp_meso"], low=0.0083, high=0.0084)
U("se_grain", "Še (grain)", M, "Mesopotamian", "Sumer, Babylonia", [-2500, -500], (1 / 180, "shekel_meso"), ["wp_meso"])
U("mina_meso", "Mina (Mesopotamian)", M, "Mesopotamian", "Sumer, Babylonia, Assyria", [-2500, -500], (60, "shekel_meso"), ["wp_meso"])
U("talent_meso", "Talent (Mesopotamian)", M, "Mesopotamian", "Sumer, Babylonia, Assyria", [-2500, -500], (60, "mina_meso"), ["wp_meso"])
U("deben", "Deben (New Kingdom)", M, "Ancient Egyptian", "Egypt", [-1550, -300], ("si", 0.091), ["wp_egypt"], low=0.09, high=0.0915,
  notes="Earlier deben were ≈ 13.6 g (gold) or ≈ 27 g (copper).")
U("kite", "Kite / qedet", M, "Ancient Egyptian", "Egypt", [-1550, -300], (0.1, "deben"), ["wp_egypt"])

# ================================================================ COUNT
CNT = "Counting"
U("each", "Each (unit)", C, CNT, "International", [None, NOW], ("si", 1), ["wp_dozen"])
U("dozen", "Dozen", C, CNT, "International", [1300, NOW], (12, "each"), ["wp_dozen"])
U("bakers_dozen", "Baker's dozen", C, CNT, "Britain", [1500, NOW], (13, "each"), ["wp_dozen"], aliases=["long dozen"])
U("score", "Score", C, CNT, "Britain", [1000, NOW], (20, "each"), ["wp_dozen"], notes="'Four score and seven' = 87.")
U("long_hundred", "Long hundred / great hundred", C, CNT, "Northern Europe", [800, 1800], (120, "each"), ["wp_longhundred"])
U("gross", "Gross", C, CNT, "International", [1400, NOW], (144, "each"), ["wp_gross"])
U("great_gross", "Great gross", C, CNT, "International", [1600, NOW], (1728, "each"), ["wp_gross"])
U("quire_old", "Quire (old)", C, CNT, "Britain", [1400, 1950], (24, "each"), ["wp_ream"], notes="Sheets of paper.")
U("ream_old", "Ream (old)", C, CNT, "Britain", [1400, 1950], (20, "quire_old"), ["wp_ream"])
U("quire", "Quire (modern)", C, CNT, "International", [1900, NOW], (25, "each"), ["wp_ream"])
U("ream", "Ream (modern)", C, CNT, "International", [1900, NOW], (20, "quire"), ["wp_ream"])

# ================================================================ resolve
BASE = {L: "m", A: "m²", V: "L", M: "kg", C: "each"}
BY_ID = {u["id"]: u for u in UNITS}
# base values fixed by law or definition; other base values are measured approximations
EXACT = {"metre", "inch", "nautical_mile", "survey_foot", "gal_imp", "lb", "kilogram", "carat", "litre", "zollpfund",
         "chi_shi", "li_shi", "mu_shi", "jin_shi", "catty_hk", "shaku", "koku", "monme", "each", "dunam_metric"}
assert len(BY_ID) == len(UNITS), "duplicate unit id"


def sig(x, n=12):
    if x == 0:
        return 0
    return float(f"{x:.{n}g}")


def fmt(x):
    return f"{x:.6g}"


def resolve(uid, stack=()):
    """Returns (value, low, high, exact)."""
    u = BY_ID[uid]
    if "value" in u:
        return u["value"], u["lo"], u["hi"], u["exact"]
    assert uid not in stack, f"cycle at {uid}"
    d = u["defn"]
    if d[0] == "si":
        v, exact, lo, hi = d[1], uid in EXACT, d[1], d[1]
    elif d[0] in ("sq", "cu"):
        pv, plo, phi, pexact = resolve(d[1], stack + (uid,))
        p = 2 if d[0] == "sq" else 3
        k = 1000 if d[0] == "cu" else 1  # cubic metres -> litres
        v, lo, hi, exact = pv ** p * k, plo ** p * k, phi ** p * k, pexact
    else:
        f, parent = d
        pv, plo, phi, pexact = resolve(parent, stack + (uid,))
        v, lo, hi, exact = f * pv, f * plo, f * phi, pexact
    if u["low"] is not None:
        lo, hi, exact = u["low"], u["high"], False
    u.update(value=v, lo=lo, hi=hi, exact=exact)
    return v, lo, hi, exact


def describe(u):
    d = u["defn"]
    base = BASE[u["category"]]
    if d[0] == "si":
        return f"Defined/measured directly as {fmt(d[1])} {base}."
    if d[0] in ("sq", "cu"):
        p = BY_ID[d[1]]
        word = "square" if d[0] == "sq" else "cube"
        conv = " (× 1000 L per m³)" if d[0] == "cu" else ""
        return f"The {word} of one {p['name']} ({fmt(p['value'])} m){conv} = {fmt(u['value'])} {base}."
    f, parent = d
    p = BY_ID[parent]
    ff = f"{f:g}" if f >= 1 or f == 0 else f"1/{1/f:g}" if abs(1 / f - round(1 / f)) < 1e-9 else f"{f:g}"
    return f"{ff} × {p['name']} ({fmt(p['value'])} {base}) = {fmt(u['value'])} {base}."


out = []
for u in UNITS:
    resolve(u["id"])
for u in UNITS:
    d = u["defn"]
    reasoning = describe(u)
    precision = "uncertain" if u["low"] is not None or (u["lo"] != u["hi"]) else "exact" if u["exact"] else "approximate"
    if precision == "uncertain":
        reasoning += f" Uncertain or variable: plausible range {fmt(u['lo'])}-{fmt(u['hi'])} {BASE[u['category']]}."
    elif precision == "approximate":
        reasoning += " Value is a modern measurement/reconstruction of a historical standard, not an exact legal definition."
    sources = []
    for i, k in enumerate(u["srcs"]):
        title, url = SRC[k]
        sources.append({"title": title, "url": url,
                        "reasoning": reasoning if i == 0 else "Independent statement of the same definition/value, cited as corroboration."})
    rec = {"id": u["id"], "name": u["name"], "category": u["category"]}
    if u["subcategory"]:
        rec["subcategory"] = u["subcategory"]
    rec.update({"system": u["system"], "region": u["region"], "era": u["era"], "aliases": u["aliases"],
                "si": sig(u["value"]), "siUnit": BASE[u["category"]], "precision": precision})
    if precision == "uncertain":
        rec["low"], rec["high"] = sig(u["lo"]), sig(u["hi"])
    if d[0] == "si":
        rec["definition"] = {"type": "base"}
    elif d[0] in ("sq", "cu"):
        rec["definition"] = {"type": "square" if d[0] == "sq" else "cube", "of": d[1]}
    else:
        rec["definition"] = {"type": "multiple", "factor": sig(d[0], 12), "of": d[1]}
    if u["notes"]:
        rec["notes"] = u["notes"]
    rec["sources"] = sources
    out.append(rec)

doc = {
    "schemaVersion": 1,
    "title": "Historical and contemporary units of measurement",
    "generated": "2026-10-08",
    "baseUnits": BASE,
    "notes": [
        "'si' is the unit's value in the base unit for its category (m, m², L, kg, each). Convert any unit to any other in the "
        "same category via si: amount × from.si / to.si.",
        "'definition' records how the unit is defined (a multiple of another unit, the square/cube of a length, or a base "
        "value), so relationships like '1 furlong = 10 chains' can be shown.",
        "'precision': 'exact' = fixed by law/definition (e.g. 1 inch = 25.4 mm); 'approximate' = a well-measured historical "
        "standard; 'uncertain' = variable or reconstructed, with 'low'/'high' giving the plausible range across sources, "
        "periods or regions. Many pre-modern units varied from town to town.",
        "'era' is [first, last] year of common use (approximate; negative = BCE; null = still in use).",
        "Volume units carry subcategory 'liquid' or 'dry' where the distinction matters.",
    ],
    "units": out,
}
json.dump(doc, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "units;", {c: sum(1 for u in out if u["category"] == c) for c in BASE})
