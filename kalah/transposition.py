"""Transposition table: caches search results keyed by ``(state, side_to_move)``.

Because the state is an immutable 14-int tuple, the key is hashable for free and
collision-proof -- no Zobrist hashing needed. Two positions with identical pits
but a different player to move are distinct keys.

Each entry is ``(value, depth, flag, move, exact)``:
  * flag describes how ``value`` relates to the (depth-bounded) score:
      EXACT - value is the exact score
      LOWER - value is a lower bound (a beta cutoff happened)
      UPPER - value is an upper bound (no move beat alpha)
  * ``exact`` (terminal-exact) marks a value derived only from terminal leaves,
    i.e. a true bound on the real game value independent of search depth. The
    exact solver trusts only these for cutoffs, so heuristic horizon estimates
    from a shallow ordering pass can never corrupt a proven result.
"""

EXACT = 0
LOWER = 1
UPPER = 2

# Entry tuple indices.
I_VALUE, I_DEPTH, I_FLAG, I_MOVE, I_EXACT = range(5)


class TranspositionTable:
    """A thin dict wrapper; instantiated per search (no global state)."""

    def __init__(self):
        self._map = {}

    def get(self, key):
        """Return the entry ``(value, depth, flag, move, exact)`` or ``None``."""
        return self._map.get(key)

    def set(self, key, value, depth, flag, move, exact):
        existing = self._map.get(key)
        if existing is not None:
            if existing[I_EXACT] and not exact:
                return  # never downgrade a terminal-exact entry
            if existing[I_EXACT] == exact and existing[I_DEPTH] > depth:
                return  # same class: keep the result searched deeper
        self._map[key] = (value, depth, flag, move, exact)

    def clear(self):
        self._map.clear()

    def __len__(self):
        return len(self._map)

    @property
    def size(self):
        return len(self._map)
