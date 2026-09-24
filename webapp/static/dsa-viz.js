/* ============================================================================
   DSA visualizers — the "Visualize" tab in the problem workspace.

   Each topic registers one or more algorithms. An algorithm is:
     code     the Python it animates (one highlighted line per step)
     parse    input string → data (throws a readable Error on bad input)
     run      data → frames[]   (every frame is a full snapshot of the state)
     draw     paints one frame onto a canvas
   The player handles stepping, playback, scrubbing, and custom input.

   Requires viz.js (drawing kit, palette) and app.js (esc, emptyMsg).
   ========================================================================= */
'use strict';

const ALGOS = {};
const defineAlgo = (topics, spec) => [].concat(topics).forEach(t => (ALGOS[t] ??= []).push(spec));

/* -------------------------------------------------------------- parsing -- */
const avNums = (s, max = 16, what = 'numbers') => {
  const out = String(s || '').split(/[\s,]+/).filter(Boolean).map(x => {
    const n = Number(x);
    if (!Number.isFinite(n)) throw new Error(`“${x}” is not a number`);
    return n;
  });
  if (!out.length) throw new Error(`Enter at least one ${what.replace(/s$/, '')}`);
  if (out.length > max) throw new Error(`Use at most ${max} ${what} so the animation stays readable`);
  return out;
};
const avParts = s => String(s || '').split(';').map(x => x.trim());
const avNum = (x, label) => { const n = Number(x); if (x === undefined || x === '' || !Number.isFinite(n)) throw new Error(`Add ${label} after the “;”`); return n; };

function avRecorder() {
  const F = [];
  return { F, snap: (line, note, state) => F.push({ line, note, ...structuredClone(state) }) };
}

/* -------------------------------------------------------- drawing helpers -- */
const AV = {
  row(ctx, P, vals, { cw, y, max = 52, gap = 6, style = () => ({}), index = true, x0 }) {
    const n = vals.length, size = Math.min(max, (cw - 40 - (n - 1) * gap) / n);
    const total = n * size + (n - 1) * gap, left = x0 ?? (cw - total) / 2;
    vals.forEach((v, i) => {
      const st = style(i) || {}, x = left + i * (size + gap);
      ctx.globalAlpha = st.fade ? .32 : 1;
      ctx.fillStyle = st.fill || P.surface2; D.rrect(ctx, x, y, size, size, Math.min(9, size / 4)); ctx.fill();
      ctx.strokeStyle = st.stroke || P.strong; ctx.lineWidth = st.stroke ? 2.4 : 1.2; ctx.stroke();
      D.text(ctx, String(v), x + size / 2, y + size / 2 + .5, { color: st.color || P.text, size: Math.max(10, Math.min(17, size * .36)), align: 'center', weight: 650, mono: true });
      if (index) D.text(ctx, String(i), x + size / 2, y - 9, { color: P.faint, size: 10, align: 'center', mono: true });
      ctx.globalAlpha = 1;
    });
    return { x: i => left + i * (size + gap) + size / 2, left, y, size, gap, total, right: left + total };
  },
  ptr(ctx, P, g, i, label, color, level = 0, above = false) {
    const x = g.x(i), y = above ? g.y - 24 - level * 16 : g.y + g.size + 14 + level * 16;
    D.text(ctx, `${above ? '▼' : '▲'} ${label}`, x, y, { color, size: 11.5, align: 'center', weight: 700, mono: true });
  },
  bracket(ctx, P, g, a, b, color, label) {
    if (a > b) return;
    const x1 = g.x(a) - g.size / 2 - 3, x2 = g.x(b) + g.size / 2 + 3, y = g.y - 4;
    ctx.fillStyle = P.alpha(color, .12); D.rrect(ctx, x1, y, x2 - x1, g.size + 8, 10); ctx.fill();
    ctx.strokeStyle = color; ctx.lineWidth = 2; D.rrect(ctx, x1, y, x2 - x1, g.size + 8, 10); ctx.stroke();
    if (label) D.text(ctx, label, (x1 + x2) / 2, y - 22, { color, size: 11, align: 'center', weight: 700 });
  },
  pills(ctx, P, x, y, maxW, title, items, { hi = null, miss = null } = {}) {
    D.text(ctx, title, x, y, { color: P.dim, size: 11.5, weight: 650 });
    let cx = x, cy = y + 14;
    items.forEach(([k, v]) => {
      const label = v === undefined ? String(k) : `${k} → ${v}`;
      D.font(ctx, 12, 600, true);
      const w = ctx.measureText(label).width + 18;
      if (cx + w > x + maxW) { cx = x; cy += 30; }
      const on = hi != null && String(k) === String(hi);
      ctx.fillStyle = on ? P.alpha('ok', .28) : P.surface2; D.rrect(ctx, cx, cy, w, 24, 12); ctx.fill();
      ctx.strokeStyle = on ? P.ok : P.strong; ctx.lineWidth = on ? 2 : 1; ctx.stroke();
      D.text(ctx, label, cx + w / 2, cy + 12.5, { color: P.text, size: 12, align: 'center', weight: 600, mono: true });
      cx += w + 6;
    });
    if (!items.length) D.text(ctx, '(empty)', x, cy + 12, { color: P.faint, size: 11.5 });
    if (miss != null) D.text(ctx, `${miss} is not here`, x, cy + 42, { color: P.err, size: 11.5, weight: 650 });
    return cy + 30 - y;
  },
  node(ctx, P, x, y, r, label, { fill, stroke, color, sub, ring } = {}) {
    if (ring) { ctx.beginPath(); ctx.arc(x, y, r + 5, 0, TAU); ctx.strokeStyle = ring; ctx.lineWidth = 2.5; ctx.stroke(); }
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU);
    ctx.fillStyle = fill || P.surface2; ctx.fill();
    ctx.strokeStyle = stroke || P.strong; ctx.lineWidth = stroke ? 2.2 : 1.3; ctx.stroke();
    D.text(ctx, String(label), x, y + .5, { color: color || P.text, size: Math.max(10, Math.min(14, r * .72)), align: 'center', weight: 700, mono: true });
    if (sub != null) D.text(ctx, String(sub), x, y + r + 11, { color: P.dim, size: 10.5, align: 'center', mono: true });
  },
  bars(ctx, P, vals, { cw, top, bottom, style = () => ({}), labels = true }) {
    const n = vals.length, gap = 6, w = Math.min(46, (cw - 40 - (n - 1) * gap) / n), total = n * w + (n - 1) * gap, left = (cw - total) / 2;
    const mx = Math.max(1, ...vals.map(Math.abs));
    vals.forEach((v, i) => {
      const st = style(i) || {}, h = Math.max(4, Math.abs(v) / mx * (bottom - top)), x = left + i * (w + gap);
      ctx.globalAlpha = st.fade ? .3 : 1;
      ctx.fillStyle = st.fill || P.alpha('accent', .55); D.rrect(ctx, x, bottom - h, w, h, 5); ctx.fill();
      if (st.stroke) { ctx.strokeStyle = st.stroke; ctx.lineWidth = 2.4; ctx.stroke(); }
      if (labels) D.text(ctx, String(v), x + w / 2, bottom - h - 9, { color: P.text, size: 11, align: 'center', mono: true, weight: 600 });
      D.text(ctx, String(i), x + w / 2, bottom + 11, { color: P.faint, size: 10, align: 'center', mono: true });
      ctx.globalAlpha = 1;
    });
    return { x: i => left + i * (w + gap) + w / 2, w, left, total, bottom, top, mx };
  },
  stack(ctx, P, x, y, w, title, items, { top = true, color } = {}) {
    D.text(ctx, title, x, y, { color: P.dim, size: 11.5, weight: 650 });
    items.forEach((it, k) => {
      const yy = y + 14 + (items.length - 1 - k) * 28, isTop = top && k === items.length - 1;
      ctx.fillStyle = isTop ? P.alpha(color || 'accent', .3) : P.surface2; D.rrect(ctx, x, yy, w, 24, 6); ctx.fill();
      ctx.strokeStyle = isTop ? (color || P.accent) : P.strong; ctx.lineWidth = 1.2; ctx.stroke();
      D.text(ctx, String(it), x + w / 2, yy + 12.5, { color: P.text, size: 12, align: 'center', mono: true, weight: 600 });
    });
    if (!items.length) D.text(ctx, '(empty)', x + w / 2, y + 26, { color: P.faint, size: 11, align: 'center' });
  },
  arrow: (ctx, x1, y1, x2, y2, col, w = 2) => D.arrow(ctx, x1, y1, x2, y2, col, w, 8),
};

/* ---------------------------------------------------------------- player -- */
function renderAlgoTab(body, topicId, cur) {
  let list = ALGOS[topicId];
  if (!list || !list.length) {
    body.innerHTML = emptyMsg('No visualizer for this topic yet', 'The Question, Solution and Topic guide tabs have everything else.');
    return;
  }
  
  // Filter down to the specific problem we're viewing
  if (cur && cur.title) {
     const matchIdx = list.findIndex(a => a.short === cur.title || a.title === cur.title);
     if (matchIdx !== -1) {
         list = [list[matchIdx]];
     } else {
         body.innerHTML = emptyMsg('No visualizer for this problem yet', 'A step-by-step visualizer has not been created for this specific problem yet.');
         return;
     }
  }

  let prefs = {};
  try { prefs = JSON.parse(localStorage.getItem('algo-prefs') || '{}'); } catch (e) { }
  
  function loadAlgo(k) {
    prefs[topicId] = k;
    try { localStorage.setItem('algo-prefs', JSON.stringify(prefs)); } catch (e) { }
    const spec = list[k];
    if (spec.type === 'dom') {
      renderDomAlgo(body, list, topicId, k, loadAlgo);
    } else {
      renderCanvasAlgo(body, list, topicId, k, loadAlgo);
    }
  }
  
  let initialK = 0;
  loadAlgo(initialK);
}

function renderCanvasAlgo(body, list, topicId, initialK, loadAlgo) {
  let prefs = {};
  try { prefs = JSON.parse(localStorage.getItem('algo-prefs') || '{}'); } catch (e) { /* private mode */ }
  const st = { k: initialK, variant: null, frames: [], i: 0, playing: false, speed: prefs.speed || 1, acc: 0, raf: 0 };
body.innerHTML = `
    <div class="algo" tabindex="-1">
      <div class="algo-head">
        <div class="algo-titles"><p class="algo-kicker">Step-by-step visualizer</p><h3 class="algo-title"></h3></div>
        ${list.length > 1 ? `<div class="seg algo-pick">${list.map((a, i) => `<button type="button" data-pick="${i}">${esc(a.short || a.title)}</button>`).join('')}</div>` : ''}
      </div>
      <p class="algo-idea"></p>
      <div class="algo-variants"></div>
      <div class="algo-canvas"><canvas></canvas></div>
      <p class="algo-note" aria-live="polite"></p>
      <div class="algo-vars"></div>
      <div class="algo-controls">
        <button type="button" class="algo-btn" data-a="first" title="Back to the start" aria-label="Back to the start">⏮</button>
        <button type="button" class="algo-btn" data-a="prev" title="Previous step (←)" aria-label="Previous step">◀</button>
        <button type="button" class="algo-btn primary" data-a="play" title="Play / pause (space)"></button>
        <button type="button" class="algo-btn" data-a="next" title="Next step (→)" aria-label="Next step">▶</button>
        <input type="range" class="algo-scrub" min="0" max="0" value="0" aria-label="Step">
        <span class="algo-step"></span>
        <div class="seg algo-speed">${[.5, 1, 2, 4].map(v => `<button type="button" data-speed="${v}">${v}×</button>`).join('')}</div>
      </div>
      <pre class="algo-code"></pre>
      <div class="algo-input">
        <label><span>Try your own input</span><input type="text" spellcheck="false"></label>
        <button type="button" class="btn btn-primary" data-a="run">Run</button>
        <button type="button" class="btn btn-ghost" data-a="example">Example</button>
        <span class="algo-hint"></span>
        <span class="algo-err" role="alert"></span>
      </div>
      <p class="algo-complexity"></p>
    </div>`;
  const root = $('.algo', body), cv = $('canvas', root), ctx = cv.getContext('2d'), wrap = $('.algo-canvas', root);
  const input = $('.algo-input input', root), scrub = $('.algo-scrub', root);
  let spec = null;

  function load(k) {
    if(list[k].type === 'dom') return loadAlgo(k);
    spec = list[k]; st.k = k;
    prefs[topicId] = k;
    try { localStorage.setItem('algo-prefs', JSON.stringify(prefs)); } catch (e) { /* ignore */ }
    $$('[data-pick]', root).forEach(b => b.classList.toggle('is-on', +b.dataset.pick === k));
    $('.algo-title', root).textContent = spec.title;
    $('.algo-idea', root).innerHTML = spec.idea;
    $('.algo-complexity', root).textContent = spec.complexity || '';
    $('.algo-hint', root).textContent = spec.hint ? `Format: ${spec.hint}` : '';
    st.variant = spec.variants ? spec.variants[0][0] : null;
    $('.algo-variants', root).innerHTML = spec.variants ? `<div class="seg">${spec.variants.map(([v, l]) => `<button type="button" data-variant="${v}" class="${v === st.variant ? 'is-on' : ''}">${l}</button>`).join('')}</div>` : '';
    input.value = spec.input;
    run();
  }
  function codeLines() { return typeof spec.code === 'function' ? spec.code(st.variant) : spec.code; }
  function run() {
    stop();
    try {
      st.frames = spec.run(spec.parse(input.value), st.variant);
      if (!st.frames.length) throw new Error('Nothing to show for this input');
      $('.algo-err', root).textContent = '';
    } catch (e) {
      $('.algo-err', root).textContent = e.message;
      return;
    }
    $('.algo-code', root).innerHTML = codeLines().map((ln, i) => `<span class="al" data-l="${i}"><i>${i + 1}</i>${esc(ln).replace(/(#.*)$/, '<em>$1</em>')}</span>`).join('');
    scrub.max = st.frames.length - 1;
    go(0);
  }
  function go(i) {
    st.i = clamp(i, 0, st.frames.length - 1);
    paint();
  }
  function paint() {
    const f = st.frames[st.i];
    if (!f) return;
    $$('.al', root).forEach(el => el.classList.toggle('is-on', +el.dataset.l === f.line));
    const onLine = $(`.al[data-l="${f.line}"]`, root);
    const pre = $('.algo-code', root);
    if (onLine && (onLine.offsetTop < pre.scrollTop || onLine.offsetTop > pre.scrollTop + pre.clientHeight - 24)) pre.scrollTop = onLine.offsetTop - 30;
    $('.algo-note', root).innerHTML = f.note || '';
    $('.algo-vars', root).innerHTML = Object.entries(f.vars || {}).map(([k, v]) => `<span class="stat-chip"><span>${esc(k)}</span><b>${esc(typeof v === 'object' ? JSON.stringify(v) : String(v))}</b></span>`).join('');
    $('.algo-step', root).textContent = `step ${st.i + 1} of ${st.frames.length}`;
    scrub.value = st.i;
    const playBtn = $('[data-a="play"]', root);
    playBtn.textContent = st.playing ? '❚❚ Pause' : st.i >= st.frames.length - 1 ? '↻ Replay' : '▶ Play';
    draw();
  }
  function draw() {
    if (!root.isConnected) return;
    const f = st.frames[st.i];
    const w = Math.max(280, wrap.clientWidth || 600);
    const h = Math.round(spec.height ? spec.height(w, st.frames[st.frames.length - 1], st.frames) : 260);
    const d = window.devicePixelRatio || 1;
    if (cv.width !== Math.round(w * d) || cv.height !== Math.round(h * d)) { cv.width = Math.round(w * d); cv.height = Math.round(h * d); cv.style.height = `${h}px`; }
    ctx.setTransform(d, 0, 0, d, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const P = labPalette(root);
    try { spec.draw(ctx, { w, h }, f, P, st.frames); } catch (e) { console.error(e); }
  }
  function tick(now) {
    if (!st.playing || !root.isConnected) { st.playing = false; return; }
    const dt = Math.min(100, now - (st.last || now));
    st.last = now;
    st.acc += dt * st.speed;
    if (st.acc >= 850) {
      st.acc = 0;
      if (st.i >= st.frames.length - 1) { stop(); return; }
      go(st.i + 1);
    }
    st.raf = requestAnimationFrame(tick);
  }
  function play() {
    if (st.i >= st.frames.length - 1) go(0);
    st.playing = true; st.acc = 600; st.last = 0;
    st.raf = requestAnimationFrame(tick);
    paint();
  }
  function stop() { st.playing = false; cancelAnimationFrame(st.raf); if (st.frames.length) paint(); }

  root.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    if (b.dataset.pick) { loadAlgo(+b.dataset.pick); return; }
    if (b.dataset.variant) { st.variant = b.dataset.variant; $$('[data-variant]', root).forEach(x => x.classList.toggle('is-on', x === b)); run(); return; }
    if (b.dataset.speed) { st.speed = +b.dataset.speed; prefs.speed = st.speed; try { localStorage.setItem('algo-prefs', JSON.stringify(prefs)); } catch (er) { /* ignore */ } paintSpeed(); return; }
    const a = b.dataset.a;
    if (a === 'play') st.playing ? stop() : play();
    else if (a === 'next') { stop(); go(st.i + 1); }
    else if (a === 'prev') { stop(); go(st.i - 1); }
    else if (a === 'first') { stop(); go(0); }
    else if (a === 'run') run();
    else if (a === 'example') { input.value = spec.input; run(); }
  });
  const paintSpeed = () => $$('[data-speed]', root).forEach(x => x.classList.toggle('is-on', +x.dataset.speed === st.speed));
  scrub.addEventListener('input', () => { stop(); go(+scrub.value); });
  input.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); run(); } e.stopPropagation(); });
  root.addEventListener('keydown', e => {
    if (e.target === input) return;
    if (e.key === 'ArrowRight') { e.preventDefault(); stop(); go(st.i + 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); stop(); go(st.i - 1); }
    else if (e.key === ' ') { e.preventDefault(); st.playing ? stop() : play(); }
  });
  new ResizeObserver(() => { if (st.frames.length) draw(); }).observe(wrap);
  new MutationObserver(() => { if (root.isConnected && st.frames.length) draw(); }).observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
  paintSpeed();
  load(st.k);
}

function renderDomAlgo(body, list, topicId, k, loadAlgo) {
    const spec = list[k];
    
    body.innerHTML = `
    <div class="dom-algo" tabindex="-1">
      <div class="algo-head">
        <div class="algo-titles"><p class="algo-kicker">Step-by-step visualizer</p><h3 class="algo-title">${esc(spec.title)}</h3></div>
        ${list.length > 1 ? `<div class="seg algo-pick">${list.map((a, i) => `<button type="button" data-pick="${i}" class="${i === k ? 'is-on' : ''}">${esc(a.short || a.title)}</button>`).join('')}</div>` : ''}
      </div>
      <p class="algo-idea">${spec.idea}</p>
      
      <div class="glass-panel controls-grid">
        <div style="flex:1;">
            <label>${spec.hint || 'Input'}</label>
            <input type="text" class="dom-input" value="${spec.input}">
        </div>
        <button class="btn-primary btn-apply">Initialize</button>
        <button class="btn-play dom-play">▶ Auto-Run</button>
      </div>
      <div class="text-error dom-err" style="color:var(--err);font-size:12px;display:none;margin:-6px 0 6px;"></div>

      <div class="workspace">
          <div class="main-col">
              <div class="dom-render-container" style="flex:1; display:flex; flex-direction:column; gap:10px;"></div>

              <!-- Inline Explanation Box -->
              <div class="glass-panel explanation-box" style="border-color: var(--accent); background: color-mix(in srgb, var(--accent) 5%, transparent); flex-shrink: 0;">
                  <div class="panel-heading" style="color: var(--accent); margin-bottom: 6px;">
                      <span style="display:flex; align-items:center; gap:6px;">ℹ️ <span class="expl-title">Concept</span></span>
                  </div>
                  <p class="expl-text" style="font-size: 0.9rem; color: var(--text); line-height: 1.4; min-height: 38px;">Ready to begin.</p>
                  <div class="explanation-actions" style="margin-top: 8px; display: none;">
                      <button class="btn-play btn-expl-resume" style="padding: 6px 12px; font-size: 0.8rem;">▶ Resume Auto-Run</button>
                  </div>
              </div>
          </div>

          <div class="glass-panel code-panel">
              <div class="panel-heading">Execution Trace</div>
              <ul class="pseudo-code">
                  ${spec.code.map((ln, i) => `<li data-line="${i+1}">${esc(ln).replace(/ /g, '&nbsp;')}</li>`).join('')}
              </ul>
              <div style="margin-top: 16px; display: flex; gap: 8px; flex-shrink: 0;">
                  <button class="btn-ghost dom-prev" style="flex: 1; padding: 8px;" disabled>◀ Prev</button>
                  <button class="btn-ghost dom-next" style="flex: 1; padding: 8px;">Next ▶</button>
              </div>
          </div>
      </div>

      <div class="status-bar">
          <div style="font-family: var(--mono); font-size: 0.75rem;" class="step-counter">Step 0 / 0</div>
          <div class="progress-container"><div class="progress-bar"></div></div>
          <div style="font-size: 0.8rem; font-weight: 500;" class="milestone-status">Ready</div>
      </div>
      <p class="algo-complexity">${spec.complexity}</p>
    </div>`;

    const root = body.querySelector('.dom-algo');
    const inputEl = root.querySelector('.dom-input');
    const errEl = root.querySelector('.dom-err');
    const btnApply = root.querySelector('.btn-apply');
    const btnPlay = root.querySelector('.dom-play');
    const btnPrev = root.querySelector('.dom-prev');
    const btnNext = root.querySelector('.dom-next');
    const btnResume = root.querySelector('.btn-expl-resume');
    const renderContainer = root.querySelector('.dom-render-container');
    const explTitle = root.querySelector('.expl-title');
    const explText = root.querySelector('.expl-text');
    const explActions = root.querySelector('.explanation-actions');
    const stepCounter = root.querySelector('.step-counter');
    const progressBar = root.querySelector('.progress-bar');
    const milestoneStatus = root.querySelector('.milestone-status');
    const codeLines = root.querySelectorAll('.pseudo-code li');

    let states = [];
    let currentStep = 0;
    let playInterval = null;

    function renderState() {
        if (!states.length) return;
        const s = states[currentStep];

        // Let the spec render the specific DOM components (arrays, maps, etc)
        spec.renderDOM(renderContainer, s, spec);

        // Highlight code
        codeLines.forEach(li => li.className = '');
        if (s.line) {
            const activeLine = root.querySelector(`.pseudo-code li[data-line="${s.line}"]`);
            if (activeLine) {
                activeLine.classList.add('active');
                if (s.color) activeLine.classList.add(s.color);
            }
        }

        // Status
        stepCounter.innerText = `Step ${currentStep + 1} / ${states.length}`;
        progressBar.style.width = `${((currentStep + 1) / states.length) * 100}%`;
        milestoneStatus.innerText = (s.kind || '').toUpperCase().replace(/-/g, ' ');

        // Buttons
        btnPrev.disabled = currentStep === 0;
        btnNext.disabled = currentStep === states.length - 1;
        
        // Explanation
        explTitle.innerText = s.explTitle || 'Concept';
        explText.innerText = s.explText || '';
        
        if (s.pause && playInterval) {
            pausePlay();
            explActions.style.display = 'block';
        } else {
            explActions.style.display = 'none';
        }
        
        if (currentStep === states.length - 1) pausePlay();
    }

    function parseAndInit() {
        errEl.style.display = 'none';
        try {
            const parsed = spec.parse(inputEl.value);
            states = spec.buildStates(parsed);
            if (!states.length) throw new Error("No steps generated.");
            currentStep = 0;
            renderState();
        } catch(e) {
            errEl.innerText = e.message;
            errEl.style.display = 'block';
        }
    }

    function pausePlay() {
        clearInterval(playInterval);
        playInterval = null;
        btnPlay.innerHTML = '▶ Auto-Run';
    }

    btnApply.addEventListener('click', () => { pausePlay(); parseAndInit(); });
    
    btnNext.addEventListener('click', () => {
        pausePlay(); explActions.style.display = 'none';
        if (currentStep < states.length - 1) { currentStep++; renderState(); }
    });
    
    btnPrev.addEventListener('click', () => {
        pausePlay(); explActions.style.display = 'none';
        if (currentStep > 0) { currentStep--; renderState(); }
    });

    btnPlay.addEventListener('click', () => {
        if (playInterval) {
            pausePlay();
        } else {
            if (currentStep === states.length - 1) currentStep = 0;
            btnPlay.innerHTML = '❚❚ Pause';
            playInterval = setInterval(() => {
                if (currentStep < states.length - 1) { currentStep++; renderState(); }
                else pausePlay();
            }, spec.speedMs || 600);
        }
    });

    btnResume.addEventListener('click', () => {
        explActions.style.display = 'none';
        btnPlay.click();
    });

    root.addEventListener('click', e => {
        const pick = e.target.closest('[data-pick]');
        if (pick) loadAlgo(+pick.dataset.pick);
    });

    parseAndInit();
}


/* =============================================================== 01 · hashing == */
defineAlgo('01_arrays_hashing', {
  type: 'dom',
  title: 'Concatenation of Array', short: 'Concat Array',
  idea: 'Create an array <code>ans</code> of length <code>2n</code> where <code>ans[i] == nums[i]</code> and <code>ans[i + n] == nums[i]</code>. It is just copying the array twice.',
  complexity: 'Time O(n) · Space O(n)',
  input: '1, 2, 1', hint: 'numbers',
  code: [
    'def get_concatenation(nums):',
    '    ans = []',
    '    for _ in range(2):',
    '        for x in nums:',
    '            ans.append(x)',
    '    return ans',
  ],
  parse(s) { return { nums: avNums(s, 10) }; },
  buildStates({ nums }) {
    const seq = [];
    const n = nums.length;
    const ans = new Array(2 * n).fill('');
    let curExplTitle = "Concept";
    let curExplText = "Ready to begin.";

    function pushState(s) {
        if (s.explTitle) curExplTitle = s.explTitle;
        if (s.explText) curExplText = s.explText;
        s.explTitle = curExplTitle;
        s.explText = curExplText;
        seq.push(s);
    }

    pushState({
        kind: 'init', line: 2, color: 'default',
        nums, ans: [...ans], i: -1, pass: 0, dest: -1,
        explTitle: "Initialization",
        explText: `We need an array 'ans' that is exactly twice as long as the input array.`,
        pause: true
    });

    for (let pass = 0; pass < 2; pass++) {
      pushState({
          kind: 'outer-loop', line: 3, color: 'default',
          nums, ans: [...ans], i: -1, pass, dest: -1,
          explTitle: `Pass ${pass + 1}`,
          explText: `Starting pass ${pass + 1} of 2. We'll iterate through all elements of 'nums'.`
      });

      for (let i = 0; i < n; i++) {
        const dest = pass * n + i;
        pushState({
            kind: 'inner-loop', line: 4, color: 'blue',
            nums, ans: [...ans], i, pass, dest,
            explTitle: "Iterating 'nums'",
            explText: `Look at nums[${i}] = ${nums[i]}.`
        });
        
        ans[dest] = nums[i];
        
        pushState({
            kind: 'append', line: 5, color: 'emerald',
            nums, ans: [...ans], i, pass, dest,
            explTitle: "Append to 'ans'",
            explText: `Append ${nums[i]} to the end of our 'ans' array (at index ${dest}).`
        });
      }
      
      pushState({
          kind: 'pass-done', line: 3, color: 'default',
          nums, ans: [...ans], i: -1, pass, dest: -1,
          explTitle: `Pass ${pass + 1} Complete`,
          explText: `Finished pass ${pass + 1}.`,
          pause: true
      });
    }
    
    pushState({
        kind: 'done', line: 6, color: 'default',
        nums, ans: [...ans], i: -1, pass: 2, dest: -1,
        explTitle: "Complete",
        explText: `Finished concatenating the array twice. We return 'ans'.`,
        pause: true
    });
    
    return seq;
  },
  renderDOM(container, s, spec) {
      const getArrayHTML = (arr, activeI, isAns, destI) => {
          return arr.map((v, idx) => {
              const isActive = !isAns && idx === activeI;
              const isTarget = isAns && idx === destI;
              const isEmpty = isAns && v === '';
              let cls = '';
              
              if (isTarget) cls = 'merged active-k'; // Highlight the appended item
              else if (isActive) cls = 'active-1';
              else if (!isEmpty && isAns) cls = 'merged'; // Show filled items differently
              
              return `
              <div class="array-node ${cls}" style="${isEmpty ? 'opacity:0.3; border-style:dashed;' : ''}">
                  ${isActive ? '<div class="pointer" style="color:var(--accent)">↓ i</div>' : ''}
                  ${isTarget ? '<div class="pointer" style="color:#34d399">↓</div>' : ''}
                  ${v}
                  <div class="node-index">${idx}</div>
              </div>`;
          }).join('');
      };

      container.innerHTML = `
          <div class="glass-panel arrays-container">
              <div>
                  <div class="panel-heading" style="color: var(--accent);">nums (Input)</div>
                  <div class="array-track">${getArrayHTML(s.nums, s.i, false, -1)}</div>
              </div>
          </div>
          <div class="glass-panel arrays-container">
              <div>
                  <div class="panel-heading" style="color: var(--text-dim);">ans (Output)</div>
                  <div class="array-track" style="padding-bottom: 24px;">${getArrayHTML(s.ans, -1, true, s.dest)}</div>
              </div>
          </div>
      `;
  }
});

defineAlgo('01_arrays_hashing', {
  type: 'dom',
  title: 'Contains Duplicate', short: 'Contains Dup',
  idea: 'Use a hash set to keep track of seen elements. If an element is already in the set, we found a duplicate.',
  complexity: 'Time O(n) · Space O(n)',
  input: '1, 2, 3, 1', hint: 'numbers',
  code: [
    'def containsDuplicate(nums):',
    '    seen = set()',
    '    for x in nums:',
    '        if x in seen:',
    '            return True',
    '        seen.add(x)',
    '    return False',
  ],
  parse(s) { return { nums: avNums(s, 14) }; },
  buildStates({ nums }) {
    const seq = [];
    const seen = [];
    let curExplTitle = 'Concept', curExplText = 'Ready to begin.';
    function pushState(s) {
      if (s.explTitle) curExplTitle = s.explTitle;
      if (s.explText) curExplText = s.explText;
      s.explTitle = curExplTitle; s.explText = curExplText;
      seq.push(s);
    }

    pushState({
      kind: 'init', line: 2, color: 'default',
      nums, seen: [...seen], i: -1, hit: null,
      explTitle: 'Initialization',
      explText: `We create an empty hash set 'seen' to track which numbers we've encountered.`,
      pause: true
    });

    for (let i = 0; i < nums.length; i++) {
      pushState({
        kind: 'check', line: 3, color: 'blue',
        nums, seen: [...seen], i, hit: null,
        explTitle: 'Iterating Array',
        explText: `Look at nums[${i}] = ${nums[i]}.`
      });

      const found = seen.includes(nums[i]);
      pushState({
        kind: 'lookup', line: 4, color: found ? 'emerald' : 'amber',
        nums, seen: [...seen], i, hit: found ? 'yes' : 'no',
        explTitle: found ? 'Duplicate Found!' : 'Not in Set',
        explText: found
          ? `${nums[i]} is already in the set! We found a duplicate.`
          : `${nums[i]} is not in the set yet.`
      });

      if (found) {
        pushState({
          kind: 'return-true', line: 5, color: 'emerald',
          nums, seen: [...seen], i, hit: 'yes',
          explTitle: 'Return True',
          explText: `We return True because ${nums[i]} appeared earlier.`,
          pause: true
        });
        return seq;
      }

      seen.push(nums[i]);
      pushState({
        kind: 'add', line: 6, color: 'default',
        nums, seen: [...seen], i, hit: null,
        explTitle: 'Add to Set',
        explText: `Add ${nums[i]} to 'seen'. Set is now: {${seen.join(', ')}}.`
      });
    }

    pushState({
      kind: 'done', line: 7, color: 'default',
      nums, seen: [...seen], i: -1, hit: null,
      explTitle: 'No Duplicates',
      explText: `Scanned all ${nums.length} elements without finding duplicates. Return False.`,
      pause: true
    });
    return seq;
  },
  renderDOM(container, s) {
    const getArrayHTML = (arr, activeI) => arr.map((v, idx) => {
      const isDup = s.hit === 'yes' && idx === activeI;
      const isActive = idx === activeI;
      let cls = '';
      if (isDup) cls = 'merged active-k';
      else if (isActive) cls = 'active-1';
      else if (activeI !== -1 && idx < activeI) cls = 'merged';
      return `<div class="array-node ${cls}" style="${!isDup && !isActive && activeI !== -1 && idx > activeI ? 'opacity:0.3' : ''}">
        ${isActive ? '<div class="pointer" style="color:var(--accent)">↓ i</div>' : ''}
        ${v}<div class="node-index">${idx}</div></div>`;
    }).join('');

    const getSetHTML = (seenArr, hit, val) => {
      if (!seenArr.length) return '<div style="color:var(--text-dim);font-size:0.8rem;padding:10px;">(empty)</div>';
      return seenArr.map(x => {
        const isHit = hit === 'yes' && x === val;
        return `<div style="display:inline-flex;align-items:center;padding:6px 14px;border-radius:999px;font-family:var(--mono);font-size:13px;font-weight:600;border:1px solid ${isHit ? '#34d399' : 'var(--border)'};background:${isHit ? 'rgba(52,211,153,0.1)' : 'var(--surface)'};color:${isHit ? '#34d399' : 'var(--text)'};box-shadow:${isHit ? '0 0 10px rgba(52,211,153,0.15)' : 'none'}">${x}</div>`;
      }).join('');
    };

    const curVal = s.i >= 0 ? s.nums[s.i] : null;
    const missHTML = s.hit === 'no' ? `<div style="color:#fb7185;font-size:12px;font-weight:600;margin-top:8px;">${curVal} is not here</div>` : '';
    container.innerHTML = `
      <div class="glass-panel arrays-container"><div>
        <div class="panel-heading" style="color:var(--accent);">nums (Input)</div>
        <div class="array-track" style="padding-bottom:24px;">${getArrayHTML(s.nums, s.i)}</div>
      </div></div>
      <div class="glass-panel" style="min-height:80px;"><div>
        <div class="panel-heading" style="color:var(--text-dim);">seen (Hash Set)</div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;padding:8px 4px;">${getSetHTML(s.seen, s.hit, curVal)}</div>
        ${missHTML}
      </div></div>`;
  }
});

defineAlgo('01_arrays_hashing', {
  title: 'Valid Anagram', short: 'Valid Anagram',
  idea: 'Count the frequencies of characters in <code>s</code>, then decrement for characters in <code>t</code>. If they match, all counts will end up at zero.',
  complexity: 'Time O(s+t) · Space O(26) = O(1) assuming lowercase English letters',
  input: 'anagram ; nagaram', hint: 's ; t',
  code: [
    'def isAnagram(s, t):',
    '    if len(s) != len(t):',
    '        return False',
    '    counts = {}',
    '    for char in s:',
    '        counts[char] = counts.get(char, 0) + 1',
    '    for char in t:',
    '        if counts.get(char, 0) == 0:',
    '            return False',
    '        counts[char] -= 1',
    '    return True',
  ],
  parse(str) { const [a, b] = avParts(str); return { sStr: a || '', tStr: b || '' }; },
  run({ sStr, tStr }) {
    const { F, snap } = avRecorder();
    const sArr = sStr.split(''), tArr = tStr.split('');
    const s = { sArr, tArr, counts: {}, i: -1, phase: 's', hit: null, vars: {} };
    snap(1, 'Check lengths. If they differ, they cannot be anagrams.', s);
    if (sArr.length !== tArr.length) {
      s.vars.result = 'False';
      snap(2, 'Lengths differ, return False.', s);
      return F;
    }
    
    snap(3, 'Create an empty map to store character frequencies.', s);
    for (let i = 0; i < sArr.length; i++) {
      const char = sArr[i];
      s.i = i; s.vars.char = `'${char}'`;
      s.counts[char] = (s.counts[char] || 0) + 1;
      snap(4, `<code>s</code>: count <code>'${char}'</code>.`, s);
    }
    
    s.phase = 't'; s.i = -1;
    snap(5, 'Now iterate through <code>t</code> and decrement counts.', s);
    for (let i = 0; i < tArr.length; i++) {
      const char = tArr[i];
      s.i = i; s.vars.char = `'${char}'`;
      snap(6, `<code>t</code>: check <code>'${char}'</code>.`, s);
      if (!s.counts[char] || s.counts[char] === 0) {
        s.hit = 'no';
        s.vars.result = 'False';
        snap(7, `<code>'${char}'</code> not found or count is zero. Not an anagram!`, s);
        return F;
      }
      s.hit = 'yes';
      s.counts[char]--;
      snap(8, `Found <code>'${char}'</code>, decrement its count.`, s);
    }
    
    s.i = -1; s.hit = null; s.vars.result = 'True';
    snap(9, 'Successfully matched all characters. Return True.', s);
    return F;
  },
  height: () => 240,
  draw(ctx, c, f, P) {
    const gS = AV.row(ctx, P, f.sArr, { cw: c.w, y: 30, style: i => f.phase === 's' && i === f.i ? { fill: P.alpha('accent', .25), stroke: P.accent } : f.phase === 't' ? { fade: true } : {} });
    if (f.phase === 's' && f.i >= 0) AV.ptr(ctx, P, gS, f.i, 'i', P.accent);
    
    const gT = AV.row(ctx, P, f.tArr, { cw: c.w, y: 90, style: i => f.phase === 't' && i === f.i && f.hit === 'yes' ? { fill: P.alpha('ok', .3), stroke: P.ok } : f.phase === 't' && i === f.i && f.hit === 'no' ? { fill: P.alpha('danger', .3), stroke: P.danger } : f.phase === 't' && i === f.i ? { fill: P.alpha('accent', .25), stroke: P.accent } : f.phase === 's' ? { fade: true } : i < f.i ? { fade: true } : {} });
    if (f.phase === 't' && f.i >= 0) AV.ptr(ctx, P, gT, f.i, 'i', P.accent);
    
    D.text(ctx, 's', gS.left - 20, gS.y + gS.size / 2, { color: P.faint, size: 14, align: 'right', mono: true });
    if (f.tArr.length > 0) D.text(ctx, 't', gT.left - 20, gT.y + gT.size / 2, { color: P.faint, size: 14, align: 'right', mono: true });
    
    const mapItems = Object.entries(f.counts).map(([k, v]) => [`'${k}'`, v]);
    AV.pills(ctx, P, 20, 160, c.w - 40, 'counts (Char → Freq)', mapItems, { hi: f.hit === 'yes' ? `'${f.tArr[f.i]}'` : null, miss: f.hit === 'no' ? `'${f.tArr[f.i]}'` : null });
  },
});

defineAlgo('01_arrays_hashing', {
  type: 'dom',
  title: 'Two Sum with a hash map', short: 'Two Sum',
  idea: 'One pass: for each number, ask the map whether its complement <code>target − x</code> has already been seen. A hash lookup is O(1), so the whole scan is O(n).',
  complexity: 'Time O(n) · Space O(n) · the brute-force pair check would be O(n²)',
  input: '3, 8, 11, 2, 15, 7 ; 9', hint: 'numbers ; target',
  code: [
    'def two_sum(nums, target):',
    '    seen = {}                      # value -> index',
    '    for i, x in enumerate(nums):',
    '        need = target - x',
    '        if need in seen:',
    '            return [seen[need], i]',
    '        seen[x] = i',
    '    return []',
  ],
  parse(s) { const [a, t] = avParts(s); return { nums: avNums(a, 14), target: avNum(t, 'the target') }; },
  buildStates({ nums, target }) {
    const seq = [];
    const seen = []; 
    let curExplTitle = "Concept";
    let curExplText = "Ready to begin.";

    function pushState(s) {
        if (s.explTitle) curExplTitle = s.explTitle;
        if (s.explText) curExplText = s.explText;
        s.explTitle = curExplTitle;
        s.explText = curExplText;
        seq.push(s);
    }

    pushState({
        kind: 'init', line: 2, color: 'default',
        nums, target, seen: [...seen], i: -1, need: null, hit: null, pair: null,
        explTitle: "Initialization",
        explText: `We want to find two numbers that add up to ${target}. We'll use a hash map 'seen' to store numbers we've visited as (value -> index).`,
        pause: true
    });

    for (let i = 0; i < nums.length; i++) {
        pushState({
            kind: 'loop', line: 3, color: 'default',
            nums, target, seen: [...seen], i, need: null, hit: null, pair: null,
            explTitle: "Iterating Array",
            explText: `Look at nums[${i}] = ${nums[i]}.`
        });

        const need = target - nums[i];
        pushState({
            kind: 'calc-need', line: 4, color: 'amber',
            nums, target, seen: [...seen], i, need, hit: null, pair: null,
            explTitle: "Calculate Complement",
            explText: `To hit our target of ${target} using ${nums[i]}, we need its complement: ${target} - ${nums[i]} = ${need}.`
        });

        const foundIdx = seen.findIndex(([k]) => k === need);
        const hit = foundIdx !== -1 ? 'yes' : 'no';
        
        pushState({
            kind: 'check-map', line: 5, color: 'blue',
            nums, target, seen: [...seen], i, need, hit, pair: null,
            explTitle: "Check Hash Map",
            explText: `We check if our complement ${need} is already in the 'seen' map. A hash map lookup is O(1) time.`
        });

        if (foundIdx !== -1) {
            const pair = [seen[foundIdx][1], i];
            pushState({
                kind: 'return-pair', line: 6, color: 'emerald',
                nums, target, seen: [...seen], i, need, hit, pair,
                explTitle: "Pair Found!",
                explText: `Success! ${need} is in the map at index ${pair[0]}. We return [${pair[0]}, ${pair[1]}].`,
                pause: true
            });
            return seq;
        }

        pushState({
            kind: 'add-to-map', line: 7, color: 'default',
            nums, target, seen: [...seen], i, need, hit, pair: null,
            explTitle: "Not Found",
            explText: `${need} is not in the map yet. We add our current number ${nums[i]} to the map at index ${i} so later numbers can find it.`
        });
        
        seen.push([nums[i], i]);
        
        pushState({
            kind: 'added', line: 7, color: 'emerald',
            nums, target, seen: [...seen], i, need, hit, pair: null,
            explTitle: "Added to Map",
            explText: `Added ${nums[i]} -> ${i} to 'seen'.`
        });
    }

    pushState({
        kind: 'not-found', line: 8, color: 'default',
        nums, target, seen: [...seen], i: -1, need: null, hit: null, pair: null,
        explTitle: "Complete",
        explText: `We checked every number and didn't find a pair that adds up to ${target}. Return empty list.`,
        pause: true
    });

    return seq;
  },
  renderDOM(container, s, spec) {
      const getArrayHTML = (arr, activeI, highlightIndices) => {
          return arr.map((v, idx) => {
              const isActive = idx === activeI;
              const isHighlight = highlightIndices && highlightIndices.includes(idx);
              let cls = '';
              if (isHighlight) cls = 'merged active-k';
              else if (isActive) cls = 'active-1';
              else if (activeI !== -1 && idx < activeI) cls = 'merged';
              
              return `
              <div class="array-node ${cls}" style="${!isHighlight && !isActive && activeI !== -1 && idx > activeI ? 'opacity:0.3' : ''}">
                  ${isActive ? '<div class="pointer" style="color:var(--accent)">↓ i</div>' : ''}
                  ${v}
                  <div class="node-index">${idx}</div>
              </div>`;
          }).join('');
      };

      const getMapHTML = (seenArr, need, hit) => {
          if (!seenArr.length) return '<div style="color:var(--text-dim);font-size:0.8rem;padding:10px;">(empty)</div>';
          return seenArr.map(([val, idx]) => {
              const isHit = hit === 'yes' && val === need;
              return `
              <div style="display:inline-flex; align-items:baseline; gap:6px; padding:6px 12px; border-radius:999px; font-family:var(--mono); font-size:12px; border:1px solid ${isHit ? '#34d399' : 'var(--border)'}; background:${isHit ? 'rgba(52, 211, 153, 0.1)' : 'var(--surface)'}; color:${isHit ? '#34d399' : 'var(--text)'}; box-shadow:${isHit ? '0 0 10px rgba(52, 211, 153, 0.15)' : 'none'}">
                  <span>${val}</span> <span style="color:var(--text-faint)">→</span> <b>${idx}</b>
              </div>`;
          }).join('');
      };

      const mapMissHTML = s.hit === 'no' ? `<div style="color:#fb7185; font-size:12px; font-weight:600; margin-top:8px;">${s.need} is not here</div>` : '';

      container.innerHTML = `
          <div class="glass-panel arrays-container">
              <div>
                  <div class="panel-heading" style="color: var(--accent);">Target = ${s.target}</div>
                  <div class="array-track" style="padding-bottom: 24px;">${getArrayHTML(s.nums, s.i, s.pair)}</div>
              </div>
          </div>
          <div class="glass-panel" style="min-height:90px;">
              <div class="panel-heading" style="color: var(--text-dim);">Seen (value → index)</div>
              <div style="display:flex; flex-wrap:wrap; gap:8px; padding:8px 4px;">
                  ${getMapHTML(s.seen, s.need, s.hit)}
              </div>
              ${mapMissHTML}
          </div>
      `;
  }
});

defineAlgo('01_arrays_hashing', {
  title: 'Majority Element', short: 'Majority Element',
  idea: 'Boyer-Moore Voting Algorithm: Keep track of a candidate and a count. If count is 0, pick the current element as the new candidate. Otherwise, increment/decrement if the current matches the candidate.',
  complexity: 'Time O(n) · Space O(1)',
  input: '2, 2, 1, 1, 1, 2, 2', hint: 'numbers',
  code: [
    'def majorityElement(nums):',
    '    candidate, count = None, 0',
    '    for num in nums:',
    '        if count == 0:',
    '            candidate = num',
    '        count += (1 if num == candidate else -1)',
    '    return candidate',
  ],
  parse(s) { return { nums: avNums(s, 14) }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    const s = { nums, candidate: null, count: 0, i: -1, phase: '', vars: {} };
    snap(1, 'Start with <code>candidate = None</code> and <code>count = 0</code>.', s);
    for (let i = 0; i < nums.length; i++) {
      const num = nums[i];
      s.i = i; s.vars.num = num; s.phase = '';
      snap(2, `Look at <code>nums[${i}] = ${num}</code>.`, s);
      if (s.count === 0) {
        s.candidate = num; s.vars.candidate = num;
        snap(3, `Count is 0, so pick <b>${num}</b> as the new candidate.`, s);
      }
      const match = num === s.candidate;
      s.phase = match ? 'match' : 'mismatch';
      s.count += (match ? 1 : -1);
      s.vars.count = s.count;
      snap(4, match ? `Matches candidate, increment count to ${s.count}.` : `Differs from candidate, decrement count to ${s.count}.`, s);
    }
    s.i = -1; s.phase = ''; s.vars.result = String(s.candidate);
    snap(5, `Finished array. The majority element is <b>${s.candidate}</b>.`, s);
    return F;
  },
  height: () => 200,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 34, style: i => i === f.i && f.phase === 'match' ? { fill: P.alpha('ok', .3), stroke: P.ok } : i === f.i && f.phase === 'mismatch' ? { fill: P.alpha('danger', .3), stroke: P.danger } : i === f.i ? { fill: P.alpha('accent', .25), stroke: P.accent } : i < f.i ? { fade: true } : {} });
    if (f.i >= 0) AV.ptr(ctx, P, g, f.i, 'i', P.accent);
    
    const items = [];
    if (f.candidate !== null) items.push(['Candidate', String(f.candidate)]);
    items.push(['Count', String(f.count)]);
    AV.pills(ctx, P, 20, g.y + g.size + 50, c.w - 40, 'State', items, { hi: null, miss: null });
  },
});

defineAlgo('01_arrays_hashing', {
  title: 'Find Disappeared Numbers', short: 'Disappeared Nums',
  idea: 'We can mark the presence of a number `x` by making the element at index `|x| - 1` negative. A second pass reveals which indices were never marked (i.e. are still positive).',
  complexity: 'Time O(n) · Space O(1) beyond the output array',
  input: '4, 3, 2, 7, 8, 2, 3, 1', hint: 'numbers',
  code: [
    'def findDisappearedNumbers(nums):',
    '    for x in nums:',
    '        idx = abs(x) - 1',
    '        if nums[idx] > 0:',
    '            nums[idx] = -nums[idx]',
    '    ans = []',
    '    for i in range(len(nums)):',
    '        if nums[i] > 0:',
    '            ans.append(i + 1)',
    '    return ans',
  ],
  parse(s) { return { nums: avNums(s, 10) }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    const arr = [...nums];
    const s = { nums: [...arr], i: -1, phase: 'mark', idx: -1, ans: [], vars: {} };
    snap(1, 'Start pass 1: mark elements negative.', s);
    for (let i = 0; i < arr.length; i++) {
      const x = arr[i];
      const idx = Math.abs(x) - 1;
      s.i = i; s.idx = -1; s.vars.x = x; s.vars.idx = idx;
      snap(2, `Look at <code>nums[${i}] = ${x}</code>. The target index is <code>|${x}| - 1 = ${idx}</code>.`, s);
      s.idx = idx;
      if (arr[idx] > 0) {
        arr[idx] = -arr[idx];
        s.nums = [...arr];
        snap(3, `<code>nums[${idx}]</code> is positive, so we make it negative to mark ${Math.abs(x)} as seen.`, s);
      } else {
        snap(4, `<code>nums[${idx}]</code> is already negative. ${Math.abs(x)} was marked before.`, s);
      }
    }
    
    s.phase = 'gather'; s.i = -1; s.idx = -1;
    snap(5, 'Start pass 2: find positive elements.', s);
    for (let i = 0; i < arr.length; i++) {
      s.i = i;
      if (arr[i] > 0) {
        s.ans.push(i + 1);
        s.vars.ans = '[' + s.ans.join(', ') + ']';
        snap(6, `<code>nums[${i}]</code> is > 0, which means ${i + 1} was never seen. Add it to ans.`, s);
      } else {
        snap(7, `<code>nums[${i}]</code> is < 0, so ${i + 1} was seen.`, s);
      }
    }
    s.i = -1;
    snap(8, `Finished. The missing numbers are [${s.ans.join(', ')}].`, s);
    return F;
  },
  height: () => 220,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 34, style: i => {
      if (f.phase === 'mark') {
        if (i === f.idx) return { fill: P.alpha('danger', .3), stroke: P.danger };
        if (i === f.i) return { fill: P.alpha('accent', .25), stroke: P.accent };
      } else if (f.phase === 'gather') {
        if (i === f.i && f.nums[i] > 0) return { fill: P.alpha('ok', .3), stroke: P.ok };
        if (i === f.i) return { fill: P.alpha('accent', .25), stroke: P.accent };
        if (i < f.i) return { fade: true };
      }
      return {};
    } });
    if (f.phase === 'mark' && f.i >= 0) AV.ptr(ctx, P, g, f.i, 'i', P.accent);
    if (f.phase === 'mark' && f.idx >= 0) AV.ptr(ctx, P, g, f.idx, 'idx', P.danger, f.idx === f.i ? 1 : 0, true);
    
    if (f.phase === 'gather') {
      if (f.i >= 0) AV.ptr(ctx, P, g, f.i, 'i', P.accent);
      if (f.ans.length > 0) {
        const ansRow = AV.row(ctx, P, f.ans, { cw: c.w, y: 120, max: 40, style: () => ({ fill: P.surface2, stroke: P.ok }) });
        D.text(ctx, 'ans', ansRow.left - 24, ansRow.y + ansRow.size / 2 + 0.5, { color: P.text, size: 13, align: 'right', weight: 600, mono: true });
      }
    }
  },
});

defineAlgo('01_arrays_hashing', {
  title: 'Group Anagrams', short: 'Group Anagrams',
  idea: 'Anagrams share the same letters. If we sort each string (or count character frequencies), all anagrams will yield the same key. We can use this key in a hash map to group them.',
  complexity: 'Time O(N × K log K) with sorting (K = max length) · Space O(N × K)',
  input: 'eat, tea, tan, ate, nat, bat', hint: 'strings',
  code: [
    'def groupAnagrams(strs):',
    '    groups = {}',
    '    for s in strs:',
    '        key = tuple(sorted(s))',
    '        if key not in groups:',
    '            groups[key] = []',
    '        groups[key].append(s)',
    '    return list(groups.values())',
  ],
  parse(str) { return { strs: str.split(',').map(s => s.trim().replace(/^['"]|['"]$/g, '')).filter(x => x) }; },
  run({ strs }) {
    const { F, snap } = avRecorder();
    const s = { strs, groups: {}, i: -1, vars: {} };
    snap(1, 'Initialize an empty hash map for groups.', s);
    for (let i = 0; i < strs.length; i++) {
      const str = strs[i];
      s.i = i; s.vars.s = `'${str}'`; s.vars.key = null;
      snap(2, `Look at <code>strs[${i}] = '${str}'</code>.`, s);
      const key = str.split('').sort().join('');
      s.vars.key = `'${key}'`;
      snap(3, `Sort the string to get the key: <b>'${key}'</b>.`, s);
      if (!s.groups[key]) {
        s.groups[key] = [];
        snap(4, `Key <code>'${key}'</code> not in map. Create an empty list for it.`, s);
      }
      s.groups[key].push(str);
      snap(5, `Append <code>'${str}'</code> to <code>groups['${key}']</code>.`, s);
    }
    s.i = -1;
    s.vars.result = '[' + Object.values(s.groups).map(g => '[' + g.map(x => `'${x}'`).join(', ') + ']').join(', ') + ']';
    snap(6, 'Finished grouping. Return the values of the hash map.', s);
    return F;
  },
  height: () => 260,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.strs.map(x => `'${x}'`), { cw: c.w, y: 34, style: i => i === f.i ? { fill: P.alpha('accent', .25), stroke: P.accent } : i < f.i ? { fade: true } : {} });
    if (f.i >= 0) AV.ptr(ctx, P, g, f.i, 'i', P.accent);
    
    const items = Object.entries(f.groups).map(([k, v]) => [`'${k}'`, '[' + v.map(x => `'${x}'`).join(', ') + ']']);
    AV.pills(ctx, P, 20, g.y + g.size + 50, c.w - 40, 'groups (Sorted Key → List of Anagrams)', items, { hi: f.i >= 0 ? `'${f.strs[f.i].split('').sort().join('')}'` : null, miss: null });
  },
});

defineAlgo('01_arrays_hashing', {
  title: 'Top K Frequent Elements', short: 'Top K Freq',
  idea: 'Count frequencies with a hash map. Then use bucket sort: create an array `freq` where index is the frequency, and value is a list of elements. Since max freq is `n`, this array is bounded. Finally, iterate backwards to gather `k` elements.',
  complexity: 'Time O(n) · Space O(n)',
  input: '1, 1, 1, 2, 2, 3 ; 2', hint: 'nums ; k',
  code: [
    'def topKFrequent(nums, k):',
    '    count = {}',
    '    for num in nums:',
    '        count[num] = count.get(num, 0) + 1',
    '    ',
    '    freq = [[] for _ in range(len(nums) + 1)]',
    '    for num, c in count.items():',
    '        freq[c].append(num)',
    '    ',
    '    res = []',
    '    for i in range(len(freq) - 1, 0, -1):',
    '        for num in freq[i]:',
    '            res.append(num)',
    '            if len(res) == k:',
    '                return res',
  ],
  parse(str) { const [a, b] = avParts(str); return { nums: avNums(a, 10), k: avNum(b, 'k') }; },
  run({ nums, k }) {
    const { F, snap } = avRecorder();
    const s = { nums, count: {}, freq: Array.from({ length: nums.length + 1 }, () => []), res: [], phase: 'count', i: -1, freqI: -1, vars: { k } };
    snap(1, 'Phase 1: Count frequencies.', s);
    for (let i = 0; i < nums.length; i++) {
      const num = nums[i];
      s.i = i; s.vars.num = num;
      s.count[num] = (s.count[num] || 0) + 1;
      snap(2, `Count element <code>${num}</code>.`, s);
    }
    s.i = -1;
    s.phase = 'bucket';
    snap(3, 'Phase 2: Group by frequency (bucket sort).', s);
    for (const [numStr, c] of Object.entries(s.count)) {
      const num = Number(numStr);
      s.freq[c] = [...s.freq[c], num];
      s.vars.num = num; s.vars.c = c;
      snap(4, `<code>${num}</code> appears ${c} times. Add it to <code>freq[${c}]</code>.`, s);
    }
    
    s.phase = 'gather';
    snap(5, 'Phase 3: Gather elements from highest frequency to lowest.', s);
    for (let i = s.freq.length - 1; i > 0; i--) {
      s.freqI = i; s.vars.i = i;
      snap(6, `Look at frequency ${i}.`, s);
      for (const num of s.freq[i]) {
        s.vars.num = num;
        s.res.push(num);
        s.vars.res = `[${s.res.join(', ')}]`;
        snap(7, `Found <code>${num}</code>. Add to result.`, s);
        if (s.res.length === k) {
          snap(8, `We found ${k} elements! Return result.`, s);
          return F;
        }
      }
    }
    return F;
  },
  height: () => 280,
  draw(ctx, c, f, P) {
    if (f.phase === 'count' || f.phase === 'bucket') {
      const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 34, style: i => f.phase === 'count' && i === f.i ? { fill: P.alpha('accent', .25), stroke: P.accent } : f.phase === 'count' && i < f.i ? { fade: true } : f.phase === 'bucket' ? { fade: true } : {} });
      if (f.phase === 'count' && f.i >= 0) AV.ptr(ctx, P, g, f.i, 'i', P.accent);
      
      const items = Object.entries(f.count).map(([k, v]) => [k, v]);
      AV.pills(ctx, P, 20, g.y + g.size + 50, c.w - 40, 'count (num → freq)', items, { hi: null, miss: null });
    }
    
    if (f.phase === 'bucket' || f.phase === 'gather') {
      const items = f.freq.map((v, i) => [`freq ${i}`, '[' + v.join(', ') + ']']).filter((v, i) => i > 0);
      AV.pills(ctx, P, 20, 150, c.w - 40, 'buckets (index = frequency)', items, { hi: null, miss: null });
    }
    
    if (f.phase === 'gather') {
      const resRow = AV.row(ctx, P, f.res, { cw: c.w, y: 34, max: 40, style: () => ({ fill: P.surface2, stroke: P.ok }) });
      if (f.res.length > 0) D.text(ctx, 'res', resRow.left - 24, resRow.y + resRow.size / 2 + 0.5, { color: P.text, size: 13, align: 'right', weight: 600, mono: true });
    }
  },
});

defineAlgo('01_arrays_hashing', {
  title: 'Encode and Decode Strings', short: 'Encode/Decode',
  idea: 'To encode, we can prefix each string with its length and a special character (like `#`). This clearly defines boundaries. To decode, we read the length, find the `#`, and slice out the exact number of characters.',
  complexity: 'Time O(N) · Space O(N)',
  input: 'leet, code', hint: 'strings',
  code: [
    'def encode(strs):',
    '    res = ""',
    '    for s in strs:',
    '        res += str(len(s)) + "#" + s',
    '    return res',
    '',
    'def decode(s):',
    '    res, i = [], 0',
    '    while i < len(s):',
    '        j = i',
    '        while s[j] != "#":',
    '            j += 1',
    '        length = int(s[i:j])',
    '        res.append(s[j + 1 : j + 1 + length])',
    '        i = j + 1 + length',
    '    return res',
  ],
  parse(str) { return { strs: str.split(',').map(s => s.trim().replace(/^['"]|['"]$/g, '')).filter(x => x) }; },
  run({ strs }) {
    const { F, snap } = avRecorder();
    const s = { strs, enc: '', dec: [], phase: 'enc', i: -1, vars: {} };
    snap(1, 'Phase 1: Encode strings', s);
    for (let i = 0; i < strs.length; i++) {
      const str = strs[i];
      s.i = i; s.vars.s = `'${str}'`;
      const chunk = `${str.length}#${str}`;
      s.enc += chunk;
      s.vars.res = `'${s.enc}'`;
      snap(2, `Encode <code>'${str}'</code> as <code>'${chunk}'</code> and append.`, s);
    }
    s.i = -1;
    s.phase = 'dec'; s.vars = { s: `'${s.enc}'`, res: '[]', i: 0 };
    snap(3, 'Phase 2: Decode the string', s);
    
    let i = 0;
    while (i < s.enc.length) {
      let j = i;
      while (s.enc[j] !== '#') j++;
      const len = parseInt(s.enc.slice(i, j), 10);
      s.vars.i = i; s.vars.j = j; s.vars.length = len;
      snap(4, `Found <code>#</code> at index ${j}. Length is ${len}.`, s);
      const str = s.enc.slice(j + 1, j + 1 + len);
      s.dec.push(str);
      i = j + 1 + len;
      s.vars.res = '[' + s.dec.map(x => `'${x}'`).join(', ') + ']';
      s.vars.i = i;
      snap(5, `Extracted <code>'${str}'</code>. Move <code>i</code> to ${i}.`, s);
    }
    snap(6, 'Decoding complete.', s);
    return F;
  },
  height: () => 280,
  draw(ctx, c, f, P) {
    if (f.phase === 'enc') {
      const g = AV.row(ctx, P, f.strs.map(x => `'${x}'`), { cw: c.w, y: 34, style: i => i === f.i ? { fill: P.alpha('accent', .25), stroke: P.accent } : i < f.i ? { fade: true } : {} });
      if (f.i >= 0) AV.ptr(ctx, P, g, f.i, 'i', P.accent);
      
      if (f.enc.length > 0) {
        const resRow = AV.row(ctx, P, [f.enc], { cw: c.w, y: 140, style: () => ({ fill: P.surface2, stroke: P.ok }) });
        D.text(ctx, 'encoded', resRow.left - 24, resRow.y + resRow.size / 2 + 0.5, { color: P.text, size: 13, align: 'right', weight: 600, mono: true });
      }
    } else {
      const encRow = AV.row(ctx, P, [f.enc], { cw: c.w, y: 34, style: () => ({ fill: P.surface2, stroke: P.accent }) });
      D.text(ctx, 'encoded', encRow.left - 24, encRow.y + encRow.size / 2 + 0.5, { color: P.text, size: 13, align: 'right', weight: 600, mono: true });
      
      const resRow = AV.row(ctx, P, f.dec.map(x => `'${x}'`), { cw: c.w, y: 140, max: 40, style: () => ({ fill: P.surface2, stroke: P.ok }) });
      if (f.dec.length > 0) D.text(ctx, 'decoded', resRow.left - 24, resRow.y + resRow.size / 2 + 0.5, { color: P.text, size: 13, align: 'right', weight: 600, mono: true });
    }
  },
});

defineAlgo('01_arrays_hashing', {
  title: 'Product of Array Except Self', short: 'Product Except Self',
  idea: 'We can solve this in O(n) without division. We compute a running prefix product and store it in our result array. Then we compute a running postfix product from right to left, multiplying it into the result.',
  complexity: 'Time O(N) · Space O(1) (excluding output array)',
  input: '1, 2, 3, 4', hint: 'numbers',
  code: [
    'def productExceptSelf(nums):',
    '    res = [1] * len(nums)',
    '    ',
    '    prefix = 1',
    '    for i in range(len(nums)):',
    '        res[i] = prefix',
    '        prefix *= nums[i]',
    '    ',
    '    postfix = 1',
    '    for i in range(len(nums) - 1, -1, -1):',
    '        res[i] *= postfix',
    '        postfix *= nums[i]',
    '    return res',
  ],
  parse(s) { return { nums: avNums(s, 10) }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    const res = Array(nums.length).fill(1);
    const s = { nums, res: [...res], phase: 'prefix', i: -1, prefix: 1, postfix: 1, vars: {} };
    snap(1, 'Initialize result array with 1s and prefix with 1.', s);
    
    for (let i = 0; i < nums.length; i++) {
      s.i = i; s.vars.i = i;
      s.res[i] = s.prefix;
      s.res = [...s.res];
      snap(2, `<code>res[${i}] = prefix = ${s.prefix}</code>.`, s);
      s.prefix *= nums[i];
      s.vars.prefix = s.prefix;
      snap(3, `Multiply prefix by <code>nums[${i}]</code> (${nums[i]}) -> ${s.prefix}.`, s);
    }
    
    s.phase = 'postfix'; s.i = -1;
    snap(4, 'Start second pass from right to left with postfix = 1.', s);
    for (let i = nums.length - 1; i >= 0; i--) {
      s.i = i; s.vars.i = i;
      s.res[i] *= s.postfix;
      s.res = [...s.res];
      snap(5, `Multiply <code>res[${i}]</code> by postfix ${s.postfix} -> ${s.res[i]}.`, s);
      s.postfix *= nums[i];
      s.vars.postfix = s.postfix;
      snap(6, `Multiply postfix by <code>nums[${i}]</code> (${nums[i]}) -> ${s.postfix}.`, s);
    }
    
    s.i = -1;
    s.vars.result = '[' + s.res.join(', ') + ']';
    snap(7, 'Done. We have the product of all elements except self.', s);
    return F;
  },
  height: () => 250,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 34, style: i => i === f.i ? { fill: P.alpha('accent', .25), stroke: P.accent } : {} });
    if (f.i >= 0) AV.ptr(ctx, P, g, f.i, 'i', P.accent);
    
    const r = AV.row(ctx, P, f.res, { cw: c.w, y: 120, max: 40, style: i => i === f.i ? { fill: P.alpha('ok', .25), stroke: P.ok } : f.phase === 'postfix' && i > f.i ? { fill: P.surface2, stroke: P.ok } : f.phase === 'postfix' ? { fill: P.surface2, stroke: P.text } : i < f.i ? { fill: P.surface2, stroke: P.text } : { fade: true } });
    D.text(ctx, 'res', r.left - 24, r.y + r.size / 2 + 0.5, { color: P.text, size: 13, align: 'right', weight: 600, mono: true });
    if (f.i >= 0) AV.ptr(ctx, P, r, f.i, 'i', P.ok);
    
    const items = [];
    if (f.phase === 'prefix') items.push(['prefix', String(f.prefix)]);
    if (f.phase === 'postfix') items.push(['postfix', String(f.postfix)]);
    AV.pills(ctx, P, 20, r.y + r.size + 50, c.w - 40, 'variables', items, { hi: null, miss: null });
  },
});

defineAlgo('01_arrays_hashing', {
  title: 'Valid Sudoku', short: 'Valid Sudoku',
  idea: 'Check rows, columns, and 3x3 boxes. A hash set for each ensures no duplicates. We can do it in one pass.',
  complexity: 'Time O(1) (81 cells) · Space O(1) (hash sets)',
  input: '53..7....,6..195...,.98....6.,8...6...3,4..8.3..1,7...2...6,.6....28.,...419..5,....8..79', hint: 'comma-separated rows',
  code: [
    'def isValidSudoku(board):',
    '    rows, cols, boxes = collections.defaultdict(set), collections.defaultdict(set), collections.defaultdict(set)',
    '    for r in range(9):',
    '        for c in range(9):',
    '            if board[r][c] == ".": continue',
    '            val = board[r][c]',
    '            box = (r // 3, c // 3)',
    '            if val in rows[r] or val in cols[c] or val in boxes[box]:',
    '                return False',
    '            rows[r].add(val)',
    '            cols[c].add(val)',
    '            boxes[box].add(val)',
    '    return True',
  ],
  parse(str) { return { board: str.split(',').map(s => s.trim()) }; },
  run({ board }) {
    const { F, snap } = avRecorder();
    const rows = Array.from({length: 9}, () => new Set());
    const cols = Array.from({length: 9}, () => new Set());
    const boxes = Array.from({length: 9}, () => new Set());
    
    const s = { board, r: -1, c: -1, phase: 'scan', vars: {} };
    snap(1, 'Initialize sets for rows, columns, and 3x3 boxes.', s);
    
    for (let r = 0; r < 9; r++) {
      for (let c = 0; c < 9; c++) {
        const val = board[r][c];
        s.r = r; s.c = c; s.vars.val = val !== '.' ? `'${val}'` : `'.'`; s.vars.r = r; s.vars.c = c;
        if (val === '.') continue;
        const boxIdx = Math.floor(r / 3) * 3 + Math.floor(c / 3);
        s.vars.box = boxIdx;
        snap(2, `Check cell (${r}, ${c}): <b>${val}</b>. Box index: ${boxIdx}.`, s);
        if (rows[r].has(val) || cols[c].has(val) || boxes[boxIdx].has(val)) {
          snap(3, `Duplicate found! Invalid Sudoku.`, s);
          return F;
        }
        rows[r].add(val);
        cols[c].add(val);
        boxes[boxIdx].add(val);
      }
    }
    s.r = -1; s.c = -1; s.vars.result = 'True';
    snap(4, 'Finished scanning all cells. No duplicates found, Sudoku is valid.', s);
    return F;
  },
  height: () => 220,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.board, { cw: c.w, y: 34, style: i => i === f.r ? { fill: P.alpha('accent', .25), stroke: P.accent } : {} });
    if (f.r >= 0) AV.ptr(ctx, P, g, f.r, 'r', P.accent);
  },
});

defineAlgo('01_arrays_hashing', {
  title: 'Longest Consecutive Sequence', short: 'Longest Consecutive',
  idea: 'Put all numbers in a HashSet. Iterate through the set. A number is the start of a sequence if <code>n - 1</code> is not in the set. Then we count upwards as long as consecutive numbers exist.',
  complexity: 'Time O(N) · Space O(N)',
  input: '100, 4, 200, 1, 3, 2', hint: 'numbers',
  code: [
    'def longestConsecutive(nums):',
    '    numSet = set(nums)',
    '    longest = 0',
    '    for n in nums:',
    '        if (n - 1) not in numSet:',
    '            length = 0',
    '            while (n + length) in numSet:',
    '                length += 1',
    '            longest = max(length, longest)',
    '    return longest',
  ],
  parse(str) { return { nums: str.split(',').map(Number) }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    const set = new Set(nums);
    let longest = 0;
    
    const s = { nums, i: -1, phase: 'init', vars: {} };
    snap(1, 'Add all numbers to a hash set.', s);
    
    for (let i = 0; i < nums.length; i++) {
      const n = nums[i];
      s.i = i; s.phase = 'scan';
      s.vars.n = n; s.vars.longest = longest; delete s.vars.length;
      snap(2, `Check if <b>${n}</b> is the start of a sequence.`, s);
      
      if (!set.has(n - 1)) {
        s.phase = 'start';
        snap(3, `<code>${n} - 1</code> (${n - 1}) is not in set. <b>${n}</b> is the start of a sequence!`, s);
        let length = 0;
        
        while (set.has(n + length)) {
          s.phase = 'count';
          s.vars.length = length;
          snap(4, `Found <b>${n + length}</b>. Increase length to ${length + 1}.`, s);
          length += 1;
        }
        
        s.phase = 'end';
        s.vars.length = length;
        snap(5, `<code>${n + length}</code> is not in set. Sequence ends with length ${length}.`, s);
        
        longest = Math.max(longest, length);
        s.vars.longest = longest;
        snap(6, `Update longest to ${longest}.`, s);
      } else {
        s.phase = 'skip';
        snap(7, `<code>${n} - 1</code> (${n - 1}) is in the set. Skip.`, s);
      }
    }
    
    s.i = -1; s.phase = 'done'; s.vars.result = longest;
    snap(8, 'Done. The length of the longest consecutive sequence is ' + longest + '.', s);
    return F;
  },
  height: () => 220,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 34, style: i => i === f.i ? { fill: P.alpha('accent', .25), stroke: P.accent } : {} });
    if (f.i >= 0) AV.ptr(ctx, P, g, f.i, 'i', P.accent);
    
    const items = [];
    if (f.vars.n !== undefined) items.push(['n', String(f.vars.n)]);
    if (f.vars.length !== undefined) items.push(['length', String(f.vars.length)]);
    if (f.vars.longest !== undefined) items.push(['longest', String(f.vars.longest)]);
    AV.pills(ctx, P, 20, 120, c.w - 40, 'variables', items, { hi: null, miss: null });
  },
});

defineAlgo('01_arrays_hashing', {
  title: 'Next Permutation', short: 'Next Permutation',
  idea: '1. Find the first decreasing element from the end (pivot). 2. Find the element just larger than the pivot from the end. 3. Swap them. 4. Reverse the elements after the pivot.',
  complexity: 'Time O(N) · Space O(1)',
  input: '1, 3, 5, 4, 2', hint: 'numbers',
  code: [
    'def nextPermutation(nums):',
    '    i = len(nums) - 2',
    '    while i >= 0 and nums[i] >= nums[i + 1]:',
    '        i -= 1',
    '    if i >= 0:',
    '        j = len(nums) - 1',
    '        while nums[j] <= nums[i]:',
    '            j -= 1',
    '        nums[i], nums[j] = nums[j], nums[i]',
    '    ',
    '    left, right = i + 1, len(nums) - 1',
    '    while left < right:',
    '        nums[left], nums[right] = nums[right], nums[left]',
    '        left += 1; right -= 1',
  ],
  parse(str) { return { nums: str.split(',').map(Number) }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    nums = [...nums];
    
    const s = { nums, i: -1, j: -1, left: -1, right: -1, phase: 'scan1' };
    snap(1, 'Start scanning from right to find the first decreasing element.', s);
    
    let i = nums.length - 2;
    while (i >= 0 && nums[i] >= nums[i + 1]) {
      s.i = i;
      snap(2, `<code>nums[${i}]</code> (${nums[i]}) >= <code>nums[${i+1}]</code> (${nums[i+1]}). Move left.`, s);
      i--;
    }
    
    s.i = i;
    if (i >= 0) {
      s.phase = 'scan2';
      snap(3, `Found first decreasing element at index ${i}: <b>${nums[i]}</b>. Now find the smallest element to its right that is larger.`, s);
      let j = nums.length - 1;
      while (nums[j] <= nums[i]) {
        s.j = j;
        snap(4, `<code>nums[${j}]</code> (${nums[j]}) <= <code>nums[${i}]</code> (${nums[i]}). Move left.`, s);
        j--;
      }
      s.j = j;
      snap(5, `Found element at index ${j}: <b>${nums[j]}</b>. Swap them.`, s);
      
      let temp = nums[i];
      nums[i] = nums[j];
      nums[j] = temp;
      s.nums = [...nums];
      snap(6, 'Swapped elements.', s);
    } else {
      snap(3, 'Array is in descending order. It is the last permutation.', s);
    }
    
    s.phase = 'reverse';
    s.j = -1;
    let left = i + 1, right = nums.length - 1;
    s.left = left; s.right = right;
    snap(7, `Reverse the sub-array from index ${left} to ${right} to get the next lexicographical permutation.`, s);
    
    while (left < right) {
      s.left = left; s.right = right;
      let temp = nums[left];
      nums[left] = nums[right];
      nums[right] = temp;
      s.nums = [...nums];
      snap(8, `Swapped elements at ${left} and ${right}.`, s);
      left++;
      right--;
    }
    
    s.left = -1; s.right = -1; s.i = -1; s.phase = 'done';
    snap(9, 'Done.', s);
    return F;
  },
  height: () => 160,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 34, style: idx => {
      if (f.phase === 'scan1' || f.phase === 'scan2') {
        if (idx === f.i) return { fill: P.alpha('accent', .25), stroke: P.accent };
        if (idx === f.j) return { fill: P.alpha('ok', .25), stroke: P.ok };
      }
      if (f.phase === 'reverse') {
        if (idx === f.left || idx === f.right) return { fill: P.alpha('accent', .25), stroke: P.accent };
      }
      return {};
    }});
    
    if (f.phase === 'scan1' || f.phase === 'scan2') {
      if (f.i >= 0) AV.ptr(ctx, P, g, f.i, 'i', P.accent);
      if (f.j >= 0) AV.ptr(ctx, P, g, f.j, 'j', P.ok);
    } else if (f.phase === 'reverse') {
      if (f.left >= 0 && f.left < f.right) AV.ptr(ctx, P, g, f.left, 'L', P.accent);
      if (f.right >= 0 && f.left < f.right) AV.ptr(ctx, P, g, f.right, 'R', P.accent);
    }
  },
});

defineAlgo('01_arrays_hashing', {
  title: 'Isomorphic Strings', short: 'Isomorphic',
  idea: 'Maintain a mapping from characters in <code>s</code> to characters in <code>t</code>. Also keep track of which characters in <code>t</code> are already mapped to, to prevent two different characters from <code>s</code> mapping to the same character in <code>t</code>.',
  complexity: 'Time O(N) · Space O(N)',
  input: 'paper, title', hint: 's, t',
  code: [
    'def isIsomorphic(s, t):',
    '    if len(s) != len(t): return False',
    '    mapST = {}',
    '    mapTS = {}',
    '    for c1, c2 in zip(s, t):',
    '        if ((c1 in mapST and mapST[c1] != c2) or',
    '            (c2 in mapTS and mapTS[c2] != c1)):',
    '            return False',
    '        mapST[c1] = c2',
    '        mapTS[c2] = c1',
    '    return True',
  ],
  parse(str) { 
    const p = str.split(',').map(s => s.trim());
    return { s: p[0] || '', t: p[1] || '' };
  },
  run({ s, t }) {
    const { F, snap } = avRecorder();
    if (s.length !== t.length) {
      snap(1, 'Lengths are different. They cannot be isomorphic.', { s: s.split(''), t: t.split(''), i: -1, phase: 'done', mapST: {}, mapTS: {}, vars: { result: 'False' } });
      return F;
    }
    const mapST = {};
    const mapTS = {};
    
    const state = { s: s.split(''), t: t.split(''), i: -1, mapST, mapTS, phase: 'scan', vars: {} };
    snap(1, 'Initialize two hash maps: <code>mapST</code> (s → t) and <code>mapTS</code> (t → s).', state);
    
    for (let i = 0; i < s.length; i++) {
      const c1 = s[i];
      const c2 = t[i];
      state.i = i;
      state.vars.c1 = `'${c1}'`;
      state.vars.c2 = `'${c2}'`;
      snap(2, `Check characters at index ${i}: <code>s[${i}]</code> = '${c1}' and <code>t[${i}]</code> = '${c2}'.`, state);
      
      if ((c1 in mapST && mapST[c1] !== c2) || (c2 in mapTS && mapTS[c2] !== c1)) {
        let msg = '';
        if (c1 in mapST && mapST[c1] !== c2) {
            msg = `<code>'${c1}'</code> in <code>s</code> is already mapped to <code>'${mapST[c1]}'</code> in <code>t</code>, not <code>'${c2}'</code>.`;
        } else {
            msg = `<code>'${c2}'</code> in <code>t</code> is already mapped from <code>'${mapTS[c2]}'</code> in <code>s</code>, not <code>'${c1}'</code>.`;
        }
        snap(3, `Conflict found! ${msg} Not isomorphic.`, state);
        state.vars.result = 'False';
        return F;
      }
      
      mapST[c1] = c2;
      mapTS[c2] = c1;
      snap(4, `Map <code>'${c1}'</code> to <code>'${c2}'</code> in mapST, and <code>'${c2}'</code> to <code>'${c1}'</code> in mapTS.`, state);
    }
    
    state.i = -1;
    state.phase = 'done';
    state.vars.result = 'True';
    snap(5, 'Successfully checked all characters without conflicts. The strings are isomorphic.', state);
    return F;
  },
  height: () => 240,
  draw(ctx, c, f, P) {
    const sRow = AV.row(ctx, P, f.s, { cw: c.w, y: 34, style: i => i === f.i ? { fill: P.alpha('accent', .25), stroke: P.accent } : {} });
    D.text(ctx, 's', sRow.left - 24, sRow.y + sRow.size / 2 + 0.5, { color: P.text, size: 13, align: 'right', weight: 600, mono: true });
    
    const tRow = AV.row(ctx, P, f.t, { cw: c.w, y: 90, style: i => i === f.i ? { fill: P.alpha('ok', .25), stroke: P.ok } : {} });
    D.text(ctx, 't', tRow.left - 24, tRow.y + tRow.size / 2 + 0.5, { color: P.text, size: 13, align: 'right', weight: 600, mono: true });
    
    if (f.i >= 0) {
      AV.ptr(ctx, P, sRow, f.i, 'i', P.accent, true); 
      AV.ptr(ctx, P, tRow, f.i, 'i', P.ok);
    }
    
    const stItems = Object.entries(f.mapST).map(([k, v]) => [`'${k}'`, `'${v}'`]);
    AV.pills(ctx, P, 20, 150, c.w / 2 - 30, 'mapST (s → t)', stItems, { hi: null, miss: null });
    
    const tsItems = Object.entries(f.mapTS).map(([k, v]) => [`'${k}'`, `'${v}'`]);
    AV.pills(ctx, P, c.w / 2 + 10, 150, c.w / 2 - 30, 'mapTS (t → s)', tsItems, { hi: null, miss: null });
  },
});

/* ============================================================ 02 · two pointers == */
defineAlgo('02_two_pointers', {
  title: 'Two pointers on a sorted array', short: 'Pair sum (sorted)',
  idea: 'Because the array is sorted, a sum that is too small can only grow by moving <code>lo</code> right, and a sum that is too big can only shrink by moving <code>hi</code> left. Each step rules out one element for good.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 3, 4, 6, 8, 11, 14 ; 14', hint: 'sorted numbers ; target',
  code: [
    'def pair_sum(nums, target):',
    '    lo, hi = 0, len(nums) - 1',
    '    while lo < hi:',
    '        s = nums[lo] + nums[hi]',
    '        if s == target: return [lo, hi]',
    '        if s < target: lo += 1     # need a bigger sum',
    '        else: hi -= 1              # need a smaller sum',
    '    return []',
  ],
  parse(s) { const [a, t] = avParts(s); const nums = avNums(a, 14); if (nums.some((x, i) => i && x < nums[i - 1])) throw new Error('The numbers must be sorted ascending'); return { nums, target: avNum(t, 'the target') }; },
  run({ nums, target }) {
    const { F, snap } = avRecorder();
    let lo = 0, hi = nums.length - 1;
    const s = () => ({ nums, lo, hi, done: null, vars: { lo, hi, target } });
    snap(1, 'Start with one pointer at each end.', s());
    while (lo < hi) {
      const sum = nums[lo] + nums[hi];
      snap(3, `${nums[lo]} + ${nums[hi]} = <b>${sum}</b>.`, { ...s(), vars: { lo, hi, sum, target } });
      if (sum === target) { snap(4, `Found it: indices ${lo} and ${hi}.`, { ...s(), done: [lo, hi], vars: { lo, hi, sum, result: `[${lo}, ${hi}]` } }); return F; }
      if (sum < target) { snap(5, `${sum} < ${target}: everything paired with ${nums[lo]} is too small, so drop it and move <code>lo</code> right.`, { ...s(), vars: { lo, hi, sum, target } }); lo++; }
      else { snap(6, `${sum} > ${target}: everything paired with ${nums[hi]} is too big, so drop it and move <code>hi</code> left.`, { ...s(), vars: { lo, hi, sum, target } }); hi--; }
    }
    snap(7, 'The pointers met: no pair adds up to the target.', { ...s(), vars: { result: '[]' } });
    return F;
  },
  height: () => 200,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 50, style: i => f.done?.includes(i) ? { fill: P.alpha('ok', .3), stroke: P.ok } : (i === f.lo || i === f.hi) ? { stroke: P.accent, fill: P.alpha('accent', .2) } : (i < f.lo || i > f.hi) ? { fade: true } : {} });
    if (f.lo < f.nums.length) AV.ptr(ctx, P, g, f.lo, 'lo', P.series[0]);
    if (f.hi >= 0) AV.ptr(ctx, P, g, f.hi, 'hi', P.series[1], f.lo === f.hi ? 1 : 0);
  },
});

defineAlgo('02_two_pointers', {
  title: 'Container With Most Water', short: 'Most water',
  idea: 'The water between two lines is limited by the shorter one. Moving the taller line inward can never help (width shrinks, height cannot rise above the short line), so always move the <b>shorter</b> side.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 8, 6, 2, 5, 4, 8, 3, 7', hint: 'heights',
  code: [
    'def max_area(h):',
    '    lo, hi, best = 0, len(h) - 1, 0',
    '    while lo < hi:',
    '        area = min(h[lo], h[hi]) * (hi - lo)',
    '        best = max(best, area)',
    '        if h[lo] < h[hi]: lo += 1',
    '        else: hi -= 1',
    '    return best',
  ],
  parse(s) { const h = avNums(s, 14, 'heights'); if (h.some(x => x < 0)) throw new Error('Heights must be ≥ 0'); return { h }; },
  run({ h }) {
    const { F, snap } = avRecorder();
    let lo = 0, hi = h.length - 1, best = 0, bestPair = null;
    snap(1, 'Start with the widest container.', { h, lo, hi, best, bestPair, vars: { lo, hi, best } });
    while (lo < hi) {
      const area = Math.min(h[lo], h[hi]) * (hi - lo);
      snap(3, `min(${h[lo]}, ${h[hi]}) × ${hi - lo} = <b>${area}</b>.`, { h, lo, hi, best, bestPair, vars: { lo, hi, area, best } });
      if (area > best) { best = area; bestPair = [lo, hi]; }
      snap(4, `Best so far: ${best}.`, { h, lo, hi, best, bestPair, vars: { lo, hi, area, best } });
      if (h[lo] < h[hi]) { snap(5, `Left line (${h[lo]}) is shorter, so it limits the height: move <code>lo</code> in.`, { h, lo, hi, best, bestPair, vars: { lo, hi, best } }); lo++; }
      else { snap(6, `Right line (${h[hi]}) is not taller than the left: move <code>hi</code> in.`, { h, lo, hi, best, bestPair, vars: { lo, hi, best } }); hi--; }
    }
    snap(7, `Done: the most water is <b>${best}</b>.`, { h, lo, hi, best, bestPair, vars: { best } });
    return F;
  },
  height: () => 270,
  draw(ctx, c, f, P) {
    const top = 30, bottom = c.h - 30;
    const g = AV.bars(ctx, P, f.h, { cw: c.w, top, bottom, style: i => (i === f.lo || i === f.hi) ? { fill: P.accent } : { fill: P.alpha('faint', .5) } });
    const water = (a, b, col, fillA) => {
      const lvl = Math.min(f.h[a], f.h[b]) / g.mx * (bottom - top), x1 = g.x(a), x2 = g.x(b);
      ctx.fillStyle = P.alpha(col, fillA); ctx.fillRect(x1, bottom - lvl, x2 - x1, lvl);
      ctx.strokeStyle = col; ctx.lineWidth = 1.5; ctx.strokeRect(x1, bottom - lvl, x2 - x1, lvl);
    };
    if (f.bestPair) water(...f.bestPair, P.ok, .08);
    if (f.lo < f.hi) water(f.lo, f.hi, P.series[0], .25);
  },
});

/* =========================================================== 03 · sliding window == */
defineAlgo('03_sliding_window', {
  title: 'Longest substring without repeating characters', short: 'No repeats',
  idea: 'Grow the window to the right one character at a time. When the new character already appears inside the window, jump <code>left</code> just past its previous position, so the window is always valid.',
  complexity: 'Time O(n) · Space O(alphabet)',
  input: 'abcabcbbxyz', hint: 'a string (up to 18 characters)',
  code: [
    'def length_of_longest(s):',
    '    last, left, best = {}, 0, 0',
    '    for right, ch in enumerate(s):',
    '        if ch in last and last[ch] >= left:',
    '            left = last[ch] + 1        # jump past the repeat',
    '        last[ch] = right',
    '        best = max(best, right - left + 1)',
    '    return best',
  ],
  parse(s) { const str = String(s || '').replace(/\s+/g, ''); if (!str) throw new Error('Enter a string'); if (str.length > 18) throw new Error('Use at most 18 characters'); return { str: [...str] }; },
  run({ str }) {
    const { F, snap } = avRecorder();
    const last = {}; let left = 0, best = 0, bestWin = null;
    const S = (right, extra = {}) => ({ str, left, right, best, bestWin, last: Object.entries(last), ...extra });
    snap(1, 'Empty window.', { ...S(-1), vars: { left, best } });
    str.forEach((ch, right) => {
      snap(2, `Extend the window to include <code>${ch}</code> at ${right}.`, { ...S(right), vars: { left, right, ch, best } });
      if (ch in last && last[ch] >= left) {
        const old = last[ch];
        snap(3, `<code>${ch}</code> is already in the window at index ${old}.`, { ...S(right, { dup: old }), vars: { left, right, ch, best } });
        left = old + 1;
        snap(4, `Move <code>left</code> to ${left}, just past the earlier <code>${ch}</code>.`, { ...S(right), vars: { left, right, ch, best } });
      }
      last[ch] = right;
      if (right - left + 1 > best) { best = right - left + 1; bestWin = [left, right]; }
      snap(6, `Window “${str.slice(left, right + 1).join('')}” has length ${right - left + 1}. Best: <b>${best}</b>.`, { ...S(right), vars: { left, right, best } });
    });
    snap(7, `The longest substring without repeats has length <b>${best}</b>.`, { ...S(str.length - 1), vars: { best } });
    return F;
  },
  height: () => 230,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.str, { cw: c.w, y: 60, max: 42, style: i => i === f.dup ? { stroke: P.err, fill: P.alpha('err', .2) } : i === f.right ? { stroke: P.accent } : (f.right >= 0 && (i < f.left || i > f.right)) ? { fade: true } : {} });
    if (f.bestWin) { ctx.strokeStyle = P.ok; ctx.lineWidth = 1.5; ctx.setLineDash([4, 4]); D.rrect(ctx, g.x(f.bestWin[0]) - g.size / 2 - 7, g.y - 8, g.x(f.bestWin[1]) - g.x(f.bestWin[0]) + g.size + 14, g.size + 16, 12); ctx.stroke(); ctx.setLineDash([]); }
    if (f.right >= 0) AV.bracket(ctx, P, g, f.left, f.right, P.accent, 'window');
    if (f.right >= 0) { AV.ptr(ctx, P, g, f.left, 'left', P.series[0]); AV.ptr(ctx, P, g, f.right, 'right', P.series[1], f.left === f.right ? 1 : 0); }
    AV.pills(ctx, P, 20, g.y + g.size + 58, c.w - 40, 'last seen index', f.last);
  },
});

/* ============================================================== 04 · prefix sum == */
defineAlgo('04_prefix_sum', {
  title: 'Subarray Sum Equals K', short: 'Sum equals K',
  idea: 'A subarray <code>(i, j]</code> sums to k exactly when <code>prefix[j] − prefix[i] = k</code>. So at each position, count how many earlier prefix sums equal <code>prefix − k</code>. Works with negative numbers, where a sliding window fails.',
  complexity: 'Time O(n) · Space O(n)',
  input: '1, 2, 1, -1, 2, 3 ; 3', hint: 'numbers ; k',
  code: [
    'def subarray_sum(nums, k):',
    '    count, prefix = 0, 0',
    '    seen = {0: 1}                  # prefix sum -> times seen',
    '    for x in nums:',
    '        prefix += x',
    '        count += seen.get(prefix - k, 0)',
    '        seen[prefix] = seen.get(prefix, 0) + 1',
    '    return count',
  ],
  parse(s) { const [a, k] = avParts(s); return { nums: avNums(a, 12), k: avNum(k, 'k') }; },
  run({ nums, k }) {
    const { F, snap } = avRecorder();
    const seen = new Map([[0, 1]]); let count = 0, prefix = 0; const prefs = [];
    const S = (i, extra = {}) => ({ nums, i, prefs: [...prefs], seen: [...seen.entries()], count, ...extra });
    snap(2, 'The empty prefix has sum 0, seen once.', { ...S(-1), vars: { k, count } });
    nums.forEach((x, i) => {
      prefix += x; prefs.push(prefix);
      snap(4, `Add ${x}: prefix sum is now <b>${prefix}</b>.`, { ...S(i), vars: { i, x, prefix, k, count } });
      const add = seen.get(prefix - k) || 0; count += add;
      snap(5, add ? `${prefix} − ${k} = ${prefix - k} was seen ${add} time${add > 1 ? 's' : ''}: that many subarrays ending here sum to ${k}.` : `${prefix} − ${k} = ${prefix - k} has not been seen, so no subarray ending here sums to ${k}.`, { ...S(i, { look: prefix - k, found: !!add }), vars: { i, prefix, need: prefix - k, count } });
      seen.set(prefix, (seen.get(prefix) || 0) + 1);
      snap(6, `Record prefix ${prefix}.`, { ...S(i), vars: { i, prefix, count } });
    });
    snap(7, `Total subarrays summing to ${k}: <b>${count}</b>.`, { ...S(nums.length - 1), vars: { count } });
    return F;
  },
  height: () => 270,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 40, max: 46, style: i => i === f.i ? { stroke: P.accent } : i > f.i ? { fade: true } : {} });
    D.text(ctx, 'nums', g.left - 10, g.y + g.size / 2, { color: P.dim, size: 11, align: 'right' });
    const pv = f.nums.map((_, i) => f.prefs[i] ?? '');
    const g2 = AV.row(ctx, P, pv, { cw: c.w, y: g.y + g.size + 26, max: 46, index: false, style: i => i === f.i ? { stroke: P.series[0], fill: P.alpha(P.series[0], .2) } : i > f.i ? { fade: true } : {} });
    D.text(ctx, 'prefix', g2.left - 10, g2.y + g2.size / 2, { color: P.dim, size: 11, align: 'right' });
    AV.pills(ctx, P, 20, g2.y + g2.size + 30, c.w - 40, 'seen  (prefix sum → count)', f.seen, { hi: f.found ? f.look : null, miss: f.look != null && !f.found ? f.look : null });
  },
});

/* ============================================================ 05 · binary search == */
defineAlgo('05_binary_search', {
  title: 'Binary search', short: 'Exact match',
  idea: 'Compare with the middle element and throw away the half that cannot contain the target. Each step halves the search space: 1 million elements take at most 20 steps.',
  complexity: 'Time O(log n) · Space O(1)',
  input: '2, 5, 8, 12, 16, 23, 38, 56, 72, 91 ; 23', hint: 'sorted numbers ; target',
  code: [
    'def search(nums, target):',
    '    lo, hi = 0, len(nums) - 1',
    '    while lo <= hi:',
    '        mid = (lo + hi) // 2',
    '        if nums[mid] == target: return mid',
    '        if nums[mid] < target: lo = mid + 1',
    '        else: hi = mid - 1',
    '    return -1',
  ],
  parse(s) { const [a, t] = avParts(s); const nums = avNums(a, 16); if (nums.some((x, i) => i && x < nums[i - 1])) throw new Error('The numbers must be sorted ascending'); return { nums, target: avNum(t, 'the target') }; },
  run({ nums, target }) {
    const { F, snap } = avRecorder();
    let lo = 0, hi = nums.length - 1, steps = 0;
    snap(1, 'The target could be anywhere.', { nums, lo, hi, mid: null, vars: { lo, hi, target } });
    while (lo <= hi) {
      const mid = (lo + hi) >> 1; steps++;
      snap(3, `Middle of [${lo}, ${hi}] is index ${mid}, value <b>${nums[mid]}</b>.`, { nums, lo, hi, mid, vars: { lo, mid, hi, target, steps } });
      if (nums[mid] === target) { snap(4, `Found ${target} at index ${mid} in ${steps} step${steps > 1 ? 's' : ''}.`, { nums, lo, hi, mid, found: mid, vars: { result: mid, steps } }); return F; }
      if (nums[mid] < target) { snap(5, `${nums[mid]} < ${target}: the target must be to the right. Discard indices ${lo}–${mid}.`, { nums, lo, hi, mid, vars: { lo, mid, hi, target, steps } }); lo = mid + 1; }
      else { snap(6, `${nums[mid]} > ${target}: the target must be to the left. Discard indices ${mid}–${hi}.`, { nums, lo, hi, mid, vars: { lo, mid, hi, target, steps } }); hi = mid - 1; }
    }
    snap(7, `${target} is not in the array (${steps} steps).`, { nums, lo, hi, mid: null, vars: { result: -1, steps } });
    return F;
  },
  height: () => 200,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 50, style: i => i === f.found ? { fill: P.alpha('ok', .35), stroke: P.ok } : i === f.mid ? { stroke: P.accent, fill: P.alpha('accent', .25) } : (i < f.lo || i > f.hi) ? { fade: true } : {} });
    if (f.lo <= f.hi) AV.bracket(ctx, P, g, f.lo, f.hi, P.series[0], 'still possible');
    if (f.lo < f.nums.length) AV.ptr(ctx, P, g, Math.min(f.lo, f.nums.length - 1), 'lo', P.series[0]);
    if (f.mid != null) AV.ptr(ctx, P, g, f.mid, 'mid', P.accent, f.mid === f.lo ? 1 : 0);
    if (f.hi >= 0) AV.ptr(ctx, P, g, f.hi, 'hi', P.series[1], f.hi === f.mid || f.hi === f.lo ? 2 : 0);
  },
});

defineAlgo('05_binary_search', {
  title: 'Lower bound: first position where nums[i] ≥ target', short: 'Lower bound',
  idea: 'Many problems ask for a <b>boundary</b>, not an exact match. Keep the invariant “the answer is in <code>[lo, hi]</code>”: if <code>nums[mid] ≥ target</code>, mid might be the answer so keep it; otherwise discard it. The loop ends when <code>lo == hi</code>.',
  complexity: 'Time O(log n) · Space O(1)',
  input: '1, 2, 4, 4, 4, 7, 9, 12 ; 4', hint: 'sorted numbers ; target',
  code: [
    'def lower_bound(nums, target):',
    '    lo, hi = 0, len(nums)          # answer is in [lo, hi]',
    '    while lo < hi:',
    '        mid = (lo + hi) // 2',
    '        if nums[mid] >= target:',
    '            hi = mid               # mid could be the answer',
    '        else:',
    '            lo = mid + 1           # mid is too small',
    '    return lo',
  ],
  parse(s) { const [a, t] = avParts(s); const nums = avNums(a, 16); if (nums.some((x, i) => i && x < nums[i - 1])) throw new Error('The numbers must be sorted ascending'); return { nums, target: avNum(t, 'the target') }; },
  run({ nums, target }) {
    const { F, snap } = avRecorder();
    let lo = 0, hi = nums.length;
    snap(1, `The answer is somewhere in [0, ${hi}] (${hi} means “after everything”).`, { nums, lo, hi, mid: null, vars: { lo, hi, target } });
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      snap(3, `mid = ${mid}, nums[mid] = <b>${nums[mid]}</b>.`, { nums, lo, hi, mid, vars: { lo, mid, hi } });
      if (nums[mid] >= target) { snap(5, `${nums[mid]} ≥ ${target}: the first such position is at mid or earlier, so <code>hi = ${mid}</code>.`, { nums, lo, hi, mid, vars: { lo, mid, hi } }); hi = mid; }
      else { snap(7, `${nums[mid]} < ${target}: mid and everything before it are too small, so <code>lo = ${mid + 1}</code>.`, { nums, lo, hi, mid, vars: { lo, mid, hi } }); lo = mid + 1; }
    }
    snap(8, `lo == hi == ${lo}: the first index with nums[i] ≥ ${target}${lo < nums.length ? ` (value ${nums[lo]})` : ' (none: insert at the end)'}.`, { nums, lo, hi, mid: null, found: lo, vars: { result: lo } });
    return F;
  },
  height: () => 200,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 50, style: i => i === f.found ? { fill: P.alpha('ok', .35), stroke: P.ok } : i === f.mid ? { stroke: P.accent, fill: P.alpha('accent', .25) } : (i < f.lo || i >= f.hi) ? { fade: true } : {} });
    if (f.lo < f.hi) AV.bracket(ctx, P, g, f.lo, Math.min(f.hi, f.nums.length) - 1, P.series[0], 'answer is in here (or at hi)');
    const at = i => Math.min(i, f.nums.length - 1);
    AV.ptr(ctx, P, g, at(f.lo), f.lo >= f.nums.length ? 'lo (end)' : 'lo', P.series[0]);
    if (f.mid != null) AV.ptr(ctx, P, g, f.mid, 'mid', P.accent, 1);
    AV.ptr(ctx, P, g, at(f.hi), f.hi >= f.nums.length ? 'hi (end)' : 'hi', P.series[1], 2);
  },
});

/* =================================================================== 06 · stack == */
defineAlgo('06_stack', {
  title: 'Daily Temperatures with a monotonic stack', short: 'Monotonic stack',
  idea: 'Keep a stack of days still waiting for a warmer day, with temperatures <b>decreasing</b> from bottom to top. A warmer day pops everything colder than itself and answers them all at once. Each index is pushed and popped once.',
  complexity: 'Time O(n) · Space O(n)',
  input: '73, 74, 75, 71, 69, 72, 76, 73', hint: 'temperatures',
  code: [
    'def daily_temperatures(t):',
    '    ans = [0] * len(t)',
    '    stack = []                     # indices, temps decreasing',
    '    for i, temp in enumerate(t):',
    '        while stack and t[stack[-1]] < temp:',
    '            j = stack.pop()',
    '            ans[j] = i - j',
    '        stack.append(i)',
    '    return ans',
  ],
  parse(s) { return { t: avNums(s, 12, 'temperatures') }; },
  run({ t }) {
    const { F, snap } = avRecorder();
    const ans = t.map(() => 0), stack = [];
    const S = (i, extra = {}) => ({ t, i, ans: [...ans], stack: [...stack], ...extra });
    snap(2, 'Nothing is waiting yet.', { ...S(-1), vars: {} });
    t.forEach((temp, i) => {
      snap(3, `Day ${i}: ${temp}°.`, { ...S(i), vars: { i, temp } });
      while (stack.length && t[stack[stack.length - 1]] < temp) {
        const j = stack[stack.length - 1];
        snap(4, `Day ${j} (${t[j]}°) is colder than today, so today is its answer.`, { ...S(i, { pop: j }), vars: { i, temp, top: j } });
        stack.pop(); ans[j] = i - j;
        snap(6, `ans[${j}] = ${i} − ${j} = <b>${i - j}</b>.`, { ...S(i, { filled: j }), vars: { i, j, wait: i - j } });
      }
      stack.push(i);
      snap(7, `Push day ${i}: it waits for something warmer than ${temp}°.`, { ...S(i), vars: { i, stack: stack.length } });
    });
    snap(8, `Days left on the stack never get warmer: their answer stays 0.`, { ...S(t.length - 1), vars: { ans: `[${ans.join(', ')}]` } });
    return F;
  },
  height: () => 330,
  draw(ctx, c, f, P) {
    const g = AV.bars(ctx, P, f.t, { cw: c.w - 130, top: 30, bottom: 190, style: i => i === f.pop ? { fill: P.err } : i === f.i ? { fill: P.accent } : f.stack.includes(i) ? { fill: P.alpha(P.series[0], .75) } : { fill: P.alpha('faint', .45) } });
    const ga = AV.row(ctx, P, f.ans, { cw: c.w - 130, y: 230, max: 40, index: false, style: i => i === f.filled ? { stroke: P.ok, fill: P.alpha('ok', .3) } : {} });
    D.text(ctx, 'ans', ga.left - 8, ga.y + ga.size / 2, { color: P.dim, size: 11, align: 'right' });
    void g;
    AV.stack(ctx, P, c.w - 110, 20, 90, 'stack (top ↑)', f.stack.map(j => `day ${j}: ${f.t[j]}°`));
  },
});

defineAlgo('06_stack', {
  title: 'Valid Parentheses', short: 'Brackets',
  idea: 'An opening bracket waits on the stack. A closing bracket must match the most recent unmatched opener, which is exactly the top of the stack.',
  complexity: 'Time O(n) · Space O(n)',
  input: '{[()()]}(]', hint: 'brackets such as ([{}])',
  code: [
    'def is_valid(s):',
    "    pairs = {')': '(', ']': '[', '}': '{'}",
    '    stack = []',
    '    for ch in s:',
    '        if ch in "([{": stack.append(ch)',
    '        elif not stack or stack.pop() != pairs[ch]:',
    '            return False',
    '    return not stack',
  ],
  parse(s) { const str = String(s || '').replace(/\s+/g, ''); if (!/^[()[\]{}]+$/.test(str)) throw new Error('Use only ( ) [ ] { }'); if (str.length > 18) throw new Error('Use at most 18 brackets'); return { str: [...str] }; },
  run({ str }) {
    const { F, snap } = avRecorder();
    const pairs = { ')': '(', ']': '[', '}': '{' }, stack = [];
    snap(2, 'Empty stack.', { str, i: -1, stack: [], vars: {} });
    for (let i = 0; i < str.length; i++) {
      const ch = str[i];
      if ('([{'.includes(ch)) { stack.push(ch); snap(4, `<code>${ch}</code> opens: push it.`, { str, i, stack: [...stack], vars: { i, ch } }); continue; }
      const top = stack[stack.length - 1];
      if (!stack.length || top !== pairs[ch]) {
        snap(5, !stack.length ? `<code>${ch}</code> closes, but nothing is open.` : `<code>${ch}</code> needs <code>${pairs[ch]}</code> on top, but the top is <code>${top}</code>.`, { str, i, stack: [...stack], bad: i, vars: { i, ch, top: top ?? '—' } });
        snap(6, 'Invalid string.', { str, i, stack: [...stack], bad: i, vars: { result: false } });
        return F;
      }
      stack.pop();
      snap(5, `<code>${ch}</code> matches <code>${top}</code> on top: pop it.`, { str, i, stack: [...stack], vars: { i, ch } });
    }
    snap(7, stack.length ? `${stack.length} opener${stack.length > 1 ? 's were' : ' was'} never closed: invalid.` : 'Every opener was closed in order: valid.', { str, i: str.length - 1, stack: [...stack], ok: !stack.length, vars: { result: !stack.length } });
    return F;
  },
  height: () => 250,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.str, { cw: c.w - 120, y: 60, max: 40, style: i => i === f.bad ? { stroke: P.err, fill: P.alpha('err', .25) } : i === f.i ? { stroke: P.accent } : i < f.i ? { fade: true } : {} });
    if (f.i >= 0) AV.ptr(ctx, P, g, f.i, 'ch', P.accent);
    AV.stack(ctx, P, c.w - 100, 20, 80, 'stack (top ↑)', f.stack);
    if (f.ok !== undefined) D.text(ctx, f.ok ? '✓ valid' : '✕ invalid', 20, c.h - 20, { color: f.ok ? P.ok : P.err, size: 15, weight: 700 });
  },
});

/* ============================================================== 07 · deque == */
defineAlgo('07_queue_deque', {
  title: 'Sliding Window Maximum with a monotonic deque', short: 'Window max',
  idea: 'The deque holds indices whose values <b>decrease</b> from front to back. A new value evicts smaller values from the back (they can never be a maximum again); the front drops out once it leaves the window. The front is always the current maximum.',
  complexity: 'Time O(n) · Space O(k)',
  input: '1, 3, -1, -3, 5, 3, 6, 7 ; 3', hint: 'numbers ; window size k',
  code: [
    'def max_sliding_window(nums, k):',
    '    dq, out = deque(), []          # indices, values decreasing',
    '    for i, x in enumerate(nums):',
    '        while dq and nums[dq[-1]] <= x:',
    '            dq.pop()               # can never be a max again',
    '        dq.append(i)',
    '        if dq[0] <= i - k:',
    '            dq.popleft()           # front slid out of the window',
    '        if i >= k - 1:',
    '            out.append(nums[dq[0]])',
    '    return out',
  ],
  parse(s) { const [a, k] = avParts(s); const nums = avNums(a, 14); const kk = avNum(k, 'k'); if (kk < 1 || kk > nums.length || !Number.isInteger(kk)) throw new Error('k must be a whole number between 1 and the array length'); return { nums, k: kk }; },
  run({ nums, k }) {
    const { F, snap } = avRecorder();
    const dq = [], out = [];
    const S = (i, extra = {}) => ({ nums, k, i, dq: [...dq], out: [...out], ...extra });
    nums.forEach((x, i) => {
      snap(2, `Next value ${x} at index ${i}.`, { ...S(i), vars: { i, x } });
      while (dq.length && nums[dq[dq.length - 1]] <= x) {
        const j = dq[dq.length - 1];
        snap(3, `${nums[j]} (index ${j}) ≤ ${x}: it can never be a window maximum while ${x} is around.`, { ...S(i, { evict: j }), vars: { i, x } });
        dq.pop();
      }
      dq.push(i);
      snap(5, `Append index ${i} to the back.`, { ...S(i), vars: { i, x, front: nums[dq[0]] } });
      if (dq[0] <= i - k) { snap(6, `Front index ${dq[0]} is outside the window [${i - k + 1}, ${i}].`, { ...S(i, { expired: dq[0] }), vars: { i } }); dq.shift(); }
      if (i >= k - 1) { out.push(nums[dq[0]]); snap(9, `Window [${i - k + 1}, ${i}]: max is the front, <b>${nums[dq[0]]}</b>.`, { ...S(i), vars: { i, max: nums[dq[0]] } }); }
    });
    snap(10, `Maxima: [${out.join(', ')}].`, { ...S(nums.length - 1), vars: { out: `[${out.join(', ')}]` } });
    return F;
  },
  height: () => 300,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 50, max: 46, style: i => i === f.evict || i === f.expired ? { stroke: P.err, fill: P.alpha('err', .2) } : i === f.i ? { stroke: P.accent } : (i < f.i - f.k + 1 || i > f.i) ? { fade: true } : {} });
    AV.bracket(ctx, P, g, Math.max(0, f.i - f.k + 1), f.i, P.series[0], 'window');
    D.text(ctx, 'deque (front → back)', 20, g.y + g.size + 40, { color: P.dim, size: 11.5, weight: 650 });
    f.dq.forEach((j, n) => {
      const x = 20 + n * 78, y = g.y + g.size + 52;
      ctx.fillStyle = n === 0 ? P.alpha('ok', .3) : P.surface2; D.rrect(ctx, x, y, 70, 30, 7); ctx.fill();
      ctx.strokeStyle = n === 0 ? P.ok : P.strong; ctx.lineWidth = 1.2; ctx.stroke();
      D.text(ctx, `${f.nums[j]} @${j}`, x + 35, y + 15, { color: P.text, size: 12, align: 'center', mono: true, weight: 600 });
    });
    AV.pills(ctx, P, 20, g.y + g.size + 108, c.w - 40, 'output (max of each window)', f.out.map(v => [v]));
  },
});

/* ============================================================= 08 · linked list == */
defineAlgo('08_linked_list', {
  title: 'Reverse a linked list', short: 'Reverse Linked List',
  idea: 'Walk the list once and flip each <code>next</code> pointer to point backwards. Save <code>nxt</code> before flipping, otherwise the rest of the list is lost.',
  complexity: 'Time O(n) · Space O(1)',
  input: '1, 2, 3, 4, 5', hint: 'node values',
  code: [
    'def reverse(head):',
    '    prev, curr = None, head',
    '    while curr:',
    '        nxt = curr.next',
    '        curr.next = prev           # flip the pointer',
    '        prev = curr',
    '        curr = nxt',
    '    return prev',
  ],
  parse(s) { return { vals: avNums(s, 8, 'nodes') }; },
  run({ vals }) {
    const { F, snap } = avRecorder();
    const n = vals.length, next = vals.map((_, i) => (i + 1 < n ? i + 1 : -1));
    let prev = -1, curr = 0, nxt = null;
    const S = (extra = {}) => ({ vals, next: [...next], prev, curr, nxt, ...extra });
    snap(1, '<code>prev</code> starts as None, <code>curr</code> at the head.', S({ vars: { prev: 'None', curr: vals[0] } }));
    while (curr !== -1) {
      nxt = next[curr];
      snap(3, `Save <code>nxt</code> = ${nxt === -1 ? 'None' : vals[nxt]} before breaking the link.`, S({ vars: { prev: prev === -1 ? 'None' : vals[prev], curr: vals[curr], nxt: nxt === -1 ? 'None' : vals[nxt] } }));
      next[curr] = prev;
      snap(4, `Point ${vals[curr]}.next back to ${prev === -1 ? 'None' : vals[prev]}.`, S({ flipped: curr, vars: { curr: vals[curr] } }));
      prev = curr; curr = nxt;
      snap(6, 'Advance both pointers.', S({ vars: { prev: vals[prev], curr: curr === -1 ? 'None' : vals[curr] } }));
    }
    snap(7, `<code>curr</code> fell off the end; <code>prev</code> (${vals[prev]}) is the new head.`, S({ head: prev, vars: { new_head: vals[prev] } }));
    return F;
  },
  height: () => 230,
  draw(ctx, c, f, P) {
    const n = f.vals.length, slot = (c.w - 40) / (n + 2), y = 110, r = Math.min(24, slot * .3);
    const xAt = i => 20 + (i + 1.5) * slot;
    D.text(ctx, 'None', xAt(-1), y, { color: P.faint, size: 12, align: 'center', mono: true });
    D.text(ctx, 'None', xAt(n), y, { color: P.faint, size: 12, align: 'center', mono: true });
    f.next.forEach((to, i) => {
      if (to === -1) {
        const tx = i === f.next.length - 1 && to === -1 && f.next[i] === -1 && !(f.prev >= i) ? xAt(n) : xAt(-1);
        if (i === n - 1 && f.curr !== -1 && f.prev < i && f.flipped !== i) AV.arrow(ctx, xAt(i) + r, y, xAt(n) - 20, y, P.strong);
        else { ctx.beginPath(); ctx.moveTo(xAt(i), y - r); ctx.quadraticCurveTo((xAt(i) + xAt(-1)) / 2, y - 70, xAt(-1) + 10, y - 12); ctx.strokeStyle = P.ok; ctx.lineWidth = 2; ctx.stroke(); }
        void tx;
      } else if (to === i + 1) AV.arrow(ctx, xAt(i) + r, y, xAt(to) - r - 2, y, P.strong);
      else { ctx.beginPath(); ctx.moveTo(xAt(i), y - r); ctx.quadraticCurveTo((xAt(i) + xAt(to)) / 2, y - 60, xAt(to) + 6, y - r - 4); ctx.strokeStyle = P.ok; ctx.lineWidth = 2; ctx.stroke(); D.text(ctx, '◂', xAt(to) + 8, y - r - 6, { color: P.ok, size: 12, align: 'center' }); }
    });
    f.vals.forEach((v, i) => AV.node(ctx, P, xAt(i), y, r, v, { fill: i === f.head ? P.alpha('ok', .3) : i === f.curr ? P.alpha('accent', .25) : null, stroke: i === f.flipped ? P.ok : i === f.curr ? P.accent : null }));
    const lab = (i, text, col, lvl) => D.text(ctx, `▲ ${text}`, xAt(i), y + r + 16 + lvl * 16, { color: col, size: 11.5, align: 'center', weight: 700, mono: true });
    lab(f.prev === -1 ? -1 : f.prev, 'prev', P.series[0], 0);
    lab(f.curr === -1 ? n : f.curr, 'curr', P.accent, f.curr === f.prev ? 1 : 0);
    if (f.nxt != null) lab(f.nxt === -1 ? n : f.nxt, 'nxt', P.series[1], (f.nxt === f.curr || (f.nxt === -1 && f.curr === -1)) ? 2 : 1);
  },
});

defineAlgo('08_linked_list', {
  title: 'Floyd cycle detection (tortoise and hare)', short: 'Linked List Cycle',
  idea: '<code>slow</code> moves one step, <code>fast</code> moves two. With no cycle, fast reaches the end. With a cycle, fast gains one step per round on slow inside the loop, so they must meet.',
  complexity: 'Time O(n) · Space O(1)',
  input: '3, 2, 0, -4, 5, 9 ; 2', hint: 'node values ; index the tail links back to (-1 = no cycle)',
  code: [
    'def has_cycle(head):',
    '    slow = fast = head',
    '    while fast and fast.next:',
    '        slow = slow.next',
    '        fast = fast.next.next',
    '        if slow is fast:',
    '            return True',
    '    return False',
  ],
  parse(s) { const [a, p] = avParts(s); const vals = avNums(a, 9, 'nodes'); const pos = p === undefined || p === '' ? -1 : avNum(p, 'the cycle index'); if (pos >= vals.length || pos < -1) throw new Error('Cycle index must be -1 or a valid node index'); return { vals, pos }; },
  run({ vals, pos }) {
    const { F, snap } = avRecorder();
    const n = vals.length, nx = i => (i + 1 < n ? i + 1 : pos);
    let slow = 0, fast = 0, round = 0;
    snap(1, 'Both start at the head.', { vals, pos, slow, fast, vars: { slow: 0, fast: 0 } });
    while (fast !== -1 && nx(fast) !== -1) {
      slow = nx(slow); fast = nx(nx(fast)); round++;
      snap(4, `Round ${round}: slow → node ${slow}, fast → node ${fast}.`, { vals, pos, slow, fast, vars: { round, slow, fast } });
      if (slow === fast) { snap(6, `They met at node ${slow}: there is a cycle.`, { vals, pos, slow, fast, met: true, vars: { result: true } }); return F; }
    }
    snap(7, 'Fast reached the end: no cycle.', { vals, pos, slow, fast: -1, vars: { result: false } });
    return F;
  },
  height: () => 240,
  draw(ctx, c, f, P) {
    const n = f.vals.length, slot = (c.w - 60) / n, y = 90, r = Math.min(22, slot * .3);
    const xAt = i => 30 + (i + .5) * slot;
    for (let i = 0; i + 1 < n; i++) AV.arrow(ctx, xAt(i) + r, y, xAt(i + 1) - r - 2, y, P.strong);
    if (f.pos >= 0) {
      ctx.beginPath(); ctx.moveTo(xAt(n - 1), y + r); ctx.bezierCurveTo(xAt(n - 1), y + 90, xAt(f.pos), y + 90, xAt(f.pos), y + r + 4);
      ctx.strokeStyle = P.series[4]; ctx.lineWidth = 2; ctx.stroke();
      D.text(ctx, '▲', xAt(f.pos), y + r + 8, { color: P.series[4], size: 11, align: 'center' });
    } else D.text(ctx, '→ None', xAt(n - 1) + r + 26, y, { color: P.faint, size: 12, align: 'center', mono: true });
    f.vals.forEach((v, i) => AV.node(ctx, P, xAt(i), y, r, v, { fill: f.met && i === f.slow ? P.alpha('ok', .35) : null, stroke: i === f.slow ? P.series[0] : i === f.fast ? P.accent : null }));
    if (f.slow >= 0) D.text(ctx, '🐢 slow', xAt(f.slow), y - r - 16, { color: P.series[0], size: 11.5, align: 'center', weight: 700 });
    if (f.fast >= 0) D.text(ctx, '🐇 fast', xAt(f.fast), y - r - (f.fast === f.slow ? 32 : 16), { color: P.accent, size: 11.5, align: 'center', weight: 700 });
  },
});

/* ============================================================ trees (helpers) == */
function avTreeFromLevel(str, max = 15) {
  const toks = String(str || '').split(/[\s,]+/).filter(Boolean);
  if (!toks.length) throw new Error('Enter the tree in level order, e.g. 1, 2, 3, null, 4');
  if (toks.length > max) throw new Error(`Use at most ${max} entries`);
  if (/^null$/i.test(toks[0])) throw new Error('The root cannot be null');
  const nodes = [], q = [];
  const mk = t => { if (/^null$/i.test(t)) return -1; const v = Number(t); if (!Number.isFinite(v)) throw new Error(`“${t}” is not a number`); nodes.push({ val: v, left: -1, right: -1 }); return nodes.length - 1; };
  q.push(mk(toks[0]));
  let i = 1;
  while (q.length && i < toks.length) {
    const cur = q.shift();
    for (const side of ['left', 'right']) {
      if (i >= toks.length) break;
      const id = mk(toks[i++]);
      nodes[cur][side] = id;
      if (id !== -1) q.push(id);
    }
  }
  return nodes;
}
function avLayoutBinary(nodes, root = 0) {
  const pos = {};
  let rank = 0, depthMax = 0;
  const walk = (id, d) => { if (id === -1 || id == null) return; walk(nodes[id].left, d + 1); pos[id] = { r: rank++, d }; depthMax = Math.max(depthMax, d); walk(nodes[id].right, d + 1); };
  walk(root, 0);
  return { pos, count: rank, depth: depthMax };
}
function avDrawBinary(ctx, P, c, nodes, lay, style, { top = 36, gapY = 58, r = 18 } = {}) {
  const x = id => 20 + (lay.pos[id].r + .5) * (c.w - 40) / Math.max(1, lay.count), y = id => top + lay.pos[id].d * gapY;
  nodes.forEach((nd, id) => {
    if (!lay.pos[id]) return;
    ['left', 'right'].forEach(side => { const ch = nd[side]; if (ch !== -1 && ch != null && lay.pos[ch]) D.line(ctx, x(id), y(id), x(ch), y(ch), (style(ch).edge) || P.strong, 1.5); });
  });
  nodes.forEach((nd, id) => { if (lay.pos[id]) { const st = style(id) || {}; if (st.hidden) return; AV.node(ctx, P, x(id), y(id), r, st.label ?? nd.val, st); } });
  return { x, y };
}

/* ======================================================= 09 · backtracking == */
defineAlgo('09_recursion_backtracking', {
  title: 'Subsets: the take / skip decision tree', short: 'Subsets',
  idea: 'Every element gets two branches: <b>take</b> it or <b>skip</b> it. Each root-to-leaf path is one subset, so there are 2ⁿ leaves. Backtracking = undo the choice (<code>path.pop()</code>) before exploring the other branch.',
  complexity: 'Time O(n · 2ⁿ) · Space O(n) recursion depth',
  input: '1, 2, 3', hint: 'up to 4 distinct numbers',
  code: [
    'def subsets(nums):',
    '    res, path = [], []',
    '    def dfs(i):',
    '        if i == len(nums):',
    '            res.append(path[:]); return',
    '        path.append(nums[i]); dfs(i + 1)   # take nums[i]',
    '        path.pop(); dfs(i + 1)             # skip nums[i]',
    '    dfs(0)',
    '    return res',
  ],
  parse(s) { return { nums: avNums(s, 4) }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    const res = [], path = [], visited = [];
    const S = (id, extra = {}) => ({ nums, cur: id, path: [...path], res: res.map(r => [...r]), visited: [...visited], ...extra });
    const dfs = (i, id) => {
      visited.push(id);
      snap(2, `dfs(${i}) with path [${path.join(', ')}].`, { ...S(id), vars: { i, path: `[${path.join(', ')}]` } });
      if (i === nums.length) { res.push([...path]); snap(4, `Leaf: record subset [${path.join(', ')}].`, { ...S(id, { leaf: id }), vars: { found: res.length } }); return; }
      path.push(nums[i]);
      snap(5, `Take ${nums[i]}.`, { ...S(id, { edge: `${id}T` }), vars: { i, path: `[${path.join(', ')}]` } });
      dfs(i + 1, `${id}T`);
      path.pop();
      snap(6, `Backtrack: remove ${nums[i]}, then explore skipping it.`, { ...S(id, { edge: `${id}S` }), vars: { i, path: `[${path.join(', ')}]` } });
      dfs(i + 1, `${id}S`);
    };
    dfs(0, 'r');
    snap(8, `All ${res.length} subsets found.`, { ...S(null), vars: { subsets: res.length } });
    return F;
  },
  height: (w, last) => 70 + last.nums.length * 62 + 60,
  draw(ctx, c, f, P) {
    const n = f.nums.length, gapY = 62, top = 30;
    const posOf = id => { const d = id.length - 1; let idx = 0; for (const ch of id.slice(1)) idx = idx * 2 + (ch === 'S' ? 1 : 0); return [20 + (idx + .5) * (c.w - 40) / 2 ** d, top + d * gapY]; };
    const all = ['r'];
    for (let d = 0; d < n; d++) all.slice().filter(x => x.length - 1 === d).forEach(x => all.push(`${x}T`, `${x}S`));
    const vis = new Set(f.visited);
    all.forEach(id => {
      if (id === 'r') return;
      const parent = id.slice(0, -1), [x1, y1] = posOf(parent), [x2, y2] = posOf(id), took = id.endsWith('T');
      if (!vis.has(id) && f.edge !== id) { D.line(ctx, x1, y1, x2, y2, P.alpha('faint', .25), 1, [3, 4]); return; }
      D.line(ctx, x1, y1, x2, y2, took ? P.ok : P.alpha('dim', .7), f.edge === id ? 3 : 1.6);
      if (n <= 3 || id.length <= 3) D.text(ctx, took ? `+${f.nums[id.length - 2]}` : 'skip', (x1 + x2) / 2 + (took ? -10 : 10), (y1 + y2) / 2 - 4, { color: took ? P.ok : P.faint, size: 10, align: 'center', mono: true });
    });
    all.forEach(id => {
      if (!vis.has(id)) return;
      const [x, y] = posOf(id), subset = [...id.slice(1)].map((ch, k) => ch === 'T' ? f.nums[k] : null).filter(v => v !== null);
      const leaf = id.length - 1 === n, rr = leaf ? Math.min(16, (c.w - 40) / 2 ** n / 2.4) : 14;
      AV.node(ctx, P, x, y, rr, leaf ? '' : '', { fill: id === f.cur ? P.alpha('accent', .35) : leaf ? P.alpha('ok', .25) : null, stroke: id === f.cur ? P.accent : null });
      if (leaf) D.text(ctx, `{${subset.join(',')}}`, x, y + rr + 11, { color: P.text, size: n > 3 ? 9 : 10.5, align: 'center', mono: true, weight: 600 });
    });
    D.text(ctx, `path = [${f.path.join(', ')}]`, 20, c.h - 16, { color: P.accent, size: 12.5, mono: true, weight: 700 });
  },
});

/* ==================================================================== 10 · trees == */
defineAlgo('10_trees', {
  title: 'Tree traversals', short: 'Traversals',
  idea: 'The same tree, four visiting orders. Pre-, in- and post-order are depth-first (recursion, i.e. a stack) and differ only in <b>when</b> the node is visited relative to its children. Level order is breadth-first and uses a queue.',
  complexity: 'Time O(n) · Space O(h) for DFS, O(width) for BFS',
  input: '1, 2, 3, 4, 5, null, 6, null, null, 7', hint: 'level order, null for missing children',
  variants: [['in', 'Inorder'], ['pre', 'Preorder'], ['post', 'Postorder'], ['level', 'Level order']],
  code: v => v === 'level' ? [
    'def level_order(root):',
    '    q = deque([root])',
    '    while q:',
    '        node = q.popleft()',
    '        visit(node)',
    '        if node.left: q.append(node.left)',
    '        if node.right: q.append(node.right)',
  ] : [
    `def ${v === 'in' ? 'inorder' : v === 'pre' ? 'preorder' : 'postorder'}(node):`,
    '    if not node: return',
    ...(v === 'pre' ? ['    visit(node)', '    preorder(node.left)', '    preorder(node.right)']
      : v === 'in' ? ['    inorder(node.left)', '    visit(node)', '    inorder(node.right)']
        : ['    postorder(node.left)', '    postorder(node.right)', '    visit(node)']),
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }, v) {
    const { F, snap } = avRecorder();
    const out = [], stack = [];
    const S = (cur, extra = {}) => ({ nodes, cur, out: [...out], stack: stack.map(id => nodes[id].val), ...extra });
    if (v === 'level') {
      const q = [0];
      snap(1, 'Put the root in the queue.', { ...S(null, { queue: [nodes[0].val] }), vars: {} });
      while (q.length) {
        const id = q.shift();
        snap(3, `Dequeue ${nodes[id].val}.`, { ...S(id, { queue: q.map(x => nodes[x].val) }), vars: { node: nodes[id].val } });
        out.push(id);
        snap(4, `Visit ${nodes[id].val}.`, { ...S(id, { queue: q.map(x => nodes[x].val) }), vars: { visited: out.length } });
        for (const side of ['left', 'right']) if (nodes[id][side] !== -1) { q.push(nodes[id][side]); snap(side === 'left' ? 5 : 6, `Enqueue its ${side} child ${nodes[nodes[id][side]].val}.`, { ...S(id, { queue: q.map(x => nodes[x].val) }), vars: {} }); }
      }
      snap(2, 'Queue is empty: done.', { ...S(null, { queue: [] }), vars: { order: out.map(i => nodes[i].val).join(' → ') } });
      return F;
    }
    const lines = v === 'pre' ? { visit: 2, left: 3, right: 4 } : v === 'in' ? { left: 2, visit: 3, right: 4 } : { left: 2, right: 3, visit: 4 };
    const go = id => {
      stack.push(id);
      snap(0, `Call on ${nodes[id].val}.`, { ...S(id), vars: { node: nodes[id].val, depth: stack.length } });
      const steps = v === 'pre' ? ['visit', 'left', 'right'] : v === 'in' ? ['left', 'visit', 'right'] : ['left', 'right', 'visit'];
      for (const step of steps) {
        if (step === 'visit') { out.push(id); snap(lines.visit, `Visit <b>${nodes[id].val}</b>.`, { ...S(id), vars: { node: nodes[id].val, visited: out.length } }); }
        else {
          const ch = nodes[id][step];
          snap(lines[step], ch === -1 ? `${nodes[id].val} has no ${step} child.` : `Go ${step} from ${nodes[id].val}.`, { ...S(id), vars: { node: nodes[id].val } });
          if (ch !== -1) go(ch);
        }
      }
      stack.pop();
    };
    go(0);
    snap(1, 'Traversal complete.', { ...S(null), vars: { order: out.map(i => nodes[i].val).join(' → ') } });
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 90; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes), order = new Map(f.out.map((id, k) => [id, k + 1]));
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({ fill: id === f.cur ? P.alpha('accent', .35) : order.has(id) ? P.alpha('ok', .22) : null, stroke: id === f.cur ? P.accent : order.has(id) ? P.ok : null, sub: order.has(id) ? `#${order.get(id)}` : null }));
    const y = c.h - 46;
    D.text(ctx, `visited: ${f.out.map(id => f.nodes[id].val).join(' → ') || '—'}`, 20, y, { color: P.ok, size: 12.5, mono: true, weight: 700 });
    if (f.queue) D.text(ctx, `queue: [${f.queue.join(', ')}]`, 20, y + 22, { color: P.series[0], size: 12, mono: true });
    else D.text(ctx, `call stack: ${f.stack.join(' → ') || '—'}`, 20, y + 22, { color: P.series[0], size: 12, mono: true });
  },
});

/* ====================================================================== 11 · BST == */
defineAlgo('11_binary_search_tree', {
  title: 'Binary search tree: insert and search', short: 'Insert + search',
  idea: 'Every node keeps smaller keys on its left and larger keys on its right. Insert and search both walk one root-to-leaf path, choosing a side at each node, so they cost O(height): O(log n) when balanced, O(n) when the input is already sorted.',
  complexity: 'Time O(h) per operation · Space O(n)',
  input: '8, 3, 10, 1, 6, 14, 4, 7, 13 ; 7', hint: 'values to insert ; value to search',
  code: [
    'def insert(root, v):',
    '    if not root: return Node(v)',
    '    if v < root.val: root.left = insert(root.left, v)',
    '    else: root.right = insert(root.right, v)',
    '    return root',
    '',
    'def search(root, v):',
    '    while root and root.val != v:',
    '        root = root.left if v < root.val else root.right',
    '    return root',
  ],
  parse(s) { const [a, q] = avParts(s); return { vals: avNums(a, 12, 'values'), q: avNum(q, 'a value to search') }; },
  run({ vals, q }) {
    const { F, snap } = avRecorder();
    const nodes = [];
    const S = (extra = {}) => ({ nodes: nodes.map(n => ({ ...n })), ...extra });
    vals.forEach(v => {
      if (!nodes.length) { nodes.push({ val: v, left: -1, right: -1 }); snap(1, `Empty tree: ${v} becomes the root.`, S({ cur: 0, vars: { insert: v } })); return; }
      let id = 0; const path = [];
      for (;;) {
        path.push(id);
        const goLeft = v < nodes[id].val;
        snap(goLeft ? 2 : 3, `${v} ${goLeft ? '<' : '≥'} ${nodes[id].val}: go ${goLeft ? 'left' : 'right'}.`, S({ cur: id, path: [...path], vars: { insert: v, at: nodes[id].val } }));
        const side = goLeft ? 'left' : 'right';
        if (nodes[id][side] === -1) { nodes.push({ val: v, left: -1, right: -1 }); nodes[id][side] = nodes.length - 1; snap(1, `Empty spot: attach ${v} as the ${side} child of ${nodes[id].val}.`, S({ cur: nodes.length - 1, path, vars: { insert: v } })); break; }
        id = nodes[id][side];
      }
    });
    let id = 0; const path = [];
    snap(6, `Search for ${q}.`, S({ cur: 0, vars: { search: q } }));
    while (id !== -1 && nodes[id].val !== q) {
      path.push(id);
      const goLeft = q < nodes[id].val;
      snap(8, `${q} ${goLeft ? '<' : '>'} ${nodes[id].val}: go ${goLeft ? 'left' : 'right'}.`, S({ cur: id, path: [...path], vars: { search: q, at: nodes[id].val } }));
      id = nodes[id][goLeft ? 'left' : 'right'];
    }
    if (id !== -1) path.push(id);
    snap(9, id === -1 ? `Reached an empty spot: ${q} is not in the tree (${path.length} comparisons).` : `Found ${q} after ${path.length} comparisons.`, S({ found: id, path, vars: { result: id === -1 ? 'None' : q, comparisons: path.length } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes), onPath = new Set(f.path || []);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({ fill: id === f.found ? P.alpha('ok', .4) : id === f.cur ? P.alpha('accent', .35) : onPath.has(id) ? P.alpha('accent', .12) : null, stroke: id === f.found ? P.ok : id === f.cur ? P.accent : onPath.has(id) ? P.accent : null, edge: onPath.has(id) ? P.accent : null }));
  },
});

/* ===================================================================== 12 · heap == */
defineAlgo('12_heap_priority_queue', {
  title: 'Min-heap: push and pop', short: 'Min-heap',
  idea: 'A heap is a complete binary tree stored in an array: children of <code>i</code> are at <code>2i+1</code> and <code>2i+2</code>. <b>Push</b> appends and sifts the new item up while it is smaller than its parent. <b>Pop</b> takes the root, moves the last item to the top and sifts it down.',
  complexity: 'push / pop O(log n) · peek O(1) · heapify O(n)',
  input: '5, 3, 8, 1, 9, 2, 7 ; 3', hint: 'values to push ; how many to pop',
  code: [
    'def push(heap, x):',
    '    heap.append(x); i = len(heap) - 1',
    '    while i > 0 and heap[(i - 1) // 2] > heap[i]:',
    '        swap(heap, i, (i - 1) // 2); i = (i - 1) // 2',
    '',
    'def pop(heap):',
    '    top = heap[0]; heap[0] = heap.pop()',
    '    i = 0',
    '    while a child of i is smaller than heap[i]:',
    '        c = the smaller child; swap(heap, i, c); i = c',
    '    return top',
  ],
  parse(s) { const [a, k] = avParts(s); const vals = avNums(a, 12, 'values'); const pops = k === undefined || k === '' ? 2 : avNum(k, 'a pop count'); if (pops < 0 || pops > vals.length) throw new Error('Pop count must be between 0 and the number of values'); return { vals, pops }; },
  run({ vals, pops }) {
    const { F, snap } = avRecorder();
    const h = [], popped = [];
    const S = (extra = {}) => ({ h: [...h], popped: [...popped], ...extra });
    vals.forEach(x => {
      h.push(x); let i = h.length - 1;
      snap(1, `Push ${x}: append at index ${i}.`, S({ cur: i, vars: { push: x, i } }));
      while (i > 0 && h[(i - 1) >> 1] > h[i]) {
        const p = (i - 1) >> 1;
        snap(2, `${h[i]} < parent ${h[p]}: swap up.`, S({ cmp: [i, p], vars: { i, parent: p } }));
        [h[i], h[p]] = [h[p], h[i]]; i = p;
        snap(3, 'Swapped.', S({ cur: i, vars: { i } }));
      }
      if (i > 0) snap(2, `${h[i]} ≥ parent ${h[(i - 1) >> 1]}: heap order holds.`, S({ cur: i, ok: true, vars: { i } }));
    });
    for (let k = 0; k < pops; k++) {
      const top = h[0];
      snap(6, `Pop: the minimum is the root, <b>${top}</b>.`, S({ cur: 0, vars: { top } }));
      const last = h.pop();
      popped.push(top);
      if (!h.length) { snap(10, `Heap is now empty.`, S({ vars: { popped: popped.join(', ') } })); break; }
      h[0] = last;
      snap(6, `Move the last item (${last}) to the root.`, S({ cur: 0, vars: { popped: popped.join(', ') } }));
      let i = 0;
      for (;;) {
        const l = 2 * i + 1, r = 2 * i + 2;
        let m = i;
        if (l < h.length && h[l] < h[m]) m = l;
        if (r < h.length && h[r] < h[m]) m = r;
        if (m === i) { snap(8, `No child is smaller than ${h[i]}: done sifting down.`, S({ cur: i, ok: true, vars: { i } })); break; }
        snap(8, `Smaller child ${h[m]} < ${h[i]}: swap down.`, S({ cmp: [i, m], vars: { i, child: m } }));
        [h[i], h[m]] = [h[m], h[i]]; i = m;
        snap(9, 'Swapped.', S({ cur: i, vars: { i } }));
      }
    }
    snap(10, `Popped in order: ${popped.join(', ') || '—'} (always the smallest remaining).`, S({ vars: { popped: popped.join(', ') || '—', heap: `[${h.join(', ')}]` } }));
    return F;
  },
  height: (w, last, frames) => { const n = Math.max(...frames.map(fr => fr.h.length)); return 60 + Math.floor(Math.log2(Math.max(1, n))) * 56 + 120; },
  draw(ctx, c, f, P) {
    const n = f.h.length, top = 34, gapY = 56;
    const xy = i => { const d = Math.floor(Math.log2(i + 1)), idx = i - (2 ** d - 1); return [20 + (idx + .5) * (c.w - 40) / 2 ** d, top + d * gapY]; };
    for (let i = 1; i < n; i++) { const [x1, y1] = xy((i - 1) >> 1), [x2, y2] = xy(i); D.line(ctx, x1, y1, x2, y2, P.strong, 1.5); }
    for (let i = 0; i < n; i++) {
      const [x, y] = xy(i), cmp = f.cmp?.includes(i);
      AV.node(ctx, P, x, y, 18, f.h[i], { fill: cmp ? P.alpha('err', .25) : i === f.cur ? P.alpha(f.ok ? 'ok' : 'accent', .35) : null, stroke: cmp ? P.err : i === f.cur ? (f.ok ? P.ok : P.accent) : null });
    }
    const depth = Math.floor(Math.log2(Math.max(1, n)));
    const g = AV.row(ctx, P, f.h.length ? f.h : ['—'], { cw: c.w, y: top + depth * gapY + 50, max: 38, style: i => f.cmp?.includes(i) ? { stroke: P.err } : i === f.cur ? { stroke: P.accent } : {} });
    D.text(ctx, 'array', g.left - 8, g.y + g.size / 2, { color: P.dim, size: 11, align: 'right' });
    if (f.popped.length) D.text(ctx, `popped: ${f.popped.join(', ')}`, 20, c.h - 12, { color: P.ok, size: 12, mono: true, weight: 700 });
  },
});

defineAlgo('15_advanced_graphs', {
  type: 'dom',
  title: 'Network Delay Time', short: 'Network Delay Time',
  idea: 'Dijkstra\'s algorithm. We want the time for the slowest node to receive the signal, which is the maximum shortest path from the start node `k`. We use a min-heap to always expand the closest unvisited node.',
  complexity: 'Time O((V + E) log V) · Space O(V + E)',
  input: '4; 2; 2,1,1; 2,3,1; 3,4,1', hint: 'n; k; u,v,w; ...',
  code: [
    'def networkDelayTime(times, n, k):',
    '    adj = collections.defaultdict(list)',
    '    for u, v, w in times:',
    '        adj[u].append((v, w))',
    '    ',
    '    dist = [float("inf")] * (n + 1)',
    '    dist[k] = 0',
    '    heap = [(0, k)]',
    '    while heap:',
    '        d, u = heapq.heappop(heap)',
    '        if d > dist[u]: continue',
    '        ',
    '        for v, w in adj[u]:',
    '            if d + w < dist[v]:',
    '                dist[v] = d + w',
    '                heapq.heappush(heap, (d + w, v))',
    '    ',
    '    reach = dist[1:n+1]',
    '    return max(reach) if float("inf") not in reach else -1',
  ],
  parse(str) {
    const parts = str.split(';');
    if (parts.length < 2) throw new Error("Input must contain at least n and k, separated by semicolons.");
    const n = parseInt(parts[0].trim());
    const k = parseInt(parts[1].trim());
    if (isNaN(n) || isNaN(k)) throw new Error("n and k must be integers.");
    const times = parts.slice(2).filter(x => x.trim().length > 0).map(edge => {
       const vals = edge.split(',').map(Number);
       if (vals.length !== 3 || vals.some(isNaN)) throw new Error("Edges must be in format u,v,w");
       return vals;
    });
    return { n, k, times };
  },
  run({ n, k, times }) {
    const { F, snap } = avRecorder();
    
    const adj = {};
    for(let i=1; i<=n; i++) adj[i] = [];
    for(let [u, v, w] of times) {
       if (!adj[u]) adj[u] = [];
       adj[u].push([v, w]);
    }
    
    let dist = new Array(n+1).fill('inf');
    dist[k] = 0;
    
    let heap = [[0, k]]; 
    
    const s = { n, k, adj, dist: [...dist], heap: [...heap], u: null, d: null, v: null, w: null, nd: null };
    snap(6, `Initialize dist array with infinity, except k (${k}) which is 0. Push (0, ${k}) to heap.`, s);
    
    while(heap.length > 0) {
       heap.sort((a,b) => a[0] - b[0]);
       const [d, u] = heap.shift();
       
       s.d = d; s.u = u; s.dist = [...dist]; s.heap = [...heap];
       s.v = null; s.w = null; s.nd = null;
       
       snap(9, `Pop node ${u} from heap with distance ${d}.`, s);
       
       if (d > (dist[u] === 'inf' ? Infinity : dist[u])) {
          snap(10, `Distance ${d} is stale (greater than dist[${u}]). Skip.`, s);
          continue;
       }
       
       for(let [v, w] of (adj[u] || [])) {
          s.v = v; s.w = w;
          const currentDistV = dist[v] === 'inf' ? Infinity : dist[v];
          s.nd = d + w;
          snap(13, `Check neighbor ${v} with edge weight ${w}. New distance = ${d} + ${w} = ${s.nd}.`, s);
          
          if (s.nd < currentDistV) {
             dist[v] = s.nd;
             heap.push([s.nd, v]);
             s.dist = [...dist];
             s.heap = [...heap];
             snap(15, `Found shorter path to ${v} (${s.nd} < ${currentDistV === Infinity ? 'inf' : currentDistV}). Update dist[${v}] and push to heap.`, s);
          } else {
             snap(14, `Path to ${v} (${s.nd}) is not shorter than current dist (${currentDistV === Infinity ? 'inf' : currentDistV}). Skip.`, s);
          }
       }
    }
    
    s.u = null; s.d = null; s.v = null; s.w = null; s.nd = null;
    let reachable = dist.slice(1);
    let allReached = reachable.indexOf('inf') === -1;
    let maxDist = allReached ? Math.max(...reachable) : -1;
    snap(18, `Dijkstra finished. Maximum distance is ${maxDist}.`, s);

    return F;
  },
  buildStates(parsed) {
    return this.run(parsed).map(f => ({ ...f, explTitle: 'Dijkstra’s algorithm', explText: f.note }));
  },
  renderDOM(container, s, spec) {
    const getNodesHTML = () => {
       let html = '<div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom: 20px;">';
       for(let i=1; i<=s.n; i++) {
          const isCurrent = i === s.u;
          const isNeighbor = i === s.v;
          const dStr = s.dist[i] === 'inf' ? '∞' : s.dist[i];
          let bg = 'var(--surface)';
          let border = 'var(--border)';
          
          if(isCurrent) { border = 'var(--accent)'; bg = 'rgba(56, 189, 248, 0.1)'; }
          else if(isNeighbor) { border = '#34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
          
          html += `
          <div style="padding: 10px; border: 2px solid ${border}; border-radius: 8px; background: ${bg}; text-align: center; min-width: 60px;">
             <div style="font-weight: bold; color: var(--text);">Node ${i}</div>
             <div style="font-family: var(--mono); color: ${isCurrent ? 'var(--accent)' : 'var(--text-dim)'};">dist: ${dStr}</div>
          </div>`;
       }
       html += '</div>';
       return html;
    };
    
    const getHeapHTML = () => {
       if (s.heap.length === 0) return '<div style="color:var(--text-dim); font-family:var(--mono);">(empty)</div>';
       return '<div style="display:flex; gap:5px; flex-wrap:wrap;">' + s.heap.map(item => {
          return `<div style="padding: 4px 8px; border: 1px solid var(--border); border-radius: 12px; font-family: var(--mono); font-size: 12px; background: var(--surface);">(${item[0]}, node ${item[1]})</div>`;
       }).join('') + '</div>';
    };
    
    const getAdjHTML = () => {
       let html = '<div style="display:flex; flex-direction: column; gap: 5px; font-family: var(--mono); font-size: 13px;">';
       for(let i=1; i<=s.n; i++) {
          const edges = (s.adj[i] || []).map(e => `[${e[0]}, w=${e[1]}]`).join(', ');
          html += `<div style="${i === s.u ? 'color: var(--accent); font-weight: bold;' : 'color: var(--text-dim)'}">Node ${i}: ${edges || '(none)'}</div>`;
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `
      <div style="display:flex; flex-direction: column; gap: 15px; width: 100%; padding: 10px;">
          <div>
              <div style="color: var(--accent); font-weight: 600; margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Nodes & Distances</div>
              ${getNodesHTML()}
          </div>
          <div style="display:flex; gap: 20px;">
              <div style="flex: 1; min-width: 0;">
                  <div style="color: var(--accent); font-weight: 600; margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Priority Queue (Heap)</div>
                  ${getHeapHTML()}
              </div>
              <div style="flex: 1; min-width: 0;">
                  <div style="color: var(--accent); font-weight: 600; margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Adjacency List</div>
                  ${getAdjHTML()}
              </div>
          </div>
      </div>
    `;
  }
});


defineAlgo('15_advanced_graphs', {
  type: 'dom',
  title: 'Number of Provinces', short: 'Number of Provinces',
  idea: 'Union-Find. We start with each city in its own province (N components). We scan the adjacency matrix for connected cities. When we find a connection `isConnected[i][j] == 1`, we union the two sets. If they were previously disjoint, the number of provinces decreases by 1.',
  complexity: 'Time O(N^2 * α(N)) · Space O(N)',
  input: '1,1,0; 1,1,0; 0,0,1', hint: 'comma-separated adjacency matrix rows',
  code: [
    'def findCircleNum(isConnected):',
    '    n = len(isConnected)',
    '    parent = list(range(n))',
    '    components = n',
    '    ',
    '    def find(x):',
    '        if parent[x] != x:',
    '            parent[x] = find(parent[x])',
    '        return parent[x]',
    '    ',
    '    def union(x, y):',
    '        nonlocal components',
    '        rx, ry = find(x), find(y)',
    '        if rx != ry:',
    '            parent[ry] = rx',
    '            components -= 1',
    '    ',
    '    for i in range(n):',
    '        for j in range(i + 1, n):',
    '            if isConnected[i][j] == 1:',
    '                union(i, j)',
    '    ',
    '    return components',
  ],
  parse(str) {
    const rows = str.split(';').map(row => row.trim()).filter(Boolean);
    const isConnected = rows.map(r => r.split(',').map(Number));
    if (!isConnected.length || isConnected[0].length !== isConnected.length) {
       throw new Error("Input must be a square adjacency matrix.");
    }
    return { isConnected, n: isConnected.length };
  },
  run({ isConnected, n }) {
    const { F, snap } = avRecorder();
    
    let parent = Array.from({length: n}, (_, i) => i);
    let components = n;
    
    const find = (x) => {
       if (parent[x] !== x) parent[x] = find(parent[x]);
       return parent[x];
    };
    
    const s = { isConnected, n, parent: [...parent], components, i: null, j: null };
    snap(3, `Start with ${n} disconnected components. Each city is its own parent.`, s);
    
    for (let i = 0; i < n; i++) {
       for (let j = i + 1; j < n; j++) {
          s.i = i; s.j = j;
          if (isConnected[i][j] === 1) {
             snap(19, `Found connection between city ${i} and city ${j}.`, s);
             let ri = find(i);
             let rj = find(j);
             
             if (ri !== rj) {
                parent[rj] = ri;
                components--;
                s.parent = [...parent];
                s.components = components;
                snap(14, `Roots are different (${ri} and ${rj}). Union them! Total components is now ${components}.`, s);
             } else {
                snap(13, `Roots are the same (${ri}). Already in the same province.`, s);
             }
          } else {
             snap(18, `No connection between city ${i} and city ${j}. Skip.`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(22, `Finished scanning the upper triangle. The number of provinces is ${components}.`, s);

    return F;
  },
  buildStates(parsed) {
    return this.run(parsed).map(f => ({ ...f, explTitle: 'Union–Find', explText: f.note }));
  },
  renderDOM(container, s, spec) {
    const getMatrixHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px; margin-bottom: 20px;">';
       for (let r = 0; r < s.n; r++) {
          html += '<div style="display:flex; gap:4px;">';
          for (let c = 0; c < s.n; c++) {
             const isScanning = (s.i === r && s.j === c) || (s.i === c && s.j === r);
             const isConnected = s.isConnected[r][c] === 1;
             
             let bg = isConnected ? 'rgba(52, 211, 153, 0.2)' : 'var(--surface)';
             let color = isConnected ? '#34d399' : 'var(--text-dim)';
             let border = isScanning ? '2px solid var(--accent)' : '1px solid var(--border)';
             
             html += `
             <div style="width: 32px; height: 32px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: ${color}; font-family: var(--mono); border-radius: 4px;">
                ${s.isConnected[r][c]}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    const getSetsHTML = () => {
       let groups = {};
       for (let i = 0; i < s.n; i++) {
          let root = i;
          let temp = root;
          while (s.parent[temp] !== temp) temp = s.parent[temp];
          root = temp;
          
          if (!groups[root]) groups[root] = [];
          groups[root].push(i);
       }
       
       let html = '<div style="display:flex; gap:10px; flex-wrap:wrap;">';
       for (let [root, members] of Object.entries(groups)) {
          html += `
          <div style="padding: 10px; border: 1px solid var(--border); border-radius: 8px; background: var(--surface);">
             <div style="font-weight: bold; color: var(--accent); margin-bottom: 4px; font-size: 12px; text-transform: uppercase;">Province (Root ${root})</div>
             <div style="font-family: var(--mono); color: var(--text);">${members.join(', ')}</div>
          </div>`;
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `
      <div style="display:flex; gap: 30px; width: 100%; padding: 10px; flex-wrap: wrap;">
          <div style="flex: 1; min-width: 250px;">
              <div style="color: var(--accent); font-weight: 600; margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Adjacency Matrix</div>
              ${getMatrixHTML()}
          </div>
          <div style="flex: 1; min-width: 250px;">
              <div style="color: var(--accent); font-weight: 600; margin-bottom: 8px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Provinces (${s.components} total)</div>
              ${getSetsHTML()}
              
              <div style="margin-top: 20px; color: var(--text-dim); font-size: 13px;">
                 <b>parent</b> array:<br>
                 <span style="font-family: var(--mono);">${s.parent.map((p,i) => `[${i}]->${p}`).join(', ')}</span>
              </div>
          </div>
      </div>
    `;
  }
});


defineAlgo('16_dp_1d', {
  type: 'dom',
  title: 'Climbing Stairs', short: 'Climbing Stairs',
  idea: 'DP state: `dp[i]` is the number of distinct ways to reach step `i`. To reach step `i`, you must come from either step `i-1` or step `i-2`. Thus `dp[i] = dp[i-1] + dp[i-2]`. Instead of an array, we can optimize space by keeping only the last two values.',
  complexity: 'Time O(N) · Space O(1)',
  input: '5', hint: 'n',
  code: [
    'def climbStairs(n):',
    '    if n <= 2: return n',
    '    prev2, prev1 = 1, 2',
    '    for i in range(3, n + 1):',
    '        curr = prev1 + prev2',
    '        prev2 = prev1',
    '        prev1 = curr',
    '    return prev1',
  ],
  parse(str) {
    const n = parseInt(str.trim());
    if (isNaN(n) || n < 1) throw new Error("Input must be a positive integer.");
    return { n };
  },
  buildStates({ n }) {
    const F = [];
    const snap = (line, note, state) => F.push({ line, explTitle: 'Climbing Stairs', explText: note, ...structuredClone(state) });

    if (n <= 2) {
       snap(1, `n is ${n}, which is <= 2. Return ${n}.`, { n, prev2: null, prev1: null, curr: null, i: null });
       return F;
    }
    
    let prev2 = 1, prev1 = 2;
    const s = { n, prev2, prev1, curr: null, i: null };
    snap(2, `Initialize prev2 = 1 (ways to reach step 1) and prev1 = 2 (ways to reach step 2).`, s);
    
    for (let i = 3; i <= n; i++) {
       s.i = i;
       let curr = prev1 + prev2;
       s.curr = curr;
       snap(4, `Step ${i}: Ways to reach this step is the sum of ways to reach step ${i-1} (${prev1}) and step ${i-2} (${prev2}). curr = ${curr}.`, s);
       
       prev2 = prev1;
       s.prev2 = prev2;
       snap(5, `Shift prev2 forward to ${prev1}.`, s);
       
       prev1 = curr;
       s.prev1 = prev1;
       snap(6, `Shift prev1 forward to ${curr}.`, s);
    }
    
    s.i = null; s.curr = null;
    snap(7, `Loop finished. Return prev1 (${prev1}).`, s);
    
    return F;
  },
  renderDOM(container, s, spec) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap: 20px; align-items:center; width: 100%; padding: 20px;">
          <div style="font-size: 16px; color: var(--accent); font-weight: bold; letter-spacing: 0.05em; text-transform: uppercase;">n = ${s.n}</div>
          
          <div style="display:flex; gap: 20px; align-items: flex-end; height: 100px; margin-top: 20px;">
             <div style="display:flex; flex-direction:column; align-items:center; gap: 10px;">
                <div style="font-family: var(--mono); color: var(--text-dim); font-size: 13px;">prev2</div>
                <div style="width: 60px; height: 60px; display:flex; align-items:center; justify-content:center; border: 2px solid ${s.prev2 !== null ? 'var(--border)' : 'transparent'}; border-radius: 8px; background: var(--surface); font-size: 20px; font-weight: bold; color: var(--text);">
                   ${s.prev2 !== null ? s.prev2 : ''}
                </div>
             </div>
             
             <div style="font-size: 24px; color: var(--text-dim); padding-bottom: 15px;">+</div>
             
             <div style="display:flex; flex-direction:column; align-items:center; gap: 10px;">
                <div style="font-family: var(--mono); color: var(--text-dim); font-size: 13px;">prev1</div>
                <div style="width: 60px; height: 60px; display:flex; align-items:center; justify-content:center; border: 2px solid ${s.prev1 !== null ? 'var(--border)' : 'transparent'}; border-radius: 8px; background: var(--surface); font-size: 20px; font-weight: bold; color: var(--text);">
                   ${s.prev1 !== null ? s.prev1 : ''}
                </div>
             </div>
             
             <div style="font-size: 24px; color: var(--text-dim); padding-bottom: 15px;">=</div>
             
             <div style="display:flex; flex-direction:column; align-items:center; gap: 10px;">
                <div style="font-family: var(--mono); color: var(--accent); font-size: 13px; font-weight: bold;">curr (step ${s.i || '?'})</div>
                <div style="width: 60px; height: 60px; display:flex; align-items:center; justify-content:center; border: 2px solid ${s.curr !== null ? 'var(--accent)' : 'transparent'}; border-radius: 8px; background: rgba(56, 189, 248, 0.1); font-size: 20px; font-weight: bold; color: var(--accent);">
                   ${s.curr !== null ? s.curr : ''}
                </div>
             </div>
          </div>
          
          <div style="margin-top: 20px; font-family: var(--mono); color: var(--text-dim); text-align: center; max-width: 400px; line-height: 1.5;">
              Visualizes the rolling variables optimization for 1D DP. Only the last two states are needed to compute the current state.
          </div>
      </div>
    `;
  }
});

defineAlgo('16_dp_1d', {
  type: 'dom',
  title: 'Coin Change', short: 'Coin Change',
  idea: 'Unbounded Knapsack. `dp[a]` is the minimum number of coins to make amount `a`. We initialize `dp` with infinity, set `dp[0] = 0`, and iterate from `1` to `amount`. For each amount, we try all coins `c`. If `c <= a`, then `dp[a] = min(dp[a], dp[a - c] + 1)`.',
  complexity: 'Time O(amount * len(coins)) · Space O(amount)',
  input: '1, 2, 5; 11', hint: 'comma-separated coins; amount',
  code: [
    'def coinChange(coins, amount):',
    '    dp = [float("inf")] * (amount + 1)',
    '    dp[0] = 0',
    '    ',
    '    for a in range(1, amount + 1):',
    '        for c in coins:',
    '            if c <= a:',
    '                dp[a] = min(dp[a], dp[a - c] + 1)',
    '                ',
    '    return dp[amount] if dp[amount] != float("inf") else -1',
  ],
  parse(str) {
    const parts = str.split(';');
    if (parts.length < 2) throw new Error("Input must contain coins and amount, separated by semicolon.");
    const coins = parts[0].split(',').map(Number).filter(n => !isNaN(n));
    const amount = parseInt(parts[1].trim());
    if (isNaN(amount)) throw new Error("Amount must be an integer.");
    if (coins.length === 0) throw new Error("Must provide at least one coin.");
    return { coins, amount };
  },
  buildStates({ coins, amount }) {
    const F = [];
    const snap = (line, note, state) => F.push({ line, explTitle: 'Coin Change', explText: note, ...structuredClone(state) });

    let dp = new Array(amount + 1).fill('inf');
    dp[0] = 0;
    
    const s = { coins, amount, dp: [...dp], a: null, c: null };
    snap(2, `Initialize dp array of size ${amount + 1} with infinity. Set dp[0] = 0.`, s);
    
    for (let a = 1; a <= amount; a++) {
       s.a = a; s.c = null;
       snap(4, `Compute min coins for amount ${a}.`, s);
       
       for (let c of coins) {
          s.c = c;
          if (c <= a) {
             const prevDp = dp[a - c] === 'inf' ? Infinity : dp[a - c];
             const curDp = dp[a] === 'inf' ? Infinity : dp[a];
             
             if (prevDp !== Infinity) {
                if (prevDp + 1 < curDp) {
                   dp[a] = prevDp + 1;
                   s.dp = [...dp];
                   snap(7, `Using coin ${c}, we reach amount ${a} from amount ${a - c}. dp[${a}] = min(${curDp === Infinity ? 'inf' : curDp}, ${prevDp} + 1) = ${prevDp + 1}.`, s);
                } else {
                   snap(7, `Using coin ${c} gives ${prevDp} + 1 = ${prevDp + 1} coins, which is not better than current dp[${a}] = ${curDp === Infinity ? 'inf' : curDp}.`, s);
                }
             } else {
                snap(7, `Amount ${a - c} is unreachable, so we cannot use coin ${c} here.`, s);
             }
          } else {
             snap(6, `Coin ${c} is greater than amount ${a}, skip.`, s);
          }
       }
    }
    
    s.a = null; s.c = null;
    const ans = dp[amount] === 'inf' ? -1 : dp[amount];
    snap(9, `Loop finished. Result is dp[${amount}] = ${ans === -1 ? 'inf -> -1' : ans}.`, s);
    
    return F;
  },
  renderDOM(container, s, spec) {
    const getDpHTML = () => {
       let html = '<div style="display:flex; flex-wrap:wrap; gap:4px; margin-bottom: 20px;">';
       for (let i = 0; i <= s.amount; i++) {
          const isActiveA = i === s.a;
          const isSourceA = s.a !== null && s.c !== null && s.c <= s.a && i === s.a - s.c;
          
          let bg = 'var(--surface)';
          let border = 'var(--border)';
          
          if (isActiveA) { border = 'var(--accent)'; bg = 'rgba(56, 189, 248, 0.1)'; }
          else if (isSourceA) { border = '#34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
          
          const val = s.dp[i] === 'inf' ? '∞' : s.dp[i];
          
          html += `
          <div style="display:flex; flex-direction:column; align-items:center;">
             <div style="font-family: var(--mono); font-size: 11px; color: var(--text-dim); margin-bottom: 2px;">${i}</div>
             <div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; border: 2px solid ${border}; background: ${bg}; color: var(--text); font-family: var(--mono); border-radius: 4px; font-weight: ${isActiveA || isSourceA ? 'bold' : 'normal'};">
                ${val}
             </div>
          </div>`;
       }
       html += '</div>';
       return html;
    };
    
    const getCoinsHTML = () => {
       let html = '<div style="display:flex; gap:8px; margin-bottom: 20px;">';
       for (let c of s.coins) {
          const isActive = c === s.c;
          let border = isActive ? 'var(--accent)' : 'var(--border)';
          let bg = isActive ? 'rgba(56, 189, 248, 0.1)' : 'var(--surface)';
          
          html += `
          <div style="padding: 6px 12px; border: 2px solid ${border}; border-radius: 999px; background: ${bg}; font-family: var(--mono); font-size: 14px; font-weight: bold; color: ${isActive ? 'var(--accent)' : 'var(--text)'};">
             ${c}
          </div>`;
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; width: 100%; padding: 10px;">
          <div style="color: var(--accent); font-weight: 600; margin-bottom: 12px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">DP Array (Minimum Coins)</div>
          ${getDpHTML()}
          
          <div style="color: var(--accent); font-weight: 600; margin-bottom: 12px; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em;">Available Coins</div>
          ${getCoinsHTML()}
          
          <div style="margin-top: 15px; font-family: var(--mono); color: var(--text-dim); font-size: 13px;">
             ${s.a !== null && s.c !== null && s.c <= s.a ? 
                `dp[${s.a}] = min(dp[${s.a}], dp[${s.a - s.c}] + 1)` : 
                'Iterating through amounts and coins...'}
          </div>
      </div>
    `;
  }
});


defineAlgo('17_dp_2d', {
  title: 'Unique Paths', short: 'Unique Paths',
  idea: '2D DP. `dp[i][j]` is the number of ways to reach cell `(i, j)`. You can only come from `(i-1, j)` (above) or `(i, j-1)` (left). So `dp[i][j] = dp[i-1][j] + dp[i][j-1]`. The first row and column are all 1s.',
  complexity: 'Time O(m*n) · Space O(m*n) (or O(n) optimized)',
  input: '3, 4', hint: 'm, n',
  code: [
    'def uniquePaths(m, n):',
    '    dp = [[1] * n for _ in range(m)]',
    '    ',
    '    for i in range(1, m):',
    '        for j in range(1, n):',
    '            dp[i][j] = dp[i-1][j] + dp[i][j-1]',
    '            ',
    '    return dp[m-1][n-1]',
  ],
  parse(str) {
    const parts = str.split(',').map(Number);
    if (parts.length !== 2 || isNaN(parts[0]) || isNaN(parts[1])) throw new Error("Input must be m, n (e.g., '3, 4').");
    const [m, n] = parts;
    if (m < 1 || n < 1 || m > 10 || n > 10) throw new Error("m and n must be between 1 and 10 for visualization.");
    return { m, n };
  },
  run({ m, n }) {
    const { F, snap } = avRecorder();
    
    // Create 2D DP array
    let dp = Array.from({length: m}, () => new Array(n).fill(1));
    
    const s = { m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(2, `Initialize a ${m}x${n} DP table with all 1s (base cases for top row and left col).`, s);
    
    for (let i = 1; i < m; i++) {
       for (let j = 1; j < n; j++) {
          s.i = i; s.j = j;
          snap(5, `Calculate ways to reach cell (${i}, ${j}).`, s);
          
          dp[i][j] = dp[i-1][j] + dp[i][j-1];
          s.dp = JSON.parse(JSON.stringify(dp));
          
          snap(6, `dp[${i}][${j}] = dp[${i-1}][${j}] (${dp[i-1][j]}) + dp[${i}][${j-1}] (${dp[i][j-1]}) = ${dp[i][j]}.`, s);
       }
    }
    
    s.i = null; s.j = null;
    snap(8, `Finished. The total unique paths to the bottom-right corner is dp[${m-1}][${n-1}] = ${dp[m-1][n-1]}.`, s);
    
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px; margin-top: 10px;">';
       for (let r = 0; r < s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          for (let c = 0; c < s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             const isAbove = s.i !== null && r === s.i - 1 && c === s.j;
             const isLeft = s.j !== null && r === s.i && c === s.j - 1;
             
             let bg = 'var(--surface)';
             let border = '1px solid var(--border)';
             
             if (isCurrent) { border = '2px solid var(--accent)'; bg = 'rgba(56, 189, 248, 0.1)'; }
             else if (isAbove || isLeft) { border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
             
             html += `
             <div style="width: 44px; height: 44px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: var(--text); font-family: var(--mono); border-radius: 6px; font-weight: ${isCurrent || isAbove || isLeft ? 'bold' : 'normal'};">
                ${s.dp[r][c]}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px;">
          <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table (Grid)</div>
          ${getGridHTML()}
          
          <div style="margin-top: 20px; font-family: var(--mono); color: var(--text-dim); font-size: 13px;">
             ${s.i !== null && s.j !== null ? 
                `dp[${s.i}][${s.j}] = dp[${s.i-1}][${s.j}] + dp[${s.i}][${s.j-1}]` : 
                'Robot starts at top-left, wants to go to bottom-right.'}
          </div>
      </div>
    `;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Longest Common Subsequence', short: 'LCS',
  idea: '2D DP over two strings. `dp[i][j]` is the LCS of `text1[:i]` and `text2[:j]`. If characters match, `dp[i][j] = dp[i-1][j-1] + 1`. If not, `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`. Note: indices are 1-based to allow for empty prefixes.',
  complexity: 'Time O(m*n) · Space O(m*n) (or O(min(m,n)) optimized)',
  input: 'abcde, ace', hint: 'text1, text2',
  code: [
    'def longestCommonSubsequence(text1, text2):',
    '    m, n = len(text1), len(text2)',
    '    dp = [[0] * (n + 1) for _ in range(m + 1)]',
    '    ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            if text1[i-1] == text2[j-1]:',
    '                dp[i][j] = dp[i-1][j-1] + 1',
    '            else:',
    '                dp[i][j] = max(dp[i-1][j], dp[i][j-1])',
    '                ',
    '    return dp[m][n]',
  ],
  parse(str) {
    const parts = str.split(',');
    if (parts.length !== 2) throw new Error("Input must be two strings separated by a comma.");
    const text1 = parts[0].trim();
    const text2 = parts[1].trim();
    if (text1.length > 10 || text2.length > 10) throw new Error("Strings must be <= 10 characters for visualization.");
    return { text1, text2 };
  },
  run({ text1, text2 }) {
    const { F, snap } = avRecorder();
    
    const m = text1.length;
    const n = text2.length;
    let dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    
    const s = { text1, text2, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(3, `Initialize a ${m+1}x${n+1} DP table with 0s (empty prefixes have 0 LCS).`, s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          snap(6, `Compare text1[${i-1}]='${text1[i-1]}' and text2[${j-1}]='${text2[j-1]}'.`, s);
          
          if (text1[i-1] === text2[j-1]) {
             dp[i][j] = dp[i-1][j-1] + 1;
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(7, `Characters match! dp[${i}][${j}] = dp[${i-1}][${j-1}] (${dp[i-1][j-1]}) + 1 = ${dp[i][j]}.`, s);
          } else {
             dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(9, `Mismatch. dp[${i}][${j}] = max(dp[${i-1}][${j}], dp[${i}][${j-1}]) = max(${dp[i-1][j]}, ${dp[i][j-1]}) = ${dp[i][j]}.`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(11, `Finished. Longest Common Subsequence length is ${dp[m][n]}.`, s);
    
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
       
       // Header row (text2)
       html += '<div style="display:flex; gap:4px;">';
       html += '<div style="width: 40px; height: 30px;"></div>'; // Empty corner
       html += '<div style="width: 40px; height: 30px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); color: var(--text-dim);">""</div>';
       for (let j = 0; j < s.n; j++) {
          const isActive = s.j !== null && j === s.j - 1;
          html += `<div style="width: 40px; height: 30px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold; color: ${isActive ? 'var(--accent)' : 'var(--text)'};">${s.text2[j]}</div>`;
       }
       html += '</div>';
       
       for (let r = 0; r <= s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          
          // Row header (text1)
          const char = r === 0 ? '""' : s.text1[r-1];
          const isRowActive = s.i !== null && r === s.i;
          html += `<div style="width: 40px; height: 40px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold; color: ${isRowActive && r > 0 ? 'var(--accent)' : 'var(--text-dim)'};">${char}</div>`;
          
          for (let c = 0; c <= s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             
             let bg = 'var(--surface)';
             let border = '1px solid var(--border)';
             let color = r === 0 || c === 0 ? 'var(--text-dim)' : 'var(--text)';
             
             if (isCurrent) { 
                 border = '2px solid var(--accent)'; 
                 bg = 'rgba(56, 189, 248, 0.1)'; 
                 color = 'var(--accent)';
             } else if (s.i !== null && s.j !== null) {
                 const match = s.text1[s.i-1] === s.text2[s.j-1];
                 const isDiag = r === s.i - 1 && c === s.j - 1;
                 const isAbove = r === s.i - 1 && c === s.j;
                 const isLeft = r === s.i && c === s.j - 1;
                 
                 if (match && isDiag) {
                     border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)';
                 } else if (!match && (isAbove || isLeft)) {
                     border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)';
                 }
             }
             
             html += `
             <div style="width: 40px; height: 40px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: ${color}; font-family: var(--mono); border-radius: 4px; font-weight: ${isCurrent ? 'bold' : 'normal'};">
                ${s.dp[r][c]}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px; overflow-x: auto;">
          <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 15px;">DP Table</div>
          ${getGridHTML()}
          
          <div style="margin-top: 20px; font-family: var(--mono); color: var(--text-dim); font-size: 13px;">
             ${s.i !== null && s.j !== null ? 
                (s.text1[s.i-1] === s.text2[s.j-1] ? 
                   `Match! dp[${s.i}][${s.j}] = dp[${s.i-1}][${s.j-1}] + 1` : 
                   `Mismatch. dp[${s.i}][${s.j}] = max(dp[${s.i-1}][${s.j}], dp[${s.i}][${s.j-1}])`) : 
                'Filling DP table to find LCS...'}
          </div>
      </div>
    `;
  }
});


defineAlgo('17_dp_2d', {
  title: 'Unique Paths II', short: 'Unique Paths II',
  idea: 'Same as Unique Paths, but with obstacles. If a cell has an obstacle `obstacleGrid[i][j] == 1`, `dp[i][j] = 0`. Otherwise, `dp[i][j] = dp[i-1][j] + dp[i][j-1]`.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: '0,0,0; 0,1,0; 0,0,0', hint: 'comma-separated rows of 0s and 1s',
  code: [
    'def uniquePathsWithObstacles(obstacleGrid):',
    '    m, n = len(obstacleGrid), len(obstacleGrid[0])',
    '    dp = [[0] * n for _ in range(m)]',
    '    ',
    '    for i in range(m):',
    '        for j in range(n):',
    '            if obstacleGrid[i][j] == 1:',
    '                dp[i][j] = 0',
    '            elif i == 0 and j == 0:',
    '                dp[i][j] = 1',
    '            else:',
    '                up = dp[i-1][j] if i > 0 else 0',
    '                left = dp[i][j-1] if j > 0 else 0',
    '                dp[i][j] = up + left',
    '                ',
    '    return dp[m-1][n-1]',
  ],
  parse(str) {
    const rows = str.split(';');
    const grid = rows.map(r => r.split(',').map(Number));
    if (!grid.length || !grid[0].length) throw new Error("Invalid grid");
    return { grid, m: grid.length, n: grid[0].length };
  },
  run({ grid, m, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: m}, () => new Array(n).fill(0));
    const s = { grid, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    
    snap(3, `Initialize ${m}x${n} DP table with 0s.`, s);
    
    for (let i = 0; i < m; i++) {
       for (let j = 0; j < n; j++) {
          s.i = i; s.j = j;
          if (grid[i][j] === 1) {
             dp[i][j] = 0;
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(8, `Cell (${i}, ${j}) is an obstacle. dp[${i}][${j}] = 0.`, s);
          } else if (i === 0 && j === 0) {
             dp[i][j] = 1;
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(10, `Start cell (0, 0) has 1 path. dp[0][0] = 1.`, s);
          } else {
             const up = i > 0 ? dp[i-1][j] : 0;
             const left = j > 0 ? dp[i][j-1] : 0;
             dp[i][j] = up + left;
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(14, `No obstacle. dp[${i}][${j}] = dp[${i-1 < 0 ? 'out' : i-1}][${j}] (${up}) + dp[${i}][${j-1 < 0 ? 'out' : j-1}] (${left}) = ${dp[i][j]}.`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(16, `Finished. Paths to bottom-right = ${dp[m-1][n-1]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px; margin-top: 10px;">';
       for (let r = 0; r < s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          for (let c = 0; c < s.n; c++) {
             const isObs = s.grid[r][c] === 1;
             const isCurrent = s.i === r && s.j === c;
             const isAbove = s.i !== null && r === s.i - 1 && c === s.j;
             const isLeft = s.j !== null && r === s.i && c === s.j - 1;
             
             let bg = isObs ? 'rgba(239, 68, 68, 0.2)' : 'var(--surface)';
             let border = '1px solid var(--border)';
             let textCol = isObs ? '#ef4444' : 'var(--text)';
             
             if (isCurrent) { border = '2px solid var(--accent)'; bg = isObs ? 'rgba(239, 68, 68, 0.3)' : 'rgba(56, 189, 248, 0.1)'; }
             else if (!isObs && (isAbove || isLeft)) { border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
             
             html += `
             <div style="width: 44px; height: 44px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: ${textCol}; font-family: var(--mono); border-radius: 6px; font-weight: ${isCurrent || isAbove || isLeft ? 'bold' : 'normal'};">
                ${isObs ? 'X' : s.dp[r][c]}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px;">
        <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table (Obstacles marked X)</div>
        ${getGridHTML()}
    </div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Minimum Path Sum', short: 'Min Path Sum',
  idea: '`dp[i][j]` is the minimum cost to reach `(i, j)`. It is the cell cost plus the minimum of reaching the cell above or left: `dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])`.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: '1,3,1; 1,5,1; 4,2,1', hint: 'comma-separated row costs',
  code: [
    'def minPathSum(grid):',
    '    m, n = len(grid), len(grid[0])',
    '    dp = [[0] * n for _ in range(m)]',
    '    ',
    '    for i in range(m):',
    '        for j in range(n):',
    '            if i == 0 and j == 0:',
    '                dp[i][j] = grid[i][j]',
    '            elif i == 0:',
    '                dp[i][j] = dp[i][j-1] + grid[i][j]',
    '            elif j == 0:',
    '                dp[i][j] = dp[i-1][j] + grid[i][j]',
    '            else:',
    '                dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])',
    '                ',
    '    return dp[m-1][n-1]',
  ],
  parse(str) {
    const rows = str.split(';');
    const grid = rows.map(r => r.split(',').map(Number));
    return { grid, m: grid.length, n: grid[0].length };
  },
  run({ grid, m, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: m}, () => new Array(n).fill(0));
    const s = { grid, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    
    snap(3, `Initialize DP table.`, s);
    
    for (let i = 0; i < m; i++) {
       for (let j = 0; j < n; j++) {
          s.i = i; s.j = j;
          if (i === 0 && j === 0) {
             dp[i][j] = grid[i][j];
          } else if (i === 0) {
             dp[i][j] = dp[i][j-1] + grid[i][j];
          } else if (j === 0) {
             dp[i][j] = dp[i-1][j] + grid[i][j];
          } else {
             dp[i][j] = grid[i][j] + Math.min(dp[i-1][j], dp[i][j-1]);
          }
          s.dp = JSON.parse(JSON.stringify(dp));
          snap(13, `Cost for cell (${i}, ${j}) is ${grid[i][j]}. Total min path = ${dp[i][j]}.`, s);
       }
    }
    
    s.i = null; s.j = null;
    snap(15, `Min path sum = ${dp[m-1][n-1]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px; margin-top: 10px;">';
       for (let r = 0; r < s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          for (let c = 0; c < s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             const isAbove = s.i !== null && r === s.i - 1 && c === s.j;
             const isLeft = s.j !== null && r === s.i && c === s.j - 1;
             
             let bg = 'var(--surface)'; let border = '1px solid var(--border)';
             if (isCurrent) { border = '2px solid var(--accent)'; bg = 'rgba(56, 189, 248, 0.1)'; }
             else if (isAbove || isLeft) { border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
             
             html += `
             <div style="width: 50px; height: 50px; display:flex; flex-direction:column; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: var(--text); font-family: var(--mono); border-radius: 6px;">
                <div style="font-size: 10px; color: var(--text-dim); margin-bottom: 2px;">+${s.grid[r][c]}</div>
                <div style="font-weight: ${isCurrent ? 'bold' : 'normal'};">${s.dp[r][c] || ''}</div>
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px;">
        <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table (Top = Cell Cost, Bottom = Total Cost)</div>
        ${getGridHTML()}
    </div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Maximal Square', short: 'Maximal Square',
  idea: '`dp[i][j]` is the side length of the max square whose bottom-right corner is at `(i, j)`. If `matrix[i][j] == "1"`, `dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1`. We track the max seen.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: '1,0,1,0,0; 1,0,1,1,1; 1,1,1,1,1; 1,0,0,1,0', hint: 'comma-separated rows of 0s and 1s',
  code: [
    'def maximalSquare(matrix):',
    '    m, n = len(matrix), len(matrix[0])',
    '    dp = [[0] * (n + 1) for _ in range(m + 1)]',
    '    max_side = 0',
    '    ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            if matrix[i-1][j-1] == "1":',
    '                dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1',
    '                max_side = max(max_side, dp[i][j])',
    '                ',
    '    return max_side * max_side',
  ],
  parse(str) {
    const rows = str.split(';');
    const matrix = rows.map(r => r.split(',').map(x => x.trim()));
    return { matrix, m: matrix.length, n: matrix[0].length };
  },
  run({ matrix, m, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    let max_side = 0;
    const s = { matrix, m, n, dp: JSON.parse(JSON.stringify(dp)), max_side, i: null, j: null };
    
    snap(3, `Initialize DP table with extra row/col of 0s.`, s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          if (matrix[i-1][j-1] === "1") {
             dp[i][j] = Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1;
             max_side = Math.max(max_side, dp[i][j]);
             s.dp = JSON.parse(JSON.stringify(dp));
             s.max_side = max_side;
             snap(9, `matrix[${i-1}][${j-1}] == "1". min(top, left, diag-top-left) + 1 = min(${dp[i-1][j]}, ${dp[i][j-1]}, ${dp[i-1][j-1]}) + 1 = ${dp[i][j]}. Max side is now ${max_side}.`, s);
          } else {
             snap(8, `matrix[${i-1}][${j-1}] == "0", skip. dp[${i}][${j}] = 0.`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(12, `Max side length is ${max_side}. Area = ${max_side * max_side}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px; margin-top: 10px;">';
       for (let r = 1; r <= s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          for (let c = 1; c <= s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             const isNeighbor = s.i !== null && s.j !== null && ((r === s.i-1 && c === s.j) || (r === s.i && c === s.j-1) || (r === s.i-1 && c === s.j-1));
             const isOne = s.matrix[r-1][c-1] === "1";
             
             let bg = isOne ? 'var(--surface)' : 'rgba(0,0,0,0.1)';
             let border = '1px solid var(--border)';
             let color = isOne ? 'var(--text)' : 'transparent';
             
             if (isCurrent) { border = '2px solid var(--accent)'; bg = isOne ? 'rgba(56, 189, 248, 0.1)' : bg; }
             else if (isNeighbor) { border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
             
             html += `
             <div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: ${color}; font-family: var(--mono); border-radius: 4px; font-weight: ${isCurrent ? 'bold' : 'normal'};">
                ${s.dp[r][c] || ''}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px;">
        <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table (Side length of square)</div>
        ${getGridHTML()}
        <div style="margin-top:10px; font-weight: bold; color: #34d399;">Max Side Length Found: ${s.max_side}</div>
    </div>`;
  }
});


defineAlgo('17_dp_2d', {
  title: 'Edit Distance', short: 'Edit Distance',
  idea: '`dp[i][j]` is the minimum operations to convert `word1[:i]` to `word2[:j]`. If characters match, `dp[i][j] = dp[i-1][j-1]`. If they mismatch, try insert, delete, or replace: `dp[i][j] = 1 + min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1])`.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: 'horse, ros', hint: 'word1, word2',
  code: [
    'def minDistance(word1, word2):',
    '    m, n = len(word1), len(word2)',
    '    dp = [[0] * (n + 1) for _ in range(m + 1)]',
    '    ',
    '    for i in range(m + 1): dp[i][0] = i',
    '    for j in range(n + 1): dp[0][j] = j',
    '    ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            if word1[i-1] == word2[j-1]:',
    '                dp[i][j] = dp[i-1][j-1]',
    '            else:',
    '                dp[i][j] = 1 + min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1])',
    '                ',
    '    return dp[m][n]',
  ],
  parse(str) {
    const parts = str.split(',');
    const word1 = parts[0].trim();
    const word2 = parts[1].trim();
    return { word1, word2, m: word1.length, n: word2.length };
  },
  run({ word1, word2, m, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    
    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;
    
    const s = { word1, word2, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(6, `Initialize DP table. Base cases: empty string to string of length k takes k inserts/deletes.`, s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          if (word1[i-1] === word2[j-1]) {
             dp[i][j] = dp[i-1][j-1];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Characters match ('${word1[i-1]}'). No operation needed. dp[${i}][${j}] = dp[${i-1}][${j-1}] = ${dp[i][j]}.`, s);
          } else {
             dp[i][j] = 1 + Math.min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1]);
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(13, `Mismatch ('${word1[i-1]}' vs '${word2[j-1]}'). 1 + min(insert:${dp[i][j-1]}, delete:${dp[i-1][j]}, replace:${dp[i-1][j-1]}) = ${dp[i][j]}.`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(15, `Minimum operations = ${dp[m][n]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
       
       html += '<div style="display:flex; gap:4px;">';
       html += '<div style="width: 36px; height: 30px;"></div><div style="width: 36px; height: 30px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); color: var(--text-dim);">""</div>';
       for (let j = 0; j < s.n; j++) {
          html += `<div style="width: 36px; height: 30px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold; color: ${s.j !== null && j === s.j - 1 ? 'var(--accent)' : 'var(--text)'};">${s.word2[j]}</div>`;
       }
       html += '</div>';
       
       for (let r = 0; r <= s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          const char = r === 0 ? '""' : s.word1[r-1];
          html += `<div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold; color: ${s.i !== null && r === s.i ? 'var(--accent)' : 'var(--text-dim)'};">${char}</div>`;
          
          for (let c = 0; c <= s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             const isNeighbor = s.i !== null && s.j !== null && ((r === s.i-1 && c === s.j) || (r === s.i && c === s.j-1) || (r === s.i-1 && c === s.j-1));
             
             let bg = 'var(--surface)'; let border = '1px solid var(--border)';
             if (isCurrent) { border = '2px solid var(--accent)'; bg = 'rgba(56, 189, 248, 0.1)'; }
             else if (isNeighbor) { border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
             
             html += `
             <div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: var(--text); font-family: var(--mono); border-radius: 4px; font-weight: ${isCurrent ? 'bold' : 'normal'};">
                ${s.dp[r][c]}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px; overflow-x: auto;">
        <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table</div>
        ${getGridHTML()}
    </div>`;
  }
});


defineAlgo('17_dp_2d', {
  title: 'Interleaving String', short: 'Interleaving String',
  idea: '`dp[i][j]` is true if `s3[:i+j]` is formed by interleaving `s1[:i]` and `s2[:j]`. `dp[i][j] = (dp[i-1][j] and s1[i-1] == s3[i+j-1]) or (dp[i][j-1] and s2[j-1] == s3[i+j-1])`.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: 'aabcc, dbbca, aadbbcbcac', hint: 's1, s2, s3',
  code: [
    'def isInterleave(s1, s2, s3):',
    '    m, n = len(s1), len(s2)',
    '    if m + n != len(s3): return False',
    '    dp = [[False] * (n + 1) for _ in range(m + 1)]',
    '    dp[0][0] = True',
    '    ',
    '    for i in range(1, m + 1):',
    '        dp[i][0] = dp[i-1][0] and s1[i-1] == s3[i-1]',
    '    for j in range(1, n + 1):',
    '        dp[0][j] = dp[0][j-1] and s2[j-1] == s3[j-1]',
    '        ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            dp[i][j] = (dp[i-1][j] and s1[i-1] == s3[i+j-1]) or \\',
    '                       (dp[i][j-1] and s2[j-1] == s3[i+j-1])',
    '                       ',
    '    return dp[m][n]',
  ],
  parse(str) {
    const parts = str.split(',');
    if (parts.length !== 3) throw new Error("Need s1, s2, s3");
    const s1 = parts[0].trim(), s2 = parts[1].trim(), s3 = parts[2].trim();
    if (s1.length + s2.length !== s3.length) throw new Error("Lengths must match");
    return { s1, s2, s3, m: s1.length, n: s2.length };
  },
  run({ s1, s2, s3, m, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(false));
    dp[0][0] = true;
    
    for (let i = 1; i <= m; i++) dp[i][0] = dp[i-1][0] && s1[i-1] === s3[i-1];
    for (let j = 1; j <= n; j++) dp[0][j] = dp[0][j-1] && s2[j-1] === s3[j-1];
    
    const s = { s1, s2, s3, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(5, `Initialize DP table and base cases (0th row and 0th column).`, s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          const match1 = dp[i-1][j] && s1[i-1] === s3[i+j-1];
          const match2 = dp[i][j-1] && s2[j-1] === s3[i+j-1];
          dp[i][j] = match1 || match2;
          s.dp = JSON.parse(JSON.stringify(dp));
          snap(13, `s3[${i+j-1}]='${s3[i+j-1]}'. Can it come from s1='${s1[i-1]}' (top)? ${match1}. From s2='${s2[j-1]}' (left)? ${match2}. dp[${i}][${j}] = ${dp[i][j]}.`, s);
       }
    }
    
    s.i = null; s.j = null;
    snap(16, `Result = ${dp[m][n]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
       
       html += '<div style="display:flex; gap:4px;">';
       html += '<div style="width: 36px; height: 30px;"></div><div style="width: 36px; height: 30px;"></div>';
       for (let j = 0; j < s.n; j++) {
          html += `<div style="width: 36px; height: 30px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold;">${s.s2[j]}</div>`;
       }
       html += '</div>';
       
       for (let r = 0; r <= s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          const char = r === 0 ? '""' : s.s1[r-1];
          html += `<div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold;">${char}</div>`;
          
          for (let c = 0; c <= s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             const isNeighbor = s.i !== null && s.j !== null && ((r === s.i-1 && c === s.j) || (r === s.i && c === s.j-1));
             
             let bg = s.dp[r][c] ? 'rgba(52, 211, 153, 0.2)' : 'var(--surface)'; 
             let border = '1px solid var(--border)';
             if (isCurrent) { border = '2px solid var(--accent)'; }
             else if (isNeighbor) { border = '2px solid #34d399'; }
             
             html += `
             <div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: var(--text); font-family: var(--mono); border-radius: 4px;">
                ${s.dp[r][c] ? 'T' : 'F'}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px; overflow-x: auto;">
        <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table (T/F)</div>
        ${getGridHTML()}
        <div style="margin-top:10px; color: var(--text-dim);">Target s3: <b>${s.s3}</b></div>
    </div>`;
  }
});


defineAlgo('17_dp_2d', {
  title: 'Best Time to Buy and Sell Stock with Cooldown', short: 'Stock w/ Cooldown',
  idea: 'State machine DP. We maintain two states for each day: `held` (holding a stock) and `sold` (no stock). Due to cooldown, buying on day `i` requires the `sold` state from day `i-2`.',
  complexity: 'Time O(N) · Space O(N)',
  input: '1, 2, 3, 0, 2', hint: 'comma-separated prices',
  code: [
    'def maxProfit(prices):',
    '    n = len(prices)',
    '    if n <= 1: return 0',
    '    ',
    '    held = [0] * n',
    '    sold = [0] * n',
    '    ',
    '    held[0] = -prices[0]',
    '    sold[0] = 0',
    '    held[1] = max(-prices[0], -prices[1])',
    '    sold[1] = max(0, held[0] + prices[1])',
    '    ',
    '    for i in range(2, n):',
    '        held[i] = max(held[i-1], sold[i-2] - prices[i])',
    '        sold[i] = max(sold[i-1], held[i-1] + prices[i])',
    '        ',
    '    return sold[n-1]'
  ],
  parse(str) {
    const prices = str.split(',').map(Number);
    if (!prices.length) throw new Error("Need prices");
    return { prices, n: prices.length };
  },
  run({ prices, n }) {
    const { F, snap } = avRecorder();
    if (n <= 1) {
       snap(1, 'Need at least 2 days', {});
       return F;
    }
    
    let held = new Array(n).fill(0);
    let sold = new Array(n).fill(0);
    
    held[0] = -prices[0];
    sold[0] = 0;
    held[1] = Math.max(-prices[0], -prices[1]);
    sold[1] = Math.max(0, held[0] + prices[1]);
    
    const s = { prices, n, held: [...held], sold: [...sold], i: null };
    snap(10, 'Initialize base cases for day 0 and day 1.', s);
    
    for (let i = 2; i < n; i++) {
       s.i = i;
       
       held[i] = Math.max(held[i-1], sold[i-2] - prices[i]);
       sold[i] = Math.max(sold[i-1], held[i-1] + prices[i]);
       
       s.held = [...held];
       s.sold = [...sold];
       
       snap(13, `Day ${i} (price=${prices[i]}): held=max(held[${i-1}], sold[${i-2}] - ${prices[i]})=${held[i]}. sold=max(sold[${i-1}], held[${i-1}] + ${prices[i]})=${sold[i]}.`, s);
    }
    
    s.i = null;
    snap(16, `Finished. Max profit is sold[${n-1}] = ${sold[n-1]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:8px;">';
    html += '<div style="display:flex; gap:4px;"><div style="width:60px;">Price:</div>';
    for(let i=0; i<s.n; i++) html += `<div style="width:40px; text-align:center; color:var(--accent); font-weight:bold;">${s.prices[i]}</div>`;
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px;">Held:</div>';
    for(let i=0; i<s.n; i++) html += `<div style="width:40px; height:30px; display:flex; align-items:center; justify-content:center; border:1px solid var(--border); ${s.i===i?'border-color:var(--accent); background:rgba(56, 189, 248, 0.1);':''}">${s.held[i]}</div>`;
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px;">Sold:</div>';
    for(let i=0; i<s.n; i++) html += `<div style="width:40px; height:30px; display:flex; align-items:center; justify-content:center; border:1px solid var(--border); ${s.i===i?'border-color:var(--accent); background:rgba(56, 189, 248, 0.1);':''}">${s.sold[i]}</div>`;
    html += '</div></div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Coin Change II', short: 'Coin Change II',
  idea: '`dp[i][a]` is ways to make amount `a` using first `i` coins. `dp[i][a] = dp[i-1][a] + dp[i][a-coin]`. We visualize this as a 2D table.',
  complexity: 'Time O(coins * amount) · Space O(coins * amount)',
  input: '1, 2, 5; 5', hint: 'coins; amount',
  code: [
    'def change(amount, coins):',
    '    n = len(coins)',
    '    dp = [[0] * (amount + 1) for _ in range(n + 1)]',
    '    ',
    '    for i in range(n + 1):',
    '        dp[i][0] = 1',
    '        ',
    '    for i in range(1, n + 1):',
    '        for a in range(1, amount + 1):',
    '            if coins[i-1] > a:',
    '                dp[i][a] = dp[i-1][a]',
    '            else:',
    '                dp[i][a] = dp[i-1][a] + dp[i][a - coins[i-1]]',
    '                ',
    '    return dp[n][amount]'
  ],
  parse(str) {
    const parts = str.split(';');
    const coins = parts[0].split(',').map(Number);
    const amount = parseInt(parts[1]);
    return { coins, amount, n: coins.length };
  },
  run({ coins, amount, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: n + 1}, () => new Array(amount + 1).fill(0));
    for (let i = 0; i <= n; i++) dp[i][0] = 1;
    
    const s = { coins, amount, n, dp: JSON.parse(JSON.stringify(dp)), i: null, a: null };
    snap(5, 'Initialize DP table. dp[i][0] = 1 (1 way to make amount 0).', s);
    
    for (let i = 1; i <= n; i++) {
       for (let a = 1; a <= amount; a++) {
          s.i = i; s.a = a;
          if (coins[i-1] > a) {
             dp[i][a] = dp[i-1][a];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Coin ${coins[i-1]} > amount ${a}. dp[${i}][${a}] = dp[${i-1}][${a}] = ${dp[i][a]}.`, s);
          } else {
             dp[i][a] = dp[i-1][a] + dp[i][a - coins[i-1]];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(13, `Use coin ${coins[i-1]}. dp[${i}][${a}] = ways without (${dp[i-1][a]}) + ways with (${dp[i][a - coins[i-1]]}) = ${dp[i][a]}.`, s);
          }
       }
    }
    
    s.i = null; s.a = null;
    snap(15, `Finished. Total ways = ${dp[n][amount]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    html += '<div style="display:flex; gap:4px;"><div style="width:40px;"></div>';
    for (let a = 0; a <= s.amount; a++) html += `<div style="width:30px; text-align:center; font-weight:bold;">${a}</div>`;
    html += '</div>';
    
    for (let r = 0; r <= s.n; r++) {
       html += '<div style="display:flex; gap:4px;">';
       const coinLabel = r === 0 ? 'None' : String(s.coins[r-1]);
       html += `<div style="width:40px; font-weight:bold;">${coinLabel}</div>`;
       for (let c = 0; c <= s.amount; c++) {
          const isCurrent = s.i === r && s.a === c;
          let border = isCurrent ? '2px solid var(--accent)' : '1px solid var(--border)';
          html += `<div style="width:30px; height:30px; display:flex; align-items:center; justify-content:center; border:${border}; ${isCurrent?'background:rgba(56, 189, 248, 0.1);':''}">${s.dp[r][c]}</div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Target Sum', short: 'Target Sum',
  idea: 'Uses 2D DP to count ways to reach target. `dp[i][s]` is ways to form sum `s` with first `i` numbers.',
  complexity: 'Time O(N * Sum) · Space O(N * Sum)',
  input: '1,1,1,1,1; 3', hint: 'nums; target',
  code: [
    'def findTargetSumWays(nums, target):',
    '    total = sum(nums)',
    '    if abs(target) > total: return 0',
    '    ',
    '    offset = total',
    '    dp = [[0] * (2 * total + 1) for _ in range(len(nums) + 1)]',
    '    dp[0][offset] = 1',
    '    ',
    '    for i in range(1, len(nums) + 1):',
    '        for s in range(2 * total + 1):',
    '            if dp[i-1][s] > 0:',
    '                dp[i][s + nums[i-1]] += dp[i-1][s]',
    '                dp[i][s - nums[i-1]] += dp[i-1][s]',
    '                ',
    '    return dp[len(nums)][target + offset]'
  ],
  parse(str) {
    const parts = str.split(';');
    const nums = parts[0].split(',').map(Number);
    const target = parseInt(parts[1]);
    return { nums, target };
  },
  run({ nums, target }) {
    const { F, snap } = avRecorder();
    const total = nums.reduce((a, b) => a + Math.abs(b), 0);
    if (Math.abs(target) > total) return snap(1, 'Target unreachable', {}) && F;
    
    let dp = Array.from({length: nums.length + 1}, () => new Array(2 * total + 1).fill(0));
    const offset = total;
    dp[0][offset] = 1;
    
    const s = { nums, target, total, offset, dp: JSON.parse(JSON.stringify(dp)), i: null };
    snap(6, 'Initialize DP. dp[0][0] = 1 (offset mapped to index).', s);
    
    for (let i = 1; i <= nums.length; i++) {
       s.i = i;
       for (let sum = 0; sum <= 2 * total; sum++) {
          if (dp[i-1][sum] > 0) {
             dp[i][sum + nums[i-1]] += dp[i-1][sum];
             dp[i][sum - nums[i-1]] += dp[i-1][sum];
          }
       }
       s.dp = JSON.parse(JSON.stringify(dp));
       snap(11, `Process num ${nums[i-1]}. Branch into + and -.`, s);
    }
    
    s.i = null;
    snap(14, `Done. Target ${target} ways = ${dp[nums.length][target + offset]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    if(!s.dp) return;
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    html += '<div style="display:flex; gap:4px;"><div style="width:40px;">Idx</div>';
    for(let sum=0; sum<=2*s.total; sum++) {
        if(s.dp[s.dp.length-1][sum] > 0 || sum === s.target + s.offset || sum === s.offset) {
            html += `<div style="width:30px; text-align:center; font-size:10px;">${sum-s.offset}</div>`;
        }
    }
    html += '</div>';
    
    for(let i=0; i<=s.nums.length; i++) {
       html += '<div style="display:flex; gap:4px;">';
       html += `<div style="width:40px; font-weight:bold;">${i}</div>`;
       for(let sum=0; sum<=2*s.total; sum++) {
          if(s.dp[s.dp.length-1][sum] > 0 || sum === s.target + s.offset || sum === s.offset) {
             let border = s.i === i ? '2px solid var(--accent)' : '1px solid var(--border)';
             let bg = s.dp[i][sum] > 0 ? 'rgba(52, 211, 153, 0.2)' : 'var(--surface)';
             html += `<div style="width:30px; height:20px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-size:11px;">${s.dp[i][sum]}</div>`;
          }
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Longest Increasing Path in a Matrix', short: 'LIP in Matrix',
  idea: 'DFS with Memoization. `memo[i][j]` stores the longest increasing path starting at `(i, j)`.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: '9,9,4; 6,6,8; 2,1,1', hint: 'comma-separated rows',
  code: [
    'def longestIncreasingPath(matrix):',
    '    m, n = len(matrix), len(matrix[0])',
    '    memo = [[0] * n for _ in range(m)]',
    '    ',
    '    def dfs(i, j):',
    '        if memo[i][j]: return memo[i][j]',
    '        ans = 1',
    '        for di, dj in [(0,1),(1,0),(0,-1),(-1,0)]:',
    '            ni, nj = i + di, j + dj',
    '            if 0<=ni<m and 0<=nj<n and matrix[ni][nj] > matrix[i][j]:',
    '                ans = max(ans, 1 + dfs(ni, nj))',
    '        memo[i][j] = ans',
    '        return ans',
    '        ',
    '    return max(dfs(i, j) for i in range(m) for j in range(n))'
  ],
  parse(str) {
    const grid = str.split(';').map(r => r.split(',').map(Number));
    return { grid, m: grid.length, n: grid[0].length };
  },
  run({ grid, m, n }) {
    const { F, snap } = avRecorder();
    let memo = Array.from({length: m}, () => new Array(n).fill(0));
    const s = { grid, memo: JSON.parse(JSON.stringify(memo)), m, n, cur: null };
    
    snap(3, 'Start DFS with Memo.', s);
    
    let maxLen = 0;
    const dfs = (i, j) => {
       if (memo[i][j]) return memo[i][j];
       let ans = 1;
       const dirs = [[0,1],[1,0],[0,-1],[-1,0]];
       for (const [di, dj] of dirs) {
          const ni = i + di, nj = j + dj;
          if (ni>=0 && ni<m && nj>=0 && nj<n && grid[ni][nj] > grid[i][j]) {
             ans = Math.max(ans, 1 + dfs(ni, nj));
          }
       }
       memo[i][j] = ans;
       s.memo = JSON.parse(JSON.stringify(memo));
       s.cur = [i, j];
       snap(11, `Memoized cell (${i}, ${j}) = ${ans}`, s);
       return ans;
    };
    
    for (let i = 0; i < m; i++) {
       for (let j = 0; j < n; j++) {
          maxLen = Math.max(maxLen, dfs(i, j));
       }
    }
    
    s.cur = null;
    snap(14, `Done. Max length = ${maxLen}`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    for (let i=0; i<s.m; i++) {
       html += '<div style="display:flex; gap:4px;">';
       for (let j=0; j<s.n; j++) {
          let border = s.cur && s.cur[0]===i && s.cur[1]===j ? '2px solid var(--accent)' : '1px solid var(--border)';
          let bg = s.memo[i][j] > 0 ? 'rgba(52,211,153,0.2)' : 'var(--surface)';
          html += `<div style="width:50px; height:50px; display:flex; flex-direction:column; align-items:center; justify-content:center; border:${border}; background:${bg};">
             <div style="font-size:10px; color:var(--text-dim);">${s.grid[i][j]}</div>
             <div style="font-weight:bold;">${s.memo[i][j] || ''}</div>
          </div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('17_dp_2d', {
  title: 'Distinct Subsequences', short: 'Distinct Subsequences',
  idea: '`dp[i][j]` is the number of distinct subsequences of `s[:i]` that equal `t[:j]`. If `s[i-1] == t[j-1]`, we can either use it (`dp[i-1][j-1]`) or not use it (`dp[i-1][j]`). If mismatch, we can only not use it.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: 'rabbbit, rabbit', hint: 's, t',
  code: [
    'def numDistinct(s, t):',
    '    m, n = len(s), len(t)',
    '    dp = [[0] * (n + 1) for _ in range(m + 1)]',
    '    for i in range(m + 1): dp[i][0] = 1',
    '    ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            if s[i-1] == t[j-1]:',
    '                dp[i][j] = dp[i-1][j-1] + dp[i-1][j]',
    '            else:',
    '                dp[i][j] = dp[i-1][j]',
    '                ',
    '    return dp[m][n]'
  ],
  parse(str) {
    const parts = str.split(',');
    return { s_str: parts[0].trim(), t_str: parts[1].trim() };
  },
  run({ s_str, t_str }) {
    const { F, snap } = avRecorder();
    const m = s_str.length, n = t_str.length;
    let dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    for (let i = 0; i <= m; i++) dp[i][0] = 1;
    
    const s = { s_str, t_str, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(4, 'Initialize DP table. Base case: empty t has 1 subsequence in any s.', s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          if (s_str[i-1] === t_str[j-1]) {
             dp[i][j] = dp[i-1][j-1] + dp[i-1][j];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(9, `Match! Use (${dp[i-1][j-1]}) + Don't use (${dp[i-1][j]}) = ${dp[i][j]}`, s);
          } else {
             dp[i][j] = dp[i-1][j];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Mismatch. Can't use. Take from above = ${dp[i][j]}`, s);
          }
       }
    }
    s.i = null; s.j = null;
    snap(13, `Total subsequences = ${dp[m][n]}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    html += '<div style="display:flex; gap:4px;"><div style="width:36px;"></div><div style="width:36px;text-align:center;">""</div>';
    for (let j = 0; j < state.n; j++) html += `<div style="width:36px; text-align:center; font-weight:bold;">${state.t_str[j]}</div>`;
    html += '</div>';
    
    for (let i = 0; i <= state.m; i++) {
       html += '<div style="display:flex; gap:4px;">';
       html += `<div style="width:36px; font-weight:bold; display:flex; align-items:center;">${i===0 ? '""' : state.s_str[i-1]}</div>`;
       for (let j = 0; j <= state.n; j++) {
          const isCurr = state.i === i && state.j === j;
          html += `<div style="width:36px; height:36px; display:flex; align-items:center; justify-content:center; border:1px solid var(--border); ${isCurr?'border:2px solid var(--accent); background:rgba(56,189,248,0.1);':''}">${state.dp[i][j]}</div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Burst Balloons', short: 'Burst Balloons',
  idea: 'Interval DP. `dp[left][right]` is max coins from bursting balloons in `(left, right)`. We try each balloon `i` as the LAST balloon to burst.',
  complexity: 'Time O(N^3) · Space O(N^2)',
  input: '3,1,5,8', hint: 'comma-separated balloons',
  code: [
    'def maxCoins(nums):',
    '    nums = [1] + nums + [1]',
    '    n = len(nums)',
    '    dp = [[0] * n for _ in range(n)]',
    '    ',
    '    for length in range(2, n):',
    '        for left in range(n - length):',
    '            right = left + length',
    '            for i in range(left + 1, right):',
    '                coins = nums[left] * nums[i] * nums[right]',
    '                coins += dp[left][i] + dp[i][right]',
    '                dp[left][right] = max(dp[left][right], coins)',
    '                ',
    '    return dp[0][n - 1]'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    nums = [1, ...nums, 1];
    const n = nums.length;
    let dp = Array.from({length: n}, () => new Array(n).fill(0));
    const s = { nums, n, dp: JSON.parse(JSON.stringify(dp)), left: null, right: null, i: null };
    
    snap(4, 'Padded array with 1s at ends.', s);
    
    for (let length = 2; length < n; length++) {
       for (let left = 0; left < n - length; left++) {
          let right = left + length;
          s.left = left; s.right = right;
          for (let i = left + 1; i < right; i++) {
             s.i = i;
             let coins = nums[left] * nums[i] * nums[right];
             coins += dp[left][i] + dp[i][right];
             dp[left][right] = Math.max(dp[left][right], coins);
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Interval (${left}, ${right}). Balloon ${i} burst last. Coins = ${coins}. dp[${left}][${right}] = ${dp[left][right]}.`, s);
          }
       }
    }
    
    s.left = null; s.right = null; s.i = null;
    snap(14, `Done. Max coins = ${dp[0][n-1]}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; gap:4px; margin-bottom:10px;">';
    for (let i=0; i<state.n; i++) {
       html += `<div style="width:40px; text-align:center; ${i===0||i===state.n-1?'color:var(--text-dim);':''}">${state.nums[i]}</div>`;
    }
    html += '</div>';
    
    html += '<div style="display:flex; flex-direction:column; gap:4px;">';
    for (let r=0; r<state.n; r++) {
       html += '<div style="display:flex; gap:4px;">';
       for (let c=0; c<state.n; c++) {
          let isCurr = state.left === r && state.right === c;
          let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
          let bg = state.dp[r][c] > 0 ? 'rgba(52,211,153,0.1)' : 'var(--surface)';
          html += `<div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg};">${state.dp[r][c] || ''}</div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Regular Expression Matching', short: 'RegEx Match',
  idea: '`dp[i][j]` is true if `s[:i]` matches `p[:j]`. Handles `.` (any char) and `*` (0 or more of preceding char).',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: 'aab, c*a*b', hint: 's, p',
  code: [
    'def isMatch(s, p):',
    '    m, n = len(s), len(p)',
    '    dp = [[False] * (n + 1) for _ in range(m + 1)]',
    '    dp[0][0] = True',
    '    for j in range(1, n + 1):',
    '        if p[j-1] == "*":',
    '            dp[0][j] = dp[0][j-2]',
    '    ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            if p[j-1] == s[i-1] or p[j-1] == ".":',
    '                dp[i][j] = dp[i-1][j-1]',
    '            elif p[j-1] == "*":',
    '                dp[i][j] = dp[i][j-2]',
    '                if p[j-2] == s[i-1] or p[j-2] == ".":',
    '                    dp[i][j] = dp[i][j] or dp[i-1][j]',
    '                    ',
    '    return dp[m][n]'
  ],
  parse(str) {
    const parts = str.split(',');
    return { s_str: parts[0].trim(), p_str: parts[1].trim() };
  },
  run({ s_str, p_str }) {
    const { F, snap } = avRecorder();
    const m = s_str.length, n = p_str.length;
    let dp = Array.from({length: m+1}, () => new Array(n+1).fill(false));
    dp[0][0] = true;
    for (let j = 1; j <= n; j++) {
       if (p_str[j-1] === '*') dp[0][j] = dp[0][j-2];
    }
    const s = { s_str, p_str, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(5, 'Initialize DP. Handled patterns like c* matching empty string.', s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          if (p_str[j-1] === s_str[i-1] || p_str[j-1] === '.') {
             dp[i][j] = dp[i-1][j-1];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Match! dp[${i}][${j}] = ${dp[i][j]}`, s);
          } else if (p_str[j-1] === '*') {
             dp[i][j] = dp[i][j-2]; // 0 occurrences
             if (p_str[j-2] === s_str[i-1] || p_str[j-2] === '.') {
                dp[i][j] = dp[i][j] || dp[i-1][j]; // 1+ occurrences
             }
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(15, `* wildcard. 0 occ: ${dp[i][j-2]}, 1+ occ: ${dp[i-1][j]}. Result: ${dp[i][j]}`, s);
          } else {
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(10, `Mismatch. dp[${i}][${j}] = false`, s);
          }
       }
    }
    s.i = null; s.j = null;
    snap(17, `Match Result = ${dp[m][n]}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    html += '<div style="display:flex; gap:4px;"><div style="width:36px;"></div><div style="width:36px;text-align:center;">""</div>';
    for (let j=0; j<state.n; j++) html += `<div style="width:36px; text-align:center; font-weight:bold;">${state.p_str[j]}</div>`;
    html += '</div>';
    
    for (let i=0; i<=state.m; i++) {
       html += '<div style="display:flex; gap:4px;">';
       html += `<div style="width:36px; font-weight:bold; display:flex; align-items:center;">${i===0?'""':state.s_str[i-1]}</div>`;
       for (let j=0; j<=state.n; j++) {
          let isCurr = state.i === i && state.j === j;
          let bg = state.dp[i][j] ? 'rgba(52,211,153,0.2)' : 'var(--surface)';
          let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
          html += `<div style="width:36px; height:36px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg};">${state.dp[i][j]?'T':'F'}</div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Longest Palindromic Subsequence', short: 'LPS',
  idea: 'Interval DP. `dp[i][j]` is LPS in `s[i:j+1]`. If `s[i] == s[j]`, `dp[i][j] = 2 + dp[i+1][j-1]`. Else `max(dp[i+1][j], dp[i][j-1])`.',
  complexity: 'Time O(N^2) · Space O(N^2)',
  input: 'bbbab', hint: 'string s',
  code: [
    'def longestPalindromeSubseq(s):',
    '    n = len(s)',
    '    dp = [[0] * n for _ in range(n)]',
    '    ',
    '    for i in range(n):',
    '        dp[i][i] = 1',
    '        ',
    '    for length in range(2, n + 1):',
    '        for i in range(n - length + 1):',
    '            j = i + length - 1',
    '            if s[i] == s[j]:',
    '                dp[i][j] = 2 + (dp[i+1][j-1] if i+1 <= j-1 else 0)',
    '            else:',
    '                dp[i][j] = max(dp[i+1][j], dp[i][j-1])',
    '                ',
    '    return dp[0][n-1]'
  ],
  parse(str) {
    return { str: str.trim(), n: str.trim().length };
  },
  run({ str, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: n}, () => new Array(n).fill(0));
    for(let i=0; i<n; i++) dp[i][i] = 1;
    
    const s = { str, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(5, 'Base cases: length 1 strings are palindromes of length 1.', s);
    
    for (let length = 2; length <= n; length++) {
       for (let i = 0; i < n - length + 1; i++) {
          let j = i + length - 1;
          s.i = i; s.j = j;
          if (str[i] === str[j]) {
             dp[i][j] = 2 + (i+1 <= j-1 ? dp[i+1][j-1] : 0);
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Match! s[${i}] == s[${j}]. dp = 2 + dp[${i+1}][${j-1}] = ${dp[i][j]}`, s);
          } else {
             dp[i][j] = Math.max(dp[i+1][j], dp[i][j-1]);
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(13, `Mismatch. max(dp[${i+1}][${j}], dp[${i}][${j-1}]) = ${dp[i][j]}`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(15, `LPS length = ${dp[0][n-1]}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    for(let i=0; i<state.n; i++) {
       html += '<div style="display:flex; gap:4px;">';
       for(let j=0; j<state.n; j++) {
          let isCurr = state.i === i && state.j === j;
          let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
          let bg = state.dp[i][j] > 0 ? 'rgba(56,189,248,0.1)' : 'var(--surface)';
          let content = j >= i ? state.dp[i][j] : '';
          html += `<div style="width:36px; height:36px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg};">${content}</div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});


defineAlgo('17_dp_2d', {
  title: 'Shortest Path Visiting All Nodes', short: 'Visit All Nodes',
  idea: 'Bitmask DP using BFS. State is `(node, mask)`. We track `dist[node][mask]` to find the shortest path visiting all nodes.',
  complexity: 'Time O(N * 2^N) · Space O(N * 2^N)',
  input: '1,2,3; 0; 0; 0', hint: 'graph adjacency list separated by ;',
  code: [
    'def shortestPathLength(graph):',
    '    n = len(graph)',
    '    if n == 1: return 0',
    '    ',
    '    q = deque()',
    '    visited = set()',
    '    ',
    '    for i in range(n):',
    '        mask = 1 << i',
    '        q.append((i, mask, 0))',
    '        visited.add((i, mask))',
    '        ',
    '    while q:',
    '        u, mask, dist = q.popleft()',
    '        if mask == (1 << n) - 1:',
    '            return dist',
    '            ',
    '        for v in graph[u]:',
    '            next_mask = mask | (1 << v)',
    '            if (v, next_mask) not in visited:',
    '                visited.add((v, next_mask))',
    '                q.append((v, next_mask, dist + 1))',
    '                ',
    '    return -1'
  ],
  parse(str) {
    const graph = str.split(';').map(row => row.trim() ? row.split(',').map(Number) : []);
    return { graph, n: graph.length };
  },
  run({ graph, n }) {
    const { F, snap } = avRecorder();
    if (n === 1) return snap(2, 'n=1, dist=0', {}) && F;
    
    let q = [];
    let visited = new Set();
    
    for (let i = 0; i < n; i++) {
       const mask = 1 << i;
       q.push({u: i, mask, dist: 0});
       visited.add(`${i},${mask}`);
    }
    
    const s = { graph, n, q: [...q], u: null, mask: null, dist: null };
    snap(8, 'Start BFS from every node with its own bitmask.', s);
    
    const targetMask = (1 << n) - 1;
    let step = 0;
    
    while (q.length > 0 && step < 100) {
       step++;
       const { u, mask, dist } = q.shift();
       s.q = [...q];
       s.u = u; s.mask = mask; s.dist = dist;
       
       if (mask === targetMask) {
          snap(14, `Found state with all bits set! Shortest path = ${dist}`, s);
          return F;
       }
       
       snap(16, `Pop node ${u}, mask ${mask.toString(2).padStart(n, '0')}, dist ${dist}`, s);
       
       for (const v of graph[u]) {
          const nextMask = mask | (1 << v);
          if (!visited.has(`${v},${nextMask}`)) {
             visited.add(`${v},${nextMask}`);
             q.push({u: v, mask: nextMask, dist: dist + 1});
          }
       }
       s.q = [...q];
    }
    
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono);">Current Node: ${state.u !== null ? state.u : '-'}</div>`;
    html += `<div style="font-family:var(--mono);">Current Mask: ${state.mask !== null ? state.mask.toString(2).padStart(state.n, '0') : '-'}</div>`;
    html += `<div style="font-family:var(--mono);">Current Dist: ${state.dist !== null ? state.dist : '-'}</div>`;
    
    html += `<div style="margin-top:10px; font-weight:bold;">Queue Size: ${state.q.length}</div>`;
    html += '<div style="display:flex; flex-wrap:wrap; gap:4px;">';
    for (let i=0; i<Math.min(state.q.length, 20); i++) {
       html += `<div style="padding:4px; border:1px solid var(--border); font-size:10px; font-family:var(--mono);">u:${state.q[i].u} m:${state.q[i].mask.toString(2)} d:${state.q[i].dist}</div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Numbers At Most N Given Digit Set', short: 'Numbers At Most N',
  idea: 'Digit DP. We construct numbers <= N using given digits. `dp[i]` is ways to form valid suffix from digit `i`.',
  complexity: 'Time O(log N) · Space O(log N)',
  input: '1,3,5,7; 100', hint: 'digits; N',
  code: [
    'def atMostNGivenDigitSet(digits, n):',
    '    s = str(n)',
    '    k = len(s)',
    '    dp = [0] * k + [1]',
    '    ',
    '    for i in range(k - 1, -1, -1):',
    '        for d in digits:',
    '            if d < s[i]:',
    '                dp[i] += len(digits) ** (k - i - 1)',
    '            elif d == s[i]:',
    '                dp[i] += dp[i + 1]',
    '                ',
    '    ans = sum(len(digits) ** i for i in range(1, k))',
    '    return ans + dp[0]'
  ],
  parse(str) {
    const parts = str.split(';');
    return { digits: parts[0].split(',').map(s=>s.trim()), n_str: parts[1].trim() };
  },
  run({ digits, n_str }) {
    const { F, snap } = avRecorder();
    const k = n_str.length;
    let dp = new Array(k + 1).fill(0);
    dp[k] = 1;
    
    const s = { digits, n_str, k, dp: [...dp], i: null, ans: 0 };
    snap(4, 'Initialize DP. dp[k] = 1 (empty suffix is valid).', s);
    
    for (let i = k - 1; i >= 0; i--) {
       s.i = i;
       for (const d of digits) {
          if (d < n_str[i]) {
             dp[i] += Math.pow(digits.length, k - i - 1);
          } else if (d === n_str[i]) {
             dp[i] += dp[i + 1];
          }
       }
       s.dp = [...dp];
       snap(10, `At index ${i} (target digit '${n_str[i]}'). dp[${i}] = ${dp[i]}`, s);
    }
    
    let ans = 0;
    for (let i = 1; i < k; i++) ans += Math.pow(digits.length, i);
    ans += dp[0];
    
    s.i = null; s.ans = ans;
    snap(13, `Result = shorter lengths + same length (${dp[0]}) = ${ans}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono);">Target N: ${state.n_str}</div>`;
    html += `<div style="font-family:var(--mono);">Digits: [${state.digits.join(', ')}]</div>`;
    html += `<div style="display:flex; gap:4px; margin-top:10px;">`;
    for(let i=0; i<=state.k; i++) {
       let isCurr = state.i === i;
       html += `<div style="width:40px; height:40px; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1px solid var(--border); ${isCurr?'border-color:var(--accent);':''}"><div style="font-size:10px;">dp[${i}]</div><div style="font-weight:bold;">${state.dp[i]}</div></div>`;
    }
    html += '</div>';
    html += `<div style="margin-top:10px; font-weight:bold; color:var(--accent);">Total: ${state.ans}</div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Count Special Integers', short: 'Count Special',
  idea: 'Digit DP for counting numbers with unique digits <= N. We use memoization `(idx, mask, is_bound, is_started)`.',
  complexity: 'Time O(log N * 2^10) · Space O(log N * 2^10)',
  input: '20', hint: 'N',
  code: [
    'def countSpecialNumbers(n):',
    '    s = str(n)',
    '    memo = {}',
    '    def dp(i, mask, bound, started):',
    '        if i == len(s): return 1 if started else 0',
    '        state = (i, mask, bound, started)',
    '        if state in memo: return memo[state]',
    '        ',
    '        ans = 0',
    '        limit = int(s[i]) if bound else 9',
    '        for d in range(limit + 1):',
    '            if d == 0 and not started:',
    '                ans += dp(i+1, mask, bound and (d == limit), False)',
    '            elif (mask & (1 << d)) == 0:',
    '                ans += dp(i+1, mask | (1<<d), bound and (d == limit), True)',
    '        memo[state] = ans',
    '        return ans',
    '    return dp(0, 0, True, False)'
  ],
  parse(str) {
    return { n_str: str.trim() };
  },
  run({ n_str }) {
    const { F, snap } = avRecorder();
    let memo = {};
    const s = { n_str, memo: {}, cur: null };
    snap(3, 'Start Digit DP.', s);
    
    const dp = (i, mask, bound, started) => {
       if (i === n_str.length) return started ? 1 : 0;
       const key = `${i},${mask},${bound},${started}`;
       if (key in memo) return memo[key];
       
       let ans = 0;
       let limit = bound ? parseInt(n_str[i]) : 9;
       
       for (let d = 0; d <= limit; d++) {
          if (d === 0 && !started) {
             ans += dp(i+1, mask, bound && d === limit, false);
          } else if ((mask & (1<<d)) === 0) {
             ans += dp(i+1, mask | (1<<d), bound && d === limit, true);
          }
       }
       memo[key] = ans;
       s.memo = JSON.parse(JSON.stringify(memo));
       s.cur = key;
       snap(15, `Memoized state: idx=${i}, mask=${mask.toString(2)}, bound=${bound}, started=${started} => ${ans}`, s);
       return ans;
    };
    
    let ans = dp(0, 0, true, false);
    s.cur = null;
    snap(18, `Done. Total unique digit numbers <= ${n_str} is ${ans}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px;">Target N: ${state.n_str}</div>`;
    html += `<div style="font-family:var(--mono);">Memoized States: ${Object.keys(state.memo).length}</div>`;
    if (state.cur) {
       html += `<div style="color:var(--accent); font-weight:bold; margin-top:10px;">Computed: ${state.cur} => ${state.memo[state.cur]}</div>`;
    }
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('18_greedy', {
  title: 'Maximize Sum Of Array After K Negations', short: 'Max Sum K Negations',
  idea: 'Greedily negate the most negative numbers first. If K > 0 and no negatives remain, repeatedly negate the smallest absolute value (which just flips its sign if K is odd).',
  complexity: 'Time O(N log N) · Space O(1)',
  input: '4, -5, 4, -3, 1, 2; 2', hint: 'nums; k',
  code: [
    'def largestSumAfterKNegations(nums, k):',
    '    nums.sort()',
    '    ',
    '    for i in range(len(nums)):',
    '        if nums[i] < 0 and k > 0:',
    '            nums[i] = -nums[i]',
    '            k -= 1',
    '            ',
    '    if k % 2 == 1:',
    '        nums.sort()',
    '        nums[0] = -nums[0]',
    '        ',
    '    return sum(nums)'
  ],
  parse(str) {
    const parts = str.split(';');
    return { nums: parts[0].split(',').map(Number), k: parseInt(parts[1]) };
  },
  run({ nums, k }) {
    const { F, snap } = avRecorder();
    nums.sort((a,b) => a - b);
    
    let currentK = k;
    const s = { nums: [...nums], currentK, i: null };
    snap(3, `Sort array: [${nums.join(', ')}]. Remaining K = ${currentK}`, s);
    
    for (let i = 0; i < nums.length; i++) {
       s.i = i;
       if (nums[i] < 0 && currentK > 0) {
          nums[i] = -nums[i];
          currentK--;
          s.nums = [...nums];
          s.currentK = currentK;
          snap(7, `nums[${i}] is negative and K > 0. Negate it to ${nums[i]}. Remaining K = ${currentK}`, s);
       } else {
          snap(5, `nums[${i}] is >= 0 or K is 0. Move to next.`, s);
       }
    }
    s.i = null;
    
    if (currentK % 2 === 1) {
       nums.sort((a,b) => a - b);
       s.nums = [...nums];
       snap(11, `K is odd (${currentK}). Re-sort array to find the smallest absolute value.`, s);
       nums[0] = -nums[0];
       s.nums = [...nums];
       snap(12, `Negate the smallest value nums[0] to ${nums[0]}.`, s);
    }
    
    const sum = nums.reduce((a,b)=>a+b, 0);
    snap(14, `Done. Max sum = ${sum}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px;">Remaining K: ${state.currentK}</div>`;
    html += '<div style="display:flex; gap:8px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = 'var(--surface)';
       html += `<div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-weight:bold;">${state.nums[i]}</div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Maximum Subarray', short: 'Kadane\'s',
  idea: 'Kadane\'s algorithm: Keep a running sum. If it goes below 0, it contributes negatively to any future subarray, so reset it to 0. Keep track of the max sum seen.',
  complexity: 'Time O(N) · Space O(1)',
  input: '-2,1,-3,4,-1,2,1,-5,4', hint: 'comma-separated nums',
  code: [
    'def maxSubArray(nums):',
    '    max_sum = nums[0]',
    '    curr_sum = 0',
    '    ',
    '    for n in nums:',
    '        if curr_sum < 0:',
    '            curr_sum = 0',
    '        curr_sum += n',
    '        max_sum = max(max_sum, curr_sum)',
    '        ',
    '    return max_sum'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let max_sum = nums[0];
    let curr_sum = 0;
    
    const s = { nums, max_sum, curr_sum, i: null };
    snap(3, 'Initialize max_sum to first element, curr_sum to 0.', s);
    
    for (let i = 0; i < nums.length; i++) {
       s.i = i;
       if (curr_sum < 0) {
          curr_sum = 0;
          s.curr_sum = curr_sum;
          snap(7, 'curr_sum < 0, resetting to 0 because a negative prefix will strictly decrease future sums.', s);
       }
       curr_sum += nums[i];
       s.curr_sum = curr_sum;
       max_sum = Math.max(max_sum, curr_sum);
       s.max_sum = max_sum;
       snap(9, `Add nums[${i}] (${nums[i]}) to curr_sum. curr_sum=${curr_sum}, max_sum=${max_sum}.`, s);
    }
    
    s.i = null;
    snap(11, `Done. Max subarray sum = ${max_sum}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:5px;">Current Sum: <span style="color:var(--accent); font-weight:bold;">${state.curr_sum}</span></div>`;
    html += `<div style="font-family:var(--mono); margin-bottom:10px;">Global Max Sum: <span style="color:#34d399; font-weight:bold;">${state.max_sum}</span></div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:4px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isCurr ? 'rgba(56,189,248,0.1)' : 'var(--surface)';
       html += `<div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-weight:bold;">${state.nums[i]}</div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Jump Game', short: 'Jump Game',
  idea: 'Greedy approach: Keep track of the furthest index we can reach (`goal` or `max_reach`). If we iterate to an index beyond our `max_reach`, we can\'t go further (return False).',
  complexity: 'Time O(N) · Space O(1)',
  input: '2,3,1,1,4', hint: 'comma-separated jump lengths',
  code: [
    'def canJump(nums):',
    '    max_reach = 0',
    '    for i in range(len(nums)):',
    '        if i > max_reach:',
    '            return False',
    '        max_reach = max(max_reach, i + nums[i])',
    '        if max_reach >= len(nums) - 1:',
    '            return True',
    '    return True'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let max_reach = 0;
    const n = nums.length;
    const s = { nums, max_reach, i: null };
    
    snap(2, 'Initialize max_reach to index 0.', s);
    
    for (let i = 0; i < n; i++) {
       s.i = i;
       if (i > max_reach) {
          snap(5, `Index ${i} is beyond our max_reach of ${max_reach}. We cannot proceed. Return False.`, s);
          return F;
       }
       
       let new_reach = i + nums[i];
       if (new_reach > max_reach) {
          max_reach = new_reach;
          s.max_reach = max_reach;
          snap(6, `At index ${i}, we can jump up to ${nums[i]} steps. New max_reach = max(old, ${i}+${nums[i]}) = ${max_reach}.`, s);
       } else {
          snap(6, `At index ${i}, jump length ${nums[i]} gives reach ${i+nums[i]}, which is not better than current max_reach ${max_reach}.`, s);
       }
       
       if (max_reach >= n - 1) {
          snap(8, `max_reach ${max_reach} covers the last index. Return True.`, s);
          return F;
       }
    }
    
    s.i = null;
    snap(9, `Successfully iterated the array. Return True.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px;">Furthest Reachable Index: <span style="color:#34d399; font-weight:bold;">${state.max_reach}</span></div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:4px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let isReachable = i <= state.max_reach;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isReachable ? 'rgba(52,211,153,0.1)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:2px;">i=${i}</div>
          <div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-weight:bold; color:${isReachable?'var(--text)':'var(--text-dim)'};">${state.nums[i]}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Jump Game II', short: 'Jump Game II',
  idea: 'We need minimum jumps. Maintain a `current_jump_end` and `farthest` index. Iterate through the array; when you hit `current_jump_end`, you *must* jump, so increment jumps and update `current_jump_end` to `farthest`.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2,3,1,1,4', hint: 'comma-separated jump lengths',
  code: [
    'def jump(nums):',
    '    jumps = 0',
    '    curr_end = 0',
    '    farthest = 0',
    '    ',
    '    for i in range(len(nums) - 1):',
    '        farthest = max(farthest, i + nums[i])',
    '        ',
    '        if i == curr_end:',
    '            jumps += 1',
    '            curr_end = farthest',
    '            ',
    '    return jumps'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let jumps = 0, curr_end = 0, farthest = 0;
    const n = nums.length;
    const s = { nums, jumps, curr_end, farthest, i: null };
    
    snap(4, 'Initialize jumps=0, curr_end=0, farthest=0.', s);
    
    for (let i = 0; i < n - 1; i++) {
       s.i = i;
       farthest = Math.max(farthest, i + nums[i]);
       s.farthest = farthest;
       
       snap(7, `At index ${i} (jump=${nums[i]}), farthest reach from here is ${i+nums[i]}. Global farthest is now ${farthest}.`, s);
       
       if (i === curr_end) {
          jumps++;
          curr_end = farthest;
          s.jumps = jumps;
          s.curr_end = curr_end;
          snap(10, `Reached curr_end (${i}). We must jump now. Jumps = ${jumps}, new curr_end = ${curr_end}.`, s);
       }
    }
    
    s.i = null;
    snap(12, `Finished. Minimum jumps required = ${jumps}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:10px;">
        <div>Jumps: <span style="color:var(--accent); font-weight:bold;">${state.jumps}</span></div>
        <div>Current Jump End: <span style="color:#ef4444; font-weight:bold;">${state.curr_end}</span></div>
        <div>Farthest Known Reach: <span style="color:#34d399; font-weight:bold;">${state.farthest}</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:4px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let isEnd = state.curr_end === i;
       let isFarthest = state.farthest === i;
       
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       if (isEnd) border = '2px solid #ef4444';
       
       let bg = i <= state.farthest ? 'rgba(52,211,153,0.1)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:2px;">i=${i}</div>
          <div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-weight:bold;">${state.nums[i]}</div>
          <div style="font-size:10px; color:#34d399; height:12px; margin-top:2px;">${isFarthest?'farthest':''}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('18_greedy', {
  title: 'Gas Station', short: 'Gas Station',
  idea: 'If total gas < total cost, return -1. Otherwise, a solution exists. We keep a `curr_tank`. If `curr_tank < 0` at station `i`, it means no station from `start` to `i` can be the answer, so we reset `start` to `i + 1` and `curr_tank` to 0.',
  complexity: 'Time O(N) · Space O(1)',
  input: '1,2,3,4,5; 3,4,5,1,2', hint: 'gas; cost',
  code: [
    'def canCompleteCircuit(gas, cost):',
    '    if sum(gas) < sum(cost):',
    '        return -1',
    '        ',
    '    curr_tank = 0',
    '    start = 0',
    '    ',
    '    for i in range(len(gas)):',
    '        curr_tank += gas[i] - cost[i]',
    '        if curr_tank < 0:',
    '            start = i + 1',
    '            curr_tank = 0',
    '            ',
    '    return start'
  ],
  parse(str) {
    const parts = str.split(';');
    return { gas: parts[0].split(',').map(Number), cost: parts[1].split(',').map(Number) };
  },
  run({ gas, cost }) {
    const { F, snap } = avRecorder();
    const sumGas = gas.reduce((a,b)=>a+b,0);
    const sumCost = cost.reduce((a,b)=>a+b,0);
    const n = gas.length;
    
    let s = { gas, cost, n, start: 0, curr_tank: 0, sumGas, sumCost, i: null };
    
    if (sumGas < sumCost) {
       snap(2, `Total gas (${sumGas}) < Total cost (${sumCost}). Impossible. Return -1.`, s);
       return F;
    }
    
    snap(4, `Total gas (${sumGas}) >= Total cost (${sumCost}). A solution must exist. Initialize start=0, curr_tank=0.`, s);
    
    let curr_tank = 0;
    let start = 0;
    
    for (let i = 0; i < n; i++) {
       s.i = i;
       let diff = gas[i] - cost[i];
       curr_tank += diff;
       s.curr_tank = curr_tank;
       
       snap(8, `Station ${i}: gas=${gas[i]}, cost=${cost[i]}. Diff = ${diff}. curr_tank = ${curr_tank}.`, s);
       
       if (curr_tank < 0) {
          start = i + 1;
          curr_tank = 0;
          s.start = start;
          s.curr_tank = curr_tank;
          snap(10, `curr_tank < 0. We cannot reach the next station. Any start point from previous start up to ${i} is invalid. Reset start to ${start}, curr_tank to 0.`, s);
       }
    }
    
    s.i = null;
    snap(12, `Finished checking. The valid start station is ${start}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:10px;">
        <div>Total Gas: ${state.sumGas}</div>
        <div>Total Cost: ${state.sumCost}</div>
        <div>Current Tank: <span style="color:${state.curr_tank<0?'#ef4444':'#34d399'}; font-weight:bold;">${state.curr_tank}</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-direction:column; gap:4px;">';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px;">Gas:</div>';
    for (let i=0; i<state.n; i++) html += `<div style="width:40px; text-align:center; font-weight:bold;">${state.gas[i]}</div>`;
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px;">Cost:</div>';
    for (let i=0; i<state.n; i++) html += `<div style="width:40px; text-align:center; font-weight:bold; color:var(--text-dim);">${state.cost[i]}</div>`;
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px; margin-top:5px;"><div style="width:60px;">Diff:</div>';
    for (let i=0; i<state.n; i++) {
       let diff = state.gas[i] - state.cost[i];
       html += `<div style="width:40px; text-align:center; font-weight:bold; color:${diff<0?'#ef4444':'#34d399'};">${diff > 0 ? '+'+diff : diff}</div>`;
    }
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px; margin-top:5px;"><div style="width:60px;">State:</div>';
    for (let i=0; i<state.n; i++) {
       let isCurr = state.i === i;
       let isStart = state.start === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid transparent';
       html += `<div style="width:40px; height:20px; display:flex; align-items:center; justify-content:center; border:${border};">
          ${isStart ? '<span style="color:#34d399; font-weight:bold; font-size:10px;">START</span>' : ''}
       </div>`;
    }
    html += '</div>';
    
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Best Time to Buy and Sell Stock II', short: 'Stock II',
  idea: 'Greedy approach. Since we can make infinite transactions, we can just capture every single upward price movement. Add `prices[i] - prices[i-1]` to profit if it\'s positive.',
  complexity: 'Time O(N) · Space O(1)',
  input: '7,1,5,3,6,4', hint: 'comma-separated prices',
  code: [
    'def maxProfit(prices):',
    '    profit = 0',
    '    for i in range(1, len(prices)):',
    '        if prices[i] > prices[i-1]:',
    '            profit += prices[i] - prices[i-1]',
    '    return profit'
  ],
  parse(str) {
    return { prices: str.split(',').map(Number) };
  },
  run({ prices }) {
    const { F, snap } = avRecorder();
    let profit = 0;
    const n = prices.length;
    const s = { prices, n, profit, i: null };
    
    snap(2, 'Initialize total profit = 0.', s);
    
    for (let i = 1; i < n; i++) {
       s.i = i;
       if (prices[i] > prices[i-1]) {
          let diff = prices[i] - prices[i-1];
          profit += diff;
          s.profit = profit;
          snap(5, `Price increased from ${prices[i-1]} to ${prices[i]}. Capture this profit (+${diff}). Total = ${profit}.`, s);
       } else {
          snap(3, `Price decreased or stayed same (${prices[i-1]} to ${prices[i]}). Do nothing.`, s);
       }
    }
    
    s.i = null;
    snap(6, `Finished. Max profit = ${profit}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px; font-size:16px;">Total Profit: <span style="color:#34d399; font-weight:bold;">${state.profit}</span></div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:8px; align-items:flex-end; height:100px;">';
    const maxP = Math.max(...state.prices, 1);
    
    for (let i=0; i<state.n; i++) {
       let isCurr = state.i === i || state.i === i+1; 
       let h = (state.prices[i] / maxP) * 80;
       let color = 'var(--surface)';
       if (state.i === i) {
          color = state.prices[i] > state.prices[i-1] ? 'rgba(52,211,153,0.5)' : 'rgba(239,68,68,0.5)';
       }
       
       html += `<div style="display:flex; flex-direction:column; align-items:center; gap:4px;">
          <div style="font-size:10px; color:var(--text-dim);">${state.prices[i]}</div>
          <div style="width:30px; height:${h}px; background:${color}; border:1px solid var(--border);"></div>
          <div style="font-size:10px; font-family:var(--mono);">Day ${i}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Hand of Straights', short: 'Hand of Straights',
  idea: 'Count frequencies. Iterate over sorted keys. If a key has count > 0, we must form a group of size W starting with this key. Decrement counts of `k, k+1, ..., k+W-1` by this count.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '1,2,3,6,2,3,4,7,8; 3', hint: 'hand; groupSize W',
  code: [
    'def isNStraightHand(hand, groupSize):',
    '    if len(hand) % groupSize != 0: return False',
    '    ',
    '    count = collections.Counter(hand)',
    '    for k in sorted(count.keys()):',
    '        if count[k] > 0:',
    '            c = count[k]',
    '            for i in range(k, k + groupSize):',
    '                if count[i] < c:',
    '                    return False',
    '                count[i] -= c',
    '                ',
    '    return True'
  ],
  parse(str) {
    const parts = str.split(';');
    return { hand: parts[0].split(',').map(Number), W: parseInt(parts[1]) };
  },
  run({ hand, W }) {
    const { F, snap } = avRecorder();
    const n = hand.length;
    let s = { hand, W, count: {}, sortedKeys: [], curK: null, curGrp: null };
    
    if (n % W !== 0) {
       snap(2, `Length ${n} is not divisible by groupSize ${W}. Return False.`, s);
       return F;
    }
    
    let count = {};
    for (const card of hand) count[card] = (count[card] || 0) + 1;
    let sortedKeys = Object.keys(count).map(Number).sort((a,b)=>a-b);
    
    s.count = JSON.parse(JSON.stringify(count));
    s.sortedKeys = sortedKeys;
    snap(4, `Count frequencies and sort keys.`, s);
    
    for (const k of sortedKeys) {
       s.curK = k;
       if (count[k] > 0) {
          const c = count[k];
          let grp = [];
          for(let i=k; i<k+W; i++) grp.push(i);
          s.curGrp = grp;
          snap(7, `We have ${c} occurrences of ${k}. We must form ${c} group(s) of [${grp.join(', ')}].`, s);
          
          for (let i = k; i < k + W; i++) {
             if ((count[i] || 0) < c) {
                snap(9, `Need ${c} of card ${i}, but only have ${count[i] || 0}. Cannot form group. Return False.`, s);
                return F;
             }
             count[i] -= c;
          }
          s.count = JSON.parse(JSON.stringify(count));
          snap(10, `Successfully subtracted ${c} from all cards in group.`, s);
       } else {
          s.curGrp = null;
          snap(6, `Count for ${k} is 0. Skip.`, s);
       }
    }
    
    s.curK = null; s.curGrp = null;
    snap(12, 'Successfully processed all cards. Return True.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px;">Group Size (W): ${state.W}</div>`;
    
    html += '<div style="display:flex; gap:10px; flex-wrap:wrap;">';
    for (const k of state.sortedKeys) {
       let inGrp = state.curGrp && state.curGrp.includes(k);
       let isRoot = state.curK === k;
       
       let border = inGrp ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isRoot ? 'rgba(56,189,248,0.2)' : (inGrp ? 'rgba(52,211,153,0.1)' : 'var(--surface)');
       
       html += `<div style="display:flex; flex-direction:column; align-items:center; justify-content:center; width:50px; height:50px; border:${border}; background:${bg}; border-radius:6px;">
          <div style="font-size:14px; font-weight:bold; font-family:var(--mono);">${k}</div>
          <div style="font-size:10px; color:var(--text-dim);">Count: ${state.count[k] || 0}</div>
       </div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('18_greedy', {
  title: 'Merge Triplets to Form Target Triplet', short: 'Merge Triplets',
  idea: 'We can merge any triplets by taking element-wise max. A triplet is usable ONLY if all its elements are <= target elements. We greedily merge all usable triplets and check if the result equals target.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2,5,3; 1,8,4; 1,7,5; 2,7,5| 2,7,5', hint: 'triplets split by ; | target',
  code: [
    'def mergeTriplets(triplets, target):',
    '    res = [0, 0, 0]',
    '    for t in triplets:',
    '        if t[0] <= target[0] and t[1] <= target[1] and t[2] <= target[2]:',
    '            res[0] = max(res[0], t[0])',
    '            res[1] = max(res[1], t[1])',
    '            res[2] = max(res[2], t[2])',
    '            ',
    '    return res == target'
  ],
  parse(str) {
    const parts = str.split('|');
    const triplets = parts[0].split(';').map(t => t.split(',').map(Number));
    const target = parts[1].split(',').map(Number);
    return { triplets, target };
  },
  run({ triplets, target }) {
    const { F, snap } = avRecorder();
    let res = [0, 0, 0];
    const s = { triplets, target, res: [...res], curT: null };
    
    snap(2, 'Initialize result to [0, 0, 0]', s);
    
    for (let i = 0; i < triplets.length; i++) {
       const t = triplets[i];
       s.curT = t;
       
       if (t[0] <= target[0] && t[1] <= target[1] && t[2] <= target[2]) {
          res[0] = Math.max(res[0], t[0]);
          res[1] = Math.max(res[1], t[1]);
          res[2] = Math.max(res[2], t[2]);
          s.res = [...res];
          snap(5, `Triplet [${t}] is usable (all elements <= target). Merge it! Current max = [${res}]`, s);
       } else {
          snap(4, `Triplet [${t}] has an element > target. Discard it.`, s);
       }
    }
    
    s.curT = null;
    const match = res[0] === target[0] && res[1] === target[1] && res[2] === target[2];
    snap(8, `Final max = [${res}]. Target = [${target}]. Matches? ${match}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:15px; font-size:16px;">
        <div>Target: <span style="font-weight:bold; color:var(--text);">[${state.target}]</span></div>
        <div>Current Max: <span style="font-weight:bold; color:var(--accent);">[${state.res}]</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-direction:column; gap:4px;">';
    for (let i=0; i<state.triplets.length; i++) {
       const t = state.triplets[i];
       const isValid = t[0]<=state.target[0] && t[1]<=state.target[1] && t[2]<=state.target[2];
       const isCurr = state.curT === t;
       
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = 'var(--surface)';
       if (isCurr && isValid) bg = 'rgba(52,211,153,0.2)';
       else if (isCurr && !isValid) bg = 'rgba(239,68,68,0.2)';
       
       html += `<div style="padding:8px; border:${border}; background:${bg}; font-family:var(--mono); width:max-content; border-radius:6px;">
          [${t[0]}, ${t[1]}, ${t[2]}] ${isCurr ? (isValid ? '✓ Valid' : '✗ Invalid') : ''}
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Partition Labels', short: 'Partition Labels',
  idea: 'Greedy. Find the last occurrence index for every char. Iterate through string, keeping a running `end = max(end, last_occurrence[char])`. When `i == end`, partition here.',
  complexity: 'Time O(N) · Space O(1) (26 chars max)',
  input: 'ababcbacadefegdehijhklij', hint: 'string s',
  code: [
    'def partitionLabels(s):',
    '    last = {c: i for i, c in enumerate(s)}',
    '    res = []',
    '    size = 0',
    '    end = 0',
    '    ',
    '    for i, c in enumerate(s):',
    '        size += 1',
    '        end = max(end, last[c])',
    '        ',
    '        if i == end:',
    '            res.append(size)',
    '            size = 0',
    '            ',
    '    return res'
  ],
  parse(str) {
    return { s_str: str.trim(), n: str.trim().length };
  },
  run({ s_str, n }) {
    const { F, snap } = avRecorder();
    let last = {};
    for (let i = 0; i < n; i++) last[s_str[i]] = i;
    
    let res = [];
    let size = 0, end = 0;
    
    const s = { s_str, n, last, res: [...res], size, end, i: null };
    snap(2, 'Compute last occurrence index for each character.', s);
    
    for (let i = 0; i < n; i++) {
       s.i = i;
       size++;
       s.size = size;
       
       const charLast = last[s_str[i]];
       end = Math.max(end, charLast);
       s.end = end;
       
       snap(7, `Char '${s_str[i]}' last seen at ${charLast}. Boundary extends to max(end, ${charLast}) = ${end}.`, s);
       
       if (i === end) {
          res.push(size);
          s.res = [...res];
          snap(10, `i == end (${i}). We can safely partition here. Partition size = ${size}.`, s);
          size = 0;
          s.size = size;
       }
    }
    
    s.i = null;
    snap(12, `Finished. Partitions = [${res.join(', ')}]`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:15px; font-size:14px;">
        <div>Required End Boundary: <span style="font-weight:bold; color:#ef4444;">${state.end}</span></div>
        <div>Current Partitions: <span style="font-weight:bold; color:var(--accent);">[${state.res.join(', ')}]</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:2px; font-family:var(--mono);">';
    let currentPartLen = 0;
    for (let i=0; i<state.n; i++) {
       let isCurr = state.i === i;
       let isEnd = state.end === i;
       
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       if (isEnd) border = '2px solid #ef4444';
       
       let bg = 'var(--surface)';
       if (i <= state.end && state.i !== null) bg = 'rgba(239,68,68,0.1)';
       
       html += `<div style="display:flex; flex-direction:column; align-items:center;">
          <div style="font-size:9px; color:var(--text-dim); margin-bottom:1px;">${i}</div>
          <div style="width:24px; height:24px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-weight:bold; font-size:12px;">${state.s_str[i]}</div>
          <div style="font-size:9px; color:var(--accent); margin-top:1px;">${state.last[state.s_str[i]]}</div>
       </div>`;
    }
    html += '</div>';
    html += '<div style="margin-top:10px; font-size:11px; color:var(--text-dim); font-family:var(--mono);">Top number = index. Box = character. Bottom number = last occurrence of this char.</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('18_greedy', {
  title: 'Valid Parenthesis String', short: 'Valid Parenthesis (*)',
  idea: 'Keep track of `min_open` and `max_open` possible open brackets. `(` increments both. `)` decrements both. `*` decrements `min` and increments `max`. `min_open` cannot be < 0. If `max_open < 0`, string is invalid.',
  complexity: 'Time O(N) · Space O(1)',
  input: '(*))', hint: 'string of (, ), and *',
  code: [
    'def checkValidString(s):',
    '    min_open = 0',
    '    max_open = 0',
    '    ',
    '    for c in s:',
    '        if c == "(": ',
    '            min_open += 1',
    '            max_open += 1',
    '        elif c == ")":',
    '            min_open -= 1',
    '            max_open -= 1',
    '        else:',
    '            min_open -= 1',
    '            max_open += 1',
    '            ',
    '        if max_open < 0:',
    '            return False',
    '        min_open = max(min_open, 0)',
    '        ',
    '    return min_open == 0'
  ],
  parse(str) {
    return { str: str.trim(), n: str.trim().length };
  },
  run({ str, n }) {
    const { F, snap } = avRecorder();
    let min_open = 0, max_open = 0;
    const s = { str, n, min_open, max_open, i: null };
    
    snap(3, 'Initialize min_open=0, max_open=0.', s);
    
    for (let i = 0; i < n; i++) {
       s.i = i;
       const c = str[i];
       
       if (c === '(') {
          min_open++; max_open++;
          s.min_open = min_open; s.max_open = max_open;
          snap(6, `Char is '('. Both min and max increment.`, s);
       } else if (c === ')') {
          min_open--; max_open--;
          s.min_open = min_open; s.max_open = max_open;
          snap(9, `Char is ')'. Both min and max decrement.`, s);
       } else {
          min_open--; max_open++;
          s.min_open = min_open; s.max_open = max_open;
          snap(12, `Char is '*'. It can be ')', empty, or '('. Min decrements, Max increments.`, s);
       }
       
       if (max_open < 0) {
          snap(14, `max_open < 0. Too many closing brackets! Return False.`, s);
          return F;
       }
       if (min_open < 0) {
          min_open = 0;
          s.min_open = min_open;
          snap(16, `min_open went below 0. We cannot have negative open brackets, so we clip it to 0.`, s);
       }
    }
    
    s.i = null;
    snap(18, `Finished. min_open == 0? ${min_open === 0}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:15px; font-size:16px;">
        <div>min_open: <span style="font-weight:bold; color:var(--text);">${state.min_open}</span></div>
        <div>max_open: <span style="font-weight:bold; color:var(--text);">${state.max_open}</span></div>
    </div>`;
    
    html += '<div style="display:flex; gap:4px; font-family:var(--mono); font-size:24px;">';
    for (let i=0; i<state.n; i++) {
       let isCurr = state.i === i;
       let color = state.str[i] === '*' ? '#38bdf8' : 'var(--text)';
       let border = isCurr ? '2px solid var(--accent)' : '2px solid transparent';
       html += `<div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; color:${color}; font-weight:bold; border:${border}; border-radius:6px; background:var(--surface);">${state.str[i]}</div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('19_intervals', {
  title: 'Meeting Rooms', short: 'Meeting Rooms',
  idea: 'Sort intervals by start time. Check if any meeting ends after the next one starts (`intervals[i][1] > intervals[i+1][0]`). If so, a person cannot attend both.',
  complexity: 'Time O(N log N) · Space O(1)',
  input: '0,30; 5,10; 15,20', hint: 'comma-separated pairs, separated by ;',
  code: [
    'def canAttendMeetings(intervals):',
    '    intervals.sort(key=lambda x: x[0])',
    '    ',
    '    for i in range(len(intervals) - 1):',
    '        if intervals[i][1] > intervals[i+1][0]:',
    '            return False',
    '            ',
    '    return True'
  ],
  parse(str) {
    const intervals = str.split(';').map(s => s.split(',').map(Number));
    return { intervals };
  },
  run({ intervals }) {
    const { F, snap } = avRecorder();
    intervals.sort((a,b) => a[0] - b[0]);
    const s = { intervals: JSON.parse(JSON.stringify(intervals)), i: null };
    
    snap(2, 'Sort intervals by start time.', s);
    
    for (let i = 0; i < intervals.length - 1; i++) {
       s.i = i;
       if (intervals[i][1] > intervals[i+1][0]) {
          snap(5, `Overlap found! Meeting ${i} ends at ${intervals[i][1]}, but meeting ${i+1} starts at ${intervals[i+1][0]}. Cannot attend all.`, s);
          return F;
       }
       snap(4, `Meeting ${i} ends at ${intervals[i][1]} and next starts at ${intervals[i+1][0]}. No overlap.`, s);
    }
    
    s.i = null;
    snap(8, 'No overlaps found. Can attend all meetings!', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px; font-family:var(--mono);">';
    const maxVal = Math.max(...state.intervals.map(x => x[1]), 10);
    for (let j=0; j<state.intervals.length; j++) {
       const [start, end] = state.intervals[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = state.i === j || state.i === j-1 ? 'rgba(56,189,248,0.8)' : 'rgba(100,100,100,0.5)';
       html += `<div style="display:flex; align-items:center; gap:8px;">
          <div style="width:30px;">[${start},${end}]</div>
          <div style="position:relative; width:calc(100% - 50px); height:24px; background:var(--surface); border:1px solid var(--border);">
             <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px;"></div>
          </div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Merge Intervals', short: 'Merge',
  idea: 'Sort by start time. Build a `merged` list. If the current interval overlaps the last added interval (`curr.start <= last.end`), update `last.end = max(last.end, curr.end)`. Otherwise, append `curr`.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '1,3; 2,6; 8,10; 15,18', hint: 'comma-separated pairs, separated by ;',
  code: [
    'def merge(intervals):',
    '    intervals.sort(key=lambda x: x[0])',
    '    merged = []',
    '    ',
    '    for interval in intervals:',
    '        if not merged or merged[-1][1] < interval[0]:',
    '            merged.append(interval)',
    '        else:',
    '            merged[-1][1] = max(merged[-1][1], interval[1])',
    '            ',
    '    return merged'
  ],
  parse(str) {
    const intervals = str.split(';').map(s => s.split(',').map(Number));
    return { intervals };
  },
  run({ intervals }) {
    const { F, snap } = avRecorder();
    intervals.sort((a,b) => a[0] - b[0]);
    let merged = [];
    const s = { intervals: JSON.parse(JSON.stringify(intervals)), merged: [...merged], i: null };
    
    snap(2, 'Sort intervals by start time.', s);
    
    for (let i = 0; i < intervals.length; i++) {
       s.i = i;
       const curr = intervals[i];
       
       if (merged.length === 0 || merged[merged.length - 1][1] < curr[0]) {
          merged.push([...curr]);
          s.merged = JSON.parse(JSON.stringify(merged));
          snap(7, `Current [${curr}] doesn't overlap with last merged (or merged is empty). Append it.`, s);
       } else {
          const last = merged[merged.length - 1];
          last[1] = Math.max(last[1], curr[1]);
          s.merged = JSON.parse(JSON.stringify(merged));
          snap(9, `Overlap! Current [${curr}] overlaps with [${last[0]}, ${last[1]}]. Extend end to max(${last[1]}, ${curr[1]}) = ${last[1]}.`, s);
       }
    }
    
    s.i = null;
    snap(12, `Finished merging.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">';
    const maxVal = Math.max(...state.intervals.map(x => x[1]), 20);
    
    html += '<div><div style="margin-bottom:5px; color:var(--text-dim);">Sorted Intervals:</div><div style="display:flex; flex-direction:column; gap:4px;">';
    for (let j=0; j<state.intervals.length; j++) {
       const [start, end] = state.intervals[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = state.i === j ? 'rgba(56,189,248,0.8)' : 'rgba(100,100,100,0.5)';
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold;">[${start},${end}]</div>
       </div>`;
    }
    html += '</div></div>';
    
    html += '<div><div style="margin-bottom:5px; color:var(--accent); font-weight:bold;">Merged Result:</div><div style="display:flex; flex-direction:column; gap:4px;">';
    for (let j=0; j<state.merged.length; j++) {
       const [start, end] = state.merged[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:rgba(52,211,153,0.8); border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold; color:#000;">[${start},${end}]</div>
       </div>`;
    }
    html += '</div></div>';
    
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Insert Interval', short: 'Insert',
  idea: 'Traverse sorted intervals. Add intervals ending before newInterval starts. Merge intervals overlapping newInterval. Add intervals starting after newInterval ends.',
  complexity: 'Time O(N) · Space O(N)',
  input: '1,3; 6,9| 2,5', hint: 'intervals split by ; | newInterval',
  code: [
    'def insert(intervals, newInterval):',
    '    res = []',
    '    i = 0',
    '    n = len(intervals)',
    '    ',
    '    while i < n and intervals[i][1] < newInterval[0]:',
    '        res.append(intervals[i])',
    '        i += 1',
    '        ',
    '    while i < n and intervals[i][0] <= newInterval[1]:',
    '        newInterval[0] = min(newInterval[0], intervals[i][0])',
    '        newInterval[1] = max(newInterval[1], intervals[i][1])',
    '        i += 1',
    '    res.append(newInterval)',
    '    ',
    '    while i < n:',
    '        res.append(intervals[i])',
    '        i += 1',
    '        ',
    '    return res'
  ],
  parse(str) {
    const parts = str.split('|');
    const intervals = parts[0].split(';').map(s => s.split(',').map(Number));
    const newInt = parts[1].split(',').map(Number);
    return { intervals, newInt };
  },
  run({ intervals, newInt }) {
    const { F, snap } = avRecorder();
    let res = [];
    let i = 0, n = intervals.length;
    const s = { intervals, newInt: [...newInt], res: [...res], phase: 'before', i };
    
    snap(3, `Start inserting [${newInt}]`, s);
    
    while (i < n && intervals[i][1] < newInt[0]) {
       res.push(intervals[i]);
       s.res = JSON.parse(JSON.stringify(res));
       s.i = i;
       snap(7, `[${intervals[i]}] ends before newInterval starts. Add to result.`, s);
       i++;
    }
    
    s.phase = 'merge';
    while (i < n && intervals[i][0] <= newInt[1]) {
       newInt[0] = Math.min(newInt[0], intervals[i][0]);
       newInt[1] = Math.max(newInt[1], intervals[i][1]);
       s.newInt = [...newInt];
       s.i = i;
       snap(12, `[${intervals[i]}] overlaps. Merge into newInterval: [${newInt}].`, s);
       i++;
    }
    res.push(newInt);
    s.res = JSON.parse(JSON.stringify(res));
    snap(13, `Done merging. Add [${newInt}] to result.`, s);
    
    s.phase = 'after';
    while (i < n) {
       res.push(intervals[i]);
       s.res = JSON.parse(JSON.stringify(res));
       s.i = i;
       snap(17, `[${intervals[i]}] starts after newInterval. Add to result.`, s);
       i++;
    }
    
    s.i = null; s.phase = 'done';
    snap(20, 'Finished insertion.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">';
    const maxVal = Math.max(...state.intervals.map(x => x[1]), state.newInt[1], 20);
    
    html += '<div><div style="margin-bottom:5px; color:var(--text-dim);">Original Intervals & <span style="color:#ef4444; font-weight:bold;">New Interval [${state.newInt[0]},${state.newInt[1]}]</span>:</div><div style="display:flex; flex-direction:column; gap:4px;">';
    for (let j=0; j<state.intervals.length; j++) {
       const [start, end] = state.intervals[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = state.i === j ? 'rgba(56,189,248,0.8)' : 'rgba(100,100,100,0.5)';
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold;">[${start},${end}]</div>
       </div>`;
    }
    html += '</div></div>';
    
    html += '<div><div style="margin-bottom:5px; color:var(--accent); font-weight:bold;">Result:</div><div style="display:flex; flex-direction:column; gap:4px;">';
    for (let j=0; j<state.res.length; j++) {
       const [start, end] = state.res[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:rgba(52,211,153,0.8); border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold; color:#000;">[${start},${end}]</div>
       </div>`;
    }
    html += '</div></div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Non-overlapping Intervals', short: 'Non-overlap',
  idea: 'Greedy. Sort by END time. Iterate through. If the current start < prev_end, it overlaps and must be removed (increment count). Otherwise, we keep it and update prev_end = current end.',
  complexity: 'Time O(N log N) · Space O(1)',
  input: '1,2; 2,3; 3,4; 1,3', hint: 'comma-separated pairs, separated by ;',
  code: [
    'def eraseOverlapIntervals(intervals):',
    '    intervals.sort(key=lambda x: x[1])',
    '    count = 0',
    '    prev_end = float("-inf")',
    '    ',
    '    for start, end in intervals:',
    '        if start >= prev_end:',
    '            prev_end = end',
    '        else:',
    '            count += 1',
    '            ',
    '    return count'
  ],
  parse(str) {
    const intervals = str.split(';').map(s => s.split(',').map(Number));
    return { intervals };
  },
  run({ intervals }) {
    const { F, snap } = avRecorder();
    intervals.sort((a,b) => a[1] - b[1]);
    let count = 0, prev_end = -Infinity;
    const s = { intervals: JSON.parse(JSON.stringify(intervals)), count, prev_end, i: null, removed: [] };
    
    snap(2, 'Sort intervals by END time. This optimally maximizes space for future intervals.', s);
    
    for (let i = 0; i < intervals.length; i++) {
       s.i = i;
       const [start, end] = intervals[i];
       
       if (start >= prev_end) {
          prev_end = end;
          s.prev_end = prev_end;
          snap(8, `[${start}, ${end}] start >= prev_end (${prev_end === -Infinity ? '-inf' : start}). Keep it. prev_end is now ${end}.`, s);
       } else {
          count++;
          s.count = count;
          s.removed.push(i);
          snap(10, `[${start}, ${end}] start < prev_end (${prev_end}). Overlap detected! Remove it. count=${count}.`, s);
       }
    }
    
    s.i = null;
    snap(13, `Done. Removed ${count} intervals.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono);">';
    html += `<div style="font-weight:bold; color:var(--text);">Removed Count: <span style="color:#ef4444;">${state.count}</span></div>`;
    
    const maxVal = Math.max(...state.intervals.map(x => x[1]), 10);
    
    for (let j=0; j<state.intervals.length; j++) {
       const [start, end] = state.intervals[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       
       let isCurr = state.i === j;
       let isRemoved = state.removed.includes(j);
       
       let color = 'rgba(100,100,100,0.5)';
       if (isCurr) color = 'rgba(56,189,248,0.8)';
       if (isRemoved) color = 'rgba(239,68,68,0.3)';
       else if (!isCurr && j < (state.i===null ? state.intervals.length : state.i)) color = 'rgba(52,211,153,0.8)';
       
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border); ${isRemoved?'opacity:0.4;':''}">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold;">[${start},${end}] ${isRemoved?'(X)':''}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('19_intervals', {
  title: 'Meeting Rooms II', short: 'Meeting Rooms II',
  idea: 'Extract start and end times separately and sort them. Use two pointers. If `start[i] < end[j]`, a room is occupied, so increment rooms. Else, a room freed up, so move both pointers.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '0,30; 5,10; 15,20', hint: 'comma-separated pairs, separated by ;',
  code: [
    'def minMeetingRooms(intervals):',
    '    starts = sorted([i[0] for i in intervals])',
    '    ends = sorted([i[1] for i in intervals])',
    '    ',
    '    res, count = 0, 0',
    '    s, e = 0, 0',
    '    ',
    '    while s < len(intervals):',
    '        if starts[s] < ends[e]:',
    '            count += 1',
    '            s += 1',
    '        else:',
    '            count -= 1',
    '            e += 1',
    '        res = max(res, count)',
    '        ',
    '    return res'
  ],
  parse(str) {
    const intervals = str.split(';').map(s => s.split(',').map(Number));
    return { intervals };
  },
  run({ intervals }) {
    const { F, snap } = avRecorder();
    const starts = intervals.map(i => i[0]).sort((a,b)=>a-b);
    const ends = intervals.map(i => i[1]).sort((a,b)=>a-b);
    
    let res = 0, count = 0;
    let s_ptr = 0, e_ptr = 0;
    const s = { starts, ends, s_ptr, e_ptr, res, count };
    
    snap(3, 'Extract and sort start and end times separately.', s);
    
    while (s_ptr < starts.length) {
       if (starts[s_ptr] < ends[e_ptr]) {
          count++;
          res = Math.max(res, count);
          s.count = count; s.res = res;
          snap(9, `starts[${s_ptr}] (${starts[s_ptr]}) < ends[${e_ptr}] (${ends[e_ptr]}). A new meeting started before the earliest end time. Rooms active: ${count}. Max: ${res}`, s);
          s_ptr++;
          s.s_ptr = s_ptr;
       } else {
          count--;
          s.count = count;
          snap(12, `starts[${s_ptr}] (${starts[s_ptr]}) >= ends[${e_ptr}] (${ends[e_ptr]}). A meeting ended. Rooms active: ${count}.`, s);
          e_ptr++;
          s.e_ptr = e_ptr;
       }
    }
    
    snap(16, `All meetings processed. Max rooms required = ${res}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:10px; font-size:14px;">
        <div>Active Rooms: <span style="font-weight:bold; color:var(--text);">${state.count}</span></div>
        <div>Max Rooms (Ans): <span style="font-weight:bold; color:var(--accent);">${state.res}</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-direction:column; gap:4px; font-family:var(--mono);">';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px; color:var(--text-dim);">Starts:</div>';
    for(let i=0; i<state.starts.length; i++) {
       let border = i === state.s_ptr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = i < state.s_ptr ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
       html += `<div style="width:30px; height:30px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg};">${state.starts[i]}</div>`;
    }
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px; color:var(--text-dim);">Ends:</div>';
    for(let i=0; i<state.ends.length; i++) {
       let border = i === state.e_ptr ? '2px solid #ef4444' : '1px solid var(--border)';
       let bg = i < state.e_ptr ? 'rgba(239,68,68,0.2)' : 'var(--surface)';
       html += `<div style="width:30px; height:30px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg};">${state.ends[i]}</div>`;
    }
    html += '</div></div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Interval List Intersections', short: 'Intersections',
  idea: 'Two pointers over two sorted lists. The intersection is `[max(start1, start2), min(end1, end2)]`. Add if valid. Move the pointer of the interval that ends earlier.',
  complexity: 'Time O(M + N) · Space O(M + N)',
  input: '0,2; 5,10; 13,23| 1,5; 8,12; 15,24; 25,26', hint: 'list1 | list2',
  code: [
    'def intervalIntersection(firstList, secondList):',
    '    res = []',
    '    i, j = 0, 0',
    '    ',
    '    while i < len(firstList) and j < len(secondList):',
    '        s = max(firstList[i][0], secondList[j][0])',
    '        e = min(firstList[i][1], secondList[j][1])',
    '        ',
    '        if s <= e:',
    '            res.append([s, e])',
    '            ',
    '        if firstList[i][1] < secondList[j][1]:',
    '            i += 1',
    '        else:',
    '            j += 1',
    '            ',
    '    return res'
  ],
  parse(str) {
    const parts = str.split('|');
    const firstList = parts[0].split(';').map(s => s.split(',').map(Number));
    const secondList = parts[1].split(';').map(s => s.split(',').map(Number));
    return { firstList, secondList };
  },
  run({ firstList, secondList }) {
    const { F, snap } = avRecorder();
    let res = [], i = 0, j = 0;
    const s = { firstList, secondList, res: [...res], i, j };
    
    snap(3, 'Start two pointers at 0.', s);
    
    while (i < firstList.length && j < secondList.length) {
       const [s1, e1] = firstList[i];
       const [s2, e2] = secondList[j];
       
       const start = Math.max(s1, s2);
       const end = Math.min(e1, e2);
       
       if (start <= end) {
          res.push([start, end]);
          s.res = JSON.parse(JSON.stringify(res));
          snap(10, `Intersection found between [${s1},${e1}] and [${s2},${e2}]: [${start},${end}]`, s);
       } else {
          snap(9, `No overlap between [${s1},${e1}] and [${s2},${e2}].`, s);
       }
       
       if (e1 < e2) {
          snap(13, `List1 ends earlier (${e1} < ${e2}). Move pointer i.`, s);
          i++;
          s.i = i;
       } else {
          snap(15, `List2 ends earlier or equal (${e2} <= ${e1}). Move pointer j.`, s);
          j++;
          s.j = j;
       }
    }
    
    snap(17, 'Done checking intersections.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono);">';
    const maxVal = Math.max(...state.firstList.map(x=>x[1]), ...state.secondList.map(x=>x[1]), 20);
    
    const renderRow = (title, list, ptr, color) => {
       let out = `<div style="display:flex; gap:10px; align-items:center;"><div style="width:60px;">${title}</div>`;
       out += `<div style="position:relative; width:calc(100% - 70px); height:20px; background:var(--surface); border:1px solid var(--border);">`;
       for (let k=0; k<list.length; k++) {
          const [start, end] = list[k];
          const w = ((end - start) / maxVal) * 100;
          const left = (start / maxVal) * 100;
          let bg = k === ptr ? color : 'rgba(100,100,100,0.5)';
          let brd = k === ptr ? `1px solid ${color}` : 'none';
          out += `<div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${bg}; border:${brd}; border-radius:4px;"></div>`;
       }
       out += `</div></div>`;
       return out;
    };
    
    html += renderRow('List 1', state.firstList, state.i, 'rgba(56,189,248,0.8)');
    html += renderRow('List 2', state.secondList, state.j, 'rgba(239,68,68,0.8)');
    
    html += `<div style="margin-top:10px; font-weight:bold; color:var(--accent);">Intersections: [${state.res.map(x=>`[${x}]`).join(', ')}]</div>`;
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Minimum Number of Arrows to Burst Balloons', short: 'Burst Balloons',
  idea: 'Greedy. Sort by END coordinate. If the next balloon starts after the current arrow position (`prev_end`), shoot a new arrow at its end.',
  complexity: 'Time O(N log N) · Space O(1)',
  input: '10,16; 2,8; 1,6; 7,12', hint: 'comma-separated pairs, separated by ;',
  code: [
    'def findMinArrowShots(points):',
    '    points.sort(key=lambda x: x[1])',
    '    arrows = 1',
    '    prev_end = points[0][1]',
    '    ',
    '    for i in range(1, len(points)):',
    '        start, end = points[i]',
    '        if start > prev_end:',
    '            arrows += 1',
    '            prev_end = end',
    '            ',
    '    return arrows'
  ],
  parse(str) {
    const points = str.split(';').map(s => s.split(',').map(Number));
    return { points };
  },
  run({ points }) {
    const { F, snap } = avRecorder();
    points.sort((a,b) => a[1] - b[1]);
    let arrows = 1;
    let prev_end = points[0][1];
    
    const s = { points: JSON.parse(JSON.stringify(points)), arrows, prev_end, i: null };
    snap(4, `Sort balloons by END time. Shoot first arrow at ${prev_end}.`, s);
    
    for (let i = 1; i < points.length; i++) {
       s.i = i;
       const [start, end] = points[i];
       if (start > prev_end) {
          arrows++;
          prev_end = end;
          s.arrows = arrows; s.prev_end = prev_end;
          snap(9, `Balloon ${i} [${start}, ${end}] starts AFTER arrow at ${s.prev_end}. Need new arrow at ${end}. Total = ${arrows}.`, s);
       } else {
          snap(7, `Balloon ${i} [${start}, ${end}] overlaps with arrow at ${prev_end}. Burst it with the same arrow!`, s);
       }
    }
    
    s.i = null;
    snap(12, `Finished. Min arrows required = ${arrows}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px; font-size:14px;">Arrows Used: <span style="font-weight:bold; color:var(--accent);">${state.arrows}</span> | Current Arrow Pos: <span style="font-weight:bold; color:#ef4444;">${state.prev_end}</span></div>`;
    
    const maxVal = Math.max(...state.points.map(x=>x[1]), 20);
    html += '<div style="display:flex; flex-direction:column; gap:4px; font-family:var(--mono);">';
    
    for (let j=0; j<state.points.length; j++) {
       const [start, end] = state.points[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = 'rgba(100,100,100,0.5)';
       if (state.i === j) color = 'rgba(56,189,248,0.8)';
       else if (j < (state.i || state.points.length)) color = 'rgba(52,211,153,0.5)'; // Burst
       
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:10px;"></div>
       </div>`;
    }
    
    // Draw arrow line
    if (state.prev_end !== null) {
       const arrowLeft = (state.prev_end / maxVal) * 100;
       html += `<div style="position:absolute; left:${arrowLeft}%; top:0; width:2px; height:100%; background:#ef4444; z-index:10;"></div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px; position:relative;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'Employee Free Time', short: 'Free Time',
  idea: 'Flatten all schedules and sort by start time. Keep track of the `max_end` seen so far. If a new interval starts strictly after `max_end`, the gap is a common free time!',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '1,2; 5,6| 1,3| 4,10', hint: 'schedules separated by |',
  code: [
    'def employeeFreeTime(schedule):',
    '    intervals = []',
    '    for emp in schedule:',
    '        intervals.extend(emp)',
    '    intervals.sort(key=lambda x: x[0])',
    '    ',
    '    res = []',
    '    max_end = intervals[0][1]',
    '    ',
    '    for i in range(1, len(intervals)):',
    '        start, end = intervals[i]',
    '        if start > max_end:',
    '            res.append([max_end, start])',
    '        max_end = max(max_end, end)',
    '        ',
    '    return res'
  ],
  parse(str) {
    const parts = str.split('|');
    const schedule = parts.map(p => p.split(';').map(s => s.split(',').map(Number)));
    return { schedule };
  },
  run({ schedule }) {
    const { F, snap } = avRecorder();
    let intervals = [];
    for (const emp of schedule) intervals.push(...emp);
    intervals.sort((a,b) => a[0] - b[0]);
    
    let res = [];
    let max_end = intervals[0][1];
    
    const s = { intervals, res: [...res], max_end, i: null };
    snap(7, `Flatten and sort all intervals. Initial max_end = ${max_end}.`, s);
    
    for (let i = 1; i < intervals.length; i++) {
       s.i = i;
       const [start, end] = intervals[i];
       
       if (start > max_end) {
          res.push([max_end, start]);
          s.res = JSON.parse(JSON.stringify(res));
          snap(12, `Interval ${i} [${start}, ${end}] starts AFTER max_end ${max_end}. We found a GAP! Added [${max_end}, ${start}] to free time.`, s);
       } else {
          snap(10, `Interval ${i} [${start}, ${end}] overlaps with max_end ${max_end}. No gap.`, s);
       }
       
       max_end = Math.max(max_end, end);
       s.max_end = max_end;
       snap(13, `Update max_end = max(old, ${end}) = ${max_end}.`, s);
    }
    
    s.i = null;
    snap(15, `Done. Free times: [${res.map(x=>`[${x}]`).join(', ')}]`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:10px; font-size:14px;">
        Max End Horizon: <span style="font-weight:bold; color:#ef4444;">${state.max_end}</span> | 
        Free Time: <span style="font-weight:bold; color:var(--accent);">[${state.res.map(x=>`[${x}]`).join(', ')}]</span>
    </div>`;
    
    const maxVal = Math.max(...state.intervals.map(x=>x[1]), 20);
    html += '<div style="display:flex; flex-direction:column; gap:4px; font-family:var(--mono); position:relative;">';
    
    for (let j=0; j<state.intervals.length; j++) {
       const [start, end] = state.intervals[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = state.i === j ? 'rgba(56,189,248,0.8)' : 'rgba(100,100,100,0.5)';
       
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:1px solid var(--border);">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px;"></div>
       </div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('19_intervals', {
  title: 'Car Pooling', short: 'Car Pooling',
  idea: 'Sweep-line algorithm. Create events: `(start, passengers)` and `(end, -passengers)`. Sort events (process drop-offs before pick-ups at same time). Accumulate passengers and check against capacity.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '2,1,5; 3,3,7| 4', hint: 'triplets (passengers, start, end) split by ; | capacity',
  code: [
    'def carPooling(trips, capacity):',
    '    events = []',
    '    for num, start, end in trips:',
    '        events.append((start, num))',
    '        events.append((end, -num))',
    '        ',
    '    events.sort(key=lambda x: (x[0], x[1]))',
    '    ',
    '    curr_cap = 0',
    '    for time, change in events:',
    '        curr_cap += change',
    '        if curr_cap > capacity:',
    '            return False',
    '            ',
    '    return True'
  ],
  parse(str) {
    const parts = str.split('|');
    const trips = parts[0].split(';').map(t => t.split(',').map(Number));
    const capacity = parseInt(parts[1]);
    return { trips, capacity };
  },
  run({ trips, capacity }) {
    const { F, snap } = avRecorder();
    let events = [];
    for (const [num, start, end] of trips) {
       events.push({time: start, diff: num, type: 'pickup'});
       events.push({time: end, diff: -num, type: 'dropoff'});
    }
    events.sort((a,b) => a.time === b.time ? a.diff - b.diff : a.time - b.time);
    
    let curr_cap = 0;
    const s = { events, capacity, curr_cap, i: null };
    snap(6, 'Create events for pickup (+passengers) and dropoff (-passengers). Sort by time.', s);
    
    for (let i = 0; i < events.length; i++) {
       s.i = i;
       curr_cap += events[i].diff;
       s.curr_cap = curr_cap;
       
       if (curr_cap > capacity) {
          snap(12, `Time ${events[i].time}: ${events[i].diff > 0 ? 'Pick up' : 'Drop off'} ${Math.abs(events[i].diff)}. Current load = ${curr_cap}. EXCEEDS capacity ${capacity}! Return False.`, s);
          return F;
       }
       
       snap(10, `Time ${events[i].time}: ${events[i].diff > 0 ? 'Pick up' : 'Drop off'} ${Math.abs(events[i].diff)}. Current load = ${curr_cap}.`, s);
    }
    
    s.i = null;
    snap(14, 'Successfully completed all trips within capacity. Return True.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:15px; font-size:16px;">
        <div>Max Capacity: <span style="font-weight:bold; color:var(--text);">${state.capacity}</span></div>
        <div>Current Load: <span style="font-weight:bold; color:${state.curr_cap > state.capacity ? '#ef4444' : 'var(--accent)'};">${state.curr_cap}</span></div>
    </div>`;
    
    html += '<div style="display:flex; gap:10px; overflow-x:auto;">';
    for (let i=0; i<state.events.length; i++) {
       const ev = state.events[i];
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = ev.type === 'pickup' ? 'rgba(239,68,68,0.1)' : 'rgba(52,211,153,0.1)';
       if (isCurr) bg = 'rgba(56,189,248,0.2)';
       
       html += `<div style="display:flex; flex-direction:column; align-items:center; min-width:60px; padding:5px; border:${border}; background:${bg}; border-radius:6px;">
          <div style="font-family:var(--mono); font-size:12px;">T=${ev.time}</div>
          <div style="font-weight:bold; font-size:18px; color:${ev.diff>0?'#ef4444':'#34d399'};">${ev.diff > 0 ? '+'+ev.diff : ev.diff}</div>
       </div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'My Calendar I', short: 'My Calendar I',
  idea: 'We need to book events without double booking. Keep a list of valid bookings. For a new booking `[start, end]`, check if it overlaps any existing booking. Overlap condition: `new_start < existing_end` AND `new_end > existing_start`.',
  complexity: 'Time O(N) per book · Space O(N)',
  input: '10,20; 15,25; 20,30', hint: 'comma-separated pairs, separated by ;',
  code: [
    'class MyCalendar:',
    '    def __init__(self):',
    '        self.calendar = []',
    '        ',
    '    def book(self, start, end):',
    '        for s, e in self.calendar:',
    '            if start < e and end > s:',
    '                return False',
    '        self.calendar.append((start, end))',
    '        return True'
  ],
  parse(str) {
    const books = str.split(';').map(s => s.split(',').map(Number));
    return { books };
  },
  run({ books }) {
    const { F, snap } = avRecorder();
    let calendar = [];
    const s = { books, calendar: [...calendar], curBook: null, checkIdx: null, status: null };
    
    snap(2, 'Initialize empty calendar.', s);
    
    for (const [start, end] of books) {
       s.curBook = [start, end];
       s.checkIdx = null; s.status = 'checking';
       snap(6, `Try to book [${start}, ${end}].`, s);
       
       let overlap = false;
       for (let i = 0; i < calendar.length; i++) {
          s.checkIdx = i;
          const [s2, e2] = calendar[i];
          if (start < e2 && end > s2) {
             overlap = true;
             s.status = 'failed';
             snap(7, `Overlap detected with [${s2}, ${e2}]! (${start} < ${e2} and ${end} > ${s2}). Booking failed.`, s);
             break;
          }
       }
       
       if (!overlap) {
          calendar.push([start, end]);
          s.calendar = JSON.parse(JSON.stringify(calendar));
          s.status = 'success';
          snap(9, `No overlaps found. Successfully booked [${start}, ${end}].`, s);
       }
    }
    
    s.curBook = null; s.checkIdx = null; s.status = null;
    snap(10, 'Finished processing all booking requests.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">';
    
    if (state.curBook) {
       let color = state.status === 'success' ? '#34d399' : (state.status === 'failed' ? '#ef4444' : 'var(--accent)');
       html += `<div>Processing: <span style="font-weight:bold; color:${color};">[${state.curBook[0]}, ${state.curBook[1]}] - ${state.status.toUpperCase()}</span></div>`;
    }
    
    const maxVal = Math.max(...state.calendar.map(x=>x[1]), state.curBook ? state.curBook[1] : 20, 20);
    
    html += '<div><div style="margin-bottom:5px; color:var(--text-dim);">Calendar:</div><div style="display:flex; flex-direction:column; gap:4px;">';
    for (let j=0; j<state.calendar.length; j++) {
       const [start, end] = state.calendar[j];
       const w = ((end - start) / maxVal) * 100;
       const left = (start / maxVal) * 100;
       let color = 'rgba(52,211,153,0.8)';
       let border = state.checkIdx === j ? '2px solid #ef4444' : '1px solid var(--border)';
       
       html += `<div style="position:relative; width:100%; height:20px; background:var(--surface); border:${border};">
          <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:10px; font-weight:bold; color:#000;">[${start},${end}]</div>
       </div>`;
    }
    html += '</div></div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('19_intervals', {
  title: 'My Calendar II', short: 'My Calendar II',
  idea: 'Allows double bookings, but NO triple bookings. Keep a list of `calendar` (single bookings) and `overlaps` (double bookings). For a new booking, check if it overlaps any in `overlaps` (if so, return False). Then find overlaps with `calendar` and add them to `overlaps`. Add booking to `calendar`.',
  complexity: 'Time O(N) per book · Space O(N)',
  input: '10,20; 50,60; 10,40; 5,15; 5,10; 25,55', hint: 'comma-separated pairs, separated by ;',
  code: [
    'class MyCalendarTwo:',
    '    def __init__(self):',
    '        self.calendar = []',
    '        self.overlaps = []',
    '        ',
    '    def book(self, start, end):',
    '        for s, e in self.overlaps:',
    '            if start < e and end > s:',
    '                return False',
    '                ',
    '        for s, e in self.calendar:',
    '            if start < e and end > s:',
    '                self.overlaps.append((max(start, s), min(end, e)))',
    '                ',
    '        self.calendar.append((start, end))',
    '        return True'
  ],
  parse(str) {
    const books = str.split(';').map(s => s.split(',').map(Number));
    return { books };
  },
  run({ books }) {
    const { F, snap } = avRecorder();
    let calendar = [];
    let overlaps = [];
    const s = { books, calendar: [...calendar], overlaps: [...overlaps], curBook: null, status: null };
    
    snap(3, 'Initialize calendar (single bookings) and overlaps (double bookings).', s);
    
    for (const [start, end] of books) {
       s.curBook = [start, end];
       s.status = 'checking';
       snap(6, `Try to book [${start}, ${end}]. First check against double bookings (overlaps array).`, s);
       
       let tripleOverlap = false;
       for (const [s2, e2] of overlaps) {
          if (start < e2 && end > s2) {
             tripleOverlap = true;
             s.status = 'failed';
             snap(8, `Overlap detected with double booking [${s2}, ${e2}]! TRIPLE BOOKING ATTEMPT! Failed.`, s);
             break;
          }
       }
       
       if (tripleOverlap) continue;
       
       snap(11, `No triple bookings. Now find any overlaps with existing single bookings and add them to double bookings array.`, s);
       for (const [s2, e2] of calendar) {
          if (start < e2 && end > s2) {
             const overlapStart = Math.max(start, s2);
             const overlapEnd = Math.min(end, e2);
             overlaps.push([overlapStart, overlapEnd]);
             s.overlaps = JSON.parse(JSON.stringify(overlaps));
             snap(13, `Overlaps with single booking [${s2}, ${e2}]. Created double booking [${overlapStart}, ${overlapEnd}].`, s);
          }
       }
       
       calendar.push([start, end]);
       s.calendar = JSON.parse(JSON.stringify(calendar));
       s.status = 'success';
       snap(15, `Added [${start}, ${end}] to single bookings. Booking successful.`, s);
    }
    
    s.curBook = null; s.status = null;
    snap(17, 'Finished processing all booking requests.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono);">';
    
    if (state.curBook) {
       let color = state.status === 'success' ? '#34d399' : (state.status === 'failed' ? '#ef4444' : 'var(--accent)');
       html += `<div>Processing: <span style="font-weight:bold; color:${color};">[${state.curBook[0]}, ${state.curBook[1]}] - ${state.status.toUpperCase()}</span></div>`;
    }
    
    const maxVal = Math.max(...state.calendar.map(x=>x[1]), ...state.overlaps.map(x=>x[1]), state.curBook ? state.curBook[1] : 60, 60);
    
    const renderList = (title, list, color) => {
       let out = `<div><div style="margin-bottom:5px; color:var(--text-dim);">${title} (${list.length}):</div><div style="display:flex; flex-direction:column; gap:4px;">`;
       if (list.length === 0) out += `<div style="font-size:12px; color:var(--text-dim);">Empty</div>`;
       for (let j=0; j<list.length; j++) {
          const [start, end] = list[j];
          const w = ((end - start) / maxVal) * 100;
          const left = (start / maxVal) * 100;
          out += `<div style="position:relative; width:100%; height:16px; background:var(--surface); border:1px solid var(--border);">
             <div style="position:absolute; left:${left}%; width:${w}%; height:100%; background:${color}; border-radius:4px; display:flex; align-items:center; justify-content:center; font-size:9px; font-weight:bold; color:#000;">[${start},${end}]</div>
          </div>`;
       }
       out += '</div></div>';
       return out;
    };
    
    html += renderList('Single Bookings (Calendar)', state.calendar, 'rgba(52,211,153,0.8)');
    html += renderList('Double Bookings (Overlaps)', state.overlaps, 'rgba(239,68,68,0.8)');
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('20_bit_manipulation', {
  title: 'Single Number', short: 'Single Number',
  idea: 'XOR all numbers. Since `x ^ x = 0` and `x ^ 0 = x`, all pairs cancel out, leaving only the single number.',
  complexity: 'Time O(N) · Space O(1)',
  input: '4, 1, 2, 1, 2', hint: 'comma-separated numbers',
  code: [
    'def singleNumber(nums):',
    '    res = 0',
    '    for n in nums:',
    '        res ^= n',
    '    return res'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let res = 0;
    const s = { nums, res, i: null };
    
    snap(2, 'Initialize res = 0', s);
    
    for (let i = 0; i < nums.length; i++) {
       s.i = i;
       const oldRes = res;
       res ^= nums[i];
       s.res = res;
       snap(4, `XOR with ${nums[i]}: ${oldRes} ^ ${nums[i]} = ${res}. In binary: ${oldRes.toString(2).padStart(4,'0')} ^ ${nums[i].toString(2).padStart(4,'0')} = ${res.toString(2).padStart(4,'0')}`, s);
    }
    
    s.i = null;
    snap(5, `Finished. Pairs cancelled out. The single number is ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:20px;">
        <div style="font-size:18px;">Current XOR Sum: <span style="font-weight:bold; color:var(--accent);">${state.res}</span> <span style="color:var(--text-dim); font-size:14px;">(${state.res.toString(2).padStart(8,'0')})</span></div>
    </div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:8px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isCurr ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center; padding:5px 10px; border:${border}; background:${bg}; border-radius:6px;">
          <div style="font-weight:bold; font-size:16px;">${state.nums[i]}</div>
          <div style="font-size:10px; color:var(--text-dim); font-family:var(--mono);">${state.nums[i].toString(2).padStart(4,'0')}</div>
       </div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Number of 1 Bits', short: 'Count 1s',
  idea: 'Use `n &= (n - 1)` to clear the lowest set bit in each iteration. Count how many times we do this until `n == 0`.',
  complexity: 'Time O(1) (max 32 ops) · Space O(1)',
  input: '11', hint: 'integer (e.g. 11 for binary 1011)',
  code: [
    'def hammingWeight(n):',
    '    res = 0',
    '    while n:',
    '        n &= (n - 1)',
    '        res += 1',
    '    return res'
  ],
  parse(str) {
    return { n: parseInt(str.trim()) };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    let res = 0;
    let curr = n;
    const s = { n, curr, res };
    
    snap(2, `Initialize count = 0. Current number = ${curr} (binary: ${curr.toString(2).padStart(8,'0')}).`, s);
    
    while (curr > 0) {
       const prev = curr;
       curr &= (curr - 1);
       res += 1;
       s.curr = curr; s.res = res;
       snap(5, `n = n & (n - 1) clears the lowest 1 bit. ${prev.toString(2).padStart(8,'0')} & ${(prev-1).toString(2).padStart(8,'0')} = ${curr.toString(2).padStart(8,'0')}. Count = ${res}.`, s);
    }
    
    snap(6, `Finished. Number of 1 bits = ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:20px; font-family:var(--mono); margin-bottom:20px; font-size:18px;">
        <div>Original: ${state.n}</div>
        <div>Count: <span style="font-weight:bold; color:var(--accent);">${state.res}</span></div>
    </div>`;
    
    html += `<div style="font-family:var(--mono); font-size:24px; letter-spacing:4px;">`;
    const bin = state.curr.toString(2).padStart(8,'0');
    for (let char of bin) {
       let color = char === '1' ? '#34d399' : 'var(--text-dim)';
       html += `<span style="color:${color}; font-weight:bold;">${char}</span>`;
    }
    html += `</div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Counting Bits', short: 'Counting Bits',
  idea: 'DP using bits: `dp[i] = dp[i >> 1] + (i & 1)`. The number of 1s in `i` is the number of 1s in `i / 2` plus 1 if `i` is odd.',
  complexity: 'Time O(N) · Space O(N)',
  input: '5', hint: 'integer n',
  code: [
    'def countBits(n):',
    '    dp = [0] * (n + 1)',
    '    for i in range(1, n + 1):',
    '        dp[i] = dp[i >> 1] + (i & 1)',
    '    return dp'
  ],
  parse(str) {
    return { n: parseInt(str.trim()) };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    let dp = new Array(n + 1).fill(0);
    const s = { n, dp: [...dp], i: null };
    
    snap(2, 'Initialize dp array with 0s.', s);
    
    for (let i = 1; i <= n; i++) {
       s.i = i;
       const half = i >> 1;
       const odd = i & 1;
       dp[i] = dp[half] + odd;
       s.dp = [...dp];
       snap(4, `i = ${i} (binary ${i.toString(2)}). dp[${i}] = dp[${half}] + ${odd} = ${dp[i]}.`, s);
    }
    
    s.i = null;
    snap(5, `Finished. Result = [${dp.join(', ')}]`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-wrap:wrap; gap:8px; font-family:var(--mono);">';
    for (let i=0; i<=state.n; i++) {
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isCurr ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center; padding:5px 10px; border:${border}; background:${bg}; border-radius:6px; min-width:50px;">
          <div style="font-size:10px; color:var(--text-dim); margin-bottom:2px;">i = ${i}</div>
          <div style="font-weight:bold; font-size:16px; color:var(--accent);">${state.dp[i]}</div>
          <div style="font-size:10px; color:var(--text-dim); margin-top:2px;">${i.toString(2).padStart(4,'0')}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Reverse Bits', short: 'Reverse Bits',
  idea: 'Iterate 32 times. Extract the lowest bit of `n` using `n & 1`. Shift `res` left and add the bit `res = (res << 1) | bit`. Shift `n` right by 1.',
  complexity: 'Time O(1) · Space O(1)',
  input: '43261596', hint: '32-bit unsigned integer',
  code: [
    'def reverseBits(n):',
    '    res = 0',
    '    for i in range(32):',
    '        bit = (n >> i) & 1',
    '        res = res | (bit << (31 - i))',
    '    return res'
  ],
  parse(str) {
    return { n: parseInt(str.trim()) };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    let res = 0;
    const s = { n, res, i: null };
    
    snap(2, `Initialize res = 0. Original = ${n.toString(2).padStart(32,'0')}`, s);
    
    for (let i = 0; i < 32; i++) {
       s.i = i;
       const bit = (n >> i) & 1;
       res = (res | (bit << (31 - i))) >>> 0; // unsigned 32-bit cast
       s.res = res;
       
       if (i % 8 === 0 || i === 31) {
          snap(5, `Step ${i}: extracted bit ${bit}. res = ${res.toString(2).padStart(32,'0')}`, s);
       }
    }
    
    s.i = null;
    snap(6, `Finished. Reversed = ${res}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); display:flex; flex-direction:column; gap:10px;">`;
    
    html += `<div><div style="color:var(--text-dim); font-size:12px;">Original (n = ${state.n}):</div>`;
    html += `<div style="font-size:18px; letter-spacing:2px;">${state.n.toString(2).padStart(32,'0')}</div></div>`;
    
    html += `<div><div style="color:var(--text-dim); font-size:12px;">Reversed (res = ${state.res}):</div>`;
    html += `<div style="font-size:18px; letter-spacing:2px; color:var(--accent);">${state.res.toString(2).padStart(32,'0')}</div></div>`;
    
    if (state.i !== null) {
       html += `<div style="margin-top:10px; color:#34d399; font-weight:bold;">Iteration: ${state.i}/32</div>`;
    }
    html += `</div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('20_bit_manipulation', {
  title: 'Missing Number', short: 'Missing Number',
  idea: 'XOR all numbers from 0 to N and all elements in the array. All present numbers will cancel out, leaving the missing number.',
  complexity: 'Time O(N) · Space O(1)',
  input: '3, 0, 1', hint: 'comma-separated numbers',
  code: [
    'def missingNumber(nums):',
    '    res = len(nums)',
    '    for i, num in enumerate(nums):',
    '        res ^= i ^ num',
    '    return res'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let res = nums.length;
    const s = { nums, res, i: null };
    
    snap(2, `Initialize res = N = ${res}.`, s);
    
    for (let i = 0; i < nums.length; i++) {
       s.i = i;
       const oldRes = res;
       res ^= i;
       res ^= nums[i];
       s.res = res;
       snap(4, `XOR with index ${i} and num ${nums[i]}: ${oldRes} ^ ${i} ^ ${nums[i]} = ${res}.`, s);
    }
    
    s.i = null;
    snap(5, `Finished. The missing number is ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="font-family:var(--mono); margin-bottom:20px; font-size:18px;">
        Current XOR Sum: <span style="font-weight:bold; color:var(--accent);">${state.res}</span>
    </div>`;
    
    html += '<div style="display:flex; flex-wrap:wrap; gap:8px;">';
    for (let i=0; i<state.nums.length; i++) {
       let isCurr = state.i === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isCurr ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center; padding:5px 10px; border:${border}; background:${bg}; border-radius:6px;">
          <div style="font-size:10px; color:var(--text-dim);">idx=${i}</div>
          <div style="font-weight:bold; font-size:16px;">${state.nums[i]}</div>
       </div>`;
    }
    html += '</div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Sum of Two Integers', short: 'Sum (No +)',
  idea: 'Use `a ^ b` for addition without carry. Use `(a & b) << 1` for the carry. Repeat until carry is 0.',
  complexity: 'Time O(1) · Space O(1)',
  input: '1, 2', hint: 'a, b',
  code: [
    'def getSum(a, b):',
    '    mask = 0xFFFFFFFF',
    '    while b != 0:',
    '        carry = (a & b) & mask',
    '        a = (a ^ b) & mask',
    '        b = (carry << 1) & mask',
    '    return a if a <= 0x7FFFFFFF else ~(a ^ mask)'
  ],
  parse(str) {
    const parts = str.split(',');
    return { a: parseInt(parts[0]), b: parseInt(parts[1]) };
  },
  run({ a, b }) {
    const { F, snap } = avRecorder();
    let currentA = a, currentB = b;
    const s = { a, b, currentA, currentB };
    
    snap(2, `Initialize a=${a}, b=${b}.`, s);
    
    let iterations = 0;
    while (currentB !== 0 && iterations < 32) {
       let carry = currentA & currentB;
       currentA = currentA ^ currentB;
       currentB = carry << 1;
       
       // simulate 32-bit integer overflow for JS
       currentA = currentA | 0;
       currentB = currentB | 0;
       
       s.currentA = currentA; s.currentB = currentB;
       snap(5, `carry = (a & b) << 1 = ${currentB}. a = a ^ b = ${currentA}.`, s);
       iterations++;
    }
    
    snap(6, `Finished. Sum = ${currentA}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    const toBin = (num) => (num >>> 0).toString(2).padStart(8,'0');
    let html = `<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono); font-size:18px;">
        <div>A: <span style="font-weight:bold; color:var(--accent);">${state.currentA}</span> <span style="color:var(--text-dim); font-size:12px;">(${toBin(state.currentA)})</span></div>
        <div>B (Carry): <span style="font-weight:bold; color:#ef4444;">${state.currentB}</span> <span style="color:var(--text-dim); font-size:12px;">(${toBin(state.currentB)})</span></div>
    </div>`;
    
    if (state.currentB === 0) {
       html += `<div style="margin-top:20px; font-weight:bold; color:#34d399;">Result: ${state.currentA}</div>`;
    }
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Reverse Integer', short: 'Reverse Int',
  idea: 'Pop the last digit using `% 10` and push it to `res = res * 10 + digit`. Handle 32-bit integer overflow.',
  complexity: 'Time O(log(x)) · Space O(1)',
  input: '123', hint: 'integer',
  code: [
    'def reverse(x):',
    '    res = 0',
    '    sign = -1 if x < 0 else 1',
    '    x = abs(x)',
    '    ',
    '    while x:',
    '        digit = x % 10',
    '        x //= 10',
    '        if res > (2**31 - 1 - digit) // 10:',
    '            return 0',
    '        res = res * 10 + digit',
    '        ',
    '    return sign * res'
  ],
  parse(str) {
    return { x: parseInt(str.trim()) };
  },
  run({ x }) {
    const { F, snap } = avRecorder();
    let res = 0;
    let sign = x < 0 ? -1 : 1;
    let curr = Math.abs(x);
    
    const s = { x, curr, res, sign, digit: null };
    snap(4, `Initialize res = 0, sign = ${sign}.`, s);
    
    while (curr > 0) {
       let digit = curr % 10;
       curr = Math.floor(curr / 10);
       
       if (res > Math.floor((2**31 - 1 - digit) / 10)) {
          snap(10, 'Integer overflow detected! Return 0.', s);
          return F;
       }
       
       res = res * 10 + digit;
       s.curr = curr; s.res = res; s.digit = digit;
       snap(11, `Pop digit ${digit}. res = res * 10 + digit = ${res}. x = ${curr}.`, s);
    }
    
    res *= sign;
    s.res = res; s.digit = null;
    snap(13, `Finished. Result = ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; gap:30px; font-family:var(--mono); font-size:18px;">
        <div style="display:flex; flex-direction:column; align-items:center;">
           <div style="color:var(--text-dim); font-size:12px;">Remaining X</div>
           <div style="font-weight:bold;">${state.curr}</div>
        </div>
        
        <div style="display:flex; flex-direction:column; align-items:center;">
           <div style="color:var(--text-dim); font-size:12px;">Popped Digit</div>
           <div style="font-weight:bold; color:#ef4444;">${state.digit !== null ? state.digit : '-'}</div>
        </div>
        
        <div style="display:flex; flex-direction:column; align-items:center;">
           <div style="color:var(--text-dim); font-size:12px;">Reversed (res)</div>
           <div style="font-weight:bold; color:var(--accent);">${state.res}</div>
        </div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('20_bit_manipulation', {
  title: 'Single Number II', short: 'Single Number II',
  idea: 'Use digital logic design. `ones` tracks bits appearing once, `twos` tracks bits appearing twice. Formula: `ones = (ones ^ n) & ~twos`, `twos = (twos ^ n) & ~ones`.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2, 2, 3, 2', hint: 'comma-separated numbers',
  code: [
    'def singleNumber(nums):',
    '    ones, twos = 0, 0',
    '    for n in nums:',
    '        ones = (ones ^ n) & ~twos',
    '        twos = (twos ^ n) & ~ones',
    '    return ones'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let ones = 0, twos = 0;
    const s = { nums, ones, twos, curr: null };
    
    snap(2, 'Initialize ones=0, twos=0.', s);
    
    for (const n of nums) {
       s.curr = n;
       ones = (ones ^ n) & ~twos;
       twos = (twos ^ n) & ~ones;
       
       // Force 32-bit unsigned for JS display (optional, keeps it clean)
       ones = ones >>> 0;
       twos = twos >>> 0;
       
       s.ones = ones; s.twos = twos;
       snap(5, `Process ${n}. ones = ${ones.toString(2).padStart(4,'0')}, twos = ${twos.toString(2).padStart(4,'0')}.`, s);
    }
    
    s.curr = null;
    snap(6, `Finished. The single number is in 'ones': ${ones}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    const toBin = (num) => (num >>> 0).toString(2).padStart(4,'0');
    let html = `<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono); font-size:16px;">
        <div style="font-weight:bold; color:var(--text-dim);">Processing: ${state.curr !== null ? state.curr : 'None'}</div>
        <div>Ones: <span style="font-weight:bold; color:var(--accent);">${state.ones}</span> <span style="color:var(--text-dim); font-size:12px;">(${toBin(state.ones)})</span></div>
        <div>Twos: <span style="font-weight:bold; color:#ef4444;">${state.twos}</span> <span style="color:var(--text-dim); font-size:12px;">(${toBin(state.twos)})</span></div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Single Number III', short: 'Single Number III',
  idea: 'XOR all elements to get `a ^ b`. Find any set bit (`diff &= -diff`). Use this bit to partition numbers into two groups and XOR each group separately to isolate `a` and `b`.',
  complexity: 'Time O(N) · Space O(1)',
  input: '1, 2, 1, 3, 2, 5', hint: 'comma-separated numbers',
  code: [
    'def singleNumber(nums):',
    '    xor = 0',
    '    for n in nums:',
    '        xor ^= n',
    '        ',
    '    diff = xor & -xor',
    '    ',
    '    a, b = 0, 0',
    '    for n in nums:',
    '        if n & diff:',
    '            a ^= n',
    '        else:',
    '            b ^= n',
    '            ',
    '    return [a, b]'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let xor = 0;
    for (const n of nums) xor ^= n;
    
    let diff = xor & -xor;
    let a = 0, b = 0;
    const s = { nums, xor, diff, a, b, phase: 1, curr: null };
    
    snap(6, `Phase 1: XOR all elements. Result = ${xor} (binary ${xor.toString(2).padStart(4,'0')}). This is a ^ b. Find rightmost set bit: diff = ${diff} (binary ${diff.toString(2).padStart(4,'0')}).`, s);
    
    s.phase = 2;
    for (const n of nums) {
       s.curr = n;
       if (n & diff) {
          a ^= n;
          s.a = a;
          snap(11, `n = ${n} (binary ${n.toString(2).padStart(4,'0')}) has the diff bit set. XOR into 'a'. a = ${a}.`, s);
       } else {
          b ^= n;
          s.b = b;
          snap(13, `n = ${n} (binary ${n.toString(2).padStart(4,'0')}) does NOT have the diff bit set. XOR into 'b'. b = ${b}.`, s);
       }
    }
    
    s.curr = null; s.phase = 3;
    snap(15, `Finished. The two single numbers are [${a}, ${b}].`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    const toBin = (num) => (num >>> 0).toString(2).padStart(4,'0');
    let html = `<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono); font-size:16px;">
        <div style="font-weight:bold; color:var(--text-dim);">a ^ b: ${state.xor} (${toBin(state.xor)}) | Diff Bit: ${state.diff} (${toBin(state.diff)})</div>
    </div>`;
    
    html += `<div style="display:flex; gap:20px; margin-top:20px;">
        <div style="display:flex; flex-direction:column; gap:5px;">
           <div style="font-weight:bold; color:var(--accent);">Group A (bit set)</div>
           <div style="font-size:24px; font-weight:bold;">${state.a}</div>
        </div>
        <div style="display:flex; flex-direction:column; gap:5px;">
           <div style="font-weight:bold; color:#ef4444;">Group B (bit NOT set)</div>
           <div style="font-size:24px; font-weight:bold;">${state.b}</div>
        </div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('20_bit_manipulation', {
  title: 'Bitwise AND of Numbers Range', short: 'AND Range',
  idea: 'The bitwise AND of a range reduces to finding the common prefix of `left` and `right`. Shift both right until they equal, keeping a count. Then shift the common prefix left by the count.',
  complexity: 'Time O(1) · Space O(1)',
  input: '5, 7', hint: 'left, right',
  code: [
    'def rangeBitwiseAnd(left, right):',
    '    shifts = 0',
    '    while left != right:',
    '        left >>= 1',
    '        right >>= 1',
    '        shifts += 1',
    '    return left << shifts'
  ],
  parse(str) {
    const parts = str.split(',');
    return { left: parseInt(parts[0]), right: parseInt(parts[1]) };
  },
  run({ left, right }) {
    const { F, snap } = avRecorder();
    let shifts = 0;
    let l = left, r = right;
    const s = { left, right, l, r, shifts };
    
    snap(2, `Initialize. We need the common prefix of left and right.`, s);
    
    while (l !== r) {
       l >>= 1;
       r >>= 1;
       shifts++;
       s.l = l; s.r = r; s.shifts = shifts;
       snap(6, `Shift right. l = ${l}, r = ${r}. Shifts = ${shifts}.`, s);
    }
    
    const res = l << shifts;
    snap(7, `They are equal! Common prefix is ${l}. Shift left by ${shifts} to restore 0s. Result = ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    const toBin = (num) => (num >>> 0).toString(2).padStart(8,'0');
    let html = `<div style="display:flex; flex-direction:column; gap:10px; font-family:var(--mono); font-size:16px;">
        <div>Shifts: <span style="font-weight:bold; color:var(--accent);">${state.shifts}</span></div>
        <div>Current Left:  <span style="font-weight:bold; letter-spacing:2px;">${toBin(state.l)}</span></div>
        <div>Current Right: <span style="font-weight:bold; letter-spacing:2px;">${toBin(state.r)}</span></div>
    </div>`;
    
    if (state.l === state.r) {
       html += `<div style="margin-top:20px; color:#34d399; font-weight:bold; font-size:18px;">Final Result: ${state.l << state.shifts}</div>`;
    }
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('21_math_geometry', {
  title: 'Palindrome Number', short: 'Palindrome',
  idea: 'Revert half of the number to avoid string conversion and overflow issues. Compare the first half with the reverted second half.',
  complexity: 'Time O(log10(N)) · Space O(1)',
  input: '1221', hint: 'integer (e.g. 1221)',
  code: [
    'def isPalindrome(x):',
    '    if x < 0 or (x % 10 == 0 and x != 0):',
    '        return False',
    '    revertedNumber = 0',
    '    while x > revertedNumber:',
    '        revertedNumber = revertedNumber * 10 + x % 10',
    '        x //= 10',
    '    return x == revertedNumber or x == revertedNumber // 10'
  ],
  parse(str) {
    return { x: parseInt(str.trim()) };
  },
  run({ x }) {
    const { F, snap } = avRecorder();
    const original = x;
    let s = { x, revertedNumber: 0, original };
    
    if (x < 0 || (x % 10 === 0 && x !== 0)) {
        snap(2, 'Negative numbers or numbers ending in 0 (except 0 itself) are not palindromes.', s);
        snap(3, 'Return false.', s);
        return F;
    }
    
    snap(4, 'Initialize revertedNumber = 0.', s);
    
    while (x > s.revertedNumber) {
        s.revertedNumber = s.revertedNumber * 10 + x % 10;
        x = Math.floor(x / 10);
        s.x = x;
        snap(6, `Pop last digit and append to revertedNumber. x = ${x}, revertedNumber = ${s.revertedNumber}.`, s);
    }
    
    snap(8, `Loop ends. If original number had odd length, we can discard the middle digit by revertedNumber // 10.`, s);
    let result = (x === s.revertedNumber) || (x === Math.floor(s.revertedNumber / 10));
    snap(8, `Return x == revertedNumber or x == revertedNumber // 10. Result: ${result}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:18px;">Original: <span style="font-weight:bold;">${state.original}</span></div>
        <div style="display:flex; gap:30px;">
            <div style="display:flex; flex-direction:column; align-items:center; padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface);">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">x (First Half)</div>
                <div style="font-size:24px; font-weight:bold; color:var(--accent);">${state.x}</div>
            </div>
            <div style="display:flex; flex-direction:column; align-items:center; padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface);">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">revertedNumber (Second Half)</div>
                <div style="font-size:24px; font-weight:bold; color:#34d399;">${state.revertedNumber}</div>
            </div>
        </div>
    </div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Plus One', short: 'Plus One',
  idea: 'Start from the last digit. If it is 9, it becomes 0 and we carry over 1. Otherwise, just add 1 and we are done. If all digits are 9, we prepend a 1.',
  complexity: 'Time O(N) · Space O(1) in-place',
  input: '1,2,9', hint: 'comma-separated digits',
  code: [
    'def plusOne(digits):',
    '    for i in range(len(digits) - 1, -1, -1):',
    '        if digits[i] == 9:',
    '            digits[i] = 0',
    '        else:',
    '            digits[i] += 1',
    '            return digits',
    '    return [1] + digits'
  ],
  parse(str) {
    return { digits: str.split(',').map(n => parseInt(n.trim())) };
  },
  run({ digits }) {
    const { F, snap } = avRecorder();
    let s = { digits: [...digits], curr: null };
    
    snap(2, 'Start traversing digits from right to left.', s);
    
    for (let i = digits.length - 1; i >= 0; i--) {
        s.curr = i;
        snap(3, `Check digit at index ${i}: ${s.digits[i]}.`, s);
        
        if (s.digits[i] === 9) {
            s.digits[i] = 0;
            snap(4, `Digit is 9, change to 0 and carry 1 to the next left digit.`, s);
        } else {
            s.digits[i] += 1;
            snap(6, `Digit is not 9, add 1. No more carry, we are done.`, s);
            s.curr = null;
            return F;
        }
    }
    
    s.curr = null;
    s.digits = [1, ...s.digits];
    snap(8, 'All digits were 9. Prepend 1 to the result.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-wrap:wrap; gap:8px;">';
    for (let i=0; i<state.digits.length; i++) {
       let isCurr = state.curr === i;
       let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
       let bg = isCurr ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
       html += `<div style="display:flex; flex-direction:column; align-items:center; padding:10px 15px; border:${border}; background:${bg}; border-radius:6px; font-family:var(--mono);">
          <div style="font-weight:bold; font-size:24px;">${state.digits[i]}</div>
       </div>`;
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Happy Number', short: 'Happy Number',
  idea: 'Replace the number by the sum of the squares of its digits. Use Floyd cycle detection (slow and fast pointers) to find if it loops to 1.',
  complexity: 'Time O(log N) · Space O(1)',
  input: '19', hint: 'integer (e.g. 19)',
  code: [
    'def get_next(n):',
    '    total_sum = 0',
    '    while n > 0:',
    '        n, digit = divmod(n, 10)',
    '        total_sum += digit ** 2',
    '    return total_sum',
    '',
    'def isHappy(n):',
    '    slow_runner = n',
    '    fast_runner = get_next(n)',
    '    while fast_runner != 1 and slow_runner != fast_runner:',
    '        slow_runner = get_next(slow_runner)',
    '        fast_runner = get_next(get_next(fast_runner))',
    '    return fast_runner == 1'
  ],
  parse(str) {
    return { n: parseInt(str.trim()) };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    
    function getNext(num) {
        let sum = 0;
        let temp = num;
        while (temp > 0) {
            let digit = temp % 10;
            sum += digit * digit;
            temp = Math.floor(temp / 10);
        }
        return sum;
    }
    
    let slow = n;
    let fast = getNext(n);
    let s = { slow, fast, n, history: [{slow, fast}] };
    
    snap(8, `Initialize slow = ${n}, fast = get_next(${n}) = ${fast}.`, s);
    
    while (fast !== 1 && slow !== fast) {
        slow = getNext(slow);
        fast = getNext(getNext(fast));
        s.slow = slow;
        s.fast = fast;
        s.history.push({slow, fast});
        snap(11, `Update slow = get_next(slow) = ${slow}, fast = get_next(get_next(fast)) = ${fast}.`, s);
    }
    
    let isHappy = (fast === 1);
    snap(14, `Loop terminates. fast == 1? ${isHappy}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:18px;">Original: ${state.n}</div>
        <div style="display:flex; gap:20px;">
            <div style="padding:10px 20px; border:2px solid #fbbf24; border-radius:8px; background:rgba(251,191,36,0.1);">
                <div style="color:var(--text-dim); font-size:12px;">Slow Pointer</div>
                <div style="font-size:24px; font-weight:bold; color:#fbbf24;">${state.slow}</div>
            </div>
            <div style="padding:10px 20px; border:2px solid #ef4444; border-radius:8px; background:rgba(239,68,68,0.1);">
                <div style="color:var(--text-dim); font-size:12px;">Fast Pointer</div>
                <div style="font-size:24px; font-weight:bold; color:#ef4444;">${state.fast}</div>
            </div>
        </div>
        <div style="font-size:14px; color:var(--text-dim); margin-top:10px;">
            History: <br/>
            ${state.history.map((h, idx) => `<span style="margin-right:10px;">[${idx}] S:${h.slow} F:${h.fast}</span>`).join('')}
        </div>
    </div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Pow(x, n)', short: 'Pow(x, n)',
  idea: 'Binary Exponentiation. Calculate x^n efficiently by squaring x and halving n. If n is odd, multiply result by current x.',
  complexity: 'Time O(log N) · Space O(1)',
  input: '2.0, 10', hint: 'x, n (e.g. 2.0, 10)',
  code: [
    'def myPow(x, n):',
    '    if n < 0:',
    '        x = 1 / x',
    '        n = -n',
    '    res = 1',
    '    while n > 0:',
    '        if n % 2 == 1:',
    '            res *= x',
    '        x *= x',
    '        n //= 2',
    '    return res'
  ],
  parse(str) {
    const parts = str.split(',');
    return { x: parseFloat(parts[0].trim()), n: parseInt(parts[1].trim()) };
  },
  run({ x, n }) {
    const { F, snap } = avRecorder();
    let currentX = x;
    let currentN = n;
    
    let s = { currentX, currentN, res: 1, isOdd: false };
    
    if (currentN < 0) {
        currentX = 1 / currentX;
        currentN = -currentN;
        s.currentX = currentX;
        s.currentN = currentN;
        snap(2, 'n is negative, invert x and negate n.', s);
    }
    
    snap(5, 'Initialize res = 1.', s);
    
    while (currentN > 0) {
        s.isOdd = currentN % 2 === 1;
        if (s.isOdd) {
            s.res *= currentX;
            snap(7, `n is odd. res *= x. res = ${s.res}.`, s);
        } else {
            snap(7, `n is even. Skip res update.`, s);
        }
        
        currentX *= currentX;
        currentN = Math.floor(currentN / 2);
        s.currentX = currentX;
        s.currentN = currentN;
        snap(9, `x *= x (x becomes ${currentX}), n //= 2 (n becomes ${currentN}).`, s);
    }
    
    s.isOdd = false;
    snap(10, `n is 0. Return res = ${s.res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="display:flex; gap:20px;">
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Result (res)</div>
                <div style="font-size:24px; font-weight:bold; color:var(--accent);">${Number.isInteger(state.res) ? state.res : state.res.toFixed(5)}</div>
            </div>
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Current x</div>
                <div style="font-size:24px; font-weight:bold; color:#34d399;">${Number.isInteger(state.currentX) ? state.currentX : state.currentX.toFixed(5)}</div>
            </div>
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Current n</div>
                <div style="font-size:24px; font-weight:bold; color:#f87171;">${state.currentN}</div>
                <div style="font-size:12px; color:var(--text-dim); margin-top:5px;">${state.currentN.toString(2)} (binary)</div>
            </div>
        </div>
        ${state.isOdd ? '<div style="color:#f87171; font-weight:bold;">Current n is odd! Multiply Result by Current x.</div>' : '<div style="color:var(--text-dim); font-weight:bold;">Current n is even. Square Current x.</div>'}
    </div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('21_math_geometry', {
  title: 'Multiply Strings', short: 'Multiply',
  idea: 'Simulate grade-school multiplication. Array of size len(num1) + len(num2) stores intermediate results. Update indices i+j and i+j+1.',
  complexity: 'Time O(N*M) · Space O(N+M)',
  input: '12, 34', hint: 'num1, num2 (e.g. 12, 34)',
  code: [
    'def multiply(num1, num2):',
    '    if "0" in [num1, num2]:',
    '        return "0"',
    '    res = [0] * (len(num1) + len(num2))',
    '    num1, num2 = num1[::-1], num2[::-1]',
    '    for i1 in range(len(num1)):',
    '        for i2 in range(len(num2)):',
    '            digit = int(num1[i1]) * int(num2[i2])',
    '            res[i1 + i2] += digit',
    '            res[i1 + i2 + 1] += res[i1 + i2] // 10',
    '            res[i1 + i2] = res[i1 + i2] % 10',
    '    res, beg = res[::-1], 0',
    '    while beg < len(res) and res[beg] == 0:',
    '        beg += 1',
    '    return "".join(map(str, res[beg:]))'
  ],
  parse(str) {
    const parts = str.split(',').map(s => s.trim());
    return { num1: parts[0], num2: parts[1] };
  },
  run({ num1, num2 }) {
    const { F, snap } = avRecorder();
    
    if (num1 === '0' || num2 === '0') {
        snap(2, 'One of the numbers is zero. Result is "0".', { num1, num2, res: [0], i1: null, i2: null });
        return F;
    }
    
    let res = new Array(num1.length + num2.length).fill(0);
    const revNum1 = num1.split('').reverse().join('');
    const revNum2 = num2.split('').reverse().join('');
    
    let s = { num1: revNum1, num2: revNum2, res: [...res], i1: null, i2: null, digit: null };
    
    snap(4, 'Initialize result array of zeros.', s);
    
    for (let i1 = 0; i1 < revNum1.length; i1++) {
        for (let i2 = 0; i2 < revNum2.length; i2++) {
            s.i1 = i1;
            s.i2 = i2;
            
            const n1 = parseInt(revNum1[i1]);
            const n2 = parseInt(revNum2[i2]);
            const digit = n1 * n2;
            s.digit = digit;
            
            res[i1 + i2] += digit;
            res[i1 + i2 + 1] += Math.floor(res[i1 + i2] / 10);
            res[i1 + i2] = res[i1 + i2] % 10;
            
            s.res = [...res];
            snap(9, `Multiply ${n1} and ${n2} = ${digit}. Add to res[${i1+i2}] and handle carry to res[${i1+i2+1}].`, s);
        }
    }
    
    s.i1 = null; s.i2 = null; s.digit = null;
    let finalRes = [...res].reverse();
    let beg = 0;
    while (beg < finalRes.length && finalRes[beg] === 0) beg++;
    finalRes = finalRes.slice(beg);
    
    s.res = finalRes;
    snap(12, `Reverse result array and remove leading zeros. Final result: ${finalRes.join('')}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="display:flex; gap:20px;">
            <div style="font-size:18px;">Reversed num1: <span style="font-weight:bold; letter-spacing:2px;">${state.num1}</span></div>
            <div style="font-size:18px;">Reversed num2: <span style="font-weight:bold; letter-spacing:2px;">${state.num2}</span></div>
        </div>`;
        
    if (state.i1 !== null && state.i2 !== null) {
        html += `<div style="padding:10px; border:1px solid var(--accent); border-radius:6px; background:rgba(56,189,248,0.1);">
            Multiplying num1[${state.i1}] (${state.num1[state.i1]}) and num2[${state.i2}] (${state.num2[state.i2]}) = ${state.digit}
        </div>`;
    }
    
    html += `<div style="margin-top:10px; font-size:14px; color:var(--text-dim);">Result Array (from least significant to most):</div>
        <div style="display:flex; flex-wrap:wrap; gap:8px;">`;
    
    for (let i = 0; i < state.res.length; i++) {
        let isUpdated = (state.i1 !== null && state.i2 !== null && (i === state.i1 + state.i2 || i === state.i1 + state.i2 + 1));
        let border = isUpdated ? '2px solid var(--accent)' : '1px solid var(--border)';
        let bg = isUpdated ? 'rgba(56,189,248,0.2)' : 'var(--surface)';
        
        html += `<div style="display:flex; flex-direction:column; align-items:center; padding:10px 15px; border:${border}; background:${bg}; border-radius:6px;">
            <div style="color:var(--text-dim); font-size:12px; margin-bottom:5px;">idx ${i}</div>
            <div style="font-size:24px; font-weight:bold; ${isUpdated ? 'color:var(--accent);' : ''}">${state.res[i]}</div>
        </div>`;
    }
    
    html += `</div></div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Integer to Roman', short: 'Int to Roman',
  idea: 'Greedy approach. Iterate through a predefined list of values and their Roman symbols from largest to smallest. Subtract value and append symbol while n >= value.',
  complexity: 'Time O(1) (max 15 ops) · Space O(1)',
  input: '3749', hint: 'integer between 1 and 3999',
  code: [
    'def intToRoman(num):',
    '    symList = [["I", 1], ["IV", 4], ["V", 5], ["IX", 9],',
    '               ["X", 10], ["XL", 40], ["L", 50], ["XC", 90],',
    '               ["C", 100], ["CD", 400], ["D", 500], ["CM", 900],',
    '               ["M", 1000]]',
    '    res = ""',
    '    for sym, val in reversed(symList):',
    '        if num // val:',
    '            count = num // val',
    '            res += (sym * count)',
    '            num = num % val',
    '    return res'
  ],
  parse(str) {
    return { num: parseInt(str.trim()) };
  },
  run({ num }) {
    const { F, snap } = avRecorder();
    const symList = [
      ["M", 1000], ["CM", 900], ["D", 500], ["CD", 400],
      ["C", 100], ["XC", 90], ["L", 50], ["XL", 40],
      ["X", 10], ["IX", 9], ["V", 5], ["IV", 4], ["I", 1]
    ];
    
    let res = "";
    let s = { num, res, currSym: null, currVal: null };
    
    snap(3, `Start with num = ${num}, res = ""`, s);
    
    for (let i = 0; i < symList.length; i++) {
        let sym = symList[i][0];
        let val = symList[i][1];
        
        s.currSym = sym;
        s.currVal = val;
        
        if (num >= val) {
            let count = Math.floor(num / val);
            res += sym.repeat(count);
            num = num % val;
            
            s.num = num;
            s.res = res;
            snap(9, `Value ${val} (${sym}) fits ${count} times. Append "${sym.repeat(count)}" to res. num becomes ${num}.`, s);
        } else {
            snap(7, `Value ${val} (${sym}) is too large for ${num}. Skip.`, s);
        }
        
        if (num === 0) break;
    }
    
    s.currSym = null; s.currVal = null;
    snap(12, `Finished. Roman numeral is "${res}".`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="display:flex; justify-content:space-between; align-items:center; padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface);">
            <div>
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Remaining Value</div>
                <div style="font-size:32px; font-weight:bold; color:var(--text);">${state.num}</div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Current Roman String</div>
                <div style="font-size:32px; font-weight:bold; color:var(--accent); letter-spacing:2px;">${state.res || '""'}</div>
            </div>
        </div>`;
        
    if (state.currSym) {
        html += `<div style="padding:15px; border:2px solid #fbbf24; border-radius:8px; background:rgba(251,191,36,0.1); text-align:center;">
            <div style="font-size:16px;">Checking Symbol: <span style="font-weight:bold; color:#fbbf24; font-size:24px; margin-left:10px;">${state.currSym} (${state.currVal})</span></div>
        </div>`;
    }
    
    html += `</div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Count Primes', short: 'Count Primes',
  idea: 'Sieve of Eratosthenes. Start with an array of booleans. For each prime found, mark all its multiples as composite (not prime).',
  complexity: 'Time O(N log(log N)) · Space O(N)',
  input: '30', hint: 'integer n',
  code: [
    'def countPrimes(n):',
    '    if n < 2:',
    '        return 0',
    '    isPrime = [True] * n',
    '    isPrime[0] = isPrime[1] = False',
    '    for i in range(2, int(math.ceil(math.sqrt(n)))):',
    '        if isPrime[i]:',
    '            for multiples_of_i in range(i * i, n, i):',
    '                isPrime[multiples_of_i] = False',
    '    return sum(isPrime)'
  ],
  parse(str) {
    let n = parseInt(str.trim());
    if (n > 100) n = 100; // Cap to 100 for visualization
    return { n };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    
    if (n < 2) {
        snap(2, 'n is less than 2, return 0.', { n, primes: [], curr: null });
        return F;
    }
    
    let isPrime = new Array(n).fill(true);
    isPrime[0] = isPrime[1] = false;
    
    let s = { n, primes: [...isPrime], curr: null, multiple: null };
    snap(4, 'Initialize boolean array for primes up to n-1. Mark 0 and 1 as False.', s);
    
    let limit = Math.ceil(Math.sqrt(n));
    
    for (let i = 2; i < limit; i++) {
        s.curr = i;
        s.multiple = null;
        
        if (isPrime[i]) {
            snap(6, `Found prime ${i}. Now mark all its multiples starting from ${i*i} as False.`, s);
            
            for (let j = i * i; j < n; j += i) {
                isPrime[j] = false;
                s.multiple = j;
                s.primes = [...isPrime];
                snap(8, `Mark ${j} (multiple of ${i}) as not prime.`, s);
            }
        } else {
            snap(6, `Number ${i} is already marked as not prime. Skip.`, s);
        }
    }
    
    s.curr = null; s.multiple = null; s.primes = [...isPrime];
    let count = isPrime.filter(p => p).length;
    snap(10, `Finished. Count of primes less than ${n} is ${count}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:15px; font-family:var(--mono);">
        <div style="font-size:18px;">Finding primes less than ${state.n}</div>
        <div style="display:flex; flex-wrap:wrap; gap:5px;">`;
        
    for (let i = 0; i < state.primes.length; i++) {
        let isCurr = state.curr === i;
        let isMultiple = state.multiple === i;
        let isPrime = state.primes[i];
        
        let border = '1px solid var(--border)';
        let bg = 'var(--surface)';
        let color = 'var(--text)';
        
        if (isCurr) {
            border = '2px solid #34d399';
            bg = 'rgba(52,211,153,0.2)';
        } else if (isMultiple) {
            border = '2px solid #ef4444';
            bg = 'rgba(239,68,68,0.2)';
        } else if (isPrime && i >= 2) {
            bg = 'rgba(52,211,153,0.1)';
            color = '#34d399';
        } else {
            color = 'var(--text-dim)';
        }
        
        html += `<div style="width:35px; height:35px; display:flex; justify-content:center; align-items:center; border:${border}; background:${bg}; border-radius:4px; font-size:14px; font-weight:${isPrime ? 'bold' : 'normal'}; color:${color}; ${!isPrime ? 'text-decoration:line-through;' : ''}">
            ${i}
        </div>`;
    }
    
    html += `</div></div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('21_math_geometry', {
  title: 'Factorial Trailing Zeroes', short: 'Trailing Zeroes',
  idea: 'A trailing zero is produced by a factor of 10, which is 2 * 5. In any factorial, the number of 5 factors is always less than the number of 2 factors, so we just count factors of 5.',
  complexity: 'Time O(log5(N)) · Space O(1)',
  input: '25', hint: 'integer (e.g. 25)',
  code: [
    'def trailingZeroes(n):',
    '    res = 0',
    '    while n > 0:',
    '        n //= 5',
    '        res += n',
    '    return res'
  ],
  parse(str) {
    return { n: parseInt(str.trim()) };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    let res = 0;
    let s = { n, res, currN: n };
    
    snap(2, 'Initialize res = 0.', s);
    
    while (s.currN > 0) {
        let added = Math.floor(s.currN / 5);
        s.currN = added;
        res += added;
        s.res = res;
        
        snap(4, `Divide n by 5: new n = ${s.currN}. Add to res. res is now ${res}.`, s);
    }
    
    snap(6, `Finished. Total trailing zeroes is ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:18px;">Original n = <span style="font-weight:bold;">${state.n}</span></div>
        <div style="display:flex; gap:20px;">
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Current n (n //= 5)</div>
                <div style="font-size:24px; font-weight:bold; color:var(--accent);">${state.currN}</div>
            </div>
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Trailing Zeroes Count (res)</div>
                <div style="font-size:24px; font-weight:bold; color:#34d399;">${state.res}</div>
            </div>
        </div>
    </div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('21_math_geometry', {
  title: 'Detect Squares', short: 'Detect Squares',
  idea: 'Maintain counts of all points. For a query point (x, y), iterate through all points (px, py). If they form a valid diagonal (abs(px-x) == abs(py-y) and x != px), check if the other two corners (x, py) and (px, y) exist.',
  complexity: 'Time O(N) per query · Space O(N)',
  input: '[3, 10], [11, 2], [3, 2], query(11, 10)', hint: 'List of added points, then query point',
  code: [
    'class DetectSquares:',
    '    def __init__(self):',
    '        self.ptsCount = collections.defaultdict(int)',
    '        self.pts = []',
    '',
    '    def add(self, point):',
    '        self.ptsCount[tuple(point)] += 1',
    '        self.pts.append(point)',
    '',
    '    def count(self, point):',
    '        res = 0',
    '        qx, qy = point',
    '        for x, y in self.pts:',
    '            if abs(x - qx) != abs(y - qy) or x == qx:',
    '                continue',
    '            res += self.ptsCount[(x, qy)] * self.ptsCount[(qx, y)]',
    '        return res'
  ],
  parse(str) {
    // A simplified parser assuming format like: "[3, 10], [11, 2], [3, 2], [11, 10]" 
    // where the last one is the query point.
    let arr = str.replace(/[^\d,]/g, '').split(',');
    let points = [];
    for (let i = 0; i < arr.length; i += 2) {
       if(arr[i] && arr[i+1]) {
           points.push([parseInt(arr[i]), parseInt(arr[i+1])]);
       }
    }
    if (points.length < 2) return { points: [], query: [0, 0] };
    const query = points.pop();
    return { points, query };
  },
  run({ points, query }) {
    const { F, snap } = avRecorder();
    
    let ptsCount = {};
    for (let p of points) {
        let key = p[0] + ',' + p[1];
        ptsCount[key] = (ptsCount[key] || 0) + 1;
    }
    
    const [qx, qy] = query;
    let res = 0;
    
    let s = { points, query, qx, qy, ptsCount, res, currP: null, p2: null, p4: null, added: 0 };
    snap(2, `Added points to map. Query point is [${qx}, ${qy}]. Initialize res = 0.`, s);
    
    for (let p of points) {
        const [x, y] = p;
        s.currP = p;
        s.p2 = null;
        s.p4 = null;
        s.added = 0;
        
        if (Math.abs(x - qx) !== Math.abs(y - qy) || x === qx) {
            snap(13, `Point [${x}, ${y}] does not form a valid diagonal with [${qx}, ${qy}]. Skip.`, s);
            continue;
        }
        
        s.p2 = [x, qy];
        s.p4 = [qx, y];
        
        let count2 = ptsCount[x + ',' + qy] || 0;
        let count4 = ptsCount[qx + ',' + y] || 0;
        
        let squares = count2 * count4;
        res += squares;
        
        s.res = res;
        s.added = squares;
        
        snap(15, `Point [${x}, ${y}] forms a diagonal! Check corners [${x}, ${qy}] (count: ${count2}) and [${qx}, ${y}] (count: ${count4}). Added ${squares} squares.`, s);
    }
    
    s.currP = null; s.p2 = null; s.p4 = null; s.added = 0;
    snap(17, `Finished. Total squares found: ${res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:16px;">
            Query Point (p1): <span style="font-weight:bold; color:var(--accent);">[${state.qx}, ${state.qy}]</span>
        </div>
        <div style="display:flex; gap:20px;">
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Current Diagonal Point (p3)</div>
                <div style="font-size:24px; font-weight:bold; color:${state.currP ? '#fbbf24' : 'var(--text-dim)'};">${state.currP ? `[${state.currP[0]}, ${state.currP[1]}]` : 'None'}</div>
            </div>
            <div style="padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface); flex:1;">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:5px;">Total Squares (res)</div>
                <div style="font-size:24px; font-weight:bold; color:#34d399;">${state.res}</div>
            </div>
        </div>`;
        
    if (state.p2 && state.p4) {
        let count2 = state.ptsCount[state.p2[0] + ',' + state.p2[1]] || 0;
        let count4 = state.ptsCount[state.p4[0] + ',' + state.p4[1]] || 0;
        
        html += `<div style="padding:15px; border:1px solid #34d399; border-radius:8px; background:rgba(52,211,153,0.1);">
            <div style="font-size:14px; margin-bottom:5px;">Other Required Corners:</div>
            <div style="display:flex; gap:20px; font-weight:bold;">
                <div>p2: [${state.p2[0]}, ${state.p2[1]}] (Found: ${count2})</div>
                <div>p4: [${state.p4[0]}, ${state.p4[1]}] (Found: ${count4})</div>
            </div>
            <div style="margin-top:10px; color:#34d399; font-weight:bold;">=> ${count2} * ${count4} = ${state.added} squares added!</div>
        </div>`;
    }
    
    let allPtsStr = Object.entries(state.ptsCount).map(([k, v]) => `[${k}]: ${v}`).join(', ');
    html += `<div style="font-size:12px; color:var(--text-dim); margin-top:10px;">Stored Points: { ${allPtsStr} }</div>`;
    
    html += `</div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('21_math_geometry', {
  title: 'Max Points on a Line', short: 'Max Points',
  idea: 'For each point, calculate the slopes to all other points. Keep a map of slopes to counts. The maximum number of points on a line going through this point is max(counts) + 1.',
  complexity: 'Time O(N^2) · Space O(N)',
  input: '[1,1],[2,2],[3,3]', hint: 'list of points',
  code: [
    'def maxPoints(points):',
    '    if len(points) <= 2: return len(points)',
    '    res = 0',
    '    for i in range(len(points)):',
    '        slopes = collections.defaultdict(int)',
    '        for j in range(i + 1, len(points)):',
    '            dx, dy = points[j][0] - points[i][0], points[j][1] - points[i][1]',
    '            if dx == 0:',
    '                slope = float("inf")',
    '            else:',
    '                slope = dy / dx',
    '            slopes[slope] += 1',
    '            res = max(res, slopes[slope] + 1)',
    '    return res'
  ],
  parse(str) {
    let arr = str.replace(/[^\d,-]/g, ' ').trim().split(/\s+/).map(x => x.replace(/,/g, ''));
    let points = [];
    for (let i = 0; i < arr.length; i += 2) {
       if(arr[i] && arr[i+1]) {
           points.push([parseInt(arr[i]), parseInt(arr[i+1])]);
       }
    }
    return { points };
  },
  run({ points }) {
    const { F, snap } = avRecorder();
    
    let s = { points, res: 0, p1: null, p2: null, slopes: {}, currSlope: null };
    
    if (points.length <= 2) {
        snap(2, '2 or fewer points, they always form a line.', s);
        return F;
    }
    
    snap(3, 'Initialize res = 0.', s);
    
    for (let i = 0; i < points.length; i++) {
        let slopes = {};
        s.p1 = points[i];
        s.slopes = slopes;
        s.p2 = null;
        s.currSlope = null;
        
        snap(5, `Anchor point: [${s.p1[0]}, ${s.p1[1]}]. Initialize slopes map.`, s);
        
        for (let j = i + 1; j < points.length; j++) {
            s.p2 = points[j];
            let dx = points[j][0] - points[i][0];
            let dy = points[j][1] - points[i][1];
            
            let slope = dx === 0 ? "inf" : (dy / dx).toFixed(4); // Simplified slope representation for viz
            // Need to fix precision issues in JS for floats, so we stringify with fixed precision.
            
            slopes[slope] = (slopes[slope] || 0) + 1;
            s.currSlope = slope;
            
            if (slopes[slope] + 1 > s.res) {
                s.res = slopes[slope] + 1;
            }
            
            s.slopes = {...slopes};
            snap(11, `Target point: [${s.p2[0]}, ${s.p2[1]}]. Slope is ${slope}. Map[${slope}] = ${slopes[slope]}. Current max result = ${s.res}.`, s);
        }
    }
    
    s.p1 = null; s.p2 = null; s.currSlope = null;
    snap(14, `Finished. Max points on a line: ${s.res}.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:15px; font-family:var(--mono);">
        <div style="font-size:18px;">Global Max Points: <span style="font-weight:bold; color:var(--accent); font-size:24px;">${state.res}</span></div>
        <div style="display:flex; gap:20px;">
            <div style="padding:15px; border:2px solid #3b82f6; border-radius:8px; background:rgba(59,130,246,0.1); flex:1;">
                <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Anchor Point (p1)</div>
                <div style="font-size:20px; font-weight:bold; color:#3b82f6;">${state.p1 ? `[${state.p1[0]}, ${state.p1[1]}]` : 'None'}</div>
            </div>
            <div style="padding:15px; border:2px solid #ef4444; border-radius:8px; background:rgba(239,68,68,0.1); flex:1;">
                <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Target Point (p2)</div>
                <div style="font-size:20px; font-weight:bold; color:#ef4444;">${state.p2 ? `[${state.p2[0]}, ${state.p2[1]}]` : 'None'}</div>
            </div>
        </div>`;
        
    if (state.currSlope) {
        html += `<div style="padding:10px; border:1px solid #fbbf24; border-radius:8px; background:rgba(251,191,36,0.1); text-align:center;">
            Calculated Slope: <span style="font-weight:bold; color:#fbbf24;">${state.currSlope}</span>
        </div>`;
    }
    
    if (state.p1) {
        let mapStr = Object.entries(state.slopes).map(([k, v]) => `<span style="background:var(--surface); padding:3px 6px; border-radius:4px; margin-right:5px; border:1px solid var(--border);">${k} : ${v}</span>`).join(' ');
        html += `<div style="font-size:14px;">
            <div style="color:var(--text-dim); margin-bottom:5px;">Slopes Map for Anchor Point:</div>
            <div style="line-height:2;">${mapStr || 'Empty'}</div>
        </div>`;
    }
    
    html += `</div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('22_sorting_algorithms', {
  title: 'Merge Sorted Array', short: 'Merge Arrays',
  idea: 'Use three pointers starting from the end of both arrays to merge them in-place into nums1 without extra space.',
  complexity: 'Time O(m + n) · Space O(1)',
  input: '[1,2,3,0,0,0], 3, [2,5,6], 3', hint: 'nums1, m, nums2, n',
  code: [
    'def merge(nums1, m, nums2, n):',
    '    p1 = m - 1',
    '    p2 = n - 1',
    '    p = m + n - 1',
    '    while p1 >= 0 and p2 >= 0:',
    '        if nums1[p1] > nums2[p2]:',
    '            nums1[p] = nums1[p1]',
    '            p1 -= 1',
    '        else:',
    '            nums1[p] = nums2[p2]',
    '            p2 -= 1',
    '        p -= 1',
    '    while p2 >= 0:',
    '        nums1[p] = nums2[p2]',
    '        p2 -= 1',
    '        p -= 1'
  ],
  parse(str) {
    let parts = str.split('],');
    if (parts.length < 2) return { nums1: [1,2,3,0,0,0], m: 3, nums2: [2,5,6], n: 3 };
    let n1_str = parts[0].replace('[', '').trim();
    let nums1 = n1_str ? n1_str.split(',').map(Number) : [];
    
    let rem = parts[1].split(',[');
    let m = parseInt(rem[0].trim());
    
    let n2_str = rem[1] ? rem[1].replace(']', '').trim() : '';
    let nums2 = n2_str ? n2_str.split(',').map(Number) : [];
    
    let n = parseInt(parts[2] || (rem[2] ? rem[2] : nums2.length));
    
    return { nums1, m, nums2, n };
  },
  run({ nums1, m, nums2, n }) {
    const { F, snap } = avRecorder();
    let s = { nums1: [...nums1], nums2: [...nums2], m, n, p1: m - 1, p2: n - 1, p: m + n - 1 };
    
    snap(2, 'Initialize pointers at the end of the arrays.', s);
    
    while (s.p1 >= 0 && s.p2 >= 0) {
        snap(4, `Compare nums1[p1] (${s.nums1[s.p1]}) and nums2[p2] (${s.nums2[s.p2]}).`, s);
        if (s.nums1[s.p1] > s.nums2[s.p2]) {
            s.nums1[s.p] = s.nums1[s.p1];
            snap(6, `nums1[p1] is larger, place it at nums1[p] (index ${s.p}).`, s);
            s.p1--;
        } else {
            s.nums1[s.p] = s.nums2[s.p2];
            snap(9, `nums2[p2] is larger or equal, place it at nums1[p] (index ${s.p}).`, s);
            s.p2--;
        }
        s.p--;
    }
    
    while (s.p2 >= 0) {
        s.nums1[s.p] = s.nums2[s.p2];
        snap(13, `Copy remaining elements from nums2. Placed ${s.nums2[s.p2]} at index ${s.p}.`, s);
        s.p2--;
        s.p--;
    }
    
    snap(16, 'Merge complete.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let renderArray = (arr, title, ptr1, ptr1Name, ptr1Color, ptr2, ptr2Name, ptr2Color) => {
        let boxes = arr.map((val, i) => {
            let bg = 'var(--surface)';
            let borderColor = 'var(--border)';
            let labels = [];
            if (i === ptr1) {
                borderColor = ptr1Color;
                labels.push(`<div style="color:${ptr1Color}; font-size:12px; font-weight:bold;">${ptr1Name}</div>`);
            }
            if (ptr2 !== undefined && i === ptr2) {
                borderColor = ptr2Color;
                labels.push(`<div style="color:${ptr2Color}; font-size:12px; font-weight:bold;">${ptr2Name}</div>`);
            }
            return `<div style="display:flex; flex-direction:column; align-items:center; width:40px;">
                ${labels.join('')}
                <div style="width:100%; height:40px; display:flex; align-items:center; justify-content:center; border:2px solid ${borderColor}; background:${bg}; border-radius:4px; font-weight:bold;">
                    ${val !== undefined && val !== null ? val : ''}
                </div>
                <div style="font-size:11px; color:var(--text-dim); margin-top:4px;">${i}</div>
            </div>`;
        }).join('');
        return `<div>
            <div style="font-size:14px; color:var(--text-dim); margin-bottom:10px;">${title}</div>
            <div style="display:flex; gap:5px;">${boxes}</div>
        </div>`;
    };
    
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        ${renderArray(state.nums1, 'nums1', state.p1, 'p1', 'var(--accent)', state.p, 'p', '#34d399')}
        ${renderArray(state.nums2, 'nums2', state.p2, 'p2', '#f43f5e')}
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('22_sorting_algorithms', {
  title: 'Sort an Array', short: 'Merge Sort',
  idea: 'Divide the array in halves recursively, then merge the sorted halves.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '5, 2, 3, 1', hint: 'comma-separated integers',
  code: [
    'def sortArray(nums):',
    '    if len(nums) <= 1:',
    '        return nums',
    '    mid = len(nums) // 2',
    '    left = sortArray(nums[:mid])',
    '    right = sortArray(nums[mid:])',
    '    return merge(left, right)',
    '',
    'def merge(left, right):',
    '    res = []',
    '    i = j = 0',
    '    while i < len(left) and j < len(right):',
    '        if left[i] < right[j]:',
    '            res.append(left[i])',
    '            i += 1',
    '        else:',
    '            res.append(right[j])',
    '            j += 1',
    '    res.extend(left[i:])',
    '    res.extend(right[j:])',
    '    return res'
  ],
  parse(str) {
    return { nums: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let s = { currArr: [...nums], subArrays: [[...nums]], level: 0, action: 'Start' };
    
    function mergeSort(arr, lLevel) {
        if (arr.length <= 1) return arr;
        let mid = Math.floor(arr.length / 2);
        
        s.action = `Splitting array of size ${arr.length}`;
        s.currArr = [...arr];
        s.level = lLevel;
        snap(4, `Split array: [${arr.join(', ')}]`, s);
        
        let left = mergeSort(arr.slice(0, mid), lLevel + 1);
        let right = mergeSort(arr.slice(mid), lLevel + 1);
        
        return mergeArrays(left, right, lLevel);
    }
    
    function mergeArrays(left, right, lLevel) {
        let res = [];
        let i = 0, j = 0;
        
        s.action = `Merging [${left.join(', ')}] and [${right.join(', ')}]`;
        s.level = lLevel;
        snap(9, `Merging two halves.`, s);
        
        while (i < left.length && j < right.length) {
            if (left[i] < right[j]) {
                res.push(left[i]);
                i++;
            } else {
                res.push(right[j]);
                j++;
            }
        }
        res = res.concat(left.slice(i)).concat(right.slice(j));
        
        s.action = `Merged Result: [${res.join(', ')}]`;
        s.currArr = [...res];
        s.level = lLevel;
        snap(19, `Merge complete.`, s);
        return res;
    }
    
    mergeSort(nums, 0);
    s.action = 'Finished Sorting';
    snap(7, 'Array is completely sorted.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:16px; font-weight:bold; color:var(--accent);">${state.action}</div>
        <div style="font-size:14px; color:var(--text-dim);">Recursion Level: ${state.level}</div>
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            ${state.currArr.map(x => `<div style="padding:10px 15px; border:1px solid var(--border); border-radius:4px; background:var(--surface); font-weight:bold; font-size:18px;">${x}</div>`).join('')}
        </div>
    </div>`;
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('22_sorting_algorithms', {
  title: 'Sort Colors', short: 'Sort Colors',
  idea: 'Dutch National Flag algorithm. Use three pointers: low, mid, and high. mid scans the array and swaps elements to place 0s before low, 2s after high, and leaves 1s in the middle.',
  complexity: 'Time O(N) · Space O(1)',
  input: '2,0,2,1,1,0', hint: 'comma-separated colors (0, 1, 2)',
  code: [
    'def sortColors(nums):',
    '    low, mid, high = 0, 0, len(nums) - 1',
    '    while mid <= high:',
    '        if nums[mid] == 0:',
    '            nums[low], nums[mid] = nums[mid], nums[low]',
    '            low += 1',
    '            mid += 1',
    '        elif nums[mid] == 1:',
    '            mid += 1',
    '        else:',
    '            nums[mid], nums[high] = nums[high], nums[mid]',
    '            high -= 1'
  ],
  parse(str) {
    return { nums: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let s = { nums: [...nums], low: 0, mid: 0, high: nums.length - 1 };
    
    snap(2, 'Initialize pointers: low = 0, mid = 0, high = len - 1.', s);
    
    while (s.mid <= s.high) {
        if (s.nums[s.mid] === 0) {
            snap(4, `nums[mid] is 0. Swap nums[low] and nums[mid].`, s);
            let temp = s.nums[s.low];
            s.nums[s.low] = s.nums[s.mid];
            s.nums[s.mid] = temp;
            s.low++;
            s.mid++;
            snap(6, `Increment low and mid.`, s);
        } else if (s.nums[s.mid] === 1) {
            snap(8, `nums[mid] is 1. Just increment mid.`, s);
            s.mid++;
            snap(9, `Increment mid.`, s);
        } else {
            snap(11, `nums[mid] is 2. Swap nums[mid] and nums[high].`, s);
            let temp = s.nums[s.high];
            s.nums[s.high] = s.nums[s.mid];
            s.nums[s.mid] = temp;
            s.high--;
            snap(12, `Decrement high.`, s);
        }
    }
    snap(12, 'Sorting complete.', s);
    return F;
  },
  renderDOM(container, state, spec) {
    let boxes = state.nums.map((val, i) => {
        let bg = 'var(--surface)';
        if (val === 0) bg = '#fca5a5'; // Red-ish
        else if (val === 1) bg = '#fde047'; // White/Yellow-ish
        else if (val === 2) bg = '#93c5fd'; // Blue-ish
        
        let labels = [];
        if (i === state.low) labels.push('<div style="color:#ef4444; font-size:12px; font-weight:bold;">low</div>');
        if (i === state.mid) labels.push('<div style="color:var(--accent); font-size:12px; font-weight:bold;">mid</div>');
        if (i === state.high) labels.push('<div style="color:#3b82f6; font-size:12px; font-weight:bold;">high</div>');
        
        return `<div style="display:flex; flex-direction:column; align-items:center; width:40px;">
            <div style="height:45px; display:flex; flex-direction:column; justify-content:flex-end;">
                ${labels.join('')}
            </div>
            <div style="width:100%; height:40px; display:flex; align-items:center; justify-content:center; border:1px solid var(--border); background:${bg}; color:#000; border-radius:4px; font-weight:bold; margin-top:5px;">
                ${val}
            </div>
            <div style="font-size:11px; color:var(--text-dim); margin-top:4px;">${i}</div>
        </div>`;
    }).join('');
    
    let html = `
        <div style="font-family:var(--mono);">
            <div style="display:flex; gap:10px;">${boxes}</div>
            <div style="margin-top:20px; font-size:14px; color:var(--text-dim);">
                Colors: <span style="color:#ef4444; font-weight:bold;">0 (Red)</span>, 
                <span style="color:#eab308; font-weight:bold;">1 (White)</span>, 
                <span style="color:#3b82f6; font-weight:bold;">2 (Blue)</span>
            </div>
        </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('22_sorting_algorithms', {
  title: 'Sort List', short: 'Sort List',
  idea: 'Top-down merge sort on a linked list. Use fast and slow pointers to find the middle, split the list, recursively sort both halves, and then merge them.',
  complexity: 'Time O(N log N) · Space O(log N) recursion depth',
  input: '4,2,1,3', hint: 'comma-separated values',
  code: [
    'def sortList(head):',
    '    if not head or not head.next:',
    '        return head',
    '    ',
    '    slow, fast = head, head.next',
    '    while fast and fast.next:',
    '        slow = slow.next',
    '        fast = fast.next.next',
    '    ',
    '    mid = slow.next',
    '    slow.next = None',
    '    ',
    '    left = sortList(head)',
    '    right = sortList(mid)',
    '    return merge(left, right)',
    '',
    'def merge(list1, list2):',
    '    dummy = ListNode()',
    '    tail = dummy',
    '    while list1 and list2:',
    '        if list1.val < list2.val:',
    '            tail.next = list1',
    '            list1 = list1.next',
    '        else:',
    '            tail.next = list2',
    '            list2 = list2.next',
    '        tail = tail.next',
    '    tail.next = list1 or list2',
    '    return dummy.next'
  ],
  parse(str) {
    return { vals: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ vals }) {
    const { F, snap } = avRecorder();
    let s = { list1: [], list2: [], action: 'Start', merged: [...vals] };
    
    function mergeSortList(arr, lLevel) {
        if (arr.length <= 1) return arr;
        let mid = Math.ceil(arr.length / 2); // To mimic slow/fast pointer (head.next)
        
        s.action = 'Splitting List';
        s.list1 = arr.slice(0, mid);
        s.list2 = arr.slice(mid);
        s.merged = [];
        snap(10, `Split list into two halves.`, s);
        
        let left = mergeSortList(arr.slice(0, mid), lLevel + 1);
        let right = mergeSortList(arr.slice(mid), lLevel + 1);
        
        return mergeArrays(left, right);
    }
    
    function mergeArrays(left, right) {
        let res = [];
        let i = 0, j = 0;
        
        s.action = 'Merging Lists';
        s.list1 = left.slice(i);
        s.list2 = right.slice(j);
        s.merged = [...res];
        snap(18, `Start merging.`, s);
        
        while (i < left.length && j < right.length) {
            if (left[i] < right[j]) {
                res.push(left[i]);
                i++;
            } else {
                res.push(right[j]);
                j++;
            }
            s.list1 = left.slice(i);
            s.list2 = right.slice(j);
            s.merged = [...res];
            snap(20, `Merge step.`, s);
        }
        res = res.concat(left.slice(i)).concat(right.slice(j));
        s.list1 = [];
        s.list2 = [];
        s.merged = [...res];
        snap(27, `Merge complete for this segment.`, s);
        return res;
    }
    
    let result = mergeSortList(vals, 0);
    s.action = 'Done';
    s.merged = result;
    s.list1 = [];
    s.list2 = [];
    snap(28, `List is fully sorted.`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let renderList = (arr) => {
        if (!arr || arr.length === 0) return `<div style="color:var(--text-dim); font-style:italic;">null</div>`;
        return arr.map((val, i) => {
            let node = `<div style="display:flex; align-items:center; justify-content:center; width:35px; height:35px; border:1px solid var(--border); border-radius:50%; background:var(--surface); font-weight:bold;">${val}</div>`;
            if (i < arr.length - 1) {
                return node + `<div style="margin:0 5px; color:var(--text-dim);">→</div>`;
            }
            return node;
        }).join('');
    };
    
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:16px; font-weight:bold; color:var(--accent);">${state.action}</div>
        
        <div style="display:flex; flex-direction:column; gap:10px;">
            <div style="font-size:14px; color:var(--text-dim);">Left List (or Split 1):</div>
            <div style="display:flex; align-items:center;">${renderList(state.list1)}</div>
        </div>
        
        <div style="display:flex; flex-direction:column; gap:10px;">
            <div style="font-size:14px; color:var(--text-dim);">Right List (or Split 2):</div>
            <div style="display:flex; align-items:center;">${renderList(state.list2)}</div>
        </div>
        
        <div style="display:flex; flex-direction:column; gap:10px; margin-top:20px;">
            <div style="font-size:14px; color:var(--text-dim);">Merged / Result List:</div>
            <div style="display:flex; align-items:center;">${renderList(state.merged)}</div>
        </div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('22_sorting_algorithms', {
  title: 'Largest Number', short: 'Largest Number',
  idea: 'Sort strings by a custom comparator where `a + b > b + a` ensures the optimal concatenation.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '3, 30, 34, 5, 9', hint: 'comma-separated integers',
  code: [
    'class Solution:',
    '    def largestNumber(self, nums: List[int]) -> str:',
    '        nums_str = [str(n) for n in nums]',
    '        nums_str.sort(key=cmp_to_key(lambda a, b: -1 if a+b > b+a else (1 if a+b < b+a else 0)))',
    '        if nums_str[0] == "0":',
    '            return "0"',
    '        return "".join(nums_str)'
  ],
  parse(str) {
    return { nums: str.split(',').map(s => s.trim()).filter(s => s) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let s = { nums: [...nums], compare: null, res: "" };
    
    snap(3, 'Convert all numbers to strings and begin custom sorting.', s);
    
    // Bubble sort for visualization purposes to show comparisons
    let arr = [...nums];
    for (let i = 0; i < arr.length; i++) {
        for (let j = 0; j < arr.length - 1 - i; j++) {
            let a = arr[j], b = arr[j+1];
            s.nums = [...arr];
            s.compare = { a, b, ab: a+b, ba: b+a, idx_a: j, idx_b: j+1, swap: false };
            
            if (a + b < b + a) {
                s.compare.swap = true;
                snap(4, `Compare '${a}' and '${b}': '${a+b}' < '${b+a}', so '${b}' should come first. Swap.`, s);
                let temp = arr[j];
                arr[j] = arr[j+1];
                arr[j+1] = temp;
                s.nums = [...arr];
                snap(4, `Swapped.`, s);
            } else {
                s.compare.swap = false;
                snap(4, `Compare '${a}' and '${b}': '${a+b}' >= '${b+a}', so order is correct.`, s);
            }
        }
    }
    
    s.compare = null;
    s.nums = [...arr];
    
    if (s.nums[0] === '0') {
        s.res = "0";
        snap(5, 'Array is sorted. Leading digit is 0, so result is "0".', s);
    } else {
        s.res = s.nums.join("");
        snap(7, `Array is sorted. Concatenate all elements.`, s);
    }
    
    return F;
  },
  renderDOM(container, state, spec) {
    let boxes = state.nums.map((val, i) => {
        let isComparing = state.compare && (state.compare.idx_a === i || state.compare.idx_b === i);
        let bg = isComparing ? 'var(--accent)' : 'var(--surface)';
        let color = isComparing ? '#000' : 'var(--text-color)';
        return `<div style="padding:10px; border:1px solid var(--border); border-radius:4px; background:${bg}; color:${color}; font-weight:bold; font-size:16px;">
            ${val}
        </div>`;
    }).join('');
    
    let compareHtml = '';
    if (state.compare) {
        let c = state.compare;
        compareHtml = `
            <div style="margin-top:20px; padding:15px; border:1px solid var(--border); border-radius:8px; background:var(--surface);">
                <div style="font-size:14px; color:var(--text-dim); margin-bottom:10px;">Comparison:</div>
                <div style="display:flex; justify-content:space-around; text-align:center;">
                    <div>
                        <div style="font-size:12px; color:var(--text-dim);">a + b</div>
                        <div style="font-weight:bold;">${c.ab}</div>
                    </div>
                    <div>
                        <div style="font-size:12px; color:var(--text-dim);">b + a</div>
                        <div style="font-weight:bold;">${c.ba}</div>
                    </div>
                    <div>
                        <div style="font-size:12px; color:var(--text-dim);">Action</div>
                        <div style="font-weight:bold; color:${c.swap ? '#ef4444' : '#34d399'};">${c.swap ? 'Swap' : 'Keep'}</div>
                    </div>
                </div>
            </div>`;
    }
    
    let html = `<div style="font-family:var(--mono); display:flex; flex-direction:column; gap:10px;">
        <div style="display:flex; gap:10px; flex-wrap:wrap;">${boxes}</div>
        ${compareHtml}
        ${state.res ? `<div style="margin-top:20px; font-size:16px;">Result: <span style="font-weight:bold; color:var(--accent);">${state.res}</span></div>` : ''}
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('22_sorting_algorithms', {
  title: 'H-Index', short: 'H-Index',
  idea: 'Sort citations descending. Linearly scan; as long as citations[i] >= i + 1, we can form an h-index of i + 1.',
  complexity: 'Time O(N log N) · Space O(1)',
  input: '3,0,6,1,5', hint: 'comma-separated citation counts',
  code: [
    'def hIndex(citations):',
    '    citations = sorted(citations, reverse=True)',
    '    h = 0',
    '    for i, c in enumerate(citations):',
    '        if c >= i + 1:',
    '            h = i + 1',
    '        else:',
    '            break',
    '    return h'
  ],
  parse(str) {
    return { citations: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ citations }) {
    const { F, snap } = avRecorder();
    let s = { citations: [...citations], sorted: false, i: null, h: 0 };
    
    snap(1, 'Initial unsorted citations array.', s);
    
    s.citations.sort((a, b) => b - a);
    s.sorted = true;
    snap(2, 'Sort citations in descending order.', s);
    
    for (let i = 0; i < s.citations.length; i++) {
        s.i = i;
        let c = s.citations[i];
        snap(4, `Examine paper at index ${i} with ${c} citations. Require ${c} >= ${i + 1} (index + 1) for an h-index of ${i + 1}.`, s);
        
        if (c >= i + 1) {
            s.h = i + 1;
            snap(6, `Condition met! c (${c}) >= ${i + 1}. Current best h-index = ${s.h}.`, s);
        } else {
            snap(8, `Condition failed! c (${c}) < ${i + 1}. Stop here.`, s);
            break;
        }
    }
    
    s.i = null;
    snap(9, `Return final h-index = ${s.h}.`, s);
    
    return F;
  },
  renderDOM(container, state, spec) {
    let boxes = state.citations.map((c, i) => {
        let isCurrent = state.i === i;
        let bg = isCurrent ? 'var(--accent)' : 'var(--surface)';
        let color = isCurrent ? '#000' : 'var(--text-color)';
        let label = (state.sorted && c >= i + 1 && (state.i === null || state.i >= i)) ? `<div style="color:#34d399; font-size:12px;">Valid</div>` : '';
        
        return `<div style="display:flex; flex-direction:column; align-items:center; width:50px;">
            <div style="height:20px;">${label}</div>
            <div style="width:100%; height:50px; display:flex; align-items:center; justify-content:center; border:1px solid var(--border); background:${bg}; color:${color}; font-weight:bold; font-size:18px; border-radius:4px;">
                ${c}
            </div>
            <div style="font-size:11px; color:var(--text-dim); margin-top:4px;">idx ${i}</div>
            <div style="font-size:11px; color:var(--text-dim);">Req >= ${i+1}</div>
        </div>`;
    }).join('');
    
    let html = `<div style="font-family:var(--mono); display:flex; flex-direction:column; gap:20px;">
        <div style="display:flex; gap:10px; flex-wrap:wrap;">${boxes}</div>
        <div style="font-size:18px;">Current h: <span style="font-weight:bold; color:var(--accent);">${state.h}</span></div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});


defineAlgo('22_sorting_algorithms', {
  title: 'Maximum Gap', short: 'Maximum Gap',
  idea: 'Use Bucket Sort concept (Pigeonhole principle). Divide the range into buckets of size `(max - min) / (N - 1)`. The maximum gap cannot be within a single bucket, so we only need to track the min and max of each bucket, and find the max difference between adjacent non-empty buckets.',
  complexity: 'Time O(N) · Space O(N)',
  input: '3, 6, 9, 1', hint: 'comma-separated integers',
  code: [
    'def maximumGap(nums):',
    '    if len(nums) < 2: return 0',
    '    lo, hi = min(nums), max(nums)',
    '    if lo == hi: return 0',
    '    ',
    '    bucket_size = max(1, (hi - lo) // (len(nums) - 1))',
    '    bucket_count = (hi - lo) // bucket_size + 1',
    '    bucket_min = [None] * bucket_count',
    '    bucket_max = [None] * bucket_count',
    '    ',
    '    for x in nums:',
    '        idx = (x - lo) // bucket_size',
    '        bucket_min[idx] = x if bucket_min[idx] is None else min(bucket_min[idx], x)',
    '        bucket_max[idx] = x if bucket_max[idx] is None else max(bucket_max[idx], x)',
    '        ',
    '    max_gap, prev_max = 0, lo',
    '    for i in range(bucket_count):',
    '        if bucket_min[i] is None: continue',
    '        max_gap = max(max_gap, bucket_min[i] - prev_max)',
    '        prev_max = bucket_max[i]',
    '    return max_gap'
  ],
  parse(str) {
    return { nums: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let s = { nums: [...nums], bucket_min: [], bucket_max: [], max_gap: 0, prev_max: null, curr_num: null, curr_bucket: null, curr_gap: null };
    
    if (nums.length < 2) {
        snap(2, 'Less than 2 elements, max gap is 0.', s);
        return F;
    }
    
    let lo = Math.min(...nums);
    let hi = Math.max(...nums);
    
    if (lo === hi) {
        snap(4, 'All elements are equal, max gap is 0.', s);
        return F;
    }
    
    let bucket_size = Math.max(1, Math.floor((hi - lo) / (nums.length - 1)));
    let bucket_count = Math.floor((hi - lo) / bucket_size) + 1;
    
    s.bucket_min = new Array(bucket_count).fill(null);
    s.bucket_max = new Array(bucket_count).fill(null);
    
    snap(9, `Calculated Min: ${lo}, Max: ${hi}. Bucket size: ${bucket_size}, Count: ${bucket_count}`, s);
    
    for (let x of nums) {
        let idx = Math.floor((x - lo) / bucket_size);
        s.curr_num = x;
        s.curr_bucket = idx;
        
        if (s.bucket_min[idx] === null || x < s.bucket_min[idx]) s.bucket_min[idx] = x;
        if (s.bucket_max[idx] === null || x > s.bucket_max[idx]) s.bucket_max[idx] = x;
        
        snap(14, `Place ${x} into bucket ${idx}. Min of bucket: ${s.bucket_min[idx]}, Max of bucket: ${s.bucket_max[idx]}.`, s);
    }
    
    s.curr_num = null;
    s.curr_bucket = null;
    s.prev_max = lo;
    s.max_gap = 0;
    
    snap(17, `Finished placing numbers. Now iterate through buckets to find max gap.`, s);
    
    for (let i = 0; i < bucket_count; i++) {
        if (s.bucket_min[i] === null) continue;
        s.curr_bucket = i;
        
        let gap = s.bucket_min[i] - s.prev_max;
        s.curr_gap = gap;
        if (gap > s.max_gap) {
            s.max_gap = gap;
            snap(20, `Bucket ${i} min is ${s.bucket_min[i]}. Gap with prev_max (${s.prev_max}) is ${gap}. NEW MAX GAP!`, s);
        } else {
            snap(20, `Bucket ${i} min is ${s.bucket_min[i]}. Gap with prev_max (${s.prev_max}) is ${gap}.`, s);
        }
        
        s.prev_max = s.bucket_max[i];
    }
    
    s.curr_bucket = null;
    snap(22, `Final max gap is ${s.max_gap}.`, s);
    
    return F;
  },
  renderDOM(container, state, spec) {
    let boxes = state.bucket_min.map((_, i) => {
        let minV = state.bucket_min[i];
        let maxV = state.bucket_max[i];
        let isCurr = state.curr_bucket === i;
        
        return `<div style="display:flex; flex-direction:column; align-items:center; width:60px; padding:5px; border:2px solid ${isCurr ? 'var(--accent)' : 'var(--border)'}; border-radius:4px; background:var(--surface);">
            <div style="font-size:12px; color:var(--text-dim);">B ${i}</div>
            <div style="font-size:14px; font-weight:bold; color:#34d399; margin-top:5px;">${minV !== null ? minV : '-'}</div>
            <div style="font-size:14px; font-weight:bold; color:#f43f5e;">${maxV !== null ? maxV : '-'}</div>
        </div>`;
    }).join('');
    
    let html = `<div style="font-family:var(--mono); display:flex; flex-direction:column; gap:20px;">
        ${state.curr_num !== null ? `<div style="font-size:16px;">Current Num: <span style="font-weight:bold; color:var(--accent);">${state.curr_num}</span></div>` : ''}
        
        <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <div style="display:flex; flex-direction:column; justify-content:center; padding-right:10px;">
                <div style="font-size:12px; color:var(--text-dim);">&nbsp;</div>
                <div style="font-size:12px; color:var(--text-dim); margin-top:5px;">Min</div>
                <div style="font-size:12px; color:var(--text-dim); margin-top:3px;">Max</div>
            </div>
            ${boxes}
        </div>
        
        <div style="display:flex; flex-direction:column; gap:5px;">
            <div>Prev Max: <span style="font-weight:bold;">${state.prev_max !== null ? state.prev_max : '-'}</span></div>
            <div>Current Gap: <span style="font-weight:bold;">${state.curr_gap !== null ? state.curr_gap : '-'}</span></div>
            <div style="font-size:18px;">Max Gap: <span style="font-weight:bold; color:var(--accent);">${state.max_gap}</span></div>
        </div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('22_sorting_algorithms', {
  title: 'Count of Smaller Numbers After Self', short: 'Count Smaller',
  idea: 'Merge Sort based. We sort an array of (value, original_index). During the merge step, when an element from the left half is added to the merged array, the number of elements already added from the right half is exactly the number of smaller elements to its right.',
  complexity: 'Time O(N log N) · Space O(N)',
  input: '5, 2, 6, 1', hint: 'comma-separated integers',
  code: [
    'def countSmaller(nums):',
    '    counts = [0] * len(nums)',
    '    arr = [(v, i) for i, v in enumerate(nums)]',
    '    ',
    '    def merge_sort(arr):',
    '        if len(arr) <= 1: return arr',
    '        mid = len(arr) // 2',
    '        left = merge_sort(arr[:mid])',
    '        right = merge_sort(arr[mid:])',
    '        ',
    '        merged = []',
    '        i = j = 0',
    '        while i < len(left) and j < len(right):',
    '            if left[i][0] <= right[j][0]:',
    '                counts[left[i][1]] += j',
    '                merged.append(left[i])',
    '                i += 1',
    '            else:',
    '                merged.append(right[j])',
    '                j += 1',
    '        while i < len(left):',
    '            counts[left[i][1]] += j',
    '            merged.append(left[i])',
    '            i += 1',
    '        merged.extend(right[j:])',
    '        return merged',
    '        ',
    '    merge_sort(arr)',
    '    return counts'
  ],
  parse(str) {
    return { nums: str.split(',').map(n => parseInt(n.trim())).filter(n => !isNaN(n)) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let s = { nums: [...nums], counts: new Array(nums.length).fill(0), arr: nums.map((v, i) => ({v, i})), action: 'Start', left: [], right: [], merged: [], current_i: null, current_j: null };
    
    function merge_sort(arr, lLevel) {
        if (arr.length <= 1) return arr;
        let mid = Math.floor(arr.length / 2);
        
        let left = merge_sort(arr.slice(0, mid), lLevel + 1);
        let right = merge_sort(arr.slice(mid), lLevel + 1);
        
        let merged = [];
        let i = 0, j = 0;
        
        s.action = `Merging Arrays`;
        s.left = [...left];
        s.right = [...right];
        s.merged = [];
        s.current_i = i;
        s.current_j = j;
        snap(10, `Merging left: [${left.map(x=>x.v).join(',')}] and right: [${right.map(x=>x.v).join(',')}]`, s);
        
        while (i < left.length && j < right.length) {
            s.current_i = i;
            s.current_j = j;
            if (left[i].v <= right[j].v) {
                s.counts[left[i].i] += j;
                merged.push(left[i]);
                snap(15, `left[${i}] (${left[i].v}) <= right[${j}] (${right[j].v}). Add to counts[${left[i].i}] += ${j} (elements taken from right).`, s);
                i++;
            } else {
                merged.push(right[j]);
                snap(19, `left[${i}] (${left[i].v}) > right[${j}] (${right[j].v}). Take from right.`, s);
                j++;
            }
            s.merged = [...merged];
        }
        
        while (i < left.length) {
            s.current_i = i;
            s.current_j = j;
            s.counts[left[i].i] += j;
            merged.push(left[i]);
            snap(23, `Take remaining from left: ${left[i].v}. Add to counts[${left[i].i}] += ${j}.`, s);
            i++;
            s.merged = [...merged];
        }
        
        while (j < right.length) {
            merged.push(right[j]);
            j++;
        }
        s.merged = [...merged];
        
        s.current_i = null;
        s.current_j = null;
        snap(26, `Merge segment complete.`, s);
        return merged;
    }
    
    snap(3, `Start merge sort. Initial counts: [${s.counts.join(', ')}]`, s);
    merge_sort(s.arr, 0);
    
    s.action = 'Finished Sorting';
    s.left = [];
    s.right = [];
    snap(29, `Merge sort complete. Final counts: [${s.counts.join(', ')}]`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = `<div style="display:flex; flex-direction:column; gap:20px; font-family:var(--mono);">
        <div style="font-size:16px; font-weight:bold; color:var(--accent);">${state.action}</div>
        
        <div style="display:flex; gap:20px;">
            <div style="display:flex; flex-direction:column;">
                <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Left</div>
                <div style="display:flex; gap:5px;">
                    ${state.left.map((item, i) => {
                        let bg = state.current_i === i ? 'var(--accent)' : 'var(--surface)';
                        let col = state.current_i === i ? '#000' : 'var(--text-color)';
                        return `<div style="padding:5px 10px; border:1px solid var(--border); background:${bg}; color:${col}; border-radius:4px; text-align:center;">
                            <div style="font-weight:bold;">${item.v}</div>
                            <div style="font-size:10px; color:${state.current_i===i?'#333':'var(--text-dim)'};">idx ${item.i}</div>
                        </div>`;
                    }).join('') || '<span style="color:var(--text-dim);">empty</span>'}
                </div>
            </div>
            
            <div style="display:flex; flex-direction:column;">
                <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Right</div>
                <div style="display:flex; gap:5px;">
                    ${state.right.map((item, j) => {
                        let bg = state.current_j === j ? '#f43f5e' : 'var(--surface)';
                        let col = state.current_j === j ? '#fff' : 'var(--text-color)';
                        return `<div style="padding:5px 10px; border:1px solid var(--border); background:${bg}; color:${col}; border-radius:4px; text-align:center;">
                            <div style="font-weight:bold;">${item.v}</div>
                            <div style="font-size:10px; color:${state.current_j===j?'#ffccd5':'var(--text-dim)'};">idx ${item.i}</div>
                        </div>`;
                    }).join('') || '<span style="color:var(--text-dim);">empty</span>'}
                </div>
            </div>
        </div>
        
        <div style="display:flex; flex-direction:column; margin-top:10px;">
            <div style="font-size:12px; color:var(--text-dim); margin-bottom:5px;">Merged</div>
            <div style="display:flex; gap:5px;">
                ${state.merged.map((item) => `<div style="padding:5px 10px; border:1px solid var(--border); background:var(--surface); border-radius:4px; text-align:center; opacity:0.8;">
                    <div style="font-weight:bold;">${item.v}</div>
                    <div style="font-size:10px; color:var(--text-dim);">idx ${item.i}</div>
                </div>`).join('') || '<span style="color:var(--text-dim);">empty</span>'}
            </div>
        </div>
        
        <div style="margin-top:20px;">
            <div style="font-size:14px; margin-bottom:10px;">Counts Array (Result):</div>
            <div style="display:flex; gap:5px;">
                ${state.counts.map((c, i) => `<div style="display:flex; flex-direction:column; align-items:center; width:40px;">
                    <div style="width:100%; height:40px; display:flex; align-items:center; justify-content:center; border:2px solid #34d399; background:var(--surface); border-radius:4px; font-weight:bold;">
                        ${c}
                    </div>
                    <div style="font-size:11px; color:var(--text-dim); margin-top:4px;">idx ${i}</div>
                </div>`).join('')}
            </div>
        </div>
    </div>`;
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
