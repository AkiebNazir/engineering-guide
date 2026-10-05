"""
================================================================================
SOLUTION · LeetCode 129 · Sum Root to Leaf Numbers                      [Medium]
https://leetcode.com/problems/sum-root-to-leaf-numbers/
================================================================================

THE CORE IDEA
--------------
Carry "the number built so far" DOWN the recursion as an accumulator
parameter, growing it by one digit at each node (`* 10 + node.val`).
When a call reaches a true leaf, the accumulator IS one complete
root-to-leaf number — no further work needed, just return it. The sum
across different leaves is combined by ADDING each child's returned
subtotal at every internal node the recursion passes back through. This
is the "pass extra state going down" pattern named in the topic guide,
in contrast to 011/012 where state only ever flowed UP.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, ACCUMULATOR PASSED DOWN — the version above. O(n) time
   (every node visited once), O(h) space (call stack depth = tree
   height, and the constraint caps it at 10). The version taught here.
2. ITERATIVE, EXPLICIT STACK OF (node, numberSoFar) PAIRS — push
   `(root, 0)`, pop, compute the updated number, push children with it
   (or add to the total if at a leaf). O(n) time, O(n) space worst case
   (a maximally unbalanced tree keeps every ancestor's pair on the
   stack). No recursion at all.
3. DFS WITHOUT AN ACCUMULATOR PARAMETER, using a nonlocal/instance
   running total updated only at leaves, and recomputing the digit
   string by walking a path list — priced, not written: strictly worse,
   since it either needs a mutable path list threaded through (more
   state to manage) or repeats work recomputing prefixes.


================================================================================
STEP BY STEP TRACE — sumNumbers([4,9,0,5,1])   tree: 4 -> {9 -> {5, 1}, 0}
================================================================================
    call dfs(node=4, numberSoFar=0)
      numberSoFar = 0*10 + 4 = 4          (not a leaf: has left=9, right=0)
      call dfs(node=9, numberSoFar=4)
        numberSoFar = 4*10 + 9 = 49        (not a leaf: has left=5, right=1)
        call dfs(node=5, numberSoFar=49)
          numberSoFar = 49*10 + 5 = 495     (leaf) -> return 495
        call dfs(node=1, numberSoFar=49)
          numberSoFar = 49*10 + 1 = 491     (leaf) -> return 491
        dfs(9) = 495 + 491 = 986
      call dfs(node=0, numberSoFar=4)
        numberSoFar = 4*10 + 0 = 40         (leaf) -> return 40
      dfs(4) = 986 + 40 = 1026

Result: 1026, matching the example exactly (495 + 491 + 40).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time   Space          Mutates input?  Note
    ---------------------------------  -----  -------------  ---------------  --------------------------------
    Recursive, accumulator down       O(n)   O(h) stack     no               h capped at 10 by constraint
    Iterative, explicit stack of pairs O(n)   O(n) worst case no             no recursion at all


================================================================================
EDGE CASES
================================================================================
    root = [0]           -> 0    a single node, itself a leaf, with
                                  value 0; the "number" formed is just
                                  0, not skipped or treated as missing.
    a node with ONLY a left child (no right) -> the recursion must skip
                                  the missing right child entirely, not
                                  attempt `dfs(None, ...)`, which would
                                  crash on `node.val`.
    a fully left-skewed tree (depth up to 10 per the constraint) ->
                                  exercises real recursion depth without
                                  approaching Python's recursion limit.
    every node value is 9 (all-9s path) -> the accumulated number grows
                                  correctly via `*10 + 9` at every step,
                                  no special digit-carry logic needed
                                  (unlike arithmetic addition problems).


================================================================================
COMMON MISTAKES
================================================================================
1. Checking only `node.left is None` (or only `node.right is None`) to
   decide "this is a leaf," instead of requiring BOTH to be None — a
   node with just one child is NOT a leaf and must still recurse into
   its remaining child, or that entire subtree's numbers are silently
   dropped from the sum.
2. Recursing into `node.left` and `node.right` unconditionally without
   checking they exist — crashes with `AttributeError` on `None.val` the
   moment any node has fewer than two children, which is the common case
   for any non-full binary tree.
3. Updating `numberSoFar` AFTER checking whether the current node is a
   leaf, instead of before — this either omits the leaf's own digit from
   the final number or requires an awkward reordering; updating first,
   unconditionally, then checking leaf-ness keeps the logic in one
   consistent order.
4. Forgetting that "the sum across leaves" is built by ADDING each
   child's returned subtotal at every ancestor on the way back up — a
   version that tries to accumulate into a single shared running total
   via a mutable outer variable works too, but risks double-counting or
   missing branches if the addition isn't placed at exactly the right
   point in each call.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you solve this without recursion?
A: Yes — an explicit stack holding `(node, numberSoFar)` pairs, same
   logic, iterative instead of recursive.

Q: What if the tree could be arbitrarily deep — would recursion still be
   safe?
A: Not necessarily — Python's default recursion limit (~1000) would be
   at risk for a very deep, unbalanced tree. This problem's own
   constraint (depth <= 10) makes that a non-issue here, but the
   iterative stack version has no such limit regardless of depth.

Q: How would this change if you needed each individual root-to-leaf
   number, not just their sum?
A: Same recursion, but instead of adding subtotals together, collect
   each leaf's `numberSoFar` into a list and return/extend lists instead
   of summing integers — a "collect leaves" variant of the same
   accumulator-passed-down pattern.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 257  Binary Tree Paths          — the same accumulator-passed-down
                                        pattern, collecting path STRINGS
                                        instead of summing numbers.
    Topic 28, 014 House Robber III     — a tree recursion where state
                                        flows UP instead (a pair of
                                        values per node), for contrast.
    Topic 10 Trees (topic-level)       — general root-to-leaf traversal
                                        patterns.
================================================================================
"""

from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def sumNumbers(self, root: Optional[TreeNode]) -> int:
        """Recursive, accumulator passed down. O(n) time, O(h) space."""
        return self._dfs(root, 0)

    def _dfs(self, node: Optional[TreeNode], number_so_far: int) -> int:
        number_so_far = number_so_far * 10 + node.val
        if node.left is None and node.right is None:
            return number_so_far
        total = 0
        if node.left:
            total += self._dfs(node.left, number_so_far)
        if node.right:
            total += self._dfs(node.right, number_so_far)
        return total

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def sumNumbers_iterative(self, root: Optional[TreeNode]) -> int:
        """Iterative, explicit stack of (node, numberSoFar) pairs."""
        if root is None:
            return 0
        total = 0
        stack = [(root, 0)]
        while stack:
            node, number_so_far = stack.pop()
            number_so_far = number_so_far * 10 + node.val
            if node.left is None and node.right is None:
                total += number_so_far
                continue
            if node.left:
                stack.append((node.left, number_so_far))
            if node.right:
                stack.append((node.right, number_so_far))
        return total


# ==============================================================================
# TESTS — run:  python 013_sum_root_to_leaf_numbers_solution.py
# ==============================================================================
def build(values):
    if not values or values[0] is None:
        return None
    nodes = [TreeNode(v) if v is not None else None for v in values]
    kids = iter(nodes[1:])
    for node in nodes:
        if node is None:
            continue
        node.left = next(kids, None)
        node.right = next(kids, None)
    return nodes[0]


CASES = [
    ([1, 2, 3], 25),
    ([4, 9, 0, 5, 1], 1026),
    ([0], 0),
    ([9, 9, 9, 9], 1098),  # tree: 9 -> {9 -> 9 (left-only), 9} ; paths 999, 99
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive, accumulator down", sol.sumNumbers),
        ("iterative, explicit stack  ", sol.sumNumbers_iterative),
    ]

    for name, fn in impls:
        ok = all(fn(build(values)) == expected for values, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
