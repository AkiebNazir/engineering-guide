/* ============================================================================
   Maths for CS Engineers labs, part 3: probability, statistics, calculus.

     math-birthday    the birthday paradox, and hash collisions in N buckets
     math-montecarlo  estimating π with random darts: the law of large numbers
     math-clt         the central limit theorem: averages become bell curves
     math-percentiles latency percentiles vs the mean, and fan-out tails
     math-pvalue      a coin-fairness test: what a p-value is and is not
     math-derivative  the derivative as the limit of secant slopes
     math-riemann     areas by rectangles: left, right, midpoint, trapezoid
     math-taylor      Taylor polynomials closing in on sin, cos, eˣ, ln(1+x)
     math-newton      Newton's method: tangent lines, digits doubling

   Object-spec labs (viz.js createLab), wrapped in a block for scope.
   ========================================================================= */
'use strict';
{
const fillRR = (ctx, x, y, w, h, r, fill, stroke, lw = 1.2) => {
  D.rrect(ctx, x, y, w, h, r);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
};
const vline = (ctx, x, y0, y1, col, label, P, dy = 0) => {
  ctx.save(); ctx.setLineDash([4, 3]); D.line(ctx, x, y0, x, y1, col, 1.5); ctx.restore();
  if (label) D.text(ctx, label, x + 4, y0 + 8 + dy, { color: col, size: 10.5, weight: 700 });
};

/* ========================================================= math-birthday == */
defineLab('math-birthday', {
  title: 'The birthday paradox and hash collisions',
  hint: 'How many people before two share a birthday is more likely than not? Guess first, then drag. Switch the “days” to hash-table buckets to see the same maths for collisions.',
  mount(L) {
    const BK = { 365: [365, 100, '365 days'], 65536: [65536, 1000, '2¹⁶ buckets'], 4294967296: [4294967296, 200000, '2³² buckets (32-bit hash)'] };
    const s = { N: 365, n: 23, room: null, rooms: 0, hits: 0 };
    const c = L.canvas(w => w < 520 ? 360 : 300);
    const probCurve = () => {
      const [N, xmax] = BK[s.N], out = new Float64Array(xmax + 1);
      let logNo = 0; out[0] = 0;
      for (let k = 1; k <= xmax; k++) { logNo += Math.log1p(-(k - 1) / N); out[k] = 1 - Math.exp(logNo); }
      return out;
    };
    let curve = probCurve();
    L.seg('buckets', Object.entries(BK).map(([k, v]) => [k, v[2]]), String(s.N), v => {
      s.N = +v; curve = probCurve(); s.room = null; s.rooms = s.hits = 0;
      L.clearDyn(); addSlider(); nSl.set(Math.round(1.1774 * Math.sqrt(s.N)), false);
    });
    let nSl;
    const addSlider = () => { nSl = L.slider('people (items)', { min: 1, max: BK[s.N][1], log: s.N > 365, value: s.n, dyn: true, fmt: v => Math.round(v).toLocaleString() }, v => { s.n = Math.round(v); s.room = null; update(); }); };
    addSlider();
    const sample = () => { const seen = new Map(); for (let i = 0; i < s.n; i++) { const d = Math.floor(Math.random() * s.N); seen.set(d, (seen.get(d) || 0) + 1); } return seen; };
    L.button('Fill one room', () => { s.room = sample(); s.rooms++; if ([...s.room.values()].some(v => v > 1)) s.hits++; update(); });
    L.button('Simulate 1,000 rooms', () => { for (let r = 0; r < 1000; r++) { const m = sample(); s.rooms++; if ([...m.values()].some(v => v > 1)) s.hits++; if (r === 999) s.room = m; } update(); });
    function update() {
      const p = curve[s.n], half = curve.findIndex(v => v >= .5);
      const shared = s.room ? [...s.room.values()].filter(v => v > 1).length : 0;
      L.stats([['people', s.n.toLocaleString()], ['pairs n(n−1)/2', (s.n * (s.n - 1) / 2).toLocaleString()], ['P(some pair collides)', `${(p * 100).toFixed(1)}%`, 'accent'],
        ['50% reached at', `${half.toLocaleString()} ≈ 1.18·√N`], s.rooms ? ['simulated', `${s.hits} / ${s.rooms} rooms = ${(100 * s.hits / s.rooms).toFixed(1)}%`, 'ok'] : null,
        s.room && s.N === 365 ? ['this room', shared ? `${shared} shared day${shared > 1 ? 's' : ''}` : 'no match'] : null]);
      L.insight(s.N === 365
        ? `Only <b>23 people</b> give a 50.7% chance of a shared birthday, and 70 people 99.9%. Intuition compares each person to <i>you</i>, but a collision can happen between <b>any pair</b>, and the number of pairs grows like n²/2: 23 people make 253 pairs. The chance of no match is (1 − 1/365)(1 − 2/365)…, and it collapses fast.`
        : `The same maths for hashing: with N buckets, collisions become likely after about <b>√N</b> items, not N. A 32-bit hash gives a 50% collision chance after only ~77,000 items — which is why hash tables resolve collisions instead of hoping to avoid them, and why unique IDs use 122+ random bits (UUIDv4) rather than 32.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, narrow = c.w < 520, xmax = BK[s.N][1];
      const pw = s.N === 365 && !narrow ? c.w * .56 : c.w, ph = s.N === 365 && narrow ? c.h * .55 : c.h;
      const v = D.view({ w: pw, h: ph }, { x0: 0, x1: xmax, y0: 0, y1: 1, pad: 18, padL: 40, padB: 28 });
      const ticks = [0, xmax / 4, xmax / 2, 3 * xmax / 4, xmax];
      D.axes(ctx, v, P, { xTicks: ticks, yTicks: [0, .5, 1], fmtY: t => `${t * 100}%`, fmtX: t => t >= 1000 ? `${t / 1000}k` : t });
      ctx.beginPath();
      const step = Math.max(1, Math.floor(xmax / 400));
      for (let k = 0; k <= xmax; k += step) { const px = v.sx(k), py = v.sy(curve[k]); k ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }
      ctx.strokeStyle = P.accent; ctx.lineWidth = 2.4; ctx.stroke();
      ctx.save(); ctx.setLineDash([4, 4]); D.line(ctx, v.sx(0), v.sy(.5), v.sx(xmax), v.sy(.5), P.faint, 1); ctx.restore();
      D.line(ctx, v.sx(s.n), v.sy(0), v.sx(s.n), v.sy(curve[s.n]), P.alpha('accent', .5), 1.2);
      D.dot(ctx, v.sx(s.n), v.sy(curve[s.n]), 6, P.accent, P.bg, 2);
      D.text(ctx, `${(curve[s.n] * 100).toFixed(1)}%`, v.sx(s.n) + 8, v.sy(curve[s.n]) + 12, { color: P.accent, size: 11, weight: 700, mono: true });
      if (s.N !== 365) return;
      // the year as a grid of 365 days
      const gx = narrow ? 14 : pw + 10, gy = narrow ? ph + 6 : 18, gw = narrow ? c.w - 28 : c.w - pw - 20, cols = 27, cs = Math.min(gw / cols, ((narrow ? c.h - ph - 12 : c.h - 30)) / 14);
      for (let d = 0; d < 365; d++) {
        const k = s.room ? s.room.get(d) || 0 : 0;
        fillRR(ctx, gx + (d % cols) * cs + .5, gy + Math.floor(d / cols) * cs + .5, cs - 1, cs - 1, 1.5, k > 1 ? P.err : k ? P.alpha('accent', .6) : P.alpha('dim', .1));
      }
      if (!narrow) D.text(ctx, s.room ? 'one room: red = shared birthday' : 'press “Fill one room”', gx, gy + 14 * cs + 10, { color: P.faint, size: 10 });
    };
    update();
  },
});

/* ====================================================== math-montecarlo == */
defineLab('math-montecarlo', {
  title: 'Estimating π with random darts',
  hint: 'Throw darts uniformly at a square. The fraction landing inside the quarter circle is about π/4. Press <b>Play</b> and watch the estimate wobble, then settle — and see how slowly the error shrinks.',
  mount(L) {
    const s = { n: 0, inside: 0, pts: [], hist: [] };
    const c = L.canvas(w => w < 520 ? 480 : 300);
    const throwN = k => {
      for (let i = 0; i < k; i++) {
        const x = Math.random(), y = Math.random(), inn = x * x + y * y <= 1;
        s.n++; if (inn) s.inside++;
        if (s.pts.length < 4000) s.pts.push([x, y, inn]);
        const lg = Math.log10(s.n);
        if (!s.hist.length || lg - Math.log10(s.hist[s.hist.length - 1][0]) > .01) s.hist.push([s.n, 4 * s.inside / s.n]);
      }
    };
    const run = L.loop(() => { throwN(s.n < 2000 ? 20 : s.n < 50000 ? 400 : 4000); update(); if (s.n >= 2e6) return false; });
    L.playButton(run, ['Play', 'Pause']);
    L.button('+100 darts', () => { throwN(100); update(); });
    L.button('Reset', () => { run.stop(); Object.assign(s, { n: 0, inside: 0, pts: [], hist: [] }); update(); });
    function update() {
      const est = s.n ? 4 * s.inside / s.n : NaN, se = s.n ? 4 * Math.sqrt((Math.PI / 4) * (1 - Math.PI / 4) / s.n) : NaN;
      L.stats([['darts', s.n.toLocaleString()], ['inside', s.inside.toLocaleString()], ['estimate 4·inside/darts', s.n ? est.toFixed(5) : '—', 'accent'],
        ['actual error', s.n ? Math.abs(est - Math.PI).toExponential(1) : '—'], ['typical error ≈ 1.64/√n', s.n ? se.toExponential(1) : '—']]);
      L.insight(`<b>Law of large numbers:</b> the average of many independent random trials converges to the expected value — here π/4 per dart. But the typical error shrinks only like <b>1/√n</b>: 100× more darts buy just 10× more accuracy (one more digit of π per 100× work). Monte Carlo is how you estimate things with no formula: load-test tail latency, a risk model, a ray-traced pixel, the win rate of a game move.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, narrow = c.w < 520, side = narrow ? Math.min(c.w - 28, 230) : c.h - 24, ox = narrow ? (c.w - side) / 2 : 12, oy = 12;
      fillRR(ctx, ox, oy, side, side, 2, P.alpha('dim', .06), P.border);
      ctx.beginPath(); ctx.moveTo(ox, oy + side); ctx.arc(ox, oy + side, side, -Math.PI / 2, 0); ctx.closePath();
      ctx.fillStyle = P.alpha('accent', .08); ctx.fill(); ctx.strokeStyle = P.accent; ctx.lineWidth = 1.5; ctx.stroke();
      s.pts.forEach(([x, y, inn]) => { ctx.fillStyle = inn ? P.alpha('accent', .8) : P.alpha('err', .7); ctx.fillRect(ox + x * side - 1, oy + (1 - y) * side - 1, 2.2, 2.2); });
      if (s.n > s.pts.length) D.text(ctx, `showing the first ${s.pts.length.toLocaleString()} darts`, ox + side / 2, oy + side + 10, { color: P.faint, size: 10, align: 'center' });
      // estimate vs darts, log x
      const px0 = narrow ? 14 : ox + side + 24, py0 = narrow ? oy + side + 26 : oy, pw = narrow ? c.w - 28 : c.w - px0 - 12, ph = narrow ? c.h - py0 - 10 : c.h - 24;
      const v = D.view({ w: px0 + pw, h: py0 + ph }, { x0: 0, x1: 6.3, y0: 2.6, y1: 3.7, pad: 14, padL: px0 + 34, padB: 22 });
      v.sy = y => py0 + 8 + (3.7 - y) / 1.1 * (ph - 30);
      D.axes(ctx, v, P, { xTicks: [0, 2, 4, 6], yTicks: [2.8, 3.14159, 3.5], fmtX: t => `10${'⁰¹²³⁴⁵⁶'[t]}`, fmtY: t => t.toFixed(2) });
      ctx.beginPath();
      for (let lg = 0; lg <= 6.3; lg += .05) { const e = 1.64 * 4 * Math.sqrt((Math.PI / 4) * (1 - Math.PI / 4) / 10 ** lg); ctx.lineTo(v.sx(lg), v.sy(Math.min(3.7, Math.PI + e))); }
      for (let lg = 6.3; lg >= 0; lg -= .05) { const e = 1.64 * 4 * Math.sqrt((Math.PI / 4) * (1 - Math.PI / 4) / 10 ** lg); ctx.lineTo(v.sx(lg), v.sy(Math.max(2.6, Math.PI - e))); }
      ctx.closePath(); ctx.fillStyle = P.alpha('ok', .1); ctx.fill();
      D.line(ctx, v.sx(0), v.sy(Math.PI), v.sx(6.3), v.sy(Math.PI), P.ok, 1.3);
      ctx.beginPath();
      s.hist.forEach(([n, e], i) => { const x = v.sx(Math.log10(n)), y = v.sy(clamp(e, 2.6, 3.7)); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
      ctx.strokeStyle = P.accent; ctx.lineWidth = 1.8; ctx.stroke();
      D.text(ctx, 'estimate vs darts · band = typical error', v.sx(0) + 4, py0 + 2, { color: P.faint, size: 10 });
    };
    throwN(300); update();
  },
});

/* ============================================================== math-clt == */
defineLab('math-clt', {
  title: 'The central limit theorem: averages become bell curves',
  hint: 'Pick a lopsided source distribution. Each “sample” averages <b>n</b> random draws from it; the histogram collects many of those averages. Raise n and watch the shape turn into a bell, and narrow.',
  mount(L) {
    const SRC = {
      unif: ['uniform', () => Math.random(), .5, Math.sqrt(1 / 12), [0, 1], x => x >= 0 && x <= 1 ? 1 : 0],
      exp: ['skewed (exponential)', () => -Math.log(1 - Math.random()), 1, 1, [0, 4], x => x >= 0 ? Math.exp(-x) : 0],
      dice: ['a die', () => 1 + Math.floor(Math.random() * 6), 3.5, Math.sqrt(35 / 12), [1, 6], x => (x >= .5 && x <= 6.5) ? 1 / 6 : 0],
      ushape: ['U-shaped', () => Math.sin(Math.random() * Math.PI / 2) ** 2, .5, Math.sqrt(1 / 8), [0, 1], x => x > .01 && x < .99 ? 1 / (Math.PI * Math.sqrt(x * (1 - x))) : 0],
    };
    const B = 44;
    const s = { src: 'exp', n: 1, bins: new Array(B).fill(0), count: 0, sum: 0, sum2: 0 };
    const c = L.canvas(w => w < 520 ? 320 : 300);
    const reset = () => { s.bins.fill(0); s.count = 0; s.sum = 0; s.sum2 = 0; };
    L.seg('source', Object.entries(SRC).map(([k, v]) => [k, v[0]]), s.src, v => { s.src = v; fill(); update(); });
    L.slider('draws per average n', { min: 1, max: 50, value: s.n }, v => { s.n = v; fill(); update(); });
    const draw = k => {
      const [, f, , , [lo, hi]] = SRC[s.src];
      for (let j = 0; j < k; j++) {
        let t = 0; for (let i = 0; i < s.n; i++) t += f();
        const m = t / s.n, b = Math.floor((m - lo) / (hi - lo) * B);
        if (b >= 0 && b < B) s.bins[b]++;
        s.count++; s.sum += m; s.sum2 += m * m;
      }
    };
    const run = L.loop(() => { draw(60); update(); if (s.count >= 20000) return false; });
    L.playButton(run, ['Draw averages', 'Pause'], () => { if (s.count >= 20000) reset(); });
    L.button('+2,000 at once', () => { draw(2000); update(); });
    const fill = () => { reset(); draw(3000); };
    function update() {
      const [name, , mu, sd] = SRC[s.src], mean = s.count ? s.sum / s.count : NaN, obs = s.count > 1 ? Math.sqrt(Math.max(0, s.sum2 / s.count - mean * mean)) : NaN;
      L.stats([['averages drawn', s.count.toLocaleString()], ['mean of averages', s.count ? mean.toFixed(3) : '—'], ['source mean μ', mu.toFixed(3)],
        ['spread of averages', s.count ? obs.toFixed(3) : '—', 'accent'], ['predicted σ/√n', (sd / Math.sqrt(s.n)).toFixed(3), 'ok']]);
      L.insight(s.n === 1
        ? `With n = 1 each “average” is a single draw, so the histogram is just the ${name} source itself. Now raise n.`
        : `Whatever the source looks like, the average of n independent draws is approximately <b>normal</b> (the green curve) with the same mean μ and a spread of <b>σ/√n</b>. That is why error bars, confidence intervals and A/B tests can use the bell curve even for skewed data like latencies or purchase amounts — and why quadrupling a sample only halves the noise.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, [, , mu, sd, [lo, hi], pdf] = SRC[s.src];
      const left = 30, right = c.w - 12, top = 70, bottom = c.h - 24, bw = (right - left) / B;
      // the source, small
      const sv = D.view({ w: Math.min(220, c.w * .4), h: 56 }, { x0: lo - (s.src === 'dice' ? .5 : 0), x1: hi + (s.src === 'dice' ? .5 : 0), y0: 0, y1: s.src === 'ushape' ? 2.5 : s.src === 'dice' ? .25 : 1.2, pad: 6, padL: left });
      D.line(ctx, sv.sx(sv.x0), sv.sy(0), sv.sx(sv.x1), sv.sy(0), P.border, 1);
      D.curve(ctx, sv, pdf, P.dim, 1.8, 160);
      D.text(ctx, 'source distribution', sv.sx(sv.x1) + 8, 30, { color: P.faint, size: 10 });
      // histogram of averages
      const mx = Math.max(1, ...s.bins), scale = s.count ? (bottom - top) / Math.max(mx, s.count * (hi - lo) / B / (sd / Math.sqrt(s.n) * Math.sqrt(TAU)) * 1.02) : 1;
      D.line(ctx, left, bottom, right, bottom, P.strong, 1);
      s.bins.forEach((k, i) => { if (k) fillRR(ctx, left + i * bw + .5, bottom - k * scale, bw - 1, k * scale, 1.5, P.alpha('accent', .6)); });
      if (s.count) {
        const se = sd / Math.sqrt(s.n), norm = x => s.count * (hi - lo) / B * Math.exp(-((x - mu) ** 2) / (2 * se * se)) / (se * Math.sqrt(TAU));
        ctx.beginPath();
        for (let i = 0; i <= 200; i++) { const x = lo + (hi - lo) * i / 200, y = bottom - norm(x) * scale; i ? ctx.lineTo(left + (right - left) * i / 200, Math.max(top - 10, y)) : ctx.moveTo(left, y); }
        ctx.strokeStyle = P.ok; ctx.lineWidth = 2; ctx.stroke();
      }
      [lo, (lo + hi) / 2, hi].forEach(t => D.text(ctx, String(+t.toFixed(2)), left + (right - left) * (t - lo) / (hi - lo), bottom + 12, { color: P.faint, size: 10, align: 'center', mono: true }));
      D.text(ctx, 'histogram of averages · green = normal(μ, σ/√n)', left, top - 12, { color: P.faint, size: 10 });
    };
    fill(); update();
  },
});

/* ======================================================= math-percentiles == */
defineLab('math-percentiles', {
  title: 'Latency: why engineers quote p99, not the average',
  hint: 'Twenty thousand request latencies: most are quick, a few are stuck behind a GC pause or a retry. Grow the slow tail and watch which numbers move. Then fan one user request out to many servers.',
  mount(L) {
    const s = { tail: 1.5, fan: 1, data: [] };
    const c = L.canvas(w => w < 520 ? 290 : 280);
    const gen = () => {
      const r = rng(11), out = [];
      for (let i = 0; i < 20000; i++) {
        const slow = r() < s.tail / 100;
        out.push(slow ? 300 + 900 * r() : 40 * Math.exp(.35 * gauss(r)));
      }
      s.data = out.sort((a, b) => a - b);
    };
    L.slider('slow requests (tail)', { min: 0, max: 5, step: .1, value: s.tail, fmt: v => `${v.toFixed(1)}%` }, v => { s.tail = v; gen(); update(); });
    L.slider('servers one request fans out to', { min: 1, max: 100, value: s.fan }, v => { s.fan = Math.round(v); update(); });
    const q = p => s.data[Math.min(s.data.length - 1, Math.floor(p * s.data.length))];
    function update() {
      const mean = s.data.reduce((a, b) => a + b, 0) / s.data.length, p99 = q(.99);
      const pFan = 1 - .99 ** s.fan;
      L.stats([['mean', `${mean.toFixed(0)} ms`], ['median p50', `${q(.5).toFixed(0)} ms`, 'ok'], ['p90', `${q(.9).toFixed(0)} ms`], ['p99', `${p99.toFixed(0)} ms`, 'accent'],
        ['p99.9', `${q(.999).toFixed(0)} ms`, 'err'], ['a fanned-out request hits ≥ one p99', `${(pFan * 100).toFixed(0)}%`, s.fan > 1 ? 'err' : '']]);
      L.insight(s.fan > 1
        ? `If one page load calls ${s.fan} servers and waits for all of them, it is slow whenever <b>any</b> of them is slow: P = 1 − 0.99${String(s.fan).replace(/\d/g, d => '⁰¹²³⁴⁵⁶⁷⁸⁹'[d])} = ${(pFan * 100).toFixed(0)}%. With fan-out, a server’s p99 becomes the <b>typical</b> user experience — the reason large systems chase tail latency and use hedged requests.`
        : `The <b>median</b> (p50) barely moves as the tail grows; the <b>mean</b> is dragged up by a few huge values and describes nobody; the <b>p99</b> — “99% of requests are faster than this” — is where the slow tail shows. A percentile is just a position in the sorted list: p99 of 20,000 values is the 19,800th.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, left = 14, right = c.w - 14, top = 30, bottom = c.h - 28, B = 60;
      const lx0 = Math.log10(8), lx1 = Math.log10(1500), X = ms => left + (right - left) * (Math.log10(ms) - lx0) / (lx1 - lx0);
      const bins = new Array(B).fill(0);
      s.data.forEach(ms => { const b = Math.floor((Math.log10(ms) - lx0) / (lx1 - lx0) * B); if (b >= 0 && b < B) bins[b]++; });
      const mx = Math.max(...bins), bw = (right - left) / B;
      bins.forEach((k, i) => { const h = (bottom - top) * Math.sqrt(k / mx); if (k) fillRR(ctx, left + i * bw + .5, bottom - h, bw - 1, h, 1.5, P.alpha('dim', .45)); });
      D.line(ctx, left, bottom, right, bottom, P.strong, 1);
      [10, 30, 100, 300, 1000].forEach(t => D.text(ctx, `${t} ms`, X(t), bottom + 12, { color: P.faint, size: 10, align: 'center', mono: true }));
      const mean = s.data.reduce((a, b) => a + b, 0) / s.data.length;
      [[q(.5), 'p50', P.ok, 0], [mean, 'mean', P.dim, 12], [q(.99), 'p99', P.accent, 24], [q(.999), 'p99.9', P.err, 36]].forEach(([x, l, col, dy]) => vline(ctx, X(x), top - 22, bottom, col, l, P, dy));
      D.text(ctx, 'latency (log scale) · bar height ∝ √count so the tail stays visible', right, 10, { color: P.faint, size: 10, align: 'right' });
    };
    gen(); update();
  },
});

/* =========================================================== math-pvalue == */
defineLab('math-pvalue', {
  title: 'Is this coin fair? A hypothesis test you can run',
  hint: 'The <b>null hypothesis</b> says the coin is fair. Flip it n times; the bars show how often a <i>fair</i> coin gives each head count. The shaded area — results at least as extreme as yours — is the <b>p-value</b>.',
  mount(L) {
    const s = { n: 100, bias: .5, h: null, runs: 0, rejects: 0 };
    const c = L.canvas(w => w < 520 ? 250 : 250);
    L.slider('flips n', { min: 10, max: 1000, log: true, value: s.n, fmt: v => Math.round(v) }, v => { s.n = Math.round(v); s.h = null; s.runs = s.rejects = 0; update(); });
    L.slider('the coin’s true P(heads) — hidden in real life', { min: .3, max: .7, step: .01, value: s.bias, fmt: v => v.toFixed(2) }, v => { s.bias = v; s.h = null; s.runs = s.rejects = 0; update(); });
    const pmf = () => { const n = s.n, out = new Float64Array(n + 1); let lc = 0; for (let k = 0; k <= n; k++) { if (k) lc += Math.log(n - k + 1) - Math.log(k); out[k] = Math.exp(lc + n * Math.log(.5)); } return out; };
    const flip = () => { let h = 0; for (let i = 0; i < s.n; i++) if (Math.random() < s.bias) h++; return h; };
    const pval = (h, pm) => { const d = Math.abs(h - s.n / 2); let p = 0; pm.forEach((v, k) => { if (Math.abs(k - s.n / 2) >= d - 1e-9) p += v; }); return Math.min(1, p); };
    L.button('Flip n coins', () => { s.h = flip(); update(); }, 'primary');
    L.button('Repeat the experiment 1,000×', () => { const pm = pmf(); for (let i = 0; i < 1000; i++) { const h = flip(); s.runs++; if (pval(h, pm) < .05) s.rejects++; if (i === 999) s.h = h; } update(); });
    function update() {
      const pm = pmf(), p = s.h == null ? null : pval(s.h, pm), rate = s.runs ? s.rejects / s.runs : null;
      L.stats([['heads', s.h == null ? '—' : `${s.h} of ${s.n}`], ['p-value', p == null ? '—' : p < 1e-4 ? p.toExponential(1) : p.toFixed(4), 'accent'],
        ['verdict at α = 0.05', p == null ? '—' : p < .05 ? 'reject “fair”' : 'no evidence against fair', p == null ? '' : p < .05 ? 'err' : 'ok'],
        rate != null ? [s.bias === .5 ? 'false alarms (fair coin rejected)' : 'power (unfair coin caught)', `${(rate * 100).toFixed(1)}%`, s.bias === .5 ? 'err' : 'ok'] : null]);
      L.insight(rate != null && Math.abs(s.bias - .5) < 1e-9
        ? `The coin really is fair, yet about <b>5%</b> of experiments reject it: that is what α = 0.05 means — the false-positive rate you accept. Run 20 A/B tests on changes that do nothing and expect one “significant” winner. Peeking at results and stopping early raises this rate further.`
        : rate != null ? `The coin is biased (${s.bias.toFixed(2)}), and the test catches it ${(rate * 100).toFixed(0)}% of the time — its <b>power</b>. Small effects need large n: power grows with the sample size and with the size of the bias.`
          : `A p-value is <b>P(data at least this extreme | the coin is fair)</b>. It is <b>not</b> the probability that the coin is fair. A small p-value says “a fair coin would rarely do this”; a large one says the data are consistent with fairness, not that fairness is proven.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, pm = pmf(), left = 16, right = c.w - 16, top = 20, bottom = c.h - 26;
      const sd = Math.sqrt(s.n) / 2, k0 = Math.max(0, Math.floor(s.n / 2 - 4.5 * sd)), k1 = Math.min(s.n, Math.ceil(s.n / 2 + 4.5 * sd));
      const lo = Math.min(k0, s.h ?? k0), hi = Math.max(k1, s.h ?? k1), bw = (right - left) / (hi - lo + 1), mx = Math.max(...pm);
      const d = s.h == null ? Infinity : Math.abs(s.h - s.n / 2);
      for (let k = lo; k <= hi; k++) {
        const h = (bottom - top) * pm[k] / mx, x = left + (k - lo) * bw, ext = Math.abs(k - s.n / 2) >= d - 1e-9;
        if (h > .3) fillRR(ctx, x + bw * .1, bottom - h, Math.max(1, bw * .8), h, 1, ext ? P.alpha('err', .75) : P.alpha('dim', .4));
      }
      D.line(ctx, left, bottom, right, bottom, P.strong, 1);
      const X = k => left + (k - lo + .5) * bw;
      [lo, Math.round(s.n / 2), hi].forEach(t => D.text(ctx, String(t), X(t), bottom + 12, { color: P.faint, size: 10, align: 'center', mono: true }));
      if (s.h != null) { D.line(ctx, X(s.h), top - 6, X(s.h), bottom, P.accent, 2); D.text(ctx, `you got ${s.h}`, X(s.h) + (X(s.h) > c.w * .7 ? -6 : 6), top - 2, { color: P.accent, size: 11, weight: 700, align: X(s.h) > c.w * .7 ? 'right' : 'left' }); }
      D.text(ctx, 'heads count if the coin were fair', left, 8, { color: P.faint, size: 10 });
    };
    s.h = 58; update();
  },
});

/* ======================================================= math-derivative == */
defineLab('math-derivative', {
  title: 'The derivative: slope of a curve at one point',
  hint: 'The secant line joins two points h apart; its slope is rise over run. <b>Shrink h</b> and it turns into the tangent line. <b>Drag the point</b> along the curve and watch the slope graph below trace f′.',
  mount(L) {
    const F = {
      sq: ['x²', x => x * x, x => 2 * x, [-3, 3], [-1, 9]],
      cube: ['x³ − 3x', x => x ** 3 - 3 * x, x => 3 * x * x - 3, [-2.6, 2.6], [-6, 6]],
      sin: ['sin x', Math.sin, Math.cos, [-6.3, 6.3], [-1.6, 1.6]],
      exp: ['eˣ', Math.exp, Math.exp, [-3, 2.2], [-.5, 9]],
      abs: ['|x|', Math.abs, x => x > 0 ? 1 : x < 0 ? -1 : NaN, [-3, 3], [-.5, 3]],
    };
    const s = { f: 'sq', x: 1, h: 1 };
    const c = L.canvas(w => w < 520 ? 420 : 400);
    L.seg('f(x)', Object.entries(F).map(([k, v]) => [k, v[0]]), s.f, v => { s.f = v; s.x = v === 'abs' ? 0 : 1; update(); });
    L.slider('h (gap between the two points)', { min: .001, max: 2, log: true, value: s.h, fmt: v => v.toFixed(v < .01 ? 3 : 2) }, v => { s.h = v; update(); });
    let v1 = null;
    L.drag(c, {
      hit: (x, y) => v1 && Math.hypot(v1.sx(s.x) - x, v1.sy(F[s.f][1](s.x)) - y) < 18 ? 'p' : null,
      move: (_, x) => { const [, , , [a, b]] = F[s.f]; s.x = clamp(Math.round(v1.ix(x) * 20) / 20, a, b); update(); },
    });
    function update() {
      const [name, f, df] = F[s.f], sec = (f(s.x + s.h) - f(s.x)) / s.h, t = df(s.x);
      const cen = (f(s.x + s.h) - f(s.x - s.h)) / (2 * s.h);
      L.stats([['x', s.x.toFixed(2)], ['secant slope (f(x+h) − f(x))/h', fmtN(sec, 4), 'accent'], ['true derivative f′(x)', Number.isNaN(t) ? 'undefined' : fmtN(t, 4), 'ok'],
        ['error', Number.isNaN(t) ? '—' : fmtN(Math.abs(sec - t), 4)], ['centred (f(x+h) − f(x−h))/2h', fmtN(cen, 4)]]);
      L.insight(s.f === 'abs' && Math.abs(s.x) < 1e-9
        ? `At x = 0, |x| has a corner: slopes from the right are +1 and from the left −1, so the secant never settles — <b>the derivative does not exist here</b>. The centred difference shows 0, a plausible-looking wrong answer. (ReLU in neural networks has exactly this corner; frameworks just pick a value.)`
        : `<b>f′(x) = the limit of (f(x + h) − f(x)) / h as h → 0.</b> It is the instantaneous rate of change: speed from position, marginal cost from total cost, how fast the loss changes when you nudge a weight. Notice the error shrinks in step with h, while the centred difference is far more accurate — that is how numerical differentiation (and gradient checking) is done in practice.${s.f === 'sq' ? ' For x² the slope at x is always 2x.' : s.f === 'exp' ? ' eˣ is its own derivative: its slope equals its height.' : ''}`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, [name, f, df, [a, b], [y0, y1]] = F[s.f], top = c.h * .62;
      v1 = D.view({ w: c.w, h: top }, { x0: a, x1: b, y0, y1, pad: 16, padL: 30 });
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, c.w, top - 6); ctx.clip();
      D.grid(ctx, v1, P, s.f === 'sin' ? Math.PI / 2 : 1);
      D.curve(ctx, v1, f, P.text, 2.4);
      const fx = f(s.x), t = df(s.x), sec = (f(s.x + s.h) - fx) / s.h;
      if (!Number.isNaN(t)) D.curve(ctx, v1, x => fx + t * (x - s.x), P.ok, 1.6, 2, [6, 4]);
      D.curve(ctx, v1, x => fx + sec * (x - s.x), P.accent, 2, 2);
      D.dot(ctx, v1.sx(s.x + s.h), v1.sy(f(s.x + s.h)), 5, P.accent);
      D.line(ctx, v1.sx(s.x), v1.sy(fx), v1.sx(s.x + s.h), v1.sy(fx), P.alpha('dim', .8), 1.2, [3, 3]);
      D.line(ctx, v1.sx(s.x + s.h), v1.sy(fx), v1.sx(s.x + s.h), v1.sy(f(s.x + s.h)), P.alpha('dim', .8), 1.2, [3, 3]);
      D.dot(ctx, v1.sx(s.x), v1.sy(fx), 7, P.accent, P.bg, 2);
      ctx.restore();
      D.line(ctx, 10, top - 3, c.w - 10, top - 3, P.border, 1);
      D.text(ctx, `f(x) = ${name}  ·  accent: secant  ·  green dashed: tangent`, 34, 10, { color: P.faint, size: 10 });
      // derivative graph
      const all = []; for (let i = 0; i <= 100; i++) { const d = df(a + (b - a) * i / 100); if (Number.isFinite(d)) all.push(d); }
      const lo = Math.min(-1, ...all), hi = Math.max(1, ...all);
      const v2 = D.view({ w: c.w, h: c.h - top }, { x0: a, x1: b, y0: lo, y1: hi, pad: 14, padL: 30 });
      const off = top; const sy2 = y => off + v2.sy(y);
      D.line(ctx, v2.sx(a), sy2(0), v2.sx(b), sy2(0), P.strong, 1);
      ctx.beginPath(); let pen = false;
      for (let i = 0; i <= 240; i++) { const x = a + (b - a) * i / 240, d = df(x); if (!Number.isFinite(d) || (s.f === 'abs' && Math.abs(x) < .02)) { pen = false; continue; } pen ? ctx.lineTo(v2.sx(x), sy2(d)) : ctx.moveTo(v2.sx(x), sy2(d)); pen = true; }
      ctx.strokeStyle = P.ok; ctx.lineWidth = 2; ctx.stroke();
      if (Number.isFinite(t)) D.dot(ctx, v2.sx(s.x), sy2(t), 5, P.ok);
      D.text(ctx, 'f′(x): the slope at every x', 34, off + 8, { color: P.ok, size: 10, weight: 650 });
    };
    update();
  },
});

/* ========================================================== math-riemann == */
defineLab('math-riemann', {
  title: 'The integral: area as a sum of thin rectangles',
  hint: 'Chop the area under the curve into <b>n</b> strips and add them up. More strips, better answer — but <i>how</i> much better depends on the rule. Compare the errors.',
  mount(L) {
    const F = {
      sq: ['x² on [0, 2]', x => x * x, 0, 2, 8 / 3],
      sin: ['sin x on [0, π]', Math.sin, 0, Math.PI, 2],
      inv: ['1/x on [1, e]', x => 1 / x, 1, Math.E, 1],
      sqrt: ['√x on [0, 4]', Math.sqrt, 0, 4, 16 / 3],
    };
    const s = { f: 'sq', n: 6, rule: 'left' };
    const c = L.canvas(w => w < 520 ? 280 : 280);
    L.seg('area under', Object.entries(F).map(([k, v]) => [k, v[0]]), s.f, v => { s.f = v; update(); });
    L.seg('rule', [['left', 'left'], ['right', 'right'], ['mid', 'midpoint'], ['trap', 'trapezoid']], s.rule, v => { s.rule = v; update(); });
    L.slider('strips n', { min: 1, max: 200, log: true, value: s.n, fmt: v => Math.round(v) }, v => { s.n = Math.round(v); update(); });
    const approx = (n, rule) => {
      const [, f, a, b] = F[s.f], w = (b - a) / n; let t = 0;
      for (let i = 0; i < n; i++) { const x = a + i * w; t += rule === 'left' ? f(x) : rule === 'right' ? f(x + w) : rule === 'mid' ? f(x + w / 2) : (f(x) + f(x + w)) / 2; }
      return t * w;
    };
    function update() {
      const ex = F[s.f][4], A = approx(s.n, s.rule), err = Math.abs(A - ex), err2 = Math.abs(approx(2 * s.n, s.rule) - ex);
      L.stats([['sum of strips', A.toFixed(6), 'accent'], ['exact integral', ex.toFixed(6), 'ok'], ['error', err.toExponential(2)],
        ['error after doubling n', `÷ ${err2 > 0 ? (err / err2).toFixed(1) : '∞'}`]]);
      L.insight(s.rule === 'left' || s.rule === 'right'
        ? `Left and right sums have error proportional to <b>1/n</b>: doubling the strips halves the error (the “÷ 2” chip). The exact area is the <b>limit</b> as n → ∞ — that limit is the integral ∫ f(x) dx. An integral is accumulation: area under a speed curve is distance travelled; under a request-rate curve, total requests.`
        : `Midpoint and trapezoid sums have error proportional to <b>1/n²</b>: doubling n divides the error by about 4. Same work per strip, far better answers — choosing a better method beats brute force, in numerics as in algorithms. (The Fundamental Theorem of Calculus gives the exact answer: find F with F′ = f, then the area is F(b) − F(a).)`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, [, f, a, b] = F[s.f];
      const ymax = s.f === 'sq' ? 4.3 : s.f === 'sqrt' ? 2.2 : 1.15;
      const v = D.view(c, { x0: a - .1 * (b - a), x1: b + .05 * (b - a), y0: -.05 * ymax, y1: ymax, pad: 16, padL: 30, padB: 24 });
      D.axes(ctx, v, P, { xTicks: [a, b], yTicks: [0, ymax / 2], fmtX: t => t === Math.PI ? 'π' : t === Math.E ? 'e' : t, fmtY: t => t.toFixed(1) });
      const w = (b - a) / s.n;
      for (let i = 0; i < s.n; i++) {
        const x = a + i * w;
        ctx.beginPath();
        if (s.rule === 'trap') { ctx.moveTo(v.sx(x), v.sy(0)); ctx.lineTo(v.sx(x), v.sy(f(x))); ctx.lineTo(v.sx(x + w), v.sy(f(x + w))); ctx.lineTo(v.sx(x + w), v.sy(0)); ctx.closePath(); }
        else { const h = s.rule === 'left' ? f(x) : s.rule === 'right' ? f(x + w) : f(x + w / 2); ctx.rect(v.sx(x), v.sy(h), v.sx(x + w) - v.sx(x), v.sy(0) - v.sy(h)); }
        ctx.fillStyle = P.alpha('accent', .28); ctx.fill();
        if (s.n <= 60) { ctx.strokeStyle = P.alpha('accent', .8); ctx.lineWidth = 1; ctx.stroke(); }
      }
      ctx.save(); ctx.beginPath(); ctx.rect(v.sx(a), 0, v.sx(b) - v.sx(a), c.h); ctx.clip();
      D.curve(ctx, v, f, P.text, 2.4); ctx.restore();
    };
    update();
  },
});

/* =========================================================== math-taylor == */
defineLab('math-taylor', {
  title: 'Taylor series: a function rebuilt from its derivatives at one point',
  hint: 'Add terms one at a time. Each new term matches one more derivative at x = 0, and the polynomial hugs the curve over a wider stretch. Then try ln(1 + x): past x = 1 it never catches up.',
  mount(L) {
    const F = {
      sin: ['sin x', Math.sin, k => k % 2 ? ((k - 1) / 2 % 2 ? -1 : 1) : 0, [-7, 7], [-2.5, 2.5]],
      cos: ['cos x', Math.cos, k => k % 2 ? 0 : (k / 2 % 2 ? -1 : 1), [-7, 7], [-2.5, 2.5]],
      exp: ['eˣ', Math.exp, () => 1, [-4, 3], [-2, 12]],
      ln: ['ln(1 + x)', x => x > -1 ? Math.log1p(x) : NaN, k => k === 0 ? 0 : (k % 2 ? 1 : -1) * [...Array(k).keys()].reduce((p, i) => p * (i + 1), 1) / k, [-1.5, 3], [-3, 2.5]],
    };
    const s = { f: 'sin', N: 3 };
    const c = L.canvas(w => w < 520 ? 290 : 300);
    const fact = k => { let r = 1; for (let i = 2; i <= k; i++) r *= i; return r; };
    L.seg('function', Object.entries(F).map(([k, v]) => [k, v[0]]), s.f, v => { s.f = v; update(); });
    L.slider('terms', { min: 1, max: 14, value: s.N }, v => { s.N = v; update(); });
    /* coefficient of xᵏ is f⁽ᵏ⁾(0)/k!; the table stores f⁽ᵏ⁾(0) */
    const coefs = () => { const out = []; for (let k = 0; out.filter(c2 => c2[1] !== 0).length < s.N && k < 40; k++) out.push([k, F[s.f][2](k) / fact(k)]); return out; };
    const poly = x => coefs().reduce((t, [k, a]) => t + a * x ** k, 0);
    const term = (k, a) => { const num = Math.abs(a) === 1 ? '' : Number.isInteger(1 / Math.abs(a)) ? `1/${1 / Math.abs(a)}·` : `${Math.abs(a).toPrecision(3)}·`; return k === 0 ? `${Math.abs(a)}` : `${num}x${k > 1 ? String(k).replace(/\d/g, d => '⁰¹²³⁴⁵⁶⁷⁸⁹'[d]) : ''}`; };
    function update() {
      const cs = coefs().filter(([, a]) => a !== 0), f = F[s.f][1];
      const expr = cs.slice(0, 5).map(([k, a], i) => `${i ? (a < 0 ? ' − ' : ' + ') : a < 0 ? '−' : ''}${term(k, a)}`).join('') + (cs.length > 5 ? ' + …' : '');
      L.stats([['polynomial', expr, 'accent'], ['error at x = 1', Math.abs(poly(1) - f(1)).toExponential(1)], ['error at x = 3', Number.isFinite(f(3)) ? Math.abs(poly(3) - f(3)).toExponential(1) : '—', s.f === 'ln' ? 'err' : '']]);
      L.insight(s.f === 'ln'
        ? `ln(1 + x) = x − x²/2 + x³/3 − … only converges for −1 &lt; x ≤ 1: its <b>radius of convergence</b> is 1, because the function blows up at x = −1. Beyond x = 1 adding terms makes things <b>worse</b>. A series is a tool with a range of validity, not magic.`
        : `Near 0, sin x ≈ x − x³/6 + x⁵/120 − … Each term fixes one more derivative, and the factorials in the denominators grow so fast that a handful of terms is extremely accurate near 0. Real maths libraries compute sin(x) this way: reduce x into a small range using periodicity, then evaluate a short polynomial. It is also why sin x ≈ x for small angles, and eˣ ≈ 1 + x.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, [name, f, , [a, b], [y0, y1]] = F[s.f];
      const v = D.view(c, { x0: a, x1: b, y0, y1, pad: 16, padL: 28 });
      D.grid(ctx, v, P, 1);
      if (s.f === 'ln') { ctx.save(); ctx.fillStyle = P.alpha('err', .07); ctx.fillRect(v.sx(1), 0, c.w - v.sx(1), c.h); ctx.restore(); D.text(ctx, 'outside the radius of convergence', v.sx(1) + 6, 14, { color: P.err, size: 10 }); }
      D.curve(ctx, v, f, P.text, 2.6, 300);
      ctx.save(); ctx.beginPath(); ctx.rect(0, 0, c.w, c.h); ctx.clip();
      D.curve(ctx, v, poly, P.accent, 2.2, 400); ctx.restore();
      D.text(ctx, `white: ${name}  ·  accent: its Taylor polynomial`, 32, c.h - 10, { color: P.faint, size: 10 });
    };
    update();
  },
});

/* =========================================================== math-newton == */
defineLab('math-newton', {
  title: 'Newton’s method: ride the tangent down to the root',
  hint: 'To solve f(x) = 0, stand at a guess, draw the tangent line, and jump to where it hits zero. Repeat. Press <b>Next step</b> and watch the correct digits in the table: they roughly <b>double</b> each time.',
  mount(L) {
    const s = { a: 2, x0: 4, k: 0, mode: 'sqrt' };
    const c = L.canvas(w => w < 520 ? 270 : 280);
    const f = x => s.mode === 'sqrt' ? x * x - s.a : Math.cos(x) - x;
    const df = x => s.mode === 'sqrt' ? 2 * x : -Math.sin(x) - 1;
    const root = () => s.mode === 'sqrt' ? Math.sqrt(s.a) : 0.7390851332151607;
    L.seg('solve', [['sqrt', 'x² − a = 0 (square root)'], ['cos', 'cos x = x']], s.mode, v => { s.mode = v; s.k = 0; s.x0 = v === 'sqrt' ? 4 : 2; update(); });
    L.slider('a', { min: 2, max: 50, value: s.a }, v => { s.a = v; s.k = 0; update(); });
    L.slider('first guess x₀', { min: .1, max: 10, step: .1, value: s.x0, fmt: v => v.toFixed(1) }, v => { s.x0 = v; s.k = 0; update(); });
    L.button('Next step', () => { s.k = Math.min(6, s.k + 1); update(); }, 'primary');
    L.button('Reset', () => { s.k = 0; update(); });
    const iters = () => { const xs = [s.x0]; for (let i = 0; i < 6; i++) { const x = xs[xs.length - 1], d = df(x); xs.push(d === 0 ? NaN : x - f(x) / d); } return xs; };
    const digits = x => { const e = Math.abs(x - root()); return !Number.isFinite(e) ? '—' : e === 0 ? '16+' : Math.max(0, Math.floor(-Math.log10(e / Math.abs(root())))); };
    function update() {
      const xs = iters(), cur = xs[s.k];
      L.stats([['step', s.k], ['xₖ', Number.isFinite(cur) ? cur.toPrecision(15) : 'failed', 'accent'], ['true root', root().toPrecision(15), 'ok'],
        ['correct digits', xs.slice(0, s.k + 1).map(digits).join(' → ')]]);
      L.insight(s.mode === 'sqrt'
        ? `For √a the update x ← x − (x² − a)/(2x) simplifies to <b>x ← (x + a/x) / 2</b>: average your guess with a divided by your guess. The Babylonians used it 3,000 years ago; CPUs and libraries still use Newton iterations for square roots and division. Near the root the error is squared each step — <b>quadratic convergence</b> — so 1 correct digit becomes 2, 4, 8, 16.`
        : `cos x = x has no formula for its solution, but Newton finds 0.7390851332… in a few steps. The price: you need the derivative, and a bad first guess (where the tangent is nearly flat) can throw the next guess far away. Gradient descent is the cautious cousin that uses only the slope, not a jump to zero.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, xs = iters(), r = root();
      const x0v = s.mode === 'sqrt' ? 0 : -1, x1v = Math.max(s.x0, r) * 1.15 + .5;
      const ymx = Math.max(...[x0v, x1v].map(x => Math.abs(f(x))), 1);
      const v = D.view(c, { x0: x0v, x1: x1v, y0: -ymx * .25, y1: ymx * .8, pad: 16, padL: 30 });
      D.line(ctx, v.sx(x0v), v.sy(0), v.sx(x1v), v.sy(0), P.strong, 1.3);
      D.curve(ctx, v, f, P.text, 2.4);
      D.dot(ctx, v.sx(r), v.sy(0), 5, P.ok);
      for (let i = 0; i < s.k; i++) {
        const x = xs[i], nx = xs[i + 1];
        if (!Number.isFinite(nx)) break;
        D.line(ctx, v.sx(x), v.sy(0), v.sx(x), v.sy(f(x)), P.alpha('dim', .7), 1, [3, 3]);
        D.line(ctx, v.sx(x), v.sy(f(x)), v.sx(nx), v.sy(0), i === s.k - 1 ? P.accent : P.alpha('accent', .45), 1.8);
        D.dot(ctx, v.sx(x), v.sy(f(x)), 4, P.accent);
      }
      const cur = xs[s.k];
      if (Number.isFinite(cur)) { D.dot(ctx, v.sx(cur), v.sy(0), 6, P.accent, P.bg, 2); D.text(ctx, `x${'₀₁₂₃₄₅₆'[s.k]}`, v.sx(cur), v.sy(0) + 16, { color: P.accent, size: 12, align: 'center', weight: 700 }); }
    };
    update();
  },
});
}
