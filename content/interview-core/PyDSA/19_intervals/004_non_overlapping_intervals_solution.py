"""
================================================================================
SOLUTION · LeetCode 435 · Non-overlapping Intervals                   [Medium]
https://leetcode.com/problems/non-overlapping-intervals/
================================================================================

THE CORE IDEA
--------------
"Minimum removals to de-conflict" is the mirror image of "maximum intervals
you can KEEP" (removals = n - kept). Maximizing the kept count is the classic
*activity selection* greedy: sort by END time, and greedily keep every
interval that doesn't conflict with the last one you kept. Sorting by END
(not start!) is what makes the greedy provably optimal — see
`_TOPIC_GUIDE.md` §2b for the exchange-argument proof and a worked
counter-example showing sort-by-start under-counts. This file reproduces
that counter-example live in the test suite below.

Boundary rule for THIS problem: touching does NOT count as overlapping —
`[1,2]` and `[2,3]` can both be kept. The "no conflict with last kept"
check is therefore `interval.start >= last_kept.end` (non-strict `>=`).

================================================================================
APPROACH 0 · Brute-force subset search (priced, not coded)
================================================================================
Try every subset of intervals, keep the largest subset with no pairwise
overlap, return `n - |largest subset|`. O(2^n) subsets, O(n) to validate
each -> O(n * 2^n). Only tractable for tiny n; useless at n = 10^5.

================================================================================
APPROACH 1 · Sort by END, greedy keep ✅ (the answer)
================================================================================
    def eraseOverlapIntervals(intervals):
        intervals.sort(key=lambda iv: iv[1])     # sort by END, not start
        kept_end = float('-inf')
        kept = 0
        for start, end in intervals:
            if start >= kept_end:                # no conflict -> keep it
                kept += 1
                kept_end = end
        return len(intervals) - kept

Time:  O(n log n) for the sort, O(n) for the greedy scan -> O(n log n).
Space: O(1) extra beyond the sort.

================================================================================
APPROACH 2 · Wrong-but-tempting: sort by START (shown live to be incorrect)
================================================================================
Sorting by start and greedily keeping every non-conflicting interval you
meet LOOKS like the same idea but is NOT — a long, early-starting interval
can block out several short intervals that would have fit had they been
considered first. Priced the same as Approach 1 (O(n log n)) but gives the
WRONG answer on some inputs. Demonstrated live in the test suite below on
`[[1,10],[2,3],[4,5]]`, straight from `_TOPIC_GUIDE.md` §2b.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — intervals = [[1,2],[2,3],[3,4],[1,3]]
--------------------------------------------------------------------------------
Sort by END: [[1,2],[2,3],[1,3],[3,4]]  (end=2, end=3, end=3, end=4;
             ties [2,3] vs [1,3] both end at 3 -- either relative order works)

Number line:
     1  2  3  4
     |--|
        [2..3]
     [1.....3]
           [3..4]

kept_end = -inf, kept = 0

iv=[1,2]: 1 >= -inf? Yes -> keep. kept=1, kept_end=2
iv=[2,3]: 2 >= 2?    Yes -> keep. kept=2, kept_end=3
iv=[1,3]: 1 >= 3?    No  -> discard (conflicts with kept_end=3)
iv=[3,4]: 3 >= 3?    Yes -> keep. kept=3, kept_end=4

kept=3, n=4 -> removals = 4 - 3 = 1. Matches expected output.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                          | Time        | Space | Mutates input? | Correct? |
|--------------------------------------|------------|-------|-------------------|----------|
| 0 · brute-force subset search        | O(n*2^n)   | O(n)  | No               | Yes      |
| 1 · sort by END, greedy ✅           | O(n log n) | O(1)* | YES (`.sort()`)  | Yes      |
| 2 · sort by START, greedy (WRONG)    | O(n log n) | O(1)* | YES (`.sort()`)  | **No**   |

*O(1) extra beyond the in-place sort's own O(n) internal usage.

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single interval — 0 removals needed, loop keeps it, `1 - 1 = 0`.
- All intervals identical, e.g. `[[1,2],[1,2],[1,2]]` — sort by end leaves
  them in arbitrary tied order; keep the first (kept_end=2), the rest all
  fail `start(1) >= kept_end(2)` -> discard both -> removals = 2.
- Touching intervals, e.g. `[[1,2],[2,3]]` — NOT a conflict (`>=`, not `>`)
  -> both kept -> 0 removals. Get this operator backwards and you'd
  over-remove intervals that were actually fine to keep together.
- One interval spans everything else, e.g. `[[1,10],[2,3],[4,5]]` — sorting
  by end puts `[2,3]` and `[4,5]` before `[1,10]`; both get kept, `[1,10]`
  conflicts with `kept_end=5` and is discarded -> removals = 1, keeping 2.
  This is THE case that breaks sort-by-start (see Approach 2's live demo).
- Negative coordinates (constraints allow `starti` down to -5*10^4) — no
  special handling needed; comparisons work identically on negative ints.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Sorting by START instead of END.** The single most common mistake in
   this problem family — it looks like the same greedy idea as Meeting
   Rooms / Merge Intervals, but for "maximum keepable subset" the sort key
   MUST be end time. Proven wrong live below on `[[1,10],[2,3],[4,5]]`
   (start-sort keeps only 1 interval; the true answer keeps 2).
2. Using strict `>` instead of `>=` in the keep condition — incorrectly
   treats touching intervals as conflicting, over-counting removals.
3. Returning `kept` instead of `len(intervals) - kept` — the problem asks
   for REMOVALS, not the size of the kept set; an easy off-by-answer
   mistake under interview pressure.
4. Forgetting to initialize `kept_end` to `-inf` (or the first interval's
   end after sorting) — starting it at `0` breaks on negative-coordinate
   inputs, since a legitimately non-conflicting interval starting at a
   negative number would be wrongly discarded.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "Can you also return WHICH intervals to remove, not just the count?" ->
  track which intervals fail the `start >= kept_end` check during the scan
  and collect them into a removal list, same O(n log n) overall.
- "Why does sort-by-end work but sort-by-start doesn't? Prove it." -> the
  exchange argument: among all valid choices for "the interval to keep
  first," the earliest-ending one leaves the most room for everything
  after it, so swapping any other choice for the earliest-ending one can
  never make the remaining schedule worse. See `_TOPIC_GUIDE.md` §2b.
- "How does this relate to Minimum Arrows to Burst Balloons?" -> nearly
  identical greedy (also sort-by-end), but the "keep" condition there uses
  strict `>` because in that problem touching balloons CAN share one arrow
  (see problem 007 in this topic).

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 19/007 Minimum Arrows to Burst Balloons — the same sort-by-end greedy,
  different boundary semantics (touching intervals ARE "poppable together").
- 19/001 Meeting Rooms — sort-by-START is correct there because the
  question is "does ANY conflict exist," not "maximize a conflict-free
  subset" — the two problems look similar but need opposite sort keys.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def eraseOverlapIntervals(self, intervals: List[List[int]]) -> int:
        intervals.sort(key=lambda iv: iv[1])
        kept_end = float("-inf")
        kept = 0
        for start, end in intervals:
            if start >= kept_end:
                kept += 1
                kept_end = end
        return len(intervals) - kept


# --------------------------------------------------------------------------
# WRONG variant: sorts by START instead of END. Shown live below to give
# an incorrect (too-high) removal count on a small counter-example.
# --------------------------------------------------------------------------
class SolutionWrongSortByStart:
    def eraseOverlapIntervals(self, intervals: List[List[int]]) -> int:
        ivs = sorted(intervals, key=lambda iv: iv[0])
        kept_end = float("-inf")
        kept = 0
        for start, end in ivs:
            if start >= kept_end:
                kept += 1
                kept_end = end
        return len(ivs) - kept


# --------------------------------------------------------------------------
# Baseline for cross-checking: brute-force subset search (small n only).
# --------------------------------------------------------------------------
class SolutionBruteForce:
    def eraseOverlapIntervals(self, intervals: List[List[int]]) -> int:
        n = len(intervals)
        best_kept = 0
        for mask in range(1 << n):
            chosen = [intervals[i] for i in range(n) if mask & (1 << i)]
            chosen.sort(key=lambda iv: iv[0])
            ok = all(
                chosen[i][0] >= chosen[i - 1][1] for i in range(1, len(chosen))
            )
            if ok:
                best_kept = max(best_kept, len(chosen))
        return n - best_kept


def run_tests():
    sol = Solution()
    assert sol.eraseOverlapIntervals([[1, 2], [2, 3], [3, 4], [1, 3]]) == 1
    assert sol.eraseOverlapIntervals([[1, 2], [1, 2], [1, 2]]) == 2
    assert sol.eraseOverlapIntervals([[1, 2], [2, 3]]) == 0
    assert sol.eraseOverlapIntervals([[1, 100], [11, 22], [1, 11], [2, 12]]) == 2
    assert sol.eraseOverlapIntervals([[1, 10], [2, 3], [4, 5]]) == 1
    assert sol.eraseOverlapIntervals([[1, 2]]) == 0

    # live proof: sort-by-start is WRONG on the guide's counter-example
    wrong = SolutionWrongSortByStart()
    counter_example = [[1, 10], [2, 3], [4, 5]]
    correct_answer = sol.eraseOverlapIntervals([iv[:] for iv in counter_example])
    wrong_answer = wrong.eraseOverlapIntervals([iv[:] for iv in counter_example])
    assert correct_answer == 1, "sort-by-end should remove only [1,10]"
    assert wrong_answer == 2, "sort-by-start greedily keeps only [1,10], removing both others"
    assert wrong_answer != correct_answer
    print(
        f"BUG DEMO on {counter_example}: sort-by-end (correct) removes "
        f"{correct_answer}; sort-by-start (wrong) removes {wrong_answer}"
    )

    # cross-check against brute force on random small inputs
    random.seed(13)
    brute = SolutionBruteForce()
    for _ in range(150):
        n = random.randint(1, 8)
        ivs = []
        for _ in range(n):
            s = random.randint(0, 10)
            e = s + random.randint(1, 5)
            ivs.append([s, e])
        got = sol.eraseOverlapIntervals([iv[:] for iv in ivs])
        want = brute.eraseOverlapIntervals([iv[:] for iv in ivs])
        assert got == want, f"mismatch on {ivs}: got {got}, want {want}"

    # --- measured runtime demo: greedy O(n log n) vs brute O(n * 2^n) ---
    random.seed(4)
    n_small = 16
    ivs_small = []
    for _ in range(n_small):
        s = random.randint(0, 20)
        e = s + random.randint(1, 5)
        ivs_small.append([s, e])

    t0 = time.perf_counter()
    greedy_result = sol.eraseOverlapIntervals([iv[:] for iv in ivs_small])
    greedy_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    brute_result = brute.eraseOverlapIntervals([iv[:] for iv in ivs_small])
    brute_time = time.perf_counter() - t0

    assert greedy_result == brute_result

    print(f"n={n_small} intervals (this machine, CPython):")
    print(f"  greedy sort-by-end O(n log n): {greedy_time*1000:8.4f} ms")
    print(f"  brute-force subsets O(n*2^n):  {brute_time*1000:8.4f} ms")
    print(f"  greedy is {brute_time / greedy_time:.0f}x faster at just n={n_small}")
    assert greedy_time < brute_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
