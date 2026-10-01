/* ============================================================================
   API module labs, part 4 — protocol-accurate canvas visualisations for
   WebSockets (full-duplex lifecycle) and Webhooks (event delivery + retries).
   Requires viz.js and viz-sd.js (topo(), D, fmtMs, pctl, rng — all globals).
   ========================================================================= */
'use strict';

defineLab('api-ws', {
  title: 'WebSocket lifecycle: handshake, heartbeats, reconnects',
  hint: 'Connect, then fire messages from either side — a WebSocket is full-duplex, not request/response. Freeze the client to watch a dead-peer heartbeat timeout, or drop the network to watch backoff-with-jitter reconnect.',
  mount(L) {
    const r = rng(17);
    const BASE = .4, CAP = 6;
    const c = L.canvas(w => Math.min(280, Math.max(210, w * .38)));
    const T = topo(c);
    T.node('client', .15, .5, 'Browser', { kind: 'client', w: 88 });
    T.node('server', .82, .5, 'Server', { w: 96 });
    T.edge('client', 'server', { w: 2 });
    const edge = T.edges[T.edges.length - 1];

    const s = {
      phase: 'idle', sentToServer: 0, sentToClient: 0,
      t: 0, openSince: 0, timeConnected: 0, acc: 0,
      reconnectAttempts: 0, reconnectTimer: 0,
      closeCode: null, closeReason: '',
      heartbeatOn: true, hbInterval: 4, hbTimer: 4,
      pingAwaitingPong: false, pingTimeoutTimer: 0, frozen: false,
    };

    L.toggle('Heartbeat ping/pong', s.heartbeatOn, v => { s.heartbeatOn = v; s.hbTimer = s.hbInterval; });
    L.toggle('Client frozen (never pongs)', s.frozen, v => { s.frozen = v; });
    L.slider('heartbeat interval', { min: 1, max: 8, step: 1, value: s.hbInterval, fmt: v => `${v}s` }, v => { s.hbInterval = v; s.hbTimer = Math.min(s.hbTimer, v); });
    L.button('Connect', () => connect(), 'primary');
    L.button('Send message → server', () => {
      if (s.phase !== 'open') return;
      T.send(['client', 'server'], { speed: 3.4, r: 4.5, color: L.P.series[0], label: 'text frame', hop: id => T.pulse(id), end: () => { s.sentToServer++; update(); } });
    });
    L.button('Push message → client', () => {
      if (s.phase !== 'open') return;
      T.send(['server', 'client'], { speed: 3.4, r: 4.5, color: L.P.series[1], label: 'text frame', hop: id => T.pulse(id), end: () => { s.sentToClient++; update(); } });
    });
    L.button('Simulate network drop', () => dropConnection(1006, 'abnormal closure'));

    function connect() {
      if (s.phase === 'open' || s.phase === 'connecting') return;
      s.phase = 'connecting';
      update();
      T.send(['client', 'server'], { speed: 2.2, r: 5, color: L.P.accent, label: 'GET · Upgrade: websocket', end: () => {
        T.pulse('server');
        T.send(['server', 'client'], { speed: 2.6, r: 5, wait: .25, color: L.P.ok, label: '101 Switching Protocols', end: () => {
          T.pulse('client');
          s.phase = 'open'; s.openSince = s.t; s.timeConnected = 0;
          s.reconnectAttempts = 0; s.hbTimer = s.hbInterval;
          s.pingAwaitingPong = false;
          update();
        } });
      } });
    }

    function dropConnection(code, reason) {
      if (s.phase !== 'open') return;
      T.packets = [];
      s.closeCode = code; s.closeReason = reason;
      s.pingAwaitingPong = false;
      scheduleReconnect();
      update();
    }

    function scheduleReconnect() {
      s.phase = 'reconnecting';
      const backoff = Math.min(CAP, BASE * 2 ** s.reconnectAttempts);
      s.reconnectTimer = r() * backoff;
    }

    function sendPing() {
      T.send(['server', 'client'], { speed: 3.2, r: 4, color: L.P.alpha('accent', .8), label: 'ping', hop: id => T.pulse(id), end: () => {
        if (s.frozen) { s.pingAwaitingPong = true; s.pingTimeoutTimer = s.hbInterval * .6; }
        else T.send(['client', 'server'], { speed: 3.8, r: 4, wait: .1, color: L.P.ok, label: 'pong', end: () => T.pulse('server') });
      } });
    }

    const run = L.loop(dt => {
      s.t += dt;
      T.step(dt);
      if (s.phase === 'open') {
        s.timeConnected = s.t - s.openSince;
        if (s.heartbeatOn) {
          s.hbTimer -= dt;
          if (s.hbTimer <= 0) { s.hbTimer = s.hbInterval; sendPing(); }
        }
        if (s.pingAwaitingPong) {
          s.pingTimeoutTimer -= dt;
          if (s.pingTimeoutTimer <= 0) { s.pingAwaitingPong = false; dropConnection(1011, 'keepalive ping timeout'); }
        }
      } else if (s.phase === 'reconnecting') {
        s.reconnectTimer -= dt;
        if (s.reconnectTimer <= 0) {
          s.reconnectAttempts++;
          const failProb = [.5, .3, .15][s.reconnectAttempts - 1] ?? 0;
          if (r() < failProb) scheduleReconnect();
          else connect();
        }
      }
      s.acc += dt;
      if (s.acc > .2) { s.acc = 0; update(); }
      L.redraw();
    });
    run.start();
    connect();

    function insightText() {
      if (s.phase === 'connecting') return `<b>Upgrade handshake in flight.</b> A plain HTTP <code>GET</code> carries <code>Upgrade: websocket</code>; the server must answer with exactly <code>101 Switching Protocols</code> before either side may send a WebSocket frame.`;
      if (s.phase === 'open') {
        const hb = s.heartbeatOn
          ? `The server pings every ${s.hbInterval}s and expects a pong back${s.frozen ? ' — the client is frozen and will never answer, so the next missed pong closes this connection with 1011.' : '.'}`
          : 'Heartbeats are off: a peer that silently vanishes (closed laptop lid, dead Wi-Fi, a NAT that dropped its table) would be held — and its memory leaked — forever.';
        return `<b>Connection open.</b> ${hb} Frames travel independently in either direction — press either send button at any time, this is not request/response.`;
      }
      if (s.phase === 'reconnecting') {
        const backoff = Math.min(CAP, BASE * 2 ** s.reconnectAttempts);
        return `<b>Closed (${s.closeCode} ${s.closeReason}).</b> Reconnecting with exponential backoff and full jitter: the wait is randomised up to ${backoff.toFixed(1)}s so that many disconnected clients don't all retry in the same instant and stampede the server the moment it returns.`;
      }
      return `<b>Idle.</b> Press Connect to send the HTTP Upgrade request and complete the handshake.`;
    }

    function update() {
      L.stats([
        ['state', s.phase, s.phase === 'open' ? 'ok' : s.phase === 'reconnecting' ? 'err' : 'accent'],
        ['sent → server', s.sentToServer],
        ['sent → client', s.sentToClient],
        ['time connected', s.phase === 'open' ? fmtMs(s.timeConnected * 1000) : '—'],
        ['reconnect attempts', s.reconnectAttempts],
      ]);
      L.insight(insightText());
    }

    L.draw = P => {
      c.clear();
      const { ctx } = c;
      edge.color = s.phase === 'open' ? P.alpha('ok', .55) : s.phase === 'connecting' ? P.alpha('accent', .6) : P.alpha('err', .45);
      edge.dash = s.phase === 'open' ? null : [5, 4];
      edge.label = s.phase === 'open' ? 'wss:// open'
        : s.phase === 'connecting' ? 'handshake…'
        : s.phase === 'reconnecting' ? `reconnect in ${Math.max(0, s.reconnectTimer).toFixed(1)}s (attempt ${s.reconnectAttempts})`
        : 'closed';
      T.draw(ctx, P);
      if (s.phase === 'reconnecting') {
        D.text(ctx, `close ${s.closeCode} · ${s.closeReason}`, c.w / 2, c.h - 12, { color: P.err, size: 11, align: 'center', weight: 600 });
      }
    };
  },
});

defineLab('api-webhooks', {
  title: 'Webhook delivery: retries, dead-lettering, HMAC and dedupe',
  hint: 'Fire events at the provider and watch them POST to your endpoint. Pick a health scenario for the receiver and see exponential backoff, dead-lettering, and how a bad signature turns into endless useless retries.',
  mount(L) {
    const r = rng(51);
    const MAX_ATTEMPTS = 6, BASE = .5, CAP = 6, XWIN = 26;
    const c = L.canvas(w => Math.min(430, Math.max(340, w * .62)));
    const T = topo(c);
    T.node('provider', .09, .14, 'Provider', { w: 80, sub: 'e.g. Stripe' });
    T.node('queue', .38, .14, 'Delivery queue', { kind: 'queue', w: 108 });
    T.node('subscriber', .71, .14, 'Your receiver', { w: 104 });
    T.node('dlq', .38, .33, 'Dead-letter', { kind: 'queue', w: 92 });
    T.edge('provider', 'queue');
    T.edge('queue', 'subscriber');
    T.edge('queue', 'dlq', { dash: [4, 4] });

    const s = {
      scenario: 'up', tamper: false, t: 0, acc: 0, downUntil: 0,
      events: [], seq: 0,
      totalAttempts: 0, totalDelivered: 0, totalDeadLettered: 0, totalDuplicates: 0,
      ttd: [],
    };

    L.seg('subscriber health', [['up', 'Always up'], ['flaky', 'Flaky (~55% fail)'], ['down', 'Down, recovers at 6s']], s.scenario, v => { s.scenario = v; resetAll(); });
    L.toggle('Tamper payload (bad signature)', s.tamper, v => { s.tamper = v; resetAll(); });
    L.button('Fire event', () => fireEvent(), 'primary');
    L.button('Fire burst (5)', () => { for (let i = 0; i < 5; i++) fireEvent(i * .15); });
    L.button('Reset', () => resetAll());

    function resetAll() {
      s.events = []; s.t = 0; s.seq = 0;
      s.totalAttempts = 0; s.totalDelivered = 0; s.totalDeadLettered = 0; s.totalDuplicates = 0; s.ttd = [];
      s.downUntil = s.scenario === 'down' ? 6 : 0;
      T.packets = [];
      T.nodes.subscriber.sub = ''; T.nodes.subscriber.badge = null;
      T.nodes.dlq.badge = null;
      update();
    }

    function fireEvent(delay = 0) {
      s.seq++;
      s.events.push({ id: `evt_${s.seq}`, t0: s.t + delay, attempts: [], attemptNum: 0, delivered: false, deadLettered: false, dupScheduled: false, pendingDup: false, nextAt: s.t + delay });
    }

    function fireAttempt(ev) {
      ev.attemptNum++;
      const departT = s.t;
      T.send(['provider', 'queue', 'subscriber'], { speed: 3, r: 4.5, color: L.P.accent, label: ev.id, hop: id => T.pulse(id), end: () => resolveAttempt(ev, departT) });
    }

    function fireDuplicate(ev) {
      T.send(['provider', 'queue', 'subscriber'], { speed: 3, r: 4, color: L.P.alpha('faint', .9), label: `${ev.id} (dup)`, hop: id => T.pulse(id), end: () => {
        s.totalDuplicates++;
        ev.attempts.push({ t: s.t, ok: true, dup: true });
        T.nodes.subscriber.sub = 'duplicate id ignored (deduped)';
        T.nodes.subscriber.badge = 'seen before'; T.nodes.subscriber.badgeColor = L.P.faint;
        update();
      } });
    }

    function resolveAttempt(ev, t) {
      let ok, label;
      if (s.tamper) { ok = false; label = '401 signature mismatch'; }
      else if (s.scenario === 'down' && s.t < s.downUntil) { ok = false; label = '503 unavailable'; }
      else if (s.scenario === 'flaky' && r() < .55) { ok = false; label = r() < .5 ? '500 error' : 'timeout'; }
      else { ok = true; label = '200 OK'; }
      ev.attempts.push({ t, ok, label });
      s.totalAttempts++;
      T.nodes.subscriber.sub = s.tamper ? 'HMAC mismatch → reject' : (ok ? 'HMAC verified ✓' : 'HMAC verified, handler failed');
      T.nodes.subscriber.badge = label; T.nodes.subscriber.badgeColor = ok ? L.P.ok : L.P.err;
      T.send(['subscriber', 'queue', 'provider'], { speed: 4, r: 3.5, color: ok ? L.P.ok : L.P.err, label });
      if (ok) {
        ev.delivered = true; ev.deliveredAt = t; s.totalDelivered++; s.ttd.push(t - ev.t0);
        if (!ev.dupScheduled && r() < .18) { ev.dupScheduled = true; ev.pendingDup = true; ev.nextAt = t + .5 + r() * .6; }
      } else if (ev.attemptNum >= MAX_ATTEMPTS) {
        ev.deadLettered = true; s.totalDeadLettered++;
        T.send(['queue', 'dlq'], { speed: 3.5, r: 4, color: L.P.err, end: () => T.pulse('dlq') });
      } else {
        const backoff = Math.min(CAP, BASE * 2 ** (ev.attemptNum - 1));
        ev.nextAt = t + r() * backoff;
      }
      update();
    }

    const run = L.loop(dt => {
      s.t += dt;
      T.step(dt);
      s.events.forEach(ev => {
        if (ev.deadLettered) return;
        if (ev.delivered && !ev.pendingDup) return;
        if (ev.nextAt != null && s.t >= ev.nextAt) {
          ev.nextAt = null;
          if (ev.pendingDup) { ev.pendingDup = false; fireDuplicate(ev); }
          else fireAttempt(ev);
        }
      });
      if (s.events.length > 80) s.events.splice(0, s.events.length - 60);
      s.acc += dt;
      if (s.acc > .2) { s.acc = 0; update(); }
      L.redraw();
    });
    run.start();
    resetAll();

    function insightText() {
      if (s.tamper) return `<b>Every attempt is rejected with a 401.</b> The provider only stops retrying once it sees a 2xx, so a wrong or stale secret doesn't just block one event — it queues, backs off for longer each time, and eventually dead-letters every event until the signature is fixed. Verification must run on the raw bytes, before any business logic.`;
      if (s.scenario === 'down') return `<b>The receiver is down until t = ${s.downUntil}s.</b> Attempts made during the outage get a 503 and back off exponentially, with full jitter so retries don't all land in the same instant; once it recovers, the next scheduled attempt for each event succeeds — nothing is lost, it just arrives late.`;
      if (s.scenario === 'flaky') return `<b>~55% of attempts fail at random.</b> Backoff keeps growing after each failure (capped at ${CAP}s), so a flaky endpoint gets hit less and less often instead of hammered. After ${MAX_ATTEMPTS} failed attempts an event is dead-lettered for manual replay.`;
      return `<b>Healthy endpoint: the first attempt usually succeeds.</b> At-least-once delivery still means duplicates can happen — the provider retries whenever it never sees your 2xx, even if you actually processed the event — so a receiver must dedupe by event <code>id</code>, not assume each id arrives exactly once.`;
    }

    function update() {
      L.stats([
        ['attempts', s.totalAttempts, 'accent'],
        ['delivered', s.totalDelivered, 'ok'],
        ['dead-lettered', s.totalDeadLettered, s.totalDeadLettered ? 'err' : ''],
        ['median time-to-delivery', s.ttd.length ? fmtMs(pctl(s.ttd, .5) * 1000) : '—'],
        ['duplicates deduped', s.totalDuplicates],
      ]);
      L.insight(insightText());
    }

    L.draw = P => {
      c.clear();
      const { ctx } = c;
      T.draw(ctx, P);
      const topoH = Math.round(c.h * .4);
      ctx.save();
      ctx.translate(0, topoH);
      const chartH = c.h - topoH;
      const x1 = Math.max(XWIN, s.t + 1), x0 = Math.max(0, x1 - XWIN);
      const v = D.view({ w: c.w, h: chartH }, { x0, x1, y0: 0, y1: MAX_ATTEMPTS + .8, pad: 10, padL: 30, padB: 24 });
      if (s.scenario === 'down' && s.downUntil > x0) {
        const shadeEnd = Math.min(s.downUntil, x1);
        ctx.fillStyle = P.alpha('err', .07);
        ctx.fillRect(v.sx(x0), v.sy(v.y1), v.sx(shadeEnd) - v.sx(x0), v.sy(v.y0) - v.sy(v.y1));
        D.text(ctx, 'receiver down', v.sx((x0 + shadeEnd) / 2), v.sy(v.y1) + 10, { color: P.err, size: 10, align: 'center', weight: 600 });
      }
      const xTicks = [];
      for (let t = Math.ceil(x0 / 5) * 5; t <= x1; t += 5) xTicks.push(t);
      D.axes(ctx, v, P, { xTicks, yTicks: [1, 2, 3, 4, 5, 6], xLabel: 'seconds', yLabel: 'attempt #' });
      s.events.forEach((ev, idx) => {
        const color = P.series[idx % P.series.length];
        let prev = null;
        ev.attempts.forEach((a, i) => {
          if (a.t < x0 - 1) { prev = null; return; }
          const x = v.sx(a.t), y = v.sy(i + 1);
          if (prev) D.line(ctx, prev.x, prev.y, x, y, P.alpha(color, .35), 1.3, [3, 3]);
          if (a.dup) D.dot(ctx, x, y, 4, P.surface, P.faint, 1.4);
          else D.dot(ctx, x, y, 5, a.ok ? P.ok : P.err, color, 1.3);
          prev = { x, y };
        });
        if (ev.deadLettered && ev.attempts.length) {
          const last = ev.attempts[ev.attempts.length - 1];
          if (last.t >= x0) D.text(ctx, '✕ DLQ', v.sx(last.t) + 8, v.sy(ev.attempts.length), { color: P.err, size: 9.5, align: 'left', weight: 600 });
        }
      });
      ctx.restore();
    };
  },
});
