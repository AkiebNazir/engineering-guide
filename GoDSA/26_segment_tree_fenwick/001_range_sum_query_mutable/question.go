package main

/*
================================================================================
LeetCode 307 · Range Sum Query - Mutable                                [Medium]
https://leetcode.com/problems/range-sum-query-mutable/
Topic: 26 · Segment Tree & Fenwick (BIT)
================================================================================

PROBLEM
-------
Given an integer array `nums`, design a data structure that supports:

    NumArray(nums)               Build from the initial array.
    update(index, val) -> None   Set nums[index] = val.
    sumRange(left, right) -> int Return the sum of nums[left..right]
                                  INCLUSIVE, i.e. sum(nums[left] + ... +
                                  nums[right]).

Both `update` and `sumRange` must be efficient over many interleaved calls
(NOT re-summing the range from scratch every time, and NOT rebuilding a
whole prefix-sum array on every update).


EXAMPLES
--------
Example 1:
    Input:
        ["NumArray", "sumRange", "update", "sumRange"]
        [[[1, 3, 5]], [0, 2], [1, 2], [0, 2]]
    Output:
        [null, 9, null, 8]

    Explanation:
        numArray = NumArray([1, 3, 5])
        numArray.sumRange(0, 2)   # 1 + 3 + 5 = 9
        numArray.update(1, 2)     # nums becomes [1, 2, 5]
        numArray.sumRange(0, 2)   # 1 + 2 + 5 = 8


CONSTRAINTS
-----------
    1 <= nums.length <= 3 * 10^4
    -100 <= nums[i] <= 100
    0 <= index < nums.length
    -100 <= val <= 100
    0 <= left <= right < nums.length
    At most 3 * 10^4 calls will be made to update and sumRange.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is a DESIGN problem (topic guide Part 0): a fixed class signature
(`__init__`, `update`, `sumRange`) that a grading harness calls directly, in
sequence, with the array mutating between range queries.

The naive tools each fail one half of the workload:

    - Re-sum the range on every `sumRange` call: O(1) update, O(n) query.
    - Precompute a full prefix-sum array once: O(1) query, but any `update`
      invalidates every prefix sum from that index onward, so keeping it
      correct costs O(n) per update.

Neither is good enough once both operations are called many times. The
Fenwick tree (Binary Indexed Tree) gives O(log n) for BOTH, by storing
partial sums keyed off each index's binary representation instead of either
extreme (all raw values, or one fully-materialized running total).


WHAT TO THINK ABOUT
--------------------
1. A BIT is conventionally 1-INDEXED internally (index 0 is unusable — it
   would never have a nonzero "lowest set bit" to walk with). Map your
   0-indexed `nums` array to a `tree` array of size `n + 1`.

2. `update(index, val)` needs the DELTA (`val - nums[index]`), not `val`
   itself — the tree stores partial SUMS, so you add the difference to
   every node responsible for covering this index, then remember the new
   value for next time.

3. `sumRange(left, right) = prefix(right) - prefix(left - 1)`, exactly
   topic 04's inclusion-exclusion identity, where `prefix(i)` is "sum of
   nums[0..i] inclusive" answered by walking the tree.

4. The key arithmetic: `i & (-i)` isolates the lowest set bit of `i`. Walk
   UP (`i += i & -i`) to propagate an update to every ancestor; walk DOWN
   (`i -= i & -i`) to accumulate a prefix sum from descendants.


PROGRESSIVE HINTS
------------------
Hint 1: You need a structure that is neither "no precomputation" nor "full
        precomputation" — something in between that only recomputes
        O(log n) partial sums per update.

Hint 2: Build a 1-indexed array `tree` of size n+1. `update` and the prefix
        query both use the SAME bit trick, just walking in opposite
        directions: `i & -i`.

Hint 3: `sumRange(left, right)` is two prefix queries and a subtraction —
        write `_prefix(i)` once and reuse it, don't special-case the range
        sum separately.


COMPLEXITY TARGET
------------------
    Build:      O(n log n)  (n calls to update-style insertion) or O(n) with
                a direct build
    update:     O(log n)
    sumRange:   O(log n)
    Space:      O(n)
================================================================================
*/

// TODO: Implement the stub
