"""
================================================================================
SOLUTION · LeetCode 239 · Sliding Window Maximum                          [Hard]
https://leetcode.com/problems/sliding-window-maximum/
================================================================================

THE CORE IDEA
--------------
Keep a MONOTONIC DEQUE of indices whose values decrease from front to back.
When a new element arrives, pop every smaller-or-equal element off the back:
they can never be a window maximum again, because the new element is at least
as large and will outlive them. Pop the front if it has slid out of the
window. The front is always the maximum of the current window.

Every index is pushed once and popped at most once, so the whole thing is
O(n), no matter how the inner while loops are distributed.


================================================================================
APPROACH 1 · Brute force: max() of every window (priced, used as oracle)
================================================================================
    [max(nums[i:i + k]) for i in range(n - k + 1)]

    Time: O(n * k) — at n = 10^5, k = 5 * 10^4 that's 2.5 * 10^9.   Space: O(k)


================================================================================
APPROACH 2 · Max-heap with lazy deletion
================================================================================
Push (-value, index). Before reading the top, pop while the top's index is
outside the window. Stale entries stay in the heap until they reach the top.

    Time: O(n log n)    Space: O(n) — stale entries can accumulate

A good answer if you don't remember the deque trick, and the "lazy deletion"
idea shows up again in Sliding Window Median (12_heap/012).


================================================================================
APPROACH 3 · Monotonic deque of indices ✅ (the answer)
================================================================================
    dq = deque()                      # indices; nums[dq] strictly decreasing
    out = []
    for i, x in enumerate(nums):
        while dq and nums[dq[-1]] <= x:
            dq.pop()                  # dominated forever
        dq.append(i)
        if dq[0] <= i - k:
            dq.popleft()              # slid out of the window
        if i >= k - 1:
            out.append(nums[dq[0]])

WHY INDICES, NOT VALUES. Eviction asks "did the front leave the window?" That
is a question about POSITION. With values you have to guess by comparing
nums[i - k] to the front value, and duplicates make that guess wrong. The
demo below shows a value-based deque returning a wrong answer on [5, 5, 1].

WHY ONLY ONE popleft PER STEP. Indices in the deque are increasing, and the
window moves by one position per step, so at most one index can fall out per
step.

    Time: O(n) amortized — each index enters and leaves the deque once
    Space: O(k)


================================================================================
STEP BY STEP TRACE · nums = [1, 3, -1, -3, 5, 3, 6, 7], k = 3
================================================================================
    i  x   pop back (<= x)       deque (idx:val)          evict front   output
    -  --  --------------------  -----------------------  ------------  ------
    0   1                        [0:1]
    1   3  pop 0:1               [1:3]
    2  -1                        [1:3, 2:-1]                            3
    3  -3                        [1:3, 2:-1, 3:-3]        none (1 > 0)  3
    4   5  pop 3:-3, 2:-1, 1:3   [4:5]                                  5
    5   3                        [4:5, 5:3]                             5
    6   6  pop 5:3, 4:5          [6:6]                                  6
    7   7  pop 6:6               [7:7]                                  7

    output: [3, 3, 5, 5, 6, 7]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time         Space   Mutates input?
    ---------------------------  -----------  ------  --------------
    max() per window             O(n*k)       O(k)    No
    Heap + lazy deletion         O(n log n)   O(n)    No
    Monotonic deque ✅           O(n)         O(k)    No


================================================================================
EDGE CASES
================================================================================
    k == 1                 Output equals input.
    k == n                 One window; output is [max(nums)].
    Duplicates             Pop with `<=` and store indices; the older equal
                            value is dropped, the newer one survives longer.
    Strictly decreasing    Nothing is ever popped from the back; eviction
                            from the front does all the work. Deque size k.
    Strictly increasing    Deque always size 1.


================================================================================
COMMON MISTAKES
================================================================================
1. Storing VALUES and evicting with `if nums[i - k] == dq[0]`. With duplicates
   the new copy gets evicted in place of the old one. The demo shows
   [5, 5, 1], k = 2 returning [5, 1] instead of [5, 5].

2. Popping with `<` and storing values — keeps duplicates, which fixes (1)
   but only by accident. Use indices and the bug class disappears.

3. Checking eviction BEFORE appending i when k == 1. Order matters less with
   the `dq[0] <= i - k` check, but be sure the current index is in the deque
   before you read the front.

4. Emitting output for i < k - 1 (partial windows).

5. Calling this O(n*k) because of the nested while. Count total pushes and
   pops instead: n each at most.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Sliding window MINIMUM?
A: Same deque with the comparison flipped (pop while nums[back] >= x).

Q: Sliding window MEDIAN?
A: The deque trick doesn't work for medians. Use two heaps with lazy deletion
   (LC 480, 12_heap_priority_queue/012) or a sorted container.

Q: Data is an infinite stream; answer "max of the last k" on demand?
A: This algorithm is already streaming: O(k) memory, O(1) amortized per new
   element, O(1) per query.

Q: Window defined by TIME (last 60 seconds), not count?
A: Evict from the front while its timestamp is older than now - 60. The
   deque holds (timestamp, value) pairs. Same amortized bound.

Q: Why not a balanced BST / SortedList?
A: Also works in O(n log k) and supports deletions of arbitrary values, which
   the median follow-up needs. For max/min alone the deque is simpler and O(n).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 480   Sliding Window Median         — two heaps + lazy deletion
    LC 1438  Longest Continuous Subarray With Absolute Diff <= Limit — two deques
    LC 862   Shortest Subarray with Sum at Least K — monotonic deque on prefix sums
    LC 1696  Jump Game VI                  — deque-optimized DP
    LC 739   Daily Temperatures (06_stack) — monotonic STACK, one-ended cousin
================================================================================
"""

import heapq
import random
import time
from collections import deque
from typing import List


class Solution:
    def maxSlidingWindow(self, nums: List[int], k: int) -> List[int]:
        dq: deque = deque()
        out: List[int] = []
        for i, x in enumerate(nums):
            while dq and nums[dq[-1]] <= x:
                dq.pop()
            dq.append(i)
            if dq[0] <= i - k:
                dq.popleft()
            if i >= k - 1:
                out.append(nums[dq[0]])
        return out


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
def max_window_brute(nums: List[int], k: int) -> List[int]:
    return [max(nums[i:i + k]) for i in range(len(nums) - k + 1)]


def max_window_heap(nums: List[int], k: int) -> List[int]:
    heap: list = []
    out: List[int] = []
    for i, x in enumerate(nums):
        heapq.heappush(heap, (-x, i))
        if i >= k - 1:
            while heap[0][1] <= i - k:
                heapq.heappop(heap)      # lazy deletion of stale maxima
            out.append(-heap[0][0])
    return out


def max_window_values_bug(nums: List[int], k: int) -> List[int]:
    """Mistake 1: deque stores VALUES and pops equals from the back."""
    dq: deque = deque()
    out: List[int] = []
    for i, x in enumerate(nums):
        if i >= k and dq and nums[i - k] == dq[0]:
            dq.popleft()                 # guesses the front left the window
        while dq and dq[-1] <= x:
            dq.pop()
        dq.append(x)
        if i >= k - 1:
            out.append(dq[0])
    return out


# ==============================================================================
# TESTS — run:  python 015_sliding_window_maximum_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: deque vs heap vs brute force ---")
    cases = [
        ([1, 3, -1, -3, 5, 3, 6, 7], 3, [3, 3, 5, 5, 6, 7]),
        ([1], 1, [1]),
        ([1, -1], 1, [1, -1]),
        ([9, 11], 2, [11]),
        ([4, -2], 2, [4]),
        ([5, 5, 1], 2, [5, 5]),
        ([7, 2, 4], 2, [7, 4]),
        ([1, 3, 1, 2, 0, 5], 3, [3, 3, 2, 5]),
    ]
    for nums, k, want in cases:
        results = (sol.maxSlidingWindow(nums, k), max_window_heap(nums, k), max_window_brute(nums, k))
        ok = all(r == want for r in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} k={k}  got={results[0]}  want={want}")

    print("\n--- randomized cross-check (600 inputs, many duplicates) ---")
    rng = random.Random(239)
    bad = 0
    for _ in range(600):
        n = rng.randint(1, 30)
        nums = [rng.randint(-3, 3) for _ in range(n)]
        k = rng.randint(1, n)
        want = max_window_brute(nums, k)
        if sol.maxSlidingWindow(nums, k) != want or max_window_heap(nums, k) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  deque and heap match brute force on 600 inputs")

    print("\n--- mistake 1 LIVE: value-based deque with duplicates ---")
    wrong = max_window_values_bug([5, 5, 1], 2)
    right = sol.maxSlidingWindow([5, 5, 1], 2)
    ok = wrong != right and right == [5, 5]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  [5,5,1], k=2: value deque returns {wrong}, index deque returns {right}")
    print("      at i=2 the value deque holds only the SECOND 5; seeing nums[0] == 5 it")
    print("      evicts that copy, even though it is still inside the window [5, 1]")

    print("\n--- amortized O(n): total deque operations never exceed 2n ---")
    nums = [rng.randint(-10**4, 10**4) for _ in range(50_000)]
    ops = 0
    dq: deque = deque()
    for i, x in enumerate(nums):
        while dq and nums[dq[-1]] <= x:
            dq.pop(); ops += 1
        dq.append(i); ops += 1
        if dq[0] <= i - 100:
            dq.popleft(); ops += 1
    ok = ops <= 2 * len(nums)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  n=50,000: {ops:,} push+pop operations (bound 2n = {2 * len(nums):,})")

    print("\n--- benchmark: n = 100,000, k = 50,000 ---")
    nums = [rng.randint(-10**4, 10**4) for _ in range(100_000)]
    k = 50_000
    for name, fn in (("heap + lazy delete", max_window_heap), ("monotonic deque   ", sol.maxSlidingWindow)):
        t0 = time.perf_counter(); fn(nums, k); dt = time.perf_counter() - t0
        print(f"      {name}  {dt * 1000:8.1f} ms")
    small = nums[:10_000]
    t0 = time.perf_counter(); max_window_brute(small, 5_000); dt = time.perf_counter() - t0
    print(f"      brute max() per window, n=10,000 k=5,000 only: {dt * 1000:8.1f} ms")
    print("      (at the full size brute force does ~2.5 billion comparisons)")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
