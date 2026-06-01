// Game rules for vertical Kalah(6,3). JS port of kalah/board.py.
// State is a 14-element number array; every function is pure (returns new arrays).

import {
  CELLS,
  P1_TOP,
  P2_BOTTOM,
  OPPONENT,
  STORE,
  OPP_STORE,
  PITS,
  ownPit,
  OPPOSITE,
  INITIAL,
} from './constants.js';

export function initialBoard() {
  return INITIAL.slice();
}

export function legalMoves(state, player) {
  return PITS[player].filter((p) => state[p] > 0);
}

/**
 * Play `pit` for `player`, sowing counter-clockwise.
 * @returns {{ state:number[], extra:boolean, captured:boolean }}
 *   extra    – the last stone landed in the player's own store (go again)
 *   captured – empty capture: last stone fell in a previously-empty own pit
 *              facing a non-empty opposite pit
 */
export function sow(state, pit, player) {
  const b = state.slice();
  let stones = b[pit];
  b[pit] = 0;
  const store = STORE[player];
  const skip = OPP_STORE[player];

  let i = pit;
  while (stones > 0) {
    i = (i + 1) % CELLS;
    if (i === skip) continue; // never seed the opponent's store
    b[i] += 1;
    stones -= 1;
  }
  const last = i;

  const extra = last === store;
  let captured = false;
  // b[last] === 1 means the pit was empty immediately before the final stone
  // (true even when a long sow laps the board).
  if (!extra && ownPit(player, last) && b[last] === 1) {
    const opp = OPPOSITE[last];
    if (b[opp] > 0) {
      b[store] += b[opp] + 1;
      b[opp] = 0;
      b[last] = 0;
      captured = true;
    }
  }
  return { state: b, extra, captured };
}

export function sideEmpty(state, player) {
  return PITS[player].every((p) => state[p] === 0);
}

export function isTerminal(state) {
  return sideEmpty(state, P1_TOP) || sideEmpty(state, P2_BOTTOM);
}

// Sweep every remaining pit stone into its owner's store (end of game).
export function cleanup(state) {
  const b = state.slice();
  for (const player of [P1_TOP, P2_BOTTOM]) {
    const store = STORE[player];
    for (const p of PITS[player]) {
      b[store] += b[p];
      b[p] = 0;
    }
  }
  return b;
}

export function finalStores(state) {
  const b = cleanup(state);
  return [b[STORE[P1_TOP]], b[STORE[P2_BOTTOM]]];
}

export function margin(state, player) {
  const b = cleanup(state);
  return b[STORE[player]] - b[STORE[OPPONENT[player]]];
}

export function winner(state) {
  const [s1, s2] = finalStores(state);
  if (s1 > s2) return P1_TOP;
  if (s2 > s1) return P2_BOTTOM;
  return 0;
}
