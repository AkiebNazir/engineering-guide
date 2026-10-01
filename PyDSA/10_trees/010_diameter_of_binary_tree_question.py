"""
================================================================================
QUESTION · LeetCode 543 · Diameter of Binary Tree                       [Easy]
https://leetcode.com/problems/diameter-of-binary-tree/
================================================================================

Given the `root` of a binary tree, return the length of the **diameter** of
the tree.

The diameter of a binary tree is the length of the LONGEST PATH between any
two nodes in the tree. This path may or may not pass through the root.

The length of a path between two nodes is represented by the number of
EDGES between them (NOT the number of nodes).

--------------------------------------------------------------------------------
EXAMPLE 1
--------------------------------------------------------------------------------
    Input:  root = [1,2,3,4,5]
    Output: 3
    Explanation: 3 is the length of the path [4,2,1,3] or [5,2,1,3].

            1
          ┌─┴─┐
          2   3
        ┌─┴─┐
        4   5

    The longest path is 4 -> 2 -> 1 -> 3 (or 5 -> 2 -> 1 -> 3): 3 edges.
    Note it does NOT go through node 5 (or 4) at all, and it DOES pass
    through the root here — but that is not guaranteed in general (see
    example 2 and the hints below).

--------------------------------------------------------------------------------
EXAMPLE 2
--------------------------------------------------------------------------------
    Input:  root = [1,2]
    Output: 1
    Explanation: the only edge, between node 1 and node 2.

--------------------------------------------------------------------------------
CONSTRAINTS
--------------------------------------------------------------------------------
    - The number of nodes in the tree is in the range [1, 10^4].
    - -100 <= Node.val <= 100

--------------------------------------------------------------------------------
HINTS (progressive — try to solve it before reading further down)
--------------------------------------------------------------------------------
    Hint 1: For ANY single node, if you know the height of its left subtree
            and the height of its right subtree, can you express the length
            of the longest path that turns around AT that node?

    Hint 2: To answer hint 1 for every node, you need the HEIGHT of every
            node's subtrees — and height is naturally computed bottom-up
            (postorder: children before parent).

    Hint 3: The diameter you're asked for is a maximum over EVERY node in
            the tree, not just the root. The path that wins does not have
            to pass through the root at all (contrast this with example 1,
            where it happens to).

    Hint 4: The value a node needs to RETURN to its parent (so the parent
            can keep computing heights) is NOT the same value you want to
            RECORD as a diameter candidate at that node. You need two
            different numbers per node, computed in one pass.

    Hint 5: Watch the units. A single node has diameter 0 (no edges at
            all). Decide up front whether your `height(None)` returns 0 or
            something else, and be consistent — mixing "edges" and "nodes"
            is the most common way to be off by one here.

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
    def diameterOfBinaryTree(self, root: Optional[TreeNode]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS
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
# TESTS — run:  python 010_diameter_of_binary_tree_question.py
# ==============================================================================
CASES = [
    ([1, 2, 3, 4, 5], 3),
    ([1, 2], 1),
    ([1], 0),
    ([1, 2, 3], 2),
    ([1, 2, 3, 4, None, None, 5, 6], 5),
    ([1, 2, None, 3, None, 4, None, 5], 4),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for vals, expected in CASES:
        got = sol.diameterOfBinaryTree(build(vals))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<40} -> {got!r:>6}  "
              f"(want {expected})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
