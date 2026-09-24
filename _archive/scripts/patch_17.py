import sys

content = """
defineAlgo('17_dp_2d', {
  title: 'Unique Paths', short: 'Unique Paths',
  idea: '2D DP. `dp[i][j]` is the number of ways to reach cell `(i, j)`. You can only come from `(i-1, j)` (above) or `(i, j-1)` (left). So `dp[i][j] = dp[i-1][j] + dp[i][j-1]`. The first row and column are all 1s.',
  complexity: 'Time O(m*n) · Space O(m*n) (or O(n) optimized)',
  input: '3, 4', hint: 'm, n',
  code: [
    'def uniquePaths(m, n):',
    '    dp = [[1] * n for _ in range(m)]',
    '    ',
    '    for i in range(1, m):',
    '        for j in range(1, n):',
    '            dp[i][j] = dp[i-1][j] + dp[i][j-1]',
    '            ',
    '    return dp[m-1][n-1]',
  ],
  parse(str) {
    const parts = str.split(',').map(Number);
    if (parts.length !== 2 || isNaN(parts[0]) || isNaN(parts[1])) throw new Error("Input must be m, n (e.g., '3, 4').");
    const [m, n] = parts;
    if (m < 1 || n < 1 || m > 10 || n > 10) throw new Error("m and n must be between 1 and 10 for visualization.");
    return { m, n };
  },
  run({ m, n }) {
    const { F, snap } = avRecorder();
    
    // Create 2D DP array
    let dp = Array.from({length: m}, () => new Array(n).fill(1));
    
    const s = { m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(2, `Initialize a ${m}x${n} DP table with all 1s (base cases for top row and left col).`, s);
    
    for (let i = 1; i < m; i++) {
       for (let j = 1; j < n; j++) {
          s.i = i; s.j = j;
          snap(5, `Calculate ways to reach cell (${i}, ${j}).`, s);
          
          dp[i][j] = dp[i-1][j] + dp[i][j-1];
          s.dp = JSON.parse(JSON.stringify(dp));
          
          snap(6, `dp[${i}][${j}] = dp[${i-1}][${j}] (${dp[i-1][j]}) + dp[${i}][${j-1}] (${dp[i][j-1]}) = ${dp[i][j]}.`, s);
       }
    }
    
    s.i = null; s.j = null;
    snap(8, `Finished. The total unique paths to the bottom-right corner is dp[${m-1}][${n-1}] = ${dp[m-1][n-1]}.`, s);
    
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px; margin-top: 10px;">';
       for (let r = 0; r < s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          for (let c = 0; c < s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             const isAbove = s.i !== null && r === s.i - 1 && c === s.j;
             const isLeft = s.j !== null && r === s.i && c === s.j - 1;
             
             let bg = 'var(--surface)';
             let border = '1px solid var(--border)';
             
             if (isCurrent) { border = '2px solid var(--accent)'; bg = 'rgba(56, 189, 248, 0.1)'; }
             else if (isAbove || isLeft) { border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
             
             html += `
             <div style="width: 44px; height: 44px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: var(--text); font-family: var(--mono); border-radius: 6px; font-weight: ${isCurrent || isAbove || isLeft ? 'bold' : 'normal'};">
                ${s.dp[r][c]}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px;">
          <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table (Grid)</div>
          ${getGridHTML()}
          
          <div style="margin-top: 20px; font-family: var(--mono); color: var(--text-dim); font-size: 13px;">
             ${s.i !== null && s.j !== null ? 
                `dp[${s.i}][${s.j}] = dp[${s.i-1}][${s.j}] + dp[${s.i}][${s.j-1}]` : 
                'Robot starts at top-left, wants to go to bottom-right.'}
          </div>
      </div>
    `;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Longest Common Subsequence', short: 'LCS',
  idea: '2D DP over two strings. `dp[i][j]` is the LCS of `text1[:i]` and `text2[:j]`. If characters match, `dp[i][j] = dp[i-1][j-1] + 1`. If not, `dp[i][j] = max(dp[i-1][j], dp[i][j-1])`. Note: indices are 1-based to allow for empty prefixes.',
  complexity: 'Time O(m*n) · Space O(m*n) (or O(min(m,n)) optimized)',
  input: 'abcde, ace', hint: 'text1, text2',
  code: [
    'def longestCommonSubsequence(text1, text2):',
    '    m, n = len(text1), len(text2)',
    '    dp = [[0] * (n + 1) for _ in range(m + 1)]',
    '    ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            if text1[i-1] == text2[j-1]:',
    '                dp[i][j] = dp[i-1][j-1] + 1',
    '            else:',
    '                dp[i][j] = max(dp[i-1][j], dp[i][j-1])',
    '                ',
    '    return dp[m][n]',
  ],
  parse(str) {
    const parts = str.split(',');
    if (parts.length !== 2) throw new Error("Input must be two strings separated by a comma.");
    const text1 = parts[0].trim();
    const text2 = parts[1].trim();
    if (text1.length > 10 || text2.length > 10) throw new Error("Strings must be <= 10 characters for visualization.");
    return { text1, text2 };
  },
  run({ text1, text2 }) {
    const { F, snap } = avRecorder();
    
    const m = text1.length;
    const n = text2.length;
    let dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    
    const s = { text1, text2, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(3, `Initialize a ${m+1}x${n+1} DP table with 0s (empty prefixes have 0 LCS).`, s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          snap(6, `Compare text1[${i-1}]='${text1[i-1]}' and text2[${j-1}]='${text2[j-1]}'.`, s);
          
          if (text1[i-1] === text2[j-1]) {
             dp[i][j] = dp[i-1][j-1] + 1;
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(7, `Characters match! dp[${i}][${j}] = dp[${i-1}][${j-1}] (${dp[i-1][j-1]}) + 1 = ${dp[i][j]}.`, s);
          } else {
             dp[i][j] = Math.max(dp[i-1][j], dp[i][j-1]);
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(9, `Mismatch. dp[${i}][${j}] = max(dp[${i-1}][${j}], dp[${i}][${j-1}]) = max(${dp[i-1][j]}, ${dp[i][j-1]}) = ${dp[i][j]}.`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(11, `Finished. Longest Common Subsequence length is ${dp[m][n]}.`, s);
    
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
       
       // Header row (text2)
       html += '<div style="display:flex; gap:4px;">';
       html += '<div style="width: 40px; height: 30px;"></div>'; // Empty corner
       html += '<div style="width: 40px; height: 30px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); color: var(--text-dim);">""</div>';
       for (let j = 0; j < s.n; j++) {
          const isActive = s.j !== null && j === s.j - 1;
          html += `<div style="width: 40px; height: 30px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold; color: ${isActive ? 'var(--accent)' : 'var(--text)'};">${s.text2[j]}</div>`;
       }
       html += '</div>';
       
       for (let r = 0; r <= s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          
          // Row header (text1)
          const char = r === 0 ? '""' : s.text1[r-1];
          const isRowActive = s.i !== null && r === s.i;
          html += `<div style="width: 40px; height: 40px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold; color: ${isRowActive && r > 0 ? 'var(--accent)' : 'var(--text-dim)'};">${char}</div>`;
          
          for (let c = 0; c <= s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             
             let bg = 'var(--surface)';
             let border = '1px solid var(--border)';
             let color = r === 0 || c === 0 ? 'var(--text-dim)' : 'var(--text)';
             
             if (isCurrent) { 
                 border = '2px solid var(--accent)'; 
                 bg = 'rgba(56, 189, 248, 0.1)'; 
                 color = 'var(--accent)';
             } else if (s.i !== null && s.j !== null) {
                 const match = s.text1[s.i-1] === s.text2[s.j-1];
                 const isDiag = r === s.i - 1 && c === s.j - 1;
                 const isAbove = r === s.i - 1 && c === s.j;
                 const isLeft = r === s.i && c === s.j - 1;
                 
                 if (match && isDiag) {
                     border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)';
                 } else if (!match && (isAbove || isLeft)) {
                     border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)';
                 }
             }
             
             html += `
             <div style="width: 40px; height: 40px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: ${color}; font-family: var(--mono); border-radius: 4px; font-weight: ${isCurrent ? 'bold' : 'normal'};">
                ${s.dp[r][c]}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px; overflow-x: auto;">
          <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 15px;">DP Table</div>
          ${getGridHTML()}
          
          <div style="margin-top: 20px; font-family: var(--mono); color: var(--text-dim); font-size: 13px;">
             ${s.i !== null && s.j !== null ? 
                (s.text1[s.i-1] === s.text2[s.j-1] ? 
                   `Match! dp[${s.i}][${s.j}] = dp[${s.i-1}][${s.j-1}] + 1` : 
                   `Mismatch. dp[${s.i}][${s.j}] = max(dp[${s.i-1}][${s.j}], dp[${s.i}][${s.j-1}])`) : 
                'Filling DP table to find LCS...'}
          </div>
      </div>
    `;
  }
});
"""
with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending topic 17 visualizers.")
