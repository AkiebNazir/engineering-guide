"""
================================================================================
SOLUTION · LeetCode 57 · Insert Interval                              [Medium]
https://leetcode.com/problems/insert-interval/
================================================================================

THE CORE IDEA
--------------
`intervals` is ALREADY sorted and already merged (no internal overlaps) —
that's a gift the problem hands you. Throwing it away by appending
`newInterval` and re-sorting/re-merging from scratch (like 002 Merge
Intervals would) costs O(n log n) when the structure already lets you do it
in a single O(n) pass: walk once, bucket every interval into exactly one of
three phases relative to `newInterval` — entirely BEFORE it (no overlap,
copy as-is), OVERLAPPING it (absorb into a growing merged interval), or
entirely AFTER it (no overlap, copy as-is) — and the phases never go
backwards because the input is sorted.

================================================================================
APPROACH 0 · Append + full re-merge, like LC 56 (priced, not coded)
================================================================================
`intervals.append(newInterval)`, sort by start (O(n log n)), then run the
002 Merge Intervals sweep (O(n)). Correct — total O(n log n) — but throws
away the fact that `intervals` was already sorted and merged; a linear
single pass suffices.

================================================================================
APPROACH 1 · Three-phase single pass ✅ (the answer)
================================================================================
    def insert(intervals, newInterval):
        result = []
        i, n = 0, len(intervals)
        ns, ne = newInterval

        # phase 1: intervals ending strictly before newInterval starts
        while i < n and intervals[i][1] < ns:
            result.append(intervals[i])
            i += 1

        # phase 2: intervals overlapping newInterval -- absorb them
        while i < n and intervals[i][0] <= ne:
            ns = min(ns, intervals[i][0])
            ne = max(ne, intervals[i][1])
            i += 1
        result.append([ns, ne])

        # phase 3: everything else, starts strictly after newInterval ends
        while i < n:
            result.append(intervals[i])
            i += 1

        return result

Time:  O(n) — each interval is visited exactly once, across all three
       `while` loops combined (they partition the index range, never
       revisit).
Space: O(n) for the output.

================================================================================
APPROACH 2 · Binary search the insertion boundaries (variant)
================================================================================
Since `intervals` is sorted by start, `bisect` can locate the first index
where overlap could begin and the last index where it could end in
O(log n), narrowing WHERE to scan — but you still must scan every
overlapping interval to merge them (that part can't be sub-linear), so this
only saves time on the non-overlapping copy boundaries, not the overlap
region itself. Worth naming as "you could binary-search the split points"
but the overall complexity is still O(n) because the merge region dominates
in the worst case (all intervals overlap `newInterval`).

--------------------------------------------------------------------------------
STEP BY STEP TRACE — intervals=[[1,2],[3,5],[6,7],[8,10],[12,16]], newInterval=[4,8]
--------------------------------------------------------------------------------
Number line:
     1  2   3    5   6  7  8    10      12          16
     |--|   |----|   |--|  |----|        |-----------|
     [1..2]
             [3......5]
                        [6..7]
                                 [8.......10]
                                              [12..........16]
                     [4...............8]   <- newInterval

ns, ne = 4, 8

Phase 1 (intervals[i].end < ns=4, copy as-is):
  intervals[0]=[1,2]: 2 < 4 -> copy. result=[[1,2]]. i=1
  intervals[1]=[3,5]: 5 < 4?  No -> stop phase 1.

Phase 2 (intervals[i].start <= ne=8, absorb & grow):
  intervals[1]=[3,5]: 3 <= 8 -> ns=min(4,3)=3, ne=max(8,5)=8. i=2
  intervals[2]=[6,7]: 6 <= 8 -> ns=min(3,6)=3, ne=max(8,7)=8. i=3
  intervals[3]=[8,10]: 8 <= 8 -> ns=min(3,8)=3, ne=max(8,10)=10. i=4
  intervals[4]=[12,16]: 12 <= 10? No -> stop phase 2.
  append merged [3,10]. result=[[1,2],[3,10]]

Phase 3 (copy the rest as-is):
  intervals[4]=[12,16] -> copy. result=[[1,2],[3,10],[12,16]]

Result: [[1,2],[3,10],[12,16]] — matches expected output.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                         | Time        | Space | Mutates input?  |
|-------------------------------------|------------|-------|-------------------|
| 0 · append + full re-merge (like 002)| O(n log n) | O(n)  | Depends (append mutates unless copied first) |
| 1 · three-phase single pass ✅      | O(n)       | O(n)  | No               |
| 2 · binary-search the boundaries    | O(n)*      | O(n)  | No               |

*Still O(n) worst case since the overlap region itself needs a full scan
to merge; binary search only tightens the non-overlap boundaries.

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Empty `intervals` — phases 1 and 3 never run; phase 2's `while` also
  never runs (n=0); `result = [newInterval]` directly. Handled naturally by
  the loop bounds, no special-casing needed.
- `newInterval` overlaps NOTHING and belongs at the very front or very back
  — phase 2 never triggers (its `while` condition is false immediately),
  `result.append([ns, ne])` still runs and inserts `newInterval` unchanged
  at the correct sorted position because phase 1 already consumed
  everything before it (or phase 1 consumed nothing and it goes first).
- `newInterval` fully swallows every existing interval, e.g.
  `intervals=[[1,5]], newInterval=[0,10]` — phase 2 absorbs `[1,5]`,
  `ns,ne` stay `0,10` since `min(0,1)=0` and `max(10,5)=10` — output
  `[[0,10]]`.
- `newInterval` is fully swallowed by one existing interval, e.g.
  `intervals=[[1,10]], newInterval=[2,5]` — phase 2 absorbs `[1,10]`,
  `ns=min(2,1)=1, ne=max(5,10)=10` — output `[[1,10]]`, `newInterval`
  vanishes into the larger block, correctly.
- Touching boundaries, e.g. `intervals=[[1,3]], newInterval=[3,5]` — phase 2
  condition is `intervals[i][0] <= ne`, i.e. `1 <= 5` triggers absorption of
  `[1,3]`; separately, `newInterval` touching from the OTHER side (e.g.
  `intervals=[[6,8]], newInterval=[1,3]`) — phase 1 condition `end < ns` is
  `8 < 1`? No, so `[6,8]` is NOT phase 1; phase 2 condition `start <= ne` is
  `6 <= 3`? No either — `[6,8]` correctly falls to phase 3 untouched, and
  `[1,3]` merges with nothing, matching this problem's `[1,4],[4,5]`-style
  "touching merges" rule (`<=`, not `<`) from Merge Intervals.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Using strict `<` in the phase-2 overlap test (`intervals[i][0] < ne`
   instead of `<=`) — fails to merge touching intervals, leaving two
   separate blocks that should have become one, e.g. `[1,3]` and
   `newInterval=[3,5]` stay unmerged instead of becoming `[1,5]`.
2. Forgetting `ns = min(ns, intervals[i][0])` in phase 2 and only updating
   `ne` — silently breaks when an overlapping existing interval starts
   BEFORE `newInterval` does (e.g. `intervals=[[1,3]], newInterval=[2,4]`);
   the merged interval's start should become 1, not stay 2.
3. Re-sorting from scratch (Approach 0) when the problem statement already
   guarantees sorted, non-overlapping input — not wrong, but throws away a
   free O(n) speedup and is a giveaway you didn't notice the guarantee, a
   detail interviewers explicitly test for in this problem.
4. Off-by-one in the phase-1 boundary: using `intervals[i][1] <= ns`
   instead of `< ns` would incorrectly skip an interval that TOUCHES
   `newInterval` at its start into phase 1 (no-overlap) when it should be
   absorbed in phase 2.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if you need to insert MANY intervals, not just one?" -> repeating
  this O(n) insert k times is O(nk); better to append all k, then run the
  O(n log n) Merge Intervals sweep once (Approach 0's logic, but amortized
  across many inserts it's now the WINNER).
- "What if `intervals` weren't guaranteed sorted/non-overlapping?" -> you'd
  have to fall back to Approach 0 in full: append, sort, merge.
- "Can you do this with binary search to beat O(n)?" -> no — the answer
  itself can require touching O(n) intervals (if `newInterval` overlaps all
  of them), so O(n) is optimal in the worst case; binary search only helps
  find the boundaries faster when overlap is sparse.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 19/002 Merge Intervals — the general (unsorted, unmerged) version this
  problem specializes; Approach 0 here IS problem 002's algorithm.
- 19/008 Employee Free Time — also relies on the "already sorted, walk and
  merge in one pass" idea, generalized to k input lists.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def insert(
        self, intervals: List[List[int]], newInterval: List[int]
    ) -> List[List[int]]:
        result = []
        i, n = 0, len(intervals)
        ns, ne = newInterval

        while i < n and intervals[i][1] < ns:
            result.append(intervals[i])
            i += 1

        while i < n and intervals[i][0] <= ne:
            ns = min(ns, intervals[i][0])
            ne = max(ne, intervals[i][1])
            i += 1
        result.append([ns, ne])

        while i < n:
            result.append(intervals[i])
            i += 1

        return result


# --------------------------------------------------------------------------
# Baseline for the runtime demo: append + full re-sort + re-merge (002's
# algorithm), which throws away the "already sorted" guarantee.
# --------------------------------------------------------------------------
class SolutionAppendAndRemerge:
    def insert(
        self, intervals: List[List[int]], newInterval: List[int]
    ) -> List[List[int]]:
        combined = [iv[:] for iv in intervals] + [newInterval[:]]
        combined.sort(key=lambda iv: iv[0])
        merged = [combined[0][:]]
        for start, end in combined[1:]:
            if start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return merged


def run_tests():
    sol = Solution()
    assert sol.insert([[1, 3], [6, 9]], [2, 5]) == [[1, 5], [6, 9]]
    assert sol.insert(
        [[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]
    ) == [[1, 2], [3, 10], [12, 16]]
    assert sol.insert([], [5, 7]) == [[5, 7]]
    assert sol.insert([[1, 5]], [2, 3]) == [[1, 5]]
    assert sol.insert([[1, 5]], [6, 8]) == [[1, 5], [6, 8]]
    assert sol.insert([[3, 5]], [1, 2]) == [[1, 2], [3, 5]]
    assert sol.insert([[1, 5]], [0, 10]) == [[0, 10]]
    assert sol.insert([[1, 3]], [3, 5]) == [[1, 5]]  # touching -> merges

    # input not mutated
    original = [[1, 2], [3, 5]]
    snapshot = [iv[:] for iv in original]
    sol.insert(original, [4, 4])
    assert original == snapshot, "insert must not mutate intervals"

    # cross-check against append+re-merge baseline on random inputs
    random.seed(21)
    baseline = SolutionAppendAndRemerge()
    for _ in range(200):
        n = random.randint(0, 12)
        pts = sorted(random.sample(range(0, 60), k=min(2 * n, 40)))
        ivs = []
        cursor = 0
        while cursor + 1 < len(pts) and len(ivs) < n:
            s, e = pts[cursor], pts[cursor] + random.randint(0, 3)
            if ivs and s <= ivs[-1][1]:
                cursor += 1
                continue
            ivs.append([s, e])
            cursor += 2
        ns = random.randint(0, 60)
        ne = ns + random.randint(0, 10)
        got = sol.insert([iv[:] for iv in ivs], [ns, ne])
        want = baseline.insert([iv[:] for iv in ivs], [ns, ne])
        assert got == want, f"mismatch: intervals={ivs} new=[{ns},{ne}] got={got} want={want}"

    # --- measured runtime demo: O(n) single pass vs O(n log n) re-sort ---
    n = 200_000
    intervals = [[i * 3, i * 3 + 1] for i in range(n)]
    new_interval = [n * 3 // 2, n * 3 // 2 + 2]

    t0 = time.perf_counter()
    fast_result = sol.insert(intervals, new_interval)
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    slow_result = baseline.insert(intervals, new_interval)
    slow_time = time.perf_counter() - t0

    assert fast_result == slow_result

    print(f"n={n} intervals (this machine, CPython):")
    print(f"  three-phase single pass O(n):      {fast_time*1000:8.3f} ms")
    print(f"  append + full re-sort O(n log n):  {slow_time*1000:8.3f} ms")
    print(f"  single pass is {slow_time / fast_time:.1f}x faster")
    assert fast_time < slow_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
