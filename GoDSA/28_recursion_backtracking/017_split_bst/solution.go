package main

import "fmt"

/*
================================================================================
LeetCode 776 · Split BST                                                [Medium]
https://leetcode.com/problems/split-bst/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given the root of a binary search tree (BST) and a value `target`,
split the tree into two subtrees where one subtree has nodes that are
all smaller or equal to the target value, while the other subtree has
all nodes that are greater than the target value. It is not necessarily
the case that the tree contains a node with value `target`.

Additionally, most of the structure of the original tree should remain.
Formally, for any child `c` with parent `p` in the original tree, if
they are both in the same subtree after the split, then node `c` should
still have the parent `p`.

Return an array of the two roots of the two subtrees, in any order.

EXAMPLES
--------
Example 1:
    Input:  root = [4,2,6,1,3,5,7], target = 2
    Output: [[2,1],[4,3,6,null,null,5,7]]

Example 2:
    Input:  root = [1], target = 1
    Output: [[1],[]]

CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 50].
    0 <= Node.val, target <= 1000

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the BST-property version of "return a pair" recursion: instead
of computing two NUMBERS per node (like 014), each call returns two
TREE ROOTS — `(smallerOrEqualRoot, greaterRoot)` — and the BST ordering
tells you exactly how to build them without re-checking every value.

If `node.val <= target`, the ENTIRE left subtree is automatically
`<= target` (BST property), so it stays whole on the "smaller-or-equal"
side; only the RIGHT subtree might straddle the target and needs to be
split recursively. Symmetrically, if `node.val > target`, the entire
right subtree is automatically `> target`, and only the LEFT subtree
needs splitting.

    splitBST(node, target):
        if node is None: return (None, None)                    <- base case
        if node.val <= target:
            smaller, greater = splitBST(node.right, target)       <- only right can straddle
            node.right = smaller                                  <- reattach the small part here
            return (node, greater)                                 <- node itself stays on the "smaller" side
        else:
            smaller, greater = splitBST(node.left, target)        <- only left can straddle
            node.left = greater                                    <- reattach the greater part here
            return (smaller, node)                                  <- node itself stays on the "greater" side

WHAT TO THINK ABOUT
--------------------
1. If `node.val <= target`, why is it guaranteed that node's ENTIRE
   left subtree also satisfies `<= target`, with zero exceptions?
2. Which single child (left or right) can ever contain a mix of values
   both `<= target` and `> target`, given `node.val <= target`? Why
   only that one?
3. After recursing into `node.right` and getting back `(smaller,
   greater)`, why does `node.right` get reassigned to `smaller` (not
   `greater`)? What is `node` doing with the piece it keeps versus the
   piece it hands back up?
4. Why does this problem NOT need to search for where `target` actually
   sits in the tree first — the recursion handles that implicitly by
   which branch it takes at each node.

PROGRESSIVE HINTS
------------------
Hint 1: Base case: `node is None` -> return `(None, None)` — nothing to
        split.
Hint 2: If `node.val <= target`, `node` and its ENTIRE left subtree
        belong on the "smaller-or-equal" side already; only `node.right`
        might need splitting further.
Hint 3: Recurse: `smaller, greater = splitBST(node.right, target)`.
        Reattach: `node.right = smaller` (keep the small part of what
        used to be the right subtree attached to `node`). Return
        `(node, greater)`.
Hint 4: Mirror this exactly for the `node.val > target` case, swapping
        left/right and which return slot `node` occupies.

COMPLEXITY TARGET
------------------
    Recursive: O(h) time (only follows ONE path down the tree, not the
               whole tree — h = tree height), O(h) space (call stack)
================================================================================
*/

func main() {
	fmt.Println("Solution for Split BST not implemented yet")
}
