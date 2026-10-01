"""
================================================================================
QUESTION · LeetCode 108 · Convert Sorted Array to Binary Search Tree    [Easy]
https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/
================================================================================

PROBLEM
-------
Given an integer array `nums` where the elements are sorted in ASCENDING
order, convert it to a HEIGHT-BALANCED binary search tree.

A height-balanced binary tree is one in which, for every node, the depths of
its two subtrees differ by no more than 1.


EXAMPLES
--------
Example 1:
    Input:  nums = [-10,-3,0,5,9]
    Output: [0,-3,9,-10,null,5]

            0                        0
           ╱ ╲                      ╱ ╲
        -3    9        or        -10   5
        ╱    ╱                      ╲    ╲
     -10    5                       -3    9

    BOTH are accepted. The answer is NOT unique — any height-balanced BST
    over these values is correct.

Example 2:
    Input:  nums = [1,3]
    Output: [3,1]      ([1,null,3] is also accepted)


CONSTRAINTS
-----------
    1 <= nums.length <= 10^4
    -10^4 <= nums[i] <= 10^4
    nums is sorted in a strictly increasing order.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Read the topic's one big idea backwards. An in-order traversal of a BST is
a sorted sequence — so a sorted array IS an in-order traversal, and this
problem asks you to invert that mapping. Which element is the root?

Any element `nums[i]` could be a legal root (everything left of it goes in
the left subtree, everything right of it goes right). But only the MIDDLE
one balances the two sides:

    nums = [-10, -3, 0, 5, 9]
                     ^ mid = index 2 -> root = 0
    left  = [-10, -3]  -> recursively build the left subtree
    right = [5, 9]      -> recursively build the right subtree

Picking `nums[0]` as the root instead gives a right-leaning chain of height
n — a valid BST, but not height-balanced, so it fails the problem.

Because `mid` for an even-length slice can round either way, `[1,3]` gives
`[3,1]` with the right-mid and `[1,null,3]` with the left-mid. Both are
height-balanced. Any test for this problem must therefore CHECK THE
PROPERTIES (is it a BST, is it height-balanced, does its in-order equal the
input) rather than compare against one hard-coded shape.


PROGRESSIVE HINTS
------------------
Hint 1: The root has to split the array into two halves of nearly equal
        size. Which element does that?

Hint 2: Recurse on index ranges, not on slices. `helper(lo, hi)` costs O(1)
        per call; `helper(nums[:mid])` copies the array at every level and
        turns O(n) into O(n log n) time and space.

Hint 3: Use the half-open or fully-closed convention consistently and pick
        your base case to match: `lo > hi -> None` for closed `[lo, hi]`.


COMPLEXITY TARGET
------------------
    Time:  O(n) — every element becomes exactly one node
    Space: O(log n) recursion depth (plus O(n) for the tree itself)
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
    def sortedArrayToBST(self, nums: List[int]) -> Optional[TreeNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — the answer is NOT unique, so we verify PROPERTIES
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


def inorder(root):
    out, stack, node = [], [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        out.append(node.val)
        node = node.right
    return out


def height_and_balanced(root):
    """Returns (height, is_height_balanced). Post-order, one pass."""
    if root is None:
        return 0, True
    lh, lb = height_and_balanced(root.left)
    rh, rb = height_and_balanced(root.right)
    return max(lh, rh) + 1, lb and rb and abs(lh - rh) <= 1


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        [-10, -3, 0, 5, 9],
        [1, 3],
        [0],
        [1, 2, 3, 4, 5, 6, 7],
        list(range(-5, 6)),
    ]
    for nums in cases:
        root = sol.sortedArrayToBST(nums)
        h, balanced = height_and_balanced(root)
        io = inorder(root)
        ok = io == nums and balanced
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<26} -> "
              f"{to_level_order(root)}  inorder_ok={io == nums} "
              f"balanced={balanced} height={h}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
