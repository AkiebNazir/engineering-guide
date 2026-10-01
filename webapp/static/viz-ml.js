/* ============================================================================
   Interactive labs: classical machine learning and deep learning.
   Requires viz.js.
   ========================================================================= */
'use strict';

defineLab('regression', {
  title: 'Fit a line, see the squared errors',
  hint: 'Drag points, or click empty space to add one. Each square is one error squared: MSE is their average area.',
  mount(L, opts) {
    const r = rng(9);
    const s = {
      mode: opts.mode || 'linear', m: .2, b: 3, squares: true, w: .6, bl: -3,
      pts: Array.from({ length: 10 }, (_, i) => { const x = .6 + i * .95; return [x, clamp(.75 * x + 1.2 + gauss(r) * .9, .3, 9.7)]; }),
      cls: [[1, 0], [1.8, 0], [2.6, 0], [3.5, 0], [4.1, 1], [4.6, 0], [5.4, 1], [6.3, 1], [7.1, 1], [8.4, 1], [9.2, 1]],
    };
    const c = L.canvas(w => Math.min(340, w * .58));
    let v = null;
    const modeSeg = L.seg('', [['linear', 'Linear regression'], ['logistic', 'Logistic regression']], s.mode, m => { s.mode = m; build(); });
    const fitLoop = L.loop(() => {
      let moved = 0;
      for (let i = 0; i < 4; i++) moved += s.mode === 'linear' ? gdLinear() : gdLogistic();
      sync(); L.redraw(); update();
      if (moved < 1e-5) return false;
    });
    function build() {
      L.clearDyn();
      fitLoop.stop();
      if (s.mode === 'linear') {
        s.sm = L.slider('slope m', { min: -2, max: 3, step: .01, value: s.m, dyn: true, fmt: x => x.toFixed(2) }, x => { s.m = x; changed(); });
        s.sb = L.slider('intercept b', { min: -4, max: 10, step: .05, value: s.b, dyn: true, fmt: x => x.toFixed(2) }, x => { s.b = x; changed(); });
      } else {
        s.sw = L.slider('weight w', { min: -4, max: 6, step: .05, value: s.w, dyn: true, fmt: x => x.toFixed(2) }, x => { s.w = x; changed(); });
        s.sbl = L.slider('bias b', { min: -30, max: 20, step: .1, value: s.bl, dyn: true, fmt: x => x.toFixed(1) }, x => { s.bl = x; changed(); });
      }
      changed();
    }
    L.playButton(fitLoop, ['Train with gradient descent', 'Pause']);
    L.button('Solve exactly', () => {
      if (s.mode === 'logistic') { for (let i = 0; i < 4000; i++) gdLogistic(); sync(); changed(); return; }
      const n = s.pts.length, mx = s.pts.reduce((a, p) => a + p[0], 0) / n, my = s.pts.reduce((a, p) => a + p[1], 0) / n;
      const sxy = s.pts.reduce((a, [x, y]) => a + (x - mx) * (y - my), 0), sxx = s.pts.reduce((a, [x]) => a + (x - mx) ** 2, 0);
      const m = sxx ? sxy / sxx : 0, b = my - m * mx, m0 = s.m, b0 = s.b;
      L.tween(600, t => { s.m = lerp(m0, m, t); s.b = lerp(b0, b, t); sync(); changed(); });
    });
    L.button('Add an outlier', () => { s.mode === 'linear' ? s.pts.push([8.8, .6]) : s.cls.push([1.4, 1]); changed(); });
    L.toggle('Show squared errors', s.squares, x => { s.squares = x; L.redraw(); });
    function sync() {
      if (s.mode === 'linear') { s.sm?.set(clamp(s.m, -2, 3), true); s.sb?.set(clamp(s.b, -4, 10), true); }
      else { s.sw?.set(clamp(s.w, -4, 6), true); s.sbl?.set(clamp(s.bl, -30, 20), true); }
    }
    const gdLinear = () => {
      const n = s.pts.length;
      let gm = 0, gb = 0, xx = 0;
      s.pts.forEach(([x, y]) => { const e = s.m * x + s.b - y; gm += 2 * e * x / n; gb += 2 * e / n; xx += x * x / n; });
      const dm = .45 * gm / (2 * xx), db = .15 * gb;
      s.m -= dm; s.b -= db;
      return Math.abs(dm) + Math.abs(db);
    };
    const sig = z => 1 / (1 + Math.exp(-z));
    const gdLogistic = () => {
      const n = s.cls.length;
      let gw = 0, gb = 0;
      s.cls.forEach(([x, y]) => { const e = sig(s.w * x + s.bl) - y; gw += e * x / n; gb += e / n; });
      s.w -= .25 * gw; s.bl -= 1.2 * gb;
      return Math.abs(.25 * gw) + Math.abs(1.2 * gb);
    };
    L.drag(c, {
      hit: (x, y) => {
        if (!v) return null;
        const list = s.mode === 'linear' ? s.pts : s.cls;
        const i = list.findIndex(([px, py]) => Math.hypot(v.sx(px) - x, v.sy(s.mode === 'linear' ? py : py) - y) < 12);
        return i < 0 ? null : i;
      },
      move: (i, x, y) => {
        if (s.mode === 'linear') s.pts[i] = [clamp(v.ix(x), 0, 10), clamp(v.iy(y), 0, 10)];
        else s.cls[i] = [clamp(v.ix(x), 0, 10), v.iy(y) > .5 ? 1 : 0];
        changed();
      },
      down: (x, y) => {
        if (s.mode === 'linear') s.pts.push([clamp(v.ix(x), 0, 10), clamp(v.iy(y), 0, 10)]);
        else s.cls.push([clamp(v.ix(x), 0, 10), v.iy(y) > .5 ? 1 : 0]);
        changed();
      },
    });
    function changed() { L.redraw(); update(); }
    function update() {
      if (s.mode === 'linear') {
        const errs = s.pts.map(([x, y]) => (s.m * x + s.b - y) ** 2);
        const mse = errs.reduce((a, e) => a + e, 0) / errs.length, worst = Math.max(...errs);
        L.stats([['MSE', fmtN(mse, 3), 'accent'], ['m', fmtN(s.m)], ['b', fmtN(s.b)], ['points', s.pts.length]]);
        L.insight(worst / (mse * errs.length) > .45 && errs.length > 4
          ? `<b>One point owns ${Math.round(worst / (mse * errs.length) * 100)}% of the total squared error.</b> Squaring makes far-away points dominate, so least squares is pulled hard by outliers.`
          : '<b>Least squares picks the line with the smallest total square area.</b> Gradient descent reaches the same line the normal equation computes in one shot.');
      } else {
        const probs = s.cls.map(([x]) => sig(s.w * x + s.bl));
        const ll = -s.cls.reduce((a, [, y], i) => a + (y ? Math.log(probs[i] + 1e-9) : Math.log(1 - probs[i] + 1e-9)), 0) / s.cls.length;
        const acc = s.cls.filter(([, y], i) => (probs[i] > .5) === !!y).length / s.cls.length;
        const boundary = -s.bl / s.w;
        L.stats([['log loss', fmtN(ll, 3), 'accent'], ['accuracy', `${Math.round(acc * 100)}%`], ['decision boundary x', Number.isFinite(boundary) ? fmtN(boundary, 2) : '—']]);
        L.insight(`<b>σ(w·x + b) turns a score into a probability.</b> The dashed line is where it crosses 50%. A larger w makes the S-curve steeper, meaning more confident predictions. Log loss punishes confident mistakes hardest.`);
      }
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      if (s.mode === 'linear') {
        v = D.view(c, { x0: 0, x1: 10, y0: 0, y1: 10, pad: 14, padL: 30, padB: 24 });
        D.axes(ctx, v, P, { xTicks: [0, 2, 4, 6, 8, 10], yTicks: [2, 4, 6, 8, 10] });
        ctx.save(); ctx.beginPath(); ctx.rect(v.sx(0), v.sy(10), v.sx(10) - v.sx(0), v.sy(0) - v.sy(10)); ctx.clip();
        s.pts.forEach(([x, y]) => {
          const yh = s.m * x + s.b, e = y - yh;
          if (s.squares) {
            const side = Math.abs(e) * v.ky;
            ctx.fillStyle = P.alpha('err', .14); ctx.strokeStyle = P.alpha('err', .5); ctx.lineWidth = 1;
            const px = v.sx(x), top = Math.min(v.sy(y), v.sy(yh));
            ctx.fillRect(px, top, side, side); ctx.strokeRect(px, top, side, side);
          }
          D.line(ctx, v.sx(x), v.sy(y), v.sx(x), v.sy(yh), P.err, 1.4);
        });
        D.line(ctx, v.sx(0), v.sy(s.b), v.sx(10), v.sy(s.m * 10 + s.b), P.accent, 3);
        ctx.restore();
        s.pts.forEach(([x, y]) => D.dot(ctx, v.sx(x), v.sy(y), 6, P.series[0], P.surface, 2));
      } else {
        v = D.view(c, { x0: 0, x1: 10, y0: -.15, y1: 1.15, pad: 14, padL: 34, padB: 24 });
        D.axes(ctx, v, P, { xTicks: [0, 2, 4, 6, 8, 10], yTicks: [0, .5, 1] });
        const bx = -s.bl / s.w;
        if (Number.isFinite(bx) && bx > 0 && bx < 10) {
          ctx.fillStyle = P.alpha(P.series[0], .08);
          const left = s.w > 0;
          ctx.fillRect(left ? v.sx(0) : v.sx(bx), v.sy(1.15), left ? v.sx(bx) - v.sx(0) : v.sx(10) - v.sx(bx), v.sy(-.15) - v.sy(1.15));
          ctx.fillStyle = P.alpha('accent', .08);
          ctx.fillRect(left ? v.sx(bx) : v.sx(0), v.sy(1.15), left ? v.sx(10) - v.sx(bx) : v.sx(bx) - v.sx(0), v.sy(-.15) - v.sy(1.15));
          D.line(ctx, v.sx(bx), v.sy(-.15), v.sx(bx), v.sy(1.15), P.dim, 1.5, [5, 4]);
        }
        D.curve(ctx, v, x => sig(s.w * x + s.bl), P.accent, 3);
        s.cls.forEach(([x, y]) => {
          const p = sig(s.w * x + s.bl);
          D.line(ctx, v.sx(x), v.sy(y), v.sx(x), v.sy(p), P.alpha('err', .6), 1.2, [2, 3]);
          D.dot(ctx, v.sx(x), v.sy(y), 6.5, y ? P.accent : P.series[0], P.surface, 2);
        });
        D.text(ctx, 'class 1', v.sx(10) - 4, v.sy(1) - 12, { color: P.accent, size: 11, align: 'right', weight: 600 });
        D.text(ctx, 'class 0', v.sx(10) - 4, v.sy(0) + 12, { color: P.series[0], size: 11, align: 'right', weight: 600 });
      }
    };
    build();
    modeSeg.set(s.mode, true);
  },
});

defineLab('tree', {
  title: 'Decision trees and random forests',
  hint: 'Each split is a straight cut that makes both sides purer (lower Gini). Raise the depth and watch the boxes get tiny.',
  mount(L, opts) {
    const s = { depth: 3, forest: !!opts.forest, noise: 10, seed: 4, data: [], model: null };
    const c = L.canvas(w => Math.min(340, w * .58));
    L.seg('', [['tree', 'One tree'], ['forest', 'Random forest (25 trees)']], s.forest ? 'forest' : 'tree', m => { s.forest = m === 'forest'; fit(); });
    L.slider('max depth', { min: 0, max: 8, step: 1, value: s.depth }, v => { s.depth = v; fit(); });
    L.slider('label noise', { min: 0, max: 30, step: 1, value: s.noise, fmt: v => `${v}%` }, v => { s.noise = v; gen(); });
    L.button('New data', () => { s.seed++; gen(); });
    const gini = p => 2 * p * (1 - p);
    function gen() {
      const r = rng(s.seed * 101);
      s.data = Array.from({ length: 150 }, () => {
        const x = r(), y = r();
        let c1 = (Math.hypot(x - .62, y - .58) < .26) || (x < .3 && y < .35);
        if (r() < s.noise / 100) c1 = !c1;
        return { x, y, c: c1 ? 1 : 0 };
      });
      fit();
    }
    function build(pts, depth, r) {
      const n = pts.length, ones = pts.reduce((a, p) => a + p.c, 0), p1 = n ? ones / n : 0;
      const node = { p: p1, n, g: gini(p1) };
      if (depth >= s.depth || n < 4 || p1 === 0 || p1 === 1) return node;
      let best = null;
      const feats = r ? [r() < .5 ? 'x' : 'y'] : ['x', 'y'];
      for (const f of feats) {
        const sorted = [...pts].sort((a, b) => a[f] - b[f]);
        let left = 0;
        for (let i = 0; i < n - 1; i++) {
          left += sorted[i].c;
          if (sorted[i][f] === sorted[i + 1][f]) continue;
          const nl = i + 1, nr = n - nl;
          if (nl < 2 || nr < 2) continue;
          const g = (nl * gini(left / nl) + nr * gini((ones - left) / nr)) / n;
          if (!best || g < best.g) best = { g, f, t: (sorted[i][f] + sorted[i + 1][f]) / 2 };
        }
      }
      if (!best || best.g >= node.g - 1e-9) return node;
      Object.assign(node, { f: best.f, t: best.t, gain: node.g - best.g });
      node.l = build(pts.filter(p => p[best.f] < best.t), depth + 1, r);
      node.r = build(pts.filter(p => p[best.f] >= best.t), depth + 1, r);
      return node;
    }
    const predict = (node, p) => node.f ? predict(p[node.f] < node.t ? node.l : node.r, p) : node.p;
    const leaves = node => node.f ? leaves(node.l) + leaves(node.r) : 1;
    function fit() {
      if (s.forest) {
        const r = rng(s.seed * 7 + s.depth);
        s.model = Array.from({ length: 25 }, () => build(Array.from({ length: s.data.length }, () => s.data[Math.floor(r() * s.data.length)]), 0, r));
      } else s.model = [build(s.data, 0, null)];
      const pr = p => s.model.reduce((a, t) => a + predict(t, p), 0) / s.model.length;
      const acc = s.data.filter(p => (pr(p) > .5) === !!p.c).length / s.data.length;
      const root = s.model[0];
      L.stats([['root Gini', fmtN(gini(s.data.reduce((a, p) => a + p.c, 0) / s.data.length), 3)], !s.forest && root.gain !== undefined && ['1st split gain', fmtN(root.gain, 3)], ['train accuracy', `${Math.round(acc * 100)}%`, 'accent'], !s.forest && ['leaves', leaves(root)]]);
      L.insight(s.depth === 0 ? '<b>Depth 0: one leaf that predicts the majority class everywhere.</b> Maximum bias.'
        : !s.forest && s.depth >= 6 ? `<b>Depth ${s.depth}: ${Math.round(acc * 100)}% on the training data</b>, but look at the tiny boxes drawn around single noisy points. That is overfitting: high variance.`
        : s.forest ? '<b>25 trees, each trained on a bootstrap sample with random features.</b> Individually they overfit in different ways; averaging them cancels much of that out, so the boundary is smoother.'
        : `<b>Depth ${s.depth}.</b> Every split is chosen greedily to lower the weighted Gini impurity of its two sides.`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, v = D.view(c, { x0: 0, x1: 1, y0: 0, y1: 1, pad: 8 });
      const G = 56, cw = (v.sx(1) - v.sx(0)) / G, ch = (v.sy(0) - v.sy(1)) / G;
      const colA = P.rgb(P.series[0]), colB = P.rgb('accent');
      for (let i = 0; i < G; i++) for (let j = 0; j < G; j++) {
        const p = { x: (i + .5) / G, y: (j + .5) / G };
        const q = s.model.reduce((a, t) => a + predict(t, p), 0) / s.model.length;
        const col = colA.map((a, k) => Math.round(lerp(a, colB[k], q)));
        ctx.fillStyle = `rgba(${col.join(',')},.22)`;
        ctx.fillRect(v.sx(i / G), v.sy((j + 1) / G), cw + .5, ch + .5);
      }
      if (!s.forest) {
        const drawSplits = (node, x0, x1, y0, y1) => {
          if (!node.f) return;
          if (node.f === 'x') { D.line(ctx, v.sx(node.t), v.sy(y0), v.sx(node.t), v.sy(y1), P.text, 1.4); drawSplits(node.l, x0, node.t, y0, y1); drawSplits(node.r, node.t, x1, y0, y1); }
          else { D.line(ctx, v.sx(x0), v.sy(node.t), v.sx(x1), v.sy(node.t), P.text, 1.4); drawSplits(node.l, x0, x1, y0, node.t); drawSplits(node.r, x0, x1, node.t, y1); }
        };
        drawSplits(s.model[0], 0, 1, 0, 1);
      }
      s.data.forEach(p => D.dot(ctx, v.sx(p.x), v.sy(p.y), 4.2, p.c ? P.accent : P.series[0], P.surface, 1.2));
    };
    gen();
  },
});

defineLab('kmeans', {
  title: 'K-means, one step at a time',
  hint: 'Assign every point to its nearest centroid, then move each centroid to the middle of its points. Repeat.',
  mount(L) {
    const s = { k: 4, seed: 2, pts: [], cent: [], trail: [], labels: [], phase: 'assign', iter: 0, changed: -1 };
    const c = L.canvas(w => Math.min(340, w * .58));
    L.slider('k (clusters)', { min: 2, max: 8, step: 1, value: s.k }, v => { s.k = v; init(); });
    let acc = 0;
    const play = L.loop(dt => { acc += dt; if (acc > .55) { acc = 0; step(); } if (s.changed === 0 && s.phase === 'assign') return false; });
    L.playButton(play, ['Play', 'Pause'], () => { if (s.changed === 0) init(true); });
    L.button('Step', () => step());
    L.button('New random start', () => { s.seed++; init(true); });
    L.button('New data', () => { s.seed += 10; gen(); });
    function gen() {
      const r = rng(s.seed * 31);
      const centers = Array.from({ length: 4 }, () => [.15 + .7 * r(), .15 + .7 * r()]);
      s.pts = Array.from({ length: 220 }, (_, i) => { const [cx, cy] = centers[i % 4]; return [clamp(cx + gauss(r) * .075, 0, 1), clamp(cy + gauss(r) * .075, 0, 1)]; });
      init();
    }
    function init(keepData) {
      const r = rng(s.seed * 17 + s.k);
      s.cent = Array.from({ length: s.k }, () => [...s.pts[Math.floor(r() * s.pts.length)]]);
      s.trail = s.cent.map(p => [[...p]]);
      s.labels = new Array(s.pts.length).fill(-1);
      s.phase = 'assign'; s.iter = 0; s.changed = -1;
      update(); L.redraw();
    }
    function step() {
      if (s.phase === 'assign') {
        let changed = 0;
        s.pts.forEach((p, i) => {
          let best = 0, bd = Infinity;
          s.cent.forEach((q, j) => { const d = (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2; if (d < bd) { bd = d; best = j; } });
          if (s.labels[i] !== best) changed++;
          s.labels[i] = best;
        });
        s.changed = changed; s.phase = 'update'; s.iter++;
        update(); L.redraw();
      } else {
        const from = s.cent.map(p => [...p]);
        const to = s.cent.map((q, j) => {
          const mine = s.pts.filter((_, i) => s.labels[i] === j);
          return mine.length ? [mine.reduce((a, p) => a + p[0], 0) / mine.length, mine.reduce((a, p) => a + p[1], 0) / mine.length] : q;
        });
        s.phase = 'assign';
        L.tween(420, t => { s.cent = from.map((p, j) => [lerp(p[0], to[j][0], t), lerp(p[1], to[j][1], t)]); L.redraw(); },
          () => { s.cent.forEach((p, j) => s.trail[j].push([...p])); update(); });
      }
    }
    function update() {
      const inertia = s.labels[0] < 0 ? NaN : s.pts.reduce((a, p, i) => { const q = s.cent[s.labels[i]]; return a + (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2; }, 0);
      L.stats([['iteration', s.iter], ['next step', s.phase === 'assign' ? 'assign points' : 'move centroids'], ['inertia', fmtN(inertia, 3), 'accent'], s.changed >= 0 && ['points that switched', s.changed]]);
      L.insight(s.changed === 0 ? `<b>Converged after ${s.iter} iterations:</b> no point changed cluster. Try “New random start”: k-means can settle in a worse local minimum, which is why k-means++ picks smarter starting centroids.`
        : s.iter === 0 ? '<b>Random centroids.</b> Press Step to assign every point to its nearest one.'
        : s.phase === 'update' ? `<b>Assigned.</b> ${s.changed} points switched cluster. Next, each centroid moves to the mean of its points.`
        : '<b>Centroids moved.</b> Inertia (total squared distance) can only go down with each step.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, v = D.view(c, { x0: 0, x1: 1, y0: 0, y1: 1, pad: 12 });
      const col = j => P.series[j % P.series.length];
      if (s.phase === 'update') s.pts.forEach((p, i) => { const q = s.cent[s.labels[i]]; D.line(ctx, v.sx(p[0]), v.sy(p[1]), v.sx(q[0]), v.sy(q[1]), P.alpha(col(s.labels[i]), .18), 1); });
      s.pts.forEach((p, i) => D.dot(ctx, v.sx(p[0]), v.sy(p[1]), 3.6, s.labels[i] < 0 ? P.faint : col(s.labels[i])));
      s.trail.forEach((tr, j) => {
        ctx.beginPath(); tr.forEach(([x, y], i) => i ? ctx.lineTo(v.sx(x), v.sy(y)) : ctx.moveTo(v.sx(x), v.sy(y)));
        ctx.strokeStyle = P.alpha(col(j), .6); ctx.lineWidth = 1.5; ctx.setLineDash([3, 3]); ctx.stroke(); ctx.setLineDash([]);
      });
      s.cent.forEach(([x, y], j) => {
        D.dot(ctx, v.sx(x), v.sy(y), 10, P.surface, col(j), 3);
        D.line(ctx, v.sx(x) - 4, v.sy(y) - 4, v.sx(x) + 4, v.sy(y) + 4, col(j), 2.4);
        D.line(ctx, v.sx(x) - 4, v.sy(y) + 4, v.sx(x) + 4, v.sy(y) - 4, col(j), 2.4);
      });
    };
    gen();
  },
});

defineLab('pca', {
  title: 'PCA: find the direction of most variance',
  hint: 'Drag anywhere to rotate the axis. Every point drops onto it; PCA picks the axis where those shadows spread out the most.',
  mount(L) {
    const r = rng(12), ang = .55;
    const pts = Array.from({ length: 160 }, () => { const a = gauss(r) * 1.05, b = gauss(r) * .32; return [a * Math.cos(ang) - b * Math.sin(ang), a * Math.sin(ang) + b * Math.cos(ang)]; });
    const mx = pts.reduce((a, p) => a + p[0], 0) / pts.length, my = pts.reduce((a, p) => a + p[1], 0) / pts.length;
    pts.forEach(p => { p[0] -= mx; p[1] -= my; });
    const cxx = pts.reduce((a, p) => a + p[0] * p[0], 0) / pts.length, cyy = pts.reduce((a, p) => a + p[1] * p[1], 0) / pts.length, cxy = pts.reduce((a, p) => a + p[0] * p[1], 0) / pts.length;
    const pc1 = .5 * Math.atan2(2 * cxy, cxx - cyy), total = cxx + cyy;
    const s = { theta: -.6, pc2: false };
    const c = L.canvas(w => Math.min(340, w * .58));
    let v = null;
    L.button('Snap to PC1', () => { const from = s.theta; let to = pc1; while (to - from > Math.PI / 2) to -= Math.PI; while (from - to > Math.PI / 2) to += Math.PI; L.tween(700, t => { s.theta = lerp(from, to, t); changed(); }); }, 'primary');
    L.toggle('Show PC2', s.pc2, x => { s.pc2 = x; changed(); });
    L.drag(c, { hit: () => 'rot', move: (_, x, y) => { if (!v) return; s.theta = Math.atan2(v.iy(y), v.ix(x)); changed(); } });
    const varAlong = t => pts.reduce((a, [x, y]) => a + (x * Math.cos(t) + y * Math.sin(t)) ** 2, 0) / pts.length;
    function changed() {
      L.redraw();
      const captured = varAlong(s.theta) / total, best = varAlong(pc1) / total;
      L.stats([['variance captured', `${(captured * 100).toFixed(1)}%`, 'accent'], ['best possible (PC1)', `${(best * 100).toFixed(1)}%`], ['angle', `${((s.theta * 180 / Math.PI) % 180).toFixed(0)}°`]]);
      L.insight(captured > best - .005
        ? `<b>This is PC1.</b> Projecting 2D points onto this one axis keeps ${(best * 100).toFixed(0)}% of the variance. PC2 is perpendicular and holds the rest. Dimensionality reduction keeps the top few such axes.`
        : `<b>${(captured * 100).toFixed(0)}% captured.</b> The shadows on the axis are bunched up, so information is lost. Rotate until they spread out as far as possible.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      v = D.view(c, { x0: -3, x1: 3, y0: -2, y1: 2, pad: 10, equal: true });
      D.grid(ctx, v, P, 1);
      const ux = Math.cos(s.theta), uy = Math.sin(s.theta);
      if (s.pc2) D.line(ctx, v.sx(-4 * Math.cos(pc1 + Math.PI / 2)), v.sy(-4 * Math.sin(pc1 + Math.PI / 2)), v.sx(4 * Math.cos(pc1 + Math.PI / 2)), v.sy(4 * Math.sin(pc1 + Math.PI / 2)), P.series[4], 2, [6, 5]);
      D.line(ctx, v.sx(-5 * ux), v.sy(-5 * uy), v.sx(5 * ux), v.sy(5 * uy), P.accent, 2.4);
      pts.forEach(([x, y]) => {
        const d = x * ux + y * uy;
        D.line(ctx, v.sx(x), v.sy(y), v.sx(d * ux), v.sy(d * uy), P.alpha('faint', .35), 1);
      });
      pts.forEach(([x, y]) => D.dot(ctx, v.sx(x), v.sy(y), 3.4, P.series[0]));
      pts.forEach(([x, y]) => { const d = x * ux + y * uy; D.dot(ctx, v.sx(d * ux), v.sy(d * uy), 2.6, P.accent); });
    };
    changed();
  },
});

defineLab('activation', {
  title: 'Activation functions and their slopes',
  hint: 'Hover over the plot to read values. Switch on derivatives to see where gradients vanish.',
  mount(L) {
    const F = {
      sigmoid: [x => 1 / (1 + Math.exp(-x)), 'Sigmoid'], tanh: [Math.tanh, 'Tanh'], relu: [x => Math.max(0, x), 'ReLU'],
      leaky: [x => x > 0 ? x : .1 * x, 'Leaky ReLU'], gelu: [x => .5 * x * (1 + Math.tanh(Math.sqrt(2 / Math.PI) * (x + .047351 * x ** 3))), 'GELU'],
      swish: [x => x / (1 + Math.exp(-x)), 'SiLU / Swish'],
    };
    const s = { on: { sigmoid: true, tanh: false, relu: true, leaky: false, gelu: true, swish: false }, deriv: false, hx: null };
    const c = L.canvas(w => Math.min(320, w * .54));
    let v = null;
    L.toggle('Show derivatives', s.deriv, x => { s.deriv = x; changed(); });
    Object.entries(F).forEach(([k, [, label]]) => L.toggle(label, s.on[k], x => { s.on[k] = x; changed(); }));
    const d = f => x => (f(x + 1e-4) - f(x - 1e-4)) / 2e-4;
    const col = k => L.P.series[Object.keys(F).indexOf(k)];
    L.drag(c, { hover: x => { s.hx = x == null || !v ? null : clamp(v.ix(x), -6, 6); changed(); } });
    function changed() {
      L.redraw();
      const x = s.hx ?? 1;
      L.stats([['x', fmtN(x, 2)], ...Object.keys(F).filter(k => s.on[k]).map(k => [F[k][1], fmtN((s.deriv ? d(F[k][0]) : F[k][0])(x), 3), '', col(k)])]);
      L.insight(s.deriv
        ? '<b>The shaded band is where sigmoid’s slope is below 0.05.</b> Its slope never exceeds 0.25, so ten stacked sigmoids shrink a gradient by at least 0.25¹⁰ ≈ 10⁻⁶. ReLU’s slope is exactly 1 for x > 0, which is why deep nets switched to it; but it is 0 for x < 0 (“dead” neurons), which GELU and Leaky ReLU soften.'
        : '<b>Without a non-linearity, stacked layers collapse into one linear map.</b> These functions bend the space so a network can model curved decision boundaries.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c;
      v = D.view(c, { x0: -6, x1: 6, y0: s.deriv ? -.2 : -1.4, y1: s.deriv ? 1.3 : 3.2, pad: 12, padL: 34, padB: 22 });
      D.axes(ctx, v, P, { xTicks: [-6, -4, -2, 0, 2, 4, 6], yTicks: s.deriv ? [0, .25, .5, 1] : [-1, 0, 1, 2, 3] });
      if (s.deriv && s.on.sigmoid) {
        const lim = 3.66;
        ctx.fillStyle = P.alpha('err', .08);
        ctx.fillRect(v.sx(-6), v.sy(v.y1), v.sx(-lim) - v.sx(-6), v.sy(v.y0) - v.sy(v.y1));
        ctx.fillRect(v.sx(lim), v.sy(v.y1), v.sx(6) - v.sx(lim), v.sy(v.y0) - v.sy(v.y1));
        D.text(ctx, 'vanishing-gradient zone', v.sx(-5.9), v.sy(v.y1) + 12, { color: P.err, size: 10.5, weight: 600 });
      }
      Object.keys(F).forEach(k => { if (s.on[k]) D.curve(ctx, v, s.deriv ? d(F[k][0]) : F[k][0], col(k), 2.4, 300); });
      if (s.hx != null) {
        D.line(ctx, v.sx(s.hx), v.sy(v.y0), v.sx(s.hx), v.sy(v.y1), P.faint, 1, [3, 3]);
        Object.keys(F).forEach(k => { if (s.on[k]) D.dot(ctx, v.sx(s.hx), v.sy((s.deriv ? d(F[k][0]) : F[k][0])(s.hx)), 4.5, col(k), P.surface, 1.5); });
      }
    };
    changed();
  },
});

defineLab('init', {
  title: 'Weight initialization through 10 layers',
  hint: 'A batch goes through 10 layers of random weights. Each column shows the spread of that layer’s activations.',
  mount(L, opts) {
    const W = 96, DEPTH = 10, B = 24;
    const s = { scheme: 'xavier', act: 'tanh', ln: !!opts.ln, layers: [] };
    const c = L.canvas(w => Math.min(300, w * .5));
    L.seg('init', [['small', 'Too small (0.01)'], ['xavier', 'Xavier'], ['he', 'He / Kaiming'], ['large', 'Too large (1.0)']], s.scheme, v => { s.scheme = v; run(); });
    L.seg('activation', [['tanh', 'tanh'], ['relu', 'ReLU']], s.act, v => { s.act = v; run(); });
    L.toggle('Normalize each layer (LayerNorm)', s.ln, v => { s.ln = v; run(); });
    function run() {
      const r = rng(8);
      let h = Array.from({ length: B }, () => Float64Array.from({ length: W }, () => gauss(r)));
      const std = { small: .01, xavier: Math.sqrt(1 / W), he: Math.sqrt(2 / W), large: 1 }[s.scheme];
      s.layers = [];
      for (let l = 0; l < DEPTH; l++) {
        const M = Float64Array.from({ length: W * W }, () => gauss(r) * std);
        h = h.map(row => {
          const z = new Float64Array(W);
          for (let i = 0; i < W; i++) { let sum = 0; for (let j = 0; j < W; j++) sum += M[i * W + j] * row[j]; z[i] = sum; }
          if (s.ln) { const m = z.reduce((a, x) => a + x, 0) / W, sd = Math.sqrt(z.reduce((a, x) => a + (x - m) ** 2, 0) / W) || 1; for (let i = 0; i < W; i++) z[i] = (z[i] - m) / sd; }
          for (let i = 0; i < W; i++) z[i] = s.act === 'tanh' ? Math.tanh(z[i]) : Math.max(0, z[i]);
          return z;
        });
        const all = h.flatMap(row => [...row]);
        const m = all.reduce((a, x) => a + x, 0) / all.length;
        s.layers.push({ all, std: Math.sqrt(all.reduce((a, x) => a + (x - m) ** 2, 0) / all.length), sat: all.filter(x => Math.abs(x) > .97).length / all.length, dead: all.filter(x => x === 0).length / all.length });
      }
      const first = s.layers[0], last = s.layers[DEPTH - 1];
      L.stats([['std layer 1', fmtN(first.std, 3)], ['std layer 10', fmtN(last.std, 3), 'accent'], s.act === 'tanh' ? ['saturated (|h| > 0.97)', `${Math.round(last.sat * 100)}%`] : ['zeros at layer 10', `${Math.round(last.dead * 100)}%`]]);
      L.insight(s.ln ? '<b>With normalization the spread is reset every layer</b>, so even a bad initialization cannot make activations vanish or explode. That is a big part of why LayerNorm/BatchNorm made deep nets trainable.'
        : last.std < .02 ? '<b>Activations collapse towards 0.</b> The backward pass multiplies by the same small weights, so gradients vanish too and early layers stop learning.'
        : s.act === 'tanh' && last.sat > .4 ? '<b>Activations pile up at ±1.</b> tanh is saturated, its slope is ≈ 0 there, and gradients vanish again, from the other side.'
        : last.std > 50 ? '<b>Activations explode.</b> Each layer multiplies the scale up; the loss will become NaN.'
        : `<b>Stable signal.</b> The spread stays roughly constant across all 10 layers. ${s.act === 'relu' ? 'He init doubles the variance to make up for ReLU zeroing half the units.' : 'Xavier sets variance to 1/fan-in so each layer preserves scale.'}`);
      L.redraw();
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, top = 18, base = c.h - 44, colW = (c.w - 30) / DEPTH;
      const lim = s.act === 'tanh' ? 1 : Math.max(.05, ...s.layers.map(l => l.std * 3));
      D.text(ctx, s.act === 'tanh' ? '+1' : fmtN(lim, 1), 4, top, { color: P.faint, size: 10, mono: true });
      D.text(ctx, s.act === 'tanh' ? '−1' : '0', 4, base, { color: P.faint, size: 10, mono: true });
      s.layers.forEach((layer, l) => {
        const x = 26 + l * colW, bins = 36, counts = new Array(bins).fill(0);
        const lo = s.act === 'tanh' ? -1 : 0;
        layer.all.forEach(val => { const i = Math.floor((val - lo) / (lim - lo) * bins); if (i >= 0 && i < bins) counts[i]++; else if (i >= bins) counts[bins - 1]++; });
        const mx = Math.max(...counts) || 1, bh = (base - top) / bins;
        counts.forEach((k, i) => {
          const wdt = k / mx * (colW - 10);
          ctx.fillStyle = P.alpha('accent', .75);
          ctx.fillRect(x + (colW - 10 - wdt) / 2, base - (i + 1) * bh, wdt, bh - .5);
        });
        D.text(ctx, `L${l + 1}`, x + (colW - 10) / 2, base + 12, { color: P.dim, size: 10.5, align: 'center' });
        D.text(ctx, fmtN(layer.std, 2), x + (colW - 10) / 2, base + 27, { color: P.faint, size: 9.5, align: 'center', mono: true });
      });
    };
    run();
  },
});

defineLab('convolution', {
  title: 'Slide a kernel over an image',
  hint: 'Click pixels to draw. Each output cell is the sum of the 3×3 patch under the kernel, multiplied weight by weight.',
  mount(L) {
    const N = 10, O = N - 2;
    const img = new Float64Array(N * N);
    [[1, 2], [1, 3], [1, 4], [1, 5], [1, 6], [1, 7], [2, 7], [3, 7], [4, 7], [5, 7], [6, 7], [6, 6], [6, 5], [6, 4], [6, 3], [6, 2], [5, 2], [4, 2], [3, 2], [2, 2], [3, 4], [4, 5], [8, 1], [8, 2], [8, 3], [8, 4], [8, 5], [8, 6], [8, 7], [8, 8]]
      .forEach(([r, q]) => { img[r * N + q] = 1; });
    const K = {
      sobelx: ['Vertical edges', [-1, 0, 1, -2, 0, 2, -1, 0, 1]], sobely: ['Horizontal edges', [-1, -2, -1, 0, 0, 0, 1, 2, 1]],
      blur: ['Blur', [1, 2, 1, 2, 4, 2, 1, 2, 1].map(x => x / 16)], sharpen: ['Sharpen', [0, -1, 0, -1, 5, -1, 0, -1, 0]],
      outline: ['Outline', [-1, -1, -1, -1, 8, -1, -1, -1, -1]],
    };
    const s = { k: 'sobelx', cur: 20, paint: null };
    const c = L.canvas(w => Math.min(300, (w - 40) / 2.55 + 30));
    let geo = null;
    L.seg('kernel', Object.entries(K).map(([k, [l]]) => [k, l]), s.k, v => { s.k = v; changed(); });
    let acc = 0;
    const play = L.loop(dt => { acc += dt; if (acc > .16) { acc = 0; s.cur++; changed(); } if (s.cur >= O * O) return false; });
    L.playButton(play, ['Slide the kernel', 'Pause'], () => { if (s.cur >= O * O) s.cur = 0; });
    L.button('Step', () => { s.cur = (s.cur + 1) % (O * O + 1); changed(); });
    L.button('Show full output', () => { play.stop(); s.cur = O * O; changed(); });
    const out = () => {
      const o = new Float64Array(O * O), k = K[s.k][1];
      for (let r = 0; r < O; r++) for (let q = 0; q < O; q++) {
        let sum = 0;
        for (let i = 0; i < 3; i++) for (let j = 0; j < 3; j++) sum += img[(r + i) * N + q + j] * k[i * 3 + j];
        o[r * O + q] = sum;
      }
      return o;
    };
    L.drag(c, {
      hit: (x, y) => {
        if (!geo) return null;
        const q = Math.floor((x - geo.ix) / geo.cell), r = Math.floor((y - geo.iy) / geo.cell);
        return q >= 0 && q < N && r >= 0 && r < N ? { set: img[r * N + q] ? 0 : 1 } : null;
      },
      move: (t, x, y) => {
        const q = Math.floor((x - geo.ix) / geo.cell), r = Math.floor((y - geo.iy) / geo.cell);
        if (q >= 0 && q < N && r >= 0 && r < N) { img[r * N + q] = t.set; changed(); }
      },
    });
    function changed() {
      L.redraw();
      const o = out(), i = Math.min(s.cur, O * O - 1), r = Math.floor(i / O), q = i % O, k = K[s.k][1];
      const terms = [];
      for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) { const px = img[(r + a) * N + q + b]; if (px && k[a * 3 + b]) terms.push(fmtN(k[a * 3 + b], 2)); }
      L.stats([['window at', `row ${r + 1}, col ${q + 1}`], ['output', fmtN(o[i], 2), 'accent'], ['sum of weights × pixels', terms.length ? terms.join(' + ').replace(/\+ -/g, '− ') : '0']]);
      const tips = {
        sobelx: 'lights up (orange) where brightness rises left→right and goes negative (red) where it falls. Flat areas give 0, because the weights sum to 0.',
        sobely: 'responds to changes from top to bottom, so horizontal strokes light up.',
        blur: 'averages each pixel with its neighbours. Weights sum to 1, so overall brightness is kept.',
        sharpen: 'boosts a pixel against its neighbours, exaggerating edges.',
        outline: 'is zero wherever the patch is uniform and large wherever the centre differs, so only outlines survive.',
      };
      L.insight(`<b>${K[s.k][0]}:</b> this kernel ${tips[s.k]} A CNN learns kernels like these by gradient descent instead of hand-picking them.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, cell = Math.min((c.h - 30) / N, (c.w - 40) / (N + 3 + O + 1.2));
      const ix = 8, iy = 22, kx = ix + N * cell + cell * .6, ox = kx + 3 * cell + cell * .6, oy = iy + cell;
      geo = { ix, iy, cell };
      const i = Math.min(s.cur, O * O - 1), wr = Math.floor(i / O), wq = i % O, o = out(), mx = Math.max(1e-9, ...[...o].map(Math.abs)), k = K[s.k][1];
      D.text(ctx, 'input (click to draw)', ix, 10, { color: P.dim, size: 11 });
      for (let r = 0; r < N; r++) for (let q = 0; q < N; q++) {
        ctx.fillStyle = P.mix('surface2', 'text', img[r * N + q] * .9);
        ctx.fillRect(ix + q * cell + .5, iy + r * cell + .5, cell - 1, cell - 1);
      }
      if (s.cur < O * O) { ctx.strokeStyle = P.accent; ctx.lineWidth = 2.5; ctx.strokeRect(ix + wq * cell, iy + wr * cell, 3 * cell, 3 * cell); }
      D.text(ctx, 'kernel', kx, iy + cell * .5, { color: P.dim, size: 11 });
      for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) {
        const w = k[a * 3 + b], x = kx + b * cell, y = oy + a * cell;
        ctx.fillStyle = w > 0 ? P.alpha('accent', Math.min(.8, Math.abs(w) / 4 + .12)) : w < 0 ? P.alpha('err', Math.min(.8, Math.abs(w) / 4 + .12)) : P.surface2;
        ctx.fillRect(x + .5, y + .5, cell - 1, cell - 1);
        D.text(ctx, Number.isInteger(w) ? String(w) : w.toFixed(2).replace(/^0/, ''), x + cell / 2, y + cell / 2, { color: P.text, size: Math.min(12, cell * .36), align: 'center', mono: true });
      }
      D.text(ctx, 'output', ox, 10, { color: P.dim, size: 11 });
      for (let r = 0; r < O; r++) for (let q = 0; q < O; q++) {
        const idx = r * O + q, x = ox + q * cell, y = iy + cell + r * cell;
        if (idx > s.cur - (s.cur >= O * O ? 1 : 0)) { ctx.strokeStyle = P.soft; ctx.lineWidth = 1; ctx.strokeRect(x + .5, y + .5, cell - 1, cell - 1); continue; }
        const val = o[idx] / mx;
        ctx.fillStyle = val >= 0 ? P.alpha('accent', Math.abs(val) * .9 + .04) : P.alpha('err', Math.abs(val) * .9 + .04);
        ctx.fillRect(x + .5, y + .5, cell - 1, cell - 1);
      }
      if (s.cur < O * O) { ctx.strokeStyle = P.text; ctx.lineWidth = 2; ctx.strokeRect(ox + wq * cell, iy + cell + wr * cell, cell, cell); }
    };
    changed();
  },
});

defineLab('rnn', {
  title: 'Why gradients vanish through time',
  hint: 'The loss is at the last step. Its gradient is multiplied by the same factor at every step on the way back.',
  mount(L, opts) {
    const T = 24;
    const s = { lstm: !!opts.lstm, w: .9, f: .97, pulse: -1 };
    const c = L.canvas(w => Math.min(280, w * .45));
    L.seg('', [['rnn', 'Vanilla RNN'], ['lstm', 'LSTM (cell state)']], s.lstm ? 'lstm' : 'rnn', v => { s.lstm = v === 'lstm'; changed(); });
    L.slider('recurrent weight |W| (RNN)', { min: .5, max: 1.8, step: .01, value: s.w, fmt: v => v.toFixed(2) }, v => { s.w = v; changed(); });
    L.slider('forget gate f (LSTM)', { min: .5, max: 1, step: .005, value: s.f, fmt: v => v.toFixed(3) }, v => { s.f = v; changed(); });
    const play = L.loop(dt => { s.pulse += dt * 9; L.redraw(); if (s.pulse > T) { s.pulse = -1; return false; } });
    L.playButton(play, ['Backpropagate', 'Pause'], () => { s.pulse = 0; });
    const factor = () => s.lstm ? s.f : s.w * .75;
    const grad = k => factor() ** (T - 1 - k);
    function changed() {
      L.redraw();
      const g1 = grad(0), fac = factor();
      L.stats([['factor per step', fmtN(fac, 3), 'accent'], ['gradient reaching step 1', fmtN(g1, 2), g1 < .01 || g1 > 100 ? 'err' : 'ok']]);
      L.insight(s.lstm
        ? `<b>The LSTM cell state is a highway:</b> the gradient is multiplied by the forget gate (${s.f.toFixed(2)}) instead of W·tanh′. With f near 1, ${fmtN(g1 * 100, 1)}% of the signal still reaches step 1, so the model can learn long-range dependencies.`
        : g1 < .01 ? `<b>Vanishing:</b> ${fmtN(fac, 2)}²³ ≈ ${fmtN(g1, 1)}. Step 1 receives essentially no learning signal, so a vanilla RNN forgets the start of the sentence.`
        : g1 > 100 ? `<b>Exploding:</b> ${fmtN(fac, 2)}²³ ≈ ${fmtN(g1, 1)}. Updates blow up; gradient clipping is the standard fix.`
        : '<b>Balanced right at the edge.</b> Only a factor of almost exactly 1 keeps the gradient alive, which is impossible to hold throughout training.');
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, cw = (c.w - 20) / T, base = c.h - 52, top = 22;
      const toY = g => { const lg = clamp(Math.log10(g), -8, 4); return base - (lg + 8) / 12 * (base - top); };
      [-8, -4, 0, 4].forEach(e => { D.line(ctx, 10, toY(10 ** e), c.w - 10, toY(10 ** e), e === 0 ? P.strong : P.soft, 1); D.text(ctx, `10^${e}`, c.w - 12, toY(10 ** e) - 7, { color: P.faint, size: 9.5, align: 'right', mono: true }); });
      for (let k = 0; k < T; k++) {
        const g = grad(k), x = 10 + k * cw, reached = s.pulse < 0 || T - 1 - k <= s.pulse;
        const color = g < .01 ? P.faint : g > 100 ? P.err : P.accent;
        const y = toY(g);
        ctx.fillStyle = reached ? P.alpha(color === P.faint ? 'faint' : color, .8) : P.alpha('faint', .12);
        D.rrect(ctx, x + 2, Math.min(y, toY(1)), cw - 4, Math.abs(toY(1) - y) || 2, 2); ctx.fill();
        ctx.fillStyle = P.surface2; D.rrect(ctx, x + 2, base + 10, cw - 4, 20, 4); ctx.fill();
        ctx.strokeStyle = k === T - 1 ? P.accent : P.strong; ctx.lineWidth = 1; ctx.stroke();
        if (cw > 18) D.text(ctx, String(k + 1), x + cw / 2, base + 20, { color: P.dim, size: 9.5, align: 'center', mono: true });
      }
      D.text(ctx, 'time step →   loss is computed here ↘', 10, c.h - 8, { color: P.faint, size: 10.5 });
      D.text(ctx, '|∂L/∂hₖ| (log scale)', 10, 10, { color: P.dim, size: 11 });
      if (s.pulse >= 0) { const k = T - 1 - s.pulse; D.dot(ctx, 10 + (k + .5) * cw, base + 20, 6, P.err); }
    };
    changed();
  },
});

defineLab('diffusion', {
  title: 'Diffusion: destroy an image with noise, then undo it',
  hint: 'Forward process: add a little Gaussian noise at each of 1,000 steps. A diffusion model learns to run it backwards.',
  mount(L) {
    const N = 32, T = 1000, r = rng(31);
    const x0 = new Float64Array(N * N), eps = Float64Array.from({ length: N * N }, () => gauss(r));
    for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) {
      const d = Math.hypot(i - 15.5, j - 15.5);
      let v = -1;
      if (d < 13) v = .55;
      if (Math.hypot(i - 11, j - 11) < 2.2 || Math.hypot(i - 11, j - 20) < 2.2) v = -.8;
      if (d > 5.5 && d < 8 && i > 16) v = -.8;
      x0[i * N + j] = v;
    }
    const sched = kind => {
      const a = new Float64Array(T + 1);
      a[0] = 1;
      if (kind === 'linear') { let p = 1; for (let t = 1; t <= T; t++) { p *= 1 - (1e-4 + (.02 - 1e-4) * (t - 1) / (T - 1)); a[t] = p; } }
      else { const f = t => Math.cos((t / T + .008) / 1.008 * Math.PI / 2) ** 2; for (let t = 0; t <= T; t++) a[t] = f(t) / f(0); }
      return a;
    };
    const s = { t: 250, kind: 'cosine', abar: sched('cosine'), dir: 0 };
    const c = L.canvas(w => Math.min(280, w * .44));
    const off = document.createElement('canvas'); off.width = off.height = N;
    const octx = off.getContext('2d');
    L.seg('noise schedule', [['linear', 'Linear'], ['cosine', 'Cosine']], s.kind, v => { s.kind = v; s.abar = sched(v); changed(); });
    const tS = L.slider('timestep t', { min: 0, max: T, step: 1, value: s.t }, v => { s.t = v; changed(); });
    const anim = L.loop(dt => {
      s.t = clamp(s.t + s.dir * dt * 380, 0, T);
      tS.set(Math.round(s.t), true); changed();
      if (s.t <= 0 || s.t >= T) return false;
    });
    L.button('Add noise →', () => { s.dir = 1; if (s.t >= T) s.t = 0; anim.start(); }, 'primary');
    L.button('← Denoise', () => { s.dir = -1; if (s.t <= 0) s.t = T; anim.start(); }, 'primary');
    function changed() {
      L.redraw();
      const a = s.abar[Math.round(s.t)];
      L.stats([['t', Math.round(s.t)], ['ᾱₜ', fmtN(a, 3), 'accent'], ['signal √ᾱ', `${Math.round(Math.sqrt(a) * 100)}%`], ['noise √(1−ᾱ)', `${Math.round(Math.sqrt(1 - a) * 100)}%`]]);
      L.insight(s.t < 80 ? '<b>Barely noisy.</b> Early steps remove only fine detail.'
        : a < .02 ? '<b>Pure noise.</b> Nothing of the face is left; this is where generation starts. Each reverse step, a trained network predicts the noise ε and subtracts a little of it.'
        : `<b>x_t = √ᾱₜ · x₀ + √(1 − ᾱₜ) · ε.</b> You can jump to any t in one shot instead of adding noise 1,000 times. ${s.kind === 'cosine' ? 'The cosine schedule destroys information more gradually than linear, which helps small images.' : 'The linear schedule reaches near-pure noise well before t = 1000.'}`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, size = c.h - 30, a = s.abar[Math.round(s.t)], sa = Math.sqrt(a), sn = Math.sqrt(1 - a);
      const img = octx.createImageData(N, N), lo = P.rgb('bg'), hi = P.rgb('text');
      for (let i = 0; i < N * N; i++) {
        const v = clamp((sa * x0[i] + sn * eps[i] + 1) / 2, 0, 1);
        for (let ch = 0; ch < 3; ch++) img.data[i * 4 + ch] = lerp(lo[ch], hi[ch], v);
        img.data[i * 4 + 3] = 255;
      }
      octx.putImageData(img, 0, 0);
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(off, 10, 20, size, size);
      D.text(ctx, `x at t = ${Math.round(s.t)}`, 10, 10, { color: P.dim, size: 11 });
      const v = D.view({ w: c.w - size - 30, h: c.h }, { x0: 0, x1: T, y0: 0, y1: 1.05, pad: 16, padL: 30, padB: 24 });
      ctx.save(); ctx.translate(size + 26, 0);
      D.axes(ctx, v, P, { xTicks: [0, 500, 1000], yTicks: [.5, 1], xLabel: 'timestep' });
      D.curve(ctx, v, t => Math.sqrt(s.abar[Math.round(t)]), P.accent, 2.4, 200);
      D.curve(ctx, v, t => Math.sqrt(1 - s.abar[Math.round(t)]), P.series[0], 2.4, 200);
      D.line(ctx, v.sx(s.t), v.sy(0), v.sx(s.t), v.sy(1.05), P.text, 1.2, [3, 3]);
      D.dot(ctx, v.sx(s.t), v.sy(sa), 5, P.accent); D.dot(ctx, v.sx(s.t), v.sy(sn), 5, P.series[0]);
      D.text(ctx, 'signal', v.sx(40), v.sy(.93), { color: P.accent, size: 11, weight: 600 });
      D.text(ctx, 'noise', v.sx(40), v.sy(.12), { color: P.series[0], size: 11, weight: 600 });
      ctx.restore();
    };
    changed();
  },
});

defineLab('gnn', {
  title: 'Message passing on a graph',
  hint: 'Each round, every node averages its own value with its neighbours’. Information spreads one hop per round.',
  mount(L) {
    const P0 = [[.1, .5], [.25, .2], [.25, .8], [.42, .45], [.55, .15], [.58, .78], [.72, .42], [.86, .18], [.9, .66], [.7, .9]];
    const E = [[0, 1], [0, 2], [1, 3], [2, 3], [1, 4], [3, 6], [2, 5], [5, 6], [4, 6], [4, 7], [6, 8], [7, 8], [5, 9], [8, 9]];
    const nb = P0.map((_, i) => E.flatMap(([a, b]) => a === i ? [b] : b === i ? [a] : []));
    const s = { h: [], start: 'one', round: 0, msg: -1 };
    const c = L.canvas(w => Math.min(300, w * .5));
    L.seg('start with', [['one', 'One flagged node'], ['random', 'Random features']], s.start, v => { s.start = v; reset(); });
    const anim = L.loop(dt => { s.msg += dt * 1.6; L.redraw(); if (s.msg >= 1) { s.msg = -1; apply(); return false; } });
    L.button('Run one round', () => { if (!anim.running) { s.msg = 0; anim.start(); } }, 'primary');
    L.button('Run 10 rounds', () => { for (let i = 0; i < 10; i++) apply(true); changed(); });
    L.button('Reset', () => reset());
    function reset() {
      const r = rng(19);
      s.h = s.start === 'one' ? P0.map((_, i) => i === 0 ? 1 : 0) : P0.map(() => r());
      s.round = 0; changed();
    }
    function apply(silent) {
      s.h = s.h.map((v, i) => (v + nb[i].reduce((a, j) => a + s.h[j], 0)) / (nb[i].length + 1));
      s.round++;
      if (!silent) changed();
    }
    function changed() {
      L.redraw();
      const m = s.h.reduce((a, x) => a + x, 0) / s.h.length, sd = Math.sqrt(s.h.reduce((a, x) => a + (x - m) ** 2, 0) / s.h.length);
      const reached = s.h.filter(x => x > 1e-9).length;
      L.stats([['round', s.round, 'accent'], ['nodes reached', `${reached} of ${s.h.length}`], ['spread (std)', fmtN(sd, 3)]]);
      L.insight(s.round === 0 ? '<b>Round 0:</b> only the flagged node carries information.'
        : sd < .01 ? '<b>Oversmoothing.</b> After many rounds every node holds the same value, so nodes become indistinguishable. This is why most GNNs use only 2–4 layers.'
        : `<b>After ${s.round} round${s.round > 1 ? 's' : ''}, each node's value depends on nodes up to ${s.round} hop${s.round > 1 ? 's' : ''} away.</b> A GNN layer is one round, with learned weights instead of a plain average.`);
    }
    L.draw = P => {
      c.clear();
      const { ctx } = c, mx = Math.max(1e-9, ...s.h), pos = i => [14 + P0[i][0] * (c.w - 28), 14 + P0[i][1] * (c.h - 28)];
      E.forEach(([a, b]) => {
        const [x1, y1] = pos(a), [x2, y2] = pos(b);
        D.line(ctx, x1, y1, x2, y2, P.strong, 1.6);
        if (s.msg >= 0) {
          [[a, b, x1, y1, x2, y2], [b, a, x2, y2, x1, y1]].forEach(([from, , fx, fy, tx, ty]) => {
            if (s.h[from] > 1e-6) D.dot(ctx, lerp(fx, tx, s.msg), lerp(fy, ty, s.msg), 3 + 3 * s.h[from] / mx, P.alpha('accent', .85));
          });
        }
      });
      P0.forEach((_, i) => {
        const [x, y] = pos(i), t = s.h[i] / mx;
        D.dot(ctx, x, y, 17, P.mix('surface2', 'accent', t), t > .5 ? P.accent : P.strong, 2);
        D.text(ctx, s.h[i].toFixed(2), x, y, { color: t > .6 ? P.surface : P.text, size: 10, align: 'center', mono: true, weight: 600 });
      });
    };
    reset();
  },
});
