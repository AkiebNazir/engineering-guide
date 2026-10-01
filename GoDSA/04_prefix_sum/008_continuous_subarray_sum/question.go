package main

/*
================================================================================
LeetCode 523 · Continuous Subarray Sum                                 [Medium]
https://leetcode.com/problems/continuous-subarray-sum/
Topic: 04 · Prefix Sum
================================================================================

PROBLEM
-------
Given an integer array `nums` and an integer `k`, return `True` if `nums` has
a CONTINUOUS subarray of SIZE AT LEAST TWO whose elements sum up to a
multiple of `k`, or `False` otherwise.

An integer `x` is a multiple of `k` if there exists an integer `n` such that
`x = n * k`. `0` is ALWAYS a multiple of `k`.


EXAMPLES
--------
Example 1:
    Input:  nums = [23,2,4,6,7], k = 6
    Output: True
    Explanation: [2,4] is a continuous subarray of size 2 whose sum is 6,
                 which is a multiple of 6.

Example 2:
    Input:  nums = [23,2,6,4,7], k = 6
    Output: True
    Explanation: [23,2,6,4,7] is an entire array whose sum is 42, which is a
                 multiple of 6. It is also a subarray of length 5, which is
                 >= 2. Another correct answer is [2,6,4], whose sum is 12.

Example 3:
    Input:  nums = [23,2,6,4,7], k = 13
    Output: False


CONSTRAINTS
-----------
    1 <= nums.length <= 10^5
    0 <= nums[i] <= 10^9
    0 <= k <= 2^31 - 1                <- NOTE: k CAN BE ZERO. This is the
                                          legacy constraint range; current
                                          LeetCode uses 1 <= k, but this file
                                          treats k=0 as a real, legal input
                                          because it is a genuine trap worth
                                          knowing how to handle correctly.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Same remainder trick as problem 007 (LC 974), but this problem asks a
different QUESTION and has a REAL trap in the details:

  - LC 974 (007): COUNT how many subarrays are divisible by k.
  - LC 523 (this): does ANY qualifying subarray of length >= 2 EXIST?

Because this is an existence question, not a count, this uses Variant B from
the topic guide (§1.4): a FIRST-INDEX map, `seen = {0: -1}`, not a counting
map. You want to know the EARLIEST index a remainder occurred, because
pairing with the earliest occurrence maximizes the gap between indices — and
that gap is exactly what the length >= 2 constraint checks.

THE ALGEBRA (same derivation as 007): a subarray `nums[l..r]` (0-indexed,
inclusive) has sum divisible by k exactly when `prefix[r+1] % k ==
prefix[l] % k` — i.e. the running prefix at position `r` (using 0-indexed
`running` updated as you scan, one entry per array index) and some EARLIER
running prefix share a remainder.

THE LENGTH >= 2 TRAP. It is not enough that two prefixes share a remainder —
they must be far enough apart. If `seen[r] = i` (an earlier occurrence's
INDEX, not yet +1'd for prefix offset) and the current index is `j`, the
subarray between them has length `j - i`. That must be `>= 2`. Concretely,
if a remainder occurs at consecutive indices (gap of 1), that is NOT a valid
answer — the subarray in between exists but has length 1, which is not
allowed. THIS IS THE #1 BUG IN THIS PROBLEM: forgetting the gap check, or
computing it off by one.

Because you only need the EARLIEST index (a longer gap can only help, never
hurt), do NOT overwrite `seen[remainder]` once it is set — same "first
occurrence wins" principle as problem 005 (LC 525, Contiguous Array) and the
`if value not in seen` line in the topic guide's §1.4 Variant B.

THE k = 0 TRAP — read this carefully, it is NOT a footnote:
"a multiple of k" is defined (LeetCode's own wording) as "x = n * k for some
integer n." Substitute k = 0: x = n * 0 = 0 for ANY n. So the ONLY multiple
of 0 is 0 itself. "Sum divisible by 0" therefore means EXACTLY "sum equals
0" — nothing else. `running % 0` is also undefined (ZeroDivisionError in
Python) so you cannot even compute a remainder when k = 0; you must branch.

The prefix-sum equivalence still holds with a raw-value check instead of a
remainder check: `sum(nums[l..r]) == 0  <=>  prefix[r+1] == prefix[l]`, i.e.
when k = 0 the map should be keyed on the RAW running prefix value (not a
remainder), looking for two prefixes that are EXACTLY equal, still with the
length >= 2 gap check. This isn't a hack — congruence mod 0 IS equality:
`a ≡ b (mod 0)` means `a - b` is a multiple of 0, i.e. `a - b == 0`, i.e.
`a == b`. So `key = running % k if k else running` is really the SAME
algorithm; k=0 is the case where the remainder computation degenerates to
plain equality, not a separate algorithm bolted on.


WHAT TO THINK ABOUT
--------------------
1. Which map variant does this problem need — counting (Variant A) or
   first-index (Variant B)? Why does an EXISTENCE question never need a count?

2. Construct, on paper, an input where two prefixes share a remainder at
   indices that are exactly 1 apart (gap = 1). What SHOULD the answer be for
   that pair, and what would a version WITHOUT the gap check incorrectly
   return?

3. Why is `seen = {0: -1}` the correct sentinel value (not `{0: 0}`)? What
   subarray starting at index 0 does this sentinel need to correctly bracket,
   and what index would that subarray's "before start" position be?

4. When a remainder recurs, should you update `seen[remainder]` to the newer
   index, or leave it at the earliest? Which choice maximizes the chance of
   satisfying the length >= 2 constraint on a LATER recurrence?

5. Work out, from the problem's own definition of "multiple," what the only
   possible multiple of 0 is. What does that imply your remainder computation
   must do instead when k == 0?

6. `nums=[0,0]`, `k=0`: is there a valid subarray? What is it, and why does
   your k=0 handling need to find it?


PROGRESSIVE HINTS
------------------
Hint 1: `seen = {0: -1}` before the loop — the empty prefix (before any
        element) is "at index -1," so a subarray starting at real index 0
        computes a gap of `0 - (-1) = 1`... wait, check that against the
        length-2 requirement carefully. (This is exactly where an off-by-one
        likes to hide — work the arithmetic by hand before trusting it.)

Hint 2: For each index `i`, `running += nums[i]`, then compute
        `key = running % k if k != 0 else running`.
        If `key in seen`: check `i - seen[key] >= 2` before returning True.
        Else: `seen[key] = i` (only on FIRST sighting — never overwrite).

Hint 3: The length check uses the CURRENT loop index `i` (0-indexed into
        `nums`) against the STORED index, not against a prefix-array index —
        get this consistent or the off-by-one will be invisible in some
        tests and wrong in others.

Hint 4: For k=0, since `nums[i] >= 0` per the constraints, prefix sums are
        non-decreasing — which means two EQUAL prefix sums with a gap >= 2
        can only happen if every element strictly between them is 0. As a
        sanity check (not a replacement): for k=0 the answer is exactly
        "does `nums` contain two ADJACENT zeros anywhere." Verify your
        general solution agrees with this specialized check.


COMPLEXITY TARGET
------------------
    Time:  O(n)          — one pass, O(1) hashmap ops per element
    Space: O(min(n, k))  — for k > 0, the map holds at most k remainders;
                           for k == 0, up to O(n) distinct raw prefix values
================================================================================
*/

// TODO: Implement the stub
