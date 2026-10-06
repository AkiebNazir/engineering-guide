"""
================================================================================
QUESTION · LeetCode 700 · Search in a Binary Search Tree               [Easy]
https://leetcode.com/problems/search-in-a-binary-search-tree/
================================================================================

PROBLEM
-------
You are given the `root` of a binary search tree (BST) and an integer `val`.

Find the node in the BST whose value equals `val` and return the subtree
rooted at that node. If such a node does not exist, return `None`.


EXAMPLES
--------
Example 1:
    Input:  root = [4,2,7,1,3], val = 2
    Output: [2,1,3]

            4
           ╱ ╲
          2   7
         ╱ ╲
        1   3

    The node holding 2 is returned, and with it its whole subtree [2,1,3].

Example 2:
    Input:  root = [4,2,7,1,3], val = 5
    Output: []


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 5000].
    1 <= Node.val <= 10^7
    root is a binary search tree.
    1 <= val <= 10^7


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The BST invariant is what makes this cheap:

    EVERY value in node.left's SUBTREE  <  node.val  <  EVERY value in
    node.right's SUBTREE

Not "node.left.val < node.val < node.right.val" — the whole subtree, all the
way down. That is why one comparison at the root lets you throw away an
entire side of the tree without looking inside it:

    val < node.val  ->  it can only be in the LEFT subtree  (prune right)
    val > node.val  ->  it can only be in the RIGHT subtree (prune left)
    val == node.val ->  found it

In a plain binary tree (topic 10) you cannot do this — no ordering means no
subtree can ever be ruled out, so search is O(n). Here it costs O(h), where
h is the tree's HEIGHT. Note carefully: O(h), not O(log n). h == log n only
if the tree happens to be balanced; a BST built by inserting sorted values
is a linked list in disguise, and then h == n.


PROGRESSIVE HINTS
------------------
Hint 1: At each node you have three cases and each one is a single
        comparison. Two of them let you ignore half the tree.

Hint 2: You never need to look at both children. That is the whole point —
        if you find yourself recursing left AND right, you have written a
        plain-tree search and thrown the BST away.

Hint 3: Because you only ever descend (never backtrack), the recursion is
        tail-recursive and rewrites to a `while node:` loop with O(1) space.


COMPLEXITY TARGET
------------------
    Time:  O(h) — h = tree height; O(log n) if balanced, O(n) if degenerate
    Space: O(1) iterative, O(h) recursive (call stack)
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
    def searchBST(self, root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — shared across topics 10 and 11; not part of the exercise
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
        ([4, 2, 7, 1, 3], 2, [2, 1, 3]),
        ([4, 2, 7, 1, 3], 5, []),
        ([4, 2, 7, 1, 3], 4, [4, 2, 7, 1, 3]),
        ([4, 2, 7, 1, 3], 3, [3]),
        ([1], 1, [1]),
        ([1], 2, []),
    ]
    for values, val, want in cases:
        got = to_level_order(sol.searchBST(build(values), val))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  tree={values!r:<20} val={val:<4} "
              f"-> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
