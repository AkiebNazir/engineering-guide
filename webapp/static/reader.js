/* ============================================================================
   Ultimate Engineering Guide — learning modules

   System Design, Go/Py Engineering, AI Roadmap, AI Library Guides and
   Agentic AI. Every module gets the same three things the DSA side has:

     · its own colour identity (data-module on #app re-points --accent)
     · a module side navigation that replaces the DSA topic tree
     · a landing page and a reader built for 30-minute sessions — section
       checks, highlights, zoomable diagrams, page themes, keyboard paging

   Reading state is saved to progress.json under state.docs.
   ========================================================================= */
'use strict';

const CDN = 'https://cdnjs.cloudflare.com/ajax/libs';

let curModule = null;      // 'sd' | 'swd' | 'roadmap' | 'library' | 'agentic' | 'go' | 'py' | … | null
let curDoc = null;         // { mod, id, key, item } while the reader is open
let chromeModule = null;   // module the sidebar was last drawn for
let modFilter = 'all';     // all | todo | done
const modCache = new Map();

const LIB_GROUPS = [
  [4, 'Data & classical ML'], [7, 'Deep learning frameworks'], [10, 'Training & fine-tuning'],
  [16, 'LLM apps & agents'], [19, 'Vector search'], [22, 'Inference & serving'], [99, 'MLOps & evaluation'],
];
const ENG_GROUPS = [
  [3, 'APIs & HTTP'], [8, 'I/O, files & config'], [11, 'Data & persistence'], [16, 'Concurrency'],
  [21, 'Design & testing'], [25, 'Performance & services'], [99, 'Advanced internals'],
];
const groupFor = (table, num) => (table.find(([max]) => +num <= max) || table[table.length - 1])[1];

const MODULES = {
  api: {
    hash: 'apis', nav: 'navApis', name: 'API Technologies', noun: 'technologies', motif: 'api',
    list: '/api/apis', doc: '/api/apis-doc',
    tagline: 'One complete theory guide per API style - REST, GraphQL, Protobuf, gRPC, WebSockets, Webhooks, SOAP - plus the fundamentals they share. Each has runnable labs in Python and Go, from basics through production topics and framework examples.',
    group: it => it.id.split('/')[0],
    label: it => it.id.split('/')[0],
    kicker: it => `API Technology · ${it.id.split('/')[0]}`,
  },
  sd: {
    hash: 'system-design', nav: 'navSystemDesign', name: 'System Design', noun: 'chapters', motif: 'sd',
    list: '/api/sd', doc: '/api/sd-doc',
    tagline: 'Requirements first, then every box on the diagram earns its place. Building blocks, patterns, and 21 designs to practise before you peek.',
    group: it => it.group,
    label: it => it.num || '',
    kicker: it => it.kind === 'problem' ? `Practice problem ${it.num}` : it.group,
    clean: t => t.replace(/^\d{2,3}\s*[—–:-]\s*/, ''),
  },
  swd: {
    hash: 'software-design', nav: 'navSoftwareDesign', name: 'Software Design', noun: 'steps', motif: 'swd',
    list: '/api/software-design', doc: '/api/software-design-doc',
    tagline: 'Designing code, in order: foundations, code that survives change, services in production, leading design — then 17 LLD problems solved against real tests.',
    group: it => it.group,
    label: it => `${it.step}`,
    kicker: it => it.kind === 'lld' ? `Step ${it.step} · LLD problem ${it.num}${it.tier ? ` · ${it.tier}` : ''}`
      : it.num ? `Step ${it.step} · Chapter ${it.num}` : 'Step 0 · Start here',
  },
  roadmap: {
    hash: 'roadmap', nav: 'navRoadmap', name: 'AI Roadmap', noun: 'lessons', motif: 'roadmap',
    list: '/api/roadmap', doc: '/api/roadmap-doc', compact: true, timeline: true,
    tagline: 'A day-by-day path from vectors and probability to fine-tuning, agents, and LLMs in production.',
    group: it => it.phase,
    label: it => it.kind === 'day' ? `Day ${it.day}` : 'Capstone',
    kicker: it => it.kind === 'day' ? `Day ${it.day} · ${it.phase}` : 'Capstone project',
    clean: t => t.replace(/^Day\s*\d+\s*[:.\-—–]\s*/i, ''),
  },
  library: {
    hash: 'library-guides', nav: 'navLibraryGuides', name: 'AI Library Guides', noun: 'guides', motif: 'library',
    list: '/api/library-guides', doc: '/api/library-guide-doc',
    tagline: 'The tools you will actually import, one deep dive each: what they are for, the core API, and the traps.',
    group: it => groupFor(LIB_GROUPS, it.num),
    label: it => it.num,
    kicker: it => `Guide ${it.num} · ${groupFor(LIB_GROUPS, it.num)}`,
  },
  agentic: {
    hash: 'agentic-ai', nav: 'navAgenticAI', name: 'Agentic AI', noun: 'modules', motif: 'agentic',
    list: '/api/agentic-ai', doc: '/api/agentic-ai-doc',
    tagline: 'How LLM systems work underneath: the runtime, the agent loop, retrieval, vector search, and GraphRAG, down to the state machine.',
    group: () => 'Modules',
    label: it => `Module ${+it.num}`,
    kicker: it => `Module ${+it.num} of 5`,
    clean: t => t.replace(/^Module\s*\d+\s*[—–:-]\s*/i, ''),
  },
  go: {
    hash: 'eng/go', nav: 'navGoEngineering', name: 'Go Engineering', noun: 'problems', motif: 'eng', eng: 'go',
    tagline: 'Production Go, not puzzles: services, concurrency, I/O, storage, and testing. Read the brief, write it, then run the real tests.',
    group: it => groupFor(ENG_GROUPS, it.num),
    label: it => it.num,
  },
  py: {
    hash: 'eng/py', nav: 'navPyEngineering', name: 'Py Engineering', noun: 'problems', motif: 'eng', eng: 'py',
    tagline: 'The same production problems in idiomatic Python 3.12: asyncio, Protocols, context managers, and pytest.',
    group: it => groupFor(ENG_GROUPS, it.num),
    label: it => it.num,
  },
  csfund: {
    hash: 'cs-fundamentals', nav: 'navCSFundamentals', name: 'CS Fundamentals', noun: 'deep dives', motif: 'csfund',
    list: '/api/cs-fundamentals', doc: '/api/cs-fundamentals-doc',
    tagline: 'Operating systems, networking, databases, and software architecture — the L5 deep dives that separate senior engineers from everyone else.',
    group: () => 'Deep Dives',
    label: it => `${+it.num}`,
    kicker: it => `Deep Dive ${+it.num}`,
    clean: t => t.replace(/^L5 Deep Dive:\s*/i, ''),
  },
  behavioral: {
    hash: 'google-behavioral', nav: 'navGoogleBehavioral', name: 'Google Behavioral', noun: 'guides', motif: 'behavioral',
    list: '/api/google-behavioral', doc: '/api/google-behavioral-doc',
    tagline: 'The Googleyness & Leadership loop: STAR blueprints, L5 leadership scenarios, and the traits that decide your level.',
    group: () => 'Guides',
    label: it => `${+it.num}`,
    kicker: it => `Guide ${+it.num}`,
  },
  sql: {
    hash: 'sql', nav: 'navSql', name: 'SQL', noun: 'levels', motif: 'sql',
    list: '/api/sql', doc: '/api/sql-doc',
    tagline: 'Relational databases end to end with PostgreSQL: tables and joins through transactions, indexing, injection, migrations, pooling, and a client capstone.',
    group: it => it.group,
    label: it => it.num || '',
    kicker: it => it.kind === 'doc' ? 'Start here' : `Level ${+it.num}`,
  },
  nosql: {
    hash: 'nosql', nav: 'navNosql', name: 'NoSQL', noun: 'levels', motif: 'nosql',
    list: '/api/nosql', doc: '/api/nosql-doc',
    tagline: 'The document and key-value families in practice: MongoDB schema design and aggregation, Redis data structures, caching, and locking.',
    group: it => it.group,
    label: it => it.num || '',
    kicker: it => it.kind === 'doc' ? 'Start here' : `${it.group} · Level ${+it.num}`,
  },
  /* The deep-dive behind each DSA pattern — one guide per language (PyDSA/<topic>/_TOPIC_GUIDE.md
     and GoDSA/<topic>/_TOPIC_GUIDE.md), each opened as its own reading page from the pattern
     page. Not sidebar sections — they belong to DSA, so the module colour and the DSA row stay
     as they are. The two are separate modules so each keeps its own reading progress. */
  dsaguide: {
    hash: 'dsa-guide', name: 'Topic guide', noun: 'guides', motif: 'dsa', guideLang: 'py',
    list: '/api/dsa-guides?lang=py', doc: '/api/dsa-guide-doc?lang=py',
    group: () => 'Pattern guide',
    label: it => it.num,
    kicker: it => `Pattern ${+it.num} · Python topic guide`,
    clean: t => t.replace(/^Topic\s*\d+\s*[·—–:-]\s*/i, '').replace(/\s*[—–-]\s*Python Deep Dive$/i, ''),
    back: it => ({ href: `#/t/${it.id}`, label: 'Pattern page' }),
  },
  dsaguidego: {
    hash: 'dsa-guide-go', name: 'Topic guide (Go)', noun: 'guides', motif: 'dsa', guideLang: 'go',
    list: '/api/dsa-guides?lang=go', doc: '/api/dsa-guide-doc?lang=go',
    group: () => 'Pattern guide',
    label: it => it.num,
    kicker: it => `Pattern ${+it.num} · Go topic guide`,
    clean: t => t.replace(/^Topic\s*\d+\s*[·—–:-]\s*/i, '').replace(/\s*[—–-]\s*Go Deep Dive$/i, ''),
    back: it => ({ href: `#/t/${it.id}`, label: 'Pattern page' }),
  },
  pystdlib: {
    hash: 'py-stdlib', nav: 'navPyStdlib', name: 'Py Standard Library', noun: 'packages', motif: 'stdlib',
    list: '/api/stdlib?lang=py', stdlibLang: 'py',
    tagline: 'The standard library itself, package by package: one most-common call at level 1, ramping to a realistic capstone at level 10 — every example runs and edits right here.',
    group: () => 'Packages',
    label: it => it.num,
    kicker: it => `Package ${+it.num} · ${it.levels.length} levels`,
  },
  gostdlib: {
    hash: 'go-stdlib', nav: 'navGoStdlib', name: 'Go Standard Library', noun: 'packages', motif: 'stdlib',
    list: '/api/stdlib?lang=go', stdlibLang: 'go',
    tagline: 'The Go standard library, package by package: one most-common call at level 1, ramping to a realistic capstone at level 10 — every example runs and edits right here.',
    group: () => 'Packages',
    label: it => it.num,
    kicker: it => `Package ${+it.num} · ${it.levels.length} levels`,
  },
};

/* the two topic-guide modules and the language tree each one reads */
const DSA_GUIDE_ROOT = { dsaguide: 'PyDSA', dsaguidego: 'GoDSA' };
const isDsaGuide = mod => Object.hasOwn(DSA_GUIDE_ROOT, mod);
const modTitle = (m, it) => (m.clean ? m.clean(it.title) : it.title);
// LLD problems live inside Software Design but open in the code workspace.
const isWorkspaceItem = (mod, it) => !!MODULES[mod].eng || it.kind === 'lld';
const engRecId = (mod, it) => `${it.kind === 'lld' ? 'lld' : mod}-eng/${it.id}`;
// stdlib-practice.js: a package is a ladder of levels (like an API type), not a
// single workspace item — its progress is the fraction of levels solved.
const stdlibRecId = (lang, pkg, level) => `stdlib/${lang}/${pkg}/${level}`;
const itemHref = (mod, it) => it.kind === 'lld' ? `#/eng/lld/${it.id}`
  : MODULES[mod].eng ? `#/eng/${mod}/${it.id}`
  : MODULES[mod].stdlibLang ? `#/stdlib-pkg/${MODULES[mod].stdlibLang}/${it.id}`
  : `#/${MODULES[mod].hash}/${it.id}`;
const slug = s => s.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');

async function modItems(mod) {
  const m = MODULES[mod];
  if (m.eng) return DATA.engTopics[m.eng] || [];
  if (!modCache.has(mod)) modCache.set(mod, (await api(m.list)).items);
  return modCache.get(mod);
}
const modItemsSync = mod => MODULES[mod].eng ? (DATA.engTopics[MODULES[mod].eng] || []) : modCache.get(mod);

/* ------------------------------------------------------ reading state -- */
const EMPTY_DOC = Object.freeze({ sections: [], highlights: [] });
const docKey = (mod, id) => `${mod}:${id}`;
const docPeek = key => {
  const d = DATA.state.docs && DATA.state.docs[key];
  return d ? { ...EMPTY_DOC, ...d, sections: d.sections || [], highlights: d.highlights || [] } : EMPTY_DOC;
};

function docRec(key) {
  DATA.state.docs ??= {};
  const d = DATA.state.docs[key] ??= {};
  d.sections ??= [];
  d.highlights ??= [];
  return d;
}
function docSave(key, p) {
  Object.assign(docRec(key), p);
  return post('/api/patch', { doc: key, docPatch: p }).catch(() => {});
}

function progressOf(mod, it) {
  if (MODULES[mod].stdlibLang) {
    const lang = MODULES[mod].stdlibLang, total = it.levels.length;
    const done = it.levels.filter(lv =>
      isDone(DATA.state.problems[stdlibRecId(lang, it.id, lv.id)] || {})).length;
    if (!total) return { state: 'new', pct: 0 };
    if (done === total) return { state: 'done', pct: 100 };
    return { state: done ? 'reading' : 'new', pct: Math.round(done / total * 100) };
  }
  if (isWorkspaceItem(mod, it)) {
    const st = (DATA.state.problems[engRecId(mod, it)] || {}).status || 'todo';
    if (st === 'solved' || st === 'mastered') return { state: 'done', pct: 100 };
    return st === 'attempting' ? { state: 'reading', pct: 40 } : { state: 'new', pct: 0 };
  }
  const d = docPeek(docKey(mod, it.id));
  if (d.done) return { state: 'done', pct: 100 };
  const pct = Math.round(d.pct || 0);
  return { state: pct > 2 || d.sections.length ? 'reading' : 'new', pct };
}

function modPasses(mod, it) {
  const p = progressOf(mod, it);
  if (modFilter === 'todo' && p.state === 'done') return false;
  if (modFilter === 'done' && p.state !== 'done') return false;
  if (query) {
    const m = MODULES[mod];
    const hay = `${m.label(it)} ${it.title} ${it.summary || ''}`.toLowerCase();
    if (!hay.includes(query)) return false;
  }
  return true;
}

function grouped(mod, items) {
  const m = MODULES[mod], order = [], map = new Map();
  for (const it of items) {
    const g = m.group(it);
    if (!map.has(g)) { map.set(g, []); order.push(g); }
    map.get(g).push(it);
  }
  return order.map(name => ({ name, items: map.get(name) }));
}

const CHECK_PATH = '<path d="M5 12.5l4.5 4.5L19 7.5"/>';
const stateGlyph = p => p.state === 'done'
  ? `<span class="sg done" aria-label="Done"><svg viewBox="0 0 24 24">${CHECK_PATH}</svg></span>`
  : `<span class="sg${p.state === 'reading' ? ' reading' : ''}" style="--p:${p.pct}" aria-hidden="true"></span>`;

/* ------------------------------------------------------------- chrome -- *
   Called from showView(): paints the module colour, highlights the nav
   item, and swaps the DSA topic tree for the module's own navigation. */
function syncModuleChrome() {
  const app = $('#app');
  if (curModule && !isDsaGuide(curModule)) app.dataset.module = curModule; else delete app.dataset.module;
  /* The sidebar tree marks the active branch itself (renderSidebar), so there
     is nothing to toggle here any more. */
  if (chromeModule !== curModule) {
    chromeModule = curModule;
    modFilter = 'all';
  }
  hideHlTool();
}

/* The sidebar is one tree over everything now (app.js renderSidebar), so the
   per-module navigation is just that tree redrawn. Kept under the old name
   because the reader calls it whenever reading progress changes. */
function renderModNav() { renderSidebar(); }

/* ------------------------------------------------------- landing page -- */
function pickNext(mod, items) {
  const m = MODULES[mod];
  let best = null;
  for (const it of items) {
    const p = progressOf(mod, it);
    if (p.state !== 'reading') continue;
    const last = isWorkspaceItem(mod, it) ? (DATA.state.problems[engRecId(mod, it)] || {}).lastOpened || 0
      : docPeek(docKey(mod, it.id)).last || 0;
    if (!best || last > best.last) best = { it, last };
  }
  if (best) return { it: best.it, label: isWorkspaceItem(mod, best.it) ? 'Continue' : 'Continue reading' };
  const fresh = items.find(it => progressOf(mod, it).state !== 'done' && (!m.eng || it.has.explanation));
  if (!fresh) return null;
  return { it: fresh, label: items.some(it => progressOf(mod, it).state === 'done') ? 'Up next' : 'Start here' };
}

async function renderModuleHome(mod) {
  const m = MODULES[mod], host = $('#viewModuleHome');
  if (!modItemsSync(mod)) host.innerHTML = `<div class="mod-loading">Loading ${m.name}…</div>`;
  let items;
  try { items = await modItems(mod); } catch (e) {
    host.innerHTML = emptyMsg(`${m.name} could not be listed`, 'The server did not answer. Check it is still running, then reload the page.');
    return;
  }
  // api-practice.js: the runnable Foundation/labs ladders, listed separately
  // from the Theory/Fundamentals docs above — fetched once, cached after.
  if (mod === 'api' && !apiTypesSync()) { try { await apiTypesData(); } catch (e) { /* strip just stays empty */ } }
  if (curModule !== mod || host.hidden) return;

  const done = items.filter(it => progressOf(mod, it).state === 'done').length;
  const pct = items.length ? done / items.length * 100 : 0;
  const hours = Math.round(items.reduce((a, it) => a + (it.minutes || 0), 0) / 60);
  const next = pickNext(mod, items);

  host.innerHTML = `
    <div class="mod-page">
      <header class="mod-hero">
        <div class="mod-hero-copy">
          <h1 class="mod-title">${m.name}</h1>
          <p class="mod-tagline">${m.tagline}</p>
          <dl class="mod-facts">
            <div><dt>${m.noun}</dt><dd>${items.length}</dd></div>
            ${hours ? `<div><dt>hours of reading</dt><dd>${hours}</dd></div>` : ''}
            <div><dt>done</dt><dd>${done}</dd></div>
          </dl>
          ${next ? `<a class="mod-continue" href="${itemHref(mod, next.it)}">
            <span class="mod-continue-label">${next.label}</span>
            <span class="mod-continue-title">${esc(m.label(next.it) && !m.compact ? '' : '')}${esc(modTitle(m, next.it))}</span>
            <svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
          </a>` : ''}
        </div>
        <div class="mod-motif" aria-hidden="true">${motif(mod, items, pct)}</div>
      </header>
      <div class="mod-body" id="modBody"></div>
    </div>`;
  renderModGrid(mod);
  requestAnimationFrame(() => requestAnimationFrame(() => liveMotif(host, mod, items, pct)));
}

/* a stable DOM id per group name, so the rail can jump to its section */
const groupSlug = name => 'g-' + name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

function renderModGrid(mod) {
  const host = $('#modBody');
  if (!host) return;
  const m = MODULES[mod], items = modItemsSync(mod) || [];
  const groups = grouped(mod, items);
  const shown = items.filter(it => modPasses(mod, it)).length;
  const FILTERS = { all: 'All', todo: 'To do', done: 'Done' };
  /* only the groups that survive the filter get a rail chip — a chip that
     scrolls to an empty section is worse than no chip */
  const live = groups.filter(g => g.items.some(it => modPasses(mod, it)));

  host.innerHTML = `
    ${mod === 'api' ? apiPracticeStrip() : ''}
    <div class="mod-toolbar">
      <div class="seg" role="group" aria-label="Show">
        ${Object.entries(FILTERS).map(([f, l]) =>
          `<button data-f="${f}" class="${modFilter === f ? 'is-on' : ''}" aria-pressed="${modFilter === f}">${l}</button>`).join('')}
      </div>
      <span class="mod-shown">${query ? `${shown} matching “${esc(query)}”` : `${shown} of ${items.length} shown`}</span>
    </div>
    ${live.length > 1 ? `<nav class="mod-rail" aria-label="Sections on this page">
      <div class="mod-rail-track">${live.map((g, i) => {
        const gd = g.items.filter(it => progressOf(mod, it).state === 'done').length;
        return `<button class="mod-chip${i ? '' : ' is-on'}" data-to="${groupSlug(g.name)}">
          <span>${esc(g.name)}</span><i>${gd}/${g.items.length}</i></button>`;
      }).join('')}</div>
    </nav>` : ''}
    ${groups.map(g => {
      const vis = g.items.filter(it => modPasses(mod, it));
      if (!vis.length) return '';
      const gd = g.items.filter(it => progressOf(mod, it).state === 'done').length;
      return `<section class="mod-group${m.timeline ? ' timeline' : ''}${gd === g.items.length ? ' complete' : ''}" id="${groupSlug(g.name)}">
        ${groups.length > 1 ? `<header class="mod-group-head">
          <h2>${esc(g.name)}</h2>
          <span class="mod-group-count">${gd} of ${g.items.length}</span>
          <span class="mod-group-bar"><i style="width:${gd / g.items.length * 100}%"></i></span>
        </header>` : ''}
        <div class="mod-grid${m.compact ? ' compact' : ''}">${vis.map(it => modCard(mod, it)).join('')}</div>
      </section>`;
    }).join('') || emptyMsg('Nothing matches', 'Clear the search box or switch the filter back to All.')}`;

  $$('.mod-toolbar .seg button', host).forEach(b => b.onclick = () => {
    modFilter = b.dataset.f;
    renderModGrid(mod);
    renderModNav();
  });
  wireModRail(host);
}

/* The rail is both a jump list and a position readout: clicking a chip scrolls
   to that section, scrolling marks the chip whose section owns the top of the
   page. Long module pages (Software Design runs to four parts and 31 entries)
   were previously one unbroken scroll with no way to reach a part directly. */
let modRailOff = null;

function wireModRail(host) {
  modRailOff?.();
  modRailOff = null;

  const chips = $$('.mod-chip', host);
  if (!chips.length) return;
  const rail = $('.mod-rail', host);
  const view = $('#viewModuleHome');
  const mark = c => chips.forEach(x => x.classList.toggle('is-on', x === c));
  const secOf = c => host.querySelector(`[id="${c.dataset.to}"]`);

  chips.forEach(c => c.onclick = () => {
    const sec = secOf(c);
    if (!sec) return;
    const pad = (rail ? rail.offsetHeight : 0) + 18;
    const top = view.scrollTop + sec.getBoundingClientRect().top - view.getBoundingClientRect().top - pad;
    view.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
    mark(c);
  });

  // scroll spy: the last section whose top has passed just under the rail
  const spy = () => {
    const line = view.getBoundingClientRect().top + (rail ? rail.offsetHeight : 0) + 32;
    let active = chips[0];
    for (const c of chips) {
      const sec = secOf(c);
      if (sec && sec.getBoundingClientRect().top <= line) active = c;
    }
    mark(active);
  };
  view.addEventListener('scroll', spy, { passive: true });
  modRailOff = () => view.removeEventListener('scroll', spy);
  spy();
}

/* one tick per level, lit by that level's status — the whole ladder at a glance */
function stdlibStrip(lang, it) {
  return `<span class="mcard-levels" aria-hidden="true">${it.levels.map(lv => {
    const r = DATA.state.problems[stdlibRecId(lang, it.id, lv.id)];
    return `<i class="st-${r ? r.status : 'todo'}${lv.kind === 'dsa' ? ' is-dsa' : ''}"></i>`;
  }).join('')}</span>`;
}

function modCard(mod, it) {
  const m = MODULES[mod], p = progressOf(mod, it);
  let foot, missing = false;
  if (m.eng) {
    missing = !(it.has.explanation && it.has.solution);
    foot = missing ? 'Not written yet'
      : ['Brief', 'solution', it.has.test ? 'tests' : ''].filter(Boolean).join(' + ');
  } else if (it.kind === 'lld') {
    foot = `${it.minutes} min · brief + tests${it.has.solution ? ' + solution' : ''}`;
  } else if (it.kind === 'problem') {
    foot = `${it.minutes || 1} min · question${it.hasSolution ? ' + reference design' : ''}`;
  } else if (m.stdlibLang) {
    foot = `${it.levels.length} runnable levels`;
  } else {
    foot = `${it.minutes || 1} min read`;
  }
  const state = p.state === 'done' ? 'Done'
    : p.state === 'reading' ? (isWorkspaceItem(mod, it) || m.stdlibLang ? 'In progress' : `${p.pct}% read`) : '';
  return `<a class="mcard st-${p.state}${missing ? ' missing' : ''}" href="${itemHref(mod, it)}" style="--p:${p.pct}">
    <span class="mcard-top"><span class="mcard-num">${esc(m.label(it))}</span>${stateGlyph(p)}</span>
    <span class="mcard-title">${esc(modTitle(m, it))}</span>
    ${!m.compact && it.summary ? `<span class="mcard-sum">${esc(it.summary)}</span>` : ''}
    ${m.stdlibLang ? stdlibStrip(m.stdlibLang, it) : ''}
    <span class="mcard-foot"><span>${foot}</span>${state ? `<span class="mcard-state">${state}</span>` : ''}</span>
    <span class="mcard-bar" aria-hidden="true"></span>
  </a>`;
}

/* ------------------------------------------------------------ motifs -- *
   One small drawing per module, built from the subject itself. Where it
   can, the drawing encodes your progress: the roadmap path is drawn as far
   as you have walked, finished guides are the coloured books on the shelf. */
function motif(mod, items, pct) {
  const kind = MODULES[mod].motif;
  if (kind === 'sd') {
    const wires = ['M78 130H118', 'M172 120C196 120 196 70 222 70', 'M172 140C196 140 196 190 222 190',
      'M257 88V112', 'M257 172V146', 'M292 70C318 70 320 104 326 110', 'M292 190C318 190 320 156 326 150'];
    const box = (x, y, w, h, t, cls = '') =>
      `<rect class="m-box ${cls}" x="${x}" y="${y}" width="${w}" height="${h}" rx="8"/><text x="${x + w / 2}" y="${y + h / 2 + 4}" text-anchor="middle">${t}</text>`;
    return `<svg class="motif" viewBox="0 0 380 260">
      <defs><pattern id="mgrid" width="20" height="20" patternUnits="userSpaceOnUse"><path class="m-grid" d="M20 0H0V20"/></pattern></defs>
      <rect width="380" height="260" rx="16" fill="url(#mgrid)"/>
      ${wires.map(d => `<path class="m-wire" d="${d}"/>`).join('')}
      ${wires.map((d, i) => `<path class="m-flow" style="animation-delay:${-i * .37}s" d="${d}"/>`).join('')}
      ${box(16, 110, 62, 40, 'client')}${box(118, 106, 54, 48, 'LB', 'is-accent')}
      ${box(222, 52, 70, 36, 'api')}${box(222, 172, 70, 36, 'api')}${box(228, 112, 58, 34, 'cache')}
      <path class="m-box" d="M326 108c0-8 44-8 44 0v44c0 8-44 8-44 0z"/><ellipse class="m-box" cx="348" cy="108" rx="22" ry="6"/>
      <text x="348" y="138" text-anchor="middle">db</text>
    </svg>`;
  }
  if (kind === 'roadmap') {
    const d = 'M26 222C92 222 70 150 138 150S212 212 258 150S300 62 356 42';
    return `<svg class="motif" viewBox="0 0 380 260">
      <path class="m-road-base" d="${d}" pathLength="100"/>
      <path class="m-road-done" d="${d}" pathLength="100" style="--p:${pct.toFixed(1)}"/>
      ${Array.from({ length: 6 }, (_, k) => `<circle class="m-stone" data-k="${k}" r="6"/>`).join('')}
      <g class="m-you"><circle class="m-you-halo" r="12"/><circle class="m-you-dot" r="5"/></g>
      <text x="26" y="246">day 0</text><text x="356" y="26" text-anchor="end">day 180</text>
    </svg>`;
  }
  if (kind === 'library') {
    const doneIds = new Set(items.filter(it => progressOf(mod, it).state === 'done').map(it => it.id));
    let x = 20, books = '';
    items.slice(0, 26).forEach((it, i) => {
      const shelf = i < 13 ? 0 : 1;
      if (i === 13) x = 20;
      const w = 18 + (i * 7) % 9, h = 64 + (i * 23) % 36, base = shelf ? 232 : 112;
      const lean = i === 9 || i === 21 ? ' lean' : '';
      books += `<g class="m-book${doneIds.has(it.id) ? ' is-done' : ''}${lean}" style="--i:${i}">
        <rect x="${x}" y="${base - h}" width="${w}" height="${h}" rx="3"/>
        <path class="m-band" d="M${x + 3} ${base - h + 12}h${w - 6}M${x + 3} ${base - 14}h${w - 6}"/></g>`;
      x += w + 4;
    });
    return `<svg class="motif" viewBox="0 0 380 260">
      ${books}<path class="m-shelf" d="M12 114H368M12 234H368"/>
    </svg>`;
  }
  if (kind === 'agentic') {
    const node = (x, y, t, cls = '') =>
      `<rect class="m-box ${cls}" x="${x - 38}" y="${y - 15}" width="76" height="30" rx="15"/><text x="${x}" y="${y + 4}" text-anchor="middle">${t}</text>`;
    return `<svg class="motif" viewBox="0 0 380 260">
      <circle class="m-wire" cx="170" cy="130" r="88"/>
      <circle class="m-flow slow" cx="170" cy="130" r="88"/>
      <g class="m-orbit"><circle class="m-you-dot" cx="170" cy="42" r="5"/></g>
      ${node(170, 42, 'think', 'is-accent')}${node(258, 130, 'act')}${node(170, 218, 'observe')}${node(82, 130, 'remember')}
      <path class="m-wire" d="M208 42H300"/><path class="m-arrow" d="M294 36l7 6-7 6"/>
      ${node(338, 42, 'answer')}
    </svg>`;
  }
  if (kind === 'api') {
    // A client talking to one gateway, which fans out to the API styles the
    // module actually teaches. A style lights up once its theory is read.
    const doneGroups = new Set(items.filter(it => progressOf(mod, it).state === 'done').map(it => it.id.split('/')[0]));
    const styles = ['REST', 'GraphQL', 'gRPC', 'WebSockets', 'Webhooks', 'SOAP'];
    const box = (x, y, w, h, t, cls = '') =>
      `<rect class="m-box ${cls}" x="${x}" y="${y}" width="${w}" height="${h}" rx="8"/><text x="${x + w / 2}" y="${y + h / 2 + 4}" text-anchor="middle">${t}</text>`;
    const sat = styles.map((name, i) => {
      const y = 8 + i * 42, cy = y + 15;
      const cls = doneGroups.has(name) ? 'is-accent' : '';
      return `<path class="m-wire" d="M228 130C252 130 250 ${cy} 276 ${cy}"/>
        <path class="m-flow" style="animation-delay:${-i * .41}s" d="M228 130C252 130 250 ${cy} 276 ${cy}"/>
        ${box(276, y, 90, 30, name, cls)}`;
    }).join('');
    return `<svg class="motif" viewBox="0 0 380 260">
      ${box(14, 110, 64, 40, 'client')}
      <path class="m-wire" d="M78 130H150"/><path class="m-flow" d="M78 130H150"/>
      ${box(150, 105, 78, 50, 'gateway', 'is-accent')}
      ${sat}
    </svg>`;
  }
  if (kind === 'swd') {
    // A class diagram: a use case depending on an interface, two implementations,
    // and a value object. The path underneath fills in as steps are done.
    const cls = (x, y, w, name, rows, cls2 = '') => `<g>
      <rect class="m-box ${cls2}" x="${x}" y="${y}" width="${w}" height="${22 + rows.length * 15}" rx="6"/>
      <text x="${x + w / 2}" y="${y + 15}" text-anchor="middle">${name}</text>
      <path class="m-wire" d="M${x} ${y + 21}h${w}"/>
      ${rows.map((r, i) => `<text x="${x + 8}" y="${y + 35 + i * 15}">${r}</text>`).join('')}</g>`;
    const dots = items.map((it, i) => {
      const x = 22 + i * (336 / Math.max(1, items.length - 1));
      return `<circle class="${progressOf(mod, it).state === 'done' ? 'm-you-dot' : 'm-box'}" cx="${x.toFixed(1)}" cy="240" r="3.2"/>`;
    }).join('');
    return `<svg class="motif" viewBox="0 0 380 260">
      ${cls(128, 12, 124, 'PlaceOrder', ['+__call__(cmd)', '-repo: Repository'], 'is-accent')}
      <path class="m-wire" d="M190 64V92"/><path class="m-arrow" d="M184 86l6 7 6-7"/>
      ${cls(118, 94, 144, '«interface» Repository', ['+get(id)', '+save(order)'])}
      <path class="m-wire" d="M150 146L92 176M230 146L288 176" stroke-dasharray="4 4"/>
      <path class="m-flow slow" d="M150 146L92 176M230 146L288 176"/>
      ${cls(18, 176, 148, 'SqlRepository', ['+save(order)'])}${cls(214, 176, 148, 'InMemoryRepository', ['+save(order)'])}
      <path class="m-wire" d="M22 240H358"/>${dots}
    </svg>`;
  }
  const isDone = it => it && progressOf(mod, it).state === 'done';
  const bar = (x, y, w) => `<rect class="m-box" x="${x}" y="${y}" width="${w}" height="8" rx="4"/>
      ${pct > 0 ? `<rect class="m-box is-accent" x="${x}" y="${y}" width="${Math.max(8, w * pct / 100).toFixed(1)}" height="8" rx="4"/>` : ''}`;
  const table = (x, y, w, name, rows, cls = '') => `<g>
      <rect class="m-box ${cls}" x="${x}" y="${y}" width="${w}" height="${22 + rows.length * 20}" rx="6"/>
      <text x="${x + 8}" y="${y + 15}">${name}</text><path class="m-wire" d="M${x} ${y + 22}h${w}"/>
      ${rows.map((r, i) => `<text x="${x + 8}" y="${y + 37 + i * 20}">${r}</text>`).join('')}</g>`;
  if (kind === 'stdlib') {
    // A snippet that runs and answers OK, a ten-step staircase (the levels of
    // one package), and one square per package — lit as packages are finished.
    const py = MODULES[mod].stdlibLang === 'py';
    const code = py
      ? ['import collections', '', 'c = collections.Counter("hi")', 'c.most_common(1)', '# [("h", 1)]']
      : ['import "sort"', '', 'xs := []int{5, 2, 9, 1}', 'sort.Ints(xs)', '// [1 2 5 9]'];
    const steps = Array.from({ length: 10 }, (_, i) =>
      `<rect class="m-box${i === 9 ? ' is-accent' : ''}" x="${14 + i * 22}" y="${242 - (i + 1) * 7.5}" width="16" height="${(i + 1) * 7.5}" rx="3"/>`).join('');
    const pkgs = items.map((it, i) =>
      `<rect class="${isDone(it) ? 'm-box is-accent' : 'm-box'}" x="${262 + (i % 5) * 20}" y="${150 + Math.floor(i / 5) * 20}" width="14" height="14" rx="4"/>`).join('');
    return `<svg class="motif" viewBox="0 0 380 260">
      <rect class="m-box" x="14" y="14" width="214" height="118" rx="10"/>
      <circle class="m-box" cx="28" cy="28" r="3"/><circle class="m-box" cx="40" cy="28" r="3"/><circle class="m-box is-accent" cx="52" cy="28" r="3"/>
      ${code.map((l, i) => `<text x="26" y="${54 + i * 15}" class="${i === 4 ? 'm-note' : ''}" xml:space="preserve">${l}</text>`).join('')}
      <path class="m-wire" d="M228 60H262"/><path class="m-flow" d="M228 60H262"/><path class="m-arrow" d="M256 54l6 6-6 6"/>
      <rect class="m-box is-accent" x="264" y="14" width="102" height="92" rx="10"/>
      <text x="278" y="38">$ run</text><text x="278" y="62">OK</text>
      <path class="m-wire" d="M278 76h34"/><path class="m-flow slow" d="M278 76h34"/>
      ${steps}
      ${pkgs}
      <text x="262" y="228">${items.length} packages</text>
    </svg>`;
  }
  if (kind === 'sql') {
    // Two tables joined on a key into a result set; the bar is levels done.
    return `<svg class="motif" viewBox="0 0 380 260">
      ${table(14, 22, 116, 'users', ['1  ada', '2  lin', '3  sam'])}
      ${table(14, 132, 116, 'orders', ['u1 book', 'u1 pen', 'u3 lamp'])}
      <path class="m-wire" d="M130 62C190 62 190 112 250 112M130 172C190 172 190 138 250 138"/>
      <path class="m-flow" d="M130 62C190 62 190 112 250 112"/>
      <path class="m-flow" style="animation-delay:-.6s" d="M130 172C190 172 190 138 250 138"/>
      ${table(250, 78, 116, 'JOIN', ['ada · book', 'ada · pen', 'sam · lamp'], 'is-accent')}
      ${bar(250, 176, 116)}<text x="250" y="202">levels done</text>
    </svg>`;
  }
  if (kind === 'nosql') {
    // A document on the left, a key-value store on the right; dots are levels.
    const lines = ['{', '  "_id": 7,', '  "name": "ada",', '  "tags": ["a", "b"]', '}'];
    const kv = ['user:7', 'cart:7', 'top:10', 'sess:x'];
    const dots = items.map((it, i) => {
      const x = 22 + i * (336 / Math.max(1, items.length - 1));
      return `<circle class="${isDone(it) ? 'm-you-dot' : 'm-box'}" cx="${x.toFixed(1)}" cy="222" r="3.2"/>`;
    }).join('');
    return `<svg class="motif" viewBox="0 0 380 260">
      <rect class="m-box" x="14" y="26" width="150" height="112" rx="8"/>
      ${lines.map((l, i) => `<text x="24" y="${48 + i * 17}" xml:space="preserve">${l}</text>`).join('')}
      <path class="m-wire" d="M164 82H230"/><path class="m-flow" d="M164 82H230"/><path class="m-arrow" d="M224 76l6 6-6 6"/>
      <rect class="m-box is-accent" x="232" y="26" width="134" height="112" rx="8"/>
      <path class="m-wire" d="M232 52h134"/><text x="242" y="43">key → value</text>
      ${kv.map((k, i) => `<text x="242" y="${72 + i * 20}">${k}</text><rect class="m-job static" x="318" y="${62 + i * 20}" width="38" height="12" rx="3"/>`).join('')}
      <text x="14" y="176">documents  ·  key-value</text>
      <path class="m-wire" d="M14 190H366"/>${dots}
    </svg>`;
  }
  if (kind === 'csfund') {
    // The stack a request falls through and a response climbs back up; the
    // layers light from the hardware upward as deep dives are finished.
    const layers = ['application', 'database', 'network', 'operating system', 'hardware'];
    const lit = Math.round(pct / 100 * layers.length);
    return `<svg class="motif" viewBox="0 0 380 260">
      ${layers.map((name, i) => `<rect class="m-box${i >= layers.length - lit ? ' is-accent' : ''}" x="90" y="${14 + i * 44}" width="200" height="32" rx="8"/>
        <text x="190" y="${34 + i * 44}" text-anchor="middle">${name}</text>`).join('')}
      <path class="m-wire" d="M52 24V214"/><path class="m-flow slow" d="M52 24V214"/><path class="m-arrow" d="M46 208l6 7 6-7"/>
      <path class="m-wire" d="M328 214V24"/><path class="m-flow slow" style="animation-delay:-3s" d="M328 214V24"/><path class="m-arrow" d="M322 30l6-7 6 7"/>
      <text x="52" y="246" text-anchor="middle">request</text><text x="328" y="246" text-anchor="middle">response</text>
    </svg>`;
  }
  if (kind === 'behavioral') {
    // S-T-A-R, then where a two-minute answer's time should actually go.
    const stars = [['S', 'situation'], ['T', 'task'], ['A', 'action'], ['R', 'result']];
    const split = [[15, 'S'], [10, 'T'], [50, 'A'], [25, 'R']];
    let sx = 20;
    const seg = split.map(([p, l]) => {
      const w = 340 * p / 100, x = sx; sx += w;
      return `<rect class="m-box${l === 'A' ? ' is-accent' : ''}" x="${x.toFixed(1)}" y="140" width="${(w - 2).toFixed(1)}" height="22" rx="4"/>
        <text x="${(x + w / 2 - 1).toFixed(1)}" y="154" text-anchor="middle">${p}%</text>`;
    }).join('');
    const dots = items.map((it, i) => `<circle class="${isDone(it) ? 'm-you-dot' : 'm-box'}" cx="${26 + i * 22}" cy="238" r="5"/>`).join('');
    return `<svg class="motif" viewBox="0 0 380 260">
      ${stars.map(([l, name], i) => `<rect class="m-box${l === 'R' ? ' is-accent' : ''}" x="${8 + i * 96}" y="22" width="76" height="60" rx="10"/>
        <text x="${46 + i * 96}" y="52" text-anchor="middle" style="font-size:20px">${l}</text>
        <text x="${46 + i * 96}" y="70" text-anchor="middle">${name}</text>
        ${i < 3 ? `<path class="m-wire" d="M${84 + i * 96} 52h20"/><path class="m-flow" style="animation-delay:${-i * .5}s" d="M${84 + i * 96} 52h20"/>` : ''}`).join('')}
      <text x="20" y="128">where a two-minute answer goes</text>${seg}
      <text x="20" y="188">“I”, not “we”  ·  a number in the result</text>
      ${dots}
    </svg>`;
  }
  if (kind === 'stdlib') {
    // A shelf of packages; each tile lights once that package is finished.
    const names = mod === 'gostdlib'
      ? ['os', 'fmt', 'io', 'bufio', 'strings', 'strconv', 'bytes', 'filepath', 'json', 'csv', 'time', 'sort', 'errors', 'regexp', 'slices']
      : ['os', 'sys', 'pathlib', 'io', 'json', 'csv', 're', 'collections', 'itertools', 'functools', 'datetime', 'subprocess', 'logging', 'argparse', 'contextlib'];
    return `<svg class="motif" viewBox="0 0 380 260">
      <rect class="m-box" x="12" y="12" width="${mod === 'gostdlib' ? 78 : 62}" height="24" rx="6"/>
      <text x="22" y="28">${mod === 'gostdlib' ? 'import ( )' : 'import'}</text>
      ${names.map((n, i) => {
        const x = 12 + (i % 5) * 72, y = 56 + Math.floor(i / 5) * 58;
        return `<rect class="m-box${isDone(items[i]) ? ' is-accent' : ''}" x="${x}" y="${y}" width="68" height="46" rx="8"/>
          <text x="${x + 34}" y="${y + 27}" text-anchor="middle">${n}</text>`;
      }).join('')}
      ${bar(12, 234, 356)}
    </svg>`;
  }
  // engineering: a worker pool — a queue feeding three lanes into a done bin
  const lang = mod === 'go' ? 'go test ./...' : 'pytest -v';
  const lanes = [74, 130, 186];
  return `<svg class="motif" viewBox="0 0 380 260">
    <rect class="m-box" x="14" y="14" width="${lang.length * 7 + 22}" height="24" rx="6"/><text x="25" y="30">${lang}</text>
    <rect class="m-box" x="18" y="62" width="58" height="136" rx="10"/>
    ${[0, 1, 2, 3].map(k => `<rect class="m-job static" x="30" y="${76 + k * 28}" width="34" height="16" rx="4"/>`).join('')}
    ${lanes.map((y, i) => `<path class="m-wire" d="M88 ${y}H300"/><text x="98" y="${y - 10}">worker ${i + 1}</text>
      ${[0, 1].map(k => `<rect class="m-job" x="92" y="${y - 8}" width="30" height="16" rx="4" style="animation-delay:${-(i * 1.7 + k * 2.9)}s"/>`).join('')}`).join('')}
    <rect class="m-box is-accent" x="306" y="62" width="58" height="136" rx="10"/>
    ${[0, 1, 2].map(k => `<path class="m-tick" d="M326 ${98 + k * 34}l6 6 12-13"/>`).join('')}
  </svg>`;
}

function liveMotif(host, mod, items, pct) {
  const wrap = $('.mod-motif', host);
  if (!wrap) return;
  wrap.classList.add('is-live');
  if (MODULES[mod].motif !== 'roadmap') return;
  const path = $('.m-road-base', wrap);
  const len = path.getTotalLength();
  const groups = grouped(mod, items).filter(g => g.name.startsWith('Phase'));
  $$('.m-stone', wrap).forEach((c, k) => {
    const pt = path.getPointAtLength(len * (k + 1) / 7);
    c.setAttribute('cx', pt.x); c.setAttribute('cy', pt.y);
    const g = groups[k];
    if (g && g.items.every(it => progressOf(mod, it).state === 'done')) c.classList.add('is-done');
  });
  const you = path.getPointAtLength(len * pct / 100);
  $('.m-you', wrap).style.transform = `translate(${you.x}px, ${you.y}px)`;
}

/* ------------------------------------------------------------- router -- */
async function routeModule(parts) {
  let mod = null, id = '';
  if (parts[0] === 'eng' && parts.length === 2 && DATA.engTopics[parts[1]] && MODULES[parts[1]]) {
    mod = parts[1];
  } else {
    // accept both the published hash ("#/system-design") and the module's
    // own short key ("#/sd") — a reasonable guess shouldn't land on a
    // silent wrong page just because it wasn't the exact published slug
    mod = Object.keys(MODULES).find(k => !MODULES[k].eng && (MODULES[k].hash === parts[0] || k === parts[0])) || null;
    id = parts.slice(1).join('/');
  }
  if (!mod) return false;
  if (isDsaGuide(mod) && !id) { location.replace('#/dsa'); return true; }   // guides are listed on the DSA pages
  await leaveWorkspace();
  curModule = mod;
  if (id) {
    curDoc = { mod, id, key: docKey(mod, id) };
    showView('doc-reader');
    renderReader(mod, id);
  } else {
    showView('module-home');
    renderModuleHome(mod);
  }
  renderSidebar();
  return true;
}

/* ============================================================== reader == */
const PREF_DEFAULT = { paper: 'app', size: 2, width: 'comfort', face: 'sans' };
function readerPrefs() {
  try { return { ...PREF_DEFAULT, ...JSON.parse(localStorage.getItem('reader-prefs') || '{}') }; }
  catch (e) { return { ...PREF_DEFAULT }; }
}
function saveReaderPrefs(p) {
  try { localStorage.setItem('reader-prefs', JSON.stringify(p)); } catch (e) { /* private mode */ }
}

function prefsPanel(p) {
  const seg = (key, opts) => `<div class="seg">${opts.map(([v, l, style = '']) =>
    `<button data-pref="${key}" data-v="${v}" class="${String(p[key]) === String(v) ? 'is-on' : ''}"${style ? ` style="${style}"` : ''}>${l}</button>`).join('')}</div>`;
  return `
    <div class="pop-row"><span class="pop-label">Page</span>
      <div class="swatches">${[['app', 'App'], ['sepia', 'Sepia'], ['night', 'Night']].map(([v, l]) =>
        `<button class="swatch sw-${v}${p.paper === v ? ' is-on' : ''}" data-pref="paper" data-v="${v}"><i></i>${l}</button>`).join('')}</div></div>
    <div class="pop-row"><span class="pop-label">Text size</span>
      ${seg('size', [1, 2, 3, 4].map(v => [v, 'A', `font-size:${9 + v * 2.5}px`]))}</div>
    <div class="pop-row"><span class="pop-label">Line length</span>
      ${seg('width', [['narrow', 'Narrow'], ['comfort', 'Medium'], ['wide', 'Wide']])}</div>
    <div class="pop-row"><span class="pop-label">Typeface</span>
      ${seg('face', [['sans', 'Sans', 'font-family:var(--sans)'], ['serif', 'Serif', 'font-family:var(--serif)']])}</div>
    <div class="pop-keys">
      <span><kbd>J</kbd><kbd>K</kbd> next or previous section</span>
      <span><kbd>C</kbd> check the current section</span>
      <span><kbd>[</kbd><kbd>]</kbd> previous or next page</span>
      <span><kbd>F</kbd> focus mode</span>
    </div>`;
}

const splitWords = t => esc(t).split(/\s+/).map((w, i) => `<span class="w" style="--i:${i}">${w}</span>`).join(' ');

/* Python | Go switch on a topic guide — jumps to the same topic in the other language. */
function guideLangSwitch(mod, it) {
  const t = (DATA.topics || []).find(x => x.id === it.id);
  if (!t) return '';
  const langs = [['py', 'Python', 'dsaguide'], ['go', 'Golang', 'dsaguidego']];
  return `<div class="guide-lang" role="group" aria-label="Guide language">
    <span class="guide-lang-label">Guide language</span>
    ${langs.map(([k, label, m]) => m === mod
      ? `<span class="guide-lang-btn is-on" data-lang="${k}" aria-current="page">${label}</span>`
      : t.guides[k] ? `<a class="guide-lang-btn" data-lang="${k}" href="#/${MODULES[m].hash}/${it.id}">${label}</a>`
      : `<span class="guide-lang-btn is-off" data-lang="${k}" title="No ${label} guide for this topic">${label}</span>`).join('')}
  </div>`;
}

async function renderReader(mod, id) {
  const m = MODULES[mod], host = $('#viewDocReader');
  const key = docKey(mod, id);
  host.innerHTML = '<div class="mod-loading">Opening…</div>';
  host.onscroll = null;

  let items, doc;
  try {
    items = await modItems(mod);
    doc = docCache.get(`doc:${key}`);
    if (!doc) {
      doc = await api(`${m.doc}${m.doc.includes('?') ? '&' : '?'}id=${encodeURIComponent(id)}`);
      docCache.set(`doc:${key}`, doc);
    }
  } catch (e) {
    host.innerHTML = emptyMsg('This page could not be opened', 'The server did not return it. Check it is still running, then reload.');
    return;
  }
  if (!curDoc || curDoc.key !== key) return;       // navigated away while loading

  const idx = items.findIndex(it => it.id === id);
  const it = items[idx];
  if (!doc.exists || !it) {
    host.innerHTML = `<div class="mod-page">${emptyMsg('Page not found',
      `It is no longer in ${m.name} on disk. Pick another page from the side navigation.`)}</div>`;
    return;
  }
  curDoc.item = it;
  const r = docRec(key);
  docSave(key, { last: Date.now() });
  renderModNav();

  const back = m.back ? m.back(it) : { href: `#/${m.hash}`, label: m.name };
  const prefs = readerPrefs();
  // solution-gate.js: a practice problem's reference design is hidden on every visit
  // until "Reveal solution" is pressed, and hides again once you navigate away.
  const hasSolution = it.kind === 'problem' && !!doc.solution;
  const revealKey = `sd:${key}`;
  const shown = hasSolution && (typeof revealIsOpen === 'undefined' ? !!r.revealed : revealIsOpen(revealKey));
  const gated = hasSolution && !shown;
  const labCount = typeof SD_LABS !== 'undefined' ? (SD_LABS[it.id] || []).length : 0;
  const solSections = hasSolution ? (doc.solution.match(/^##\s/gm) || []).length : 0;

  host.innerHTML = `
    <div class="reader" data-mod="${mod}" data-paper="${prefs.paper}" data-size="${prefs.size}" data-width="${prefs.width}" data-face="${prefs.face}">
      <div class="reader-bar">
        <a class="reader-back" href="${back.href}"><svg viewBox="0 0 24 24"><path d="M15 6l-6 6 6 6"/></svg><span>${esc(back.label)}</span></a>
        <span class="reader-crumb">${esc(m.group(it))}</span>
        <div class="reader-tools">
          <button class="icon-btn" data-act="focus" title="Focus mode (F)" aria-label="Focus mode" aria-pressed="${$('#app').classList.contains('reading-focus')}">
            <svg viewBox="0 0 24 24"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>
          </button>
          <button class="reader-aa" data-act="prefs" aria-expanded="false" aria-haspopup="true" title="Page settings">Aa</button>
        </div>
        <div class="reader-pop" hidden>${prefsPanel(prefs)}</div>
        <div class="reader-progress"><i></i></div>
      </div>
      <div class="reader-grid">
        <article class="doc">
          <header class="doc-hero">
            <p class="doc-kicker">${esc(m.kicker(it))}</p>
            <h1 class="doc-title">${splitWords(modTitle(m, it))}</h1>
            <div class="doc-meta">
              <span>${it.kind === 'problem' ? '45 min design exercise' : `${it.minutes || 1} min read`}</span>
              <span data-meta="sections"></span>
              <span class="doc-state" data-meta="state"></span>
            </div>
            ${isDsaGuide(mod) ? `
            <div class="doc-guide-actions">
              <a class="doc-practice-cta" href="#/t/${it.id}">
                <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4l12 8-12 8z"/></svg>
                Practice: solve this pattern's problems
              </a>
              ${guideLangSwitch(mod, it)}
            </div>` : ''}
            ${mod === 'api' && it.id.endsWith('/Theory') ? `
            <a class="doc-practice-cta" href="#/api-type/${encodeURIComponent(it.id.split('/')[0])}">
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4l12 8-12 8z"/></svg>
              Practice: Foundation levels &amp; labs — run real code for this
            </a>` : ''}
          </header>
          <div class="prose doc-prose" id="docProse"></div>
          ${gated && typeof revealGateHTML === 'function' ? revealGateHTML({
            kicker: 'Reference design · hidden',
            title: 'Design it yourself first',
            copy: 'Run the 45-minute round above, or at least sketch your answer: requirements, estimates, API, data model, a baseline diagram, and what fails. Then compare your decisions with the reference.',
            checks: ['I wrote requirements and scale numbers', 'I drew a baseline and walked a read and a write', 'I picked the two hardest parts and chose an approach', 'I listed failure modes and how I would notice them'],
            inside: [['sections', String(solSections || '—')], ...(labCount ? [['animated diagrams', String(labCount)]] : [])],
            button: 'Reveal solution',
            note: 'Hidden again as soon as you leave this problem.',
          }) : gated ? `<div class="gate">
            <svg class="gate-icon" viewBox="0 0 24 24"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/></svg>
            <div class="gate-copy">
              <h3>Design it yourself first</h3>
              <p>State your assumptions, estimate the load, sketch a baseline, then ask what fails. Open the reference design once you have your own to compare against.</p>
            </div>
            <button class="btn-mod" data-act="reveal">Show reference design</button>
          </div>` : ''}
          <footer class="doc-end" id="docEnd"></footer>
        </article>
        <aside class="doc-rail" aria-label="On this page">
          <div class="rail-progress" id="railProgress"></div>
          <nav class="rail-toc" id="railToc"></nav>
          <div class="rail-hl" id="railHl"></div>
        </aside>
      </div>
      <div class="lightbox" id="lightbox" hidden></div>
    </div>`;

  let md = doc.markdown;
  if (shown) {
    md += `\n\n<div class="sol-divider"><span>Reference design</span></div>\n\n${doc.solution.replace(/^#\s/m, '## ')}`;
  }
  const prose = $('#docProse', host);
  // cross-references resolve against every module's page list, so have them all
  await Promise.allSettled(Object.keys(MODULES).filter(k => MODULES[k].list).map(k => modItems(k)));
  if (!curDoc || curDoc.key !== key) return;
  prose.innerHTML = renderMarkdown(md);
  const h1 = prose.firstElementChild;
  if (h1 && h1.tagName === 'H1') h1.remove();
  $$(':scope > h1', prose).forEach(h => { const h2 = document.createElement('h2'); h2.append(...h.childNodes); h.replaceWith(h2); });

  const secs = sectionize(prose);
  decorateHeadings(prose, true);
  if (shown) {
    // The divider stays where it is (sd.js finds the solution by it) but the visible
    // marker is a banner between the question and the answer, with "Hide solution".
    const divider = $('.sol-divider', prose);
    const at = divider ? secs.indexOf(divider.closest('.sec')) : -1;
    if (divider && at >= 0) {
      divider.classList.add('has-banner');
      secs.slice(at + 1).forEach(s => s.classList.add('is-solution'));
      if (typeof revealBannerHTML === 'function') {
        (secs[at + 1] || divider).insertAdjacentHTML('beforebegin', revealBannerHTML({
          title: 'Reference design',
          sub: 'One strong answer, not the only one. Compare your decisions and trade-offs, not your wording.',
          just: !!(curDoc && curDoc.justRevealed),
        }));
      }
    }
  }
  enhanceCallouts(prose);
  wrapTables(prose);
  rewriteLinks(prose, mod, id);
  mountDocLabs(prose);
  // roadmap.js: hour track, labs, challenge checklist, mock interview, glossary
  // sd.js: animated system labs and the L5 interview coach
  const extras = mod === 'roadmap' && typeof enhanceRoadmapDay === 'function' ? enhanceRoadmapDay(host, prose, it, key)
    : mod === 'sd' && typeof enhanceSystemDesign === 'function' ? enhanceSystemDesign(host, prose, it, key) : null;
  $('[data-meta="sections"]', host).textContent = secs.length ? `${secs.length} sections` : '';

  buildRailToc(host, secs);
  paintReaderProgress();
  paintDocEnd(mod, items, idx);
  wireReader(host, mod, items, idx);

  await renderMath(prose);
  await Promise.all([renderCode(prose), renderMermaidBlocks(prose)]);
  if (!curDoc || curDoc.key !== key) return;
  if (extras) await extras.afterRender();
  if (!curDoc || curDoc.key !== key) return;
  applyHighlights(prose, r);
  paintRailHighlights();
  observeReveals(host);
  wireReaderScroll(host, key);

  if (r.pos && !r.done && r.pos > 0.02 && !curDoc.skipRestore) {
    host.scrollTop = r.pos * host.scrollHeight;
    toast('Picked up where you left off.');
  }
}

/* Wrap each h2 and everything up to the next h2 in a <section>, so a
   section can be checked off, tracked by the TOC, and jumped to. */
function sectionize(root) {
  const frag = document.createDocumentFragment();
  const seen = new Map(), secs = [];
  let sec = null;
  for (const node of [...root.childNodes]) {
    if (node.nodeType === 1 && node.tagName === 'H2') {
      sec = document.createElement('section');
      sec.className = 'sec';
      const base = slug(node.textContent) || 'section';
      const n = (seen.get(base) || 0) + 1;
      seen.set(base, n);
      sec.dataset.sid = n === 1 ? base : `${base}-${n}`;
      node.id = `s-${sec.dataset.sid}`;
      secs.push(sec);
      frag.append(sec);
    } else if (!sec) {
      sec = document.createElement('section');
      sec.className = 'sec sec-intro';
      frag.append(sec);
    }
    sec.append(node);
  }
  // A trailing `---` duplicates the gap the next section already opens with.
  frag.querySelectorAll('.sec').forEach(s => { if (s.lastElementChild?.tagName === 'HR') s.lastElementChild.remove(); });
  root.replaceChildren(frag);
  $$('h3', root).forEach((h, i) => { h.id = `h-${i}-${slug(h.textContent)}`; });
  return secs;
}

const EMOJI_RE = /^(\p{Extended_Pictographic}️?)\s*/u;
const ACRONYMS = new Set(('AI ML LLM LLMS RAG API APIS GPU CPU TPU NLP RL RLHF DPO PPO MCP SQL CRF RNN CNN LSTM GRU BERT GPT KV SFT ' +
  'VAE GAN MLE MAP PCA SVD SVM KNN NER JSON HTTP HTTPS GIL IO OS UI CI CD DAG TTL CDN DB DNS TCP UDP TLS ID URL REST GRPC ' +
  'MAANG FAANG SLO SLA QPS P99 LB MOE ROPE GQA LORA QLORA RAM SSD AWS GCP K8S EDA OOP SOLID DRY YAGNI CAP ACID BASE').split(' '));

function tidyHeading(text) {
  const letters = text.replace(/[^A-Za-z]/g, '');
  if (letters.length < 4 || letters !== letters.toUpperCase()) return text;
  const lower = text.toLowerCase().replace(/[a-z][a-z0-9]*/g, w => ACRONYMS.has(w.toUpperCase()) ? w.toUpperCase() : w);
  return lower.replace(/(^[^a-zA-Z]*|[:.!?]\s+)([a-z])/g, (_, a, b) => a + b.toUpperCase());
}

function decorateHeadings(root, withChecks) {
  $$('h2, h3', root).forEach(h => {
    const first = h.firstChild;
    if (first && first.nodeType === 3) {
      const em = h.tagName === 'H2' && first.textContent.match(EMOJI_RE);
      if (em) first.textContent = first.textContent.slice(em[0].length);
      if (h.childNodes.length === 1) first.textContent = tidyHeading(first.textContent);
      const hour = h.tagName === 'H2' && first.textContent.match(/^(hour|step|part|phase)\s*(\d+)\s*[:.\-—–]\s*/i);
      if (hour) {
        first.textContent = first.textContent.slice(hour[0].length);
        h.insertAdjacentHTML('afterbegin', `<span class="h-step">${hour[1][0].toUpperCase()}${hour[1].slice(1).toLowerCase()} ${hour[2]}</span>`);
      } else if (em) {
        h.insertAdjacentHTML('afterbegin', `<span class="h-emoji" aria-hidden="true">${em[1]}</span>`);
      }
    }
    h.dataset.label = [...h.childNodes].filter(n => !(n.nodeType === 1 && n.classList.contains('h-emoji')))
      .map(n => n.textContent).join(' ').replace(/\s+/g, ' ').trim();
    if (withChecks && h.tagName === 'H2') {
      // The check sits where you finish the section, not where you start it.
      const sec = h.closest('.sec');
      sec.insertAdjacentHTML('beforeend', `<div class="sec-foot">
        <button class="sec-check" data-sid="${sec.dataset.sid}" aria-pressed="false" title="Mark this section as understood (C)">
          <svg viewBox="0 0 24 24">${CHECK_PATH}</svg><span>Got it</span></button></div>`);
    }
  });
}

/* ----------------------------------------------------------- callouts -- *
   Two ways a blockquote becomes a coloured card: a leading emoji
   (💡 ✅ ⚠️ 🎯 📖 🧠 …) or a leading bold label (**Analogy:**,
   **Mathematical Example:**, **Real-World Intuition:** …) — the roadmap
   lessons use the second style throughout. */
const CALLOUT_META = {
  key: ['💡', 'Key idea'], tip: ['✅', 'Do this'], warn: ['⚠️', 'Watch out'], interview: ['🎯', 'Interview angle'],
  definition: ['📖', 'Definition'], intuition: ['🧠', 'Intuition'], analogy: ['🧩', 'Analogy'],
  example: ['🔢', 'Worked example'], practice: ['🏭', 'In practice'], question: ['❓', 'Check yourself'],
};
const EMOJI_CALLOUT = {
  '💡': 'key', '🔑': 'key', '📌': 'key', '✅': 'tip', '⚠️': 'warn', '⚠': 'warn', '❗': 'warn', '🚫': 'warn',
  '🎯': 'interview', '📖': 'definition', '🧠': 'intuition', '🧩': 'analogy', '🧪': 'example', '🔢': 'example',
  '🏭': 'practice', '🚀': 'practice', '❓': 'question',
};
const LABEL_CALLOUT = [
  [/analog/i, 'analogy'],
  [/interview/i, 'interview'],
  [/warn|pitfall|gotcha|caution|trap|mistake|danger|watch out|anti-?pattern/i, 'warn'],
  [/example|worked|walk-?through|concrete|scenario|case study|trace/i, 'example'],
  [/intuition|mental model|picture|think of|in plain/i, 'intuition'],
  [/real[- ]world|context|in practice|production|enterprise|industry|application/i, 'practice'],
  [/tip|best practice|rule of thumb|do this|recommend/i, 'tip'],
  [/defin|formal|terminology|notation/i, 'definition'],
  [/question|quiz|check yourself|exercise|try it|challenge/i, 'question'],
  [/note|remember|important|key|takeaway|summary|tl;?dr|insight|why it matters|scope/i, 'key'],
];

/* Lab placeholders authored straight into a markdown file:
     <div class="lab" data-viz="lsm-tree"></div>
   viz.js knows two lab shapes. The object spec is the one createLab() builds
   chrome for. The function spec (viz-csfund.js) fills its host itself and
   returns a per-frame draw(dt) — it needs a loop, and because it reads the
   palette once at build time it is rebuilt when the theme flips. */
function mountDocLabs(root) {
  if (typeof LABS === 'undefined') return;
  $$('[data-viz]', root).forEach(ph => {
    const name = ph.dataset.viz;
    const spec = LABS.get(name);
    if (!spec) { ph.remove(); return; }

    if (typeof spec !== 'function') {
      const fig = createLab(name);
      fig ? ph.replaceWith(fig) : ph.remove();
      return;
    }

    ph.classList.add('lab', 'lab-embed');
    let draw = null, raf = 0, last = 0, visible = true;
    const build = () => {
      try {
        draw = spec(ph);
      } catch (e) {
        console.error(`lab ${name}`, e);
        ph.innerHTML = `<p class="lab-error">This lab could not start: ${esc(String(e.message || e))}</p>`;
        return false;
      }
      return typeof draw === 'function';
    };
    const tick = now => {
      raf = 0;
      if (!ph.isConnected) return;
      const dt = Math.min(.05, (now - (last || now)) / 1000);
      last = now;
      if (visible) {
        try { draw(dt); } catch (e) { console.error(`lab ${name}`, e); return; }
      }
      raf = requestAnimationFrame(tick);
    };
    if (!build()) return;
    raf = requestAnimationFrame(tick);
    /* a lab scrolled out of view keeps its state but stops burning frames */
    new IntersectionObserver(es => { visible = es[0].isIntersecting; last = 0; }).observe(ph);
    liveLabs.add({ fig: ph, redraw: () => { if (ph.isConnected) build(); } });
  });
}

function enhanceCallouts(root) {
  $$('blockquote', root).forEach(bq => {
    const p = bq.firstElementChild;
    if (!p) return;
    let type = null, label = null;
    const lead = p.textContent.trimStart();
    const emoji = Object.keys(EMOJI_CALLOUT).find(e => lead.startsWith(e));
    if (emoji) {
      type = EMOJI_CALLOUT[emoji];
      const walker = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
      for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        if (!n.textContent.trim()) continue;
        n.textContent = n.textContent.replace(emoji, '').replace(/^[\s️]+/, '');
        break;
      }
    } else if (p.tagName === 'P') {
      const strong = [...p.childNodes].find(n => !(n.nodeType === 3 && !n.textContent.trim()));
      if (strong && strong.nodeType === 1 && strong.tagName === 'STRONG') {
        const raw = strong.textContent.trim();
        const after = strong.nextSibling;
        const colon = /:$/.test(raw) || (after && after.nodeType === 3 && /^\s*:/.test(after.textContent));
        const hit = raw.length <= 48 && colon && LABEL_CALLOUT.find(([re]) => re.test(raw));
        if (hit) {
          type = hit[1];
          label = raw.replace(/:$/, '').trim();
          strong.remove();
          if (after && after.nodeType === 3) after.textContent = after.textContent.replace(/^\s*:?\s*/, '');
          if (p.firstChild && p.firstChild.nodeName === 'BR') p.firstChild.remove();
        }
      }
    }
    if (!type) { bq.classList.add('quote'); return; }
    const [icon, defLabel] = CALLOUT_META[type];
    const card = document.createElement('aside');
    card.className = `callout callout-${type}`;
    card.innerHTML = `<span class="callout-icon" aria-hidden="true">${icon}</span><div class="callout-body"><span class="callout-label">${esc(label || defLabel)}</span></div>`;
    $('.callout-body', card).append(...bq.childNodes);
    bq.replaceWith(card);
  });
}

function wrapTables(root) {
  $$('table', root).forEach(t => {
    if (t.parentElement.classList.contains('table-wrap')) return;
    const w = document.createElement('div');
    w.className = 'table-wrap';
    t.replaceWith(w);
    w.append(t);
  });
}

/* ---- repo paths → app pages -------------------------------------------- *
   Guides cite each other by source path (`SystemDesign/building_blocks/06_x.md`,
   `PyDSA/08_linked_list/014_x_solution.py`, `../best_practices/01_x.md`). Readers
   never see that tree, so every such reference becomes a link to the page the app
   has for it, labelled with the page's title — or plain words when there is none. */
const REPO_ROOTS = ['SystemDesign', 'SoftwareDesign', 'CSFundamentals', 'GoogleBehavioral', 'AI-Libraries-Guides',
  'Agentic-AI', 'AI-road-map', 'API', 'SQL', 'NoSQL', 'PyStdLib', 'GoStdLib', 'PyDSA', 'GoDSA', 'PyEngineering', 'GoEngineering'];
const REPO_ROOT_RE = new RegExp(`^(?:${REPO_ROOTS.join('|')})/`);
const REPO_HOME = { sd: 'SystemDesign', swd: 'SoftwareDesign', csfund: 'CSFundamentals', behavioral: 'GoogleBehavioral',
  library: 'AI-Libraries-Guides', agentic: 'Agentic-AI', roadmap: 'AI-road-map', api: 'API', sql: 'SQL', nosql: 'NoSQL' };

function docSourcePath(mod, id) {
  if (isDsaGuide(mod)) return `${DSA_GUIDE_ROOT[mod]}/${id}/_TOPIC_GUIDE.md`;
  const home = REPO_HOME[mod];
  if (!home) return null;
  if (mod === 'sd') {
    if (id === 'readme') return `${home}/README.md`;
    const pr = id.match(/^problem\/(.+)$/);
    return pr ? `${home}/problems/${pr[1]}_question.md` : `${home}/${id}.md`;
  }
  return `${home}/${id}.md`;
}

const prettyName = s => s.replace(/\.[a-z]+$/i, '').replace(/^\d+_/, '').replace(/_(solution|question|deep_dive)$/, '')
  .replace(/[_-]+/g, ' ').replace(/^\w/, c => c.toUpperCase());

function repoRoute(path) {
  let r;
  const item = (mod, id) => {
    const it = (modItemsSync(mod) || []).find(x => x.id === id);
    return it ? { href: itemHref(mod, it), title: modTitle(MODULES[mod], it) } : null;
  };
  if ((r = path.match(/^SystemDesign\/README\.md$/))) return item('sd', 'readme');
  if ((r = path.match(/^SystemDesign\/(building_blocks|best_practices)\/([\w-]+)\.md$/))) return item('sd', `${r[1]}/${r[2]}`);
  if ((r = path.match(/^SystemDesign\/(?:problems|solutions)\/([\w-]+?)_(?:question|solution)\.md$/))) return item('sd', `problem/${r[1]}`);
  if ((r = path.match(/^SystemDesign\/SYSTEM_DESIGN_GUIDE\.md$/))) return item('sd', 'guide');
  if ((r = path.match(/^SystemDesign\/(\d{2}_[\w-]+)\.md$/))) return item('sd', r[1]);
  if ((r = path.match(/^SoftwareDesign\/lld\/([\w-]+?)_(?:solution|question)\.(?:py|md)$/))) {
    const t = ((DATA.engTopics || {}).lld || []).find(x => x.id === r[1]);
    return t ? { href: `#/eng/lld/${t.id}`, title: t.title || prettyName(t.id) } : null;
  }
  if ((r = path.match(/^SoftwareDesign\/([\w-]+)\.md$/))) return item('swd', r[1]);
  if ((r = path.match(/^CSFundamentals\/([\w-]+)\.md$/))) return item('csfund', r[1]);
  if ((r = path.match(/^GoogleBehavioral\/([\w-]+)\.md$/))) return item('behavioral', r[1]);
  if ((r = path.match(/^AI-Libraries-Guides\/([\w-]+)\.md$/))) return item('library', r[1]);
  if ((r = path.match(/^Agentic-AI\/([\w-]+)\.md$/))) return item('agentic', r[1]);
  if ((r = path.match(/^AI-road-map\/(?:[\w-]+\/)*([\w-]+)\.md$/))) return item('roadmap', r[1]);
  if ((r = path.match(/^API\/(\w+)\/(?:Foundation|labs)\/(?:python|golang)\/([\w-]+)\.(?:py|go)$/)))
    return { href: `#/api-item/${r[1]}/${/\/labs\//.test(path) ? 'labs' : 'Foundation'}/${r[2]}`, title: prettyName(r[2]) };
  if ((r = path.match(/^API\/(\w+)\/([\w-]+)\.md$/))) return item('api', `${r[1]}/${r[2]}`);
  if ((r = path.match(/^SQL\/([\w-]+)\.md$/))) return item('sql', r[1]);
  if ((r = path.match(/^NoSQL\/(README|(?:mongodb|redis|concepts)\/[\w-]+)\.md$/))) return item('nosql', r[1]);
  if ((r = path.match(/^(Py|Go)StdLib\/(\d+_\w+)\/GUIDE\.md$/)))
    return { href: `#/stdlib-pkg/${r[1].toLowerCase() === 'py' ? 'py' : 'go'}/${r[2]}`, title: prettyName(r[2]) };
  if ((r = path.match(/^(Py|Go)StdLib\/(\d+_\w+)\/(level_[\w]+)\.(?:py|go)$/)))
    return { href: `#/stdlib-item/${r[1] === 'Py' ? 'py' : 'go'}/${r[2]}/${r[3]}`, title: prettyName(r[3].replace(/^level_\d+_?/, '')) };
  if ((r = path.match(/^(Py|Go)DSA\/(\d{2}_\w+)\/_TOPIC_GUIDE\.md$/))) {
    const t = (DATA.topics || []).find(x => x.id === r[2]), go = r[1] === 'Go';
    return t && t.guides[go ? 'go' : 'py']
      ? { href: `#/dsa-guide${go ? '-go' : ''}/${t.id}`, title: `${t.title} — ${go ? 'Go' : 'Python'} topic guide` } : null;
  }
  if ((r = path.match(/^(?:Py|Go)DSA\/(\d{2}_\w+)\/(\d{3})_[\w]+?(?:_(?:question|solution))?(?:\.(?:py|go)|\/(?:question|solution)\.go)$/))) {
    const p = DATA.problems.find(x => x.topic === r[1] && x.seq === r[2]);
    return p ? { href: `#/p/${p.topic}/${p.seq}`, title: p.title } : null;
  }
  if ((r = path.match(/^(Py|Go)Engineering\/(\d{2}_[\w]+)\//))) {
    const lang = r[1] === 'Py' ? 'py' : 'go';
    const t = ((DATA.engTopics || {})[lang] || []).find(x => x.id === r[2]);
    return t ? { href: `#/eng/${lang}/${t.id}`, title: t.title || prettyName(t.id) } : null;
  }
  return null;
}

/* a reference may be written relative to the current doc, or to its module's folder */
function repoRefRoute(ref, mod, id) {
  let p = ref.replace(/[#?].*$/, '').replace(/^\.\//, '');
  if (REPO_ROOT_RE.test(p)) return repoRoute(p);
  const src = docSourcePath(mod, id);
  const home = REPO_HOME[mod] || DSA_GUIDE_ROOT[mod] || null;
  if (!src) return null;
  const tries = [src.split('/').slice(0, -1), home ? [home] : []];
  for (const segs of tries) {
    const out = [...segs];
    for (const s of p.split('/')) { if (s === '..') out.pop(); else if (s && s !== '.') out.push(s); }
    const hit = REPO_ROOT_RE.test(out.join('/')) ? repoRoute(out.join('/')) : null;
    if (hit) return hit;
  }
  return null;
}

const looksLikePath = t => !/\s/.test(t) && (/\//.test(t) || /\.(md|py|go|sh|ya?ml|txt)$/i.test(t));
const isSourceRef = t => /\.(md|py|go|sh|ya?ml|txt)$/i.test(t) && (/\//.test(t) || REPO_ROOT_RE.test(t));

function rewriteLinks(root, mod, id) {
  const items = modItemsSync(mod) || [];
  const base = mod !== 'sd' ? [] : id.startsWith('problem/') ? ['problems'] : id.includes('/') ? [id.split('/')[0]] : [];
  $$('a[href]', root).forEach(a => {
    let href = a.getAttribute('href');
    // an absolute file:///…/AI-road-map/x.md link is a repo path in disguise
    const fileUrl = href.match(new RegExp(`^file://.*?/((?:${REPO_ROOTS.join('|')})/.*)$`));
    if (fileUrl) { href = decodeURIComponent(fileUrl[1]); a.setAttribute('href', href); }
    if (/^[a-z]+:/i.test(href)) { a.target = '_blank'; a.rel = 'noopener'; return; }
    if (href.startsWith('#')) { a.dataset.anchor = slug(decodeURIComponent(href.slice(1))); a.removeAttribute('href'); a.tabIndex = 0; return; }
    const path = href.replace(/[#?].*$/, '');
    if (href.startsWith('/')) return;
    const text = a.textContent.trim();
    const hit = repoRefRoute(path, mod, id);
    if (hit) {
      a.setAttribute('href', hit.href);
      if (looksLikePath(text)) a.textContent = hit.title;
      return;
    }
    // legacy: a .md that only matches by file name inside this module
    if (/\.md$/i.test(path)) {
      const segs = [...base];
      for (const s of path.split('/')) { if (s === '..') segs.pop(); else if (s && s !== '.') segs.push(s); }
      let target = segs.join('/').replace(/\.md$/i, '');
      if (mod === 'sd') {
        target = target.replace(/^README$/, 'readme').replace(/(^|\/)SYSTEM_DESIGN_GUIDE$/, 'guide')
          .replace(/^problems\/(.+)_question$/, 'problem/$1').replace(/^solutions\/(.+)_solution$/, 'problem/$1');
      } else {
        target = target.split('/').pop();
      }
      if (items.some(x => x.id === target)) { a.setAttribute('href', `#/${MODULES[mod].hash}/${target}`); return; }
    }
    // no page in the app for it: keep the words, drop the file path and the dead href
    a.removeAttribute('href');
    a.classList.add('dead-link');
    a.title = 'Not part of the app';
    if (looksLikePath(text)) a.textContent = prettyName(text.split('/').pop());
  });

  // `SystemDesign/building_blocks/06_x.md` written as inline code → a titled link
  $$('code', root).forEach(c => {
    if (c.closest('pre, a')) return;
    const t = c.textContent.trim();
    if (!isSourceRef(t)) return;
    const hit = repoRefRoute(t, mod, id);
    if (!hit) {
      // a repo doc/source file with no page in the app: say what it is, not where it lives
      if (REPO_ROOT_RE.test(t) && /\.(md|py|go)$/i.test(t) && !t.includes('*')) {
        const span = document.createElement('span');
        span.className = 'ref-link is-plain';
        span.textContent = prettyName(t.split('/').pop());
        c.replaceWith(span);
      }
      return;
    }
    const a = document.createElement('a');
    a.className = 'ref-link';
    a.href = hit.href;
    a.textContent = hit.title;
    c.replaceWith(a);
  });
}

/* --------------------------------------------------------------- code -- */
const LANG_NAMES = { py: 'Python', python: 'Python', go: 'Go', golang: 'Go', js: 'JavaScript', javascript: 'JavaScript',
  ts: 'TypeScript', typescript: 'TypeScript', bash: 'Shell', sh: 'Shell', shell: 'Shell', zsh: 'Shell', json: 'JSON',
  yaml: 'YAML', yml: 'YAML', sql: 'SQL', toml: 'TOML', dockerfile: 'Dockerfile', text: 'Text', plaintext: 'Text',
  proto: 'Protobuf', protobuf: 'Protobuf', http: 'HTTP', ini: 'INI', rust: 'Rust', cpp: 'C++', c: 'C', java: 'Java' };

let hljsLoad = null;
function ensureHljs() {
  if (window.hljs) return Promise.resolve(true);
  hljsLoad ??= new Promise(resolve => {
    const s = document.createElement('script');
    s.src = `${CDN}/highlight.js/11.9.0/highlight.min.js`;
    s.onload = () => { if (window.hljs) hljs.configure({ ignoreUnescapedHTML: true }); resolve(!!window.hljs); };
    s.onerror = () => { hljsLoad = null; resolve(false); };
    document.head.appendChild(s);
  });
  return hljsLoad;
}

function highlightCode(code, lang) {
  if (!window.hljs || !lang || !hljs.getLanguage(lang)) return;
  try { hljs.highlightElement(code); } catch (e) { /* leave it plain */ }
}

async function renderCode(root) {
  const blocks = $$('pre > code', root).filter(c => !c.classList.contains('language-mermaid') && !c.closest('.code'));
  if (!blocks.length) return;
  const langs = [];
  for (const code of blocks) {
    const pre = code.parentElement;
    const lang = ([...code.classList].find(c => c.startsWith('language-')) || '').slice(9).toLowerCase();
    const wrap = document.createElement('div');
    wrap.className = `code${!lang || lang === 'text' || lang === 'plaintext' ? ' is-plain' : ''}`;
    wrap.innerHTML = `<div class="code-head"><span class="code-lang">${esc(pre.dataset.filename || LANG_NAMES[lang] || lang || 'Text')}</span>
      <button type="button" class="code-copy">Copy</button></div>`;
    pre.replaceWith(wrap);
    wrap.append(pre);
    langs.push([code, lang]);
  }
  if (langs.some(([, l]) => l && l !== 'text' && l !== 'plaintext') && await ensureHljs()) {
    langs.forEach(([code, lang]) => highlightCode(code, lang));
  }
}

/* A whole source file (engineering Solution / Test tabs): line numbers in
   their own column so highlighting spans can never break the alignment. */
async function renderCodeFile(body, d, lang) {
  const lines = d.code.replace(/\n$/, '').split('\n');
  body.innerHTML = `<div class="code code-file">
    <div class="code-head"><span class="code-lang">${lang === 'go' ? 'Go' : 'Python'}</span>
      <span class="code-lines">${lines.length} lines</span><button type="button" class="code-copy">Copy</button></div>
    <div class="code-scroll"><div class="lnums" aria-hidden="true">${lines.map((_, i) => i + 1).join('\n')}</div>
      <pre><code class="language-${lang === 'go' ? 'go' : 'python'}">${esc(d.code)}</code></pre></div>
  </div>`;
  if (await ensureHljs()) highlightCode($('pre code', body), lang === 'go' ? 'go' : 'python');
}

/* ----------------------------------------------------------- diagrams -- */
function mermaidVars(el) {
  const cs = getComputedStyle(el);
  const v = (name, fb) => { const x = cs.getPropertyValue(name).trim(); return /^#[0-9a-f]{6}$/i.test(x) ? x : fb; };
  const dark = el.closest('.reader[data-paper="night"]') ||
    (!el.closest('.reader[data-paper="sepia"]') && document.documentElement.dataset.theme === 'dark');
  const bg = v('--surface', dark ? '#11151d' : '#ffffff'), box = v('--surface-2', dark ? '#171c26' : '#f1f4f8');
  const text = v('--text', dark ? '#e9edf5' : '#0f141c'), dim = v('--text-dim', dark ? '#9ba6b9' : '#4c5566');
  const line = v('--border-strong', dark ? '#36415a' : '#b5bfcf'), accent = v('--accent', dark ? '#e5ab4f' : '#96650d');
  return {
    darkMode: !!dark, background: bg, fontFamily: 'IBM Plex Sans, sans-serif', fontSize: '18px',
    primaryColor: box, primaryTextColor: text, primaryBorderColor: line, lineColor: dim,
    secondaryColor: bg, secondaryTextColor: text, secondaryBorderColor: line,
    tertiaryColor: bg, tertiaryTextColor: text, tertiaryBorderColor: line,
    clusterBkg: bg, clusterBorder: line, titleColor: text, edgeLabelBackground: bg, textColor: text,
    nodeTextColor: text, noteBkgColor: box, noteTextColor: dim, noteBorderColor: line,
    actorBkg: box, actorBorder: line, actorTextColor: text, actorLineColor: line,
    signalColor: dim, signalTextColor: text, labelBoxBkgColor: box, labelBoxBorderColor: line,
    labelTextColor: text, loopTextColor: dim, activationBkgColor: box, activationBorderColor: line,
    sequenceNumberColor: bg, altSectionBkgColor: 'transparent',
  };
}

async function renderMermaidBlocks(root) {
  const codes = $$('pre > code.language-mermaid', root);
  const existing = $$('.diagram[data-src]', root);
  if (!codes.length && !existing.length) return;
  const targets = existing.slice();
  for (const code of codes) {
    let src = code.textContent, caption = '';
    const cap = src.match(/^\s*%%\s*caption:\s*(.+)$/m);
    if (cap) { caption = cap[1].trim(); src = src.replace(cap[0], '').trim(); }
    const fig = document.createElement('figure');
    fig.className = 'diagram';
    fig.dataset.src = src;
    fig.dataset.caption = caption;
    code.parentElement.replaceWith(fig);
    targets.push(fig);
  }
  if (!await ensureMermaid()) {
    targets.forEach(f => { f.innerHTML = emptyMsg('Diagram unavailable', 'The diagram library did not load. Reconnect to the internet, then reload the page.'); });
    mermaidLoad = null;
    return;
  }
  mermaid.initialize({
    startOnLoad: false, securityLevel: 'strict', theme: 'base', themeVariables: mermaidVars(root),
    flowchart: { useMaxWidth: false, htmlLabels: true, curve: 'basis', nodeSpacing: 34, rankSpacing: 46, padding: 14 },
  });
  let i = 0;
  for (const fig of targets) {
    try {
      const { svg } = await mermaid.render(`mmd-${Date.now()}-${i++}`, fig.dataset.src);
      fig.innerHTML = `<div class="diagram-canvas">${svg}</div>
        <button type="button" class="diagram-zoom" aria-label="Expand diagram"><svg viewBox="0 0 24 24"><path d="M14 4h6v6M10 20H4v-6M20 4l-7 7M4 20l7-7"/></svg>Expand</button>
        ${fig.dataset.caption ? `<figcaption>${esc(fig.dataset.caption)}</figcaption>` : ''}`;
      const vb = $('.diagram-canvas svg', fig)?.viewBox?.baseVal;      // natural size, for .reader[data-mod] CSS
      if (vb && vb.width) fig.style.setProperty('--nat', `${Math.round(vb.width)}px`);
    } catch (e) {
      fig.innerHTML = emptyMsg('This diagram has a syntax error', esc(String(e.message || e)));
    }
  }
}

function rethemeMermaid() {
  const visible = $$('.view').find(v => !v.hidden);
  if (!visible) return;
  $$('.doc-prose', visible).forEach(p => { if ($('.diagram[data-src]', p)) renderMermaidBlocks(p); });
}

function openLightbox(fig) {
  const lb = $('#lightbox');
  const svg = $('.diagram-canvas svg', fig);
  if (!lb || !svg) return;
  const back = document.activeElement;
  lb.innerHTML = `
    <div class="lb-backdrop" data-lb="close"></div>
    <div class="lb-frame" role="dialog" aria-modal="true" aria-label="Diagram">
      <div class="lb-bar">
        <span class="lb-cap">${esc(fig.dataset.caption || 'Diagram')}</span>
        <div class="seg lb-tools">
          <button data-lb="out" aria-label="Zoom out">−</button>
          <button data-lb="fit">Fit</button>
          <button data-lb="in" aria-label="Zoom in">+</button>
        </div>
        <button class="icon-btn" data-lb="close" aria-label="Close"><svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg></button>
      </div>
      <div class="lb-stage"><div class="lb-canvas"></div></div>
      <p class="lb-hint">Scroll or use + and − to zoom. Drag to move around. Esc closes.</p>
    </div>`;
  const clone = svg.cloneNode(true);
  const vb = (clone.getAttribute('viewBox') || '0 0 800 600').split(/[\s,]+/).map(Number);
  clone.removeAttribute('style');
  clone.setAttribute('width', vb[2]);
  clone.setAttribute('height', vb[3]);
  const canvas = $('.lb-canvas', lb), stage = $('.lb-stage', lb);
  canvas.append(clone);
  lb.hidden = false;

  const view = { k: 1, x: 0, y: 0 };
  const paint = () => { canvas.style.transform = `translate(${view.x}px, ${view.y}px) scale(${view.k})`; };
  const fit = () => {
    const w = stage.clientWidth, h = stage.clientHeight;
    view.k = Math.min(w / vb[2], h / vb[3]) * .92;
    view.x = (w - vb[2] * view.k) / 2;
    view.y = (h - vb[3] * view.k) / 2;
    paint();
  };
  const zoom = (f, cx = stage.clientWidth / 2, cy = stage.clientHeight / 2) => {
    const k = Math.min(8, Math.max(.2, view.k * f));
    view.x = cx - (cx - view.x) * (k / view.k);
    view.y = cy - (cy - view.y) * (k / view.k);
    view.k = k;
    paint();
  };
  fit();
  stage.onwheel = e => {
    e.preventDefault();
    const box = stage.getBoundingClientRect();
    zoom(e.deltaY < 0 ? 1.12 : 1 / 1.12, e.clientX - box.left, e.clientY - box.top);
  };
  stage.onpointerdown = e => {
    stage.setPointerCapture(e.pointerId);
    stage.classList.add('dragging');
    const sx = e.clientX - view.x, sy = e.clientY - view.y;
    stage.onpointermove = ev => { view.x = ev.clientX - sx; view.y = ev.clientY - sy; paint(); };
    stage.onpointerup = () => { stage.onpointermove = null; stage.classList.remove('dragging'); };
  };
  lb.onclick = e => {
    const act = e.target.closest('[data-lb]')?.dataset.lb;
    if (act === 'close') closeLightbox();
    else if (act === 'in') zoom(1.25);
    else if (act === 'out') zoom(1 / 1.25);
    else if (act === 'fit') fit();
  };
  lb._back = back;
  $('.lb-bar [data-lb="close"]', lb).focus();
}

function closeLightbox() {
  const lb = $('#lightbox');
  if (!lb || lb.hidden) return false;
  lb.hidden = true;
  lb.innerHTML = '';
  lb._back?.focus?.();
  return true;
}

/* -------------------------------------------------------------- rail -- */
function buildRailToc(host, secs) {
  const toc = $('#railToc', host);
  if (!secs.length) { toc.innerHTML = ''; return; }
  toc.innerHTML = `<p class="rail-label">On this page<span class="rail-count">${secs.length}</span></p>
    <span class="toc-spine" aria-hidden="true"><i></i></span>` + secs.map((sec, i) => {
    const h2 = $('h2', sec);
    const subs = $$('h3', sec);
    return `<div class="toc-group" data-sid="${sec.dataset.sid}" style="--i:${i}">
      <a class="toc-h2" data-target="${h2.id}" tabindex="0"><i class="toc-dot" aria-hidden="true"></i><span>${esc(h2.dataset.label)}</span></a>
      ${subs.length ? `<div class="toc-subs">${subs.map(h => `<a class="toc-h3" data-target="${h.id}" tabindex="0">${esc(h.dataset.label)}</a>`).join('')}</div>` : ''}
    </div>`;
  }).join('');
}

function paintReaderProgress() {
  if (!curDoc) return;
  const r = docRec(curDoc.key);
  const secs = $$('#docProse .sec[data-sid]');
  const total = secs.length;
  const got = secs.filter(s => r.sections.includes(s.dataset.sid)).length;
  const pct = r.done ? 100 : total ? Math.round(got / total * 100) : Math.round(r.pct || 0);

  const wrap = $('#railProgress');
  if (wrap.dataset.n !== String(total)) {
    wrap.dataset.n = String(total);
    wrap.innerHTML = `
      <div class="rail-progress-top">
        <span class="ring-lg" style="--p:0"><b></b><svg viewBox="0 0 24 24" hidden>${CHECK_PATH}</svg></span>
        <span class="rail-progress-text"><b></b><span></span></span>
      </div>
      ${total ? `<div class="rail-meter" aria-hidden="true">${secs.map(() => '<i></i>').join('')}</div>` : ''}
      <p class="rail-eta"></p>`;
  }
  const ring = $('.ring-lg', wrap), ringNum = $('b', ring);
  ring.classList.toggle('done', !!r.done);
  ringNum.textContent = total ? `${got}/${total}` : `${pct}%`;
  ringNum.hidden = !!r.done;
  $('svg', ring).hidden = !r.done;
  requestAnimationFrame(() => ring.style.setProperty('--p', pct));
  $('.rail-progress-text b', wrap).textContent = r.done ? 'Completed' : got ? 'Getting there' : 'Not started';
  $('.rail-progress-text span', wrap).textContent = total ? `${got} of ${total} sections checked` : `${pct}% read`;
  $$('.rail-meter i', wrap).forEach((el, i) => el.classList.toggle('on', r.sections.includes(secs[i].dataset.sid)));
  const mins = curDoc.item?.minutes || 0, eta = $('.rail-eta', wrap);
  eta.className = `rail-eta${r.done ? ' done' : ''}`;
  eta.textContent = r.done ? 'Finished'
    : mins && total ? `about ${Math.max(1, Math.ceil(mins * (1 - got / total)))} min left`
      : '';

  $$('.sec-check').forEach(b => {
    const on = r.sections.includes(b.dataset.sid);
    b.setAttribute('aria-pressed', on);
    b.closest('.sec')?.classList.toggle('is-checked', on);
  });
  $$('#railToc .toc-group').forEach(g => g.classList.toggle('is-checked', r.sections.includes(g.dataset.sid)));
  const st = $('[data-meta="state"]');
  if (st) {
    st.textContent = r.done ? 'Completed' : got ? `${got} of ${total} sections checked` : r.pct > 2 ? `${Math.round(r.pct)}% read` : '';
    st.classList.toggle('is-done', !!r.done);
  }
  if (typeof paintRoadmapDay === 'function') paintRoadmapDay();
}

function paintDocEnd(mod, items, idx) {
  const m = MODULES[mod], r = docRec(curDoc.key);
  const prev = items[idx - 1], next = items[idx + 1];
  const link = (it, dir) => it ? `<a class="pager-link ${dir}" href="${itemHref(mod, it)}">
      <span>${dir === 'prev' ? 'Previous' : 'Next'}${m.label(it) ? `: ${esc(m.label(it))}` : ''}</span>
      <b>${esc(modTitle(m, it))}</b></a>` : '<span></span>';
  $('#docEnd').innerHTML = `
    <div class="done-card${r.done ? ' is-done' : ''}">
      <svg class="done-check" viewBox="0 0 52 52" aria-hidden="true"><circle cx="26" cy="26" r="23"/><path d="M15 27l7 7 15-16"/></svg>
      <div class="done-copy">
        <h3>${r.done ? 'Completed' : 'Finished this page?'}</h3>
        <p>${r.done ? `Ticked off${r.doneAt ? ` on ${fmtDate(r.doneAt)}` : ''}. It shows as done in the side navigation.`
          : 'Mark it complete to tick it off in the side navigation. Checking every section does the same.'}</p>
      </div>
      <button class="btn-mod${r.done ? ' ghost' : ''}" data-act="complete">${r.done ? 'Mark not complete' : 'Mark complete'}</button>
    </div>
    <nav class="pager" aria-label="Pages">${link(prev, 'prev')}${link(next, 'next')}</nav>`;
}

function setDocDone(done, celebrate) {
  if (!curDoc) return;
  docSave(curDoc.key, done ? { done: true, doneAt: today(), pct: 100 } : { done: false, doneAt: null });
  const items = modItemsSync(curDoc.mod) || [];
  paintDocEnd(curDoc.mod, items, items.findIndex(x => x.id === curDoc.id));
  paintReaderProgress();
  renderModNav();
  if (done && celebrate) {
    $('.done-card')?.classList.add('just-done');
    toast('Marked complete.', 'ok');
  }
}

function toggleSection(sid) {
  if (!curDoc) return;
  const r = docRec(curDoc.key);
  const on = r.sections.includes(sid);
  const sections = on ? r.sections.filter(s => s !== sid) : [...r.sections, sid];
  docSave(curDoc.key, { sections });
  paintReaderProgress();
  const all = $$('#docProse .sec[data-sid]').map(s => s.dataset.sid);
  if (!on && !r.done && all.length && all.every(s => sections.includes(s))) {
    setDocDone(true, false);
    $('.done-card')?.classList.add('just-done');
    toast('Every section checked. Page marked complete.', 'ok');
  } else {
    renderModNav();
  }
}

function wireReader(host, mod, items, idx) {
  const reader = $('.reader', host);
  host.onclick = e => {
    const t = e.target;
    const act = t.closest('[data-act]')?.dataset.act;
    if (act === 'prefs') {
      const pop = $('.reader-pop', host), btn = t.closest('[data-act]');
      pop.hidden = !pop.hidden;
      btn.setAttribute('aria-expanded', !pop.hidden);
      return;
    }
    if (act === 'focus') { toggleFocus(); return; }
    if (act === 'complete') { setDocDone(!docRec(curDoc.key).done, true); return; }
    if (act === 'reveal' || act === 'hide-solution') {
      const open = act === 'reveal', docKey_ = curDoc.key, id_ = curDoc.id;
      if (typeof revealOpen !== 'undefined') open ? revealOpen(`sd:${docKey_}`) : revealClose(`sd:${docKey_}`);
      if (open) docSave(docKey_, { revealed: true, reveals: (docRec(docKey_).reveals || 0) + 1, revealedAt: Date.now() });
      curDoc.justRevealed = open;
      curDoc.skipRestore = true;
      renderReader(mod, id_).then(() => {
        if (!curDoc || curDoc.key !== docKey_) return;
        curDoc.justRevealed = false;
        curDoc.skipRestore = false;
        $(open ? '[data-banner]' : '[data-gate]', host)?.scrollIntoView({ behavior: 'smooth', block: open ? 'start' : 'center' });
      });
      return;
    }
    const pref = t.closest('[data-pref]');
    if (pref) {
      const prefs = readerPrefs();
      prefs[pref.dataset.pref] = pref.dataset.v;
      saveReaderPrefs(prefs);
      reader.dataset[pref.dataset.pref] = pref.dataset.v;
      $$(`[data-pref="${pref.dataset.pref}"]`, host).forEach(b => b.classList.toggle('is-on', b === pref));
      if (pref.dataset.pref === 'paper') renderMermaidBlocks($('#docProse', host));
      return;
    }
    if (!t.closest('.reader-pop') && !$('.reader-pop', host).hidden) {
      $('.reader-pop', host).hidden = true;
      $('[data-act="prefs"]', host).setAttribute('aria-expanded', 'false');
    }
    const check = t.closest('.sec-check');
    if (check) { toggleSection(check.dataset.sid); return; }
    const toc = t.closest('[data-target]');
    if (toc) { document.getElementById(toc.dataset.target)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); return; }
    const copy = t.closest('.code-copy');
    if (copy) { copyCode(copy); return; }
    const zoom = t.closest('.diagram-zoom') || (t.closest('.diagram-canvas') && t.closest('.diagram'));
    if (zoom) { openLightbox(t.closest('.diagram')); return; }
    const anchor = t.closest('[data-anchor]');
    if (anchor) {
      const h = $$('#docProse h2, #docProse h3', host).find(x => slug(x.dataset.label || x.textContent).includes(anchor.dataset.anchor) || anchor.dataset.anchor.includes(slug(x.dataset.label || '')));
      h?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    const hl = t.closest('mark.hl');
    if (hl && getSelection().isCollapsed) { showHlTool(hl.getBoundingClientRect(), { mode: 'existing', hid: hl.dataset.hid }); return; }
    const jump = t.closest('[data-hl-jump]');
    if (jump) {
      const mk = $(`mark.hl[data-hid="${jump.dataset.hlJump}"]`, host);
      if (mk) {
        mk.scrollIntoView({ behavior: 'smooth', block: 'center' });
        $$(`mark.hl[data-hid="${jump.dataset.hlJump}"]`, host).forEach(x => {
          x.classList.remove('flash'); void x.offsetWidth; x.classList.add('flash');
        });
      }
    }
  };
  $('#docProse', host).onmouseup = () => setTimeout(onProseSelect, 0);
  $('#railToc', host).onkeydown = e => { if (e.key === 'Enter') e.target.click(); };
}

async function copyCode(btn) {
  const pre = btn.closest('.code').querySelector('pre');
  try {
    await navigator.clipboard.writeText(pre.textContent);
    btn.textContent = 'Copied';
    btn.classList.add('is-copied');
    setTimeout(() => { btn.textContent = 'Copy'; btn.classList.remove('is-copied'); }, 1400);
  } catch (e) { toast('The browser blocked clipboard access.', 'err'); }
}

function toggleFocus() {
  const on = $('#app').classList.toggle('reading-focus');
  $$('[data-act="focus"]').forEach(b => b.setAttribute('aria-pressed', on));
}

function wireReaderScroll(host, key) {
  const fill = $('.reader-progress i', host);
  const heads = $$('#docProse h2[id], #docProse h3[id]', host);
  const groups = $$('#railToc .toc-group', host);
  let raf = 0, saveT = 0, lastActive = null;
  const onScroll = (save = true) => {
    raf = 0;
    if (!curDoc || curDoc.key !== key) return;
    const max = host.scrollHeight - host.clientHeight;
    const pct = max > 0 ? Math.min(100, host.scrollTop / max * 100) : 0;
    fill.style.width = `${pct}%`;
    $('#railToc .toc-spine i', host)?.style.setProperty('--fill', `${pct}%`);

    const line = host.getBoundingClientRect().top + 110;
    let active = null;
    for (const h of heads) { if (h.getBoundingClientRect().top <= line) active = h; else break; }
    if (active !== lastActive) {
      lastActive = active;
      const sid = active ? active.closest('.sec')?.dataset.sid : null;
      groups.forEach(g => g.classList.toggle('is-active', g.dataset.sid === sid));
      $$('#railToc [data-target]', host).forEach(a => a.classList.toggle('is-on', !!active && a.dataset.target === active.id));
      const on = $('#railToc .toc-group.is-active', host);
      if (on) {
        const rail = $('.doc-rail', host), rb = rail.getBoundingClientRect(), ob = on.getBoundingClientRect();
        if (ob.top < rb.top || ob.bottom > rb.bottom) rail.scrollTop += ob.top - rb.top - 80;
      }
    }

    if (!save) return;   // opening a page is not reading it
    clearTimeout(saveT);
    saveT = setTimeout(() => {
      if (!curDoc || curDoc.key !== key) return;
      const r = docRec(key);
      const p = { pos: +(host.scrollTop / Math.max(1, host.scrollHeight)).toFixed(4), last: Date.now() };
      if (pct > (r.pct || 0)) p.pct = Math.round(pct);
      docSave(key, p);
    }, 900);
  };
  host.onscroll = () => { if (!raf) raf = requestAnimationFrame(() => onScroll(true)); };
  onScroll(false);
}

function observeReveals(host) {
  if (!('IntersectionObserver' in window) || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const io = new IntersectionObserver(entries => entries.forEach(en => {
    if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
  }), { root: host, rootMargin: '0px 0px -6% 0px' });
  $$('#docProse .callout, #docProse .diagram, #docProse .code, #docProse .table-wrap', host).forEach(el => {
    const box = el.getBoundingClientRect();
    if (box.top < host.getBoundingClientRect().bottom) return;   // already on screen: no entrance
    el.classList.add('rv');
    io.observe(el);
  });
}

/* ---------------------------------------------------------- highlights -- *
   Select text inside one paragraph, list item or table cell and pick a
   colour. Highlights are stored as the exact text plus the section it was
   in, and re-found on the next visit. */
const HL_BLOCKS = 'p, li, td, th, h3, h4, dd, figcaption';
const HL_COLORS = [['y', 'Yellow'], ['g', 'Green'], ['b', 'Blue'], ['p', 'Pink']];
let hlPending = null;

function hlBlockOf(node, root) {
  const el = (node.nodeType === 3 ? node.parentElement : node)?.closest(HL_BLOCKS);
  return el && root.contains(el) && !el.closest('pre, .diagram, .code, .sec-check, .lab, .iv-rubric button, .gloss-bar') ? el : null;
}

function onProseSelect() {
  const root = $('#docProse');
  const sel = getSelection();
  if (!root || !sel.rangeCount || sel.isCollapsed) return;
  const range = sel.getRangeAt(0);
  const block = hlBlockOf(range.startContainer, root);
  if (!block || block !== hlBlockOf(range.endContainer, root)) return;
  const offset = (container, off) => {
    const r = document.createRange();
    r.setStart(block, 0);
    r.setEnd(container, off);
    return r.toString().length;
  };
  const s = offset(range.startContainer, range.startOffset), e = offset(range.endContainer, range.endOffset);
  const text = block.textContent.slice(s, e);
  if (text.trim().length < 3) return;
  showHlTool(range.getBoundingClientRect(), { mode: 'new', block, s, e, text });
}

function hlTool() {
  let el = $('#hlTool');
  if (!el) {
    el = document.createElement('div');
    el.id = 'hlTool';
    el.className = 'hl-tool';
    el.hidden = true;
    document.body.append(el);
    el.addEventListener('mousedown', e => e.preventDefault());   // keep the selection alive
    el.onclick = e => {
      const b = e.target.closest('button');
      if (!b || !hlPending) return;
      if (b.dataset.color) addHighlight(b.dataset.color);
      else if (b.dataset.do === 'remove') removeHighlight(hlPending.hid);
      else if (b.dataset.do === 'copy') {
        const text = hlPending.text || $$(`mark.hl[data-hid="${hlPending.hid}"]`).map(m => m.textContent).join('');
        navigator.clipboard.writeText(text).then(() => toast('Copied.', 'ok'), () => toast('The browser blocked clipboard access.', 'err'));
        hideHlTool();
      }
    };
  }
  return el;
}

function showHlTool(rect, pending) {
  const el = hlTool();
  hlPending = pending;
  el.innerHTML = pending.mode === 'new'
    ? `${HL_COLORS.map(([c, l]) => `<button class="hl-swatch hl-${c}" data-color="${c}" aria-label="Highlight ${l.toLowerCase()}" title="Highlight"></button>`).join('')}
       <span class="hl-sep"></span><button data-do="copy">Copy</button>`
    : `<button data-do="remove">Remove highlight</button><span class="hl-sep"></span><button data-do="copy">Copy</button>`;
  el.hidden = false;
  const w = el.offsetWidth;
  el.style.left = `${Math.max(8, Math.min(innerWidth - w - 8, rect.left + rect.width / 2 - w / 2))}px`;
  el.style.top = `${Math.max(8, rect.top - el.offsetHeight - 10)}px`;
}

function hideHlTool() {
  const el = $('#hlTool');
  if (el) el.hidden = true;
  hlPending = null;
}

function wrapTextRange(block, s, e, h) {
  const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
  const hits = [];
  let pos = 0;
  for (let n = walker.nextNode(); n && pos < e; n = walker.nextNode()) {
    const len = n.data.length, a = Math.max(s, pos), b = Math.min(e, pos + len);
    if (a < b) hits.push([n, a - pos, b - pos]);
    pos += len;
  }
  for (const [n, a, b] of hits) {
    let target = n;
    if (a > 0) target = target.splitText(a);
    if (b - a < target.data.length) target.splitText(b - a);
    const mark = document.createElement('mark');
    mark.className = `hl hl-${h.color}`;
    mark.dataset.hid = h.id;
    target.replaceWith(mark);
    mark.append(target);
  }
}

function addHighlight(color) {
  const p = hlPending;
  if (!p || p.mode !== 'new' || !curDoc) return;
  const r = docRec(curDoc.key);
  const h = { id: Date.now().toString(36), text: p.text, color, sid: p.block.closest('.sec')?.dataset.sid || '' };
  wrapTextRange(p.block, p.s, p.e, h);
  docSave(curDoc.key, { highlights: [...r.highlights, h] });
  getSelection().removeAllRanges();
  hideHlTool();
  paintRailHighlights();
}

function removeHighlight(hid) {
  if (!curDoc) return;
  $$(`mark.hl[data-hid="${hid}"]`).forEach(m => { m.replaceWith(...m.childNodes); });
  $('#docProse')?.normalize();
  docSave(curDoc.key, { highlights: docRec(curDoc.key).highlights.filter(h => h.id !== hid) });
  hideHlTool();
  paintRailHighlights();
}

function applyHighlights(root, r) {
  for (const h of r.highlights) {
    const find = scope => $$(HL_BLOCKS, scope).find(b => !b.closest('pre, .diagram, .code') && b.textContent.includes(h.text));
    const sec = h.sid && $(`.sec[data-sid="${CSS.escape(h.sid)}"]`, root);
    const block = (sec && find(sec)) || find(root);
    if (!block) continue;
    const s = block.textContent.indexOf(h.text);
    wrapTextRange(block, s, s + h.text.length, h);
  }
}

function paintRailHighlights() {
  const host = $('#railHl');
  if (!host || !curDoc) return;
  const found = docRec(curDoc.key).highlights.filter(h => $(`mark.hl[data-hid="${h.id}"]`));
  host.innerHTML = found.length ? `
    <p class="rail-label">Your highlights</p>
    ${found.map(h => `<button class="hl-item hl-${h.color}" data-hl-jump="${h.id}">${esc(h.text.length > 90 ? `${h.text.slice(0, 88)}…` : h.text)}</button>`).join('')}`
    : `<p class="rail-tip">Select any sentence to highlight it. Highlights are saved with your progress.</p>`;
}

/* ------------------------------------------------------------ keyboard -- */
function jumpSection(dir) {
  const host = $('#viewDocReader');
  const heads = $$('#docProse h2[id]', host);
  if (!heads.length) return;
  const line = host.getBoundingClientRect().top + 120;
  let cur = -1;
  heads.forEach((h, i) => { if (h.getBoundingClientRect().top <= line) cur = i; });
  const target = heads[Math.min(heads.length - 1, Math.max(0, cur + dir))];
  target.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    if (closeLightbox()) return;
    const pop = $('.reader-pop:not([hidden])');
    if (pop) { pop.hidden = true; return; }
    if ($('#hlTool:not([hidden])')) { hideHlTool(); return; }
    if ($('#app').classList.contains('reading-focus') && !$('#viewDocReader').hidden) toggleFocus();
    return;
  }
  if (!curDoc || $('#viewDocReader').hidden || e.metaKey || e.ctrlKey || e.altKey) return;
  if (/^(INPUT|TEXTAREA|SELECT)$/.test(e.target.tagName) || !$('#lightbox')?.hidden) return;
  const k = e.key.toLowerCase();
  if (k === 'j' || k === 'k') { e.preventDefault(); jumpSection(k === 'j' ? 1 : -1); }
  else if (k === 'f') { e.preventDefault(); toggleFocus(); }
  else if (k === 'c') {
    const g = $('#railToc .toc-group.is-active') || $('#railToc .toc-group');
    if (g) toggleSection(g.dataset.sid);
  } else if (e.key === '[' || e.key === ']') {
    const a = $(`.pager-link.${e.key === '[' ? 'prev' : 'next'}`);
    if (a) location.hash = a.getAttribute('href');
  }
});
document.addEventListener('mousedown', e => {
  if (!e.target.closest('#hlTool') && !e.target.closest('mark.hl')) hideHlTool();
});

/* ============================================= engineering explanation == *
   GoEngineering / PyEngineering briefs are plain-text docstrings with
   underlined or ALL-CAPS headings, indented bullets and indented code.
   Convert that to markdown so the brief gets the same reader treatment. */
function docstringToMarkdown(text, lang) {
  const lines = text.replace(/\t/g, '    ').replace(/[ \t]+$/gm, '').split('\n');
  const out = [];
  const isRule = l => /^\s*([=\-~^*])\1{2,}$/.test(l);
  const isMarker = l => /^\s*([-*•]|\d+[.)])\s+\S/.test(l);
  const isCaps = l => !/^\s/.test(l) && l.length <= 64 && /^[A-Z][A-Z0-9 '’()/&,:.+?—–-]*$/.test(l) &&
    l.replace(/[^A-Z]/g, '').length >= 3;
  const inline = s => s.split(/(`[^`]*`)/).map((part, i) => i % 2 ? part
    : part.replace(/</g, '&lt;').replace(/(\w)_(?=\w)/g, '$1\\_')).join('');
  const looksArt = body => body.some(l => /[│┃┌┐└┘├┤┬┴┼─━═║╔╗╚╝▶◀►◄▼▲→←↑↓]|-->|<--|\+--|--\+|\|\s.*\s\|/.test(l)) ||
    body.filter(l => /\S {3,}\S/.test(l)).length >= 2;
  const looksCode = body => body.some(l =>
    /[{};]\s*$|:=|->|=>|^\s*(def|class|func|type|async|await|return|import|from|package|var|const|if|for|while|with|go|defer|select|case)\b|\w\(.*\)|^\s*@\w/.test(l));
  let i = 0, titled = false;

  while (i < lines.length) {
    const l = lines[i], nx = lines[i + 1] ?? '';
    if (!l.trim()) { out.push(''); i++; continue; }
    if (!/^\s/.test(l) && isRule(nx) && !isRule(l)) {
      out.push('', `${!titled && /=/.test(nx) ? '#' : '##'} ${tidyHeading(l.trim().replace(/:$/, ''))}`, '');
      titled = true; i += 2; continue;
    }
    if (isRule(l)) { i++; continue; }
    if (isCaps(l) && (!nx.trim() || /^\s/.test(nx) || isRule(nx))) {
      out.push('', `## ${tidyHeading(l.trim().replace(/:$/, ''))}`, '');
      i++; continue;
    }
    if (/^\s/.test(l) || isMarker(l)) {
      const block = [];
      while (i < lines.length) {
        const c = lines[i];
        if (c.trim()) {
          if (!/^\s/.test(c) && !isMarker(c)) break;
          block.push(c); i++;
        } else {
          const ahead = lines.slice(i + 1).find(x => x.trim());
          if (ahead && (/^\s/.test(ahead) || isMarker(ahead))) { block.push(''); i++; } else break;
        }
      }
      const filled = block.filter(b => b.trim());
      const ind = Math.min(...filled.map(b => b.match(/^\s*/)[0].length));
      const body = block.map(b => b.slice(ind));
      if (isMarker(body.find(b => b.trim()))) {
        const itemsOut = [];
        for (const raw of body) {
          if (!raw.trim()) continue;
          const mk = raw.match(/^(\s*)([-*•]|\d+[.)])\s+(.*)$/);
          if (mk) itemsOut.push({ indent: mk[1].length, num: /\d/.test(mk[2]) ? mk[2].replace(')', '.') : '-', text: mk[3] });
          else if (itemsOut.length) itemsOut[itemsOut.length - 1].text += ` ${raw.trim()}`;
        }
        const base = Math.min(...itemsOut.map(x => x.indent));
        out.push('', ...itemsOut.map(x => `${x.indent > base ? '    ' : ''}${x.num} ${inline(x.text)}`), '');
      } else if (looksCode(filled) || looksArt(filled)) {
        out.push('', `\`\`\`${looksArt(filled) && !looksCode(filled) ? 'text' : lang}`, ...body, '```', '');
      } else {
        out.push('', inline(filled.map(b => b.trim()).join(' ')), '');
      }
      continue;
    }
    const para = [];
    while (i < lines.length && lines[i].trim() && !/^\s/.test(lines[i]) && !isMarker(lines[i]) &&
           !isRule(lines[i + 1] ?? '') && !(para.length && isCaps(lines[i]))) {
      para.push(lines[i].trim()); i++;
    }
    if (!para.length) { para.push(l.trim()); i++; }
    out.push(inline(para.join(' ')), '');
  }
  return out.join('\n').replace(/\n{3,}/g, '\n\n');
}

async function renderEngExplanation(body, d, lang) {
  body.innerHTML = `<div class="eng-doc">
    <nav class="eng-chips" aria-label="Sections"></nav>
    <article class="prose doc-prose eng-prose"></article>
  </div>`;
  const art = $('.eng-prose', body);
  art.innerHTML = renderMarkdown(docstringToMarkdown(d.doc || '', lang === 'go' ? 'go' : 'python'));
  const h1 = art.firstElementChild;
  if (h1 && h1.tagName === 'H1') h1.remove();
  const secs = sectionize(art);
  decorateHeadings(art, false);
  enhanceCallouts(art);
  wrapTables(art);

  const chips = $('.eng-chips', body);
  chips.innerHTML = secs.map(s => `<button data-target="${$('h2', s).id}">${esc($('h2', s).dataset.label)}</button>`).join('');
  chips.hidden = secs.length < 2;
  chips.onclick = e => {
    const b = e.target.closest('[data-target]');
    if (b) document.getElementById(b.dataset.target)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };
  art.onclick = e => { const c = e.target.closest('.code-copy'); if (c) copyCode(c); };
  const heads = secs.map(s => $('h2', s));
  body.onscroll = () => {
    const line = body.getBoundingClientRect().top + 90;
    let active = heads[0];
    for (const h of heads) { if (h.getBoundingClientRect().top <= line) active = h; }
    $$('button', chips).forEach(b => b.classList.toggle('is-on', !!active && b.dataset.target === active.id));
  };
  body.onscroll();
  await renderCode(art);
}
