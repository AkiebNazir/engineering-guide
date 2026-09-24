/* ============================================================================
   System design request flows — an animated, narrated walk through a real
   request: the packet leaves the client, crosses each component in order,
   and every hop says what happens there and what it costs.

   A flow is described as data:
     nodes      id → { x, y, label, sub, kind: 'client'|'svc'|'db'|'cache'|'queue' }
     edges      [a, b, { async }]            drawn once, lit while in use
     scenarios  [{ id, name, summary, down: [nodeIds], steps: [...] }]
   A step is either a hop  { path: [a, b, (c…)], label, title, detail, ms }
             or local work { at: node, badge, title, detail, ms }
   plus optional { tone: 'ok'|'warn'|'err', async: true }.

   defineFlow(name, spec) registers it as a lab (viz.js), so sd.js places it
   next to the heading it explains. Everything is SVG coloured with CSS
   variables, so both themes and the reader's page themes work for free.
   ========================================================================= */
'use strict';

const FLOW_W = 900, FLOW_H = 560;
const flowEsc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

function defineFlow(name, spec) {
  defineLab(name, { title: spec.title, hint: spec.hint, mount: L => mountFlow(L, spec) });
}

function mountFlow(L, spec) {
  L.fig.classList.add('lab-flow');
  const nodes = spec.nodes;
  const st = { sc: 0, i: -1, t: 0, playing: false, speed: 1, hold: 0, raf: 0, last: 0, seen: false };
  const pairKey = (a, b) => [a, b].sort().join('|');

  L.stage.innerHTML = `
    <div class="flow">
      <div class="flow-top">
        <div class="seg flow-tabs" role="tablist">${spec.scenarios.map((s, k) =>
          `<button type="button" role="tab" data-sc="${k}">${flowEsc(s.name)}</button>`).join('')}</div>
      </div>
      <p class="flow-summary"></p>
      <div class="flow-canvas">
        <svg viewBox="0 0 ${FLOW_W} ${FLOW_H}" role="img" aria-label="${flowEsc(spec.title)}">
          <defs>
            <pattern id="flowGrid-${name}" width="25" height="25" patternUnits="userSpaceOnUse"><path d="M25 0H0V25" class="fl-grid"/></pattern>
            
          </defs>
          <rect width="${FLOW_W}" height="${FLOW_H}" rx="18" fill="url(#flowGrid-${name})"/>
          ${(spec.zones || []).map(z => `<g class="fl-zone"><rect x="${z.x}" y="${z.y}" width="${z.w}" height="${z.h}" rx="16"/><text x="${z.x + 14}" y="${z.y + 24}">${flowEsc(z.label)}</text></g>`).join('')}
          <g class="fl-edges"></g>
          <g class="fl-nodes"></g>
          <g class="fl-packets"></g>
        </svg>
        <div class="flow-hint" hidden>Press play to follow the request</div>
      </div>
      <div class="flow-bar">
        <button type="button" class="flow-btn" data-f="restart" title="Start again" aria-label="Start again">⏮</button>
        <button type="button" class="flow-btn" data-f="prev" title="Previous step (←)" aria-label="Previous step">◀</button>
        <button type="button" class="flow-btn primary" data-f="play"></button>
        <button type="button" class="flow-btn" data-f="next" title="Next step (→)" aria-label="Next step">▶</button>
        <div class="flow-track" aria-hidden="true"></div>
        <div class="seg flow-speed">${[.5, 1, 2].map(v => `<button type="button" data-speed="${v}">${v}×</button>`).join('')}</div>
      </div>
      <div class="flow-bottom">
        <div class="flow-now" aria-live="polite"></div>
        <ol class="flow-steps"></ol>
      </div>
    </div>`;

  const root = L.stage.querySelector('.flow');
  const $f = s => root.querySelector(s), $$f = s => [...root.querySelectorAll(s)];
  const svg = $f('svg');

  /* ------------------------------------------------------------ geometry -- */
  const box = id => { const n = nodes[id]; return { x: n.x, y: n.y, w: n.w || 150, h: n.h || 66 }; };
  function border(id, tx, ty) {                     // point on node's outline toward (tx, ty)
    const b = box(id), dx = tx - b.x, dy = ty - b.y;
    if (!dx && !dy) return [b.x, b.y];
    const s = Math.min((b.w / 2 + 6) / Math.abs(dx || 1e-9), (b.h / 2 + 6) / Math.abs(dy || 1e-9));
    return [b.x + dx * s, b.y + dy * s];
  }
  const seg = (a, b) => {
    const [x1, y1] = border(a, nodes[b].x, nodes[b].y), [x2, y2] = border(b, nodes[a].x, nodes[a].y);
    return { x1, y1, x2, y2 };
  };

  /* ------------------------------------------------------------- drawing -- */
  $f('.fl-edges').innerHTML = spec.edges.map(([a, b, o = {}]) => {
    const g = seg(a, b);
    return `<line class="fl-edge${o.async ? ' is-async' : ''}" data-e="${pairKey(a, b)}" x1="${g.x1}" y1="${g.y1}" x2="${g.x2}" y2="${g.y2}"/>
      <line class="fl-edge-flow" data-e="${pairKey(a, b)}" x1="${g.x1}" y1="${g.y1}" x2="${g.x2}" y2="${g.y2}"/>`;
  }).join('');

  const shape = (n, b) => {
    const x = b.x - b.w / 2, y = b.y - b.h / 2;
    if (n.kind === 'db') {
      const ry = 11;
      return `<path class="fl-shape" d="M${x} ${y + ry}v${b.h - 2 * ry}a${b.w / 2} ${ry} 0 0 0 ${b.w} 0v${-(b.h - 2 * ry)}a${b.w / 2} ${ry} 0 0 0 ${-b.w} 0z"/>
        <ellipse class="fl-shape-line" cx="${b.x}" cy="${y + ry}" rx="${b.w / 2}" ry="${ry}"/>`;
    }
    if (n.kind === 'client') return `<rect class="fl-shape" x="${x}" y="${y}" width="${b.w}" height="${b.h}" rx="${b.h / 2}"/>`;
    if (n.kind === 'queue') {
      return `<rect class="fl-shape" x="${x}" y="${y}" width="${b.w}" height="${b.h}" rx="10"/>
        ${[0, 1, 2, 3].map(k => `<rect class="fl-slot" x="${x + b.w - 40 + k * 8}" y="${y + 14}" width="5" height="${b.h - 28}" rx="2"/>`).join('')}`;
    }
    if (n.kind === 'cache') {
      return `<rect class="fl-shape" x="${x}" y="${y}" width="${b.w}" height="${b.h}" rx="10"/>
        <path class="fl-bolt" d="M${x + b.w - 24} ${y + b.h / 2 - 15}l-8 16h8l-4 14 12-19h-8l4-11z"/>`;
    }
    return `<rect class="fl-shape" x="${x}" y="${y}" width="${b.w}" height="${b.h}" rx="12"/>`;
  };
  $f('.fl-nodes').innerHTML = Object.entries(nodes).map(([id, n]) => {
    const b = box(id);
    const tx = n.kind === 'queue' || n.kind === 'cache' ? b.x - 14 : b.x;
    return `<g class="fl-node kind-${n.kind || 'svc'}" data-n="${id}">
      <rect class="fl-halo" x="${b.x - b.w / 2 - 8}" y="${b.y - b.h / 2 - 8}" width="${b.w + 16}" height="${b.h + 16}" rx="20"/>
      ${shape(n, b)}
      <text class="fl-label" x="${tx}" y="${b.y + (n.sub ? -1 : 7)}" text-anchor="middle">${flowEsc(n.label)}</text>
      ${n.sub ? `<text class="fl-sub" x="${tx}" y="${b.y + 19}" text-anchor="middle">${flowEsc(n.sub)}</text>` : ''}
      <g class="fl-badge" transform="translate(${b.x} ${b.y - b.h / 2 - 20})"><rect rx="13" height="26" y="-2"/><text text-anchor="middle" y="16"></text></g>
      <text class="fl-down" x="${b.x}" y="${b.y + b.h / 2 + 22}" text-anchor="middle">unavailable</text>
    </g>`;
  }).join('');

  const packet = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  packet.setAttribute('class', 'fl-packet');
  packet.innerHTML = '<circle class="fl-pk-halo" r="18"/><circle class="fl-pk-dot" r="9"/><g class="fl-pk-tag"><rect rx="13" height="26"/><text text-anchor="middle" y="18"></text></g>';
  $f('.fl-packets').append(packet);

  /* ------------------------------------------------------------- scenario -- */
  const scenario = () => spec.scenarios[st.sc];
  const steps = () => scenario().steps;
  const stepDur = s => (s.path ? (s.path.length - 1) * 1.05 : 1.15) * (s.async ? 1.15 : 1);
  const syncTotal = sc => sc.steps.filter(s => !s.async).reduce((a, s) => a + (s.ms || 0), 0);
  const fmt = ms => ms >= 100 ? `${Math.round(ms)} ms` : ms >= 1 ? `${+ms.toFixed(1)} ms` : ms > 0 ? '<1 ms' : '';

  function loadScenario(k) {
    stop();
    st.sc = k; st.i = -1; st.t = 0;
    const sc = scenario();
    $$f('[data-sc]').forEach(b => b.classList.toggle('is-on', +b.dataset.sc === k));
    $f('.flow-summary').innerHTML = sc.summary;
    $f('.flow-steps').innerHTML = sc.steps.map((s, i) => `
      <li data-step="${i}" class="${s.async ? 'is-async' : ''} tone-${s.tone || 'none'}">
        <button type="button"><span class="fs-n">${i + 1}</span><span class="fs-t">${flowEsc(s.title)}</span>
        <span class="fs-ms">${s.async ? 'async' : fmt(s.ms || 0)}</span></button></li>`).join('');
    $f('.flow-track').innerHTML = sc.steps.map((s, i) => `<i data-step="${i}" class="${s.async ? 'is-async' : ''}"></i>`).join('');
    paint();
  }

  /* ----------------------------------------------------------- rendering -- */
  function paint() {
    const sc = scenario(), list = sc.steps, s = list[st.i];
    const down = new Set(sc.down || []);
    const involved = new Set(s ? (s.path || [s.at]) : []);
    const activeEdges = new Set();
    if (s && s.path) for (let k = 0; k < s.path.length - 1; k++) activeEdges.add(pairKey(s.path[k], s.path[k + 1]));

    $$f('.fl-node').forEach(g => {
      const id = g.dataset.n;
      g.classList.toggle('is-on', involved.has(id));
      g.classList.toggle('is-down', down.has(id));
      g.classList.toggle('is-used', list.slice(0, st.i + 1).some(x => (x.path || [x.at]).includes(id)));
      const badge = s && (s.at === id ? s.badge : s.badgeAt === id ? s.badge : null);
      const bg = g.querySelector('.fl-badge');
      bg.classList.toggle('is-shown', !!badge && st.t > (s.at ? .05 : .85));
      bg.classList.remove('tone-ok', 'tone-warn', 'tone-err');
      if (badge) {
        const tx = bg.querySelector('text'), rect = bg.querySelector('rect');
        tx.textContent = badge;
        const w = Math.max(64, badge.length * 8.7 + 26);
        rect.setAttribute('width', w); rect.setAttribute('x', -w / 2);
        if (s.tone) bg.classList.add(`tone-${s.tone}`);
      }
    });
    $$f('.fl-edge, .fl-edge-flow').forEach(e => {
      e.classList.toggle('is-on', activeEdges.has(e.dataset.e));
      e.classList.toggle('is-async-on', activeEdges.has(e.dataset.e) && !!(s && s.async));
    });

    // packet
    packet.classList.toggle('is-shown', !!(s && s.path));
    packet.classList.remove('tone-ok', 'tone-warn', 'tone-err', 'tone-async');
    if (s && s.path) {
      if (s.tone) packet.classList.add(`tone-${s.tone}`);
      else if (s.async) packet.classList.add('tone-async');
      const hops = s.path.length - 1, pos = Math.min(hops - 1e-6, st.t * hops), k = Math.floor(pos);
      const f = pos - k, e = f < .5 ? 2 * f * f : 1 - Math.pow(-2 * f + 2, 2) / 2;
      const g = seg(s.path[k], s.path[k + 1]);
      const x = g.x1 + (g.x2 - g.x1) * e, y = g.y1 + (g.y2 - g.y1) * e;
      packet.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)})`);
      const tag = packet.querySelector('.fl-pk-tag'), tx = tag.querySelector('text'), rect = tag.querySelector('rect');
      if (tx.textContent !== s.label) {
        tx.textContent = s.label || '';
        const w = Math.max(44, (s.label || '').length * 8.7 + 24);
        rect.setAttribute('width', w); rect.setAttribute('x', -w / 2);
      }
      tag.setAttribute('transform', `translate(0 ${y < 100 ? 22 : -46})`);
      tag.style.opacity = f > .8 && k === hops - 1 ? 0 : 1;          // don't cover the node it lands on
    }

    // steps list + track
    $$f('.flow-steps li').forEach(li => {
      const i = +li.dataset.step;
      li.classList.toggle('is-done', i < st.i || (i === st.i && st.t >= 1));
      li.classList.toggle('is-now', i === st.i);
    });
    $$f('.flow-track i').forEach(el => {
      const i = +el.dataset.step;
      el.style.setProperty('--p', i < st.i ? 1 : i === st.i ? Math.min(1, st.t) : 0);
    });

    // narration
    const done = list.slice(0, st.i + (st.t >= 1 ? 1 : 0)).filter(x => !x.async).reduce((a, x) => a + (x.ms || 0), 0);
    const total = syncTotal(sc);
    $f('.flow-now').innerHTML = s ? `
        <div class="fn-head"><span class="fn-step">Step ${st.i + 1} of ${list.length}</span>
          ${s.async ? '<span class="fn-chip async">async · after the response</span>' : s.ms ? `<span class="fn-chip">+${fmt(s.ms)}</span>` : ''}
          ${s.tone ? `<span class="fn-chip tone-${s.tone}">${{ ok: 'success', warn: 'miss', err: 'failure' }[s.tone]}</span>` : ''}</div>
        <div class="fn-title">${flowEsc(s.title)}</div>
        ${s.detail ? `<p class="fn-detail">${s.detail}</p>` : ''}
        <div class="fn-lat"><span>User-visible latency so far</span><b>${fmt(done) || '0 ms'}</b><em>of ${fmt(total)}</em>
          <i style="--p:${total ? Math.min(1, done / total) : 0}"></i></div>`
      : `<div class="fn-head"><span class="fn-step">${list.length} steps</span><span class="fn-chip">${fmt(total)} user-visible</span></div>
        <div class="fn-title">${flowEsc(scenario().name)}</div>
        <p class="fn-detail">Press <b>Play</b> to watch the request move through the system, or step through it with ◀ ▶. Click any step in the list to jump to it.</p>`;

    const playBtn = $f('[data-f="play"]');
    const atEnd = st.i >= list.length - 1 && st.t >= 1;
    playBtn.textContent = st.playing ? '❚❚ Pause' : atEnd ? '↻ Replay' : st.i < 0 ? '▶ Play' : '▶ Resume';
    $f('.flow-hint').hidden = st.i >= 0;
  }

  /* ------------------------------------------------------------ playback -- */
  function tick(now) {
    if (!st.playing || !root.isConnected) { st.playing = false; return; }
    const dt = Math.min(.05, (now - (st.last || now)) / 1000) * st.speed;
    st.last = now;
    const list = steps();
    if (st.i < 0) { st.i = 0; st.t = 0; }
    const s = list[st.i];
    if (st.t < 1) {
      st.t = Math.min(1, st.t + dt / stepDur(s));
      if (st.t >= 1) st.hold = s.at ? .9 : .55;
    } else if ((st.hold -= dt) <= 0) {
      if (st.i >= list.length - 1) { st.playing = false; paint(); return; }
      st.i++; st.t = 0;
    }
    paint();
    st.raf = requestAnimationFrame(tick);
  }
  function play() {
    const list = steps();
    if (st.i >= list.length - 1 && st.t >= 1) { st.i = -1; st.t = 0; }
    st.playing = true; st.last = 0;
    cancelAnimationFrame(st.raf);
    st.raf = requestAnimationFrame(tick);
    paint();
  }
  function stop() { st.playing = false; cancelAnimationFrame(st.raf); }
  function jump(i) {
    stop();
    st.i = Math.max(-1, Math.min(steps().length - 1, i));
    st.t = st.i < 0 ? 0 : 1;
    paint();
  }
  function stepAnimated(i) {                          // animate just one step, then pause
    stop();
    const list = steps();
    if (i < 0 || i >= list.length) return;
    st.i = i; st.t = 0; st.last = 0; st.playing = true;
    const once = now => {
      if (!st.playing || !root.isConnected) return;
      const dt = Math.min(.05, (now - (st.last || now)) / 1000) * st.speed;
      st.last = now;
      st.t = Math.min(1, st.t + dt / stepDur(list[st.i]));
      paint();
      if (st.t < 1) st.raf = requestAnimationFrame(once);
      else { st.playing = false; paint(); }
    };
    st.raf = requestAnimationFrame(once);
  }

  root.addEventListener('click', e => {
    const b = e.target.closest('button');
    if (!b) return;
    if (b.dataset.sc) { loadScenario(+b.dataset.sc); play(); return; }
    if (b.dataset.speed) { st.speed = +b.dataset.speed; $$f('[data-speed]').forEach(x => x.classList.toggle('is-on', x === b)); return; }
    const li = b.closest('[data-step]');
    if (li) { stepAnimated(+li.dataset.step); return; }
    const f = b.dataset.f;
    if (f === 'play') st.playing ? (stop(), paint()) : play();
    else if (f === 'restart') { jump(-1); play(); }
    else if (f === 'prev') jump(st.i - 1);
    else if (f === 'next') stepAnimated(st.t < 1 && st.i >= 0 ? st.i : st.i + 1);
  });
  root.tabIndex = -1;
  root.addEventListener('keydown', e => {
    if (e.key === 'ArrowRight') { e.preventDefault(); e.stopPropagation(); stepAnimated(st.i + 1); }
    else if (e.key === 'ArrowLeft') { e.preventDefault(); e.stopPropagation(); jump(st.i - 1); }
    else if (e.key === ' ') { e.preventDefault(); e.stopPropagation(); st.playing ? (stop(), paint()) : play(); }
  });
  $$f('[data-speed]').forEach(x => x.classList.toggle('is-on', +x.dataset.speed === st.speed));

  loadScenario(0);
  // Start playing the first time the diagram scrolls into view.
  const reduce = typeof reducedMotion === 'function' && reducedMotion();
  if (!reduce && 'IntersectionObserver' in window) {
    const io = new IntersectionObserver(entries => {
      if (entries.some(en => en.isIntersecting) && !st.seen) { st.seen = true; play(); io.disconnect(); }
    }, { threshold: .45 });
    io.observe(svg);
  }
}

/* ---------------------------------------------------------- lane layout --
   Most diagrams are a pipeline: clients on the left, state and external
   systems on the right. lane() places nodes into evenly spaced, labelled
   columns (zones) so nothing overlaps and nothing floats in dead space,
   the way the URL-shortener diagram was hand-tuned — but computed. -- */
function lane(cols, opts = {}) {
  const n = cols.length;
  const padX = opts.padX ?? 14, gapX = opts.gapX ?? 22, padY = opts.padY ?? 58;
  const colW = (FLOW_W - padX * 2 - gapX * (n - 1)) / n;
  const nodes = {}, zones = [];
  cols.forEach((col, i) => {
    const zx = padX + i * (colW + gapX);
    zones.push({ x: zx, y: 12, w: colW, h: FLOW_H - 24, label: col.label });
    const cx = zx + colW / 2;
    const bandH = (FLOW_H - padY * 2) / col.nodes.length;
    col.nodes.forEach((nd, j) => {
      nodes[nd.id] = {
        x: Math.round(cx), y: Math.round(padY + bandH * j + bandH / 2),
        label: nd.label, sub: nd.sub, kind: nd.kind, w: nd.w, h: nd.h,
      };
    });
  });
  return { nodes, zones };
}

/* ============================================================= URL shortener == */
defineFlow('sd-flow-shortener', {
  title: 'Live request flow: create a link, then follow a click',
  hint: 'Pick a scenario. Each hop lights up, the packet shows what is sent, and the panel explains the decision made at that component and what it costs in latency.',
  zones: [
    { x: 12, y: 12, w: 126, h: 536, label: 'CLIENTS' },
    { x: 150, y: 12, w: 330, h: 536, label: 'SERVING PATH' },
    { x: 494, y: 12, w: 188, h: 536, label: 'STATE' },
    { x: 694, y: 12, w: 194, h: 536, label: 'ASYNC · DERIVED' },
  ],
  nodes: {
    creator:   { x: 75,  y: 135, label: 'Creator', sub: 'signed in', kind: 'client', w: 112, h: 64 },
    visitor:   { x: 75,  y: 385, label: 'Visitor', sub: 'opens link', kind: 'client', w: 112, h: 64 },
    edge:      { x: 232, y: 385, label: 'Edge', sub: 'CDN · WAF', w: 124 },
    api:       { x: 398, y: 135, label: 'Link API', sub: 'create · disable', w: 146 },
    redirect:  { x: 398, y: 385, label: 'Redirect', sub: 'stateless svc', w: 146 },
    db:        { x: 588, y: 240, label: 'Link DB', sub: 'source of truth', kind: 'db', w: 168, h: 92 },
    cache:     { x: 588, y: 478, label: 'Redis', sub: 'link:{code}', kind: 'cache', w: 168, h: 70 },
    relay:     { x: 791, y: 135, label: 'Outbox relay', sub: 'polls commits', w: 176 },
    stream:    { x: 791, y: 310, label: 'Event stream', sub: 'Kafka', kind: 'queue', w: 176 },
    analytics: { x: 791, y: 478, label: 'Analytics', sub: '≤ 5 min fresh', kind: 'db', w: 176, h: 84 },
  },
  edges: [
    ['creator', 'api'], ['visitor', 'edge'], ['edge', 'redirect'],
    ['api', 'db'], ['redirect', 'cache'], ['redirect', 'db'],
    ['db', 'relay', { async: true }], ['relay', 'stream', { async: true }],
    ['redirect', 'stream', { async: true }], ['stream', 'analytics', { async: true }],
  ],
  scenarios: [
    {
      id: 'create', name: 'Create a link',
      summary: 'The <b>write path</b>: about 190 creates/s at peak. Correctness matters more than speed here — no duplicate links, no lost events.',
      steps: [
        { path: ['creator', 'api'], label: 'POST /v1/links', ms: 30, title: 'Creator sends the long URL',
          detail: 'Body: <code>destination_url</code> and an optional <code>custom_alias</code>. Header <code>Idempotency-Key: 58f0…</code> means a retry after a timeout can never create a second link.' },
        { at: 'api', badge: 'auth ✓  URL policy ✓', ms: 2, title: 'Authenticate and validate before storage',
          detail: 'Check the bearer token, URL scheme and length, reserved words for aliases, and abuse rules. Cheap rejections happen before any database work.' },
        { path: ['api', 'db', 'api'], label: 'idempotency key?', ms: 3, title: 'Has this exact request been seen?',
          detail: 'Look up <code>(owner_id, key)</code> in <code>IdempotencyKey</code>. Not found, so this is a first attempt and it goes ahead.' },
        { at: 'api', badge: 'code = aZ8k2P', ms: .1, title: 'Generate a 7-character base62 code',
          detail: '62⁷ ≈ 3.5 trillion possible codes. Random codes cannot be guessed in sequence. A collision is rejected by the primary key and simply retried with a new code.' },
        { path: ['api', 'db', 'api'], label: 'BEGIN … COMMIT', badgeAt: 'db', badge: '3 rows committed', tone: 'ok', ms: 6,
          title: 'One transaction writes three rows',
          detail: '<code>Link</code> (aZ8k2P → destination), <code>IdempotencyKey</code> (the saved response) and <code>OutboxEvent</code> (LinkCreated). They commit together or not at all.' },
        { path: ['api', 'creator'], label: '201 Created', tone: 'ok', ms: 30, title: 'Creator gets the short link',
          detail: '<code>https://sho.rt/aZ8k2P</code>. The user-visible part of the create flow ends here.' },
        { path: ['db', 'relay'], label: 'poll outbox', async: true, title: 'Outbox relay picks up the event',
          detail: 'A separate process reads committed outbox rows. If the API crashed straight after COMMIT, the event is still in the table, so nothing downstream is ever missed.' },
        { path: ['relay', 'stream'], label: 'LinkCreated', async: true, title: 'Event published for everyone else',
          detail: 'Audit, cache warming and analytics consume it. They are eventually consistent, and the redirect path never waits for them.' },
      ],
    },
    {
      id: 'retry', name: 'Retry after a timeout',
      summary: 'The response to the first create was lost on the network. The client retries with the <b>same idempotency key</b>.',
      steps: [
        { path: ['creator', 'api'], label: 'POST (same key)', ms: 30, title: 'The client retries',
          detail: 'Same body and the same <code>Idempotency-Key: 58f0…</code>. Without idempotency, this is how users end up with two links, or are charged twice in a payments system.' },
        { path: ['api', 'db', 'api'], label: 'idempotency key?', badgeAt: 'db', badge: 'key found', tone: 'warn', ms: 3, title: 'The key already exists',
          detail: 'Same key and the same request hash: this request already succeeded. If the body were different, the API would reject it with <code>422</code>.' },
        { at: 'api', badge: 'replay saved response', ms: .2, title: 'No second insert',
          detail: 'The API returns the response stored with the key. No new code, no new row, no new event.' },
        { path: ['api', 'creator'], label: '201 (aZ8k2P)', tone: 'ok', ms: 30, title: 'Same link as before',
          detail: 'Exactly one link exists, however many times the client retries.' },
      ],
    },
    {
      id: 'hit', name: 'Redirect · cache hit',
      summary: 'The <b>hot path</b>: about 19,000 redirects/s at peak, p99 under 100 ms. Most requests end at the cache.',
      steps: [
        { path: ['visitor', 'edge'], label: 'GET /aZ8k2P', ms: 15, title: 'A visitor opens the short link',
          detail: 'DNS resolves <code>sho.rt</code> to the nearest edge, and TLS terminates close to the user.' },
        { at: 'edge', badge: 'WAF ✓  rate limit ✓', ms: 1, title: 'The edge filters abuse',
          detail: 'Bad bots and code-guessing bursts are stopped here, before they cost any origin capacity.' },
        { path: ['edge', 'redirect'], label: 'GET /aZ8k2P', ms: 8, title: 'Forwarded to any redirect instance',
          detail: 'The service keeps no state, so the load balancer can pick any healthy instance and scaling out is just adding instances.' },
        { path: ['redirect', 'cache', 'redirect'], label: 'GET link:aZ8k2P', badgeAt: 'cache', badge: 'HIT', tone: 'ok', ms: 1, title: 'Cache hit',
          detail: 'Redis returns the destination and <code>status = ACTIVE</code> in about a millisecond. The database is not touched.' },
        { path: ['redirect', 'edge', 'visitor'], label: '302 Location', tone: 'ok', ms: 23, title: 'Redirect sent',
          detail: '<b>302, not 301.</b> Browsers cache a 301 permanently, so a link that is later disabled or edited would keep redirecting to the old destination.' },
        { path: ['redirect', 'stream'], label: 'click event', async: true, title: 'Click recorded without waiting',
          detail: 'The event goes into a bounded, non-blocking buffer. The visitor already has their redirect.' },
        { path: ['stream', 'analytics'], label: 'aggregate', async: true, title: 'Analytics catch up',
          detail: 'Consumers aggregate clicks, and dashboards are fresh within five minutes, as the requirements promise.' },
      ],
    },
    {
      id: 'miss', name: 'Redirect · cache miss',
      summary: 'A new or unpopular link that is not in Redis yet: <b>cache-aside</b>. Read the source of truth once, then remember the answer.',
      steps: [
        { path: ['visitor', 'edge'], label: 'GET /aZ8k2P', ms: 15, title: 'A visitor opens the short link',
          detail: 'Same entry as a cache hit: nearest edge, TLS, abuse filtering.' },
        { path: ['edge', 'redirect'], label: 'GET /aZ8k2P', ms: 9, title: 'Forwarded to a redirect instance',
          detail: 'Any instance will do.' },
        { path: ['redirect', 'cache', 'redirect'], label: 'GET link:aZ8k2P', badgeAt: 'cache', badge: 'MISS', tone: 'warn', ms: 1, title: 'Cache miss',
          detail: 'The key is absent: the link is new, was evicted, or its TTL expired.' },
        { path: ['redirect', 'db', 'redirect'], label: 'SELECT by code', ms: 4, title: 'Read the source of truth',
          detail: 'A primary-key lookup on <code>code</code>: one index seek, a few milliseconds. Concurrent misses for the same code are coalesced, so only one of them reaches the database.' },
        { path: ['redirect', 'cache', 'redirect'], label: 'SET · TTL 1h ± jitter', badgeAt: 'cache', badge: 'cached', tone: 'ok', ms: 1, title: 'Populate the cache',
          detail: 'The TTL is jittered so thousands of keys do not expire in the same second. Disabling a link deletes this key immediately; the TTL is only a safety net.' },
        { path: ['redirect', 'edge', 'visitor'], label: '302 Location', tone: 'ok', ms: 23, title: 'Redirect sent',
          detail: 'About 5 ms slower than a hit. The next visitor to this code gets the cached path.' },
        { path: ['redirect', 'stream'], label: 'click event', async: true, title: 'Click recorded without waiting',
          detail: 'Same asynchronous path as every redirect.' },
      ],
    },
    {
      id: 'unknown', name: 'Unknown code',
      summary: 'Someone requests a code that does not exist — a typo, or a bot <b>guessing codes</b>.',
      steps: [
        { path: ['visitor', 'edge', 'redirect'], label: 'GET /zzzzzz', ms: 24, title: 'Request for a code that was never created',
          detail: 'The edge counts 404s per client, so an enumeration burst gets rate-limited quickly.' },
        { path: ['redirect', 'cache', 'redirect'], label: 'GET link:zzzzzz', badgeAt: 'cache', badge: 'MISS', tone: 'warn', ms: 1, title: 'Not in the cache',
          detail: 'Nothing cached for this code yet.' },
        { path: ['redirect', 'db', 'redirect'], label: 'SELECT → no row', badgeAt: 'db', badge: 'no row', tone: 'err', ms: 4, title: 'The database has no such link',
          detail: 'The lookup is still a cheap primary-key seek, but a bot sending millions of these would turn the database into the bottleneck.' },
        { path: ['redirect', 'cache', 'redirect'], label: 'SET not-found · 60s', badgeAt: 'cache', badge: 'negative cache', ms: 1, title: 'Cache the absence',
          detail: 'Remembering "no such code" for a short time means repeated probes for the same code are answered from Redis.' },
        { path: ['redirect', 'edge', 'visitor'], label: '404 Not Found', tone: 'err', ms: 23, title: '404 returned',
          detail: 'Random 7-character codes make guessing a real link astronomically unlikely, but that is not access control: private links still need authorization.' },
      ],
    },
    {
      id: 'outage', name: 'Analytics down',
      down: ['stream'],
      summary: 'The event stream is unavailable. This is the design\'s <b>central decision</b> being tested: analytics is derived data and must never break redirects.',
      steps: [
        { path: ['visitor', 'edge', 'redirect'], label: 'GET /aZ8k2P', ms: 24, title: 'A normal redirect request',
          detail: 'Nothing about the incoming request has changed.' },
        { path: ['redirect', 'cache', 'redirect'], label: 'GET link:aZ8k2P', badgeAt: 'cache', badge: 'HIT', tone: 'ok', ms: 1, title: 'Cache hit',
          detail: 'The mapping is served as usual.' },
        { path: ['redirect', 'edge', 'visitor'], label: '302 Location', tone: 'ok', ms: 23, title: 'The visitor is redirected',
          detail: 'Same latency as on a healthy day.' },
        { path: ['redirect', 'stream'], label: 'click event ✗', async: true, tone: 'err', title: 'Publishing the click fails',
          detail: 'The publish fails fast with a timeout of a few milliseconds, on a background path. <code>clicks_dropped_total</code> increases and consumer-lag alerts page the on-call engineer.' },
        { at: 'redirect', badge: 'redirects unaffected', tone: 'ok', ms: 0, title: 'Users never notice',
          detail: 'Had the redirect written clicks synchronously, this outage would have taken down every short link. Durable mappings are the source of truth; analytics can be replayed or tolerate small gaps.' },
      ],
    },
  ],
});
const Lrl = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Client', kind: 'client' }] },
  { label: 'EDGE', nodes: [{ id: 'waf', label: 'WAF', sub: 'L7 firewall' }] },
  { label: 'GATEWAY', nodes: [{ id: 'gw', label: 'API Gateway', sub: 'authenticate & route', w: 160 }] },
  { label: 'LIMIT STATE', nodes: [{ id: 'redis', label: 'Redis Cluster', sub: 'token bucket (Lua)', kind: 'cache', w: 160 }] },
  { label: 'ORIGIN', nodes: [{ id: 'backend', label: 'Backend', sub: 'protected service' }] },
]);
defineFlow('sd-flow-ratelimiter', {
  title: 'Distributed Rate Limiter',
  hint: 'A request hits a rate limiter',
  zones: Lrl.zones,
  nodes: Lrl.nodes,
  edges: [
    ['client', 'waf'],
    ['waf', 'gw'],
    ['gw', 'redis'],
    ['gw', 'backend']
  ],
  scenarios: [
    {
      id: 'allowed', name: 'Allowed Request',
      summary: 'A normal request with available quota.',
      steps: [
        { path: ['client', 'waf'], label: 'GET /checkout', ms: 12, title: 'Request reaches edge' },
        { path: ['waf', 'gw'], label: 'GET /checkout', ms: 2, title: 'WAF allows traffic' },
        { path: ['gw', 'redis'], label: 'EVALSHA bucket', ms: 1, title: 'Check & deduct bucket', detail: 'Evaluate Lua script atomically.' },
        { at: 'redis', badge: 'tokens: 9', tone: 'ok', ms: 1, title: 'Token available', detail: 'Bucket has enough tokens. Subtract 1.' },
        { path: ['redis', 'gw'], label: 'allowed: 9', tone: 'ok', ms: 1, title: 'Allow request' },
        { path: ['gw', 'backend'], label: 'GET /checkout', ms: 2, title: 'Forward to backend' },
        { path: ['backend', 'gw'], label: '200 OK', tone: 'ok', ms: 45, title: 'Backend process' },
        { path: ['gw', 'waf', 'client'], label: '200 OK', tone: 'ok', ms: 15, title: 'Response sent', detail: 'Include X-RateLimit-Remaining: 9 header.' }
      ]
    },
    {
      id: 'denied', name: 'Rate Limit Exceeded',
      summary: 'The client has exhausted their quota and is rejected early.',
      steps: [
        { path: ['client', 'waf'], label: 'GET /checkout', ms: 12, title: 'Request reaches edge' },
        { path: ['waf', 'gw'], label: 'GET /checkout', ms: 2, title: 'WAF allows traffic' },
        { path: ['gw', 'redis'], label: 'EVALSHA bucket', ms: 1, title: 'Check & deduct bucket' },
        { at: 'redis', badge: 'tokens: 0', tone: 'err', ms: 1, title: 'Bucket empty', detail: 'No tokens remaining in the bucket.' },
        { path: ['redis', 'gw'], label: 'denied: 0', tone: 'err', ms: 1, title: 'Deny request' },
        { at: 'gw', badge: 'short circuit', tone: 'err', ms: 1, title: 'Reject early', detail: 'Do not forward to backend. Return 429 immediately.' },
        { path: ['gw', 'waf', 'client'], label: '429 Too Many Requests', tone: 'err', ms: 14, title: 'Response sent', detail: 'Include Retry-After header.' }
      ]
    },
    {
      id: 'redis_down', name: 'Redis Unavailable',
      down: ['redis'],
      summary: 'The rate limiter store goes down. The gateway must decide to fail open or closed.',
      steps: [
        { path: ['client', 'waf'], label: 'GET /checkout', ms: 12, title: 'Request reaches edge' },
        { path: ['waf', 'gw'], label: 'GET /checkout', ms: 2, title: 'WAF allows traffic' },
        { path: ['gw', 'redis'], label: 'EVALSHA bucket', tone: 'err', ms: 5, title: 'Redis call times out', detail: 'Fast timeout configured to preserve latency budget.' },
        { at: 'gw', badge: 'fail closed', tone: 'warn', ms: 1, title: 'Fail open or closed?', detail: 'For a sensitive /checkout route, we might fail closed to protect resources. For a read-heavy route, fail open with a local bucket.' },
        { path: ['gw', 'waf', 'client'], label: '503 Service Unavailable', tone: 'err', ms: 14, title: 'Reject request', detail: 'Failed closed due to unavailable dependency.' }
      ]
    }
  ]
});
const Lpb = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Client', kind: 'client' }] },
  { label: 'EDGE', nodes: [{ id: 'cdn', label: 'CDN / Edge', sub: 'public cache' }] },
  { label: 'SERVICE', nodes: [{ id: 'api', label: 'API Service', sub: 'auth & logic' }] },
  { label: 'STATE', nodes: [{ id: 'meta', label: 'Metadata DB', sub: 'PostgreSQL', kind: 'db' }, { id: 's3', label: 'Object Store', sub: 'blob storage', kind: 'db' }] },
  { label: 'BACKGROUND', nodes: [{ id: 'worker', label: 'Async Worker', sub: 'cleanup & expiry' }] },
]);
defineFlow('sd-flow-pastebin', {
  title: 'Pastebin Architecture',
  hint: 'Trace upload and read paths',
  zones: Lpb.zones,
  nodes: Lpb.nodes,
  edges: [
    ['client', 'cdn'],
    ['cdn', 'api'],
    ['api', 'meta'],
    ['api', 's3'],
    ['client', 's3', { async: true }],
    ['worker', 'meta'],
    ['worker', 's3']
  ],
  scenarios: [
    {
      id: 'upload', name: 'Upload Snippet',
      summary: 'Store bytes safely first, then commit the metadata record.',
      steps: [
        { path: ['client', 'cdn', 'api'], label: 'POST /v1/snippets', ms: 14, title: 'Upload content', detail: 'Includes size, visibility, expiry limits.' },
        { path: ['api', 's3'], label: 'PUT staging key', ms: 35, title: 'Store bytes first', detail: 'Write to a pending object key. Never create metadata pointing to missing bytes.' },
        { path: ['api', 'meta'], label: 'INSERT PENDING', ms: 4, title: 'Commit metadata', detail: 'Transactionally record the snippet ID, owner, and active status.' },
        { at: 'meta', badge: 'committed', tone: 'ok', ms: 1, title: 'Status ACTIVE' },
        { path: ['api', 'cdn', 'client'], label: '201 Created', tone: 'ok', ms: 12, title: 'Return snippet URL' }
      ]
    },
    {
      id: 'read_public', name: 'Read Public (Cache)',
      summary: 'A widely shared public snippet is served from the edge.',
      steps: [
        { path: ['client', 'cdn'], label: 'GET /v1/snippets/8fzK', ms: 8, title: 'Request reaches CDN' },
        { at: 'cdn', badge: 'MISS', tone: 'warn', ms: 1, title: 'Cache Miss' },
        { path: ['cdn', 'api'], label: 'Forward GET', ms: 15, title: 'Fetch from origin' },
        { path: ['api', 'meta'], label: 'SELECT status', ms: 2, title: 'Check metadata', detail: 'Verify snippet exists, is public, and not expired.' },
        { path: ['api', 's3'], label: 'GET object', ms: 12, title: 'Stream bytes' },
        { path: ['api', 'cdn'], label: '200 OK + Cache-Control', ms: 18, title: 'Origin response' },
        { at: 'cdn', badge: 'cached', tone: 'ok', ms: 1, title: 'Edge populates cache', detail: 'Future reads in this region bypass the origin completely.' },
        { path: ['cdn', 'client'], label: '200 OK', tone: 'ok', ms: 8, title: 'Delivered to client' }
      ]
    },
    {
      id: 'read_private', name: 'Read Private',
      summary: 'Private content requires authorization and signed URLs.',
      steps: [
        { path: ['client', 'cdn', 'api'], label: 'GET /v1/snippets/sec1', ms: 14, title: 'Request hits API', detail: 'CDN passes through private requests without caching.' },
        { path: ['api', 'meta'], label: 'SELECT authz', ms: 3, title: 'Check permissions', detail: 'Verify the caller has the role to view this snippet ID.' },
        { at: 'meta', badge: 'authorized', tone: 'ok', ms: 1, title: 'Permission granted' },
        { path: ['api', 'cdn', 'client'], label: '302 Redirect', ms: 12, title: 'Return signed URL', detail: 'Instead of proxying 10MB through the API, issue a short-lived S3 pre-signed URL.' },
        { path: ['client', 's3'], label: 'GET signed URL', async: true, tone: 'ok', ms: 22, title: 'Direct download', detail: 'Client fetches bytes directly from object storage securely.' }
      ]
    },
    {
      id: 'delete', name: 'Expiry & Deletion',
      summary: 'A worker handles background cleanup safely.',
      steps: [
        { path: ['worker', 'meta'], label: 'Find expired', ms: 5, title: 'Scan for expired snippets' },
        { at: 'meta', badge: 'mark deleted', tone: 'ok', ms: 2, title: 'Soft delete metadata', detail: 'Origin immediately denies new read requests.' },
        { path: ['worker', 's3'], label: 'DELETE object', async: true, ms: 15, title: 'Delete bytes', detail: 'Asynchronously clean up storage to save costs.' }
      ]
    }
  ]
});
const Lnp = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Client', kind: 'client' }] },
  { label: 'API · STATE', nodes: [{ id: 'api', label: 'Notification API', sub: 'auth & accept' }, { id: 'db', label: 'Record DB', sub: 'idempotency & log', kind: 'db' }] },
  { label: 'QUEUE', nodes: [{ id: 'queue', label: 'Event Queue', sub: 'partitioned topic', kind: 'queue' }] },
  { label: 'WORKERS', nodes: [{ id: 'workers', label: 'Worker Fleet', sub: 'fetch & dispatch' }] },
  { label: 'EXTERNAL', nodes: [{ id: 'provider', label: '3rd Party', sub: 'FCM / SMS' }] },
]);
defineFlow('sd-flow-notifications', {
  title: 'Notification Platform',
  hint: 'Trace publish and delivery',
  zones: Lnp.zones,
  nodes: Lnp.nodes,
  edges: [
    ['client', 'api'],
    ['api', 'db'],
    ['api', 'queue'],
    ['queue', 'workers', { async: true }],
    ['workers', 'provider'],
    ['workers', 'db', { async: true }],
    ['provider', 'api', { async: true }]
  ],
  scenarios: [
    {
      id: 'accept', name: 'Accept & Enqueue',
      summary: 'The API accepts the request, ensures durability, and returns quickly.',
      steps: [
        { path: ['client', 'api'], label: 'POST /notifications', ms: 12, title: 'Client sends intent' },
        { path: ['api', 'db'], label: 'INSERT idempotency', ms: 4, title: 'Check duplicates', detail: 'Ensures we do not spam users if the client retries.' },
        { path: ['api', 'queue'], label: 'Produce Event', ms: 3, title: 'Durably enqueue', detail: 'Queue guarantees delivery to async workers.' },
        { path: ['api', 'client'], label: '202 Accepted', tone: 'ok', ms: 1, title: 'Acknowledge', detail: 'Caller gets a fast response. Delivery happens asynchronously.' }
      ]
    },
    {
      id: 'dispatch', name: 'Process & Dispatch',
      summary: 'Workers consume the queue, format the message, and apply rate limits.',
      steps: [
        { path: ['queue', 'workers'], label: 'Consume Event', async: true, ms: 5, title: 'Worker picks up task' },
        { at: 'workers', badge: 'rate limit', tone: 'warn', ms: 2, title: 'Apply limits', detail: 'Check user preferences and provider rate limits.' },
        { path: ['workers', 'provider'], label: 'POST /v1/send', ms: 45, title: 'Send to provider', detail: 'Call external API (e.g. Twilio, FCM).' },
        { path: ['provider', 'workers'], label: '200 OK', tone: 'ok', ms: 1, title: 'Provider accepted' },
        { path: ['workers', 'db'], label: 'UPDATE status=SENT', async: true, ms: 4, title: 'Log success' }
      ]
    },
    {
      id: 'callback', name: 'Provider Callback',
      summary: 'The external provider asynchronously reports ultimate delivery or bounce.',
      steps: [
        { path: ['provider', 'api'], label: 'POST /webhook', async: true, ms: 15, title: 'Webhook fired', detail: 'Provider reports that the SMS was delivered to the handset.' },
        { path: ['api', 'queue'], label: 'Produce Callback', ms: 3, title: 'Enqueue update' },
        { path: ['queue', 'workers'], label: 'Consume', async: true, ms: 5, title: 'Worker processes webhook' },
        { path: ['workers', 'db'], label: 'UPDATE status=DELIVERED', async: true, tone: 'ok', ms: 4, title: 'Update final state' }
      ]
    }
  ]
});
const Lpp = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Client', kind: 'client' }] },
  { label: 'SERVICE', nodes: [{ id: 'api', label: 'Upload API', sub: 'metadata & auth' }, { id: 'queue', label: 'Transform Q', sub: 'job queue', kind: 'queue' }, { id: 'cdn', label: 'CDN Edge', sub: 'public cache' }] },
  { label: 'STORAGE · WORKERS', nodes: [{ id: 's3', label: 'Object Store', sub: 'original & variants', kind: 'db' }, { id: 'worker', label: 'Worker Fleet', sub: 'resize & scan' }] },
]);
defineFlow('sd-flow-photopipeline', {
  title: 'Photo Upload & Pipeline',
  hint: 'Trace direct uploads and async processing',
  zones: Lpp.zones,
  nodes: Lpp.nodes,
  edges: [
    ['client', 'api'],
    ['client', 's3', { async: true }],
    ['api', 's3'],
    ['api', 'queue'],
    ['queue', 'worker', { async: true }],
    ['worker', 's3'],
    ['worker', 'api'],
    ['client', 'cdn'],
    ['cdn', 's3']
  ],
  scenarios: [
    {
      id: 'upload', name: 'Direct Upload',
      summary: 'Clients upload 50MB blobs directly to storage to save API bandwidth.',
      steps: [
        { path: ['client', 'api'], label: 'POST /uploads', ms: 12, title: 'Request upload session' },
        { at: 'api', badge: 'authz', tone: 'ok', ms: 2, title: 'Check limits', detail: 'Validate size and format limits.' },
        { path: ['api', 'client'], label: '201 Signed URL', ms: 8, title: 'Return pre-signed URL', detail: 'API gives client a direct cryptographic pass to S3.' },
        { path: ['client', 's3'], label: 'PUT multipart', async: true, ms: 800, title: 'Direct transfer', detail: '50MB payload goes straight to S3, bypassing our application servers entirely.' }
      ]
    },
    {
      id: 'processing', name: 'Process Pipeline',
      summary: 'Metadata completion triggers asynchronous resizing.',
      steps: [
        { path: ['client', 'api'], label: 'POST /complete', ms: 15, title: 'Mark upload complete' },
        { path: ['api', 's3'], label: 'HEAD object', ms: 20, title: 'Verify bytes', detail: 'Confirm the file actually exists in S3 before trusting the client.' },
        { path: ['api', 'queue'], label: 'Produce Event', ms: 5, title: 'Enqueue transform job' },
        { path: ['api', 'client'], label: '202 PENDING', tone: 'ok', ms: 10, title: 'Return to client' },
        { path: ['queue', 'worker'], label: 'Consume', async: true, ms: 8, title: 'Worker starts job' },
        { at: 'worker', badge: 'resizing', tone: 'warn', ms: 200, title: 'Generate variants', detail: 'Compute intensive: create thumbnails, WebP, AVIF.' },
        { path: ['worker', 's3'], label: 'PUT variants', ms: 40, title: 'Save outputs' },
        { path: ['worker', 'api'], label: 'Webhook: READY', ms: 12, title: 'Update metadata state', detail: 'Mark media as fully READY for viewing.' }
      ]
    },
    {
      id: 'view', name: 'Serve Variants',
      summary: 'Thumbnails are served globally via CDN.',
      steps: [
        { path: ['client', 'cdn'], label: 'GET /thumb.jpg', ms: 10, title: 'Request thumbnail' },
        { at: 'cdn', badge: 'MISS', tone: 'warn', ms: 1, title: 'Cache miss' },
        { path: ['cdn', 's3'], label: 'Fetch from origin', ms: 25, title: 'Read variant bytes' },
        { at: 'cdn', badge: 'cached', tone: 'ok', ms: 1, title: 'Cache at edge' },
        { path: ['cdn', 'client'], label: '200 OK', tone: 'ok', ms: 10, title: 'Deliver quickly' }
      ]
    }
  ]
});
const Lch = lane([
  { label: 'CLIENTS', nodes: [{ id: 'alice', label: 'Alice', kind: 'client' }, { id: 'bob', label: 'Bob', kind: 'client' }] },
  { label: 'GATEWAYS', nodes: [{ id: 'gwa', label: 'Gateway A', sub: 'WebSocket state' }, { id: 'gwb', label: 'Gateway B', sub: 'WebSocket state' }] },
  { label: 'ROUTING', nodes: [{ id: 'svc', label: 'Message Router', sub: 'business logic' }, { id: 'push', label: 'Push Svc', sub: 'FCM / APNs' }] },
  { label: 'STATE', nodes: [{ id: 'db', label: 'Chat Log', sub: 'Cassandra / KV', kind: 'db' }] },
]);
defineFlow('sd-flow-chat', {
  title: 'Real-Time Chat',
  hint: 'Trace a message from Alice to Bob',
  zones: Lch.zones,
  nodes: Lch.nodes,
  edges: [
    ['alice', 'gwa'],
    ['bob', 'gwb'],
    ['gwa', 'svc'],
    ['gwb', 'svc'],
    ['svc', 'db'],
    ['svc', 'push'],
    ['push', 'bob', { async: true }]
  ],
  scenarios: [
    {
      id: 'send', name: 'Online Delivery',
      summary: 'Alice sends a message to Bob, who is currently connected.',
      steps: [
        { path: ['alice', 'gwa'], label: 'SEND {text}', ms: 12, title: 'Send over WebSocket' },
        { path: ['gwa', 'svc'], label: 'Route msg', ms: 4, title: 'Internal routing', detail: 'Gateway forwards to stateless message service.' },
        { path: ['svc', 'db'], label: 'INSERT msg', ms: 8, title: 'Persist durably', detail: 'Ensure no message loss before acknowledging.' },
        { path: ['svc', 'gwa', 'alice'], label: 'SENT (seq: 42)', tone: 'ok', ms: 14, title: 'Acknowledge sender', detail: 'Alice gets a checkmark (sent).' },
        { at: 'svc', badge: 'lookup Bob', ms: 2, title: 'Find recipient session', detail: 'Redis/Session store says Bob is on Gateway B.' },
        { path: ['svc', 'gwb'], label: 'Forward to Bob', ms: 3, title: 'Internal dispatch' },
        { path: ['gwb', 'bob'], label: 'MESSAGE {text}', ms: 15, title: 'Deliver over WebSocket', detail: 'Push down long-lived connection.' },
        { path: ['bob', 'gwb', 'svc', 'gwa', 'alice'], label: 'DELIVERED (seq: 42)', tone: 'ok', ms: 30, title: 'Delivery Receipt', detail: 'Alice gets a double checkmark (delivered).' }
      ]
    },
    {
      id: 'offline', name: 'Offline Push',
      summary: 'Bob is disconnected, so the message triggers a mobile push notification.',
      steps: [
        { path: ['alice', 'gwa', 'svc'], label: 'SEND {text}', ms: 16, title: 'Alice sends message' },
        { path: ['svc', 'db'], label: 'INSERT msg', ms: 8, title: 'Persist durably' },
        { at: 'svc', badge: 'Bob offline', tone: 'warn', ms: 2, title: 'Session lookup fails', detail: 'Bob has no active WebSocket.' },
        { path: ['svc', 'push'], label: 'Trigger Push', ms: 5, title: 'Send to Push Platform' },
        { path: ['push', 'bob'], label: 'Wake up device', async: true, ms: 500, title: 'Apple/Google Push', detail: 'Device wakes up and connects to sync.' }
      ]
    },
    {
      id: 'read', name: 'Read Receipt',
      summary: 'Bob opens the app and reads the message.',
      steps: [
        { path: ['bob', 'gwb', 'svc'], label: 'READ (seq: 42)', ms: 15, title: 'Send read cursor' },
        { path: ['svc', 'db'], label: 'UPDATE cursor', async: true, ms: 8, title: 'Persist read state' },
        { path: ['svc', 'gwa', 'alice'], label: 'READ {seq: 42}', tone: 'ok', ms: 15, title: 'Notify Alice', detail: 'Blue checkmarks appear for Alice.' }
      ]
    }
  ]
});
const Lnf = lane([
  { label: 'CLIENTS', nodes: [{ id: 'author', label: 'Author', kind: 'client' }, { id: 'reader', label: 'Follower', kind: 'client' }] },
  { label: 'API', nodes: [{ id: 'api_w', label: 'Write API', sub: 'create post' }, { id: 'api_r', label: 'Read API', sub: 'merge & hydrate' }] },
  { label: 'STATE', nodes: [{ id: 'db_post', label: 'Post DB', sub: 'outbox & source', kind: 'db' }, { id: 'db_feed', label: 'Feed Cache', sub: 'Redis timeline', kind: 'cache' }] },
  { label: 'ASYNC', nodes: [{ id: 'worker', label: 'Fanout Worker', sub: 'async routing' }] },
]);
defineFlow('sd-flow-newsfeed', {
  title: 'Hybrid News Feed',
  hint: 'Trace fanout on write vs read',
  zones: Lnf.zones,
  nodes: Lnf.nodes,
  edges: [
    ['author', 'api_w'],
    ['api_w', 'db_post'],
    ['db_post', 'worker', { async: true }],
    ['worker', 'db_feed'],
    ['reader', 'api_r'],
    ['api_r', 'db_feed'],
    ['api_r', 'db_post']
  ],
  scenarios: [
    {
      id: 'write', name: 'Write & Fanout',
      summary: 'Normal users fan out to followers. Celebrities do not.',
      steps: [
        { path: ['author', 'api_w'], label: 'POST /status', ms: 12, title: 'Create Post' },
        { path: ['api_w', 'db_post'], label: 'INSERT post + outbox', ms: 5, title: 'Save to DB', detail: 'Single transaction commits the post and queues a fanout event.' },
        { path: ['api_w', 'author'], label: '201 Created', tone: 'ok', ms: 1, title: 'Ack to author' },
        { path: ['db_post', 'worker'], label: 'Consume Event', async: true, ms: 15, title: 'Worker processes outbox' },
        { at: 'worker', badge: 'followers < 100k', tone: 'ok', ms: 2, title: 'Routing decision', detail: 'Normal user: push to all followers. If celebrity, skip push to save writes.' },
        { path: ['worker', 'db_feed'], label: 'ZADD feeds', async: true, ms: 8, title: 'Write feed references', detail: 'Push the post ID into active followers Redis timelines.' }
      ]
    },
    {
      id: 'read', name: 'Read (Hybrid Merge)',
      summary: 'Read time merges the push-timeline with celebrity pull-posts.',
      steps: [
        { path: ['reader', 'api_r'], label: 'GET /feed', ms: 10, title: 'Reader opens app' },
        { path: ['api_r', 'db_feed'], label: 'ZRANGE push_feed', ms: 2, title: 'Fetch precomputed feed' },
        { path: ['api_r', 'db_post'], label: 'SELECT celeb_posts', ms: 4, title: 'Fetch from celebs', detail: 'Read recent posts from celebrities this user follows.' },
        { at: 'api_r', badge: 'merge', ms: 1, title: 'Merge by timestamp' },
        { path: ['api_r', 'db_post'], label: 'MGET post_details', ms: 4, title: 'Hydrate data', detail: 'Fetch the actual post text, resolving any deleted or blocked posts.' },
        { path: ['api_r', 'reader'], label: '200 OK', tone: 'ok', ms: 8, title: 'Deliver Feed' }
      ]
    }
  ]
});

const Lco = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Shopper', kind: 'client' }] },
  { label: 'API', nodes: [{ id: 'api', label: 'Checkout API', sub: 'idempotent' }] },
  { label: 'STATE', nodes: [{ id: 'db_o', label: 'Order DB', sub: 'PENDING state', kind: 'db' }, { id: 'db_i', label: 'Inventory DB', sub: 'conditional hold', kind: 'db' }] },
  { label: 'SAGA', nodes: [{ id: 'saga', label: 'Saga Worker', sub: 'async payment' }] },
  { label: 'EXTERNAL', nodes: [{ id: 'psp', label: 'Stripe / PSP', sub: 'external' }] },
]);
defineFlow('sd-flow-checkout', {
  title: 'Checkout Saga',
  hint: 'Trace the asynchronous payment state machine',
  zones: Lco.zones,
  nodes: Lco.nodes,
  edges: [
    ['client', 'api'],
    ['api', 'db_o'],
    ['api', 'db_i'],
    ['db_o', 'saga', { async: true }],
    ['saga', 'psp'],
    ['saga', 'db_o'],
    ['saga', 'db_i']
  ],
  scenarios: [
    {
      id: 'success', name: 'Reserve & Pay (Success)',
      summary: 'Inventory is reserved conditionally; external payment is handled async.',
      steps: [
        { path: ['client', 'api'], label: 'POST /checkout', ms: 14, title: 'Submit Cart', detail: 'Includes idempotency key.' },
        { path: ['api', 'db_i'], label: 'UPDATE hold qty', ms: 4, title: 'Reserve Inventory', detail: 'Move items to held state. Will expire if payment takes too long.' },
        { path: ['api', 'db_o'], label: 'INSERT PENDING', ms: 4, title: 'Create Order & Outbox', detail: 'Local transaction safely records the order before ANY external calls.' },
        { path: ['api', 'client'], label: '202 Accepted', tone: 'ok', ms: 1, title: 'Ack receipt', detail: 'Client polls for final status.' },
        { path: ['db_o', 'saga'], label: 'Consume Outbox', async: true, ms: 5, title: 'Payment Worker' },
        { path: ['saga', 'psp'], label: 'POST /charge', ms: 450, title: 'External Call', detail: 'Slow and fallible Stripe/Adyen call using Order ID as idempotency key.' },
        { path: ['psp', 'saga'], label: '200 Paid', tone: 'ok', ms: 1, title: 'Payment Success' },
        { path: ['saga', 'db_o'], label: 'UPDATE CONFIRMED', tone: 'ok', ms: 4, title: 'Complete Order' }
      ]
    },
    {
      id: 'fail', name: 'Payment Failure',
      summary: 'A declined card must rollback the inventory hold.',
      steps: [
        { path: ['client', 'api'], label: 'POST /checkout', ms: 14, title: 'Submit Cart' },
        { path: ['api', 'db_i'], label: 'UPDATE hold qty', ms: 4, title: 'Reserve Inventory' },
        { path: ['api', 'db_o'], label: 'INSERT PENDING', ms: 4, title: 'Create Order' },
        { path: ['api', 'client'], label: '202 Accepted', ms: 1, title: 'Ack receipt' },
        { path: ['db_o', 'saga'], label: 'Consume Outbox', async: true, ms: 5, title: 'Payment Worker' },
        { path: ['saga', 'psp'], label: 'POST /charge', ms: 300, title: 'External Call' },
        { path: ['psp', 'saga'], label: '402 Declined', tone: 'err', ms: 1, title: 'Payment Failed', detail: 'Card declined or insufficient funds.' },
        { path: ['saga', 'db_o'], label: 'UPDATE FAILED', tone: 'err', ms: 4, title: 'Mark Order Failed' },
        { path: ['saga', 'db_i'], label: 'Release Hold', tone: 'ok', ms: 4, title: 'Restore Inventory', detail: 'Release the conditional hold so others can buy.' }
      ]
    }
  ]
});
const Lsa = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Client', kind: 'client' }] },
  { label: 'SERVICE', nodes: [{ id: 'sug', label: 'Suggest API', sub: 'in-memory trie' }, { id: 'search', label: 'Search API', sub: 'query parser' }] },
  { label: 'INDEX', nodes: [{ id: 'ingest', label: 'Ingest Pipeline', sub: 'async indexer' }, { id: 'idx', label: 'Search Index', sub: 'Elasticsearch', kind: 'db' }] },
  { label: 'SOURCE', nodes: [{ id: 'db', label: 'Catalog DB', sub: 'source of truth', kind: 'db' }] },
]);
defineFlow('sd-flow-search', {
  title: 'Search & Autocomplete',
  hint: 'Trace suggest vs full search',
  zones: Lsa.zones,
  nodes: Lsa.nodes,
  edges: [
    ['client', 'sug'],
    ['client', 'search'],
    ['search', 'idx'],
    ['db', 'ingest', { async: true }],
    ['ingest', 'idx', { async: true }],
    ['ingest', 'sug', { async: true }]
  ],
  scenarios: [
    {
      id: 'suggest', name: 'Suggest',
      summary: 'Autocomplete fires on every keystroke and must be extremely fast.',
      steps: [
        { path: ['client', 'sug'], label: 'GET /suggest?q=app', ms: 10, title: 'Keystroke' },
        { at: 'sug', badge: 'trie lookup', tone: 'ok', ms: 2, title: 'Memory hit', detail: 'Prefix matching in memory or Redis.' },
        { path: ['sug', 'client'], label: '["apple", "apparel"]', ms: 8, title: 'Instant return' }
      ]
    },
    {
      id: 'search', name: 'Full Search',
      summary: 'A full query runs against the distributed search index.',
      steps: [
        { path: ['client', 'search'], label: 'GET /search?q=apple', ms: 12, title: 'Submit query' },
        { path: ['search', 'idx'], label: 'Scatter-Gather', ms: 20, title: 'Query shards', detail: 'Fetch top N hits from each index shard.' },
        { at: 'search', badge: 'merge & rank', ms: 5, title: 'Finalize results' },
        { path: ['search', 'client'], label: '200 OK', tone: 'ok', ms: 15, title: 'Deliver page' }
      ]
    },
    {
      id: 'update', name: 'Catalog Update',
      summary: 'Changes in the catalog asynchronously propagate to the index and suggest structures.',
      steps: [
        { at: 'db', badge: 'price changed', ms: 2, title: 'DB transaction' },
        { path: ['db', 'ingest'], label: 'CDC Event', async: true, ms: 10, title: 'Change Data Capture' },
        { path: ['ingest', 'idx'], label: 'Bulk Update', async: true, ms: 100, title: 'Update Index' },
        { path: ['ingest', 'sug'], label: 'Update Trie', async: true, ms: 15, title: 'Update Suggest' }
      ]
    }
  ]
});

const Lst = lane([
  { label: 'BUYER', nodes: [{ id: 'buyer', label: 'Buyer', kind: 'client' }] },
  { label: 'SERVICE', nodes: [{ id: 'wait', label: 'Waiting Room', sub: 'rate limiter' }, { id: 'api', label: 'Booking API', sub: 'transactional' }] },
  { label: 'STATE', nodes: [{ id: 'db', label: 'Seat DB', sub: 'conditional updates', kind: 'db' }] },
  { label: 'EXTERNAL', nodes: [{ id: 'pay', label: 'Payment', sub: 'external PSP' }] },
]);
defineFlow('sd-flow-seats', {
  title: 'Seat Reservation',
  hint: 'Trace a high-contention booking',
  zones: Lst.zones,
  nodes: Lst.nodes,
  edges: [
    ['buyer', 'wait'],
    ['wait', 'api'],
    ['buyer', 'api'],
    ['api', 'db'],
    ['api', 'pay']
  ],
  scenarios: [
    {
      id: 'buy', name: 'Hold & Buy',
      summary: 'A user successfully claims a seat and pays for it.',
      steps: [
        { path: ['buyer', 'wait'], label: 'GET /event', ms: 10, title: 'Enter queue' },
        { path: ['wait', 'api'], label: 'Token issued', tone: 'ok', ms: 5, title: 'Admitted' },
        { path: ['buyer', 'api'], label: 'POST /hold (Seat 1)', ms: 15, title: 'Request seat' },
        { path: ['api', 'db'], label: 'UPDATE seat=HELD', ms: 6, title: 'Conditional Hold', detail: "WHERE status='AVAILABLE'. Rowcount=1 means success." },
        { path: ['api', 'pay'], label: 'Process Card', ms: 300, title: 'External Payment' },
        { path: ['pay', 'api'], label: '200 Paid', tone: 'ok', ms: 2, title: 'Payment Success' },
        { path: ['api', 'db'], label: 'UPDATE seat=SOLD', tone: 'ok', ms: 5, title: 'Confirm Order', detail: 'WHERE status=HELD and hold_id matches.' },
        { path: ['api', 'buyer'], label: 'Ticket Issued', tone: 'ok', ms: 10, title: 'Done' }
      ]
    },
    {
      id: 'conflict', name: 'Double Booking Prevented',
      summary: 'Two users try to hold the same seat at the exact same millisecond.',
      steps: [
        { path: ['buyer', 'api'], label: 'POST /hold (Seat 1)', ms: 15, title: 'Concurrent requests' },
        { path: ['api', 'db'], label: 'UPDATE seat=HELD', ms: 6, title: 'Database lock contention' },
        { at: 'db', badge: 'rowcount=0', tone: 'warn', ms: 2, title: 'Lost race', detail: 'The other transaction won the lock. This one sees 0 rows updated.' },
        { path: ['db', 'api'], label: '0 rows affected', ms: 2, title: 'DB response' },
        { path: ['api', 'buyer'], label: '409 Conflict', tone: 'err', ms: 10, title: 'Seat Taken', detail: 'Prompt user to pick another seat. No double sell.' }
      ]
    }
  ]
});

const Lcr = lane([
  { label: 'DISCOVERY', nodes: [{ id: 'disc', label: 'Discovery', sub: 'extract links' }] },
  { label: 'DEDUP', nodes: [{ id: 'dup', label: 'URL Dedup', sub: 'Bloom filter', kind: 'cache' }] },
  { label: 'FRONTIER', nodes: [{ id: 'front', label: 'Frontier', sub: 'per-host queues', kind: 'queue' }] },
  { label: 'FETCH', nodes: [{ id: 'fetch', label: 'Fetcher', sub: 'politeness rules' }] },
  { label: 'STORAGE', nodes: [{ id: 'store', label: 'Storage', sub: 'content dedup', kind: 'db' }] },
]);
defineFlow('sd-flow-crawler', {
  title: 'Web Crawler',
  hint: 'Trace the URL discovery loop',
  zones: Lcr.zones,
  nodes: Lcr.nodes,
  edges: [
    ['disc', 'dup'],
    ['dup', 'front'],
    ['front', 'fetch'],
    ['fetch', 'store'],
    ['store', 'disc', { async: true }]
  ],
  scenarios: [
    {
      id: 'crawl', name: 'Crawl Loop',
      summary: 'URLs flow through deduplication, politeness shaping, and fetching.',
      steps: [
        { path: ['disc', 'dup'], label: 'Found URL', ms: 2, title: 'New link discovered' },
        { at: 'dup', badge: 'not seen', tone: 'ok', ms: 1, title: 'Check Bloom Filter', detail: 'URL is novel, proceed to queue.' },
        { path: ['dup', 'front'], label: 'Enqueue URL', ms: 3, title: 'Add to Frontier' },
        { at: 'front', badge: 'host rate limit', ms: 50, title: 'Politeness delay', detail: 'Wait until the target host is ready to be crawled again.' },
        { path: ['front', 'fetch'], label: 'Dequeue URL', ms: 4, title: 'Worker ready' },
        { at: 'fetch', badge: 'downloading', ms: 300, title: 'HTTP GET', detail: 'Fetch the page content over the internet.' },
        { path: ['fetch', 'store'], label: 'Save bytes', ms: 15, title: 'Store content' },
        { path: ['store', 'disc'], label: 'Extract links', async: true, ms: 10, title: 'Parse HTML', detail: 'Find new hrefs and feed them back to Discovery.' }
      ]
    }
  ]
});
const Lsc = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Client', kind: 'client' }] },
  { label: 'SERVICE', nodes: [{ id: 'api', label: 'Scheduler API', sub: 'submit & state' }, { id: 'disp', label: 'Dispatcher', sub: 'cron & polling' }] },
  { label: 'STATE', nodes: [{ id: 'db', label: 'State DB', sub: 'PostgreSQL', kind: 'db' }, { id: 'q', label: 'Task Queue', sub: 'ready to run', kind: 'queue' }] },
  { label: 'WORKERS', nodes: [{ id: 'worker', label: 'Worker Fleet', sub: 'execute tasks' }] },
]);
defineFlow('sd-flow-scheduler', {
  title: 'Workflow Scheduler',
  hint: 'Trace task dispatch and execution',
  zones: Lsc.zones,
  nodes: Lsc.nodes,
  edges: [
    ['client', 'api'],
    ['api', 'db'],
    ['disp', 'db'],
    ['disp', 'q'],
    ['q', 'worker', { async: true }],
    ['worker', 'db']
  ],
  scenarios: [
    {
      id: 'submit', name: 'Submit Workflow',
      summary: 'A client submits a DAG of tasks to be executed.',
      steps: [
        { path: ['client', 'api'], label: 'POST /workflows', ms: 12, title: 'Submit Job' },
        { path: ['api', 'db'], label: 'INSERT PENDING', ms: 5, title: 'Persist state', detail: 'Tasks are stored with dependencies and PENDING status.' },
        { path: ['api', 'client'], label: '201 Created', tone: 'ok', ms: 1, title: 'Ack receipt' }
      ]
    },
    {
      id: 'execute', name: 'Dispatch & Execute',
      summary: 'The dispatcher finds ready tasks and queues them for workers.',
      steps: [
        { path: ['disp', 'db'], label: 'SELECT PENDING', ms: 4, title: 'Find ready tasks', detail: 'Tasks whose dependencies are met or scheduled time has passed.' },
        { path: ['disp', 'q'], label: 'Enqueue task', ms: 3, title: 'Push to queue' },
        { path: ['q', 'worker'], label: 'Consume', async: true, ms: 5, title: 'Worker picks up task' },
        { path: ['worker', 'db'], label: 'UPDATE RUNNING', ms: 4, title: 'Claim task', detail: 'Lock the task so others do not run it.' },
        { at: 'worker', badge: 'executing', ms: 500, title: 'Run business logic' },
        { path: ['worker', 'db'], label: 'UPDATE SUCCESS', tone: 'ok', ms: 4, title: 'Mark complete', detail: 'This may unblock downstream tasks in the DAG.' }
      ]
    }
  ]
});

const Lmt = lane([
  { label: 'AGENT', nodes: [{ id: 'agent', label: 'Agent', kind: 'client' }] },
  { label: 'INGEST', nodes: [{ id: 'ingest', label: 'Ingest API', sub: 'validate & quota' }] },
  { label: 'BUFFER', nodes: [{ id: 'wal', label: 'WAL Buffer', sub: 'durable stream', kind: 'queue' }] },
  { label: 'STORAGE', nodes: [{ id: 'tsdb', label: 'TSDB', sub: 'blocks & index', kind: 'db' }, { id: 'comp', label: 'Compactor', sub: 'downsample' }] },
]);
defineFlow('sd-flow-metrics', {
  title: 'Metrics Platform',
  hint: 'Trace high-volume ingest',
  zones: Lmt.zones,
  nodes: Lmt.nodes,
  edges: [
    ['agent', 'ingest'],
    ['ingest', 'wal'],
    ['wal', 'tsdb', { async: true }],
    ['comp', 'tsdb']
  ],
  scenarios: [
    {
      id: 'ingest', name: 'Ingest & Batch',
      summary: 'High volume metrics are buffered before being written to optimized storage.',
      steps: [
        { path: ['agent', 'ingest'], label: 'POST /metrics', ms: 5, title: 'Push samples' },
        { at: 'ingest', badge: 'quota check', ms: 1, title: 'Validate cardinality', detail: 'Reject if tenant exceeds active series limit.' },
        { path: ['ingest', 'wal'], label: 'Append batch', ms: 3, title: 'Write Ahead Log', detail: 'Durably buffer the writes.' },
        { path: ['ingest', 'agent'], label: '202 Accepted', tone: 'ok', ms: 1, title: 'Ack quickly' },
        { path: ['wal', 'tsdb'], label: 'Flush chunks', async: true, ms: 50, title: 'Write to TSDB', detail: 'Periodically flush memory chunks to immutable block storage.' }
      ]
    },
    {
      id: 'downsample', name: 'Background Downsample',
      summary: 'Older data is compacted to save space and speed up long-range queries.',
      steps: [
        { path: ['comp', 'tsdb'], label: 'Read raw blocks', ms: 200, title: 'Fetch old data' },
        { at: 'comp', badge: 'aggregate', ms: 50, title: 'Roll up into 1h chunks' },
        { path: ['comp', 'tsdb'], label: 'Write 1h blocks', tone: 'ok', ms: 100, title: 'Save compacted data' }
      ]
    }
  ]
});

const Llg = lane([
  { label: 'SERVICE', nodes: [{ id: 'app', label: 'Service', kind: 'client' }] },
  { label: 'AGENT', nodes: [{ id: 'agent', label: 'Log Agent', sub: 'local buffer' }] },
  { label: 'INGEST', nodes: [{ id: 'ingest', label: 'Log Ingest', sub: 'redact & route' }] },
  { label: 'STORAGE', nodes: [{ id: 'store', label: 'Log Store', sub: 'blob & index', kind: 'db' }] },
]);
defineFlow('sd-flow-logging', {
  title: 'Logging Platform',
  hint: 'Trace structured log delivery',
  zones: Llg.zones,
  nodes: Llg.nodes,
  edges: [
    ['app', 'agent'],
    ['agent', 'ingest', { async: true }],
    ['ingest', 'store']
  ],
  scenarios: [
    {
      id: 'ship', name: 'Buffer & Ship',
      summary: 'Logs are written asynchronously to avoid blocking the product service.',
      steps: [
        { path: ['app', 'agent'], label: 'Write stdout', ms: 0, title: 'Local emit', detail: 'Service writes to local disk or stdout. No network call.' },
        { at: 'agent', badge: 'batching', ms: 1000, title: 'Buffer locally', detail: 'Wait for batch size or time limit.' },
        { path: ['agent', 'ingest'], label: 'POST /logs', async: true, ms: 20, title: 'Ship to backend' },
        { at: 'ingest', badge: 'redact PII', tone: 'warn', ms: 2, title: 'Scrub secrets', detail: 'Remove sensitive fields before durable storage.' },
        { path: ['ingest', 'store'], label: 'Save Chunks', tone: 'ok', ms: 45, title: 'Durable storage', detail: 'Save compressed chunks and index common fields.' }
      ]
    }
  ]
});
const Ldv = lane([
  { label: 'DEVICES', nodes: [{ id: 'd1', label: 'Device A', kind: 'client' }, { id: 'd2', label: 'Device B', kind: 'client' }] },
  { label: 'API', nodes: [{ id: 'api', label: 'Sync API', sub: 'metadata commit' }] },
  { label: 'STATE', nodes: [{ id: 'db', label: 'Metadata DB', sub: 'version & cursor', kind: 'db' }, { id: 's3', label: 'Object Store', sub: 'immutable blocks', kind: 'db' }] },
  { label: 'ASYNC', nodes: [{ id: 'pub', label: 'Change Feed', sub: 'async fanout' }] },
]);
defineFlow('sd-flow-drive', {
  title: 'Cloud Drive Sync',
  hint: 'Trace direct upload and multi-device sync',
  zones: Ldv.zones,
  nodes: Ldv.nodes,
  edges: [
    ['d1', 'api'],
    ['d1', 's3', { async: true }],
    ['api', 'db'],
    ['db', 'pub', { async: true }],
    ['pub', 'd2', { async: true }],
    ['d2', 'api'],
    ['d2', 's3']
  ],
  scenarios: [
    {
      id: 'upload', name: 'Upload & Sync',
      summary: 'Device A uploads a new version, which is synced to Device B.',
      steps: [
        { path: ['d1', 'api'], label: 'Get URL', ms: 10, title: 'Request Upload Session' },
        { path: ['api', 'd1'], label: 'Signed URL', ms: 5, title: 'Return Token' },
        { path: ['d1', 's3'], label: 'PUT chunks', async: true, ms: 500, title: 'Direct Upload', detail: 'Bytes bypass API servers.' },
        { path: ['d1', 'api'], label: 'Commit File', ms: 12, title: 'Finalize Upload' },
        { path: ['api', 'db'], label: 'UPDATE version', ms: 8, title: 'Commit Metadata', detail: 'Bump change cursor and record new immutable object ID.' },
        { path: ['db', 'pub'], label: 'Cursor bumped', async: true, ms: 15, title: 'Notify Feed' },
        { path: ['pub', 'd2'], label: 'Invalidate', async: true, ms: 20, title: 'Push Notification', detail: 'Wake up Device B via WebSocket/APNs.' },
        { path: ['d2', 'api'], label: 'Poll changes', ms: 10, title: 'Fetch Metadata', detail: 'Device B learns about the new version ID.' },
        { path: ['d2', 's3'], label: 'GET object', ms: 400, title: 'Download File', detail: 'Device B fetches the new bytes.' }
      ]
    }
  ]
});

const Lvd = lane([
  { label: 'CLIENTS', nodes: [{ id: 'creator', label: 'Creator', kind: 'client' }, { id: 'viewer', label: 'Viewer', kind: 'client' }] },
  { label: 'SERVICE', nodes: [{ id: 'job', label: 'Transcoder', sub: 'async ladder' }, { id: 'auth', label: 'Auth API', sub: 'signed manifests' }] },
  { label: 'STORAGE', nodes: [{ id: 's3', label: 'Object Store', sub: 'derivatives', kind: 'db' }] },
  { label: 'EDGE', nodes: [{ id: 'cdn', label: 'CDN Edge', sub: 'global cache' }] },
]);
defineFlow('sd-flow-vod', {
  title: 'Video On Demand',
  hint: 'Trace upload, transcode, and streaming',
  zones: Lvd.zones,
  nodes: Lvd.nodes,
  edges: [
    ['creator', 's3'],
    ['s3', 'job', { async: true }],
    ['job', 's3'],
    ['viewer', 'auth'],
    ['viewer', 'cdn'],
    ['cdn', 's3']
  ],
  scenarios: [
    {
      id: 'transcode', name: 'Upload & Transcode',
      summary: 'A source video is transformed into an adaptive bitrate ladder.',
      steps: [
        { path: ['creator', 's3'], label: 'PUT source', ms: 800, title: 'Upload Original' },
        { path: ['s3', 'job'], label: 'Event', async: true, ms: 10, title: 'Trigger job' },
        { at: 'job', badge: 'encoding', ms: 2000, title: 'Transcode Ladder', detail: 'Generate 1080p, 720p, 480p segments + HLS manifest.' },
        { path: ['job', 's3'], label: 'PUT segments', tone: 'ok', ms: 50, title: 'Store derivatives' }
      ]
    },
    {
      id: 'play', name: 'Playback',
      summary: 'A viewer receives a signed manifest and pulls segments from the CDN.',
      steps: [
        { path: ['viewer', 'auth'], label: 'GET /play', ms: 15, title: 'Request Playback' },
        { path: ['auth', 'viewer'], label: 'Signed URL', ms: 5, title: 'Issue Entitlement', detail: 'Token scoped to this session.' },
        { path: ['viewer', 'cdn'], label: 'GET manifest', ms: 10, title: 'Request HLS Manifest' },
        { at: 'cdn', badge: 'MISS', tone: 'warn', ms: 1, title: 'Cache Miss' },
        { path: ['cdn', 's3'], label: 'Fetch Origin', ms: 30, title: 'Shield / Origin Pull' },
        { path: ['cdn', 'viewer'], label: 'Return manifest', ms: 10, title: 'Player decides bitrate' },
        { path: ['viewer', 'cdn'], label: 'GET segment_0', tone: 'ok', ms: 15, title: 'Fetch video chunks', detail: 'Future requests hit edge cache instantly.' }
      ]
    }
  ]
});

const Lld = lane([
  { label: 'CLIENTS', nodes: [{ id: 'client', label: 'Client', kind: 'client' }, { id: 'settle', label: 'Bank / PSP', kind: 'client' }] },
  { label: 'SERVICE', nodes: [{ id: 'api', label: 'Ledger API', sub: 'idempotent' }, { id: 'recon', label: 'Reconciler', sub: 'audit mismatches' }] },
  { label: 'STATE', nodes: [{ id: 'db', label: 'Journal DB', sub: 'immutable entries', kind: 'db' }] },
  { label: 'DERIVED', nodes: [{ id: 'proj', label: 'Projection', sub: 'materialized balance' }] },
]);
defineFlow('sd-flow-ledger', {
  title: 'Payment Ledger',
  hint: 'Trace immutable double-entry accounting',
  zones: Lld.zones,
  nodes: Lld.nodes,
  edges: [
    ['client', 'api'],
    ['api', 'db'],
    ['db', 'proj', { async: true }],
    ['settle', 'recon'],
    ['recon', 'db']
  ],
  scenarios: [
    {
      id: 'transfer', name: 'Internal Transfer',
      summary: 'A transfer atomically debits and credits inside the immutable journal.',
      steps: [
        { path: ['client', 'api'], label: 'POST /transfer', ms: 10, title: 'Initiate Transfer', detail: 'Includes idempotency key.' },
        { at: 'api', badge: 'lock accounts', ms: 2, title: 'Check funds', detail: 'Verify Sender has available balance.' },
        { path: ['api', 'db'], label: 'INSERT debit/credit', ms: 5, title: 'Double Entry', detail: 'Write both lines atomically in a single transaction.' },
        { path: ['api', 'client'], label: '201 Created', tone: 'ok', ms: 2, title: 'Transfer Complete' },
        { path: ['db', 'proj'], label: 'Emit CDC', async: true, ms: 8, title: 'Update Balances', detail: 'Projection worker updates the fast-read balance cache.' }
      ]
    },
    {
      id: 'reconcile', name: 'Settlement Recon',
      summary: 'External bank files are treated as evidence, not direct edits to balances.',
      steps: [
        { path: ['settle', 'recon'], label: 'Upload file', ms: 100, title: 'T+1 Settlement File' },
        { at: 'recon', badge: 'diffing', ms: 50, title: 'Match records', detail: 'Compare processor records against our immutable journal.' },
        { path: ['recon', 'db'], label: 'INSERT correction', tone: 'warn', ms: 15, title: 'Post Adjustments', detail: 'Mismatches create new correcting entries, never edit past ones.' }
      ]
    }
  ]
});
const Lcc = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Client', kind: 'client' }] },
  { label: 'APP', nodes: [{ id: 'api', label: 'App Node', sub: 'hash ring & stampede lock' }] },
  { label: 'CACHE RING', nodes: [{ id: 'node_a', label: 'Cache Node A', sub: 'shard 1', kind: 'cache' }, { id: 'node_b', label: 'Cache Node B', sub: 'shard 2', kind: 'cache' }] },
  { label: 'ORIGIN', nodes: [{ id: 'db', label: 'Database', sub: 'origin', kind: 'db' }] },
]);
defineFlow('sd-flow-cache', {
  title: 'Distributed Cache',
  hint: 'Trace consistent hashing and stampede protection',
  zones: Lcc.zones,
  nodes: Lcc.nodes,
  edges: [
    ['client', 'api'],
    ['api', 'node_a'],
    ['api', 'node_b'],
    ['api', 'db']
  ],
  scenarios: [
    {
      id: 'hash', name: 'Consistent Hashing',
      summary: 'A key is routed to a specific node based on its hash.',
      steps: [
        { path: ['client', 'api'], label: 'GET user_42', ms: 10, title: 'Request data' },
        { at: 'api', badge: 'hash(user_42)', ms: 2, title: 'Route key', detail: 'Consistent hashing points to Node A.' },
        { path: ['api', 'node_a'], label: 'GET user_42', ms: 5, title: 'Check cache' },
        { path: ['node_a', 'api'], label: 'MISS', tone: 'warn', ms: 2, title: 'Cache miss' },
        { path: ['api', 'db'], label: 'SELECT user_42', ms: 30, title: 'Fetch Origin' },
        { path: ['api', 'node_a'], label: 'SET user_42', tone: 'ok', ms: 5, title: 'Populate cache' }
      ]
    },
    {
      id: 'stampede', name: 'Stampede Protection',
      summary: 'When a popular key expires, only one request queries the database.',
      steps: [
        { path: ['client', 'api'], label: '1,000 reqs: GET popular_item', ms: 5, title: 'Thundering Herd' },
        { path: ['api', 'node_b'], label: 'GET popular_item', ms: 3, title: 'Check cache' },
        { path: ['node_b', 'api'], label: 'MISS', tone: 'warn', ms: 1, title: 'Cache expired' },
        { at: 'api', badge: 'acquire lock', tone: 'warn', ms: 2, title: 'Single-flight lock', detail: '999 requests wait on a local promise. Only 1 proceeds to DB.' },
        { path: ['api', 'db'], label: 'SELECT popular_item', ms: 30, title: 'Fetch Origin' },
        { path: ['api', 'node_b'], label: 'SET popular_item', tone: 'ok', ms: 5, title: 'Populate cache' },
        { path: ['api', 'client'], label: 'Resolve 1,000 responses', tone: 'ok', ms: 5, title: 'Fulfill all waiters' }
      ]
    }
  ]
});

const Lfl = lane([
  { label: 'CLIENT', nodes: [{ id: 'req', label: 'User Req', kind: 'client' }] },
  { label: 'APPLICATION', nodes: [{ id: 'app', label: 'Application', sub: 'SDK cache' }] },
  { label: 'DISTRIBUTION', nodes: [{ id: 'cdn', label: 'Distribution', sub: 'CDN / SSE stream' }] },
  { label: 'CONTROL PLANE', nodes: [{ id: 'api', label: 'Control Plane', sub: 'manage flags' }] },
  { label: 'STATE', nodes: [{ id: 'db', label: 'Rules DB', sub: 'PostgreSQL', kind: 'db' }] },
]);
defineFlow('sd-flow-flags', {
  title: 'Feature Flags',
  hint: 'Trace local evaluation and async updates',
  zones: Lfl.zones,
  nodes: Lfl.nodes,
  edges: [
    ['req', 'app'],
    ['app', 'cdn', { async: true }],
    ['cdn', 'api', { async: true }],
    ['api', 'db']
  ],
  scenarios: [
    {
      id: 'eval', name: 'Local Evaluation',
      summary: 'Flags are evaluated in memory on the hot path without network calls.',
      steps: [
        { path: ['req', 'app'], label: 'GET /feature', ms: 10, title: 'Request hits app' },
        { at: 'app', badge: 'eval(user, flag)', tone: 'ok', ms: 0, title: 'In-memory check', detail: 'SDK evaluates the cached rules locally in < 1ms.' },
        { path: ['app', 'req'], label: '200 OK (Feature ON)', tone: 'ok', ms: 5, title: 'Instant response' }
      ]
    },
    {
      id: 'update', name: 'Flag Update',
      summary: 'A developer turns on a flag, which fans out to all SDKs asynchronously.',
      steps: [
        { path: ['api', 'db'], label: 'UPDATE flag=ON', ms: 15, title: 'Dev edits flag' },
        { path: ['db', 'api'], label: 'CDC / Trigger', async: true, ms: 5, title: 'Notify Control Plane' },
        { path: ['api', 'cdn'], label: 'Publish snapshot', async: true, ms: 20, title: 'Push to Edge' },
        { path: ['cdn', 'app'], label: 'SSE / Stream Update', async: true, tone: 'ok', ms: 30, title: 'SDK syncs', detail: 'Local cache is updated. Future requests use the new rule.' }
      ]
    }
  ]
});

const Lrd = lane([
  { label: 'CLIENTS', nodes: [{ id: 'driver', label: 'Driver', kind: 'client' }, { id: 'rider', label: 'Rider', kind: 'client' }] },
  { label: 'DISPATCH', nodes: [{ id: 'api', label: 'Dispatch Svc', sub: 'match & offer' }] },
  { label: 'STATE', nodes: [{ id: 'geo', label: 'Geo Index', sub: 'ephemeral locations', kind: 'cache' }, { id: 'db', label: 'Trip DB', sub: 'transactional state', kind: 'db' }] },
]);
defineFlow('sd-flow-ride', {
  title: 'Ride Dispatch',
  hint: 'Trace location pings and assignment',
  zones: Lrd.zones,
  nodes: Lrd.nodes,
  edges: [
    ['driver', 'api'],
    ['api', 'geo'],
    ['rider', 'api'],
    ['api', 'db']
  ],
  scenarios: [
    {
      id: 'ping', name: 'Location Ping',
      summary: 'Drivers constantly update their location in an ephemeral, lossy index.',
      steps: [
        { path: ['driver', 'api'], label: 'POST /location (lat,lng)', async: true, ms: 30, title: 'Ping every 4s' },
        { path: ['api', 'geo'], label: 'SET geohash', async: true, ms: 5, title: 'Update Index', detail: 'This index uses a TTL. If a driver stops pinging, they drop off.' }
      ]
    },
    {
      id: 'dispatch', name: 'Request & Assign',
      summary: 'A rider requests a trip, candidates are ranked, and assignment is locked transactionally.',
      steps: [
        { path: ['rider', 'api'], label: 'POST /request', ms: 20, title: 'Rider needs a car' },
        { path: ['api', 'geo'], label: 'Search near cells', ms: 10, title: 'Candidate Discovery', detail: 'Find drivers near the pickup location.' },
        { at: 'api', badge: 'rank ETA', ms: 5, title: 'Rank candidates' },
        { path: ['api', 'driver'], label: 'Offer Trip', ms: 50, title: 'Send short lease offer' },
        { path: ['driver', 'api'], label: 'Accept', ms: 2000, title: 'Driver accepts' },
        { path: ['api', 'db'], label: 'UPDATE trip=ASSIGNED', tone: 'ok', ms: 10, title: 'Conditional Write', detail: 'WHERE status=PENDING. First driver to accept wins the lock.' }
      ]
    }
  ]
});

const Lgw = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Client', sub: 'tenant A', kind: 'client' }] },
  { label: 'GATEWAY', nodes: [{ id: 'gw', label: 'Gateway', sub: 'auth · route · deadline' }, { id: 'quota', label: 'Quota store', sub: 'per-tenant buckets', kind: 'cache' }] },
  { label: 'CONFIG', nodes: [{ id: 'policy', label: 'Route policy', sub: 'cached · versioned', kind: 'db' }] },
  { label: 'ORIGIN', nodes: [{ id: 'backend', label: 'Backend svc', sub: 're-authorizes' }] },
]);
defineFlow('sd-flow-gateway', {
  title: 'Multi-Tenant API Gateway',
  hint: 'Trace verified identity, quota, and a spoofed-header attempt',
  zones: Lgw.zones,
  nodes: Lgw.nodes,
  edges: [
    ['client', 'gw'],
    ['gw', 'quota'],
    ['gw', 'policy'],
    ['gw', 'backend']
  ],
  scenarios: [
    {
      id: 'auth', name: 'Verified request',
      summary: 'The gateway validates the token, checks quota, and forwards only the <b>verified</b> tenant claim — never a caller-supplied header.',
      steps: [
        { path: ['client', 'gw'], label: 'GET /orders', ms: 20, title: 'Request with bearer token' },
        { at: 'gw', badge: 'token ✓ → tenant A', tone: 'ok', ms: 2, title: 'Validate signature and expiry', detail: 'The verified principal/tenant claim is extracted here. Nothing the caller sent directly is trusted yet.' },
        { path: ['gw', 'quota', 'gw'], label: 'check bucket(A, route)', badgeAt: 'quota', badge: 'under limit', tone: 'ok', ms: 3, title: 'Per-tenant quota check' },
        { path: ['gw', 'policy', 'gw'], label: 'resolve route', ms: 2, title: 'Look up cached policy', detail: 'Config maps this path/version to the owning backend service.' },
        { path: ['gw', 'backend'], label: 'forward + verified claim', ms: 15, title: 'Verified claim propagated', detail: 'Header carries the claim the gateway extracted — not anything the client set.' },
        { at: 'backend', badge: 'reauthorize ✓', tone: 'ok', ms: 5, title: 'Backend re-checks resource access', detail: 'Defense in depth: gateway checks are necessary but not sufficient.' },
        { path: ['backend', 'gw', 'client'], label: '200 OK', tone: 'ok', ms: 20, title: 'Response returned' }
      ]
    },
    {
      id: 'spoof', name: 'Spoofed tenant header',
      summary: 'A caller sets <code>X-Tenant-Id: tenantB</code> by hand, hoping to read another tenant\'s data.',
      steps: [
        { path: ['client', 'gw'], label: 'GET /orders  X-Tenant-Id: tenantB', ms: 20, title: 'Forged header included' },
        { at: 'gw', badge: 'token ✓ → tenant A', tone: 'ok', ms: 2, title: 'Verified claim still says tenant A', detail: 'The header is simply ignored — tenant scope only ever comes from the validated token.' },
        { path: ['gw', 'backend'], label: 'forward + verified claim (A)', tone: 'ok', ms: 15, title: 'Real tenant forwarded', detail: 'The backend scopes every query by this claim, so the forged header never reaches the data layer.' },
        { path: ['backend', 'gw', 'client'], label: '200 OK (tenant A data only)', tone: 'ok', ms: 20, title: 'No cross-tenant leak' }
      ]
    },
    {
      id: 'spike', name: 'Noisy-neighbor spike',
      summary: 'Tenant A spikes traffic 100×. Its own bucket throttles it; every other tenant is unaffected.',
      steps: [
        { path: ['client', 'gw'], label: 'burst of requests', ms: 15, title: 'Tenant A floods the route' },
        { path: ['gw', 'quota', 'gw'], label: 'check bucket(A, route)', badgeAt: 'quota', badge: 'exhausted', tone: 'err', ms: 3, title: 'Tenant A\'s bucket is empty' },
        { at: 'gw', badge: '429 Too Many Requests', tone: 'err', ms: 1, title: 'Rejected before touching the backend', detail: 'Shared backend capacity, and every other tenant\'s bucket, is untouched.' },
        { path: ['gw', 'client'], label: '429', tone: 'err', ms: 10, title: 'Tenant A backs off' }
      ]
    }
  ]
});

const Lsf = lane([
  { label: 'APP', nodes: [{ id: 'app', label: 'App server', sub: 'ID library' }] },
  { label: 'COORDINATION · STATE', nodes: [{ id: 'coord', label: 'etcd / ZooKeeper', sub: 'worker-ID lease', kind: 'db' }, { id: 'db', label: 'Database', sub: 'BIGINT primary key', kind: 'db' }] },
]);
defineFlow('sd-flow-snowflake', {
  title: 'Unique ID Generator',
  hint: 'Trace in-process generation, a worker-ID lease, and a clock rollback',
  zones: Lsf.zones,
  nodes: Lsf.nodes,
  edges: [
    ['app', 'coord'],
    ['app', 'db']
  ],
  scenarios: [
    {
      id: 'lease', name: 'Startup: lease a worker ID',
      summary: 'Coordination happens <b>once per process</b>, on the startup path only — never on the hot path.',
      steps: [
        { path: ['app', 'coord'], label: 'lease request', ms: 4, title: 'Process asks for a free worker ID' },
        { path: ['coord', 'app'], label: 'worker = 17, TTL 30s', tone: 'ok', ms: 3, title: 'Lease granted', detail: 'Renewed every 10s. If it cannot be renewed, this process stops generating before the TTL expires.' },
        { at: 'app', badge: 'ready', tone: 'ok', ms: 0, title: 'Generator is now safe to use', detail: 'No other process can hold worker 17 while this lease is live.' }
      ]
    },
    {
      id: 'generate', name: 'Generate an ID (hot path)',
      summary: 'No network hop, no coordination — well under 1 µs per ID.',
      steps: [
        { at: 'app', badge: 'now = 41-bit ms', ms: 0, title: 'Read local clock' },
        { at: 'app', badge: 'seq = (seq+1) & 4095', ms: 0, title: 'Bump the per-ms sequence', detail: '4,096 IDs per millisecond per generator before it has to wait for the next tick.' },
        { at: 'app', badge: 'id = ts·dc·worker·seq', tone: 'ok', ms: 0, title: 'Pack the 64-bit ID', detail: 'timestamp(41) | datacenter(5) | worker(5) | sequence(12). k-sortable by construction.' },
        { path: ['app', 'db'], label: 'INSERT (id=…)', tone: 'ok', ms: 3, title: 'ID used as the primary key', detail: 'Time-ordered IDs keep B-tree inserts at the right-hand edge — few page splits.' }
      ]
    },
    {
      id: 'rollback', name: 'Clock moves backwards',
      summary: 'NTP steps the clock back 5ms. Generating anyway could duplicate an already-issued ID.',
      steps: [
        { at: 'app', badge: 'now (T-5) < lastTs (T)', tone: 'warn', ms: 0, title: 'Clock regression detected' },
        { at: 'app', badge: 'blocking…', tone: 'warn', ms: 5, title: 'Generator waits', detail: 'A small regression (a few ms) blocks until the clock passes lastTs. A large regression (> 1s) instead refuses and pages on-call.' },
        { at: 'app', badge: 'now ≥ lastTs, resume', tone: 'ok', ms: 0, title: 'Generation resumes safely', detail: 'No duplicate was ever issued — the alternative (generating during the regression) risks reusing (timestamp, worker, sequence).' }
      ]
    }
  ]
});

const Ldy = lane([
  { label: 'CLIENT', nodes: [{ id: 'client', label: 'Client', kind: 'client' }] },
  { label: 'COORDINATOR', nodes: [{ id: 'coord', label: 'Coordinator', sub: 'any node' }] },
  { label: 'REPLICAS (N=3)', nodes: [{ id: 'nodeA', label: 'Replica A', kind: 'db' }, { id: 'nodeB', label: 'Replica B', kind: 'db' }, { id: 'nodeC', label: 'Replica C', kind: 'db' }] },
  { label: 'FAILOVER', nodes: [{ id: 'standin', label: 'Stand-in node', sub: 'holds a hint', kind: 'db' }] },
]);
defineFlow('sd-flow-dynamo', {
  title: 'Distributed Key-Value Store',
  hint: 'Trace a quorum write, a sloppy-quorum failover, and conflicting reads',
  zones: Ldy.zones,
  nodes: Ldy.nodes,
  edges: [
    ['client', 'coord'],
    ['coord', 'nodeA'], ['coord', 'nodeB'], ['coord', 'nodeC'],
    ['coord', 'standin']
  ],
  scenarios: [
    {
      id: 'write', name: 'Quorum write (W=2)',
      summary: 'The coordinator writes to all N=3 replicas in parallel and returns once W=2 acknowledge.',
      steps: [
        { path: ['client', 'coord'], label: 'PUT key, value', ms: 5, title: 'Client sends a write' },
        { path: ['coord', 'nodeA'], label: 'PUT', ms: 3, title: 'Sent to replica A' },
        { path: ['coord', 'nodeB'], label: 'PUT', ms: 3, title: 'Sent to replica B' },
        { path: ['coord', 'nodeC'], label: 'PUT', ms: 3, title: 'Sent to replica C' },
        { at: 'coord', badge: '2 of 3 acked', tone: 'ok', ms: 2, title: 'W=2 satisfied', detail: 'The coordinator does not wait for the third — it will catch up via hinted handoff or read repair.' },
        { path: ['coord', 'client'], label: 'ok', tone: 'ok', ms: 4, title: 'Write acknowledged' }
      ]
    },
    {
      id: 'sloppy', name: 'Replica down: sloppy quorum',
      summary: 'Replica C is unreachable. A stand-in accepts the write with a hint so the write stays available.',
      down: ['nodeC'],
      steps: [
        { path: ['client', 'coord'], label: 'PUT key, value', ms: 5, title: 'Client sends a write' },
        { path: ['coord', 'nodeA'], label: 'PUT', tone: 'ok', ms: 3, title: 'Replica A acks' },
        { path: ['coord', 'nodeB'], label: 'PUT', tone: 'ok', ms: 3, title: 'Replica B acks' },
        { path: ['coord', 'standin'], label: 'PUT + hint: "belongs to C"', tone: 'warn', ms: 4, title: 'Stand-in accepts on C\'s behalf', detail: 'Forwards the data to C once it recovers. This keeps writes available during the failure, at the cost of weakening R+W>N until the hint replays.' },
        { path: ['coord', 'client'], label: 'ok', tone: 'ok', ms: 4, title: 'Write still succeeds' }
      ]
    },
    {
      id: 'conflict', name: 'Concurrent writes, conflicting read',
      summary: 'Two coordinators accepted concurrent writes during a partition. A read now sees siblings.',
      steps: [
        { path: ['client', 'coord'], label: 'GET key', ms: 5, title: 'Client reads' },
        { path: ['coord', 'nodeA'], label: 'GET', ms: 3, title: 'Read from replica A' },
        { path: ['coord', 'nodeB'], label: 'GET', ms: 3, title: 'Read from replica B' },
        { at: 'coord', badge: 'version vectors: concurrent', tone: 'warn', ms: 2, title: 'Neither version descends from the other', detail: 'A real conflict — not staleness. Both versions are returned with a context the client can merge.' },
        { path: ['coord', 'client'], label: '[v1, v2] + context', tone: 'warn', ms: 4, title: 'Client resolves the conflict', detail: 'Last-writer-wins, an application-level merge, or a CRDT — the store does not decide for the client.' }
      ]
    }
  ]
});

const Led = lane([
  { label: 'EDITORS', nodes: [{ id: 'a', label: 'Editor A', kind: 'client' }, { id: 'b', label: 'Editor B', kind: 'client' }] },
  { label: 'GATEWAY', nodes: [{ id: 'gw', label: 'Connection gateway', sub: 'holds WebSockets' }] },
  { label: 'OWNERSHIP', nodes: [{ id: 'sess', label: 'Session server', sub: 'owns doc · OT' }] },
  { label: 'STATE', nodes: [{ id: 'oplog', label: 'Operation log', sub: 'append per doc', kind: 'db' }] },
]);
defineFlow('sd-flow-editor', {
  title: 'Collaborative Document Editor',
  hint: 'Trace operational transform, reconnect/resync, and session failover',
  zones: Led.zones,
  nodes: Led.nodes,
  edges: [
    ['a', 'gw'], ['b', 'gw'],
    ['gw', 'sess'],
    ['sess', 'oplog']
  ],
  scenarios: [
    {
      id: 'ot', name: 'Concurrent edit',
      summary: 'A types locally with zero lag; the session server orders and transforms before broadcasting to B.',
      steps: [
        { at: 'a', badge: 'apply locally', tone: 'ok', ms: 0, title: 'A\'s keystroke applies instantly', detail: 'The user never waits on the network for their own typing.' },
        { path: ['a', 'gw', 'sess'], label: 'op @ base_revision=41', ms: 15, title: 'Op sent with base revision' },
        { path: ['sess', 'oplog'], label: 'append rev 42', tone: 'ok', ms: 3, title: 'Transformed and appended', detail: 'Transformed against every op committed after base_revision 41 — a single owner makes this ordering tractable.' },
        { path: ['sess', 'gw', 'a'], label: 'ack rev 42', tone: 'ok', ms: 15, title: 'Author acknowledged' },
        { path: ['sess', 'gw', 'b'], label: 'broadcast rev 42', tone: 'ok', ms: 15, title: 'Broadcast to other editors', detail: 'B transforms this against its own unacknowledged local ops before applying.' }
      ]
    },
    {
      id: 'resync', name: 'Reconnect and resync',
      summary: 'Editor A\'s connection drops mid-edit and comes back.',
      down: ['gw'],
      steps: [
        { at: 'a', badge: 'buffering ops offline', tone: 'warn', ms: 0, title: 'Connection lost', detail: 'Unacknowledged ops and base_revision are persisted locally (IndexedDB).' },
        { path: ['a', 'gw'], label: 'resync(last_revision=42)', tone: 'ok', ms: 20, title: 'Reconnects to a gateway', detail: 'Any gateway — they hold no per-document state.' },
        { path: ['gw', 'sess', 'gw', 'a'], label: 'ops since 42', tone: 'ok', ms: 20, title: 'Server sends what A missed' },
        { path: ['a', 'gw', 'sess'], label: 'replay buffered ops', tone: 'ok', ms: 20, title: 'Buffered ops transformed against everything that happened meanwhile', detail: 'op_id makes this idempotent even if some had actually already landed.' }
      ]
    },
    {
      id: 'failover', name: 'Session server dies',
      summary: 'The server owning this document crashes. Ownership must never split.',
      down: ['sess'],
      steps: [
        { at: 'sess', badge: 'lease expires', tone: 'err', ms: 0, title: 'Owner is gone', detail: 'No heartbeat renewal — the coordination service lets the lease lapse.' },
        { path: ['sess', 'oplog'], label: 'load snapshot + log', tone: 'warn', ms: 25, title: 'A new session server is elected', detail: 'It reconstructs the document from the latest snapshot plus subsequent ops — nothing acknowledged is lost.' },
        { path: ['a', 'gw'], label: 'resend unacknowledged ops', tone: 'ok', ms: 15, title: 'Clients resend', detail: 'Idempotent by op_id, so a race where the old owner half-committed an op cannot duplicate it.' },
        { at: 'gw', badge: 'conditional append fences stale owner', tone: 'ok', ms: 0, title: 'Split-brain is impossible', detail: 'Appends are conditional on revision = last + 1, so an old owner that somehow wakes back up gets rejected.' }
      ]
    }
  ]
});

const Lse = lane([
  { label: 'SEARCHER', nodes: [{ id: 'user', label: 'Searcher', kind: 'client' }] },
  { label: 'FRONTEND', nodes: [{ id: 'fe', label: 'Frontend', sub: 'query cache' }] },
  { label: 'MIXER', nodes: [{ id: 'root', label: 'Root / mixer' }] },
  { label: 'LEAF SHARDS', nodes: [{ id: 'leaf1', label: 'Leaf shard 1', kind: 'db' }, { id: 'leaf2', label: 'Leaf shard 2', kind: 'db' }, { id: 'leaf3', label: 'Leaf shard 3', kind: 'db' }] },
]);
defineFlow('sd-flow-searchengine', {
  title: 'Web Search Engine — Query Serving',
  hint: 'Trace a cache hit, a full fan-out, and a hedged request against a slow leaf',
  zones: Lse.zones,
  nodes: Lse.nodes,
  edges: [
    ['user', 'fe'], ['fe', 'root'],
    ['root', 'leaf1'], ['root', 'leaf2'], ['root', 'leaf3']
  ],
  scenarios: [
    {
      id: 'cachehit', name: 'Cache hit',
      summary: 'A popular query is served without touching a single leaf.',
      steps: [
        { path: ['user', 'fe'], label: 'GET q=weather', ms: 10, title: 'Query arrives at the frontend' },
        { at: 'fe', badge: 'cache HIT', tone: 'ok', ms: 1, title: 'Normalized query matches the result cache', detail: 'Popular queries follow a steep power law — a short-TTL cache absorbs a large share of traffic.' },
        { path: ['fe', 'user'], label: '10 results', tone: 'ok', ms: 8, title: 'Returned instantly' }
      ]
    },
    {
      id: 'fanout', name: 'Fan-out and merge',
      summary: 'A fresh query fans out to every leaf, and results are merged and re-ranked.',
      steps: [
        { path: ['user', 'fe'], label: 'GET q=rare phrase', ms: 10, title: 'Query arrives, cache miss' },
        { path: ['fe', 'root'], label: 'dispatch', ms: 5, title: 'Sent to the root / mixer' },
        { path: ['root', 'leaf1'], label: 'query', ms: 30, title: 'Fanned to shard 1' },
        { path: ['root', 'leaf2'], label: 'query', ms: 30, title: 'Fanned to shard 2' },
        { path: ['root', 'leaf3'], label: 'query', ms: 30, title: 'Fanned to shard 3' },
        { at: 'root', badge: 'k-way merge top-1000', tone: 'ok', ms: 10, title: 'Merge and re-rank', detail: 'A second-stage ranker applies expensive features to the merged top few hundred.' },
        { path: ['root', 'fe', 'user'], label: '10 results', tone: 'ok', ms: 15, title: 'Final page returned' }
      ]
    },
    {
      id: 'hedge', name: 'Slow leaf: hedged request',
      summary: 'With thousands of leaves per query, even a 0.1% chance of one being slow makes most queries slow — so the root hedges.',
      steps: [
        { path: ['root', 'leaf2'], label: 'query', ms: 30, title: 'Sent to shard 2\'s primary replica' },
        { at: 'root', badge: 'no response by p95', tone: 'warn', ms: 25, title: 'Deadline for the primary is exceeded' },
        { path: ['root', 'leaf3'], label: 'hedge: same query, other replica', tone: 'warn', ms: 15, title: 'Duplicate request sent to a replica', detail: 'Whichever response arrives first is used — the slow one is discarded when it eventually lands.' },
        { at: 'root', badge: 'first response wins', tone: 'ok', ms: 2, title: 'Query stays fast', detail: 'Partial results after a deadline are the fallback if even hedging does not return in time.' }
      ]
    }
  ]
});

const Lpl = lane([
  { label: 'CLIENTS', nodes: [{ id: 'user', label: 'User', kind: 'client' }, { id: 'owner', label: 'Business owner', kind: 'client' }] },
  { label: 'EDGE · API', nodes: [{ id: 'edge', label: 'Edge / CDN', sub: 'result cache', kind: 'cache' }, { id: 'api', label: 'Places API' }] },
  { label: 'SERVING', nodes: [{ id: 'gw', label: 'Search gateway' }] },
  { label: 'STATE', nodes: [{ id: 'index', label: 'S2 geo index', sub: 'in-memory', kind: 'cache' }, { id: 'db', label: 'Place store', sub: 'source of truth', kind: 'db' }] },
]);
defineFlow('sd-flow-places', {
  title: 'Nearby Places Search',
  hint: 'Trace a cached search, an S2 index scan, and an async place update',
  zones: Lpl.zones,
  nodes: Lpl.nodes,
  edges: [
    ['user', 'edge'], ['edge', 'gw'], ['gw', 'index'],
    ['owner', 'api'], ['api', 'db'],
    ['db', 'index', { async: true }]
  ],
  scenarios: [
    {
      id: 'hit', name: 'Cached search',
      summary: 'Many people search "coffee" near the same downtown blocks — the cache absorbs it.',
      steps: [
        { path: ['user', 'edge'], label: 'coffee near 37.78,-122.41', ms: 15, title: 'Search request' },
        { at: 'edge', badge: 'HIT (rounded cell, 1-5 min TTL)', tone: 'ok', ms: 1, title: 'Cache hit', detail: 'Location is rounded to a level-14 cell so nearby searchers share the same key.' },
        { path: ['edge', 'user'], label: 'results', tone: 'ok', ms: 15, title: 'Returned without touching the index' }
      ]
    },
    {
      id: 'miss', name: 'Cache miss: S2 covering scan',
      summary: 'Compute a small set of S2 cells covering the search circle, then range-scan each.',
      steps: [
        { path: ['user', 'edge', 'gw'], label: 'coffee near …', ms: 20, title: 'Cache miss, forwarded' },
        { at: 'gw', badge: 'S2 covering: 6 cells', ms: 2, title: 'Compute the covering', detail: 'A handful of cell-ID ranges cover the circle, naturally including neighbouring cells.' },
        { path: ['gw', 'index'], label: 'range-scan 6 cells', ms: 8, title: 'Scan sorted (cell_id, place) arrays', detail: 'The whole world\'s index fits in memory — this never touches the place store.' },
        { at: 'gw', badge: 'rank by distance, rating, open-now', ms: 5, title: 'Rank candidates' },
        { path: ['gw', 'edge', 'user'], label: '20 results', tone: 'ok', ms: 15, title: 'Returned and cached for the next searcher' }
      ]
    },
    {
      id: 'update', name: 'Owner update (async)',
      summary: 'Writes never touch the search path directly — the in-memory index catches up within seconds.',
      steps: [
        { path: ['owner', 'api'], label: 'PATCH hours', ms: 20, title: 'Owner updates business hours' },
        { path: ['api', 'db'], label: 'UPDATE + emit change event', tone: 'ok', ms: 8, title: 'Written to the source of truth' },
        { path: ['db', 'index'], label: 'CDC event', async: true, title: 'Geo indexer applies the change', detail: 'Freshness is seconds to minutes; a periodic full rebuild corrects any drift.' },
        { at: 'gw', badge: 'searches unaffected during update', tone: 'ok', ms: 0, title: 'Reads never wait on writes' }
      ]
    }
  ]
});

const Lac = lane([
  { label: 'USER', nodes: [{ id: 'user', label: 'User', kind: 'client' }] },
  { label: 'CLICK SERVER', nodes: [{ id: 'cs', label: 'Click server', sub: 'log + redirect' }] },
  { label: 'DURABLE LOG', nodes: [{ id: 'log', label: 'Event log', sub: 'Kafka', kind: 'queue' }] },
  { label: 'FAST PATH', nodes: [{ id: 'stream', label: 'Stream aggregator', sub: '1-min windows' }, { id: 'olap', label: 'Real-time OLAP', kind: 'db' }] },
  { label: 'EXACT PATH', nodes: [{ id: 'archive', label: 'Raw archive', sub: 'immutable', kind: 'db' }, { id: 'batch', label: 'Batch job', sub: 'dedup + fraud' }] },
]);
defineFlow('sd-flow-adclick', {
  title: 'Ad Click Aggregation',
  hint: 'Trace the non-blocking redirect, the streaming window, and batch billing',
  zones: Lac.zones,
  nodes: Lac.nodes,
  edges: [
    ['user', 'cs'], ['cs', 'log'],
    ['log', 'stream'], ['stream', 'olap'],
    ['log', 'archive'], ['archive', 'batch']
  ],
  scenarios: [
    {
      id: 'click', name: 'Click never waits on logging',
      summary: 'The redirect is the user-visible contract — the log write must never block it.',
      steps: [
        { path: ['user', 'cs'], label: 'GET /click?ad=42&sig=…', ms: 10, title: 'User clicks the ad' },
        { at: 'cs', badge: 'signature ✓', ms: 1, title: 'Verify the ad server\'s signature' },
        { path: ['cs', 'user'], label: '302 → advertiser', tone: 'ok', ms: 8, title: 'Redirected immediately', detail: 'The event write happens on a background path — it is buffered locally first.' },
        { path: ['cs', 'log'], label: 'ClickEvent', async: true, title: 'Event appended to the durable log', detail: 'If this were synchronous, a slow log would slow down every click.' }
      ]
    },
    {
      id: 'stream', name: 'Streaming aggregation (~1 min fresh)',
      summary: 'Dashboards and budget pacing read a fast, approximate path — corrected later.',
      steps: [
        { path: ['log', 'stream'], label: 'events keyed by ad_id', ms: 20, title: 'Stream job consumes the log' },
        { at: 'stream', badge: '1-min tumbling window (event time)', ms: 5, title: 'Aggregate by event time, not processing time', detail: 'A watermark fires the window about a minute after it closes.' },
        { path: ['stream', 'olap'], label: 'upsert (ad_id, window_start) = count', tone: 'ok', ms: 10, title: 'Idempotent absolute write', detail: 'Writing count += n would double-count on replay — this writes the full value for the window instead.' },
        { at: 'stream', badge: 'dashboards fresh ~1 min', tone: 'ok', ms: 0, title: 'Freshness target met' }
      ]
    },
    {
      id: 'billing', name: 'Batch reconciliation for billing',
      summary: 'Money reads from the immutable raw log, hours later, exact and reproducible.',
      steps: [
        { path: ['archive', 'batch'], label: 'read raw events', ms: 40, title: 'Batch job scans the archive' },
        { at: 'batch', badge: 'dedup by click_id, apply fraud rules', tone: 'ok', ms: 15, title: 'Global exact deduplication', detail: 'Replaying this job produces identical results — what auditors need.' },
        { at: 'batch', badge: 'compare vs streaming aggregates', ms: 5, title: 'Reconciliation check', detail: 'A discrepancy beyond ~0.5% is treated as a pipeline bug, not just late data.' },
        { at: 'batch', badge: 'billing finalized', tone: 'ok', ms: 0, title: 'Invoices generated after the close period', detail: 'Typically 48 hours, to include late events.' }
      ]
    }
  ]
});

const Ltr = lane([
  { label: 'EVENTS', nodes: [{ id: 'ev', label: 'Events', sub: 'views / uses', kind: 'client' }] },
  { label: 'LOG', nodes: [{ id: 'log', label: 'Event log', sub: 'by item_id', kind: 'queue' }] },
  { label: 'COUNTING', nodes: [{ id: 'counter', label: 'Counter worker', sub: 'sketch + heap' }, { id: 'store', label: 'Minute buckets', kind: 'cache' }] },
  { label: 'WINDOW', nodes: [{ id: 'merger', label: 'Window merger' }] },
  { label: 'RESULTS', nodes: [{ id: 'topk', label: 'Top-K results', kind: 'db' }] },
  { label: 'READERS', nodes: [{ id: 'client', label: 'Client', kind: 'client' }] },
]);
defineFlow('sd-flow-trending', {
  title: 'Top-K Trending',
  hint: 'Trace sketch counting, the sliding-window merge, and a cached read',
  zones: Ltr.zones,
  nodes: Ltr.nodes,
  edges: [
    ['ev', 'log'], ['log', 'counter'],
    ['counter', 'store'], ['store', 'merger'],
    ['merger', 'topk'], ['topk', 'client']
  ],
  scenarios: [
    {
      id: 'count', name: 'Per-minute counting',
      summary: 'Constant memory per slice, regardless of how many distinct items exist.',
      steps: [
        { path: ['ev', 'log'], label: 'view(item_9182)', ms: 5, title: 'Event produced' },
        { path: ['log', 'counter'], label: 'consume', ms: 5, title: 'Counter worker reads its partitions' },
        { at: 'counter', badge: 'sketch.add(item_9182)', ms: 0, title: 'Count-min sketch updated', detail: '~760 KB per sketch, independent of the number of distinct items — never undercounts.' },
        { at: 'counter', badge: 'heap: is it top-500 candidate?', ms: 0, title: 'Candidate heap keeps ~K×10 items', detail: 'Extra headroom above K absorbs estimation noise near the cut-off.' },
        { path: ['counter', 'store'], label: 'flush minute bucket', tone: 'ok', ms: 8, title: 'Sketch + heap persisted per minute' }
      ]
    },
    {
      id: 'window', name: 'Sliding-window merge',
      summary: 'The last hour = sum of the latest 60 minute buckets — one added, one subtracted, every minute.',
      steps: [
        { path: ['store', 'merger'], label: 'read latest 60 buckets', ms: 15, title: 'Merger sums the window' },
        { at: 'merger', badge: 'add newest, subtract oldest', ms: 3, title: 'Sketches merge by cell-wise addition', detail: 'Count-min sketches support subtraction of exactly what was added, which is what makes the sliding hop cheap.' },
        { at: 'merger', badge: 'union of candidate heaps → top K', tone: 'ok', ms: 5, title: 'Re-estimate and rank candidates', detail: 'An item can be moderately popular on every partition without leading any single one — union matters.' },
        { path: ['merger', 'topk'], label: 'publish top 50', tone: 'ok', ms: 5, title: 'Result published for the window' }
      ]
    },
    {
      id: 'read', name: 'Client read',
      summary: 'Reads are plain key-value lookups against precomputed results.',
      steps: [
        { path: ['client', 'topk'], label: 'GET /trending?window=1h', ms: 12, title: 'Client requests the list' },
        { path: ['topk', 'client'], label: 'items[] + generated_at', tone: 'ok', ms: 8, title: 'Served from precomputed results', detail: 'CDN-cacheable for 30-60 seconds — no aggregation happens on the read path.' }
      ]
    }
  ]
});

const Llb = lane([
  { label: 'SOURCE', nodes: [{ id: 'gs', label: 'Game server', sub: 'signed result', kind: 'client' }] },
  { label: 'WRITE PATH', nodes: [{ id: 'api', label: 'Score service' }, { id: 'reader', label: 'Leaderboard API' }] },
  { label: 'SOURCE OF TRUTH', nodes: [{ id: 'db', label: 'Score DB', sub: 'source of truth', kind: 'db' }] },
  { label: 'PROJECTION', nodes: [{ id: 'upd', label: 'Leaderboard updater' }] },
  { label: 'READ MODELS', nodes: [{ id: 'topset', label: 'Top-1000 set', kind: 'cache' }, { id: 'hist', label: 'Score histogram', kind: 'cache' }] },
]);
defineFlow('sd-flow-leaderboard', {
  title: 'Real-Time Leaderboard',
  hint: 'Trace a score submission, a top-100 read, and a long-tail rank estimate',
  zones: Llb.zones,
  nodes: Llb.nodes,
  edges: [
    ['gs', 'api'], ['api', 'db'],
    ['db', 'upd', { async: true }],
    ['upd', 'topset'], ['upd', 'hist'],
    ['reader', 'topset'], ['reader', 'hist']
  ],
  scenarios: [
    {
      id: 'submit', name: 'Score submission',
      summary: 'The database is the source of truth; sorted-set ranking structures are a rebuildable projection.',
      steps: [
        { path: ['gs', 'api'], label: 'signed match result', ms: 15, title: 'Server-authoritative result' },
        { at: 'api', badge: 'plausibility check ✓', ms: 3, title: 'Anti-cheat validation', detail: 'Only game servers are trusted — never a client-reported score.' },
        { path: ['api', 'db'], label: 'INSERT (idempotent by match_id)', tone: 'ok', ms: 8, title: 'Durable write' },
        { path: ['db', 'upd'], label: 'CDC / outbox', async: true, title: 'Ranking structures update asynchronously', detail: 'Seconds of lag — if Redis is lost entirely, these rebuild from this table.' }
      ]
    },
    {
      id: 'top', name: 'Top-100 read',
      summary: 'The same list for everyone — caches and answers from the global top set perfectly.',
      steps: [
        { path: ['reader', 'topset'], label: 'ZREVRANGE 0 99', ms: 2, title: 'Read the global top-1000 set', detail: 'Exact ranks for the leaderboard\'s head come straight from here.' },
        { at: 'reader', badge: 'served, cacheable', tone: 'ok', ms: 1, title: 'Top 100 returned' }
      ]
    },
    {
      id: 'longtail', name: 'My rank (long tail)',
      summary: 'For the millions outside the top set, an exact rank would mean fanning out to every shard — instead, a histogram estimates it.',
      steps: [
        { path: ['reader', 'topset'], label: 'score ≥ top-set min?', badgeAt: 'topset', badge: 'no', tone: 'warn', ms: 2, title: 'Not in the exact top set' },
        { path: ['reader', 'hist'], label: 'bucket lookup', ms: 2, title: 'Estimate from the score histogram', detail: 'rank ≈ players in higher buckets + interpolated position — accurate to well under 1% for the tail.' },
        { path: ['hist', 'reader'], label: 'rank ≈ 1,204,000', tone: 'warn', ms: 1, title: 'Approximate rank returned', detail: 'Flagged rank_is_approx: true — which is what players actually look at.' }
      ]
    }
  ]
});

const Lllm = lane([
  { label: 'CLIENT', nodes: [{ id: 'ui', label: 'Mail client', sub: 'SSE stream', kind: 'client' }] },
  { label: 'GATEWAY', nodes: [{ id: 'gw', label: 'AI gateway', sub: 'auth · quota' }] },
  { label: 'ORCHESTRATION', nodes: [{ id: 'orch', label: 'Orchestrator', sub: 'context + guard' }, { id: 'ret', label: 'Mailbox index', sub: 'ACL-filtered', kind: 'db' }] },
  { label: 'ROUTING', nodes: [{ id: 'router', label: 'Model router' }] },
  { label: 'MODEL POOLS', nodes: [{ id: 'small', label: 'Small model pool' }, { id: 'large', label: 'Large model pool' }] },
]);
defineFlow('sd-flow-llm', {
  title: 'LLM Assistant Feature',
  hint: 'Trace a cheap small-model answer, escalation, and a saturated-pool fallback',
  zones: Lllm.zones,
  nodes: Lllm.nodes,
  edges: [
    ['ui', 'gw'], ['gw', 'orch'],
    ['orch', 'ret'], ['orch', 'router'],
    ['router', 'small'], ['router', 'large']
  ],
  scenarios: [
    {
      id: 'fast', name: 'Fast path: small model',
      summary: 'Cheap checks and retrieval happen before any GPU is touched; simple tasks route to the small model.',
      steps: [
        { path: ['ui', 'gw'], label: 'POST /assist {task: summarize}', ms: 20, title: 'Request opens an SSE stream' },
        { at: 'gw', badge: 'quota ✓ rate limit ✓', ms: 3, title: 'Checked before any model is involved' },
        { path: ['gw', 'orch'], label: 'forward', ms: 5, title: 'Orchestrator builds the prompt' },
        { path: ['orch', 'ret'], label: 'retrieve relevant messages', ms: 25, title: 'ACL-filtered retrieval', detail: 'A few relevant messages, not the whole mailbox — this is the biggest lever on prompt tokens.' },
        { path: ['orch', 'router'], label: 'route(short thread)', ms: 2, title: 'Simple task → small model', detail: 'Routing most traffic to a model 5× cheaper roughly halves cost.' },
        { path: ['router', 'small'], label: 'generate (prefix-cached)', tone: 'ok', ms: 180, title: 'Streamed tokens', detail: 'The shared system-prompt prefix is cached, removing that prefill cost.' },
        { path: ['small', 'router', 'orch', 'gw', 'ui'], label: 'token stream + citation', tone: 'ok', ms: 30, title: 'Response streamed to the client' }
      ]
    },
    {
      id: 'escalate', name: 'Escalation to the large model',
      summary: 'A long thread or a low-confidence draft escalates, trading cost for quality.',
      steps: [
        { path: ['orch', 'router'], label: 'route(long thread, complex ask)', ms: 2, title: 'Router evaluates task complexity' },
        { at: 'router', badge: 'escalate', tone: 'warn', ms: 1, title: 'Small-model confidence too low / task too complex' },
        { path: ['router', 'large'], label: 'generate', tone: 'ok', ms: 400, title: 'Large model pool handles it', detail: 'Slower and more expensive, reserved for where it changes the answer.' }
      ]
    },
    {
      id: 'saturated', name: 'Large pool saturated',
      summary: 'Core email must never break because the model tier is overloaded.',
      down: ['large'],
      steps: [
        { path: ['orch', 'router'], label: 'route(complex ask)', ms: 2, title: 'Would normally escalate' },
        { at: 'router', badge: 'large pool: queue > deadline', tone: 'err', ms: 3, title: 'Saturation detected' },
        { path: ['router', 'small'], label: 'fallback: small model', tone: 'warn', ms: 150, title: 'Degrade gracefully', detail: 'Served with a lower-quality badge rather than making the user wait indefinitely.' },
        { path: ['small', 'router', 'orch', 'gw', 'ui'], label: 'response (lower quality)', tone: 'warn', ms: 25, title: 'User still gets an answer' }
      ]
    }
  ]
});
