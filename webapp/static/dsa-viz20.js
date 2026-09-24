/* ============================================================================
   Visualizations for 14_graphs — the 15 problems that had no exact animation
   (001, 003, 004, 005, 007, 008, 009, 010, 012, 013, 014, 015, 016, 017, 018).
   Problems 002 (Number of Islands), 006 (Rotting Oranges) and 011 (Course
   Schedule) already had DOM-engine specs elsewhere — left untouched.
   ========================================================================= */
'use strict';

/* ------------------------------------------------------- shared helpers -- */
/* A generic box grid: cellFn(value, r, c) -> {content, bg, border, color, opacity, extra} */
function ggGridHTML(grid, cellFn, { cell = 38 } = {}) {
  return grid.map((row, r) => `<div style="display:flex;">${row.map((v, c) => {
    const st = cellFn(v, r, c) || {};
    return `<div style="width:${cell}px;height:${cell}px;margin:2px;border-radius:5px;
        display:flex;align-items:center;justify-content:center;
        background:${st.bg || 'var(--surface)'};border:2px solid ${st.border || 'var(--border)'};
        font-size:${st.fontSize || 13}px;font-family:var(--mono);font-weight:600;
        color:${st.color || 'var(--text-bright)'};opacity:${st.opacity ?? 1};
        transition:all .15s;${st.extra || ''}">${st.content ?? v}</div>`;
  }).join('')}</div>`).join('');
}

/* A small node-link graph laid out on a circle, drawn with inline SVG.
   nodeFn(i) -> {fill, stroke, color, label}; edgeFn([u,v]) -> {stroke, width} */
function ggGraphSVG(n, edges, nodeFn, edgeFn, { size = 240, r = 17 } = {}) {
  const R = size / 2 - 34, CX = size / 2, CY = size / 2;
  const pos = i => n === 1 ? [CX, CY] : [CX + R * Math.cos(-Math.PI / 2 + 2 * Math.PI * i / n), CY + R * Math.sin(-Math.PI / 2 + 2 * Math.PI * i / n)];
  const edgesSvg = edges.map(([u, v]) => {
    const [x1, y1] = pos(u), [x2, y2] = pos(v);
    const st = (edgeFn && edgeFn([u, v])) || {};
    return `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${st.stroke || 'var(--border)'}" stroke-width="${st.width || 2}" />`;
  }).join('');
  const nodesSvg = Array.from({ length: n }, (_, i) => {
    const [x, y] = pos(i);
    const st = (nodeFn && nodeFn(i)) || {};
    return `<circle cx="${x}" cy="${y}" r="${r}" fill="${st.fill || 'var(--surface)'}" stroke="${st.stroke || 'var(--border)'}" stroke-width="2.5" />
      <text x="${x}" y="${y + 5}" text-anchor="middle" font-size="13" font-weight="700" fill="${st.color || 'var(--text-bright)'}" font-family="var(--mono)">${st.label ?? i}</text>`;
  }).join('');
  return `<svg viewBox="0 0 ${size} ${size}" style="width:100%; max-width:${size}px; height:auto; display:block; margin:0 auto;">${edgesSvg}${nodesSvg}</svg>`;
}

function ggPanel(title, body, extraStyle = '') {
  return `<div class="glass-panel" style="${extraStyle}">
    <div class="panel-heading">${title}</div>
    ${body}
  </div>`;
}

function ggParseGrid(s, { max = 7 } = {}) {
  const rows = s.trim().split(',').map(r => r.trim());
  if (!rows.length) throw new Error('Enter at least one row');
  if (rows.length > max || rows[0].length > max) throw new Error(`Keep the grid to at most ${max}x${max} for visualization`);
  const w = rows[0].length;
  rows.forEach(r => { if (r.length !== w) throw new Error('Every row must have the same length'); });
  return rows.map(r => [...r].map(Number));
}

/* ============================================================ 001 · Flood Fill */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Flood Fill', short: 'Flood Fill',
  idea: 'Iterative DFS with an explicit stack. Remember the starting color first — if the new color is the same, return immediately (the classic trap: skipping this check turns a same-color fill into an infinite loop).',
  complexity: 'Time O(rows × cols) · Space O(rows × cols)',
  input: '111,110,101 ; 1,1 ; 2', hint: 'grid rows (digits) ; sr,sc ; new color',
  code: [
    'def floodFill(image, sr, sc, color):',
    '    rows, cols = len(image), len(image[0])',
    '    old_color = image[sr][sc]',
    '    if old_color == color:',
    '        return image                 # THE TRAP',
    '    stack = [(sr, sc)]',
    '    image[sr][sc] = color',
    '    while stack:',
    '        r, c = stack.pop()',
    '        for dr, dc in DIRS:',
    '            nr, nc = r + dr, c + dc',
    '            if in_bounds and image[nr][nc] == old_color:',
    '                image[nr][nc] = color',
    '                stack.append((nr, nc))',
    '    return image',
  ],
  parse(s) {
    const parts = s.split(';').map(x => x.trim());
    if (parts.length !== 3) throw new Error('Format: rows ; sr,sc ; color');
    const grid = ggParseGrid(parts[0], { max: 6 });
    const [sr, sc] = parts[1].split(',').map(Number);
    const color = Number(parts[2]);
    if (!(sr >= 0 && sr < grid.length && sc >= 0 && sc < grid[0].length)) throw new Error('sr,sc out of range');
    if (Number.isNaN(color)) throw new Error('color must be a number');
    return { grid, sr, sc, color };
  },
  buildStates({ grid, sr, sc, color }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const rows = grid.length, cols = grid[0].length;
    const img = grid.map(r => [...r]);
    const old = img[sr][sc];
    const snap = (line, clr, cur, stack, title, text, pause) =>
      domPushState(seq, { line, color: clr, img: img.map(r => [...r]), sr, sc, cur, stack: [...stack], explTitle: title, explText: text, pause }, ctx);
    snap(3, 'default', null, [], 'Remember the old color', `Cell (${sr},${sc}) starts as ${old}. New color is ${color}.`, true);
    if (old === color) { snap(5, 'emerald', null, [], 'Short-circuit', 'Old color equals new color — return immediately, or this would loop forever.', true); return seq; }
    const stack = [[sr, sc]];
    img[sr][sc] = color;
    snap(7, 'blue', null, stack, 'Seed the stack', `Push (${sr},${sc}) and recolor it to ${color} right away.`);
    const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    while (stack.length) {
      const [r, c] = stack.pop();
      snap(9, 'amber', [r, c], stack, 'Pop', `Popped (${r},${c}) — check its 4 neighbors for old color ${old}.`);
      for (const [dr, dc] of dirs) {
        const nr = r + dr, nc = c + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && img[nr][nc] === old) {
          img[nr][nc] = color; stack.push([nr, nc]);
          snap(13, 'emerald', [r, c], stack, 'Paint & push', `(${nr},${nc}) was old color — recolor to ${color} and push it.`);
        }
      }
    }
    snap(15, 'emerald', null, [], 'Done', 'Stack empty — every connected old-color cell has been repainted.', true);
    return seq;
  },
  renderDOM(container, s) {
    const pal = ['#0f172a', '#38bdf8', '#34d399', '#fbbf24', '#f472b6', '#a78bfa', '#f87171', '#94a3b8'];
    const grid = ggGridHTML(s.img, (v, r, c) => {
      const isCur = s.cur && s.cur[0] === r && s.cur[1] === c;
      const isStart = r === s.sr && c === s.sc;
      const onStack = s.stack.some(([sr, sc]) => sr === r && sc === c);
      return {
        content: v, bg: pal[v % pal.length], color: '#fff',
        border: isCur ? '#fbbf24' : isStart ? '#f472b6' : onStack ? '#38bdf8' : 'var(--border)',
        extra: isCur ? 'transform:scale(1.12);box-shadow:0 0 12px #fbbf24;' : '',
      };
    });
    container.innerHTML = `
      <div style="display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap;">
        ${ggPanel('Image', grid, 'padding:10px;')}
        ${ggPanel('Stack (next to pop from the end)', chipRow(s.stack.map(p => `(${p[0]},${p[1]})`)), 'flex:1; min-width:160px;')}
      </div>`;
  }
});

/* ===================================================== 003 · Max Area of Island */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Max Area of Island', short: 'Max Area of Island',
  idea: 'Same iterative-DFS "sink as you go" idea as Number of Islands, but count the cells sunk per island and keep a running maximum instead of just a count.',
  complexity: 'Time O(rows × cols) · Space O(rows × cols)',
  input: '11000,11000,00100,00011', hint: 'grid rows of 0 (water) / 1 (land)',
  code: [
    'def maxAreaOfIsland(grid):',
    '    rows, cols = len(grid), len(grid[0])',
    '    best = 0',
    '    def area(r, c):',
    '        stack = [(r, c)]',
    '        grid[r][c] = 0',
    '        count = 0',
    '        while stack:',
    '            cr, cc = stack.pop()',
    '            count += 1',
    '            for dr, dc in DIRS:',
    '                nr, nc = cr+dr, cc+dc',
    '                if in_bounds and grid[nr][nc] == 1:',
    '                    grid[nr][nc] = 0',
    '                    stack.append((nr, nc))',
    '        return count',
    '    for r in range(rows):',
    '        for c in range(cols):',
    '            if grid[r][c] == 1:',
    '                best = max(best, area(r, c))',
    '    return best',
  ],
  parse(s) {
    const grid = ggParseGrid(s, { max: 6 });
    if (grid.some(row => row.some(v => v !== 0 && v !== 1))) throw new Error('Cells must be 0 or 1');
    return { grid };
  },
  buildStates({ grid }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const rows = grid.length, cols = grid[0].length;
    const g = grid.map(r => [...r]);
    let best = 0;
    const snap = (line, clr, cur, stack, title, text, pause) =>
      domPushState(seq, { line, color: clr, grid: g.map(r => [...r]), cur, stack: [...stack], best, explTitle: title, explText: text, pause }, ctx);
    snap(2, 'default', null, [], 'Scan', 'Scan every cell; whenever we find unvisited land, sink its whole island and measure it.', true);
    const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      if (g[r][c] !== 1) continue;
      const stack = [[r, c]]; g[r][c] = 0; let count = 0;
      snap(17, 'amber', [r, c], stack, 'Found land', `(${r},${c}) is land — start sinking this island.`);
      while (stack.length) {
        const [cr, cc] = stack.pop(); count++;
        snap(9, 'blue', [cr, cc], stack, 'Pop & count', `Popped (${cr},${cc}) — area so far in this island: ${count}.`);
        for (const [dr, dc] of dirs) {
          const nr = cr + dr, nc = cc + dc;
          if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && g[nr][nc] === 1) { g[nr][nc] = 0; stack.push([nr, nc]); }
        }
      }
      best = Math.max(best, count);
      snap(18, 'emerald', null, [], 'Island done', `This island's area was ${count}. Best so far: ${best}.`);
    }
    snap(20, 'emerald', null, [], 'Done', `Every island sunk. Max area: ${best}.`, true);
    return seq;
  },
  renderDOM(container, s) {
    const grid = ggGridHTML(s.grid, (v, r, c) => {
      const isCur = s.cur && s.cur[0] === r && s.cur[1] === c;
      const onStack = s.stack.some(([sr, sc]) => sr === r && sc === c);
      return { content: v ? '🟩' : '·', bg: v ? 'rgba(52,211,153,.12)' : 'transparent', border: isCur ? '#fbbf24' : onStack ? '#38bdf8' : 'var(--border)', extra: isCur ? 'transform:scale(1.12);' : '' };
    });
    container.innerHTML = `
      <div style="display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap;">
        ${ggPanel('Grid', grid, 'padding:10px;')}
        ${ggPanel('Best area', `<div style="font-size:40px;font-weight:800;color:var(--accent);text-align:center;">${s.best}</div>`, 'flex:1; min-width:120px;')}
      </div>`;
  }
});

/* =========================================================== 004 · Clone Graph */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Clone Graph', short: 'Clone Graph',
  idea: 'Recursive DFS with a node → clone MAP. Register a node\'s clone in the map BEFORE recursing into its neighbors — that is what breaks cycles and stops infinite recursion on a graph that loops back on itself.',
  complexity: 'Time O(V + E) · Space O(V)',
  input: '1-2,1-4,2-3,3-4', hint: 'undirected edges "u-v" (1-indexed nodes), start DFS at node 1',
  code: [
    'def cloneGraph(node):',
    '    if node is None: return None',
    '    clones = {}',
    '    def dfs(original):',
    '        if original in clones:',
    '            return clones[original]',
    '        copy = Node(original.val)',
    '        clones[original] = copy      # BEFORE recursing',
    '        for nb in original.neighbors:',
    '            copy.neighbors.append(dfs(nb))',
    '        return copy',
    '    return dfs(node)',
  ],
  parse(s) {
    const edges = s.split(',').map(t => t.trim()).filter(Boolean).map(t => {
      const m = t.match(/^(\d+)-(\d+)$/);
      if (!m) throw new Error(`"${t}" should look like 1-2`);
      return [+m[1], +m[2]];
    });
    if (!edges.length) throw new Error('Enter at least one edge');
    const nodes = new Set(); edges.forEach(([u, v]) => { nodes.add(u); nodes.add(v); });
    if (nodes.size > 7) throw new Error('Use at most 7 nodes for visualization');
    return { edges, n: Math.max(...nodes) };
  },
  buildStates({ edges, n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const adj = Array.from({ length: n + 1 }, () => []);
    edges.forEach(([u, v]) => { adj[u].push(v); adj[v].push(u); });
    const clones = new Set(); const cloneEdges = [];
    const snap = (line, clr, cur, title, text, pause) =>
      domPushState(seq, { line, color: clr, n, edges, cur, clones: [...clones], cloneEdges: cloneEdges.map(e => [...e]), explTitle: title, explText: text, pause }, ctx);
    snap(2, 'default', null, 'Start', `Start DFS at node 1 (original graph on the left, clone being built on the right).`, true);
    function dfs(orig, from) {
      if (clones.has(orig)) { snap(4, 'blue', orig, 'Already cloned', `Node ${orig} is already in the map — reuse its clone (this is what stops the cycle).`); return; }
      clones.add(orig);
      snap(7, 'emerald', orig, 'Clone & register', `Create clone(${orig}) and register it in the map BEFORE visiting its neighbors.`);
      for (const nb of adj[orig]) {
        if (from === nb && !clones.has(nb)) { /* still traverse, undirected */ }
        cloneEdges.push([orig, nb]);
        snap(9, 'amber', orig, 'Recurse', `Visit neighbor ${nb} of ${orig}.`);
        dfs(nb, orig);
      }
    }
    dfs(1, -1);
    snap(11, 'emerald', null, 'Done', `Clone graph complete: ${clones.size} nodes cloned.`, true);
    return seq;
  },
  renderDOM(container, s) {
    const dedupe = arr => { const seen = new Set(), out = []; arr.forEach(([u, v]) => { const k = u < v ? `${u}-${v}` : `${v}-${u}`; if (!seen.has(k)) { seen.add(k); out.push([u, v]); } }); return out; };
    const origEdges = s.edges.map(([u, v]) => [u - 1, v - 1]);
    const cloneSet = new Set(s.clones);
    const cloneEdges = dedupe(s.cloneEdges).map(([u, v]) => [u - 1, v - 1]);
    const origSvg = ggGraphSVG(s.n, origEdges,
      i => ({ fill: (i + 1) === s.cur ? 'rgba(251,191,36,.35)' : cloneSet.has(i + 1) ? 'rgba(52,211,153,.2)' : null, stroke: (i + 1) === s.cur ? '#fbbf24' : cloneSet.has(i + 1) ? '#34d399' : null, label: i + 1 }));
    const cloneSvg = ggGraphSVG(s.n, cloneEdges,
      i => cloneSet.has(i + 1) ? ({ fill: 'rgba(56,189,248,.2)', stroke: '#38bdf8', label: `${i + 1}'` }) : ({ fill: 'transparent', stroke: 'transparent', color: 'transparent', label: '' }),
      ([u, v]) => cloneSet.has(u + 1) && cloneSet.has(v + 1) ? { stroke: '#38bdf8' } : { stroke: 'transparent' });
    container.innerHTML = `
      <div style="display:flex; gap:16px; flex-wrap:wrap;">
        ${ggPanel('Original graph', origSvg, 'flex:1; min-width:240px;')}
        ${ggPanel('Clone (built so far)', cloneSvg, 'flex:1; min-width:240px;')}
      </div>`;
  }
});

/* ========================================================= 005 · Walls and Gates */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Walls and Gates', short: 'Walls and Gates',
  idea: 'Multi-source BFS: seed the queue with EVERY gate (value 0) at once, before the first pop. Every empty room is then filled in with its true shortest distance to the nearest gate in one pass.',
  complexity: 'Time O(rows × cols) · Space O(rows × cols)',
  input: 'I0IW,IIII,IWI0,IIII', hint: 'I = empty room (INF), W = wall, 0 = gate',
  code: [
    'def solve(rooms):',
    '    rows, cols = len(rooms), len(rooms[0])',
    '    q = deque()',
    '    for r, c in all cells:',
    '        if rooms[r][c] == 0:',
    '            q.append((r, c))     # every gate at once',
    '    while q:',
    '        r, c = q.popleft()',
    '        for dr, dc in DIRS:',
    '            nr, nc = r+dr, c+dc',
    '            if in_bounds and rooms[nr][nc] == INF:',
    '                rooms[nr][nc] = rooms[r][c] + 1',
    '                q.append((nr, nc))',
  ],
  parse(s) {
    const rows = s.split(',').map(r => r.trim());
    if (rows.length > 6 || rows[0].length > 6) throw new Error('Keep the grid to at most 6x6');
    const w = rows[0].length;
    const grid = rows.map(r => {
      if (r.length !== w) throw new Error('Every row must have the same length');
      return [...r].map(ch => { if (ch === 'I') return 999; if (ch === 'W') return -1; if (ch === '0') return 0; throw new Error(`"${ch}" must be I, W or 0`); });
    });
    return { grid };
  },
  buildStates({ grid }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const rows = grid.length, cols = grid[0].length;
    const g = grid.map(r => [...r]);
    const q = [];
    const snap = (line, clr, cur, title, text, pause) =>
      domPushState(seq, { line, color: clr, grid: g.map(r => [...r]), q: [...q], cur, explTitle: title, explText: text, pause }, ctx);
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) if (g[r][c] === 0) q.push([r, c]);
    snap(6, 'blue', null, 'Seed with every gate', `Found ${q.length} gate(s) — enqueue all of them before the first pop. This is what makes it multi-source.`, true);
    const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    while (q.length) {
      const [r, c] = q.shift();
      snap(8, 'amber', [r, c], 'Pop', `Popped (${r},${c}), distance ${g[r][c]}. Expand to empty-room neighbors.`);
      for (const [dr, dc] of dirs) {
        const nr = r + dr, nc = c + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && g[nr][nc] === 999) {
          g[nr][nc] = g[r][c] + 1; q.push([nr, nc]);
          snap(11, 'emerald', [r, c], 'Fill distance', `(${nr},${nc}) is an empty room — set it to ${g[r][c]} and enqueue it.`);
        }
      }
    }
    snap(12, 'emerald', null, 'Done', 'Queue empty — every reachable room now holds its true shortest distance to a gate.', true);
    return seq;
  },
  renderDOM(container, s) {
    const grid = ggGridHTML(s.grid, (v, r, c) => {
      const isCur = s.cur && s.cur[0] === r && s.cur[1] === c;
      const inQ = s.q.some(([qr, qc]) => qr === r && qc === c);
      if (v === -1) return { content: '🧱', bg: 'rgba(148,163,184,.15)', color: 'var(--text-dim)' };
      if (v === 0) return { content: '🚪', bg: 'rgba(251,191,36,.15)', border: isCur ? '#fbbf24' : '#f59e0b' };
      return { content: v === 999 ? '·' : v, bg: v === 999 ? 'transparent' : 'rgba(56,189,248,.15)', border: isCur ? '#fbbf24' : inQ ? '#38bdf8' : 'var(--border)', fontSize: 15 };
    });
    container.innerHTML = `${ggPanel('Rooms (🚪 gate · 🧱 wall · number = distance)', grid, 'padding:10px; display:inline-block;')}`;
  }
});

/* ================================================ 007 · Pacific Atlantic Water Flow */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Pacific Atlantic Water Flow', short: 'Pacific Atlantic',
  idea: 'Flow flows FROM low TO high, so flood-fill in reverse: from the two oceans\' border cells, walk to any neighbor with height >= current. Do this in two independent visited sets (never mutate one shared grid); the answer is their intersection.',
  complexity: 'Time O(rows × cols) · Space O(rows × cols)',
  input: '1231,2321,3123,4321', hint: 'grid of heights, one digit each',
  code: [
    'def pacificAtlantic(heights):',
    '    def flood(starts):',
    '        visited = set(starts)',
    '        q = deque(starts)',
    '        while q:',
    '            r, c = q.popleft()',
    '            for dr, dc in DIRS:',
    '                nr, nc = r+dr, c+dc',
    '                if in_bounds and (nr,nc) not in visited',
    '                   and heights[nr][nc] >= heights[r][c]:',
    '                    visited.add((nr, nc))',
    '                    q.append((nr, nc))',
    '        return visited',
    '    pacific = flood(top_and_left_borders)',
    '    atlantic = flood(bottom_and_right_borders)',
    '    return pacific & atlantic',
  ],
  parse(s) {
    const grid = ggParseGrid(s, { max: 5 });
    return { grid };
  },
  buildStates({ grid }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const rows = grid.length, cols = grid[0].length;
    const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    let pacSet = new Set(), atlSet = new Set();
    const snap = (line, clr, name, title, text, pause) =>
      domPushState(seq, { line, color: clr, grid, pac: new Set(pacSet), atl: new Set(atlSet), phase: name, explTitle: title, explText: text, pause }, ctx);
    const flood = (starts, name) => {
      const visited = new Set(starts.map(([r, c]) => `${r},${c}`));
      const q = [...starts];
      if (name === 'Pacific') pacSet = visited; else atlSet = visited;
      snap(13, 'blue', name, `${name}: seed the borders`, `Start from every ${name} border cell at once (${starts.length} cells) and flow uphill only.`, true);
      while (q.length) {
        const [r, c] = q.shift();
        for (const [dr, dc] of dirs) {
          const nr = r + dr, nc = c + dc, k = `${nr},${nc}`;
          if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && !visited.has(k) && grid[nr][nc] >= grid[r][c]) {
            visited.add(k); q.push([nr, nc]);
          }
        }
      }
      snap(12, 'emerald', name, `${name} flood done`, `${visited.size} cells can reach the ${name}.`, true);
      return visited;
    };
    const pacStarts = []; for (let c = 0; c < cols; c++) pacStarts.push([0, c]); for (let r = 1; r < rows; r++) pacStarts.push([r, 0]);
    const atlStarts = []; for (let c = 0; c < cols; c++) atlStarts.push([rows - 1, c]); for (let r = 0; r < rows - 1; r++) atlStarts.push([r, cols - 1]);
    const pac = flood(pacStarts, 'Pacific');
    const atl = flood(atlStarts, 'Atlantic');
    const both = [...pac].filter(k => atl.has(k));
    snap(15, 'emerald', 'Both', 'Intersection', `${both.length} cell(s) can reach BOTH oceans — that is the answer.`, true);
    return seq;
  },
  renderDOM(container, s) {
    const grid = ggGridHTML(s.grid, (v, r, c) => {
      const k = `${r},${c}`, p = s.pac.has(k), a = s.atl.has(k);
      let bg = 'var(--surface)';
      if (p && a) bg = 'rgba(52,211,153,.35)'; else if (p) bg = 'rgba(56,189,248,.3)'; else if (a) bg = 'rgba(244,114,182,.3)';
      return { content: v, bg, border: p && a ? '#34d399' : 'var(--border)' };
    });
    container.innerHTML = `<div style="display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap;">
      ${ggPanel(`Heights (${s.phase} flood)`, grid, 'padding:10px;')}
      ${ggPanel('Legend', `<div style="font-size:12px; line-height:2;">
        <span style="color:#38bdf8;">■</span> reaches Pacific &nbsp;
        <span style="color:#f472b6;">■</span> reaches Atlantic &nbsp;
        <span style="color:#34d399;">■</span> reaches BOTH (answer)
      </div>`, 'flex:1; min-width:200px;')}
    </div>`;
  }
});

/* ===================================================== 008 · Surrounded Regions */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Surrounded Regions', short: 'Surrounded Regions',
  idea: 'You cannot safely flip \'O\' to \'X\' as you scan (a region touching the border must survive). So flood-fill from the BORDER inward first, marking every border-connected \'O\' as safe — then flip every remaining \'O\' (truly surrounded) to \'X\', and flip safe marks back to \'O\'.',
  complexity: 'Time O(rows × cols) · Space O(rows × cols)',
  input: 'XXXX,XOOX,XXOX,XOXX', hint: 'grid of X (wall) / O (open)',
  code: [
    'def solve(board):',
    '    def flood(r, c):',
    '        stack = [(r, c)]',
    "        while stack:",
    "            cr, cc = stack.pop()",
    "            if not in_bounds or board[cr][cc] != 'O': continue",
    "            board[cr][cc] = SAFE",
    '            for dr, dc in DIRS:',
    '                stack.append((cr+dr, cc+dc))',
    "    for cell on the border:",
    "        if board[r][c] == 'O': flood(r, c)",
    '    for every cell:',
    "        if board[r][c] == 'O': board[r][c] = 'X'      # truly surrounded",
    '        elif board[r][c] == SAFE: board[r][c] = "O"    # restore',
  ],
  parse(s) {
    const rows = s.split(',').map(r => r.trim());
    if (rows.length > 6 || rows[0].length > 6) throw new Error('Keep the grid to at most 6x6');
    const w = rows[0].length;
    rows.forEach(r => { if (r.length !== w || ![...r].every(ch => ch === 'X' || ch === 'O')) throw new Error('Rows must be equal-length strings of X/O'); });
    return { grid: rows.map(r => [...r]) };
  },
  buildStates({ grid }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const rows = grid.length, cols = grid[0].length;
    const g = grid.map(r => [...r]);
    const SAFE = '#';
    const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    const snap = (line, clr, cur, title, text, pause) =>
      domPushState(seq, { line, color: clr, grid: g.map(r => [...r]), cur, explTitle: title, explText: text, pause }, ctx);
    snap(10, 'blue', null, 'Flood from the border', 'Walk inward from every border O — those cannot be surrounded, so mark them safe.', true);
    const borders = [];
    for (let c = 0; c < cols; c++) { borders.push([0, c]); borders.push([rows - 1, c]); }
    for (let r = 0; r < rows; r++) { borders.push([r, 0]); borders.push([r, cols - 1]); }
    for (const [br, bc] of borders) {
      if (g[br][bc] !== 'O') continue;
      const stack = [[br, bc]];
      while (stack.length) {
        const [cr, cc] = stack.pop();
        if (cr < 0 || cr >= rows || cc < 0 || cc >= cols || g[cr][cc] !== 'O') continue;
        g[cr][cc] = SAFE;
        snap(7, 'emerald', [cr, cc], 'Mark safe', `(${cr},${cc}) is connected to the border — mark it safe.`);
        for (const [dr, dc] of dirs) stack.push([cr + dr, cc + dc]);
      }
    }
    snap(12, 'amber', null, 'Flip the rest', 'Any O left is fully surrounded — flip to X. Any SAFE mark reverts back to O.', true);
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
      if (g[r][c] === 'O') { g[r][c] = 'X'; snap(13, 'rose', [r, c], 'Capture', `(${r},${c}) was fully surrounded — flip to X.`); }
      else if (g[r][c] === SAFE) { g[r][c] = 'O'; }
    }
    snap(14, 'emerald', null, 'Done', 'Border-connected regions restored to O, fully-surrounded regions captured as X.', true);
    return seq;
  },
  renderDOM(container, s) {
    const grid = ggGridHTML(s.grid, (v, r, c) => {
      const isCur = s.cur && s.cur[0] === r && s.cur[1] === c;
      if (v === 'X') return { content: 'X', bg: 'rgba(148,163,184,.12)', color: 'var(--text-dim)' };
      if (v === '#') return { content: '✓', bg: 'rgba(52,211,153,.2)', border: isCur ? '#34d399' : '#10b981', color: '#34d399' };
      return { content: 'O', bg: isCur ? 'rgba(251,113,133,.25)' : 'rgba(56,189,248,.12)', border: isCur ? '#fb7185' : 'var(--border)' };
    });
    container.innerHTML = ggPanel('Board (✓ = marked safe, pending restore to O)', grid, 'padding:10px; display:inline-block;');
  }
});

/* ================= 009 · Number of Connected Components in an Undirected Graph */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Number of Connected Components in an Undirected Graph', short: 'Connected Components',
  idea: 'Iterative DFS from every unvisited node. Each DFS you have to launch is a brand new component — count how many times you launch one.',
  complexity: 'Time O(V + E) · Space O(V + E)',
  input: '5 ; 0,1 ; 1,2 ; 3,4', hint: 'n ; edges u,v',
  code: [
    'def countComponents(n, edges):',
    '    graph = {i: [] for i in range(n)}',
    '    for u, v in edges:',
    '        graph[u].append(v); graph[v].append(u)',
    '    visited = set()',
    '    components = 0',
    '    for start in range(n):',
    '        if start in visited: continue',
    '        components += 1',
    '        stack = [start]',
    '        while stack:',
    '            node = stack.pop()',
    '            if node in visited: continue',
    '            visited.add(node)',
    '            for nxt in graph[node]:',
    '                if nxt not in visited: stack.append(nxt)',
    '    return components',
  ],
  parse(s) {
    const parts = s.split(';').map(x => x.trim());
    const n = parseInt(parts[0]);
    if (!(n > 0 && n <= 9)) throw new Error('n must be 1-9');
    const edges = parts.slice(1).filter(Boolean).map(p => p.split(',').map(Number));
    edges.forEach(([u, v]) => { if (!(u >= 0 && u < n && v >= 0 && v < n)) throw new Error('Edge endpoints must be in range'); });
    return { n, edges };
  },
  buildStates({ n, edges }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const graph = Array.from({ length: n }, () => []);
    edges.forEach(([u, v]) => { graph[u].push(v); graph[v].push(u); });
    const visited = new Set(); const compOf = Array(n).fill(-1); let components = 0;
    const snap = (line, clr, cur, title, text, pause) =>
      domPushState(seq, { line, color: clr, n, edges, compOf: [...compOf], cur, components, explTitle: title, explText: text, pause }, ctx);
    for (let start = 0; start < n; start++) {
      if (visited.has(start)) continue;
      components++;
      snap(8, 'amber', start, 'New component', `Node ${start} is unvisited — this starts component #${components}.`, true);
      const stack = [start];
      while (stack.length) {
        const node = stack.pop();
        if (visited.has(node)) continue;
        visited.add(node); compOf[node] = components - 1;
        snap(13, 'blue', node, 'Visit', `Visit ${node}, mark it component #${components}, push its unvisited neighbors.`);
        for (const nxt of graph[node]) if (!visited.has(nxt)) stack.push(nxt);
      }
    }
    snap(16, 'emerald', null, 'Done', `${components} connected component(s) found.`, true);
    return seq;
  },
  renderDOM(container, s) {
    const pal = ['#34d399', '#38bdf8', '#fbbf24', '#f472b6', '#a78bfa', '#f87171', '#22d3ee', '#fb923c', '#94a3b8'];
    const svg = ggGraphSVG(s.n, s.edges,
      i => ({ fill: i === s.cur ? 'rgba(251,191,36,.35)' : s.compOf[i] >= 0 ? `color-mix(in srgb, ${pal[s.compOf[i] % pal.length]} 25%, transparent)` : null, stroke: i === s.cur ? '#fbbf24' : s.compOf[i] >= 0 ? pal[s.compOf[i] % pal.length] : null }));
    container.innerHTML = `<div style="display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap;">
      ${ggPanel('Graph', svg, 'flex:1; min-width:240px;')}
      ${ggPanel('Components found', `<div style="font-size:40px;font-weight:800;color:var(--accent);text-align:center;">${s.components}</div>`, 'min-width:120px;')}
    </div>`;
  }
});

/* ============================================================ 010 · Graph Valid Tree */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Graph Valid Tree', short: 'Graph Valid Tree',
  idea: 'A graph with n nodes is a tree iff it has exactly n-1 edges AND is fully connected. Check the edge count first (O(1) short-circuit), then run one BFS from node 0 and see if it reaches every node.',
  complexity: 'Time O(V + E) · Space O(V + E)',
  input: '5 ; 0,1 ; 0,2 ; 0,3 ; 1,4', hint: 'n ; edges u,v',
  code: [
    'def validTree(n, edges):',
    '    if len(edges) != n - 1:',
    '        return False               # too few/many edges',
    '    if n <= 1: return True',
    '    graph = {i: [] for i in range(n)}',
    '    for u, v in edges:',
    '        graph[u].append(v); graph[v].append(u)',
    '    visited = {0}',
    '    q = deque([0])',
    '    while q:',
    '        node = q.popleft()',
    '        for nxt in graph[node]:',
    '            if nxt not in visited:',
    '                visited.add(nxt); q.append(nxt)',
    '    return len(visited) == n',
  ],
  parse(s) {
    const parts = s.split(';').map(x => x.trim());
    const n = parseInt(parts[0]);
    if (!(n > 0 && n <= 9)) throw new Error('n must be 1-9');
    const edges = parts.slice(1).filter(Boolean).map(p => p.split(',').map(Number));
    return { n, edges };
  },
  buildStates({ n, edges }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const snap = (line, clr, visited, cur, title, text, pause) =>
      domPushState(seq, { line, color: clr, n, edges, visited: [...(visited || [])], cur, explTitle: title, explText: text, pause }, ctx);
    if (edges.length !== n - 1) {
      snap(2, 'rose', [], null, 'Edge-count short-circuit', `${edges.length} edges but n-1 = ${n - 1} — a tree needs exactly n-1 edges. Not a tree.`, true);
      return seq;
    }
    snap(2, 'default', [], null, 'Edge count OK', `${edges.length} edges = n-1. Now check connectivity with one BFS.`, true);
    const graph = Array.from({ length: n }, () => []);
    edges.forEach(([u, v]) => { graph[u].push(v); graph[v].push(u); });
    const visited = new Set([0]); const q = [0];
    snap(8, 'blue', visited, 0, 'Start BFS', 'Start from node 0.');
    while (q.length) {
      const node = q.shift();
      snap(11, 'amber', visited, node, 'Visit', `Expand ${node}'s neighbors.`);
      for (const nxt of graph[node]) if (!visited.has(nxt)) { visited.add(nxt); q.push(nxt); snap(13, 'emerald', visited, node, 'Reach', `Reached ${nxt} for the first time.`); }
    }
    const ok = visited.size === n;
    snap(14, ok ? 'emerald' : 'rose', visited, null, ok ? 'All reached — valid tree' : 'Some node unreachable', ok ? `All ${n} nodes reached — connected + right edge count = valid tree.` : `Only ${visited.size}/${n} nodes reached — the graph is disconnected.`, true);
    return seq;
  },
  renderDOM(container, s) {
    const vis = new Set(s.visited);
    const svg = ggGraphSVG(s.n, s.edges, i => ({ fill: i === s.cur ? 'rgba(251,191,36,.35)' : vis.has(i) ? 'rgba(52,211,153,.2)' : null, stroke: i === s.cur ? '#fbbf24' : vis.has(i) ? '#34d399' : null }));
    container.innerHTML = ggPanel(`Graph — ${s.edges.length} edges, n=${s.n}`, svg, 'display:inline-block; min-width:260px;');
  }
});

/* ==================================================== 012 · Course Schedule II */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Course Schedule II', short: 'Course Schedule II',
  idea: 'Same Kahn\'s-algorithm idea as Course Schedule, but this time the pop sequence itself IS the answer — collect it into an order list as you go.',
  complexity: 'Time O(V + E) · Space O(V + E)',
  input: '4 ; 1,0 ; 2,0 ; 3,1 ; 3,2', hint: 'numCourses ; a,b pairs meaning "a needs b first"',
  code: [
    'def findOrder(numCourses, prerequisites):',
    '    graph = {i: [] for i in range(numCourses)}',
    '    indegree = [0] * numCourses',
    '    for a, b in prerequisites:      # a needs b first',
    '        graph[b].append(a); indegree[a] += 1',
    '    q = deque(i for i in range(numCourses) if indegree[i] == 0)',
    '    order = []',
    '    while q:',
    '        node = q.popleft()',
    '        order.append(node)',
    '        for nxt in graph[node]:',
    '            indegree[nxt] -= 1',
    '            if indegree[nxt] == 0: q.append(nxt)',
    '    return order if len(order) == numCourses else []',
  ],
  parse(s) {
    const parts = s.split(';').map(x => x.trim());
    const n = parseInt(parts[0]);
    if (!(n > 0 && n <= 9)) throw new Error('numCourses must be 1-9');
    const prereqs = parts.slice(1).filter(Boolean).map(p => p.split(',').map(Number));
    return { n, prereqs };
  },
  buildStates({ n, prereqs }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const graph = Array.from({ length: n }, () => []); const indeg = Array(n).fill(0);
    prereqs.forEach(([a, b]) => { graph[b].push(a); indeg[a]++; });
    const snap = (line, clr, q, order, cur, title, text, pause) =>
      domPushState(seq, { line, color: clr, n, indeg: [...indeg], q: [...q], order: [...order], cur, explTitle: title, explText: text, pause }, ctx);
    const q = []; for (let i = 0; i < n; i++) if (indeg[i] === 0) q.push(i);
    const order = [];
    snap(6, 'blue', q, order, null, 'Seed queue', `Courses with 0 prerequisites: [${q.join(', ')}].`, true);
    while (q.length) {
      const node = q.shift(); order.push(node);
      snap(9, 'amber', q, order, node, 'Take course', `Take ${node} — it's next in the order.`);
      for (const nxt of graph[node]) {
        indeg[nxt]--;
        if (indeg[nxt] === 0) { q.push(nxt); snap(12, 'emerald', q, order, node, 'Unlocked', `${nxt}'s last prerequisite is done — enqueue it.`); }
      }
    }
    const ok = order.length === n;
    snap(13, ok ? 'emerald' : 'rose', q, order, null, ok ? 'Valid order' : 'Cycle detected', ok ? `Order: [${order.join(', ')}].` : `Only ${order.length}/${n} courses ordered — a cycle blocks the rest.`, true);
    return seq;
  },
  renderDOM(container, s) {
    const cards = Array.from({ length: s.n }, (_, i) => {
      const done = s.order.includes(i), cur = s.cur === i, ready = s.q.includes(i);
      const bg = done ? 'rgba(52,211,153,.12)' : cur ? 'rgba(251,191,36,.15)' : 'var(--surface)';
      const border = done ? '#34d399' : cur ? '#fbbf24' : ready ? '#38bdf8' : 'var(--border)';
      return `<div style="padding:8px 14px;border-radius:8px;border:2px solid ${border};background:${bg};display:flex;flex-direction:column;align-items:center;min-width:60px;">
        <div style="font-size:20px;font-weight:800;">${i}</div>
        <div style="font-size:10px;color:var(--text-dim);">${done ? '✅' : cur ? '⏳' : ready ? '📝' : `🔒${s.indeg[i]}`}</div>
      </div>`;
    }).join('');
    container.innerHTML = `${ggPanel('Courses', `<div style="display:flex;flex-wrap:wrap;gap:10px;">${cards}</div>`, 'padding:14px;')}
      ${ggPanel('Order so far', chipRow(s.order), 'margin-top:10px;')}`;
  }
});

/* ======================================================= 013 · Redundant Connection */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Redundant Connection', short: 'Redundant Connection',
  idea: 'Add edges one at a time. Before adding an edge, check (DFS) whether its two endpoints are already connected by edges added so far — the first edge that would close a cycle is the redundant one.',
  complexity: 'Time O(E × (V + E)) · Space O(V + E)',
  input: '1,2;1,3;2,3', hint: 'edges u,v in the order they are added',
  code: [
    'def findRedundantConnection(edges):',
    '    graph = {}',
    '    def connected(u, v):',
    '        visited, stack = set(), [u]',
    '        while stack:',
    '            node = stack.pop()',
    '            if node == v: return True',
    '            if node in visited: continue',
    '            visited.add(node)',
    '            for nxt in graph.get(node, []):',
    '                stack.append(nxt)',
    '        return False',
    '    for u, v in edges:',
    '        if u in graph and v in graph and connected(u, v):',
    '            return [u, v]              # closes a cycle',
    '        graph.setdefault(u, []).append(v)',
    '        graph.setdefault(v, []).append(u)',
  ],
  parse(s) {
    const edges = s.split(';').map(t => t.trim()).filter(Boolean).map(t => t.split(',').map(Number));
    if (edges.length < 2 || edges.length > 9) throw new Error('Use 2-9 edges');
    return { edges };
  },
  buildStates({ edges }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const graph = {};
    const snap = (line, clr, cur, answer, title, text, pause) =>
      domPushState(seq, { line, color: clr, edgesSoFar: Object.entries(graph).flatMap(([u, ns]) => ns.filter(v => +v > +u).map(v => [+u, v])), allEdges: edges, cur, answer, explTitle: title, explText: text, pause }, ctx);
    function connected(u, v) {
      const visited = new Set(); const stack = [u];
      while (stack.length) { const node = stack.pop(); if (node === v) return true; if (visited.has(node)) continue; visited.add(node); for (const nxt of (graph[node] || [])) stack.push(nxt); }
      return false;
    }
    for (const [u, v] of edges) {
      snap(13, 'amber', [u, v], null, 'Try next edge', `Consider edge (${u},${v}).`);
      if (graph[u] && graph[v] && connected(u, v)) {
        snap(15, 'rose', [u, v], [u, v], 'Redundant!', `${u} and ${v} are already connected — this edge closes a cycle. Answer: [${u},${v}].`, true);
        return seq;
      }
      (graph[u] ??= []).push(v); (graph[v] ??= []).push(u);
      snap(16, 'emerald', [u, v], null, 'Add edge', `Not yet connected — add (${u},${v}) to the graph.`);
    }
    return seq;
  },
  renderDOM(container, s) {
    const nodes = new Set(); s.allEdges.forEach(([u, v]) => { nodes.add(u); nodes.add(v); });
    const idOf = {}; [...nodes].sort((a, b) => a - b).forEach((n, i) => idOf[n] = i);
    const n = nodes.size;
    const built = s.edgesSoFar.map(([u, v]) => [idOf[u], idOf[v]]);
    const cur = s.cur ? [idOf[s.cur[0]], idOf[s.cur[1]]] : null;
    const ans = s.answer ? [idOf[s.answer[0]], idOf[s.answer[1]]] : null;
    const allDrawEdges = [...built, ...(cur && !built.some(([u, v]) => (u === cur[0] && v === cur[1]) || (u === cur[1] && v === cur[0])) ? [cur] : [])];
    const origLabel = Object.fromEntries([...nodes].map(k => [idOf[k], k]));
    const svg = ggGraphSVG(n, allDrawEdges,
      i => ({ label: origLabel[i] }),
      ([u, v]) => {
        if (ans && ((u === ans[0] && v === ans[1]) || (u === ans[1] && v === ans[0]))) return { stroke: '#f43f5e', width: 3 };
        if (cur && ((u === cur[0] && v === cur[1]) || (u === cur[1] && v === cur[0]))) return { stroke: '#fbbf24', width: 3 };
        return { stroke: '#34d399' };
      });
    container.innerHTML = ggPanel('Graph built so far (amber = edge under test, red = redundant)', svg, 'display:inline-block; min-width:260px;');
  }
});

/* =================================================================== 014 · 01 Matrix */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: '01 Matrix', short: '01 Matrix',
  idea: 'Multi-source BFS again: seed the queue with every 0-cell at once (distance 0), then expand outward — the first time a 1-cell is reached is guaranteed to be via the shortest path to SOME 0.',
  complexity: 'Time O(rows × cols) · Space O(rows × cols)',
  input: '0101,1111,0100,1110', hint: 'grid of 0s and 1s',
  code: [
    'def updateMatrix(mat):',
    '    rows, cols = len(mat), len(mat[0])',
    '    dist = [[-1]*cols for _ in range(rows)]',
    '    q = deque()',
    '    for r, c in all cells:',
    '        if mat[r][c] == 0:',
    '            dist[r][c] = 0; q.append((r, c))',
    '    while q:',
    '        r, c = q.popleft()',
    '        for dr, dc in DIRS:',
    '            nr, nc = r+dr, c+dc',
    '            if in_bounds and dist[nr][nc] == -1:',
    '                dist[nr][nc] = dist[r][c] + 1',
    '                q.append((nr, nc))',
    '    return dist',
  ],
  parse(s) {
    const grid = ggParseGrid(s, { max: 6 });
    if (grid.some(row => row.some(v => v !== 0 && v !== 1))) throw new Error('Cells must be 0 or 1');
    return { grid };
  },
  buildStates({ grid }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const rows = grid.length, cols = grid[0].length;
    const dist = grid.map(row => row.map(v => v === 0 ? 0 : -1));
    const q = [];
    for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) if (dist[r][c] === 0) q.push([r, c]);
    const snap = (line, clr, cur, title, text, pause) => domPushState(seq, { line, color: clr, dist: dist.map(r => [...r]), cur, explTitle: title, explText: text, pause }, ctx);
    snap(6, 'blue', null, 'Seed with every 0', `${q.length} zero-cell(s) enqueued at distance 0.`, true);
    const dirs = [[-1, 0], [1, 0], [0, -1], [0, 1]];
    while (q.length) {
      const [r, c] = q.shift();
      snap(9, 'amber', [r, c], 'Pop', `Popped (${r},${c}), distance ${dist[r][c]}.`);
      for (const [dr, dc] of dirs) {
        const nr = r + dr, nc = c + dc;
        if (nr >= 0 && nr < rows && nc >= 0 && nc < cols && dist[nr][nc] === -1) {
          dist[nr][nc] = dist[r][c] + 1; q.push([nr, nc]);
          snap(12, 'emerald', [r, c], 'Set distance', `(${nr},${nc}) reached for the first time — distance ${dist[nr][nc]}.`);
        }
      }
    }
    snap(13, 'emerald', null, 'Done', 'Every cell now holds its shortest distance to the nearest 0.', true);
    return seq;
  },
  renderDOM(container, s) {
    const grid = ggGridHTML(s.dist, (v, r, c) => {
      const isCur = s.cur && s.cur[0] === r && s.cur[1] === c;
      return { content: v, bg: v === 0 ? 'rgba(52,211,153,.2)' : `color-mix(in srgb, #38bdf8 ${Math.min(60, v * 12)}%, transparent)`, border: isCur ? '#fbbf24' : 'var(--border)' };
    });
    container.innerHTML = ggPanel('Distance to nearest 0', grid, 'padding:10px; display:inline-block;');
  }
});

/* ===================================== 015 · Shortest Path in Binary Matrix */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Shortest Path in Binary Matrix', short: 'Shortest Path (Binary Matrix)',
  idea: 'Plain BFS from (0,0) to (n-1,n-1) — the only twist is 8-directional movement (diagonals count as one step), so all 8 neighbors are checked, not just 4.',
  complexity: 'Time O(n²) · Space O(n²)',
  input: '000,001,000', hint: 'n×n grid of 0 (open) / 1 (blocked)',
  code: [
    'def shortestPathBinaryMatrix(grid):',
    '    n = len(grid)',
    '    if grid[0][0] or grid[-1][-1]: return -1',
    '    visited = {(0,0)}',
    '    q = deque([(0, 0, 1)])',
    '    while q:',
    '        r, c, length = q.popleft()',
    '        for dr, dc in DIRS_8:          # 8 directions, incl. diagonals',
    '            nr, nc = r+dr, c+dc',
    '            if in_bounds and grid[nr][nc]==0 and (nr,nc) not in visited:',
    '                if (nr, nc) == (n-1, n-1): return length + 1',
    '                visited.add((nr, nc)); q.append((nr, nc, length+1))',
    '    return -1',
  ],
  parse(s) {
    const grid = ggParseGrid(s, { max: 6 });
    if (grid.length !== grid[0].length) throw new Error('Grid must be square (n×n)');
    if (grid.some(row => row.some(v => v !== 0 && v !== 1))) throw new Error('Cells must be 0 or 1');
    return { grid };
  },
  buildStates({ grid }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const n = grid.length;
    const snap = (line, clr, cur, visited, title, text, pause) =>
      domPushState(seq, { line, color: clr, grid, cur, visited: [...visited], explTitle: title, explText: text, pause }, ctx);
    if (grid[0][0] || grid[n - 1][n - 1]) { snap(3, 'rose', null, new Set(), 'Blocked at an end', 'Start or end cell is blocked — return -1 immediately.', true); return seq; }
    const dirs8 = [[-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1]];
    const visited = new Set(['0,0']); const q = [[0, 0, 1]];
    snap(4, 'blue', [0, 0], visited, 'Start', 'BFS from (0,0), path length 1.', true);
    while (q.length) {
      const [r, c, length] = q.shift();
      snap(7, 'amber', [r, c], visited, 'Pop', `At (${r},${c}), length ${length}. Check all 8 neighbors.`);
      for (const [dr, dc] of dirs8) {
        const nr = r + dr, nc = c + dc, k = `${nr},${nc}`;
        if (nr >= 0 && nr < n && nc >= 0 && nc < n && grid[nr][nc] === 0 && !visited.has(k)) {
          if (nr === n - 1 && nc === n - 1) { snap(11, 'emerald', [nr, nc], visited, 'Reached the end!', `Reached (${n - 1},${n - 1}) — shortest path length: ${length + 1}.`, true); return seq; }
          visited.add(k); q.push([nr, nc, length + 1]);
          snap(12, 'emerald', [r, c], visited, 'Enqueue', `(${nr},${nc}) reached at length ${length + 1}.`);
        }
      }
    }
    snap(13, 'rose', null, visited, 'No path', 'Queue exhausted without reaching the end — return -1.', true);
    return seq;
  },
  renderDOM(container, s) {
    const vis = new Set(s.visited);
    const grid = ggGridHTML(s.grid, (v, r, c) => {
      const isCur = s.cur && s.cur[0] === r && s.cur[1] === c;
      const k = `${r},${c}`;
      if (v === 1) return { content: '🧱', bg: 'rgba(148,163,184,.15)' };
      return { content: isCur ? '●' : vis.has(k) ? '·' : '', bg: isCur ? 'rgba(251,191,36,.3)' : vis.has(k) ? 'rgba(52,211,153,.18)' : 'transparent', border: isCur ? '#fbbf24' : 'var(--border)' };
    });
    container.innerHTML = ggPanel('Grid (start top-left, target bottom-right)', grid, 'padding:10px; display:inline-block;');
  }
});

/* ==================================================================== 016 · Word Ladder */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Word Ladder', short: 'Word Ladder',
  idea: 'BFS where each "neighbor" of a word is generated on the fly by swapping one letter at a time and checking the word set — the implicit graph is never built explicitly. Discard a word from the set the moment it is enqueued so it can never be visited twice.',
  complexity: 'Time O(N × L × 26) · Space O(N × L)',
  input: 'hit,hot,dot,dog,lot,log,cog ; hit ; cog', hint: 'wordList ; beginWord ; endWord',
  code: [
    'def ladderLength(beginWord, endWord, wordList):',
    '    word_set = set(wordList)',
    '    if endWord not in word_set: return 0',
    '    q = deque([(beginWord, 1)])',
    '    word_set.discard(beginWord)',
    '    while q:',
    '        word, length = q.popleft()',
    '        if word == endWord: return length',
    '        for i in range(len(word)):',
    '            for c in "abcdefghijklmnopqrstuvwxyz":',
    '                candidate = word[:i] + c + word[i+1:]',
    '                if candidate in word_set:',
    '                    word_set.discard(candidate)',
    '                    q.append((candidate, length + 1))',
    '    return 0',
  ],
  parse(s) {
    const parts = s.split(';').map(x => x.trim());
    if (parts.length !== 3) throw new Error('Format: wordList ; beginWord ; endWord');
    const wordList = parts[0].split(',').map(w => w.trim().toLowerCase());
    const beginWord = parts[1].toLowerCase(), endWord = parts[2].toLowerCase();
    if (wordList.length > 10) throw new Error('Use at most 10 words');
    if (new Set(wordList.map(w => w.length)).size > 1 || wordList[0].length !== beginWord.length) throw new Error('All words must be the same length');
    return { wordList, beginWord, endWord };
  },
  buildStates({ wordList, beginWord, endWord }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const wordSet = new Set(wordList);
    const snap = (line, clr, cur, q, title, text, pause) =>
      domPushState(seq, { line, color: clr, wordSet: [...wordSet], cur, q: q.map(([w, l]) => `${w}(${l})`), explTitle: title, explText: text, pause }, ctx);
    if (!wordSet.has(endWord)) { snap(2, 'rose', null, [], 'Not reachable', `"${endWord}" is not in the word list — return 0.`, true); return seq; }
    const q = [[beginWord, 1]]; wordSet.delete(beginWord);
    snap(4, 'blue', beginWord, q, 'Start', `Start BFS from "${beginWord}" at length 1.`, true);
    const alpha = 'abcdefghijklmnopqrstuvwxyz';
    while (q.length) {
      const [word, length] = q.shift();
      snap(7, 'amber', word, q, 'Pop', `Popped "${word}" (length ${length}).`);
      if (word === endWord) { snap(8, 'emerald', word, q, 'Reached it!', `"${word}" is the end word — answer: ${length}.`, true); return seq; }
      const found = [];
      for (let i = 0; i < word.length; i++) for (const c of alpha) {
        const cand = word.slice(0, i) + c + word.slice(i + 1);
        if (wordSet.has(cand)) { wordSet.delete(cand); q.push([cand, length + 1]); found.push(cand); }
      }
      if (found.length) snap(13, 'emerald', word, q, 'One-letter neighbors found', `From "${word}": ${found.map(f => `"${f}"`).join(', ')} — enqueue all, remove from the set.`);
    }
    snap(14, 'rose', null, q, 'No path', 'Queue exhausted — end word unreachable.', true);
    return seq;
  },
  renderDOM(container, s) {
    container.innerHTML = `
      ${ggPanel('Remaining word set', chipRow(s.wordSet, { cls: w => w === s.cur ? 'active-k' : '' }), '')}
      ${ggPanel('Queue (word(length))', chipRow(s.q), 'margin-top:10px;')}`;
  }
});

/* ============================================================ 017 · Is Graph Bipartite? */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Is Graph Bipartite?', short: 'Is Graph Bipartite?',
  idea: 'Try to 2-color the graph with BFS: color the start 0, every neighbor gets the OPPOSITE color. If a neighbor already has the SAME color as the current node, two nodes that must differ are forced equal — not bipartite. Must restart from every uncolored node (the graph may be disconnected).',
  complexity: 'Time O(V + E) · Space O(V)',
  input: '0:1,3;1:0,2;2:1,3;3:0,2', hint: 'adjacency list "node:nbr,nbr;..."',
  code: [
    'def isBipartite(graph):',
    '    n = len(graph)',
    '    color = [-1] * n',
    '    for s in range(n):',
    '        if color[s] != -1: continue',
    '        color[s] = 0',
    '        q = deque([s])',
    '        while q:',
    '            u = q.popleft()',
    '            for v in graph[u]:',
    '                if color[v] == -1:',
    '                    color[v] = 1 - color[u]; q.append(v)',
    '                elif color[v] == color[u]:',
    '                    return False        # forced same color — conflict',
    '    return True',
  ],
  parse(s) {
    const entries = s.split(';').map(x => x.trim()).filter(Boolean);
    const n = entries.length;
    if (n < 2 || n > 8) throw new Error('Use 2-8 nodes');
    const graph = Array.from({ length: n }, () => []);
    entries.forEach(e => {
      const [idPart, nbrPart] = e.split(':');
      const id = Number(idPart);
      const nbrs = (nbrPart || '').split(',').filter(Boolean).map(Number);
      graph[id] = nbrs;
    });
    return { graph, n };
  },
  buildStates({ graph, n }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const color = Array(n).fill(-1);
    const snap = (line, clr, cur, conflict, title, text, pause) =>
      domPushState(seq, { line, color: clr, n, graph, colors: [...color], cur, conflict, explTitle: title, explText: text, pause }, ctx);
    for (let start = 0; start < n; start++) {
      if (color[start] !== -1) continue;
      color[start] = 0;
      snap(6, 'blue', start, null, 'New component root', `Color node ${start} = 0 and BFS from it.`);
      const q = [start];
      while (q.length) {
        const u = q.shift();
        snap(9, 'amber', u, null, 'Expand', `Expand ${u} (color ${color[u]}).`);
        for (const v of graph[u]) {
          if (color[v] === -1) { color[v] = 1 - color[u]; q.push(v); snap(11, 'emerald', u, null, 'Color opposite', `Color ${v} = ${color[v]} (opposite of ${u}) and enqueue it.`); }
          else if (color[v] === color[u]) { snap(13, 'rose', u, [u, v], 'Conflict!', `${v} already has color ${color[v]}, same as ${u} — they're neighbors, so this can't be bipartite.`, true); return seq; }
        }
      }
    }
    snap(14, 'emerald', null, null, 'Bipartite!', 'Every node colored with no conflicts — the graph is bipartite.', true);
    return seq;
  },
  renderDOM(container, s) {
    const edges = []; s.graph.forEach((nbrs, u) => nbrs.forEach(v => { if (u < v) edges.push([u, v]); }));
    const svg = ggGraphSVG(s.n, edges,
      i => s.colors[i] === -1 ? {} : { fill: s.colors[i] === 0 ? 'rgba(56,189,248,.25)' : 'rgba(244,114,182,.25)', stroke: s.colors[i] === 0 ? '#38bdf8' : '#f472b6' },
      ([u, v]) => s.conflict && ((u === s.conflict[0] && v === s.conflict[1]) || (u === s.conflict[1] && v === s.conflict[0])) ? { stroke: '#f43f5e', width: 3 } : {});
    container.innerHTML = ggPanel('Graph (blue / pink = the two color classes)', svg, 'display:inline-block; min-width:260px;');
  }
});

/* =================================================================== 018 · Open the Lock */
defineAlgoDom('14_graphs', {
  type: 'dom',
  title: 'Open the Lock', short: 'Open the Lock',
  idea: 'BFS over an implicit graph: each 4-digit combo is a node, edges connect combos that are one wheel-turn apart (8 neighbors per combo). Level-by-level BFS from "0000" gives the minimum turns; deadends are simply never-visitable nodes.',
  complexity: 'Time O(10⁴) states · Space O(10⁴)',
  input: '0201,0101,0102,1212,2002 ; 0202', hint: 'deadends ; target',
  code: [
    'def openLock(deadends, target):',
    '    seen = set(deadends)',
    '    if "0000" in seen: return -1',
    '    seen.add("0000")',
    '    q = deque(["0000"])',
    '    steps = 0',
    '    while q:',
    '        for _ in range(len(q)):       # process one BFS level at a time',
    '            code = q.popleft()',
    '            if code == target: return steps',
    '            for nxt in neighbors(code):   # 8 one-turn neighbors',
    '                if nxt not in seen:',
    '                    seen.add(nxt); q.append(nxt)',
    '        steps += 1',
    '    return -1',
  ],
  parse(s) {
    const parts = s.split(';').map(x => x.trim());
    if (parts.length !== 2) throw new Error('Format: deadends ; target');
    const deadends = parts[0].split(',').map(x => x.trim()).filter(Boolean);
    const target = parts[1];
    if (!/^\d{4}$/.test(target)) throw new Error('target must be 4 digits');
    deadends.forEach(d => { if (!/^\d{4}$/.test(d)) throw new Error('deadends must be 4-digit codes'); });
    return { deadends, target };
  },
  buildStates({ deadends, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready.' };
    const seen = new Set(deadends);
    const snap = (line, clr, cur, frontier, steps, title, text, pause) =>
      domPushState(seq, { line, color: clr, cur, frontier: [...frontier], steps, seenCount: seen.size, explTitle: title, explText: text, pause }, ctx);
    if (seen.has('0000')) { snap(3, 'rose', null, [], 0, 'Start is dead', '"0000" is itself a deadend — return -1.', true); return seq; }
    seen.add('0000'); let q = ['0000']; let steps = 0;
    snap(5, 'blue', null, q, steps, 'Start BFS', 'Start from "0000" with 0 turns.', true);
    function neighbors(code) {
      const out = [];
      for (let i = 0; i < 4; i++) for (const d of [1, 9]) {
        const digit = (Number(code[i]) + d) % 10;
        out.push(code.slice(0, i) + digit + code.slice(i + 1));
      }
      return out;
    }
    while (q.length) {
      if (q.includes(target)) { snap(12, 'emerald', target, q, steps, 'Unlocked!', `Target "${target}" is in this level's frontier — reached in ${steps} turn(s).`, true); return seq; }
      snap(11, 'amber', null, q, steps, 'Check this level', `Checking ${q.length} code(s) reachable in ${steps} turn(s) — none is the target yet, expand them all before moving to the next level.`);
      const next = [];
      for (const code of q) for (const nxt of neighbors(code)) if (!seen.has(nxt)) { seen.add(nxt); next.push(nxt); }
      steps++;
      q = next;
      if (q.length) snap(14, 'blue', null, q, steps, 'Next level', `${q.length} new combo(s) reachable in ${steps} turn(s).`);
    }
    snap(15, 'rose', null, [], steps, 'Unreachable', 'Queue exhausted without reaching the target — return -1.', true);
    return seq;
  },
  renderDOM(container, s) {
    container.innerHTML = `<div style="display:flex; gap:16px; align-items:flex-start; flex-wrap:wrap;">
      ${ggPanel('Current code', `<div style="font-size:36px;font-weight:800;letter-spacing:4px;font-family:var(--mono);text-align:center;color:var(--accent);">${s.cur || '····'}</div>
        <div style="text-align:center;color:var(--text-dim);font-size:12px;margin-top:4px;">${s.steps} turn(s) so far</div>`, 'min-width:180px;')}
      ${ggPanel(`Frontier (${s.frontier.length})`, chipRow(s.frontier.slice(0, 24)), 'flex:1; min-width:220px;')}
    </div>`;
  }
});
