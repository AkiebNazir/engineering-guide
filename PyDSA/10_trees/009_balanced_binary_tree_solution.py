"""
================================================================================
SOLUTION · LeetCode 110 · Balanced Binary Tree                          [Easy]
https://leetcode.com/problems/balanced-binary-tree/
================================================================================

THE CORE IDEA
--------------
"Height-balanced" is a statement about EVERY node, not just the root: for
each node, |height(left) - height(right)| <= 1. Height itself is the
familiar postorder aggregate from problem 005
(`1 + max(height(left), height(right))`) — a value that flows UP the call
stack from children to parent (topic guide, Part 4.2).

The naive approach takes the definition literally: at every node, call an
INDEPENDENT `height()` helper on its left and right children, check the
diff, and recurse. `height()` is itself O(size of that subtree), and it gets
called at every one of the n nodes in the tree — the classic "recompute a
bottom-up aggregate from scratch at every level" trap.

The fix is the same insight problem 005 already uses, pushed one step
further: a SINGLE postorder pass can return the height of a subtree AND
signal whether that subtree (and everything below it) is balanced, in the
very same return value. There's no need for a second "is balanced" pass
layered on top of a first "compute height" pass, because postorder already
visits children before parents — by the time a node is ready to compute its
own height, it already has both children's height AND balance status in
hand, for free.

The one extra trick beyond "combine height and balanced into one return
value" is EARLY BAILOUT: the moment any subtree below is found to be
unbalanced, there is no point computing further heights at all — the whole
tree is already unbalanced regardless of what the rest of it looks like.
Returning a sentinel (here, `-1`, since a real height is never negative)
lets that bad news propagate straight up to the root in O(1) extra work per
frame, instead of doing more arithmetic that nobody will use:

    def check(node):
        if node is None:
            return 0                        # empty subtree: height 0
        lh = check(node.left)
        if lh == -1:                        # already broken below-left —
            return -1                        # stop, don't touch the right side
        rh = check(node.right)
        if rh == -1:
            return -1
        if abs(lh - rh) > 1:
            return -1                        # broken HERE — signal upward
        return 1 + max(lh, rh)               # genuinely still balanced

    def isBalanced(root):
        return check(root) != -1

This is one postorder pass, O(n) time, O(h) space — no closures, no
`nonlocal`, no second traversal. The sentinel return value IS the
"balanced so far" signal; it just rides along on the same channel that
already carries height.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, O(n^2)) — for every node, call an independent `height()`
   helper on its left and right children (a full O(subtree size) traversal
   each time), check `abs(lh - rh) <= 1`, and recurse into both children to
   check the rest of the tree the same way:

       def check(node):
           if node is None: return True
           lh, rh = height(node.left), height(node.right)
           return (abs(lh - rh) <= 1
                   and check(node.left) and check(node.right))

   `height()` is O(k) for a subtree of size k, and it is invoked once per
   node — for a tree shaped like a chain, the node at depth i triggers a
   height() call that walks the remaining (n - i) nodes, so the total work
   is `sum_{i=0}^{n} (n - i)` = O(n^2). Measured below: real, not
   theoretical.

Approach 1 (optimal, O(n)) ✅ — the postorder-with-sentinel shape above.
   Height and "balanced so far" share one return value; an imbalance found
   anywhere short-circuits the rest of that branch immediately. This is
   what the tests check and what the timing demo contrasts against
   Approach 0.

Approach 2 (postorder returning a tuple, no sentinel) — return
   `(height, is_balanced)` explicitly instead of overloading `-1`:

       def check(node):
           if node is None: return (0, True)
           lh, l_ok = check(node.left)
           rh, r_ok = check(node.right)
           ok = l_ok and r_ok and abs(lh - rh) <= 1
           return (1 + max(lh, rh), ok)

   Same O(n) time and O(h) space as Approach 1, and arguably more readable
   since nothing is overloaded — the cost is that every call still does the
   `max`/`+1` height arithmetic even after a subtree is already known
   broken (no early bailout), and it allocates a 2-tuple per call. Worth
   naming as the tuple-return variant from the topic guide's Part 5.4, even
   though this problem's aggregation is boolean rather than a running best.

Approach 3 (`nonlocal` closure, tree guide Part 5.2 style) — track a
   `balanced = True` flag closed over by a nested `height()` function that
   sets it to `False` the moment it finds an imbalance, and let `height()`
   itself keep returning genuine heights throughout (no sentinel, no early
   return once flagged — it just keeps computing, wastefully, after the
   answer is already known):

       def isBalanced(root):
           balanced = True
           def height(node):
               nonlocal balanced
               if node is None: return 0
               lh, rh = height(node.left), height(node.right)
               if abs(lh - rh) > 1:
                   balanced = False
               return 1 + max(lh, rh)
           height(root)
           return balanced

   Still O(n) (each node visited once, and no per-node O(n) `height()`
   call), but strictly worse than Approach 1 in practice — no early
   bailout, so a tree that goes unbalanced at the root still walks every
   remaining node. Included to contrast against the topic guide's Part 5
   idiom directly: this problem does NOT strictly need `nonlocal`, because
   the "different second value" the guide describes (a through-value that
   can't be returned) doesn't arise here — a plain sentinel return is
   sufficient and strictly better. Diameter (problem 010) is the case where
   `nonlocal` earns its keep.


================================================================================
DEMO — MEASURED, NOT GUESSED (see run_tests() for the exact code)
================================================================================
Built a LEFT-skewed chain of n nodes (so `height()` at depth i really does
walk the remaining n-i nodes), ran the naive Approach 0 and the optimal
Approach 1 on the SAME tree, and timed each with `time.perf_counter()`.
Naive here always recurses into both children regardless of the local
diff check (no short-circuit on the boolean itself) — that is what makes
`height()` fire at every one of the n nodes, matching the textbook O(n^2)
claim; a naive version that short-circuits its recursion the instant it
finds ANY imbalance would return after one O(n) call at the root, because a
skewed chain is already unbalanced there — a different, much weaker
"naive" that doesn't illustrate the trap at all.

    n      naive (Approach 0)   optimal (Approach 1)   ratio
    -----  -------------------  ---------------------  ------
     500          9.88 ms              0.025 ms          398x
    1000         37.48 ms              0.036 ms         1040x
    2000        145.85 ms              0.066 ms         2197x
    4000        585.82 ms              0.144 ms         4055x

Doubling n (500 -> 1000 -> 2000 -> 4000) roughly QUADRUPLES the naive time
each step (9.88 -> 37.48 -> 145.85 -> 585.82 ms, each ~3.8-4.0x the last) —
the O(n^2) signature. The optimal version's time barely more than doubles
each step (0.025 -> 0.036 -> 0.066 -> 0.144 ms) — O(n), as expected. The
ratio between them grows with n itself (398x at 500, 4055x at 4000) because
one side is linear and the other quadratic — exactly what "O(n) vs O(n^2)"
predicts, and this is the actual `run_tests()` output on this machine, not
an estimate.


================================================================================
STEP BY STEP TRACE — root = [3,9,20,null,null,15,7]
================================================================================
            3
          ╱   ╲
         9     20
             ╱    ╲
            15     7

    check(3)
      check(9)                          <- left child, a leaf
        check(None) -> 0   (9's left)
        check(None) -> 0   (9's right)
        |0 - 0| <= 1  -> height = 1 + max(0,0) = 1
      lh = 1
      check(20)
        check(15)
          check(None) -> 0, check(None) -> 0
          |0-0|<=1 -> height = 1
        lh(20) = 1
        check(7)
          check(None) -> 0, check(None) -> 0
          |0-0|<=1 -> height = 1
        rh(20) = 1
        |1 - 1| <= 1  -> height(20) = 1 + max(1,1) = 2
      rh = 2
      |lh - rh| = |1 - 2| = 1 <= 1  -> height(3) = 1 + max(1,2) = 3
    check(3) returns 3 (not -1)  -> isBalanced = True

Now Example 2, [1,2,2,3,3,null,null,4,4] — the imbalance is buried FOUR
levels down, not visible at the root's immediate children:

                1
              ╱   ╲
            2       2          <- right 2 is a LEAF (height 1)
          ╱   ╲
        3       3
      ╱   ╲
    4       4

    check(1)
      check(2)  [left branch, the deep one]
        check(3)  [left branch of that 2]
          check(4) -> height 1 (leaf)
          check(4) -> height 1 (leaf)
          |1-1|<=1 -> height(3, left-left) = 2
        lh(2) = 2
        check(3)  [right branch of that 2, a childless leaf here]
          check(None) -> 0, check(None) -> 0 -> height = 1
        rh(2) = 1
        |2 - 1| = 1 <= 1  -> height(2, left) = 1 + max(2,1) = 3
      lh(1) = 3
      check(2)  [right branch, a leaf]
        check(None) -> 0, check(None) -> 0 -> height = 1
      rh(1) = 1
      |lh - rh| = |3 - 1| = 2 > 1   <- FOUND IT, at the ROOT's own check
      check(1) returns -1
    isBalanced = (check(1) != -1) = False

    The imbalance is detected exactly once, at node 1, the instant both
    subtree heights are known — no separate "was anything below broken"
    pass was needed; the sentinel already carried that news up from every
    level beneath it (in this example, nothing below the root happened to
    be locally imbalanced, so no early -1 short-circuit fired before
    reaching the root — but if it had, e.g. node 3's own children differed
    by more than 1, the -1 would propagate straight to node 1 without
    recomputing anything else in that branch).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time      Space   Mutates?  Note
    -------------------------------  --------  -------  --------  ----------------
    Naive: height() at every node ❌  O(n^2)    O(h)     no        real, measured
    Postorder + sentinel (-1) ✅      O(n)      O(h)     no        the answer
    Postorder + (height, bool) tuple  O(n)      O(h)     no        no early bailout,
                                                                     allocates tuples
    `nonlocal` closure flag           O(n)      O(h)     no        works, but no
                                                                     early bailout
    Iterative postorder + sentinel    O(n)      O(n)     no        avoids recursion
                                                                     limit (§2.2)

    h = tree height: O(log n) for a balanced tree, O(n) for a fully skewed
    one (and a fully skewed tree with n large enough is exactly the case
    that ALSO risks Python's recursion limit — see Edge Cases below).


================================================================================
EDGE CASES
================================================================================
    Empty tree (root=None)      -> True. `check(None)` returns 0 (a valid,
                                    non-negative height), never -1, so there
                                    is no node for which an imbalance could
                                    exist. Matches Example 3 / LeetCode's
                                    stated convention.
    Single node                 -> True. Both children are None, both
                                    return height 0, diff 0.
    One-sided skew (chain)      -> False, and detected AT THE ROOT already
                                    (one side has height n-1, the other 0),
                                    so the naive approach doesn't even get a
                                    chance to look expensive on THIS shape —
                                    the O(n^2) trap needs the imbalance
                                    buried away from the root (see the demo
                                    note above and Common Mistake 2).
    Minimally imbalanced tree
    (diff exactly 2 at one node) -> False; `> 1` (strict) is the correct
                                    test. `>= 1` would reject perfectly
                                    valid balanced trees (diff of exactly 1
                                    is ALLOWED by the problem statement).
    Deep but genuinely balanced
    tree (e.g. a full/complete
    binary tree of height ~log n) -> True, and cheap: the recursion depth
                                    stays O(log n), nowhere near Python's
                                    recursion limit even for n in the tens
                                    of thousands.
    Large SKEWED tree (n in the
    thousands, e.g. LC's own
    upper bound of 5000)        -> Still answered correctly and in one
                                    postorder pass, but the recursion depth
                                    is O(n) here, not O(log n) — see the
                                    topic guide §2.2 recursion-limit note;
                                    an iterative postorder-with-explicit-
                                    stack is the fix if n grows past what
                                    `sys.setrecursionlimit` comfortably
                                    allows.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking only the ROOT's two children's heights, not every node's. A
   tree can look fine at the top and be broken four levels down (Example
   2's actual shape) — the check has to be recursive over every subtree,
   not a single top-level `abs(height(root.left) - height(root.right))`.
2. Assuming the O(n^2) naive trap is visible on ANY skewed tree. A skewed
   chain is unbalanced right at the root (one side has height n-1, the
   other 0), so a naive implementation detects it in a single O(n) call
   and never gets the chance to look quadratic — the actual O(n^2)
   worst case needs a naive implementation that does NOT short-circuit its
   own recursion once a local imbalance is found (Approach 0 above always
   recurses into both children regardless), otherwise the "trap" input
   silently stops looking expensive. Always demonstrate a claim by
   measuring it, not by assuming a superficially "bad-looking" tree proves
   the point (CONTEXT.md's rule, learned the hard way on 007-012).
3. Not short-circuiting on the sentinel: writing the optimal-shaped
   function but still unconditionally computing BOTH `check(node.left)`
   and `check(node.right)` even after the left side already came back -1.
   This still visits every node exactly once (so it stays O(n), it isn't
   "wrong" complexity-wise) but it wastes work that Approach 1's early
   `if lh == -1: return -1` avoids — worth naming as the difference between
   "technically O(n)" and "actually fast" in a follow-up.
4. Off-by-one on the allowed difference: using `>= 1` (or `> 0`) instead of
   `> 1` as the imbalance test. The problem explicitly allows a difference
   of exactly 1 — `>= 1` rejects Example 1 itself (node 3's children have
   heights 1 and 2, diff exactly 1, which IS balanced).
5. Overloading `-1` as a sentinel while heights can also legitimately be
   `-1` in some other convention (e.g. counting edges instead of nodes,
   where an empty tree's height is `-1` rather than `0`). Pick ONE
   convention for "height of empty subtree" and be consistent — this file
   uses node-count height, so 0 is the empty-tree height and -1 is free to
   mean "broken".
6. Recomputing height via TWO separate full traversals (one pass to build
   a height map, a second pass to check every node against it) when a
   single postorder pass already produces both pieces of information in
   the right order — needless but common over-engineering once someone has
   already learned "compute height first."


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you avoid the O(n^2) naive approach?
A: Yes — fold height and "balanced so far" into one postorder return value
   with an early-bailout sentinel (Approach 1). O(n) time, O(h) space.

Q: What if I wanted to know not just IS it balanced, but the WORST
   imbalance anywhere in the tree (the maximum |lh - rh| over all nodes)?
A: Same postorder shape, but instead of a boolean sentinel, thread a
   running maximum through a `nonlocal` variable or a second tuple slot —
   this is exactly the topic guide's Part 5 idiom (a value that RETURNS
   upward for the parent's own height math, plus a SEPARATE side channel
   for a running best that is never itself returned). Diameter (problem
   010) is the canonical worked example of that exact pattern.

Q: How does this relate to AVL trees?
A: An AVL tree maintains this EXACT invariant (height diff <= 1 at every
   node) after every insert/delete, via rotations, so that its height stays
   O(log n) — which is precisely why AVL search/insert/delete are all
   O(log n) guaranteed. This problem is "check the AVL invariant once,
   statically"; a real AVL tree enforces it continuously and incrementally.

Q: Can you do it iteratively, without recursion?
A: Yes — an explicit postorder traversal with a stack (topic guide §2.3),
   using a hashmap from node -> computed height as each node is popped
   after both children are done, and returning False the moment any
   node's `abs(lh - rh) > 1`. Needed if n could be large enough on a
   skewed shape to risk Python's recursion limit (§2.2) — the same
   RecursionError concern problem 018 measures directly on a 30,000-node
   chain.

Q: Would memoizing `height()` fix the naive O(n^2) approach?
A: No, not the way it's usually attempted — the naive bug is calling an
   INDEPENDENT `height()` helper repeatedly on OVERLAPPING subtrees from
   different ancestor calls. Memoizing by node identity would work (each
   node's height computed once, O(n) total), but at that point you have
   reinvented the postorder-single-pass approach with extra bookkeeping;
   there's no reason to keep the two-function structure once you notice
   heights only need to be computed once, bottom-up.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 104   Maximum Depth of Binary Tree   — the bare height aggregate (005 here)
    LC 543   Diameter of Binary Tree        — postorder + `nonlocal`, a SECOND,
                                               non-returnable answer (010 here)
    LC 124   Binary Tree Maximum Path Sum   — same idiom at full difficulty,
                                               with a `max(x, 0)` clamp (018 here)
    LC 111   Minimum Depth of Binary Tree   — the leaf-only asymmetric trap
                                               (006 here) — a different postorder
                                               subtlety from this problem's
    Topic guide Part 4.2                    — "return value carries info UP"
    Topic guide Part 5                      — the `nonlocal`/sentinel/tuple family
                                               of ways to carry a SECOND value out
                                               of the same postorder pass
================================================================================
"""

import random
import sys
import time
from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    # ------------------------------------------------------------------
    # Approach 1 — the answer: postorder height + sentinel, one pass, O(n).
    # ------------------------------------------------------------------
    def isBalanced(self, root: Optional[TreeNode]) -> bool:
        """One postorder pass. Returns -1 the instant any subtree below is
        found unbalanced, short-circuiting further work in that branch."""
        return self._check(root) != -1

    def _check(self, node: Optional[TreeNode]) -> int:
        if node is None:
            return 0
        lh = self._check(node.left)
        if lh == -1:
            return -1
        rh = self._check(node.right)
        if rh == -1:
            return -1
        if abs(lh - rh) > 1:
            return -1
        return 1 + max(lh, rh)

    # ------------------------------------------------------------------
    # Approach 0 — naive: an independent height() call at every node.
    #   Always recurses into BOTH children regardless of the local check,
    #   so height() genuinely fires at every one of the n nodes -> O(n^2).
    # ------------------------------------------------------------------
    def isBalanced_naive(self, root: Optional[TreeNode]) -> bool:
        return self._check_naive(root)

    def _height_naive(self, node: Optional[TreeNode]) -> int:
        if node is None:
            return 0
        return 1 + max(self._height_naive(node.left),
                        self._height_naive(node.right))

    def _check_naive(self, node: Optional[TreeNode]) -> bool:
        if node is None:
            return True
        lh = self._height_naive(node.left)
        rh = self._height_naive(node.right)
        left_ok = self._check_naive(node.left)
        right_ok = self._check_naive(node.right)
        return abs(lh - rh) <= 1 and left_ok and right_ok

    # ------------------------------------------------------------------
    # Approach 2 — postorder returning (height, is_balanced) as a tuple.
    #   No sentinel overload, but no early bailout either.
    # ------------------------------------------------------------------
    def isBalanced_tuple(self, root: Optional[TreeNode]) -> bool:
        return self._check_tuple(root)[1]

    def _check_tuple(self, node: Optional[TreeNode]):
        if node is None:
            return (0, True)
        lh, l_ok = self._check_tuple(node.left)
        rh, r_ok = self._check_tuple(node.right)
        ok = l_ok and r_ok and abs(lh - rh) <= 1
        return (1 + max(lh, rh), ok)

    # ------------------------------------------------------------------
    # Approach 3 — `nonlocal` closure flag (topic guide Part 5.2 style).
    #   Correct, O(n), but no early bailout once the flag flips.
    # ------------------------------------------------------------------
    def isBalanced_nonlocal(self, root: Optional[TreeNode]) -> bool:
        balanced = True

        def height(node: Optional[TreeNode]) -> int:
            nonlocal balanced
            if node is None:
                return 0
            lh, rh = height(node.left), height(node.right)
            if abs(lh - rh) > 1:
                balanced = False
            return 1 + max(lh, rh)

        height(root)
        return balanced

    # ------------------------------------------------------------------
    # Approach 4 — iterative postorder + sentinel, no recursion at all.
    #   Immune to RecursionError on very deep skewed trees (topic guide §2.2).
    # ------------------------------------------------------------------
    def isBalanced_iterative(self, root: Optional[TreeNode]) -> bool:
        if root is None:
            return True
        heights = {}
        stack = [(root, False)]
        while stack:
            node, processed = stack.pop()
            if node is None:
                continue
            if processed:
                lh = heights.get(node.left, 0)
                rh = heights.get(node.right, 0)
                if abs(lh - rh) > 1:
                    return False
                heights[node] = 1 + max(lh, rh)
            else:
                stack.append((node, True))
                stack.append((node.left, False))
                stack.append((node.right, False))
        return True


# ==============================================================================
# TEST HELPERS — standard tree kit (documented in 001)
# ==============================================================================
def build(values):
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


def build_skewed(n, side="left"):
    if n == 0:
        return None
    root = TreeNode(0)
    curr = root
    for i in range(1, n):
        node = TreeNode(i)
        if side == "left":
            curr.left = node
        else:
            curr.right = node
        curr = node
    return root


def random_tree(n, rng, vals=6):
    if n == 0:
        return None
    root = TreeNode(rng.randrange(vals))
    nodes = [root]
    for _ in range(n - 1):
        parent = rng.choice(nodes)
        while parent.left is not None and parent.right is not None:
            parent = rng.choice(nodes)
        node = TreeNode(rng.randrange(vals))
        if parent.left is None and (parent.right is not None or rng.random() < 0.5):
            parent.left = node
        else:
            parent.right = node
        nodes.append(node)
    return root


# ==============================================================================
# TESTS — run:  python 009_balanced_binary_tree_solution.py
# ==============================================================================
CASES = [
    ([3, 9, 20, None, None, 15, 7], True),
    ([1, 2, 2, 3, 3, None, None, 4, 4], False),
    ([], True),
    ([1], True),
    ([1, 2, None, 3], False),
    ([1, 2, 3, 4, 5, 6, 7], True),
    ([1, 2, 2, 3, None, None, None, 4], False),
    ([1, 2], True),
    ([1, 2, 3], True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: optimal (postorder + sentinel) ---")
    for rv, want in CASES:
        got = sol.isBalanced(build(rv))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  root={rv!r:<40} -> {got}  (want {want})")

    print("\n--- correctness: naive, tuple, nonlocal, iterative all agree ---")
    impls = [
        ("naive O(n^2)   ", sol.isBalanced_naive),
        ("tuple return   ", sol.isBalanced_tuple),
        ("nonlocal       ", sol.isBalanced_nonlocal),
        ("iterative      ", sol.isBalanced_iterative),
    ]
    for name, fn in impls:
        ok = all(fn(build(rv)) == want for rv, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Randomised cross-check: all five implementations agree on many trees.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check: all 5 implementations agree ---")
    rng = random.Random(110)
    mismatches = 0
    trials = 3000
    all_fns = [sol.isBalanced, sol.isBalanced_naive, sol.isBalanced_tuple,
               sol.isBalanced_nonlocal, sol.isBalanced_iterative]
    for _ in range(trials):
        t = random_tree(rng.randint(0, 20), rng, vals=5)
        want = sol.isBalanced(t)
        if any(fn(t) != want for fn in all_fns):
            mismatches += 1
    print(f"  {trials} random trees (0-20 nodes each): {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Off-by-one guard: a tree with diff EXACTLY 1 must be True, diff 2 False.
    # ----------------------------------------------------------------------
    print("\n--- off-by-one guard: diff-of-1 is BALANCED, diff-of-2 is NOT ---")
    exactly_one = build([1, 2, 3, 4])          # left subtree height 2, right 1
    exactly_two = build([1, 2, None, 3, None, 4])  # a straight 4-node left chain
    r1 = sol.isBalanced(exactly_one)
    r2 = sol.isBalanced(exactly_two)
    print(f"  diff=1 tree -> {r1} (want True)")
    print(f"  diff=3 chain -> {r2} (want False)")
    all_ok &= (r1 is True and r2 is False)

    # ----------------------------------------------------------------------
    # ⚠️  MEASURED: naive O(n^2) vs optimal O(n) on a skewed chain.
    # ----------------------------------------------------------------------
    print("\n--- measured: naive O(n^2) vs optimal O(n), left-skewed chains ---")
    print("  naive always recurses into BOTH children regardless of the local")
    print("  diff check, so height() genuinely fires at every node -> O(n^2).")
    print(f"  {'n':>6} {'naive':>14} {'optimal':>14} {'ratio':>10}")
    saved = sys.getrecursionlimit()
    sys.setrecursionlimit(200_000)
    try:
        prev_naive_ms = None
        for n in (500, 1000, 2000, 4000):
            t = build_skewed(n, "left")

            t0 = time.perf_counter()
            r_naive = sol.isBalanced_naive(t)
            naive_ms = (time.perf_counter() - t0) * 1000

            t0 = time.perf_counter()
            r_opt = sol.isBalanced(t)
            opt_ms = (time.perf_counter() - t0) * 1000

            ratio = naive_ms / opt_ms if opt_ms > 0 else float("inf")
            print(f"  {n:>6} {naive_ms:>11.2f}ms {opt_ms:>11.3f}ms {ratio:>9.0f}x")
            all_ok &= (r_naive is False and r_opt is False)  # a chain is unbalanced

            if prev_naive_ms is not None:
                growth = naive_ms / prev_naive_ms
                print(f"         (n doubled -> naive time grew {growth:.1f}x; "
                      f"O(n^2) predicts ~4x)")
            prev_naive_ms = naive_ms
    finally:
        sys.setrecursionlimit(saved)

    print("\n  Both agree the chain is unbalanced (it is: a left-only chain has")
    print("  height diff n-1 vs 0 right at the root). The point is not the")
    print("  ANSWER — it's that naive's wall-clock time roughly QUADRUPLES each")
    print("  time n doubles, while optimal's barely more than doubles. That is")
    print("  the O(n^2) vs O(n) gap made visible, not asserted.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
