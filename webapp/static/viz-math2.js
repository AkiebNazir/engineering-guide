/* ============================================================================
   Maths for CS Engineers labs, part 2: sums, numbers, graphs, linear algebra.

     math-log        a logarithm counts halvings (binary search, bits, tree depth)
     math-series     partial sums: geometric, harmonic, arithmetic
     math-mod        modular arithmetic on a clock: add, multiply, powers
     math-euclid     Euclid's gcd as squares tiling a rectangle
     math-sieve      the sieve of Eratosthenes, crossing off multiples
     math-graph      a graph playground: degrees, BFS, 2-colouring, Euler paths
     math-transform  a 2×2 matrix as a transformation of the plane
     math-gauss      Gaussian elimination, one row operation at a time
     math-pagerank   PageRank by power iteration and by a random surfer

   Object-spec labs (viz.js createLab), wrapped in a block for scope.
   ========================================================================= */
'use strict';
{
const fillRR = (ctx, x, y, w, h, r, fill, stroke, lw = 1.2) => {
  D.rrect(ctx, x, y, w, h, r);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
};
const onTap = (c, fn) => c.cv.addEventListener('click', e => { const r = c.cv.getBoundingClientRect(); fn(e.clientX - r.left, e.clientY - r.top); });
const gcd = (a, b) => { a = Math.abs(a); b = Math.abs(b); while (b) [a, b] = [b, a % b]; return a; };
const sup = n => String(n).replace(/[0-9-]/g, ch => '⁰¹²³⁴⁵⁶⁷⁸⁹⁻'['0123456789-'.indexOf(ch)]);

/* ============================================================== math-log == */
defineLab('math-log', {
  title: 'A logarithm counts halvings',
  hint: 'Looking for one name in a sorted list of <b>n</b> names: open the middle, keep the half that must contain it, repeat. Press <b>Play</b> and count the steps; then make n enormous.',
  mount(L) {
    const s = { n: 1e6, k: 0, target: .6180339, ylog: false, acc: 0 };
    const c = L.canvas(w => w < 520 ? 330 : 310);
    const K = () => Math.ceil(Math.log2(s.n));
    const rem = k => Math.max(1, Math.ceil(s.n / 2 ** k));
    L.slider('list size n', { min: 2, max: 1e9, log: true, value: s.n, fmt: v => fmtBig(Math.round(v)) }, v => { s.n = Math.round(v); s.k = Math.min(s.k, K()); update(); });
    const run = L.loop(dt => { s.acc += dt; if (s.acc > .32) { s.acc = 0; if (s.k >= K()) return false; s.k++; update(); } });
    L.playButton(run, ['Play', 'Pause'], () => { if (s.k >= K()) s.k = 0; });
    L.button('Halve once', () => { run.stop(); s.k = s.k >= K() ? 0 : s.k + 1; update(); });
    L.toggle('log scale', false, v => { s.ylog = v; update(); });
    function update() {
      const lg = Math.log2(s.n);
      L.stats([['log₂ n', fmtN(lg, 2), 'accent'], ['halvings to reach 1', `${s.k} / ${K()}`], ['bits to write n', Math.floor(lg) + 1],
        ['decimal digits (log₁₀)', Math.floor(Math.log10(s.n)) + 1], ['a linear scan checks', fmtBig(s.n)]]);
      L.insight(s.ylog
        ? `On a <b>log scale</b> the halving curve becomes a straight line: each step moves down by the same amount (one factor of 2). Logarithms turn multiplication into addition — log(ab) = log a + log b — which is why log scales show growth rates so clearly.`
        : `<b>log₂ n answers “how many times can I halve n before reaching 1?”</b> For a million that is 20; for a billion, only 30. That is why binary search, balanced search trees, heaps and divide-and-conquer are fast. The same number is the count of bits needed to write n, and the height of a balanced binary tree with n leaves. Read the other way it is doubling: 2³⁰ ≈ 10⁹.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, x0 = 16, x1 = c.w - 16, bw = x1 - x0;
      // the sorted list as one bar, the half still in play highlighted
      const w = 1 / 2 ** s.k, lo = Math.min(1 - w, Math.floor(s.target / w) * w);
      D.text(ctx, `${fmtBig(rem(s.k))} of ${fmtBig(s.n)} sorted names still in play after ${s.k} halving${s.k === 1 ? '' : 's'}`, x0, 14, { color: P.dim, size: 11, weight: 600 });
      fillRR(ctx, x0, 26, bw, 26, 6, P.alpha('dim', .12), P.border);
      fillRR(ctx, x0 + lo * bw, 26, Math.max(3, w * bw), 26, 4, P.alpha('accent', .75), P.accent);
      const tx = x0 + s.target * bw;
      D.line(ctx, tx, 22, tx, 56, P.err, 2);
      D.text(ctx, 'the name you want', Math.min(tx + 6, x1 - 96), 64, { color: P.err, size: 10 });
      // remaining vs step
      const top = 90, bottom = c.h - 28, left = 56, right = x1;
      const Kx = Math.max(1, K());
      const X = k => left + (right - left) * k / Kx;
      const Y = v => s.ylog ? bottom - (bottom - top) * Math.log2(v) / Math.log2(s.n) : bottom - (bottom - top) * (v - 1) / (s.n - 1 || 1);
      D.line(ctx, left, bottom, right, bottom, P.strong, 1); D.line(ctx, left, top, left, bottom, P.strong, 1);
      D.text(ctx, fmtBig(s.n), left - 6, top, { color: P.faint, size: 10, align: 'right', mono: true });
      D.text(ctx, '1', left - 6, bottom, { color: P.faint, size: 10, align: 'right', mono: true });
      if (s.ylog) D.text(ctx, fmtBig(Math.round(Math.sqrt(s.n))), left - 6, (top + bottom) / 2, { color: P.faint, size: 10, align: 'right', mono: true });
      D.text(ctx, 'still in play', left + 6, top - 8, { color: P.faint, size: 10 });
      D.text(ctx, 'halvings →', right, bottom - 10, { color: P.faint, size: 10, align: 'right' });
      for (let k = 0; k <= Kx; k += Kx > 20 ? 5 : Kx > 10 ? 2 : 1) D.text(ctx, String(k), X(k), bottom + 12, { color: P.faint, size: 9.5, align: 'center', mono: true });
      ctx.beginPath();
      for (let k = 0; k <= Kx; k++) { const px = X(k), py = Y(rem(k)); k ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }
      ctx.strokeStyle = P.alpha('accent', .35); ctx.lineWidth = 1.5; ctx.stroke();
      for (let k = 0; k <= s.k; k++) D.dot(ctx, X(k), Y(rem(k)), k === s.k ? 5 : 3.2, k === s.k ? P.accent : P.alpha('accent', .7));
    };
    update();
  },
});

/* =========================================================== math-series == */
defineLab('math-series', {
  title: 'Adding forever: when does a sum settle down?',
  hint: 'Each bar is one term; the line is the running total (the partial sum). Slide the ratio <b>r</b> of a geometric series across 1 and watch the total go from settling to exploding.',
  mount(L) {
    const s = { mode: 'geo', r: .5, k: 30, shown: 30, acc: 0 };
    const c = L.canvas(w => w < 520 ? 300 : 300);
    L.seg('series', [['geo', 'geometric 1 + r + r² + …'], ['harm', 'harmonic 1 + ½ + ⅓ + …'], ['arith', 'arithmetic 1 + 2 + 3 + …']], s.mode, v => { s.mode = v; update(); });
    const rs = L.slider('ratio r (geometric)', { min: .1, max: 2, step: .05, value: s.r, fmt: v => v.toFixed(2) }, v => { s.r = v; update(); });
    const run = L.loop(dt => { s.acc += dt; if (s.acc > .12) { s.acc = 0; if (s.shown >= s.k) return false; s.shown++; update(); } });
    L.playButton(run, ['Add terms one by one', 'Pause'], () => { if (s.shown >= s.k) s.shown = 0; });
    const term = i => s.mode === 'geo' ? s.r ** i : s.mode === 'harm' ? 1 / (i + 1) : i + 1;
    const partial = n => { let t = 0; for (let i = 0; i < n; i++) t += term(i); return t; };
    function update() {
      rs.input.disabled = s.mode !== 'geo';
      const S = partial(s.shown), lim = s.mode === 'geo' && s.r < 1 ? 1 / (1 - s.r) : null;
      L.stats([['terms added', s.shown], ['partial sum', fmtN(S, 3), 'accent'], ['last term', s.shown ? fmtN(term(s.shown - 1), 4) : '—'],
        lim ? ['limit 1/(1 − r)', fmtN(lim, 3), 'ok'] : ['limit', s.mode === 'geo' && Math.abs(s.r - 1) < 1e-9 ? 'none (grows like n)' : 'none: diverges', 'err']]);
      L.insight(s.mode === 'geo'
        ? s.r < 1 ? `With r = ${s.r.toFixed(2)} each term is a fixed fraction of the one before, so the terms shrink fast enough that the total <b>converges</b> to 1/(1 − r) = ${fmtN(1 / (1 - s.r), 3)}. At r = ½: 1 + ½ + ¼ + … = 2 — the first term is half of the total, so a halving algorithm’s total work is dominated by its <b>first</b> step (O(n) for n + n/2 + n/4 + …).`
          : s.r > 1.001 ? `With r = ${s.r.toFixed(2)} &gt; 1 the terms grow and the sum explodes — but notice the <b>last term dominates</b>: the whole sum is less than ${fmtN(s.r / (s.r - 1), 2)}× the last term. With r = 2, 1 + 2 + 4 + … + 2ᵏ = 2ᵏ⁺¹ − 1: a full binary tree’s levels, or all the copying a doubling array has ever done, cost about as much as the last level alone.`
            : `At r = 1 every term is 1, so n terms add to n: no limit, linear growth. The boundary between converging and diverging geometric series is exactly |r| = 1.`
        : s.mode === 'harm' ? `The harmonic series <b>diverges</b> even though its terms shrink to 0 — just very slowly: the partial sum is about ln n + 0.577. Terms going to zero is necessary for a sum to converge, not sufficient. In CS this is the “n/1 + n/2 + n/3 + …” pattern: O(n log n).`
          : `The arithmetic series grows like n²/2: 1 + 2 + … + n = n(n + 1)/2. Every nested loop of the form <code>for i: for j &lt; i</code> is this sum in disguise.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, left = 48, right = c.w - 12, top = 18, bottom = c.h - 26;
      const all = Array.from({ length: s.k }, (_, i) => partial(i + 1));
      const lim = s.mode === 'geo' && s.r < 1 ? 1 / (1 - s.r) : null;
      const ymax = Math.max(lim ? lim * 1.12 : 0, s.mode === 'geo' && s.r >= 1 ? Math.min(all[s.k - 1], 60) : all[s.k - 1] * 1.05, 1.5);
      const X = i => left + (right - left) * (i + .5) / s.k, Y = v => bottom - (bottom - top) * Math.min(v, ymax * 1.02) / ymax, bw = (right - left) / s.k;
      D.line(ctx, left, bottom, right, bottom, P.strong, 1); D.line(ctx, left, top, left, bottom, P.strong, 1);
      [0, ymax / 2, ymax].forEach(v => D.text(ctx, fmtN(v, v < 10 ? 1 : 0), left - 6, Y(v), { color: P.faint, size: 10, align: 'right', mono: true }));
      if (lim) { ctx.save(); ctx.setLineDash([6, 4]); D.line(ctx, left, Y(lim), right, Y(lim), P.ok, 1.4); ctx.restore(); D.text(ctx, `limit ${fmtN(lim, 2)}`, right, Y(lim) - 9, { color: P.ok, size: 10.5, align: 'right', weight: 650 }); }
      for (let i = 0; i < s.shown; i++) fillRR(ctx, X(i) - bw * .35, Y(term(i)), bw * .7, bottom - Y(term(i)), 2, P.alpha('dim', .35));
      ctx.beginPath();
      for (let i = 0; i < s.shown; i++) { const px = X(i), py = Y(all[i]); i ? ctx.lineTo(px, py) : ctx.moveTo(px, py); }
      ctx.strokeStyle = P.accent; ctx.lineWidth = 2.4; ctx.stroke();
      if (s.shown) D.dot(ctx, X(s.shown - 1), Y(all[s.shown - 1]), 4.5, P.accent);
      if (all[s.shown - 1] > ymax) D.text(ctx, '↑ off the chart', X(s.shown - 1), top + 8, { color: P.err, size: 10, align: 'right' });
      D.text(ctx, 'bars: each term · line: running total', left + 6, top, { color: P.faint, size: 10 });
      D.text(ctx, 'terms →', right, bottom + 14, { color: P.faint, size: 10, align: 'right' });
    };
    update();
  },
});

/* ============================================================== math-mod == */
defineLab('math-mod', {
  title: 'Modular arithmetic is clock arithmetic',
  hint: 'Numbers wrap around after m, like hours on a clock. Pick an operation and a number <b>a</b>, press <b>Play</b>, and see which numbers get visited. The magic ingredient is gcd(a, m).',
  mount(L) {
    const s = { m: 12, a: 5, mode: 'add', shown: 0, acc: 0 };
    const c = L.canvas(w => Math.min(360, Math.max(290, w * .55)));
    L.seg('operation', [['add', 'keep adding a'], ['mul', 'multiply by a'], ['pow', 'powers of a']], s.mode, v => { s.mode = v; s.shown = 0; update(); });
    L.slider('modulus m', { min: 2, max: 24, value: s.m }, v => { s.m = v; s.shown = 0; update(); });
    L.slider('a', { min: 1, max: 23, value: s.a }, v => { s.a = v; s.shown = 0; update(); });
    const run = L.loop(dt => { s.acc += dt; if (s.acc > .45) { s.acc = 0; if (s.shown >= seq().length - 1) return false; s.shown++; L.redraw(); update(); } });
    L.playButton(run, ['Play', 'Pause'], () => { if (s.shown >= seq().length - 1) s.shown = 0; });
    L.button('m = 13 (prime)', () => { s.m = 13; L.sliders.querySelectorAll('input')[0].value = 13; L.sliders.querySelectorAll('input')[0].dispatchEvent(new Event('input')); });
    const A = () => s.a % s.m;
    /* the walk from the start until the first repeat */
    function seq() {
      const out = [], seen = new Set();
      let x = s.mode === 'pow' ? 1 % s.m : 0;
      if (s.mode === 'mul') return Array.from({ length: s.m }, (_, i) => i);
      while (!seen.has(x)) { seen.add(x); out.push(x); x = s.mode === 'add' ? (x + A()) % s.m : (x * A()) % s.m; }
      out.push(x);
      return out;
    }
    const inverse = () => { for (let x = 1; x < s.m; x++) if ((A() * x) % s.m === 1) return x; return null; };
    const isPrime = n => { if (n < 2) return false; for (let d = 2; d * d <= n; d++) if (n % d === 0) return false; return true; };
    function update() {
      const q = seq(), g = gcd(A(), s.m), inv = inverse(), visited = new Set(q).size;
      const imgs = new Set(Array.from({ length: s.m }, (_, x) => (x * A()) % s.m)).size;
      L.stats([['a mod m', `${s.a} mod ${s.m} = ${A()}`], ['gcd(a, m)', g, g === 1 ? 'ok' : 'err'],
        s.mode === 'mul' ? ['distinct results', `${imgs} / ${s.m}`, imgs === s.m ? 'ok' : 'err'] : [s.mode === 'pow' ? 'cycle length (order)' : 'numbers visited', s.mode === 'pow' ? q.length - 1 - q.indexOf(q[q.length - 1]) : `${visited} / ${s.m}`, 'accent'],
        ['inverse a⁻¹', inv ? `${inv}  (${A()}·${inv} = ${A() * inv} ≡ 1)` : 'none', inv ? 'ok' : 'err'],
        s.mode === 'pow' && isPrime(s.m) && A() ? ['Fermat: a^(m−1) mod m', `${A()}${sup(s.m - 1)} ≡ ${Number((BigInt(A()) ** BigInt(s.m - 1)) % BigInt(s.m))}`, 'ok'] : null]);
      L.insight(s.mode === 'add'
        ? (g === 1 ? `Adding ${A()} again and again visits <b>every</b> number 0…${s.m - 1} before returning to 0, because gcd(${A()}, ${s.m}) = 1. Hash tables with open addressing use exactly this: a probe step coprime with the table size is guaranteed to reach every slot.`
          : `gcd(${A()}, ${s.m}) = ${g}, so adding ${A()} only ever lands on multiples of ${g}: ${s.m / g} of the ${s.m} numbers. A probe step that shares a factor with the table size leaves slots unreachable.`)
        : s.mode === 'mul' ? (g === 1 ? `Multiplying by ${A()} <b>shuffles</b> 0…${s.m - 1} — every result appears exactly once — so it can be undone: the inverse of ${A()} is ${inv}, and “dividing by ${A()}” means multiplying by ${inv}. RSA and modular hashing both rely on inverses existing.`
          : `Because gcd(${A()}, ${s.m}) = ${g} ≠ 1, several inputs collide on the same result, so multiplication by ${A()} cannot be undone: there is no x with ${A()}·x ≡ 1 (mod ${s.m}). With a prime modulus every non-zero a has an inverse.`)
          : `Powers of a eventually cycle, because there are only ${s.m} possible values. When m is prime, Fermat’s little theorem says a^(m−1) ≡ 1 for every a not divisible by m — the basis of the Fermat primality test and of fast modular inverses (a⁻¹ = a^(m−2)).`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, cx = c.w / 2, cy = c.h / 2 + 4, R = Math.min(c.w, c.h) * .38;
      const pos = x => { const t = -Math.PI / 2 + TAU * x / s.m; return [cx + R * Math.cos(t), cy + R * Math.sin(t)]; };
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.strokeStyle = P.border; ctx.lineWidth = 1.5; ctx.stroke();
      const q = seq(), visited = new Set();
      if (s.mode === 'mul') {
        for (let x = 0; x < s.m; x++) {
          const y = (x * A()) % s.m, [x1, y1] = pos(x), [x2, y2] = pos(y);
          if (x === y) { D.dot(ctx, x1, y1, 17, null, P.alpha('ok', .6), 1.4); continue; }
          D.arrow(ctx, lerp(x1, x2, .1), lerp(y1, y2, .1), lerp(x1, x2, .86), lerp(y1, y2, .86), P.alpha(gcd(A(), s.m) === 1 ? 'accent' : 'err', .7), 1.5, 8);
        }
      } else {
        for (let i = 0; i < s.shown; i++) {
          const [x1, y1] = pos(q[i]), [x2, y2] = pos(q[i + 1]);
          D.arrow(ctx, lerp(x1, x2, .08), lerp(y1, y2, .08), lerp(x1, x2, .9), lerp(y1, y2, .9), i === s.shown - 1 ? P.accent : P.alpha('accent', .45), i === s.shown - 1 ? 2.4 : 1.5, 9);
        }
        for (let i = 0; i <= s.shown; i++) visited.add(q[i]);
      }
      for (let x = 0; x < s.m; x++) {
        const [px, py] = pos(x), on = s.mode === 'mul' || visited.has(x), cur = s.mode !== 'mul' && x === q[s.shown];
        D.dot(ctx, px, py, 13, cur ? P.accent : on ? P.alpha('accent', .25) : P.surface2, on ? P.accent : P.border, 1.4);
        D.text(ctx, String(x), px, py, { color: cur ? P.bg : on ? P.text : P.faint, size: 11.5, align: 'center', mono: true, weight: 700 });
      }
      D.text(ctx, `mod ${s.m}`, cx, cy - 8, { color: P.dim, size: 14, align: 'center', weight: 700, mono: true });
      D.text(ctx, s.mode === 'add' ? `x → x + ${A()}` : s.mode === 'mul' ? `x → ${A()}·x` : `x → ${A()}·x from 1`, cx, cy + 12, { color: P.faint, size: 11, align: 'center', mono: true });
    };
    update();
  },
});

/* =========================================================== math-euclid == */
defineLab('math-euclid', {
  title: 'Euclid’s algorithm: tile a rectangle with squares',
  hint: 'Cut the biggest square you can from an <b>a × b</b> rectangle, again and again. The last square tiles everything before it exactly, so its side divides both a and b: it is the <b>gcd</b>.',
  mount(L) {
    const s = { a: 42, b: 30, shown: 0, acc: 0 };
    const c = L.canvas(w => w < 560 ? 420 : 300);
    const sa = L.slider('a', { min: 1, max: 89, value: s.a }, v => { s.a = v; s.shown = 0; update(); });
    const sb = L.slider('b', { min: 1, max: 89, value: s.b }, v => { s.b = v; s.shown = 0; update(); });
    const run = L.loop(dt => { s.acc += dt; if (s.acc > .35) { s.acc = 0; if (s.shown >= plan().squares.length) return false; s.shown++; update(); } });
    L.playButton(run, ['Cut squares', 'Pause'], () => { if (s.shown >= plan().squares.length) s.shown = 0; });
    const pick = (label, a, b) => L.button(label, () => { run.stop(); sa.set(a, true); sb.set(b, true); s.a = a; s.b = b; s.shown = plan().squares.length; update(); });
    pick('42 × 30', 42, 30); pick('89 × 55 (Fibonacci)', 89, 55); pick('17 × 5', 17, 5);
    function plan() {
      const squares = [], rows = [];
      let x = 0, y = 0, w = Math.max(s.a, s.b), h = Math.min(s.a, s.b), step = 0;
      let A = w, B = h;
      while (B) { rows.push([A, B, Math.floor(A / B), A % B]); [A, B] = [B, A % B]; }
      while (w && h) {
        if (w >= h) { const q = Math.floor(w / h); for (let i = 0; i < q; i++) squares.push({ x: x + i * h, y, s: h, step }); x += q * h; w -= q * h; }
        else { const q = Math.floor(h / w); for (let i = 0; i < q; i++) squares.push({ x, y: y + i * w, s: w, step }); y += q * w; h -= q * w; }
        step++;
      }
      return { squares, rows };
    }
    const extended = (a, b) => { if (!b) return [a, 1, 0]; const [g, x, y] = extended(b, a % b); return [g, y, x - Math.floor(a / b) * y]; };
    function update() {
      const big = Math.max(s.a, s.b), small = Math.min(s.a, s.b), [g, x, y] = extended(big, small), { rows } = plan();
      L.stats([['gcd', g, 'accent'], ['lcm = a·b / gcd', big * small / g], ['division steps', rows.length],
        ['Bézout', `${big}·(${x}) + ${small}·(${y}) = ${g}`, 'ok']]);
      L.insight(s.a === 89 && s.b === 55 || s.a === 55 && s.b === 89
        ? `Consecutive Fibonacci numbers are Euclid’s <b>worst case</b>: every quotient is 1, so each step shrinks the numbers as little as possible. Even so the number of steps grows only like log(min(a, b)) — about 5 × (number of decimal digits). gcd is fast even for 1000-digit numbers, which is what makes RSA key generation possible.`
        : `Each row of the table is one step: <b>a = q·b + r</b>, then continue with (b, r). Anything that divides a and b also divides r = a − q·b, so the gcd never changes while the numbers shrink. When r hits 0, b is the answer. In code: <code>while b: a, b = b, a % b</code>. The Bézout line (from the extended algorithm) is how modular inverses are computed.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, narrow = c.w < 560, { squares, rows } = plan();
      const W = Math.max(s.a, s.b), H = Math.min(s.a, s.b);
      const areaW = narrow ? c.w - 24 : c.w * .6 - 24, areaH = narrow ? 250 : c.h - 24;
      const k = Math.min(areaW / W, areaH / H), ox = 12, oy = 12;
      fillRR(ctx, ox, oy, W * k, H * k, 3, P.alpha('dim', .08), P.strong, 1.5);
      squares.slice(0, s.shown).forEach((q, i) => {
        const col = P.series[q.step % P.series.length], last = i === s.shown - 1;
        ctx.fillStyle = P.alpha(col, last ? .55 : .3); ctx.fillRect(ox + q.x * k, oy + q.y * k, q.s * k, q.s * k);
        ctx.strokeStyle = col; ctx.lineWidth = 1.4; ctx.strokeRect(ox + q.x * k + .5, oy + q.y * k + .5, q.s * k - 1, q.s * k - 1);
        if (q.s * k > 22) D.text(ctx, String(q.s), ox + (q.x + q.s / 2) * k, oy + (q.y + q.s / 2) * k, { color: P.text, size: Math.min(13, q.s * k * .3), align: 'center', mono: true, weight: 700 });
      });
      D.text(ctx, `${W} × ${H}`, ox + W * k - 4, oy + H * k + 12, { color: P.faint, size: 10.5, align: 'right', mono: true });
      // the division table
      const tx = narrow ? 14 : c.w * .6 + 8, ty = narrow ? oy + H * k + 34 : 22;
      D.text(ctx, 'a = q·b + r', tx, ty, { color: P.dim, size: 11.5, weight: 700, mono: true });
      const doneSteps = s.shown ? squares[s.shown - 1].step + (s.shown === squares.length ? 1 : 0) : 0;
      rows.slice(0, narrow ? 7 : 11).forEach(([A, B, q, r], i) => {
        const on = i < doneSteps;
        D.text(ctx, `${A} = ${q}·${B} + ${r}`, tx, ty + 20 + i * 19, { color: on ? (r === 0 ? P.ok : P.text) : P.faint, size: 12, mono: true, weight: on ? 650 : 500 });
      });
      if (rows.length > (narrow ? 7 : 11)) D.text(ctx, '…', tx, ty + 20 + (narrow ? 7 : 11) * 19, { color: P.faint, size: 12 });
    };
    s.shown = plan().squares.length;
    update();
  },
});

/* ============================================================ math-sieve == */
defineLab('math-sieve', {
  title: 'The sieve of Eratosthenes',
  hint: 'Every number that survives is prime. For each prime p, cross off its multiples — starting at <b>p²</b>, and stopping once p² passes N. Press <b>Play</b>.',
  mount(L) {
    const N = 120;
    const s = { i: 0, acc: 0, speed: 12 };
    const c = L.canvas(w => w < 520 ? 400 : 300);
    const events = [];
    (() => {
      const comp = new Uint8Array(N + 1);
      for (let p = 2; p <= N; p++) {
        if (comp[p]) continue;
        events.push({ t: 'prime', p });
        if (p * p > N) continue;
        for (let m = p * p; m <= N; m += p) { events.push({ t: 'cross', p, m, dup: !!comp[m] }); comp[m] = comp[m] || p; }
      }
    })();
    const lastSieving = events.filter(e => e.t === 'cross').pop().p;
    L.slider('speed', { min: 2, max: 60, value: s.speed, fmt: v => `${Math.round(v)} steps/s` }, v => { s.speed = v; });
    const run = L.loop(dt => { s.acc += dt * s.speed; while (s.acc >= 1) { s.acc--; if (s.i >= events.length) { update(); return false; } s.i++; } update(); });
    L.playButton(run, ['Play', 'Pause'], () => { if (s.i >= events.length) s.i = 0; });
    L.button('Next prime', () => { run.stop(); let j = s.i + 1; while (j < events.length && events[j].t !== 'prime') j++; s.i = Math.min(events.length, j + 1); update(); });
    L.button('Finish', () => { run.stop(); s.i = events.length; update(); });
    L.button('Reset', () => { run.stop(); s.i = 0; update(); });
    const trialDivisions = (() => { let t = 0; for (let n = 2; n <= N; n++) { for (let d = 2; d * d <= n; d++) { t++; if (n % d === 0) break; } } return t; })();
    function state() {
      const st = Array(N + 1).fill(0), by = Array(N + 1).fill(0);
      let cur = null, crosses = 0;
      for (let j = 0; j < s.i; j++) { const e = events[j]; if (e.t === 'prime') { st[e.p] = 2; cur = e.p; } else { crosses++; if (!st[e.m]) { st[e.m] = 1; by[e.m] = e.p; } } }
      return { st, by, cur, crosses, last: events[s.i - 1] };
    }
    function update() {
      const { st, cur, crosses } = state(), primes = st.filter(v => v === 2).length;
      const allPrimes = events.filter(e => e.t === 'prime').length;
      L.stats([['current prime p', cur ?? '—', 'accent'], ['primes found', `${primes} / ${allPrimes}`], ['cross-offs so far', crosses],
        ['trial division would do', `${trialDivisions} divisions`]]);
      L.insight(cur && cur > lastSieving
        ? `Once p² &gt; N (here ${cur}² = ${cur * cur} &gt; ${N}), every composite number up to N has already been crossed off — a composite n always has a prime factor ≤ √n. So everything left is prime. The sieve does about N·log log N work in total: nearly linear.`
          : `Why start at <b>p²</b>? Smaller multiples of p, such as 2p or 3p, have a smaller prime factor and were already crossed off by it. Numbers crossed twice (for example 12, by 2 and by 3) are why the sieve does a little more than N steps. Use it whenever you need all primes up to a limit; test a single number with trial division up to √n.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, cols = c.w < 520 ? 10 : 15, rows = Math.ceil(N / cols), cs = Math.min((c.w - 16) / cols, (c.h - 12) / rows), x0 = (c.w - cs * cols) / 2;
      const { st, by, cur, last } = state();
      for (let n = 1; n <= N; n++) {
        const i = n - 1, x = x0 + (i % cols) * cs, y = 6 + Math.floor(i / cols) * cs;
        const isCur = n === cur, justHit = last && last.t === 'cross' && last.m === n;
        const fill = n === 1 ? P.alpha('dim', .08) : st[n] === 2 ? P.alpha('accent', isCur ? .95 : .55) : st[n] === 1 ? P.alpha('dim', .06) : P.surface2;
        fillRR(ctx, x + 2, y + 2, cs - 4, cs - 4, 5, fill, justHit ? P.err : isCur ? P.accent : P.border, justHit ? 2 : 1);
        D.text(ctx, String(n), x + cs / 2, y + cs / 2, { color: st[n] === 2 ? (isCur ? P.bg : P.text) : st[n] === 1 ? P.alpha('dim', .45) : P.dim, size: Math.min(12, cs * .36), align: 'center', mono: true, weight: 650 });
        if (st[n] === 1) D.line(ctx, x + 6, y + cs - 6, x + cs - 6, y + 6, P.alpha(P.series[[2, 3, 5, 7].indexOf(by[n])] || P.err, .8), 1.6);
      }
    };
    update();
  },
});

/* ============================================================ math-graph == */
defineLab('math-graph', {
  title: 'Graph playground',
  hint: '<b>Click empty space</b> to add a vertex. <b>Click one vertex, then another</b> to add or remove the edge between them. Drag vertices to move them. Then switch what the colours show.',
  mount(L) {
    const s = { nodes: [], edges: new Set(), sel: null, drag: null, view: 'deg', src: 0 };
    const c = L.canvas(w => w < 520 ? 320 : 330);
    const key = (i, j) => i < j ? `${i}-${j}` : `${j}-${i}`;
    const adj = () => { const a = s.nodes.map(() => []); s.edges.forEach(k => { const [i, j] = k.split('-').map(Number); a[i].push(j); a[j].push(i); }); return a; };
    const PRE = {
      path: [5, i => [[.12 + i * .19, .5]], [[0, 1], [1, 2], [2, 3], [3, 4]]],
      cycle: [6, i => [[.5 + .32 * Math.cos(i * TAU / 6 - Math.PI / 2), .5 + .38 * Math.sin(i * TAU / 6 - Math.PI / 2)]], [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0]]],
      k5: [5, i => [[.5 + .3 * Math.cos(i * TAU / 5 - Math.PI / 2), .52 + .38 * Math.sin(i * TAU / 5 - Math.PI / 2)]], [[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]],
      tree: [7, i => [[[.5, .12], [.3, .45], [.7, .45], [.18, .82], [.4, .82], [.6, .82], [.82, .82]][i]], [[0, 1], [0, 2], [1, 3], [1, 4], [2, 5], [2, 6]]],
      k33: [6, i => [[i < 3 ? .25 : .75, .2 + (i % 3) * .3]], [[0, 3], [0, 4], [0, 5], [1, 3], [1, 4], [1, 5], [2, 3], [2, 4], [2, 5]]],
      house: [5, i => [[[.3, .85], [.7, .85], [.7, .45], [.3, .45], [.5, .12]][i]], [[0, 1], [1, 2], [2, 3], [3, 0], [0, 2], [1, 3], [2, 4], [3, 4]]],
      split: [7, i => [[[.15, .3], [.35, .2], [.3, .6], [.62, .3], [.85, .25], [.8, .7], [.6, .72]][i]], [[0, 1], [1, 2], [2, 0], [3, 4], [4, 5], [5, 6], [6, 3]]],
    };
    const load = name => { const [n, f, e] = PRE[name]; s.nodes = Array.from({ length: n }, (_, i) => { const [[x, y]] = f(i); return { x, y }; }); s.edges = new Set(e.map(([i, j]) => key(i, j))); s.sel = null; s.src = 0; update(); };
    L.seg('colour by', [['deg', 'degree'], ['bfs', 'BFS distance'], ['col', '2-colouring'], ['euler', 'Euler path']], s.view, v => { s.view = v; update(); });
    [['path', 'path'], ['cycle', 'cycle C₆'], ['tree', 'tree'], ['k5', 'complete K₅'], ['k33', 'bipartite K₃,₃'], ['house', 'house'], ['split', 'two pieces']]
      .forEach(([k, l]) => L.button(l, () => load(k)));
    L.button('Clear', () => { s.nodes = []; s.edges.clear(); s.sel = null; update(); });
    let v = null;
    const nodeAt = (x, y) => { if (!v) return null; const i = s.nodes.findIndex(n => Math.hypot(v.sx(n.x) - x, v.sy(n.y) - y) < 16); return i < 0 ? null : i; };
    L.drag(c, {
      hit: nodeAt,
      move: (i, x, y) => {
        if (!s.drag || s.drag.i !== i) { s.drag = { i, x, y, moved: false }; return; }
        if (!s.drag.moved && Math.hypot(x - s.drag.x, y - s.drag.y) < 5) return;
        s.drag.moved = true;
        s.nodes[i] = { x: clamp(v.ix(x), .04, .96), y: clamp(v.iy(y), .05, .95) }; L.redraw();
      },
      up: i => {
        const moved = s.drag && s.drag.moved; s.drag = null;
        if (moved) return;
        if (s.sel == null) { s.sel = i; s.src = i; }
        else if (s.sel === i) s.sel = null;
        else { const k = key(s.sel, i); s.edges.has(k) ? s.edges.delete(k) : s.edges.add(k); s.sel = null; }
        update();
      },
      down: (x, y) => {
        if (s.sel != null) { s.sel = null; update(); return; }
        if (s.nodes.length >= 14) return;
        s.nodes.push({ x: clamp(v.ix(x), .04, .96), y: clamp(v.iy(y), .05, .95) }); update();
      },
    });
    function analyse() {
      const a = adj(), n = s.nodes.length, comp = Array(n).fill(-1);
      let nc = 0;
      for (let i = 0; i < n; i++) { if (comp[i] >= 0) continue; const q = [i]; comp[i] = nc; while (q.length) { const u = q.shift(); a[u].forEach(w => { if (comp[w] < 0) { comp[w] = nc; q.push(w); } }); } nc++; }
      const color = Array(n).fill(-1), bad = new Set();
      for (let i = 0; i < n; i++) { if (color[i] >= 0) continue; color[i] = 0; const q = [i]; while (q.length) { const u = q.shift(); a[u].forEach(w => { if (color[w] < 0) { color[w] = 1 - color[u]; q.push(w); } else if (color[w] === color[u]) bad.add(key(u, w)); }); } }
      const dist = Array(n).fill(Infinity);
      if (n) { const src = Math.min(s.src, n - 1); dist[src] = 0; const q = [src]; while (q.length) { const u = q.shift(); a[u].forEach(w => { if (dist[w] === Infinity) { dist[w] = dist[u] + 1; q.push(w); } }); } }
      const deg = a.map(x => x.length), odd = deg.map((d, i) => d % 2 ? i : -1).filter(i => i >= 0);
      const nonIso = deg.map((d, i) => d ? i : -1).filter(i => i >= 0), eulerConn = nonIso.every(i => comp[i] === comp[nonIso[0]]);
      const E = s.edges.size;
      return { a, n, comp, nc, color, bad, dist, deg, odd, E, eulerConn, nonIso,
        tree: n > 0 && nc === 1 && E === n - 1, cycle: E > n - nc, bip: bad.size === 0,
        euler: !E ? 'no edges' : !eulerConn ? 'no (edges in two pieces)' : odd.length === 0 ? 'circuit (every degree even)' : odd.length === 2 ? `path from ${odd[0]} to ${odd[1]}` : `no (${odd.length} odd vertices)` };
    }
    function update() {
      const g = analyse();
      L.stats([['vertices V', g.n], ['edges E', g.E], ['sum of degrees', `${g.deg.reduce((x, y) => x + y, 0)} = 2E`, 'accent'], ['components', g.nc],
        ['tree?', g.tree ? 'yes' : 'no', g.tree ? 'ok' : ''], ['has a cycle?', g.cycle ? 'yes' : 'no'], ['bipartite?', g.bip ? 'yes' : 'no (odd cycle)', g.bip ? 'ok' : 'err'], ['Euler', g.euler]]);
      const tips = {
        deg: `<b>Handshake lemma:</b> every edge has two ends, so the degrees always add up to exactly 2E — and the number of odd-degree vertices is always even. A graph is a <b>tree</b> exactly when it is connected and has V − 1 edges; one more edge always creates a cycle.`,
        bfs: `Breadth-first search explores in rings: distance 0, then 1, then 2… so the first time it reaches a vertex is along a shortest path (counting edges). Click a vertex to make it the source. Vertices in another component stay at ∞.`,
        col: g.bip ? `This graph is <b>bipartite</b>: its vertices split into two groups with every edge crossing between them — like students and courses, or tasks and machines. BFS finds the split by alternating colours layer by layer.`
          : `Not bipartite: the red edge joins two vertices of the same colour. A graph can be 2-coloured <b>exactly when it has no odd-length cycle</b> — a triangle or a pentagon can never alternate two colours.`,
        euler: `An <b>Euler path</b> uses every edge exactly once. Euler proved (the Königsberg bridges, 1736) that a connected graph has one exactly when 0 or 2 vertices have odd degree: each time you pass through a vertex you use one edge in and one out. Odd vertices are ringed. Try the house: 2 odd vertices, so you can draw it without lifting the pen, starting at one of them.`,
      };
      L.insight(tips[s.view]);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      v = D.view(c, { x0: 0, x1: 1, y0: 1, y1: 0, pad: 14 });
      v = { ...v, sy: y => 14 + y * (c.h - 28), iy: py => (py - 14) / (c.h - 28) };
      const g = analyse(), layer = ['#6cb6ff', '#4fcf8e', '#f5b453', '#f2727c', '#b996ff', '#4fc1b0', '#f28ac0'];
      if (!g.n) D.text(ctx, 'Click anywhere to add a vertex, or pick a preset below.', c.w / 2, c.h / 2, { color: P.faint, size: 12.5, align: 'center' });
      s.edges.forEach(k => {
        const [i, j] = k.split('-').map(Number), A = s.nodes[i], B = s.nodes[j];
        const badEdge = s.view === 'col' && g.bad.has(k);
        D.line(ctx, v.sx(A.x), v.sy(A.y), v.sx(B.x), v.sy(B.y), badEdge ? P.err : P.alpha('dim', .75), badEdge ? 3.2 : 2);
      });
      s.nodes.forEach((nd, i) => {
        let fill = P.surface2, stroke = P.accent, label = String(i), sub = '';
        if (s.view === 'deg') { sub = `deg ${g.deg[i]}`; fill = P.alpha('accent', .12 + .1 * Math.min(g.deg[i], 6)); }
        if (s.view === 'bfs') { const d = g.dist[i]; fill = d === Infinity ? P.surface2 : P.alpha(layer[d % layer.length], .75); stroke = d === Infinity ? P.border : layer[d % layer.length]; sub = d === Infinity ? '∞' : `d = ${d}`; }
        if (s.view === 'col') { fill = g.color[i] ? P.alpha('#f5b453', .8) : P.alpha('#6cb6ff', .8); stroke = fill; }
        if (s.view === 'euler') { const odd = g.deg[i] % 2 === 1; stroke = odd ? P.err : P.border; sub = `deg ${g.deg[i]}`; if (odd) D.dot(ctx, v.sx(nd.x), v.sy(nd.y), 20, null, P.err, 2); }
        if (i === s.sel) D.dot(ctx, v.sx(nd.x), v.sy(nd.y), 19, P.alpha('accent', .25));
        D.dot(ctx, v.sx(nd.x), v.sy(nd.y), 14, fill, stroke, 2);
        D.text(ctx, label, v.sx(nd.x), v.sy(nd.y), { color: P.text, size: 12, align: 'center', weight: 700, mono: true });
        if (sub) D.text(ctx, sub, v.sx(nd.x), v.sy(nd.y) + 24, { color: P.dim, size: 10, align: 'center', mono: true });
      });
    };
    load('house');
  },
});

/* ======================================================== math-transform == */
defineLab('math-transform', {
  title: 'A matrix is a transformation of the plane',
  hint: 'The columns of the matrix are where the two unit arrows <b>î</b> and <b>ĵ</b> land. <b>Drag their tips</b>, or pick a preset. The grid, the square and the letter F all move with them.',
  mount(L) {
    const s = { m: [1, 0, 0, 1], eig: true };   // [a, b, c, d] = [[a, b], [c, d]]; î = (a, c), ĵ = (b, d)
    const c = L.canvas(w => Math.min(400, Math.max(300, w * .62)));
    let v = null;
    L.drag(c, {
      hit: (x, y) => { if (!v) return null; const [a, b, cc, d] = s.m; if (Math.hypot(v.sx(a) - x, v.sy(cc) - y) < 16) return 'i'; if (Math.hypot(v.sx(b) - x, v.sy(d) - y) < 16) return 'j'; return null; },
      move: (k, x, y) => { const px = Math.round(v.ix(x) * 4) / 4, py = Math.round(v.iy(y) * 4) / 4; if (k === 'i') { s.m[0] = clamp(px, -3.5, 3.5); s.m[2] = clamp(py, -3.5, 3.5); } else { s.m[1] = clamp(px, -3.5, 3.5); s.m[3] = clamp(py, -3.5, 3.5); } update(); },
    });
    const go = target => { const from = [...s.m]; L.tween(600, t => { s.m = from.map((x, i) => lerp(x, target[i], t)); update(); }); };
    const r45 = Math.SQRT1_2;
    [['identity', [1, 0, 0, 1]], ['rotate 45°', [r45, -r45, r45, r45]], ['scale ×2', [2, 0, 0, 2]], ['shear', [1, 1, 0, 1]], ['reflect', [-1, 0, 0, 1]],
      ['stretch', [2, 1, 1, 2]], ['squash (det 0)', [1, 2, .5, 1]]].forEach(([l, m]) => L.button(l, () => go(m)));
    L.toggle('eigenvectors', true, x => { s.eig = x; update(); });
    const eigen = () => {
      const [a, b, cc, d] = s.m, tr = a + d, det = a * d - b * cc, disc = tr * tr - 4 * det;
      if (disc < -1e-9) return { real: false, tr, det, re: tr / 2, im: Math.sqrt(-disc) / 2 };
      const r = Math.sqrt(Math.max(0, disc)), ls = [(tr + r) / 2, (tr - r) / 2];
      const vec = l => Math.abs(b) > 1e-9 ? [b, l - a] : Math.abs(cc) > 1e-9 ? [l - d, cc] : null;
      let vs = ls.map(vec);
      if (!vs[0]) vs = Math.abs(ls[0] - a) < 1e-9 ? [[1, 0], [0, 1]] : [[0, 1], [1, 0]];
      return { real: true, tr, det, ls, vs };
    };
    function update() {
      const [a, b, cc, d] = s.m, e = eigen(), det = a * d - b * cc;
      L.stats([['matrix', `[[${fmtN(a, 2)}, ${fmtN(b, 2)}], [${fmtN(cc, 2)}, ${fmtN(d, 2)}]]`], ['determinant', fmtN(det, 2), Math.abs(det) < 1e-6 ? 'err' : det < 0 ? 'err' : 'accent'],
        ['invertible?', Math.abs(det) < 1e-6 ? 'no' : 'yes', Math.abs(det) < 1e-6 ? 'err' : 'ok'],
        ['eigenvalues', e.real ? e.ls.map(x => fmtN(x, 2)).join(', ') : `${fmtN(e.re, 2)} ± ${fmtN(e.im, 2)}i (complex)`]]);
      L.insight(Math.abs(det) < 1e-6
        ? `<b>Determinant 0:</b> the whole plane is squashed onto a line (area × 0). Different inputs land on the same output, so the transformation cannot be undone — the matrix has no inverse, and a system Ax = b has either no solution or infinitely many.`
        : det < 0 ? `<b>Negative determinant:</b> the plane is flipped — the F is mirrored, like a reflection. |det| = ${fmtN(Math.abs(det), 2)} is still the factor by which areas are scaled.`
          : !e.real ? `A rotation leaves <b>no direction unchanged</b>, so there are no real eigenvectors (the eigenvalues are complex). The determinant ${fmtN(det, 2)} says areas are scaled by that factor.`
            : `The determinant ${fmtN(det, 2)} is the area of the shaded parallelogram: every area is multiplied by it. The dashed lines are <b>eigenvectors</b> — directions that only get stretched (by the eigenvalue), never turned. Matrix × vector = combine the columns: A·(x, y) = x·î + y·ĵ.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, [a, b, cc, d] = s.m;
      v = D.view(c, { x0: -4, x1: 4, y0: -3, y1: 3, pad: 10, equal: true });
      const T = (x, y) => [a * x + b * y, cc * x + d * y];
      const seg = (p, q, col, w, dash) => { const [x1, y1] = T(...p), [x2, y2] = T(...q); D.line(ctx, v.sx(x1), v.sy(y1), v.sx(x2), v.sy(y2), col, w, dash); };
      D.grid(ctx, v, P, 1);
      for (let k = -6; k <= 6; k++) { seg([k, -6], [k, 6], P.alpha('accent', .22), 1); seg([-6, k], [6, k], P.alpha('accent', .22), 1); }
      // unit square → parallelogram
      const det = a * d - b * cc, sq = [[0, 0], [1, 0], [1, 1], [0, 1]].map(p => T(...p));
      ctx.beginPath(); sq.forEach(([x, y], i) => i ? ctx.lineTo(v.sx(x), v.sy(y)) : ctx.moveTo(v.sx(x), v.sy(y))); ctx.closePath();
      ctx.fillStyle = P.alpha(det < 0 ? 'err' : 'accent', .22); ctx.fill();
      // an F, to show orientation
      [[[-2.2, -1.6], [-2.2, -.2]], [[-2.2, -.2], [-1.5, -.2]], [[-2.2, -.9], [-1.7, -.9]]].forEach(([p, q]) => seg(p, q, P.text, 3));
      if (s.eig) {
        const e = eigen();
        if (e.real) e.vs.forEach((vv, k) => {
          const n = Math.hypot(...vv) || 1, ux = vv[0] / n, uy = vv[1] / n;
          ctx.save(); ctx.setLineDash([7, 5]); D.line(ctx, v.sx(-6 * ux), v.sy(-6 * uy), v.sx(6 * ux), v.sy(6 * uy), P.alpha(k ? 'ok' : 'ok', .75), 1.6); ctx.restore();
          D.text(ctx, `λ = ${fmtN(e.ls[k], 2)}`, v.sx(2.6 * ux) + 6, v.sy(2.6 * uy) - 10, { color: P.ok, size: 11, weight: 650 });
        });
      }
      D.arrow(ctx, v.sx(0), v.sy(0), v.sx(a), v.sy(cc), P.series[2], 3, 12);
      D.arrow(ctx, v.sx(0), v.sy(0), v.sx(b), v.sy(d), P.series[3], 3, 12);
      D.dot(ctx, v.sx(a), v.sy(cc), 7, P.series[2], P.bg, 2); D.dot(ctx, v.sx(b), v.sy(d), 7, P.series[3], P.bg, 2);
      D.text(ctx, 'î', v.sx(a) + 10, v.sy(cc) - 10, { color: P.series[2], size: 15, weight: 700 });
      D.text(ctx, 'ĵ', v.sx(b) + 10, v.sy(d) - 10, { color: P.series[3], size: 15, weight: 700 });
    };
    update();
  },
});

/* ============================================================ math-gauss == */
defineLab('math-gauss', {
  title: 'Gaussian elimination, one row operation at a time',
  hint: 'Solving three equations in three unknowns is just two moves repeated: <b>subtract a multiple of one row from another</b> to create zeros, then <b>back-substitute</b>. Step through it.',
  mount(L) {
    const SYS = {
      unique: [[2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3]],
      none: [[1, 1, 1, 2], [1, 2, 3, 5], [2, 3, 4, 8]],
      many: [[1, 1, 1, 2], [1, 2, 3, 5], [2, 3, 4, 7]],
    };
    /* tiny exact fractions, so every entry is shown the way you would write it by hand */
    const F = (n, d = 1) => { if (d < 0) { n = -n; d = -d; } const g = gcd(n, d) || 1; return { n: n / g, d: d / g }; };
    const add = (x, y) => F(x.n * y.d + y.n * x.d, x.d * y.d), mul = (x, y) => F(x.n * y.n, x.d * y.d), div = (x, y) => F(x.n * y.d, x.d * y.n);
    const neg = x => F(-x.n, x.d), isZ = x => x.n === 0, show = x => x.d === 1 ? String(x.n) : `${x.n}/${x.d}`;
    const s = { sys: 'unique', i: 0 };
    L.stage.innerHTML = `<div class="mlab-split"><div class="mlab-box"><table class="mlab-table mg-m"></table></div><div class="mlab-box"><p class="mlab-note mg-say"></p></div></div>`;
    const tbl = L.stage.querySelector('.mg-m'), say = L.stage.querySelector('.mg-say');
    L.seg('system', [['unique', 'one solution'], ['none', 'no solution'], ['many', 'infinitely many']], s.sys, v => { s.sys = v; s.i = 0; update(); });
    L.button('← Back', () => { s.i = Math.max(0, s.i - 1); update(); });
    L.button('Next step →', () => { s.i = Math.min(steps().length - 1, s.i + 1); update(); }, 'primary');
    L.button('Restart', () => { s.i = 0; update(); });
    const V = ['x', 'y', 'z'];
    function steps() {
      let M = SYS[s.sys].map(r => r.map(x => F(x)));
      const out = [{ M: M.map(r => [...r]), say: 'Write the system as an <b>augmented matrix</b>: one row per equation, one column per unknown, the right-hand side after the bar.', hl: [] }];
      let row = 0; const piv = [];
      for (let col = 0; col < 3 && row < 3; col++) {
        let p = row; while (p < 3 && isZ(M[p][col])) p++;
        if (p === 3) { out.push({ M: M.map(r => [...r]), say: `No usable pivot in the ${V[col]} column: <b>${V[col]} is a free variable</b>.`, hl: [] }); continue; }
        if (p !== row) { [M[p], M[row]] = [M[row], M[p]]; out.push({ M: M.map(r => [...r]), say: `Swap rows ${row + 1} and ${p + 1} to get a non-zero pivot.`, hl: [row, p] }); }
        for (let r = row + 1; r < 3; r++) {
          if (isZ(M[r][col])) continue;
          const f = div(M[r][col], M[row][col]);
          M[r] = M[r].map((x, k) => add(x, neg(mul(f, M[row][k]))));
          out.push({ M: M.map(rr => [...rr]), say: `R${r + 1} ← R${r + 1} − (${show(f)})·R${row + 1}: this makes the ${V[col]} entry of row ${r + 1} zero, eliminating ${V[col]} from that equation.`, hl: [r], piv: [row, col] });
        }
        piv.push([row, col]); row++;
      }
      const bad = M.findIndex(r => r.slice(0, 3).every(isZ) && !isZ(r[3]));
      if (bad >= 0) { out.push({ M, say: `Row ${bad + 1} now reads <b>0x + 0y + 0z = ${show(M[bad][3])}</b>, which is impossible. The equations contradict each other: <b>no solution</b>. (Geometrically, the three planes have no common point.)`, hl: [bad], end: 'none' }); return out; }
      if (piv.length < 3) { out.push({ M, say: `A row became <b>0 = 0</b>: one equation was a combination of the others and added no information. With ${piv.length} pivots for 3 unknowns there is ${3 - piv.length} free variable, so there are <b>infinitely many solutions</b> — a whole line of them.`, hl: M.map((r, i) => r.every(isZ) ? i : -1).filter(i => i >= 0), end: 'many' }); return out; }
      const x = [null, null, null];
      for (let r = 2; r >= 0; r--) {
        let rhs = M[r][3];
        for (let k = r + 1; k < 3; k++) rhs = add(rhs, neg(mul(M[r][k], x[k])));
        x[r] = div(rhs, M[r][r]);
        out.push({ M, say: `Back-substitute into row ${r + 1}: <b>${V[r]} = ${show(x[r])}</b>.`, hl: [r], sol: x.map(v => v && show(v)) });
      }
      out[out.length - 1].end = 'unique';
      return out;
    }
    function update() {
      const all = steps(), st = all[s.i];
      tbl.innerHTML = `<tr><th></th><th>x</th><th>y</th><th>z</th><th>= rhs</th></tr>` + st.M.map((r, i) =>
        `<tr class="${st.hl.includes(i) ? 'on' : ''}"><td>R${i + 1}</td>${r.map((x, k) => `<td${k === 3 ? ' style="border-left:2px solid var(--border-strong)"' : ''}>${show(x)}</td>`).join('')}</tr>`).join('');
      say.innerHTML = st.say + (st.sol ? `<br><br>Solution so far: ${st.sol.map((v, k) => v ? `${V[k]} = ${v}` : '').filter(Boolean).join(', ')}` : '');
      L.stats([['step', `${s.i + 1} / ${all.length}`], st.end ? ['outcome', { unique: 'exactly one solution', none: 'no solution', many: 'infinitely many' }[st.end], st.end === 'unique' ? 'ok' : 'err'] : null]);
      L.insight(`Elimination costs about <b>n³/3</b> multiplications for n equations — cubic, which is why large linear systems in graphics, ML and simulation use it carefully (or iterative methods). The three outcomes match the determinant: det ≠ 0 means exactly one solution; det = 0 means none or infinitely many.`);
    }
    update();
  },
});

/* ========================================================= math-pagerank == */
defineLab('math-pagerank', {
  title: 'PageRank: an eigenvector found by iteration',
  hint: 'A random surfer clicks a random link on each page, and with probability 1 − d jumps to a random page instead. <b>Iterate</b> the rank update, or <b>release the surfer</b> and count visits — both reach the same answer.',
  mount(L) {
    const names = ['A', 'B', 'C', 'D', 'E'];
    const links = [[0, 1], [0, 2], [1, 2], [2, 0], [3, 2], [3, 0], [4, 3], [4, 2], [1, 4]];
    const pos = [[.5, .15], [.83, .42], [.5, .55], [.17, .42], [.68, .86]];
    const out = names.map((_, i) => links.filter(([a]) => a === i).map(([, b]) => b));
    const s = { d: .85, r: Array(5).fill(.2), it: 0, surf: false, at: 0, visits: Array(5).fill(0), steps: 0, acc: 0, hop: null };
    const c = L.canvas(w => w < 520 ? 360 : 300);
    L.slider('damping d', { min: .5, max: .99, step: .01, value: s.d, fmt: v => v.toFixed(2) }, v => { s.d = v; update(); });
    const iterate = () => {
      const n = 5, nr = Array(n).fill((1 - s.d) / n);
      s.r.forEach((ri, i) => out[i].forEach(j => { nr[j] += s.d * ri / out[i].length; }));
      const delta = nr.reduce((t, x, i) => t + Math.abs(x - s.r[i]), 0);
      s.r = nr; s.it++; s.delta = delta;
    };
    L.button('One iteration', () => { iterate(); update(); });
    const run = L.loop(dt => {
      s.acc += dt;
      if (!s.surf) { if (s.acc > .45) { s.acc = 0; iterate(); update(); if (s.delta < 1e-6) return false; } return; }
      if (s.acc > .05) {
        s.acc = 0;
        for (let k = 0; k < 6; k++) {
          const nxt = Math.random() < s.d ? out[s.at][Math.floor(Math.random() * out[s.at].length)] : Math.floor(Math.random() * 5);
          s.hop = [s.at, nxt]; s.at = nxt; s.visits[nxt]++; s.steps++;
        }
        update();
      }
    });
    L.playButton(run, ['Play', 'Pause']);
    L.toggle('random surfer', false, v => { s.surf = v; if (v) { s.visits.fill(0); s.steps = 0; } update(); });
    L.button('Reset', () => { run.stop(); s.r = Array(5).fill(.2); s.it = 0; s.delta = undefined; s.visits.fill(0); s.steps = 0; update(); });
    function update() {
      const best = s.r.indexOf(Math.max(...s.r));
      L.stats([['iterations', s.it], ['change last step', s.delta === undefined ? '—' : s.delta.toExponential(1), s.delta !== undefined && s.delta < 1e-4 ? 'ok' : ''],
        ['top page', `${names[best]} (${(s.r[best] * 100).toFixed(1)}%)`, 'accent'], s.surf ? ['surfer clicks', s.steps.toLocaleString()] : null]);
      L.insight(s.surf
        ? `The bars now also show how often the surfer has been on each page (outlined). As the clicks pile up, the visit shares converge to the PageRank values: <b>PageRank is the long-run fraction of time a random surfer spends on each page</b> — the stationary distribution of a Markov chain.`
        : `Each iteration multiplies the rank vector by the same matrix: r ← (1 − d)/N + d·M·r. Repeating a matrix multiplication (<b>power iteration</b>) converges to the matrix’s dominant <b>eigenvector</b> — the ranks that no longer change. Four pages link to C, yet <b>A</b> finishes on top (33% vs 32%): C passes its whole vote to A alone, while B, D and E split theirs. Who links to you matters more than how many.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, narrow = c.w < 520;
      const gw = narrow ? c.w : c.w * .55, gh = narrow ? c.h * .6 : c.h;
      const X = p => 20 + p * (gw - 40), Y = p => 14 + p * (gh - 30);
      links.forEach(([a, b]) => {
        let [x1, y1] = [X(pos[a][0]), Y(pos[a][1])], [x2, y2] = [X(pos[b][0]), Y(pos[b][1])];
        const ang = Math.atan2(y2 - y1, x2 - x1);
        if (links.some(([p, q]) => p === b && q === a)) { const ox = -Math.sin(ang) * 6, oy = Math.cos(ang) * 6; x1 += ox; y1 += oy; x2 += ox; y2 += oy; }
        const hot = s.surf && s.hop && s.hop[0] === a && s.hop[1] === b;
        const r1 = 12 + 40 * Math.sqrt(s.r[a]), r2 = 12 + 40 * Math.sqrt(s.r[b]);
        D.arrow(ctx, x1 + Math.cos(ang) * r1, y1 + Math.sin(ang) * r1, x2 - Math.cos(ang) * (r2 + 2), y2 - Math.sin(ang) * (r2 + 2), hot ? P.accent : P.alpha('dim', .6), hot ? 2.6 : 1.5, 8);
      });
      names.forEach((nm, i) => {
        const r = 12 + 40 * Math.sqrt(s.r[i]);
        D.dot(ctx, X(pos[i][0]), Y(pos[i][1]), r, P.alpha('accent', .18 + s.r[i]), P.accent, 1.6);
        D.text(ctx, nm, X(pos[i][0]), Y(pos[i][1]), { color: P.text, size: 13, align: 'center', weight: 700 });
        if (s.surf && i === s.at) D.dot(ctx, X(pos[i][0]) + r * .7, Y(pos[i][1]) - r * .7, 5, P.err);
      });
      // bars
      const bx = narrow ? 30 : gw + 20, by = narrow ? gh + 14 : 26, bwid = narrow ? c.w - 60 : c.w - gw - 40, bh = narrow ? c.h - gh - 36 : c.h - 60;
      const rowH = bh / 5, tot = s.visits.reduce((x, y) => x + y, 0) || 1;
      D.text(ctx, 'rank (share of importance)', bx, by - 12, { color: P.faint, size: 10 });
      names.forEach((nm, i) => {
        const y = by + i * rowH, w = bwid * s.r[i] / .5;
        D.text(ctx, nm, bx - 8, y + rowH / 2, { color: P.dim, size: 11, align: 'right', weight: 700 });
        fillRR(ctx, bx, y + rowH * .2, Math.max(2, w), rowH * .6, 3, P.alpha('accent', .7));
        if (s.surf) fillRR(ctx, bx, y + rowH * .2, Math.max(2, bwid * (s.visits[i] / tot) / .5), rowH * .6, 3, null, P.text, 1.4);
        D.text(ctx, `${(s.r[i] * 100).toFixed(1)}%`, bx + Math.max(2, w) + 6, y + rowH / 2, { color: P.dim, size: 10.5, mono: true });
      });
    };
    update();
  },
});
}
