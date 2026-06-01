// Negamax + alpha-beta search for Kalah(6,3). JS port of kalah/search.py.
//
//   search() – iterative deepening to a time budget (heuristic leaves)
//   solve()  – exact: a shallow ordering pre-pass, then a search to terminal
//              that trusts only terminal-`exact` results. Accepts an optional
//              `maxNodes` budget: if the position is too big to solve within it
//              the call aborts (returns { aborted:true }) so the caller can fall
//              back to a time-limited search. This keeps the browser bounded —
//              an unbounded exact solve of the opening needs >16.7M states.
//
// Kalah's extra turn breaks negamax's alternation assumption, so the recursion
// branches: a turn-passing move flips sign + window (-negamax(child, opp,-b,-a));
// an extra-turn move does NOT (+negamax(child, player, a, b)).

import {
  INF,
  TERMINAL_SCALE,
  WIN_THRESHOLD,
  MAX_DEPTH,
  ORDER_DEPTH,
  TIME_BUDGET_MS,
  OPPONENT,
  STORE,
} from './constants.js';
import { legalMoves, sow, isTerminal, margin } from './board.js';
import { evaluate } from './evaluate.js';
import { TranspositionTable, EXACT, LOWER, UPPER } from './transposition.js';

const TIMEOUT = Symbol('timeout');
const NODE_LIMIT = Symbol('node-limit');

// Compact, collision-proof key: one char for the player + one per cell.
const keyOf = (state, player) => String.fromCharCode(player, ...state);

export function terminalValue(state, player, ply) {
  const m = margin(state, player);
  if (m > 0) return m * TERMINAL_SCALE - ply; // prefer faster wins
  if (m < 0) return m * TERMINAL_SCALE + ply; // prefer slower losses
  return 0;
}

function orderedChildren(state, player, ttMove) {
  const store = STORE[player];
  const children = [];
  for (const pit of legalMoves(state, player)) {
    const r = sow(state, pit, player);
    // rank: TT move >> extra-turn >> capture >> stones banked (ordering only)
    const rank =
      (pit === ttMove ? 1e6 : 0) +
      (r.extra ? 1e4 : 0) +
      (r.captured ? 1e2 : 0) +
      r.state[store];
    children.push({ pit, child: r.state, extra: r.extra, rank });
  }
  children.sort((a, b) => b.rank - a.rank);
  return children;
}

function negamax(state, player, depth, alpha, beta, ply, ctx) {
  ctx.nodes += 1;
  if (ctx.maxNodes !== 0 && ctx.nodes > ctx.maxNodes) throw NODE_LIMIT;
  if (
    ctx.deadline !== null &&
    (ctx.nodes & 2047) === 0 &&
    performance.now() >= ctx.deadline
  ) {
    throw TIMEOUT;
  }

  // Terminal is a true leaf at any depth -- check before the horizon.
  if (isTerminal(state)) {
    return { value: terminalValue(state, player, ply), move: -1, exact: true };
  }
  if (ctx.depthCap && depth <= 0) {
    return { value: evaluate(state, player), move: -1, exact: false };
  }

  const alphaOrig = alpha;
  const key = keyOf(state, player);
  const entry = ctx.tt.get(key);
  let ttMove = -1;
  if (entry !== undefined) {
    ttMove = entry.move;
    if (entry.exact || (ctx.depthCap && entry.depth >= depth)) {
      if (entry.flag === EXACT) {
        return { value: entry.value, move: entry.move, exact: entry.exact };
      }
      if (entry.flag === LOWER && entry.value > alpha) alpha = entry.value;
      else if (entry.flag === UPPER && entry.value < beta) beta = entry.value;
      if (alpha >= beta) {
        return { value: entry.value, move: entry.move, exact: entry.exact };
      }
    }
  }

  let best = -INF;
  let bestMove = -1;
  let nodeExact = true;
  for (const c of orderedChildren(state, player, ttMove)) {
    let score;
    if (c.extra) {
      const r = negamax(c.child, player, depth - 1, alpha, beta, ply + 1, ctx);
      score = r.value;
      if (!r.exact) nodeExact = false;
    } else {
      const r = negamax(c.child, OPPONENT[player], depth - 1, -beta, -alpha, ply + 1, ctx);
      score = -r.value;
      if (!r.exact) nodeExact = false;
    }
    if (score > best) {
      best = score;
      bestMove = c.pit;
    }
    if (best > alpha) alpha = best;
    if (alpha >= beta) break; // beta cutoff
  }

  let flag = EXACT;
  if (best <= alphaOrig) flag = UPPER;
  else if (best >= beta) flag = LOWER;
  ctx.tt.set(key, best, depth, flag, bestMove, nodeExact);
  return { value: best, move: bestMove, exact: nodeExact };
}

export function search(state, player, opts = {}) {
  const { maxDepth = MAX_DEPTH, timeMs = TIME_BUDGET_MS, tt = null } = opts;
  const table = tt || new TranspositionTable();
  const deadline = timeMs > 0 ? performance.now() + timeMs : null;
  const ctx = { tt: table, nodes: 0, deadline, depthCap: true, maxNodes: 0 };

  const legal = legalMoves(state, player);
  let bestMove = legal.length ? legal[0] : -1;
  let bestValue = 0;
  let reached = 0;

  for (let depth = 1; depth <= maxDepth; depth++) {
    try {
      const r = negamax(state, player, depth, -INF, INF, 0, ctx);
      bestMove = r.move;
      bestValue = r.value;
      reached = depth;
    } catch (e) {
      if (e === TIMEOUT) break;
      throw e;
    }
    if (Math.abs(bestValue) >= WIN_THRESHOLD) break; // proven
    if (legal.length <= 1) break;
  }
  return { move: bestMove, value: bestValue, depth: reached, nodes: ctx.nodes };
}

export function solve(state, player, opts = {}) {
  const { tt = null, orderDepth = ORDER_DEPTH, maxNodes = 0 } = opts;
  const table = tt || new TranspositionTable();

  // Warm start: a persistent TT may already hold the proven answer.
  const cached = table.get(keyOf(state, player));
  if (cached !== undefined && cached.exact && cached.flag === EXACT) {
    return { move: cached.move, value: cached.value, nodes: 0 };
  }

  // One context across both passes so `maxNodes` bounds the whole solve.
  const ctx = { tt: table, nodes: 0, deadline: null, depthCap: true, maxNodes };
  try {
    for (let d = 1; d <= orderDepth; d++) {
      negamax(state, player, d, -INF, INF, 0, ctx);
    }
    ctx.depthCap = false;
    const r = negamax(state, player, MAX_DEPTH, -INF, INF, 0, ctx);
    return { move: r.move, value: r.value, nodes: ctx.nodes };
  } catch (e) {
    if (e === NODE_LIMIT) return { move: -1, value: 0, nodes: ctx.nodes, aborted: true };
    throw e;
  }
}
