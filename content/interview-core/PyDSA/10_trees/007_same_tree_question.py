"""
================================================================================
QUESTION · LeetCode 100 · Same Tree                                     [Easy]
https://leetcode.com/problems/same-tree/
================================================================================

PROBLEM
-------
Given the roots of two binary trees `p` and `q`, write a function to check
if they are the same or not.

Two binary trees are considered the same if they are STRUCTURALLY IDENTICAL
and the nodes have the same value.


EXAMPLES
--------
Example 1:
    Input:  p = [1,2,3], q = [1,2,3]
    Output: true

         1        1
        ╱ ╲      ╱ ╲
       2   3    2   3

Example 2:
    Input:  p = [1,2], q = [1,null,2]
    Output: false

         1        1
        ╱          ╲
       2            2

    Same values, same node count, DIFFERENT shape. This pair is the reason
    "compare the traversals" is not a solution: the preorder of both trees is
    [1,2].

Example 3:
    Input:  p = [1,2,1], q = [1,1,2]
    Output: false

    Same shape, values in different places.


CONSTRAINTS
-----------
    The number of nodes in both trees is in the range [0, 100].
    -10^4 <= Node.val <= 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the topic's first TWO-TREE recursion: the function walks two trees in
lockstep, taking one step in each at the same time.

    same(a, b) = both None                                  -> True
               = exactly one None                            -> False
               = a.val != b.val                              -> False
               = same(a.left, b.left) AND same(a.right, b.right)

Note the pairing: LEFT with LEFT, RIGHT with RIGHT. Problem 012 (Symmetric
Tree) is the same function with the pairing crossed — `(a.left, b.right)` —
and that one character of difference is the entire distinction between
"identical" and "mirrored". Learning them as one pattern with two pairings is
much more reliable than memorising two functions.

The three base cases must come in this order:

    1. both None      -> True    (two empty subtrees ARE the same)
    2. one None        -> False   (structure differs)
    3. values differ    -> False

If you check `a.val != b.val` before ruling out `None`, you get
`AttributeError: 'NoneType' object has no attribute 'val'`.


PROGRESSIVE HINTS
------------------
Hint 1: What does it mean for two EMPTY trees to be the same? Answer that
        first — it is the base case that makes the recursion terminate.

Hint 2: You are recursing on a PAIR of nodes, not one node. The function
        signature takes two arguments and both advance together.

Hint 3: Order the None checks before any `.val` access, and combine the two
        subtree results with `and` (which short-circuits, so a mismatch stops
        the walk early).


COMPLEXITY TARGET
------------------
    Time:  O(min(n, m)) — the walk stops at the first difference, and cannot
           visit more nodes than the smaller tree has (+1 for the mismatch)
    Space: O(min(h_p, h_q)) for the call stack
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
    def isSameTree(self, p: Optional[TreeNode], q: Optional[TreeNode]) -> bool:
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
        ([1, 2, 3], [1, 2, 3], True),
        ([1, 2], [1, None, 2], False),
        ([1, 2, 1], [1, 1, 2], False),
        ([], [], True),
        ([1], [], False),
        ([1], [1], True),
        ([1, 2, 3], [1, 2, 4], False),
    ]
    for pv, qv, want in cases:
        got = sol.isSameTree(build(pv), build(qv))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  p={pv!r:<18} q={qv!r:<18} -> {got}  "
              f"(want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
