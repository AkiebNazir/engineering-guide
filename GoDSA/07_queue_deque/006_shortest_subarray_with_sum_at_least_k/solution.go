package main

import "fmt"

/*
================================================================================
LeetCode 862 · Shortest Subarray with Sum at Least K                     [Hard]
https://leetcode.com/problems/shortest-subarray-with-sum-at-least-k/
Topic: 07 · Queue / Deque
================================================================================

PROBLEM
-------
Given an integer array `nums` and an integer `k`, return the length of the
SHORTEST, NON-EMPTY, CONTIGUOUS subarray of `nums` with a sum of at least
`k`. If there is no such subarray, return -1.


EXAMPLES
--------
Example 1:
    Input:  nums = [1], k = 1
    Output: 1

Example 2:
    Input:  nums = [1,2], k = 4
    Output: -1
    Explanation: no subarray sums to >= 4.

Example 3:
    Input:  nums = [2,-1,2], k = 3
    Output: 3
    Explanation: the whole array [2,-1,2] sums to 3; no shorter subarray
    reaches 3 (note the -1 — this is why the numbers being negative
    matters, see below).


CONSTRAINTS
-----------
    1 <= nums.length <= 10^5
    -10^5 <= nums[i] <= 10^5      <- NOTE: numbers CAN be NEGATIVE
    1 <= k <= 10^9


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is THE hard capstone of the topic, and it is deliberately identical in
WORDING to topic 03's LC 209 (Minimum Size Subarray Sum) except for one
constraint: `nums[i]` can be negative here. Topic 03's own guide names LC
862 explicitly as the trap — read that section before attempting this.

WHY SLIDING WINDOW FAILS: a sliding window's shrink step (`l += 1`) is only
safe when growing the window can only ever help the sum move in one
direction. With negative numbers, growing the window can make the sum go
UP or DOWN — there's no principled rule for "should I shrink from the
left?" A window that looks invalid now might become valid again after
growing past a negative number, so shrinking away the left side can throw
away a real answer.

THE TOOL THAT WORKS: prefix sums (topic 04) turn "sum of nums[l..r]" into
`prefix[r+1] - prefix[l]`, so "sum >= k" becomes a comparison between two
prefix values:

    prefix[r+1] - prefix[l] >= k    <=>    prefix[l] <= prefix[r+1] - k

For each r, you want the LARGEST valid `l` (closest to r+1, for the
shortest length) satisfying that inequality. A MONOTONIC DEQUE of indices
(with strictly increasing prefix values) lets you find and discard
candidates in O(1) amortized:

- **Front of the deque**: once `prefix[r+1] - prefix[dq[0]] >= k`, that
  front index is a valid, and now PERMANENTLY useless-to-reconsider, left
  endpoint — record the length and pop it for good (later r's can only
  make that same l's subarray LONGER, never shorter).

- **Back of the deque**: before appending index `r+1`, pop any index `j`
  from the back with `prefix[j] >= prefix[r+1]` — `r+1` is both MORE
  RECENT (a shorter resulting subarray) and has a SMALLER OR EQUAL prefix
  (at least as easy to satisfy `>= k`), so `j` can never win again.


WHAT TO THINK ABOUT
--------------------
1. Construct a small array with a negative number where a naive sliding
   window (`while running_sum >= k: shrink`) gives the WRONG answer. Trace
   it by hand and see exactly where the shrink logic breaks.

2. Why do you need `prefix[l] <= prefix[r+1] - k` for the LARGEST valid
   `l`, not just ANY valid `l`? What does "largest l" buy you for the
   shortest-length objective?

3. Explain the front-pruning rule: once a deque-front index is used to
   record an answer, why can it never produce a BETTER (shorter) answer
   later, and so can be discarded forever?

4. Explain the back-pruning rule: why does a later index `r+1` with
   `prefix[r+1] <= prefix[j]` make an earlier index `j` USELESS forever,
   for BOTH the "does it satisfy `>= k`" test and the "how long is the
   resulting subarray" question?

5. What is the total number of deque push/pop operations across the whole
   algorithm, in terms of n? Derive the O(n) bound, don't just assert it.

6. Why doesn't a plain sorted structure (e.g. binary search into a sorted
   list of prefixes) improve on the deque's O(n) — what would its
   complexity be, and why is the deque strictly better here?


PROGRESSIVE HINTS
------------------
Hint 1: Build `prefix[0..n]` first (topic 04's mechanism). The problem is
        now about pairs of indices into `prefix`, not about `nums`
        directly.

Hint 2: For each `r+1`, you want the largest `l < r+1` with
        `prefix[l] <= prefix[r+1] - k`. Maintaining a deque of indices with
        INCREASING prefix values lets you binary-search-like discard from
        both ends in O(1) amortized instead of needing an actual binary
        search.

Hint 3: Deque invariant: `prefix[dq[0]] < prefix[dq[1]] < ... `
        (strictly increasing left to right).

Hint 4:
    from collections import deque
    prefix = [0]*(n+1)
    for i, x in enumerate(nums): prefix[i+1] = prefix[i] + x
    dq = deque()
    best = n + 1
    for i, p in enumerate(prefix):
        while dq and p - prefix[dq[0]] >= k:
            best = min(best, i - dq.popleft())
        while dq and prefix[dq[-1]] >= p:
            dq.pop()
        dq.append(i)
    return best if best <= n else -1

Hint 5: The FRONT while-loop must run fully (not just once) at each step —
        several early indices might all satisfy `>= k` simultaneously once
        the prefix has grown enough.


COMPLEXITY TARGET
------------------
    Time:  O(n)     — each index pushed once, popped at most once, from
                       either end
    Space: O(n)     — the prefix array and the deque
================================================================================
*/

func main() {
	fmt.Println("Solution for Shortest Subarray with Sum at Least K not implemented yet")
}
