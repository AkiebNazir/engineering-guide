"""
================================================================================
LeetCode 129 · Sum Root to Leaf Numbers                                 [Medium]
https://leetcode.com/problems/sum-root-to-leaf-numbers/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
You are given the root of a binary tree containing digits from 0 to 9
only. Each root-to-leaf path in the tree represents a number.

For example, the root-to-leaf path 1 -> 2 -> 3 represents the number 123.

Return the total sum of all root-to-leaf numbers. Test cases are
generated so that the answer fits in a 32-bit integer.

A leaf node is a node with no children.

EXAMPLES
--------
Example 1:
    Input:  root = [1,2,3]
    Output: 25
    Explanation: The root-to-leaf path 1->2 represents the number 12.
                 The root-to-leaf path 1->3 represents the number 13.
                 Therefore, sum = 12 + 13 = 25.

Example 2:
    Input:  root = [4,9,0,5,1]
    Output: 1026
    Explanation: The root-to-leaf path 4->9->5 represents 495.
                 The root-to-leaf path 4->9->1 represents 491.
                 The root-to-leaf path 4->0 represents 40.
                 sum = 495 + 491 + 40 = 1026.

CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 1000].
    0 <= Node.val <= 9
    The depth of the tree will not exceed 10.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the "pass extra state going down" combine pattern the topic
guide names: as you descend the tree, you carry along "the number formed
so far," growing it by one digit (`* 10 + node.val`) at each step. When
you reach a LEAF, that accumulated number is one complete root-to-leaf
number to add to the total. When you reach an INTERNAL node with only
one child, you must recurse only into the child that exists.

    dfs(node, numberSoFar):
        numberSoFar = numberSoFar * 10 + node.val
        if node is a leaf: return numberSoFar             <- base case: complete number
        total = 0
        if node.left:  total += dfs(node.left, numberSoFar)
        if node.right: total += dfs(node.right, numberSoFar)
        return total

WHAT TO THINK ABOUT
--------------------
1. What piece of information must flow DOWN the recursion (not up)?
   Contrast this with 011/012 where information flowed UP.
2. What exactly defines a leaf here, and why must BOTH `node.left is
   None` and `node.right is None` be true, not just one?
3. If a node has only a LEFT child (no right), what happens if you
   blindly recurse into both `node.left` and `node.right` without
   checking for `None` first?
4. Where does the sum ACROSS different leaves get combined — at the
   leaves themselves, or somewhere higher up in the tree?

PROGRESSIVE HINTS
------------------
Hint 1: Pass an extra parameter down through the recursion representing
        "the number built from the root down to (and including) this
        node."
Hint 2: At each call, first update it: `numberSoFar = numberSoFar * 10 +
        node.val`.
Hint 3: Base case: if `node.left is None and node.right is None` (a true
        leaf), return `numberSoFar` as a complete number — no further
        recursion needed.
Hint 4: Otherwise, sum the recursive calls into whichever children
        actually exist (`if node.left: ... ; if node.right: ...`), and
        return that sum.

COMPLEXITY TARGET
------------------
    Recursive (accumulator passed down): O(n) time, O(h) space (call
                                          stack, h = tree height)
    Iterative (explicit stack of (node, numberSoFar) pairs): O(n) time,
                                          O(n) space in the worst case
================================================================================
"""

from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def sumNumbers(self, root: Optional[TreeNode]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 013_sum_root_to_leaf_numbers_question.py
# ==============================================================================
def build(values):
    """Level-order build with None gaps, e.g. [1,2,3] or [4,9,0,5,1,None,None,None,None,None,None]."""
    if not values or values[0] is None:
        return None
    nodes = [TreeNode(v) if v is not None else None for v in values]
    kids = iter(nodes[1:])
    for node in nodes:
        if node is None:
            continue
        node.left = next(kids, None)
        node.right = next(kids, None)
    return nodes[0]


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 2, 3], 25),
        ([4, 9, 0, 5, 1], 1026),
        ([0], 0),
    ]
    passed = 0
    for values, expected in cases:
        root = build(values)
        got = sol.sumNumbers(root)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  sumNumbers({values}) -> {got}  (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
