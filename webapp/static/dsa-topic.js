/* ============================================================================
   DSA topic page (#/t/<topicId>) — the level that was missing.

   The DSA home answers "which pattern next?"; the workspace answers "solve
   this one". Between them sat nothing: a topic's 6–25 problems could only be
   reached through the sidebar accordion, which unrolls a dense list under a
   row in a 296px rail. This page is that middle level — one pattern, its
   progress, and every problem in it, laid out to be scanned.

   Reads app.js globals: DATA, rec, isDone, dueList, today, addDays, esc, $,
   $$, dmeter, fmtTime, topicStats — and dsa-home.js's DSA_FAMILIES/dsaFamily.
   ========================================================================= */
'use strict';

let dsaTopicId = null;                       // topic currently shown, for the sidebar
let tpStatus = 'all', tpDiff = 'all', tpSort = 'curriculum';

const TP_STATUS = { all: 'All', todo: 'To do', attempting: 'In progress', solved: 'Solved', mastered: '★' };
const TP_DIFF   = { all: 'Any', Easy: 'Easy', Medium: 'Med', Hard: 'Hard' };
const TP_SORT   = { curriculum: 'Curriculum', unsolved: 'Unsolved', difficulty: 'Easiest' };
const DIFF_RANK = { Easy: 0, Medium: 1, Hard: 2 };

const tpTopic = id => DATA.topics.find(t => t.id === id);

/* "Read the topic guide" — one deep-dive per language. Each button opens that language's guide
   as a reading page (#/dsa-guide/<topic> for Python, #/dsa-guide-go/<topic> for Go); a language
   with no guide for this topic shows as a disabled button instead of vanishing. */
function guideChooser(t) {
  const g = t.guides || {};
  if (!g.py && !g.go) return '';
  const btn = (lang, label, href) => g[lang]
    ? `<a class="tp-guide-btn" data-lang="${lang}" href="${href}"><i aria-hidden="true"></i>${label}</a>`
    : `<span class="tp-guide-btn is-off" data-lang="${lang}" title="No ${label} guide for this topic yet"><i aria-hidden="true"></i>${label}</span>`;
  return `<div class="tp-guide" role="group" aria-label="Topic guide">
    <span class="tp-guide-label">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5.5A2.5 2.5 0 016.5 3H20v16H6.5A2.5 2.5 0 004 21.5zM4 21.5A2.5 2.5 0 016.5 19H20"/></svg>
      Read the topic guide
    </span>
    ${btn('py', 'Python', `#/dsa-guide/${t.id}`)}
    ${btn('go', 'Golang', `#/dsa-guide-go/${t.id}`)}
  </div>`;
}

/* status the row is drawn in — 'missing' is a file that has not been authored */
function tpState(p, r) {
  if (!p.has.pyQuestion) return 'missing';
  return r.status;
}

function tpPasses(p, r) {
  if (tpDiff !== 'all' && p.diff !== tpDiff) return false;
  if (tpStatus === 'todo' && r.status !== 'todo') return false;
  if (tpStatus === 'attempting' && r.status !== 'attempting') return false;
  if (tpStatus === 'solved' && !isDone(r)) return false;
  if (tpStatus === 'mastered' && r.status !== 'mastered') return false;
  return true;
}

/* the review badge on a row: overdue and due-today read as "now" */
function tpDue(r) {
  if (!r.nextReview || r.status === 'mastered') return null;
  const d = daysBetween(today(), r.nextReview);
  if (d <= 0) return { label: 'review due', hot: true };
  if (d <= 2) return { label: `review in ${d}d`, hot: false };
  return null;
}

function renderDsaTopic(id) {
  const host = $('#viewDsaTopic');
  const t = tpTopic(id);
  if (!t) { location.hash = '#/dsa'; return; }
  dsaTopicId = id;

  const items = DATA.problems.filter(p => p.topic === id);
  const recs = new Map(items.map(p => [p.id, rec(p.id)]));
  const done = items.filter(p => isDone(recs.get(p.id))).length;
  const mastered = items.filter(p => recs.get(p.id).status === 'mastered').length;
  const going = items.filter(p => recs.get(p.id).status === 'attempting').length;
  const secs = items.reduce((a, p) => a + (recs.get(p.id).timeSpent || 0), 0);
  const dueNow = items.filter(p => { const d = tpDue(recs.get(p.id)); return d && d.hot; }).length;
  const pct = items.length ? done / items.length * 100 : 0;
  const diff = { Easy: 0, Medium: 0, Hard: 0 };
  items.forEach(p => diff[p.diff]++);
  const fam = dsaFamily(t.num);

  const next = items.find(p => recs.get(p.id).status === 'attempting')
    || items.find(p => !isDone(recs.get(p.id)) && p.has.pyQuestion)
    || items.find(p => !isDone(recs.get(p.id)))
    || items[0];

  const idx = DATA.topics.indexOf(t);
  const prev = DATA.topics[idx - 1], after = DATA.topics[idx + 1];

  let rows = items.filter(p => tpPasses(p, recs.get(p.id)));
  if (tpSort === 'difficulty') {
    rows = [...rows].sort((a, b) => DIFF_RANK[a.diff] - DIFF_RANK[b.diff] || a.seq.localeCompare(b.seq));
  } else if (tpSort === 'unsolved') {
    const rank = p => isDone(recs.get(p.id)) ? 2 : recs.get(p.id).status === 'attempting' ? 0 : 1;
    rows = [...rows].sort((a, b) => rank(a) - rank(b) || a.seq.localeCompare(b.seq));
  }

  const fact = (label, value) => `<div><dt>${label}</dt><dd>${value}</dd></div>`;
  const segment = (name, label, map, active) => `
    <div class="seg" role="group" aria-label="${label}">
      ${Object.entries(map).map(([k, l]) =>
        `<button data-${name}="${k}" class="${active === k ? 'is-on' : ''}" aria-pressed="${active === k}">${l}</button>`).join('')}
    </div>`;

  host.innerHTML = `
    <div class="tpage">
      <nav class="tp-crumb" aria-label="Breadcrumb">
        <a href="#/dsa"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M19 12H5M11 18l-6-6 6-6"/></svg>All patterns</a>
        <span class="tp-crumb-sep" aria-hidden="true">/</span>
        <span class="tp-crumb-fam" data-fam="${fam.key}">${fam.name}</span>
      </nav>

      <header class="tp-hero">
        <div class="tp-hero-copy">
          <p class="tp-eyebrow" data-fam="${fam.key}">Pattern ${t.num} of ${DATA.topics.length}</p>
          <h1 class="tp-title">${esc(t.title)}</h1>
          <p class="tp-tagline">${items.length} problem${items.length === 1 ? '' : 's'} in curriculum order — ${
            ['Easy', 'Medium', 'Hard'].filter(d => diff[d]).map(d => `${diff[d]} ${d.toLowerCase()}`).join(' · ')
          }.</p>

          <div class="tp-mix" role="img" aria-label="${diff.Easy} easy, ${diff.Medium} medium, ${diff.Hard} hard">
            ${['Easy', 'Medium', 'Hard'].filter(d => diff[d]).map(d =>
              `<span class="tp-mix-seg d-${d}" style="flex:${diff[d]}"><em>${diff[d]}</em>${d}</span>`).join('')}
          </div>

          <div class="tp-actions">
            ${next ? `<a class="tp-go" href="#/p/${next.topic}/${next.seq}">
              <span class="tp-go-label">${done === items.length ? 'Re-solve' : going ? 'Continue' : done ? 'Next up' : 'Start here'}</span>
              <span class="tp-go-title">${esc(next.title)}</span>
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
            </a>` : ''}
            ${guideChooser(t)}
            ${dueNow ? `<a class="tp-btn is-hot" href="#/review">${dueNow} to re-solve</a>` : ''}
          </div>
        </div>

        <aside class="tp-gauge" aria-label="Progress in this pattern">
          <span class="tp-ring${pct >= 100 ? ' done' : ''}" style="--p:0" data-p="${pct.toFixed(1)}">
            <b>${done}<span>/${items.length}</span></b>
          </span>
          <dl class="tp-facts">
            ${fact('mastered', mastered)}
            ${fact('in progress', going)}
            ${fact('left', items.length - done)}
            ${fact('time on pattern', secs ? fmtTime(secs).replace(/^0/, '') : '—')}
          </dl>
        </aside>
      </header>

      <div class="tp-toolbar">
        ${segment('status', 'Filter by status', TP_STATUS, tpStatus)}
        ${segment('diff', 'Filter by difficulty', TP_DIFF, tpDiff)}
        <span class="tp-sortlabel">Order</span>${segment('sort', 'Sort order', TP_SORT, tpSort)}
        <span class="tp-shown">${rows.length} of ${items.length} shown</span>
      </div>

      <ol class="tp-list">
        ${rows.map((p, i) => tpRow(p, recs.get(p.id), i)).join('') ||
          `<li class="tp-empty">Nothing in this pattern matches the filter. Set status back to <b>All</b>.</li>`}
      </ol>

      <nav class="tp-nav" aria-label="Other patterns">
        ${prev ? tpNavCard(prev, 'Previous pattern', 'prev') : '<span></span>'}
        ${after ? tpNavCard(after, 'Next pattern', 'next') : '<span></span>'}
      </nav>
    </div>`;

  $$('.tp-toolbar .seg button', host).forEach(b => b.onclick = () => {
    if (b.dataset.status) tpStatus = b.dataset.status;
    else if (b.dataset.diff) tpDiff = b.dataset.diff;
    else if (b.dataset.sort) tpSort = b.dataset.sort;
    renderDsaTopic(id);
  });

  requestAnimationFrame(() => requestAnimationFrame(() => {
    if (!host.isConnected || host.hidden) return;
    host.querySelector('.tpage')?.classList.add('is-in');
    $$('[data-p]', host).forEach(el => el.style.setProperty('--p', el.dataset.p));
  }));
}

function tpRow(p, r, i) {
  const state = tpState(p, r);
  const due = tpDue(r);
  const secs = r.timeSpent || 0;
  return `
    <li style="--i:${i}">
      <a class="tprow st-${state}" href="#/p/${p.topic}/${p.seq}">
        <span class="tprow-seq">${p.seq}</span>
        <span class="tprow-glyph" aria-hidden="true">${state === 'missing' ? '·' : STATUS_GLYPH[r.status]}</span>
        <span class="tprow-main">
          <span class="tprow-title">${esc(p.title)}</span>
          <span class="tprow-tags">
            <span class="tptag mono">LC ${p.lc}</span>
            ${p.has.goQuestion ? '<span class="tptag">Go</span>' : ''}
            ${state === 'missing' ? '<span class="tptag">not written yet</span>' : ''}
            ${due ? `<span class="tptag${due.hot ? ' hot' : ''}">${due.label}</span>` : ''}
            ${r.status === 'mastered' ? '<span class="tptag star">mastered</span>' : ''}
          </span>
        </span>
        <span class="tprow-diff">${dmeter(p.diff)}<em>${p.diff}</em></span>
        <span class="tprow-time">${secs ? fmtTime(secs) : ''}</span>
        <svg class="tprow-chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M9 6l6 6-6 6"/></svg>
      </a>
    </li>`;
}

function tpNavCard(t, label, dir) {
  const st = topicStats(t.id);
  return `
    <a class="tp-navcard ${dir}" href="#/t/${t.id}">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
      <span class="tp-navcard-label">${label}</span>
      <span class="tp-navcard-title">${t.num} · ${esc(t.title)}</span>
      <span class="tp-navcard-meta">${st.done} of ${st.total} solved</span>
    </a>`;
}
