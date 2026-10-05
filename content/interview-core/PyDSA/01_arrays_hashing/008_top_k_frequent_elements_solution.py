"""
================================================================================
SOLUTION · LeetCode 347 · Top K Frequent Elements                      [Medium]
https://leetcode.com/problems/top-k-frequent-elements/
================================================================================

THE CORE IDEA
-------------
Split the problem in two and notice they are independent:

    PHASE 1   count       O(n)   — a Counter. Never the bottleneck, never
                                   the interesting part.
    PHASE 2   select k    ???    — this is the entire problem.

Then the one insight that unlocks the optimal answer:

    A FREQUENCY IS A SMALL BOUNDED INTEGER.

No value can appear more than n times or fewer than once, so every frequency
lives in [1, n]. Whenever your sort key is a bounded integer, you do not need
comparison sorting at all — you can INDEX BY IT. That is bucket sort, and it
turns O(m log m) into O(n).

    buckets[f] = [every value that appears exactly f times]

Walk the buckets from the top down and take the first k values you meet. You
never compared two frequencies to each other.

This is the same instinct as LC 448's "the array is its own hash table": when
your keys are bounded, an array beats a comparison.


================================================================================
APPROACH 0 · Sort the counts (state it, then beat it)
================================================================================
    freq = Counter(nums)
    return sorted(freq, key=freq.get, reverse=True)[:k]

    Time:  O(n + m log m)     Space: O(m)

Perfectly correct, two lines, and what you should say FIRST. Then read the
follow-up out loud: "must be better than O(n log n)". Sorting is exactly what
it forbids, which is a giant arrow pointing at "you don't need total order —
you only need the top k."


================================================================================
APPROACH 1 · Min-heap of size k ✅ (the standard "top k" answer)
================================================================================
To keep the k LARGEST items, hold a MIN-heap of size k. The smallest of your
current winners sits at the root, which is exactly the one to evict when a
better candidate arrives.

    heap = []
    for val, f in freq.items():
        heapq.heappush(heap, (f, val))
        if len(heap) > k:
            heapq.heappop(heap)          # drop the weakest survivor
    return [val for f, val in heap]

    Time:  O(m log k)        Space: O(k)

STEP BY STEP for nums = [5,5,4,4,3,3,2,1], k = 3:

    freq = {5:2, 4:2, 3:2, 2:1, 1:1}      (m = 5 unique values)

    item      push               size>k?  pop       heap (root = smallest freq)
    --------  -----------------  -------  --------  --------------------------
    (2,5)     [(2,5)]            no                 [(2,5)]
    (2,4)     [(2,4),(2,5)]      no                 [(2,4),(2,5)]
    (2,3)     [...3 items...]    no                 [(2,3),(2,5),(2,4)]
    (1,2)     [...4 items...]    YES      (1,2)     [(2,3),(2,5),(2,4)]
    (1,1)     [...4 items...]    YES      (1,1)     [(2,3),(2,5),(2,4)]

    return [3, 5, 4]      ✓  (any order accepted)

⚠️  WHY MIN-HEAP AND NOT MAX-HEAP
    This is the counter-intuitive bit and interviewers ask it directly.
    A max-heap puts the BEST item at the root — but you never want to remove
    the best item, so the root is useless to you. You want cheap access to the
    WORST of your current winners, because that is the one a new candidate
    must beat. Min-heap root = weakest winner = the eviction candidate.

    Rule of thumb:  k LARGEST  -> min-heap of size k
                    k SMALLEST -> max-heap of size k
    You always heap the OPPOSITE of what you are looking for.

⚠️  PUSH-THEN-POP, NOT PUSH-IF-BIGGER
    `heappushpop(heap, item)` does both in one sift and is faster. But the
    naive `if f > heap[0][0]: heappushpop(...)` is a bug magnet when the heap
    is not yet full. Push unconditionally, then pop if oversized — it is
    obviously correct and the cost is identical.

    Note `heapq.nlargest(k, freq, key=freq.get)` does all of this for you, and
    CPython implements it with exactly this algorithm.


================================================================================
APPROACH 2 · Bucket sort by frequency ✅✅ (the O(n) answer)
================================================================================
Frequencies are bounded by n, so index an array by frequency directly.

    buckets = [[] for _ in range(len(nums) + 1)]     # index = frequency
    for val, f in Counter(nums).items():
        buckets[f].append(val)

    out = []
    for f in range(len(buckets) - 1, 0, -1):         # high freq -> low
        for val in buckets[f]:
            out.append(val)
            if len(out) == k:
                return out

    Time:  O(n)        Space: O(n)

STEP BY STEP for nums = [1,1,1,2,2,3], k = 2:

    freq = {1: 3, 2: 2, 3: 1}       n = 6, so buckets has indices 0..6

    index:    0     1     2     3     4     5     6
    bucket:  [ ]   [3]   [2]   [1]   [ ]   [ ]   [ ]
              ^     ^     ^     ^
              |     |     |     +-- value 1 appears 3 times
              |     |     +-------- value 2 appears 2 times
              |     +-------------- value 3 appears 1 time
              +-------------------- nothing appears 0 times (always empty)

    walk backwards from index 6:
       f=6 empty · f=5 empty · f=4 empty
       f=3 -> take 1   out=[1]
       f=2 -> take 2   out=[1,2]   len == k, return    ✓

⚠️  BUCKET SIZE MUST BE n+1, NOT n
    A value can appear all n times (`[4,4,4,4]` -> freq 4 with n = 4), so index
    n must exist. `range(len(nums))` gives 0..n-1 and raises IndexError on the
    all-same input. The tests below trigger this.

⚠️  IS THIS REALLY O(n)?
    Yes. Building buckets is O(m) <= O(n). The backward walk visits n+1 bucket
    indices and touches each unique value at most once, so it is O(n + m) =
    O(n). The nested loop LOOKS quadratic but the inner loop's total work
    across all iterations is bounded by m.

⚠️  THE SPACE TRADE — AND WHY O(n) CAN STILL LOSE
    Bucket sort allocates n+1 lists even when m is tiny: `[7]*100000` builds
    100001 list objects to hold one value. The heap uses O(k).

    The benchmark at the bottom of this file measures all three on n = 200000
    and finds something worth internalising: BUCKET SORT IS THE SLOWEST, even
    though it is the only O(n) option. Allocating 200001 Python list objects
    costs more wall-clock than sorting 20000 keys inside CPython's C-coded
    Timsort. The asymptotic win is real; the constant factor eats it alive.

    That does NOT make bucket sort the wrong interview answer — O(n) is the
    correct complexity claim and it is what the follow-up is fishing for. But
    "which would you actually deploy?" has a different answer, and it depends
    on m/n and on how cheap your language's allocation is. In Go, where a
    bucket is a nil slice header and costs nothing until appended to, the
    result flips. Knowing both is the senior answer.


================================================================================
APPROACH 3 · Quickselect (the "I know the theory" answer)
================================================================================
Partition the (value, freq) pairs around a pivot like quicksort, but recurse
into only ONE side — the side containing index k. Expected O(m), worst case
O(m²) on adversarial pivots (fixable with median-of-medians, O(m) worst case).

Worth naming because it is THE classic selection algorithm and it needs O(1)
extra space. Not worth coding here: bucket sort already gives guaranteed O(n)
with far less code and no pivot-choice risk. Mention it, move on.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(nums), m = unique values (m <= n), k <= m

    Approach              Time            Extra space   Mutates input?
    --------------------  --------------  ------------  --------------
    Sort the counts       O(n + m log m)  O(m)          no
    Min-heap size k   ✅  O(n + m log k)  O(m + k)      no
    Bucket sort     ✅✅  O(n)            O(n + m)      no
    Quickselect           O(m) expected   O(m)          reorders a copy

    Every approach pays O(n) for counting first — that term is unavoidable and
    is why "better than O(n log n)" is the bar, not "better than O(n)".


================================================================================
EDGE CASES
================================================================================
    ([1], 1)                 -> [1]
                                Single element. Bucket list must have index 1.

    ([4,4,4,4], 1)           -> [4]
                                MAX FREQUENCY == n. This is the case that
                                IndexErrors if you sized buckets as `range(n)`.

    ([1,2], 2)               -> [1,2]
                                k == m: you return everything. The heap never
                                evicts; the bucket walk drains every bucket.

    ([5,5,4,4,3,3,2,1], 3)   -> any 3 of {5,4,3}
                                TIES. Three values share frequency 2. The
                                problem guarantees the answer is unique, so a
                                real test never depends on tie order — but your
                                own asserts must not either. Compare sorted().

    ([-1,-1,-1,0,0,7], 2)    -> [-1,0]
                                NEGATIVE VALUES. Buckets are indexed by
                                FREQUENCY (always >= 1), never by the value, so
                                negatives are harmless. Anyone who tried to
                                index by value crashes here.


================================================================================
COMMON MISTAKES
================================================================================
1. Sizing buckets as `[[] for _ in range(len(nums))]` — IndexError the moment
   one value fills the whole array.

2. Using a MAX-heap and popping k times. It works (O(m + k log m) with
   heapify) but if you instead push all m items and pop k, you have paid
   O(m log m) — you did not beat sorting, you just rewrote it.

3. Indexing buckets by VALUE instead of by FREQUENCY. Dies on negatives and on
   any value larger than n.

4. Forgetting Python's heapq is min-only. To fake a max-heap, push `-f`.
   Getting the sign wrong silently returns the k LEAST frequent elements.

5. Comparing results with `==` in tests when ties exist. Order is not
   specified; compare `sorted(got) == sorted(want)`.

6. In the bucket walk, using `range(len(buckets)-1, -1, -1)` and including
   index 0. Harmless (bucket 0 is always empty — no value appears zero times)
   but it signals you have not thought about what index 0 means.

7. Returning as soon as a bucket is exhausted rather than when `len(out) == k`.
   A single bucket can hold several values; k may be satisfied mid-bucket.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: The array is a stream and does not fit in memory. Now what?
A: Exact top-k needs O(m) memory, period — you cannot know the winner without
   tracking every candidate. So go approximate: Count-Min Sketch for frequency
   estimates with a bounded-error guarantee, or the Space-Saving / Misra-Gries
   algorithm which finds all items above a frequency threshold in O(1/ε) space.
   This is the "heavy hitters" problem and it is a real system-design answer.

Q: k changes constantly and nums is fixed. Optimise for repeated queries.
A: Preprocess once: sort unique values by frequency descending, O(m log m).
   Every query is then an O(k) slice. Amortise the sort across queries.

Q: What if you need them in sorted-by-frequency order, not any order?
A: The bucket walk already emits high-to-low, so it is free there. The heap
   version needs a final sort of k items: + O(k log k).

Q: Why is O(n) not beatable?
A: You must read every element at least once to know its frequency. Any
   algorithm that skips an element can be wrong about it. O(n) is the floor.


================================================================================
RELATED PROBLEMS — the top-k / bucket family
================================================================================
    LC 692  Top K Frequent Words       — same, but ties break lexicographically,
                                          so the heap needs a custom comparator
    LC 451  Sort Characters By Freq    — bucket sort, emit the whole ordering
    LC 215  Kth Largest Element        — pure selection: heap or quickselect
    LC 973  K Closest Points to Origin — identical heap shape, distance as key
    LC 1046 Last Stone Weight          — max-heap simulation
    LC 295  Find Median from Stream    — TWO heaps, the classic follow-on
    LC 621  Task Scheduler             — greedy on frequencies (max-heap)
================================================================================
"""

import heapq
import random
import time
from collections import Counter
from typing import List


class Solution:
    def topKFrequent(self, nums: List[int], k: int) -> List[int]:
        """Bucket sort by frequency. Time O(n), space O(n). No mutation."""
        freq = Counter(nums)

        # Index = frequency. Size n+1 because a value may appear all n times.
        buckets = [[] for _ in range(len(nums) + 1)]
        for val, f in freq.items():
            buckets[f].append(val)

        out = []
        for f in range(len(buckets) - 1, 0, -1):     # high frequency -> low
            for val in buckets[f]:
                out.append(val)
                if len(out) == k:                    # may finish mid-bucket
                    return out
        return out

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def topKFrequent_heap(self, nums: List[int], k: int) -> List[int]:
        """Min-heap of size k. Time O(n + m log k), space O(m + k)."""
        heap = []
        for val, f in Counter(nums).items():
            heapq.heappush(heap, (f, val))
            if len(heap) > k:
                heapq.heappop(heap)          # evict the weakest winner
        return [val for _, val in heap]

    def topKFrequent_sort(self, nums: List[int], k: int) -> List[int]:
        """Sort the counts. O(n + m log m) — correct, but fails the follow-up."""
        freq = Counter(nums)
        return sorted(freq, key=freq.get, reverse=True)[:k]

    def topKFrequent_stdlib(self, nums: List[int], k: int) -> List[int]:
        """Counter.most_common — know it exists; implement it when asked."""
        return [val for val, _ in Counter(nums).most_common(k)]


# ==============================================================================
# TESTS — run:  python 008_top_k_frequent_elements_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    # Ties make exact output unstable, so cases carry the ACCEPTABLE frequency
    # multiset rather than one fixed answer where ties exist.
    cases = [
        ([1, 1, 1, 2, 2, 3], 2, [1, 2]),
        ([1], 1, [1]),
        ([1, 2], 2, [1, 2]),
        ([4, 4, 4, 4], 1, [4]),                       # max freq == n
        ([5, 5, 4, 4, 3, 3, 2, 1], 3, [3, 4, 5]),     # three-way tie
        ([-1, -1, -1, 0, 0, 7], 2, [-1, 0]),          # negative values
        ([3, 0, 1, 0], 1, [0]),
        ([1] * 50 + [2] * 30 + [3] * 20, 2, [1, 2]),
    ]
    impls = [
        ("bucket sort  ", sol.topKFrequent),
        ("min-heap     ", sol.topKFrequent_heap),
        ("sort counts  ", sol.topKFrequent_sort),
        ("most_common  ", sol.topKFrequent_stdlib),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(sorted(fn(list(nums), k)) == sorted(exp) for nums, k, exp in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # ----------------------------------------------------------------------
    # See the buckets.
    # ----------------------------------------------------------------------
    print("\n--- bucket layout for nums = [1,1,1,2,2,3], k = 2 ---")
    nums = [1, 1, 1, 2, 2, 3]
    buckets = [[] for _ in range(len(nums) + 1)]
    for val, f in Counter(nums).items():
        buckets[f].append(val)
    print(f"  index   {'  '.join(f'{i}' for i in range(len(buckets)))}")
    print(f"  bucket  {'  '.join(str(b) if b else '[]' for b in buckets)}")
    out = []
    for f in range(len(buckets) - 1, 0, -1):
        if buckets[f]:
            print(f"  f={f}: take {buckets[f]}", end="")
            for v in buckets[f]:
                out.append(v)
                if len(out) == 2:
                    print(f"  -> out={out}  len == k, STOP")
                    break
            else:
                print(f"  -> out={out}")
                continue
            break
        else:
            print(f"  f={f}: empty, skip")

    # ----------------------------------------------------------------------
    # ⚠️  buckets sized n instead of n+1 -> IndexError.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  why buckets must be size n+1 ---")
    bad = [4, 4, 4, 4]
    print(f"  nums = {bad}   n = {len(bad)}   freq(4) = {len(bad)}")
    try:
        small = [[] for _ in range(len(bad))]        # the bug: only 0..n-1
        for val, f in Counter(bad).items():
            small[f].append(val)
        print("  no error?! (should never print)")
    except IndexError as e:
        print(f"  buckets = [[] for _ in range(n)]  -> IndexError: {e}")
    ok = [[] for _ in range(len(bad) + 1)]
    for val, f in Counter(bad).items():
        ok[f].append(val)
    print(f"  buckets = [[] for _ in range(n+1)] -> OK, buckets[4] = {ok[4]}")

    # ----------------------------------------------------------------------
    # ⚠️  Min-heap vs max-heap: which root do you actually want?
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  min-heap keeps the k LARGEST. Watch the evictions. ---")
    freq = Counter([5, 5, 4, 4, 3, 3, 2, 1])
    k = 3
    heap = []
    print(f"  freq = {dict(freq)}   k = {k}")
    for val, f in freq.items():
        heapq.heappush(heap, (f, val))
        if len(heap) > k:
            evicted = heapq.heappop(heap)
            print(f"  push (f={f}, v={val})  size {k+1} > {k}  -> evict {evicted}"
                  f"   heap={sorted(heap)}")
        else:
            print(f"  push (f={f}, v={val})  root={heap[0]}"
                  f"   heap={sorted(heap)}")
    print(f"  result {[v for _, v in heap]}")
    print("  The root is the WEAKEST winner — exactly what a newcomer must beat.")

    # ----------------------------------------------------------------------
    # ⚠️  Wrong sign on a fake max-heap returns the k LEAST frequent.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  heapq is min-only; a sign slip inverts the answer ---")
    nums = [1] * 50 + [2] * 30 + [3] * 20 + [4] * 1
    freq = Counter(nums)
    right = [v for _, v in heapq.nlargest(2, ((f, v) for v, f in freq.items()))]
    wrong = [v for _, v in heapq.nsmallest(2, ((f, v) for v, f in freq.items()))]
    print(f"  freq = {dict(freq)}")
    print(f"  k largest  (correct) -> {sorted(right)}")
    print(f"  k smallest (sign bug)-> {sorted(wrong)}   same code, flipped sign")

    # ----------------------------------------------------------------------
    # Bucket O(n) vs sort O(m log m) — and where bucket's space hurts.
    # ----------------------------------------------------------------------
    print("\n--- O(n) bucket vs O(m log m) sort ---")
    random.seed(11)
    for n, spread in ((200_000, 20_000), (200_000, 50)):
        data = [random.randint(0, spread) for _ in range(n)]
        m = len(set(data))
        t0 = time.perf_counter(); sol.topKFrequent(data, 10)
        t_bucket = time.perf_counter() - t0
        t0 = time.perf_counter(); sol.topKFrequent_sort(data, 10)
        t_sort = time.perf_counter() - t0
        t0 = time.perf_counter(); sol.topKFrequent_heap(data, 10)
        t_heap = time.perf_counter() - t0
        print(f"  n={n} m={m:<6}  bucket {t_bucket*1000:6.1f}ms   "
              f"sort {t_sort*1000:6.1f}ms   heap {t_heap*1000:6.1f}ms")
    print("  Read that again: the O(n) algorithm LOSES to the O(m log m) one,")
    print("  in both rows. Allocating n+1 = 200001 Python list objects costs")
    print("  more than sorting 20000 keys in C. Bucket sort's win is real only")
    print("  when m is close to n AND allocation is cheap (a Go []([]int), a")
    print("  C array) — not when every bucket is a heap-allocated PyObject.")
    print("  Say 'O(n)' in the interview; know THIS when you ship it.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
