package main

import "fmt"

/*
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
*/

func main() {
	fmt.Println("Solution for Delete Node in a BST not implemented yet")
}
