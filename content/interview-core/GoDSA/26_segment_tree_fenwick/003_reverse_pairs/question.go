package main

/*
================================================================================
LeetCode 493 · Reverse Pairs                                              [Hard]
https://leetcode.com/problems/reverse-pairs/
Topic: 26 · Segment Tree & Fenwick (BIT)
================================================================================

PROBLEM
-------
Given an integer array `nums`, return the number of "reverse pairs" in the
array.

A reverse pair is a pair `(i, j)` where:

    0 <= i < j < nums.length
    nums[i] > 2 * nums[j]


EXAMPLES
--------
Example 1:
    Input:  nums = [1, 3, 2, 3, 1]
    Output: 2
    Explanation:
        The reverse pairs are:
            (1, 4) -> nums[1]=3, nums[4]=1, 3 > 2*1=2  [OK]
            (3, 4) -> nums[3]=3, nums[4]=1, 3 > 2*1=2  [OK]

Example 2:
    Input:  nums = [2, 4, 3, 5, 1]
    Output: 3
    Explanation:
        (1, 4) -> 4 > 2*1=2  [OK]
        (2, 4) -> 3 > 2*1=2  [OK]
        (3, 4) -> 5 > 2*1=2  [OK]


CONSTRAINTS
-----------
    1 <= nums.length <= 5 * 10^4
    -2^31 <= nums[i] <= 2^31 - 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The naive double loop (`for i: for j > i: if nums[i] > 2*nums[j]: count++`)
is O(n^2) and will not pass at n = 5*10^4 (up to 2.5*10^9 comparisons).

The key realization (topic guide Part 0): this is NOT a running-aggregate
problem like topic 04's prefix sum — it's a CROSS-INDEX PAIR COUNT over the
whole array, which is exactly the shape a modified merge sort solves for
free. When merge sort recurses, it eventually has two SORTED halves in
front of it right before merging them. Because both halves are sorted, you
can count, for every element in the left half, how many elements in the
right half satisfy `left[i] > 2*right[j]` using a two-pointer scan that
NEVER backtracks — giving O(n) counting work per merge level, O(n log n)
total across all levels combined with the sort itself.

An alternative (see topic guide Part 3): coordinate-compress the values,
then use a Fenwick tree, inserting from one end and querying "how many
already-inserted values satisfy the condition" as you go. Genuinely
equivalent in complexity — the merge-sort version is what's taught as
primary here because it needs no separate compression step.


WHAT TO THINK ABOUT
--------------------
1. The counting step happens BEFORE the merge step (while the two halves
   are still separately sorted arrays occupying contiguous positions) —
   count first using the pre-merge sorted subarrays, THEN merge them for
   the next level up.

2. The comparison is `nums[i] > 2 * nums[j]`, not `nums[i] > nums[j]` — the
   two-pointer condition and the actual merge-sort comparison
   (`nums[i] <= nums[j]`, standard merge) are DIFFERENT, and mixing them up
   (using the doubled condition for the merge itself) is a common bug.

3. `2 * nums[j]` can overflow a 32-bit int in a fixed-width language (values
   go up to `2^31 - 1`); use 64-bit arithmetic there. Python ints don't
   overflow, but it's worth knowing why this problem's constraint range
   looks the way it does.

4. This function must eventually leave the RECURSIVE calls with sorted
   subarrays, or the two-pointer counting logic at the next level up is
   invalid (it assumes sortedness). Don't skip actually merging.


PROGRESSIVE HINTS
------------------
Hint 1: Standard merge sort, but do EXTRA work right before each merge: for
        each element in the left half, use a moving pointer into the right
        half to count qualifying pairs in O(1) amortized per element.

Hint 2: The right-half pointer for the counting step only ever moves
        FORWARD as the left-half pointer advances (both halves are sorted)
        — never reset it to the start of the right half mid-loop.

Hint 3: After counting cross-pairs at this level, actually MERGE the two
        sorted halves into one sorted array before returning — the parent
        call's counting step depends on receiving two truly sorted halves.


COMPLEXITY TARGET
------------------
    Time:  O(n log n)
    Space: O(n) (merge sort's auxiliary array)
================================================================================
*/

// TODO: Implement the stub
