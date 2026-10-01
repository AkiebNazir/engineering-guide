/* ============================================================================
   DSA learning layer — what turns one solved problem into a pattern you own.

     mountQuestionLearn(body, p)   Question tab: a hint ladder climbed one rung
                                   at a time (pattern → move → the file's own
                                   hints or the key idea → the trap), plus a
                                   jump chip at the top of the statement.
     transferCardHTML / mountTransferCard
                                   Solution tab: the move, the trap, the
                                   invariant, and "same move — solve these next".
     playbookHTML / wirePlaybook   Pattern page: signals, look-alikes,
                                   templates, families, pitfalls.

   Data: dsa-patterns.js (PLAYBOOKS, problemFamily, familySiblings) and the
   server's /api/dsa-map (per-problem move / idea / trap from each topic
   guide's problem map, plus statements for the recognition drill).

   Uses app.js globals: DATA, rec, patch, isDone, esc, $, $$, STATUS_GLYPH,
   dmeter, api; problem-doc.js pdInline; reader.js ensureHljs/highlightCode.
   ========================================================================= */
'use strict';

let dsaMapPromise = null;
let dsaMapData = null;
function dsaMap() {
  if (dsaMapData) return Promise.resolve(dsaMapData);
  dsaMapPromise ??= fetch('/api/dsa-map').then(r => r.json()).then(d => (dsaMapData = d.problems || {}))
    .catch(() => { dsaMapPromise = null; return {}; });
  return dsaMapPromise;
}

const learnInline = s => (typeof pdInline === 'function' ? pdInline(String(s || '')) : esc(String(s || '')));
const probById = id => DATA.problems.find(p => p.id === id);

/* a Python code card with a working copy button; highlighted once hljs is in */
function learnCodeHTML(code, title = '') {
  return `<div class="code learn-code">
    <div class="code-head"><span class="code-lang">${title ? esc(title) : 'Python'}</span>
      <button type="button" class="code-copy" data-learn-copy>Copy</button></div>
    <pre><code class="language-python">${esc(code)}</code></pre>
  </div>`;
}
function learnEnhanceCode(root) {
  const blocks = $$('.learn-code code.language-python', root).filter(c => !c.dataset.hl);
  if (blocks.length && typeof ensureHljs === 'function') {
    ensureHljs().then(ok => { if (ok) blocks.forEach(c => { c.dataset.hl = '1'; highlightCode(c, 'python'); }); });
  }
  if (root.dataset.learnWired) return;
  root.dataset.learnWired = '1';
  root.addEventListener('click', e => {
    const btn = e.target.closest('[data-learn-copy]');
    if (!btn) return;
    const code = btn.closest('.code')?.querySelector('code');
    navigator.clipboard?.writeText(code?.textContent || '').then(() => {
      btn.textContent = 'Copied';
      setTimeout(() => { btn.textContent = 'Copy'; }, 1400);
    }).catch(() => { btn.textContent = 'Press ⌘C'; });
  });
}

/* a problem chip: status glyph, title, difficulty — links into the workspace */
function learnChip(id, why = '') {
  const p = probById(id);
  if (!p) return '';
  const r = rec(p.id);
  const pb = playbook(p.topic);
  return `<a class="lchip st-${r.status}" href="#/p/${p.topic}/${p.seq}" title="${esc(why ? `${why} · ` : '')}${esc(p.topicTitle)}">
    <span class="lchip-glyph" aria-hidden="true">${STATUS_GLYPH[r.status] || '○'}</span>
    <span class="lchip-title">${esc(p.title)}</span>
    ${why.includes('other') && pb ? `<span class="lchip-topic">${esc(pb.name)}</span>` : ''}
    <span class="lchip-diff d-${p.diff}">${p.diff[0]}</span>
  </a>`;
}

/* ======================================================= hint ladder ====== */
function ladderRungs(p, m) {
  const pb = playbook(p.topic);
  const fam = problemFamily(p.id);
  const rungs = [];
  if (pb) {
    rungs.push({
      title: 'Recognise the pattern',
      sub: 'Which of these signals is in the statement?',
      html: `<p>This is a <b>${esc(pb.name)}</b> problem — ${esc(pb.tagline.charAt(0).toLowerCase() + pb.tagline.slice(1))}</p>
        <ul class="hl-signals">${pb.signals.map(s => `<li>${learnInline(s)}</li>`).join('')}</ul>
        <a class="hl-link" href="#/t/${p.topic}" data-playbook-tab="recognise">Open the ${esc(pb.name)} playbook</a>`,
    });
  }
  if (fam || (m && m.move)) {
    const tpls = pb ? pb.templates : [];
    rungs.push({
      title: 'Name the move',
      sub: 'The variant of the pattern this problem uses',
      html: `${fam ? `<p><b>${esc(fam.family.name)}</b> — ${learnInline(fam.family.when)}</p>` : ''}
        ${m && m.move ? `<p class="hl-move">The topic guide calls it <code>${esc(m.move)}</code>.</p>` : ''}
        ${tpls.length ? `<details class="hl-tpl"><summary>Show the template${tpls.length > 1 ? 's' : ''} to adapt</summary>
          ${tpls.map(t => learnCodeHTML(t.code, t.title)).join('')}</details>` : ''}`,
    });
  }
  if (m && m.fileHints && m.fileHints.length) {
    m.fileHints.forEach((h, i) => rungs.push({ title: `Hint ${i + 1}`, sub: 'From the problem file', html: h }));
  } else if (m && m.idea) {
    rungs.push({ title: 'The key idea', sub: 'The insight the solution turns on', html: `<p>${learnInline(m.idea)}.</p>` });
  }
  if (m && m.trap) {
    rungs.push({ title: 'The trap', sub: 'The bug the tests are written to catch', html: `<p>${learnInline(m.trap)}</p>`, trap: true });
  }
  return rungs;
}

function ladderHTML(p, rungs, used) {
  const r = rec(p.id);
  const mins = Math.floor((r.timeSpent || 0) / 60);
  const advice = mins >= 40 ? `You are at <b>${mins} min</b>. Past 40 minutes the ladder says: open the solution, then re-solve it cold tomorrow.`
    : mins >= 25 ? `You are at <b>${mins} min</b> — a good moment for the next rung. At 40 min, open the solution.`
    : `You are at <b>${mins} min</b>. The ladder: one rung at 25 min, the solution at 40. Take a rung only when you are truly stuck.`;
  return `
    <header class="hl-head">
      <div><p class="hl-kicker">Stuck? One rung at a time</p><h3>Hint ladder</h3></div>
      <span class="hl-count"><b>${used}</b> of ${rungs.length}</span>
    </header>
    <p class="hl-advice">${advice}</p>
    <ol class="hl-rungs">
      ${rungs.map((g, k) => {
        const state = k < used ? 'is-open' : k === used ? 'is-next' : 'is-locked';
        return `<li class="hl-rung ${state}${g.trap ? ' is-trap' : ''}" data-k="${k}">
          <button type="button" class="hl-rung-head" ${k === used ? 'data-hl-reveal' : ''} ${k > used ? 'disabled' : ''} aria-expanded="${k < used}">
            <span class="hl-num">${k + 1}</span>
            <span class="hl-rung-text"><b>${esc(g.title)}</b><em>${esc(g.sub)}</em></span>
            <span class="hl-rung-act">${k < used ? '' : k === used ? 'Reveal' : '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/></svg>'}</span>
          </button>
          ${k < used ? `<div class="hl-body">${g.html}</div>` : ''}
        </li>`;
      }).join('')}
    </ol>
    ${used ? '<div class="hl-actions"><button type="button" class="hl-hide" data-hl-hide>Hide the hints again</button></div>' : ''}`;
}

async function mountQuestionLearn(body, p) {
  if (!p || typeof playbook !== 'function') return;
  const pd = body.querySelector('.pd');
  if (!pd) return;
  const src = pd.querySelector('.hl-src');
  const fileHints = src ? $$('[data-n]', src).map(el => el.innerHTML) : [];
  const map = await dsaMap();
  if (!body.isConnected || body.querySelector('.hl')) return;
  const m = { ...(map[p.id] || {}), fileHints };
  const rungs = ladderRungs(p, m);
  if (!rungs.length) return;

  const host = document.createElement('section');
  host.className = 'hl';
  host.id = 'hint-ladder';
  if (src) src.replaceWith(host); else pd.append(host);

  const r = rec(p.id);
  const paint = () => {
    const used = Math.min(r.hintsUsed || 0, rungs.length);
    host.innerHTML = ladderHTML(p, rungs, used);
    learnEnhanceCode(host);
    const chip = body.querySelector('.pd-hintjump b');
    if (chip) chip.textContent = `${used}/${rungs.length}`;
  };
  host.addEventListener('click', e => {
    if (e.target.closest('[data-hl-reveal]')) {
      r.hintsUsed = Math.min((r.hintsUsed || 0) + 1, rungs.length);
      patch(p.id, { hintsUsed: r.hintsUsed, lastHintAt: Date.now() });
      paint();
      host.querySelector(`.hl-rung[data-k="${r.hintsUsed - 1}"]`)?.classList.add('just-opened');
    } else if (e.target.closest('[data-hl-hide]')) {
      r.hintsUsed = 0;
      patch(p.id, { hintsUsed: 0 });
      paint();
    } else if (e.target.closest('[data-playbook-tab]')) {
      pbTab = e.target.closest('[data-playbook-tab]').dataset.playbookTab;
    }
  });

  /* the jump chip at the top of the statement */
  const strip = pd.querySelector('.pd-strip');
  if (strip && !strip.querySelector('.pd-hintjump')) {
    strip.insertAdjacentHTML('beforeend', `<button type="button" class="pd-hintjump" title="Jump to the hint ladder">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 18h6M10 22h4M12 2a7 7 0 00-4 12.7V17h8v-2.3A7 7 0 0012 2z"/></svg>
      Hints <b></b></button>`);
    strip.querySelector('.pd-hintjump').onclick = () => host.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  paint();
}

/* ==================================================== transfer card ======= */
function transferCardHTML(p, m) {
  const pb = playbook(p.topic);
  if (!pb) return '';
  const fam = problemFamily(p.id);
  const sibs = familySiblings(p.id);
  const todo = sibs.filter(s => { const q = probById(s.id); return q && !isDone(rec(q.id)); });
  const done = sibs.filter(s => !todo.includes(s));
  const cell = (h, html) => html ? `<div class="xfer-cell"><h4>${h}</h4>${html}</div>` : '';
  return `<section class="xfer" aria-label="Make it transfer">
    <div class="xfer-head">
      <span class="xfer-tag">Make it transfer</span>
      <h3>${esc(pb.name)}${fam ? ` <span aria-hidden="true">→</span> ${esc(fam.family.name)}` : ''}</h3>
      <p>Close the tab on this problem only when you could explain these three lines to someone else.</p>
    </div>
    <div class="xfer-grid">
      ${cell('The move', m && m.idea ? `<p>${m.move ? `<code>${esc(m.move)}</code> — ` : ''}${learnInline(m.idea)}.</p>` : fam ? `<p>${learnInline(fam.family.when)}</p>` : '')}
      ${cell('The trap', m && m.trap ? `<p>${learnInline(m.trap)}</p>` : '')}
      ${cell('The invariant', `<p>${learnInline(pb.invariant)}</p>`)}
    </div>
    ${sibs.length ? `<div class="xfer-next">
      <h4>${todo.length ? 'Same move — solve these next, while it is fresh' : 'Same move — all solved; re-solve one cold'}</h4>
      <div class="lchips">${[...todo, ...done].slice(0, 8).map(s => learnChip(s.id, s.why)).join('')}</div>
    </div>` : ''}
    <p class="xfer-foot">
      <button type="button" class="xfer-notes" data-xfer-notes>Write the trigger in Notes</button>
      <a href="#/t/${p.topic}">${esc(pb.name)} playbook</a>
      <a href="#/dsa-drill">Recognition drill</a>
    </p>
  </section>`;
}

async function mountTransferCard(host, p) {
  if (!host || typeof playbook !== 'function') return;
  const map = await dsaMap();
  if (!host.isConnected) return;
  host.innerHTML = transferCardHTML(p, map[p.id]);
  host.querySelector('[data-xfer-notes]')?.addEventListener('click', () => {
    document.querySelector('#proseTabs .tab[data-tab="notes"]')?.click();
  });
}

/* ========================================================= playbook ======= */
let pbTab = 'recognise';
const PB_TABS = { recognise: 'Recognise', template: 'Template', families: 'Families', pitfalls: 'Pitfalls' };

function playbookHTML(t) {
  const pb = playbook(t.id);
  if (!pb) return '';
  const panes = {
    recognise: `
      <div class="pb-cols">
        <div class="pb-block"><h4>Signals in the statement</h4>
          <ul class="pb-signals">${pb.signals.map(s => `<li>${learnInline(s)}</li>`).join('')}</ul></div>
        <div class="pb-block"><h4>Looks like it, but…</h4>
          <ul class="pb-not">${pb.notThis.map(([a, b]) => `<li><span>${learnInline(a)}</span><b aria-hidden="true">→</b><span>${learnInline(b)}</span></li>`).join('')}</ul></div>
      </div>
      <div class="pb-facts">
        <p><span>Invariant</span><em>${learnInline(pb.invariant)}</em></p>
        <p><span>Cost</span><em>${learnInline(pb.complexity)}</em></p>
      </div>`,
    template: `<p class="pb-lede">Write these from memory before the first problem, then adapt them. Every template here is run against tests.</p>
      <div class="pb-tpls">${pb.templates.map(x => learnCodeHTML(x.code, x.title)).join('')}</div>`,
    families: `<p class="pb-lede">Every problem in this pattern, grouped by the move it shares with its siblings. Solve one family at a time — the second problem in a family is where the move sticks.</p>
      <div class="pb-fams">${pb.families.map((f, i) => {
        const ids = f.seqs.map(s => `${t.id}/${s}`);
        const solved = ids.filter(id => isDone(rec(id))).length;
        return `<article class="pb-fam" style="--i:${i}">
          <header><b>${esc(f.name)}</b><span>${solved}/${ids.length}</span></header>
          <p>${learnInline(f.when)}</p>
          <div class="lchips">${ids.map(id => learnChip(id)).join('')}${(f.also || []).map(id => learnChip(id, 'same move, other pattern')).join('')}</div>
        </article>`;
      }).join('')}</div>`,
    pitfalls: `<ol class="pb-pits">${pb.pitfalls.map(x => `<li>${learnInline(x)}</li>`).join('')}</ol>`,
  };
  if (!PB_TABS[pbTab]) pbTab = 'recognise';
  return `<section class="pb" id="playbook" aria-label="Pattern playbook">
    <header class="pb-head">
      <div><p class="pb-kicker">Pattern playbook</p><h2>${esc(pb.name)}</h2><p class="pb-tag">${esc(pb.tagline)}</p></div>
      <div class="seg pb-tabs" role="tablist">${Object.entries(PB_TABS).map(([k, l]) =>
        `<button type="button" role="tab" data-pbtab="${k}" class="${k === pbTab ? 'is-on' : ''}" aria-selected="${k === pbTab}">${l}</button>`).join('')}</div>
    </header>
    ${Object.entries(panes).map(([k, html]) => `<div class="pb-pane" data-pane="${k}" role="tabpanel" ${k === pbTab ? '' : 'hidden'}>${html}</div>`).join('')}
  </section>`;
}

function wirePlaybook(root) {
  const pb = root.querySelector('.pb');
  if (!pb) return;
  learnEnhanceCode(pb);
  pb.addEventListener('click', e => {
    const b = e.target.closest('[data-pbtab]');
    if (!b) return;
    pbTab = b.dataset.pbtab;
    $$('[data-pbtab]', pb).forEach(x => { x.classList.toggle('is-on', x === b); x.setAttribute('aria-selected', x === b); });
    $$('.pb-pane', pb).forEach(x => { x.hidden = x.dataset.pane !== pbTab; });
    learnEnhanceCode(pb);
  });
}
