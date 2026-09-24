"""
================================================================================
SOLUTION · LeetCode 1834 · Single-Threaded CPU                        [Medium]
https://leetcode.com/problems/single-threaded-cpu/
================================================================================

THE CORE IDEA
--------------
The CPU's rule ("of the tasks currently AVAILABLE, run the one with the
shortest processing time, ties broken by original index") is a min-heap
query answered repeatedly over a growing/shrinking AVAILABLE set. Sort tasks
by `enqueueTime` once so you can advance a pointer through "who has become
available by now" in order, and maintain a min-heap of `(processingTime,
originalIndex)` for everyone currently available but not yet run.

The one non-obvious wrinkle: when the CPU goes idle because NOTHING is
available yet, you must jump the clock forward to the next task's
`enqueueTime` rather than advancing one unit at a time — this problem's
`enqueueTime` values can be up to 10^9 apart, so tick-by-tick simulation
(Approach 0) would time out.

================================================================================
APPROACH 0 · Tick-by-tick simulation (brute force, priced not coded)
================================================================================
Advance a clock by 1 each step; at every tick, scan all tasks for ones whose
`enqueueTime <= clock` and not yet run, pick the shortest (ties by index).
    Time:  O(max_enqueue_time * n) in the worst case — with enqueueTime up
           to 10^9, this is astronomically infeasible even for small n.
    Space: O(n).
Correct in principle, but the huge time-value range makes this the canonical
"don't simulate real time unit-by-unit, jump to the next EVENT" lesson.

================================================================================
APPROACH 1 · Sort by enqueueTime + min-heap of available tasks ✅ (the answer)
================================================================================
  1. Sort tasks (keeping original indices) by `enqueueTime`.
  2. Maintain `time` = current CPU clock, a pointer `i` into the sorted
     tasks, and a min-heap of `(processingTime, originalIndex)` for tasks
     that have become available (`enqueueTime <= time`) but haven't run yet.
  3. Loop: push every task whose `enqueueTime <= time` into the heap
     (advancing `i`). If the heap is empty (CPU idle, nothing available
     yet), JUMP `time` forward to the next unprocessed task's `enqueueTime`
     instead of ticking — this is the key optimization. Otherwise pop the
     heap's min `(processingTime, idx)`, append `idx` to the result, and
     advance `time += processingTime`.

    Time:  O(n log n) for the sort + O(n log n) for n heap push/pop pairs =
           O(n log n) overall.
    Space: O(n) for the heap + sorted order + result.

================================================================================
APPROACH 2 · Variants worth naming
================================================================================
- Skip the explicit index-jump and instead push a SENTINEL/no-op "idle"
  entry with a large processing time when the heap is empty — works but is
  a less direct way to express "jump to the next enqueue event"; the direct
  jump in Approach 1 is clearer and avoids fabricating fake tasks.
- Using a balanced BST / sorted-list structure instead of a heap for the
  available set would also work (O(log n) insert/extract-min) but `heapq`
  is the idiomatic and simplest tool here since we never need to query
  anything except the current min.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — tasks = [[1,2],[2,4],[3,2],[4,1]]
--------------------------------------------------------------------------------
Sorted by enqueueTime (already sorted here): idx0=[1,2], idx1=[2,4],
idx2=[3,2], idx3=[4,1]

  time=1, i=0: push tasks with enqueueTime<=1 -> push (2, 0) [idx0, proc=2]
               i=1. heap=[(2,0)]. Not empty -> pop (2,0) -> run idx0.
               result=[0]. time = 1 + 2 = 3.

  time=3, i=1: push tasks with enqueueTime<=3 -> push (4,1) [idx1], then
               push (2,2) [idx2]. i=3. heap=[(2,2),(4,1)] (min-heap root=2).
               pop (2,2) -> run idx2. result=[0,2]. time = 3 + 2 = 5.

  time=5, i=3: push tasks with enqueueTime<=5 -> push (1,3) [idx3]. i=4.
               heap=[(1,3),(4,1)] (root=1). pop (1,3) -> run idx3.
               result=[0,2,3]. time = 5 + 1 = 6.

  time=6, i=4 (all pushed already): heap=[(4,1)]. pop (4,1) -> run idx1.
               result=[0,2,3,1]. time = 6 + 4 = 10.

  i==len(tasks), heap empty -> done. result = [0,2,3,1]. Matches expected
  output.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                                | Time              | Space | Mutates input `tasks`? |
|--------------------------------------------|-------------------|-------|---------------------------|
| 0 · tick-by-tick simulation (brute)         | O(max_time * n)   | O(n)  | No                        |
| 1 · sort + min-heap of available tasks ✅   | O(n log n)        | O(n)  | No — sorts a copy of indices, not `tasks` itself |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single task: `[[5,2]]` -> immediately available at time=5, no heap
  contention, result = [0].
- All tasks share the same enqueueTime: heap ties are broken purely by
  processing time, then by index (the tuple's natural second-element
  comparison) — see the example with all `enqueueTime=7` in the question
  file.
- A big gap in enqueue times (CPU goes idle): e.g. tasks enqueued at t=1 and
  t=1000 with nothing in between — the time-jump in Approach 1 is what
  makes this efficient; without it (Approach 0) this single gap alone could
  cost 999 wasted ticks.
- Two tasks with identical processingTime available simultaneously: the
  tuple `(processingTime, originalIndex)` tiebreaks correctly by index
  without extra code, since tuple comparison falls through to the second
  element automatically once the first ties.
- Tasks not given in enqueueTime order in the input: the sort step handles
  this; the ORIGINAL index must be preserved through the sort (zip with
  `range(n)` before sorting, never assume post-sort position == original
  index).

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Ticking the clock forward one unit at a time when the CPU is idle instead
   of jumping straight to the next task's `enqueueTime` — passes tiny toy
   tests, times out on inputs with `enqueueTime` values spread across the
   full 10^9 range.
2. Losing track of the ORIGINAL index after sorting by enqueueTime — the
   answer must report indices into the INPUT array, not positions in the
   sorted order; forgetting to carry `(enqueueTime, processingTime,
   originalIndex)` triples (or sorting `list(enumerate(tasks))`) through the
   sort silently returns the wrong index sequence.
3. Pushing ALL tasks into the heap up front regardless of `enqueueTime` —
   this violates the "only currently available tasks are eligible" rule;
   a task enqueued at t=100 must not be selectable at t=5 just because it
   has the shortest processing time globally.
4. Off-by-one on the "push while enqueueTime <= time" condition — using
   strict `<` instead of `<=` wrongly excludes a task that becomes
   available at EXACTLY the current time.
5. Forgetting the tiebreak is on ORIGINAL index, not on processing time
   alone or on sorted-array position — pushing `(processingTime,)` alone
   into the heap without an index tiebreaker either loses index information
   entirely or (if tasks happen to be objects/lists) risks the same
   `TypeError`-on-tie problem covered in problem 003's Common Mistakes.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if tasks can be PREEMPTED (interrupted mid-run by a shorter task
  that just arrived)?" — a fundamentally different scheduling problem
  (shortest-remaining-time-first), needs re-evaluating the heap at every
  new arrival event, not just at completion events.
- "What if there are MULTIPLE CPUs?" — becomes a multiprocessor scheduling
  problem; a common heuristic is one heap of available tasks shared across
  a heap of "CPU free-at" times (a two-heap or heap-of-heaps design).
- "How would you support tasks with PRIORITY in addition to processing
  time?" — extend the tuple to `(priority, processingTime, originalIndex)`
  or whatever tiebreak order the spec requires — the heap mechanism is
  unchanged, only the sort key shape grows.
- "Can this be done without sorting first, in a true streaming setting
  where you don't know all enqueueTimes up front?" — no, you fundamentally
  need to know which tasks arrive when to correctly decide idle-jump
  targets; a true live stream would need a different data feed (e.g. a
  second heap of "not yet arrived" tasks keyed by enqueueTime, replacing
  the sorted-array pointer with a heap pop).

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 12/005 Task Scheduler — also a heap-driven greedy simulation, but keyed
  on remaining COUNT rather than availability + shortest-processing-time.
- 12/010 Minimum Interval to Include Each Query — same "sort + min-heap of
  currently-relevant candidates, advanced by a pointer" shape, applied to
  interval containment instead of task scheduling.
- LC 253 Meeting Rooms II (topic 19, Intervals) — another sort + heap
  pattern for tracking "currently active" resources over time.
================================================================================
"""

import heapq
import random
import time as time_module
from typing import List


class Solution:
    def getOrder(self, tasks: List[List[int]]) -> List[int]:
        n = len(tasks)
        # (enqueueTime, processingTime, originalIndex), sorted by enqueueTime
        order = sorted(range(n), key=lambda i: tasks[i][0])

        result = []
        heap: List[tuple] = []   # (processingTime, originalIndex)
        clock = 0
        i = 0

        while len(result) < n:
            # admit every task that has become available by `clock`
            while i < n and tasks[order[i]][0] <= clock:
                idx = order[i]
                heapq.heappush(heap, (tasks[idx][1], idx))
                i += 1

            if not heap:
                # CPU idle: jump straight to the next task's enqueueTime
                clock = tasks[order[i]][0]
                continue

            proc_time, idx = heapq.heappop(heap)
            result.append(idx)
            clock += proc_time

        return result


def run_tests():
    sol = Solution()

    assert sol.getOrder([[1, 2], [2, 4], [3, 2], [4, 1]]) == [0, 2, 3, 1]
    assert sol.getOrder([[7, 10], [7, 12], [7, 5], [7, 4], [7, 2]]) == [4, 3, 2, 0, 1]
    assert sol.getOrder([[1, 1], [2, 2], [3, 3]]) == [0, 1, 2]
    assert sol.getOrder([[5, 2]]) == [0]

    # unsorted enqueueTime input: original index must be preserved correctly
    assert sol.getOrder([[3, 1], [1, 1], [2, 1]]) == [1, 2, 0]

    # big idle gap between task arrivals: must not hang or misbehave
    assert sol.getOrder([[1, 1], [1000000000, 1]]) == [0, 1]

    # input not mutated
    original = [[1, 2], [2, 4], [3, 2], [4, 1]]
    snapshot = [row[:] for row in original]
    sol.getOrder(original)
    assert original == snapshot, "getOrder must not mutate its input"

    # cross-check against a brute-force tick simulation on small randomized cases
    def brute_force(tasks):
        n = len(tasks)
        done = [False] * n
        t = 0
        result = []
        remaining = n
        while remaining > 0:
            available = [i for i in range(n) if not done[i] and tasks[i][0] <= t]
            if not available:
                t = min(tasks[i][0] for i in range(n) if not done[i])
                continue
            best = min(available, key=lambda i: (tasks[i][1], i))
            done[best] = True
            result.append(best)
            t += tasks[best][1]
            remaining -= 1
        return result

    random.seed(9)
    for _ in range(200):
        n = random.randint(1, 8)
        tasks = [[random.randint(1, 15), random.randint(1, 10)] for _ in range(n)]
        assert sol.getOrder([row[:] for row in tasks]) == brute_force(tasks)

    # --- measured runtime demo: idle-jump heap approach vs tick-by-tick brute force ---
    random.seed(42)
    n = 300
    tasks = [[random.randint(1, 10**6), random.randint(1, 100)] for _ in range(n)]

    t0 = time_module.perf_counter()
    fast_result = sol.getOrder([row[:] for row in tasks])
    fast_time = time_module.perf_counter() - t0

    t0 = time_module.perf_counter()
    slow_result = brute_force(tasks)
    slow_time = time_module.perf_counter() - t0

    assert fast_result == slow_result, "both approaches must agree"

    print(f"n={n} tasks, enqueueTime up to 10^6 (this machine, CPython):")
    print(f"  sort + min-heap (idle-jump): {fast_time*1000:8.2f} ms")
    print(f"  tick-by-tick brute force:    {slow_time*1000:8.2f} ms")
    print(f"  heap approach is {slow_time / fast_time:.0f}x faster")
    assert fast_time < slow_time, (
        "expected the idle-jumping heap approach to crush tick-by-tick simulation "
        "once enqueueTime values are spread out"
    )

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
