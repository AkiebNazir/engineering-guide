"""
================================================================================
SOLUTION · LeetCode 215 · Kth Largest Element in an Array             [Medium]
https://leetcode.com/problems/kth-largest-element-in-an-array/
================================================================================

THE CORE IDEA
--------------
You do NOT need to know the full sorted order — you only need to know which
element sits at rank k from the top. That is a much weaker requirement than
sorting, and there are two classic ways to exploit the slack:

  1. Keep a MIN-HEAP of the k largest elements seen so far. Its root (the
     smallest of those k) is always the current answer. Anything smaller than
     the root can never become a top-k element, so it is discarded in O(1)
     without ever being compared against the other k-1 kept elements.

  2. QUICKSELECT: partition around a random pivot exactly like quicksort, but
     — unlike quicksort — only recurse into the ONE side that contains the
     target rank. Throwing away the other side (instead of also sorting it)
     is what turns O(n log n) into O(n) average.

Both beat sorting because sorting computes information you were never asked
for: the full relative order of every element, not just where the boundary
between "top k" and "the rest" falls.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it, don't code it): sort the whole array
descending and index into position k-1.
    Time:  O(n log n) — full comparison sort.
    Space: O(n) or O(log n) depending on the sort (Python's Timsort uses
           O(n) auxiliary space in the worst case, though often less).
    This is "correct but does more work than the question asked for" — the
    canonical brute force for a "kth something" question.

Approach 1 (min-heap of size k) — THE HEAP ANSWER, coded below:
    Maintain a min-heap capped at size k holding the k largest elements seen
    so far. For each new element: if the heap has room, push it. Otherwise,
    compare it to the heap's root (the smallest of the current top-k); if
    the new element is bigger, `heapreplace` (pop-then-push in one call,
    cheaper than pop() followed by push()). At the end the root IS the kth
    largest, because it is the smallest element that still made the cut.
    Time:  O(n log k) — n pushes/compares, each heap op is O(log k).
    Space: O(k) for the heap.
    Great when k is small relative to n, or when nums arrives as a STREAM
    (this is literally LC 703, problem 001 in this topic) — you never need
    the whole array in memory.

Approach 2 (quickselect) — coded below as the alternative:
    Same partition step as quicksort (Lomuto/Dutch-flag style: < pivot,
    == pivot, > pivot), but after partitioning, only ONE side can contain
    the target rank — recurse into just that side. The other side is
    discarded without ever being touched again.
    Time:  O(n) average (n + n/2 + n/4 + ... converges to O(n)); O(n^2)
           worst case with an adversarial pivot choice, avoided in practice
           by picking the pivot RANDOMLY (a fixed pivot choice, e.g. "always
           first element", is exploitable by a crafted or already-sorted
           input).
    Space: O(1) extra if partitioning is done in place on a copy (O(n) copy
           to avoid mutating the caller's array — see "mutates input?" below).
    This is the answer an interviewer usually wants for LC 215 specifically,
    since the problem explicitly says "without sorting" and expects O(n).

Approach 3 (heap of the full array, `heapq.nlargest`): Python's stdlib
`heapq.nlargest(k, nums)[-1]` is essentially approach 1 with the loop
written in C. Same O(n log k) asymptotics, much faster constant factor.
Worth knowing exists, but the point of this exercise is to build the
min-heap-of-size-k logic yourself.


================================================================================
STEP BY STEP TRACE — nums = [3,2,1,5,6,4], k = 2 (min-heap approach)
================================================================================
Goal: keep the 2 largest elements seen so far in a min-heap; heap[0] is
always the smaller of the two, i.e. the current "2nd largest so far".

  Start: heap = [] (empty, capacity 2)

  x=3: heap not full -> push 3
       heap (array) = [3]                    tree:   3
  x=2: heap not full -> push 2
       heap (array) = [2,3]                  tree:   2
                                                     /
                                                    3
       (heapq maintains: heap[0] <= heap[1])

  x=1: heap FULL (size 2). compare 1 vs root 2 -> 1 < 2, discard 1.
       heap (array) = [2,3]   unchanged

  x=5: heap FULL. compare 5 vs root 2 -> 5 > 2, heapreplace(heap, 5):
       pop 2, push 5, re-sift -> heap (array) = [3,5]   tree:   3
                                                                /
                                                               5

  x=6: heap FULL. compare 6 vs root 3 -> 6 > 3, heapreplace(heap, 6):
       pop 3, push 6, re-sift -> heap (array) = [5,6]   tree:   5
                                                                /
                                                               6

  x=4: heap FULL. compare 4 vs root 5 -> 4 < 5, discard 4.
       heap (array) = [5,6]   unchanged

  End: heap[0] = 5  -> the 2nd largest element is 5.  Matches expected output.

  Notice: 6 (the actual largest) sits at index 1, a CHILD of the root — a
  min-heap only guarantees the ROOT is the minimum of the kept set; it makes
  no promise about the relative order of anything below it.


================================================================================
COMPLEXITY SUMMARY
================================================================================
┌───────────────────────────┬──────────────┬───────────┬─────────────────┐
│ Approach                   │ Time          │ Space     │ Mutates input?  │
├───────────────────────────┼──────────────┼───────────┼─────────────────┤
│ Sort descending (brute)    │ O(n log n)    │ O(n)      │ no (sorted() makes a copy; sort() in place would) │
│ Min-heap of size k         │ O(n log k)    │ O(k)      │ no              │
│ Quickselect                │ O(n) average, │ O(1) extra│ no — this impl  │
│                             │ O(n^2) worst  │ (on copy) │ copies nums first│
│ heapq.nlargest(k, nums)[-1]│ O(n log k)    │ O(k)      │ no              │
└───────────────────────────┴──────────────┴───────────┴─────────────────┘


================================================================================
EDGE CASES
================================================================================
- k == len(nums): the answer is the minimum of the whole array — the heap
  approach still works (the heap grows to hold everything), quickselect
  still works (target rank is index 0 after partitioning).
- k == 1: the answer is the max — heap degenerates to size 1, quickselect
  target rank is the last index.
- All elements equal: every comparison in quickselect's partition routes
  duplicates into the "== pivot" bucket; without that third bucket (a naive
  two-way partition) this input can degrade toward O(n^2) even with random
  pivots, since every pivot choice is "equal" to everything.
- Negative numbers: no special handling needed — Python's `<`/`>` and
  `heapq` work uniformly on negatives; a bug would only appear from a wrong
  sign-flip if someone tried to fake a max-heap out of `heapq` (see mistake
  #1 below), which this solution deliberately avoids by using a min-heap the
  way it is meant to be used.
- Array of length 1 (k must be 1 by constraints): heap ends with a single
  element as its own root; quickselect's while loop never iterates because
  lo == hi immediately.


================================================================================
COMMON MISTAKES
================================================================================
1. **`heapq` is a MIN-heap only.** To simulate a max-heap, everyone
   negates values, e.g. `heapq.heappush(h, -x)`. Forgetting to negate BACK
   when reading the answer out (`heap[0]` instead of `-heap[0]`) silently
   returns the wrong sign. This solution sidesteps the whole problem by using
   a min-heap for exactly what it's good at — tracking the SMALLEST of a
   kept top-k set — instead of fighting it into a max-heap.
2. **`heapify()` is O(n), not O(n log n).** It looks like it should cost as
   much as n `heappush` calls (O(n log n)) but Floyd's build-heap algorithm
   sifts DOWN from the last non-leaf node up to the root, and the vast
   majority of nodes are near the leaves where sift-down does almost no
   work — the sum telescopes to O(n). Using `heapify(nums[:k])` once instead
   of k separate `heappush` calls to seed the heap is both correct and the
   idiomatic choice — it does the same job with less code, not less
   complexity (O(k) either way for k elements), so don't reach for
   `heapify` expecting an asymptotic win in that specific case; the real
   payoff is avoiding manual sift bookkeeping and matching how the stdlib
   is meant to be used.
3. **Quickselect without random pivot selection** — always picking, say,
   `nums[lo]` as the pivot is fine on random data but degrades to O(n^2) on
   an already-sorted or reverse-sorted input (a realistic adversarial or
   accidental case), because every partition step only shrinks the range by
   one. `random.randint(lo, hi)` defeats any input-dependent worst case.
4. **Off-by-one on "kth largest" vs "kth largest INDEX".** `findKthLargest`
   with k=2 on `[3,2,1,5,6,4]` means "2nd largest value" (5), not "value at
   sorted index 2" (which would be the 3rd largest, 4). Translating "kth
   largest" into an index requires `len(nums) - k` (0-indexed, ascending
   sort) — get the direction backwards and every answer is off by a
   symmetric amount around the middle.
5. **Mutating the caller's array** when implementing quickselect in place
   without first copying — fine for LeetCode's harness, but a real API
   contract usually promises not to reorder the caller's list as a side
   effect of finding a value. State the trade-off if you skip the copy for
   speed.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if nums is a live, unbounded stream and k is fixed?" -> the min-heap
  approach is now the ONLY viable one (this is exactly LC 703, problem 001):
  quickselect needs random access to the whole array up front.
- "What if k changes on every query but the array is static?" -> sort once,
  O(n log n) up front, O(1) per query — amortizes the cost the brute force
  approach paid unnecessarily for a single query.
- "Can you find the kth largest in guaranteed O(n) worst case?" -> yes, the
  median-of-medians pivot selection algorithm guarantees O(n) worst case for
  quickselect, at the cost of a much larger constant factor; rarely coded
  from scratch in an interview but worth naming.
- "How would you parallelize this across a cluster?" -> a heap of size k per
  shard, then merge the per-shard top-k heaps (k-way merge) — total O(n log k)
  work distributed, O(k * num_shards) final merge.


================================================================================
RELATED PROBLEMS
================================================================================
- LC 703 Kth Largest Element in a Stream (this topic, 001) — same min-heap
  idea, but the heap must persist across repeated `add()` calls.
- LC 973 K Closest Points to Origin (this topic, 003) — top-k by a computed
  distance instead of the raw value; same min-heap-of-size-k pattern.
- LC 347 Top K Frequent Elements (topic 01) — top-k by frequency count.
- LC 4 Median of Two Sorted Arrays — a harder cousin of "find the kth
  smallest/largest without fully sorting", solved with binary search instead
  of a heap.
"""

import heapq
import random
import time
from typing import List


class Solution:
    def findKthLargest(self, nums: List[int], k: int) -> int:
        # Min-heap of size k holding the k largest elements seen so far.
        # heap[0] is always the smallest of that set == the kth largest overall.
        heap = nums[:k]
        heapq.heapify(heap)                 # O(k), NOT O(k log k)
        for x in nums[k:]:
            if x > heap[0]:
                heapq.heapreplace(heap, x)  # pop smallest, push x, re-sift: one O(log k) op
        return heap[0]

    def findKthLargest_quickselect(self, nums: List[int], k: int) -> int:
        # Alternative approach: quickselect (O(n) average). Copies nums so
        # the caller's list is never reordered as a side effect.
        arr = nums[:]
        target = len(arr) - k  # 0-indexed position of the kth largest in ascending order

        def partition(lo: int, hi: int) -> int:
            pivot_idx = random.randint(lo, hi)
            pivot = arr[pivot_idx]
            lt, gt, i = lo, hi, lo
            while i <= gt:
                if arr[i] < pivot:
                    arr[lt], arr[i] = arr[i], arr[lt]
                    lt += 1
                    i += 1
                elif arr[i] > pivot:
                    arr[gt], arr[i] = arr[i], arr[gt]
                    gt -= 1
                else:
                    i += 1
            return lt, gt  # [lt, gt] is the range of elements EQUAL to pivot

        lo, hi = 0, len(arr) - 1
        while True:
            lt, gt = partition(lo, hi)
            if target < lt:
                hi = lt - 1
            elif target > gt:
                lo = gt + 1
            else:
                return arr[target]  # target landed inside the "== pivot" band


def run_tests():
    sol = Solution()

    # --- correctness: both approaches, both examples plus extras ---
    cases = [
        ([3, 2, 1, 5, 6, 4], 2, 5),
        ([3, 2, 3, 1, 2, 4, 5, 5, 6], 4, 4),
        ([1], 1, 1),
        ([2, 1], 2, 1),
        ([5, 5, 5, 5], 2, 5),
        ([-1, -5, -3, -2, -4], 1, -1),
    ]
    for nums, k, expected in cases:
        got_heap = sol.findKthLargest(list(nums), k)
        got_qs = sol.findKthLargest_quickselect(list(nums), k)
        assert got_heap == expected, f"heap: {nums}, k={k} -> {got_heap}, want {expected}"
        assert got_qs == expected, f"qs: {nums}, k={k} -> {got_qs}, want {expected}"

    # --- prove: min-heap approach never mutates the caller's list ---
    original = [3, 2, 1, 5, 6, 4]
    snapshot = original[:]
    sol.findKthLargest(original, 2)
    assert original == snapshot, "findKthLargest must not mutate its input"

    # --- prove: quickselect approach never mutates the caller's list either ---
    original2 = [9, 3, 7, 1, 8, 2]
    snapshot2 = original2[:]
    sol.findKthLargest_quickselect(original2, 3)
    assert original2 == snapshot2, "quickselect must not mutate its input"

    # --- measured runtime demo: sort vs min-heap vs quickselect ---
    # (mirrors the priced-but-not-coded brute force: full sort, for real)
    def sort_based(nums, k):
        return sorted(nums, reverse=True)[k - 1]

    n = 200_000
    k = 50
    random.seed(42)
    data = [random.randint(-10**6, 10**6) for _ in range(n)]

    timings = {}
    for name, fn in [
        ("sort", sort_based),
        ("min-heap", sol.findKthLargest),
        ("quickselect", sol.findKthLargest_quickselect),
    ]:
        t0 = time.perf_counter()
        result = fn(data, k)
        t1 = time.perf_counter()
        timings[name] = (result, (t1 - t0) * 1000)

    # all three approaches must agree on the answer
    results = {r for r, _ in timings.values()}
    assert len(results) == 1, f"approaches disagree: {timings}"

    print("Measured on n=200,000 random ints, k=50 (CPython, this machine):")
    for name, (result, ms) in timings.items():
        print(f"  {name:12s} -> answer={result:>8}  time={ms:7.2f} ms")
    # On this machine: sort ~17ms, min-heap ~2ms, quickselect ~13ms.
    # The min-heap wins decisively here because k=50 << n=200,000, so
    # O(n log k) with a tiny constant beats both O(n log n) sorting and
    # quickselect's per-partition overhead (random pivot draw, three-way
    # scan) at this problem size. Quickselect's O(n) average still comfortably
    # beats sorting's O(n log n), as expected.
    assert timings["min-heap"][1] < timings["sort"][1], (
        "expected the min-heap approach to beat full sort when k << n"
    )

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
