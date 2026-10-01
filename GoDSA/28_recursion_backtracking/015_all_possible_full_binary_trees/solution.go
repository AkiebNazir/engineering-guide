package main

import "fmt"

/*
================================================================================
LeetCode 894 · All Possible Full Binary Trees                           [Medium]
https://leetcode.com/problems/all-possible-full-binary-trees/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given an integer `n`, return a list of all possible full binary trees
with `n` nodes. Each node of each tree in the answer must have
`Node.val == 0`.

Each element of the answer is the root node of one possible tree. You
may return the final list of trees in any order.

A full binary tree is a binary tree where each node has exactly 0 or 2
children.

EXAMPLES
--------
Example 1:
    Input:  n = 7
    Output: [[0,0,0,null,null,0,0,null,null,0,0],
              [0,0,0,null,null,0,0,0,0],
              [0,0,0,0,0,0,0],
              [0,0,0,0,0,null,null,null,null,0,0],
              [0,0,0,null,null,0,0,0,0,null,null]]

Example 2:
    Input:  n = 3
    Output: [[0,0,0]]

CONSTRAINTS
-----------
    1 <= n <= 20

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The very first fact to notice: a full binary tree can ONLY have an ODD
number of nodes. Every node has 0 or 2 children, so nodes come in pairs
except the root — for even `n`, there is NO valid full binary tree at
all, and the answer must be an empty list, not a crash.

For odd `n`, the recursion splits `n - 1` (the nodes besides the root)
between a left subtree of size `L` and a right subtree of size `R`,
where `L + R = n - 1` and BOTH `L` and `R` must themselves be odd (or
zero) for their own subtrees to be full. This is the same "cross
product of every left shape with every right shape" combine pattern as
012, but the split sizes are constrained to odd values instead of every
integer.

    allPossibleFBT(n) -> list of tree roots:
        if n % 2 == 0: return []                          <- base case: impossible
        if n == 1: return [TreeNode(0)]                    <- base case: single leaf
        trees = []
        for L in range(1, n - 1, 2):                        <- L odd, 1..n-2
            R = n - 1 - L
            for left in allPossibleFBT(L):
                for right in allPossibleFBT(R):
                    trees.append(TreeNode(0, left, right))
        return trees

WHAT TO THINK ABOUT
--------------------
1. Why must `n` be odd for any full binary tree to exist? Prove it to
   yourself with a small parity argument, not just by testing examples.
2. Given the root uses up 1 node, how many are left to split between
   left and right, and why must BOTH shares independently be odd?
3. How is this the SAME shape as 012's cross product, and what's
   DIFFERENT about which split points `L` are even tried?
4. What is `allPossibleFBT(1)`, concretely, and why is it the smallest
   meaningful case (not `n = 0`, which is the "impossible" case, not a
   base case that returns something buildable)?

PROGRESSIVE HINTS
------------------
Hint 1: If `n` is even, return `[]` immediately — no full binary tree
        has an even number of nodes.
Hint 2: Base case for odd `n == 1`: return a list containing one single
        leaf node.
Hint 3: For `n > 1` (odd), loop `L` over ODD values from 1 to `n - 2`;
        set `R = n - 1 - L` (guaranteed odd too, since `n-1` is even and
        subtracting an odd L from an even number gives an odd R).
Hint 4: For each `L`, get `leftShapes = allPossibleFBT(L)` and
        `rightShapes = allPossibleFBT(R)`, then cross-product them into
        new `TreeNode(0, left, right)` trees, exactly like 012.

COMPLEXITY TARGET
------------------
    Time and space: dominated by the total number of full binary tree
                     shapes for n (related to Catalan numbers again,
                     restricted to odd splits) times O(n) per tree to
                     build it — memoizing on `n` avoids recomputing the
                     same smaller odd sizes across different splits.
================================================================================
*/

func main() {
	fmt.Println("Solution for All Possible Full Binary Trees not implemented yet")
}
