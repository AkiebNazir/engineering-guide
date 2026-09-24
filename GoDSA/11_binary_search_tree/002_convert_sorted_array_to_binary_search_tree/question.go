package main

/*
================================================================================
QUESTION · LeetCode 108 · Convert Sorted Array to Binary Search Tree    [Easy]
https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/
================================================================================

PROBLEM
-------
Given an integer array `nums` where the elements are sorted in ASCENDING
order, convert it to a HEIGHT-BALANCED binary search tree.

A height-balanced binary tree is one in which, for every node, the depths of
its two subtrees differ by no more than 1.


EXAMPLES
--------
Example 1:
    Input:  nums = [-10,-3,0,5,9]
    Output: [0,-3,9,-10,null,5]

            0                        0
           ╱ ╲                      ╱ ╲
        -3    9        or        -10   5
        ╱    ╱                      ╲    ╲
     -10    5                       -3    9

    BOTH are accepted. The answer is NOT unique — any height-balanced BST
    over these values is correct.

Example 2:
    Input:  nums = [1,3]
    Output: [3,1]      ([1,null,3] is also accepted)


CONSTRAINTS
-----------
    1 <= nums.length <= 10^4
    -10^4 <= nums[i] <= 10^4
    nums is sorted in a strictly increasing order.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Read the topic's one big idea backwards. An in-order traversal of a BST is
a sorted sequence — so a sorted array IS an in-order traversal, and this
problem asks you to invert that mapping. Which element is the root?

Any element `nums[i]` could be a legal root (everything left of it goes in
the left subtree, everything right of it goes right). But only the MIDDLE
one balances the two sides:

    nums = [-10, -3, 0, 5, 9]
                     ^ mid = index 2 -> root = 0
    left  = [-10, -3]  -> recursively build the left subtree
    right = [5, 9]      -> recursively build the right subtree

Picking `nums[0]` as the root instead gives a right-leaning chain of height
n — a valid BST, but not height-balanced, so it fails the problem.

Because `mid` for an even-length slice can round either way, `[1,3]` gives
`[3,1]` with the right-mid and `[1,null,3]` with the left-mid. Both are
height-balanced. Any test for this problem must therefore CHECK THE
PROPERTIES (is it a BST, is it height-balanced, does its in-order equal the
input) rather than compare against one hard-coded shape.


PROGRESSIVE HINTS
------------------
Hint 1: The root has to split the array into two halves of nearly equal
        size. Which element does that?

Hint 2: Recurse on index ranges, not on slices. `helper(lo, hi)` costs O(1)
        per call; `helper(nums[:mid])` copies the array at every level and
        turns O(n) into O(n log n) time and space.

Hint 3: Use the half-open or fully-closed convention consistently and pick
        your base case to match: `lo > hi -> None` for closed `[lo, hi]`.


COMPLEXITY TARGET
------------------
    Time:  O(n) — every element becomes exactly one node
    Space: O(log n) recursion depth (plus O(n) for the tree itself)
================================================================================
*/

// TODO: Implement the stub
