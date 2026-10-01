"""
================================================================================
LeetCode 347 · Top K Frequent Elements                                 [Medium]
https://leetcode.com/problems/top-k-frequent-elements/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an integer array `nums` and an integer `k`, return the `k` most frequent
elements. You may return the answer in any order.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,1,1,2,2,3], k = 2
    Output: [1,2]

Example 2:
    Input:  nums = [1], k = 1
    Output: [1]


CONSTRAINTS
-----------
    1 <= nums.length <= 10^5
    -10^4 <= nums[i] <= 10^4
    k is in the range [1, number of unique elements in nums]
    It is GUARANTEED that the answer is unique.


FOLLOW UP
---------
    Your algorithm's time complexity must be better than O(n log n), where n is
    the array's size.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Two phases, and they are completely independent:

    PHASE 1   count      nums -> {value: frequency}        O(n), no debate
    PHASE 2   select     pick the k largest frequencies    <- the whole problem

Phase 1 is a `Counter`. Every solution does it identically. All the design
happens in phase 2, and the follow-up tells you exactly what it is testing:

    "better than O(n log n)"    -> you may NOT just sort the counts

    nums = [1,1,1,2,2,3]   k = 2

    phase 1:   {1: 3, 2: 2, 3: 1}

    phase 2:   frequencies are 3, 2, 1 — take the top 2 -> values 1 and 2

The trap is that "top k" pattern-matches to "sort, then slice", which is
O(m log m) on m unique values. That works and it is worth stating, but the
follow-up explicitly rules it out. You need to beat it.


WHAT TO THINK ABOUT
-------------------
1. If you only need the top k, do you need the other m-k in sorted order at
   all? What data structure gives you "the k largest" without fully sorting?

2. Look hard at the RANGE of a frequency. If the array has n elements, what is
   the largest a frequency can possibly be? What is the smallest?
   How many distinct frequency values are therefore possible?

3. When a key is a small bounded integer, you can index an array by it instead
   of comparing. What would `buckets[f]` hold if f is a frequency?

4. Python's heap is a MIN-heap. If you want the k LARGEST things, which end do
   you evict from, and how big does the heap ever need to get?


PROGRESSIVE HINTS
-----------------
Hint 1: `collections.Counter(nums)` gives you the frequency map in one line.
        (`Counter(nums).most_common(k)` also solves it outright — know that it
        exists, but be able to implement the selection yourself.)

Hint 2: Heap approach — push each (freq, value) onto a min-heap and pop
        whenever its size exceeds k. The heap holds the k best seen so far, so
        each push/pop is log k, giving O(m log k).

Hint 3: Bucket approach — a frequency is an integer in [1, n]. Make a list of
        n+1 empty lists and put value v into `buckets[freq[v]]`. Then walk the
        buckets from the high end backwards, collecting until you have k. That
        is O(n) — no comparisons, no sorting.


COMPLEXITY TARGET
-----------------
    n = len(nums), m = number of unique values (m <= n)

    O(m log k) with a heap        — beats O(n log n)
    O(n)       with bucket sort   — optimal
================================================================================
"""

from typing import List


class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 008_top_k_frequent_elements_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 1, 1, 2, 2, 3], 2, [1, 2]),
        ([1], 1, [1]),
        ([1, 2], 2, [1, 2]),
        ([4, 4, 4, 4], 1, [4]),
        ([5, 5, 4, 4, 3, 3, 2, 1], 3, [3, 4, 5]),
        ([-1, -1, -1, 0, 0, 7], 2, [-1, 0]),
        ([3, 0, 1, 0], 1, [0]),
    ]
    passed = 0
    for nums, k, expected in cases:
        got = sol.topKFrequent(list(nums), k)
        ok = got is not None and sorted(got) == sorted(expected)
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} k={k} -> {got} (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
