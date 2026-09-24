/* ============================================================================
   API practice — Foundation ladders + labs, runnable in-browser.

   The API module (reader.js MODULES.api) already reads Theory.md end to end.
   This file adds the missing hands-on layer on top of it, in the same shape
   dsa-topic.js already proved out for DSA:

     #/api-type/<Type>        "main page of the topic" — every Foundation
                               level and lab for one API style, in order,
                               with prev/next to the neighbouring style.
     #/api-item/<Type>/<section>/<id>
                               the level itself, opened in the SAME #viewProblem
                               workspace DSA and Go/Py Engineering already use
                               (mode = 'api' alongside 'dsa' | 'eng') — read the
                               explanation, edit the code, run it for real
                               output, switch Python <-> Go.

   Foundation files are fully worked, self-checking examples, not fill-in-
   stubs (see api-foundation-teaching-order.md) — so there is one tab, not a
   question/solution split, and "solved" just means "I ran it and understood
   it", set by hand like Go/Py Engineering.

   Reads/writes app.js globals: DATA, mode, cur, curEng, curLang, curModule,
   editor, originalCode, docCache, rec, patch, flushDraft, showView, timer,
   paintStatus, renderSidebar, setCode, getCode, esc, $, $$, api, post,
   STATUS_GLYPH, emptyMsg — and reader.js's renderEngExplanation.
   ========================================================================= */
'use strict';

let curApi = null;          // { type, section, id, num, title, has, recId } while #viewProblem shows an API level
let apiTypeId = null;        // type currently shown on #viewApiType, for the sidebar
let apiTypesCache = null;    // /api/api-types, cached — module-home practice strip
const apiTypeCache = new Map();  // type -> /api/api-type?type=... detail

async function apiTypesData() {
  if (!apiTypesCache) {
    try { apiTypesCache = (await api('/api/api-types')).items; }
    catch (e) { apiTypesCache = []; }
  }
  return apiTypesCache;
}
const apiTypesSync = () => apiTypesCache;

async function apiTypeDetail(type) {
  if (!apiTypeCache.has(type)) {
    apiTypeCache.set(type, api(`/api/api-type?type=${encodeURIComponent(type)}`).catch(() => ({ exists: false })));
  }
  return apiTypeCache.get(type);
}

/* -------------------------------------------------- module-home strip -- *
   Injected at the top of the API module's card grid (reader.js renderModGrid)
   so "how do I actually run any of this" is answered before you even open a
   Theory page. */
function apiPracticeStrip() {
  const types = apiTypesSync();
  if (!types || !types.length) return '';
  return `
    <section class="aps">
      <header class="aps-head">
        <h2>Practice: Foundation levels &amp; labs</h2>
        <p>Fully worked, self-checking code, ground zero to production topic — read it, edit it, run it for real
           output, right in the browser, in Python and Go.</p>
      </header>
      <div class="aps-grid">
        ${types.map(t => `
          <a class="aps-card" href="#/api-type/${encodeURIComponent(t.id)}">
            <span class="aps-card-name">${esc(t.id)}</span>
            <span class="aps-card-counts">
              <span><b>${t.foundationCount}</b> Foundation levels</span>
              <span><b>${t.labsCount}</b> labs</span>
            </span>
            <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
          </a>`).join('')}
      </div>
    </section>`;
}

/* --------------------------------------------------------- type page -- */
function apiRowState(rowId) {
  const r = DATA.state.problems[rowId];
  return r ? r.status : 'todo';
}

function apiRow(type, section, item, i) {
  const rowId = `api/${type}/${section}/${item.id}`;
  const st = apiRowState(rowId);
  const href = `#/api-item/${type}/${section}/${item.id}`;
  return `
    <li style="--i:${i}">
      <a class="tprow st-${st}" href="${href}">
        <span class="tprow-seq">${item.num}</span>
        <span class="tprow-glyph" aria-hidden="true">${STATUS_GLYPH[st]}</span>
        <span class="tprow-main">
          <span class="tprow-title">${esc(item.title)}</span>
          <span class="tprow-tags">
            ${item.has.py ? '<span class="tptag">Python</span>' : ''}
            ${item.has.go ? '<span class="tptag">Go</span>' : ''}
          </span>
        </span>
        <svg class="tprow-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>
      </a>
    </li>`;
}

function apiTypeNavCard(type, label, dir) {
  return `
    <a class="tp-navcard ${dir}" href="#/api-type/${encodeURIComponent(type)}">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
      <span class="tp-navcard-label">${label}</span>
      <span class="tp-navcard-title">${esc(type)}</span>
    </a>`;
}

async function renderApiType(type) {
  const host = $('#viewApiType');
  apiTypeId = type;
  host.innerHTML = `<div class="mod-loading">Loading ${esc(type)}…</div>`;

  let d;
  try { d = await apiTypeDetail(type); } catch (e) { d = { exists: false }; }
  if (apiTypeId !== type || host.hidden) return;
  if (!d || !d.exists) {
    host.innerHTML = emptyMsg('Not found', `"${esc(type)}" is not one of the API styles in this curriculum.`);
    return;
  }

  const rows = [...d.foundation.map(it => ({ it, section: 'Foundation' })),
                ...d.labs.map(it => ({ it, section: 'labs' }))];
  const done = rows.filter(({ it, section }) => {
    const st = apiRowState(`api/${type}/${section}/${it.id}`);
    return st === 'solved' || st === 'mastered';
  }).length;
  const pct = rows.length ? done / rows.length * 100 : 0;
  const next = rows.find(({ it, section }) => apiRowState(`api/${type}/${section}/${it.id}`) === 'attempting')
    || rows.find(({ it, section }) => apiRowState(`api/${type}/${section}/${it.id}`) === 'todo')
    || rows[0];

  host.innerHTML = `
    <div class="tpage atpage">
      <nav class="tp-crumb" aria-label="Breadcrumb">
        <a href="#/apis"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 18l-6-6 6-6"/></svg>API Technologies</a>
        <span class="tp-crumb-sep" aria-hidden="true">/</span>
        <span>${esc(type)}</span>
      </nav>

      <header class="tp-hero">
        <div class="tp-hero-copy">
          <p class="tp-eyebrow">${d.foundation.length} Foundation levels · ${d.labs.length} labs</p>
          <h1 class="tp-title">${esc(type)}</h1>
          <p class="tp-tagline">${d.theorySummary ? esc(d.theorySummary) : `Ground zero to a complete, secured ${esc(type)} service — read, edit and run every level in Python and Go.`}</p>
          <div class="tp-actions">
            ${next ? `<a class="tp-go" href="#/api-item/${type}/${next.section}/${next.it.id}">
              <span class="tp-go-label">${done === rows.length && rows.length ? 'Re-run' : done ? 'Continue' : 'Start here'}</span>
              <span class="tp-go-title">${esc(next.it.title)}</span>
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
            </a>` : ''}
            ${d.hasTheory ? `<a class="tp-btn" href="#/apis/${type}/Theory">Read the Theory</a>` : ''}
          </div>
        </div>
        <aside class="tp-gauge" aria-label="Progress in this API style">
          <span class="tp-ring${pct >= 100 && rows.length ? ' done' : ''}" style="--p:0" data-p="${pct.toFixed(1)}">
            <b>${done}<span>/${rows.length}</span></b>
          </span>
        </aside>
      </header>

      ${d.foundation.length ? `
      <section class="at-section">
        <h2 class="at-section-title">Foundation <span>ground zero to a complete, protected ${esc(type)} service</span></h2>
        <ol class="tp-list">${d.foundation.map((it, i) => apiRow(type, 'Foundation', it, i)).join('')}</ol>
      </section>` : ''}

      ${d.labs.length ? `
      <section class="at-section">
        <h2 class="at-section-title">Labs <span>production topics — Python and Go teach different things, do both</span></h2>
        <ol class="tp-list">${d.labs.map((it, i) => apiRow(type, 'labs', it, i)).join('')}</ol>
      </section>` : ''}

      <nav class="tp-nav" aria-label="Other API styles">
        ${d.prevType ? apiTypeNavCard(d.prevType, 'Previous style', 'prev') : '<span></span>'}
        ${d.nextType ? apiTypeNavCard(d.nextType, 'Next style', 'next') : '<span></span>'}
      </nav>
    </div>`;

  requestAnimationFrame(() => requestAnimationFrame(() => {
    if (!host.isConnected || host.hidden) return;
    host.querySelector('.tpage')?.classList.add('is-in');
    $$('[data-p]', host).forEach(el => el.style.setProperty('--p', el.dataset.p));
  }));
}

/* --------------------------------------------------------- workspace -- *
   Shares #viewProblem with DSA (mode='dsa') and Go/Py Engineering
   (mode='eng') — see app.js's setDsaTabs/setEngTabs for the precedent. */
function setApiTabs() {
  $('#proseTabs').innerHTML = `
    <button class="tab is-on" data-tab="lesson">Lesson</button>
    <button class="tab" data-tab="notes">Notes</button>`;
  curTab = 'lesson';
}

async function loadApiEditor() {
  const key = `api:${curApi.recId}:${curLang}`;
  let d = docCache.get(key);
  if (!d) {
    d = await api(`/api/api-file?type=${encodeURIComponent(curApi.type)}&section=${curApi.section}&level=${curApi.id}&lang=${curLang}`);
    docCache.set(key, d);
  }
  originalCode = d.code || (curLang !== 'go'
    ? '# This level has not been authored in Python yet.\n'
    : 'package main\n\nfunc main() {\n}\n');

  const r = rec(curApi.recId);
  setCode(r.drafts[curLang] ?? originalCode);
  $('#saveDot').textContent = 'saved';
  $('#saveDot').className = 'save-dot';
}

async function loadApiPane(tab) {
  const body = $('#proseBody');

  if (tab === 'notes') {
    const r = rec(curApi.recId);
    body.innerHTML = `
      <div class="notes-wrap">
        <div class="notes-label">
          What you'd want to remember about this level — the <strong>one idea</strong> it teaches,
          or a gotcha that bit you while running it.
        </div>
        <textarea id="notesArea" placeholder="e.g. urllib treats any non-2xx as an exception, that's a urllib quirk not an HTTP rule"></textarea>
      </div>`;
    const ta = $('#notesArea');
    ta.value = r.notes || '';
    let t;
    ta.oninput = () => {
      clearTimeout(t);
      t = setTimeout(() => { r.notes = ta.value; patch(curApi.recId, { notes: r.notes }); }, 600);
    };
    return;
  }

  const key = `api:${curApi.recId}:${curLang}`;
  let d = docCache.get(key);
  if (!d) {
    d = await api(`/api/api-file?type=${encodeURIComponent(curApi.type)}&section=${curApi.section}&level=${curApi.id}&lang=${curLang}`);
    docCache.set(key, d);
  }
  if (!d.exists) {
    body.innerHTML = emptyMsg('Not written yet',
      `This level hasn't been authored in ${curLang === 'py' ? 'Python' : 'Go'} yet.`);
    return;
  }
  await renderEngExplanation(body, d, curLang);
}

async function openApiItem(type, section, id) {
  let d;
  try { d = await apiTypeDetail(type); } catch (e) { d = { exists: false }; }
  if (!d || !d.exists) { location.hash = '#/apis'; return; }
  const ladder = section === 'labs' ? d.labs : d.foundation;
  const item = (ladder || []).find(x => x.id === id);
  if (!item) { location.hash = `#/api-type/${type}`; return; }

  await flushDraft();
  cur = null; curEng = null;
  mode = 'api';
  curModule = 'api';
  curApi = { type, section, id, num: item.num, title: item.title, has: item.has,
             recId: `api/${type}/${section}/${id}` };
  if (!item.has[curLang]) curLang = item.has.py ? 'py' : 'go';

  showView('problem');
  setApiTabs();
  $('#crumb').innerHTML =
    `<a href="#/api-type/${type}">${esc(type)} · ${section === 'labs' ? 'Labs' : 'Foundation'}</a>`;
  $('#problemTitle').innerHTML = `<span class="lc-num">${item.num}</span>${esc(item.title)}`;
  $('#diffPill').hidden = true;
  $('#lcLink').hidden = true;
  $('#langSwitch').hidden = false;
  $$('#langSwitch .lang').forEach(b => b.classList.toggle('is-on', b.dataset.lang === curLang));
  $('#esLang').textContent = curLang === 'py' ? 'Python' : 'Go';
  if (editor) editor.setOption('mode', curLang === 'go' ? 'go' : 'python');
  $('#timer').hidden = false;

  const r = rec(curApi.recId);
  timer.reset(r.timeSpent || 0);
  paintStatus();
  r.lastOpened = Date.now();
  patch(curApi.recId, { lastOpened: r.lastOpened });
  if (r.status === 'todo') {
    r.status = 'attempting'; r.attempts = (r.attempts || 0) + 1;
    patch(curApi.recId, { status: r.status, attempts: r.attempts });
    paintStatus();
  }

  await loadApiEditor();
  await loadApiPane('lesson');
  renderSidebar();
}
