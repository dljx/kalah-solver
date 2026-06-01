"""Perfect-play book: an optional precomputed map of position -> optimal move.

This is the Kalah analogue of the reference engine's opening book. It is filled
offline by ``tools/solve.py`` (which solves the game exactly) and lets the engine
answer instantly with provably optimal moves instead of searching.

Keys are JSON strings ``"<player>:<comma-separated-cells>"`` so the map survives
a round-trip through JSON (whose object keys must be strings).
"""

import json

_BOOK = None


def key_for(state, player):
    """Stable string key for ``(state, player)`` usable as a JSON object key."""
    return f"{player}:" + ",".join(str(c) for c in state)


def set_book(mapping):
    """Install a book dict directly (used by the solver tool and tests)."""
    global _BOOK
    _BOOK = mapping


def has_book():
    return _BOOK is not None


def load_book(path):
    """Load a book JSON from ``path``; missing/invalid file installs an empty book."""
    global _BOOK
    try:
        with open(path, "r", encoding="utf-8") as fh:
            _BOOK = json.load(fh)
    except (OSError, ValueError):
        _BOOK = {}
    return _BOOK


def book_move(state, player):
    """Optimal move from the book for ``(state, player)``, or ``None`` if absent."""
    if not _BOOK:
        return None
    entry = _BOOK.get(key_for(state, player))
    if entry is None:
        return None
    # Stored either as a bare move or as ``[move, value]``.
    return entry[0] if isinstance(entry, list) else entry
