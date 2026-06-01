// Optional perfect-play book: precomputed (state, player) -> optimal move.
// JS port of kalah/book.py. Missing book is a no-op (engine falls back to search).

let BOOK = null;

export function keyFor(state, player) {
  return player + ':' + state.join(',');
}

export function setBook(obj) {
  BOOK = obj;
}

export function hasBook() {
  return BOOK !== null;
}

export async function loadBook(url) {
  try {
    const res = await fetch(url);
    BOOK = res.ok ? await res.json() : {};
  } catch {
    BOOK = {};
  }
  return BOOK;
}

export function bookMove(state, player) {
  if (!BOOK) return -1;
  const entry = BOOK[keyFor(state, player)];
  if (entry === undefined) return -1;
  return Array.isArray(entry) ? entry[0] : entry;
}
