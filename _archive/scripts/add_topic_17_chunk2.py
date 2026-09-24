import sys

content = """
defineAlgo('17_dp_2d', {
  title: 'Distinct Subsequences', short: 'Distinct Subsequences',
  idea: '`dp[i][j]` is the number of distinct subsequences of `s[:i]` that equal `t[:j]`. If `s[i-1] == t[j-1]`, we can either use it (`dp[i-1][j-1]`) or not use it (`dp[i-1][j]`). If mismatch, we can only not use it.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: 'rabbbit, rabbit', hint: 's, t',
  code: [
    'def numDistinct(s, t):',
    '    m, n = len(s), len(t)',
    '    dp = [[0] * (n + 1) for _ in range(m + 1)]',
    '    for i in range(m + 1): dp[i][0] = 1',
    '    ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            if s[i-1] == t[j-1]:',
    '                dp[i][j] = dp[i-1][j-1] + dp[i-1][j]',
    '            else:',
    '                dp[i][j] = dp[i-1][j]',
    '                ',
    '    return dp[m][n]'
  ],
  parse(str) {
    const parts = str.split(',');
    return { s_str: parts[0].trim(), t_str: parts[1].trim() };
  },
  run({ s_str, t_str }) {
    const { F, snap } = avRecorder();
    const m = s_str.length, n = t_str.length;
    let dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    for (let i = 0; i <= m; i++) dp[i][0] = 1;
    
    const s = { s_str, t_str, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(4, 'Initialize DP table. Base case: empty t has 1 subsequence in any s.', s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          if (s_str[i-1] === t_str[j-1]) {
             dp[i][j] = dp[i-1][j-1] + dp[i-1][j];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(9, `Match! Use (${dp[i-1][j-1]}) + Don't use (${dp[i-1][j]}) = ${dp[i][j]}`, s);
          } else {
             dp[i][j] = dp[i-1][j];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Mismatch. Can't use. Take from above = ${dp[i][j]}`, s);
          }
       }
    }
    s.i = null; s.j = null;
    snap(13, `Total subsequences = ${dp[m][n]}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    html += '<div style="display:flex; gap:4px;"><div style="width:36px;"></div><div style="width:36px;text-align:center;">""</div>';
    for (let j = 0; j < state.n; j++) html += `<div style="width:36px; text-align:center; font-weight:bold;">${state.t_str[j]}</div>`;
    html += '</div>';
    
    for (let i = 0; i <= state.m; i++) {
       html += '<div style="display:flex; gap:4px;">';
       html += `<div style="width:36px; font-weight:bold; display:flex; align-items:center;">${i===0 ? '""' : state.s_str[i-1]}</div>`;
       for (let j = 0; j <= state.n; j++) {
          const isCurr = state.i === i && state.j === j;
          html += `<div style="width:36px; height:36px; display:flex; align-items:center; justify-content:center; border:1px solid var(--border); ${isCurr?'border:2px solid var(--accent); background:rgba(56,189,248,0.1);':''}">${state.dp[i][j]}</div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Burst Balloons', short: 'Burst Balloons',
  idea: 'Interval DP. `dp[left][right]` is max coins from bursting balloons in `(left, right)`. We try each balloon `i` as the LAST balloon to burst.',
  complexity: 'Time O(N^3) · Space O(N^2)',
  input: '3,1,5,8', hint: 'comma-separated balloons',
  code: [
    'def maxCoins(nums):',
    '    nums = [1] + nums + [1]',
    '    n = len(nums)',
    '    dp = [[0] * n for _ in range(n)]',
    '    ',
    '    for length in range(2, n):',
    '        for left in range(n - length):',
    '            right = left + length',
    '            for i in range(left + 1, right):',
    '                coins = nums[left] * nums[i] * nums[right]',
    '                coins += dp[left][i] + dp[i][right]',
    '                dp[left][right] = max(dp[left][right], coins)',
    '                ',
    '    return dp[0][n - 1]'
  ],
  parse(str) {
    return { nums: str.split(',').map(Number) };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    nums = [1, ...nums, 1];
    const n = nums.length;
    let dp = Array.from({length: n}, () => new Array(n).fill(0));
    const s = { nums, n, dp: JSON.parse(JSON.stringify(dp)), left: null, right: null, i: null };
    
    snap(4, 'Padded array with 1s at ends.', s);
    
    for (let length = 2; length < n; length++) {
       for (let left = 0; left < n - length; left++) {
          let right = left + length;
          s.left = left; s.right = right;
          for (let i = left + 1; i < right; i++) {
             s.i = i;
             let coins = nums[left] * nums[i] * nums[right];
             coins += dp[left][i] + dp[i][right];
             dp[left][right] = Math.max(dp[left][right], coins);
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Interval (${left}, ${right}). Balloon ${i} burst last. Coins = ${coins}. dp[${left}][${right}] = ${dp[left][right]}.`, s);
          }
       }
    }
    
    s.left = null; s.right = null; s.i = null;
    snap(14, `Done. Max coins = ${dp[0][n-1]}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; gap:4px; margin-bottom:10px;">';
    for (let i=0; i<state.n; i++) {
       html += `<div style="width:40px; text-align:center; ${i===0||i===state.n-1?'color:var(--text-dim);':''}">${state.nums[i]}</div>`;
    }
    html += '</div>';
    
    html += '<div style="display:flex; flex-direction:column; gap:4px;">';
    for (let r=0; r<state.n; r++) {
       html += '<div style="display:flex; gap:4px;">';
       for (let c=0; c<state.n; c++) {
          let isCurr = state.left === r && state.right === c;
          let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
          let bg = state.dp[r][c] > 0 ? 'rgba(52,211,153,0.1)' : 'var(--surface)';
          html += `<div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg};">${state.dp[r][c] || ''}</div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Regular Expression Matching', short: 'RegEx Match',
  idea: '`dp[i][j]` is true if `s[:i]` matches `p[:j]`. Handles `.` (any char) and `*` (0 or more of preceding char).',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: 'aab, c*a*b', hint: 's, p',
  code: [
    'def isMatch(s, p):',
    '    m, n = len(s), len(p)',
    '    dp = [[False] * (n + 1) for _ in range(m + 1)]',
    '    dp[0][0] = True',
    '    for j in range(1, n + 1):',
    '        if p[j-1] == "*":',
    '            dp[0][j] = dp[0][j-2]',
    '    ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            if p[j-1] == s[i-1] or p[j-1] == ".":',
    '                dp[i][j] = dp[i-1][j-1]',
    '            elif p[j-1] == "*":',
    '                dp[i][j] = dp[i][j-2]',
    '                if p[j-2] == s[i-1] or p[j-2] == ".":',
    '                    dp[i][j] = dp[i][j] or dp[i-1][j]',
    '                    ',
    '    return dp[m][n]'
  ],
  parse(str) {
    const parts = str.split(',');
    return { s_str: parts[0].trim(), p_str: parts[1].trim() };
  },
  run({ s_str, p_str }) {
    const { F, snap } = avRecorder();
    const m = s_str.length, n = p_str.length;
    let dp = Array.from({length: m+1}, () => new Array(n+1).fill(false));
    dp[0][0] = true;
    for (let j = 1; j <= n; j++) {
       if (p_str[j-1] === '*') dp[0][j] = dp[0][j-2];
    }
    const s = { s_str, p_str, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(5, 'Initialize DP. Handled patterns like c* matching empty string.', s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          if (p_str[j-1] === s_str[i-1] || p_str[j-1] === '.') {
             dp[i][j] = dp[i-1][j-1];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Match! dp[${i}][${j}] = ${dp[i][j]}`, s);
          } else if (p_str[j-1] === '*') {
             dp[i][j] = dp[i][j-2]; // 0 occurrences
             if (p_str[j-2] === s_str[i-1] || p_str[j-2] === '.') {
                dp[i][j] = dp[i][j] || dp[i-1][j]; // 1+ occurrences
             }
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(15, `* wildcard. 0 occ: ${dp[i][j-2]}, 1+ occ: ${dp[i-1][j]}. Result: ${dp[i][j]}`, s);
          } else {
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(10, `Mismatch. dp[${i}][${j}] = false`, s);
          }
       }
    }
    s.i = null; s.j = null;
    snap(17, `Match Result = ${dp[m][n]}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    html += '<div style="display:flex; gap:4px;"><div style="width:36px;"></div><div style="width:36px;text-align:center;">""</div>';
    for (let j=0; j<state.n; j++) html += `<div style="width:36px; text-align:center; font-weight:bold;">${state.p_str[j]}</div>`;
    html += '</div>';
    
    for (let i=0; i<=state.m; i++) {
       html += '<div style="display:flex; gap:4px;">';
       html += `<div style="width:36px; font-weight:bold; display:flex; align-items:center;">${i===0?'""':state.s_str[i-1]}</div>`;
       for (let j=0; j<=state.n; j++) {
          let isCurr = state.i === i && state.j === j;
          let bg = state.dp[i][j] ? 'rgba(52,211,153,0.2)' : 'var(--surface)';
          let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
          html += `<div style="width:36px; height:36px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg};">${state.dp[i][j]?'T':'F'}</div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Longest Palindromic Subsequence', short: 'LPS',
  idea: 'Interval DP. `dp[i][j]` is LPS in `s[i:j+1]`. If `s[i] == s[j]`, `dp[i][j] = 2 + dp[i+1][j-1]`. Else `max(dp[i+1][j], dp[i][j-1])`.',
  complexity: 'Time O(N^2) · Space O(N^2)',
  input: 'bbbab', hint: 'string s',
  code: [
    'def longestPalindromeSubseq(s):',
    '    n = len(s)',
    '    dp = [[0] * n for _ in range(n)]',
    '    ',
    '    for i in range(n):',
    '        dp[i][i] = 1',
    '        ',
    '    for length in range(2, n + 1):',
    '        for i in range(n - length + 1):',
    '            j = i + length - 1',
    '            if s[i] == s[j]:',
    '                dp[i][j] = 2 + (dp[i+1][j-1] if i+1 <= j-1 else 0)',
    '            else:',
    '                dp[i][j] = max(dp[i+1][j], dp[i][j-1])',
    '                ',
    '    return dp[0][n-1]'
  ],
  parse(str) {
    return { str: str.trim(), n: str.trim().length };
  },
  run({ str, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: n}, () => new Array(n).fill(0));
    for(let i=0; i<n; i++) dp[i][i] = 1;
    
    const s = { str, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(5, 'Base cases: length 1 strings are palindromes of length 1.', s);
    
    for (let length = 2; length <= n; length++) {
       for (let i = 0; i < n - length + 1; i++) {
          let j = i + length - 1;
          s.i = i; s.j = j;
          if (str[i] === str[j]) {
             dp[i][j] = 2 + (i+1 <= j-1 ? dp[i+1][j-1] : 0);
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Match! s[${i}] == s[${j}]. dp = 2 + dp[${i+1}][${j-1}] = ${dp[i][j]}`, s);
          } else {
             dp[i][j] = Math.max(dp[i+1][j], dp[i][j-1]);
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(13, `Mismatch. max(dp[${i+1}][${j}], dp[${i}][${j-1}]) = ${dp[i][j]}`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(15, `LPS length = ${dp[0][n-1]}`, s);
    return F;
  },
  renderDOM(container, state, spec) {
    let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
    for(let i=0; i<state.n; i++) {
       html += '<div style="display:flex; gap:4px;">';
       for(let j=0; j<state.n; j++) {
          let isCurr = state.i === i && state.j === j;
          let border = isCurr ? '2px solid var(--accent)' : '1px solid var(--border)';
          let bg = state.dp[i][j] > 0 ? 'rgba(56,189,248,0.1)' : 'var(--surface)';
          let content = j >= i ? state.dp[i][j] : '';
          html += `<div style="width:36px; height:36px; display:flex; align-items:center; justify-content:center; border:${border}; background:${bg};">${content}</div>`;
       }
       html += '</div>';
    }
    html += '</div>';
    container.innerHTML = `<div style="padding:10px; overflow-x:auto;">${html}</div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
