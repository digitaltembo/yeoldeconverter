"""Check that every source 'quote' in the data appears on the page it cites.

Usage: python3 scripts/check_quotes.py [--fetch] data/currencies.json data/units.json

Pages are read from sources/pages/ (gitignored). With --fetch, missing pages are downloaded first:
Wikipedia (any language) and Tolkien Gateway as wikitext (action=raw), Project Gutenberg books as plain text, anything
else as HTML. Wikitext is rendered roughly as it reads on the page (links, {{frac}}, {{val}}, {{convert}}, {{lang}},
&nbsp;, superscripts; table cells joined by " | ") before searching, so quotes are written as the page displays them.
A unit's quote must also appear within 400 characters of one of the unit's names. Exits with status 1 on any problem.
"""
import functools, html, json, os, re, sys, unicodedata, urllib.parse, urllib.request

PAGES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sources", "pages")
UA = {"User-Agent": "yeoldeconverter-source-check/0.1"}
WIKIS = {"tolkiengateway.net": "https://tolkiengateway.net/w/index.php"}  # and every *.wikipedia.org


def local_page(url):
    """(local path, download URL) for a cited URL."""
    u = urllib.parse.urlsplit(url)
    wiki = WIKIS.get(u.netloc) or (f"https://{u.netloc}/w/index.php" if u.netloc.endswith(".wikipedia.org") else None)
    if wiki and u.path.startswith("/wiki/"):
        title = urllib.parse.unquote(u.path[len("/wiki/"):])
        return (os.path.join(PAGES, u.netloc, title.replace("/", "_") + ".txt"),
                f"{wiki}?title={urllib.parse.quote(title)}&action=raw")
    m = re.fullmatch(r"/ebooks/(\d+)", u.path)
    if u.netloc == "www.gutenberg.org" and m:
        return os.path.join(PAGES, u.netloc, m[1] + ".txt"), f"https://www.gutenberg.org/cache/epub/{m[1]}/pg{m[1]}.txt"
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", (u.path + ("?" + u.query if u.query else "")).strip("/")) or "index"
    return os.path.join(PAGES, u.netloc, name + ".html"), url


FR = {("1", "2"): "½", ("2", "3"): "⅔", ("1", "3"): "⅓", ("1", "4"): "¼", ("3", "4"): "¾"}


def frac(m):
    a = m.group(1).split("|")
    if len(a) == 3:
        return a[0] + FR.get((a[1], a[2]), f" {a[1]}/{a[2]}")
    if len(a) == 2:
        return FR.get((a[0], a[1]), f"{a[0]}/{a[1]}")
    return f"1/{a[0]}"


def render(text, path):
    if path.endswith(".html"):
        text = re.sub(r"(?s)<(script|style).*?</\1>", " ", text)
        text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    else:
        text = re.sub(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>|<hiero>.*?</hiero>", "", text, flags=re.S)
        text = re.sub(r"<br\s*/?>|\{\{(?:nbsp|snd)\}\}", " ", text)
        text = re.sub(r"\{\{(?:[Tt]ransliteration|[Tt]ransl)\|[^|{}]*\|([^|{}]*)\}\}", r"\1", text)
        text = re.sub(r"<sup>([23])</sup>|\{\{sup\|([23])\}\}", lambda m: "²" if (m[1] or m[2]) == "2" else "³", text)
        text = re.sub(r"\{\{s?frac\|([^{}]*)\}\}", frac, text)
        text = re.sub(r"\{\{val\|([^|{}]*)(?:\|e=([^|{}]*))?(?:\|u[l]?=([^|{}]*))?[^{}]*\}\}",
                      lambda m: m[1] + (f" × 10^{m[2]}" if m[2] else "") + (f" {m[3]}" if m[3] else ""), text)
        text = re.sub(r"\{\{(?:[Cc]onvert|[Cc]vt)\|([^|{}]*)\|(and|to|or|-|–|and\(-\)|to\(-\))\|([^|{}]*)\|([^|{}]*)[^{}]*\}\}",
                      lambda m: f"{m[1]} {m[2].replace('(-)', '')} {m[3]} {m[4]}" if m[2][0].isalpha() else f"{m[1]}–{m[3]} {m[4]}", text)
        text = re.sub(r"\{\{(?:[Cc]onvert|[Cc]vt|unité)\|([^|{}]*)\|([^|{}]*)[^{}]*\}\}", r"\1 \2", text)
        text = re.sub(r"\{\{(?:[Ll]ang|[Ll]angx)\|[^|{}]*\|(?:[a-z]+=[^|{}]*\|)*([^|{}=]*)[^{}]*\}\}", r"\1", text)
        for _ in range(3):  # footnote templates, innermost first
            text = re.sub(r"\{\{(?:sfnp?|rp|r|efn|refn|citation needed|cn)(?:\|[^{}]*)?\}\}", "", text, flags=re.I)
        text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)
        text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)
        text = text.replace("&nbsp;", " ").replace("'''", "").replace("''", "")
        # tables: drop cell attributes, then write every cell separator as " | "
        text = re.sub(r'(?:style|align|colspan|rowspan|height|width|class|scope|valign|bgcolor)=("[^"\n]*"|[^\s|]+)\s*\|(?!\|)', "", text)
        text = re.sub(r"\s*(?:\|\||!!|\|)\s*", " | ", text)
    return re.sub(r"\s+", " ", text)


def normalize(quote, path):
    """A quote as it will be searched for: whitespace collapsed; in wikitext, cell separators as in render()."""
    if not path.endswith(".html"):
        quote = re.sub(r"\s*(?:\|\||!!|\|)\s*", " | ", quote)
    return re.sub(r"\s+", " ", quote).strip()


def fold(text):
    """Lower case without accents, so 'cùn' matches 'Cun'."""
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


GENERIC = {"the", "old", "new", "and", "unit", "imperial", "english", "modern", "dry", "liquid", "wine", "beer"}


def unit_names(u):
    names = {u["name"], *u.get("aliases", [])}
    names |= {part for n in list(names) for part in re.split(r"[()/,]| or | d'| de | des ", n)}
    return {fold(n.strip()) for n in names if len(n.strip()) >= 2 and fold(n.strip()) not in GENERIC}


def sources_in(doc):
    """(where, source, names): names, for a unit, are what its quote must appear near."""
    for c in doc.get("currencies", []):
        yield from ((c["id"], s, None) for s in c.get("sources", []))
        for p in c["series"]:
            yield from ((f"{c['id']} {p['year']}", s, None) for s in p["sources"])
    for u in doc.get("units", []):
        yield from ((u["id"], s, unit_names(u)) for s in u.get("sources", []))


NEAR = 400  # characters: a unit's quote must have one of the unit's names within this distance


def near_name(text, quote, names):
    t, q = fold(text), fold(quote)
    for m in re.finditer(re.escape(q), t):
        window = t[max(0, m.start() - NEAR): m.end() + NEAR]
        if any(re.search(r"(?<![^\W_])" + re.escape(n) + r"(?:s|es|e|h)?(?![^\W_])", window) for n in names):
            return True
    return False


# What a number in a unit's quote may be expressed in, as (base units per unit): the base unit's own multiples and the
# English units that pages give alongside.
SCALES = {
    "length": [1, 1e-3, 1e-2, 1e3, 1e-6, 0.0254, 0.3048, 0.9144, 1609.344, 1852, 149597870700, 9460730472580800, 3.0856775814913673e16],
    "area": [1, 1e4, 1e6, 0.09290304, 0.83612736, 4046.8564224, 2589988.110336],
    "volume": [1, 1e-3, 1e3, 0.016387064, 28.316846592, 4.54609, 3.785411784, 0.56826125, 0.473176473, 1.1365225, 0.946352946,
               0.0284130625, 0.0295735295625, 36.36872, 35.23907016688, 8.80976754172],
    "mass": [1, 1e-3, 1e-6, 1e3, 0.45359237, 0.028349523125, 6.479891e-5, 0.0311034768],
    "count": [1],
}
VULGAR = {"½": .5, "⅓": 1 / 3, "⅔": 2 / 3, "¼": .25, "¾": .75, "⅛": .125}
NUMBER = re.compile(r"(\d+)/(\d+)|(\d[\d.,  ]*\d|\d)\s?([½⅓⅔¼¾⅛])?(?: ?(?:[x×] ?10 ?\^? ?|E)([−+-]?\d+))?|([½⅓⅔¼¾⅛])")
WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
         "eleven": 11, "twelve": 12, "twenty": 20, "seventy": 70, "hundred": 100, "thousand": 1e3, "million": 1e6,
         "half": 1 / 2, "third": 1 / 3, "fourth": 1 / 4, "quarter": 1 / 4, "sixth": 1 / 6, "tenth": 1 / 10,
         "twelfth": 1 / 12, "fourteenth": 1 / 14, "sixteenth": 1 / 16}


def words(text):
    """Numbers written as words: 'five thousand' is 5000, 'one sixth larger' is 7/6."""
    out, t = [], text.lower()
    for m in re.finditer(r"\b(" + "|".join(WORDS) + r")(?:[ -](" + "|".join(WORDS) + r"))?\b( larger| longer)?", t):
        a, b = WORDS[m[1]], WORDS.get(m[2] or "", None)
        v = a * b if b and b >= 100 else (a * b if b and b < 1 else a)
        out += [v] + ([b] if b and b < 100 and b >= 1 else []) + ([1 + v] if m[3] and v < 1 else [])
    for m in re.finditer(r"(\d+)\s*(?:feet|foot|ft)[ ,]+(\d+)\s*(?:inches|inch|in)\b", t):  # 5 feet 7 inches, in inches
        out.append(int(m[1]) * 12 + int(m[2]))
    return out


def numbers(text):
    """Every reading of every number in text: '1,145' is both 1145 and 1.145, '316.080 640' is 316.08064."""
    out = words(text)
    for m in NUMBER.finditer(text.replace("−", "-")):
        if m[1]:
            out += [int(m[1]) / int(m[2])] if int(m[2]) else []; continue
        if m[6]:
            out.append(VULGAR[m[6]]); continue
        digits, readings = re.sub(r"[  ]", "", m[3]), set()
        for dec in ".,":
            other = "," if dec == "." else "."
            t = digits.replace(other, "")
            if t.count(dec) <= 1:
                try:
                    readings.add(float(t.replace(dec, ".")))
                except ValueError:
                    pass
        for v in readings:
            v += VULGAR.get(m[4] or "", 0)
            out.append(v * 10 ** int(m[5]) if m[5] else v)
    for m in re.finditer(r"(\d+(?:\.\d+)?) ?± ?(\d+(?:\.\d+)?)", text):  # 8.40±0.34 is 8.06 to 8.74
        out += [float(m[1]) - float(m[2]), float(m[1]) + float(m[2])]
    return [v for v in out if v]


@functools.lru_cache(maxsize=None)
def name_pattern(names):
    if not names:
        return None
    return re.compile(r"(?<![^\W_])(?:" + "|".join(map(re.escape, sorted(names))) + r")(?:s|es|e)?(?![^\W_])")


def value_targets(u, units, quote):
    """Numbers the quote may state for unit u: its value or range in any listed scale, or its ratio (either way) to a
    unit in its definition chain or to another unit the quote names (or that unit's square or cube)."""
    vals = [u["si"]] + [u[k] for k in ("low", "high") if k in u]
    targets = [v / s for v in vals for s in SCALES[u["category"]]]
    others, p = [], u
    while p["definition"]["type"] == "multiple":
        p = units[p["definition"]["of"]]
        others.append(p["si"])
    q, mine = fold(quote), unit_names(u)
    for o in units.values():
        pattern = name_pattern(frozenset(n for n in unit_names(o) - mine if len(n) >= 3))
        if o["id"] != u["id"] and pattern and pattern.search(q):
            if o["category"] == u["category"]:
                others.append(o["si"])
            elif o["category"] == "length" and u["category"] in ("area", "volume"):
                others.append(o["si"] ** 2 if u["category"] == "area" else o["si"] ** 3 * 1000)
    targets += [r for o in others for v in vals for r in (v / o, o / v)]
    return targets


def inherits_range(u, units):
    """True if u's range is its parent's range carried through the definition (checked on the parent instead)."""
    d = u["definition"]
    p = units.get(d.get("of", ""))
    if not p or "low" not in p:
        return False
    k = {"multiple": d.get("factor"), "square": None, "cube": None}[d["type"]]
    f = (lambda v: v * k) if k else (lambda v: v ** 2) if d["type"] == "square" else (lambda v: v ** 3 * 1000)
    return all(abs(f(p[e]) / u[e] - 1) < 1e-6 for e in ("low", "high"))


def states_value(quotes, u, units, tolerance=0.01):
    for q in quotes:
        xs = numbers(q) + [1]  # a bare unit name ("in the quart range") states 1 of it
        if len(xs) <= 4:  # "seventy glumgluffs ... about six feet": a ratio of two numbers in a short statement
            xs += [a / b for a in xs for b in xs if b]
        if any(abs(x / t - 1) <= tolerance for x in xs for t in value_targets(u, units, q)):
            return True
    return False


def main(args):
    fetch = "--fetch" in args
    rendered, problems, checked = {}, [], set()
    for data_path in [a for a in args if a != "--fetch"]:
        doc = json.load(open(data_path, encoding="utf-8"))
        units = {u["id"]: u for u in doc.get("units", [])}
        for u in units.values():
            quotes = [s["quote"] for s in u["sources"] if s.get("quote")]
            if quotes and not states_value(quotes, u, units):
                problems.append(f"no number in the quotes for {u['id']} matches its value, range or factor: {quotes}")
            if quotes and "low" in u and not inherits_range(u, units):
                for end in ("low", "high"):
                    alone = {k: v for k, v in u.items() if k not in ("low", "high")} | {"si": u[end]}
                    if not states_value(quotes, alone, units):
                        problems.append(f"no number in the quotes for {u['id']} matches its {end} end, {u[end]:.6g}: {quotes}")
        for where, s, names in sources_in(doc):
            q = s.get("quote")
            if not q or (s["url"], q, where if names else None) in checked:
                continue
            checked.add((s["url"], q, where if names else None))
            path, download = local_page(s["url"])
            if not os.path.exists(path) and fetch:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with urllib.request.urlopen(urllib.request.Request(download, headers=UA), timeout=60) as r:
                    open(path, "wb").write(r.read())
            if not os.path.exists(path):
                problems.append(f"no local copy of {s['url']} ({where}); run with --fetch")
                continue
            if path not in rendered:
                rendered[path] = render(open(path, encoding="utf-8", errors="replace").read(), path)
            if normalize(q, path) not in rendered[path]:
                problems.append(f"quote not found on {s['url']} ({where}): {q}")
            elif names and not near_name(rendered[path], normalize(q, path), names):
                problems.append(f"quote is not near the unit's name on {s['url']} ({where}): {q}")
    print(f"{len(checked)} quotes checked, {len(problems)} problems")
    for p in problems:
        print("  " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
