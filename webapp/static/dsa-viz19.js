/* ============================================================================
   Visualizations for 11_binary_search_tree (remaining 9 problems).
   Canvas engine (defineAlgo). Reuses avTreeFromLevel / avLayoutBinary /
   avDrawBinary / avRecorder / AV.node / avParts / avNums / avNum from
   dsa-viz.js — see that file's "Binary search tree: insert and search"
   spec (already covering 001 and 003) for the pattern this file follows.
   ========================================================================= */
'use strict';

/* ============================================== 002 · sorted array to BST == */
defineAlgo('11_binary_search_tree', {
  title: 'Convert Sorted Array to Binary Search Tree', short: 'Sorted Array → BST',
  idea: 'Always pick the <b>middle</b> of the current [lo, hi] window as the root of that subtree, then recurse on the two halves. Picking the middle is what keeps the tree height O(log n) instead of O(n) — a first/leftmost pick would just rebuild a sorted list as a degenerate chain.',
  complexity: 'Time O(n) · Space O(log n) recursion (O(n) for the output tree)',
  input: '-10, -3, 0, 5, 9', hint: 'sorted values, strictly ascending',
  code: [
    'def sortedArrayToBST(nums):',
    '    def helper(lo, hi):',
    '        if lo > hi:',
    '            return None',
    '        mid = (lo + hi) // 2',
    '        node = Node(nums[mid])',
    '        node.left = helper(lo, mid - 1)',
    '        node.right = helper(mid + 1, hi)',
    '        return node',
    '    return helper(0, len(nums) - 1)',
  ],
  parse(s) {
    const nums = avNums(s, 15, 'values');
    for (let i = 1; i < nums.length; i++) if (nums[i] <= nums[i - 1]) throw new Error('Values must be sorted, strictly ascending');
    return { nums };
  },
  run({ nums }) {
    const { F, snap } = avRecorder();
    const nodes = [];
    const S = (extra = {}) => ({ nums, nodes, ...extra });
    function helper(lo, hi) {
      if (lo > hi) { snap(2, `Range [${lo}, ${hi}] is empty — return None.`, S({ lo, hi, cur: null })); return -1; }
      const mid = (lo + hi) >> 1;
      snap(4, `Range [${lo}, ${hi}]: mid index ${mid} → value ${nums[mid]}.`, S({ lo, hi, mid, cur: null }));
      const id = nodes.length;
      nodes.push({ val: nums[mid], left: -1, right: -1 });
      snap(5, `Create node ${nums[mid]}.`, S({ lo, hi, mid, cur: id }));
      nodes[id].left = helper(lo, mid - 1);
      nodes[id].right = helper(mid + 1, hi);
      return id;
    }
    const root = helper(0, nums.length - 1);
    snap(9, 'Tree complete — height-balanced by construction.', S({ lo: 0, hi: nums.length - 1, cur: root }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 46; },
  draw(ctx, c, f, P) {
    if (f.nodes.length) {
      const lay = avLayoutBinary(f.nodes);
      avDrawBinary(ctx, P, c, f.nodes, lay, id => ({ fill: id === f.cur ? P.alpha('accent', .35) : null, stroke: id === f.cur ? P.accent : null }));
    } else {
      D.text(ctx, '(empty so far)', c.w / 2, 70, { color: P.faint, size: 13, align: 'center' });
    }
    const win = f.nums.map((v, i) => i === f.mid ? `[${v}]` : (i >= f.lo && i <= f.hi ? String(v) : '·')).join(', ');
    D.text(ctx, `nums = [${win}]`, 20, c.h - 16, { color: P.dim, size: 12, mono: true });
  },
});

/* ==================================================== 004 · delete node == */
defineAlgo('11_binary_search_tree', {
  title: 'Delete Node in a BST', short: 'Delete Node',
  idea: 'Find the node by descending like a search. To remove it: a leaf or single-child node is spliced out directly by returning its one side; a node with <b>two</b> children copies up its in-order successor (the minimum of the right subtree) and then deletes that successor instead — which is now guaranteed to be a simple case.',
  complexity: 'Time O(h) · Space O(h)',
  input: '5, 3, 6, 2, 4, null, 7 ; 3', hint: 'tree ; value to delete',
  code: [
    'def deleteNode(root, key):',
    '    if root is None: return None',
    '    if key < root.val:',
    '        root.left = deleteNode(root.left, key)',
    '    elif key > root.val:',
    '        root.right = deleteNode(root.right, key)',
    '    else:',
    '        if root.left is None: return root.right',
    '        if root.right is None: return root.left',
    '        succ = root.right',
    '        while succ.left: succ = succ.left',
    '        root.val = succ.val',
    '        root.right = deleteNode(root.right, succ.val)',
    '    return root',
  ],
  parse(s) {
    const [a, kStr] = avParts(s);
    const nodes = avTreeFromLevel(a);
    const key = avNum(kStr, 'a value to delete');
    if (!nodes.some(n => n.val === key)) throw new Error(`${key} is not in the tree`);
    return { nodes, key };
  },
  run({ nodes, key }) {
    const { F, snap } = avRecorder();
    const S = (cur, extra = {}) => ({ nodes, cur, ...extra });
    function del(id) {
      if (id === -1) { snap(1, 'Empty subtree — nothing to do.', S(null)); return -1; }
      if (key < nodes[id].val) {
        snap(2, `${key} < ${nodes[id].val}: go left.`, S(id));
        nodes[id].left = del(nodes[id].left);
      } else if (key > nodes[id].val) {
        snap(4, `${key} > ${nodes[id].val}: go right.`, S(id));
        nodes[id].right = del(nodes[id].right);
      } else {
        snap(6, `Found ${key}.`, S(id, { found: id }));
        if (nodes[id].left === -1) { snap(7, 'No left child: splice out, promote the right child.', S(id, { found: id })); return nodes[id].right; }
        if (nodes[id].right === -1) { snap(8, 'No right child: splice out, promote the left child.', S(id, { found: id })); return nodes[id].left; }
        let succ = nodes[id].right; const succPath = [succ];
        snap(9, 'Two children: find the in-order successor — leftmost node of the right subtree.', S(id, { found: id, succPath: [...succPath] }));
        while (nodes[succ].left !== -1) { succ = nodes[succ].left; succPath.push(succ); snap(10, `Keep going left: ${nodes[succ].val}.`, S(id, { found: id, succPath: [...succPath] })); }
        snap(11, `Successor is ${nodes[succ].val}: copy its value up to ${nodes[id].val}'s spot.`, S(id, { found: id, succ, succPath }));
        nodes[id].val = nodes[succ].val;
        snap(12, `Now delete ${nodes[succ].val} from the right subtree (it's now a simple case).`, S(id));
        nodes[id].right = del(nodes[id].right);
      }
      return id;
    }
    const newRoot = del(0);
    snap(13, 'Done.', S(newRoot, { root: newRoot }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes, last.root ?? 0); return 60 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    const root = f.root ?? 0;
    const lay = avLayoutBinary(f.nodes, root);
    const succSet = new Set(f.succPath || []);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.succ ? P.alpha('ok', .35) : id === f.found ? P.alpha('err', .3) : id === f.cur ? P.alpha('accent', .3) : succSet.has(id) ? P.alpha('accent', .12) : null,
      stroke: id === f.succ ? P.ok : id === f.found ? P.err : id === f.cur ? P.accent : succSet.has(id) ? P.accent : null,
    }));
  },
});

/* ======================================================== 005 · LCA (BST) == */
defineAlgo('11_binary_search_tree', {
  title: 'Lowest Common Ancestor of a Binary Search Tree', short: 'LCA (BST)',
  idea: 'The BST ordering makes the split point fully determined by comparisons alone: whichever node sits between p and q in value — one on each side, or one of them IS the node — is the LCA. No need to search both subtrees like a general tree would.',
  complexity: 'Time O(h) · Space O(1)',
  input: '6, 2, 8, 0, 4, 7, 9, null, null, 3, 5 ; 0 ; 4', hint: 'tree ; value p ; value q',
  code: [
    'def lowestCommonAncestor(root, p, q):',
    '    node = root',
    '    while node:',
    '        if p.val < node.val and q.val < node.val:',
    '            node = node.left',
    '        elif p.val > node.val and q.val > node.val:',
    '            node = node.right',
    '        else:',
    '            return node',
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
    const S = (cur, extra = {}) => ({ nodes, p, q, cur, ...extra });
    let id = 0; const path = [];
    snap(1, `Start at the root (${nodes[0].val}).`, S(0, { path: [0] }));
    for (;;) {
      path.push(id);
      if (p < nodes[id].val && q < nodes[id].val) { snap(4, `${p} and ${q} are both < ${nodes[id].val}: go left.`, S(id, { path: [...path] })); id = nodes[id].left; }
      else if (p > nodes[id].val && q > nodes[id].val) { snap(6, `${p} and ${q} are both > ${nodes[id].val}: go right.`, S(id, { path: [...path] })); id = nodes[id].right; }
      else { snap(8, `${nodes[id].val} splits p and q (or is one of them) — this is the LCA.`, S(id, { path: [...path], lca: id })); break; }
    }
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes), onPath = new Set(f.path || []);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.lca ? P.alpha('ok', .4) : id === f.cur ? P.alpha('accent', .3) : onPath.has(id) ? P.alpha('accent', .12) : null,
      stroke: id === f.lca ? P.ok : id === f.cur ? P.accent : onPath.has(id) ? P.accent : null,
      sub: f.nodes[id].val === f.p ? 'p' : f.nodes[id].val === f.q ? 'q' : null,
    }));
  },
});

/* ================================================ 006 · validate BST == */
defineAlgo('11_binary_search_tree', {
  title: 'Validate Binary Search Tree', short: 'Validate BST',
  idea: 'An in-order traversal of a valid BST visits values in strictly increasing order. So: do an in-order walk with an explicit stack, and the moment a value is not strictly greater than the one visited just before it, the tree is invalid.',
  complexity: 'Time O(n) · Space O(h)',
  input: '5, 1, 4, null, null, 3, 6', hint: 'level order, null for missing children',
  code: [
    'def isValidBST(root):',
    '    stack, node, prev = [], root, None',
    '    while stack or node:',
    '        while node:',
    '            stack.append(node); node = node.left',
    '        node = stack.pop()',
    '        if prev is not None and node.val <= prev:',
    '            return False',
    '        prev = node.val',
    '        node = node.right',
    '    return True',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const S = (cur, extra = {}) => ({ nodes, cur, ...extra });
    const stack = []; let node = 0, prev = null;
    while (stack.length || node !== -1) {
      while (node !== -1) { stack.push(node); snap(4, `Push ${nodes[node].val}, descend left.`, S(node, { stack: [...stack], prevVal: prev })); node = nodes[node].left; }
      node = stack.pop();
      snap(5, `Pop ${nodes[node].val}.`, S(node, { stack: [...stack], prevVal: prev }));
      if (prev !== null && nodes[node].val <= prev) {
        snap(7, `${nodes[node].val} ≤ previous value ${prev}: order is broken — invalid.`, S(node, { stack: [...stack], bad: node, prevVal: prev }));
        return F;
      }
      snap(9, `${nodes[node].val} > ${prev === null ? '(nothing yet)' : prev}: order holds so far.`, S(node, { stack: [...stack], prevVal: prev }));
      prev = nodes[node].val;
      node = nodes[node].right;
    }
    snap(10, 'Stack and node both empty: every value increased — valid.', S(null, { valid: true, prevVal: prev }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 46; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.bad ? P.alpha('err', .35) : id === f.cur ? P.alpha('accent', .3) : null,
      stroke: id === f.bad ? P.err : id === f.cur ? P.accent : null,
    }));
    D.text(ctx, `stack: [${(f.stack || []).map(id => f.nodes[id].val).join(', ')}]  prev: ${f.prevVal ?? '—'}`, 20, c.h - 16, { color: P.dim, size: 12, mono: true });
  },
});

/* ============================================ 007 · kth smallest == */
defineAlgo('11_binary_search_tree', {
  title: 'Kth Smallest Element in a BST', short: 'Kth Smallest',
  idea: 'In-order traversal visits BST values in ascending order, so the k-th value visited is the k-th smallest — no need to visit the rest of the tree once the counter hits k.',
  complexity: 'Time O(h + k) · Space O(h)',
  input: '5, 3, 6, 2, 4, null, null, 1 ; 3', hint: 'tree ; k',
  code: [
    'def kthSmallest(root, k):',
    '    stack, node, count = [], root, 0',
    '    while stack or node:',
    '        while node:',
    '            stack.append(node); node = node.left',
    '        node = stack.pop()',
    '        count += 1',
    '        if count == k:',
    '            return node.val',
    '        node = node.right',
  ],
  parse(s) {
    const [a, kStr] = avParts(s);
    const nodes = avTreeFromLevel(a);
    const k = avNum(kStr, 'k');
    if (k < 1 || k > nodes.length) throw new Error(`k must be between 1 and ${nodes.length}`);
    return { nodes, k };
  },
  run({ nodes, k }) {
    const { F, snap } = avRecorder();
    const S = (cur, extra = {}) => ({ nodes, cur, k, ...extra });
    const stack = []; let node = 0, count = 0;
    while (stack.length || node !== -1) {
      while (node !== -1) { stack.push(node); snap(4, `Push ${nodes[node].val}, descend left.`, S(node, { stack: [...stack], count })); node = nodes[node].left; }
      node = stack.pop();
      count++;
      const ord = count === 1 ? '1st' : count === 2 ? '2nd' : count === 3 ? '3rd' : `${count}th`;
      snap(6, `Pop ${nodes[node].val} — the ${ord} smallest so far.`, S(node, { stack: [...stack], count }));
      if (count === k) { snap(8, `count == k == ${k}: answer is ${nodes[node].val}.`, S(node, { stack: [...stack], count, found: node })); return F; }
      node = nodes[node].right;
    }
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 46; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.found ? P.alpha('ok', .4) : id === f.cur ? P.alpha('accent', .3) : null,
      stroke: id === f.found ? P.ok : id === f.cur ? P.accent : null,
    }));
    D.text(ctx, `stack: [${(f.stack || []).map(id => f.nodes[id].val).join(', ')}]  count: ${f.count}/${f.k}`, 20, c.h - 16, { color: P.dim, size: 12, mono: true });
  },
});

/* =============================================== 008 · BST iterator == */
defineAlgo('11_binary_search_tree', {
  title: 'Binary Search Tree Iterator', short: 'BST Iterator',
  idea: 'Keep only the <b>left spine</b> on a stack, never the whole in-order list. next() pops the top, then pushes the left spine of its right child — at most O(h) extra memory, and every node is pushed and popped exactly once across the whole iteration.',
  complexity: 'O(h) space · O(1) amortized time per next()',
  input: '7, 3, 15, null, null, 9, 20 ; next, next, hasNext, next, next', hint: 'tree ; comma-separated next/hasNext calls',
  code: [
    'def __init__(self, root):',
    '    self.stack = []',
    '    self._push_left(root)',
    '',
    'def next(self):',
    '    node = self.stack.pop()',
    '    if node.right:',
    '        self._push_left(node.right)',
    '    return node.val',
    '',
    'def hasNext(self):',
    '    return bool(self.stack)',
  ],
  parse(s) {
    const [a, opsStr] = avParts(s);
    const nodes = avTreeFromLevel(a);
    const ops = String(opsStr || '').split(',').map(x => x.trim().toLowerCase()).filter(Boolean);
    if (!ops.length) throw new Error('Enter at least one call: next or hasNext');
    ops.forEach(op => { if (op !== 'next' && op !== 'hasnext') throw new Error(`"${op}" — only next or hasNext`); });
    if (ops.length > 12) throw new Error('Use at most 12 calls');
    return { nodes, ops };
  },
  run({ nodes, ops }) {
    const { F, snap } = avRecorder();
    const stack = []; const out = [];
    const S = (cur, extra = {}) => ({ nodes, cur, stack: [...stack], out: [...out], ...extra });
    function pushLeft(id) { while (id !== -1) { stack.push(id); snap(2, `Push ${nodes[id].val} onto the stack.`, S(id)); id = nodes[id].left; } }
    pushLeft(0);
    ops.forEach(op => {
      if (op === 'hasnext') { snap(10, `hasNext(): stack ${stack.length ? 'is not' : 'is'} empty → ${stack.length > 0}.`, S(null, { call: `hasNext() → ${stack.length > 0}` })); return; }
      const id = stack.pop();
      snap(5, `next(): pop ${nodes[id].val}.`, S(id));
      if (nodes[id].right !== -1) { snap(7, `${nodes[id].val} has a right child — push its left spine.`, S(id)); pushLeft(nodes[id].right); }
      out.push(nodes[id].val);
      snap(8, `Return ${nodes[id].val}.`, S(id, { call: `next() → ${nodes[id].val}` }));
    });
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 60; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes), inStack = new Set(f.stack || []);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.cur ? P.alpha('accent', .35) : inStack.has(id) ? P.alpha('accent', .12) : null,
      stroke: id === f.cur ? P.accent : inStack.has(id) ? P.accent : null,
    }));
    D.text(ctx, `stack (top→bottom): [${[...f.stack].reverse().map(id => f.nodes[id].val).join(', ')}]`, 20, c.h - 34, { color: P.dim, size: 12, mono: true });
    D.text(ctx, f.call ? f.call : `returned so far: [${f.out.join(', ')}]`, 20, c.h - 14, { color: P.ok, size: 12.5, mono: true, weight: 700 });
  },
});

/* =============================================== 009 · recover BST == */
defineAlgo('11_binary_search_tree', {
  title: 'Recover Binary Search Tree', short: 'Recover BST',
  idea: 'Exactly two nodes were swapped. An in-order scan of a valid BST is strictly increasing, so scan in-order and watch for a value that is not greater than the one before it — each such "dip" implicates the earlier of the pair (only the first time) and the later of the pair (every time it happens). Swap those two values back.',
  complexity: 'Time O(n) · Space O(h)',
  input: '3, 1, 4, null, null, 2', hint: 'level order — exactly two values are swapped',
  code: [
    'def recoverTree(root):',
    '    first = second = prev = None',
    '    stack, node = [], root',
    '    while stack or node:',
    '        while node:',
    '            stack.append(node); node = node.left',
    '        node = stack.pop()',
    '        if prev and prev.val > node.val:',
    '            if first is None: first = prev',
    '            second = node',
    '        prev = node',
    '        node = node.right',
    '    first.val, second.val = second.val, first.val',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    let first = null, second = null, prev = null;
    const stack = []; let node = 0;
    const S = (cur, extra = {}) => ({ nodes, cur, first, second, ...extra });
    while (stack.length || node !== -1) {
      while (node !== -1) { stack.push(node); snap(5, `Push ${nodes[node].val}, descend left.`, S(node)); node = nodes[node].left; }
      node = stack.pop();
      snap(6, `Visit ${nodes[node].val}.`, S(node, { prevVal: prev === null ? null : nodes[prev].val }));
      if (prev !== null && nodes[prev].val > nodes[node].val) {
        if (first === null) { first = prev; snap(8, `Dip: ${nodes[prev].val} > ${nodes[node].val}. First swapped node is ${nodes[prev].val}.`, S(node, { first, prevVal: nodes[prev].val })); }
        second = node;
        snap(9, `Second swapped node (so far) is ${nodes[node].val}.`, S(node, { first, second, prevVal: nodes[prev].val }));
      }
      prev = node;
      node = nodes[node].right;
    }
    snap(11, `Swap the values back: ${nodes[first].val} ↔ ${nodes[second].val}.`, S(null, { swap: true }));
    const tmp = nodes[first].val; nodes[first].val = nodes[second].val; nodes[second].val = tmp;
    snap(11, 'Recovered — a valid BST again.', S(null));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.first || id === f.second ? P.alpha('err', .3) : id === f.cur ? P.alpha('accent', .3) : null,
      stroke: id === f.first || id === f.second ? P.err : id === f.cur ? P.accent : null,
      sub: id === f.first ? '1st' : id === f.second ? '2nd' : null,
    }));
  },
});

/* ============================================ 010 · inorder successor == */
defineAlgo('11_binary_search_tree', {
  title: 'Inorder Successor in BST', short: 'Inorder Successor',
  idea: 'Descend from the root comparing against p\'s value: every time we go left (because p is smaller than the current node), the node being left behind is a candidate for "smallest value greater than p" — keep only the LAST such candidate. One pass, no special-casing on whether p has a right child.',
  complexity: 'Time O(h) · Space O(1)',
  input: '5, 3, 6, 2, 4 ; 3', hint: 'tree ; value p (find its successor)',
  code: [
    'def inorderSuccessor(root, p):',
    '    candidate = None',
    '    node = root',
    '    while node:',
    '        if p.val < node.val:',
    '            candidate = node',
    '            node = node.left',
    '        else:',
    '            node = node.right',
    '    return candidate',
  ],
  parse(s) {
    const [a, pStr] = avParts(s);
    const nodes = avTreeFromLevel(a);
    const p = avNum(pStr, 'value p');
    if (!nodes.some(n => n.val === p)) throw new Error(`${p} is not in the tree`);
    return { nodes, p };
  },
  run({ nodes, p }) {
    const { F, snap } = avRecorder();
    let candidate = null, node = 0;
    const S = (cur, extra = {}) => ({ nodes, cur, p, candidate, ...extra });
    snap(2, 'candidate = None.', S(0));
    while (node !== -1) {
      if (p < nodes[node].val) {
        candidate = node;
        snap(5, `${p} < ${nodes[node].val}: new candidate. Go left.`, S(node, { candidate }));
        node = nodes[node].left;
      } else {
        snap(7, `${p} ≥ ${nodes[node].val}: successor must be further right. Go right.`, S(node, { candidate }));
        node = nodes[node].right;
      }
    }
    snap(8, candidate === null ? 'Node is empty — p is the maximum value, it has no successor.' : `Node is empty — return the last candidate: ${nodes[candidate].val}.`, S(null, { candidate, done: true }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 30; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: f.done && id === f.candidate ? P.alpha('ok', .4) : id === f.candidate ? P.alpha('accent', .18) : id === f.cur ? P.alpha('accent', .3) : null,
      stroke: f.done && id === f.candidate ? P.ok : id === f.candidate ? P.accent : id === f.cur ? P.accent : null,
      sub: f.nodes[id].val === f.p ? 'p' : null,
    }));
  },
});

/* ======================================= 011 · minimum absolute diff == */
defineAlgo('11_binary_search_tree', {
  title: 'Minimum Absolute Difference in BST', short: 'Min Abs Diff',
  idea: 'In-order traversal visits BST values in sorted order, so the minimum absolute difference between ANY two nodes must occur between two IN-ORDER-ADJACENT values — track only the previous value and the running minimum gap, never all pairs.',
  complexity: 'Time O(n) · Space O(h)',
  input: '4, 2, 6, 1, 3', hint: 'level order, null for missing children',
  code: [
    'def getMinimumDifference(root):',
    '    stack, node, prev, best = [], root, None, inf',
    '    while stack or node:',
    '        while node:',
    '            stack.append(node); node = node.left',
    '        node = stack.pop()',
    '        if prev is not None:',
    '            best = min(best, node.val - prev)',
    '        prev = node.val',
    '        node = node.right',
    '    return best',
  ],
  parse(s) { return { nodes: avTreeFromLevel(s) }; },
  run({ nodes }) {
    const { F, snap } = avRecorder();
    const stack = []; let node = 0, prev = null, best = Infinity;
    const S = (cur, extra = {}) => ({ nodes, cur, prev, best: best === Infinity ? null : best, ...extra });
    while (stack.length || node !== -1) {
      while (node !== -1) { stack.push(node); snap(4, `Push ${nodes[node].val}, descend left.`, S(node)); node = nodes[node].left; }
      node = stack.pop();
      snap(5, `Visit ${nodes[node].val}.`, S(node));
      if (prev !== null) {
        const diff = nodes[node].val - prev;
        const improved = diff < best;
        if (improved) best = diff;
        snap(7, `Gap since ${prev}: ${diff}${improved ? ' — new minimum!' : ` (minimum stays ${best})`}.`, S(node, { improved }));
      }
      prev = nodes[node].val;
      node = nodes[node].right;
    }
    snap(10, `Done — minimum absolute difference is ${best}.`, S(null, { done: true }));
    return F;
  },
  height: (w, last) => { const lay = avLayoutBinary(last.nodes); return 60 + lay.depth * 58 + 46; },
  draw(ctx, c, f, P) {
    const lay = avLayoutBinary(f.nodes);
    avDrawBinary(ctx, P, c, f.nodes, lay, id => ({
      fill: id === f.cur ? (f.improved ? P.alpha('ok', .35) : P.alpha('accent', .3)) : null,
      stroke: id === f.cur ? (f.improved ? P.ok : P.accent) : null,
    }));
    D.text(ctx, `prev: ${f.prev ?? '—'}   best gap so far: ${f.best ?? '—'}`, 20, c.h - 16, { color: P.dim, size: 12, mono: true });
  },
});
