/* ============================================================================
   Visualizations for 16_dp_1d — the 14 problems that were fallback-only
   (seq 002 Climbing Stairs, seq 005 House Robber, seq 010 Coin Change already
   have specs elsewhere; left untouched).
   ========================================================================= */
'use strict';

/* ------------------------------------------------------- shared helpers -- */
function dpBox(v, sub, cls, ptr) {
  return `
  <div class="array-node ${cls || ''}">
      ${ptr ? `<div class="pointer" style="color:${ptr.color || 'var(--accent)'}">${ptr.label}</div>` : ''}
      ${v}
      <div class="node-index">${sub}</div>
  </div>`;
}
function dpStrip(vals, { subOf = (v, i) => i, clsOf = () => '', ptrOf = () => null } = {}) {
  return vals.map((v, i) => dpBox(v, subOf(v, i), clsOf(v, i), ptrOf(v, i))).join('');
}
function dpPanel(heading, inner) {
  return `<div class="glass-panel arrays-container">
      <div class="panel-heading">${heading}</div>
      <div class="array-track">${inner}</div>
  </div>`;
}
function dpWrap(...panels) {
  return `<div style="display:flex; flex-direction:column; gap:15px; width:100%;">${panels.join('')}</div>`;
}

/* ============================================== 001 · N-th Tribonacci Number == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'N-th Tribonacci Number', short: 'Tribonacci',
  idea: 'Roll three variables forward: <code>a, b, c = b, c, a+b+c</code>. Each cell only needs the last three, so there is no need to keep a full array.',
  complexity: 'Time O(n) · Space O(1)',
  input: '9', hint: 'n (0-30)',
  code: [
    'def tribonacci(n):',
    '    if n == 0: return 0',
    '    if n in (1, 2): return 1',
    '    a, b, c = 0, 1, 1',
    '    for _ in range(3, n + 1):',
    '        a, b, c = b, c, a + b + c',
    '    return c',
  ],
  parse(str) {
    const n = parseInt(String(str).trim(), 10);
    if (isNaN(n) || n < 0 || n > 30) throw new Error('Enter an integer n between 0 and 30');
    return { n };
  },
  buildStates({ n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    if (n === 0 || n === 1 || n === 2) {
      domPushState(seq, { line: 2, color: 'emerald', n, a: null, b: null, c: n === 0 ? 0 : 1, i: null, done: true,
        explTitle: 'Base case', explText: `n = ${n} is a base case — return ${n === 0 ? 0 : 1} directly.`, pause: true }, ctx);
      return seq;
    }
    let a = 0, b = 1, c = 1;
    domPushState(seq, { line: 4, color: 'default', n, a, b, c, i: null, done: false,
      explTitle: 'Initialize', explText: 'a, b, c start as dp[0], dp[1], dp[2] = 0, 1, 1.' }, ctx);
    for (let i = 3; i <= n; i++) {
      const next = a + b + c;
      domPushState(seq, { line: 6, color: 'blue', n, a, b, c, i, next, done: false,
        explTitle: `Step to i=${i}`, explText: `a+b+c = ${a}+${b}+${c} = ${next}. Shift: a←b, b←c, c←${next}.` }, ctx);
      a = b; b = c; c = next;
    }
    domPushState(seq, { line: 7, color: 'emerald', n, a, b, c, i: null, done: true,
      explTitle: 'Done', explText: `Return c = ${c}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const box = (label, v, hot) => `
      <div style="display:flex; flex-direction:column; align-items:center; gap:8px;">
        <div style="font-family:var(--mono); color:var(--text-dim); font-size:12px;">${label}</div>
        <div class="array-node ${hot ? 'active-k' : ''}" style="min-width:56px;">${v === null ? '' : v}</div>
      </div>`;
    container.innerHTML = dpWrap(`<div class="glass-panel arrays-container">
      <div class="panel-heading">n = ${s.n}${s.i != null ? ` · computing i=${s.i}` : ''}</div>
      <div style="display:flex; gap:20px; align-items:center; padding:10px; justify-content:center;">
        ${box('a', s.a, false)}<div style="font-size:22px; color:var(--text-dim);">+</div>
        ${box('b', s.b, false)}<div style="font-size:22px; color:var(--text-dim);">+</div>
        ${box('c', s.c, !s.done)}<div style="font-size:22px; color:var(--text-dim);">=</div>
        ${box('next', s.next ?? (s.done ? s.c : null), s.done)}
      </div>
    </div>`);
  }
});

/* ==================================== 003 · Min Cost Climbing Stairs == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Min Cost Climbing Stairs', short: 'Min Cost Stairs',
  idea: 'Same rolling-pair shape as Climbing Stairs, but each step costs money: <code>dp[i] = min(dp[i-1]+cost[i-1], dp[i-2]+cost[i-2])</code>. You may start on step 0 or 1 for free.',
  complexity: 'Time O(n) · Space O(1)',
  input: '10, 15, 20, 5', hint: 'comma-separated stair costs',
  code: [
    'def minCostClimbingStairs(cost):',
    '    n = len(cost)',
    '    prev2, prev1 = 0, 0',
    '    for i in range(2, n + 1):',
    '        prev2, prev1 = prev1, min(prev1 + cost[i-1],',
    '                                   prev2 + cost[i-2])',
    '    return prev1',
  ],
  parse(str) {
    const cost = String(str).split(',').map(x => parseInt(x.trim(), 10));
    if (!cost.length || cost.some(isNaN)) throw new Error('Enter comma-separated integers');
    if (cost.length > 10) throw new Error('Use at most 10 stairs for visualization');
    return { cost };
  },
  buildStates({ cost }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const n = cost.length;
    let prev2 = 0, prev1 = 0;
    domPushState(seq, { line: 3, color: 'default', cost, i: null, prev2, prev1,
      explTitle: 'Initialize', explText: 'dp[0] = dp[1] = 0 — both bottom steps are free to stand on.' }, ctx);
    for (let i = 2; i <= n; i++) {
      const optA = prev1 + cost[i - 1], optB = prev2 + cost[i - 2];
      const next = Math.min(optA, optB);
      domPushState(seq, { line: 5, color: 'blue', cost, i, prev2, prev1, optA, optB, next,
        explTitle: `Step i=${i}`, explText: `min(dp[i-1]+cost[${i-1}]=${prev1}+${cost[i-1]}=${optA}, dp[i-2]+cost[${i-2}]=${prev2}+${cost[i-2]}=${optB}) = ${next}.` }, ctx);
      prev2 = prev1; prev1 = next;
    }
    domPushState(seq, { line: 7, color: 'emerald', cost, i: null, prev2, prev1,
      explTitle: 'Done', explText: `Return dp[n] = ${prev1}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const strip = dpStrip(s.cost, {
      subOf: (v, i) => i,
      clsOf: (v, i) => (i === s.i - 1 || i === s.i - 2) ? 'active-1' : (s.i != null && i < s.i - 2 ? 'merged' : ''),
    });
    container.innerHTML = dpWrap(dpPanel('cost', strip), `<div class="glass-panel arrays-container">
      <div class="panel-heading">rolling state</div>
      <div style="display:flex; gap:20px; padding:10px; justify-content:center;">
        <div style="text-align:center;"><div style="font-size:12px; color:var(--text-dim);">prev2</div><div class="array-node">${s.prev2}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:var(--text-dim);">prev1</div><div class="array-node active-k">${s.prev1}</div></div>
        ${s.next != null ? `<div style="text-align:center;"><div style="font-size:12px; color:var(--accent);">next</div><div class="array-node active-1">${s.next}</div></div>` : ''}
      </div>
    </div>`);
  }
});

/* ================================================== 004 · Pascal's Triangle == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: "Pascal's Triangle", short: "Pascal's Triangle",
  idea: 'Each row is built from the row above it: interior <code>row[j] = prev[j-1] + prev[j]</code>, and every row starts and ends with 1.',
  complexity: 'Time O(numRows²) · Space O(numRows²) for the output',
  input: '6', hint: 'number of rows (1-8)',
  code: [
    'def generate(numRows):',
    '    triangle = []',
    '    for i in range(numRows):',
    '        row = [1] * (i + 1)',
    '        for j in range(1, i):',
    '            row[j] = triangle[i-1][j-1] + triangle[i-1][j]',
    '        triangle.append(row)',
    '    return triangle',
  ],
  parse(str) {
    const n = parseInt(String(str).trim(), 10);
    if (isNaN(n) || n < 1 || n > 8) throw new Error('Enter an integer between 1 and 8');
    return { n };
  },
  buildStates({ n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const triangle = [];
    for (let i = 0; i < n; i++) {
      const row = new Array(i + 1).fill(1);
      domPushState(seq, { line: 4, color: 'default', triangle: triangle.map(r => [...r]), row: [...row], i, j: null,
        explTitle: `Start row ${i}`, explText: `Row ${i} has ${i + 1} cells, both ends fixed at 1.` }, ctx);
      for (let j = 1; j < i; j++) {
        row[j] = triangle[i - 1][j - 1] + triangle[i - 1][j];
        domPushState(seq, { line: 6, color: 'blue', triangle: triangle.map(r => [...r]), row: [...row], i, j,
          explTitle: `row[${j}]`, explText: `row[${j}] = triangle[${i-1}][${j-1}] + triangle[${i-1}][${j}] = ${triangle[i-1][j-1]} + ${triangle[i-1][j]} = ${row[j]}.` }, ctx);
      }
      triangle.push([...row]);
    }
    domPushState(seq, { line: 8, color: 'emerald', triangle: triangle.map(r => [...r]), row: null, i: null, j: null,
      explTitle: 'Done', explText: `Return the full ${n}-row triangle.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const rows = s.row != null ? [...s.triangle, s.row] : s.triangle;
    const html = rows.map((row, ri) => `
      <div style="display:flex; justify-content:center; gap:6px; margin-bottom:6px;">
        ${row.map((v, ci) => {
          const isCurRow = ri === s.i;
          const isCur = isCurRow && ci === s.j;
          const isParent = isCurRow && s.j != null && (ci === s.j - 1 || ci === s.j);
          return `<div class="array-node ${isCur ? 'active-k' : (isParent ? 'active-1' : '')}" style="min-width:40px; min-height:40px;">${v}</div>`;
        }).join('')}
      </div>`).join('');
    container.innerHTML = dpWrap(`<div class="glass-panel arrays-container"><div class="panel-heading">triangle</div>${html}</div>`);
  }
});

/* ==================================================== 006 · House Robber II == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'House Robber II', short: 'House Robber II',
  idea: 'Houses are in a circle, so you cannot rob both the first and last. Run the plain (linear) House Robber twice — once excluding the last house, once excluding the first — and take the max.',
  complexity: 'Time O(n) · Space O(1)',
  input: '2, 3, 2, 4', hint: 'house values, arranged in a circle',
  code: [
    'def rob_linear(nums):',
    '    prev2, prev1 = 0, 0',
    '    for x in nums:',
    '        prev2, prev1 = prev1, max(prev1, prev2 + x)',
    '    return prev1',
    '',
    'def rob(nums):',
    '    if len(nums) == 1: return nums[0]',
    '    return max(rob_linear(nums[:-1]), rob_linear(nums[1:]))',
  ],
  parse(str) {
    const nums = String(str).split(',').map(x => parseInt(x.trim(), 10));
    if (!nums.length || nums.some(isNaN)) throw new Error('Enter comma-separated integers');
    if (nums.length > 9) throw new Error('Use at most 9 houses for visualization');
    return { nums };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    if (nums.length === 1) {
      domPushState(seq, { line: 8, color: 'emerald', nums, pass: null, k: null, prev2: null, prev1: null,
        explTitle: 'Single house', explText: `Only one house — rob it: ${nums[0]}.`, pause: true }, ctx);
      return seq;
    }
    const runPass = (arr, passLabel, offset) => {
      let prev2 = 0, prev1 = 0;
      domPushState(seq, { line: 9, color: 'default', nums, pass: passLabel, arr, offset, k: null, prev2, prev1,
        explTitle: `Pass: ${passLabel}`, explText: `Run the linear House Robber on ${JSON.stringify(arr)}.` }, ctx);
      for (let k = 0; k < arr.length; k++) {
        const next = Math.max(prev1, prev2 + arr[k]);
        domPushState(seq, { line: 4, color: 'blue', nums, pass: passLabel, arr, offset, k, prev2, prev1, next,
          explTitle: `house ${k}`, explText: `max(prev1=${prev1}, prev2+${arr[k]}=${prev2}+${arr[k]}=${prev2+arr[k]}) = ${next}.` }, ctx);
        prev2 = prev1; prev1 = next;
      }
      return prev1;
    };
    const a = runPass(nums.slice(0, -1), 'exclude last house', 0);
    const b = runPass(nums.slice(1), 'exclude first house', 1);
    domPushState(seq, { line: 9, color: 'emerald', nums, pass: 'result', k: null, prev2: null, prev1: null, a, b, ans: Math.max(a, b),
      explTitle: 'Done', explText: `max(exclude-last=${a}, exclude-first=${b}) = ${Math.max(a, b)}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const houseStrip = dpStrip(s.nums, {
      clsOf: (v, i) => {
        if (s.pass === 'exclude last house' && i === s.nums.length - 1) return 'merged';
        if (s.pass === 'exclude first house' && i === 0) return 'merged';
        if (s.arr != null && (i - s.offset) === s.k) return 'active-k';
        return '';
      },
    });
    const state = s.pass === 'result'
      ? `<div style="text-align:center; padding:10px; font-family:var(--mono);">exclude-last=${s.a} · exclude-first=${s.b} · <b style="color:var(--emerald);">answer=${s.ans}</b></div>`
      : (s.pass ? `<div style="display:flex; gap:20px; padding:10px; justify-content:center;">
          <div style="text-align:center;"><div style="font-size:12px; color:var(--text-dim);">prev2</div><div class="array-node">${s.prev2}</div></div>
          <div style="text-align:center;"><div style="font-size:12px; color:var(--text-dim);">prev1</div><div class="array-node active-1">${s.prev1}</div></div>
        </div>` : '');
    container.innerHTML = dpWrap(dpPanel(`houses (circle) ${s.pass ? '· ' + s.pass : ''}`, houseStrip), state ? `<div class="glass-panel arrays-container">${state}</div>` : '');
  }
});

/* ===================================== 007 · Longest Palindromic Substring == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Longest Palindromic Substring', short: 'Longest Palindrome',
  idea: 'Expand around every possible center (each character, and each gap between two characters) — a palindrome is symmetric around its middle, so growing outward from that middle finds it in O(n) per center.',
  complexity: 'Time O(n²) · Space O(1)',
  input: 'babad', hint: 'string (max 12 chars)',
  code: [
    'def expand(left, right):',
    '    while left >= 0 and right < len(s) and s[left] == s[right]:',
    '        left -= 1; right += 1',
    '    return s[left+1:right]',
    '',
    'best = ""',
    'for center in range(len(s)):',
    '    best = max(best, expand(center, center),',
    '                     expand(center, center+1), key=len)',
  ],
  parse(str) {
    const s = String(str).trim();
    if (!s) throw new Error('Enter a non-empty string');
    if (s.length > 12) throw new Error('Use at most 12 characters for visualization');
    return { s };
  },
  buildStates({ s }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let best = s.length ? s[0] : '';
    const expand = (center, l, r, kind) => {
      domPushState(seq, { line: 1, color: 'blue', s, l, r, center, kind, best,
        explTitle: `Expand (${kind}) around ${center}`, explText: `Try l=${l}, r=${r}.` }, ctx);
      while (l >= 0 && r < s.length && s[l] === s[r]) {
        const cand = s.slice(l, r + 1);
        if (cand.length > best.length) best = cand;
        domPushState(seq, { line: 2, color: 'emerald', s, l, r, center, kind, best, match: cand,
          explTitle: 'Match', explText: `s[${l}]==s[${r}]=='${s[l]}' — palindrome so far: "${cand}".` }, ctx);
        l--; r++;
      }
    };
    for (let c = 0; c < s.length; c++) {
      expand(c, c, c, 'odd');
      expand(c, c, c + 1, 'even');
    }
    domPushState(seq, { line: 9, color: 'emerald', s, l: null, r: null, center: null, best,
      explTitle: 'Done', explText: `Longest palindromic substring: "${best}".`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const strip = dpStrip([...s.s], {
      clsOf: (v, i) => (i === s.l || i === s.r) ? 'active-k' : (s.l != null && s.r != null && i > s.l && i < s.r ? 'active-1' : ''),
    });
    container.innerHTML = dpWrap(dpPanel(`s${s.center != null ? ` · center=${s.center} (${s.kind})` : ''}`, strip),
      `<div class="glass-panel arrays-container"><div class="panel-heading">best so far</div>
        <div style="text-align:center; padding:10px; font-family:var(--mono); font-size:18px; color:var(--emerald);">"${s.best}"</div></div>`);
  }
});

/* ========================================= 008 · Palindromic Substrings == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Palindromic Substrings', short: 'Palindromic Substrings',
  idea: 'Same expand-around-center technique as Longest Palindromic Substring, but instead of tracking the longest match, count every successful expansion.',
  complexity: 'Time O(n²) · Space O(1)',
  input: 'aaa', hint: 'string (max 12 chars)',
  code: [
    'count = 0',
    'def expand(left, right):',
    '    global count',
    '    while left >= 0 and right < len(s) and s[left] == s[right]:',
    '        count += 1',
    '        left -= 1; right += 1',
    '',
    'for center in range(len(s)):',
    '    expand(center, center); expand(center, center+1)',
  ],
  parse(str) {
    const s = String(str).trim();
    if (!s) throw new Error('Enter a non-empty string');
    if (s.length > 12) throw new Error('Use at most 12 characters for visualization');
    return { s };
  },
  buildStates({ s }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let count = 0;
    const expand = (center, l, r, kind) => {
      domPushState(seq, { line: 4, color: 'blue', s, l, r, center, kind, count,
        explTitle: `Expand (${kind}) around ${center}`, explText: `Try l=${l}, r=${r}.` }, ctx);
      while (l >= 0 && r < s.length && s[l] === s[r]) {
        count++;
        domPushState(seq, { line: 5, color: 'emerald', s, l, r, center, kind, count, match: s.slice(l, r + 1),
          explTitle: 'Palindrome found', explText: `"${s.slice(l, r + 1)}" is a palindrome. count = ${count}.` }, ctx);
        l--; r++;
      }
    };
    for (let c = 0; c < s.length; c++) {
      expand(c, c, c, 'odd');
      expand(c, c, c + 1, 'even');
    }
    domPushState(seq, { line: 9, color: 'emerald', s, l: null, r: null, center: null, count,
      explTitle: 'Done', explText: `Total palindromic substrings: ${count}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const strip = dpStrip([...s.s], {
      clsOf: (v, i) => (i === s.l || i === s.r) ? 'active-k' : (s.l != null && s.r != null && i > s.l && i < s.r ? 'active-1' : ''),
    });
    container.innerHTML = dpWrap(dpPanel(`s${s.center != null ? ` · center=${s.center} (${s.kind})` : ''}`, strip),
      `<div class="glass-panel arrays-container"><div class="panel-heading">count</div>
        <div style="text-align:center; padding:10px; font-family:var(--mono); font-size:24px; color:var(--emerald);">${s.count}</div></div>`);
  }
});

/* ==================================================== 009 · Decode Ways == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Decode Ways', short: 'Decode Ways',
  idea: 'Rolling 1D DP over digit positions: a position contributes prev1 ways if its own digit is nonzero, and prev2 ways more if the last two digits form 10-26.',
  complexity: 'Time O(n) · Space O(1)',
  input: '226', hint: 'digit string (no leading zero)',
  code: [
    'prev2, prev1 = 1, 1 if s[0] != "0" else 0',
    'for i in range(2, n + 1):',
    '    cur = 0',
    '    if s[i-1] != "0": cur += prev1',
    '    if 10 <= int(s[i-2:i]) <= 26: cur += prev2',
    '    prev2, prev1 = prev1, cur',
    'return prev1',
  ],
  parse(str) {
    const s = String(str).trim();
    if (!/^[0-9]+$/.test(s)) throw new Error('Enter a digit string');
    if (s.length > 10) throw new Error('Use at most 10 digits for visualization');
    return { s };
  },
  buildStates({ s }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const n = s.length;
    let prev2 = 1, prev1 = s[0] !== '0' ? 1 : 0;
    domPushState(seq, { line: 1, color: 'default', s, i: null, prev2, prev1,
      explTitle: 'Initialize', explText: `dp[0]=1 (empty prefix). dp[1]=${prev1} (first digit ${s[0] !== '0' ? 'is' : 'is not'} valid alone).` }, ctx);
    for (let i = 2; i <= n; i++) {
      let cur = 0;
      const oneDigit = s[i - 1] !== '0';
      if (oneDigit) cur += prev1;
      domPushState(seq, { line: 4, color: 'blue', s, i, prev2, prev1, cur, oneDigit,
        explTitle: `Position ${i}: one digit`, explText: `s[${i-1}]='${s[i-1]}' ${oneDigit ? `is nonzero — add prev1=${prev1}. cur=${cur}.` : 'is 0 — no single-digit decode here.'}` }, ctx);
      const two = parseInt(s.slice(i - 2, i), 10);
      const twoDigit = two >= 10 && two <= 26;
      if (twoDigit) cur += prev2;
      domPushState(seq, { line: 5, color: 'blue', s, i, prev2, prev1, cur, twoDigit, two,
        explTitle: `Position ${i}: two digits`, explText: `"${s.slice(i-2,i)}"=${two} ${twoDigit ? `is 10-26 — add prev2=${prev2}. cur=${cur}.` : 'is out of range — skip.'}` }, ctx);
      prev2 = prev1; prev1 = cur;
      domPushState(seq, { line: 6, color: 'default', s, i, prev2, prev1,
        explTitle: 'Shift', explText: `dp[${i}] = ${prev1}.` }, ctx);
    }
    domPushState(seq, { line: 7, color: 'emerald', s, i: null, prev2: null, prev1,
      explTitle: 'Done', explText: `Return dp[n] = ${prev1}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const strip = dpStrip([...s.s], {
      clsOf: (v, i) => (s.i != null && (i === s.i - 1 || i === s.i - 2)) ? 'active-k' : '',
    });
    container.innerHTML = dpWrap(dpPanel('s', strip), `<div class="glass-panel arrays-container">
      <div class="panel-heading">rolling state</div>
      <div style="display:flex; gap:20px; padding:10px; justify-content:center;">
        <div style="text-align:center;"><div style="font-size:12px; color:var(--text-dim);">prev2</div><div class="array-node">${s.prev2 ?? ''}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:var(--text-dim);">prev1</div><div class="array-node active-1">${s.prev1 ?? ''}</div></div>
        ${s.cur != null ? `<div style="text-align:center;"><div style="font-size:12px; color:var(--accent);">cur</div><div class="array-node active-k">${s.cur}</div></div>` : ''}
      </div>
    </div>`);
  }
});

/* ========================================= 011 · Maximum Product Subarray == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Maximum Product Subarray', short: 'Max Product Subarray',
  idea: 'Track BOTH a running max and a running min ending here — a negative number can flip the smallest product into the largest, so the min must be carried forward too.',
  complexity: 'Time O(n) · Space O(1)',
  input: '2, 3, -2, 4', hint: 'comma-separated integers',
  code: [
    'max_end = min_end = result = nums[0]',
    'for num in nums[1:]:',
    '    candidates = (num, max_end*num, min_end*num)',
    '    max_end, min_end = max(candidates), min(candidates)',
    '    result = max(result, max_end)',
    'return result',
  ],
  parse(str) {
    const nums = String(str).split(',').map(x => parseInt(x.trim(), 10));
    if (!nums.length || nums.some(isNaN)) throw new Error('Enter comma-separated integers');
    if (nums.length > 9) throw new Error('Use at most 9 numbers for visualization');
    return { nums };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    let maxEnd = nums[0], minEnd = nums[0], result = nums[0];
    domPushState(seq, { line: 1, color: 'default', nums, i: 0, maxEnd, minEnd, result,
      explTitle: 'Initialize', explText: `max_end = min_end = result = nums[0] = ${nums[0]}.` }, ctx);
    for (let i = 1; i < nums.length; i++) {
      const num = nums[i];
      const cands = [num, maxEnd * num, minEnd * num];
      const newMax = Math.max(...cands), newMin = Math.min(...cands);
      result = Math.max(result, newMax);
      domPushState(seq, { line: 3, color: 'blue', nums, i, maxEnd, minEnd, result, num, cands, newMax, newMin,
        explTitle: `i=${i}, num=${num}`, explText: `candidates = (${num}, ${maxEnd}×${num}=${maxEnd*num}, ${minEnd}×${num}=${minEnd*num}) → new max=${newMax}, new min=${newMin}. result=${result}.` }, ctx);
      maxEnd = newMax; minEnd = newMin;
    }
    domPushState(seq, { line: 6, color: 'emerald', nums, i: null, maxEnd, minEnd, result,
      explTitle: 'Done', explText: `Return result = ${result}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const strip = dpStrip(s.nums, { clsOf: (v, i) => i === s.i ? 'active-k' : (i < s.i ? 'merged' : '') });
    container.innerHTML = dpWrap(dpPanel('nums', strip), `<div class="glass-panel arrays-container">
      <div class="panel-heading">running state</div>
      <div style="display:flex; gap:16px; padding:10px; justify-content:center; flex-wrap:wrap;">
        <div style="text-align:center;"><div style="font-size:12px; color:var(--text-dim);">max_end</div><div class="array-node active-k">${s.maxEnd}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:var(--text-dim);">min_end</div><div class="array-node">${s.minEnd}</div></div>
        <div style="text-align:center;"><div style="font-size:12px; color:var(--emerald);">result</div><div class="array-node active-1">${s.result}</div></div>
      </div>
    </div>`);
  }
});

/* ==================================================== 012 · Word Break == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Word Break', short: 'Word Break',
  idea: 'dp[i] means "the prefix s[:i] can be fully segmented." To fill dp[i], look back at every dp[j] that is already True and check whether s[j:i] is a dictionary word.',
  complexity: 'Time O(n² ) amortized by max word length · Space O(n)',
  input: 'leetcode ; leet, code', hint: 's ; comma-separated dictionary',
  code: [
    'dp = [False] * (n + 1); dp[0] = True',
    'for i in range(1, n + 1):',
    '    for j in range(i):',
    '        if dp[j] and s[j:i] in words:',
    '            dp[i] = True; break',
    'return dp[n]',
  ],
  parse(str) {
    const [a, b] = String(str).split(';');
    const s = String(a || '').trim();
    const words = String(b || '').split(',').map(w => w.trim()).filter(Boolean);
    if (!s) throw new Error('Enter a string before the ";"');
    if (s.length > 14) throw new Error('Use at most 14 characters for visualization');
    if (!words.length) throw new Error('Enter at least one dictionary word after the ";"');
    return { s, words: new Set(words) };
  },
  buildStates({ s, words }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const n = s.length;
    const dp = new Array(n + 1).fill(false);
    dp[0] = true;
    domPushState(seq, { line: 1, color: 'default', s, dp: [...dp], i: null, j: null,
      explTitle: 'Initialize', explText: 'dp[0] = True — the empty prefix is trivially segmentable.' }, ctx);
    for (let i = 1; i <= n; i++) {
      for (let j = 0; j < i; j++) {
        const word = s.slice(j, i);
        const ok = dp[j] && words.has(word);
        domPushState(seq, { line: 4, color: ok ? 'emerald' : 'default', s, dp: [...dp], i, j, word, dpJ: dp[j], inDict: words.has(word), ok,
          explTitle: `dp[${i}] via j=${j}`, explText: `dp[${j}]=${dp[j]} and "${word}" ${words.has(word) ? 'IS' : 'is NOT'} in the dictionary${ok ? ' — dp[' + i + '] = True.' : '.'}` }, ctx);
        if (ok) { dp[i] = true; break; }
      }
    }
    domPushState(seq, { line: 6, color: 'emerald', s, dp: [...dp], i: null, j: null,
      explTitle: 'Done', explText: `Return dp[n] = ${dp[n]}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const dpStripHTML = dpStrip(s.dp, {
      subOf: (v, i) => i,
      clsOf: (v, i) => v ? 'active-1' : (i === s.i ? 'active-k' : ''),
    });
    const charStrip = dpStrip([...s.s], {
      clsOf: (v, i) => (s.j != null && s.i != null && i >= s.j && i < s.i) ? 'active-k' : '',
    });
    const info = s.word != null ? `<div style="text-align:center; padding:10px; font-family:var(--mono);">s[${s.j}:${s.i}] = "${s.word}" — ${s.inDict ? 'in dictionary' : 'not in dictionary'}, dp[${s.j}]=${String(s.dpJ)}</div>` : '';
    container.innerHTML = dpWrap(dpPanel('s', charStrip), dpPanel('dp[0..n]', dpStripHTML), info ? `<div class="glass-panel arrays-container">${info}</div>` : '');
  }
});

/* ============================== 013 · Longest Increasing Subsequence == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Longest Increasing Subsequence', short: 'LIS',
  idea: 'Patience sorting: keep `tails[k]` = the smallest possible tail of an increasing subsequence of length k+1. For each number, binary-search where it belongs in `tails` and overwrite (or append) — the FINAL length of `tails` is the answer, though its contents are not necessarily a real subsequence.',
  complexity: 'Time O(n log n) · Space O(n)',
  input: '10, 9, 2, 5, 3, 7, 101, 18', hint: 'comma-separated integers',
  code: [
    'tails = []',
    'for x in nums:',
    '    pos = bisect_left(tails, x)',
    '    if pos == len(tails): tails.append(x)',
    '    else: tails[pos] = x',
    'return len(tails)',
  ],
  parse(str) {
    const nums = String(str).split(',').map(x => parseInt(x.trim(), 10));
    if (!nums.length || nums.some(isNaN)) throw new Error('Enter comma-separated integers');
    if (nums.length > 10) throw new Error('Use at most 10 numbers for visualization');
    return { nums };
  },
  buildStates({ nums }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const tails = [];
    const bisectLeft = (arr, x) => { let lo = 0, hi = arr.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (arr[mid] < x) lo = mid + 1; else hi = mid; } return lo; };
    domPushState(seq, { line: 1, color: 'default', nums, tails: [], i: null,
      explTitle: 'Initialize', explText: 'tails starts empty.' }, ctx);
    for (let i = 0; i < nums.length; i++) {
      const x = nums[i], pos = bisectLeft(tails, x);
      const append = pos === tails.length;
      domPushState(seq, { line: 3, color: 'blue', nums, tails: [...tails], i, x, pos, append,
        explTitle: `x=${x}`, explText: `bisect_left(tails, ${x}) = ${pos} — ${append ? 'extends tails by one.' : `overwrites tails[${pos}].`}` }, ctx);
      if (append) tails.push(x); else tails[pos] = x;
      domPushState(seq, { line: append ? 4 : 5, color: 'emerald', nums, tails: [...tails], i, x, pos, append,
        explTitle: 'tails updated', explText: `tails = [${tails.join(', ')}].` }, ctx);
    }
    domPushState(seq, { line: 6, color: 'emerald', nums, tails: [...tails], i: null,
      explTitle: 'Done', explText: `Return len(tails) = ${tails.length}. (tails is NOT the actual subsequence, only its length is meaningful.)`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const numStrip = dpStrip(s.nums, { clsOf: (v, i) => i === s.i ? 'active-k' : (i < s.i ? 'merged' : '') });
    const tailStrip = dpStrip(s.tails, { clsOf: (v, i) => i === s.pos ? 'active-1' : '' });
    container.innerHTML = dpWrap(dpPanel('nums', numStrip), dpPanel('tails', tailStrip));
  }
});

/* ===================================== 014 · Partition Equal Subset Sum == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Partition Equal Subset Sum', short: 'Partition Subset Sum',
  idea: '0/1 knapsack: dp[s] means "some subset sums to s." Scanning each number\'s effect on the sum axis HIGH→LOW (never low→high) is what keeps each number used at most once.',
  complexity: 'Time O(n × target) · Space O(target)',
  input: '1, 5, 11, 5', hint: 'comma-separated positive integers',
  code: [
    'target = sum(nums) // 2',
    'dp = [False] * (target + 1); dp[0] = True',
    'for num in nums:',
    '    for s in range(target, num - 1, -1):',
    '        if dp[s - num]: dp[s] = True',
    '    if dp[target]: return True',
    'return dp[target]',
  ],
  parse(str) {
    const nums = String(str).split(',').map(x => parseInt(x.trim(), 10));
    if (!nums.length || nums.some(n => isNaN(n) || n < 0)) throw new Error('Enter comma-separated non-negative integers');
    if (nums.length > 8) throw new Error('Use at most 8 numbers for visualization');
    const total = nums.reduce((a, b) => a + b, 0);
    if (total / 2 > 40) throw new Error('Keep the total sum at 80 or below for visualization');
    return { nums, total };
  },
  buildStates({ nums, total }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    if (total % 2 !== 0) {
      domPushState(seq, { line: 1, color: 'rose', nums, target: null, dp: [], num: null, s: null,
        explTitle: 'Odd total', explText: `Total = ${total} is odd — an equal partition is impossible.`, pause: true }, ctx);
      return seq;
    }
    const target = total / 2;
    const dp = new Array(target + 1).fill(false);
    dp[0] = true;
    domPushState(seq, { line: 2, color: 'default', nums, target, dp: [...dp], num: null, s: null,
      explTitle: 'Initialize', explText: `target = ${target}. dp[0] = True.` }, ctx);
    for (const num of nums) {
      for (let s = target; s >= num; s--) {
        if (dp[s - num]) {
          dp[s] = true;
          domPushState(seq, { line: 5, color: 'emerald', nums, target, dp: [...dp], num, s,
            explTitle: `num=${num}, s=${s}`, explText: `dp[${s-num}] is True, so dp[${s}] becomes True.` }, ctx);
        } else {
          domPushState(seq, { line: 4, color: 'default', nums, target, dp: [...dp], num, s,
            explTitle: `num=${num}, s=${s}`, explText: `dp[${s-num}] is False — no change.` }, ctx);
        }
      }
      if (dp[target]) break;
    }
    domPushState(seq, { line: 7, color: dp[target] ? 'emerald' : 'rose', nums, target, dp: [...dp], num: null, s: null,
      explTitle: 'Done', explText: `Return dp[target] = ${dp[target]}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const numStrip = dpStrip(s.nums, { clsOf: (v) => v === s.num ? 'active-k' : '' });
    const parts = [dpPanel('nums', numStrip)];
    if (s.dp.length) {
      const dpStripHTML = dpStrip(s.dp.map(v => v ? 'T' : 'F'), { clsOf: (v, i) => i === s.s ? 'active-k' : (v === 'T' ? 'active-1' : '') });
      parts.push(dpPanel(`dp[0..${s.target}] (achievable sums)`, dpStripHTML));
    }
    container.innerHTML = dpWrap(...parts);
  }
});

/* ===================================== 015 · Combination Sum IV == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Combination Sum IV', short: 'Combination Sum IV',
  idea: 'dp[t] = number of ORDERED sequences that sum to t. Looping target OUTER and nums INNER (the opposite nesting from Coin Change) is what makes order matter — the same multiset counted in different orders counts separately.',
  complexity: 'Time O(target × len(nums)) · Space O(target)',
  input: '1, 2, 3 ; 4', hint: 'comma-separated nums ; target',
  code: [
    'dp = [0] * (target + 1); dp[0] = 1',
    'for t in range(1, target + 1):',
    '    for num in nums:',
    '        if num <= t:',
    '            dp[t] += dp[t - num]',
    'return dp[target]',
  ],
  parse(str) {
    const [a, b] = String(str).split(';');
    const nums = String(a || '').split(',').map(x => parseInt(x.trim(), 10));
    const target = parseInt(String(b || '').trim(), 10);
    if (!nums.length || nums.some(isNaN)) throw new Error('Enter comma-separated integers before the ";"');
    if (isNaN(target) || target < 0) throw new Error('Enter a non-negative target after the ";"');
    if (target > 20) throw new Error('Keep target at 20 or below for visualization');
    return { nums, target };
  },
  buildStates({ nums, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const dp = new Array(target + 1).fill(0);
    dp[0] = 1;
    domPushState(seq, { line: 1, color: 'default', nums, target, dp: [...dp], t: null, num: null,
      explTitle: 'Initialize', explText: 'dp[0] = 1 — one way to make 0 (use nothing).' }, ctx);
    for (let t = 1; t <= target; t++) {
      for (const num of nums) {
        if (num <= t) {
          dp[t] += dp[t - num];
          domPushState(seq, { line: 5, color: 'blue', nums, target, dp: [...dp], t, num,
            explTitle: `t=${t}, num=${num}`, explText: `dp[${t}] += dp[${t-num}] → dp[${t}] = ${dp[t]}.` }, ctx);
        }
      }
    }
    domPushState(seq, { line: 6, color: 'emerald', nums, target, dp: [...dp], t: null, num: null,
      explTitle: 'Done', explText: `Return dp[target] = ${dp[target]}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const numStrip = dpStrip(s.nums, { clsOf: (v) => v === s.num ? 'active-k' : '' });
    const dpStripHTML = dpStrip(s.dp, { clsOf: (v, i) => i === s.t ? 'active-k' : '' });
    container.innerHTML = dpWrap(dpPanel('nums', numStrip), dpPanel(`dp[0..${s.target}]`, dpStripHTML));
  }
});

/* ===================================================== 016 · Perfect Squares == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Perfect Squares', short: 'Perfect Squares',
  idea: 'dp[i] = minimum number of perfect squares summing to i. For each i, try every perfect square ≤ i as the last term: dp[i] = min(dp[i - sq] + 1).',
  complexity: 'Time O(n√n) · Space O(n)',
  input: '12', hint: 'n (1-40)',
  code: [
    'squares = [k*k for k in range(1, int(n**0.5)+1)]',
    'dp = [0] + [inf] * n',
    'for i in range(1, n + 1):',
    '    for sq in squares:',
    '        if sq > i: break',
    '        dp[i] = min(dp[i], dp[i - sq] + 1)',
    'return dp[n]',
  ],
  parse(str) {
    const n = parseInt(String(str).trim(), 10);
    if (isNaN(n) || n < 1 || n > 40) throw new Error('Enter an integer between 1 and 40');
    return { n };
  },
  buildStates({ n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const squares = [];
    for (let k = 1; k * k <= n; k++) squares.push(k * k);
    const INF = Infinity;
    const dp = new Array(n + 1).fill(INF); dp[0] = 0;
    domPushState(seq, { line: 1, color: 'default', n, squares, dp: dp.map(v => v === INF ? '∞' : v), i: null, sq: null,
      explTitle: 'Initialize', explText: `Candidate squares ≤ ${n}: [${squares.join(', ')}]. dp[0] = 0.` }, ctx);
    for (let i = 1; i <= n; i++) {
      for (const sq of squares) {
        if (sq > i) break;
        const cand = dp[i - sq] + 1;
        const improved = cand < dp[i];
        if (improved) dp[i] = cand;
        domPushState(seq, { line: 6, color: improved ? 'emerald' : 'default', n, squares, dp: dp.map(v => v === INF ? '∞' : v), i, sq, cand, improved,
          explTitle: `dp[${i}] via ${sq}`, explText: `dp[${i-sq}] + 1 = ${dp[i-sq] === INF ? '∞' : dp[i-sq]+1} ${improved ? `— improves dp[${i}] to ${dp[i]}.` : '— no improvement.'}` }, ctx);
      }
    }
    domPushState(seq, { line: 7, color: 'emerald', n, squares, dp: dp.map(v => v === INF ? '∞' : v), i: null, sq: null,
      explTitle: 'Done', explText: `Return dp[n] = ${dp[n]}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const dpStripHTML = dpStrip(s.dp, { clsOf: (v, i) => i === s.i ? 'active-k' : (i === s.i - s.sq ? 'active-1' : '') });
    const sqInfo = s.sq != null ? `<div style="text-align:center; padding:6px; font-family:var(--mono); font-size:12px; color:var(--text-dim);">trying square ${s.sq} → dp[${s.i - s.sq}] + 1</div>` : '';
    container.innerHTML = dpWrap(dpPanel(`dp[0..${s.n}]`, dpStripHTML) + sqInfo);
  }
});

/* =============================================== 017 · Russian Doll Envelopes == */
defineAlgoDom('16_dp_1d', {
  type: 'dom',
  title: 'Russian Doll Envelopes', short: 'Russian Doll Envelopes',
  idea: 'Sort by width ascending, and for EQUAL widths by height DESCENDING (so no two same-width envelopes ever count together in the LIS pass). Then this collapses to Longest Increasing Subsequence on the heights alone.',
  complexity: 'Time O(n log n) · Space O(n)',
  input: '5,4 ; 6,4 ; 6,7 ; 2,3', hint: 'semicolon-separated width,height pairs',
  code: [
    'ordered = sorted(envelopes, key=lambda e: (e[0], -e[1]))',
    'tails = []',
    'for _, h in ordered:',
    '    i = bisect_left(tails, h)',
    '    if i == len(tails): tails.append(h)',
    '    else: tails[i] = h',
    'return len(tails)',
  ],
  parse(str) {
    const envs = String(str).split(';').map(pair => pair.split(',').map(x => parseInt(x.trim(), 10)));
    if (!envs.length || envs.some(e => e.length !== 2 || e.some(isNaN))) throw new Error('Enter semicolon-separated "width,height" pairs');
    if (envs.length > 8) throw new Error('Use at most 8 envelopes for visualization');
    return { envs };
  },
  buildStates({ envs }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const ordered = [...envs].sort((a, b) => a[0] - b[0] || b[1] - a[1]);
    domPushState(seq, { line: 1, color: 'default', envs, ordered: [...ordered], tails: [], i: null,
      explTitle: 'Sort', explText: `Sorted by width asc, ties by height desc: [${ordered.map(e => `(${e[0]},${e[1]})`).join(' ')}].` }, ctx);
    const bisectLeft = (arr, x) => { let lo = 0, hi = arr.length; while (lo < hi) { const mid = (lo + hi) >> 1; if (arr[mid] < x) lo = mid + 1; else hi = mid; } return lo; };
    const tails = [];
    for (let i = 0; i < ordered.length; i++) {
      const h = ordered[i][1], pos = bisectLeft(tails, h), append = pos === tails.length;
      domPushState(seq, { line: 4, color: 'blue', envs, ordered, tails: [...tails], i, h, pos, append,
        explTitle: `envelope (${ordered[i][0]},${h})`, explText: `bisect_left(tails, ${h}) = ${pos} — ${append ? 'extend tails.' : `overwrite tails[${pos}].`}` }, ctx);
      if (append) tails.push(h); else tails[pos] = h;
      domPushState(seq, { line: append ? 5 : 6, color: 'emerald', envs, ordered, tails: [...tails], i, h, pos, append,
        explTitle: 'tails updated', explText: `tails = [${tails.join(', ')}].` }, ctx);
    }
    domPushState(seq, { line: 7, color: 'emerald', envs, ordered, tails: [...tails], i: null,
      explTitle: 'Done', explText: `Return len(tails) = ${tails.length}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const ordStrip = dpStrip(s.ordered.map(e => `${e[0]},${e[1]}`), { clsOf: (v, i) => i === s.i ? 'active-k' : (i < s.i ? 'merged' : '') });
    const tailStrip = dpStrip(s.tails, { clsOf: (v, i) => i === s.pos ? 'active-1' : '' });
    container.innerHTML = dpWrap(dpPanel('envelopes (sorted)', ordStrip), dpPanel('tails (by height)', tailStrip));
  }
});
