'use strict';

/* ============================================================================
   SOAP lab — envelope anatomy, WSDL contract enforcement and Faults.
   Requires viz.js (labApi, D, palette) and viz-sd.js (topo, drawSysNode).
   ========================================================================= */

defineLab('api-soap', {
  title: 'SOAP envelope, WSDL contract & Faults',
  hint: 'Build a request — pick the operation, break a field, attach or drop the WS-Security header — then send it and watch the WSDL gate accept or reject it before business logic ever runs. Flip to REST-style to see the same bad data sail through unchecked.',
  mount(L) {
    /* ---------------------------------------------------------- contract -- */
    const CONTRACTS = {
      GetBalance: {
        in: [['accountId', 'xsd:string'], ['includePending', 'xsd:boolean']],
        out: [['balance', 'xsd:decimal']],
        requiresAuth: false,
      },
      Transfer: {
        in: [['fromAccount', 'xsd:string'], ['toAccount', 'xsd:string'], ['amount', 'xsd:decimal']],
        out: [['confirmationId', 'xsd:string']],
        requiresAuth: true,
      },
    };
    const sampleValue = name => ({
      accountId: 'ACC-1001', fromAccount: 'ACC-1001', toAccount: 'ACC-2002',
      amount: '500.00', includePending: 'true',
    }[name] ?? '—');

    const s = {
      op: 'GetBalance', payload: 'valid', auth: false, skew: 0, ver: '1.1', mode: 'soap',
      sent: 0, success: 0, rejected: 0, bugsThrough: 0, last: null,
    };

    /* ------------------------------------------------------------ canvas -- */
    const c = L.canvas(w => Math.min(560, Math.max(440, w * .58)));
    const T = topo(c);
    T.node('client', .09, .24, 'Client app', { kind: 'client', w: 84 });
    T.node('gate', .42, .10, 'WSDL Gate', { w: 132, sub: 'schema + mustUnderstand' });
    T.node('rest', .42, .40, 'REST handler', { w: 132, sub: 'no schema check' });
    T.node('biz', .80, .24, 'Bank core', { kind: 'db', w: 108, h: 56, sub: 'ACID txn' });
    T.edge('client', 'gate', { grp: 'soap' });
    T.edge('gate', 'biz', { grp: 'soap' });
    T.edge('client', 'rest', { grp: 'rest' });
    T.edge('rest', 'biz', { grp: 'rest' });

    /* ----------------------------------------------------------- request -- */
    function buildFields() {
      const ct = CONTRACTS[s.op];
      const missingField = ct.in[ct.in.length - 1][0];
      const wrongField = (ct.in.find(([, t]) => t === 'xsd:decimal' || t === 'xsd:boolean') || ct.in[0])[0];
      const badnsField = ct.in[0][0];
      return ct.in.map(([name, type]) => {
        let value = sampleValue(name), ok = true, note = '';
        if (s.payload === 'missing' && name === missingField) { value = '(absent)'; ok = false; note = `required, minOccurs="1"`; }
        else if (s.payload === 'wrongtype' && name === wrongField) { value = '"many"'; ok = false; note = `expected ${type}`; }
        else if (s.payload === 'badns' && name === badnsField) { value = sampleValue(name); ok = false; note = 'wrong XML namespace prefix'; }
        return { name, type, value, ok, note };
      });
    }
    function validate(fields) {
      const ct = CONTRACTS[s.op];
      if (s.mode === 'rest') return { pass: true, bug: fields.some(f => !f.ok) };
      if (ct.requiresAuth && !s.auth) {
        return { pass: false, code: 'MustUnderstand', status: 500,
          text: `&lt;wsse:Security mustUnderstand="1"&gt; is required for ${s.op} but was not attached. The receiver must reject the whole message without ever looking at the Body.` };
      }
      if (s.auth && s.skew > 300) {
        return { pass: false, code: s.ver === '1.1' ? 'Client' : 'Sender', status: s.ver === '1.1' ? 500 : 400,
          text: 'WS-Security validation failed.' };
      }
      const bad = fields.find(f => !f.ok);
      if (bad) {
        const text = bad.note.includes('namespace')
          ? `Required element {${bad.name}} not found — the client used the wrong XML namespace, so the WSDL-generated parser never sees it.`
          : bad.note.includes('minOccurs')
            ? `Required element &lt;${bad.name}&gt; is missing (WSDL: minOccurs="1").`
            : `Type mismatch on &lt;${bad.name}&gt;: expected ${bad.type}, got a non-numeric value.`;
        return { pass: false, code: s.ver === '1.1' ? 'Client' : 'Sender', status: s.ver === '1.1' ? 500 : 400, text };
      }
      return { pass: true };
    }

    /* --------------------------------------------------------- controls -- */
    const onChange = () => { s.last = null; update(); L.redraw(); };
    L.seg('operation', [['GetBalance', 'GetBalance (read)'], ['Transfer', 'Transfer (write)']], s.op, v => { s.op = v; onChange(); });
    L.seg('payload', [['valid', 'Valid'], ['missing', 'Missing field'], ['wrongtype', 'Wrong type'], ['badns', 'Wrong namespace']], s.payload, v => { s.payload = v; onChange(); });
    L.toggle('WS-Security token attached', s.auth, v => { s.auth = v; onChange(); });
    L.slider('clock skew on token', { min: 0, max: 600, step: 15, value: s.skew, fmt: v => `${v}s` }, v => { s.skew = v; onChange(); });
    L.seg('SOAP version', [['1.1', 'SOAP 1.1'], ['1.2', 'SOAP 1.2']], s.ver, v => { s.ver = v; onChange(); });
    L.seg('contract mode', [['soap', 'SOAP (strict WSDL)'], ['rest', 'REST-style (loose JSON)']], s.mode, v => { s.mode = v; onChange(); });

    const run = L.loop(dt => { T.step(dt); L.redraw(); if (!T.busy()) return false; });
    L.button('Send request', () => { fire(); run.start(); }, 'primary');
    L.button('Reset stats', () => { s.sent = s.success = s.rejected = s.bugsThrough = 0; s.last = null; update(); L.redraw(); });

    function fire() {
      s.sent++;
      const fields = buildFields();
      const v = validate(fields);
      let outcome, path, color;
      if (s.mode === 'soap') {
        if (v.pass) { outcome = 'success'; path = ['client', 'gate', 'biz', 'gate', 'client']; color = L.P.ok; s.success++; }
        else { outcome = 'fault'; path = ['client', 'gate', 'client']; color = L.P.err; s.rejected++; }
      } else {
        outcome = v.bug ? 'bug' : 'success';
        path = ['client', 'rest', 'biz', 'rest', 'client'];
        color = v.bug ? L.P.series[1] : L.P.ok;
        v.bug ? s.bugsThrough++ : s.success++;
      }
      T.send(path, {
        speed: 3, color, hop: id => T.pulse(id),
        end: () => {
          s.last = { mode: s.mode, op: s.op, outcome, status: v.status || 200, code: v.code || null, text: v.text || '', fields };
          update(); L.redraw();
        },
      });
    }

    /* ---------------------------------------------------------- readout -- */
    function update() {
      const l = s.last;
      const label = !l ? '—' : l.outcome === 'success' ? 'Success' : l.outcome === 'fault' ? `Fault: ${l.code}` : 'Accepted (bug)';
      const cls = !l ? '' : l.outcome === 'success' ? 'ok' : l.outcome === 'fault' ? 'err' : '';
      L.stats([
        ['result', label, cls],
        ['HTTP status', l ? l.status : '—'],
        ['fault code', l && l.outcome === 'fault' ? l.code : '—'],
        ['requests sent', s.sent],
        ['rejected by gate', s.rejected],
        ['silent bugs (REST)', s.bugsThrough],
      ]);
      L.insight(insightHtml());
    }
    function insightHtml() {
      const l = s.last, ct = CONTRACTS[s.op];
      if (!l) return `<b>Build a request, then press "Send request".</b> The WSDL fixes exactly what <code>${s.op}</code> accepts (types, required fields, whether WS-Security is mandatory) — try breaking it and watch where the break gets caught.`;
      if (l.mode === 'soap') {
        if (l.outcome === 'fault') return `<b>Rejected at the gate — HTTP ${l.status}, ${s.ver === '1.1' ? 'faultcode' : 'Code'} <code>${l.code}</code>.</b> ${l.text} Business logic never ran: that is what contract-first, fail-fast buys a bank.`;
        return `<b>HTTP ${l.status} OK.</b> The WSDL-generated parser matched every element by name and namespace${ct.requiresAuth ? ', the mandatory Security header was understood,' : ''} and every type checked out, so <code>${s.op}</code> executed against the real backend.`;
      }
      if (l.outcome === 'bug') {
        const bad = l.fields.find(f => !f.ok);
        return `<b>HTTP ${l.status} OK — but silently wrong.</b> Nothing here validates against a schema, so <code>${bad.name}</code> (${bad.note}) slipped straight into business logic. The identical payload sent as SOAP would have bounced at the gate before touching the database.`;
      }
      return `<b>HTTP ${l.status} OK.</b> The payload happened to be well-formed, so loose validation made no visible difference here — the risk only shows up once a field is malformed.`;
    }

    /* ------------------------------------------------------------- draw -- */
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      T.edges.forEach(e => {
        const active = e.grp === s.mode;
        e.color = active ? P.strong : P.alpha('faint', .25);
        e.dash = active ? null : [4, 4];
        e.w = active ? 1.8 : 1.2;
      });
      T.nodes.gate.stroke = s.mode === 'soap' ? null : P.alpha('faint', .35);
      T.nodes.gate.labelColor = s.mode === 'soap' ? null : P.faint;
      T.nodes.gate.subColor = s.mode === 'soap' ? null : P.alpha('faint', .5);
      T.nodes.rest.stroke = s.mode === 'rest' ? null : P.alpha('faint', .35);
      T.nodes.rest.labelColor = s.mode === 'rest' ? null : P.faint;
      T.nodes.rest.subColor = s.mode === 'rest' ? null : P.alpha('faint', .5);
      T.draw(ctx, P);
      drawPanel(ctx, P);
    };

    function drawPanel(ctx, P) {
      const ct = CONTRACTS[s.op];
      const fields = buildFields();
      const x = 14, w = c.w - 28;
      const topY = c.h * .56;

      if (s.last) {
        const l = s.last;
        const chip = l.outcome === 'fault' ? `HTTP ${l.status} · Fault: ${l.code}` : l.outcome === 'bug' ? `HTTP ${l.status} · accepted (bug)` : `HTTP ${l.status} · OK`;
        D.text(ctx, chip, x + w, topY - 2, { color: l.outcome === 'fault' ? P.err : l.outcome === 'bug' ? P.series[1] : P.ok, size: 10.5, align: 'right', weight: 700, mono: true });
      }
      D.text(ctx, `WSDL: ${s.op}(${ct.in.map(([n, t]) => `${n}:${t}`).join(', ')}) → ${ct.out.map(([n, t]) => `${n}:${t}`).join(', ')}`,
        x, topY - 2, { color: P.faint, size: 10.5, mono: true, align: 'left' });

      let y = topY + 14;
      const boxTop = y;
      const showHeader = s.mode === 'soap';

      if (showHeader) {
        const h = 34;
        ctx.fillStyle = s.auth ? P.alpha('ok', .08) : P.alpha('faint', .06);
        ctx.strokeStyle = s.auth ? P.alpha('ok', .5) : P.alpha('faint', .35);
        D.rrect(ctx, x + 8, y, w - 16, h, 6); ctx.fill(); ctx.stroke();
        D.text(ctx, 'Header', x + 16, y + 12, { color: P.dim, size: 10, weight: 700 });
        const stale = s.auth && s.skew > 300;
        D.text(ctx, s.auth ? `wsse:UsernameToken · mustUnderstand="1" · clock skew ${s.skew}s${stale ? '  ← STALE (>300s)' : ''}` : (ct.requiresAuth ? 'empty — no WS-Security attached (required!)' : 'empty — no WS-Security attached (not required)'),
          x + 16, y + 25, { color: s.auth ? (stale ? P.err : P.ok) : (ct.requiresAuth ? P.err : P.faint), size: 10, mono: true });
        y += h + 8;
      }

      const bad = fields.find(f => !f.ok);
      const bodyOutcome = s.mode === 'soap' ? (bad || (ct.requiresAuth && !s.auth) || (s.auth && s.skew > 300) ? 'err' : 'ok') : (bad ? 'warn' : 'ok');
      const bodyCol = bodyOutcome === 'err' ? 'err' : bodyOutcome === 'warn' ? P.series[1] : 'ok';
      const bodyH = 22 + fields.length * 16;
      ctx.fillStyle = P.alpha(bodyCol, .08);
      ctx.strokeStyle = bodyOutcome === 'err' ? P.err : bodyOutcome === 'warn' ? P.series[1] : P.ok;
      D.rrect(ctx, x + 8, y, w - 16, bodyH, 6); ctx.fill(); ctx.stroke();
      D.text(ctx, s.mode === 'soap' ? `Body — ${s.op}` : `Body — JSON ${s.op}`, x + 16, y + 12, { color: P.dim, size: 10, weight: 700 });
      fields.forEach((f, i) => {
        const fy = y + 24 + i * 16;
        D.text(ctx, `${f.name}: ${f.value}`, x + 16, fy, { color: f.ok ? P.text : P.err, size: 10, mono: true });
        D.text(ctx, f.ok ? f.type : f.note, x + w - 24, fy, { color: P.faint, size: 9.5, align: 'right', mono: true });
      });
      y += bodyH + 8;

      ctx.strokeStyle = P.alpha('strong', showHeader ? .5 : .35);
      D.rrect(ctx, x, boxTop, w, y - boxTop, 8); ctx.stroke();
      D.text(ctx, showHeader ? `Envelope · SOAP ${s.ver}` : `HTTP POST /api/${s.op.toLowerCase()} · application/json`,
        x + w - 10, boxTop + 2, { color: P.faint, size: 9.5, align: 'right' });
    }

    update();
  },
});
