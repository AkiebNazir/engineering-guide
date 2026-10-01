"""
================================================================================
SOLUTION · LeetCode 124 · Binary Tree Maximum Path Sum                   [Hard]
https://leetcode.com/problems/binary-tree-maximum-path-sum/
================================================================================

THE CORE IDEA
--------------
A legal path is a "V": it climbs from somewhere, TURNS AROUND at exactly one
node — its highest point — and descends. It cannot fork twice. So:

    every path has exactly ONE turning point
    => maximise over turning points
    => for each node, compute the best path that TURNS THERE, and take the
       max over all n nodes

At a node, that requires knowing the best straight-DOWN path from each child.
Which gives the recursion its shape — and its one genuinely hard idea: the
value you RECORD and the value you RETURN are two different numbers.

    def gain(node):                       # returns the best DOWNWARD sum
        if node is None: return 0
        left  = max(gain(node.left),  0)   # a negative branch is DROPPED
        right = max(gain(node.right), 0)
        best = max(best, node.val + left + right)   # RECORD: path TURNING here
        return node.val + max(left, right)           # RETURN: path CONTINUING up

    best = -inf; gain(root); return best

    RECORDED (the "through" value):  node.val + left + right
        uses BOTH children — a complete V, a candidate for the final answer,
        and it can NEVER be extended upward: a parent joining it would give
        the node three path-neighbours, which is a fork, not a path.

    RETURNED (the "gain"):           node.val + max(left, right)
        uses ONE child at most — a path with a loose end at `node`, which is
        exactly the thing the parent can attach to.

O(n) time, O(h) space. This is the archetype of topic guide Part 3's
"postorder aggregate": a value returned upward, plus a global best recorded
in a `nonlocal`.


================================================================================
⚠️ THE #1 FAILURE: RETURNING THE "THROUGH" VALUE
================================================================================
Change one line — return `node.val + left + right` instead of
`node.val + max(left, right)` — and the function still runs, still returns an
integer, and still passes plenty of tests. What it computes is not a path sum.

            -1
          ┌──┴──┐
          2     3
        ┌─┴─┐
        4    5

    correct answer      : 11   (the path 4 -> 2 -> 5)
    "return through"    : 13

Where does 13 come from? At node 2 the buggy version returns 2 + 4 + 5 = 11
upward. The root then computes -1 + max(0, 11) + max(0, 3) = 13, believing
there is a path worth 13. Written out, that "path" is
4 -> 2 -> 5 ... -> -1 -> 3, which visits node 2 twice and forks at it. It
does not exist. The demo below runs both versions on this tree and prints
both numbers.

Note how PLAUSIBLE the bug is: 13 > 11, so it looks like the correct
algorithm merely found a better path. Nothing about the output says
"impossible". And on many trees the two agree — any tree where no node's
best V is ever extended upward. That is why this specific bug is worth
being able to spot by reading, not by testing.


================================================================================
THE OTHER TWO TRAPS
================================================================================
CLAMPING. `max(gain(child), 0)` is not an optimisation — it is part of the
definition. If a child's best downward path is negative, the best path
through this node simply does not go that way; the "0" means "attach nothing
on that side". Drop the clamp and:

            2
          ┌─┴─┐
         -5    3

    correct       : 5   (the path 2 -> 3; the -5 branch is dropped)
    no clamping   : 0   (it computes 2 + (-5) + 3 = 0 as the through-value
                          and never considers 2 + 0 + 3)

Why does the clamp not break the all-negative case? Because the CLAMP applies
to children, never to the node itself: `node.val + 0 + 0` is still
`node.val`, so a single negative node still records its own (negative) value
as a candidate. The clamp says "a path may decline to use a subtree"; it
never says "a path may be empty".

THE INITIAL VALUE. The problem says "any NON-EMPTY path", and values go down
to -1000, so the answer can be negative. `best = 0` silently asserts that an
empty path (sum 0) is allowed:

    [-3]     correct -3,  best=0 gives 0
    [-2,-1]  correct -1,  best=0 gives 0

Use `float("-inf")`, or `root.val`, or seed it from the first node visited.


================================================================================
MULTIPLE APPROACHES
================================================================================
0. BRUTE FORCE — treat the tree as an undirected graph and enumerate every
   simple path (for each start node, DFS over all paths from it), tracking
   the maximum sum. There are O(n^2) paths in a tree, and enumerating them
   this way costs O(n^2). Correct and completely independent of the real
   algorithm, which makes it the ideal test oracle. Coded below and used as
   such — this is how the tests avoid grading the answer against a
   reimplementation of itself.

1. POSTORDER AGGREGATE WITH A `nonlocal` BEST ✅ — the version above. O(n)
   time, O(h) space. The answer.

2. POSTORDER RETURNING A TUPLE `(gain, best_in_subtree)` — the same
   algorithm with no mutable state: each call returns both numbers and the
   parent combines them. Slightly more verbose, and it allocates a tuple per
   node, but it makes the "two different quantities" fact impossible to
   overlook, since they are literally two slots of the return value. Coded
   below. Worth writing this way the first time you learn the problem, then
   collapsing to the `nonlocal` form.

3. ITERATIVE POSTORDER — explicit stack, memoising each node's gain in a
   dict as its children complete. O(n) time, O(n) space. Necessary in Python
   when the tree may be a deep chain: n can be 3 * 10^4 here and the default
   recursion limit is 1000, so a chain is a legal input that kills the
   recursive versions. Coded and demonstrated below.

All three are O(n); there is no faster answer, because the best path's
turning point could be any node and each node's value must be read at least
once.


================================================================================
STEP BY STEP TRACE — root = [-10,9,20,null,null,15,7]  (answer 42)
================================================================================
           -10
          ┌─┴──┐
          9    20
             ┌─┴─┐
            15    7

    node   gain(left)  gain(right)  clamped L,R  RECORD through      RETURN gain
                                                  = val + L + R       = val + max(L,R)
    -----  ----------  -----------  -----------  ------------------  ----------------
    9      0 (None)    0 (None)     0, 0         9 + 0 + 0  =  9      9 + 0  =  9
    15     0           0            0, 0         15         = 15      15
    7      0           0            0, 0         7          =  7      7
    20     15          7            15, 7        20+15+7    = 42 ***  20 + 15 = 35
    -10    9           35           9, 35        -10+9+35   = 34      -10 + 35 = 25

    best = max(9, 15, 7, 42, 34) = 42          <- the turning point is node 20

    Note the two columns for node 20 disagree: 42 (a V through 20, using both
    children) versus 35 (a straight line down through 15, extendable upward).
    The root uses the 35, not the 42 — and that is exactly the distinction
    the buggy version erases.

    Note also the root's own through-value, 34, loses to 42. The best path
    does not pass through the root. Any solution that only ever considers
    root-to-leaf paths cannot find it.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                            Time    Space (aux)  Mutates input?  Note
    ----------------------------------  ------  -----------  --------------  -------------------
    Brute: enumerate all simple paths   O(n^2)  O(n + h)     no              the test oracle
    Postorder + nonlocal best ✅        O(n)    O(h)         no              the answer
    Postorder returning a tuple         O(n)    O(h)         no              no mutable state,
                                                                               one tuple per node
    Iterative postorder + gain dict     O(n)    O(n)         no              survives a chain of
                                                                               3 * 10^4 nodes

    n = nodes, h = height. Nothing mutates the tree.

    WHY THERE ARE O(n^2) PATHS: a tree has exactly one simple path between
    each pair of nodes, so there are C(n,2) + n = O(n^2) non-empty paths. The
    O(n) algorithm never enumerates them; it groups them by turning point and
    evaluates each group in O(1) from its children's summaries. That grouping
    is the entire asymptotic win, and it is the reusable idea: "classify
    every candidate answer by some node, then compute the best candidate per
    node in O(1) from below."


================================================================================
EDGE CASES
================================================================================
    single node, positive       -> [5] -> 5. Trivial, but confirms the
                                   through-value uses `+0+0`, not `-inf`.
    single node, NEGATIVE        -> [-3] -> -3. Kills `best = 0`.
    all values negative          -> [-2,-1] -> -1. The answer is the single
                                   least-negative node.
    one negative child            -> [2,-5,3] -> 5. Kills "no clamping".
    best path avoids the root     -> [-10,9,20,null,null,15,7] -> 42. Kills
                                   any root-to-leaf-only approach.
    best path IS a single node     -> [-1,-2,-3] -> -1. Both children clamp
                                   to 0 and the node stands alone.
    a straight chain of positives  -> the whole chain; the "V" degenerates to
                                   a line, which is a legal path.
    mixed signs mid-chain          -> e.g. [1,-2,-3,1,3,-2,null,-1] -> 3; the
                                   best path is a single node deep in the
                                   tree, not any long run.
    a 3 * 10^4-node chain           -> legal per the constraints and fatal to
                                   the recursive versions at the default
                                   recursion limit. Demonstrated.
    root = None                    -> excluded (n >= 1). If it happened,
                                   `best` would stay -inf; there is no
                                   meaningful answer for an empty path set.


================================================================================
COMMON MISTAKES
================================================================================
1. RETURNING the through-value (`node.val + left + right`) instead of the
   gain (`node.val + max(left, right)`). The reported number then
   corresponds to a forked "path" that does not exist. THE defining mistake
   of this problem — printed live below on a tree with a negative root.

2. RECORDING the gain instead of the through-value — the mirror image. Then
   you only ever consider straight-line downward paths and never a V, so
   [1,2,3] returns 3 instead of 6.

3. No clamping: using `gain(child)` where `max(gain(child), 0)` is required.
   Forces the path through negative subtrees. [2,-5,3] returns 0 instead of 5.

4. Clamping the wrong thing — applying `max(..., 0)` to the node's own
   through-value or to the final answer. That reintroduces the empty path and
   returns 0 for every all-negative tree.

5. `best = 0` as the initial value. Same effect as mistake 4 by a different
   route. Use `float("-inf")`.

6. Returning `max(gain_left, gain_right, 0) + node.val` and ALSO clamping at
   the call site — harmless duplication, but people then "simplify" by
   removing the wrong one of the two. Keep exactly one clamp, at the point
   where a child's contribution is consumed.

7. Forgetting `nonlocal best` — `best = max(best, ...)` then raises
   `UnboundLocalError`, because assigning to `best` anywhere in the helper
   makes it local for the whole function. See topic 015's mistake 8.

8. Returning `best` from `gain` and reading the recursion's return value as
   the answer. `gain(root)` is the best DOWNWARD path from the root, which is
   a different (and smaller-or-equal) quantity. For [-10,9,20,null,null,15,7]
   it is 25, not 42.

9. Assuming the answer is at least `max(node.val)`. It is exactly that when
   all values are negative, but people invert this into "start best at
   max(node.val)" and then also clamp, which double-counts nothing but
   obscures why -inf is the honest initialiser.

10. Recursing on a chain of 3 * 10^4 nodes. Legal input, RecursionError.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the PATH itself, not just its sum.
A: Record the turning node alongside the best sum, then reconstruct: from
   that node, walk down each side always choosing the child with the larger
   clamped gain, stopping when the best gain is 0 (that side contributes
   nothing). Store each node's gain in a dict on the way up so the
   reconstruction is O(h) rather than a re-run.

Q: Restrict to ROOT-TO-LEAF paths.
A: Much easier and a different pattern: top-down, carry the running sum down
   as a parameter and record at leaves. That is LC 112/113/129 — problems
   011 here and topic 015's family. No clamping, no nonlocal aggregate.

Q: Restrict to paths that go strictly DOWNWARD (any node to any descendant).
A: Then the answer is `max over nodes of gain(node)` with the same clamping
   — you just stop recording the two-sided through-value. This is LC 437's
   shape (count downward paths summing to a target) and it is exactly the
   "record the gain" mistake 2 — which shows that mistake 2 is not nonsense,
   it is the correct answer to a DIFFERENT question.

Q: Maximum path sum where the path must have at least k nodes.
A: The O(1)-per-node summary must grow: return the best downward sum for
   each length 1..k, i.e. a small array per node. O(nk) time.

Q: The same question on a general graph.
A: NP-hard (longest path). The O(n) algorithm depends entirely on tree
   structure: a unique path between any two nodes and exactly one turning
   point. Say this out loud — it is the cleanest way to show you know WHY
   the tree property is doing the work, and it is the boundary between this
   topic and topic 14.

Q: Diameter (LC 543) — same or different?
A: Structurally IDENTICAL, with edge counts instead of values: return the
   height upward, record `left_height + right_height` as the candidate. No
   clamping is needed because heights are never negative, which is precisely
   why 543 is rated Easy and this is rated Hard. That single difference —
   values can be negative — is the whole difficulty gap.

Q: Do it iteratively.
A: Explicit postorder with a `gain` dict (approach 3). Motivate it with the
   recursion limit, not with style.


================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
  BOTTOM-UP POSTORDER AGGREGATE — return a value up, keep a global best:
    LC 124   Binary Tree Maximum Path Sum      — this problem
    LC 543   Diameter of Binary Tree           — same shape, no clamping (010)
    LC 687   Longest Univalue Path             — same shape, equality guard
    LC 1522  Diameter of N-Ary Tree             — 543 with k children: keep the
                                                   TOP TWO child depths
    LC 110   Balanced Binary Tree               — return height, flag a failure (009)
    LC 236   LCA of a Binary Tree               — return the found node up (017)
    LC 508   Most Frequent Subtree Sum           — return the subtree sum up
    LC 1026  Maximum Difference Between Node and Ancestor — needs BOTH directions

  THE ROOT-TO-LEAF (top-down) CONTRAST:
    LC 112   Path Sum                          — carry the target down (011)
    LC 113   Path Sum II                        — 112 plus the path list
    LC 129   Sum Root to Leaf Numbers            — carry the number down
    LC 1448  Count Good Nodes                   — carry the max down (015)

  THE DOWNWARD-ONLY MIDDLE GROUND:
    LC 437   Path Sum III                       — any-node-to-descendant,
                                                   prefix sums in a hashmap
                                                   (topic 04's trick on a tree)

  THE 1-D ANALOGUE — worth knowing you have seen this before:
    LC 53    Maximum Subarray (Kadane)          — "extend or restart" is the
                                                   same max(x, 0) clamp on a
                                                   line instead of a tree
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
    def maxPathSum(self, root: Optional[TreeNode]) -> int:
        """Postorder aggregate: RETURN the one-sided gain, RECORD the
        two-sided through-value in a nonlocal best. O(n) time, O(h) space.
        See THE CORE IDEA above."""
        best = float("-inf")                  # NOT 0 — values may all be negative

        def gain(node: Optional[TreeNode]) -> int:
            nonlocal best
            if node is None:
                return 0
            left = max(gain(node.left), 0)     # a negative branch contributes 0
            right = max(gain(node.right), 0)
            best = max(best, node.val + left + right)    # RECORD: turns here
            return node.val + max(left, right)            # RETURN: continues up

        gain(root)
        return int(best)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def maxPathSum_tuple(self, root: Optional[TreeNode]) -> int:
        """Approach 2: return (gain, best_in_subtree). No mutable state —
        the two quantities are two slots of the return value, which makes
        the distinction impossible to miss."""

        def go(node: Optional[TreeNode]) -> Tuple[int, float]:
            if node is None:
                return (0, float("-inf"))
            lg, lb = go(node.left)
            rg, rb = go(node.right)
            lg = max(lg, 0)
            rg = max(rg, 0)
            through = node.val + lg + rg
            return (node.val + max(lg, rg), max(lb, rb, through))

        return int(go(root)[1])

    def maxPathSum_iterative(self, root: Optional[TreeNode]) -> int:
        """Approach 3: explicit postorder, gains memoised in a dict.
        O(n) time, O(n) space, immune to the recursion limit — which
        matters because n can be 3 * 10^4 and a chain is legal."""
        if root is None:
            return 0
        best = float("-inf")
        gains: Dict[int, int] = {}                 # id(node) -> its gain
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
            left = max(gains.get(id(node.left), 0), 0) if node.left else 0
            right = max(gains.get(id(node.right), 0), 0) if node.right else 0
            best = max(best, node.val + left + right)
            gains[id(node)] = node.val + max(left, right)
        return int(best)

    def maxPathSum_brute(self, root: Optional[TreeNode]) -> int:
        """Approach 0: enumerate EVERY simple path by treating the tree as
        an undirected graph. O(n^2). Fully independent of the real
        algorithm, so it is the honest test oracle."""
        if root is None:
            return 0
        adj: Dict[int, List[TreeNode]] = {}
        nodes: List[TreeNode] = []
        stack = [root]
        while stack:
            node = stack.pop()
            nodes.append(node)
            adj.setdefault(id(node), [])
            for child in (node.left, node.right):
                if child is not None:
                    adj[id(node)].append(child)
                    adj.setdefault(id(child), []).append(node)
                    stack.append(child)

        best = float("-inf")
        for start in nodes:
            # DFS over every simple path beginning at `start`
            walk = [(start, start.val, {id(start)})]
            while walk:
                node, total, seen = walk.pop()
                best = max(best, total)
                for nxt in adj[id(node)]:
                    if id(nxt) not in seen:
                        walk.append((nxt, total + nxt.val, seen | {id(nxt)}))
        return int(best)

    # ------------------------------------------------------------------
    # Deliberate breakage — the three named traps.
    # ------------------------------------------------------------------
    def maxPathSum_broken_return_through(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE (mistake 1) — RETURNS the two-sided
        through-value. Reports sums for forked "paths" that do not exist."""
        best = float("-inf")

        def gain(node):
            nonlocal best
            if node is None:
                return 0
            left = max(gain(node.left), 0)
            right = max(gain(node.right), 0)
            best = max(best, node.val + left + right)
            return node.val + left + right          # <- both children: WRONG
        gain(root)
        return int(best)

    def maxPathSum_broken_record_gain(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE (mistake 2) — RECORDS the one-sided gain, so
        it never considers a V. Answers the DOWNWARD-only question instead."""
        best = float("-inf")

        def gain(node):
            nonlocal best
            if node is None:
                return 0
            left = max(gain(node.left), 0)
            right = max(gain(node.right), 0)
            g = node.val + max(left, right)
            best = max(best, g)                      # <- one side only: WRONG
            return g
        gain(root)
        return int(best)

    def maxPathSum_broken_no_clamp(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE (mistake 3) — no `max(..., 0)`, so the path
        is forced through negative subtrees."""
        best = float("-inf")

        def gain(node):
            nonlocal best
            if node is None:
                return 0
            left = gain(node.left)                    # not clamped
            right = gain(node.right)
            best = max(best, node.val + left + right)
            return node.val + max(left, right)
        gain(root)
        return int(best)

    def maxPathSum_broken_zero_init(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE (mistake 5) — `best = 0` admits the empty
        path, so every all-negative tree answers 0."""
        best = 0

        def gain(node):
            nonlocal best
            if node is None:
                return 0
            left = max(gain(node.left), 0)
            right = max(gain(node.right), 0)
            best = max(best, node.val + left + right)
            return node.val + max(left, right)
        gain(root)
        return int(best)

    def maxPathSum_clamped_return(self, root: Optional[TreeNode]) -> int:
        """NOT broken — clamps the RETURN value as well
        (`max(node.val + max(l, r), 0)`). Kept so the demo can check
        whether the duplicate clamp changes anything, instead of guessing."""
        best = float("-inf")

        def gain(node):
            nonlocal best
            if node is None:
                return 0
            left = max(gain(node.left), 0)
            right = max(gain(node.right), 0)
            best = max(best, node.val + left + right)
            return max(node.val + max(left, right), 0)     # extra clamp
        gain(root)
        return int(best)


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


def random_tree(n: int, rng: random.Random, lo: int = -9, hi: int = 9):
    """Random binary tree of n nodes with values in [lo, hi]."""
    if n == 0:
        return None
    root = TreeNode(rng.randint(lo, hi))
    nodes = [root]
    for _ in range(n - 1):
        v = rng.randint(lo, hi)
        while True:
            parent = rng.choice(nodes)
            if parent.left is None and (parent.right is None or rng.random() < 0.5):
                parent.left = TreeNode(v)
                nodes.append(parent.left)
                break
            if parent.right is None:
                parent.right = TreeNode(v)
                nodes.append(parent.right)
                break
    return root


def left_chain(vals: List[int]) -> Optional[TreeNode]:
    if not vals:
        return None
    root = TreeNode(vals[0])
    cur = root
    for v in vals[1:]:
        cur.left = TreeNode(v)
        cur = cur.left
    return root


# ==============================================================================
# TESTS — run:  python 018_binary_tree_maximum_path_sum_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 3], 6),
    ([-10, 9, 20, None, None, 15, 7], 42),
    ([-3], -3),
    ([5], 5),
    ([2, -1], 2),
    ([-2, -1], -1),
    ([-1, 2, 3, 4, 5], 11),
    ([2, -5, 3], 5),
    ([-1, -2, -3], -1),
    ([1, -2, -3, 1, 3, -2, None, -1], 3),
    ([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1], 48),
    ([1, 2, 3, 4, 5, 6, 7], 18),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: four working implementations agree ---")
    impls = [
        ("postorder + nonlocal ", sol.maxPathSum),
        ("postorder tuple      ", sol.maxPathSum_tuple),
        ("iterative postorder  ", sol.maxPathSum_iterative),
        ("brute: all n^2 paths ", sol.maxPathSum_brute),
    ]
    for name, fn in impls:
        ok = all(fn(build(vals)) == expected for vals, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- per-case output ---")
    for vals, expected in CASES:
        got = sol.maxPathSum(build(vals))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<50} -> {got:>4}  "
              f"(want {expected})")

    # ----------------------------------------------------------------------
    # The central table: gain vs through, per node.
    # ----------------------------------------------------------------------
    print("\n--- the two quantities, per node: root = [-10,9,20,null,null,15,7] ---")
    root = build([-10, 9, 20, None, None, 15, 7])
    print(f"  {'node':>5} {'clamped L':>10} {'clamped R':>10} "
          f"{'RECORD through':>15} {'RETURN gain':>12}  note")
    rows = []

    def table(node):
        if node is None:
            return 0
        left = max(table(node.left), 0)
        right = max(table(node.right), 0)
        through = node.val + left + right
        g = node.val + max(left, right)
        rows.append((node.val, left, right, through, g))
        return g

    table(root)
    best = max(r[3] for r in rows)
    for val, left, right, through, g in rows:
        note = "<- the answer, and NOT what is returned" if through == best else ""
        print(f"  {val:>5} {left:>10} {right:>10} {through:>15} {g:>12}  {note}")
    print(f"  best = max of the RECORD column = {best}")
    all_ok &= (best == 42)
    print("  Node 20's two numbers differ (42 vs 35). The root consumes 35.")
    print("  Node -10's own through-value is 34 — the best path does NOT pass")
    print("  through the root, so no root-to-leaf approach can find it.")

    # ----------------------------------------------------------------------
    # ⚠️ THE #1 FAILURE, on a tree with a negative root.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  returning the THROUGH value instead of the gain (mistake 1) ---")
    trap = [-1, 2, 3, 4, 5]
    print("             -1")
    print("           ┌──┴──┐")
    print("           2     3")
    print("         ┌─┴─┐")
    print("         4    5")
    root = build(trap)
    good = sol.maxPathSum(root)
    bad = sol.maxPathSum_broken_return_through(root)
    oracle = sol.maxPathSum_brute(root)
    print(f"  correct (and confirmed by the O(n^2) path oracle): {good}  "
          f"(oracle {oracle})")
    print(f"  'return through'                                 : {bad}")
    print(f"  the bug reports a LARGER number than any real path: {bad > good}")
    all_ok &= (good == 11 and oracle == 11 and bad == 13)
    print("  Where 13 comes from: node 2 returns 2+4+5 = 11 upward, then the")
    print("  root computes -1 + max(0,11) + max(0,3) = 13. Spelled out, that")
    print("  'path' is 4->2->5 ... ->-1->3: it visits node 2 twice and forks")
    print("  there. It is not a path. The bug's answer is larger, which is why")
    print("  it never looks like a bug.")
    print(f"  {'tree':<44} {'correct':>8} {'return-through':>15}  diverges?")
    div = 0
    for vals, _ in CASES:
        a = sol.maxPathSum(build(vals))
        b = sol.maxPathSum_broken_return_through(build(vals))
        div += (a != b)
        print(f"  {str(vals):<44} {a:>8} {b:>15}  {a != b}")
    print(f"  diverges on {div} of {len(CASES)} cases — so it also AGREES on")
    print(f"  {len(CASES) - div} of them. LeetCode's own Example 1 ([1,2,3]) is one")
    print("  of the agreements.")
    all_ok &= (div > 0)

    print("\n--- ⚠️  recording the GAIN instead of the through value (mistake 2) ---")
    print(f"  {'tree':<44} {'correct':>8} {'record-gain':>12}")
    div2 = 0
    for vals, _ in CASES[:8]:
        a = sol.maxPathSum(build(vals))
        b = sol.maxPathSum_broken_record_gain(build(vals))
        div2 += (a != b)
        print(f"  {str(vals):<44} {a:>8} {b:>12}")
    all_ok &= (div2 > 0)
    print("  This never considers a V, so it answers the DOWNWARD-ONLY question")
    print("  ('best any-node-to-descendant path'). Not nonsense — the correct")
    print("  answer to a different problem, which is what makes it seductive.")

    print("\n--- ⚠️  no clamping (mistake 3) ---")
    print(f"  {'tree':<44} {'correct':>8} {'no-clamp':>9}")
    div3 = 0
    for vals, _ in CASES:
        a = sol.maxPathSum(build(vals))
        b = sol.maxPathSum_broken_no_clamp(build(vals))
        div3 += (a != b)
        if a != b:
            print(f"  {str(vals):<44} {a:>8} {b:>9}")
    all_ok &= (div3 > 0)
    print(f"  diverges on {div3} of {len(CASES)} cases (only the ones shown). The")
    print("  clamp is required exactly when some subtree's best downward sum is")
    print("  negative, so an all-positive tree can never expose it.")

    print("\n--- ⚠️  best initialised to 0 (mistake 5) ---")
    print(f"  {'tree':<24} {'correct':>8} {'best=0':>8}")
    div5 = 0
    for vals in ([-3], [-2, -1], [-1, -2, -3], [2, -5, 3], [1, 2, 3]):
        a = sol.maxPathSum(build(vals))
        b = sol.maxPathSum_broken_zero_init(build(vals))
        div5 += (a != b)
        print(f"  {str(vals):<24} {a:>8} {b:>8}")
    all_ok &= (div5 > 0)
    print("  `best = 0` silently allows the EMPTY path. The problem says")
    print("  'non-empty', and values reach -1000, so use float('-inf').")

    print("\n--- and a NON-bug: clamping the RETURN value too ---")
    print(f"  {'tree':<44} {'one clamp':>10} {'two clamps':>11}  same?")
    same = True
    for vals, _ in CASES:
        a = sol.maxPathSum(build(vals))
        b = sol.maxPathSum_clamped_return(build(vals))
        same &= (a == b)
        print(f"  {str(vals):<44} {a:>10} {b:>11}  {a == b}")
    rng = random.Random(1)
    same_rand = all(sol.maxPathSum(t) == sol.maxPathSum_clamped_return(t)
                    for t in (random_tree(rng.randint(1, 14), rng)
                              for _ in range(2000)))
    all_ok &= same and same_rand
    print(f"  identical on all {len(CASES)} cases and on 2000 random trees: "
          f"{same and same_rand}")
    print("  Returning `max(gain, 0)` is harmless because the PARENT already")
    print("  clamps with max(child, 0) — the two clamps are idempotent. Measured,")
    print("  not assumed. Keep one anyway: two clamps invite deleting the wrong")
    print("  one later (mistake 6).")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n^2) enumeration oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the all-paths oracle ---")
    for label, lo, hi, trials in (("mixed signs   ", -9, 9, 1200),
                                  ("all NEGATIVE  ", -9, -1, 600),
                                  ("all positive  ", 1, 9, 600)):
        rng = random.Random(124)
        bad = 0
        for _ in range(trials):
            t = random_tree(rng.randint(1, 11), rng, lo, hi)
            want = sol.maxPathSum_brute(t)
            for _name, fn in impls[:3]:
                if fn(t) != want:
                    bad += 1
        all_ok &= (bad == 0)
        print(f"  {label} {trials} random trees x 3 implementations: "
              f"{bad} mismatches")
    print("  The oracle enumerates every simple path in the tree as a graph, so")
    print("  it shares no logic with the algorithm under test.")

    print("\n--- how often does each bug get caught by random testing? ---")
    rng = random.Random(7)
    trees = [random_tree(rng.randint(1, 11), rng, -9, 9) for _ in range(2000)]
    print(f"  {'variant':<28} {'wrong on':>10} {'of 2000':>9} {'%':>7}")
    for label, fn in (("return the through value", sol.maxPathSum_broken_return_through),
                      ("record the gain", sol.maxPathSum_broken_record_gain),
                      ("no clamping", sol.maxPathSum_broken_no_clamp),
                      ("best = 0", sol.maxPathSum_broken_zero_init)):
        wrong = sum(1 for t in trees if fn(t) != sol.maxPathSum_brute(t))
        print(f"  {label:<28} {wrong:>10} {2000:>9} {100 * wrong / 2000:>6.1f}%")
    print("  Every one of them is wrong on a large fraction of random trees —")
    print("  they survive only because the HAND-PICKED examples people test with")
    print("  are small, positive, and symmetric.")

    # ----------------------------------------------------------------------
    # Recursion limit: a chain of 3 * 10^4 nodes is a legal input.
    # ----------------------------------------------------------------------
    print("\n--- n can be 3*10^4 and a chain is legal ---")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}")
    chain = left_chain([(i % 21) - 10 for i in range(30_000)])
    try:
        r = sol.maxPathSum(chain)
        rec_msg, died = f"ok -> {r}", False
    except RecursionError as exc:
        rec_msg, died = f"{type(exc).__name__}: {exc}", True
    all_ok &= died
    print(f"  recursive postorder -> {rec_msg}")
    it = sol.maxPathSum_iterative(chain)
    print(f"  iterative postorder -> ok -> {it}")
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(60_000)
    try:
        rec = sol.maxPathSum(chain)
        print(f"  recursive after sys.setrecursionlimit(60000) -> ok -> {rec}")
        all_ok &= (rec == it)
    except RecursionError as exc:
        print(f"  recursive after sys.setrecursionlimit(60000) -> STILL {exc}")
        all_ok = False
    finally:
        sys.setrecursionlimit(old_limit)
    print("  Both routes work; the iterative one needs no global fiddling, and")
    print("  raising the limit can still hard-crash the C stack on a deeper tree.")

    # ----------------------------------------------------------------------
    # Timing: O(n) vs the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- benchmark: O(n) aggregate vs the O(n^2) path enumeration ---")
    print(f"  {'nodes':>7} {'O(n) (ms)':>11} {'O(n^2) (ms)':>13} {'ratio':>8}")
    rng = random.Random(3)
    for n in (50, 100, 200, 400):
        t = random_tree(n, rng, -9, 9)
        t0 = time.perf_counter()
        a = sol.maxPathSum(t)
        t1 = time.perf_counter()
        b = sol.maxPathSum_brute(t)
        t2 = time.perf_counter()
        all_ok &= (a == b)
        fast, slow = (t1 - t0) * 1000, (t2 - t1) * 1000
        print(f"  {n:>7} {fast:>11.3f} {slow:>13.2f} {slow / fast:>7.0f}x")
    print("  The oracle is only usable as a test tool because the trees are")
    print("  tiny. Note the ratio roughly quadrupling as n doubles — O(n^2)/O(n).")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
