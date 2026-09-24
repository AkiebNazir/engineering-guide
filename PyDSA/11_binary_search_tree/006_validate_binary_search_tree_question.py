"""
================================================================================
QUESTION · LeetCode 98 · Validate Binary Search Tree                 [Medium]
https://leetcode.com/problems/validate-binary-search-tree/
================================================================================

PROBLEM
-------
Given the `root` of a binary tree, determine if it is a valid binary search
tree (BST).

A valid BST is defined as follows:
    · The left subtree of a node contains only nodes with keys LESS THAN the
      node's key.
    · The right subtree of a node contains only nodes with keys GREATER THAN
      the node's key.
    · Both the left and right subtrees must also be binary search trees.


EXAMPLES
--------
Example 1:
    Input:  root = [2,1,3]
    Output: true

              2
            ╱   ╲
          1       3

Example 2:
    Input:  root = [5,1,4,null,null,3,6]
    Output: false
    Explanation: the root's value is 5 but its right child's value is 4.

              5
            ╱   ╲
          1       4
                ╱   ╲
              3       6


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 10^4].
    -2^31 <= Node.val <= 2^31 - 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Read the definition once more, slowly. It says "the left SUBTREE contains
only nodes with keys less than the node's key" — the whole subtree, every
node in it, not just the immediate child.

⚠️  THIS IS THE PROBLEM. Nearly every failed attempt at LC 98 checks only
    parent-against-child:

              5
            ╱   ╲
          1       7
                ╱   ╲
              3       8

    Every parent-child pair here is fine: 1 < 5, 7 > 5, 3 < 7, 8 > 7.
    But the tree is NOT a BST — 3 sits in the RIGHT subtree of 5, and 3 < 5.
    A search for 3 starting at the root would turn LEFT at 5 and never find
    it. The tree is unusable as a BST, and a parent-child-only checker calls
    it valid.

Two correct approaches, and you should know both:

  A. BOUNDS. Carry an allowed open interval down the recursion. The root may
     be anything; going left tightens the upper bound to the parent's value,
     going right tightens the lower bound. A node is valid iff its value is
     strictly inside its interval.

         node 5: (-inf, +inf)   ok
           node 1: (-inf, 5)     ok
           node 7: (5, +inf)     ok
             node 3: (5, 7)      3 <= 5  ->  INVALID ✅ caught

  B. IN-ORDER. An in-order traversal of a valid BST is a strictly increasing
     sequence. Traverse in-order and check each value against the previous
     one. This is the topic's one big idea used as a test.

         in-order of the tree above: 1, 5, 3, 8  ->  3 < 5, not increasing
                                                     ->  INVALID ✅ caught


PROGRESSIVE HINTS
------------------
Hint 1: Whatever you write must reject a tree whose every parent-child pair
        is individually fine. Build that tree on paper first and test against
        it.

Hint 2: For the bounds approach the recursive signature is
        `valid(node, low, high)`, and only ONE of the two bounds changes per
        recursive call.

Hint 3: For the in-order approach you only need to remember the PREVIOUS
        value, not the whole list.

Hint 4: "Less than", not "less than or equal to" — duplicates make the tree
        invalid under this problem's definition.


COMPLEXITY TARGET
------------------
    Time:  O(n) — every node must be checked; there is no pruning here
    Space: O(h) — the recursion stack, or the explicit stack for in-order
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
    def isValidBST(self, root: Optional[TreeNode]) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — shared with topic 10; not part of the exercise
# ==============================================================================
def build(values):
    """LeetCode level-order list (with `None` holes) -> root TreeNode."""
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
    """Inverse of build(): level-order list with `None` for absent children,
    trailing `None`s trimmed."""
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
        ([2, 1, 3], True),
        ([5, 1, 4, None, None, 3, 6], False),
        ([5, 1, 7, None, None, 3, 8], False),   # every parent-child pair is fine
        ([1], True),
        ([1, 1], False),                         # duplicates are invalid
        ([2, 2, 2], False),
        ([10, 5, 15, None, None, 6, 20], False), # 6 is in 10's right subtree
        ([3, 1, 5, 0, 2, 4, 6], True),
        ([-2147483648], True),                   # INT_MIN as a real value
        ([2147483647], True),                    # INT_MAX as a real value
    ]
    for values, want in cases:
        got = sol.isValidBST(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<40} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
