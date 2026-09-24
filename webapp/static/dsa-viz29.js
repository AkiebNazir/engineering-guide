/* ============================================================================
   Visualizations for 28_recursion_backtracking ("Recursion Mastery") — group 3
   (tree recursion A: 011, 012, 013, 014, 015, 017), group 4 (tree recursion B:
   018, 019, 020, 021, 025) and group 5 (hard backtracking: 022, 023, 024).
   Canvas engine (defineAlgo) for everything tree-shaped, reusing
   avTreeFromLevel/avLayoutBinary/avDrawBinary/avDrawBinaryIn/avRecorder/AV.node
   from dsa-viz.js and dsa-viz18.js — see that file's topic-10 specs for the
   original pattern. DOM engine (defineAlgoDom) for 020 (array/range, not tree-
   shaped) and 022-024 (string backtracking), reusing the call-stack tracer
   (mkTracer/stackFrameHTML) from dsa-viz28.js.
   ========================================================================= */
'use strict';

/* small helper: draw N trees side by side as thumbnails, for problems whose
   answer is a LIST of trees (012, 015). */
function avDrawForest(ctx, c, P, trees, { curIdx = -1 } = {}) {
  const n = trees.length;
  if (!n) { D.text(ctx, '(no completed trees yet)', c.w / 2, c.h / 2, { color: P.dim, size: 13, align: 'center' }); return; }
  const cols = Math.min(n, 5);
  const w = c.w / cols;
  trees.forEach((nodes, i) => {
    const region = { x: (i % cols) * w, w: w - 6, h: c.h };
    const lay = avLayoutBinary(nodes);
    avDrawBinaryIn(ctx, P, region, nodes, lay, id => ({ stroke: i === curIdx ? P.accent : P.strong }), { top: 24, gapY: 34, r: 11 });
    D.text(ctx, `#${i + 1}`, region.x + 8, c.h - 8, { color: P.dim, size: 10 });
  });
}

/* =============================================== 011 · Unique BST count === */
defineAlgo('28_recursion_backtracking', {
  title: 'Unique Binary Search Trees', short: 'Unique BSTs',
  idea: 'count(k) = number of distinct BST shapes on k nodes. Choosing each possible root r splits the rest into a left group of r-1 nodes and a right group of k-r nodes — count(k) = Σ count(r-1) × count(k-r). A memo turns repeated sub-counts into a single lookup.',
  complexity: 'Memoized: O(n²) time, O(n) space · naive: exponential (Catalan-number blowup)',
  input: '5', hint: 'n from 1 to 8',
  code: [
    'def count(k, memo={0:1, 1:1}):',
    '    if k in memo: return memo[k]',
    '    total = 0',
    '    for r in range(1, k + 1):',
    '        total += count(r-1) * count(k-r)',
    '    memo[k] = total',
    '    return total',
  ],
  parse(s) { const n = avNums(s, 1, 'one number')[0]; if (n < 1 || n > 8) throw new Error('Use n from 1 to 8'); return { n }; },
  run({ n }) {
    const { F, snap } = avRecorder();
    const nodes = [], memo = { 0: 1, 1: 1 };
    const S = (extra = {}) => ({ n, nodes: nodes.map(x => ({ ...x })), memo: { ...memo }, ...extra });
    const go = (k, parent, depth) => {
      const id = nodes.length;
      nodes.push({ k, parent, depth, val: null, hit: false });
      snap(1, `Call count(${k}).`, S({ cur: id, vars: { call: `count(${k})` } }));
      if (memo[k] !== undefined && k <= 1) { nodes[id].val = memo[k]; snap(1, `Base case: count(${k}) = ${memo[k]}.`, S({ cur: id })); return memo[k]; }
      if (memo[k] !== undefined) { nodes[id].val = memo[k]; nodes[id].hit = true; snap(2, `<b>Memo hit</b>: count(${k}) = ${memo[k]}.`, S({ cur: id })); return memo[k]; }
      let total = 0;
      for (let r = 1; r <= k; r++) {
        snap(4, `Root choice r=${r}: left has ${r - 1} node(s), right has ${k - r}.`, S({ cur: id, vars: { r } }));
        const left = go(r - 1, id, depth + 1), right = go(k - r, id, depth + 1);
        total += left * right;
      }
      memo[k] = total; nodes[id].val = total;
      snap(6, `count(${k}) = ${total}, stored in the memo.`, S({ cur: id, vars: { [`count(${k})`]: total } }));
      return total;
    };
    const ans = go(n, -1, 0);
    snap(7, `count(${n}) = ${ans} distinct BST shapes.`, S({ vars: { answer: ans } }));
    return F;
  },
  height: (w, last) => 40 + (Math.max(0, ...last.nodes.map(x => x.depth)) + 1) * 50 + 46,
  draw(ctx, c, f, P) {
    const perLevel = {};
    f.nodes.forEach(nd => { (perLevel[nd.depth] ??= []).push(nd); });
    const xy = new Map();
    Object.entries(perLevel).forEach(([d, list]) => list.forEach((nd, i) => xy.set(nd, [24 + (i + .5) * (c.w - 48) / list.length, 36 + +d * 50])));
    f.nodes.forEach(nd => { if (nd.parent < 0) return; const [x1, y1] = xy.get(f.nodes[nd.parent]), [x2, y2] = xy.get(nd); D.line(ctx, x1, y1 + 13, x2, y2 - 13, P.strong, 1.2); });
    const maxPerLevel = Math.max(4, ...Object.values(perLevel).map(l => l.length));
    const r = Math.max(9, Math.min(15, (c.w - 48) / maxPerLevel / 2.6));
    f.nodes.forEach((nd, id) => {
      const [x, y] = xy.get(nd);
      AV.node(ctx, P, x, y, r, nd.k, { fill: id === f.cur ? P.alpha('accent', .4) : nd.hit ? P.alpha('ok', .35) : nd.val !== null ? P.alpha('ok', .12) : null, stroke: id === f.cur ? P.accent : nd.hit ? P.ok : null, sub: nd.val !== null && r > 11 ? String(nd.val) : null });
    });
    const mk = Object.keys(f.memo).filter(k => +k > 1);
    D.text(ctx, mk.length ? `memo: ${mk.sort((a, b) => a - b).map(k => `${k}→${f.memo[k]}`).join('  ')}` : 'memo: (only base cases so far)', 20, c.h - 14, { color: mk.length ? P.ok : P.dim, size: 12, mono: true });
  },
});

/* ======================================== 012 · Unique Binary Search Trees II */
defineAlgo('28_recursion_backtracking', {
  title: 'Unique Binary Search Trees II', short: 'Unique BSTs II',
  idea: 'For each range [lo,hi], try every value r as the root; the left subtree is built recursively from [lo,r-1] and the right from [r+1,hi]. Every combination of a left shape and a right shape is a distinct tree — build() returns a LIST, and the caller takes a cross product.',
  complexity: 'Time/space proportional to the Catalan number of results',
  input: '3', hint: 'n from 1 to 3 (result count grows fast — Catalan(3) = 5 trees)',
  code: [
    'def build(lo, hi):',
    '    if lo > hi: return [None]',
    '    trees = []',
    '    for r in range(lo, hi + 1):',
    '        for left in build(lo, r - 1):',
    '            for right in build(r + 1, hi):',
    '                trees.append(TreeNode(r, left, right))',
    '    return trees',
  ],
  parse(s) { const n = avNums(s, 1, 'one number')[0]; if (n < 1 || n > 3) throw new Error('Use n from 1 to 3 (results grow fast)'); return { n }; },
  run({ n }) {
    const { F, snap } = avRecorder();
    const done = [];
    const S = (extra = {}) => ({ done: done.map(t => t.map(x => ({ ...x }))), ...extra });
    /* returns an array of node-lists, each node-list a flat [{val,left,right}] tree with root at index 0 */
    const build = (lo, hi) => {
      snap(1, `Call build(${lo}, ${hi}).`, S({ range: [lo, hi], vars: { lo, hi } }));
      if (lo > hi) { snap(2, 'Empty range — one shape: no subtree (null).', S({ range: [lo, hi] })); return [null]; }
      const trees = [];
      for (let r = lo; r <= hi; r++) {
        snap(4, `Try root=${r} for range [${lo},${hi}].`, S({ range: [lo, hi], vars: { root: r } }));
        const lefts = build(lo, r - 1), rights = build(r + 1, hi);
        for (const left of lefts) for (const right of rights) {
          const clone = (list, idx, out) => { if (idx === -1) return -1; const nid = out.length; out.push({ val: list[idx].val, left: -1, right: -1 }); out[nid].left = clone(list, list[idx].left, out); out[nid].right = clone(list, list[idx].right, out); return nid; };
          const flat = [{ val: r, left: -1, right: -1 }];
          flat[0].left = left ? clone(left, 0, flat) : -1;
          flat[0].right = right ? clone(right, 0, flat) : -1;
          trees.push(flat);
          if (lo === 1 && hi === n) { done.push(flat); snap(7, `Completed tree #${done.length}: root ${r}.`, S({ range: [lo, hi], curTree: flat })); }
        }
      }
      snap(8, `build(${lo}, ${hi}) returns ${trees.length} shape(s).`, S({ range: [lo, hi], vars: { count: trees.length } }));
      return trees;
    };
    build(1, n);
    snap(8, `Finished: ${done.length} distinct trees for n=${n}.`, S({ range: [1, n] }));
    return F;
  },
  height: () => 220,
  draw(ctx, c, f, P) {
    avDrawForest(ctx, c, P, f.done, { curIdx: f.curTree ? f.done.length - 1 : -1 });
    D.text(ctx, f.range ? `building range [${f.range[0]}, ${f.range[1]}]` : '', 20, 16, { color: P.accent, size: 12.5, weight: 700 });
  },
});

/* ================================================ 013 · Sum Root to Leaf == */
defineAlgo('28_recursion_backtracking', {
  title: 'Sum Root to Leaf Numbers', short: 'Sum Root to Leaf',
  idea: 'Carry a running "number so far" down as an argument: at each node, number_so_far = number_so_far*10 + node.val. A leaf reports that number; an internal node sums whatever its children report.',
  complexity: 'Time O(n) · Space O(h) recursion depth',
  input: '4, 9, 0, 5, 1', hint: 'level order, digits 0-9, null for missing children',
  code: [
    'def dfs(node, number_so_far):',
    '    number_so_far = number_so_far*10 + node.val',
    '    if not node.left and not node.right:',
    '        return number_so_far',
    '    total = 0',
    '    if node.left: total += dfs(node.left, number_so_far)',
    '    if node.right: total += dfs(node.right, number_so_far)',
    '    return total',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const soFar = {};
    const S = (cur, extra = {}) => ({ nodes, cur, soFar: { ...soFar }, ...extra });
    const go = (id, prefix) => {
      const n = prefix * 10 + nodes[id].val;
      soFar[id] = n;
      snap(1, `At ${nodes[id].val}: number_so_far = ${prefix}×10 + ${nodes[id].val} = ${n}.`, S(id, { vars: { node: nodes[id].val, number_so_far: n } }));
      const isLeaf = nodes[id].left === -1 && nodes[id].right === -1;
      if (isLeaf) { snap(3, `Leaf — report ${n} up to the caller.`, S(id, { vars: { leaf_value: n } })); return n; }
      let total = 0;
      if (nodes[id].left !== -1) total += go(nodes[id].left, n);
      if (nodes[id].right !== -1) total += go(nodes[id].right, n);
      snap(7, `${nodes[id].val}: sum of children's reports = ${total}.`, S(id, { vars: { total } }));
      return total;
    };
    const ans = go(0, 0);
    snap(7, `Total of all root-to-leaf numbers = ${ans}.`, S(null, { vars: { answer: ans } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 40; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({ fill: id === f.cur ? P.alpha('accent', .35) : f.soFar[id] != null ? P.alpha('ok', .16) : null, stroke: id === f.cur ? P.accent : null, sub: f.soFar[id] != null ? f.soFar[id] : null }));
  },
});

/* ==================================================== 014 · House Robber III */
defineAlgo('28_recursion_backtracking', {
  title: 'House Robber III', short: 'House Robber III',
  idea: 'Each node returns a PAIR: (best if this node is robbed, best if it is not). Robbed = this node\'s value + both children\'s not-robbed totals (can\'t rob a direct neighbor). Not-robbed = the better of each child\'s two options.',
  complexity: 'Time O(n) · Space O(h) recursion depth',
  input: '3, 4, 5, 1, 3, null, 1', hint: 'level order house values, null for missing children',
  code: [
    'def dfs(node):',
    '    if not node: return 0, 0',
    '    lr, lnr = dfs(node.left)',
    '    rr, rnr = dfs(node.right)',
    '    robbed = node.val + lnr + rnr',
    '    not_robbed = max(lr, lnr) + max(rr, rnr)',
    '    return robbed, not_robbed',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const pair = {};
    const S = (cur, extra = {}) => ({ nodes, cur, pair: { ...pair }, ...extra });
    const go = id => {
      if (id === -1) return [0, 0];
      snap(1, `Call dfs(${nodes[id].val}).`, S(id));
      const [lr, lnr] = go(nodes[id].left);
      const [rr, rnr] = go(nodes[id].right);
      const robbed = nodes[id].val + lnr + rnr;
      const notRobbed = Math.max(lr, lnr) + Math.max(rr, rnr);
      pair[id] = [robbed, notRobbed];
      snap(6, `${nodes[id].val}: robbed = ${nodes[id].val}+${lnr}+${rnr} = ${robbed}; not-robbed = max(${lr},${lnr})+max(${rr},${rnr}) = ${notRobbed}.`, S(id, { vars: { robbed, not_robbed: notRobbed } }));
      return [robbed, notRobbed];
    };
    const [robbedRoot, notRobbedRoot] = go(0);
    const ans = Math.max(robbedRoot, notRobbedRoot);
    snap(6, `Root's best = max(${robbedRoot}, ${notRobbedRoot}) = ${ans}.`, S(null, { vars: { answer: ans } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 40; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({ fill: id === f.cur ? P.alpha('accent', .35) : f.pair[id] ? P.alpha('ok', .16) : null, stroke: id === f.cur ? P.accent : null, sub: f.pair[id] ? `R${f.pair[id][0]}/N${f.pair[id][1]}` : null }));
  },
});

/* ======================================== 015 · All Possible Full Binary Trees */
defineAlgo('28_recursion_backtracking', {
  title: 'All Possible Full Binary Trees', short: 'All Full Binary Trees',
  idea: 'A full binary tree has n nodes (n odd): the root uses 1, and the remaining n-1 split into a left size and a right size, both odd, in every possible way. Cross-multiply every left shape with every right shape.',
  complexity: 'Time/space proportional to the number of results (grows fast)',
  input: '7', hint: 'an odd number, kept small (5 or 7) so the gallery stays readable',
  code: [
    'def allPossibleFBT(n):',
    '    if n % 2 == 0: return []',
    '    if n == 1: return [TreeNode(0)]',
    '    trees = []',
    '    for left_size in range(1, n - 1, 2):',
    '        right_size = n - 1 - left_size',
    '        for left in allPossibleFBT(left_size):',
    '            for right in allPossibleFBT(right_size):',
    '                trees.append(TreeNode(0, left, right))',
    '    return trees',
  ],
  parse(s) { const n = avNums(s, 1, 'one number')[0]; if (n % 2 === 0 || n < 1 || n > 7) throw new Error('Use an odd n from 1 to 7'); return { n }; },
  run({ n }) {
    const { F, snap } = avRecorder();
    const done = [];
    const S = (extra = {}) => ({ done: done.map(t => t.map(x => ({ ...x }))), ...extra });
    const clone = (list, idx, out) => { if (idx === -1) return -1; const nid = out.length; out.push({ val: 0, left: -1, right: -1 }); out[nid].left = clone(list, list[idx].left, out); out[nid].right = clone(list, list[idx].right, out); return nid; };
    const go = k => {
      snap(1, `Call allPossibleFBT(${k}).`, S({ vars: { n: k } }));
      if (k % 2 === 0) { snap(2, `${k} is even — a full binary tree needs an odd node count. Return [].`, S()); return []; }
      if (k === 1) { const t = [{ val: 0, left: -1, right: -1 }]; snap(3, 'Base case: a single leaf.', S()); return [t]; }
      const trees = [];
      for (let leftSize = 1; leftSize < k - 1; leftSize += 2) {
        const rightSize = k - 1 - leftSize;
        snap(6, `Split ${k - 1} remaining nodes: left gets ${leftSize}, right gets ${rightSize}.`, S({ vars: { left_size: leftSize, right_size: rightSize } }));
        const lefts = go(leftSize), rights = go(rightSize);
        for (const left of lefts) for (const right of rights) {
          const flat = [{ val: 0, left: -1, right: -1 }];
          flat[0].left = clone(left, 0, flat);
          flat[0].right = clone(right, 0, flat);
          trees.push(flat);
          if (k === n) { done.push(flat); snap(9, `Completed tree #${done.length} (n=${n}).`, S({ curTree: flat })); }
        }
      }
      return trees;
    };
    go(n);
    snap(9, `Finished: ${done.length} distinct full binary trees for n=${n}.`, S());
    return F;
  },
  height: () => 220,
  draw(ctx, c, f, P) { avDrawForest(ctx, c, P, f.done, { curIdx: f.curTree ? f.done.length - 1 : -1 }); },
});

/* ===================================================== 017 · Split BST ==== */
defineAlgo('28_recursion_backtracking', {
  title: 'Split BST', short: 'Split BST',
  idea: 'One-sided descent using the BST ordering: if node.val <= target, everything at and left of node belongs to "smaller" — recurse right and re-attach the returned "greater" piece there; mirror image if node.val > target.',
  complexity: 'Time O(h) · Space O(h) recursion depth',
  input: '4, 2, 6, 1, 3, 5, 7; 2', hint: 'BST in level order ; target value',
  code: [
    'def split(node, target):',
    '    if not node: return None, None',
    '    if node.val <= target:',
    '        smaller, greater = split(node.right, target)',
    '        node.right = smaller',
    '        return node, greater',
    '    smaller, greater = split(node.left, target)',
    '    node.left = greater',
    '    return smaller, node',
  ],
  parse(s) {
    const [treeStr, targetStr] = String(s || '').split(';');
    const nodes = avTreeFromLevel(treeStr);
    const target = parseInt((targetStr || '').trim(), 10);
    if (!Number.isFinite(target)) throw new Error('Add a target value after the ";"');
    return { nodes, target };
  },
  run({ nodes, target }) {
    const { F, snap } = avRecorder();
    const S = (cur, extra = {}) => ({ nodes, cur, phase: 'walk', target, ...extra });
    const clone = (idx, out) => { if (idx === -1) return -1; const nid = out.length; out.push({ val: nodes[idx].val, left: -1, right: -1 }); out[nid].left = clone(nodes[idx].left, out); out[nid].right = clone(nodes[idx].right, out); return nid; };
    const go = id => {
      if (id === -1) return [[], []];
      snap(1, `At node ${nodes[id].val}: compare to target ${target}.`, S(id));
      if (nodes[id].val <= target) {
        snap(3, `${nodes[id].val} <= ${target} — this node and its left subtree are all "smaller". Recurse right.`, S(id));
        const [smallerSub, greaterSub] = go(nodes[id].right);
        const smaller = [{ val: nodes[id].val, left: -1, right: -1 }];
        smaller[0].left = clone(nodes[id].left, smaller);
        smaller[0].right = smallerSub.length ? (() => { const off = smaller.length; smallerSub.forEach(n => smaller.push({ ...n, left: n.left === -1 ? -1 : n.left + off, right: n.right === -1 ? -1 : n.right + off })); return off; })() : -1;
        return [smaller, greaterSub];
      } else {
        snap(7, `${nodes[id].val} > ${target} — this node and its right subtree are all "greater". Recurse left.`, S(id));
        const [smallerSub, greaterSub] = go(nodes[id].left);
        const greater = [{ val: nodes[id].val, left: -1, right: -1 }];
        greater[0].left = greaterSub.length ? (() => { const off = greater.length; greaterSub.forEach(n => greater.push({ ...n, left: n.left === -1 ? -1 : n.left + off, right: n.right === -1 ? -1 : n.right + off })); return off; })() : -1;
        greater[0].right = clone(nodes[id].right, greater);
        return [smallerSub, greater];
      }
    };
    const [smaller, greater] = go(0);
    snap(9, `Split complete: "smaller" holds every value <= ${target}, "greater" holds the rest.`, { nodes, cur: null, phase: 'result', target, smaller, greater });
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return Math.max(220, 60 + lay.depth * 58 + 40); },
  draw(ctx, c, f, P) {
    if (f.phase === 'walk') {
      const lay = avLayoutBinary(f.nodes);
      avDrawBinary(ctx, P, c, f.nodes, lay, id => ({ fill: id === f.cur ? P.alpha('accent', .35) : null, stroke: id === f.cur ? P.accent : null }));
      D.text(ctx, `target = ${f.target}`, 20, 16, { color: P.accent, size: 12.5, weight: 700 });
    } else {
      const left = { x: 0, w: c.w / 2 - 6, h: c.h }, right = { x: c.w / 2 + 6, w: c.w / 2 - 6, h: c.h };
      if (f.smaller.length) avDrawBinaryIn(ctx, P, left, f.smaller, avLayoutBinary(f.smaller), () => ({ stroke: P.ok }), { top: 30 });
      else D.text(ctx, '(empty)', left.w / 2, c.h / 2, { color: P.dim, size: 12, align: 'center' });
      if (f.greater.length) avDrawBinaryIn(ctx, P, right, f.greater, avLayoutBinary(f.greater), () => ({ stroke: P.accent }), { top: 30 });
      else D.text(ctx, '(empty)', right.x + right.w / 2, c.h / 2, { color: P.dim, size: 12, align: 'center' });
      D.text(ctx, `smaller (<= ${f.target})`, left.w / 2, 14, { color: P.ok, size: 12, align: 'center', weight: 700 });
      D.text(ctx, `greater (> ${f.target})`, right.x + right.w / 2, 14, { color: P.accent, size: 12, align: 'center', weight: 700 });
    }
  },
});

/* ============================================ 018 · Distribute Coins ====== */
defineAlgo('28_recursion_backtracking', {
  title: 'Distribute Coins in Binary Tree', short: 'Distribute Coins',
  idea: 'Postorder: each node reports its "excess" = coins_here + excess_from_children - 1 (every node needs exactly 1 coin). A move is one coin crossing one edge, so |excess| gets added to the move counter at every edge, regardless of direction.',
  complexity: 'Time O(n) · Space O(h) recursion depth',
  input: '3, 0, 0', hint: 'level order coin counts per node (total coins must equal node count)',
  code: [
    'def dfs(node):',
    '    if not node: return 0',
    '    left_excess = dfs(node.left)',
    '    right_excess = dfs(node.right)',
    '    moves += abs(left_excess) + abs(right_excess)',
    '    return node.val + left_excess + right_excess - 1',
  ],
  parse(s) { const nodes = avTreeFromLevel(s); return { nodes }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    let moves = 0;
    const excess = {};
    const S = (cur, extra = {}) => ({ nodes, cur, excess: { ...excess }, moves, ...extra });
    const go = id => {
      if (id === -1) return 0;
      snap(1, `Call dfs at node with ${nodes[id].val} coin(s).`, S(id));
      const le = go(nodes[id].left), re = go(nodes[id].right);
      moves += Math.abs(le) + Math.abs(re);
      const ex = nodes[id].val + le + re - 1;
      excess[id] = ex;
      snap(5, `moves += |${le}| + |${re}| → ${moves}. This node's excess = ${nodes[id].val}+${le}+${re}-1 = ${ex}.`, S(id, { vars: { moves, excess: ex } }));
      return ex;
    };
    go(0);
    snap(5, `Done. Total moves = ${moves}.`, S(null, { vars: { answer: moves } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 40; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({ fill: id === f.cur ? P.alpha('accent', .35) : f.excess[id] !== undefined ? (f.excess[id] === 0 ? P.alpha('ok', .16) : P.alpha('err', .16)) : null, stroke: id === f.cur ? P.accent : null, sub: f.excess[id] !== undefined ? `ex=${f.excess[id]}` : null }));
    D.text(ctx, `moves so far: ${f.moves}`, 20, 16, { color: P.accent, size: 12.5, weight: 700 });
  },
});

/* ============================== 019 · LCA of Deepest Leaves ================ */
defineAlgo('28_recursion_backtracking', {
  title: 'Lowest Common Ancestor of Deepest Leaves', short: 'LCA of Deepest Leaves',
  idea: 'One postorder pass returns (depth, candidate LCA) per node: if both subtrees are equally deep, this node IS the answer for its subtree; otherwise the deeper side\'s candidate wins.',
  complexity: 'Time O(n) · Space O(h) recursion depth',
  input: '3, 5, 1, 6, 2, 0, 8, null, null, 7, 4', hint: 'level order, null for missing children',
  code: [
    'def dfs(node):',
    '    if not node: return 0, None',
    '    ld, la = dfs(node.left)',
    '    rd, ra = dfs(node.right)',
    '    if ld == rd: return ld + 1, node',
    '    return (ld + 1, la) if ld > rd else (rd + 1, ra)',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const depth = {};
    const S = (cur, extra = {}) => ({ nodes, cur, depth: { ...depth }, ...extra });
    const go = id => {
      if (id === -1) return [0, -1];
      snap(1, `Call dfs(${nodes[id].val}).`, S(id));
      const [ld, la] = go(nodes[id].left);
      const [rd, ra] = go(nodes[id].right);
      let d, lca;
      if (ld === rd) { d = ld + 1; lca = id; snap(4, `${nodes[id].val}: both sides depth ${ld} — this node is the LCA for its subtree.`, S(id, { lca: id })); }
      else if (ld > rd) { d = ld + 1; lca = la; snap(5, `${nodes[id].val}: left is deeper (${ld} > ${rd}) — carry up the left candidate.`, S(id, { lca: la })); }
      else { d = rd + 1; lca = ra; snap(5, `${nodes[id].val}: right is deeper (${rd} > ${ld}) — carry up the right candidate.`, S(id, { lca: ra })); }
      depth[id] = d;
      return [d, lca];
    };
    const [, finalLca] = go(0);
    snap(5, `Done. Lowest common ancestor of the deepest leaves = ${nodes[finalLca].val}.`, S(null, { lca: finalLca, vars: { answer: nodes[finalLca].val } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 40; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({ fill: id === f.lca ? P.alpha('ok', .35) : id === f.cur ? P.alpha('accent', .35) : f.depth[id] != null ? P.alpha('faint', .12) : null, stroke: id === f.lca ? P.ok : id === f.cur ? P.accent : null, ring: id === f.lca ? P.ok : null, sub: f.depth[id] != null ? `d=${f.depth[id]}` : null }));
  },
});

/* ================================ 020 · Minimum Cost Tree From Leaf Values = */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Minimum Cost Tree From Leaf Values', short: 'Min Cost Tree From Leaves',
  idea: 'For a range [lo,hi] of leaves, try every split point: cost = best(left half) + best(right half) + max(left half) x max(right half) — the two maxima become the parent node created by joining those two subtrees. Memoize on (lo,hi).',
  complexity: 'Time O(n³) memoized · Space O(n²)',
  input: '6,2,4', hint: 'leaf values, no two adjacent equal (kept small: max 6 values)',
  code: [
    'def min_cost(lo, hi):',
    '    if lo == hi: return 0',
    '    best = inf',
    '    for split in range(lo, hi):',
    '        best = min(best, min_cost(lo, split)',
    '            + min_cost(split+1, hi)',
    '            + max(arr[lo:split+1]) * max(arr[split+1:hi+1]))',
    '    return best',
  ],
  parse(s) {
    const arr = String(s || '').split(',').map(x => parseInt(x.trim(), 10));
    if (arr.length < 2 || arr.some(v => !Number.isFinite(v))) throw new Error('Enter at least 2 comma-separated leaf values');
    if (arr.length > 6) throw new Error('Use at most 6 leaf values for visualization');
    return { arr };
  },
  buildStates({ arr }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const memo = {};
    const maxIn = (lo, hi) => Math.max(...arr.slice(lo, hi + 1));
    const go = (lo, hi) => {
      T.call('min_cost', `lo=${lo}, hi=${hi}`);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), arr, lo, hi, splitAt: -1, line: 1, color: 'blue', explTitle: `Call min_cost(${lo}, ${hi})`, explText: `Consider leaves [${arr.slice(lo, hi + 1).join(', ')}].` }, ctx);
      let result;
      if (lo === hi) {
        result = 0;
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), arr, lo, hi, splitAt: -1, line: 2, color: 'emerald', explTitle: 'Single leaf', explText: 'Only one leaf in this range — no internal node needed, cost 0.' }, ctx);
      } else if (memo[`${lo},${hi}`] !== undefined) {
        result = memo[`${lo},${hi}`];
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), arr, lo, hi, splitAt: -1, line: 3, color: 'emerald', explTitle: 'Memo hit', explText: `min_cost(${lo},${hi}) already computed: ${result}.` }, ctx);
      } else {
        let best = Infinity;
        for (let split = lo; split < hi; split++) {
          domPushState(seq, { stack: T.stack.map(f => ({ ...f })), arr, lo, hi, splitAt: split, line: 4, color: 'amber', explTitle: `Try split at ${split}`, explText: `Left leaves [${arr.slice(lo, split + 1).join(',')}], right leaves [${arr.slice(split + 1, hi + 1).join(',')}].` }, ctx);
          const leftCost = go(lo, split), rightCost = go(split + 1, hi);
          const joinCost = maxIn(lo, split) * maxIn(split + 1, hi);
          const total = leftCost + rightCost + joinCost;
          if (total < best) best = total;
          domPushState(seq, { stack: T.stack.map(f => ({ ...f })), arr, lo, hi, splitAt: split, line: 5, color: 'amber', explTitle: 'Join cost', explText: `max(${arr.slice(lo, split + 1)}) × max(${arr.slice(split + 1, hi + 1)}) = ${joinCost}. Total for this split = ${leftCost}+${rightCost}+${joinCost} = ${total}. Best so far: ${best}.` }, ctx);
        }
        result = best; memo[`${lo},${hi}`] = best;
      }
      T.ret(result);
      T.pop();
      return result;
    };
    const ans = go(0, arr.length - 1);
    domPushState(seq, { stack: [], arr, lo: 0, hi: arr.length - 1, splitAt: -1, line: 6, color: 'emerald', explTitle: 'Done', explText: `Minimum total cost = ${ans}.` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const html = s.arr.map((v, i) => {
      const inRange = i >= s.lo && i <= s.hi;
      const leftHalf = s.splitAt !== -1 && i <= s.splitAt && i >= s.lo;
      const rightHalf = s.splitAt !== -1 && i > s.splitAt && i <= s.hi;
      const cls = leftHalf ? 'active-k' : rightHalf ? 'active-1' : inRange ? 'merged' : '';
      return `<div class="array-node ${cls}">${v}<div class="node-index">${i}</div></div>`;
    }).join('');
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Leaf values</div>
                  <div class="array-track">${html}</div>
              </div>
          ${stackPanelHTML(s, 'Call Stack (memoized on lo,hi)')}
      </div>`;
  }
});

/* ==================== 021 · Recover a Tree From Preorder Traversal ========= */
defineAlgo('28_recursion_backtracking', {
  title: 'Recover a Tree From Preorder Traversal', short: 'Recover Tree From Preorder',
  idea: 'Stack-based reconstruction: each token is (depth, value). Truncate the stack down to `depth` entries — whatever remains on top is the parent (fills its left child first, then right) — then push the new node.',
  complexity: 'Time O(n) · Space O(depth)',
  input: '1-2--3--4-5--6--7', hint: 'dashes = depth, then the value (LeetCode format)',
  code: [
    'stack = []',
    'for depth, value in tokens:',
    '    node = TreeNode(value)',
    '    del stack[depth:]',
    '    if stack:',
    '        parent = stack[-1]',
    '        if parent.left is None: parent.left = node',
    '        else: parent.right = node',
    '    else:',
    '        root = node',
    '    stack.append(node)',
  ],
  parse(s) {
    const src = String(s || '').trim();
    if (!src) throw new Error('Enter a preorder string, e.g. 1-2--3--4-5--6--7');
    const tokens = [];
    let i = 0;
    while (i < src.length) {
      let depth = 0; while (src[i] === '-') { depth++; i++; }
      let k = i; while (k < src.length && /\d/.test(src[k])) k++;
      if (k === i) throw new Error('Malformed preorder string');
      tokens.push([depth, parseInt(src.slice(i, k), 10)]);
      i = k;
    }
    if (tokens.length > 10) throw new Error('Use at most 10 nodes for visualization');
    return { tokens };
  },
  run({ tokens }) {
    const { F, snap } = avRecorder();
    const nodes = []; // {val, left, right}
    const stack = []; // indices into nodes
    let root = -1;
    const S = (extra = {}) => ({ nodes: nodes.map(n => ({ ...n })), stack: [...stack], ...extra });
    snap(0, 'Start with an empty stack.', S());
    for (const [depth, value] of tokens) {
      const id = nodes.length; nodes.push({ val: value, left: -1, right: -1 });
      snap(2, `New node ${value} at depth ${depth}.`, S({ cur: id, vars: { depth, value } }));
      stack.length = depth;
      snap(3, `Truncate the stack to ${depth} entr${depth === 1 ? 'y' : 'ies'} — that discards any ancestor deeper than this node's parent.`, S({ cur: id }));
      if (stack.length) {
        const parent = stack[stack.length - 1];
        if (nodes[parent].left === -1) { nodes[parent].left = id; snap(6, `Parent ${nodes[parent].val} has no left child yet — attach ${value} as its left child.`, S({ cur: id })); }
        else { nodes[parent].right = id; snap(7, `Parent ${nodes[parent].val} already has a left child — attach ${value} as its right child.`, S({ cur: id })); }
      } else { root = id; snap(9, `Stack is empty — ${value} is the root.`, S({ cur: id })); }
      stack.push(id);
    }
    snap(10, 'All tokens consumed — tree fully rebuilt.', S({ cur: null }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return Math.max(200, 60 + lay.depth * 58 + 60); },
  draw(ctx, c, f, P) {
    if (!f.nodes.length) { D.text(ctx, '(no nodes yet)', c.w / 2, c.h / 2, { color: P.dim, size: 13, align: 'center' }); return; }
    const lay = avLayoutBinary(f.nodes, 0);
    avDrawBinary(ctx, P, { w: c.w, h: c.h - 30 }, f.nodes, lay, id => ({ fill: id === f.cur ? P.alpha('accent', .35) : null, stroke: id === f.cur ? P.accent : null }));
    D.text(ctx, `stack (open ancestors): [${f.stack.map(id => f.nodes[id].val).join(', ')}]`, 20, c.h - 12, { color: P.accent, size: 12, mono: true });
  },
});

/* =============================================== 025 · Binary Tree Cameras = */
defineAlgo('28_recursion_backtracking', {
  title: 'Binary Tree Cameras', short: 'Binary Tree Cameras',
  idea: 'Postorder, 3 states per node: NOT_COVERED, COVERED (no camera here), HAS_CAMERA. If either child is not covered, place a camera HERE (greedy — cameras as low as possible cover the most). The root gets one final camera if it ends up not covered.',
  complexity: 'Time O(n) · Space O(h) recursion depth',
  input: '0, 0, null, 0, 0', hint: 'level order (values are ignored — only shape matters), null for missing children',
  code: [
    'def dfs(node):',
    '    if not node: return COVERED',
    '    l, r = dfs(node.left), dfs(node.right)',
    '    if l == NOT_COVERED or r == NOT_COVERED:',
    '        cameras += 1; return HAS_CAMERA',
    '    if l == HAS_CAMERA or r == HAS_CAMERA:',
    '        return COVERED',
    '    return NOT_COVERED',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const NOT_COVERED = 0, COVERED = 1, HAS_CAMERA = 2;
    const LABEL = { [NOT_COVERED]: 'not covered', [COVERED]: 'covered', [HAS_CAMERA]: 'camera' };
    let cameras = 0;
    const state = {};
    const S = (cur, extra = {}) => ({ nodes, cur, state: { ...state }, cameras, ...extra });
    const go = id => {
      if (id === -1) return COVERED;
      snap(1, `Call dfs at this node.`, S(id));
      const l = go(nodes[id].left), r = go(nodes[id].right);
      let st;
      if (l === NOT_COVERED || r === NOT_COVERED) { cameras++; st = HAS_CAMERA; snap(4, `A child is not covered — place a camera here. Cameras so far: ${cameras}.`, S(id, { vars: { cameras } })); }
      else if (l === HAS_CAMERA || r === HAS_CAMERA) { st = COVERED; snap(6, 'A child already has a camera — this node is covered, no camera needed here.', S(id)); }
      else { st = NOT_COVERED; snap(7, 'Both children are covered (no camera) — this node itself is not covered yet.', S(id)); }
      state[id] = st;
      return st;
    };
    const rootState = go(0);
    if (rootState === NOT_COVERED) cameras++;
    snap(7, `Root ${rootState === NOT_COVERED ? "isn't covered — place one final camera. " : ''}Total cameras = ${cameras}.`, S(null, { cameras, vars: { answer: cameras } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 40; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    const LABEL = { 0: 'N', 1: 'C', 2: '📷' };
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({ fill: id === f.cur ? P.alpha('accent', .35) : f.state[id] === 2 ? P.alpha('ok', .3) : f.state[id] !== undefined ? P.alpha('faint', .14) : null, stroke: id === f.cur ? P.accent : f.state[id] === 2 ? P.ok : null, sub: f.state[id] !== undefined ? LABEL[f.state[id]] : null }));
    D.text(ctx, `cameras so far: ${f.cameras}`, 20, 16, { color: P.accent, size: 12.5, weight: 700 });
  },
});

/* =============================================== 022 · Special Binary String */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Special Binary String', short: 'Special Binary String',
  idea: 'A special string decomposes into top-level balanced pieces (each starts with 1, ends with 0, and never touches zero balance in between). Recursively maximize the INSIDE of each piece, then sort all top-level pieces descending — swapping two special strings can only ever be a full-piece swap.',
  complexity: 'Time O(n log n) · Space O(n) recursion depth',
  input: '11011000', hint: 'a special binary string (balanced 1s/0s), kept short',
  code: [
    'def makeLargestSpecial(s):',
    '    if s == "": return ""',
    '    pieces, balance, start = [], 0, 0',
    '    for i, ch in enumerate(s):',
    '        balance += 1 if ch == "1" else -1',
    '        if balance == 0:',
    '            inside = makeLargestSpecial(s[start+1:i])',
    '            pieces.append("1" + inside + "0")',
    '            start = i + 1',
    '    pieces.sort(reverse=True)',
    '    return "".join(pieces)',
  ],
  parse(s) {
    const str = String(s || '').trim();
    if (!/^[01]*$/.test(str)) throw new Error('Enter only 0s and 1s');
    if (str.length > 16) throw new Error('Use at most 16 characters for visualization');
    let bal = 0; for (const ch of str) { bal += ch === '1' ? 1 : -1; if (bal < 0) throw new Error('Not a valid special string (balance went negative)'); }
    if (bal !== 0) throw new Error('Not a valid special string (unbalanced 1s/0s)');
    return { str };
  },
  buildStates({ str }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const go = s => {
      T.call('makeLargestSpecial', `"${s}"`);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), s, pieces: [], line: 1, color: 'blue', explTitle: `Call makeLargestSpecial("${s}")`, explText: s ? `Decompose "${s}" into balanced top-level pieces.` : 'Empty string.' }, ctx);
      if (!s) { domPushState(seq, { stack: T.stack.map(f => ({ ...f })), s, pieces: [], line: 2, color: 'emerald', explTitle: 'Base case', explText: 'Empty string — return "".' }, ctx); T.ret('""'); T.pop(); return ''; }
      const pieces = [];
      let balance = 0, start = 0;
      for (let i = 0; i < s.length; i++) {
        balance += s[i] === '1' ? 1 : -1;
        if (balance === 0) {
          const inner = s.slice(start + 1, i);
          domPushState(seq, { stack: T.stack.map(f => ({ ...f })), s, pieces: [...pieces], splitAt: [start, i], line: 5, color: 'amber', explTitle: 'Found a balanced piece', explText: `"${s.slice(start, i + 1)}" is balanced — recurse on its inside "${inner}".` }, ctx);
          const insideMax = go(inner);
          const piece = '1' + insideMax + '0';
          pieces.push(piece);
          domPushState(seq, { stack: T.stack.map(f => ({ ...f })), s, pieces: [...pieces], line: 6, color: 'amber', explTitle: 'Piece maximized', explText: `Piece becomes "1" + "${insideMax}" + "0" = "${piece}".` }, ctx);
          start = i + 1;
        }
      }
      pieces.sort().reverse();
      const result = pieces.join('');
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), s, pieces: [...pieces], line: 8, color: 'emerald', explTitle: 'Sort pieces descending', explText: `Pieces sorted: [${pieces.join(', ')}] → "${result}".` }, ctx);
      T.ret(`"${result}"`);
      T.pop();
      return result;
    };
    const final = go(str);
    domPushState(seq, { stack: [], s: str, pieces: [final], line: 8, color: 'emerald', explTitle: 'Done', explText: `Largest special string: "${final}".` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const charHTML = [...s.s].map((ch, i) => {
      const inSplit = s.splitAt && i >= s.splitAt[0] && i <= s.splitAt[1];
      return `<div class="array-node ${inSplit ? 'active-k' : ''}" style="min-width:34px;">${ch}<div class="node-index">${i}</div></div>`;
    }).join('');
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Current string</div>
                  <div class="array-track">${charHTML}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Top-level pieces found</div>
                  <div style="display:flex; flex-wrap:wrap; gap:8px; padding:6px 0;">${s.pieces.length ? s.pieces.map(p => `<span class="array-node merged" style="min-width:auto; padding:6px 12px; font-family:var(--mono);">${p}</span>`).join('') : '<span style="color:var(--text-dim);">(none yet)</span>'}</div>
              </div>
          ${stackPanelHTML(s)}
      </div>`;
  }
});

/* ===================================================== 023 · Scramble String */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Scramble String', short: 'Scramble String',
  idea: 'Try every split point i of s1: either both halves match straight across (s1[:i]~s2[:i] and s1[i:]~s2[i:]) or s1 was flipped at this level (s1[:i]~s2[-i:] and s1[i:]~s2[:-i]). A quick sorted-character check prunes impossible pairs before recursing. Memoized on (a,b).',
  complexity: 'Time O(n⁴) memoized · Space O(n⁴)',
  input: 'great;rgeat', hint: 's1;s2 — equal length, kept short',
  code: [
    'def scramble(a, b):',
    '    if a == b: return True',
    '    if sorted(a) != sorted(b): return False',
    '    n = len(a)',
    '    for i in range(1, n):',
    '        if scramble(a[:i],b[:i]) and scramble(a[i:],b[i:]): return True',
    '        if scramble(a[:i],b[-i:]) and scramble(a[i:],b[:-i]): return True',
    '    return False',
  ],
  parse(s) {
    const [a, b] = String(s || '').split(';').map(x => (x || '').trim());
    if (!a || !b || a.length !== b.length) throw new Error('Enter two equal-length strings, e.g. great;rgeat');
    if (a.length > 6) throw new Error('Use strings of length <= 6 for visualization');
    return { a, b };
  },
  buildStates({ a: s1, b: s2 }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const memo = {};
    const sorted = s => [...s].sort().join('');
    const go = (a, b) => {
      const key = a + '|' + b;
      T.call('scramble', `"${a}", "${b}"`);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), a, b, line: 1, color: 'blue', explTitle: `Call scramble("${a}", "${b}")`, explText: `Compare "${a}" and "${b}".` }, ctx);
      let result;
      if (a === b) { result = true; domPushState(seq, { stack: T.stack.map(f => ({ ...f })), a, b, line: 2, color: 'emerald', explTitle: 'Equal', explText: 'The strings are already identical — return True.' }, ctx); }
      else if (sorted(a) !== sorted(b)) { result = false; domPushState(seq, { stack: T.stack.map(f => ({ ...f })), a, b, line: 3, color: 'rose', explTitle: 'Different letters', explText: `Different multiset of characters (${sorted(a)} vs ${sorted(b)}) — no scramble can fix that. Return False.` }, ctx); }
      else if (memo[key] !== undefined) { result = memo[key]; domPushState(seq, { stack: T.stack.map(f => ({ ...f })), a, b, line: 1, color: 'emerald', explTitle: 'Memo hit', explText: `scramble("${a}","${b}") already known: ${result}.` }, ctx); }
      else {
        result = false;
        for (let i = 1; i < a.length && !result; i++) {
          domPushState(seq, { stack: T.stack.map(f => ({ ...f })), a, b, splitI: i, line: 5, color: 'amber', explTitle: `Try split i=${i} (no flip)`, explText: `Check "${a.slice(0, i)}"~"${b.slice(0, i)}" and "${a.slice(i)}"~"${b.slice(i)}".` }, ctx);
          if (go(a.slice(0, i), b.slice(0, i)) && go(a.slice(i), b.slice(i))) { result = true; break; }
          domPushState(seq, { stack: T.stack.map(f => ({ ...f })), a, b, splitI: i, line: 6, color: 'amber', explTitle: `Try split i=${i} (flipped)`, explText: `Check "${a.slice(0, i)}"~"${b.slice(-i)}" and "${a.slice(i)}"~"${b.slice(0, -i)}".` }, ctx);
          if (go(a.slice(0, i), b.slice(-i)) && go(a.slice(i), b.slice(0, -i))) { result = true; break; }
        }
        memo[key] = result;
      }
      T.ret(result);
      T.pop();
      return result;
    };
    const final = go(s1, s2);
    domPushState(seq, { stack: [], a: s1, b: s2, line: 7, color: final ? 'emerald' : 'rose', explTitle: 'Done', explText: `isScramble("${s1}", "${s2}") = ${final}.` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const strip = (label, str) => `
      <div class="glass-panel arrays-container">
          <div class="panel-heading">${label}</div>
          <div class="array-track">${[...str].map((c, i) => `<div class="array-node ${s.splitI !== undefined && i < s.splitI ? 'active-k' : s.splitI !== undefined ? 'merged' : ''}">${c}</div>`).join('')}</div>
      </div>`;
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:12px; width:100%;">
          ${strip('a', s.a)}
          ${strip('b', s.b)}
          ${stackPanelHTML(s)}
      </div>`;
  }
});

/* ============================================== 024 · Expression Add Operators */
defineAlgoDom('28_recursion_backtracking', {
  type: 'dom',
  title: 'Expression Add Operators', short: 'Expression Add Operators',
  idea: 'Backtracking over every way to (a) cut the digit string into chunks (no leading-zero multi-digit chunks) and (b) join each new chunk with +, - or *. Multiplication needs the previous chunk\'s signed value kept separately so it can be "undone" and redone at the new precedence.',
  complexity: 'Time O(4ⁿ) worst case · Space O(n) recursion depth',
  input: '123;6', hint: 'digit string ; target value (kept short)',
  code: [
    'def backtrack(index, path, eval_so_far, prev):',
    '    if index == n:',
    '        if eval_so_far == target: results.append(path)',
    '        return',
    '    for length in range(1, n - index + 1):',
    '        chunk = num[index:index+length]',
    '        if length > 1 and chunk[0] == "0": break',
    '        val = int(chunk)',
    '        if index == 0: backtrack(length, chunk, val, val); continue',
    '        backtrack(index+length, path+"+"+chunk, eval_so_far+val, val)',
    '        backtrack(index+length, path+"-"+chunk, eval_so_far-val, -val)',
    '        backtrack(index+length, path+"*"+chunk, eval_so_far-prev+prev*val, prev*val)',
  ],
  parse(s) {
    const [numStr, targetStr] = String(s || '').split(';');
    const num = (numStr || '').trim();
    if (!/^\d+$/.test(num)) throw new Error('The digit string must contain only digits');
    if (num.length > 5) throw new Error('Use at most 5 digits so the backtracking tree stays small');
    const target = parseInt((targetStr || '').trim(), 10);
    if (!Number.isFinite(target)) throw new Error('Add a target value after the ";"');
    return { num, target };
  },
  buildStates({ num, target }) {
    const seq = [], ctx = { t: 'Concept', x: 'Ready to begin.' };
    const T = mkTracer(seq, ctx);
    const n = num.length;
    const results = [];
    const backtrack = (index, path, evalSoFar, prev) => {
      T.call('backtrack', `idx=${index}, eval=${evalSoFar}`);
      domPushState(seq, { stack: T.stack.map(f => ({ ...f })), num, index, path, results: [...results], line: 1, color: 'blue', explTitle: `backtrack(index=${index}, path="${path}")`, explText: index === n ? 'Reached the end of the digit string.' : `${n - index} digit(s) remain.` }, ctx);
      if (index === n) {
        if (evalSoFar === target) { results.push(path); domPushState(seq, { stack: T.stack.map(f => ({ ...f })), num, index, path, results: [...results], line: 2, color: 'emerald', explTitle: 'Match!', explText: `path "${path}" evaluates to ${evalSoFar} = target. Record it.` }, ctx); }
        T.pop();
        return;
      }
      for (let length = 1; length <= n - index; length++) {
        const chunk = num.slice(index, index + length);
        if (length > 1 && chunk[0] === '0') { domPushState(seq, { stack: T.stack.map(f => ({ ...f })), num, index, path, results: [...results], line: 6, color: 'rose', explTitle: 'Leading zero', explText: `Chunk "${chunk}" has a leading zero and length > 1 — no longer chunk starting here can be valid either. Stop growing.` }, ctx); break; }
        const val = parseInt(chunk, 10);
        domPushState(seq, { stack: T.stack.map(f => ({ ...f })), num, index, path, results: [...results], line: 7, color: 'amber', explTitle: `Chunk "${chunk}"`, explText: `Take the next ${length} digit(s) as ${val}.` }, ctx);
        if (index === 0) { backtrack(length, chunk, val, val); continue; }
        backtrack(index + length, path + '+' + chunk, evalSoFar + val, val);
        backtrack(index + length, path + '-' + chunk, evalSoFar - val, -val);
        backtrack(index + length, path + '*' + chunk, evalSoFar - prev + prev * val, prev * val);
      }
      T.pop();
    };
    backtrack(0, '', 0, 0);
    domPushState(seq, { stack: [], num, index: n, path: '', results: [...results], line: 3, color: 'emerald', explTitle: 'Done', explText: `Found ${results.length} expression(s) equal to ${target}: ${results.join(', ') || '(none)'}.` }, ctx);
    return seq;
  },
  renderDOM(container, s) {
    const numHTML = [...s.num].map((c, i) => `<div class="array-node ${i < s.index ? 'merged' : i === s.index ? 'active-k' : ''}">${c}<div class="node-index">${i}</div></div>`).join('');
    container.innerHTML = `
      <div style="display:flex; flex-direction:column; gap:15px; width:100%;">
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">num</div>
                  <div class="array-track">${numHTML}</div>
              </div>
              <div class="glass-panel arrays-container">
                  <div class="panel-heading">Current path / results found</div>
                  <div style="padding:10px; font-family:var(--mono);">path so far: "${s.path}"</div>
                  <div style="display:flex; flex-wrap:wrap; gap:8px; padding:6px 10px;">${s.results.length ? s.results.map(r => `<span class="array-node merged" style="min-width:auto; padding:6px 12px; font-family:var(--mono);">${r}</span>`).join('') : '<span style="color:var(--text-dim);">(none yet)</span>'}</div>
              </div>
          ${stackPanelHTML(s)}
      </div>`;
  }
});
