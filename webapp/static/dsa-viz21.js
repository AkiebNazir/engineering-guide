/* ============================================================================
   Visualizations for 15_advanced_graphs (13 remaining problems).
   Reuses ggGridHTML / ggGraphSVG / ggPanel / ggParseGrid from dsa-viz20.js.
   ========================================================================= */
'use strict';

/* small shared bits ------------------------------------------------------- */
function agChip(label, value, on) {
  return `<span class="stat-chip" style="${on ? 'border-color:var(--accent);color:var(--accent);' : ''}"><span>${label}</span><b>${value}</b></span>`;
}
function agChips(items) { return `<div style="display:flex;gap:8px;flex-wrap:wrap;">${items}</div>`; }

/* ============================================================ 002 · Satisfiability of Equality Equations */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Satisfiability of Equality Equations', short: 'Equality Equations',
  idea: 'Union-Find, two passes. Union every "==" pair first so transitivity is fully resolved, then a "!=" is a contradiction exactly when its two letters ended up in the same set.',
  complexity: 'Time O(n) · Space O(1) — at most 26 variables',
  input: 'a==b, b!=c, c==a', hint: 'comma-separated equations like a==b, b!=c',
  code: [
    'def equationsPossible(equations):',
    '    uf = UnionFind(26)',
    '    for eq in equations:      # pass 1',
    '        if eq[1] == "=":',
    '            uf.union(idx(eq[0]), idx(eq[3]))',
    '    for eq in equations:      # pass 2',
    '        if eq[1] == "!":',
    '            if uf.find(idx(eq[0])) == uf.find(idx(eq[3])):',
    '                return False',
    '    return True',
  ],
  parse(s) {
    const eqs = s.split(',').map(x => x.trim()).filter(Boolean);
    if (!eqs.length) throw new Error('Enter at least one equation, e.g. a==b');
    if (eqs.length > 10) throw new Error('Use at most 10 equations for visualization');
    eqs.forEach(e => { if (!/^[a-z](==|!=)[a-z]$/.test(e)) throw new Error(`"${e}" should look like a==b or a!=b (single lowercase letters)`); });
    return { eqs };
  },
  buildStates({ eqs }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const letters = [...new Set(eqs.flatMap(e => [e[0], e[3]]))].sort();
    const idOf = {}; letters.forEach((l, i) => idOf[l] = i);
    const parent = letters.map((_, i) => i);
    const find = x => { while (parent[x] !== x) x = parent[x]; return x; };
    const edges = eqs.map(e => [idOf[e[0]], idOf[e[3]], e[1] === '=' ? 'eq' : 'neq']);
    const snapS = (extra) => ({ letters, parent: [...parent], edges, ...extra });

    domPushState(seq, { line: 2, color: 'default', ...snapS({ cur: -1 }),
      explTitle: 'Initialization', explText: `Each of the ${letters.length} letters starts as its own set.` }, ctx);

    domPushState(seq, { line: 3, color: 'blue', ...snapS({ cur: -1 }),
      explTitle: 'Pass 1: unions', explText: 'Union every "==" pair first, so transitivity is fully resolved before any "!=" is checked.' }, ctx);
    eqs.forEach((e, i) => {
      if (e[1] !== '=') return;
      const a = idOf[e[0]], b = idOf[e[3]];
      const ra = find(a), rb = find(b);
      if (ra !== rb) parent[rb] = ra;
      domPushState(seq, { line: 4, color: 'emerald', ...snapS({ cur: i }),
        explTitle: `Union ${e[0]} and ${e[3]}`, explText: ra === rb ? `${e[0]} and ${e[3]} were already in the same set.` : `Merge the set containing ${e[3]} into the set containing ${e[0]}.` }, ctx);
    });

    domPushState(seq, { line: 6, color: 'blue', ...snapS({ cur: -1 }),
      explTitle: 'Pass 2: contradictions', explText: 'Now check every "!=" — it is a contradiction iff both letters ended up in the same set.' }, ctx);
    for (let i = 0; i < eqs.length; i++) {
      const e = eqs[i];
      if (e[1] !== '!') continue;
      const a = idOf[e[0]], b = idOf[e[3]];
      const ra = find(a), rb = find(b);
      if (ra === rb) {
        domPushState(seq, { line: 8, color: 'rose', ...snapS({ cur: i, result: false }),
          explTitle: 'Contradiction found', explText: `${e[0]} and ${e[3]} were forced equal in pass 1, but this says they differ. Return False.`, pause: true }, ctx);
        return seq;
      }
      domPushState(seq, { line: 7, color: 'default', ...snapS({ cur: i }),
        explTitle: `Check ${e[0]} != ${e[3]}`, explText: `${e[0]} and ${e[3]} are in different sets — no contradiction yet.` }, ctx);
    }
    domPushState(seq, { line: 10, color: 'emerald', ...snapS({ cur: -1, result: true }),
      explTitle: 'Complete', explText: 'No contradiction found. Return True.', pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const n = s.letters.length;
    const graph = ggGraphSVG(n, s.edges.map(e => [e[0], e[1]]),
      i => {
        const root = (x => { let p = s.parent[x]; while (s.parent[p] !== p) p = s.parent[p]; return p; })(i);
        return { label: s.letters[i], fill: `hsl(${(root * 67) % 360} 55% 22%)`, stroke: `hsl(${(root * 67) % 360} 65% 55%)`, color: '#fff' };
      },
      (edgeIdxPair) => {
        const idx = s.edges.findIndex(e => e[0] === edgeIdxPair[0] && e[1] === edgeIdxPair[1]);
        const isCur = idx === s.cur;
        const kind = s.edges[idx][2];
        return { stroke: isCur ? (kind === 'eq' ? 'var(--emerald)' : 'var(--rose)') : (kind === 'eq' ? 'rgba(52,211,153,.4)' : 'rgba(244,63,94,.4)'), width: isCur ? 3.5 : 2 };
      });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel('Variables & equations (green = ==, red = !=)', graph)}
        ${ggPanel('Result', `<div style="font-size:18px;font-weight:700;color:${s.result === true ? 'var(--emerald)' : s.result === false ? 'var(--rose)' : 'var(--text-dim)'};">${s.result === true ? 'True — satisfiable' : s.result === false ? 'False — contradiction' : '?'}</div>`)}
      </div>`;
  }
});

/* ============================================================ 004 · Cheapest Flights Within K Stops */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Cheapest Flights Within K Stops', short: 'Cheapest Flights',
  idea: 'Bellman-Ford, capped at k+1 rounds. Relax every edge against a snapshot of last round’s distances — snapshotting is what stops one round from silently chaining more than one edge.',
  complexity: 'Time O(k × E) · Space O(V)',
  input: '4; 0; 3; 1; 0,1,100; 1,2,100; 2,0,100; 1,3,600; 2,3,200', hint: 'n; src; dst; k; u,v,w; ...',
  code: [
    'def findCheapestPrice(n, flights, src, dst, k):',
    '    dist = [inf] * n',
    '    dist[src] = 0',
    '    for _ in range(k + 1):',
    '        snapshot = dist[:]',
    '        for u, v, w in flights:',
    '            if snapshot[u] + w < dist[v]:',
    '                dist[v] = snapshot[u] + w',
    '    return dist[dst] if dist[dst] < inf else -1',
  ],
  parse(s) {
    const parts = s.split(';').map(x => x.trim());
    if (parts.length < 5) throw new Error('Format: n; src; dst; k; u,v,w; ...');
    const [n, src, dst, k] = parts.slice(0, 4).map(Number);
    if ([n, src, dst, k].some(Number.isNaN)) throw new Error('n, src, dst, k must be integers');
    if (n > 8) throw new Error('Use at most 8 cities for visualization');
    const flights = parts.slice(4).filter(Boolean).map(e => {
      const v = e.split(',').map(Number);
      if (v.length !== 3 || v.some(Number.isNaN)) throw new Error('Edges must be u,v,w');
      return v;
    });
    return { n, src, dst, k, flights };
  },
  buildStates({ n, src, dst, k, flights }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const INF = Infinity;
    let dist = new Array(n).fill(INF); dist[src] = 0;
    const snapS = extra => ({ n, flights, dist: dist.map(d => d === INF ? '∞' : d), src, dst, ...extra });
    domPushState(seq, { line: 2, color: 'default', ...snapS({ round: 0, edge: -1 }),
      explTitle: 'Initialization', explText: `dist[${src}] = 0, everywhere else ∞. We get k+1 = ${k + 1} rounds of relaxation.` }, ctx);
    for (let r = 0; r < k + 1; r++) {
      const snapshot = [...dist];
      domPushState(seq, { line: 4, color: 'blue', ...snapS({ round: r + 1, edge: -1 }),
        explTitle: `Round ${r + 1} of ${k + 1}`, explText: 'Snapshot the current distances — this round only relaxes against last round’s values.' }, ctx);
      flights.forEach(([u, v, w], ei) => {
        const su = snapshot[u] === INF ? INF : snapshot[u];
        const cand = su === INF ? INF : su + w;
        if (cand < dist[v]) {
          dist[v] = cand;
          domPushState(seq, { line: 7, color: 'emerald', ...snapS({ round: r + 1, edge: ei }),
            explTitle: `Relax ${u}→${v}`, explText: `snapshot[${u}] + ${w} = ${cand} improves dist[${v}]. Update it (but not until next round can it be used again).` }, ctx);
        } else {
          domPushState(seq, { line: 6, color: 'default', ...snapS({ round: r + 1, edge: ei }),
            explTitle: `Check ${u}→${v}`, explText: su === INF ? `City ${u} is still unreached this round — nothing to relax.` : `snapshot[${u}] + ${w} = ${cand} does not improve dist[${v}] = ${dist[v] === INF ? '∞' : dist[v]}.` }, ctx);
        }
      });
    }
    const ans = dist[dst] === INF ? -1 : dist[dst];
    domPushState(seq, { line: 8, color: ans === -1 ? 'rose' : 'emerald', ...snapS({ round: k + 1, edge: -1, done: true }),
      explTitle: 'Complete', explText: `dist[${dst}] = ${ans === -1 ? '∞ → unreachable within k stops → -1' : ans}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const graph = ggGraphSVG(s.n, s.flights.map(f => [f[0], f[1]]),
      i => ({ label: `${i}\n${s.dist[i]}`, fill: i === s.src ? 'rgba(56,189,248,.25)' : i === s.dst ? 'rgba(52,211,153,.25)' : null, stroke: i === s.src ? 'var(--accent)' : i === s.dst ? 'var(--emerald)' : null }),
      ([u, v]) => { const ei = s.flights.findIndex(f => f[0] === u && f[1] === v); return { stroke: ei === s.edge ? 'var(--accent)' : 'var(--border)', width: ei === s.edge ? 3.5 : 2 }; });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel(`Round ${s.round} of relaxation`, graph)}
        ${ggPanel('dist[]', agChips(s.dist.map((d, i) => agChip(i, d, i === s.dst)).join('')))}
      </div>`;
  }
});

/* ============================================================ 005 · Min Cost to Connect All Points */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Min Cost to Connect All Points', short: 'Connect All Points',
  idea: 'Prim’s MST, array-based (no heap needed — the graph is dense/complete). Repeatedly pull the closest not-yet-in-tree point and relax everyone else’s distance using the Manhattan metric.',
  complexity: 'Time O(n²) · Space O(n) — appropriate since a complete graph has O(n²) edges anyway',
  input: '0,0; 2,2; 3,10; 5,2; 7,0', hint: 'points as x,y; x,y; ...',
  code: [
    'def minCostConnectPoints(points):',
    '    n = len(points)',
    '    in_tree = [False] * n',
    '    min_dist = [inf] * n; min_dist[0] = 0',
    '    total = 0',
    '    for _ in range(n):',
    '        u = argmin over not-in_tree of min_dist',
    '        in_tree[u] = True; total += min_dist[u]',
    '        for v not in_tree:',
    '            d = manhattan(u, v)',
    '            if d < min_dist[v]: min_dist[v] = d',
    '    return total',
  ],
  parse(s) {
    const pts = s.split(';').map(x => x.trim()).filter(Boolean).map(p => p.split(',').map(Number));
    if (pts.length < 2) throw new Error('Enter at least 2 points, e.g. 0,0; 2,2');
    if (pts.length > 8) throw new Error('Use at most 8 points for visualization');
    pts.forEach(p => { if (p.length !== 2 || p.some(Number.isNaN)) throw new Error('Each point must be x,y'); });
    return { pts };
  },
  buildStates({ pts }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const n = pts.length;
    const man = (i, j) => Math.abs(pts[i][0] - pts[j][0]) + Math.abs(pts[i][1] - pts[j][1]);
    const inTree = new Array(n).fill(false);
    const minDist = new Array(n).fill(Infinity); minDist[0] = 0;
    const mstEdges = []; let total = 0;
    const snapS = extra => ({ pts, inTree: [...inTree], minDist: minDist.map(d => d === Infinity ? '∞' : d), mstEdges: [...mstEdges], total, ...extra });
    domPushState(seq, { line: 3, color: 'default', ...snapS({ u: -1 }),
      explTitle: 'Initialization', explText: 'minDist[0] = 0, everywhere else ∞. Point 0 will be pulled in first.' }, ctx);
    for (let step = 0; step < n; step++) {
      let u = -1, best = Infinity;
      for (let c = 0; c < n; c++) if (!inTree[c] && minDist[c] < best) { u = c; best = minDist[c]; }
      inTree[u] = true; total += best;
      if (step > 0) {
        let from = -1;
        for (let v = 0; v < n; v++) if (v !== u) mstEdges.forEach(() => {});
        mstEdges.push([u, best]);
      }
      domPushState(seq, { line: 7, color: 'emerald', ...snapS({ u }),
        explTitle: `Pull in point ${u}`, explText: step === 0 ? `Point ${u} starts the tree at cost 0.` : `Point ${u} is the closest point not yet in the tree (cost ${best}). Add it — running total is now ${total}.` }, ctx);
      for (let v = 0; v < n; v++) {
        if (inTree[v]) continue;
        const d = man(u, v);
        if (d < minDist[v]) {
          minDist[v] = d;
          domPushState(seq, { line: 10, color: 'blue', ...snapS({ u, v }),
            explTitle: `Relax point ${v}`, explText: `Manhattan distance from ${u} to ${v} is ${d}, which improves minDist[${v}].` }, ctx);
        }
      }
    }
    domPushState(seq, { line: 11, color: 'emerald', ...snapS({ u: -1, done: true }),
      explTitle: 'Complete', explText: `Every point is connected. Minimum total cost = ${total}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const xs = s.pts.map(p => p[0]), ys = s.pts.map(p => p[1]);
    const minX = Math.min(...xs), maxX = Math.max(...xs), minY = Math.min(...ys), maxY = Math.max(...ys);
    const W = 320, H = 220, pad = 30;
    const sx = x => pad + (maxX === minX ? W / 2 - pad : (x - minX) / (maxX - minX) * (W - 2 * pad));
    const sy = y => pad + (maxY === minY ? H / 2 - pad : (y - minY) / (maxY - minY) * (H - 2 * pad));
    const edgesSvg = s.mstEdges.map(() => '').join('');
    let lines = '';
    // Recompute which point each MST edge connects to (nearest already-in-tree point at the time) for drawing;
    // simplest faithful rendering: connect each non-first inTree point to its nearest earlier inTree point.
    const order = [];
    s.pts.forEach((_, i) => { if (s.inTree[i]) order.push(i); });
    for (let oi = 1; oi < order.length; oi++) {
      const v = order[oi];
      let best = -1, bestD = Infinity;
      for (let oj = 0; oj < oi; oj++) {
        const u = order[oj];
        const d = Math.abs(s.pts[u][0] - s.pts[v][0]) + Math.abs(s.pts[u][1] - s.pts[v][1]);
        if (d < bestD) { bestD = d; best = u; }
      }
      if (best !== -1) lines += `<line x1="${sx(s.pts[best][0])}" y1="${sy(s.pts[best][1])}" x2="${sx(s.pts[v][0])}" y2="${sy(s.pts[v][1])}" stroke="var(--emerald)" stroke-width="2.5" />`;
    }
    const dots = s.pts.map((p, i) => `<circle cx="${sx(p[0])}" cy="${sy(p[1])}" r="10" fill="${i === s.u ? 'rgba(56,189,248,.4)' : s.inTree[i] ? 'rgba(52,211,153,.3)' : 'var(--surface)'}" stroke="${i === s.u ? 'var(--accent)' : s.inTree[i] ? 'var(--emerald)' : 'var(--border)'}" stroke-width="2.5" /><text x="${sx(p[0])}" y="${sy(p[1]) + 4}" text-anchor="middle" font-size="11" font-weight="700" fill="var(--text-bright)" font-family="var(--mono)">${i}</text>`).join('');
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel('Points on the plane (green edges = MST so far)', `<svg viewBox="0 0 ${W} ${H}" style="width:100%; max-width:${W}px; height:auto; display:block; margin:0 auto;">${lines}${dots}</svg>`)}
        ${ggPanel('minDist[] to the tree', agChips(s.minDist.map((d, i) => agChip(i, d, i === s.u)).join('')))}
        ${ggPanel('Running total', `<div style="font-size:18px;font-weight:700;color:var(--emerald);">${s.total}</div>`)}
      </div>`;
  }
});

/* Parse a small integer grid: rows separated by ";", cells by "," */
function agParseIntGrid(s, { max = 6 } = {}) {
  const rows = s.split(';').map(r => r.trim()).filter(Boolean);
  if (!rows.length) throw new Error('Enter at least one row, cells comma-separated, rows separated by ";"');
  if (rows.length > max) throw new Error(`Use at most ${max} rows for visualization`);
  const grid = rows.map(r => r.split(',').map(x => Number(x.trim())));
  const w = grid[0].length;
  if (w > max) throw new Error(`Use at most ${max} columns for visualization`);
  grid.forEach(r => { if (r.length !== w || r.some(Number.isNaN)) throw new Error('Every row must have the same number of integer cells'); });
  return grid;
}

/* ============================================================ 006 · Path With Minimum Effort */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Path With Minimum Effort', short: 'Minimum Effort Path',
  idea: 'Minimax Dijkstra: a "distance" here is the largest single step so far, not a sum. Always expand the cell whose worst step is currently smallest.',
  complexity: 'Time O(R·C log(R·C)) · Space O(R·C)',
  input: '1,2,2; 3,8,2; 5,3,5', hint: 'grid rows of heights; rows separated by ";", cells by ","',
  code: [
    'def minimumEffortPath(heights):',
    '    effort = [[inf]*cols for _ in range(rows)]',
    '    effort[0][0] = 0',
    '    heap = [(0, 0, 0)]',
    '    while heap:',
    '        e, r, c = heappop(heap)',
    '        if e > effort[r][c]: continue',
    '        if (r, c) == (rows-1, cols-1): return e',
    '        for nr, nc in neighbors(r, c):',
    '            cost = max(e, abs(heights[r][c]-heights[nr][nc]))',
    '            if cost < effort[nr][nc]:',
    '                effort[nr][nc] = cost',
    '                heappush(heap, (cost, nr, nc))',
  ],
  parse(s) { return { heights: agParseIntGrid(s) }; },
  buildStates({ heights }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const R = heights.length, C = heights[0].length;
    const INF = Infinity;
    const effort = Array.from({ length: R }, () => new Array(C).fill(INF));
    effort[0][0] = 0;
    let heap = [[0, 0, 0]];
    const snapS = extra => ({ heights, effort: effort.map(r => r.map(v => v === INF ? '∞' : v)), heap: [...heap], ...extra });
    domPushState(seq, { line: 3, color: 'default', ...snapS({ r: -1, c: -1 }),
      explTitle: 'Initialization', explText: 'effort[0][0] = 0, everywhere else ∞. Push (0, 0, 0) onto the heap.' }, ctx);
    if (R === 1 && C === 1) {
      domPushState(seq, { line: 8, color: 'emerald', ...snapS({ r: 0, c: 0, done: true, ans: 0 }), explTitle: 'Single cell', explText: 'Start equals destination — the answer is 0.', pause: true }, ctx);
      return seq;
    }
    while (heap.length) {
      heap.sort((a, b) => a[0] - b[0]);
      const [e, r, c] = heap.shift();
      if (e > effort[r][c]) { domPushState(seq, { line: 7, color: 'default', ...snapS({ r, c }), explTitle: 'Stale entry', explText: `(${r},${c}) was already finalized with a smaller effort. Skip.` }, ctx); continue; }
      domPushState(seq, { line: 6, color: 'blue', ...snapS({ r, c }),
        explTitle: `Pop (${r},${c})`, explText: `This is the frontier cell whose worst step so far (${e}) is smallest.` }, ctx);
      if (r === R - 1 && c === C - 1) {
        domPushState(seq, { line: 8, color: 'emerald', ...snapS({ r, c, done: true, ans: e }),
          explTitle: 'Reached the destination', explText: `Answer = ${e}.`, pause: true }, ctx);
        return seq;
      }
      for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nr = r + dr, nc = c + dc;
        if (nr < 0 || nr >= R || nc < 0 || nc >= C) continue;
        const cost = Math.max(e, Math.abs(heights[r][c] - heights[nr][nc]));
        if (cost < effort[nr][nc]) {
          effort[nr][nc] = cost; heap.push([cost, nr, nc]);
          domPushState(seq, { line: 11, color: 'emerald', ...snapS({ r, c, nr, nc }),
            explTitle: `Relax (${nr},${nc})`, explText: `max(${e}, |${heights[r][c]}-${heights[nr][nc]}|) = ${cost} improves effort[${nr}][${nc}].` }, ctx);
        }
      }
    }
    return seq;
  },
  renderDOM(container, s, spec) {
    const R = s.heights.length, C = s.heights[0].length;
    const grid = ggGridHTML(s.heights, (v, r, c) => {
      const isCur = r === s.r && c === s.c;
      const isNb = r === s.nr && c === s.nc;
      return { content: `${v}<br><span style="font-size:9px;opacity:.7;">${s.effort[r][c]}</span>`,
        bg: isCur ? 'rgba(56,189,248,.25)' : isNb ? 'rgba(52,211,153,.2)' : 'var(--surface)',
        border: isCur ? 'var(--accent)' : isNb ? 'var(--emerald)' : 'var(--border)', fontSize: 12 };
    }, { cell: 52 });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel('Grid (height, effort-so-far)', grid)}
        ${ggPanel('Heap (effort, r, c)', agChips(s.heap.map(h => agChip('', `(${h[0]},${h[1]},${h[2]})`)).join('') || '<span style="color:var(--text-dim);">empty</span>')) }
        ${s.done ? ggPanel('Answer', `<div style="font-size:18px;font-weight:700;color:var(--emerald);">${s.ans}</div>`) : ''}
      </div>`;
  }
});

/* ============================================================ 007 · Course Schedule IV */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Course Schedule IV', short: 'Course Schedule IV',
  idea: 'Floyd-Warshall transitive closure, precomputed once: reach[i][j] becomes true if some intermediate course k makes i reach k and k reach j.',
  complexity: 'Time O(V³ + Q) · Space O(V²)',
  input: '5; 1,0 , 2,1 , 3,2 , 3,1 , 4,3; 4,0 , 4,1 , 3,0 , 0,4', hint: 'numCourses; prereqs a,b ,...; queries u,v ,...',
  code: [
    'def checkIfPrerequisite(V, prerequisites, queries):',
    '    reach = [[False]*V for _ in range(V)]',
    '    for a, b in prerequisites: reach[a][b] = True',
    '    for k in range(V):',
    '        for i in range(V):',
    '            if not reach[i][k]: continue',
    '            for j in range(V):',
    '                if reach[k][j]: reach[i][j] = True',
    '    return [reach[u][v] for u, v in queries]',
  ],
  parse(s) {
    const parts = s.split(';');
    if (parts.length < 3) throw new Error('Format: numCourses; prereqs a,b ,...; queries u,v ,...');
    const V = parseInt(parts[0].trim());
    if (!V || V > 7) throw new Error('Use 1-7 courses for visualization');
    const parsePairs = str => {
      const nums = str.split(',').map(x => x.trim()).filter(Boolean).map(Number);
      if (nums.some(Number.isNaN)) throw new Error('Pairs must be numbers, comma-separated, taken two at a time');
      const pairs = [];
      for (let i = 0; i + 1 < nums.length; i += 2) pairs.push([nums[i], nums[i + 1]]);
      return pairs;
    };
    const prereqs = parsePairs(parts[1]);
    const queries = parsePairs(parts[2]);
    return { V, prereqs, queries };
  },
  buildStates({ V, prereqs, queries }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const reach = Array.from({ length: V }, () => new Array(V).fill(false));
    prereqs.forEach(([a, b]) => { reach[a][b] = true; });
    const snapS = extra => ({ V, reach: reach.map(r => [...r]), ...extra });
    domPushState(seq, { line: 3, color: 'default', ...snapS({ i: -1, j: -1, k: -1 }),
      explTitle: 'Seed direct prerequisites', explText: `reach[a][b] = True for each direct prerequisite pair.` }, ctx);
    for (let k = 0; k < V; k++) {
      domPushState(seq, { line: 4, color: 'blue', ...snapS({ i: -1, j: -1, k }),
        explTitle: `Intermediate course ${k}`, explText: `Try routing paths through course ${k}.` }, ctx);
      for (let i = 0; i < V; i++) {
        if (!reach[i][k]) continue;
        for (let j = 0; j < V; j++) {
          if (reach[k][j] && !reach[i][j]) {
            reach[i][j] = true;
            domPushState(seq, { line: 8, color: 'emerald', ...snapS({ i, j, k }),
              explTitle: `${i} → ${k} → ${j}`, explText: `${i} reaches ${k} and ${k} reaches ${j}, so ${i} reaches ${j} too.` }, ctx);
          }
        }
      }
    }
    domPushState(seq, { line: 9, color: 'emerald', ...snapS({ i: -1, j: -1, k: -1, queries: queries.map(([u, v]) => [u, v, reach[u][v]]) }),
      explTitle: 'Answer queries', explText: 'Each query is now a single O(1) lookup in the reach matrix.', pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const grid = ggGridHTML(s.reach.map((row, i) => row.map((v, j) => (i === j ? '·' : v ? '1' : '0'))), (v, r, c) => {
      const isCur = (r === s.i && c === s.j) || (r === s.k && c === s.j) || (r === s.i && c === s.k);
      return { content: v, bg: v === '1' ? 'rgba(52,211,153,.18)' : 'var(--surface)', border: isCur ? 'var(--accent)' : 'var(--border)', color: v === '1' ? 'var(--emerald)' : 'var(--text-dim)' };
    }, { cell: 34 });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel('reach[i][j] matrix', grid)}
        ${s.queries ? ggPanel('Query answers', agChips(s.queries.map(([u, v, r]) => agChip(`${u}→${v}`, r ? 'True' : 'False', r)).join(''))) : ''}
      </div>`;
  }
});

/* ============================================================ 008 · Swim in Rising Water */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Swim in Rising Water', short: 'Swim in Rising Water',
  idea: 'The same minimax-Dijkstra shape as Path With Minimum Effort, but the "cost" of a cell is its own elevation, not the difference to a neighbor.',
  complexity: 'Time O(n² log(n²)) · Space O(n²)',
  input: '0,2; 1,3', hint: 'square grid rows; rows separated by ";", cells by ","',
  code: [
    'def swimInWater(grid):',
    '    cost = [[inf]*n for _ in range(n)]',
    '    cost[0][0] = grid[0][0]',
    '    heap = [(grid[0][0], 0, 0)]',
    '    while heap:',
    '        t, r, c = heappop(heap)',
    '        if t > cost[r][c]: continue',
    '        if (r, c) == (n-1, n-1): return t',
    '        for nr, nc in neighbors(r, c):',
    '            nt = max(t, grid[nr][nc])',
    '            if nt < cost[nr][nc]:',
    '                cost[nr][nc] = nt',
    '                heappush(heap, (nt, nr, nc))',
  ],
  parse(s) {
    const grid = agParseIntGrid(s, { max: 5 });
    if (grid.length !== grid[0].length) throw new Error('Grid must be square for this problem');
    return { grid };
  },
  buildStates({ grid }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const n = grid.length;
    const INF = Infinity;
    const cost = Array.from({ length: n }, () => new Array(n).fill(INF));
    cost[0][0] = grid[0][0];
    let heap = [[grid[0][0], 0, 0]];
    const snapS = extra => ({ grid, cost: cost.map(r => r.map(v => v === INF ? '∞' : v)), heap: [...heap], ...extra });
    domPushState(seq, { line: 3, color: 'default', ...snapS({ r: -1, c: -1 }),
      explTitle: 'Initialization', explText: `cost[0][0] = ${grid[0][0]} (you must at least wait for your own tile to flood). Push it onto the heap.` }, ctx);
    if (n === 1) {
      domPushState(seq, { line: 7, color: 'emerald', ...snapS({ r: 0, c: 0, done: true, ans: grid[0][0] }), explTitle: 'Single cell', explText: `Answer = ${grid[0][0]}.`, pause: true }, ctx);
      return seq;
    }
    while (heap.length) {
      heap.sort((a, b) => a[0] - b[0]);
      const [t, r, c] = heap.shift();
      if (t > cost[r][c]) { domPushState(seq, { line: 6, color: 'default', ...snapS({ r, c }), explTitle: 'Stale entry', explText: `(${r},${c}) already finalized lower. Skip.` }, ctx); continue; }
      domPushState(seq, { line: 5, color: 'blue', ...snapS({ r, c }),
        explTitle: `Pop (${r},${c})`, explText: `Smallest time-to-reach on the frontier is ${t}.` }, ctx);
      if (r === n - 1 && c === n - 1) {
        domPushState(seq, { line: 7, color: 'emerald', ...snapS({ r, c, done: true, ans: t }), explTitle: 'Reached the destination', explText: `Answer = ${t}.`, pause: true }, ctx);
        return seq;
      }
      for (const [dr, dc] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const nr = r + dr, nc = c + dc;
        if (nr < 0 || nr >= n || nc < 0 || nc >= n) continue;
        const nt = Math.max(t, grid[nr][nc]);
        if (nt < cost[nr][nc]) {
          cost[nr][nc] = nt; heap.push([nt, nr, nc]);
          domPushState(seq, { line: 10, color: 'emerald', ...snapS({ r, c, nr, nc }),
            explTitle: `Relax (${nr},${nc})`, explText: `max(${t}, ${grid[nr][nc]}) = ${nt} improves cost[${nr}][${nc}].` }, ctx);
        }
      }
    }
    return seq;
  },
  renderDOM(container, s, spec) {
    const grid = ggGridHTML(s.grid, (v, r, c) => {
      const isCur = r === s.r && c === s.c, isNb = r === s.nr && c === s.nc;
      return { content: `${v}<br><span style="font-size:9px;opacity:.7;">${s.cost[r][c]}</span>`,
        bg: isCur ? 'rgba(56,189,248,.25)' : isNb ? 'rgba(52,211,153,.2)' : 'var(--surface)',
        border: isCur ? 'var(--accent)' : isNb ? 'var(--emerald)' : 'var(--border)', fontSize: 12 };
    }, { cell: 52 });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel('Grid (elevation, cost-so-far)', grid)}
        ${ggPanel('Heap (time, r, c)', agChips(s.heap.map(h => agChip('', `(${h[0]},${h[1]},${h[2]})`)).join('') || '<span style="color:var(--text-dim);">empty</span>')) }
        ${s.done ? ggPanel('Answer', `<div style="font-size:18px;font-weight:700;color:var(--emerald);">${s.ans}</div>`) : ''}
      </div>`;
  }
});

/* ============================================================ 009 · Alien Dictionary */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Alien Dictionary', short: 'Alien Dictionary',
  idea: 'Compare each pair of adjacent words to find their first differing letter — that gives one precedence edge. Then Kahn’s BFS topological sort over the derived letter graph gives a valid order.',
  complexity: 'Time O(C + V + E) · Space O(26)',
  input: 'wrt, wrf, er, ett, rftt', hint: 'comma-separated words, already sorted per alien rules',
  code: [
    'def alienOrder(words):',
    '    adj, indegree = build from adjacent pairs',
    '    for a, b in zip(words, words[1:]):',
    '        find first index i where a[i] != b[i]',
    '        add edge a[i] -> b[i]',
    '        if no difference and len(a) > len(b): return ""',
    '    queue = [ch for ch in letters if indegree[ch] == 0]',
    '    order = []',
    '    while queue:',
    '        ch = queue.pop(); order.append(ch)',
    '        for nxt in adj[ch]:',
    '            indegree[nxt] -= 1',
    '            if indegree[nxt] == 0: queue.append(nxt)',
    '    return "".join(order) if len(order) == len(letters) else ""',
  ],
  parse(s) {
    const words = s.split(',').map(w => w.trim().toLowerCase()).filter(Boolean);
    if (words.length < 2) throw new Error('Enter at least 2 words');
    if (words.length > 8) throw new Error('Use at most 8 words for visualization');
    words.forEach(w => { if (!/^[a-z]{1,8}$/.test(w)) throw new Error(`"${w}" — letters only, up to 8 per word`); });
    return { words };
  },
  buildStates({ words }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const letters = [...new Set(words.join(''))].sort();
    const idOf = {}; letters.forEach((l, i) => idOf[l] = i);
    const adj = letters.map(() => new Set());
    const indegree = letters.map(() => 0);
    const snapS = extra => ({ letters, edges: adj.map((s2, i) => [...s2].map(j => [i, j])).flat(), indegree: [...indegree], ...extra });

    domPushState(seq, { line: 2, color: 'default', ...snapS({ a: -1, b: -1 }),
      explTitle: 'Letters found', explText: `Alphabet in play: ${letters.join(', ')}.` }, ctx);

    for (let w = 0; w < words.length - 1; w++) {
      const a = words[w], b = words[w + 1];
      const minLen = Math.min(a.length, b.length);
      let found = false;
      for (let i = 0; i < minLen; i++) {
        if (a[i] !== b[i]) {
          found = true;
          const u = idOf[a[i]], v = idOf[b[i]];
          if (!adj[u].has(v)) { adj[u].add(v); indegree[v]++; }
          domPushState(seq, { line: 4, color: 'blue', ...snapS({ a: u, b: v }),
            explTitle: `"${a}" vs "${b}"`, explText: `First difference at position ${i}: "${a[i]}" before "${b[i]}" → edge ${a[i]}→${b[i]}.` }, ctx);
          break;
        }
      }
      if (!found && a.length > b.length) {
        domPushState(seq, { line: 5, color: 'rose', ...snapS({ a: -1, b: -1, result: '' }),
          explTitle: 'Invalid order', explText: `"${a}" is a longer word that comes before its own prefix "${b}" — no valid ordering exists.`, pause: true }, ctx);
        return seq;
      }
    }

    let queue = letters.map((_, i) => i).filter(i => indegree[i] === 0);
    const order = [];
    domPushState(seq, { line: 6, color: 'blue', ...snapS({ a: -1, b: -1, queue: [...queue], order: [...order] }),
      explTitle: 'Start Kahn’s BFS', explText: `Letters with indegree 0: ${queue.map(i => letters[i]).join(', ') || '(none)'}.` }, ctx);
    while (queue.length) {
      const ch = queue.shift();
      order.push(ch);
      domPushState(seq, { line: 10, color: 'emerald', ...snapS({ a: ch, b: -1, queue: [...queue], order: [...order] }),
        explTitle: `Emit "${letters[ch]}"`, explText: `"${letters[ch]}" has no unresolved predecessors — it’s next in the order.` }, ctx);
      for (const nxt of adj[ch]) {
        indegree[nxt]--;
        if (indegree[nxt] === 0) { queue.push(nxt); }
      }
    }
    const ok = order.length === letters.length;
    domPushState(seq, { line: 13, color: ok ? 'emerald' : 'rose', ...snapS({ a: -1, b: -1, order: [...order], result: ok ? order.map(i => letters[i]).join('') : '' }),
      explTitle: 'Complete', explText: ok ? `Order: "${order.map(i => letters[i]).join('')}".` : 'Not every letter reached indegree 0 — there’s a cycle, so no valid order exists.', pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const n = s.letters.length;
    const graph = ggGraphSVG(n, s.edges,
      i => ({ label: s.letters[i], fill: i === s.a ? 'rgba(56,189,248,.3)' : (s.order || []).includes(i) ? 'rgba(52,211,153,.2)' : null, stroke: i === s.a ? 'var(--accent)' : i === s.b ? 'var(--emerald)' : null }),
      ([u, v]) => ({ stroke: u === s.a && v === s.b ? 'var(--accent)' : 'var(--border)', width: u === s.a && v === s.b ? 3.5 : 2 }));
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel('Precedence graph', graph)}
        ${ggPanel('indegree[]', agChips(s.indegree.map((d, i) => agChip(s.letters[i], d, d === 0)).join('')))}
        ${s.order ? ggPanel('Emitted order', agChips(s.order.map(i => agChip('', s.letters[i], true)).join('') || '<span style="color:var(--text-dim);">(none yet)</span>')) : ''}
        ${s.result !== undefined ? ggPanel('Result', `<div style="font-size:18px;font-weight:700;font-family:var(--mono);color:${s.result ? 'var(--emerald)' : 'var(--rose)'};">"${s.result}"</div>`) : ''}
      </div>`;
  }
});

/* ============================================================ 010 · Reconstruct Itinerary */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Reconstruct Itinerary', short: 'Reconstruct Itinerary',
  idea: 'Hierholzer’s algorithm. Walk greedily to the lexicographically smallest unused destination; when you get stuck, pop back onto the route — a dead end is not a mistake, it’s the last stop of a sub-loop.',
  complexity: 'Time O(E log E) · Space O(E)',
  input: 'JFK-MUC, MUC-LHR, LHR-SFO, SFO-SJC', hint: 'comma-separated tickets as SRC-DST (3-letter codes)',
  code: [
    'def findItinerary(tickets):',
    '    graph = defaultdict(min-heap)',
    '    for src, dst in tickets: push(graph[src], dst)',
    '    stack = ["JFK"]; route = []',
    '    while stack:',
    '        while graph[stack[-1]]:',
    '            stack.append(heappop(graph[stack[-1]]))',
    '        route.append(stack.pop())',
    '    return reversed(route)',
  ],
  parse(s) {
    const tickets = s.split(',').map(t => t.trim()).filter(Boolean).map(t => t.split('-'));
    if (!tickets.length) throw new Error('Enter at least one ticket, e.g. JFK-MUC');
    if (tickets.length > 8) throw new Error('Use at most 8 tickets for visualization');
    tickets.forEach(t => { if (t.length !== 2 || !/^[A-Z]{3}$/.test(t[0]) || !/^[A-Z]{3}$/.test(t[1])) throw new Error('Each ticket must be SRC-DST with 3 uppercase letters'); });
    if (!tickets.some(t => t[0] === 'JFK')) throw new Error('At least one ticket must depart from JFK');
    return { tickets };
  },
  buildStates({ tickets }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const graph = {};
    tickets.forEach(([u, v]) => { (graph[u] ??= []).push(v); });
    Object.values(graph).forEach(list => list.sort());
    const stack = ['JFK'], route = [];
    const snapS = extra => ({ graph: JSON.parse(JSON.stringify(graph)), stack: [...stack], route: [...route], ...extra });
    domPushState(seq, { line: 3, color: 'default', ...snapS({ cur: 'JFK' }),
      explTitle: 'Initialization', explText: 'Each city’s destinations are kept in sorted order. Start the stack at JFK.' }, ctx);
    let guard = 0;
    while (stack.length && guard++ < 200) {
      const top = stack[stack.length - 1];
      if (graph[top] && graph[top].length) {
        const nxt = graph[top].shift();
        stack.push(nxt);
        domPushState(seq, { line: 6, color: 'blue', ...snapS({ cur: nxt }),
          explTitle: `Fly ${top} → ${nxt}`, explText: `Take the smallest unused destination from ${top}. Push ${nxt} onto the stack.` }, ctx);
      } else {
        const city = stack.pop();
        route.push(city);
        domPushState(seq, { line: 8, color: 'emerald', ...snapS({ cur: city }),
          explTitle: `Dead end at ${city}`, explText: `${city} has no unused outgoing tickets left. Commit it to the route (we’ll reverse at the end) and back up.` }, ctx);
      }
    }
    const final = [...route].reverse();
    domPushState(seq, { line: 9, color: 'emerald', ...snapS({ cur: -1, final }),
      explTitle: 'Complete', explText: `Reverse the committed order: ${final.join(' → ')}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const graphHTML = ggPanel('Remaining destinations (sorted)', Object.keys(s.graph).sort().map(city =>
      `<div style="font-family:var(--mono);font-size:13px;margin-bottom:4px;${city === s.cur ? 'color:var(--accent);font-weight:700;' : 'color:var(--text-dim);'}">${city}: [${s.graph[city].join(', ') || '—'}]</div>`).join(''));
    const stackHTML = ggPanel('Stack (bottom → top)', agChips(s.stack.map((c, i) => agChip('', c, i === s.stack.length - 1)).join('')));
    const routeHTML = ggPanel('Committed (will be reversed)', agChips(s.route.map(c => agChip('', c)).join('') || '<span style="color:var(--text-dim);">(none yet)</span>'));
    const finalHTML = s.final ? ggPanel('Final itinerary', `<div style="font-family:var(--mono);font-weight:700;color:var(--emerald);">${s.final.join(' → ')}</div>`) : '';
    container.innerHTML = `<div style="display:flex; flex-direction:column; gap:15px; width:100%;">${graphHTML}${stackHTML}${routeHTML}${finalHTML}</div>`;
  }
});

/* ============================================================ 011 · Find Critical and Pseudo-Critical Edges in MST */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Find Critical and Pseudo-Critical Edges in Minimum Spanning Tree', short: 'Critical MST Edges',
  idea: 'Compute the baseline MST weight with Kruskal’s. Then for every edge, rebuild the MST once excluding it and once forcing it in — an edge is critical if excluding it makes the MST worse (or impossible), and pseudo-critical if forcing it in still matches the baseline.',
  complexity: 'Time O(E² · α(V)) · Space O(V+E)',
  input: '5; 0,1,1; 1,2,1; 2,3,2; 0,3,2; 0,4,3; 3,4,3', hint: 'n; u,v,w; u,v,w; ...',
  code: [
    'def findCriticalAndPseudoCriticalEdges(n, edges):',
    '    order = edges sorted by weight',
    '    def mst_weight(exclude=None, include=None):',
    '        uf = UnionFind(n); total = 0',
    '        if include: union it first, total += its weight',
    '        for i in order:',
    '            if i in (exclude, include): continue',
    '            if uf.union(edges[i]): total += edges[i].w',
    '        return total if one component else inf',
    '    base = mst_weight()',
    '    for i in range(len(edges)):',
    '        if mst_weight(exclude=i) > base: critical.append(i)',
    '        elif mst_weight(include=i) == base: pseudo.append(i)',
    '    return critical, pseudo',
  ],
  parse(s) {
    const parts = s.split(';').map(x => x.trim());
    const n = parseInt(parts[0]);
    if (!n || n > 6) throw new Error('Use at most 6 nodes for visualization');
    const edges = parts.slice(1).filter(Boolean).map(e => e.split(',').map(Number));
    if (edges.length > 8) throw new Error('Use at most 8 edges for visualization');
    edges.forEach(e => { if (e.length !== 3 || e.some(Number.isNaN)) throw new Error('Edges must be u,v,w'); });
    return { n, edges };
  },
  buildStates({ n, edges }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const m = edges.length;
    const order = edges.map((_, i) => i).sort((a, b) => edges[a][2] - edges[b][2]);
    function mstWeight(exclude, include) {
      const parent = Array.from({ length: n }, (_, i) => i);
      const find = x => { while (parent[x] !== x) x = parent[x]; return x; };
      let total = 0, comps = n;
      if (include != null) { const [a, b, w] = edges[include]; const ra = find(a), rb = find(b); if (ra !== rb) { parent[rb] = ra; comps--; total += w; } }
      for (const i of order) {
        if (i === exclude || i === include) continue;
        const [a, b, w] = edges[i]; const ra = find(a), rb = find(b);
        if (ra !== rb) { parent[rb] = ra; comps--; total += w; }
      }
      return comps === 1 ? total : Infinity;
    }
    const snapS = extra => ({ n, edges, ...extra });
    const base = mstWeight();
    domPushState(seq, { line: 10, color: 'default', ...snapS({ cur: -1 }),
      explTitle: 'Baseline MST', explText: `The minimum spanning tree with every edge available weighs ${base}.` }, ctx);
    const critical = [], pseudo = [];
    for (let i = 0; i < m; i++) {
      const exW = mstWeight(i, null);
      if (exW > base) {
        critical.push(i);
        domPushState(seq, { line: 12, color: 'rose', ...snapS({ cur: i, critical: [...critical], pseudo: [...pseudo] }),
          explTitle: `Edge ${i} is critical`, explText: `Excluding edge ${edges[i].slice(0, 2).join('–')} makes the MST ${exW === Infinity ? 'impossible (disconnects the graph)' : `worse (${exW} > ${base})`} — every MST needs it.` }, ctx);
        continue;
      }
      const inW = mstWeight(null, i);
      if (inW === base) {
        pseudo.push(i);
        domPushState(seq, { line: 13, color: 'blue', ...snapS({ cur: i, critical: [...critical], pseudo: [...pseudo] }),
          explTitle: `Edge ${i} is pseudo-critical`, explText: `Forcing edge ${edges[i].slice(0, 2).join('–')} into the tree still reaches weight ${base} — it can appear in *some* MST, just not every one.` }, ctx);
      } else {
        domPushState(seq, { line: 13, color: 'default', ...snapS({ cur: i, critical: [...critical], pseudo: [...pseudo] }),
          explTitle: `Edge ${i} is neither`, explText: `Removing it doesn’t hurt (${exW} = ${base}) and forcing it in doesn’t help either (${inW} > ${base}) — it never appears in any MST.` }, ctx);
      }
    }
    domPushState(seq, { line: 14, color: 'emerald', ...snapS({ cur: -1, critical, pseudo, done: true }),
      explTitle: 'Complete', explText: `Critical: [${critical.join(', ')}]. Pseudo-critical: [${pseudo.join(', ')}].`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const graph = ggGraphSVG(s.n, s.edges.map(e => [e[0], e[1]]), () => ({}),
      ([u, v]) => {
        const idx = s.edges.findIndex(e => e[0] === u && e[1] === v);
        if (idx === s.cur) return { stroke: 'var(--accent)', width: 4 };
        if ((s.critical || []).includes(idx)) return { stroke: 'var(--rose)', width: 3 };
        if ((s.pseudo || []).includes(idx)) return { stroke: 'var(--blue, #60a5fa)', width: 3 };
        return { stroke: 'var(--border)', width: 2 };
      });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel('Graph (red = critical, blue = pseudo-critical, gold ring = edge under test)', graph)}
        ${ggPanel('Edge under test', s.cur >= 0 ? `<div style="font-family:var(--mono);">edge ${s.cur}: ${s.edges[s.cur].slice(0, 2).join('–')} (w=${s.edges[s.cur][2]})</div>` : '<span style="color:var(--text-dim);">baseline MST</span>')}
        ${ggPanel('Classified so far', agChips([...(s.critical || []).map(i => agChip('critical', i)), ...(s.pseudo || []).map(i => agChip('pseudo', i))].join('') || '<span style="color:var(--text-dim);">(none yet)</span>'))}
      </div>`;
  }
});

/* ============================================================ 012 · Critical Connections in a Network */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Critical Connections in a Network', short: 'Critical Connections',
  idea: 'Tarjan’s bridge-finding: track each node’s discovery time and its "low-link" (the earliest-discovered node reachable via one back-edge). An edge parent→child is a bridge exactly when the child’s subtree can’t reach back at or above the parent’s discovery time.',
  complexity: 'Time O(V+E) · Space O(V+E)',
  input: '4; 0,1; 1,2; 2,0; 1,3', hint: 'n; u,v; u,v; ... (undirected)',
  code: [
    'def criticalConnections(n, connections):',
    '    disc = [-1]*n; low = [0]*n; timer = 0; bridges = []',
    '    def dfs(u, parent):',
    '        nonlocal timer',
    '        disc[u] = low[u] = timer; timer += 1',
    '        for v in adj[u]:',
    '            if v == parent: continue',
    '            if disc[v] == -1:',
    '                dfs(v, u)',
    '                low[u] = min(low[u], low[v])',
    '                if low[v] > disc[u]: bridges.append([u, v])',
    '            else:',
    '                low[u] = min(low[u], disc[v])',
    '    dfs(0, -1)',
    '    return bridges',
  ],
  parse(s) {
    const parts = s.split(';').map(x => x.trim());
    const n = parseInt(parts[0]);
    if (!n || n > 8) throw new Error('Use at most 8 nodes for visualization');
    const edges = parts.slice(1).filter(Boolean).map(e => e.split(',').map(Number));
    edges.forEach(e => { if (e.length !== 2 || e.some(Number.isNaN)) throw new Error('Edges must be u,v'); });
    return { n, edges };
  },
  buildStates({ n, edges }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const adj = Array.from({ length: n }, () => []);
    edges.forEach(([u, v]) => { adj[u].push(v); adj[v].push(u); });
    const disc = new Array(n).fill(-1), low = new Array(n).fill(0);
    let timer = 0; const bridges = [];
    const snapS = extra => ({ n, edges, disc: [...disc], low: [...low], bridges: bridges.map(b => [...b]), ...extra });
    domPushState(seq, { line: 2, color: 'default', ...snapS({ u: -1, v: -1 }), explTitle: 'Initialization', explText: 'Every node starts undiscovered (disc = -1).' }, ctx);
    function dfs(u, parent) {
      disc[u] = low[u] = timer++;
      domPushState(seq, { line: 4, color: 'blue', ...snapS({ u, v: -1, parent }), explTitle: `Discover node ${u}`, explText: `disc[${u}] = low[${u}] = ${disc[u]}.` }, ctx);
      for (const v of adj[u]) {
        if (v === parent) continue;
        if (disc[v] === -1) {
          domPushState(seq, { line: 8, color: 'blue', ...snapS({ u, v, parent }), explTitle: `Tree edge ${u}→${v}`, explText: `${v} is undiscovered — recurse into it.` }, ctx);
          dfs(v, u);
          low[u] = Math.min(low[u], low[v]);
          domPushState(seq, { line: 9, color: 'default', ...snapS({ u, v, parent }), explTitle: `Back from ${v}`, explText: `low[${u}] = min(low[${u}], low[${v}]) = ${low[u]}.` }, ctx);
          if (low[v] > disc[u]) {
            bridges.push([u, v]);
            domPushState(seq, { line: 10, color: 'rose', ...snapS({ u, v, parent }), explTitle: `Bridge found: ${u}–${v}`, explText: `low[${v}] (${low[v]}) > disc[${u}] (${disc[u]}) — ${v}’s subtree has no other way back, so this edge is critical.` }, ctx);
          }
        } else {
          low[u] = Math.min(low[u], disc[v]);
          domPushState(seq, { line: 12, color: 'emerald', ...snapS({ u, v, parent }), explTitle: `Back edge ${u}→${v}`, explText: `${v} is already discovered — low[${u}] = min(low[${u}], disc[${v}]) = ${low[u]}.` }, ctx);
        }
      }
    }
    for (let start = 0; start < n; start++) if (disc[start] === -1) dfs(start, -1);
    domPushState(seq, { line: 14, color: 'emerald', ...snapS({ u: -1, v: -1, done: true }), explTitle: 'Complete', explText: `Bridges found: ${bridges.map(b => b.join('–')).join(', ') || '(none)'}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const graph = ggGraphSVG(s.n, s.edges.map(e => [e[0], e[1]]),
      i => ({ label: `${i}\n${s.disc[i] === -1 ? '·' : s.disc[i]}/${s.disc[i] === -1 ? '·' : s.low[i]}`, fill: i === s.u ? 'rgba(56,189,248,.3)' : null, stroke: i === s.u ? 'var(--accent)' : i === s.v ? 'var(--emerald)' : null }),
      ([u, v]) => {
        const isBridge = s.bridges.some(b => (b[0] === u && b[1] === v) || (b[0] === v && b[1] === u));
        const isCur = (u === s.u && v === s.v) || (u === s.v && v === s.u);
        return { stroke: isBridge ? 'var(--rose)' : isCur ? 'var(--accent)' : 'var(--border)', width: isBridge ? 4 : isCur ? 3 : 2 };
      }, { size: 260 });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel('Graph (label = disc/low, red = bridge)', graph)}
        ${ggPanel('disc[] / low[]', agChips(s.disc.map((d, i) => agChip(i, `${d === -1 ? '·' : d}/${d === -1 ? '·' : s.low[i]}`, i === s.u)).join('')))}
        ${ggPanel('Bridges found', agChips(s.bridges.map(b => agChip('', b.join('–'), true)).join('') || '<span style="color:var(--text-dim);">(none yet)</span>'))}
      </div>`;
  }
});

/* ============================================================ 013 · Accounts Merge */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Accounts Merge', short: 'Accounts Merge',
  idea: 'Union-Find over emails, not accounts. For every account, union its first email with each of its other emails — two accounts that share even one email end up in the same set and get merged.',
  complexity: 'Time O(N·α(N) log N) · Space O(N)',
  input: 'John:jw@m.com,jw2@m.com ; John:jw2@m.com,jw3@m.com ; Mary:m@m.com', hint: 'accounts as Name:email,email ; separated by ";"',
  code: [
    'def accountsMerge(accounts):',
    '    parent, owner = {}, {}',
    '    def find(x): ... path compression ...',
    '    for name, *emails in accounts:',
    '        first = emails[0]',
    '        for email in emails:',
    '            parent.setdefault(email, email)',
    '            owner[email] = name',
    '            ra, rb = find(first), find(email)',
    '            if ra != rb: parent[rb] = ra',
    '    group emails by find(email); prepend owner name; sort',
  ],
  parse(s) {
    const accounts = s.split(';').map(a => a.trim()).filter(Boolean).map(a => {
      const [name, rest] = a.split(':');
      if (!name || !rest) throw new Error('Each account must be Name:email,email,...');
      return [name.trim(), ...rest.split(',').map(e => e.trim())];
    });
    if (accounts.length > 6) throw new Error('Use at most 6 accounts for visualization');
    return { accounts };
  },
  buildStates({ accounts }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const parent = {}, owner = {};
    const find = x => { while (parent[x] !== x) x = parent[x]; return x; };
    const snapS = extra => ({ accounts, parent: { ...parent }, owner: { ...owner }, ...extra });
    domPushState(seq, { line: 2, color: 'default', ...snapS({ ai: -1, email: null }), explTitle: 'Initialization', explText: 'Every email will become its own parent the first time it’s seen.' }, ctx);
    accounts.forEach(([name, ...emails], ai) => {
      const first = emails[0];
      domPushState(seq, { line: 4, color: 'blue', ...snapS({ ai, email: null }), explTitle: `Account: ${name}`, explText: `First email is ${first} — every other email in this account will union with it.` }, ctx);
      emails.forEach(email => {
        if (!(email in parent)) parent[email] = email;
        owner[email] = name;
        const ra = find(first), rb = find(email);
        if (ra !== rb) parent[rb] = ra;
        domPushState(seq, { line: 9, color: 'emerald', ...snapS({ ai, email }), explTitle: `Union ${first} ↔ ${email}`, explText: ra === rb ? `${email} was already in the same set as ${first}.` : `Merge the set containing ${email} into the set containing ${first}.` }, ctx);
      });
    });
    const groups = {};
    Object.keys(parent).forEach(email => { const r = find(email); (groups[r] ??= []).push(email); });
    const result = Object.entries(groups).map(([root, emails]) => [owner[root] || owner[emails[0]], ...emails.sort()]);
    domPushState(seq, { line: 10, color: 'emerald', ...snapS({ ai: -1, email: null, result }), explTitle: 'Complete', explText: `${result.length} merged account${result.length === 1 ? '' : 's'} — every set of emails that shares a union is one person.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const groupsHTML = ggPanel('Accounts (this session)', s.accounts.map(([name, ...emails], ai) =>
      `<div style="margin-bottom:6px;${ai === s.ai ? 'color:var(--accent);font-weight:700;' : 'color:var(--text-dim);'}"><b>${name}</b>: ${emails.map(e => `<span style="${e === s.email ? 'color:var(--emerald);font-weight:700;' : ''}">${e}</span>`).join(', ')}</div>`).join(''));
    const parentHTML = ggPanel('parent[] (email → root, path not yet compressed)', Object.keys(s.parent).length
      ? agChips(Object.entries(s.parent).map(([e, p]) => agChip(e, p, e === s.email)).join(''))
      : '<span style="color:var(--text-dim);">(none yet)</span>');
    const resultHTML = s.result ? ggPanel('Merged accounts', s.result.map(([name, ...emails]) => `<div style="margin-bottom:6px;"><b style="color:var(--emerald);">${name}</b>: ${emails.join(', ')}</div>`).join('')) : '';
    container.innerHTML = `<div style="display:flex; flex-direction:column; gap:15px; width:100%;">${groupsHTML}${parentHTML}${resultHTML}</div>`;
  }
});

/* ============================================================ 014 · Evaluate Division */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Evaluate Division', short: 'Evaluate Division',
  idea: 'Build a weighted graph from a/b = v (edge a→b weight v, and b→a weight 1/v). Answering c/d is then a DFS from c to d, multiplying edge weights along the path.',
  complexity: 'Time O(Q·(V+E)) · Space O(V+E)',
  input: 'a,b,2 ; b,c,3 ; a,c', hint: 'equations a,b,value ; ... ; then one query c,d',
  code: [
    'def calcEquation(equations, values, queries):',
    '    graph[a].append((b, v)); graph[b].append((a, 1/v))',
    '    def query(c, d):',
    '        if c not in graph or d not in graph: return -1',
    '        stack = [(c, 1.0)]; seen = {c}',
    '        while stack:',
    '            node, acc = stack.pop()',
    '            if node == d: return acc',
    '            for nxt, w in graph[node]:',
    '                if nxt not in seen:',
    '                    seen.add(nxt); stack.append((nxt, acc*w))',
    '        return -1',
  ],
  parse(s) {
    const parts = s.split(';').map(x => x.trim()).filter(Boolean);
    if (parts.length < 2) throw new Error('Format: a,b,value ; a,b,value ; ... ; query_c,query_d (last part)');
    const query = parts[parts.length - 1].split(',').map(x => x.trim());
    if (query.length !== 2) throw new Error('The last part must be the query: c,d');
    const equations = parts.slice(0, -1).map(p => {
      const [a, b, v] = p.split(',').map(x => x.trim());
      const val = Number(v);
      if (!a || !b || Number.isNaN(val) || val <= 0) throw new Error(`"${p}" should look like a,b,2 (positive value)`);
      return [a, b, val];
    });
    if (!equations.length) throw new Error('Enter at least one equation');
    if (equations.length > 6) throw new Error('Use at most 6 equations for visualization');
    return { equations, query };
  },
  buildStates({ equations, query }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const graph = {};
    equations.forEach(([a, b, v]) => { (graph[a] ??= []).push([b, v]); (graph[b] ??= []).push([a, 1 / v]); });
    const vars = Object.keys(graph);
    const snapS = extra => ({ vars, graph, equations, ...extra });
    domPushState(seq, { line: 2, color: 'default', ...snapS({ cur: null, stack: [] }), explTitle: 'Build the weighted graph', explText: `Each equation a/b=v becomes two directed edges: a→b (weight ${equations[0][2]}) and b→a (weight 1/${equations[0][2]}).` }, ctx);
    const [c, d] = query;
    if (!(c in graph) || !(d in graph)) {
      domPushState(seq, { line: 4, color: 'rose', ...snapS({ cur: null, stack: [], result: -1 }), explTitle: 'Unknown variable', explText: `"${!(c in graph) ? c : d}" never appears in any equation — answer is -1.0.`, pause: true }, ctx);
      return seq;
    }
    const stack = [[c, 1.0]], seen = new Set([c]);
    domPushState(seq, { line: 5, color: 'blue', ...snapS({ cur: c, stack: stack.map(x => [...x]) }), explTitle: `Query ${c} / ${d}`, explText: `Start a DFS from ${c} with an accumulated product of 1.0.` }, ctx);
    while (stack.length) {
      const [node, acc] = stack.pop();
      if (node === d) {
        domPushState(seq, { line: 8, color: 'emerald', ...snapS({ cur: node, stack: stack.map(x => [...x]), result: acc }), explTitle: 'Reached the target', explText: `${c} / ${d} = ${acc}.`, pause: true }, ctx);
        return seq;
      }
      domPushState(seq, { line: 7, color: 'blue', ...snapS({ cur: node, stack: stack.map(x => [...x]) }), explTitle: `Visit ${node}`, explText: `Accumulated product so far: ${acc.toFixed(4)}.` }, ctx);
      for (const [nxt, w] of graph[node] || []) {
        if (!seen.has(nxt)) {
          seen.add(nxt); stack.push([nxt, acc * w]);
          domPushState(seq, { line: 11, color: 'default', ...snapS({ cur: node, stack: stack.map(x => [...x]) }), explTitle: `Queue ${nxt}`, explText: `${node} → ${nxt} (weight ${w.toFixed(4)}), accumulated product would become ${(acc * w).toFixed(4)}.` }, ctx);
        }
      }
    }
    domPushState(seq, { line: 12, color: 'rose', ...snapS({ cur: null, stack: [], result: -1 }), explTitle: 'No path found', explText: `${d} is not reachable from ${c} — answer is -1.0.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const n = s.vars.length;
    const idOf = {}; s.vars.forEach((v, i) => idOf[v] = i);
    const edges = s.equations.map(([a, b, v]) => [idOf[a], idOf[b], v]);
    const graph = ggGraphSVG(n, edges.map(e => [e[0], e[1]]),
      i => ({ label: s.vars[i], fill: s.vars[i] === s.cur ? 'rgba(56,189,248,.3)' : null, stroke: s.vars[i] === s.cur ? 'var(--accent)' : null }),
      ([u, v]) => { const w = edges.find(e => e[0] === u && e[1] === v)?.[2]; return { stroke: 'var(--border)', width: 2 }; });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel('Weighted graph', graph)}
        ${ggPanel('DFS stack (node, accumulated product)', agChips(s.stack.map(([node, acc]) => agChip(node, acc.toFixed(3))).join('') || '<span style="color:var(--text-dim);">empty</span>'))}
        ${s.result !== undefined ? ggPanel('Answer', `<div style="font-size:18px;font-weight:700;color:${s.result === -1 ? 'var(--rose)' : 'var(--emerald)'};">${s.result === -1 ? '-1.0' : s.result.toFixed(5)}</div>`) : ''}
      </div>`;
  }
});

/* ============================================================ 015 · Minimum Cost to Make at Least One Valid Path in a Grid */
defineAlgoDom('15_advanced_graphs', {
  type: 'dom',
  title: 'Minimum Cost to Make at Least One Valid Path in a Grid', short: '0-1 BFS Grid Path',
  idea: '0-1 BFS with a deque. Following the arrow already on a cell costs 0 (push to the FRONT of the deque, process immediately); going any other direction costs 1 (push to the BACK). This keeps the deque sorted by distance without a heap.',
  complexity: 'Time O(R·C) · Space O(R·C)',
  input: '1,1,1,1; 2,2,2,2; 1,1,1,1; 2,2,2,2; 1,1,1,1', hint: 'grid rows of signs 1=right 2=left 3=down 4=up; rows separated by ";", cells by ","',
  code: [
    'DIRS = [(0,1), (0,-1), (1,0), (-1,0)]  # signs 1,2,3,4',
    'def minCost(grid):',
    '    dist = [[inf]*n for _ in range(m)]; dist[0][0] = 0',
    '    dq = deque([(0, 0)])',
    '    while dq:',
    '        i, j = dq.popleft()',
    '        for s, (di, dj) in enumerate(DIRS, 1):',
    '            ni, nj = i+di, j+dj',
    '            cost = 0 if grid[i][j] == s else 1',
    '            if dist[i][j]+cost < dist[ni][nj]:',
    '                dist[ni][nj] = dist[i][j] + cost',
    '                dq.appendleft((ni,nj)) if cost==0 else dq.append((ni,nj))',
    '    return dist[m-1][n-1]',
  ],
  parse(s) {
    const grid = agParseIntGrid(s, { max: 6 });
    grid.forEach(row => row.forEach(v => { if (v < 1 || v > 4) throw new Error('Signs must be 1 (right), 2 (left), 3 (down) or 4 (up)'); }));
    return { grid };
  },
  buildStates({ grid }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const DIRS = [[0, 1], [0, -1], [1, 0], [-1, 0]];
    const m = grid.length, n = grid[0].length;
    const INF = Infinity;
    const dist = Array.from({ length: m }, () => new Array(n).fill(INF));
    dist[0][0] = 0;
    let dq = [[0, 0]];
    const snapS = extra => ({ grid, dist: dist.map(r => r.map(v => v === INF ? '∞' : v)), dq: [...dq], ...extra });
    domPushState(seq, { line: 3, color: 'default', ...snapS({ i: -1, j: -1 }), explTitle: 'Initialization', explText: 'dist[0][0] = 0. Push it onto the deque.' }, ctx);
    let guard = 0;
    while (dq.length && guard++ < 400) {
      const [i, j] = dq.shift();
      domPushState(seq, { line: 6, color: 'blue', ...snapS({ i, j }), explTitle: `Pop front (${i},${j})`, explText: `0-1 BFS always finalizes the front of the deque next — it holds the smallest known distance.` }, ctx);
      for (let sgn = 1; sgn <= 4; sgn++) {
        const [di, dj] = DIRS[sgn - 1];
        const ni = i + di, nj = j + dj;
        if (ni < 0 || ni >= m || nj < 0 || nj >= n) continue;
        const cost = grid[i][j] === sgn ? 0 : 1;
        if (dist[i][j] + cost < dist[ni][nj]) {
          dist[ni][nj] = dist[i][j] + cost;
          if (cost === 0) dq.unshift([ni, nj]); else dq.push([ni, nj]);
          domPushState(seq, { line: 10, color: cost === 0 ? 'emerald' : 'default', ...snapS({ i, j, ni, nj }),
            explTitle: `Relax (${ni},${nj})`, explText: cost === 0 ? `The arrow at (${i},${j}) already points this way — free move, pushed to the FRONT of the deque.` : `Against the arrow — costs 1, pushed to the BACK of the deque.` }, ctx);
        }
      }
    }
    const ans = dist[m - 1][n - 1];
    domPushState(seq, { line: 12, color: 'emerald', ...snapS({ i: m - 1, j: n - 1, done: true, ans: ans === INF ? '∞' : ans }), explTitle: 'Complete', explText: `dist[${m - 1}][${n - 1}] = ${ans === INF ? '∞' : ans}.`, pause: true }, ctx);
    return seq;
  },
  renderDOM(container, s, spec) {
    const ARROW = { 1: '→', 2: '←', 3: '↓', 4: '↑' };
    const grid = ggGridHTML(s.grid, (v, r, c) => {
      const isCur = r === s.i && c === s.j, isNb = r === s.ni && c === s.nj;
      return { content: `${ARROW[v]}<br><span style="font-size:9px;opacity:.7;">${s.dist[r][c]}</span>`,
        bg: isCur ? 'rgba(56,189,248,.25)' : isNb ? 'rgba(52,211,153,.2)' : 'var(--surface)',
        border: isCur ? 'var(--accent)' : isNb ? 'var(--emerald)' : 'var(--border)', fontSize: 15 };
    }, { cell: 48 });
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
        ${ggPanel('Grid (arrow = required direction, number = dist-so-far)', grid)}
        ${ggPanel('Deque front → back', agChips(s.dq.map((c, i) => agChip('', `(${c[0]},${c[1]})`, i === 0)).join('') || '<span style="color:var(--text-dim);">empty</span>'))}
        ${s.done ? ggPanel('Answer', `<div style="font-size:18px;font-weight:700;color:var(--emerald);">${s.ans}</div>`) : ''}
      </div>`;
  }
});

