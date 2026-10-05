"""
================================================================================
QUESTION · LeetCode 105 · Construct Binary Tree from Preorder and Inorder
                          Traversal                                    [Medium]
https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/
================================================================================
Given two integer arrays `preorder` and `inorder` where `preorder` is the
preorder traversal of a binary tree and `inorder` is the inorder traversal of
the SAME tree, construct and return the binary tree.

Example 1:
    Input:  preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]
    Output: [3,9,20,null,null,15,7]

            3
          ┌─┴──┐
          9    20
             ┌─┴─┐
            15    7

        preorder (node, left, right) : 3  9  20 15 7
        inorder  (left, node, right) : 9  3  15 20 7

Example 2:
    Input:  preorder = [-1], inorder = [-1]
    Output: [-1]

Constraints:
    1 <= preorder.length <= 3000
    inorder.length == preorder.length
    -3000 <= preorder[i], inorder[i] <= 3000
    `preorder` and `inorder` consist of UNIQUE values.
    `inorder` is guaranteed to be the inorder traversal of the tree described
    by `preorder`.


WHY TWO TRAVERSALS, AND WHY THESE TWO
--------------------------------------
One traversal is never enough: [1,2] as a preorder could be "1 with a left
child 2" or "1 with a right child 2". You need a second, INDEPENDENT view.

    preorder  gives you WHICH node is the root (it is always first).
    inorder    gives you HOW BIG the left subtree is (everything before the
               root's position belongs to the left subtree).

Root identity + left-subtree size is exactly enough to split both arrays and
recurse. Note that preorder + POSTORDER is NOT enough in general — both put
the root at an end and neither tells you where the split is. (LC 889 does it
with pre+post, but only because it additionally guarantees a FULL binary
tree, where every node has 0 or 2 children.)


PROGRESSIVE HINTS
------------------
Hint 1: `preorder[0]` is the root. Full stop, always.

Hint 2: Find that root's value inside `inorder`. Say it sits at index k.
        Then `inorder[:k]` is the entire left subtree and `inorder[k+1:]` is
        the entire right subtree — so the left subtree has exactly k nodes.

Hint 3: Since the left subtree has k nodes, `preorder[1:k+1]` is its preorder
        and `preorder[k+1:]` is the right subtree's preorder. Recurse on
        those four slices. That is a complete, correct solution.

Hint 4: It is O(n^2), for two reasons: `inorder.index(...)` is a linear scan,
        and every slice copies. Fix the first with a dict `{value: index}`
        built once. Fix the second by passing (lo, hi) index BOUNDS instead
        of slices.

Hint 5: With bounds instead of slices you no longer know where each
        subtree's preorder begins — so stop tracking it. Consume `preorder`
        left to right with ONE shared cursor, because preorder visits nodes
        in exactly the order this recursion creates them. Build the LEFT
        child before the right, or the cursor hands out the wrong values.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(n) for the index map + O(h) recursion stack
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
    def buildTree(self, preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — level-order (de)serialisation, LeetCode's array format
# ==============================================================================
def build(vals: List[Optional[int]]) -> Optional[TreeNode]:
    """Level-order list with `None` for absent children -> root node."""
    if not vals or vals[0] is None:
        return None
    root = TreeNode(vals[0])
    queue = deque([root])
    i = 1
    while queue and i < len(vals):
        node = queue.popleft()
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
    return root


def to_level_order(root: Optional[TreeNode]) -> List[Optional[int]]:
    """Root -> level-order list with `None`s, trailing `None`s trimmed."""
    if root is None:
        return []
    out: List[Optional[int]] = []
    queue = deque([root])
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


def preorder_of(root: Optional[TreeNode]) -> List[int]:
    return [] if root is None else (
        [root.val] + preorder_of(root.left) + preorder_of(root.right))


def inorder_of(root: Optional[TreeNode]) -> List[int]:
    return [] if root is None else (
        inorder_of(root.left) + [root.val] + inorder_of(root.right))


# ==============================================================================
# TESTS — run:  python 016_construct_binary_tree_from_preorder_and_inorder_traversal_question.py
# ==============================================================================
CASES = [
    ([3, 9, 20, 15, 7], [9, 3, 15, 20, 7], [3, 9, 20, None, None, 15, 7]),
    ([-1], [-1], [-1]),
    ([1, 2], [2, 1], [1, 2]),
    ([1, 2], [1, 2], [1, None, 2]),
    ([1, 2, 3, 4, 5], [4, 3, 5, 2, 1], [1, 2, None, 3, None, 4, 5]),
    ([1, 2, 4, 5, 3, 6, 7], [4, 2, 5, 1, 6, 3, 7], [1, 2, 3, 4, 5, 6, 7]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for pre, ino, expected in CASES:
        try:
            got = to_level_order(sol.buildTree(pre, ino))
        except Exception as exc:  # noqa: BLE001 — stub raises until implemented
            got = f"{type(exc).__name__}: {exc}"
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  pre={str(pre):<24} in={str(ino):<24} "
              f"-> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
