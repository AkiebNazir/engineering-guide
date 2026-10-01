/* ============================================================================
   Pattern recognition — the skill interviews actually test in the first
   ninety seconds: read a statement, name the technique.

     #/dsa-drill     the drill. A real problem statement from the curriculum,
                     title hidden; pick the pattern from four (the wrong
                     answers are the patterns it is most often confused with).
                     Every answer teaches: the tells, the move, the look-alikes.
                     Accuracy per pattern is kept in progress.json
                     (state.docs["dsa-drill"]) and "Focus on my misses" deals
                     the weakest patterns more often.
     #/dsa-patterns  the cheat sheet: triage questions, what the constraints
                     allow, and every pattern's signals on one searchable page.

   Also: dsaLearnLoopHTML() — the "how to learn a pattern" strip on the DSA home.

   Reads app.js (DATA, rec, isDone, esc, $, $$, post, curView), dsa-home.js
   (DSA_FAMILIES, dsaFamily), dsa-patterns.js, dsa-learn.js (dsaMap,
   learnInline, learnChip).
   ========================================================================= */
'use strict';

const DRILL_DOC = 'dsa-drill';
const DRILL_MODES = { mixed: 'Mixed', misses: 'Focus on my misses', studied: 'Patterns I have started' };
const drill = { mode: 'mixed', card: null, picked: null, session: { right: 0, total: 0, streak: 0 }, recent: [] };

function drillStore() {
  DATA.state.docs ??= {};
  const d = DATA.state.docs[DRILL_DOC] ??= {};
  d.stats ??= {};                          // topic -> [right, seen]
  return d;
}
function drillSave() {
  const d = drillStore();
  post('/api/patch', { doc: DRILL_DOC, docPatch: { stats: d.stats, best: d.best || 0 } }).catch(() => {});
}
const drillAcc = t => { const s = drillStore().stats[t]; return s && s[1] ? s[0] / s[1] : null; };
const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

function drillPool(map) {
  let pool = DATA.problems.filter(p => playbook(p.topic) && map[p.id] && map[p.id].statement && map[p.id].statement.text.length);
  if (drill.mode === 'studied') {
    const started = new Set(DATA.problems.filter(p => rec(p.id).status !== 'todo').map(p => p.topic));
    const narrowed = pool.filter(p => started.has(p.topic));
    if (narrowed.length >= 8) pool = narrowed;
  }
  return pool;
}

function drillDeal(map) {
  const pool = drillPool(map).filter(p => !drill.recent.includes(p.id));
  if (!pool.length) return null;
  let p;
  if (drill.mode === 'misses') {
    // weight each problem by how often its pattern is missed; unseen patterns count as half-missed
    const w = pool.map(q => { const a = drillAcc(q.topic); return a === null ? 0.5 : Math.max(0.08, 1 - a); });
    let r = Math.random() * w.reduce((x, y) => x + y, 0);
    p = pool[w.findIndex(x => (r -= x) <= 0)] || pool[0];
  } else {
    p = pool[Math.floor(Math.random() * pool.length)];
  }
  drill.recent = [p.id, ...drill.recent].slice(0, 40);
  const pb = playbook(p.topic);
  const exclude = new Set([p.topic, ...(pb.accepts || [])]);
  const wrong = shuffle(pb.neighbours.filter(t => !exclude.has(t) && playbook(t))).slice(0, 3);
  const others = shuffle(Object.keys(PLAYBOOKS).filter(t => !exclude.has(t) && !wrong.includes(t)));
  while (wrong.length < 3) wrong.push(others.pop());
  return { p, m: map[p.id], options: shuffle([p.topic, ...wrong]) };
}

function drillStatementHTML(st) {
  return `<div class="dr-statement">
    ${st.text.map(t => `<p>${learnInline(t)}</p>`).join('')}
    ${st.example && st.example.length ? `<div class="dr-example">${st.example.map(l => `<code>${esc(l)}</code>`).join('')}</div>` : ''}
    ${st.constraints && st.constraints.length ? `<ul class="dr-cons">${st.constraints.map(c => `<li>${learnInline(c)}</li>`).join('')}</ul>` : ''}
  </div>`;
}

function drillVerdictHTML(card, picked) {
  const { p, m } = card;
  const pb = playbook(p.topic);
  const accepted = (pb.accepts || []).includes(picked);
  const right = picked === p.topic || accepted;
  const mine = playbook(picked);
  const fam = problemFamily(p.id);
  return `<div class="dr-verdict ${right ? 'is-right' : 'is-wrong'}">
    <p class="dr-verdict-head">${right
      ? `${accepted ? 'Fair call' : 'Right'} — <b>${esc(pb.name)}</b>${accepted ? ` (it lives under ${esc(pb.name)}; ${esc(mine.name)} is a fair reading too)` : ''}`
      : `Not quite — this is <b>${esc(pb.name)}</b>, not ${esc(mine.name)}`}</p>
    <div class="dr-teach">
      <div><h4>The tells</h4><ul>${pb.signals.slice(0, 3).map(s => `<li>${learnInline(s)}</li>`).join('')}</ul></div>
      <div><h4>The move</h4><p>${fam ? `<b>${esc(fam.family.name)}</b>. ` : ''}${m && m.idea ? `${learnInline(m.idea)}.` : ''}</p></div>
      ${right ? '' : `<div class="dr-contrast"><h4>Telling them apart</h4>
        <p><b>${esc(mine.name)}</b> — ${esc(mine.tagline)}</p>
        <p><b>${esc(pb.name)}</b> — ${esc(pb.tagline)}</p></div>`}
    </div>
    <p class="dr-reveal">It was <b>LC ${esc(p.lc)} · ${esc(p.title)}</b> <span class="dr-diff d-${p.diff}">${p.diff}</span>
      <a href="#/p/${p.topic}/${p.seq}">Open the problem</a><a href="#/t/${p.topic}">${esc(pb.name)} playbook</a></p>
  </div>`;
}

function drillStatsHTML() {
  const stats = drillStore().stats;
  const rows = Object.keys(PLAYBOOKS).map(t => ({ t, s: stats[t] })).filter(r => r.s && r.s[1]);
  const s = drill.session;
  const pct = x => `${Math.round(x * 100)}%`;
  return `
    <div class="dr-score">
      <div><b>${s.total ? pct(s.right / s.total) : '—'}</b><span>this session · ${s.right}/${s.total}</span></div>
      <div><b>${s.streak}</b><span>in a row</span></div>
      <div><b>${drillStore().best || 0}</b><span>best streak</span></div>
    </div>
    <h4 class="dr-side-h">By pattern ${rows.length ? '<span>weakest first</span>' : ''}</h4>
    ${rows.length ? `<ul class="dr-bars">${rows.sort((a, b) => a.s[0] / a.s[1] - b.s[0] / b.s[1]).map(r => {
      const a = r.s[0] / r.s[1];
      return `<li><a href="#/t/${r.t}">${esc(playbook(r.t).name)}</a><i style="--a:${(a * 100).toFixed(0)}%" class="${a < .5 ? 'is-low' : a < .8 ? 'is-mid' : 'is-ok'}"></i><em>${r.s[0]}/${r.s[1]}</em></li>`;
    }).join('')}</ul>` : '<p class="dr-side-empty">Answer a few cards and your weakest patterns show up here.</p>'}`;
}

async function renderDsaDrill() {
  const host = $('#viewDsaDrill');
  host.innerHTML = `<div class="dr-page"><p class="dr-loading">Dealing a card…</p></div>`;
  const map = await dsaMap();
  if (curView !== 'dsa-drill') return;
  if (!drill.card) { drill.card = drillDeal(map); drill.picked = null; }
  paintDrill(host, map);
}

function paintDrill(host, map) {
  const c = drill.card;
  host.innerHTML = `
  <div class="dr-page">
    <nav class="tp-crumb" aria-label="Breadcrumb">
      <a href="#/dsa"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 18l-6-6 6-6"/></svg>All patterns</a>
      <span class="tp-crumb-sep" aria-hidden="true">/</span><a href="#/dsa-patterns">Cheat sheet</a>
    </nav>
    <header class="dr-hero">
      <p class="dr-eyebrow">Recognition drill</p>
      <h1>Name the pattern</h1>
      <p class="dr-lede">Interviews are decided in the first ninety seconds, when you map a statement onto a technique. Read the problem — the title is hidden, because it often gives the game away — and pick the pattern. <kbd>1</kbd>–<kbd>4</kbd> to answer, <kbd>Enter</kbd> for the next card.</p>
      <div class="seg dr-modes" role="group" aria-label="Deal">${Object.entries(DRILL_MODES).map(([k, l]) =>
        `<button type="button" data-mode="${k}" class="${drill.mode === k ? 'is-on' : ''}" aria-pressed="${drill.mode === k}">${l}</button>`).join('')}</div>
    </header>
    <div class="dr-layout">
      <section class="dr-card" aria-live="polite">
        ${c ? `
          <p class="dr-card-kicker">Card ${drill.session.total + (drill.picked ? 0 : 1)} · ${c.p.diff}</p>
          ${drillStatementHTML(c.m.statement)}
          <div class="dr-options" role="group" aria-label="Which pattern?">
            ${c.options.map((t, i) => {
              const pb = playbook(t);
              const isAns = t === c.p.topic, isPick = t === drill.picked;
              const state = !drill.picked ? '' : isAns ? ' is-answer' : isPick ? ' is-picked' : ' is-dim';
              return `<button type="button" class="dr-opt${state}" data-opt="${t}" ${drill.picked ? 'disabled' : ''}>
                <kbd>${i + 1}</kbd><span><b>${esc(pb.name)}</b><em>${esc(pb.tagline)}</em></span></button>`;
            }).join('')}
          </div>
          ${drill.picked ? drillVerdictHTML(c, drill.picked) + `<div class="dr-next-row"><button type="button" class="dr-next" data-next>Next card <kbd>Enter</kbd></button></div>` : ''}
        ` : '<p class="dr-loading">No statements available for this deal. Switch to Mixed.</p>'}
      </section>
      <aside class="dr-side">${drillStatsHTML()}
        <a class="dr-sheet" href="#/dsa-patterns">Open the pattern cheat sheet</a>
      </aside>
    </div>
  </div>`;

  host.onclick = e => {
    const opt = e.target.closest('[data-opt]');
    if (opt && !drill.picked) return drillAnswer(host, map, opt.dataset.opt);
    if (e.target.closest('[data-next]')) return drillNext(host, map);
    const mode = e.target.closest('[data-mode]');
    if (mode) { drill.mode = mode.dataset.mode; drill.card = drillDeal(map); drill.picked = null; paintDrill(host, map); }
  };
  if (drill.picked) host.querySelector('[data-next]')?.focus({ preventScroll: true });
}

function drillAnswer(host, map, topic) {
  const c = drill.card;
  drill.picked = topic;
  const pb = playbook(c.p.topic);
  const right = topic === c.p.topic || (pb.accepts || []).includes(topic);
  const d = drillStore();
  const s = d.stats[c.p.topic] ??= [0, 0];
  s[1]++; if (right) s[0]++;
  drill.session.total++;
  if (right) { drill.session.right++; drill.session.streak++; } else drill.session.streak = 0;
  d.best = Math.max(d.best || 0, drill.session.streak);
  drillSave();
  paintDrill(host, map);
  host.querySelector('.dr-verdict')?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function drillNext(host, map) {
  drill.card = drillDeal(map);
  drill.picked = null;
  paintDrill(host, map);
  host.scrollTop = 0;
  $('#main')?.scrollTo?.({ top: 0 });
  window.scrollTo({ top: 0 });
}

document.addEventListener('keydown', e => {
  if (typeof curView === 'undefined' || curView !== 'dsa-drill' || !drill.card) return;
  if (e.metaKey || e.ctrlKey || e.altKey || /INPUT|TEXTAREA/.test(document.activeElement?.tagName || '')) return;
  const host = $('#viewDsaDrill');
  if (!drill.picked && /^[1-4]$/.test(e.key)) {
    const t = drill.card.options[+e.key - 1];
    if (t) { e.preventDefault(); drillAnswer(host, dsaMapData || {}, t); }
  } else if (drill.picked && (e.key === 'Enter' || e.key === 'ArrowRight')) {
    e.preventDefault(); drillNext(host, dsaMapData || {});
  }
});

/* ======================================================== cheat sheet ===== */
const TRIAGE = [
  ['Is the input sorted — or would sorting it cost nothing you care about?', ['05_binary_search', '02_two_pointers']],
  ['Is the answer a contiguous subarray or substring?', ['03_sliding_window', '04_prefix_sum']],
  ['“Have I seen it?”, counts, pairs in an unsorted array?', ['01_arrays_hashing']],
  ['Next greater / smaller, nesting, or undo?', ['06_stack']],
  ['Top k, k-th, merge k sorted, or a running median?', ['12_heap_priority_queue']],
  ['Is it a tree, a grid, or things with connections?', ['10_trees', '14_graphs', '15_advanced_graphs']],
  ['Asked for ALL combinations, permutations or placements?', ['09_recursion_backtracking']],
  ['Count the ways, the min cost, or can-you-reach — with repeated subproblems?', ['16_dp_1d', '17_dp_2d']],
  ['Is a locally best choice provably safe?', ['18_greedy']],
  ['A list of [start, end] pairs?', ['19_intervals']],
  ['Prefixes, a dictionary of words, autocomplete?', ['13_trie']],
  ['O(1) extra space with pairs that cancel?', ['20_bit_manipulation']],
  ['Design a class whose every operation must be O(1)?', ['25_design']],
  ['Range queries with updates in between?', ['26_segment_tree_fenwick']],
];
const CONSTRAINTS = [
  ['n ≤ 10–12', 'O(n!)', 'permutations, brute-force backtracking'],
  ['n ≤ 15–22', 'O(2ⁿ)', 'subsets, bitmask DP'],
  ['n ≤ 100', 'O(n³)', 'triple loop, Floyd–Warshall, interval DP'],
  ['n ≤ 1,000–5,000', 'O(n²)', 'double loop, most 2D DP'],
  ['n ≤ 10⁵–10⁶', 'O(n log n)', 'sort, heap, binary search'],
  ['n ≤ 10⁷–10⁸', 'O(n)', 'one pass, two pointers, sliding window'],
  ['n ≥ 10⁹', 'O(log n) or O(1)', 'binary search on the answer, math'],
];
let sheetQuery = '';

function renderDsaPatterns() {
  const host = $('#viewDsaPatterns');
  const tag = t => `<a class="cs-tag" href="#/t/${t}">${esc(playbook(t).name)}</a>`;
  host.innerHTML = `
  <div class="cs-page">
    <nav class="tp-crumb" aria-label="Breadcrumb">
      <a href="#/dsa"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 18l-6-6 6-6"/></svg>All patterns</a>
      <span class="tp-crumb-sep" aria-hidden="true">/</span><a href="#/dsa-drill">Recognition drill</a>
    </nav>
    <header class="dr-hero">
      <p class="dr-eyebrow">Pattern cheat sheet</p>
      <h1>From statement to technique</h1>
      <p class="dr-lede">Three passes, in order: read the constraints (they tell you the complexity you can afford), ask the triage questions, then check the pattern's signals and its look-alikes. Search for a phrase from the problem you are stuck on.</p>
    </header>

    <div class="cs-top">
      <section class="cs-box">
        <h2><span>1</span>Read the constraints first</h2>
        <table class="cs-table"><thead><tr><th>Input size</th><th>Affordable</th><th>Usually means</th></tr></thead>
          <tbody>${CONSTRAINTS.map(([n, o, w]) => `<tr><td>${n}</td><td><code>${o}</code></td><td>${w}</td></tr>`).join('')}</tbody></table>
      </section>
      <section class="cs-box">
        <h2><span>2</span>Ask the triage questions</h2>
        <ol class="cs-triage">${TRIAGE.map(([q, ts]) => `<li><p>${esc(q)}</p><div>${ts.map(tag).join('')}</div></li>`).join('')}</ol>
      </section>
    </div>

    <section class="cs-patterns">
      <div class="cs-head">
        <h2><span>3</span>Check the signals</h2>
        <label class="cs-search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>
          <input type="search" placeholder="e.g. “at most k”, sorted, top k, prerequisites" value="${esc(sheetQuery)}" aria-label="Filter patterns by signal"></label>
      </div>
      <div class="cs-grid"></div>
    </section>
  </div>`;
  const grid = $('.cs-grid', host), input = $('.cs-search input', host);
  const paint = () => {
    const q = sheetQuery.trim().toLowerCase();
    const words = q.split(/\s+/).filter(Boolean);
    const cards = Object.entries(PLAYBOOKS).map(([t, pb]) => {
      const hay = [pb.name, pb.tagline, ...pb.signals, ...pb.notThis.flat()].join(' ').toLowerCase();
      if (words.length && !words.every(w => hay.includes(w))) return '';
      const fam = typeof dsaFamily === 'function' ? dsaFamily(t.slice(0, 2)) : { key: '' };
      const mark = s => { let h = learnInline(s); words.forEach(w => { if (w.length > 1) h = h.replace(new RegExp(`(${w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})(?![^<]*>)`, 'gi'), '<mark>$1</mark>'); }); return h; };
      return `<article class="cs-card" data-fam="${fam.key}">
        <header><span class="cs-num">${t.slice(0, 2)}</span><a href="#/t/${t}">${esc(pb.name)}</a></header>
        <p class="cs-tagline">${mark(pb.tagline)}</p>
        <ul>${pb.signals.map(s => `<li>${mark(s)}</li>`).join('')}</ul>
        <details><summary>Looks like it, but…</summary>
          <ul class="cs-not">${pb.notThis.map(([a, b]) => `<li>${mark(a)} <b>→</b> ${mark(b)}</li>`).join('')}</ul></details>
      </article>`;
    }).join('');
    grid.innerHTML = cards || `<p class="cs-empty">No pattern mentions “${esc(sheetQuery)}”. Try a shorter phrase.</p>`;
  };
  input.oninput = () => { sheetQuery = input.value; paint(); };
  input.addEventListener('keydown', e => e.stopPropagation());
  paint();
}

/* ============================================ DSA home: the learning loop == */
function dsaLearnLoopHTML() {
  const d = (DATA.state.docs && DATA.state.docs[DRILL_DOC]) || {};
  const seen = Object.values(d.stats || {}).reduce((a, s) => a + s[1], 0);
  const right = Object.values(d.stats || {}).reduce((a, s) => a + s[0], 0);
  const steps = [
    ['Recognise', 'Read the pattern’s playbook: its signals, its look-alikes, its template.'],
    ['Attempt', 'Solve the first problem in a family. At 25 min, climb one rung of the hint ladder.'],
    ['Watch', 'Step through the visualizer. Turn on Predict mode and call each step before it happens.'],
    ['Transfer', 'Read “Make it transfer”, then solve a sibling with the same move while it is fresh.'],
    ['Retain', 'Re-solve cold on the review schedule, and keep the recognition drill in your warm-up.'],
  ];
  return `<section class="dsa-loop" aria-label="How to learn a pattern">
    <div class="dsa-loop-steps">
      <p class="dsa-loop-kicker">How to learn a pattern</p>
      <ol>${steps.map(([h, p], i) => `<li style="--i:${i}"><b><span>${i + 1}</span>${h}</b><p>${p}</p></li>`).join('')}</ol>
    </div>
    <div class="dsa-loop-tools">
      <a class="dsa-tool" href="#/dsa-drill">
        <span class="dsa-tool-kicker">Recognition drill</span>
        <b>Name the pattern from the statement</b>
        <span class="dsa-tool-meta">${seen ? `${Math.round(right / seen * 100)}% right over ${seen} card${seen === 1 ? '' : 's'}` : `${DATA.problems.length} real statements, titles hidden`}</span>
      </a>
      <a class="dsa-tool" href="#/dsa-patterns">
        <span class="dsa-tool-kicker">Cheat sheet</span>
        <b>Constraints, triage, every signal</b>
        <span class="dsa-tool-meta">28 patterns on one searchable page</span>
      </a>
    </div>
  </section>`;
}
