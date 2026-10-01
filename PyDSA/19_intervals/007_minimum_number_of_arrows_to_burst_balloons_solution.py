"""
================================================================================
SOLUTION · LeetCode 452 · Minimum Number of Arrows to Burst Balloons  [Medium]
https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons/
================================================================================

THE CORE IDEA
--------------
Same sort-by-END greedy family as 004 Non-overlapping Intervals — but with
the touching-vs-overlapping boundary FLIPPED. Here, `[1,2]` and `[2,3]`
CAN be popped by ONE arrow (touching balloons share a shot), whereas in 004
touching intervals were fine to keep SEPARATE. That flip changes the
strict-vs-non-strict comparison in the greedy check, even though the sort
key and overall shape of the algorithm are identical. This is the sharpest
illustration in the whole topic of "the algorithm skeleton is reusable, the
boundary operator is NOT."

Framing: minimizing arrows = maximizing how many balloons EACH arrow bursts
= grouping balloons into the fewest possible "all mutually overlapping"
clusters. Sort by end, greedily start a new arrow only when the current
balloon starts strictly AFTER the current arrow's position.

================================================================================
APPROACH 0 · Brute-force clustering search (priced, not coded)
================================================================================
Try every way to partition points into overlapping clusters (equivalent to
brute-force interval graph coloring / subset search) and take the minimum
cluster count. Exponential — O(2^n)-ish. Only viable for tiny n.

================================================================================
APPROACH 1 · Sort by END, greedy arrow placement ✅ (the answer)
================================================================================
    def findMinArrowShots(points):
        if not points:
            return 0
        points.sort(key=lambda p: p[1])
        arrows = 1
        arrow_pos = points[0][1]
        for start, end in points[1:]:
            if start > arrow_pos:            # strict > -- touching still bursts
                arrows += 1
                arrow_pos = end
        return arrows

Time:  O(n log n) for the sort, O(n) for the scan.
Space: O(1) extra beyond the sort.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — points = [[10,16],[2,8],[1,6],[7,12]]
--------------------------------------------------------------------------------
Sort by end: [[1,6],[2,8],[7,12],[10,16]]  (ends: 6, 8, 12, 16)

Number line:
     1     6  7  8       12         16
     [1........6]
        [2...........8]
                   [7........12]
                                    [10..........16]

arrows=1, arrow_pos=6  (first arrow tentatively placed at the first
                        balloon's end)

iv=[2,8]: start=2 > arrow_pos=6?  No -> already burst by the arrow at x=6
          (2 <= 6 <= 8, confirmed). No new arrow.
iv=[7,12]: start=7 > arrow_pos=6? Yes -> needs a NEW arrow.
          arrows=2, arrow_pos=12
iv=[10,16]: start=10 > arrow_pos=12? No -> burst by the arrow at x=12
          (10 <= 12 <= 16). No new arrow.

Result: arrows=2 — matches expected output (arrows at x=6 and x=12, close
enough in spirit to the example's x=6/x=11 — any x in the valid overlap
range works, the COUNT is what's graded).

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                       | Time        | Space | Mutates input? |
|-----------------------------------|------------|-------|-------------------|
| 0 · brute-force clustering (brute)| O(2^n)-ish | O(n)  | No               |
| 1 · sort by end, greedy ✅        | O(n log n) | O(1)* | YES (`.sort()`)  |

*O(1) extra beyond the in-place sort's own internal usage.

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single balloon — 1 arrow, loop doesn't run.
- Empty input — 0 arrows (explicit guard; without it, `points[0]` would
  IndexError).
- ALL balloons disjoint, e.g. `[[1,2],[3,4],[5,6],[7,8]]` — every balloon
  needs its own arrow -> answer = n = 4.
- Touching balloons burst TOGETHER, e.g. `[[1,2],[2,3],[3,4],[4,5]]` — sort
  by end gives the same order; `arrow_pos` after `[1,2]` is 2; `[2,3]` has
  start=2, `2 > 2`? No -> shares the arrow. `[3,4]` has start=3, `3 > 2`?
  Yes -> new arrow at pos=4. `[4,5]` has start=4, `4 > 4`? No -> shares.
  Total 2 arrows. THIS is the exact reverse boundary rule from 004, where
  touching balloons would NOT have needed removal either, but here they
  actively SHARE an arrow because the strict `>` (not `>=`) treats a tie
  as "still in range."
- Duplicate balloons, e.g. `[[2,3],[2,3]]` — both burst by the same arrow,
  answer = 1.
- Extreme coordinate range (`-2^31` to `2^31-1`) — Python ints have no
  overflow concern; comparisons work identically.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Reusing 004's `>=` boundary here instead of `>`.** The two problems
   look identical (same sort key, same shape of loop) but have OPPOSITE
   touching semantics: 004's "keep" check is `start >= kept_end`
   (touching does NOT conflict, so both are kept separately); this
   problem's "new arrow needed" check is `start > arrow_pos` (touching
   DOES share an arrow, so `start == arrow_pos` must NOT trigger a new
   arrow). Copy-pasting 004's operator here silently overcounts arrows on
   any input with touching balloons.
2. Sorting by START instead of END — same failure mode as 004's Approach 2:
   a long early-starting balloon can block the greedy from correctly
   grouping several short, later balloons that all overlap each other.
3. Off-by-one in the initial `arrow_pos` — must initialize to
   `points[0][1]` (the END of the first sorted balloon), not `points[0][0]`
   (its start); the arrow logically fires at the earliest point that still
   bursts the first balloon and leaves maximum room for subsequent ones,
   which is that balloon's end.
4. Forgetting the empty-input guard before indexing `points[0]`.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "Why sort by end and not start, concretely?" -> same exchange-argument
  proof as 004: the earliest-ending balloon constrains the fewest future
  choices, so anchoring the first arrow there is never worse than any
  other choice.
- "What is the actual x-coordinate of each arrow, not just the count?" ->
  track `arrow_pos` at the moment each new arrow is created and collect
  those into a list alongside `arrows`.
- "How does the strict `>` here compare to 004's `>=`? Can you state the
  rule that decides which one to use in a novel interval problem?" -> ask
  "does touching count as a shared resource, or a genuine conflict?" for
  the SPECIFIC problem at hand — there's no universal answer, only a
  question you must ask every time (see `_TOPIC_GUIDE.md` §1).

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 19/004 Non-overlapping Intervals — identical algorithm skeleton (sort by
  end, greedy scan), opposite touching-boundary operator. Read them
  side-by-side to internalize the distinction.
- 19/005 Meeting Rooms II — a different "how many resources" question, but
  solved with sweep+heap rather than this single-pass greedy, because it
  needs a COUNT of concurrent overlaps at every instant, not just a
  clustering count.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def findMinArrowShots(self, points: List[List[int]]) -> int:
        if not points:
            return 0
        points.sort(key=lambda p: p[1])
        arrows = 1
        arrow_pos = points[0][1]
        for start, end in points[1:]:
            if start > arrow_pos:
                arrows += 1
                arrow_pos = end
        return arrows


# --------------------------------------------------------------------------
# WRONG variant: reuses 004's non-strict `>=` boundary. Shown live below to
# UNDER-count arrows (treats a touching balloon as needing a fresh shot
# less often than it should be allowed to share) -- actually this specific
# swap OVER-counts, since `>=` treats a tie as "out of range" (needs a new
# arrow) when a tie should mean "still shareable." Demonstrated, not
# asserted from memory.
# --------------------------------------------------------------------------
class SolutionWrongBoundary:
    def findMinArrowShots(self, points: List[List[int]]) -> int:
        if not points:
            return 0
        points.sort(key=lambda p: p[1])
        arrows = 1
        arrow_pos = points[0][1]
        for start, end in points[1:]:
            if start >= arrow_pos:  # BUG: should be strict >
                arrows += 1
                arrow_pos = end
        return arrows


class SolutionBruteForce:
    def findMinArrowShots(self, points: List[List[int]]) -> int:
        # minimum clique cover of an interval graph == greedy clustering;
        # brute force it directly by trying every assignment of balloons
        # to arrow-groups for small n (interval scheduling clustering).
        n = len(points)
        best = [n]

        def backtrack(idx, arrow_ranges):
            if len(arrow_ranges) >= best[0]:
                return
            if idx == n:
                best[0] = min(best[0], len(arrow_ranges))
                return
            s, e = points[idx]
            # try joining an existing arrow's range
            for i, (lo, hi) in enumerate(arrow_ranges):
                new_lo, new_hi = max(lo, s), min(hi, e)
                if new_lo <= new_hi:
                    arrow_ranges[i] = (new_lo, new_hi)
                    backtrack(idx + 1, arrow_ranges)
                    arrow_ranges[i] = (lo, hi)
            # try a new arrow
            arrow_ranges.append((s, e))
            backtrack(idx + 1, arrow_ranges)
            arrow_ranges.pop()

        backtrack(0, [])
        return best[0]


def run_tests():
    sol = Solution()
    assert sol.findMinArrowShots([[10, 16], [2, 8], [1, 6], [7, 12]]) == 2
    assert sol.findMinArrowShots([[1, 2], [3, 4], [5, 6], [7, 8]]) == 4
    assert sol.findMinArrowShots([[1, 2], [2, 3], [3, 4], [4, 5]]) == 2
    assert sol.findMinArrowShots([[1, 2]]) == 1
    assert sol.findMinArrowShots([[2, 3], [2, 3]]) == 1

    # live proof: the >= boundary variant is wrong on touching balloons
    wrong = SolutionWrongBoundary()
    touching = [[1, 2], [2, 3], [3, 4], [4, 5]]
    correct_answer = sol.findMinArrowShots([p[:] for p in touching])
    wrong_answer = wrong.findMinArrowShots([p[:] for p in touching])
    assert correct_answer == 2
    assert wrong_answer == 4, f"expected the >= bug to overcount to 4, got {wrong_answer}"
    print(
        f"BUG DEMO on {touching}: strict '>' (correct) needs {correct_answer} "
        f"arrows; non-strict '>=' (wrong) needs {wrong_answer}"
    )

    # cross-check against brute-force clustering on random small inputs
    random.seed(19)
    brute = SolutionBruteForce()
    for _ in range(80):
        n = random.randint(1, 7)
        pts = []
        for _ in range(n):
            s = random.randint(0, 10)
            e = s + random.randint(0, 4)
            pts.append([s, e])
        got = sol.findMinArrowShots([p[:] for p in pts])
        want = brute.findMinArrowShots([p[:] for p in pts])
        assert got == want, f"mismatch on {pts}: got {got}, want {want}"

    # --- measured runtime demo: greedy O(n log n) vs brute clustering ---
    random.seed(8)
    n_small = 10
    pts_small = []
    for _ in range(n_small):
        s = random.randint(0, 15)
        e = s + random.randint(0, 5)
        pts_small.append([s, e])

    t0 = time.perf_counter()
    greedy_result = sol.findMinArrowShots([p[:] for p in pts_small])
    greedy_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    brute_result = brute.findMinArrowShots([p[:] for p in pts_small])
    brute_time = time.perf_counter() - t0

    assert greedy_result == brute_result

    print(f"n={n_small} balloons (this machine, CPython):")
    print(f"  greedy sort-by-end O(n log n):  {greedy_time*1000:8.4f} ms")
    print(f"  brute-force clustering search:  {brute_time*1000:8.4f} ms")
    print(f"  greedy is {brute_time / greedy_time:.0f}x faster at just n={n_small}")
    assert greedy_time < brute_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
