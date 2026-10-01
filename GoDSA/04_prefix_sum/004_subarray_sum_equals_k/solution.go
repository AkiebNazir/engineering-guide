package main

import "fmt"

/*
================================================================================
LeetCode 560 · Subarray Sum Equals K                                    [Medium]
https://leetcode.com/problems/subarray-sum-equals-k/
Topic: 04 · Prefix Sum
================================================================================

PROBLEM
-------
Given an array of integers `nums` and an integer `k`, return the TOTAL NUMBER
of contiguous subarrays whose sum equals `k`.

A subarray is a contiguous non-empty sequence of elements.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,1,1], k = 2
    Output: 2
    Explanation: [1,1] (indices 0-1) and [1,1] (indices 1-2) both sum to 2.

Example 2:
    Input:  nums = [1,2,3], k = 3
    Output: 2
    Explanation: [1,2] (indices 0-1) and [3] (index 2) both sum to 3.

Example 3:
    Input:  nums = [1,-1,0], k = 0
    Output: 3
    Explanation: [1,-1], [0], and [1,-1,0] all sum to 0.


CONSTRAINTS
-----------
    1 <= nums.length <= 2 * 10^4
    -1000 <= nums[i] <= 1000        <- NOTE: numbers CAN be NEGATIVE
    -10^7 <= k <= 10^7


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is THE flagship problem of the whole prefix-sum topic. It is the direct
"what if the numbers can be negative" answer to topic 03's LC 209 (Minimum
Size Subarray Sum), which only worked as a sliding window because its numbers
were guaranteed non-negative. Here they are not — so there is no monotone
window to grow or shrink, and a sliding window has no principled rule for
"should I extend or should I shrink?" Extending the window can make the sum
go up OR down.

The tool that DOES work with arbitrary sign is prefix sum + hashmap. Define

    prefix[0] = 0
    prefix[i] = nums[0] + nums[1] + ... + nums[i-1]

Then a subarray nums[l..r] sums to k exactly when

    prefix[r+1] - prefix[l] == k

Rearranged, for a FIXED r, this is a question about the PAST:

    prefix[l] == prefix[r+1] - k

So instead of scanning backwards for every r (which is the O(n^2) brute
force), keep a running prefix sum as you walk forward, and a hashmap counting
how many times each prefix value has occurred so far. At each index, the
number of valid subarrays ENDING here is exactly the count of prior prefixes
equal to `running - k` — an O(1) lookup.

    a = [1, 1, 1],  k = 2

      running prefixes as we walk: 1, 2, 3   (these are prefix[1], prefix[2], prefix[3])

      at running=2: is there an earlier prefix equal to 2 - 2 = 0? YES (the
                    empty prefix, before any element) -> subarray [1,1] (0..1)
      at running=3: is there an earlier prefix equal to 3 - 2 = 1? YES (seen
                    once, after index 0) -> subarray [1,1] (1..2)


THE SEED VALUE IS NOT OPTIONAL
-------------------------------
Initialise the map with `seen = {0: 1}` BEFORE the loop starts — the empty
prefix (sum of zero elements, "before index 0") has occurred once. Skip this
and every subarray that itself starts at index 0 is silently undercounted.
Build a broken variant with `seen = {}` and watch it fail on a case where the
whole array from the start sums to k.


WHAT TO THINK ABOUT
--------------------
1. Why does a sliding window not work here? What specifically breaks if you
   try to write `while running > k: l += 1` on an array containing a -5?

2. What exactly does the hashmap need to store: a boolean "have I seen this
   value," a first index, or a COUNT? Why does this problem specifically need
   a count and not just a first index? (Hint: [1,1,1], k=2 has TWO answers,
   both using running=2's map entry pattern differently — trace it.)

3. What must `seen` be initialised to, and why is `{0: 1}` — not `{}` — the
   only correct starting state? Construct an input where the difference is
   visible in the final answer.

4. In what order do you (i) look up `running - k` and add to the count, then
   (ii) record `running` itself into the map? Getting this backwards would
   let a subarray "match against itself" (a zero-length subarray) — work out
   why the order given actually prevents that on its own, or if it needs an
   explicit guard.

5. What is the brute-force complexity, and can you beat O(n^3) even without
   a hashmap? (Hint: an O(n^2) version exists using a running inner sum
   instead of re-summing every subarray from scratch.)

6. Can nums contain zeros? What does k = 0 look for, and does your solution
   handle it without special-casing?


PROGRESSIVE HINTS
------------------
Hint 1: prefix[r+1] - prefix[l] == k  <=>  prefix[l] == prefix[r+1] - k.
        You don't need the actual prefix array — a running total is enough.

Hint 2: seen = {0: 1}
        running = count = 0
        for x in nums:
            running += x
            count += seen.get(running - k, 0)
            seen[running] = seen.get(running, 0) + 1

Hint 3: The lookup happens BEFORE you record the current running sum into the
        map. If you recorded first, a single element equal to k would count
        itself against itself when k == 0 is involved in certain orders —
        work out exactly what would go wrong and why the given order avoids
        it.

Hint 4: The seed `{0: 1}` represents "the empty prefix has been seen once."
        Without it, any subarray starting at index 0 whose sum is exactly k
        is missed, because there is no earlier recorded prefix of 0 to match
        against.

Hint 5: This is a COUNTING problem (how many subarrays), not a "does one
        exist" or "how long is the longest" problem — so the map counts
        OCCURRENCES of each prefix value, not just a first index.


COMPLEXITY TARGET
------------------
    Time:  O(n)     — one pass, O(1) amortized hashmap ops per element
    Space: O(n)     — the map can hold up to n+1 distinct prefix values
================================================================================
*/

func main() {
	fmt.Println("Solution for Subarray Sum Equals K not implemented yet")
}
