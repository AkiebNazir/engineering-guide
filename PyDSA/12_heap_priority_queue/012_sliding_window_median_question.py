"""
================================================================================
LeetCode 480 · Sliding Window Median                                      [Hard]
https://leetcode.com/problems/sliding-window-median/
Topic: 12 · Heap / Priority Queue
================================================================================

PROBLEM
-------
The median is the middle value in an ordered integer list. If the size of the
list is even, there is no single middle value, and the median is the mean of
the two middle values.

You are given an integer array `nums` and an integer k. A sliding window of
size k moves from the very left of the array to the very right, one position
at a time. Return the median of each window. Answers within 10^-5 of the
actual value are accepted.


EXAMPLES
--------
Example 1:
    Input:  nums = [1, 3, -1, -3, 5, 3, 6, 7], k = 3
    Output: [1.0, -1.0, -1.0, 3.0, 5.0, 6.0]

    Window                 Median
    [1  3  -1] -3  5 ...      1
     1 [3  -1  -3] 5 ...     -1
     1  3 [-1  -3  5] ...    -1
     ...

Example 2:
    Input:  nums = [1, 2, 3, 4, 2, 3, 1, 4, 2], k = 3
    Output: [2.0, 3.0, 3.0, 3.0, 2.0, 3.0, 2.0]


CONSTRAINTS
-----------
    1 <= k <= nums.length <= 10^5
    -2^31 <= nums[i] <= 2^31 - 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Find Median from Data Stream (009) keeps two heaps: a max-heap `small` for the
lower half and a min-heap `large` for the upper half. The median lives at the
tops. That handles INSERTS.

A sliding window also needs DELETES, and a heap can't delete an arbitrary
element efficiently. The standard trick is LAZY DELETION:

    - Don't remove the element. Record it in a `delayed` counter.
    - Keep SIZE counters that pretend it's already gone.
    - Only physically pop it when it surfaces at the top of its heap.

The median only ever reads the tops, so stale elements buried inside a heap
are harmless.


WHAT TO THINK ABOUT
--------------------
1. When you "delete" x, which heap is it in? (Compare to the top of small.)

2. After a deletion or insertion, the halves may be unbalanced BY THE SIZE
   COUNTERS. When you move a top element across, what must you do to the
   heap you took it from?

3. For an even k, (a + b) / 2 on two 32-bit values can overflow in Java/C++.
   Python ints don't, but note it.


PROGRESSIVE HINTS
------------------
Hint 1: Invariants: every element in small <= every element in large, and
        small_size == large_size or small_size == large_size + 1. The top of
        each heap is never a delayed element.

Hint 2: prune(heap): while its top is in delayed, pop it and decrement delayed.

Hint 3: After every insert/erase: rebalance by moving one top across, then
        prune the heap you moved from. After erase, prune whichever heap had
        the erased value on top.


COMPLEXITY TARGET
------------------
    Time:  O(n log n)
    Space: O(n)
================================================================================
"""

from typing import List


class Solution:
    def medianSlidingWindow(self, nums: List[int], k: int) -> List[float]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 012_sliding_window_median_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ([1, 3, -1, -3, 5, 3, 6, 7], 3, [1.0, -1.0, -1.0, 3.0, 5.0, 6.0]),
        ([1, 2, 3, 4, 2, 3, 1, 4, 2], 3, [2.0, 3.0, 3.0, 3.0, 2.0, 3.0, 2.0]),
        ([1, 4, 2, 3], 4, [2.5]),
        ([5], 1, [5.0]),
        ([1, 2], 2, [1.5]),
        ([2147483647, 2147483647], 2, [2147483647.0]),
        ([1, 1, 1, 1], 2, [1.0, 1.0, 1.0]),
    ]
    all_ok = True
    for nums, k, want in cases:
        got = Solution().medianSlidingWindow(list(nums), k)
        ok = got is not None and len(got) == len(want) and all(abs(a - b) < 1e-5 for a, b in zip(got, want))
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} k={k}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
