/* ============================================================================
   Maths for CS Engineers labs, part 4: information, computation, geometry.

     math-huffman   Huffman coding: build the tree, compare with entropy
     math-hamming   Hamming(7,4): three parity circles find and fix a flipped bit
     math-dfa       finite automata: step a machine through an input string
     math-geometry  the cross product as a turn test: orientation, segment
                    intersection, polygon area (shoelace) and convexity

   Object-spec labs (viz.js createLab), wrapped in a block for scope.
   ========================================================================= */
'use strict';
{
const fillRR = (ctx, x, y, w, h, r, fill, stroke, lw = 1.2) => {
  D.rrect(ctx, x, y, w, h, r);
  if (fill) { ctx.fillStyle = fill; ctx.fill(); }
  if (stroke) { ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke(); }
};
const onTap = (c, fn) => c.cv.addEventListener('click', e => { const r = c.cv.getBoundingClientRect(); fn(e.clientX - r.left, e.clientY - r.top); });
const escH = t => String(t).replace(/[&<>"]/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]));
const showSym = ch => ch === ' ' ? '␣' : ch === '\n' ? '↵' : ch;

/* ========================================================== math-huffman == */
defineLab('math-huffman', {
  title: 'Huffman coding: short codes for common symbols',
  hint: 'Type any text. Huffman repeatedly merges the two <b>rarest</b> symbols into one node; the path from the root spells each code (left = 0, right = 1). Press <b>Build</b> to watch the merges.',
  mount(L) {
    const s = { text: 'abracadabra', step: 0, acc: 0 };
    L.stage.innerHTML = `<label class="mlab-in"><span>text</span><input type="text" spellcheck="false" maxlength="80" value="abracadabra"></label>`;
    const input = L.stage.querySelector('input');
    const c = L.canvas(w => w < 520 ? 250 : 260);
    const tableBox = document.createElement('div'); tableBox.className = 'mlab-box'; L.stage.append(tableBox);
    input.addEventListener('input', () => { s.text = input.value || 'a'; s.step = build().merges.length; update(); });
    function build() {
      const freq = new Map(); [...s.text].forEach(ch => freq.set(ch, (freq.get(ch) || 0) + 1));
      let id = 0;
      const leaves = [...freq.entries()].sort((a, b) => a[1] - b[1] || (a[0] < b[0] ? -1 : 1)).map(([ch, w]) => ({ ch, w, id: id++, at: -1 }));
      const pq = [...leaves], merges = [];
      while (pq.length > 1) {
        pq.sort((a, b) => a.w - b.w || a.id - b.id);
        const a = pq.shift(), b = pq.shift();
        const n = { w: a.w + b.w, l: a, r: b, id: id++, at: merges.length };
        merges.push(n); pq.push(n);
      }
      const root = pq[0], codes = new Map();
      const walk = (n, code, d) => { n.depth = d; if (n.ch !== undefined) codes.set(n.ch, code || '0'); else { walk(n.l, code + '0', d + 1); walk(n.r, code + '1', d + 1); } };
      walk(root, '', 0);
      return { freq, leaves, merges, root, codes };
    }
    const run = L.loop(dt => { s.acc += dt; if (s.acc > .6) { s.acc = 0; if (s.step >= build().merges.length) return false; s.step++; update(); } });
    L.playButton(run, ['Build the tree', 'Pause'], () => { if (s.step >= build().merges.length) s.step = 0; });
    [['abracadabra', 'abracadabra'], ['aaaaaaab', 'skewed'], ['abcdefgh', 'all equal'], ['the quick brown fox jumps over the lazy dog', 'pangram']]
      .forEach(([t, l]) => L.button(l, () => { run.stop(); input.value = t; s.text = t; s.step = build().merges.length; update(); }));
    function update() {
      const { freq, codes } = build(), n = s.text.length, k = freq.size;
      const fixed = n * Math.max(1, Math.ceil(Math.log2(k))), huff = [...freq].reduce((t, [ch, f]) => t + f * codes.get(ch).length, 0);
      const H = -[...freq.values()].reduce((t, f) => t + f / n * Math.log2(f / n), 0);
      tableBox.innerHTML = `<table class="mlab-table"><tr><th>symbol</th><th>count</th><th>probability</th><th>code</th><th>bits</th></tr>${[...freq].sort((a, b) => b[1] - a[1]).map(([ch, f]) =>
        `<tr><td>${escH(showSym(ch))}</td><td>${f}</td><td>${(f / n).toFixed(3)}</td><td>${codes.get(ch)}</td><td>${f * codes.get(ch).length}</td></tr>`).join('')}</table>`;
      L.stats([['symbols', `${n} (${k} distinct)`], ['fixed-length code', `${fixed} bits`], ['Huffman', `${huff} bits`, 'accent'], ['entropy bound n·H', `${(n * H).toFixed(1)} bits`, 'ok'], ['H per symbol', `${H.toFixed(3)} bits`]]);
      L.insight(k === 1 ? 'A single repeated symbol carries no information: entropy 0. (A real coder still needs 1 bit per symbol, or a run length.)'
        : `Frequent symbols get short codes, rare ones long codes, and <b>no code is a prefix of another</b> (every symbol is a leaf), so the bit stream decodes without separators. Huffman is optimal among symbol-by-symbol codes and always lands within 1 bit per symbol of the <b>entropy</b> H — Shannon’s limit on lossless compression. When every symbol is equally likely there is nothing to exploit: Huffman equals fixed length.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, { leaves, merges, root } = build();
      if (!root) return;
      // x positions: leaves in tree (in-order) order; internal nodes centred over children
      let li = 0; const pos = new Map(), nl = leaves.length, maxD = Math.max(1, ...leaves.map(l => l.depth));
      const place = n => { if (n.ch !== undefined) { pos.set(n.id, [18 + (c.w - 36) * (nl === 1 ? .5 : li++ / (nl - 1)), 0]); return; } place(n.l); place(n.r); pos.set(n.id, [(pos.get(n.l.id)[0] + pos.get(n.r.id)[0]) / 2, 0]); };
      place(root);
      const Y = d => 22 + (c.h - 60) * d / maxD, visible = n => n.ch !== undefined || n.at < s.step;
      const edges = n => { if (n.ch !== undefined) return; if (visible(n)) [[n.l, '0'], [n.r, '1']].forEach(([ch, bit]) => { const [x1] = pos.get(n.id), [x2] = pos.get(ch.id); D.line(ctx, x1, Y(n.depth), x2, Y(ch.depth), P.alpha('dim', .7), 1.5); D.text(ctx, bit, (x1 + x2) / 2 + (bit === '0' ? -7 : 7), (Y(n.depth) + Y(ch.depth)) / 2, { color: P.accent, size: 11, align: 'center', weight: 700, mono: true }); }); edges(n.l); edges(n.r); };
      edges(root);
      const nodes = n => { if (visible(n)) { const [x] = pos.get(n.id), y = Y(n.depth), fresh = n.at === s.step - 1; if (n.ch !== undefined) { fillRR(ctx, x - 13, y - 13, 26, 26, 6, P.alpha('accent', .25), P.accent); D.text(ctx, showSym(n.ch), x, y - 1, { color: P.text, size: 13, align: 'center', weight: 700, mono: true }); D.text(ctx, String(n.w), x, y + 22, { color: P.faint, size: 10, align: 'center', mono: true }); } else { D.dot(ctx, x, y, 12, fresh ? P.accent : P.surface2, P.accent, 1.5); D.text(ctx, String(n.w), x, y, { color: fresh ? P.bg : P.text, size: 11, align: 'center', weight: 700, mono: true }); } } if (n.ch === undefined) { nodes(n.l); nodes(n.r); } };
      nodes(root);
      D.text(ctx, `merges ${s.step} / ${merges.length}`, c.w - 10, 10, { color: P.faint, size: 10, align: 'right' });
    };
    s.step = build().merges.length;
    update();
  },
});

/* ========================================================== math-hamming == */
defineLab('math-hamming', {
  title: 'Hamming(7,4): find and fix a flipped bit',
  hint: 'Four data bits get three parity bits; each parity bit makes its circle hold an <b>even</b> number of 1s. Click the data bits to set a message, then <b>click a bit in the received row</b> to simulate noise. The failing circles point straight at the damaged bit.',
  mount(L) {
    const s = { d: [1, 0, 1, 1], noise: new Set() };
    const c = L.canvas(w => w < 520 ? 440 : 320);
    // positions 1..7: p1 p2 d1 p3 d2 d3 d4 ; circle A = {1,3,5,7}, B = {2,3,6,7}, C = {4,5,6,7}
    const encode = () => { const [d1, d2, d3, d4] = s.d; return [d1 ^ d2 ^ d4, d1 ^ d3 ^ d4, d1, d2 ^ d3 ^ d4, d2, d3, d4]; };
    const recv = () => encode().map((b, i) => s.noise.has(i) ? 1 - b : b);
    const syndrome = r => { const bit = (set) => set.reduce((t, p) => t ^ r[p - 1], 0); return [bit([1, 3, 5, 7]), bit([2, 3, 6, 7]), bit([4, 5, 6, 7])]; };
    L.button('Flip a random bit', () => { s.noise = new Set([Math.floor(Math.random() * 7)]); update(); });
    L.button('Flip two bits', () => { const a = Math.floor(Math.random() * 7); let b = Math.floor(Math.random() * 6); if (b >= a) b++; s.noise = new Set([a, b]); update(); });
    L.button('Clear noise', () => { s.noise.clear(); update(); });
    let hits = [];
    onTap(c, (x, y) => {
      const h = hits.find(q => x >= q.x && x <= q.x + q.w && y >= q.y && y <= q.y + q.h); if (!h) return;
      if (h.row === 'data') s.d[h.i] ^= 1; else s.noise.has(h.i) ? s.noise.delete(h.i) : s.noise.add(h.i);
      update();
    });
    const names = ['p₁', 'p₂', 'd₁', 'p₃', 'd₂', 'd₃', 'd₄'];
    function update() {
      const r = recv(), [a, b, cc] = syndrome(r), pos = a + 2 * b + 4 * cc;
      const fixed = [...r]; if (pos) fixed[pos - 1] ^= 1;
      const ok = fixed.join('') === encode().join('');
      L.stats([['sent', encode().join('')], ['received', r.join(''), s.noise.size ? 'err' : ''], ['syndrome (c₃ c₂ c₁)', `${cc}${b}${a} = ${pos}`, 'accent'],
        ['decoder says', pos ? `bit ${pos} (${names[pos - 1]}) is wrong` : 'no error'], ['after correction', ok ? 'message recovered ✓' : 'WRONG message ✗', ok ? 'ok' : 'err']]);
      L.insight(s.noise.size >= 2
        ? `<b>Two errors fool it.</b> The syndrome points at a third, innocent bit and the “correction” makes things worse. Hamming(7,4) has minimum distance 3: it corrects any 1 error, or detects (without correcting) 2. Adding one overall parity bit (SECDED, used in ECC memory) tells 1 and 2 errors apart.`
        : s.noise.size === 1 ? `Each circle whose parity is now odd is a “no” vote, each even circle a “yes”. The three answers, read as binary, <b>are the position</b> of the flipped bit: that is why the parity bits sit at positions 1, 2 and 4. Three check bits distinguish 8 cases: “no error” or one of 7 positions.`
          : `No noise: all three circles have even parity, so the syndrome is 000. Only 3 extra bits protect 4 data bits — ECC RAM, QR codes and deep-space links use the same idea with bigger codes.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, narrow = c.w < 520, r = recv(), [sa, sb, sc] = syndrome(r), sent = encode();
      hits = [];
      const cell = Math.min(40, ((narrow ? c.w : c.w * .5) - 40) / 7), rx = 16;
      const row = (label, bits, y, kind, marks) => {
        D.text(ctx, label, rx, y - 10, { color: P.dim, size: 11, weight: 650 });
        bits.forEach((b, i) => {
          const x = rx + i * cell, bad = marks && marks.has(i);
          fillRR(ctx, x + 2, y, cell - 4, cell - 4, 6, b ? P.alpha('accent', .7) : P.surface2, bad ? P.err : i === 0 || i === 1 || i === 3 ? P.alpha('ok', .8) : P.border, bad ? 2.4 : 1.2);
          D.text(ctx, String(b), x + cell / 2, y + (cell - 4) / 2, { color: b ? P.bg : P.dim, size: 14, align: 'center', mono: true, weight: 700 });
          D.text(ctx, names[i], x + cell / 2, y + cell + 6, { color: P.faint, size: 10, align: 'center' });
          if (kind) hits.push({ x: x + 2, y, w: cell - 4, h: cell - 4, i, row: kind });
        });
      };
      D.text(ctx, 'data (click to set)', rx, 14, { color: P.dim, size: 11, weight: 650 });
      s.d.forEach((b, i) => { const x = rx + i * cell; fillRR(ctx, x + 2, 22, cell - 4, cell - 4, 6, b ? P.alpha('accent', .7) : P.surface2, P.border); D.text(ctx, String(b), x + cell / 2, 22 + (cell - 4) / 2, { color: b ? P.bg : P.dim, size: 14, align: 'center', mono: true, weight: 700 }); hits.push({ x: x + 2, y: 22, w: cell - 4, h: cell - 4, i, row: 'data' }); });
      row('sent codeword (green = parity bits)', sent, 22 + cell + 30, null);
      row('received (click to flip a bit)', r, 22 + 2 * cell + 66, 'noise', s.noise);
      // the three circles
      const vx = narrow ? c.w / 2 : c.w * .72, vy = narrow ? 22 + 3 * cell + 160 : c.h / 2 + 4, R = Math.min(narrow ? 60 : 66, c.w * .12 + 20);
      const cen = [[vx - R * .5, vy - R * .35], [vx + R * .5, vy - R * .35], [vx, vy + R * .5]];
      [[sa, 'A: p₁'], [sb, 'B: p₂'], [sc, 'C: p₃']].forEach(([bad, l], k) => {
        ctx.beginPath(); ctx.arc(cen[k][0], cen[k][1], R, 0, TAU);
        ctx.fillStyle = bad ? P.alpha('err', .12) : P.alpha('ok', .05); ctx.fill();
        ctx.strokeStyle = bad ? P.err : P.alpha('ok', .8); ctx.lineWidth = bad ? 2.6 : 1.5; ctx.stroke();
        const lx = cen[k][0] + [-R * .55, R * .55, 0][k], ly = cen[k][1] + [-R * 1.14, -R * 1.14, R * 1.16][k];
        D.text(ctx, `${l} ${bad ? 'odd ✗' : 'even ✓'}`, lx, ly, { color: bad ? P.err : P.ok, size: 11, align: 'center', weight: 700 });
      });
      const spot = [[vx - R * .85, vy - R * .6], [vx + R * .85, vy - R * .6], [vx, vy - R * .55], [vx, vy + R * .95], [vx - R * .45, vy + R * .2], [vx + R * .45, vy + R * .2], [vx, vy - R * .05]];
      r.forEach((b, i) => { D.dot(ctx, spot[i][0], spot[i][1], 12, s.noise.has(i) ? P.alpha('err', .35) : P.surface2, s.noise.has(i) ? P.err : P.border, 1.4); D.text(ctx, String(b), spot[i][0], spot[i][1] - 1, { color: P.text, size: 12, align: 'center', mono: true, weight: 700 }); D.text(ctx, names[i], spot[i][0], spot[i][1] + 19, { color: P.faint, size: 9, align: 'center' }); });
    };
    update();
  },
});

/* ============================================================== math-dfa == */
defineLab('math-dfa', {
  title: 'A finite automaton reads a string',
  hint: 'A DFA has a finite set of states and one rule per (state, symbol). Type an input, press <b>Step</b> or <b>Run</b>, and follow the highlighted state. Double-ringed states accept.',
  mount(L) {
    const M = {
      div3: { name: 'binary number divisible by 3', alpha: '01', states: ['r0', 'r1', 'r2'], start: 0, acc: [0], d: (q, ch) => (2 * q + +ch) % 3, sample: '1001',
        tests: ['0', '11', '110', '1001', '111', '10010'], note: 'The state is the remainder so far. Reading bit b turns value v into 2v + b, so the remainder r becomes (2r + b) mod 3. Three states are enough to test divisibility of numbers of any length — the machine never stores the number itself.' },
      evena: { name: 'even number of a’s', alpha: 'ab', states: ['even', 'odd'], start: 0, acc: [0], d: (q, ch) => ch === 'a' ? 1 - q : q, sample: 'abbab',
        tests: ['', 'a', 'aa', 'abba', 'bab', 'aaab'], note: 'Two states remember one bit of history: the parity of a’s seen so far. That is exactly the memory a finite automaton has — a fixed number of states, no matter how long the input.' },
      ab: { name: 'contains “ab”', alpha: 'ab', states: ['start', 'saw a', 'found'], start: 0, acc: [2], d: (q, ch) => q === 2 ? 2 : ch === 'a' ? 1 : q === 1 ? 2 : 0, sample: 'bbaab',
        tests: ['ab', 'ba', 'bbb', 'aab', 'baaa', 'abab'], note: 'Substring search is a DFA: state = how much of the pattern you have matched so far. KMP and grep’s regex engines build exactly these machines, so each input character is examined once.' },
      end01: { name: 'ends in “01”', alpha: '01', states: ['q0', 'last 0', 'last 01'], start: 0, acc: [2], d: (q, ch) => ch === '0' ? 1 : q === 1 ? 2 : 0, sample: '11001',
        tests: ['01', '001', '010', '1101', '0', '10101'], note: 'The machine only needs to remember the last two symbols. Every regular expression can be turned into a DFA like this one; the regex 1*… is just a friendlier notation.' },
    };
    const s = { m: 'div3', input: M.div3.sample, i: 0, acc: 0 };
    L.stage.innerHTML = `<label class="mlab-in"><span>input</span><input type="text" spellcheck="false" maxlength="24"></label>`;
    const inp = L.stage.querySelector('input');
    const c = L.canvas(w => w < 520 ? 300 : 280);
    const box = document.createElement('div'); box.className = 'mlab-box'; L.stage.append(box);
    inp.value = s.input;
    inp.addEventListener('input', () => { s.input = inp.value; s.i = 0; update(); });
    L.seg('machine', Object.entries(M).map(([k, v]) => [k, v.name]), s.m, v => { s.m = v; s.input = inp.value = M[v].sample; s.i = 0; update(); });
    const run = L.loop(dt => { s.acc += dt; if (s.acc > .6) { s.acc = 0; if (s.i >= s.input.length) return false; s.i++; update(); } });
    L.playButton(run, ['Run', 'Pause'], () => { if (s.i >= s.input.length) s.i = 0; });
    L.button('Step', () => { run.stop(); if (s.i < s.input.length) s.i++; else s.i = 0; update(); });
    L.button('Reset', () => { run.stop(); s.i = 0; update(); });
    const trace = str => { const m = M[s.m], qs = [m.start]; for (const ch of str) { if (!m.alpha.includes(ch)) return null; qs.push(m.d(qs[qs.length - 1], ch)); } return qs; };
    function update() {
      const m = M[s.m], qs = trace(s.input);
      if (!qs) { L.stats([['error', `only the symbols ${[...m.alpha].join(' and ')} are allowed`, 'err']]); L.insight(''); L.redraw(); return; }
      const q = qs[s.i], done = s.i >= s.input.length, accept = m.acc.includes(qs[qs.length - 1]);
      L.stats([['read', `${s.i} / ${s.input.length}`], ['current state', m.states[q], 'accent'], done ? ['verdict', accept ? 'ACCEPT' : 'REJECT', accept ? 'ok' : 'err'] : null]);
      box.innerHTML = `<table class="mlab-table"><tr><th>test string</th><th>final state</th><th>verdict</th></tr>${m.tests.map(t => { const tq = trace(t), ok = m.acc.includes(tq[tq.length - 1]);
        return `<tr><td>${t === '' ? 'ε (empty)' : t}${s.m === 'div3' && t ? ` = ${parseInt(t, 2)}` : ''}</td><td>${m.states[tq[tq.length - 1]]}</td><td style="color:var(${ok ? '--ok' : '--err'})">${ok ? 'accept' : 'reject'}</td></tr>`; }).join('')}</table>`;
      L.insight(`${m.note} What no DFA can do: check balanced parentheses, because it would need unboundedly many states to count the open ones — that needs a stack (a pushdown automaton).`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, m = M[s.m], qs = trace(s.input) || [m.start], n = m.states.length;
      // tape
      const cw = Math.min(30, (c.w - 30) / Math.max(1, s.input.length)), tx = (c.w - cw * s.input.length) / 2;
      [...s.input].forEach((ch, i) => { fillRR(ctx, tx + i * cw + 1, 10, cw - 2, 26, 4, i < s.i ? P.alpha('dim', .15) : P.surface2, i === s.i ? P.accent : P.border, i === s.i ? 2 : 1); D.text(ctx, ch, tx + i * cw + cw / 2, 23, { color: i < s.i ? P.faint : P.text, size: 13, align: 'center', mono: true, weight: 700 }); });
      if (s.i < s.input.length) D.text(ctx, '▲ head', tx + s.i * cw + cw / 2, 46, { color: P.accent, size: 10, align: 'center' });
      // states on a line
      const y = c.h * .62, xs = m.states.map((_, i) => c.w * (i + 1) / (n + 1)), R = 24;
      const cur = qs[Math.min(s.i, qs.length - 1)], prev = s.i > 0 ? qs[s.i - 1] : null, lastCh = s.i > 0 ? s.input[s.i - 1] : null;
      const groups = new Map();
      m.states.forEach((_, q) => [...m.alpha].forEach(ch => { const t = m.d(q, ch), k = `${q}>${t}`; groups.set(k, [...(groups.get(k) || []), ch]); }));
      groups.forEach((chs, k) => {
        const [a, b] = k.split('>').map(Number), hot = prev === a && cur === b && chs.includes(lastCh);
        const col = hot ? P.accent : P.alpha('dim', .7), lw = hot ? 2.6 : 1.5, label = chs.join(',');
        if (a === b) {
          ctx.beginPath(); ctx.arc(xs[a], y - R - 14, 14, .75 * Math.PI, 2.25 * Math.PI); ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.stroke();
          D.arrow(ctx, xs[a] + 11, y - R - 5, xs[a] + 8, y - R + 1, col, lw, 7);
          D.text(ctx, label, xs[a], y - R - 36, { color: hot ? P.accent : P.dim, size: 12, align: 'center', mono: true, weight: 700 });
          return;
        }
        const dir = b > a ? 1 : -1, span = Math.abs(b - a), bend = (groups.has(`${b}>${a}`) ? 26 : 0) + (span > 1 ? 34 * span : 0);
        const mx = (xs[a] + xs[b]) / 2, my = y + (dir > 0 ? -bend : bend);
        ctx.beginPath(); ctx.moveTo(xs[a] + dir * R * .7, y + (dir > 0 ? -R * .6 : R * .6) * (bend ? 1 : 0)); ctx.quadraticCurveTo(mx, my, xs[b] - dir * R * .9, y + (dir > 0 ? -R * .5 : R * .5) * (bend ? 1 : 0));
        ctx.strokeStyle = col; ctx.lineWidth = lw; ctx.stroke();
        const ex = xs[b] - dir * R * .9, ey = y + (dir > 0 ? -R * .5 : R * .5) * (bend ? 1 : 0);
        D.arrow(ctx, ex - dir * 8, ey + (bend ? (dir > 0 ? -5 : 5) : 0), ex, ey, col, lw, 8);
        D.text(ctx, label, mx, (y + my) / 2 + (dir > 0 ? -8 : 8), { color: hot ? P.accent : P.dim, size: 12, align: 'center', mono: true, weight: 700 });
      });
      m.states.forEach((name, q) => {
        const on = q === cur;
        D.dot(ctx, xs[q], y, R, on ? P.alpha('accent', .8) : P.surface2, on ? P.accent : P.strong, 2);
        if (m.acc.includes(q)) D.dot(ctx, xs[q], y, R - 5, null, on ? P.bg : P.strong, 1.5);
        D.text(ctx, name, xs[q], y, { color: on ? P.bg : P.text, size: name.length > 4 ? 10 : 12, align: 'center', weight: 700, mono: true });
        if (q === m.start) D.arrow(ctx, xs[q] - R - 26, y, xs[q] - R - 2, y, P.dim, 1.8, 8);
      });
    };
    update();
  },
});

/* ========================================================= math-geometry == */
defineLab('math-geometry', {
  title: 'The cross product as a turn test',
  hint: 'Drag the points. The sign of the 2-D cross product tells left turn, right turn or straight — and that one test is enough for segment intersection, polygon area and convexity, with no angles or division.',
  mount(L) {
    const s = { mode: 'orient', pts: {
      orient: [[-2, -1], [1.5, -1.2], [0, 1.8]],
      cross: [[-2.5, -1.5], [2, 1.5], [-2, 1.8], [2.2, -1.4]],
      poly: [[-2.5, -1], [-.5, -2], [2, -1.2], [2.6, 1], [.3, 2.1], [-1.8, 1.4]],
    } };
    const c = L.canvas(w => Math.min(360, Math.max(280, w * .55)));
    L.seg('show', [['orient', 'orientation of 3 points'], ['cross', 'do two segments cross?'], ['poly', 'polygon area and convexity']], s.mode, v => { s.mode = v; update(); });
    let v = null;
    const P0 = () => s.pts[s.mode];
    L.drag(c, {
      hit: (x, y) => { if (!v) return null; const i = P0().findIndex(([px, py]) => Math.hypot(v.sx(px) - x, v.sy(py) - y) < 16); return i < 0 ? null : i; },
      move: (i, x, y) => { P0()[i] = [clamp(Math.round(v.ix(x) * 4) / 4, -3.5, 3.5), clamp(Math.round(v.iy(y) * 4) / 4, -2.6, 2.6)]; update(); },
    });
    const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    const sgn = x => Math.abs(x) < 1e-9 ? 0 : Math.sign(x);
    const turn = x => sgn(x) > 0 ? 'left (counter-clockwise)' : sgn(x) < 0 ? 'right (clockwise)' : 'straight (collinear)';
    function analyse() {
      const p = P0();
      if (s.mode === 'orient') return { c: cross(...p) };
      if (s.mode === 'cross') {
        const [a, b, cc, d] = p, d1 = cross(a, b, cc), d2 = cross(a, b, d), d3 = cross(cc, d, a), d4 = cross(cc, d, b);
        const hit = sgn(d1) * sgn(d2) < 0 && sgn(d3) * sgn(d4) < 0;
        const t = hit ? d3 / (d3 - d4) : null;
        return { d1, d2, d3, d4, hit, at: hit ? [a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])] : null };
      }
      let area2 = 0; p.forEach((q, i) => { const r = p[(i + 1) % p.length]; area2 += q[0] * r[1] - r[0] * q[1]; });
      const turns = p.map((q, i) => sgn(cross(q, p[(i + 1) % p.length], p[(i + 2) % p.length])));
      const convex = turns.every(t => t >= 0) || turns.every(t => t <= 0);
      return { area: area2 / 2, turns, convex };
    }
    function update() {
      const g = analyse();
      if (s.mode === 'orient') {
        L.stats([['cross(AB, AC)', fmtN(g.c, 2), 'accent'], ['turn A → B → C', turn(g.c), sgn(g.c) ? '' : 'err'], ['triangle area = |cross| / 2', fmtN(Math.abs(g.c) / 2, 2)]]);
        L.insight(`For vectors u = B − A and v = C − A, <b>cross(u, v) = uₓ·v_y − u_y·vₓ</b>. Positive: C is to the left of the line A→B; negative: to the right; zero: collinear. Its size is twice the triangle’s area (the parallelogram spanned by u and v). Only multiplications and subtractions, so it is exact on integer coordinates — no floating-point angles.`);
      } else if (s.mode === 'cross') {
        L.stats([['C, D on opposite sides of AB?', sgn(g.d1) * sgn(g.d2) < 0 ? 'yes' : 'no'], ['A, B on opposite sides of CD?', sgn(g.d3) * sgn(g.d4) < 0 ? 'yes' : 'no'],
          ['segments cross?', g.hit ? 'yes' : 'no', g.hit ? 'ok' : 'err'], g.at ? ['at', `(${fmtN(g.at[0], 2)}, ${fmtN(g.at[1], 2)})`] : null]);
        L.insight(`Two segments properly cross exactly when <b>each one’s endpoints lie on opposite sides of the other’s line</b> — four orientation tests. (Touching and collinear overlaps need the zero cases handled separately; that is where most geometry bugs live.)`);
      } else {
        L.stats([['shoelace area', fmtN(Math.abs(g.area), 2), 'accent'], ['vertex order', g.area > 0 ? 'counter-clockwise' : 'clockwise'], ['convex?', g.convex ? 'yes: every turn the same way' : 'no: a turn goes the other way', g.convex ? 'ok' : 'err']]);
        L.insight(`<b>Shoelace formula:</b> area = ½·|Σ (xᵢ·yᵢ₊₁ − xᵢ₊₁·yᵢ)| — the sum of signed triangle areas from the origin, where the outside parts cancel. A polygon is <b>convex</b> when all its turns have the same sign. Convex hulls, map clipping, collision detection and GIS all reduce to this orientation test.`);
      }
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, p = P0(), g = analyse();
      v = D.view(c, { x0: -3.6, x1: 3.6, y0: -2.7, y1: 2.7, pad: 10, equal: true });
      D.grid(ctx, v, P, 1);
      const path = (pts, close) => { ctx.beginPath(); pts.forEach(([x, y], i) => i ? ctx.lineTo(v.sx(x), v.sy(y)) : ctx.moveTo(v.sx(x), v.sy(y))); if (close) ctx.closePath(); };
      const lbl = 'ABCDEFGH';
      if (s.mode === 'orient') {
        path(p, true); ctx.fillStyle = P.alpha(sgn(g.c) > 0 ? 'ok' : sgn(g.c) < 0 ? 'err' : 'dim', .18); ctx.fill();
        D.arrow(ctx, v.sx(p[0][0]), v.sy(p[0][1]), v.sx(p[1][0]), v.sy(p[1][1]), P.series[0], 2.6, 11);
        D.arrow(ctx, v.sx(p[0][0]), v.sy(p[0][1]), v.sx(p[2][0]), v.sy(p[2][1]), P.series[1], 2.6, 11);
        const dx = p[1][0] - p[0][0], dy = p[1][1] - p[0][1];
        ctx.save(); ctx.setLineDash([5, 5]); D.line(ctx, v.sx(p[0][0] - dx * 3), v.sy(p[0][1] - dy * 3), v.sx(p[0][0] + dx * 3), v.sy(p[0][1] + dy * 3), P.alpha('dim', .5), 1); ctx.restore();
      } else if (s.mode === 'cross') {
        D.line(ctx, v.sx(p[0][0]), v.sy(p[0][1]), v.sx(p[1][0]), v.sy(p[1][1]), P.series[0], 3);
        D.line(ctx, v.sx(p[2][0]), v.sy(p[2][1]), v.sx(p[3][0]), v.sy(p[3][1]), P.series[1], 3);
        if (g.at) D.dot(ctx, v.sx(g.at[0]), v.sy(g.at[1]), 7, P.ok, P.bg, 2);
      } else {
        path(p, true); ctx.fillStyle = P.alpha(g.convex ? 'accent' : 'err', .16); ctx.fill(); ctx.strokeStyle = P.accent; ctx.lineWidth = 2; ctx.stroke();
        p.forEach((q, i) => { if (g.turns[(i + p.length - 1) % p.length] === -Math.sign(g.area)) { const r = p[i]; D.dot(ctx, v.sx(r[0]), v.sy(r[1]), 16, null, P.err, 2); } });
      }
      p.forEach(([x, y], i) => { D.dot(ctx, v.sx(x), v.sy(y), 8, P.accent, P.bg, 2); D.text(ctx, lbl[i], v.sx(x) + 12, v.sy(y) - 12, { color: P.text, size: 13, weight: 700 }); });
    };
    update();
  },
});
}
