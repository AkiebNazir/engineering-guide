"""
================================================================================
LeetCode 974 · Subarray Sums Divisible by K                            [Medium]
https://leetcode.com/problems/subarray-sums-divisible-by-k/
Topic: 04 · Prefix Sum
================================================================================

PROBLEM
-------
Given an integer array `nums` and an integer `k`, return the number of
non-empty CONTIGUOUS subarrays whose SUM is divisible by `k`.


EXAMPLES
--------
Example 1:
    Input:  nums = [4,5,0,-2,-3,1], k = 5
    Output: 7
    Explanation: 7 subarrays have a sum divisible by 5:
        [4,5,0,-2,-3,1], [5], [5,0], [5,0,-2,-3], [0], [0,-2,-3], [-2,-3]

Example 2:
    Input:  nums = [5], k = 9
    Output: 0


CONSTRAINTS
-----------
    1 <= nums.length <= 3 * 10^4
    -10^4 <= nums[i] <= 10^4
    2 <= k <= 10^4                    <- NOTE: k is always >= 2 here (unlike
                                          problem 008, where k can be 0 or 1)


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is problem 004 (LC 560, Subarray Sum Equals K) with one twist: instead
of matching subarrays whose sum EQUALS a target, match subarrays whose sum is
DIVISIBLE BY k. `nums` can contain negatives, so there is no monotone window
here (topic guide §1.1) — this is a hashmap problem, not sliding window.

THE ALGEBRA. Let `prefix[i]` be the sum of the first `i` elements (topic
guide §1.0). A subarray `nums[l..r]` has sum divisible by k exactly when:

    sum(nums[l..r]) % k == 0
    (prefix[r+1] - prefix[l]) % k == 0
    prefix[r+1] % k == prefix[l] % k          <- (see the derivation below)

So a subarray is "good" exactly when its two bracketing prefixes have the
SAME REMAINDER mod k. Instead of a hashmap keyed on the raw prefix value
(problem 004), key it on `prefix % k`. As you scan left to right, for each
new running prefix, ask "how many earlier prefixes had this same remainder?"
— each one bounds off a distinct good subarray ending here.

WHY `(prefix[r+1] - prefix[l]) % k == 0` MEANS THE REMAINDERS ARE EQUAL: if
`A - B` is a multiple of k, then A and B differ by a multiple of k, so they
land in the same "bucket" when reduced mod k. This is modular arithmetic's
core fact, and it is exactly the same congruence idea as clock arithmetic:
9 o'clock and 21 o'clock are "the same time" mod 12 because they differ by
12. See the topic guide §1.5 for the formal statement.

A PYTHON-SPECIFIC WRINKLE THAT MATTERS HERE: `nums` contains negative values
per the constraints. In C, Java, or Go, `%` on a negative operand can return
a NEGATIVE result (`-5 % 7 == -5` in those languages), and you would need
`((x % k) + k) % k` to force it into `[0, k)` before using it as a dictionary
/ array key. Python's `%` is already sign-correct: it always returns a
result with the SAME SIGN AS THE DIVISOR, so for `k > 0`, `running % k` in
Python is already the canonical non-negative remainder in `[0, k)` — no
normalization needed. Confirm this for yourself before writing any code:
run `-5 % 7` in a Python REPL and see what comes back. (Spoiler in the guide,
§1.5 — but work it out yourself first.)


WHAT TO THINK ABOUT
--------------------
1. This wants a COUNT of subarrays, not the longest one. Which map variant
   from the topic guide's §1.4 is that — count occurrences, or record the
   first index? What sentinel value seeds the map, and why?

2. Why does keying on `prefix % k` instead of the raw `prefix` value bound
   the map to at most k entries, no matter how large `nums` or the prefix
   sums themselves get?

3. Convince yourself out loud: `-5 % 7` in Python. Is it negative? What would
   it be in Java? Why does that matter for using it as a dict key or an
   array index directly?

4. What subarray does the `{0: 1}` sentinel let you count that you would
   otherwise miss? (Same question as topic guide §1.3, one layer removed —
   think about which subarrays START at index 0.)

5. k = 1: every possible subarray sum is divisible by 1. Does your formula
   naturally produce `n*(n+1)/2` in that case, or does it need a special
   case?


PROGRESSIVE HINTS
------------------
Hint 1: `seen = {0: 1}` before the loop — the empty prefix has remainder 0,
        seen once, "before any element."

Hint 2: For each `x` in `nums`: `running += x`, then
        `remainder = running % k` (already correctly signed by Python).
        `count += seen.get(remainder, 0)`, then
        `seen[remainder] = seen.get(remainder, 0) + 1`.

Hint 3: This is Variant A (counting) from the topic guide's §1.4 — the exact
        same shape as problem 004, with the map keyed on a remainder instead
        of a raw sum.

Hint 4: Do NOT normalize the remainder yourself in Python — `running % k` is
        already in `[0, k)` for `k > 0`. Adding `((running % k) + k) % k` is
        harmless (it's a no-op here) but signals you're translating from a
        different language without checking Python's actual behavior.


COMPLEXITY TARGET
------------------
    Time:  O(n)          — one pass, O(1) hashmap ops per element
    Space: O(min(n, k))  — the map holds at most k distinct remainders
================================================================================
"""

from typing import List


class Solution:
    def subarraysDivByK(self, nums: List[int], k: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 007_subarray_sums_divisible_by_k_question.py
# ==============================================================================
def _brute(nums, k):
    """O(n^2) reference: every subarray, sum it, check % k == 0."""
    n = len(nums)
    count = 0
    for i in range(n):
        total = 0
        for j in range(i, n):
            total += nums[j]
            if total % k == 0:
                count += 1
    return count


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([4, 5, 0, -2, -3, 1], 5, 7),
        ([5], 9, 0),
        ([5], 5, 1),                       # single element, divisible
        ([1, 2, 3], 1, 6),                 # k=1: every subarray counts, n(n+1)/2 = 6
        ([-1, -2, -3], 3, 3),              # negatives: [-3], [-1,-2], [-1,-2,-3]
        ([2, 2, 2, 2, 2], 2, 15),          # all same remainder, maximizes count
        ([1, 2, 3, 4, 5, 6], 100, 0),      # k larger than any element/sum here
        ([0, 0, 0], 5, 6),                 # zeros are divisible by everything
        ([7], 7, 1),
        ([-5], 5, 1),                      # -5 % 5 == 0
    ]

    passed = 0
    for nums, k, expected in cases:
        oracle = _brute(nums, k)
        assert oracle == expected, (
            f"bad test expectation for {nums}, k={k}: "
            f"oracle says {oracle}, test says {expected}")
        got = sol.subarraysDivByK(nums, k)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {nums}, k={k} -> {got}  (want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
