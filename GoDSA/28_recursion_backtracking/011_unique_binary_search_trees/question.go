package main

/*
================================================================================
LeetCode 96 · Unique Binary Search Trees                                [Medium]
https://leetcode.com/problems/unique-binary-search-trees/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given an integer `n`, return the number of structurally unique BST's
(binary search trees) which has exactly `n` nodes of unique values from
`1` to `n`.

EXAMPLES
--------
Example 1:
    Input:  n = 3
    Output: 5

Example 2:
    Input:  n = 1
    Output: 1

CONSTRAINTS
-----------
    1 <= n <= 19

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The values 1..n are fixed and sorted, so for ANY choice of root value `r`,
the BST property forces the left subtree to be built from exactly
`{1, ..., r-1}` and the right subtree from exactly `{r+1, ..., n}` — no
other split is possible. So the number of unique BSTs on `n` nodes is a
sum over every possible root choice, of (ways to build the left subtree)
times (ways to build the right subtree):

    numTrees(n) = sum over r in 1..n of
                  numTrees(r - 1) * numTrees(n - r)

This is a TREE recursion where subproblems OVERLAP heavily — computing
`numTrees(4)` needs `numTrees(3)`, `numTrees(2)`, `numTrees(1)`, and
`numTrees(0)` (base case), and each of THOSE recomputes even smaller
values again and again if done naively. This is deliberately placed to
feel exactly like naive Fibonacci (topic 09) — the fix is the same:
memoize on `n`. Note that only the COUNT of left/right possibilities
matters here, not their actual shapes — that harder version is 012.

WHAT TO THINK ABOUT
--------------------
1. Why does choosing a root value `r` completely determine which VALUES
   go left and which go right, with zero freedom left over?
2. `numTrees(n - r)` uses just the COUNT `n - r`, not the actual set of
   values `{r+1, ..., n}` — why is the number of unique BST shapes on
   `k` distinct sorted values always the same regardless of which k
   values they are? (Any set of k values in sorted order is
   structurally interchangeable — only relative order matters for BST
   shape counting.)
3. What's the base case, and why must `numTrees(0) = 1` (not 0)? (An
   empty subtree is exactly ONE valid "shape" — the absence of a
   subtree — needed so multiplying by it doesn't zero out the count
   when a root has no left or no right children.)
4. Without memoization, how many times does `numTrees(1)` get
   recomputed while computing `numTrees(10)`? Is this exponential,
   and if so why?

PROGRESSIVE HINTS
------------------
Hint 1: Base case: `numTrees(0) = 1` (the empty tree is one valid shape)
        and, equivalently, `numTrees(1) = 1`.
Hint 2: For a fixed `n`, loop `r` from 1 to `n` as the ROOT value; the
        left subtree has `r - 1` nodes, the right has `n - r` nodes.
Hint 3: `numTrees(n) = sum(numTrees(r-1) * numTrees(n-r) for r in 1..n)`.
Hint 4: Memoize on `n` (e.g. `@lru_cache` or a dict) — without it, this
        recomputes the same smaller `n` values exponentially many times,
        exactly like naive Fibonacci.

COMPLEXITY TARGET
------------------
    Naive recursive (no memo):     exponential (same growth as Catalan
                                    number computed the slow way)
    Memoized recursive:            O(n^2) time, O(n) space
    Iterative DP (bottom-up):      O(n^2) time, O(n) space
    Closed form (Catalan number):  O(n) time, O(n) space (or O(1) with a
                                    direct formula, modulo big-int cost)
================================================================================
*/

// TODO: Implement the stub
