"""Tests for the public engine API: mode dispatch, book hits, terminal handling,
and the guarantee that exact play never loses from the theoretically winning seat."""

import random
import unittest

from kalah import engine
from kalah import board
from kalah import book
from kalah.transposition import TranspositionTable
from kalah.constants import WIN_THRESHOLD, P1_TOP, P2_BOTTOM, OPPONENT


def make(overrides):
    cells = [0] * 14
    for i, v in overrides.items():
        cells[i] = v
    return tuple(cells)


def play_out(start, ai_seat, ai_mode, rng, ai_opts):
    """Play one full game from ``start``; AI holds ``ai_seat``, opponent random.

    Honors extra turns (the same player keeps moving). Returns the winner.
    """
    state = start
    player = P1_TOP  # P1 (Top) moves first by convention
    while not board.is_terminal(state):
        if player == ai_seat:
            move = engine.best_move(state, player, mode=ai_mode, **ai_opts)["move"]
        else:
            move = rng.choice(board.legal_moves(state, player))
        state, extra, _ = board.sow(state, move, player)
        if board.is_terminal(state):
            break
        if not extra:
            player = OPPONENT[player]
    return board.winner(state)


class TestEngineAPI(unittest.TestCase):
    def tearDown(self):
        book.set_book(None)  # never leak a book between tests

    def test_play_returns_legal_move(self):
        b = board.initial_board()
        result = engine.best_move(b, P1_TOP, mode="play", time_budget_ms=200)
        self.assertIn(result["move"], board.legal_moves(b, P1_TOP))
        self.assertEqual(result["source"], "search")

    def test_solve_returns_exact_value_and_legal_move(self):
        state = make({0: 1, 11: 10})  # forced winning capture for P2
        result = engine.best_move(state, P2_BOTTOM, mode="solve")
        self.assertEqual(result["move"], 0)
        self.assertGreater(result["value"], WIN_THRESHOLD)
        self.assertEqual(result["source"], "solve")

    def test_book_hit_is_used(self):
        b = board.initial_board()
        book.set_book({book.key_for(b, P1_TOP): [9, 0]})
        result = engine.best_move(b, P1_TOP, mode="play")
        self.assertEqual(result["move"], 9)
        self.assertEqual(result["source"], "book")

    def test_terminal_state_has_no_move(self):
        state = make({6: 18, 13: 18})
        result = engine.best_move(state, P2_BOTTOM, mode="play")
        self.assertIsNone(result["move"])
        self.assertEqual(result["source"], "terminal")

    def test_analyze_reports_tt_size(self):
        state = make({0: 1, 11: 10})
        result = engine.analyze(state, P2_BOTTOM, mode="solve")
        self.assertIn("tt_size", result)
        self.assertGreaterEqual(result["tt_size"], 1)


class TestExactPlayNeverLoses(unittest.TestCase):
    """Exact play must never lose from a theoretically winning seat.

    Uses the 1-stone-per-pit variant (first player wins) so the proof is fast; a
    shared TT keeps repeated solves O(1). The full Kalah(6,3) result -- second
    player wins -- is verified by ``tools/solve.py`` and ``tests/test_solve``.
    """

    def test_exact_first_player_always_wins_small_game(self):
        start = tuple([1] * 6 + [0] + [1] * 6 + [0])
        tt = TranspositionTable()
        rng = random.Random(99)
        for _ in range(25):
            winner = play_out(start, P1_TOP, "solve", rng, {"tt": tt})
            self.assertEqual(winner, P1_TOP, "exact P1 failed to win the 1-stone game")


if __name__ == "__main__":
    unittest.main()
