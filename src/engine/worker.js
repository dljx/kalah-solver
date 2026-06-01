// Web Worker: runs the search off the main thread so the UI stays responsive.
//
// The browser engine is a time-bounded iterative-deepening search. It plays very
// strongly everywhere and returns the provably exact result whenever it proves a
// win/loss/draw within the budget -- which it does quickly once the board
// simplifies (iterative deepening breaks early on a proven score). A capped,
// persistent transposition table keeps memory bounded and warm across moves; the
// UI resets it on a new game. A shipped opening book (if loaded) gives instant,
// perfect early moves.

import { bestMove } from './engine.js';
import { bookMove } from './book.js';
import { TranspositionTable } from './transposition.js';

const tt = new TranspositionTable();

self.onmessage = (e) => {
  const msg = e.data || {};
  if (msg.type === 'reset') {
    tt.clear();
    return;
  }
  const { state, player, timeMs = 1500 } = msg;

  const booked = bookMove(state, player);
  if (booked >= 0) {
    self.postMessage({ move: booked, value: null, source: 'book' });
    return;
  }
  self.postMessage(bestMove(state, player, { mode: 'play', timeMs, tt }));
};
