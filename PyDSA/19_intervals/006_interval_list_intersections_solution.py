"""
================================================================================
SOLUTION · LeetCode 986 · Interval List Intersections                 [Medium]
https://leetcode.com/problems/interval-list-intersections/
================================================================================

THE CORE IDEA
--------------
Both lists are ALREADY sorted by start and internally non-overlapping — that
is exactly the precondition for a linear two-pointer merge, the same trick
that makes the merge step of merge sort O(n) instead of O(n log n). At each
step, compute the overlap of the two CURRENT pointed-at intervals (if any),
then advance whichever one ends first — it's provably impossible for it to
intersect anything further along in the OTHER list, since that list is
sorted and non-overlapping (see `_TOPIC_GUIDE.md` §4).

================================================================================
APPROACH 0 · Brute-force all pairs (priced, not coded)
================================================================================
For every `i` in `firstList` and every `j` in `secondList`, compute the
overlap `[max(starts), min(ends)]` and keep it if `max(starts) <=
min(ends)`. O(n*m) pairs checked. Correct (order the kept results by
start afterward), but throws away the fact that BOTH lists are already
sorted — a two-pointer walk never needs to compare a pair more than once.

================================================================================
APPROACH 1 · Two-pointer merge walk ✅ (the answer)
================================================================================
    def intervalIntersection(A, B):
        result = []
        i = j = 0
        while i < len(A) and j < len(B):
            lo = max(A[i][0], B[j][0])
            hi = min(A[i][1], B[j][1])
            if lo <= hi:
                result.append([lo, hi])
            if A[i][1] < B[j][1]:
                i += 1
            else:
                j += 1
        return result

Time:  O(n + m) — each pointer advances at most n (or m) times total, never
       resets.
Space: O(n + m) worst case for the output (every interval in A can
       intersect an interval in B).

--------------------------------------------------------------------------------
STEP BY STEP TRACE — A=[[0,2],[5,10],[13,23],[24,25]], B=[[1,5],[8,12],[15,24],[25,26]]
--------------------------------------------------------------------------------
Number line (A above the axis, B below):
    0  1  2     5        10  12   15         23 24 25  26
    [0..2]
    A: [0..2]           [5......10]      [13.........23][24.25]
    B:    [1.....5]        [8.12]              [15........24]  [25.26]

i=0,j=0: A[0]=[0,2], B[0]=[1,5]. lo=max(0,1)=1, hi=min(2,5)=2. 1<=2 -> emit [1,2].
         A[0].end(2) < B[0].end(5) -> advance i. i=1.

i=1,j=0: A[1]=[5,10], B[0]=[1,5]. lo=max(5,1)=5, hi=min(10,5)=5. 5<=5 -> emit [5,5].
         A[1].end(10) < B[0].end(5)? No -> advance j. j=1.

i=1,j=1: A[1]=[5,10], B[1]=[8,12]. lo=max(5,8)=8, hi=min(10,12)=10. emit [8,10].
         A[1].end(10) < B[1].end(12) -> advance i. i=2.

i=2,j=1: A[2]=[13,23], B[1]=[8,12]. lo=max(13,8)=13, hi=min(23,12)=12. 13<=12? No -> skip.
         A[2].end(23) < B[1].end(12)? No -> advance j. j=2.

i=2,j=2: A[2]=[13,23], B[2]=[15,24]. lo=max(13,15)=15, hi=min(23,24)=23. emit [15,23].
         A[2].end(23) < B[2].end(24) -> advance i. i=3.

i=3,j=2: A[3]=[24,25], B[2]=[15,24]. lo=max(24,15)=24, hi=min(25,24)=24. emit [24,24].
         A[3].end(25) < B[2].end(24)? No -> advance j. j=3.

i=3,j=3: A[3]=[24,25], B[3]=[25,26]. lo=max(24,25)=25, hi=min(25,26)=25. emit [25,25].
         A[3].end(25) < B[3].end(26) -> advance i. i=4. Loop ends (i == len(A)).

Result: [[1,2],[5,5],[8,10],[15,23],[24,24],[25,25]] — matches expected.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                     | Time      | Space   | Mutates input? |
|-------------------------------|----------|---------|-------------------|
| 0 · brute-force all pairs     | O(n*m)   | O(n+m)  | No               |
| 1 · two-pointer merge walk ✅ | O(n+m)   | O(n+m)  | No               |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Either list empty — `while i < len(A) and j < len(B)` never runs -> `[]`.
  Both example 2 and a symmetric "second list empty" case are tested below.
- No overlaps at all, e.g. `A=[[1,3]], B=[[4,6]]` — `lo=4, hi=3`, `lo <= hi`
  is False -> nothing emitted, but the pointer still advances (whichever
  ends first: here A ends at 3 < B ends at 6, so `i` advances) — the walk
  correctly continues rather than getting stuck.
- Touching intervals, e.g. `A=[[1,3]], B=[[3,5]]` — `lo=max(1,3)=3,
  hi=min(3,5)=3`, `3<=3` -> emits a ZERO-WIDTH intersection `[3,3]` (a
  single point). This problem's closed-interval definition explicitly
  allows and expects this — the touching point IS the intersection, unlike
  Meeting Rooms where touching means "no conflict."
- One interval fully contains another, e.g. `A=[[1,10]], B=[[2,3]]` — the
  intersection is exactly the smaller one, `[2,3]`; `lo=max(1,2)=2,
  hi=min(10,3)=3`.
- Both pointers reach an interval that ends at the SAME time — the
  `if A[i][1] < B[j][1]` tie-break advances `j` (the `else` branch); either
  choice is safe here since both intervals are fully consumed together, but
  advancing only one avoids an infinite loop if the tie-break were written
  wrong (see COMMON MISTAKES #2).

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Concatenating both lists and re-sorting/re-merging (treating this like
   Merge Intervals) — wrong problem: merging COMBINES overlapping
   intervals into one, but this problem wants the INTERSECTION (the
   overlap region) kept as its own separate output, not merged away. Also
   throws away the O(n+m) two-pointer opportunity for no benefit.
2. Advancing BOTH pointers every iteration instead of only the one whose
   interval ends first — can skip a valid intersection between the
   not-yet-advanced interval and the next one in the other list.
3. Forgetting the `if lo <= hi` guard and appending `[lo, hi]`
   unconditionally — emits invalid/backwards "intervals" like `[13,12]`
   when the two current intervals don't actually overlap.
4. Using `<=` for the advance tie-break (`A[i][1] <= B[j][1]`) instead of
   strict `<` when advancing `i`, without also handling the equal case
   correctly for `j` — can cause both pointers to advance in ways that skip
   a valid pairing, or (if written carelessly) neither advances, causing an
   infinite loop. Advance strictly the one that ends first; on a tie,
   advancing either one (but only one) is safe.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if the lists weren't guaranteed sorted or non-overlapping?" -> sort
  each list first (O(n log n) + O(m log m)) and merge each internally if
  needed, THEN run the two-pointer walk — total O(n log n + m log m).
- "Can you extend this to k lists, not just 2?" -> a k-way merge, typically
  with a min-heap keyed by each list's current pointer's start — see
  problem 008 Employee Free Time, which flattens k lists via exactly this
  generalization (though for the UNION rather than pairwise intersection).
- "What's the maximum possible size of the output?" -> O(n+m) in the worst
  case (e.g. `A` and `B` are both many tiny intervals all inside one big
  overlapping region) — worth naming to show you've thought about output
  size, not just algorithmic time.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 19/002 Merge Intervals — same sort-by-start family, but combines instead
  of intersecting, and operates on ONE list instead of two.
- 19/008 Employee Free Time — generalizes the two-list merge idea to k
  lists for a UNION (not intersection).
- Merge step of merge sort (Topic 22, when written) — identical O(n+m)
  two-pointer merge mechanics.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def intervalIntersection(
        self, firstList: List[List[int]], secondList: List[List[int]]
    ) -> List[List[int]]:
        result = []
        i = j = 0
        while i < len(firstList) and j < len(secondList):
            lo = max(firstList[i][0], secondList[j][0])
            hi = min(firstList[i][1], secondList[j][1])
            if lo <= hi:
                result.append([lo, hi])
            if firstList[i][1] < secondList[j][1]:
                i += 1
            else:
                j += 1
        return result


# --------------------------------------------------------------------------
# Baseline for the runtime demo: brute-force all pairs, O(n*m).
# --------------------------------------------------------------------------
class SolutionBruteForce:
    def intervalIntersection(
        self, firstList: List[List[int]], secondList: List[List[int]]
    ) -> List[List[int]]:
        result = []
        for a in firstList:
            for b in secondList:
                lo = max(a[0], b[0])
                hi = min(a[1], b[1])
                if lo <= hi:
                    result.append([lo, hi])
        result.sort()
        return result


def run_tests():
    sol = Solution()
    assert sol.intervalIntersection(
        [[0, 2], [5, 10], [13, 23], [24, 25]], [[1, 5], [8, 12], [15, 24], [25, 26]]
    ) == [[1, 2], [5, 5], [8, 10], [15, 23], [24, 24], [25, 25]]
    assert sol.intervalIntersection([], [[1, 5]]) == []
    assert sol.intervalIntersection([[1, 5]], []) == []
    assert sol.intervalIntersection([[1, 3]], [[2, 4]]) == [[2, 3]]
    assert sol.intervalIntersection([[1, 3]], [[4, 6]]) == []
    assert sol.intervalIntersection([[1, 5]], [[2, 3]]) == [[2, 3]]
    assert sol.intervalIntersection([[1, 3]], [[3, 5]]) == [[3, 3]]

    # cross-check against brute-force on random non-overlapping sorted lists
    def random_disjoint_list(n, span=100):
        ivs = []
        cursor = 0
        for _ in range(n):
            cursor += random.randint(0, 4)
            start = cursor
            cursor += random.randint(0, 4)
            end = cursor
            ivs.append([start, end])
            cursor += 1  # ensure strictly disjoint (gap of at least 1)
        return ivs

    random.seed(6)
    brute = SolutionBruteForce()
    for _ in range(200):
        A = random_disjoint_list(random.randint(0, 8))
        B = random_disjoint_list(random.randint(0, 8))
        got = sol.intervalIntersection(A, B)
        want = brute.intervalIntersection(A, B)
        assert got == want, f"mismatch: A={A} B={B} got={got} want={want}"

    # --- measured runtime demo: two-pointer O(n+m) vs brute O(n*m) ---
    random.seed(1)
    n = 4000
    A = random_disjoint_list(n)
    B = random_disjoint_list(n)

    t0 = time.perf_counter()
    fast_result = sol.intervalIntersection(A, B)
    fast_time = time.perf_counter() - t0

    small_n = 400
    A_small, B_small = A[:small_n], B[:small_n]
    t0 = time.perf_counter()
    brute_result = brute.intervalIntersection(A_small, B_small)
    brute_time = time.perf_counter() - t0
    fast_small = sol.intervalIntersection(A_small, B_small)
    assert fast_small == brute_result

    print(f"n=m={n} intervals each (this machine, CPython):")
    print(f"  two-pointer merge walk O(n+m): {fast_time*1000:8.3f} ms")
    print(f"n=m={small_n} intervals each (brute force too slow at n=m={n}):")
    print(f"  brute-force all pairs O(n*m):  {brute_time*1000:8.3f} ms")
    print(f"  two-pointer handles {n}x{n} in less time than brute handles "
          f"{small_n}x{small_n}")

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
