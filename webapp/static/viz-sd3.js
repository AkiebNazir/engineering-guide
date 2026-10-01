/* ============================================================================
   System design labs, part 3 — probabilistic structures, geo indexes, feeds,
   IDs, estimation, tail latency, collaboration, streaming windows, sagas,
   real-time transports, idempotency and autoscaling.
   Requires viz.js and viz-sd.js.
   ========================================================================= */
'use strict';

const fmtBytes = b => { const u = ['B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB']; let i = 0; while (b >= 1000 && i < u.length - 1) { b /= 1000; i++; } return `${b >= 100 ? Math.round(b) : +b.toFixed(1)} ${u[i]}`; };
const fmtBits = b => { const u = ['bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']; let i = 0; while (b >= 1000 && i < u.length - 1) { b /= 1000; i++; } return `${b >= 100 ? Math.round(b) : +b.toFixed(1)} ${u[i]}`; };
const fmtQps = q => q >= 1e6 ? `${+(q / 1e6).toFixed(1)}M/s` : q >= 1e3 ? `${+(q / 1e3).toFixed(1)}K/s` : `${q >= 10 ? Math.round(q) : +q.toFixed(1)}/s`;

/* ======================================== 13 · bloom filter + count-min == */
defineLab('sd-sketch', {
  title: 'Probabilistic structures: Bloom filter and count-min sketch',
  hint: 'Trade a little accuracy for a lot of memory. A Bloom filter answers “seen before?”; a count-min sketch answers “how many times?”.',
  mount(L, opts) {
    const r = rng(15);
    const s = { mode: opts.mode || 'bloom', m: 48, k: 3, items: [], last: null, w: 10, d: 3, grid: [], counts: new Map(), N: 0, flash: [] };
    const c = L.canvas(w => Math.min(290, w * .44));
    L.seg('', [['bloom', 'Bloom filter'], ['cms', 'Count-min sketch']], s.mode, v => { s.mode = v; build(); });
    const pos = (x, j, m) => fnv(x, j * 131 + 7) % m;
    function build() {
      L.clearDyn();
      L.actions.querySelectorAll('[data-dyn]').forEach(n => n.remove());
      const btn = (label, fn, cls) => { const b = L.button(label, fn, cls); b.dataset.dyn = '1'; return b; };
      if (s.mode === 'bloom') {
        L.slider('bits m', { min: 16, max: 96, step: 8, value: s.m, dyn: true }, v => { s.m = v; update(); });
        L.slider('hash functions k', { min: 1, max: 6, step: 1, value: s.k, dyn: true }, v => { s.k = v; update(); });
        btn('Insert the next URL', () => { s.items.push(`site.com/p/${s.items.length}`); s.last = { x: s.items[s.items.length - 1], insert: true }; update(); }, 'primary');
        btn('Insert 5', () => { for (let i = 0; i < 5; i++) s.items.push(`site.com/p/${s.items.length}`); s.last = null; update(); });
        btn('Query a URL', () => { const known = r() < .4 && s.items.length; s.last = { x: known ? s.items[Math.floor(r() * s.items.length)] : `other.org/${Math.floor(r() * 1e5)}` }; update(); }, 'primary');
        btn('Clear', () => { s.items = []; s.last = null; update(); });
      } else {
        L.slider('width w (columns)', { min: 4, max: 24, step: 1, value: s.w, dyn: true }, v => { s.w = v; resetCms(); });
        L.slider('depth d (hash rows)', { min: 1, max: 5, step: 1, value: s.d, dyn: true }, v => { s.d = v; resetCms(); });
        const stream = L.loop(() => { for (let i = 0; i < 6 && s.queue > 0; i++, s.queue--) addEvent(); update(); if (s.queue <= 0) return false; });
        btn('Stream 300 events', () => { s.queue = 300; stream.start(); }, 'primary');
        btn('Reset', () => resetCms());
        resetCms();
      }
      update();
    }
    const zipf = (() => { const w = Array.from({ length: 40 }, (_, i) => 1 / (i + 1)), tot = w.reduce((a, b) => a + b, 0); return () => { let u = r() * tot; for (let i = 0; i < 40; i++) { if ((u -= w[i]) <= 0) return `#${i + 1}`; } return '#40'; }; })();
    function resetCms() { s.grid = Array.from({ length: s.d }, () => new Array(s.w).fill(0)); s.counts = new Map(); s.N = 0; s.queue = 0; update(); }
    function addEvent() {
      const x = zipf();
      s.counts.set(x, (s.counts.get(x) || 0) + 1); s.N++;
      s.flash = [];
      for (let j = 0; j < s.d; j++) { const col = pos(x, j, s.w); s.grid[j][col]++; s.flash.push([j, col]); }
    }
    const estimate = x => Math.min(...Array.from({ length: s.d }, (_, j) => s.grid[j][pos(x, j, s.w)]));
    function update() {
      if (s.mode === 'bloom') {
        const bits = new Set(); s.items.forEach(x => { for (let j = 0; j < s.k; j++) bits.add(pos(x, j, s.m)); });
        s.bits = bits;
        let fp = 0; for (let i = 0; i < 400; i++) { const x = `probe-${i}`; if (Array.from({ length: s.k }, (_, j) => bits.has(pos(x, j, s.m))).every(Boolean)) fp++; }
        const n = s.items.length, theory = (1 - Math.exp(-s.k * n / s.m)) ** s.k;
        let verdict = '';
        if (s.last && !s.last.insert) {
          const all = Array.from({ length: s.k }, (_, j) => bits.has(pos(s.last.x, j, s.m))).every(Boolean), real = s.items.includes(s.last.x);
          s.last.result = !all ? 'no' : real ? 'yes' : 'fp';
          verdict = !all ? `“${s.last.x}” is definitely not in the set: one of its ${s.k} bits is 0.` : real ? `“${s.last.x}” is probably in the set, and it really is.` : `False positive: every bit for “${s.last.x}” happens to be set by other URLs, but it was never inserted.`;
        }
        L.stats([['inserted', n], ['bits set', `${Math.round(bits.size / s.m * 100)}%`], ['false-positive rate (theory)', `${(theory * 100).toFixed(1)}%`, 'accent'], ['measured on 400 unseen URLs', `${(fp / 4).toFixed(1)}%`]]);
        L.insight(verdict ? `<b>${verdict}</b> A Bloom filter never gives a false “no”, which is why a crawler can use it to skip URLs it has seen, and an LSM tree to skip files.` : `<b>Each insert sets ${s.k} bits.</b> As the array fills, unrelated items collide and false positives rise. With about 10 bits per item and k = 7 the rate is about 1%, in a fraction of the memory a hash set needs.`);
      } else {
        const top = [...s.counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 6);
        const errs = top.map(([x, cnt]) => estimate(x) - cnt), eps = Math.E / s.w;
        s.top = top;
        L.stats([['events', s.N], ['memory', `${s.w * s.d} counters`], ['worst overcount in top 6', errs.length ? Math.max(...errs) : 0, 'accent'], ['error bound e/w · N', Math.round(eps * s.N)]]);
        L.insight(!s.N ? '<b>Stream events.</b> Each event adds 1 to one counter in every row. The estimate is the minimum across rows, so it can only overcount.'
          : `<b>Estimates never undercount.</b> Collisions only add, and taking the minimum across ${s.d} independent rows discards most of the noise. Heavy hitters stand out clearly, which is how top-K trending and ad-click counters work at scale in fixed memory.`);
      }
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      if (s.mode === 'bloom') {
        const perRow = 24, cell = Math.min(24, (c.w - 20) / perRow), rows = Math.ceil(s.m / perRow);
        const hl = s.last ? Array.from({ length: s.k }, (_, j) => pos(s.last.x, j, s.m)) : [];
        for (let i = 0; i < s.m; i++) {
          const x = 10 + (i % perRow) * cell, y = 30 + Math.floor(i / perRow) * cell, on = s.bits?.has(i);
          ctx.fillStyle = on ? P.accent : P.surface2; D.rrect(ctx, x + 1, y + 1, cell - 2, cell - 2, 3); ctx.fill();
          if (hl.includes(i)) { ctx.strokeStyle = on ? (s.last.result === 'fp' ? P.err : P.ok) : P.err; ctx.lineWidth = 2.4; D.rrect(ctx, x + 1, y + 1, cell - 2, cell - 2, 3); ctx.stroke(); }
          D.text(ctx, on ? '1' : '0', x + cell / 2, y + cell / 2, { color: on ? P.surface : P.faint, size: 9, align: 'center', mono: true });
        }
        D.text(ctx, `bit array (m = ${s.m})`, 10, 14, { color: P.dim, size: 11 });
        if (s.last) {
          const y = 40 + rows * cell;
          D.text(ctx, `${s.last.insert ? 'inserted' : 'query'}: ${s.last.x}  →  hash positions ${hl.join(', ')}`, 10, y, { color: P.text, size: 11.5, mono: true });
          if (!s.last.insert) D.text(ctx, s.last.result === 'no' ? 'DEFINITELY NOT PRESENT' : s.last.result === 'yes' ? 'PROBABLY PRESENT (correct)' : 'PROBABLY PRESENT (false positive)', 10, y + 20, { color: s.last.result === 'fp' ? P.err : s.last.result === 'no' ? P.dim : P.ok, size: 12, weight: 700 });
        }
      } else {
        const gw = Math.min(c.w * .58, 30 * s.w), cell = gw / s.w, ch = Math.min(34, (c.h - 40) / s.d), mx = Math.max(1, ...s.grid.flat());
        s.grid.forEach((row, j) => {
          D.text(ctx, `h${j + 1}`, 8, 34 + j * ch + ch / 2, { color: P.faint, size: 10, mono: true });
          row.forEach((v, i) => {
            const x = 30 + i * cell, y = 34 + j * ch, fl = s.flash.some(([a, b]) => a === j && b === i);
            ctx.fillStyle = P.alpha('accent', .08 + .8 * v / mx); D.rrect(ctx, x + 1, y + 1, cell - 2, ch - 2, 4); ctx.fill();
            if (fl) { ctx.strokeStyle = P.text; ctx.lineWidth = 2; ctx.stroke(); }
            if (cell > 22) D.text(ctx, String(v), x + cell / 2, y + ch / 2, { color: v / mx > .5 ? P.surface : P.text, size: 10, align: 'center', mono: true });
          });
        });
        D.text(ctx, `${s.d} × ${s.w} counters`, 30, 16, { color: P.dim, size: 11 });
        const tx = 50 + gw;
        D.text(ctx, 'item   true   estimate', tx, 16, { color: P.dim, size: 11, mono: true });
        (s.top || []).forEach(([x, cnt], i) => {
          const est = estimate(x);
          D.text(ctx, `${x.padEnd(5)}  ${String(cnt).padStart(4)}   ${String(est).padStart(4)}`, tx, 38 + i * 20, { color: P.text, size: 11, mono: true });
          if (est > cnt) D.text(ctx, `+${est - cnt}`, tx + 170, 38 + i * 20, { color: P.err, size: 10.5, mono: true });
        });
      }
    };
    build();
  },
});

/* ============================================= 14 · geospatial indexing == */
defineLab('sd-geo', {
  title: 'Finding nearby drivers: geohash grid vs quadtree',
  hint: 'Drag the rider (the ring) or click the map. Compare how many drivers each index has to scan to answer “who is within the radius?”.',
  mount(L) {
    const r = rng(27);
    const pts = [];
    [[.3, .35, .08, 170], [.7, .6, .06, 150], [.55, .2, .05, 60]].forEach(([cx, cy, sd, n]) => { for (let i = 0; i < n; i++) pts.push([clamp(cx + gauss(r) * sd, 0, .999), clamp(cy + gauss(r) * sd, 0, .999)]); });
    for (let i = 0; i < 80; i++) pts.push([r(), r()]);
    const s = { mode: 'grid', level: 4, cap: 12, q: [.32, .38], rad: .07 };
    const c = L.canvas(w => Math.min(380, w * .6));
    let v = null;
    L.seg('index', [['grid', 'Geohash grid'], ['quad', 'Quadtree'], ['brute', 'Scan everything']], s.mode, x => { s.mode = x; update(); });
    L.slider('search radius', { min: .02, max: .2, step: .005, value: s.rad, fmt: x => `${(x * 20).toFixed(1)} km` }, x => { s.rad = x; update(); });
    L.slider('grid precision (cells per side = 2^n)', { min: 1, max: 6, step: 1, value: s.level, fmt: x => `${2 ** x}` }, x => { s.level = x; update(); });
    L.slider('quadtree leaf capacity', { min: 4, max: 40, step: 1, value: s.cap }, x => { s.cap = x; update(); });
    L.drag(c, {
      hit: (x, y) => v && Math.hypot(v.sx(s.q[0]) - x, v.sy(s.q[1]) - y) < 18 ? 'q' : null,
      move: (_, x, y) => { s.q = [clamp(v.ix(x), 0, 1), clamp(v.iy(y), 0, 1)]; update(); },
      down: (x, y) => { if (!v) return; s.q = [clamp(v.ix(x), 0, 1), clamp(v.iy(y), 0, 1)]; update(); },
    });
    const build = (x0, y0, x1, y1, list, d) => {
      if (list.length <= s.cap || d > 8) return { x0, y0, x1, y1, list };
      const mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
      return { x0, y0, x1, y1, kids: [
        build(x0, y0, mx, my, list.filter(p => p[0] < mx && p[1] < my), d + 1), build(mx, y0, x1, my, list.filter(p => p[0] >= mx && p[1] < my), d + 1),
        build(x0, my, mx, y1, list.filter(p => p[0] < mx && p[1] >= my), d + 1), build(mx, my, x1, y1, list.filter(p => p[0] >= mx && p[1] >= my), d + 1)] };
    };
    const within = p => Math.hypot(p[0] - s.q[0], p[1] - s.q[1]) <= s.rad;
    function query() {
      if (s.mode === 'brute') return { scanned: pts, cells: [], visited: 0 };
      if (s.mode === 'grid') {
        const n = 2 ** s.level, cx0 = clamp(Math.floor((s.q[0] - s.rad) * n), 0, n - 1), cx1 = clamp(Math.floor((s.q[0] + s.rad) * n), 0, n - 1);
        const cy0 = clamp(Math.floor((s.q[1] - s.rad) * n), 0, n - 1), cy1 = clamp(Math.floor((s.q[1] + s.rad) * n), 0, n - 1);
        const cells = []; for (let i = cx0; i <= cx1; i++) for (let j = cy0; j <= cy1; j++) cells.push([i / n, j / n, 1 / n]);
        return { scanned: pts.filter(p => Math.floor(p[0] * n) >= cx0 && Math.floor(p[0] * n) <= cx1 && Math.floor(p[1] * n) >= cy0 && Math.floor(p[1] * n) <= cy1), cells, visited: cells.length };
      }
      const root = build(0, 0, 1, 1, pts, 0), scanned = [], leaves = [], all = [];
      let visited = 0;
      const walk = nd => {
        all.push(nd);
        const dx = Math.max(nd.x0 - s.q[0], 0, s.q[0] - nd.x1), dy = Math.max(nd.y0 - s.q[1], 0, s.q[1] - nd.y1);
        if (Math.hypot(dx, dy) > s.rad) return;
        visited++;
        if (nd.kids) nd.kids.forEach(walk); else { leaves.push(nd); scanned.push(...nd.list); }
      };
      walk(root);
      const every = []; const collect = nd => { every.push(nd); nd.kids?.forEach(collect); }; collect(root);
      return { scanned, leaves, every, visited };
    }
    let res = null;
    function update() {
      res = query();
      const matches = res.scanned.filter(within).length;
      L.stats([['drivers in radius', matches, 'accent'], ['drivers scanned', `${res.scanned.length} of ${pts.length}`, res.scanned.length > 150 ? 'err' : 'ok'], s.mode === 'grid' ? ['cells looked up', res.cells.length] : s.mode === 'quad' ? ['tree nodes visited', res.visited] : null]);
      L.insight(s.mode === 'brute' ? '<b>Scanning every driver</b> is fine for a few hundred, but with millions of location updates per second you need an index keyed by space.'
        : s.mode === 'grid' ? `<b>A geohash turns a location into a string prefix</b>, so nearby points share a prefix and live in the same key range. The catch is boundaries: a nearby driver can sit in the next cell, so you query every cell the circle touches. ${2 ** s.level > 30 ? 'Very fine cells mean many lookups.' : 2 ** s.level < 6 ? 'Very coarse cells mean scanning too many drivers.' : ''}`
        : '<b>A quadtree splits only where drivers are dense</b>, so downtown gets tiny cells and the countryside stays coarse. Google’s S2 library uses a similar hierarchy of cells on a sphere.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      v = D.view(c, { x0: 0, x1: 1, y0: 0, y1: 1, pad: 8, equal: true });
      ctx.fillStyle = P.alpha('faint', .05); ctx.fillRect(v.sx(0), v.sy(1), v.sx(1) - v.sx(0), v.sy(0) - v.sy(1));
      if (s.mode === 'grid') {
        const n = 2 ** s.level;
        for (let i = 0; i <= n; i++) { D.line(ctx, v.sx(i / n), v.sy(0), v.sx(i / n), v.sy(1), P.soft, 1); D.line(ctx, v.sx(0), v.sy(i / n), v.sx(1), v.sy(i / n), P.soft, 1); }
        res.cells.forEach(([x, y, w]) => { ctx.fillStyle = P.alpha('accent', .14); ctx.fillRect(v.sx(x), v.sy(y + w), v.sx(w) - v.sx(0), v.sy(0) - v.sy(w)); });
      } else if (s.mode === 'quad') {
        res.every.forEach(nd => { if (!nd.kids) { ctx.strokeStyle = P.soft; ctx.lineWidth = 1; ctx.strokeRect(v.sx(nd.x0), v.sy(nd.y1), v.sx(nd.x1) - v.sx(nd.x0), v.sy(nd.y0) - v.sy(nd.y1)); } });
        res.leaves.forEach(nd => { ctx.fillStyle = P.alpha('accent', .14); ctx.fillRect(v.sx(nd.x0), v.sy(nd.y1), v.sx(nd.x1) - v.sx(nd.x0), v.sy(nd.y0) - v.sy(nd.y1)); });
      }
      const scanned = new Set(res.scanned);
      pts.forEach(p => D.dot(ctx, v.sx(p[0]), v.sy(p[1]), 2.6, within(p) ? P.accent : scanned.has(p) && s.mode !== 'brute' ? P.series[0] : P.alpha('faint', .55)));
      ctx.beginPath(); ctx.arc(v.sx(s.q[0]), v.sy(s.q[1]), s.rad * v.kx, 0, TAU); ctx.strokeStyle = P.text; ctx.lineWidth = 1.6; ctx.setLineDash([5, 4]); ctx.stroke(); ctx.setLineDash([]);
      D.dot(ctx, v.sx(s.q[0]), v.sy(s.q[1]), 8, P.surface, P.text, 2.5);
      D.dot(ctx, v.sx(s.q[0]), v.sy(s.q[1]), 3, P.text);
    };
    update();
  },
});

/* ================================================= 15 · feed fan-out == */
defineLab('sd-fanout', {
  title: 'News feed fan-out: push, pull, or hybrid',
  hint: 'Post as a normal user and as a celebrity, then open a follower’s feed. Compare write cost, delivery delay, and read cost.',
  mount(L) {
    const s = { strat: 'hybrid', wave: -1, waveKind: null, reads: null, last: null, openT: -1 };
    const c = L.canvas(w => Math.min(330, w * .5));
    const T = topo(c);
    T.node('normal', .1, .28, 'Normal user', { sub: '300 followers', w: 104 });
    T.node('celeb', .1, .72, 'Celebrity', { sub: '50M followers', w: 104 });
    T.node('workers', .36, .5, 'Fan-out workers', { kind: 'queue', w: 110 });
    T.node('posts', .36, .14, 'Post store', { kind: 'db', w: 90, h: 44 });
    [['normal', 'workers'], ['celeb', 'workers'], ['normal', 'posts'], ['celeb', 'posts']].forEach(([a, b]) => T.edge(a, b, { dash: [4, 4] }));
    L.seg('strategy', [['push', 'Push (fan-out on write)'], ['pull', 'Pull (fan-out on read)'], ['hybrid', 'Hybrid']], s.strat, v => { s.strat = v; s.last = null; s.reads = null; update(); });
    const run = L.loop(dt => { T.step(dt); if (s.wave >= 0) s.wave += dt / (s.waveKind === 'celeb' ? 4 : 1); if (s.openT >= 0) s.openT += dt; L.redraw(); if (!T.busy() && (s.wave < 0 || s.wave > 1.05) && (s.openT < 0 || s.openT > 1.2)) return false; });
    const post = kind => {
      const followers = kind === 'celeb' ? 5e7 : 300, push = s.strat === 'push' || (s.strat === 'hybrid' && kind === 'normal');
      T.send([kind, 'posts'], { speed: 2.5, color: L.P.series[4] });
      if (push) {
        T.send([kind, 'workers'], { speed: 2.5, color: L.P.accent, end: () => { s.wave = 0; s.waveKind = kind; } });
        s.last = { kind, writes: followers, lag: followers / 1e5, push: true };
      } else s.last = { kind, writes: 1, lag: 0, push: false };
      T.nodes.workers.load = push && kind === 'celeb' ? 1 : push ? .2 : 0;
      update(); run.start();
    };
    L.button('Normal user posts', () => post('normal'), 'primary');
    L.button('Celebrity posts', () => post('celeb'), 'primary');
    L.button('A follower opens their feed', () => {
      const pullFrom = s.strat === 'push' ? 0 : s.strat === 'pull' ? 300 : 3;
      s.reads = { queries: 1 + pullFrom, ms: s.strat === 'push' ? 8 : s.strat === 'pull' ? 180 : 25 };
      s.openT = 0; update(); run.start();
    });
    function update() {
      const l = s.last, rd = s.reads;
      L.stats([l && ['feed writes for that post', fmtBig(l.writes), l.writes > 1e6 ? 'err' : 'accent'], l && ['time until every follower has it', l.push ? (l.lag < 1 ? 'instant' : `≈ ${Math.round(l.lag / 60)} min`) : 'on next read', l.lag > 60 ? 'err' : 'ok'], rd && ['queries to open a feed', rd.queries, rd.queries > 50 ? 'err' : 'ok'], rd && ['feed load time', `≈ ${rd.ms} ms`]]);
      L.insight(!l && !rd ? '<b>Pick a strategy and post.</b> Each tile on the right is a slice of that user’s followers’ feeds.'
        : l && l.push && l.kind === 'celeb' ? '<b>Pushing a celebrity post means 50 million feed writes.</b> At 100k writes/s the workers need about 8 minutes, and every other post queues behind it. This is the fan-out storm.'
        : rd && s.strat === 'pull' ? '<b>Pull keeps writes to one, but every feed open merges the recent posts of all 300 followed accounts</b>, which is slow and expensive at a million feed reads per second.'
        : s.strat === 'hybrid' ? '<b>Hybrid: push for normal accounts, pull only for the few celebrities you follow.</b> Writes stay bounded and reads merge just a handful of extra timelines. This is how large social feeds are usually built.'
        : '<b>Push precomputes feeds</b>, so reading is a single lookup. It works well until a single account has millions of followers.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      T.draw(ctx, P);
      const gx = c.w * .55, cols = 10, rows = 6, cw = (c.w - gx - 14) / cols, chh = (c.h - 40) / rows;
      D.text(ctx, s.last?.kind === 'celeb' && s.last.push ? 'follower feeds (each tile ≈ 1M followers)' : 'follower feeds', gx, 12, { color: P.dim, size: 11 });
      for (let i = 0; i < cols * rows; i++) {
        const x = gx + (i % cols) * cw, y = 24 + Math.floor(i / rows / (cols / rows)) * 0 + Math.floor(i / cols) * chh;
        const reached = s.wave >= 0 && i / (cols * rows) <= s.wave;
        ctx.fillStyle = reached ? P.alpha('accent', .75) : P.surface2;
        D.rrect(ctx, x + 2, y + 2, cw - 4, chh - 4, 4); ctx.fill();
        if (i === 0) { ctx.strokeStyle = P.text; ctx.lineWidth = 2; ctx.stroke(); D.text(ctx, 'you', x + cw / 2, y + chh / 2, { color: reached ? P.surface : P.text, size: 10, align: 'center', weight: 700 }); }
      }
      if (s.openT >= 0 && s.openT < 1.2) {
        const n = s.strat === 'push' ? 1 : s.strat === 'pull' ? 14 : 3, tx = gx + cw / 2, ty = 24 + chh / 2;
        for (let k = 0; k < n; k++) {
          const sx = s.strat === 'push' ? tx + 30 : c.w * .36, sy = s.strat === 'push' ? ty + 20 : c.h * (.14 + .06 * k);
          const t = clamp(s.openT - k * .04, 0, 1);
          D.dot(ctx, lerp(sx, tx, t), lerp(sy, ty, t), 4, P.series[0]);
        }
      }
    };
    update();
  },
});

/* ================================================== 16 · Snowflake IDs == */
defineLab('sd-snowflake', {
  title: 'Snowflake IDs: 64 bits, no coordination',
  hint: 'Generate IDs and watch the bits. Timestamp first makes IDs sortable by time; worker bits make them unique without a central counter.',
  mount(L) {
    const EPOCH = 1577836800000n;
    const s = { dc: 3, worker: 17, seq: 0, lastTs: -1, now: Date.now(), ids: [], note: '', back: false, waits: 0 };
    const c = L.canvas(w => Math.min(260, Math.max(230, w * .36)));
    L.slider('datacenter ID (5 bits)', { min: 0, max: 31, step: 1, value: s.dc }, v => { s.dc = v; });
    L.slider('worker ID (5 bits)', { min: 0, max: 31, step: 1, value: s.worker }, v => { s.worker = v; });
    const tick = L.loop(dt => { s.now += dt * 1000; });
    tick.start();
    L.button('Generate an ID', () => { gen(); update(); }, 'primary');
    L.button('Burst 5,000 in one millisecond', () => { const t0 = Math.floor(s.now); s.waits = 0; for (let i = 0; i < 5000; i++) gen(t0 + s.waits); s.note = `5,000 IDs requested in 1 ms. The 12-bit sequence holds 4,096 per millisecond, so the generator waited ${s.waits} ms for the clock to tick.`; update(); });
    L.button('Clock jumps back 5 ms (NTP correction)', () => { s.back = true; gen(); update(); });
    const b62 = n => { const a = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'; let out = ''; n = BigInt(n); if (n === 0n) return '0'; while (n > 0n) { out = a[Number(n % 62n)] + out; n /= 62n; } return out; };
    function gen(forceTs) {
      let ts = BigInt(Math.floor(forceTs ?? s.now)) - EPOCH;
      if (s.back) { ts -= 5n; s.back = false; }
      if (s.lastTs >= 0 && ts < BigInt(s.lastTs)) { s.note = `Clock moved backwards by ${BigInt(s.lastTs) - ts} ms. Issuing IDs now could duplicate earlier ones, so the generator refuses until the clock catches up.`; return null; }
      if (Number(ts) === s.lastTs) {
        s.seq = (s.seq + 1) & 4095;
        if (s.seq === 0) { ts = BigInt(s.lastTs + 1); s.waits++; }
      } else s.seq = 0;
      s.lastTs = Number(ts);
      const id = (ts << 22n) | (BigInt(s.dc) << 17n) | (BigInt(s.worker) << 12n) | BigInt(s.seq);
      s.ids.unshift(id); if (s.ids.length > 5) s.ids.pop();
      if (forceTs == null) s.note = 'Timestamp (41 bits) · datacenter (5) · worker (5) · sequence (12).';
      return id;
    }
    function update() {
      const id = s.ids[0];
      L.stats([id != null && ['ID', id.toString(), 'accent'], id != null && ['base62 (URL short code)', b62(id)], ['per worker', '4,096 IDs/ms'], ['timestamp lasts', '69 years']]);
      L.insight(`<b>${s.note || 'Press Generate.'}</b> ${s.ids.length > 1 ? 'Newer IDs are always larger, so they sort by creation time and keep B-tree inserts at the right edge of the index.' : ''}`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, id = s.ids[0] ?? 0n, cell = (c.w - 24) / 64;
      const bits = id.toString(2).padStart(64, '0');
      const segs = [[0, 1, 'sign', P.faint], [1, 42, 'timestamp · ms since 2020-01-01', P.accent], [42, 47, 'datacenter', P.series[0]], [47, 52, 'worker', P.series[1]], [52, 64, 'sequence', P.series[2]]];
      segs.forEach(([a, b, label, col]) => {
        for (let i = a; i < b; i++) {
          ctx.fillStyle = bits[i] === '1' ? col : P.alpha(col, .15);
          ctx.fillRect(12 + i * cell + .5, 34, cell - 1, 26);
        }
        D.text(ctx, label, 12 + ((a + b) / 2) * cell, 22, { color: col, size: b - a > 6 ? 10.5 : 9, align: 'center', weight: 650 });
        const val = BigInt(`0b${bits.slice(a, b)}`);
        const shown = label.startsWith('timestamp') ? new Date(Number(val + EPOCH)).toISOString().replace('T', ' ').slice(0, 23) : val.toString();
        if (b - a > 1) D.text(ctx, shown, 12 + ((a + b) / 2) * cell, 74, { color: P.text, size: 10.5, align: 'center', mono: true });
      });
      D.text(ctx, 'recent IDs (newest first, always increasing)', 12, 104, { color: P.dim, size: 11 });
      s.ids.forEach((x, i) => D.text(ctx, `${x.toString().padEnd(20)}  ${b62(x)}`, 12, 126 + i * 19, { color: i ? P.dim : P.text, size: 11.5, mono: true }));
    };
    update();
  },
});

/* ================================================ 17 · estimation lab == */
defineLab('sd-estimate', {
  title: 'Back-of-envelope estimator',
  hint: 'Move the inputs or pick a preset. The cards say which number actually shapes the design.',
  mount(L) {
    const PRE = {
      url: { label: 'URL shortener', dau: 1e8, w: .1, rd: 10, size: 500, years: 5, rf: 3, peak: 3, per: 5000 },
      photo: { label: 'Photo sharing', dau: 5e8, w: .2, rd: 30, size: 2e6, years: 10, rf: 3, peak: 3, per: 1000 },
      chat: { label: 'Chat', dau: 1e9, w: 40, rd: 40, size: 1000, years: 3, rf: 3, peak: 4, per: 5000 },
      feed: { label: 'News feed', dau: 5e8, w: .5, rd: 20, size: 2000, years: 5, rf: 3, peak: 3, per: 2000 },
    };
    const s = { ...PRE.photo };
    const box = document.createElement('div');
    box.className = 'est-box';
    L.stage.append(box);
    const sl = {};
    L.seg('preset', Object.entries(PRE).map(([k, p]) => [k, p.label]), 'photo', k => { Object.assign(s, PRE[k]); Object.keys(sl).forEach(key => sl[key].set(s[key], true)); render(); });
    sl.dau = L.slider('daily active users', { min: 1e5, max: 3e9, log: true, value: s.dau, fmt: fmtBig }, v => { s.dau = v; render(); });
    sl.w = L.slider('writes per user per day', { min: .01, max: 100, log: true, value: s.w, fmt: v => +v.toPrecision(2) }, v => { s.w = v; render(); });
    sl.rd = L.slider('reads per user per day', { min: .1, max: 1000, log: true, value: s.rd, fmt: v => +v.toPrecision(2) }, v => { s.rd = v; render(); });
    sl.size = L.slider('size of one record / object', { min: 100, max: 5e7, log: true, value: s.size, fmt: fmtBytes }, v => { s.size = v; render(); });
    sl.years = L.slider('retention (years)', { min: 1, max: 10, step: 1, value: s.years }, v => { s.years = v; render(); });
    sl.rf = L.slider('replication factor', { min: 1, max: 5, step: 1, value: s.rf }, v => { s.rf = v; render(); });
    sl.peak = L.slider('peak ÷ average', { min: 1, max: 10, step: .5, value: s.peak, fmt: v => `${v}×` }, v => { s.peak = v; render(); });
    sl.per = L.slider('requests/s one app server handles', { min: 100, max: 50000, log: true, value: s.per, fmt: fmtBig }, v => { s.per = v; render(); });
    function render() {
      const wq = s.dau * s.w / 86400, rq = s.dau * s.rd / 86400;
      const perDay = s.dau * s.w * s.size, total = perDay * 365 * s.years * s.rf;
      const ingress = wq * s.size * 8, egress = rq * s.size * 8;
      const cache = s.dau * s.rd * .2 * Math.min(s.size, 1e5);
      const servers = Math.ceil((wq + rq) * s.peak / s.per);
      const card = (label, value, note, cls = '') => `<div class="est-card ${cls}"><span>${label}</span><b>${value}</b><p>${note}</p></div>`;
      box.innerHTML = `
        <div class="est-grid">
          ${card('write QPS', `${fmtQps(wq)} <small>peak ${fmtQps(wq * s.peak)}</small>`, wq * s.peak > 10000 ? 'Beyond one relational primary. Plan for sharding or a write-optimised store.' : wq * s.peak > 2000 ? 'One well-tuned primary can take this. Keep a sharding plan ready.' : 'A single primary database is plenty.', wq * s.peak > 10000 ? 'hot' : '')}
          ${card('read QPS', `${fmtQps(rq)} <small>peak ${fmtQps(rq * s.peak)}</small>`, rq / Math.max(wq, 1e-9) > 10 ? `Read-heavy (${Math.round(rq / Math.max(wq, 1e-9))}:1). Caching and read replicas pay off.` : 'Balanced read/write: caching helps less.', rq * s.peak > 1e5 ? 'hot' : '')}
          ${card('new data per day', fmtBytes(perDay), perDay > 1e12 ? 'Terabytes a day: object storage plus tiering, not a database column.' : 'Fits comfortably in a database.')}
          ${card(`total storage (${s.years}y × ${s.rf} copies)`, fmtBytes(total), total > 1e15 ? 'Petabyte scale: blob store, lifecycle tiers, and erasure coding instead of triple replication.' : total > 1e13 ? 'Tens of terabytes or more: shard it.' : 'Manageable on a few machines.', total > 1e15 ? 'hot' : '')}
          ${card('bandwidth out', fmtBits(egress), egress > 1e10 ? 'Tens of Gbps: serve through a CDN.' : 'A handful of servers can push this.', egress > 1e10 ? 'hot' : '')}
          ${card('bandwidth in', fmtBits(ingress), ingress > 1e9 ? 'Big uploads: presigned direct-to-storage uploads.' : 'Uploads go through the API without trouble.')}
          ${card('cache for hot 20% of daily reads', fmtBytes(cache), cache > 1e12 ? 'More than a small cache cluster: cache IDs and metadata, not whole objects.' : 'A modest Redis or Memcached cluster.')}
          ${card('app servers at peak', `${servers}`, `${fmtQps((wq + rq) * s.peak)} ÷ ${fmtBig(s.per)} per server, before redundancy and headroom.`)}
        </div>
        <div class="est-cheat"><span>1 day ≈ 86,400 s ≈ 10⁵ s</span><span>1M requests/day ≈ 12/s</span><span>1B/day ≈ 12K/s</span><span>2¹⁰ ≈ 1 thousand · 2²⁰ ≈ 1 million · 2³⁰ ≈ 1 billion</span></div>`;
      L.stats([]);
      L.insight('<b>Estimate to make a decision, not to be precise.</b> Round aggressively, say each assumption out loud, and name the one number that forces an architectural choice: usually peak write QPS, total storage, or egress bandwidth.');
    }
    render();
  },
});

/* =========================================== 18 · tail latency at scale == */
defineLab('sd-tail', {
  title: 'Tail latency: why fan-out makes p99 your p50',
  hint: 'A search query fans out to N leaf servers and waits for all of them. Each leaf is slow 1% of the time.',
  mount(L) {
    const s = { n: 50, slow: 1, hedge: false };
    const c = L.canvas(w => Math.min(300, w * .46));
    L.slider('leaf servers per request', { min: 1, max: 200, step: 1, value: s.n }, v => { s.n = v; compute(); });
    L.slider('chance one leaf is slow', { min: .1, max: 5, step: .1, value: s.slow, fmt: v => `${v}%` }, v => { s.slow = v; compute(); });
    L.toggle('Hedged requests (send a backup after 20 ms)', s.hedge, v => { s.hedge = v; compute(); });
    let sim = null;
    function compute() {
      const r = rng(71), p = s.slow / 100, lat = () => r() < p ? 150 + r() * 850 : 4 + Math.abs(gauss(r)) * 3 + r() * 4;
      const out = [];
      for (let q = 0; q < 2500; q++) {
        let worst = 0;
        for (let i = 0; i < s.n; i++) { let t = lat(); if (s.hedge && t > 20) t = Math.min(t, 20 + lat()); worst = Math.max(worst, t); }
        out.push(worst + 2);
      }
      const pSlow = 1 - (1 - p) ** s.n;
      sim = { out, p50: pctl(out, .5), p99: pctl(out, .99), pSlow };
      L.stats([['p50', fmtMs(sim.p50), sim.p50 > 100 ? 'err' : 'ok'], ['p99', fmtMs(sim.p99), sim.p99 > 200 ? 'err' : 'accent'], ['requests hitting a slow leaf', `${(pSlow * 100).toFixed(0)}%`, pSlow > .3 ? 'err' : '']]);
      L.insight(s.hedge ? '<b>Hedging:</b> if a leaf has not answered by its p95, send the same request to another replica and take whichever answers first. It costs about 5% extra load and removes most of the tail. Google’s “The Tail at Scale” describes this.'
        : s.n >= 50 ? `<b>With ${s.n} leaves, ${(pSlow * 100).toFixed(0)}% of queries touch at least one slow server</b>, so a 1-in-100 event on a single machine becomes the typical experience. At fan-out, per-server p99 decides end-to-end p50.`
        : '<b>With few leaves the rare slow server stays rare.</b> Raise the fan-out and watch the whole distribution shift right.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, lo = Math.log10(2), hi = Math.log10(2000), bins = 40, counts = new Array(bins).fill(0);
      sim.out.forEach(x => { const i = Math.floor((Math.log10(x) - lo) / (hi - lo) * bins); counts[clamp(i, 0, bins - 1)]++; });
      const w = c.w * .62, v = D.view({ w, h: c.h }, { x0: lo, x1: hi, y0: 0, y1: Math.max(...counts) * 1.1, pad: 12, padL: 16, padB: 26 });
      D.axes(ctx, v, P, { xTicks: [1, 2, 3].map(Math.log10).concat([Math.log10(10), Math.log10(100), Math.log10(1000)]).filter((x, i, a) => a.indexOf(x) === i && x >= lo), fmtX: x => fmtMs(10 ** x), xLabel: 'end-to-end latency (log scale)' });
      counts.forEach((k, i) => { const x = lerp(lo, hi, i / bins); ctx.fillStyle = 10 ** x > 100 ? P.err : P.accent; ctx.fillRect(v.sx(x) + .5, v.sy(k), v.sx(lerp(lo, hi, 1 / bins)) - v.sx(0) - 1, v.sy(0) - v.sy(k)); });
      [[sim.p50, 'p50'], [sim.p99, 'p99']].forEach(([val, lb]) => { const x = v.sx(clamp(Math.log10(val), lo, hi)); D.line(ctx, x, v.sy(v.y1), x, v.sy(0), P.text, 1.4, [4, 3]); D.text(ctx, lb, x + 4, v.sy(v.y1) + 8, { color: P.text, size: 10.5, weight: 700 }); });
      const v2 = D.view({ w: c.w - w - 10, h: c.h }, { x0: 1, x1: 200, y0: 0, y1: 1, pad: 12, padL: 34, padB: 26 });
      ctx.save(); ctx.translate(w + 10, 0);
      D.axes(ctx, v2, P, { xTicks: [1, 100, 200], yTicks: [0, .5, 1], fmtY: t => `${t * 100}%`, xLabel: 'fan-out' });
      D.curve(ctx, v2, n => 1 - (1 - s.slow / 100) ** n, P.series[0], 2.2);
      D.dot(ctx, v2.sx(s.n), v2.sy(sim.pSlow), 5, P.series[0], P.surface, 2);
      D.text(ctx, 'P(any slow leaf)', v2.sx(1) + 4, v2.sy(1) + 10, { color: P.series[0], size: 10.5 });
      ctx.restore();
    };
    compute();
  },
});

/* ==================================== 19 · collaborative editing (OT/CRDT) == */
defineLab('sd-collab', {
  title: 'Two people edit the same document at once',
  hint: 'Both edits happen at the same moment, then cross on the network. Naive index-based apply diverges; OT and CRDTs converge.',
  mount(L) {
    const s = { mode: 'ot', scen: 'insdel', t: 4.2 };
    const c = L.canvas(w => Math.min(320, w * .5));
    L.seg('merge strategy', [['naive', 'Apply as-is'], ['ot', 'Operational transform'], ['crdt', 'CRDT (unique IDs)']], s.mode, v => { s.mode = v; s.t = 4.2; update(); });
    L.seg('scenario', [['insdel', 'Insert vs delete'], ['insins', 'Both insert at the same spot']], s.scen, v => { s.scen = v; s.t = 4.2; update(); });
    const play = L.loop(dt => { s.t += dt; update(); if (s.t > 4.2) return false; });
    L.playButton(play, ['Replay', 'Pause'], () => { s.t = 0; });
    const base = 'CAT';
    const ops = () => s.scen === 'insdel'
      ? { a: { type: 'ins', pos: 1, ch: 'H', site: 'A' }, b: { type: 'del', pos: 2, site: 'B' } }
      : { a: { type: 'ins', pos: 1, ch: 'X', site: 'A' }, b: { type: 'ins', pos: 1, ch: 'Y', site: 'B' } };
    const apply = (doc, op) => op.type === 'noop' ? doc : op.type === 'ins' ? doc.slice(0, op.pos) + op.ch + doc.slice(op.pos) : doc.slice(0, op.pos) + doc.slice(op.pos + 1);
    const xform = (op, against) => {
      const o = { ...op };
      if (op.type === 'ins' && against.type === 'ins') { if (against.pos < op.pos || (against.pos === op.pos && against.site < op.site)) o.pos++; }
      else if (op.type === 'ins' && against.type === 'del') { if (against.pos < op.pos) o.pos--; }
      else if (op.type === 'del' && against.type === 'ins') { if (against.pos <= op.pos) o.pos++; }
      else if (op.type === 'del' && against.type === 'del') { if (against.pos < op.pos) o.pos--; else if (against.pos === op.pos) o.type = 'noop'; }
      return o;
    };
    const crdt = () => {
      const mk = () => base.split('').map((ch, i) => ({ ch, id: `o${i + 1}`, dead: false }));
      const { a, b } = ops();
      const toCrdt = (doc, op) => op.type === 'ins' ? { type: 'ins', after: doc.filter(x => !x.dead)[op.pos - 1].id, id: `${op.site}1`, ch: op.ch } : { type: 'del', id: doc.filter(x => !x.dead)[op.pos].id };
      const applyC = (doc, op) => {
        if (op.type === 'del') { doc.find(x => x.id === op.id).dead = true; return; }
        let i = doc.findIndex(x => x.id === op.after) + 1;
        while (i < doc.length && doc[i].id > op.id && doc[i].id[0] !== 'o') i++;
        doc.splice(i, 0, { ch: op.ch, id: op.id, dead: false });
      };
      const A = mk(), B = mk(), ca = toCrdt(A, a), cb = toCrdt(B, b);
      applyC(A, ca); applyC(B, cb); const midA = A.map(x => ({ ...x })), midB = B.map(x => ({ ...x }));
      applyC(A, cb); applyC(B, ca);
      return { A, B, midA, midB, ca, cb };
    };
    const describe = op => op.type === 'noop' ? 'no-op' : op.type === 'ins' ? `insert “${op.ch}” at ${op.pos}` : `delete at ${op.pos}`;
    function result() {
      const { a, b } = ops();
      const midA = apply(base, a), midB = apply(base, b);
      if (s.mode === 'crdt') { const r = crdt(); const txt = d => d.filter(x => !x.dead).map(x => x.ch).join(''); return { midA, midB, finA: txt(r.A), finB: txt(r.B), recvA: `${r.cb.type} ${r.cb.type === 'ins' ? `“${r.cb.ch}” after ${r.cb.after}` : r.cb.id}`, recvB: `${r.ca.type} ${r.ca.type === 'ins' ? `“${r.ca.ch}” after ${r.ca.after}` : r.ca.id}`, sentA: describe(a), sentB: describe(b), crdtA: r.A, crdtB: r.B }; }
      const inA = s.mode === 'ot' ? xform(b, a) : b, inB = s.mode === 'ot' ? xform(a, b) : a;
      return { midA, midB, finA: apply(midA, inA), finB: apply(midB, inB), recvA: describe(inA), recvB: describe(inB), sentA: describe(a), sentB: describe(b) };
    }
    function update() {
      const res = result(), same = res.finA === res.finB;
      L.stats([['Alice sees', `“${res.finA}”`, same ? 'ok' : 'err'], ['Bob sees', `“${res.finB}”`, same ? 'ok' : 'err'], ['converged', same ? 'yes' : 'no', same ? 'ok' : 'err']]);
      L.insight(s.mode === 'naive' ? `<b>Indexes are relative to the document the sender saw.</b> By the time the op arrives, the other person’s edit has shifted every position, so the same op hits a different character. The two copies diverge permanently.`
        : s.mode === 'ot' ? `<b>Operational transformation rewrites each incoming op against the concurrent local op</b>: an insert before your position shifts it right; two inserts at the same spot are ordered by a site tie-break. Google Docs uses OT with a central server that fixes the order.`
        : '<b>A CRDT gives every character a permanent unique ID</b> and edits refer to IDs, not indexes (“insert after o1”, “delete o3”). Concurrent inserts are ordered by ID, so any delivery order produces the same result without a central server. That makes CRDTs good for offline-first and peer-to-peer apps.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, res = result(), t = s.t;
      const panelW = c.w * .34, ax = 12, bx = c.w - panelW - 12, top = 28;
      const doc = (x, y, text, title, col, hi) => {
        D.text(ctx, title, x, y - 12, { color: col, size: 11.5, weight: 700 });
        ctx.fillStyle = P.surface2; D.rrect(ctx, x, y, panelW, 44, 10); ctx.fill(); ctx.strokeStyle = col; ctx.lineWidth = 1.5; ctx.stroke();
        text.split('').forEach((ch, i) => {
          const cx = x + 12 + i * 28;
          ctx.fillStyle = hi && hi.includes(i) ? P.alpha(col, .35) : P.surface; D.rrect(ctx, cx, y + 8, 24, 28, 5); ctx.fill();
          D.text(ctx, ch, cx + 12, y + 22, { color: P.text, size: 15, align: 'center', mono: true, weight: 700 });
        });
      };
      const phase = t < 1 ? 0 : t < 2.6 ? 1 : t < 3.6 ? 2 : 3;
      const aText = phase === 0 ? (t < .5 ? base : res.midA) : phase < 2 ? res.midA : res.finA;
      const bText = phase === 0 ? (t < .5 ? base : res.midB) : phase < 2 ? res.midB : res.finB;
      doc(ax, top, aText, 'Alice', P.series[0]);
      doc(bx, top, bText, 'Bob', P.series[1]);
      if (s.mode === 'crdt' && phase >= 2) {
        const ids = (arr, x) => arr.filter(z => !z.dead).forEach((z, i) => D.text(ctx, z.id, x + 24 + i * 28, top + 54, { color: P.faint, size: 9, align: 'center', mono: true }));
        const r = crdt(); ids(r.A, ax); ids(r.B, bx);
      }
      const sx = c.w / 2;
      ctx.fillStyle = P.surface2; D.rrect(ctx, sx - 50, top + 90, 100, 36, 9); ctx.fill(); ctx.strokeStyle = P.strong; ctx.stroke();
      D.text(ctx, s.mode === 'crdt' ? 'sync relay' : 'collab server', sx, top + 108, { color: P.dim, size: 11, align: 'center', weight: 650 });
      if (phase >= 1) {
        const k = clamp((t - 1) / 1.6, 0, 1);
        const pa = [lerp(ax + panelW / 2, bx + panelW / 2, k), top + 60 + Math.sin(k * Math.PI) * 60], pb = [lerp(bx + panelW / 2, ax + panelW / 2, k), top + 60 + Math.sin(k * Math.PI) * 60];
        if (phase === 1) {
          D.dot(ctx, pa[0], pa[1], 6, P.series[0]); D.text(ctx, res.sentA, pa[0], pa[1] - 14, { color: P.series[0], size: 10.5, align: 'center', mono: true, weight: 600 });
          D.dot(ctx, pb[0], pb[1] + 30, 6, P.series[1]); D.text(ctx, res.sentB, pb[0], pb[1] + 48, { color: P.series[1], size: 10.5, align: 'center', mono: true, weight: 600 });
        }
      }
      const y0 = top + 150;
      D.text(ctx, `Alice typed:  ${res.sentA}`, ax, y0, { color: P.series[0], size: 11.5, mono: true });
      D.text(ctx, `Bob typed:    ${res.sentB}`, ax, y0 + 20, { color: P.series[1], size: 11.5, mono: true });
      if (phase >= 2) {
        D.text(ctx, `Alice applies Bob’s op as:  ${res.recvA}`, ax, y0 + 48, { color: P.text, size: 11.5, mono: true });
        D.text(ctx, `Bob applies Alice’s op as:  ${res.recvB}`, ax, y0 + 68, { color: P.text, size: 11.5, mono: true });
      }
      if (phase >= 3) {
        const same = res.finA === res.finB;
        D.text(ctx, same ? `✓ Both documents read “${res.finA}”` : `✕ Diverged: “${res.finA}” vs “${res.finB}”`, ax, y0 + 100, { color: same ? P.ok : P.err, size: 14, weight: 700 });
      }
    };
    update();
  },
});

/* ==================================== 20 · stream processing windows == */
defineLab('sd-windows', {
  title: 'Event time, watermarks and late data',
  hint: 'Each dot is an ad click: x = when it reached the pipeline, y = when it actually happened. Windows fire when the watermark passes their end.',
  mount(L) {
    const r = rng(52);
    const events = [];
    [[2, 9, 16], [13, 20, 14], [31, 45, 22], [52, 58, 12]].forEach(([a, b, n]) => { for (let i = 0; i < n; i++) { const et = a + (b - a) * r(); events.push({ et, pt: et + -Math.log(1 - r()) * 2 + .3 }); } });
    [8.5, 17, 38, 41, 55].forEach(et => events.push({ et, pt: et + 14 + r() * 10 }));
    events.sort((a, b) => a.pt - b.pt);
    const s = { kind: 'tumbling', lag: 4, late: 0, gap: 5, reveal: 1 };
    const c = L.canvas(w => Math.min(360, w * .56));
    L.seg('window', [['tumbling', 'Tumbling 10 s'], ['sliding', 'Sliding 10 s every 5 s'], ['session', 'Session (gap)']], s.kind, v => { s.kind = v; update(); });
    L.slider('watermark lag', { min: 0, max: 15, step: .5, value: s.lag, fmt: v => `${v} s` }, v => { s.lag = v; update(); });
    L.slider('allowed lateness', { min: 0, max: 20, step: 1, value: s.late, fmt: v => `${v} s` }, v => { s.late = v; update(); });
    L.slider('session gap', { min: 2, max: 8, step: .5, value: s.gap, fmt: v => `${v} s` }, v => { s.gap = v; update(); });
    const play = L.loop(dt => { s.reveal = Math.min(1, s.reveal + dt / 7); update(); if (s.reveal >= 1) return false; });
    L.playButton(play, ['Replay the stream', 'Pause'], () => { if (s.reveal >= 1) s.reveal = 0; });
    const PT = 90;
    const wmAt = x => { let m = -Infinity; for (const e of events) { if (e.pt > x) break; m = Math.max(m, e.et); } return m - s.lag; };
    const windows = () => {
      if (s.kind === 'tumbling') return Array.from({ length: 7 }, (_, i) => [i * 10, i * 10 + 10]);
      if (s.kind === 'sliding') return Array.from({ length: 13 }, (_, i) => [i * 5, i * 5 + 10]);
      const ts = events.map(e => e.et).sort((a, b) => a - b), out = [];
      let st = ts[0], last = ts[0];
      ts.slice(1).forEach(t => { if (t - last > s.gap) { out.push([st, last + s.gap]); st = t; } last = t; });
      out.push([st, last + s.gap]);
      return out;
    };
    function evaluate() {
      const cut = s.reveal * PT, ws = windows().map(([a, b]) => ({ a, b, fireAt: null, count: 0, updated: 0 }));
      const cls = new Map();
      events.forEach(e => {
        if (e.pt > cut) return;
        const wmBefore = wmAt(e.pt - 1e-6);
        const mine = ws.filter(w => e.et >= w.a && e.et < w.b);
        const late = e.et < wmBefore;
        if (!late) { cls.set(e, 'on'); return; }
        const accepted = mine.some(w => wmBefore < w.b + s.late);
        cls.set(e, accepted ? 'late-ok' : 'dropped');
      });
      ws.forEach(w => {
        for (const e of events) { if (e.pt > cut) break; if (wmAt(e.pt) >= w.b) { w.fireAt = e.pt; break; } }
        if (w.fireAt == null) return;
        events.forEach(e => { if (e.pt > cut || e.et < w.a || e.et >= w.b) return; const k = cls.get(e); if (k === 'dropped') return; if (e.pt <= w.fireAt) w.count++; else if (k === 'late-ok') { w.count++; w.updated++; } });
      });
      return { ws, cls, cut };
    }
    let ev = null;
    function update() {
      ev = evaluate();
      const vals = [...ev.cls.values()], n = k => vals.filter(v => v === k).length;
      L.stats([['on time', n('on'), 'ok'], ['late but accepted', n('late-ok'), 'accent'], ['late and dropped', n('dropped'), n('dropped') ? 'err' : ''], ['windows fired', ev.ws.filter(w => w.fireAt != null).length]]);
      L.insight(s.lag < 1.5 ? '<b>An aggressive watermark fires windows early</b>, so results arrive fast, but many stragglers are treated as late. Raise the lag or allow lateness.'
        : s.lag > 10 ? '<b>A generous watermark catches almost everything</b>, but every result waits that long. Latency versus completeness is the core trade-off of stream processing.'
        : n('dropped') && !s.late ? '<b>Red events arrived after their window had already fired and closed.</b> Allowed lateness keeps window state around so they can still update the result, and you emit a correction.'
        : s.kind === 'session' ? '<b>Session windows have no fixed size.</b> A session stays open while events keep arriving within the gap, which is how user sessions or visits are measured.'
        : '<b>The watermark is the pipeline’s estimate that “no more events older than this will arrive”.</b> When it crosses a window’s end, the window emits its count.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, v = D.view(c, { x0: 0, x1: PT, y0: 0, y1: 70, pad: 14, padL: 40, padB: 28 });
      ev.ws.forEach((w, i) => {
        ctx.fillStyle = i % 2 ? P.alpha('faint', .05) : P.alpha('accent', .05);
        ctx.fillRect(v.sx(0), v.sy(Math.min(70, w.b)), v.sx(PT) - v.sx(0), v.sy(w.a) - v.sy(Math.min(70, w.b)));
        if (w.fireAt != null) {
          D.dot(ctx, v.sx(w.fireAt), v.sy(Math.min(69, w.b)), 4, P.series[4]);
          D.text(ctx, `${w.count}${w.updated ? ` (+${w.updated} late)` : ''}`, v.sx(w.fireAt) + 6, v.sy(Math.min(69, w.b)) + (s.kind === 'sliding' && i % 2 ? 8 : -6), { color: P.series[4], size: 10, mono: true, weight: 700 });
        }
      });
      D.axes(ctx, v, P, { xTicks: [0, 30, 60, 90], yTicks: [0, 20, 40, 60], xLabel: 'processing time (arrival) →', yLabel: 'event time' });
      D.line(ctx, v.sx(0), v.sy(0), v.sx(70), v.sy(70), P.soft, 1, [3, 4]);
      ctx.beginPath();
      let first = true;
      for (let x = 0; x <= ev.cut; x += .5) { const wm = wmAt(x); if (!Number.isFinite(wm)) continue; const y = v.sy(clamp(wm, 0, 70)); first ? ctx.moveTo(v.sx(x), y) : ctx.lineTo(v.sx(x), y); first = false; }
      ctx.strokeStyle = P.series[0]; ctx.lineWidth = 2.2; ctx.stroke();
      D.text(ctx, 'watermark', v.sx(Math.min(ev.cut, 80)), v.sy(clamp(wmAt(Math.min(ev.cut, 80)), 0, 70)) - 10, { color: P.series[0], size: 10.5, weight: 650, align: 'right' });
      events.forEach(e => {
        if (e.pt > ev.cut) return;
        const k = ev.cls.get(e);
        D.dot(ctx, v.sx(e.pt), v.sy(e.et), k === 'on' ? 3.2 : 4.5, k === 'on' ? P.accent : k === 'late-ok' ? P.series[1] : P.err);
      });
      if (ev.cut < PT) D.line(ctx, v.sx(ev.cut), v.sy(0), v.sx(ev.cut), v.sy(70), P.faint, 1, [3, 3]);
    };
    update();
  },
});

/* ============================================== 21 · 2PC vs saga == */
defineLab('sd-saga', {
  title: 'Distributed transactions: two-phase commit vs saga',
  hint: 'An order has to charge a card, reserve stock, and book shipping across three services. Inject a failure and watch each approach.',
  mount(L) {
    const c = L.canvas(w => Math.min(330, w * .5));
    const s = { mode: '2pc', fail: 'none', steps: [], i: 0, t: 0, state: {}, locks: {}, lockTime: 0, outcome: '', crashed: false };
    const T = topo(c);
    T.node('order', .16, .5, 'Order service', { sub: 'coordinator', w: 116, h: 50 });
    T.node('pay', .78, .18, 'Payments', { w: 104, h: 50 });
    T.node('inv', .78, .5, 'Inventory', { w: 104, h: 50 });
    T.node('ship', .78, .82, 'Shipping', { w: 104, h: 50 });
    ['pay', 'inv', 'ship'].forEach(n => T.edge('order', n, { dash: [4, 4] }));
    L.seg('approach', [['2pc', 'Two-phase commit'], ['saga', 'Saga (orchestrated)']], s.mode, v => { s.mode = v; build(); });
    L.seg('failure', [['none', 'No failure'], ['inv', 'Inventory is out of stock'], ['crash', 'Coordinator crashes midway']], s.fail, v => { s.fail = v; build(); });
    const run = L.loop(dt => { T.step(dt); s.t += dt; Object.keys(s.locks).forEach(k => { if (s.locks[k]) s.lockTime += dt; }); if (!T.busy() && s.t > .25) next(); update(); if (s.i >= s.steps.length && !T.busy()) return false; });
    L.playButton(run, ['Run the transaction', 'Pause'], () => { if (s.i >= s.steps.length) build(); });
    const P3 = ['pay', 'inv', 'ship'], NAME = { pay: 'Payments', inv: 'Inventory', ship: 'Shipping' };
    function build() {
      const st = [], msg = (from, to, label, color, fx) => st.push({ from, to, label, color, fx });
      const set = (n, text, lock) => () => { s.state[n] = text; if (lock !== undefined) s.locks[n] = lock; };
      if (s.mode === '2pc') {
        P3.forEach(n => msg('order', n, 'prepare', 'accent', set(n, 'prepared · rows locked', true)));
        P3.forEach(n => { const no = s.fail === 'inv' && n === 'inv'; msg(n, 'order', no ? 'vote NO' : 'vote YES', no ? 'err' : 'ok', set(n, no ? 'voted no' : 'prepared · rows locked', !no)); });
        if (s.fail === 'inv') { P3.filter(n => n !== 'inv').forEach(n => msg('order', n, 'abort', 'err', set(n, 'aborted', false))); st.push({ fx: () => { s.outcome = 'Aborted atomically: nothing was charged or reserved.'; } }); }
        else if (s.fail === 'crash') {
          st.push({ fx: () => { s.crashed = true; T.nodes.order.down = true; s.outcome = 'Coordinator crashed after collecting YES votes. Participants are stuck in doubt, holding locks.'; P3.forEach(n => { s.state[n] = 'in doubt · blocked'; }); }, wait: 4 });
          st.push({ fx: () => { s.crashed = false; T.nodes.order.down = false; s.outcome = 'Coordinator recovered, read its log, and finished the commit.'; } });
          P3.forEach(n => msg('order', n, 'commit', 'ok', set(n, 'committed', false)));
        } else { P3.forEach(n => msg('order', n, 'commit', 'ok', set(n, 'committed', false))); st.push({ fx: () => { s.outcome = 'Committed atomically across all three services.'; } }); }
      } else {
        const lbl = { pay: 'charge card', inv: 'reserve stock', ship: 'book courier' };
        for (const n of P3) {
          msg('order', n, lbl[n], 'accent', () => {});
          if (s.fail === 'inv' && n === 'inv') {
            msg(n, 'order', 'failed: out of stock', 'err', set(n, 'failed'));
            msg('order', 'pay', 'refund card', 'series1', set('pay', 'refunded (compensated)'));
            st.push({ fx: () => { s.outcome = 'Saga rolled back with a compensating refund. The customer briefly saw a charge that was then reversed.'; } });
            break;
          }
          msg(n, 'order', 'done', 'ok', set(n, n === 'pay' ? 'charged' : n === 'inv' ? 'reserved' : 'booked'));
          if (s.fail === 'crash' && n === 'pay') {
            st.push({ fx: () => { s.crashed = true; T.nodes.order.down = true; s.outcome = 'Orchestrator crashed. Its saga log says step 1 is done; no locks are held anywhere.'; }, wait: 2 });
            st.push({ fx: () => { s.crashed = false; T.nodes.order.down = false; s.outcome = 'Orchestrator restarted and resumed from the saga log at step 2.'; } });
          }
        }
        if (s.fail !== 'inv') st.push({ fx: () => { s.outcome = 'All local transactions committed. The order is confirmed.'; } });
      }
      Object.assign(s, { steps: st, i: 0, t: 0, state: { pay: 'idle', inv: 'idle', ship: 'idle' }, locks: {}, lockTime: 0, outcome: '', crashed: false });
      T.packets = []; T.nodes.order.down = false;
      update();
    }
    function next() {
      if (s.i >= s.steps.length) return;
      const st = s.steps[s.i++];
      s.t = 0;
      if (!st.from) { st.fx(); if (st.wait) s.t = -st.wait; return; }
      const col = st.color === 'series1' ? L.P.series[1] : L.P[st.color];
      T.send([st.from, st.to], { speed: 1.3, color: col, label: st.label, end: () => st.fx() });
    }
    function update() {
      P3.forEach(n => { T.nodes[n].sub = s.state[n]; T.nodes[n].badge = s.locks[n] ? '🔒 locked' : null; T.nodes[n].badgeColor = L.P.series[1]; T.nodes[n].subColor = /fail|doubt|no/.test(s.state[n]) ? L.P.err : /commit|charged|reserved|booked/.test(s.state[n]) ? L.P.ok : null; });
      L.stats([['outcome', s.outcome ? (/rolled|Aborted|blocked|stuck|in doubt/.test(s.outcome) ? 'rolled back / waiting' : 'in progress / done') : '—'], ['lock-seconds held', s.lockTime.toFixed(1), s.lockTime > 6 ? 'err' : 'accent']]);
      L.insight(`<b>${s.outcome || 'Press Run.'}</b> ${s.mode === '2pc' ? 'Two-phase commit gives true atomicity, but participants hold locks while waiting, and a crashed coordinator can block them indefinitely. It rarely crosses service or company boundaries.' : 'A saga is a sequence of local transactions, each with a compensating action. Nothing is locked across services, so it scales and survives crashes, but the intermediate states are visible and compensations must be designed carefully.'}`);
      L.redraw();
    }
    L.draw = P => { c.clear(); T.draw(c.ctx, P); };
    build();
  },
});

/* =================================== 22 · polling vs push transports == */
defineLab('sd-realtime', {
  title: 'Polling, long polling, SSE and WebSockets',
  hint: 'Sixty seconds of a chat thread. Server-side messages are the orange ticks; each lane shows when that transport actually delivers them.',
  mount(L) {
    const s = { rate: 6, poll: 5 };
    const c = L.canvas(w => Math.min(320, w * .5));
    L.slider('messages per minute', { min: 1, max: 30, step: 1, value: s.rate }, v => { s.rate = v; update(); });
    L.slider('short-poll interval', { min: 1, max: 20, step: 1, value: s.poll, fmt: v => `${v} s` }, v => { s.poll = v; update(); });
    let sim = null;
    function simulate() {
      const r = rng(s.rate * 7 + 1), msgs = [];
      let t = 0; while ((t += -Math.log(1 - r()) * 60 / s.rate) < 60) msgs.push(t);
      const HDR = 800;
      const short = { reqs: [], delays: [] };
      for (let x = 0; x < 60; x += s.poll) short.reqs.push([x, x + .15]);
      msgs.forEach(m => { const next = Math.ceil(m / s.poll) * s.poll; short.delays.push(next - m); });
      const long = { reqs: [], delays: [] };
      let open = 0, mi = 0;
      while (open < 60) {
        const m = msgs[mi];
        if (m != null && m - open < 30) { long.reqs.push([open, m + .05]); long.delays.push(.05); open = m + .1; mi++; }
        else { long.reqs.push([open, Math.min(60, open + 30)]); open += 30.1; }
      }
      return {
        msgs,
        rows: [
          { name: 'Short polling', reqs: short.reqs, delay: short.delays, requests: short.reqs.length, bytes: short.reqs.length * HDR * 2 },
          { name: 'Long polling', reqs: long.reqs, delay: long.delays, requests: long.reqs.length, bytes: long.reqs.length * HDR * 2 },
          { name: 'Server-sent events', reqs: [[0, 60]], delay: msgs.map(() => .02), requests: 1, bytes: HDR * 2 + msgs.length * 60 },
          { name: 'WebSocket', reqs: [[0, 60]], delay: msgs.map(() => .02), requests: 1, bytes: HDR * 2 + msgs.length * 10, duplex: true },
        ],
      };
    }
    function update() {
      sim = simulate();
      const avg = row => row.delay.length ? row.delay.reduce((a, b) => a + b, 0) / row.delay.length : 0;
      L.stats(sim.rows.map(row => [row.name, `${avg(row) < .1 ? 'instant' : `${avg(row).toFixed(1)} s`} · ${row.requests} req · ${fmtBytes(row.bytes)}`]));
      L.insight(s.rate < 3 ? '<b>Rare messages make short polling wasteful:</b> almost every request comes back empty, yet each one costs a full HTTP round trip with headers.'
        : '<b>Short polling trades delay for simplicity</b>: a message waits up to one interval. Long polling holds the request open until there is news, so delivery is instant, but every message costs a new request. SSE streams server-to-client over one connection; WebSockets add client-to-server frames with only a few bytes of overhead. Chat and multiplayer use WebSockets; live feeds and notifications are fine with SSE.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, v = D.view(c, { x0: 0, x1: 60, y0: 0, y1: 1, pad: 12, padL: 124, padB: 24 }), laneH = (c.h - 60) / 4;
      sim.msgs.forEach(m => { D.line(ctx, v.sx(m), 16, v.sx(m), c.h - 24, P.alpha('accent', .25), 1); D.text(ctx, '▼', v.sx(m), 10, { color: P.accent, size: 9, align: 'center' }); });
      sim.rows.forEach((row, i) => {
        const y = 30 + i * laneH + laneH / 2;
        D.text(ctx, row.name, 10, y, { color: P.text, size: 11.5, weight: 650 });
        row.reqs.forEach(([a, b]) => {
          const w = Math.max(3, v.sx(b) - v.sx(a));
          ctx.fillStyle = row.reqs.length === 1 ? P.alpha(P.series[i], .28) : P.alpha(P.series[i], .7);
          D.rrect(ctx, v.sx(a), y - 8, w - (row.reqs.length > 1 ? 2 : 0), 16, 4); ctx.fill();
        });
        sim.msgs.forEach((m, k) => {
          const d = row.delay[k] ?? 0;
          D.dot(ctx, v.sx(Math.min(60, m + d)), y, 3.5, P.text);
          if (d > .3) D.line(ctx, v.sx(m), y - 11, v.sx(Math.min(60, m + d)), y - 11, P.err, 1.2);
        });
        if (row.duplex) [8, 23, 41, 52].forEach(t => D.text(ctx, '▲', v.sx(t), y + 13, { color: P.series[i], size: 9, align: 'center' }));
      });
      for (let t = 0; t <= 60; t += 10) D.text(ctx, `${t}s`, v.sx(t), c.h - 10, { color: P.faint, size: 10, align: 'center', mono: true });
    };
    update();
  },
});

/* =============================================== 23 · idempotency keys == */
defineLab('sd-idempotency', {
  title: 'Retries without double charging: idempotency keys',
  hint: 'The charge succeeds, but the response is lost on the way back. The client times out and retries. Does the customer pay twice?',
  mount(L) {
    const s = { key: false, lost: true, step: 0, t: 0 };
    const c = L.canvas(w => Math.min(360, w * .56));
    L.toggle('Send an Idempotency-Key header', s.key, v => { s.key = v; s.step = 99; update(); });
    L.toggle('Network loses the first response', s.lost, v => { s.lost = v; s.step = 99; update(); });
    const run = L.loop(dt => { s.t += dt * 1.1; const n = script().length; s.step = Math.min(n, s.t); L.redraw(); update(); if (s.t > n + .2) return false; });
    L.playButton(run, ['Play the sequence', 'Pause'], () => { s.t = 0; s.step = 0; });
    const LANES = ['Client', 'Payments API', 'Database', 'Card network'];
    function script() {
      const st = [
        [0, 1, `POST /charges  $40${s.key ? '\nIdempotency-Key: 7f3a' : ''}`],
        ...(s.key ? [[1, 2, 'INSERT key 7f3a (status: processing)']] : []),
        [1, 3, 'charge card $40'], [3, 1, 'approved · ch_123'],
        [1, 2, s.key ? 'save response under key 7f3a' : 'save charge ch_123'],
        [1, 0, '200 OK ch_123', s.lost],
      ];
      if (!s.lost) return st;
      st.push([0, 0, 'timeout… retry'], [0, 1, `POST /charges  $40${s.key ? '\nIdempotency-Key: 7f3a' : ''}`]);
      if (s.key) st.push([1, 2, 'key 7f3a exists → load saved response'], [1, 0, '200 OK ch_123 (replayed)']);
      else st.push([1, 3, 'charge card $40'], [3, 1, 'approved · ch_124'], [1, 2, 'save charge ch_124'], [1, 0, '200 OK ch_124']);
      return st;
    }
    function update() {
      const st = script().slice(0, Math.floor(s.step));
      const charges = st.filter(x => x[2].startsWith('charge card')).length;
      L.stats([['card charges', charges, charges > 1 ? 'err' : 'accent'], ['customer billed', `$${charges * 40}`, charges > 1 ? 'err' : 'ok']]);
      L.insight(s.step < script().length ? '<b>Press Play.</b> Watch where the response gets lost.'
        : !s.lost ? '<b>No failure, no problem.</b> The trouble only starts when a success is invisible to the caller.'
        : s.key ? '<b>The retry carries the same key</b>, so the API finds the stored result and replays it without touching the card network. At-least-once retries plus an idempotent server give effectively-once charges. Store the key in the same transaction as the charge record.'
        : '<b>Charged twice.</b> The client cannot tell “failed” from “succeeded but the reply was lost”, so it must retry, and without a key the server treats the retry as a brand-new payment.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, lx = i => c.w * (.12 + i * .25), rows = script(), stepH = (c.h - 50) / Math.max(rows.length, 1);
      LANES.forEach((n, i) => {
        ctx.fillStyle = P.surface2; D.rrect(ctx, lx(i) - 52, 6, 104, 26, 8); ctx.fill();
        D.text(ctx, n, lx(i), 19, { color: P.text, size: 11.5, align: 'center', weight: 650 });
        D.line(ctx, lx(i), 34, lx(i), c.h - 8, P.soft, 1.4, [4, 4]);
      });
      rows.forEach(([a, b, label, lost], i) => {
        const k = clamp(s.step - i, 0, 1);
        if (k <= 0) return;
        const y = 50 + i * stepH;
        if (a === b) { D.text(ctx, `⏱ ${label}`, lx(a) + 8, y, { color: P.series[1], size: 11, weight: 650 }); return; }
        const x1 = lx(a), x2 = lerp(lx(a), lx(b), lost ? Math.min(k, .5) : k);
        const col = /charge card/.test(label) ? P.series[1] : /exists|replayed/.test(label) ? P.ok : P.accent;
        D.arrow(ctx, x1, y, x2, y, col, 2, k === 1 && !lost ? 9 : 0);
        label.split('\n').forEach((ln, j) => D.text(ctx, ln, (x1 + lx(b)) / 2, y - 8 - (label.includes('\n') ? (1 - j) * 12 : 0), { color: P.text, size: 10.5, align: 'center', mono: true }));
        if (lost && k >= .5) D.text(ctx, '✕ lost', (lx(a) + lx(b)) / 2, y + 12, { color: P.err, size: 11, align: 'center', weight: 700 });
      });
    };
    s.step = 99;
    update();
  },
});

/* ================================================== 24 · autoscaling == */
defineLab('sd-autoscale', {
  title: 'Autoscaling lag and load shedding',
  hint: 'An hour of traffic with a sudden spike at minute 30. New instances take minutes to boot. What happens to latency in between?',
  mount(L) {
    const s = { target: .6, boot: 3, shed: false, reveal: 1 };
    const CAP = 250, MIN = 10;
    const c = L.canvas(w => Math.min(340, w * .52));
    L.slider('target CPU utilization', { min: .3, max: .95, step: .05, value: s.target, fmt: v => `${Math.round(v * 100)}%` }, v => { s.target = v; compute(); });
    L.slider('instance boot time', { min: .5, max: 8, step: .5, value: s.boot, fmt: v => `${v} min` }, v => { s.boot = v; compute(); });
    L.toggle('Load shedding (reject what we cannot serve)', s.shed, v => { s.shed = v; compute(); });
    const play = L.loop(dt => { s.reveal = Math.min(1, s.reveal + dt / 6); L.redraw(); if (s.reveal >= 1) return false; });
    L.playButton(play, ['Replay the hour', 'Pause'], () => { if (s.reveal >= 1) s.reveal = 0; });
    let sim = null;
    function compute() {
      const load = m => 1800 + 900 * Math.min(1, m / 25) + (m >= 30 && m < 36 ? 3800 * Math.min(1, (m - 30) * 2) * (m < 34 ? 1 : (36 - m) / 2) : 0) + 50 * Math.sin(m / 3);
      const out = [];
      let running = MIN, booting = [], backlog = 0, below = 0, instMin = 0;
      for (let m = 0; m <= 60; m += .25) {
        booting = booting.filter(b => { if (b <= m) { running++; return false; } return true; });
        const L0 = load(m), capacity = running * CAP;
        if (Math.abs(m % 1) < 1e-9) {
          const desired = Math.max(MIN, Math.ceil(L0 / (CAP * s.target)));
          const pending = running + booting.length;
          if (desired > pending) for (let i = 0; i < desired - pending; i++) booting.push(m + s.boot);
          if (desired < running) { below++; if (below >= 5) { running = Math.max(desired, MIN); below = 0; } } else below = 0;
        }
        let drop = 0, lat;
        const util = L0 / capacity;
        if (s.shed) { drop = Math.max(0, (L0 - capacity) / L0); lat = 40 / (1 - Math.min(util, .95)); backlog = 0; }
        else { backlog = Math.max(0, backlog + (L0 - capacity) * 15); lat = 40 / (1 - Math.min(util, .95)) + backlog / capacity * 1000; }
        instMin += running * .25;
        out.push({ m, load: L0, capacity, drop, lat: Math.min(lat, 60000), running });
      }
      const worst = Math.max(...out.map(o => o.lat)), dropped = out.reduce((a, o) => a + o.drop * o.load, 0) / out.reduce((a, o) => a + o.load, 0);
      sim = { out, worst, dropped, instHours: instMin / 60 };
      L.stats([['worst latency', fmtMs(worst), worst > 2000 ? 'err' : 'accent'], ['requests rejected', `${(dropped * 100).toFixed(1)}%`, dropped > 0 ? 'err' : 'ok'], ['instance-hours', sim.instHours.toFixed(0)]]);
      L.insight(s.shed ? '<b>Load shedding rejects the excess</b> during the gap, so the requests you do accept stay fast and the service never builds an unrecoverable backlog. A fast 503 with Retry-After is better than a 30-second timeout.'
        : worst > 5000 ? `<b>Traffic tripled faster than instances could boot.</b> For ${s.boot} minutes capacity trailed load, requests queued, and latency ran away. The backlog keeps latency high even after capacity catches up.`
        : s.target > .8 ? '<b>A high utilization target is cheap but leaves no headroom</b> for spikes or for losing a zone.'
        : '<b>The headroom absorbed the spike.</b> A lower target (or pre-warmed capacity, or faster boot times) is what buys that safety, and you pay for it in idle instances.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, cut = s.reveal * 60, split = c.h * .55;
      const pts = sim.out.filter(o => o.m <= cut);
      const v1 = D.view({ w: c.w, h: split }, { x0: 0, x1: 60, y0: 0, y1: Math.max(...sim.out.map(o => Math.max(o.load, o.capacity))) * 1.08, pad: 12, padL: 50, padB: 16 });
      D.axes(ctx, v1, P, { yTicks: [2000, 4000, 6000], fmtY: t => `${t / 1000}k`, yLabel: 'requests/s' });
      ctx.beginPath(); pts.forEach((o, i) => i ? ctx.lineTo(v1.sx(o.m), v1.sy(o.capacity)) : ctx.moveTo(v1.sx(o.m), v1.sy(o.capacity)));
      ctx.strokeStyle = P.ok; ctx.lineWidth = 2.2; ctx.stroke();
      ctx.beginPath(); pts.forEach((o, i) => i ? ctx.lineTo(v1.sx(o.m), v1.sy(o.load)) : ctx.moveTo(v1.sx(o.m), v1.sy(o.load)));
      ctx.strokeStyle = P.accent; ctx.lineWidth = 2.4; ctx.stroke();
      D.text(ctx, 'traffic', v1.sx(2), v1.sy(sim.out[8].load) - 12, { color: P.accent, size: 10.5, weight: 650 });
      D.text(ctx, 'capacity', v1.sx(2), v1.sy(sim.out[8].capacity) + 12, { color: P.ok, size: 10.5, weight: 650 });
      const v2 = D.view({ w: c.w, h: c.h - split }, { x0: 0, x1: 60, y0: 0, y1: 4.5, pad: 8, padL: 50, padB: 22 });
      ctx.save(); ctx.translate(0, split);
      D.axes(ctx, v2, P, { xTicks: [0, 15, 30, 45, 60], yTicks: [2, 3, 4], fmtY: t => fmtMs(10 ** t), xLabel: 'minutes', yLabel: 'p99 latency' });
      ctx.beginPath(); pts.forEach((o, i) => { const y = v2.sy(clamp(Math.log10(o.lat), 1, 4.5)); i ? ctx.lineTo(v2.sx(o.m), y) : ctx.moveTo(v2.sx(o.m), y); });
      ctx.strokeStyle = P.series[0]; ctx.lineWidth = 2; ctx.stroke();
      pts.forEach(o => { if (o.drop > 0) { ctx.fillStyle = P.alpha('err', .5); ctx.fillRect(v2.sx(o.m), v2.sy(4.5), v2.sx(.25) - v2.sx(0), (v2.sy(0) - v2.sy(4.5)) * o.drop); } });
      ctx.restore();
    };
    compute();
  },
});
