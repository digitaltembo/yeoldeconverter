export class NotFoundError extends Error {
  constructor(kind: string, query: string) {
    super(`No ${kind} matches "${query}"`);
    this.name = "NotFoundError";
  }
}

export class AmbiguousError extends Error {
  readonly candidates: string[];
  constructor(kind: string, query: string, candidates: string[]) {
    super(`"${query}" is ambiguous (${kind}): ${candidates.join(", ")} — use an id`);
    this.name = "AmbiguousError";
    this.candidates = candidates;
  }
}

export class IncompatibleUnitsError extends Error {
  constructor(from: string, fromCategory: string, to: string, toCategory: string) {
    super(`Cannot convert ${from} (${fromCategory}) to ${to} (${toCategory})`);
    this.name = "IncompatibleUnitsError";
  }
}
