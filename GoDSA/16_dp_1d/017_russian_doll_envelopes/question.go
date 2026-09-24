package main

/*
================================================================================
LeetCode 354 · Russian Doll Envelopes                                     [Hard]
https://leetcode.com/problems/russian-doll-envelopes/
Topic: 16 · Dynamic Programming (1D)
================================================================================

PROBLEM
-------
You are given a 2D array of integers `envelopes` where envelopes[i] = [w, h]
is the width and height of an envelope.

One envelope can fit into another if and only if BOTH its width and height are
STRICTLY greater than the other envelope's width and height.

Return the maximum number of envelopes you can Russian doll (put one inside
the other). You cannot rotate an envelope.


EXAMPLES
--------
Example 1:
    Input:  envelopes = [[5,4],[6,4],[6,7],[2,3]]
    Output: 3
    Explanation: [2,3] => [5,4] => [6,7]

Example 2:
    Input:  envelopes = [[1,1],[1,1],[1,1]]
    Output: 1


CONSTRAINTS
-----------
    1 <= envelopes.length <= 10^5
    envelopes[i].length == 2
    1 <= w, h <= 10^5


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
In one dimension this would be Longest Increasing Subsequence (16_dp_1d/013).
Two dimensions make it harder, but a sort reduces it back to one:

    Sort by width ascending. Now any chain must go left to right, and you only
    need heights to be strictly increasing.

The catch is EQUAL widths. [3,4] and [3,5] have increasing heights but don't
nest (3 is not > 3). The trick: among equal widths, sort heights DESCENDING.
Then no two envelopes with the same width can both appear in an increasing
height sequence.

After that it's pure LIS on the heights, and LIS has an O(n log n) patience
sorting solution with binary search. At n = 10^5, O(n^2) DP is too slow.


WHAT TO THINK ABOUT
--------------------
1. Why exactly does "height descending for ties" prevent same-width nesting?

2. In the O(n log n) LIS, tails[i] = smallest possible tail of an increasing
   subsequence of length i + 1. For STRICTLY increasing, bisect_left or
   bisect_right?

3. What would the O(n^2) DP be, and how slow is it at 10^5?


PROGRESSIVE HINTS
------------------
Hint 1: envelopes.sort(key=lambda e: (e[0], -e[1])).

Hint 2: tails = []. For each height h: i = bisect_left(tails, h).
        If i == len(tails): append h, else tails[i] = h.

Hint 3: Return len(tails).


COMPLEXITY TARGET
------------------
    Time:  O(n log n)
    Space: O(n)
================================================================================
*/

// TODO: Implement the stub
