/* ============================================================================
   CS Fundamentals labs, part 2: the machine, the network and the database.

     cs-sched       CPU scheduling on a Gantt chart: FCFS, SJF, SRTF, round robin
     cs-locality    row vs column traversal through a small LRU cache
     cs-latency     latency numbers on a log scale, and in human time
     cs-race        counter += 1 from two threads: step the interleaving yourself
     cs-prodcons    a bounded buffer between producers and consumers
     cs-tcp-window  sliding window, ACKs, loss and the bandwidth-delay product
     cs-isolation   isolation levels run against the five classic anomalies

   Object-spec labs (viz.js createLab). cs-isolation is HTML, styled in
   labs-cs.css. Wrapped in a block: every script shares one global scope.
   ========================================================================= */
'use strict';
{
const fillRR = (ctx, x, y, w, h, r, fill, stroke, lw = 1.2) => {
  D.rrect(ctx, x, y, w, h, r);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
};
const escH = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const expo = (r, mean) => -Math.log(1 - r()) * mean;

/* ============================================================= cs-sched == */
defineLab('cs-sched', {
  title: 'CPU scheduling: who runs next?',
  hint: 'One CPU, several processes. Each row is a process: <b>▲</b> is when it arrives, coloured blocks are when it runs. Change the policy and watch waiting time, response time and context switches move.',
  mount(L) {
    const SETS = {
      mixed: [[0, 7], [2, 4], [4, 1], [5, 4]],
      convoy: [[0, 12], [1, 2], [2, 2], [3, 2], [4, 2]],
      interactive: [[0, 14], [1, 1], [4, 1], [8, 1], [11, 1]],
    };
    const s = { set: 'convoy', algo: 'fcfs', q: 2, cursor: 1 };
    const c = L.canvas(w => Math.min(330, Math.max(260, w * .44)));
    L.seg('policy', [['fcfs', 'First come, first served'], ['sjf', 'Shortest job first'], ['srtf', 'Shortest remaining time (preemptive)'], ['rr', 'Round robin']], s.algo, v => { s.algo = v; replay(); });
    L.seg('workload', [['convoy', 'One long job first'], ['mixed', 'Textbook mix'], ['interactive', 'Batch job + keystrokes']], s.set, v => { s.set = v; replay(); });
    L.slider('round-robin time slice (quantum)', { min: 1, max: 8, step: 1, value: s.q }, v => { s.q = v; if (s.algo === 'rr') replay(); });
    const play = L.loop(dt => { s.cursor = Math.min(1, s.cursor + dt / 5); L.redraw(); if (s.cursor >= 1) return false; });
    L.playButton(play, ['Replay', 'Pause'], () => { if (s.cursor >= 1) s.cursor = 0; });
    let sim = null;
    function simulate() {
      const J = SETS[s.set].map(([arrive, burst], id) => ({ id, arrive, burst, rem: burst, start: -1, end: -1 }));
      const segs = [], queue = [];
      let t = 0, done = 0, cur = null, slice = 0;
      const run = (pid, at) => { const last = segs[segs.length - 1]; if (last && last.pid === pid && last.end === at) last.end++; else segs.push({ pid, start: at, end: at + 1 }); };
      while (done < J.length && t < 200) {
        J.filter(j => j.arrive === t).forEach(j => queue.push(j));
        if (s.algo === 'rr' && cur && slice >= s.q) { queue.push(cur); cur = null; }
        if (s.algo === 'srtf') {
          let best = cur;
          queue.forEach(j => { if (!best || j.rem < best.rem) best = j; });
          if (best && best !== cur) { if (cur) queue.push(cur); queue.splice(queue.indexOf(best), 1); cur = best; }
        } else if (!cur && queue.length) {
          if (s.algo === 'sjf') queue.sort((a, b) => a.burst - b.burst || a.arrive - b.arrive);
          cur = queue.shift(); slice = 0;
        }
        if (cur) {
          if (cur.start < 0) cur.start = t;
          run(cur.id, t); cur.rem--; slice++;
          if (!cur.rem) { cur.end = t + 1; done++; cur = null; }
        } else run(-1, t);
        t++;
      }
      const switches = segs.filter((g, i) => i && g.pid >= 0 && segs[i - 1].pid >= 0 && g.pid !== segs[i - 1].pid).length;
      const avg = f => J.reduce((a, j) => a + f(j), 0) / J.length;
      return { J, segs, T: t, switches, wait: avg(j => j.end - j.arrive - j.burst), tat: avg(j => j.end - j.arrive), resp: avg(j => j.start - j.arrive) };
    }
    function replay() { sim = simulate(); s.cursor = 0; play.start(); update(); }
    function update() {
      L.stats([['average waiting time', fmtN(sim.wait, 1), 'accent'], ['average turnaround', fmtN(sim.tat, 1)], ['average response time', fmtN(sim.resp, 1), 'accent'], ['context switches', sim.switches, sim.switches > 8 ? 'err' : '']]);
      const tips = {
        fcfs: '<b>FCFS</b> runs jobs in arrival order, to completion. Simple and starvation-free, but one long job at the front makes every short job behind it wait — the <b>convoy effect</b>.',
        sjf: '<b>Shortest job first</b> gives the lowest possible average waiting time among non-preemptive policies — but the OS cannot know a burst length in advance (it predicts from past bursts), and a stream of short jobs can <b>starve</b> a long one.',
        srtf: '<b>Shortest remaining time first</b> preempts whenever a shorter job arrives. It minimises average waiting time overall, at the cost of more context switches and possible starvation.',
        rr: `<b>Round robin</b> gives each process a ${s.q}-tick slice in turn. Response time is great for short, interactive jobs; turnaround is worse. A tiny slice means constant switching (each switch costs microseconds and a cold cache); a huge slice turns into FCFS. Linux does not use a fixed slice: CFS picked the task with the least virtual runtime, and EEVDF (default since 6.6) the earliest eligible virtual deadline.`,
      };
      L.insight(tips[s.algo]);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, left = 54, right = c.w - 150, top = 30, n = sim.J.length, rowH = Math.min(38, (c.h - top - 58) / (n + 1));
      const T = Math.max(sim.T, 12), X = t => left + (right - left) * t / T, cut = s.cursor * sim.T;
      for (let t = 0; t <= T; t++) {
        D.line(ctx, X(t), top - 4, X(t), top + (n + 1) * rowH, t % 5 ? P.soft : P.border, 1);
        if (t % 2 === 0) D.text(ctx, t, X(t), top + (n + 1) * rowH + 12, { color: P.faint, size: 9.5, align: 'center', mono: true });
      }
      D.text(ctx, 'CPU', 10, top + rowH / 2, { color: P.dim, size: 11, weight: 700 });
      sim.segs.forEach(g => {
        if (g.start >= cut) return;
        const e = Math.min(g.end, cut);
        if (g.pid < 0) { D.text(ctx, 'idle', X((g.start + e) / 2), top + rowH / 2, { color: P.faint, size: 9, align: 'center' }); return; }
        const col = P.series[g.pid % 8];
        fillRR(ctx, X(g.start) + 1, top + 4, X(e) - X(g.start) - 2, rowH - 8, 3, P.alpha(col, .75));
        if (X(e) - X(g.start) > 22) D.text(ctx, `P${g.pid + 1}`, X((g.start + e) / 2), top + rowH / 2, { color: P.bg, size: 10.5, align: 'center', weight: 700 });
        const y = top + (g.pid + 1) * rowH;
        fillRR(ctx, X(g.start) + 1, y + 6, X(e) - X(g.start) - 2, rowH - 12, 3, P.alpha(col, .45), col);
      });
      sim.J.forEach(j => {
        const y = top + (j.id + 1) * rowH, col = P.series[j.id % 8];
        D.text(ctx, `P${j.id + 1}`, 10, y + rowH / 2, { color: col, size: 11, weight: 700 });
        D.text(ctx, `burst ${j.burst}`, 10, y + rowH / 2 + 11, { color: P.faint, size: 8.5 });
        ctx.fillStyle = col; ctx.beginPath(); const ax = X(j.arrive);
        ctx.moveTo(ax, y + rowH - 2); ctx.lineTo(ax - 5, y + rowH + 6); ctx.lineTo(ax + 5, y + rowH + 6); ctx.fill();
        if (j.end <= cut) {
          ctx.save(); ctx.setLineDash([2, 3]); D.line(ctx, X(j.arrive), y + rowH / 2, X(j.end), y + rowH / 2, P.alpha(col, .35), 1); ctx.restore();
          D.text(ctx, `wait ${j.end - j.arrive - j.burst} · resp ${j.start - j.arrive}`, right + 12, y + rowH / 2, { color: P.dim, size: 10.5, mono: true });
        }
      });
      if (s.cursor < 1) D.line(ctx, X(cut), top - 8, X(cut), top + (n + 1) * rowH + 2, P.accent, 2);
      D.text(ctx, 'time →', right, c.h - 8, { color: P.faint, size: 10, align: 'right' });
    };
    replay();
  },
});

/* ========================================================== cs-locality == */
defineLab('cs-locality', {
  title: 'Cache lines: why loop order changes speed',
  hint: 'An 8 × 8 matrix stored <b>row by row</b> in memory. The CPU never fetches one number: it fetches a whole <b>cache line</b> (here 4 numbers; 64 bytes on real CPUs). Green = cache hit, red = miss that went to RAM.',
  mount(L) {
    const R = 8, C = 8, LINE = 4;
    const s = { order: 'row', lines: 4, i: 0, seq: [], res: [], cache: [], hits: 0, miss: 0 };
    const c = L.canvas(w => Math.min(330, Math.max(270, w * .44)));
    L.seg('loop order', [['row', 'for row: for col (row-major)'], ['col', 'for col: for row (column-major)'], ['tile', '4 × 4 tiles']], s.order, v => { s.order = v; reset(); });
    L.slider('cache size (lines, LRU)', { min: 2, max: 16, step: 1, value: s.lines }, v => { s.lines = v; reset(); });
    const run = L.loop(dt => { s.acc = (s.acc || 0) + dt; while (s.acc > .09) { s.acc -= .09; if (!step()) { L.redraw(); return false; } } L.redraw(); });
    L.playButton(run, ['Run the loop', 'Pause'], () => { if (s.i >= s.seq.length) reset(); });
    L.button('Step', () => step());
    L.button('Finish instantly', () => { while (step()); });
    function order() {
      const out = [];
      if (s.order === 'row') for (let i = 0; i < R; i++) for (let j = 0; j < C; j++) out.push([i, j]);
      else if (s.order === 'col') for (let j = 0; j < C; j++) for (let i = 0; i < R; i++) out.push([i, j]);
      else for (let bi = 0; bi < R; bi += 4) for (let bj = 0; bj < C; bj += 4) for (let j = bj; j < bj + 4; j++) for (let i = bi; i < bi + 4; i++) out.push([i, j]);
      return out;
    }
    function reset() { Object.assign(s, { i: 0, seq: order(), res: Array(R * C).fill(0), cache: [], hits: 0, miss: 0 }); update(); }
    function step() {
      if (s.i >= s.seq.length) return false;
      const [i, j] = s.seq[s.i++], addr = i * C + j, line = Math.floor(addr / LINE), at = s.cache.indexOf(line);
      if (at >= 0) { s.cache.splice(at, 1); s.cache.unshift(line); s.hits++; s.res[addr] = 1; }
      else { s.cache.unshift(line); if (s.cache.length > s.lines) s.cache.pop(); s.miss++; s.res[addr] = 2; }
      update();
      return true;
    }
    function update() {
      const n = s.hits + s.miss, ns = s.hits * 1 + s.miss * 100;
      L.stats([['accesses', n], ['hits', s.hits, 'ok'], ['misses', s.miss, 'err'], ['hit rate', n ? `${Math.round(s.hits / n * 100)}%` : '—', 'accent'], ['time at 1 ns/hit, 100 ns/miss', `${ns.toLocaleString()} ns`]]);
      const tips = {
        row: 'Walking a row reads addresses in order: one miss loads a line, and the next 3 reads are free. That is <b>spatial locality</b> — 75% hits no matter how small the cache. The hardware prefetcher usually hides even that first miss.',
        col: `Walking down a column jumps ${C} elements each step, so every read lands on a <b>different line</b>. Column 1 can only reuse the lines column 0 loaded if all ${R} of them are still cached: with fewer than ${R} lines, LRU has evicted each one just before it is needed, and every access misses. Grow the cache to ${R} and watch it flip.`,
        tile: 'Tiling (blocking) walks a 4 × 4 block at a time, so the lines a block needs fit in a small cache and are reused before eviction. Matrix multiply, transposes and image filters are tiled for exactly this reason.',
      };
      L.insight(`${tips[s.order]} On a real 4096 × 4096 matrix of doubles the column-order loop is often 5–10× slower than row order, for the same Big-O. NumPy and C store row-major; Fortran, MATLAB and R column-major.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, cell = Math.min(30, (c.h - 60) / R, (c.w * .45) / C), mx = 16, my = 30;
      D.text(ctx, 'the matrix (what the code sees)', mx, 14, { color: P.dim, size: 10.5, weight: 600 });
      const cur = s.i ? s.seq[s.i - 1] : null;
      for (let i = 0; i < R; i++) for (let j = 0; j < C; j++) {
        const addr = i * C + j, r = s.res[addr], x = mx + j * cell, y = my + i * cell;
        fillRR(ctx, x + 1, y + 1, cell - 2, cell - 2, 3, r === 1 ? P.alpha('ok', .55) : r === 2 ? P.alpha('err', .55) : P.surface2, P.border, 1);
        if (cur && cur[0] === i && cur[1] === j) fillRR(ctx, x, y, cell, cell, 4, null, P.accent, 2.6);
      }
      for (let i = 0; i < R; i++) D.line(ctx, mx + cell * 4, my + i * cell + 3, mx + cell * 4, my + (i + 1) * cell - 3, P.strong, 2);
      const lx = mx + C * cell + 40, lw = c.w - lx - 16, lcell = Math.min(24, lw / (R * C / LINE) - 2);
      D.text(ctx, 'memory, one cache line per box (4 numbers each)', lx, 14, { color: P.dim, size: 10.5, weight: 600 });
      const lines = R * C / LINE, perRow = Math.max(1, Math.floor(lw / (lcell + 2)));
      for (let k = 0; k < lines; k++) {
        const x = lx + (k % perRow) * (lcell + 2), y = my + Math.floor(k / perRow) * (lcell + 18);
        const inC = s.cache.indexOf(k);
        fillRR(ctx, x, y, lcell, lcell, 3, inC >= 0 ? P.alpha('accent', .35 + .5 * (1 - inC / s.lines)) : P.surface2, inC === 0 ? P.accent : P.border, inC === 0 ? 2 : 1);
        D.text(ctx, k, x + lcell / 2, y + lcell + 8, { color: P.faint, size: 8.5, align: 'center', mono: true });
      }
      const cy = my + Math.ceil(lines / perRow) * (lcell + 18) + 20;
      D.text(ctx, `the cache: ${s.lines} lines, most recently used first`, lx, cy, { color: P.dim, size: 10.5, weight: 600 });
      for (let k = 0; k < s.lines; k++) {
        const x = lx + k * Math.min(34, lw / s.lines), w = Math.min(30, lw / s.lines - 4);
        fillRR(ctx, x, cy + 10, w, 24, 4, s.cache[k] != null ? P.alpha('accent', .25) : 'transparent', P.border);
        if (s.cache[k] != null) D.text(ctx, s.cache[k], x + w / 2, cy + 22, { color: P.text, size: 10.5, align: 'center', mono: true, weight: 650 });
      }
      if (cur) {
        const addr = cur[0] * C + cur[1];
        D.text(ctx, `a[${cur[0]}][${cur[1]}] → address ${addr} → line ${Math.floor(addr / LINE)} → ${s.res[addr] === 1 ? 'HIT' : 'MISS'}`, lx, cy + 52, { color: s.res[addr] === 1 ? P.ok : P.err, size: 11.5, mono: true, weight: 700 });
      }
    };
    reset();
  },
});

/* =========================================================== cs-latency == */
defineLab('cs-latency', {
  title: 'Latency numbers every engineer should feel',
  hint: 'Order-of-magnitude costs on a log scale. Switch to <b>human scale</b> to stretch them so that one L1 cache hit takes one second, then set a latency budget and see how many of each fit inside it.',
  mount(L) {
    const ROWS = [
      ['L1 cache hit', 1e-9, 'cpu'], ['Branch mispredict', 3e-9, 'cpu'], ['L2 cache hit', 4e-9, 'cpu'], ['Uncontended mutex lock/unlock', 2e-8, 'cpu'],
      ['Main memory (RAM) access', 1e-7, 'mem'], ['Compress 1 KB (Snappy/LZ4)', 2e-6, 'cpu'], ['OS thread context switch', 3e-6, 'cpu'],
      ['Random 4 KB read, NVMe SSD', 2e-5, 'disk'], ['Read 1 MB sequentially from RAM', 5e-5, 'mem'], ['Read 1 MB sequentially from NVMe SSD', 3e-4, 'disk'],
      ['Round trip inside one datacenter', 5e-4, 'net'], ['Send 1 MB over a 10 Gbps link', 1e-3, 'net'], ['HDD seek', 5e-3, 'disk'], ['Read 1 MB sequentially from HDD', 5e-3, 'disk'],
      ['Round trip US East ↔ US West', 7e-2, 'net'], ['Round trip California ↔ Netherlands', 1.5e-1, 'net'], ['New HTTPS connection across an ocean (TCP + TLS 1.3)', 3e-1, 'net'],
    ];
    const KIND = { cpu: 0, mem: 2, disk: 1, net: 3 };
    const s = { human: false, budget: .1, grow: 0 };
    const c = L.canvas(() => 26 + ROWS.length * 21 + 46);
    L.seg('scale', [[0, 'Real time'], [1, 'Human scale: L1 hit = 1 second']], 0, v => { s.human = !!v; L.redraw(); update(); });
    L.slider('latency budget (e.g. a request’s p99 target)', { min: 1e-3, max: 1, log: true, value: s.budget, fmt: v => v < 1 ? `${Math.round(v * 1000)} ms` : '1 s' }, v => { s.budget = v; update(); });
    const grow = L.loop(dt => { s.grow = Math.min(1, s.grow + dt * 1.4); L.redraw(); if (s.grow >= 1) return false; });
    const human = sec => {
      const h = sec * 1e9;
      if (h < 60) return `${fmtN(h, h < 10 ? 1 : 0)} s`;
      if (h < 3600) return `${fmtN(h / 60, 1)} min`;
      if (h < 86400) return `${fmtN(h / 3600, 1)} hours`;
      if (h < 3.15e7) return `${fmtN(h / 86400, 1)} days`;
      return `${fmtN(h / 3.15e7, 1)} years`;
    };
    const real = sec => sec < 1e-6 ? `${fmtN(sec * 1e9, 0)} ns` : sec < 1e-3 ? `${fmtN(sec * 1e6, 0)} µs` : sec < 1 ? `${fmtN(sec * 1e3, 0)} ms` : `${fmtN(sec, 1)} s`;
    function update() {
      const fit = sec => Math.floor(s.budget / sec);
      L.stats([['budget', real(s.budget), 'accent'], ['RAM reads that fit', fmtBig(fit(1e-7))], ['SSD random reads', fmtBig(fit(2e-5))], ['datacenter round trips', fmtBig(fit(5e-4)), 'ok'], ['cross-ocean round trips', fit(1.5e-1), fit(1.5e-1) < 1 ? 'err' : 'ok']]);
      L.insight(`Inside a ${real(s.budget)} budget you can afford about ${fmtBig(fit(5e-4))} sequential calls to another service in the same datacenter, but ${fit(1.5e-1) < 1 ? '<b>not even one</b>' : `only <b>${fit(1.5e-1)}</b>`} round trip across an ocean. That single fact drives CDNs, regional replicas, connection reuse, and batching. The ratio that matters most: RAM is ~100× slower than L1, an SSD read ~200× slower than RAM, and the network between regions is a million times slower than RAM.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, left = Math.min(330, c.w * .42), right = c.w - 90, top = 22, rowH = 21;
      const e0 = -9, e1 = 0, X = sec => left + (right - left) * (Math.log10(sec) - e0) / (e1 - e0);
      [-9, -6, -3, 0].forEach((e, k) => {
        D.line(ctx, X(10 ** e), top - 6, X(10 ** e), top + ROWS.length * rowH, P.soft, 1);
        D.text(ctx, s.human ? ['1 s', '17 min', '12 days', '32 years'][k] : ['1 ns', '1 µs', '1 ms', '1 s'][k], X(10 ** e), top + ROWS.length * rowH + 12, { color: P.faint, size: 10, align: 'center', mono: true });
      });
      ctx.save(); ctx.setLineDash([6, 4]); D.line(ctx, X(s.budget), top - 10, X(s.budget), top + ROWS.length * rowH, P.err, 1.6); ctx.restore();
      D.text(ctx, `budget ${real(s.budget)}`, X(s.budget) - 4, top - 12, { color: P.err, size: 10, align: 'right', weight: 650 });
      D.font(ctx, 11);
      const fitName = t => { let x = t; while (x.length > 4 && ctx.measureText(x).width > left - 16) x = x.slice(0, -2); return x === t ? t : x.trimEnd() + '…'; };
      ROWS.forEach(([name, sec, kind], i) => {
        const y = top + i * rowH, col = P.series[KIND[kind]];
        D.font(ctx, 11);
        D.text(ctx, fitName(name), left - 10, y + rowH / 2, { color: P.text, size: 11, align: 'right' });
        const w = (X(sec) - left) * easeOut(s.grow);
        fillRR(ctx, left, y + 4, Math.max(2, w), rowH - 8, 3, P.alpha(col, .45), col, 1);
        D.text(ctx, s.human ? human(sec) : real(sec), left + Math.max(2, w) + 6, y + rowH / 2, { color: sec > s.budget ? P.err : P.dim, size: 10.5, mono: true, weight: 600 });
      });
      [['cpu', 'CPU'], ['mem', 'memory'], ['disk', 'storage'], ['net', 'network']].forEach(([k, lbl], i) => {
        D.dot(ctx, 12 + i * 78, c.h - 9, 4, P.series[KIND[k]]);
        D.text(ctx, lbl, 20 + i * 78, c.h - 9, { color: P.dim, size: 10 });
      });
    };
    update(); grow.start();
  },
});

/* ============================================================== cs-race == */
defineLab('cs-race', {
  title: 'A data race you can step through: counter += 1 on two threads',
  hint: '<code>counter += 1</code> is not one step: the CPU <b>loads</b> the value into a register, <b>adds</b> one, and <b>stores</b> it back. You are the scheduler — step either thread in any order, then try to lose an update.',
  mount(L) {
    const r = rng(3);
    const s = { mode: 'none', k: 2, hist: null };
    const c = L.canvas(w => Math.min(360, Math.max(300, w * .5)));
    L.seg('protection', [['none', 'None'], ['lock', 'Mutex around it'], ['atomic', 'Atomic add']], s.mode, v => { s.mode = v; s.hist = null; reset(); });
    L.seg('increments per thread', [[1, '1'], [2, '2'], [3, '3']], s.k, v => { s.k = v; s.hist = null; reset(); });
    L.button('Step T1', () => step(0), 'primary');
    L.button('Step T2', () => step(1), 'primary');
    L.button('Show me a lost update', () => scripted());
    L.button('Random schedule', () => { reset(); auto.start(); });
    L.button('Run 10,000 random schedules', () => histogram());
    L.button('Reset', () => { auto.stop(); reset(); });
    const auto = L.loop(dt => { s.acc = (s.acc || 0) + dt; if (s.acc < .32) return; s.acc = 0; const pick = s.plan ? s.plan.shift() : null; const run = runnable(st); if (!run.length) return false; step(pick != null && run.includes(pick) ? pick : run[Math.floor(r() * run.length)]); });
    let st;
    const prog = () => {
      const one = s.mode === 'none' ? ['LOAD', 'ADD', 'STORE'] : s.mode === 'lock' ? ['LOCK', 'LOAD', 'ADD', 'STORE', 'UNLOCK'] : ['ATOMIC_ADD'];
      return Array.from({ length: s.k }, () => one).flat();
    };
    function fresh() { const p = prog(); return { counter: 0, owner: -1, th: [0, 1].map(() => ({ pc: 0, reg: null, prog: p, blocked: false })), trace: [] }; }
    function reset() { st = fresh(); s.plan = null; update(); }
    const runnable = S => [0, 1].filter(t => S.th[t].pc < S.th[t].prog.length && !(S.th[t].prog[S.th[t].pc] === 'LOCK' && S.owner >= 0 && S.owner !== t));
    function exec(S, t) {
      const T = S.th[t];
      if (T.pc >= T.prog.length) return null;
      const op = T.prog[T.pc];
      let note = '';
      if (op === 'LOCK') { if (S.owner >= 0 && S.owner !== t) { T.blocked = true; return { t, op, note: `waits — T${S.owner + 1} holds the lock`, blocked: true }; } S.owner = t; note = 'acquired'; }
      if (op === 'LOAD') { T.reg = S.counter; note = `reg = ${T.reg}`; }
      if (op === 'ADD') { T.reg++; note = `reg = ${T.reg}`; }
      if (op === 'STORE') { const lost = S.counter !== T.reg - 1; S.counter = T.reg; note = `counter = ${S.counter}${lost ? '  ← overwrote an update' : ''}`; }
      if (op === 'UNLOCK') { S.owner = -1; S.th.forEach(x => { x.blocked = false; }); note = 'released'; }
      if (op === 'ATOMIC_ADD') { S.counter++; note = `counter = ${S.counter} (one indivisible instruction)`; }
      T.blocked = false; T.pc++;
      return { t, op, note, lost: /overwrote/.test(note) };
    }
    function step(t) { const e = exec(st, t); if (e) st.trace.push(e); update(); }
    function scripted() {
      auto.stop(); reset();
      if (s.mode !== 'none') { s.plan = [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1]; auto.start(); return; }
      s.plan = [0, 1, 0, 0, 1, 1]; for (let i = 1; i < s.k; i++) s.plan.push(0, 0, 0, 1, 1, 1);
      auto.start();
    }
    function histogram() {
      auto.stop();
      const counts = {};
      for (let n = 0; n < 10000; n++) {
        const S = fresh();
        for (let g = 0; g < 200; g++) { const run = runnable(S); if (!run.length) break; exec(S, run[Math.floor(r() * run.length)]); }
        counts[S.counter] = (counts[S.counter] || 0) + 1;
      }
      s.hist = counts; update();
    }
    function update() {
      const done = st.th.every(T => T.pc >= T.prog.length), want = 2 * s.k;
      L.stats([['counter', st.counter, done ? (st.counter === want ? 'ok' : 'err') : 'accent'], ['expected', want], ['T1 register', st.th[0].reg ?? '—'], ['T2 register', st.th[1].reg ?? '—'],
        s.hist ? ['correct in 10,000 random runs', `${((s.hist[want] || 0) / 100).toFixed(1)}%`, (s.hist[want] || 0) === 10000 ? 'ok' : 'err'] : null]);
      const lost = st.trace.some(e => e.lost);
      const base = {
        none: 'Without protection, the result depends on the interleaving. If both threads LOAD before either STOREs, they both write the same value and one increment vanishes: a <b>lost update</b>. Most schedules are fine, which is exactly why races survive testing.',
        lock: 'The mutex makes LOAD-ADD-STORE a <b>critical section</b>: a thread that reaches LOCK while the other holds it must wait. Every schedule now gives the right answer, and the three steps of the two threads can no longer interleave — correctness bought with serialisation.',
        atomic: 'An atomic add does the read-modify-write as one indivisible hardware instruction (<code>LOCK XADD</code> on x86, <code>LDADD</code> on ARM). No lock, no waiting — but it only works for a single machine word. Go: <code>atomic.AddInt64</code>; Java: <code>AtomicLong</code>; C++: <code>std::atomic</code>.',
      };
      L.insight(`${done ? (st.counter === want ? `Finished: counter = ${want}, as expected. ` : `<b>Finished: counter = ${st.counter}, but ${want} increments ran.</b> `) : ''}${lost && !done ? '<b>An update was just overwritten.</b> ' : ''}${base[s.mode]} In Python the GIL does not save you: <code>counter += 1</code> is several bytecodes and a thread switch can land between them. <code>go run -race</code> and ThreadSanitizer catch this class of bug.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, colW = Math.min(210, c.w * .3), gap = (c.w - colW * 2) / 2, x1 = 10, x2 = c.w - colW - 10, mid = c.w / 2;
      const top = 30, lineH = Math.min(19, (c.h * .62 - 40) / Math.max(1, st.th[0].prog.length));
      [x1, x2].forEach((x, t) => {
        const T = st.th[t], col = P.series[t ? 1 : 0];
        D.text(ctx, `Thread T${t + 1}`, x, 14, { color: col, size: 12, weight: 700 });
        D.text(ctx, `register: ${T.reg ?? '—'}`, x + colW, 14, { color: P.dim, size: 10.5, align: 'right', mono: true });
        T.prog.forEach((op, i) => {
          const y = top + i * lineH, cur = i === T.pc, past = i < T.pc;
          if (cur) fillRR(ctx, x, y, colW, lineH - 2, 3, P.alpha(col, T.blocked ? .08 : .2), T.blocked ? P.err : col);
          D.text(ctx, `${cur ? '▶ ' : '  '}${op}`, x + 6, y + lineH / 2 - 1, { color: past ? P.faint : cur ? P.text : P.dim, size: 11, mono: true, weight: cur ? 700 : 500 });
        });
        if (T.pc >= T.prog.length) D.text(ctx, 'done', x + 6, top + T.prog.length * lineH + 8, { color: P.ok, size: 10.5, weight: 700 });
      });
      const my = top + 16;
      fillRR(ctx, mid - 60, my, 120, 58, 10, P.surface2, P.accent, 1.6);
      D.text(ctx, 'shared memory', mid, my + 16, { color: P.dim, size: 10, align: 'center' });
      D.text(ctx, `counter = ${st.counter}`, mid, my + 38, { color: P.text, size: 15, align: 'center', mono: true, weight: 700 });
      if (s.mode === 'lock') {
        fillRR(ctx, mid - 60, my + 70, 120, 30, 8, st.owner >= 0 ? P.alpha(P.series[st.owner ? 1 : 0], .2) : P.surface2, P.border);
        D.text(ctx, st.owner >= 0 ? `lock held by T${st.owner + 1}` : 'lock: free', mid, my + 85, { color: P.text, size: 11, align: 'center', weight: 600 });
      }
      const ty = c.h * .66;
      D.text(ctx, 'what actually ran, in order', 10, ty - 10, { color: P.dim, size: 10.5, weight: 600 });
      const shown = st.trace.slice(-8), cw = (c.w - 20) / 8;
      shown.forEach((e, i) => {
        const x = 10 + i * cw, col = P.series[e.t ? 1 : 0];
        fillRR(ctx, x + 2, ty, cw - 4, 34, 5, P.alpha(e.lost ? 'err' : col, e.lost ? .3 : .16), e.lost ? P.err : e.blocked ? P.faint : col);
        D.text(ctx, `T${e.t + 1} ${e.op}`, x + cw / 2, ty + 11, { color: P.text, size: cw > 90 ? 10.5 : 9, align: 'center', mono: true, weight: 700 });
        D.text(ctx, e.note.replace('  ← overwrote an update', ' ✗'), x + cw / 2, ty + 25, { color: e.lost ? P.err : P.dim, size: cw > 90 ? 9.5 : 8, align: 'center', mono: true });
      });
      if (s.hist) {
        const keys = Object.keys(s.hist).map(Number).sort((a, b) => a - b), mx = Math.max(...Object.values(s.hist)), want = 2 * s.k;
        const hx = 10, hy = c.h - 8, bw = Math.min(60, (c.w - 200) / keys.length);
        D.text(ctx, 'final counter over 10,000 random schedules:', hx, hy - 30, { color: P.dim, size: 10.5 });
        keys.forEach((k, i) => {
          const h = 18 * s.hist[k] / mx, x = 270 + i * (bw + 6);
          fillRR(ctx, x, hy - h - 12, bw, h + 1, 2, k === want ? P.ok : P.err);
          D.text(ctx, `${k}: ${(s.hist[k] / 100).toFixed(1)}%`, x + bw / 2, hy - 4, { color: k === want ? P.ok : P.err, size: 9.5, align: 'center', mono: true });
        });
      }
    };
    reset();
  },
});

/* ========================================================== cs-prodcons == */
defineLab('cs-prodcons', {
  title: 'Producers, consumers and a bounded buffer',
  hint: 'A producer puts work into a buffer, consumers take it out. Make the producer faster than the consumers can keep up with, then compare a <b>bounded</b> buffer (the producer blocks: backpressure) with an <b>unbounded</b> one (the queue just grows).',
  mount(L) {
    const r = rng(17);
    const s = { lam: 4, mu: 1.5, nc: 2, cap: 8, unbounded: false, t: 0 };
    const c = L.canvas(w => Math.min(320, Math.max(260, w * .42)));
    L.slider('producer rate (items/s)', { min: .5, max: 10, step: .5, value: s.lam }, v => { s.lam = v; });
    L.slider('each consumer’s rate (items/s)', { min: .5, max: 5, step: .5, value: s.mu }, v => { s.mu = v; });
    L.slider('buffer capacity', { min: 1, max: 20, step: 1, value: s.cap }, v => { s.cap = v; });
    L.seg('consumers', [[1, '1'], [2, '2'], [3, '3'], [4, '4']], s.nc, v => { s.nc = v; resetConsumers(); });
    L.toggle('Unbounded buffer', s.unbounded, v => { s.unbounded = v; });
    const run = L.loop(dt => { tick(dt); L.redraw(); s.acc = (s.acc || 0) + dt; if (s.acc > .3) { s.acc = 0; update(); } });
    L.playButton(run, ['Run', 'Pause']);
    L.button('Reset', () => { reset(); L.redraw(); });
    let st;
    function resetConsumers() { if (st) st.cons = Array.from({ length: s.nc }, () => ({ busyUntil: 0, item: null })); }
    function reset() { s.t = 0; st = { buf: [], next: 0, blocked: null, blockedT: 0, produced: 0, consumed: 0, waitSum: 0, idleT: 0, occ: 0, hist: [], fly: [] }; resetConsumers(); update(); }
    function tick(dt) {
      s.t += dt;
      const room = () => s.unbounded || st.buf.length < s.cap;
      if (st.blocked) { st.blockedT += dt; if (room()) { st.buf.push(st.blocked); st.fly.push({ a: 'p', t: 0 }); st.blocked = null; } }
      else if (s.t >= st.next) {
        const it = { born: s.t, id: st.produced++ };
        if (room()) { st.buf.push(it); st.fly.push({ a: 'p', t: 0 }); } else st.blocked = it;
        st.next = s.t + expo(r, 1 / s.lam);
      }
      st.cons.forEach((cn, k) => {
        if (cn.item && s.t >= cn.busyUntil) { cn.item = null; st.consumed++; }
        if (!cn.item && st.buf.length) { cn.item = st.buf.shift(); st.waitSum += s.t - cn.item.born; cn.busyUntil = s.t + expo(r, 1 / s.mu); cn.start = s.t; st.fly.push({ a: 'c', k, t: 0 }); }
        if (!cn.item) st.idleT += dt / s.nc;
      });
      st.occ += st.buf.length * dt;
      st.fly.forEach(f => { f.t += dt * 3; }); st.fly = st.fly.filter(f => f.t < 1);
      if ((st.hist.length ? s.t - st.hist[st.hist.length - 1][0] : 1) > .1) { st.hist.push([s.t, st.buf.length]); if (st.hist.length > 240) st.hist.shift(); }
    }
    function update() {
      const cap = s.nc * s.mu, t = Math.max(s.t, 1e-9);
      L.stats([['offered load λ', `${s.lam}/s`], ['service capacity c·μ', `${fmtN(cap, 1)}/s`, s.lam > cap ? 'err' : 'ok'], ['throughput', `${fmtN(st.consumed / t, 1)}/s`, 'accent'],
        ['avg items waiting', fmtN(st.occ / t, 1)], ['avg wait in buffer', `${fmtN(st.consumed ? st.waitSum / Math.max(1, st.consumed) : 0, 2)} s`], ['producer blocked', `${Math.round(st.blockedT / t * 100)}%`, st.blockedT / t > .1 ? 'err' : ''], ['consumers idle', `${Math.round(st.idleT / t * 100)}%`]]);
      const over = s.lam > cap;
      L.insight(over
        ? (s.unbounded
          ? `Arrivals (${s.lam}/s) exceed capacity (${fmtN(cap, 1)}/s) and nothing pushes back, so the queue grows without limit — and by <b>Little’s law</b> (items waiting = arrival rate × wait) every new item waits longer than the last. In production this is the memory leak that ends in an out-of-memory crash, or the Kafka consumer lag that is hours behind.`
          : `Arrivals (${s.lam}/s) exceed capacity (${fmtN(cap, 1)}/s). The buffer fills and <code>put()</code> <b>blocks the producer</b>: throughput settles at the consumers’ ${fmtN(cap, 1)}/s and the pressure is pushed upstream instead of piling up in memory. That is <b>backpressure</b> — Python’s <code>queue.Queue(maxsize)</code>, a buffered Go channel, TCP’s receive window.`)
        : `Capacity (${fmtN(cap, 1)}/s) exceeds arrivals (${s.lam}/s), so the buffer is usually near empty and consumers sit idle part of the time. The buffer only absorbs bursts. Push λ close to c·μ and watch the waiting time climb long before the buffer is ever full — queues get slow well before they get full.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, H = c.h - 70, px = 16, pw = 110, cx = c.w - 150, cw = 134;
      const midY = H / 2 + 8;
      fillRR(ctx, px, midY - 28, pw, 56, 10, st.blocked ? P.alpha('err', .2) : P.surface2, st.blocked ? P.err : P.series[0], 1.6);
      D.text(ctx, 'producer', px + pw / 2, midY - 8, { color: P.text, size: 12, align: 'center', weight: 700 });
      D.text(ctx, st.blocked ? 'blocked: buffer full' : `${s.lam}/s`, px + pw / 2, midY + 12, { color: st.blocked ? P.err : P.dim, size: 10, align: 'center' });
      const bx = px + pw + 26, bw = cx - bx - 26, slots = s.unbounded ? Math.max(20, st.buf.length) : s.cap, sw = Math.min(26, bw / Math.min(slots, 30));
      D.text(ctx, s.unbounded ? `buffer: ${st.buf.length} items (no limit)` : `buffer: ${st.buf.length} / ${s.cap}`, bx, midY - 30, { color: P.dim, size: 10.5, weight: 600 });
      const vis = Math.min(slots, Math.floor(bw / sw));
      for (let i = 0; i < vis; i++) {
        const x = bx + i * sw, full = i < st.buf.length;
        fillRR(ctx, x + 1, midY - 14, sw - 2, 28, 3, full ? P.alpha('accent', .7) : 'transparent', full ? null : P.border);
      }
      if (st.buf.length > vis) D.text(ctx, `+${st.buf.length - vis} more`, bx + bw, midY + 26, { color: P.err, size: 10.5, align: 'right', weight: 700 });
      st.cons.forEach((cn, k) => {
        const y = 16 + k * ((H - 10) / s.nc), h = Math.min(46, (H - 10) / s.nc - 8);
        fillRR(ctx, cx, y, cw, h, 8, cn.item ? P.alpha(P.series[2], .18) : P.surface2, cn.item ? P.series[2] : P.border, 1.4);
        D.text(ctx, `consumer ${k + 1}`, cx + 10, y + h / 2 - (h > 34 ? 7 : 0), { color: P.text, size: 11, weight: 650 });
        if (h > 34) D.text(ctx, cn.item ? 'working' : 'waiting: buffer empty', cx + 10, y + h / 2 + 9, { color: cn.item ? P.dim : P.faint, size: 9.5 });
        if (cn.item) { const p = clamp((s.t - cn.start) / Math.max(.01, cn.busyUntil - cn.start), 0, 1); fillRR(ctx, cx + cw - 42, y + h / 2 - 3, 34 * p, 6, 3, P.series[2]); }
      });
      st.fly.forEach(f => {
        const e = easeOut(f.t);
        if (f.a === 'p') D.dot(ctx, lerp(px + pw, bx + Math.max(0, st.buf.length - 1) * sw + sw / 2, e), midY, 5, P.accent);
        else { const y = 16 + f.k * ((H - 10) / s.nc) + Math.min(46, (H - 10) / s.nc - 8) / 2; D.dot(ctx, lerp(bx, cx, e), lerp(midY, y, e), 5, P.accent); }
      });
      const gy = c.h - 8, gh = 44, gx = 16, gw = c.w - 32;
      D.text(ctx, 'items in the buffer over time', gx, gy - gh - 8, { color: P.faint, size: 10 });
      if (st.hist.length > 1) {
        const mx = Math.max(s.unbounded ? 10 : s.cap, ...st.hist.map(h => h[1]));
        ctx.beginPath();
        st.hist.forEach(([, v], i) => { const x = gx + gw * i / 239, y = gy - gh * v / mx; i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
        ctx.strokeStyle = P.accent; ctx.lineWidth = 1.8; ctx.stroke();
        if (!s.unbounded) { ctx.save(); ctx.setLineDash([4, 4]); D.line(ctx, gx, gy - gh * s.cap / mx, gx + gw, gy - gh * s.cap / mx, P.err, 1); ctx.restore(); }
      }
      D.line(ctx, gx, gy, gx + gw, gy, P.border, 1);
    };
    reset();
  },
});

/* ======================================================== cs-tcp-window == */
defineLab('cs-tcp-window', {
  title: 'TCP’s sliding window and the bandwidth-delay product',
  hint: 'The sender may have at most <b>W</b> unacknowledged packets in flight; each ACK slides the window forward. Slowed down so one round trip takes about a second and a half. Try a small window on a long, fat link.',
  mount(L) {
    const r = rng(23);
    const s = { W: 4, rtt: 100, mbps: 100, loss: 0 };
    const c = L.canvas(w => Math.min(300, Math.max(250, w * .4)));
    L.slider('window W (packets)', { min: 1, max: 32, step: 1, value: s.W }, v => { s.W = v; update(); });
    L.slider('round-trip time (ms)', { min: 10, max: 300, step: 10, value: s.rtt }, v => { s.rtt = v; reset(); });
    L.seg('link', [[10, '10 Mbps'], [100, '100 Mbps'], [1000, '1 Gbps']], s.mbps, v => { s.mbps = v; reset(); });
    L.seg('packet loss', [[0, '0%'], [.03, '3%'], [.1, '10%']], s.loss, v => { s.loss = v; });
    const run = L.loop(dt => { tick(dt); L.redraw(); s.acc = (s.acc || 0) + dt; if (s.acc > .25) { s.acc = 0; update(); } });
    L.playButton(run, ['Send', 'Pause']);
    L.button('Reset', () => { reset(); L.redraw(); });
    let st;
    const ser = () => 12 / s.mbps;
    function reset() { st = { now: 0, base: 0, next: 0, sent: {}, pk: [], acks: [], exp: 0, got: new Set(), dup: 0, lastAck: 0, linkFree: 0, delivered: 0, retrans: 0 }; update(); }
    function send(seq, re) {
      const t0 = Math.max(st.now, st.linkFree); st.linkFree = t0 + ser();
      const lost = r() < s.loss;
      st.pk.push({ seq, t0, t1: t0 + s.rtt / 2, lost, re }); st.sent[seq] = t0;
      if (re) st.retrans++;
    }
    function tick(dt) {
      const step = dt * s.rtt / 1.5;
      const end = st.now + step;
      for (let sub = 0; sub < 20; sub++) {
        st.now += step / 20;
        while (st.next < st.base + s.W && st.linkFree <= st.now + ser()) { send(st.next, false); st.next++; }
        st.pk = st.pk.filter(p => {
          if (p.t1 > st.now) return true;
          if (p.lost) return false;
          st.got.add(p.seq);
          while (st.got.has(st.exp)) { st.exp++; st.delivered++; }
          st.acks.push({ ack: st.exp, t0: p.t1, t1: p.t1 + s.rtt / 2 });
          return false;
        });
        st.acks = st.acks.filter(a => {
          if (a.t1 > st.now) return true;
          if (a.ack > st.base) { st.base = a.ack; st.dup = 0; }
          else if (a.ack === st.lastAck && ++st.dup === 3 && st.base < st.next) send(st.base, true);
          st.lastAck = a.ack;
          return false;
        });
        if (st.base < st.next && st.now - st.sent[st.base] > 2 * s.rtt + 5) send(st.base, true);
      }
      st.now = end;
    }
    function update() {
      const bdp = s.mbps * 1e6 * s.rtt / 1e3 / (1500 * 8), limit = Math.min(s.W * 1500 * 8 / (s.rtt / 1e3) / 1e6, s.mbps);
      const meas = st.now > 0 ? st.delivered * 1500 * 8 / (st.now / 1e3) / 1e6 : 0;
      L.stats([['in flight', st.next - st.base], ['window W', s.W], ['pipe size (BDP)', `${fmtN(bdp, bdp < 10 ? 1 : 0)} packets`, 'accent'], ['max throughput W/RTT', `${fmtN(limit, 1)} Mbps`, 'accent'], ['measured', `${fmtN(meas, 1)} Mbps`], ['link used', `${limit / s.mbps < .1 ? fmtN(limit / s.mbps * 100, 1) : Math.round(limit / s.mbps * 100)}%`, limit / s.mbps < .5 ? 'err' : 'ok'], s.loss ? ['retransmits', st.retrans, 'err'] : null]);
      L.insight(`A sender can push at most W packets per round trip, so <b>throughput ≤ W / RTT</b> however fast the link is. Filling this ${s.mbps} Mbps link at ${s.rtt} ms RTT needs a window of bandwidth × RTT = <b>${fmtN(bdp, 0)} packets</b> (${fmtN(bdp * 1.5, 0)} KB) in flight. That is why the original 64 KB TCP window needed the <i>window scaling</i> option for fast long-haul links, and why a single transfer to a far-away region can be slow on a fat pipe. ${s.loss ? 'With loss, duplicate ACKs stall the window until the hole is retransmitted (three duplicates trigger fast retransmit; otherwise a timeout).' : ''}`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, sx = 90, rx = c.w - 90, top = 56, laneD = top + 40, laneA = top + 110;
      fillRR(ctx, 10, top, 70, 150, 10, P.surface2, P.series[0], 1.4); D.text(ctx, 'sender', 45, top + 16, { color: P.text, size: 11, align: 'center', weight: 700 });
      fillRR(ctx, c.w - 80, top, 70, 150, 10, P.surface2, P.series[2], 1.4); D.text(ctx, 'receiver', c.w - 45, top + 16, { color: P.text, size: 11, align: 'center', weight: 700 });
      D.line(ctx, sx, laneD, rx, laneD, P.border, 1); D.line(ctx, sx, laneA, rx, laneA, P.border, 1);
      D.text(ctx, 'data →', sx + 4, laneD - 12, { color: P.faint, size: 10 }); D.text(ctx, '← ACKs', rx - 4, laneA + 14, { color: P.faint, size: 10, align: 'right' });
      st.pk.forEach(p => {
        if (p.t0 > st.now) return;
        const f = clamp((st.now - p.t0) / (p.t1 - p.t0), 0, 1);
        if (p.lost && f > .55) { D.text(ctx, '✕', lerp(sx, rx, .55), laneD, { color: P.err, size: 14, align: 'center', weight: 700 }); return; }
        fillRR(ctx, lerp(sx, rx, f) - 11, laneD - 9, 22, 18, 3, P.alpha(p.re ? 'err' : 'accent', .8));
        D.text(ctx, p.seq, lerp(sx, rx, f), laneD, { color: P.bg, size: 9.5, align: 'center', mono: true, weight: 700 });
      });
      st.acks.forEach(a => {
        const f = clamp((st.now - a.t0) / (a.t1 - a.t0), 0, 1);
        fillRR(ctx, lerp(rx, sx, f) - 13, laneA - 8, 26, 16, 8, P.alpha(P.series[2], .75));
        D.text(ctx, a.ack, lerp(rx, sx, f), laneA, { color: P.bg, size: 9, align: 'center', mono: true, weight: 700 });
      });
      const cells = Math.min(40, Math.floor((c.w - 40) / 20)), start = Math.max(0, st.base - 6), cw = (c.w - 40) / cells, y = 16;
      D.text(ctx, 'sequence numbers', 20, 8, { color: P.faint, size: 9.5 });
      for (let k = 0; k < cells; k++) {
        const q = start + k, x = 20 + k * cw;
        const state = q < st.base ? 'acked' : q < st.next ? 'flight' : q < st.base + s.W ? 'ready' : 'wait';
        const col = { acked: P.alpha('ok', .55), flight: P.alpha('accent', .6), ready: P.alpha('accent', .15), wait: P.surface2 }[state];
        fillRR(ctx, x + 1, y, cw - 2, 20, 3, col, P.border, .8);
        if (cw > 16) D.text(ctx, q, x + cw / 2, y + 10, { color: state === 'wait' ? P.faint : P.text, size: 8.5, align: 'center', mono: true });
      }
      const wx0 = 20 + (st.base - start) * cw, wx1 = wx0 + s.W * cw;
      fillRR(ctx, wx0 - 1, y - 4, Math.min(wx1, c.w - 18) - wx0 + 2, 28, 5, null, P.accent, 2.2);
      D.text(ctx, `window (W = ${s.W})`, wx0, y + 34, { color: P.accent, size: 10, weight: 700 });
      D.text(ctx, `delivered in order: ${st.delivered}`, c.w - 10, top + 166, { color: P.dim, size: 10, align: 'right', mono: true });
    };
    reset();
  },
});

/* ========================================================= cs-isolation == */
defineLab('cs-isolation', {
  title: 'Isolation levels vs. the five classic anomalies',
  hint: 'Two transactions run interleaved, one statement at a time. Pick an anomaly and an isolation level, then step through and see what each SELECT returns, whether the database stops it, and how. The engine is a small MVCC model of PostgreSQL.',
  mount(L) {
    const LEVELS = [['RU', 'Read uncommitted'], ['RC', 'Read committed'], ['RR', 'Repeatable read (snapshot)'], ['SER', 'Serializable']];
    const SC = {
      dirty: {
        name: 'Dirty read', init: { 'acct:A': 100 },
        story: 'T1 zeroes an account but then rolls back. Does T2 ever see the 0?',
        steps: [
          [1, () => "UPDATE accounts SET balance = 0 WHERE id = 'A'", (x, T) => x.write(T, 'acct:A', 0)],
          [2, () => "SELECT balance FROM accounts WHERE id = 'A'", (x, T) => x.read(T, 'acct:A', 'seen')],
          [1, () => 'ROLLBACK', (x, T) => x.rollback(T)],
          [2, () => 'COMMIT', (x, T) => x.commit(T)],
        ],
        bad: v => v.seen[2] === 0, badText: 'T2 read a balance of 0 that never existed: T1 rolled it back.',
      },
      nonrep: {
        name: 'Non-repeatable read', init: { 'acct:A': 100 },
        story: 'T1 reads the same row twice while T2 changes it in between.',
        steps: [
          [1, () => "SELECT balance FROM accounts WHERE id = 'A'", (x, T) => x.read(T, 'acct:A', 'first')],
          [2, () => "UPDATE accounts SET balance = 50 WHERE id = 'A'", (x, T) => x.write(T, 'acct:A', 50)],
          [2, () => 'COMMIT', (x, T) => x.commit(T)],
          [1, () => "SELECT balance FROM accounts WHERE id = 'A'", (x, T) => x.read(T, 'acct:A', 'second')],
          [1, () => 'COMMIT', (x, T) => x.commit(T)],
        ],
        bad: v => v.first[1] !== v.second[1], badText: 'The same SELECT inside one transaction returned two different answers.',
      },
      phantom: {
        name: 'Phantom', init: { 'emp:1': 'eng', 'emp:2': 'eng', 'emp:3': 'sales', 'emp:4': 'eng' },
        story: 'T1 counts rows matching a condition twice; T2 inserts a new matching row in between.',
        steps: [
          [1, () => "SELECT count(*) FROM staff WHERE dept = 'eng'", (x, T) => x.count(T, 'emp:', 'eng', 'c1')],
          [2, () => "INSERT INTO staff VALUES (5, 'eng')", (x, T) => x.write(T, 'emp:5', 'eng')],
          [2, () => 'COMMIT', (x, T) => x.commit(T)],
          [1, () => "SELECT count(*) FROM staff WHERE dept = 'eng'", (x, T) => x.count(T, 'emp:', 'eng', 'c2')],
          [1, () => 'COMMIT', (x, T) => x.commit(T)],
        ],
        bad: v => v.c1[1] !== v.c2[1], badText: 'A row appeared between two identical queries: a phantom.',
      },
      lost: {
        name: 'Lost update', init: { 'item:7': 10 },
        story: 'Two checkouts each read the stock, subtract one in application code, and write it back.',
        steps: [
          [1, () => 'SELECT stock FROM items WHERE id = 7', (x, T) => x.read(T, 'item:7', 'r1')],
          [2, () => 'SELECT stock FROM items WHERE id = 7', (x, T) => x.read(T, 'item:7', 'r2')],
          [1, v => `UPDATE items SET stock = ${v.r1 ? v.r1[1] - 1 : '?'} WHERE id = 7`, (x, T, v) => x.write(T, 'item:7', v.r1[1] - 1)],
          [1, () => 'COMMIT', (x, T) => x.commit(T)],
          [2, v => `UPDATE items SET stock = ${v.r2 ? v.r2[2] - 1 : '?'} WHERE id = 7`, (x, T, v) => x.write(T, 'item:7', v.r2[2] - 1)],
          [2, () => 'COMMIT', (x, T) => x.commit(T)],
        ],
        bad: (v, x) => x.committed('item:7') === 9 && x.txn[2].status === 'committed', badText: 'Two items were sold but stock only fell by one: T2 overwrote T1’s write.',
      },
      skew: {
        name: 'Write skew', init: { 'doc:alice': 'on', 'doc:bob': 'on' },
        story: 'Rule: at least one doctor must stay on call. Alice and Bob both check, see two on call, and each goes off call.',
        steps: [
          [1, () => "SELECT count(*) FROM doctors WHERE on_call   -- Alice checks", (x, T) => x.count(T, 'doc:', 'on', 'a')],
          [2, () => "SELECT count(*) FROM doctors WHERE on_call   -- Bob checks", (x, T) => x.count(T, 'doc:', 'on', 'b')],
          [1, () => "UPDATE doctors SET on_call = false WHERE name = 'alice'", (x, T) => x.write(T, 'doc:alice', 'off')],
          [2, () => "UPDATE doctors SET on_call = false WHERE name = 'bob'", (x, T) => x.write(T, 'doc:bob', 'off')],
          [1, () => 'COMMIT', (x, T) => x.commit(T)],
          [2, () => 'COMMIT', (x, T) => x.commit(T)],
        ],
        bad: (v, x) => x.committed('doc:alice') === 'off' && x.committed('doc:bob') === 'off', badText: 'Both went off call. Each transaction was valid alone; together they broke the rule. Snapshot isolation does not prevent this.',
      },
    };
    const s = { sc: 'lost', lv: 'RC', i: 0 };
    L.stage.innerHTML = '<div class="iso"></div>';
    const root = L.stage.querySelector('.iso');
    L.seg('anomaly', Object.entries(SC).map(([k, v]) => [k, v.name]), s.sc, v => { s.sc = v; reset(); });
    L.seg('isolation level', LEVELS, s.lv, v => { s.lv = v; reset(); });
    L.button('Next statement', () => step(), 'primary');
    L.button('Run to the end', () => { while (step(true)); render(); });
    L.button('Reset', () => reset());

    function engine(sc, lv) {
      const x = { seq: 0, v: {}, vals: {}, txn: { 1: { id: 1, snap: null, status: 'active', reads: new Set(), writes: new Set() }, 2: { id: 2, snap: null, status: 'active', reads: new Set(), writes: new Set() } } };
      Object.entries(sc.init).forEach(([k, val]) => { x.v[k] = [{ val, by: 0, state: 'committed', seq: 0 }]; });
      const touch = T => { if ((lv === 'RR' || lv === 'SER') && T.snap == null) T.snap = x.seq; };
      const lastC = k => [...(x.v[k] || [])].reverse().find(v => v.state === 'committed');
      x.committed = k => (lastC(k) || {}).val;
      x.visible = (T, k) => {
        const vs = x.v[k] || [], own = [...vs].reverse().find(v => v.by === T.id && v.state === 'pending');
        if (own) return own;
        if (lv === 'RU') return [...vs].reverse().find(v => v.state !== 'aborted');
        if (lv === 'RC') return lastC(k);
        return [...vs].reverse().find(v => v.state === 'committed' && v.seq <= T.snap);
      };
      x.abort = (T, why) => { T.status = 'aborted'; Object.values(x.v).forEach(vs => vs.forEach(v => { if (v.by === T.id && v.state === 'pending') v.state = 'aborted'; })); return { err: why }; };
      x.read = (T, k, name) => { touch(T); T.reads.add(k); const v = x.visible(T, k); x.vals[name] = { ...(x.vals[name] || {}), [T.id]: v ? v.val : null }; return { out: v ? String(v.val) : '(no row)', why: v && v.state === 'pending' && v.by !== T.id ? 'uncommitted data from the other transaction' : '' }; };
      x.count = (T, pre, want, name) => {
        touch(T); T.reads.add(pre + '*');
        const n = Object.keys(x.v).filter(k => k.startsWith(pre)).filter(k => { const v = x.visible(T, k); return v && v.val === want; }).length;
        x.vals[name] = { ...(x.vals[name] || {}), [T.id]: n };
        return { out: String(n) };
      };
      x.write = (T, k, val) => {
        touch(T);
        const lc = lastC(k);
        if ((lv === 'RR' || lv === 'SER') && lc && lc.seq > T.snap) return x.abort(T, 'ERROR: could not serialize access due to concurrent update');
        (x.v[k] = x.v[k] || []).push({ val, by: T.id, state: 'pending' }); T.writes.add(k);
        return { out: k.startsWith('emp:') ? 'INSERT 0 1' : 'UPDATE 1' };
      };
      const hits = (reads, writes) => [...reads].some(r => [...writes].some(w => r === w || (r.endsWith('*') && w.startsWith(r.slice(0, -1)))));
      x.commit = T => {
        if (lv === 'SER') {
          const U = x.txn[T.id === 1 ? 2 : 1];
          if (U.status === 'committed' && hits(T.reads, U.writes) && hits(U.reads, T.writes))
            return x.abort(T, 'ERROR: could not serialize access due to read/write dependencies among transactions');
        }
        x.seq++; Object.values(x.v).forEach(vs => vs.forEach(v => { if (v.by === T.id && v.state === 'pending') { v.state = 'committed'; v.seq = x.seq; } }));
        T.status = 'committed'; return { out: 'COMMIT' };
      };
      x.rollback = T => { x.abort(T); return { out: 'ROLLBACK' }; };
      return x;
    }
    function play(scKey, lv, upto) {
      const sc = SC[scKey], x = engine(sc, lv), log = [];
      sc.steps.slice(0, upto).forEach(([t, sql, fn]) => {
        const T = x.txn[t], text = sql(x.vals);
        if (T.status === 'aborted') { log.push({ t, sql: text, res: { skip: true } }); return; }
        log.push({ t, sql: text, res: fn(x, T, x.vals) });
      });
      return { x, log, bad: upto >= sc.steps.length ? !!sc.bad(x.vals, x) : null };
    }
    const matrix = {};
    Object.keys(SC).forEach(k => { matrix[k] = {}; LEVELS.forEach(([lv]) => { matrix[k][lv] = play(k, lv, 99).bad; }); });
    function reset() { s.i = 0; render(); }
    function step(quiet) { if (s.i >= SC[s.sc].steps.length) return false; s.i++; if (!quiet) render(); return true; }
    function render() {
      const sc = SC[s.sc], run = play(s.sc, s.lv, s.i), fin = s.i >= sc.steps.length;
      const why = {
        RU: 'Reads see other transactions’ uncommitted writes.',
        RC: 'Each statement sees the data committed before <i>that statement</i> began.',
        RR: 'The whole transaction reads one snapshot taken at its first statement; writing a row someone else changed after that snapshot is an error.',
        SER: 'Snapshot isolation plus tracking of read/write dependencies (SSI): if the interleaving could not have happened one-at-a-time, one transaction is aborted.',
      };
      const errStep = run.log.find(e => e.res && e.res.err);
      let verdict = '';
      if (fin) verdict = run.bad
        ? `<div class="iso-verdict bad"><b>Anomaly.</b> ${sc.badText}</div>`
        : `<div class="iso-verdict ok"><b>Prevented.</b> ${errStep ? `T${errStep.t} was aborted with <code>${escH(errStep.res.err.replace('ERROR: ', ''))}</code>. The application must catch this and <b>retry the transaction</b> — at Repeatable Read and Serializable that retry loop is part of the contract.` : `${why[s.lv]}`}</div>`;
      const rows = Object.keys(run.x.v).map(k => {
        const vs = run.x.v[k], c = [...vs].reverse().find(v => v.state === 'committed'), p = vs.filter(v => v.state === 'pending');
        return `<tr><td><code>${escH(k)}</code></td><td>${c ? escH(c.val) : '—'}</td><td>${p.map(v => `<span class="iso-pend t${v.by}">T${v.by}: ${escH(v.val)}</span>`).join(' ') || ''}</td></tr>`;
      }).join('');
      root.innerHTML = `
        <p class="iso-story">${escH(sc.story)} <span class="iso-lv">${escH(LEVELS.find(l => l[0] === s.lv)[1])}:</span> ${why[s.lv]}</p>
        <div class="iso-grid">
          <div class="iso-steps">
            <div class="iso-row iso-headrow"><span>T1</span><span>T2</span></div>
            ${sc.steps.map(([t, sql], i) => {
              const e = run.log[i], text = e ? e.sql : sql(run.x.vals);
              const res = !e ? '' : e.res.skip ? '<em>skipped: transaction already aborted</em>' : e.res.err ? `<b class="err">${escH(e.res.err)}</b>` : `→ ${escH(e.res.out)}${e.res.why ? ` <em class="warn">(${e.res.why})</em>` : ''}`;
              const cell = `<div class="iso-cell t${t}${e ? ' done' : ''}${i === s.i ? ' next' : ''}"><code>${escH(text)}</code>${res ? `<div class="iso-res">${res}</div>` : ''}</div>`;
              return `<div class="iso-row">${t === 1 ? cell + '<div></div>' : '<div></div>' + cell}</div>`;
            }).join('')}
          </div>
          <div class="iso-db">
            <div class="iso-dbh">Database</div>
            <table><thead><tr><th>row</th><th>committed</th><th>pending</th></tr></thead><tbody>${rows}</tbody></table>
            <div class="iso-tx">${[1, 2].map(t => `<span class="t${t}">T${t}: ${run.x.txn[t].status}${run.x.txn[t].snap != null ? ' · snapshot taken' : ''}</span>`).join('')}</div>
          </div>
        </div>
        ${verdict}
        <table class="iso-matrix"><thead><tr><th>anomaly</th>${LEVELS.map(([k, n]) => `<th class="${k === s.lv ? 'on' : ''}">${escH(n.replace(' (snapshot)', ''))}</th>`).join('')}</tr></thead>
        <tbody>${Object.entries(SC).map(([k, v]) => `<tr class="${k === s.sc ? 'on' : ''}"><td>${escH(v.name)}</td>${LEVELS.map(([lv]) => `<td class="${matrix[k][lv] ? 'bad' : 'ok'}${k === s.sc && lv === s.lv ? ' cur' : ''}">${matrix[k][lv] ? 'happens' : 'prevented'}</td>`).join('')}</tr>`).join('')}</tbody></table>
        <p class="iso-note">Every cell above is computed by running the same engine. PostgreSQL treats READ UNCOMMITTED as READ COMMITTED, so the first column shows the ANSI meaning. MySQL/InnoDB differs at Repeatable Read: its UPDATE reads the latest committed row instead of raising an error, so the lost-update scenario is <b>not</b> prevented there. At any level, <code>UPDATE … SET stock = stock - 1</code> or <code>SELECT … FOR UPDATE</code> avoids the lost update, and a constraint or <code>FOR UPDATE</code> on the rows read fixes write skew.</p>`;
      L.stats([['statement', `${s.i} / ${sc.steps.length}`], fin ? ['result', run.bad ? 'anomaly' : 'prevented', run.bad ? 'err' : 'ok'] : null]);
    }
    reset();
  },
});
}
