# Ye Olde Converter

Makes sense of the money and measures, inspired by that feeling of adriftness you get when a book mentions an unfamiliar currency. It converts:

- **Money:** 35 historical currencies, from the Roman denarius to the Deutsche Mark, into 2025 US dollars for a given year, or into one another. It reads sums as books write them (`£3 4s 6d`, `2 guineas`, `30 denarii`) and explains coins ("what's a florin?"). It also includes fictional money: D&D, Westeros, Star Wars, Star Trek, Discworld and Hitchhiker's.
- **Measures:** 364 units of length, area, volume, mass and count, including English, French, German, Russian, Japanese, Chinese, Indian, Roman, Greek, biblical, astronomical and fictional units.

Every value comes with a plausible range, a confidence rating and its sources. It is not meant to have the highest accuracy, but rather to get a general sense or intuition around numbers.

Yes, this is entirely written by AI, but I have double checked some sources and tried to suggest remaining at least slightly accurate, so again: not meant to be the highest accuracy, just provide a general intuition.

## Usage

Easiest way to use it is in the example site, hosted at https://nhawk.in/ideas/tools/converter/yeolde.htm. Otherwise, if you want to use it programatically:

```sh
npm install yeoldeconverter
```

```ts
import { currencies, units } from "yeoldeconverter";

const sum = currencies.parseAmount("£3 4s 6d", "gbp", 1815);
currencies.toUSD2025(sum.base, { currency: "gbp", year: 1815 }); // { amount, low, high, confidence, from: { sources, … } }
currencies.convert(100, { currency: "livre", year: 1780 }, { currency: "gbp", year: 1780 });
currencies.describeDenomination("gbp", "florin", 1900);          // 2 shillings, ≈ $16

units.convert(3, "league", "kilometre");                         // { value: 14.48, low, high, precision: "exact" }
units.explain("hogshead_wine");                                  // "Hogshead (wine) = 63 × Gallon (US / wine / Queen Anne) = 238.481 L, exact"
```

Lookups accept names, aliases and plurals. An ambiguous name such as "gallon" throws an `AmbiguousError` listing the candidates.

The full data is large (about 3 MB) because every data point carries its sources. If you only need the numbers, import `yeoldeconverter/slim` instead. It has the same API and gives the same results, but without sources or notes.

In the browser, load a bundle from jsDelivr:

```html
<script src="https://cdn.jsdelivr.net/npm/yeoldeconverter/dist/yeoldeconverter.slim.iife.min.js"></script>
<script>
  YeOldeConverter.units.convert(1, "furlong", "metre");
</script>
```

The bundles are `yeoldeconverter.min.js` (ES module) and `yeoldeconverter.iife.min.js` (script tag), each also available as a `.slim` version. `example/index.html` is a demo page.

## Where the data comes from

**Currencies.** Each value answers one question: how many 2025 dollars buy the same consumer goods that one unit bought in that year?

1. The currency is converted into pounds sterling of the time (up to 1910) or US dollars (from 1915). This uses its silver or gold content, legal parities such as the gold standard, or recorded exchange rates.
2. That amount is adjusted to 2025 with consumer price indexes: the Bank of England's *Millennium of Macroeconomic Data* joined to ONS CPI for the UK, and the Minneapolis Fed CPI for the US.
3. Where no price index exists (antiquity, Edo Japan), the value is estimated from grain or rice prices.

Rates and coin standards come from MeasuringWorth, the Bank of England and the Federal Reserve, from monetary histories (Spooner, Pamuk, Gemmill & Mayhew, Scheidel), and from Wikipedia for coin weights and parities. Fictional rates come from the works themselves or their official and fan references.

**Units.** Values are based on statutes and standards (the 1959 international yard and pound, the UK Weights and Measures Act 1985, NIST, BIPM, the IAU and CODATA), and on reference articles for historical units. Each unit is defined in terms of another, so conversions stay consistent with each other.

**Every data point lists its own sources**, with links and the reasoning for each step, in `data/currencies.json` and `data/units.json`. The scripts in `scripts/` rebuild these files.

**Caveats:**
- Medieval and ancient figures are rough.
- Price-based values understate how large a sum felt before about 1900. Comparing against wages gives 3–10× more.
- Pre-standard units varied from town to town.

The ranges reflect all of this.

## License

[MIT](LICENSE). Releases are published to npm automatically when a GitHub release tagged `vX.Y.Z` is published.



## Everything it accepts

### Currencies

Pass a currency's ID, name or an alias. Coins can be named in amounts (`2 guineas`) and in `denomination` options.

| Currency | ID | Years (or source) | Coins and units of account |
|---|---|---|---|
| Pound sterling | `gbp` | 1210–2025 | Pound (sovereign/quid), Mark (money of account), Noble, Angel, Sovereign (Tudor), Guinea, Sovereign, Half sovereign, Crown, Half-crown, Florin, Shilling, Sixpence, Groat, Threepence, Twopence, Penny (old), Halfpenny, Farthing, Penny (decimal) |
| Pound Scots | `scots` | 1370–1705 | Pound Scots, Merk, Shilling Scots, Bawbee, Plack, Bodle / turner, Penny Scots |
| Irish pound (pre-1826) | `iep_old` | 1705–1825 | Pound (Irish), Shilling (Irish), Penny (Irish), Guinea (in Ireland) |
| United States dollar | `usd` | 1795–2025 | Dollar, Eagle, Double eagle, Half eagle, Quarter eagle, Half dollar, Quarter, Bit, Dime, Nickel / half dime, Cent, Mill |
| Spanish dollar (peso, real de a ocho) | `spd` | 1575–1850 | Dollar / peso / piece of eight, Real (silver), Half real (medio), Maravedí, Escudo (gold), Pistole (2 escudos), Doubloon (8 escudos / onza) |
| Livre tournois | `livre` | 1270–1795 | Livre (tournois), Sou / sol, Denier, Liard, Gros tournois, Écu d'or, Écu (silver, 'écu blanc'), Louis d'or, Pistole (accounting) |
| French franc (1795-1959) | `frf` | 1800–1955 | Franc, Centime, Décime, Sou, Écu / pièce de cent sous, Napoléon / louis |
| French new franc (1960-2001) | `frf_new` | 1960–2000 | Franc, Centime, Ancien franc |
| Prussian / North German thaler | `thaler` | 1750–1870 | Thaler, Gute Groschen, Silbergroschen, Pfennig, Friedrich d'or, South German gulden, Kreuzer (south German), Mark (1873 conversion) |
| German mark (Goldmark / Papiermark) | `mark` | 1875–1920 | Mark, Pfennig, Thaler (coin, still current to 1907), Krone (gold 10 marks), Doppelkrone (gold 20 marks) |
| Reichsmark | `reichsmark` | 1925–1940 | Reichsmark, Reichspfennig |
| Deutsche Mark | `dem` | 1950–2000 | Deutsche Mark, Pfennig, Groschen (colloquial), Heiermann (slang) |
| Austrian gulden (florin) | `aut_gulden` | 1760–1890 | Gulden / florin, Kreuzer, Conventionsthaler / Maria Theresa thaler, Ducat (Austrian gold), Krone (1892 conversion) |
| Austro-Hungarian krone | `aut_krone` | 1895–1910 | Krone / korona, Heller / fillér, Gulden (old) |
| Florentine florin | `florin_fl` | 1255–1530 | Florin (fiorino d'oro), Lira (di piccioli, Florentine), Soldo, Denaro |
| Venetian ducat (zecchino) | `ducat_ve` | 1285–1795 | Ducat / zecchino / sequin, Lira di piccoli, Soldo, Grosso, Ducat of account (6 lire 4 soldi) |
| Italian lira | `itl` | 1865–2000 | Lira, Centesimo, Soldo (colloquial), Scudo (5 lire silver) |
| Dutch guilder | `nlg` | 1600–2000 | Guilder / gulden, Stuiver, Duit, Schelling, Daalder, Rijksdaalder, Ducaton (silver rider), Cent, Dubbeltje, Kwartje, Gouden tientje |
| Portuguese real / milréis | `pte_real` | 1725–1890 | Milréis (1,000 réis), Real (pl. réis), Vintém, Tostão, Cruzado, Moidore (moeda d'ouro), Johannes / joe / peça, Conto (de réis) |
| Russian ruble (imperial) | `rub_imp` | 1705–1915 | Ruble (rouble), Kopek (kopeck), Denga / denezhka, Polushka, Altyn, Grivennik / grivna, Piatialtynnyi, Chetvertak / polupoltina, Poltina / poltinnik, Imperial (gold), Half-imperial, Assignat ruble (paper) |
| Ryō (Tokugawa coinage) | `ryo` | 1605–1865 | Ryō (koban), Bu (ichibu), Shu (isshu), Mon (copper), Kan (kanmon, string of 1,000 mon), Monme (of silver), Kanme (1,000 monme of silver) |
| Japanese yen | `jpy` | 1870–2025 | Yen, Sen, Rin, Ryō (at 1871 conversion) |
| Chinese silver tael (liang) | `tael` | 1650–1930 | Tael / liang, Mace / qian, Candareen / fen, Li / cash (weight), Cash (wen, copper coin), String of cash (diao/chuan), Silver dollar / yuan (1889-), Sycee ingot (yuanbao) |
| Renminbi (yuan) | `cny` | 1955–2025 | Yuan, Jiao, Fen |
| Indian rupee | `inr` | 1600–2025 | Rupee / rupiya, Anna, Pice / paisa (old), Pie, Naya paisa / paisa, Mohur (gold), Star pagoda (Madras), Lakh, Crore |
| Ottoman akçe (asper) | `akce` | 1330–1685 | Akçe / asper, Para, Kuruş (when introduced), Sultani / altın (gold) |
| Ottoman kuruş (piastre) | `kurus` | 1690–1910 | Kuruş / piastre, Para, Akçe, Mecidiye (silver), Lira (gold) / Turkish pound, Purse (kese) |
| Euro | `eur` | 2000–2025 | Euro, Cent |
| Swiss franc | `chf` | 1850–2025 | Franc / Franken, Rappen / centime, Batzen (colloquial 10 Rp.) |
| Swedish krona | `sek` | 1875–2025 | Krona, Öre |
| Spanish peseta | `esp` | 1870–2000 | Peseta, Céntimo, Duro, Real (colloquial) |
| Roman denarius | `denarius` | 200 BC–301 | Denarius, Aureus (gold), Antoninianus, Quinarius, Sestertius, Dupondius, As, Semis, Quadrans |
| Solidus / nomisma (Late Roman & Byzantine) | `solidus` | 325–1050 | Solidus / nomisma / bezant, Semissis, Tremissis, Miliaresion (silver), Siliqua / keration, Follis (bronze), Pound of gold (litra), Kentenarion |
| Athenian drachma | `drachma_att` | 450 BC–300 BC | Drachma, Obol, Hemiobol, Chalkous, Didrachm / stater, Tetradrachm ('owl'), Mina, Talent |
| Shekel (ancient Near East / biblical) | `shekel` | 1750 BC–30 | Shekel, Gerah, Beka (half-shekel), Mina / maneh, Talent / kikkar, Drachma (1st c.), Denarius (1st c.), Thirty pieces of silver |
| Dungeons & Dragons coinage | `dnd` | *Dungeons & Dragons (TSR / Wizards of the Coast, 1974–)* | Gold piece, Platinum piece, Electrum piece, Silver piece, Copper piece |
| Westerosi coinage | `westeros` | *A Song of Ice and Fire (George R. R. Martin, 1996–)* | Gold dragon, Silver moon, Silver stag, Copper star, Half-groat, Groat, Copper penny, Halfpenny |
| Galactic credit (with Hutt coinage) | `sw_credit` | *Star Wars (Lucasfilm, 1977–)* | Credit, Wupiupi, Trugut, Peggat |
| Gold-pressed latinum | `latinum` | *Star Trek (Paramount, Deep Space Nine 1993–1999)* | Bar, Strip, Slip |
| Ankh-Morpork dollar | `ankh_morpork` | *Discworld (Terry Pratchett, 1983–2015)* | Dollar, Guinea, Crown, Half-crown, Shilling, Sixpence, Groat, Thruppeny bit, Penny, Halfpenny, Farthing, Mite, Elim |
| Triganic Pu | `triganic_pu` | *The Hitchhiker's Guide to the Galaxy (Douglas Adams, 1978–)* | Pu, Ningi |

### Units

Pass a unit's ID, name or an alias. Values are in metres, square metres, litres, kilograms or items.

<details>
<summary>Length (123)</summary>

| Unit | ID | Also accepts | System | Value (m) |
|---|---|---|---|---|
| Metre | `metre` | meter, m | Metric (SI) | 1 |
| Kilometre | `kilometre` | km | Metric (SI) | 1,000 |
| Ångström | `angstrom` | angstrom, Å | Metric (SI) | 1 × 10<sup>-10</sup> |
| Inch | `inch` | in, " | English / Imperial / US customary | 0.0,254 |
| Foot | `foot` | ft, ', feet | English / Imperial / US customary | 0.3,048 |
| Yard | `yard` | yd | English / Imperial / US customary | 0.9,144 |
| Mile (statute) | `mile` | mi, statute mile | English / Imperial / US customary | 1609.34 |
| Furlong | `furlong` |  | English / Imperial / US customary | 201.168 |
| Chain (Gunter's) | `chain` |  | English / Imperial / US customary | 20.1,168 |
| Link | `link` |  | English / Imperial / US customary | 0.201,168 |
| Rod / pole / perch | `rod` | pole, perch, rood (length) | English / Imperial / US customary | 5.0,292 |
| Fathom | `fathom` |  | English / Imperial / US customary | 1.8,288 |
| Hand | `hand` |  | English / Imperial / US customary | 0.1,016 |
| Span | `span` |  | English / Imperial / US customary | 0.2,286 |
| Nail (cloth) | `nail` |  | English / Imperial / US customary | 0.05,715 |
| Barleycorn | `barleycorn` |  | English / Imperial / US customary | 0.00,846,667 |
| Line | `line` |  | English / Imperial / US customary | 0.00,211,667 |
| Thou / mil | `thou` | mil | English / Imperial / US customary | 2.54 × 10<sup>-5</sup> |
| Point (typographic) | `point_dtp` |  | English / Imperial / US customary | 3.528 × 10<sup>-4</sup> |
| Pica | `pica` |  | English / Imperial / US customary | 0.00,423,333 |
| Cubit (English) | `cubit_en` |  | English / Imperial / US customary | 0.4,572 |
| Ell (English) | `ell_en` |  | English / Imperial / US customary | 1.143 |
| League (land) | `league` |  | English / Imperial / US customary | 4828.03 |
| Nautical mile | `nautical_mile` | nmi, sea mile | Nautical | 1,852 |
| Admiralty mile | `admiralty_mile` |  | Nautical | 1853.18 |
| Cable (Royal Navy) | `cable_rn` | cable length | Nautical | 185.318 |
| Cable (US Navy) | `cable_us` |  | Nautical | 219.456 |
| League (marine) | `league_marine` |  | Nautical | 5,556 |
| US survey foot | `survey_foot` |  | English / Imperial / US customary | 0.304,801 |
| Ell (Scots) | `ell_scots` |  | Scottish | ≈ 0.941 |
| Fall (Scots) | `fall_scots` |  | Scottish | ≈ 5.646 |
| Mile (Scots) | `mile_scots` |  | Scottish | ≈ 1806.72 |
| Perch (Irish) | `perch_irish` |  | Irish | 6.4,008 |
| Mile (Irish) | `mile_irish` |  | Irish | 2048.26 |
| Pes (Roman foot) | `pes` | Roman foot | Ancient Roman | ≈ 0.296 |
| Digitus | `digitus` |  | Ancient Roman | ≈ 0.0,185 |
| Uncia (Roman inch) | `uncia_len` |  | Ancient Roman | ≈ 0.0,246,667 |
| Palmus | `palmus` |  | Ancient Roman | ≈ 0.074 |
| Cubitus | `cubitus` |  | Ancient Roman | ≈ 0.444 |
| Gradus (step) | `gradus` |  | Ancient Roman | ≈ 0.74 |
| Passus (pace) | `passus` |  | Ancient Roman | ≈ 1.48 |
| Actus | `actus` |  | Ancient Roman | ≈ 35.52 |
| Stadium (Roman) | `stadium_rom` |  | Ancient Roman | ≈ 185 |
| Roman mile (mille passus) | `mille_passus` | mille passuum, Roman mile | Ancient Roman | ≈ 1,480 |
| Leuga (Gallic league) | `leuga` |  | Ancient Roman | ≈ 2,220 |
| Pous (Greek foot) | `pous` |  | Ancient Greek | ≈ 0.308 |
| Daktylos | `daktylos` |  | Ancient Greek | ≈ 0.01,925 |
| Pechys (Greek cubit) | `pechys` |  | Ancient Greek | ≈ 0.462 |
| Orguia (Greek fathom) | `orguia` |  | Ancient Greek | ≈ 1.848 |
| Plethron | `plethron` |  | Ancient Greek | ≈ 30.8 |
| Stadion | `stadion` | stade, furlong (KJV) | Ancient Greek | ≈ 184.8 |
| Parasang | `parasang` | farsakh, fersah, farsang | Ancient Persian | ≈ 5,600 |
| Royal cubit (meh niswt) | `royal_cubit` |  | Ancient Egyptian | ≈ 0.5,236 |
| Palm (shesep) | `egypt_palm` |  | Ancient Egyptian | ≈ 0.0,748 |
| Digit (djeba) | `egypt_digit` |  | Ancient Egyptian | ≈ 0.0,187 |
| Khet | `khet` |  | Ancient Egyptian | ≈ 52.36 |
| Iteru (river measure) | `iteru` |  | Ancient Egyptian | ≈ 10,472 |
| Kuš (Mesopotamian cubit) | `kus` |  | Mesopotamian | ≈ 0.497 |
| Cubit (biblical, common) | `cubit_bib` | ammah, amah | Biblical / Talmudic | ≈ 0.457 |
| Cubit (long / royal, Ezekiel) | `cubit_bib_long` |  | Biblical / Talmudic | ≈ 0.523 |
| Span (zeret) | `span_bib` |  | Biblical / Talmudic | ≈ 0.2,285 |
| Handbreadth (tefah) | `handbreadth` |  | Biblical / Talmudic | ≈ 0.0,761,667 |
| Finger (etzba) | `finger_bib` |  | Biblical / Talmudic | ≈ 0.0,190,417 |
| Reed (qaneh) | `reed` |  | Biblical / Talmudic | ≈ 2.742 |
| Sabbath day's journey | `sabbath_journey` |  | Biblical / Talmudic | ≈ 914 |
| Pied du roi (French foot) | `pied_du_roi` | pied, Paris foot | French (pre-metric) | ≈ 0.324,839 |
| Pouce (French inch) | `pouce` |  | French (pre-metric) | ≈ 0.0,270,699 |
| Ligne | `ligne` |  | French (pre-metric) | ≈ 0.00,225,583 |
| Toise | `toise` |  | French (pre-metric) | ≈ 1.94,903 |
| Perche (de Paris) | `perche_paris` |  | French (pre-metric) | ≈ 5.8,471 |
| Arpent (length) | `arpent_len` |  | French (pre-metric) | ≈ 58.471 |
| Aune (de Paris) | `aune` | French ell | French (pre-metric) | ≈ 1.188 |
| Lieue de poste | `lieue_poste` |  | French (pre-metric) | ≈ 3898.07 |
| Lieue commune (1/25°) | `lieue_commune` |  | French (pre-metric) | ≈ 4444.44 |
| Rheinfuß (Prussian foot) | `rheinfuss` | Rhineland foot, Fuß | German (pre-metric) | ≈ 0.31,385 |
| Rute (Prussian) | `rute_pr` |  | German (pre-metric) | ≈ 3.7,662 |
| Meile (Prussian mile) | `meile_pr` |  | German (pre-metric) | ≈ 7532.4 |
| Elle (Prussian) | `elle_pr` |  | German (pre-metric) | ≈ 0.66,694 |
| Fuß (Viennese) | `fuss_wien` |  | German (pre-metric) | ≈ 0.316,081 |
| Klafter (Viennese) | `klafter` |  | German (pre-metric) | ≈ 1.89,649 |
| Meile (Austrian post mile) | `meile_at` |  | German (pre-metric) | ≈ 7585.94 |
| Geographic mile (German) | `geo_mile` |  | German (pre-metric) | ≈ 7420.4 |
| Arshin | `arshin` |  | Russian (pre-1924) | 0.7,112 |
| Vershok | `vershok` |  | Russian (pre-1924) | 0.04,445 |
| Sazhen | `sazhen` |  | Russian (pre-1924) | 2.1,336 |
| Verst | `verst` | versta | Russian (pre-1924) | 1066.8 |
| Vara (de Burgos) | `vara` |  | Spanish customary | ≈ 0.835,905 |
| Pie (Castilian foot) | `pie_es` |  | Spanish customary | ≈ 0.278,635 |
| Legua (legal) | `legua_es` |  | Spanish customary | ≈ 4179.52 |
| Arşın (architect's) | `arsin` |  | Ottoman | ≈ 0.758 |
| Shaku | `shaku` |  | Japanese | 0.30,303 |
| Sun | `sun` |  | Japanese | 0.030,303 |
| Ken | `ken` |  | Japanese | 1.81,818 |
| Jō | `jo` |  | Japanese | 3.0,303 |
| Chō (length) | `cho_len` |  | Japanese | 109.091 |
| Ri (Japanese) | `ri_jp` |  | Japanese | 3927.27 |
| Chi (Qing) | `chi_qing` |  | Chinese | ≈ 0.32 |
| Cun (Qing) | `cun_qing` |  | Chinese | ≈ 0.032 |
| Zhang (Qing) | `zhang_qing` |  | Chinese | ≈ 3.2 |
| Li (Qing) | `li_qing` |  | Chinese | ≈ 576 |
| Chi (shì, modern) | `chi_shi` |  | Chinese | 0.333,333 |
| Li (shì, modern) | `li_shi` |  | Chinese | 500 |
| Gaz (Ilahi, Mughal) | `gaz_ilahi` |  | Indian | ≈ 0.83 |
| Gaz (British India) | `gaz_brit` |  | Indian | 0.9,144 |
| Hath (Indian cubit) | `hath` |  | Indian | 0.4,572 |
| Kos (koss) | `kos` |  | Indian | ≈ 3,200 |
| Astronomical unit | `au` | AU, ua | Astronomical | 1.496 × 10<sup>11</sup> |
| Light-year | `light_year` | ly, lightyear | Astronomical | 9.461 × 10<sup>15</sup> |
| Parsec | `parsec` | pc | Astronomical | 3.086 × 10<sup>16</sup> |
| Kiloparsec | `kiloparsec` | kpc | Astronomical | 3.086 × 10<sup>19</sup> |
| Megaparsec | `megaparsec` | Mpc | Astronomical | 3.086 × 10<sup>22</sup> |
| Planck length | `planck_length` | lP | Planck (natural units) | ≈ 1.616 × 10<sup>-35</sup> |
| Smoot | `smoot` |  | Novelty | 1.7,018 |
| Drurr | `drurr` |  | Lilliputian (fictional) | ≈ 0.00,181,429 |
| Glumgluff | `glumgluff` |  | Lilliputian (fictional) | ≈ 0.0,261,257 |
| Blustrug | `blustrug` |  | Lilliputian (fictional) | ≈ 3.86,243 |
| Ranga (full pace) | `ranga` | rangar, Numenorean pace | Númenórean (fictional) | ≈ 0.9,652 |
| Man-high | `man_high` |  | Númenórean (fictional) | ≈ 1.9,304 |
| Lár (Númenórean league) | `lar` | lar, lárar | Númenórean (fictional) | ≈ 4,826 |
| 'uj | `uj` | uj, ujmey | Klingon (fictional) | ≈ 0.35 |
| 'uj'a' | `uj_a` | uj'a', uja | Klingon (fictional) | ≈ 3.15 |
| Kellicam (qelI'qam) | `kellicam` | qelI'qam, qeliqam, kellicams | Klingon (fictional) | ≈ 2,000 |
| Loghqam | `loghqam` |  | Klingon (fictional) | ≈ 1.183 × 10<sup>16</sup> |

</details>

<details>
<summary>Area (46)</summary>

| Unit | ID | Also accepts | System | Value (m²) |
|---|---|---|---|---|
| Square metre | `sq_metre` | m² | Metric (SI) | 1 |
| Are | `are` |  | Metric | 100 |
| Hectare | `hectare` | ha | Metric | 10,000 |
| Square foot | `sq_foot` | sq ft, ft² | English / Imperial / US customary | 0.092,903 |
| Square yard | `sq_yard` |  | English / Imperial / US customary | 0.836,127 |
| Square rod / perch | `sq_rod` | perch (area), pole (area) | English / Imperial / US customary | 25.2,929 |
| Rood | `rood` |  | English / Imperial / US customary | 1011.71 |
| Acre | `acre` |  | English / Imperial / US customary | 4046.86 |
| Square (roofing) | `square_roof` |  | English / Imperial / US customary | 9.2,903 |
| Square mile | `sq_mile` |  | English / Imperial / US customary | 2.59 × 10<sup>6</sup> |
| Section | `section` |  | English / Imperial / US customary | 2.59 × 10<sup>6</sup> |
| Quarter section | `quarter_section` |  | English / Imperial / US customary | 647,497 |
| Township (survey) | `township` |  | English / Imperial / US customary | 9.324 × 10<sup>7</sup> |
| Hide | `hide` |  | Anglo-Saxon / medieval English | ≈ 485,623 |
| Carucate / ploughland | `carucate` |  | Anglo-Saxon / medieval English | ≈ 485,623 |
| Virgate / yardland | `virgate` |  | Medieval English | ≈ 121,406 |
| Oxgang / bovate | `oxgang` |  | Medieval English | ≈ 60702.8 |
| Acre (Scots) | `acre_scots` |  | Scottish | ≈ 5,067 |
| Acre (Irish / plantation) | `acre_irish` |  | Irish | 6555.24 |
| Square perch (Irish) | `sq_perch_irish` |  | Irish | 40.9,702 |
| Jugerum | `jugerum` | iugerum | Ancient Roman | ≈ 2523.34 |
| Square pes | `sq_pes` |  | Ancient Roman | ≈ 0.087,616 |
| Heredium | `heredium` |  | Ancient Roman | ≈ 5046.68 |
| Centuria (land) | `centuria` |  | Ancient Roman | ≈ 504,668 |
| Plethron (area) | `plethron_sq` |  | Ancient Greek | ≈ 948.64 |
| Setat / aroura | `setat` | aroura, arura | Ancient Egyptian | ≈ 2741.57 |
| Arpent (de Paris) | `arpent` |  | French (pre-metric) | ≈ 3418.86 |
| Arpent d'ordonnance (des eaux et forêts) | `arpent_ordonnance` |  | French (pre-metric) | ≈ 5107.2 |
| Morgen (Prussian) | `morgen_pr` |  | German (pre-metric) | ≈ 2553.22 |
| Morgen (Dutch / Rhineland) | `morgen_nl` |  | Dutch | ≈ 8,516 |
| Joch (Austrian) | `joch` | Katastraljoch, hold (Hungarian) | German (pre-metric) | ≈ 5754.64 |
| Desyatina | `desyatina` |  | Russian (pre-1924) | 10925.4 |
| Square sazhen | `sq_sazhen` |  | Russian (pre-1924) | 4.55,225 |
| Fanega (land, Castile) | `fanega_land` |  | Spanish customary | ≈ 6439.6 |
| Tsubo | `tsubo` |  | Japanese | 3.30,579 |
| Se | `se` |  | Japanese | 99.1,736 |
| Tan | `tan` |  | Japanese | 991.736 |
| Chō (area) | `cho_area` |  | Japanese | 9917.36 |
| Mu (Qing) | `mu_qing` |  | Chinese | ≈ 614.4 |
| Square chi (Qing) | `sq_chi_qing` |  | Chinese | ≈ 0.1,024 |
| Mu (shì, modern) | `mu_shi` | mou | Chinese | 666.667 |
| Qing (area) | `qing_area` |  | Chinese | 66666.7 |
| Dönüm (Ottoman) | `donum` | dunam, dunum, donum | Ottoman | ≈ 919.3 |
| Dunam (metric) | `dunam_metric` |  | Metric-derived | 1,000 |
| Bigha | `bigha` |  | Indian | ≈ 1337.8 |
| Planck area | `planck_area` |  | Planck (natural units) | ≈ 2.612 × 10<sup>-70</sup> |

</details>

<details>
<summary>Volume (97)</summary>

| Unit | ID | Also accepts | System | Value (L) |
|---|---|---|---|---|
| Litre | `litre` | liter, L | Metric | 1 |
| Cubic inch | `cu_inch` |  | English / Imperial / US customary | 0.0,163,871 |
| Cubic foot | `cu_foot` |  | English / Imperial / US customary | 28.3,168 |
| Gallon (US / wine / Queen Anne) | `gal_us` | wine gallon, Queen Anne gallon | English / Imperial / US customary | 3.78,541 |
| Quart (US liquid) | `qt_us` |  | English / Imperial / US customary | 0.946,353 |
| Pint (US liquid) | `pt_us` |  | English / Imperial / US customary | 0.473,176 |
| Cup (US) | `cup_us` |  | English / Imperial / US customary | 0.236,588 |
| Gill (US) | `gill_us` |  | English / Imperial / US customary | 0.118,294 |
| Fluid ounce (US) | `floz_us` |  | English / Imperial / US customary | 0.0,295,735 |
| Tablespoon (US) | `tbsp_us` |  | English / Imperial / US customary | 0.0,147,868 |
| Teaspoon (US) | `tsp_us` |  | English / Imperial / US customary | 0.00,492,892 |
| Barrel (petroleum) | `barrel_oil` | bbl | English / Imperial / US customary | 158.987 |
| Tun (wine) | `tun` |  | English / Imperial / US customary | 953.924 |
| Pipe / butt (wine) | `pipe` | butt | English / Imperial / US customary | 476.962 |
| Puncheon (wine) | `puncheon` |  | English / Imperial / US customary | 317.975 |
| Hogshead (wine) | `hogshead_wine` |  | English / Imperial / US customary | 238.481 |
| Tierce | `tierce` |  | English / Imperial / US customary | 158.987 |
| Barrel (wine) | `barrel_wine` |  | English / Imperial / US customary | 119.24 |
| Rundlet | `rundlet` |  | English / Imperial / US customary | 68.1,374 |
| Gallon (ale, pre-1824) | `gal_ale` |  | English / Imperial / US customary | 4.62,115 |
| Gallon (imperial) | `gal_imp` |  | English / Imperial / US customary | 4.54,609 |
| Quart (imperial) | `qt_imp` |  | English / Imperial / US customary | 1.13,652 |
| Pint (imperial) | `pt_imp` |  | English / Imperial / US customary | 0.568,261 |
| Gill (imperial) | `gill_imp` |  | English / Imperial / US customary | 0.142,065 |
| Fluid ounce (imperial) | `floz_imp` |  | English / Imperial / US customary | 0.0,284,131 |
| Fluid drachm (imperial) | `fldr_imp` | fluid dram | English / Imperial / US customary | 0.00,355,163 |
| Minim (imperial) | `minim_imp` |  | English / Imperial / US customary | 5.919 × 10<sup>-5</sup> |
| Barrel (beer, imperial) | `barrel_beer` |  | English / Imperial / US customary | 163.659 |
| Hogshead (beer) | `hogshead_beer` |  | English / Imperial / US customary | 245.489 |
| Kilderkin | `kilderkin` |  | English / Imperial / US customary | 81.8,296 |
| Firkin (beer) | `firkin` |  | English / Imperial / US customary | 40.9,148 |
| Pin | `pin` |  | English / Imperial / US customary | 20.4,574 |
| Bushel (Winchester / US) | `bu_us` |  | English / Imperial / US customary | 35.2,391 |
| Peck (US) | `pk_us` |  | English / Imperial / US customary | 8.80,977 |
| Gallon (US dry) | `galdry_us` |  | English / Imperial / US customary | 4.40,488 |
| Quart (US dry) | `qtdry_us` |  | English / Imperial / US customary | 1.10,122 |
| Bushel (imperial) | `bu_imp` |  | English / Imperial / US customary | 36.3,687 |
| Peck (imperial) | `pk_imp` |  | English / Imperial / US customary | 9.09,218 |
| Quarter (grain) | `quarter_vol` |  | English / Imperial / US customary | 290.95 |
| Chaldron (coal) | `chaldron` |  | English / Imperial / US customary | 1309.27 |
| Pint (Scots) | `pint_scots` | joug | Scottish | ≈ 1.696 |
| Boll (Scots, wheat) | `boll` |  | Scottish | ≈ 145.4 |
| Firlot (Scots, wheat) | `firlot` |  | Scottish | ≈ 36.35 |
| Amphora (quadrantal) | `amphora_rom` |  | Ancient Roman | ≈ 25.9,343 |
| Culleus | `culleus` |  | Ancient Roman | ≈ 518.687 |
| Congius | `congius` |  | Ancient Roman | ≈ 3.24,179 |
| Sextarius | `sextarius` |  | Ancient Roman | ≈ 0.540,299 |
| Hemina | `hemina` |  | Ancient Roman | ≈ 0.270,149 |
| Cyathus | `cyathus` |  | Ancient Roman | ≈ 0.0,450,249 |
| Modius | `modius` |  | Ancient Roman | ≈ 8.64,478 |
| Metretes (Attic) | `metretes` | amphora (Greek) | Ancient Greek | ≈ 39.4 |
| Chous | `chous` |  | Ancient Greek | ≈ 3.28,333 |
| Kotyle | `kotyle` |  | Ancient Greek | ≈ 0.273,611 |
| Kyathos | `kyathos` |  | Ancient Greek | ≈ 0.0,456,019 |
| Medimnos (Attic) | `medimnos` |  | Ancient Greek | ≈ 52.5 |
| Choinix | `choinix` |  | Ancient Greek | ≈ 1.09,375 |
| Bath | `bath` |  | Biblical / Talmudic | ≈ 22 |
| Ephah | `ephah` |  | Biblical / Talmudic | ≈ 22 |
| Homer / kor | `homer` | kor, cor | Biblical / Talmudic | ≈ 220 |
| Seah | `seah` | measure (KJV) | Biblical / Talmudic | ≈ 7.33,333 |
| Omer | `omer` |  | Biblical / Talmudic | ≈ 2.2 |
| Kab / cab | `kab` |  | Biblical / Talmudic | ≈ 1.22,222 |
| Hin | `hin` |  | Biblical / Talmudic | ≈ 3.66,667 |
| Log | `log` |  | Biblical / Talmudic | ≈ 0.305,556 |
| Pinte (de Paris) | `pinte` |  | French (pre-metric) | ≈ 0.931,389 |
| Chopine | `chopine` |  | French (pre-metric) | ≈ 0.465,695 |
| Velte | `velte` |  | French (pre-metric) | ≈ 7.45,111 |
| Muid (wine, Paris) | `muid_vin` |  | French (pre-metric) | ≈ 268.24 |
| Boisseau (de Paris) | `boisseau` |  | French (pre-metric) | ≈ 13.008 |
| Minot | `minot` |  | French (pre-metric) | ≈ 39.024 |
| Setier (grain, Paris) | `setier` |  | French (pre-metric) | ≈ 156.096 |
| Muid (grain, Paris) | `muid_grain` |  | French (pre-metric) | ≈ 1873.15 |
| Quart (Prussian) | `quart_pr` |  | German (pre-metric) | ≈ 1.145 |
| Eimer (Prussian) | `eimer_pr` |  | German (pre-metric) | ≈ 68.7 |
| Scheffel (Prussian) | `scheffel_pr` |  | German (pre-metric) | ≈ 54.96 |
| Maß (Austrian) | `mass_at` | Mass | German (pre-metric) | ≈ 1.415 |
| Maß (Bavarian) | `mass_by` |  | German (pre-metric) | ≈ 1.069 |
| Vedro | `vedro` |  | Russian (pre-1924) | ≈ 12.2,994 |
| Shtof | `shtof` |  | Russian (pre-1924) | ≈ 1.22,994 |
| Charka | `charka` |  | Russian (pre-1924) | ≈ 0.122,994 |
| Bochka | `bochka` |  | Russian (pre-1924) | ≈ 491.976 |
| Chetvert (dry) | `chetvert` |  | Russian (pre-1924) | ≈ 209.91 |
| Chetverik | `chetverik` |  | Russian (pre-1924) | ≈ 26.2,387 |
| Fanega (dry, Castile) | `fanega` |  | Spanish customary | ≈ 55.5 |
| Celemín | `celemin` |  | Spanish customary | ≈ 4.625 |
| Cántara / arroba (wine) | `cantara` |  | Spanish customary | ≈ 16.133 |
| Azumbre | `azumbre` |  | Spanish customary | ≈ 2.01,662 |
| Kile (Istanbul) | `kile` |  | Ottoman | ≈ 37 |
| Koku | `koku` |  | Japanese | 180.391 |
| To | `to_jp` |  | Japanese | 18.0,391 |
| Shō | `sho` |  | Japanese | 1.80,391 |
| Gō | `go` |  | Japanese | 0.180,391 |
| Sheng (Qing) | `sheng_qing` |  | Chinese | ≈ 1.0,355 |
| Dou (Qing) | `dou_qing` | peck (Chinese) | Chinese | ≈ 10.355 |
| Shi / dan (volume, Qing) | `shi_vol` |  | Chinese | ≈ 103.55 |
| Planck volume | `planck_volume` |  | Planck (natural units) | ≈ 4.222 × 10<sup>-102</sup> |
| Tlho'ren | `tlhoren` | tlho'ren | Klingon (fictional) | ≈ 1 |

</details>

<details>
<summary>Mass (87)</summary>

| Unit | ID | Also accepts | System | Value (kg) |
|---|---|---|---|---|
| Kilogram | `kilogram` | kg | Metric (SI) | 1 |
| Pound (avoirdupois) | `lb` | lb, pound | English / Imperial / US customary | 0.453,592 |
| Ounce (avoirdupois) | `oz` | oz | English / Imperial / US customary | 0.0,283,495 |
| Dram (avoirdupois) | `dram_avdp` | dr | English / Imperial / US customary | 0.00,177,185 |
| Grain | `grain` | gr | English / Imperial / US customary | 6.48 × 10<sup>-5</sup> |
| Stone | `stone` | st | English / Imperial / US customary | 6.35,029 |
| Quarter (weight) | `quarter_mass` |  | English / Imperial / US customary | 12.7,006 |
| Hundredweight (long) | `cwt_long` | cwt | English / Imperial / US customary | 50.8,023 |
| Hundredweight (short) | `cwt_short` |  | English / Imperial / US customary | 45.3,592 |
| Ton (long) | `ton_long` | imperial ton | English / Imperial / US customary | 1016.05 |
| Ton (short) | `ton_short` |  | English / Imperial / US customary | 907.185 |
| Tonne (metric ton) | `tonne` |  | Metric | 1,000 |
| Clove (wool) | `clove` |  | English / Imperial / US customary | 3.17,515 |
| Tod (wool) | `tod` |  | English / Imperial / US customary | 12.7,006 |
| Sack (wool) | `sack_wool` |  | English / Imperial / US customary | 165.108 |
| Pound (troy) | `lb_troy` |  | English / Imperial / US customary | 0.373,242 |
| Ounce (troy) | `oz_troy` | ozt | English / Imperial / US customary | 0.0,311,035 |
| Pennyweight | `dwt` | dwt | English / Imperial / US customary | 0.00,155,517 |
| Tower pound | `lb_tower` |  | English / Imperial / US customary | 0.349,914 |
| Merchants' pound | `lb_merchant` |  | English / Imperial / US customary | 0.437,393 |
| Scruple (apothecaries') | `scruple` |  | English / Imperial / US customary | 0.00,129,598 |
| Drachm (apothecaries') | `drachm_ap` | dram (apothecaries') | English / Imperial / US customary | 0.00,388,793 |
| Carat (metric) | `carat` | ct | Metric | 2 × 10<sup>-4</sup> |
| Pound (Scots troy) | `lb_scots_troy` |  | Scottish | ≈ 0.4,944 |
| Tron pound (Scots) | `lb_tron` |  | Scottish | ≈ 0.6 |
| Livre (poids de marc) | `livre_poids` |  | French (pre-metric) | ≈ 0.489,506 |
| Marc (French) | `marc_fr` |  | French (pre-metric) | ≈ 0.244,753 |
| Once (French) | `once_fr` |  | French (pre-metric) | ≈ 0.0,305,941 |
| Gros | `gros_fr` |  | French (pre-metric) | ≈ 0.00,382,426 |
| Grain (French) | `grain_fr` |  | French (pre-metric) | ≈ 5.311 × 10<sup>-5</sup> |
| Quintal (French, old) | `quintal_fr` |  | French (pre-metric) | ≈ 48.9,506 |
| Cologne mark | `cologne_mark` |  | German (pre-metric) | ≈ 0.233,856 |
| Pfund (Prussian, 1816) | `pfund_pr` |  | German (pre-metric) | ≈ 0.467,711 |
| Lot (Prussian) | `lot_pr` |  | German (pre-metric) | ≈ 0.014,616 |
| Zollpfund | `zollpfund` |  | German (pre-metric) | 0.5 |
| Zentner | `zentner` | hundredweight (German) | German (pre-metric) | 50 |
| Pfund (Viennese) | `pfund_wien` |  | German (pre-metric) | ≈ 0.56,006 |
| Funt | `funt` | Russian pound | Russian (pre-1924) | ≈ 0.409,512 |
| Pud | `pud` | pood | Russian (pre-1924) | ≈ 16.3,805 |
| Berkovets | `berkovets` |  | Russian (pre-1924) | ≈ 163.805 |
| Lot (Russian) | `lot_ru` |  | Russian (pre-1924) | ≈ 0.0,127,973 |
| Zolotnik | `zolotnik` |  | Russian (pre-1924) | ≈ 0.00,426,575 |
| Dolya | `dolya` |  | Russian (pre-1924) | ≈ 4.443 × 10<sup>-5</sup> |
| Libra (Castilian) | `libra_es` |  | Spanish customary | ≈ 0.4,601 |
| Onza | `onza_es` |  | Spanish customary | ≈ 0.0,287,563 |
| Arroba (Castilian) | `arroba_es` |  | Spanish customary | ≈ 11.5,025 |
| Quintal (Castilian) | `quintal_es` |  | Spanish customary | ≈ 46.01 |
| Arrátel | `arratel` |  | Portuguese customary | ≈ 0.459 |
| Arroba (Portuguese) | `arroba_pt` |  | Portuguese customary | ≈ 14.688 |
| Okka / oka | `okka` | oke, oka | Ottoman | ≈ 1.2,829 |
| Dirhem | `dirhem` |  | Ottoman | ≈ 0.00,320,725 |
| Kantar / qintar | `kantar` |  | Ottoman | ≈ 56.4,476 |
| Monme | `monme` |  | Japanese | 0.00,375 |
| Kin | `kin` | catty (Japanese) | Japanese | 0.6 |
| Kan / kanme | `kan` |  | Japanese | 3.75 |
| Liang / tael (Qing) | `liang_qing` | tael | Chinese | ≈ 0.0,373 |
| Qian / mace (Qing) | `qian_qing` |  | Chinese | ≈ 0.00,373 |
| Jin / catty (Qing) | `jin_qing` | catty | Chinese | ≈ 0.5,968 |
| Dan / picul | `picul` |  | Chinese | ≈ 59.68 |
| Catty (Hong Kong legal) | `catty_hk` |  | Chinese | 0.60,479 |
| Jin (shì, modern) | `jin_shi` |  | Chinese | 0.5 |
| Tola | `tola` |  | Indian | 0.0,116,638 |
| Ratti | `ratti` |  | Indian | 1.215 × 10<sup>-4</sup> |
| Seer | `seer` |  | Indian | 0.933,104 |
| Maund (Indian government) | `maund` | mun | Indian | 37.3,242 |
| Maund (Bengal factory) | `maund_bengal` |  | Indian | ≈ 33.8,688 |
| Libra (Roman pound) | `libra_rom` |  | Ancient Roman | ≈ 0.3,275 |
| Uncia (Roman ounce) | `uncia_mass` |  | Ancient Roman | ≈ 0.0,272,917 |
| Scripulum | `scripulum` |  | Ancient Roman | ≈ 0.00,113,715 |
| Siliqua | `siliqua` |  | Ancient Roman | ≈ 1.895 × 10<sup>-4</sup> |
| Mina (Attic) | `mina_att` |  | Ancient Greek | ≈ 0.431 |
| Drachma (weight) | `drachma_mass` |  | Ancient Greek | ≈ 0.00,431 |
| Obol (weight) | `obol_mass` |  | Ancient Greek | ≈ 7.183 × 10<sup>-4</sup> |
| Talent (Attic) | `talent_att` |  | Ancient Greek | ≈ 25.86 |
| Shekel (biblical) | `shekel_bib` |  | Biblical / Talmudic | ≈ 0.0,114 |
| Gerah | `gerah` |  | Biblical / Talmudic | ≈ 5.7 × 10<sup>-4</sup> |
| Beka | `beka` |  | Biblical / Talmudic | ≈ 0.0,057 |
| Mina / maneh (biblical) | `mina_bib` |  | Biblical / Talmudic | ≈ 0.57 |
| Talent / kikkar (biblical) | `talent_bib` |  | Biblical / Talmudic | ≈ 34.2 |
| Shekel (Mesopotamian) | `shekel_meso` |  | Mesopotamian | ≈ 0.00,833 |
| Še (grain) | `se_grain` |  | Mesopotamian | ≈ 4.628 × 10<sup>-5</sup> |
| Mina (Mesopotamian) | `mina_meso` |  | Mesopotamian | ≈ 0.4,998 |
| Talent (Mesopotamian) | `talent_meso` |  | Mesopotamian | ≈ 29.988 |
| Deben (New Kingdom) | `deben` |  | Ancient Egyptian | ≈ 0.091 |
| Kite / qedet | `kite` |  | Ancient Egyptian | ≈ 0.0,091 |
| Planck mass | `planck_mass` | mP | Planck (natural units) | ≈ 2.176 × 10<sup>-8</sup> |
| Cheb | `cheb` |  | Klingon (fictional) | ≈ 2.25 |

</details>

<details>
<summary>Count (11)</summary>

| Unit | ID | Also accepts | System | Value (each) |
|---|---|---|---|---|
| Each (unit) | `each` |  | Counting | 1 |
| Dozen | `dozen` |  | Counting | 12 |
| Baker's dozen | `bakers_dozen` | long dozen | Counting | 13 |
| Score | `score` |  | Counting | 20 |
| Long hundred / great hundred | `long_hundred` |  | Counting | 120 |
| Gross | `gross` |  | Counting | 144 |
| Great gross | `great_gross` |  | Counting | 1,728 |
| Quire (old) | `quire_old` |  | Counting | 24 |
| Ream (old) | `ream_old` |  | Counting | 480 |
| Quire (modern) | `quire` |  | Counting | 25 |
| Ream (modern) | `ream` |  | Counting | 500 |

</details>
