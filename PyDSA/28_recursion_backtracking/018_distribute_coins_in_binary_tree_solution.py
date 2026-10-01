"""
================================================================================
SOLUTION · LeetCode 979 · Distribute Coins in Binary Tree               [Medium]
https://leetcode.com/problems/distribute-coins-in-binary-tree/
================================================================================

THE CORE IDEA
--------------
Every edge in the tree gets crossed by exactly `abs(excess)` coin-moves,
where `excess` is "coins in the subtree below this edge minus nodes in
that subtree" — a positive excess must flow UP through the edge, a
negative excess (deficit) must flow DOWN, and either way the coin COUNT
crossing is the absolute value. The recursion returns each subtree's
excess (what the PARENT needs), while separately ACCUMULATING the move
total into a running counter — two genuinely different pieces of
information handled two different ways, unlike every earlier "return a
pair" problem where both pieces flowed through the return value itself.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, EXCESS RETURNED + MOVES ACCUMULATED SEPARATELY — the
   version above, using an instance attribute (or a mutable list cell)
   to accumulate moves while the excess flows back through normal
   return values. O(n) time, O(h) space (call stack). The version
   taught here.
2. RECURSIVE, RETURN A PAIR (excess, movesSoFar) — fold the accumulator
   INTO the return value as a second element, summing the children's
   move-counts explicitly at each level instead of using external
   mutable state. Same complexity; purely a style choice between
   "accumulate via shared state" and "accumulate via an explicit second
   return value," worth naming since 014/017 both used the latter style.
3. ITERATIVE POST-ORDER with an explicit stack, computing excess
   bottom-up and accumulating moves in a local variable, no recursion.
   O(n) time, O(n) space (stack).


================================================================================
STEP BY STEP TRACE — distributeCoins([0,3,0])   tree: 0 -> {3, 0}
================================================================================
    call dfs(root=0)
      call dfs(left=3)             a leaf with 3 coins
        call dfs(None) -> 0          (twice, for its own null children)
        moves += |0| + |0| = 0
        excess = 3 + 0 + 0 - 1 = 2      [3 coins, 1 node needed -> 2 excess]
        return 2
      call dfs(right=0)            a leaf with 0 coins
        call dfs(None) -> 0          (twice)
        moves += 0
        excess = 0 + 0 + 0 - 1 = -1     [0 coins, 1 node needed -> deficit of 1]
        return -1
      leftExcess=2, rightExcess=-1
      moves += |2| + |-1| = 2 + 1 = 3
      excess(root) = 0 + 2 + (-1) - 1 = 0    [not used further, root has no parent]

Total moves = 3, matching the expected output exactly (2 coins flow down
from the left child to the root, 1 coin then flows from the root to the
right child — or equivalently, 2 moves left-to-root plus 1 move
root-to-right, 3 total).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time   Space         Mutates input?  Note
    -------------------------------------  -----  ------------  ---------------  --------------------------------
    Recursive, excess ret. + moves accum. O(n)   O(h) stack    no               shared-state accumulator
    Recursive, return (excess, moves) pair O(n)   O(h) stack    no               accumulator folded into return value
    Iterative post-order, explicit stack   O(n)   O(n)          no               no recursion


================================================================================
EDGE CASES
================================================================================
    a single node with exactly 1 coin  -> 0 moves; excess is `1 + 0 + 0
                                - 1 = 0`, no edges exist at all to cross.
    every node already has exactly 1 coin -> 0 moves overall; every
                                subtree's excess resolves to exactly 0
                                at every level, contributing nothing to
                                the running total.
    all coins concentrated at one deep leaf, every other node has 0
                                -> moves accumulate along the ENTIRE
                                path from that leaf to the root, since
                                every edge along the way has a nonzero
                                excess/deficit crossing it.
    a node with only one child (not two) -> the missing child's
                                recursive call correctly returns 0
                                (base case), contributing `abs(0) = 0`
                                extra moves for a nonexistent edge — no
                                special-casing needed.


================================================================================
COMMON MISTAKES
================================================================================
1. Accumulating `leftExcess + rightExcess` (without `abs()`) into the
   move total instead of `abs(leftExcess) + abs(rightExcess)` — a
   negative excess (deficit) still requires coins to physically cross
   that edge (just in the opposite direction), so omitting `abs()`
   under-counts (or even cancels out) moves whenever excesses have
   mixed signs.
2. Forgetting the `- 1` in `node.val + leftExcess + rightExcess - 1` —
   this fails to account for the current node itself needing exactly
   one coin, causing every subtree's excess to be off by exactly 1 at
   every level (compounding as the recursion unwinds toward the root).
3. Returning the ACCUMULATED MOVE COUNT from `dfs` instead of the
   subtree's EXCESS — these are two different quantities serving two
   different purposes (excess flows to the parent for further
   computation; the move count is a running total across the WHOLE
   tree) — conflating them breaks the recursion's correctness the
   moment a parent tries to use a "move count" as if it were an
   "excess."
4. Using a plain Python `int` as a closure variable and trying to
   `+=` it inside a nested function without `nonlocal` — raises
   `UnboundLocalError` in Python (ints are immutable, so a bare
   assignment inside a nested scope creates a new local instead of
   updating the enclosing one); the instance-attribute or
   single-element-list-cell tricks avoid this specific pitfall.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why is the number of moves across an edge exactly `abs(excess)`,
   not something more complex?
A: Each move only ever transfers ONE coin across ONE edge. If a subtree
   needs a net `k` coins to flow across its single connecting edge
   (in either direction), that requires exactly `k` separate moves
   across that edge — no move can be "skipped" or "combined," and no
   fewer than `k` moves can satisfy the requirement either.

Q: Can this be done without recursion?
A: Yes — an iterative post-order traversal (explicit stack, processing
   a node only after both its children are done) computes the same
   excess values bottom-up without a call stack.

Q: Does the ORDER coins are moved in matter for computing the minimum,
   or just the total count?
A: Only the total count matters for this problem's answer — the
   `abs(excess)` sum gives the minimum number of moves regardless of
   which specific sequence of parent/child transfers is chosen to
   realize it.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 014 House Robber III      — another per-node recursion
                                          returning derived subtree
                                          information, there a full
                                          pair instead of a
                                          separately-accumulated total.
    Topic 28, 019 LCA of Deepest Leaves — another tree recursion needing
                                          two DIFFERENT kinds of
                                          information to flow
                                          differently (depth vs. the
                                          actual LCA node).
    Topic 04 Prefix Sum (topic-level)   — the general "running total /
                                          balance" accounting idea, in
                                          array form instead of on a
                                          tree.
================================================================================
"""

from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def distributeCoins(self, root: Optional[TreeNode]) -> int:
        """Recursive: excess returned, moves accumulated via instance state."""
        self._moves = 0
        self._dfs(root)
        return self._moves

    def _dfs(self, node: Optional[TreeNode]) -> int:
        if node is None:
            return 0
        left_excess = self._dfs(node.left)
        right_excess = self._dfs(node.right)
        self._moves += abs(left_excess) + abs(right_excess)
        return node.val + left_excess + right_excess - 1

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def distributeCoins_pair_return(self, root: Optional[TreeNode]) -> int:
        """Recursive, folds the move-count accumulator into the return value."""
        def dfs(node):
            if node is None:
                return 0, 0  # (excess, moves)
            left_excess, left_moves = dfs(node.left)
            right_excess, right_moves = dfs(node.right)
            moves = left_moves + right_moves + abs(left_excess) + abs(right_excess)
            excess = node.val + left_excess + right_excess - 1
            return excess, moves

        return dfs(root)[1]

    def distributeCoins_iterative(self, root: Optional[TreeNode]) -> int:
        """Iterative post-order, explicit stack, no recursion."""
        if root is None:
            return 0
        moves = 0
        excess = {}
        stack = [(root, False)]
        while stack:
            node, visited_children = stack.pop()
            if node is None:
                continue
            if visited_children:
                left_excess = excess.get(node.left, 0)
                right_excess = excess.get(node.right, 0)
                moves += abs(left_excess) + abs(right_excess)
                excess[node] = node.val + left_excess + right_excess - 1
            else:
                stack.append((node, True))
                stack.append((node.left, False))
                stack.append((node.right, False))
        return moves


# ==============================================================================
# TESTS — run:  python 018_distribute_coins_in_binary_tree_solution.py
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
    ([3, 0, 0], 2),
    ([0, 3, 0], 3),
    ([1, 0, 2], 2),
    ([1, 0, 0, None, 3], 4),
    ([1], 0),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive, shared-state accum", sol.distributeCoins),
        ("recursive, (excess,moves) pair", sol.distributeCoins_pair_return),
        ("iterative post-order          ", sol.distributeCoins_iterative),
    ]

    for name, fn in impls:
        ok = all(fn(build(values)) == expected for values, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
