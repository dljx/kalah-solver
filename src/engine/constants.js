// Board geometry, player maps, and tunable constants for vertical Kalah(6,3).
// JavaScript port of the Python engine's constants (kalah/constants.py).
//
// 14 receptacles in a vertical 2-column / 6-row grid:
//   0..5    left column   Player 2 (Bottom / AI) pits, descending to the store
//   6       bottom store  Player 2's store
//   7..12   right column  Player 1 (Top / Opponent) pits, ascending to the store
//   13      top store     Player 1's store
//
// The index order makes counter-clockwise sowing a plain (i+1) % 14 that only
// ever skips the opponent's store.

export const NUM_PITS = 6;
export const STONES_PER_PIT = 3;
export const CELLS = 14;

export const P1_TOP = 1; // Top / Opponent
export const P2_BOTTOM = 2; // Bottom / Me (the AI's home seat)

export const OPPONENT = { 1: 2, 2: 1 };
export const STORE = { 1: 13, 2: 6 };
export const OPP_STORE = { 1: 6, 2: 13 }; // the store this player must skip
export const PITS = { 1: [7, 8, 9, 10, 11, 12], 2: [0, 1, 2, 3, 4, 5] };

// O(1) "is this pit on my side?" test for the sowing hot path.
export const ownPit = (player, i) =>
  player === P1_TOP ? i >= 7 && i <= 12 : i >= 0 && i <= 5;

// Capture pairing: pit i faces pit 12-i (0<->12 ... 5<->7). Indices 0..12.
export const OPPOSITE = Array.from({ length: 13 }, (_, i) => 12 - i);

export const INITIAL = [3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 0];

// Steps from a pit until a stone lands in the player's own store.
export function distanceToStore(pit, player) {
  const store = STORE[player];
  const skip = OPP_STORE[player];
  let d = 0;
  let i = pit;
  for (;;) {
    i = (i + 1) % CELLS;
    if (i === skip) continue;
    d += 1;
    if (i === store) return d;
  }
}

// Precomputed pit -> steps-to-own-store, per player (used by the heuristic).
export const DIST_TO_STORE = {
  1: Object.fromEntries(PITS[1].map((p) => [p, distanceToStore(p, P1_TOP)])),
  2: Object.fromEntries(PITS[2].map((p) => [p, distanceToStore(p, P2_BOTTOM)])),
};

// --- Scoring / search ---
export const INF = 1e9;
export const TERMINAL_SCALE = 10000; // a proven margin dominates any heuristic leaf
export const DRAW_SCORE = 0;
export const WIN_THRESHOLD = TERMINAL_SCALE - 1000;

// Heuristic weights (timed mode). Store differential dominates.
export const WEIGHTS = { store: 100, control: 2, extraTurn: 6 };

export const MAX_DEPTH = 64;
export const TIME_BUDGET_MS = 1500;
export const ORDER_DEPTH = 12; // shallow pre-pass depth that primes the exact solver
