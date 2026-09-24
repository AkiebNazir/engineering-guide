/* ============================================================================
   Interactive labs — small visual experiments placed next to the theory they
   explain in the AI Roadmap. Each lab is a canvas (or plain HTML) plus a few
   controls, a row of live numbers, and one sentence that explains what the
   numbers mean right now.

   viz.js      toolkit + linear algebra, probability, optimisation labs
   viz-ml.js   classical ML and deep learning labs
   viz-llm.js  transformers, LLM training/serving and agent labs
   ========================================================================= */
'use strict';

const LABS = new Map();
const liveLabs = new Set();
const defineLab = (name, spec) => LABS.set(name, spec);

const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
const lerp = (a, b, t) => a + (b - a) * t;
const easeOut = t => 1 - Math.pow(1 - t, 3);
const TAU = Math.PI * 2;

function rng(seed = 7) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6D2B79F5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
const gauss = r => { let u = 0; while (!u) u = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(TAU * r()); };
const softmaxT = (xs, T = 1) => {
  const z = xs.map(x => x / T), m = Math.max(...z.filter(Number.isFinite));
  const e = z.map(x => Number.isFinite(x) ? Math.exp(x - m) : 0);
  const s = e.reduce((a, b) => a + b, 0) || 1;
  return e.map(x => x / s);
};
const fmtN = (v, d = 2) => {
  if (!Number.isFinite(v)) return v > 0 ? '∞' : '—';
  const a = Math.abs(v);
  return a !== 0 && (a >= 1e5 || a < 1e-3) ? v.toExponential(1) : v.toFixed(d);
};
const fmtBig = v => v >= 1e12 ? `${+(v / 1e12).toFixed(1)}T` : v >= 1e9 ? `${+(v / 1e9).toFixed(1)}B`
  : v >= 1e6 ? `${+(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `${+(v / 1e3).toFixed(1)}K` : `${Math.round(v)}`;
const reducedMotion = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
const erf = x => {
  const s = Math.sign(x); x = Math.abs(x);
  const t = 1 / (1 + 0.3275911 * x);
  const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x);
  return s * y;
};
const normCdf = (x, mu = 0, sd = 1) => 0.5 * (1 + erf((x - mu) / (sd * Math.SQRT2)));

/* -------------------------------------------------------------- palette -- */
function labPalette(el) {
  const cs = getComputedStyle(el);
  const hex = (n, fb) => { const v = cs.getPropertyValue(n).trim(); return /^#([0-9a-f]{3}|[0-9a-f]{6})$/i.test(v) ? v : fb; };
  const rgbOf = h => {
    h = h.replace('#', '');
    if (h.length === 3) h = [...h].map(c => c + c).join('');
    const n = parseInt(h, 16);
    return [n >> 16 & 255, n >> 8 & 255, n & 255];
  };
  const P = {
    bg: hex('--bg', '#0b0e14'), surface: hex('--surface', '#11151d'), surface2: hex('--surface-2', '#171c26'),
    border: hex('--border', '#242c3a'), soft: hex('--border-soft', '#191f2a'), strong: hex('--border-strong', '#36415a'),
    text: hex('--text', '#e9edf5'), dim: hex('--text-dim', '#9ba6b9'), faint: hex('--text-faint', '#7a8497'),
    accent: hex('--accent', '#e5ab4f'), ok: hex('--ok', '#4fbf8b'), err: hex('--err', '#f2626d'),
  };
  const [r, g, b] = rgbOf(P.bg);
  P.dark = 0.2126 * r + 0.7152 * g + 0.0722 * b < 128;
  P.series = P.dark
    ? ['#6cb6ff', '#f5b453', '#4fcf8e', '#f2727c', '#b996ff', '#4fc1b0', '#f28ac0', '#c7d05a']
    : ['#1f6fd1', '#b26b00', '#1e8a4c', '#c53030', '#6d3fc4', '#0f7c72', '#b02a74', '#6b7a00'];
  P.rgb = c => rgbOf(P[c] || c);
  P.alpha = (c, a) => `rgba(${P.rgb(c).join(',')},${a})`;
  P.mix = (c1, c2, t) => { const x = P.rgb(c1), y = P.rgb(c2); return `rgb(${x.map((v, i) => Math.round(lerp(v, y[i], clamp(t, 0, 1)))).join(',')})`; };
  P.mixRgb = (c1, c2, t) => { const x = P.rgb(c1), y = P.rgb(c2); return x.map((v, i) => Math.round(lerp(v, y[i], clamp(t, 0, 1)))); };
  return P;
}

/* re-draw every live lab when the theme or the reader's page theme flips */
new MutationObserver(() => liveLabs.forEach(L => (L.fig.isConnected ? L.redraw() : liveLabs.delete(L))))
  .observe(document.documentElement, { attributes: true, subtree: true, attributeFilter: ['data-theme', 'data-paper'] });

/* ---------------------------------------------------------- drawing kit -- */
const D = {
  font: (ctx, size = 12, weight = 500, mono = false) => {
    ctx.font = `${weight} ${size}px ${mono ? '"IBM Plex Mono", ui-monospace, monospace' : '"IBM Plex Sans", system-ui, sans-serif'}`;
  },
  text(ctx, s, x, y, { color = '#888', size = 12, align = 'left', base = 'middle', weight = 500, mono = false } = {}) {
    D.font(ctx, size, weight, mono);
    ctx.fillStyle = color; ctx.textAlign = align; ctx.textBaseline = base;
    ctx.fillText(s, x, y);
  },
  line(ctx, x1, y1, x2, y2, color, w = 1, dash) {
    ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round';
    if (dash) ctx.setLineDash(dash);
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.restore();
  },
  arrow(ctx, x1, y1, x2, y2, color, w = 2.4, head = 10) {
    const a = Math.atan2(y2 - y1, x2 - x1), len = Math.hypot(x2 - x1, y2 - y1);
    if (len < 1) return;
    const h = Math.min(head, len * .45);
    ctx.save(); ctx.strokeStyle = ctx.fillStyle = color; ctx.lineWidth = w; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2 - Math.cos(a) * h * .6, y2 - Math.sin(a) * h * .6); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(x2, y2);
    ctx.lineTo(x2 - h * Math.cos(a - .42), y2 - h * Math.sin(a - .42));
    ctx.lineTo(x2 - h * Math.cos(a + .42), y2 - h * Math.sin(a + .42));
    ctx.closePath(); ctx.fill(); ctx.restore();
  },
  dot(ctx, x, y, r, fill, stroke, sw = 2) {
    ctx.beginPath(); ctx.arc(x, y, r, 0, TAU);
    if (fill) { ctx.fillStyle = fill; ctx.fill(); }
    if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = sw; ctx.stroke(); }
  },
  rrect(ctx, x, y, w, h, r) {
    r = Math.min(r, Math.abs(w) / 2, Math.abs(h) / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
  },
  /* world <-> pixel mapping; `equal` keeps circles round */
  view(c, { x0, x1, y0, y1, pad = 24, padL, padB, equal = false }) {
    const pl = padL ?? pad, pb = padB ?? pad;
    let W = c.w - pl - pad, H = c.h - pad - pb, kx = W / (x1 - x0), ky = H / (y1 - y0), ox = pl, oy = pad;
    if (equal) { const k = Math.min(kx, ky); ox += (W - k * (x1 - x0)) / 2; oy += (H - k * (y1 - y0)) / 2; kx = ky = k; }
    return { sx: x => ox + (x - x0) * kx, sy: y => oy + (y1 - y) * ky, ix: px => x0 + (px - ox) / kx, iy: py => y1 - (py - oy) / ky, kx, ky, x0, x1, y0, y1 };
  },
  grid(ctx, v, P, step = 1, labels = false) {
    for (let x = Math.ceil(v.x0 / step) * step; x <= v.x1 + 1e-9; x += step) {
      D.line(ctx, v.sx(x), v.sy(v.y0), v.sx(x), v.sy(v.y1), Math.abs(x) < 1e-9 ? P.strong : P.soft, Math.abs(x) < 1e-9 ? 1.4 : 1);
      if (labels && Math.abs(x) > 1e-9) D.text(ctx, +x.toFixed(2), v.sx(x), v.sy(v.y0) + 11, { color: P.faint, size: 10, align: 'center', mono: true });
    }
    for (let y = Math.ceil(v.y0 / step) * step; y <= v.y1 + 1e-9; y += step) {
      D.line(ctx, v.sx(v.x0), v.sy(y), v.sx(v.x1), v.sy(y), Math.abs(y) < 1e-9 ? P.strong : P.soft, Math.abs(y) < 1e-9 ? 1.4 : 1);
    }
  },
  /* x/y axes for function plots */
  axes(ctx, v, P, { xTicks = [], yTicks = [], xLabel = '', yLabel = '', fmtX = t => t, fmtY = t => t } = {}) {
    D.line(ctx, v.sx(v.x0), v.sy(v.y0), v.sx(v.x1), v.sy(v.y0), P.strong, 1);
    D.line(ctx, v.sx(v.x0), v.sy(v.y0), v.sx(v.x0), v.sy(v.y1), P.strong, 1);
    xTicks.forEach(t => {
      D.line(ctx, v.sx(t), v.sy(v.y0), v.sx(t), v.sy(v.y1), P.soft, 1);
      D.text(ctx, String(fmtX(t)), v.sx(t), v.sy(v.y0) + 12, { color: P.faint, size: 10, align: 'center', mono: true });
    });
    yTicks.forEach(t => {
      D.line(ctx, v.sx(v.x0), v.sy(t), v.sx(v.x1), v.sy(t), P.soft, 1);
      D.text(ctx, String(fmtY(t)), v.sx(v.x0) - 6, v.sy(t), { color: P.faint, size: 10, align: 'right', mono: true });
    });
    if (xLabel) D.text(ctx, xLabel, v.sx(v.x1), v.sy(v.y0) - 9, { color: P.dim, size: 11, align: 'right' });
    if (yLabel) D.text(ctx, yLabel, v.sx(v.x0) + 6, v.sy(v.y1) + 6, { color: P.dim, size: 11 });
  },
  curve(ctx, v, f, color, w = 2.2, n = 240, dash) {
    ctx.save(); ctx.strokeStyle = color; ctx.lineWidth = w; ctx.lineJoin = 'round';
    if (dash) ctx.setLineDash(dash);
    ctx.beginPath();
    let pen = false;
    for (let i = 0; i <= n; i++) {
      const x = lerp(v.x0, v.x1, i / n), y = f(x);
      if (!Number.isFinite(y)) { pen = false; continue; }
      const py = clamp(v.sy(y), -1e4, 1e4);
      pen ? ctx.lineTo(v.sx(x), py) : ctx.moveTo(v.sx(x), py);
      pen = true;
    }
    ctx.stroke(); ctx.restore();
  },
};

/* ------------------------------------------------------------- lab API -- */
function createLab(name, opts = {}) {
  const spec = LABS.get(name);
  if (!spec) return null;
  const fig = document.createElement('figure');
  fig.className = 'lab';
  fig.dataset.lab = name;
  fig.innerHTML = `
    <figcaption class="lab-head">
      <span class="lab-badge"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 3h6M10 3v6l-5.6 9.7A1.5 1.5 0 005.7 21h12.6a1.5 1.5 0 001.3-2.3L14 9V3"/><path d="M7.5 15h9"/></svg>Try it</span>
      <span class="lab-title">${spec.title}</span>
    </figcaption>
    ${spec.hint ? `<p class="lab-hint">${spec.hint}</p>` : ''}
    <div class="lab-stage"></div>
    <div class="lab-readout" aria-live="polite"></div>
    <div class="lab-controls"><div class="lab-sliders"></div><div class="lab-actions"></div></div>
    <p class="lab-insight" hidden></p>`;
  queueMicrotask(() => {
    if (!fig.isConnected) return;
    const L = labApi(fig);
    liveLabs.add(L);
    try { spec.mount(L, opts); } catch (e) {
      console.error(`lab ${name}`, e);
      fig.querySelector('.lab-stage').innerHTML = `<p class="lab-error">This lab could not start: ${String(e.message || e)}</p>`;
    }
    L.redraw();
  });
  return fig;
}

function labApi(fig) {
  const $in = s => fig.querySelector(s);
  const stage = $in('.lab-stage'), sliders = $in('.lab-sliders'), actions = $in('.lab-actions');
  const readout = $in('.lab-readout'), insight = $in('.lab-insight');
  let pending = false;
  const L = {
    fig, stage, sliders, actions, visible: true, draw: null, P: labPalette(fig),
    redraw() {
      if (pending) return;
      pending = true;
      requestAnimationFrame(() => {
        pending = false;
        if (!fig.isConnected) return;
        L.P = labPalette(fig);
        L.draw?.(L.P);
      });
    },
    canvas(height, parent = stage) {
      const wrap = document.createElement('div');
      wrap.className = 'lab-canvas';
      const cv = document.createElement('canvas');
      wrap.append(cv);
      parent.append(wrap);
      const c = { cv, wrap, ctx: cv.getContext('2d'), w: 300, h: 200 };
      c.fit = () => {
        const w = Math.max(240, wrap.clientWidth || 600);
        const h = Math.round(typeof height === 'function' ? height(w) : height);
        const d = window.devicePixelRatio || 1;
        if (cv.width !== Math.round(w * d) || cv.height !== Math.round(h * d)) {
          cv.width = Math.round(w * d); cv.height = Math.round(h * d); cv.style.height = `${h}px`;
        }
        c.w = w; c.h = h;
        c.ctx.setTransform(d, 0, 0, d, 0, 0);
      };
      c.clear = () => { c.fit(); c.ctx.clearRect(0, 0, c.w, c.h); };
      c.fit();
      new ResizeObserver(() => { c.fit(); L.redraw(); }).observe(wrap);
      return c;
    },
    slider(label, { min, max, step = 1, value, fmt = v => v, log = false, dyn = false }, on) {
      const row = document.createElement('label');
      row.className = 'lab-slider';
      if (dyn) row.dataset.dyn = '1';
      row.innerHTML = `<span class="ls-label">${label}</span><output></output><input type="range">`;
      const input = row.querySelector('input'), out = row.querySelector('output');
      const lmin = Math.log(min), lmax = Math.log(max);
      const toV = s => log ? Math.exp(lmin + (lmax - lmin) * s / 1000) : +s;
      const toS = v => log ? 1000 * (Math.log(v) - lmin) / (lmax - lmin) : v;
      if (log) { input.min = 0; input.max = 1000; input.step = 1; } else { input.min = min; input.max = max; input.step = step; }
      const api = {
        input,
        get: () => toV(+input.value),
        set(v, silent) { input.value = toS(v); paint(); if (!silent) on?.(api.get()); },
      };
      const paint = () => {
        const p = (input.value - input.min) / (input.max - input.min) * 100;
        input.style.setProperty('--fill', `${p}%`);
        out.textContent = fmt(api.get());
      };
      input.value = toS(value);
      paint();
      input.addEventListener('input', () => { paint(); on?.(api.get()); });
      sliders.append(row);
      return api;
    },
    clearDyn() { sliders.querySelectorAll('[data-dyn]').forEach(n => n.remove()); },
    seg(label, options, value, on, parent = actions) {
      const row = document.createElement('div');
      row.className = 'lab-seg';
      row.innerHTML = `${label ? `<span class="ls-label">${label}</span>` : ''}<div class="seg">${
        options.map(([v, l]) => `<button type="button" data-v="${v}">${l}</button>`).join('')}</div>`;
      const api = {
        value,
        set(v, silent) {
          api.value = v;
          row.querySelectorAll('button').forEach(b => {
            const is = b.dataset.v === String(v);
            b.classList.toggle('is-on', is);
            b.setAttribute('aria-pressed', is);
          });
          if (!silent) on?.(v);
        },
      };
      row.addEventListener('click', e => {
        const b = e.target.closest('button');
        if (b) api.set(options.find(o => String(o[0]) === b.dataset.v)[0]);
      });
      api.set(value, true);
      parent.append(row);
      return api;
    },
    button(label, on, cls = '') {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = `lab-btn ${cls}`;
      b.innerHTML = label;
      b.onclick = on;
      actions.append(b);
      return b;
    },
    toggle(label, value, on) {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'lab-toggle';
      b.innerHTML = `<i aria-hidden="true"></i>${label}`;
      const api = { value, set(v, silent) { api.value = v; b.setAttribute('aria-pressed', v); if (!silent) on?.(v); } };
      b.onclick = () => api.set(!api.value);
      api.set(value, true);
      actions.append(b);
      return api;
    },
    stats(pairs) {
      readout.innerHTML = pairs.filter(Boolean).map(([k, v, cls = '', dot]) =>
        `<span class="stat-chip ${cls}">${dot ? `<i style="background:${dot}"></i>` : ''}<span>${k}</span><b>${v}</b></span>`).join('');
    },
    insight(html) { insight.innerHTML = html || ''; insight.hidden = !html; },
    loop(step) {
      let raf = 0, last = 0;
      const api = {
        running: false,
        onchange: null,
        start() {
          if (api.running) return;
          api.running = true;
          last = performance.now();
          const tick = now => {
            if (!api.running) return;
            if (!fig.isConnected) { api.running = false; return; }
            const dt = Math.min(0.05, (now - last) / 1000);
            last = now;
            if (L.visible && step(dt) === false) { api.stop(); return; }
            raf = requestAnimationFrame(tick);
          };
          raf = requestAnimationFrame(tick);
          api.onchange?.();
        },
        stop() { api.running = false; cancelAnimationFrame(raf); api.onchange?.(); },
        toggle() { api.running ? api.stop() : api.start(); },
      };
      return api;
    },
    playButton(loop, labels = ['Play', 'Pause'], onStart) {
      const b = L.button(`<span class="pb-ico"></span>${labels[0]}`, () => {
        if (!loop.running) onStart?.();
        loop.toggle();
      }, 'primary');
      loop.onchange = () => {
        b.innerHTML = `<span class="pb-ico ${loop.running ? 'is-pause' : ''}"></span>${loop.running ? labels[1] : labels[0]}`;
      };
      return b;
    },
    tween(ms, step, done) {
      if (reducedMotion()) { step(1); done?.(); return; }
      const t0 = performance.now();
      const tick = now => {
        if (!fig.isConnected) return;
        const t = Math.min(1, (now - t0) / ms);
        step(easeOut(t));
        t < 1 ? requestAnimationFrame(tick) : done?.();
      };
      requestAnimationFrame(tick);
    },
    drag(c, { hit, move, down, up, hover }) {
      let target = null;
      const pos = e => { const r = c.cv.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
      c.cv.style.touchAction = 'none';
      c.cv.addEventListener('pointerdown', e => {
        const [x, y] = pos(e);
        const h = hit ? hit(x, y) : null;
        if (h != null) {
          target = h;
          e.preventDefault();
          c.cv.setPointerCapture(e.pointerId);
          c.cv.style.cursor = 'grabbing';
          move?.(target, x, y);
        } else if (down) {
          e.preventDefault();
          down(x, y, e);
        }
      });
      c.cv.addEventListener('pointermove', e => {
        const [x, y] = pos(e);
        if (target != null) { move(target, x, y); return; }
        hover?.(x, y);
        c.cv.style.cursor = hit && hit(x, y) != null ? 'grab' : down ? 'crosshair' : '';
      });
      const end = () => { if (target != null) up?.(target); target = null; c.cv.style.cursor = ''; };
      c.cv.addEventListener('pointerup', end);
      c.cv.addEventListener('pointercancel', end);
      c.cv.addEventListener('pointerleave', () => { if (target == null) hover?.(null, null); });
    },
  };
  new IntersectionObserver(([en]) => { L.visible = en.isIntersecting; }).observe(fig);
  return L;
}

/* ======================================================= linear algebra == */
defineLab('vectors', {
  title: 'Dot product and cosine similarity',
  hint: 'Drag the tips of <b>a</b> and <b>b</b>. The thick band on <b>a</b> is the shadow (projection) of <b>b</b>.',
  mount(L) {
    const c = L.canvas(w => Math.min(360, w * .6));
    const s = { a: [3, 1], b: [1.5, 2.5] };
    let v = null;
    const snap = x => Math.round(x * 4) / 4;
    L.drag(c, {
      hit: (x, y) => v ? (['b', 'a'].find(k => Math.hypot(v.sx(s[k][0]) - x, v.sy(s[k][1]) - y) < 18) ?? null) : null,
      move: (k, x, y) => { s[k] = [clamp(snap(v.ix(x)), -5.5, 5.5), clamp(snap(v.iy(y)), -3.75, 3.75)]; L.redraw(); update(); },
    });
    const go = (a, b) => {
      const a0 = [...s.a], b0 = [...s.b];
      L.tween(500, t => {
        s.a = [lerp(a0[0], a[0], t), lerp(a0[1], a[1], t)];
        s.b = [lerp(b0[0], b[0], t), lerp(b0[1], b[1], t)];
        L.redraw(); update();
      });
    };
    L.button('Same taste, 2× as active', () => go([2, 1], [4, 2]));
    L.button('Nothing in common', () => go([3, 0], [0, 2.5]));
    L.button('Opposite', () => go([2.5, 1.5], [-2, -1.2]));

    function update() {
      const [ax, ay] = s.a, [bx, by] = s.b;
      const dot = ax * bx + ay * by, na = Math.hypot(ax, ay), nb = Math.hypot(bx, by);
      const cos = na && nb ? dot / (na * nb) : 0, deg = Math.acos(clamp(cos, -1, 1)) * 180 / Math.PI;
      const dist = Math.hypot(ax - bx, ay - by);
      L.stats([['a · b', fmtN(dot)], ['‖a‖', fmtN(na)], ['‖b‖', fmtN(nb)], ['cos θ', fmtN(cos, 3), 'accent'], ['θ', `${deg.toFixed(0)}°`], ['‖a − b‖', fmtN(dist)]]);
      const ratio = Math.max(na, nb) / Math.max(1e-9, Math.min(na, nb));
      L.insight(cos > .985
        ? `<b>Same direction.</b> cos θ ≈ 1 although one arrow is ${fmtN(ratio, 1)}× longer. Cosine similarity ignores length; Euclidean distance (${fmtN(dist)}) does not. That is why embeddings are compared with cosine.`
        : Math.abs(cos) < .06 ? '<b>Orthogonal.</b> The dot product is 0 and the shadow disappears: knowing one vector tells you nothing about the other.'
        : cos < -.4 ? '<b>Opposite directions.</b> The dot product is negative. In a recommender these two users disagree.'
        : `<b>Partial overlap.</b> About ${Math.round(Math.max(0, cos) * 100)}% of b points along a. That overlap is exactly the shadow on a.`);
    }

    L.draw = P => {
      c.clear();
      const { ctx } = c;
      v = D.view(c, { x0: -6, x1: 6, y0: -4, y1: 4, pad: 12, equal: true });
      D.grid(ctx, v, P, 1);
      const [ax, ay] = s.a, [bx, by] = s.b;
      const k = (ax * bx + ay * by) / Math.max(1e-9, ax * ax + ay * ay);
      const px = k * ax, py = k * ay;
      D.line(ctx, v.sx(0), v.sy(0), v.sx(px), v.sy(py), P.alpha('accent', .3), 10);
      D.line(ctx, v.sx(bx), v.sy(by), v.sx(px), v.sy(py), P.faint, 1.3, [5, 5]);
      const a1 = Math.atan2(-ay, ax), a2 = Math.atan2(-by, bx);
      let diff = a2 - a1;
      while (diff > Math.PI) diff -= TAU;
      while (diff < -Math.PI) diff += TAU;
      ctx.beginPath(); ctx.arc(v.sx(0), v.sy(0), 30, a1, a1 + diff, diff < 0);
      ctx.strokeStyle = P.dim; ctx.lineWidth = 1.5; ctx.stroke();
      D.arrow(ctx, v.sx(0), v.sy(0), v.sx(ax), v.sy(ay), P.accent, 3.2, 13);
      D.arrow(ctx, v.sx(0), v.sy(0), v.sx(bx), v.sy(by), P.series[0], 3.2, 13);
      D.dot(ctx, v.sx(ax), v.sy(ay), 7, P.surface, P.accent, 2.5);
      D.dot(ctx, v.sx(bx), v.sy(by), 7, P.surface, P.series[0], 2.5);
      D.text(ctx, 'a', v.sx(ax) + 12, v.sy(ay) - 12, { color: P.accent, size: 15, weight: 700 });
      D.text(ctx, 'b', v.sx(bx) + 12, v.sy(by) - 12, { color: P.series[0], size: 15, weight: 700 });
      D.text(ctx, 'θ', v.sx(0) + 38 * Math.cos(a1 + diff / 2), v.sy(0) + 38 * Math.sin(a1 + diff / 2), { color: P.dim, size: 13, align: 'center' });
    };
    update();
  },
});

defineLab('matrix', {
  title: 'A matrix is a transformation of space',
  hint: 'The columns of the matrix are where <b>î</b> and <b>ĵ</b> land. Everything else follows. Drag the grey vector <b>v</b> to see where it goes.',
  mount(L, opts) {
    const c = L.canvas(w => Math.min(380, w * .64));
    const M = { a: 1, b: 0, c: 0, d: 1 };
    const s = { v: [1.5, 1], eigen: !!opts.eigen };
    let view = null;
    const sl = {
      a: L.slider('a  (î → x)', { min: -2, max: 2, step: .05, value: 1, fmt: x => x.toFixed(2) }, x => { M.a = x; changed(); }),
      c: L.slider('c  (î → y)', { min: -2, max: 2, step: .05, value: 0, fmt: x => x.toFixed(2) }, x => { M.c = x; changed(); }),
      b: L.slider('b  (ĵ → x)', { min: -2, max: 2, step: .05, value: 0, fmt: x => x.toFixed(2) }, x => { M.b = x; changed(); }),
      d: L.slider('d  (ĵ → y)', { min: -2, max: 2, step: .05, value: 1, fmt: x => x.toFixed(2) }, x => { M.d = x; changed(); }),
    };
    const presets = [
      ['Identity', [1, 0, 0, 1]], ['Stretch', [2, 0, 0, .5]], ['Rotate 45°', [.71, -.71, .71, .71]],
      ['Shear', [1, 1, 0, 1]], ['Reflect', [-1, 0, 0, 1]], ['Squash to a line', [1, .5, 2, 1]], ['Symmetric', [2, 1, 1, 2]],
    ];
    presets.forEach(([label, [a, b, cc, d]]) => L.button(label, () => {
      const from = { ...M };
      L.tween(650, t => {
        M.a = lerp(from.a, a, t); M.b = lerp(from.b, b, t); M.c = lerp(from.c, cc, t); M.d = lerp(from.d, d, t);
        Object.keys(sl).forEach(k => sl[k].set(M[k], true));
        changed();
      });
    }));
    L.toggle('Eigenvectors', s.eigen, x => { s.eigen = x; changed(); });
    L.drag(c, {
      hit: (x, y) => view && Math.hypot(view.sx(s.v[0]) - x, view.sy(s.v[1]) - y) < 16 ? 'v' : null,
      move: (_, x, y) => { s.v = [clamp(Math.round(view.ix(x) * 4) / 4, -3, 3), clamp(Math.round(view.iy(y) * 4) / 4, -3, 3)]; changed(); },
    });
    const eig = () => {
      const tr = M.a + M.d, det = M.a * M.d - M.b * M.c, disc = tr * tr - 4 * det;
      if (disc < -1e-9) return { det, complex: true };
      const r = Math.sqrt(Math.max(0, disc));
      return {
        det,
        pairs: [(tr + r) / 2, (tr - r) / 2].map(l => {
          let x, y;
          if (Math.abs(M.b) > 1e-6) { x = M.b; y = l - M.a; } else if (Math.abs(M.c) > 1e-6) { x = l - M.d; y = M.c; } else { x = Math.abs(l - M.a) < 1e-9 ? 1 : 0; y = x ? 0 : 1; }
          const n = Math.hypot(x, y) || 1;
          return { l, x: x / n, y: y / n };
        }),
      };
    };
    function changed() {
      L.redraw();
      const e = eig();
      L.stats([
        ['M', `[${M.a.toFixed(2)} ${M.b.toFixed(2)}; ${M.c.toFixed(2)} ${M.d.toFixed(2)}]`],
        ['det', fmtN(e.det), 'accent'],
        ['eigenvalues', e.complex ? 'complex' : e.pairs.map(p => fmtN(p.l)).join(', ')],
        ['v → Mv', `(${fmtN(M.a * s.v[0] + M.b * s.v[1], 1)}, ${fmtN(M.c * s.v[0] + M.d * s.v[1], 1)})`],
      ]);
      L.insight(Math.abs(e.det) < .06
        ? '<b>det ≈ 0: the plane is squashed onto a line.</b> Area becomes zero, many inputs land on the same output, and the matrix has no inverse.'
        : e.det < 0 ? `<b>det = ${fmtN(e.det)}: orientation flips.</b> The unit square is mirrored and its area scales by ${fmtN(Math.abs(e.det))}×.`
        : e.complex ? '<b>No real eigenvectors.</b> Every direction gets rotated, so no arrow keeps pointing the same way.'
        : s.eigen ? `<b>Eigenvectors don't turn.</b> Vectors on the dashed lines only stretch, by λ = ${e.pairs.map(p => fmtN(p.l)).join(' and ')}. Area scales by det = ${fmtN(e.det)}.`
        : `<b>Area scales by det = ${fmtN(e.det)}.</b> The shaded unit square shows it.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      const v = view = D.view(c, { x0: -4.5, x1: 4.5, y0: -3.2, y1: 3.2, pad: 10, equal: true });
      D.grid(ctx, v, P, 1);
      ctx.save();
      ctx.beginPath(); ctx.rect(0, 0, c.w, c.h); ctx.clip();
      const T = (x, y) => [v.sx(M.a * x + M.b * y), v.sy(M.c * x + M.d * y)];
      for (let i = -8; i <= 8; i++) {
        const col = i === 0 ? P.alpha('accent', .55) : P.alpha('accent', .2);
        D.line(ctx, ...T(i, -8), ...T(i, 8), col, i === 0 ? 1.6 : 1);
        D.line(ctx, ...T(-8, i), ...T(8, i), col, i === 0 ? 1.6 : 1);
      }
      ctx.beginPath();
      [[0, 0], [1, 0], [1, 1], [0, 1]].forEach(([x, y], i) => { const [px, py] = T(x, y); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
      ctx.closePath(); ctx.fillStyle = P.alpha('accent', .22); ctx.fill();
      if (s.eigen) {
        const e = eig();
        if (!e.complex) e.pairs.forEach((p, i) => {
          D.line(ctx, v.sx(-9 * p.x), v.sy(-9 * p.y), v.sx(9 * p.x), v.sy(9 * p.y), P.series[4], 2, [7, 6]);
          D.text(ctx, `λ${i + 1}=${fmtN(p.l, 1)}`, v.sx(2.6 * p.x) + 8, v.sy(2.6 * p.y) - 10 - i * 4, { color: P.series[4], size: 12, weight: 650 });
        });
      }
      ctx.restore();
      D.arrow(ctx, v.sx(0), v.sy(0), ...T(1, 0), P.series[3], 3, 12);
      D.arrow(ctx, v.sx(0), v.sy(0), ...T(0, 1), P.series[0], 3, 12);
      D.text(ctx, 'î', T(1, 0)[0] + 9, T(1, 0)[1] - 9, { color: P.series[3], size: 15, weight: 700 });
      D.text(ctx, 'ĵ', T(0, 1)[0] + 9, T(0, 1)[1] - 9, { color: P.series[0], size: 15, weight: 700 });
      D.arrow(ctx, v.sx(0), v.sy(0), v.sx(s.v[0]), v.sy(s.v[1]), P.faint, 2, 10);
      D.dot(ctx, v.sx(s.v[0]), v.sy(s.v[1]), 6, P.surface, P.faint, 2);
      const [mx, my] = T(...s.v);
      D.line(ctx, v.sx(s.v[0]), v.sy(s.v[1]), mx, my, P.faint, 1, [3, 4]);
      D.arrow(ctx, v.sx(0), v.sy(0), mx, my, P.series[1], 3, 12);
      D.text(ctx, 'v', v.sx(s.v[0]) + 10, v.sy(s.v[1]) + 12, { color: P.dim, size: 13, weight: 650 });
      D.text(ctx, 'Mv', mx + 10, my - 10, { color: P.series[1], size: 13, weight: 700 });
    };
    changed();
  },
});

defineLab('svd', {
  title: 'Keep the top k singular values',
  hint: 'An image is a matrix. SVD splits it into layers ordered by importance. Rebuild it from only the first <b>k</b>.',
  mount(L) {
    const N = 40;
    const A = new Float64Array(N * N);
    for (let r = 0; r < N; r++) for (let q = 0; q < N; q++) {
      let x = .12 + .22 * q / N;
      const dr = Math.hypot(r - 14, q - 13);
      if (Math.abs(dr - 8.5) < 2) x = .95;
      if (r > 22 && r < 35 && q > 21 && q < 35) x = .75 + (((r >> 2) + (q >> 2)) % 2) * .15;
      if (Math.abs(r - (N - 1 - q)) < 1.2 && q < 18) x = .85;
      A[r * N + q] = x;
    }
    const ATA = new Float64Array(N * N);
    for (let i = 0; i < N; i++) for (let j = i; j < N; j++) {
      let sum = 0;
      for (let r = 0; r < N; r++) sum += A[r * N + i] * A[r * N + j];
      ATA[i * N + j] = ATA[j * N + i] = sum;
    }
    const { vals, V } = symEig(ATA, N);
    const order = vals.map((l, i) => [l, i]).sort((x, y) => y[0] - x[0]);
    const S = order.map(([l]) => Math.sqrt(Math.max(0, l)));
    const Vc = order.map(([, i]) => Array.from({ length: N }, (_, r) => V[r * N + i]));
    const Uc = Vc.map((vec, k) => Array.from({ length: N }, (_, r) => {
      let sum = 0;
      for (let q = 0; q < N; q++) sum += A[r * N + q] * vec[q];
      return S[k] > 1e-9 ? sum / S[k] : 0;
    }));
    const total = S.reduce((a, x) => a + x * x, 0);
    let k = 3;
    const recon = () => {
      const R = new Float64Array(N * N);
      for (let i = 0; i < k; i++) for (let r = 0; r < N; r++) {
        const u = S[i] * Uc[i][r];
        for (let q = 0; q < N; q++) R[r * N + q] += u * Vc[i][q];
      }
      return R;
    };
    let R = recon();
    const c = L.canvas(w => Math.min(300, w * .44));
    L.slider('k (layers kept)', { min: 1, max: 24, step: 1, value: k }, x => { k = x; R = recon(); update(); L.redraw(); });
    [1, 3, 8, 20].forEach(x => L.button(`k = ${x}`, () => { k = x; R = recon(); update(); L.redraw(); }));
    const off = document.createElement('canvas');
    off.width = off.height = N;
    const octx = off.getContext('2d');
    function paintImage(ctx, M, x, y, size, P) {
      const img = octx.createImageData(N, N);
      const lo = P.rgb('bg'), hi = P.rgb('text');
      for (let i = 0; i < N * N; i++) {
        const t = clamp(M[i], 0, 1);
        img.data[i * 4] = lerp(lo[0], hi[0], t); img.data[i * 4 + 1] = lerp(lo[1], hi[1], t);
        img.data[i * 4 + 2] = lerp(lo[2], hi[2], t); img.data[i * 4 + 3] = 255;
      }
      octx.putImageData(img, 0, 0);
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(off, x, y, size, size);
    }
    function update() {
      const kept = S.slice(0, k).reduce((a, x) => a + x * x, 0) / total;
      const stored = k * (2 * N + 1);
      L.stats([['energy kept', `${(kept * 100).toFixed(1)}%`, 'accent'], ['numbers stored', `${stored} of ${N * N}`], ['compression', `${fmtN(N * N / stored, 1)}×`]]);
      L.insight(k <= 2 ? `<b>k = ${k}</b>: only the broadest structure survives, the background gradient and a smudge.`
        : stored < N * N ? `<b>k = ${k}</b> keeps ${(kept * 100).toFixed(1)}% of the energy with ${Math.round(stored / (N * N) * 100)}% of the numbers. The later layers mostly carry fine detail and noise. LoRA and PCA exploit the same fact.`
        : `<b>k = ${k}</b> stores more numbers than the original. Low rank only pays off when k is small.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      const size = Math.min(c.h - 36, (c.w - 60) / 3.1);
      const y = 24;
      paintImage(ctx, A, 12, y, size, P);
      paintImage(ctx, R, 24 + size, y, size, P);
      D.text(ctx, 'original', 12, 12, { color: P.dim, size: 11 });
      D.text(ctx, `rank ${k}`, 24 + size, 12, { color: P.accent, size: 11, weight: 650 });
      const bx = 44 + 2 * size, bw = c.w - bx - 12, n = 24, gap = 2, barW = (bw - gap * n) / n;
      D.text(ctx, 'singular values σ', bx, 12, { color: P.dim, size: 11 });
      for (let i = 0; i < n; i++) {
        const hgt = (S[i] / S[0]) * (size - 4);
        ctx.fillStyle = i < k ? P.accent : P.alpha('dim', .35);
        D.rrect(ctx, bx + i * (barW + gap), y + size - hgt, barW, hgt, 2); ctx.fill();
      }
    };
    update();
  },
});

function symEig(M, n) {
  const a = Float64Array.from(M), V = new Float64Array(n * n);
  for (let i = 0; i < n; i++) V[i * n + i] = 1;
  for (let sweep = 0; sweep < 24; sweep++) {
    let off = 0;
    for (let p = 0; p < n; p++) for (let q = p + 1; q < n; q++) off += a[p * n + q] ** 2;
    if (off < 1e-12) break;
    for (let p = 0; p < n; p++) for (let q = p + 1; q < n; q++) {
      const apq = a[p * n + q];
      if (Math.abs(apq) < 1e-14) continue;
      const phi = .5 * Math.atan2(2 * apq, a[q * n + q] - a[p * n + p]);
      const cs = Math.cos(phi), sn = Math.sin(phi);
      for (let k = 0; k < n; k++) { const x = a[k * n + p], y = a[k * n + q]; a[k * n + p] = cs * x - sn * y; a[k * n + q] = sn * x + cs * y; }
      for (let k = 0; k < n; k++) { const x = a[p * n + k], y = a[q * n + k]; a[p * n + k] = cs * x - sn * y; a[q * n + k] = sn * x + cs * y; }
      for (let k = 0; k < n; k++) { const x = V[k * n + p], y = V[k * n + q]; V[k * n + p] = cs * x - sn * y; V[k * n + q] = sn * x + cs * y; }
    }
  }
  return { vals: Array.from({ length: n }, (_, i) => a[i * n + i]), V };
}

defineLab('norms', {
  title: 'What “length” means: L1, L2 and L∞',
  hint: 'The shape is every vector of length 1 under that norm. Drag the point to compare distances.',
  mount(L, opts) {
    const c = L.canvas(w => Math.min(360, w * .6));
    const s = { p: opts.reg ? 1 : 2, q: [1.4, .9], reg: !!opts.reg };
    let v = null;
    L.seg('p', [[.5, '½'], [1, '1'], [2, '2'], [4, '4'], ['inf', '∞']], s.p, x => { s.p = x; changed(); });
    L.toggle('Loss contours (regularization)', s.reg, x => { s.reg = x; changed(); });
    const norm = (x, y, p) => p === 'inf' ? Math.max(Math.abs(x), Math.abs(y)) : Math.pow(Math.abs(x) ** p + Math.abs(y) ** p, 1 / p);
    const C = [1.9, 1.25], ROT = .55, SA = 2.2, SB = .45;
    const loss = (x, y) => {
      const dx = x - C[0], dy = y - C[1];
      const u = dx * Math.cos(ROT) + dy * Math.sin(ROT), w = -dx * Math.sin(ROT) + dy * Math.cos(ROT);
      return u * u / SA + w * w / SB;
    };
    const best = () => {
      let b = null;
      for (let i = 0; i < 2880; i++) {
        const t = i / 2880 * TAU, n = norm(Math.cos(t), Math.sin(t), s.p);
        const x = Math.cos(t) / n, y = Math.sin(t) / n, f = loss(x, y);
        if (!b || f < b.f) b = { x, y, f };
      }
      return b;
    };
    L.drag(c, {
      hit: (x, y) => v && Math.hypot(v.sx(s.q[0]) - x, v.sy(s.q[1]) - y) < 16 ? 'q' : null,
      move: (_, x, y) => { s.q = [clamp(v.ix(x), -2.4, 2.4), clamp(v.iy(y), -2.2, 2.2)]; changed(); },
    });
    function changed() {
      L.redraw();
      const [x, y] = s.q;
      const b = s.reg ? best() : null;
      L.stats([
        ['‖q‖₁', fmtN(norm(x, y, 1)), '', L.P.series[0]], ['‖q‖₂', fmtN(norm(x, y, 2)), 'accent'],
        ['‖q‖∞', fmtN(norm(x, y, 'inf')), '', L.P.series[1]],
        b && ['best weights', `(${fmtN(b.x)}, ${fmtN(b.y)})`],
      ]);
      if (s.reg) {
        const sparse = Math.min(Math.abs(b.x), Math.abs(b.y)) < .02;
        L.insight(sparse
          ? `<b>The loss touches a corner.</b> One weight is exactly 0 (${fmtN(b.x)}, ${fmtN(b.y)}). This is why L1 regularization (Lasso) produces sparse models.`
          : s.p === 2 ? '<b>The L2 ball is round, so there are no corners to land on.</b> Both weights shrink but neither reaches 0. That is Ridge regression.'
          : `<b>The best weights under a budget of 1</b> sit where the smallest loss ellipse first touches the ball: (${fmtN(b.x)}, ${fmtN(b.y)}).`);
      } else {
        L.insight(s.p === 1 ? '<b>L1 (Manhattan):</b> add the absolute steps along each axis, like walking city blocks. The blue staircase is its length.'
          : s.p === 'inf' ? '<b>L∞:</b> only the biggest coordinate counts, so the unit ball is a square.'
          : s.p < 1 ? '<b>p < 1 is not a true norm.</b> The ball caves in, is not convex, and the triangle inequality breaks.'
          : `<b>L${s.p}:</b> the orange straight line. As p grows the ball bulges from a diamond towards a square.`);
      }
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      v = D.view(c, { x0: -2.8, x1: 3.2, y0: -2.2, y1: 2.4, pad: 12, equal: true });
      D.grid(ctx, v, P, .5);
      if (s.reg) {
        const b = best();
        [b.f, b.f * 2.2, b.f * 4.5, b.f * 8].forEach((lv, i) => {
          ctx.beginPath();
          for (let t = 0; t <= 96; t++) {
            const a = t / 96 * TAU, u = Math.sqrt(lv * SA) * Math.cos(a), w = Math.sqrt(lv * SB) * Math.sin(a);
            const x = C[0] + u * Math.cos(ROT) - w * Math.sin(ROT), y = C[1] + u * Math.sin(ROT) + w * Math.cos(ROT);
            t ? ctx.lineTo(v.sx(x), v.sy(y)) : ctx.moveTo(v.sx(x), v.sy(y));
          }
          ctx.strokeStyle = i ? P.alpha('series' in P ? P.series[4] : P.dim, .35) : P.series[4];
          ctx.lineWidth = i ? 1.2 : 2; ctx.stroke();
        });
        D.text(ctx, '★', v.sx(C[0]), v.sy(C[1]), { color: P.series[4], size: 14, align: 'center' });
      }
      ctx.beginPath();
      for (let i = 0; i <= 720; i++) {
        const t = i / 720 * TAU, n = norm(Math.cos(t), Math.sin(t), s.p);
        const x = Math.cos(t) / n, y = Math.sin(t) / n;
        i ? ctx.lineTo(v.sx(x), v.sy(y)) : ctx.moveTo(v.sx(x), v.sy(y));
      }
      ctx.closePath(); ctx.fillStyle = P.alpha('accent', .18); ctx.fill();
      ctx.strokeStyle = P.accent; ctx.lineWidth = 2.2; ctx.stroke();
      if (s.reg) {
        const b = best();
        D.dot(ctx, v.sx(b.x), v.sy(b.y), 6, P.series[4], P.surface, 2);
        D.text(ctx, 'best under budget', v.sx(b.x) + 10, v.sy(b.y) + 14, { color: P.series[4], size: 11, weight: 600 });
      } else {
        const [x, y] = s.q;
        D.line(ctx, v.sx(0), v.sy(0), v.sx(x), v.sy(0), P.series[0], 2.4, [6, 4]);
        D.line(ctx, v.sx(x), v.sy(0), v.sx(x), v.sy(y), P.series[0], 2.4, [6, 4]);
        const m = Math.max(Math.abs(x), Math.abs(y));
        ctx.strokeStyle = P.alpha(P.series[1], .7); ctx.lineWidth = 1.4; ctx.setLineDash([3, 4]);
        ctx.strokeRect(v.sx(-m), v.sy(m), v.sx(m) - v.sx(-m), v.sy(-m) - v.sy(m)); ctx.setLineDash([]);
        D.arrow(ctx, v.sx(0), v.sy(0), v.sx(x), v.sy(y), P.accent, 2.8, 11);
        D.dot(ctx, v.sx(x), v.sy(y), 7, P.surface, P.text, 2.5);
        D.text(ctx, 'q', v.sx(x) + 12, v.sy(y) - 10, { color: P.text, size: 14, weight: 700 });
      }
    };
    changed();
  },
});

/* ============================================================ calculus == */
defineLab('backprop', {
  title: 'Backpropagation, one node at a time',
  hint: 'Run the forward pass, then the backward pass. Each red number is ∂L/∂(that node), built by multiplying local slopes right to left.',
  mount(L) {
    const s = { x: 1.5, w: .8, b: -.5, y: 1, lr: .8, phase: 'idle', t: 0, shown: 0, grads: 0, hist: [] };
    const c = L.canvas(w => Math.min(320, Math.max(270, w * .45)));
    const sig = z => 1 / (1 + Math.exp(-z));
    const calc = () => {
      const m = s.w * s.x, z = m + s.b, a = sig(z), Lo = (a - s.y) ** 2;
      const dLda = 2 * (a - s.y), dadz = a * (1 - a), dLdz = dLda * dadz;
      return { m, z, a, L: Lo, dLda, dadz, dLdz, dLdm: dLdz, dLdb: dLdz, dLdw: dLdz * s.x, dLdx: dLdz * s.w };
    };
    const nodes = {
      x: [.08, .18, 'x'], w: [.08, .5, 'w'], b: [.08, .84, 'b'], m: [.31, .34, 'w·x'],
      z: [.52, .56, 'z = w·x + b'], a: [.72, .56, 'a = σ(z)'], L: [.92, .56, 'L = (a − y)²'], y: [.72, .88, 'y (target)'],
    };
    const stages = [[['x', 'm'], ['w', 'm']], [['m', 'z'], ['b', 'z']], [['z', 'a']], [['a', 'L'], ['y', 'L']]];
    const sx = L.slider('input x', { min: -3, max: 3, step: .1, value: s.x, fmt: v => v.toFixed(1) }, v => { s.x = v; reset(); });
    const sw = L.slider('weight w', { min: -3, max: 3, step: .05, value: s.w, fmt: v => v.toFixed(2) }, v => { s.w = v; reset(); });
    const sb = L.slider('bias b', { min: -3, max: 3, step: .05, value: s.b, fmt: v => v.toFixed(2) }, v => { s.b = v; reset(); });
    L.slider('target y', { min: 0, max: 1, step: .05, value: s.y, fmt: v => v.toFixed(2) }, v => { s.y = v; reset(); });
    L.slider('learning rate', { min: .05, max: 3, step: .05, value: s.lr, fmt: v => v.toFixed(2) }, v => { s.lr = v; });
    const anim = L.loop(dt => {
      s.t += dt * 1.6;
      if (s.phase === 'fwd') s.shown = Math.min(4, s.t);
      if (s.phase === 'bwd') s.grads = Math.min(4, s.t);
      L.redraw();
      if (s.t >= 4) { s.phase = 'idle'; explain(); return false; }
    });
    L.button('1 · Forward pass', () => { s.phase = 'fwd'; s.t = 0; s.shown = 0; s.grads = 0; anim.start(); }, 'primary');
    L.button('2 · Backward pass', () => { if (s.shown < 4) s.shown = 4; s.phase = 'bwd'; s.t = 0; s.grads = 0; anim.start(); }, 'primary');
    L.button('3 · Gradient step', () => {
      const g = calc();
      s.hist.push(g.L);
      s.w -= s.lr * g.dLdw; s.b -= s.lr * g.dLdb;
      sw.set(clamp(s.w, -3, 3), true); sb.set(clamp(s.b, -3, 3), true);
      s.shown = 4; s.grads = 0; explain(); L.redraw();
    });
    L.button('Train 25 steps', () => {
      for (let i = 0; i < 25; i++) { const g = calc(); s.hist.push(g.L); s.w -= s.lr * g.dLdw; s.b -= s.lr * g.dLdb; }
      sw.set(clamp(s.w, -3, 3), true); sb.set(clamp(s.b, -3, 3), true);
      s.shown = 4; s.grads = 4; explain(); L.redraw();
    });
    function reset() { s.shown = 0; s.grads = 0; s.hist = []; explain(); L.redraw(); }
    function explain() {
      const g = calc();
      L.stats([['loss L', fmtN(g.L, 4), 'accent'], ['∂L/∂w', fmtN(g.dLdw, 4), 'err'], ['∂L/∂b', fmtN(g.dLdb, 4), 'err'], s.hist.length && ['steps taken', s.hist.length]]);
      L.insight(s.grads >= 4
        ? `<b>Chain rule:</b> ∂L/∂w = ∂L/∂a · ∂a/∂z · ∂z/∂w = <code>${fmtN(g.dLda, 3)} × ${fmtN(g.dadz, 3)} × ${fmtN(s.x, 2)} = ${fmtN(g.dLdw, 4)}</code>. A gradient step moves w by −lr × that: the sign says which way lowers the loss.`
        : s.shown >= 4 ? '<b>Forward pass done.</b> Every node now holds its value. Run the backward pass to see how much each one is to blame for the loss.'
        : s.hist.length ? `<b>Loss went from ${fmtN(s.hist[0], 4)} to ${fmtN(g.L, 4)}.</b> Each step follows the negative gradient.`
        : '<b>Start with the forward pass.</b> Values flow left to right: w·x, add b, squash with σ, compare with y.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, g = calc();
      const pos = k => [nodes[k][0] * c.w, nodes[k][1] * c.h];
      const stageOf = (from, to) => stages.findIndex(st => st.some(([f, t]) => f === from && t === to));
      stages.flat().forEach(([f, t]) => {
        const [x1, y1] = pos(f), [x2, y2] = pos(t), si = stageOf(f, t);
        const lit = s.shown > si;
        D.line(ctx, x1, y1, x2, y2, lit ? P.alpha('accent', .7) : P.strong, lit ? 2.2 : 1.4);
        if (s.phase === 'fwd' && Math.floor(s.t) === si) {
          const k = s.t - si;
          D.dot(ctx, lerp(x1, x2, k), lerp(y1, y2, k), 5, P.accent);
        }
        const bsi = 3 - si;
        if (s.phase === 'bwd' && Math.floor(s.t) === bsi) {
          const k = s.t - bsi;
          D.dot(ctx, lerp(x2, x1, k), lerp(y2, y1, k), 5, P.err);
        }
      });
      const val = { x: s.x, w: s.w, b: s.b, y: s.y, m: g.m, z: g.z, a: g.a, L: g.L };
      const grad = { w: g.dLdw, b: g.dLdb, x: g.dLdx, m: g.dLdm, z: g.dLdz, a: g.dLda, L: 1 };
      const reveal = { x: 0, w: 0, b: 0, y: 0, m: 1, z: 2, a: 3, L: 4 };
      const gradAt = { L: 0, a: 1, y: 9, z: 2, m: 3, b: 3, x: 4, w: 4 };
      Object.entries(nodes).forEach(([k, [, , label]]) => {
        const [x, y] = pos(k), w = Math.min(118, c.w * .15), h = 46;
        const showV = reveal[k] === 0 || s.shown >= reveal[k];
        const showG = grad[k] !== undefined && s.grads >= gradAt[k] + (s.phase === 'bwd' ? .999 : 0) || (s.grads >= 4 && grad[k] !== undefined);
        ctx.fillStyle = k === 'L' ? P.alpha('accent', .16) : P.surface2;
        D.rrect(ctx, x - w / 2, y - h / 2, w, h, 10); ctx.fill();
        ctx.strokeStyle = k === 'L' || k === 'w' || k === 'b' ? P.accent : P.strong; ctx.lineWidth = 1.4; ctx.stroke();
        D.text(ctx, label, x, y - 11, { color: P.dim, size: 10.5, align: 'center' });
        D.text(ctx, showV ? fmtN(val[k], 3) : '?', x, y + 8, { color: P.text, size: 14, align: 'center', weight: 650, mono: true });
        if (showG) D.text(ctx, `∂L = ${fmtN(grad[k], 3)}`, x, y + h / 2 + 11, { color: P.err, size: 10.5, align: 'center', mono: true, weight: 600 });
      });
      if (s.hist.length > 1) {
        const bx = c.w * .22, by = 10, bw = c.w * .2, bh = 40, mx = Math.max(...s.hist, 1e-9);
        D.text(ctx, 'loss per step', bx, by + 4, { color: P.faint, size: 10 });
        ctx.beginPath();
        s.hist.forEach((h, i) => { const px = bx + i / (s.hist.length - 1) * bw, py = by + 12 + bh - h / mx * bh; i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); });
        ctx.strokeStyle = P.accent; ctx.lineWidth = 1.8; ctx.stroke();
      }
    };
    explain();
  },
});

/* ========================================================= probability == */
defineLab('bayes', {
  title: 'Base rates: 1,000 people take the test',
  hint: 'Each square is a person. Solid squares tested positive. How many of them are really sick?',
  mount(L) {
    const s = { prev: .01, sens: .95, spec: .95 };
    const N = 1000, COLS = 50, ROWS = 20;
    const c = L.canvas(w => (w - 20) / COLS * ROWS + 20);
    let cells = new Array(N).fill(3), prevCells = cells.slice(), mixT = 1;
    const pct = v => `${(v * 100).toFixed(v < .01 ? 1 : 0)}%`;
    L.slider('how common is the disease', { min: .001, max: .5, log: true, value: s.prev, fmt: pct }, v => { s.prev = v; changed(); });
    L.slider('sensitivity (sick → positive)', { min: .5, max: .999, step: .001, value: s.sens, fmt: pct }, v => { s.sens = v; changed(); });
    L.slider('specificity (healthy → negative)', { min: .5, max: .999, step: .001, value: s.spec, fmt: pct }, v => { s.spec = v; changed(); });
    function changed() {
      const sick = Math.round(N * s.prev), tp = Math.round(sick * s.sens), fn = sick - tp;
      const fp = Math.round((N - sick) * (1 - s.spec)), tn = N - sick - fp;
      prevCells = cells.slice();
      cells = [...Array(tp).fill(0), ...Array(fn).fill(1), ...Array(fp).fill(2), ...Array(tn).fill(3)];
      const post = s.prev * s.sens / (s.prev * s.sens + (1 - s.prev) * (1 - s.spec));
      L.stats([['sick & positive', tp, 'ok', L.P.ok], ['sick, missed', fn], ['healthy but positive', fp, 'err', L.P.err], ['P(sick | positive)', pct(post), 'accent']]);
      L.insight(`<b>${tp + fp} people test positive, but only ${tp} are sick: ${pct(post)}.</b> ${post < .5
        ? `The ${fp} false alarms come from the huge healthy group, so a rare disease stays unlikely even after a positive result. That is the base-rate fallacy.`
        : 'The disease is common enough (or the test specific enough) that a positive result is trustworthy.'}`);
      mixT = 0;
      L.tween(450, t => { mixT = t; L.redraw(); });
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, size = (c.w - 20) / COLS, pad = 10;
      const color = g => g === 0 ? P.ok : g === 1 ? P.alpha('ok', .25) : g === 2 ? P.err : P.alpha('faint', .16);
      for (let i = 0; i < N; i++) {
        const x = pad + (i % COLS) * size, y = pad + Math.floor(i / COLS) * size;
        const g = cells[i], was = prevCells[i];
        ctx.globalAlpha = 1;
        ctx.fillStyle = color(was);
        D.rrect(ctx, x + 1, y + 1, size - 2, size - 2, 2); ctx.fill();
        if (was !== g) {
          ctx.globalAlpha = mixT;
          ctx.fillStyle = color(g);
          D.rrect(ctx, x + 1, y + 1, size - 2, size - 2, 2); ctx.fill();
        }
        ctx.globalAlpha = 1;
        if ((mixT > .5 ? g : was) === 1) { ctx.strokeStyle = P.ok; ctx.lineWidth = 1.2; D.rrect(ctx, x + 1.5, y + 1.5, size - 3, size - 3, 2); ctx.stroke(); }
      }
    };
    changed();
  },
});

defineLab('distributions', {
  title: 'Distributions and the Central Limit Theorem',
  hint: 'Pick a distribution, move its parameters, then draw samples and watch the histogram approach the curve.',
  mount(L, opts) {
    const r = rng(11);
    const s = { mode: opts.mode || 'normal', mu: 0, sd: 1, n: 20, p: .3, lam: 4, rate: 1, cltN: 1, samples: [] };
    const c = L.canvas(w => Math.min(300, w * .5));
    const modes = [['normal', 'Normal'], ['binomial', 'Binomial'], ['poisson', 'Poisson'], ['exponential', 'Exponential'], ['clt', 'CLT: averages']];
    L.seg('', modes, s.mode, m => { s.mode = m; build(); });
    const sampler = L.loop(() => {
      for (let i = 0; i < 30 && s.samples.length < 2000; i++) s.samples.push(draw());
      update(); L.redraw();
      if (s.samples.length >= 2000) return false;
    });
    L.playButton(sampler, ['Draw 2,000 samples', 'Pause'], () => { if (s.samples.length >= 2000) s.samples = []; });
    L.button('Clear samples', () => { s.samples = []; update(); L.redraw(); });
    const lgamma = z => {
      const g = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, .1208650973866179e-2, -.5395239384953e-5];
      let x = z, y = z, t = x + 5.5; t -= (x + .5) * Math.log(t);
      let ser = 1.000000000190015; for (const q of g) ser += q / ++y;
      return -t + Math.log(2.5066282746310005 * ser / x);
    };
    const pdf = x => {
      switch (s.mode) {
        case 'normal': return Math.exp(-((x - s.mu) ** 2) / (2 * s.sd ** 2)) / (s.sd * Math.sqrt(TAU));
        case 'binomial': { const k = Math.round(x); if (k < 0 || k > s.n) return 0; return Math.exp(lgamma(s.n + 1) - lgamma(k + 1) - lgamma(s.n - k + 1) + k * Math.log(s.p) + (s.n - k) * Math.log(1 - s.p)); }
        case 'poisson': { const k = Math.round(x); if (k < 0) return 0; return Math.exp(k * Math.log(s.lam) - s.lam - lgamma(k + 1)); }
        case 'exponential': return x < 0 ? 0 : s.rate * Math.exp(-s.rate * x);
        default: { const sd = 1 / Math.sqrt(s.cltN); return Math.exp(-((x - 1) ** 2) / (2 * sd * sd)) / (sd * Math.sqrt(TAU)); }
      }
    };
    const draw = () => {
      switch (s.mode) {
        case 'normal': return s.mu + s.sd * gauss(r);
        case 'binomial': { let k = 0; for (let i = 0; i < s.n; i++) k += r() < s.p; return k; }
        case 'poisson': { const lim = Math.exp(-s.lam); let k = 0, p = 1; do { k++; p *= r(); } while (p > lim); return k - 1; }
        case 'exponential': return -Math.log(1 - r()) / s.rate;
        default: { let sum = 0; for (let i = 0; i < s.cltN; i++) sum -= Math.log(1 - r()); return sum / s.cltN; }
      }
    };
    const discrete = () => s.mode === 'binomial' || s.mode === 'poisson';
    const range = () => s.mode === 'normal' ? [-7, 7] : s.mode === 'binomial' ? [-.5, s.n + .5]
      : s.mode === 'poisson' ? [-.5, Math.max(12, Math.ceil(s.lam + 4 * Math.sqrt(s.lam))) + .5] : s.mode === 'exponential' ? [0, 6] : [0, 3];
    const theo = () => s.mode === 'normal' ? [s.mu, s.sd ** 2] : s.mode === 'binomial' ? [s.n * s.p, s.n * s.p * (1 - s.p)]
      : s.mode === 'poisson' ? [s.lam, s.lam] : s.mode === 'exponential' ? [1 / s.rate, 1 / s.rate ** 2] : [1, 1 / s.cltN];
    function build() {
      L.clearDyn(); s.samples = [];
      const on = f => v => { f(v); s.samples = []; update(); L.redraw(); };
      if (s.mode === 'normal') {
        L.slider('mean μ', { min: -3, max: 3, step: .1, value: s.mu, dyn: true, fmt: v => v.toFixed(1) }, on(v => { s.mu = v; }));
        L.slider('std σ', { min: .3, max: 3, step: .05, value: s.sd, dyn: true, fmt: v => v.toFixed(2) }, on(v => { s.sd = v; }));
      } else if (s.mode === 'binomial') {
        L.slider('trials n', { min: 1, max: 40, step: 1, value: s.n, dyn: true }, on(v => { s.n = v; }));
        L.slider('success p', { min: .02, max: .98, step: .01, value: s.p, dyn: true, fmt: v => v.toFixed(2) }, on(v => { s.p = v; }));
      } else if (s.mode === 'poisson') {
        L.slider('rate λ', { min: .3, max: 15, step: .1, value: s.lam, dyn: true, fmt: v => v.toFixed(1) }, on(v => { s.lam = v; }));
      } else if (s.mode === 'exponential') {
        L.slider('rate λ', { min: .3, max: 3, step: .05, value: s.rate, dyn: true, fmt: v => v.toFixed(2) }, on(v => { s.rate = v; }));
      } else {
        L.slider('draws averaged per sample', { min: 1, max: 50, step: 1, value: s.cltN, dyn: true }, on(v => { s.cltN = v; }));
      }
      update(); L.redraw();
    }
    function update() {
      const [m, v] = theo(), n = s.samples.length;
      const sm = n ? s.samples.reduce((a, x) => a + x, 0) / n : NaN;
      const sv = n > 1 ? s.samples.reduce((a, x) => a + (x - sm) ** 2, 0) / (n - 1) : NaN;
      L.stats([['mean', fmtN(m)], ['variance', fmtN(v)], n && ['sample mean', fmtN(sm), 'accent'], n > 1 && ['sample variance', fmtN(sv), 'accent'], n && ['samples', n]]);
      const text = {
        normal: '<b>The bell curve.</b> About 68% of samples land within one σ of μ and 95% within two.',
        binomial: `<b>Count of successes in ${s.n} coin flips with p = ${s.p.toFixed(2)}.</b> With many trials it starts to look like a bell curve centred on n·p = ${fmtN(s.n * s.p, 1)}.`,
        poisson: `<b>How many events arrive in a fixed window</b> when they happen ${s.lam.toFixed(1)} times on average. Mean and variance are both λ.`,
        exponential: '<b>Waiting time until the next event.</b> Heavily skewed: short waits are common, long ones rare.',
        clt: s.cltN === 1 ? '<b>n = 1: each sample is one skewed exponential draw.</b> Now raise n: every sample becomes the average of n draws.'
          : s.cltN < 8 ? `<b>n = ${s.cltN}:</b> the skew is already fading. Keep going.` : `<b>n = ${s.cltN}: a bell curve</b>, even though every single draw is skewed. Averages of independent things become Gaussian, with spread shrinking like 1/√n.`,
      };
      L.insight(text[s.mode]);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, [x0, x1] = range();
      let ymax = 0;
      for (let i = 0; i <= 200; i++) ymax = Math.max(ymax, pdf(lerp(x0, x1, i / 200)));
      if (s.mode === 'clt' && s.cltN === 1) ymax = Math.max(ymax, 1);
      const bins = discrete() ? Math.round(x1 - x0) : 44, bw = (x1 - x0) / bins;
      const counts = new Array(bins).fill(0);
      s.samples.forEach(x => { const i = Math.floor((x - x0) / bw); if (i >= 0 && i < bins) counts[i]++; });
      const dens = counts.map(k => s.samples.length ? k / (s.samples.length * bw) : 0);
      ymax = Math.max(ymax, ...dens) * 1.12 || 1;
      const v = D.view(c, { x0, x1, y0: 0, y1: ymax, pad: 14, padL: 40, padB: 26 });
      const step = (x1 - x0) > 20 ? 5 : (x1 - x0) > 8 ? 2 : 1;
      const ticks = []; for (let t = Math.ceil(x0); t <= x1; t += step) ticks.push(t);
      D.axes(ctx, v, P, { xTicks: ticks, yTicks: [ymax / 2, ymax].map(t => +t.toFixed(2)) });
      dens.forEach((d, i) => {
        if (!d) return;
        const x = x0 + i * bw;
        ctx.fillStyle = P.alpha('accent', .45);
        ctx.fillRect(v.sx(x) + 1, v.sy(d), v.sx(x + bw) - v.sx(x) - 2, v.sy(0) - v.sy(d));
      });
      if (discrete()) {
        for (let k = Math.ceil(x0); k <= x1; k++) {
          const p = pdf(k);
          D.line(ctx, v.sx(k), v.sy(0), v.sx(k), v.sy(p), P.series[0], 3);
          D.dot(ctx, v.sx(k), v.sy(p), 3.5, P.series[0]);
        }
      } else {
        if (s.mode === 'clt' && s.cltN === 1) D.curve(ctx, v, x => x < 0 ? NaN : Math.exp(-x), P.series[0], 2.4);
        else D.curve(ctx, v, pdf, P.series[0], 2.4);
      }
    };
    build();
  },
});

defineLab('mle', {
  title: 'MLE vs MAP on a coin',
  hint: 'Flip the coin a few times. MLE trusts only the flips; MAP also trusts a prior belief that coins are usually fair.',
  mount(L) {
    const r = rng(5);
    const s = { h: 3, t: 0, alpha: 6, bias: .7, queue: 0 };
    const c = L.canvas(w => Math.min(290, w * .48));
    const sh = L.slider('heads', { min: 0, max: 60, step: 1, value: s.h }, v => { s.h = v; update(); });
    const st = L.slider('tails', { min: 0, max: 60, step: 1, value: s.t }, v => { s.t = v; update(); });
    L.slider('prior strength (belief the coin is fair)', { min: 1, max: 40, step: 1, value: s.alpha }, v => { s.alpha = v; update(); });
    L.slider('true bias of the coin', { min: .05, max: .95, step: .05, value: s.bias, fmt: v => v.toFixed(2) }, v => { s.bias = v; });
    let acc = 0;
    const flipper = L.loop(dt => {
      acc += dt;
      if (acc < .12) return;
      acc = 0;
      r() < s.bias ? s.h++ : s.t++;
      sh.set(Math.min(60, s.h), true); st.set(Math.min(60, s.t), true);
      update();
      if (--s.queue <= 0) return false;
    });
    L.button('Flip 10 more', () => { s.queue = 10; flipper.start(); }, 'primary');
    L.button('Start over', () => { s.h = 0; s.t = 0; sh.set(0, true); st.set(0, true); update(); });
    const logBeta = (th, a, b) => (a - 1) * Math.log(th) + (b - 1) * Math.log(1 - th);
    const curve = (a, b) => {
      const xs = Array.from({ length: 301 }, (_, i) => .001 + .998 * i / 300);
      const ls = xs.map(x => logBeta(x, a, b)), m = Math.max(...ls);
      return xs.map((x, i) => [x, Math.exp(ls[i] - m)]);
    };
    const mle = () => s.h + s.t ? s.h / (s.h + s.t) : NaN;
    const map = () => (s.h + s.alpha - 1) / (s.h + s.t + 2 * s.alpha - 2);
    function update() {
      L.redraw();
      const n = s.h + s.t;
      L.stats([['flips', n], ['MLE θ', fmtN(mle(), 3), '', L.P.series[0]], ['MAP θ', fmtN(map(), 3), 'accent'], ['true θ', s.bias.toFixed(2)]]);
      L.insight(!n ? '<b>No data yet.</b> MLE is undefined; MAP falls back on the prior and says 0.5.'
        : n < 12 ? `<b>Only ${n} flips.</b> MLE says θ = ${fmtN(mle(), 2)} and trusts it completely. The prior pulls MAP to ${fmtN(map(), 2)}: a prior acts like ${2 * s.alpha - 2} imaginary flips, half heads.`
        : `<b>${n} flips.</b> The data now outweighs the prior, so MLE and MAP agree (${fmtN(mle(), 2)} vs ${fmtN(map(), 2)}). Priors matter most when data is scarce.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      const v = D.view(c, { x0: 0, x1: 1, y0: 0, y1: 1.12, pad: 16, padL: 16, padB: 26 });
      D.axes(ctx, v, P, { xTicks: [0, .25, .5, .75, 1], xLabel: 'θ = P(heads)' });
      const plot = (pts, color, fill, w = 2.2) => {
        ctx.beginPath();
        pts.forEach(([x, y], i) => i ? ctx.lineTo(v.sx(x), v.sy(y)) : ctx.moveTo(v.sx(x), v.sy(y)));
        if (fill) { ctx.lineTo(v.sx(1), v.sy(0)); ctx.lineTo(v.sx(0), v.sy(0)); ctx.closePath(); ctx.fillStyle = fill; ctx.fill(); }
        else { ctx.strokeStyle = color; ctx.lineWidth = w; ctx.stroke(); }
      };
      plot(curve(s.alpha, s.alpha), P.faint, null, 1.6);
      if (s.h + s.t) plot(curve(s.h + 1, s.t + 1), P.series[0]);
      const post = curve(s.h + s.alpha, s.t + s.alpha);
      plot(post, null, P.alpha('accent', .22));
      plot(post, P.accent);
      const mark = (x, color, label, dy) => {
        if (!Number.isFinite(x)) return;
        D.line(ctx, v.sx(x), v.sy(0), v.sx(x), v.sy(1.05), color, 1.6, [4, 4]);
        D.text(ctx, label, v.sx(x) + 5, v.sy(1.05) + dy, { color, size: 11, weight: 650 });
      };
      mark(mle(), P.series[0], 'MLE', 0);
      mark(map(), P.accent, 'MAP', 14);
      [['prior', P.faint], ['likelihood', P.series[0]], ['posterior', P.accent]].forEach(([l, col], i) => {
        D.dot(ctx, 24 + i * 96, 14, 4, col);
        D.text(ctx, l, 32 + i * 96, 14, { color: P.dim, size: 11 });
      });
    };
    update();
  },
});

defineLab('entropy', {
  title: 'Entropy, cross-entropy and KL divergence',
  hint: 'Drag the tops of the bars. <b>P</b> is the truth, <b>Q</b> is what your model predicts.',
  mount(L) {
    const s = { P: [.7, .1, .1, .1], Q: [.25, .25, .25, .25] };
    const labels = ['cat', 'dog', 'fox', 'owl'];
    const c = L.canvas(w => Math.min(320, w * .52));
    let geo = null;
    const set = (dist, i, val) => {
      const d = s[dist], vv = clamp(val, .01, .97), rest = 1 - vv;
      const others = d.reduce((a, x, j) => j === i ? a : a + x, 0);
      d.forEach((x, j) => { if (j !== i) d[j] = others > 1e-9 ? x / others * rest : rest / 3; });
      d[i] = vv;
    };
    L.drag(c, {
      hit: (x, y) => {
        if (!geo) return null;
        for (let i = 0; i < 4; i++) for (const k of ['P', 'Q']) {
          const bx = geo.x(i, k);
          if (x >= bx - 4 && x <= bx + geo.bw + 4 && y >= geo.top - 8 && y <= geo.base + 4) return [k, i];
        }
        return null;
      },
      move: ([k, i], x, y) => { set(k, i, (geo.base - y) / (geo.base - geo.top)); update(); },
    });
    const preset = (P, Q) => L.button(P[0], () => { s.P = [...P[1]]; s.Q = [...Q]; update(); });
    preset(['Model matches truth', [.6, .2, .1, .1]], [.6, .2, .1, .1]);
    preset(['Confidently wrong', [.9, .03, .04, .03]], [.04, .9, .03, .03]);
    preset(['Truth is certain', [.97, .01, .01, .01]], [.4, .2, .2, .2]);
    preset(['Pure uncertainty', [.25, .25, .25, .25]], [.25, .25, .25, .25]);
    const H = d => -d.reduce((a, p) => a + p * Math.log2(p), 0);
    const CE = () => -s.P.reduce((a, p, i) => a + p * Math.log2(s.Q[i]), 0);
    function update() {
      L.redraw();
      const h = H(s.P), ce = CE(), kl = ce - h;
      L.stats([['H(P)', `${fmtN(h, 3)} bits`, '', L.P.series[0]], ['KL(P‖Q)', `${fmtN(kl, 3)} bits`, 'err'], ['cross-entropy H(P,Q)', `${fmtN(ce, 3)} bits`, 'accent']]);
      L.insight(kl < .01 ? `<b>Q matches P, so KL ≈ 0.</b> Cross-entropy equals the entropy of the truth (${fmtN(h, 2)} bits). That part of the loss can never be trained away.`
        : kl > 2 ? `<b>Confidently wrong costs a lot:</b> KL = ${fmtN(kl, 2)} bits. Cross-entropy punishes putting low probability on what actually happens.`
        : `<b>Cross-entropy = entropy + KL.</b> Training can only shrink the red KL part (${fmtN(kl, 2)} bits) by moving Q towards P.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, top = 30, base = c.h - 78, gw = (c.w - 40) / 4, bw = Math.min(40, gw * .3);
      geo = { top, base, bw, x: (i, k) => 20 + i * gw + gw / 2 + (k === 'P' ? -bw - 3 : 3) };
      D.line(ctx, 16, base, c.w - 16, base, P.strong, 1);
      labels.forEach((l, i) => {
        ['P', 'Q'].forEach(k => {
          const val = s[k][i], x = geo.x(i, k), hgt = val * (base - top);
          ctx.fillStyle = k === 'P' ? P.series[0] : P.accent;
          D.rrect(ctx, x, base - hgt, bw, hgt, 4); ctx.fill();
          ctx.fillStyle = P.surface; ctx.fillRect(x + bw / 2 - 7, base - hgt + 3, 14, 3);
          D.text(ctx, val.toFixed(2), x + bw / 2, base - hgt - 10, { color: P.dim, size: 10.5, align: 'center', mono: true });
        });
        D.text(ctx, l, 20 + i * gw + gw / 2, base + 14, { color: P.dim, size: 12, align: 'center' });
      });
      D.text(ctx, '■ P (truth)', 20, 12, { color: P.series[0], size: 11.5, weight: 600 });
      D.text(ctx, '■ Q (model)', 110, 12, { color: P.accent, size: 11.5, weight: 600 });
      const h = H(s.P), kl = CE() - h, scale = (c.w - 40) / Math.max(4, h + kl), y = c.h - 40;
      ctx.fillStyle = P.series[0]; D.rrect(ctx, 20, y, h * scale, 22, 5); ctx.fill();
      ctx.fillStyle = P.err; D.rrect(ctx, 20 + h * scale, y, Math.max(0, kl * scale), 22, 5); ctx.fill();
      D.text(ctx, `entropy ${fmtN(h, 2)}`, 26, y + 11, { color: P.surface, size: 11, weight: 650 });
      if (kl * scale > 60) D.text(ctx, `+ KL ${fmtN(kl, 2)}`, 26 + h * scale, y + 11, { color: P.surface, size: 11, weight: 650 });
      D.text(ctx, `= cross-entropy ${fmtN(h + kl, 2)} bits`, Math.min(c.w - 16, 28 + (h + kl) * scale), y - 10, { color: P.accent, size: 11, weight: 650, align: (h + kl) * scale > c.w - 200 ? 'right' : 'left' });
    };
    update();
  },
});

/* ========================================================= optimisation == */
defineLab('gradient', {
  title: 'Race the optimizers down a loss surface',
  hint: 'Click anywhere on the map to choose a starting point, then press Play. Darker means lower loss.',
  mount(L, opts) {
    const r = rng(3);
    const SURF = {
      bowl: { f: (x, y) => x * x + y * y, g: (x, y) => [2 * x, 2 * y], dom: [-3, 3, -3, 3], start: [-2.4, 2.3], lr: .1, min: [0, 0] },
      ravine: { f: (x, y) => .08 * x * x + 3 * y * y, g: (x, y) => [.16 * x, 6 * y], dom: [-3, 3, -2, 2], start: [-2.8, 1.4], lr: .15, min: [0, 0] },
      rosen: { f: (x, y) => (1 - x) ** 2 + 5 * (y - x * x) ** 2, g: (x, y) => [-2 * (1 - x) - 20 * x * (y - x * x), 10 * (y - x * x)], dom: [-2, 2, -1, 3], start: [-1.6, 2.6], lr: .02, min: [1, 1] },
      bumpy: { f: (x, y) => .25 * (x * x + y * y) + 1.2 * Math.sin(1.7 * x) * Math.sin(1.7 * y) + 1.3, g: (x, y) => [.5 * x + 2.04 * Math.cos(1.7 * x) * Math.sin(1.7 * y), .5 * y + 2.04 * Math.sin(1.7 * x) * Math.cos(1.7 * y)], dom: [-3.2, 3.2, -3.2, 3.2], start: [-2.6, 2.4], lr: .08, min: [0, 0] },
    };
    const OPT = [['gd', 'Gradient descent'], ['mom', 'Momentum'], ['rms', 'RMSProp'], ['adam', 'Adam']];
    const s = { surf: opts.surface || 'bowl', lr: 0, noise: opts.noise || 0, on: { gd: true, mom: true, rms: false, adam: true }, runs: {}, steps: 0 };
    s.lr = SURF[s.surf].lr;
    s.start = [...SURF[s.surf].start];
    const c = L.canvas(w => Math.min(360, w * .62));
    let v = null, heat = null, heatKey = '';
    L.seg('surface', [['bowl', 'Bowl'], ['ravine', 'Narrow ravine'], ['rosen', 'Rosenbrock'], ['bumpy', 'Bumpy']], s.surf, x => {
      s.surf = x; s.start = [...SURF[x].start]; lrS.set(SURF[x].lr, true); s.lr = SURF[x].lr; reset();
    });
    const lrS = L.slider('learning rate', { min: .001, max: 1, log: true, value: s.lr, fmt: x => x.toFixed(3) }, x => { s.lr = x; reset(); });
    L.slider('gradient noise (SGD mini-batches)', { min: 0, max: 3, step: .1, value: s.noise, fmt: x => x.toFixed(1) }, x => { s.noise = x; reset(); });
    const run = L.loop(() => {
      for (let i = 0; i < 2; i++) step();
      L.redraw(); update();
      if (s.steps >= 400 || Object.values(s.runs).every(q => q.dead || q.done)) return false;
    });
    L.playButton(run, ['Play', 'Pause'], () => { if (s.steps >= 400) reset(); });
    L.button('Step', () => { step(); L.redraw(); update(); });
    L.button('Reset', () => { run.stop(); reset(); });
    OPT.forEach(([k, label]) => L.toggle(label, s.on[k], x => { s.on[k] = x; reset(); }));
    L.drag(c, { down: (x, y) => { if (!v) return; s.start = [v.ix(x), v.iy(y)]; run.stop(); reset(); run.start(); } });
    function reset() {
      s.steps = 0;
      s.runs = {};
      OPT.forEach(([k]) => { if (s.on[k]) s.runs[k] = { x: s.start[0], y: s.start[1], m: [0, 0], v: [0, 0], t: 0, trail: [[...s.start]], dead: false, done: false }; });
      L.redraw(); update();
    }
    function step() {
      const S = SURF[s.surf];
      s.steps++;
      Object.entries(s.runs).forEach(([k, q]) => {
        if (q.dead || q.done) return;
        let [gx, gy] = S.g(q.x, q.y);
        if (s.noise) { gx += s.noise * gauss(r); gy += s.noise * gauss(r); }
        q.t++;
        const lr = s.lr;
        if (k === 'gd') { q.x -= lr * gx; q.y -= lr * gy; }
        else if (k === 'mom') { q.m = [.9 * q.m[0] + gx, .9 * q.m[1] + gy]; q.x -= lr * q.m[0]; q.y -= lr * q.m[1]; }
        else if (k === 'rms') { q.v = [.9 * q.v[0] + .1 * gx * gx, .9 * q.v[1] + .1 * gy * gy]; q.x -= lr * gx / (Math.sqrt(q.v[0]) + 1e-8); q.y -= lr * gy / (Math.sqrt(q.v[1]) + 1e-8); }
        else {
          q.m = [.9 * q.m[0] + .1 * gx, .9 * q.m[1] + .1 * gy]; q.v = [.999 * q.v[0] + .001 * gx * gx, .999 * q.v[1] + .001 * gy * gy];
          const b1 = 1 - .9 ** q.t, b2 = 1 - .999 ** q.t;
          q.x -= lr * (q.m[0] / b1) / (Math.sqrt(q.v[0] / b2) + 1e-8); q.y -= lr * (q.m[1] / b1) / (Math.sqrt(q.v[1] / b2) + 1e-8);
        }
        if (!Number.isFinite(q.x) || Math.abs(q.x) > 1e3 || Math.abs(q.y) > 1e3) { q.dead = true; return; }
        q.trail.push([q.x, q.y]);
        if (!s.noise && Math.hypot(...S.g(q.x, q.y)) < 1e-3) q.done = true;
      });
    }
    function update() {
      const S = SURF[s.surf], names = Object.fromEntries(OPT);
      L.stats([['step', s.steps], ...Object.entries(s.runs).map(([k, q], i) =>
        [names[k], q.dead ? 'diverged' : fmtN(S.f(q.x, q.y), 3), q.dead ? 'err' : '', colorOf(k)])]);
      const runs = Object.entries(s.runs), dead = runs.filter(([, q]) => q.dead).map(([k]) => names[k]);
      L.insight(dead.length ? `<b>${dead.join(' and ')} diverged.</b> The learning rate is too big for this curvature: each step overshoots further than the last.`
        : s.surf === 'ravine' && s.on.gd && s.steps > 20 ? '<b>Plain gradient descent zig-zags across the ravine</b> because the slope is steep one way and flat the other. Momentum builds speed along the valley; Adam rescales each direction.'
        : s.surf === 'bumpy' && s.steps > 60 ? '<b>Local minima.</b> Some runs get stuck in a dimple. Momentum can roll through small bumps, and noise helps too.'
        : s.surf === 'rosen' && s.steps > 60 ? '<b>Rosenbrock:</b> finding the curved valley is easy, following it to (1, 1) is slow. It is the classic stress test for optimizers.'
        : s.noise > .5 ? '<b>Noisy gradients</b> are what mini-batch SGD sees. Paths wander, and a smaller learning rate settles closer to the minimum.'
        : '<b>Each optimizer takes the same gradient and turns it into a step differently.</b> Try the narrow ravine or push the learning rate up.');
    }
    const colorOf = k => ({ gd: L.P.series[0], mom: L.P.series[1], rms: L.P.series[4], adam: L.P.series[3] }[k]);
    L.draw = P => {
      c.clear();
      const { ctx } = c, S = SURF[s.surf], [x0, x1, y0, y1] = S.dom;
      v = D.view(c, { x0, x1, y0, y1, pad: 0 });
      const key = `${s.surf}|${c.w}|${c.h}|${P.accent}|${P.bg}`;
      if (key !== heatKey) {
        heatKey = key;
        const gw = Math.ceil(c.w / 3), gh = Math.ceil(c.h / 3);
        heat = document.createElement('canvas'); heat.width = gw; heat.height = gh;
        const hctx = heat.getContext('2d'), img = hctx.createImageData(gw, gh);
        const vals = new Float64Array(gw * gh);
        let lo = Infinity, hi = -Infinity;
        for (let j = 0; j < gh; j++) for (let i = 0; i < gw; i++) {
          const f = S.f(lerp(x0, x1, i / gw), lerp(y1, y0, j / gh));
          vals[j * gw + i] = f; lo = Math.min(lo, f); hi = Math.max(hi, f);
        }
        const low = P.rgb('accent'), high = P.rgb('surface'), line = P.rgb('text');
        for (let i = 0; i < gw * gh; i++) {
          const t = Math.log1p(vals[i] - lo) / Math.log1p(hi - lo);
          const band = (t * 14) % 1 < .07 ? .2 : 0;
          for (let ch = 0; ch < 3; ch++) {
            const base = lerp(low[ch], high[ch], .45 + .55 * t);
            img.data[i * 4 + ch] = lerp(base, line[ch], band);
          }
          img.data[i * 4 + 3] = 255;
        }
        hctx.putImageData(img, 0, 0);
      }
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(heat, 0, 0, c.w, c.h);
      D.text(ctx, '★', v.sx(S.min[0]), v.sy(S.min[1]), { color: P.text, size: 16, align: 'center' });
      Object.entries(s.runs).forEach(([k, q]) => {
        const col = colorOf(k);
        ctx.beginPath();
        q.trail.forEach(([x, y], i) => i ? ctx.lineTo(v.sx(x), v.sy(y)) : ctx.moveTo(v.sx(x), v.sy(y)));
        ctx.strokeStyle = col; ctx.lineWidth = 2.2; ctx.lineJoin = 'round'; ctx.stroke();
        const [lx, ly] = q.trail[q.trail.length - 1];
        D.dot(ctx, clamp(v.sx(lx), 4, c.w - 4), clamp(v.sy(ly), 4, c.h - 4), 6, col, P.surface, 2);
      });
      D.dot(ctx, v.sx(s.start[0]), v.sy(s.start[1]), 5, null, P.text, 2);
    };
    reset();
  },
});

defineLab('lrschedule', {
  title: 'Learning-rate schedules and warmup',
  hint: 'Top: the learning rate over training. Bottom: a simulated training loss using that schedule.',
  mount(L) {
    const s = { kind: 'warmcos', warm: 5, reveal: 1 };
    const c = L.canvas(w => Math.min(330, w * .56));
    const STEPS = 1000;
    const f = t => {
      const cos = u => .05 + .95 * .5 * (1 + Math.cos(Math.PI * clamp(u, 0, 1)));
      let lr;
      switch (s.kind) {
        case 'const': lr = 1; break;
        case 'step': lr = .5 ** Math.floor(t / .3); break;
        case 'exp': lr = Math.exp(-3 * t); break;
        case 'cos': lr = cos(t); break;
        case 'onecycle': lr = t < .3 ? lerp(.08, 1, t / .3) : cos((t - .3) / .7); break;
        default: { const w = Math.max(.001, s.warm / 100); lr = t < w ? t / w : cos((t - w) / (1 - w)); }
      }
      if (s.kind !== 'warmcos' && s.kind !== 'onecycle' && s.warm > 0) lr *= Math.min(1, t / (s.warm / 100));
      return lr;
    };
    let lossCache = null;
    const simulate = () => {
      const r = rng(21), out = [];
      let loss = 4.2;
      for (let i = 0; i < STEPS; i++) {
        const lr = f(i / STEPS);
        // early on, the model can only tolerate a learning rate that grows with step count
        const spike = i < 80 ? Math.max(0, lr - (i + 6) / 70) * 1.6 * Math.abs(gauss(r)) : 0;
        loss += -0.011 * lr * (loss - .35) + spike + lr * .05 * gauss(r) * Math.sqrt(loss);
        loss = clamp(loss, .3, 9);
        out.push(loss + lr * .35);
      }
      return out;
    };
    L.seg('schedule', [['const', 'Constant'], ['step', 'Step decay'], ['exp', 'Exponential'], ['cos', 'Cosine'], ['warmcos', 'Warmup + cosine'], ['onecycle', 'One-cycle']], s.kind, k => { s.kind = k; changed(); });
    L.slider('warmup (% of steps)', { min: 0, max: 30, step: 1, value: s.warm, fmt: v => `${v}%` }, v => { s.warm = v; changed(); });
    const play = L.loop(dt => { s.reveal = Math.min(1, s.reveal + dt * .45); L.redraw(); if (s.reveal >= 1) return false; });
    L.playButton(play, ['Replay training', 'Pause'], () => { if (s.reveal >= 1) s.reveal = 0; });
    function changed() {
      lossCache = simulate();
      const last = lossCache.slice(-50).reduce((a, b) => a + b, 0) / 50;
      const early = Math.max(...lossCache.slice(0, 120));
      L.stats([['final loss (avg last 50)', fmtN(last, 3), 'accent'], ['worst loss in first 120 steps', fmtN(early, 2), early > 4.6 ? 'err' : '']]);
      const tips = {
        const: 'A constant rate never lets training settle: the loss keeps bouncing at the end.',
        step: 'Step decay drops the rate at fixed milestones. Each drop gives a visible step down in loss.',
        exp: 'Exponential decay settles smoothly but can shrink the rate before the model has learned much.',
        cos: 'Cosine decay stays high for exploration, then glides down so the model can settle into a minimum.',
        warmcos: 'Warmup ramps up slowly while Adam\'s statistics are still unreliable, which avoids early loss spikes. Transformers are almost always trained this way.',
        onecycle: 'One-cycle climbs to a high rate (fast progress, a regularising effect), then anneals far below the start.',
      };
      L.insight(`<b>${early > 4.6 && s.warm === 0 ? 'Early instability.' : 'Schedule:'}</b> ${tips[s.kind]}${early > 4.6 && s.warm === 0 ? ' Add a few percent of warmup and watch the early spike disappear.' : ''}`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, split = c.h * .44, upto = Math.floor(s.reveal * STEPS);
      const v1 = { ...D.view({ w: c.w, h: split }, { x0: 0, x1: 1, y0: 0, y1: 1.1, pad: 12, padL: 44, padB: 8 }) };
      D.axes(ctx, v1, P, { yTicks: [.5, 1], fmtY: t => `${t}×`, yLabel: 'learning rate' });
      D.curve(ctx, v1, x => f(x), P.accent, 2.6, 400);
      if (s.warm > 0) { ctx.fillStyle = P.alpha('accent', .1); ctx.fillRect(v1.sx(0), v1.sy(1.1), v1.sx(s.warm / 100) - v1.sx(0), v1.sy(0) - v1.sy(1.1)); }
      const maxL = Math.max(4.8, ...lossCache);
      const v2 = D.view({ w: c.w, h: c.h - split }, { x0: 0, x1: STEPS, y0: 0, y1: maxL, pad: 10, padL: 44, padB: 22 });
      ctx.save(); ctx.translate(0, split);
      D.axes(ctx, v2, P, { xTicks: [0, 250, 500, 750, 1000], yTicks: [2, 4], yLabel: 'training loss' });
      ctx.beginPath();
      for (let i = 0; i < upto; i++) i ? ctx.lineTo(v2.sx(i), v2.sy(lossCache[i])) : ctx.moveTo(v2.sx(i), v2.sy(lossCache[i]));
      ctx.strokeStyle = P.series[0]; ctx.lineWidth = 1.5; ctx.stroke();
      if (s.reveal < 1) D.line(ctx, v2.sx(upto), v2.sy(0), v2.sx(upto), v2.sy(maxL), P.faint, 1, [3, 3]);
      ctx.restore();
    };
    changed();
  },
});
