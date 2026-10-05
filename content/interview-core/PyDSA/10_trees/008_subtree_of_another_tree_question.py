"""
================================================================================
QUESTION · LeetCode 572 · Subtree of Another Tree                       [Easy]
https://leetcode.com/problems/subtree-of-another-tree/
================================================================================

PROBLEM
-------
Given the roots of two binary trees `root` and `subRoot`, return true if
there is a subtree of `root` with the same structure and node values as
`subRoot`, and false otherwise.

A subtree of a binary tree `tree` is a tree that consists of a NODE in
`tree` and ALL of this node's descendants. The tree `tree` could also be
considered as a subtree of itself.


EXAMPLES
--------
Example 1:
    Input:  root = [3,4,5,1,2], subRoot = [4,1,2]
    Output: true

            3                      4
          ╱   ╲                  ╱   ╲
         4     5                1     2
        ╱ ╲
       1   2

    The node 4 in `root`, together with ALL its descendants, is exactly
    `subRoot`.

Example 2:
    Input:  root = [3,4,5,1,2,null,null,null,null,0], subRoot = [4,1,2]
    Output: false

            3
          ╱   ╲
         4     5
        ╱ ╲
       1   2
          ╱
         0

    Node 4's subtree now contains an extra node 0, and "subtree" means the
    node AND ALL its descendants — no partial matches.


CONSTRAINTS
-----------
    The number of nodes in root is in the range [1, 2000].
    The number of nodes in subRoot is in the range [1, 1000].
    -10^4 <= root.val, subRoot.val <= 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The definition of "subtree" is the crux: a node plus EVERYTHING under it.
`[4,1,2]` is not a subtree of a tree where node 4 has an extra grandchild,
even though every node of `[4,1,2]` appears in the right place. That is why
this problem is not "find a matching pattern" but "find a node where the two
trees are IDENTICAL from there down" — which is problem 007 (Same Tree), used
as a subroutine:

    isSubtree(root, sub) = isSameTree(root, sub)
                            or isSubtree(root.left,  sub)
                            or isSubtree(root.right, sub)

Composition of an existing solution, and that composition is the lesson. Cost:
`isSameTree` is O(m) and it may be called at each of the n nodes, so O(n * m)
worst case (n = |root|, m = |subRoot|).

There is also an O(n + m) route: SERIALISE both trees into strings and ask
whether one string contains the other. It works only if the serialisation is
lossless AND unambiguous, and getting that right is the interesting part —
a naive serialisation reports matches that do not exist. The solution file
constructs a real false positive and shows what fixes it.


PROGRESSIVE HINTS
------------------
Hint 1: You already solved "are these two trees identical" in problem 007.
        Where would you have to call it?

Hint 2: At every node of `root`. If it matches there, done; otherwise ask the
        same question of the left and right subtrees.

Hint 3: For the O(n + m) version, think about how to turn a tree into a
        string such that different trees can never produce strings where one
        contains the other by accident. What has to be in the string besides
        the values?


COMPLEXITY TARGET
------------------
    Time:  O(n * m) for the composition; O(n + m) for serialise-and-search
    Space: O(h_root + h_sub) for the composition; O(n + m) for the strings
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
    def isSubtree(self, root: Optional[TreeNode],
                  subRoot: Optional[TreeNode]) -> bool:
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
        ([3, 4, 5, 1, 2], [4, 1, 2], True),
        ([3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2], False),
        ([1, 1], [1], True),
        ([1], [1], True),
        ([1, 2], [1, None, 2], False),
        ([12], [2], False),
        ([1, 2, 3], [1, 2, 3], True),
    ]
    for rv, sv, want in cases:
        got = sol.isSubtree(build(rv), build(sv))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  root={rv!r:<40} sub={sv!r:<14} -> "
              f"{got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
