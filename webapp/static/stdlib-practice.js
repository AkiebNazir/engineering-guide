/* ============================================================================
   Py/Go Standard Library — runnable in-browser, level by level.

   PyStdLib/<pkg>/GUIDE.md + level_01..level_10(+dsa_interview).py
   GoStdLib/<pkg>/GUIDE.md + level_01../main.go
   are globbed server-side into one package-per-row list (see server.py
   load_stdlib) already carrying every level, so — unlike API, which needs a
   second request per type — one /api/stdlib?lang= call has everything.

   Shape, same precedent as api-practice.js and dsa-topic.js:

     #/stdlib-pkg/<lang>/<pkg>   "main page of the package" — the GUIDE.md
                                 overview plus every level in order, with
                                 prev/next to the neighbouring package.
     #/stdlib-item/<lang>/<pkg>/<level>
                                 the level itself, in the SAME #viewProblem
                                 workspace DSA/Engineering/API already use
                                 (mode = 'stdlib' alongside 'dsa'|'eng'|'api')
                                 — read the lesson, edit the code, run it for
                                 real output.

   reader.js registers 'pystdlib'/'gostdlib' as ordinary MODULES entries
   (stdlibLang: 'py'|'go') so the sidebar, search and the module-home card
   grid (#/py-stdlib, #/go-stdlib) come for free — itemHref() there already
   points a package card at #/stdlib-pkg/<lang>/<id> instead of the generic
   doc reader.

   Reads/writes app.js globals: DATA, mode, cur, curEng, curApi, curStdlib,
   curLang, curModule, editor, originalCode, docCache, rec, patch, flushDraft,
   showView, timer, paintStatus, renderSidebar, setCode, getCode, esc, $, $$,
   api, post, STATUS_GLYPH, emptyMsg — and reader.js's modItems, stdlibRecId,
   renderEngExplanation, decorateHeadings, enhanceCallouts, wrapTables,
   renderCode.
   ========================================================================= */
'use strict';

let stdlibPkgId = null;   // `${lang}/${pkgId}` currently shown on #viewStdlibPkg, guards races
const stdlibGuideCache = new Map();   // `${lang}:${pkg}` -> /api/stdlib-doc

async function stdlibPackages(lang) {
  return modItems(lang === 'go' ? 'gostdlib' : 'pystdlib');
}
const stdlibPackagesSync = lang => modItemsSync(lang === 'go' ? 'gostdlib' : 'pystdlib');

async function stdlibGuide(lang, pkg) {
  const key = `${lang}:${pkg}`;
  if (!stdlibGuideCache.has(key)) {
    stdlibGuideCache.set(key, api(`/api/stdlib-doc?lang=${lang}&id=${encodeURIComponent(pkg)}`)
      .catch(() => ({ exists: false, markdown: '' })));
  }
  return stdlibGuideCache.get(key);
}

/* ------------------------------------------------------------ package page -- */
function stdlibLevelState(lang, pkg, levelId) {
  const r = DATA.state.problems[stdlibRecId(lang, pkg, levelId)];
  return r ? r.status : 'todo';
}
const stdlibDone = st => st === 'solved' || st === 'mastered';

/* Every package follows the same ten-step shape (GoStdLib/README.md, PyStdLib/
   README.md), so a level's number says what kind of level it is even though
   each package words its own titles. Three bands: get productive, get
   correct, get production-ready. */
const STDLIB_STAGES = {
  1: 'Essentials', 2: 'Core API', 3: 'Idiom', 4: 'Errors', 5: 'Pattern',
  6: 'Measured', 7: 'Lifecycle', 8: 'Interop', 9: 'Gotcha', 10: 'Capstone',
};
const STDLIB_BANDS = [
  { id: 'basic', name: 'Basics', sub: 'the calls you use every day', from: 1, to: 3 },
  { id: 'core', name: 'Core', sub: 'errors, patterns, cost, lifecycle', from: 4, to: 7 },
  { id: 'adv', name: 'Advanced', sub: 'interop, traps, a real program', from: 8, to: 99 },
];
const stdlibBand = lv => lv.kind === 'dsa' ? 'dsa'
  : (STDLIB_BANDS.find(b => lv.num >= b.from && lv.num <= b.to) || STDLIB_BANDS[2]).id;
const stdlibStage = lv => lv.kind === 'dsa' ? 'Interview' : (STDLIB_STAGES[lv.num] || `Level ${lv.num}`);
const stdlibNum = lv => lv.kind === 'dsa' ? '★' : String(lv.num).padStart(2, '0');

/* Turn `Counter(votes)`, `.most_common()`, `sort.Search(n, f)` and `backticked`
   spans in a lesson sentence into <code>, so a bullet reads like documentation
   instead of a wall of plain text. Everything is escaped first. */
function stdlibInline(text) {
  return text.split(/(`[^`]+`)/).map(part => {
    if (part.startsWith('`') && part.endsWith('`') && part.length > 2) return `<code>${esc(part.slice(1, -1))}</code>`;
    return esc(part)
      .replace(/(^|[\s(])(\.?[A-Za-z_][\w.]*\([^()]*\))/g, (m, pre, call) => `${pre}<code>${call}</code>`);
  }).join('');
}

const stdlibStatusLabel = st =>
  st === 'mastered' ? 'Mastered' : st === 'solved' ? 'Solved' : st === 'attempting' ? 'In progress' : '';

function stdlibLevelRow(lang, pkg, lv, i) {
  const st = stdlibLevelState(lang, pkg, lv.id);
  const href = `#/stdlib-item/${lang}/${pkg}/${lv.id}`;
  const label = stdlibStatusLabel(st);
  const headline = lv.blurb || lv.title;
  return `
    <li style="--i:${i}">
      <a class="sp-row st-${st} band-${stdlibBand(lv)}" href="${href}">
        <span class="sp-node" aria-hidden="true">${stdlibDone(st)
          ? '<svg viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>' : `<b>${stdlibNum(lv)}</b>`}</span>
        <span class="sp-body">
          <span class="sp-stage">${stdlibStage(lv)}${lv.blurb ? `<em>${esc(lv.title)}</em>` : ''}</span>
          <span class="sp-title">${stdlibInline(headline)}</span>
        </span>
        ${label ? `<span class="sp-state">${label}</span>` : ''}
        <svg class="sp-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>
      </a>
    </li>`;
}

function stdlibLadder(lang, pkg) {
  let k = 0;
  const bands = [...STDLIB_BANDS, { id: 'dsa', name: 'Interview practice', sub: 'this package under DSA pressure' }];
  return bands.map(b => {
    const lvs = pkg.levels.filter(lv => stdlibBand(lv) === b.id);
    if (!lvs.length) return '';
    const done = lvs.filter(lv => stdlibDone(stdlibLevelState(lang, pkg.id, lv.id))).length;
    return `
      <section class="sp-band band-${b.id}">
        <header class="sp-band-head">
          <h3>${b.name}</h3><span>${b.sub}</span>
          <i class="sp-band-count">${done}/${lvs.length}</i>
        </header>
        <ol class="sp-ladder">${lvs.map(lv => stdlibLevelRow(lang, pkg.id, lv, k++)).join('')}</ol>
      </section>`;
  }).join('');
}

function stdlibPkgNavCard(lang, pkg, label, dir) {
  return `
    <a class="tp-navcard ${dir}" href="#/stdlib-pkg/${lang}/${encodeURIComponent(pkg.id)}">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
      <span class="tp-navcard-label">${label}</span>
      <span class="tp-navcard-title">${esc(pkg.title)}</span>
    </a>`;
}

async function renderStdlibPkg(lang, pkgId) {
  const host = $('#viewStdlibPkg');
  const key = `${lang}/${pkgId}`;
  stdlibPkgId = key;
  host.innerHTML = `<div class="mod-loading">Loading ${esc(pkgId)}…</div>`;

  let items;
  try { items = await stdlibPackages(lang); } catch (e) { items = null; }
  if (stdlibPkgId !== key || host.hidden) return;
  const i = (items || []).findIndex(p => p.id === pkgId);
  const pkg = i >= 0 ? items[i] : null;
  if (!pkg) {
    host.innerHTML = emptyMsg('Not found', `"${esc(pkgId)}" is not a package in the ${lang === 'go' ? 'Go' : 'Python'} standard library curriculum.`);
    return;
  }
  const guide = await stdlibGuide(lang, pkgId).catch(() => ({ exists: false, markdown: '' }));
  if (stdlibPkgId !== key || host.hidden) return;

  const total = pkg.levels.length;
  const done = pkg.levels.filter(lv => stdlibDone(stdlibLevelState(lang, pkgId, lv.id))).length;
  const pct = total ? done / total * 100 : 0;
  const next = pkg.levels.find(lv => stdlibLevelState(lang, pkgId, lv.id) === 'attempting')
    || pkg.levels.find(lv => stdlibLevelState(lang, pkgId, lv.id) === 'todo')
    || pkg.levels[0];
  const langName = lang === 'go' ? 'Go' : 'Python';
  const modHash = lang === 'go' ? 'go-stdlib' : 'py-stdlib';
  const importLine = lang === 'go' ? `import "${pkg.title}"` : `import ${pkg.title}`;
  const tab = host.dataset.tab === 'guide' && guide.exists ? 'guide' : 'levels';

  host.innerHTML = `
    <div class="tpage atpage sp">
      <nav class="tp-crumb" aria-label="Breadcrumb">
        <a href="#/${modHash}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 18l-6-6 6-6"/></svg>${langName} Standard Library</a>
        <span class="tp-crumb-sep" aria-hidden="true">/</span>
        <span>${esc(pkg.title)}</span>
      </nav>

      <header class="tp-hero">
        <div class="tp-hero-copy">
          <p class="tp-eyebrow"><span class="sp-lang">${langName}</span>Package ${+pkg.num} of ${items.length}</p>
          <h1 class="tp-title"><code>${esc(pkg.title)}</code></h1>
          <p class="sp-import"><span>${lang === 'go' ? '' : '>>> '}</span>${esc(importLine)}</p>
          <p class="tp-tagline">${esc(pkg.summary || `${langName}'s ${pkg.title} package, one call at a time.`)}</p>
          <div class="tp-actions">
            ${next ? `<a class="tp-go" href="#/stdlib-item/${lang}/${pkgId}/${next.id}">
              <span class="tp-go-label">${done === total && total ? 'Review from the start' : done ? 'Continue' : 'Start here'}</span>
              <span class="tp-go-title">${stdlibNum(next)} · ${esc(next.blurb || next.title)}</span>
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
            </a>` : ''}
          </div>
        </div>
        <aside class="tp-gauge" aria-label="Progress in this package">
          <span class="tp-ring${pct >= 100 && total ? ' done' : ''}" style="--p:0" data-p="${pct.toFixed(1)}">
            <b>${done}<span>/${total}</span></b>
          </span>
          <dl class="sp-facts">
            <div><dt>levels</dt><dd>${total}</dd></div>
            <div><dt>minutes</dt><dd>${pkg.minutes}</dd></div>
          </dl>
        </aside>
      </header>

      <div class="sp-tabs" role="tablist" aria-label="Package sections">
        <button role="tab" data-tab="levels" aria-selected="${tab === 'levels'}">Levels<i>${total}</i></button>
        ${guide.exists ? `<button role="tab" data-tab="guide" aria-selected="${tab === 'guide'}">Guide<i>gotchas</i></button>` : ''}
      </div>

      <section class="sp-pane" data-pane="levels" ${tab === 'levels' ? '' : 'hidden'}>${stdlibLadder(lang, pkg)}</section>
      ${guide.exists ? `<section class="sp-pane stdlib-guide" data-pane="guide" ${tab === 'guide' ? '' : 'hidden'}>
        <div class="prose doc-prose" id="stdlibGuideProse"></div>
      </section>` : ''}

      <nav class="tp-nav" aria-label="Other packages">
        ${i > 0 ? stdlibPkgNavCard(lang, items[i - 1], 'Previous package', 'prev') : '<span></span>'}
        ${i < items.length - 1 ? stdlibPkgNavCard(lang, items[i + 1], 'Next package', 'next') : '<span></span>'}
      </nav>
    </div>`;

  $$('.sp-tabs button', host).forEach(btn => btn.onclick = () => {
    host.dataset.tab = btn.dataset.tab;
    $$('.sp-tabs button', host).forEach(b => b.setAttribute('aria-selected', String(b === btn)));
    $$('.sp-pane', host).forEach(p => { p.hidden = p.dataset.pane !== btn.dataset.tab; });
  });

  if (guide.exists) {
    const gh = $('#stdlibGuideProse', host);
    gh.innerHTML = marked.parse(guide.markdown);
    // the hero already prints the package name as its own <h1>
    const h1 = gh.firstElementChild;
    if (h1 && h1.tagName === 'H1') h1.remove();
    decorateHeadings(gh, false);
    enhanceCallouts(gh);
    wrapTables(gh);
    await renderCode(gh);
  }

  requestAnimationFrame(() => requestAnimationFrame(() => {
    if (!host.isConnected || host.hidden) return;
    host.querySelector('.tpage')?.classList.add('is-in');
    $$('[data-p]', host).forEach(el => el.style.setProperty('--p', el.dataset.p));
  }));
}

/* --------------------------------------------------------------- workspace -- *
   Shares #viewProblem with DSA (mode='dsa'), Go/Py Engineering (mode='eng')
   and API (mode='api') — see app.js's setDsaTabs/setEngTabs/setApiTabs. */
function setStdlibTabs() {
  $('#proseTabs').innerHTML = `
    <button class="tab is-on" data-tab="lesson">Lesson</button>
    <button class="tab" data-tab="notes">Notes</button>`;
  curTab = 'lesson';
}

async function stdlibFile(lang, pkg, level) {
  const key = `stdlib:${lang}:${pkg}:${level}`;
  let d = docCache.get(key);
  if (!d) {
    d = await api(`/api/stdlib-file?lang=${lang}&pkg=${encodeURIComponent(pkg)}&level=${encodeURIComponent(level)}`);
    docCache.set(key, d);
  }
  return d;
}

async function loadStdlibEditor() {
  const d = await stdlibFile(curStdlib.lang, curStdlib.pkg, curStdlib.level);
  originalCode = d.code || (curStdlib.lang === 'go'
    ? 'package main\n\nfunc main() {\n}\n'
    : '# This level has not been authored yet.\n');

  const r = rec(curStdlib.recId);
  setCode(r.drafts[curStdlib.lang] ?? originalCode);
  $('#saveDot').textContent = 'saved';
  $('#saveDot').className = 'save-dot';
}

async function loadStdlibPane(tab) {
  const body = $('#proseBody');

  if (tab === 'notes') {
    const r = rec(curStdlib.recId);
    body.innerHTML = `
      <div class="notes-wrap">
        <div class="notes-label">
          The <strong>one idea</strong> this level teaches, or a gotcha that surprised you
          when you actually ran it.
        </div>
        <textarea id="notesArea" placeholder="e.g. defaultdict inserts on read — a plain lookup silently grows the dict"></textarea>
      </div>`;
    const ta = $('#notesArea');
    ta.value = r.notes || '';
    let t;
    ta.oninput = () => {
      clearTimeout(t);
      t = setTimeout(() => { r.notes = ta.value; patch(curStdlib.recId, { notes: r.notes }); }, 600);
    };
    return;
  }

  const [d, items] = await Promise.all([
    stdlibFile(curStdlib.lang, curStdlib.pkg, curStdlib.level),
    stdlibPackages(curStdlib.lang).catch(() => []),
  ]);
  if (!d.exists) {
    body.innerHTML = emptyMsg('Not written yet', 'This level has not been authored yet.');
    return;
  }
  const pkg = (items || []).find(p => p.id === curStdlib.pkg);
  renderStdlibLesson(body, d, pkg);
}

/* The lesson is the level file's own opening comment:

     LEVEL 04 (core) - Real exceptions: namedtuple immutability
     You will learn
       * ...
     Run: python level_04_errors.py

   Rather than print that block as prose, lift it into a header, a "you will
   learn" card list and a how-to-work-it strip — and drop the `Run:` line,
   which names a terminal command that means nothing inside the studio. */
function parseStdlibDoc(doc) {
  const lines = doc.replace(/\r/g, '').split('\n');
  const out = { title: '', learn: [], extra: [] };
  let i = 0;
  while (i < lines.length && !lines[i].trim()) i++;
  const hm = /^LEVEL\s+\d+\s*\([^)]*\)\s*[-–—]+\s*(.+)$/.exec((lines[i] || '').trim());
  if (hm) {
    out.title = hm[1];
    i++;
    while (i < lines.length && /^[=\-\s]*$/.test(lines[i])) i++;
  }
  let mode = 'extra';
  for (; i < lines.length; i++) {
    const line = lines[i], t = line.trim();
    if (/^You will learn\b/i.test(t)) { mode = 'learn'; continue; }
    if (/^Run:/i.test(t)) { mode = 'run'; continue; }
    if (mode === 'run') { if (!t) mode = 'extra'; continue; }
    if (mode === 'learn') {
      const bm = /^\s*[*\-•★]\s+(.*)$/.exec(line);
      if (bm) { out.learn.push(bm[1].trim()); continue; }
      if (t && /^\s+/.test(line) && out.learn.length) { out.learn[out.learn.length - 1] += ' ' + t; continue; }
      if (!t) continue;
      mode = 'extra';
    }
    out.extra.push(line);
  }
  return out;
}

function stdlibStepper(lang, pkg) {
  return `<ol class="sl-steps" aria-label="Levels in ${esc(pkg.title)}">${pkg.levels.map(lv => {
    const st = stdlibLevelState(lang, pkg.id, lv.id);
    return `<li><a class="sl-step st-${st} band-${stdlibBand(lv)}${lv.id === curStdlib.level ? ' is-cur' : ''}"
      data-level="${lv.id}" href="#/stdlib-item/${lang}/${pkg.id}/${lv.id}"
      title="${stdlibNum(lv)} · ${esc(lv.blurb || lv.title)}" aria-label="Level ${stdlibNum(lv)}: ${esc(lv.title)}"
      ${lv.id === curStdlib.level ? 'aria-current="step"' : ''}><span>${stdlibNum(lv)}</span></a></li>`;
  }).join('')}</ol>`;
}

function renderStdlibLesson(body, d, pkg) {
  const { lang, level } = curStdlib;
  const parsed = parseStdlibDoc(d.doc || '');
  const levels = pkg ? pkg.levels : [];
  const at = levels.findIndex(lv => lv.id === level);
  const lv = levels[at];
  const prev = at > 0 ? levels[at - 1] : null;
  const next = at >= 0 && at < levels.length - 1 ? levels[at + 1] : null;
  const href = l => `#/stdlib-item/${lang}/${pkg.id}/${l.id}`;
  const langName = lang === 'go' ? 'Go' : 'Python';
  const heading = parsed.title || (lv && lv.blurb) || curStdlib.title;

  const extra = parsed.extra.join('\n').trim();
  body.innerHTML = `
    <article class="sl">
      ${pkg ? stdlibStepper(lang, pkg) : ''}
      <header class="sl-head">
        <p class="sl-meta">
          ${lv ? `<span class="sl-stage band-${stdlibBand(lv)}">${stdlibStage(lv)}</span>` : ''}
          <span>${lv && lv.kind === 'dsa' ? 'Interview practice' : `Level ${curStdlib.num}${levels.length ? ` of ${levels.filter(l => l.kind !== 'dsa').length}` : ''}`}</span>
          ${pkg ? `<a class="sl-pkg" href="#/stdlib-pkg/${lang}/${pkg.id}"><code>${esc(pkg.title)}</code></a>` : ''}
        </p>
        <h2 class="sl-title">${stdlibInline(heading)}</h2>
      </header>

      ${parsed.learn.length ? `<section class="sl-learn">
        <h3>You will learn</h3>
        <ol>${parsed.learn.map(t => `<li><span>${stdlibInline(t)}</span></li>`).join('')}</ol>
      </section>` : ''}

      ${extra ? `<section class="sl-extra prose doc-prose"></section>` : ''}

      <section class="sl-how" aria-label="How to work this level">
        <h3>How to work it</h3>
        <ol>
          <li><b>Read</b> the ${langName} on the right — the comments say what each block proves.</li>
          <li><b>Predict</b> what every check does before you run it.</li>
          <li><b>Run</b> it. A level passes when it exits <code>0</code> and prints <code>OK</code>.</li>
          <li><b>Break it</b> on purpose — change a value, watch which check fails and why.</li>
        </ol>
      </section>

      <nav class="sl-nav" aria-label="Neighbouring levels">
        ${prev ? `<a class="sl-nav-a prev" href="${href(prev)}"><span>Previous</span><b>${stdlibNum(prev)} · ${esc(prev.title)}</b></a>` : '<span></span>'}
        ${next ? `<a class="sl-nav-a next" href="${href(next)}"><span>Next</span><b>${stdlibNum(next)} · ${esc(next.title)}</b></a>`
          : pkg ? `<a class="sl-nav-a next" href="#/stdlib-pkg/${lang}/${pkg.id}"><span>Finished</span><b>Back to ${esc(pkg.title)}</b></a>` : '<span></span>'}
      </nav>
    </article>`;

  if (extra) {
    const host = $('.sl-extra', body);
    host.innerHTML = renderMarkdown(docstringToMarkdown(extra, lang === 'go' ? 'go' : 'python'));
    decorateHeadings(host, false);
    enhanceCallouts(host);
    wrapTables(host);
    renderCode(host);
  }
  const cur = $('.sl-step.is-cur', body);
  if (cur && cur.scrollIntoView) cur.scrollIntoView({ block: 'nearest', inline: 'center' });
}

/* setStatus()/paintStatus() in app.js call this: keep the stepper dots in step
   with the status buttons without rebuilding the pane (and losing scroll). */
function paintStdlibProgress() {
  if (mode !== 'stdlib' || !curStdlib) return;
  $$('#proseBody .sl-step').forEach(a => {
    const st = stdlibLevelState(curStdlib.lang, curStdlib.pkg, a.dataset.level);
    a.className = a.className.replace(/\bst-\w+\b/, `st-${st}`);
  });
}

async function openStdlibItem(lang, pkgId, levelId) {
  let items;
  try { items = await stdlibPackages(lang); } catch (e) { items = null; }
  const pkg = (items || []).find(p => p.id === pkgId);
  const lv = pkg && pkg.levels.find(x => x.id === levelId);
  if (!pkg || !lv) { location.hash = `#/stdlib-pkg/${lang}/${pkgId}`; return; }

  await flushDraft();
  cur = null; curEng = null; curApi = null;
  mode = 'stdlib';
  curModule = lang === 'go' ? 'gostdlib' : 'pystdlib';
  curLang = lang;
  curStdlib = { lang, pkg: pkgId, level: levelId, num: lv.num, title: lv.title,
                recId: stdlibRecId(lang, pkgId, levelId) };

  showView('problem');
  setStdlibTabs();
  $('#crumb').innerHTML = `<a href="#/stdlib-pkg/${lang}/${pkgId}">${esc(pkg.title)}</a>`;
  $('#problemTitle').innerHTML =
    `<span class="lc-num">${lv.kind === 'dsa' ? '★' : String(lv.num).padStart(2, '0')}</span>${esc(lv.title)}`;
  $('#diffPill').hidden = true;
  $('#lcLink').hidden = true;
  $('#langSwitch').hidden = true;
  $('#esLang').textContent = lang === 'go' ? 'Go' : 'Python';
  if (editor) editor.setOption('mode', lang === 'go' ? 'go' : 'python');
  $('#timer').hidden = false;

  const r = rec(curStdlib.recId);
  timer.reset(r.timeSpent || 0);
  paintStatus();
  r.lastOpened = Date.now();
  patch(curStdlib.recId, { lastOpened: r.lastOpened });
  if (r.status === 'todo') {
    r.status = 'attempting'; r.attempts = (r.attempts || 0) + 1;
    patch(curStdlib.recId, { status: r.status, attempts: r.attempts });
    paintStatus();
  }

  await loadStdlibEditor();
  await loadStdlibPane('lesson');
  renderSidebar();
}
