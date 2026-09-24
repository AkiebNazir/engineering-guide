import sys

content = """
defineAlgo('17_dp_2d', {
  title: 'Unique Paths II', short: 'Unique Paths II',
  idea: 'Same as Unique Paths, but with obstacles. If a cell has an obstacle `obstacleGrid[i][j] == 1`, `dp[i][j] = 0`. Otherwise, `dp[i][j] = dp[i-1][j] + dp[i][j-1]`.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: '0,0,0; 0,1,0; 0,0,0', hint: 'comma-separated rows of 0s and 1s',
  code: [
    'def uniquePathsWithObstacles(obstacleGrid):',
    '    m, n = len(obstacleGrid), len(obstacleGrid[0])',
    '    dp = [[0] * n for _ in range(m)]',
    '    ',
    '    for i in range(m):',
    '        for j in range(n):',
    '            if obstacleGrid[i][j] == 1:',
    '                dp[i][j] = 0',
    '            elif i == 0 and j == 0:',
    '                dp[i][j] = 1',
    '            else:',
    '                up = dp[i-1][j] if i > 0 else 0',
    '                left = dp[i][j-1] if j > 0 else 0',
    '                dp[i][j] = up + left',
    '                ',
    '    return dp[m-1][n-1]',
  ],
  parse(str) {
    const rows = str.split(';');
    const grid = rows.map(r => r.split(',').map(Number));
    if (!grid.length || !grid[0].length) throw new Error("Invalid grid");
    return { grid, m: grid.length, n: grid[0].length };
  },
  run({ grid, m, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: m}, () => new Array(n).fill(0));
    const s = { grid, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    
    snap(3, `Initialize ${m}x${n} DP table with 0s.`, s);
    
    for (let i = 0; i < m; i++) {
       for (let j = 0; j < n; j++) {
          s.i = i; s.j = j;
          if (grid[i][j] === 1) {
             dp[i][j] = 0;
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(8, `Cell (${i}, ${j}) is an obstacle. dp[${i}][${j}] = 0.`, s);
          } else if (i === 0 && j === 0) {
             dp[i][j] = 1;
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(10, `Start cell (0, 0) has 1 path. dp[0][0] = 1.`, s);
          } else {
             const up = i > 0 ? dp[i-1][j] : 0;
             const left = j > 0 ? dp[i][j-1] : 0;
             dp[i][j] = up + left;
             s.dp = JSON.parse(JSON.stringify(dp));
             snap(14, `No obstacle. dp[${i}][${j}] = dp[${i-1 < 0 ? 'out' : i-1}][${j}] (${up}) + dp[${i}][${j-1 < 0 ? 'out' : j-1}] (${left}) = ${dp[i][j]}.`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(16, `Finished. Paths to bottom-right = ${dp[m-1][n-1]}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px; margin-top: 10px;">';
       for (let r = 0; r < s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          for (let c = 0; c < s.n; c++) {
             const isObs = s.grid[r][c] === 1;
             const isCurrent = s.i === r && s.j === c;
             const isAbove = s.i !== null && r === s.i - 1 && c === s.j;
             const isLeft = s.j !== null && r === s.i && c === s.j - 1;
             
             let bg = isObs ? 'rgba(239, 68, 68, 0.2)' : 'var(--surface)';
             let border = '1px solid var(--border)';
             let textCol = isObs ? '#ef4444' : 'var(--text)';
             
             if (isCurrent) { border = '2px solid var(--accent)'; bg = isObs ? 'rgba(239, 68, 68, 0.3)' : 'rgba(56, 189, 248, 0.1)'; }
             else if (!isObs && (isAbove || isLeft)) { border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
             
             html += `
             <div style="width: 44px; height: 44px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: ${textCol}; font-family: var(--mono); border-radius: 6px; font-weight: ${isCurrent || isAbove || isLeft ? 'bold' : 'normal'};">
                ${isObs ? 'X' : s.dp[r][c]}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px;">
        <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table (Obstacles marked X)</div>
        ${getGridHTML()}
    </div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Minimum Path Sum', short: 'Min Path Sum',
  idea: '`dp[i][j]` is the minimum cost to reach `(i, j)`. It is the cell cost plus the minimum of reaching the cell above or left: `dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])`.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: '1,3,1; 1,5,1; 4,2,1', hint: 'comma-separated row costs',
  code: [
    'def minPathSum(grid):',
    '    m, n = len(grid), len(grid[0])',
    '    dp = [[0] * n for _ in range(m)]',
    '    ',
    '    for i in range(m):',
    '        for j in range(n):',
    '            if i == 0 and j == 0:',
    '                dp[i][j] = grid[i][j]',
    '            elif i == 0:',
    '                dp[i][j] = dp[i][j-1] + grid[i][j]',
    '            elif j == 0:',
    '                dp[i][j] = dp[i-1][j] + grid[i][j]',
    '            else:',
    '                dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])',
    '                ',
    '    return dp[m-1][n-1]',
  ],
  parse(str) {
    const rows = str.split(';');
    const grid = rows.map(r => r.split(',').map(Number));
    return { grid, m: grid.length, n: grid[0].length };
  },
  run({ grid, m, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: m}, () => new Array(n).fill(0));
    const s = { grid, m, n, dp: JSON.parse(JSON.stringify(dp)), i: null, j: null };
    
    snap(3, `Initialize DP table.`, s);
    
    for (let i = 0; i < m; i++) {
       for (let j = 0; j < n; j++) {
          s.i = i; s.j = j;
          if (i === 0 && j === 0) {
             dp[i][j] = grid[i][j];
          } else if (i === 0) {
             dp[i][j] = dp[i][j-1] + grid[i][j];
          } else if (j === 0) {
             dp[i][j] = dp[i-1][j] + grid[i][j];
          } else {
             dp[i][j] = grid[i][j] + Math.min(dp[i-1][j], dp[i][j-1]);
          }
          s.dp = JSON.parse(JSON.stringify(dp));
          snap(13, `Cost for cell (${i}, ${j}) is ${grid[i][j]}. Total min path = ${dp[i][j]}.`, s);
       }
    }
    
    s.i = null; s.j = null;
    snap(15, `Min path sum = ${dp[m-1][n-1]}.`, s);
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
             
             let bg = 'var(--surface)'; let border = '1px solid var(--border)';
             if (isCurrent) { border = '2px solid var(--accent)'; bg = 'rgba(56, 189, 248, 0.1)'; }
             else if (isAbove || isLeft) { border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
             
             html += `
             <div style="width: 50px; height: 50px; display:flex; flex-direction:column; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: var(--text); font-family: var(--mono); border-radius: 6px;">
                <div style="font-size: 10px; color: var(--text-dim); margin-bottom: 2px;">+${s.grid[r][c]}</div>
                <div style="font-weight: ${isCurrent ? 'bold' : 'normal'};">${s.dp[r][c] || ''}</div>
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px;">
        <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table (Top = Cell Cost, Bottom = Total Cost)</div>
        ${getGridHTML()}
    </div>`;
  }
});

defineAlgo('17_dp_2d', {
  title: 'Maximal Square', short: 'Maximal Square',
  idea: '`dp[i][j]` is the side length of the max square whose bottom-right corner is at `(i, j)`. If `matrix[i][j] == "1"`, `dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1`. We track the max seen.',
  complexity: 'Time O(m*n) · Space O(m*n)',
  input: '1,0,1,0,0; 1,0,1,1,1; 1,1,1,1,1; 1,0,0,1,0', hint: 'comma-separated rows of 0s and 1s',
  code: [
    'def maximalSquare(matrix):',
    '    m, n = len(matrix), len(matrix[0])',
    '    dp = [[0] * (n + 1) for _ in range(m + 1)]',
    '    max_side = 0',
    '    ',
    '    for i in range(1, m + 1):',
    '        for j in range(1, n + 1):',
    '            if matrix[i-1][j-1] == "1":',
    '                dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1',
    '                max_side = max(max_side, dp[i][j])',
    '                ',
    '    return max_side * max_side',
  ],
  parse(str) {
    const rows = str.split(';');
    const matrix = rows.map(r => r.split(',').map(x => x.trim()));
    return { matrix, m: matrix.length, n: matrix[0].length };
  },
  run({ matrix, m, n }) {
    const { F, snap } = avRecorder();
    let dp = Array.from({length: m + 1}, () => new Array(n + 1).fill(0));
    let max_side = 0;
    const s = { matrix, m, n, dp: JSON.parse(JSON.stringify(dp)), max_side, i: null, j: null };
    
    snap(3, `Initialize DP table with extra row/col of 0s.`, s);
    
    for (let i = 1; i <= m; i++) {
       for (let j = 1; j <= n; j++) {
          s.i = i; s.j = j;
          if (matrix[i-1][j-1] === "1") {
             dp[i][j] = Math.min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1;
             max_side = Math.max(max_side, dp[i][j]);
             s.dp = JSON.parse(JSON.stringify(dp));
             s.max_side = max_side;
             snap(9, `matrix[${i-1}][${j-1}] == "1". min(top, left, diag-top-left) + 1 = min(${dp[i-1][j]}, ${dp[i][j-1]}, ${dp[i-1][j-1]}) + 1 = ${dp[i][j]}. Max side is now ${max_side}.`, s);
          } else {
             snap(8, `matrix[${i-1}][${j-1}] == "0", skip. dp[${i}][${j}] = 0.`, s);
          }
       }
    }
    
    s.i = null; s.j = null;
    snap(12, `Max side length is ${max_side}. Area = ${max_side * max_side}.`, s);
    return F;
  },
  renderDOM(container, s, spec) {
    const getGridHTML = () => {
       let html = '<div style="display:flex; flex-direction:column; gap:4px; margin-top: 10px;">';
       for (let r = 1; r <= s.m; r++) {
          html += '<div style="display:flex; gap:4px;">';
          for (let c = 1; c <= s.n; c++) {
             const isCurrent = s.i === r && s.j === c;
             const isNeighbor = s.i !== null && s.j !== null && ((r === s.i-1 && c === s.j) || (r === s.i && c === s.j-1) || (r === s.i-1 && c === s.j-1));
             const isOne = s.matrix[r-1][c-1] === "1";
             
             let bg = isOne ? 'var(--surface)' : 'rgba(0,0,0,0.1)';
             let border = '1px solid var(--border)';
             let color = isOne ? 'var(--text)' : 'transparent';
             
             if (isCurrent) { border = '2px solid var(--accent)'; bg = isOne ? 'rgba(56, 189, 248, 0.1)' : bg; }
             else if (isNeighbor) { border = '2px solid #34d399'; bg = 'rgba(52, 211, 153, 0.1)'; }
             
             html += `
             <div style="width: 36px; height: 36px; display:flex; align-items:center; justify-content:center; border: ${border}; background: ${bg}; color: ${color}; font-family: var(--mono); border-radius: 4px; font-weight: ${isCurrent ? 'bold' : 'normal'};">
                ${s.dp[r][c] || ''}
             </div>`;
          }
          html += '</div>';
       }
       html += '</div>';
       return html;
    };
    
    container.innerHTML = `<div style="display:flex; flex-direction:column; align-items:center; width: 100%; padding: 10px;">
        <div style="color: var(--accent); font-weight: 600; font-size: 14px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 5px;">DP Table (Side length of square)</div>
        ${getGridHTML()}
        <div style="margin-top:10px; font-weight: bold; color: #34d399;">Max Side Length Found: ${s.max_side}</div>
    </div>`;
  }
});
"""

with open('webapp/static/dsa-viz.js', 'a') as f:
    f.write("\n" + content)
print("Done appending batch 1.")
