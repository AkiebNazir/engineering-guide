/* ============================================================================
   System design labs, part 2 — consensus, partitioning, rate limiting,
   streams, resilience and storage engines. Requires viz.js and viz-sd.js.
   ========================================================================= */
'use strict';

/* ============================================================ 7 · Raft == */
defineLab('sd-raft', {
  title: 'Raft: leader election and log replication',
  hint: 'Press Run. Click a server to crash or restart it, split the network, and add client writes. An entry is committed once a majority stores it.',
  mount(L) {
    const N = 5, HB = .9, TRAVEL = .45;
    const r = rng(33);
    const c = L.canvas(w => Math.min(400, Math.max(340, w * .56)));
    let T, nodes, split = false, event = '';
    const timeout = () => 2.2 + r() * 1.9;
    const run = L.loop(dt => { tick(dt); L.redraw(); });
    L.playButton(run, ['Run the cluster', 'Pause']);
    L.button('Client write', () => clientWrite(), 'primary');
    L.button('Crash the leader', () => { const ld = leader(); if (ld) crash(ld.i); });
    L.toggle('Network partition: S1 S2 | S3 S4 S5', split, v => { split = v; event = v ? 'The network split. S1 and S2 can no longer reach the majority side.' : 'The partition healed.'; update(); });
    L.button('Reset', () => reset());
    const group = i => (i < 2 ? 0 : 1);
    const reach = (a, b) => nodes[a].alive && nodes[b].alive && (!split || group(a) === group(b));
    const leader = () => nodes.filter(n => n.alive && n.role === 'leader').sort((a, b) => b.term - a.term)[0];

    function reset() {
      T = topo(c);
      nodes = Array.from({ length: N }, (_, i) => {
        const a = -Math.PI / 2 + i * TAU / N;
        T.node(`s${i}`, .5 + .3 * Math.cos(a) * Math.min(1, c.h / c.w * 1.7), .44 + .33 * Math.sin(a), `S${i + 1}`, { kind: 'round', w: 60, h: 60 });
        return { i, id: `s${i}`, role: 'follower', term: 0, voted: null, timer: 1 + r() * 2.5, log: [], commit: 0, alive: true, votes: new Set(), match: {}, hb: 0 };
      });
      for (let i = 0; i < N; i++) for (let j = i + 1; j < N; j++) T.edge(`s${i}`, `s${j}`, { color: 'transparent' });
      event = 'All five servers start as followers with random election timeouts.';
      update(); L.redraw();
    }
    function send(from, to, msg, color, label) {
      if (!reach(from, to)) return;
      T.send([nodes[from].id, nodes[to].id], { speed: 1 / TRAVEL, color, label, r: 4, end: () => { if (reach(from, to)) handle(to, { ...msg, from }); } });
    }
    function startElection(n) {
      n.role = 'candidate'; n.term++; n.voted = n.i; n.votes = new Set([n.i]); n.timer = timeout();
      event = `S${n.i + 1} timed out without hearing a leader. It starts term ${n.term} and asks for votes.`;
      nodes.forEach(p => { if (p !== n) send(n.i, p.i, { type: 'rv', term: n.term, lastIdx: n.log.length, lastTerm: n.log[n.log.length - 1] || 0 }, L.P.series[1], 'vote?'); });
    }
    function becomeLeader(n) {
      n.role = 'leader'; n.match = {}; n.hb = 0;
      event = `S${n.i + 1} won a majority of votes and is leader for term ${n.term}. Its heartbeats stop other elections.`;
    }
    function handle(i, m) {
      const n = nodes[i];
      if (!n.alive) return;
      if (m.term > n.term) { n.term = m.term; n.role = 'follower'; n.voted = null; }
      if (m.type === 'rv') {
        const myLast = n.log[n.log.length - 1] || 0;
        const upToDate = m.lastTerm > myLast || (m.lastTerm === myLast && m.lastIdx >= n.log.length);
        const grant = m.term === n.term && (n.voted === null || n.voted === m.from) && upToDate;
        if (grant) { n.voted = m.from; n.timer = timeout(); }
        send(i, m.from, { type: 'vote', term: n.term, granted: grant }, grant ? L.P.ok : L.P.err, grant ? 'yes' : 'no');
      } else if (m.type === 'vote') {
        if (n.role === 'candidate' && m.term === n.term && m.granted) { n.votes.add(m.from); if (n.votes.size > N / 2) becomeLeader(n); }
      } else if (m.type === 'ae') {
        if (m.term < n.term) { send(i, m.from, { type: 'ack', term: n.term, ok: false, match: 0 }, L.P.err, null); return; }
        n.role = 'follower'; n.timer = timeout();
        n.log = m.log.slice(); n.commit = Math.min(m.commit, n.log.length);
        send(i, m.from, { type: 'ack', term: n.term, ok: true, match: n.log.length }, L.P.ok, null);
      } else if (m.type === 'ack') {
        if (n.role === 'leader' && m.term === n.term && m.ok) {
          n.match[m.from] = m.match;
          for (let idx = n.log.length; idx > n.commit; idx--) {
            const count = 1 + Object.values(n.match).filter(x => x >= idx).length;
            if (count > N / 2 && n.log[idx - 1] === n.term) {
              if (idx > n.commit) event = `Entry ${idx} is stored on ${count} of ${N} servers, a majority, so S${n.i + 1} marks it committed.`;
              n.commit = idx; break;
            }
          }
        }
      }
    }
    function tick(dt) {
      T.step(dt);
      nodes.forEach(n => {
        if (!n.alive) return;
        if (n.role === 'leader') {
          if ((n.hb -= dt) <= 0) {
            n.hb = HB;
            nodes.forEach(p => { if (p !== n) send(n.i, p.i, { type: 'ae', term: n.term, log: n.log.slice(), commit: n.commit }, L.P.accent, n.log.length > (n.match[p.i] || 0) ? 'entries' : null); });
          }
        } else if ((n.timer -= dt) <= 0) startElection(n);
      });
      update();
    }
    function clientWrite() {
      const ld = leader();
      if (!ld) { event = 'No leader right now: the client has to wait and retry.'; update(); return; }
      ld.log.push(ld.term);
      event = `The client wrote to S${ld.i + 1}. The entry is uncommitted until a majority has it.${split && group(ld.i) === 0 ? ' This leader is on the minority side, so it can never commit. The entry will be discarded when the partition heals.' : ''}`;
      if (!run.running) run.start();
      update();
    }
    function crash(i) {
      const n = nodes[i];
      n.alive = !n.alive;
      if (n.alive) { n.role = 'follower'; n.timer = timeout(); event = `S${i + 1} restarted as a follower.`; }
      else event = `S${i + 1} crashed.${n.role === 'leader' ? ' Followers stop receiving heartbeats; the first to time out starts an election.' : ''}`;
      T.nodes[n.id].down = !n.alive;
      if (!run.running) run.start();
      update();
    }
    L.drag(c, {
      down: (x, y) => {
        const hit = nodes.find(n => { const [nx, ny] = T.xy(n.id); return Math.hypot(nx - x, ny - y) < 32; });
        if (hit) crash(hit.i);
      },
    });
    function update() {
      nodes.forEach(n => {
        const tn = T.nodes[n.id];
        tn.fill = !n.alive ? null : n.role === 'leader' ? L.P.accent : n.role === 'candidate' ? L.P.alpha(L.P.series[1], .35) : null;
        tn.labelColor = n.role === 'leader' && n.alive ? L.P.surface : null;
        tn.sub = `term ${n.term}`;
        tn.subColor = n.role === 'leader' && n.alive ? L.P.surface : null;
      });
      const ld = leader();
      L.stats([['leader', ld ? `S${ld.i + 1}` : 'none', ld ? 'accent' : 'err'], ['term', ld ? ld.term : Math.max(...nodes.map(n => n.term))], ['committed entries', ld ? ld.commit : '—'], ['alive', `${nodes.filter(n => n.alive).length} of ${N}`]]);
      L.insight(`<b>${event}</b> ${nodes.filter(n => n.alive).length <= N / 2 ? 'Fewer than a majority are alive, so no leader can be elected and nothing can commit: Raft chooses consistency over availability.' : ''}`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      if (split) {
        const [x1, y1] = T.xy('s1'), [x2, y2] = T.xy('s2');
        const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
        D.line(ctx, mx - 40, my - 120, mx + 50, my + 130, P.err, 2, [8, 6]);
      }
      T.draw(ctx, P);
      nodes.forEach(n => {
        const [x, y] = T.xy(n.id);
        if (n.alive && n.role !== 'leader') {
          ctx.beginPath(); ctx.arc(x, y, 36, -Math.PI / 2, -Math.PI / 2 + TAU * clamp(n.timer / 4.1, 0, 1));
          ctx.strokeStyle = P.alpha(n.role === 'candidate' ? P.series[1] : 'faint', .8); ctx.lineWidth = 2.5; ctx.stroke();
        }
        const cell = 12, start = x - Math.min(n.log.length, 8) * (cell + 2) / 2;
        n.log.slice(-8).forEach((term, k) => {
          const idx = n.log.length - Math.min(n.log.length, 8) + k + 1, cx = start + k * (cell + 2), cy = y + 44;
          ctx.fillStyle = idx <= n.commit ? P.ok : P.surface2;
          D.rrect(ctx, cx, cy, cell, cell, 3); ctx.fill();
          ctx.strokeStyle = idx <= n.commit ? P.ok : P.strong; ctx.lineWidth = 1; ctx.stroke();
          D.text(ctx, String(term), cx + cell / 2, cy + cell / 2 + .5, { color: idx <= n.commit ? P.surface : P.dim, size: 8.5, align: 'center', mono: true, weight: 700 });
        });
      });
      D.text(ctx, 'ring = election timeout left · squares = log entries (term), green = committed', 10, c.h - 10, { color: P.faint, size: 10.5 });
    };
    reset();
  },
});

/* ==================================================== 8 · partitioning == */
defineLab('sd-shard', {
  title: 'Choosing a shard key: range, hash, and hot keys',
  hint: 'Six hundred users spread across shards. Compare storage and traffic per shard, then add a celebrity whose traffic is 400× a normal user’s.',
  mount(L) {
    const W = { A: 9, B: 5, C: 7, D: 6, E: 4, F: 3, G: 4, H: 4, I: 2, J: 8, K: 5, L: 6, M: 9, N: 4, O: 2, P: 3, R: 6, S: 10, T: 6, V: 2, W: 3, Z: 2 };
    const letters = Object.keys(W), totalW = Object.values(W).reduce((a, b) => a + b, 0);
    const users = [];
    let k = 0;
    letters.forEach(ch => { const n = Math.round(W[ch] / totalW * 600); for (let i = 0; i < n; i++) users.push({ name: `${ch.toLowerCase()}user${k++}`, letter: ch }); });
    const HOT = { name: 'taylor', letter: 'T' };
    const s = { strat: 'range', n: 4, hot: true, bars: null };
    const c = L.canvas(w => Math.min(300, w * .48));
    L.seg('shard by', [['range', 'Key range (A–Z)'], ['hash', 'hash(key)'], ['salt', 'hash(key) + salted hot key']], s.strat, v => { s.strat = v; update(); });
    L.seg('shards', [[2, '2'], [4, '4'], [8, '8']], s.n, v => { s.n = v; update(); });
    L.toggle('Celebrity account (400× traffic)', s.hot, v => { s.hot = v; update(); });
    const alpha = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
    const rangeOf = i => { const per = 26 / s.n; return [alpha[Math.round(i * per)], alpha[Math.round((i + 1) * per) - 1]]; };
    const shardOf = u => s.strat === 'range' ? Math.min(s.n - 1, Math.floor(alpha.indexOf(u.letter) / (26 / s.n))) : fnv(u.name, 4) % s.n;
    function compute() {
      const storage = new Array(s.n).fill(0), traffic = new Array(s.n).fill(0), hot = new Array(s.n).fill(0);
      users.forEach(u => { const sh = shardOf(u); storage[sh]++; traffic[sh]++; });
      if (s.hot) {
        storage[shardOf(HOT)]++;
        if (s.strat === 'salt') for (let i = 0; i < s.n; i++) { const sh = fnv(`${HOT.name}#${i}`, 4) % s.n; hot[sh] += 400 / s.n; }
        else hot[shardOf(HOT)] += 400;
      }
      return { storage, traffic, hot };
    }
    function update() {
      const next = compute(), from = s.bars;
      s.bars = next;
      if (from && from.storage.length === next.storage.length) {
        const f = JSON.parse(JSON.stringify(from));
        L.tween(500, t => { s.anim = { storage: f.storage.map((v, i) => lerp(v, next.storage[i], t)), traffic: f.traffic.map((v, i) => lerp(v, next.traffic[i], t)), hot: f.hot.map((v, i) => lerp(v, next.hot[i], t)) }; L.redraw(); });
      } else { s.anim = next; L.redraw(); }
      const tr = next.traffic.map((v, i) => v + next.hot[i]), st = next.storage;
      const avgT = tr.reduce((a, b) => a + b, 0) / s.n, avgS = st.reduce((a, b) => a + b, 0) / s.n;
      const tSkew = Math.max(...tr) / avgT, sSkew = Math.max(...st) / avgS;
      L.stats([['busiest shard traffic', `${fmtN(tSkew, 2)}× average`, tSkew > 1.6 ? 'err' : 'ok'], ['largest shard storage', `${fmtN(sSkew, 2)}× average`, sSkew > 1.4 ? 'err' : 'ok'], s.hot && ['reads of the celebrity touch', s.strat === 'salt' ? `${s.n} shards` : '1 shard']]);
      L.insight(s.strat === 'range' ? '<b>Range sharding keeps neighbouring keys together</b>, so range scans are cheap. But real keys are not uniform: S and M names pile onto some shards, and sequential keys like timestamps send every new write to the last shard.'
        : s.strat === 'hash' && s.hot ? '<b>Hashing evens out storage</b>, but one hot key still lands on one shard. No shard key fixes a single key that is 400× busier than the rest.'
        : s.strat === 'salt' ? `<b>Salting splits the hot key into ${s.n} sub-keys</b> (taylor#0…taylor#${s.n - 1}), so its traffic spreads out. The price is that reading all of its data means asking ${s.n} shards and merging. Only salt the keys you know are hot.`
        : '<b>Hashing spreads keys evenly</b> but loses ordering: a range scan now has to ask every shard.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, a = s.anim || s.bars;
      if (!a) return;
      const half = (c.w - 40) / 2;
      const chart = (x0, title, vals, extra, fmt) => {
        const mx = Math.max(...vals.map((v, i) => v + (extra ? extra[i] : 0)), 1) * 1.1, bw = (half - 20) / s.n;
        D.text(ctx, title, x0, 12, { color: P.dim, size: 11.5, weight: 600 });
        const base = c.h - 34, top = 30;
        vals.forEach((v, i) => {
          const h1 = v / mx * (base - top), h2 = extra ? extra[i] / mx * (base - top) : 0, x = x0 + i * bw;
          ctx.fillStyle = P.alpha('accent', .8); D.rrect(ctx, x + 4, base - h1, bw - 8, h1, 4); ctx.fill();
          if (h2 > .5) { ctx.fillStyle = P.err; D.rrect(ctx, x + 4, base - h1 - h2, bw - 8, h2, 4); ctx.fill(); }
          D.text(ctx, fmt(v + (extra ? extra[i] : 0)), x + bw / 2, base - h1 - h2 - 9, { color: P.dim, size: 10, align: 'center', mono: true });
          const label = s.strat === 'range' ? rangeOf(i).join('–') : `shard ${i + 1}`;
          D.text(ctx, label, x + bw / 2, base + 12, { color: P.faint, size: 10, align: 'center' });
        });
        const avg = vals.reduce((p, v, i) => p + v + (extra ? extra[i] : 0), 0) / s.n;
        const ay = base - avg / mx * (base - top);
        D.line(ctx, x0, ay, x0 + half - 20, ay, P.faint, 1, [4, 4]);
      };
      chart(14, 'storage (users per shard)', a.storage, null, v => Math.round(v));
      chart(34 + half, 'traffic per shard (red = celebrity)', a.traffic, a.hot, v => Math.round(v));
    };
    update();
  },
});

/* ================================================== 9 · rate limiting == */
defineLab('sd-ratelimit', {
  title: 'Rate-limiting algorithms on the same traffic',
  hint: 'Ten seconds of requests. Green dots were allowed, red were rejected. Pick an algorithm and a traffic pattern.',
  mount(L) {
    const s = { algo: 'token', pattern: 'edge', limit: 5, burst: 5, reveal: 1 };
    const c = L.canvas(w => Math.min(300, w * .46));
    L.seg('algorithm', [['token', 'Token bucket'], ['leaky', 'Leaky bucket'], ['fixed', 'Fixed window'], ['log', 'Sliding log'], ['counter', 'Sliding window counter']], s.algo, v => { s.algo = v; update(); });
    L.seg('traffic', [['steady', 'Steady'], ['bursty', 'Bursty'], ['edge', 'Burst at a window edge']], s.pattern, v => { s.pattern = v; update(); });
    L.slider('limit (requests/second)', { min: 2, max: 10, step: 1, value: s.limit }, v => { s.limit = v; update(); });
    L.slider('burst capacity (token / leaky bucket)', { min: 1, max: 15, step: 1, value: s.burst }, v => { s.burst = v; update(); });
    const play = L.loop(dt => { s.reveal = Math.min(1, s.reveal + dt / 6); L.redraw(); if (s.reveal >= 1) return false; });
    L.playButton(play, ['Replay', 'Pause'], () => { if (s.reveal >= 1) s.reveal = 0; });
    function arrivals() {
      const r = rng(s.pattern.length * 13), out = [];
      const add = (a, b, n) => { for (let i = 0; i < n; i++) out.push(a + (b - a) * r()); };
      if (s.pattern === 'steady') { for (let t = .1; t < 10; t += .26) out.push(t + r() * .05); }
      else if (s.pattern === 'bursty') { let t = 0; while ((t += -Math.log(1 - r()) / 2.2) < 10) out.push(t); add(2, 2.4, 14); add(6.4, 6.7, 11); }
      else { let t = 0; while ((t += -Math.log(1 - r()) / 1.2) < 10) out.push(t); add(3.82, 3.99, 9); add(4.01, 4.18, 9); add(7.85, 7.99, 8); add(8.0, 8.15, 8); }
      return out.filter(t => t < 10).sort((a, b) => a - b);
    }
    function simulate() {
      const reqs = arrivals().map(t => ({ t, ok: false, out: t })), curve = [];
      if (s.algo === 'token') {
        let tokens = s.burst, last = 0;
        for (let x = 0; x <= 10; x += .02) {
          reqs.filter(q => q.t >= x && q.t < x + .02).forEach(q => { tokens = Math.min(s.burst, tokens + (q.t - last) * s.limit); last = q.t; if (tokens >= 1) { tokens -= 1; q.ok = true; } });
          tokens = Math.min(s.burst, tokens + (x + .02 - last) * s.limit); last = x + .02;
          curve.push([x, tokens]);
        }
      } else if (s.algo === 'leaky') {
        let water = 0, last = 0;
        reqs.forEach(q => { water = Math.max(0, water - (q.t - last) * s.limit); last = q.t; if (water + 1 <= s.burst) { water += 1; q.ok = true; q.out = q.t + (water - 1) / s.limit; } });
      } else if (s.algo === 'fixed') {
        const count = {};
        reqs.forEach(q => { const w = Math.floor(q.t); count[w] = count[w] || 0; if (count[w] < s.limit) { count[w]++; q.ok = true; } });
        s.windows = count;
      } else if (s.algo === 'log') {
        const log = [];
        reqs.forEach(q => { while (log.length && log[0] <= q.t - 1) log.shift(); if (log.length < s.limit) { log.push(q.t); q.ok = true; } });
      } else {
        const count = {};
        reqs.forEach(q => { const w = Math.floor(q.t), prev = count[w - 1] || 0, cur = count[w] || 0, est = prev * (1 - (q.t - w)) + cur; if (est < s.limit) { count[w] = cur + 1; q.ok = true; } });
      }
      const ok = reqs.filter(q => q.ok).map(q => q.t);
      let worst = 0, worstAt = 0;
      ok.forEach((t, i) => { let j = i; while (j < ok.length && ok[j] < t + 1) j++; if (j - i > worst) { worst = j - i; worstAt = t; } });
      return { reqs, curve, worst, worstAt };
    }
    let sim = null;
    function update() {
      sim = simulate();
      const allowed = sim.reqs.filter(q => q.ok).length;
      L.stats([['allowed', allowed, 'ok'], ['rejected', sim.reqs.length - allowed, 'err'], ['most allowed in any 1 s', sim.worst, sim.worst > s.limit ? 'err' : 'accent'], ['limit', `${s.limit}/s`]]);
      const tips = {
        token: `<b>Token bucket</b> refills ${s.limit} tokens per second up to ${s.burst}. A request spends one token. It allows short bursts (up to the bucket size) while holding the long-run average. Most API gateways use it.`,
        leaky: '<b>Leaky bucket</b> queues requests and releases them at a constant rate (the grey lines show each request waiting). The output is perfectly smooth, but bursts add latency, and a full bucket rejects.',
        fixed: `<b>Fixed window</b> counts per calendar second. It is cheap (one counter), but a burst at the end of one window plus one at the start of the next lets ${sim.worst} requests through in under a second, ${sim.worst > s.limit ? `${fmtN(sim.worst / s.limit, 1)}× the limit` : 'right at the limit'}.`,
        log: '<b>Sliding log</b> stores every timestamp and counts the last second exactly. It is accurate, but memory grows with the limit, which is expensive for large limits.',
        counter: '<b>Sliding window counter</b> weights the previous window’s count by how much of it still overlaps. It is almost as accurate as the log and needs only two counters per key, which is why it is a common choice in Redis-based limiters.',
      };
      L.insight(tips[s.algo]);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, v = D.view(c, { x0: 0, x1: 10, y0: 0, y1: 1, pad: 12, padL: 18, padB: 24 }), mid = c.h * .62;
      const cut = s.reveal * 10;
      D.axes(ctx, { ...v, y0: 0, sy: () => c.h - 24, sx: v.sx, x0: 0, x1: 10, y1: 1 }, P, {});
      for (let t = 0; t <= 10; t++) {
        D.line(ctx, v.sx(t), 20, v.sx(t), c.h - 24, P.soft, 1);
        D.text(ctx, `${t}s`, v.sx(t), c.h - 12, { color: P.faint, size: 10, align: 'center', mono: true });
        if ((s.algo === 'fixed' || s.algo === 'counter') && t < 10) {
          ctx.fillStyle = t % 2 ? P.alpha('faint', .05) : 'transparent'; ctx.fillRect(v.sx(t), 20, v.sx(1) - v.sx(0), c.h - 44);
          if (s.algo === 'fixed' && s.windows) D.text(ctx, `${s.windows[t] || 0}/${s.limit}`, v.sx(t + .5), 30, { color: P.dim, size: 10, align: 'center', mono: true });
        }
      }
      if (s.algo === 'token' && sim.curve.length) {
        ctx.beginPath();
        sim.curve.filter(([x]) => x <= cut).forEach(([x, tk], i) => { const y = mid - 30 - tk / s.burst * (mid - 80); i ? ctx.lineTo(v.sx(x), y) : ctx.moveTo(v.sx(x), y); });
        ctx.strokeStyle = P.series[0]; ctx.lineWidth = 2; ctx.stroke();
        D.text(ctx, 'tokens in bucket', v.sx(.05), 34, { color: P.series[0], size: 10.5, weight: 600 });
      }
      D.line(ctx, v.sx(0), mid, v.sx(10), mid, P.strong, 1);
      if (sim.worst > s.limit) {
        ctx.fillStyle = P.alpha('err', .1); ctx.fillRect(v.sx(sim.worstAt), mid - 40, v.sx(1) - v.sx(0), 80);
        D.text(ctx, `${sim.worst} allowed within 1 s`, v.sx(sim.worstAt + .5), mid - 48, { color: P.err, size: 10.5, align: 'center', weight: 650 });
      }
      sim.reqs.forEach(q => {
        if (q.t > cut) return;
        if (s.algo === 'leaky' && q.ok && q.out - q.t > .02) D.line(ctx, v.sx(q.t), mid - 14, v.sx(Math.min(q.out, 10)), mid - 26, P.faint, 1);
        D.dot(ctx, v.sx(q.t), q.ok ? mid - 14 : mid + 14, 4, q.ok ? P.ok : P.err);
      });
      D.text(ctx, 'allowed', 4, mid - 14, { color: P.ok, size: 9.5 });
      D.text(ctx, 'rejected', 4, mid + 14, { color: P.err, size: 9.5 });
    };
    update();
  },
});

/* =========================================== 10 · log-based messaging == */
defineLab('sd-kafka', {
  title: 'Partitions, consumer groups and redelivery',
  hint: 'Messages with the same key go to the same partition. Each partition is read by one consumer in the group. Kill a consumer and watch the rebalance.',
  mount(L) {
    const r = rng(12);
    const s = { P: 4, rate: 10, speed: 4, idem: false, dlq: true, t: 0, parts: [], consumers: [], rebalance: 0, processed: 0, dups: 0, dlqN: 0, seen: new Set(), nextId: 1, acc: 0, poisonNext: false };
    const c = L.canvas(w => Math.min(360, w * .56));
    L.seg('partitions', [[2, '2'], [4, '4'], [6, '6']], s.P, v => { s.P = v; reset(); });
    L.slider('producer rate (msgs/s)', { min: 2, max: 30, step: 1, value: s.rate }, v => { s.rate = v; });
    L.slider('each consumer’s speed (msgs/s)', { min: 1, max: 12, step: 1, value: s.speed }, v => { s.speed = v; });
    const run = L.loop(dt => { tick(dt); L.redraw(); if ((s.acc += dt) > .25) { s.acc = 0; update(); } });
    L.playButton(run, ['Run the stream', 'Pause']);
    L.button('Add consumer', () => { if (s.consumers.filter(x => x.alive).length < 6) { s.consumers.push(mkConsumer()); startRebalance(); } });
    L.button('Kill a consumer', () => { const alive = s.consumers.filter(x => x.alive); if (alive.length > 1) { const v = alive[alive.length - 1]; v.alive = false; startRebalance(v); } });
    L.button('Send a poison message', () => { s.poisonNext = true; });
    L.toggle('Idempotent consumer', s.idem, v => { s.idem = v; });
    L.toggle('Dead-letter queue', s.dlq, v => { s.dlq = v; });
    function mkConsumer() { return { id: s.consumers.length, alive: true, busy: null, rr: 0 }; }
    function reset() {
      s.parts = Array.from({ length: s.P }, () => ({ log: [], committed: 0, next: 0, owner: null }));
      s.consumers = [mkConsumer(), mkConsumer()];
      Object.assign(s, { t: 0, rebalance: 0, processed: 0, dups: 0, dlqN: 0, seen: new Set(), nextId: 1 });
      assign(); update(); L.redraw();
    }
    function assign() {
      const alive = s.consumers.filter(x => x.alive);
      s.parts.forEach((p, i) => { p.owner = alive.length ? alive[i % alive.length].id : null; p.next = p.committed; });
      s.consumers.forEach(x => { x.busy = null; });
    }
    function startRebalance(victim) {
      s.rebalance = 1.6;
      s.event = victim ? `Consumer ${victim.id + 1} died. Everything it processed after its last commit will be read again by the new owner.` : 'A consumer joined. The group pauses to reassign partitions.';
      update();
    }
    function tick(dt) {
      s.t += dt;
      const n = Math.floor(s.rate * dt + r());
      for (let i = 0; i < n; i++) {
        const key = Math.floor(r() * 12), p = s.parts[key % s.P];
        p.log.push({ id: s.nextId++, key, poison: s.poisonNext, tries: 0 });
        s.poisonNext = false;
      }
      if (s.rebalance > 0) { s.rebalance -= dt; if (s.rebalance <= 0) assign(); return; }
      s.consumers.forEach(cn => {
        if (!cn.alive) return;
        if (cn.busy) {
          cn.busy.left -= dt;
          if (cn.busy.left > 0) return;
          const { p, msg } = cn.busy;
          cn.busy = null;
          const part = s.parts[p];
          if (msg.poison) {
            msg.tries++;
            if (msg.tries < 3) return;
            if (!s.dlq) { msg.tries = 0; return; }
            s.dlqN++;
          } else {
            s.processed++;
            if (s.seen.has(msg.id)) { if (!s.idem) s.dups++; }
            s.seen.add(msg.id);
          }
          part.next++;
          if (part.next - part.committed >= 5) part.committed = part.next;
          return;
        }
        const mine = s.parts.map((p, i) => [p, i]).filter(([p]) => p.owner === cn.id && p.next < p.log.length);
        if (!mine.length) return;
        const [part, i] = mine[cn.rr++ % mine.length];
        const msg = part.log[part.next];
        cn.busy = { p: i, msg, left: msg.poison ? .5 : 1 / s.speed };
      });
    }
    function update() {
      const lag = s.parts.reduce((a, p) => a + (p.log.length - p.committed), 0);
      const alive = s.consumers.filter(x => x.alive), idle = alive.filter(cn => !s.parts.some(p => p.owner === cn.id)).length;
      const stuck = s.parts.some(p => { const m = p.log[p.next]; return m && m.poison && !s.dlq; });
      L.stats([['consumer lag', lag, lag > 60 ? 'err' : 'accent'], ['processed', s.processed], ['duplicates processed', s.dups, s.dups ? 'err' : ''], ['dead-lettered', s.dlqN], ['idle consumers', idle, idle ? 'err' : '']]);
      L.insight(s.rebalance > 0 ? `<b>Rebalancing.</b> ${s.event || ''} Every consumer in the group stops while partitions are reassigned.`
        : stuck ? '<b>A poison message is blocking its partition.</b> The consumer retries it forever, and everything behind it on that partition waits. A dead-letter queue lets you park it and move on.'
        : idle ? `<b>${idle} consumer${idle > 1 ? 's are' : ' is'} idle.</b> A partition is read by at most one consumer in a group, so consumers beyond the partition count do nothing. Partition count caps parallelism.`
        : s.dups && !s.idem ? `<b>${s.dups} messages were processed twice.</b> Delivery is at-least-once: offsets are committed in batches, so a crash replays the uncommitted tail. Make the consumer idempotent (dedupe by message ID, or upsert).`
        : lag > 60 ? '<b>Lag is growing:</b> consumers are slower than producers. Add consumers (up to the partition count) or speed up processing.'
        : '<b>Same key, same partition, so order is kept per key.</b> Different partitions are processed in parallel. Try killing a consumer while the stream runs.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, rowH = (c.h - 50) / s.P, x0 = c.w * .16, x1 = c.w * .7, cell = Math.min(16, (x1 - x0) / 18);
      ctx.fillStyle = P.surface2; D.rrect(ctx, 10, c.h / 2 - 24, c.w * .1, 48, 10); ctx.fill(); ctx.strokeStyle = P.strong; ctx.stroke();
      D.text(ctx, 'Producer', 10 + c.w * .05, c.h / 2, { color: P.text, size: 11.5, align: 'center', weight: 650 });
      const cy = i => 30 + (i + .5) * ((c.h - 50) / Math.max(1, s.consumers.filter(x => x.alive).length));
      const alive = s.consumers.filter(x => x.alive);
      s.parts.forEach((p, i) => {
        const y = 25 + i * rowH + rowH / 2;
        D.line(ctx, 10 + c.w * .1, c.h / 2, x0 - 6, y, P.soft, 1);
        D.text(ctx, `P${i}`, x0 - 22, y, { color: P.dim, size: 11, mono: true, weight: 600 });
        const start = Math.max(0, p.log.length - 18);
        p.log.slice(start).forEach((m, k) => {
          const idx = start + k, x = x0 + k * (cell + 2);
          ctx.fillStyle = m.poison ? P.err : idx < p.committed ? P.alpha('ok', .55) : idx < p.next ? P.series[1] : P.surface2;
          D.rrect(ctx, x, y - cell / 2, cell, cell, 3); ctx.fill();
          ctx.strokeStyle = P.soft; ctx.lineWidth = 1; ctx.stroke();
        });
        const lag = p.log.length - p.committed;
        D.text(ctx, `lag ${lag}`, x1 + 6, y, { color: lag > 15 ? P.err : P.faint, size: 10, mono: true });
        const owner = alive.findIndex(cn => cn.id === p.owner);
        if (owner >= 0 && s.rebalance <= 0) D.line(ctx, x1 + 48, y, c.w * .84 - 40, cy(owner), P.alpha(P.series[owner % 6], .7), 1.8);
      });
      alive.forEach((cn, k) => {
        const y = cy(k), x = c.w * .84;
        ctx.fillStyle = s.rebalance > 0 ? P.alpha('faint', .2) : P.surface2; D.rrect(ctx, x - 40, y - 18, 80, 36, 9); ctx.fill();
        ctx.strokeStyle = P.series[k % 6]; ctx.lineWidth = 1.6; ctx.stroke();
        D.text(ctx, `consumer ${cn.id + 1}`, x, y - 5, { color: P.text, size: 10.5, align: 'center', weight: 650 });
        D.text(ctx, cn.busy ? (cn.busy.msg.poison ? `retry ${cn.busy.msg.tries + 1}` : 'working') : 'idle', x, y + 9, { color: cn.busy?.msg.poison ? P.err : P.faint, size: 9.5, align: 'center' });
      });
      if (s.dlqN) { ctx.fillStyle = P.alpha('err', .15); D.rrect(ctx, c.w - 70, c.h - 34, 60, 26, 7); ctx.fill(); D.text(ctx, `DLQ ${s.dlqN}`, c.w - 40, c.h - 21, { color: P.err, size: 10.5, align: 'center', weight: 700 }); }
      if (s.rebalance > 0) D.text(ctx, 'rebalancing…', c.w * .84, 16, { color: P.series[1], size: 11, align: 'center', weight: 700 });
      D.text(ctx, 'grey = not yet read · orange = processed, not committed · green = committed', x0, c.h - 8, { color: P.faint, size: 10 });
    };
    reset();
  },
});

/* ===================================== 11 · retries and circuit breaker == */
defineLab('sd-retry', {
  title: 'Retry storms, backoff with jitter, and circuit breakers',
  hint: 'A dependency is down from 5 s to 10 s. Watch how each retry policy loads it, and how long recovery takes once it comes back.',
  mount(L) {
    const s = { policy: 'backoff', breaker: false, reveal: 1 };
    const CAP = 250, B = .25, H = 20, OUT = [5, 10];
    const c = L.canvas(w => Math.min(320, w * .5));
    L.seg('retry policy', [['none', 'No retries'], ['immediate', 'Immediate retries'], ['backoff', 'Exponential backoff'], ['jitter', 'Backoff + jitter']], s.policy, v => { s.policy = v; compute(); });
    L.toggle('Circuit breaker', s.breaker, v => { s.breaker = v; compute(); });
    const play = L.loop(dt => { s.reveal = Math.min(1, s.reveal + dt / 5); L.redraw(); if (s.reveal >= 1) return false; });
    L.playButton(play, ['Replay', 'Pause'], () => { if (s.reveal >= 1) s.reveal = 0; });
    let sim = null;
    function compute() {
      const r = rng(99), nb = Math.ceil(H / B);
      const att = new Array(nb).fill(0), ok = new Array(nb).fill(0), short = new Array(nb).fill(0), state = new Array(nb).fill('closed');
      const heap = [];
      const push = e => { heap.push(e); let i = heap.length - 1; while (i > 0) { const p = (i - 1) >> 1; if (heap[p].t <= heap[i].t) break; [heap[p], heap[i]] = [heap[i], heap[p]]; i = p; } };
      const pop = () => { const top = heap[0], last = heap.pop(); if (heap.length) { heap[0] = last; let i = 0; for (;;) { const a = 2 * i + 1, b = a + 1; let m = i; if (a < heap.length && heap[a].t < heap[m].t) m = a; if (b < heap.length && heap[b].t < heap[m].t) m = b; if (m === i) break; [heap[m], heap[i]] = [heap[i], heap[m]]; i = m; } } return top; };
      const CLIENTS = 400;
      for (let cl = 0; cl < CLIENTS; cl++) { const phase = r() * 2; for (let t = phase; t < H; t += 2) push({ t, k: 0 }); }
      let breaker = 'closed', openUntil = 0, lastEval = 0, logical = 0, logicalOk = 0;
      while (heap.length) {
        const e = pop();
        if (e.t >= H) continue;
        const bi = Math.floor(e.t / B);
        if (e.t - lastEval >= B && s.breaker) {
          const pb = bi - 1;
          if (pb >= 0) {
            const tot = ok[pb] + (att[pb] - ok[pb]);
            if (breaker === 'closed' && att[pb] >= 20 && (att[pb] - ok[pb]) / att[pb] > .5) { breaker = 'open'; openUntil = e.t + 2; }
            else if (breaker === 'open' && e.t >= openUntil) breaker = 'half';
            else if (breaker === 'half' && att[pb] >= 3) { breaker = (ok[pb] / att[pb] > .8) ? 'closed' : 'open'; if (breaker === 'open') openUntil = e.t + 2; }
            void tot;
          }
          lastEval = e.t;
        }
        state[bi] = breaker;
        if (e.k === 0) logical++;
        if (s.breaker && (breaker === 'open' || (breaker === 'half' && r() > .06))) { short[bi]++; continue; }
        att[bi]++;
        const load = (bi > 0 ? att[bi - 1] : 0) / B;
        const outage = e.t >= OUT[0] && e.t < OUT[1];
        const pOk = outage ? 0 : load > CAP ? CAP / load : 1;
        if (r() < pOk) { ok[bi]++; logicalOk++; continue; }
        if (s.policy === 'none' || e.k >= 3) continue;
        const base = .4 * 2 ** e.k;
        const delay = s.policy === 'immediate' ? .05 : s.policy === 'backoff' ? base : r() * base * 2;
        push({ t: e.t + .1 + delay, k: e.k + 1 });
      }
      let recovered = null;
      for (let i = Math.ceil(OUT[1] / B); i < nb; i++) if (att[i] && ok[i] / att[i] > .9) { recovered = i * B - OUT[1]; break; }
      const during = att.slice(Math.floor(OUT[0] / B), Math.ceil(OUT[1] / B)).reduce((a, b) => a + b, 0);
      sim = { att, ok, short, state, recovered, during, rate: logicalOk / logical };
      L.stats([['attempts sent while it was down', during, 'accent'], ['time to recover after 10 s', recovered == null ? 'did not recover' : `${recovered.toFixed(2)} s`, recovered == null || recovered > 2 ? 'err' : 'ok'], ['requests that succeeded', `${Math.round(sim.rate * 100)}%`]]);
      L.insight(s.policy === 'immediate' ? '<b>Immediate retries multiply the load</b> on a service that is already failing, up to 4× here. When it comes back it is hit by the queued herd and falls over again.'
        : s.policy === 'backoff' && !s.breaker ? '<b>Backoff without jitter still synchronizes.</b> Everyone who failed at the same moment retries at the same moment, so you get evenly spaced spikes, including a big one right as the service recovers.'
        : s.policy === 'jitter' && !s.breaker ? '<b>Full jitter spreads retries randomly across the backoff window</b>, turning spikes into a gentle hum. This is the AWS-recommended default.'
        : s.breaker ? '<b>The circuit breaker opens</b> once most calls fail, so clients fail fast instead of piling on (grey = short-circuited). It lets a few probe calls through in half-open state and closes when they succeed.'
        : '<b>No retries:</b> the dependency sees normal load and recovers instantly, but every failure during the outage goes straight to the user. Retries should be bounded and backed off, not removed.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, nb = sim.att.length, cut = Math.floor(s.reveal * nb);
      const mx = Math.max(CAP * B * 1.8, ...sim.att.map((a, i) => a + sim.short[i])) * 1.05;
      const v = D.view(c, { x0: 0, x1: H, y0: 0, y1: mx, pad: 14, padL: 44, padB: 40 });
      ctx.fillStyle = P.alpha('err', .07); ctx.fillRect(v.sx(OUT[0]), v.sy(mx), v.sx(OUT[1]) - v.sx(OUT[0]), v.sy(0) - v.sy(mx));
      D.text(ctx, 'dependency down', v.sx(7.5), v.sy(mx) + 10, { color: P.err, size: 10.5, align: 'center', weight: 600 });
      D.axes(ctx, v, P, { xTicks: [0, 5, 10, 15, 20], yTicks: [CAP * B], fmtY: () => 'capacity', xLabel: 'seconds' });
      D.line(ctx, v.sx(0), v.sy(CAP * B), v.sx(H), v.sy(CAP * B), P.err, 1.2, [5, 4]);
      const bw = v.sx(B) - v.sx(0);
      for (let i = 0; i < cut; i++) {
        const x = v.sx(i * B) + .5, okH = sim.ok[i], fail = sim.att[i] - sim.ok[i], sh = sim.short[i];
        ctx.fillStyle = P.ok; ctx.fillRect(x, v.sy(okH), bw - 1, v.sy(0) - v.sy(okH));
        ctx.fillStyle = P.err; ctx.fillRect(x, v.sy(okH + fail), bw - 1, v.sy(okH) - v.sy(okH + fail));
        ctx.fillStyle = P.alpha('faint', .45); ctx.fillRect(x, v.sy(okH + fail + sh), bw - 1, v.sy(okH + fail) - v.sy(okH + fail + sh));
      }
      if (s.breaker) {
        for (let i = 0; i < cut; i++) {
          const st = sim.state[i];
          ctx.fillStyle = st === 'open' ? P.err : st === 'half' ? P.series[1] : P.ok;
          ctx.fillRect(v.sx(i * B), c.h - 18, bw, 6);
        }
        D.text(ctx, 'breaker: green closed · orange half-open · red open', v.sx(0), c.h - 5, { color: P.faint, size: 9.5 });
      }
    };
    compute();
  },
});

/* ============================================= 12 · LSM storage engine == */
defineLab('sd-lsm', {
  title: 'Inside an LSM tree: memtable, SSTables, compaction',
  hint: 'Writes land in memory, get flushed to immutable files, and files get merged in the background. Then read a key and count the files it has to check.',
  mount(L) {
    const KEYS = 'abcdefghijkl'.split('');
    const r = rng(6);
    const s = { mem: new Map(), l0: [], l1: [], seq: 0, userWrites: 0, diskWrites: 0, bloom: true, probe: null, wal: [], flash: null };
    const c = L.canvas(w => Math.min(340, w * .52));
    L.button('Write a random key', () => { write(); }, 'primary');
    L.button('Write 8 keys', () => { for (let i = 0; i < 8; i++) write(true); update(); });
    L.button('Read a random key', () => read(KEYS[Math.floor(r() * KEYS.length)]), 'primary');
    L.button('Compact now', () => { compact(); update(); });
    L.toggle('Bloom filters on SSTables', s.bloom, v => { s.bloom = v; update(); });
    L.button('Reset', () => { Object.assign(s, { mem: new Map(), l0: [], l1: [], seq: 0, userWrites: 0, diskWrites: 0, probe: null, wal: [] }); update(); });
    const bloomOf = keys => { const bits = new Set(); keys.forEach(k => { bits.add(fnv(k, 1) % 24); bits.add(fnv(k, 2) % 24); }); return bits; };
    const mayContain = (sst, k) => sst.bloom.has(fnv(k, 1) % 24) && sst.bloom.has(fnv(k, 2) % 24);
    function write(silent) {
      const k = KEYS[Math.floor(r() * KEYS.length)];
      s.seq++; s.userWrites++;
      s.mem.set(k, s.seq);
      s.wal.push(`${k}${s.seq}`); if (s.wal.length > 14) s.wal.shift();
      s.diskWrites += .25;
      s.probe = null;
      if (s.mem.size >= 4) flush();
      if (!silent) update();
    }
    function flush() {
      const entries = [...s.mem.entries()].sort((a, b) => a[0] < b[0] ? -1 : 1);
      s.l0.unshift({ entries, bloom: bloomOf(entries.map(e => e[0])), born: performance.now() });
      s.diskWrites += entries.length;
      s.mem = new Map(); s.wal = [];
      s.flash = 'flush';
      if (s.l0.length > 3) compact();
    }
    function compact() {
      if (!s.l0.length) return;
      const merged = new Map();
      [...s.l1, ...[...s.l0].reverse()].forEach(sst => sst.entries.forEach(([k, v]) => { if (!merged.has(k) || merged.get(k) < v) merged.set(k, v); }));
      const entries = [...merged.entries()].sort((a, b) => a[0] < b[0] ? -1 : 1);
      s.diskWrites += entries.length;
      s.l1 = [{ entries, bloom: bloomOf(entries.map(e => e[0])) }];
      s.l0 = [];
      s.flash = 'compact';
    }
    function read(k) {
      const steps = [{ where: 'mem', hit: s.mem.has(k) }];
      let found = s.mem.has(k) ? s.mem.get(k) : null;
      const files = [...s.l0.map((f, i) => ['l0', i, f]), ...s.l1.map((f, i) => ['l1', i, f])];
      for (const [lvl, i, f] of files) {
        if (found != null) break;
        const maybe = !s.bloom || mayContain(f, k), has = f.entries.find(e => e[0] === k);
        steps.push({ where: lvl, i, skipped: !maybe, hit: !!has && maybe });
        if (has && maybe) found = has[1];
      }
      s.probe = { k, steps, found, shown: 0 };
      L.tween(steps.length * 380, t => { s.probe.shown = Math.ceil(t * steps.length); L.redraw(); }, update);
      update();
    }
    function update() {
      const p = s.probe, touched = p ? p.steps.filter(x => x.where !== 'mem' && !x.skipped).length : null;
      L.stats([['user writes', s.userWrites], ['write amplification', s.userWrites ? `${fmtN(s.diskWrites / s.userWrites, 2)}×` : '—', 'accent'], ['SSTables', s.l0.length + s.l1.length], p && ['last read', `${p.k} → ${p.found != null ? `v${p.found}` : 'not found'}`], p && ['files read from disk', touched, touched > 2 ? 'err' : 'ok']]);
      L.insight(p ? (p.found == null ? `<b>Key “${p.k}” does not exist</b>, yet a read has to prove that by checking every level. ${s.bloom ? 'Bloom filters answer “definitely not here” for most files without touching disk.' : 'Without bloom filters that means opening every SSTable. Turn them on.'}` : `<b>Read “${p.k}”</b>: memtable first, then SSTables newest to oldest, stopping at the first match. Newer files shadow older versions of the same key.`)
        : s.flash === 'compact' ? '<b>Compaction merged the files</b>, keeping only the newest version of each key. Reads get faster, but the data was written to disk again: that rewriting is write amplification.'
        : s.flash === 'flush' ? '<b>The memtable was full, so it was flushed</b> as an immutable sorted file (SSTable). Writes never modify files in place, which is why LSM trees are fast for write-heavy workloads like Bigtable, Cassandra and RocksDB.'
        : '<b>Writes append to the write-ahead log and go into the in-memory memtable.</b> Nothing on disk is updated in place.');
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, step = i => s.probe && s.probe.shown > i ? s.probe.steps[i] : null;
      const tile = (x, y, k, v, hl) => {
        ctx.fillStyle = hl ? P.accent : P.surface; D.rrect(ctx, x, y, 34, 22, 5); ctx.fill();
        ctx.strokeStyle = P.strong; ctx.lineWidth = 1; ctx.stroke();
        D.text(ctx, `${k}:${v}`, x + 17, y + 11, { color: hl ? P.surface : P.text, size: 10.5, align: 'center', mono: true, weight: 600 });
      };
      const box = (x, y, w, h, title, stepInfo) => {
        ctx.fillStyle = P.surface2; D.rrect(ctx, x, y, w, h, 10); ctx.fill();
        ctx.strokeStyle = stepInfo ? (stepInfo.skipped ? P.faint : stepInfo.hit ? P.ok : P.accent) : P.strong;
        ctx.lineWidth = stepInfo ? 2.4 : 1.2;
        if (stepInfo?.skipped) ctx.setLineDash([5, 4]);
        ctx.stroke(); ctx.setLineDash([]);
        D.text(ctx, title, x + 8, y + 11, { color: P.dim, size: 10.5, weight: 600 });
        if (stepInfo?.skipped) D.text(ctx, 'bloom: not here', x + w - 8, y + 11, { color: P.faint, size: 9.5, align: 'right' });
      };
      D.text(ctx, 'RAM', 10, 16, { color: P.faint, size: 10, weight: 700 });
      const mw = Math.min(200, c.w * .38);
      box(10, 24, mw, 58, 'memtable (sorted, in memory)', step(0));
      [...s.mem.entries()].sort().forEach(([k, v], i) => tile(18 + i * 40, 46, k, v, s.probe?.k === k && step(0)));
      const wx = mw + 30;
      D.text(ctx, 'write-ahead log (append-only, on disk)', wx, 32, { color: P.dim, size: 10.5, weight: 600 });
      s.wal.forEach((w, i) => { ctx.fillStyle = P.alpha('faint', .25); D.rrect(ctx, wx + i * 26, 42, 23, 18, 4); ctx.fill(); D.text(ctx, w, wx + i * 26 + 11.5, 51, { color: P.dim, size: 9, align: 'center', mono: true }); });
      D.line(ctx, 10, 96, c.w - 10, 96, P.soft, 1, [4, 4]);
      D.text(ctx, 'DISK', 10, 108, { color: P.faint, size: 10, weight: 700 });
      const fw = Math.min(160, (c.w - 40) / 4);
      D.text(ctx, 'L0: flushed SSTables, newest first', 10, 124, { color: P.dim, size: 10.5 });
      s.l0.forEach((f, i) => {
        const x = 10 + i * (fw + 8), si = 1 + i;
        box(x, 132, fw, 34 + Math.ceil(f.entries.length / 4) * 26, `SSTable ${s.l0.length - i}`, step(si));
        f.entries.forEach(([k, v], j) => tile(x + 6 + (j % 4) * 37, 152 + Math.floor(j / 4) * 26, k, v, s.probe?.k === k && step(si)?.hit));
      });
      const l1y = Math.max(210, c.h - 104);
      D.text(ctx, 'L1: compacted, one sorted run per key range', 10, l1y - 8, { color: P.dim, size: 10.5 });
      s.l1.forEach(f => {
        const si = 1 + s.l0.length;
        const w = Math.min(c.w - 20, 12 + Math.min(12, f.entries.length) * 37 + 4);
        box(10, l1y, w, 34 + Math.ceil(f.entries.length / 12) * 26, 'SSTable (L1)', step(si));
        f.entries.forEach(([k, v], j) => tile(16 + (j % 12) * 37, l1y + 20 + Math.floor(j / 12) * 26, k, v, s.probe?.k === k && step(si)?.hit));
      });
    };
    update();
  },
});
