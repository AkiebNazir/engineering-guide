/* ============================================================================
   Reveal-solution gate — one behaviour for every place a solution lives.

   System Design practice problems (reader.js) and DSA problem solutions
   (app.js → loadPane('solution')) both start hidden behind a gate and only
   open when you press "Reveal solution". The reveal lasts only while you stay
   on that problem (switching tabs inside it is fine); navigate away, come
   back or reload, and it is hidden again, so a re-solve is always cold.
   Each reveal is still recorded in progress.json.

   DSA solutions also get a "Watch it run" animation at the top, using the
   step-by-step player from dsa-viz.js: the exact problem when an animation
   exists for it, otherwise the topic's pattern animations (clearly labelled).
   ========================================================================= */
'use strict';

/* `sd:<doc key>` or `dsa:<problem id>` → the route it was revealed on */
const REVEALED = new Map();
const revealIsOpen = key => REVEALED.has(key);
const revealOpen = key => REVEALED.set(key, location.hash.replace(/\/(question|solution|visualize|guide|notes)$/, ''));
const revealClose = key => REVEALED.delete(key);
window.addEventListener('hashchange', () => {
  for (const [key, route] of REVEALED) if (!location.hash.startsWith(route)) REVEALED.delete(key);
});

const GATE_ICON = {
  lock: '<rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
  eye: '<path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
  eyeOff: '<path d="M3 3l18 18M10.6 5.1A10.4 10.4 0 0112 5c6.4 0 10 7 10 7a17.6 17.6 0 01-3.2 4.1M6.6 6.6C3.8 8.4 2 12 2 12s3.6 7 10 7a9.8 9.8 0 005.4-1.6"/><path d="M9.9 9.9a3 3 0 004.2 4.2"/>',
  check: '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
};
const gateSvg = name => `<svg viewBox="0 0 24 24" aria-hidden="true">${GATE_ICON[name]}</svg>`;

/* The locked card. `act` is the data-act the reveal button carries. */
function revealGateHTML({ kicker, title, copy, checks = [], inside = [], button = 'Reveal solution', act = 'reveal', note = '' }) {
  return `<section class="rv-gate" data-gate>
    <div class="rv-gate-top">
      <span class="rv-lock">${gateSvg('lock')}</span>
      <div>
        <p class="rv-kicker">${kicker}</p>
        <div class="rv-title">${title}</div>
        <p class="rv-copy">${copy}</p>
      </div>
    </div>
    ${checks.length ? `<ul class="rv-checks">${checks.map(c => `<li><label><input type="checkbox"> <span>${c}</span></label></li>`).join('')}</ul>` : ''}
    ${inside.length ? `<div class="rv-inside">${inside.map(([k, v]) => `<span>${k} <b>${v}</b></span>`).join('')}</div>` : ''}
    <div class="rv-actions">
      <button type="button" class="rv-btn" data-act="${act}">${gateSvg('eye')}${button}</button>
      ${note ? `<span class="rv-note">${note}</span>` : ''}
    </div>
  </section>`;
}

/* The strip that replaces the gate once it is open, with a way to close it again. */
function revealBannerHTML({ title, sub, act = 'hide-solution', just = false }) {
  return `<div class="rv-banner${just ? ' rv-just' : ''}" data-banner>
    <span class="rv-banner-mark">${gateSvg('check')}</span>
    <span class="rv-banner-text"><b>${title}</b><span>${sub}</span></span>
    <button type="button" class="rv-btn ghost" data-act="${act}">${gateSvg('eyeOff')}Hide solution</button>
  </div>`;
}

/* ================================================================ DSA ====== */
const normTitle = s => String(s || '').toLowerCase().replace(/[^a-z0-9]/g, '');

/* Animations whose title is not the LeetCode title, mapped to the problems they solve. */
const SOLUTION_ALGO_FOR = {
  'Two Sum with a hash map': ['01_arrays_hashing/004'],
  'Find Disappeared Numbers': ['01_arrays_hashing/006'],
  'Two pointers on a sorted array': ['02_two_pointers/006'],
  'Lower bound: first position where nums[i] ≥ target': ['05_binary_search/002'],
  'Daily Temperatures with a monotonic stack': ['06_stack/007'],
  'Sliding Window Maximum with a monotonic deque': ['03_sliding_window/015'],
  'Reverse a linked list': ['08_linked_list/001'],
  'Floyd cycle detection (tortoise and hare)': ['08_linked_list/003'],
  'Subsets: the take / skip decision tree': ['09_recursion_backtracking/002'],
  'Tree traversals': ['10_trees/001', '10_trees/002', '10_trees/003'],
  'Binary search tree: insert and search': ['11_binary_search_tree/001', '11_binary_search_tree/003'],
  'Trie: insert words, then search a prefix': ['13_trie/001'],
  'Number of islands: flood fill': ['14_graphs/002'],
  'Rotting oranges: multi-source BFS': ['14_graphs/006'],
  'House robber: one row of state': ['16_dp_1d/005'],
  'Recursion tree vs memoisation': ['09_recursion_backtracking/001'],
  'Longest common subsequence, with traceback': ['17_dp_2d/005'],
  'Jump game: the furthest reach': ['18_greedy/003'],
  'Meeting rooms II: the sweep line': ['19_intervals/005'],
  'Single number: XOR cancellation': ['20_bit_manipulation/001'],
  'Counting bits with n & (n − 1)': ['20_bit_manipulation/003'],
  'Fast power: squaring instead of multiplying': ['21_math_geometry/004'],
  'Happy number: the cycle in digit squares': ['21_math_geometry/003'],
  'Quicksort vs merge sort': ['22_sorting_algorithms/002'],
  'Dutch national flag (sort colors)': ['22_sorting_algorithms/003'],
  'KMP: never re-read the text': ['23_string_algorithms/001'],
  'Spiral order: four shrinking walls': ['24_matrix/003'],
  'LRU cache: hash map + doubly linked list': ['08_linked_list/013'],
  'Segment tree: range sum with updates': ['26_segment_tree_fenwick/001'],
  'Fisher–Yates shuffle': ['27_algorithms/001'],
  'Weighted random pick: prefix sums + binary search': ['27_algorithms/004'],
};

function allAlgos() {
  if (typeof ALGOS === 'undefined') return [];
  return [...new Set(Object.entries(ALGOS).filter(([k]) => k !== '__solution__').flatMap(([, v]) => v))];
}

/* { exact: spec|null, pattern: spec[] } for a DATA.problems entry */
function solutionAlgosFor(p) {
  const all = allAlgos();
  const exact = all.find(a => normTitle(a.title) === normTitle(p.title))
    || all.find(a => (SOLUTION_ALGO_FOR[a.title] || []).includes(p.id)) || null;
  const pattern = typeof ALGOS !== 'undefined' ? (ALGOS[p.topic] || []).filter(a => a !== exact) : [];
  return { exact, pattern };
}

function mountSolutionViz(host, specs, startAt = 0) {
  if (typeof renderAlgoTab !== 'function' || !specs.length) return;
  ALGOS.__solution__ = specs;
  try { localStorage.setItem('algo-prefs', JSON.stringify({ ...JSON.parse(localStorage.getItem('algo-prefs') || '{}'), __solution__: startAt })); } catch (e) { /* private mode */ }
  renderAlgoTab(host, '__solution__');
}

function vizBlockHTML(p, { exact, pattern }) {
  if (exact) {
    return `<section class="sol-viz" data-solviz="exact">
      <div class="sol-viz-head"><span class="sol-viz-tag">Watch it run</span><b>${esc(String(exact.title))}</b>
        <span>Play it, step through it, or try your own input.</span></div>
      <div class="sol-viz-body"></div>
    </section>`;
  }
  if (pattern.length) {
    return `<section class="sol-viz is-collapsed" data-solviz="pattern">
      <div class="sol-viz-head"><span class="sol-viz-tag pattern">Pattern animation</span>
        <b>${esc(String(pattern.map(a => a.short || a.title).join(' · ')))}</b>
        <span>No animation for this exact problem yet; this is the ${esc(String(p.topicTitle || 'topic'))} pattern it builds on.</span>
        <button type="button" class="rv-btn ghost sol-viz-open" data-solviz-open>Show animation</button></div>
      <div class="sol-viz-body"></div>
    </section>`;
  }
  return '';
}

/* Called from app.js loadPane('solution') once the file has been fetched. */
function renderGatedSolution(body, p, d, lang, { justRevealed = false } = {}) {
  const key = `dsa:${p.id}`;
  const r = typeof rec === 'function' ? rec(p.id) : {};
  const mins = Math.floor((r.timeSpent || 0) / 60);
  const viz = solutionAlgosFor(p);

  if (!revealIsOpen(key)) {
    body.innerHTML = `<div class="rv-wrap">${revealGateHTML({
      kicker: `LeetCode ${esc(String(p.lc || ''))} · ${esc(String(p.diff || ''))}`,
      title: 'Solve it before you look',
      copy: `You have spent <b>${mins} min</b> on this problem. The ladder: stuck at <b>25 min</b> → reread the question and take one hint from the Topic guide; still stuck at <b>40 min</b> → open the solution, then re-solve it cold tomorrow.`,
      checks: ['My code runs on the examples', 'I tried the edge cases', 'I can state the time and space complexity', 'I named the pattern'],
      inside: [
        ['solution', lang === 'go' ? 'Go' : 'Python'],
        ...(viz.exact ? [['includes', 'step-by-step animation']] : viz.pattern.length ? [['includes', 'pattern animation']] : []),
        ['views so far', String(r.solutionViews || 0)],
      ],
      button: 'Reveal solution',
      note: 'Hidden again as soon as you leave this problem.',
    })}</div>`;
    body.onscroll = null;
    body.scrollTop = 0;
    body.querySelector('[data-act="reveal"]').onclick = () => {
      revealOpen(key);
      const views = (r.solutionViews || 0) + 1;
      r.solutionViews = views;
      if (typeof patch === 'function') patch(p.id, { solutionViews: views, lastSolutionView: Date.now() });
      renderGatedSolution(body, p, d, lang, { justRevealed: true });
    };
    return;
  }

  body.innerHTML = `
    ${revealBannerHTML({ title: 'Solution open', sub: 'Compare it with your own attempt, then write the trigger you missed in Notes.', just: justRevealed })}
    ${vizBlockHTML(p, viz)}
    <div class="sol-doc">${renderDoc(d.doc || '(no description in this file)', 'solution')}</div>`;
  const docHost = body.querySelector('.sol-doc');
  if (typeof enhanceProblemDoc === 'function') enhanceProblemDoc(docHost);

  body.querySelector('[data-act="hide-solution"]').onclick = () => {
    revealClose(key);
    renderGatedSolution(body, p, d, lang);
  };
  const vizSec = body.querySelector('[data-solviz]');
  if (vizSec) {
    const vbody = vizSec.querySelector('.sol-viz-body');
    if (vizSec.dataset.solviz === 'exact') mountSolutionViz(vbody, [viz.exact]);
    const open = vizSec.querySelector('[data-solviz-open]');
    if (open) {
      open.onclick = () => {
        const collapsed = vizSec.classList.toggle('is-collapsed');
        open.textContent = collapsed ? 'Show animation' : 'Hide animation';
        if (!collapsed && !vbody.childElementCount) {
          mountSolutionViz(vbody, viz.pattern);
          vbody.querySelector('.algo-head')?.style.setProperty('display', viz.pattern.length > 1 ? 'flex' : 'none');
        }
      };
    }
  }
  if (justRevealed) body.scrollTop = 0;
}
