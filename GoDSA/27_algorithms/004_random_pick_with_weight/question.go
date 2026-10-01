package main

/*
================================================================================
QUESTION · LeetCode 528 · Random Pick with Weight                   [Medium]
https://leetcode.com/problems/random-pick-with-weight/
================================================================================

PROBLEM
-------
You are given a 0-indexed array of positive integers `w` where `w[i]`
describes the WEIGHT of the i-th index. You need to implement the function
`pickIndex`, which randomly picks an index in the range [0, w.length - 1]
(inclusive) and returns it. The probability of picking an index i is
`w[i] / sum(w)`.

Implement the `Solution` class:
    Solution(w)      Initializes the object with the array w.
    pickIndex()      Picks the index i in the range [0, w.length - 1] and
                     returns it. The PROBABILITY of returning i is
                     w[i] / sum(w).


EXAMPLES
--------
Example 1:
    Input:
        ["Solution", "pickIndex"]
        [[[1]], []]
    Output:
        [null, 0]
    Explanation:
        Solution solution = new Solution([1]);
        solution.pickIndex(); // always returns 0 since there's only one index.

Example 2:
    Input:
        ["Solution", "pickIndex", "pickIndex", "pickIndex", "pickIndex", "pickIndex"]
        [[[1, 3]], [], [], [], [], []]
    Output:
        [null, 1, 1, 1, 1, 0]
    Explanation:
        Solution solution = new Solution([1, 3]);
        solution.pickIndex(); // returns 1, with probability 3/4
        solution.pickIndex(); // returns 0, with probability 1/4


CONSTRAINTS
-----------
    1 <= w.length <= 10^4
    1 <= w[i] <= 10^5
    pickIndex will be called at most 10^4 times.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Each index i must be returned with probability EXACTLY w[i] / total, not
"roughly" -- this is weighted random sampling, different from the uniform
sampling in 001-003. The technique: build a PREFIX SUM array of the
weights (monotonically increasing since weights are positive), draw one
uniform random integer in [1, total], and binary search (bisect_right) for
the first prefix-sum bucket that is >= the draw. Each index's "bucket
width" in the prefix-sum line is exactly its own weight, so landing
uniformly on a random point along the total line hits index i with
probability exactly width_i / total = w[i] / total.

PROGRESSIVE HINTS
------------------
Hint 1: Precompute prefix sums of w in __init__: prefix[i] = w[0] + ... + w[i].
Hint 2: pickIndex() draws target = random.randint(1, prefix[-1]) (1-indexed
        so index 0's bucket is [1, w[0]], not [0, w[0]-1] -- pick whichever
        convention you're consistent about).
Hint 3: Use bisect.bisect_left(prefix, target) to find the first index
        whose prefix sum is >= target -- that's the answer index.
Hint 4: Draw ONE random number per call, not one per weight -- looping
        weight-by-weight with independent coin flips does not produce the
        correct joint distribution.

COMPLEXITY TARGET
------------------
    Time:  O(n) preprocessing in __init__, O(log n) per pickIndex() call
    Space: O(n) for the prefix sum array
================================================================================
*/

// TODO: Implement the stub
