"""Interactive terminal client for vertical Kalah(6,3).

    python -m kalah.cli                 # you are P1 (first); the AI is P2, perfect
    python -m kalah.cli --mode play     # AI uses a 1s time-limited search instead
    python -m kalah.cli --ai 1          # let the AI take P1; you play P2

In the default ``solve`` mode the AI plays provably optimal moves (it is the
second player, which wins Kalah(6,3) by 2). A persistent transposition table is
reused across the game, so only the first move is slow.
"""

import argparse

from .board import (
    initial_board,
    legal_moves,
    sow,
    is_terminal,
    cleanup,
    final_stores,
    winner,
)
from .constants import P1_TOP, P2_BOTTOM, OPPONENT, WIN_THRESHOLD, TERMINAL_SCALE
from .engine import best_move
from .transposition import TranspositionTable

LABEL = {P1_TOP: "P1 (Top)", P2_BOTTOM: "P2 (Bottom)"}


def render(state):
    """Return the vertical board as text: P2's pits left, P1's pits right."""
    rows = [f"            {LABEL[P1_TOP]} store [13]: {state[13]:>2}",
            "          +----+      +----+"]
    for r in range(6):
        left, right = r, 12 - r
        rows.append(
            f"     [{left:>2}] | {state[left]:>2} |      | {state[right]:>2} | [{right:>2}]"
        )
    rows.append("          +----+      +----+")
    rows.append(f"            {LABEL[P2_BOTTOM]} store [ 6]: {state[6]:>2}")
    rows.append("          left = P2 (Bottom)   right = P1 (Top)")
    return "\n".join(rows)


def forecast(value):
    """Human-readable outcome forecast from a (terminal-scaled) search value."""
    if abs(value) < WIN_THRESHOLD:
        return ""
    m = round(value / TERMINAL_SCALE)
    if m > 0:
        return f"  (forecast: win by {m})"
    if m < 0:
        return f"  (forecast: loss by {-m})"
    return "  (forecast: draw)"


def ask_human(state, player):
    """Prompt the human for a legal pit; return the pit or None to quit."""
    legal = legal_moves(state, player)
    while True:
        try:
            raw = input(f"Your move ({LABEL[player]}) -- choose a pit {legal} (q to quit): ").strip()
        except EOFError:
            return None
        if raw.lower() in ("q", "quit", "exit"):
            return None
        if raw.isdigit() and int(raw) in legal:
            return int(raw)
        print(f"  invalid -- pick one of {legal}")


def announce_end(state):
    final = cleanup(state)
    print("\n" + render(final))
    s1, s2 = final_stores(state)
    w = winner(state)
    print(f"\nFinal: P1 = {s1}, P2 = {s2}.")
    if w == 0:
        print("It's a draw.")
    else:
        print(f"{LABEL[w]} wins by {abs(s1 - s2)}.")


def play(ai_seat=P2_BOTTOM, mode="solve", time_budget_ms=1000, first=P1_TOP):
    tt = TranspositionTable()
    state = initial_board()
    player = first

    print("Vertical Kalah(6,3). Counter-clockwise sowing; land in your store to go again.")
    print(f"AI = {LABEL[ai_seat]} ({mode} mode).  You = {LABEL[OPPONENT[ai_seat]]}.\n")

    while not is_terminal(state):
        print(render(state))
        if player == ai_seat:
            if mode == "solve":
                print(f"{LABEL[player]} (AI) is solving to perfect play...")
            res = best_move(state, player, mode=mode, tt=tt, time_budget_ms=time_budget_ms)
            move = res["move"]
            print(f"{LABEL[player]} (AI) plays pit {move}.{forecast(res.get('value') or 0)}")
        else:
            move = ask_human(state, player)
            if move is None:
                print("Bye.")
                return

        state, extra, captured = sow(state, move, player)
        if captured:
            print("  -> empty capture!")
        if is_terminal(state):
            break
        if extra:
            print(f"  -> {LABEL[player]} landed in the store and goes again!")
        else:
            player = OPPONENT[player]
        print()

    announce_end(state)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Play vertical Kalah(6,3) against the solver.")
    parser.add_argument("--ai", type=int, choices=(1, 2), default=2, help="AI seat (default 2 = P2)")
    parser.add_argument("--mode", choices=("solve", "play"), default="solve", help="AI strength (default solve = perfect)")
    parser.add_argument("--time", type=int, default=1000, help="play-mode time budget in ms")
    parser.add_argument("--first", type=int, choices=(1, 2), default=1, help="who moves first (default 1)")
    args = parser.parse_args(argv)
    play(ai_seat=args.ai, mode=args.mode, time_budget_ms=args.time, first=args.first)


if __name__ == "__main__":
    main()
