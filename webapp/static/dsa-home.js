/* ============================================================================
   DSA home (#/dsa) — the landing page for the problem curriculum.

   The studio dashboard answers "am I on pace for December?". This page answers
   a different question: "which pattern do I work on now?". So the hero is the
   pattern lattice — 28 cells, one per topic, each filled by how much of that
   topic is solved — and everything below it is a way into a specific problem.

   Reads app.js globals: DATA, rec, isDone, dueList, today, streakDays, dmeter,
   esc, $, $$.
   ========================================================================= */
'use strict';

let dsaFilter = 'all';
/* Families group the 28 topics into the shape of the curriculum, so the
   lattice reads as a map even at zero progress instead of 28 blank tiles. */
const DSA_FAMILIES = [
  { upto: 5,  key: 'scan',   name: 'Scanning arrays' },
  { upto: 8,  key: 'linear', name: 'Linear structures' },
  { upto: 13, key: 'tree',   name: 'Trees and heaps' },
  { upto: 15, key: 'graph',  name: 'Graphs' },
  { upto: 18, key: 'dp',     name: 'DP and greedy' },
  { upto: 24, key: 'craft',  name: 'Technique drills' },
  { upto: 99, key: 'design', name: 'Design and advanced' },
];
const dsaFamily = num => DSA_FAMILIES.find(f => +num <= f.upto) || DSA_FAMILIES[DSA_FAMILIES.length - 1];


const DSA_FILTERS = { all: 'All patterns', todo: 'Not started', active: 'In progress', done: 'Complete' };

/* one row per topic: counts, difficulty mix, and the problem to open next */
function dsaRows() {
  return DATA.topics.map(t => {
    const items = DATA.problems.filter(p => p.topic === t.id);
    const recs = items.map(p => rec(p.id));
    const done = items.filter((p, i) => isDone(recs[i])).length;
    const attempting = items.filter((p, i) => recs[i].status === 'attempting').length;
    const mastered = items.filter((p, i) => recs[i].status === 'mastered').length;
    const diff = { Easy: 0, Medium: 0, Hard: 0 };
    items.forEach(p => diff[p.diff]++);
    const next = items.find((p, i) => recs[i].status === 'attempting')
      || items.find((p, i) => !isDone(recs[i]))
      || items[0];
    return {
      t, items, done, attempting, mastered, diff, next, fam: dsaFamily(t.num),
      pct: items.length ? done / items.length * 100 : 0,
      state: !items.length ? 'empty' : done === items.length ? 'done' : done || attempting ? 'active' : 'todo',
    };
  });
}

const dsaPasses = r => dsaFilter === 'all' || r.state === dsaFilter;

/* what "keep going" should open: an overdue review beats an unfinished
   attempt, which beats the first problem you have never opened */
function dsaResume(due) {
  if (due.length) return { p: due[0].p, kicker: 'Review due', action: 'Re-solve cold' };
  const going = DATA.problems.find(p => rec(p.id).status === 'attempting');
  if (going) return { p: going, kicker: 'In progress', action: 'Pick up where you stopped' };
  const fresh = DATA.problems.find(p => rec(p.id).status === 'todo' && p.has.pyQuestion);
  if (fresh) return { p: fresh, kicker: 'Next problem', action: 'Start a focused session' };
  return null;
}

function renderDsaHome() {
  const host = $('#viewDsaHome');
  const rows = dsaRows();
  const total = DATA.problems.length;
  const solved = DATA.problems.filter(p => isDone(rec(p.id))).length;
  const mastered = DATA.problems.filter(p => rec(p.id).status === 'mastered').length;
  const due = dueList().filter(x => x.r.nextReview <= today());
  const streak = streakDays();
  const resume = dsaResume(due);
  const weakest = rows.filter(r => r.items.length && r.pct < 100)
    .sort((a, b) => a.pct - b.pct || b.items.length - a.items.length)[0];
  const shown = rows.filter(dsaPasses);

  const fact = (label, value) => `<div><dt>${label}</dt><dd>${value}</dd></div>`;

  host.innerHTML = `
    <div class="dsa-page">
      <header class="dsa-hero">
        <div class="dsa-hero-copy">
          <p class="dsa-eyebrow">Practice space</p>
          <h1 class="dsa-title">Data structures and algorithms</h1>
          <p class="dsa-tagline">${total} problems, grouped into ${DATA.topics.length} patterns. Work a pattern until the trigger is obvious, then move on — the visualizer tab shows you what each algorithm is doing while you read.</p>
          <dl class="dsa-facts">
            ${fact('problems', total)}
            ${fact('patterns', DATA.topics.length)}
            ${fact('solved', solved)}
            ${fact('mastered', mastered)}
            ${fact('day streak', streak)}
          </dl>
          ${resume ? `
            <a class="dsa-resume" href="#/p/${resume.p.topic}/${resume.p.seq}">
              <span class="dsa-resume-kicker">${resume.kicker}</span>
              <span class="dsa-resume-title">${esc(resume.p.title)}</span>
              <span class="dsa-resume-meta">${esc(resume.p.topicTitle)} · ${resume.p.diff} · ${resume.action}</span>
              <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>
            </a>` : ''}
        </div>

        <div class="dsa-lattice" role="group" aria-label="Progress by pattern">
          ${rows.map((r, i) => `
            <a class="dsa-cell st-${r.state}" style="--p:0; --i:${i}" data-p="${r.pct.toFixed(1)}"
               data-fam="${r.fam.key}"
               href="#/t/${r.t.id}"
               title="${esc(r.t.title)} — ${r.fam.name} — ${r.done} of ${r.items.length} solved">
              <i>${r.t.num}</i>
            </a>`).join('')}
          <ul class="dsa-legend">
            ${DSA_FAMILIES.map(f => `<li data-fam="${f.key}">${f.name}</li>`).join('')}
          </ul>
        </div>
      </header>

      <div class="dsa-rail">
        <a class="dsa-tile${due.length ? ' is-hot' : ''}" href="#/review">
          <span class="dsa-tile-num">${due.length}</span>
          <span class="dsa-tile-label">${due.length === 1 ? 'review due' : 'reviews due'}</span>
          <span class="dsa-tile-foot">${due.length ? 'Cold re-solves keep a pattern earned.' : 'Nothing to re-solve today.'}</span>
        </a>
        ${weakest ? `
          <a class="dsa-tile dsa-tile-wide" href="#/t/${weakest.t.id}">
            <span class="dsa-tile-name">${esc(weakest.t.title)}</span>
            <span class="dsa-tile-label">${solved ? 'thinnest pattern' : 'start here'}</span>
            <span class="dsa-tile-foot">${weakest.items.length - weakest.done} of ${weakest.items.length} still unsolved${weakest.next ? ` · next is ${esc(weakest.next.title)}` : ''}.</span>
          </a>` : ''}
        <a class="dsa-tile" href="#/dashboard">
          <span class="dsa-tile-num">${total - solved}</span>
          <span class="dsa-tile-label">${total - solved === 1 ? 'problem to go' : 'problems to go'}</span>
          <span class="dsa-tile-foot">The dashboard tracks these against your December date.</span>
        </a>
      </div>

      <div class="dsa-toolbar">
        <div class="seg" role="group" aria-label="Filter patterns">
          ${Object.entries(DSA_FILTERS).map(([f, l]) =>
            `<button data-f="${f}" class="${dsaFilter === f ? 'is-on' : ''}" aria-pressed="${dsaFilter === f}">${l}</button>`).join('')}
        </div>
        <span class="dsa-shown">${shown.length} of ${rows.length} patterns</span>
      </div>

      <div class="dsa-grid">
        ${shown.map((r, i) => dsaCard(r, i)).join('') ||
          `<p class="dsa-empty">No pattern is ${DSA_FILTERS[dsaFilter].toLowerCase()} right now. Switch the filter back to all patterns.</p>`}
      </div>
    </div>`;

  $$('.dsa-toolbar .seg button', host).forEach(b => b.onclick = () => {
    dsaFilter = b.dataset.f;
    renderDsaHome();
  });

  /* one orchestrated fill on arrival: rings and cells run from 0 to their real
     value, staggered, instead of every card animating on every hover */
  requestAnimationFrame(() => requestAnimationFrame(() => {
    if (!host.isConnected || host.hidden) return;
    host.querySelector('.dsa-page')?.classList.add('is-in');
    $$('[data-p]', host).forEach(el => { el.style.setProperty('--p', el.dataset.p); });
  }));
}

function dsaCard(r, i) {
  const left = r.items.length - r.done;
  const diffs = ['Easy', 'Medium', 'Hard'].filter(d => r.diff[d]);
  return `
    <a class="dsa-card st-${r.state}" style="--i:${i}" href="#/t/${r.t.id}">
      <span class="dsa-card-num">${r.t.num}</span>
      <h3 class="dsa-card-title">${esc(r.t.title)}</h3>
      <span class="dsa-ring${r.state === 'done' ? ' done' : ''}" style="--p:0" data-p="${r.pct.toFixed(1)}">
        <b>${r.done}<span>/${r.items.length}</span></b>
      </span>
      <div class="dsa-card-diffs">
        ${diffs.map(d => `<span class="dsa-diff">${dmeter(d)}<em>${r.diff[d]}</em></span>`).join('')}
        ${r.mastered ? `<span class="dsa-diff mastered">★<em>${r.mastered}</em></span>` : ''}
      </div>
      <span class="dsa-card-next">
        ${r.state === 'done' ? 'Every problem solved'
          : r.next ? `Next: ${esc(r.next.title)}`
            : 'Nothing authored yet'}
        ${left && r.next ? `<em>${left} left</em>` : ''}
      </span>
    </a>`;
}
