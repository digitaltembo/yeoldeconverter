// Name normalisation shared by the currency and unit lookups.

/** Lower-case, strip accents and punctuation (keeping currency/unit symbols), collapse whitespace. */
export function normalize(s: string): string {
  return s
    .normalize("NFKD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[’']/g, "'")
    .replace(/[^\p{L}\p{N}£$¥€¢ƒ'"²³./ ]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const IRREGULAR_PLURALS: Record<string, string> = {
  pence: "penny",
  feet: "foot",
  denarii: "denarius",
  sestertii: "sestertius",
  asses: "as",
  reales: "real",
  reis: "real",
  "réis": "real",
  drachmae: "drachma",
  drachmai: "drachma",
  obols: "obol",
  talents: "talent",
  minae: "mina",
  kopecks: "kopek",
  kopeks: "kopek",
  kreuzers: "kreuzer",
  groschen: "groschen",
  scudi: "scudo",
  soldi: "soldo",
  denari: "denaro",
  lire: "lira",
  centesimi: "centesimo",
  zecchini: "zecchino",
  fiorini: "fiorino",
  pfennige: "pfennig",
  gulden: "gulden",
  kronen: "krone",
  kronor: "krona",
  kroner: "krone",
  heller: "heller",
  stuivers: "stuiver",
  duiten: "duit",
  cubits: "cubit",
  stadia: "stadion",
  jugera: "jugerum",
  talenta: "talent",
  minas: "mina",
  ells: "ell",
};

function singularWord(w: string): string[] {
  const out: string[] = [];
  const irregular = IRREGULAR_PLURALS[w];
  if (irregular) out.push(irregular);
  if (w.endsWith("ies")) out.push(w.slice(0, -3) + "y");
  if (w.endsWith("es")) out.push(w.slice(0, -2));
  if (w.endsWith("s")) out.push(w.slice(0, -1));
  if (w.endsWith("i")) out.push(w.slice(0, -1) + "us");
  if (w.endsWith("ae")) out.push(w.slice(0, -1));
  return out;
}

/**
 * Candidate singular forms of a (possibly plural) normalised word or phrase: the phrase itself,
 * then forms with one word singularised ("square feet" → "square foot", "pieces of eight" → "piece of eight").
 */
export function singularForms(s: string): string[] {
  const words = s.split(" ");
  const out = new Set<string>([s]);
  for (let i = words.length - 1; i >= 0; i--) {
    for (const form of singularWord(words[i]!)) out.add([...words.slice(0, i), form, ...words.slice(i + 1)].join(" "));
  }
  return [...out];
}

/** Index entries under every name; returns a map from normalised key to entries. */
export function buildIndex<T>(items: T[], names: (item: T) => (string | undefined)[]): Map<string, T[]> {
  const index = new Map<string, T[]>();
  for (const item of items) {
    const keys = new Set<string>();
    for (const n of names(item)) {
      if (!n) continue;
      const k = normalize(n);
      if (k) keys.add(k);
      // "Pound (sovereign/quid)" is also findable as "pound"
      const bare = normalize(n.replace(/\([^)]*\)/g, ""));
      if (bare) keys.add(bare);
    }
    for (const k of keys) {
      const list = index.get(k) ?? [];
      list.push(item);
      index.set(k, list);
    }
  }
  return index;
}

/** Lookup by name/alias/id, including singular forms of the query (exact-form matches first). */
export function lookup<T>(index: Map<string, T[]>, query: string): T[] {
  const out = new Set<T>();
  for (const form of singularForms(normalize(query))) {
    for (const hit of index.get(form) ?? []) out.add(hit);
  }
  return [...out];
}

/**
 * Narrow ambiguous hits to those whose full name/alias/id equals the query (or its singular),
 * so "pound" picks the unit aliased exactly "pound" over "Pound (troy)".
 */
export function preferExact<T>(hits: T[], query: string, names: (item: T) => (string | undefined)[]): T[] {
  if (hits.length < 2) return hits;
  const forms = new Set(singularForms(normalize(query)));
  const exact = hits.filter((h) => names(h).some((n) => n !== undefined && forms.has(normalize(n))));
  return exact.length > 0 ? exact : hits;
}
