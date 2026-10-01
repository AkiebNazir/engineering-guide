"""
================================================================================
QUESTION · LeetCode 450 · Delete Node in a BST                       [Medium]
https://leetcode.com/problems/delete-node-in-a-bst/
================================================================================

PROBLEM
-------
Given a root node reference of a BST and a key, delete the node with the
given key in the BST. Return the root node reference (possibly updated) of
the BST.

Basically, the deletion can be divided into two stages:
    1. Search for the node to remove.
    2. If the node is found, delete the node.


EXAMPLES
--------
Example 1:
    Input:  root = [5,3,6,2,4,null,7], key = 3
    Output: [5,4,6,2,null,null,7]

            5                          5
           ╱ ╲                        ╱ ╲
          3   6        ->            4   6
         ╱ ╲   ╲                    ╱     ╲
        2   4   7                  2       7

    Explanation: another accepted answer is [5,2,6,null,4,null,7]:

            5
           ╱ ╲
          2   6
           ╲   ╲
            4   7

    Both are valid — one promoted the in-order SUCCESSOR (4), the other the
    in-order PREDECESSOR (2).

Example 2:
    Input:  root = [5,3,6,2,4,null,7], key = 0
    Output: [5,3,6,2,4,null,7]      (key not found: return the tree unchanged)

Example 3:
    Input:  root = [], key = 0
    Output: []


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [0, 10^4].
    -10^5 <= Node.val <= 10^5
    Each node has a UNIQUE value.
    root is a valid binary search tree.
    -10^5 <= key <= 10^5

FOLLOW UP
---------
    Could you solve it with time complexity O(height of tree)?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the hardest of the "easy" BST problems and the most error-prone
problem in the topic. Finding the node is problem 001. The difficulty is
entirely in what to put in the hole afterwards.

THREE CASES, and you must name all three before writing any code:

  1. LEAF (no children)         -> just remove it. Nothing needs a new home.

            5              5
           ╱ ╲            ╱ ╲
          3   6    ->    3   6      delete 7
         ╱ ╲   ╲        ╱ ╲
        2   4   7      2   4

  2. ONE CHILD                   -> promote that child into the node's place.
                                     The child's whole subtree already sits on
                                     the correct side of every ancestor.

            5              5
           ╱ ╲            ╱ ╲
          3   6    ->    3   7      delete 6 (only a right child)
         ╱ ╲   ╲        ╱ ╲
        2   4   7      2   4

  3. TWO CHILDREN                -> you cannot promote either child (each has
                                    its own two subtrees, and the hole has room
                                    for one node). Instead:
                                      a. find the node's IN-ORDER SUCCESSOR =
                                         the MINIMUM of its right subtree
                                         (walk right once, then left forever);
                                      b. copy that value into the node;
                                      c. delete THAT node from the right
                                         subtree — and it is guaranteed to be
                                         case 1 or case 2, because the minimum
                                         of a subtree has no left child.

            5                    5
           ╱ ╲                  ╱ ╲
          3   6      ->        4   6         delete 3
         ╱ ╲                  ╱
        2   4                2

     The successor (4) is the smallest value larger than 3, so it is larger
     than everything in 3's left subtree and smaller than everything else in
     3's right subtree: it is the unique value that can sit in 3's slot.
     The in-order PREDECESSOR (max of the left subtree) works identically.


PROGRESSIVE HINTS
------------------
Hint 1: Write the search first. `if key < root.val: ... elif key > root.val:
        ... else: <delete this node>`.

Hint 2: The reason to write it recursively is the re-attachment idiom:
            root.left = self.deleteNode(root.left, key)
        The recursive call returns whatever the left subtree's root is NOW —
        which for a delete really can be a different node than before. The
        parent overwriting its own child pointer with that return value is
        what keeps the tree connected.

Hint 3: In the two-children case you do not need to move any pointers at
        all: copy the successor's VALUE into the node, then recursively
        delete the successor from the right subtree.

Hint 4: `min` of a subtree = keep going left until `.left is None`.


COMPLEXITY TARGET
------------------
    Time:  O(h) — one descent to find the node, plus one more to find and
           remove the successor, and both walk the same single path
    Space: O(h) recursive, O(1) iterative-with-parent
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
    def deleteNode(self, root: Optional[TreeNode], key: int) -> Optional[TreeNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TEST HELPERS — the answer is not unique (successor OR predecessor), so the
# tests check the BST INVARIANT rather than a fixed shape
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
        ([5, 3, 6, 2, 4, None, 7], 3),
        ([5, 3, 6, 2, 4, None, 7], 0),      # not present
        ([], 0),
        ([5, 3, 6, 2, 4, None, 7], 5),      # the root, two children
        ([5, 3, 6, 2, 4, None, 7], 7),      # a leaf
        ([5, 3, 6, 2, 4, None, 7], 6),      # one child
        ([1], 1),
    ]
    for values, key in cases:
        root = sol.deleteNode(build(values), key)
        io = inorder(root)
        present = [v for v in values if v is not None]
        want = sorted(v for v in present if v != key)
        ok = io == want                     # sorted in-order == still a BST,
        all_ok &= ok                        # and the key is gone, nothing else lost
        print(f"{'PASS' if ok else 'FAIL'}  tree={values!r:<28} key={key:<4} "
              f"-> {to_level_order(root)}  inorder={io} (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
