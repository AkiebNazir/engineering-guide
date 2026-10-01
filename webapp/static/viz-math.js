/* ============================================================================
   Maths for CS Engineers labs, part 1: the language of maths and counting.

     math-sigma      Σ notation is a for-loop: run it term by term
     math-bits       eight bits read as unsigned, signed (two's complement) and hex
     math-float      the 32 bits of an IEEE 754 float, and the value really stored
     math-truth      truth tables side by side: which laws are equivalences
     math-induction  proof by induction as falling dominoes
     math-venn       set operations shaded on a Venn diagram, with code equivalents
     math-function   injective, surjective, bijective as arrow diagrams
     math-choose     the four counting cases listed out: orderings grouped by
                     the selection they belong to, collapsing when order stops mattering
     math-perm       next permutation step by step, and the k-th permutation
                     read off the factorial number system
     math-pascal     Pascal's triangle: C(n, k), its parents, parity, row sums
     math-paths      counting grid paths: the formula, then DP when cells are blocked

   All are object-spec labs (viz.js createLab). The file is wrapped in a block
   because every script shares one global scope.
   ========================================================================= */
'use strict';
{
const fillRR = (ctx, x, y, w, h, r, fill, stroke, lw = 1.2) => {
  D.rrect(ctx, x, y, w, h, r);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
};
const fmtNum = v => Number.isInteger(v) ? v.toLocaleString('en-US') : (Math.abs(v) < 1e-4 ? v.toExponential(3) : v.toFixed(4));
/* a click (not a drag) on a canvas, in CSS pixels */
const onTap = (c, fn) => c.cv.addEventListener('click', e => { const r = c.cv.getBoundingClientRect(); fn(e.clientX - r.left, e.clientY - r.top); });
const binom = (n, k) => { if (k < 0 || k > n) return 0; k = Math.min(k, n - k); let r = 1; for (let i = 1; i <= k; i++) r = r * (n - k + i) / i; return Math.round(r); };

/* ============================================================ math-sigma == */
defineLab('math-sigma', {
  title: 'Σ is just a for-loop',
  hint: 'Pick a sum and press <b>Run the loop</b>. The code is the Σ, one iteration at a time; each bar is one term, and the total is the running accumulator.',
  mount(L) {
    const SUMS = {
      lin: { sym: 'i', lo: 1, term: i => i, code: 'i', closed: n => n * (n + 1) / 2, closedTxt: 'n(n + 1) / 2' },
      sq: { sym: 'i²', lo: 1, term: i => i * i, code: 'i * i', closed: n => n * (n + 1) * (2 * n + 1) / 6, closedTxt: 'n(n + 1)(2n + 1) / 6' },
      pow: { sym: '2ⁱ', lo: 0, term: i => 2 ** i, code: '2 ** i', closed: n => 2 ** (n + 1) - 1, closedTxt: '2ⁿ⁺¹ − 1' },
      half: { sym: '1/2ⁱ', lo: 1, term: i => 1 / 2 ** i, code: '1 / 2 ** i', closed: n => 1 - 1 / 2 ** n, closedTxt: '1 − 1/2ⁿ' },
      harm: { sym: '1/i', lo: 1, term: i => 1 / i, code: '1 / i', closed: n => Math.log(n) + 0.5772156649 + 1 / (2 * n), closedTxt: '≈ ln n + 0.5772', approx: true },
    };
    const s = { key: 'lin', n: 8, k: 0, acc: 0 };
    const c = L.canvas(w => w < 560 ? 420 : 330);
    const S = () => SUMS[s.key];
    const count = () => s.n - S().lo + 1;
    const total = () => { let t = 0; for (let j = 0; j < s.k; j++) t += S().term(S().lo + j); return t; };
    L.seg('sum', [['lin', 'Σ i'], ['sq', 'Σ i²'], ['pow', 'Σ 2ⁱ'], ['half', 'Σ 1/2ⁱ'], ['harm', 'Σ 1/i']], s.key, v => { s.key = v; s.k = 0; run.stop(); update(); });
    L.slider('upper limit n', { min: 1, max: 20, value: s.n }, v => { s.n = v; s.k = Math.min(s.k, count()); update(); });
    const run = L.loop(dt => {
      s.acc += dt;
      if (s.acc > .5) { s.acc = 0; if (s.k >= count()) return false; s.k++; update(); }
    });
    L.playButton(run, ['Run the loop', 'Pause'], () => { if (s.k >= count()) s.k = 0; s.acc = .5; });
    L.button('One iteration', () => { run.stop(); if (s.k >= count()) s.k = 0; else s.k++; update(); });
    L.button('Reset', () => { run.stop(); s.k = 0; update(); });
    function update() {
      const t = total(), done = s.k >= count(), cf = S().closed(s.n);
      L.stats([['iterations', `${s.k} / ${count()}`], ['loop total', fmtNum(t), 'accent'],
        [`closed form ${S().closedTxt}`, fmtNum(cf)],
        done ? ['match', S().approx ? `off by ${fmtN(Math.abs(cf - t), 4)}` : Math.abs(cf - t) < 1e-9 ? 'exact ✓' : '✗', S().approx ? '' : 'ok'] : null]);
      const tips = {
        lin: `Σ i from 1 to n adds 1 + 2 + … + n. Pair the first and last terms (1 + n), the second and second-last (2 + n − 1): every pair makes n + 1, and there are n/2 pairs. That is the whole proof of <b>n(n + 1)/2</b>, and why a double loop <code>for i … for j &lt; i</code> does about n²/2 steps: O(n²).`,
        sq: `Σ i² grows like n³/3. Whenever you see a loop whose inner work is proportional to i² (for example all pairs inside a prefix), the total is cubic.`,
        pow: `Σ 2ⁱ: every term is bigger than all the previous terms together (1 + 2 + 4 = 7 &lt; 8). The last term dominates, so the sum is under twice the last term. This is why a full binary tree with 2ⁿ leaves has fewer than 2ⁿ⁺¹ nodes, and why doubling an array's capacity costs O(1) per append on average.`,
        half: `Σ 1/2ⁱ: half, plus a quarter, plus an eighth… Each term covers half of what is left, so the sum creeps towards 1 and never passes it. An infinite loop of work can have a finite total — the idea behind geometric decay, halving algorithms and <code>1 + 1/2 + 1/4 + … = 2</code>.`,
        harm: `Σ 1/i (the harmonic series) grows without limit, but only like ln n: a million terms add up to about 14.4. It appears when the i-th step costs n/i — for example <code>for i in 1..n: for j in range(0, n, i)</code> — giving O(n log n) in total.`,
      };
      L.insight(tips[s.key]);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, narrow = c.w < 560, sm = S();
      const curI = sm.lo + Math.min(s.k, count() - 1), done = s.k >= count();
      // ---- the Σ, drawn big
      const sx = narrow ? 18 : c.w - 230, sy = narrow ? 14 : 18;
      D.text(ctx, 'maths', sx, sy + 4, { color: P.faint, size: 10, weight: 650 });
      D.text(ctx, String(s.n), sx + 22, sy + 22, { color: P.dim, size: 12, align: 'center', mono: true });
      D.text(ctx, 'Σ', sx + 22, sy + 50, { color: P.accent, size: 38, align: 'center', weight: 500 });
      D.text(ctx, `i=${sm.lo}`, sx + 22, sy + 80, { color: P.dim, size: 12, align: 'center', mono: true });
      D.text(ctx, sm.sym, sx + 46, sy + 50, { color: P.text, size: 22, weight: 600 });
      D.text(ctx, `= ${fmtNum(total())}${done ? '' : ' …'}`, sx + 46, sy + 80, { color: P.dim, size: 13, mono: true });
      // ---- the loop
      const cx = narrow ? 18 : 18, cy = narrow ? 118 : 18, lh = 22;
      D.text(ctx, 'code', cx, cy + 4, { color: P.faint, size: 10, weight: 650 });
      const lines = [
        ['total = 0', s.k === 0 ? '' : ''],
        [`for i in range(${sm.lo}, n + 1):`, s.k > 0 && !done ? `# i = ${curI}` : done ? '# loop finished' : ''],
        [`    total += ${sm.code}`, s.k > 0 ? `# total = ${fmtNum(total())}` : ''],
      ];
      const active = s.k === 0 ? 0 : done ? -1 : 2;
      lines.forEach(([code, note], i) => {
        const y = cy + 22 + i * lh;
        if (i === active) fillRR(ctx, cx - 6, y - 10, (narrow ? c.w - 24 : c.w - 270), 20, 5, P.alpha('accent', .14));
        D.text(ctx, code, cx, y, { color: P.text, size: 12.5, mono: true, weight: 500 });
        if (note) D.text(ctx, note, cx + (narrow ? Math.min(250, c.w * .5) : 250), y, { color: P.accent, size: 12, mono: true, weight: 600 });
      });
      // ---- one bar per term
      const top = narrow ? 232 : 120, bottom = c.h - 26, left = 40, right = c.w - 14;
      const terms = Array.from({ length: count() }, (_, j) => sm.term(sm.lo + j));
      const mx = Math.max(...terms), bw = (right - left) / terms.length;
      D.text(ctx, 'each bar is one term; filled bars are already in the total', left, top - 10, { color: P.faint, size: 10.5 });
      D.line(ctx, left, bottom, right, bottom, P.strong, 1);
      terms.forEach((v, j) => {
        const h = (bottom - top - 12) * v / mx, x = left + j * bw;
        const added = j < s.k, now = j === s.k - 1;
        fillRR(ctx, x + bw * .12, bottom - h, bw * .76, Math.max(1, h), 3, added ? P.alpha('accent', now ? .95 : .55) : 'transparent', added ? null : P.border);
        if (bw > 17) D.text(ctx, String(sm.lo + j), x + bw / 2, bottom + 11, { color: now ? P.accent : P.faint, size: 10, align: 'center', mono: true });
      });
      D.text(ctx, 'i →', left - 8, bottom + 11, { color: P.faint, size: 10, align: 'right' });
    };
    update();
  },
});

/* ============================================================= math-bits == */
defineLab('math-bits', {
  title: 'Eight bits: binary, hex and two’s complement',
  hint: 'Click any bit to flip it. Then use the buttons: add one to 127 or 255, negate a number, shift left and right. Switch between reading the same bits as unsigned or signed.',
  mount(L) {
    const s = { v: 0b01001001, signed: false, msg: null };
    const c = L.canvas(w => w < 520 ? 270 : 240);
    const sgn = v => v >= 128 ? v - 256 : v;
    const val = v => s.signed ? sgn(v) : v;
    L.seg('read the same bits as', [['u', 'unsigned 0…255'], ['s', 'signed −128…127']], 'u', v => { s.signed = v === 's'; s.msg = null; update(); });
    const op = (label, f, explain) => L.button(label, () => {
      const before = s.v, exact = f(val(before));
      s.v = ((s.signed ? exact : f(before)) % 256 + 256) % 256;
      s.msg = explain(before, exact);
      update();
    });
    const range = s2 => s2 ? [-128, 127] : [0, 255];
    const wrapped = exact => { const [lo, hi] = range(s.signed); return exact < lo || exact > hi; };
    op('+1', x => x + 1, (b, e) => wrapped(e)
      ? (s.signed ? `<b>Signed overflow.</b> 127 + 1 needs 8 bits of magnitude, so the result lands on the sign bit: 0111 1111 + 1 = 1000 0000, which reads as <b>−128</b>. In C this is undefined behaviour, Java and Go wrap exactly like this, and Python integers never overflow because they grow extra digits.`
        : `<b>Unsigned wrap-around.</b> 1111 1111 + 1 carries out of the 8th bit, and the carry has nowhere to go: the result is <b>0</b>, like a car odometer rolling over. All unsigned arithmetic is arithmetic <b>mod 2⁸ = 256</b>.`)
      : `Adding one flips the lowest 0 to 1 and every 1 below it to 0 — the carry ripples, exactly like 0199 + 1 = 0200 in decimal.`);
    op('−1', x => x - 1, (b, e) => wrapped(e)
      ? (s.signed ? `<b>Signed underflow:</b> −128 − 1 wraps to <b>127</b>.` : `<b>Wrap-around:</b> 0 − 1 is 255 (1111 1111) in 8-bit unsigned arithmetic, the same way 0 − 1 ≡ 255 (mod 256). A classic bug: <code>for (unsigned i = n − 1; i &gt;= 0; i--)</code> never ends.`)
      : `Subtracting one borrows through the low zeros.`);
    op('&lt;&lt; 1', x => x * 2, (b, e) => `<b>Shift left = multiply by 2.</b> Every bit moves one place up, so every place value doubles${(b & 128) ? `. The top bit was 1 and <b>fell off the end</b>: the true answer ${e} does not fit in 8 bits` : ''}. <code>x &lt;&lt; k</code> is x·2ᵏ.`);
    op('&gt;&gt; 1', x => Math.floor(x / 2), () => s.signed
      ? `<b>Arithmetic shift right = divide by 2, rounding down.</b> For signed numbers the sign bit is copied into the top so negatives stay negative: −7 &gt;&gt; 1 = −4 (floor, not truncation).`
      : `<b>Shift right = divide by 2, rounding down.</b> The lowest bit falls off; that bit was the remainder. <code>x &gt;&gt; k</code> is ⌊x / 2ᵏ⌋.`);
    op('NOT ~', x => s.signed ? -x - 1 : 255 - x, () => `<b>~x flips every bit.</b> Read as unsigned that is 255 − x; read as signed it is <b>−x − 1</b>. So ~0 = −1 (all ones), and ~x + 1 = −x.`);
    op('negate −x', x => -x, (b, e) => s.signed && b === 128
      ? `<b>−(−128) = −128.</b> The range −128…127 is lopsided, so the most negative number has no positive partner. Negating it overflows back to itself — the reason <code>abs(INT_MIN)</code> is still negative in C and Java.`
      : `<b>Two’s complement negation: flip every bit, then add one.</b> x + (~x + 1) = 1111 1111 + 1 = 1 0000 0000, which is 0 once the 9th bit falls off. That is why one adder circuit does both addition and subtraction.`);
    const setTo = (label, v) => L.button(label, () => { s.v = v; s.msg = null; update(); });
    setTo('127', 127); setTo('255', 255);
    let cells = [];
    onTap(c, (x, y) => {
      const hit = cells.find(r => x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h);
      if (!hit) return;
      s.v ^= 1 << hit.bit;
      s.msg = `Bit ${hit.bit} is worth ${hit.bit === 7 && s.signed ? '<b>−128</b> when read as signed (the sign bit), 128 when unsigned' : `<b>2${'⁰¹²³⁴⁵⁶⁷'[hit.bit]} = ${1 << hit.bit}</b>`}. A number’s value is the sum of the place values of its 1 bits.`;
      update();
    });
    function update() {
      const v = val(s.v), pc = s.v.toString(2).split('').filter(b => b === '1').length;
      L.stats([['binary', s.v.toString(2).padStart(8, '0').replace(/(....)(....)/, '$1 $2')], ['hex', `0x${s.v.toString(16).toUpperCase().padStart(2, '0')}`, 'accent'],
        ['unsigned', s.v], ['signed', sgn(s.v)], ['bits set', pc], ['power of two?', s.v && !(s.v & (s.v - 1)) ? 'yes: x & (x−1) = 0' : 'no']]);
      L.insight(s.msg || `Binary is base 2: the places are worth 1, 2, 4, 8, … instead of 1, 10, 100. Hex groups bits in fours (one hex digit = one nibble), which is why programmers read bytes as two hex digits. In signed mode the top bit is worth <b>−128</b> instead of +128 — that single change is all two’s complement is.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, cw = Math.min(58, (c.w - 32) / 8), x0 = (c.w - cw * 8) / 2, y0 = 34;
      cells = [];
      for (let i = 0; i < 8; i++) {
        const bit = 7 - i, on = (s.v >> bit) & 1, x = x0 + i * cw;
        const pv = bit === 7 && s.signed ? -128 : 1 << bit;
        D.text(ctx, String(pv), x + cw / 2, y0 - 10, { color: pv < 0 ? P.err : P.dim, size: 11, align: 'center', mono: true, weight: 650 });
        fillRR(ctx, x + 3, y0, cw - 6, cw - 6, 8, on ? P.alpha('accent', .85) : P.surface2, on ? P.accent : P.border, 1.4);
        D.text(ctx, String(on), x + cw / 2, y0 + (cw - 6) / 2, { color: on ? P.bg : P.faint, size: cw * .42, align: 'center', mono: true, weight: 700 });
        cells.push({ x: x + 3, y: y0, w: cw - 6, h: cw - 6, bit });
        if (on) D.text(ctx, (pv > 0 ? '+' : '') + pv, x + cw / 2, y0 + cw + 6, { color: pv < 0 ? P.err : P.accent, size: 10.5, align: 'center', mono: true });
      }
      // nibble brackets and hex digits
      const yb = y0 + cw + 24;
      [0, 1].forEach(g => {
        const xa = x0 + g * 4 * cw + 6, xb = xa + 4 * cw - 12;
        D.line(ctx, xa, yb, xb, yb, P.strong, 1.2); D.line(ctx, xa, yb - 5, xa, yb, P.strong, 1.2); D.line(ctx, xb, yb - 5, xb, yb, P.strong, 1.2);
        const nib = (s.v >> (4 - g * 4)) & 15;
        D.text(ctx, `${nib.toString(16).toUpperCase()} (hex) = ${nib}`, (xa + xb) / 2, yb + 13, { color: P.dim, size: 11, align: 'center', mono: true });
      });
      // number line with the value marked and the wrap point
      const [lo, hi] = range(s.signed), ly = c.h - 34, la = 26, lb = c.w - 26;
      const X = v => la + (lb - la) * (v - lo) / (hi - lo);
      D.line(ctx, la, ly, lb, ly, P.strong, 2);
      [lo, s.signed ? 0 : 128, hi].forEach(t => { D.line(ctx, X(t), ly - 5, X(t), ly + 5, P.strong, 1.2); D.text(ctx, String(t), X(t), ly + 16, { color: P.faint, size: 10, align: 'center', mono: true }); });
      const vv = val(s.v);
      D.dot(ctx, X(vv), ly, 7, P.accent, P.bg, 2);
      D.text(ctx, String(vv), X(vv), ly - 16, { color: P.accent, size: 12, align: 'center', mono: true, weight: 700 });
      ctx.save(); ctx.setLineDash([3, 4]);
      ctx.strokeStyle = P.alpha('err', .7); ctx.lineWidth = 1.3; ctx.beginPath();
      ctx.moveTo(lb, ly - 8); ctx.bezierCurveTo(lb, ly - 44, la, ly - 44, la, ly - 8); ctx.stroke(); ctx.restore();
      D.text(ctx, `past ${hi} you wrap to ${lo}`, c.w / 2, ly - 40, { color: P.alpha('err', .85), size: 10.5, align: 'center' });
    };
    update();
  },
});

/* ============================================================ math-float == */
defineLab('math-float', {
  title: 'Inside a 32-bit float (IEEE 754)',
  hint: 'Type a number or press a preset. Every bit is clickable. <b>Stored exactly</b> is the value the hardware really keeps — usually not quite what you typed.',
  mount(L) {
    const dv = new DataView(new ArrayBuffer(4));
    const s = { bits: 0, typed: '0.1' };
    L.stage.innerHTML = `<div class="mf">
      <label class="mf-in"><span>number</span><input type="text" inputmode="decimal" spellcheck="false" value="0.1"></label>
      <div class="mf-bits" role="group" aria-label="32 bits"></div>
      <div class="mf-legend"><span class="s">sign · 1 bit</span><span class="e">exponent · 8 bits</span><span class="m">fraction (mantissa) · 23 bits</span></div>
      <div class="mf-eq"></div>
    </div>`;
    const input = L.stage.querySelector('input'), bitsEl = L.stage.querySelector('.mf-bits'), eq = L.stage.querySelector('.mf-eq');
    for (let i = 31; i >= 0; i--) {
      const b = document.createElement('button');
      b.type = 'button'; b.dataset.i = i;
      b.className = i === 31 ? 's' : i >= 23 ? 'e' : 'm';
      bitsEl.append(b);
    }
    bitsEl.addEventListener('click', e => {
      const b = e.target.closest('button'); if (!b) return;
      s.bits = (s.bits ^ (1 << +b.dataset.i)) >>> 0; s.typed = null; input.value = String(asFloat()); update();
    });
    const fromNum = x => { dv.setFloat32(0, x); s.bits = dv.getUint32(0); };
    const asFloat = () => { dv.setUint32(0, s.bits); return dv.getFloat32(0); };
    input.addEventListener('input', () => { const t = input.value.trim(); const x = Number(t); if (t && !Number.isNaN(x)) { s.typed = t; fromNum(x); update(); } });
    const preset = (label, t) => L.button(label, () => { s.typed = t; input.value = t; fromNum(Number(t)); update(); });
    preset('0.1', '0.1'); preset('1/3', String(1 / 3)); preset('16777217', '16777217'); preset('3.4e38', '3.4e38'); preset('1e-45', '1e-45');
    L.button('next float ↑', () => { if ((s.bits & 0x7f800000) >>> 0 !== 0x7f800000) { s.bits = (s.bits + (s.bits >>> 31 ? -1 : 1)) >>> 0; s.typed = null; input.value = String(asFloat()); update(); } });
    /* the exact decimal expansion of a float32 bit pattern (every binary fraction terminates in decimal) */
    function exact(bits) {
      const sign = bits >>> 31 ? '−' : '', E = (bits >>> 23) & 255, F = bits & 0x7fffff;
      if (E === 255) return F ? 'NaN' : `${sign}∞`;
      let M = BigInt(E ? F + 0x800000 : F), k = E ? E - 150 : -149;
      if (M === 0n) return `${sign}0`;
      while (M % 2n === 0n && k < 0) { M /= 2n; k++; }
      if (k >= 0) return sign + (M << BigInt(k)).toString();
      const digits = (M * 5n ** BigInt(-k)).toString().padStart(-k + 1, '0');
      return `${sign}${digits.slice(0, digits.length + k)}.${digits.slice(digits.length + k)}`;
    }
    const sup = n => String(n).replace(/[0-9-]/g, ch => '⁰¹²³⁴⁵⁶⁷⁸⁹⁻'['0123456789-'.indexOf(ch)]);
    function update() {
      [...bitsEl.children].forEach(b => { const on = (s.bits >>> +b.dataset.i) & 1; b.textContent = on; b.classList.toggle('on', !!on); });
      const E = (s.bits >>> 23) & 255, F = s.bits & 0x7fffff, sign = s.bits >>> 31, v = asFloat();
      const kind = E === 255 ? (F ? 'NaN' : 'infinity') : E === 0 ? (F ? 'subnormal' : 'zero') : 'normal';
      eq.innerHTML = kind === 'normal'
        ? `<span>(−1)<sup>${sign}</sup> × <b>${(1 + F / 2 ** 23).toFixed(7)}</b> × 2<sup>${E} − 127</sup></span><span>= ${sign ? '−' : ''}${(1 + F / 2 ** 23).toFixed(7)} × 2${sup(E - 127)} ≈ ${v.toPrecision(8)}</span>`
        : kind === 'subnormal' ? `<span>exponent field 0 → subnormal: (−1)<sup>${sign}</sup> × <b>0.fraction</b> × 2<sup>−126</sup> — no hidden 1, precision fades out</span>`
          : kind === 'zero' ? `<span>all exponent and fraction bits 0 → ${sign ? '−0 (negative zero: equal to 0, but 1/−0 = −∞)' : '+0'}</span>`
            : `<span>exponent field all ones → ${kind === 'NaN' ? 'NaN (not a number): NaN ≠ NaN' : `${sign ? '−' : '+'}∞`}</span>`;
      const ex = exact(s.bits);
      dv.setUint32(0, (s.bits + 1) >>> 0); const nxt = dv.getFloat32(0);
      const gap = kind === 'normal' || kind === 'subnormal' ? Math.abs(nxt - v) : NaN;
      const typedNum = s.typed != null ? Number(s.typed) : NaN;
      const err = s.typed != null && Number.isFinite(v) && Number.isFinite(typedNum) ? v - typedNum : NaN;
      L.stats([['kind', kind], ['exponent', kind === 'normal' ? `${E} − 127 = ${E - 127}` : E], ['stored exactly', ex.length > 44 ? `${ex.slice(0, 44)}…` : ex, 'accent'],
        Number.isFinite(err) ? ['error vs typed', err === 0 ? '0 (exact)' : err.toExponential(2), err === 0 ? 'ok' : 'err'] : null,
        Number.isFinite(gap) ? ['gap to next float', gap.toExponential(2)] : null]);
      const tip = s.typed === '0.1' ? `0.1 is <b>not</b> stored exactly. One tenth in binary is 0.000110011001100… repeating forever (just as 1/3 = 0.333… in decimal), so it is cut off after 24 significant bits. That is why <code>0.1 + 0.2 != 0.3</code> and why money is kept in integer cents or decimals.`
        : s.typed === '16777217' ? `2²⁴ + 1 = 16 777 217 is the first integer a float32 cannot hold: with 24 significant bits, the gap between neighbouring floats here is 2. It is stored as 16 777 216. (float64 has 53 bits, so its first missing integer is 2⁵³ + 1 — the reason JavaScript's <code>Number.MAX_SAFE_INTEGER</code> is 2⁵³ − 1.)`
          : kind === 'subnormal' ? `Subnormal numbers fill the gap between 0 and the smallest normal float (about 1.2 × 10⁻³⁸), trading precision for range; 1e-45 is the smallest positive float32, a single 1 in the lowest bit.`
            : kind === 'infinity' || kind === 'NaN' ? `The all-ones exponent is reserved for ∞ and NaN, so overflow and 0/0 have a defined answer instead of crashing.`
              : `A float is scientific notation in base 2: a sign, an exponent that picks the scale, and 23 fraction bits (plus a hidden leading 1) of precision — about 7 decimal digits. The gap between neighbours grows with the number: floats are dense near 0 and sparse far out.`;
      L.insight(tip);
    }
    fromNum(0.1); update();
  },
});

/* ============================================================ math-truth == */
defineLab('math-truth', {
  title: 'Truth tables: are these two statements the same?',
  hint: 'Pick two statements. Two statements are <b>logically equivalent</b> when their columns agree on every row — then one can always replace the other, in a proof or in an <code>if</code>.',
  mount(L) {
    const E = [
      ['p ∧ q', (p, q) => p && q, 'p and q'],
      ['p ∨ q', (p, q) => p || q, 'p or q'],
      ['p → q', (p, q) => !p || q, '(not p) or q'],
      ['¬p ∨ q', (p, q) => !p || q, '(not p) or q'],
      ['q → p', (p, q) => !q || p, '(not q) or p'],
      ['¬q → ¬p', (p, q) => q || !p, 'q or (not p)'],
      ['¬(p ∧ q)', (p, q) => !(p && q), 'not (p and q)'],
      ['¬p ∨ ¬q', (p, q) => !p || !q, '(not p) or (not q)'],
      ['¬(p ∨ q)', (p, q) => !(p || q), 'not (p or q)'],
      ['¬p ∧ ¬q', (p, q) => !p && !q, '(not p) and (not q)'],
      ['p ↔ q', (p, q) => p === q, 'p == q'],
      ['(p → q) ∧ (q → p)', (p, q) => (!p || q) && (!q || p), '((not p) or q) and ((not q) or p)'],
      ['p ⊕ q', (p, q) => p !== q, 'p != q   # xor, p ^ q'],
      ['p ∨ ¬p', p => p || !p, 'p or (not p)'],
    ];
    const LAWS = {
      'p → q|¬p ∨ q': 'An implication is an OR in disguise: <b>p → q ≡ ¬p ∨ q</b>. “If it rains I take an umbrella” is only broken on a rainy day without an umbrella.',
      'p → q|¬q → ¬p': 'The <b>contrapositive</b>: p → q ≡ ¬q → ¬p. Proving “if not q then not p” proves the original — a standard proof technique.',
      'p → q|q → p': 'The <b>converse</b> is <b>not</b> equivalent. “If it is a square, it is a rectangle” is true; “if it is a rectangle, it is a square” is not. Confusing the two is the most common logic mistake in proofs and in code reviews.',
      '¬(p ∧ q)|¬p ∨ ¬q': '<b>De Morgan’s law:</b> not (A and B) = (not A) or (not B). Push a NOT inside and the AND flips to OR — handy for simplifying <code>if not (x &gt; 0 and y &gt; 0)</code>.',
      '¬(p ∨ q)|¬p ∧ ¬q': '<b>De Morgan’s other law:</b> not (A or B) = (not A) and (not B). “Neither p nor q.”',
      'p ↔ q|(p → q) ∧ (q → p)': '<b>“If and only if”</b> is implication both ways. To prove p ↔ q you prove both directions.',
      'p ⊕ q|p ↔ q': 'XOR is exactly the negation of ↔: they disagree on every row. XOR is “different”, ↔ is “same”.',
    };
    const opts = E.map(([t], i) => `<option value="${i}">${t}</option>`).join('');
    L.stage.innerHTML = `<div class="mt">
      <div class="mt-pick"><label>A <select data-s="a">${opts}</select></label><label>B <select data-s="b">${opts}</select></label></div>
      <div class="table-wrap"><table class="mt-table"><thead></thead><tbody></tbody></table></div>
      <p class="mt-code"></p></div>`;
    const selA = L.stage.querySelector('[data-s=a]'), selB = L.stage.querySelector('[data-s=b]');
    selA.value = 2; selB.value = 3;
    selA.onchange = selB.onchange = update;
    const pair = (a, b) => L.button(`${E[a][0]} vs ${E[b][0]}`, () => { selA.value = a; selB.value = b; update(); });
    pair(2, 4); pair(2, 5); pair(6, 7);
    const rows = [[true, true], [true, false], [false, true], [false, false]];
    const T = v => `<span class="${v ? 'tv' : 'fv'}">${v ? 'T' : 'F'}</span>`;
    function update() {
      const a = E[+selA.value], b = E[+selB.value];
      L.stage.querySelector('thead').innerHTML = `<tr><th>p</th><th>q</th><th>A: ${a[0]}</th><th>B: ${b[0]}</th><th>same?</th></tr>`;
      let agree = 0;
      L.stage.querySelector('tbody').innerHTML = rows.map(([p, q]) => {
        const x = a[1](p, q), y = b[1](p, q);
        if (x === y) agree++;
        return `<tr class="${x === y ? '' : 'diff'}"><td>${T(p)}</td><td>${T(q)}</td><td>${T(x)}</td><td>${T(y)}</td><td>${x === y ? '✓' : '✗'}</td></tr>`;
      }).join('');
      L.stage.querySelector('.mt-code').innerHTML = `In Python: <code>A = ${a[2]}</code> · <code>B = ${b[2]}</code>`;
      const eqv = agree === 4;
      L.stats([['rows that agree', `${agree} / 4`, eqv ? 'ok' : 'err'], ['verdict', eqv ? 'equivalent' : 'not equivalent', eqv ? 'ok' : 'err']]);
      const key = [a[0], b[0]].join('|'), rev = [b[0], a[0]].join('|');
      const law = a[0] === b[0] ? 'A statement is always equivalent to itself.' : LAWS[key] || LAWS[rev];
      L.insight(law || (eqv ? 'These agree on every row, so they are equivalent: either can replace the other anywhere.'
        : `They disagree on the highlighted row${4 - agree > 1 ? 's' : ''}. One counterexample row is enough to show two statements are <b>not</b> equivalent.`));
    }
    update();
  },
});

/* ======================================================== math-induction == */
defineLab('math-induction', {
  title: 'Proof by induction: the domino picture',
  hint: 'Induction needs two things: the <b>first domino falls</b> (base case) and <b>each domino knocks over the next</b> (inductive step). Break either one and press <b>Push</b>.',
  mount(L) {
    const N = 14;
    const s = { base: true, step: true, gapAt: 6, angle: Array(N).fill(0), t: 0, running: false, fallen: 0 };
    const c = L.canvas(w => w < 520 ? 230 : 210);
    const base = L.toggle('base case: P(1) holds', true, v => { s.base = v; reset(); });
    L.seg('inductive step P(k) ⇒ P(k+1)', [['all', 'holds for every k'], ['gap', 'fails at one k']], 'all', v => { s.step = v === 'all'; reset(); });
    L.slider('where the step fails (k)', { min: 1, max: N - 1, value: s.gapAt }, v => { s.gapAt = v; reset(); });
    const anim = L.loop(dt => {
      s.t += dt * 7;
      let moving = false;
      for (let i = 0; i < N; i++) {
        const canFall = s.base && (s.step || i < s.gapAt);
        if (!canFall || s.t < i) continue;
        const target = Math.PI / 2 * .8;
        if (s.angle[i] < target) { s.angle[i] = Math.min(target, s.angle[i] + dt * 5); moving = true; }
      }
      s.fallen = s.angle.filter(a => a > .5).length;
      update(false);
      if (!moving && s.t > N + 1) return false;
    });
    L.playButton(anim, ['Push the first domino', 'Pause'], () => { reset(false); });
    L.button('Reset', () => { anim.stop(); reset(); });
    base.set(true, true);
    function reset(redraw = true) { s.angle.fill(0); s.t = 0; s.fallen = 0; if (redraw) update(); }
    function update(full = true) {
      const k = Math.max(1, s.fallen);
      L.stats([['dominoes fallen', `${s.fallen} / ${N}`, s.fallen === N ? 'ok' : s.fallen ? 'accent' : ''],
        ['example claim P(n)', '1 + 2 + … + n = n(n+1)/2'],
        s.fallen ? [`P(${k})`, `${k * (k + 1) / 2} = ${k}·${k + 1}/2 ✓`, 'ok'] : null]);
      if (full) L.insight(!s.base
        ? `<b>No base case, no proof.</b> Every domino would knock over the next one, but nobody pushes the first. A step that holds for every k proves nothing on its own: “if n is odd then n + 2 is odd” holds for all n, yet does not make every n odd.`
        : !s.step ? `<b>The step fails at k = ${s.gapAt}</b>, so the chain stops after domino ${s.gapAt}. Checking the first ${s.gapAt} cases by hand is evidence, not proof. (Famous example: n² + n + 41 is prime for n = 0…39 and fails at n = 40.)`
          : `<b>Both parts hold, so every domino falls</b> — for 14 dominoes or 14 billion. Proving P(1) and “P(k) ⇒ P(k+1)” proves P(n) for every n ≥ 1. A loop invariant is the same argument for code: true before the first iteration, preserved by each iteration, so true when the loop ends.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, floor = c.h - 50, gap = (c.w - 40) / N, h = Math.min(90, gap * 2.3), w = Math.max(6, gap * .22);
      D.line(ctx, 10, floor, c.w - 10, floor, P.strong, 2);
      for (let i = 0; i < N; i++) {
        const x = 26 + i * gap, a = s.angle[i];
        ctx.save(); ctx.translate(x + w, floor); ctx.rotate(a);
        const col = !s.base && i === 0 ? P.err : a > .5 ? P.accent : P.dim;
        fillRR(ctx, -w, -h, w, h, 2, P.alpha(col === P.dim ? 'dim' : col === P.err ? 'err' : 'accent', .35), col, 1.5);
        ctx.restore();
        D.text(ctx, String(i + 1), x + w / 2, floor + 14, { color: P.faint, size: 10, align: 'center', mono: true });
        if (!s.step && i === s.gapAt - 1) {
          D.text(ctx, '✗', x + gap / 2 + w, floor - h - 12, { color: P.err, size: 16, align: 'center', weight: 700 });
          ctx.save(); ctx.setLineDash([3, 3]); D.line(ctx, x + gap / 2 + w, floor - h, x + gap / 2 + w, floor, P.alpha('err', .6), 1.2); ctx.restore();
        }
      }
      D.text(ctx, 'n →', 10, floor + 30, { color: P.faint, size: 10 });
      D.text(ctx, s.base ? 'base case: push domino 1' : 'base case missing: domino 1 is never pushed', 26, 16, { color: s.base ? P.dim : P.err, size: 11, weight: 600 });
    };
    update();
  },
});

/* ============================================================= math-venn == */
defineLab('math-venn', {
  title: 'Set operations on a Venn diagram',
  hint: 'The universe U is 1…20. <b>A</b> = multiples of 2, <b>B</b> = multiples of 3. Pick an operation: the shaded region is the result, and the same operation is shown in Python, SQL and as a bitmask.',
  mount(L) {
    const U = Array.from({ length: 20 }, (_, i) => i + 1);
    const inA = x => x % 2 === 0, inB = x => x % 3 === 0;
    const OPS = {
      union: ['A ∪ B', (a, b) => a || b, 'a | b', 'UNION', 'maskA | maskB'],
      inter: ['A ∩ B', (a, b) => a && b, 'a & b', 'INTERSECT', 'maskA & maskB'],
      diff: ['A − B', (a, b) => a && !b, 'a - b', 'EXCEPT', 'maskA & ~maskB'],
      rdiff: ['B − A', (a, b) => b && !a, 'b - a', 'EXCEPT', 'maskB & ~maskA'],
      sym: ['A △ B', (a, b) => a !== b, 'a ^ b', '(… EXCEPT …) UNION (… EXCEPT …)', 'maskA ^ maskB'],
      comp: ['Aᶜ', a => !a, 'U - a', 'NOT IN', '~maskA & ALL'],
      nor: ['(A ∪ B)ᶜ', (a, b) => !(a || b), 'U - (a | b)', 'NOT IN (… UNION …)', '~(maskA | maskB) & ALL'],
      dm: ['Aᶜ ∩ Bᶜ', (a, b) => !a && !b, '(U - a) & (U - b)', '', '~maskA & ~maskB & ALL'],
    };
    const s = { op: 'union' };
    const c = L.canvas(w => Math.min(320, Math.max(250, w * .5)));
    L.seg('operation', Object.entries(OPS).map(([k, v]) => [k, v[0]]), s.op, v => { s.op = v; update(); });
    const res = () => U.filter(x => OPS[s.op][1](inA(x), inB(x)));
    function update() {
      const r = res(), A = U.filter(inA), B = U.filter(inB), AB = U.filter(x => inA(x) && inB(x));
      L.stats([['result', `{${r.join(', ')}}`, 'accent'], ['|result|', r.length], ['|A| + |B| − |A∩B|', `${A.length} + ${B.length} − ${AB.length} = ${A.length + B.length - AB.length} = |A∪B|`]]);
      const o = OPS[s.op];
      L.insight(`${s.op === 'nor' || s.op === 'dm' ? '<b>De Morgan:</b> (A ∪ B)ᶜ and Aᶜ ∩ Bᶜ shade exactly the same region — “not in either” = “not in A and not in B”. ' : ''}`
        + `Python sets: <code>${o[2]}</code>${o[3] ? ` · SQL: <code>${o[3]}</code>` : ''} · bitmask: <code>${o[4]}</code>. `
        + (s.op === 'union' ? 'Counting a union needs <b>inclusion–exclusion</b>: adding |A| and |B| counts 6, 12 and 18 twice, so subtract |A ∩ B| once.'
          : s.op === 'sym' ? 'Symmetric difference is “in exactly one” — XOR on membership, which is why it is the <code>^</code> operator on sets and bits alike.'
            : s.op === 'inter' ? 'Intersection = logical AND on membership: the multiples of 6.'
              : s.op === 'comp' ? 'A complement is only defined relative to a universe U — here 1…20. Without a universe, “everything that is not even” has no answer.'
                : 'Set difference keeps what is in the first set and not the second — not symmetric: A − B ≠ B − A.'));
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, W = c.w, H = c.h, r = Math.min(H * .36, W * .21);
      const ca = { x: W / 2 - r * .55, y: H / 2 + 6 }, cb = { x: W / 2 + r * .55, y: H / 2 + 6 };
      const box = { x: 10, y: 22, w: W - 20, h: H - 32 };
      const circle = (p, rr = r) => { const path = new Path2D(); path.arc(p.x, p.y, rr, 0, TAU); return path; };
      const outside = p => { const path = new Path2D(); path.rect(box.x, box.y, box.w, box.h); path.arc(p.x, p.y, r, 0, TAU); return path; };
      const f = OPS[s.op][1];
      const regions = [[true, true], [true, false], [false, true], [false, false]];
      regions.forEach(([a, b]) => {
        if (!f(a, b)) return;
        ctx.save();
        const clipA = a ? circle(ca) : outside(ca), clipB = b ? circle(cb) : outside(cb);
        ctx.clip(clipA, 'evenodd'); ctx.clip(clipB, 'evenodd');
        ctx.fillStyle = P.alpha('accent', .32); ctx.fillRect(box.x, box.y, box.w, box.h);
        ctx.restore();
      });
      fillRR(ctx, box.x, box.y, box.w, box.h, 10, null, P.border);
      D.text(ctx, 'U = {1 … 20}', box.x + 8, 12, { color: P.faint, size: 10.5 });
      [[ca, 'A (even)'], [cb, 'B (multiple of 3)']].forEach(([p, l], i) => {
        ctx.strokeStyle = P.series[i]; ctx.lineWidth = 2; ctx.stroke(circle(p));
        D.text(ctx, l, p.x + (i ? r * .3 : -r * .3), p.y - r - 8, { color: P.series[i], size: 11.5, align: 'center', weight: 700 });
      });
      // place elements inside their region
      const groups = { ab: [], a: [], b: [], n: [] };
      U.forEach(x => groups[inA(x) && inB(x) ? 'ab' : inA(x) ? 'a' : inB(x) ? 'b' : 'n'].push(x));
      const place = (list, cx, cy, cols, dx = 24, dy = 22) => list.map((x, i) => [x, cx + ((i % cols) - (cols - 1) / 2) * dx, cy + (Math.floor(i / cols) - (Math.ceil(list.length / cols) - 1) / 2) * dy]);
      const pts = [
        ...place(groups.ab, W / 2, ca.y, 1),
        ...place(groups.a, ca.x - r * .45, ca.y, 2, Math.min(24, r * .35)),
        ...place(groups.b, cb.x + r * .45, cb.y, 1),
      ];
      const nOut = groups.n, leftN = nOut.slice(0, 4), rightN = nOut.slice(4);
      pts.push(...leftN.map((x, i) => [x, box.x + 18, box.y + 22 + i * ((box.h - 30) / 4)]));
      pts.push(...rightN.map((x, i) => [x, box.x + box.w - 18, box.y + 22 + i * ((box.h - 30) / 4)]));
      pts.forEach(([x, px, py]) => {
        const on = f(inA(x), inB(x));
        D.dot(ctx, px, py, 10, on ? P.accent : P.surface2, on ? null : P.border, 1);
        D.text(ctx, String(x), px, py, { color: on ? P.bg : P.dim, size: 10.5, align: 'center', mono: true, weight: 700 });
      });
    };
    update();
  },
});

/* ========================================================= math-function == */
defineLab('math-function', {
  title: 'Functions as arrows: injective, surjective, bijective',
  hint: 'Each input on the left sends exactly one arrow to the right. <b>Click an input</b> to move its arrow to the next output. Change the size of the codomain and watch what becomes possible.',
  mount(L) {
    const X = ['a', 'b', 'c', 'd'];
    const s = { ny: 4, map: [0, 1, 2, 3] };
    const c = L.canvas(w => w < 520 ? 280 : 250);
    L.seg('outputs |Y|', [[3, '3'], [4, '4'], [5, '5']], s.ny, v => { s.ny = v; s.map = s.map.map(t => t % v); update(); });
    L.button('make it a bijection', () => { if (s.ny !== 4) return; s.map = [2, 0, 3, 1]; update(); });
    L.button('collide two inputs', () => { s.map = [0, 0, 1, 2 % s.ny]; update(); });
    let hits = [];
    onTap(c, (x, y) => { const h = hits.find(p => Math.hypot(p.x - x, p.y - y) < 22); if (h) { s.map[h.i] = (s.map[h.i] + 1) % s.ny; update(); } });
    const props = () => {
      const img = new Set(s.map), inj = img.size === X.length, sur = img.size === s.ny;
      return { img, inj, sur, bij: inj && sur };
    };
    function update() {
      const { img, inj, sur, bij } = props();
      const coll = [];
      for (let j = 0; j < s.ny; j++) { const pre = X.filter((_, i) => s.map[i] === j); if (pre.length > 1) coll.push(`${pre.join(', ')} → ${j + 1}`); }
      L.stats([['injective (one-to-one)', inj ? 'yes' : 'no', inj ? 'ok' : 'err'], ['surjective (onto)', sur ? 'yes' : 'no', sur ? 'ok' : 'err'],
        ['bijective', bij ? 'yes → invertible' : 'no', bij ? 'ok' : ''], ['image', `{${[...img].map(j => j + 1).sort().join(', ')}}`]]);
      L.insight(s.ny < X.length
        ? `<b>Pigeonhole:</b> 4 inputs and only ${s.ny} outputs, so some output must receive two arrows — no function from X to Y can be injective. Any hash function from a big key space to a small table <b>must</b> have collisions; good hashing only makes them rare and spread out.${coll.length ? ` Collisions now: ${coll.join('; ')}.` : ''}`
        : s.ny > X.length ? `4 inputs cannot cover 5 outputs, so no function from X to Y can be <b>surjective</b> — some output is always left without an arrow. It can still be injective (no collisions).`
          : bij ? `<b>A bijection</b> pairs every input with exactly one output and vice versa, so you can reverse every arrow and get the inverse function. Encoding and decoding, encryption and decryption, and permutations are all bijections.`
            : `With |X| = |Y| = 4, injective and surjective come together: if there is no collision, every output must be hit. Collisions now: ${coll.join('; ') || 'none'}.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, lx = c.w * .22, rx = c.w * .78, top = 44, bottom = c.h - 22;
      const yX = i => top + (bottom - top) * (i + .5) / X.length, yY = j => top + (bottom - top) * (j + .5) / s.ny;
      fillRR(ctx, lx - 38, top - 8, 76, bottom - top + 16, 38, P.alpha('dim', .06), P.border);
      fillRR(ctx, rx - 38, top - 8, 76, bottom - top + 16, 38, P.alpha('dim', .06), P.border);
      D.text(ctx, 'X (domain)', lx, 16, { color: P.dim, size: 11.5, align: 'center', weight: 650 });
      D.text(ctx, 'Y (codomain)', rx, 16, { color: P.dim, size: 11.5, align: 'center', weight: 650 });
      const { img } = props(), load = Array(s.ny).fill(0);
      s.map.forEach(j => load[j]++);
      s.map.forEach((j, i) => D.arrow(ctx, lx + 16, yX(i), rx - 18, yY(j), load[j] > 1 ? P.err : P.accent, 2, 9));
      hits = X.map((name, i) => { D.dot(ctx, lx, yX(i), 14, P.surface, P.accent, 2); D.text(ctx, name, lx, yX(i), { color: P.text, size: 13, align: 'center', weight: 700, mono: true }); return { x: lx, y: yX(i), i }; });
      for (let j = 0; j < s.ny; j++) {
        const hit = img.has(j);
        D.dot(ctx, rx, yY(j), 14, P.surface, hit ? (load[j] > 1 ? P.err : P.ok) : P.border, 2);
        D.text(ctx, String(j + 1), rx, yY(j), { color: hit ? P.text : P.faint, size: 13, align: 'center', weight: 700, mono: true });
        if (!hit) D.text(ctx, 'no arrow', rx + 22, yY(j), { color: P.faint, size: 10 });
      }
    };
    update();
  },
});

/* =========================================================== math-pascal == */
defineLab('math-pascal', {
  title: 'Pascal’s triangle: C(n, k) and where it comes from',
  hint: '<b>Click any cell.</b> It is the sum of the two cells above it, and it counts the ways to choose k things from n. Try the colourings to see hidden patterns.',
  mount(L) {
    const s = { n: 5, k: 2, view: 'plain' };
    const c = L.canvas(w => w < 520 ? 300 : 340);
    L.seg('colour by', [['plain', 'the choice'], ['parity', 'odd / even'], ['rows', 'row sums']], s.view, v => { s.view = v; update(); });
    let cells = [];
    onTap(c, (x, y) => { const h = cells.find(p => Math.abs(p.x - x) < p.r && Math.abs(p.y - y) < p.r); if (h) { s.n = h.n; s.k = h.k; update(); } });
    const rowsN = () => c.w < 520 ? 10 : 13;
    function update() {
      const v = binom(s.n, s.k);
      L.stats([['C(n, k)', `C(${s.n}, ${s.k}) = ${v}`, 'accent'], ['formula', `${s.n}! / (${s.k}! · ${s.n - s.k}!)`],
        s.n > 0 && s.k > 0 && s.k < s.n ? ['from above', `${binom(s.n - 1, s.k - 1)} + ${binom(s.n - 1, s.k)} = ${v}`] : ['edge of the triangle', 'always 1'],
        ['row sum', `2${String(s.n).replace(/\d/g, d => '⁰¹²³⁴⁵⁶⁷⁸⁹'[d])} = ${2 ** s.n}`]]);
      L.insight(s.view === 'parity'
        ? `Colour the odd entries and <b>Sierpiński’s triangle</b> appears. Lucas’s theorem explains it: C(n, k) is odd exactly when every 1 bit of k is also a 1 bit of n, i.e. <code>(k &amp; n) == k</code>.`
        : s.view === 'rows' ? `Every row adds up to a power of two: row n sums to <b>2ⁿ</b>, because choosing 0 items, or 1, or 2 … or n of n items covers every subset exactly once, and n items have 2ⁿ subsets (each item is in or out).`
          : `<b>Why the sum rule works:</b> to choose ${s.k} of ${s.n} items, look at the last item. Either you take it and choose ${Math.max(0, s.k - 1)} more from the other ${Math.max(0, s.n - 1)}, or you skip it and choose all ${s.k} from the other ${Math.max(0, s.n - 1)}. Those two cases never overlap, so their counts add. That sentence is also the DP recurrence <code>C[n][k] = C[n-1][k-1] + C[n-1][k]</code>.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, R = rowsN(), dy = (c.h - 20) / R, dx = Math.min(c.w / (R + 1), dy * 1.25), r = Math.min(dx, dy) * .46;
      cells = [];
      for (let n = 0; n < R; n++) {
        for (let k = 0; k <= n; k++) {
          const x = c.w / 2 + (k - n / 2) * dx, y = 16 + n * dy + r;
          const v = binom(n, k), sel = n === s.n && k === s.k, parent = s.view === 'plain' && n === s.n - 1 && (k === s.k || k === s.k - 1);
          let fill = P.surface2, stroke = P.border, tc = P.dim;
          if (s.view === 'parity' && v % 2) { fill = P.alpha('accent', .7); stroke = P.accent; tc = P.bg; }
          if (s.view === 'rows' && n === s.n) { fill = P.alpha('accent', .35); stroke = P.accent; tc = P.text; }
          if (parent) { fill = P.alpha('ok', .3); stroke = P.ok; tc = P.text; }
          if (sel) { fill = P.accent; stroke = P.accent; tc = P.bg; }
          D.dot(ctx, x, y, r, fill, stroke, 1.3);
          const txt = String(v);
          D.text(ctx, txt, x, y, { color: tc, size: Math.min(12, r * (txt.length > 3 ? .62 : txt.length > 2 ? .8 : 1)), align: 'center', mono: true, weight: 650 });
          cells.push({ x, y, r, n, k });
        }
        if (s.view === 'rows') D.text(ctx, `= ${2 ** n}`, c.w / 2 + (n / 2 + .5) * dx + 6, 16 + n * dy + r, { color: n === s.n ? P.accent : P.faint, size: 10, mono: true });
      }
      if (s.view === 'plain' && s.n > 0 && s.k > 0 && s.k < s.n) {
        const x = c.w / 2 + (s.k - s.n / 2) * dx, y = 16 + s.n * dy + r;
        D.arrow(ctx, x - dx / 2, y - dy + r, x - r * .5, y - r * .8, P.ok, 1.6, 7);
        D.arrow(ctx, x + dx / 2, y - dy + r, x + r * .5, y - r * .8, P.ok, 1.6, 7);
      }
    };
    update();
  },
});

/* ============================================================ math-paths == */
defineLab('math-paths', {
  title: 'Counting grid paths: a formula, then dynamic programming',
  hint: 'How many ways from the top-left to the bottom-right corner, moving only <b>right</b> or <b>down</b>? Each cell shows the number of ways to reach it. <b>Click cells to block them</b> — the formula breaks, the DP does not.',
  mount(L) {
    const s = { R: 4, C: 6, blocked: new Set(), shown: 0, acc: 0 };
    const c = L.canvas(w => w < 520 ? 250 : 290);
    L.slider('rows', { min: 2, max: 7, value: s.R }, v => { s.R = v; s.blocked.clear(); s.shown = 0; update(); });
    L.slider('columns', { min: 2, max: 9, value: s.C }, v => { s.C = v; s.blocked.clear(); s.shown = 0; update(); });
    const run = L.loop(dt => { s.acc += dt; if (s.acc > .09) { s.acc = 0; s.shown++; L.redraw(); if (s.shown >= s.R * s.C) { update(); return false; } } });
    L.playButton(run, ['Fill the table', 'Pause'], () => { if (s.shown >= s.R * s.C) s.shown = 0; });
    L.button('Clear blocks', () => { s.blocked.clear(); update(); });
    let geo = null;
    onTap(c, (x, y) => {
      if (!geo) return;
      const col = Math.floor((x - geo.x0) / geo.cs), row = Math.floor((y - geo.y0) / geo.cs);
      if (row < 0 || col < 0 || row >= s.R || col >= s.C || (row === 0 && col === 0) || (row === s.R - 1 && col === s.C - 1)) return;
      const key = `${row},${col}`;
      s.blocked.has(key) ? s.blocked.delete(key) : s.blocked.add(key);
      s.shown = s.R * s.C; update();
    });
    const dp = () => {
      const t = Array.from({ length: s.R }, () => Array(s.C).fill(0));
      for (let r = 0; r < s.R; r++) for (let q = 0; q < s.C; q++) {
        if (s.blocked.has(`${r},${q}`)) continue;
        t[r][q] = r === 0 && q === 0 ? 1 : (r ? t[r - 1][q] : 0) + (q ? t[r][q - 1] : 0);
      }
      return t;
    };
    function update() {
      const t = dp(), ans = t[s.R - 1][s.C - 1], moves = s.R - 1 + s.C - 1;
      L.stats([['moves per path', `${s.R - 1} down + ${s.C - 1} right = ${moves}`], ['formula C(moves, downs)', `C(${moves}, ${s.R - 1}) = ${binom(moves, s.R - 1)}`, s.blocked.size ? '' : 'accent'],
        ['DP answer', ans, 'accent'], s.blocked.size ? ['blocked cells', s.blocked.size, 'err'] : null]);
      L.insight(s.blocked.size
        ? `With blocked cells the closed formula no longer applies, but the <b>recurrence</b> still does: ways(cell) = ways(above) + ways(left), and a blocked cell has 0 ways. Counting with a recurrence and a table is exactly what dynamic programming is.`
        : `Every path is a word of ${moves} letters with ${s.R - 1} D’s and ${s.C - 1} R’s, like <code>${'R'.repeat(Math.min(3, s.C - 1))}${'D'.repeat(s.R - 1)}${'R'.repeat(Math.max(0, s.C - 4))}</code>. Choosing which ${s.R - 1} of the ${moves} positions are D’s picks the path, so there are <b>C(${moves}, ${s.R - 1}) = ${binom(moves, s.R - 1)}</b>. The table is Pascal’s triangle turned on its side.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, t = dp(), cs = Math.min((c.w - 30) / s.C, (c.h - 20) / s.R), x0 = (c.w - cs * s.C) / 2, y0 = 10;
      geo = { x0, y0, cs };
      for (let r = 0; r < s.R; r++) for (let q = 0; q < s.C; q++) {
        const idx = r * s.C + q, x = x0 + q * cs, y = y0 + r * cs, blk = s.blocked.has(`${r},${q}`), vis = idx < s.shown;
        const end = r === s.R - 1 && q === s.C - 1, start = r === 0 && q === 0;
        fillRR(ctx, x + 2, y + 2, cs - 4, cs - 4, 6, blk ? P.alpha('err', .35) : end && vis ? P.alpha('accent', .8) : vis ? P.alpha('accent', .12) : P.surface2, blk ? P.err : P.border);
        if (blk) D.text(ctx, '✕', x + cs / 2, y + cs / 2, { color: P.err, size: cs * .35, align: 'center', weight: 700 });
        else if (vis) D.text(ctx, String(t[r][q]), x + cs / 2, y + cs / 2, { color: end ? P.bg : P.text, size: Math.min(15, cs * .32), align: 'center', mono: true, weight: 700 });
        if (start) D.text(ctx, 'start', x + 6, y + 11, { color: P.faint, size: 9 });
        if (vis && idx === s.shown - 1 && !blk && !start && run.running) {
          if (r) D.arrow(ctx, x + cs / 2, y - cs * .2, x + cs / 2, y + cs * .22, P.ok, 1.6, 6);
          if (q) D.arrow(ctx, x - cs * .2, y + cs / 2, x + cs * .22, y + cs / 2, P.ok, 1.6, 6);
        }
      }
    };
    s.shown = s.R * s.C;
    update();
  },
});

/* =========================================================== math-choose == */
defineLab('math-choose', {
  title: 'Arrange or choose? Every outcome, listed',
  hint: 'Answer the two questions, <b>does order matter?</b> and <b>can an item repeat?</b>, and every outcome is listed. Each row holds all the orderings of one selection. Switch order off and watch each row collapse to a single outcome.',
  mount(L) {
    const s = { n: 4, k: 2, order: 'yes', rep: 'no' };
    const NAMES = 'ABCDEF', ROWS = 30;
    const fact = m => m <= 1 ? 1 : m * fact(m - 1);
    const sup = v => String(v).replace(/\d/g, d => '⁰¹²³⁴⁵⁶⁷⁸⁹'[d]);
    const nS = L.slider('items to pick from (n)', { min: 2, max: 6, value: s.n }, v => { s.n = v; update(); });
    const kS = L.slider('how many you pick (k)', { min: 1, max: 4, value: s.k }, v => { s.k = v; update(); });
    const oS = L.seg('order matters?', [['yes', 'yes'], ['no', 'no']], s.order, v => { s.order = v; update(); });
    const rS = L.seg('repeats allowed?', [['no', 'no'], ['yes', 'yes']], s.rep, v => { s.rep = v; update(); });
    const EX = { pin: ['PIN code', 6, 3, 'yes', 'yes'], podium: ['Podium', 5, 3, 'yes', 'no'], team: ['Team', 5, 3, 'no', 'no'], scoops: ['Ice-cream scoops', 3, 3, 'no', 'yes'] };
    L.seg('example', Object.entries(EX).map(([k, v]) => [k, v[0]]), '', v => {
      const [, n, k, o, r] = EX[v]; s.n = n; s.k = k; s.order = o; s.rep = r;
      nS.set(n, true); kS.set(k, true); oS.set(o, true); rS.set(r, true); update();
    });
    L.stage.innerHTML = '<div class="mc"><div class="mc-rows"></div><p class="mlab-note"></p></div>';
    const rowsEl = L.stage.querySelector('.mc-rows'), noteEl = L.stage.querySelector('.mlab-note');
    /* selections: sorted index tuples, with or without repeats */
    function groups(n, k, rep) {
      const out = [], cur = [];
      (function go(start) {
        if (cur.length === k) { out.push(cur.slice()); return; }
        for (let i = start; i < n; i++) { cur.push(i); go(rep ? i : i + 1); cur.pop(); }
      })(0);
      return out;
    }
    /* the distinct orderings of one selection, in lexicographic order */
    function orderings(sel) {
      const out = [], cur = [], used = sel.map(() => false);
      (function go() {
        if (cur.length === sel.length) { out.push(cur.slice()); return; }
        for (let i = 0; i < sel.length; i++) {
          if (used[i] || (i && sel[i] === sel[i - 1] && !used[i - 1])) continue;
          used[i] = true; cur.push(sel[i]); go(); cur.pop(); used[i] = false;
        }
      })();
      return out;
    }
    const tok = i => `<i class="mc-t mc-c${i}">${NAMES[i]}</i>`;
    const bars = (sel, n) => Array.from({ length: n }, (_, i) => '★'.repeat(sel.filter(x => x === i).length)).join('|');
    function update() {
      const { n, k } = s, ord = s.order === 'yes', rep = s.rep === 'yes';
      const G = !rep && k > n ? [] : groups(n, k, rep);
      let total = 0, html = '';
      G.forEach((g, gi) => {
        const os = orderings(g);
        total += ord ? os.length : 1;
        if (gi >= ROWS) return;
        const label = `{${g.map(i => NAMES[i]).join(', ')}}`;
        html += `<div class="mc-row${ord ? '' : ' collapsed'}"><span class="mc-set">${label}${rep && !ord ? `<small>${bars(g, n)}</small>` : ''}</span>
          <span class="mc-chips">${os.map((o, j) => `<span class="mc-chip${!ord && j ? ' gone' : ''}">${o.map(tok).join('')}</span>`).join('')}</span>
          <span class="mc-n">${ord ? os.length : 1}</span></div>`;
      });
      rowsEl.innerHTML = html || `<p class="mc-empty">No outcomes: you cannot pick ${k} <b>different</b> items from only ${n}.</p>`;
      noteEl.innerHTML = G.length > ROWS ? `Showing the first ${ROWS} of ${G.length} rows. Every outcome is still counted in the total.` : `Items: ${Array.from({ length: n }, (_, i) => tok(i)).join(' ')} · each row is one ${rep ? 'multiset' : 'set'}; the number on the right is how many outcomes it contributes.`;
      const perm = !rep && k <= n ? fact(n) / fact(n - k) : 0;
      const F = ord && rep ? [`n${sup('k')}`, `${Array(k).fill(n).join(' × ')} = ${n ** k}`, `product(S, repeat=${k})`, 'a PIN code or password']
        : ord ? ['P(n, k) = n! / (n − k)!', k > n ? '0' : `${Array.from({ length: k }, (_, i) => n - i).join(' × ')} = ${perm}`, `permutations(S, ${k})`, 'gold, silver and bronze']
        : !rep ? ['C(n, k) = P(n, k) / k!', k > n ? '0' : `${perm} / ${k}! = ${perm / fact(k)}`, `combinations(S, ${k})`, 'picking a team']
        : ['C(n + k − 1, k)', `C(${n + k - 1}, ${k}) = ${binom(n + k - 1, k)}`, `combinations_with_replacement(S, ${k})`, 'scoops from flavours'];
      L.stats([['outcomes', total.toLocaleString('en-US'), 'accent'], ['formula', F[0]], ['here', F[1], 'ok'], ['itertools', F[2]], ['think of', F[3]]]);
      L.insight(!rep && k > n ? `<b>Zero.</b> Every pick uses an item up, and after ${n} picks nothing is left. That is the pigeonhole principle from chapter 04.`
        : ord && !rep ? `<b>Each pick uses an item up:</b> ${n} choices for the first slot, ${n - 1} for the next, and so on. Look at the right-hand column: <b>every row has exactly ${k}! = ${fact(k)} orderings</b> of the same set. Now switch <i>order matters</i> to <b>no</b>.`
        : !ord && !rep ? `<b>Every row collapsed to one outcome.</b> When order mattered, each set was listed ${k}! = ${fact(k)} times, so dividing by ${k}! counts each set once: C(${n}, ${k}) = ${perm} / ${fact(k)} = ${total}. That division is the whole difference between permutations and combinations.`
        : ord ? `<b>Every slot has all ${n} choices, independently</b>, so multiply: ${n}${sup(k)} = ${total}. Look at the right-hand column. Rows with a repeated item have <b>fewer</b> orderings (AA has one, AB has two), so the rows are not all the same size.`
        : `<b>You cannot just divide ${n}${sup(k)} by ${k}!</b> here, because the rows had different sizes. Instead, write each selection as stars and bars (the small code under each row): ${k} stars for the picks and ${n - 1} bars between the ${n} flavours. That gives C(${n + k - 1}, ${k}) = ${total}.`);
    }
    update();
  },
});

/* ============================================================= math-perm == */
defineLab('math-perm', {
  title: 'Permutations in order: next, and k-th',
  hint: '<b>Next permutation</b>: press <b>Step</b> to run the four-step algorithm on the tiles. <b>k-th permutation</b>: drag k and read each position straight off a factorial-sized block, with no listing at all.',
  mount(L) {
    const fact = m => m <= 1 ? 1 : m * fact(m - 1);
    const START = { a: [1, 2, 3, 4], b: [1, 2, 3, 4, 5], c: [1, 1, 2, 3], d: [3, 1, 4, 2] };
    const s = { mode: 'next', seq: 'a', a: START.a.slice(), phase: 0, i: -1, j: -1, n: 4, k: 10 };
    L.stage.innerHTML = '<div class="mp"><div class="mp-tiles"></div><div class="mp-body"></div></div>';
    const tilesEl = L.stage.querySelector('.mp-tiles'), bodyEl = L.stage.querySelector('.mp-body');
    L.seg('', [['next', 'next permutation'], ['kth', 'k-th permutation']], s.mode, v => { s.mode = v; build(); });
    const seqSeg = L.seg('start from', [['a', '1 2 3 4'], ['b', '1 2 3 4 5'], ['c', '1 1 2 3'], ['d', '3 1 4 2']], s.seq, v => { s.seq = v; reset(); });
    const seqRow = L.actions.lastElementChild;
    const bStep = L.button('Step', step), bNext = L.button('Next permutation', () => { do step(); while (s.phase); }), bReset = L.button('Reset', reset);
    function reset() { s.a = START[s.seq].slice(); s.phase = 0; s.i = s.j = -1; update(); }
    function build() {
      const next = s.mode === 'next';
      [seqRow, bStep, bNext, bReset].forEach(e => { e.hidden = !next; });
      L.clearDyn();
      if (!next) {
        L.slider('items (n)', { min: 3, max: 6, value: s.n, dyn: true }, v => { s.n = v; s.k = Math.min(s.k, fact(v)); build(); });
        L.slider('k', { min: 1, max: fact(s.n), value: s.k, dyn: true }, v => { s.k = v; update(); });
      }
      update();
    }
    function step() {
      const a = s.a;
      if (s.phase === 0) {
        let i = a.length - 2;
        while (i >= 0 && a[i] >= a[i + 1]) i--;
        s.i = i; s.phase = 1;
      } else if (s.phase === 1) {
        if (s.i < 0) { a.reverse(); s.phase = 0; s.i = -1; s.wrapped = true; update(); return; }
        let j = a.length - 1;
        while (a[j] <= a[s.i]) j--;
        s.j = j; s.phase = 2;
      } else if (s.phase === 2) {
        [a[s.i], a[s.j]] = [a[s.j], a[s.i]]; s.phase = 3;
      } else {
        const r = a.splice(s.i + 1).reverse(); a.push(...r); s.phase = 0;
      }
      s.wrapped = false;
      update();
    }
    const allPerms = base => {
      const out = [], cur = [], b = base.slice().sort((x, y) => x - y), used = b.map(() => false);
      (function go() {
        if (cur.length === b.length) { out.push(cur.join(' ')); return; }
        for (let i = 0; i < b.length; i++) {
          if (used[i] || (i && b[i] === b[i - 1] && !used[i - 1])) continue;
          used[i] = true; cur.push(b[i]); go(); cur.pop(); used[i] = false;
        }
      })();
      return out;
    };
    const tile = (v, cls = '') => `<span class="mp-tile ${cls}">${v}</span>`;
    function update() {
      if (s.mode === 'next') return updateNext();
      const n = s.n, pool = Array.from({ length: n }, (_, i) => i + 1), res = [];
      let r = s.k - 1, rows = '';
      for (let p = 0; p < n; p++) {
        const f = fact(n - 1 - p), idx = Math.floor(r / f);
        rows += `<tr><td>${p + 1}</td><td class="mp-pool">${pool.map((v, i) => tile(v, i === idx ? 'pick' : '')).join('')}</td><td>${(n - 1 - p)}! = ${f}</td><td>${r} ÷ ${f} = <b>${idx}</b> rem ${r % f}</td></tr>`;
        res.push(pool.splice(idx, 1)[0]); r %= f;
      }
      tilesEl.innerHTML = res.map(v => tile(v, 'done')).join('');
      bodyEl.innerHTML = `<div class="table-wrap"><table class="mlab-table mp-table"><thead><tr><th>position</th><th>items left (picked one lit)</th><th>block size</th><th>remaining ÷ block</th></tr></thead><tbody>${rows}</tbody></table></div>`;
      L.stats([['k', `${s.k} of ${fact(n)}`, 'accent'], ['start from', `k − 1 = ${s.k - 1}`], ['answer', res.join(' '), 'ok'], ['work', `O(n²), not O(n!)`]]);
      L.insight(`<b>Think of a car odometer with wheels of size ${n}, ${n - 1}, …, 1.</b> The first item stays the same for blocks of ${n - 1}! = ${fact(n - 1)} permutations, so (k − 1) ÷ ${fact(n - 1)} says which block, and so which remaining item, comes first. The remainder is the position inside that block, and the same step repeats with one item fewer.`);
    }
    function updateNext() {
      const a = s.a, n = a.length;
      tilesEl.innerHTML = a.map((v, x) => {
        let c = '';
        if (s.phase >= 1 && s.i >= 0 && x > s.i) c = 'suffix';
        if (s.phase >= 1 && s.i < 0) c = 'suffix';
        if (x === s.i && s.phase >= 1) c = 'pivot';
        if (x === s.j && s.phase === 2) c = 'succ';
        if (s.phase === 3 && (x === s.i || x === s.j)) c = x === s.i ? 'pivot' : 'suffix swapped';
        return tile(v, c);
      }).join('');
      const list = allPerms(a), cur = a.join(' '), at = list.indexOf(cur);
      const near = list.map((p, x) => [p, x]).filter(([, x]) => Math.abs(x - at) <= 3);
      bodyEl.innerHTML = `<div class="mp-list">${near.map(([p, x]) => `<span class="${x === at ? 'on' : ''}">#${x + 1}&nbsp; ${p}</span>`).join('')}</div>`;
      const msg = [
        s.wrapped ? '<b>That was the last permutation</b> (fully descending), so the algorithm wrapped around to the first one: the whole array reversed.'
          : '<b>Step 1: find the pivot.</b> Scan from the right while the numbers keep rising. The part you pass over is already in its <i>largest</i> order and cannot grow on its own.',
        s.i < 0 ? '<b>No pivot:</b> the whole array is descending, so this is the last permutation. The next step reverses everything and wraps around to the first.'
          : `<b>Pivot found: ${a[s.i]}</b> at position ${s.i + 1}. Everything to its right (shaded) is descending. To get the <i>next</i> arrangement, ${a[s.i]} must grow by as little as possible.`,
        `<b>Step 2: pick the successor.</b> Take the rightmost item in the suffix that is larger than the pivot: <b>${s.j >= 0 ? a[s.j] : ''}</b>. It is the smallest value that can replace ${s.i >= 0 ? a[s.i] : ''}.`,
        '<b>Step 3: swapped.</b> The suffix is still descending, which is its largest order. <b>Step 4</b> reverses it into ascending order, its smallest, so the result is the very next permutation.',
      ];
      L.stats([['rank', `#${at + 1} of ${list.length}`, 'accent'], ['phase', ['ready', 'pivot', 'successor', 'swapped'][s.phase]], ['cost per step', 'O(n)'], list.length < fact(n) ? ['distinct', `${n}! / repeats = ${list.length}`, 'ok'] : null]);
      L.insight(msg[s.phase]);
    }
    build();
  },
});
}
