/* ============================================================================
   API module, part 3 — deeper gRPC and Protobuf labs.
   Requires viz.js (LABS, defineLab, D, rng, lerp, clamp) and viz-sd.js
   (fmtMs), both loaded earlier on the page. Overrides the simple DOM
   animations previously registered for 'api-grpc' and 'api-protobuf'
   (LABS is a Map, so the later definition wins).
   ========================================================================= */
'use strict';

/* ===================================================== 1 · gRPC streams == */
defineLab('api-grpc', {
  title: 'One HTTP/2 connection, four call shapes',
  hint: 'Pick a call shape and send it. Every gRPC call is one HTTP/2 stream; turn on background calls to see other streams share the same connection without blocking each other.',
  mount(L) {
    /* simulated protocol timing, in "formula ms" — independent of the
       animation speed, used only for the accurate numbers in stats/insight */
    const NET = { oneWay: 25, process: 10, chunkProcess: 5, chunkTransit: 5, sendGap: 4, interleave: 14 };
    const REAL_MS_PER_SIM_MS = 15; // how slowly the animation plays the timeline
    const MODE_NAME = { unary: 'Unary', server: 'Server streaming', client: 'Client streaming', bidi: 'Bidirectional' };
    const r = rng(4);

    const s = {
      mode: 'unary', n: 6, mux: true,
      scheduled: [], frames: [], clockMs: 0,
      sent: 0, received: 0,
      formulaMs: undefined, lastTotalMs: null, lastCmpMs: null,
    };

    const c = L.canvas(w => Math.min(340, Math.max(260, w * .46)));

    L.seg('call shape', [['unary', 'Unary'], ['server', 'Server streaming'], ['client', 'Client streaming'], ['bidi', 'Bidirectional']], s.mode, v => { s.mode = v; update(); });
    L.slider('messages in the stream', { min: 2, max: 12, step: 1, value: s.n }, v => { s.n = v; update(); });
    L.toggle('2 background calls sharing the connection', s.mux, v => { s.mux = v; update(); });
    L.button('Send call', () => send(), 'primary');
    L.button('Reset', () => reset());

    function push(list, atMs, dir, kind, label, lane) { list.push({ atMs, dir, kind, label, lane }); }

    function planMain() {
      const evs = [], n = s.n;
      if (s.mode === 'unary') {
        push(evs, 0, 1, 'req', 'REQ', 0);
        push(evs, NET.oneWay + NET.process, -1, 'res', 'RES', 0);
        push(evs, NET.oneWay + NET.process + 4, -1, 'trailer', 'OK', 0);
        s.formulaMs = NET.oneWay * 2 + NET.process;
      } else if (s.mode === 'server') {
        push(evs, 0, 1, 'req', 'REQ', 0);
        let t = NET.oneWay;
        for (let i = 0; i < n; i++) { t += NET.chunkProcess; push(evs, t, -1, 'res', `#${i + 1}`, 0); t += NET.chunkTransit; }
        push(evs, t + NET.chunkTransit, -1, 'trailer', 'OK', 0);
        s.formulaMs = t + NET.chunkTransit;
      } else if (s.mode === 'client') {
        let t = 0;
        for (let i = 0; i < n; i++) { push(evs, t, 1, 'req', `#${i + 1}`, 0); t += NET.sendGap; }
        push(evs, t + NET.process, -1, 'res', 'RES', 0);
        push(evs, t + NET.process + 4, -1, 'trailer', 'OK', 0);
        s.formulaMs = t + NET.process + 4;
      } else {
        let t = 0;
        for (let i = 0; i < n; i++) {
          push(evs, t, 1, 'req', String.fromCharCode(65 + (i % 26)), 0);
          push(evs, t + NET.chunkProcess, -1, 'res', `${i + 1}`, 0);
          t += NET.interleave;
        }
        push(evs, t + 4, -1, 'trailer', 'OK', 0);
        s.formulaMs = t + 4;
      }
      return evs;
    }

    function planBackground(totalMs) {
      const evs = [];
      [1, 2].forEach(lane => {
        let t = r() * 120;
        while (t < totalMs + 60) {
          push(evs, t, 1, 'req', 'req', lane);
          push(evs, t + NET.oneWay, -1, 'res', 'res', lane);
          push(evs, t + NET.oneWay + 6, -1, 'trailer', 'OK', lane);
          t += NET.oneWay * 2 + 70 + r() * 90;
        }
      });
      return evs;
    }

    function send() {
      const main = planMain();
      const bg = s.mux ? planBackground(s.formulaMs) : [];
      s.scheduled = [...main, ...bg].sort((a, b) => a.atMs - b.atMs);
      s.frames = [];
      s.clockMs = 0; s.sent = 0; s.received = 0;
      s.lastTotalMs = null;
      s.lastCmpMs = s.n * (NET.oneWay * 2 + NET.process);
      run.start();
      update();
    }

    function reset() {
      run.stop();
      s.scheduled = []; s.frames = []; s.clockMs = 0;
      s.sent = 0; s.received = 0; s.formulaMs = undefined; s.lastTotalMs = null; s.lastCmpMs = null;
      update();
    }

    const run = L.loop(dt => {
      s.clockMs += (dt * 1000) / REAL_MS_PER_SIM_MS;
      while (s.scheduled.length && s.scheduled[0].atMs <= s.clockMs) spawn(s.scheduled.shift());
      s.frames.forEach(f => { f.t += (dt * 1000) / f.durMs; });
      const arrived = s.frames.filter(f => f.t >= 1);
      arrived.forEach(onArrive);
      s.frames = s.frames.filter(f => f.t < 1);
      L.redraw();
      if (!s.scheduled.length && !s.frames.length) {
        if (s.lastTotalMs == null) { s.lastTotalMs = s.formulaMs; update(); }
        return false;
      }
    });

    function spawn(ev) { s.frames.push({ ...ev, t: 0, durMs: 420 }); }

    function onArrive(f) {
      if (f.lane === 0) {
        if (f.kind === 'req') s.sent++;
        else if (f.kind === 'res') s.received++;
        update();
      }
    }

    function update() {
      const laneCount = s.mux ? 3 : 1;
      L.stats([
        ['call shape', MODE_NAME[s.mode], 'accent'],
        ['sent →', s.sent],
        ['← received', s.received],
        s.mode !== 'unary' && ['this call', s.lastTotalMs != null ? fmtMs(s.lastTotalMs) : (s.formulaMs ? '…' : '—')],
        s.mode !== 'unary' && [`${s.n}× unary would take`, fmtMs(s.lastCmpMs ?? (s.n * (NET.oneWay * 2 + NET.process)))],
        ['streams on this connection', laneCount],
      ]);
      L.insight(insightText());
    }

    function insightText() {
      const base = {
        unary: 'One request frame, one response frame, then <b>trailers</b> carry the real result (<code>grpc-status</code>). The HTTP status line is almost always 200 — gRPC needs HTTP/2 because HTTP/1.1 has no trailers on a streamed response.',
        server: `The client sends one request; the server pushes ${s.n} response messages down the <b>same stream</b> without being asked again — built for big result sets or live feeds. That is one round trip total, not ${s.n}.`,
        client: `The client sends ${s.n} messages without waiting for a reply to each one, then half-closes and gets exactly <b>one</b> response — built for uploads and batched telemetry.`,
        bidi: 'Both sides send and receive <b>independently</b> on the same stream — a reply does not have to wait for the client to finish sending. This is what makes a real conversation (chat, multiplayer state) possible.',
      }[s.mode];
      const cmp = s.mode !== 'unary' && s.lastTotalMs != null
        ? ` This call took ${fmtMs(s.lastTotalMs)}; doing the same ${s.n} messages as ${s.n} separate unary calls would cost ${fmtMs(s.lastCmpMs)} — ${s.n} extra round trips instead of one.`
        : '';
      const mux = s.mux
        ? ' Two other calls are sharing this exact connection right now; their frames interleave with yours because HTTP/2 multiplexes independent streams — unlike HTTP/1.1, where a slow request blocks the next one queued on the same connection (head-of-line blocking).'
        : ' Turn on background calls to see other streams share this same connection without waiting for yours to finish.';
      return `<b>${MODE_NAME[s.mode]}.</b> ${base}${cmp}${mux}`;
    }

    L.draw = P => {
      c.clear();
      const { ctx } = c;
      const laneCount = s.mux ? 3 : 1;
      const top = 46, bottom = c.h - 26;
      const bandH = bottom - top;
      const laneYs = Array.from({ length: laneCount }, (_, i) => top + (i + .5) * bandH / laneCount);
      const cx = 54, sx = c.w - 54;

      ctx.fillStyle = P.alpha('surface2', .6);
      D.rrect(ctx, cx + 20, top - 6, sx - cx - 40, bandH + 12, 10); ctx.fill();
      ctx.strokeStyle = P.soft; ctx.lineWidth = 1; ctx.stroke();
      D.text(ctx, '1 HTTP/2 connection (TCP + TLS) — reused for every call', (cx + sx) / 2, top - 16, { color: P.faint, size: 10.5, align: 'center' });

      ctx.fillStyle = P.surface2; ctx.strokeStyle = P.strong; ctx.lineWidth = 1.5;
      D.rrect(ctx, cx - 32, top - 6, 36, bandH + 12, 10); ctx.fill(); ctx.stroke();
      D.rrect(ctx, sx - 4, top - 6, 36, bandH + 12, 10); ctx.fill(); ctx.stroke();
      D.text(ctx, 'Client', cx - 14, top - 16, { color: P.text, size: 11, align: 'center', weight: 650 });
      D.text(ctx, 'Server', sx + 14, top - 16, { color: P.text, size: 11, align: 'center', weight: 650 });

      laneYs.forEach((y, i) => {
        D.line(ctx, cx, y, sx, y, P.alpha('faint', .35), 1, [3, 4]);
        D.text(ctx, i === 0 ? 'stream 1 · your call' : `stream ${i + 1} · background`, cx + 4, y - 9, { color: P.dim, size: 9.5, align: 'left' });
      });

      s.frames.forEach(f => {
        const y = laneYs[f.lane] ?? laneYs[0];
        const x = f.dir === 1 ? lerp(cx, sx, f.t) : lerp(sx, cx, f.t);
        const col = f.kind === 'trailer' ? P.ok : P.series[f.lane % P.series.length];
        const w = 30, h = 15;
        ctx.fillStyle = P.alpha(col, .92);
        D.rrect(ctx, x - w / 2, y - h / 2, w, h, 4); ctx.fill();
        D.text(ctx, f.label, x, y + 1, { color: P.surface, size: 8.5, align: 'center', weight: 700, mono: true });
      });

      D.text(ctx, 'boxes = HTTP/2 DATA frames (5-byte length-prefixed) · green = trailers (grpc-status)', cx - 20, c.h - 8, { color: P.faint, size: 9.5 });
    };

    update();
  },
});

/* ================================================== 2 · Protobuf wire == */
defineLab('api-protobuf', {
  title: 'Bytes on the wire, and what a renumbered field does',
  hint: 'Change the fields below and watch the exact bytes protobuf emits. Switch to schema evolution to see the same bytes read by an old or a new reader.',
  mount(L) {
    const names = ['Al', 'Ana', 'Zoe', 'Alex', 'Diana', 'Alexandria', 'Bartholomew'];
    const cities = ['NY', 'Oslo', 'Paris', 'Berlin', 'Reykjavik'];

    const s = { view: 'encode', id: 150, negId: false, nameIdx: 2, cityIdx: 1, addrOn: true, field16: false, reader: 'v1' };

    const c = L.canvas(w => Math.min(400, Math.max(300, w * .52)));

    L.seg('view', [['encode', 'Byte-level encoding'], ['evolve', 'Schema evolution']], s.view, v => { s.view = v; update(); });
    L.slider('id — field 1 (int64, varint)', { min: 0, max: 500000, step: 1, value: s.id, fmt: v => v.toLocaleString() }, v => { s.id = v; update(); });
    L.toggle('negative id (sign-extension trap)', s.negId, v => { s.negId = v; update(); });
    L.slider('name — field 2 (string)', { min: 0, max: names.length - 1, step: 1, value: s.nameIdx, fmt: i => `"${names[i]}"` }, v => { s.nameIdx = v; update(); });
    L.toggle('address present — field 3 (nested message)', s.addrOn, v => { s.addrOn = v; update(); });
    L.slider('address.city — nested string', { min: 0, max: cities.length - 1, step: 1, value: s.cityIdx, fmt: i => `"${cities[i]}"` }, v => { s.cityIdx = v; update(); });
    L.toggle('move address to field 16 (2-byte tag)', s.field16, v => { s.field16 = v; update(); });
    L.seg('reader (schema-evolution view)', [['v1', 'v1 reader'], ['v2safe', 'v2: +email'], ['v2unsafe', 'v2: reused #3']], s.reader, v => { s.reader = v; update(); });

    /* ---- wire-format helpers, matching protoc's actual encoding ---- */
    function varintBytes(nRaw) {
      let v = BigInt.asUintN(64, BigInt(Math.trunc(nRaw)));
      const bytes = [];
      do {
        let b = Number(v & 0x7Fn);
        v >>= 7n;
        if (v > 0n) b |= 0x80;
        bytes.push(b);
      } while (v > 0n);
      return bytes;
    }
    function utf8(str) { return Array.from(new TextEncoder().encode(str)); }
    function tagBytes(field, wireType) { return varintBytes((field << 3) | wireType); }
    function escBytes(bytes) {
      return bytes.map(b => (b >= 0x20 && b < 0x7f) ? String.fromCharCode(b) : `\\x${b.toString(16).padStart(2, '0')}`).join('');
    }

    function buildMessage() {
      const segs = [];
      const idVal = s.negId ? -Math.abs(s.id || 1) : s.id;
      segs.push({ field: 'id', part: 'tag', bytes: tagBytes(1, 0) });
      segs.push({ field: 'id', part: 'value', bytes: varintBytes(idVal) });

      const nameBytes = utf8(names[s.nameIdx]);
      segs.push({ field: 'name', part: 'tag', bytes: tagBytes(2, 2) });
      segs.push({ field: 'name', part: 'len', bytes: varintBytes(nameBytes.length) });
      segs.push({ field: 'name', part: 'value', bytes: nameBytes });

      const addrFieldNum = s.field16 ? 16 : 3;
      let addrInner = null;
      if (s.addrOn) {
        const cityBytes = utf8(cities[s.cityIdx]);
        addrInner = [...tagBytes(1, 2), ...varintBytes(cityBytes.length), ...cityBytes];
        segs.push({ field: 'address', part: 'tag', bytes: tagBytes(addrFieldNum, 2) });
        segs.push({ field: 'address', part: 'len', bytes: varintBytes(addrInner.length) });
        segs.push({ field: 'address', part: 'value', bytes: addrInner });
      }
      const bytes = segs.flatMap(x => x.bytes);
      return { bytes, segs, idVal, addrInner, addrFieldNum };
    }

    function jsonBytesFor(msg) {
      const obj = { id: msg.idVal, name: names[s.nameIdx] };
      if (s.addrOn) obj.address = { city: cities[s.cityIdx] };
      return JSON.stringify(obj).length;
    }

    function decodeEvolve(msg) {
      const rows = [];
      rows.push({ tag: 1, as: 'id (int64)', value: String(msg.idVal), ok: true });
      rows.push({ tag: 2, as: 'name (string)', value: `"${names[s.nameIdx]}"`, ok: true });
      if (s.addrOn) {
        if (s.reader === 'v2unsafe' && msg.addrFieldNum === 3) {
          rows.push({ tag: 3, as: 'nickname (string) — REUSED', value: `"${escBytes(msg.addrInner)}"`, ok: false });
        } else if (s.reader === 'v2unsafe' && msg.addrFieldNum === 16) {
          rows.push({ tag: 16, as: 'address (message)', value: `{city:"${cities[s.cityIdx]}"}`, ok: true });
        } else {
          rows.push({ tag: msg.addrFieldNum, as: 'address (message)', value: `{city:"${cities[s.cityIdx]}"}`, ok: true });
        }
      }
      if (s.reader === 'v2safe') rows.push({ tag: 4, as: 'email (string) — new', value: '"" (default: never sent)', ok: true });
      return rows;
    }

    function encodeInsight(msg) {
      if (s.negId) {
        const idValBytes = msg.segs.find(x => x.field === 'id' && x.part === 'value').bytes.length;
        return `<b>Field 1 is <code>int64</code>, not <code>sint64</code>.</b> A negative value is sign-extended to a 64-bit two's-complement number before it is varint-encoded, so it costs <b>${idValBytes} value bytes</b> — the same as a huge positive number. A field that is often negative should be <code>sint32</code>/<code>sint64</code> (ZigZag), which would cost 1-2 bytes for a small magnitude like this.`;
      }
      if (!s.addrOn) {
        return '<b>address is unset</b>, and proto3 never writes a field equal to its default — so it costs exactly <b>0 bytes</b> on the wire, not even a null marker. That also means "unset" and "the empty default" look identical once decoded.';
      }
      if (s.field16) {
        return '<b>address moved to field number 16.</b> A tag is <code>(number &lt;&lt; 3) | wire_type</code> encoded as a varint: up to 15 that fits in one byte, from 16 it needs two. Reserve numbers 1-15 for the fields present in almost every message.';
      }
      return `<b>No field names are on the wire</b> — only the numbers 1, 2 and ${msg.addrFieldNum} (the tags) are. Only a receiver holding the same <code>.proto</code> file can turn tag 2 back into "name". That is <b>${msg.bytes.length} protobuf bytes</b> against <b>${jsonBytesFor(msg)} JSON bytes</b> for the same data.`;
    }

    function evolveInsight(msg, rows) {
      if (s.reader === 'v1') {
        return `<b>The v1 reader knows exactly this schema:</b> tag 1 → id, tag 2 → name, tag ${msg.addrFieldNum} → address. Every field decodes to what it was written as.`;
      }
      if (s.reader === 'v2safe') {
        return '<b>v2 adds <code>email</code> at a brand-new field number (4).</b> This message never wrote tag 4, so email simply reads back as its default, <code>""</code> — no crash, no missing-field error. Adding a field with a new number is always backward-compatible.';
      }
      if (!s.addrOn) {
        return `<b>Nothing to corrupt here</b> — address was never written, so there is no tag ${msg.addrFieldNum} on the wire for the reused number to collide with. Turn address back on to see the collision.`;
      }
      if (msg.addrFieldNum === 16) {
        return "<b>No collision.</b> address now lives at field 16, so the v2 reader's reused field 3 finds nothing here. But if <i>any other</i> message in this system still writes real data at field 3, reusing it there corrupts exactly the way shown when address is back at field 3.";
      }
      return `<b>Silent corruption.</b> v2 reused field number 3 for a new <code>string nickname</code>, but this message's tag 3 is still the old <b>nested address</b> — and a nested message and a string share the same wire type (LEN), so nothing errors. The reader just decodes those raw bytes as text and calls it <code>nickname</code>: <code>"${escBytes(msg.addrInner)}"</code>. No exception, no warning — just the wrong field, forever. This is exactly why field numbers are never reused; <code>reserved</code> makes the compiler refuse it.`;
    }

    function drawByteGrid(ctx, P, x0, y0, maxW, segs) {
      const boxW = 18, boxH = 18, gap = 2, fieldGap = 12, rowH = 26;
      const fieldOrder = [];
      segs.forEach(sg => { if (!fieldOrder.includes(sg.field)) fieldOrder.push(sg.field); });
      const colorOf = f => P.series[fieldOrder.indexOf(f) % P.series.length];
      let x = x0, y = y0, lastField = null;
      segs.forEach(sg => {
        if (lastField !== null && sg.field !== lastField) x += fieldGap;
        sg.bytes.forEach(b => {
          if (x + boxW > x0 + maxW) { x = x0; y += rowH; }
          const col = colorOf(sg.field);
          ctx.fillStyle = P.alpha(col, sg.part === 'value' ? .85 : .35);
          D.rrect(ctx, x, y, boxW, boxH, 4); ctx.fill();
          ctx.strokeStyle = P.alpha(col, .9); ctx.lineWidth = 1; ctx.stroke();
          D.text(ctx, b.toString(16).padStart(2, '0'), x + boxW / 2, y + boxH / 2 + 1, { color: P.text, size: 9, align: 'center', mono: true, weight: 600 });
          x += boxW + gap;
        });
        lastField = sg.field;
      });
      return { bottom: y + boxH, fieldOrder, colorOf };
    }

    function update() {
      const msg = buildMessage();
      s._msg = msg;
      if (s.view === 'encode') {
        const jsonBytes = jsonBytesFor(msg);
        const idBytes = msg.segs.filter(x => x.field === 'id').reduce((a, x) => a + x.bytes.length, 0);
        L.stats([
          ['protobuf bytes', msg.bytes.length, 'accent'],
          ['JSON bytes', jsonBytes],
          ['smaller by', `${(jsonBytes / msg.bytes.length).toFixed(1)}×`],
          ['id costs', `${idBytes} B`],
          ['fields on the wire', msg.segs.filter(x => x.part === 'tag').length],
        ]);
        L.insight(encodeInsight(msg));
      } else {
        const rows = decodeEvolve(msg);
        const corrupted = rows.some(row => !row.ok);
        L.stats([
          ['bytes on the wire', msg.bytes.length, 'accent'],
          ['reader', { v1: 'v1 (original)', v2safe: 'v2 (+email)', v2unsafe: 'v2 (reused #3)' }[s.reader]],
          ['fields decoded', rows.length],
          ['result', corrupted ? 'silently wrong' : 'correct', corrupted ? 'err' : 'ok'],
        ]);
        L.insight(evolveInsight(msg, rows));
      }
      L.redraw();
    }

    L.draw = P => {
      c.clear();
      const { ctx } = c;
      const msg = s._msg || buildMessage();
      const x0 = 16, maxW = c.w - 32;

      D.text(ctx, s.view === 'encode'
        ? `Customer { id=1, name=2, address=${msg.addrFieldNum} } — bytes on the wire`
        : 'these bytes were written once, using the schema above — only the reader changes below', x0, 16, { color: P.faint, size: 10.5 });

      const { bottom, fieldOrder, colorOf } = drawByteGrid(ctx, P, x0, 30, maxW, msg.segs);

      let lx = x0, ly = bottom + 18;
      fieldOrder.forEach(f => {
        const col = colorOf(f);
        ctx.fillStyle = col; D.rrect(ctx, lx, ly - 8, 10, 10, 2); ctx.fill();
        D.text(ctx, f, lx + 14, ly - 2, { color: P.dim, size: 10, align: 'left' });
        lx += 14 + ctx.measureText(f).width + 20;
      });
      ly += 20;

      if (s.view === 'encode') {
        const jsonBytes = jsonBytesFor(msg);
        const barY = ly + 12, barH = 16, barMaxW = maxW;
        const pbW = Math.max(4, barMaxW * msg.bytes.length / jsonBytes);
        ctx.fillStyle = P.alpha('faint', .18); D.rrect(ctx, x0, barY, barMaxW, barH, 4); ctx.fill();
        ctx.fillStyle = P.accent; D.rrect(ctx, x0, barY, pbW, barH, 4); ctx.fill();
        D.text(ctx, `protobuf ${msg.bytes.length} B`, x0 + 6, barY + barH / 2 + 1, { color: P.surface, size: 9.5, align: 'left', weight: 650 });
        D.text(ctx, `JSON ${jsonBytes} B`, x0 + barMaxW, barY - 8, { color: P.faint, size: 10, align: 'right' });
      } else {
        const rows = decodeEvolve(msg);
        let ry = ly + 8;
        D.text(ctx, 'tag', x0, ry, { color: P.faint, size: 9.5 });
        D.text(ctx, 'reader decodes as', x0 + 46, ry, { color: P.faint, size: 9.5 });
        D.text(ctx, 'value', Math.min(x0 + 230, c.w - 90), ry, { color: P.faint, size: 9.5 });
        ry += 18;
        rows.forEach(row => {
          const col = row.ok ? P.ok : P.err;
          D.dot(ctx, x0 + 4, ry - 3, 3.5, col);
          D.text(ctx, String(row.tag), x0 + 16, ry, { color: P.text, size: 10.5, mono: true });
          D.text(ctx, row.as, x0 + 46, ry, { color: row.ok ? P.text : P.err, size: 10, align: 'left' });
          D.text(ctx, row.value, Math.min(x0 + 230, c.w - 90), ry, { color: P.dim, size: 9.5, mono: true, align: 'left' });
          ry += 20;
        });
      }
    };

    update();
  },
});
