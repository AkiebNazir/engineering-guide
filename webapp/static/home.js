/* ============================================================================
   Home (#/home) — the landing page behind the logo.

   The dashboard answers "am I on pace?" and the DSA page answers "which pattern
   next?". This page answers "what is this place?": one sentence on what the
   studio is, how a study session works, and every module as a card that opens
   it. Counts and progress are live and patched in as each module list arrives.

   Reads app.js globals: DATA, $, $$, esc, SECTION_ICON, sectionName,
   sectionHref, sectionCount, MODULES.
   ========================================================================= */
'use strict';

const HOME_GROUPS = [
  { name: 'Interview core', note: 'What the loop actually tests',
    mods: ['dsa', 'sd', 'swd', 'csfund', 'behavioral'] },
  { name: 'Build in Go and Python', note: 'Production code, run against real tests',
    mods: ['go', 'py', 'gostdlib', 'pystdlib'] },
  { name: 'Data and APIs', note: 'The layers every service sits on',
    mods: ['sql', 'nosql', 'api'] },
  { name: 'AI engineering', note: 'From the maths to agents in production',
    mods: ['roadmap', 'library', 'agentic'] },
];

const HOME_BLURB = {
  dsa: () => `${DATA.topics.length} patterns, each with a topic guide, graded problems in Python and Go, and a step-by-step visualizer.`,
  sd: () => 'Requirements first, then every box earns its place. Building blocks, patterns and 21 full designs.',
  swd: () => 'Foundations, code that survives change, and 17 low-level design problems solved against real tests.',
  csfund: () => 'Operating systems, networking, databases and architecture: the deep dives that separate senior engineers.',
  behavioral: () => 'The Googleyness and Leadership loop: STAR blueprints and leadership scenarios.',
  go: () => 'Production Go, not puzzles: services, concurrency, I/O, storage and testing.',
  py: () => 'The same production problems in idiomatic Python 3.12: asyncio, Protocols, pytest.',
  gostdlib: () => 'The Go standard library package by package, level 1 to a realistic level 10 capstone.',
  pystdlib: () => 'The Python standard library package by package, level 1 to a realistic level 10 capstone.',
  sql: () => 'PostgreSQL end to end: joins and transactions through indexing, migrations and pooling.',
  nosql: () => 'MongoDB schema design and aggregation, Redis data structures, caching and locking.',
  api: () => 'REST, GraphQL, gRPC, WebSockets, Webhooks and more, each with runnable labs in Python and Go.',
  roadmap: () => 'A day-by-day path from vectors and probability to fine-tuning, agents and LLMs in production.',
  library: () => 'The tools you will actually import, one deep dive each: core API and the traps.',
  agentic: () => 'How LLM systems work underneath: the agent loop, retrieval, vector search and GraphRAG.',
};

const HOME_STEPS = [
  { n: '01', name: 'Read', text: 'Theory guides written for 30-minute sessions, with zoomable diagrams and checks after every section.',
    icon: '<path d="M4 5a2 2 0 012-2h12v16H6a2 2 0 00-2 2z"/><path d="M4 19V5M9 8h6M9 12h6"/>' },
  { n: '02', name: 'Run', text: 'Write Python or Go in the built-in editor. Code runs as a real process against real tests.',
    icon: '<path d="M8 9l-4 3 4 3M16 9l4 3-4 3M13.5 6l-3 12"/>' },
  { n: '03', name: 'Visualize', text: 'Step through 50 algorithms with the matching line highlighted, and feed them your own input.',
    icon: '<circle cx="12" cy="12" r="9"/><path d="M10 8.5v7l6-3.5z"/>' },
  { n: '04', name: 'Retain', text: 'Solved problems return as cold re-solves after 1, 3, 10 and 30 days, until they stick.',
    icon: '<path d="M21 12a9 9 0 11-2.6-6.4"/><path d="M21 3v6h-6"/>' },
];

const HOME_ARROW = '<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg>';

function homeCount(key) {
  const c = sectionCount(key);
  const noun = key === 'dsa' ? 'problems' : MODULES[key].noun;
  if (!c) return { text: '&nbsp;', pct: 0 };
  return { text: `<b>${c.done}</b> / ${c.total} ${esc(noun)}`, pct: c.total ? c.done / c.total * 100 : 0 };
}

function renderHome() {
  let idx = 0;
  const card = key => {
    const c = homeCount(key);
    return `
      <a class="hc" data-m="${key}" href="${sectionHref(key)}" style="--i:${idx++}">
        <span class="hc-icon"><svg viewBox="0 0 24 24">${SECTION_ICON[key]}</svg></span>
        <span class="hc-name">${esc(sectionName(key))}</span>
        <span class="hc-text">${esc(HOME_BLURB[key]())}</span>
        <span class="hc-foot">
          <span class="hc-count" data-count="${key}">${c.text}</span>
          <span class="hc-go">${HOME_ARROW}</span>
        </span>
        <span class="hc-bar" aria-hidden="true"><i data-bar="${key}" style="width:${c.pct}%"></i></span>
      </a>`;
  };

  $('#viewHome').innerHTML = `
    <div class="home">
      <section class="hero">
        <div class="hero-copy">
          <span class="hero-badge"><img src="/logo.svg" alt="" width="20" height="20">Ultimate Engineering Guide</span>
          <h1 class="hero-title">One workshop for the whole engineering craft.</h1>
          <p class="hero-sub">Algorithms, system design, production Go and Python, data, and AI.
            Read the theory, run real code, watch the algorithm move, and let spaced repetition
            make it stick. Everything runs on your machine and saves as you go.</p>
          <div class="hero-cta">
            <a class="btn-hero primary" href="#/dsa">Start with DSA ${HOME_ARROW}</a>
            <a class="btn-hero" href="#/dashboard">Open my dashboard</a>
          </div>
          <div class="hero-keys">
            <span><kbd>⌘</kbd><kbd>K</kbd> jump anywhere</span>
            <span><kbd>/</kbd> search everything</span>
            <span><kbd>⌘</kbd><kbd>B</kbd> toggle sidebar</span>
          </div>
        </div>

        <div class="hero-panel" aria-hidden="true">
          <div class="hp-bar"><i></i><i></i><i></i><span>two_sum.py</span><em>Python</em></div>
          <pre class="hp-code"><span class="k">def</span> <span class="f">two_sum</span>(nums, target):
    seen = {}
    <span class="k">for</span> i, x <span class="k">in</span> <span class="f">enumerate</span>(nums):
        <span class="k">if</span> target - x <span class="k">in</span> seen:
            <span class="k">return</span> [seen[target - x], i]
        seen[x] = i</pre>
          <div class="hp-run">
            <span class="hp-ok">✓ 12 / 12 tests passed</span>
            <span class="hp-dim">0.04s</span>
          </div>
          <div class="hp-viz">
            ${[3, 7, 2, 9, 5, 8, 4].map((h, i) => `<i class="${i === 1 || i === 3 ? 'on' : ''}" style="--h:${h * 9}%;--d:${i * 90}ms"></i>`).join('')}
          </div>
        </div>
      </section>

      <section class="home-stats" id="homeStats"></section>

      <section class="steps">
        ${HOME_STEPS.map((s, i) => `
          <div class="step" style="--i:${i}">
            <span class="step-icon"><svg viewBox="0 0 24 24">${s.icon}</svg></span>
            <span class="step-n">${s.n}</span>
            <h3>${s.name}</h3>
            <p>${s.text}</p>
          </div>`).join('')}
      </section>

      ${HOME_GROUPS.map(g => `
        <section class="hgroup">
          <div class="hgroup-head"><h2>${g.name}</h2><span>${g.note}</span></div>
          <div class="hgrid">${g.mods.map(card).join('')}</div>
        </section>`).join('')}
    </div>`;

  updateHome();
}

/* Counts arrive one module at a time; patch them in place so the cards do not
   re-run their entrance animation on every response. */
function updateHome() {
  if (!$('#viewHome .home')) return;
  let done = 0, total = 0, loaded = 0;
  for (const key of SECTIONS) {
    const c = sectionCount(key);
    if (!c) continue;
    loaded++; done += c.done; total += c.total;
    const h = homeCount(key);
    const t = $(`[data-count="${key}"]`, $('#viewHome')), b = $(`[data-bar="${key}"]`, $('#viewHome'));
    if (t) t.innerHTML = h.text;
    if (b) b.style.width = `${h.pct}%`;
  }
  const stat = (v, l) => `<div class="hs"><b>${v}</b><span>${l}</span></div>`;
  $('#homeStats').innerHTML =
    stat(SECTIONS.length, 'modules') +
    stat(loaded === SECTIONS.length ? total.toLocaleString() : '…', 'problems, chapters and labs') +
    stat('Py + Go', 'run for real, side by side') +
    stat(loaded === SECTIONS.length ? done.toLocaleString() : '…', 'completed so far');
}
