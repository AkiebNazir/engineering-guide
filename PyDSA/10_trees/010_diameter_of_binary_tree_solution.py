"""
================================================================================
SOLUTION · LeetCode 543 · Diameter of Binary Tree                       [Easy]
https://leetcode.com/problems/diameter-of-binary-tree/
================================================================================

THE CORE IDEA
--------------
Any path in a tree has exactly one highest point — the node where it stops
climbing and starts descending (possibly the same as one endpoint, if the
path only goes one direction). So:

    every path has exactly ONE "turning point"
    => the longest path overall is the best path TURNING at SOME node
    => for each node, compute the longest path that turns THERE, and take
       the max over all n nodes

At a node, "the longest path turning here" is just the height of its left
subtree plus the height of its right subtree — walk all the way down the
left side, turn, walk all the way down the right side. That requires
knowing every node's height, computed bottom-up (postorder):

    def height(node):                 # returns height, in EDGES down from
        if node is None:              # this node to its deepest leaf.
            return -1                 # height(None) = -1 so a LEAF gets
        l = height(node.left)         # 1 + max(-1, -1) = 0, matching "a
        r = height(node.right)        # leaf has 0 edges below it".
        best = max(best, l + r + 2)   # RECORD: the path THROUGH this node
        return 1 + max(l, r)          # RETURN: height, for the PARENT

    best = 0; height(root); return best

This is the topic guide's Part 5 idiom, in its bare form (no clamping,
because a height is never negative — see the units discussion below for why
that is the one thing that makes this Easy where problem 018, the same
shape with values instead of heights, is Hard).

    RECORDED (the diameter candidate):  left_height + right_height (+2, with
        the height(None) = -1 convention below) — uses BOTH children, is a
        complete path, and can never be extended by a parent: joining it
        upward would give the node three path-neighbours, which is a fork.

    RETURNED (the height):  1 + max(left_height, right_height) — uses ONE
        child at most, a path with a loose end at this node, exactly what
        the parent needs to compute ITS OWN height and candidate.

O(n) time, O(h) space. Every node is visited once; nothing is recomputed.


================================================================================
UNITS: EDGES, NOT NODES — get this exactly right before writing code
================================================================================
The problem is explicit: "the length of a path... is represented by the
number of EDGES". A tree of k nodes on a straight line has k-1 edges. A
single node has 0 edges below it and IS its own path of length 0.

There are two equally valid conventions for `height(None)`, and mixing them
is the single most common bug in this problem:

    (a) height(None) = -1, height(leaf) = 0     <- used above; "edges below"
    (b) height(None) =  0, height(leaf) = 1     <- "nodes on the path down"

Both give the SAME diameter if you are consistent, because the diameter
formula changes to match:

    (a)  diam_at_node = height(left) + height(right) + 2
                         (each side contributes height+1 edges to reach the
                          node, unless that side is None, in which case
                          height(None)+1 = -1+1 = 0 — the "+1" cancels the
                          "-1" automatically, so no branching is needed)

    (b)  diam_at_node = height(left) + height(right)
                         (each side's height ALREADY counts the edge down
                          to it from the current node — a None child
                          contributes height 0, correctly adding nothing)

Convention (b) is the one used in almost every published writeup (and in
problem 018's sibling for max path sum) because the formula has no "+2" to
forget, so it is the one this solution leads with in the code below. Both
are implemented and cross-checked in the tests — see `diameterOfBinaryTree`
(convention b) and `diameterOfBinaryTree_conv_a` (convention a).


================================================================================
MULTIPLE APPROACHES
================================================================================
0. NAIVE — compute height with an independent O(n) `height()` call at every
   single node, take `height(left) + height(right)` there, and recurse.
   Each of the n nodes triggers a full height computation over its own
   subtree, so total work is O(n) heights each costing up to O(n) ->
   O(n^2) worst case (a left-skewed chain, exactly the shape problem 009's
   naive approach — `PyDSA/10_trees/009_balanced_binary_tree_solution.py`
   — is also O(n^2) for). Coded below, and used as the correctness ORACLE
   because it shares no logic with the postorder version.

1. POSTORDER + `nonlocal` BEST ✅ — the version above. O(n) time, O(h)
   space. The answer; what to write first in an interview.

2. MUTABLE SINGLE-ELEMENT BOX — same algorithm, `best = [0]` instead of
   `nonlocal best`; mutate `best[0]` instead of rebinding the name. No
   keyword needed because mutating a box's CONTENTS isn't a rebind. Coded
   below (`diameterOfBinaryTree_box`).

3. TUPLE RETURN — `height(node)` returns `(height, best_diameter_in_subtree)`
   and the caller combines them; no closure or mutable state at all. Coded
   below (`diameterOfBinaryTree_tuple`).

All three of 1-3 are O(n) time, O(h) space, and produce identical answers —
they differ only in HOW the "second answer" (the running best) is carried,
which is exactly what topic guide Part 5 is about.


================================================================================
STEP BY STEP TRACE — root = [1,2,3,4,None,None,5,6]  (answer 5)
================================================================================
              1
            ┌─┴─┐
            2   3
           ╱      ╲
          4         5
         ╱
        6

    Convention (b): height(None) = 0, height(leaf) = 1, diam = hL + hR.

    node   height(left)  height(right)  RECORD diam=hL+hR   RETURN height
                                                              = 1+max(hL,hR)
    -----  ------------  -------------  -------------------  ---------------
    6      0 (None)      0 (None)       0+0 = 0               1
    4      1 (node 6)    0 (None)       1+0 = 1               2
    2      2 (node 4)    0 (None)       2+0 = 2               3
    5      0             0              0                     1
    3      0 (None)      1 (node 5)     0+1 = 1               2
    1      3 (node 2)    2 (node 3)     3+2 = 5  ***           4

    best = max(0, 1, 2, 0, 1, 5) = 5      <- the turning point is the root

    The winning path is 6 -> 4 -> 2 -> 1 -> 3 -> 5: 5 edges across 6 nodes.
    Note node 2's own RECORD (2) and RETURN (3) are different numbers, and
    the root uses the RETURNED 3 (not the recorded 2) to compute its own
    candidate — exactly the return-vs-record split the topic guide names.

    A case where the winner is NOT at the root — root = [1,2,3,4,5], answer 3:

              1
            ┌─┴─┐
            2   3
          ┌─┴─┐
          4   5

    node   height(left)  height(right)  RECORD diam        RETURN height
    -----  ------------  -------------  ------------------  -------------
    4      0             0              0                    1
    5      0             0              0                    1
    2      1             1              1+1 = 2  ***          2
    3      0             0              0                     1
    1      2             1              2+1 = 3               3

    best = max(0, 0, 2, 0, 3) = 3. Here the root DOES win (3 > 2), but only
    just — change the tree slightly (see EDGE CASES) and it stops winning,
    which is why "assume the root wins" is Common Mistake 4 below.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                            Time    Space (aux)  Mutates input?  Note
    ----------------------------------  ------  -----------  --------------  -------------------
    Naive: height() called per node     O(n^2)  O(h)         no              the test oracle
    Postorder + nonlocal best ✅        O(n)    O(h)         no              the answer
    Postorder + mutable box             O(n)    O(h)         no              no `nonlocal` needed
    Postorder returning a tuple         O(n)    O(h)         no              no mutable state,
                                                                               one tuple per node

    n = nodes, h = height. Nothing mutates the tree. The naive approach's
    O(n^2) worst case is a left- or right-skewed chain: computing height()
    at the top node walks the whole remaining chain, then again one node
    shorter at the next node down, and so on — a triangular sum, O(n^2).


================================================================================
EDGE CASES
================================================================================
    single node                 -> [1] -> 0. No edges exist at all; confirms
                                    height(None)=0 (or -1) is the base case,
                                    not the leaf case.
    two nodes                   -> [1,2] -> 1. The one edge is the whole
                                    tree's diameter.
    perfectly balanced tree      -> [1,2,3,4,5,6,7] -> 4 (the path from any
                                    leaf, through the root, to a leaf on the
                                    other side: e.g. 4-2-1-3-6, 4 edges).
    skewed / linear chain         -> a chain of n nodes has diameter n-1 (the
                                    whole chain is the longest path, and
                                    every node's own diam-candidate is small
                                    compared to the return height it passes
                                    up).
    diameter NOT through the root -> [1,2,3,4,None,None,5,6] -> 5, winning
                                    node is node 2's neighbourhood, not the
                                    root's own candidate (root's own is only
                                    3+2=5... see trace above, this ONE
                                    happens to tie at the root; use the
                                    two-heavy-subtrees case below for a
                                    clean non-root win).
    diameter strictly off-root    -> a tree where one whole side is a deep
                                    chain hanging off a leaf of a shallow
                                    side: the winning pair of subtrees both
                                    live under one child of the root, so the
                                    root's own hL+hR loses. Demonstrated
                                    live in the tests.
    negative-ish values           -> irrelevant here: diameter depends only
                                    on SHAPE, never on `node.val`. (Contrast
                                    problem 018, where values are central.)


================================================================================
COMMON MISTAKES
================================================================================
1. Confusing edges and nodes: reporting `hL + hR + 2` under convention (b),
   or `hL + hR` under convention (a) — one off-by-two, the other off by the
   number of nodes on the path. Pick ONE convention for `height(None)` and
   keep the matching diameter formula; the trace above shows convention (b)
   throughout.

2. RETURNING the diameter candidate (`hL + hR`) instead of the height
   (`1 + max(hL, hR)`) up to the parent. Demonstrated live below: this
   corrupts every ancestor's own height, which corrupts every ancestor's
   own candidate — the exact same failure family as problem 018's mistake 1
   (returning the "through" value instead of the "gain"), just without
   negative-value clamping to obscure it.

3. Forgetting `nonlocal best` (or the box/tuple alternative) — assigning to
   `best` inside the nested function without it raises `UnboundLocalError`
   on the FIRST recursive call, because Python decides `best` is local for
   the WHOLE function body the moment it sees any assignment to it anywhere
   inside. See topic guide §5.1.

4. Assuming the answer must pass through the root, and therefore computing
   only `height(root.left) + height(root.right)`. Wrong whenever the
   longest path lives entirely under one child — demonstrated live below.

5. Recomputing height from scratch at every node with an independent
   `height()` helper (the naive O(n^2) approach) and not recognising that
   the postorder walk you're already doing to find candidates ALSO computes
   every height for free, in the same pass, if you just return it.

6. For an iterative rewrite: forgetting that height, like the diameter
   candidate, must be computed POSTORDER (children finished before the
   parent) — visiting the current node before its children have reported
   back gives an incomplete height and an incomplete candidate.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the tree is n-ary (each node can have any number of children),
   not binary?
A: LC 1522, Diameter of N-Ary Tree. Same idea, but a node can have more
   than two children, so you can't just take "left height + right height" —
   track the TOP TWO child heights seen so far while iterating a node's
   children, and use their sum as that node's candidate.

Q: What if edges have weights?
A: The recurrence is identical; height becomes "the maximum weighted
   downward path", accumulating edge weight instead of `1 +`. The
   turning-point argument (every path has one highest point) doesn't
   depend on unit edge weights at all.

Q: How does this relate to LC 124 (Binary Tree Maximum Path Sum)?
A: Structurally identical — this problem, with `node.val` replaced by an
   implicit "1" (an edge always contributes exactly 1 regardless of the
   node) and no clamping needed because heights can't be negative. LC 124
   adds real, possibly-negative values, which forces `max(gain, 0)`
   clamping on each side — that clamp is the entire reason 124 is Hard and
   this is Easy. See problem 018's solution file for the full writeup.

Q: Can you find the actual path, not just its length?
A: Record the turning node alongside `best`, then from that node walk down
   each side always following whichever child has the larger height,
   stopping when height hits 0 (leaf reached, or that side was empty).

Q: Do it without recursion.
A: Explicit postorder with a stack, memoising each node's height in a dict
   as its children finish (same shape as problem 018's iterative postorder)
   — necessary once the tree could be a long chain (n up to 10^4 here,
   right at Python's default recursion-limit boundary).


================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
  BOTTOM-UP POSTORDER AGGREGATE — return a value up, keep a running best:
    LC 543   Diameter of Binary Tree             — this problem
    LC 124   Binary Tree Maximum Path Sum        — same shape + clamping,
                                                    values instead of heights (018)
    LC 110   Balanced Binary Tree                — postorder height, early
                                                    bailout instead of a running
                                                    max (009)
    LC 687   Longest Univalue Path               — same shape, equality guard
    LC 1522  Diameter of N-Ary Tree              — 543 with k children: keep
                                                    the TOP TWO child heights

  See `PyDSA/10_trees/_TOPIC_GUIDE.md` Part 5 for the closure/`nonlocal`
  idiom this whole family shares, spelled out in full generality.
================================================================================
"""

import random
import sys
import time
from collections import deque
from typing import Dict, List, Optional, Tuple


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def diameterOfBinaryTree(self, root: Optional[TreeNode]) -> int:
        """Postorder aggregate, convention (b): height(None) = 0,
        height(leaf) = 1, diameter-at-node = height(left) + height(right).
        RETURN the height up to the parent; RECORD the diameter candidate
        in a nonlocal best. O(n) time, O(h) space. See THE CORE IDEA above."""
        best = 0

        def height(node: Optional[TreeNode]) -> int:
            nonlocal best
            if node is None:
                return 0
            l = height(node.left)
            r = height(node.right)
            best = max(best, l + r)            # RECORD: path THROUGH this node
            return 1 + max(l, r)                # RETURN: height, for the PARENT

        height(root)
        return best

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def diameterOfBinaryTree_conv_a(self, root: Optional[TreeNode]) -> int:
        """Same algorithm, convention (a): height(None) = -1,
        height(leaf) = 0, diameter-at-node = hL + hR + 2. Kept to prove the
        two conventions agree — see UNITS above."""
        best = 0

        def height(node: Optional[TreeNode]) -> int:
            nonlocal best
            if node is None:
                return -1
            l = height(node.left)
            r = height(node.right)
            best = max(best, l + r + 2)
            return 1 + max(l, r)

        height(root)
        return best

    def diameterOfBinaryTree_box(self, root: Optional[TreeNode]) -> int:
        """Approach 2: a mutable one-element box instead of `nonlocal` —
        mutating best[0]'s CONTENTS needs no keyword, only rebinding a
        NAME would."""
        best = [0]

        def height(node: Optional[TreeNode]) -> int:
            if node is None:
                return 0
            l = height(node.left)
            r = height(node.right)
            best[0] = max(best[0], l + r)
            return 1 + max(l, r)

        height(root)
        return best[0]

    def diameterOfBinaryTree_tuple(self, root: Optional[TreeNode]) -> int:
        """Approach 3: return (height, best_diameter_here). No closures, no
        mutable state — the two quantities are two slots of the return
        value, which makes them impossible to conflate by accident."""

        def go(node: Optional[TreeNode]) -> Tuple[int, int]:
            if node is None:
                return (0, 0)
            lh, ld = go(node.left)
            rh, rd = go(node.right)
            return (1 + max(lh, rh), max(ld, rd, lh + rh))

        return go(root)[1]

    def diameterOfBinaryTree_iterative(self, root: Optional[TreeNode]) -> int:
        """Explicit postorder with a stack, heights memoised in a dict as
        each node's children finish. O(n) time, O(n) space, immune to the
        recursion limit — n can be up to 10^4, right at the default
        recursion-limit boundary for a chain-shaped tree."""
        if root is None:
            return 0
        best = 0
        heights: Dict[int, int] = {}
        stack = [(root, False)]
        while stack:
            node, children_done = stack.pop()
            if not children_done:
                stack.append((node, True))
                if node.right is not None:
                    stack.append((node.right, False))
                if node.left is not None:
                    stack.append((node.left, False))
                continue
            l = heights.get(id(node.left), 0) if node.left else 0
            r = heights.get(id(node.right), 0) if node.right else 0
            best = max(best, l + r)
            heights[id(node)] = 1 + max(l, r)
        return best

    def diameterOfBinaryTree_naive(self, root: Optional[TreeNode]) -> int:
        """Approach 0: recompute height from scratch (a fresh O(n) helper)
        at every node. O(n^2) worst case on a skewed tree — same shape as
        problem 009's naive approach. Used below as the test oracle: it
        shares no logic with the postorder version."""

        def height(node: Optional[TreeNode]) -> int:
            if node is None:
                return 0
            return 1 + max(height(node.left), height(node.right))

        def diameter(node: Optional[TreeNode]) -> int:
            if node is None:
                return 0
            through = height(node.left) + height(node.right)
            return max(through, diameter(node.left), diameter(node.right))

        return diameter(root)

    # ------------------------------------------------------------------
    # Deliberate breakage — the named traps.
    # ------------------------------------------------------------------
    def diameterOfBinaryTree_broken_return_diam(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE (mistake 2) — RETURNS the diameter candidate
        (l + r) up to the parent instead of the height. Corrupts every
        ancestor's own height and therefore its own candidate."""
        best = 0

        def height(node):
            nonlocal best
            if node is None:
                return 0
            l = height(node.left)
            r = height(node.right)
            best = max(best, l + r)
            return l + r                  # <- should be 1 + max(l, r): WRONG

        height(root)
        return best

    def diameterOfBinaryTree_broken_root_only(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE (mistake 4) — only ever considers a path
        through the ROOT, never checking any other node."""

        def height(node):
            if node is None:
                return 0
            return 1 + max(height(node.left), height(node.right))

        if root is None:
            return 0
        return height(root.left) + height(root.right)


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build(vals: List[Optional[int]]) -> Optional[TreeNode]:
    """Level-order list with `None` for absent children -> root node."""
    if not vals or vals[0] is None:
        return None
    root = TreeNode(vals[0])
    queue = deque([root])
    i = 1
    while queue and i < len(vals):
        node = queue.popleft()
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
    return root


def to_level_order(root: Optional[TreeNode]) -> List[Optional[int]]:
    """Root -> level-order list with `None`s, trailing `None`s trimmed."""
    if root is None:
        return []
    out: List[Optional[int]] = []
    queue = deque([root])
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


def random_tree(n: int, rng: random.Random) -> Optional[TreeNode]:
    """Random binary tree of n nodes."""
    if n == 0:
        return None
    root = TreeNode(0)
    nodes = [root]
    for i in range(1, n):
        while True:
            parent = rng.choice(nodes)
            if parent.left is None and (parent.right is None or rng.random() < 0.5):
                parent.left = TreeNode(i)
                nodes.append(parent.left)
                break
            if parent.right is None:
                parent.right = TreeNode(i)
                nodes.append(parent.right)
                break
    return root


def left_chain(n: int) -> Optional[TreeNode]:
    if n == 0:
        return None
    root = TreeNode(0)
    cur = root
    for i in range(1, n):
        cur.left = TreeNode(i)
        cur = cur.left
    return root


# ==============================================================================
# TESTS — run:  python 010_diameter_of_binary_tree_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 3, 4, 5], 3),
    ([1, 2], 1),
    ([1], 0),
    ([1, 2, 3], 2),
    ([1, 2, 3, 4, None, None, 5, 6], 5),
    ([1, 2, None, 3, None, 4, None, 5], 4),
    ([1, 2, 3, 4, 5, 6, 7], 4),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: four implementations agree ---")
    impls = [
        ("postorder + nonlocal (b)", sol.diameterOfBinaryTree),
        ("postorder + nonlocal (a)", sol.diameterOfBinaryTree_conv_a),
        ("postorder + box         ", sol.diameterOfBinaryTree_box),
        ("postorder + tuple       ", sol.diameterOfBinaryTree_tuple),
        ("iterative postorder     ", sol.diameterOfBinaryTree_iterative),
        ("naive O(n^2)            ", sol.diameterOfBinaryTree_naive),
    ]
    for name, fn in impls:
        ok = all(fn(build(vals)) == expected for vals, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- per-case output ---")
    for vals, expected in CASES:
        got = sol.diameterOfBinaryTree(build(vals))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<40} -> {got:>3}  "
              f"(want {expected})")

    # ----------------------------------------------------------------------
    # The central table: height vs diameter-candidate, per node.
    # ----------------------------------------------------------------------
    print("\n--- the two quantities, per node: root = [1,2,3,4,None,None,5,6] ---")
    root = build([1, 2, 3, 4, None, None, 5, 6])
    print(f"  {'val':>4} {'height(L)':>10} {'height(R)':>10} "
          f"{'RECORD diam':>12} {'RETURN height':>14}  note")
    rows = []

    def table(node):
        if node is None:
            return 0
        l = table(node.left)
        r = table(node.right)
        diam = l + r
        h = 1 + max(l, r)
        rows.append((node.val, l, r, diam, h))
        return h

    table(root)
    best = max(r[3] for r in rows)
    for val, l, r, diam, h in rows:
        note = "<- the answer" if diam == best else ""
        print(f"  {val:>4} {l:>10} {r:>10} {diam:>12} {h:>14}  {note}")
    print(f"  best = max of the RECORD column = {best}")
    all_ok &= (best == 5)
    print("  Node 2's two numbers differ (2 vs 3) — the parent (root) uses")
    print("  the RETURNED 3, not the RECORDED 2, to compute its own diameter.")

    # ----------------------------------------------------------------------
    # ⚠️ Mistake 2: returning the diameter candidate instead of the height.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  returning the diameter candidate instead of the height (mistake 2) ---")
    print(f"  {'tree':<44} {'correct':>8} {'return-diam':>12}")
    div = 0
    for vals, _ in CASES:
        a = sol.diameterOfBinaryTree(build(vals))
        b = sol.diameterOfBinaryTree_broken_return_diam(build(vals))
        div += (a != b)
        print(f"  {str(vals):<44} {a:>8} {b:>12}")
    all_ok &= (div > 0)
    print("  Corrupting the returned height cascades: every ancestor now")
    print("  computes ITS OWN height and candidate from a wrong number.")

    # ----------------------------------------------------------------------
    # ⚠️ Mistake 4: assuming the answer passes through the root.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  assuming the diameter passes through the root (mistake 4) ---")
    # 1 -> 2 -> {3 -> 5, 4 -> 6}: root's own candidate (3) loses to node 2's
    # candidate (4), so root-only under-counts the true diameter.
    off_root = TreeNode(1, left=TreeNode(
        2,
        left=TreeNode(3, left=TreeNode(5)),
        right=TreeNode(4, left=TreeNode(6)),
    ))
    print("  a tree where the longest path lives entirely under the LEFT child:")
    print(f"  level-order: {to_level_order(off_root)}")
    correct = sol.diameterOfBinaryTree(off_root)
    root_only = sol.diameterOfBinaryTree_broken_root_only(off_root)
    print(f"  correct (checks every node) -> {correct}")
    print(f"  root-only ('through root')  -> {root_only}")
    all_ok &= (correct > root_only)
    print(f"  root-only UNDER-counts: {root_only} < {correct}")

    # ----------------------------------------------------------------------
    # Randomised cross-check vs the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    rng = random.Random(543)
    bad = 0
    trials = 3000
    for _ in range(trials):
        t = random_tree(rng.randint(1, 14), rng)
        want = sol.diameterOfBinaryTree_naive(t)
        for _name, fn in impls[:-1]:
            if fn(t) != want:
                bad += 1
    all_ok &= (bad == 0)
    print(f"  {trials} random trees x 5 implementations vs naive O(n^2): "
          f"{bad} mismatches")

    # ----------------------------------------------------------------------
    # Recursion limit: n up to 10^4, a chain is legal.
    # ----------------------------------------------------------------------
    print("\n--- n can be 10^4 and a chain is legal ---")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}")
    chain = left_chain(9_500)
    try:
        r = sol.diameterOfBinaryTree(chain)
        rec_msg, died = f"ok -> {r}", False
    except RecursionError as exc:
        rec_msg, died = f"{type(exc).__name__}", True
    print(f"  recursive postorder (9500-node chain) -> {rec_msg}")
    it = sol.diameterOfBinaryTree_iterative(chain)
    print(f"  iterative postorder                    -> ok -> {it}")
    all_ok &= (it == 9_499)
    if not died:
        all_ok &= (r == it)
    print("  Whether the recursive version survives depends on the exact")
    print("  recursion limit and chain length; the iterative version never")
    print("  depends on it.")

    # ----------------------------------------------------------------------
    # Timing: O(n) postorder vs O(n^2) naive, on a skewed tree.
    # ----------------------------------------------------------------------
    print("\n--- benchmark: O(n) postorder vs O(n^2) naive, on skewed trees ---")
    print(f"  {'nodes':>7} {'O(n) (ms)':>11} {'O(n^2) (ms)':>13} {'ratio':>8}")
    sys.setrecursionlimit(20_000)
    for n in (200, 400, 800, 1600):
        t = left_chain(n)
        t0 = time.perf_counter()
        a = sol.diameterOfBinaryTree(t)
        t1 = time.perf_counter()
        b = sol.diameterOfBinaryTree_naive(t)
        t2 = time.perf_counter()
        all_ok &= (a == b == n - 1)
        fast, slow = (t1 - t0) * 1000, (t2 - t1) * 1000
        ratio = slow / fast if fast > 0 else float("inf")
        print(f"  {n:>7} {fast:>11.3f} {slow:>13.2f} {ratio:>7.0f}x")
    print("  The naive approach recomputes height from the top of the")
    print("  remaining chain at every node — a triangular sum of work,")
    print("  O(n^2) — on a skewed tree specifically; on a balanced tree the")
    print("  gap is much smaller because every subtree is short.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
