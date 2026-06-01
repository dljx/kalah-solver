// Browser-free validation of the web engine and the shipped game logic.
// Run: node tools/check_web.mjs
import {
  initialBoard,
  sow,
  legalMoves,
  isTerminal,
  winner,
} from '../src/engine/board.js';
import { bestMove } from '../src/engine/engine.js';
import { TranspositionTable } from '../src/engine/transposition.js';
import {
  OPPONENT,
  OPP_STORE,
  OPPOSITE,
  P1_TOP,
  P2_BOTTOM,
  WIN_THRESHOLD,
  TERMINAL_SCALE,
} from '../src/engine/constants.js';

let fail = 0;
const check = (cond, msg) => {
  console.log((cond ? 'PASS ' : 'FAIL ') + msg);
  if (!cond) fail += 1;
};
function mkrng(s) {
  s >>>= 0;
  return () => ((s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff);
}

// 1. The animation's sow path reproduces sow()'s distribution (no-capture case).
function sowPath(state, pit, player) {
  const p = [];
  let s = state[pit];
  let i = pit;
  const skip = OPP_STORE[player];
  while (s > 0) {
    i = (i + 1) % 14;
    if (i === skip) continue;
    p.push(i);
    s -= 1;
  }
  return p;
}
{
  const rng = mkrng(42);
  let ok = true;
  for (let t = 0; t < 3000; t++) {
    const cells = new Array(14).fill(0);
    for (let k = 0; k < 4 + Math.floor(rng() * 10); k++) {
      cells[[0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12][Math.floor(rng() * 12)]] += 1;
    }
    for (const player of [P1_TOP, P2_BOTTOM]) {
      for (const pit of legalMoves(cells, player)) {
        const res = sow(cells, pit, player);
        if (res.captured) continue;
        const d = cells.slice();
        d[pit] = 0;
        for (const idx of sowPath(cells, pit, player)) d[idx] += 1;
        if (d.join(',') !== res.state.join(',')) ok = false;
      }
    }
  }
  check(ok, 'animation sow-path matches sow() on 3000 random positions');
}

// 2. A forced winning capture is found and proven instantly.
{
  const s = new Array(14).fill(0);
  s[0] = 1;
  s[11] = 10; // P2's only move captures 10 opposite -> P2 wins 11-0
  const r = bestMove(s, P2_BOTTOM, { mode: 'play', timeMs: 300, tt: new TranspositionTable() });
  check(r.move === 0, `winning capture: move=${r.move} (expect 0)`);
  check(
    r.value >= WIN_THRESHOLD && Math.round(r.value / TERMINAL_SCALE) === 11,
    `winning capture proven: margin=${Math.round(r.value / TERMINAL_SCALE)} (expect 11)`,
  );
}

// 3. The shipped engine path (timed search) never loses as P2 when the opponent
//    starts -- the configuration in which the second player wins Kalah(6,3).
{
  let wins = 0;
  let losses = 0;
  for (let g = 0; g < 8; g++) {
    const tt = new TranspositionTable();
    const rng = mkrng(g + 100);
    let state = initialBoard();
    let player = P1_TOP; // opponent starts
    let guard = 0;
    while (!isTerminal(state) && guard++ < 4000) {
      let mv;
      if (player === P2_BOTTOM) mv = bestMove(state, P2_BOTTOM, { mode: 'play', timeMs: 700, tt }).move;
      else {
        const m = legalMoves(state, P1_TOP);
        mv = m[Math.floor(rng() * m.length)];
      }
      const s = sow(state, mv, player);
      state = s.state;
      if (isTerminal(state)) break;
      if (!s.extra) player = OPPONENT[player];
    }
    const w = winner(state);
    if (w === P2_BOTTOM) wins += 1;
    else if (w === P1_TOP) losses += 1;
  }
  check(losses === 0 && wins === 8, `engine (P2) won ${wins}/8, lost ${losses} vs random`);
}

console.log(fail ? `\n${fail} FAILURE(S)` : '\nALL CHECKS PASS');
process.exit(fail ? 1 : 0);
