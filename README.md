# Vertical Kalah(6,3) — perfect-play solver

Two parts that share one set of rules:

1. **A browser app (the GitHub Pages site)** — a vertical Kalah board that coaches
   your perfect move, mirroring the Connect 5 frontend. The engine runs entirely
   in your browser (JavaScript in a Web Worker), so the site is static: free to
   host, installable, and playable offline.
2. **A Python engine, CLI & exact verifier** — used to *prove* the game's value
   and to play/solve from the terminal.

## The result

Vertical Kalah(6,3) is a **second-player win by 2**: whoever moves *first* loses
17–19 with perfect play. Your seat in the app is **Bottom (P2)** — the second
player — so with the opponent starting you can force a win every time. (Proven by
an exact solve cross-checked against an independent minimax; see `tools/solve.py`.)

---

## The web app

```bash
# from the project root — then open http://localhost:8000
python -m http.server 8000
```

It's a **solver assistant** (the Connect 5 interaction model):

- You are **Bottom (P2)**; the engine highlights **your best pit** in green and
  sows it for you, stones animating **anticlockwise** one at a time.
- You **tap the opponent's pits** (Top / right column) to enter their moves.
- **Extra turns** (last stone in your store → go again) and **empty captures**
  are handled and animated for both sides.
- Controls: who-starts toggle, **New game**, **Undo**. The readout forecasts the
  result and shows **“Perfect move”** once the position is provably solved.
- Installable PWA, works offline, dark machined theme — same as Connect 5.

### Deploy to GitHub Pages (your `*.github.io` site)

Any static host works; GitHub Pages is the simplest free, always-on option:

1. Create a public repo and push this folder to it.
2. **Settings → Pages → Build and deployment →** Source *Deploy from a branch*,
   branch `main`, folder `/ (root)`. Save.
3. Open the `https://<you>.github.io/<repo>/` URL it gives you; on a phone, use
   **Add to Home Screen** to install.

### The in-browser engine (and why it's a hybrid)

The JavaScript port lives in `src/engine/` and runs in `src/engine/worker.js` off
the main thread. Each move it plays a **time-bounded iterative-deepening search**
(~1.5 s): very strong everywhere, and **provably exact** the moment it proves a
win/loss/draw — which it does quickly once stones drain into the stores, so the
endgame is played perfectly.

It is *not* exact-always because exactly solving the **opening** explores **>16.7
million** distinct positions — past a JavaScript `Map`'s limit and a phone's
memory. The transposition table is hard-capped so the tab can never blow up. (The
Python engine, with no such limit, still solves the opening exactly to prove the
game's value.)

---

## Python engine, CLI & verifier

```bash
python -m kalah.cli              # play in the terminal; you are P1, the AI is perfect P2
python -m unittest discover -s tests -t .        # 48 tests
python tools/solve.py            # prints the exact game value + "AI is UNBEATABLE (+2)"
node tools/check_web.mjs         # validates the JS engine (sow paths, never-lose)
```

`kalah/` is the exact solver: `solve` (provably optimal) and `search` (timed)
modes, a transposition table keyed by `(state, side-to-move)`, and a CLI.
`tools/solve.py` reports the exact value and, with `--book`, walks every opponent
line to prove the AI never loses (run it on `--variant 1` for a fast full proof).

---

## How it works

| Browser (JS, `src/`) | Terminal (Python, `kalah/`) | Role |
| --- | --- | --- |
| `engine/constants.js` | `constants.py` | indices, maps, capture pairing, weights |
| `engine/board.js` | `board.py` | state + `sow` (skip / extra-turn / capture), terminal, cleanup |
| `engine/evaluate.js` | `evaluate.py` | heuristic: store diff ≫ control + extra-turn pressure |
| `engine/transposition.js` | `transposition.py` | TT keyed by `(state, player)`, capped in JS |
| `engine/search.js` | `search.py` | negamax + α-β; `search` (timed) and `solve` (exact) |
| `engine/engine.js` | `engine.py` | `bestMove` / mode dispatch + book hook |
| `ui/app.js` | `cli.py` | the playable interface |

- **State** is a 14-cell board; the index order makes counter-clockwise sowing a
  plain `(i+1) % 14` that only skips the opponent's store. Pit `i` faces `12 − i`.
- **The extra-turn twist.** Vanilla negamax assumes the side to move alternates
  every ply. Kalah's extra turn breaks that, so a turn-passing move recurses as
  `-negamax(child, opp, -β, -α)` while an extra-turn move recurses as
  `+negamax(child, player, α, β)` — no flip, same window, same player.
- Move ordering tries the TT move, then extra-turn moves, then captures, then the
  biggest store gain. Terminal value is the final store margin (scaled to
  dominate any heuristic leaf) with a tiny ply term to prefer faster wins.
