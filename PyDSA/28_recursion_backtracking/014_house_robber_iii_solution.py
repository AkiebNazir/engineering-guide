"""
================================================================================
SOLUTION · LeetCode 337 · House Robber III                              [Medium]
https://leetcode.com/problems/house-robber-iii/
================================================================================

THE CORE IDEA
--------------
Each subtree can be summarized by exactly two numbers: the best total if
its root IS robbed, and the best total if it is NOT. Returning this PAIR
lets a parent combine both of a child's answers without ever needing to
recompute either — the canonical fix for the naive version's exponential
re-exploration, and the "return a pair" combine pattern the topic guide
calls the hallmark of this folder's hardest problems.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. NAIVE, SINGLE-VALUE RETURN — `best(node) = max(node.val + best(left.left)
   + best(left.right) + best(right.left) + best(right.right), best(left)
   + best(right))` — re-explores each grandchild's subtree from BOTH the
   "rob this node" and "skip this node" branches, causing exponential
   blowup with tree height. Priced, not the version taught, but
   measured live below via a call counter.
2. PAIR-RETURNING RECURSION — the `(robbed, notRobbed)` version above.
   O(n) time (every node visited exactly once), O(h) space (call stack).
   The version taught here.
3. ITERATIVE POST-ORDER with an explicit stack, computing the same pair
   per node bottom-up without recursion. O(n) time, O(n) space (stack +
   a dict of computed pairs, since post-order iteration needs to know
   when both children are done).


================================================================================
STEP BY STEP TRACE — rob([3,2,3,null,3,null,1])   tree: 3 -> {2 -> {None, 3}, 3 -> {None, 1}}
================================================================================
    call dfs(3)                          root
      call dfs(2)                        left child of root
        call dfs(None) -> (0, 0)           left.left
        call dfs(3) -> ?                    left.right (leaf, val 3)
          call dfs(None) -> (0,0)  twice (its own children)
          robbed = 3 + 0 + 0 = 3
          notRobbed = max(0,0) + max(0,0) = 0
          -> (3, 0)
        robbed(2) = 2 + notRobbed(left.left=0) + notRobbed(left.right=0) = 2 + 0 + 0 = 2
        notRobbed(2) = max(0,0) + max(3,0) = 0 + 3 = 3
        -> dfs(2) = (2, 3)
      call dfs(3)  [the right child of root, value 3]
        call dfs(None) -> (0,0)             right.left
        call dfs(1) -> (1, 0)                right.right (leaf, val 1)
        robbed(right-3) = 3 + 0 + 0 = 3
        notRobbed(right-3) = max(0,0) + max(1,0) = 0 + 1 = 1
        -> dfs(right-3) = (3, 1)
      robbed(root) = 3 + notRobbed(2)=3 + notRobbed(right-3)=1 = 3 + 3 + 1 = 7
      notRobbed(root) = max(2,3) + max(3,1) = 3 + 3 = 6
    dfs(root) = (7, 6) -> answer = max(7, 6) = 7

Matches the expected output of 7 (rob the two 3s and the 1).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time         Space          Mutates input?  Note
    ------------------------------  -----------  -------------  ---------------  --------------------------------
    Naive, single-value             exponential  O(h) stack     no               re-explores grandchildren, measured below
    Pair-returning recursion        O(n)         O(h) stack     no               the version taught here
    Iterative post-order w/ stack   O(n)         O(n)           no               no recursion, explicit pair storage


================================================================================
EDGE CASES
================================================================================
    root only, no children      -> rob it; `dfs(root)` returns
                                   `(root.val, 0)`, answer = root.val.
    a node with only ONE child  -> the pair formula for `robbed` and
                                   `notRobbed` still works unchanged,
                                   since the missing child's pair is
                                   `(0, 0)` from the base case — no
                                   special-casing needed.
    every node's value is 0     -> answer is 0; confirms the "rob
                                   nothing" branch is a legitimate,
                                   correctly-computed possibility, not
                                   accidentally excluded.
    a long chain (skewed tree)  -> exercises real recursion depth and
                                   confirms the pair-passing logic
                                   matches a plain linear house-robber
                                   DP on that chain (cross-checked below).


================================================================================
COMMON MISTAKES
================================================================================
1. Returning only ONE number per subtree (the naive approach) — forces
   re-deriving "what if this subtree's root were robbed vs not" from
   scratch at every ancestor that needs both answers, causing the exact
   exponential blowup naive Fibonacci has, measured live below.
2. Computing `robbed = node.val + leftRobbed + rightRobbed` (using the
   children's ROBBED values) instead of their NOT-ROBBED values — if the
   current node is robbed, its direct children CANNOT also be robbed
   (they're directly linked), so `robbed` must add `leftNotRobbed` and
   `rightNotRobbed`, never the robbed variants.
3. Computing `notRobbed = leftNotRobbed + rightNotRobbed` instead of
   `max(leftRobbed, leftNotRobbed) + max(rightRobbed, rightNotRobbed)` —
   if the CURRENT node is skipped, its children are NOT constrained at
   all; forcing them to also be skipped needlessly throws away money the
   thief could have taken.
4. Forgetting the final `max()` at the very top level — the pair
   `(robbed, notRobbed)` for the ROOT itself still represents two
   different totals; the actual answer is whichever is larger, not
   automatically `notRobbed` or `robbed`.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why does the naive version blow up exponentially, concretely?
A: `best(node)`'s "skip this node" branch calls `best(left)` and
   `best(right)` directly, while its "rob this node" branch calls
   `best(left.left)`, `best(left.right)`, `best(right.left)`,
   `best(right.right)` — these grandchild calls duplicate work already
   done (or about to be done) inside `best(left)` and `best(right))`
   themselves, and this duplication compounds at every level.

Q: How does the pair-returning fix compare to memoizing the naive
   version by node identity?
A: Both eliminate the exponential blowup and reach O(n), but the pair
   version is cleaner: it computes BOTH answers a parent could ever need
   in a single bottom-up pass, with no need for a separate memo
   structure — the "memoization" is built into the return value's shape.

Q: How does this relate to the classic linear House Robber (LC 198)?
A: Same rob/skip decision and "no two adjacent" constraint, but LC 198's
   "adjacent" is array-index adjacency (handled with a simple 1D DP),
   while this problem's "adjacent" is tree parent-child adjacency
   (handled with the pair-per-subtree recursion). Verified below by
   confirming the tree version matches a linear DP when the tree happens
   to be a straight chain.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 198  House Robber              — the linear-array version of the
                                        same rob/skip constraint.
    LC 213  House Robber II           — the circular-array variant.
    Topic 28, 013 Sum Root to Leaf Numbers — contrast: state flows DOWN
                                        there, UP (as a pair) here.
================================================================================
"""

from typing import Optional, Tuple


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def rob(self, root: Optional[TreeNode]) -> int:
        """Pair-returning recursion. O(n) time, O(h) space."""
        return max(self._dfs(root))

    def _dfs(self, node: Optional[TreeNode]) -> Tuple[int, int]:
        if node is None:
            return 0, 0
        left_robbed, left_not_robbed = self._dfs(node.left)
        right_robbed, right_not_robbed = self._dfs(node.right)
        robbed = node.val + left_not_robbed + right_not_robbed
        not_robbed = max(left_robbed, left_not_robbed) + max(right_robbed, right_not_robbed)
        return robbed, not_robbed

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def rob_naive_single_value(self, root: Optional[TreeNode], calls: list = None) -> int:
        """Naive single-value, re-explores grandchildren. `calls` counts total calls."""
        if calls is not None:
            calls[0] += 1
        if root is None:
            return 0

        def grandchildren_sum(node):
            total = 0
            if node.left:
                total += (self.rob_naive_single_value(node.left.left, calls)
                          + self.rob_naive_single_value(node.left.right, calls))
            if node.right:
                total += (self.rob_naive_single_value(node.right.left, calls)
                          + self.rob_naive_single_value(node.right.right, calls))
            return total

        rob_root = root.val + grandchildren_sum(root)
        skip_root = (self.rob_naive_single_value(root.left, calls)
                     + self.rob_naive_single_value(root.right, calls))
        return max(rob_root, skip_root)


# ==============================================================================
# TESTS — run:  python 014_house_robber_iii_solution.py
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
    ([3, 2, 3, None, 3, None, 1], 7),
    ([3, 4, 5, 1, 3, None, 1], 9),
    ([1], 1),
    ([4, 1, None, 2, None, 3], 7),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("pair-returning recursion", sol.rob),
        ("naive single-value      ", sol.rob_naive_single_value),
    ]

    for name, fn in impls:
        ok = all(fn(build(values)) == expected for values, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- naive version's call-count blowup on a deep chain, measured live ---")
    print(f"  {'chain length':>14} {'total calls (naive)':>22}")
    for length in (4, 8, 12):
        chain = [1]
        values = [1]
        for _ in range(length - 1):
            values.extend([1, None])  # each node has only a left child -> a straight chain
        root = build(values)
        calls = [0]
        sol.rob_naive_single_value(root, calls)
        print(f"  {length:>14} {calls[0]:>22}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
