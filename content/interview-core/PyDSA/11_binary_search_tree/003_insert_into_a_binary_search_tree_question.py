"""
================================================================================
QUESTION · LeetCode 701 · Insert into a Binary Search Tree           [Medium]
https://leetcode.com/problems/insert-into-a-binary-search-tree/
================================================================================

PROBLEM
-------
You are given the `root` node of a binary search tree (BST) and a `value` to
insert into the tree. Return the root node of the BST after the insertion.
It is guaranteed that the new value does NOT exist in the original BST.

Notice that there may exist multiple valid ways for the insertion, as long
as the tree remains a BST after insertion. You can return ANY of them.


EXAMPLES
--------
Example 1:
    Input:  root = [4,2,7,1,3], val = 5
    Output: [4,2,7,1,3,5]

            4                          4
           ╱ ╲                        ╱ ╲
          2   7        ->            2   7
         ╱ ╲                        ╱ ╲  ╱
        1   3                      1  3 5

Example 2:
    Input:  root = [40,20,60,10,30,50,70], val = 25
    Output: [40,20,60,10,30,50,70,null,null,null,null,null,null,null,null,null,25]

Example 3:
    Input:  root = [4,2,7,1,3,null,null,null,null,null,null], val = 5
    Output: [4,2,7,1,3,5]


CONSTRAINTS
-----------
    The number of nodes in the tree will be in the range [0, 10^4].
    -10^8 <= Node.val <= 10^8
    All the values Node.val are UNIQUE.
    -10^8 <= val <= 10^8
    It's guaranteed that val does not exist in the original BST.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Search for `val` (problem 001). It is guaranteed not to be there, so the
search must fail — and where it falls off the bottom of the tree is exactly
the one place the new node can go without breaking anything.

    insert 5 into [4,2,7,1,3]:
        at 4: 5 > 4 -> right
        at 7: 5 < 7 -> left
        7.left is None  ->  THIS is the empty slot. Put the node here.

That is the whole algorithm: **descend as if searching, then hang the new
node on the None pointer you hit.** The new node is always a LEAF. You never
need to restructure anything, never need to move an existing node, and
never need to look at more than one root-to-leaf path.

The "any valid answer" clause in the statement refers to solutions that
rotate or re-root the tree; the leaf insert above is what every interviewer
is looking for and is what LeetCode's example output shows.

⚠️  Sting in the tail: repeat this operation with ASCENDING values and every
insert lands on the rightmost leaf, one level deeper than the last. n sorted
inserts build a chain of height n and cost O(n^2) in total. The solution
file measures exactly that.


PROGRESSIVE HINTS
------------------
Hint 1: You already know how to find where `val` WOULD be — that is problem
        001's descent. What do you do when you arrive at `None`?

Hint 2: To attach a node you need the PARENT, not the None you landed on.
        Either keep a trailing `parent` pointer in a loop, or let the
        recursion re-attach on the way back up:
            root.left = self.insertIntoBST(root.left, val)

Hint 3: Handle `root is None` first — inserting into an empty tree returns a
        brand-new single node, and that is also the recursion's base case.


COMPLEXITY TARGET
------------------
    Time:  O(h) — one root-to-leaf path
    Space: O(1) iterative, O(h) recursive
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
    def insertIntoBST(self, root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
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


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([4, 2, 7, 1, 3], 5),
        ([40, 20, 60, 10, 30, 50, 70], 25),
        ([], 1),
        ([1], 0),
        ([1], 2),
        ([4, 2, 7, 1, 3], 100),
        ([4, 2, 7, 1, 3], -100),
    ]
    for values, val in cases:
        root = sol.insertIntoBST(build(values), val)
        io = inorder(root)
        want = sorted([v for v in values if v is not None] + [val])
        ok = io == want                     # in-order sorted == still a BST,
        all_ok &= ok                        # and the value is present exactly once
        print(f"{'PASS' if ok else 'FAIL'}  tree={values!r:<28} val={val:<6} "
              f"-> {to_level_order(root)}  inorder={io} (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
