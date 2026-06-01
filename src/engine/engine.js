// Public engine API: pick the best move for a position. JS port of kalah/engine.py.
//   mode: "solve" -> exact/perfect ; "play" -> time-limited search.
// A loaded book is consulted first in any mode (book moves are proven optimal).

import { MAX_DEPTH, TIME_BUDGET_MS } from './constants.js';
import { isTerminal, margin } from './board.js';
import { search, solve } from './search.js';
import { TranspositionTable } from './transposition.js';
import { bookMove } from './book.js';

export function bestMove(state, player, opts = {}) {
  if (isTerminal(state)) {
    return { move: -1, value: margin(state, player), source: 'terminal' };
  }
  const booked = bookMove(state, player);
  if (booked >= 0) return { move: booked, value: null, source: 'book' };

  if (opts.mode === 'solve') {
    const r = solve(state, player, { tt: opts.tt });
    r.source = 'solve';
    return r;
  }
  const r = search(state, player, {
    maxDepth: opts.maxDepth ?? MAX_DEPTH,
    timeMs: opts.timeMs ?? TIME_BUDGET_MS,
    tt: opts.tt,
  });
  r.source = 'search';
  return r;
}

export function analyze(state, player, opts = {}) {
  const tt = opts.tt || new TranspositionTable();
  const r = bestMove(state, player, { ...opts, tt });
  r.ttSize = tt.size;
  return r;
}

export { search, solve } from './search.js';
export {
  initialBoard,
  legalMoves,
  sow,
  isTerminal,
  cleanup,
  winner,
  margin,
  finalStores,
} from './board.js';
export {
  P1_TOP,
  P2_BOTTOM,
  OPPONENT,
  PITS,
  STORE,
  OPP_STORE,
  OPPOSITE,
  CELLS,
  WIN_THRESHOLD,
  TERMINAL_SCALE,
} from './constants.js';
