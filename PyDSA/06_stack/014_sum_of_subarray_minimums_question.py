"""
================================================================================
LeetCode 907 · Sum of Subarray Minimums                                 [Medium]
https://leetcode.com/problems/sum-of-subarray-minimums/
Topic: 06 · Stack & Monotonic Stack
================================================================================

PROBLEM
-------
Given an array of integers `arr`, find the sum of min(b), where b ranges over
every (contiguous) subarray of arr. Since the answer may be large, return it
modulo 10^9 + 7.


EXAMPLES
--------
Example 1:
    Input:  arr = [3, 1, 2, 4]
    Output: 17
    Explanation:
        Subarrays: [3], [1], [2], [4], [3,1], [1,2], [2,4], [3,1,2], [1,2,4],
                   [3,1,2,4]
        Minimums:   3,   1,   2,   4,   1,     1,     2,     1,       1,
                    1
        Sum = 17.

Example 2:
    Input:  arr = [11, 81, 94, 43, 3]
    Output: 444


CONSTRAINTS
-----------
    1 <= arr.length <= 3 * 10^4
    1 <= arr[i] <= 3 * 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
There are n(n+1)/2 subarrays: 450 million at n = 3 * 10^4. You can't visit
them. Flip the question around — this is the CONTRIBUTION TECHNIQUE:

    Instead of "for each subarray, what's its min?"
    ask        "for each element, in how many subarrays is it the min?"

    answer = sum( arr[i] * (number of subarrays where arr[i] is the minimum) )

arr[i] is the minimum of a subarray [L..R] exactly when L..R contains i and
no smaller element. If `left` = how far you can extend left before hitting a
smaller element, and `right` = the same to the right, then there are
left * right such subarrays.


WHAT TO THINK ABOUT
--------------------
1. For each i, find the index of the previous smaller element and the next
   smaller element. Which data structure does "previous/next smaller" in O(n)?

2. DUPLICATES. In [2, 2], the subarray [2, 2] has min 2 — but WHICH 2 gets the
   credit? If both do, you count it twice. How do you break ties?

3. When do you apply the modulo?


PROGRESSIVE HINTS
------------------
Hint 1: left[i]  = i - (index of previous element STRICTLY less than arr[i])
        right[i] = (index of next element LESS THAN OR EQUAL to arr[i]) - i
        Use -1 and n when none exists.

Hint 2: Both come from monotonic increasing stacks, one pass each (or one
        combined pass: when an element is popped, the element causing the pop
        is its "next smaller-or-equal", and the new top is its "previous
        smaller").

Hint 3: answer = sum(arr[i] * left[i] * right[i]) % (10^9 + 7).


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(n)
================================================================================
"""

from typing import List


class Solution:
    def sumSubarrayMins(self, arr: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 014_sum_of_subarray_minimums_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ([3, 1, 2, 4], 17),
        ([11, 81, 94, 43, 3], 444),
        ([1], 1),
        ([2, 2], 6),
        ([3, 3, 3], 18),
        ([1, 2, 3], 10),
        ([3, 2, 1], 10),
    ]
    all_ok = True
    for arr, want in cases:
        got = Solution().sumSubarrayMins(list(arr))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  arr={arr}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
