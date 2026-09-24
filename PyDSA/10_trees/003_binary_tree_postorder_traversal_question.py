"""
================================================================================
QUESTION · LeetCode 145 · Binary Tree Postorder Traversal               [Easy]
https://leetcode.com/problems/binary-tree-postorder-traversal/
================================================================================

PROBLEM
-------
Given the `root` of a binary tree, return the postorder traversal of its
nodes' values.

Postorder = visit the LEFT subtree, then the RIGHT subtree, then the NODE.
The node is recorded LAST — only after both of its subtrees are finished.


EXAMPLES
--------
Example 1:
    Input:  root = [1,null,2,3]
    Output: [3,2,1]

        1
         ╲
          2
         ╱
        3

Example 2:
    Input:  root = []
    Output: []

Example 3:
    Input:  root = [1]
    Output: [1]

Example 4:
    Input:  root = [1,2,3,4,5,null,8,null,null,6,7,9]
    Output: [4,6,7,5,2,9,8,3,1]

                    1
                  ╱   ╲
                 2      3
                ╱ ╲       ╲
               4   5       8
                  ╱ ╲     ╱
                 6   7   9

    The root is always the LAST value in a postorder traversal, because
    everything below it must finish first.


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [0, 100].
    -100 <= Node.val <= 100

FOLLOW UP
---------
    Recursive solution is trivial, could you do it iteratively?
    (There are TWO iterative answers, and an interviewer may want both.)


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Postorder is the "children first" order, and that makes it the traversal
behind every BOTTOM-UP tree algorithm in this folder: max depth (005),
balanced (009), diameter (010), max path sum (018) all compute something for
each child and then combine it at the parent. If you find yourself saying
"I need both children's answers before I can answer for this node", you are
writing a postorder traversal.

Iteratively it is the hardest of the three orders, because on popping a node
you cannot tell whether you are arriving for the first time (children still
to do) or coming back up (children done). Two standard answers:

  (a) THE REVERSED-PREORDER TRICK. Run preorder but push LEFT before RIGHT,
      which yields node-right-left, then reverse the result:

          reverse(node, right, left) == (left, right, node)

      Four lines, easy to remember. But it produces the right *sequence of
      values* while visiting the nodes in the wrong order — so it cannot be
      used when the work at each node must actually happen after its
      children (freeing nodes, accumulating subtree sums in place).

  (b) THE HONEST ONE-STACK VERSION, with a `last_visited` pointer: dive down
      the left spine, then peek at the top of the stack. If it has a right
      child you have not just come back from, go there; otherwise both
      children are done, so pop and record it. This visits nodes in true
      postorder.


PROGRESSIVE HINTS
------------------
Hint 1: Recursively, put the `out.append(...)` AFTER both recursive calls.
        That is the whole difference from problems 001 and 002.

Hint 2: For an iterative version, notice that (node, right, left) reversed is
        exactly (left, right, node). What is (node, right, left)? Preorder
        with the two pushes swapped.

Hint 3: For the honest version you need to know, on arriving at a node, where
        you came from. Keep a `last_visited` node: if `top.right` exists and
        is not `last_visited`, descend right; otherwise pop and record.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(h) auxiliary — O(n) skewed, O(log n) balanced.
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
    def postorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
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
        ([1, None, 2, 3], [3, 2, 1]),
        ([], []),
        ([1], [1]),
        ([4, 2, 6, 1, 3, 5, 7], [1, 3, 2, 5, 7, 6, 4]),
        ([1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9], [4, 6, 7, 5, 2, 9, 8, 3, 1]),
    ]
    for values, want in cases:
        got = sol.postorderTraversal(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<44} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
