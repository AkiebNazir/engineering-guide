"""
================================================================================
QUESTION · LeetCode 112 · Path Sum                                       [Easy]
https://leetcode.com/problems/path-sum/
================================================================================
Given the root of a binary tree and an integer `targetSum`, return True if the
tree has a ROOT-TO-LEAF path such that adding up all the values along the path
equals `targetSum`. Otherwise, return False.

A LEAF is a node with no children.

Example 1:
    Input:  root = [5,4,8,11,null,13,4,7,2,null,null,null,1], targetSum = 22
    Output: True

                5
              ┌─┴──┐
              4     8
            ┌─┘   ┌─┴──┐
           11     13    4
         ┌─┴─┐         ┌─┴┐
         7   2       null 1

    Path 5 -> 4 -> 11 -> 2 sums to 5+4+11+2 = 22, and 2 is a leaf. True.

Example 2:
    Input:  root = [1,2,3], targetSum = 5
    Output: False

            1
          ┌─┴─┐
          2   3

    Leaf paths are 1->2 (sum 3) and 1->3 (sum 4). Neither is 5. Note: the sum
    5 DOES appear if you stop at node 1+2+... no combination hits it, and
    critically 1+2=3, 1+3=4 — no root-to-LEAF path sums to 5, so False, even
    though a naive "does any prefix hit 5" check on a different tree could be
    tempted to stop early at a non-leaf.

Example 3:
    Input:  root = [], targetSum = 0
    Output: False
    Explanation: Since the tree is empty, there are no root-to-leaf paths at
    all — not even a trivial "empty path" of sum 0. An empty tree has no
    leaves, so the answer is False regardless of targetSum.

Constraints:
    The number of nodes in the tree is in the range [0, 5000].
    -1000 <= Node.val <= 1000
    -1000 <= targetSum <= 1000


WHAT THIS PROBLEM IS TEACHING
------------------------------
This is the archetypal TOP-DOWN pattern: information a node needs (how much
of the target is still "owed") comes from its ANCESTORS, so it has to travel
DOWN the call stack as a PARAMETER — the mirror image of the bottom-up
postorder-return pattern used for height/diameter/balance. See the topic
guide Part 4.1 for the general rule and Part 4.3 for the one-question test to
tell the two patterns apart.

The subtlety that trips people up: the check "does the running sum equal
targetSum" must only fire at a LEAF. A node deep inside the tree can have a
cumulative sum that happens to equal targetSum while still having children —
that is not a complete root-to-leaf path, and reporting True there is a bug
(or reporting False and giving up before checking that node's descendants,
which might complete a valid path of their own, is a different bug). Get the
leaf-only condition exactly right.


PROGRESSIVE HINTS
------------------
Hint 1: What does node X need to know from its ancestors to decide whether
        continuing through X could still reach targetSum? Not the whole path
        — just one number: how much of targetSum is still unaccounted for.

Hint 2: Carry `remaining` DOWN as a parameter, starting at `targetSum` and
        subtracting `node.val` at every node (including the leaf itself).

Hint 3: Only test `remaining == 0` when you are AT a leaf (no left child and
        no right child). Testing it at an internal node is wrong — that node
        isn't the end of any path yet, and a matching prefix there does not
        mean the tree contains a qualifying root-to-leaf path.

Hint 4: `hasPathSum(node, remaining)`:
            if node is None: return False
            remaining -= node.val
            if node.left is None and node.right is None:   # leaf
                return remaining == 0
            return (hasPathSum(node.left, remaining)
                    or hasPathSum(node.right, remaining))
        Handle the empty tree explicitly: `root is None` must return False,
        even when targetSum is 0 — an empty tree has no leaves, so no path
        exists to check.


COMPLEXITY TARGET
------------------
    Time:  O(n) — one visit per node, O(1) work each
    Space: O(h) for the recursion stack (h = height; O(n) worst case on a
           skewed tree, and n can be 5000 here — mind the recursion limit)
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
    def hasPathSum(self, root: Optional[TreeNode], targetSum: int) -> bool:
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


# ==============================================================================
# TESTS — run:  python 011_path_sum_question.py
# ==============================================================================
CASES = [
    ([5, 4, 8, 11, None, 13, 4, 7, 2, None, None, None, 1], 22, True),
    ([1, 2, 3], 5, False),
    ([], 0, False),
    ([1], 1, True),
    ([1], 2, False),
    ([1, 2], 1, False),
    ([-2, None, -3], -5, True),
    ([0], 0, True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for vals, target, expected in CASES:
        try:
            got = sol.hasPathSum(build(vals), target)
        except Exception as exc:  # noqa: BLE001 — stub raises until implemented
            got = f"{type(exc).__name__}: {exc}"
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  root={str(vals):<50} target={target:>5} "
              f"-> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
