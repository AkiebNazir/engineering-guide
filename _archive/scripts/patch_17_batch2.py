import sys

content = """
defineAlgo('17_dp_2d', {
  title: 'Edit Distance', short: 'Edit Distance',
  idea: '`dp[i][j]` is the minimum operations to convert `word1[:i]` to `word2[:j]`. If characters match, `dp[i][j] = dp[i-1][j-1]`. If they mismatch, try insert, delete, or replace: `dp[i][j] = 1 + min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1])`.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: 'horse, ros', hint: 'word1, word2',
  code: [
    'def minDistance(word1, word2):',
    '    m, n = len(word1), len(word2)',
    '    dp = [[0] * (n + 1) for _ in range(m + 1)]',
    '    ',
    '    for i in range(m + 1): dp[i][0] = i',
    '    for j in range(n + 1): dp[0][j] = j',
    '    ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            if word1[i-1] == word2[j-1]:',
    '                dp[i][j] = dp[i-1][j-1]',
    '            else:',
    '                dp[i][j] = 1 + min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1])',
    '                ',
    '    return dp[m][n]',
  ],
  parse(str) {
    const parts = str.split(',');
    const word1 = parts[0].trim();
    const word2 = parts[1].trim();
    return { word1, word2, m: word1.length, n: word2.length };
  },
  run({ word1, word2, m, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    
    for (let i = 0; i <= m; i++) dp[i][0] = i;
    for (let j = 0; j <= n; j++) dp[0][j] = j;
    
    const s = { word1, word2, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(6, `Initialize DP table. Base cases: empty string to string of length k takes k inserts/deletes.`, s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          if (word1[i-1] === word2[j-1]) {
             dp[i][j] = dp[i-1][j-1];
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(11, `Characters match ('${word1[i-1]}'). No operation needed. dp[${i}][${j}] = dp[${i-1}][${j-1}] = ${dp[i][j]}.`, s);
          } else {
             dp[i][j] = 1 + Math.min(dp[i][j-1], dp[i-1][j], dp[i-1][j-1]);
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(13, `Mismatch ('${word1[i-1]}' vs '${word2[j-1]}'). 1 + min(insert:${dp[i][j-1]}, delete:${dp[i-1][j]}, replace:${dp[i-1][j-1]}) = ${dp[i][j]}.`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(15, `Minimum operations = ${dp[m][n]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
       
       html += '<div style="display:flex; gap:4px;">';
       html += '<div style="width: 36px; height: 30px;"></div><div style="width: 36px; height: 30px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); color: var(--text-dim);">""</div>';
       for (let j = 0; j < s.n; j++) {
          html += `<div style="width: 36px; height: 30px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold; color: ${s.j !== null && j === s.j - 1 ? 'var(--accent)' : 'var(--text)'};">${s.word2[j]}</div>`;
       }
       html += '</div>';
       
       for (let r = 0; r <= s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          const char = r === 0 ? '""' : s.word1[r-1];
          html += `<div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold; color: ${s.i !== null && r === s.i ? 'var(--accent)' : 'var(--text-dim)'};">${char}</div>`;
          
          for (let c = 0; c <= s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             const isNeighbor = s.i !== null && s.j !== null && ((r === s.i-1 && c === s.j) || (r === s.i && c === s.j-1) || (r === s.i-1 && c === s.j-1));
             
             let bg = 'var(--surface)'; let border = '1px solid var(--border)';
             if (isCurrent) { border = '2px solid var(--accent)'; bg = 'rgba(56, 189, 248, 0.1)'; }
             else if (isNeighbor) { border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
             
             html += `
             <div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: var(--text); font-family: var(--mono); border-radius: 4px; font-weight: ${isCurrent ? 'bold' : 'normal'};">
                ${s.dp[r][c]}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px; overflow-x: auto;">
        <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table</div>
        ${getGridHTML()}
    </div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending batch 2.")
