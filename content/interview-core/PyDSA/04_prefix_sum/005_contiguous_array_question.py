"""
================================================================================
LeetCode 525 · Contiguous Array                                         [Medium]
https://leetcode.com/problems/contiguous-array/
Topic: 04 · Prefix Sum
================================================================================

PROBLEM
-------
Given a binary array `nums` (only 0s and 1s), return the length of the
LONGEST contiguous subarray with an equal number of 0s and 1s.


EXAMPLES
--------
Example 1:
    Input:  nums = [0,1]
    Output: 2
    Explanation: [0,1] is the longest with equal 0s and 1s.

Example 2:
    Input:  nums = [0,1,0]
    Output: 2
    Explanation: [0,1] or [1,0], either has one 0 and one 1.

Example 3:
    Input:  nums = [0,1,0,0,1,1,0]
    Output: 6
    Explanation: Several subarrays work, e.g. indices 1..6 = [1,0,0,1,1,0]
                 has three 0s and three 1s.


CONSTRAINTS
-----------
    1 <= nums.length <= 10^5
    nums[i] is 0 or 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

nums only contains 0s and 1s, so this LOOKS like it should be a sliding
window (topic 03) — but there is no monotone validity condition here. Growing
a window by one element can turn a "balanced" subarray into an unbalanced one
in EITHER direction (add a 0, tip toward 0s; add a 1, tip toward 1s), and
there's no rule for which way to shrink. This is a prefix-sum + hashmap
problem, same family as problem 004, just with a different transform and a
different map shape.

THE TRANSFORM. Treat every 0 as -1 and every 1 as +1. A subarray has an equal
count of 0s and 1s exactly when its TRANSFORMED SUM is 0:

    nums       = [0, 1, 0, 0, 1, 1, 0]
    transformed= [-1, 1, -1, -1, 1, 1, -1]

Now "equal 0s and 1s in nums[l..r]" becomes "transformed sum of [l..r] is 0",
which — same algebra as problem 004 — becomes:

    prefix[r+1] - prefix[l] == 0   <=>   prefix[r+1] == prefix[l]

Two EQUAL prefix values bracket a balanced subarray. This is different from
problem 004: there you needed to COUNT how many times each prefix value
recurred; here you want the LONGEST span, so for each prefix value you only
need to remember the EARLIEST index it occurred at — pairing with the
earliest occurrence always gives the widest possible span.


WHAT TO THINK ABOUT
--------------------
1. Why is "equal 0s and 1s" not a sliding-window condition, even though the
   array only has two possible values? What exactly fails if you try
   `while count0 != count1: shrink`?

2. After mapping 0 -> -1 and 1 -> +1, what does "prefix[r+1] == prefix[l]"
   mean physically about the subarray between them?

3. Should the map store a COUNT (like problem 004) or a first INDEX? Why does
   wanting the LONGEST subarray specifically require "first index," and what
   goes wrong if you overwrite the stored index every time a prefix value
   recurs?

4. What must the map be seeded with before the loop starts, and why is the
   seeded index -1 rather than 0? (Hint: what index would a subarray starting
   at position 0 need to pair against?)

5. Is it possible for the answer to be the whole array? What input makes
   that true? Is it possible for the answer to be 0?

6. Construct an input where the best subarray does NOT start at index 0.


PROGRESSIVE HINTS
------------------
Hint 1: running = 0; for each element, running += 1 if nums[i] == 1 else -1.

Hint 2: seen = {0: -1}          # prefix value -> EARLIEST index it occurred,
                                  # -1 = "before index 0" (the sentinel)
        for i, x in enumerate(nums):
            running += 1 if x == 1 else -1
            if running in seen:
                best = max(best, i - seen[running])
            else:
                seen[running] = i

Hint 3: The `else` branch is doing the important work: it records a prefix
        value ONLY the first time it is seen. If you unconditionally wrote
        `seen[running] = i` every time (no `else`), later occurrences would
        overwrite the earliest index, and pairing against a LATER occurrence
        gives a SHORTER span than the true answer. Construct an input that
        exposes this before writing any code.

Hint 4: The sentinel `seen = {0: -1}` represents "the empty prefix occurs at
        index -1, one position before the array starts." Without it, a
        balanced subarray beginning at index 0 has nothing to pair against.

Hint 5: `i - seen[running]`, not `i - seen[running] + 1`. Work out why by
        testing on nums = [0, 1] by hand: seen={0:-1}, at i=0 running=-1
        (new), at i=1 running=0 -> found at seen[0]=-1 -> length = 1-(-1) = 2.
        Correct.


COMPLEXITY TARGET
------------------
    Time:  O(n)     — one pass, O(1) amortized hashmap ops per element
    Space: O(n)     — the map can hold up to n+1 distinct running values,
                      though in this problem running is bounded to [-n, n]
================================================================================
"""

from typing import List


class Solution:
    def findMaxLength(self, nums: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 005_contiguous_array_question.py
# ==============================================================================
def _brute(nums):
    """O(n^2) reference: for every (l, r), count 0s and 1s directly."""
    n = len(nums)
    best = 0
    for i in range(n):
        zeros = ones = 0
        for j in range(i, n):
            if nums[j] == 0:
                zeros += 1
            else:
                ones += 1
            if zeros == ones:
                best = max(best, j - i + 1)
    return best


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([0, 1], 2),
        ([0, 1, 0], 2),
        ([0, 1, 0, 0, 1, 1, 0], 6),
        ([0], 0),
        ([1], 0),
        ([0, 0, 0], 0),
        ([1, 1, 1], 0),
        ([0, 1, 1, 0], 4),
        ([1, 0, 1, 0, 1, 0], 6),                   # alternating: whole array
        ([1, 1, 0, 0, 1, 0, 1, 1], 8),
        ([1, 1, 1, 0, 0, 0], 6),
        ([0, 0, 1, 0, 0, 1, 1, 1], 8),
        ([1, 0, 0, 1, 0, 0, 1, 1], 6),              # best subarray not the whole array
        ([1, 1, 0, 1, 1, 1, 0, 0, 1, 1], 4),
    ]

    passed = 0
    for nums, expected in cases:
        assert _brute(nums) == expected, (
            f"bad test expectation for {nums!r}: "
            f"oracle says {_brute(nums)}, test says {expected}")
        got = sol.findMaxLength(list(nums))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<36} -> {got}  "
              f"(want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
