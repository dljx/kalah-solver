// Solver controller for vertical Kalah(6,3). Mirrors the Connect 5 model:
// the engine computes YOUR best move (you are Bottom / P2); you enter the
// OPPONENT's moves (Top / P1) by tapping their pits. Extra turns chain for both
// sides. The engine runs in a Web Worker (hybrid: a time-bounded search that is
// provably exact once the board simplifies), with a main-thread fallback.
// Sowing animates anticlockwise, one stone at a time.

import {
  initialBoard,
  legalMoves,
  sow,
  isTerminal,
  winner,
  finalStores,
  OPPONENT,
  OPP_STORE,
  OPPOSITE,
  STORE,
  P1_TOP,
  P2_BOTTOM,
  TERMINAL_SCALE,
  WIN_THRESHOLD,
} from '../engine/engine.js';

const USER = P2_BOTTOM; // engine advises your side (Bottom, left pits 0-5)
const OPP = P1_TOP; // you tap the opponent's side (Top, right pits 7-12)
const THINK_MS = 1500; // hybrid search budget per recommendation

const $ = (id) => document.getElementById(id);
const delay = (ms) => new Promise((r) => setTimeout(r, ms));

const boardEl = $('board');
const consoleEl = $('console');
const overlay = $('overlay');

let board = initialBoard();
let display = board.slice();
let firstChoice = 'you'; // 'you' | 'opp'
let phase = 'idle'; // me-think | me-anim | opp-input | opp-anim | over | idle
let history = []; // [{ state, current }] snapshots taken before each sow
let worker = null;
let fallback = null; // lazily-imported engine module
const pitEl = {}; // idx -> element

// ---- Engine plumbing ---------------------------------------------------

function setupWorker() {
  try {
    worker = new Worker(new URL('../engine/worker.js', import.meta.url), { type: 'module' });
  } catch {
    worker = null;
  }
}

async function computeMove(state, player) {
  if (worker) {
    return new Promise((resolve) => {
      const onMsg = (ev) => {
        worker.removeEventListener('message', onMsg);
        resolve(ev.data);
      };
      worker.addEventListener('message', onMsg);
      worker.postMessage({ state, player, timeMs: THINK_MS });
    });
  }
  if (!fallback) fallback = await import('../engine/engine.js');
  await delay(15); // let the "Computing" frame paint before we block
  return fallback.bestMove(state, player, { mode: 'play', timeMs: THINK_MS });
}

// ---- Board construction & rendering ------------------------------------

function makeStore(idx, cls, tag) {
  const el = document.createElement('div');
  el.className = `store ${cls}`;
  el.dataset.idx = String(idx);
  el.innerHTML = `<span class="store-tag">${tag}</span><span class="store-num"></span>`;
  pitEl[idx] = el;
  return el;
}

function makePit(idx) {
  const el = document.createElement('div');
  const mine = idx >= 0 && idx <= 5;
  el.className = `pit ${mine ? 'you' : 'opp'}`;
  el.dataset.idx = String(idx);
  el.innerHTML = `<div class="pips"></div><div class="num"></div>`;
  el.addEventListener('click', () => onPitTap(idx));
  pitEl[idx] = el;
  return el;
}

function buildBoard() {
  boardEl.innerHTML = '';
  boardEl.appendChild(makeStore(13, 'top', 'Opponent store'));
  for (let r = 0; r < 6; r++) {
    boardEl.appendChild(makePit(r)); // left column, your pits 0..5
    boardEl.appendChild(makePit(12 - r)); // right column, opponent pits 12..7
  }
  boardEl.appendChild(makeStore(6, 'bottom', 'Your store'));
  renderAll();
}

function renderCell(idx) {
  const el = pitEl[idx];
  const v = display[idx];
  if (idx === 6 || idx === 13) {
    el.querySelector('.store-num').textContent = String(v);
    return;
  }
  el.querySelector('.num').textContent = String(v);
  el.classList.toggle('empty', v === 0);
  const pips = el.querySelector('.pips');
  const n = Math.min(v, 12);
  if (pips.childElementCount !== n) {
    pips.innerHTML = '';
    for (let i = 0; i < n; i++) {
      const d = document.createElement('span');
      d.className = 'pip';
      pips.appendChild(d);
    }
  }
}

function renderAll() {
  for (let i = 0; i < 14; i++) renderCell(i);
}

function bump(idx) {
  const el = pitEl[idx];
  el.classList.remove('bump');
  void el.offsetWidth;
  el.classList.add('bump');
  setTimeout(() => el.classList.remove('bump'), 280);
}

function clearMarks(...classes) {
  for (let i = 0; i < 14; i++) pitEl[i].classList.remove(...classes);
}

// ---- Sowing animation (anticlockwise, one stone at a time) -------------

function sowPath(state, pit, player) {
  const path = [];
  let stones = state[pit];
  let i = pit;
  const skip = OPP_STORE[player];
  while (stones > 0) {
    i = (i + 1) % 14;
    if (i === skip) continue;
    path.push(i);
    stones -= 1;
  }
  return path;
}

async function animateSow(pit, player) {
  const result = sow(board, pit, player); // authoritative outcome
  const path = sowPath(board, pit, player);
  const stepMs = Math.max(55, Math.min(150, Math.round(430 / path.length)));

  display[pit] = 0;
  renderCell(pit);
  bump(pit);

  for (const idx of path) {
    await delay(stepMs);
    display[idx] += 1;
    renderCell(idx);
    bump(idx);
  }

  if (result.captured) {
    await delay(170);
    const landing = path[path.length - 1];
    const opp = OPPOSITE[landing];
    display[landing] = 0;
    display[opp] = 0;
    display[STORE[player]] = result.state[STORE[player]];
    renderCell(landing);
    renderCell(opp);
    renderCell(STORE[player]);
    bump(STORE[player]);
  }

  display = result.state.slice();
  board = result.state;
  renderAll();
  return result;
}

// ---- Console & overlay -------------------------------------------------

function setConsole(mode, label, value, sub) {
  consoleEl.dataset.mode = mode;
  $('consoleLabel').textContent = label;
  $('consoleValue').textContent = value;
  $('consoleSub').textContent = sub;
}

function proven(value) {
  return value !== null && value !== undefined && Math.abs(value) >= WIN_THRESHOLD;
}

function forecastText(value) {
  if (!proven(value)) return '';
  const m = Math.round(value / TERMINAL_SCALE);
  if (m > 0) return `Forecast: you win by ${m}`;
  if (m < 0) return `Forecast: you lose by ${-m}`;
  return 'Forecast: draw';
}

function showOverlay() {
  const w = winner(board);
  const [s1, s2] = finalStores(board);
  const emblem = $('overlayEmblem');
  if (w === 0) {
    $('overlayTitle').textContent = 'Draw';
    $('overlaySub').textContent = `Stores level at ${s1}–${s2}.`;
    emblem.style.cssText = '--c0:#9aa6c8;--c1:#5b678a';
  } else if (w === USER) {
    $('overlayTitle').textContent = 'You win!';
    $('overlaySub').textContent = `Final stores ${s2}–${s1} in your favour.`;
    emblem.style.cssText = '--c0:var(--you-0);--c1:var(--you-1)';
  } else {
    $('overlayTitle').textContent = 'Opponent wins';
    $('overlaySub').textContent = `Final stores ${s1}–${s2}.`;
    emblem.style.cssText = '--c0:var(--opp-0);--c1:var(--opp-1)';
  }
  overlay.hidden = false;
}

// ---- Game flow ---------------------------------------------------------

function end() {
  phase = 'over';
  boardEl.classList.remove('opp-input');
  const w = winner(board);
  const [s1, s2] = finalStores(board);
  if (w === USER) setConsole('play', 'You win', `+${s2 - s1}`, 'Board kept — press New game');
  else if (w === OPP) setConsole('await', 'Opponent wins', `−${s1 - s2}`, 'Board kept — press New game');
  else setConsole('think', 'Draw', '=', 'Board kept — press New game');
  showOverlay();
}

async function meTurn() {
  if (isTerminal(board)) return end();
  phase = 'me-think';
  boardEl.classList.remove('opp-input');
  clearMarks('rec', 'flash');
  setConsole('think', 'Computing', '…', 'Finding your best move');

  const { move, value } = await computeMove(board, USER);
  history.push({ state: board.slice(), current: USER });
  phase = 'me-anim';
  const res = await animateSow(move, USER);

  clearMarks('rec', 'flash', 'last');
  pitEl[move].classList.add('rec', 'flash');
  const fc = forecastText(value);
  setConsole('play', proven(value) ? 'Perfect move' : 'Best move', `▸ ${move}`, fc || 'Your recommended pit');

  if (isTerminal(board)) return end();
  if (res.extra) return meTurn(); // extra turn — you go again
  oppInput();
}

function oppInput() {
  if (isTerminal(board)) return end();
  phase = 'opp-input';
  boardEl.classList.add('opp-input');
  setConsole('await', "Opponent's turn", '▼', 'Tap the pit they played (top / right)');
}

async function onPitTap(idx) {
  if (phase !== 'opp-input') return;
  if (!legalMoves(board, OPP).includes(idx)) return;
  history.push({ state: board.slice(), current: OPP });
  phase = 'opp-anim';
  boardEl.classList.remove('opp-input');
  clearMarks('last');
  const res = await animateSow(idx, OPP);
  pitEl[idx].classList.add('last');

  if (isTerminal(board)) return end();
  if (res.extra) return oppInput(); // opponent earned an extra turn
  meTurn();
}

function undo() {
  if (phase === 'me-think' || phase === 'me-anim' || phase === 'opp-anim') return;
  if (history.length === 0) return;
  // Step back to the previous opponent-input decision (your moves are automatic).
  let snap = history.pop();
  while (snap.current === USER && history.length > 0) snap = history.pop();
  board = snap.state.slice();
  display = board.slice();
  overlay.hidden = true;
  clearMarks('rec', 'flash', 'last');
  renderAll();
  if (snap.current === USER) meTurn();
  else oppInput();
}

function newGame() {
  if (worker) worker.postMessage({ type: 'reset' });
  board = initialBoard();
  display = board.slice();
  history = [];
  phase = 'idle';
  overlay.hidden = true;
  clearMarks('rec', 'flash', 'last');
  buildBoard();
  const first = firstChoice === 'you' ? USER : OPP;
  if (first === USER) meTurn();
  else oppInput();
}

// ---- Wiring ------------------------------------------------------------

function init() {
  setupWorker();
  buildBoard();

  document.querySelectorAll('.seg-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.seg-btn').forEach((b) => b.classList.remove('is-active'));
      btn.classList.add('is-active');
      firstChoice = btn.dataset.first;
    });
  });

  $('newGame').addEventListener('click', newGame);
  $('overlayNew').addEventListener('click', newGame);
  $('undo').addEventListener('click', undo);

  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js').catch(() => {});
  }

  newGame();
}

init();
