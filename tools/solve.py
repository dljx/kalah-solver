"""Perfect-play verifier and book generator for vertical Kalah(6,3).

Run from the project root:

    python tools/solve.py                 # report the exact game value (both seats)
    python tools/solve.py --book          # also build + verify + persist P2's book
    python tools/solve.py --variant 2     # do it all on a smaller (faster) variant

The exact game value alone proves unbeatability: a positive value for a seat
means that seat has a strategy guaranteeing a win against *every* opponent line.
With ``--book`` the verifier also walks the entire game tree under optimal AI
play -- branching every opponent reply -- and asserts the AI's margin never
drops below that guaranteed value, then writes the AI's move for each position
it can face to ``assets/solved.json`` (the analogue of the reference engine's
opening book), so the engine can later answer instantly and perfectly.
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from kalah.board import legal_moves, sow, is_terminal, margin
from kalah.constants import (
    OPPONENT,
    TERMINAL_SCALE,
    P1_TOP,
    P2_BOTTOM,
)
from kalah.search import solve
from kalah.transposition import TranspositionTable
from kalah.book import key_for

OUT_PATH = os.path.join(ROOT, "assets", "solved.json")
SEAT_NAME = {P1_TOP: "P1 (Top, first)", P2_BOTTOM: "P2 (Bottom, the AI)"}


def variant_board(stones):
    """Starting board with ``stones`` per pit (3 = the real Kalah(6,3))."""
    return tuple([stones] * 6 + [0] + [stones] * 6 + [0])


def to_margin(value):
    return round(value / TERMINAL_SCALE)


def report_values(start, tt):
    """Solve the opening for each seat and print the exact result."""
    print("Exact game value (optimal play by both sides):")
    seat_margin = {}
    for player in (P1_TOP, P2_BOTTOM):
        res = solve(start, player, tt=tt)
        m = to_margin(res["value"])
        seat_margin[player] = m
        outcome = "WIN" if m > 0 else ("DRAW" if m == 0 else "LOSS")
        print(
            f"  {SEAT_NAME[player]:<24} to move: {outcome} by {abs(m)}  "
            f"(best move = pit {res['move']}, nodes = {res['nodes']:,})"
        )
    return seat_margin


def build_book(start, ai, first_mover, tt, target):
    """Walk every line under optimal AI play, verifying and recording the AI's moves.

    Returns ``(book, ai_nodes, terminals, failures)``. ``failures`` lists any
    terminal where the AI's margin fell below ``target`` -- empty means proven.
    """
    book = {}
    visited = set()
    stats = {"ai_nodes": 0, "terminals": 0}
    failures = []

    def walk(state, player):
        if is_terminal(state):
            stats["terminals"] += 1
            if margin(state, ai) < target:
                failures.append(state)
            return
        key = (state, player)
        if key in visited:
            return
        visited.add(key)

        if player == ai:
            res = solve(state, ai, tt=tt)
            move = res["move"]
            book[key_for(state, ai)] = [move, to_margin(res["value"])]
            stats["ai_nodes"] += 1
            child, extra, _ = sow(state, move, ai)
            walk(child, ai if extra else OPPONENT[ai])
        else:
            for move in legal_moves(state, player):
                child, extra, _ = sow(state, move, player)
                walk(child, player if extra else OPPONENT[player])

    walk(start, first_mover)
    return book, stats["ai_nodes"], stats["terminals"], failures


def main(argv=None):
    parser = argparse.ArgumentParser(description="Exact solver / verifier for Kalah(6,3).")
    parser.add_argument("--variant", type=int, default=3, help="stones per pit (default 3)")
    parser.add_argument("--ai", type=int, choices=(1, 2), default=2, help="AI seat (default 2 = P2)")
    parser.add_argument("--first", type=int, choices=(1, 2), default=1, help="who moves first (default 1)")
    parser.add_argument("--book", action="store_true", help="build, verify and persist the AI's book")
    parser.add_argument("--out", default=OUT_PATH, help="book output path")
    args = parser.parse_args(argv)

    start = variant_board(args.variant)
    ai = args.ai
    first = args.first
    tt = TranspositionTable()

    print(f"Vertical Kalah(6,{args.variant})  --  {args.variant * 12} stones in play\n")
    seat_margin = report_values(start, tt)

    # The AI's guaranteed margin from the actual starting position.
    ai_target = seat_margin[ai] if first == ai else -seat_margin[first]
    verdict = "UNBEATABLE" if ai_target >= 0 else "theoretically lost"
    print(
        f"\nWith {SEAT_NAME[ai]} as the AI and P{first} moving first: "
        f"AI is {verdict} (guaranteed margin {ai_target:+d})."
    )

    if not args.book:
        print("\n(Pass --book to verify across all opponent lines and write the book.)")
        return 0

    print(f"\nBuilding + verifying {SEAT_NAME[ai]}'s book (this can take a while)...")
    book, ai_nodes, terminals, failures = build_book(start, ai, first, tt, ai_target)
    if failures:
        print(f"  PROOF FAILED: {len(failures)} terminal(s) below margin {ai_target}.")
        print(f"  example: {failures[0]}")
        return 1

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(book, fh)
    print(
        f"  PROVEN: every one of {terminals:,} reachable endings has the AI ahead "
        f"by >= {ai_target}."
    )
    print(f"  Book: {ai_nodes:,} AI positions written to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
