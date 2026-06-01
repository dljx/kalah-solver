"""Negamax + alpha-beta search for Kalah(6,3).

Two entry points share one core:
  * ``search`` - iterative deepening to a time budget, heuristic leaves at the
    horizon (the faithful port of the reference engine).
  * ``solve``  - exact: a shallow ordering pre-pass, then a search to terminal
    that trusts only terminal-derived ("exact") results, so its answer is the
    true game-theoretic value. This is what makes the engine provably optimal.

The crux vs. the reference is Kalah's *extra turn*. Vanilla negamax assumes the
side to move alternates every ply, so it flips sign and negates the window on
every recursion. Here a sow whose last stone lands in the mover's own store
keeps the SAME player on move, so we must NOT flip in that case:

    terminal child : value = margin(child, player)            # game over
    extra turn     : value =  negamax(child, player, ...)     # no flip
    turn passes    : value = -negamax(child, opp,    a/b neg) # reference flip

Both the terminal and turn-passing paths agree because ``margin`` is
antisymmetric, so a terminal child is scored correctly whichever branch reaches
it.

Exactness with move ordering: a shallow depth-capped pre-pass seeds good moves
into the TT (ordering never affects correctness). The final pass is depth-capped
off, so its only leaves are terminal -> every value it produces is terminal-
exact. It trusts only ``exact`` TT entries for cutoffs, so a heuristic estimate
from the pre-pass can never corrupt the proven result.
"""

import sys
import time

from .constants import (
    INF,
    TERMINAL_SCALE,
    WIN_THRESHOLD,
    MAX_DEPTH,
    ORDER_DEPTH,
    TIME_BUDGET_MS,
    OPPONENT,
    STORE,
)
from .board import legal_moves, sow, is_terminal, margin
from .evaluate import evaluate
from .transposition import (
    TranspositionTable,
    EXACT,
    LOWER,
    UPPER,
    I_VALUE,
    I_FLAG,
    I_MOVE,
    I_EXACT,
)

# Long extra-turn chains can make the game tree deep; give the recursion room.
sys.setrecursionlimit(1_000_000)


class _Timeout(Exception):
    """Raised to abandon a search iteration that ran past its deadline."""


class _Ctx:
    """Per-search mutable state threaded through the recursion."""

    __slots__ = ("tt", "nodes", "deadline", "depth_cap")

    def __init__(self, tt, deadline, depth_cap):
        self.tt = tt
        self.nodes = 0
        self.deadline = deadline
        self.depth_cap = depth_cap


def terminal_value(state, player, ply):
    """Score of a finished game from ``player``'s view.

    Scaled so it dominates any heuristic leaf; a tiny ply term prefers faster
    wins and slower losses (sign-aware so both players push the result the right
    way -- the relation survives negamax's negation).
    """
    m = margin(state, player)
    if m > 0:
        return m * TERMINAL_SCALE - ply
    if m < 0:
        return m * TERMINAL_SCALE + ply
    return 0


def _ordered_children(state, player, tt_move):
    """Sow every legal move once and order the resulting children.

    Order (affects pruning speed only, never the result): the TT's best move
    first, then extra-turn moves, then captures, then by how many stones the
    move banks in our own store. Banking-heavy moves tend to be strongest, so
    trying them first produces sharp alpha-beta cutoffs.
    """
    store = STORE[player]
    children = []
    for pit in legal_moves(state, player):
        child, extra, captured = sow(state, pit, player)
        children.append((pit, child, extra, captured))
    children.sort(
        key=lambda c: (c[0] == tt_move, c[2], c[3], c[1][store]), reverse=True
    )
    return children


def negamax(state, player, depth, alpha, beta, ply, ctx):
    """Return ``(value, best_move, exact)`` for ``player`` to move in ``state``.

    ``exact`` is True when ``value`` derives only from terminal leaves (a true
    bound on the real game value, independent of depth).
    """
    ctx.nodes += 1

    if ctx.deadline is not None and time.monotonic() >= ctx.deadline:
        raise _Timeout

    # Terminal is a true leaf at any depth -- check it before the horizon.
    if is_terminal(state):
        return terminal_value(state, player, ply), None, True
    if ctx.depth_cap and depth <= 0:
        return evaluate(state, player), None, False  # heuristic estimate

    alpha_orig = alpha
    key = (state, player)
    entry = ctx.tt.get(key)
    tt_move = None
    if entry is not None:
        e_value, e_depth, e_flag, e_move, e_exact = entry
        tt_move = e_move
        # Trust a stored value when it is terminal-exact (depth-independent) or,
        # in depth-capped mode, when it was searched at least this deep.
        if e_exact or (ctx.depth_cap and e_depth >= depth):
            if e_flag == EXACT:
                return e_value, e_move, e_exact
            if e_flag == LOWER and e_value > alpha:
                alpha = e_value
            elif e_flag == UPPER and e_value < beta:
                beta = e_value
            if alpha >= beta:
                return e_value, e_move, e_exact

    best = -INF
    best_move = None
    node_exact = True
    for pit, child, extra, captured in _ordered_children(state, player, tt_move):
        if extra:
            score, _, child_exact = negamax(
                child, player, depth - 1, alpha, beta, ply + 1, ctx
            )
        else:
            score, _, child_exact = negamax(
                child, OPPONENT[player], depth - 1, -beta, -alpha, ply + 1, ctx
            )
            score = -score
        if not child_exact:
            node_exact = False
        if score > best:
            best = score
            best_move = pit
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break  # beta cutoff

    flag = EXACT
    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta:
        flag = LOWER
    ctx.tt.set(key, best, depth, flag, best_move, node_exact)
    return best, best_move, node_exact


def search(state, player, max_depth=MAX_DEPTH, time_budget_ms=TIME_BUDGET_MS, tt=None):
    """Iterative-deepening search to a time budget.

    Returns ``{"move", "value", "depth", "nodes"}``. Keeps the result of the last
    fully completed depth when the deadline interrupts a deeper one.
    """
    tt = tt if tt is not None else TranspositionTable()
    deadline = time.monotonic() + time_budget_ms / 1000 if time_budget_ms > 0 else None
    ctx = _Ctx(tt, deadline, depth_cap=True)

    legal = legal_moves(state, player)
    best_move = legal[0] if legal else None
    best_value = 0
    reached = 0

    for depth in range(1, max_depth + 1):
        try:
            value, move, _ = negamax(state, player, depth, -INF, INF, 0, ctx)
        except _Timeout:
            break
        best_move, best_value, reached = move, value, depth
        if abs(best_value) >= WIN_THRESHOLD:
            break  # proven win/loss -- deeper search cannot change it
        if len(legal) <= 1:
            break

    return {"move": best_move, "value": best_value, "depth": reached, "nodes": ctx.nodes}


def solve(state, player, tt=None, order_depth=ORDER_DEPTH):
    """Exact search to terminal; returns ``{"move", "value", "nodes"}``.

    ``value`` is the true final store margin under optimal play (scaled by
    ``TERMINAL_SCALE``): positive = win for ``player``, 0 = draw, negative = loss.
    A shallow depth-capped pre-pass seeds move ordering before the exact pass.
    """
    tt = tt if tt is not None else TranspositionTable()

    # Warm start: a persistent TT (book / verifier / repeated play) may already
    # hold the proven answer, making this call O(1).
    cached = tt.get((state, player))
    if cached is not None and cached[I_EXACT] and cached[I_FLAG] == EXACT:
        return {"move": cached[I_MOVE], "value": cached[I_VALUE], "nodes": 0}

    pre = _Ctx(tt, deadline=None, depth_cap=True)
    for d in range(1, order_depth + 1):
        negamax(state, player, d, -INF, INF, 0, pre)

    final = _Ctx(tt, deadline=None, depth_cap=False)
    value, move, _ = negamax(state, player, MAX_DEPTH, -INF, INF, 0, final)
    return {"move": move, "value": value, "nodes": pre.nodes + final.nodes}
