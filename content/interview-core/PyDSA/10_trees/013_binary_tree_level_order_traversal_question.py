"""
================================================================================
QUESTION · LeetCode 102 · Binary Tree Level Order Traversal            [Medium]
https://leetcode.com/problems/binary-tree-level-order-traversal/
================================================================================
Given the `root` of a binary tree, return the level order traversal of its
nodes' values — i.e. from left to right, level by level.

Example 1:
    Input:  root = [3,9,20,null,null,15,7]
    Output: [[3],[9,20],[15,7]]

            3               <- level 0
          ┌─┴──┐
          9    20           <- level 1
             ┌─┴─┐
            15    7         <- level 2

Example 2:
    Input:  root = [1]
    Output: [[1]]

Example 3:
    Input:  root = []
    Output: []

Constraints:
    The number of nodes in the tree is in the range [0, 2000].
    -1000 <= Node.val <= 1000


WHY THIS PROBLEM MATTERS
-------------------------
This is the PARENT of an entire family. Once you can group a traversal by
level, these are all one-line edits on top of it:

    LC 107  Level Order Traversal II   -> reverse the output list
    LC 103  Zigzag Level Order          -> reverse every other level
    LC 199  Right Side View              -> take level[-1]
    LC 637  Average of Levels            -> sum(level) / len(level)
    LC 515  Largest Value in Each Row     -> max(level)
    LC 1161 Maximum Level Sum             -> argmax over sum(level)

So the goal is not "solve 102"; it is to own the level-grouping idiom so
tightly that all six become the same problem.


PROGRESSIVE HINTS
------------------
Hint 1: A queue visits nodes in level order automatically — but a plain
        queue drain gives you one FLAT list. You need to know where each
        level ends.

Hint 2: At the top of each outer iteration, the queue contains EXACTLY the
        nodes of one level and nothing else. So snapshot its length first,
        then pop exactly that many nodes.

Hint 3: `for _ in range(len(q))` — `len(q)` is evaluated ONCE, before the
        loop body starts appending children. That single expression is the
        whole trick.

Hint 4: Use `collections.deque` and `popleft()`, not a list and `pop(0)`.
        A list's `pop(0)` shifts every remaining element (O(n)); on a wide
        tree that turns an O(n) traversal into O(n^2).


COMPLEXITY TARGET
------------------
    Time:  O(n) — every node enqueued once, dequeued once
    Space: O(w) where w is the maximum level width (up to n/2 for the
           bottom level of a perfect tree), plus O(n) for the output
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
    def levelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
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
# TESTS — run:  python 013_binary_tree_level_order_traversal_question.py
# ==============================================================================
CASES = [
    ([3, 9, 20, None, None, 15, 7], [[3], [9, 20], [15, 7]]),
    ([1], [[1]]),
    ([], []),
    ([1, 2, 3, 4, 5, 6, 7], [[1], [2, 3], [4, 5, 6, 7]]),
    ([1, 2, None, 3, None, 4], [[1], [2], [3], [4]]),
    ([1, None, 2, None, 3], [[1], [2], [3]]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for vals, expected in CASES:
        try:
            got = sol.levelOrder(build(vals))
        except Exception as exc:  # noqa: BLE001 — stub raises until implemented
            got = f"{type(exc).__name__}: {exc}"
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<34} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
