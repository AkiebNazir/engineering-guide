/* ============================================================================
   The visualizer player — one player for every animation in the DSA module.

   Specs come in three shapes (see dsa-viz.js / dsa-viz-dom.js):
     canvas    run() → frames, draw() paints one frame on a canvas
     html      run() → frames, renderDOM() paints one frame as HTML
     dom       buildStates() → states, renderDOM() paints one state
   Before this file there were two players with different controls, and the
   67 "html" specs (most of 2D DP, among others) fell into the canvas player,
   which called a draw() they do not have — a blank box. Now all three share:

     transport     first / prev / play / next / last, a scrubber with ticks at
                   the key moments, step count, speed 0.5×–4×
     narration     what just happened, in words, under the stage, with the
                   line that ran and what it changed ("r: 0 → 1",
                   "stack.append(5)")
     state         every variable the program holds after this step; changed
                   ones lit with their old value, inputs folded away, and a
                   click on a name gives the steps where it changed
     phases        the run split into its phases (expand / shrink, fill /
                   read back…) as a coloured strip under the scrubber
     code          the Python being animated, the running line lit, the line
                   that ran before it marked, and how often each line has run
     story         the beats so far — click one to jump back to it
     predict mode  before each step, the line about to run is shown and the
                   learner picks which variables will change, then reveals it
                   and is scored
     key moments   autoplay stops where the spec marks a moment worth a pause
     motion        HTML stages are patched, not replaced, so CSS transitions
                   animate each change and changed values flash
     theater       hides the editor so the animation gets the whole width
     keyboard      ← → space Home End  P predict  F theater  ? help

   Requires dsa-viz.js (avParts etc.), viz.js (labPalette, D) and app.js
   (esc, $, $$, clamp).
   ========================================================================= */
'use strict';

const VZ_SPEEDS = [0.25, 0.5, 1, 2, 4];
const VZ_PY_KW = /\b(def|return|for|while|if|elif|else|in|not|and|or|None|True|False|class|import|from|lambda|yield|break|continue|pass|with|as|is|nonlocal|global|try|except|raise|del)\b/;

function vzPrefs() {
  try { return JSON.parse(localStorage.getItem('algo-prefs') || '{}'); } catch (e) { return {}; }
}
function vzSavePrefs(p) {
  try { localStorage.setItem('algo-prefs', JSON.stringify(p)); } catch (e) { /* private mode */ }
}

/* `code` in authored prose → <code>; leaves existing HTML alone */
const vzTicks = s => String(s || '').replace(/`([^`<>]+)`/g, '<code>$1</code>');

/* a tiny Python highlighter for the code panel: comments, strings, keywords, numbers */
function vzHighlight(line) {
  const re = /(#.*$)|("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')|\b(def|return|for|while|if|elif|else|in|not|and|or|None|True|False|class|import|from|lambda|yield|break|continue|pass|with|as|is|nonlocal|global|try|except|raise|del)\b|\b(\d+(?:\.\d+)?)\b/g;
  let out = '', last = 0, m;
  while ((m = re.exec(line))) {
    out += esc(line.slice(last, m.index));
    const cls = m[1] ? 'c' : m[2] ? 's' : m[3] ? 'k' : 'n';
    out += `<span class="vz-${cls}">${esc(m[0])}</span>`;
    last = m.index + m[0].length;
  }
  return out + esc(line.slice(last));
}

/* Which convention does a run()-based spec use for frame.line: 0-based
   (the canvas player's original reading) or 1-based (what the HTML specs
   were written against)? Decide once per spec from its own example run. */
function vzLineBase(spec, frames, code) {
  if (spec._lineBase !== undefined) return spec._lineBase;
  const ls = frames.map(f => f.line).filter(l => typeof l === 'number' && l >= 0);
  const blanks = base => ls.filter(l => { const t = code[l - base]; return t === undefined || !t.trim(); }).length;
  let base;
  if (ls.includes(0)) base = 0;
  else if (ls.some(l => l >= code.length)) base = 1;
  else if (blanks(0) !== blanks(1)) base = blanks(0) < blanks(1) ? 0 : 1;
  else base = spec.draw ? 0 : 1;
  spec._lineBase = base;
  return base;
}

/* Patch `target` to match `source` (a detached node holding the new render)
   instead of replacing it, so elements persist between steps and their CSS
   transitions run. Text that changed flashes, when `flash` is on. */
function vzMorph(target, source, flash, budget = { n: 0 }) {
  const tc = [...target.childNodes], sc = [...source.childNodes];
  sc.forEach((s, i) => {
    const t = tc[i];
    if (!t) { target.appendChild(s); return; }
    if (t.nodeType !== s.nodeType || (t.nodeType === 1 && t.tagName !== s.tagName)) { target.replaceChild(s, t); return; }
    if (t.nodeType !== 1) {
      if (t.nodeValue !== s.nodeValue) {
        t.nodeValue = s.nodeValue;
        if (flash && t.nodeType === 3 && s.nodeValue.trim() && t.parentElement) (budget.hits ??= []).push(t.parentElement);
      }
      return;
    }
    if (t.tagName === 'STYLE' || t.tagName === 'svg' || t.tagName === 'SVG') {
      if (t.outerHTML !== s.outerHTML) target.replaceChild(s, t);
      return;
    }
    for (const a of [...t.attributes]) if (!s.hasAttribute(a.name)) t.removeAttribute(a.name);
    for (const a of [...s.attributes]) if (t.getAttribute(a.name) !== a.value) t.setAttribute(a.name, a.value);
    vzMorph(t, s, flash, budget);
  });
  for (let i = tc.length - 1; i >= sc.length; i--) target.removeChild(tc[i]);
  return budget;
}

/* ------------------------------------------------------------------ state --
   Every frame already carries the program's state (pointers, sums, the dp
   table, the stack…), because the stage is drawn from it. The inspector shows
   that state the way the program holds it and what each step changed. It is
   the frame's own fields, minus the ones that only drive the drawing or the
   words, with any authored `vars` laid over them (authored `vars` often list
   only the scalars, while the array being rewritten lives in the frame). */
const VZ_NOT_STATE = new Set(['line', 'note', 'explTitle', 'explText', 'color', 'pause', 'kind', 'phase', 'vars',
  'tone', 'html', 'caption', 'msg', 'message']);

/* JSON with the values JSON drops kept readable: ∞, sets, maps */
const vzSer = v => JSON.stringify(v, (k, x) => (x === Infinity ? '∞' : x === -Infinity ? '-∞' : Number.isNaN(x) ? 'NaN'
  : x === undefined ? null : x instanceof Set ? [...x] : x instanceof Map ? Object.fromEntries(x) : x)) ?? 'null';

function vzStateOf(f) {
  const out = {};
  const take = (k, v) => {
    if (typeof v === 'function' || (typeof v === 'string' && /<\/?[a-z][^>]*>/i.test(v))) return;
    try { out[k] = JSON.parse(vzSer(v)); } catch (e) { /* cyclic: not something a learner can read anyway */ }
  };
  for (const [k, v] of Object.entries(f)) if (!VZ_NOT_STATE.has(k) && k[0] !== '_') take(k, v);
  if (f.vars && typeof f.vars === 'object') for (const [k, v] of Object.entries(f.vars)) take(k, v);
  return out;
}

const vzIsPrim = v => v === null || typeof v !== 'object';
const vzIsRow = v => Array.isArray(v) && v.every(x => vzIsPrim(x));
const vzIsGrid = v => Array.isArray(v) && v.length > 0 && v.every(r => vzIsRow(r) && r.length === v[0].length && r.length > 0);   // a rectangular table
const vzIsMap = v => !!v && typeof v === 'object' && !Array.isArray(v) && Object.values(v).every(x => vzIsPrim(x));

/* a value as Python would print it */
function vzFmt(v, quote) {
  if (v === null || v === undefined) return 'None';
  if (v === true) return 'True';
  if (v === false) return 'False';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : String(+v.toFixed(4));
  const s = String(v);
  if (!quote || s === '∞' || s === '-∞' || s === 'NaN') return s;
  return `'${s.length > 40 ? `${s.slice(0, 40)}…` : s}'`;
}
const vzBrief = v => (vzIsPrim(v) ? vzFmt(v, true) : (s => (s.length > 28 ? `${s.slice(0, 27)}…` : s))(vzSer(v).replace(/"/g, "'").replace(/,/g, ', ')));

/* one value, drawn with what changed since the previous step lit */
function vzShow(v, p, had) {
  const changed = had && vzSer(v) !== vzSer(p);
  if (vzIsPrim(v)) {
    return changed && vzIsPrim(p)
      ? `<s>${esc(vzFmt(p, true))}</s><b class="is-chg">${esc(vzFmt(v, true))}</b>`
      : `<b class="${changed ? 'is-chg' : ''}">${esc(vzFmt(v, true))}</b>`;
  }
  if (vzIsRow(v)) {
    const pr = had && vzIsRow(p) ? p : null, cap = 32;
    const cells = v.slice(0, cap).map((x, i) => `<i class="${pr && (i >= pr.length || pr[i] !== x) ? 'is-chg' : ''}"><sup>${i}</sup>${esc(vzFmt(x))}</i>`).join('');
    return `<span class="vz-cells">${cells || '<em>empty</em>'}${v.length > cap ? `<em>… +${v.length - cap}</em>` : ''}</span><small>len ${v.length}</small>`;
  }
  if (vzIsGrid(v) && v.length <= 12 && Math.max(...v.map(r => r.length)) <= 16) {
    const pr = had && vzIsGrid(p) ? p : null;
    return `<table class="vz-grid"><tbody>${v.map((r, i) => `<tr><th>${i}</th>${r.map((x, j) =>
      `<td class="${pr && (!pr[i] || j >= pr[i].length || pr[i][j] !== x) ? 'is-chg' : ''}">${esc(vzFmt(x))}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  }
  if (vzIsMap(v)) {
    const pm = had && vzIsMap(p) ? p : null, ks = Object.keys(v), cap = 30;
    const gone = pm ? Object.keys(pm).filter(k => !(k in v)) : [];
    const chips = ks.slice(0, cap).map(k => `<i class="${pm && (!(k in pm) || pm[k] !== v[k]) ? 'is-chg' : ''}"><u>${esc(k)}</u>${esc(vzFmt(v[k], true))}</i>`).join('')
      + gone.map(k => `<i class="is-gone" title="removed this step"><u>${esc(k)}</u>${esc(vzFmt(pm[k], true))}</i>`).join('');
    return `<span class="vz-map">${chips || '<em>empty</em>'}${ks.length > cap ? `<em>… +${ks.length - cap}</em>` : ''}</span>`;
  }
  if (Array.isArray(v) && v.length <= 16) {
    // a list of records (call frames, tree nodes, heap pairs): one brief cell per item
    const pr = had && Array.isArray(p) ? p : null;
    const item = x => (x && typeof x === 'object' && !Array.isArray(x) && 'val' in x ? vzFmt(x.val, true) : vzBrief(x));
    const cells = v.map((x, i) => `<i class="${pr && (i >= pr.length || vzSer(pr[i]) !== vzSer(x)) ? 'is-chg' : ''}" title="${esc(vzSer(x).slice(0, 300))}"><sup>${i}</sup>${esc(item(x))}</i>`).join('');
    return `<span class="vz-cells is-rec">${cells || '<em>empty</em>'}</span><small>len ${v.length}</small>`;
  }
  const n = Array.isArray(v) ? v.length : Object.keys(v).length;
  return `<span class="vz-sum${changed ? ' is-chg' : ''}" title="${esc(vzSer(v).slice(0, 400))}">${Array.isArray(v) ? `list of ${n}` : `${n} fields`}</span>`;
}

/* what a step did to one variable, in the words of the code: "r: 0 → 1", "stack.pop() → 5" */
function vzDelta(k, v, p, had, has = true) {
  if (!has) return had ? `${k} cleared` : null;
  if (!had) return `${k} = ${vzBrief(v)}`;
  if (vzSer(v) === vzSer(p)) return null;
  if (vzIsPrim(v) || vzIsPrim(p)) return `${k}: ${vzBrief(p)} → ${vzBrief(v)}`;
  if (Array.isArray(v) && Array.isArray(p)) {
    const S = a => vzSer(a);
    if (v.length === p.length + 1 && S(v.slice(0, -1)) === S(p)) return `${k}.append(${vzBrief(v[v.length - 1])})`;
    if (v.length === p.length + 1 && S(v.slice(1)) === S(p)) return `${k}.appendleft(${vzBrief(v[0])})`;
    if (v.length === p.length - 1 && S(p.slice(0, -1)) === S(v)) return `${k}.pop() → ${vzBrief(p[p.length - 1])}`;
    if (v.length === p.length - 1 && S(p.slice(1)) === S(v)) return `${k}.popleft() → ${vzBrief(p[0])}`;
    if (v.length !== p.length) return `${k}: len ${p.length} → ${v.length}`;
    const cells = [];
    v.forEach((x, i) => {
      if (vzIsRow(x) && vzIsRow(p[i]) && x.length === p[i].length) x.forEach((y, j) => { if (y !== p[i][j]) cells.push(`${k}[${i}][${j}]: ${vzFmt(p[i][j], true)} → ${vzFmt(y, true)}`); });
      else if (S(x) !== S(p[i])) cells.push(`${k}[${i}]: ${vzBrief(p[i])} → ${vzBrief(x)}`);
    });
    return cells.length <= 2 ? cells.join(', ') : `${k}: ${cells.length} cells changed`;
  }
  if (vzIsMap(v) && vzIsMap(p)) {
    const bits = [];
    for (const key of Object.keys(v)) {
      if (!(key in p)) bits.push(`${k}[${vzFmt(key, true)}] = ${vzFmt(v[key], true)}`);
      else if (p[key] !== v[key]) bits.push(`${k}[${vzFmt(key, true)}]: ${vzFmt(p[key], true)} → ${vzFmt(v[key], true)}`);
    }
    for (const key of Object.keys(p)) if (!(key in v)) bits.push(`del ${k}[${vzFmt(key, true)}]`);
    return bits.length <= 3 ? bits.join(', ') : `${k}: ${bits.length} entries changed`;
  }
  return `${k} changed`;
}

/* The phases of a run — the stretch of steps spent expanding vs shrinking a
   window, filling vs reading back a table. Taken from the first frame field
   that splits the run into 2–7 named parts; runs without one get no strip. */
function vzPhases(frames, A) {
  const pretty = s => s.replace(/[_-]+/g, ' ').replace(/^\w/, c => c.toUpperCase());
  for (const get of [f => f.phase, f => f.kind, f => A.title(f)]) {
    const raw = frames.map(f => { const x = get(f); return typeof x === 'string' && x.trim() && x.length <= 40 ? pretty(x.trim()) : null; });
    if (raw.filter(Boolean).length < frames.length * 0.6) continue;
    const labels = raw.map((x, i) => x || raw.slice(0, i).reverse().find(Boolean) || raw.find(Boolean));
    const names = [...new Set(labels)];
    if (names.length < 2 || names.length > 7) continue;
    const runs = [];
    labels.forEach((l, i) => { if (runs.length && runs[runs.length - 1].label === l) runs[runs.length - 1].end = i; else runs.push({ label: l, start: i, end: i }); });
    if (runs.length > 60) continue;           // flickers every step: a strip would be noise
    return { labels, names, runs };
  }
  return null;
}

/* adapters: one per spec shape, all exposing the same small surface */
function vzAdapter(spec) {
  const kind = spec.type === 'dom' ? 'dom' : spec.draw ? 'canvas' : 'html';
  return {
    kind,
    codeLines: variant => (typeof spec.code === 'function' ? spec.code(variant) : spec.code) || [],
    build(input, variant) {
      const data = spec.parse(input);
      return kind === 'dom' ? spec.buildStates(data) : spec.run(data, variant);
    },
    line(step, frames, code) {
      if (typeof step.line !== 'number') return -1;
      if (kind === 'dom') return step.line;                       // 1-based by construction
      return step.line + 1 - vzLineBase(spec, frames, code);      // → 1-based
    },
    tone: step => (kind === 'dom' && step.color && step.color !== 'default' ? step.color : ''),
    title: step => (kind === 'dom' ? step.explTitle || '' : ''),
    text: step => (kind === 'dom' ? esc(step.explText || '') : step.note || ''),
    pause: step => !!(kind === 'dom' && step.pause),
    interval: () => (kind === 'dom' ? spec.speedMs || 750 : 850),
  };
}

function renderVizPlayer(body, list, topicId, startK, loadAlgo) {
  const prefs = vzPrefs();
  const spec = list[startK];
  const A = vzAdapter(spec);
  const st = {
    frames: [], i: 0, variant: spec.variants ? spec.variants[0][0] : null,
    playing: false, timer: 0, predicting: false, beats: [], maxH: 0, code: [],
    states: [], fixed: new Set(), keys: [], phases: null, lines: [],
    hist: null, guess: new Set(), verdict: null, score: { n: 0, ok: 0 },
    speed: VZ_SPEEDS.includes(prefs.speed) ? prefs.speed : 1,
    stops: prefs.stops !== false, predict: !!prefs.predict,
  };
  const embedded = topicId === '__solution__';
  const multiline = String(spec.input || '').includes('\n');       // a grid / board: a single-line field would drop the rows
  const svg = d => `<svg viewBox="0 0 24 24" aria-hidden="true">${d}</svg>`;
  const I = {
    first: svg('<path d="M6 5v14M18 6l-9 6 9 6z"/>'),
    prev: svg('<path d="M15 6l-7 6 7 6"/>'),
    next: svg('<path d="M9 6l7 6-7 6"/>'),
    last: svg('<path d="M18 5v14M6 6l9 6-9 6z"/>'),
    play: '<svg class="is-solid" viewBox="0 0 24 24" aria-hidden="true"><path d="M7 5l12 7-12 7z"/></svg>',
    pause: svg('<path d="M8 5v14M16 5v14"/>'),
    replay: svg('<path d="M4 12a8 8 0 108-8H8M8 1v6h6" transform="translate(0 1)"/>'),
    theater: svg('<path d="M4 9V5h4M20 9V5h-4M4 15v4h4M20 15v4h-4"/>'),
    keys: svg('<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10h.01M11 10h.01M15 10h.01M8 14h8"/>'),
    brain: svg('<path d="M12 4a3 3 0 00-3 3 3 3 0 00-3 3 3 3 0 001 5 3 3 0 005 3V4zM12 4a3 3 0 013 3 3 3 0 013 3 3 3 0 01-1 5 3 3 0 01-5 3"/>'),
  };

  body.innerHTML = `
  <div class="vz" tabindex="-1" data-kind="${A.kind}">
    <div class="vz-head">
      <div class="vz-titles"><p class="vz-kicker">Step-by-step visualizer</p><h3 class="vz-title">${esc(spec.title)}</h3></div>
      <div class="vz-head-acts">
        ${list.length > 1 ? `<div class="seg vz-pick">${list.map((a, i) => `<button type="button" data-pick="${i}" class="${i === startK ? 'is-on' : ''}">${esc(a.short || a.title)}</button>`).join('')}</div>` : ''}
        <button type="button" class="vz-icon" data-a="theater" title="Theater mode — hide the editor (F)" aria-pressed="false">${I.theater}<span>Theater</span></button>
        <button type="button" class="vz-icon" data-a="keys" title="Keyboard shortcuts (?)" aria-expanded="false">${I.keys}</button>
      </div>
    </div>
    <div class="vz-keys" hidden>
      <span><kbd>←</kbd><kbd>→</kbd> step</span><span><kbd>Space</kbd> play / pause</span>
      <span><kbd>Home</kbd><kbd>End</kbd> first / last</span><span><kbd>P</kbd> predict mode</span>
      <span><kbd>F</kbd> theater</span><span>Click a story beat to jump to it</span>
    </div>
    <p class="vz-idea">${vzTicks(spec.idea)}</p>
    ${spec.variants ? `<div class="seg vz-variants">${spec.variants.map(([v, l]) => `<button type="button" data-variant="${v}" class="${v === st.variant ? 'is-on' : ''}">${esc(l)}</button>`).join('')}</div>` : ''}

    <div class="vz-stage">${A.kind === 'canvas' ? '<canvas></canvas>' : '<div class="dom-algo vz-dom"></div>'}</div>

    <div class="vz-narr" aria-live="polite">
      <div class="vz-narr-top"><span class="vz-narr-step"></span><span class="vz-phase-chip" hidden></span><b class="vz-narr-title"></b></div>
      <p class="vz-narr-text"></p>
      <div class="vz-now" hidden><span class="vz-tag">Ran</span><span class="vz-now-line"></span><code class="vz-now-code"></code></div>
      <div class="vz-diff" hidden><span class="vz-tag">Changed</span><span class="vz-diff-list"></span></div>
      <div class="vz-verdict" hidden></div>
    </div>
    <div class="vz-predict" hidden>
      <span class="vz-predict-tag">${I.brain}Predict</span>
      <div class="vz-predict-body">
        <p>Line <b class="vz-pline"></b> runs next: <code class="vz-pcode"></code></p>
        <p class="vz-guess-ask">Which variables will it change? Tick them, then reveal.</p>
        <div class="vz-guess"></div>
      </div>
      <button type="button" class="vz-reveal" data-a="reveal">Reveal <kbd>→</kbd></button>
    </div>

    <div class="vz-transport">
      <div class="vz-btns">
        <button type="button" class="vz-btn" data-a="first" title="First step (Home)" aria-label="First step">${I.first}</button>
        <button type="button" class="vz-btn" data-a="prev" title="Previous step (←)" aria-label="Previous step">${I.prev}</button>
        <button type="button" class="vz-btn vz-play" data-a="play" title="Play / pause (Space)"></button>
        <button type="button" class="vz-btn" data-a="next" title="Next step (→)" aria-label="Next step">${I.next}</button>
        <button type="button" class="vz-btn" data-a="last" title="Last step (End)" aria-label="Last step">${I.last}</button>
      </div>
      <div class="vz-track">
        <div class="vz-phasebar"></div><div class="vz-fill"></div><div class="vz-ticks"></div>
        <input type="range" class="vz-scrub" min="0" max="0" value="0" aria-label="Step">
      </div>
      <span class="vz-count"></span>
      <div class="seg vz-speed" role="group" aria-label="Speed">${VZ_SPEEDS.map(v => `<button type="button" data-speed="${v}">${v}×</button>`).join('')}</div>
      <div class="vz-opts">
        <label class="vz-opt" title="Autoplay stops at the moments worth a pause"><input type="checkbox" data-opt="stops"><span>Stop at key moments</span></label>
        <label class="vz-opt" title="Guess each step before you see it (P)"><input type="checkbox" data-opt="predict"><span>Predict mode</span></label>
      </div>
      <div class="vz-phase-legend" hidden></div>
    </div>

    <div class="vz-lower">
      <section class="vz-panel vz-state-panel" hidden>
        <h4>State after this step <span>lit = changed by this step · click a name for its history</span></h4>
        <div class="vz-state"></div>
        <div class="vz-hist" hidden></div>
        <div class="vz-fixed" hidden></div>
      </section>
      <section class="vz-panel vz-code-panel"><h4>Code <span class="vz-lineinfo"></span></h4><ol class="vz-code"></ol></section>
      <section class="vz-panel vz-story-panel"><h4>Story so far <span>click a beat to jump</span></h4><ol class="vz-story"></ol></section>
    </div>

    <div class="vz-input">
      <label><span>Try your own input${multiline ? ' <em>(⌘/Ctrl + Enter runs it)</em>' : ''}</span>${multiline
        ? `<textarea rows="${Math.min(10, String(spec.input).split('\n').length)}" spellcheck="false"></textarea>`
        : '<input type="text" spellcheck="false" autocomplete="off">'}</label>
      <button type="button" class="btn btn-primary" data-a="run">Run</button>
      <button type="button" class="btn btn-ghost" data-a="example">Example</button>
      <span class="vz-hint"></span>
      <span class="vz-err" role="alert"></span>
    </div>
    <p class="vz-cx">${spec.complexity ? esc(spec.complexity) : ''}</p>
  </div>`;

  const root = $('.vz', body);
  const stage = $('.vz-stage', root);
  const cv = $('canvas', stage), ctx = cv ? cv.getContext('2d') : null;
  const dom = $('.vz-dom', stage);
  const input = $('.vz-input input, .vz-input textarea', root), scrub = $('.vz-scrub', root);
  input.value = spec.input;
  $('.vz-hint', root).textContent = spec.hint ? `Format: ${spec.hint}` : '';

  /* ---------------------------------------------------------- building -- */
  function buildBeats() {
    // DOM specs carry titled beats; frames from run() have only notes, so every
    // change of note is its own beat
    const beats = [];
    st.frames.forEach((f, i) => {
      const key = A.kind === 'dom' ? A.title(f) : String(A.text(f)).replace(/<[^>]+>/g, '');
      if (!beats.length || beats[beats.length - 1].key !== key) beats.push({ key, start: i, end: i, pause: A.pause(f) });
      else { beats[beats.length - 1].end = i; if (A.pause(f)) beats[beats.length - 1].pause = true; }
    });
    st.beats = beats;
  }
  function buildState() {
    st.states = st.frames.map(f => vzStateOf(f));
    const keys = [];
    st.states.forEach(s => Object.keys(s).forEach(k => { if (!keys.includes(k)) keys.push(k); }));
    // present and identical on every step: the inputs, folded away under the live state
    st.fixed = new Set(st.frames.length < 2 ? [] : keys.filter(k => {
      const first = k in st.states[0] ? vzSer(st.states[0][k]) : null;
      return first !== null && st.states.every(s => k in s && vzSer(s[k]) === first);
    }));
    st.keys = keys;
    if (st.hist && !keys.includes(st.hist)) st.hist = null;
    st.guess.clear();
    st.verdict = null;
    st.score = { n: 0, ok: 0 };
    $('.vz-state-panel', root).hidden = !keys.length;

    st.phases = vzPhases(st.frames, A);
    const n = st.frames.length, P = st.phases;
    const color = l => `var(--series-${P.names.indexOf(l) % 8})`;
    $('.vz-phasebar', root).innerHTML = P ? P.runs.map(r =>
      `<i style="left:${(r.start / n) * 100}%;width:${((r.end - r.start + 1) / n) * 100}%;background:${color(r.label)}" title="${esc(r.label)} · steps ${r.start + 1}–${r.end + 1}"></i>`).join('') : '';
    root.classList.toggle('has-phases', !!P);
    const legend = $('.vz-phase-legend', root);
    legend.hidden = !P;
    legend.innerHTML = P ? `<span class="vz-tag">Phases</span>${P.names.map(l =>
      `<button type="button" data-phase="${esc(l)}" title="Jump to the next “${esc(l)}” step"><i style="background:${color(l)}"></i>${esc(l)}</button>`).join('')}` : '';
  }
  /* which variables did the step into frame i change? */
  function changedAt(i) {
    if (i <= 0) return [];
    const a = st.states[i - 1], b = st.states[i];
    return st.keys.filter(k => !st.fixed.has(k) && vzSer(a[k]) !== vzSer(b[k]));
  }
  function run() {
    stop();
    try {
      st.frames = A.build(input.value, st.variant) || [];
      if (!st.frames.length) throw new Error('Nothing to show for this input');
      $('.vz-err', root).textContent = '';
    } catch (e) {
      $('.vz-err', root).textContent = e.message;
      return;
    }
    st.code = A.codeLines(st.variant);
    $('.vz-code', root).innerHTML = st.code.map((ln, i) => `<li data-l="${i + 1}"><i>${i + 1}</i><span>${vzHighlight(ln) || ' '}</span><em class="vz-hits"></em></li>`).join('');
    st.lines = st.frames.map(f => A.line(f, st.frames, st.code));
    buildBeats();
    buildState();
    scrub.max = st.frames.length - 1;
    // ticks: the key moments (DOM pauses), else beat starts when there are few enough to read
    const marks = st.frames.map((f, i) => (A.pause(f) ? i : -1)).filter(i => i > 0);
    const ticks = marks.length ? marks : (A.kind === 'dom' && st.beats.length <= 30 ? st.beats.slice(1).map(b => b.start) : []);
    const span = Math.max(1, st.frames.length - 1);
    $('.vz-ticks', root).innerHTML = ticks.map(i => `<i style="left:${(i / span) * 100}%" data-tick="${i}" title="Step ${i + 1}"></i>`).join('');
    st.maxH = 0;
    stage.style.minHeight = '';
    if (dom) dom.innerHTML = '';
    st.predicting = false;
    go(0, false);
  }

  /* ---------------------------------------------------------- painting -- */
  function paintStage(flash) {
    const f = st.frames[st.i];
    if (A.kind === 'canvas') return drawCanvas();
    const scratch = document.createElement('div');
    try { spec.renderDOM(scratch, f, spec); } catch (e) { console.error(e); return; }
    const res = vzMorph(dom, scratch, flash);
    const hits = res.hits || [];
    if (flash && hits.length && hits.length <= 14) hits.forEach(el => { el.classList.remove('vz-flash'); void el.offsetWidth; el.classList.add('vz-flash'); });
    // hold the tallest height seen so the controls do not jump between steps
    const h = dom.offsetHeight;
    if (h > st.maxH) { st.maxH = h; stage.style.minHeight = `${h}px`; }
  }
  function drawCanvas() {
    if (!root.isConnected) return;
    const f = st.frames[st.i];
    const w = Math.max(280, stage.clientWidth || 600);
    const h = Math.round(spec.height ? spec.height(w, st.frames[st.frames.length - 1], st.frames) : 260);
    const d = window.devicePixelRatio || 1;
    if (cv.width !== Math.round(w * d) || cv.height !== Math.round(h * d)) { cv.width = Math.round(w * d); cv.height = Math.round(h * d); cv.style.height = `${h}px`; }
    ctx.setTransform(d, 0, 0, d, 0, 0);
    ctx.clearRect(0, 0, w, h);
    try { spec.draw(ctx, { w, h }, f, labPalette(root), st.frames); } catch (e) { console.error(e); }
  }
  function paintCode() {
    const f = st.frames[st.i];
    const line = A.line(f, st.frames, st.code);
    const nextF = st.predicting ? st.frames[st.i + 1] : null;
    const nextLine = nextF ? A.line(nextF, st.frames, st.code) : -1;
    const tone = A.tone(f);
    // how often each line has run up to here — loops show up as counts
    const hits = {};
    for (let k = 0; k <= st.i; k++) if (st.lines[k] > 0) hits[st.lines[k]] = (hits[st.lines[k]] || 0) + 1;
    const prevLine = !st.predicting && st.i > 0 ? st.lines[st.i - 1] : -1;
    $$('.vz-code li', root).forEach(li => {
      const l = +li.dataset.l;
      li.className = l === line && !st.predicting ? `is-on${tone ? ` t-${tone}` : ''}` : l === nextLine ? 'is-next' : l === line ? 'is-was'
        : l === prevLine ? 'is-prev' : '';
      const em = li.lastElementChild;
      em.textContent = hits[l] ? `×${hits[l]}` : '';
      em.title = hits[l] ? `Ran ${hits[l]} time${hits[l] === 1 ? '' : 's'} up to this step` : '';
    });
    $('.vz-lineinfo', root).textContent = line > 0 ? `line ${line} · run ${hits[line] || 0}× so far` : '';
    const lit = $('.vz-code li.is-on, .vz-code li.is-next', root);
    const box = $('.vz-code', root);
    if (lit && (lit.offsetTop < box.scrollTop || lit.offsetTop > box.scrollTop + box.clientHeight - 28)) box.scrollTop = lit.offsetTop - 40;
  }
  function paintStory() {
    const cur = st.beats.findIndex(b => st.i >= b.start && st.i <= b.end);
    const from = Math.max(0, cur - 7);
    $('.vz-story', root).innerHTML = st.beats.slice(from, cur + 1).map((b, k) => {
      const idx = from + k;
      const label = A.kind === 'dom' ? b.key : b.key;
      return `<li class="${idx === cur ? 'is-cur' : ''}${b.pause ? ' is-key' : ''}"><button type="button" data-beat="${b.start}">
        <span class="vz-beat-n">${b.start + 1}</span><span class="vz-beat-t">${esc(label || '—')}</span></button></li>`;
    }).join('') + (cur < st.beats.length - 1 ? `<li class="vz-story-more">${st.beats.length - 1 - cur} more beat${st.beats.length - 1 - cur === 1 ? '' : 's'} ahead</li>` : '<li class="vz-story-more is-end">End of the run</li>');
    const box = $('.vz-story', root);
    box.scrollTop = box.scrollHeight;
  }
  function paintState() {
    if (!st.keys.length) return;
    const cur = st.states[st.i], prev = st.i > 0 ? st.states[st.i - 1] : null;
    const row = (k, live) => {
      const had = !!prev && k in prev;
      const chg = live && had && vzSer(cur[k]) !== vzSer(prev[k]);
      const fresh = live && !!prev && !had;
      return `<div class="vz-row${chg ? ' is-chg' : ''}${fresh ? ' is-new' : ''}${st.hist === k ? ' is-hist' : ''}">
        <button type="button" class="vz-name" data-hist="${esc(k)}" title="When did ${esc(k)} change?">${esc(k)}${fresh ? '<sup>new</sup>' : ''}</button>
        <div class="vz-val">${vzShow(cur[k], live && prev ? prev[k] : undefined, live && had)}</div></div>`;
    };
    const live = st.keys.filter(k => !st.fixed.has(k) && k in cur);
    const gone = prev ? st.keys.filter(k => !st.fixed.has(k) && k in prev && !(k in cur)) : [];
    $('.vz-state', root).innerHTML = live.map(k => row(k, true)).join('')
      + gone.map(k => `<div class="vz-row is-gone"><span class="vz-name">${esc(k)}</span><div class="vz-val"><em>out of scope after this step</em></div></div>`).join('')
      || '<p class="vz-state-empty">Nothing but the inputs yet.</p>';
    // keep the first changed variable in view inside the panel, without moving the page
    const box = $('.vz-state', root), hot = $('.vz-row.is-chg, .vz-row.is-new', box);
    if (hot && (hot.offsetTop < box.scrollTop || hot.offsetTop + hot.offsetHeight > box.scrollTop + box.clientHeight)) box.scrollTop = hot.offsetTop - 8;
    const fixed = st.keys.filter(k => st.fixed.has(k));
    const fx = $('.vz-fixed', root);
    fx.hidden = !fixed.length;
    fx.innerHTML = fixed.length ? `<p class="vz-fixed-head">Inputs — the same on every step</p>${fixed.map(k => row(k, false)).join('')}` : '';

    // the history of one variable: the steps where it took a new value
    const h = $('.vz-hist', root);
    h.hidden = !st.hist;
    if (!st.hist) return;
    const k = st.hist, pts = [];
    let last;
    st.states.forEach((s, i) => { const x = k in s ? vzSer(s[k]) : '∅'; if (x !== last) { pts.push(i); last = x; } });
    const curPt = pts.filter(i => i <= st.i).pop();
    const shown = pts.length > 80 ? pts.filter(i => Math.abs(pts.indexOf(i) - pts.indexOf(curPt)) < 40) : pts;
    h.innerHTML = `<p><b>${esc(k)}</b> took ${pts.length} value${pts.length === 1 ? '' : 's'} over ${st.frames.length} steps
      ${st.fixed.has(k) ? '— it never changes' : '— click one to jump there'}<button type="button" class="vz-hist-x" data-hist="${esc(k)}" aria-label="Close history">×</button></p>
      <ol>${shown.map(i => `<li><button type="button" data-jump="${i}" class="${i === curPt ? 'is-cur' : ''}${i > st.i ? ' is-future' : ''}">
        <span>step ${i + 1}</span><b>${esc(k in st.states[i] ? vzBrief(st.states[i][k]) : '—')}</b></button></li>`).join('')}</ol>`;
  }
  function paintChrome() {
    const f = st.frames[st.i], n = st.frames.length;
    $('.vz-narr-step', root).textContent = `Step ${st.i + 1} of ${n}`;
    const title = A.title(f);
    $('.vz-narr-title', root).textContent = title;
    $('.vz-narr-title', root).hidden = !title;
    const chip = $('.vz-phase-chip', root), ph = st.phases ? st.phases.labels[st.i] : '';
    chip.hidden = !ph || ph === title;
    chip.textContent = ph || '';
    if (ph) chip.style.setProperty('--ph', `var(--series-${st.phases.names.indexOf(ph) % 8})`);
    $$('.vz-phase-legend button', root).forEach(b => b.classList.toggle('is-on', b.dataset.phase === ph));
    $('.vz-narr-text', root).innerHTML = vzTicks(A.text(f));
    // the line that just ran, so the stage and the code can be read together
    const line = st.lines[st.i];
    $('.vz-now', root).hidden = !(line > 0 && st.code[line - 1]);
    if (line > 0) {
      $('.vz-now-line', root).textContent = `line ${line}`;
      $('.vz-now-code', root).textContent = (st.code[line - 1] || '').trim();
    }
    // what that line did to the state
    const diff = $('.vz-diff', root);
    diff.hidden = !st.keys.length;
    if (st.keys.length) {
      const prev = st.states[st.i - 1], cur = st.states[st.i];
      const ds = st.i === 0 ? [] : changedAt(st.i).map(k => vzDelta(k, cur[k], prev[k], k in prev, k in cur)).filter(Boolean);
      $('.vz-diff-list', root).innerHTML = st.i === 0
        ? '<em>the starting state — see it below</em>'
        : ds.length ? ds.slice(0, 5).map(d => `<code>${esc(d)}</code>`).join('') + (ds.length > 5 ? `<em>+${ds.length - 5} more</em>` : '')
          : '<em>nothing — this step reads or compares, it does not write</em>';
    }
    const v = $('.vz-verdict', root), vd = st.verdict && st.verdict.at === st.i ? st.verdict : null;
    v.hidden = !vd;
    if (vd) {
      const list = ks => ks.map(k => `<code>${esc(k)}</code>`).join(' ');
      v.className = `vz-verdict ${vd.ok ? 'is-ok' : 'is-miss'}`;
      v.innerHTML = `<b>${vd.ok ? 'Right.' : 'Not quite.'}</b> ${vd.actual.length ? `This step changed ${list(vd.actual)}.` : 'This step changed nothing.'}`
        + (vd.missed.length ? ` You missed ${list(vd.missed)}.` : '') + (vd.wrong.length ? ` ${list(vd.wrong)} stayed the same.` : '')
        + ` <span class="vz-score">Score ${st.score.ok}/${st.score.n}</span>`;
    }
    $('.vz-narr', root).classList.toggle('is-key', A.pause(f));
    $('.vz-count', root).textContent = `${st.i + 1} / ${n}`;
    scrub.value = st.i;
    $('.vz-fill', root).style.width = `${n > 1 ? (st.i / (n - 1)) * 100 : 100}%`;
    const play = $('[data-a="play"]', root);
    const atEnd = st.i >= n - 1;
    play.innerHTML = st.playing ? `${I.pause}<span>Pause</span>` : atEnd ? `${I.replay}<span>Replay</span>` : `${I.play}<span>Play</span>`;
    $('[data-a="prev"]', root).disabled = st.i === 0;
    $('[data-a="first"]', root).disabled = st.i === 0;
    $('[data-a="next"]', root).disabled = atEnd;
    $('[data-a="last"]', root).disabled = atEnd;
    const pr = $('.vz-predict', root);
    pr.hidden = !st.predicting;
    if (st.predicting) {
      const nf = st.frames[st.i + 1];
      const nl = A.line(nf, st.frames, st.code);
      $('.vz-pline', root).textContent = nl > 0 ? nl : '—';
      $('.vz-pcode', root).textContent = nl > 0 ? (st.code[nl - 1] || '').trim() : '(no line change)';
      const live = st.keys.filter(k => !st.fixed.has(k)).slice(0, 14);
      $('.vz-guess-ask', root).hidden = !live.length;
      $('.vz-guess', root).innerHTML = live.map(k =>
        `<button type="button" data-guess="${esc(k)}" aria-pressed="${st.guess.has(k)}" class="${st.guess.has(k) ? 'is-on' : ''}">${esc(k)}</button>`).join('')
        + (live.length ? `<button type="button" data-guess="" class="vz-guess-none${st.guess.size ? '' : ' is-on'}">nothing</button>` : '');
    }
    $$('[data-speed]', root).forEach(b => b.classList.toggle('is-on', +b.dataset.speed === st.speed));
    $('[data-opt="stops"]', root).checked = st.stops;
    $('[data-opt="predict"]', root).checked = st.predict;
  }
  function go(i, flash = false) {
    st.i = clamp(i, 0, st.frames.length - 1);
    paintStage(flash);
    paintCode();
    paintStory();
    paintState();
    paintChrome();
  }

  /* ---------------------------------------------------------- stepping -- */
  function stepForward() {
    if (st.i >= st.frames.length - 1) return;
    if (st.predict && !st.predicting) { st.predicting = true; paintCode(); paintChrome(); return; }
    if (st.predicting && st.keys.length) {
      // score the guess against what the step really changed
      const actual = changedAt(st.i + 1);
      const missed = actual.filter(k => !st.guess.has(k)), wrong = [...st.guess].filter(k => !actual.includes(k));
      const ok = !missed.length && !wrong.length;
      st.score.n++;
      if (ok) st.score.ok++;
      st.verdict = { at: st.i + 1, actual, missed, wrong, ok };
      st.guess.clear();
    }
    st.predicting = false;
    go(st.i + 1, true);
  }
  function stepBack() {
    if (st.predicting) { st.predicting = false; paintCode(); paintChrome(); return; }
    go(st.i - 1);
  }
  function tick() {
    if (!st.playing || !root.isConnected) { st.playing = false; return; }
    if (st.i >= st.frames.length - 1) { stop(); return; }
    go(st.i + 1, true);
    if (st.stops && A.pause(st.frames[st.i])) { stop(); return; }
    st.timer = setTimeout(tick, A.interval() / st.speed);
  }
  function play() {
    st.predicting = false;
    if (st.i >= st.frames.length - 1) go(0);
    st.playing = true;
    paintChrome();
    st.timer = setTimeout(tick, Math.min(350, A.interval() / st.speed));
  }
  function stop() {
    st.playing = false;
    clearTimeout(st.timer);
    if (st.frames.length) paintChrome();
  }
  const setPredict = on => {
    st.predict = on; prefs.predict = on; vzSavePrefs(prefs);
    if (on) stop();
    if (!on && st.predicting) st.predicting = false;
    if (st.frames.length) { paintCode(); paintChrome(); }
  };
  const theaterOn = () => document.getElementById('split')?.classList.contains('code-hidden');
  const paintTheater = () => {
    const b = $('[data-a="theater"]', root);
    b.setAttribute('aria-pressed', String(!!theaterOn()));
    b.classList.toggle('is-on', !!theaterOn());
  };

  /* ------------------------------------------------------------ events -- */
  root.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b || !root.contains(b)) return;
    if (b.dataset.pick !== undefined) { stop(); loadAlgo(+b.dataset.pick); return; }
    if (b.dataset.variant) { st.variant = b.dataset.variant; $$('[data-variant]', root).forEach(x => x.classList.toggle('is-on', x === b)); run(); return; }
    if (b.dataset.speed) { st.speed = +b.dataset.speed; prefs.speed = st.speed; vzSavePrefs(prefs); paintChrome(); return; }
    if (b.dataset.beat !== undefined) { stop(); st.predicting = false; go(+b.dataset.beat); return; }
    if (b.dataset.jump !== undefined) { stop(); st.predicting = false; go(+b.dataset.jump); return; }
    if (b.dataset.hist !== undefined) { st.hist = st.hist === b.dataset.hist ? null : b.dataset.hist; paintState(); return; }
    if (b.dataset.guess !== undefined) {
      const k = b.dataset.guess;
      if (!k) st.guess.clear(); else if (st.guess.has(k)) st.guess.delete(k); else st.guess.add(k);
      paintChrome();
      return;
    }
    if (b.dataset.phase !== undefined) {
      // the next step in that phase, wrapping round to the first
      const L = st.phases.labels, n = L.length;
      let j = -1;
      for (let d = 1; d <= n; d++) { const x = (st.i + d) % n; if (L[x] === b.dataset.phase && L[(x - 1 + n) % n] !== L[x]) { j = x; break; } }
      if (j < 0) j = L.indexOf(b.dataset.phase);
      stop(); st.predicting = false; go(j);
      return;
    }
    const a = b.dataset.a;
    if (a === 'play') st.playing ? stop() : play();
    else if (a === 'next' || a === 'reveal') { stop(); stepForward(); }
    else if (a === 'prev') { stop(); stepBack(); }
    else if (a === 'first') { stop(); st.predicting = false; go(0); }
    else if (a === 'last') { stop(); st.predicting = false; go(st.frames.length - 1); }
    else if (a === 'run') run();
    else if (a === 'example') { input.value = spec.input; run(); }
    else if (a === 'theater') {
      // a view choice for this sitting, not the remembered editor preference
      if (typeof setCodeOpen === 'function') setCodeOpen(!!theaterOn(), false);
      paintTheater();
      setTimeout(() => { if (A.kind === 'canvas') drawCanvas(); }, 60);
    }
    else if (a === 'keys') { const k = $('.vz-keys', root); k.hidden = !k.hidden; b.setAttribute('aria-expanded', String(!k.hidden)); }
  });
  root.addEventListener('change', e => {
    const o = e.target.dataset.opt;
    if (o === 'stops') { st.stops = e.target.checked; prefs.stops = st.stops; vzSavePrefs(prefs); }
    if (o === 'predict') setPredict(e.target.checked);
  });
  scrub.addEventListener('input', () => { stop(); st.predicting = false; go(+scrub.value); });
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && (!multiline || e.metaKey || e.ctrlKey)) { e.preventDefault(); run(); }
    e.stopPropagation();
  });
  root.addEventListener('keydown', e => {
    if (e.target === input || e.metaKey || e.ctrlKey || e.altKey) return;
    const k = e.key;
    if (k === 'ArrowRight') { e.preventDefault(); stop(); stepForward(); }
    else if (k === 'ArrowLeft') { e.preventDefault(); stop(); stepBack(); }
    else if (k === ' ' && e.target.tagName !== 'BUTTON') { e.preventDefault(); st.playing ? stop() : play(); }
    else if (k === 'Home') { e.preventDefault(); stop(); st.predicting = false; go(0); }
    else if (k === 'End') { e.preventDefault(); stop(); st.predicting = false; go(st.frames.length - 1); }
    else if (k === 'p' || k === 'P') { setPredict(!st.predict); }
    else if (k === 'f' || k === 'F') { $('[data-a="theater"]', root).click(); }
    else if (k === '?') { $('[data-a="keys"]', root).click(); }
  });
  if (A.kind === 'canvas') {
    new ResizeObserver(() => { if (st.frames.length) drawCanvas(); }).observe(stage);
    new MutationObserver(() => { if (root.isConnected && st.frames.length) drawCanvas(); })
      .observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  }
  paintTheater();
  run();
  if (!embedded) root.focus({ preventScroll: true });
}
