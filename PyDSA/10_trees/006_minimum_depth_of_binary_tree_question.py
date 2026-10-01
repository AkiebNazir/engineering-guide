"""
================================================================================
QUESTION · LeetCode 111 · Minimum Depth of Binary Tree                  [Easy]
https://leetcode.com/problems/minimum-depth-of-binary-tree/
================================================================================

PROBLEM
-------
Given a binary tree, find its minimum depth.

The minimum depth is the number of NODES along the shortest path from the
root node down to the nearest LEAF node.

    Note: a leaf is a node with NO children.


EXAMPLES
--------
Example 1:
    Input:  root = [3,9,20,null,null,15,7]
    Output: 2

            3
          ╱   ╲
         9     20          9 is a leaf at depth 2  <- the answer
              ╱  ╲
            15    7        these leaves are at depth 3

Example 2:
    Input:  root = [2,null,3,null,4,null,5,null,6]
    Output: 5

        2
         ╲
          3
           ╲
            4
             ╲
              5
               ╲
                6           the ONLY leaf is at depth 5

    This is the example that breaks the obvious solution. Node 2 has no left
    child — but 2 is NOT a leaf, so the "path" of length 1 ending at 2 does
    not count. Answering `1 + min(minDepth(left), minDepth(right))` gives
    1 + min(0, 4) = 1, which is wrong.

Example 3:
    Input:  root = []
    Output: 0


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [0, 10^5].
    -1000 <= Node.val <= 1000

    10^5 nodes: a skewed tree here is 100x past CPython's recursion limit.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the same shape as problem 005 with `max` replaced by `min` — and that
substitution is WRONG. It is the most-failed easy problem in the whole tree
topic, so it is worth being precise about why.

    minDepth(node) = 1 + min(minDepth(left), minDepth(right))     ✗ WRONG

`minDepth(None)` is 0, and 0 is smaller than anything. So for a node with one
child, `min` picks the MISSING side and reports a path that stops at an
internal node. But the problem says the path must end at a LEAF.

Max depth does not have this problem: `max` naturally ignores a missing side
(0 never wins a maximum), which is why 005 is a two-liner and 006 is not.

The fix is to make "has exactly one child" its own case:

    if not root:                       return 0
    if not root.left:                  return 1 + minDepth(root.right)
    if not root.right:                 return 1 + minDepth(root.left)
    return 1 + min(minDepth(root.left), minDepth(root.right))

And there is a second, better answer. "Shortest path to a leaf" is a
shortest-path question, so BFS is the natural tool: walk the tree level by
level and STOP at the first leaf you meet. On a tree whose nearest leaf is
shallow but whose other subtree is enormous, DFS must explore everything
while BFS returns almost immediately. The solution file measures both.


PROGRESSIVE HINTS
------------------
Hint 1: Write down what the answer should be for `[1,2]` (a root with only a
        left child). Now run `1 + min(minDepth(left), minDepth(right))` on it
        by hand. Those two numbers disagree — why?

Hint 2: `minDepth(None) == 0`, and a missing child is not a path to a leaf.
        Handle "only one child exists" separately from "two children exist".

Hint 3: The question asks for a SHORTEST path. BFS finds shortest paths and
        can return the moment it meets the first leaf, without touching the
        rest of the tree.


COMPLEXITY TARGET
------------------
    Time:  O(n) worst case for both DFS and BFS — but BFS often returns after
           visiting only O(nearest-leaf-level) nodes, which can be a handful.
    Space: O(h) for DFS, O(w) for BFS.
================================================================================
"""

from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def minDepth(self, root: Optional[TreeNode]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — the standard tree kit for this topic. Nothing to solve here.
# ==============================================================================
def build(values):
    """LeetCode level-order notation -> tree. `None` means "no child here"."""
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
    return root


def to_level_order(root):
    """Inverse of build(): tree -> level-order list, trailing Nones trimmed."""
    if root is None:
        return []
    out, queue = [], deque([root])
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


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([3, 9, 20, None, None, 15, 7], 2),
        ([2, None, 3, None, 4, None, 5, None, 6], 5),
        ([], 0),
        ([1], 1),
        ([1, 2], 2),
        ([1, 2, 3, 4, 5], 2),
        ([1, 2, 3, 4, None, None, 5], 3),
    ]
    for values, want in cases:
        got = sol.minDepth(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<44} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
