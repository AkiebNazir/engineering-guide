"""
================================================================================
QUESTION · LeetCode 94 · Binary Tree Inorder Traversal                  [Easy]
https://leetcode.com/problems/binary-tree-inorder-traversal/
================================================================================

PROBLEM
-------
Given the `root` of a binary tree, return the inorder traversal of its nodes'
values.

Inorder = visit the LEFT subtree first, then the NODE, then the RIGHT subtree.


EXAMPLES
--------
Example 1:
    Input:  root = [1,null,2,3]
    Output: [1,3,2]

        1
         ╲
          2
         ╱
        3

    Left of 1 is empty -> record 1 -> descend right into 2 -> left of 2 is 3,
    so 3 is recorded before 2.

Example 2:
    Input:  root = []
    Output: []

Example 3:
    Input:  root = [1]
    Output: [1]

Example 4:
    Input:  root = [4,2,6,1,3,5,7]
    Output: [1,2,3,4,5,6,7]

              4
            ╱   ╲
           2     6
          ╱ ╲   ╱ ╲
         1   3 5   7

    That sorted output is not a coincidence — see below.


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [0, 100].
    -100 <= Node.val <= 100

FOLLOW UP
---------
    Recursive solution is trivial, could you do it iteratively?
    (And then: could you do it in O(1) space? That is Morris traversal.)


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Inorder is the traversal that matters most in the whole topic, for one
reason: **the inorder traversal of a Binary Search Tree is sorted.** Almost
every BST problem in topic 11 is "run an inorder walk and check/use the fact
that the values come out in ascending order" (LC 98 Validate BST, LC 230 Kth
Smallest, LC 173 BST Iterator, LC 530 Minimum Absolute Difference).

The iterative form is NOT the same shape as preorder's. In preorder you can
record a node the moment you pop it. In inorder you must not record a node
until its entire left subtree is finished, so the loop has two phases:

    1. Run as far LEFT as possible, pushing every node you pass (the
       "left spine").
    2. Pop one — its left subtree is provably done, so record it — then move
       to its RIGHT child and go back to phase 1.

    while curr or stack:
        while curr:                 # phase 1: dive left, pushing
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()          # phase 2: this node's left is finished
        out.append(curr.val)
        curr = curr.right            # now owe the right subtree the same treatment

The `curr or stack` loop condition is the subtle part: `curr` alone would exit
while nodes are still parked on the stack, and `stack` alone would exit before
the first dive has pushed anything.


PROGRESSIVE HINTS
------------------
Hint 1: Recursively, move the `out.append(...)` line to sit BETWEEN the two
        recursive calls. That is the entire difference from problem 001.

Hint 2: Iteratively, you cannot record a node when you first meet it — its
        left subtree has not been walked yet. So push it and keep going left.

Hint 3: When you pop a node, its left subtree is finished by construction.
        Record it, then set `curr = node.right` and repeat the left dive.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(h) auxiliary — O(n) if skewed, O(log n) if balanced.
           O(1) is achievable with Morris traversal (temporarily mutates
           the tree; see the solution file).
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
    def inorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
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
        ([1, None, 2, 3], [1, 3, 2]),
        ([], []),
        ([1], [1]),
        ([4, 2, 6, 1, 3, 5, 7], [1, 2, 3, 4, 5, 6, 7]),
        ([1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9], [4, 2, 6, 5, 7, 1, 3, 9, 8]),
    ]
    for values, want in cases:
        got = sol.inorderTraversal(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<44} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
