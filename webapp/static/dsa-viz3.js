/* ============================================================================
   DSA visualizers, part 3 — topics 21 to 27.
   Engine and helpers live in dsa-viz.js; grid/graph helpers in dsa-viz2.js.
   ========================================================================= */
'use strict';

/* =========================================================== 21 · math & geometry == */
defineAlgo('21_math_geometry', {
  title: 'Fast power: squaring instead of multiplying', short: 'Fast power',
  idea: 'Read the exponent in binary. Square the base at every step, and multiply it into the answer only where the exponent has a 1-bit. 2³⁰ costs 5 multiplications instead of 30 — the same trick modular exponentiation and matrix power use.',
  complexity: 'Time O(log n) multiplications · Space O(1) iteratively',
  input: '3 ; 13', hint: 'base ; exponent (0–30)',
  code: [
    'def power(x, n):',
    '    result = 1',
    '    while n:',
    '        if n & 1:                 # this bit is set',
    '            result *= x',
    '        x *= x                    # square the base',
    '        n >>= 1                   # drop the bit',
    '    return result',
  ],
  parse(s) {
    const [a, b] = avParts(s);
    const x = avNum(a, 'a base'), n = avNum(b, 'an exponent');
    if (n < 0 || n > 30 || n % 1) throw new Error('Use a whole exponent from 0 to 30');
    if (Math.abs(x) > 12) throw new Error('Keep the base between −12 and 12 so the numbers stay readable');
    return { x, n };
  },
  run({ x, n }) {
    const { F, snap } = avRecorder();
    const bits = n.toString(2);
    let base = x, k = n, result = 1, step = 0, mults = 0;
    const S = (extra = {}) => ({ x, n, bits, base, k, result, step, mults, ...extra });
    snap(1, `Exponent ${n} is <code>${bits}₂</code>. Read it right to left.`, S({ vars: { result: 1, base: x } }));
    while (k) {
      const set = k & 1;
      snap(3, `Bit ${step} of the exponent is ${set}${set ? ' — this power of the base is part of the answer.' : ' — skip it.'}`, S({ set, vars: { bit: step, base } }));
      if (set) { result *= base; mults++; snap(4, `result ×= ${base} → <b>${result}</b>.`, S({ set, used: true, vars: { result, multiplications: mults } })); }
      k >>= 1; step++;
      if (k) { base *= base; mults++; snap(5, `Square the base: ${base} (that is x^${2 ** step}).`, S({ squared: true, vars: { base, multiplications: mults } })); }
    }
    snap(7, `${x}^${n} = <b>${result}</b> using ${mults} multiplications instead of ${n}.`, S({ done: true, vars: { answer: result, multiplications: mults, naive: n } }));
    return F;
  },
  height: () => 250,
  draw(ctx, c, f, P) {
    const bits = [...f.bits];
    const bw = Math.min(40, (c.w - 60) / bits.length);
    const left = (c.w - bits.length * (bw + 5)) / 2;
    bits.forEach((b, i) => {
      const idx = bits.length - 1 - i, on = idx === f.step, used = idx < f.step;
      const x = left + i * (bw + 5);
      ctx.fillStyle = on ? P.alpha('accent', .4) : b === '1' ? P.alpha('ok', .22) : P.surface2;
      D.rrect(ctx, x, 40, bw, 34, 7); ctx.fill();
      ctx.strokeStyle = on ? P.accent : b === '1' ? P.ok : P.strong; ctx.lineWidth = on ? 2.4 : 1;
      ctx.globalAlpha = used && !on ? .45 : 1; ctx.stroke();
      D.text(ctx, b, x + bw / 2, 57, { color: P.text, size: 15, align: 'center', mono: true, weight: 700 });
      D.text(ctx, `x^${2 ** idx}`, x + bw / 2, 86, { color: b === '1' ? P.ok : P.faint, size: 10, align: 'center', mono: true });
      ctx.globalAlpha = 1;
    });
    D.text(ctx, `exponent ${f.n} in binary`, c.w / 2, 24, { color: P.dim, size: 11.5, align: 'center', weight: 650 });
    const y = 128;
    const card = (x, w, label, val, color, hot) => {
      ctx.fillStyle = hot ? P.alpha(color, .3) : P.surface2; D.rrect(ctx, x, y, w, 52, 10); ctx.fill();
      ctx.strokeStyle = hot ? color : P.strong; ctx.lineWidth = hot ? 2.4 : 1; ctx.stroke();
      D.text(ctx, label, x + w / 2, y + 16, { color: P.dim, size: 11, align: 'center', weight: 650 });
      D.text(ctx, String(val), x + w / 2, y + 36, { color: P.text, size: 16, align: 'center', mono: true, weight: 700 });
    };
    const w = Math.min(190, (c.w - 60) / 2);
    card(c.w / 2 - w - 10, w, 'result', f.result, P.ok, f.used || f.done);
    card(c.w / 2 + 10, w, 'base (x²ᵏ)', f.base, P.accent, f.squared);
    D.text(ctx, f.done ? `${f.mults} multiplications, not ${f.n}` : 'set bit → fold the base into the result; then square', c.w / 2, c.h - 16, { color: f.done ? P.ok : P.dim, size: 12.5, align: 'center', weight: 650 });
  },
});

defineAlgo('21_math_geometry', {
  title: 'Happy number: the cycle in digit squares', short: 'Happy number',
  idea: 'Replace the number by the sum of the squares of its digits and repeat. The sequence must either reach 1 or fall into a loop, because the values quickly drop below 243 — so a visited set (or Floyd’s two pointers) decides it in constant space.',
  complexity: 'Time O(log n) per step, O(1) extra space with slow/fast pointers',
  input: '19', hint: 'any positive number (try 19 and 116)',
  code: [
    'def is_happy(n):',
    '    seen = set()',
    '    while n != 1 and n not in seen:',
    '        seen.add(n)',
    '        n = sum(int(d) ** 2 for d in str(n))',
    '    return n == 1',
  ],
  parse(s) { const n = avNums(s, 1, 'one number')[0]; if (n < 1 || n > 9999 || n % 1) throw new Error('Use a whole number from 1 to 9999'); return { n }; },
  run({ n }) {
    const { F, snap } = avRecorder();
    const seen = [];
    let cur = n;
    const S = (extra = {}) => ({ seq: [...seen], cur, ...extra });
    snap(2, `Start at ${n}.`, S({ vars: { n } }));
    for (let guard = 0; guard < 40; guard++) {
      if (cur === 1) { snap(5, 'Reached 1 — the number is <b>happy</b>.', S({ happy: true, vars: { result: 'True' } })); return F; }
      const at = seen.indexOf(cur);
      if (at >= 0) { snap(2, `${cur} has been seen before (step ${at + 1}): the sequence is in a <b>cycle</b>, so it never reaches 1.`, S({ cycleAt: at, vars: { result: 'False' } })); return F; }
      seen.push(cur);
      const digits = String(cur).split('').map(Number);
      const next = digits.reduce((a, d) => a + d * d, 0);
      snap(4, `${digits.map(d => `${d}²`).join(' + ')} = ${digits.map(d => d * d).join(' + ')} = <b>${next}</b>.`, S({ digits, next, vars: { from: cur, to: next } }));
      cur = next;
    }
    snap(5, 'Stopped after 40 steps.', S({}));
    return F;
  },
  height: () => 260,
  draw(ctx, c, f, P) {
    const seq = f.seq.concat(f.cur !== undefined && !f.seq.includes(f.cur) ? [f.cur] : []);
    const per = Math.min(6, Math.max(3, Math.ceil(seq.length / 2)));
    const pos = i => [40 + (i % per) * ((c.w - 100) / Math.max(1, per - 1 || 1)), 60 + Math.floor(i / per) * 86];
    seq.forEach((v, i) => {
      if (i === 0) return;
      const [x1, y1] = pos(i - 1), [x2, y2] = pos(i);
      if (Math.floor((i - 1) / per) === Math.floor(i / per)) AV.arrow(ctx, x1 + 24, y1, x2 - 24, y2, P.strong, 1.6);
      else { ctx.beginPath(); ctx.moveTo(x1, y1 + 24); ctx.quadraticCurveTo(c.w / 2, y1 + 56, x2, y2 - 24); ctx.strokeStyle = P.strong; ctx.lineWidth = 1.6; ctx.stroke(); }
    });
    if (f.cycleAt != null) {
      const [x1, y1] = pos(seq.length - 1), [x2, y2] = pos(f.cycleAt);
      ctx.beginPath(); ctx.moveTo(x1, y1 + 26); ctx.bezierCurveTo(x1, y1 + 74, x2, y2 + 74, x2, y2 + 26);
      ctx.strokeStyle = P.err; ctx.lineWidth = 2.4; ctx.stroke();
      D.text(ctx, 'cycle', (x1 + x2) / 2, Math.max(y1, y2) + 66, { color: P.err, size: 12, align: 'center', weight: 700 });
    }
    seq.forEach((v, i) => {
      const [x, y] = pos(i), isCur = v === f.cur;
      AV.node(ctx, P, x, y, 23, v, {
        fill: v === 1 ? P.alpha('ok', .35) : isCur ? P.alpha('accent', .32) : f.cycleAt != null && i >= f.cycleAt ? P.alpha('err', .18) : null,
        stroke: v === 1 ? P.ok : isCur ? P.accent : null,
        sub: i === 0 ? 'start' : null,
      });
    });
    if (f.digits) D.text(ctx, `${f.digits.map(d => `${d}²`).join(' + ')} = ${f.next}`, c.w / 2, c.h - 16, { color: P.accent, size: 13, align: 'center', mono: true, weight: 650 });
    else if (f.happy) D.text(ctx, 'reached 1 — happy', c.w / 2, c.h - 16, { color: P.ok, size: 13, align: 'center', weight: 700 });
    else if (f.cycleAt != null) D.text(ctx, 'back to a number already seen — not happy', c.w / 2, c.h - 16, { color: P.err, size: 13, align: 'center', weight: 700 });
  },
});

/* ================================================================== 22 · sorting == */
defineAlgo('22_sorting_algorithms', {
  title: 'Quicksort vs merge sort', short: 'Quick / merge',
  idea: '<b>Quicksort</b> partitions first and recurses on halves that are already in the right place — in-place, cache-friendly, O(n²) on an unlucky pivot. <b>Merge sort</b> splits blindly and does the work while combining — stable, predictable O(n log n), but it needs a second buffer.',
  complexity: 'Quicksort: average O(n log n), worst O(n²), space O(log n) · Merge sort: always O(n log n), space O(n)',
  input: '38, 27, 43, 3, 9, 82, 10', hint: 'numbers to sort',
  variants: [['quick', 'Quicksort'], ['merge', 'Merge sort']],
  code: v => v === 'merge' ? [
    'def merge_sort(a):',
    '    if len(a) <= 1: return a',
    '    mid = len(a) // 2',
    '    left  = merge_sort(a[:mid])',
    '    right = merge_sort(a[mid:])',
    '    out = []',
    '    while left and right:                 # the real work',
    '        out.append(left.pop(0) if left[0] <= right[0] else right.pop(0))',
    '    return out + left + right',
  ] : [
    'def quicksort(a, lo, hi):',
    '    if lo >= hi: return',
    '    pivot = a[hi]',
    '    i = lo',
    '    for j in range(lo, hi):',
    '        if a[j] < pivot:',
    '            a[i], a[j] = a[j], a[i]; i += 1',
    '    a[i], a[hi] = a[hi], a[i]             # pivot lands here, for good',
    '    quicksort(a, lo, i - 1); quicksort(a, i + 1, hi)',
  ],
  parse(s) { return { nums: avNums(s, 10, 'values') }; },
  run({ nums }, v) {
    const { F, snap } = avRecorder();
    const a = [...nums];
    const settled = a.map(() => false);
    const S = (extra = {}) => ({ a: [...a], settled: [...settled], ...extra });
    if (v === 'merge') {
      const depthOf = [];
      const sort = (lo, hi, depth) => {
        if (hi - lo <= 0) { snap(1, `A single element [${a[lo]}] is already sorted.`, S({ lo, hi, depth, vars: { size: 1 } })); return; }
        const mid = (lo + hi) >> 1;
        snap(2, `Split [${a.slice(lo, hi + 1).join(', ')}] into two halves.`, S({ lo, hi, mid, depth, vars: { left: `${lo}…${mid}`, right: `${mid + 1}…${hi}` } }));
        sort(lo, mid, depth + 1); sort(mid + 1, hi, depth + 1);
        const L = a.slice(lo, mid + 1), R = a.slice(mid + 1, hi + 1), out = [];
        while (L.length && R.length) {
          const takeLeft = L[0] <= R[0];
          out.push(takeLeft ? L.shift() : R.shift());
          snap(7, `Compare fronts: take <b>${out[out.length - 1]}</b> from the ${takeLeft ? 'left' : 'right'} half.`, S({ lo, hi, mid, depth, merging: [...out], rest: [...L, ...R], vars: { merged: out.length } }));
        }
        const merged = out.concat(L, R);
        merged.forEach((x, k) => (a[lo + k] = x));
        snap(8, `Merged into [${merged.join(', ')}].`, S({ lo, hi, depth, mergedRange: [lo, hi], vars: { range: `${lo}…${hi}` } }));
        depthOf.push(depth);
      };
      sort(0, a.length - 1, 0);
      a.forEach((_, i) => (settled[i] = true));
      snap(8, `Sorted: [${a.join(', ')}] — merge sort always costs n log n comparisons, whatever the input looks like.`, S({ done: true, vars: { result: `[${a.join(', ')}]` } }));
      return F;
    }
    const qs = (lo, hi) => {
      if (lo >= hi) { if (lo === hi) { settled[lo] = true; snap(1, `One element left at index ${lo}: it is in place.`, S({ lo, hi })); } return; }
      const pivot = a[hi];
      snap(2, `Partition ${lo}…${hi} around the pivot <b>${pivot}</b> (the last element).`, S({ lo, hi, pivot: hi, vars: { pivot, range: `${lo}…${hi}` } }));
      let i = lo;
      for (let j = lo; j < hi; j++) {
        snap(5, `${a[j]} ${a[j] < pivot ? '<' : '≥'} ${pivot}: ${a[j] < pivot ? 'it belongs on the left' : 'leave it on the right'}.`, S({ lo, hi, pivot: hi, i, j, vars: { i, j, value: a[j] } }));
        if (a[j] < pivot) {
          if (i !== j) { [a[i], a[j]] = [a[j], a[i]]; snap(6, `Swap it to index ${i}.`, S({ lo, hi, pivot: hi, i, j, swap: [i, j], vars: { i, j } })); }
          i++;
        }
      }
      [a[i], a[hi]] = [a[hi], a[i]];
      settled[i] = true;
      snap(7, `Put the pivot at index ${i}: every smaller value is left of it, every larger one right. <b>Index ${i} is final.</b>`, S({ lo, hi, pivot: i, i, placed: i, vars: { pivot_index: i } }));
      qs(lo, i - 1); qs(i + 1, hi);
    };
    qs(0, a.length - 1);
    snap(8, `Sorted in place: [${a.join(', ')}]. No extra array was allocated.`, S({ done: true, vars: { result: `[${a.join(', ')}]` } }));
    return F;
  },
  height: () => 300,
  draw(ctx, c, f, P) {
    const g = AV.bars(ctx, P, f.a, {
      cw: c.w, top: 44, bottom: 200,
      style: i => {
        if (f.swap?.includes(i)) return { fill: P.alpha('err', .5), stroke: P.err };
        if (i === f.pivot) return { fill: P.alpha('accent', .65), stroke: P.accent };
        if (f.settled[i]) return { fill: P.alpha('ok', .5) };
        if (i === f.j) return { fill: P.alpha(P.series[0], .55), stroke: P.series[0] };
        if (f.lo != null && (i < f.lo || i > f.hi)) return { fill: P.alpha('faint', .2), fade: true };
        return {};
      },
    });
    if (f.lo != null && f.hi != null && f.hi >= f.lo) {
      const x1 = g.x(f.lo) - g.w / 2 - 4, x2 = g.x(f.hi) + g.w / 2 + 4;
      ctx.strokeStyle = P.alpha('accent', .5); ctx.lineWidth = 1.4;
      D.rrect(ctx, x1, 36, x2 - x1, 172, 8); ctx.stroke();
      D.text(ctx, `working range ${f.lo}…${f.hi}`, (x1 + x2) / 2, 28, { color: P.accent, size: 11, align: 'center', weight: 650 });
    }
    if (f.i != null) AV.ptr(ctx, P, { x: g.x, y: 212, size: 0 }, f.i, 'i', P.ok);
    if (f.j != null) AV.ptr(ctx, P, { x: g.x, y: 212, size: 0 }, f.j, 'j', P.series[0], f.i === f.j ? 1 : 0);
    if (f.merging) D.text(ctx, `merging → [${f.merging.join(', ')}]  ·  left over: [${f.rest.join(', ')}]`, 20, c.h - 34, { color: P.series[0], size: 12, mono: true });
    D.text(ctx, f.done ? 'green = final position' : f.pivot != null ? 'orange = pivot · green = settled for good' : 'split, then merge in order', 20, c.h - 12, { color: f.done ? P.ok : P.dim, size: 12.5, weight: 650 });
  },
});

defineAlgo('22_sorting_algorithms', {
  title: 'Dutch national flag (sort colors)', short: 'Sort colors',
  idea: 'Three pointers cut the array into four regions: settled 0s, settled 1s, unknown, settled 2s. Each step shrinks the unknown region by one, so one pass with no counting sort and no extra memory.',
  complexity: 'Time O(n), one pass · Space O(1)',
  input: '2, 0, 2, 1, 1, 0', hint: 'only 0, 1 and 2',
  code: [
    'def sort_colors(a):',
    '    low, mid, high = 0, 0, len(a) - 1',
    '    while mid <= high:',
    '        if a[mid] == 0:',
    '            a[low], a[mid] = a[mid], a[low]; low += 1; mid += 1',
    '        elif a[mid] == 1:',
    '            mid += 1                      # already in the middle band',
    '        else:',
    '            a[mid], a[high] = a[high], a[mid]; high -= 1   # do not advance mid',
  ],
  parse(s) { const nums = avNums(s, 12, 'colors'); if (nums.some(x => ![0, 1, 2].includes(x))) throw new Error('Use only 0, 1 and 2'); return { nums }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    const a = [...nums];
    let low = 0, mid = 0, high = a.length - 1;
    const S = (extra = {}) => ({ a: [...a], low, mid, high, ...extra });
    snap(1, 'Everything between mid and high is still unknown.', S({ vars: { low, mid, high } }));
    while (mid <= high) {
      snap(2, `Look at a[mid] = ${a[mid]}.`, S({ look: mid, vars: { mid, value: a[mid] } }));
      if (a[mid] === 0) {
        [a[low], a[mid]] = [a[mid], a[low]];
        snap(4, `A 0 belongs at the front: swap with index ${low}, then advance both pointers.`, S({ swap: [low, mid], vars: { low, mid } }));
        low++; mid++;
      } else if (a[mid] === 1) { snap(6, 'A 1 is already in the middle band — just advance mid.', S({ vars: { mid } })); mid++; }
      else {
        [a[mid], a[high]] = [a[high], a[mid]];
        snap(8, `A 2 belongs at the back: swap with index ${high} and shrink high. <b>mid does not move</b> — the value just swapped in is still unknown.`, S({ swap: [mid, high], vars: { mid, high } }));
        high--;
      }
    }
    snap(8, `mid passed high: sorted in one pass — [${a.join(', ')}].`, S({ done: true, vars: { result: `[${a.join(', ')}]` } }));
    return F;
  },
  height: () => 240,
  draw(ctx, c, f, P) {
    const col = v => (v === 0 ? P.err : v === 1 ? P.accent : P.series[0]);
    const g = AV.row(ctx, P, f.a, {
      cw: c.w, y: 64, max: 48,
      style: i => ({
        fill: P.alpha(col(f.a[i]), f.swap?.includes(i) ? .6 : i === f.look ? .45 : .22),
        stroke: f.swap?.includes(i) ? P.text : i === f.look ? col(f.a[i]) : null,
        fade: false,
      }),
    });
    const band = (a, b, label, color) => {
      if (a > b) return;
      const x1 = g.x(a) - g.size / 2 - 3, x2 = g.x(b) + g.size / 2 + 3;
      ctx.strokeStyle = color; ctx.lineWidth = 1.6;
      D.rrect(ctx, x1, g.y - 8, x2 - x1, g.size + 16, 10); ctx.stroke();
      D.text(ctx, label, (x1 + x2) / 2, g.y - 20, { color, size: 11, align: 'center', weight: 650 });
    };
    band(0, f.low - 1, 'settled 0s', P.err);
    band(f.low, f.mid - 1, 'settled 1s', P.accent);
    band(f.mid, f.high, 'unknown', P.dim);
    band(f.high + 1, f.a.length - 1, 'settled 2s', P.series[0]);
    AV.ptr(ctx, P, g, Math.min(f.low, f.a.length - 1), 'low', P.err);
    AV.ptr(ctx, P, g, Math.min(f.mid, f.a.length - 1), 'mid', P.accent, f.mid === f.low ? 1 : 0);
    AV.ptr(ctx, P, g, Math.max(0, f.high), 'high', P.series[0], f.high === f.mid ? 2 : 0);
    D.text(ctx, f.done ? 'one pass, constant space' : 'each step shrinks the unknown band by one', 20, c.h - 14, { color: f.done ? P.ok : P.dim, size: 12.5, weight: 650 });
  },
});

/* ================================================================== 23 · strings == */
defineAlgo('23_string_algorithms', {
  title: 'KMP: never re-read the text', short: 'KMP search',
  idea: 'The prefix table says, for each position of the pattern, how much of what already matched is <b>also a prefix</b>. On a mismatch you slide the pattern by that amount instead of starting over, so the text pointer only ever moves forward.',
  complexity: 'Time O(n + m) · Space O(m) for the prefix table — naive search is O(n × m)',
  input: 'ababcabcabababd ; ababd', hint: 'text ; pattern',
  variants: [['lps', 'Build the table'], ['search', 'Search the text']],
  code: v => v === 'lps' ? [
    'def build_lps(p):',
    '    lps = [0] * len(p)',
    '    length, i = 0, 1',
    '    while i < len(p):',
    '        if p[i] == p[length]:',
    '            length += 1; lps[i] = length; i += 1',
    '        elif length:',
    '            length = lps[length - 1]      # fall back, do not reset',
    '        else:',
    '            lps[i] = 0; i += 1',
    '    return lps',
  ] : [
    'def kmp(text, pattern):',
    '    lps = build_lps(pattern)',
    '    i = j = 0',
    '    while i < len(text):',
    '        if text[i] == pattern[j]:',
    '            i += 1; j += 1',
    '            if j == len(pattern): return i - j     # match',
    '        elif j:',
    '            j = lps[j - 1]                # slide, i never goes back',
    '        else:',
    '            i += 1',
    '    return -1',
  ],
  parse(s) {
    const [a, b] = avParts(s);
    const text = String(a || '').replace(/\s/g, ''), pat = String(b || '').replace(/\s/g, '');
    if (!text || !pat) throw new Error('Enter text ; pattern');
    if (text.length > 22) throw new Error('Keep the text to 22 characters');
    if (pat.length > 8) throw new Error('Keep the pattern to 8 characters');
    return { text, pat };
  },
  run({ text, pat }, v) {
    const { F, snap } = avRecorder();
    const lps = pat.split('').map(() => 0);
    const buildFrames = [];
    {
      let len = 0, i = 1;
      while (i < pat.length) {
        if (pat[i] === pat[len]) { len++; lps[i] = len; i++; }
        else if (len) len = lps[len - 1];
        else { lps[i] = 0; i++; }
      }
    }
    if (v === 'lps') {
      const t = pat.split('').map(() => 0);
      let len = 0, i = 1;
      const S = (extra = {}) => ({ mode: 'lps', pat, lps: [...t], ...extra });
      snap(1, 'lps[0] is always 0 — a single character has no proper prefix.', S({ i: 0, vars: { lps0: 0 } }));
      while (i < pat.length) {
        snap(4, `Compare pattern[${i}] = <code>${pat[i]}</code> with pattern[${len}] = <code>${pat[len]}</code>.`, S({ i, len, vars: { i, length: len } }));
        if (pat[i] === pat[len]) {
          len++; t[i] = len; i++;
          snap(5, `They match: the prefix that also ends here is <b>${len}</b> long.`, S({ i: i - 1, len, filled: i - 1, vars: { [`lps[${i - 1}]`]: len } }));
        } else if (len) {
          len = t[len - 1];
          snap(7, `Mismatch, but ${t[i - 1] ? '' : ''}fall back to lps[${len === 0 ? '…' : ''}] = ${len} instead of starting from zero.`, S({ i, len, fallback: true, vars: { length: len } }));
        } else { t[i] = 0; i++; snap(9, 'No prefix matches here: lps stays 0.', S({ i: i - 1, len, filled: i - 1, vars: { [`lps[${i - 1}]`]: 0 } })); }
      }
      snap(10, `Prefix table: [${t.join(', ')}]. Each entry is "how much of the match is reusable".`, S({ done: true, vars: { lps: `[${t.join(', ')}]` } }));
      return F;
    }
    let i = 0, j = 0, comparisons = 0;
    const S = (extra = {}) => ({ mode: 'search', text, pat, lps, i, j, comparisons, ...extra });
    snap(1, `Prefix table for “${pat}”: [${lps.join(', ')}].`, S({ vars: { lps: `[${lps.join(', ')}]` } }));
    while (i < text.length) {
      comparisons++;
      const hit = text[i] === pat[j];
      snap(4, `text[${i}] = <code>${text[i]}</code> vs pattern[${j}] = <code>${pat[j]}</code> — ${hit ? 'match' : 'mismatch'}.`, S({ compare: true, hit, vars: { i, j, comparisons } }));
      if (hit) {
        i++; j++;
        if (j === pat.length) { snap(6, `All ${pat.length} characters matched: the pattern starts at index <b>${i - j}</b>.`, S({ found: i - j, vars: { result: i - j, comparisons } })); return F; }
        snap(5, `Advance both pointers.`, S({ vars: { i, j, comparisons } }));
      } else if (j) {
        const nj = lps[j - 1];
        snap(8, `Slide the pattern: j drops from ${j} to <b>${nj}</b> because the first ${nj} characters already match. <b>i does not move.</b>`, S({ slide: [j, nj], vars: { i, j: nj } }));
        j = nj;
      } else { i++; snap(10, 'Nothing matched yet — move one character along the text.', S({ vars: { i, j } })); }
    }
    snap(11, `Reached the end of the text with ${comparisons} comparisons and no match — return −1.`, S({ vars: { result: -1, comparisons } }));
    return F;
  },
  height: (w, last) => (last.mode === 'lps' ? 250 : 280),
  draw(ctx, c, f, P) {
    if (f.mode === 'lps') {
      const g = AV.row(ctx, P, [...f.pat], { cw: c.w, y: 50, max: 46, style: i => i === f.i ? { fill: P.alpha('accent', .35), stroke: P.accent } : i === f.len ? { fill: P.alpha(P.series[0], .3), stroke: P.series[0] } : {} });
      AV.ptr(ctx, P, g, Math.min(f.i ?? 0, f.pat.length - 1), 'i', P.accent);
      if (f.len != null) AV.ptr(ctx, P, g, Math.min(f.len, f.pat.length - 1), 'length', P.series[0], f.len === f.i ? 1 : 0, true);
      const l = AV.row(ctx, P, f.lps, { cw: c.w, y: g.y + g.size + 66, max: 46, index: false, style: i => i === f.filled ? { fill: P.alpha('ok', .3), stroke: P.ok } : { fill: P.alpha('ok', .1) } });
      D.text(ctx, 'lps', l.left - 10, l.y + l.size / 2, { color: P.dim, size: 11.5, align: 'right', weight: 650 });
      D.text(ctx, f.fallback ? 'mismatch → fall back through the table, never back to zero' : 'lps[i] = length of the longest prefix that is also a suffix here', 20, c.h - 14, { color: f.fallback ? P.accent : P.dim, size: 12, weight: 650 });
      return;
    }
    const g = AV.row(ctx, P, [...f.text], { cw: c.w, y: 44, max: 34, style: i => f.found != null && i >= f.found && i < f.found + f.pat.length ? { fill: P.alpha('ok', .35), stroke: P.ok } : i === f.i ? { fill: P.alpha(f.hit === false ? 'err' : 'accent', .35), stroke: f.hit === false ? P.err : P.accent } : i < f.i ? { fade: true } : {} });
    D.text(ctx, 'text', 20, g.y + g.size / 2, { color: P.dim, size: 11.5, weight: 650 });
    const off = f.i - f.j, py = g.y + g.size + 52;
    [...f.pat].forEach((ch, k) => {
      const idx = off + k;
      if (idx < 0 || idx >= f.text.length) return;
      const x = g.x(idx) - g.size / 2, on = k === f.j;
      ctx.fillStyle = on ? P.alpha(f.hit === false ? 'err' : 'accent', .3) : k < f.j ? P.alpha('ok', .22) : P.surface2;
      D.rrect(ctx, x, py, g.size, g.size, 8); ctx.fill();
      ctx.strokeStyle = on ? (f.hit === false ? P.err : P.accent) : k < f.j ? P.ok : P.strong; ctx.lineWidth = on ? 2.4 : 1.2; ctx.stroke();
      D.text(ctx, ch, x + g.size / 2, py + g.size / 2, { color: P.text, size: 13, align: 'center', mono: true, weight: 650 });
    });
    D.text(ctx, 'pattern', 20, py + g.size / 2, { color: P.dim, size: 11.5, weight: 650 });
    if (f.slide) D.text(ctx, `slide: j ${f.slide[0]} → ${f.slide[1]}, the ${f.slide[1]} characters already matched are reused`, 20, py + g.size + 26, { color: P.accent, size: 12, weight: 650 });
    const l = AV.row(ctx, P, f.lps, { cw: c.w, y: py + g.size + 42, max: 28, index: false, style: k => k === f.j - 1 && f.slide ? { fill: P.alpha('accent', .3), stroke: P.accent } : { fill: P.alpha('ok', .1) } });
    D.text(ctx, 'lps', l.left - 8, l.y + l.size / 2, { color: P.dim, size: 11, align: 'right', weight: 650 });
    D.text(ctx, `comparisons: ${f.comparisons}  ·  i never moves backwards`, 20, c.h - 12, { color: P.ok, size: 12, mono: true, weight: 650 });
  },
});

/* =================================================================== 24 · matrix == */
defineAlgo('24_matrix', {
  title: 'Spiral order: four shrinking walls', short: 'Spiral order',
  idea: 'Keep four boundaries — top, bottom, left, right — and walk one edge at a time, moving that boundary inwards afterwards. The two guards (<code>if top &lt;= bottom</code>, <code>if left &lt;= right</code>) before the reverse passes are what stops a single leftover row or column being read twice.',
  complexity: 'Time O(rows × cols) · Space O(1) beyond the output',
  input: '1 2 3 4; 5 6 7 8; 9 10 11 12', hint: 'rows of numbers, separated by “;”',
  code: [
    'def spiral(m):',
    '    top, bottom, left, right = 0, len(m) - 1, 0, len(m[0]) - 1',
    '    out = []',
    '    while top <= bottom and left <= right:',
    '        for c in range(left, right + 1): out.append(m[top][c])',
    '        top += 1',
    '        for r in range(top, bottom + 1): out.append(m[r][right])',
    '        right -= 1',
    '        if top <= bottom:                      # guard the reverse pass',
    '            for c in range(right, left - 1, -1): out.append(m[bottom][c])',
    '            bottom -= 1',
    '        if left <= right:',
    '            for r in range(bottom, top - 1, -1): out.append(m[r][left])',
    '            left += 1',
    '    return out',
  ],
  parse(s) {
    const rows = String(s || '').trim().split(/[;\n]/).map(r => r.trim()).filter(Boolean)
      .map(r => r.split(/[\s,]+/).filter(Boolean).map(Number));
    if (!rows.length) throw new Error('Enter a matrix, one row per “;”');
    if (rows.some(r => r.some(v => !Number.isFinite(v)))) throw new Error('Every cell must be a number');
    if (rows.some(r => r.length !== rows[0].length)) throw new Error('Every row needs the same number of cells');
    if (rows.length > 6 || rows[0].length > 6) throw new Error('Use at most 6 × 6');
    return { m: rows };
  },
  run({ m }) {
    const { F, snap } = avRecorder();
    let top = 0, bottom = m.length - 1, left = 0, right = m[0].length - 1;
    const out = [], order = m.map(r => r.map(() => -1));
    const S = (extra = {}) => ({ m, top, bottom, left, right, out: [...out], order: order.map(r => [...r]), ...extra });
    snap(1, 'Four walls surround the part that has not been read yet.', S({ vars: { top, bottom, left, right } }));
    while (top <= bottom && left <= right) {
      for (let c0 = left; c0 <= right; c0++) { order[top][c0] = out.length; out.push(m[top][c0]); snap(4, `Top row, left to right: ${m[top][c0]}.`, S({ cur: [top, c0], vars: { read: m[top][c0], count: out.length } })); }
      top++;
      snap(5, `Top wall moves down to row ${top}.`, S({ vars: { top } }));
      for (let r = top; r <= bottom; r++) { order[r][right] = out.length; out.push(m[r][right]); snap(6, `Right column, top to bottom: ${m[r][right]}.`, S({ cur: [r, right], vars: { read: m[r][right], count: out.length } })); }
      right--;
      snap(7, `Right wall moves in to column ${right}.`, S({ vars: { right } }));
      if (top <= bottom) {
        for (let c0 = right; c0 >= left; c0--) { order[bottom][c0] = out.length; out.push(m[bottom][c0]); snap(9, `Bottom row, right to left: ${m[bottom][c0]}.`, S({ cur: [bottom, c0], vars: { read: m[bottom][c0], count: out.length } })); }
        bottom--;
        snap(10, `Bottom wall moves up to row ${bottom}.`, S({ vars: { bottom } }));
      } else snap(8, 'Only one row was left and it is already read — the guard stops a double read.', S({ guard: true, vars: { top, bottom } }));
      if (left <= right) {
        for (let r = bottom; r >= top; r--) { order[r][left] = out.length; out.push(m[r][left]); snap(12, `Left column, bottom to top: ${m[r][left]}.`, S({ cur: [r, left], vars: { read: m[r][left], count: out.length } })); }
        left++;
        snap(13, `Left wall moves right to column ${left}.`, S({ vars: { left } }));
      } else snap(11, 'One column left and already read — the second guard stops the double read.', S({ guard: true, vars: { left, right } }));
    }
    snap(14, `The walls crossed: every cell read exactly once — [${out.join(', ')}].`, S({ done: true, vars: { cells: out.length } }));
    return F;
  },
  height: (w, last) => 40 + last.m.length * 48 + 70,
  draw(ctx, c, f, P) {
    const g = avDrawGrid(ctx, P, c, f.m, (i, j) => {
      const cur = f.cur && f.cur[0] === i && f.cur[1] === j;
      const read = f.order[i][j] >= 0;
      const inside = i >= f.top && i <= f.bottom && j >= f.left && j <= f.right;
      return {
        fill: cur ? P.alpha('accent', .45) : read ? P.alpha('ok', .2) : inside ? P.surface2 : P.alpha('faint', .07),
        stroke: cur ? P.accent : read ? P.alpha('ok', .6) : null,
      };
    }, { top: 34 });
    if (f.top <= f.bottom && f.left <= f.right) {
      const x1 = g.x(f.left) - g.cell / 2 - 5, x2 = g.x(f.right) + g.cell / 2 + 5;
      const y1 = g.y(f.top) - g.cell / 2 - 5, y2 = g.y(f.bottom) + g.cell / 2 + 5;
      ctx.strokeStyle = P.accent; ctx.lineWidth = 2; ctx.setLineDash([5, 4]);
      D.rrect(ctx, x1, y1, x2 - x1, y2 - y1, 10); ctx.stroke(); ctx.setLineDash([]);
    }
    D.text(ctx, `output: ${f.out.join(', ') || '—'}`, 20, g.bottom + 26, { color: P.ok, size: 12.5, mono: true, weight: 650 });
    if (f.guard) D.text(ctx, 'guard hit — without it this line would be read twice', 20, g.bottom + 48, { color: P.err, size: 12, weight: 650 });
    else D.text(ctx, `walls: top ${f.top} · bottom ${f.bottom} · left ${f.left} · right ${f.right}`, 20, g.bottom + 48, { color: P.dim, size: 12, mono: true });
  },
});

/* =================================================================== 25 · design == */
defineAlgo('25_design', {
  title: 'LRU cache: hash map + doubly linked list', short: 'LRU cache',
  idea: 'The hash map gives O(1) lookup; the linked list gives O(1) reordering. Every <code>get</code> and <code>put</code> moves its node to the front, so the node at the back is always the least recently used one — and evicting it is a pointer change, not a scan.',
  complexity: 'get / put O(1) · Space O(capacity)',
  input: '2 ; put a 1, put b 2, get a, put c 3, get b, put a 9', hint: 'capacity ; operations (put k v / get k)',
  code: [
    'class LRUCache:',
    '    def get(self, key):',
    '        if key not in self.map: return -1',
    '        node = self.map[key]',
    '        self._move_to_front(node)      # it is now the newest',
    '        return node.value',
    '',
    '    def put(self, key, value):',
    '        if key in self.map:',
    '            self.map[key].value = value; self._move_to_front(...)',
    '        else:',
    '            if len(self.map) == self.cap:',
    '                self._evict(self.tail)  # least recently used',
    '            self._push_front(Node(key, value))',
  ],
  parse(s) {
    const [a, b] = avParts(s);
    const cap = avNum(a, 'a capacity');
    if (cap < 1 || cap > 4) throw new Error('Use a capacity between 1 and 4');
    const ops = String(b || '').split(',').map(x => x.trim()).filter(Boolean).map(tok => {
      const m = tok.match(/^(put|get)\s+(\w+)(?:\s+(-?\d+))?$/i);
      if (!m) throw new Error(`“${tok}” should look like “put a 1” or “get a”`);
      if (/put/i.test(m[1]) && m[3] === undefined) throw new Error(`“${tok}” needs a value`);
      return { op: m[1].toLowerCase(), k: m[2], v: m[3] === undefined ? null : +m[3] };
    });
    if (!ops.length) throw new Error('Add some operations after the “;”');
    if (ops.length > 10) throw new Error('Use at most 10 operations');
    return { cap, ops };
  },
  run({ cap, ops }) {
    const { F, snap } = avRecorder();
    let list = [];            // front (newest) → back (oldest)
    const S = (extra = {}) => ({ cap, list: list.map(n => ({ ...n })), ...extra });
    snap(0, `Empty cache with capacity ${cap}. Front = newest, back = least recently used.`, S({ vars: { size: 0, capacity: cap } }));
    ops.forEach(({ op, k, v }) => {
      const at = list.findIndex(n => n.k === k);
      if (op === 'get') {
        if (at < 0) { snap(2, `<code>get ${k}</code> → miss, return −1.`, S({ miss: k, vars: { op: `get ${k}`, result: -1 } })); return; }
        const node = list[at];
        snap(3, `<code>get ${k}</code> → hit, value ${node.v}.`, S({ hot: k, vars: { op: `get ${k}`, result: node.v } }));
        list.splice(at, 1); list.unshift(node);
        snap(4, `Move <b>${k}</b> to the front: it is now the most recently used.`, S({ hot: k, moved: k, vars: { order: list.map(n => n.k).join(' → ') } }));
        return;
      }
      if (at >= 0) {
        const node = list[at];
        node.v = v;
        list.splice(at, 1); list.unshift(node);
        snap(9, `<code>put ${k} ${v}</code> → key exists: update the value and move it to the front.`, S({ hot: k, moved: k, vars: { op: `put ${k} ${v}`, order: list.map(n => n.k).join(' → ') } }));
        return;
      }
      if (list.length === cap) {
        const victim = list[list.length - 1];
        snap(12, `Cache is full and <b>${k}</b> is new: evict <b>${victim.k}</b>, the node at the back.`, S({ evict: victim.k, vars: { op: `put ${k} ${v}`, evicted: victim.k } }));
        list = list.slice(0, -1);
      }
      list.unshift({ k, v });
      snap(13, `Insert <b>${k} = ${v}</b> at the front.`, S({ hot: k, moved: k, vars: { op: `put ${k} ${v}`, size: list.length } }));
    });
    snap(13, `Final order, newest first: ${list.map(n => `${n.k}=${n.v}`).join(' → ') || 'empty'}.`, S({ done: true, vars: { order: list.map(n => n.k).join(' → ') || '—' } }));
    return F;
  },
  height: () => 260,
  draw(ctx, c, f, P) {
    const n = Math.max(1, f.cap), bw = Math.min(110, (c.w - 60 - (n - 1) * 30) / n);
    const left = 30, y = 110;
    D.text(ctx, 'hash map: key → node', 20, 24, { color: P.dim, size: 11.5, weight: 650 });
    let cx = 150;
    f.list.forEach(nd => {
      const lab = `${nd.k}`;
      ctx.fillStyle = nd.k === f.hot ? P.alpha('accent', .3) : P.surface2;
      D.rrect(ctx, cx, 12, 46, 24, 8); ctx.fill();
      ctx.strokeStyle = nd.k === f.hot ? P.accent : P.strong; ctx.lineWidth = 1.2; ctx.stroke();
      D.text(ctx, lab, cx + 23, 24.5, { color: P.text, size: 12, align: 'center', mono: true, weight: 650 });
      cx += 54;
    });
    if (f.miss) D.text(ctx, `${f.miss} is not in the map → −1`, cx + 8, 24, { color: P.err, size: 12, weight: 650 });
    D.text(ctx, 'front · most recently used', left, y - 32, { color: P.ok, size: 11, weight: 650 });
    D.text(ctx, 'back · evict from here', c.w - 30, y - 32, { color: P.err, size: 11, align: 'right', weight: 650 });
    for (let i = 0; i < n; i++) {
      const x = left + i * (bw + 30), nd = f.list[i];
      const hot = nd && nd.k === f.hot, ev = nd && nd.k === f.evict;
      ctx.fillStyle = ev ? P.alpha('err', .3) : hot ? P.alpha('accent', .3) : nd ? P.surface2 : P.alpha('faint', .05);
      D.rrect(ctx, x, y, bw, 58, 10); ctx.fill();
      ctx.strokeStyle = ev ? P.err : hot ? P.accent : nd ? P.strong : P.soft; ctx.lineWidth = ev || hot ? 2.4 : 1.2;
      if (!nd) ctx.setLineDash([4, 4]);
      ctx.stroke(); ctx.setLineDash([]);
      if (nd) {
        D.text(ctx, nd.k, x + bw / 2, y + 22, { color: P.text, size: 15, align: 'center', mono: true, weight: 700 });
        D.text(ctx, `= ${nd.v}`, x + bw / 2, y + 42, { color: P.dim, size: 12, align: 'center', mono: true });
      } else D.text(ctx, 'free', x + bw / 2, y + 30, { color: P.faint, size: 11.5, align: 'center' });
      if (i < n - 1) {
        AV.arrow(ctx, x + bw + 3, y + 22, x + bw + 27, y + 22, P.strong, 1.6);
        AV.arrow(ctx, x + bw + 27, y + 40, x + bw + 3, y + 40, P.strong, 1.6);
      }
      if (f.list[i] && f.list[i].k === f.hot) D.text(ctx, '▲ just used', x + bw / 2, y + 74, { color: P.accent, size: 11, align: 'center', weight: 650 });
    }
    D.text(ctx, f.evict ? `evicting “${f.evict}” — the back of the list is by definition the least recently used`
      : 'every touch moves a node to the front; the list order IS the recency order',
    20, c.h - 14, { color: f.evict ? P.err : P.dim, size: 12.5, weight: 650 });
  },
});

/* ========================================================== 26 · segment tree == */
defineAlgo('26_segment_tree_fenwick', {
  title: 'Segment tree: range sum with updates', short: 'Segment tree',
  idea: 'Each node stores the sum of a range; the children split it in half. A query touches at most two nodes per level — <b>fully covered</b> nodes return immediately, <b>disjoint</b> ones return 0. An update walks one root-to-leaf path and fixes the sums on the way back up.',
  complexity: 'Build O(n) · query and update O(log n) · Space O(4n)',
  input: '2, 5, 1, 4, 9, 3 ; 1 4 ; 2 = 7', hint: 'values ; query lo hi ; index = new value',
  code: [
    'def query(node, lo, hi, l, r):',
    '    if r < lo or hi < l:',
    '        return 0                       # disjoint',
    '    if l <= lo and hi <= r:',
    '        return tree[node]              # fully covered',
    '    mid = (lo + hi) // 2',
    '    return query(2*node, lo, mid, l, r) + query(2*node+1, mid+1, hi, l, r)',
    '',
    'def update(node, lo, hi, i, value):',
    '    if lo == hi: tree[node] = value; return',
    '    mid = (lo + hi) // 2',
    '    update(2*node, lo, mid, i, value) if i <= mid else update(2*node+1, mid+1, hi, i, value)',
    '    tree[node] = tree[2*node] + tree[2*node+1]     # fix on the way back up',
  ],
  parse(s) {
    const [a, q, u] = avParts(s);
    const nums = avNums(a, 8, 'values');
    const qm = String(q || '').match(/^(\d+)\s+(\d+)$/);
    if (!qm) throw new Error('Add a query as “lo hi” after the first “;”');
    const [lo, hi] = [+qm[1], +qm[2]];
    if (lo > hi || hi >= nums.length) throw new Error(`The query range must fit inside 0…${nums.length - 1}`);
    let upd = null;
    if (u) {
      const um = String(u).match(/^(\d+)\s*=\s*(-?\d+)$/);
      if (!um) throw new Error('The update looks like “2 = 7”');
      if (+um[1] >= nums.length) throw new Error(`Index ${um[1]} is outside the array`);
      upd = { i: +um[1], v: +um[2] };
    }
    return { nums, lo, hi, upd };
  },
  run({ nums, lo, hi, upd }) {
    const { F, snap } = avRecorder();
    const n = nums.length, tree = {};
    const ranges = {};
    const build = (node, l, r) => {
      ranges[node] = [l, r];
      if (l === r) { tree[node] = nums[l]; return tree[node]; }
      const mid = (l + r) >> 1;
      tree[node] = build(2 * node, l, mid) + build(2 * node + 1, mid + 1, r);
      return tree[node];
    };
    build(1, 0, n - 1);
    const S = (extra = {}) => ({ nums, n, tree: { ...tree }, ranges, ...extra });
    snap(1, `Built: every node holds the sum of its range, the root holds ${tree[1]}.`, S({ vars: { total: tree[1] } }));
    const visited = [];
    const query = (node, l, r) => {
      visited.push(node);
      if (r < lo || hi < l) { snap(1, `Node [${l}, ${r}] is completely outside the query [${lo}, ${hi}] — return 0.`, S({ cur: node, visited: [...visited], kind: 'out', lo, hi, vars: { node: `[${l},${r}]`, returns: 0 } })); return 0; }
      if (lo <= l && r <= hi) { snap(3, `Node [${l}, ${r}] is fully inside the query — return its stored sum ${tree[node]} without going deeper.`, S({ cur: node, visited: [...visited], kind: 'in', lo, hi, vars: { node: `[${l},${r}]`, returns: tree[node] } })); return tree[node]; }
      snap(5, `Node [${l}, ${r}] only partly overlaps — split and ask both children.`, S({ cur: node, visited: [...visited], kind: 'partial', lo, hi, vars: { node: `[${l},${r}]` } }));
      const mid = (l + r) >> 1;
      return query(2 * node, l, mid) + query(2 * node + 1, mid + 1, r);
    };
    const sum = query(1, 0, n - 1);
    snap(6, `Sum of [${lo}, ${hi}] = <b>${sum}</b> after touching ${visited.length} nodes, not ${hi - lo + 1} array cells.`, S({ visited: [...visited], lo, hi, answer: sum, vars: { answer: sum, nodes_touched: visited.length } }));
    if (upd) {
      const path = [];
      const update = (node, l, r) => {
        path.push(node);
        if (l === r) {
          snap(9, `Leaf [${l}] reached: set it to ${upd.v}.`, S({ cur: node, path: [...path], lo, hi, vars: { index: upd.i, value: upd.v } }));
          tree[node] = upd.v; nums[l] = upd.v;
          return;
        }
        const mid = (l + r) >> 1;
        snap(11, `Index ${upd.i} is in the ${upd.i <= mid ? 'left' : 'right'} half of [${l}, ${r}].`, S({ cur: node, path: [...path], lo, hi, vars: { node: `[${l},${r}]` } }));
        if (upd.i <= mid) update(2 * node, l, mid); else update(2 * node + 1, mid + 1, r);
        tree[node] = tree[2 * node] + tree[2 * node + 1];
        snap(12, `On the way back up: node [${l}, ${r}] becomes ${tree[node]}.`, S({ cur: node, path: [...path], fixed: node, lo, hi, vars: { node: `[${l},${r}]`, sum: tree[node] } }));
      };
      update(1, 0, n - 1);
      snap(12, `One root-to-leaf path repaired — ${path.length} nodes for an update, versus recomputing ${n} values.`, S({ path: [...path], lo, hi, vars: { nodes_updated: path.length } }));
    }
    return F;
  },
  height: (w, last) => 70 + (Math.ceil(Math.log2(last.n)) + 1) * 54 + 70,
  draw(ctx, c, f, P) {
    const levels = {};
    Object.keys(f.ranges).forEach(k => { const d = Math.floor(Math.log2(+k)); (levels[d] ??= []).push(+k); });
    Object.values(levels).forEach(l => l.sort((a, b) => f.ranges[a][0] - f.ranges[b][0]));
    const xy = {};
    Object.entries(levels).forEach(([d, list]) => list.forEach((node, i) => { xy[node] = [24 + (i + .5) * (c.w - 48) / list.length, 40 + +d * 54]; }));
    const vis = new Set(f.visited || []), path = new Set(f.path || []);
    Object.keys(xy).forEach(k => {
      const node = +k, parent = node >> 1;
      if (node > 1 && xy[parent]) D.line(ctx, xy[parent][0], xy[parent][1] + 14, xy[node][0], xy[node][1] - 14, path.has(node) ? P.accent : vis.has(node) ? P.alpha('ok', .6) : P.strong, path.has(node) || vis.has(node) ? 2 : 1.1);
    });
    const wNode = Math.min(56, (c.w - 48) / Math.max(...Object.values(levels).map(l => l.length)) - 6);
    Object.keys(xy).forEach(k => {
      const node = +k, [x, y] = xy[node], [l, r] = f.ranges[node];
      const cur = node === f.cur;
      const kind = cur ? f.kind : null;
      ctx.fillStyle = cur ? P.alpha(kind === 'in' ? 'ok' : kind === 'out' ? 'err' : 'accent', .38)
        : node === f.fixed ? P.alpha('accent', .25) : vis.has(node) ? P.alpha('ok', .12) : P.surface2;
      D.rrect(ctx, x - wNode / 2, y - 15, wNode, 30, 8); ctx.fill();
      ctx.strokeStyle = cur ? (kind === 'in' ? P.ok : kind === 'out' ? P.err : P.accent) : path.has(node) ? P.accent : P.strong;
      ctx.lineWidth = cur || path.has(node) ? 2.2 : 1; ctx.stroke();
      D.text(ctx, String(f.tree[node]), x, y - 3, { color: P.text, size: 12.5, align: 'center', mono: true, weight: 700 });
      D.text(ctx, l === r ? `[${l}]` : `${l}–${r}`, x, y + 9, { color: P.faint, size: 9.5, align: 'center', mono: true });
    });
    const bottom = 40 + Object.keys(levels).length * 54 + 10;
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: bottom, max: 36, style: i => i >= f.lo && i <= f.hi ? { fill: P.alpha('ok', .22), stroke: P.ok } : {} });
    D.text(ctx, `query [${f.lo}, ${f.hi}]${f.answer !== undefined ? ` = ${f.answer}` : ''}`, 20, 20, { color: P.ok, size: 12.5, weight: 700, mono: true });
    D.text(ctx, f.kind === 'in' ? 'fully covered → return the stored sum, stop recursing'
      : f.kind === 'out' ? 'disjoint → return 0, stop recursing'
        : f.kind === 'partial' ? 'partial overlap → split into both children'
          : f.fixed ? 'sums repaired on the way back up the path' : 'green nodes are the ones the query actually read',
    20, g.y + g.size + 26, { color: P.dim, size: 12, weight: 650 });
  },
});

/* =============================================================== 27 · algorithms == */
defineAlgo('27_algorithms', {
  title: 'Fisher–Yates shuffle', short: 'Shuffle',
  idea: 'Walk backwards and swap each position with a random earlier-or-equal one. Every one of the n! orderings is equally likely. The tempting version — swapping with any random index — is <b>biased</b>, and that is the follow-up question interviewers ask.',
  complexity: 'Time O(n) · Space O(1), shuffled in place',
  input: 'A, B, C, D, E ; 42', hint: 'items ; random seed',
  code: [
    'def shuffle(a):',
    '    for i in range(len(a) - 1, 0, -1):',
    '        j = randint(0, i)        # 0..i inclusive, NOT 0..n-1',
    '        a[i], a[j] = a[j], a[i]',
    '    return a',
  ],
  parse(s) {
    const [a, seed] = avParts(s);
    const items = String(a || '').split(/[\s,]+/).filter(Boolean);
    if (items.length < 2) throw new Error('Enter at least two items');
    if (items.length > 8) throw new Error('Use at most 8 items');
    return { items, seed: seed ? avNum(seed, 'a seed') : 42 };
  },
  run({ items, seed }) {
    const { F, snap } = avRecorder();
    const a = [...items], r = rng(Math.abs(Math.round(seed)) || 1);
    const S = (extra = {}) => ({ a: [...a], ...extra });
    snap(0, 'Start with the array in its given order.', S({ vars: { n: a.length } }));
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(r() * (i + 1));
      snap(2, `i = ${i}: pick j uniformly from 0…${i} → <b>${j}</b>. The range shrinks with i — that is what keeps it unbiased.`, S({ i, j, pick: true, vars: { i, j, choices: i + 1 } }));
      [a[i], a[j]] = [a[j], a[i]];
      snap(3, `Swap ${a[i]} and ${a[j]}: position ${i} is now settled.`, S({ i, j, swapped: true, vars: { settled: a.length - i } }));
    }
    snap(4, `Shuffled: ${a.join(', ')}. Each of the ${[...Array(items.length).keys()].reduce((p, k) => p * (k + 1), 1).toLocaleString()} orderings was equally likely.`, S({ done: true, vars: { result: a.join(' ') } }));
    return F;
  },
  height: () => 230,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.a, {
      cw: c.w, y: 60, max: 48,
      style: k => f.swapped && (k === f.i || k === f.j) ? { fill: P.alpha('ok', .35), stroke: P.ok }
        : k === f.j && f.pick ? { fill: P.alpha(P.series[0], .35), stroke: P.series[0] }
          : k === f.i ? { fill: P.alpha('accent', .3), stroke: P.accent }
            : f.i != null && k > f.i ? { fill: P.alpha('ok', .14) } : {},
    });
    if (f.i != null) {
      const x1 = g.left - 4, x2 = g.x(f.i) + g.size / 2 + 4;
      ctx.strokeStyle = P.alpha('accent', .6); ctx.lineWidth = 1.4; ctx.setLineDash([5, 4]);
      D.rrect(ctx, x1, g.y - 10, x2 - x1, g.size + 20, 10); ctx.stroke(); ctx.setLineDash([]);
      D.text(ctx, `j comes from this range (0…${f.i})`, (x1 + x2) / 2, g.y - 20, { color: P.accent, size: 11, align: 'center', weight: 650 });
      AV.ptr(ctx, P, g, f.i, 'i', P.accent);
      if (f.j != null) AV.ptr(ctx, P, g, f.j, 'j', P.series[0], f.i === f.j ? 1 : 0);
      if (f.i < f.a.length - 1) D.text(ctx, 'settled', (g.x(f.i) + g.right) / 2 + g.size / 2, g.y + g.size + 34, { color: P.ok, size: 11, align: 'center', weight: 650 });
    }
    D.text(ctx, f.done ? 'every ordering equally likely' : 'swap only within 0…i — picking from 0…n−1 would bias the result', 20, c.h - 16, { color: f.done ? P.ok : P.dim, size: 12.5, weight: 650 });
  },
});

defineAlgo('27_algorithms', {
  title: 'Weighted random pick: prefix sums + binary search', short: 'Weighted pick',
  idea: 'Turn the weights into a running total, then throw one dart at <code>[0, total)</code> and binary search for the first prefix above it. The width of each band <b>is</b> its probability — the same trick powers weighted load balancing and sampling from a distribution.',
  complexity: 'Build O(n) · each pick O(log n) · Space O(n)',
  input: '1, 3, 2, 4 ; 7', hint: 'weights ; random seed',
  code: [
    'class Solution:',
    '    def __init__(self, w):',
    '        self.prefix = list(accumulate(w))      # running totals',
    '        self.total = self.prefix[-1]',
    '',
    '    def pick_index(self):',
    '        dart = random.random() * self.total',
    '        lo, hi = 0, len(self.prefix) - 1',
    '        while lo < hi:',
    '            mid = (lo + hi) // 2',
    '            if self.prefix[mid] <= dart: lo = mid + 1',
    '            else: hi = mid',
    '        return lo                              # first prefix above the dart',
  ],
  parse(s) {
    const [a, seed] = avParts(s);
    const w = avNums(a, 7, 'weights');
    if (w.some(x => x <= 0 || x % 1)) throw new Error('Weights must be whole numbers above 0');
    return { w, seed: seed ? avNum(seed, 'a seed') : 7 };
  },
  run({ w, seed }) {
    const { F, snap } = avRecorder();
    const prefix = [];
    let acc = 0;
    const S = (extra = {}) => ({ w, prefix: [...prefix], total: acc, ...extra });
    snap(2, 'Build the running totals — each weight becomes a band on a number line.', S({ vars: { n: w.length } }));
    w.forEach((x, i) => { acc += x; prefix.push(acc); snap(2, `Band ${i} covers ${acc - x} up to ${acc} — a width of ${x}.`, S({ build: i, vars: { [`prefix[${i}]`]: acc } })); });
    snap(3, `Total weight ${acc}. Band <i>i</i> has probability weight[i] / ${acc}.`, S({ vars: { total: acc } }));
    const r = rng(Math.abs(Math.round(seed)) || 1);
    const counts = w.map(() => 0);
    for (let t = 0; t < 4; t++) {
      const dart = r() * acc;
      let lo = 0, hi = w.length - 1;
      snap(6, `Throw a dart at <b>${dart.toFixed(2)}</b> on [0, ${acc}).`, S({ dart, lo, hi, counts: [...counts], vars: { dart: +dart.toFixed(2) } }));
      while (lo < hi) {
        const mid = (lo + hi) >> 1;
        const left = prefix[mid] <= dart;
        snap(9, `mid = ${mid}: prefix[${mid}] = ${prefix[mid]} ${left ? '≤' : '>'} ${dart.toFixed(2)} → search the ${left ? 'right' : 'left'} half.`, S({ dart, lo, hi, mid, counts: [...counts], vars: { lo, hi, mid } }));
        if (left) lo = mid + 1; else hi = mid;
      }
      counts[lo]++;
      snap(11, `The dart landed in band <b>${lo}</b> (weight ${w[lo]}).`, S({ dart, lo, hi: lo, hit: lo, counts: [...counts], vars: { picked: lo } }));
    }
    snap(11, `Four picks: ${counts.map((n2, i) => `${i}×${n2}`).join('  ')}. Over many picks the counts converge on the band widths.`, S({ counts: [...counts], done: true, vars: Object.fromEntries(counts.map((n2, i) => [`band ${i}`, n2])) }));
    return F;
  },
  height: () => 280,
  draw(ctx, c, f, P) {
    const pad = 30, W = c.w - pad * 2, total = f.total || 1;
    const X = v => pad + v / total * W;
    const y = 60, h = 44;
    f.w.forEach((wt, i) => {
      if (f.prefix[i] === undefined) return;
      const a = f.prefix[i] - wt, b = f.prefix[i];
      const on = i === f.hit, cand = f.lo != null && i >= f.lo && i <= f.hi;
      ctx.fillStyle = on ? P.alpha('ok', .45) : cand ? P.alpha('accent', .22) : P.alpha(P.series[i % P.series.length], .28);
      D.rrect(ctx, X(a) + 1, y, Math.max(3, X(b) - X(a) - 2), h, 6); ctx.fill();
      ctx.strokeStyle = on ? P.ok : cand ? P.accent : P.strong; ctx.lineWidth = on ? 2.6 : 1.2; ctx.stroke();
      D.text(ctx, String(i), (X(a) + X(b)) / 2, y + 17, { color: P.text, size: 13, align: 'center', mono: true, weight: 700 });
      D.text(ctx, `w=${wt}`, (X(a) + X(b)) / 2, y + 33, { color: P.dim, size: 10.5, align: 'center', mono: true });
      D.text(ctx, String(b), X(b), y + h + 13, { color: P.faint, size: 10, align: 'center', mono: true });
    });
    D.text(ctx, '0', pad, y + h + 13, { color: P.faint, size: 10, align: 'center', mono: true });
    if (f.dart != null) {
      D.line(ctx, X(f.dart), y - 18, X(f.dart), y + h + 4, P.accent, 2.4);
      D.text(ctx, `dart ${f.dart.toFixed(2)}`, X(f.dart), y - 26, { color: P.accent, size: 11.5, align: 'center', weight: 700, mono: true });
    }
    if (f.mid != null) D.text(ctx, `binary search window: ${f.lo}…${f.hi}, testing prefix[${f.mid}] = ${f.prefix[f.mid]}`, 20, y + h + 38, { color: P.accent, size: 12, mono: true });
    if (f.counts) {
      const by = y + h + 66;
      D.text(ctx, 'picks so far', 20, by, { color: P.dim, size: 11.5, weight: 650 });
      const mx = Math.max(1, ...f.counts);
      f.counts.forEach((n2, i) => {
        const bx = 20 + i * 56;
        const bh = 30 * n2 / mx;
        ctx.fillStyle = P.alpha(P.series[i % P.series.length], .5);
        D.rrect(ctx, bx, by + 42 - bh, 40, Math.max(2, bh), 4); ctx.fill();
        D.text(ctx, String(n2), bx + 20, by + 54, { color: P.text, size: 11, align: 'center', mono: true });
        D.text(ctx, `band ${i}`, bx + 20, by + 68, { color: P.faint, size: 9.5, align: 'center' });
      });
    }
    D.text(ctx, f.done ? 'band width = probability' : 'wider band = more likely', c.w - 20, c.h - 14, { color: f.done ? P.ok : P.dim, size: 12, align: 'right', weight: 650 });
  },
});
