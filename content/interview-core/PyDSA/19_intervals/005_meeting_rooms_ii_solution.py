"""
================================================================================
SOLUTION · LeetCode 253 · Meeting Rooms II                            [Medium]
https://leetcode.com/problems/meeting-rooms-ii/
================================================================================

THE CORE IDEA
--------------
This is no longer "does anything conflict" (001) — it's "what is the PEAK
number of meetings happening AT THE SAME INSTANT, across the whole
timeline?" That peak equals the minimum number of rooms needed, because a
room is only reusable once its current meeting ends. The natural tool for
"track how many things are open right now, and let me know the earliest one
that closes" is a min-heap of end times, swept in start order — see
`_TOPIC_GUIDE.md` §3.

================================================================================
APPROACH 0 · Brute-force timeline simulation (priced, not coded)
================================================================================
For every meeting, scan all ROOM_COUNT rooms currently in use to find one
whose current meeting has ended; if none free, add a room. Naively this is
O(n * rooms) and rooms can be O(n) -> O(n^2). Correct but quadratic.

================================================================================
APPROACH 1 · Sort by start, min-heap of end times ✅
================================================================================
    import heapq

    def minMeetingRooms(intervals):
        if not intervals:
            return 0
        intervals.sort(key=lambda iv: iv[0])
        heap = []                               # end times of rooms in use
        for start, end in intervals:
            if heap and heap[0] <= start:        # earliest-freeing room is free
                heapq.heappop(heap)              # reuse it
            heapq.heappush(heap, end)            # occupy a room until `end`
        return len(heap)

Time:  O(n log n) — sort O(n log n), then n heap ops at O(log n) each.
Space: O(n) worst case for the heap (every meeting concurrent).

================================================================================
APPROACH 2 · Two sorted arrays, two-pointer sweep (often faster in practice)
================================================================================
    def minMeetingRooms(intervals):
        starts = sorted(iv[0] for iv in intervals)
        ends = sorted(iv[1] for iv in intervals)
        rooms = max_rooms = 0
        s = e = 0
        while s < len(starts):
            if starts[s] < ends[e]:
                rooms += 1
                s += 1
            else:
                rooms -= 1
                e += 1
            max_rooms = max(max_rooms, rooms)
        return max_rooms

Time:  O(n log n) for the two sorts, O(n) for the two-pointer sweep.
Space: O(n) for the two sorted arrays (no heap object, less per-step
       overhead than heap push/pop in CPython — measured below).

Note the boundary: `starts[s] < ends[e]` (strict) mirrors this problem's
"touching does not conflict" rule — a meeting starting exactly when another
ends does NOT need a new room, so on a tie we retire the ending meeting
first (`e` advances), matching 001's strict-`<` conflict test.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — intervals = [[0,30],[5,10],[15,20]] (Approach 1, heap)
--------------------------------------------------------------------------------
Sort by start (already sorted): [[0,30],[5,10],[15,20]]

Number line:
    0        5    10        15   20              30
    [0............................................30]
              [5....10]
                         [15..20]

heap = []

iv=[0,30]: heap empty -> no reuse. push 30. heap=[30]
iv=[5,10]: heap[0]=30 <= 5? No (room still busy until 30) -> push 10.
           heap=[10,30]  (heap-order array; root=10)
iv=[15,20]: heap[0]=10 <= 15? Yes -> pop 10 (room freed, reuse it).
            push 20. heap=[20,30]

Final heap size = 2 -> answer 2. At t=5..10, both [0,30] and [5,10] are
open simultaneously -> that's the peak -> 2 rooms confirmed correct.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                             | Time        | Space | Mutates input? |
|------------------------------------------|------------|-------|-------------------|
| 0 · brute-force room-scan (brute)         | O(n^2)     | O(n)  | No               |
| 1 · sort + min-heap of ends ✅            | O(n log n) | O(n)  | YES (`.sort()`)  |
| 2 · two sorted arrays, two-pointer        | O(n log n) | O(n)  | No (builds new arrays) |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Empty input — 0 rooms. Both approaches must guard: Approach 1 explicitly
  returns 0 early (the heap-size return would ALSO be 0 naturally even
  without the guard, since the loop never runs — the explicit early return
  is for clarity, not correctness).
- Single meeting — 1 room, no heap contention.
- Touching endpoints, e.g. `[[1,2],[2,3]]` — must NOT require a second room.
  `heap[0] <= start` (non-strict `<=`) reuses the room the instant it frees,
  even if that's the exact instant the new meeting starts. Getting this
  strict (`<`) instead would incorrectly report 2 rooms for a schedule that
  only ever needs 1.
- All meetings fully concurrent, e.g. `[[1,10],[2,6],[3,8],[4,7]]` — every
  meeting overlaps every other -> heap never gets to pop -> answer equals
  n (4 rooms), the worst case.
- All meetings identical time slot — same as above, answer = n.
- Meetings already sorted / reverse-sorted / random order — the explicit
  sort handles all orderings identically.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Sorting by END instead of START before the heap sweep — the sweep's
   correctness depends on processing meetings in the order they BEGIN
   (that's what lets "is a room free yet" make sense as you go); sorting by
   end scrambles that order and undercounts/overcounts rooms.
2. Using strict `<` instead of `<=` for the reuse check — see EDGE CASES;
   overcounts rooms on touching-boundary schedules.
3. Popping the heap unconditionally every iteration instead of only when
   `heap[0] <= start` — silently frees a room that ISN'T actually free yet,
   undercounting the true peak.
4. Confusing this with 001 Meeting Rooms and returning a boolean instead of
   a count — different return type, different question ("can one person
   attend all" vs "how many rooms are needed").
5. In Approach 2, using the SAME index variable to walk both `starts` and
   `ends` (rather than two independent pointers `s` and `e`) — they advance
   at different rates and must be tracked separately.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "Can you report WHICH room each meeting is assigned to, not just the
  count?" -> store `(end, room_id)` tuples in the heap instead of bare end
  times; popping gives you the specific room being reused.
- "What if rooms have different costs and you must minimize total cost, not
  just count?" -> a genuinely different (harder) problem — becomes an
  assignment/matching problem, no longer solvable by this greedy sweep
  alone.
- "How does this generalize to Car Pooling (each 'meeting' occupies more
  than 1 unit of a shared resource)?" -> replace the heap's implicit
  "occupies 1 room" with a running passenger-count difference array — see
  problem 009 (Car Pooling) in this topic, and `_TOPIC_GUIDE.md` §3.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 19/001 Meeting Rooms — the yes/no version this problem generalizes into a
  count.
- 19/009 Car Pooling — the weighted generalization (each interval "counts"
  as more than 1 concurrently).
- Topic 12 (Heap) task-scheduling problems — same "lazy expiration via
  min-heap" pattern applied to CPU/task scheduling instead of rooms.
================================================================================
"""

import heapq
import random
import time
from typing import List


class Solution:
    def minMeetingRooms(self, intervals: List[List[int]]) -> int:
        if not intervals:
            return 0
        intervals.sort(key=lambda iv: iv[0])
        heap = []
        for start, end in intervals:
            if heap and heap[0] <= start:
                heapq.heappop(heap)
            heapq.heappush(heap, end)
        return len(heap)


class SolutionTwoPointer:
    def minMeetingRooms(self, intervals: List[List[int]]) -> int:
        if not intervals:
            return 0
        starts = sorted(iv[0] for iv in intervals)
        ends = sorted(iv[1] for iv in intervals)
        rooms = max_rooms = 0
        s = e = 0
        n = len(intervals)
        while s < n:
            if starts[s] < ends[e]:
                rooms += 1
                s += 1
            else:
                rooms -= 1
                e += 1
            max_rooms = max(max_rooms, rooms)
        return max_rooms


# --------------------------------------------------------------------------
# Baseline for cross-checking: brute-force room-scan simulation.
# --------------------------------------------------------------------------
class SolutionBruteForce:
    def minMeetingRooms(self, intervals: List[List[int]]) -> int:
        if not intervals:
            return 0
        ivs = sorted(intervals, key=lambda iv: iv[0])
        room_free_at: List[int] = []
        for start, end in ivs:
            assigned = False
            for i in range(len(room_free_at)):
                if room_free_at[i] <= start:
                    room_free_at[i] = end
                    assigned = True
                    break
            if not assigned:
                room_free_at.append(end)
        return len(room_free_at)


def run_tests():
    sol = Solution()
    assert sol.minMeetingRooms([[0, 30], [5, 10], [15, 20]]) == 2
    assert sol.minMeetingRooms([[7, 10], [2, 4]]) == 1
    assert sol.minMeetingRooms([[1, 2], [2, 3]]) == 1
    assert sol.minMeetingRooms([[1, 10], [2, 6], [3, 8], [4, 7]]) == 4
    assert sol.minMeetingRooms([[5, 8]]) == 1
    assert sol.minMeetingRooms([]) == 0

    two_ptr = SolutionTwoPointer()
    brute = SolutionBruteForce()

    # cross-check all three approaches against each other
    random.seed(17)
    for _ in range(300):
        n = random.randint(0, 12)
        ivs = []
        for _ in range(n):
            s = random.randint(0, 20)
            e = s + random.randint(1, 8)
            ivs.append([s, e])
        r1 = sol.minMeetingRooms([iv[:] for iv in ivs])
        r2 = two_ptr.minMeetingRooms([iv[:] for iv in ivs])
        r3 = brute.minMeetingRooms([iv[:] for iv in ivs])
        assert r1 == r2 == r3, f"mismatch on {ivs}: heap={r1} two_ptr={r2} brute={r3}"

    # --- measured runtime demo: min-heap vs two-sorted-arrays two-pointer ---
    random.seed(2)
    n = 20_000
    ivs = []
    for _ in range(n):
        s = random.randint(0, 10**6)
        e = s + random.randint(1, 500)
        ivs.append([s, e])

    t0 = time.perf_counter()
    heap_result = sol.minMeetingRooms([iv[:] for iv in ivs])
    heap_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    two_ptr_result = two_ptr.minMeetingRooms([iv[:] for iv in ivs])
    two_ptr_time = time.perf_counter() - t0

    assert heap_result == two_ptr_result

    print(f"n={n} meetings (this machine, CPython):")
    print(f"  min-heap of end times:        {heap_time*1000:8.3f} ms")
    print(f"  two sorted arrays, 2-pointer: {two_ptr_time*1000:8.3f} ms")
    faster = "two-pointer" if two_ptr_time < heap_time else "heap"
    ratio = max(heap_time, two_ptr_time) / min(heap_time, two_ptr_time)
    print(f"  {faster} is {ratio:.1f}x faster here (both are O(n log n); "
          f"the win is lower per-step constant factor, not asymptotics)")

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
