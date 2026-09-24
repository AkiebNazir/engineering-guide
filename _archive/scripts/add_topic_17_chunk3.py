import sys

content = """
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
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
