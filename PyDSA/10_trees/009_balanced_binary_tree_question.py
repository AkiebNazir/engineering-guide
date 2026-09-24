"""
================================================================================
QUESTION · LeetCode 110 · Balanced Binary Tree                          [Easy]
https://leetcode.com/problems/balanced-binary-tree/
================================================================================

PROBLEM
-------
Given a binary tree, determine if it is height-balanced.

A height-balanced binary tree is a binary tree in which the depth of the two
subtrees of EVERY node never differs by more than one.


EXAMPLES
--------
Example 1:
    Input:  root = [3,9,20,null,null,15,7]
    Output: true

            3
          ╱   ╲
         9     20
             ╱    ╲
            15     7

    Every node's left/right subtree heights differ by at most 1. (9 is a
    leaf: height 1 on both sides trivially. 20's children are both leaves:
    heights 1 and 1. 3's children have heights 1 and 2 -> diff 1, OK.)

Example 2:
    Input:  root = [1,2,2,3,3,null,null,4,4]
    Output: false

                1
              ╱   ╲
            2       2
          ╱   ╲
        3       3
      ╱   ╲
    4       4

    Node 1's left subtree (rooted at the first 2) has height 4; its right
    subtree (the second 2, a leaf) has height 1. |4 - 1| = 3 > 1 -> not
    balanced. It doesn't matter that the imbalance is buried deep on one
    side — EVERY node's two subtree heights must be checked, not just the
    root's.

Example 3:
    Input:  root = []
    Output: true

    The empty tree is height-balanced by convention (there is no node whose
    subtrees could disagree).


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [0, 5000].
    -10^4 <= Node.val <= 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Balanced" here does NOT mean the values are sorted, or that the tree looks
symmetric — it is purely a statement about HEIGHTS: for every single node in
the tree (not just the root), look at its left subtree's height and its
right subtree's height, and they must differ by at most 1.

The naive way to check this is exactly what the sentence says: for every
node, independently compute the height of its left subtree and the height of
its right subtree (a separate O(n) helper call each time), and check the
difference. That works, but computing height afresh at every node makes the
whole thing O(n^2) in the worst case (a skewed tree makes this concrete —
see the solution file's runtime demo).

The key realization: height is ALREADY a postorder aggregate (topic guide,
Part 4.2 — "does this node's answer depend on its descendants? Return it up
the call stack.") A single postorder pass can compute a node's height AND
notice, for free, whether an imbalance exists anywhere in its subtree — no
second pass required. The only trick is folding "is this subtree balanced"
and "what is this subtree's height" into ONE return value, and bailing out
early (returning a sentinel like -1) the moment an imbalance is found
anywhere below, instead of doing useless extra work.


PROGRESSIVE HINTS
------------------
Hint 1: Height is `1 + max(height(left), height(right))`, a postorder
        aggregate — you already know this pattern from problem 005.

Hint 2: A "check balance at every node" naive approach means calling a
        height() helper at every node of the tree. Each helper call is O(n)
        by itself. How many nodes are there to call it at, and what does
        that make the total?

Hint 3: Can you get height AND "is this subtree balanced" out of the SAME
        postorder call, instead of two separate passes? What single sentinel
        return value could mean "already broken, don't bother computing
        further up"?


COMPLEXITY TARGET
------------------
    Time:  O(n) — one postorder pass, each node visited once
    Space: O(h) — the recursion stack, h = tree height
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
    def isBalanced(self, root: Optional[TreeNode]) -> bool:
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
        ([3, 9, 20, None, None, 15, 7], True),
        ([1, 2, 2, 3, 3, None, None, 4, 4], False),
        ([], True),
        ([1], True),
        ([1, 2, None, 3], False),
        ([1, 2, 3, 4, 5, 6, 7], True),
    ]
    for rv, want in cases:
        got = sol.isBalanced(build(rv))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  root={rv!r:<40} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
