// Heuristic leaf evaluation for the time-limited search. JS port of
// kalah/evaluate.py. Score is from the side-to-move's perspective.

import { OPPONENT, STORE, PITS, DIST_TO_STORE, WEIGHTS } from './constants.js';

function extraTurnReady(state, player) {
  const dist = DIST_TO_STORE[player];
  let n = 0;
  for (const p of PITS[player]) if (state[p] === dist[p]) n += 1;
  return n;
}

export function evaluate(state, player) {
  const opp = OPPONENT[player];
  const storeDiff = state[STORE[player]] - state[STORE[opp]];

  let mine = 0;
  let theirs = 0;
  for (const p of PITS[player]) mine += state[p];
  for (const p of PITS[opp]) theirs += state[p];
  const control = mine - theirs;

  const extra = extraTurnReady(state, player) - extraTurnReady(state, opp);

  return (
    WEIGHTS.store * storeDiff +
    WEIGHTS.control * control +
    WEIGHTS.extraTurn * extra
  );
}
