"""Tests for the heuristic: antisymmetry, store dominance, extra-turn pressure."""

import unittest

from kalah import board
from kalah.evaluate import evaluate
from kalah import constants as C


def make(overrides):
    cells = [0] * C.CELLS
    for i, v in overrides.items():
        cells[i] = v
    return tuple(cells)


class TestEvaluate(unittest.TestCase):
    def test_initial_is_balanced(self):
        self.assertEqual(evaluate(board.initial_board(), C.P1_TOP), 0)
        self.assertEqual(evaluate(board.initial_board(), C.P2_BOTTOM), 0)

    def test_antisymmetry(self):
        b = make({0: 2, 3: 5, 6: 4, 9: 1, 11: 7, 13: 2})
        self.assertEqual(
            evaluate(b, C.P1_TOP), -evaluate(b, C.P2_BOTTOM)
        )

    def test_store_lead_is_positive(self):
        b = make({6: 10, 7: 3, 8: 3})  # P2 has banked 10; P1 has a little control
        self.assertGreater(evaluate(b, C.P2_BOTTOM), 0)
        self.assertLess(evaluate(b, C.P1_TOP), 0)

    def test_store_weight_dominates_control(self):
        # P2 leads the store by 1 (=> +100) but trails control by a few stones.
        b = make({6: 1, 7: 4})
        self.assertGreater(evaluate(b, C.P2_BOTTOM), 0)

    def test_extra_turn_pressure_counts(self):
        # pit 3 holds exactly its distance-to-store (3) => an extra-turn threat.
        ready = make({3: C.DIST_TO_STORE[C.P2_BOTTOM][3]})
        none = make({3: C.DIST_TO_STORE[C.P2_BOTTOM][3] + 1})
        self.assertGreater(
            evaluate(ready, C.P2_BOTTOM), evaluate(none, C.P2_BOTTOM)
        )


if __name__ == "__main__":
    unittest.main()
