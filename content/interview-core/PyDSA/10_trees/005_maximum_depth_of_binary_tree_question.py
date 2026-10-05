"""
================================================================================
QUESTION · LeetCode 104 · Maximum Depth of Binary Tree                  [Easy]
https://leetcode.com/problems/maximum-depth-of-binary-tree/
================================================================================

PROBLEM
-------
Given the `root` of a binary tree, return its maximum depth.

A binary tree's maximum depth is the number of NODES along the longest path
from the root node down to the farthest leaf node.


EXAMPLES
--------
Example 1:
    Input:  root = [3,9,20,null,null,15,7]
    Output: 3

            3                depth 1
          ╱   ╲
         9     20            depth 2
              ╱  ╲
            15    7          depth 3   <- farthest leaves

Example 2:
    Input:  root = [1,null,2]
    Output: 2

Example 3:
    Input:  root = []
    Output: 0

Example 4:
    Input:  root = [0]
    Output: 1


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [0, 10^4].
    -100 <= Node.val <= 100

    Note that 10^4: a skewed tree of 10,000 nodes is INSIDE the constraints
    and OUTSIDE CPython's default recursion limit of ~1000 frames. The
    solution file triggers the real RecursionError and shows the escapes.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Depth counted in NODES" — so a single node has depth 1, not 0, and the empty
tree has depth 0. Getting that boundary right is most of the problem.

Then the recursion writes itself: the deepest path through a node goes down
one of its two subtrees, so

    depth(node) = 1 + max(depth(node.left), depth(node.right))
    depth(None) = 0

This is the topic's first BOTTOM-UP recursion: each child returns a NUMBER up
to its parent, and the parent combines the two numbers. Compare it with the
TOP-DOWN shape, which carries the answer *down* as an argument and records it
at the leaves:

    best = 0
    def dfs(node, depth):
        nonlocal best
        if not node: return
        best = max(best, depth)          # record on the way down
        dfs(node.left, depth + 1)
        dfs(node.right, depth + 1)

Both are O(n). This problem is the cleanest place to learn the difference,
because here the two are equally good — and from 009 onwards, choosing the
wrong one of the two costs you a factor of n.


PROGRESSIVE HINTS
------------------
Hint 1: What is the depth of an empty tree? Of a single node? Answer those
        two and the base case is written.

Hint 2: If you knew the depth of the left subtree and of the right subtree,
        how would you get the depth of the whole tree? (One `max`, one `+1`.)

Hint 3: For an iterative version, either BFS level by level (count the
        levels) or DFS with a stack of `(node, depth)` pairs.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(h) recursive/DFS-stack — O(n) skewed, O(log n) balanced;
           O(w) for BFS, w = widest level.
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
    def maxDepth(self, root: Optional[TreeNode]) -> int:
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
        ([3, 9, 20, None, None, 15, 7], 3),
        ([1, None, 2], 2),
        ([], 0),
        ([0], 1),
        ([1, 2, 3, 4, None, None, 5], 3),
        ([1, 2, 2, 3, 3, None, None, 4, 4], 4),
    ]
    for values, want in cases:
        got = sol.maxDepth(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<38} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
