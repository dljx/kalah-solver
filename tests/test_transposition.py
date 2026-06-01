"""Tests for the transposition table: key identity, player-sensitivity, depth
preference, the terminal-exact override, and clearing."""

import unittest

from kalah import board
from kalah.transposition import TranspositionTable, EXACT, LOWER
from kalah import constants as C


class TestTranspositionTable(unittest.TestCase):
    def setUp(self):
        self.tt = TranspositionTable()
        self.state = board.initial_board()

    def test_set_get_roundtrip(self):
        key = (self.state, C.P1_TOP)
        self.tt.set(key, 42, depth=5, flag=EXACT, move=9, exact=True)
        self.assertEqual(self.tt.get(key), (42, 5, EXACT, 9, True))

    def test_missing_key_returns_none(self):
        self.assertIsNone(self.tt.get((self.state, C.P2_BOTTOM)))

    def test_player_is_part_of_key(self):
        self.tt.set((self.state, C.P1_TOP), 7, 3, EXACT, 8, True)
        self.assertIsNone(self.tt.get((self.state, C.P2_BOTTOM)))

    def test_keeps_deeper_entry_same_class(self):
        key = (self.state, C.P1_TOP)
        self.tt.set(key, 10, 6, EXACT, 7, False)
        self.tt.set(key, 99, 2, LOWER, 8, False)  # shallower, same class -> ignored
        self.assertEqual(self.tt.get(key)[0], 10)

    def test_overwrites_with_deeper_entry_same_class(self):
        key = (self.state, C.P1_TOP)
        self.tt.set(key, 10, 2, EXACT, 7, False)
        self.tt.set(key, 99, 8, EXACT, 8, False)  # deeper -> replaces
        self.assertEqual(self.tt.get(key)[0], 99)

    def test_exact_entry_not_downgraded(self):
        key = (self.state, C.P1_TOP)
        self.tt.set(key, 10, 3, EXACT, 7, True)   # terminal-exact
        self.tt.set(key, 99, 9, EXACT, 8, False)  # deeper but non-exact -> ignored
        self.assertEqual(self.tt.get(key)[0], 10)

    def test_nonexact_replaced_by_exact(self):
        key = (self.state, C.P1_TOP)
        self.tt.set(key, 10, 9, EXACT, 7, False)  # deep but non-exact
        self.tt.set(key, 99, 1, EXACT, 8, True)   # shallow but exact -> wins
        self.assertEqual(self.tt.get(key), (99, 1, EXACT, 8, True))

    def test_size_and_clear(self):
        self.tt.set((self.state, C.P1_TOP), 1, 1, EXACT, 7, True)
        self.tt.set((self.state, C.P2_BOTTOM), 1, 1, EXACT, 0, True)
        self.assertEqual(self.tt.size, 2)
        self.tt.clear()
        self.assertEqual(self.tt.size, 0)


if __name__ == "__main__":
    unittest.main()
