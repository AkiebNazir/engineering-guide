/* ============================================================================
   Visualizations for 28_recursion_backtracking ("Recursion Mastery") — group 1
   (math recursion: 001, 003, 004, 005, 016) and group 2 (array/string +
   linked-list recursion: 002, 006, 007, 008, 009, 010). DOM engine throughout.
   Tree-shaped problems (011-021, 025) and the hard backtracking ones
   (022-024) live in dsa-viz29.js.

   New shared helper: a generic call-stack tracer (`mkTracer`/`stackFrameHTML`)
   — every problem here is "recursion drills," so showing the literal call
   stack growing then shrinking, with each frame's argument and (once it
   returns) its return value, is the single most on-topic visual for this
   whole file. Also a small linked-list chain renderer (`llNodesHTML`).
   ========================================================================= */
'use strict';

/* ---------------------------------------------------- shared: call stack -- */
function stackFrameHTML(stack) {
  if (!stack.length) return `<div style="text-align:center; padding:24px; color:var(--text-dim);">Stack empty${stack.done ? '' : ' — no calls yet'}</div>`;
  return `<div style="display:flex; flex-direction:column-reverse; gap:8px; align-items:flex-start; width:100%;">` +
    stack.map((f, i) => `
    <div class="array-node ${i === stack.length - 1 ? 'active-k' : 'merged'}" style="min-width:170px; align-items:flex-start; padding:10px 14px; text-align:left;">
        <div style="font-size:11px; color:var(--text-dim);">${esc(f.label)}</div>
        <div style="font-weight:bold; font-family:var(--mono); font-size:13px;">${esc(f.arg)}</div>
        ${f.ret !== undefined ? `<div style="font-size:12px; color:var(--emerald); margin-top:4px;">→ returns ${esc(String(f.ret))}</div>` : ''}
    </div>`).join('') + `</div>`;
}
/* seq/ctx-bound call-stack tracer: call(label,arg) pushes a frame, ret(v)
   marks the current top frame's return value, pop() removes it, snap(...)
   records one animation frame with the CURRENT stack shape. */
function mkTracer(seq, ctx) {
  const stack = [];
  return {
    stack,
    call(label, arg) { stack.push({ label, arg, ret: undefined }); },
    ret(val) { stack[stack.length - 1].ret = val; },
    pop() { stack.pop(); },
    snap(line, color, title, text, extra = {}) {
      domPushState(seq, { stack: stack.map(f => ({ ...f })), line, color, explTitle: title, explText: text, ...extra }, ctx);
    },
  };
}
function stackPanelHTML(s, heading = 'Call Stack') {
  return `
      <div class="glass-panel arrays-container">
          <div class="panel-heading">${heading}</div>
          <div style="min-height:170px; display:flex; align-items:flex-end; padding:10px 16px;">
              ${stackFrameHTML(s.stack)}
          </div>
      </div>`;
}
/* ---------------------------------------------------- shared: linked list - */
function llNodesHTML(vals, { activeIdx = [], labels = {}, dim = [] } = {}) {
  if (!vals.length) return `<div style="text-align:center; padding:20px; color:var(--text-dim);">(empty list)</div>`;
  return vals.map((v, i) => `
    <div class="array-node ${activeIdx.includes(i) ? 'active-k' : dim.includes(i) ? 'merged' : ''}" style="min-width:50px;">
        ${labels[i] ? `<div class="pointer" style="top:-25px; color:var(--accent);">${esc(labels[i])}</div>` : ''}
        ${v}
        ${i < vals.length - 1 ? `<div class="node-index" style="position:absolute; right:-22px; font-size:20px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">→</div>` : `<div class="node-index" style="position:absolute; right:-30px; font-size:12px; color:var(--text-dim); background:transparent; border:none; box-shadow:none;">null</div>`}
    </div>`).join('');
}
function llPanelHTML(title, vals, opts) {
  return `
      <div class="glass-panel arrays-container">
          <div class="panel-heading">${title}</div>
          <div class="array-track" style="padding-top:20px; padding-right:36px;">${llNodesHTML(vals, opts)}</div>
      </div>`;
}

/* =============================================== 001 · Number of Steps ==== */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Number of Steps to Reduce a Number to Zero', short: 'Number of Steps',
  idea: 'Recurse following the actual rule: halve if even, subtract one if odd, count one step per call. The call stack depth is exactly the answer.',
  complexity: 'Time O(log num) · Space O(log num) recursion depth',
  input: '14', hint: 'a non-negative integer, kept small so the call stack stays readable',
  code: [
    'def numberOfSteps(num):',
    '    if num == 0:',
    '        return 0',
    '    if num % 2 == 0:',
    '        return 1 + numberOfSteps(num // 2)',
    '    return 1 + numberOfSteps(num - 1)',
  ],
  parse(s) {
    const num = parseInt(String(s || '').trim(), 10);
    if (!Number.isFinite(num) || num < 0) throw new Error('Enter a non-negative integer');
    if (num > 100) throw new Error('Keep num <= 100 so the call stack stays readable');
    return { num };
  },
  buildStates({ num }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const go = n => {
      T.call('numberOfSteps', n);
      T.snap(1, 'blue', `Call numberOfSteps(${n})`, `Push a new frame for numberOfSteps(${n}).`);
      let result;
      if (n === 0) {
        result = 0;
        T.snap(3, 'emerald', 'Base case', 'num is 0 — return 0.');
      } else if (n % 2 === 0) {
        T.snap(4, 'amber', 'Even', `${n} is even — recurse on ${n} // 2 = ${Math.floor(n / 2)}.`);
        result = 1 + go(Math.floor(n / 2));
      } else {
        T.snap(5, 'amber', 'Odd', `${n} is odd — recurse on ${n} - 1 = ${n - 1}.`);
        result = 1 + go(n - 1);
      }
      T.ret(result);
      T.snap(n === 0 ? 3 : (n % 2 === 0 ? 4 : 5), 'emerald', `Return ${result}`, `numberOfSteps(${n}) returns ${result}.`);
      T.pop();
      return result;
    };
    const total = go(num);
    domPushState(seq, { stack: [], line: 6, color: 'emerald', explTitle: 'Done', explText: `All frames returned. numberOfSteps(${num}) = ${total}.` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
          ${stackPanelHTML(s)}
      </div>`;
  }
});

/* =================================================== 003 · Add Digits ===== */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Add Digits', short: 'Add Digits',
  idea: 'Two-layer recursion: the outer addDigits re-applies itself to the result of an inner _digit_sum recursion, until a single digit remains. Both share one call stack here.',
  complexity: 'Time O(log num) outer x O(log num) inner · Space O(log num)',
  input: '493193', hint: 'a non-negative integer',
  code: [
    'def addDigits(num):',
    '    if num < 10:',
    '        return num',
    '    return addDigits(digit_sum(num))',
    '',
    'def digit_sum(n):',
    '    if n < 10:',
    '        return n',
    '    return n % 10 + digit_sum(n // 10)',
  ],
  parse(s) {
    const num = parseInt(String(s || '').trim(), 10);
    if (!Number.isFinite(num) || num < 0) throw new Error('Enter a non-negative integer');
    if (num > 999999) throw new Error('Keep num under 1,000,000 so the call stack stays readable');
    return { num };
  },
  buildStates({ num }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const digitSum = n => {
      T.call('digit_sum', n);
      T.snap(6, 'blue', `Call digit_sum(${n})`, `Push a frame for digit_sum(${n}).`);
      let result;
      if (n < 10) {
        result = n;
        T.snap(7, 'emerald', 'Base case', `${n} is a single digit — return it.`);
      } else {
        T.snap(8, 'amber', 'Peel a digit', `${n} % 10 = ${n % 10}, then recurse on ${n} // 10 = ${Math.floor(n / 10)}.`);
        result = (n % 10) + digitSum(Math.floor(n / 10));
      }
      T.ret(result);
      T.snap(n < 10 ? 7 : 8, 'emerald', `Return ${result}`, `digit_sum(${n}) returns ${result}.`);
      T.pop();
      return result;
    };
    const addDigits = n => {
      T.call('addDigits', n);
      T.snap(1, 'blue', `Call addDigits(${n})`, `Push a frame for addDigits(${n}).`);
      let result;
      if (n < 10) {
        result = n;
        T.snap(2, 'emerald', 'Base case', `${n} is already a single digit — return it.`);
      } else {
        const ds = digitSum(n);
        T.snap(3, 'amber', 'Recurse', `digit_sum(${n}) = ${ds}. Recurse: addDigits(${ds}).`);
        result = addDigits(ds);
      }
      T.ret(result);
      T.snap(n < 10 ? 2 : 3, 'emerald', `Return ${result}`, `addDigits(${n}) returns ${result}.`);
      T.pop();
      return result;
    };
    const total = addDigits(num);
    domPushState(seq, { stack: [], line: 4, color: 'emerald', explTitle: 'Done', explText: `All frames returned. addDigits(${num}) = ${total} — the digital root.` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
          ${stackPanelHTML(s)}
      </div>`;
  }
});

/* =================================================== 004 · Power of Two === */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Power of Two', short: 'Power of Two',
  idea: 'Three base cases (n<=0 false, n==1 true, n odd false), otherwise recurse on n/2. Every recursive call halves n, so a power of two reaches 1 in exactly log2(n) calls.',
  complexity: 'Time O(log n) · Space O(log n) recursion depth',
  input: '32', hint: 'an integer (can be non-positive)',
  code: [
    'def isPowerOfTwo(n):',
    '    if n <= 0:',
    '        return False',
    '    if n == 1:',
    '        return True',
    '    if n % 2 != 0:',
    '        return False',
    '    return isPowerOfTwo(n // 2)',
  ],
  parse(s) {
    const n = parseInt(String(s || '').trim(), 10);
    if (!Number.isFinite(n)) throw new Error('Enter an integer');
    if (Math.abs(n) > 1 << 20) throw new Error('Keep |n| reasonably small so the call stack stays readable');
    return { n };
  },
  buildStates({ n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const go = k => {
      T.call('isPowerOfTwo', k);
      T.snap(1, 'blue', `Call isPowerOfTwo(${k})`, `Push a frame for isPowerOfTwo(${k}).`);
      let result;
      if (k <= 0) { result = false; T.snap(3, 'rose', 'n <= 0', `${k} <= 0 — return False.`); }
      else if (k === 1) { result = true; T.snap(5, 'emerald', 'n == 1', `${k} == 1 — return True.`); }
      else if (k % 2 !== 0) { result = false; T.snap(7, 'rose', 'n is odd', `${k} is odd (and not 1) — cannot be a power of two. Return False.`); }
      else {
        T.snap(8, 'amber', 'Halve', `${k} is even — recurse on ${k} // 2 = ${k / 2}.`);
        result = go(k / 2);
      }
      T.ret(result);
      T.pop();
      return result;
    };
    const total = go(n);
    domPushState(seq, { stack: [], line: 8, color: total ? 'emerald' : 'rose', explTitle: 'Done', explText: `All frames returned. isPowerOfTwo(${n}) = ${total}.` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    container.innerHTML = `<div style="display:flex; flex-direction:column; gap:15px; width:100%;">${stackPanelHTML(s)}</div>`;
  }
});

/* ================================================= 005 · Power of Three === */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Power of Three', short: 'Power of Three',
  idea: 'Same shape as Power of Two but dividing by 3 each time: n<=0 false, n==1 true, n%3!=0 false, else recurse on n/3.',
  complexity: 'Time O(log₃ n) · Space O(log₃ n) recursion depth',
  input: '81', hint: 'an integer (can be non-positive)',
  code: [
    'def isPowerOfThree(n):',
    '    if n <= 0:',
    '        return False',
    '    if n == 1:',
    '        return True',
    '    if n % 3 != 0:',
    '        return False',
    '    return isPowerOfThree(n // 3)',
  ],
  parse(s) {
    const n = parseInt(String(s || '').trim(), 10);
    if (!Number.isFinite(n)) throw new Error('Enter an integer');
    if (Math.abs(n) > 3 ** 12) throw new Error('Keep |n| reasonably small so the call stack stays readable');
    return { n };
  },
  buildStates({ n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const go = k => {
      T.call('isPowerOfThree', k);
      T.snap(1, 'blue', `Call isPowerOfThree(${k})`, `Push a frame for isPowerOfThree(${k}).`);
      let result;
      if (k <= 0) { result = false; T.snap(3, 'rose', 'n <= 0', `${k} <= 0 — return False.`); }
      else if (k === 1) { result = true; T.snap(5, 'emerald', 'n == 1', `${k} == 1 — return True.`); }
      else if (k % 3 !== 0) { result = false; T.snap(7, 'rose', 'n % 3 != 0', `${k} is not divisible by 3 — return False.`); }
      else {
        T.snap(8, 'amber', 'Divide by 3', `${k} is divisible by 3 — recurse on ${k} // 3 = ${k / 3}.`);
        result = go(k / 3);
      }
      T.ret(result);
      T.pop();
      return result;
    };
    const total = go(n);
    domPushState(seq, { stack: [], line: 8, color: total ? 'emerald' : 'rose', explTitle: 'Done', explText: `All frames returned. isPowerOfThree(${n}) = ${total}.` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    container.innerHTML = `<div style="display:flex; flex-direction:column; gap:15px; width:100%;">${stackPanelHTML(s)}</div>`;
  }
});

/* ================================================ 016 · Super Pow ========= */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Super Pow', short: 'Super Pow',
  idea: 'Peel the last digit of b each call: superPow(a,b) = pow(superPow(a,b[:-1]), 10) * pow(a, last_digit), all mod 1337. The recursion bottoms out on an empty digit list (returns 1).',
  complexity: 'Time O(len(b)) · Space O(len(b)) recursion depth',
  input: '2;1,0', hint: 'a ; digits of b (comma-separated, most significant first)',
  code: [
    'def superPow(a, b):',
    '    if not b:',
    '        return 1',
    '    last = b[-1]',
    '    rest = superPow(a, b[:-1])',
    '    return (pow(rest, 10, MOD)',
    '            * pow(a, last, MOD)) % MOD',
  ],
  parse(s) {
    const [aStr, bStr] = String(s || '').split(';');
    const a = parseInt((aStr || '').trim(), 10);
    if (!Number.isFinite(a) || a < 1 || a > 1000) throw new Error('a must be an integer 1-1000');
    const b = (bStr || '').split(',').map(x => parseInt(x.trim(), 10));
    if (!b.length || b.some(d => !Number.isFinite(d) || d < 0 || d > 9)) throw new Error('b must be comma-separated single digits, e.g. 1,0');
    if (b.length > 6) throw new Error('Use at most 6 digits for b so the call stack stays readable');
    return { a, b };
  },
  buildStates({ a, b }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const MOD = 1337;
    const modpow = (base, exp, mod) => { let r = 1; base %= mod; while (exp > 0) { if (exp & 1) r = (r * base) % mod; base = (base * base) % mod; exp >>= 1; } return r; };
    const go = digits => {
      T.call('superPow', `[${digits.join(',')}]`);
      T.snap(1, 'blue', `Call superPow(a, [${digits.join(',')}])`, `Push a frame for b = [${digits.join(',')}].`);
      let result;
      if (!digits.length) {
        result = 1;
        T.snap(2, 'emerald', 'Base case', 'b is empty — return 1.');
      } else {
        const last = digits[digits.length - 1], rest = digits.slice(0, -1);
        T.snap(4, 'amber', 'Peel last digit', `Last digit is ${last}. Recurse on the remaining digits [${rest.join(',')}].`);
        const restVal = go(rest);
        result = (modpow(restVal, 10, MOD) * modpow(a, last, MOD)) % MOD;
        T.snap(6, 'amber', 'Combine', `pow(${restVal},10,${MOD}) * pow(${a},${last},${MOD}) mod ${MOD} = ${result}.`);
      }
      T.ret(result);
      T.pop();
      return result;
    };
    const total = go(b);
    domPushState(seq, { stack: [], line: 7, color: 'emerald', explTitle: 'Done', explText: `All frames returned. superPow(${a}, [${b.join(',')}]) = ${total}.` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    container.innerHTML = `<div style="display:flex; flex-direction:column; gap:15px; width:100%;">${stackPanelHTML(s, 'Call Stack (b, most-significant digit peeled last)')}</div>`;
  }
});

/* =================================================== 002 · Reverse String = */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Reverse String', short: 'Reverse String',
  idea: 'Recursive two-pointer: swap s[lo] and s[hi], then recurse on the inner range (lo+1, hi-1). Base case: lo >= hi.',
  complexity: 'Time O(n) · Space O(n) recursion depth',
  input: 'h,e,l,l,o', hint: 'comma-separated characters',
  code: [
    'def reverseString(s, lo, hi):',
    '    if lo >= hi:',
    '        return',
    '    s[lo], s[hi] = s[hi], s[lo]',
    '    reverseString(s, lo + 1, hi - 1)',
  ],
  parse(s) {
    const chars = String(s || '').split(',').map(x => x.trim()).filter(x => x.length);
    if (!chars.length) throw new Error('Enter comma-separated characters, e.g. h,e,l,l,o');
    if (chars.length > 10) throw new Error('Use at most 10 characters for visualization');
    return { chars };
  },
  buildStates({ chars }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const arr = [...chars];
    const T = mkTracer(seq, ctx);
    const go = (lo, hi) => {
      T.call('reverseString', `lo=${lo}, hi=${hi}`);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), arr: [...arr], lo, hi, line: 1, color: 'blue', explTitle: `Call reverseString(lo=${lo}, hi=${hi})`, explText: `Consider the range [${lo}, ${hi}].` }, ctx);
      if (lo >= hi) {
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), arr: [...arr], lo, hi, line: 2, color: 'emerald', explTitle: 'Base case', explText: `lo (${lo}) >= hi (${hi}) — the range has 0 or 1 elements. Return.` }, ctx);
      } else {
        [arr[lo], arr[hi]] = [arr[hi], arr[lo]];
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), arr: [...arr], lo, hi, line: 4, color: 'amber', explTitle: 'Swap', explText: `Swap s[${lo}]='${arr[hi]}' and s[${hi}]='${arr[lo]}'.` }, ctx);
        go(lo + 1, hi - 1);
      }
      T.pop();
    };
    go(0, arr.length - 1);
    domPushState(seq, { stack: [], arr: [...arr], lo: -1, hi: -1, line: 5, color: 'emerald', explTitle: 'Done', explText: `All frames returned. Reversed: [${arr.join(', ')}].` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const getArrayHTML = (arr, lo, hi) => arr.map((v, idx) => {
      const isLo = idx === lo, isHi = idx === hi, cls = (isLo || isHi) ? 'active-k' : (lo !== -1 && idx > lo && idx < hi) ? 'merged' : '';
      return `
            <div class="array-node ${cls}">
                ${isLo ? '<div class="pointer" style="color:#34d399">↓ lo</div>' : ''}
                ${isHi ? '<div class="pointer" style="color:#f59e0b">↓ hi</div>' : ''}
                ${v}
                <div class="node-index">${idx}</div>
    </div>`;
    }).join('');
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">s</div>
                  <div class="array-track">${getArrayHTML(s.arr, s.lo, s.hi)}</div>
              </div>
          ${stackPanelHTML(s, 'Call Stack (recursion depth)')}
      </div>`;
  }
});

/* ============================================ 006 · Pascal's Triangle II == */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: "Pascal's Triangle II", short: "Pascal's Triangle II",
  idea: 'Recurse down to row 0 first, then build each row up from the previous one as the calls return — row[i] = prev[i-1] + prev[i]. The triangle fills in from the top as the stack unwinds.',
  complexity: 'Time O(rowIndex²) · Space O(rowIndex) recursion depth',
  input: '4', hint: 'rowIndex, 0-indexed (kept small for visualization)',
  code: [
    'def getRow(rowIndex):',
    '    if rowIndex == 0:',
    '        return [1]',
    '    prev = getRow(rowIndex - 1)',
    '    row = [1] * (rowIndex + 1)',
    '    for i in range(1, rowIndex):',
    '        row[i] = prev[i-1] + prev[i]',
    '    return row',
  ],
  parse(s) {
    const rowIndex = parseInt(String(s || '').trim(), 10);
    if (!Number.isFinite(rowIndex) || rowIndex < 0) throw new Error('Enter a non-negative integer');
    if (rowIndex > 7) throw new Error('Keep rowIndex <= 7 so the triangle stays readable');
    return { rowIndex };
  },
  buildStates({ rowIndex }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const triangle = [];
    const go = k => {
      T.call('getRow', k);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), triangle: triangle.map(r => [...r]), line: 1, color: 'blue', explTitle: `Call getRow(${k})`, explText: `Push a frame for row ${k}.` }, ctx);
      let row;
      if (k === 0) {
        row = [1];
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), triangle: triangle.map(r => [...r]), line: 2, color: 'emerald', explTitle: 'Base case', explText: 'rowIndex is 0 — return [1].' }, ctx);
      } else {
        const prev = go(k - 1);
        row = new Array(k + 1).fill(1);
        for (let i = 1; i < k; i++) row[i] = prev[i - 1] + prev[i];
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), triangle: triangle.map(r => [...r]), line: 5, color: 'amber', explTitle: `Build row ${k}`, explText: `Combine adjacent pairs from row ${k - 1} = [${prev.join(', ')}] to get row ${k} = [${row.join(', ')}].` }, ctx);
      }
      triangle[k] = row;
      T.ret(`[${row.join(',')}]`);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), triangle: triangle.map(r => [...r]), line: 7, color: 'emerald', explTitle: `Return row ${k}`, explText: `getRow(${k}) returns [${row.join(', ')}].` }, ctx);
      T.pop();
      return row;
    };
    const finalRow = go(rowIndex);
    domPushState(seq, { stack: [], triangle: triangle.map(r => [...r]), line: 7, color: 'emerald', explTitle: 'Done', explText: `All frames returned. Row ${rowIndex} = [${finalRow.join(', ')}].` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const triHTML = s.triangle.map((row, r) => `
        <div style="display:flex; justify-content:center; gap:8px; margin-bottom:6px;">
            ${row.map(v => `<div class="array-node" style="min-width:36px; ${r === s.triangle.length - 1 ? 'border-color:var(--emerald); color:var(--emerald);' : ''}">${v}</div>`).join('')}
        </div>`).join('');
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Triangle built so far</div>
                  <div style="padding:10px; min-height:60px;">${s.triangle.length ? triHTML : '<div style="text-align:center;color:var(--text-dim);">(nothing yet — still recursing down)</div>'}</div>
              </div>
          ${stackPanelHTML(s)}
      </div>`;
  }
});

/* ============================================= 007 · Swap Nodes in Pairs == */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Swap Nodes in Pairs', short: 'Swap Nodes in Pairs',
  idea: 'Recurse to the end of the list FIRST (swap the rest), then wire the current pair around that already-swapped rest: first.next = swapPairs(second.next); second.next = first; return second.',
  complexity: 'Time O(n) · Space O(n) recursion depth',
  input: '1,2,3,4', hint: 'comma-separated node values',
  code: [
    'def swapPairs(head):',
    '    if not head or not head.next:',
    '        return head',
    '    first, second = head, head.next',
    '    first.next = swapPairs(second.next)',
    '    second.next = first',
    '    return second',
  ],
  parse(s) {
    const vals = String(s || '').split(',').map(x => parseInt(x.trim(), 10));
    if (!vals.length || vals.some(v => !Number.isFinite(v))) throw new Error('Enter comma-separated integers, e.g. 1,2,3,4');
    if (vals.length > 8) throw new Error('Use at most 8 nodes for visualization');
    return { vals };
  },
  buildStates({ vals }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const swapped = [];
    const go = (list) => {
      T.call('swapPairs', `head=${list.length ? list[0] : 'None'}`);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), remaining: [...list], swapped: [...swapped], line: 1, color: 'blue', explTitle: `Call swapPairs(head=${list.length ? list[0] : 'None'})`, explText: `Remaining unswapped sub-list: [${list.join(', ')}].` }, ctx);
      if (list.length < 2) {
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), remaining: [...list], swapped: [...swapped], line: 2, color: 'emerald', explTitle: 'Base case', explText: 'Fewer than 2 nodes remain — return head as-is (nothing to swap).' }, ctx);
      } else {
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), remaining: [...list], swapped: [...swapped], line: 4, color: 'amber', explTitle: 'Take a pair', explText: `first=${list[0]}, second=${list[1]}. Recurse on the rest: [${list.slice(2).join(', ')}].` }, ctx);
        go(list.slice(2));
        swapped.unshift(list[0]); swapped.unshift(list[1]);
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), remaining: list.slice(2), swapped: [...swapped], line: 6, color: 'emerald', explTitle: 'Wire this pair', explText: `second (${list[1]}) now points to first (${list[0]}), and first points into the already-swapped rest.` }, ctx);
      }
      T.pop();
    };
    go(vals);
    domPushState(seq, { stack: [], remaining: [], swapped: [...swapped], line: 7, color: 'emerald', explTitle: 'Done', explText: `All frames returned. Result: [${swapped.join(', ')}].` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
          ${llPanelHTML('Result so far (swapped) → remaining (untouched)', [...s.swapped, ...s.remaining], { dim: s.remaining.map((_, i) => s.swapped.length + i) })}
          ${stackPanelHTML(s)}
      </div>`;
  }
});

/* ========================================= 008 · Reverse Linked List II === */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Reverse Linked List II', short: 'Reverse Linked List II',
  idea: 'Two recursive helpers stacked: _reverse_between walks down to position `left`, then _reverse_first_n reverses the next `n` nodes in place (capturing the successor once) while the outer recursion rewires the head before it.',
  complexity: 'Time O(n) · Space O(right) recursion depth',
  input: '1,2,3,4,5;2;4', hint: 'values ; left ; right (1-indexed)',
  code: [
    'def reverseBetween(head, left, right):',
    '    if left == 1:',
    '        return reverse_first_n(head, right)',
    '    head.next = reverseBetween(',
    '        head.next, left - 1, right - 1)',
    '    return head',
    '',
    'def reverse_first_n(head, n):',
    '    if n == 1:',
    '        successor = head.next; return head',
    '    rest = reverse_first_n(head.next, n - 1)',
    '    head.next.next = head',
    '    head.next = successor',
    '    return rest',
  ],
  parse(s) {
    const [valsStr, leftStr, rightStr] = String(s || '').split(';');
    const vals = (valsStr || '').split(',').map(x => parseInt(x.trim(), 10));
    if (!vals.length || vals.some(v => !Number.isFinite(v))) throw new Error('Enter comma-separated integers for the list');
    if (vals.length > 8) throw new Error('Use at most 8 nodes for visualization');
    const left = parseInt((leftStr || '').trim(), 10), right = parseInt((rightStr || '').trim(), 10);
    if (!Number.isFinite(left) || !Number.isFinite(right) || left < 1 || right > vals.length || left > right) throw new Error('Need 1 <= left <= right <= list length');
    return { vals, left, right };
  },
  buildStates({ vals, left, right }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    let successor = null;
    const reverseFirstN = (list, n) => {
      T.call('reverse_first_n', `head=${list[0]}, n=${n}`);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), list: [...list], windowLo: 0, windowHi: n - 1, line: 8, color: 'blue', explTitle: `Call reverse_first_n(head=${list[0]}, n=${n})`, explText: `Reverse the first ${n} of [${list.join(', ')}] in place.` }, ctx);
      let result;
      if (n === 1) {
        successor = list.slice(1);
        result = [list[0]];
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), list: [...list], windowLo: 0, windowHi: 0, line: 9, color: 'emerald', explTitle: 'Base case', explText: `n == 1 — capture the successor (node after this window: ${successor.length ? successor[0] : 'None'}), return this single node.` }, ctx);
      } else {
        const rest = reverseFirstN(list.slice(1), n - 1);
        result = [...rest, list[0]];
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), list: [...result, ...successor], windowLo: 0, windowHi: n - 1, line: 12, color: 'amber', explTitle: 'Relink', explText: `Point the already-reversed rest's tail back at ${list[0]}, then point ${list[0]} at the captured successor.` }, ctx);
      }
      T.ret(`[${result.join(',')}]`);
      T.pop();
      return result;
    };
    const reverseBetween = (list, l, r) => {
      T.call('reverseBetween', `head=${list[0]}, left=${l}, right=${r}`);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), list: [...list], windowLo: l - 1, windowHi: r - 1, line: 1, color: 'blue', explTitle: `Call reverseBetween(head=${list[0]}, left=${l}, right=${r})`, explText: `Walk toward position left=${l}.` }, ctx);
      let result;
      if (l === 1) {
        const rev = reverseFirstN(list, r);
        result = [...rev, ...successor];
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), list: [...result], windowLo: 0, windowHi: r - 1, line: 2, color: 'emerald', explTitle: 'Reversed window reached', explText: `left == 1 — the window to reverse starts here. Return reverse_first_n's result.` }, ctx);
      } else {
        const rest = reverseBetween(list.slice(1), l - 1, r - 1);
        result = [list[0], ...rest];
      }
      T.ret(`[${result.join(',')}]`);
      T.pop();
      return result;
    };
    const final = reverseBetween(vals, left, right);
    domPushState(seq, { stack: [], list: final, windowLo: -1, windowHi: -1, line: 6, color: 'emerald', explTitle: 'Done', explText: `All frames returned. Result: [${final.join(', ')}].` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
          ${llPanelHTML('List', s.list, { activeIdx: s.windowLo === -1 ? [] : Array.from({ length: Math.max(0, s.windowHi - s.windowLo + 1) }, (_, i) => s.windowLo + i) })}
          ${stackPanelHTML(s)}
      </div>`;
  }
});

/* ===================================== 009 · Flatten Nested List Iterator = */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Flatten Nested List Iterator', short: 'Flatten Nested List Iterator',
  idea: 'Eager approach: recursively flatten the whole nested structure into a plain list once, in the constructor. After that, next()/hasNext() are just an O(1) pointer walk over that flat list.',
  complexity: 'Build O(n) time/space · next/hasNext O(1) each',
  input: '[1,1],2,[1,1] ; next,next,next,hasNext,next,hasNext', hint: 'nested list (brackets for nesting) ; operations',
  code: [
    'def __init__(self, nestedList):',
    '    self._data = self._flatten(nestedList)',
    '    self._index = 0',
    '',
    'def _flatten(self, lst):',
    '    result = []',
    '    for item in lst:',
    '        if item.isInteger():',
    '            result.append(item.getInteger())',
    '        else:',
    '            result += self._flatten(item.getList())',
    '    return result',
    '',
    'def next(self):',
    '    v = self._data[self._index]; self._index += 1; return v',
    '',
    'def hasNext(self):',
    '    return self._index < len(self._data)',
  ],
  parse(s) {
    const [structStr, opsStr] = String(s || '').split(';');
    const src = (structStr || '').trim();
    if (!src) throw new Error('Enter a nested list, e.g. [1,1],2,[1,1]');
    let i = 0;
    function parseList() {
      const items = [];
      while (i < src.length && src[i] !== ']') {
        if (src[i] === ',') { i++; continue; }
        if (src[i] === '[') { i++; items.push({ list: parseList() }); if (src[i] === ']') i++; }
        else {
          let j = i; while (j < src.length && /[-\d]/.test(src[j])) j++;
          if (j === i) throw new Error(`Unexpected character "${src[i]}" in nested list`);
          items.push({ int: parseInt(src.slice(i, j), 10) }); i = j;
        }
      }
      return items;
    }
    const top = parseList();
    const ops = (opsStr || 'next,hasNext').split(',').map(x => x.trim()).filter(Boolean);
    if (ops.length > 12) throw new Error('Use at most 12 operations');
    return { top, ops };
  },
  buildStates({ top, ops }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const fmt = list => list.map(it => it.list ? `[${fmt(it.list)}]` : it.int).join(',');
    const flatten = list => {
      T.call('_flatten', `[${fmt(list)}]`);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), phase: 'build', data: [], line: 5, color: 'blue', explTitle: `Call _flatten([${fmt(list)}])`, explText: 'Walk each item: integers append directly, nested lists recurse.' }, ctx);
      let result = [];
      for (const item of list) {
        if (item.int !== undefined) {
          result.push(item.int);
          domPushState(seq, { stack: T.stack.map(f => ({ ...f })), phase: 'build', data: [...result], line: 8, color: 'emerald', explTitle: 'Integer', explText: `${item.int} is an integer — append it.` }, ctx);
        } else {
          domPushState(seq, { stack: T.stack.map(f => ({ ...f })), phase: 'build', data: [...result], line: 10, color: 'amber', explTitle: 'Nested list', explText: `[${fmt(item.list)}] is a list — recurse into it.` }, ctx);
          result = result.concat(flatten(item.list));
        }
      }
      T.ret(`[${result.join(',')}]`);
      T.pop();
      return result;
    };
    const flat = flatten(top);
    domPushState(seq, { stack: [], phase: 'build', data: flat, line: 11, color: 'emerald', explTitle: 'Flattened', explText: `Construction done: _data = [${flat.join(', ')}].` }, ctx);
    let idx = 0;
    for (const op of ops) {
      if (op === 'next') {
        const v = flat[idx]; idx++;
        domPushState(seq, { stack: [], phase: 'iterate', data: flat, index: idx - 1, op: `next() → ${v}`, line: 14, color: 'blue', explTitle: 'next()', explText: `Return _data[${idx - 1}] = ${v}, then advance the index to ${idx}.` }, ctx);
      } else {
        const has = idx < flat.length;
        domPushState(seq, { stack: [], phase: 'iterate', data: flat, index: idx, op: `hasNext() → ${has}`, line: 17, color: has ? 'emerald' : 'rose', explTitle: 'hasNext()', explText: `index (${idx}) ${has ? '<' : '>='} data.length (${flat.length}) — return ${has}.` }, ctx);
      }
    }
    return seq;
  },
  renderDOM(container, s) {
    const arrHTML = s.data.map((v, i) => `
            <div class="array-node ${i === s.index ? 'active-k' : i < s.index ? 'merged' : ''}">
                ${i === s.index && s.phase === 'iterate' ? '<div class="pointer" style="color:#34d399">↓ index</div>' : ''}
                ${v}
                <div class="node-index">${i}</div>
    </div>`).join('');
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">${s.phase === 'build' ? 'Flattening... (_data so far)' : `_data — ${s.op || ''}`}</div>
                  <div class="array-track">${s.data.length ? arrHTML : '<div style="color:var(--text-dim);">(empty)</div>'}</div>
              </div>
          ${s.phase === 'build' ? stackPanelHTML(s) : ''}
      </div>`;
  }
});

/* ============================================= 010 · Add Two Numbers II === */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Add Two Numbers II', short: 'Add Two Numbers II',
  idea: 'Pad the shorter list with leading zeros, then recurse to the very end of both lists — the base case returns (carry=0, node=None) — and build the result digit-by-digit as the calls return, carrying into the caller.',
  complexity: 'Time O(max(m,n)) · Space O(max(m,n)) recursion depth',
  input: '7,2,4,3;5,6,4', hint: 'l1 digits ; l2 digits (most significant first)',
  code: [
    'def add_same_length(l1, l2):',
    '    if l1 is None:',
    '        return 0, None',
    '    carry, rest = add_same_length(',
    '        l1.next, l2.next)',
    '    total = l1.val + l2.val + carry',
    '    node = ListNode(total % 10, rest)',
    '    return total // 10, node',
  ],
  parse(s) {
    const [s1, s2] = String(s || '').split(';');
    const l1 = (s1 || '').split(',').map(x => parseInt(x.trim(), 10));
    const l2 = (s2 || '').split(',').map(x => parseInt(x.trim(), 10));
    if (!l1.length || !l2.length || l1.some(v => !Number.isFinite(v)) || l2.some(v => !Number.isFinite(v))) throw new Error('Enter two comma-separated digit lists, e.g. 7,2,4,3;5,6,4');
    if (Math.max(l1.length, l2.length) > 7) throw new Error('Use at most 7 digits per list for visualization');
    return { l1, l2 };
  },
  buildStates({ l1: rawL1, l2: rawL2 }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const pad = (a, n) => Array(n - a.length).fill(0).concat(a);
    const n = Math.max(rawL1.length, rawL2.length);
    const l1 = pad(rawL1, n), l2 = pad(rawL2, n);
    if (rawL1.length !== rawL2.length) domPushState(seq, { stack: [], l1, l2, result: [], line: 0, color: 'blue', explTitle: 'Pad to equal length', explText: `Lengths differ — pad the shorter list with leading zeros: l1=[${l1.join(',')}], l2=[${l2.join(',')}].` }, ctx);
    const T = mkTracer(seq, ctx);
    const go = i => {
      T.call('add_same_length', i < n ? `l1[${i}]=${l1[i]}, l2[${i}]=${l2[i]}` : 'None, None');
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), l1, l2, cur: i, result: [], line: 1, color: 'blue', explTitle: `Call add_same_length at position ${i}`, explText: i < n ? `Recurse deeper before adding anything at this position.` : 'Reached the end of both lists.' }, ctx);
      let carry, rest;
      if (i === n) {
        carry = 0; rest = [];
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), l1, l2, cur: i, result: [], line: 2, color: 'emerald', explTitle: 'Base case', explText: 'Both lists exhausted — return (carry=0, node=None).' }, ctx);
      } else {
        const inner = go(i + 1);
        carry = inner.carry; rest = inner.rest;
        const total = l1[i] + l2[i] + carry;
        const digit = total % 10;
        rest = [digit, ...rest];
        carry = Math.floor(total / 10);
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), l1, l2, cur: i, result: [...rest], line: 6, color: 'amber', explTitle: `Add at position ${i}`, explText: `${l1[i]} + ${l2[i]} + carry(${inner.carry}) = ${total} → digit ${digit}, new carry ${carry}.` }, ctx);
      }
      T.ret(`carry=${carry}`);
      T.pop();
      return { carry, rest };
    };
    const { carry, rest } = go(0);
    const final = carry ? [carry, ...rest] : rest;
    domPushState(seq, { stack: [], l1, l2, cur: -1, result: final, line: 8, color: 'emerald', explTitle: 'Done', explText: `All frames returned. Result: [${final.join(', ')}]${carry ? ' (leading carry became a new digit)' : ''}.` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const numHTML = (label, arr, cur) => `
      <div class="glass-panel arrays-container">
          <div class="panel-heading">${label}</div>
          <div class="array-track">${arr.map((v, i) => `<div class="array-node ${i === cur ? 'active-k' : ''}">${v}<div class="node-index">${i}</div></div>`).join('')}</div>
      </div>`;
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:12px; width:100%;">
          ${numHTML('l1', s.l1, s.cur)}
          ${numHTML('l2', s.l2, s.cur)}
          <div class="glass-panel arrays-container">
              <div class="panel-heading">Result being built (from the tail forward)</div>
              <div class="array-track">${s.result.length ? s.result.map(v => `<div class="array-node merged">${v}</div>`).join('') : '<div style="color:var(--text-dim);">(nothing yet)</div>'}</div>
          </div>
          ${stackPanelHTML(s)}
      </div>`;
  }
});
