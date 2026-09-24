"""
================================================================================
QUESTION · LeetCode 144 · Binary Tree Preorder Traversal                [Easy]
https://leetcode.com/problems/binary-tree-preorder-traversal/
================================================================================

PROBLEM
-------
Given the `root` of a binary tree, return the preorder traversal of its
nodes' values.

Preorder = visit the NODE first, then its LEFT subtree, then its RIGHT
subtree.


EXAMPLES
--------
Example 1:
    Input:  root = [1,null,2,3]
    Output: [1,2,3]

        1
         ╲
          2
         ╱
        3

Example 2:
    Input:  root = []
    Output: []

Example 3:
    Input:  root = [1]
    Output: [1]

Example 4:
    Input:  root = [1,2,3,4,5,null,8,null,null,6,7,9]
    Output: [1,2,4,5,6,7,3,8,9]


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [0, 100].
    -100 <= Node.val <= 100

FOLLOW UP
---------
    Recursive solution is trivial, could you do it iteratively?
    (That follow-up is not optional in an interview. Expect it every time.)


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
A traversal ORDER is nothing more than *where you put the "record the value"
line* relative to the two recursive calls:

    preorder:    record;  go left;  go right      <- this problem
    inorder:     go left; record;   go right      <- problem 002
    postorder:   go left; go right; record        <- problem 003

That is the whole distinction. Three problems, one function, one line moved.

    Tree:            1              preorder  = 1 2 4 5 3
                    / \             inorder   = 4 2 5 1 3
                   2   3            postorder = 4 5 2 3 1
                  ╱ ╲
                 4   5

The iterative form is the part interviewers actually probe, because it forces
you to say out loud what the call stack was doing for you. For preorder it is
short — one explicit stack, and you push RIGHT before LEFT so that LEFT is
popped first (a stack reverses the order in which you push).


READING THE INPUT FORMAT
-------------------------
LeetCode gives trees as a level-order (breadth-first) list where `null` marks
a missing child: `[3,9,20,null,null,15,7]` is

            3
          ╱   ╲
         9     20
              ╱  ╲
            15    7

The `build()` helper at the bottom of this file turns that list into real
`TreeNode` objects (Python `None` in place of `null`), and `to_level_order()`
turns a tree back into that notation so results can be compared. Both are
used by every problem in this folder — read them once here.


PROGRESSIVE HINTS
------------------
Hint 1: Recursively — write a nested `dfs(node)` that returns immediately on
        `None`, appends `node.val`, then calls itself on `node.left` and
        `node.right`. The output list lives in the enclosing scope.

Hint 2: Iteratively — a stack of nodes still to process. Pop one, record it,
        then push its children. Which child do you push FIRST if you want the
        LEFT one handled next?

Hint 3: A stack is last-in-first-out, so push RIGHT first and LEFT second.
        `if node.right: stack.append(node.right)` before the `.left` line.


COMPLEXITY TARGET
------------------
    Time:  O(n) — every node visited exactly once
    Space: O(h) auxiliary, h = tree height (call stack or explicit stack);
           O(n) in the worst case of a fully skewed tree, O(log n) if balanced.
           The output list itself is O(n) and is not counted as auxiliary.
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
    def preorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
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
        ([1, None, 2, 3], [1, 2, 3]),
        ([], []),
        ([1], [1]),
        ([1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9], [1, 2, 4, 5, 6, 7, 3, 8, 9]),
        ([3, 9, 20, None, None, 15, 7], [3, 9, 20, 15, 7]),
    ]
    for values, want in cases:
        got = sol.preorderTraversal(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<44} -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
