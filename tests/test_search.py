"""Search tests: exact solve of hand-verified tactics (capture, extra-turn
chains, terminal precedence) and time-limited search behaviour."""

import unittest

from kalah import board
from kalah.search import search, solve
from kalah.constants import WIN_THRESHOLD, P1_TOP, P2_BOTTOM


def make(overrides):
    cells = [0] * 14
    for i, v in overrides.items():
        cells[i] = v
    return tuple(cells)


class TestSolveTactics(unittest.TestCase):
    def test_winning_capture(self):
        # P2's only move (pit 0) sows into empty pit 1, capturing the 10 stones
        # opposite (pit 11). Both sides then empty -> P2 wins 11-0.
        state = make({0: 1, 11: 10})
        result = solve(state, P2_BOTTOM)
        self.assertEqual(result["move"], 0)
        self.assertGreater(result["value"], WIN_THRESHOLD)

    def test_beneficial_extra_turn_chain(self):
        # pit 4 (2 stones) -> pit5, store (extra turn); then pit5 -> store (extra
        # turn); P2 side empties -> P2 wins 2-1. The extra-turn handling must
        # keep the same player on move without flipping.
        state = make({4: 2, 7: 1})
        result = solve(state, P2_BOTTOM)
        self.assertEqual(result["move"], 4)
        self.assertGreater(result["value"], WIN_THRESHOLD)

    def test_extra_turn_that_ends_game_is_a_loss(self):
        # P2's only move banks one stone (extra turn) but empties P2's side ->
        # terminal takes precedence, P1 sweeps 3 -> P2 loses 1-3.
        state = make({5: 1, 7: 3})
        result = solve(state, P2_BOTTOM)
        self.assertEqual(result["move"], 5)
        self.assertLess(result["value"], -WIN_THRESHOLD)

    def test_forced_single_move(self):
        state = make({2: 4, 7: 3, 8: 2})
        result = solve(state, P2_BOTTOM)
        self.assertEqual(result["move"], 2)


class TestSearchBehaviour(unittest.TestCase):
    def test_returns_legal_move_within_budget(self):
        b = board.initial_board()
        result = search(b, P1_TOP, time_budget_ms=300)
        self.assertIn(result["move"], board.legal_moves(b, P1_TOP))
        self.assertGreaterEqual(result["depth"], 1)
        self.assertGreater(result["nodes"], 0)

    def test_search_agrees_with_solve_on_tactic(self):
        state = make({0: 1, 11: 10})
        s = search(state, P2_BOTTOM, time_budget_ms=500)
        self.assertEqual(s["move"], 0)
        self.assertGreater(s["value"], WIN_THRESHOLD)

    def test_initial_search_is_deterministic(self):
        b = board.initial_board()
        a = search(b, P1_TOP, max_depth=6, time_budget_ms=0)
        c = search(b, P1_TOP, max_depth=6, time_budget_ms=0)
        self.assertEqual(a["move"], c["move"])
        self.assertEqual(a["value"], c["value"])


if __name__ == "__main__":
    unittest.main()
