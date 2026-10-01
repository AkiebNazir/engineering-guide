"""
================================================================================
QUESTION · LeetCode 199 · Binary Tree Right Side View                  [Medium]
https://leetcode.com/problems/binary-tree-right-side-view/
================================================================================
Given the `root` of a binary tree, imagine yourself standing on the RIGHT
side of it. Return the values of the nodes you can see, ordered from top to
bottom.

Example 1:
    Input:  root = [1,2,3,null,5,null,4]
    Output: [1,3,4]

            1               <- you see 1
          ┌─┴─┐
          2   3             <- you see 3 (2 is hidden behind it)
           └┐   └┐
            5    4          <- you see 4 (5 is hidden behind it)

Example 2:
    Input:  root = [1,2,3,4]
    Output: [1,3,4]

            1               <- you see 1
          ┌─┴─┐
          2   3             <- you see 3
        ┌─┘
        4                   <- you see 4: nothing on level 2 is to its right!

Example 3:
    Input:  root = [1,null,3]
    Output: [1,3]

Example 4:
    Input:  root = []
    Output: []

Constraints:
    The number of nodes in the tree is in the range [0, 100].
    -100 <= Node.val <= 100


⚠️ THE TRAP THIS PROBLEM IS BUILT AROUND
------------------------------------------
"The right side view" is NOT "the path you get by following `.right`
repeatedly." Example 2 above is the counterexample: following `.right` from
the root gives 1 -> 3 -> (nothing) = [1, 3], and misses 4 entirely — because
node 4 is the ONLY node on its level, so it is visible from the right even
though it is a LEFT child reached through a LEFT child.

The correct definition is per-LEVEL: the view is the LAST node of each level
in left-to-right order. Get that definition right and the problem is easy;
get it wrong and you will pass Example 1 and fail Example 2.


PROGRESSIVE HINTS
------------------
Hint 1: Restate the question as "for each level, which node is furthest
        right?" Nothing about pointer direction; everything about levels.

Hint 2: You already know how to group a traversal by level (problem 013).
        Take `level[-1]`.

Hint 3: For the O(h)-space DFS version: recurse RIGHT child first, carrying
        `depth`. The FIRST node you ever reach at a given depth is the
        rightmost one at that depth.

Hint 4: "First arrival at this depth" is testable with `len(out) == depth` —
        the same growth condition as 013's DFS variant.


COMPLEXITY TARGET
------------------
    Time:  O(n) — every node visited once
    Space: O(w) for the BFS version (w = widest level),
           O(h) for the DFS version (h = height)
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
    def rightSideView(self, root: Optional[TreeNode]) -> List[int]:
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
# TESTS — run:  python 014_binary_tree_right_side_view_question.py
# ==============================================================================
CASES = [
    ([1, 2, 3, None, 5, None, 4], [1, 3, 4]),
    ([1, 2, 3, 4], [1, 3, 4]),
    ([1, None, 3], [1, 3]),
    ([], []),
    ([1], [1]),
    ([1, 2], [1, 2]),
    ([1, 2, 3, 4, None, None, None, 5], [1, 3, 4, 5]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for vals, expected in CASES:
        try:
            got = sol.rightSideView(build(vals))
        except Exception as exc:  # noqa: BLE001 — stub raises until implemented
            got = f"{type(exc).__name__}: {exc}"
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<38} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
