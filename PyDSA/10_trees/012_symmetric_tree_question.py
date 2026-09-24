"""
================================================================================
QUESTION · LeetCode 101 · Symmetric Tree                                [Easy]
https://leetcode.com/problems/symmetric-tree/
================================================================================

PROBLEM
-------
Given the root of a binary tree, check whether it is a mirror of itself
(symmetric around its center).

Example 1:

    Input: root = [1,2,2,3,4,4,3]
    Output: true

            1
          ╱   ╲
         2      2
       ╱  ╲    ╱  ╲
      3    4  4    3

    Fold the tree down its vertical center line and the left half lands
    exactly on the right half: 3 lines up with 3, 4 lines up with 4. This is
    a MIRROR image, not a copy — read the right subtree's preorder and it is
    the left subtree's preorder with every "left" and "right" swapped.

Example 2:

    Input: root = [1,2,2,null,3,null,3]
    Output: false

            1
          ╱   ╲
         2      2
          ╲      ╲
           3      3

    Same values on both sides (2,2 then 3,3) but NOT a mirror: node 2's `3`
    hangs off its RIGHT, and so does the other node 2's `3`. A true mirror
    needs the left node's right-side child to line up with the right node's
    LEFT-side child. Folding this tree down the center does NOT make the two
    halves coincide — both `3`s land on the same side of the fold instead of
    opposite sides.

CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 1000].
    -100 <= Node.val <= 100

================================================================================
HINTS (progressive)
================================================================================
Hint 1:
    This folder already has 007 (Same Tree, LC 100): given two trees `p` and
    `q`, `isSameTree` walks them together and compares `p.val == q.val`,
    recursing on `(p.left, q.left)` and `(p.right, q.right)`. Symmetric Tree
    is the same shape of recursion, over `root.left` and `root.right` treated
    as if they were TWO separate trees that must match — except "match"
    doesn't mean "identical", it means "mirror image of each other".

Hint 2:
    Write a helper `isMirror(left, right)` and call it once, as
    `isMirror(root.left, root.right)`. The base cases are identical to 007's:
    both `None` -> True; exactly one `None` -> False; values differ -> False.

Hint 3:
    The one line that changes is the recursive call. 007's `isSameTree` pairs
    SAME sides: `isSameTree(p.left, q.left) and isSameTree(p.right, q.right)`.
    A mirror needs CROSSED sides instead:

        isMirror(left.left, right.right)   # outer edges of the fold
        and
        isMirror(left.right, right.left)   # inner edges of the fold

    Read it as: the left subtree's LEFT child must mirror the right
    subtree's RIGHT child (both are the "outermost" branches), and the left
    subtree's RIGHT child must mirror the right subtree's LEFT child (both
    are the "innermost" branches, nearest the center fold). This crossing IS
    what "mirror" means — pairing same-side children instead would check
    whether the two subtrees are literally identical (007's question, not
    this one), which is a stricter and different condition.

Hint 4:
    Think of it as TWO-POINTER recursion over one tree's two halves: one
    pointer walks `root.left` going left-then-right, the other walks
    `root.right` going right-then-left, and at every step they must agree.

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
    def isSymmetric(self, root: Optional[TreeNode]) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — standard tree kit (documented in 001)
# ==============================================================================
def build(values):
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


# ==============================================================================
# TESTS — run:  python 012_symmetric_tree_question.py
# ==============================================================================
CASES = [
    ([1, 2, 2, 3, 4, 4, 3], True),
    ([1, 2, 2, None, 3, None, 3], False),
    ([], True),
    ([1], True),
    ([1, 2, 2], True),
    ([1, 2, 2, None, 3, 3, None], True),
    ([1, 2, 2, 3, None, None, 3], True),
    ([1, 2, 2, 3, None, 3, None], False),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for vals, want in CASES:
        got = sol.isSymmetric(build(vals))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  root={vals!r:<32} -> {got}  (want {want})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT (expected — write the solution)'}")


if __name__ == "__main__":
    run_tests()
