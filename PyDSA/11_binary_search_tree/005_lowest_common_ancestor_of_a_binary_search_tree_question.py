"""
================================================================================
QUESTION · LeetCode 235 · Lowest Common Ancestor of a BST            [Medium]
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/
================================================================================

PROBLEM
-------
Given a binary search tree (BST), find the lowest common ancestor (LCA) node
of two given nodes in the BST.

According to the definition of LCA on Wikipedia: "The lowest common ancestor
is defined between two nodes p and q as the lowest node in T that has both p
and q as descendants (where we allow A NODE TO BE A DESCENDANT OF ITSELF)."


EXAMPLES
--------
Example 1:
    Input:  root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 8
    Output: 6

                    6
              ╱          ╲
            2              8
          ╱   ╲          ╱   ╲
        0      4       7      9
              ╱ ╲
             3   5

    Explanation: the LCA of nodes 2 and 8 is 6.

Example 2:
    Input:  root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 4
    Output: 2
    Explanation: the LCA of nodes 2 and 4 is 2, since a node can be a
    descendant of itself according to the LCA definition.

Example 3:
    Input:  root = [2,1], p = 2, q = 1
    Output: 2


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [2, 10^5].
    -10^9 <= Node.val <= 10^9
    All Node.val are UNIQUE.
    p != q
    p and q will exist in the BST.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Do NOT reach for the general binary-tree LCA algorithm (LC 236) here. That
one is a full O(n) post-order traversal, because in a plain tree you have no
way to know which side a value is on without looking. A BST tells you the
side with one comparison — so this is an O(h) descent, and the whole
question is what "lowest" means in terms of comparisons.

Stand at some node and ask where p and q are:

    both p.val and q.val  <  node.val   ->  both are in the LEFT subtree.
                                             This node is an ancestor, but
                                             not the LOWEST one. Go left.
    both p.val and q.val  >  node.val   ->  both in the RIGHT subtree. Go right.
    otherwise (they SPLIT, or one of them
    IS this node)                        ->  STOP. This node is the LCA.

That third case is the insight: the LCA is exactly the first node where the
two search paths diverge — the SPLIT POINT. Above it, the two values agree on
which way to turn; below it they never share a node again. And if one of the
two values equals the current node, that node is the LCA by the "a node is
its own descendant" clause in the definition.


PROGRESSIVE HINTS
------------------
Hint 1: Walk down from the root. At each node, both values being on the SAME
        side tells you the answer is deeper.

Hint 2: You do not need to find p or q at all, and you do not need to
        compare node identities — only the two values against `node.val`.

Hint 3: The loop is `while True` with three cases and no backtracking, so it
        is O(1) space. You never need a stack, a parent map, or a second
        pass.


COMPLEXITY TARGET
------------------
    Time:  O(h)  — compare with O(n) for LC 236 on a plain binary tree
    Space: O(1) iterative, O(h) recursive
================================================================================
"""

from collections import deque


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


def find_node(root, val):
    """LeetCode hands you the NODE objects for p and q, not the values."""
    node = root
    while node:
        if node.val == val:
            return node
        node = node.left if val < node.val else node.right
    return None


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    tree = [6, 2, 8, 0, 4, 7, 9, None, None, 3, 5]
    cases = [
        (tree, 2, 8, 6),
        (tree, 2, 4, 2),
        (tree, 3, 5, 4),
        (tree, 0, 5, 2),
        (tree, 7, 9, 8),
        (tree, 0, 9, 6),
        ([2, 1], 2, 1, 2),
    ]
    for values, pv, qv, want in cases:
        root = build(values)
        got = sol.lowestCommonAncestor(root, find_node(root, pv),
                                       find_node(root, qv))
        got_val = got.val if got else None
        ok = got_val == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  p={pv:<3} q={qv:<3} -> {got_val}  "
              f"(want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
