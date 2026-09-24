package main

/*
================================================================================
LeetCode 95 · Unique Binary Search Trees II                             [Medium]
https://leetcode.com/problems/unique-binary-search-trees-ii/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given an integer `n`, return all the structurally unique BST's (binary
search trees), which has exactly `n` nodes of unique values from `1` to
`n`. Return the answer in any order.

EXAMPLES
--------
Example 1:
    Input:  n = 3
    Output: [[1,null,2,null,3],[1,null,3,2],[2,1,3],[3,1,null,null,2],
              [3,2,null,1]]
    (5 distinct tree shapes — matches numTrees(3) = 5 from problem 011.)

Example 2:
    Input:  n = 1
    Output: [[1]]

CONSTRAINTS
-----------
    1 <= n <= 8

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Same recurrence as 011 (choosing a root splits the range into a left part
and a right part), but now the "combine step" must BUILD actual TreeNode
objects instead of just counting them. This is the general-range version
of 011's `1..n`: because BST shape only depends on RELATIVE order, this
folder writes it directly as `build(lo, hi)` over an arbitrary range
`[lo, hi]`, which is more reusable than special-casing `1..n`.

    build(lo, hi) -> list of tree roots:
        if lo > hi: return [None]                       <- base case: one shape, the empty tree
        trees = []
        for r in range(lo, hi + 1):                       <- try every value as root
            for left in build(lo, r - 1):                  <- every possible left shape
                for right in build(r + 1, hi):               <- every possible right shape
                    trees.append(TreeNode(r, left, right))    <- CROSS PRODUCT: one tree per (left, right) pair
        return trees

The critical new idea versus 011: for a fixed root `r`, the number of
resulting trees is `len(leftShapes) * len(rightShapes)` — a CROSS
PRODUCT, built with a nested loop, because every left shape can be
paired with every right shape independently to form a distinct whole
tree.

WHAT TO THINK ABOUT
--------------------
1. What does `build(lo, hi)` return when `lo > hi` — and why must it be
   a list CONTAINING one `None`, not an empty list? (An empty list would
   mean "there are zero ways to build this subtree," but there's
   actually exactly one way — an empty tree — and that single "shape"
   must be paired with every combination on the other side, or the
   cross product below collapses to nothing.)
2. For a fixed root `r`, why is it a NESTED loop over left shapes and
   right shapes, rather than one loop appending pairs?
3. How does the total number of trees this function returns for
   `build(1, n)` relate to `numTrees(n)` from problem 011? (They must
   match exactly — 011's count IS `len(build(1, n))`, and this file's
   tests verify that directly rather than assuming it.)
4. Are the same TreeNode objects ever reused across different returned
   trees (e.g. the same empty-subtree `None` reused everywhere)? Is that
   safe here, given trees aren't mutated after being built?

PROGRESSIVE HINTS
------------------
Hint 1: Base case: `build(lo, hi)` for `lo > hi` returns `[None]` — a
        list with exactly one element, representing "the empty tree."
Hint 2: For each root value `r` from `lo` to `hi`, recursively get
        `leftShapes = build(lo, r-1)` and `rightShapes = build(r+1, hi)`.
Hint 3: For every `left` in `leftShapes` and every `right` in
        `rightShapes`, build a new `TreeNode(r, left, right)` and append
        it to the result.
Hint 4: The public method calls `build(1, n)`; if `n == 0`... (the
        constraint guarantees `n >= 1`, so this edge doesn't need
        separate handling here, unlike 011 which explicitly needed
        `numTrees(0) = 1`).

COMPLEXITY TARGET
------------------
    Time and space:  O(numTrees(n) * n) roughly — there are
                      Catalan(n) trees total, each with n nodes, and
                      building them all dominates the cost (the
                      recursion itself, WITHOUT memoizing the returned
                      lists by range, redundantly rebuilds the same
                      sub-shapes many times — naming this cost is part
                      of the exercise; memoizing on (lo, hi) fixes it).
================================================================================
*/

// TODO: Implement the stub
