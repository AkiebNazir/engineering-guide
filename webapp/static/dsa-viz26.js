/* ============================================================================
   Visualizations for 24_matrix (remaining 7 — seq 003 "Spiral Matrix" already
   has a spec in dsa-viz3.js, left untouched).
   ========================================================================= */
'use strict';

/* ------------------------------------------------------- shared helpers -- */
function mtxParseGrid(s, { max = 6 } = {}) {
  const rows = String(s || '').trim().split(/[;\n]/).map(r => r.trim()).filter(Boolean)
    .map(r => r.split(/[\s,]+/).filter(Boolean).map(Number));
  if (!rows.length) throw new Error('Enter a matrix, one row per “;”');
  if (rows.some(r => r.some(v => !Number.isFinite(v)))) throw new Error('Every cell must be a number');
  if (rows.some(r => r.length !== rows[0].length)) throw new Error('Every row needs the same number of cells');
  if (rows.length > max || rows[0].length > max) throw new Error(`Use at most ${max} × ${max}`);
  return rows;
}
/* draw a grid confined to a horizontal slice of the canvas (for side-by-side grids) */
function mtxDrawGridIn(ctx, P, c, leftX, widthPx, grid, style, opts = {}) {
  return avDrawGrid(ctx, P, { w: widthPx, h: c.h }, grid, style, { ...opts, left: leftX });
}

/* =================================================================== 001 · Transpose Matrix == */
defineAlgo('24_matrix', {
  title: 'Transpose Matrix', short: 'Transpose',
  idea: 'A fresh <code>n × m</code> result matrix. Every cell just swaps its row and column index: <code>result[j][i] = matrix[i][j]</code>. No cell ever depends on another, so the order of the double loop does not matter.',
  complexity: 'Time O(rows × cols) · Space O(rows × cols) for the output',
  input: '1 2 3; 4 5 6', hint: 'rows of numbers, separated by “;”',
  code: [
    'def transpose(matrix):',
    '    m, n = len(matrix), len(matrix[0])',
    '    result = [[0] * m for _ in range(n)]',
    '    for i in range(m):',
    '        for j in range(n):',
    '            result[j][i] = matrix[i][j]',
    '    return result',
  ],
  parse(s) { return { m: mtxParseGrid(s) }; },
  run({ m }) {
    const { F, snap } = avRecorder();
    const rows = m.length, cols = m[0].length;
    const result = Array.from({ length: cols }, () => Array(rows).fill(null));
    const S = (extra = {}) => ({ m, result: result.map(r => [...r]), ...extra });
    snap(3, `Result will be ${cols} × ${rows} — dimensions flip.`, S({ vars: { rows, cols } }));
    for (let i = 0; i < rows; i++) {
      for (let j = 0; j < cols; j++) {
        snap(5, `Look at matrix[${i}][${j}] = ${m[i][j]}.`, S({ src: [i, j], vars: { i, j } }));
        result[j][i] = m[i][j];
        snap(6, `Write it to result[${j}][${i}].`, S({ src: [i, j], dst: [j, i], vars: { i, j, value: m[i][j] } }));
      }
    }
    snap(7, 'Every cell copied once — done.', S({ done: true }));
    return F;
  },
  height: (w, last) => 40 + Math.max(last.m.length, last.m[0].length) * 44 + 60,
  draw(ctx, c, f, P) {
    const half = c.w / 2;
    const g1 = mtxDrawGridIn(ctx, P, c, 20, half - 30, f.m, (i, j) => {
      const isSrc = f.src && f.src[0] === i && f.src[1] === j;
      return { fill: isSrc ? P.alpha('accent', .45) : P.surface2, stroke: isSrc ? P.accent : null };
    }, { top: 40 });
    D.text(ctx, 'matrix', 20, 16, { color: P.dim, size: 12, weight: 700 });
    const g2 = mtxDrawGridIn(ctx, P, c, half + 10, half - 30, f.result, (i, j) => {
      const isDst = f.dst && f.dst[0] === i && f.dst[1] === j;
      const filled = f.result[i][j] !== null;
      return { fill: isDst ? P.alpha('ok', .45) : filled ? P.alpha('ok', .12) : P.alpha('faint', .07), stroke: isDst ? P.ok : null, label: f.result[i][j] === null ? '' : f.result[i][j] };
    }, { top: 40 });
    D.text(ctx, 'result', half + 10, 16, { color: P.dim, size: 12, weight: 700 });
    D.line(ctx, half, 10, half, c.h - 10, P.strong, 1);
  },
});

/* =================================================================== 002 · Rotate Image == */
defineAlgo('24_matrix', {
  title: 'Rotate Image', short: 'Rotate Image',
  idea: 'Two in-place passes, no extra grid: <b>transpose</b> across the main diagonal (swap <code>matrix[i][j]</code> with <code>matrix[j][i]</code> for <code>j &gt; i</code>), then <b>reverse every row</b>. Transpose + row-reverse together is exactly a 90° clockwise rotation.',
  complexity: 'Time O(n²) · Space O(1) — genuinely in place',
  input: '1 2 3; 4 5 6; 7 8 9', hint: 'a square (n × n) matrix, rows separated by “;”',
  code: [
    'def rotate(matrix):',
    '    n = len(matrix)',
    '    for i in range(n):',
    '        for j in range(i + 1, n):',
    '            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]',
    '    for row in matrix:',
    '        row.reverse()',
  ],
  parse(s) {
    const m = mtxParseGrid(s);
    if (m.length !== m[0].length) throw new Error('Rotate Image needs a square matrix (rows == cols)');
    return { m };
  },
  run({ m }) {
    const { F, snap } = avRecorder();
    const grid = m.map(r => [...r]);
    const n = grid.length;
    const S = (extra = {}) => ({ m: grid.map(r => [...r]), n, ...extra });
    snap(3, 'Phase 1: transpose in place — swap across the main diagonal.', S({ phase: 'transpose' }));
    for (let i = 0; i < n; i++) {
      for (let j = i + 1; j < n; j++) {
        snap(4, `Swap matrix[${i}][${j}] and matrix[${j}][${i}].`, S({ phase: 'transpose', a: [i, j], b: [j, i] }));
        [grid[i][j], grid[j][i]] = [grid[j][i], grid[i][j]];
        snap(4, `Swapped: matrix[${i}][${j}]=${grid[i][j]}, matrix[${j}][${i}]=${grid[j][i]}.`, S({ phase: 'transpose', a: [i, j], b: [j, i] }));
      }
    }
    snap(5, 'Phase 2: reverse every row.', S({ phase: 'reverse' }));
    for (let r = 0; r < n; r++) {
      let l = 0, rr = n - 1;
      while (l < rr) {
        snap(6, `Row ${r}: swap columns ${l} and ${rr}.`, S({ phase: 'reverse', a: [r, l], b: [r, rr] }));
        [grid[r][l], grid[r][rr]] = [grid[r][rr], grid[r][l]];
        l++; rr--;
      }
    }
    snap(6, 'Every row reversed — the matrix is rotated 90° clockwise.', S({ phase: 'done', done: true }));
    return F;
  },
  height: (w, last) => 40 + last.n * 48 + 70,
  draw(ctx, c, f, P) {
    const hot = new Set();
    if (f.a) hot.add(f.a.join(','));
    if (f.b) hot.add(f.b.join(','));
    const g = avDrawGrid(ctx, P, c, f.m, (i, j) => {
      const isHot = hot.has(`${i},${j}`);
      return { fill: isHot ? P.alpha('accent', .45) : P.surface2, stroke: isHot ? P.accent : null };
    }, { top: 34 });
    D.text(ctx, f.phase === 'transpose' ? 'phase 1 — transpose across the diagonal' : f.phase === 'reverse' ? 'phase 2 — reverse each row' : 'done', 20, 16, { color: P.dim, size: 12, weight: 700 });
    D.text(ctx, `matrix is mutated in place — no second grid`, 20, g.bottom + 26, { color: P.ok, size: 12, mono: true });
  },
});

/* =================================================================== 004 · Spiral Matrix II == */
defineAlgo('24_matrix', {
  title: 'Spiral Matrix II', short: 'Spiral Matrix II',
  idea: 'The mirror image of reading a spiral: keep the same four shrinking walls, but instead of reading a value out, <b>write the next counter value in</b> at each step. Same walk, opposite direction of data flow.',
  complexity: 'Time O(n²) · Space O(1) beyond the output grid',
  input: '3', hint: 'a single n (grid size), 2 – 6',
  code: [
    'def generateMatrix(n):',
    '    matrix = [[0] * n for _ in range(n)]',
    '    top, bottom, left, right = 0, n - 1, 0, n - 1',
    '    num = 1',
    '    while top <= bottom and left <= right:',
    '        for col in range(left, right + 1):',
    '            matrix[top][col] = num; num += 1',
    '        top += 1',
    '        for row in range(top, bottom + 1):',
    '            matrix[row][right] = num; num += 1',
    '        right -= 1',
    '        if top <= bottom:',
    '            for col in range(right, left - 1, -1):',
    '                matrix[bottom][col] = num; num += 1',
    '            bottom -= 1',
    '        if left <= right:',
    '            for row in range(bottom, top - 1, -1):',
    '                matrix[row][left] = num; num += 1',
    '            left += 1',
    '    return matrix',
  ],
  parse(s) {
    const n = avNum(s, 'n');
    if (n < 2 || n > 6) throw new Error('Use n between 2 and 6 for visualization');
    return { n };
  },
  run({ n }) {
    const { F, snap } = avRecorder();
    const m = Array.from({ length: n }, () => Array(n).fill(null));
    let top = 0, bottom = n - 1, left = 0, right = n - 1, num = 1;
    const S = (extra = {}) => ({ m: m.map(r => [...r]), top, bottom, left, right, ...extra });
    snap(2, `Empty ${n} × ${n} grid. Counter starts at 1.`, S({ vars: { num } }));
    while (top <= bottom && left <= right) {
      for (let col = left; col <= right; col++) { m[top][col] = num; snap(6, `Write ${num} at [${top}][${col}] — top row, left to right.`, S({ cur: [top, col], vars: { num } })); num++; }
      top++;
      for (let row = top; row <= bottom; row++) { m[row][right] = num; snap(9, `Write ${num} at [${row}][${right}] — right column, top to bottom.`, S({ cur: [row, right], vars: { num } })); num++; }
      right--;
      if (top <= bottom) {
        for (let col = right; col >= left; col--) { m[bottom][col] = num; snap(13, `Write ${num} at [${bottom}][${col}] — bottom row, right to left.`, S({ cur: [bottom, col], vars: { num } })); num++; }
        bottom--;
      }
      if (left <= right) {
        for (let row = bottom; row >= top; row--) { m[row][left] = num; snap(17, `Write ${num} at [${row}][${left}] — left column, bottom to top.`, S({ cur: [row, left], vars: { num } })); num++; }
        left++;
      }
    }
    snap(18, `All ${n * n} cells filled in spiral order.`, S({ done: true }));
    return F;
  },
  height: (w, last) => 40 + last.m.length * 48 + 60,
  draw(ctx, c, f, P) {
    const g = avDrawGrid(ctx, P, c, f.m, (i, j) => {
      const cur = f.cur && f.cur[0] === i && f.cur[1] === j;
      const filled = f.m[i][j] !== null;
      return { fill: cur ? P.alpha('accent', .45) : filled ? P.alpha('ok', .16) : P.alpha('faint', .07), stroke: cur ? P.accent : null, label: f.m[i][j] === null ? '' : f.m[i][j] };
    }, { top: 30 });
    if (f.top <= f.bottom && f.left <= f.right && !f.done) {
      const x1 = g.x(f.left) - g.cell / 2 - 5, x2 = g.x(f.right) + g.cell / 2 + 5;
      const y1 = g.y(f.top) - g.cell / 2 - 5, y2 = g.y(f.bottom) + g.cell / 2 + 5;
      ctx.strokeStyle = P.accent; ctx.lineWidth = 2; ctx.setLineDash([5, 4]);
      D.rrect(ctx, x1, y1, x2 - x1, y2 - y1, 10); ctx.stroke(); ctx.setLineDash([]);
    }
    D.text(ctx, f.done ? 'done' : `walls: top ${f.top} · bottom ${f.bottom} · left ${f.left} · right ${f.right}`, 20, g.bottom + 26, { color: P.dim, size: 12, mono: true });
  },
});

/* =================================================================== 005 · Set Matrix Zeroes == */
defineAlgo('24_matrix', {
  title: 'Set Matrix Zeroes', short: 'Set Matrix Zeroes',
  idea: 'Use <b>row 0 and column 0 themselves</b> as the marker storage instead of a separate set — O(1) extra space. Snapshot whether row 0 / col 0 originally had a zero <i>first</i> (before they get overwritten as markers), mark the interior into row 0 / col 0, zero the interior from those markers, then apply the snapshotted border decision last.',
  complexity: 'Time O(rows × cols) · Space O(1)',
  input: '1 1 1; 1 0 1; 1 1 1', hint: 'rows of numbers, separated by “;”',
  code: [
    'def setZeroes(matrix):',
    '    m, n = len(matrix), len(matrix[0])',
    '    first_row_has_zero = any(matrix[0][j] == 0 for j in range(n))',
    '    first_col_has_zero = any(matrix[i][0] == 0 for i in range(m))',
    '    for i in range(1, m):                # pass 1: mark via row0/col0',
    '        for j in range(1, n):',
    '            if matrix[i][j] == 0:',
    '                matrix[i][0] = 0; matrix[0][j] = 0',
    '    for i in range(1, m):                # pass 2: zero the interior',
    '        for j in range(1, n):',
    '            if matrix[i][0] == 0 or matrix[0][j] == 0:',
    '                matrix[i][j] = 0',
    '    if first_row_has_zero:               # pass 3: the border, last',
    '        for j in range(n): matrix[0][j] = 0',
    '    if first_col_has_zero:',
    '        for i in range(m): matrix[i][0] = 0',
  ],
  parse(s) { return { m: mtxParseGrid(s) }; },
  run({ m: input }) {
    const { F, snap } = avRecorder();
    const m = input.map(r => [...r]);
    const rows = m.length, cols = m[0].length;
    const S = (extra = {}) => ({ m: m.map(r => [...r]), ...extra });
    const firstRowHasZero = Array.from({ length: cols }, (_, j) => m[0][j] === 0).some(Boolean);
    const firstColHasZero = Array.from({ length: rows }, (_, i) => m[i][0] === 0).some(Boolean);
    snap(3, `Snapshot BEFORE row 0 / col 0 become markers: first_row_has_zero=${firstRowHasZero}, first_col_has_zero=${firstColHasZero}.`, S({ phase: 'snapshot', firstRowHasZero, firstColHasZero }));
    for (let i = 1; i < rows; i++) {
      for (let j = 1; j < cols; j++) {
        if (m[i][j] === 0) {
          m[i][0] = 0; m[0][j] = 0;
          snap(8, `matrix[${i}][${j}]=0 → mark row ${i} via matrix[${i}][0], mark col ${j} via matrix[0][${j}].`, S({ phase: 'mark', cur: [i, j], firstRowHasZero, firstColHasZero }));
        }
      }
    }
    for (let i = 1; i < rows; i++) {
      for (let j = 1; j < cols; j++) {
        if (m[i][0] === 0 || m[0][j] === 0) {
          m[i][j] = 0;
          snap(11, `Row ${i} or col ${j} is marked → zero matrix[${i}][${j}].`, S({ phase: 'zero', cur: [i, j], firstRowHasZero, firstColHasZero }));
        }
      }
    }
    if (firstRowHasZero) { for (let j = 0; j < cols; j++) m[0][j] = 0; snap(13, 'Snapshot said row 0 had a zero originally — zero all of row 0 now.', S({ phase: 'border', firstRowHasZero, firstColHasZero })); }
    if (firstColHasZero) { for (let i = 0; i < rows; i++) m[i][0] = 0; snap(15, 'Snapshot said col 0 had a zero originally — zero all of col 0 now.', S({ phase: 'border', firstRowHasZero, firstColHasZero })); }
    snap(15, 'Done — all achieved with zero extra space.', S({ phase: 'done', done: true, firstRowHasZero, firstColHasZero }));
    return F;
  },
  height: (w, last) => 40 + last.m.length * 48 + 70,
  draw(ctx, c, f, P) {
    const g = avDrawGrid(ctx, P, c, f.m, (i, j) => {
      const isCur = f.cur && f.cur[0] === i && f.cur[1] === j;
      const isMarker = (i === 0 || j === 0) && f.phase === 'mark';
      return { fill: isCur ? P.alpha('accent', .45) : (f.m[i][j] === 0 ? P.alpha('err', .25) : isMarker ? P.alpha('amber', .18) : P.surface2), stroke: isCur ? P.accent : null };
    }, { top: 30 });
    D.text(ctx, `first_row_has_zero=${f.firstRowHasZero} · first_col_has_zero=${f.firstColHasZero}`, 20, 16, { color: P.dim, size: 11.5, mono: true });
    D.text(ctx, `phase: ${f.phase}`, 20, g.bottom + 26, { color: P.ok, size: 12.5, weight: 650 });
  },
});

/* =================================================================== 006 · Search a 2D Matrix II == */
defineAlgo('24_matrix', {
  title: 'Search a 2D Matrix II', short: 'Search 2D Matrix II',
  idea: 'Start at the <b>top-right corner</b>. That cell is the largest in its row and the smallest in its column, so one comparison always eliminates a whole row or a whole column: too big → move left (drop a column), too small → move down (drop a row).',
  complexity: 'Time O(rows + cols) · Space O(1)',
  input: '1 4 7 11 | 2 5 8 12 | 3 6 9 16 | 10 13 14 17 || 5', hint: 'rows separated by “|”, then “||”, then the target',
  code: [
    'def searchMatrix(matrix, target):',
    '    m, n = len(matrix), len(matrix[0])',
    '    row, col = 0, n - 1',
    '    while row < m and col >= 0:',
    '        val = matrix[row][col]',
    '        if val == target:',
    '            return True',
    '        elif val > target:',
    '            col -= 1',
    '        else:',
    '            row += 1',
    '    return False',
  ],
  parse(s) {
    const [gridPart, targetPart] = String(s || '').split('||');
    if (targetPart === undefined) throw new Error('Add “|| target” after the matrix');
    const rows = String(gridPart || '').trim().split('|').map(r => r.trim()).filter(Boolean).map(r => r.split(/[\s,]+/).filter(Boolean).map(Number));
    if (!rows.length) throw new Error('Enter a matrix, rows separated by “|”');
    if (rows.some(r => r.some(v => !Number.isFinite(v)))) throw new Error('Every cell must be a number');
    if (rows.some(r => r.length !== rows[0].length)) throw new Error('Every row needs the same number of cells');
    if (rows.length > 6 || rows[0].length > 6) throw new Error('Use at most 6 × 6');
    const target = avNum(targetPart, 'a target');
    return { m: rows, target };
  },
  run({ m, target }) {
    const { F, snap } = avRecorder();
    const rows = m.length, cols = m[0].length;
    let row = 0, col = cols - 1;
    const S = (extra = {}) => ({ m, target, row, col, ...extra });
    snap(3, `Start at top-right corner [${row}][${col}].`, S());
    while (row < rows && col >= 0) {
      const val = m[row][col];
      snap(5, `matrix[${row}][${col}] = ${val}, comparing against target ${target}.`, S({ cur: [row, col] }));
      if (val === target) { snap(7, `${val} == ${target} — found it.`, S({ cur: [row, col], found: true })); return F; }
      else if (val > target) { snap(9, `${val} > ${target} — everything below in this column is even bigger. Drop the column.`, S({ cur: [row, col] })); col--; }
      else { snap(11, `${val} < ${target} — everything left in this row is even smaller. Drop the row.`, S({ cur: [row, col] })); row++; }
    }
    snap(12, `Ran out of rows/columns — ${target} is not in the matrix.`, S({ notFound: true }));
    return F;
  },
  height: (w, last) => 40 + last.m.length * 48 + 60,
  draw(ctx, c, f, P) {
    const g = avDrawGrid(ctx, P, c, f.m, (i, j) => {
      const isCur = f.cur && f.cur[0] === i && f.cur[1] === j;
      const eliminated = (f.cur && ((i === f.cur[0] && j > f.cur[1]) || (j === f.cur[1] && i < f.cur[0])));
      return { fill: isCur ? (f.found ? P.alpha('ok', .5) : P.alpha('accent', .45)) : eliminated ? P.alpha('faint', .05) : P.surface2, stroke: isCur ? (f.found ? P.ok : P.accent) : null };
    }, { top: 30 });
    D.text(ctx, `target: ${f.target}`, 20, 16, { color: P.dim, size: 12.5, weight: 700, mono: true });
    D.text(ctx, f.found ? 'found!' : f.notFound ? 'not found' : `row ${f.row}, col ${f.col}`, 20, g.bottom + 26, { color: f.found ? P.ok : f.notFound ? P.err : P.dim, size: 12.5, weight: 650, mono: true });
  },
});

/* =================================================================== 007 · Game of Life == */
defineAlgo('24_matrix', {
  title: 'Game of Life', short: 'Game of Life',
  idea: 'Every cell\'s next state depends on the CURRENT state of all 8 neighbors — but updating in place would corrupt that for later cells. The trick: encode both states in one number, <code>cell = old + 2·new</code>. Reading a neighbor with <code>% 2</code> always recovers its ORIGINAL bit even if that neighbor has already been re-encoded. A final <code>&gt;&gt;= 1</code> pass decodes everything to the new state — zero extra grid.',
  complexity: 'Time O(rows × cols) · Space O(1)',
  input: '0 1 0; 0 0 1; 1 1 1; 0 0 0', hint: 'rows of 0/1, separated by “;”',
  code: [
    'def gameOfLife(board):',
    '    m, n = len(board), len(board[0])',
    '    def live_neighbors(r, c):',
    '        count = 0',
    '        for dr in (-1, 0, 1):',
    '            for dc in (-1, 0, 1):',
    '                if dr == 0 and dc == 0: continue',
    '                nr, nc = r + dr, c + dc',
    '                if 0 <= nr < m and 0 <= nc < n:',
    '                    count += board[nr][nc] % 2   # original state only',
    '        return count',
    '    for i in range(m):',
    '        for j in range(n):',
    '            old, live = board[i][j], live_neighbors(i, j)',
    '            new = 1 if (old == 1 and live in (2, 3)) or (old == 0 and live == 3) else 0',
    '            board[i][j] = old + 2 * new          # encode',
    '    for i in range(m):',
    '        for j in range(n):',
    '            board[i][j] >>= 1                    # decode',
  ],
  parse(s) {
    const m = mtxParseGrid(s);
    if (m.some(r => r.some(v => v !== 0 && v !== 1))) throw new Error('Cells must be 0 (dead) or 1 (live)');
    return { m };
  },
  run({ m: input }) {
    const { F, snap } = avRecorder();
    const m = input.map(r => [...r]);
    const rows = m.length, cols = m[0].length;
    const S = (extra = {}) => ({ m: m.map(r => [...r]), phase: 'encode', ...extra });
    const liveNeighbors = (r, cc) => {
      let count = 0;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) {
        if (dr === 0 && dc === 0) continue;
        const nr = r + dr, nc = cc + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols) count += m[nr][nc] % 2;
      }
      return count;
    };
    snap(3, 'Pass 1: encode old + 2·new into every cell, reading neighbors with %2.', S());
    for (let i = 0; i < rows; i++) {
      for (let j = 0; j < cols; j++) {
        const old = m[i][j] % 2;
        const live = liveNeighbors(i, j);
        const nw = (old === 1 && (live === 2 || live === 3)) || (old === 0 && live === 3) ? 1 : 0;
        snap(15, `[${i}][${j}]: old=${old}, live neighbors=${live} → new=${nw}. Encode as ${old + 2 * nw}.`, S({ cur: [i, j], old, live, nw }));
        m[i][j] = old + 2 * nw;
      }
    }
    snap(17, 'Pass 2: decode — every cell shifts right by 1.', S({ phase: 'decode' }));
    for (let i = 0; i < rows; i++) for (let j = 0; j < cols; j++) { m[i][j] >>= 1; snap(18, `[${i}][${j}] >>= 1 → ${m[i][j]}.`, S({ phase: 'decode', cur: [i, j] })); }
    snap(18, 'Board now holds the next generation, computed with no extra grid.', S({ phase: 'done', done: true }));
    return F;
  },
  height: (w, last) => 40 + last.m.length * 48 + 70,
  draw(ctx, c, f, P) {
    const g = avDrawGrid(ctx, P, c, f.m, (i, j) => {
      const isCur = f.cur && f.cur[0] === i && f.cur[1] === j;
      const v = f.m[i][j];
      const isLive = f.phase === 'decode' || f.phase === 'done' ? v === 1 : (v % 2) === 1;
      return { fill: isCur ? P.alpha('accent', .45) : isLive ? P.alpha('ok', .3) : P.alpha('faint', .07), stroke: isCur ? P.accent : null, label: f.phase === 'encode' ? v : (v % 1 === 0 ? v : v) };
    }, { top: 34 });
    D.text(ctx, f.phase === 'encode' ? 'encode: old + 2·new' : f.phase === 'decode' ? 'decode: >>= 1' : 'done', 20, 16, { color: P.dim, size: 12, weight: 700 });
    if (f.live !== undefined) D.text(ctx, `old=${f.old} · live neighbors=${f.live} · new=${f.nw}`, 20, g.bottom + 26, { color: P.ok, size: 12, mono: true, weight: 650 });
  },
});

/* =================================================================== 008 · Diagonal Traverse == */
defineAlgo('24_matrix', {
  title: 'Diagonal Traverse', short: 'Diagonal Traverse',
  idea: 'Walk cell by cell, flipping between "up-right" and "down-left" every time an edge is hit. The three bounce rules per direction (hit the right edge, hit the top edge, or just keep moving) — and their mirror image for the other direction — are what keep the zigzag inside the grid.',
  complexity: 'Time O(rows × cols) · Space O(1) beyond the output',
  input: '1 2 3; 4 5 6; 7 8 9', hint: 'rows of numbers, separated by “;”',
  code: [
    'def findDiagonalOrder(mat):',
    '    m, n = len(mat), len(mat[0])',
    '    result = []',
    '    row, col, going_up = 0, 0, True',
    '    for _ in range(m * n):',
    '        result.append(mat[row][col])',
    '        if going_up:',
    '            if col == n - 1:   row += 1; going_up = False',
    '            elif row == 0:     col += 1; going_up = False',
    '            else:              row -= 1; col += 1',
    '        else:',
    '            if row == m - 1:   col += 1; going_up = True',
    '            elif col == 0:     row += 1; going_up = True',
    '            else:              row += 1; col -= 1',
    '    return result',
  ],
  parse(s) { return { m: mtxParseGrid(s) }; },
  run({ m }) {
    const { F, snap } = avRecorder();
    const rows = m.length, cols = m[0].length;
    let row = 0, col = 0, goingUp = true;
    const result = [];
    const S = (extra = {}) => ({ m, result: [...result], row, col, goingUp, ...extra });
    snap(4, 'Start at [0][0], heading up-right.', S({ cur: [row, col] }));
    for (let k = 0; k < rows * cols; k++) {
      result.push(m[row][col]);
      snap(6, `Append matrix[${row}][${col}] = ${m[row][col]}.`, S({ cur: [row, col] }));
      if (goingUp) {
        if (col === cols - 1) { row++; goingUp = false; snap(8, 'Hit the right edge — drop down a row, flip to down-left.', S({ cur: [row, col] })); }
        else if (row === 0) { col++; goingUp = false; snap(9, 'Hit the top edge — step right, flip to down-left.', S({ cur: [row, col] })); }
        else { row--; col++; snap(10, 'Keep going up-right.', S({ cur: [row, col] })); }
      } else {
        if (row === rows - 1) { col++; goingUp = true; snap(12, 'Hit the bottom edge — step right, flip to up-right.', S({ cur: [row, col] })); }
        else if (col === 0) { row++; goingUp = true; snap(13, 'Hit the left edge — drop down a row, flip to up-right.', S({ cur: [row, col] })); }
        else { row++; col--; snap(14, 'Keep going down-left.', S({ cur: [row, col] })); }
      }
    }
    snap(15, `Every cell visited once — [${result.join(', ')}].`, S({ done: true }));
    return F;
  },
  height: (w, last) => 40 + last.m.length * 48 + 60,
  draw(ctx, c, f, P) {
    const g = avDrawGrid(ctx, P, c, f.m, (i, j) => {
      const isCur = !f.done && f.cur && f.cur[0] === i && f.cur[1] === j;
      const visited = f.result.length > 0 && f.m[i][j] !== undefined;
      return { fill: isCur ? P.alpha('accent', .45) : P.surface2, stroke: isCur ? P.accent : null };
    }, { top: 30 });
    D.text(ctx, f.done ? 'done' : `heading ${f.goingUp ? 'up-right ↗' : 'down-left ↙'}`, 20, 16, { color: P.dim, size: 12.5, weight: 650 });
    D.text(ctx, `output: ${f.result.join(', ') || '—'}`, 20, g.bottom + 26, { color: P.ok, size: 12, mono: true, weight: 650 });
  },
});
