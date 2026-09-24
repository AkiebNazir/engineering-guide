/* ============================================================================
   Ultimate Engineering Guide — client
   ========================================================================= */
'use strict';

const $  = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];

const REVIEW_DAYS = [1, 3, 10, 30];       // D+1 → D+3 → D+10 → D+30 → mastered
const HINT_AT = 25 * 60;                  // hint ladder, from master_dsa_plan §0
const SOLVE_AT = 40 * 60;
const STATUS_GLYPH = { todo: '○', attempting: '◐', solved: '●', mastered: '★' };

// The 13-week runway from master_dsa_plan.md — the dashboard measures against it.
const PLAN_START = '2026-09-07';
const PLAN_END   = '2026-12-07';

// Difficulty is ordinal, so it is drawn as a 1/2/3-segment meter, not a colour.
const dmeter = (diff) =>
  `<span class="dmeter" data-diff="${diff}" title="${diff}" role="img" aria-label="${diff}"><i></i><i></i><i></i></span>`;

const daysBetween = (a, b) =>
  Math.round((new Date(b + 'T00:00:00') - new Date(a + 'T00:00:00')) / 86400000);

const fmtDate = iso => new Date(iso + 'T00:00:00')
  .toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

let DATA = { problems: [], topics: [], engTopics: { go: [], py: [] }, state: null, runtimes: {} };
let cur = null;            // current DSA problem record from DATA.problems
let curEng = null;         // current engineering topic: { lang, id, recId, num, title, has }
let curStdlib = null;      // current stdlib level: { lang, pkg, level, num, title, recId }
let mode = 'dsa';          // 'dsa' | 'eng' | 'api' | 'stdlib' — which workspace #viewProblem is showing
let curTab = 'question';
let curLang = 'py';
let editor = null;        // CodeMirror instance, or null when unavailable
let originalCode = '';    // pristine stub, for Reset
let saveTimer = null;
let docCache = new Map();

// Whichever workspace (DSA problem, engineering topic, API level, or stdlib level) is open.
const activeId = () =>
  mode === 'eng' ? (curEng && curEng.recId) :
  mode === 'api' ? (curApi && curApi.recId) :
  mode === 'stdlib' ? (curStdlib && curStdlib.recId) : (cur && cur.id);

/* --------------------------------------------------------------- utils -- */
const api = async (path, opts) => {
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
};
const post = (path, body) =>
  api(path, { method: 'POST', headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(body) });

const esc = s => s.replace(/[&<>"]/g, c =>
  ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const today = () => new Date().toISOString().slice(0, 10);
const addDays = (iso, n) => {
  const d = new Date(iso + 'T00:00:00');
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
};
const fmtTime = s => {
  const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
  return h ? `${h}:${String(m).padStart(2, '0')}:${String(x).padStart(2, '0')}`
           : `${String(m).padStart(2, '0')}:${String(x).padStart(2, '0')}`;
};

function rec(id) {
  if (!DATA.state.problems[id]) {
    DATA.state.problems[id] = {
      status: 'todo', notes: '', drafts: {}, timeSpent: 0,
      attempts: 0, runs: 0, solvedAt: null, reviews: [], nextReview: null,
    };
  }
  const r = DATA.state.problems[id];
  r.drafts ??= {}; r.reviews ??= []; r.timeSpent ??= 0;
  return r;
}

function toast(msg, kind = '') {
  const el = document.createElement('div');
  el.className = `toast ${kind}`;
  el.innerHTML = `<span class="bar"></span><span>${esc(msg)}</span>`;
  $('#toasts').append(el);
  setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 220); }, 2800);
}

/* ---------------------------------------------------------------- theme -- *
   Three states, not two: system / light / dark. "system" is the default and
   tracks the OS live, so the app is never the one window that stayed dark at
   sunrise. The chosen state — not the painted one — drives the toggle icon.  */
const THEMES = ['system', 'light', 'dark'];
const LIGHT_MQ = matchMedia('(prefers-color-scheme: light)');
let themePref = 'system';

/* ------------------------------------------------------------ sidebar --- *
   Below 860px the sidebar becomes a full-height overlay (see styles.css),
   so "hidden by default" and "shown by default" have to flip depending on
   viewport — a phone that opens straight into a 295px overlay covering the
   page is not a working first impression. setSidebarOpen() is the one place
   that decides the open/closed state so every trigger (hamburger, backdrop
   tap, Escape, search-while-collapsed, picking a link) stays in sync.       */
const MOBILE_MQ = matchMedia('(max-width: 860px)');
function setSidebarOpen(open) {
  $('#app').classList.toggle('sidebar-hidden', !open);
  document.documentElement.classList.toggle('scroll-lock', open && MOBILE_MQ.matches);
}
/* Code panel: fold the editor + console away to read the statement, solution or
   visualiser full width. Remembered across problems; Run reveals it again. */
function setCodeOpen(open, persist = true) {
  $('#split').classList.toggle('code-hidden', !open);
  const b = $('#toggleCode');
  b.setAttribute('aria-pressed', String(open));
  b.title = open ? 'Hide code panel (⌘\\)' : 'Show code panel (⌘\\)';
  if (open && editor) setTimeout(() => editor.refresh(), 0);
  if (persist) { try { localStorage.setItem('code-hidden', open ? '' : '1'); } catch (e) { /* private mode */ } }
}
/* Output panel: drag its top edge to size it, click the header (or ⌘J) to fold it to
   a single bar. Shared by every workspace — DSA, engineering, API, stdlib. */
function setConsoleFolded(folded, persist = true) {
  const c = $('#console');
  c.classList.toggle('is-collapsed', folded);
  const b = $('#btnFoldConsole');
  b.setAttribute('aria-expanded', String(!folded));
  b.setAttribute('aria-label', folded ? 'Expand output' : 'Collapse output');
  if (editor) setTimeout(() => editor.refresh(), 0);
  if (persist) { try { localStorage.setItem('console-folded', folded ? '1' : ''); } catch (e) { /* private mode */ } }
}
function setConsoleHeight(px, persist = true) {
  const pane = $('.pane-editor').getBoundingClientRect().height || 600;
  const h = Math.round(Math.min(Math.max(px, 84), Math.max(120, pane - 170)));
  $('#console').style.setProperty('--console-h', `${h}px`);
  if (editor) editor.refresh();
  if (persist) { try { localStorage.setItem('console-h', String(h)); } catch (e) { /* private mode */ } }
  return h;
}
const consoleFolded = () => $('#console').classList.contains('is-collapsed');
const codeOpen = () => !$('#split').classList.contains('code-hidden');
function syncSidebarForViewport() { setSidebarOpen(!MOBILE_MQ.matches); }

const resolveTheme = pref =>
  pref === 'system' ? (LIGHT_MQ.matches ? 'light' : 'dark') : pref;

function applyTheme(pref, persist) {
  themePref = THEMES.includes(pref) ? pref : 'system';
  const painted = resolveTheme(themePref);
  const root = document.documentElement;
  root.dataset.theme = painted;
  root.dataset.themePref = themePref;

  const label = themePref === 'system' ? `Theme: system (${painted})` : `Theme: ${themePref}`;
  const btn = $('#themeToggle');
  btn.title = label;
  btn.setAttribute('aria-label', label);

  try { localStorage.setItem('dsa-theme', themePref); } catch (e) { /* private mode */ }
  if (editor) editor.refresh();       // repaint gutters against the new ground
  rethemeMermaid();                   // diagrams are painted, not CSS — repaint on flip
  if (persist) {
    DATA.state.settings.theme = themePref;
    post('/api/patch', { settings: { theme: themePref } }).catch(() => {});
  }
}

function initTheme() {
  let pref = null;
  try { pref = localStorage.getItem('dsa-theme'); } catch (e) { /* private mode */ }
  applyTheme(pref || DATA.state.settings.theme || 'system', false);
  LIGHT_MQ.addEventListener('change', () => {
    if (themePref === 'system') applyTheme('system', false);
  });
}

/* --------------------------------------------------------------- saving -- */
function patch(id, p) { return post('/api/patch', { id, patch: p }).catch(() => {}); }

function markDirty() {
  $('#saveDot').textContent = 'unsaved';
  $('#saveDot').className = 'save-dot dirty';
  clearTimeout(saveTimer);
  saveTimer = setTimeout(flushDraft, 700);
}

async function flushDraft() {
  const id = activeId();
  if (!id) return;
  const r = rec(id);
  r.drafts[curLang] = getCode();
  $('#saveDot').textContent = 'saving';
  $('#saveDot').className = 'save-dot saving';
  await patch(id, { drafts: r.drafts });
  $('#saveDot').textContent = 'saved';
  $('#saveDot').className = 'save-dot';
}

/* ---------------------------------------------------------------- timer -- */
const timer = {
  sec: 0, running: false, handle: null, notifiedHint: false, notifiedSolve: false,
  start() {
    if (this.running) return;
    this.running = true;
    this.handle = setInterval(() => this.tick(), 1000);
    $('#timer').classList.add('running');
  },
  pause() {
    this.running = false;
    clearInterval(this.handle);
    $('#timer').classList.remove('running');
    const id = activeId();
    if (id) { rec(id).timeSpent = this.sec; patch(id, { timeSpent: this.sec }); }
  },
  toggle() { this.running ? this.pause() : this.start(); },
  reset(sec = 0) {
    this.pause(); this.sec = sec;
    this.notifiedHint = sec >= HINT_AT;
    this.notifiedSolve = sec >= SOLVE_AT;
    this.render();
  },
  tick() {
    this.sec++;
    const id = activeId();
    if (this.sec % 15 === 0 && id) {
      rec(id).timeSpent = this.sec;
      patch(id, { timeSpent: this.sec });
      post('/api/patch', { session: { date: today(), seconds: 15 } }).catch(() => {});
    }
    if (!this.notifiedHint && this.sec >= HINT_AT) {
      this.notifiedHint = true;
      toast('25 min — take ONE hint, then 15 more minutes.', 'warn');
    }
    if (!this.notifiedSolve && this.sec >= SOLVE_AT) {
      this.notifiedSolve = true;
      toast('40 min — open the solution. This one is auto-queued for review.', 'err');
    }
    this.render();
  },
  render() {
    $('#timerValue').textContent = fmtTime(this.sec);
    const el = $('#timer');
    el.classList.toggle('phase-hint', this.sec >= HINT_AT && this.sec < SOLVE_AT);
    el.classList.toggle('phase-solve', this.sec >= SOLVE_AT);
    $('#timerPhase').textContent =
      this.sec >= SOLVE_AT ? 'solution' : this.sec >= HINT_AT ? 'hint' : 'solo';
  },
};

/* ------------------------------------------------------------- progress -- */
const isDone = r => r.status === 'solved' || r.status === 'mastered';

function topicStats(tid) {
  const items = DATA.problems.filter(p => p.topic === tid);
  const done = items.filter(p => isDone(rec(p.id))).length;
  return { total: items.length, done, pct: items.length ? done / items.length * 100 : 0 };
}

function dueList() {
  const t = today();
  return DATA.problems
    .map(p => ({ p, r: rec(p.id) }))
    .filter(x => x.r.nextReview && x.r.status !== 'mastered')
    .filter(x => x.r.nextReview <= addDays(t, 2))
    .sort((a, b) => a.r.nextReview.localeCompare(b.r.nextReview));
}

function streakDays() {
  const s = DATA.state.sessions || {};
  let n = 0, d = today();
  if (!s[d]) d = addDays(d, -1);          // today not started yet is still fine
  while (s[d] && s[d] > 60) { n++; d = addDays(d, -1); }
  return n;
}

/* -------------------------------------------------------------- sidebar -- */
let query = '';

/* "two sum" should find "Two Sum" and "sql join" should find a join chapter:
   every word has to appear, in any order. */
const matchesAll = (hay, q) => q.split(/\s+/).every(t => hay.includes(t));

function passes(p, q = query) {
  if (q) {
    const hay = `${p.lc} ${p.title} ${p.topicTitle}`.toLowerCase();
    if (!matchesAll(hay, q)) return false;
  }
  return true;
}

/* -------------------------------------------------------- the sidebar -- *
   Modules, nothing else. Depth lives on the pages, not in a
   296px rail: DSA home → pattern page → problem, and each module's landing
   page → its cards. Typing in the search box turns the module list into one
   flat result list across the whole library.
   ========================================================================= */
const SECTIONS = ['dsa', 'sd', 'swd', 'go', 'py', 'roadmap', 'library', 'agentic', 'csfund', 'behavioral', 'api', 'sql', 'nosql', 'pystdlib', 'gostdlib'];

const SECTION_ICON = {
  dsa: '<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><path d="M17.5 14v7M14 17.5h7"/>',
  sd: '<rect x="3" y="3" width="7" height="6" rx="1.5"/><rect x="14" y="3" width="7" height="6" rx="1.5"/><rect x="8.5" y="15" width="7" height="6" rx="1.5"/><path d="M6.5 9v2.5h11V9M12 11.5V15"/>',
  swd: '<rect x="3" y="3" width="8" height="7" rx="1.5"/><rect x="13" y="14" width="8" height="7" rx="1.5"/><path d="M3 6.5h8M13 17.5h8M7 10v7.5h6"/>',
  go: '<path d="M4 17V7a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H6a2 2 0 01-2-2z"/><path d="M8 10l2 2-2 2M13 14h3"/>',
  py: '<path d="M4 17V7a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H6a2 2 0 01-2-2z"/><path d="M8 10l2 2-2 2M13 14h3"/>',
  roadmap: '<path d="M5 19c4 0 3-6 7-6s3-6 7-6"/><circle cx="5" cy="19" r="2"/><circle cx="19" cy="7" r="2"/>',
  library: '<path d="M4 4h4v16H4zM10 4h4v16h-4zM16.2 4.6l3.8-1 4 15.5-3.9 1z"/>',
  agentic: '<path d="M20 12a8 8 0 01-13.7 5.6M4 12a8 8 0 0113.7-5.6"/><path d="M17.5 2.5v4h-4M6.5 21.5v-4h4"/><circle cx="12" cy="12" r="2.5"/>',
  csfund: '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9z"/><path d="M12 12l8-4.5M12 12v9M12 12L4 7.5"/>',
  behavioral: '<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/>',
  api: '<path d="M17 1l4 4-4 4"/><path d="M3 11V9a4 4 0 014-4h14"/><path d="M7 23l-4-4 4-4"/><path d="M21 13v2a4 4 0 01-4 4H3"/>',
  sql: '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.66 3.58 3 8 3s8-1.34 8-3V5"/><path d="M4 12c0 1.66 3.58 3 8 3s8-1.34 8-3"/>',
  nosql: '<path d="M4 4h7v7H4zM13 4h7v7h-7z"/><path d="M4 14a4 4 0 004 4M13 14a4 4 0 004 4"/><circle cx="8" cy="20" r="2"/><circle cx="17" cy="20" r="2"/>',
  pystdlib: '<path d="M12 3c-4 0-5 1.5-5 4v2h5"/><path d="M12 21c4 0 5-1.5 5-4v-2h-5"/><rect x="3" y="9" width="9" height="6" rx="2"/><rect x="12" y="9" width="9" height="6" rx="2"/><circle cx="7" cy="6" r=".6" fill="currentColor" stroke="none"/><circle cx="17" cy="18" r=".6" fill="currentColor" stroke="none"/>',
  gostdlib: '<circle cx="8" cy="8" r="2.4"/><circle cx="16" cy="8" r="2.4"/><circle cx="12" cy="16" r="2.4"/><path d="M9.9 9.6L14.1 9.6M9.2 10.3L11 14M14.8 10.3L13 14"/>',
};

const sectionName = key => key === 'dsa' ? 'DSA' : MODULES[key].name;
const sectionHref = key => key === 'dsa' ? '#/dsa' : `#/${MODULES[key].hash}`;
const modsAsked = new Set();          // module lists already requested

/* the module the current page belongs to, so its row marks itself */
function activeSection() {
  if (curView === 'home' || curView === 'dashboard' || curView === 'review') return null;
  if (isDsaGuide(curModule)) return 'dsa';
  if (curModule) return curModule;
  if (mode === 'eng' && curEng) return curEng.lang === 'lld' ? 'swd' : curEng.lang;
  return 'dsa';
}

/* progress for a module row — null until its list has arrived from the server */
function sectionCount(key) {
  if (key === 'dsa') {
    return { done: DATA.problems.filter(p => isDone(rec(p.id))).length, total: DATA.problems.length };
  }
  const items = modItemsSync(key);
  if (!items) return null;
  return { done: items.filter(it => progressOf(key, it).state === 'done').length, total: items.length };
}

/* every module list, fetched once, so the rows can show real counts and the
   search box can reach a module you have never opened */
function loadSections() {
  for (const key of SECTIONS) {
    if (key === 'dsa' || modItemsSync(key) || modsAsked.has(key)) continue;
    modsAsked.add(key);
    modItems(key).then(() => renderSidebar()).catch(() => {});
  }
}

const modHit = (mod, it, q = query) => {
  const m = MODULES[mod];
  return matchesAll(`${m.name} ${m.label(it)} ${it.title} ${it.group || ''} ${it.summary || ''}`.toLowerCase(), q);
};

/* ---- search: one flat list over DSA and every module ---- */
const RESULT_CAP = 60;

function searchResults(q = query) {
  const out = [];
  for (const p of DATA.problems) {
    if (passes(p, q)) out.push({ sec: 'DSA', href: `#/p/${p.topic}/${p.seq}`, name: p.title,
                              meta: p.lc, on: cur && cur.id === p.id, st: rec(p.id).status });
  }
  for (const key of SECTIONS) {
    if (key === 'dsa') continue;
    const items = modItemsSync(key);
    if (!items) continue;
    const m = MODULES[key];
    for (const it of items) {
      if (!modHit(key, it, q)) continue;
      out.push({ sec: m.name, href: itemHref(key, it), name: modTitle(m, it),
                 meta: m.label(it), st: progressOf(key, it).state === 'done' ? 'solved' : 'todo' });
    }
  }
  return out;
}

function renderResults(host) {
  const all = searchResults();
  const shown = all.slice(0, RESULT_CAP);
  host.innerHTML = `
    <p class="results-head">${all.length ? `${all.length} result${all.length === 1 ? '' : 's'}` : 'No match'}
      ${all.length > shown.length ? `<em>showing ${shown.length}</em>` : ''}</p>
    ${shown.map(r => `
      <a class="rrow st-${r.st}${r.on ? ' is-on' : ''}" href="${r.href}">
        <span class="rrow-sec">${esc(r.sec)}</span>
        <span class="rrow-name">${esc(r.name)}</span>
        <span class="rrow-meta">${esc(String(r.meta || ''))}</span>
      </a>`).join('') ||
    `<p class="results-empty">Nothing in the library matches “${esc(query)}”.</p>`}`;
}

/* ------------------------------------------------------ quick jump (⌘K) --- *
   The sidebar search keeps its filter chips and lives beside the module
   list. This is the other way in: a centred box you can open from anywhere —
   even with the sidebar hidden or on a phone — type into, arrow through, and
   Enter. It ignores the DSA chips on purpose; jumping is not filtering.     */
const PAL_CAP = 40;
let palRows = [], palIdx = 0, palReturnFocus = null;

function paletteRows(q) {
  if (!q) {
    const go = [['Home', '#/home'], ['Dashboard', '#/dashboard'], ['Review queue', '#/review']]
      .map(([name, href]) => ({ sec: 'Go to', name, href, meta: '' }));
    const mods = SECTIONS.map(k => {
      const c = sectionCount(k);
      return { sec: 'Modules', name: sectionName(k), href: sectionHref(k), meta: c ? `${c.done}/${c.total}` : '' };
    });
    return [...go, ...mods];
  }
  const wordStart = new RegExp('(^|[^a-z0-9])' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
  const rank = r => {
    const n = r.name.toLowerCase();
    return n.startsWith(q) ? 0 : wordStart.test(n) ? 1 : n.includes(q) ? 2 : 3;
  };
  return searchResults(q)
    .map((r, i) => ({ r, i, k: rank(r) }))
    .sort((a, b) => a.k - b.k || a.i - b.i)
    .slice(0, PAL_CAP).map(x => x.r);
}

function renderPalette() {
  const q = $('#paletteInput').value.trim().toLowerCase();
  palRows = paletteRows(q);
  palIdx = Math.min(palIdx, Math.max(0, palRows.length - 1));
  let last = '';
  $('#paletteList').innerHTML = palRows.map((r, i) => {
    const head = !q && r.sec !== last ? `<p class="pal-head">${esc(r.sec)}</p>` : '';
    last = r.sec;
    return `${head}<a class="pal-row${i === palIdx ? ' is-on' : ''}" role="option" data-i="${i}" href="${r.href}"
        aria-selected="${i === palIdx}">
      <span class="pal-name">${esc(r.name)}</span>
      ${q ? `<span class="pal-sec">${esc(r.sec)}</span>` : ''}
      <span class="pal-meta">${esc(String(r.meta || ''))}</span></a>`;
  }).join('') || `<p class="pal-empty">Nothing matches “${esc(q)}”. Try fewer words — every word has to appear.</p>`;
}

function movePalette(to) {
  if (!palRows.length) return;
  palIdx = (to + palRows.length) % palRows.length;
  $$('#paletteList .pal-row').forEach((el, i) => {
    el.classList.toggle('is-on', i === palIdx);
    el.setAttribute('aria-selected', i === palIdx);
    if (i === palIdx) el.scrollIntoView({ block: 'nearest' });
  });
}

function openPalette() {
  loadSections();
  palReturnFocus = document.activeElement;
  $('#palette').hidden = false;
  $('#paletteInput').value = '';
  palIdx = 0;
  renderPalette();
  $('#paletteInput').focus();
}

function closePalette() {
  if ($('#palette').hidden) return;
  $('#palette').hidden = true;
  palReturnFocus?.focus?.();
}

function wirePalette() {
  $('#paletteBtn').onclick = openPalette;
  $('#palette .palette-scrim').onclick = closePalette;
  $('#paletteInput').oninput = () => { palIdx = 0; renderPalette(); };
  $('#paletteInput').onkeydown = e => {
    if (e.key === 'ArrowDown') { e.preventDefault(); movePalette(palIdx + 1); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); movePalette(palIdx - 1); }
    else if (e.key === 'Enter') {
      e.preventDefault();
      const r = palRows[palIdx];
      if (r) { palReturnFocus = null; closePalette(); location.hash = r.href; }
    }
    else if (e.key === 'Escape') { e.preventDefault(); closePalette(); }
    else if (e.key === 'Tab') { e.preventDefault(); }   // one control in the dialog — keep focus inside it
  };
  $('#paletteList').onclick = e => { if (e.target.closest('.pal-row')) { palReturnFocus = null; closePalette(); } };
  $('#paletteList').onmousemove = e => {
    const row = e.target.closest('.pal-row');
    if (row && +row.dataset.i !== palIdx) movePalette(+row.dataset.i);
  };
}

function renderSidebar() {
  const due = dueList().filter(x => x.r.nextReview <= today()).length;
  const badge = $('#reviewBadge');
  badge.hidden = !due; badge.textContent = due;

  const s = streakDays();
  $('#streakValue').textContent = s;
  $('#streak').classList.toggle('hot', s >= 3);

  loadSections();
  if (curView === 'home') updateHome();

  const active = activeSection();
  const host = $('#modules');

  if (query) {
    renderResults(host);
  } else {
    host.innerHTML = SECTIONS.map(key => {
      const c = sectionCount(key);
      const pct = c && c.total ? c.done / c.total * 100 : 0;
      return `
        <a class="mod-item${active === key ? ' is-on' : ''}" href="${sectionHref(key)}">
          <svg class="mod-icon" viewBox="0 0 24 24">${SECTION_ICON[key]}</svg>
          <span class="mod-name">${esc(sectionName(key))}</span>
          ${c ? `<span class="mod-count">${c.done}<i>/${c.total}</i></span>` : ''}
          <span class="mod-bar" aria-hidden="true"><i style="width:${pct}%"></i></span>
        </a>`;
    }).join('');
  }

  const foot = sectionCount(active && active !== 'dsa' ? active : 'dsa');
  const noun = active && active !== 'dsa' ? `${MODULES[active].noun} done` : 'solved';
  if (foot) {
    $('#overallFill').style.width = `${foot.total ? foot.done / foot.total * 100 : 0}%`;
    $('#overallText').textContent = `${foot.done} / ${foot.total} ${noun}`;
  }
}

/* ------------------------------------------------------------ dashboard -- */
function renderDashboard() {
  const total = DATA.problems.length;
  const byStatus = { todo: 0, attempting: 0, solved: 0, mastered: 0 };
  const byDiff = { Easy: [0, 0], Medium: [0, 0], Hard: [0, 0] };
  let written = 0;

  for (const p of DATA.problems) {
    const r = rec(p.id);
    byStatus[r.status]++;
    byDiff[p.diff][1]++;
    if (isDone(r)) byDiff[p.diff][0]++;
    if (p.has.pySolution) written++;
  }
  const done = byStatus.solved + byStatus.mastered;
  const secs = Object.values(DATA.state.sessions || {}).reduce((a, b) => a + b, 0);
  const due = dueList().filter(x => x.r.nextReview <= today()).length;
  const reviewReady = dueList().filter(x => x.r.nextReview <= today());
  const active = reviewReady[0]?.p || DATA.problems.find(p => rec(p.id).status === 'attempting') ||
    DATA.problems.find(p => rec(p.id).status === 'todo');
  const activeState = active ? rec(active.id) : null;
  const firstName = new Intl.DateTimeFormat('en-US', { weekday: 'long' }).format(new Date());

  let statN = 0;
  const stat = (label, value, foot, cls = '') => `
    <div class="stat ${cls}" style="--i:${statN++}">
      <div class="stat-label">${label}</div>
      <div class="stat-value">${value}</div>
      <div class="stat-foot">${foot}</div>
    </div>`;

  /* ---- the runway --------------------------------------------------------
     One question matters here: on pace for 7 Dec? So that is the hero. The
     track shows what is authored, what is solved, and a tick at where a steady
     pace would put you today. */
  const span    = daysBetween(PLAN_START, PLAN_END);
  const elapsed = Math.min(Math.max(daysBetween(PLAN_START, today()), 0), span);
  const left    = span - elapsed;
  const onPace  = Math.round(total * elapsed / span);
  const delta   = done - onPace;
  const pct     = n => (n / total * 100).toFixed(2);

  const verdict = done === 0
    ? { cls: 'start', line: 'Ready when you are',
        sub: `${left} days left · ${(total / Math.max(left, 1)).toFixed(1)}/day from here` }
    : delta >= 0
      ? { cls: 'ahead',  line: delta === 0 ? 'On pace' : `${delta} ahead of pace`,
          sub: `${left} days left · ${(total - done)} to go` }
      : { cls: 'behind', line: `${-delta} behind pace`,
          sub: `${left} days left · ${((total - done) / Math.max(left, 1)).toFixed(1)}/day to finish` };

  const weeks = Array.from({ length: 13 }, (_, i) => `<span>${i + 1}</span>`).join('');

  const dRow = (d) => {
    const [a, b] = byDiff[d];
    return `<div class="dbreak-row">
      ${dmeter(d)}
      <span class="dbreak-name">${d}</span>
      <span class="dbreak-track"><span style="width:${b ? a / b * 100 : 0}%"></span></span>
      <span class="dbreak-num">${a} / ${b}</span>
    </div>`;
  };

  $('#viewDashboard').innerHTML = `
    <div class="dash">
      <div class="dash-head">
        <span class="eyebrow">${firstName} · your engineering guide</span>
        <h1 class="dash-title">Engineer depth, one topic at a time.</h1>
        <p class="dash-sub">Your 13-week interview runway ends ${fmtDate(PLAN_END)}. Keep the next rep small and obvious.</p>
      </div>

      <div class="focus-grid">
        <section class="focus-card">
          <div class="focus-card-top">
            <span class="focus-kicker">${due ? 'Review is ready' : 'Next up'}</span>
            <span class="focus-orb" aria-hidden="true"></span>
          </div>
          ${active ? `<p class="focus-topic">${esc(active.topicTitle)}</p>
          <h2>${esc(active.title)}</h2>
          <div class="focus-meta">${dmeter(active.diff)} <span>${active.diff}</span><span class="focus-dot">·</span><span>${reviewReady.length ? 'Cold re-solve' : activeState.status === 'attempting' ? 'In progress' : 'Fresh problem'}</span></div>
          <button class="focus-action" data-open="${active.id}"><span>${reviewReady.length ? 'Begin review' : activeState.status === 'attempting' ? 'Continue solving' : 'Start a focused session'}</span><svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6"/></svg></button>` : ''}
        </section>
        <section class="review-card">
          <div class="review-card-icon">${due ? '↻' : '✓'}</div>
          <div>
            <span class="focus-kicker">Spaced repetition</span>
            <h2>${due ? `${due} ${due === 1 ? 'review' : 'reviews'} due` : 'Queue is clear'}</h2>
            <p>${due ? 'Keep the patterns you have earned sharp.' : 'Solved problems will appear here for cold re-solves.'}</p>
          </div>
          <button class="text-action" data-review>${due ? 'Open queue' : 'How it works'} <span>→</span></button>
        </section>
      </div>

      <div class="pace">
        <div class="pace-top">
          <div>
            <div class="pace-count"><b>${done}</b> <span>/ ${total}</span></div>
            <div class="pace-of">solved · ${written} of ${total} problems authored</div>
          </div>
          <div class="pace-verdict ${verdict.cls}">
            <div class="pace-verdict-line">${verdict.line}</div>
            <div class="pace-verdict-sub">${verdict.sub}</div>
          </div>
        </div>

        <div class="pace-track">
          <div class="pace-fill written" style="width:${pct(written)}%"></div>
          <div class="pace-fill solved"  style="width:${pct(done)}%"></div>
          <div class="pace-mark ${elapsed / span < .08 ? 'at-start' : elapsed / span > .92 ? 'at-end' : ''}"
               data-label="steady pace" style="left:${(elapsed / span * 100).toFixed(2)}%"></div>
        </div>
        <div class="pace-weeks">${weeks}</div>

        <div class="pace-key">
          <span><i style="background:var(--accent)"></i>solved</span>
          <span><i style="background:var(--border)"></i>authored, not yet solved</span>
        </div>
      </div>

      <div class="stat-strip">
        ${stat('Mastered', `${byStatus.mastered}`, 'cleared all four cold re-solves')}
        ${stat('In progress', byStatus.attempting, 'opened, not yet solved')}
        ${stat('Due for review', due, due ? 'cold re-solves waiting' : 'nothing due', due ? 'is-due' : '')}
        ${stat('Time practised', fmtTime(secs), `${streakDays()}-day streak`)}
      </div>

      <h2 class="section-title">By difficulty</h2>
      <div class="dbreak">${dRow('Easy')}${dRow('Medium')}${dRow('Hard')}</div>

      <h2 class="section-title">Topics</h2>
      <div class="topic-grid">
        ${DATA.topics.map((t, i) => {
          const st = topicStats(t.id);
          return `<button class="tcard" data-topic="${t.id}" style="--i:${i}">
            <span class="ring ${st.pct >= 100 ? 'done' : ''}" style="--p:${st.pct}">
              <span class="ring-label">${Math.round(st.pct)}</span>
            </span>
            <span class="tcard-body">
              <span class="tcard-name">${esc(t.title)}</span>
              <span class="tcard-meta">${st.done}/${st.total} solved · ${t.written} written${
                t.guides.py || t.guides.go ? ' · guides' : ''}</span>
            </span>
          </button>`;
        }).join('')}
      </div>
    </div>`;

  $$('.tcard', $('#viewDashboard')).forEach(el => {
    el.onclick = () => { location.hash = `#/t/${el.dataset.topic}`; };   // the pattern page, not its first problem
  });
  $('[data-open]', $('#viewDashboard'))?.addEventListener('click', e => {
    const [topic, seq] = e.currentTarget.dataset.open.split('/');
    location.hash = `#/p/${topic}/${seq}`;
  });
  $('[data-review]', $('#viewDashboard'))?.addEventListener('click', () => { location.hash = '#/review'; });
}

function renderReview() {
  const due = dueList();
  const t = today();
  const overdue = due.filter(x => x.r.nextReview < t).length;
  const todayN = due.filter(x => x.r.nextReview === t).length;
  const LADDER = [1, 3, 10, 30];

  const body = due.length ? `
    <div class="rq-summary">
      ${overdue ? `<span class="rq-pill over">${overdue} overdue</span>` : ''}
      ${todayN ? `<span class="rq-pill today">${todayN} due today</span>` : ''}
      <span class="rq-pill soon">${due.length - overdue - todayN} coming up</span>
    </div>
    <div class="rq">${due.map(({ p, r }, i) => {
      const cls = r.nextReview < t ? 'over' : r.nextReview === t ? 'today' : 'soon';
      const label = r.nextReview < t ? 'overdue' : r.nextReview === t ? 'today' : r.nextReview.slice(5);
      const pass = r.reviews.length;
      return `<button class="rq-item" data-id="${p.topic}/${p.seq}" style="--i:${i}">
        <span class="rq-due ${cls}">${label}</span>
        <span class="rq-body">
          <span class="rq-name"><span class="lc-num">${p.lc}</span>${esc(p.title)}</span>
          <span class="rq-meta">${esc(p.topicTitle)} · ${p.diff}</span>
        </span>
        <span class="rq-ladder" title="Pass ${pass} of 4">
          ${LADDER.map((d, k) => `<i class="${k < pass ? 'on' : ''}">D+${d}</i>`).join('')}
        </span>
        ${dmeter(p.diff)}
      </button>`;
    }).join('')}</div>` : `
    <div class="rq-zero">
      <div class="rq-zero-ladder" aria-hidden="true">
        ${LADDER.map((d, k) => `<span class="rq-step" style="--i:${k}"><b>D+${d}</b><i></i></span>`).join('')}
        <span class="rq-step is-end" style="--i:4"><b>★</b><i></i></span>
      </div>
      <h2>Nothing to re-solve today</h2>
      <p>Solving a problem puts it on this ladder. It comes back after one day,
         then three, then ten, then thirty — each time with a blank editor and no
         notes. Clear all four cold and it is marked mastered.</p>
      <a class="rq-cta" href="#/dsa">Pick a pattern to start<svg viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
    </div>`;

  $('#viewReview').innerHTML = `
    <div class="dash">
      <div class="dash-head">
        <span class="eyebrow">Spaced repetition</span>
        <h1 class="dash-title">Review queue</h1>
        <p class="dash-sub">Cold re-solves: blank editor, no notes, 20-minute timer. The point is recall, not recognition.</p>
      </div>${body}
    </div>`;

  $$('.rq-item', $('#viewReview')).forEach(el => {
    el.onclick = () => { location.hash = `#/p/${el.dataset.id}`; };
  });
}

/* -------------------------------------------------- markdown helpers -- *
   Shared by every markdown reader. The reader itself — layout, callouts,
   diagrams, highlights — lives in reader.js. */
/* Markdown's own backslash-escaping ("\_" -> "_", also "\*", "\[" etc.) runs
   on every plain-text character, math or not — it has no idea `$...$` is a
   different, incompatible escaping language living inside its paragraphs.
   `\text{bytes\_per\_element}` is correct KaTeX, but marked strips that
   backslash before KaTeX ever sees it, turning it into a bare `_` inside
   `\text{}` — which KaTeX rejects (underscore still means "subscript",
   even in text mode). The fix is to never let marked's inline parser touch
   math source at all: swap every span for an opaque placeholder first,
   parse normally, then splice the ORIGINAL raw LaTeX back in afterward. */
function stashMath(md) {
  const store = [];
  const stash = raw => { store.push(raw); return `${store.length - 1}`; };
  return {
    stashed: md
      .replace(/\$\$[\s\S]+?\$\$/g, stash)          // display math first — it contains bare $
      .replace(/\$(?!\s)[^\n$]+?(?<!\s)\$/g, stash), // then inline math, never crossing a blank line
    store,
  };
}
function unstashMath(html, store) {
  return html.replace(/(\d+)/g, (_, i) => esc(store[+i]));
}
function renderMarkdown(md) {
  const { stashed, store } = stashMath(md);
  return unstashMath(marked.parse(stashed), store);
}

/* Loaded once, lazily, on first use. A plain <script src> tag in index.html
   only runs for a tab that (re)loaded the page after the tag was added — a
   tab left open from before then never picks it up, and neither does a tab
   where the CDN request silently failed. Injecting the tag ourselves gives
   every page a real retry, and — unlike the silent early-return this
   replaced — a failure now shows a message instead of leaving raw mermaid
   source sitting on screen looking like a rendering bug. */
let mermaidLoad = null;
function ensureMermaid() {
  if (typeof mermaid !== 'undefined') return Promise.resolve(true);
  if (mermaidLoad) return mermaidLoad;
  mermaidLoad = new Promise(resolve => {
    const s = document.createElement('script');
    s.src = 'https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js';
    s.onload = () => resolve(typeof mermaid !== 'undefined');
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  });
  return mermaidLoad;
}

/* Loaded lazily, same reasoning and same self-healing shape as ensureMermaid
   above: a plain <script> tag only helps a tab that (re)loaded after the tag
   was added, and a failed CDN fetch should be retryable, not permanent. */
let katexLoad = null;
function ensureKatex() {
  if (typeof renderMathInElement !== 'undefined') return Promise.resolve(true);
  if (katexLoad) return katexLoad;
  const load = src => new Promise(resolve => {
    const s = document.createElement('script');
    s.src = src;
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.head.appendChild(s);
  });
  katexLoad = (async () => {
    if (typeof katex === 'undefined') {
      if (!await load('https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/katex.min.js')) return false;
    }
    if (typeof renderMathInElement === 'undefined') {
      if (!await load('https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.9/contrib/auto-render.min.js')) return false;
    }
    return typeof renderMathInElement !== 'undefined';
  })();
  return katexLoad;
}

async function renderMath(article) {
  // Cheap prefilter — most pages have no math at all, skip the CDN round trip.
  if (!/\$|\\\(|\\\[/.test(article.textContent)) return;
  const ready = await ensureKatex();
  if (!ready) { katexLoad = null; return; } // let the next reader retry
  try {
    renderMathInElement(article, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '\\[', right: '\\]', display: true },
        { left: '$', right: '$', display: false },
        { left: '\\(', right: '\\)', display: false },
      ],
      throwOnError: false,
    });
  } catch (e) { /* a genuinely malformed formula shouldn't blank the page */ }
}

/* --------------------------------------------------------------- editor -- */
function getCode() {
  return editor ? editor.getValue() : $('#editor').value;
}
function setCode(v) {
  if (editor) { editor.setValue(v); editor.clearHistory(); }
  else $('#editor').value = v;
}
function initEditor() {
  if (typeof CodeMirror === 'undefined') {
    $('#editor').addEventListener('input', markDirty);
    renderEditorStatus();
    toast('CodeMirror unavailable (offline?) — using a plain editor.', 'warn');
    return;
  }
  editor = CodeMirror.fromTextArea($('#editor'), {
    // 'studio' swaps cm-s-default for cm-s-studio on the wrapper. Without it
    // CodeMirror's stock light theme (.cm-s-default .cm-keyword etc.) outranks
    // our token rules on specificity and paints #708/#00f/#164 on near-black.
    theme: 'studio',
    mode: 'python', lineNumbers: true, indentUnit: 4, tabSize: 4,
    indentWithTabs: false, autoCloseBrackets: true, styleActiveLine: true,
    matchBrackets: true, lineWrapping: false,
    extraKeys: {
      'Cmd-Enter': runCode, 'Ctrl-Enter': runCode,
      'Cmd-S': cmSave, 'Ctrl-S': cmSave,
      'Cmd-/': cm => cm.toggleComment(), 'Ctrl-/': cm => cm.toggleComment(),
      'Shift-Tab': cm => cm.indentSelection('subtract'),
      Tab: cm => cm.somethingSelected()
        ? cm.indentSelection('add')
        : cm.replaceSelection(' '.repeat(cm.getOption('indentUnit'))),
    },
  });
  editor.on('change', markDirty);
  editor.on('cursorActivity', renderEditorStatus);
  renderEditorStatus();
}

/* The strip under the editor: where the caret is, and how much is selected.
   Same information VS Code's status bar carries, in the same order. */
function renderEditorStatus() {
  const cur$ = $('#esCursor'), sel$ = $('#esSel');
  if (!editor) { cur$.textContent = ''; sel$.hidden = true; return; }
  const c = editor.getCursor();
  cur$.textContent = `Ln ${c.line + 1}, Col ${c.ch + 1}`;

  const ranges = editor.listSelections().filter(r => CodeMirror.cmpPos(r.anchor, r.head));
  const chars = editor.getSelections().reduce((n, t) => n + t.length, 0);
  sel$.hidden = !chars;
  sel$.textContent = ranges.length > 1
    ? `${chars} selected in ${ranges.length} ranges`
    : `${chars} selected`;
}
function cmSave(cm) { flushDraft().then(() => toast('Saved', 'ok')); }

/* ------------------------------------------------------------------ run -- */
async function runCode() {
  const id = activeId();
  if (!id) return;
  if (!codeOpen()) setCodeOpen(true);   // the output lives in the code panel
  if (consoleFolded()) setConsoleFolded(false);
  const btn = $('#btnRun');
  btn.classList.add('busy');
  const stat = $('#consoleStat');
  stat.className = 'console-stat';
  stat.textContent = 'running…';
  $('#consoleBody').innerHTML = '<span class="muted">Executing…</span>';

  await flushDraft();
  try {
    const r = mode === 'eng'
      ? await post('/api/eng-run', { lang: curEng.lang, topic: curEng.id, code: getCode() })
      : mode === 'api'
      ? await post('/api/api-run', { type: curApi.type, section: curApi.section,
                                      level: curApi.id, lang: curLang, code: getCode() })
      : mode === 'stdlib'
      ? await post('/api/stdlib-run', { lang: curStdlib.lang, pkg: curStdlib.pkg,
                                         level: curStdlib.level, code: getCode() })
      : await post('/api/run', { code: getCode(), lang: curLang });
    const parts = [];
    if (r.stdout) parts.push(esc(r.stdout));
    if (r.stderr) parts.push(`<span class="err-text">${esc(r.stderr)}</span>`);
    if (!parts.length) parts.push('<span class="muted">(no output)</span>');
    $('#consoleBody').innerHTML = parts.join('\n');

    stat.className = `console-stat ${r.ok ? 'ok' : 'err'}`;
    stat.textContent = `${r.ok ? 'exit 0' : `exit ${r.exitCode}`} · ${r.ms} ms`;

    const rc = rec(id);
    rc.runs = (rc.runs || 0) + 1;
    patch(id, { runs: rc.runs });

    // LLD briefs print PASS/FAIL lines and exit 0 either way; only ALL PASSED counts.
    const engPassed = r.ok && (curEng?.lang !== 'lld' || /ALL PASSED/.test(r.stdout));
    if (mode === 'eng' && !engPassed && r.ok) {
      toast('Some checks failed — look for FAIL lines in the output.', 'warn');
    } else if (engPassed && mode === 'eng' && rc.status !== 'mastered') {
      toast('Tests passed — mark it solved?', 'ok');
    } else if ((mode === 'api' || mode === 'stdlib') && r.ok && rc.status !== 'mastered') {
      toast('Ran clean — mark it solved?', 'ok');
    } else if (r.ok && /ALL PASSED|all passed/i.test(r.stdout) && rc.status !== 'mastered') {
      toast('All tests passed — mark it solved?', 'ok');
    }
  } catch (e) {
    $('#consoleBody').innerHTML = `<span class="err-text">${esc(String(e))}</span>`;
    stat.className = 'console-stat err';
    stat.textContent = 'failed';
  } finally {
    btn.classList.remove('busy');
  }
}

async function formatCode() {
  if (curLang !== 'go') { toast('Format is Go-only (gofmt).', 'warn'); return; }
  const r = await post('/api/format', { code: getCode() });
  if (r.ok) { setCode(r.code); markDirty(); toast('gofmt applied', 'ok'); }
  else toast(r.error || 'gofmt failed', 'err');
}

/* -------------------------------------------------------------- statuses -- */
function setStatus(status) {
  const id = activeId();
  if (!id) return;
  const r = rec(id);
  const wasDone = isDone(r);
  r.status = status;

  if ((status === 'solved' || status === 'mastered') && !wasDone) {
    if (mode === 'eng' || mode === 'api' || mode === 'stdlib') {
      r.solvedAt = today();
      toast('Solved.', 'ok');
    } else {
      r.solvedAt = today();
      r.nextReview = addDays(today(), REVIEW_DAYS[0]);
      /* say where the solve leaves you, not just that it happened */
      const sibs = DATA.problems.filter(p => p.topic === cur.topic);
      const n = sibs.filter(p => isDone(rec(p.id))).length;
      const streak = streakDays();
      toast(n === sibs.length
        ? `Pattern complete: ${cur.topicTitle}. All ${n} solved.`
        : `Solved — ${n} of ${sibs.length} in ${cur.topicTitle}${streak >= 2 ? ` · ${streak}-day streak` : ''}. Re-solve due ${r.nextReview}.`, 'ok');
    }
  }
  if (status === 'mastered') r.nextReview = null;
  if (status === 'todo' || status === 'attempting') { r.nextReview = null; r.solvedAt = null; }

  patch(id, { status: r.status, solvedAt: r.solvedAt, nextReview: r.nextReview });
  paintStatus();
  renderSidebar();
  const btn = $(`#statusGroup .status-btn[data-status="${status}"]`);
  if (btn) { btn.classList.remove('pop'); void btn.offsetWidth; btn.classList.add('pop'); }
}

function paintStatus() {
  const id = activeId();
  const st = id ? rec(id).status : 'todo';
  $$('#statusGroup .status-btn').forEach(b =>
    b.classList.toggle('is-on', b.dataset.status === st));
  if (mode === 'stdlib' && typeof paintStdlibProgress === 'function') paintStdlibProgress();
}

/* -------------------------------------------------------------- prose -- */
function renderDoc(text, tab) {
  // problem-doc.js turns the ASCII-structured docstring into a real document:
  // example cards, constraint chips, highlighted code, complexity badges.
  if (typeof renderProblemDoc === 'function') {
    try { return renderProblemDoc(text, tab); } catch (e) { console.error('problem doc', e); }
  }
  // fallback: the original <pre>, with section headers lifted so it stays scannable
  const html = esc(text)
    .replace(/^(={10,})$/gm, '<span class="hd">$1</span>')
    .replace(/^(-{10,})$/gm, '<span class="hd">$1</span>')
    .replace(/^([A-Z][A-Z0-9 ()/&,'.\-]{3,})$/gm, '<span class="em">$1</span>')
    .replace(/^(\s*(?:⚠️|WARNING|NOTE:).*)$/gm, '<span class="warn">$1</span>')
    .replace(/(https?:\/\/\S+)/g, '<a href="$1" target="_blank" rel="noopener">$1</a>');
  return `<pre class="prose-pre">${html}</pre>`;
}

async function loadPane(tab) {
  curTab = tab;
  $$('#proseTabs .tab').forEach(t => t.classList.toggle('is-on', t.dataset.tab === tab));
  const body = $('#proseBody');

  if (mode === 'eng') return loadEngPane(tab);
  if (mode === 'api') return loadApiPane(tab);
  if (mode === 'stdlib') return loadStdlibPane(tab);

  if (tab === 'notes') {
    const r = rec(cur.id);
    /* The journal is what you reread the night before the interview, so it asks
       for the four things that actually transfer, and says when it saved. */
    const PROMPTS = [
      ['Trigger', 'Trigger: '],
      ['Technique', 'Technique: '],
      ['Gotcha', 'Gotcha: '],
      ['Complexity', 'Complexity: '],
    ];
    body.innerHTML = `
      <div class="notes-wrap">
        <div class="notes-head">
          <h3>Pattern journal</h3>
          <span class="notes-save" id="notesSave" aria-live="polite"></span>
        </div>
        <p class="notes-label">
          The <strong>trigger you should have spotted</strong> and the technique it points to —
          not the code. One or two lines is the right length.
        </p>
        <div class="notes-prompts">
          ${PROMPTS.map(([label, insert]) =>
            `<button type="button" class="notes-chip" data-insert="${insert}">${label}</button>`).join('')}
        </div>
        <textarea id="notesArea" placeholder="e.g. &quot;sorted array + find a pair&quot; → two pointers, converge from both ends"></textarea>
      </div>`;
    const ta = $('#notesArea'), save = $('#notesSave');
    ta.value = r.notes || '';
    save.textContent = r.notes ? 'saved' : '';
    let t;
    const flush = () => {
      r.notes = ta.value;
      patch(cur.id, { notes: r.notes });
      save.textContent = 'saved';
      save.classList.remove('is-dirty');
    };
    ta.oninput = () => {
      clearTimeout(t);
      save.textContent = 'saving…';
      save.classList.add('is-dirty');
      t = setTimeout(flush, 600);
    };
    $$('.notes-chip', body).forEach(b => b.onclick = () => {
      const prefix = ta.value && !ta.value.endsWith('\n') ? '\n' : '';
      ta.value += `${prefix}${b.dataset.insert}`;
      ta.focus();
      ta.setSelectionRange(ta.value.length, ta.value.length);
      ta.dispatchEvent(new Event('input'));
    });
    return;
  }

  /* dsa-viz.js: the step-by-step algorithm player for this topic */
  if (tab === 'visualize') {
    if (typeof renderAlgoTab === 'function') renderAlgoTab(body, cur.topic, cur);
    else body.innerHTML = emptyMsg('Visualizer unavailable', 'dsa-viz.js did not load.');
    return;
  }

  const key = `${cur.id}:${tab}:${curLang}`;
  let d = docCache.get(key);
  if (!d) {
    d = await api(`/api/problem?topic=${cur.topic}&seq=${cur.seq}&kind=${tab}&lang=${curLang}`);
    docCache.set(key, d);
  }
  /* solution-gate.js: solutions stay hidden until "Reveal solution" is pressed */
  if (tab === 'solution' && d.exists && typeof renderGatedSolution === 'function') {
    if (curTab === 'solution') renderGatedSolution(body, cur, d, curLang);
    return;
  }
  body.innerHTML = d.exists
    ? renderDoc(d.doc || '(no description in this file)', tab)
    : emptyMsg('Not written yet',
        `<code>${tab}</code> for this problem hasn't been authored in ${curLang === 'py' ? 'Python' : 'Go'} yet. The LeetCode link above still works.`);
  if (d.exists && typeof enhanceProblemDoc === 'function') enhanceProblemDoc(body);
}

const emptyMsg = (h, p) =>
  `<div class="empty"><div class="empty-icon">◌</div><h3>${h}</h3><p>${p}</p></div>`;

/* ------------------------------------------------ engineering workspace -- *
   GoEngineering / PyEngineering are a separate, single-language curriculum:
   production-grade problems (explanation/solution/test), not LeetCode
   question/solution pairs. They share the #viewProblem workspace and the
   one CodeMirror instance with the DSA flow — setEngTabs()/setDsaTabs()
   swap the tab bar's meaning, and mode + activeId() tell every shared
   helper (flushDraft, runCode, timer, setStatus) which record to touch. */
function setDsaTabs() {
  $('#proseTabs').innerHTML = `
    <button class="tab is-on" data-tab="question">Question</button>
    <button class="tab" data-tab="solution">Solution</button>
    <button class="tab" data-tab="visualize">Visualize</button>
    <button class="tab" data-tab="notes">Notes</button>`;
  curTab = 'question';
}
// LLD problems (Software Design) have no separate test file: the tests are at the
// bottom of the brief's own file, so the tab bar drops "Test".
const engTabs = lang => lang === 'lld' ? ['explanation', 'solution', 'notes'] : ['explanation', 'solution', 'test', 'notes'];
const ENG_TAB_LABEL = { explanation: 'Explanation', solution: 'Solution', test: 'Test', notes: 'Notes' };
const ENG_NAMES = { go: 'Go Engineering', py: 'Py Engineering', lld: 'Software Design · LLD practice' };

function setEngTabs(lang) {
  $('#proseTabs').innerHTML = engTabs(lang).map((t, i) =>
    `<button class="tab${i ? '' : ' is-on'}" data-tab="${t}">${lang === 'lld' && t === 'explanation' ? 'Brief' : ENG_TAB_LABEL[t]}</button>`).join('');
  curTab = 'explanation';
}

async function loadEngPane(tab) {
  const body = $('#proseBody');

  if (tab === 'notes') {
    const r = rec(curEng.recId);
    body.innerHTML = `
      <div class="notes-wrap">
        <div class="notes-label">
          Engineering journal — the <strong>design decision or trade-off</strong>
          you'd explain to a reviewer. Not the code.
        </div>
        <textarea id="notesArea" placeholder="e.g. chose optimistic locking over SELECT FOR UPDATE because writes are rare"></textarea>
      </div>`;
    const ta = $('#notesArea');
    ta.value = r.notes || '';
    let t;
    ta.oninput = () => {
      clearTimeout(t);
      t = setTimeout(() => { r.notes = ta.value; patch(curEng.recId, { notes: r.notes }); }, 600);
    };
    return;
  }

  const key = `eng:${curEng.recId}:${tab}`;
  let d = docCache.get(key);
  if (!d) {
    d = await api(`/api/eng-problem?lang=${curEng.lang}&topic=${curEng.id}&kind=${tab}`);
    docCache.set(key, d);
  }
  const langName = curEng.lang === 'go' ? 'Go' : 'Python';
  if (!d.exists) {
    body.innerHTML = emptyMsg('Not written yet',
      `This topic's <code>${tab}</code> hasn't been authored in ${langName} yet.`);
    return;
  }
  body.onscroll = null;
  body.scrollTop = 0;
  if (tab === 'explanation') await renderEngExplanation(body, d, curEng.lang);   // reader.js
  else if (curEng.lang === 'lld' && d.doc) {
    // LLD solutions carry a long written walkthrough in their docstring: render it as
    // prose, then the code beneath it.
    body.innerHTML = '<div class="lld-sol-doc"></div><div class="lld-sol-code"></div>';
    await renderEngExplanation($('.lld-sol-doc', body), d, 'lld');
    await renderCodeFile($('.lld-sol-code', body), d, 'lld');
  } else await renderCodeFile(body, d, curEng.lang);
}

async function loadEngEditor() {
  const key = `eng:${curEng.recId}:explanation`;
  let d = docCache.get(key);
  if (!d) {
    d = await api(`/api/eng-problem?lang=${curEng.lang}&topic=${curEng.id}&kind=explanation`);
    docCache.set(key, d);
  }
  originalCode = d.code || (curEng.lang !== 'go'
    ? '# This topic has not been authored yet.\n'
    : 'package main\n\nfunc main() {\n}\n');

  const r = rec(curEng.recId);
  setCode(r.drafts[curLang] ?? originalCode);
  $('#saveDot').textContent = 'saved';
  $('#saveDot').className = 'save-dot';
}

async function openEngTopic(lang, topicId) {
  const list = DATA.engTopics[lang] || [];
  const t = list.find(x => x.id === topicId);
  if (!t) { location.hash = lang === 'lld' ? '#/software-design' : `#/eng/${lang}`; return; }

  await flushDraft();
  cur = null;
  mode = 'eng';
  curLang = lang;
  curEng = { ...t, lang, recId: `${lang}-eng/${t.id}` };
  curModule = lang === 'lld' ? 'swd' : lang;

  showView('problem');
  setEngTabs(lang);
  $('#crumb').textContent = ENG_NAMES[lang] || lang;
  $('#problemTitle').innerHTML = `<span class="lc-num">${t.num}</span>${esc(t.title)}`;
  $('#diffPill').hidden = true;
  $('#lcLink').hidden = true;
  $('#langSwitch').hidden = true;
  $('#esLang').textContent = lang === 'go' ? 'Go' : 'Python';
  if (editor) editor.setOption('mode', lang === 'go' ? 'go' : 'python');
  $('#timer').hidden = false;

  const r = rec(curEng.recId);
  timer.reset(r.timeSpent || 0);
  paintStatus();
  r.lastOpened = Date.now();
  patch(curEng.recId, { lastOpened: r.lastOpened });

  if (r.status === 'todo') {
    r.status = 'attempting'; r.attempts = (r.attempts || 0) + 1;
    patch(curEng.recId, { status: r.status, attempts: r.attempts });
    paintStatus();
  }

  await loadEngEditor();
  await loadPane('explanation');
  renderSidebar();
}

/* ------------------------------------------------------- open a problem -- */
const DSA_TABS = ['question', 'solution', 'visualize', 'notes'];

async function openProblem(topic, seq, tab) {
  // exact match first; fall back to numeric so a typed/bookmarked "#/p/<topic>/1/…"
  // still finds "001" instead of silently landing on the dashboard
  const p = DATA.problems.find(x => x.topic === topic && x.seq === seq) ||
    DATA.problems.find(x => x.topic === topic && +x.seq === +seq);
  if (!p) { location.hash = '#/dashboard'; return; }

  await flushDraft();
  cur = p;
  curEng = null;
  mode = 'dsa';
  curModule = null;
  const r = rec(p.id);

  showView('problem');
  setDsaTabs();
  /* the crumb is the way back up to the pattern — without it the workspace is
     a dead end you can only leave through the sidebar */
  $('#crumb').innerHTML =
    `<a href="#/t/${p.topic}">${p.topic.split('_')[0]} · ${esc(p.topicTitle)}</a>`;
  $('#problemTitle').innerHTML =
    `<span class="lc-num">${p.lc}</span>${esc(p.title)}`;
  $('#diffPill').hidden = false;
  $('#diffPill').innerHTML = `${dmeter(p.diff)}${p.diff}`;
  $('#diffPill').className = 'pill';
  $('#lcLink').hidden = false;
  $('#lcLink').href = p.url;
  $('#langSwitch').hidden = false;
  $('#timer').hidden = false;

  timer.reset(r.timeSpent || 0);
  paintStatus();

  if (r.status === 'todo') { r.status = 'attempting'; r.attempts = (r.attempts || 0) + 1;
    patch(p.id, { status: r.status, attempts: r.attempts }); paintStatus(); }

  if (tab === 'guide') {                            // old bookmarks: the guide is a page now, not a tab
    const t = DATA.topics.find(x => x.id === topic);
    const lang = t && t.guides[curLang] ? curLang : 'py';
    location.replace(`#/dsa-guide${lang === 'go' ? '-go' : ''}/${topic}`);
    return;
  }
  await loadEditorFor(curLang);
  await loadPane(DSA_TABS.includes(tab) ? tab : curTab === 'notes' ? 'question' : curTab);
  renderSidebar();
}

async function loadEditorFor(lang) {
  curLang = lang;
  $$('#langSwitch .lang').forEach(b => b.classList.toggle('is-on', b.dataset.lang === lang));
  if (editor) editor.setOption('mode', lang === 'py' ? 'python' : 'go');
  $('#esLang').textContent = lang === 'py' ? 'Python' : 'Go';

  const key = `${cur.id}:question:${lang}`;
  let d = docCache.get(key);
  if (!d) {
    d = await api(`/api/problem?topic=${cur.topic}&seq=${cur.seq}&kind=question&lang=${lang}`);
    docCache.set(key, d);
  }
  originalCode = d.code || (lang === 'py'
    ? '# This problem has not been authored yet.\n'
    : 'package main\n\nfunc main() {\n}\n');

  const r = rec(cur.id);
  setCode(r.drafts[lang] ?? originalCode);
  $('#saveDot').textContent = 'saved';
  $('#saveDot').className = 'save-dot';
}

/* --------------------------------------------------------------- router -- */
const VIEWS = {
  home: '#viewHome', dashboard: '#viewDashboard', review: '#viewReview', 'dsa-home': '#viewDsaHome',
  'dsa-topic': '#viewDsaTopic', 'api-type': '#viewApiType', 'stdlib-pkg': '#viewStdlibPkg',
  'module-home': '#viewModuleHome', 'doc-reader': '#viewDocReader', problem: '#viewProblem',
};

let curView = '';

function showView(name) {
  curView = name;
  for (const [n, sel] of Object.entries(VIEWS)) $(sel).hidden = n !== name;
  if (name !== 'doc-reader') { curDoc = null; $('#app').classList.remove('reading-focus'); }
  $('#navDashboard').classList.toggle('is-on', name === 'dashboard');
  $('#navReview').classList.toggle('is-on', name === 'review');
  if (name !== 'dsa-topic') dsaTopicId = null;
  if (name !== 'api-type') apiTypeId = null;
  if (name !== 'stdlib-pkg') stdlibPkgId = null;
  syncModuleChrome();   // reader.js — module colour, nav highlight, sidebar swap
  if (name !== 'problem') { $('#timer').hidden = true; timer.pause(); }
  if (editor && name === 'problem') setTimeout(() => editor.refresh(), 0);
}

async function leaveWorkspace() {
  await flushDraft();
  cur = null; curEng = null; curApi = null; curStdlib = null; mode = 'dsa';
}

async function route() {
  if (MOBILE_MQ.matches) setSidebarOpen(false);   // picking a link closes the overlay behind it
  const h = location.hash.replace(/^#\//, '') || 'home';
  const parts = h.split('/').map(s => { try { return decodeURIComponent(s); } catch (e) { return s; } });
  if (parts[0] === 'eng' && parts[1] === 'lld' && parts.length === 2) {
    location.hash = '#/software-design';           // LLD problems are listed inside Software Design
    return;
  }
  if (parts[0] === 'p' && parts.length >= 3) {
    await openProblem(parts[1], parts[2], parts[3]);
  } else if (parts[0] === 't' && parts.length >= 2) {
    await leaveWorkspace(); curModule = null;
    showView('dsa-topic'); renderDsaTopic(parts[1]); renderSidebar();
  } else if (parts[0] === 'eng' && parts.length >= 3) {
    await openEngTopic(parts[1], parts[2]);
  } else if (parts[0] === 'api-type' && parts.length >= 2) {
    await leaveWorkspace(); curModule = 'api';
    showView('api-type'); renderApiType(parts[1]); renderSidebar();
  } else if (parts[0] === 'api-item' && parts.length >= 4) {
    await openApiItem(parts[1], parts[2], parts[3]);
  } else if (parts[0] === 'stdlib-pkg' && parts.length >= 3) {
    await leaveWorkspace(); curModule = parts[1] === 'go' ? 'gostdlib' : 'pystdlib';
    showView('stdlib-pkg'); renderStdlibPkg(parts[1], parts[2]); renderSidebar();
  } else if (parts[0] === 'stdlib-item' && parts.length >= 4) {
    await openStdlibItem(parts[1], parts[2], parts[3]);
  } else if (await routeModule(parts)) {
    // System Design, engineering lists, AI Roadmap, Library Guides, Agentic AI
  } else if (parts[0] === 'dsa') {
    await leaveWorkspace(); curModule = null;
    showView('dsa-home'); renderDsaHome(); renderSidebar();
  } else if (parts[0] === 'review') {
    await leaveWorkspace(); curModule = null;
    showView('review'); renderReview(); renderSidebar();
  } else if (parts[0] === 'dashboard') {
    await leaveWorkspace(); curModule = null;
    showView('dashboard'); renderDashboard(); renderSidebar();
  } else {
    await leaveWorkspace(); curModule = null;
    showView('home'); renderHome(); renderSidebar();
  }
}

/* ----------------------------------------------------------------- init -- */
function wireUI() {
  let hidden = false;
  try { hidden = !!localStorage.getItem('code-hidden'); } catch (e) { /* private mode */ }
  setCodeOpen(!hidden, false);
  try {
    const h = +localStorage.getItem('console-h');
    if (h) $('#console').style.setProperty('--console-h', `${h}px`);
    if (localStorage.getItem('console-folded')) setConsoleFolded(true, false);
  } catch (e) { /* private mode */ }
  $('#btnFoldConsole').onclick = () => setConsoleFolded(!consoleFolded());
  $('#consoleBar').ondblclick = e => { if (!e.target.closest('button')) setConsoleFolded(!consoleFolded()); };
  const grip = $('#consoleResize');
  grip.ondblclick = () => setConsoleFolded(true);
  grip.onpointerdown = e => {
    e.preventDefault();
    grip.setPointerCapture(e.pointerId);
    grip.classList.add('dragging'); document.body.classList.add('is-resizing');
    const bottom = $('.pane-editor').getBoundingClientRect().bottom;
    const move = ev => setConsoleHeight(bottom - ev.clientY, false);
    const up = () => {
      grip.classList.remove('dragging'); document.body.classList.remove('is-resizing');
      grip.removeEventListener('pointermove', move); grip.removeEventListener('pointerup', up);
      try { localStorage.setItem('console-h', String(Math.round($('#console').getBoundingClientRect().height))); } catch (er) { /* private mode */ }
    };
    grip.addEventListener('pointermove', move); grip.addEventListener('pointerup', up);
  };
  grip.onkeydown = e => {
    if (e.key !== 'ArrowUp' && e.key !== 'ArrowDown') return;
    e.preventDefault();
    setConsoleHeight($('#console').getBoundingClientRect().height + (e.key === 'ArrowUp' ? 24 : -24));
  };
  $('#toggleCode').onclick = () => setCodeOpen(!codeOpen());
  $('#toggleSidebar').onclick = () => setSidebarOpen($('#app').classList.contains('sidebar-hidden'));
  $('#sidebarBackdrop').onclick = () => setSidebarOpen(false);
  wirePalette();
  MOBILE_MQ.addEventListener('change', syncSidebarForViewport);

  $('#themeToggle').onclick = () => {
    const next = THEMES[(THEMES.indexOf(themePref) + 1) % THEMES.length];
    applyTheme(next, true);
    toast(next === 'system' ? `Theme: system (${resolveTheme(next)})` : `Theme: ${next}`);
  };

  /* Two characters minimum: one letter matches most of a 700-row library, and
     search mode redraws the whole tree on every keystroke. */
  $('#search').oninput = e => {
    const v = e.target.value.trim().toLowerCase();
    query = v.length >= 2 ? v : '';
    if (query && $('#app').classList.contains('sidebar-hidden')) setSidebarOpen(true);   // results render in the sidebar
    renderSidebar();
  };

  $('#proseTabs').onclick = e => {
    const t = e.target.closest('.tab'); if (t && activeId()) loadPane(t.dataset.tab);
  };
  $('#langSwitch').onclick = async e => {
    const b = e.target.closest('.lang'); if (!b || b.dataset.lang === curLang) return;
    if (mode === 'dsa') {
      if (!cur) return;
      await flushDraft();
      await loadEditorFor(b.dataset.lang);
      DATA.state.settings.lang = b.dataset.lang;
      post('/api/patch', { settings: { lang: b.dataset.lang } }).catch(() => {});
      if (curTab !== 'notes') loadPane(curTab);
    } else if (mode === 'api') {
      if (!curApi) return;
      await flushDraft();
      curLang = b.dataset.lang;
      $$('#langSwitch .lang').forEach(x => x.classList.toggle('is-on', x.dataset.lang === curLang));
      $('#esLang').textContent = curLang === 'py' ? 'Python' : 'Go';
      if (editor) editor.setOption('mode', curLang === 'go' ? 'go' : 'python');
      await loadApiEditor();
      if (curTab !== 'notes') loadPane(curTab);
    }
  };
  $('#statusGroup').onclick = e => {
    const b = e.target.closest('.status-btn'); if (b) setStatus(b.dataset.status);
  };

  $('#btnRun').onclick = runCode;
  $('#btnFormat').onclick = formatCode;
  $('#btnReset').onclick = () => {
    if (!activeId()) return;
    if (!confirm('Discard your code and restore the original stub?')) return;
    setCode(originalCode); markDirty();
  };
  $('#btnCopyConsole').onclick = async () => {
    const text = $('#consoleBody').innerText.trim();
    if (!text) return;
    try { await navigator.clipboard.writeText(text); toast('Output copied', 'ok'); }
    catch (e) { toast('Clipboard blocked by the browser', 'err'); }
  };
  $('#btnClearConsole').onclick = () => {
    $('#consoleBody').innerHTML = '<span class="muted">Cleared.</span>';
    $('#consoleStat').textContent = ''; $('#consoleStat').className = 'console-stat';
  };
  $('#timerToggle').onclick = () => timer.toggle();

  // split resize
  const gutter = $('#gutter'), prose = $('.pane-prose');
  gutter.onmousedown = e => {
    e.preventDefault();
    gutter.classList.add('dragging');
    const move = ev => {
      const box = $('#split').getBoundingClientRect();
      const pct = Math.min(75, Math.max(22, (ev.clientX - box.left) / box.width * 100));
      prose.style.flexBasis = `${pct}%`;
      if (editor) editor.refresh();
    };
    const up = () => {
      gutter.classList.remove('dragging');
      document.removeEventListener('mousemove', move);
      document.removeEventListener('mouseup', up);
    };
    document.addEventListener('mousemove', move);
    document.addEventListener('mouseup', up);
  };

  window.addEventListener('hashchange', route);
  window.addEventListener('beforeunload', () => {
    const id = activeId();
    if (id) { navigator.sendBeacon?.('/api/patch', new Blob(
      [JSON.stringify({ id, patch: { drafts: { ...rec(id).drafts, [curLang]: getCode() },
        timeSpent: timer.sec } })], { type: 'application/json' })); }
  });

  document.onkeydown = e => {
    const mod = e.metaKey || e.ctrlKey;
    const typing = /^(INPUT|TEXTAREA)$/.test(e.target.tagName) ||
                   e.target.closest('.CodeMirror');
    if (mod && e.key.toLowerCase() === 'k') { e.preventDefault(); $('#palette').hidden ? openPalette() : closePalette(); }
    else if (mod && e.key === 'Enter') { e.preventDefault(); runCode(); }
    else if (mod && e.key.toLowerCase() === 'j') { e.preventDefault(); if (codeOpen()) setConsoleFolded(!consoleFolded()); }
    else if (mod && e.key === '\\') { e.preventDefault(); setCodeOpen(!codeOpen()); }
    else if (mod && e.key.toLowerCase() === 'b') { e.preventDefault(); $('#toggleSidebar').click(); }
    else if (mod && e.shiftKey && e.key.toLowerCase() === 't') { e.preventDefault(); timer.toggle(); }
    else if (mod && e.key.toLowerCase() === 's' && !editor) { e.preventDefault(); flushDraft(); }
    else if (e.key === '/' && !typing) { e.preventDefault(); $('#search').focus(); }
    else if (e.key === 'Escape' && e.target === $('#search')) {
      $('#search').value = ''; query = ''; renderSidebar(); $('#search').blur();
    }
    else if (e.key === 'Escape' && MOBILE_MQ.matches && !$('#app').classList.contains('sidebar-hidden')) {
      setSidebarOpen(false);
    }
    else if (!typing && activeId() && ['1', '2', '3', '4', '5'].includes(e.key)) {
      const tabs = mode === 'eng' ? engTabs(curEng.lang)
                                   : ['question', 'solution', 'visualize', 'notes'];
      if (tabs[+e.key - 1]) loadPane(tabs[+e.key - 1]);
    }
  };
}

(async function boot() {
  syncSidebarForViewport();   // set before first paint settles — no flash of an open overlay on phones
  try {
    DATA = await api('/api/bootstrap');
  } catch (e) {
    document.body.innerHTML =
      `<div class="empty" style="padding-top:120px"><div class="empty-icon">⚠</div>
       <h3>Cannot reach the server</h3><p>Start it with <code>python webapp/server.py</code>.</p></div>`;
    return;
  }
  initTheme();
  initEditor();
  wireUI();
  await route();
})();
