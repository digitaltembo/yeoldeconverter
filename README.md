# Ye Olde Converter

Makes sense of the money and measures, inspired by that feeling of adriftness you get when a book mentions an unfamiliar currency. It converts:

- **Money:** 38 historical currencies, from the Roman denarius to the Deutsche Mark, into 2025 US dollars for a given year, or into one another. It reads sums as books write them (`£3 4s 6d`, `2 guineas`, `30 denarii`) and explains coins ("what's a florin?"). It also includes fictional money: D&D, Westeros, Star Wars, Star Trek, Discworld and Hitchhiker's.
- **Measures:** 357 units of length, area, volume, mass and count, including English, French, German, Russian, Japanese, Chinese, Indian, Roman, Greek, biblical, astronomical and fictional units.

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

Exchange rates come from downloaded datasets: MeasuringWorth (dollar exchange rates and the gold/silver price ratio), the Federal Reserve via FRED, the Bank of England, the Jordà–Schularick–Taylor Macrohistory Database and the Penn World Table. Coin standards and parities are quoted from Wikipedia. Where neither exists, values are estimates based on monetary histories (Spooner, Pamuk, Gemmill & Mayhew, Scheidel). Fictional rates come from the works themselves or their official and fan references.

Each data point is labelled by the weakest number behind it:
- `dataset`: every exchange rate and price index was read from a downloaded dataset.
- `quoted`: it also uses a parity, coin standard or rate quoted from the cited source. The source's `quote` field holds the text.
- `estimate`: at least one number is neither, such as an interpolation between known standards. All ancient, Edo-period and fictional values are estimates.

**Units.** Values are based on statutes and standards (the 1959 international yard and pound, the UK Weights and Measures Act 1985, NIST, BIPM, the IAU and CODATA), and on reference articles for historical units. Each unit is defined in terms of another, so conversions stay consistent with each other. Every unit not defined purely from others (such as a square foot) has at least one source with a `quote`: text from the cited page that states its value, its relation to another unit, or its range. A unit is given a low–high range only where a quoted source states both ends.

`scripts/check_quotes.py` checks every quote, for both currencies and units, against saved copies of the cited pages. For a unit's quote, it also checks that the quote is near the unit's name on the page and that a number in it matches the unit's value, range or defining factor. The saved pages and downloaded datasets live in `sources/` (gitignored); `python3 -I scripts/check_quotes.py --fetch data/currencies.json data/units.json` downloads any that are missing.

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
| Canadian dollar | `cad` | 1860–2025 | Dollar, Toonie, Fifty-cent piece, Quarter, Dime, Nickel, Cent |
| Mexican peso (1863-1992) | `mxp` | 1865–1990 | Peso, Centavo, Real (colloquial), Tostón, Hidalgo (gold), Centenario (gold) |
| Mexican peso | `mxn` | 1995–2025 | Peso, Centavo, Old peso (1863-1992) |
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

Pass a unit's ID, name or an alias. Values are in metres, square metres, litres, kilograms or items. ≈ marks values that are not exact by definition.

<details>
<summary>Length (121)</summary>

| Unit | ID | Also accepts | System | Value (m) |
|---|---|---|---|---|
| Metre | `metre` | meter, m | Metric (SI) | 1 |
| Kilometre | `kilometre` | km | Metric (SI) | 1,000 |
| Ångström | `angstrom` | angstrom, Å, Å | Metric (SI) | 1 × 10<sup>-10</sup> |
| Inch | `inch` | in, " | English / Imperial / US customary | 0.0254 |
| Foot | `foot` | ft, ', feet | English / Imperial / US customary | 0.3048 |
| Yard | `yard` | yd | English / Imperial / US customary | 0.9144 |
| Mile (statute) | `mile` | mi, statute mile | English / Imperial / US customary | 1,609.34 |
| Furlong | `furlong` |  | English / Imperial / US customary | 201.168 |
| Chain (Gunter's) | `chain` |  | English / Imperial / US customary | 20.1168 |
| Link | `link` |  | English / Imperial / US customary | 0.201168 |
| Rod / pole / perch | `rod` | pole, perch, rood (length) | English / Imperial / US customary | 5.0292 |
| Fathom | `fathom` |  | English / Imperial / US customary | 1.8288 |
| Hand | `hand` |  | English / Imperial / US customary | 0.1016 |
| Span | `span` |  | English / Imperial / US customary | 0.2286 |
| Nail (cloth) | `nail` |  | English / Imperial / US customary | 0.05715 |
| Barleycorn | `barleycorn` |  | English / Imperial / US customary | 0.00846667 |
| Line | `line` |  | English / Imperial / US customary | 0.00211667 |
| Thou / mil | `thou` | mil | English / Imperial / US customary | 2.54 × 10<sup>-5</sup> |
| Point (typographic) | `point_dtp` |  | English / Imperial / US customary | 3.528 × 10<sup>-4</sup> |
| Pica | `pica` |  | English / Imperial / US customary | 0.00423333 |
| Cubit (English) | `cubit_en` |  | English / Imperial / US customary | 0.4572 |
| Ell (English) | `ell_en` |  | English / Imperial / US customary | 1.143 |
| League (land) | `league` |  | English / Imperial / US customary | 4,828.03 |
| Nautical mile | `nautical_mile` | nmi, sea mile | Nautical | 1,852 |
| Admiralty mile | `admiralty_mile` |  | Nautical | 1,853.18 |
| Cable (Royal Navy) | `cable_rn` | cable length | Nautical | 185.318 |
| Cable (US Navy) | `cable_us` |  | Nautical | 219.456 |
| US survey foot | `survey_foot` |  | English / Imperial / US customary | 0.304801 |
| Ell (Scots) | `ell_scots` |  | Scottish | ≈ 0.941 |
| Fall (Scots) | `fall_scots` |  | Scottish | ≈ 5.646 |
| Mile (Scots) | `mile_scots` |  | Scottish | ≈ 1,806.72 |
| Perch (Irish) | `perch_irish` |  | Irish | 6.4008 |
| Mile (Irish) | `mile_irish` |  | Irish | 2,048.26 |
| Pes (Roman foot) | `pes` | Roman foot | Ancient Roman | ≈ 0.296 |
| Digitus | `digitus` |  | Ancient Roman | ≈ 0.0185 |
| Uncia (Roman inch) | `uncia_len` |  | Ancient Roman | ≈ 0.0246667 |
| Palmus | `palmus` |  | Ancient Roman | ≈ 0.074 |
| Cubitus | `cubitus` | cubitum | Ancient Roman | ≈ 0.444 |
| Gradus (step) | `gradus` |  | Ancient Roman | ≈ 0.74 |
| Passus (pace) | `passus` |  | Ancient Roman | ≈ 1.48 |
| Actus | `actus` |  | Ancient Roman | ≈ 35.52 |
| Stadium (Roman) | `stadium_rom` |  | Ancient Roman | ≈ 185 |
| Roman mile (mille passus) | `mille_passus` | mille passuum, Roman mile | Ancient Roman | ≈ 1,480 |
| Leuga (Gallic league) | `leuga` |  | Ancient Roman | ≈ 2,220 |
| Pous (Greek foot) | `pous` |  | Ancient Greek | ≈ 0.308 |
| Daktylos | `daktylos` |  | Ancient Greek | ≈ 0.01925 |
| Pechys (Greek cubit) | `pechys` |  | Ancient Greek | ≈ 0.462 |
| Orguia (Greek fathom) | `orguia` |  | Ancient Greek | ≈ 1.848 |
| Plethron | `plethron` |  | Ancient Greek | ≈ 30.8 |
| Stadion | `stadion` | stade, furlong (KJV) | Ancient Greek | ≈ 184.8 |
| Parasang | `parasang` | farsakh, fersah, farsang | Ancient Persian | ≈ 5,700 |
| Royal cubit (meh niswt) | `royal_cubit` |  | Ancient Egyptian | ≈ 0.5236 |
| Palm (shesep) | `egypt_palm` |  | Ancient Egyptian | ≈ 0.0748 |
| Digit (djeba) | `egypt_digit` |  | Ancient Egyptian | ≈ 0.0187 |
| Khet | `khet` |  | Ancient Egyptian | ≈ 52.36 |
| Iteru (river measure) | `iteru` |  | Ancient Egyptian | ≈ 10,472 |
| Kuš (Mesopotamian cubit) | `kus` | Babylonian cubit | Mesopotamian | ≈ 0.495 |
| Cubit (biblical, common) | `cubit_bib` | ammah, amah | Biblical / Talmudic | ≈ 0.495 |
| Cubit (long / royal, Ezekiel) | `cubit_bib_long` |  | Biblical / Talmudic | ≈ 0.5775 |
| Span (zeret) | `span_bib` |  | Biblical / Talmudic | ≈ 0.2475 |
| Handbreadth (tefah) | `handbreadth` |  | Biblical / Talmudic | ≈ 0.0825 |
| Finger (etzba) | `finger_bib` |  | Biblical / Talmudic | ≈ 0.020625 |
| Sabbath day's journey | `sabbath_journey` | techum shabbat, Sabbath limit | Biblical / Talmudic | ≈ 990 |
| Pied du roi (French foot) | `pied_du_roi` | pied, Paris foot | French (pre-metric) | ≈ 0.324839 |
| Pouce (French inch) | `pouce` |  | French (pre-metric) | ≈ 0.0270699 |
| Ligne | `ligne` |  | French (pre-metric) | ≈ 0.00225583 |
| Toise | `toise` |  | French (pre-metric) | ≈ 1.94903 |
| Perche (de Paris) | `perche_paris` |  | French (pre-metric) | ≈ 5.8471 |
| Arpent (length) | `arpent_len` |  | French (pre-metric) | ≈ 58.471 |
| Aune (de Paris) | `aune` | French ell | French (pre-metric) | ≈ 1.188 |
| Lieue de poste | `lieue_poste` | lieue de Paris | French (pre-metric) | ≈ 3,898.07 |
| Lieue commune (1/25°) | `lieue_commune` |  | French (pre-metric) | ≈ 4,452.2 |
| Rheinfuß (Prussian foot) | `rheinfuss` | Rhineland foot, Fuß | German (pre-metric) | ≈ 0.31385 |
| Rute (Prussian) | `rute_pr` |  | German (pre-metric) | ≈ 3.7662 |
| Meile (Prussian mile) | `meile_pr` |  | German (pre-metric) | ≈ 7,532.4 |
| Elle (Prussian) | `elle_pr` |  | German (pre-metric) | ≈ 0.66694 |
| Fuß (Viennese) | `fuss_wien` |  | German (pre-metric) | ≈ 0.316081 |
| Klafter (Viennese) | `klafter` |  | German (pre-metric) | ≈ 1.89648 |
| Meile (Austrian post mile) | `meile_at` |  | German (pre-metric) | ≈ 7,585.94 |
| Geographic mile (German) | `geo_mile` |  | German (pre-metric) | ≈ 7,420.4 |
| Arshin | `arshin` |  | Russian (pre-1924) | 0.7112 |
| Vershok | `vershok` | vyershok | Russian (pre-1924) | 0.04445 |
| Sazhen | `sazhen` |  | Russian (pre-1924) | 2.1336 |
| Verst | `verst` | vyersta, versta | Russian (pre-1924) | 1,066.8 |
| Vara (de Burgos) | `vara` |  | Spanish customary | ≈ 0.835905 |
| Pie (Castilian foot) | `pie_es` |  | Spanish customary | ≈ 0.278635 |
| Legua (legal) | `legua_es` |  | Spanish customary | ≈ 4,179.52 |
| Arşın (architect's) | `arsin` |  | Ottoman | ≈ 0.758 |
| Shaku | `shaku` |  | Japanese | 0.30303 |
| Sun | `sun` |  | Japanese | 0.030303 |
| Ken | `ken` |  | Japanese | 1.81818 |
| Jō | `jo` |  | Japanese | 3.0303 |
| Chō (length) | `cho_len` |  | Japanese | 109.091 |
| Ri (Japanese) | `ri_jp` |  | Japanese | 3,927.27 |
| Chi (Qing) | `chi_qing` |  | Chinese | ≈ 0.32 |
| Cun (Qing) | `cun_qing` |  | Chinese | ≈ 0.032 |
| Zhang (Qing) | `zhang_qing` |  | Chinese | ≈ 3.2 |
| Li (Qing) | `li_qing` |  | Chinese | ≈ 576 |
| Chi (shì, modern) | `chi_shi` |  | Chinese | 0.333333 |
| Li (shì, modern) | `li_shi` |  | Chinese | 500 |
| Gaz (Ilahi, Mughal) | `gaz_ilahi` |  | Indian | ≈ 0.8382 |
| Gaz (British India) | `gaz_brit` |  | Indian | 0.9144 |
| Hath (Indian cubit) | `hath` |  | Indian | 0.4572 |
| Kos (koss) | `kos` |  | Indian | ≈ 3,200 |
| Astronomical unit | `au` | AU, ua | Astronomical | 1.496 × 10<sup>11</sup> |
| Light-year | `light_year` | ly, lightyear | Astronomical | 9.461 × 10<sup>15</sup> |
| Parsec | `parsec` | pc | Astronomical | 3.086 × 10<sup>16</sup> |
| Kiloparsec | `kiloparsec` | kpc | Astronomical | 3.086 × 10<sup>19</sup> |
| Megaparsec | `megaparsec` | Mpc | Astronomical | 3.086 × 10<sup>22</sup> |
| Planck length | `planck_length` | lP | Planck (natural units) | ≈ 1.616 × 10<sup>-35</sup> |
| Smoot | `smoot` |  | Novelty | 1.7018 |
| Drurr | `drurr` |  | Lilliputian (fictional) (fictional) | ≈ 0.00181429 |
| Glumgluff | `glumgluff` |  | Lilliputian (fictional) (fictional) | ≈ 0.0261257 |
| Blustrug | `blustrug` |  | Lilliputian (fictional) (fictional) | ≈ 3.86243 |
| Ranga (full pace) | `ranga` | rangar, Numenorean pace | Númenórean (fictional) (fictional) | ≈ 0.9652 |
| Man-high | `man_high` |  | Númenórean (fictional) (fictional) | ≈ 1.9304 |
| Lár (Númenórean league) | `lar` | lar, lárar | Númenórean (fictional) (fictional) | ≈ 4,826 |
| 'uj | `uj` | uj, ujmey | Klingon (fictional) (fictional) | ≈ 0.35 |
| 'uj'a' | `uj_a` | uj'a', uja | Klingon (fictional) (fictional) | ≈ 3.15 |
| Kellicam (qelI'qam) | `kellicam` | qelI'qam, qeliqam, kellicams | Klingon (fictional) (fictional) | ≈ 2,000 |
| Loghqam | `loghqam` |  | Klingon (fictional) (fictional) | ≈ 1.183 × 10<sup>16</sup> |

</details>

<details>
<summary>Area (45)</summary>

| Unit | ID | Also accepts | System | Value (m²) |
|---|---|---|---|---|
| Square metre | `sq_metre` | m² | Metric (SI) | 1 |
| Are | `are` |  | Metric | 100 |
| Hectare | `hectare` | ha | Metric | 10,000 |
| Square foot | `sq_foot` | sq ft, ft² | English / Imperial / US customary | 0.092903 |
| Square yard | `sq_yard` |  | English / Imperial / US customary | 0.836127 |
| Square rod / perch | `sq_rod` | perch (area), pole (area) | English / Imperial / US customary | 25.2929 |
| Rood | `rood` |  | English / Imperial / US customary | 1,011.71 |
| Acre | `acre` |  | English / Imperial / US customary | 4,046.86 |
| Square (roofing) | `square_roof` |  | English / Imperial / US customary | 9.2903 |
| Square mile | `sq_mile` |  | English / Imperial / US customary | 2.58999e+06 |
| Section | `section` |  | English / Imperial / US customary | 2.58999e+06 |
| Quarter section | `quarter_section` |  | English / Imperial / US customary | 647,497 |
| Township (survey) | `township` |  | English / Imperial / US customary | 9.324 × 10<sup>7</sup> |
| Hide | `hide` |  | Anglo-Saxon / medieval English | 485,623 |
| Carucate / ploughland | `carucate` |  | Anglo-Saxon / medieval English | ≈ 485,623 |
| Virgate / yardland | `virgate` |  | Medieval English | 121,406 |
| Oxgang / bovate | `oxgang` |  | Medieval English | ≈ 60,702.8 |
| Acre (Scots) | `acre_scots` |  | Scottish | ≈ 5,067 |
| Acre (Irish / plantation) | `acre_irish` |  | Irish | 6,555.24 |
| Square perch (Irish) | `sq_perch_irish` |  | Irish | 40.9702 |
| Jugerum | `jugerum` | iugerum | Ancient Roman | ≈ 2,523.34 |
| Square pes | `sq_pes` |  | Ancient Roman | ≈ 0.087616 |
| Heredium | `heredium` |  | Ancient Roman | ≈ 5,046.68 |
| Centuria (land) | `centuria` |  | Ancient Roman | ≈ 504,668 |
| Plethron (area) | `plethron_sq` |  | Ancient Greek | ≈ 948.64 |
| Setat / aroura | `setat` | aroura, arura | Ancient Egyptian | ≈ 2,741.57 |
| Arpent (de Paris) | `arpent` |  | French (pre-metric) | ≈ 3,418.86 |
| Arpent d'ordonnance (des eaux et forêts) | `arpent_ordonnance` |  | French (pre-metric) | ≈ 5,107.2 |
| Morgen (Prussian) | `morgen_pr` |  | German (pre-metric) | ≈ 2,553.22 |
| Morgen (Dutch / Cape) | `morgen_nl` |  | Dutch | ≈ 8,565.32 |
| Joch (Austrian) | `joch` | Katastraljoch, hold (Hungarian) | German (pre-metric) | ≈ 5,754.64 |
| Desyatina | `desyatina` |  | Russian (pre-1924) | 10,925.4 |
| Square sazhen | `sq_sazhen` |  | Russian (pre-1924) | 4.55225 |
| Tsubo | `tsubo` |  | Japanese | 3.30579 |
| Se | `se` |  | Japanese | 99.1736 |
| Tan | `tan` |  | Japanese | 991.736 |
| Chō (area) | `cho_area` |  | Japanese | 9,917.36 |
| Mu (Qing) | `mu_qing` |  | Chinese | ≈ 614.4 |
| Square chi (Qing) | `sq_chi_qing` |  | Chinese | ≈ 0.1024 |
| Mu (shì, modern) | `mu_shi` | mou | Chinese | 666.667 |
| Qing (area) | `qing_area` |  | Chinese | 66,666.7 |
| Dönüm (Ottoman) | `donum` | dunam, dunum, donum | Ottoman | ≈ 919.3 |
| Dunam (metric) | `dunam_metric` |  | Metric-derived | 1,000 |
| Bigha | `bigha` |  | Indian | ≈ 1,337.8 |
| Planck area | `planck_area` |  | Planck (natural units) | ≈ 2.612 × 10<sup>-70</sup> |

</details>

<details>
<summary>Volume (95)</summary>

| Unit | ID | Also accepts | System | Value (L) |
|---|---|---|---|---|
| Litre | `litre` | liter, L | Metric | 1 |
| Cubic inch | `cu_inch` |  | English / Imperial / US customary | 0.0163871 |
| Cubic foot | `cu_foot` |  | English / Imperial / US customary | 28.3168 |
| Gallon (US / wine / Queen Anne) | `gal_us` | wine gallon, Queen Anne gallon | English / Imperial / US customary | 3.78541 |
| Quart (US liquid) | `qt_us` |  | English / Imperial / US customary | 0.946353 |
| Pint (US liquid) | `pt_us` |  | English / Imperial / US customary | 0.473176 |
| Cup (US) | `cup_us` |  | English / Imperial / US customary | 0.236588 |
| Gill (US) | `gill_us` |  | English / Imperial / US customary | 0.118294 |
| Fluid ounce (US) | `floz_us` |  | English / Imperial / US customary | 0.0295735 |
| Tablespoon (US) | `tbsp_us` |  | English / Imperial / US customary | 0.0147868 |
| Teaspoon (US) | `tsp_us` |  | English / Imperial / US customary | 0.00492892 |
| Barrel (petroleum) | `barrel_oil` | bbl | English / Imperial / US customary | 158.987 |
| Tun (wine) | `tun` |  | English / Imperial / US customary | 953.924 |
| Pipe / butt (wine) | `pipe` | butt | English / Imperial / US customary | 476.962 |
| Puncheon (wine) | `puncheon` |  | English / Imperial / US customary | 317.975 |
| Hogshead (wine) | `hogshead_wine` |  | English / Imperial / US customary | 238.481 |
| Tierce | `tierce` |  | English / Imperial / US customary | 158.987 |
| Barrel (wine) | `barrel_wine` |  | English / Imperial / US customary | 119.24 |
| Rundlet | `rundlet` |  | English / Imperial / US customary | 68.1374 |
| Gallon (ale, pre-1824) | `gal_ale` |  | English / Imperial / US customary | 4.62115 |
| Gallon (imperial) | `gal_imp` |  | English / Imperial / US customary | 4.54609 |
| Quart (imperial) | `qt_imp` |  | English / Imperial / US customary | 1.13652 |
| Pint (imperial) | `pt_imp` |  | English / Imperial / US customary | 0.568261 |
| Gill (imperial) | `gill_imp` |  | English / Imperial / US customary | 0.142065 |
| Fluid ounce (imperial) | `floz_imp` |  | English / Imperial / US customary | 0.0284131 |
| Fluid drachm (imperial) | `fldr_imp` | fluid dram | English / Imperial / US customary | 0.00355163 |
| Minim (imperial) | `minim_imp` |  | English / Imperial / US customary | 5.919 × 10<sup>-5</sup> |
| Barrel (beer, imperial) | `barrel_beer` |  | English / Imperial / US customary | 163.659 |
| Hogshead (beer) | `hogshead_beer` |  | English / Imperial / US customary | 245.489 |
| Kilderkin | `kilderkin` |  | English / Imperial / US customary | 81.8296 |
| Firkin (beer) | `firkin` |  | English / Imperial / US customary | 40.9148 |
| Pin | `pin` |  | English / Imperial / US customary | 20.4574 |
| Bushel (Winchester / US) | `bu_us` |  | English / Imperial / US customary | 35.2391 |
| Peck (US) | `pk_us` |  | English / Imperial / US customary | 8.80977 |
| Gallon (US dry) | `galdry_us` |  | English / Imperial / US customary | 4.40488 |
| Quart (US dry) | `qtdry_us` |  | English / Imperial / US customary | 1.10122 |
| Bushel (imperial) | `bu_imp` |  | English / Imperial / US customary | 36.3687 |
| Peck (imperial) | `pk_imp` |  | English / Imperial / US customary | 9.09218 |
| Quarter (grain) | `quarter_vol` |  | English / Imperial / US customary | 290.95 |
| Chaldron (coal) | `chaldron` |  | English / Imperial / US customary | 1,309.27 |
| Pint (Scots) | `pint_scots` | joug | Scottish | ≈ 1.696 |
| Firlot (Scots) | `firlot` |  | Scottish | ≈ 35 |
| Boll (Scots) | `boll` |  | Scottish | ≈ 140 |
| Amphora (quadrantal) | `amphora_rom` |  | Ancient Roman | ≈ 25.9344 |
| Congius | `congius` |  | Ancient Roman | ≈ 3.2418 |
| Sextarius | `sextarius` |  | Ancient Roman | ≈ 0.5403 |
| Hemina | `hemina` |  | Ancient Roman | ≈ 0.27015 |
| Cyathus | `cyathus` |  | Ancient Roman | ≈ 0.045025 |
| Modius | `modius` |  | Ancient Roman | ≈ 8.6448 |
| Metretes (Attic) | `metretes` | amphora (Greek) | Ancient Greek | ≈ 39.3 |
| Chous | `chous` |  | Ancient Greek | ≈ 3.275 |
| Kotyle | `kotyle` |  | Ancient Greek | ≈ 0.272917 |
| Kyathos | `kyathos` |  | Ancient Greek | ≈ 0.0454861 |
| Medimnos (Attic) | `medimnos` |  | Ancient Greek | ≈ 52.4 |
| Choinix | `choinix` |  | Ancient Greek | ≈ 1.09167 |
| Bath | `bath` |  | Biblical / Talmudic | ≈ 22 |
| Ephah | `ephah` |  | Biblical / Talmudic | ≈ 22 |
| Homer / kor | `homer` | kor, cor | Biblical / Talmudic | ≈ 220 |
| Seah | `seah` | measure (KJV) | Biblical / Talmudic | ≈ 7.33333 |
| Omer | `omer` |  | Biblical / Talmudic | ≈ 2.2 |
| Kab / cab | `kab` |  | Biblical / Talmudic | ≈ 1.22222 |
| Hin | `hin` |  | Biblical / Talmudic | ≈ 3.66667 |
| Log | `log` |  | Biblical / Talmudic | ≈ 0.305556 |
| Pinte (de Paris) | `pinte` |  | French (pre-metric) | ≈ 0.9521 |
| Chopine | `chopine` |  | French (pre-metric) | ≈ 0.47605 |
| Velte | `velte` |  | French (pre-metric) | ≈ 7.6168 |
| Muid (wine, Paris) | `muid_vin` |  | French (pre-metric) | ≈ 274.205 |
| Boisseau (de Paris) | `boisseau` |  | French (pre-metric) | ≈ 12.695 |
| Minot | `minot` |  | French (pre-metric) | ≈ 38.085 |
| Setier (grain, Paris) | `setier` |  | French (pre-metric) | ≈ 152.34 |
| Muid (grain, Paris) | `muid_grain` |  | French (pre-metric) | ≈ 1,828.08 |
| Quart (Prussian) | `quart_pr` |  | German (pre-metric) | ≈ 1.145 |
| Eimer (Prussian) | `eimer_pr` |  | German (pre-metric) | ≈ 68.7 |
| Scheffel (Prussian) | `scheffel_pr` |  | German (pre-metric) | ≈ 54.96 |
| Maß (Austrian) | `mass_at` | Mass | German (pre-metric) | ≈ 1.41777 |
| Maß (Bavarian) | `mass_by` |  | German (pre-metric) | ≈ 1.069 |
| Vedro | `vedro` |  | Russian (pre-1924) | ≈ 12.2994 |
| Shtof | `shtof` |  | Russian (pre-1924) | ≈ 1.22994 |
| Charka | `charka` |  | Russian (pre-1924) | ≈ 0.122994 |
| Bochka | `bochka` |  | Russian (pre-1924) | ≈ 491.976 |
| Chetvert (dry) | `chetvert` | chyetvyert' | Russian (pre-1924) | ≈ 209.91 |
| Chetverik | `chetverik` | chyetvyerik | Russian (pre-1924) | ≈ 26.2387 |
| Fanega (dry, Castile) | `fanega` |  | Spanish customary | ≈ 55.5 |
| Celemín | `celemin` |  | Spanish customary | ≈ 4.625 |
| Cántara / arroba (wine) | `cantara` |  | Spanish customary | ≈ 16.133 |
| Kile (Istanbul) | `kile` |  | Ottoman | ≈ 37 |
| Koku | `koku` |  | Japanese | 180.391 |
| To | `to_jp` |  | Japanese | 18.0391 |
| Shō | `sho` |  | Japanese | 1.80391 |
| Gō | `go` |  | Japanese | 0.180391 |
| Sheng (Qing) | `sheng_qing` |  | Chinese | ≈ 1.0355 |
| Dou (Qing) | `dou_qing` | peck (Chinese) | Chinese | ≈ 10.355 |
| Shi / dan (volume, Qing) | `shi_vol` |  | Chinese | ≈ 103.55 |
| Planck volume | `planck_volume` |  | Planck (natural units) | ≈ 4.222 × 10<sup>-102</sup> |
| Tlho'ren | `tlhoren` | tlho'ren | Klingon (fictional) (fictional) | ≈ 1 |

</details>

<details>
<summary>Mass (85)</summary>

| Unit | ID | Also accepts | System | Value (kg) |
|---|---|---|---|---|
| Kilogram | `kilogram` | kg | Metric (SI) | 1 |
| Pound (avoirdupois) | `lb` | lb, pound | English / Imperial / US customary | 0.453592 |
| Ounce (avoirdupois) | `oz` | oz | English / Imperial / US customary | 0.0283495 |
| Dram (avoirdupois) | `dram_avdp` | dr | English / Imperial / US customary | 0.00177185 |
| Grain | `grain` | gr | English / Imperial / US customary | 6.48 × 10<sup>-5</sup> |
| Stone | `stone` | st | English / Imperial / US customary | 6.35029 |
| Quarter (weight) | `quarter_mass` |  | English / Imperial / US customary | 12.7006 |
| Hundredweight (long) | `cwt_long` | cwt | English / Imperial / US customary | 50.8023 |
| Hundredweight (short) | `cwt_short` |  | English / Imperial / US customary | 45.3592 |
| Ton (long) | `ton_long` | imperial ton | English / Imperial / US customary | 1,016.05 |
| Ton (short) | `ton_short` |  | English / Imperial / US customary | 907.185 |
| Tonne (metric ton) | `tonne` |  | Metric | 1,000 |
| Clove (wool) | `clove` |  | English / Imperial / US customary | 3.17515 |
| Tod (wool) | `tod` |  | English / Imperial / US customary | 12.7006 |
| Sack (wool) | `sack_wool` |  | English / Imperial / US customary | 165.108 |
| Pound (troy) | `lb_troy` |  | English / Imperial / US customary | 0.373242 |
| Ounce (troy) | `oz_troy` | ozt | English / Imperial / US customary | 0.0311035 |
| Pennyweight | `dwt` | dwt | English / Imperial / US customary | 0.00155517 |
| Tower pound | `lb_tower` |  | English / Imperial / US customary | 0.349914 |
| Merchants' pound | `lb_merchant` | mercantile pound | English / Imperial / US customary | 0.437393 |
| Scruple (apothecaries') | `scruple` |  | English / Imperial / US customary | 0.00129598 |
| Drachm (apothecaries') | `drachm_ap` | dram (apothecaries') | English / Imperial / US customary | 0.00388793 |
| Carat (metric) | `carat` | ct | Metric | 2 × 10<sup>-4</sup> |
| Tron pound (Scots) | `lb_tron` | trone pound | Scottish | ≈ 0.6 |
| Livre (poids de marc) | `livre_poids` |  | French (pre-metric) | ≈ 0.489506 |
| Marc (French) | `marc_fr` |  | French (pre-metric) | ≈ 0.244753 |
| Once (French) | `once_fr` |  | French (pre-metric) | ≈ 0.0305941 |
| Gros | `gros_fr` |  | French (pre-metric) | ≈ 0.00382426 |
| Grain (French) | `grain_fr` |  | French (pre-metric) | ≈ 5.311 × 10<sup>-5</sup> |
| Quintal (French, old) | `quintal_fr` |  | French (pre-metric) | ≈ 48.9506 |
| Cologne mark | `cologne_mark` |  | German (pre-metric) | ≈ 0.233856 |
| Pfund (Prussian, 1816) | `pfund_pr` |  | German (pre-metric) | ≈ 0.467711 |
| Lot (Prussian) | `lot_pr` | Loth | German (pre-metric) | ≈ 0.014616 |
| Zollpfund | `zollpfund` |  | German (pre-metric) | 0.5 |
| Zentner | `zentner` | hundredweight (German) | German (pre-metric) | 50 |
| Pfund (Viennese) | `pfund_wien` |  | German (pre-metric) | ≈ 0.56 |
| Funt | `funt` | Russian pound | Russian (pre-1924) | ≈ 0.409512 |
| Pud | `pud` | pood | Russian (pre-1924) | ≈ 16.3805 |
| Berkovets | `berkovets` |  | Russian (pre-1924) | ≈ 163.805 |
| Lot (Russian) | `lot_ru` |  | Russian (pre-1924) | ≈ 0.0127973 |
| Zolotnik | `zolotnik` |  | Russian (pre-1924) | ≈ 0.00426575 |
| Dolya | `dolya` |  | Russian (pre-1924) | ≈ 4.443 × 10<sup>-5</sup> |
| Libra (Castilian) | `libra_es` |  | Spanish customary | ≈ 0.4601 |
| Onza | `onza_es` |  | Spanish customary | ≈ 0.0287563 |
| Arroba (Castilian) | `arroba_es` |  | Spanish customary | ≈ 11.5025 |
| Quintal (Castilian) | `quintal_es` |  | Spanish customary | ≈ 46.01 |
| Arrátel | `arratel` |  | Portuguese customary | ≈ 0.459 |
| Arroba (Portuguese) | `arroba_pt` |  | Portuguese customary | ≈ 14.688 |
| Okka / oka | `okka` | oke, oka | Ottoman | ≈ 1.2829 |
| Dirhem | `dirhem` |  | Ottoman | ≈ 0.00320725 |
| Kantar / qintar | `kantar` |  | Ottoman | ≈ 56.4476 |
| Monme | `monme` |  | Japanese | 0.00375 |
| Kin | `kin` | catty (Japanese) | Japanese | 0.6 |
| Kan / kanme | `kan` |  | Japanese | 3.75 |
| Liang / tael (Qing) | `liang_qing` | tael | Chinese | ≈ 0.0373 |
| Qian / mace (Qing) | `qian_qing` |  | Chinese | ≈ 0.00373 |
| Jin / catty (Qing) | `jin_qing` | catty | Chinese | ≈ 0.5968 |
| Dan / picul | `picul` |  | Chinese | ≈ 59.68 |
| Catty (Hong Kong legal) | `catty_hk` |  | Chinese | 0.60479 |
| Jin (shì, modern) | `jin_shi` |  | Chinese | 0.5 |
| Tola | `tola` |  | Indian | 0.0116638 |
| Ratti | `ratti` |  | Indian | 1.215 × 10<sup>-4</sup> |
| Seer | `seer` |  | Indian | 0.933104 |
| Maund (Indian government) | `maund` | mun | Indian | 37.3242 |
| Libra (Roman pound) | `libra_rom` |  | Ancient Roman | ≈ 0.3289 |
| Uncia (Roman ounce) | `uncia_mass` |  | Ancient Roman | ≈ 0.0274083 |
| Scripulum | `scripulum` | scrupulum | Ancient Roman | ≈ 0.00114201 |
| Siliqua | `siliqua` |  | Ancient Roman | ≈ 1.903 × 10<sup>-4</sup> |
| Mina (Attic) | `mina_att` |  | Ancient Greek | ≈ 0.431 |
| Drachma (weight) | `drachma_mass` |  | Ancient Greek | ≈ 0.00431 |
| Obol (weight) | `obol_mass` |  | Ancient Greek | ≈ 7.183 × 10<sup>-4</sup> |
| Talent (Attic) | `talent_att` |  | Ancient Greek | ≈ 25.86 |
| Shekel (biblical) | `shekel_bib` |  | Biblical / Talmudic | ≈ 0.011 |
| Gerah | `gerah` |  | Biblical / Talmudic | ≈ 5.5 × 10<sup>-4</sup> |
| Beka | `beka` | bekah | Biblical / Talmudic | ≈ 0.0055 |
| Mina / maneh (biblical) | `mina_bib` |  | Biblical / Talmudic | ≈ 0.55 |
| Talent / kikkar (biblical) | `talent_bib` |  | Biblical / Talmudic | ≈ 33 |
| Shekel (Mesopotamian) | `shekel_meso` |  | Mesopotamian | ≈ 0.0084 |
| Še (grain) | `se_grain` |  | Mesopotamian | ≈ 4.667 × 10<sup>-5</sup> |
| Mina (Mesopotamian) | `mina_meso` |  | Mesopotamian | ≈ 0.504 |
| Talent (Mesopotamian) | `talent_meso` |  | Mesopotamian | ≈ 30.24 |
| Deben (New Kingdom) | `deben` |  | Ancient Egyptian | ≈ 0.091 |
| Kite / qedet | `kite` |  | Ancient Egyptian | ≈ 0.0091 |
| Planck mass | `planck_mass` | mP | Planck (natural units) | ≈ 2.176 × 10<sup>-8</sup> |
| Cheb | `cheb` |  | Klingon (fictional) (fictional) | ≈ 2.25 |

</details>

<details>
<summary>Count (11)</summary>

| Unit | ID | Also accepts | System | Value (items) |
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
