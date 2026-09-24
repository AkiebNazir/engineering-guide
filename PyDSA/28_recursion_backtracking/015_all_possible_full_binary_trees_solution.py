"""
================================================================================
SOLUTION · LeetCode 894 · All Possible Full Binary Trees                [Medium]
https://leetcode.com/problems/all-possible-full-binary-trees/
================================================================================

THE CORE IDEA
--------------
A full binary tree (every node has 0 or 2 children) can only have an ODD
number of nodes — the root plus pairs of children forces this by a
simple parity argument. For odd `n`, split the `n - 1` non-root nodes
into a left share `L` and right share `R = n - 1 - L`, where BOTH must
themselves be odd for their subtrees to be full, then cross-product
every left shape with every right shape — the same combine pattern as
012, restricted to a smaller set of valid split points.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, NO MEMO — the version above. Recomputes
   `allPossibleFBT(k)` for a given odd `k` every time a different parent
   split needs it, similar in spirit to 012's redundant sub-range work.
   The version taught here.
2. MEMOIZED ON n — cache the list of shapes for each odd `n` the first
   time it's built. Since (unlike 012) EVERY tree of size `k` really is
   structurally interchangeable with any other size-`k` full binary tree
   for the purposes of being someone's left or right child (there's no
   "value range" tying shapes to specific positions, all node values
   are 0), memoizing purely on the integer `n` is both correct and
   effective here — a genuine improvement over 012, where memoizing had
   to key on the full `(lo, hi)` range instead.
3. BUILD FROM COUNTS FIRST (analogous to 011's approach for 012) — not
   applicable as a shortcut here either, for the same reason as 012:
   every distinct shape still has to be constructed.


================================================================================
STEP BY STEP TRACE — allPossibleFBT(5)
================================================================================
    allPossibleFBT(5): n-1 = 4 nodes to split between left (L) and right (R)
      L must be odd, R = 4 - L must also be odd -> L in {1, 3}
      L=1, R=3: leftShapes = allPossibleFBT(1) = [leaf]
                rightShapes = allPossibleFBT(3) = [0,0,0]  (one shape)
                cross product: 1 * 1 = 1 tree: root(0, leaf, [0,0,0])
      L=3, R=1: leftShapes = allPossibleFBT(3) = [0,0,0]
                rightShapes = allPossibleFBT(1) = [leaf]
                cross product: 1 * 1 = 1 tree: root(0, [0,0,0], leaf)
    Total: 2 trees for n=5 — matches Catalan((5-1)/2) = Catalan(2) = 2.

    (L=2 or R=2 would be attempted only if L ranged over all integers,
    not just odd ones — they're skipped entirely, since a subtree of
    size 2 can never be full: one node would have exactly one child.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time                    Space                   Mutates input?  Note
    -----------------------  ----------------------  ----------------------  ---------------  --------------------------------
    Recursive, no memo      related to Catalan((n-1)/2) * n, with redundant  no               same shape as 012, odd-only splits
                             recomputation of shared smaller odd sizes
    Memoized on n            same total trees built, less redundant work     no               n alone is a valid, sufficient key here


================================================================================
EDGE CASES
================================================================================
    n even (e.g. n=2, n=4) -> []    no full binary tree has an even
                                number of nodes; must return an empty
                                list immediately, not attempt any split
                                (which would loop over an empty odd
                                range naturally, but checking explicitly
                                up front avoids relying on that
                                incidental behavior).
    n = 1              -> [leaf]    the base case: a single node, 0
                                children, itself already "full."
    n = 20 (even, upper bound) -> []  the STATED constraint's upper
                                bound happens to be even, so the actual
                                answer is empty — a reminder that
                                constraint bounds don't guarantee a
                                "real" case; n=19 (odd, near the bound)
                                is the actual stress case.
    n = 19 (odd, near upper bound) -> exercises Catalan(9) = 4862 shapes,
                                a real stress test of the cross-product
                                blowup.


================================================================================
COMMON MISTAKES
================================================================================
1. Looping `L` over ALL integers from `1` to `n - 2` instead of only ODD
   ones — attempting even `L` (and thus even `R`) wastes work calling
   `allPossibleFBT` on sizes that are guaranteed to return `[]`, and
   while this doesn't produce WRONG trees (the empty list correctly
   contributes zero to the cross product), it's needless recursive
   overhead the odd-only range avoids entirely.
2. Forgetting the `n % 2 == 0` early return — without it, the loop
   `range(1, n-1, 2)` over ODD `L` values naturally produces an empty
   range when `n` is even anyway (since `n-1` would be odd, and stepping
   by 2 from 1 might still skip past it correctly) — but relying on this
   incidental correctness instead of stating the impossibility
   explicitly is a fragile design choice a reviewer may flag.
3. Building `TreeNode(0, left, right)` but reusing the SAME cached
   `left`/`right` node objects across multiple DIFFERENT resulting trees
   under the assumption "shapes aren't mutated afterward" — true and
   harmless in THIS specific problem, same caveat as noted in 012.
4. Confusing this problem's node COUNT-based split (`L + R = n - 1`)
   with 012's VALUE-RANGE-based split (`{lo,...,r-1}` and
   `{r+1,...,hi}`) — the underlying cross-product combine step is
   identical, but what's being split (a count vs. a range of specific
   values) is genuinely different, and code that tries to reuse 012's
   exact recursion signature here will not type-check cleanly.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How many trees does allPossibleFBT(n) return, for odd n?
A: `Catalan((n-1)/2)` — verified below against the Catalan formula from
   problem 011, not merely asserted.

Q: Why can you memoize by the bare integer n here, when 012 needed to
   key on the full (lo, hi) range?
A: Every node in this problem has the same fixed value (0), so any two
   size-k full binary trees are completely interchangeable as a child of
   some larger tree — there's no positional information (like 012's
   actual node VALUES) that a bare size wouldn't already capture.

Q: What if the tree could have nodes with 0, 1, or 2 children (i.e.
   NOT required to be full)? How would the recursion change?
A: That's closer to 012's unrestricted split — `L` would range over
   EVERY value from 0 to n-1, not just odd ones, since a node with
   exactly one child becomes legal.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 012 Unique Binary Search Trees II — the same "split, cross
                                       product, build" combine pattern,
                                       splitting a value range instead of
                                       a node count.
    Topic 28, 011 Unique Binary Search Trees    — where the
                                       Catalan-number connection for this
                                       problem's counts comes from.
    LC 24 Swap Nodes in Pairs / Topic 09 (Generate Parentheses) — other
                                       "structurally constrained
                                       enumeration" recursions.
================================================================================
"""

from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def allPossibleFBT(self, n: int) -> List[Optional[TreeNode]]:
        """Recursive, cross product over odd left/right splits. No memo."""
        if n % 2 == 0:
            return []
        if n == 1:
            return [TreeNode(0)]
        trees = []
        for left_size in range(1, n - 1, 2):
            right_size = n - 1 - left_size
            for left in self.allPossibleFBT(left_size):
                for right in self.allPossibleFBT(right_size):
                    trees.append(TreeNode(0, left, right))
        return trees

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def allPossibleFBT_memoized(self, n: int) -> List[Optional[TreeNode]]:
        """Memoized on n alone (valid here since all node values are 0)."""
        memo = {}

        def build(k: int) -> List[Optional[TreeNode]]:
            if k % 2 == 0:
                return []
            if k == 1:
                return [TreeNode(0)]
            if k in memo:
                return memo[k]
            trees = []
            for left_size in range(1, k - 1, 2):
                right_size = k - 1 - left_size
                for left in build(left_size):
                    for right in build(right_size):
                        trees.append(TreeNode(0, left, right))
            memo[k] = trees
            return trees

        return build(n)


# ==============================================================================
# TESTS — run:  python 015_all_possible_full_binary_trees_solution.py
# ==============================================================================
def to_tuple(node):
    if node is None:
        return None
    return (node.val, to_tuple(node.left), to_tuple(node.right))


def is_full(node):
    if node is None:
        return True
    if (node.left is None) != (node.right is None):
        return False
    return is_full(node.left) and is_full(node.right)


def count_nodes(node):
    if node is None:
        return 0
    return 1 + count_nodes(node.left) + count_nodes(node.right)


def catalan(k):
    from math import comb
    return comb(2 * k, k) // (k + 1)


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive, no memo", sol.allPossibleFBT),
        ("memoized on n      ", sol.allPossibleFBT_memoized),
    ]

    for name, fn in impls:
        ok = True
        for n, expected_count in [(1, 1), (2, 0), (3, 1), (5, 2), (7, 5), (9, 14)]:
            trees = fn(n)
            all_full = all(is_full(t) for t in trees)
            all_sized = all(count_nodes(t) == n for t in trees)
            shapes = {to_tuple(t) for t in trees}
            ok &= (len(trees) == expected_count and all_full and all_sized
                   and len(shapes) == len(trees))
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} (n in 1,2,3,5,7,9)")

    print("\n--- confirming count matches Catalan((n-1)/2), n=1..15, measured live ---")
    mismatches = []
    for n in range(1, 16):
        trees = sol.allPossibleFBT(n)
        expected = 0 if n % 2 == 0 else catalan((n - 1) // 2)
        if len(trees) != expected:
            mismatches.append((n, len(trees), expected))
    if mismatches:
        print(f"  FAIL — mismatches: {mismatches}")
        all_ok = False
    else:
        print("  CONFIRMED: counts match Catalan((n-1)/2) for all odd n in 1..15.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
