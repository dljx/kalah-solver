"""Rules tests for vertical Kalah(6,3): sowing, store-skip, capture, extra-turn,
and terminal cleanup. Expected outcomes are hand-computed."""

import unittest

from kalah import board
from kalah import constants as C


def make(overrides):
    """A 14-cell board, all zeros except the given ``{index: count}`` overrides."""
    cells = [0] * C.CELLS
    for i, v in overrides.items():
        cells[i] = v
    return tuple(cells)


class TestGeometry(unittest.TestCase):
    def test_initial_board(self):
        b = board.initial_board()
        self.assertEqual(len(b), 14)
        for p in range(0, 6):
            self.assertEqual(b[p], 3)
        for p in range(7, 13):
            self.assertEqual(b[p], 3)
        self.assertEqual(b[6], 0)   # P2 store
        self.assertEqual(b[13], 0)  # P1 store

    def test_opposite_pairing(self):
        self.assertEqual(C.OPPOSITE[0], 12)
        self.assertEqual(C.OPPOSITE[5], 7)
        self.assertEqual(C.OPPOSITE[7], 5)
        self.assertEqual(C.OPPOSITE[12], 0)

    def test_distance_to_store(self):
        self.assertEqual(C.distance_to_store(5, C.P2_BOTTOM), 1)
        self.assertEqual(C.distance_to_store(0, C.P2_BOTTOM), 6)
        self.assertEqual(C.distance_to_store(12, C.P1_TOP), 1)
        self.assertEqual(C.distance_to_store(7, C.P1_TOP), 6)


class TestLegalMoves(unittest.TestCase):
    def test_initial_legal_moves(self):
        b = board.initial_board()
        self.assertEqual(board.legal_moves(b, C.P2_BOTTOM), [0, 1, 2, 3, 4, 5])
        self.assertEqual(board.legal_moves(b, C.P1_TOP), [7, 8, 9, 10, 11, 12])

    def test_empty_pits_excluded(self):
        b = make({0: 3, 1: 0, 2: 5})
        self.assertEqual(board.legal_moves(b, C.P2_BOTTOM), [0, 2])


class TestSow(unittest.TestCase):
    def test_basic_sow(self):
        b = board.initial_board()
        new, extra, cap = board.sow(b, 2, C.P2_BOTTOM)
        self.assertEqual(new, (3, 3, 0, 4, 4, 4, 0, 3, 3, 3, 3, 3, 3, 0))
        self.assertFalse(extra)
        self.assertFalse(cap)

    def test_extra_turn_last_in_own_store(self):
        b = board.initial_board()
        new, extra, cap = board.sow(b, 3, C.P2_BOTTOM)  # 3 stones reach store at 6
        self.assertTrue(extra)
        self.assertFalse(cap)
        self.assertEqual(new[6], 1)
        self.assertEqual(new[3], 0)

    def test_sowing_through_own_store_continues(self):
        b = make({5: 2})  # stone 1 -> store(6), stone 2 -> pit 7; turn ends
        new, extra, cap = board.sow(b, 5, C.P2_BOTTOM)
        self.assertEqual(new[6], 1)
        self.assertEqual(new[7], 1)
        self.assertFalse(extra)
        self.assertFalse(cap)

    def test_p2_skips_opponent_store(self):
        b = make({0: 14})  # long sow must skip P1's store (13), seed own store (6)
        new, extra, cap = board.sow(b, 0, C.P2_BOTTOM)
        self.assertEqual(new[13], 0, "P2 must never seed the top store")
        self.assertEqual(new[6], 1, "P2 seeds its own store")
        self.assertFalse(cap)  # last stone lands in pit 1 which now holds 2

    def test_p1_skips_opponent_store(self):
        b = make({7: 14})  # P1 long sow must skip P2's store (6), seed own store (13)
        new, extra, cap = board.sow(b, 7, C.P1_TOP)
        self.assertEqual(new[6], 0, "P1 must never seed the bottom store")
        self.assertEqual(new[13], 1, "P1 seeds its own store")


class TestCapture(unittest.TestCase):
    def test_empty_capture(self):
        b = make({1: 1, 10: 5})  # sow 1 -> lands in empty pit 2; opposite(2)=10 has 5
        new, extra, cap = board.sow(b, 1, C.P2_BOTTOM)
        self.assertTrue(cap)
        self.assertFalse(extra)
        self.assertEqual(new[6], 6, "captured 5 opposite + 1 landing stone")
        self.assertEqual(new[2], 0)
        self.assertEqual(new[10], 0)

    def test_no_capture_when_opposite_empty(self):
        b = make({1: 1, 10: 0})
        new, extra, cap = board.sow(b, 1, C.P2_BOTTOM)
        self.assertFalse(cap)
        self.assertEqual(new[2], 1)
        self.assertEqual(new[6], 0)

    def test_no_capture_when_landing_pit_occupied(self):
        b = make({1: 1, 2: 3, 10: 5})  # pit 2 not empty -> not a capture
        new, extra, cap = board.sow(b, 1, C.P2_BOTTOM)
        self.assertFalse(cap)
        self.assertEqual(new[2], 4)

    def test_no_capture_on_opponent_side(self):
        b = make({5: 2})  # last stone lands in pit 7 (opponent side) -> no capture
        new, extra, cap = board.sow(b, 5, C.P2_BOTTOM)
        self.assertFalse(cap)


class TestTerminal(unittest.TestCase):
    def test_not_terminal_initial(self):
        self.assertFalse(board.is_terminal(board.initial_board()))

    def test_terminal_when_a_side_empties(self):
        b = make({6: 5, 7: 3, 8: 3, 9: 3, 10: 3, 11: 3, 12: 3, 13: 1})
        self.assertTrue(board.is_terminal(b))  # P2 pits 0-5 all empty

    def test_cleanup_and_winner(self):
        b = make({6: 5, 7: 3, 8: 3, 9: 3, 10: 3, 11: 3, 12: 3, 13: 1})
        s1, s2 = board.final_stores(b)
        self.assertEqual(s1, 19)  # 1 + swept 18
        self.assertEqual(s2, 5)
        self.assertEqual(board.winner(b), C.P1_TOP)
        self.assertEqual(board.margin(b, C.P1_TOP), 14)
        self.assertEqual(board.margin(b, C.P2_BOTTOM), -14)

    def test_draw(self):
        b = make({6: 18, 13: 18})  # both sides already empty, equal stores
        self.assertTrue(board.is_terminal(b))
        self.assertEqual(board.winner(b), 0)


class TestStoneConservation(unittest.TestCase):
    def test_sow_conserves_stones(self):
        b = board.initial_board()
        for player in (C.P1_TOP, C.P2_BOTTOM):
            for pit in board.legal_moves(b, player):
                new, _, _ = board.sow(b, pit, player)
                self.assertEqual(sum(new), sum(b), f"stones not conserved sowing {pit}")


if __name__ == "__main__":
    unittest.main()
