"""Vertical Kalah(6,3) solver package.

Public API re-exported from :mod:`kalah.engine`.
"""

from .engine import (
    best_move,
    analyze,
    initial_board,
    legal_moves,
    sow,
    is_terminal,
    cleanup,
    winner,
    margin,
    search,
    solve,
    P1_TOP,
    P2_BOTTOM,
)

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
