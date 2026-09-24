"""
================================================================================
QUESTION · LeetCode 1448 · Count Good Nodes in Binary Tree             [Medium]
https://leetcode.com/problems/count-good-nodes-in-binary-tree/
================================================================================
Given a binary tree `root`, a node X in the tree is named GOOD if in the path
from root to X there are no nodes with a value GREATER than X.

Return the number of good nodes in the binary tree.

Example 1:
    Input:  root = [3,1,4,3,null,1,5]
    Output: 4

            3                 <- GOOD (the root is always good)
          ┌─┴──┐
          1    4              <- 4 is GOOD (path max before it is 3)
        ┌─┘  ┌─┴─┐               1 is not (3 > 1 on its path)
        3    1    5           <- 3 is GOOD (path 3->1->3, max 3, 3 >= 3)
                                 5 is GOOD (path 3->4->5, max 4, 5 >= 4)
                                 1 is not (path max 4 > 1)
    Good nodes: 3 (root), 4, 3, 5 -> 4

Example 2:
    Input:  root = [3,3,null,4,2]
    Output: 3

            3                 <- GOOD
        ┌───┘
        3                     <- GOOD (3 >= 3; the test is >=, not >)
      ┌─┴─┐
      4    2                  <- 4 is GOOD, 2 is not
    Good nodes: 3, 3, 4 -> 3

Example 3:
    Input:  root = [1]
    Output: 1
    Explanation: The root is always a good node.

Constraints:
    The number of nodes in the binary tree is in the range [1, 10^5].
    Each node's value is between [-10^4, 10^4].


WHAT THIS PROBLEM IS TEACHING
------------------------------
This is the ARCHETYPE of the top-down pattern. "Good" is defined by a node's
ANCESTORS, so no amount of information returned upward from a node's
children can decide it. The only thing that can travel from an ancestor to a
descendant is a PARAMETER, and the only parameter you need here is one
integer: the maximum value seen so far on the path.

Contrast with the other big tree pattern (bottom-up / postorder aggregate,
e.g. maximum depth, diameter, balanced): those compute a property of a
node's DESCENDANTS and return it upward. Ask which direction the information
flows and the pattern picks itself.


PROGRESSIVE HINTS
------------------
Hint 1: What exactly do you need to know at node X to decide whether X is
        good? Not the whole path — just one number from it.

Hint 2: That number is `max(values on the path from root to X's parent)`.
        Compute it on the way DOWN and hand it to each child.

Hint 3: `go(node, best)` where `best` is the max so far. X is good iff
        `node.val >= best`. Recurse with `max(best, node.val)`.

Hint 4: What should `best` be at the root? Not 0 — values can be negative.
        `root.val` (making the root trivially good) or `float("-inf")` both
        work; 0 does not.


COMPLEXITY TARGET
------------------
    Time:  O(n) — one visit per node, O(1) work each
    Space: O(h) for the recursion stack (h = height; O(n) worst case on a
           skewed tree, and n can be 10^5 here — mind the recursion limit)
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
    def goodNodes(self, root: Optional[TreeNode]) -> int:
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
# TESTS — run:  python 015_count_good_nodes_in_binary_tree_question.py
# ==============================================================================
CASES = [
    ([3, 1, 4, 3, None, 1, 5], 4),
    ([3, 3, None, 4, 2], 3),
    ([1], 1),
    ([5, 1, None, 3], 1),
    ([-1, -2, -3], 1),
    ([2, 4, 4, 4, None, None, 5, None, None, 4, 4], 5),
    ([9, None, 3, 6], 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for vals, expected in CASES:
        try:
            got = sol.goodNodes(build(vals))
        except Exception as exc:  # noqa: BLE001 — stub raises until implemented
            got = f"{type(exc).__name__}: {exc}"
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<42} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
