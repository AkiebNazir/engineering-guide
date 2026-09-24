"""
================================================================================
SOLUTION · LeetCode 480 · Sliding Window Median                           [Hard]
https://leetcode.com/problems/sliding-window-median/
================================================================================

THE CORE IDEA
--------------
Two heaps (max-heap `small` for the lower half, min-heap `large` for the upper
half) plus LAZY DELETION. Leaving elements are recorded in a `delayed` counter
instead of being removed, and explicit size counters track the LOGICAL sizes.
A delayed element is physically popped only when it reaches the top of its
heap, which is the only place the median ever looks. Every element is pushed
once and popped at most once, so the total cost stays O(n log n).


================================================================================
APPROACH 1 · Sort every window (priced, used as oracle)
================================================================================
    sorted(nums[i:i+k]) and read the middle.

    Time: O(n * k log k)    Space: O(k)


================================================================================
APPROACH 2 · Sorted list + bisect (insort / delete by binary search)
================================================================================
Keep the window in a sorted Python list. Each step: bisect to find and delete
the outgoing value, bisect.insort the incoming value, read the middle.

    Time: O(n * k) worst case — list insert/delete shift up to k pointers
    Space: O(k)

On paper this is worse than the heaps. In CPython the shift is a single C
memmove, which is very fast, so the benchmark below measures both honestly.
On this machine at n = 100,000: with k = 100 the sorted list was about 4x
FASTER than the heaps; with k = 10,000 the heaps won by about 3x, and with
k = 50,000 by about 12x. Small windows favor the simple list; the asymptotic
win only shows up once k is large.
A balanced BST or `sortedcontainers.SortedList` gives O(n log k) for real.


================================================================================
APPROACH 3 · Dual heap + lazy deletion ✅ (the answer)
================================================================================
State:
    small  max-heap (stored negated)     small_size  logical size
    large  min-heap                      large_size  logical size
    delayed Counter of values removed but not yet popped

Invariants:
    (a) every live value in small <= every live value in large
    (b) small_size == large_size  or  small_size == large_size + 1
    (c) the TOP of each heap is live (not delayed)

    prune(heap):   while heap top is delayed: pop it, delayed[top] -= 1
    balance():     if small_size > large_size + 1: move small top -> large, prune(small)
                   if small_size < large_size:     move large top -> small, prune(large)
    insert(x):     x <= top(small) ? push small : push large; balance()
    erase(x):      delayed[x] += 1
                   if x <= top(small): small_size -= 1; if x == top(small): prune(small)
                   else:               large_size -= 1; if x == top(large): prune(large)
                   balance()
    median:        k odd -> top(small); k even -> (top(small) + top(large)) / 2

WHY `x <= top(small)` IDENTIFIES THE RIGHT HEAP. By invariant (a) every live
value <= top(small) is in small (ties may sit in either heap, but a tie has the
same VALUE, and lazy deletion only cares about values). By (c) top(small) is
live, so the comparison is meaningful.

    Time: O(n log n) — each value pushed once, popped at most once
    Space: O(n) — delayed values can linger inside the heaps


================================================================================
STEP BY STEP TRACE · nums = [1, 3, -1, -3, 5], k = 3
================================================================================
    step         small (max)   large (min)   delayed   sizes (s,l)  median
    -----------  ------------  ------------  --------  -----------  ------
    insert 1     [1]           []            {}        (1,0)
    insert 3     [1]           [3]           {}        (1,1)
    insert -1    [1,-1]        [3]           {}        (2,1)          1
    insert -3    [1,-1,-3]     [3]           {}        (3,1)
      balance -> move 1 to large              (2,2)
                 [-1,-3]       [1,3]
    erase 1      1 > top(small)=-1 -> large; top(large)==1 -> prune pops it
                 [-1,-3]       [3]           {}        (2,1)         -1
    insert 5     [-1,-3]       [3,5]         {}        (2,2)
    erase 3      3 > -1 -> large side, top(large)==3 -> pop
                 [-1,-3]       [5]           {}        (2,1)         -1


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time           Space   Mutates input?
    ------------------------------  -------------  ------  --------------
    Sort every window               O(n k log k)   O(k)    No
    Sorted list + bisect            O(n k) (fast C shifts)  O(k)  No
    Dual heap + lazy deletion ✅    O(n log n)     O(n)    No


================================================================================
EDGE CASES
================================================================================
    k == 1                 Median is the element itself.
    k == n                 One window.
    Duplicates              Lazy deletion counts by VALUE; any copy works.
    Extreme values          (2^31-1 + 2^31-1) / 2 — fine in Python, overflows
                            int32 elsewhere: use a / 2.0 + b / 2.0 or 64-bit.
    Even k                 Float result, e.g. 2.5.


================================================================================
COMMON MISTAKES
================================================================================
1. Integer division for even k: (a + b) // 2 turns 1.5 into 1. Demo below.

2. Using len(heap) instead of the logical size counters. Stale elements
   inflate len() and the halves drift out of balance. Demo below.

3. Forgetting to prune after moving a top across. The next top might be a
   delayed value, and then the median reads a value that already left.

4. Removing with list.remove + heapify: correct but O(k) per step.

5. Deciding which heap holds x by checking `x in small` (O(k) scan) instead
   of comparing to the top.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Arbitrary percentile (p90), not the median?
A: Keep the same two heaps but balance to sizes ceil(0.9k) and floor(0.1k).

Q: Stream with deletions by id, not sliding?
A: Lazy deletion works unchanged: delay by id or value, prune when surfaced.

Q: Approximate median over a huge stream, bounded memory?
A: Quantile sketches (t-digest, KLL, GK) give epsilon-accurate quantiles in
   sublinear memory. See the probabilistic data structures in SystemDesign.

Q: Sliding Window MAX instead?
A: Monotonic deque in O(n) (03_sliding_window/015).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 295   Find Median from Data Stream (009) — two heaps, inserts only
    LC 239   Sliding Window Maximum (03/015)    — deque; also has a lazy heap version
    LC 2102  Sequentially Ordinal Rank Tracker  — two heaps, moving boundary
    LC 1825  Finding MK Average                 — three multisets, same balancing idea
================================================================================
"""

import bisect
import heapq
import random
import time
from collections import Counter
from typing import List


class DualHeap:
    def __init__(self, k: int):
        self.small: List[int] = []    # max-heap, negated
        self.large: List[int] = []    # min-heap
        self.delayed: Counter = Counter()
        self.small_size = 0
        self.large_size = 0
        self.k = k

    def _prune(self, heap: List[int], sign: int) -> None:
        while heap:
            top = sign * heap[0]
            if self.delayed[top]:
                self.delayed[top] -= 1
                heapq.heappop(heap)
            else:
                break

    def _balance(self) -> None:
        if self.small_size > self.large_size + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
            self.small_size -= 1
            self.large_size += 1
            self._prune(self.small, -1)
        elif self.small_size < self.large_size:
            heapq.heappush(self.small, -heapq.heappop(self.large))
            self.small_size += 1
            self.large_size -= 1
            self._prune(self.large, 1)

    def insert(self, x: int) -> None:
        if not self.small or x <= -self.small[0]:
            heapq.heappush(self.small, -x)
            self.small_size += 1
        else:
            heapq.heappush(self.large, x)
            self.large_size += 1
        self._balance()

    def erase(self, x: int) -> None:
        self.delayed[x] += 1
        if x <= -self.small[0]:
            self.small_size -= 1
            if x == -self.small[0]:
                self._prune(self.small, -1)
        else:
            self.large_size -= 1
            if x == self.large[0]:
                self._prune(self.large, 1)
        self._balance()

    def median(self) -> float:
        if self.k & 1:
            return float(-self.small[0])
        return (-self.small[0] + self.large[0]) / 2


class Solution:
    def medianSlidingWindow(self, nums: List[int], k: int) -> List[float]:
        dh = DualHeap(k)
        for x in nums[:k]:
            dh.insert(x)
        out = [dh.median()]
        for i in range(k, len(nums)):
            dh.insert(nums[i])
            dh.erase(nums[i - k])
            out.append(dh.median())
        return out


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def median_sort_each(nums: List[int], k: int) -> List[float]:
    out = []
    for i in range(len(nums) - k + 1):
        w = sorted(nums[i:i + k])
        out.append(float(w[k // 2]) if k & 1 else (w[k // 2 - 1] + w[k // 2]) / 2)
    return out


def median_bisect(nums: List[int], k: int) -> List[float]:
    window = sorted(nums[:k])
    out = []
    for i in range(k, len(nums) + 1):
        out.append(float(window[k // 2]) if k & 1 else (window[k // 2 - 1] + window[k // 2]) / 2)
        if i == len(nums):
            break
        del window[bisect.bisect_left(window, nums[i - k])]
        bisect.insort(window, nums[i])
    return out


def median_int_div_bug(nums: List[int], k: int) -> List[float]:
    """Mistake 1: floor-divides the two middle values."""
    out = []
    for i in range(len(nums) - k + 1):
        w = sorted(nums[i:i + k])
        out.append(w[k // 2] if k & 1 else (w[k // 2 - 1] + w[k // 2]) // 2)   # BUG
    return out


class DualHeapLenBug(DualHeap):
    """Mistake 2: balances on len(heap), which still counts delayed elements."""

    def _balance(self) -> None:
        if len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
            self._prune(self.small, -1)
        elif len(self.small) < len(self.large):
            heapq.heappush(self.small, -heapq.heappop(self.large))
            self._prune(self.large, 1)


def median_len_bug(nums: List[int], k: int) -> List[float]:
    dh = DualHeapLenBug(k)
    for x in nums[:k]:
        dh.insert(x)
    out = [dh.median()]
    for i in range(k, len(nums)):
        dh.insert(nums[i])
        dh.erase(nums[i - k])
        out.append(dh.median())
    return out


def close(a: List[float], b: List[float]) -> bool:
    return len(a) == len(b) and all(abs(x - y) < 1e-5 for x, y in zip(a, b))


# ==============================================================================
# TESTS — run:  python 012_sliding_window_median_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: dual heap vs bisect vs sort-each ---")
    cases = [
        ([1, 3, -1, -3, 5, 3, 6, 7], 3, [1.0, -1.0, -1.0, 3.0, 5.0, 6.0]),
        ([1, 2, 3, 4, 2, 3, 1, 4, 2], 3, [2.0, 3.0, 3.0, 3.0, 2.0, 3.0, 2.0]),
        ([1, 4, 2, 3], 4, [2.5]),
        ([5], 1, [5.0]),
        ([1, 2], 2, [1.5]),
        ([2147483647, 2147483647], 2, [2147483647.0]),
        ([1, 1, 1, 1], 2, [1.0, 1.0, 1.0]),
    ]
    for nums, k, want in cases:
        a, b, c = sol.medianSlidingWindow(nums, k), median_bisect(nums, k), median_sort_each(nums, k)
        ok = close(a, want) and close(b, want) and close(c, want)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} k={k}  got={a}")

    print("\n--- randomized cross-check (1000 inputs, lots of duplicates) ---")
    rng = random.Random(480)
    bad = 0
    for _ in range(1000):
        n = rng.randint(1, 25)
        nums = [rng.randint(-3, 3) for _ in range(n)]
        k = rng.randint(1, n)
        want = median_sort_each(nums, k)
        if not close(sol.medianSlidingWindow(nums, k), want) or not close(median_bisect(nums, k), want):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  1000 random inputs agree with sorting every window")

    print("\n--- mistake 1 LIVE: integer division for even k ---")
    wrong = median_int_div_bug([1, 2], 2)
    ok = wrong == [1] and sol.medianSlidingWindow([1, 2], 2) == [1.5]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  [1, 2], k=2: // gives {wrong}, correct [1.5]")

    print("\n--- mistake 2 LIVE: balancing by len(heap) instead of logical sizes ---")
    failures = 0
    example = None
    for _ in range(1000):
        n = rng.randint(2, 25)
        nums = [rng.randint(-3, 3) for _ in range(n)]
        k = rng.randint(1, n)
        try:
            got = median_len_bug(nums, k)
            wrong_here = not close(got, median_sort_each(nums, k))
        except IndexError:
            wrong_here = True
            got = "IndexError"
        if wrong_here:
            failures += 1
            if example is None:
                example = (nums, k, got, median_sort_each(nums, k))
    ok = failures > 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  len()-balanced version wrong on {failures} of 1000 random inputs")
    if example:
        print(f"      e.g. nums={example[0]} k={example[1]}\n           got  {example[2]}\n           want {example[3]}")

    print("\n--- benchmark: n = 100,000 ---")
    nums = [rng.randint(-2**31, 2**31 - 1) for _ in range(100_000)]
    for k in (100, 10_000, 50_000):
        t0 = time.perf_counter(); a = sol.medianSlidingWindow(nums, k); th = time.perf_counter() - t0
        t0 = time.perf_counter(); b = median_bisect(nums, k); tb = time.perf_counter() - t0
        all_ok &= close(a, b)
        print(f"      k={k:>6}  dual heap {th * 1000:7.1f} ms   sorted list + bisect {tb * 1000:7.1f} ms")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
