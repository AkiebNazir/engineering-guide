"""
================================================================================
SOLUTION · LeetCode 703 · Kth Largest Element in a Stream               [Easy]
https://leetcode.com/problems/kth-largest-element-in-a-stream/
================================================================================

THE CORE IDEA
--------------
We never need to know the full sorted order of the stream — only "what is
currently the kth largest?" after every insert. Keep a **min-heap of size
exactly k** holding the k largest elements seen so far. Its root (the
smallest of those k) IS the answer to "kth largest" by definition: exactly
k-1 elements in the heap are >= it, and everything discarded (never even
entered the heap) was smaller than the current kth largest at the time it
arrived, so it can never affect the answer. See _TOPIC_GUIDE.md §3 for the
general top-k-heap trade against sorting.

================================================================================
APPROACH 0 · Re-sort on every add (baseline, don't code as the answer)
================================================================================
Keep the whole stream in a list. On every `add`, append and re-sort (or use
`bisect.insort` to keep it sorted incrementally), then read off index
`-k`. `bisect.insort` on a list is O(n) per insert (shifting elements), and
a full re-sort is O(n log n) per insert. Either way this is O(n) or worse
PER CALL, growing with the stream — for m calls on a stream that grows to
size n, that's O(n*m) or O(n log n * m) total. Correct, trivial to write,
never the answer once the stream is long-lived.

================================================================================
APPROACH 1 · Min-heap of size k ✅ (the answer)
================================================================================
    import heapq

    class KthLargest:
        def __init__(self, k, nums):
            self.k = k
            self.heap = nums[:]
            heapq.heapify(self.heap)          # O(n), see guide §1.5
            while len(self.heap) > k:
                heapq.heappop(self.heap)      # trim to size k, O((n-k) log n)

        def add(self, val):
            if len(self.heap) < self.k:
                heapq.heappush(self.heap, val)
            elif val > self.heap[0]:
                heapq.heapreplace(self.heap, val)   # pop min, push val: one sift
            return self.heap[0]

`heapreplace` (guide §2.2) does the pop-then-push in a single O(log k) sift
instead of two separate O(log k) operations — and critically, since we
already checked `val > heap[0]` before calling it, we know the new heap
still has exactly k elements, so `heapreplace` never needs to grow the
heap.

    Time:  __init__ O(n) heapify + O((n-k) log n) trim
           add: O(log k) amortized (O(1) when val doesn't beat the top-k)
    Space: O(k) — the heap never exceeds k elements (init trims immediately)

================================================================================
APPROACH 2 · Track only k, ignore anything below the current floor
================================================================================
Same as Approach 1; the "elif val > self.heap[0]" branch already IS this
optimization — most `add` calls in a real stream will fail that check and
cost a single comparison, not a full sift. Nothing further to add; it is
not a separate algorithm, just worth calling out that Approach 1 already
captures the fast path.

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
KthLargest(3, [4, 5, 8, 2])

  heapify([4,5,8,2]) -> min-heap array (one valid layout): [2, 4, 8, 5]
        2
       / \
      4   8
     /
    5
  len=4 > k=3, pop min (2) once:
        4
       / \
      5   8
  heap array = [4, 5, 8], root = 4   (this IS the 3rd-largest of {2,4,5,8})

  add(3): len(heap)==3==k, 3 > heap[0]=4? No -> discard. return heap[0] = 4
  add(5): 5 > 4? Yes -> heapreplace: pop 4, push 5.
          array before: [4,5,8] ; after sift: [5,8,5]  (root=5)
          return 5
  add(10): 10 > 5? Yes -> heapreplace: pop 5, push 10.
          array: [5,8,10] region reorganizes to root=5 still (8 and 10 both >=5)
          return 5
  add(9): 9 > 5? Yes -> heapreplace: pop 5, push 9.
          heap now holds {8,9,10}, root = 8
          return 8
  add(4): 4 > 8? No -> discard. return heap[0] = 8

Matches the example output: [4, 5, 5, 8, 8].

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                         | init            | add (amortized) | Space | Mutates input `nums`? |
|-----------------------------------|-----------------|------------------|-------|------------------------|
| 0 · re-sort / bisect.insort every call | O(n log n) or O(n) | O(n)        | O(n)  | No (copies)            |
| 1 · size-k min-heap ✅            | O(n) heapify + O((n-k) log n) trim | O(log k), O(1) fast path | O(k) | No — `nums[:]` copies before heapify |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- `nums` shorter than k initially: heap just holds fewer than k elements
  until enough `add` calls arrive; the `len(self.heap) < self.k` branch in
  `add` covers this (LeetCode guarantees a query never happens before k
  elements exist, but the code doesn't crash even if it did — `heap[0]`
  would just be the current min of fewer-than-k elements).
- `nums = []`: heap starts empty, first k `add` calls all take the "push"
  branch, `heap[0]` should not be read before k elements exist (guaranteed
  by constraints).
- Duplicate values: heap comparisons work fine on ties (min-heap doesn't
  need strict ordering); "kth largest" explicitly means kth in sorted
  order counting duplicates, not kth distinct — no special handling needed
  since we never deduplicate.
- k == 1: heap of size 1 — `add` degenerates to "track the running max",
  still correct via the same branch logic.
- Negative values / val below current floor: `val > self.heap[0]` correctly
  rejects them without disturbing the heap — this is the O(1) fast path
  that keeps `add` cheap on average for a realistic stream.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Using a max-heap of ALL elements instead of a min-heap of just the top
   k — works, but costs O(n) space and O(log n) per add instead of O(k)
   space and O(log k) per add; defeats the point of bounding the heap.
2. Forgetting `heapq` is min-heap only (guide §2.1) and trying to negate
   values here — unnecessary, since this problem wants the SMALLEST of the
   top-k as the answer (the root of a min-heap), which is exactly what a
   plain min-heap already gives without any sign-flipping.
3. Calling `heapq.heappush` unconditionally on every `add` without first
   trimming back down to size k — silently turns this into an unbounded
   max-heap-of-everything, still "correct" on tiny test inputs but wrong
   complexity, and will return the wrong answer if you then read `heap[0]`
   expecting it to be the kth largest of a k-sized heap.
4. Using `heapreplace` when the heap has fewer than k elements — raises no
   error but silently discards the smallest existing element instead of
   growing the heap to size k, giving a wrong kth-largest until the stream
   catches up. Always branch on `len(self.heap) < self.k` first.
5. Not copying `nums` before `heapify` — `heapq.heapify(nums)` mutates the
   caller's list in place; using `nums[:]` (as above) avoids surprising the
   caller, matching this repo's "mutates input?" discipline.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if `k` can change after construction?" — re-trim/re-grow the heap;
  growing means re-heapifying with more source data if the discarded
  elements are gone (they may need to be tracked separately, or you accept
  O(n) full rebuild from a retained full history).
- "What if you also need to support removing an arbitrary value from the
  stream?" — plain `heapq` has no O(log n) arbitrary-delete; needs a
  lazy-deletion marker set or an indexed heap (position map) to do better
  than O(n) scan-and-rebuild.
- "Kth SMALLEST of a stream instead?" — symmetric: keep a max-heap (negate
  values) of size k holding the k smallest seen so far; root is the answer.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 12/004 Kth Largest Element in an Array — same idea, one-shot instead of a
  live stream (no `add` calls after construction).
- 12/002 Last Stone Weight — max-heap driven simulation, this topic.
- 12/009 Find Median from Data Stream — two-heap generalization of "track a
  moving boundary over a stream," see guide §5.
================================================================================
"""

import heapq
import random
import time


class KthLargest:
    def __init__(self, k: int, nums: list[int]):
        self.k = k
        self.heap = nums[:]          # copy: never mutate caller's list
        heapq.heapify(self.heap)     # O(n)
        while len(self.heap) > k:
            heapq.heappop(self.heap)

    def add(self, val: int) -> int:
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, val)
        elif val > self.heap[0]:
            heapq.heapreplace(self.heap, val)
        return self.heap[0]


# --------------------------------------------------------------------------
# Baseline for the runtime demo: re-sort (bisect.insort) on every add.
# --------------------------------------------------------------------------
import bisect


class KthLargestSorted:
    def __init__(self, k: int, nums: list[int]):
        self.k = k
        self.sorted_nums = sorted(nums)

    def add(self, val: int) -> int:
        bisect.insort(self.sorted_nums, val)
        return self.sorted_nums[-self.k]


def run_tests():
    kl = KthLargest(3, [4, 5, 8, 2])
    assert kl.add(3) == 4
    assert kl.add(5) == 5
    assert kl.add(10) == 5
    assert kl.add(9) == 8
    assert kl.add(4) == 8

    # nums shorter than k
    kl2 = KthLargest(1, [])
    assert kl2.add(-3) == -3
    assert kl2.add(-2) == -2
    assert kl2.add(-4) == -2
    assert kl2.add(0) == 0
    assert kl2.add(4) == 4

    # duplicates
    kl3 = KthLargest(2, [0])
    assert kl3.add(-1) == -1
    assert kl3.add(1) == 0
    assert kl3.add(-2) == 0
    assert kl3.add(-4) == 0
    assert kl3.add(3) == 1

    # input not mutated
    original = [4, 5, 8, 2]
    KthLargest(3, original)
    assert original == [4, 5, 8, 2], "KthLargest must not mutate caller's list"

    # --- Runtime demo: heap-of-size-k vs re-sort-on-every-add ---------------
    random.seed(42)
    n_initial = 2000
    n_adds = 4000
    k = 50
    init_nums = [random.randint(-10**6, 10**6) for _ in range(n_initial)]
    add_vals = [random.randint(-10**6, 10**6) for _ in range(n_adds)]

    heap_kl = KthLargest(k, init_nums)
    t0 = time.perf_counter()
    heap_results = [heap_kl.add(v) for v in add_vals]
    heap_time = time.perf_counter() - t0

    sorted_kl = KthLargestSorted(k, init_nums)
    t0 = time.perf_counter()
    sorted_results = [sorted_kl.add(v) for v in add_vals]
    sorted_time = time.perf_counter() - t0

    assert heap_results == sorted_results, "both approaches must agree"

    print(f"Heap-of-size-{k}: {n_adds} add() calls in {heap_time*1000:.2f} ms")
    print(f"bisect.insort:    {n_adds} add() calls in {sorted_time*1000:.2f} ms")
    print(f"heap is {sorted_time / heap_time:.1f}x faster on this run")
    assert heap_time < sorted_time, (
        "expected the size-k heap to beat bisect.insort on a stream this long"
    )

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
