"""Immutable game state and rules for vertical Kalah(6,3).

State is a 14-int ``tuple`` (see ``constants`` for the layout). Every function is
pure: ``sow`` returns a brand-new tuple, so states are hashable and safe to use
directly as transposition-table keys. We deliberately use immutable tuples
instead of the reference engine's make/unmake mutation -- in Python a tuple is
hashable for free, which makes the TT key trivial and collision-proof.
"""

from .constants import (
    CELLS,
    P1_TOP,
    P2_BOTTOM,
    OPPONENT,
    STORE,
    OPP_STORE,
    PITS,
    OWN_PITS_RANGE,
    OPPOSITE,
    INITIAL_BOARD,
)


def initial_board():
    """The starting position: every pit holds 3 stones, both stores empty."""
    return INITIAL_BOARD


def legal_moves(state, player):
    """Pits on ``player``'s side that contain at least one stone."""
    return [p for p in PITS[player] if state[p] > 0]


def sow(state, pit, player):
    """Play ``pit`` for ``player``; sow counter-clockwise.

    Returns ``(new_state, extra_turn, captured)``:
      * ``extra_turn`` -- the last stone landed in the player's own store.
      * ``captured``   -- the last stone landed in a previously-empty own pit
                          facing a non-empty opposite pit (an empty capture).
    A player never seeds the opponent's store (it is skipped while sowing).
    """
    if pit not in OWN_PITS_RANGE[player]:
        raise ValueError(f"pit {pit} is not on player {player}'s side")
    board = list(state)
    stones = board[pit]
    if stones == 0:
        raise ValueError(f"cannot sow from empty pit {pit}")

    board[pit] = 0
    store = STORE[player]
    skip = OPP_STORE[player]

    i = pit
    while stones > 0:
        i = (i + 1) % CELLS
        if i == skip:          # never place a stone in the opponent's store
            continue
        board[i] += 1
        stones -= 1
    last = i

    extra_turn = last == store
    captured = False
    # Empty capture: the final stone fell into an own-side pit that was empty
    # before it landed. ``board[last] == 1`` is exactly that test -- the only way
    # to end at 1 is to have been 0 immediately before the final stone (true even
    # if a long sow lapped the board).
    if not extra_turn and last in OWN_PITS_RANGE[player] and board[last] == 1:
        opp_pit = OPPOSITE[last]
        if board[opp_pit] > 0:
            board[store] += board[opp_pit] + 1
            board[opp_pit] = 0
            board[last] = 0
            captured = True

    return tuple(board), extra_turn, captured


def _side_empty(state, player):
    return not any(state[p] for p in PITS[player])


def is_terminal(state):
    """The game ends the instant either player's column of pits is empty."""
    return _side_empty(state, P1_TOP) or _side_empty(state, P2_BOTTOM)


def cleanup(state):
    """Sweep every remaining pit stone into its owner's store.

    Called on terminal states: the side that still holds stones banks them. The
    already-empty side contributes nothing, so sweeping both sides is equivalent
    and simpler.
    """
    board = list(state)
    for player in (P1_TOP, P2_BOTTOM):
        store = STORE[player]
        for p in PITS[player]:
            board[store] += board[p]
            board[p] = 0
    return tuple(board)


def final_stores(state):
    """``(store_p1, store_p2)`` after end-of-game cleanup."""
    board = cleanup(state)
    return board[STORE[P1_TOP]], board[STORE[P2_BOTTOM]]


def margin(state, player):
    """Final store differential from ``player``'s perspective (after cleanup)."""
    board = cleanup(state)
    return board[STORE[player]] - board[STORE[OPPONENT[player]]]


def winner(state):
    """Return the winning player (1 or 2) after cleanup, or 0 for a draw."""
    s1, s2 = final_stores(state)
    if s1 > s2:
        return P1_TOP
    if s2 > s1:
        return P2_BOTTOM
    return 0
