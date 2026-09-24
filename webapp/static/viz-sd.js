/* ============================================================================
   System design labs, part 1 — animated architectures.
   Requires viz.js. A tiny topology engine (boxes, wires, moving packets)
   powers most of them, so each lab only describes its system and its rules.
   ========================================================================= */
'use strict';

const fnv = (str, seed = 0) => {
  let h = (2166136261 ^ seed) >>> 0;
  for (let i = 0; i < str.length; i++) { h ^= str.charCodeAt(i); h = Math.imul(h, 16777619) >>> 0; }
  h ^= h >>> 13; h = Math.imul(h, 0x5bd1e995) >>> 0; h ^= h >>> 15;
  return h >>> 0;
};
const unit = (str, seed) => fnv(str, seed) / 4294967296;
const pctl = (arr, p) => { if (!arr.length) return NaN; const s = [...arr].sort((a, b) => a - b); return s[Math.min(s.length - 1, Math.floor(p * s.length))]; };
const fmtMs = ms => !Number.isFinite(ms) ? '—' : ms >= 1000 ? `${(ms / 1000).toFixed(ms >= 10000 ? 0 : 1)} s` : `${Math.round(ms)} ms`;

/* ------------------------------------------------------ topology engine -- */
function topo(c) {
  const T = { nodes: {}, edges: [], packets: [] };
  T.node = (id, x, y, label, o = {}) => (T.nodes[id] = { id, x, y, label, w: 96, h: 44, kind: 'svc', sub: '', down: false, glow: 0, ...o });
  T.edge = (a, b, o = {}) => T.edges.push({ a, b, ...o });
  T.xy = id => { const n = T.nodes[id]; return [n.x * c.w, n.y * c.h]; };
  T.send = (path, o = {}) => { const p = { path, i: 0, t: 0, speed: 2.2, r: 5, wait: 0, ...o }; T.packets.push(p); return p; };
  T.pulse = id => { if (T.nodes[id]) T.nodes[id].glow = 1; };
  T.step = dt => {
    for (const p of T.packets) {
      if (p.wait > 0) { p.wait -= dt; continue; }
      p.t += dt * p.speed;
      while (p.t >= 1 && !p.done) {
        p.t -= 1; p.i++;
        p.hop?.(p.path[p.i], p);
        if (p.i >= p.path.length - 1) { p.done = true; p.end?.(p); }
      }
    }
    T.packets = T.packets.filter(p => !p.done);
    Object.values(T.nodes).forEach(n => { n.glow = Math.max(0, n.glow - dt * 2.2); });
  };
  T.busy = () => T.packets.length > 0;
  T.draw = (ctx, P) => {
    T.edges.forEach(e => {
      const [x1, y1] = T.xy(e.a), [x2, y2] = T.xy(e.b);
      D.line(ctx, x1, y1, x2, y2, e.color || P.strong, e.w || 1.5, e.dash);
      if (e.label) D.text(ctx, e.label, (x1 + x2) / 2, (y1 + y2) / 2 - 8, { color: P.faint, size: 10, align: 'center' });
    });
    T.packets.forEach(p => {
      if (p.wait > 0) return;
      const a = p.path[p.i], b = p.path[Math.min(p.i + 1, p.path.length - 1)];
      const [x1, y1] = T.xy(a), [x2, y2] = T.xy(b), x = lerp(x1, x2, p.t), y = lerp(y1, y2, p.t);
      const col = p.color || P.accent;
      D.dot(ctx, x, y, p.r + 4, P.alpha(col, .22));
      D.dot(ctx, x, y, p.r, col);
      if (p.label) D.text(ctx, p.label, x, y - p.r - 8, { color: P.text, size: 10, align: 'center', mono: true, weight: 600 });
    });
    Object.values(T.nodes).forEach(n => drawSysNode(ctx, n, P, c));
  };
  return T;
}

function drawSysNode(ctx, n, P, c) {
  const x = n.x * c.w, y = n.y * c.h, w = n.w, h = n.h;
  const stroke = n.down ? P.err : n.stroke || (n.glow > 0 ? P.mix('strong', 'accent', n.glow) : P.strong);
  const fill = n.down ? P.alpha('err', .1) : n.fill || P.surface2;
  ctx.save();
  if (n.glow > 0 && !n.down) { ctx.shadowColor = P.accent; ctx.shadowBlur = 18 * n.glow; }
  ctx.fillStyle = fill; ctx.strokeStyle = stroke; ctx.lineWidth = n.glow > .2 ? 2.2 : 1.5;
  if (n.kind === 'db') {
    const rx = w / 2, ry = 7, top = y - h / 2 + ry, bot = y + h / 2 - ry;
    ctx.beginPath();
    ctx.moveTo(x - rx, top); ctx.lineTo(x - rx, bot);
    ctx.ellipse(x, bot, rx, ry, 0, Math.PI, 0, true);
    ctx.lineTo(x + rx, top);
    ctx.ellipse(x, top, rx, ry, 0, 0, Math.PI, true);
    ctx.closePath(); ctx.fill(); ctx.stroke();
    ctx.shadowBlur = 0;
    ctx.beginPath(); ctx.ellipse(x, top, rx, ry, 0, 0, TAU); ctx.stroke();
  } else if (n.kind === 'client') {
    D.rrect(ctx, x - w / 2, y - h / 2, w, h, h / 2); ctx.fill(); ctx.stroke();
  } else if (n.kind === 'round') {
    ctx.beginPath(); ctx.arc(x, y, w / 2, 0, TAU); ctx.fill(); ctx.stroke();
  } else {
    D.rrect(ctx, x - w / 2, y - h / 2, w, h, 10); ctx.fill(); ctx.stroke();
    if (n.kind === 'queue') for (let i = 1; i < 5; i++) D.line(ctx, x - w / 2 + i * w / 5, y - h / 2 + 5, x - w / 2 + i * w / 5, y + h / 2 - 5, P.alpha('strong', .6), 1);
  }
  ctx.restore();
  if (n.load != null) {
    const bw = w - 16, frac = clamp(n.load, 0, 1);
    ctx.fillStyle = P.alpha('faint', .2); D.rrect(ctx, x - bw / 2, y + h / 2 - 9, bw, 4, 2); ctx.fill();
    ctx.fillStyle = n.load > .95 ? P.err : n.load > .7 ? P.series[1] : P.ok; D.rrect(ctx, x - bw / 2, y + h / 2 - 9, bw * frac, 4, 2); ctx.fill();
  }
  const ty = n.sub ? y - 7 : y;
  D.text(ctx, n.label, x, ty, { color: n.down ? P.err : n.labelColor || P.text, size: n.size || 12, align: 'center', weight: 650 });
  if (n.sub) D.text(ctx, n.sub, x, y + 9, { color: n.subColor || P.faint, size: 10, align: 'center', mono: true });
  if (n.down) D.text(ctx, '✕', x + w / 2 - 8, y - h / 2 + 8, { color: P.err, size: 12, align: 'center', weight: 700 });
  if (n.badge) {
    D.font(ctx, 10, 700);
    const tw = ctx.measureText(n.badge).width + 12;
    ctx.fillStyle = n.badgeColor || P.accent; D.rrect(ctx, x - tw / 2, y - h / 2 - 20, tw, 16, 8); ctx.fill();
    D.text(ctx, n.badge, x, y - h / 2 - 12, { color: P.surface, size: 10, align: 'center', weight: 700 });
  }
}

/* a tiny event scheduler in simulated seconds, for labs driven by timers */
function simClock() {
  const S = { now: 0, q: [] };
  S.at = (t, fn) => { S.q.push({ t, fn }); S.q.sort((a, b) => a.t - b.t); };
  S.after = (d, fn) => S.at(S.now + d, fn);
  S.advance = dt => { S.now += dt; while (S.q.length && S.q[0].t <= S.now) S.q.shift().fn(); };
  S.clear = () => { S.q = []; };
  return S;
}

/* ==================================================== 1 · request path == */
defineLab('sd-request', {
  title: 'Follow a request through the stack',
  hint: 'Send requests and watch every hop add latency. Toggle the CDN, change the cache hit ratio, or take a server down.',
  mount(L) {
    const c = L.canvas(w => Math.min(360, Math.max(300, w * .5)));
    const T = topo(c);
    T.node('client', .07, .52, 'Browser', { kind: 'client', w: 76 });
    T.node('dns', .22, .14, 'DNS', { w: 64 });
    T.node('cdn', .25, .52, 'CDN edge', { w: 82 });
    T.node('lb', .44, .52, 'Load balancer', { w: 106 });
    T.node('app1', .63, .27, 'App server 1', { w: 102 });
    T.node('app2', .63, .77, 'App server 2', { w: 102 });
    T.node('cache', .88, .2, 'Cache', { w: 80 });
    T.node('db', .88, .7, 'Database', { kind: 'db', w: 86, h: 52 });
    T.edge('client', 'dns', { dash: [4, 4] });
    [['client', 'cdn'], ['cdn', 'lb'], ['lb', 'app1'], ['lb', 'app2'], ['app1', 'cache'], ['app2', 'cache'], ['app1', 'db'], ['app2', 'db']].forEach(([a, b]) => T.edge(a, b));
    const r = rng(8);
    const s = { kind: 'read', cdn: true, hit: .8, down: false, detected: false, dns: false, rr: 0, lats: [], last: null, hits: 0, reads: 0, queue: 0, gap: 0 };
    L.seg('request', [['static', 'Static image'], ['read', 'API read'], ['write', 'API write']], s.kind, v => { s.kind = v; });
    L.slider('cache hit ratio', { min: 0, max: 1, step: .05, value: s.hit, fmt: v => `${Math.round(v * 100)}%` }, v => { s.hit = v; });
    const run = L.loop(dt => {
      if (s.queue > 0 && (s.gap -= dt) <= 0) { s.queue--; s.gap = .35; fire(); }
      T.step(dt); L.redraw();
      if (!T.busy() && s.queue <= 0) return false;
    });
    L.button('Send one request', () => { fire(); run.start(); }, 'primary');
    L.button('Send 20 requests', () => { s.queue = 20; run.start(); });
    L.toggle('CDN', s.cdn, v => { s.cdn = v; });
    L.toggle('App server 1 down', s.down, v => { s.down = v; s.detected = false; T.nodes.app1.down = v; L.redraw(); });
    L.button('Reset stats', () => { s.lats = []; s.hits = 0; s.reads = 0; s.dns = false; s.last = null; update(); });

    function fire() {
      const segs = [], path = ['client'];
      const hop = (to, ms, label) => { path.push(to); segs.push([label, ms]); };
      if (!s.dns) { hop('dns', 25, 'DNS lookup'); hop('client', 0, ''); s.dns = true; }
      let note = '';
      if (s.kind === 'static') {
        if (s.cdn) {
          hop('cdn', 12, 'to nearby edge');
          if (r() < .95) { note = 'CDN hit: served from the edge, the origin never saw it.'; finish(path, segs, note, 'cdn'); return; }
          hop('lb', 55, 'edge → origin'); note = 'CDN miss: the edge fetched from origin and will cache it.';
        } else { hop('cdn', 0, ''); path.pop(); segs.pop(); hop('lb', 85, 'long haul to origin'); note = 'No CDN: every image crosses the ocean to your origin.'; }
        const app = pickApp(path, segs);
        hop('db', 6, 'read object'); path.push(app); segs.push(['', 0]);
        finish(path, segs, note, app); return;
      }
      if (s.cdn) { hop('cdn', 12, 'to nearby edge'); hop('lb', 40, 'edge → origin backbone'); } else hop('lb', 85, 'long haul to origin');
      const app = pickApp(path, segs);
      if (s.kind === 'read') {
        s.reads++;
        hop('cache', 1, 'cache lookup');
        if (r() < s.hit) { s.hits++; note = 'Cache hit: the database was never touched.'; path.push(app); segs.push(['', 0]); }
        else { path.push(app); segs.push(['', 0]); hop('db', 9, 'cache miss → DB query'); path.push(app); segs.push(['', 0]); hop('cache', 1, 'write back to cache'); path.push(app); segs.push(['', 0]); note = 'Cache miss: query the database, then populate the cache.'; }
      } else {
        hop('db', 14, 'write + commit'); path.push(app); segs.push(['', 0]);
        hop('cache', 1, 'invalidate key'); path.push(app); segs.push(['', 0]);
        note = 'Writes go to the source of truth, then invalidate the cached copy.';
      }
      finish(path, segs, note, app);
    }
    function pickApp(path, segs) {
      let app = s.rr++ % 2 ? 'app2' : 'app1';
      if (s.down && app === 'app1') {
        if (!s.detected) {
          s.detected = true;
          path.push('app1'); segs.push(['timeout on dead server', 1000]); path.push('lb'); segs.push(['retry', 1]);
        }
        app = 'app2';
      }
      path.push(app); segs.push(['LB → app', 1]);
      segs.push(['app work', 4]);
      return app;
    }
    function finish(path, segs, note, served) {
      const back = path.slice(0, -1).reverse().filter((n, i, a) => i === 0 || n !== a[i - 1]);
      const forward = [...path];
      const full = [...forward, ...back.slice(back[0] === forward[forward.length - 1] ? 1 : 0)];
      const oneWay = segs.reduce((a, [, ms]) => a + ms, 0);
      const total = oneWay + segs.filter(([l]) => /edge|origin|haul|nearby/.test(l)).reduce((a, [, ms]) => a + ms, 0);
      const color = s.kind === 'write' ? L.P.series[1] : s.kind === 'static' ? L.P.series[4] : L.P.accent;
      T.send(full, { speed: 3.2, color, hop: id => T.pulse(id), end: () => { s.lats.push(total); s.last = { total, segs: segs.filter(([l, ms]) => l && ms), note, served }; update(); L.redraw(); } });
    }
    function update() {
      const l = s.last;
      L.stats([['last request', l ? fmtMs(l.total) : '—', 'accent'], ['p50', fmtMs(pctl(s.lats, .5))], ['p99', fmtMs(pctl(s.lats, .99)), pctl(s.lats, .99) > 500 ? 'err' : ''], s.reads && ['cache hits', `${s.hits} of ${s.reads}`], ['requests', s.lats.length]]);
      L.insight(!l ? '<b>Press “Send one request”.</b> The first request also pays for a DNS lookup; after that the answer is cached.'
        : l.segs.some(([lbl]) => /timeout/.test(lbl)) ? '<b>The load balancer sent this request to a dead server</b> and waited a full second before retrying. Health checks remove the server from rotation, but until they fire, real users pay the timeout. That one slow request is what your p99 shows.'
        : `<b>${fmtMs(l.total)}.</b> ${l.note} ${!s.cdn && s.kind !== 'write' ? 'The long-haul round trip dominates everything else; that is what CDNs remove.' : ''}`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      T.draw(ctx, P);
      const l = s.last;
      if (l && l.segs.length) {
        const y = c.h - 18, total = l.segs.reduce((a, [, ms]) => a + ms, 0), x0 = 12, W = c.w - 24;
        let x = x0;
        l.segs.forEach(([lbl, ms], i) => {
          const w = Math.max(3, ms / total * W);
          ctx.fillStyle = /timeout/.test(lbl) ? P.err : P.alpha(P.series[i % 6], .8);
          D.rrect(ctx, x, y - 8, w - 2, 14, 4); ctx.fill();
          if (w > 70) D.text(ctx, `${lbl} ${ms}ms`, x + 5, y - 1, { color: P.surface, size: 9.5, weight: 650 });
          x += w;
        });
        D.text(ctx, 'one-way latency breakdown', x0, y - 16, { color: P.faint, size: 10 });
      }
    };
    update();
  },
});

/* ================================================= 2 · load balancing == */
defineLab('sd-lb', {
  title: 'Load-balancing algorithms under pressure',
  hint: 'Requests arrive at random. One server can be slow. Compare how each algorithm spreads the queueing.',
  mount(L) {
    const r = rng(21);
    const N = 4;
    const s = { algo: 'rr', load: .75, slow: true, servers: [], lats: [], rr: 0, acc: 0, fly: [] };
    const c = L.canvas(w => Math.min(320, w * .5));
    L.seg('algorithm', [['rr', 'Round robin'], ['random', 'Random'], ['least', 'Least connections'], ['p2c', 'Power of two choices']], s.algo, v => { s.algo = v; reset(); });
    L.slider('traffic (% of total capacity)', { min: .3, max: .98, step: .01, value: s.load, fmt: v => `${Math.round(v * 100)}%` }, v => { s.load = v; });
    L.toggle('Server 3 is slow (half speed)', s.slow, v => { s.slow = v; reset(); });
    const run = L.loop(dt => { for (let i = 0; i < 3; i++) tick(dt / 1.2); L.redraw(); if ((s.acc += dt) > .4) { s.acc = 0; update(); } });
    L.playButton(run, ['Run traffic', 'Pause']);
    L.button('Reset', () => reset());
    const expo = rate => -Math.log(1 - r()) / rate;
    function reset() {
      s.servers = Array.from({ length: N }, (_, i) => ({ mu: s.slow && i === 2 ? 5 : 10, q: [], busy: null, done: 0 }));
      s.lats = []; s.rr = 0; s.t = 0; s.nextArrival = 0; s.fly = [];
      update(); L.redraw();
    }
    function pick() {
      const out = i => s.servers[i].q.length + (s.servers[i].busy ? 1 : 0);
      if (s.algo === 'rr') return s.rr++ % N;
      if (s.algo === 'random') return Math.floor(r() * N);
      if (s.algo === 'least') { let best = 0; for (let i = 1; i < N; i++) if (out(i) < out(best) || (out(i) === out(best) && r() < .5)) best = i; return best; }
      const a = Math.floor(r() * N); let b = Math.floor(r() * (N - 1)); if (b >= a) b++;
      return out(a) <= out(b) ? a : b;
    }
    function tick(dt) {
      s.t += dt;
      const cap = s.servers.reduce((a, sv) => a + sv.mu, 0), lam = s.load * cap;
      while (s.nextArrival <= s.t) {
        const i = pick();
        s.servers[i].q.push(s.nextArrival);
        s.fly.push({ i, t: 0 });
        s.nextArrival += expo(lam);
      }
      s.servers.forEach(sv => {
        if (sv.busy && s.t >= sv.busy.end) { s.lats.push((s.t - sv.busy.arrive) * 1000); sv.done++; sv.busy = null; }
        if (!sv.busy && sv.q.length) { const arrive = sv.q.shift(); sv.busy = { arrive, end: s.t + expo(sv.mu) }; }
      });
      if (s.lats.length > 600) s.lats.splice(0, s.lats.length - 600);
      s.fly.forEach(f => { f.t += dt * 3; });
      s.fly = s.fly.filter(f => f.t < 1);
    }
    function update() {
      const p50 = pctl(s.lats, .5), p99 = pctl(s.lats, .99), qs = s.servers.map(sv => sv.q.length + (sv.busy ? 1 : 0));
      L.stats([['p50 latency', fmtMs(p50)], ['p99 latency', fmtMs(p99), p99 > 2000 ? 'err' : 'accent'], ['queue lengths', qs.join(' · ')]]);
      const names = { rr: 'Round robin', random: 'Random', least: 'Least connections', p2c: 'Power of two choices' };
      L.insight(!s.lats.length ? '<b>Press “Run traffic”.</b> Each server handles about 10 requests per second; the slow one handles 5.'
        : (s.algo === 'rr' || s.algo === 'random') && s.slow ? `<b>${names[s.algo]} ignores how busy a server is.</b> The slow server gets its equal share, its queue grows without bound, and every request routed there waits. That queue is your p99.`
        : s.algo === 'p2c' ? '<b>Power of two choices:</b> sample two servers at random and pick the less busy one. Nearly as good as least connections, but it needs no global view, so it works with many load balancers that don’t share state.'
        : `<b>${names[s.algo]} steers work away from backed-up servers</b>, so queues stay short even with a slow machine in the pool.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, lbx = c.w * .12, lby = c.h / 2, sx = c.w * .5;
      const sy = i => c.h * (i + .5) / N;
      ctx.fillStyle = P.surface2; D.rrect(ctx, lbx - 48, lby - 24, 96, 48, 10); ctx.fill(); ctx.strokeStyle = P.accent; ctx.lineWidth = 1.5; ctx.stroke();
      D.text(ctx, 'Load balancer', lbx, lby, { color: P.text, size: 12, align: 'center', weight: 650 });
      s.servers.forEach((sv, i) => {
        const y = sy(i);
        D.line(ctx, lbx + 48, lby, sx - 60, y, P.strong, 1.2);
        const n = sv.q.length + (sv.busy ? 1 : 0), util = Math.min(1, n / 10);
        ctx.fillStyle = P.surface2; D.rrect(ctx, sx - 60, y - 22, 120, 44, 10); ctx.fill();
        ctx.strokeStyle = n > 12 ? P.err : P.strong; ctx.stroke();
        D.text(ctx, `Server ${i + 1}${sv.mu < 10 ? ' (slow)' : ''}`, sx, y - 7, { color: sv.mu < 10 ? P.series[1] : P.text, size: 11.5, align: 'center', weight: 650 });
        D.text(ctx, `${sv.mu} req/s`, sx, y + 9, { color: P.faint, size: 10, align: 'center', mono: true });
        const qx = sx + 70, cell = Math.min(14, (c.w - qx - 50) / 22);
        for (let k = 0; k < Math.min(n, 22); k++) {
          ctx.fillStyle = k === 0 && sv.busy ? P.ok : n > 12 ? P.alpha('err', .75) : P.alpha('accent', .75);
          D.rrect(ctx, qx + k * (cell + 2), y - cell / 2, cell, cell, 3); ctx.fill();
        }
        if (n > 22) D.text(ctx, `+${n - 22}`, qx + 22 * (cell + 2) + 4, y, { color: P.err, size: 11, weight: 700 });
        void util;
      });
      s.fly.forEach(f => D.dot(ctx, lerp(lbx + 48, sx - 60, f.t), lerp(lby, sy(f.i), f.t), 4, P.accent));
    };
    reset();
  },
});

/* ============================================== 3 · consistent hashing == */
defineLab('sd-ring', {
  title: 'Consistent hashing: add a server, move few keys',
  hint: 'Dots on the ring are keys, colored by the server that owns them. Add or remove a server and count how many keys have to move.',
  mount(L, opts) {
    const KEYS = Array.from({ length: 120 }, (_, i) => `user:${i * 7919 % 10007}`);
    const NAMES = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
    const s = { mode: opts.mode || 'ring', n: 4, v: 16, owners: null, moved: new Set(), lastMoved: null, flash: 0 };
    const c = L.canvas(w => Math.min(360, w * .56));
    L.seg('method', [['ring', 'Consistent hashing'], ['mod', 'hash(key) mod N']], s.mode, m => { s.mode = m; recompute(true); });
    L.slider('virtual nodes per server', { min: 1, max: 64, step: 1, value: s.v }, v => { s.v = v; recompute(true); });
    L.button('Add a server', () => { if (s.n < 8) { s.n++; recompute(); } }, 'primary');
    L.button('Remove a server', () => { if (s.n > 2) { s.n--; recompute(); } });
    const vnodes = () => {
      const list = [];
      for (let i = 0; i < s.n; i++) for (let k = 0; k < (s.mode === 'ring' ? s.v : 1); k++) list.push({ pos: unit(`${NAMES[i]}#${k}`, 3), owner: i });
      return list.sort((a, b) => a.pos - b.pos);
    };
    const owner = (key, vn) => {
      if (s.mode === 'mod') return fnv(key, 9) % s.n;
      const p = unit(key, 1);
      return (vn.find(v => v.pos >= p) || vn[0]).owner;
    };
    function recompute(silent) {
      const vn = vnodes(), next = KEYS.map(k => owner(k, vn));
      if (s.owners && !silent) {
        s.moved = new Set(KEYS.map((_, i) => i).filter(i => s.owners[i] !== next[i]));
        s.lastMoved = s.moved.size;
        s.flash = 1;
        L.tween(1400, t => { s.flash = 1 - t; L.redraw(); });
      } else { s.moved = new Set(); s.lastMoved = null; }
      s.owners = next;
      const counts = Array.from({ length: s.n }, (_, i) => next.filter(o => o === i).length);
      const avg = KEYS.length / s.n, worst = Math.max(...counts) / avg;
      L.stats([['servers', s.n], s.lastMoved != null && ['keys moved', `${s.lastMoved} of ${KEYS.length} (${Math.round(s.lastMoved / KEYS.length * 100)}%)`, 'accent'], ['ideal', `≈ ${Math.round(100 / s.n)}%`], ['busiest / average', `${fmtN(worst, 2)}×`, worst > 1.5 ? 'err' : '']]);
      L.insight(s.lastMoved == null
        ? (s.mode === 'ring' ? `<b>Each server sits at ${s.v} points on the ring</b>; a key belongs to the next point clockwise. ${s.v < 4 ? 'With so few points the arcs are uneven, so one server owns far more keys. Raise the virtual nodes.' : 'Many virtual nodes even out the load.'}` : '<b>hash(key) mod N</b> spreads keys evenly, as long as N never changes. Now add a server.')
        : s.mode === 'mod' ? `<b>${Math.round(s.lastMoved / KEYS.length * 100)}% of keys moved.</b> Changing N changes almost every key’s remainder, so the whole cache goes cold or the whole database reshuffles at once.`
        : `<b>Only ${Math.round(s.lastMoved / KEYS.length * 100)}% of keys moved</b>, close to the ideal 1/N. Only keys on the arcs the new server took over change owner. That is why Dynamo, Cassandra and memcached clients use a ring.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, R = Math.min(c.h * .4, c.w * .26), cx = R + 34, cy = c.h / 2;
      ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.strokeStyle = P.strong; ctx.lineWidth = 2; ctx.stroke();
      const ang = p => p * TAU - Math.PI / 2;
      if (s.mode === 'ring') vnodes().forEach(v => {
        const a = ang(v.pos);
        D.line(ctx, cx + (R - 9) * Math.cos(a), cy + (R - 9) * Math.sin(a), cx + (R + 9) * Math.cos(a), cy + (R + 9) * Math.sin(a), P.series[v.owner], s.v > 24 ? 1.6 : 3);
      });
      KEYS.forEach((k, i) => {
        const a = ang(unit(k, 1)), rr = R - 22 - (i % 3) * 7;
        const moved = s.moved.has(i) && s.flash > 0;
        if (moved) D.dot(ctx, cx + rr * Math.cos(a), cy + rr * Math.sin(a), 4 + 8 * s.flash, P.alpha('text', .25 * s.flash));
        D.dot(ctx, cx + rr * Math.cos(a), cy + rr * Math.sin(a), moved ? 4.5 : 3.2, P.series[s.owners[i]]);
      });
      D.text(ctx, s.mode === 'ring' ? 'hash ring' : 'key → server by remainder', cx, cy, { color: P.faint, size: 11, align: 'center' });
      const bx = cx + R + 48, bw = c.w - bx - 20, rowH = Math.min(30, (c.h - 30) / 8);
      D.text(ctx, 'keys per server', bx, 14, { color: P.dim, size: 11 });
      const counts = Array.from({ length: s.n }, (_, i) => s.owners.filter(o => o === i).length), mx = Math.max(...counts, KEYS.length / s.n * 1.6);
      counts.forEach((k, i) => {
        const y = 30 + i * rowH;
        D.text(ctx, `server ${NAMES[i]}`, bx, y + rowH / 2 - 2, { color: P.series[i], size: 11, weight: 650 });
        ctx.fillStyle = P.alpha(P.series[i], .8); D.rrect(ctx, bx + 64, y + 4, (bw - 100) * k / mx, rowH - 12, 4); ctx.fill();
        D.text(ctx, String(k), bx + 70 + (bw - 100) * k / mx, y + rowH / 2 - 2, { color: P.dim, size: 10.5, mono: true });
      });
      const ideal = bx + 64 + (bw - 100) * (KEYS.length / s.n) / mx;
      D.line(ctx, ideal, 28, ideal, 30 + s.n * rowH - 6, P.faint, 1, [3, 3]);
    };
    recompute(true);
  },
});

/* ================================================= 4 · cache stampede == */
defineLab('sd-cache', {
  title: 'Cache expiry and the thundering herd',
  hint: 'Fifty hot keys, all cached with the same TTL. Watch the database load when they expire together.',
  mount(L) {
    const K = 50, CAP = 400;
    const s = { rps: 3000, ttl: 12, jitter: false, coalesce: false, t: 0, keys: [], db: [], bucket: 0, hits: 0, total: 0, over: 0 };
    const c = L.canvas(w => Math.min(330, w * .5));
    L.slider('traffic (requests/s)', { min: 500, max: 8000, step: 100, value: s.rps }, v => { s.rps = v; });
    L.slider('TTL (seconds)', { min: 4, max: 30, step: 1, value: s.ttl }, v => { s.ttl = v; reset(); });
    L.toggle('Jittered TTL (±20%)', s.jitter, v => { s.jitter = v; reset(); });
    L.toggle('Request coalescing (one refresh per key)', s.coalesce, v => { s.coalesce = v; reset(); });
    const run = L.loop(dt => { const step = dt * 3; tick(step); L.redraw(); if (s.t > 60) return false; });
    L.playButton(run, ['Run 60 seconds', 'Pause'], () => { if (s.t > 60) reset(); });
    const r = rng(5);
    function reset() {
      s.t = 0; s.db = []; s.bucket = 0; s.hits = 0; s.total = 0; s.over = 0;
      s.keys = Array.from({ length: K }, () => ({ exp: s.ttl * (s.jitter ? .8 + .4 * r() : 1), refreshUntil: -1 }));
      update(); L.redraw();
    }
    function tick(dt) {
      s.t += dt;
      const reqs = s.rps * dt;
      let dbHits = 0;
      s.keys.forEach(k => {
        const n = reqs / K;
        if (s.t < k.exp) { s.hits += n; s.total += n; return; }
        s.total += n;
        if (k.refreshUntil < 0) { k.refreshUntil = s.t + .4; dbHits += 1; }
        if (!s.coalesce) dbHits += n;
        if (s.t >= k.refreshUntil) { k.exp = s.t + s.ttl * (s.jitter ? .8 + .4 * r() : 1); k.refreshUntil = -1; }
      });
      const idx = Math.floor(s.t / .5);
      s.db[idx] = (s.db[idx] || 0) + dbHits / .5;
      if (s.db[idx] > CAP) s.over += dt;
      update();
    }
    function update() {
      const peak = Math.max(0, ...s.db.filter(Number.isFinite));
      L.stats([['cache hit ratio', s.total ? `${(s.hits / s.total * 100).toFixed(1)}%` : '—', 'accent'], ['peak DB load', `${Math.round(peak)} q/s`, peak > CAP ? 'err' : 'ok'], ['DB capacity', `${CAP} q/s`], ['seconds overloaded', s.over.toFixed(1), s.over > 0 ? 'err' : '']]);
      L.insight(!s.total ? '<b>Press Run.</b> All 50 keys were written at the same moment with the same TTL.'
        : !s.coalesce && !s.jitter && peak > CAP ? '<b>Stampede.</b> Every key expires in the same instant, and every request for a missing key goes to the database while the value is being rebuilt. The database falls over exactly when the cache needs it most.'
        : s.jitter && !s.coalesce && peak > CAP ? '<b>Jitter spreads the expiries out</b>, but each individual miss still sends every concurrent request to the database. Add coalescing.'
        : s.coalesce && !s.jitter ? '<b>Coalescing means one request rebuilds each key</b> while the rest wait for it (single-flight / a short lock). The spike shrinks to one query per key; jitter would smooth even that.'
        : '<b>Jitter plus coalescing:</b> expiries are spread out and each rebuild is done once. This is the standard defence, often combined with serving stale data while refreshing in the background.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, gridH = c.h * .34, cols = 25, cw = (c.w - 24) / cols, ch = gridH / 2;
      s.keys.forEach((k, i) => {
        const x = 12 + (i % cols) * cw, y = 18 + Math.floor(i / cols) * ch;
        const left = clamp((k.exp - s.t) / s.ttl, 0, 1), rebuilding = s.t >= k.exp;
        ctx.fillStyle = rebuilding ? P.err : P.alpha('accent', .2 + .7 * left);
        D.rrect(ctx, x + 2, y + 2, cw - 4, ch - 4, 4); ctx.fill();
      });
      D.text(ctx, 'hot keys (brightness = time left before expiry, red = expired)', 12, 8, { color: P.faint, size: 10.5 });
      const top = gridH + 30, v = D.view({ w: c.w, h: c.h - top }, { x0: 0, x1: 60, y0: 0, y1: Math.max(CAP * 1.6, ...s.db.filter(Number.isFinite)) * 1.05, pad: 8, padL: 44, padB: 20 });
      ctx.save(); ctx.translate(0, top);
      D.axes(ctx, v, P, { xTicks: [0, 15, 30, 45, 60], yTicks: [CAP], fmtY: t => `${t}`, yLabel: 'database queries/s', xLabel: 'seconds' });
      D.line(ctx, v.sx(0), v.sy(CAP), v.sx(60), v.sy(CAP), P.err, 1.3, [5, 4]);
      s.db.forEach((q, i) => {
        if (!q) return;
        ctx.fillStyle = q > CAP ? P.err : P.accent;
        ctx.fillRect(v.sx(i * .5) + .5, v.sy(q), v.sx(.5) - v.sx(0) - 1, v.sy(0) - v.sy(q));
      });
      if (s.t > 0 && s.t < 60) D.line(ctx, v.sx(s.t), v.sy(0), v.sx(s.t), v.sy(v.y1), P.faint, 1, [3, 3]);
      ctx.restore();
    };
    reset();
  },
});

/* ==================================================== 5 · replication == */
defineLab('sd-replication', {
  title: 'Leader–follower replication, lag and failover',
  hint: 'Writes go to the leader and are copied to followers. Try reading your own write from a replica, then kill the leader.',
  mount(L) {
    const c = L.canvas(w => Math.min(320, w * .5));
    const T = topo(c), S = simClock();
    T.node('client', .08, .5, 'Client', { kind: 'client', w: 74 });
    T.node('leader', .42, .5, 'Leader', { kind: 'db', w: 96, h: 56 });
    T.node('f1', .8, .22, 'Follower 1', { kind: 'db', w: 96, h: 56 });
    T.node('f2', .8, .78, 'Follower 2', { kind: 'db', w: 96, h: 56 });
    T.edge('client', 'leader'); T.edge('leader', 'f1', { dash: [5, 4] }); T.edge('leader', 'f2', { dash: [5, 4] }); T.edge('client', 'f1', { color: 'transparent' });
    const s = { mode: 'async', lag: 1.2, logs: { leader: [], f1: [], f2: [] }, leader: 'leader', seq: 0, acked: [], lost: [], stale: 0, writeLat: null, msg: '' };
    L.seg('replication', [['sync', 'Synchronous'], ['async', 'Asynchronous']], s.mode, v => { s.mode = v; });
    L.slider('replication lag (async)', { min: 0, max: 3, step: .1, value: s.lag, fmt: v => `${v.toFixed(1)} s` }, v => { s.lag = v; });
    const run = L.loop(dt => { S.advance(dt); T.step(dt); L.redraw(); if (!T.busy() && !S.q.length) { update(); return false; } });
    const send = (a, b, dur, color, label, end) => T.send([a, b], { speed: 1 / Math.max(.25, dur), color, label, end });
    const followers = () => ['leader', 'f1', 'f2'].filter(n => n !== s.leader && !T.nodes[n].down);
    L.button('Write', () => { write(); run.start(); }, 'primary');
    L.button('Write, then read from a follower', () => { write(() => S.after(.1, readReplica)); run.start(); });
    L.button('Kill the leader', () => { failover(); run.start(); });
    L.button('Reset', () => reset());
    function write(after) {
      const v = ++s.seq, t0 = S.now, ld = s.leader;
      if (T.nodes[ld].down) { s.msg = 'No leader: writes are refused until failover finishes.'; update(); return; }
      send('client', ld, .45, L.P.accent, `v${v}`, () => {
        s.logs[ld].push(v);
        const ackClient = () => send(ld, 'client', .45, L.P.ok, 'ok', () => { s.acked.push(v); s.writeLat = S.now - t0; s.msg = `Write v${v} acknowledged.`; update(); after?.(); });
        const fs = followers();
        if (s.mode === 'sync') {
          let pending = fs.length;
          if (!pending) ackClient();
          fs.forEach(f => send(ld, f, .6, L.P.series[0], `v${v}`, () => { s.logs[f].push(v); send(f, ld, .4, L.P.ok, 'ack', () => { if (--pending === 0) ackClient(); }); }));
        } else {
          ackClient();
          fs.forEach(f => T.send([ld, f], { speed: 1 / Math.max(.3, s.lag + .3), color: L.P.series[0], label: `v${v}`, end: () => { if (!T.nodes[f].down && !s.logs[f].includes(v)) s.logs[f].push(v); } }));
        }
      });
    }
    function readReplica() {
      const f = followers()[0];
      if (!f) return;
      send('client', f, .4, L.P.series[4], 'read', () => {
        const have = s.logs[f].length ? Math.max(...s.logs[f]) : 0, want = s.acked.length ? Math.max(...s.acked) : 0;
        const stale = have < want;
        if (stale) s.stale++;
        T.nodes[f].badge = stale ? `stale: sees v${have || '–'}` : `fresh v${have}`;
        T.nodes[f].badgeColor = stale ? L.P.err : L.P.ok;
        send(f, 'client', .4, stale ? L.P.err : L.P.ok, stale ? `v${have || '–'}` : `v${have}`, () => {
          s.msg = stale ? `Read-your-writes violated: you wrote v${want} but the follower still returns v${have || 'nothing'}.` : 'The follower had caught up, so the read was fresh.';
          update();
          S.after(2.5, () => { T.nodes[f].badge = null; L.redraw(); });
        });
      });
    }
    function failover() {
      const old = s.leader;
      T.nodes[old].down = true;
      s.msg = 'Leader is down. Followers wait for a timeout before electing a new one.';
      update();
      S.after(1.4, () => {
        const cands = ['leader', 'f1', 'f2'].filter(n => n !== old && !T.nodes[n].down);
        if (!cands.length) return;
        const best = cands.sort((a, b) => s.logs[b].length - s.logs[a].length)[0];
        s.leader = best;
        const have = new Set(s.logs[best]);
        s.lost = s.acked.filter(v => !have.has(v));
        Object.keys(T.nodes).forEach(k => { if (T.nodes[k].label.startsWith('Leader')) T.nodes[k].label = 'Old leader'; });
        T.nodes[best].label = 'New leader';
        T.nodes[best].badge = s.lost.length ? `lost ${s.lost.map(v => `v${v}`).join(', ')}` : 'promoted';
        T.nodes[best].badgeColor = s.lost.length ? L.P.err : L.P.ok;
        T.edges = [{ a: 'client', b: best }, ...['leader', 'f1', 'f2'].filter(n => n !== best).map(n => ({ a: best, b: n, dash: [5, 4] }))];
        s.msg = s.lost.length ? `Failover done, but ${s.lost.length} acknowledged write(s) never reached the new leader. They are gone.` : 'Failover done with no data loss: the new leader had every acknowledged write.';
        update(); L.redraw();
      });
    }
    function reset() {
      Object.assign(s, { logs: { leader: [], f1: [], f2: [] }, leader: 'leader', seq: 0, acked: [], lost: [], stale: 0, writeLat: null, msg: '' });
      T.packets = []; S.clear();
      T.edges = [{ a: 'client', b: 'leader' }, { a: 'leader', b: 'f1', dash: [5, 4] }, { a: 'leader', b: 'f2', dash: [5, 4] }];
      Object.entries({ leader: 'Leader', f1: 'Follower 1', f2: 'Follower 2' }).forEach(([k, l]) => Object.assign(T.nodes[k], { label: l, down: false, badge: null }));
      update(); L.redraw();
    }
    function update() {
      ['leader', 'f1', 'f2'].forEach(k => { const lg = s.logs[k]; T.nodes[k].sub = lg.length ? lg.slice(-4).map(v => `v${v}`).join(' ') : 'empty'; });
      L.stats([['last write latency', s.writeLat == null ? '—' : fmtMs(s.writeLat * 1000), 'accent'], ['stale reads', s.stale, s.stale ? 'err' : ''], ['acknowledged writes lost', s.lost.length, s.lost.length ? 'err' : '']]);
      L.insight(s.msg ? `<b>${s.msg}</b> ${s.mode === 'sync' ? 'Synchronous replication waits for followers, so writes are slower but a failover loses nothing.' : 'Asynchronous replication acknowledges immediately: fast writes, but anything not yet copied can be read stale or lost on failover.'}` : '<b>Press Write.</b> Watch the leader acknowledge and the copies travel to the followers.');
      L.redraw();
    }
    L.draw = P => { c.clear(); T.draw(c.ctx, P); };
    reset();
  },
});

/* ======================================================== 6 · quorums == */
defineLab('sd-quorum', {
  title: 'Quorums: why R + W > N',
  hint: 'Click a replica to take it down. A write needs W acknowledgements, a read asks R replicas and keeps the newest version.',
  mount(L) {
    const c = L.canvas(w => Math.min(320, w * .5));
    const r = rng(17);
    const s = { N: 3, W: 2, R: 2, ver: 0, committed: 0, reps: [], msg: '', result: null };
    let T = null, S = simClock();
    const sN = L.seg('replicas N', [[3, '3'], [5, '5']], s.N, v => { s.N = v; s.W = Math.min(s.W, v); s.R = Math.min(s.R, v); wS.input.max = v; rS.input.max = v; wS.set(s.W, true); rS.set(s.R, true); build(); });
    const wS = L.slider('write quorum W', { min: 1, max: 3, step: 1, value: s.W }, v => { s.W = v; update(); });
    const rS = L.slider('read quorum R', { min: 1, max: 3, step: 1, value: s.R }, v => { s.R = v; update(); });
    const run = L.loop(dt => { S.advance(dt); T.step(dt); L.redraw(); if (!T.busy() && !S.q.length) return false; });
    L.button('Write a new version', () => { write(); run.start(); }, 'primary');
    L.button('Read', () => { read(); run.start(); }, 'primary');
    L.button('Reset', () => build());
    void sN;
    function build() {
      T = topo(c); S = simClock();
      T.node('coord', .5, .5, 'Coordinator', { w: 104 });
      s.reps = Array.from({ length: s.N }, (_, i) => {
        const a = -Math.PI / 2 + i * TAU / s.N;
        const id = `r${i}`;
        T.node(id, .5 + .36 * Math.cos(a) * (c.h / c.w) * 1.5, .5 + .38 * Math.sin(a), `Replica ${i + 1}`, { kind: 'db', w: 88, h: 48 });
        T.edge('coord', id, { dash: [4, 4] });
        return { id, ver: 0, down: false };
      });
      s.ver = 0; s.committed = 0; s.msg = ''; s.result = null;
      update(); L.redraw();
    }
    L.drag(c, {
      down: (x, y) => {
        const hit = s.reps.find(rp => { const [nx, ny] = T.xy(rp.id); return Math.abs(nx - x) < 46 && Math.abs(ny - y) < 28; });
        if (hit) { hit.down = !hit.down; T.nodes[hit.id].down = hit.down; update(); L.redraw(); }
      },
    });
    function write() {
      const v = ++s.ver, up = s.reps.filter(rp => !rp.down);
      if (up.length < s.W) { s.msg = `Write v${v} failed: only ${up.length} replicas are up but W = ${s.W}. Strong quorums trade availability for consistency.`; s.ver--; update(); return; }
      const order = [...up].sort(() => r() - .5);
      let acks = 0, done = false;
      order.forEach((rp, i) => {
        const late = i >= s.W;
        T.send(['coord', rp.id], {
          speed: late ? .28 : 1.4 - i * .15, color: L.P.accent, label: `v${v}`,
          end: () => {
            rp.ver = Math.max(rp.ver, v);
            if (late) { update(); return; }
            T.send([rp.id, 'coord'], { speed: 1.6, color: L.P.ok, label: 'ack', end: () => { if (++acks >= s.W && !done) { done = true; s.committed = v; s.msg = `v${v} committed after ${s.W} acks. The other replicas get it later.`; update(); } } });
          },
        });
      });
      s.msg = `Writing v${v}…`; update();
    }
    function read() {
      const up = s.reps.filter(rp => !rp.down);
      if (up.length < s.R) { s.msg = `Read failed: only ${up.length} replicas up, R = ${s.R}.`; update(); return; }
      const ask = [...up].sort(() => r() - .5).slice(0, s.R);
      let got = [];
      ask.forEach(rp => T.send(['coord', rp.id], { speed: 1.5, color: L.P.series[4], label: 'get', end: () => {
        T.send([rp.id, 'coord'], { speed: 1.5, color: L.P.series[4], label: `v${rp.ver}`, end: () => {
          got.push(rp.ver);
          if (got.length === ask.length) {
            const best = Math.max(...got);
            s.result = best;
            s.msg = best < s.committed ? `Stale read: got v${best} although v${s.committed} is committed. None of the ${s.R} replicas asked were in the write quorum.` : `Read returned v${best}${s.committed ? `, the latest committed version` : ''}.`;
            update();
          }
        } });
      } }));
    }
    function update() {
      s.reps.forEach(rp => { T.nodes[rp.id].sub = rp.down ? 'down' : `has v${rp.ver}`; });
      const safe = s.R + s.W > s.N;
      L.stats([['R + W', `${s.R} + ${s.W} = ${s.R + s.W}`, safe ? 'ok' : 'err'], ['N', s.N], ['guaranteed overlap', safe ? 'yes' : 'no', safe ? 'ok' : 'err'], ['latest committed', s.committed ? `v${s.committed}` : '—', 'accent'], s.result != null && ['last read', `v${s.result}`, s.result < s.committed ? 'err' : 'ok']]);
      L.insight(`${s.msg ? `<b>${s.msg}</b> ` : ''}${safe ? `R + W > N, so every read set shares at least one replica with every write set and always sees the newest committed version.` : `R + W ≤ N: a read can miss every replica that took the write. Press Write, then Read a few times.`} ${s.W === s.N ? 'W = N means one dead replica blocks all writes.' : ''}`);
      L.redraw();
    }
    L.draw = P => { c.clear(); T.draw(c.ctx, P); };
    build();
  },
});
