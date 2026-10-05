"""
================================================================================
QUESTION · LeetCode 230 · Kth Smallest Element in a BST              [Medium]
https://leetcode.com/problems/kth-smallest-element-in-a-bst/
================================================================================

PROBLEM
-------
Given the `root` of a binary search tree, and an integer `k`, return the
`k`th smallest value (1-indexed) of all the values of the nodes in the tree.


EXAMPLES
--------
Example 1:
    Input:  root = [3,1,4,null,2], k = 1
    Output: 1

              3
            ╱   ╲
          1       4
            ╲
              2

    In-order: 1, 2, 3, 4  ->  1st smallest is 1.

Example 2:
    Input:  root = [5,3,6,2,4,null,null,1], k = 3
    Output: 3

                    5
                  ╱   ╲
                3       6
              ╱   ╲
            2       4
          ╱
        1

    In-order: 1, 2, 3, 4, 5, 6  ->  3rd smallest is 3.


CONSTRAINTS
-----------
    The number of nodes in the tree is n.
    1 <= k <= n <= 10^4
    0 <= Node.val <= 10^4

Follow up: If the BST is modified often (insert/delete operations) and you
need to find the kth smallest frequently, how would you optimize?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Part 1 of the topic guide: in-order traversal of a BST visits values in
strictly increasing order. So "the kth smallest value" is just "the kth
value produced by an in-order walk" — you don't need to sort anything, the
tree's shape already IS the sorted order.

The naive move is: collect the whole in-order sequence into a list, then
index `list[k-1]`. That works, but it does O(n) work and O(n) space even
when `k` is 1 and the tree has 10,000 nodes — you'd walk the ENTIRE right
side of the tree just to throw the result away.

The better move: traverse in-order but STOP the instant you've produced the
kth value. An iterative in-order walk with an explicit stack lets you pause
after exactly `k` pops instead of materializing the whole sequence first.


PROGRESSIVE HINTS
------------------
Hint 1: Whatever "in-order, but stop early" looks like, it needs to count
        nodes AS it visits them, not after building a full list.

Hint 2: The classic iterative in-order pattern: push all left children onto
        a stack, pop one, "visit" it, then move to its right child and
        repeat.

Hint 3: You do not need recursion. An explicit stack (`list` used as a
        stack) gives you a natural place to `break`/`return` the moment
        your visit-counter hits `k`.

Hint 4: Think about the follow-up before you look at the solution file: if
        this exact query is going to be asked MANY times against a tree
        that also mutates, what would you store at each node to answer it
        in O(h) instead of O(h + k)?


COMPLEXITY TARGET
------------------
    Time:  O(h + k) — descend to the leftmost node (O(h)), then visit k
           nodes via the stack
    Space: O(h) — the explicit stack, not the whole tree
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
    def kthSmallest(self, root: Optional[TreeNode], k: int) -> int:
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


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([3, 1, 4, None, 2], 1, 1),
        ([5, 3, 6, 2, 4, None, None, 1], 3, 3),
        ([5, 3, 6, 2, 4, None, None, 1], 1, 1),
        ([5, 3, 6, 2, 4, None, None, 1], 6, 6),
        ([1], 1, 1),
        ([2, 1, 3], 2, 2),
        ([2, 1, 3], 3, 3),
    ]
    for values, k, want in cases:
        got = sol.kthSmallest(build(values), k)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  tree={values!r:<30} k={k} "
              f"-> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
