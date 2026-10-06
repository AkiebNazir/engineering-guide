"""
================================================================================
SOLUTION · LeetCode 252 · Meeting Rooms                                 [Easy]
https://leetcode.com/problems/meeting-rooms/
================================================================================

THE CORE IDEA
--------------
"Can one person attend every meeting?" is exactly "does ANY pair of intervals
overlap?" Checking every pair is O(n^2). But if you SORT by start time first,
a conflict can only ever appear between a meeting and the one immediately
before it in sorted order — if meeting i overlaps something, the tightest
possible overlap is with i-1, because everything before i-1 already ended no
later than i-1 did (sorting by start doesn't guarantee that in general, but
checking the immediate predecessor's END against the current START is
sufficient here, since we only need a yes/no answer and the FIRST conflict
found anywhere proves the answer is "no"). Sort once, then one linear scan.

Boundary rule for THIS problem: `[1,2]` and `[2,3]` do **NOT** conflict — a
meeting ending at 2 and one starting at 2 can be attended by the same person
back-to-back. So the check is strict: `intervals[i][0] < intervals[i-1][1]`.

================================================================================
APPROACH 0 · Brute-force pairwise (priced, not coded)
================================================================================
For every pair (i, j), i != j, check if they overlap:
`max(a.start, b.start) < min(a.end, b.end)`. O(n^2) pairs, O(1) each ->
O(n^2) time, O(1) extra space. Correct but wasteful — most pairs are far
apart in time and never need comparing.

================================================================================
APPROACH 1 · Sort by start, scan for adjacent overlap ✅ (the answer)
================================================================================
    def canAttendMeetings(intervals):
        intervals.sort(key=lambda iv: iv[0])
        for i in range(1, len(intervals)):
            if intervals[i][0] < intervals[i - 1][1]:
                return False
        return True

Time:  O(n log n) for the sort, O(n) for the scan -> O(n log n) overall.
Space: O(1) extra (Timsort is O(n) internally, but no new data structure of
       ours is allocated; `sort()` is in-place — see EDGE CASES for the
       mutation consequence).

--------------------------------------------------------------------------------
STEP BY STEP TRACE — intervals = [[0,30],[5,10],[15,20]]
--------------------------------------------------------------------------------
Sort by start (already sorted here): [[0,30],[5,10],[15,20]]

Number line (each meeting drawn on its own row):
    0         5    10        15   20              30
    |---------|----|         |    |               |
    [0............................................30]
              [5....10]
                         [15..20]

i=1: intervals[1]=[5,10], intervals[0]=[0,30].
     5 < 30 (prev end)?  Yes -> CONFLICT -> return False immediately.

Result: False. [0,30] swallows both other meetings — correct, matches
example 1.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                     | Time         | Space | Mutates input?          |
|-------------------------------|-------------|-------|---------------------------|
| 0 · brute-force pairwise      | O(n^2)      | O(1)  | No                        |
| 1 · sort + linear scan ✅     | O(n log n)  | O(1)* | YES — `list.sort()` is in-place |

*`sorted()` instead of `.sort()` would make this O(n) extra space and leave
the caller's list untouched — see COMMON MISTAKES #2.

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Empty input `[]` — no meetings, trivially attendable -> True. The `for`
  loop never runs.
- Single meeting — no pair to conflict -> True.
- Touching endpoints `[1,2],[2,3]` — NOT a conflict (strict `<`). This is
  the topic's central "touching vs overlapping" question (see
  `_TOPIC_GUIDE.md` §1) and the #1 place interviewers probe: get the
  operator direction backwards (`<=` instead of `<`) and you'll reject a
  perfectly attendable back-to-back schedule.
- Nested meetings, e.g. `[1,10],[2,3]` — sorted by start puts `[1,10]`
  first; `2 < 10` -> correctly flagged as a conflict even though `[2,3]`
  doesn't "overlap the end" of `[1,10]` in a naive sense — it's fully
  inside it.
- Input already sorted, or sorted in reverse, or all identical — the sort
  handles every ordering identically; no special-casing needed.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Using `<=` instead of `<` in the conflict check — silently rejects valid
   back-to-back schedules where one meeting ends exactly when the next
   starts.
2. Sorting with `intervals.sort(...)` when the caller didn't expect their
   list mutated — for a LeetCode submission this doesn't matter, but in a
   real codebase mutating a caller's argument as a side effect of an
   "is this valid" QUERY function is a classic hidden-bug source. Use
   `sorted(intervals, key=...)` if the input must stay untouched.
3. Sorting by END instead of START — sorting by end does not let you use
   "compare only to the immediate predecessor," because an interval that
   starts very early but ends late could still be sitting earlier in a
   start-sorted list without being caught by an end-sorted adjacent check.
   Always sort by START for "does anything overlap" (see `_TOPIC_GUIDE.md`
   §2a).
4. Comparing every interval to the FIRST interval only, instead of the
   PREVIOUS one — misses conflicts between interval 3 and interval 2 when
   interval 1 doesn't conflict with either.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "How many rooms would you need if meetings CAN'T all be attended by one
  person?" -> that's LC 253, Meeting Rooms II, problem 005 in this topic.
- "What if intervals arrive as a stream, not a fixed array?" -> you'd need
  an ordered structure (e.g. a sorted list / balanced BST / interval tree)
  to keep the O(log n)-per-insert property instead of re-sorting from
  scratch each time.
- "Can you avoid mutating the input?" -> yes, use `sorted()` (O(n) extra
  space) instead of `.sort()` (in-place).

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 19/005 Meeting Rooms II — same sort-by-start idea, extended to COUNT
  concurrent overlaps instead of a yes/no check.
- 19/002 Merge Intervals — same sort-by-start scan, but extends/merges
  blocks instead of returning early on the first conflict.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def canAttendMeetings(self, intervals: List[List[int]]) -> bool:
        intervals.sort(key=lambda iv: iv[0])
        for i in range(1, len(intervals)):
            if intervals[i][0] < intervals[i - 1][1]:
                return False
        return True


# --------------------------------------------------------------------------
# Baseline for the runtime demo: brute-force pairwise overlap check.
# --------------------------------------------------------------------------
class SolutionBruteForce:
    def canAttendMeetings(self, intervals: List[List[int]]) -> bool:
        n = len(intervals)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = intervals[i], intervals[j]
                if max(a[0], b[0]) < min(a[1], b[1]):
                    return False
        return True


def run_tests():
    sol = Solution()
    assert sol.canAttendMeetings([[0, 30], [5, 10], [15, 20]]) is False
    assert sol.canAttendMeetings([[7, 10], [2, 4]]) is True
    assert sol.canAttendMeetings([]) is True
    assert sol.canAttendMeetings([[5, 8]]) is True
    assert sol.canAttendMeetings([[1, 2], [2, 3]]) is True
    assert sol.canAttendMeetings([[1, 5], [4, 8]]) is False
    assert sol.canAttendMeetings([[1, 10], [2, 3]]) is False

    # cross-check against brute force on random inputs
    random.seed(11)
    brute = SolutionBruteForce()
    for _ in range(300):
        n = random.randint(0, 15)
        ivs = []
        for _ in range(n):
            s = random.randint(0, 50)
            e = s + random.randint(1, 10)
            ivs.append([s, e])
        assert sol.canAttendMeetings(ivs[:]) == brute.canAttendMeetings(ivs[:])

    # --- measured runtime demo: sort+scan vs brute-force pairwise ---
    # Use NON-OVERLAPPING (all-True) meetings so brute force can't
    # short-circuit early on a random hit -- it must check every pair,
    # showing its true O(n^2) cost instead of getting lucky.
    n = 2500
    ivs = [[i * 10, i * 10 + 5] for i in range(n)]
    random.seed(3)
    random.shuffle(ivs)

    t0 = time.perf_counter()
    fast_result = sol.canAttendMeetings(ivs[:])
    fast_time = time.perf_counter() - t0
    assert fast_result is True

    t0 = time.perf_counter()
    brute_result = brute.canAttendMeetings(ivs[:])
    brute_time = time.perf_counter() - t0
    assert brute_result is True

    print(f"n={n} non-overlapping meetings (this machine, CPython):")
    print(f"  sort + linear scan  O(n log n): {fast_time*1000:8.3f} ms")
    print(f"  brute-force pairwise O(n^2):    {brute_time*1000:8.3f} ms")
    print(f"  sort+scan is {brute_time / fast_time:.0f}x faster")
    assert fast_time < brute_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
