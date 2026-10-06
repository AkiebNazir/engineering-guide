"""
================================================================================
SOLUTION · LeetCode 1046 · Last Stone Weight                            [Easy]
https://leetcode.com/problems/last-stone-weight/
================================================================================

THE CORE IDEA
--------------
Every step of the simulation asks the same question: "what are the two
LARGEST stones right now?" That is exactly what a max-heap answers in O(log
n) per pop, versus O(n log n) (or O(n) with insertion into a kept-sorted
list) if you re-derive the max from scratch every step. `heapq` is a
min-heap (see _TOPIC_GUIDE.md §2.1), so we negate weights on the way in and
negate back on the way out — the standard max-heap-via-min-heap trick.

================================================================================
APPROACH 0 · Re-sort the list every round (brute force, priced not coded)
================================================================================
Sort `stones` descending, pop the first two, smash, insert the remainder back
in sorted position (or just append and re-sort next round). Each round costs
O(n log n) for a full sort (or O(n) for `bisect.insort`), and there are up to
n-1 rounds -> O(n^2 log n) worst case with full re-sorts, O(n^2) with
`bisect.insort`. Correct, and for LeetCode's n <= 30 constraint it would even
pass — but it does needless work: we only ever need the top TWO stones, never
the full order of the rest.

================================================================================
APPROACH 1 · Max-heap simulation ✅ (the answer)
================================================================================
    import heapq

    def lastStoneWeight(stones):
        heap = [-w for w in stones]
        heapq.heapify(heap)                     # O(n)
        while len(heap) > 1:
            y = -heapq.heappop(heap)             # heaviest
            x = -heapq.heappop(heap)             # 2nd heaviest
            if y != x:
                heapq.heappush(heap, -(y - x))   # smashed remainder, still negated
        return -heap[0] if heap else 0

Time:  O(n) heapify + O(n) rounds * O(log n) per round = O(n log n) overall.
Space: O(n) for the heap (one negated copy of `stones`).

================================================================================
APPROACH 2 · Variants worth naming
================================================================================
- Sorted-array-with-binary-insert (`bisect.insort`): pop the two ends,
  `bisect.insort` the remainder back in. O(n) per round (list shift) instead
  of O(log n) -> worse asymptotically than the heap, but for n <= 30 the
  constant-factor difference is invisible; only matters as n grows.
- If stones arrive as an unbounded STREAM (smash-as-you-go, not a fixed
  array), the heap approach generalizes directly — same idea as problem 001
  in this topic — while re-sorting from scratch does not.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — stones = [2, 7, 4, 1, 8, 1]
--------------------------------------------------------------------------------
Negate everything, heapify (min-heap of negatives == max-heap of originals):
  originals: [2, 7, 4, 1, 8, 1]
  negated:   [-2,-7,-4,-1,-8,-1]  -> heapify -> min-heap array (one valid
                                      layout): [-8, -7, -4, -1, -2, -1]
  (root = -8, i.e. heaviest original stone is 8 -- correct)

Round 1: pop -8 (y=8), pop -7 (x=7). y != x -> smash: 8-7=1, push -1.
  heap now holds negated {4,1,2,1,1} -> originals remaining: [4,1,2,1,1]

Round 2: pop largest two of {4,1,2,1,1} -> y=4, x=2. y != x -> push -(4-2)=-2.
  remaining originals: [2,1,1,1]

Round 3: pop largest two of {2,1,1,1} -> y=2, x=1. y != x -> push -(2-1)=-1.
  remaining originals: [1,1,1]

Round 4: pop largest two of {1,1,1} -> y=1, x=1. y == x -> destroy both,
  push nothing.
  remaining originals: [1]

heap has 1 element left -> -heap[0] = 1.  Matches expected output: 1.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                       | Time            | Space | Mutates input `stones`? |
|---------------------------------|-----------------|-------|---------------------------|
| 0 · re-sort every round (brute) | O(n^2 log n)    | O(n)  | No (builds a new list)   |
| 1 · max-heap (negated) ✅       | O(n log n)      | O(n)  | No — negated copy, `stones` untouched |
| 2 · bisect.insort per round     | O(n^2)          | O(n)  | No (builds a new list)   |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single stone: `stones = [x]` — loop never runs (len(heap) == 1), returns x
  directly; matches "at most one stone left" framing.
- All stones destroy to zero: e.g. [1,1] -> 0, or a chain that ends exactly
  even; `heap` becomes empty, `heap[0]` would IndexError, so the code must
  guard with `if heap else 0`.
- All equal stones with odd count: e.g. [3,3,3] -> pairs annihilate two at a
  time, one 3 always survives to the next round eventually landing as the
  answer (3 in this case) — no special-casing needed, the loop naturally
  handles it.
- Two equal stones: [2,2] -> single round, both destroyed, heap empty -> 0.
- Max weight values (1000) with max count (30): heap depth is tiny
  (log2(30) ~ 5), no overflow concerns in Python (arbitrary precision ints).

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Forgetting to re-negate when computing the smashed remainder — pushing
   `y - x` (positive) into a heap that is supposed to hold negatives breaks
   the invariant silently; the heap still "works" but starts returning the
   SMALLEST remaining original weight instead of the largest on the next
   pop, corrupting every subsequent round without raising an error.
2. Not guarding the empty-heap case at the end — `-heap[0]` on an empty list
   raises `IndexError`; the problem explicitly allows "no stones left" (0).
3. Popping only ONE stone per round instead of two, or comparing without
   popping first (e.g. peeking `heap[0]` and `heap[1]` — index 1 is NOT
   guaranteed to be the second-largest in a heap's array layout, only the
   smaller of the root's two children; see _TOPIC_GUIDE.md §1.1 on the weak
   sibling-order guarantee).
4. Re-inserting a zero-difference remainder — when `y == x`, nothing should
   be pushed back (both stones are destroyed); pushing `-(y-x)` = `-0` when
   the intent was "destroyed" would (harmlessly, since -0==0, but wastefully)
   add a phantom zero-weight stone that must then be smashed away later.
5. Using a plain list + `max()`/`remove()` each round — `list.remove` is
   O(n) AND only removes the first matching value, silently wrong if
   duplicate weights exist and you meant to remove one specific occurrence
   (say, the just-computed remainder rather than an equal-weight original).

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if stones arrive as a live stream instead of a fixed array?" — same
  max-heap; push new stones in as they arrive (negated), smash pairs
  whenever >= 2 are available. Same amortized O(log n) per event.
- "What if you smash the two SMALLEST stones instead?" — swap to a plain
  min-heap (no negation needed) and the same loop structure applies.
- "What's the theoretical lower bound here?" — you must observe every stone
  at least once, so Omega(n); the heap approach is O(n log n), matching the
  brute-force sort's asymptotics but doing meaningfully less real work per
  round in practice (see the runtime demo below).

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 12/001 Kth Largest Element in a Stream — same negate-for-max-heap trick,
  different query (running kth-largest instead of iterative pairwise smash).
- 12/005 Task Scheduler — a different "repeatedly take the current max(es)"
  greedy-with-heap simulation.
- 12/008 Single-Threaded CPU — heap-driven simulation of a process queue.
================================================================================
"""

import heapq
import random
import time
from typing import List


class Solution:
    def lastStoneWeight(self, stones: List[int]) -> int:
        heap = [-w for w in stones]      # negate: min-heap of negatives == max-heap
        heapq.heapify(heap)              # O(n)
        while len(heap) > 1:
            y = -heapq.heappop(heap)     # heaviest
            x = -heapq.heappop(heap)     # 2nd heaviest
            if y != x:
                heapq.heappush(heap, -(y - x))
        return -heap[0] if heap else 0


# --------------------------------------------------------------------------
# Baseline for the runtime demo: re-sort the whole remaining list every round.
# --------------------------------------------------------------------------
class SolutionSortEveryRound:
    def lastStoneWeight(self, stones: List[int]) -> int:
        remaining = sorted(stones, reverse=True)
        while len(remaining) > 1:
            y = remaining.pop(0)
            x = remaining.pop(0)
            if y != x:
                remaining.append(y - x)
            remaining.sort(reverse=True)
        return remaining[0] if remaining else 0


def run_tests():
    sol = Solution()
    assert sol.lastStoneWeight([2, 7, 4, 1, 8, 1]) == 1
    assert sol.lastStoneWeight([1]) == 1
    assert sol.lastStoneWeight([1, 1]) == 0
    assert sol.lastStoneWeight([2, 2]) == 0
    assert sol.lastStoneWeight([1, 3]) == 2
    assert sol.lastStoneWeight([10, 4, 2, 10]) == 2

    # input not mutated
    original = [2, 7, 4, 1, 8, 1]
    snapshot = original[:]
    sol.lastStoneWeight(original)
    assert original == snapshot, "lastStoneWeight must not mutate its input"

    # cross-check against the brute-force baseline on random inputs
    random.seed(7)
    sort_sol = SolutionSortEveryRound()
    for _ in range(200):
        n = random.randint(1, 20)
        stones = [random.randint(1, 50) for _ in range(n)]
        assert sol.lastStoneWeight(stones[:]) == sort_sol.lastStoneWeight(stones[:])

    # --- measured runtime demo: max-heap vs re-sort-every-round ---
    random.seed(42)
    n = 4000
    stones = [random.randint(1, 10**6) for _ in range(n)]

    t0 = time.perf_counter()
    heap_result = sol.lastStoneWeight(stones[:])
    heap_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    sort_result = sort_sol.lastStoneWeight(stones[:])
    sort_time = time.perf_counter() - t0

    assert heap_result == sort_result, "both approaches must agree"

    print(f"n={n} stones (this machine, CPython):")
    print(f"  max-heap simulation:      {heap_time*1000:8.2f} ms")
    print(f"  re-sort every round:      {sort_time*1000:8.2f} ms")
    print(f"  heap is {sort_time / heap_time:.1f}x faster")
    assert heap_time < sort_time, (
        "expected the heap simulation to beat re-sorting the whole list every round"
    )

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
