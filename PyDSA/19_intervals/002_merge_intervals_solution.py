"""
================================================================================
SOLUTION · LeetCode 56 · Merge Intervals                              [Medium]
https://leetcode.com/problems/merge-intervals/
================================================================================

THE CORE IDEA
--------------
Sort by START. Once sorted, any interval that can possibly merge with the
block you're building MUST come immediately next in the scan — an interval
starting later than everything already merged can never retroactively need
to join an earlier block once you've moved past it. So a single left-to-right
sweep, extending or closing the current block, is enough — no need to revisit
anything. Sorting by END would let an interval that starts earlier slip in
AFTER one that should have been merged first, corrupting the merge order.

Boundary rule for THIS problem: `[1,4]` and `[4,5]` DO merge (touching counts
as overlapping) — a block ending at 4 and one starting at 4 are considered
continuous coverage. Merge condition: `next.start <= current.end` (non-strict).

================================================================================
APPROACH 0 · Brute-force repeated pairwise merge (priced, not coded)
================================================================================
Repeatedly scan all pairs, merge any that overlap, restart the scan, until a
full pass finds nothing to merge. Each full pass is O(n^2) to find a
mergeable pair, and up to O(n) passes may be needed -> O(n^3) worst case.
Correct, but absurdly wasteful compared to sorting first.

================================================================================
APPROACH 1 · Sort by start, single sweep ✅ (the answer)
================================================================================
    def merge(intervals):
        intervals.sort(key=lambda iv: iv[0])
        merged = [intervals[0]]
        for start, end in intervals[1:]:
            if start <= merged[-1][1]:            # overlaps/touches last block
                merged[-1][1] = max(merged[-1][1], end)   # NOT just `= end`!
            else:
                merged.append([start, end])
        return merged

Time:  O(n log n) for the sort, O(n) for the sweep -> O(n log n) overall.
Space: O(n) for the output (or O(1) extra beyond output + the in-place sort).

================================================================================
APPROACH 2 · Variant — build a new sorted copy, don't mutate input
================================================================================
`sorted(intervals, key=lambda iv: iv[0])` instead of `.sort()` avoids
mutating the caller's list, at the cost of an O(n) copy (same time
complexity, marginally more space). Worth mentioning if an interviewer asks
about side effects on shared data.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — intervals = [[1,3],[2,6],[8,10],[15,18]]
--------------------------------------------------------------------------------
Already sorted by start.

Number line:
     1  2  3        6              10          15    18
     |--|--|        |              |            |     |
     [1....3]
        [2........6]
                              [8....10]
                                          [15........18]

merged = [[1,3]]

iv=[2,6]: start=2 <= merged[-1].end=3?  Yes -> extend:
          merged[-1].end = max(3, 6) = 6  -> merged = [[1,6]]

iv=[8,10]: start=8 <= merged[-1].end=6?  No -> new block:
          merged = [[1,6], [8,10]]

iv=[15,18]: start=15 <= merged[-1].end=10?  No -> new block:
          merged = [[1,6], [8,10], [15,18]]

Result: [[1,6],[8,10],[15,18]] — matches expected output.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                          | Time        | Space | Mutates input?         |
|-------------------------------------|------------|-------|---------------------------|
| 0 · repeated pairwise merge (brute) | O(n^3)     | O(n)  | No (new lists per pass)  |
| 1 · sort + single sweep ✅          | O(n log n) | O(n)  | YES — `.sort()` is in-place |
| 2 · `sorted()` copy variant         | O(n log n) | O(n)  | No                       |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single interval — nothing to merge, return it as-is (still wrapped in a
  list, `[[1,4]]` not `[1,4]`).
- Fully nested intervals, e.g. `[1,4],[2,3]` — the inner interval's end (3)
  is LESS than the outer's end (4). `merged[-1][1] = max(merged[-1][1], end)`
  correctly keeps 4. Writing `merged[-1][1] = end` instead (no `max`) would
  silently SHRINK the block to `[1,3]`, losing the tail `[3,4]` — the single
  most common bug in this problem, see COMMON MISTAKES #1.
- Touching endpoints `[1,4],[4,5]` — DO merge (non-strict `<=`); see THE CORE
  IDEA boundary rule.
- Unsorted input, e.g. `[[1,4],[0,4]]` — must sort first; a naive "just scan
  in input order" fails here since `[0,4]` needs to come first to correctly
  absorb `[1,4]`.
- All intervals identical, e.g. `[[1,2],[1,2],[1,2]]` — merges down to a
  single `[1,2]`.
- Zero-length interval `[a,a]` (start == end allowed per constraints) —
  merges normally; `start <= end` logic doesn't special-case width-0.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. `merged[-1][1] = end` instead of `max(merged[-1][1], end)` — silently
   shrinks the block whenever a nested interval ends before the block it's
   being absorbed into. This passes on inputs without nesting and fails
   only on nested inputs — exactly the kind of bug that survives casual
   testing.
2. Forgetting to sort at all, or sorting by END instead of START — see
   `_TOPIC_GUIDE.md` §2a for why start-sort is required for merging.
3. Using strict `<` instead of `<=` in the overlap check — incorrectly
   leaves `[1,4]` and `[4,5]` as two separate blocks instead of merging
   them, violating this problem's touching-counts-as-overlapping rule.
4. Mutating and returning the SAME sublists that were sorted in place while
   also mutating a caller-visible list — usually harmless for LeetCode, but
   worth naming if asked "does this have side effects?"

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if intervals arrive one at a time (streaming) and you need the
  merged state after each insertion?" -> maintaining a sorted structure
  (e.g. a balanced BST of intervals, or `bisect.insort`) gives O(log n) find
  + O(n) worst-case shift per insert, versus O(n log n) full re-sort each
  time.
- "What if `intervals[i][0] > intervals[i][1]` is possible (malformed
  input)?" -> validate/normalize (swap or reject) before sorting.
- "Can you do this without extra space for the output?" -> not really below
  O(n): you must materialize at least the merged blocks; you CAN avoid a
  separate `merged` list by merging into `intervals` itself in place with a
  write pointer, trading code clarity for O(1) extra space beyond the sort.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 19/003 Insert Interval — the same merge machinery specialized: input is
  already sorted/merged, and you're inserting exactly one new interval.
- 19/008 Employee Free Time — flattens k lists then reuses this exact merge
  step before reading the answer off the GAPS between merged blocks.
- 19/001 Meeting Rooms — same sort-by-start scan, but a yes/no early-exit
  instead of building merged blocks.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        intervals.sort(key=lambda iv: iv[0])
        merged = [intervals[0][:]]
        for start, end in intervals[1:]:
            if start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])
        return merged


# --------------------------------------------------------------------------
# Buggy variant for the runtime/correctness demo: overwrites instead of
# max()-ing the end, so it silently shrinks nested-interval merges.
# --------------------------------------------------------------------------
class SolutionBuggyOverwrite:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        intervals.sort(key=lambda iv: iv[0])
        merged = [intervals[0][:]]
        for start, end in intervals[1:]:
            if start <= merged[-1][1]:
                merged[-1][1] = end  # BUG: no max() -- can shrink the block
            else:
                merged.append([start, end])
        return merged


# --------------------------------------------------------------------------
# Baseline for the runtime demo: O(n^3) repeated pairwise merge passes.
# --------------------------------------------------------------------------
class SolutionBruteForce:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        result = [iv[:] for iv in intervals]
        changed = True
        while changed:
            changed = False
            for i in range(len(result)):
                for j in range(i + 1, len(result)):
                    a, b = result[i], result[j]
                    if max(a[0], b[0]) <= min(a[1], b[1]):
                        merged = [min(a[0], b[0]), max(a[1], b[1])]
                        result.pop(j)
                        result.pop(i)
                        result.append(merged)
                        changed = True
                        break
                if changed:
                    break
        return sorted(result, key=lambda iv: iv[0])


def run_tests():
    sol = Solution()
    assert sol.merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [
        [1, 6],
        [8, 10],
        [15, 18],
    ]
    assert sol.merge([[1, 4], [4, 5]]) == [[1, 5]]
    assert sol.merge([[1, 4]]) == [[1, 4]]
    assert sol.merge([[1, 4], [2, 3]]) == [[1, 4]]
    assert sol.merge([[1, 4], [0, 4]]) == [[0, 4]]
    assert sol.merge([[1, 4], [5, 6]]) == [[1, 4], [5, 6]]

    # live proof: the buggy "overwrite instead of max" variant gets the
    # NESTED-interval case wrong while passing the simple cases.
    buggy = SolutionBuggyOverwrite()
    assert buggy.merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [
        [1, 6],
        [8, 10],
        [15, 18],
    ], "buggy variant happens to pass the non-nested case"
    buggy_nested = buggy.merge([[1, 4], [2, 3]])
    assert buggy_nested != [[1, 4]], "expected the bug to shrink the block"
    assert buggy_nested == [[1, 3]], f"bug should shrink to [1,3], got {buggy_nested}"
    print(f"BUG DEMO: merge([[1,4],[2,3]]) with no max() gives {buggy_nested},"
          f" not [[1, 4]] -- the nested interval's tail is silently lost")

    # cross-check against brute force on random inputs
    random.seed(5)
    brute = SolutionBruteForce()
    for _ in range(150):
        n = random.randint(1, 12)
        ivs = []
        for _ in range(n):
            s = random.randint(0, 20)
            e = s + random.randint(0, 8)
            ivs.append([s, e])
        got = sol.merge([iv[:] for iv in ivs])
        want = brute.merge([iv[:] for iv in ivs])
        assert got == want, f"mismatch on {ivs}: got {got}, want {want}"

    # --- measured runtime demo: sort+sweep vs O(n^3) brute force ---
    n = 300
    intervals = [[i * 3, i * 3 + 1] for i in range(n)]  # mostly non-overlapping
    random.seed(9)
    random.shuffle(intervals)

    t0 = time.perf_counter()
    fast_result = sol.merge([iv[:] for iv in intervals])
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    brute_result = brute.merge([iv[:] for iv in intervals])
    brute_time = time.perf_counter() - t0

    assert sorted(fast_result) == sorted(brute_result)

    print(f"n={n} intervals (this machine, CPython):")
    print(f"  sort + single sweep O(n log n): {fast_time*1000:8.3f} ms")
    print(f"  repeated pairwise merge O(n^3): {brute_time*1000:8.3f} ms")
    print(f"  sweep is {brute_time / fast_time:.0f}x faster")
    assert fast_time < brute_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
