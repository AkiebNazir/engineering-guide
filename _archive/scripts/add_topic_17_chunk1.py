import sys

content = """
defineAlgo('17_dp_2d', {
  title: 'Best Time to Buy and Sell Stock with Cooldown', short: 'Stock w/ Cooldown',
  idea: 'State machine DP. We maintain two states for each day: `held` (holding a stock) and `sold` (no stock). Due to cooldown, buying on day `i` requires the `sold` state from day `i-2`.',
  complexity: 'Time O(N) · Space O(N)',
  input: '1, 2, 3, 0, 2', hint: 'comma-separated prices',
  code: [
    'def maxProfit(prices):',
    '    n = len(prices)',
    '    if n <= 1: return 0',
    '    ',
    '    held = [0] * n',
    '    sold = [0] * n',
    '    ',
    '    held[0] = -prices[0]',
    '    sold[0] = 0',
    '    held[1] = max(-prices[0], -prices[1])',
    '    sold[1] = max(0, held[0] + prices[1])',
    '    ',
    '    for i in range(2, n):',
    '        held[i] = max(held[i-1], sold[i-2] - prices[i])',
    '        sold[i] = max(sold[i-1], held[i-1] + prices[i])',
    '        ',
    '    return sold[n-1]'
  ],
  parse(str) {
    const prices = str.split(',').map(Number);
    if (!prices.length) throw new Error("Need prices");
    return { prices, n: prices.length };
  },
  run({ prices, n }) {
    const { F, snap } = avRecorder();
    if (n <= 1) {
       snap(1, 'Need at least 2 days', {});
       return F;
    }
    
    let held = new Array(n).fill(0);
    let sold = new Array(n).fill(0);
    
    held[0] = -prices[0];
    sold[0] = 0;
    held[1] = Math.max(-prices[0], -prices[1]);
    sold[1] = Math.max(0, held[0] + prices[1]);
    
    const s = { prices, n, held: [...held], sold: [...sold], i: null };
    snap(10, 'Initialize base cases for day 0 and day 1.', s);
    
    for (let i = 2; i < n; i++) {
       s.i = i;
       
       held[i] = Math.max(held[i-1], sold[i-2] - prices[i]);
       sold[i] = Math.max(sold[i-1], held[i-1] + prices[i]);
       
       s.held = [...held];
       s.sold = [...sold];
       
       snap(13, `Day ${i} (price=${prices[i]}): held=max(held[${i-1}], sold[${i-2}] - ${prices[i]})=${held[i]}. sold=max(sold[${i-1}], held[${i-1}] + ${prices[i]})=${sold[i]}.`, s);
    }
    
    s.i = null;
    snap(16, `Finished. Max profit is sold[${n-1}] = ${sold[n-1]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:8px;">';
    html += '<div style="display:flex; gap:4px;"><div style="width:60px;">Price:</div>';
    for(let i=0; i<s.n; i++) html += `<div style="width:40px; text-align:center; color:var(--accent); font-weight:bold;">${s.prices[i]}</div>`;
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px;">Held:</div>';
    for(let i=0; i<s.n; i++) html += `<div style="width:40px; height:30px; display:flex; align-items:center; justify-content:center; border:1px solid var(--border); ${s.i===i?'border-color:var(--accent); background:rgba(56, 189, 248, 0.1);':''}">${s.held[i]}</div>`;
    html += '</div>';
    
    html += '<div style="display:flex; gap:4px;"><div style="width:60px;">Sold:</div>';
    for(let i=0; i<s.n; i++) html += `<div style="width:40px; height:30px; display:flex; align-items:center; justify-content:center; border:1px solid var(--border); ${s.i===i?'border-color:var(--accent); background:rgba(56, 189, 248, 0.1);':''}">${s.sold[i]}</div>`;
    html += '</div></div>';
    
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Coin Change II', short: 'Coin Change II',
  idea: '`dp[i][a]` is ways to make amount `a` using first `i` coins. `dp[i][a] = dp[i-1][a] + dp[i][a-coin]`. We visualize this as a 2D table.',
  complexity: 'Time O(coins * amount) · Space O(coins * amount)',
  input: '1, 2, 5; 5', hint: 'coins; amount',
  code: [
    'def change(amount, coins):',
    '    n = len(coins)',
    '    dp = [[0] * (amount + 1) for _ in range(n + 1)]',
    '    ',
    '    for i in range(n + 1):',
    '        dp[i][0] = 1',
    '        ',
    '    for i in range(1, n + 1):',
    '        for a in range(1, amount + 1):',
    '            if coins[i-1] > a:',
    '                dp[i][a] = dp[i-1][a]',
    '            else:',
    '                dp[i][a] = dp[i-1][a] + dp[i][a - coins[i-1]]',
    '                ',
    '    return dp[n][amount]'
  ],
  parse(str) {
    const parts = str.split(';');
    const coins = parts[0].split(',').map(Number);
    const amount = parseInt(parts[1]);
    return { coins, amount, n: coins.length };
  },
  run({ coins, amount, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: n + 1}, () => new Array(amount + 1).fill(0));
    for (let i = 0; i <= n; i++) dp[i][0] = 1;
    
    const s = { coins, amount, n, dp: JSON.parse(JSON.stringify(dp)), i: null, a: null };
    snap(5, 'Initialize DP table. dp[i][0] = 1 (1 way to make amount 0).', s);
    
    for (let i = 1; i <= n; i++) {
       for (let a = 1; a <= amount; a++) {
          s.i = i; s.a = a;
          if (coins[i-1] > a) {
             dp[i][a] = dp[i-1][a];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Coin ${coins[i-1]} > amount ${a}. dp[${i}][${a}] = dp[${i-1}][${a}] = ${dp[i][a]}.`, s);
          } else {
             dp[i][a] = dp[i-1][a] + dp[i][a - coins[i-1]];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(13, `Use coin ${coins[i-1]}. dp[${i}][${a}] = ways without (${dp[i-1][a]}) + ways with (${dp[i][a - coins[i-1]]}) = ${dp[i][a]}.`, s);
          }
       }
    }
    
    s.i = null; s.a = null;
    snap(15, `Finished. Total ways = ${dp[n][amount]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    html += '<div style="display:flex; gap:4px;"><div style="width:40px;"></div>';
    for (let a = 0; a <= s.amount; a++) html += `<div style="width:30px; text-align:center; font-weight:bold;">${a}</div>`;
    html += '</div>';
    
    for (let r = 0; r <= s.n; r++) {
       html += '<div style="display:flex; gap:4px;">';
       const coinLabel = r === 0 ? 'None' : String(s.coins[r-1]);
       html += `<div style="width:40px; font-weight:bold;">${coinLabel}</div>`;
       for (let c = 0; c <= s.amount; c++) {
          const isCurrent = s.i === r && s.a === c;
          let border = isCurrent ? '2px solid var(--accent)' : '1px solid var(--border)';
          html += `<div style="width:30px; height:30px; display:flex; align-items:center; justify-content:center; border:${border}; ${isCurrent?'background:rgba(56, 189, 248, 0.1);':''}">${s.dp[r][c]}</div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Target Sum', short: 'Target Sum',
  idea: 'Uses 2D DP to count ways to reach target. `dp[i][s]` is ways to form sum `s` with first `i` numbers.',
  complexity: 'Time O(N * Sum) · Space O(N * Sum)',
  input: '1,1,1,1,1; 3', hint: 'nums; target',
  code: [
    'def findTargetSumWays(nums, target):',
    '    total = sum(nums)',
    '    if abs(target) > total: return 0',
    '    ',
    '    offset = total',
    '    dp = [[0] * (2 * total + 1) for _ in range(len(nums) + 1)]',
    '    dp[0][offset] = 1',
    '    ',
    '    for i in range(1, len(nums) + 1):',
    '        for s in range(2 * total + 1):',
    '            if dp[i-1][s] > 0:',
    '                dp[i][s + nums[i-1]] += dp[i-1][s]',
    '                dp[i][s - nums[i-1]] += dp[i-1][s]',
    '                ',
    '    return dp[len(nums)][target + offset]'
  ],
  parse(str) {
    const parts = str.split(';');
    const nums = parts[0].split(',').map(Number);
    const target = parseInt(parts[1]);
    return { nums, target };
  },
  run({ nums, target }) {
    const { F, snap } = avRecorder();
    const total = nums.reduce((a, b) => a + Math.abs(b), 0);
    if (Math.abs(target) > total) return snap(1, 'Target unreachable', {}) && F;
    
    let dp = Array.from({length: nums.length + 1}, () => new Array(2 * total + 1).fill(0));
    const offset = total;
    dp[0][offset] = 1;
    
    const s = { nums, target, total, offset, dp: JSON.parse(JSON.stringify(dp)), i: null };
    snap(6, 'Initialize DP. dp[0][0] = 1 (offset mapped to index).', s);
    
    for (let i = 1; i <= nums.length; i++) {
       s.i = i;
       for (let sum = 0; sum <= 2 * total; sum++) {
          if (dp[i-1][sum] > 0) {
             dp[i][sum + nums[i-1]] += dp[i-1][sum];
             dp[i][sum - nums[i-1]] += dp[i-1][sum];
          }
       }
       s.dp = JSON.parse(JSON.stringify(dp));
       snap(11, `Process num ${nums[i-1]}. Branch into + and -.`, s);
    }
    
    s.i = null;
    snap(14, `Done. Target ${target} ways = ${dp[nums.length][target + offset]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    if(!s.dp) return;
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    html += '<div style="display:flex; gap:4px;"><div style="width:40px;">Idx</div>';
    for(let sum=0; sum<=2*s.total; sum++) {
        if(s.dp[s.dp.length-1][sum] > 0 || sum === s.target + s.offset || sum === s.offset) {
            html += `<div style="width:30px; text-align:center; font-size:10px;">${sum-s.offset}</div>`;
        }
    }
    html += '</div>';
    
    for(let i=0; i<=s.nums.length; i++) {
       html += '<div style="display:flex; gap:4px;">';
       html += `<div style="width:40px; font-weight:bold;">${i}</div>`;
       for(let sum=0; sum<=2*s.total; sum++) {
          if(s.dp[s.dp.length-1][sum] > 0 || sum === s.target + s.offset || sum === s.offset) {
             let border = s.i === i ? '2px solid var(--accent)' : '1px solid var(--border)';
             let bg = s.dp[i][sum] > 0 ? 'rgba(52, 211, 153, 0.2)' : 'var(--surface)';
             html += `<div style="width:30px; height:20px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg}; font-size:11px;">${s.dp[i][sum]}</div>`;
          }
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Longest Increasing Path in a Matrix', short: 'LIP in Matrix',
  idea: 'DFS with Memoization. `memo[i][j]` stores the longest increasing path starting at `(i, j)`.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: '9,9,4; 6,6,8; 2,1,1', hint: 'comma-separated rows',
  code: [
    'def longestIncreasingPath(matrix):',
    '    m, n = len(matrix), len(matrix[0])',
    '    memo = [[0] * n for _ in range(m)]',
    '    ',
    '    def dfs(i, j):',
    '        if memo[i][j]: return memo[i][j]',
    '        ans = 1',
    '        for di, dj in [(0,1),(1,0),(0,-1),(-1,0)]:',
    '            ni, nj = i + di, j + dj',
    '            if 0<=ni<m and 0<=nj<n and matrix[ni][nj] > matrix[i][j]:',
    '                ans = max(ans, 1 + dfs(ni, nj))',
    '        memo[i][j] = ans',
    '        return ans',
    '        ',
    '    return max(dfs(i, j) for i in range(m) for j in range(n))'
  ],
  parse(str) {
    const grid = str.split(';').map(r => r.split(',').map(Number));
    return { grid, m: grid.length, n: grid[0].length };
  },
  run({ grid, m, n }) {
    const { F, snap } = avRecorder();
    let memo = Array.from({length: m}, () => new Array(n).fill(0));
    const s = { grid, memo: JSON.parse(JSON.stringify(memo)), m, n, cur: null };
    
    snap(3, 'Start DFS with Memo.', s);
    
    let maxLen = 0;
    const dfs = (i, j) => {
       if (memo[i][j]) return memo[i][j];
       let ans = 1;
       const dirs = [[0,1],[1,0],[0,-1],[-1,0]];
       for (const [di, dj] of dirs) {
          const ni = i + di, nj = j + dj;
          if (ni>=0 && ni<m && nj>=0 && nj<n && grid[ni][nj] > grid[i][j]) {
             ans = Math.max(ans, 1 + dfs(ni, nj));
          }
       }
       memo[i][j] = ans;
       s.memo = JSON.parse(JSON.stringify(memo));
       s.cur = [i, j];
       snap(11, `Memoized cell (${i}, ${j}) = ${ans}`, s);
       return ans;
    };
    
    for (let i = 0; i < m; i++) {
       for (let j = 0; j < n; j++) {
          maxLen = Math.max(maxLen, dfs(i, j));
       }
    }
    
    s.cur = null;
    snap(14, `Done. Max length = ${maxLen}`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    for (let i=0; i<s.m; i++) {
       html += '<div style="display:flex; gap:4px;">';
       for (let j=0; j<s.n; j++) {
          let border = s.cur && s.cur[0]===i && s.cur[1]===j ? '2px solid var(--accent)' : '1px solid var(--border)';
          let bg = s.memo[i][j] > 0 ? 'rgba(52,211,153,0.2)' : 'var(--surface)';
          html += `<div style="width:50px; height:50px; display:flex; flex-direction:column; align-items:center; justify-content:center; border:${border}; background:${bg};">
             <div style="font-size:10px; color:var(--text-dim);">${s.grid[i][j]}</div>
             <div style="font-weight:bold;">${s.memo[i][j] || ''}</div>
          </div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
