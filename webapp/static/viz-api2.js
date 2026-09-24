/* ============================================================================
   API module labs, part 2 — protocol-accurate REST and GraphQL visualizations.
   Requires viz.js (labApi, D helpers) and viz-sd.js (topo(), drawSysNode,
   fmtMs). Overrides the older, simpler 'api-rest' / 'api-graphql' entries
   registered by viz-api.js, since LABS is a Map keyed by lab id.
   ========================================================================= */
'use strict';

/* ===================================================== 1 · REST lifecycle == */
defineLab('api-rest', {
  title: 'REST request lifecycle: methods, idempotency, caching',
  hint: 'Pick a method and send it against the same resource. Watch the status code, the ETag cache, and what happens when you repeat the exact same call.',
  mount(L) {
    const c = L.canvas(w => Math.min(320, Math.max(260, w * .46)));
    const T = topo(c);
    T.node('client', .1, .34, 'Client', { kind: 'client', w: 78 });
    T.node('api', .5, .34, 'API server', { w: 110 });
    T.node('db', .89, .34, 'Database', { kind: 'db', w: 84, h: 50 });
    T.edge('client', 'api');
    T.edge('api', 'db');

    const s = { method: 'GET', netMs: 60, exists: true, version: 1, done: false, etagKnown: null, created: 0, lats: [], last: null, queue: 0, gap: 0 };

    L.seg('method', [['GET', 'GET'], ['POST', 'POST'], ['PATCH', 'PATCH'], ['DELETE', 'DELETE']], s.method, v => { s.method = v; });
    L.slider('network latency', { min: 10, max: 200, step: 10, value: s.netMs, fmt: v => `${v} ms` }, v => { s.netMs = v; });
    const run = L.loop(dt => {
      if (s.queue > 0 && (s.gap -= dt) <= 0) { s.queue--; s.gap = .3; fire(); }
      T.step(dt); L.redraw();
      if (!T.busy() && s.queue <= 0) return false;
    });
    L.button('Send request', () => { fire(); run.start(); }, 'primary');
    L.button('Send 5×', () => { s.queue = 5; run.start(); });
    L.button('Reset resource', () => {
      s.exists = true; s.version = 1; s.done = false; s.etagKnown = null; s.created = 0; s.lats = []; s.last = null;
      paintNodes(); update();
    });

    function methodColor(P, m) { return m === 'GET' ? P.accent : m === 'POST' ? P.series[1] : m === 'PATCH' ? P.series[2] : P.series[3]; }

    function fire() {
      const m = s.method;
      let path, status, note, cache = '—';
      if (m === 'GET') {
        if (s.etagKnown === s.version && s.exists) {
          path = ['client', 'api', 'client']; status = 304; cache = 'hit';
          note = `304 Not Modified: the client already holds ETag "v${s.version}" via If-None-Match, and it still matches. No body is sent, and the database is never touched.`;
        } else {
          path = ['client', 'api', 'db', 'api', 'client']; cache = 'miss';
          status = s.exists ? 200 : 404;
          if (s.exists) { s.etagKnown = s.version; note = `200 OK: a fresh copy is fetched from the database and tagged ETag "v${s.version}". The client now caches it and will send If-None-Match next time.`; }
          else note = '404 Not Found: no such resource — GET is safe, so asking again costs nothing but a wasted round trip.';
        }
      } else if (m === 'POST') {
        path = ['client', 'api', 'db', 'api', 'client'];
        s.created++; s.exists = true; s.version++; s.etagKnown = null;
        status = 201;
        note = `201 Created (Location: /tasks/${s.created}). POST is <b>not</b> idempotent — every call inserts a brand-new row. This is creation #${s.created} from identical requests.`;
      } else if (m === 'PATCH') {
        if (!s.exists) { path = ['client', 'api', 'client']; status = 404; note = '404 Not Found: nothing to patch — it was deleted.'; }
        else {
          path = ['client', 'api', 'db', 'api', 'client'];
          s.done = !s.done; s.version++; s.etagKnown = null;
          status = 200;
          note = `200 OK: this PATCH flips "done" to <b>${s.done}</b>. Resend the exact same request and it flips again. The REST spec marks PATCH idempotent ❌ for exactly this reason — unlike PUT and DELETE, whether a given PATCH is safe to repeat depends on what it does.`;
        }
      } else { // DELETE
        if (s.exists) {
          path = ['client', 'api', 'db', 'api', 'client'];
          s.exists = false; s.version++; s.etagKnown = null;
          status = 204;
          note = '204 No Content: resource removed. DELETE is idempotent by contract.';
        } else {
          path = ['client', 'api', 'client'];
          status = 404;
          note = '404 Not Found: already gone. Still idempotent — the <b>end state</b> (no resource) is identical to the first call, even though the status code changed from 204 to 404. Idempotency is about server state, not identical responses.';
        }
      }
      const throughDb = path.length > 3;
      const segs = throughDb
        ? [['client → api', s.netMs / 2], ['db query', 8], ['api → client', s.netMs / 2]]
        : [['client → api', s.netMs / 2], ['api → client (no DB hit)', s.netMs / 2]];
      const ms = segs.reduce((a, [, x]) => a + x, 0);
      const col = status >= 400 ? L.P.err : methodColor(L.P, m);
      T.send(path, {
        speed: 3.4, color: col, hop: id => T.pulse(id),
        end: () => { s.lats.push(ms); s.last = { method: m, status, ms, cache, note, segs }; paintNodes(); update(); L.redraw(); },
      });
    }

    function paintNodes() {
      T.nodes.db.sub = s.exists ? `v${s.version}${s.done ? ' · done' : ''}` : 'deleted';
      T.nodes.api.sub = s.last ? `last: ${s.last.status}` : '';
    }

    function update() {
      const l = s.last;
      L.stats([
        ['status', l ? String(l.status) : '—', l ? (l.status < 300 || l.status === 304 ? 'ok' : l.status >= 400 ? 'err' : '') : ''],
        ['latency', l ? fmtMs(l.ms) : '—'],
        ['cache', l ? l.cache : '—'],
        ['resource', s.exists ? `v${s.version}` : 'deleted'],
        s.created ? ['created', s.created] : null,
        ['requests sent', s.lats.length],
      ]);
      L.insight(!l
        ? '<b>Press "Send request".</b> Try GET twice in a row (304 on the second), then POST a few times (each creates a new row), then DELETE twice (idempotent, but the second response differs).'
        : `<b>${l.method} → ${l.status} · ${fmtMs(l.ms)}.</b> ${l.note}`);
    }

    L.draw = P => {
      c.clear();
      const { ctx } = c;
      T.draw(ctx, P);
      const l = s.last;
      if (l && l.segs.length) {
        const y = c.h - 18, total = l.segs.reduce((a, [, ms]) => a + ms, 0) || 1, x0 = 12, W = c.w - 24;
        let x = x0;
        l.segs.forEach(([lbl, ms], i) => {
          const w = Math.max(3, ms / total * W);
          ctx.fillStyle = P.alpha(P.series[i % P.series.length], .8);
          D.rrect(ctx, x, y - 8, w - 2, 14, 4); ctx.fill();
          if (w > 78) D.text(ctx, `${lbl} ${Math.round(ms)}ms`, x + 5, y - 1, { color: P.surface, size: 9.5, weight: 650 });
          x += w;
        });
        D.text(ctx, 'one-way latency breakdown', x0, y - 16, { color: P.faint, size: 10 });
      }
    };
    paintNodes();
    update();
  },
});

/* ============================================ 2 · GraphQL vs REST fan-out == */
defineLab('api-graphql', {
  title: 'One round trip vs many: GraphQL vs REST, and N+1',
  hint: 'Fetch the same screen — post titles plus author names — as REST (one call per resource) or GraphQL (one call, walked server-side). Toggle DataLoader to collapse N+1 backend calls into one batch.',
  mount(L) {
    const c = L.canvas(w => Math.min(360, Math.max(300, w * .52)));
    const T = topo(c);
    T.node('client', .1, .3, 'Client', { kind: 'client', w: 78 });
    T.node('api', .5, .3, 'API server', { w: 116 });
    T.node('db', .89, .3, 'Database', { kind: 'db', w: 84, h: 50 });
    T.edge('client', 'api');
    T.edge('api', 'db');

    const s = { mode: 'rest', dataLoader: false, n: 5, netMs: 90, dbMs: 8, last: null };
    let busy = false;

    L.seg('data need', [['rest', 'REST (N round trips)'], ['graphql', 'GraphQL (1 round trip)']], s.mode, v => { s.mode = v; T.nodes.api.sub = v === 'rest' ? 'REST API' : 'GraphQL server'; L.redraw(); });
    L.slider('posts on screen', { min: 3, max: 8, step: 1, value: s.n, fmt: v => `${v} posts (3 authors)` }, v => { s.n = v; });
    L.toggle('DataLoader batching (GraphQL only)', s.dataLoader, v => { s.dataLoader = v; });
    L.slider('network latency', { min: 20, max: 250, step: 10, value: s.netMs, fmt: v => `${v} ms` }, v => { s.netMs = v; });
    const run = L.loop(dt => { T.step(dt); L.redraw(); if (!T.busy() && !busy) return false; });
    L.button('Fetch screen data', () => { if (!busy) { animate(); run.start(); } }, 'primary');
    L.button('Reset stats', () => { s.last = null; update(); });

    function computeResult() {
      const n = s.n;
      const posts = Array.from({ length: n }, (_, i) => ({ id: i + 1, authorId: (i % 3) + 1 }));
      const uniqueAuthors = new Set(posts.map(p => p.authorId)).size;
      let roundTrips, dbCalls, payload, tripLabels, dbLabels;
      if (s.mode === 'rest') {
        roundTrips = 1 + n;
        dbCalls = 1 + n;
        payload = 32 * n + 210 * n; // list rows (id+title) + N full user objects, over-fetched, never deduped
        tripLabels = ['GET /posts', ...posts.map(p => `GET /users/${p.authorId}`)];
        dbLabels = ['SELECT posts', ...posts.map(p => `SELECT user ${p.authorId}`)];
      } else {
        roundTrips = 1;
        payload = 34 * n; // title + author.name only, exactly what was asked for
        tripLabels = ['POST /graphql (1 round trip)'];
        if (s.dataLoader) {
          dbCalls = 2;
          const uniq = [...new Set(posts.map(p => p.authorId))];
          dbLabels = ['SELECT posts', `SELECT users WHERE id IN (${uniq.join(',')})`];
        } else {
          dbCalls = 1 + n;
          dbLabels = ['SELECT posts', ...posts.map(p => `Post.author(${p.id}) → SELECT user ${p.authorId}`)];
        }
      }
      const ms = roundTrips * s.netMs + dbCalls * s.dbMs;
      return { mode: s.mode, dataLoader: s.dataLoader, n, uniqueAuthors, roundTrips, dbCalls, payload, ms, tripLabels, dbLabels };
    }

    function animate() {
      busy = true;
      const n = s.n;
      const posts = Array.from({ length: n }, (_, i) => ({ id: i + 1, authorId: (i % 3) + 1 }));
      const tripColor = s.mode === 'rest' ? L.P.series[3] : L.P.accent;

      const finish = () => { busy = false; s.last = computeResult(); update(); L.redraw(); };

      if (s.mode === 'rest') {
        let i = 0;
        const steps = n + 1;
        const doStep = () => {
          if (i >= steps) { finish(); return; }
          i++;
          T.send(['client', 'api', 'db', 'api', 'client'], { speed: 3.6, color: tripColor, hop: id => T.pulse(id), end: doStep });
        };
        doStep();
      } else {
        T.send(['client', 'api'], {
          speed: 3.6, color: tripColor, hop: id => T.pulse(id), end: () => {
            const dbTotal = s.dataLoader ? 2 : 1 + n; // posts query + (batched authors) or (one author call per post)
            let j = 0;
            const doDb = () => {
              if (j >= dbTotal) { T.send(['api', 'client'], { speed: 3.6, color: tripColor, hop: id => T.pulse(id), end: finish }); return; }
              const batched = s.dataLoader && j === 1;
              j++;
              T.send(['api', 'db', 'api'], { speed: 4.4, color: batched ? L.P.ok : L.P.series[1], hop: id => T.pulse(id), end: doDb });
            };
            doDb();
          },
        });
      }
    }

    function insightFor(l) {
      const kb = (l.payload / 1024).toFixed(2);
      if (l.mode === 'rest') {
        return `<b>${l.roundTrips} round trips, ${kb} KB.</b> One call lists the posts, then one more call <i>per post</i> fetches its author — even though only ${l.uniqueAuthors} distinct authors exist among ${l.n} posts, nothing is deduped. Each <code>GET /users/:id</code> also returns the full user object (email, address, history) though the screen only needed a name — REST's over-fetching, on top of the under-fetching that forced the extra round trips.`;
      }
      if (!l.dataLoader) {
        return `<b>1 round trip, but ${l.dbCalls} backend calls, ${kb} KB.</b> The client got exactly the fields it asked for in a single request — no over-fetching. But the naive <code>Post.author</code> resolver still runs once per post, so N+1 didn't disappear, it just moved server-side where the client can't see it, and it's still ${l.dbCalls - 1} extra queries.`;
      }
      return `<b>1 round trip, ${l.dbCalls} backend calls, ${kb} KB — constant, regardless of post count.</b> DataLoader collects every <code>.load(authorId)</code> call made in this tick, dedupes the ${l.uniqueAuthors} distinct authors among ${l.n} posts, and fires one <code>WHERE id IN (...)</code> query. N+1 collapses to a flat 2 backend calls no matter how many posts are on screen.`;
    }

    function update() {
      const l = s.last;
      L.stats([
        ['mode', l ? (l.mode === 'rest' ? 'REST' : 'GraphQL') : '—'],
        ['round trips', l ? l.roundTrips : '—', l ? (l.roundTrips > 1 ? 'err' : 'ok') : ''],
        ['backend / DB calls', l ? l.dbCalls : '—', l ? (l.dbCalls > 2 ? 'err' : 'ok') : ''],
        ['payload', l ? `${(l.payload / 1024).toFixed(2)} KB` : '—'],
        ['latency', l ? fmtMs(l.ms) : '—'],
      ]);
      L.insight(!l
        ? '<b>Press "Fetch screen data".</b> Compare REST\'s round trips against GraphQL\'s one call, then flip DataLoader on to collapse GraphQL\'s own N+1 backend calls.'
        : insightFor(l));
    }

    function drawRow(ctx, P, labels, y, color, caption, batchedIdx = -1) {
      const x0 = 12, W = c.w - 24, n = labels.length, gap = 3;
      const w = Math.max(3, (W - (n - 1) * gap) / n);
      let x = x0;
      labels.forEach((lbl, i) => {
        ctx.fillStyle = i === batchedIdx ? P.alpha('ok', .85) : P.alpha(color, .75);
        D.rrect(ctx, x, y - 8, w - 1, 14, 4); ctx.fill();
        if (w > 66) D.text(ctx, lbl, x + 5, y - 1, { color: P.surface, size: 9, weight: 600 });
        x += w + gap;
      });
      D.text(ctx, caption, x0, y - 16, { color: P.faint, size: 10 });
    }

    L.draw = P => {
      c.clear();
      const { ctx } = c;
      T.draw(ctx, P);
      const l = s.last;
      if (l) {
        drawRow(ctx, P, l.tripLabels, c.h - 46, l.mode === 'rest' ? P.series[3] : P.accent, 'network round trips (client ↔ API)');
        drawRow(ctx, P, l.dbLabels, c.h - 20, P.series[1], 'backend / DB calls', l.mode === 'graphql' && l.dataLoader ? 1 : -1);
      }
    };
    T.nodes.api.sub = 'REST API';
    update();
  },
});
