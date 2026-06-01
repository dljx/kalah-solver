"""Board geometry, player maps, and tunable constants for vertical Kalah(6,3).

Receptacle layout (14 cells, a vertical 2-column / 6-row grid):

      indices            owner
    ---------------------------------------------
    0..5    left column   Player 2 (Bottom / AI) pits, descending to the store
    6       bottom store  Player 2's store
    7..12   right column  Player 1 (Top / Opponent) pits, ascending to the store
    13      top store     Player 1's store

The index order 0,1,...,13 was chosen so that counter-clockwise sowing is simply
``next = (i + 1) % 14`` -- a player only ever *skips the opponent's store*.
"""

# --- Dimensions -------------------------------------------------------------
NUM_PITS = 6
STONES_PER_PIT = 3
CELLS = 14

# --- Players ----------------------------------------------------------------
P1_TOP = 1      # Top / Opponent
P2_BOTTOM = 2   # Bottom / Me (the AI's default seat)

OPPONENT = {P1_TOP: P2_BOTTOM, P2_BOTTOM: P1_TOP}

# Each player's own store, the opponent store they must skip, and their pits.
STORE = {P1_TOP: 13, P2_BOTTOM: 6}
OPP_STORE = {P1_TOP: 6, P2_BOTTOM: 13}
PITS = {P1_TOP: (7, 8, 9, 10, 11, 12), P2_BOTTOM: (0, 1, 2, 3, 4, 5)}

# O(1) "is this pit on my side?" tests for the sowing hot path.
OWN_PITS_RANGE = {P1_TOP: range(7, 13), P2_BOTTOM: range(0, 6)}

# Capture pairing: the pit directly opposite pit ``i`` (0<->12, 1<->11, ... 5<->7).
# Valid for pit indices 0..12; stores are never used as an opposite.
OPPOSITE = tuple(12 - i for i in range(13))

# All twelve pits start with three stones; both stores start empty.
INITIAL_BOARD = (3, 3, 3, 3, 3, 3, 0, 3, 3, 3, 3, 3, 3, 0)


def distance_to_store(pit, player):
    """Number of sowing steps from ``pit`` until a stone lands in the player's store."""
    store = STORE[player]
    skip = OPP_STORE[player]
    d = 0
    i = pit
    while True:
        i = (i + 1) % CELLS
        if i == skip:
            continue
        d += 1
        if i == store:
            return d


# Precomputed pit -> steps-to-own-store, per player (used by the heuristic).
DIST_TO_STORE = {
    player: {pit: distance_to_store(pit, player) for pit in PITS[player]}
    for player in (P1_TOP, P2_BOTTOM)
}

# --- Search / scoring constants --------------------------------------------
INF = 10**9

# A terminal result is the final store margin scaled so it dominates any
# heuristic leaf value; a tiny ply term then prefers faster wins / slower losses.
TERMINAL_SCALE = 10_000
DRAW_SCORE = 0
# |score| >= WIN_THRESHOLD  =>  a proven win/loss (never reachable by the heuristic).
WIN_THRESHOLD = TERMINAL_SCALE - 1_000

# Heuristic weights (timed mode only). Store differential dominates; board
# control and pending extra-turns are secondary. Kept well below TERMINAL_SCALE.
WEIGHTS = {"store": 100, "control": 2, "extra_turn": 6}

# Search defaults.
MAX_DEPTH = 64
TIME_BUDGET_MS = 1000
# Depth of the shallow move-ordering pre-pass that primes the exact solver.
ORDER_DEPTH = 12
