"""
================================================================================
SOLUTION · LeetCode 621 · Task Scheduler                              [Medium]
https://leetcode.com/problems/task-scheduler/
================================================================================

THE CORE IDEA
--------------
The bottleneck is always the MOST FREQUENT task: it needs `n` units of
cooldown between every pair of its own occurrences, and everything else gets
slotted into those gaps if there's enough variety to fill them. This is a
greedy simulation — "always run whichever available task currently has the
most REMAINING occurrences" — and a max-heap is exactly the structure that
answers "what's currently most frequent?" in O(log 26) after every tick,
instead of O(26) (or O(n) naive) rescanning.

Because there are only 26 possible task letters, there's also a beautiful
closed-form shortcut (Approach 2) that avoids simulating the CPU tick by
tick entirely — both are shown below; the closed form is what interviewers
usually want, but the heap simulation is the more GENERAL technique (it
still works if you relax "26 uppercase letters" to "arbitrary task types").

================================================================================
APPROACH 0 · Simulate every unit of time literally (brute force, priced not coded)
================================================================================
Track, for each task letter, the next time unit it's allowed to run again.
At every tick, scan all task types, pick the most frequent one that's
currently allowed (cooldown satisfied), run it, or idle if none qualifies.
    Time:  O(total_time * 26) — total_time can be up to ~ n * (max_count-1) +
           26, and the linear scan over 26 letters happens on every tick.
    Space: O(26).
Correct, but does a fresh O(26) scan per tick instead of letting a heap
maintain "current max" incrementally — the difference matters more once you
generalize past exactly-26 fixed task types.

================================================================================
APPROACH 1 · Max-heap simulation with a cooldown queue ✅ (the general answer)
================================================================================
Count occurrences of each task letter. Push all nonzero counts (negated) into
a max-heap. Simulate time in a loop; each iteration represents one "cooldown
cycle" of length up to `n+1`:
  - Pop up to `n+1` of the currently most frequent tasks off the heap,
    decrement each by one, and stash them in a "cooling down" side list
    (they cannot re-enter the heap until this cycle ends, or they'd violate
    the n-cooldown against themselves).
  - After the cycle, push back any task whose remaining count is still > 0.
  - Track elapsed time: if the heap (or the cooling side list) still has work
    left after this cycle, a FULL cycle of n+1 elapsed (including idle slots
    if fewer than n+1 distinct tasks were available); if everything finished
    early inside this cycle, only the actual number of tasks run counts
    (no trailing idle needed after the very last task).

    Time:  O(total_time * log 26) — each of the (up to) 26 heap entries is
           pushed/popped O(max_count) times overall; since there are at most
           26 distinct letters, this is effectively O(total_time) with a
           tiny log-26 constant.
    Space: O(26) for the heap + cooldown buffer.

================================================================================
APPROACH 2 · Closed-form frequency math ✅ (the answer interviewers often want)
================================================================================
Let `max_count` = the highest single-letter frequency, and `num_max` = how
MANY letters tie for that highest frequency. The most frequent task(s) force
a rigid skeleton: `(max_count - 1)` full cooldown blocks of length `(n + 1)`,
plus one final row containing all `num_max` tied-for-most tasks:

    frame = (max_count - 1) * (n + 1) + num_max

If there are enough OTHER distinct tasks to fully pack every gap in that
frame, the answer is just `len(tasks)` (no idle time needed at all — the
frame is a LOWER bound, not the true bound, once you have enough variety).
Otherwise the frame itself (which already accounts for necessary idle slots)
is the answer:

    return max(len(tasks), frame)

    Time:  O(n_tasks) to count + O(26) to find max_count/num_max — no
           simulation loop at all.
    Space: O(26).

--------------------------------------------------------------------------------
STEP BY STEP TRACE — tasks = ["A","A","A","B","B","B"], n = 2 (closed form)
--------------------------------------------------------------------------------
Counts: A=3, B=3.  max_count = 3, num_max = 2 (both A and B tied at 3).

  frame = (max_count - 1) * (n + 1) + num_max
        = (3 - 1) * (2 + 1) + 2
        = 2 * 3 + 2
        = 8

  Visualize the skeleton (each row is one cooldown block of width n+1=3,
  the LAST row only needs num_max=2 slots, not a full 3):
      row 0: A B _        <- one idle slot: only 2 distinct tasks to fill 3 slots
      row 1: A B _        <- same
      row 2: A B          <- final row, exactly num_max=2 slots, no idle needed here

  Total slots drawn = 3 + 3 + 2 = 8, matching `frame`.
  len(tasks) = 6 <= 8, so the frame's idle slots are NECESSARY -> answer = 8.
  Matches expected output: 8.

  Compare tasks = ["A","A","A","A","A","A","B","C","D","E","F","G"], n=2:
  Counts: A=6 (max_count), everyone else = 1 (num_max=1, only A ties for max).
  frame = (6-1)*(2+1) + 1 = 15 + 1 = 16
  len(tasks) = 12 <= 16 -> answer = 16 (matches expected output).

  Compare tasks = ["A","A","A","B","B","B"], n=0 (no cooldown at all):
  frame = (3-1)*(0+1) + 2 = 2 + 2 = 4
  len(tasks) = 6 > frame(4) -> answer = max(6, 4) = 6 (matches expected: run
  tasks back-to-back with zero forced idle, since n=0 means no restriction).

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                          | Time                  | Space | Mutates input `tasks`? |
|--------------------------------------|-----------------------|-------|---------------------------|
| 0 · tick-by-tick scan (brute)        | O(total_time * 26)    | O(26) | No                        |
| 1 · max-heap simulation ✅ (general) | O(total_time log 26)  | O(26) | No                        |
| 2 · closed-form frequency math ✅    | O(n_tasks + 26)       | O(26) | No                        |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- n == 0: no cooldown restriction at all; the answer is simply `len(tasks)`
  (tasks can run back-to-back in any order) — both Approach 1 and 2 reduce
  to this correctly (frame collapses since `(n+1) == 1`).
- Single task type, e.g. ["A"], any n: frame = (1-1)*(n+1) + 1 = 1,
  len(tasks) = 1 -> answer 1, no idle needed for a single occurrence.
- Every task distinct (no repeats): frame is tiny (max_count=1 for all,
  num_max = 26 or however many types), len(tasks) always dominates ->
  answer = len(tasks), zero forced idle.
- n very large relative to task counts: idle time dominates; frame grows
  large and the `max(len(tasks), frame)` correctly picks the frame.
- Exactly enough variety to fill every gap with zero idle: `len(tasks) ==
  frame` exactly — `max` picks either (they're equal), still correct.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Forgetting the `max(len(tasks), frame)` step in the closed-form approach
   — the frame formula alone UNDERCOUNTS when there's enough task variety
   to fill every gap without idle (see the n=0 case and the "every task
   distinct" edge case above): the frame can come out SMALLER than
   len(tasks), which is nonsensical (you can't finish in less time than the
   number of tasks you must run), so the max is not optional.
2. Off-by-one on `(max_count - 1) * (n + 1)` — the `-1` matters: with
   `max_count` occurrences of the busiest task there are only
   `max_count - 1` GAPS between them, not `max_count` gaps; forgetting the
   `-1` overcounts by one full cooldown block.
3. In the heap simulation, re-pushing a task back into the heap for
   selection WITHIN the same cooldown cycle it just ran in — this defeats
   the entire cooldown constraint; tasks popped for the current cycle must
   sit in a separate side buffer until the cycle's `n+1` slots are consumed
   or exhausted, then rejoin the heap for the NEXT cycle.
4. Counting idle slots even when the heap (and cooldown buffer) both empty
   out before a cycle's `n+1` width is used up — the LAST batch of tasks
   never needs trailing idle (nothing runs after it), only mid-schedule
   gaps do; a naive `time += n + 1` every cycle overcounts the final cycle.
5. Using `heapq` as-is for max-heap without negating counts (see
   _TOPIC_GUIDE.md §2.1) — a very common transcription slip in this
   specific problem since the "obvious" heap use here (most frequent first)
   is inherently a max-heap query.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "Can you reconstruct the actual SCHEDULE, not just its length?" — that's
  exactly what Approach 1's simulation produces as a side effect (the order
  tasks are popped from the heap each cycle); Approach 2 only gives the
  total length, not the sequence.
- "What if tasks have different DURATIONS instead of all taking 1 unit?" —
  the closed-form frequency trick breaks (it assumes uniform unit cost);
  you'd need a more general scheduling algorithm (e.g. weighted round-robin
  or an interval-scheduling heap keyed by finish time).
- "What if there's no fixed cooldown but a general 'no two of the same
  within a window of the k most recent tasks' rule?" — this is exactly
  problem 007 (Reorganize String) generalized with a distance-k constraint
  instead of always-adjacent; same greedy-with-max-heap shape.
- "How would this change with MULTIPLE CPUs (parallel execution)?" — this
  becomes a much harder scheduling problem (akin to multiprocessor
  scheduling), generally NP-hard in full generality; heap-greedy heuristics
  can still help but no longer guarantee optimality the way this single-CPU
  case does.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 12/007 Reorganize String — the k=1 (always non-adjacent) special case of
  this exact greedy-with-max-heap shape.
- 12/002 Last Stone Weight — repeatedly consume the current max via a
  max-heap, same mechanical pattern applied to a different rule.
- 12/008 Single-Threaded CPU — another heap-driven greedy simulation, keyed
  on availability + shortest-processing-time instead of frequency.
================================================================================
"""

import heapq
import random
import time
from collections import Counter, deque
from typing import List


class Solution:
    def leastInterval(self, tasks: List[str], n: int) -> int:
        counts = Counter(tasks)
        heap = [-c for c in counts.values()]
        heapq.heapify(heap)

        elapsed = 0
        cooldown: deque = deque()  # (ready_time, -remaining_count)

        while heap or cooldown:
            elapsed += 1
            if heap:
                remaining = -heapq.heappop(heap) - 1
                if remaining > 0:
                    cooldown.append((elapsed + n, -remaining))
            if cooldown and cooldown[0][0] == elapsed:
                heapq.heappush(heap, cooldown.popleft()[1])

        return elapsed

    def leastInterval_formula(self, tasks: List[str], n: int) -> int:
        counts = Counter(tasks)
        max_count = max(counts.values())
        num_max = sum(1 for c in counts.values() if c == max_count)
        frame = (max_count - 1) * (n + 1) + num_max
        return max(len(tasks), frame)


def run_tests():
    sol = Solution()

    cases = [
        (["A", "A", "A", "B", "B", "B"], 2, 8),
        (["A", "A", "A", "B", "B", "B"], 0, 6),
        (["A", "A", "A", "A", "A", "A", "B", "C", "D", "E", "F", "G"], 2, 16),
        (["A"], 5, 1),
    ]
    for tasks, n, expected in cases:
        got_heap = sol.leastInterval(list(tasks), n)
        got_formula = sol.leastInterval_formula(list(tasks), n)
        assert got_heap == expected, f"heap: {tasks}, n={n} -> {got_heap}, want {expected}"
        assert got_formula == expected, f"formula: {tasks}, n={n} -> {got_formula}, want {expected}"

    # all distinct tasks, n large: no idle needed at all
    distinct = ["A", "B", "C", "D"]
    assert sol.leastInterval(distinct, 10) == 4
    assert sol.leastInterval_formula(distinct, 10) == 4

    # cross-check on randomized inputs
    random.seed(11)
    letters = "ABCDE"
    for _ in range(300):
        tasks = [random.choice(letters) for _ in range(random.randint(1, 20))]
        n = random.randint(0, 5)
        assert sol.leastInterval(list(tasks), n) == sol.leastInterval_formula(list(tasks), n)

    # input not mutated
    original = ["A", "A", "A", "B", "B", "B"]
    snapshot = original[:]
    sol.leastInterval(original, 2)
    assert original == snapshot, "leastInterval must not mutate its input"

    # --- measured runtime demo: heap simulation vs closed-form formula ---
    random.seed(42)
    n_tasks = 20_000
    tasks = [random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(n_tasks)]
    cooldown = 10

    t0 = time.perf_counter()
    heap_result = sol.leastInterval(tasks, cooldown)
    heap_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    formula_result = sol.leastInterval_formula(tasks, cooldown)
    formula_time = time.perf_counter() - t0

    assert heap_result == formula_result, "both approaches must agree"

    print(f"n_tasks={n_tasks}, cooldown={cooldown} (this machine, CPython):")
    print(f"  heap simulation:   {heap_time*1000:8.3f} ms")
    print(f"  closed-form math:  {formula_time*1000:8.3f} ms")
    print(f"  formula is {heap_time / formula_time:.0f}x faster (O(n) count vs O(total_time) simulation)")
    assert formula_time < heap_time, (
        "expected the O(n) closed-form formula to beat the tick-by-tick heap simulation"
    )

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
