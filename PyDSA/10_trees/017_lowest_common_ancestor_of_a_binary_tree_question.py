"""
================================================================================
QUESTION · LeetCode 236 · Lowest Common Ancestor of a Binary Tree      [Medium]
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/
================================================================================
Given a binary tree, find the lowest common ancestor (LCA) of two given nodes
`p` and `q` in the tree.

According to the definition of LCA on Wikipedia: "The lowest common ancestor
is defined between two nodes p and q as the LOWEST node in T that has both p
and q as descendants (where we allow A NODE TO BE A DESCENDANT OF ITSELF)."

Example 1:
    Input:  root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 1
    Output: 3

                    3
              ┌─────┴─────┐
              5           1
           ┌──┴──┐     ┌──┴──┐
           6     2     0     8
               ┌─┴─┐
               7    4

Example 2:
    Input:  root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 4
    Output: 5
    Explanation: node 5 is a descendant of ITSELF, per the definition above.

Example 3:
    Input:  root = [1,2], p = 1, q = 2
    Output: 1

Constraints:
    The number of nodes in the tree is in the range [2, 10^5].
    -10^9 <= Node.val <= 10^9
    All Node.val are UNIQUE.
    p != q
    p and q WILL EXIST in the tree.

Note: `p` and `q` are given as NODE REFERENCES, not values. Compare with
`is`, not `==` — and see the follow-up about what changes if they are given
as values instead.


THE TWO SHAPES OF THE ANSWER
-----------------------------
Only two things can be true at the LCA node, and recognising both is the
whole problem:

    (a) p and q are in DIFFERENT subtrees of this node — one on each side.
        Then this node is the split point, and it is the answer.

    (b) this node IS p (or IS q), and the other one is somewhere below it.
        Then this node is the answer, because a node is a descendant of
        itself.

Case (b) is the one people forget. If you only handle (a) you will return
`None` for Example 2.


PROGRESSIVE HINTS
------------------
Hint 1: Ask each subtree one question: "did you find p or q anywhere inside
        you?" Then reason about the two answers at the parent.

Hint 2: Let `left` = result from the left subtree, `right` = result from the
        right. If BOTH are non-null, p and q are on opposite sides, so the
        current node is the answer.

Hint 3: If only ONE side is non-null, pass it up unchanged — the answer is
        somewhere in that side, and this node knows nothing more.

Hint 4: Base cases: `None` returns `None`; a node that IS p or q returns
        ITSELF immediately, without even looking at its children. That
        single line is what makes case (b) work.


COMPLEXITY TARGET
------------------
    Time:  O(n) — you may have to visit every node
    Space: O(h) for the recursion stack
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
    def lowestCommonAncestor(self, root: 'TreeNode', p: 'TreeNode',
                             q: 'TreeNode') -> 'TreeNode':
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


def find(root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
    """Locate the NODE with the given value (values are unique)."""
    if root is None:
        return None
    stack = [root]
    while stack:
        node = stack.pop()
        if node.val == val:
            return node
        if node.left is not None:
            stack.append(node.left)
        if node.right is not None:
            stack.append(node.right)
    return None


# ==============================================================================
# TESTS — run:  python 017_lowest_common_ancestor_of_a_binary_tree_question.py
# ==============================================================================
#            tree                                      p   q   expected LCA value
CASES = [
    ([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 1, 3),
    ([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 5, 4, 5),
    ([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 7, 4, 2),
    ([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 6, 4, 5),
    ([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 7, 8, 3),
    ([1, 2], 1, 2, 1),
    ([1, 2, 3], 2, 3, 1),
    ([1, 2, None, 3, None, 4], 3, 4, 3),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for vals, pv, qv, expected in CASES:
        root = build(vals)
        p, q = find(root, pv), find(root, qv)
        try:
            got_node = sol.lowestCommonAncestor(root, p, q)
            got = got_node.val if got_node is not None else None
        except Exception as exc:  # noqa: BLE001 — stub raises until implemented
            got = f"{type(exc).__name__}: {exc}"
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  p={pv:<3} q={qv:<3} -> {got}  "
              f"(want {expected})   tree={vals}")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
