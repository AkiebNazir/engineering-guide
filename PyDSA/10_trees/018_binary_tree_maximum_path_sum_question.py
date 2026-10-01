"""
================================================================================
QUESTION · LeetCode 124 · Binary Tree Maximum Path Sum                   [Hard]
https://leetcode.com/problems/binary-tree-maximum-path-sum/
================================================================================
A PATH in a binary tree is a sequence of nodes where each pair of adjacent
nodes in the sequence has an edge connecting them. A node can only appear in
the sequence AT MOST ONCE. Note that the path DOES NOT NEED TO PASS THROUGH
THE ROOT.

The path sum of a path is the sum of the node's values in the path.

Given the `root` of a binary tree, return the maximum path sum of ANY
non-empty path.

Example 1:
    Input:  root = [1,2,3]
    Output: 6
    Explanation: the path 2 -> 1 -> 3 has a sum of 2 + 1 + 3 = 6.

            1
          ┌─┴─┐
          2   3

Example 2:
    Input:  root = [-10,9,20,null,null,15,7]
    Output: 42
    Explanation: the path 15 -> 20 -> 7 has a sum of 15 + 20 + 7 = 42.
                 The root is NOT on the best path.

           -10
          ┌─┴──┐
          9    20
             ┌─┴─┐
            15    7

Constraints:
    The number of nodes in the tree is in the range [1, 3 * 10^4].
    -1000 <= Node.val <= 1000


WHAT MAKES THIS HARD (and it is not the recursion)
---------------------------------------------------
A legal path is a "V" (or a straight line): it goes UP from some node, turns
around at its highest point, and comes back DOWN. It may not fork twice. So
at any node there are TWO DIFFERENT quantities in play, and confusing them is
the single most common failure on this problem:

    (1) the best path THROUGH this node — it may use BOTH children, and it
        is a candidate for the final answer, but it can never be extended
        upward (a parent joining it would create a fork);

    (2) the best path that STARTS at this node and goes DOWN one side only —
        this is what the parent can extend, and it is what must be RETURNED.

You compute (1) and record it in a running global maximum. You return (2).
They are different numbers, and returning (1) upward produces answers that
correspond to no actual path in the tree.

Second trap: a child whose best downward sum is NEGATIVE should be dropped
(contribute 0), not included. Third trap: every value can be negative, so
the answer may be negative and the running maximum must not start at 0.


PROGRESSIVE HINTS
------------------
Hint 1: Where can the best path's TURNING POINT be? At exactly one node.
        So: for each node, compute the best path whose turning point is that
        node, and take the maximum over all nodes.

Hint 2: If you know, for each child, the best sum of a path going straight
        DOWN from that child, then the best path turning at this node is
        `node.val + left_down + right_down`.

Hint 3: So the recursion should return "best sum going straight down from
        here", and record `node.val + left + right` into a `nonlocal` best
        as a side effect. Two different numbers — one returned, one recorded.

Hint 4: What if `left_down` is negative? Then the path is better off not
        going that way at all. Clamp it: `max(left_down, 0)`.

Hint 5: What should the running best start at? Not 0 — all values may be
        negative, and the answer for `[-3]` is -3.


COMPLEXITY TARGET
------------------
    Time:  O(n) — one visit per node
    Space: O(h) for the recursion stack
================================================================================
"""

from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def maxPathSum(self, root: Optional[TreeNode]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — level-order (de)serialisation, LeetCode's array format
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


# ==============================================================================
# TESTS — run:  python 018_binary_tree_maximum_path_sum_question.py
# ==============================================================================
CASES = [
    ([1, 2, 3], 6),
    ([-10, 9, 20, None, None, 15, 7], 42),
    ([-3], -3),
    ([2, -1], 2),
    ([-2, -1], -1),
    ([-1, 2, 3, 4, 5], 11),
    ([2, -5, 3], 5),
    ([1, -2, -3, 1, 3, -2, None, -1], 3),
    ([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1], 48),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for vals, expected in CASES:
        try:
            got = sol.maxPathSum(build(vals))
        except Exception as exc:  # noqa: BLE001 — stub raises until implemented
            got = f"{type(exc).__name__}: {exc}"
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<48} -> {got}  "
              f"(want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
