import sys

content = """
defineAlgo('17_dp_2d', {
  title: 'Interleaving String', short: 'Interleaving String',
  idea: '`dp[i][j]` is true if `s3[:i+j]` is formed by interleaving `s1[:i]` and `s2[:j]`. `dp[i][j] = (dp[i-1][j] and s1[i-1] == s3[i+j-1]) or (dp[i][j-1] and s2[j-1] == s3[i+j-1])`.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: 'aabcc, dbbca, aadbbcbcac', hint: 's1, s2, s3',
  code: [
    'def isInterleave(s1, s2, s3):',
    '    m, n = len(s1), len(s2)',
    '    if m + n != len(s3): return False',
    '    dp = [[False] * (n + 1) for _ in range(m + 1)]',
    '    dp[0][0] = True',
    '    ',
    '    for i in range(1, m + 1):',
    '        dp[i][0] = dp[i-1][0] and s1[i-1] == s3[i-1]',
    '    for j in range(1, n + 1):',
    '        dp[0][j] = dp[0][j-1] and s2[j-1] == s3[j-1]',
    '        ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            dp[i][j] = (dp[i-1][j] and s1[i-1] == s3[i+j-1]) or \\',
    '                       (dp[i][j-1] and s2[j-1] == s3[i+j-1])',
    '                       ',
    '    return dp[m][n]',
  ],
  parse(str) {
    const parts = str.split(',');
    if (parts.length !== 3) throw new Error("Need s1, s2, s3");
    const s1 = parts[0].trim(), s2 = parts[1].trim(), s3 = parts[2].trim();
    if (s1.length + s2.length !== s3.length) throw new Error("Lengths must match");
    return { s1, s2, s3, m: s1.length, n: s2.length };
  },
  run({ s1, s2, s3, m, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(false));
    dp[0][0] = true;
    
    for (let i = 1; i <= m; i++) dp[i][0] = dp[i-1][0] && s1[i-1] === s3[i-1];
    for (let j = 1; j <= n; j++) dp[0][j] = dp[0][j-1] && s2[j-1] === s3[j-1];
    
    const s = { s1, s2, s3, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    snap(5, `Initialize DP table and base cases (0th row and 0th column).`, s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          const match1 = dp[i-1][j] && s1[i-1] === s3[i+j-1];
          const match2 = dp[i][j-1] && s2[j-1] === s3[i+j-1];
          dp[i][j] = match1 || match2;
          s.dp = JSON.parse(JSON.stringify(dp));
          snap(13, `s3[${i+j-1}]='${s3[i+j-1]}'. Can it come from s1='${s1[i-1]}' (top)? ${match1}. From s2='${s2[j-1]}' (left)? ${match2}. dp[${i}][${j}] = ${dp[i][j]}.`, s);
       }
    }
    
    s.i = null; s.j = null;
    snap(16, `Result = ${dp[m][n]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px;">';
       
       html += '<div style="display:flex; gap:4px;">';
       html += '<div style="width: 36px; height: 30px;"></div><div style="width: 36px; height: 30px;"></div>';
       for (let j = 0; j < s.n; j++) {
          html += `<div style="width: 36px; height: 30px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold;">${s.s2[j]}</div>`;
       }
       html += '</div>';
       
       for (let r = 0; r <= s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          const char = r === 0 ? '""' : s.s1[r-1];
          html += `<div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; font-family: var(--mono); font-weight: bold;">${char}</div>`;
          
          for (let c = 0; c <= s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             const isNeighbor = s.i !== null && s.j !== null && ((r === s.i-1 && c === s.j) || (r === s.i && c === s.j-1));
             
             let bg = s.dp[r][c] ? 'rgba(52, 211, 153, 0.2)' : 'var(--surface)'; 
             let border = '1px solid var(--border)';
             if (isCurrent) { border = '2px solid var(--accent)'; }
             else if (isNeighbor) { border = '2px solid #34d399'; }
             
             html += `
             <div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: var(--text); font-family: var(--mono); border-radius: 4px;">
                ${s.dp[r][c] ? 'T' : 'F'}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px; overflow-x: auto;">
        <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table (T/F)</div>
        ${getGridHTML()}
        <div style="margin-top:10px; color: var(--text-dim);">Target s3: <b>${s.s3}</b></div>
    </div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending batch 3.")
