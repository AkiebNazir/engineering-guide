package main

import "fmt"

/*
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
*/

func main() {
	fmt.Println("Solution for Insert into a Binary Search Tree not implemented yet")
}
