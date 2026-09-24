/* ============================================================================
   Interactive labs: transformers, LLM training and serving, RAG and agents.
   Requires viz.js.
   ========================================================================= */
'use strict';

defineLab('attention', {
  title: 'Self-attention: who looks at whom',
  hint: 'Click a word to make it the query. Line thickness is its attention weight on every other word.',
  mount(L, opts) {
    const tok = ['The', 'animal', "didn't", 'cross', 'the', 'street', 'because', 'it', 'was', 'tired'];
    const n = tok.length;
    const heads = {
      meaning: (() => {
        const m = Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => i === j ? 1 : 0));
        [[7, 1, 4.2], [7, 5, 2.3], [9, 1, 3.3], [9, 7, 2.7], [3, 5, 3], [3, 1, 2.3], [5, 3, 2.6], [1, 9, 2.1], [2, 3, 2.7], [8, 9, 2.5], [6, 9, 1.9], [0, 1, 2.6], [4, 5, 2.9], [8, 7, 1.8]]
          .forEach(([i, j, v]) => { m[i][j] = v; });
        return m;
      })(),
      previous: Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => j === i - 1 ? 4 : i === j ? 1.5 : 0)),
      local: Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => 1.5 - .9 * Math.abs(i - j))),
    };
    const s = { q: 7, head: 'meaning', temp: 1, scaled: true, causal: !!opts.causal };
    const c = L.canvas(w => Math.min(430, Math.max(360, w * .66)));
    let geo = null;
    L.seg('head', [['meaning', 'Head 1: meaning'], ['previous', 'Head 2: previous word'], ['local', 'Head 3: nearby words']], s.head, v => { s.head = v; changed(); });
    L.slider('softmax temperature', { min: .3, max: 3, step: .05, value: s.temp, fmt: v => v.toFixed(2) }, v => { s.temp = v; changed(); });
    L.toggle('Divide by √dₖ', s.scaled, v => { s.scaled = v; changed(); });
    L.toggle('Causal mask (decoder / GPT)', s.causal, v => { s.causal = v; changed(); });
    const weights = i => {
      const row = heads[s.head][i].map((v, j) => s.causal && j > i ? -Infinity : v * (s.scaled ? 1 : 3.5));
      return softmaxT(row, s.temp);
    };
    L.drag(c, {
      down: (x, y) => {
        if (!geo) return;
        if (y < geo.rowY + 16) {
          const j = geo.tokX.findIndex(tx => Math.abs(tx - x) < geo.tw / 2);
          if (j >= 0) { s.q = j; changed(); }
        } else if (x > geo.hx && y > geo.hy) {
          const i = Math.floor((y - geo.hy) / geo.cell);
          if (i >= 0 && i < n) { s.q = i; changed(); }
        }
      },
    });
    function changed() {
      L.redraw();
      const w = weights(s.q), top = w.map((v, j) => [v, j]).sort((a, b) => b[0] - a[0]).slice(0, 3);
      L.stats([['query', `“${tok[s.q]}”`, 'accent'], ...top.map(([v, j]) => [`→ ${tok[j]}`, `${Math.round(v * 100)}%`])]);
      const [bw, bj] = top[0];
      L.insight(!s.scaled && bw > .9 ? `<b>Without ÷√dₖ the scores are huge</b>, softmax saturates, and “${tok[bj]}” takes ${Math.round(bw * 100)}% while everything else gets ≈ 0. The gradient to the other words vanishes.`
        : s.causal && s.q === 0 ? '<b>The first token can only see itself</b> under a causal mask. GPT generates left to right, so a token may never attend to the future.'
        : s.head === 'meaning' && s.q === 7 ? `<b>“it” puts ${Math.round(weights(7)[1] * 100)}% of its attention on “animal”.</b> That is how the model works out what “it” refers to. The new vector for “it” is this weighted blend of the value vectors.`
        : s.head === 'previous' ? '<b>A previous-token head.</b> Real models learn heads like this; combined with others they form “induction heads” that copy patterns.'
        : s.temp > 2 ? '<b>High temperature flattens the weights</b> towards uniform, so every word contributes about equally.'
        : `<b>Row “${tok[s.q]}” of the attention matrix</b> is highlighted below. Every row is a softmax, so it sums to 1. Multi-head attention runs several of these in parallel, each free to track a different relation.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, tw = (c.w - 20) / n, rowY = 26, w = weights(s.q);
      const tokX = tok.map((_, j) => 10 + tw * (j + .5));
      const arcTop = rowY + 16, hgt = Math.min(150, c.h * .36);
      tok.forEach((t, j) => {
        const on = j === s.q;
        ctx.fillStyle = on ? P.accent : P.alpha('accent', clamp(w[j] * 1.4, .06, .9));
        D.rrect(ctx, tokX[j] - tw / 2 + 3, rowY - 13, tw - 6, 26, 7); ctx.fill();
        D.text(ctx, t, tokX[j], rowY, { color: on || w[j] > .45 ? P.surface : P.text, size: Math.min(13, tw * .2), align: 'center', weight: on ? 700 : 550 });
      });
      tok.forEach((_, j) => {
        if (j === s.q || w[j] < .005) return;
        const x1 = tokX[s.q], x2 = tokX[j], mid = (x1 + x2) / 2, depth = arcTop + Math.min(hgt, 20 + Math.abs(x2 - x1) * .5);
        ctx.beginPath(); ctx.moveTo(x1, arcTop); ctx.quadraticCurveTo(mid, depth, x2, arcTop);
        ctx.strokeStyle = P.alpha('accent', .25 + .75 * w[j]); ctx.lineWidth = 1 + 12 * w[j]; ctx.lineCap = 'round'; ctx.stroke();
        if (w[j] > .06) D.text(ctx, `${Math.round(w[j] * 100)}%`, mid, Math.min(depth - 6, arcTop + hgt - 4), { color: P.dim, size: 10.5, align: 'center', mono: true });
      });
      const hy = arcTop + hgt + 34, cell = Math.min((c.h - hy - 8) / n, 26), hx = c.w / 2 - cell * n / 2 + 30;
      geo = { tokX, tw, rowY, hx, hy, cell };
      D.text(ctx, 'attention matrix (rows = queries, columns = keys)', 10, hy - 8, { color: P.dim, size: 11 });
      for (let i = 0; i < n; i++) {
        const wi = weights(i);
        D.text(ctx, tok[i], hx - 6, hy + (i + .5) * cell, { color: i === s.q ? P.accent : P.faint, size: 10, align: 'right', weight: i === s.q ? 700 : 400 });
        for (let j = 0; j < n; j++) {
          const masked = s.causal && j > i;
          ctx.fillStyle = masked ? P.alpha('faint', .08) : P.alpha('accent', clamp(wi[j] * 1.1, .03, 1));
          ctx.fillRect(hx + j * cell + .5, hy + i * cell + .5, cell - 1, cell - 1);
        }
      }
      ctx.strokeStyle = P.text; ctx.lineWidth = 1.5; ctx.strokeRect(hx, hy + s.q * cell, cell * n, cell);
    };
    changed();
  },
});

defineLab('embeddings', {
  title: 'Word vectors: meaning as geometry',
  hint: 'Pick an analogy to watch the vector arithmetic, or click any word to see its nearest neighbours.',
  mount(L) {
    const W = {
      man: [-.5, -1], woman: [2, -1], king: [-.5, 2.2], queen: [2, 2.2], boy: [-.8, -2.6], girl: [1.7, -2.6], prince: [-.9, .8], princess: [1.6, .8],
      France: [6, .5], Paris: [6, 2.7], Italy: [8.6, .3], Rome: [8.6, 2.5], Japan: [9.8, -2.4], Tokyo: [9.8, -.2],
      apple: [-4, 3.2], banana: [-3, 4], mango: [-4.3, 4.3], dog: [-3.6, -2.6], cat: [-2.8, -3.2],
    };
    const group = w => ['France', 'Paris', 'Italy', 'Rome', 'Japan', 'Tokyo'].includes(w) ? 2 : ['apple', 'banana', 'mango'].includes(w) ? 1 : ['dog', 'cat'].includes(w) ? 3 : 0;
    const AN = { royal: ['king', 'man', 'woman'], capital: ['Paris', 'France', 'Italy'], tokyo: ['Tokyo', 'Japan', 'France'] };
    const s = { an: 'royal', t: 1, sel: null };
    const c = L.canvas(w => Math.min(360, w * .6));
    let v = null;
    L.seg('analogy', [['royal', 'king − man + woman'], ['capital', 'Paris − France + Italy'], ['tokyo', 'Tokyo − Japan + France']], s.an, x => { s.an = x; s.sel = null; animate(); });
    L.button('Replay', () => animate(), 'primary');
    L.drag(c, {
      down: (x, y) => {
        if (!v) return;
        const hit = Object.entries(W).find(([, [a, b]]) => Math.hypot(v.sx(a) - x, v.sy(b) - y) < 16);
        s.sel = hit ? hit[0] : null; changed();
      },
    });
    const result = () => { const [a, b, cc] = AN[s.an].map(k => W[k]); return [a[0] - b[0] + cc[0], a[1] - b[1] + cc[1]]; };
    const nearest = (p, exclude = []) => Object.entries(W).filter(([k]) => !exclude.includes(k)).map(([k, q]) => [k, Math.hypot(q[0] - p[0], q[1] - p[1])]).sort((a, b) => a[1] - b[1]);
    function animate() { s.t = 0; L.tween(1800, t => { s.t = t; L.redraw(); }, changed); changed(); }
    function changed() {
      L.redraw();
      if (s.sel) {
        const nn = nearest(W[s.sel], [s.sel]).slice(0, 3);
        L.stats([['word', s.sel, 'accent'], ...nn.map(([k, d]) => [`near ${k}`, fmtN(d, 2)])]);
        L.insight(`<b>Words used in similar contexts end up close together.</b> Word2Vec never sees definitions, only which words appear near which; this map is the result.`);
        return;
      }
      const [a, b, cc] = AN[s.an], res = result(), [best, d] = nearest(res, [a, b, cc])[0];
      L.stats([['a − b + c', `${a} − ${b} + ${cc}`], ['lands nearest', best, 'accent'], ['distance', fmtN(d, 2)]]);
      L.insight(`<b>${a} − ${b} isolates a direction</b> (${s.an === 'royal' ? '“royalty”' : '“capital city of”'}). Adding it to ${cc} lands next to <b>${best}</b>. Real embeddings have hundreds of dimensions, but the arithmetic works the same way.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      v = D.view(c, { x0: -5.4, x1: 11, y0: -3.8, y1: 5, pad: 14, equal: true });
      D.grid(ctx, v, P, 1);
      if (!s.sel) {
        const [a, b, cc] = AN[s.an].map(k => W[k]), res = result();
        const t1 = clamp(s.t / .4, 0, 1), t2 = clamp((s.t - .4) / .4, 0, 1), t3 = clamp((s.t - .8) / .2, 0, 1);
        D.arrow(ctx, v.sx(b[0]), v.sy(b[1]), v.sx(lerp(b[0], a[0], t1)), v.sy(lerp(b[1], a[1], t1)), P.series[1], 3, 12);
        if (t2 > 0) {
          const dx = a[0] - b[0], dy = a[1] - b[1];
          D.arrow(ctx, v.sx(cc[0]), v.sy(cc[1]), v.sx(cc[0] + dx * t2), v.sy(cc[1] + dy * t2), P.accent, 3.2, 12);
        }
        if (t3 > 0) { D.dot(ctx, v.sx(res[0]), v.sy(res[1]), 16 * t3, null, P.accent, 2.5); D.dot(ctx, v.sx(res[0]), v.sy(res[1]), 4, P.accent); }
      } else {
        nearest(W[s.sel], [s.sel]).slice(0, 3).forEach(([k]) => D.line(ctx, v.sx(W[s.sel][0]), v.sy(W[s.sel][1]), v.sx(W[k][0]), v.sy(W[k][1]), P.alpha('accent', .7), 2, [4, 4]));
      }
      Object.entries(W).forEach(([k, [x, y]]) => {
        const col = P.series[[0, 2, 4, 5][group(k)]];
        D.dot(ctx, v.sx(x), v.sy(y), k === s.sel ? 7 : 5, col, P.surface, 1.5);
        D.text(ctx, k, v.sx(x) + 8, v.sy(y) - 8, { color: k === s.sel ? P.accent : P.text, size: 12, weight: k === s.sel ? 700 : 550 });
      });
    };
    changed();
  },
});

defineLab('bpe', {
  title: 'Byte-pair encoding, merge by merge',
  hint: 'Start from characters. Each merge fuses the most frequent adjacent pair into a new token. Type your own text.',
  mount(L) {
    const s = { text: 'low lower lowest newer newest wider widest slow slower slowest', m: 0, merges: [] };
    const input = document.createElement('input');
    input.className = 'lab-input';
    input.value = s.text;
    input.setAttribute('aria-label', 'Text to tokenize');
    L.stage.append(input);
    const box = document.createElement('div');
    box.className = 'bpe-box';
    L.stage.append(box);
    const mS = L.slider('merges applied', { min: 0, max: 30, step: 1, value: 0 }, v => { s.m = v; render(); });
    let acc = 0;
    const play = L.loop(dt => { acc += dt; if (acc > .6) { acc = 0; if (s.m >= s.merges.length) return false; s.m++; mS.set(s.m, true); render(true); } });
    L.playButton(play, ['Play merges', 'Pause'], () => { if (s.m >= s.merges.length) { s.m = 0; mS.set(0, true); } });
    input.addEventListener('input', () => { s.text = input.value; learn(); });
    const words = () => s.text.toLowerCase().split(/\s+/).filter(Boolean).map(w => w.replace(/[^\p{L}\p{N}]/gu, '')).filter(Boolean);
    const applyMerges = (syms, k) => {
      for (let i = 0; i < k; i++) {
        const [a, b] = s.merges[i];
        for (let j = 0; j < syms.length - 1; j++) if (syms[j] === a && syms[j + 1] === b) { syms.splice(j, 2, a + b); }
      }
      return syms;
    };
    function learn() {
      const freq = new Map();
      words().forEach(w => freq.set(w, (freq.get(w) || 0) + 1));
      let vocab = [...freq].map(([w, f]) => [[...w, '·'], f]);
      s.merges = [];
      for (let it = 0; it < 30; it++) {
        const pairs = new Map();
        vocab.forEach(([syms, f]) => { for (let j = 0; j < syms.length - 1; j++) { const k = `${syms[j]} ${syms[j + 1]}`; pairs.set(k, (pairs.get(k) || 0) + f); } });
        const best = [...pairs].sort((a, b) => b[1] - a[1])[0];
        if (!best || best[1] < 2) break;
        const [a, b] = best[0].split(' ');
        s.merges.push([a, b, best[1]]);
        vocab = vocab.map(([syms, f]) => {
          const out = [];
          for (let j = 0; j < syms.length; j++) { if (syms[j] === a && syms[j + 1] === b) { out.push(a + b); j++; } else out.push(syms[j]); }
          return [out, f];
        });
      }
      mS.input.max = Math.max(1, s.merges.length);
      s.m = Math.min(s.m, s.merges.length);
      mS.set(s.m, true);
      render();
    }
    const hue = t => { let h = 0; for (const ch of t) h = (h * 31 + ch.codePointAt(0)) % 360; return h; };
    function render(pop) {
      const ws = words(), P = labPalette(L.fig);
      const newest = s.m ? s.merges[s.m - 1][0] + s.merges[s.m - 1][1] : null;
      let tokens = 0, chars = 0;
      const vocab = new Set();
      box.innerHTML = `<div class="bpe-words">${ws.map(w => {
        const syms = applyMerges([...w, '·'], s.m);
        tokens += syms.length; chars += w.length + 1;
        syms.forEach(t => vocab.add(t));
        return `<span class="bpe-word">${syms.map(t => `<span class="bpe-tok${t === newest ? ` is-new${pop ? ' pop' : ''}` : ''}" style="--h:${hue(t)}">${esc(t)}</span>`).join('')}</span>`;
      }).join('')}</div>
      <ol class="bpe-merges">${s.merges.slice(Math.max(0, s.m - 5), s.m).map(([a, b, f], i, arr) =>
        `<li${i === arr.length - 1 ? ' class="is-new"' : ''}><span>#${s.m - arr.length + i + 1}</span><code>${esc(a)}</code> + <code>${esc(b)}</code> → <code>${esc(a + b)}</code><em>seen ${f}×</em></li>`).join('') || '<li class="bpe-empty">No merges yet: every character is its own token.</li>'}</ol>`;
      L.stats([['tokens', tokens, 'accent'], ['characters (incl. ·)', chars], ['compression', `${fmtN(chars / Math.max(1, tokens), 2)}×`], ['merges learned', s.merges.length]]);
      L.insight(s.m === 0 ? '<b>Every character is a token</b> (· marks the end of a word). Long sequences, but no unknown words ever.'
        : s.m >= s.merges.length ? `<b>All ${s.merges.length} useful merges applied.</b> Frequent pieces such as “est·” and “er·” became single tokens, while rarer words stay split into subwords. That is how GPT tokenizers handle words they have never seen.`
        : `<b>Merge ${s.m}: “${esc(s.merges[s.m - 1][0])}” + “${esc(s.merges[s.m - 1][1])}”</b> was the most frequent adjacent pair (${s.merges[s.m - 1][2]}×), so it becomes a new vocabulary entry.`);
      void P;
    }
    learn();
  },
});

defineLab('softmax', {
  title: 'Temperature, top-k and top-p sampling',
  hint: 'The model scored every candidate for the next word. Reshape the distribution, then sample from it.',
  mount(L) {
    const r = rng(77);
    const cand = [['mat', 3.2], ['floor', 2.5], ['sofa', 2.2], ['bed', 1.6], ['roof', .9], ['moon', -.4], ['piano', -1.3]];
    const s = { T: 1, k: 7, p: 1, counts: cand.map(() => 0), drawn: [], queue: 0 };
    const c = L.canvas(w => Math.min(310, Math.max(270, w * .45)));
    L.slider('temperature', { min: .1, max: 2.5, step: .05, value: s.T, fmt: v => v.toFixed(2) }, v => { s.T = v; changed(true); });
    L.slider('top-k', { min: 1, max: 7, step: 1, value: s.k }, v => { s.k = v; changed(true); });
    L.slider('top-p (nucleus)', { min: .1, max: 1, step: .05, value: s.p, fmt: v => v.toFixed(2) }, v => { s.p = v; changed(true); });
    let acc = 0;
    const sampler = L.loop(dt => {
      acc += dt;
      if (acc < .07) return;
      acc = 0;
      const d = dist(), u = r();
      let cum = 0, pick = d.findIndex(x => (cum += x) >= u);
      if (pick < 0) pick = d.findIndex(x => x > 0);
      s.counts[pick]++; s.drawn.push(cand[pick][0]);
      changed();
      if (--s.queue <= 0) return false;
    });
    L.button('Sample 30 next words', () => { s.queue = 30; sampler.start(); }, 'primary');
    L.button('Clear', () => { s.counts = cand.map(() => 0); s.drawn = []; changed(); });
    function dist() {
      const probs = softmaxT(cand.map(x => x[1]), s.T);
      const order = probs.map((p, i) => [p, i]).sort((a, b) => b[0] - a[0]);
      const keep = new Set();
      let cum = 0;
      for (const [p, i] of order) { if (keep.size >= s.k) break; if (cum >= s.p && keep.size) break; keep.add(i); cum += p; }
      const kept = probs.map((p, i) => keep.has(i) ? p : 0), sum = kept.reduce((a, b) => a + b, 0);
      return kept.map(p => p / sum);
    }
    function changed(reset) {
      if (reset) { s.counts = cand.map(() => 0); s.drawn = []; }
      L.redraw();
      const d = dist(), H = -d.reduce((a, p) => a + (p > 0 ? p * Math.log2(p) : 0), 0);
      const top = d.indexOf(Math.max(...d));
      L.stats([['most likely', `${cand[top][0]} ${Math.round(d[top] * 100)}%`, 'accent'], ['candidates kept', d.filter(x => x > 0).length], ['entropy', `${fmtN(H, 2)} bits`], ['perplexity', fmtN(2 ** H, 2)]]);
      L.insight(s.T < .35 ? '<b>Low temperature ≈ greedy decoding.</b> “mat” wins nearly every time: safe, repetitive, and a good fit for code or extraction.'
        : s.T > 1.6 && s.k === 7 && s.p === 1 ? '<b>High temperature flattens the distribution.</b> Even “piano” gets picked: creative, but prone to nonsense. Top-k or top-p cut off that long tail.'
        : s.p < 1 ? `<b>Top-p keeps the smallest set of words whose probability adds up to ${s.p.toFixed(2)}</b>, then renormalises. The set grows when the model is unsure and shrinks when it is confident.`
        : s.k < 7 ? `<b>Top-k keeps only the ${s.k} best candidates</b>, however flat or peaked the distribution is.`
        : '<b>Softmax(logits / T).</b> Temperature divides the scores before softmax: below 1 sharpens, above 1 flattens. Perplexity is the “effective number of choices”.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, d = dist(), total = s.counts.reduce((a, b) => a + b, 0);
      const rowH = (c.h - 58) / cand.length, labelW = 70, barX = labelW + 14, barW = c.w - barX - 70;
      D.text(ctx, 'The cat sat on the …', 10, 14, { color: P.dim, size: 12.5, weight: 600 });
      if (s.drawn.length) D.text(ctx, s.drawn.slice(-9).join(' · '), c.w - 10, 14, { color: P.accent, size: 11.5, align: 'right', mono: true });
      cand.forEach(([w, logit], i) => {
        const y = 34 + i * rowH, cut = d[i] === 0;
        D.text(ctx, w, labelW, y + rowH / 2, { color: cut ? P.faint : P.text, size: 13, align: 'right', weight: 600 });
        ctx.fillStyle = P.surface2; D.rrect(ctx, barX, y + 4, barW, rowH - 8, 5); ctx.fill();
        const pw = (cut ? softmaxT(cand.map(x => x[1]), s.T)[i] : d[i]) * barW;
        ctx.fillStyle = cut ? P.alpha('faint', .25) : P.accent; D.rrect(ctx, barX, y + 4, Math.max(2, pw), rowH - 8, 5); ctx.fill();
        if (cut) D.line(ctx, barX, y + rowH / 2, barX + Math.max(20, pw), y + rowH / 2, P.faint, 1.4);
        if (total) { const cw = s.counts[i] / total * barW; ctx.strokeStyle = P.series[0]; ctx.lineWidth = 2; D.rrect(ctx, barX, y + 2, Math.max(0, cw), rowH - 4, 5); ctx.stroke(); }
        D.text(ctx, cut ? 'cut' : `${(d[i] * 100).toFixed(1)}%`, barX + barW + 8, y + rowH / 2, { color: cut ? P.faint : P.text, size: 11.5, mono: true });
        D.text(ctx, `logit ${logit}`, barX + 8, y + rowH / 2, { color: pw > 90 ? P.surface : P.faint, size: 10, mono: true });
      });
      if (total) D.text(ctx, `blue outline: share of ${total} samples`, 10, c.h - 10, { color: P.series[0], size: 11 });
    };
    changed();
  },
});

defineLab('posenc', {
  title: 'Sinusoidal positional encoding',
  hint: 'Each row is one dimension, each column one position. Hover to read a dimension’s wave and how similar positions are.',
  mount(L) {
    const POS = 64;
    const s = { d: 32, hp: 20, hd: 4 };
    const c = L.canvas(w => Math.min(390, w * .66));
    let geo = null;
    L.seg('d_model', [[16, '16'], [32, '32'], [64, '64']], s.d, v => { s.d = v; s.hd = Math.min(s.hd, v - 1); changed(); });
    const pe = (p, i) => { const k = Math.floor(i / 2), f = 1 / 10000 ** (2 * k / s.d); return i % 2 ? Math.cos(p * f) : Math.sin(p * f); };
    L.drag(c, {
      hover: (x, y) => {
        if (!geo || x == null) return;
        const p = Math.floor((x - geo.x) / geo.cw), i = Math.floor((y - geo.y) / geo.ch);
        if (p >= 0 && p < POS && i >= 0 && i < s.d) { s.hp = p; s.hd = i; changed(); }
      },
    });
    function changed() {
      L.redraw();
      const k = Math.floor(s.hd / 2), wl = TAU * 10000 ** (2 * k / s.d);
      L.stats([['position', s.hp, 'accent'], ['dimension', s.hd], ['wavelength', `${fmtN(wl, 1)} positions`]]);
      L.insight(s.hd < 4 ? '<b>Low dimensions oscillate fast</b>, like the seconds hand of a clock: they tell neighbouring positions apart.'
        : '<b>Higher dimensions change slowly</b>, like the hour hand: they encode coarse position. Together every position gets a unique pattern, and the dot product of two encodings depends mostly on their distance, which is what the lower-right plot shows. RoPE uses the same frequencies but rotates Q and K instead of adding a vector.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, heatH = c.h * .56, x0 = 36, y0 = 18, cw = (c.w - x0 - 10) / POS, ch = (heatH - y0) / s.d;
      geo = { x: x0, y: y0, cw, ch };
      const pos = P.rgb('accent'), neg = P.rgb(P.series[0]), mid = P.rgb('surface');
      for (let p = 0; p < POS; p++) for (let i = 0; i < s.d; i++) {
        const v = pe(p, i), col = (v > 0 ? pos : neg).map((cc, k) => Math.round(lerp(mid[k], cc, Math.abs(v))));
        ctx.fillStyle = `rgb(${col.join(',')})`;
        ctx.fillRect(x0 + p * cw, y0 + i * ch, cw + .4, ch + .4);
      }
      ctx.strokeStyle = P.text; ctx.lineWidth = 1.2;
      ctx.strokeRect(x0, y0 + s.hd * ch, POS * cw, ch);
      ctx.strokeRect(x0 + s.hp * cw, y0, cw, s.d * ch);
      D.text(ctx, 'position →', c.w - 10, 9, { color: P.dim, size: 10.5, align: 'right' });
      D.text(ctx, 'dim', 4, y0 + 6, { color: P.dim, size: 10.5 });
      const half = (c.w - 30) / 2, by = heatH + 14, bh = c.h - by - 22;
      const v1 = D.view({ w: half, h: bh }, { x0: 0, x1: POS - 1, y0: -1.1, y1: 1.1, pad: 8, padL: 26, padB: 16 });
      ctx.save(); ctx.translate(0, by);
      D.axes(ctx, v1, P, { xTicks: [0, 32, 63], yTicks: [-1, 1] });
      D.curve(ctx, v1, p => pe(p, s.hd), P.accent, 2.2, 300);
      D.dot(ctx, v1.sx(s.hp), v1.sy(pe(s.hp, s.hd)), 4.5, P.accent);
      D.text(ctx, `dimension ${s.hd} across positions`, v1.sx(0) + 4, 2, { color: P.dim, size: 10.5, base: 'top' });
      ctx.restore();
      const sims = Array.from({ length: POS }, (_, q) => { let sum = 0; for (let i = 0; i < s.d; i++) sum += pe(s.hp, i) * pe(q, i); return sum / (s.d / 2); });
      const v2 = D.view({ w: half, h: bh }, { x0: 0, x1: POS - 1, y0: Math.min(...sims) - .05, y1: 1.05, pad: 8, padL: 26, padB: 16 });
      ctx.save(); ctx.translate(half + 20, by);
      D.axes(ctx, v2, P, { xTicks: [0, 32, 63], yTicks: [0, 1] });
      ctx.beginPath(); sims.forEach((y, q) => q ? ctx.lineTo(v2.sx(q), v2.sy(y)) : ctx.moveTo(v2.sx(q), v2.sy(y)));
      ctx.strokeStyle = P.series[0]; ctx.lineWidth = 2; ctx.stroke();
      D.line(ctx, v2.sx(s.hp), v2.sy(v2.y0), v2.sx(s.hp), v2.sy(v2.y1), P.faint, 1, [3, 3]);
      D.text(ctx, `similarity to position ${s.hp}`, v2.sx(0) + 4, 2, { color: P.dim, size: 10.5, base: 'top' });
      ctx.restore();
    };
    changed();
  },
});

defineLab('scaling', {
  title: 'Scaling laws: model size vs data at fixed compute',
  hint: 'Chinchilla’s fitted loss L(N, D). With a fixed compute budget C ≈ 6·N·D, a bigger model means fewer tokens.',
  mount(L) {
    const E = 1.69, A = 406.4, B = 410.7, al = .34, be = .28;
    const loss = (N, D) => E + A / N ** al + B / D ** be;
    const s = { N: 7e9, D: 1.4e11 };
    const c = L.canvas(w => Math.min(320, w * .54));
    L.slider('parameters N', { min: 1e8, max: 1e12, log: true, value: s.N, fmt: fmtBig }, v => { s.N = v; changed(); });
    L.slider('training tokens D', { min: 1e9, max: 1e13, log: true, value: s.D, fmt: fmtBig }, v => { s.D = v; changed(); });
    L.button('Make it compute-optimal', () => {
      const C = 6 * s.N * s.D, opt = best(C), n0 = Math.log(s.N), d0 = Math.log(s.D);
      L.tween(700, t => { s.N = Math.exp(lerp(n0, Math.log(opt.N), t)); s.D = C / (6 * s.N); changed(); });
    }, 'primary');
    const best = C => {
      let b = null;
      for (let e = 7; e <= 13; e += .01) { const N = 10 ** e, D = C / (6 * N); const l = loss(N, D); if (!b || l < b.l) b = { N, D, l }; }
      return b;
    };
    function changed() {
      L.redraw();
      const C = 6 * s.N * s.D, opt = best(C), ratio = s.D / s.N;
      L.stats([['loss', fmtN(loss(s.N, s.D), 3), 'accent'], ['compute', `${fmtN(C, 1)} FLOPs`], ['tokens per parameter', fmtN(ratio, 1)], ['optimal at this budget', `${fmtBig(opt.N)} params, ${fmtBig(opt.D)} tokens`]]);
      L.insight(ratio < 8 ? `<b>Under-trained:</b> ${fmtN(ratio, 1)} tokens per parameter. For the same compute a ${fmtBig(opt.N)} model on more data reaches lower loss. GPT-3 (175B on 300B tokens) sat here.`
        : ratio > 60 ? `<b>Over-trained for compute:</b> ${fmtN(ratio, 0)} tokens per parameter costs more to train than necessary, but the smaller model is cheaper for every future request. LLaMA-style models deliberately do this.`
        : '<b>Near compute-optimal.</b> Chinchilla found roughly 20 tokens per parameter minimises loss for a given budget.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, C = 6 * s.N * s.D;
      const curves = [C / 10, C, C * 10];
      const pts = curves.map(cc => Array.from({ length: 121 }, (_, i) => { const e = 7.5 + i * .04, N = 10 ** e; return [e, loss(N, cc / (6 * N))]; }));
      const all = pts.flat().map(p => p[1]).filter(y => y < 6);
      const v = D.view(c, { x0: 7.5, x1: 12.3, y0: Math.min(...all) - .05, y1: Math.min(4.5, Math.max(...all)), pad: 14, padL: 38, padB: 26 });
      D.axes(ctx, v, P, { xTicks: [8, 9, 10, 11, 12], fmtX: t => fmtBig(10 ** t), yTicks: [2, 2.5, 3, 3.5, 4].filter(t => t > v.y0 && t < v.y1), xLabel: 'model size (parameters)', yLabel: 'loss' });
      ctx.save(); ctx.beginPath(); ctx.rect(v.sx(v.x0), v.sy(v.y1), v.sx(v.x1) - v.sx(v.x0), v.sy(v.y0) - v.sy(v.y1)); ctx.clip();
      pts.forEach((line, k) => {
        ctx.beginPath(); line.forEach(([x, y], i) => i ? ctx.lineTo(v.sx(x), v.sy(y)) : ctx.moveTo(v.sx(x), v.sy(y)));
        ctx.strokeStyle = k === 1 ? P.accent : P.alpha('faint', .6); ctx.lineWidth = k === 1 ? 2.6 : 1.4; ctx.stroke();
        const b = best(curves[k]);
        D.dot(ctx, v.sx(Math.log10(b.N)), v.sy(b.l), 4, k === 1 ? P.series[2] : P.faint);
      });
      ctx.restore();
      D.dot(ctx, v.sx(Math.log10(s.N)), v.sy(loss(s.N, s.D)), 7, P.accent, P.surface, 2.5);
      D.text(ctx, 'you', v.sx(Math.log10(s.N)) + 10, v.sy(loss(s.N, s.D)) - 10, { color: P.accent, size: 11.5, weight: 700 });
      D.text(ctx, '● compute-optimal point on each curve', v.sx(v.x1) - 4, v.sy(v.y1) + 10, { color: P.series[2], size: 10.5, align: 'right' });
    };
    changed();
  },
});

defineLab('quantization', {
  title: 'Quantizing weights to a few bits',
  hint: 'Blue: the original weights. Orange spikes: the only values left after rounding to 2ᵇ levels.',
  mount(L) {
    const r = rng(41);
    const base = Array.from({ length: 4000 }, () => gauss(r));
    const s = { bits: 4, scheme: 'sym', group: false, outliers: false };
    const c = L.canvas(w => Math.min(300, w * .5));
    L.seg('bits', [[2, '2'], [3, '3'], [4, '4'], [8, '8']], s.bits, v => { s.bits = v; changed(); });
    L.seg('scheme', [['sym', 'Symmetric'], ['asym', 'Asymmetric']], s.scheme, v => { s.scheme = v; changed(); });
    L.toggle('Outlier weights', s.outliers, v => { s.outliers = v; changed(); });
    L.toggle('Per-group scales (64)', s.group, v => { s.group = v; changed(); });
    const weights = () => s.outliers ? base.map((w, i) => i % 500 === 7 ? (i % 1000 === 7 ? 14 : -12) : w) : base;
    const quant = ws => {
      const out = new Float64Array(ws.length), G = s.group ? 64 : ws.length;
      for (let g = 0; g < ws.length; g += G) {
        const part = ws.slice(g, g + G);
        if (s.scheme === 'sym') {
          const qmax = 2 ** (s.bits - 1) - 1 || 1, scale = Math.max(...part.map(Math.abs)) / qmax;
          part.forEach((w, i) => { out[g + i] = clamp(Math.round(w / scale), -qmax - 1, qmax) * scale; });
        } else {
          const lo = Math.min(...part), hi = Math.max(...part), levels = 2 ** s.bits - 1, scale = (hi - lo) / levels, zero = Math.round(-lo / scale);
          part.forEach((w, i) => { out[g + i] = (clamp(Math.round(w / scale) + zero, 0, levels) - zero) * scale; });
        }
      }
      return out;
    };
    function changed() {
      L.redraw();
      const ws = weights(), q = quant(ws);
      const mse = ws.reduce((a, w, i) => a + (w - q[i]) ** 2, 0) / ws.length;
      const zeros = [...q].filter(x => x === 0).length / q.length;
      const eff = s.bits + (s.group ? 16 / 64 : 0);
      L.stats([['levels', 2 ** s.bits], ['error (MSE)', fmtN(mse, 4), 'accent'], ['weights rounded to 0', `${Math.round(zeros * 100)}%`], ['7B model size', `${fmtN(7 * eff / 8, 1)} GB vs 14 GB FP16`]]);
      L.insight(s.outliers && !s.group ? `<b>A few outliers stretch the scale</b>, so the step between levels is huge and ${Math.round(zeros * 100)}% of normal weights round to 0. Per-group scales contain the damage. That is the group-size setting in GPTQ/AWQ, and why LLM.int8() keeps outliers in FP16.`
        : s.bits <= 2 ? '<b>2 bits = 4 levels.</b> Most detail is gone; models need quantization-aware training or clever methods to survive this.'
        : s.bits >= 8 ? '<b>INT8: 256 levels.</b> The error is tiny, which is why 8-bit inference is nearly lossless.'
        : `<b>${s.bits}-bit: ${2 ** s.bits} levels.</b> The weight distribution is bell-shaped, so levels in the tails are rarely used. NF4 in QLoRA places levels at normal-distribution quantiles instead of evenly.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, ws = weights(), q = quant(ws);
      const v = D.view(c, { x0: -4.5, x1: 4.5, y0: 0, y1: 1, pad: 12, padL: 12, padB: 24 });
      const bins = 90, bw = 9 / bins, h1 = new Array(bins).fill(0), h2 = new Map();
      ws.forEach(w => { const i = Math.floor((w + 4.5) / bw); if (i >= 0 && i < bins) h1[i]++; });
      q.forEach(w => { const k = w.toFixed(4); h2.set(k, (h2.get(k) || 0) + 1); });
      const m1 = Math.max(...h1), m2 = Math.max(...h2.values());
      D.axes(ctx, v, P, { xTicks: [-4, -2, 0, 2, 4] });
      h1.forEach((k, i) => { const hgt = k / m1 * .62; ctx.fillStyle = P.alpha(P.series[0], .55); ctx.fillRect(v.sx(-4.5 + i * bw) + .5, v.sy(hgt), v.sx(bw) - v.sx(0) - 1, v.sy(0) - v.sy(hgt)); });
      [...h2].forEach(([k, cnt]) => {
        const x = +k;
        if (x < -4.5 || x > 4.5) return;
        const hgt = .1 + cnt / m2 * .85;
        D.line(ctx, v.sx(x), v.sy(0), v.sx(x), v.sy(hgt), P.accent, 2.4);
        D.dot(ctx, v.sx(x), v.sy(hgt), 2.6, P.accent);
      });
      if (s.outliers) {
        D.text(ctx, '← outlier at −12', v.sx(-4.4), v.sy(.95), { color: P.err, size: 11, weight: 600 });
        D.text(ctx, 'outlier at +14 →', v.sx(4.4), v.sy(.95), { color: P.err, size: 11, weight: 600, align: 'right' });
      }
    };
    changed();
  },
});

defineLab('moe', {
  title: 'Mixture of experts: routing tokens',
  hint: 'A router sends each token to its top-k experts. Only those experts run, so compute stays small while total parameters grow.',
  mount(L) {
    const r = rng(13);
    const TYPES = ['code', 'math', 'prose', 'chat'];
    const s = { N: 8, k: 2, cap: 1.25, balance: false, tokens: [], load: [], dropped: 0, total: 0, window: 0, clock: 0 };
    const c = L.canvas(w => Math.min(330, w * .56));
    L.seg('experts', [[4, '4'], [8, '8'], [16, '16']], s.N, v => { s.N = v; reset(); });
    L.seg('top-k', [[1, '1'], [2, '2']], s.k, v => { s.k = v; reset(); });
    L.slider('capacity factor', { min: 1, max: 2, step: .05, value: s.cap, fmt: v => v.toFixed(2) }, v => { s.cap = v; });
    L.toggle('Load-balancing loss', s.balance, v => { s.balance = v; reset(); });
    const play = L.loop(dt => { s.clock += dt; if (s.clock > .16) { s.clock = 0; spawn(); } s.tokens.forEach(t => { t.t += dt * 1.4; }); s.tokens = s.tokens.filter(t => t.t < 1.2); L.redraw(); });
    L.playButton(play, ['Route tokens', 'Pause']);
    L.button('Reset', () => reset());
    function reset() { s.load = new Array(s.N).fill(0); s.dropped = 0; s.total = 0; s.window = 0; s.tokens = []; update(); L.redraw(); }
    function spawn() {
      const type = Math.floor(r() * 4);
      if (s.window >= 24) { s.load = new Array(s.N).fill(0); s.window = 0; }
      s.window++;
      const capacity = Math.ceil(s.cap * 24 * s.k / s.N);
      const scores = Array.from({ length: s.N }, (_, e) => {
        const pref = e === (type * 3) % s.N || e === (type * 3 + 1) % s.N ? 2.2 : 0;
        const skew = e < 2 ? 1.6 : 0;
        return pref + (s.balance ? 0 : skew) + gauss(r) * .6 - (s.balance ? s.load[e] * .35 : 0);
      });
      const chosen = scores.map((v, e) => [v, e]).sort((a, b) => b[0] - a[0]).slice(0, s.k).map(([, e]) => e);
      const routes = chosen.map(e => { const drop = s.load[e] >= capacity; if (!drop) s.load[e]++; else s.dropped++; return { e, drop }; });
      s.total += s.k;
      s.tokens.push({ type, routes, t: 0 });
      update();
    }
    function update() {
      const mean = s.load.reduce((a, b) => a + b, 0) / s.N || 0, mx = Math.max(...s.load, 0);
      L.stats([['active experts per token', `${s.k} of ${s.N}`, 'accent'], ['FFN compute used', `${Math.round(s.k / s.N * 100)}%`], ['dropped routes', s.total ? `${Math.round(s.dropped / s.total * 100)}%` : '0%', s.dropped / Math.max(1, s.total) > .1 ? 'err' : ''], ['busiest / average load', mean ? `${fmtN(mx / mean, 1)}×` : '—']]);
      L.insight(!s.balance && s.dropped / Math.max(1, s.total) > .08 ? '<b>The router favours a couple of experts</b>, they hit capacity, and tokens are dropped (skip the layer). Turn on the load-balancing loss: it penalises uneven routing so every expert gets used.'
        : s.balance ? '<b>Balanced routing:</b> load spreads evenly and few tokens overflow. Mixtral (8 experts, top-2) has 47B parameters but runs about 13B per token.'
        : '<b>Press “Route tokens”.</b> Each token visits only its top-k experts. Watch the load bars fill up during each batch window.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, rx = c.w * .3, ry = c.h / 2, ex = c.w * .72, eh = Math.min(32, (c.h - 30) / s.N - 4);
      const capacity = Math.ceil(s.cap * 24 * s.k / s.N);
      const ey = e => 15 + e * ((c.h - 30) / s.N) + ((c.h - 30) / s.N - eh) / 2;
      ctx.fillStyle = P.surface2; D.rrect(ctx, rx - 36, ry - 26, 72, 52, 12); ctx.fill(); ctx.strokeStyle = P.accent; ctx.lineWidth = 1.6; ctx.stroke();
      D.text(ctx, 'router', rx, ry, { color: P.text, size: 12, align: 'center', weight: 650 });
      for (let e = 0; e < s.N; e++) {
        const y = ey(e), load = s.load[e] / capacity;
        ctx.fillStyle = P.surface2; D.rrect(ctx, ex, y, c.w - ex - 14, eh, 8); ctx.fill();
        ctx.fillStyle = load >= 1 ? P.alpha('err', .55) : P.alpha('accent', .45);
        D.rrect(ctx, ex, y, (c.w - ex - 14) * Math.min(1, load), eh, 8); ctx.fill();
        D.text(ctx, `expert ${e + 1}`, ex + 8, y + eh / 2, { color: P.text, size: Math.min(11.5, eh * .45), weight: 600 });
      }
      s.tokens.forEach(t => {
        const col = P.series[t.type];
        if (t.t < .5) {
          const k = t.t / .5;
          D.dot(ctx, lerp(14, rx - 36, k), ry + (t.type - 1.5) * 20 * (1 - k), 6, col);
        } else {
          const k = Math.min(1, (t.t - .5) / .5);
          t.routes.forEach(({ e, drop }) => {
            const y = ey(e) + eh / 2, x = lerp(rx + 36, drop ? ex - 40 : ex, k), yy = lerp(ry, y, k);
            D.line(ctx, rx + 36, ry, x, yy, P.alpha(col, .35), 1.4);
            if (drop && k > .9) D.text(ctx, '✕', x, yy, { color: P.err, size: 14, align: 'center', weight: 700 });
            else D.dot(ctx, x, yy, 5, col);
          });
        }
      });
      TYPES.forEach((tp, i) => { D.dot(ctx, 16, c.h - 12 - (3 - i) * 16, 4, P.series[i]); D.text(ctx, tp, 26, c.h - 12 - (3 - i) * 16, { color: P.dim, size: 10.5 }); });
    };
    reset();
  },
});

defineLab('rag', {
  title: 'Chunk, retrieve, then prompt',
  hint: 'The policy text is split into chunks. The question is matched against every chunk, and the best ones are pasted into the prompt.',
  mount(L) {
    const DOC = 'Orders can be returned within 30 days of delivery for a full refund. Items must be unused and in their original packaging. To start a return, open the Orders page and choose Request return. Refunds go back to the original payment method within 5 to 7 business days after the warehouse receives the item. Shipping costs are refunded only when the item arrived damaged or was the wrong item. Gift cards and downloadable software cannot be returned. Customers in the EU may cancel any order within 14 days without giving a reason. Express shipping upgrades are non-refundable. For damaged items, upload a photo within 48 hours of delivery so support can approve a free replacement.';
    const words = DOC.split(' ');
    const Q = {
      refund: ['How long until I get my money back?', 'refund payment days business money back receive', '5 to 7 business days'],
      gift: ['Can I return a gift card?', 'gift card return returned cannot', 'Gift cards and downloadable software cannot be returned'],
      broken: ['My parcel arrived broken. What should I do?', 'damaged broken arrived photo replacement delivery', 'upload a photo within 48 hours'],
    };
    const STOP = new Set('a an the and or of to in for be can is are was my i what do should how until get me it on at by when so any after'.split(' '));
    const norm = w => w.toLowerCase().replace(/[^a-z0-9]/g, '').replace(/(ing|ed|es|s)$/, '');
    const tf = text => { const m = new Map(); text.split(/\s+/).map(norm).filter(w => w && !STOP.has(w)).forEach(w => m.set(w, (m.get(w) || 0) + 1)); return m; };
    const cos = (a, b) => { let d = 0, na = 0, nb = 0; a.forEach((v, k) => { d += v * (b.get(k) || 0); na += v * v; }); b.forEach(v => { nb += v * v; }); return na && nb ? d / Math.sqrt(na * nb) : 0; };
    const s = { size: 24, overlap: 4, k: 2, q: 'refund' };
    const box = document.createElement('div');
    box.className = 'rag-box';
    L.stage.append(box);
    L.seg('question', Object.entries(Q).map(([k, [q]]) => [k, q]), s.q, v => { s.q = v; render(); });
    L.slider('chunk size (words)', { min: 6, max: 50, step: 1, value: s.size }, v => { s.size = v; s.overlap = Math.min(s.overlap, v - 2); ov.set(s.overlap, true); render(); });
    const ov = L.slider('overlap (words)', { min: 0, max: 12, step: 1, value: s.overlap }, v => { s.overlap = Math.min(v, s.size - 2); render(); });
    L.slider('top-k chunks', { min: 1, max: 4, step: 1, value: s.k }, v => { s.k = v; render(); });
    function render() {
      const stride = Math.max(1, s.size - s.overlap), chunks = [];
      for (let st = 0; st < words.length; st += stride) { chunks.push([st, Math.min(words.length, st + s.size)]); if (st + s.size >= words.length) break; }
      const [question, expand, answer] = Q[s.q];
      const qv = tf(`${question} ${expand}`);
      const scored = chunks.map(([a, b], i) => ({ i, a, b, text: words.slice(a, b).join(' '), score: cos(qv, tf(words.slice(a, b).join(' '))) }));
      const top = [...scored].sort((x, y) => y.score - x.score).slice(0, s.k);
      const hit = new Set(top.map(t => t.i));
      const context = top.map(t => t.text).join('\n…\n');
      const found = context.includes(answer);
      const P = labPalette(L.fig);
      box.innerHTML = `
        <div class="rag-doc" aria-label="Document split into chunks">${words.map((w, wi) => {
          const owners = chunks.map((ch, i) => wi >= ch[0] && wi < ch[1] ? i : -1).filter(i => i >= 0);
          const cols = owners.map(i => P.alpha(P.series[i % 6], hit.has(i) ? .38 : .14));
          const bg = cols.length > 1 ? `repeating-linear-gradient(135deg, ${cols[0]} 0 5px, ${cols[1]} 5px 10px)` : cols[0];
          return `<span class="rag-w${owners.some(i => hit.has(i)) ? ' is-hit' : ''}" style="background:${bg}">${esc(w)}</span>`;
        }).join(' ')}</div>
        <div class="rag-side">
          <p class="rag-label">Similarity of each chunk to the question</p>
          <ol class="rag-scores">${scored.map(ch => `<li class="${hit.has(ch.i) ? 'is-hit' : ''}"><span>chunk ${ch.i + 1}</span><i style="--w:${Math.round(ch.score * 100)}%;--c:${P.series[ch.i % 6]}"></i><b>${ch.score.toFixed(2)}</b></li>`).join('')}</ol>
          <p class="rag-label">Prompt sent to the LLM</p>
          <pre class="rag-prompt">Answer using only the context.\n\nContext:\n${esc(context)}\n\nQuestion: ${esc(question)}</pre>
          <p class="rag-verdict ${found ? 'ok' : 'bad'}">${found ? '✓ The answer is inside the retrieved context.' : '✕ The sentence with the answer is not in the prompt, so the model has to guess.'}</p>
        </div>`;
      L.stats([['chunks', chunks.length], ['best score', top[0].score.toFixed(2), 'accent'], ['prompt words', context.split(/\s+/).length]]);
      L.insight(!found && s.size < 12 ? '<b>Chunks too small:</b> the answer sentence is cut in half, so no single chunk contains it. Raise the size or add overlap.'
        : !found ? '<b>Retrieval missed.</b> The best-scoring chunks share words with the question but not the answer. That is why production RAG adds hybrid search and a reranker.'
        : s.size > 38 ? '<b>Found, but the chunks are big:</b> the prompt fills with irrelevant text, which costs tokens and can distract the model.'
        : '<b>Retrieved correctly.</b> Overlap (striped words) makes sure a sentence cut at a boundary still appears whole in one chunk.');
    }
    render();
  },
});

defineLab('distributed', {
  title: 'Where does training memory go? DDP vs ZeRO',
  hint: 'Mixed-precision Adam needs about 16 bytes per parameter. The strategy decides how that is split across GPUs.',
  mount(L) {
    const s = { B: 7, gpus: 8, strat: 'ddp' };
    const box = document.createElement('div');
    box.className = 'gpu-box';
    L.stage.append(box);
    L.seg('model', [[7, '7B'], [13, '13B'], [70, '70B']], s.B, v => { s.B = v; render(); });
    L.seg('GPUs', [[1, '1'], [8, '8'], [16, '16'], [64, '64']], s.gpus, v => { s.gpus = v; render(); });
    L.seg('strategy', [['ddp', 'DDP'], ['z1', 'ZeRO-1'], ['z2', 'ZeRO-2'], ['z3', 'ZeRO-3 / FSDP']], s.strat, v => { s.strat = v; render(); });
    function render() {
      const Phi = s.B, N = s.gpus;
      const parts = { ddp: [2, 2, 12], z1: [2, 2, 12 / N], z2: [2, 2 / N, 12 / N], z3: [2 / N, 2 / N, 12 / N] }[s.strat].map(b => b * Phi);
      const total = parts.reduce((a, b) => a + b, 0), fits = total <= 80;
      const shown = Math.min(N, 16);
      const P = labPalette(L.fig);
      const names = ['weights (FP16)', 'gradients (FP16)', 'Adam state (FP32)'], cols = [P.series[0], P.series[1], P.accent];
      box.innerHTML = `
        <div class="gpu-legend">${names.map((n, i) => `<span><i style="background:${cols[i]}"></i>${n}: ${fmtN(parts[i], 1)} GB</span>`).join('')}</div>
        <div class="gpu-grid">${Array.from({ length: shown }, (_, g) => `
          <div class="gpu${fits ? '' : ' oom'}">
            <div class="gpu-bar">${parts.map((p, i) => `<i style="height:${Math.min(100, p / 80 * 100)}%;background:${cols[i]}"></i>`).join('')}</div>
            <span class="gpu-name">GPU ${g + 1}</span><b>${fmtN(total, 0)} GB</b>
          </div>`).join('')}${N > shown ? `<div class="gpu more">+ ${N - shown} more</div>` : ''}</div>`;
      L.stats([['memory per GPU', `${fmtN(total, 1)} GB of 80 GB`, fits ? 'ok' : 'err'], ['fits?', fits ? 'yes' : 'out of memory', fits ? 'ok' : 'err'], ['total model state', `${16 * Phi} GB`]]);
      L.insight(s.strat === 'ddp' ? `<b>DDP copies everything to every GPU.</b> More GPUs add speed but not memory: ${fmtN(total, 0)} GB each, whether you have 1 GPU or 64.`
        : s.strat === 'z3' ? `<b>ZeRO-3 / FSDP shards weights, gradients and optimizer state.</b> Memory per GPU falls to 16Φ/N = ${fmtN(total, 1)} GB, at the cost of all-gathering each layer’s weights just before it runs.`
        : `<b>${s.strat === 'z1' ? 'ZeRO-1 shards only the Adam state' : 'ZeRO-2 shards Adam state and gradients'}</b>, the biggest pieces, for little extra communication.${fits ? '' : ' Still not enough here: try ZeRO-3 or more GPUs.'}`);
    }
    render();
  },
});

defineLab('lora', {
  title: 'LoRA: train two thin matrices instead of one huge one',
  hint: 'W stays frozen. The update ΔW = B·A has rank r, so it only needs 2·d·r numbers instead of d².',
  mount(L) {
    const RANKS = [1, 2, 4, 8, 16, 32, 64, 128, 256];
    const s = { d: 4096, ri: 3, r: 8, mats: 2, anim: 8 };
    const c = L.canvas(w => Math.min(280, w * .44));
    L.seg('hidden size d', [[1024, '1024'], [4096, '4096 (7B)'], [8192, '8192 (70B)']], s.d, v => { s.d = v; changed(); });
    L.slider('rank r', { min: 0, max: 8, step: 1, value: s.ri, fmt: i => RANKS[i] }, i => {
      const from = s.anim; s.r = RANKS[i];
      L.tween(350, t => { s.anim = lerp(from, s.r, t); L.redraw(); });
      changed();
    });
    L.seg('adapt', [[2, 'q, v projections'], [7, 'all linear layers']], s.mats, v => { s.mats = v; changed(); });
    function changed() {
      L.redraw();
      const per = 2 * s.d * s.r, full = s.d * s.d, layers = 32, trainable = per * s.mats * layers, model = 12 * s.d * s.d * layers;
      L.stats([['per matrix', `${fmtBig(per)} vs ${fmtBig(full)}`, 'accent'], ['trainable in model', `${fmtBig(trainable)} (${fmtN(trainable / model * 100, 2)}%)`], ['optimizer memory', `${fmtN(trainable * 12 / 1e9, 2)} GB vs ${fmtN(model * 12 / 1e9, 0)} GB`]]);
      L.insight(`<b>r = ${s.r}: one ${s.d}×${s.d} matrix needs ${fmtN(per / full * 100, 2)}% of its parameters trained.</b> It works because fine-tuning updates tend to be low-rank: a few directions of change matter. After training, B·A can be merged into W, so inference costs nothing extra.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, S = c.h - 50, y = 30, k = S / s.d, thin = Math.max(3, s.anim * k * 6);
      const wx = 14;
      ctx.fillStyle = P.alpha('faint', .18); D.rrect(ctx, wx, y, S, S, 8); ctx.fill();
      ctx.strokeStyle = P.strong; ctx.lineWidth = 1.2; ctx.stroke();
      for (let i = 1; i < 8; i++) { D.line(ctx, wx + S * i / 8, y, wx + S * i / 8, y + S, P.soft, 1); D.line(ctx, wx, y + S * i / 8, wx + S, y + S * i / 8, P.soft, 1); }
      D.text(ctx, `W  ${s.d}×${s.d}  (frozen)`, wx, y - 12, { color: P.dim, size: 11.5, weight: 600 });
      const px = wx + S + 22;
      D.text(ctx, '+', px, y + S / 2, { color: P.text, size: 20, weight: 600 });
      const bx = px + 22;
      ctx.fillStyle = P.series[0]; D.rrect(ctx, bx, y, thin, S, 4); ctx.fill();
      D.text(ctx, `B  ${s.d}×${s.r}`, bx, y + S + 12, { color: P.series[0], size: 11.5, weight: 600 });
      const ax = bx + thin + 24;
      D.text(ctx, '×', ax - 12, y + S / 2, { color: P.text, size: 16, align: 'center' });
      const aw = Math.min(S, c.w - ax - 14);
      ctx.fillStyle = P.accent; D.rrect(ctx, ax, y, aw, thin, 4); ctx.fill();
      D.text(ctx, `A  ${s.r}×${s.d}`, ax, y - 12, { color: P.accent, size: 11.5, weight: 600 });
      D.text(ctx, 'trainable', ax, y + thin + 16, { color: P.faint, size: 11 });
    };
    changed();
  },
});

defineLab('agentloop', {
  title: 'Run an agent loop step by step',
  hint: 'The model never runs tools itself. It writes a request, the harness runs the tool, and the result is appended to the transcript for the next call.',
  mount(L) {
    const SCRIPTS = {
      happy: [
        ['think', 'I need the live weather for Paris before I can answer.'],
        ['act', 'get_weather({"city": "Paris"})'],
        ['observe', '{"temp_c": 18, "sky": "light rain"}'],
        ['think', "That's 18 °C. The user asked for Fahrenheit, so convert it."],
        ['act', 'calculator({"expression": "18 * 9 / 5 + 32"})'],
        ['observe', '64.4'],
        ['answer', "It's 64.4 °F (18 °C) with light rain in Paris right now."],
      ],
      error: [
        ['think', 'I need the live weather for Paris.'],
        ['act', 'get_weather({"city": "Paris"})'],
        ['observe', 'ERROR 503: weather service unavailable'],
        ['think', 'The tool failed. Retry once before giving up.'],
        ['act', 'get_weather({"city": "Paris"})'],
        ['observe', '{"temp_c": 18, "sky": "light rain"}'],
        ['think', 'Convert 18 °C to Fahrenheit.'],
        ['act', 'calculator({"expression": "18 * 9 / 5 + 32"})'],
        ['observe', '64.4'],
        ['answer', "It's 64.4 °F (18 °C) with light rain in Paris."],
      ],
    };
    const LABEL = { think: 'LLM call', act: 'Tool request', observe: 'Tool result', answer: 'Final answer', stop: 'Harness' };
    const s = { script: 'happy', i: 0, max: 4, log: [], stopped: false };
    const box = document.createElement('div');
    box.className = 'agent-box';
    box.innerHTML = `
      <svg class="agent-ring" viewBox="0 0 220 220" aria-hidden="true">
        <circle cx="110" cy="110" r="72" class="ag-orbit"/>
        ${[['think', 110, 38], ['act', 182, 110], ['observe', 110, 182], ['answer', 38, 110]].map(([k, x, y]) =>
          `<g class="ag-node" data-node="${k}"><circle cx="${x}" cy="${y}" r="30"/><text x="${x}" y="${y + 4}">${k}</text></g>`).join('')}
      </svg>
      <ol class="agent-log" aria-live="polite"></ol>`;
    L.stage.append(box);
    const logEl = box.querySelector('.agent-log');
    L.seg('scenario', [['happy', 'Everything works'], ['error', 'Tool fails once']], s.script, v => { s.script = v; reset(); });
    L.slider('max LLM calls (max_steps)', { min: 1, max: 6, step: 1, value: s.max }, v => { s.max = v; reset(); });
    let acc = 0;
    const play = L.loop(dt => { acc += dt; if (acc > 1.1) { acc = 0; if (!step()) return false; } });
    L.playButton(play, ['Run the agent', 'Pause'], () => { if (done()) reset(); });
    L.button('Next step', () => step());
    L.button('Reset', () => { play.stop(); reset(); });
    const done = () => s.stopped || s.i >= SCRIPTS[s.script].length;
    const calls = () => s.log.filter(e => e.kind === 'think' || e.kind === 'answer').length;
    function reset() { s.i = 0; s.log = []; s.stopped = false; paint(); }
    function step() {
      if (done()) return false;
      const [kind, text] = SCRIPTS[s.script][s.i];
      if ((kind === 'think' || kind === 'answer') && calls() >= s.max) {
        s.log.push({ kind: 'stop', text: `Stopped: max_steps = ${s.max} reached before a final answer.` });
        s.stopped = true; paint(); return false;
      }
      s.log.push({ kind, text });
      s.i++;
      paint();
      return !done();
    }
    function paint() {
      const last = s.log[s.log.length - 1];
      box.querySelectorAll('.ag-node').forEach(n => n.classList.toggle('is-on', !!last && n.dataset.node === last.kind));
      logEl.innerHTML = s.log.map((e, i) => `<li class="ag-${e.kind}${i === s.log.length - 1 ? ' is-new' : ''}"><span>${LABEL[e.kind]}</span><code>${esc(e.text)}</code></li>`).join('') || '<li class="ag-empty">The transcript starts with the system prompt, the tool list and the user question: “What’s the weather in Paris right now, in Fahrenheit?”</li>';
      logEl.scrollTop = logEl.scrollHeight;
      let ctx = 320, billed = 0;
      s.log.forEach(e => { if (e.kind === 'think' || e.kind === 'answer') billed += ctx; ctx += Math.ceil(e.text.length / 4) + 8; });
      const tools = s.log.filter(e => e.kind === 'act').length;
      L.stats([['LLM calls', calls(), 'accent'], ['tool calls', tools], ['context now', `${ctx} tokens`], ['input tokens billed', billed]]);
      L.insight(s.stopped ? '<b>The step limit fired.</b> Without max_steps a confused agent can loop forever and burn money; with it too low, a recoverable error (like one failed tool call) becomes a failure.'
        : last?.kind === 'answer' ? `<b>Done in ${calls()} LLM calls.</b> Notice the billed tokens: every call re-reads the whole growing transcript, so cost grows roughly quadratically with the number of steps.`
        : last?.kind === 'act' ? '<b>The model only wrote text</b> that the harness parses into a tool name and JSON arguments. The harness runs it.'
        : last?.kind === 'observe' ? '<b>The tool result is appended as text.</b> The next LLM call sees it as if it were part of the conversation.'
        : '<b>Run the agent</b> and watch the loop go think → act → observe until the model writes a final answer.');
    }
    reset();
  },
});

defineLab('serving', {
  title: 'Static vs continuous batching',
  hint: 'Four GPU slots decode requests of different lengths. Hatched areas are slots sitting idle.',
  mount(L) {
    const REQ = [[0, 6], [0, 2], [0, 3], [0, 9], [1, 2], [1, 4], [2, 3], [3, 5], [4, 2], [5, 3], [6, 4], [7, 2]];
    const SLOTS = 4;
    const s = { mode: 'continuous', t: 999 };
    const c = L.canvas(w => Math.min(250, w * .4));
    L.seg('', [['static', 'Static batching'], ['continuous', 'Continuous batching']], s.mode, v => { s.mode = v; s.t = 999; changed(); });
    const play = L.loop(dt => { s.t += dt * 3.2; L.redraw(); if (s.t > sim().end + .5) return false; });
    L.playButton(play, ['Replay', 'Pause'], () => { s.t = 0; });
    function sim() {
      const segs = [], free = new Array(SLOTS).fill(0), queue = REQ.map(([a, len], id) => ({ id, a, len }));
      if (s.mode === 'continuous') {
        queue.forEach(rq => {
          const slot = free.indexOf(Math.min(...free)), start = Math.max(free[slot], rq.a);
          segs.push({ slot, id: rq.id, start, end: start + rq.len, a: rq.a });
          free[slot] = start + rq.len;
        });
      } else {
        let tNow = 0, i = 0;
        while (i < queue.length) {
          const batch = queue.slice(i, i + SLOTS);
          const start = Math.max(tNow, batch[batch.length - 1].a);
          const end = start + Math.max(...batch.map(b => b.len));
          batch.forEach((rq, k) => segs.push({ slot: k, id: rq.id, start, end: start + rq.len, a: rq.a, batchEnd: end }));
          tNow = end; i += SLOTS;
        }
      }
      return { segs, end: Math.max(...segs.map(x => x.batchEnd || x.end)) };
    }
    function changed() {
      L.redraw();
      const { segs, end } = sim(), busy = segs.reduce((a, x) => a + (x.end - x.start), 0);
      const lat = segs.reduce((a, x) => a + (x.end - x.a), 0) / segs.length;
      L.stats([['all done at step', end, 'accent'], ['throughput', `${fmtN(busy / end, 2)} tokens/step`], ['mean latency', `${fmtN(lat, 1)} steps`], ['GPU slot utilisation', `${Math.round(busy / (end * SLOTS) * 100)}%`]]);
      L.insight(s.mode === 'static'
        ? '<b>Static batching waits for the longest request in each batch.</b> Short requests finish early and their slots sit idle (hatched) while new requests wait in the queue.'
        : '<b>Continuous batching (vLLM, TGI) admits a new request the moment any slot frees up.</b> Same GPU, same requests: less idle time, higher throughput and lower latency. PagedAttention makes this practical by allocating KV cache in small blocks.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, { segs, end } = sim(), x0 = 58, rowH = (c.h - 44) / SLOTS, kx = (c.w - x0 - 14) / Math.max(end, 20);
      for (let k = 0; k <= Math.max(end, 20); k += 2) { D.line(ctx, x0 + k * kx, 20, x0 + k * kx, c.h - 22, P.soft, 1); D.text(ctx, String(k), x0 + k * kx, c.h - 10, { color: P.faint, size: 10, align: 'center', mono: true }); }
      REQ.forEach(([a], id) => D.text(ctx, '▾', x0 + a * kx + (id % 3) * 3, 12, { color: P.faint, size: 10, align: 'center' }));
      for (let r = 0; r < SLOTS; r++) D.text(ctx, `slot ${r + 1}`, 8, 26 + r * rowH + rowH / 2, { color: P.dim, size: 11 });
      segs.forEach(sg => {
        const y = 24 + sg.slot * rowH, h = rowH - 8;
        if (sg.batchEnd && sg.end < sg.batchEnd) {
          const ix = x0 + sg.end * kx, iw = (sg.batchEnd - sg.end) * kx;
          ctx.save(); ctx.beginPath(); ctx.rect(ix, y, iw, h); ctx.clip();
          for (let k = -h; k < iw; k += 7) D.line(ctx, ix + k, y + h, ix + k + h, y, P.alpha('err', .35), 1.4);
          ctx.restore();
        }
        const vis = clamp(s.t - sg.start, 0, sg.end - sg.start);
        if (vis <= 0) return;
        ctx.fillStyle = P.alpha(P.series[sg.id % 8], .75);
        D.rrect(ctx, x0 + sg.start * kx + 1, y, vis * kx - 2, h, 6); ctx.fill();
        if (vis * kx > 26) D.text(ctx, `R${sg.id + 1}`, x0 + sg.start * kx + 8, y + h / 2, { color: P.surface, size: 11, weight: 700 });
      });
      if (s.t < end) D.line(ctx, x0 + s.t * kx, 18, x0 + s.t * kx, c.h - 20, P.text, 1.4);
    };
    changed();
  },
});

defineLab('semcache', {
  title: 'Semantic cache: how similar is similar enough?',
  hint: 'Dots are questions in embedding space. A new question reuses a cached answer if it falls inside the similarity radius.',
  mount(L) {
    const CACHE = [['How do I reset my password?', 2, 2], ['Cancel my subscription', 6, 5], ["What's your refund policy?", 8.2, 1.8]];
    const QUERIES = [
      ['I forgot my password, how do I reset it?', 2.35, 2.3, 0], ['reset password please', 1.7, 1.65, 0], ['How do I change my email address?', 3.1, 2.95, -1],
      ['Cancel my order', 6.7, 5.65, -1], ['How can I end my subscription?', 5.35, 4.3, 1], ['refund policy for EU customers', 8.9, 2.5, 2], ['Do you ship to Canada?', 9, 6, -1],
    ];
    const s = { thr: .9, hover: -1 };
    const c = L.canvas(w => Math.min(320, w * .54));
    let v = null;
    L.slider('similarity threshold', { min: .75, max: .99, step: .005, value: s.thr, fmt: x => x.toFixed(3) }, x => { s.thr = x; changed(); });
    L.drag(c, { hover: (x, y) => { if (!v || x == null) { s.hover = -1; } else { s.hover = QUERIES.findIndex(([, qx, qy]) => Math.hypot(v.sx(qx) - x, v.sy(qy) - y) < 12); } L.redraw(); } });
    const radius = () => (1 - s.thr) * 10;
    const classify = () => QUERIES.map(([text, x, y, truth]) => {
      const near = CACHE.map(([, cx, cy], i) => [Math.hypot(cx - x, cy - y), i]).sort((a, b) => a[0] - b[0])[0];
      const hit = near[0] <= radius();
      const kind = hit ? (near[1] === truth ? 'hit' : 'false') : (truth >= 0 ? 'missed' : 'miss');
      return { text, x, y, kind, sim: 1 - near[0] / 10 };
    });
    function changed() {
      L.redraw();
      const cl = classify(), n = k => cl.filter(q => q.kind === k).length;
      L.stats([['correct cache hits', n('hit'), 'ok'], ['wrong answer served', n('false'), n('false') ? 'err' : ''], ['missed a reusable answer', n('missed')], ['cache hit rate', `${Math.round((n('hit') + n('false')) / cl.length * 100)}%`, 'accent']]);
      L.insight(n('false') ? `<b>Threshold too loose:</b> ${n('false')} question${n('false') > 1 ? 's' : ''} got someone else’s answer (“Cancel my order” is not “Cancel my subscription”). A wrong cached answer is worse than a cache miss.`
        : n('missed') > 1 ? '<b>Threshold too strict:</b> paraphrases of cached questions go to the LLM again, so you pay for answers you already have.'
        : '<b>A good balance for this data.</b> In production you tune this on real traffic and often add a cheap check, such as matching intent or entities, before serving a hit.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      v = D.view(c, { x0: 0, x1: 10.5, y0: 0, y1: 7, pad: 14, equal: true });
      D.grid(ctx, v, P, 1);
      const rpx = radius() * v.kx;
      CACHE.forEach(([t, x, y]) => {
        D.dot(ctx, v.sx(x), v.sy(y), rpx, P.alpha('accent', .12), P.alpha('accent', .6), 1.4);
        D.dot(ctx, v.sx(x), v.sy(y), 7, P.accent, P.surface, 2);
        D.text(ctx, t, v.sx(x), v.sy(y) - 14, { color: P.accent, size: 11, align: 'center', weight: 650 });
      });
      const colors = { hit: P.ok, false: P.err, missed: P.series[1], miss: P.faint };
      classify().forEach((q, i) => {
        D.dot(ctx, v.sx(q.x), v.sy(q.y), 5.5, colors[q.kind], P.surface, 1.5);
        if (i === s.hover) {
          D.font(ctx, 11.5, 600);
          const tw = ctx.measureText(q.text).width + 16, bx = clamp(v.sx(q.x) - tw / 2, 4, c.w - tw - 4), by = v.sy(q.y) + 12;
          ctx.fillStyle = P.surface2; D.rrect(ctx, bx, by, tw, 22, 6); ctx.fill();
          D.text(ctx, q.text, bx + 8, by + 11, { color: P.text, size: 11.5, weight: 600 });
        }
      });
      [['hit', 'correct hit'], ['false', 'wrong answer'], ['missed', 'missed'], ['miss', 'new question']].forEach(([k, l], i) => {
        D.dot(ctx, 20 + i * 104, c.h - 12, 4.5, colors[k]); D.text(ctx, l, 28 + i * 104, c.h - 12, { color: P.dim, size: 10.5 });
      });
    };
    changed();
  },
});

defineLab('drift', {
  title: 'Detecting data drift with PSI',
  hint: 'Grey: the feature’s distribution at training time. Orange: what production traffic looks like now.',
  mount(L) {
    const BINS = 10, r = rng(3);
    const s = { shift: .4, scale: 1, week: -1, hist: [] };
    const c = L.canvas(w => Math.min(300, w * .5));
    const shS = L.slider('mean shift (in σ)', { min: 0, max: 2, step: .05, value: s.shift, fmt: v => v.toFixed(2) }, v => { s.shift = v; changed(); });
    L.slider('spread change', { min: .5, max: 2, step: .05, value: s.scale, fmt: v => `${v.toFixed(2)}×` }, v => { s.scale = v; changed(); });
    const edges = Array.from({ length: BINS + 1 }, (_, i) => i === 0 ? -Infinity : i === BINS ? Infinity : -2.5 + 5 * i / BINS);
    const probs = (mu, sd) => edges.slice(0, -1).map((e, i) => normCdf(edges[i + 1], mu, sd) - normCdf(e, mu, sd));
    const psiOf = (mu, sd, noise) => {
      const p = probs(0, 1), q = probs(mu, sd).map(x => Math.max(1e-4, x + (noise ? gauss(r) * Math.sqrt(x * (1 - x) / 800) : 0)));
      const qs = q.reduce((a, b) => a + b, 0);
      return p.reduce((a, pi, i) => a + (q[i] / qs - pi) * Math.log((q[i] / qs) / pi), 0);
    };
    let acc = 0;
    const play = L.loop(dt => {
      acc += dt;
      if (acc < .35) return;
      acc = 0; s.week++;
      const k = s.week / 11;
      shS.set(+(k * 1.5).toFixed(2), true); s.shift = k * 1.5;
      s.hist.push(psiOf(s.shift, lerp(1, s.scale, k), true));
      changed(true);
      if (s.week >= 11) return false;
    });
    L.playButton(play, ['Simulate 12 weeks', 'Pause'], () => { s.week = -1; s.hist = []; });
    function changed(keep) {
      if (!keep) s.hist = [];
      L.redraw();
      const psi = psiOf(s.shift, s.scale, false), status = psi < .1 ? ['stable', 'ok'] : psi < .25 ? ['watch', ''] : ['drift: retrain', 'err'];
      L.stats([['PSI', fmtN(psi, 3), 'accent'], ['status', status[0], status[1]]]);
      L.insight(psi < .1 ? '<b>PSI below 0.1: no meaningful change.</b> The model is still seeing the data it was trained on.'
        : psi < .25 ? '<b>PSI between 0.1 and 0.25: moderate drift.</b> Investigate the feature pipeline before accuracy quietly slips.'
        : '<b>PSI above 0.25: significant drift.</b> The model is making predictions on data unlike its training set. Alert, check upstream changes, and plan a retrain. Accuracy often drops long before anyone notices.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, p = probs(0, 1), q = probs(s.shift, s.scale), w = (c.w * (s.hist.length ? .62 : 1) - 40) / BINS, base = c.h - 28, top = 18;
      const mx = Math.max(...p, ...q);
      for (let i = 0; i < BINS; i++) {
        const x = 20 + i * w;
        ctx.fillStyle = P.alpha('faint', .45); D.rrect(ctx, x + 2, base - p[i] / mx * (base - top), w / 2 - 3, p[i] / mx * (base - top), 3); ctx.fill();
        ctx.fillStyle = P.accent; D.rrect(ctx, x + w / 2, base - q[i] / mx * (base - top), w / 2 - 3, q[i] / mx * (base - top), 3); ctx.fill();
      }
      D.line(ctx, 16, base, 20 + BINS * w, base, P.strong, 1);
      D.text(ctx, 'feature value bins →', 20, c.h - 10, { color: P.faint, size: 10.5 });
      if (s.hist.length) {
        const gx = c.w * .66, v = D.view({ w: c.w - gx, h: c.h }, { x0: 0, x1: 11, y0: 0, y1: Math.max(.5, ...s.hist) * 1.1, pad: 16, padL: 30, padB: 24 });
        ctx.save(); ctx.translate(gx, 0);
        D.axes(ctx, v, P, { yTicks: [.1, .25], xTicks: [0, 4, 8, 11], xLabel: 'week' });
        D.line(ctx, v.sx(0), v.sy(.25), v.sx(11), v.sy(.25), P.err, 1.2, [4, 3]);
        ctx.beginPath(); s.hist.forEach((y, i) => i ? ctx.lineTo(v.sx(i), v.sy(y)) : ctx.moveTo(v.sx(i), v.sy(y)));
        ctx.strokeStyle = P.accent; ctx.lineWidth = 2.2; ctx.stroke();
        s.hist.forEach((y, i) => D.dot(ctx, v.sx(i), v.sy(y), 3.5, y > .25 ? P.err : P.accent));
        ctx.restore();
      }
    };
    changed();
  },
});
