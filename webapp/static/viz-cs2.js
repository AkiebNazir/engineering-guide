/* ============================================================================
   CS Fundamentals labs, part 1: cost and the structures that pay it.

     cs-growth      how each complexity class grows, in steps and wall-clock time
     cs-amortized   dynamic-array growth: why doubling makes append O(1) amortized
     cs-master      recursion trees and the master theorem, level by level
     cs-hashtable   chaining vs linear probing, load factor, resize, tombstones
     cs-heap        a binary heap as a tree and as the array it really is
     cs-btree       a B+ tree growing by splits, and the page reads of a lookup

   All are object-spec labs (viz.js createLab): canvas + controls + readout +
   one insight sentence. The file is wrapped in a block because every script
   shares one global scope.
   ========================================================================= */
'use strict';
{
const fillRR = (ctx, x, y, w, h, r, fill, stroke, lw = 1.2) => {
  D.rrect(ctx, x, y, w, h, r);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
};
const sup = n => String(n).replace(/[0-9-]/g, c => '⁰¹²³⁴⁵⁶⁷⁸⁹'['0123456789'.indexOf(c)] || '⁻');
function fmtTime(sec) {
  if (!Number.isFinite(sec)) return '> age of the universe';
  if (sec < 1e-6) return `${fmtN(sec * 1e9, sec * 1e9 < 10 ? 1 : 0)} ns`;
  if (sec < 1e-3) return `${fmtN(sec * 1e6, sec * 1e6 < 10 ? 1 : 0)} µs`;
  if (sec < 1) return `${fmtN(sec * 1e3, sec * 1e3 < 10 ? 1 : 0)} ms`;
  if (sec < 120) return `${fmtN(sec, sec < 10 ? 1 : 0)} s`;
  if (sec < 7200) return `${Math.round(sec / 60)} min`;
  if (sec < 172800) return `${Math.round(sec / 3600)} hours`;
  if (sec < 3.15e7 * 2) return `${Math.round(sec / 86400)} days`;
  const y = sec / 3.15e7;
  if (y > 1.4e10) return '> age of the universe';
  return `${y >= 1e6 ? fmtBig(y) : Math.round(y).toLocaleString()} years`;
}
const log10fact = n => {
  if (n < 2) return 0;
  if (n < 1000) { let s = 0; for (let k = 2; k <= n; k++) s += Math.log10(k); return s; }
  return n * Math.log10(n / Math.E) + 0.5 * Math.log10(2 * Math.PI * n);
};
const pow10 = e => e < 15 ? fmtBig(Math.round(Math.pow(10, e))) : `10${sup(Math.floor(e))}`;
const nice = v => { if (v < 100) return Math.max(1, Math.round(v)); const p = Math.pow(10, Math.floor(Math.log10(v)) - 1); return Math.round(v / p) * p; };

/* ============================================================ cs-growth == */
defineLab('cs-growth', {
  title: 'How fast does each complexity class grow?',
  hint: 'Drag <b>n</b>. Each bar is the number of basic steps on a log scale, labelled with the wall-clock time. The dashed line is a one-second budget, the limit most judges and interviewers have in mind.',
  mount(L) {
    const s = { n: 1e5, speed: 1e8 };
    const K = [
      ['O(1)', () => 0, 'hash lookup'],
      ['O(log n)', n => Math.log10(Math.max(1, Math.log2(n))), 'binary search'],
      ['O(n)', n => Math.log10(n), 'one pass'],
      ['O(n log n)', n => Math.log10(n) + Math.log10(Math.max(1, Math.log2(n))), 'sorting'],
      ['O(n²)', n => 2 * Math.log10(n), 'all pairs'],
      ['O(n³)', n => 3 * Math.log10(n), 'triple loop'],
      ['O(2ⁿ)', n => n * Math.log10(2), 'all subsets'],
      ['O(n!)', n => log10fact(n), 'all orderings'],
    ];
    const shown = K.map(() => 0);
    const c = L.canvas(w => Math.min(380, Math.max(300, w * .5)));
    L.slider('input size n', { min: 1, max: 1e9, log: true, value: s.n, fmt: v => fmtBig(nice(v)) }, v => { s.n = nice(v); update(); });
    L.seg('machine', [[1e7, 'Python ≈ 10⁷ steps/s'], [1e8, 'Java / Go / C++ ≈ 10⁸'], [1e9, 'tight C loop ≈ 10⁹']], s.speed, v => { s.speed = v; update(); });
    L.button('n = 20', () => setN(20));
    L.button('n = 10⁵', () => setN(1e5));
    L.button('n = 10⁹', () => setN(1e9));
    const nSlider = L.sliders.querySelector('input');
    function setN(v) { s.n = v; nSlider.value = 1000 * Math.log(v) / Math.log(1e9); nSlider.dispatchEvent(new Event('input')); }
    const anim = L.loop(dt => {
      let moving = false;
      K.forEach(([, f], i) => { const t = Math.min(40, f(s.n)); shown[i] += (t - shown[i]) * Math.min(1, dt * 10); if (Math.abs(t - shown[i]) > .01) moving = true; else shown[i] = t; });
      L.redraw();
      if (!moving) return false;
    });
    const maxN = f => { let lo = 1, hi = 1e12; for (let k = 0; k < 90; k++) { const m = Math.sqrt(lo * hi); f(m) <= Math.log10(s.speed) ? lo = m : hi = m; } return lo; };
    function update() {
      const fits = [3, 4, 6, 7].map(i => [K[i][0], maxN(K[i][1])]);
      L.stats(fits.map(([name, v]) => [`largest n in 1 s · ${name}`, v >= 1e4 ? fmtBig(v) : Math.floor(v).toLocaleString(), 'accent']));
      const t = i => Math.pow(10, K[i][1](s.n)) / s.speed;
      const ok = K.filter((_, i) => t(i) <= 1).map(k => k[0]);
      const fastBad = K.findIndex((_, i) => t(i) > 1);
      L.insight(fastBad < 0
        ? `At n = ${fmtBig(s.n)} every class finishes inside a second. Tiny inputs are where brute force is a perfectly good answer.`
        : `At n = ${fmtBig(s.n)}, ${ok.length ? `<b>${ok[ok.length - 1]}</b> is the slowest class that still fits in one second` : 'nothing fits in one second'}; <b>${K[fastBad][0]}</b> needs ${fmtTime(t(fastBad))}. Read constraints backwards: n ≤ 20 invites O(2ⁿ), n ≤ 10⁴ allows O(n²), n ≤ 10⁶ wants O(n log n) or better, and n ≈ 10⁹ means O(log n) or a formula.`);
      anim.start();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, left = Math.min(150, c.w * .26), right = c.w - 14, top = 26, rowH = (c.h - top - 30) / K.length;
      const X = e => left + (right - left) * Math.min(e, 20) / 20;
      [0, 4, 8, 12, 16, 20].forEach(e => {
        D.line(ctx, X(e), top - 6, X(e), c.h - 26, P.soft, 1);
        D.text(ctx, e ? `10${sup(e)}` : '1', X(e), c.h - 14, { color: P.faint, size: 10, align: 'center', mono: true });
      });
      D.text(ctx, 'steps (log scale) →', 8, 10, { color: P.faint, size: 10 });
      const marks = [[1, '1 s'], [3600, '1 hour'], [3.15e7, '1 year']];
      marks.forEach(([sec, label], k) => {
        const e = Math.log10(s.speed * sec);
        if (e > 20) return;
        ctx.save(); ctx.setLineDash(k ? [2, 4] : [6, 4]);
        D.line(ctx, X(e), top - 8, X(e), c.h - 26, k ? P.faint : P.err, k ? 1 : 1.6); ctx.restore();
        D.text(ctx, label, X(e) + 4, top - 12, { color: k ? P.faint : P.err, size: 10, weight: 650 });
      });
      K.forEach(([name, , ex], i) => {
        const y = top + i * rowH + rowH / 2, e = shown[i], sec = Math.pow(10, K[i][1](s.n)) / s.speed;
        const col = sec <= 1 ? P.ok : sec <= 3600 ? P.accent : P.err;
        D.text(ctx, name, 8, y - 6, { color: P.text, size: c.w < 500 ? 10.5 : 12.5, weight: 700, mono: true });
        if (left > 120) D.text(ctx, ex, 8, y + 9, { color: P.faint, size: 9.5 });
        const w = Math.max(3, X(e) - left);
        fillRR(ctx, left, y - rowH * .32, w, rowH * .64, 4, P.alpha(col, .28), col);
        const off = K[i][1](s.n) > 20;
        const e0 = K[i][1](s.n);
        let lbl = `${off ? '→ ' : ''}${pow10(e0)} step${e0 < .01 ? '' : 's'} · ${fmtTime(sec)}`;
        D.font(ctx, 11, 600, true);
        const outside = right - (left + w) - 12, room = Math.max(outside, w - 16);
        if (ctx.measureText(lbl).width > room) lbl = fmtTime(sec);
        const inside = ctx.measureText(lbl).width > outside;
        D.text(ctx, lbl, inside ? left + w - 8 : left + w + 8, y, { color: inside ? P.text : P.dim, size: 11, align: inside ? 'right' : 'left', mono: true, weight: 600 });
      });
    };
    update();
  },
});

/* ========================================================= cs-amortized == */
defineLab('cs-amortized', {
  title: 'Why append is O(1) “amortized”: growing a dynamic array',
  hint: 'A dynamic array (Python <code>list</code>, Go slice, Java <code>ArrayList</code>) lives in one fixed block. When it is full, the next append allocates a bigger block and <b>copies every element</b>. Press play and compare growth rules.',
  mount(L) {
    const MAX = 96;
    const s = { rule: 'x2', n: 0, cap: 1, costs: [], resizes: 0, copies: 0, flash: 0, lastCopy: 0 };
    const c = L.canvas(w => Math.min(400, Math.max(320, w * .56)));
    L.seg('when full, grow to', [['x2', 'capacity × 2'], ['x1.5', 'capacity × 1.5'], ['+4', 'capacity + 4']], s.rule, v => { s.rule = v; reset(); });
    const run = L.loop(dt => {
      s.acc = (s.acc || 0) + dt;
      if (s.acc > .09) { s.acc = 0; if (!append()) return false; }
      s.flash = Math.max(0, s.flash - dt * 1.5); L.redraw();
    });
    L.playButton(run, ['Append 96 items', 'Pause'], () => { if (s.n >= MAX) reset(); });
    L.button('Append one', () => { append(); });
    L.button('Reset', () => { run.stop(); reset(); });
    function reset() { Object.assign(s, { n: 0, cap: s.rule === '+4' ? 4 : 1, costs: [], resizes: 0, copies: 0, flash: 0, lastCopy: 0 }); update(); }
    function append() {
      if (s.n >= MAX) return false;
      let cost = 1;
      if (s.n === s.cap) {
        const next = s.rule === 'x2' ? s.cap * 2 : s.rule === 'x1.5' ? Math.max(s.cap + 1, Math.floor(s.cap * 1.5)) : s.cap + 4;
        cost += s.n; s.copies += s.n; s.resizes++; s.cap = next; s.flash = 1; s.lastCopy = s.n;
      }
      s.n++; s.costs.push(cost); update();
      return true;
    }
    function update() {
      const total = s.costs.reduce((a, b) => a + b, 0);
      L.stats([['appends', s.n], ['capacity', s.cap], ['resizes', s.resizes, 'accent'], ['elements copied', s.copies],
        ['average cost per append', s.n ? fmtN(total / s.n, 2) : '—', s.n && total / s.n > 3.01 ? 'err' : 'ok'], ['unused slots', s.cap - s.n]]);
      const tips = {
        x2: `Copies happen when the length reaches 1, 2, 4, 8, … and add up to 1 + 2 + 4 + … &lt; 2n. So n appends cost under 3n steps in total: <b>O(1) per append on average</b>, even though a single append that triggers a resize is O(n). The price is memory: right after a resize the array is half empty.`,
        'x1.5': `Growing by 1.5× still gives a geometric series, so the average stays constant (a little higher than with doubling), and it wastes less memory. CPython grows lists by about 1.125× plus a constant, Go slices by 2× until 256 elements then gradually towards 1.25×, and Java's <code>ArrayList</code> by 1.5×.`,
        '+4': `Growing by a <b>constant</b> is the trap: a copy every 4 appends, each copy the size of the whole array, so the total is about n²/8 and the average cost keeps rising with n. That makes append O(n) amortized, and building a list of n items O(n²).`,
      };
      L.insight(tips[s.rule]);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, pad = 14, cols = 48, cell = Math.min(16, (c.w - pad * 2) / cols), capRows = Math.ceil(Math.max(s.cap, 1) / cols);
      D.text(ctx, `memory block: capacity ${s.cap}, length ${s.n}`, pad, 12, { color: P.dim, size: 11, weight: 600 });
      for (let i = 0; i < s.cap; i++) {
        const x = pad + (i % cols) * cell, y = 24 + Math.floor(i / cols) * cell;
        const filled = i < s.n, fresh = s.flash > 0 && i >= s.lastCopy;
        fillRR(ctx, x + 1, y + 1, cell - 2, cell - 2, 2, filled ? P.alpha('accent', .75) : fresh ? P.alpha('err', .18 * s.flash + .04) : 'transparent', filled ? null : P.border);
      }
      if (s.flash > 0) D.text(ctx, `full → new block of ${s.cap}, copied ${s.lastCopy} elements`, pad, 24 + capRows * cell + 12, { color: P.alpha('err', .5 + .5 * s.flash), size: 11, weight: 650 });
      const top = 24 + 3 * 16 + 34, bottom = c.h - 22, h = bottom - top, bw = (c.w - pad * 2 - 34) / MAX, x0 = pad + 34;
      const ymax = s.rule === 'x2' ? 66 : 96;
      const Y = v => bottom - Math.min(v, ymax) / ymax * h;
      D.text(ctx, 'cost of each append (1 write + any copies)', x0, top - 10, { color: P.dim, size: 11, weight: 600 });
      [0, 16, 32, 48, 64, 80, 96].filter(v => v <= ymax).forEach(v => { D.line(ctx, x0, Y(v), c.w - pad, Y(v), P.soft, 1); D.text(ctx, v, x0 - 6, Y(v), { color: P.faint, size: 9.5, align: 'right', mono: true }); });
      let run = 0;
      ctx.beginPath();
      s.costs.forEach((cost, i) => {
        const x = x0 + i * bw;
        fillRR(ctx, x + .5, Y(cost), Math.max(1, bw - 1), bottom - Y(cost), 1, cost > 1 ? P.alpha('err', .8) : P.alpha('accent', .55));
        run += cost;
        const ay = Y(run / (i + 1));
        i ? ctx.lineTo(x + bw / 2, ay) : ctx.moveTo(x + bw / 2, ay);
      });
      ctx.strokeStyle = P.ok; ctx.lineWidth = 2.4; ctx.stroke();
      ctx.save(); ctx.setLineDash([4, 4]); D.line(ctx, x0, Y(3), c.w - pad, Y(3), P.alpha('ok', .7), 1.2); ctx.restore();
      D.text(ctx, '3 per append', c.w - pad, Y(3) - 9, { color: P.alpha('ok', .8), size: 10, align: 'right', weight: 600 });
      D.line(ctx, c.w - pad - 150, top - 10, c.w - pad - 132, top - 10, P.ok, 2.4);
      D.text(ctx, 'average cost so far', c.w - pad - 126, top - 10, { color: P.ok, size: 10.5, weight: 650 });
      D.text(ctx, 'append #', c.w - pad, bottom + 12, { color: P.faint, size: 10, align: 'right' });
    };
    reset();
  },
});

/* ============================================================ cs-master == */
defineLab('cs-master', {
  title: 'Recursion trees and the master theorem',
  hint: 'T(n) = <b>a</b>·T(n/<b>b</b>) + n<sup><b>d</b></sup>: a problem splits into <b>a</b> subproblems of size n/<b>b</b> and does n<sup>d</sup> work to split and combine. Each row is one level of the recursion tree; its bar is the total work on that level.',
  mount(L) {
    const s = { a: 2, b: 2, d: 1, reveal: 1 };
    const presets = { bs: [1, 2, 0, 'Binary search'], ms: [2, 2, 1, 'Merge sort'], tr: [2, 2, 0, 'Tree traversal'], qs: [1, 2, 1, 'Quickselect (average)'], ka: [3, 2, 1, 'Karatsuba multiply'], st: [7, 2, 2, 'Strassen matrix multiply'] };
    const c = L.canvas(w => Math.min(380, Math.max(300, w * .52)));
    const pre = L.seg('example', Object.entries(presets).map(([k, v]) => [k, v[3]]), 'ms', k => { const [a, b, d] = presets[k]; s.a = a; s.b = b; s.d = d; aS.set(a, true); bS.set(b, true); dS.set(d, true); replay(); });
    const aS = L.slider('a — subproblems per call', { min: 1, max: 8, step: 1, value: s.a }, v => { s.a = v; custom(); });
    const bS = L.slider('b — size shrinks by', { min: 2, max: 4, step: 1, value: s.b }, v => { s.b = v; custom(); });
    const dS = L.slider('d — combine work is n^d', { min: 0, max: 3, step: .5, value: s.d }, v => { s.d = v; custom(); });
    const play = L.loop(dt => { s.reveal = Math.min(1, s.reveal + dt / 2.4); L.redraw(); if (s.reveal >= 1) return false; });
    L.playButton(play, ['Build level by level', 'Pause'], () => { if (s.reveal >= 1) s.reveal = 0; });
    function custom() { const hit = Object.entries(presets).find(([, v]) => v[0] === s.a && v[1] === s.b && v[2] === s.d); pre.set(hit ? hit[0] : null, true); update(); }
    function replay() { s.reveal = 0; play.start(); update(); }
    const K = 6;
    const levelWork = i => Math.pow(s.a, i) * Math.pow(Math.pow(s.b, K - i), s.d);
    const fmtExp = x => Math.abs(x - Math.round(x)) < 1e-9 ? `${Math.round(x)}` : x.toFixed(2);
    const nPow = e => e === 0 ? '1' : e === 1 ? 'n' : `n^${fmtExp(e)}`;
    function result() {
      const crit = Math.log(s.a) / Math.log(s.b), bd = Math.pow(s.b, s.d);
      if (Math.abs(s.a - bd) < 1e-9) return { kase: 2, crit, name: 'balanced: every level does the same work', big: s.d === 0 ? 'Θ(log n)' : `Θ(${nPow(s.d)} log n)` };
      if (s.a < bd) return { kase: 3, crit, name: 'root-heavy: work shrinks as you go down', big: `Θ(${nPow(s.d)})` };
      return { kase: 1, crit, name: 'leaf-heavy: work grows as you go down', big: `Θ(${nPow(crit)})` };
    }
    function update() {
      const r = result();
      L.stats([['log_b a', fmtExp(r.crit)], ['d', fmtExp(s.d)], ['ratio a / b^d', fmtN(s.a / Math.pow(s.b, s.d), 2), r.kase === 3 ? 'ok' : r.kase === 1 ? 'err' : 'accent'], ['case (CLRS numbering)', r.kase, 'accent'], ['T(n) grows as', r.big.replace(/^Θ\((.*)\)$/, '$1'), 'accent']]);
      const why = {
        3: `Each level does <b>a / b^d = ${fmtN(s.a / Math.pow(s.b, s.d), 2)}</b> times the work of the level above, less than 1, so the bars shrink geometrically and the <b>root dominates</b>: T(n) = ${r.big}. The recursion is nearly free; the top-level combine step is the cost.`,
        2: `a = b^d, so every level does the same ${nPow(s.d)} work and there are log_b n levels: T(n) = ${r.big}. This is merge sort's shape — n work per level, log n levels.`,
        1: `Each level does <b>${fmtN(s.a / Math.pow(s.b, s.d), 2)}×</b> the level above, so the bottom dominates. There are a^(log_b n) = n^(log_b a) leaves, so T(n) = ${r.big}. To speed this up, cut <b>a</b> (Karatsuba turns 4 multiplications into 3) rather than the combine step.`,
      };
      L.insight(why[r.kase]);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, top = 30, rowH = (c.h - top - 16) / (K + 1), glyphW = Math.min(c.w * .44, 330), barX = glyphW + 30, barW = c.w - barX - 110;
      const works = Array.from({ length: K + 1 }, (_, i) => levelWork(i)), mx = Math.max(...works);
      const shownLv = Math.floor(s.reveal * (K + 1) - 1e-9);
      D.text(ctx, `level (problem size, n = ${s.b}${sup(K)})`, 8, 12, { color: P.dim, size: 10.5, weight: 600 });
      D.text(ctx, 'work on this level', barX, 12, { color: P.dim, size: 10.5, weight: 600 });
      let total = 0;
      works.forEach((wk, i) => {
        if (i > shownLv) return;
        total += wk;
        const y = top + i * rowH, count = Math.pow(s.a, i), size = Math.pow(s.b, K - i);
        D.text(ctx, `${i}`, 8, y + rowH / 2, { color: P.faint, size: 10, mono: true });
        const maxG = Math.floor((glyphW - 100) / 8), draw = Math.min(count, maxG), gw = Math.min(26, Math.max(5, (glyphW - 26) / Math.max(draw, 1) - 2));
        for (let k = 0; k < draw; k++) fillRR(ctx, 22 + k * (gw + 2), y + rowH * .22, gw, rowH * .5, 2, P.alpha(P.series[i % 8], .5), P.series[i % 8], 1);
        if (count > draw) D.text(ctx, `… ${fmtBig(count)} calls`, 22 + draw * (gw + 2) + 4, y + rowH * .47, { color: P.text, size: 10, weight: 650 });
        D.text(ctx, `${fmtBig(count)} × size ${fmtBig(size)}`, 22, y + rowH * .9, { color: P.faint, size: 9.5, mono: true });
        const w = Math.max(2, wk / mx * barW);
        fillRR(ctx, barX, y + rowH * .2, w, rowH * .56, 4, P.alpha(P.series[i % 8], .35), P.series[i % 8]);
        D.text(ctx, fmtBig(wk), barX + w + 6, y + rowH * .48, { color: P.text, size: 10.5, mono: true, weight: 600 });
      });
      if (shownLv >= K) D.text(ctx, `total ≈ ${fmtBig(total)}`, c.w - 8, c.h - 8, { color: P.accent, size: 11.5, align: 'right', weight: 700, mono: true });
    };
    update();
  },
});

/* ========================================================= cs-hashtable == */
defineLab('cs-hashtable', {
  title: 'Inside a hash table: collisions, load factor and resizing',
  hint: 'Keys are small integers and <b>hash(k) = k mod capacity</b>, so you can check every step by hand. Insert until keys collide, then compare <b>chaining</b> with <b>linear probing</b>.',
  mount(L) {
    const r = rng(42);
    const s = { mode: 'probe', thr: .75, cap: 8, slots: [], keys: [], resizes: 0, anim: null, msg: '' };
    const c = L.canvas(w => Math.min(300, Math.max(230, w * .4)));
    L.seg('collisions', [['probe', 'Linear probing (open addressing)'], ['chain', 'Separate chaining']], s.mode, v => { s.mode = v; reset(); });
    L.seg('resize when load factor >', [[.5, '0.5'], [.75, '0.75'], [9, 'never']], s.thr, v => { s.thr = v; reset(); });
    L.button('Insert a key', () => insert(fresh()), 'primary');
    L.button('Insert 5', () => { for (let i = 0; i < 5; i++) insert(fresh(), i < 4); });
    L.button('Look up a key', () => { if (s.keys.length) lookup(s.keys[Math.floor(r() * s.keys.length)]); });
    L.button('Look up a missing key', () => lookup(fresh()));
    L.button('Delete a key', () => { if (s.keys.length) del(s.keys[Math.floor(r() * s.keys.length)]); });
    L.button('Reset', () => reset());
    const tick = L.loop(dt => { if (!s.anim) return false; s.anim.t += dt * 3.2; L.redraw(); if (s.anim.t > s.anim.path.length + 1.5) { s.anim.done = true; return false; } });
    const h = (k, cap = s.cap) => k % cap;
    function fresh() { let k; do k = Math.floor(r() * 100); while (s.keys.includes(k)); return k; }
    function reset() { s.cap = 8; s.resizes = 0; s.keys = []; s.anim = null; s.msg = ''; s.slots = s.mode === 'chain' ? Array.from({ length: s.cap }, () => []) : Array(s.cap).fill(null); update(); }
    function place(k) {
      if (s.mode === 'chain') { const b = h(k); s.slots[b].push(k); return { path: [b], depth: s.slots[b].length }; }
      let i = h(k); const path = [i];
      while (s.slots[i] !== null && s.slots[i] !== 'T') { i = (i + 1) % s.cap; path.push(i); }
      s.slots[i] = k; return { path };
    }
    function rebuild(cap) {
      s.cap = cap;
      s.slots = s.mode === 'chain' ? Array.from({ length: cap }, () => []) : Array(cap).fill(null);
      s.keys.forEach(place);
    }
    function insert(k, quiet) {
      if (s.mode === 'probe' && s.keys.length >= s.cap) { s.msg = 'The table is full: open addressing cannot hold more keys than slots. Allow resizing.'; update(); return; }
      if (s.keys.length >= 60) { s.msg = 'That is enough keys to see the pattern. Reset to try another setting.'; update(); return; }
      let grew = '';
      if ((s.keys.length + 1) / s.cap > s.thr) { const old = s.cap; rebuild(s.cap * 2); s.resizes++; grew = ` The load factor would pass ${s.thr}, so the table doubled from ${old} to ${s.cap} slots and <b>every key was re-hashed</b> into its new position (an O(n) step that is rare enough to stay O(1) amortized).`; }
      s.keys.push(k);
      const { path } = place(k);
      s.anim = { path: s.mode === 'chain' ? [path[0]] : path, t: 0, key: k, kind: 'insert', found: true };
      const probes = s.mode === 'probe' ? path.length : s.slots[path[0]].length;
      s.msg = s.mode === 'chain'
        ? `insert ${k}: ${k} mod ${s.cap} = ${h(k)}. ${probes > 1 ? `Bucket ${h(k)} already held ${probes - 1} key${probes > 2 ? 's' : ''}, so ${k} joins its chain.` : 'The bucket was empty.'}${grew}`
        : `insert ${k}: ${k} mod ${s.cap} = ${h(k)}. ${path.length > 1 ? `Slot ${h(k)} was taken, so it probed ${path.length - 1} more slot${path.length > 2 ? 's' : ''} and landed in ${path[path.length - 1]}.` : 'The slot was free.'}${grew}`;
      if (!quiet) tick.start();
      update();
    }
    function lookup(k) {
      if (s.mode === 'chain') {
        const b = h(k), chain = s.slots[b], at = chain.indexOf(k);
        s.anim = { path: [b], t: 0, key: k, kind: 'lookup', found: at >= 0, cmp: at >= 0 ? at + 1 : chain.length };
        s.msg = `look up ${k}: go to bucket ${b}, compare along the chain: ${at >= 0 ? `found after ${at + 1} comparison${at ? 's' : ''}` : `${chain.length} comparison${chain.length === 1 ? '' : 's'}, not there`}.`;
      } else {
        let i = h(k); const path = [i];
        while (s.slots[i] !== null && s.slots[i] !== k && path.length <= s.cap) { i = (i + 1) % s.cap; path.push(i); }
        const found = s.slots[i] === k;
        s.anim = { path, t: 0, key: k, kind: 'lookup', found };
        s.msg = `look up ${k}: start at ${k} mod ${s.cap} = ${h(k)} and walk right until the key or an <b>empty</b> slot: ${path.length} probe${path.length > 1 ? 's' : ''}, ${found ? 'found' : 'not present'}.${path.some(j => s.slots[j] === 'T') ? ' It walked <b>past a tombstone</b>: a deleted slot cannot stop the search, or keys placed after it would vanish.' : ''}`;
      }
      tick.start(); update();
    }
    function del(k) {
      s.keys = s.keys.filter(x => x !== k);
      if (s.mode === 'chain') { const b = h(k); s.slots[b] = s.slots[b].filter(x => x !== k); s.msg = `delete ${k}: unlink it from bucket ${b}'s chain. Nothing else moves.`; s.anim = { path: [b], t: 0, key: k, kind: 'delete', found: true }; }
      else {
        let i = h(k); const path = [i];
        while (s.slots[i] !== k) { i = (i + 1) % s.cap; path.push(i); }
        s.slots[i] = 'T';
        s.anim = { path, t: 0, key: k, kind: 'delete', found: true };
        s.msg = `delete ${k}: its slot becomes a <b>tombstone</b> (†), not empty. Emptying it would break the probe chain for any key that was pushed past this slot. Tombstones are cleared at the next resize.`;
      }
      tick.start(); update();
    }
    function avgProbes() {
      if (!s.keys.length) return 0;
      if (s.mode === 'chain') return s.slots.reduce((a, ch) => a + ch.reduce((x, _, i) => x + i + 1, 0), 0) / s.keys.length;
      return s.keys.reduce((a, k) => { let i = h(k), n = 1; while (s.slots[i] !== k) { i = (i + 1) % s.cap; n++; } return a + n; }, 0) / s.keys.length;
    }
    function worst() {
      if (s.mode === 'chain') return Math.max(0, ...s.slots.map(ch => ch.length));
      let best = 0, run = 0;
      for (let i = 0; i < s.cap * 2; i++) { const v = s.slots[i % s.cap]; run = v !== null ? run + 1 : 0; best = Math.max(best, Math.min(run, s.cap)); }
      return best;
    }
    function update() {
      const lf = s.keys.length / s.cap;
      L.stats([['keys', s.keys.length], ['capacity', s.cap], ['load factor', fmtN(lf, 2), lf > .8 ? 'err' : 'accent'], ['avg probes to find a key', fmtN(avgProbes(), 2)],
        [s.mode === 'chain' ? 'longest chain' : 'longest cluster', worst(), worst() > 4 ? 'err' : ''], ['resizes', s.resizes],
        s.mode === 'probe' ? ['tombstones', s.slots.filter(x => x === 'T').length] : null]);
      const theory = s.mode === 'probe'
        ? `Linear probing keeps keys in one flat array (cache-friendly), but occupied runs merge into <b>clusters</b>: expected probes for a hit ≈ ½(1 + 1/(1−α)) and for a miss ≈ ½(1 + 1/(1−α)²), which explodes as α → 1. Real tables resize early — CPython's dict at ⅔ full (with perturbed, not linear, probing), Go 1.24+ uses Swiss tables with 8-slot groups.`
        : `Chaining never runs out of room, and a lookup costs 1 + α/2 comparisons on average, but every node is a separate allocation and pointer chase. Java's HashMap chains, resizes at 0.75, and turns a bucket with 8+ entries into a red-black tree so a flood of colliding keys costs O(log n), not O(n).`;
      L.insight(`${s.msg ? s.msg + '<br><br>' : ''}${theory}`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, pad = 12, cw = Math.min(58, (c.w - pad * 2) / s.cap), ch = 34, y = 44, x0 = (c.w - cw * s.cap) / 2;
      const small = cw < 26;
      D.text(ctx, `hash(k) = k mod ${s.cap}`, pad, 14, { color: P.dim, size: 11, mono: true, weight: 600 });
      const a = s.anim, step = a ? Math.floor(a.t) : -1;
      for (let i = 0; i < s.cap; i++) {
        const x = x0 + i * cw, onPath = a && a.path.indexOf(i) >= 0 && a.path.indexOf(i) <= step;
        const isEnd = a && a.path[Math.min(step, a.path.length - 1)] === i && step >= a.path.length - 1;
        const v = s.mode === 'probe' ? s.slots[i] : null;
        const col = isEnd ? (a.found ? P.ok : P.err) : onPath ? P.accent : P.border;
        fillRR(ctx, x + 2, y, cw - 4, ch, 5, onPath ? P.alpha(col, .22) : v === 'T' ? P.alpha('faint', .12) : v !== null && v !== undefined ? P.alpha('accent', .12) : P.surface2, col, onPath ? 2 : 1);
        if (s.mode === 'probe' && v !== null) D.text(ctx, v === 'T' ? '†' : v, x + cw / 2, y + ch / 2, { color: v === 'T' ? P.faint : P.text, size: small ? 9.5 : 13, align: 'center', mono: true, weight: 650 });
        if (!small || i % 2 === 0) D.text(ctx, i, x + cw / 2, y - 9, { color: P.faint, size: 9.5, align: 'center', mono: true });
        if (s.mode === 'chain') {
          const chain = s.slots[i];
          chain.slice(0, 5).forEach((k, j) => {
            const ny = y + ch + 14 + j * 30;
            D.line(ctx, x + cw / 2, ny - 14, x + cw / 2, ny, P.strong, 1);
            const hit = a && a.path[0] === i && step >= 0 && a.kind === 'lookup' && a.found && j === a.cmp - 1;
            fillRR(ctx, x + 4, ny, cw - 8, 22, 4, hit ? P.alpha('ok', .3) : P.surface, hit ? P.ok : P.strong);
            D.text(ctx, k, x + cw / 2, ny + 11, { color: P.text, size: small ? 9 : 12, align: 'center', mono: true, weight: 600 });
          });
          if (chain.length > 5) D.text(ctx, `+${chain.length - 5}`, x + cw / 2, y + ch + 14 + 5 * 30 + 6, { color: P.err, size: 10, align: 'center', weight: 700 });
        }
      }
      if (a && s.mode === 'probe') {
        for (let k = 1; k <= Math.min(step, a.path.length - 1); k++) {
          const i0 = a.path[k - 1], i1 = a.path[k];
          if (i1 < i0) continue;
          const xa = x0 + i0 * cw + cw / 2, xb = x0 + i1 * cw + cw / 2;
          ctx.beginPath(); ctx.moveTo(xa, y + ch + 4); ctx.quadraticCurveTo((xa + xb) / 2, y + ch + 22, xb, y + ch + 4);
          ctx.strokeStyle = P.accent; ctx.lineWidth = 1.6; ctx.stroke();
        }
        D.text(ctx, `${a.kind} ${a.key}`, pad, c.h - 14, { color: P.accent, size: 11.5, mono: true, weight: 700 });
      }
      if (s.mode === 'probe') {
        const lf = s.keys.length / s.cap, gx = c.w - 180, gy = c.h - 58;
        D.text(ctx, 'expected probes on a miss', gx, gy - 8, { color: P.faint, size: 10 });
        ctx.beginPath();
        for (let q = 0; q <= 90; q++) { const al = q / 100, v = .5 * (1 + 1 / ((1 - al) ** 2)); const px = gx + al * 170, py = gy + 44 - Math.min(v, 50) / 50 * 44; q ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }
        ctx.strokeStyle = P.dim; ctx.lineWidth = 1.4; ctx.stroke();
        const v = .5 * (1 + 1 / ((1 - Math.min(lf, .9)) ** 2));
        D.dot(ctx, gx + Math.min(lf, .9) * 170, gy + 44 - Math.min(v, 50) / 50 * 44, 4.5, lf > .8 ? P.err : P.accent);
        D.text(ctx, `α=${fmtN(lf, 2)}`, gx + Math.min(lf, .9) * 170 - 8, gy + 44 - Math.min(v, 50) / 50 * 44 - 10, { color: P.text, size: 10, align: 'right', mono: true });
      }
    };
    reset();
  },
});

/* ============================================================== cs-heap == */
defineLab('cs-heap', {
  title: 'A binary heap is a tree stored in an array',
  hint: 'Node <b>i</b> has children <b>2i+1</b> and <b>2i+2</b> and parent <b>(i−1)//2</b>, so no pointers are needed. The rule: every parent ≤ its children. Watch push sift up and pop sift down.',
  mount(L) {
    const r = rng(9);
    const s = { a: [], steps: [], hl: null, cmp: 0, swaps: 0, msg: '', acc: 0 };
    const c = L.canvas(w => Math.min(340, Math.max(280, w * .46)));
    L.button('Push a random value', () => push(Math.floor(r() * 99) + 1), 'primary');
    L.button('Pop the minimum', () => pop());
    L.button('Build a heap from 15 values (heapify)', () => build());
    L.button('Clear', () => { s.a = []; s.steps = []; s.hl = null; s.msg = ''; update(); });
    const run = L.loop(dt => {
      s.acc += dt;
      if (s.acc < .55) { L.redraw(); return; }
      s.acc = 0;
      const st = s.steps.shift();
      if (!st) { s.hl = null; L.redraw(); update(); return false; }
      if (st.type === 'swap') { [s.a[st.i], s.a[st.j]] = [s.a[st.j], s.a[st.i]]; s.swaps++; }
      if (st.type === 'cmp') s.cmp++;
      if (st.type === 'set') s.a = st.a.slice();
      s.hl = st;
      update(); L.redraw();
    });
    const busy = () => s.steps.length > 0;
    function plan(work) { s.cmp = 0; s.swaps = 0; s.steps = work; s.acc = .5; run.start(); }
    function siftUp(a, i, out) {
      while (i > 0) { const p = (i - 1) >> 1; out.push({ type: 'cmp', i, j: p }); if (a[p] <= a[i]) break; out.push({ type: 'swap', i, j: p }); [a[p], a[i]] = [a[i], a[p]]; i = p; }
    }
    function siftDown(a, i, n, out) {
      for (;;) {
        const l = 2 * i + 1, rr = l + 1; let m = i;
        if (l < n) { out.push({ type: 'cmp', i: l, j: m }); if (a[l] < a[m]) m = l; }
        if (rr < n) { out.push({ type: 'cmp', i: rr, j: m }); if (a[rr] < a[m]) m = rr; }
        if (m === i) return;
        out.push({ type: 'swap', i, j: m }); [a[i], a[m]] = [a[m], a[i]]; i = m;
      }
    }
    function push(v) {
      if (busy() || s.a.length >= 31) return;
      const a = s.a.slice(); a.push(v); s.a.push(v);
      const out = [{ type: 'mark', i: a.length - 1, j: a.length - 1 }]; siftUp(a, a.length - 1, out);
      s.msg = `push ${v}: append at index ${a.length - 1} (the next free leaf, keeping the tree complete), then <b>sift up</b> — swap with the parent while smaller. At most one swap per level: O(log n).`;
      plan(out);
    }
    function pop() {
      if (busy() || !s.a.length) return;
      const min = s.a[0], a = s.a.slice(), last = a.pop();
      const out = [];
      if (a.length) { a[0] = last; out.push({ type: 'set', a: a.slice(), i: 0, j: 0 }); siftDown(a, 0, a.length, out); }
      else out.push({ type: 'set', a: [], i: -1, j: -1 });
      s.msg = `pop returns ${min}, the root. The last leaf (${last}) moves to the root to keep the shape complete, then <b>sifts down</b> — swap with the smaller child until neither child is smaller. O(log n).`;
      plan(out);
    }
    function build() {
      if (busy()) return;
      const a = Array.from({ length: 15 }, () => Math.floor(r() * 99) + 1);
      const out = [{ type: 'set', a: a.slice(), i: -1, j: -1 }], w = a.slice();
      for (let i = (w.length >> 1) - 1; i >= 0; i--) { out.push({ type: 'mark', i, j: i }); siftDown(w, i, w.length, out); }
      s.a = [];
      s.msg = `<b>heapify</b> (Floyd): drop 15 values in any order, then sift down every parent from the last one (index ${(a.length >> 1) - 1}) back to the root. Half the nodes are leaves and never move, a quarter move at most one level… the total is O(n), cheaper than n pushes at O(n log n). This is what <code>heapq.heapify</code> does.`;
      plan(out);
    }
    function update() {
      const n = s.a.length;
      L.stats([['size', n], ['height', n ? Math.floor(Math.log2(n)) + 1 : 0], ['comparisons', s.cmp, 'accent'], ['swaps', s.swaps, 'accent'], ['minimum (root)', n ? s.a[0] : '—', 'ok']]);
      L.insight(s.msg || 'Push a few values, then pop. The array below the tree is the whole data structure: the tree is only a way of reading it.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, n = s.a.length, treeH = c.h - 74, levels = Math.max(1, Math.floor(Math.log2(Math.max(1, n))) + 1);
      const pos = i => { const l = Math.floor(Math.log2(i + 1)), k = i - (2 ** l - 1), cnt = 2 ** l; return [c.w * (k + .5) / cnt, 22 + l * Math.min(62, (treeH - 30) / Math.max(1, levels - 1 || 1))]; };
      const hl = s.hl, isHl = i => hl && (hl.i === i || hl.j === i);
      for (let i = 1; i < n; i++) { const [x, y] = pos(i), [px, py] = pos((i - 1) >> 1); D.line(ctx, x, y, px, py, P.strong, 1.2); }
      const R = Math.min(17, c.w / 2 ** levels / 2.2 + 6);
      for (let i = 0; i < n; i++) {
        const [x, y] = pos(i), on = isHl(i);
        const col = on ? (hl.type === 'swap' ? P.err : P.accent) : i === 0 ? P.ok : P.border;
        D.dot(ctx, x, y, R, on ? P.alpha(col, .3) : P.surface2, col, on ? 2.4 : 1.4);
        D.text(ctx, s.a[i], x, y, { color: P.text, size: R > 13 ? 12.5 : 10, align: 'center', mono: true, weight: 700 });
      }
      const cw = Math.min(34, (c.w - 20) / Math.max(n, 15)), ax = (c.w - cw * Math.max(n, 1)) / 2, ay = c.h - 44;
      D.text(ctx, 'the array', ax, ay - 10, { color: P.faint, size: 10 });
      for (let i = 0; i < n; i++) {
        const on = isHl(i), col = on ? (hl.type === 'swap' ? P.err : P.accent) : P.border;
        fillRR(ctx, ax + i * cw + 1, ay, cw - 2, 24, 4, on ? P.alpha(col, .3) : P.surface2, col);
        D.text(ctx, s.a[i], ax + i * cw + cw / 2, ay + 12, { color: P.text, size: cw > 24 ? 11.5 : 9, align: 'center', mono: true, weight: 650 });
        D.text(ctx, i, ax + i * cw + cw / 2, ay + 34, { color: P.faint, size: 9, align: 'center', mono: true });
      }
    };
    [40, 12, 67, 5, 31, 22, 88].forEach(v => { s.a.push(v); const tmp = []; siftUp(s.a, s.a.length - 1, tmp); });
    update();
  },
});

/* ============================================================= cs-btree == */
defineLab('cs-btree', {
  title: 'A B+ tree grows by splitting, and stays shallow',
  hint: 'Each box is one disk page. Keys live in the <b>leaves</b> (linked left to right for range scans); inner nodes only route. When a node overflows it splits in two and pushes a separator up — the tree grows at the root, so every leaf stays at the same depth.',
  mount(L) {
    const r = rng(5);
    const s = { m: 3, root: null, count: 0, splits: 0, path: [], fresh: new Set(), msg: '', seq: 0, fade: 0 };
    const c = L.canvas(w => Math.min(340, Math.max(260, w * .44)));
    L.seg('max keys per page', [[3, '3'], [4, '4'], [5, '5']], s.m, v => { s.m = v; reset(); });
    L.button('Insert a random key', () => insert(fresh()), 'primary');
    L.button('Insert 10 increasing keys', () => { for (let i = 0; i < 10; i++) insert(s.seq += 3 + Math.floor(r() * 3), true); s.msg = 'Increasing keys always land in the rightmost leaf, so splits happen only on the right edge and leaves are left about half full. Databases special-case this (PostgreSQL and InnoDB split an append-heavy rightmost page unevenly) because auto-increment IDs and timestamps do exactly this.'; update(); });
    L.button('Search for a key', () => search());
    L.button('Reset', () => reset());
    const fade = L.loop(dt => { s.fade = Math.max(0, s.fade - dt * .6); L.redraw(); if (!s.fade) return false; });
    const mk = leaf => ({ leaf, keys: [], kids: [], next: null });
    let used = new Set();
    function fresh() { let k; do k = 1 + Math.floor(r() * 199); while (used.has(k)); return k; }
    function reset() { s.root = mk(true); s.count = 0; s.splits = 0; s.path = []; s.fresh = new Set(); s.seq = 200; used = new Set(); s.msg = ''; [50, 20, 80, 35, 65, 10].forEach(k => insert(k, true)); s.msg = ''; s.fresh = new Set(); s.path = []; update(); }
    function insert(k, quiet) {
      if (s.count >= (c.w < 520 ? 24 : 36)) { s.msg = 'That is plenty to see the shape. Reset to start again.'; update(); return; }
      if (used.has(k)) return;
      used.add(k); s.count++;
      const path = [], newly = [];
      const split = ins(s.root, k, path, newly);
      if (split) { const nr = mk(false); nr.keys = [split.key]; nr.kids = [s.root, split.right]; s.root = nr; newly.push(nr); }
      s.path = path; s.fresh = new Set(newly);
      if (!quiet) {
        s.msg = newly.length
          ? `insert ${k}: the leaf overflowed (more than ${s.m} keys), so it split in two and a separator went up to the parent${split ? ', which also overflowed — the root split and the tree grew one level taller' : ''}. ${s.splits} split${s.splits === 1 ? '' : 's'} so far.`
          : `insert ${k}: routed down ${path.length} page${path.length > 1 ? 's' : ''} to its leaf, which had room. No split.`;
        s.fade = 1; fade.start();
      }
      update();
    }
    function ins(node, k, path, newly) {
      path.push(node);
      if (node.leaf) {
        let i = 0; while (i < node.keys.length && node.keys[i] < k) i++;
        node.keys.splice(i, 0, k);
        if (node.keys.length <= s.m) return null;
        const mid = Math.ceil(node.keys.length / 2), right = mk(true);
        right.keys = node.keys.splice(mid); right.next = node.next; node.next = right;
        s.splits++; newly.push(node, right);
        return { key: right.keys[0], right };
      }
      let i = 0; while (i < node.keys.length && k >= node.keys[i]) i++;
      const sp = ins(node.kids[i], k, path, newly);
      if (!sp) return null;
      node.keys.splice(i, 0, sp.key); node.kids.splice(i + 1, 0, sp.right);
      if (node.keys.length <= s.m) return null;
      const mid = Math.floor(node.keys.length / 2), right = mk(false), up = node.keys[mid];
      right.keys = node.keys.splice(mid + 1); node.keys.pop();
      right.kids = node.kids.splice(mid + 1);
      s.splits++; newly.push(node, right);
      return { key: up, right };
    }
    function search() {
      const keys = [...used]; if (!keys.length) return;
      const k = keys[Math.floor(r() * keys.length)], path = [];
      let n = s.root;
      for (;;) { path.push(n); if (n.leaf) break; let i = 0; while (i < n.keys.length && k >= n.keys[i]) i++; n = n.kids[i]; }
      s.path = path; s.fresh = new Set(); s.fade = 1; fade.start();
      s.msg = `search ${k}: ${path.length} page read${path.length > 1 ? 's' : ''}, one per level — at each inner page, follow the child whose range holds ${k}. A range query (say ${k}…${k + 30}) would then walk right along the leaf links without going back up.`;
      update();
    }
    const height = () => { let h = 1, n = s.root; while (!n.leaf) { n = n.kids[0]; h++; } return h; };
    const nodes = () => { let q = [s.root], all = 0; while (q.length) { const n = q.shift(); all++; q.push(...n.kids); } return all; };
    function update() {
      const H = height();
      L.stats([['keys', s.count], ['height (page reads per lookup)', H, 'accent'], ['pages', nodes()], ['splits', s.splits]]);
      const fan = 300, rows = 1e9;
      L.insight(`${s.msg ? s.msg + '<br><br>' : ''}Here a page holds ${s.m} keys, so the tree is tall for its size. A real 8–16 KB page holds a few hundred keys: with a fanout of ${fan}, a billion rows need a height of only <b>${Math.ceil(Math.log(rows) / Math.log(fan))}</b>, and the top levels stay in the buffer pool — so an indexed lookup is usually one or two actual disk reads.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, levels = [];
      let q = [s.root];
      while (q.length) { levels.push(q); q = q.flatMap(n => n.kids); }
      const leaves = levels[levels.length - 1];
      const totalKeys = leaves.reduce((a, n) => a + n.keys.length, 0);
      const gap = clamp((c.w - 20) * .22 / Math.max(1, leaves.length), 4, 12), cw = Math.max(11, Math.min(30, (c.w - 20 - gap * (leaves.length - 1)) / Math.max(1, totalKeys)));
      const nodeW = n => Math.max(1, n.keys.length) * cw + 6;
      const pos = new Map();
      let x = (c.w - (leaves.reduce((a, n) => a + nodeW(n), 0) + gap * (leaves.length - 1))) / 2;
      const rowH = Math.min(72, (c.h - 40) / Math.max(1, levels.length - 1 || 1));
      const yOf = d => 16 + d * (levels.length > 1 ? rowH : 0);
      leaves.forEach(n => { pos.set(n, { x, y: yOf(levels.length - 1), w: nodeW(n) }); x += nodeW(n) + gap; });
      for (let d = levels.length - 2; d >= 0; d--) levels[d].forEach(n => {
        const a = pos.get(n.kids[0]), b = pos.get(n.kids[n.kids.length - 1]), cx = (a.x + b.x + b.w) / 2, w = nodeW(n);
        pos.set(n, { x: cx - w / 2, y: yOf(d), w });
      });
      const hh = 26;
      levels.forEach(lv => lv.forEach(n => {
        const p = pos.get(n);
        n.kids.forEach((k, i) => { const q2 = pos.get(k); const sx = p.x + 3 + i * cw; D.line(ctx, Math.min(sx, p.x + p.w - 3), p.y + hh, q2.x + q2.w / 2, q2.y, s.path.includes(k) && s.path.includes(n) ? P.alpha('accent', .4 + .6 * s.fade) : P.strong, s.path.includes(k) && s.path.includes(n) ? 2.2 : 1); });
      }));
      leaves.forEach((n, i) => { if (i < leaves.length - 1) { const a = pos.get(n), b = pos.get(leaves[i + 1]); ctx.save(); ctx.setLineDash([3, 3]); D.arrow(ctx, a.x + a.w, a.y + hh / 2, b.x, b.y + hh / 2, P.faint, 1.1, 6); ctx.restore(); } });
      levels.forEach(lv => lv.forEach(n => {
        const p = pos.get(n), onPath = s.path.includes(n), isNew = s.fresh.has(n);
        const col = isNew ? P.err : onPath ? P.accent : n.leaf ? P.border : P.strong;
        const glow = isNew || onPath ? s.fade : 0;
        fillRR(ctx, p.x, p.y, p.w, hh, 5, glow ? P.alpha(col, .1 + .25 * glow) : n.leaf ? P.surface2 : P.surface, glow ? col : n.leaf ? P.border : P.strong, glow ? 2 : 1.2);
        n.keys.forEach((k, i) => {
          if (i) D.line(ctx, p.x + 3 + i * cw, p.y + 4, p.x + 3 + i * cw, p.y + hh - 4, P.soft, 1);
          D.text(ctx, k, p.x + 3 + i * cw + cw / 2, p.y + hh / 2, { color: n.leaf ? P.text : P.dim, size: Math.min(11.5, Math.max(8, cw / 1.75)), align: 'center', mono: true, weight: n.leaf ? 650 : 500 });
        });
      }));
      D.text(ctx, 'leaves: every key, linked in order →', 10, c.h - 8, { color: P.faint, size: 10 });
    };
    reset();
  },
});
}
