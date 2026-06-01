// Transposition table keyed by (state, side-to-move). JS port of
// kalah/transposition.py. Entries carry an `exact` tag (terminal-derived value,
// depth-independent) so the exact solver never trusts a heuristic estimate.

export const EXACT = 0;
export const LOWER = 1;
export const UPPER = 2;

// Hard ceiling on cached entries. A JS Map throws past ~16.7M, and an unbounded
// table would also exhaust a browser tab's memory on a big search. Once full we
// stop caching *new* states (existing ones still update) -- the search stays
// correct, just without further speedups. ~1M entries is roughly 150 MB.
const MAX_ENTRIES = 1_000_000;

export class TranspositionTable {
  constructor() {
    this.map = new Map();
  }

  get(key) {
    return this.map.get(key);
  }

  set(key, value, depth, flag, move, exact) {
    const e = this.map.get(key);
    if (e !== undefined) {
      if (e.exact && !exact) return; // never downgrade a terminal-exact entry
      if (e.exact === exact && e.depth > depth) return; // same class: keep deeper
    } else if (this.map.size >= MAX_ENTRIES) {
      return; // table full: stop adding new states (search stays correct)
    }
    this.map.set(key, { value, depth, flag, move, exact });
  }

  clear() {
    this.map.clear();
  }

  get size() {
    return this.map.size;
  }
}
