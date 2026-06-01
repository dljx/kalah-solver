"""Heuristic leaf evaluation for the time-limited search mode.

Returns a score from the side-to-move's perspective (positive = good for the
player to move), so it slots straight into negamax. Three terms, in priority
order per the spec:

  * store differential  -- by far the most important (stones already banked)
  * board control       -- stones sitting on my side vs the opponent's
  * extra-turn pressure  -- pits poised to land their last stone in my store

Magnitudes stay well below ``TERMINAL_SCALE`` so a proven win/loss always
outranks any heuristic estimate.
"""

from .constants import (
    OPPONENT,
    STORE,
    PITS,
    DIST_TO_STORE,
    WEIGHTS,
)


def _extra_turn_ready(state, player):
    """How many of ``player``'s pits would grant an extra turn if played now."""
    dist = DIST_TO_STORE[player]
    return sum(1 for p in PITS[player] if state[p] == dist[p])


def evaluate(state, player):
    """Static score of ``state`` from ``player``'s point of view."""
    opp = OPPONENT[player]

    store_diff = state[STORE[player]] - state[STORE[opp]]
    control = sum(state[p] for p in PITS[player]) - sum(state[p] for p in PITS[opp])
    extra = _extra_turn_ready(state, player) - _extra_turn_ready(state, opp)

    return (
        WEIGHTS["store"] * store_diff
        + WEIGHTS["control"] * control
        + WEIGHTS["extra_turn"] * extra
    )
