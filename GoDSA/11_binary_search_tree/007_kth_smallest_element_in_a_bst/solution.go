package main

import "fmt"

/*
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
*/

func main() {
	fmt.Println("Solution for Kth Smallest Element in a BST not implemented yet")
}
