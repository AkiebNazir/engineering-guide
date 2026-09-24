/* ============================================================================
   DSA visualizers, part 2 — topics 13 to 20.
   Engine, helpers and topics 01-12 live in dsa-viz.js.
   ========================================================================= */
'use strict';

/* ------------------------------------------------------- shared helpers -- */
/* a grid of cells: rows of numbers, drawn as squares with an optional label */
function avParseGrid(s, { max = 8, chars = '01' } = {}) {
  const rows = String(s || '').trim().split(/[;\n]/).map(r => r.replace(/[\s,]/g, '')).filter(Boolean);
  if (!rows.length) throw new Error('Enter a grid, one row per “;”');
  if (rows.length > max) throw new Error(`Use at most ${max} rows`);
  const w = rows[0].length;
  if (!w || w > max) throw new Error(`Rows must have 1 to ${max} cells`);
  return rows.map(r => {
    if (r.length !== w) throw new Error('Every row needs the same number of cells');
    return [...r].map(ch => {
      if (!chars.includes(ch)) throw new Error(`“${ch}” is not one of ${[...chars].join('/')}`);
      return +ch;
    });
  });
}
function avDrawGrid(ctx, P, c, grid, style, { top = 26, max = 52, gap = 4, left } = {}) {
  const rows = grid.length, cols = grid[0].length;
  const cell = Math.min(max, (c.w - 40 - (cols - 1) * gap) / cols, (c.h - top - 40 - (rows - 1) * gap) / rows);
  const total = cols * cell + (cols - 1) * gap, x0 = left ?? (c.w - total) / 2;
  const X = j => x0 + j * (cell + gap), Y = i => top + i * (cell + gap);
  for (let i = 0; i < rows; i++) for (let j = 0; j < cols; j++) {
    const st = style(i, j, grid[i][j]) || {};
    ctx.fillStyle = st.fill || P.surface2;
    D.rrect(ctx, X(j), Y(i), cell, cell, Math.min(8, cell / 5)); ctx.fill();
    ctx.strokeStyle = st.stroke || P.strong; ctx.lineWidth = st.stroke ? 2.4 : 1;
    ctx.stroke();
    const label = st.label ?? grid[i][j];
    if (label !== '') D.text(ctx, String(label), X(j) + cell / 2, Y(i) + cell / 2, { color: st.color || P.text, size: Math.max(10, cell * .34), align: 'center', weight: 650, mono: true });
  }
  return { x: j => X(j) + cell / 2, y: i => Y(i) + cell / 2, cell, left: x0, top, bottom: Y(rows - 1) + cell };
}
/* label -> index graph from "A-B:4, B-C:1" */
function avParseGraph(s, { max = 8, weighted = true } = {}) {
  const ids = [], idx = {}, edges = [];
  const id = ch => (idx[ch] ??= (ids.push(ch), ids.length - 1));
  String(s || '').split(/[,\n]/).map(x => x.trim()).filter(Boolean).forEach(tok => {
    const m = tok.match(/^([A-Za-z]\w*)\s*[-–>]\s*([A-Za-z]\w*)(?:\s*[:=]\s*(-?\d+))?$/);
    if (!m) throw new Error(`“${tok}” should look like A-B${weighted ? ':4' : ''}`);
    const w = m[3] === undefined ? 1 : +m[3];
    if (weighted && (w <= 0 || w > 99)) throw new Error('Edge weights must be between 1 and 99');
    edges.push({ a: id(m[1].toUpperCase()), b: id(m[2].toUpperCase()), w });
  });
  if (!edges.length) throw new Error('Enter at least one edge');
  if (ids.length > max) throw new Error(`Use at most ${max} nodes so the picture stays readable`);
  return { ids, edges };
}
/* nodes on a circle — readable for up to ~8 vertices */
function avCircle(c, n, { cy, r } = {}) {
  const R = r ?? Math.min(c.w / 2 - 60, (c.h - 120) / 2);
  const CY = cy ?? 30 + R + 10;
  return i => [c.w / 2 + R * Math.cos(-Math.PI / 2 + TAU * i / n), CY + R * Math.sin(-Math.PI / 2 + TAU * i / n)];
}

/* ===================================================================== 13 · trie == */
defineAlgo('13_trie', {
  title: 'Trie: insert words, then search a prefix', short: 'Trie',
  idea: 'Each edge is one character, so a word is a root-to-node path and shared prefixes are stored once. Lookup cost depends on the <b>length of the word</b>, not on how many words the trie holds — that is what a hash map cannot do.',
  complexity: 'insert / search / startsWith O(L) · space O(total characters), shared prefixes stored once',
  input: 'car, cart, care, dog, do ; car', hint: 'words ; prefix to look up',
  code: [
    'class Trie:',
    '    def __init__(self):',
    '        self.kids, self.end = {}, False',
    '',
    '    def insert(self, word):',
    '        node = self',
    '        for ch in word:',
    '            if ch not in node.kids:',
    '                node.kids[ch] = Trie()      # new branch',
    '            node = node.kids[ch]',
    '        node.end = True                     # word ends here',
    '',
    '    def starts_with(self, prefix):',
    '        node = self',
    '        for ch in prefix:',
    '            if ch not in node.kids:',
    '                return False',
    '            node = node.kids[ch]',
    '        return True',
  ],
  parse(s) {
    const [a, q] = avParts(s);
    const words = String(a || '').split(/[\s,]+/).filter(Boolean).map(w => w.toLowerCase());
    if (!words.length) throw new Error('Enter at least one word');
    if (words.length > 6) throw new Error('Use at most 6 words');
    words.forEach(w => { if (!/^[a-z]{1,7}$/.test(w)) throw new Error(`“${w}” — use letters only, up to 7 per word`); });
    const prefix = String(q || '').trim().toLowerCase();
    if (!/^[a-z]{1,7}$/.test(prefix)) throw new Error('Add a prefix (letters only) after the “;”');
    return { words, prefix };
  },
  run({ words, prefix }) {
    const { F, snap } = avRecorder();
    const nodes = [{ ch: '', kids: {}, end: false }];
    const S = (extra = {}) => ({ nodes: nodes.map(n => ({ ...n, kids: { ...n.kids } })), ...extra });
    snap(1, 'Start with one empty root node.', S({ cur: 0, vars: { nodes: 1 } }));
    words.forEach(word => {
      let node = 0; const path = [0];
      snap(5, `Insert <b>${word}</b> — walk from the root.`, S({ cur: 0, path: [...path], word, vars: { word } }));
      [...word].forEach((ch, k) => {
        const has = nodes[node].kids[ch] !== undefined;
        snap(7, has ? `<code>${ch}</code> already branches off here — reuse it.` : `No <code>${ch}</code> branch yet.`, S({ cur: node, path: [...path], word, at: k, reuse: has, vars: { word, ch } }));
        if (!has) {
          nodes.push({ ch, kids: {}, end: false });
          nodes[node].kids[ch] = nodes.length - 1;
          snap(8, `Create a node for <code>${ch}</code>.`, S({ cur: nodes.length - 1, path: [...path, nodes.length - 1], word, at: k, fresh: nodes.length - 1, vars: { word, ch, nodes: nodes.length } }));
        }
        node = nodes[node].kids[ch];
        path.push(node);
      });
      nodes[node].end = true;
      snap(10, `Mark the last node as the end of <b>${word}</b>.`, S({ cur: node, path: [...path], word, done: true, vars: { word, nodes: nodes.length } }));
    });
    let node = 0; const path = [0];
    snap(13, `Now look up the prefix <b>${prefix}</b>.`, S({ cur: 0, path: [...path], query: prefix, vars: { prefix } }));
    for (let k = 0; k < prefix.length; k++) {
      const ch = prefix[k], nxt = nodes[node].kids[ch];
      if (nxt === undefined) {
        snap(16, `No <code>${ch}</code> branch from here: nothing in the trie starts with <b>${prefix}</b>.`, S({ cur: node, path: [...path], query: prefix, at: k, miss: true, vars: { prefix, result: 'False' } }));
        return F;
      }
      node = nxt; path.push(node);
      snap(17, `Follow <code>${ch}</code> — ${k + 1} of ${prefix.length} characters matched.`, S({ cur: node, path: [...path], query: prefix, at: k, vars: { prefix, matched: k + 1 } }));
    }
    const under = (id => { let n = 0; const go = x => { if (nodes[x].end) n++; Object.values(nodes[x].kids).forEach(go); }; go(id); return n; })(node);
    snap(18, `Prefix found. The subtree below holds <b>${under}</b> word${under === 1 ? '' : 's'} — that subtree is exactly what autocomplete returns.`, S({ cur: node, path: [...path], query: prefix, sub: node, vars: { prefix, result: 'True', words_below: under } }));
    return F;
  },
  height: (w, last, frames) => {
    const deep = Math.max(...frames.map(f => { const d = id => 1 + Math.max(0, ...Object.values(f.nodes[id].kids).map(d)); return d(0); }));
    return 40 + deep * 58 + 40;
  },
  draw(ctx, c, f, P) {
    const nodes = f.nodes, pos = {};
    let col = 0, maxD = 0;
    const walk = (id, d) => {
      maxD = Math.max(maxD, d);
      const ks = Object.keys(nodes[id].kids).sort();
      if (!ks.length) { pos[id] = { x: col++, d }; return; }
      const xs = ks.map(k => { walk(nodes[id].kids[k], d + 1); return pos[nodes[id].kids[k]].x; });
      pos[id] = { x: (Math.min(...xs) + Math.max(...xs)) / 2, d };
    };
    walk(0, 0);
    const cols = Math.max(1, col), slot = (c.w - 56) / cols;
    const X = id => 28 + (pos[id].x + .5) * slot, Y = id => 34 + pos[id].d * 58;
    const onPath = new Set(f.path || []);
    const sub = new Set();
    if (f.sub != null) { const go = x => { sub.add(x); Object.values(nodes[x].kids).forEach(go); }; go(f.sub); }
    nodes.forEach((nd, id) => Object.entries(nd.kids).forEach(([ch, kid]) => {
      const hot = onPath.has(id) && onPath.has(kid);
      D.line(ctx, X(id), Y(id) + 16, X(kid), Y(kid) - 16, hot ? P.accent : sub.has(kid) ? P.ok : P.strong, hot ? 2.6 : 1.4);
      D.text(ctx, ch, (X(id) + X(kid)) / 2 + 9, (Y(id) + Y(kid)) / 2, { color: hot ? P.accent : P.dim, size: 12, weight: 700, mono: true });
    }));
    nodes.forEach((nd, id) => {
      const isCur = id === f.cur;
      AV.node(ctx, P, X(id), Y(id), 15, nd.ch || '·', {
        fill: id === f.fresh ? P.alpha('ok', .35) : isCur ? P.alpha('accent', .35) : sub.has(id) ? P.alpha('ok', .16) : nd.end ? P.alpha('ok', .12) : null,
        stroke: isCur ? P.accent : nd.end ? P.ok : sub.has(id) ? P.ok : null,
        ring: nd.end ? P.alpha('ok', .8) : null,
      });
    });
    if (f.miss) D.text(ctx, `dead end — “${f.query}” is not a prefix of any stored word`, c.w / 2, c.h - 16, { color: P.err, size: 12, align: 'center', weight: 650 });
    else if (f.word) D.text(ctx, `inserting “${f.word}”`, c.w / 2, c.h - 16, { color: P.dim, size: 12, align: 'center', mono: true });
    else if (f.query) D.text(ctx, `searching “${f.query}”`, c.w / 2, c.h - 16, { color: P.dim, size: 12, align: 'center', mono: true });
    D.text(ctx, '◎ = a word ends here', 20, 16, { color: P.ok, size: 11 });
  },
});

/* =================================================================== 14 · graphs == */
defineAlgo('14_graphs', {
  title: 'Number of islands: flood fill', short: 'Islands',
  idea: 'Scan the grid. Every time you meet an unvisited <code>1</code>, that is a new island — then flood the whole island so it is never counted twice. <b>DFS</b> uses a stack and dives down one arm; <b>BFS</b> uses a queue and spreads in rings. Same answer, different shape of the frontier.',
  complexity: 'Time O(rows × cols) — every cell is pushed at most once · Space O(rows × cols) worst case',
  input: '11000; 11000; 00100; 00011', hint: 'rows of 0/1, separated by “;”',
  variants: [['dfs', 'DFS (stack)'], ['bfs', 'BFS (queue)']],
  code: v => [
    'def num_islands(grid):',
    '    seen, count = set(), 0',
    '    for r, c in all_cells(grid):',
    '        if grid[r][c] == "1" and (r, c) not in seen:',
    '            count += 1                     # a new island',
    `            frontier = ${v === 'dfs' ? '[(r, c)]' : 'deque([(r, c)])'}`,
    '            while frontier:',
    `                r, c = frontier.${v === 'dfs' ? 'pop()' : 'popleft()'}`,
    '                for nr, nc in neighbours(r, c):',
    '                    if grid[nr][nc] == "1" and (nr, nc) not in seen:',
    '                        seen.add((nr, nc)); frontier.append((nr, nc))',
    '    return count',
  ],
  parse(s) { return { grid: avParseGrid(s, { max: 7 }) }; },
  run({ grid }, v) {
    const { F, snap } = avRecorder();
    const R = grid.length, C = grid[0].length;
    const seen = grid.map(row => row.map(() => 0));
    const island = grid.map(row => row.map(() => 0));
    let count = 0;
    const S = (extra = {}) => ({ grid, seen: seen.map(r => [...r]), island: island.map(r => [...r]), count, ...extra });
    snap(1, 'Nothing visited yet, zero islands.', S({ vars: { count: 0 } }));
    for (let r = 0; r < R; r++) for (let c0 = 0; c0 < C; c0++) {
      if (grid[r][c0] !== 1 || seen[r][c0]) {
        snap(3, grid[r][c0] !== 1 ? `(${r}, ${c0}) is water — skip.` : `(${r}, ${c0}) already belongs to island ${island[r][c0]}.`, S({ scan: [r, c0], vars: { r, c: c0, count } }));
        continue;
      }
      count++;
      seen[r][c0] = 1; island[r][c0] = count;
      const frontier = [[r, c0]];
      snap(4, `Unvisited land at (${r}, ${c0}): island <b>#${count}</b> starts here.`, S({ scan: [r, c0], frontier: [...frontier], vars: { r, c: c0, count } }));
      while (frontier.length) {
        const [cr, cc] = v === 'dfs' ? frontier.pop() : frontier.shift();
        snap(7, `Take (${cr}, ${cc}) off the ${v === 'dfs' ? 'top of the stack' : 'front of the queue'}.`, S({ scan: [r, c0], cur: [cr, cc], frontier: frontier.map(x => [...x]), vars: { cell: `(${cr}, ${cc})`, frontier: frontier.length, count } }));
        const nb = [[cr - 1, cc], [cr + 1, cc], [cr, cc - 1], [cr, cc + 1]].filter(([a, b]) => a >= 0 && b >= 0 && a < R && b < C);
        let added = 0;
        nb.forEach(([nr, nc]) => {
          if (grid[nr][nc] === 1 && !seen[nr][nc]) { seen[nr][nc] = 1; island[nr][nc] = count; frontier.push([nr, nc]); added++; }
        });
        snap(10, added ? `${added} new land neighbour${added === 1 ? '' : 's'} joined the frontier.` : 'No new land neighbours — this arm is finished.', S({ scan: [r, c0], cur: [cr, cc], frontier: frontier.map(x => [...x]), vars: { frontier: frontier.length, count } }));
      }
      snap(11, `Island #${count} is fully flooded; the scan continues from (${r}, ${c0}).`, S({ scan: [r, c0], vars: { count } }));
    }
    snap(11, `Every cell visited once: <b>${count}</b> island${count === 1 ? '' : 's'}.`, S({ vars: { islands: count } }));
    return F;
  },
  height: (w, last) => 60 + last.grid.length * 52 + 40,
  draw(ctx, c, f, P) {
    const inF = new Set((f.frontier || []).map(([a, b]) => `${a},${b}`));
    const hue = k => P.series[(k - 1) % P.series.length];
    const g = avDrawGrid(ctx, P, c, f.grid, (i, j, v) => {
      const cur = f.cur && f.cur[0] === i && f.cur[1] === j;
      const front = inF.has(`${i},${j}`);
      const isl = f.island[i][j];
      return {
        fill: cur ? P.alpha('accent', .45) : front ? P.alpha('accent', .18) : isl ? P.alpha(hue(isl), .3) : v === 1 ? P.surface2 : P.alpha('faint', .07),
        stroke: cur ? P.accent : front ? P.accent : isl ? hue(isl) : null,
        color: v === 1 ? P.text : P.faint,
        label: isl ? `#${isl}` : v === 1 ? '1' : '0',
      };
    }, { top: 40 });
    if (f.scan) { const [r, cc] = f.scan; D.text(ctx, '▸', g.x(cc) - g.cell / 2 - 10, g.y(r), { color: P.dim, size: 14, align: 'center' }); }
    D.text(ctx, `frontier: ${(f.frontier || []).map(([a, b]) => `(${a},${b})`).join(' ') || '—'}`, 20, g.bottom + 22, { color: P.accent, size: 12, mono: true });
    D.text(ctx, `islands so far: ${f.count}`, 20, 20, { color: P.ok, size: 13, weight: 700 });
  },
});

defineAlgo('14_graphs', {
  title: 'Rotting oranges: multi-source BFS', short: 'Rotting oranges',
  idea: 'Every rotten orange starts in the queue at once, so the BFS spreads from all of them in lockstep. One pass of the queue = one minute. Multi-source BFS is the standard answer to “how long until this reaches everything”.',
  complexity: 'Time O(rows × cols) · Space O(rows × cols) for the queue',
  input: '2110; 1101; 0110; 0011', hint: 'rows of 0 empty / 1 fresh / 2 rotten',
  code: [
    'def oranges_rotting(grid):',
    '    q = deque(all rotten cells)      # every source at once',
    '    fresh = count of 1s',
    '    minutes = 0',
    '    while q and fresh:',
    '        for _ in range(len(q)):      # exactly one minute',
    '            r, c = q.popleft()',
    '            for nr, nc in neighbours(r, c):',
    '                if grid[nr][nc] == 1:',
    '                    grid[nr][nc] = 2; fresh -= 1; q.append((nr, nc))',
    '        minutes += 1',
    '    return -1 if fresh else minutes',
  ],
  parse(s) { return { grid: avParseGrid(s, { max: 7, chars: '012' }) }; },
  run({ grid }) {
    const { F, snap } = avRecorder();
    const R = grid.length, C = grid[0].length;
    const g = grid.map(r => [...r]);
    let q = [], fresh = 0, minutes = 0;
    for (let i = 0; i < R; i++) for (let j = 0; j < C; j++) { if (g[i][j] === 2) q.push([i, j]); else if (g[i][j] === 1) fresh++; }
    const S = (extra = {}) => ({ grid: g.map(r => [...r]), q: q.map(x => [...x]), minutes, fresh, ...extra });
    snap(1, `${q.length} rotten orange${q.length === 1 ? '' : 's'} go into the queue together; ${fresh} fresh left.`, S({ vars: { sources: q.length, fresh, minute: 0 } }));
    while (q.length && fresh) {
      const layer = q;
      q = [];
      snap(5, `Minute ${minutes + 1}: process the whole layer of ${layer.length}.`, S({ layer: layer.map(x => [...x]), vars: { minute: minutes + 1, layer: layer.length, fresh } }));
      layer.forEach(([r, c0]) => {
        [[r - 1, c0], [r + 1, c0], [r, c0 - 1], [r, c0 + 1]].forEach(([nr, nc]) => {
          if (nr < 0 || nc < 0 || nr >= R || nc >= C || g[nr][nc] !== 1) return;
          g[nr][nc] = 2; fresh--; q.push([nr, nc]);
        });
      });
      minutes++;
      snap(9, `${q.length} orange${q.length === 1 ? '' : 's'} just turned rotten; ${fresh} still fresh.`, S({ fresh, vars: { minute: minutes, newly_rotten: q.length, fresh } }));
    }
    snap(11, fresh ? `${fresh} fresh orange${fresh === 1 ? '' : 's'} can never be reached — return −1.` : `All oranges rotten after <b>${minutes}</b> minute${minutes === 1 ? '' : 's'}.`, S({ done: true, vars: { result: fresh ? -1 : minutes } }));
    return F;
  },
  height: (w, last) => 60 + last.grid.length * 52 + 30,
  draw(ctx, c, f, P) {
    const inQ = new Set((f.q || []).concat(f.layer || []).map(([a, b]) => `${a},${b}`));
    const g = avDrawGrid(ctx, P, c, f.grid, (i, j, v) => ({
      fill: v === 2 ? P.alpha(inQ.has(`${i},${j}`) ? 'err' : 'faint', inQ.has(`${i},${j}`) ? .4 : .18) : v === 1 ? P.alpha('ok', .22) : P.alpha('faint', .06),
      stroke: inQ.has(`${i},${j}`) ? P.err : v === 1 ? P.ok : null,
      color: v === 0 ? P.faint : P.text,
      label: v === 2 ? '🦠' : v === 1 ? '🍊' : '·',
    }), { top: 40 });
    D.text(ctx, `minute ${f.minutes}`, 20, 20, { color: P.accent, size: 14, weight: 700 });
    D.text(ctx, `fresh left: ${f.fresh}`, 20, g.bottom + 22, { color: f.fresh ? P.ok : P.dim, size: 12.5, weight: 650 });
    if (f.done) D.text(ctx, f.fresh ? 'unreachable fresh oranges → −1' : 'every orange reached', c.w - 20, g.bottom + 22, { color: f.fresh ? P.err : P.ok, size: 12.5, align: 'right', weight: 650 });
  },
});

/* ========================================================= 15 · advanced graphs == */
defineAlgo('15_advanced_graphs', {
  title: "Dijkstra's shortest path", short: 'Dijkstra',
  idea: 'Always settle the <b>closest unsettled node</b> next. Because every edge weight is positive, once a node is popped from the min-heap no later path can beat it — that is the whole proof, and it is also why a single negative edge breaks the algorithm.',
  complexity: 'Time O((V + E) log V) with a binary heap · Space O(V)',
  input: 'A-B:4, A-C:2, B-C:5, B-D:10, C-E:3, E-D:4, D-F:11 ; A', hint: 'edges A-B:weight ; source node',
  code: [
    'def dijkstra(graph, src):',
    '    dist = {v: inf for v in graph}; dist[src] = 0',
    '    heap = [(0, src)]',
    '    while heap:',
    '        d, u = heappop(heap)          # closest unsettled node',
    '        if d > dist[u]: continue      # stale heap entry',
    '        for v, w in graph[u]:',
    '            if d + w < dist[v]:',
    '                dist[v] = d + w       # relax the edge',
    '                heappush(heap, (dist[v], v))',
    '    return dist',
  ],
  parse(s) {
    const [a, q] = avParts(s);
    const { ids, edges } = avParseGraph(a);
    const src = String(q || ids[0]).trim().toUpperCase();
    const si = ids.indexOf(src);
    if (si < 0) throw new Error(`Source “${src}” is not one of ${ids.join(', ')}`);
    return { ids, edges, src: si };
  },
  run({ ids, edges, src }) {
    const { F, snap } = avRecorder();
    const n = ids.length, adj = ids.map(() => []);
    edges.forEach(({ a, b, w }) => { adj[a].push([b, w]); adj[b].push([a, w]); });
    const dist = ids.map(() => Infinity), done = ids.map(() => false), from = ids.map(() => -1);
    dist[src] = 0;
    let heap = [[0, src]];
    const D9 = () => dist.map(d => (d === Infinity ? null : d));
    const S = (extra = {}) => ({ ids, edges, dist: D9(), done: [...done], from: [...from], heap: heap.map(x => [...x]), ...extra });
    snap(2, `Everything starts at ∞ except the source <b>${ids[src]}</b>, which is 0.`, S({ vars: { source: ids[src] } }));
    while (heap.length) {
      heap.sort((x, y) => x[0] - y[0]);
      const [d, u] = heap.shift();
      if (d > dist[u]) { snap(5, `(${d}, ${ids[u]}) is a stale entry — ${ids[u]} already has ${dist[u]}. Skip it.`, S({ cur: u, stale: true, vars: { skipped: ids[u] } })); continue; }
      done[u] = true;
      snap(4, `Pop the closest unsettled node: <b>${ids[u]}</b> at distance ${d}. It is now final.`, S({ cur: u, vars: { settled: ids[u], dist: d } }));
      for (const [v, w] of adj[u]) {
        if (done[v]) { snap(6, `${ids[v]} is already settled — nothing to relax.`, S({ cur: u, look: v, vars: { edge: `${ids[u]}→${ids[v]}` } })); continue; }
        const cand = d + w;
        const better = cand < dist[v];
        snap(7, `${ids[u]} → ${ids[v]} costs ${d} + ${w} = ${cand}, versus the current ${dist[v] === Infinity ? '∞' : dist[v]}.`, S({ cur: u, look: v, vars: { candidate: cand, current: dist[v] === Infinity ? '∞' : dist[v] } }));
        if (better) {
          dist[v] = cand; from[v] = u; heap.push([cand, v]);
          snap(8, `Better: <b>${ids[v]}</b> drops to ${cand} via ${ids[u]}.`, S({ cur: u, relax: v, vars: { [ids[v]]: cand } }));
        }
      }
    }
    snap(10, `Heap empty. Shortest distances from ${ids[src]}: ${ids.map((x, i) => `${x}=${dist[i] === Infinity ? '∞' : dist[i]}`).join(', ')}.`, S({ vars: Object.fromEntries(ids.map((x, i) => [x, dist[i] === Infinity ? '∞' : dist[i]])) }));
    return F;
  },
  height: (w, last) => Math.max(300, Math.min(360, w * .52)),
  draw(ctx, c, f, P) {
    const n = f.ids.length, at = avCircle(c, n, { cy: (c.h - 60) / 2 + 20, r: Math.min(c.w / 2 - 70, (c.h - 130) / 2) });
    const tree = new Set(f.from.map((p, i) => (p >= 0 ? `${Math.min(p, i)}-${Math.max(p, i)}` : null)).filter(Boolean));
    f.edges.forEach(({ a, b, w }) => {
      const [x1, y1] = at(a), [x2, y2] = at(b);
      const hot = (f.cur === a && f.look === b) || (f.cur === b && f.look === a);
      const inTree = tree.has(`${Math.min(a, b)}-${Math.max(a, b)}`);
      D.line(ctx, x1, y1, x2, y2, hot ? P.accent : inTree ? P.ok : P.strong, hot ? 3 : inTree ? 2.2 : 1.2);
      D.text(ctx, String(w), (x1 + x2) / 2, (y1 + y2) / 2, { color: hot ? P.accent : P.dim, size: 11.5, align: 'center', weight: 700, mono: true });
    });
    f.ids.forEach((lab, i) => {
      const [x, y] = at(i);
      AV.node(ctx, P, x, y, 20, lab, {
        fill: i === f.cur ? P.alpha('accent', .4) : f.done[i] ? P.alpha('ok', .25) : i === f.relax ? P.alpha(P.series[0], .2) : null,
        stroke: i === f.cur ? P.accent : f.done[i] ? P.ok : i === f.relax || i === f.look ? P.series[0] : null,
        sub: f.dist[i] === null ? '∞' : String(f.dist[i]),
      });
    });
    const hs = [...f.heap].sort((a, b) => a[0] - b[0]).map(([d, v]) => `(${d}, ${f.ids[v]})`);
    D.text(ctx, `min-heap: ${hs.join('  ') || 'empty'}`, 20, c.h - 34, { color: P.series[0], size: 12, mono: true });
    D.text(ctx, `settled: ${f.ids.filter((_, i) => f.done[i]).join(' ') || '—'}`, 20, c.h - 14, { color: P.ok, size: 12, mono: true, weight: 650 });
  },
});

defineAlgo('15_advanced_graphs', {
  title: "Union-find and Kruskal's MST", short: 'Union-find / MST',
  idea: 'Sort the edges by weight and take each one unless its two ends are already connected. “Already connected?” is a <b>find</b>; joining two components is a <b>union</b>. With path compression the answer is near O(1), so the sort dominates.',
  complexity: 'Time O(E log E) for the sort · union-find is O(α(V)) ≈ O(1) per operation',
  input: 'A-B:1, B-C:4, A-C:3, C-D:2, B-D:5, D-E:7, C-E:6', hint: 'edges A-B:weight',
  code: [
    'def kruskal(nodes, edges):',
    '    parent = {v: v for v in nodes}',
    '    def find(x):',
    '        while parent[x] != x:',
    '            parent[x] = parent[parent[x]]   # path compression',
    '            x = parent[x]',
    '        return x',
    '    mst, cost = [], 0',
    '    for w, u, v in sorted(edges):',
    '        ru, rv = find(u), find(v)',
    '        if ru == rv: continue               # would make a cycle',
    '        parent[ru] = rv                     # union',
    '        mst.append((u, v)); cost += w',
    '    return mst, cost',
  ],
  parse(s) { return avParseGraph(s); },
  run({ ids, edges }) {
    const { F, snap } = avRecorder();
    const parent = ids.map((_, i) => i);
    const find = x => { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; };
    const sorted = [...edges].sort((a, b) => a.w - b.w);
    const mst = [], rejected = [];
    let cost = 0;
    const S = (extra = {}) => ({ ids, edges, sorted, parent: [...parent], mst: [...mst], rejected: [...rejected], cost, ...extra });
    snap(1, 'Every node starts as its own component.', S({ vars: { components: ids.length } }));
    sorted.forEach((e, k) => {
      snap(8, `Cheapest edge left: <b>${ids[e.a]}–${ids[e.b]}</b> (${e.w}).`, S({ look: k, vars: { edge: `${ids[e.a]}-${ids[e.b]}`, weight: e.w } }));
      const ra = find(e.a), rb = find(e.b);
      snap(9, `find(${ids[e.a]}) = ${ids[ra]}, find(${ids[e.b]}) = ${ids[rb]}.`, S({ look: k, roots: [ra, rb], vars: { root_a: ids[ra], root_b: ids[rb] } }));
      if (ra === rb) {
        rejected.push(k);
        snap(10, `Same component — taking it would close a cycle. Skip.`, S({ look: k, reject: k, vars: { skipped: `${ids[e.a]}-${ids[e.b]}` } }));
        return;
      }
      parent[ra] = rb; mst.push(k); cost += e.w;
      const comps = new Set(ids.map((_, i) => find(i))).size;
      snap(11, `Different components: union them and keep the edge. Cost so far ${cost}, ${comps} component${comps === 1 ? '' : 's'} left.`, S({ take: k, vars: { cost, components: comps } }));
    });
    snap(13, `Spanning tree: ${mst.map(k => `${ids[sorted[k].a]}–${ids[sorted[k].b]}`).join(', ')} with total weight <b>${cost}</b>.`, S({ vars: { edges_kept: mst.length, total: cost } }));
    return F;
  },
  height: (w, last) => Math.max(320, Math.min(380, w * .55)),
  draw(ctx, c, f, P) {
    const n = f.ids.length, at = avCircle(c, n, { cy: (c.h - 90) / 2 + 18, r: Math.min(c.w / 2 - 70, (c.h - 170) / 2) });
    const kept = new Set(f.mst), bad = new Set(f.rejected);
    f.sorted.forEach((e, k) => {
      const [x1, y1] = at(e.a), [x2, y2] = at(e.b);
      const on = k === f.look, keep = kept.has(k), rej = bad.has(k);
      D.line(ctx, x1, y1, x2, y2, on ? P.accent : keep ? P.ok : rej ? P.alpha('err', .5) : P.strong, on ? 3.2 : keep ? 2.6 : 1.2, rej && !on ? [4, 4] : null);
      D.text(ctx, String(e.w), (x1 + x2) / 2, (y1 + y2) / 2, { color: on ? P.accent : keep ? P.ok : P.faint, size: 11.5, align: 'center', weight: 700, mono: true });
    });
    const roots = f.parent.map((_, i) => { let x = i; const p = f.parent; while (p[x] !== x) x = p[x]; return x; });
    f.ids.forEach((lab, i) => {
      const [x, y] = at(i);
      AV.node(ctx, P, x, y, 19, lab, {
        fill: P.alpha(P.series[roots[i] % P.series.length], .22),
        stroke: f.roots?.includes(i) ? P.accent : P.series[roots[i] % P.series.length],
        sub: `→${f.ids[f.parent[i]]}`,
      });
    });
    D.text(ctx, 'parent array (a colour = one component)', 20, c.h - 62, { color: P.dim, size: 11.5, weight: 650 });
    f.ids.forEach((lab, i) => {
      const x = 20 + i * 54, y = c.h - 52;
      ctx.fillStyle = P.alpha(P.series[roots[i] % P.series.length], .22); D.rrect(ctx, x, y, 48, 24, 7); ctx.fill();
      ctx.strokeStyle = P.series[roots[i] % P.series.length]; ctx.lineWidth = 1.2; ctx.stroke();
      D.text(ctx, `${lab}→${f.ids[f.parent[i]]}`, x + 24, y + 12.5, { color: P.text, size: 11.5, align: 'center', mono: true, weight: 600 });
    });
    D.text(ctx, `MST weight: ${f.cost}`, 20, c.h - 12, { color: P.ok, size: 13, weight: 700 });
  },
});

/* ==================================================================== 16 · dp 1d == */
defineAlgo('16_dp_1d', {
  title: 'House robber: one row of state', short: 'House Robber',
  idea: 'At each house the choice is <b>rob it</b> (then you must skip the previous one) or <b>skip it</b> (then keep the best so far). <code>dp[i] = max(dp[i-1], dp[i-2] + nums[i])</code> — each cell is decided once, so the exponential recursion collapses to one pass.',
  complexity: 'Time O(n) · Space O(n), or O(1) keeping just the last two values',
  input: '2, 7, 9, 3, 1, 5', hint: 'house values',
  code: [
    'def rob(nums):',
    '    if not nums: return 0',
    '    dp = [0] * len(nums)',
    '    dp[0] = nums[0]',
    '    for i in range(1, len(nums)):',
    '        skip = dp[i - 1]              # do not rob house i',
    '        take = nums[i] + (dp[i - 2] if i > 1 else 0)',
    '        dp[i] = max(skip, take)',
    '    return dp[-1]',
  ],
  parse(s) { return { nums: avNums(s, 10, 'houses') }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    const dp = nums.map(() => null), pick = nums.map(() => null);
    dp[0] = nums[0]; pick[0] = 'take';
    const S = (extra = {}) => ({ nums, dp: [...dp], pick: [...pick], ...extra });
    snap(3, `With only house 0 available the best is ${nums[0]}.`, S({ cur: 0, vars: { 'dp[0]': dp[0] } }));
    for (let i = 1; i < nums.length; i++) {
      const skip = dp[i - 1], take = nums[i] + (i > 1 ? dp[i - 2] : 0);
      snap(5, `Skip house ${i}: keep <code>dp[${i - 1}] = ${skip}</code>.`, S({ cur: i, from: i - 1, vars: { i, skip } }));
      snap(6, `Rob house ${i}: ${nums[i]}${i > 1 ? ` + dp[${i - 2}] = ${dp[i - 2]}` : ''} = ${take}.`, S({ cur: i, from: i > 1 ? i - 2 : null, rob: i, vars: { i, take } }));
      dp[i] = Math.max(skip, take); pick[i] = take > skip ? 'take' : 'skip';
      snap(7, `<code>dp[${i}] = max(${skip}, ${take}) = <b>${dp[i]}</b></code> — ${pick[i] === 'take' ? `rob house ${i}` : `walk past house ${i}`}.`, S({ cur: i, vars: { i, [`dp[${i}]`]: dp[i] } }));
    }
    const path = [];
    let i = nums.length - 1;
    while (i >= 0) { if (pick[i] === 'take') { path.push(i); i -= 2; } else i -= 1; }
    snap(8, `Best haul <b>${dp[nums.length - 1]}</b>, from houses ${path.reverse().join(', ')}.`, S({ chosen: path, vars: { answer: dp[nums.length - 1] } }));
    return F;
  },
  height: () => 280,
  draw(ctx, c, f, P) {
    const chosen = new Set(f.chosen || []);
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 44, max: 48, style: i => chosen.has(i) ? { fill: P.alpha('ok', .3), stroke: P.ok } : i === f.rob ? { fill: P.alpha('accent', .3), stroke: P.accent } : i === f.cur ? { stroke: P.accent } : i === f.from ? { stroke: P.series[0] } : {} });
    D.text(ctx, 'nums', g.left - 10, g.y + g.size / 2, { color: P.dim, size: 11.5, align: 'right', weight: 650 });
    const dy = g.y + g.size + 52;
    const d = AV.row(ctx, P, f.dp.map(v => (v === null ? '·' : v)), { cw: c.w, y: dy, max: 48, index: false, style: i => f.dp[i] === null ? { fade: true } : i === f.cur ? { fill: P.alpha('accent', .25), stroke: P.accent } : i === f.from ? { stroke: P.series[0] } : { fill: P.alpha('ok', .12) } });
    D.text(ctx, 'dp', d.left - 10, d.y + d.size / 2, { color: P.dim, size: 11.5, align: 'right', weight: 650 });
    if (f.cur > 0) {
      const y0 = d.y - 8;
      if (f.from != null) AV.arrow(ctx, d.x(f.from), y0, d.x(f.cur), y0, P.series[0], 2);
      if (f.rob != null) AV.arrow(ctx, g.x(f.rob), g.y + g.size + 6, d.x(f.cur), d.y - 6, P.accent, 2);
    }
    D.text(ctx, f.chosen ? `robbed: ${f.chosen.map(i => `house ${i} (${f.nums[i]})`).join(' + ')}` : 'dp[i] = max(skip previous best, rob this + dp[i−2])', 20, c.h - 16, { color: f.chosen ? P.ok : P.dim, size: 12.5, mono: !!f.chosen, weight: 650 });
  },
});

defineAlgo(['16_dp_1d', '28_recursion_backtracking'], {
  title: 'Recursion tree vs memoisation', short: 'Memoisation',
  idea: 'Plain <code>fib(n)</code> re-solves the same subproblem on every branch — the tree doubles at each level. A memo turns each distinct call into a single node: <b>overlapping subproblems</b> is exactly the signal that says “this is dynamic programming”.',
  complexity: 'Naive O(φⁿ) calls · memoised O(n) calls, O(n) space',
  input: '6', hint: 'n between 3 and 8',
  variants: [['naive', 'Plain recursion'], ['memo', 'With a memo']],
  code: v => v === 'memo' ? [
    'def fib(n, memo={}):',
    '    if n < 2: return n',
    '    if n in memo:',
    '        return memo[n]                # already solved',
    '    memo[n] = fib(n - 1, memo) + fib(n - 2, memo)',
    '    return memo[n]',
  ] : [
    'def fib(n):',
    '    if n < 2: return n',
    '    return fib(n - 1) + fib(n - 2)    # both sides re-computed',
  ],
  parse(s) { const n = avNums(s, 1, 'one number')[0]; if (n < 3 || n > 8) throw new Error('Use an n between 3 and 8'); return { n }; },
  run({ n }, v) {
    const { F, snap } = avRecorder();
    const nodes = [], memo = {};
    let calls = 0;
    const S = (extra = {}) => ({ n, nodes: nodes.map(x => ({ ...x })), memo: { ...memo }, calls, ...extra });
    const go = (k, parent, depth) => {
      const id = nodes.length;
      nodes.push({ k, parent, depth, val: null, hit: false });
      calls++;
      snap(0, `Call <code>fib(${k})</code>.`, S({ cur: id, vars: { call: `fib(${k})`, calls } }));
      if (k < 2) { nodes[id].val = k; snap(1, `Base case: fib(${k}) = ${k}.`, S({ cur: id, vars: { calls } })); return k; }
      if (v === 'memo' && memo[k] !== undefined) {
        nodes[id].val = memo[k]; nodes[id].hit = true;
        snap(3, `<b>Memo hit</b>: fib(${k}) = ${memo[k]} — the whole subtree below is skipped.`, S({ cur: id, vars: { calls, memo_hits: Object.keys(memo).length } }));
        return memo[k];
      }
      const a = go(k - 1, id, depth + 1), b = go(k - 2, id, depth + 1);
      nodes[id].val = a + b;
      if (v === 'memo') memo[k] = a + b;
      snap(v === 'memo' ? 4 : 2, `fib(${k}) = ${a} + ${b} = <b>${a + b}</b>${v === 'memo' ? `, stored in the memo` : ''}.`, S({ cur: id, vars: { calls, [`fib(${k})`]: a + b } }));
      return a + b;
    };
    const r = go(n, -1, 0);
    snap(v === 'memo' ? 5 : 2, `fib(${n}) = ${r} after <b>${calls}</b> call${calls === 1 ? '' : 's'}${v === 'naive' ? ' — switch to the memo variant and compare.' : '.'}`, S({ vars: { result: r, calls } }));
    return F;
  },
  height: (w, last) => 40 + (Math.max(...last.nodes.map(x => x.depth)) + 1) * 50 + 46,
  draw(ctx, c, f, P) {
    const maxD = Math.max(...f.nodes.map(x => x.depth));
    const perLevel = {};
    f.nodes.forEach(nd => { (perLevel[nd.depth] ??= []).push(nd); });
    const xy = new Map();
    Object.entries(perLevel).forEach(([d, list]) => list.forEach((nd, i) => {
      xy.set(nd, [24 + (i + .5) * (c.w - 48) / list.length, 36 + +d * 50]);
    }));
    f.nodes.forEach(nd => {
      if (nd.parent < 0) return;
      const [x1, y1] = xy.get(f.nodes[nd.parent]), [x2, y2] = xy.get(nd);
      D.line(ctx, x1, y1 + 13, x2, y2 - 13, P.strong, 1.2);
    });
    const r = Math.max(11, Math.min(17, (c.w - 48) / Math.max(4, Math.max(...Object.values(perLevel).map(l => l.length))) / 2.6));
    f.nodes.forEach((nd, id) => {
      const [x, y] = xy.get(nd);
      AV.node(ctx, P, x, y, r, nd.k, {
        fill: id === f.cur ? P.alpha('accent', .4) : nd.hit ? P.alpha('ok', .35) : nd.val !== null ? P.alpha('ok', .12) : null,
        stroke: id === f.cur ? P.accent : nd.hit ? P.ok : null,
        sub: nd.val !== null && r > 12 ? String(nd.val) : null,
      });
    });
    D.text(ctx, `calls so far: ${f.calls}`, 20, 16, { color: P.accent, size: 12.5, weight: 700 });
    const mk = Object.keys(f.memo);
    D.text(ctx, mk.length ? `memo: ${mk.sort((a, b) => a - b).map(k => `${k}→${f.memo[k]}`).join('  ')}` : 'no memo — every branch is recomputed', 20, c.h - 14, { color: mk.length ? P.ok : P.err, size: 12, mono: !!mk.length });
  },
});

/* ==================================================================== 17 · dp 2d == */
defineAlgo('17_dp_2d', {
  title: 'Longest common subsequence, with traceback', short: 'LCS grid',
  idea: 'Fill a table where <code>dp[i][j]</code> is the LCS of the first <i>i</i> and first <i>j</i> characters. Matching characters extend the diagonal by one; otherwise take the better of dropping one character from either string. Walking back from the corner reconstructs the subsequence itself.',
  complexity: 'Time O(m × n) · Space O(m × n), O(min(m, n)) if only the length is needed',
  input: 'abcde ; ace', hint: 'first string ; second string',
  code: [
    'def lcs(a, b):',
    '    dp = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]',
    '    for i in range(1, len(a) + 1):',
    '        for j in range(1, len(b) + 1):',
    '            if a[i - 1] == b[j - 1]:',
    '                dp[i][j] = dp[i - 1][j - 1] + 1   # extend the match',
    '            else:',
    '                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])',
    '    return dp[-1][-1]',
  ],
  parse(s) {
    const [a, b] = avParts(s);
    const A = String(a || '').replace(/\s/g, ''), B = String(b || '').replace(/\s/g, '');
    if (!A || !B) throw new Error('Enter two strings separated by “;”');
    if (A.length > 8 || B.length > 8) throw new Error('Use at most 8 characters per string');
    return { a: A, b: B };
  },
  run({ a, b }) {
    const { F, snap } = avRecorder();
    const m = a.length, n = b.length;
    const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0));
    const filled = Array.from({ length: m + 1 }, (_, i) => Array(n + 1).fill(i === 0));
    filled.forEach(r => (r[0] = true));
    const S = (extra = {}) => ({ a, b, dp: dp.map(r => [...r]), filled: filled.map(r => [...r]), ...extra });
    snap(1, 'Row 0 and column 0 are zero: an empty string shares nothing.', S({ vars: { m, n } }));
    for (let i = 1; i <= m; i++) for (let j = 1; j <= n; j++) {
      const match = a[i - 1] === b[j - 1];
      snap(4, `Compare <code>${a[i - 1]}</code> and <code>${b[j - 1]}</code>: ${match ? 'they match.' : 'no match.'}`, S({ cur: [i, j], vars: { i, j, a_i: a[i - 1], b_j: b[j - 1] } }));
      if (match) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
        snap(5, `Extend the diagonal: dp[${i - 1}][${j - 1}] + 1 = <b>${dp[i][j]}</b>.`, S({ cur: [i, j], src: [[i - 1, j - 1]], match: true, vars: { value: dp[i][j] } }));
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
        snap(7, `Take the better neighbour: max(${dp[i - 1][j]}, ${dp[i][j - 1]}) = <b>${dp[i][j]}</b>.`, S({ cur: [i, j], src: [[i - 1, j], [i, j - 1]], vars: { value: dp[i][j] } }));
      }
      filled[i][j] = true;
    }
    let i = m, j = n; const path = [], letters = [];
    while (i > 0 && j > 0) {
      path.push([i, j]);
      if (a[i - 1] === b[j - 1]) { letters.push(a[i - 1]); i--; j--; }
      else if (dp[i - 1][j] >= dp[i][j - 1]) i--;
      else j--;
    }
    snap(8, `Walk back from the corner: the LCS is <b>${letters.reverse().join('') || '(empty)'}</b>, length ${dp[m][n]}.`, S({ path, lcs: letters.join(''), vars: { length: dp[m][n], lcs: letters.join('') || '—' } }));
    return F;
  },
  height: (w, last) => 60 + (last.a.length + 1) * 40 + 40,
  draw(ctx, c, f, P) {
    const m = f.a.length, n = f.b.length;
    const cell = Math.min(40, (c.w - 90) / (n + 1), (c.h - 110) / (m + 1));
    const x0 = 56, y0 = 52;
    const X = j => x0 + j * cell, Y = i => y0 + i * cell;
    const path = new Set((f.path || []).map(([i, j]) => `${i},${j}`));
    const src = new Set((f.src || []).map(([i, j]) => `${i},${j}`));
    [...f.b].forEach((ch, j) => D.text(ctx, ch, X(j + 1) + cell / 2, y0 - 14, { color: f.cur && f.cur[1] === j + 1 ? P.accent : P.dim, size: 13, align: 'center', weight: 700, mono: true }));
    [...f.a].forEach((ch, i) => D.text(ctx, ch, x0 - 14, Y(i + 1) + cell / 2, { color: f.cur && f.cur[0] === i + 1 ? P.accent : P.dim, size: 13, align: 'center', weight: 700, mono: true }));
    for (let i = 0; i <= m; i++) for (let j = 0; j <= n; j++) {
      const cur = f.cur && f.cur[0] === i && f.cur[1] === j, key = `${i},${j}`;
      ctx.fillStyle = cur ? P.alpha('accent', .35) : path.has(key) ? P.alpha('ok', .28) : src.has(key) ? P.alpha(P.series[0], .22) : f.filled[i][j] ? P.surface2 : P.alpha('faint', .05);
      D.rrect(ctx, X(j) + 1, Y(i) + 1, cell - 2, cell - 2, 6); ctx.fill();
      ctx.strokeStyle = cur ? P.accent : path.has(key) ? P.ok : P.soft; ctx.lineWidth = cur || path.has(key) ? 2 : 1; ctx.stroke();
      if (f.filled[i][j]) D.text(ctx, String(f.dp[i][j]), X(j) + cell / 2, Y(i) + cell / 2, { color: f.dp[i][j] ? P.text : P.faint, size: Math.max(10, cell * .36), align: 'center', mono: true, weight: 650 });
    }
    if (f.cur && f.src) f.src.forEach(([si, sj]) => AV.arrow(ctx, X(sj) + cell / 2, Y(si) + cell / 2, X(f.cur[1]) + cell / 2 - (sj === f.cur[1] ? 0 : 6), Y(f.cur[0]) + cell / 2 - (si === f.cur[0] ? 0 : 6), f.match ? P.ok : P.series[0], 2));
    D.text(ctx, f.lcs !== undefined ? `LCS = “${f.lcs}” (length ${f.dp[m][n]})` : 'match → diagonal + 1   ·   mismatch → best of up / left', 20, c.h - 16, { color: f.lcs !== undefined ? P.ok : P.dim, size: 12.5, weight: 650, mono: f.lcs !== undefined });
  },
});

/* ==================================================================== 18 · greedy == */
defineAlgo('18_greedy', {
  title: 'Jump game: the furthest reach', short: 'Jump game',
  idea: 'Carry one number: the furthest index reachable so far. At index <i>i</i>, if <code>reach &lt; i</code> you are standing past the end of the world and the answer is no. Otherwise stretch the reach. One pass, one variable — no DP table needed.',
  complexity: 'Time O(n) · Space O(1)',
  input: '2, 3, 1, 1, 4', hint: 'jump lengths (try 3, 2, 1, 0, 4 for a failure)',
  code: [
    'def can_jump(nums):',
    '    reach = 0',
    '    for i, jump in enumerate(nums):',
    '        if i > reach:',
    '            return False              # a gap you cannot cross',
    '        reach = max(reach, i + jump)',
    '    return True',
  ],
  parse(s) { return { nums: avNums(s, 12, 'jump lengths') }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let reach = 0;
    const S = (extra = {}) => ({ nums, reach, ...extra });
    snap(1, 'Reach starts at index 0 — you are standing there.', S({ vars: { reach: 0 } }));
    for (let i = 0; i < nums.length; i++) {
      if (i > reach) { snap(4, `Index ${i} is beyond the reach of ${reach}: a gap you cannot cross. <b>False</b>.`, S({ cur: i, dead: true, vars: { i, reach, result: 'False' } })); return F; }
      snap(3, `Index ${i} is within reach (${reach}).`, S({ cur: i, vars: { i, reach } }));
      const cand = i + nums[i];
      if (cand > reach) { reach = cand; snap(5, `From here you can hop ${nums[i]}: reach stretches to <b>${reach}</b>.`, S({ cur: i, grew: true, vars: { i, reach } })); }
      else snap(5, `${i} + ${nums[i]} = ${cand} does not beat the current reach ${reach}.`, S({ cur: i, vars: { i, reach } }));
    }
    snap(6, `Walked the whole array without a gap: the last index is reachable. <b>True</b>.`, S({ cur: nums.length - 1, win: true, vars: { result: 'True' } }));
    return F;
  },
  height: () => 250,
  draw(ctx, c, f, P) {
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 70, max: 46, style: i => i === f.cur ? { fill: P.alpha(f.dead ? 'err' : 'accent', .35), stroke: f.dead ? P.err : P.accent } : i <= f.reach ? { fill: P.alpha('ok', .14), stroke: i === f.reach ? P.ok : null } : { fade: true } });
    const x1 = g.left - 4, x2 = g.x(Math.min(f.reach, f.nums.length - 1)) + g.size / 2 + 4;
    ctx.fillStyle = P.alpha('ok', .1); D.rrect(ctx, x1, g.y - 34, x2 - x1, 26, 8); ctx.fill();
    D.text(ctx, `reachable up to index ${f.reach}`, (x1 + x2) / 2, g.y - 21, { color: P.ok, size: 11.5, align: 'center', weight: 700 });
    if (f.cur != null && !f.dead) {
      const to = Math.min(f.nums.length - 1, f.cur + f.nums[f.cur]);
      ctx.beginPath(); ctx.moveTo(g.x(f.cur), g.y + g.size + 6);
      ctx.quadraticCurveTo((g.x(f.cur) + g.x(to)) / 2, g.y + g.size + 62, g.x(to), g.y + g.size + 6);
      ctx.strokeStyle = f.grew ? P.accent : P.alpha('dim', .5); ctx.lineWidth = f.grew ? 2.4 : 1.4; ctx.stroke();
      D.text(ctx, `jump ${f.nums[f.cur]}`, (g.x(f.cur) + g.x(to)) / 2, g.y + g.size + 48, { color: f.grew ? P.accent : P.faint, size: 11, align: 'center', mono: true });
    }
    D.text(ctx, f.dead ? 'stuck: this index is unreachable' : f.win ? 'the last index is reachable' : 'greedy state = one number, the furthest reach', 20, c.h - 16, { color: f.dead ? P.err : f.win ? P.ok : P.dim, size: 12.5, weight: 650 });
  },
});

defineAlgo('18_greedy', {
  title: "Kadane's maximum subarray", short: 'Max subarray',
  idea: 'At each element decide one thing: <b>extend</b> the running sum, or <b>start fresh</b> here. You start fresh exactly when the running sum has gone negative — a negative prefix can never help what follows.',
  complexity: 'Time O(n) · Space O(1)',
  input: '-2, 1, -3, 4, -1, 2, 1, -5, 4', hint: 'numbers, negatives allowed',
  code: [
    'def max_subarray(nums):',
    '    best = cur = nums[0]',
    '    for x in nums[1:]:',
    '        cur = max(x, cur + x)      # extend, or start fresh at x',
    '        best = max(best, cur)',
    '    return best',
  ],
  parse(s) { return { nums: avNums(s, 12) }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let cur = nums[0], best = nums[0], start = 0, bs = 0, be = 0;
    const S = (extra = {}) => ({ nums, cur, best, start, bs, be, ...extra });
    snap(1, `Both the running sum and the best start at ${nums[0]}.`, S({ i: 0, vars: { cur, best } }));
    for (let i = 1; i < nums.length; i++) {
      const extend = cur + nums[i];
      const fresh = nums[i] > extend;
      snap(3, fresh ? `${cur} + ${nums[i]} = ${extend} is worse than ${nums[i]} alone — <b>start fresh</b> at index ${i}.` : `Extend: ${cur} + ${nums[i]} = <b>${extend}</b>.`, S({ i, fresh, vars: { i, extend, alone: nums[i] } }));
      if (fresh) { cur = nums[i]; start = i; } else cur = extend;
      if (cur > best) { best = cur; bs = start; be = i; snap(4, `New best: <b>${best}</b> from index ${bs} to ${be}.`, S({ i, newBest: true, vars: { cur, best } })); }
      else snap(4, `Best stays ${best}.`, S({ i, vars: { cur, best } }));
    }
    snap(5, `Maximum subarray sum <b>${best}</b>, the slice [${bs}…${be}].`, S({ i: null, done: true, vars: { answer: best, slice: `[${bs}…${be}]` } }));
    return F;
  },
  height: () => 300,
  draw(ctx, c, f, P) {
    const g = AV.bars(ctx, P, f.nums, {
      cw: c.w, top: 40, bottom: 190,
      style: i => i >= f.bs && i <= f.be ? { fill: P.alpha('ok', .55), stroke: i === f.i ? P.accent : null }
        : i >= f.start && i <= (f.i ?? -1) ? { fill: P.alpha('accent', .4) }
          : i === f.i ? { fill: P.alpha('accent', .5), stroke: P.accent } : { fill: P.alpha('faint', .25) },
    });
    D.line(ctx, 20, 190, c.w - 20, 190, P.strong, 1);
    if (f.i != null) AV.ptr(ctx, P, { x: g.x, y: 202, size: 0 }, f.i, 'i', P.accent);
    D.text(ctx, `running sum: ${f.cur}`, 20, 240, { color: P.accent, size: 13, weight: 700, mono: true });
    D.text(ctx, `best so far: ${f.best}  (indices ${f.bs}…${f.be})`, 20, 262, { color: P.ok, size: 13, weight: 700, mono: true });
    if (f.fresh) D.text(ctx, 'restart — a negative prefix never helps', c.w - 20, 240, { color: P.err, size: 12, align: 'right', weight: 650 });
    if (f.done) D.text(ctx, 'green = the winning subarray', c.w - 20, 262, { color: P.ok, size: 12, align: 'right', weight: 650 });
  },
});

/* ================================================================= 19 · intervals == */
defineAlgo('19_intervals', {
  title: 'Merge intervals', short: 'Merge',
  idea: 'Sort by start. Then one sweep is enough: an interval either overlaps the one you are holding — extend its end — or starts after it, which closes the current interval for good. Sorting is what makes “one look back” sufficient.',
  complexity: 'Time O(n log n) for the sort, O(n) for the sweep · Space O(n) for the output',
  input: '1-3, 8-10, 2-6, 15-18, 9-12', hint: 'intervals as start-end, comma separated',
  code: [
    'def merge(intervals):',
    '    intervals.sort(key=lambda x: x[0])',
    '    out = [intervals[0]]',
    '    for start, end in intervals[1:]:',
    '        if start <= out[-1][1]:            # overlaps the open one',
    '            out[-1][1] = max(out[-1][1], end)',
    '        else:',
    '            out.append([start, end])       # a gap: close and open',
    '    return out',
  ],
  parse(s) {
    const iv = String(s || '').split(/[,\n]/).map(x => x.trim()).filter(Boolean).map(tok => {
      const m = tok.match(/^(-?\d+)\s*[-–:]\s*(-?\d+)$/);
      if (!m) throw new Error(`“${tok}” should look like 3-7`);
      const a = +m[1], b = +m[2];
      if (b < a) throw new Error(`“${tok}” ends before it starts`);
      return [a, b];
    });
    if (!iv.length) throw new Error('Enter at least one interval');
    if (iv.length > 8) throw new Error('Use at most 8 intervals');
    return { iv };
  },
  run({ iv }) {
    const { F, snap } = avRecorder();
    const sorted = [...iv].sort((a, b) => a[0] - b[0]);
    const out = [];
    const S = (extra = {}) => ({ iv, sorted: sorted.map(x => [...x]), out: out.map(x => [...x]), ...extra });
    snap(1, `Sort by start: ${sorted.map(([a, b]) => `[${a},${b}]`).join(' ')}.`, S({ vars: { n: iv.length } }));
    out.push([...sorted[0]]);
    snap(2, `Open the first interval [${sorted[0][0]}, ${sorted[0][1]}].`, S({ cur: 0, vars: { open: `[${out[0][0]}, ${out[0][1]}]` } }));
    for (let i = 1; i < sorted.length; i++) {
      const [s0, e0] = sorted[i], last = out[out.length - 1];
      const ov = s0 <= last[1];
      snap(4, `Does [${s0}, ${e0}] start before the open interval ends (${last[1]})? ${ov ? 'Yes — they overlap.' : 'No — there is a gap.'}`, S({ cur: i, compare: true, vars: { start: s0, open_end: last[1] } }));
      if (ov) {
        const grew = e0 > last[1];
        last[1] = Math.max(last[1], e0);
        snap(5, grew ? `Extend the open interval to ${last[1]}.` : `Fully contained — the open interval does not change.`, S({ cur: i, merged: true, vars: { open: `[${last[0]}, ${last[1]}]` } }));
      } else {
        out.push([s0, e0]);
        snap(7, `Close the previous one and open [${s0}, ${e0}].`, S({ cur: i, opened: true, vars: { open: `[${s0}, ${e0}]`, closed: out.length - 1 } }));
      }
    }
    snap(8, `Result: ${out.map(([a, b]) => `[${a}, ${b}]`).join(', ')} — ${iv.length} intervals became ${out.length}.`, S({ done: true, vars: { merged_to: out.length } }));
    return F;
  },
  height: () => 300,
  draw(ctx, c, f, P) {
    const all = f.sorted.concat(f.out);
    const lo = Math.min(...all.map(x => x[0])), hi = Math.max(...all.map(x => x[1]));
    const pad = 30, W = c.w - pad * 2;
    const X = v => pad + (v - lo) / Math.max(1, hi - lo) * W;
    D.text(ctx, 'sorted by start', 20, 18, { color: P.dim, size: 11.5, weight: 650 });
    f.sorted.forEach(([a, b], i) => {
      const y = 32 + i * 22, on = i === f.cur;
      ctx.fillStyle = on ? P.alpha('accent', .35) : i < f.cur ? P.alpha('ok', .18) : P.surface2;
      D.rrect(ctx, X(a), y, Math.max(8, X(b) - X(a)), 16, 6); ctx.fill();
      ctx.strokeStyle = on ? P.accent : P.strong; ctx.lineWidth = on ? 2.2 : 1; ctx.stroke();
      D.text(ctx, `${a}–${b}`, (X(a) + X(b)) / 2, y + 8, { color: P.text, size: 10.5, align: 'center', mono: true });
    });
    const base = 32 + f.sorted.length * 22 + 26;
    D.text(ctx, 'merged output', 20, base - 12, { color: P.ok, size: 11.5, weight: 650 });
    f.out.forEach(([a, b], i) => {
      const y = base, last = i === f.out.length - 1;
      ctx.fillStyle = P.alpha('ok', last ? .35 : .18);
      D.rrect(ctx, X(a), y, Math.max(8, X(b) - X(a)), 20, 6); ctx.fill();
      ctx.strokeStyle = P.ok; ctx.lineWidth = last ? 2.4 : 1.2; ctx.stroke();
      D.text(ctx, `${a}–${b}`, (X(a) + X(b)) / 2, y + 10, { color: P.text, size: 11, align: 'center', mono: true, weight: 600 });
    });
    D.line(ctx, pad, base + 36, c.w - pad, base + 36, P.strong, 1);
    for (let v = lo; v <= hi; v += Math.max(1, Math.round((hi - lo) / 8))) D.text(ctx, String(v), X(v), base + 48, { color: P.faint, size: 10, align: 'center', mono: true });
    if (f.merged) D.text(ctx, 'overlap → extend the open interval', 20, c.h - 14, { color: P.accent, size: 12, weight: 650 });
    else if (f.opened) D.text(ctx, 'gap → close one, open the next', 20, c.h - 14, { color: P.series[0], size: 12, weight: 650 });
    else if (f.done) D.text(ctx, `${f.sorted.length} intervals → ${f.out.length} after merging`, 20, c.h - 14, { color: P.ok, size: 12.5, weight: 700 });
  },
});

defineAlgo('19_intervals', {
  title: 'Meeting rooms II: the sweep line', short: 'Meeting rooms',
  idea: 'Forget the intervals, keep only the events: +1 at every start, −1 at every end. Sort the events by time and sweep — the running count is how many rooms are in use, and its maximum is the answer.',
  complexity: 'Time O(n log n) · Space O(n) — identical to the min-heap solution, easier to say out loud',
  input: '0-30, 5-10, 15-20, 12-25', hint: 'meetings as start-end',
  code: [
    'def min_rooms(meetings):',
    '    events = []',
    '    for s, e in meetings:',
    '        events += [(s, +1), (e, -1)]      # ends sort first on ties',
    '    events.sort()',
    '    rooms = peak = 0',
    '    for _, delta in events:',
    '        rooms += delta',
    '        peak = max(peak, rooms)',
    '    return peak',
  ],
  parse(s) {
    const iv = String(s || '').split(/[,\n]/).map(x => x.trim()).filter(Boolean).map(tok => {
      const m = tok.match(/^(\d+)\s*[-–:]\s*(\d+)$/);
      if (!m) throw new Error(`“${tok}” should look like 5-10`);
      if (+m[2] <= +m[1]) throw new Error(`“${tok}” must end after it starts`);
      return [+m[1], +m[2]];
    });
    if (!iv.length) throw new Error('Enter at least one meeting');
    if (iv.length > 7) throw new Error('Use at most 7 meetings');
    return { iv };
  },
  run({ iv }) {
    const { F, snap } = avRecorder();
    const events = [];
    iv.forEach(([s, e], i) => { events.push({ t: s, d: 1, i }); events.push({ t: e, d: -1, i }); });
    events.sort((a, b) => a.t - b.t || a.d - b.d);
    let rooms = 0, peak = 0;
    const open = new Set();
    const S = (extra = {}) => ({ iv, events, rooms, peak, open: [...open], ...extra });
    snap(4, `${iv.length} meetings become ${events.length} events, sorted by time (an end before a start at the same instant, so a room can be reused).`, S({ vars: { events: events.length } }));
    events.forEach((ev, k) => {
      rooms += ev.d;
      if (ev.d === 1) open.add(ev.i); else open.delete(ev.i);
      const isPeak = rooms > peak;
      if (isPeak) peak = rooms;
      snap(ev.d === 1 ? 7 : 7, `t = ${ev.t}: meeting ${ev.i + 1} ${ev.d === 1 ? 'starts' : 'ends'} → ${rooms} room${rooms === 1 ? '' : 's'} in use${isPeak ? ' — a new peak.' : '.'}`, S({ k, peakNow: isPeak, vars: { time: ev.t, rooms, peak } }));
    });
    snap(9, `The sweep never needed more than <b>${peak}</b> room${peak === 1 ? '' : 's'} at once.`, S({ k: null, done: true, vars: { answer: peak } }));
    return F;
  },
  height: (w, last) => 120 + last.iv.length * 26 + 90,
  draw(ctx, c, f, P) {
    const lo = Math.min(...f.iv.map(x => x[0])), hi = Math.max(...f.iv.map(x => x[1]));
    const pad = 34, X = v => pad + (v - lo) / Math.max(1, hi - lo) * (c.w - pad * 2);
    const openSet = new Set(f.open);
    const now = f.k == null ? null : f.events[f.k].t;
    f.iv.forEach(([a, b], i) => {
      const y = 30 + i * 26;
      ctx.fillStyle = openSet.has(i) ? P.alpha('accent', .32) : P.surface2;
      D.rrect(ctx, X(a), y, Math.max(10, X(b) - X(a)), 19, 6); ctx.fill();
      ctx.strokeStyle = openSet.has(i) ? P.accent : P.strong; ctx.lineWidth = openSet.has(i) ? 2.2 : 1; ctx.stroke();
      D.text(ctx, `${a}–${b}`, (X(a) + X(b)) / 2, y + 9.5, { color: P.text, size: 10.5, align: 'center', mono: true });
    });
    const axis = 30 + f.iv.length * 26 + 14;
    D.line(ctx, pad, axis, c.w - pad, axis, P.strong, 1);
    f.events.forEach(ev => {
      D.line(ctx, X(ev.t), axis - 5, X(ev.t), axis + 5, ev.d === 1 ? P.ok : P.err, 2);
      D.text(ctx, ev.d === 1 ? '+1' : '−1', X(ev.t), axis + 15, { color: ev.d === 1 ? P.ok : P.err, size: 9.5, align: 'center', mono: true });
    });
    if (now != null) {
      D.line(ctx, X(now), 22, X(now), axis + 22, P.accent, 2, [5, 4]);
      D.text(ctx, `t = ${now}`, X(now), 14, { color: P.accent, size: 11.5, align: 'center', weight: 700, mono: true });
    }
    const gy = axis + 40, gh = 46, mx = Math.max(1, f.peak);
    let count = 0;
    ctx.beginPath(); ctx.moveTo(pad, gy + gh);
    f.events.forEach((ev, k) => {
      if (f.k != null && k > f.k) return;
      count += ev.d;
      ctx.lineTo(X(ev.t), gy + gh - (count - ev.d) / mx * gh);
      ctx.lineTo(X(ev.t), gy + gh - count / mx * gh);
    });
    ctx.lineTo(f.k == null ? c.w - pad : X(f.events[f.k].t), gy + gh - (f.k == null ? 0 : f.rooms) / mx * gh);
    ctx.strokeStyle = P.accent; ctx.lineWidth = 2.2; ctx.stroke();
    D.line(ctx, pad, gy + gh - f.peak / mx * gh, c.w - pad, gy + gh - f.peak / mx * gh, P.alpha('ok', .7), 1.4, [4, 4]);
    D.text(ctx, `peak ${f.peak}`, c.w - pad, gy + gh - f.peak / mx * gh - 9, { color: P.ok, size: 11.5, align: 'right', weight: 700 });
    D.text(ctx, `rooms in use: ${f.rooms}`, 20, c.h - 12, { color: P.accent, size: 13, weight: 700, mono: true });
  },
});

/* =========================================================== 20 · bit manipulation == */
defineAlgo('20_bit_manipulation', {
  title: 'Single number: XOR cancellation', short: 'Single number',
  idea: 'XOR is its own inverse: <code>x ^ x = 0</code> and <code>x ^ 0 = x</code>. It is also commutative, so the order does not matter — every pair annihilates itself and the loner is what survives. Constant space, no hash set.',
  complexity: 'Time O(n) · Space O(1)',
  input: '4, 1, 2, 1, 2', hint: 'numbers where every value but one appears twice',
  code: [
    'def single_number(nums):',
    '    acc = 0',
    '    for x in nums:',
    '        acc ^= x        # pairs cancel, the loner survives',
    '    return acc',
  ],
  parse(s) { const nums = avNums(s, 9); if (nums.some(x => x < 0 || x > 255)) throw new Error('Use values between 0 and 255 so the bits fit'); return { nums }; },
  run({ nums }) {
    const { F, snap } = avRecorder();
    let acc = 0;
    const S = (extra = {}) => ({ nums, acc, ...extra });
    snap(1, 'The accumulator starts at 0 — all bits off.', S({ vars: { acc: 0 } }));
    nums.forEach((x, i) => {
      const before = acc;
      acc ^= x;
      const flips = [...Array(8).keys()].filter(b => ((before ^ acc) >> b) & 1);
      snap(3, `XOR in ${x}: bits ${flips.map(b => b).reverse().join(', ') || '(none)'} flip → ${acc}.`, S({ i, before, flips, vars: { x, acc } }));
    });
    snap(4, `Everything paired off. The number that appears once is <b>${acc}</b>.`, S({ i: null, done: true, vars: { answer: acc } }));
    return F;
  },
  height: () => 270,
  draw(ctx, c, f, P) {
    const bits = (v, n = 8) => [...Array(n).keys()].map(b => (v >> (n - 1 - b)) & 1);
    const g = AV.row(ctx, P, f.nums, { cw: c.w, y: 34, max: 40, style: i => i === f.i ? { fill: P.alpha('accent', .35), stroke: P.accent } : i < (f.i ?? f.nums.length) ? { fade: true } : {} });
    const rowY = g.y + g.size + 54, bw = Math.min(30, (c.w - 200) / 8);
    const drawBits = (y, val, label, color, flips = []) => {
      D.text(ctx, label, 20, y + 13, { color: P.dim, size: 11.5, weight: 650, mono: true });
      bits(val).forEach((b, k) => {
        const x = 120 + k * (bw + 4), flip = flips.includes(7 - k);
        ctx.fillStyle = flip ? P.alpha('accent', .4) : b ? P.alpha(color, .3) : P.surface2;
        D.rrect(ctx, x, y, bw, 26, 5); ctx.fill();
        ctx.strokeStyle = flip ? P.accent : b ? color : P.strong; ctx.lineWidth = flip ? 2.2 : 1; ctx.stroke();
        D.text(ctx, String(b), x + bw / 2, y + 13, { color: b ? P.text : P.faint, size: 12.5, align: 'center', mono: true, weight: 700 });
      });
      D.text(ctx, `= ${val}`, 120 + 8 * (bw + 4) + 10, y + 13, { color, size: 12, mono: true, weight: 650 });
    };
    if (f.i != null) {
      drawBits(rowY, f.before, 'acc', P.series[0]);
      drawBits(rowY + 34, f.nums[f.i], `^ ${f.nums[f.i]}`, P.accent);
      D.line(ctx, 20, rowY + 66, c.w - 20, rowY + 66, P.strong, 1);
      drawBits(rowY + 74, f.acc, '= acc', P.ok, f.flips || []);
    } else {
      drawBits(rowY + 34, f.acc, 'acc', f.done ? P.ok : P.series[0]);
      if (f.done) D.text(ctx, 'every duplicate cancelled itself out', c.w / 2, rowY + 88, { color: P.ok, size: 12.5, align: 'center', weight: 650 });
    }
  },
});

defineAlgo('20_bit_manipulation', {
  title: 'Counting bits with n & (n − 1)', short: 'Count bits',
  idea: '<code>n & (n − 1)</code> clears the lowest set bit — so the loop runs once per 1-bit, not once per bit width. The DP version reuses that: <code>bits[n] = bits[n &amp; (n − 1)] + 1</code>, an answer you already computed.',
  complexity: 'Brian Kernighan O(popcount) per number · the DP table is O(n) for all numbers up to n',
  input: '13', hint: 'a number from 1 to 255',
  variants: [['kern', 'Clear lowest bit'], ['dp', 'DP table to n']],
  code: v => v === 'dp' ? [
    'def count_bits(n):',
    '    bits = [0] * (n + 1)',
    '    for i in range(1, n + 1):',
    '        bits[i] = bits[i & (i - 1)] + 1   # already solved, + 1',
    '    return bits',
  ] : [
    'def popcount(n):',
    '    count = 0',
    '    while n:',
    '        n &= n - 1        # clears the lowest set bit',
    '        count += 1',
    '    return count',
  ],
  parse(s) { const n = avNums(s, 1, 'one number')[0]; if (n < 1 || n > 255) throw new Error('Use a number from 1 to 255'); return { n }; },
  run({ n }, v) {
    const { F, snap } = avRecorder();
    if (v === 'dp') {
      const top = Math.min(n, 16);
      const bits = [0];
      const S = (extra = {}) => ({ mode: 'dp', top, bits: [...bits], ...extra });
      snap(1, `Build the table for 0…${top}. bits[0] = 0.`, S({ vars: { n: top } }));
      for (let i = 1; i <= top; i++) {
        const prev = i & (i - 1);
        snap(3, `<code>${i} & ${i - 1} = ${prev}</code> — that is ${i} with its lowest 1-bit removed.`, S({ cur: i, src: prev, vars: { i, 'i & (i-1)': prev } }));
        bits[i] = bits[prev] + 1;
        snap(3, `bits[${i}] = bits[${prev}] + 1 = <b>${bits[i]}</b>.`, S({ cur: i, src: prev, filled: true, vars: { i, bits: bits[i] } }));
      }
      snap(4, `Whole table in one pass: ${bits.map((b, i) => `${i}:${b}`).join('  ')}.`, S({ done: true, vars: { total: bits.reduce((a, b) => a + b, 0) } }));
      return F;
    }
    let x = n, count = 0;
    const S = (extra = {}) => ({ mode: 'kern', n, x, count, ...extra });
    snap(1, `Start with ${n} = ${n.toString(2)}₂.`, S({ vars: { n, count: 0 } }));
    while (x) {
      const nx = x & (x - 1), cleared = 31 - Math.clz32(x & -x);
      snap(3, `${x} & ${x - 1} = ${nx}: bit ${cleared} (the lowest 1) is gone.`, S({ before: x, cleared, vars: { x, 'x & (x-1)': nx } }));
      x = nx; count++;
      snap(4, `Count = ${count}.`, S({ cleared, vars: { x, count } }));
    }
    snap(5, `x reached 0 after <b>${count}</b> iteration${count === 1 ? '' : 's'} — ${n} has ${count} one-bit${count === 1 ? '' : 's'}.`, S({ done: true, vars: { answer: count } }));
    return F;
  },
  height: (w, last) => (last.mode === 'dp' ? 260 : 230),
  draw(ctx, c, f, P) {
    if (f.mode === 'dp') {
      const vals = [...Array(f.top + 1).keys()];
      const g = AV.row(ctx, P, vals, { cw: c.w, y: 34, max: 34, index: false, style: i => i === f.cur ? { fill: P.alpha('accent', .3), stroke: P.accent } : i === f.src ? { fill: P.alpha(P.series[0], .25), stroke: P.series[0] } : {} });
      D.text(ctx, 'i', g.left - 10, g.y + g.size / 2, { color: P.dim, size: 11.5, align: 'right', weight: 650 });
      const b = AV.row(ctx, P, vals.map(i => (f.bits[i] === undefined ? '·' : f.bits[i])), { cw: c.w, y: g.y + g.size + 42, max: 34, index: false, style: i => f.bits[i] === undefined ? { fade: true } : i === f.cur ? { fill: P.alpha('accent', .3), stroke: P.accent } : i === f.src ? { stroke: P.series[0] } : { fill: P.alpha('ok', .12) } });
      D.text(ctx, 'bits', b.left - 10, b.y + b.size / 2, { color: P.dim, size: 11.5, align: 'right', weight: 650 });
      if (f.cur != null) AV.arrow(ctx, b.x(f.src), b.y + b.size + 12, b.x(f.cur), b.y + b.size + 12, P.series[0], 2);
      D.text(ctx, f.done ? 'each answer reuses one already in the table' : 'bits[i] = bits[i & (i−1)] + 1', 20, c.h - 16, { color: f.done ? P.ok : P.dim, size: 12.5, weight: 650 });
      return;
    }
    const bw = Math.min(34, (c.w - 140) / 8), y = 60;
    const draw8 = (val, yy, label, color, hi) => {
      D.text(ctx, label, 20, yy + 15, { color: P.dim, size: 11.5, weight: 650, mono: true });
      for (let k = 0; k < 8; k++) {
        const bit = (val >> (7 - k)) & 1, x = 104 + k * (bw + 5), on = hi === 7 - k;
        ctx.fillStyle = on ? P.alpha('err', .35) : bit ? P.alpha(color, .3) : P.surface2;
        D.rrect(ctx, x, yy, bw, 30, 6); ctx.fill();
        ctx.strokeStyle = on ? P.err : bit ? color : P.strong; ctx.lineWidth = on ? 2.4 : 1; ctx.stroke();
        D.text(ctx, String(bit), x + bw / 2, yy + 15, { color: bit ? P.text : P.faint, size: 13, align: 'center', mono: true, weight: 700 });
        if (yy === y) D.text(ctx, String(7 - k), x + bw / 2, yy - 10, { color: P.faint, size: 9.5, align: 'center', mono: true });
      }
      D.text(ctx, `= ${val}`, 104 + 8 * (bw + 5) + 8, yy + 15, { color, size: 12.5, mono: true, weight: 650 });
    };
    if (f.before != null) { draw8(f.before, y, 'before', P.accent, f.cleared); draw8(f.x, y + 44, 'after', P.ok); }
    else draw8(f.x, y + 22, f.done ? 'x = 0' : 'x', f.done ? P.ok : P.accent);
    D.text(ctx, `count = ${f.count}`, 20, c.h - 16, { color: P.ok, size: 13.5, weight: 700, mono: true });
    D.text(ctx, 'the loop runs once per 1-bit, not 32 times', c.w - 20, c.h - 16, { color: P.dim, size: 12, align: 'right' });
  },
});
