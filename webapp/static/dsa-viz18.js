/* ============================================================================
   Visualizations for 10_trees (remaining 16 problems — 005 through 020).
   Canvas engine (defineAlgo). Reuses avTreeFromLevel / avLayoutBinary /
   avDrawBinary / avRecorder / AV.node from dsa-viz.js — see that file's
   "Tree traversals" (10_trees) and "BST insert/search" (11) specs for the
   original pattern this file follows.
   ========================================================================= */
'use strict';

/* Draw a binary tree inside a horizontal sub-region of the canvas — for
   problems that need two trees side by side (Same Tree, Subtree, Serialize/
   Deserialize). Just translates ctx and calls the existing avDrawBinary with
   a narrower fake canvas width. */
function avDrawBinaryIn(ctx, P, region, nodes, lay, style, opts) {
  ctx.save();
  ctx.translate(region.x, 0);
  const g = avDrawBinary(ctx, P, { w: region.w, h: region.h }, nodes, lay, style, opts);
  ctx.restore();
  return { x: id => g.x(id) + region.x, y: g.y };
}

/* ============================================================ 005 · max depth == */
defineAlgo('10_trees', {
  title: 'Maximum Depth of Binary Tree', short: 'Max Depth',
  idea: 'Postorder recursion: a node\'s depth is <b>1 + the deeper of its two children\'s depths</b>. The recursion has to reach every leaf (depth 0 for a null child) before a node above it can compute its own answer.',
  complexity: 'Time O(n) · Space O(h) recursion depth',
  input: '3, 9, 20, null, null, 15, 7', hint: 'level order, null for missing children',
  code: [
    'def maxDepth(root):',
    '    if not root:',
    '        return 0',
    '    return 1 + max(maxDepth(root.left),',
    '                   maxDepth(root.right))',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const depth = {};
    const S = (cur, extra = {}) => ({ nodes, cur, depth: { ...depth }, ...extra });
    const go = id => {
      if (id === -1) return 0;
      snap(0, `Call maxDepth(${nodes[id].val}).`, S(id, { vars: { node: nodes[id].val } }));
      const l = go(nodes[id].left), r = go(nodes[id].right);
      const d = 1 + Math.max(l, r);
      depth[id] = d;
      snap(3, `${nodes[id].val}: 1 + max(${l}, ${r}) = ${d}.`, S(id, { vars: { node: nodes[id].val, left: l, right: r, depth: d } }));
      return d;
    };
    const ans = go(0);
    snap(3, `Root returns ${ans}: the whole tree's max depth.`, S(null, { vars: { answer: ans } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 40; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.cur ? P.alpha('accent', .35) : f.depth[id] != null ? P.alpha('ok', .16) : null,
      stroke: id === f.cur ? P.accent : null,
      sub: f.depth[id] != null ? `d=${f.depth[id]}` : null,
    }));
  },
});

/* ============================================================ 006 · min depth == */
defineAlgo('10_trees', {
  title: 'Minimum Depth of Binary Tree', short: 'Min Depth',
  idea: 'BFS explores level by level, so the <b>first leaf it dequeues is automatically the shallowest one</b> — no need to visit the rest of the tree. DFS would have to explore every path to find the same answer.',
  complexity: 'Time O(n) worst case · Space O(w) for the queue',
  input: '2, null, 3, null, 4, null, 5, null, 6', hint: 'level order, null for missing children',
  code: [
    'def minDepth(root):',
    '    if not root:',
    '        return 0',
    '    q = deque([(root, 1)])',
    '    while q:',
    '        node, depth = q.popleft()',
    '        if not node.left and not node.right:',
    '            return depth',
    '        if node.left:',
    '            q.append((node.left, depth + 1))',
    '        if node.right:',
    '            q.append((node.right, depth + 1))',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    let q = [{ id: 0, d: 1 }];
    const S = (cur, extra = {}) => ({ nodes, cur, queue: q.map(x => `${nodes[x.id].val}@${x.d}`), ...extra });
    snap(3, 'Start BFS: root goes in the queue at depth 1.', S(0, { vars: { depth: 1 } }));
    while (q.length) {
      const { id, d } = q.shift();
      snap(5, `Dequeue ${nodes[id].val} (depth ${d}).`, S(id, { vars: { node: nodes[id].val, depth: d } }));
      const isLeaf = nodes[id].left === -1 && nodes[id].right === -1;
      if (isLeaf) { snap(7, `${nodes[id].val} is a leaf — first one found. Return ${d}.`, S(id, { leaf: id, vars: { answer: d } })); return F; }
      snap(6, `${nodes[id].val} has a child — keep exploring.`, S(id));
      if (nodes[id].left !== -1) { q.push({ id: nodes[id].left, d: d + 1 }); snap(9, `Enqueue left child ${nodes[nodes[id].left].val}.`, S(id)); }
      if (nodes[id].right !== -1) { q.push({ id: nodes[id].right, d: d + 1 }); snap(11, `Enqueue right child ${nodes[nodes[id].right].val}.`, S(id)); }
    }
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 60; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.leaf ? P.alpha('ok', .4) : id === f.cur ? P.alpha('accent', .35) : null,
      stroke: id === f.leaf ? P.ok : id === f.cur ? P.accent : null,
    }));
    D.text(ctx, `queue: [${f.queue.join(', ') || '—'}]`, 20, c.h - 16, { color: P.series[0], size: 12, mono: true });
  },
});

/* ============================================================== 007 · same tree == */
defineAlgo('10_trees', {
  title: 'Same Tree', short: 'Same Tree',
  idea: 'Walk both trees at once. At every pair of positions the shapes and values must agree — one null where the other has a node, or two different values, is an immediate <b>False</b>. Only when every pair matches all the way down is it <b>True</b>.',
  complexity: 'Time O(min(n, m)) · Space O(h)',
  input: '1, 2, 3 ; 1, 2, 3', hint: 'two level-order trees, separated by “;”',
  code: [
    'def isSameTree(p, q):',
    '    if not p and not q:',
    '        return True',
    '    if not p or not q:',
    '        return False',
    '    if p.val != q.val:',
    '        return False',
    '    return (isSameTree(p.left, q.left) and',
    '            isSameTree(p.right, q.right))',
  ],
  parse(s) {
    const [a, b] = avParts(s);
    return { na: avTreeFromLevel(a), nb: avTreeFromLevel(b) };
  },
  run({ na, nb }) {
    const { F, snap } = avRecorder();
    const S = (curA, curB, extra = {}) => ({ na, nb, curA, curB, ...extra });
    const go = (a, b) => {
      if (a === -1 && b === -1) { snap(1, 'Both sides null here — match.', S(a, b)); return true; }
      if (a === -1 || b === -1) { snap(3, 'One side is null, the other is not — mismatch.', S(a, b, { bad: true })); return false; }
      snap(5, `Compare ${na[a].val} vs ${nb[b].val}.`, S(a, b, { vars: { p: na[a].val, q: nb[b].val } }));
      if (na[a].val !== nb[b].val) { snap(6, `${na[a].val} ≠ ${nb[b].val} — mismatch.`, S(a, b, { bad: true })); return false; }
      return go(na[a].left, nb[b].left) && go(na[a].right, nb[b].right);
    };
    const ans = go(0, 0);
    snap(0, `Trees are ${ans ? 'the same' : 'different'}.`, S(null, null, { vars: { result: ans } }));
    return F;
  },
  height: (w, last) => { const la = avLayoutBinary(last.na), lb = avLayoutBinary(last.nb); return 60 + Math.max(la.depth, lb.depth) * 58 + 30; },
  draw(ctx, c, f, P) {
    const la = avLayoutBinary(f.na), lb = avLayoutBinary(f.nb);
    const style = (cur, bad) => id => ({ fill: id === cur ? P.alpha(bad ? 'err' : 'accent', .35) : null, stroke: id === cur ? (bad ? P.err : P.accent) : null });
    avDrawBinaryIn(ctx, P, { x: 0, w: c.w / 2, h: c.h }, f.na, la, style(f.curA, f.bad));
    avDrawBinaryIn(ctx, P, { x: c.w / 2, w: c.w / 2, h: c.h }, f.nb, lb, style(f.curB, f.bad));
    D.line(ctx, c.w / 2, 0, c.w / 2, c.h, P.strong, 1);
    D.text(ctx, 'p', 14, 16, { color: P.dim, size: 12, weight: 700 });
    D.text(ctx, 'q', c.w / 2 + 14, 16, { color: P.dim, size: 12, weight: 700 });
  },
});

/* ===================================================== 008 · subtree of another == */
defineAlgo('10_trees', {
  title: 'Subtree of Another Tree', short: 'Subtree',
  idea: 'Try <b>isSameTree</b> at every node of the main tree. The moment one of them matches subRoot exactly, it is a subtree — otherwise recurse into both children and keep trying.',
  complexity: 'Time O(n·m) worst case · Space O(h)',
  input: '3, 4, 5, 1, 2 ; 4, 1, 2', hint: 'main tree ; candidate subtree',
  code: [
    'def isSubtree(root, subRoot):',
    '    if not root:',
    '        return subRoot is None',
    '    if isSameTree(root, subRoot):',
    '        return True',
    '    return (isSubtree(root.left, subRoot) or',
    '            isSubtree(root.right, subRoot))',
  ],
  parse(s) {
    const [a, b] = avParts(s);
    return { na: avTreeFromLevel(a), nb: avTreeFromLevel(b) };
  },
  run({ na, nb }) {
    const { F, snap } = avRecorder();
    const same = (a, b) => {
      if (a === -1 && b === -1) return true;
      if (a === -1 || b === -1) return false;
      if (na[a].val !== nb[b].val) return false;
      return same(na[a].left, nb[b].left) && same(na[a].right, nb[b].right);
    };
    const S = (cur, extra = {}) => ({ na, nb, cur, ...extra });
    const go = id => {
      if (id === -1) { snap(2, 'Ran off the tree without a match.', S(null)); return false; }
      snap(3, `Try isSameTree at ${na[id].val}.`, S(id));
      if (same(id, 0)) { snap(4, `Match! The subtree rooted at ${na[id].val} equals subRoot.`, S(id, { found: id })); return true; }
      snap(6, `No match at ${na[id].val} — recurse into its children.`, S(id));
      return go(na[id].left) || go(na[id].right);
    };
    const ans = go(0);
    snap(0, `Result: ${ans}.`, S(null, { vars: { result: ans } }));
    return F;
  },
  height: (w, last) => { const la = avLayoutBinary(last.na), lb = avLayoutBinary(last.nb); return 60 + Math.max(la.depth, lb.depth) * 58 + 30; },
  draw(ctx, c, f, P) {
    const la = avLayoutBinary(f.na), lb = avLayoutBinary(f.nb);
    avDrawBinaryIn(ctx, P, { x: 0, w: c.w * .62, h: c.h }, f.na, la, id => ({
      fill: id === f.found ? P.alpha('ok', .4) : id === f.cur ? P.alpha('accent', .35) : null,
      stroke: id === f.found ? P.ok : id === f.cur ? P.accent : null,
    }));
    avDrawBinaryIn(ctx, P, { x: c.w * .64, w: c.w * .36, h: c.h }, f.nb, lb, () => ({}));
    D.line(ctx, c.w * .63, 0, c.w * .63, c.h, P.strong, 1);
    D.text(ctx, 'root', 14, 16, { color: P.dim, size: 12, weight: 700 });
    D.text(ctx, 'subRoot', c.w * .64 + 14, 16, { color: P.dim, size: 12, weight: 700 });
  },
});

/* ======================================================= 009 · balanced tree == */
defineAlgo('10_trees', {
  title: 'Balanced Binary Tree', short: 'Balanced?',
  idea: 'One postorder pass computes height AND balance together: <b>height(node) returns -1</b> the instant any subtree below is already unbalanced, so a broken branch poisons everything above it without a second traversal.',
  complexity: 'Time O(n) · Space O(h)',
  input: '3, 9, 20, null, null, 15, 7', hint: 'level order, null for missing children',
  code: [
    'def check(node):',
    '    if node is None:',
    '        return 0',
    '    lh = check(node.left)',
    '    if lh == -1: return -1',
    '    rh = check(node.right)',
    '    if rh == -1: return -1',
    '    if abs(lh - rh) > 1:',
    '        return -1',
    '    return 1 + max(lh, rh)',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const h = {};
    const S = (cur, extra = {}) => ({ nodes, cur, h: { ...h }, ...extra });
    const go = id => {
      if (id === -1) return 0;
      snap(0, `check(${nodes[id].val}).`, S(id));
      const lh = go(nodes[id].left);
      if (lh === -1) { h[id] = -1; snap(4, `Left subtree of ${nodes[id].val} is already unbalanced — bail out.`, S(id, { bad: id })); return -1; }
      const rh = go(nodes[id].right);
      if (rh === -1) { h[id] = -1; snap(6, `Right subtree of ${nodes[id].val} is already unbalanced — bail out.`, S(id, { bad: id })); return -1; }
      if (Math.abs(lh - rh) > 1) { h[id] = -1; snap(8, `${nodes[id].val}: heights ${lh} and ${rh} differ by more than 1 — unbalanced.`, S(id, { bad: id })); return -1; }
      const height = 1 + Math.max(lh, rh);
      h[id] = height;
      snap(9, `${nodes[id].val}: balanced here, height ${height}.`, S(id, { vars: { node: nodes[id].val, height } }));
      return height;
    };
    const ans = go(0) !== -1;
    snap(0, `Tree is ${ans ? 'balanced' : 'not balanced'}.`, S(null, { vars: { result: ans } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.bad ? P.alpha('err', .35) : id === f.cur ? P.alpha('accent', .35) : f.h[id] != null ? P.alpha('ok', .14) : null,
      stroke: id === f.bad ? P.err : id === f.cur ? P.accent : null,
      sub: f.h[id] != null ? (f.h[id] === -1 ? '✗' : `h=${f.h[id]}`) : null,
    }));
  },
});

/* ======================================================= 010 · diameter == */
defineAlgo('10_trees', {
  title: 'Diameter of Binary Tree', short: 'Diameter',
  idea: 'The longest path between any two nodes always passes <b>through</b> some node as its highest point, contributing left-height + right-height edges. Postorder height computes both the height AND the best diameter candidate in one pass.',
  complexity: 'Time O(n) · Space O(h)',
  input: '1, 2, 3, 4, 5', hint: 'level order, null for missing children',
  code: [
    'def height(node):',
    '    if node is None:',
    '        return 0',
    '    l = height(node.left)',
    '    r = height(node.right)',
    '    best = max(best, l + r)',
    '    return 1 + max(l, r)',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    let best = 0; const h = {};
    const S = (cur, extra = {}) => ({ nodes, cur, h: { ...h }, best, ...extra });
    const go = id => {
      if (id === -1) return 0;
      snap(0, `height(${nodes[id].val}).`, S(id));
      const l = go(nodes[id].left), r = go(nodes[id].right);
      const prevBest = best;
      best = Math.max(best, l + r);
      h[id] = 1 + Math.max(l, r);
      snap(5, best > prevBest ? `${nodes[id].val}: path through here is ${l} + ${r} = ${l + r} edges — new best!` : `${nodes[id].val}: path through here is ${l + r}, not better than ${best}.`, S(id, { vars: { node: nodes[id].val, l, r, best } }));
      return h[id];
    };
    go(0);
    snap(5, `Diameter is ${best} edges.`, S(null, { vars: { answer: best } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 50; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.cur ? P.alpha('accent', .35) : f.h[id] != null ? P.alpha('ok', .14) : null,
      stroke: id === f.cur ? P.accent : null,
      sub: f.h[id] != null ? `h=${f.h[id]}` : null,
    }));
    D.text(ctx, `best diameter so far: ${f.best}`, 20, c.h - 16, { color: P.ok, size: 12.5, mono: true, weight: 700 });
  },
});

/* ============================================================ 011 · path sum == */
defineAlgo('10_trees', {
  title: 'Path Sum', short: 'Path Sum',
  idea: 'Carry the <b>remaining</b> target down as you descend, subtracting each node\'s value. A leaf is a hit only if the remaining amount is exactly zero right there — not before, not after.',
  complexity: 'Time O(n) · Space O(h)',
  input: '5, 4, 8, 11, null, 13, 4, 7, 2, null, null, null, 1 ; 22', hint: 'tree ; target sum',
  code: [
    'def go(node, remaining):',
    '    remaining -= node.val',
    '    if not node.left and not node.right:',
    '        return remaining == 0',
    '    if node.left and go(node.left, remaining):',
    '        return True',
    '    if node.right and go(node.right, remaining):',
    '        return True',
    '    return False',
  ],
  parse(s) { const [a, t] = avParts(s); return { nodes: avTreeFromLevel(a), target: avNum(t, 'a target sum') }; },
  run({ nodes, target }) {
    const { F, snap } = avRecorder();
    const S = (cur, remaining, path, extra = {}) => ({ nodes, cur, path: [...path], vars: { remaining }, ...extra });
    const go = (id, remaining, path) => {
      remaining -= nodes[id].val;
      path.push(id);
      snap(1, `At ${nodes[id].val}: remaining = ${remaining + nodes[id].val} - ${nodes[id].val} = ${remaining}.`, S(id, remaining, path));
      const isLeaf = nodes[id].left === -1 && nodes[id].right === -1;
      if (isLeaf) {
        const hit = remaining === 0;
        snap(3, `Leaf ${nodes[id].val}: remaining is ${remaining} — ${hit ? 'exactly 0, path found!' : 'not 0, dead end.'}`, S(id, remaining, path, { hit }));
        path.pop();
        return hit;
      }
      if (nodes[id].left !== -1 && go(nodes[id].left, remaining, path)) return true;
      if (nodes[id].right !== -1 && go(nodes[id].right, remaining, path)) return true;
      path.pop();
      return false;
    };
    const ans = go(0, target, []);
    snap(0, `Result: ${ans}.`, S(null, 0, [], { vars: { result: ans } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes), onPath = new Set(f.path);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: f.hit && id === f.cur ? P.alpha('ok', .4) : id === f.cur ? P.alpha('accent', .35) : onPath.has(id) ? P.alpha('accent', .14) : null,
      stroke: f.hit && id === f.cur ? P.ok : id === f.cur ? P.accent : onPath.has(id) ? P.accent : null,
      edge: onPath.has(id) ? P.accent : null,
    }));
  },
});

/* ========================================================= 012 · symmetric == */
defineAlgo('10_trees', {
  title: 'Symmetric Tree', short: 'Symmetric?',
  idea: 'A tree is symmetric if its left half is a <b>mirror image</b> of its right half. Compare left-outer with right-outer, and left-inner with right-inner — crossed pairing, not the same-position pairing that isSameTree uses.',
  complexity: 'Time O(n) · Space O(h)',
  input: '1, 2, 2, 3, 4, 4, 3', hint: 'level order, null for missing children',
  code: [
    'def isMirror(left, right):',
    '    if not left and not right:',
    '        return True',
    '    if not left or not right:',
    '        return False',
    '    if left.val != right.val:',
    '        return False',
    '    return (isMirror(left.left, right.right) and',
    '            isMirror(left.right, right.left))',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const S = (a, b, extra = {}) => ({ nodes, pair: [a, b].filter(x => x !== -1 && x != null), ...extra });
    const go = (a, b) => {
      if (a === -1 && b === -1) { snap(1, 'Both sides null — mirrors here.', S(a, b)); return true; }
      if (a === -1 || b === -1) { snap(3, 'One side null, the other not — not symmetric.', S(a, b, { bad: true })); return false; }
      snap(5, `Compare ${nodes[a].val} (left) with ${nodes[b].val} (right).`, S(a, b, { vars: { left: nodes[a].val, right: nodes[b].val } }));
      if (nodes[a].val !== nodes[b].val) { snap(6, `${nodes[a].val} ≠ ${nodes[b].val} — not symmetric.`, S(a, b, { bad: true })); return false; }
      return go(nodes[a].left, nodes[b].right) && go(nodes[a].right, nodes[b].left);
    };
    if (nodes.length <= 1) { snap(0, 'A single node (or empty tree) is trivially symmetric.', S(-1, -1, { vars: { result: true } })); return F; }
    const ans = go(nodes[0].left, nodes[0].right);
    snap(0, `Result: ${ans}.`, S(-1, -1, { vars: { result: ans } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes), pair = new Set(f.pair || []);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: pair.has(id) ? P.alpha(f.bad ? 'err' : 'accent', .35) : null,
      stroke: pair.has(id) ? (f.bad ? P.err : P.accent) : null,
    }));
  },
});

/* ============================================== 013 · level order traversal == */
defineAlgo('10_trees', {
  title: 'Binary Tree Level Order Traversal', short: 'Level Order',
  idea: 'BFS with a queue naturally visits the tree one level at a time. Snapshotting <code>len(q)</code> once before the inner loop tells you exactly how many nodes belong to the current level, so you can close each level into its own list.',
  complexity: 'Time O(n) · Space O(w) for the widest level',
  input: '3, 9, 20, null, null, 15, 7', hint: 'level order, null for missing children',
  code: [
    'def levelOrder(root):',
    '    out, q = [], deque([root])',
    '    while q:',
    '        level = []',
    '        for _ in range(len(q)):',
    '            node = q.popleft()',
    '            level.append(node.val)',
    '            if node.left: q.append(node.left)',
    '            if node.right: q.append(node.right)',
    '        out.append(level)',
    '    return out',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const out = []; let q = [0];
    const S = (cur, level, extra = {}) => ({ nodes, cur, out: out.map(l => [...l]), level: [...level], queue: q.map(id => nodes[id].val), ...extra });
    while (q.length) {
      const width = q.length, level = [];
      snap(4, `New level: ${width} node${width > 1 ? 's' : ''} currently queued.`, S(null, level));
      for (let i = 0; i < width; i++) {
        const id = q.shift();
        level.push(nodes[id].val);
        snap(6, `Visit ${nodes[id].val} — add it to this level.`, S(id, level));
        if (nodes[id].left !== -1) { q.push(nodes[id].left); snap(7, `Enqueue left child ${nodes[nodes[id].left].val}.`, S(id, level)); }
        if (nodes[id].right !== -1) { q.push(nodes[id].right); snap(8, `Enqueue right child ${nodes[nodes[id].right].val}.`, S(id, level)); }
      }
      out.push(level);
      snap(9, `Level complete: [${level.join(', ')}].`, S(null, [], { justClosed: [...level] }));
    }
    snap(10, `All levels: ${JSON.stringify(out)}.`, S(null, [], { vars: { levels: out.length } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 70; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes), doneVals = new Set(f.out.flat());
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.cur ? P.alpha('accent', .35) : doneVals.has(f.nodes[id].val) ? P.alpha('ok', .16) : null,
      stroke: id === f.cur ? P.accent : null,
    }));
    let y = c.h - 16 - (f.out.length) * 18;
    f.out.forEach((lvl, i) => D.text(ctx, `level ${i}: [${lvl.join(', ')}]`, 20, y + i * 18, { color: P.ok, size: 11.5, mono: true }));
    if (f.level.length) D.text(ctx, `building: [${f.level.join(', ')}]`, 20, y + f.out.length * 18, { color: P.accent, size: 11.5, mono: true, weight: 700 });
  },
});

/* ============================================ 014 · right side view == */
defineAlgo('10_trees', {
  title: 'Binary Tree Right Side View', short: 'Right Side View',
  idea: 'BFS level by level, keeping only the <b>last node dequeued at each level</b> — that is the rightmost node still visible when the tree is viewed from the right.',
  complexity: 'Time O(n) · Space O(w)',
  input: '1, 2, 3, null, 5, null, 4', hint: 'level order, null for missing children',
  code: [
    'def rightSideView(root):',
    '    out, q = [], deque([root])',
    '    while q:',
    '        width = len(q)',
    '        for i in range(width):',
    '            node = q.popleft()',
    '            if i == width - 1:',
    '                out.append(node.val)',
    '            if node.left: q.append(node.left)',
    '            if node.right: q.append(node.right)',
    '    return out',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const out = []; let q = [0];
    const S = (cur, extra = {}) => ({ nodes, cur, out: [...out], ...extra });
    while (q.length) {
      const width = q.length;
      snap(3, `Level width is ${width}.`, S(null));
      for (let i = 0; i < width; i++) {
        const id = q.shift();
        const rightmost = i === width - 1;
        snap(6, rightmost ? `${nodes[id].val} is the last one this level — it's visible from the right.` : `${nodes[id].val} — not the last of this level, hidden from the right.`, S(id, { rightmost }));
        if (rightmost) out.push(nodes[id].val);
        if (nodes[id].left !== -1) q.push(nodes[id].left);
        if (nodes[id].right !== -1) q.push(nodes[id].right);
      }
    }
    snap(0, `Right side view: [${out.join(', ')}].`, S(null, { vars: { view: out.join(', ') } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 40; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes), seen = new Set(f.out);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.cur ? P.alpha(f.rightmost ? 'ok' : 'accent', .35) : seen.has(f.nodes[id].val) ? P.alpha('ok', .16) : null,
      stroke: id === f.cur ? (f.rightmost ? P.ok : P.accent) : null,
    }));
    D.text(ctx, `view so far: [${f.out.join(', ')}]`, 20, c.h - 16, { color: P.ok, size: 12.5, mono: true, weight: 700 });
  },
});

/* ============================================ 015 · count good nodes == */
defineAlgo('10_trees', {
  title: 'Count Good Nodes in Binary Tree', short: 'Good Nodes',
  idea: 'Carry the <b>maximum value seen so far on the path from the root</b> down as you descend. A node is "good" if its value is at least that running maximum — ties count, because the node itself would then become the new path maximum.',
  complexity: 'Time O(n) · Space O(h)',
  input: '3, 1, 4, 3, null, 1, 5', hint: 'level order, null for missing children',
  code: [
    'def go(node, best):',
    '    if node is None:',
    '        return',
    '    if node.val >= best:',
    '        count += 1',
    '    best = max(best, node.val)',
    '    go(node.left, best)',
    '    go(node.right, best)',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    let count = 0; const good = new Set();
    const S = (cur, best, extra = {}) => ({ nodes, cur, good: [...good], vars: { best, count }, ...extra });
    const go = (id, best) => {
      snap(0, `Visit ${nodes[id].val} — path max so far is ${best}.`, S(id, best));
      if (nodes[id].val >= best) { count++; good.add(id); snap(4, `${nodes[id].val} ≥ ${best} — good node! (${count} so far)`, S(id, best)); }
      const nb = Math.max(best, nodes[id].val);
      if (nodes[id].left !== -1) go(nodes[id].left, nb);
      if (nodes[id].right !== -1) go(nodes[id].right, nb);
    };
    go(0, nodes[0].val);
    snap(0, `Total good nodes: ${count}.`, S(null, null, { vars: { answer: count } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes), good = new Set(f.good);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.cur ? P.alpha('accent', .35) : good.has(id) ? P.alpha('ok', .25) : null,
      stroke: id === f.cur ? P.accent : good.has(id) ? P.ok : null,
      ring: good.has(id) ? P.alpha('ok', .8) : null,
    }));
  },
});

/* ========================== 016 · construct from preorder+inorder == */
defineAlgo('10_trees', {
  title: 'Construct Binary Tree from Preorder and Inorder Traversal', short: 'Build from Pre+In',
  idea: 'Preorder always lists the <b>root first</b>. Find that value in inorder — everything to its left is the left subtree, everything to its right is the right subtree. Recurse on each side, walking the shared preorder cursor forward exactly once per node.',
  complexity: 'Time O(n) with an index map · Space O(n)',
  input: '3, 9, 20, 15, 7 ; 9, 3, 15, 20, 7', hint: 'preorder ; inorder',
  code: [
    'def go(lo, hi):',
    '    if lo > hi:',
    '        return None',
    '    val = preorder[cursor]; cursor += 1',
    '    node = TreeNode(val)',
    '    k = pos[val]',
    '    node.left = go(lo, k - 1)',
    '    node.right = go(k + 1, hi)',
    '    return node',
  ],
  parse(s) {
    const [a, b] = avParts(s);
    const pre = avNums(a, 12, 'preorder values'), ino = avNums(b, 12, 'inorder values');
    if (pre.length !== ino.length) throw new Error('preorder and inorder must have the same length');
    if (new Set(pre).size !== pre.length) throw new Error('Use distinct values so the visualization stays unambiguous');
    return { pre, ino };
  },
  run({ pre, ino }) {
    const { F, snap } = avRecorder();
    const pos = {}; ino.forEach((v, i) => pos[v] = i);
    let cursor = 0;
    const nodes = []; // {val, left, right}, index = node id, root always 0
    const S = (cur, lo, hi, extra = {}) => ({ nodes: nodes.map(n => ({ ...n })), pre, ino, cur, cursor, range: [lo, hi], ...extra });
    const go = (lo, hi) => {
      if (lo > hi) { snap(1, 'Empty interval — no node here.', S(null, lo, hi)); return -1; }
      const val = pre[cursor];
      snap(3, `Next preorder value is ${val} — that's this subtree's root.`, S(null, lo, hi, { vars: { val } }));
      cursor++;
      nodes.push({ val, left: -1, right: -1 });
      const id = nodes.length - 1;
      const k = pos[val];
      snap(6, `${val} sits at inorder index ${k}: left subtree is indices ${lo}..${k - 1}, right is ${k + 1}..${hi}.`, S(id, lo, hi));
      nodes[id].left = go(lo, k - 1);
      nodes[id].right = go(k + 1, hi);
      return id;
    };
    go(0, ino.length - 1);
    snap(8, 'Tree fully built.', S(null, 0, ino.length - 1, { done: true }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 100 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    AV.row(ctx, P, f.pre, { cw: c.w, y: 20, max: 34, style: i => ({ fade: i < f.cursor }) });
    D.text(ctx, 'preorder', 14, 14, { color: P.dim, size: 10.5 });
    AV.row(ctx, P, f.ino, { cw: c.w, y: 62, max: 34, style: i => ({ fill: i >= f.range[0] && i <= f.range[1] ? P.alpha('accent', .18) : null }) });
    D.text(ctx, 'inorder', 14, 56, { color: P.dim, size: 10.5 });
    if (f.nodes.length) {
      const lay = avLayoutBinary(f.nodes);
      avDrawBinary(ctx, P, { w: c.w, h: c.h - 96 }, f.nodes, lay, id => ({
        fill: id === f.cur ? P.alpha('accent', .35) : null,
        stroke: id === f.cur ? P.accent : null,
      }), { top: 96 + 36 });
    }
  },
});

/* ==================================== 017 · lowest common ancestor == */
defineAlgo('10_trees', {
  title: 'Lowest Common Ancestor of a Binary Tree', short: 'LCA',
  idea: 'Postorder recursion: a node reports "found p or q" up to its parent by returning non-null. The <b>first node where both children report a find</b> is exactly where the two search paths split — the LCA.',
  complexity: 'Time O(n) · Space O(h)',
  input: '3, 5, 1, 6, 2, 0, 8, null, null, 7, 4 ; 5 ; 4', hint: 'tree ; value p ; value q',
  code: [
    'def lca(root, p, q):',
    '    if root is None or root is p or root is q:',
    '        return root',
    '    left = lca(root.left, p, q)',
    '    right = lca(root.right, p, q)',
    '    if left and right:',
    '        return root',
    '    return left if left else right',
  ],
  parse(s) {
    const [a, pStr, qStr] = avParts(s);
    const nodes = avTreeFromLevel(a);
    const p = avNum(pStr, 'value p'), q = avNum(qStr, 'value q');
    if (!nodes.some(n => n.val === p)) throw new Error(`${p} is not in the tree`);
    if (!nodes.some(n => n.val === q)) throw new Error(`${q} is not in the tree`);
    return { nodes, p, q };
  },
  run({ nodes, p, q }) {
    const { F, snap } = avRecorder();
    const S = (cur, extra = {}) => ({ nodes, cur, p, q, ...extra });
    const go = id => {
      if (id === -1) return -1;
      if (nodes[id].val === p || nodes[id].val === q) { snap(1, `Found ${nodes[id].val === p ? 'p' : 'q'} = ${nodes[id].val} — report it upward.`, S(id, { hit: id })); return id; }
      snap(0, `Search below ${nodes[id].val}.`, S(id));
      const l = go(nodes[id].left), r = go(nodes[id].right);
      if (l !== -1 && r !== -1) { snap(6, `${nodes[id].val}: p and q were found on DIFFERENT sides — this is the LCA.`, S(id, { lca: id })); return id; }
      return l !== -1 ? l : r;
    };
    const ans = go(0);
    snap(0, `Lowest common ancestor: ${nodes[ans].val}.`, S(ans, { lca: ans, vars: { lca: nodes[ans].val } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.lca ? P.alpha('ok', .4) : id === f.hit ? P.alpha('accent', .35) : id === f.cur ? P.alpha('accent', .18) : null,
      stroke: id === f.lca ? P.ok : (id === f.hit || id === f.cur) ? P.accent : null,
      sub: f.nodes[id].val === f.p ? 'p' : f.nodes[id].val === f.q ? 'q' : null,
    }));
  },
});

/* ===================================== 018 · max path sum == */
defineAlgo('10_trees', {
  title: 'Binary Tree Maximum Path Sum', short: 'Max Path Sum',
  idea: 'Postorder "gain": a subtree only contributes to its parent\'s path if it is positive — a negative branch is clipped to 0. Separately, at every node, RECORD the best path that turns around here (both children\'s gains plus the node), even though only ONE side can continue upward.',
  complexity: 'Time O(n) · Space O(h)',
  input: '-10, 9, 20, null, null, 15, 7', hint: 'level order, null for missing children (values may be negative)',
  code: [
    'def gain(node):',
    '    if node is None:',
    '        return 0',
    '    left = max(gain(node.left), 0)',
    '    right = max(gain(node.right), 0)',
    '    best = max(best, node.val + left + right)',
    '    return node.val + max(left, right)',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    let best = -Infinity; const gains = {};
    const S = (cur, extra = {}) => ({ nodes, cur, gains: { ...gains }, best, ...extra });
    const go = id => {
      if (id === -1) return 0;
      snap(0, `gain(${nodes[id].val}).`, S(id));
      const l = Math.max(go(nodes[id].left), 0), r = Math.max(go(nodes[id].right), 0);
      const through = nodes[id].val + l + r;
      const prevBest = best;
      best = Math.max(best, through);
      const g = nodes[id].val + Math.max(l, r);
      gains[id] = g;
      snap(5, best > prevBest ? `${nodes[id].val}: path turning here is ${nodes[id].val}+${l}+${r} = ${through} — new best!` : `${nodes[id].val}: path turning here is ${through}, best stays ${best}.`, S(id, { vars: { node: nodes[id].val, left: l, right: r, through, best } }));
      return g;
    };
    go(0);
    snap(6, `Maximum path sum: ${best}.`, S(null, { vars: { answer: best } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 50; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.cur ? P.alpha('accent', .35) : f.gains[id] != null ? P.alpha('ok', .14) : null,
      stroke: id === f.cur ? P.accent : null,
      sub: f.gains[id] != null ? `gain=${f.gains[id]}` : null,
    }));
    D.text(ctx, `best path sum so far: ${f.best === -Infinity ? '—' : f.best}`, 20, c.h - 16, { color: P.ok, size: 12.5, mono: true, weight: 700 });
  },
});

/* =========================== 019 · serialize and deserialize == */
defineAlgo('10_trees', {
  title: 'Serialize and Deserialize Binary Tree', short: 'Serialize/Deserialize',
  idea: 'Preorder (root, left, right) plus a marker for every empty child makes the encoding <b>lossless</b> — the shape is recoverable with no ambiguity. Decoding just replays the same order: read one token, and if it wasn\'t a marker, its two children come next in the stream.',
  complexity: 'Time O(n) both ways · Space O(n)',
  input: '1, 2, null, null, 3, 4, null, null, 5', hint: 'level order, null for missing children',
  code: [
    '# serialize: preorder, "#" for every empty child',
    'def walk(node):',
    '    if node is None:',
    '        out.append("#"); return',
    '    out.append(str(node.val))',
    '    walk(node.left); walk(node.right)',
    '',
    '# deserialize: one shared cursor into the tokens',
    'def build():',
    '    tok = tokens[idx]; idx += 1',
    '    if tok == "#": return None',
    '    node = TreeNode(int(tok))',
    '    node.left = build(); node.right = build()',
    '    return node',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const tokens = [];
    const S = (cur, extra = {}) => ({ nodes, tokens: [...tokens], cur, phase: 'serialize', ...extra });
    const walk = id => {
      if (id === -1) { tokens.push('#'); snap(3, 'Empty child — write "#".', S(null)); return; }
      snap(4, `Write ${nodes[id].val}.`, S(id));
      tokens.push(String(nodes[id].val));
      walk(nodes[id].left); walk(nodes[id].right);
    };
    walk(0);
    snap(0, `Serialized: ${tokens.join(',')}`, S(null, { vars: { serialized: tokens.join(',') } }));

    let idx = 0; const built = [];
    const S2 = (cur, extra = {}) => ({ nodes: built.map(n => ({ ...n })), tokens, idx, cur, phase: 'deserialize', ...extra });
    const build = () => {
      const tok = tokens[idx]; idx++;
      if (tok === '#') { snap(10, 'Read "#" — this is a null child.', S2(null)); return -1; }
      built.push({ val: Number(tok), left: -1, right: -1 });
      const id = built.length - 1;
      snap(11, `Read ${tok} — create a node.`, S2(id));
      built[id].left = build();
      built[id].right = build();
      return id;
    };
    build();
    snap(0, 'Rebuilt tree matches the original.', S2(0, { done: true }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 100 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    D.text(ctx, f.phase === 'serialize' ? 'serializing…' : 'deserializing…', 14, 16, { color: P.dim, size: 11, weight: 650 });
    D.text(ctx, `tokens: [${f.tokens.join(', ')}]`, 14, 34, { color: P.accent, size: 11.5, mono: true });
    if (f.nodes.length) {
      const lay = avLayoutBinary(f.nodes);
      avDrawBinary(ctx, P, { w: c.w, h: c.h - 56 }, f.nodes, lay, id => ({
        fill: id === f.cur ? P.alpha('accent', .35) : null,
        stroke: id === f.cur ? P.accent : null,
      }), { top: 56 + 36 });
    }
  },
});

/* ========================= 020 · all nodes distance k == */
defineAlgo('10_trees', {
  title: 'All Nodes Distance K in Binary Tree', short: 'Distance K',
  idea: 'A binary tree only has child pointers, so reaching a node\'s <b>parent</b> means first recording one — one DFS/BFS pass builds a parent map. From there it is a plain multi-source BFS from the target through left, right, AND parent, stopping at distance k.',
  complexity: 'Time O(n) · Space O(n)',
  input: '3, 5, 1, 6, 2, 0, 8, null, null, 7, 4 ; 5 ; 2', hint: 'tree ; target value ; k',
  code: [
    'parent = {root: None}',
    'for node in preorder(root):',
    '    for child in (node.left, node.right):',
    '        if child: parent[child] = node',
    '',
    'queue, seen = deque([target]), {target}',
    'for _ in range(k):',
    '    for _ in range(len(queue)):',
    '        node = queue.popleft()',
    '        for nxt in (node.left, node.right, parent[node]):',
    '            if nxt and nxt not in seen:',
    '                seen.add(nxt); queue.append(nxt)',
  ],
  parse(s) {
    const [a, tStr, kStr] = avParts(s);
    const nodes = avTreeFromLevel(a);
    const target = avNum(tStr, 'a target value');
    const k = avNum(kStr, 'k');
    if (!nodes.some(n => n.val === target)) throw new Error(`${target} is not in the tree`);
    if (k < 0 || k > 10) throw new Error('Use a k between 0 and 10');
    return { nodes, target, k };
  },
  run({ nodes, target, k }) {
    const { F, snap } = avRecorder();
    const parent = {};
    const S = (cur, extra = {}) => ({ nodes, cur, parent: { ...parent }, ...extra });
    const walk = (id, p) => {
      if (id === -1) return;
      parent[id] = p;
      if (p !== -1) snap(3, `Record ${nodes[id].val}'s parent as ${nodes[p].val}.`, S(id));
      walk(nodes[id].left, id); walk(nodes[id].right, id);
    };
    walk(0, -1);
    snap(0, 'Parent map complete.', S(null));

    const targetId = nodes.findIndex(n => n.val === target);
    let q = [targetId]; const seen = new Set([targetId]);
    snap(5, `Start BFS from ${target} (distance 0).`, S(targetId, { dist: 0, seen: [...seen] }));
    for (let d = 1; d <= k; d++) {
      if (!q.length) break;
      const next = [];
      snap(7, `Expand to distance ${d}.`, S(null, { dist: d, seen: [...seen] }));
      for (const id of q) {
        for (const nxt of [nodes[id].left, nodes[id].right, parent[id]]) {
          if (nxt !== -1 && nxt != null && !seen.has(nxt)) { seen.add(nxt); next.push(nxt); }
        }
      }
      q = next;
      snap(10, `Nodes newly reached at distance ${d}: ${q.map(id => nodes[id].val).join(', ') || '(none)'}.`, S(null, { dist: d, seen: [...seen], frontier: [...q] }));
    }
    snap(0, `Nodes at distance ${k}: [${q.map(id => nodes[id].val).join(', ')}].`, S(null, { frontier: [...q], vars: { answer: q.map(id => nodes[id].val).join(', ') } }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 40; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes), seen = new Set(f.seen || []), frontier = new Set(f.frontier || []);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: frontier.has(id) ? P.alpha('ok', .4) : id === f.cur ? P.alpha('accent', .35) : seen.has(id) ? P.alpha('accent', .14) : null,
      stroke: frontier.has(id) ? P.ok : id === f.cur ? P.accent : null,
    }));
    D.text(ctx, `distance: ${f.dist ?? 0}`, 20, c.h - 16, { color: P.accent, size: 12.5, mono: true, weight: 700 });
  },
});
