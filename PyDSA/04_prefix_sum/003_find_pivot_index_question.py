"""
================================================================================
LeetCode 724 · Find Pivot Index                                         [Easy]
https://leetcode.com/problems/find-pivot-index/
Topic: 04 · Prefix Sum
================================================================================

PROBLEM
-------
Given an array of integers `nums`, calculate the PIVOT INDEX of this array.

The pivot index is the index where the sum of all the numbers strictly to
the LEFT of the index is equal to the sum of all the numbers strictly to the
RIGHT of the index.

If the index is on the left edge of the array, the left sum is 0, because
there are no elements to the left. This also applies to the right edge.

Return the LEFTMOST pivot index. If no such index exists, return -1.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,7,3,6,5,6]
    Output: 3
    Explanation: The pivot index is 3.
        Left sum  = nums[0] + nums[1] + nums[2] = 1 + 7 + 3 = 11
        Right sum = nums[4] + nums[5] = 5 + 6 = 11

Example 2:
    Input:  nums = [1,2,3]
    Output: -1
    Explanation: There is no index that satisfies the conditions in the
                 problem statement.

Example 3:
    Input:  nums = [2,1,-1]
    Output: 0
    Explanation:
        Left sum  = 0 (no elements to the left of index 0)
        Right sum = nums[1] + nums[2] = 1 + (-1) = 0


CONSTRAINTS
-----------
    1 <= nums.length <= 10^4
    -1000 <= nums[i] <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The brute force at index i re-sums the left side and the right side from
scratch:

    for i in range(n):
        left  = sum(nums[:i])
        right = sum(nums[i+1:])
        if left == right: return i

That is O(n) work PER index, times n indices, so O(n^2) overall — and it is
the exact trap the topic guide's Part 4 complexity table calls out
("recompute sum(a[l:r+1]) per query — the trap"). The fix carries a running
total instead of recomputing it:

    total   = sum(nums)              # computed once, up front
    leftSum = 0
    for i, x in enumerate(nums):
        rightSum = total - leftSum - x
        if leftSum == rightSum: return i
        leftSum += x
    return -1

At each index, `rightSum` is derived algebraically — `total` minus
everything already accounted for (the left side AND the current element) —
instead of being re-summed from `nums[i+1:]`. `leftSum` only ever grows by
one element per step, so the whole scan is O(n).

    nums = [1, 7, 3, 6, 5, 6],  total = 28

      i    leftSum    nums[i]    rightSum = total - leftSum - nums[i]
      0       0          1        28 - 0 - 1  = 27      0 != 27
      1       1          7        28 - 1 - 7  = 20      1 != 20
      2       8          3        28 - 8 - 3  = 17      8 != 17
      3      11          6        28 - 11 - 6 = 11     11 == 11  <- PIVOT
                          leftSum updates to 11+6=17 only AFTER the check


WHAT TO THINK ABOUT
--------------------
1. Do you need a stored prefix ARRAY (topic guide §1.0, like problem 002),
   or does a single running total suffice? What's different about this
   problem that changes the answer?

2. In what order do you (a) compute `rightSum` for the current index,
   (b) compare it to `leftSum`, (c) update `leftSum` for the next index?
   Getting this order wrong compares the wrong pair of sums.

3. What is `rightSum` when `i` is the LAST index? What is `leftSum` when
   `i` is the FIRST index? Neither should need a special case if the
   running-total formula is right.

4. What if NO pivot exists? What if EVERY index could be argued as a
   pivot (all zeros)? The problem says return the LEFTMOST — does your
   loop naturally stop at the first match, or does it need to be told to?


PROGRESSIVE HINTS
------------------
Hint 1: Compute `total = sum(nums)` once, before the loop.

Hint 2: Track `leftSum`, starting at 0. At each index i, the right sum is
        `total - leftSum - nums[i]` — total minus the left side minus the
        current element itself (which belongs to neither side).

Hint 3: Check `leftSum == rightSum` BEFORE updating `leftSum` for the next
        iteration — `leftSum` at the start of iteration i is exactly the
        sum of everything strictly left of i.

Hint 4: If the loop finishes without returning, return -1.


COMPLEXITY TARGET
------------------
    Time:  O(n)  — one pass to sum, one pass with a running total
    Space: O(1)  — no array needed, just a couple of running numbers
================================================================================
"""

from typing import List


class Solution:
    def pivotIndex(self, nums: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 003_find_pivot_index_question.py
# ==============================================================================
def _brute(nums):
    """O(n^2) reference: re-sum the left and right sides at every index."""
    n = len(nums)
    for i in range(n):
        left = sum(nums[:i])
        right = sum(nums[i + 1:])
        if left == right:
            return i
    return -1


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 7, 3, 6, 5, 6], 3),
        ([1, 2, 3], -1),                 # no pivot exists
        ([2, 1, -1], 0),                 # pivot at index 0 (leftSum = 0)
        ([-1, -1, 0, 1, 1, 0], 5),        # pivot at the LAST index
        ([5], 0),                        # single element -> trivially pivot 0
        ([0, 0, 0, 0], 0),                # all zeros -> leftmost (index 0) wins
        ([-1, -1, -1, -1, -1, -1], -1),   # no pivot with all-equal negatives
        ([1, -1, 1, -1, 1], 0),           # negatives mixed with positives
        ([0], 0),                        # single zero
        ([1, 0], 0),                     # pivot right at the start, right sum 0 too? check
    ]

    passed = 0
    for nums, expected in cases:
        # cross-check the hand-written expectation against the oracle
        assert _brute(nums) == expected, (
            f"bad test expectation for {nums!r}: "
            f"oracle says {_brute(nums)}, test says {expected}")
        got = sol.pivotIndex(list(nums))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {nums!r:<28} -> {got}  "
              f"(want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
