"""
================================================================================
SOLUTION · LeetCode 530 · Minimum Absolute Difference in BST             [Easy]
https://leetcode.com/problems/minimum-absolute-difference-in-bst/
================================================================================

THE CORE IDEA
--------------
In-order traversal of a BST produces values in sorted order (topic guide,
Part 1). Once you have sorted order, the minimum absolute difference
between ANY two elements can only ever occur between two ADJACENT elements
in that order — never between two elements with something in between them.

Proof sketch: for any three values `a < b < c` drawn from the sorted
sequence, `c - a = (c - b) + (b - a)`. Both terms on the right are
non-negative, so `c - a >= max(c - b, b - a)` — the gap between the
non-adjacent pair `(a, c)` can never be SMALLER than the gap of at least
one of the two adjacent pairs sandwiching it. By induction this holds for
any pair, not just three elements, so checking only adjacent pairs in the
sorted sequence is sufficient — no O(n^2) all-pairs comparison is ever
needed.

That turns the problem into: walk in-order, keep a running `prev` and a
running `best` (minimum gap seen so far), update `best = min(best,
curr - prev)` at every step. Same skeleton as problem 006 (validate) and
problem 009 (recover), tracking a different quantity.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it and drop it): compare every pair of
node values, `O(n^2)` time, `O(1)` extra space (or O(n) if you first
collect values into a list to make the double loop easier to write). The
BST's ordering is never used — this is the "I forgot the input is sorted"
answer, exactly the trap topic 04's prefix-sum guide and this topic's own
guide both warn about: don't reach for O(n^2) work when a sorted structure
lets you check only neighbors.

Approach 1 (collect full in-order list, then scan adjacent pairs) —
correct, O(n) time, but O(n) EXTRA space to store the whole list when you
only ever need the PREVIOUS value at any point in time.

Approach 2 (in-order walk, iterative, track prev + running min) ✅ — the
answer, below. O(n) time, O(h) space (just the traversal stack, no
separate list of values).

Approach 3 (in-order walk, recursive with a mutable box) — same complexity
class as Approach 2's time, O(h) call-stack depth instead of an explicit
stack. Same recursion-ceiling caveat as every other recursive in-order
variant in this topic (guide Part 7): a skewed 10^4-node tree is legal
input here too.


================================================================================
STEP BY STEP TRACE
================================================================================
tree = [4,2,6,1,3]

              4
            ╱   ╲
          2       6
        ╱   ╲
      1       3

In-order: 1, 2, 3, 4, 6

    prev=None, best=+inf
    visit 1: prev is None -> no comparison. prev=1
    visit 2: best = min(+inf, 2-1=1) = 1. prev=2
    visit 3: best = min(1, 3-2=1) = 1. prev=3
    visit 4: best = min(1, 4-3=1) = 1. prev=4
    visit 6: best = min(1, 6-4=2) = 1. prev=6

    result: 1 ✅ — matches Example 1. Note the answer (gap of 1, between
    1&2, 2&3, AND 3&4) is achieved by THREE different adjacent pairs; the
    algorithm doesn't need to know which pair, only the minimum value.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                            Time    Space   Mutates input?  Note
    -----------------------------------  ------  ------  --------------  -----------
    All-pairs comparison (brute)         O(n^2)  O(1)    no              ignores
                                                                         sortedness
    Full list, then scan adjacent pairs  O(n)    O(n)    no              extra list
                                                                         unnecessary
    In-order walk, iterative ✅          O(n)    O(h)    no              the answer
    In-order walk, recursive             O(n)    O(h)    no              recursion
                                                                         ceiling risk


================================================================================
EDGE CASES
================================================================================
    two-node tree (n=2, the minimum)   -> exactly one adjacent pair to
                                        compare; `best` is set exactly once.
    values 0 and a very large gap       -> constraints allow 0 <= val <=
                                        10^5; using `float('inf')` as the
                                        initial `best` handles any legal
                                        gap without needing a sentinel
                                        integer trick.
    the minimum gap occurs between      -> the algorithm doesn't need or
    NON-adjacent TREE positions (e.g.     produce which nodes achieved the
    root and a deep leaf)                 minimum — only the value — so
                                        tree SHAPE is irrelevant; only
                                        in-order RANK adjacency matters.
    all values equally spaced            -> every adjacent gap is the same;
                                        `best` converges to that one value,
                                        exercised by test cases with evenly
                                        spaced BSTs.
    left-skewed or right-skewed tree     -> h == n; the iterative version
    (sorted input inserted ascending)      handles it fine, the recursive
                                        one risks RecursionError at the
                                        problem's 10^4-node bound.
    duplicate values                     -> excluded by BST rules in this
                                        problem's context (values are
                                        implicitly distinct per typical BST
                                        node value constraints used here);
                                        if duplicates were legal, the
                                        minimum difference would trivially
                                        be 0 the moment two equal values
                                        are adjacent in-order.


================================================================================
COMMON MISTAKES
================================================================================
1. Writing the O(n^2) all-pairs comparison because "minimum difference
   between any two nodes" sounds like it needs to check every pair — it
   does NOT, once you notice in-order gives you sorted order. This is the
   single biggest thing this problem is testing.

2. Collecting the full in-order list before scanning it (Approach 1) when
   asked to optimize space — works, but wastes O(n) when only the previous
   value needs to be remembered.

3. Off-by-one / never initializing `prev`: comparing on the VERY FIRST
   visited node (when there is no previous value yet) either crashes
   (`NoneType` subtraction) or silently corrupts `best` with a garbage
   comparison against an uninitialized value.

4. Using `abs(curr - prev)` — harmless here since in-order values are
   already increasing so `curr - prev` is always non-negative, but writing
   `abs(prev - curr)` or `abs(curr - prev)` is a good defensive habit if
   you're not 100% sure the traversal order is guaranteed increasing at
   the point you write the line.

5. Resetting `best` per recursive call (i.e., not sharing it across the
   whole traversal via `nonlocal`/an instance attribute/a mutable box) —
   silently reports the minimum gap only within the LAST subtree visited,
   not the whole tree.

6. Forgetting the constraint that guarantees `n >= 2` and adding dead code
   to defend against a 0- or 1-node tree, which the problem's own
   constraints already rule out.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Prove why checking only adjacent pairs in sorted order is sufficient.
A: The three-term inequality in THE CORE IDEA above:
   `c - a = (c - b) + (b - a) >= max(c - b, b - a)` for any `a < b < c`.
   The non-adjacent gap is never smaller than the tightest adjacent gap
   sandwiching it, by induction over any span.

Q: What if the tree were NOT a BST (a plain binary tree)?
A: In-order no longer gives sorted order, so the "only check neighbors"
   shortcut is gone. You'd need to collect all n values and sort them
   (O(n log n)) or, if you only need the minimum gap and values fit a
   bounded range, a counting/bucket approach — but the O(n)-in-a-BST
   result does not carry over.

Q: How would you also report WHICH pair of values achieves the minimum?
A: Track the pair alongside `best` — update `best_pair = (prev, node.val)`
   in the same branch that updates `best`. No extra pass needed.

Q: Many queries for the minimum gap against a tree that also mutates
   (insert/delete)?
A: A single global minimum doesn't compose nicely under arbitrary
   insert/delete without re-scanning, UNLESS you maintain it incrementally:
   on insert, the new value's minimum gap only needs comparing against its
   own in-order PREDECESSOR and SUCCESSOR (problem 010) — O(h) per insert
   to find those, then O(1) to update a running global minimum candidate
   set. Deletion is trickier (removing a value might have been the ONLY
   thing keeping a large gap small) and generally needs a order-statistics
   structure (e.g. a balanced BST augmented with subtree min-gap, mirroring
   problem 007's augmented-size follow-up) to stay sub-linear.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 2 of the topic guide's taxonomy: in-order-is-sorted, used to bound
a PAIRWISE quantity by only ever checking neighbors.

    LC 783  Minimum Distance Between BST Nodes  — identical problem,
                                                 different LC number
    LC 98   Validate Binary Search Tree          — in-order adjacent check
                                                 used as a boolean TEST (006)
    LC 99   Recover Binary Search Tree            — in-order adjacent check
                                                 used to LOCATE a corruption (009)
    LC 230  Kth Smallest Element in a BST         — in-order used to INDEX (007)
    LC 285  Inorder Successor in BST               — single-neighbor lookup
                                                 without a full scan (010)
    LC 220  Contains Duplicate III                 — the general (non-BST)
                                                 "closest pair within a
                                                 bound" cousin, solved with
                                                 a different structure
================================================================================
"""

import random
import time
from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def getMinimumDifference(self, root: Optional[TreeNode]) -> int:
        """✅ THE ANSWER — iterative in-order, track prev + running min.
        O(n) time, O(h) space."""
        stack, node, prev, best = [], root, None, float('inf')
        while stack or node:
            while node:
                stack.append(node)
                node = node.left
            node = stack.pop()
            if prev is not None:
                best = min(best, node.val - prev)
            prev = node.val
            node = node.right
        return best

    def getMinimumDifference_brute(self, root: Optional[TreeNode]) -> int:
        """Brute force: all-pairs comparison. O(n^2) time, ignores the
        BST's sortedness entirely."""
        values = []

        def collect(node):
            if node is None:
                return
            values.append(node.val)
            collect(node.left)
            collect(node.right)

        collect(root)
        best = float('inf')
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                best = min(best, abs(values[i] - values[j]))
        return best

    def getMinimumDifference_full_list(self, root: Optional[TreeNode]) -> int:
        """Full in-order list, then scan adjacent pairs. O(n) time, O(n)
        space — the list is unnecessary since only `prev` is ever needed."""
        values = []

        def walk(node):
            if node is None:
                return
            walk(node.left)
            values.append(node.val)
            walk(node.right)

        walk(root)
        return min(b - a for a, b in zip(values, values[1:]))

    def getMinimumDifference_recursive(self, root: Optional[TreeNode]) -> int:
        """In-order, recursive with a mutable box. Same O(n) time as the
        answer, O(h) call-stack depth — risks RecursionError on a skewed
        10^4-node tree."""
        state = {"prev": None, "best": float('inf')}

        def walk(node):
            if node is None:
                return
            walk(node.left)
            if state["prev"] is not None:
                state["best"] = min(state["best"], node.val - state["prev"])
            state["prev"] = node.val
            walk(node.right)

        walk(root)
        return state["best"]


# ==============================================================================
# TEST HELPERS — shared with topic 10; not part of the exercise
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


def balanced_bst_from_sorted(values):
    """Balanced BST built from an already-sorted list of distinct values."""
    def helper(lo, hi):
        if lo >= hi:
            return None
        mid = (lo + hi) // 2
        node = TreeNode(values[mid])
        node.left = helper(lo, mid)
        node.right = helper(mid + 1, hi)
        return node
    return helper(0, len(values))


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


# ==============================================================================
# TESTS — run:  python 011_minimum_absolute_difference_in_bst_solution.py
# ==============================================================================
CASES = [
    ([4, 2, 6, 1, 3], 1),
    ([1, 0, 48, None, None, 12, 49], 1),
    ([1, 0, 2], 1),
    ([0, None, 1], 1),
    ([90, 69, None, 49, 89, None, 52], 1),
    ([27, None, 34, None, None, 33], 7),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: iterative in-order, track prev+min (the answer) ---")
    for values, want in CASES:
        got = sol.getMinimumDifference(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<35} -> {got}  (want {want})")

    print("\n--- all four implementations agree ---")
    for values, want in CASES:
        a = sol.getMinimumDifference(build(values))
        b = sol.getMinimumDifference_brute(build(values))
        c = sol.getMinimumDifference_full_list(build(values))
        d = sol.getMinimumDifference_recursive(build(values))
        ok = a == b == c == d == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  iterative={a} brute={b} "
              f"full-list={c} recursive={d}")

    # ----------------------------------------------------------------------
    # STEP BY STEP trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: [4,2,6,1,3] ---")
    root = build([4, 2, 6, 1, 3])
    stack, node, prev, best = [], root, None, float('inf')
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        if prev is not None:
            gap = node.val - prev
            best = min(best, gap)
            print(f"  visit {node.val}: gap vs prev({prev}) = {gap}, "
                  f"best so far = {best}")
        else:
            print(f"  visit {node.val}: (first value, no prev yet)")
        prev = node.val
        node = node.right
    print(f"  result: {best}")

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO: the all-pairs trap — same answer, wildly different cost.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  DEMO: the O(n^2) all-pairs trap, measured ---")
    print(f"  {'n':>7} {'in-order us':>13} {'all-pairs us':>14} {'speedup':>9}")
    ratios_grow = []
    for n in (500, 2_000, 8_000):
        sorted_vals = list(range(0, n * 2, 2))  # evenly spaced, distinct
        random.seed(n)
        random.shuffle(sorted_vals)
        root = None
        for v in sorted_vals:
            root = bst_insert_iterative(root, v)
        reps = 200 if n <= 2000 else 30
        t0 = time.perf_counter()
        for _ in range(reps):
            sol.getMinimumDifference(root)
        t1 = time.perf_counter()
        # all-pairs is expensive; fewer reps for large n to keep this fast
        brute_reps = max(1, reps // 20)
        for _ in range(brute_reps):
            sol.getMinimumDifference_brute(root)
        t2 = time.perf_counter()
        us_io = (t1 - t0) / reps * 1e6
        us_brute = (t2 - t1) / brute_reps * 1e6
        ratio = us_brute / us_io
        ratios_grow.append(ratio)
        print(f"  {n:>7} {us_io:>13.1f} {us_brute:>14.1f} {ratio:>8.0f}x")
    print("  Measured on THIS machine: the speedup GROWS as n grows — O(n)")
    print("  vs O(n^2) — because the all-pairs version does quadratically more")
    print("  comparisons every time n doubles, while the in-order scan's cost")
    print("  only doubles.")
    growing = ratios_grow[-1] > ratios_grow[0]
    all_ok &= growing

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: memory, in-order-with-prev (O(h)) vs full-list (O(n)).
    # ----------------------------------------------------------------------
    print("\n--- DEMO: peak memory — O(h) running-prev vs O(n) full list ---")
    import tracemalloc
    n = 50_000
    root = balanced_bst_from_sorted(list(range(0, n * 2, 2)))
    h = height_iterative(root)
    print(f"  n={n}, height={h}")

    tracemalloc.start()
    sol.getMinimumDifference(root)
    _, peak_running = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tracemalloc.start()
    sol.getMinimumDifference_full_list(root)
    _, peak_full = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    print(f"  running-prev version peak extra memory: {peak_running:>9,} bytes")
    print(f"  full-list version peak extra memory:     {peak_full:>9,} bytes")
    print(f"  ratio: {peak_full / peak_running:.1f}x more for the full-list version")
    demo_mem_ok = peak_full > peak_running
    all_ok &= demo_mem_ok

    # ----------------------------------------------------------------------
    # Randomised cross-check across all four implementations.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check ---")
    random.seed(530)
    mismatches, trials = 0, 2000
    for _ in range(trials):
        vals = random.sample(range(0, 100_000), random.randint(2, 40))
        root = None
        for v in vals:
            root = bst_insert_iterative(root, v)
        a = sol.getMinimumDifference(root)
        b = sol.getMinimumDifference_brute(root)
        c = sol.getMinimumDifference_full_list(root)
        d = sol.getMinimumDifference_recursive(root)
        if not (a == b == c == d):
            mismatches += 1
    print(f"  {trials} random BSTs x 4 implementations: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
