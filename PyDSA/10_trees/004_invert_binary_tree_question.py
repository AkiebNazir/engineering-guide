"""
================================================================================
QUESTION · LeetCode 226 · Invert Binary Tree                            [Easy]
https://leetcode.com/problems/invert-binary-tree/
================================================================================

PROBLEM
-------
Given the `root` of a binary tree, invert the tree (mirror it left-to-right),
and return its root.


EXAMPLES
--------
Example 1:
    Input:  root = [4,2,7,1,3,6,9]
    Output: [4,7,2,9,6,3,1]

            4                     4
          ╱   ╲                 ╱   ╲
         2     7      ->       7     2
        ╱ ╲   ╱ ╲             ╱ ╲   ╱ ╲
       1   3 6   9           9   6 3   1

Example 2:
    Input:  root = [2,1,3]
    Output: [2,3,1]

Example 3:
    Input:  root = []
    Output: []


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [0, 100].
    -100 <= Node.val <= 100


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Invert" means: at EVERY node, swap the left and right child references —
not the values, the whole subtrees. Do that everywhere and the tree is
mirrored about its vertical axis.

    node.left, node.right = node.right, node.left

That one line, applied to every node in any order (preorder, postorder or
level order — all three work here), is the entire algorithm. The traversal
choice does not matter because the swap at a node does not depend on any
other node's result. That independence is unusual in this topic; hold on to
it, because problems 005-012 all DO depend on children's results.

Two things bite people:

  1. The swap must be a genuine simultaneous swap. Writing
         node.left = node.right
         node.right = node.left      # already overwritten!
     assigns the same subtree to both sides. Python's tuple assignment
     (`a, b = b, a`) evaluates the right-hand side first, so it is safe;
     writing it as two statements is not.

  2. The same trap in recursive dress:
         node.left = invert(node.right)
         node.right = invert(node.left)   # reads the NEW left
     The second line re-inverts the subtree the first line just installed.
     The solution file runs this live: it produces a tree in which one node
     object appears in several places at once.

This problem is famous for a second reason — the author of Homebrew was
rejected after being asked it. The lesson interviewers actually take from
that story is that they will ask you to also do it iteratively, and to say
which traversal you used and why it does not matter.


PROGRESSIVE HINTS
------------------
Hint 1: What has to happen at ONE node for the mirror to be correct there?

Hint 2: Swap its two child references, then ask the same question of both
        children. Base case: `None` — nothing to swap, return it.

Hint 3: For an iterative version, any worklist works: a stack (DFS) or a
        deque (BFS). Pop a node, swap its children, push the children.


COMPLEXITY TARGET
------------------
    Time:  O(n) — one swap per node
    Space: O(h) recursive/stack, O(w) for BFS (w = widest level, up to n/2)
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
    def invertTree(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
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
        ([4, 2, 7, 1, 3, 6, 9], [4, 7, 2, 9, 6, 3, 1]),
        ([2, 1, 3], [2, 3, 1]),
        ([], []),
        ([1], [1]),
        ([1, 2], [1, None, 2]),
        ([1, None, 2, 3], [1, 2, None, None, 3]),
    ]
    for values, want in cases:
        got = to_level_order(sol.invertTree(build(values)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<24} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
