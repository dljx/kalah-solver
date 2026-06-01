"""Tests for the exact solver and the perfect-play verifier.

Fast checks run by default:
  * the fast solver agrees with an independent plain minimax on random positions
  * the verifier exhaustively proves the winning seat never loses (1-stone game)

The full Kalah(6,3) solve (~30s) is gated behind KALAH_SLOW=1.
"""

import os
import random
import sys
import unittest

sys.setrecursionlimit(10**6)

from kalah.board import legal_moves, sow, is_terminal, margin, initial_board
from kalah.constants import OPPONENT, TERMINAL_SCALE, P1_TOP, P2_BOTTOM
from kalah.search import solve
from kalah.transposition import TranspositionTable
from tools.solve import variant_board, build_book


def _value_ref(state, player, memo):
    """Plain memoized minimax -- no pruning, no heuristic -- as ground truth."""
    if is_terminal(state):
        m = margin(state, player)
        return m * TERMINAL_SCALE if m else 0
    k = (state, player)
    if k in memo:
        return memo[k]
    best = -(10**9)
    for pit in legal_moves(state, player):
        child, extra, _ = sow(state, pit, player)
        v = _value_ref(child, player, memo) if extra else -_value_ref(child, OPPONENT[player], memo)
        best = max(best, v)
    memo[k] = best
    return best


def _margin(value):
    return round(value / TERMINAL_SCALE)


class TestSolverCorrectness(unittest.TestCase):
    def test_matches_reference_on_random_positions(self):
        rng = random.Random(7)
        pits = [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11, 12]
        checked = 0
        for _ in range(30):
            cells = [0] * 14
            for _ in range(rng.randint(4, 9)):
                cells[rng.choice(pits)] += 1
            state = tuple(cells)
            if is_terminal(state):
                continue
            for player in (P1_TOP, P2_BOTTOM):
                ref = _margin(_value_ref(state, player, {}))
                got = _margin(solve(state, player)["value"])
                self.assertEqual(ref, got, f"state={state} player={player}")
                checked += 1
        self.assertGreater(checked, 30)


class TestVerifierProvesUnbeatable(unittest.TestCase):
    def test_first_player_unbeatable_in_one_stone_game(self):
        # 1 stone/pit: the first player wins by 2. The verifier must walk every
        # opponent line and find no ending where P1's margin drops below 2.
        start = variant_board(1)
        tt = TranspositionTable()
        book, ai_nodes, terminals, failures = build_book(
            start, ai=P1_TOP, first_mover=P1_TOP, tt=tt, target=2
        )
        self.assertEqual(failures, [])
        self.assertGreater(ai_nodes, 0)
        self.assertGreater(terminals, 0)


class TestRealGameValue(unittest.TestCase):
    @unittest.skipUnless(
        os.environ.get("KALAH_SLOW"), "set KALAH_SLOW=1 to run the full Kalah(6,3) solve (~30s)"
    )
    def test_second_player_wins_real_game(self):
        # P1 (the side to move first) loses by 2 -> the second player (the AI's
        # P2 seat) wins by 2 with perfect play.
        res = solve(initial_board(), P1_TOP)
        self.assertEqual(_margin(res["value"]), -2)


if __name__ == "__main__":
    unittest.main()
