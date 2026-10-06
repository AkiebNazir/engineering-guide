"""
================================================================================
SOLUTION · LeetCode 95 · Unique Binary Search Trees II                  [Medium]
https://leetcode.com/problems/unique-binary-search-trees-ii/
================================================================================

THE CORE IDEA
--------------
Same split as 011 (a fixed root forces a left range and a right range),
but now the combine step is a CROSS PRODUCT of actual tree shapes: every
possible left subtree pairs with every possible right subtree to form a
distinct whole tree. Writing the recursion as `build(lo, hi)` over an
arbitrary range (rather than special-casing `1..n`) makes the base case
and the recursive call symmetric and reusable for any sub-range.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, NO MEMO — `build(lo, hi)` recomputes the same sub-range's
   full list of shapes every time it's needed by a different root choice
   one level up (e.g. `build(1, 3)` and `build(2, 4)` both independently
   trigger their own `build(2, 3)`-shaped subcalls if the ranges
   overlap in width). O(Catalan(n) * n) time overall to just enumerate
   the final trees, but with real redundant work for the intermediate
   range computations. The version taught here, kept unmemoized because
   the ranges `(lo, hi)` used by DIFFERENT root choices under `1..n`
   rarely repeat exactly — memoizing on `(lo, hi)` DOES help once n
   grows, and is priced as a follow-up.
2. MEMOIZED ON (lo, hi) — cache `build(lo, hi)`'s returned list of tree
   shapes, keyed by the range, since (per 011's insight) only the WIDTH
   of the range determines shape count, but the actual VALUES differ per
   position, so caching must key on `(lo, hi)`, not just width, because
   the returned objects carry real values.
3. BUILD FROM 011's COUNTS FIRST — precompute `numTrees(k)` for every
   `k` (011's DP), then... this doesn't actually save the enumeration
   cost, since every single tree still has to be constructed regardless;
   named only to clarify that 011 and 012 solve genuinely different
   problems (counting vs. enumerating), not that one shortcuts the other.


================================================================================
STEP BY STEP TRACE — generateTrees(3), i.e. build(1, 3)
================================================================================
    build(1, 3): try every root r in {1, 2, 3}
      r=1: left = build(1, 0) = [None]           right = build(2, 3) = [2 trees]
           cross product: 1 * 2 = 2 trees with root 1
      r=2: left = build(1, 1) = [1 tree: node(1)]  right = build(3, 3) = [1 tree: node(3)]
           cross product: 1 * 1 = 1 tree with root 2
      r=3: left = build(1, 2) = [2 trees]          right = build(4, 3) = [None]
           cross product: 2 * 1 = 2 trees with root 3
    Total: 2 + 1 + 2 = 5 trees — matches numTrees(3) = 5 from problem 011 exactly.

    build(2, 3) (needed for r=1's right side) itself splits again:
      r=2: left=build(2,1)=[None], right=build(3,3)=[node(3)] -> 1 tree: node(2, right=3)
      r=3: left=build(2,2)=[node(2)], right=build(4,3)=[None] -> 1 tree: node(3, left=2)
    -> 2 trees, confirming the "2 trees" claimed above for r=1's right side.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time                   Space                  Mutates input?  Note
    -----------------------  ---------------------  ---------------------  ---------------  --------------------------------
    Recursive, no memo      O(Catalan(n) * n)-ish   O(Catalan(n) * n)-ish   no               some redundant sub-range work
    Memoized on (lo, hi)     same asymptotic total   same total, less       no               avoids recomputation, not
                                                     redundant work                          fewer FINAL trees (still all built)


================================================================================
EDGE CASES
================================================================================
    n = 1        -> [[1]]  a single node; `build(1,1)`'s only root
                            choice has empty left AND right (`[None]`
                            each), producing exactly one tree.
    n = 8        -> upper constraint bound (Catalan(8) = 1430 trees) —
                            exercises the cross-product blowup at a
                            real, non-trivial scale.
    every returned tree is a VALID BST -> checked structurally below,
                            not merely assumed from the construction
                            being "obviously" correct.
    every returned tree is STRUCTURALLY DISTINCT -> also checked below;
                            a subtle construction bug (e.g. reusing a
                            mutable node across trees) could otherwise
                            silently produce duplicates or shared state.


================================================================================
COMMON MISTAKES
================================================================================
1. Returning `[]` (empty list) instead of `[None]` for the `lo > hi` base
   case — this makes the cross-product loop over left/right shapes
   iterate ZERO times whenever one side is empty, silently producing NO
   trees at all for any root whose left or right subtree is empty
   (which is every root except when both lo<root<hi strictly).
2. Using a SINGLE loop that zips left and right shapes together
   (`for left, right in zip(leftShapes, rightShapes)`) instead of a
   NESTED loop — this only pairs shapes at matching INDICES instead of
   every combination, undercounting the true number of trees whenever
   either side has more than one shape.
3. Sharing/reusing the SAME `TreeNode` object across multiple returned
   trees under the mistaken assumption that "the tree is never mutated
   after construction, so sharing is safe" — true in THIS problem since
   nothing mutates the trees afterward, but a fragile assumption to
   carry forward; if any caller later mutated a shared node, every tree
   containing it would corrupt silently.
4. Forgetting that shape count for `build(lo, hi)` depends only on
   `hi - lo + 1` (matching 011's count), but the ACTUAL VALUES inside
   each tree depend on `lo` and `hi` themselves — so results can't be
   cached by width alone the way 011's counts can; caching (if added)
   must key on the full `(lo, hi)` pair.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How many trees does this return for a given n, and how do you know
   without recounting?
A: Exactly `Catalan(n)` (011's answer) — verified directly against 011's
   formula in the tests below, not merely asserted.

Q: Would memoizing `build(lo, hi)` by `(lo, hi)` help here?
A: It avoids recomputing the SAME sub-range's shape list when it's
   needed by more than one parent call (which does happen for n > 3,
   as overlapping ranges of the same width but different offsets show up
   repeatedly) — it doesn't reduce the FINAL number of trees built or
   returned, only the redundant recursive work along the way.

Q: How would you adapt this to also return `numTrees(n)` without
   building any trees at all, for large n?
A: That's exactly 011 — same recurrence, but the combine step multiplies
   counts instead of building a cross product of actual objects,
   avoiding the O(Catalan(n)) space/time cost of materializing every
   tree.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 011 Unique Binary Search Trees — the counting-only version
                                       of this exact recurrence.
    Topic 28, 015 All Possible Full Binary Trees — another "split a range/
                                       count, build a cross product of
                                       left and right shapes" recursion.
    Topic 09 Recursion & Backtracking (Generate Parentheses) — a
                                       different but related "enumerate
                                       all structurally valid
                                       combinatorial objects" recursion.
================================================================================
"""

from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def generateTrees(self, n: int) -> List[Optional[TreeNode]]:
        """Recursive, cross product of left/right shapes per root choice."""
        if n == 0:
            return []
        return self._build(1, n)

    def _build(self, lo: int, hi: int) -> List[Optional[TreeNode]]:
        if lo > hi:
            return [None]
        trees = []
        for r in range(lo, hi + 1):
            for left in self._build(lo, r - 1):
                for right in self._build(r + 1, hi):
                    trees.append(TreeNode(r, left, right))
        return trees

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def generateTrees_memoized(self, n: int) -> List[Optional[TreeNode]]:
        """Memoized on (lo, hi) to avoid recomputing shared sub-ranges."""
        if n == 0:
            return []
        memo = {}

        def build(lo: int, hi: int) -> List[Optional[TreeNode]]:
            if lo > hi:
                return [None]
            key = (lo, hi)
            if key in memo:
                return memo[key]
            trees = []
            for r in range(lo, hi + 1):
                for left in build(lo, r - 1):
                    for right in build(r + 1, hi):
                        trees.append(TreeNode(r, left, right))
            memo[key] = trees
            return trees

        return build(1, n)


# ==============================================================================
# TESTS — run:  python 012_unique_binary_search_trees_ii_solution.py
# ==============================================================================
def to_tuple(node):
    if node is None:
        return None
    return (node.val, to_tuple(node.left), to_tuple(node.right))


def is_valid_bst(node, lo=float("-inf"), hi=float("inf")):
    if node is None:
        return True
    if not (lo < node.val < hi):
        return False
    return is_valid_bst(node.left, lo, node.val) and is_valid_bst(node.right, node.val, hi)


def run_tests() -> None:
    sol = Solution()
    from math import comb

    def catalan(n):
        return comb(2 * n, n) // (n + 1)

    all_ok = True

    impls = [
        ("recursive, no memo ", sol.generateTrees),
        ("memoized on (lo,hi)", sol.generateTrees_memoized),
    ]

    for name, fn in impls:
        ok = True
        for n in (1, 2, 3, 4, 5):
            trees = fn(n)
            expected_count = catalan(n)
            all_valid = all(is_valid_bst(t) for t in trees)
            shapes = {to_tuple(t) for t in trees}
            ok &= len(trees) == expected_count == len(shapes) and all_valid
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} (n=1..5, cross-checked against Catalan(n))")

    print("\n--- n=8 (upper constraint bound), measured live ---")
    trees8 = sol.generateTrees(8)
    expected8 = catalan(8)
    print(f"  generateTrees(8) produced {len(trees8)} trees (Catalan(8) = {expected8})")
    all_ok &= len(trees8) == expected8

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
