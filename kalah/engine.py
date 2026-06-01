"""Public engine API: pick the best move for a position.

Thin orchestration over the search core, mirroring the reference engine's
``engine.js``. Two modes:
  * ``"solve"`` - exact, provably optimal (search to terminal).
  * ``"play"``  - consult the perfect-play book if loaded, else iterative
                  deepening to a time budget.
"""

from .constants import MAX_DEPTH, TIME_BUDGET_MS, P1_TOP, P2_BOTTOM
from .board import (
    initial_board,
    legal_moves,
    sow,
    is_terminal,
    cleanup,
    winner,
    margin,
)
from .search import search, solve
from .transposition import TranspositionTable
from . import book


def best_move(state, player, mode="play", **opts):
    """Return ``{"move", "value", "source", ...}`` for ``player`` in ``state``.

    ``mode="solve"`` always computes the exact answer. ``mode="play"`` prefers a
    book hit, then falls back to a time-limited search.
    """
    if is_terminal(state):
        return {"move": None, "value": margin(state, player), "source": "terminal"}

    if mode == "solve":
        result = solve(state, player, tt=opts.get("tt"))
        result["source"] = "solve"
        return result

    bm = book.book_move(state, player)
    if bm is not None:
        return {"move": bm, "value": None, "source": "book"}

    result = search(
        state,
        player,
        max_depth=opts.get("max_depth", MAX_DEPTH),
        time_budget_ms=opts.get("time_budget_ms", TIME_BUDGET_MS),
        tt=opts.get("tt"),
    )
    result["source"] = "search"
    return result


def analyze(state, player, mode="play", **opts):
    """Like :func:`best_move` but also reports transposition-table size."""
    tt = opts.pop("tt", None) or TranspositionTable()
    result = best_move(state, player, mode=mode, tt=tt, **opts)
    result["tt_size"] = tt.size
    return result


__all__ = [
    "best_move",
    "analyze",
    "initial_board",
    "legal_moves",
    "sow",
    "is_terminal",
    "cleanup",
    "winner",
    "margin",
    "search",
    "solve",
    "P1_TOP",
    "P2_BOTTOM",
]
