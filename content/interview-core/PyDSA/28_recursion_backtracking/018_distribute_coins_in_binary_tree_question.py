"""
================================================================================
LeetCode 979 · Distribute Coins in Binary Tree                          [Medium]
https://leetcode.com/problems/distribute-coins-in-binary-tree/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
You are given the root of a binary tree with `n` nodes where each
`node` in the tree has `node.val` coins. There are `n` coins total
throughout the whole tree.

In one move, we may choose two adjacent nodes and move one coin from
one node to another. A move may be from parent to child, or from child
to parent.

Return the minimum number of moves required to make every node have
exactly one coin.

EXAMPLES
--------
Example 1:
    Input:  root = [3,0,0]
    Output: 2
    Explanation: From the root of the tree, we move one coin to its
    left child, and one coin to its right child.

Example 2:
    Input:  root = [0,3,0]
    Output: 3
    Explanation: From the left child of the root, we move two coins to
    the root [taking two moves]. Then, we move one coin from the root
    of the tree to the right child.

CONSTRAINTS
-----------
    The number of nodes in the tree is n.
    1 <= n <= 100
    0 <= Node.val <= n
    The sum of all Node.val is n.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Every EDGE in the tree is crossed by some number of coin-moves — the key
insight is that the number of moves across a given edge is exactly the
absolute value of the "excess" (or "deficit") flowing through that
subtree: if a subtree has `k` nodes and `total` coins, it has
`total - k` excess coins that must flow OUT through the edge to its
parent (if positive), or `k - total` coins that must flow IN (if
negative). Either way, `|total - k|` coins must cross that single edge,
regardless of direction — and the ANSWER is the sum of this quantity
over every edge in the tree.

    dfs(node) -> excess (coins - required, for this whole subtree):
        if node is None: return 0                            <- base case: no coins, no nodes needed
        leftExcess = dfs(node.left)
        rightExcess = dfs(node.right)
        self.moves += abs(leftExcess) + abs(rightExcess)       <- accumulate moves for BOTH edges below this node
        return node.val + leftExcess + rightExcess - 1          <- this subtree's own excess, passed up

WHAT TO THINK ABOUT
--------------------
1. What does "excess" mean for a subtree, precisely — coins minus how
   many nodes there are to fill? Why can it be negative?
2. Why is the number of moves across ONE edge exactly `abs(childExcess)`,
   regardless of whether the excess is positive (coins flow up) or
   negative (coins flow down)?
3. Where does the RUNNING TOTAL of moves get accumulated — at every
   single node, or only at the leaves? Why?
4. What does the recursive call RETURN versus what does it ACCUMULATE
   into a running total — are these the same value, or two genuinely
   different pieces of information handled differently?

PROGRESSIVE HINTS
------------------
Hint 1: Define `excess(subtree) = (total coins in subtree) - (number
        of nodes in subtree)`. A subtree with excess 0 is already
        "balanced" internally, needing no coins moved across its own
        parent edge.
Hint 2: Base case: an empty subtree (`node is None`) has 0 coins and 0
        nodes, so excess is trivially 0 and contributes to `abs()` as 0
        (no edge exists to a null child anyway).
Hint 3: For a real node, recursively get `leftExcess` and `rightExcess`
        from its children, add `abs(leftExcess) + abs(rightExcess)` to
        a running move counter (these are exactly the moves needed
        across the two edges below `node`), then return
        `node.val + leftExcess + rightExcess - 1` as THIS subtree's own
        excess (the `-1` accounts for `node` itself needing exactly 1
        coin).
Hint 4: Use an instance attribute (or a `nonlocal` counter in a nested
        function) to accumulate moves across the whole traversal, since
        the RETURN value at each level is deliberately a different
        thing (this subtree's excess, needed by the PARENT) than the
        cumulative move count (needed by the caller of the whole
        function).

COMPLEXITY TARGET
------------------
    Recursive: O(n) time (every node visited once), O(h) space (call
               stack, h = tree height)
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
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 018_distribute_coins_in_binary_tree_question.py
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


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([3, 0, 0], 2),
        ([0, 3, 0], 3),
        ([1, 0, 2], 2),
        ([1, 0, 0, None, 3], 4),
    ]
    passed = 0
    for values, expected in cases:
        root = build(values)
        got = sol.distributeCoins(root)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  distributeCoins({values}) -> {got}  (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
