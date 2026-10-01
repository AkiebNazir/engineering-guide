/* ============================================================================
   Visualizations for the eight problems added 30 Sep 2026 to fill missing
   patterns: 06/015 Decode String, 06/016 Maximal Rectangle, 10/021 Kth
   Ancestor of a Tree Node, 14/019 Bus Routes, 17/019 Predict the Winner,
   17/020 Best Time to Buy and Sell Stock IV, 17/021 Ones and Zeroes,
   17/022 Partition to K Equal Sum Subsets.
   Shape: `run` + `renderDOM` (the html shape in VIZ_PROGRESS.md), 1-based
   code lines, frames recorded with avRecorder from dsa-viz.js. Every helper is
   inside this block because all viz files share one global scope.
   ========================================================================= */
'use strict';
{
const cell = (content, { on = false, hot = false, dim = false, w = 34 } = {}) =>
  `<div style="min-width:${w}px;height:34px;padding:0 4px;display:flex;align-items:center;justify-content:center;` +
  `border:${on ? '2px solid var(--accent)' : '1px solid var(--border)'};border-radius:6px;` +
  `background:${hot ? 'color-mix(in srgb, var(--accent) 22%, transparent)' : 'var(--surface)'};` +
  `opacity:${dim ? 0.38 : 1};font:500 13px var(--mono, monospace)">${content}</div>`;
const rowOf = (cells, label = '') =>
  `<div style="display:flex;gap:4px;align-items:center">${label ? `<div style="width:92px;font-size:12px;color:var(--dim)">${label}</div>` : ''}${cells.join('')}</div>`;
const box = inner => `<div style="padding:10px;overflow-x:auto;display:flex;flex-direction:column;gap:6px">${inner}</div>`;
const note = text => `<div style="font-size:12px;color:var(--dim);margin-top:4px">${text}</div>`;
const nums = s => s.split(/[,\s]+/).filter(Boolean).map(Number);

/* ------------------------------------------------ 17/019 Predict the Winner */
defineAlgo('17_dp_2d', {
  title: 'Predict the Winner', short: 'Minimax DP',
  idea: '`dp[j]` holds `diff(i, j)`: the mover\'s best score minus the other player\'s on `nums[i..j]`. Taking an end gains it and hands the rest to the opponent: `max(nums[i] - diff(i+1, j), nums[j] - diff(i, j-1))`.',
  complexity: 'Time O(n^2) · Space O(n)',
  input: '1, 5, 233, 7', hint: 'nums (comma-separated)',
  code: [
    'def predictTheWinner(nums):',
    '    n = len(nums)',
    '    dp = nums[:]                  # dp[j] = diff(j, j)',
    '    for i in range(n - 2, -1, -1):',
    '        for j in range(i + 1, n):',
    '            take_left = nums[i] - dp[j]',
    '            take_right = nums[j] - dp[j - 1]',
    '            dp[j] = max(take_left, take_right)',
    '    return dp[n - 1] >= 0',
  ],
  parse: str => ({ nums: nums(str).slice(0, 12) }),
  run({ nums: a }) {
    const { F, snap } = avRecorder();
    const n = a.length, dp = a.slice();
    const s = { a, dp: dp.slice(), i: null, j: null, pick: null, done: false };
    snap(3, 'One number left: the mover takes it, so diff(j, j) = nums[j].', s);
    for (let i = n - 2; i >= 0; i--) {
      for (let j = i + 1; j < n; j++) {
        const L = a[i] - dp[j], R = a[j] - dp[j - 1];
        dp[j] = Math.max(L, R);
        Object.assign(s, { dp: dp.slice(), i, j, pick: L >= R ? 'left' : 'right' });
        snap(8, `Window [${i}..${j}]: take ${a[i]} → ${a[i]} − diff(${i + 1}, ${j}) = ${L}; take ${a[j]} → ${a[j]} − diff(${i}, ${j - 1}) = ${R}. Best ${dp[j]} (the ${s.pick} end).`, s);
      }
    }
    Object.assign(s, { i: null, j: null, done: true });
    snap(9, `diff(0, ${n - 1}) = ${dp[n - 1]}: player 1 ${dp[n - 1] >= 0 ? 'wins (ties count)' : 'loses'}.`, s);
    return F;
  },
  renderDOM(el, st) {
    const n = st.a.length;
    const numsRow = st.a.map((v, k) => cell(v, { on: k === st.i || k === st.j, dim: st.i !== null && (k < st.i || k > st.j) }));
    const dpRow = st.dp.map((v, k) => cell(v, { hot: k === st.j, dim: st.i !== null && k < st.i }));
    el.innerHTML = box(rowOf(numsRow, 'nums') + rowOf(dpRow, 'dp (diff)') +
      note(st.i === null ? (st.done ? `Answer: ${st.dp[n - 1] >= 0}` : 'Row for windows of length 1') :
        `dp[${st.j}] now means diff(${st.i}, ${st.j}); cells left of ${st.i} still hold older rows`));
  },
});

/* ------------------------------------ 17/020 Best Time to Buy and Sell Stock IV */
defineAlgo('17_dp_2d', {
  title: 'Best Time to Buy and Sell Stock IV', short: 'k transactions',
  idea: 'Two states per transaction count: `hold[j]` (own a share in the j-th trade) and `free[j]` (j trades completed). Each price can buy (free[j-1] − p) or sell (hold[j] + p).',
  complexity: 'Time O(n·k) · Space O(k)',
  input: '2 | 3, 2, 6, 5, 0, 3', hint: 'k | prices',
  code: [
    'def maxProfit(k, prices):',
    '    if k >= len(prices) // 2:',
    '        return sum(max(0, b - a) for a, b in zip(prices, prices[1:]))',
    '    hold = [-inf] * (k + 1)',
    '    free = [0] * (k + 1)',
    '    for p in prices:',
    '        for j in range(1, k + 1):',
    '            hold[j] = max(hold[j], free[j - 1] - p)',
    '            free[j] = max(free[j], hold[j] + p)',
    '    return free[k]',
  ],
  parse(str) {
    const [a, b] = str.includes('|') ? str.split('|') : ['2', str];
    return { k: Math.max(1, Math.min(4, Number(a) || 1)), prices: nums(b).slice(0, 10) };
  },
  run({ k, prices }) {
    const { F, snap } = avRecorder();
    const n = prices.length;
    if (k >= Math.floor(n / 2)) {
      let sum = 0;
      for (let d = 1; d < n; d++) sum += Math.max(0, prices[d] - prices[d - 1]);
      snap(3, `k = ${k} ≥ n // 2 = ${Math.floor(n / 2)}: the limit can't bind, so sum every rise = ${sum}.`,
        { prices, k, hold: [], free: [], day: null, j: null, answer: sum });
      return F;
    }
    const hold = Array(k + 1).fill(null), free = Array(k + 1).fill(0);
    const s = { prices, k, hold: hold.slice(), free: free.slice(), day: null, j: null, answer: null };
    snap(5, 'Before any price: holding is impossible (−∞), and doing nothing earns 0.', s);
    prices.forEach((p, d) => {
      for (let j = 1; j <= k; j++) {
        const buy = free[j - 1] - p;
        if (hold[j] === null || buy > hold[j]) hold[j] = buy;
        Object.assign(s, { hold: hold.slice(), day: d, j });
        snap(8, `Day ${d} (price ${p}): hold[${j}] = max(keep, free[${j - 1}] − ${p} = ${buy}) = ${hold[j]}`, s);
        if (hold[j] + p > free[j]) free[j] = hold[j] + p;
        s.free = free.slice();
        snap(9, `Day ${d}: free[${j}] = max(keep, hold[${j}] + ${p}) = ${free[j]}`, s);
      }
    });
    Object.assign(s, { day: null, j: null, answer: free[k] });
    snap(10, `Best with at most ${k} transactions: free[${k}] = ${free[k]}`, s);
    return F;
  },
  renderDOM(el, st) {
    const pr = st.prices.map((p, d) => cell(p, { on: d === st.day, dim: st.day !== null && d > st.day }));
    let rows = rowOf(pr, 'prices');
    for (let j = 1; j <= st.k && st.hold.length; j++) {
      rows += rowOf([cell(st.hold[j] === null ? '−∞' : st.hold[j], { hot: st.j === j, w: 56 }),
        cell(st.free[j], { hot: st.j === j, w: 56 })], `j=${j}: hold · free`);
    }
    el.innerHTML = box(rows + note(st.answer !== null ? `Answer: ${st.answer}` : 'hold = own a share now · free = trades completed, no share'));
  },
});

/* ------------------------------------------------------ 17/021 Ones and Zeroes */
defineAlgo('17_dp_2d', {
  title: 'Ones and Zeroes', short: '2-capacity knapsack',
  idea: 'Each string costs (zeros, ones). `dp[i][j]` = most strings within i zeros and j ones. Loop both capacities DOWNWARD so each string is used once.',
  complexity: 'Time O(L·m·n) · Space O(m·n)',
  input: '10, 0, 1 | 1 | 1', hint: 'strs | m | n',
  code: [
    'def findMaxForm(strs, m, n):',
    '    dp = [[0] * (n + 1) for _ in range(m + 1)]',
    '    for s in strs:',
    '        z, o = s.count("0"), s.count("1")',
    '        for i in range(m, z - 1, -1):',
    '            for j in range(n, o - 1, -1):',
    '                dp[i][j] = max(dp[i][j], dp[i - z][j - o] + 1)',
    '    return dp[m][n]',
  ],
  parse(str) {
    const [a, b, c] = str.split('|');
    return { strs: (a || '').split(/[,\s]+/).filter(x => /^[01]+$/.test(x)).slice(0, 6),
             m: Math.min(5, Number(b) || 1), n: Math.min(5, Number(c) || 1) };
  },
  run({ strs, m, n }) {
    const { F, snap } = avRecorder();
    const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
    const s = { strs, m, n, dp: dp.map(r => r.slice()), cur: null, ci: null, cj: null, src: null };
    snap(2, 'Empty table: with no strings considered, every budget holds 0 strings.', s);
    strs.forEach((str, k) => {
      const z = [...str].filter(c => c === '0').length, o = str.length - z;
      Object.assign(s, { cur: k, ci: null, cj: null, src: null });
      snap(4, `String "${str}" costs ${z} zero(s) and ${o} one(s).`, s);
      for (let i = m; i >= z; i--) for (let j = n; j >= o; j--) {
        const cand = dp[i - z][j - o] + 1;
        const upd = cand > dp[i][j];
        if (upd) dp[i][j] = cand;
        Object.assign(s, { dp: dp.map(r => r.slice()), ci: i, cj: j, src: [i - z, j - o] });
        snap(7, `dp[${i}][${j}]: take "${str}" → dp[${i - z}][${j - o}] + 1 = ${cand}${upd ? ' (better)' : ' (keep ' + dp[i][j] + ')'}`, s);
      }
    });
    Object.assign(s, { cur: null, ci: m, cj: n, src: null });
    snap(8, `Answer dp[${m}][${n}] = ${dp[m][n]}`, s);
    return F;
  },
  renderDOM(el, st) {
    const strRow = st.strs.map((x, k) => cell(x, { on: k === st.cur, w: 52, dim: st.cur !== null && k > st.cur }));
    let grid = rowOf(strRow, 'strings') + rowOf(Array.from({ length: st.n + 1 }, (_, j) => cell(`j=${j}`, { dim: true })), 'ones →');
    st.dp.forEach((r, i) => {
      grid += rowOf(r.map((v, j) => cell(v, { on: i === st.ci && j === st.cj, hot: st.src && i === st.src[0] && j === st.src[1] })), `zeros i=${i}`);
    });
    el.innerHTML = box(grid + note('Outlined: the cell being updated · tinted: the cell it reads (one string earlier)'));
  },
});

/* ------------------------------------------- 17/022 Partition to K Equal Sum Subsets */
defineAlgo('17_dp_2d', {
  title: 'Partition to K Equal Sum Subsets', short: 'Bitmask DP',
  idea: '`dp[mask]` = how full the current bucket is after using the numbers in `mask`. Buckets fill in order, so the mask alone decides the state; a full bucket resets the fill with `% target`.',
  complexity: 'Time O(n·2^n) · Space O(2^n)',
  input: '2, 2, 3, 3, 4 | 2', hint: 'nums | k',
  code: [
    'def canPartitionKSubsets(nums, k):',
    '    total = sum(nums)',
    '    if total % k: return False',
    '    target = total // k',
    '    dp = [-1] * (1 << n); dp[0] = 0',
    '    for mask in range(1 << n):',
    '        if dp[mask] < 0: continue',
    '        for i in range(n):',
    '            if not mask >> i & 1 and dp[mask] + nums[i] <= target:',
    '                dp[mask | 1 << i] = (dp[mask] + nums[i]) % target',
    '    return dp[-1] == 0',
  ],
  parse(str) {
    const [a, b] = str.includes('|') ? str.split('|') : [str, '2'];
    return { a: nums(a).slice(0, 6), k: Math.max(1, Number(b) || 2) };
  },
  run({ a, k }) {
    const { F, snap } = avRecorder();
    const n = a.length, total = a.reduce((x, y) => x + y, 0);
    const base = { a, k, target: null, mask: 0, fill: 0, next: null, reach: [], answer: null };
    if (total % k) { snap(3, `Sum ${total} isn't divisible by ${k}: impossible.`, { ...base, answer: false }); return F; }
    const target = total / k, dp = Array(1 << n).fill(-1);
    dp[0] = 0;
    const s = { ...base, target, reach: [[0, 0]] };
    snap(5, `Target per bucket = ${total} / ${k} = ${target}. Start: nothing used, fill 0.`, s);
    for (let mask = 0; mask < 1 << n; mask++) {
      if (dp[mask] < 0) continue;
      Object.assign(s, { mask, fill: dp[mask], next: null });
      snap(7, `Mask ${mask.toString(2).padStart(n, '0')} is reachable with fill ${dp[mask]}.`, s);
      for (let i = 0; i < n; i++) {
        if (mask >> i & 1 || dp[mask] + a[i] > target) continue;
        const nm = mask | 1 << i, nf = (dp[mask] + a[i]) % target;
        if (dp[nm] < 0) s.reach = [...s.reach, [nm, nf]].slice(-8);
        dp[nm] = nf;
        s.next = i;
        snap(10, `Add nums[${i}] = ${a[i]}: fill ${dp[mask]} + ${a[i]} = ${dp[mask] + a[i]}${nf === 0 ? ' — a bucket is complete, fill resets to 0' : ''}.`, s);
      }
    }
    Object.assign(s, { mask: (1 << n) - 1, fill: dp[(1 << n) - 1], next: null, answer: dp[(1 << n) - 1] === 0 });
    snap(11, `All numbers used with fill ${dp[(1 << n) - 1]}: ${s.answer}.`, s);
    return F;
  },
  renderDOM(el, st) {
    const n = st.a.length;
    const used = st.a.map((v, i) => cell(v, { on: i === st.next, hot: (st.mask >> i & 1) === 1 }));
    const pct = st.target ? Math.round(100 * st.fill / st.target) : 0;
    const bar = `<div style="width:220px;height:14px;border:1px solid var(--border);border-radius:7px;overflow:hidden">` +
      `<div style="width:${pct}%;height:100%;background:var(--accent)"></div></div>`;
    const reach = st.reach.map(([m, f]) => cell(`${m.toString(2).padStart(n, '0')}:${f}`, { w: 70, dim: true }));
    el.innerHTML = box(rowOf(used, 'used (tinted)') +
      `<div style="display:flex;gap:8px;align-items:center"><div style="width:92px;font-size:12px;color:var(--dim)">bucket fill</div>${bar}<span style="font-size:12px">${st.fill} / ${st.target ?? '—'}</span></div>` +
      rowOf(reach, 'new masks') + note(st.answer === null ? 'mask bits read right to left: bit i = nums[i]' : `Answer: ${st.answer}`));
  },
});

/* --------------------------------------------- 10/021 Kth Ancestor of a Tree Node */
defineAlgo('10_trees', {
  title: 'Kth Ancestor of a Tree Node', short: 'Binary lifting',
  idea: '`up[j][v]` is the 2^j-th ancestor of v, built level by level from `up[j-1]`. A query jumps once per set bit of k.',
  complexity: 'Build O(n log n) · Query O(log k)',
  input: '-1, 0, 0, 1, 1, 2, 2 | 6 | 2', hint: 'parent | node | k',
  code: [
    'class TreeAncestor:',
    '    def __init__(self, n, parent):',
    '        up = [parent[:]]',
    '        for j in range(1, n.bit_length()):',
    '            prev = up[-1]',
    '            up.append([prev[prev[v]] if prev[v] != -1 else -1 for v in range(n)])',
    '        self.up = up',
    '    def getKthAncestor(self, node, k):',
    '        j = 0',
    '        while k and node != -1:',
    '            if k & 1: node = self.up[j][node]',
    '            k >>= 1; j += 1',
    '        return node',
  ],
  parse(str) {
    const [a, b, c] = str.split('|');
    const parent = nums(a).slice(0, 12);
    return { parent, node: Math.min(parent.length - 1, Number(b) || 0), k: Math.max(1, Number(c) || 1) };
  },
  run({ parent, node, k }) {
    const { F, snap } = avRecorder();
    const n = parent.length, levels = Math.max(1, n.toString(2).length);
    const up = [parent.slice()];
    const s = { up: up.map(r => r.slice()), levels, j: 0, v: null, node: null, k, path: [] };
    snap(3, 'Level 0 is the parent array: jumps of 2^0 = 1.', s);
    for (let j = 1; j < levels; j++) {
      const prev = up[j - 1];
      up.push(prev.map(p => (p === -1 ? -1 : prev[p])));
      Object.assign(s, { up: up.map(r => r.slice()), j });
      snap(6, `Level ${j}: jumps of ${2 ** j} = two jumps of ${2 ** (j - 1)} (−1 stays −1).`, s);
    }
    let cur = node, kk = k, j = 0;
    Object.assign(s, { node: cur, j: null, path: [cur] });
    snap(9, `Query: the ${k}-th ancestor of ${node}; k = ${k.toString(2)} in binary.`, s);
    while (kk && cur !== -1) {
      if (j >= levels) { cur = -1; break; }
      if (kk & 1) {
        const nxt = up[j][cur];
        Object.assign(s, { j, v: cur });
        cur = nxt;
        s.node = cur; s.path = [...s.path, cur];
        snap(11, `Bit ${j} is set: jump ${2 ** j} → up[${j}][${s.v}] = ${cur}.`, s);
      }
      kk >>= 1; j += 1;
    }
    Object.assign(s, { node: cur, j: null, v: null });
    snap(13, `Answer: ${cur}.`, s);
    return F;
  },
  renderDOM(el, st) {
    const n = st.up[0].length;
    let html = rowOf(Array.from({ length: n }, (_, v) => cell(`v${v}`, { dim: true })), 'node');
    st.up.forEach((r, j) => {
      html += rowOf(r.map((x, v) => cell(x, { on: st.j === j && st.v === v, hot: st.j === j && st.v === null })), `up[${j}] (+${2 ** j})`);
    });
    html += note(`Path: ${st.path.length ? st.path.join(' → ') : '—'}`);
    el.innerHTML = box(html);
  },
});

/* ------------------------------------------------------------ 06/015 Decode String */
defineAlgo('06_stack', {
  title: 'Decode String', short: 'Stack of contexts',
  idea: 'On `[` save (text so far, repeat count) and start fresh; on `]` pop and continue with `outer + inner * k`. Counts can have several digits.',
  complexity: 'Time O(output) · Space O(output)',
  input: '3[a2[c]]', hint: 'encoded string',
  code: [
    'def decodeString(s):',
    '    stack, current, count = [], "", 0',
    '    for ch in s:',
    '        if ch.isdigit(): count = count * 10 + int(ch)',
    '        elif ch == "[":',
    '            stack.append((current, count)); current, count = "", 0',
    '        elif ch == "]":',
    '            outer, k = stack.pop(); current = outer + current * k',
    '        else: current += ch',
    '    return current',
  ],
  parse: str => ({ s: str.trim().slice(0, 24) }),
  run({ s }) {
    const { F, snap } = avRecorder();
    const st = { s, pos: null, stack: [], current: '', count: 0 };
    snap(2, 'Start with an empty stack, empty text and count 0.', st);
    let stack = [], current = '', count = 0;
    [...s].forEach((ch, i) => {
      st.pos = i;
      if (/\d/.test(ch)) { count = count * 10 + Number(ch); Object.assign(st, { count }); snap(4, `Digit ${ch}: count = ${count}.`, st); }
      else if (ch === '[') { stack.push([current, count]); current = ''; count = 0; Object.assign(st, { stack: stack.map(x => x.slice()), current, count }); snap(6, 'Open bracket: save (text, count), start fresh inside.', st); }
      else if (ch === ']') { const [outer, k] = stack.pop(); current = outer + current.repeat(k); Object.assign(st, { stack: stack.map(x => x.slice()), current }); snap(8, `Close bracket: pop ("${outer}", ${k}) → text = "${current.length > 30 ? current.slice(0, 30) + '…' : current}".`, st); }
      else { current += ch; st.current = current; snap(9, `Letter ${ch}: append.`, st); }
    });
    st.pos = null;
    snap(10, `Decoded: "${current.length > 40 ? current.slice(0, 40) + '…' : current}" (${current.length} chars).`, st);
    return F;
  },
  renderDOM(el, st) {
    const chars = [...st.s].map((c, i) => cell(c, { on: i === st.pos, dim: st.pos !== null && i > st.pos, w: 26 }));
    const frames = st.stack.length ? st.stack.map(([t, k]) => cell(`("${t}", ${k})`, { w: 90, hot: true })) : [cell('empty', { dim: true, w: 60 })];
    const cur = st.current.length > 36 ? st.current.slice(0, 36) + '…' : st.current;
    el.innerHTML = box(rowOf(chars, 'input') + rowOf(frames, 'stack') +
      rowOf([cell(`"${cur}"`, { w: 160 })], 'current') + rowOf([cell(st.count)], 'count'));
  },
});

/* -------------------------------------------------------- 06/016 Maximal Rectangle */
defineAlgo('06_stack', {
  title: 'Maximal Rectangle', short: 'Histogram per row',
  idea: 'Fix the bottom row: column heights of consecutive 1s form a histogram, and the monotonic stack finds its largest rectangle. The best over all rows wins.',
  complexity: 'Time O(rows·cols) · Space O(cols)',
  input: '10100\n10111\n11111\n10010', hint: 'rows of 0/1',
  code: [
    'def maximalRectangle(matrix):',
    '    heights, best = [0] * (cols + 1), 0',
    '    for row in matrix:',
    '        for j in range(cols):',
    '            heights[j] = heights[j] + 1 if row[j] == "1" else 0',
    '        stack = []',
    '        for j in range(cols + 1):',
    '            while stack and heights[stack[-1]] >= heights[j]:',
    '                top = stack.pop(); left = stack[-1] + 1 if stack else 0',
    '                best = max(best, heights[top] * (j - left))',
    '            stack.append(j)',
    '    return best',
  ],
  parse(str) {
    const rows = str.split(/\n|[,|]/).map(r => r.replace(/[^01]/g, '')).filter(Boolean).slice(0, 6);
    const c = Math.min(8, Math.max(...rows.map(r => r.length)));
    return { grid: rows.map(r => r.padEnd(c, '0').slice(0, c)) };
  },
  run({ grid }) {
    const { F, snap } = avRecorder();
    const cols = grid[0].length, heights = Array(cols + 1).fill(0);
    let best = 0, bestBox = null;
    const s = { grid, r: null, heights: heights.slice(0, cols), stack: [], j: null, best, bestBox };
    snap(2, 'All heights start at 0.', s);
    grid.forEach((row, r) => {
      for (let j = 0; j < cols; j++) heights[j] = row[j] === '1' ? heights[j] + 1 : 0;
      Object.assign(s, { r, heights: heights.slice(0, cols), stack: [], j: null });
      snap(5, `Row ${r} is the bottom: heights = [${heights.slice(0, cols).join(', ')}].`, s);
      const stack = [];
      for (let j = 0; j <= cols; j++) {
        while (stack.length && heights[stack[stack.length - 1]] >= heights[j]) {
          const top = stack.pop(), left = stack.length ? stack[stack.length - 1] + 1 : 0;
          const area = heights[top] * (j - left);
          if (area > best) { best = area; bestBox = [r - heights[top] + 1, left, r, j - 1]; }
          Object.assign(s, { stack: stack.slice(), j, best, bestBox });
          snap(10, `Pop bar ${top} (height ${heights[top]}): spans columns ${left}..${j - 1} → area ${area}. Best ${best}.`, s);
        }
        stack.push(j);
      }
    });
    Object.assign(s, { j: null, stack: [] });
    snap(12, `Largest rectangle: ${best}.`, s);
    return F;
  },
  renderDOM(el, st) {
    const b = st.bestBox;
    let html = '';
    st.grid.forEach((row, r) => {
      html += rowOf([...row].map((c, j) => cell(c, {
        on: b && r >= b[0] && r <= b[2] && j >= b[1] && j <= b[3],
        hot: r === st.r, dim: st.r !== null && r > st.r })), `row ${r}`);
    });
    html += rowOf(st.heights.map((h, j) => cell(h, { on: st.stack.includes(j) })), 'heights');
    el.innerHTML = box(html + note(`Outlined in the grid: best rectangle so far (${st.best}) · outlined heights: on the stack`));
  },
});

/* ---------------------------------------------------------------- 14/019 Bus Routes */
defineAlgo('14_graphs', {
  title: 'Bus Routes', short: 'BFS over routes',
  idea: 'Count buses, so routes are the nodes and a shared stop is an edge. BFS from the routes through the source; the first level that reaches the target is the answer.',
  complexity: 'Time O(sum of route lengths) · Space O(same)',
  input: '1 2 7 ; 3 6 7 | 1 | 6', hint: 'routes (;) | source | target',
  code: [
    'def numBusesToDestination(routes, source, target):',
    '    if source == target: return 0',
    '    stop_to_routes = {stop: [routes through it]}',
    '    used = set(stop_to_routes[source]); frontier = list(used); buses = 1',
    '    while frontier:',
    '        nxt = []',
    '        for r in frontier:',
    '            for s in routes[r]:',
    '                if s == target: return buses',
    '                for r2 in stop_to_routes[s]:',
    '                    if r2 not in used: used.add(r2); nxt.append(r2)',
    '        frontier, buses = nxt, buses + 1',
    '    return -1',
  ],
  parse(str) {
    const [a, b, c] = str.split('|');
    return { routes: (a || '').split(';').map(nums).filter(r => r.length).slice(0, 6), source: Number(b), target: Number(c) };
  },
  run({ routes, source, target }) {
    const { F, snap } = avRecorder();
    const base = { routes, source, target, used: [], frontier: [], buses: 0, r: null, stop: null, answer: null };
    if (source === target) { snap(2, 'Already there: 0 buses.', { ...base, answer: 0 }); return F; }
    const s2r = new Map();
    routes.forEach((stops, r) => stops.forEach(x => { if (!s2r.has(x)) s2r.set(x, []); s2r.get(x).push(r); }));
    const used = new Set(s2r.get(source) || []);
    let frontier = [...used], buses = 1;
    const s = { ...base, used: [...used], frontier: frontier.slice(), buses };
    snap(4, `Routes through stop ${source}: [${frontier.join(', ')}] — one bus.`, s);
    while (frontier.length) {
      const nxt = [];
      for (const r of frontier) {
        for (const x of routes[r]) {
          Object.assign(s, { r, stop: x });
          if (x === target) { s.answer = buses; snap(9, `Route ${r} reaches stop ${target}: ${buses} bus${buses > 1 ? 'es' : ''}.`, s); return F; }
          const fresh = (s2r.get(x) || []).filter(r2 => !used.has(r2));
          fresh.forEach(r2 => { used.add(r2); nxt.push(r2); });
          s.used = [...used];
          snap(11, fresh.length ? `Stop ${x}: change to route(s) [${fresh.join(', ')}] next.` : `Stop ${x}: no new routes.`, s);
        }
      }
      frontier = nxt; buses += 1;
      Object.assign(s, { frontier: frontier.slice(), buses, r: null, stop: null });
      snap(12, frontier.length ? `Next level (${buses} buses): routes [${frontier.join(', ')}].` : 'No new routes to try.', s);
    }
    s.answer = -1;
    snap(13, 'Target unreachable: -1.', s);
    return F;
  },
  renderDOM(el, st) {
    let html = '';
    st.routes.forEach((stops, r) => {
      html += rowOf(stops.map(x => cell(x, { on: r === st.r && x === st.stop, hot: x === st.target || x === st.source })),
        `route ${r}${st.frontier.includes(r) ? ' ▶' : st.used.includes(r) ? ' ✓' : ''}`);
    });
    el.innerHTML = box(html + note(`▶ current level · ✓ already used · tinted: source ${st.source} and target ${st.target}` +
      (st.answer !== null ? ` · Answer: ${st.answer}` : ` · buses so far: ${st.buses}`)));
  },
});
}
