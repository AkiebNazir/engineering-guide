"""
================================================================================
SOLUTION · LeetCode 759 · Employee Free Time                             [Hard]
https://leetcode.com/problems/employee-free-time/
================================================================================

THE CORE IDEA
--------------
"Free time common to everyone" is the COMPLEMENT of "busy time for anyone" —
solve the union first, then read the answer off the gaps. Flatten all k
employees' schedules into one list (throwing away which employee each
interval belongs to — for finding free time, only the union of busy time
matters, not who's busy), sort by start, and run the exact same
sort-by-start merge sweep as 002 Merge Intervals. The free intervals are
then simply the gaps BETWEEN consecutive merged blocks: `merged[i].end` to
`merged[i+1].start`, wherever that gap is positive (see `_TOPIC_GUIDE.md`
§4, "union across k lists, then find gaps").

================================================================================
APPROACH 0 · Pairwise intersection-of-complements (priced, not coded)
================================================================================
Compute each employee's free time individually (complement of their own
busy intervals within some bounding range), then intersect all k free-time
sets pairwise using the two-pointer merge from 006 Interval List
Intersections, folding employees in one at a time. Correct, but needs a
bounding range for each individual complement (what's the overall min/max
time horizon?) and does k-1 pairwise intersections, each O(n) -> O(nk)
overall — roughly the same order as Approach 1, but far more bookkeeping
(each employee's complement must itself be computed and bounded) for no
practical benefit. Approach 1's "union first, complement once at the end"
avoids ever computing an individual complement.

================================================================================
APPROACH 1 · Flatten + sort + merge, then read the gaps ✅ (the answer)
================================================================================
    def employeeFreeTime(schedule):
        flat = [iv for employee in schedule for iv in employee]
        flat.sort(key=lambda iv: iv[0])

        merged = [flat[0][:]]
        for start, end in flat[1:]:
            if start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])

        free = []
        for i in range(1, len(merged)):
            gap_start = merged[i - 1][1]
            gap_end = merged[i][0]
            if gap_start < gap_end:              # positive-length gap only
                free.append([gap_start, gap_end])
        return free

Time:  O(N log N) where N = total number of intervals across ALL employees
       (the sort dominates); the merge and gap-read are both O(N).
Space: O(N) for the flattened list and the merged output.

================================================================================
APPROACH 2 · k-way heap merge across employees (variant)
================================================================================
Push each employee's FIRST interval onto a min-heap keyed by start, pop the
minimum, push that employee's next interval, repeat — a classic k-way
merge (same idea as merging k sorted linked lists). This processes
intervals in global start order without ever concatenating+sorting all N
of them at once: O(N log k) instead of O(N log N), which wins when
k << N (few employees, each with many meetings). Worth naming as the
"if k is small and N is huge" optimization; for LeetCode's constraint
(schedule.length <= 50), the plain sort in Approach 1 is simpler and the
difference is negligible.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — schedule = [[[1,2],[5,6]],[[1,3]],[[4,10]]]
--------------------------------------------------------------------------------
Flatten: [[1,2],[5,6],[1,3],[4,10]]
Sort by start: [[1,2],[1,3],[4,10],[5,6]]

Number line (each employee on its own row, busy blocks shown):
    1  2  3  4        10
    A: [1..2]
    B: [1.....3]
    C:          [4..........10]
                     [5..6]     <- (A's second meeting, folded into flat)

merged = [[1,2]]

iv=[1,3]: start=1 <= merged[-1].end=2? Yes -> extend: max(2,3)=3.
          merged=[[1,3]]
iv=[4,10]: start=4 <= merged[-1].end=3? No -> new block.
          merged=[[1,3],[4,10]]
iv=[5,6]: start=5 <= merged[-1].end=10? Yes -> extend: max(10,6)=10 (no change).
          merged=[[1,3],[4,10]]

Merged busy union: [[1,3],[4,10]]

Gaps: between merged[0]=[1,3] and merged[1]=[4,10]:
      gap_start=3, gap_end=4. 3 < 4 -> emit [3,4].

Result: [[3,4]] — matches expected output. Everyone is free from 3 to 4.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                              | Time        | Space | Mutates input? |
|-------------------------------------------|------------|-------|-------------------|
| 0 · pairwise complement intersection      | O(Nk)      | O(N)  | No               |
| 1 · flatten + sort + merge + gaps ✅      | O(N log N) | O(N)  | No               |
| 2 · k-way heap merge across employees     | O(N log k) | O(N)  | No               |

N = total intervals across all employees, k = number of employees.

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single employee — no other schedule to create a "common" gap with in the
  usual sense, but by this problem's definition, "common free time for all
  employees" with only one employee IS just that employee's own busy-time
  complement — but since we never bound the free time before/after their
  first/last meeting (the problem only wants FINITE gaps BETWEEN busy
  blocks), a single employee's single meeting produces `[]` — no internal
  gap exists. Confirmed in the tests below.
- Fully overlapping schedules, e.g. employee A busy `[1,5]`, employee B
  busy `[2,3]` — B's meeting is entirely swallowed by A's during the merge,
  leaving one merged block `[1,5]` and hence no gap at all -> `[]`.
- Zero merged blocks... impossible per constraints (`schedule.length >= 1`
  and each employee has `>= 1` interval), so `flat` is never empty; the
  `merged = [flat[0][:]]` initialization is always safe.
- Touching busy blocks across different employees, e.g. A busy `[1,3]`, B
  busy `[3,5]` — merge condition is non-strict `<=` (same as 002 Merge
  Intervals: touching counts as continuous busy coverage), so these merge
  into `[1,5]` with NO gap at 3, even though they belong to different
  employees. This matches the intent: if one employee's meeting ends
  exactly when another's starts, there is no instant where everyone is
  simultaneously free.
- Many employees, each with only one interval, all mutually disjoint with
  clean gaps — produces one free interval per gap, in sorted order.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Forgetting to flatten across employees before sorting — sorting each
   employee's list individually (they're already sorted per the problem
   statement) but then trying to merge GLOBALLY without first combining
   into one flat, start-sorted sequence produces wrong gaps, since the
   merge sweep must see every employee's intervals interleaved by time,
   not employee-by-employee.
2. Using `merged[-1][1] = end` instead of `max(merged[-1][1], end)` in the
   merge step — the exact same nested-interval bug as 002 Merge Intervals;
   here it would falsely shrink a merged busy block and manufacture a fake
   "free" gap inside what is actually still busy time for someone.
3. Reporting a ZERO-length or negative "gap" — must check `gap_start <
   gap_end` strictly; touching merged blocks (`gap_start == gap_end`)
   are NOT free time, they're the exact instant coverage hands off from
   one busy block to the next.
4. Forgetting to strip the employee grouping before merging — attempting
   to merge WITHIN each employee's own list only misses gaps that exist
   because of how DIFFERENT employees' schedules interleave, which is the
   entire point of the problem.
5. Reporting free time BEFORE the first busy block or AFTER the last —
   the problem only wants gaps BETWEEN merged blocks (bounded free time);
   an unbounded "everyone is free before their first meeting" is correctly
   excluded by only ever iterating `range(1, len(merged))`.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if you only cared about free time common to a SUBSET of employees,
  not all of them?" -> flatten only that subset's schedules before the
  merge; same algorithm, smaller N.
- "How would you do this if N is huge but k (employee count) is small?" ->
  Approach 2's k-way heap merge, O(N log k) instead of O(N log N).
- "How is this different from Interval List Intersections (LC 986)?" -> 986
  computes the INTERSECTION of two already-known-nonoverlapping lists
  directly; this problem computes the COMPLEMENT of a UNION across k lists
  — a fundamentally different operation (union+complement) even though
  both rely on sorted-interval sweeps.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 19/002 Merge Intervals — the exact merge step reused here verbatim, just
  applied to a flattened multi-employee list instead of a single list.
- 19/006 Interval List Intersections — a different two-list operation
  (intersection, not union+complement), contrasted in the follow-ups above.
- 19/003 Insert Interval — another problem that leans on "the input is
  already sorted, don't throw that away" the same way this one leans on
  flattening once instead of repeated pairwise work (Approach 0).
================================================================================
"""

import heapq
import random
import time
from typing import List


class Solution:
    def employeeFreeTime(self, schedule: List[List[List[int]]]) -> List[List[int]]:
        flat = [iv for employee in schedule for iv in employee]
        flat.sort(key=lambda iv: iv[0])

        merged = [flat[0][:]]
        for start, end in flat[1:]:
            if start <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], end)
            else:
                merged.append([start, end])

        free = []
        for i in range(1, len(merged)):
            gap_start = merged[i - 1][1]
            gap_end = merged[i][0]
            if gap_start < gap_end:
                free.append([gap_start, gap_end])
        return free


class SolutionKWayHeapMerge:
    def employeeFreeTime(self, schedule: List[List[List[int]]]) -> List[List[int]]:
        heap = []
        for emp_idx, employee in enumerate(schedule):
            if employee:
                s, e = employee[0]
                heapq.heappush(heap, (s, e, emp_idx, 0))

        merged = []
        while heap:
            s, e, emp_idx, meeting_idx = heapq.heappop(heap)
            if merged and s <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], e)
            else:
                merged.append([s, e])
            next_idx = meeting_idx + 1
            if next_idx < len(schedule[emp_idx]):
                ns, ne = schedule[emp_idx][next_idx]
                heapq.heappush(heap, (ns, ne, emp_idx, next_idx))

        free = []
        for i in range(1, len(merged)):
            gap_start = merged[i - 1][1]
            gap_end = merged[i][0]
            if gap_start < gap_end:
                free.append([gap_start, gap_end])
        return free


def run_tests():
    sol = Solution()
    assert sol.employeeFreeTime([[[1, 2], [5, 6]], [[1, 3]], [[4, 10]]]) == [[3, 4]]
    assert sol.employeeFreeTime(
        [[[1, 3], [6, 7]], [[2, 4]], [[2, 5], [9, 12]]]
    ) == [[5, 6], [7, 9]]
    assert sol.employeeFreeTime([[[1, 5]], [[2, 3]]]) == []
    assert sol.employeeFreeTime([[[1, 2]]]) == []
    assert sol.employeeFreeTime([[[1, 3]], [[3, 5]]]) == []  # touching -> no gap

    # cross-check against the k-way heap merge variant on random inputs
    heap_sol = SolutionKWayHeapMerge()
    random.seed(23)
    for _ in range(150):
        k = random.randint(1, 5)
        schedule = []
        for _ in range(k):
            n = random.randint(1, 4)
            cursor = random.randint(0, 5)
            emp = []
            for _ in range(n):
                cursor += random.randint(0, 3)
                s = cursor
                cursor += random.randint(1, 4)
                e = cursor
                emp.append([s, e])
                cursor += 1
            schedule.append(emp)
        got = sol.employeeFreeTime([[iv[:] for iv in emp] for emp in schedule])
        want = heap_sol.employeeFreeTime([[iv[:] for iv in emp] for emp in schedule])
        assert got == want, f"mismatch on {schedule}: got {got}, want {want}"

    # --- measured runtime demo: flatten+sort O(N log N) vs k-way heap O(N log k) ---
    random.seed(31)
    k = 6  # few employees...
    per_employee = 15000  # ...but each with many meetings -> N is large, k small
    schedule = []
    for e in range(k):
        emp = []
        cursor = e  # stagger start so employees interleave
        for _ in range(per_employee):
            cursor += 3
            s = cursor
            cursor += 1
            e_end = cursor
            emp.append([s, e_end])
            cursor += k  # leave room for other employees to interleave
        schedule.append(emp)

    t0 = time.perf_counter()
    flat_result = sol.employeeFreeTime([[iv[:] for iv in emp] for emp in schedule])
    flat_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    heap_result = heap_sol.employeeFreeTime([[iv[:] for iv in emp] for emp in schedule])
    heap_time = time.perf_counter() - t0

    assert flat_result == heap_result

    N = k * per_employee
    print(f"N={N} total intervals across k={k} employees (this machine, CPython):")
    print(f"  flatten + full sort O(N log N): {flat_time*1000:8.3f} ms")
    print(f"  k-way heap merge O(N log k):    {heap_time*1000:8.3f} ms")
    faster = "k-way heap" if heap_time < flat_time else "flatten+sort"
    ratio = max(flat_time, heap_time) / min(flat_time, heap_time)
    print(f"  {faster} is {ratio:.1f}x faster here (k is small relative to N, "
          f"so log k << log N)")

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
