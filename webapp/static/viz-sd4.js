/* ============================================================================
   System Design labs, part 4: the arithmetic of distributed systems.

     sd-queueing     utilization vs latency: the M/M/c hockey stick, live
     sd-availability composing nines: series, redundancy, soft dependencies
     sd-clocks       Lamport and vector clocks on three processes
     sd-gossip       epidemic broadcast: push, pull, fanout and dead nodes
     sd-erasure      replication vs Reed–Solomon erasure coding

   Object-spec labs (viz.js createLab). Placed by SD_LABS in sd.js and by
   data-viz placeholders in CSFundamentals. Wrapped in a block because every
   script shares one global scope.
   ========================================================================= */
'use strict';
{
const fillRR = (ctx, x, y, w, h, r, fill, stroke, lw = 1.2) => {
  D.rrect(ctx, x, y, w, h, r);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
};
const expo = (r, mean) => -Math.log(1 - r()) * mean;
const fmtMs = ms => !Number.isFinite(ms) ? '∞' : ms < 1 ? `${fmtN(ms, 2)} ms` : ms < 1000 ? `${fmtN(ms, ms < 10 ? 1 : 0)} ms` : `${fmtN(ms / 1000, 1)} s`;
function erlangC(c, a) {
  if (a / c >= 1) return 1;
  let sum = 0, term = 1;
  for (let k = 0; k < c; k++) { if (k) term *= a / k; sum += term; }
  const top = term * a / c / (1 - a / c);
  return top / (sum + top);
}

/* ========================================================== sd-queueing == */
defineLab('sd-queueing', {
  title: 'Why latency explodes near 100% utilization',
  hint: 'Requests arrive at random (rate <b>λ</b>) and each takes a random time to serve (average <b>S</b>). Push the load up and watch the queue — and the response-time curve — bend like a hockey stick long before the servers are “full”.',
  mount(L) {
    const r = rng(31);
    const s = { lam: 60, S: 40, c: 4, t: 0 };
    const c = L.canvas(w => Math.min(360, Math.max(300, w * .5)));
    L.slider('arrival rate λ (requests/s)', { min: 5, max: 400, step: 5, value: s.lam }, v => { s.lam = v; update(); });
    L.slider('average service time S (ms)', { min: 5, max: 200, step: 5, value: s.S }, v => { s.S = v; update(); });
    L.slider('servers c (one shared queue)', { min: 1, max: 16, step: 1, value: s.c }, v => { s.c = v; st.srv = Array.from({ length: s.c }, (_, i) => st.srv[i] || { until: 0, busy: false }); update(); });
    const run = L.loop(dt => { tick(dt); L.redraw(); s.acc = (s.acc || 0) + dt; if (s.acc > .4) { s.acc = 0; update(); } });
    L.playButton(run, ['Run the traffic', 'Pause']);
    L.button('Set load to 50%', () => setRho(.5));
    L.button('80%', () => setRho(.8));
    L.button('95%', () => setRho(.95));
    const lamSlider = L.sliders.querySelector('input');
    function setRho(rho) { const v = Math.round(rho * s.c * 1000 / s.S / 5) * 5; lamSlider.value = clamp(v, 5, 400); lamSlider.dispatchEvent(new Event('input')); resetSim(); }
    let st;
    function resetSim() { st = { q: [], srv: Array.from({ length: s.c }, () => ({ until: 0, busy: false })), next: 0, done: 0, sum: 0, fly: [], hist: [] }; s.t = 0; }
    function tick(dt) {
      const speed = 7 / s.lam;
      const end = s.t + dt * speed;
      while (true) {
        const nextDone = Math.min(...st.srv.filter(x => x.busy).map(x => x.until), Infinity);
        const nextEv = Math.min(st.next, nextDone);
        if (nextEv > end) break;
        s.t = nextEv;
        if (nextEv === st.next) { st.q.push({ born: s.t }); st.next = s.t + expo(r, 1 / s.lam); }
        st.srv.forEach(x => { if (x.busy && x.until <= s.t) { x.busy = false; st.done++; st.sum += s.t - x.job.born; st.hist.push(s.t - x.job.born); if (st.hist.length > 400) st.hist.shift(); } });
        st.srv.forEach(x => { if (!x.busy && st.q.length) { x.job = st.q.shift(); x.busy = true; x.start = s.t; x.until = s.t + expo(r, s.S / 1000); } });
        if (st.q.length > 400) st.q.splice(0, st.q.length - 400);
      }
      s.t = end;
    }
    function model(lam = s.lam, cc = s.c) {
      const mu = 1000 / s.S, a = lam / mu, rho = a / cc;
      if (rho >= 1) return { rho, W: Infinity, Wq: Infinity, C: 1, p99q: Infinity };
      const C = erlangC(cc, a), Wq = C / (cc * mu - lam), W = Wq + 1 / mu;
      const p99q = C > .01 ? Math.log(C / .01) / (cc * mu - lam) : 0;
      return { rho, W: W * 1000, Wq: Wq * 1000, C, p99q: p99q * 1000 };
    }
    function update() {
      const m = model(), meas = st.done ? st.sum / st.done * 1000 : 0;
      const sorted = [...st.hist].sort((a, b) => a - b), p99 = sorted.length > 50 ? sorted[Math.floor(sorted.length * .99)] * 1000 : null;
      L.stats([['utilization ρ', `${Math.round(m.rho * 100)}%`, m.rho >= .9 ? 'err' : m.rho >= .7 ? 'accent' : 'ok'], ['mean response W', fmtMs(m.W), 'accent'], ['× service time', Number.isFinite(m.W) ? `${fmtN(m.W / s.S, 1)}×` : '∞'],
        ['requests in system L = λW', Number.isFinite(m.W) ? fmtN(s.lam * m.W / 1000, 1) : '∞'], ['p99 wait in queue', fmtMs(m.p99q)], ['simulated mean / p99', `${st.done > 20 ? fmtMs(meas) : '—'} / ${p99 != null ? fmtMs(p99) : '—'}`]]);
      L.insight(m.rho >= 1
        ? `<b>Overloaded:</b> ${s.lam} requests/s arrive but ${s.c} server${s.c > 1 ? 's' : ''} can only finish ${fmtN(s.c * 1000 / s.S, 0)}/s. The queue grows without limit and so does latency — no amount of waiting fixes it. Shed load, add capacity, or apply backpressure.`
        : `With randomness in arrivals and service, waiting grows like <b>1 / (1 − ρ)</b>. For one server: 50% busy → responses take 2× the service time, 80% → 5×, 90% → 10×, 95% → 20×. That is why latency-sensitive services are scaled out at around 60–70% utilization, and why a “small” traffic bump near saturation causes an outage. More servers sharing one queue flatten the curve (pooling), which is one reason big shared pools beat many small ones.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, simH = 118;
      const qx = 16, qw = Math.min(c.w * .45, 360), sx = qx + qw + 30, sw = Math.min(46, (c.w - sx - 16) / Math.max(4, Math.ceil(s.c / 2)) - 6);
      D.text(ctx, `queue: ${st.q.length} waiting`, qx, 14, { color: P.dim, size: 10.5, weight: 600 });
      const shown = Math.min(st.q.length, Math.floor(qw / 11));
      for (let i = 0; i < shown; i++) D.dot(ctx, qx + qw - 6 - i * 11, 46, 4.5, st.q.length > shown && i === shown - 1 ? P.err : P.accent);
      if (st.q.length > shown) D.text(ctx, `+${st.q.length - shown}`, qx, 66, { color: P.err, size: 10.5, weight: 700 });
      D.line(ctx, qx, 58, qx + qw, 58, P.border, 1);
      D.text(ctx, 'servers', sx, 14, { color: P.dim, size: 10.5, weight: 600 });
      st.srv.forEach((x, i) => {
        const col = i % Math.ceil(s.c / 2), row = Math.floor(i / Math.ceil(s.c / 2)), bx = sx + col * (sw + 6), by = 24 + row * 44;
        fillRR(ctx, bx, by, sw, 36, 6, x.busy ? P.alpha(P.series[2], .3) : P.surface2, x.busy ? P.series[2] : P.border);
        if (x.busy) { const p = clamp((s.t - x.start) / Math.max(1e-6, x.until - x.start), 0, 1); fillRR(ctx, bx + 4, by + 27, (sw - 8) * p, 4, 2, P.series[2]); }
      });
      const gx = 52, gy = simH + 14, gw = c.w - gx - 20, gh = c.h - gy - 30, YMAX = 20;
      const X = rho => gx + gw * rho, Y = k => gy + gh - gh * Math.min(k, YMAX) / YMAX;
      [0, .2, .4, .6, .8, 1].forEach(v => { D.line(ctx, X(v), gy, X(v), gy + gh, P.soft, 1); D.text(ctx, `${v * 100}%`, X(v), gy + gh + 12, { color: P.faint, size: 10, align: 'center', mono: true }); });
      [1, 5, 10, 15, 20].forEach(v => { D.line(ctx, gx, Y(v), gx + gw, Y(v), P.soft, 1); D.text(ctx, `${v}×`, gx - 6, Y(v), { color: P.faint, size: 10, align: 'right', mono: true }); });
      D.text(ctx, 'response time ÷ service time', gx + 4, gy + 8, { color: P.dim, size: 10.5 });
      D.text(ctx, 'utilization ρ →', gx + gw, gy + gh - 8, { color: P.dim, size: 10.5, align: 'right' });
      ctx.save(); ctx.fillStyle = P.alpha('err', .06); ctx.fillRect(X(.8), gy, X(1) - X(.8), gh); ctx.restore();
      const curve = (cc, col, w, dash) => {
        ctx.save(); if (dash) ctx.setLineDash(dash); ctx.beginPath();
        for (let k = 0; k <= 200; k++) { const rho = k / 200 * .995, m = model(rho * cc * 1000 / s.S, cc), y = Y(m.W / s.S); k ? ctx.lineTo(X(rho), y) : ctx.moveTo(X(rho), y); }
        ctx.strokeStyle = col; ctx.lineWidth = w; ctx.stroke(); ctx.restore();
      };
      if (s.c > 1) { curve(1, P.faint, 1.4, [4, 4]); D.text(ctx, '1 server', X(.86), Y(model(.86 * 1000 / s.S, 1).W / s.S) - 10, { color: P.faint, size: 10, align: 'right' }); }
      curve(s.c, P.accent, 2.6);
      const m = model();
      if (m.rho < 1) { D.dot(ctx, X(m.rho), Y(m.W / s.S), 6, P.accent, P.bg, 2); D.text(ctx, `you: ${Math.round(m.rho * 100)}%, ${fmtN(m.W / s.S, 1)}×`, X(m.rho) - 10, Y(m.W / s.S) - 14, { color: P.text, size: 11, align: 'right', weight: 700 }); }
      else D.text(ctx, 'ρ ≥ 100%: unstable', X(1) - 6, gy + 24, { color: P.err, size: 11.5, align: 'right', weight: 700 });
    };
    resetSim(); update();
  },
});

/* ======================================================= sd-availability == */
defineLab('sd-availability', {
  title: 'Composing nines: how a request path’s availability adds up',
  hint: 'Components a request <b>must</b> pass through multiply (series). Redundant copies only fail together (parallel). Change the design and watch the yearly downtime — then simulate a year against your SLO.',
  mount(L) {
    const r = rng(8);
    const s = { app: 2, db: 'standby', cache: 'soft', deps: 2, region: 1, slo: .999, year: null, yt: 1 };
    const c = L.canvas(w => Math.min(300, Math.max(250, w * .4)));
    L.slider('app servers behind the load balancer (99.5% each)', { min: 1, max: 6, step: 1, value: s.app }, v => { s.app = v; update(); });
    L.slider('other services called in series (99.9% each)', { min: 0, max: 10, step: 1, value: s.deps }, v => { s.deps = v; update(); });
    L.seg('database', [['single', 'Single primary'], ['standby', 'Primary + auto-failover standby']], s.db, v => { s.db = v; update(); });
    L.seg('cache', [['hard', 'Hard dependency'], ['soft', 'Soft (fall back to DB)']], s.cache, v => { s.cache = v; update(); });
    L.seg('regions', [[1, 'One region'], [2, 'Two regions, active-active']], s.region, v => { s.region = v; update(); });
    L.seg('SLO', [[.99, '99%'], [.999, '99.9%'], [.9995, '99.95%'], [.9999, '99.99%']], s.slo, v => { s.slo = v; update(); });
    const yr = L.loop(dt => { s.yt = Math.min(1, s.yt + dt / 3); L.redraw(); if (s.yt >= 1) { update(); return false; } });
    L.button('Simulate a year', () => { simulate(); s.yt = 0; yr.start(); }, 'primary');
    const par = (a, n) => 1 - Math.pow(1 - a, n);
    function tiers() {
      const t = [['DNS + load balancer', .9999], [`App ×${s.app}`, par(.995, s.app)]];
      if (s.cache === 'hard') t.push(['Cache', .999]);
      t.push([s.db === 'single' ? 'Database' : 'DB primary + standby', s.db === 'single' ? .999 : par(.999, 2)]);
      if (s.deps) t.push([`${s.deps} downstream service${s.deps > 1 ? 's' : ''}`, Math.pow(.999, s.deps)]);
      return t;
    }
    function total() { const regionA = tiers().reduce((a, [, x]) => a * x, 1) * .9995; return s.region === 2 ? par(regionA, 2) : regionA; }
    const nines = a => -Math.log10(1 - a);
    const down = a => { const m = (1 - a) * 525600; return m < 1 ? `${fmtN(m * 60, 0)} s` : m < 120 ? `${fmtN(m, m < 10 ? 1 : 0)} min` : `${fmtN(m / 60, 1)} h`; };
    function simulate() {
      const A = total(), minutes = (1 - A) * 525600, mean = 40, n = Math.max(0, Math.round(minutes / mean + (r() - .5) * 2));
      const days = Array(365).fill(0);
      for (let i = 0; i < n; i++) days[Math.floor(r() * 365)] += expo(r, minutes / Math.max(1, n));
      s.year = days;
    }
    function update() {
      const A = total(), budget = (1 - s.slo) * 43200;
      const used = s.year ? s.year.reduce((a, b) => a + b, 0) : null;
      L.stats([['availability', `${fmtN(A * 100, A > .9999 ? 4 : 3)}%`, A >= s.slo ? 'ok' : 'err'], ['nines', fmtN(nines(A), 1), 'accent'], ['downtime / year', down(A)], ['downtime / month', `${fmtN((1 - A) * 43200, 1)} min`],
        ['SLO error budget / month', `${fmtN(budget, 1)} min`], used != null ? ['simulated downtime this year', `${fmtN(used / 60, 1)} h`, used / 12 > budget ? 'err' : 'ok'] : null]);
      const worst = tiers().reduce((a, b) => (b[1] < a[1] ? b : a));
      L.insight(`Series multiplies: ${tiers().length + 1} hard dependencies at “three nines” each already cost more than three nines together, and the weakest link here is <b>${worst[0]}</b> at ${fmtN(worst[1] * 100, 3)}%. Redundancy adds nines only when copies fail <i>independently</i> and failover is automatic and tested — two replicas in the same rack, or a standby nobody has promoted in a year, do not count. Making a dependency <b>soft</b> (serve stale, degrade, fall back) removes it from the product entirely, which is often cheaper than another nine.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, t = tiers(), n = t.length, top = 24, bw = Math.min(150, (c.w - 40 - (n - 1) * 18) / n), bh = 64;
      const regions = s.region;
      for (let g = 0; g < regions; g++) {
        const y = top + g * (bh + 26);
        D.text(ctx, regions > 1 ? `region ${g + 1} (whole-region outage risk: 99.95%)` : 'one region (whole-region outage risk: 99.95%)', 16, y - 7, { color: P.faint, size: 10 });
        t.forEach(([name, a], i) => {
          const x = 16 + i * (bw + 18), col = a >= .9999 ? P.ok : a >= .999 ? P.accent : P.err;
          fillRR(ctx, x, y, bw, regions > 1 ? bh - 14 : bh, 8, P.alpha(col, .12), col, 1.4);
          let fs = 11; D.font(ctx, fs, 650); while (fs > 8 && ctx.measureText(name).width > bw - 10) { fs -= .5; D.font(ctx, fs, 650); }
          D.text(ctx, name, x + bw / 2, y + 18, { color: P.text, size: fs, align: 'center', weight: 650 });
          D.text(ctx, `${fmtN(a * 100, a > .9999 ? 4 : 3)}%`, x + bw / 2, y + 40, { color: col, size: 12, align: 'center', mono: true, weight: 700 });
          if (i < n - 1) D.arrow(ctx, x + bw + 2, y + (regions > 1 ? bh - 14 : bh) / 2, x + bw + 16, y + (regions > 1 ? bh - 14 : bh) / 2, P.strong, 1.6, 7);
        });
      }
      const sy = c.h - 58;
      D.text(ctx, s.year ? 'a simulated year: each cell is a day, darker = more downtime' : 'press “Simulate a year” to see how downtime actually lands', 16, sy - 10, { color: P.dim, size: 10.5 });
      const cols = 73, cw = (c.w - 32) / cols;
      for (let d = 0; d < 365; d++) {
        const x = 16 + (d % cols) * cw, y = sy + Math.floor(d / cols) * 9;
        const shown = s.year && d / 365 <= s.yt, m = shown ? s.year[d] : 0;
        const budgetDay = (1 - s.slo) * 1440;
        fillRR(ctx, x + .5, y, cw - 1, 7.5, 1.5, !shown ? P.surface2 : m === 0 ? P.alpha('ok', .35) : m > budgetDay * 30 ? P.err : P.alpha('err', .45 + .5 * Math.min(1, m / 120)));
      }
    };
    update();
  },
});

/* ============================================================ sd-clocks == */
defineLab('sd-clocks', {
  title: 'Logical clocks: Lamport timestamps and vector clocks',
  hint: 'Three processes with no shared clock. Add local events and send messages, then <b>click two events</b> to ask: did one happen before the other, or are they concurrent? Messages take a while to arrive, so you can create concurrency on purpose.',
  mount(L) {
    const s = { from: 0, to: 1, show: 'both', sel: [] };
    const NAMES = ['A', 'B', 'C'];
    const c = L.canvas(w => Math.min(330, Math.max(270, w * .44)));
    L.seg('process', [[0, 'A'], [1, 'B'], [2, 'C']], s.from, v => { s.from = v; if (s.to === v) toSeg.set((v + 1) % 3, true), s.to = (v + 1) % 3; });
    L.button('Local event', () => local(s.from), 'primary');
    const toSeg = L.seg('send to', [[0, 'A'], [1, 'B'], [2, 'C']], s.to, v => { s.to = v; });
    L.button('Send message', () => { if (s.to !== s.from) send(s.from, s.to); }, 'primary');
    L.seg('show', [['lamport', 'Lamport'], ['vector', 'Vector'], ['both', 'Both']], s.show, v => { s.show = v; L.redraw(); });
    L.button('Load an example', () => example());
    L.button('Clear', () => reset());
    const anim = L.loop(dt => { let live = false; st.msgs.forEach(m => { if (!m.done) { m.t += dt / 1.3; live = true; if (m.t >= 1) deliver(m); } }); L.redraw(); if (!live) return false; });
    let st;
    function reset() { st = { tick: 0, ev: [], L: [0, 0, 0], V: [[0, 0, 0], [0, 0, 0], [0, 0, 0]], msgs: [] }; s.sel = []; update(); }
    function add(p, kind, extra = {}) { const e = { id: st.ev.length, p, kind, x: st.tick++, L: st.L[p], V: st.V[p].slice(), ...extra }; st.ev.push(e); return e; }
    function local(p) { st.L[p]++; st.V[p][p]++; add(p, 'local'); update(); }
    function send(a, b) {
      st.L[a]++; st.V[a][a]++;
      const e = add(a, 'send', { to: b });
      st.msgs.push({ from: e, to: b, t: 0, done: false, L: st.L[a], V: st.V[a].slice() });
      anim.start(); update();
    }
    function deliver(m) {
      m.done = true;
      const b = m.to;
      st.L[b] = Math.max(st.L[b], m.L) + 1;
      st.V[b] = st.V[b].map((v, i) => Math.max(v, m.V[i])); st.V[b][b]++;
      m.recv = add(b, 'recv', { src: m.from.id });
      update();
    }
    function example() {
      reset();
      local(0); send(0, 1); local(2);
      st.msgs.forEach(m => { m.t = 1; deliver(m); });
      local(1); send(2, 0); local(0); send(1, 2);
      st.msgs.forEach(m => { if (!m.done) { m.t = 1; deliver(m); } });
      local(2); local(1);
      update();
    }
    const leq = (a, b) => a.every((v, i) => v <= b[i]);
    function relation(a, b) {
      if (a.id === b.id) return 'same';
      if (leq(a.V, b.V)) return 'before';
      if (leq(b.V, a.V)) return 'after';
      return 'concurrent';
    }
    const vstr = v => `[${v.join(',')}]`;
    function update() {
      const [a, b] = s.sel.map(i => st.ev[i]);
      let msg = 'Click an event to see its <b>causal past</b> (everything that could have influenced it), then click a second event to compare them.';
      if (a && !b) msg = `Event ${NAMES[a.p]}${a.L} (Lamport ${a.L}, vector ${vstr(a.V)}) — the shaded events are its causal past: every event with a vector clock ≤ ${vstr(a.V)} in every position. Click another event to compare.`;
      if (a && b) {
        const rel = relation(a, b), nA = `${NAMES[a.p]}:${vstr(a.V)}`, nB = `${NAMES[b.p]}:${vstr(b.V)}`;
        if (rel === 'concurrent') msg = `<b>Concurrent.</b> Neither vector is ≤ the other (${vstr(a.V)} vs ${vstr(b.V)}), so no chain of messages connects them. Yet their Lamport timestamps are ${a.L} and ${b.L}${a.L !== b.L ? ` — Lamport puts one “first”, which is exactly its limitation: <b>L(a) &lt; L(b) does not mean a happened before b</b>` : ''}. Detecting concurrent writes like these is why Dynamo-style stores keep vector clocks (or version vectors) and return both versions as siblings.`;
        else msg = `<b>${rel === 'before' ? nA : nB} happened before ${rel === 'before' ? nB : nA}.</b> Its vector is ≤ the other’s in every position, so a chain of local steps and messages links them, and Lamport agrees (${Math.min(a.L, b.L)} &lt; ${Math.max(a.L, b.L)}). Rule: a → b implies L(a) &lt; L(b), but not the reverse — only vector clocks can tell “before” from “concurrent”.`;
      }
      L.stats([['events', st.ev.length], ['messages in flight', st.msgs.filter(m => !m.done).length, 'accent'], ...[0, 1, 2].map(p => [`${NAMES[p]} clock`, s.show === 'lamport' ? st.L[p] : s.show === 'vector' ? vstr(st.V[p]) : `${st.L[p]} · ${vstr(st.V[p])}`])]);
      L.insight(`${msg}<br><br><b>Rules.</b> Lamport: tick before each event; on receive, take max(mine, message) + 1. Vector: tick your own slot; on receive, take the element-wise max, then tick. Wall clocks cannot do this job — NTP skew of even a few milliseconds reorders events, which is why Spanner needed TrueTime’s bounded uncertainty to use physical time.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, left = 44, right = c.w - 16, n = Math.max(st.tick, 8), X = x => left + (right - left) * (x + .5) / (n + .5), Y = p => 44 + p * ((c.h - 80) / 2);
      NAMES.forEach((nm, p) => {
        D.line(ctx, left, Y(p), right, Y(p), P.border, 1.4);
        D.text(ctx, nm, 14, Y(p), { color: P.series[p], size: 14, weight: 700 });
      });
      const [a] = s.sel.map(i => st.ev[i]);
      const past = a ? new Set(st.ev.filter(e => leq(e.V, a.V)).map(e => e.id)) : null;
      st.msgs.forEach(m => {
        const x0 = X(m.from.x), y0 = Y(m.from.p), y1 = Y(m.to);
        if (m.done) { D.arrow(ctx, x0, y0, X(m.recv.x), y1, P.alpha(P.series[m.from.p], .6), 1.4, 8); return; }
        const x1 = X(st.tick), f = easeOut(Math.min(1, m.t));
        ctx.save(); ctx.setLineDash([3, 4]); D.line(ctx, x0, y0, lerp(x0, x1, f), lerp(y0, y1, f), P.alpha(P.series[m.from.p], .6), 1.2); ctx.restore();
        D.dot(ctx, lerp(x0, x1, f), lerp(y0, y1, f), 5, P.series[m.from.p]);
      });
      st.ev.forEach(e => {
        const x = X(e.x), y = Y(e.p), selIdx = s.sel.indexOf(e.id), inPast = past && past.has(e.id);
        if (inPast) D.dot(ctx, x, y, 13, P.alpha('accent', .16));
        D.dot(ctx, x, y, e.kind === 'local' ? 6 : 7, selIdx >= 0 ? P.accent : e.kind === 'local' ? P.surface2 : P.series[e.p], selIdx >= 0 ? P.text : P.series[e.p], 2);
        const lab = s.show === 'lamport' ? `${e.L}` : s.show === 'vector' ? vstr(e.V) : `${e.L} ${vstr(e.V)}`;
        const k = st.ev.filter(o => o.p === e.p && o.id < e.id).length;
        D.text(ctx, lab, x, y + (k % 2 ? 19 : -16), { color: selIdx >= 0 ? P.accent : P.dim, size: 10, align: 'center', mono: true, weight: selIdx >= 0 ? 700 : 500 });
      });
      e0Hit = (px, py) => { let best = null, bd = 14; st.ev.forEach(e => { const d = Math.hypot(X(e.x) - px, Y(e.p) - py); if (d < bd) { bd = d; best = e; } }); return best; };
      D.text(ctx, '○ local   ● send / receive   ⟶ message', right, 10, { color: P.faint, size: 10, align: 'right' });
    };
    let e0Hit = () => null;
    L.drag(c, {
      hit: () => null,
      down: (x, y) => {
        const e = e0Hit(x, y);
        if (!e) { s.sel = []; update(); return; }
        s.sel = s.sel.length >= 2 || s.sel.includes(e.id) ? [e.id] : [...s.sel, e.id];
        update();
      },
    });
    reset(); example();
  },
});

/* ============================================================ sd-gossip == */
defineLab('sd-gossip', {
  title: 'Gossip: spreading news through a cluster in O(log N) rounds',
  hint: 'One node learns something. Every round, each node that knows tells <b>fanout</b> random peers. No coordinator, no global view — yet the whole cluster hears within a handful of rounds, even with nodes dead.',
  mount(L) {
    const s = { N: 48, f: 2, mode: 'push', dead: 0, seed: 1 };
    const c = L.canvas(w => Math.min(340, Math.max(280, w * .46)));
    L.slider('cluster size N', { min: 8, max: 128, step: 8, value: s.N }, v => { s.N = v; reset(); });
    L.slider('fanout (peers contacted per round)', { min: 1, max: 4, step: 1, value: s.f }, v => { s.f = v; reset(); });
    L.seg('style', [['push', 'Push'], ['pull', 'Pull'], ['pushpull', 'Push-pull']], s.mode, v => { s.mode = v; reset(); });
    L.seg('dead nodes', [[0, 'none'], [.2, '20%'], [.4, '40%']], s.dead, v => { s.dead = v; reset(); });
    const run = L.loop(dt => { s.acc = (s.acc || 0) + dt; st.anim = Math.min(1, st.anim + dt * 1.6); if (s.acc > .9) { s.acc = 0; if (!round()) { L.redraw(); return false; } } L.redraw(); });
    L.playButton(run, ['Spread it', 'Pause'], () => { if (done()) reset(); });
    L.button('One round', () => round());
    L.button('Reset', () => { run.stop(); reset(); });
    let st, r;
    const alive = () => st.nodes.filter(n => !n.dead);
    const done = () => alive().every(n => n.know);
    function reset() {
      r = rng(s.seed++ * 7 + s.N);
      st = { nodes: Array.from({ length: s.N }, (_, i) => ({ i, know: false, dead: false, when: -1 })), round: 0, msgs: 0, lines: [], curve: [], anim: 1 };
      const idx = [...Array(s.N).keys()].slice(1);
      for (let k = 0; k < Math.round(s.N * s.dead); k++) { const j = Math.floor(r() * idx.length); st.nodes[idx.splice(j, 1)[0]].dead = true; }
      st.nodes[0].know = true; st.nodes[0].when = 0;
      st.curve.push(1 / alive().length);
      update();
    }
    function round() {
      if (done() || st.round > 40) return false;
      st.round++; st.lines = []; st.anim = 0;
      const knowers = st.nodes.filter(n => n.know && !n.dead), learn = new Set();
      const peer = self => { let j; do j = Math.floor(r() * s.N); while (j === self); return st.nodes[j]; };
      if (s.mode !== 'pull') knowers.forEach(n => { for (let k = 0; k < s.f; k++) { const p = peer(n.i); st.msgs++; st.lines.push([n.i, p.i, !p.dead]); if (!p.dead && !p.know) learn.add(p.i); } });
      if (s.mode !== 'push') st.nodes.filter(n => !n.know && !n.dead).forEach(n => { for (let k = 0; k < s.f; k++) { const p = peer(n.i); st.msgs++; if (p.know && !p.dead) { st.lines.push([p.i, n.i, true]); learn.add(n.i); } } });
      learn.forEach(i => { st.nodes[i].know = true; st.nodes[i].when = st.round; });
      st.curve.push(alive().filter(n => n.know).length / alive().length);
      update();
      return !done();
    }
    function update() {
      const a = alive(), k = a.filter(n => n.know).length;
      const expect = Math.log(s.N) / Math.log(s.f + 1) + Math.log(s.N);
      L.stats([['round', st.round, 'accent'], ['informed', `${k} / ${a.length} alive`, k === a.length ? 'ok' : ''], ['messages sent', st.msgs], ['messages per node', fmtN(st.msgs / s.N, 1)], ['rough estimate for push', `≈ ${fmtN(expect, 1)} rounds`]]);
      L.insight(`${done() ? `<b>Everyone alive knows after ${st.round} rounds.</b> ` : ''}The informed set roughly multiplies by (1 + fanout) each round at first, so reaching N nodes takes about log(N) rounds: doubling the cluster adds about one round. <b>Push</b> is fast early but slow at the end, when most messages hit nodes that already know. <b>Pull</b> is the opposite, so <b>push-pull</b> finishes fastest. Dead nodes only waste some messages — there is no single point of failure. Cassandra and ScyllaDB gossip membership and schema this way, and SWIM (Consul, memberlist) adds failure detection on top.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, gw = Math.min(c.h - 20, c.w * .56), cx = gw / 2 + 12, cy = c.h / 2, R = gw / 2 - 18;
      const pos = i => [cx + R * Math.cos(-Math.PI / 2 + i / s.N * Math.PI * 2), cy + R * Math.sin(-Math.PI / 2 + i / s.N * Math.PI * 2)];
      st.lines.forEach(([a, b, ok]) => {
        const [x0, y0] = pos(a), [x1, y1] = pos(b), f = easeOut(st.anim);
        D.line(ctx, x0, y0, lerp(x0, x1, f), lerp(y0, y1, f), ok ? P.alpha('accent', .45) : P.alpha('err', .35), 1.1);
      });
      const nr = Math.max(3.5, Math.min(8, 170 / s.N));
      st.nodes.forEach(n => {
        const [x, y] = pos(n.i);
        if (n.dead) { D.text(ctx, '✕', x, y, { color: P.faint, size: nr * 2, align: 'center', weight: 700 }); return; }
        D.dot(ctx, x, y, nr, n.know ? (n.when === st.round && st.round ? P.accent : P.ok) : P.surface2, n.know ? null : P.strong, 1.2);
      });
      D.text(ctx, `round ${st.round}`, cx, cy, { color: P.text, size: 14, align: 'center', weight: 700 });
      const gx = gw + 50, gwid = c.w - gx - 16, gy = 24, gh = c.h - 60;
      if (gwid < 120) return;
      D.text(ctx, 'fraction informed per round', gx, 12, { color: P.dim, size: 10.5 });
      D.line(ctx, gx, gy + gh, gx + gwid, gy + gh, P.border, 1); D.line(ctx, gx, gy, gx, gy + gh, P.border, 1);
      const R0 = Math.max(10, st.curve.length);
      for (let k = 0; k < R0; k += 2) D.text(ctx, k, gx + gwid * k / (R0 - 1), gy + gh + 12, { color: P.faint, size: 9.5, align: 'center', mono: true });
      ctx.beginPath();
      st.curve.forEach((v, k) => { const x = gx + gwid * k / (R0 - 1), y = gy + gh - gh * v; k ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
      ctx.strokeStyle = P.accent; ctx.lineWidth = 2.4; ctx.stroke();
      st.curve.forEach((v, k) => D.dot(ctx, gx + gwid * k / (R0 - 1), gy + gh - gh * v, 3, P.accent));
      D.text(ctx, '100%', gx - 4, gy, { color: P.faint, size: 9.5, align: 'right', mono: true });
    };
    reset();
  },
});

/* ============================================================ sd-erasure == */
defineLab('sd-erasure', {
  title: 'Replication vs. erasure coding: paying for durability',
  hint: 'An object is stored across separate disks. <b>Click disks</b> to fail them. With replication any one copy is enough; with Reed–Solomon RS(k, m) the object is cut into k data chunks plus m parity chunks, and <b>any k of the k+m</b> rebuild it.',
  mount(L) {
    const SCHEMES = { rep3: [1, 2, '3× replication'], rs42: [4, 2, 'RS(4, 2)'], rs63: [6, 3, 'RS(6, 3)'], rs104: [10, 4, 'RS(10, 4)'] };
    const s = { sch: 'rs63', failed: new Set(), rebuilt: new Map(), anim: null };
    const DISKS = 16;
    const c = L.canvas(w => Math.min(300, Math.max(240, w * .4)));
    L.seg('scheme', Object.entries(SCHEMES).map(([k, v]) => [k, v[2]]), s.sch, v => { s.sch = v; reset(); });
    L.button('Fail a random disk', () => { const ok = [...Array(DISKS).keys()].filter(i => !s.failed.has(i) && holder(i) != null); if (ok.length) { s.failed.add(ok[Math.floor(Math.random() * ok.length)]); update(); } });
    L.button('Rebuild lost chunks', () => rebuild(), 'primary');
    L.button('Reset', () => reset());
    const anim = L.loop(dt => { if (!s.anim) return false; s.anim.t += dt / 1.6; L.redraw(); if (s.anim.t >= 1) { s.anim.done(); s.anim = null; update(); return false; } });
    const k = () => SCHEMES[s.sch][0], m = () => SCHEMES[s.sch][1];
    let place = [];
    function reset() {
      s.failed = new Set(); s.anim = null;
      const n = k() + m(), step = DISKS / n;
      place = Array.from({ length: n }, (_, i) => Math.floor(i * step));
      update();
    }
    const holder = d => { const i = place.indexOf(d); return i < 0 ? null : i; };
    const label = i => s.sch === 'rep3' ? `copy ${i + 1}` : i < k() ? `D${i + 1}` : `P${i - k() + 1}`;
    const lost = () => place.map((d, i) => s.failed.has(d) ? i : -1).filter(i => i >= 0);
    const readable = () => place.length - lost().length >= k();
    function rebuild() {
      const gone = lost();
      if (!gone.length || !readable() || s.anim) return;
      const spares = [...Array(DISKS).keys()].filter(d => !s.failed.has(d) && holder(d) == null);
      const src = place.filter(d => !s.failed.has(d)).slice(0, k());
      const moves = gone.slice(0, spares.length).map((ci, j) => ({ ci, to: spares[j] }));
      s.anim = { t: 0, src, moves, done: () => moves.forEach(mv => { place[mv.ci] = mv.to; }) };
      anim.start();
    }
    function update() {
      const n = k() + m(), ok = readable(), gone = lost().length;
      L.stats([['storage used', `${fmtN(n / k(), 2)}× the data`, 'accent'], ['disk failures survived', m(), 'ok'], ['chunks lost now', gone, gone ? 'err' : ''],
        ['object', ok ? (gone ? 'readable (degraded)' : 'healthy') : 'LOST', ok ? (gone ? 'accent' : 'ok') : 'err'], ['to rebuild one chunk, read', `${k()} chunk${k() > 1 ? 's' : ''} (${k()}× its size)`]]);
      L.insight(!ok
        ? `<b>Data loss:</b> only ${n - gone} of ${n} chunks survive and ${k()} are needed. Durability is a race between failures and repair: the faster you rebuild, the less likely a further ${m() + 1 - gone > 0 ? 'failure' : 'loss'} lands in the window.`
        : s.sch === 'rep3'
          ? '3× replication survives two failures at 200% overhead. Its strengths are speed: reads can go to any copy, and repairing a lost copy reads just one other copy. GFS and classic HDFS store hot data this way.'
          : `${SCHEMES[s.sch][2]} survives ${m()} failures for only ${fmtN((n / k() - 1) * 100, 0)}% overhead — far cheaper than replication for the same or better durability. The price: every repair reads <b>${k()} chunks</b> across the network to rebuild one, and a degraded read must decode. So hot data stays replicated and warm or cold data is erasure-coded (Facebook f4 used RS(10, 4); HDFS supports RS(6, 3); Backblaze spreads 17 data + 3 parity shards across a vault).`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, cols = 8, dw = (c.w - 32) / cols, dh = Math.min(70, (c.h - 70) / 2);
      const posD = d => [16 + (d % cols) * dw, 30 + Math.floor(d / cols) * (dh + 18)];
      D.text(ctx, 'disks (each on a different machine and rack) — click to fail or recover', 16, 14, { color: P.dim, size: 10.5 });
      for (let d = 0; d < DISKS; d++) {
        const [x, y] = posD(d), ci = holder(d), dead = s.failed.has(d);
        const isParity = ci != null && s.sch !== 'rep3' && ci >= k();
        const col = dead ? P.err : ci == null ? P.border : isParity ? P.series[1] : P.series[0];
        fillRR(ctx, x + 4, y, dw - 8, dh, 8, dead ? P.alpha('err', .12) : ci != null ? P.alpha(col, .2) : P.surface2, col, 1.4);
        D.text(ctx, `disk ${d + 1}`, x + dw / 2, y + 14, { color: P.faint, size: 9.5, align: 'center' });
        if (ci != null) D.text(ctx, label(ci), x + dw / 2, y + dh / 2 + 6, { color: dead ? P.err : P.text, size: 13, align: 'center', mono: true, weight: 700 });
        if (dead) D.text(ctx, '✕ failed', x + dw / 2, y + dh - 12, { color: P.err, size: 10, align: 'center', weight: 700 });
      }
      if (s.anim) {
        const f = easeOut(s.anim.t);
        s.anim.moves.forEach(mv => {
          const [tx, ty] = posD(mv.to);
          s.anim.src.forEach(sd => { const [sx, sy] = posD(sd); D.line(ctx, sx + dw / 2, sy + dh / 2, lerp(sx + dw / 2, tx + dw / 2, f), lerp(sy + dh / 2, ty + dh / 2, f), P.alpha('accent', .55), 1.5); });
          fillRR(ctx, tx + 4, ty, dw - 8, dh, 8, P.alpha('accent', .35 * f), P.accent, 2);
        });
      }
      D.text(ctx, readable() ? (lost().length ? `degraded: ${lost().length} chunk${lost().length > 1 ? 's' : ''} lost, still readable from any ${k()} survivors — rebuild before the next failure` : `healthy: ${k() + m()} chunks on ${k() + m()} disks, any ${k()} rebuild the object`) : `lost: fewer than ${k()} chunks survive`, 16, c.h - 14, { color: readable() ? (lost().length ? P.accent : P.ok) : P.err, size: 11, weight: 650 });
    };
    L.drag(c, {
      hit: () => null,
      down: (x, y) => {
        const cols = 8, dw = (c.w - 32) / cols, dh = Math.min(70, (c.h - 70) / 2);
        const col = Math.floor((x - 16) / dw), row = Math.floor((y - 30) / (dh + 18));
        if (col < 0 || col >= cols || row < 0 || row > 1 || (y - 30) % (dh + 18) > dh) return;
        const d = row * cols + col;
        s.failed.has(d) ? s.failed.delete(d) : s.failed.add(d);
        update();
      },
    });
    reset();
  },
});
}
