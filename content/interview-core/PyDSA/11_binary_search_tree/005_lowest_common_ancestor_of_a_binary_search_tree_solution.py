"""
================================================================================
SOLUTION · LeetCode 235 · Lowest Common Ancestor of a BST            [Medium]
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/
================================================================================

THE CORE IDEA
--------------
The LCA is the SPLIT POINT: the first node, walking down from the root, where
p and q stop agreeing about which way to turn.

    node = root
    while node:
        if p.val < node.val and q.val < node.val:
            node = node.left            # both smaller -> both in the left subtree
        elif p.val > node.val and q.val > node.val:
            node = node.right           # both bigger  -> both in the right subtree
        else:
            return node                 # they split here (or one IS this node)

O(h) time, O(1) space. Three comparisons per level, one path, no backtracking.

Why the split point is provably the LOWEST common ancestor: while both values
are on the same side, that side's root is a strictly lower common ancestor,
so the current node cannot be the answer. The moment they disagree — one goes
left, the other right — no node below can contain both, because the two
subtrees are disjoint. So the split node is a common ancestor and no
descendant of it is: that is the definition of "lowest". The `else` also
absorbs the "one of them IS this node" case, which is correct precisely
because the problem's definition allows a node to be its own descendant.

Note what this code never does: it never looks for p or q. It never compares
node identity. It reads only two integers and `node.val`.


================================================================================
SIDE BY SIDE WITH LC 236 (GENERAL BINARY TREE) — THE POINT OF THIS PROBLEM
================================================================================
LC 236 is the same question on a plain binary tree, and it is a completely
different algorithm because the ordering is gone:

    # LC 236 — general binary tree, O(n) time, O(h) space
    def lca_general(root, p, q):
        if root is None or root is p or root is q:
            return root
        left = lca_general(root.left, p, q)
        right = lca_general(root.right, p, q)
        if left and right:      # p and q found in DIFFERENT subtrees -> split
            return root
        return left or right     # both on one side (or neither) -> pass it up

    ┌──────────────────────┬───────────────────────┬────────────────────────┐
    │                       │ LC 235 (BST)          │ LC 236 (plain tree)    │
    ├──────────────────────┼───────────────────────┼────────────────────────┤
    │ how it finds a side   │ ONE comparison        │ must search both       │
    │ traversal             │ single descent        │ full post-order        │
    │ time                  │ O(h)                  │ O(n) — always          │
    │ space                 │ O(1) iterative        │ O(h) call stack        │
    │ visits                │ <= h nodes            │ EVERY node             │
    │ needs p/q identity?   │ no, only their values │ yes, `is` comparisons  │
    │ can prune a subtree?  │ YES — that's the BST  │ never                  │
    └──────────────────────┴───────────────────────┴────────────────────────┘

Both find the split point. The difference is that a BST lets you find it by
comparison on the way DOWN, while a plain tree can only discover it by
reporting findings back UP from the leaves. This is the single clearest
illustration in the whole curriculum of what the BST invariant actually buys,
and the demo below measures it: on a balanced BST of 100,000 nodes the BST
version visits about 17 nodes and the general version visits all 100,000.

If an interviewer gives you 235 and you answer with 236's algorithm, the code
is correct and the answer is wrong — you were being asked to notice the
ordering.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it and drop it): collect the root-to-p path
and the root-to-q path as lists, then walk both from the front and return
the last node they share. O(h) time but O(h) space, and two passes. It is
actually the natural answer when nodes have PARENT pointers and you have no
root (LC 1650), so it is worth knowing — but here it is strictly worse.

Approach 1 (recursive descent):

    def lca(root, p, q):
        if p.val < root.val and q.val < root.val:
            return self.lca(root.left, p, q)
        if p.val > root.val and q.val > root.val:
            return self.lca(root.right, p, q)
        return root

Clean and tail-recursive, O(h) stack. At the problem's 10^5-node limit a
degenerate BST would exceed CPython's recursion limit, so it is not the
version to ship.

Approach 2 (iterative, one loop) ✅ — the answer, above. O(1) space.

Approach 3 (normalise first): `lo, hi = sorted((p.val, q.val))` and then the
loop reads `if hi < node.val` / `elif lo > node.val`. Two comparisons per
level instead of four, and it removes any chance of getting the two-sided
conditions inconsistent. Slightly faster and arguably clearer; measured in
the demo below (the difference is small but real).


================================================================================
STEP BY STEP TRACE
================================================================================
tree = [6,2,8,0,4,7,9,null,null,3,5]

                    6
              ╱          ╲
            2              8
          ╱   ╲          ╱   ╲
        0      4       7      9
              ╱ ╲
             3   5

p = 2, q = 8:
    node=6:  2 < 6 but 8 > 6  ->  they SPLIT here -> return 6 ✅
    (one comparison; the answer is the root and we never descend at all)

p = 3, q = 5:
    node=6:  3 < 6 and 5 < 6   -> both left  -> node = 2
    node=2:  3 > 2 and 5 > 2   -> both right -> node = 4
    node=4:  3 < 4 but 5 > 4   -> SPLIT      -> return 4 ✅

p = 2, q = 4:
    node=6:  2 < 6 and 4 < 6   -> both left  -> node = 2
    node=2:  p.val == 2 == node.val -> neither "both <" nor "both >" holds
             -> falls into the else -> return 2 ✅
    This is the "a node is a descendant of itself" case, handled with no
    special-case code at all.

p = 0, q = 9:
    node=6:  0 < 6, 9 > 6 -> SPLIT -> return 6 ✅


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time    Space   Mutates input?  Note
    -----------------------------  ------  ------  --------------  -------------
    Two root-to-node paths, compare O(h)    O(h)    no              2 passes;
                                                                     the right
                                                                     answer for
                                                                     LC 1650
    LC 236's post-order (general)  O(n)    O(h)    no              correct but
                                                                     ignores the BST
    Recursive descent               O(h)    O(h)    no              stack ceiling
                                                                     at h = 10^5
    Iterative descent ✅             O(h)    O(1)    no              the answer
    Iterative, values pre-sorted    O(h)    O(1)    no              2 comparisons
                                                                     per level

    Nothing here mutates the tree — the whole problem is read-only, which is
    what makes the O(1)-space claim easy to defend.


================================================================================
EDGE CASES
================================================================================
    p is an ancestor of q       -> the answer is p itself. Handled by the
                                   `else` branch, not by a special case. This
                                   is the case most people forget to test.
    q is an ancestor of p       -> symmetric; the code is symmetric in p and q,
                                   so no extra branch.
    p and q are the two children of the same node -> the classic split, one
                                   comparison at that node.
    LCA is the root              -> the loop returns on its first iteration.
    p and q are the deepest two   -> a full-height descent, the worst case.
    p.val > q.val (arguments in   -> must still work; the conditions test both
    "wrong" order)                 values independently, so order is irrelevant.
                                   Approach 3 sorts them explicitly to make
                                   that obvious.
    two-node tree [2,1]          -> the minimum legal input (n >= 2).
    degenerate chain              -> h == n; O(n) descent, and the recursive
                                   variant raises RecursionError at 10^5.
    p or q not in the tree        -> excluded by the constraints. This code
                                   would return the node where the two
                                   nonexistent paths diverge, silently. If the
                                   guarantee is removed you must verify both
                                   exist (see the follow-ups).


================================================================================
COMMON MISTAKES
================================================================================
1. Answering with LC 236's post-order algorithm. Correct output, O(n) instead
   of O(h), and it demonstrates you did not notice the input was sorted. The
   most common way to lose points on this problem.

2. Forgetting the "a node can be its own descendant" case and writing an
   explicit `if node is p or node is q: return node` guard BEFORE the
   comparisons. Harmless but unnecessary — and if you write it with `==`
   instead of `is`, or write it AFTER the comparisons, you get a wrong answer
   for `p = 2, q = 4` (it descends past 2 and returns 4).

3. Using `<=` instead of `<` in the descent. With `p.val <= node.val` the
   case "p IS this node" is treated as "go left", and the walk descends past
   the true LCA.

4. Comparing NODES instead of values (`if p < node`). Python has no default
   ordering for a custom class, so this raises TypeError: '<' not supported
   between instances of 'TreeNode' and 'TreeNode'.

5. Only checking one of the two values (`if p.val < node.val: go left`).
   Both must be on the same side to justify descending.

6. Returning a value instead of a NODE. LeetCode compares node identity here.

7. Building a parent map or storing paths (Approach 0) when the split-point
   descent needs neither. It works; it just throws away the O(1) space.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Now do it on a plain binary tree (LC 236).
A: The post-order algorithm shown above: recurse both sides, and the node
   where the two searches report success on OPPOSITE sides is the LCA. O(n),
   because without ordering you cannot rule out a subtree. This file
   implements both and cross-checks them on thousands of random trees.

Q: What if p or q might NOT be in the tree?
A: The descent alone cannot tell — it returns the split point of two paths
   that may lead nowhere. Verify membership first with two O(h) searches
   (problem 001), or make the descent confirm it found both. LC 1644 is the
   general-tree version of this same caveat.

Q: Each node has a `parent` pointer and you are not given the root.
A: LC 1650. Walk up from p collecting ancestors into a set, then walk up
   from q and return the first node already in the set — O(h) time, O(h)
   space. Or the O(1)-space trick: measure both depths, lift the deeper
   pointer to match, then step both up together.

Q: Many LCA queries on the same static tree.
A: Preprocess. Binary lifting gives O(n log n) build and O(log n) per query;
   Euler tour + sparse-table RMQ gives O(n log n) build and O(1) per query;
   Tarjan's offline LCA with union-find handles a known query batch in
   near-linear total time. Naming binary lifting is usually enough.

Q: LCA of a whole SET of nodes, not just two?
A: In a BST, the LCA of a set is the split point for its MIN and MAX — run
   this exact algorithm on those two, and every other member is between them
   and therefore below that node. A one-line reduction, and a nice thing to
   spot out loud.

Q: What is the LCA's distance to p and q (i.e. the path length between them)?
A: depth(p) + depth(q) - 2*depth(LCA). Each depth is another O(h) descent.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 1 of the topic guide's taxonomy: O(h) descent by comparison.

    LC 236  LCA of a Binary Tree            — the same question, no ordering:
                                                O(n) post-order (topic 10)
    LC 1650 LCA III (parent pointers)        — no root available
    LC 1644 LCA II (nodes may not exist)     — the membership caveat above
    LC 700  Search in a BST                  — the descent, one target (001)
    LC 270  Closest BST Value                — descent tracking the best-so-far
    LC 938  Range Sum of BST                 — descent that prunes on a RANGE,
                                                the two-sided version of this
    LC 285  Inorder Successor in BST          — descent remembering the last
                                                left turn
    LC 653  Two Sum IV - Input is a BST       — two values again, different
                                                question
================================================================================
"""

import random
import sys
import time
from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def lowestCommonAncestor(self, root: 'TreeNode', p: 'TreeNode',
                             q: 'TreeNode') -> 'TreeNode':
        """✅ THE ANSWER — iterative split-point descent. O(h) time, O(1) space."""
        node = root
        while node:
            if p.val < node.val and q.val < node.val:
                node = node.left
            elif p.val > node.val and q.val > node.val:
                node = node.right
            else:
                return node          # split point, or one of them IS this node
        return None                   # unreachable given the constraints

    def lca_sorted_bounds(self, root: 'TreeNode', p: 'TreeNode',
                          q: 'TreeNode') -> 'TreeNode':
        """Same descent, values normalised first: two comparisons per level
        instead of four, and the p/q argument order becomes visibly irrelevant."""
        lo, hi = (p.val, q.val) if p.val <= q.val else (q.val, p.val)
        node = root
        while node:
            if hi < node.val:
                node = node.left
            elif lo > node.val:
                node = node.right
            else:
                return node
        return None

    def lca_recursive(self, root: 'TreeNode', p: 'TreeNode',
                      q: 'TreeNode') -> 'TreeNode':
        """Recursive descent. O(h) stack — at the stated 10^5-node limit a
        degenerate BST raises RecursionError."""
        if p.val < root.val and q.val < root.val:
            return self.lca_recursive(root.left, p, q)
        if p.val > root.val and q.val > root.val:
            return self.lca_recursive(root.right, p, q)
        return root

    # ------------------------------------------------------------------
    # LC 236's algorithm — the plain-binary-tree version, for contrast.
    # ------------------------------------------------------------------
    def lca_general_tree(self, root: Optional[TreeNode], p: 'TreeNode',
                         q: 'TreeNode') -> Optional[TreeNode]:
        """LC 236: correct on ANY binary tree, and therefore also on a BST —
        but O(n), because with no ordering no subtree can be ruled out.
        Compares node IDENTITY (`is`), not values."""
        if root is None or root is p or root is q:
            return root
        left = self.lca_general_tree(root.left, p, q)
        right = self.lca_general_tree(root.right, p, q)
        if left and right:
            return root               # p and q split here
        return left or right           # both on one side, or neither

    def lca_broken_le(self, root: 'TreeNode', p: 'TreeNode',
                      q: 'TreeNode') -> 'TreeNode':
        """✗ BROKEN ON PURPOSE — mistake #3: `<=` instead of `<`. Treats "one
        of them IS this node" as "descend left", walking straight past the
        real LCA."""
        node = root
        while node:
            if p.val <= node.val and q.val <= node.val:
                node = node.left
            elif p.val >= node.val and q.val >= node.val:
                node = node.right
            else:
                return node
        return None


# ==============================================================================
# TEST HELPERS — shared with topic 10 (plain binary trees), verbatim
# ==============================================================================
def build(values):
    """LeetCode level-order list (with `None` holes) -> root TreeNode."""
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
    return root


def to_level_order(root):
    """Inverse of build(): level-order list with `None` for absent children,
    trailing `None`s trimmed."""
    if root is None:
        return []
    out, queue = [], deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def find_node(root, val):
    """LeetCode passes p and q as NODE objects; the tests need to look them up."""
    node = root
    while node:
        if node.val == val:
            return node
        node = node.left if val < node.val else node.right
    return None


def bst_insert_iterative(root, val):
    node = TreeNode(val)
    if root is None:
        return node
    curr = root
    while True:
        if val < curr.val:
            if curr.left is None:
                curr.left = node
                return root
            curr = curr.left
        else:
            if curr.right is None:
                curr.right = node
                return root
            curr = curr.right


def balanced_bst(lo, hi):
    """Build a perfectly balanced BST over range(lo, hi) — problem 002."""
    if lo >= hi:
        return None
    mid = (lo + hi) // 2
    node = TreeNode(mid)
    node.left = balanced_bst(lo, mid)
    node.right = balanced_bst(mid + 1, hi)
    return node


def height_iterative(root):
    if root is None:
        return 0
    best, stack = 0, [(root, 1)]
    while stack:
        node, d = stack.pop()
        best = max(best, d)
        if node.left:
            stack.append((node.left, d + 1))
        if node.right:
            stack.append((node.right, d + 1))
    return best


def count_nodes(root):
    n, stack = 0, [root] if root else []
    while stack:
        node = stack.pop()
        n += 1
        if node.left:
            stack.append(node.left)
        if node.right:
            stack.append(node.right)
    return n


# --- instrumented counters: nodes VISITED by each algorithm -------------------
def visited_bst_lca(root, p, q):
    n, node = 0, root
    while node:
        n += 1
        if p.val < node.val and q.val < node.val:
            node = node.left
        elif p.val > node.val and q.val > node.val:
            node = node.right
        else:
            return n
    return n


def visited_general_lca(root, p, q):
    """Node-visit count for LC 236's post-order, run iteratively so it does
    not blow the stack on the large trees in the demo."""
    count = 0
    result = {}
    stack = [(root, False)]
    while stack:
        node, processed = stack.pop()
        if node is None:
            continue
        if not processed:
            count += 1
            if node is p or node is q:
                result[id(node)] = node
                continue
            stack.append((node, True))
            stack.append((node.left, False))
            stack.append((node.right, False))
        else:
            left = result.get(id(node.left))
            right = result.get(id(node.right))
            if left and right:
                result[id(node)] = node
            else:
                result[id(node)] = left or right
    return count


def naive_lca_by_paths(root, pv, qv):
    """Oracle: collect both root-to-node paths, return the last shared node."""
    def path(val):
        out, node = [], root
        while node:
            out.append(node)
            if node.val == val:
                return out
            node = node.left if val < node.val else node.right
        return out

    a, b = path(pv), path(qv)
    best = None
    for x, y in zip(a, b):
        if x is y:
            best = x
        else:
            break
    return best


# ==============================================================================
# TESTS — run:  python 005_lowest_common_ancestor_of_a_binary_search_tree_solution.py
# ==============================================================================
TREE = [6, 2, 8, 0, 4, 7, 9, None, None, 3, 5]
CASES = [
    (TREE, 2, 8, 6),
    (TREE, 2, 4, 2),      # p is an ancestor of q
    (TREE, 4, 2, 2),      # same, arguments swapped
    (TREE, 3, 5, 4),
    (TREE, 0, 5, 2),
    (TREE, 7, 9, 8),
    (TREE, 0, 9, 6),      # the whole span -> the root
    (TREE, 3, 4, 4),      # q is an ancestor of p
    (TREE, 0, 3, 2),
    ([2, 1], 2, 1, 2),
    ([2, 1, 3], 1, 3, 2),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: iterative split-point descent ---")
    for values, pv, qv, want in CASES:
        root = build(values)
        got = sol.lowestCommonAncestor(root, find_node(root, pv),
                                       find_node(root, qv))
        ok = got is not None and got.val == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  p={pv:<3} q={qv:<3} -> "
              f"{got.val if got else None:<4} (want {want})")

    print("\n--- all four implementations agree (identity-compared) ---")
    for values, pv, qv, want in CASES:
        root = build(values)
        p, q = find_node(root, pv), find_node(root, qv)
        a = sol.lowestCommonAncestor(root, p, q)
        b = sol.lca_sorted_bounds(root, p, q)
        c = sol.lca_recursive(root, p, q)
        d = sol.lca_general_tree(root, p, q)      # LC 236's algorithm
        e = naive_lca_by_paths(root, pv, qv)      # the two-paths oracle
        ok = a is b is c is d is e and a.val == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  p={pv:<3} q={qv:<3} -> {a.val:<4} "
              f"(descent == sorted == recursive == LC236 == path-oracle)")

    # ----------------------------------------------------------------------
    # Trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: three shapes of query on the example tree ---")
    for pv, qv, label in ((2, 8, "split at the root"),
                          (3, 5, "split two levels down"),
                          (2, 4, "p IS the ancestor (self-descendant rule)")):
        root = build(TREE)
        p, q = find_node(root, pv), find_node(root, qv)
        node = root
        print(f"  p={pv}, q={qv}  ({label})")
        while node:
            if p.val < node.val and q.val < node.val:
                print(f"    at {node.val}: both {pv},{qv} < {node.val} "
                      f"-> descend LEFT (a lower ancestor exists)")
                node = node.left
            elif p.val > node.val and q.val > node.val:
                print(f"    at {node.val}: both {pv},{qv} > {node.val} "
                      f"-> descend RIGHT (a lower ancestor exists)")
                node = node.right
            else:
                print(f"    at {node.val}: they no longer agree -> "
                      f"LCA = {node.val}")
                break

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO: mistake #3 — `<=` swallows the self-descendant case.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: mistake #3, `<=` instead of `<` ---")
    broke = False
    for pv, qv in ((2, 4), (4, 3), (8, 9)):
        root = build(TREE)
        p, q = find_node(root, pv), find_node(root, qv)
        good = sol.lowestCommonAncestor(root, p, q)
        bad = sol.lca_broken_le(root, p, q)
        print(f"  p={pv}, q={qv}:  correct -> {good.val:<3} "
              f"`<=` version -> {bad.val if bad else None}")
        if bad is not good:
            broke = True
    print("  With `<=`, 'p IS this node' counts as 'both are on the left', so")
    print("  the walk descends PAST the answer. It only misbehaves when one of")
    print("  the two nodes is an ancestor of the other — which is exactly the")
    print("  case the problem statement calls out in its own Example 2.")
    all_ok &= broke

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 1: nodes VISITED, BST descent vs LC 236's post-order.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 1: nodes VISITED — O(h) BST descent vs O(n) LC 236 ---")
    print("  Two query shapes per tree: the two EXTREMES (which split at the")
    print("  root, the best case) and two ADJACENT deep values (worst case).")
    print(f"  {'n':>8} {'height':>7} {'query':>10} {'BST 235':>9} "
          f"{'general 236':>12} {'ratio':>9}")
    ratios_ok = True
    for n in (1_000, 10_000, 100_000):
        root = balanced_bst(0, n)
        h = height_iterative(root)
        for pv, qv, label in ((0, n - 1, "extremes"), (1, 2, "adjacent")):
            p, q = find_node(root, pv), find_node(root, qv)
            bst_v = visited_bst_lca(root, p, q)
            gen_v = visited_general_lca(root, p, q)
            print(f"  {n:>8} {h:>7} {label:>10} {bst_v:>9} {gen_v:>12} "
                  f"{gen_v / bst_v:>8.0f}x")
            ratios_ok &= (bst_v <= h and gen_v > 0.99 * n)
    print("  The BST descent visits 1 node in the best case and at most `height`")
    print("  in the worst — and `height` barely moves as n grows 100x (10 -> 17).")
    print("  LC 236 touches essentially every node on EVERY query, best case or")
    print("  worst, because nothing tells it which subtree to skip. (It reads")
    print("  n-1 rather than n only because it stops descending at p and q.)")
    all_ok &= ratios_ok

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 2: the same gap in wall-clock time.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 2: wall clock, same trees, same answers ---")
    print(f"  {'n':>8} {'235 us':>10} {'236 us':>11} {'speedup':>9}")
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(300_000)             # LC 236's recursion is O(h) deep
    try:
        for n in (1_000, 10_000, 100_000):
            root = balanced_bst(0, n)
            p, q = find_node(root, 1), find_node(root, n - 2)
            reps = 200 if n <= 10_000 else 20
            t0 = time.perf_counter()
            for _ in range(reps):
                sol.lowestCommonAncestor(root, p, q)
            t1 = time.perf_counter()
            for _ in range(reps):
                sol.lca_general_tree(root, p, q)
            t2 = time.perf_counter()
            us_a = (t1 - t0) / reps * 1e6
            us_b = (t2 - t1) / reps * 1e6
            print(f"  {n:>8} {us_a:>9.2f}  {us_b:>10.1f}  {us_b / us_a:>8.0f}x")
    finally:
        sys.setrecursionlimit(old_limit)       # restore, per the house rules
    print(f"  (recursion limit temporarily raised to 300000 for LC 236, then")
    print(f"  restored to {sys.getrecursionlimit()} — a balanced 100k-node tree")
    print("  is ~17 deep, but LC 236's version recurses to the FULL height on")
    print("  both sides of every node, and CPython counts every frame.)")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 3: the sorted-bounds micro-optimisation, measured.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 3: 4 comparisons per level vs 2 (pre-sorted bounds) ---")
    root = balanced_bst(0, 100_000)
    p, q = find_node(root, 3), find_node(root, 99_997)
    reps = 20_000
    t0 = time.perf_counter()
    for _ in range(reps):
        sol.lowestCommonAncestor(root, p, q)
    t1 = time.perf_counter()
    for _ in range(reps):
        sol.lca_sorted_bounds(root, p, q)
    t2 = time.perf_counter()
    a_us, b_us = (t1 - t0) / reps * 1e6, (t2 - t1) / reps * 1e6
    print(f"  four-comparison version:  {a_us:.3f} us/call")
    print(f"  pre-sorted two-comparison: {b_us:.3f} us/call")
    print(f"  ratio: {a_us / b_us:.2f}x  (same O(h); this is a constant factor)")
    print("  Small, and honest: both are O(h). Worth mentioning as a clarity")
    print("  win — sorting p/q once makes the argument order visibly irrelevant.")

    # ----------------------------------------------------------------------
    # Randomised cross-check: BST descent vs LC 236 on random shapes.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs LC 236 and the path oracle ---")
    random.seed(235)
    mismatches, trials = 0, 4000
    for _ in range(trials):
        vals = random.sample(range(-200, 200), random.randint(2, 30))
        root = None
        for v in vals:
            root = bst_insert_iterative(root, v)
        pv, qv = random.sample(vals, 2)
        p, q = find_node(root, pv), find_node(root, qv)
        a = sol.lowestCommonAncestor(root, p, q)
        b = sol.lca_sorted_bounds(root, p, q)
        c = sol.lca_general_tree(root, p, q)
        d = naive_lca_by_paths(root, pv, qv)
        if not (a is b is c is d):
            mismatches += 1
    print(f"  {trials} random BSTs x 4 implementations: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 4: recursion ceiling on a legal degenerate tree.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 4: a legal chain breaks the recursive descent ---")
    chain = None
    for v in range(4_000):
        chain = bst_insert_iterative(chain, v)
    p, q = find_node(chain, 3_998), find_node(chain, 3_999)
    print(f"  chain of {count_nodes(chain)} nodes, height "
          f"{height_iterative(chain)}, limit {sys.getrecursionlimit()}")
    it = sol.lowestCommonAncestor(chain, p, q)
    it_ok = it is not None and it.val == 3_998
    print(f"  iterative descent: LCA = {it.val} -> {it_ok}")
    raised = False
    try:
        sol.lca_recursive(chain, p, q)
        print("  recursive descent: did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  recursive descent: RecursionError -> {e!r}")
    print(f"  iterative succeeded where recursive failed: {it_ok and raised}")
    print("  The constraints allow 10^5 nodes, so this is inside the problem.")
    all_ok &= it_ok and raised

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
