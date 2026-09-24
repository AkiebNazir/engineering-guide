"""
================================================================================
SOLUTION · LeetCode 767 · Reorganize String                           [Medium]
https://leetcode.com/problems/reorganize-string/
================================================================================

THE CORE IDEA
--------------
This is problem 005 (Task Scheduler) with the cooldown fixed at exactly n=1
("never place the same character twice in a row"). Greedily always place the
CURRENTLY most frequent remaining character, then temporarily bench it for
exactly one slot (so it can't be placed immediately adjacent to itself) —
"what's currently most frequent?" is a max-heap query, same shape as 005.

================================================================================
APPROACH 0 · Try every permutation / backtrack (brute force, priced not coded)
================================================================================
Generate arrangements and check adjacency validity, backtracking on
violation. Factorial-in-the-worst-case (bounded better by counting
duplicate-permutation classes, but still exponential); with `s.length` up to
500 this is completely infeasible. Never the answer, stated only to price
the naive space.

================================================================================
APPROACH 1 · Max-heap greedy, bench-for-one-slot ✅ (the answer)
================================================================================
Count characters. Push `(-count, char)` for each into a max-heap. Repeatedly
pop the most frequent character, append it to the result, decrement its
count; if the PREVIOUSLY placed character still has remaining count, push it
back onto the heap now (it was benched for exactly one slot, satisfying the
non-adjacency rule). If at any point the heap is empty but a previously
placed character still has count > 0 and nothing else is available to
separate it, reorganization is impossible.

    Time:  O(n log 26) — n characters, O(log 26) per heap op (at most 26
           distinct lowercase letters).
    Space: O(26) for the heap + O(n) for the output string.

================================================================================
APPROACH 2 · Feasibility check + closed-form placement (no heap, `n` cooldown=1)
================================================================================
Reuse problem 005's `max(len(tasks), frame)` insight, specialized to n=1:
`frame = (max_count - 1) * 2 + num_max`. Reorganization is possible iff
`max_count <= (len(s) + 1) // 2` (the most frequent character can't exceed
"half the string, rounded up" — otherwise no arrangement can separate all its
occurrences). When feasible, one direct construction: sort characters by
descending frequency, then deal them round-robin into EVEN indices first
(0, 2, 4, ...) and once those run out continue into ODD indices (1, 3, 5,
...) — this guarantees the most frequent character's occurrences land with
maximum spacing without ever running a heap at all.

    Time:  O(n log 26) to sort by frequency (or O(n + 26 log 26) with
           counting); O(n) to place. Same asymptotic family as Approach 1,
           different constant, and avoids repeated heap churn.
    Space: O(26) + O(n) output.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — s = "aab" (max-heap approach)
--------------------------------------------------------------------------------
Counts: a=2, b=1.  Heap (negated): [(-2,'a'), (-1,'b')]

  Step 1: pop (-2,'a') -> place 'a'. result="a". remaining a-count=1.
          prev_char=None this round has nothing to push back yet.
          prev = ('a', remaining=1)

  Step 2: pop (-1,'b') -> place 'b'. result="ab". remaining b-count=0.
          push back prev ('a', 1) since its remaining > 0 -> heap=[(-1,'a')]
          prev = ('b', remaining=0)  (won't be pushed back, count is 0)

  Step 3: pop (-1,'a') -> place 'a'. result="aba". remaining a-count=0.
          prev ('b', 0) not pushed back (count 0).
          prev = ('a', remaining=0)

  Heap empty, prev has 0 remaining -> done. result = "aba".
  Check: no two adjacent characters equal. Matches a valid rearrangement of
  "aab" (the expected family of answers, e.g. "aba").

--------------------------------------------------------------------------------
STEP BY STEP TRACE — s = "aaab" (infeasible case)
--------------------------------------------------------------------------------
Counts: a=3, b=1. len(s)=4, (len(s)+1)//2 = 2. max_count=3 > 2 -> infeasible
by the closed-form check. Tracing the heap approach confirms: after placing
"aba", 'a' still has remaining=1 but the heap and prev-bench are both empty
of any OTHER character to separate it from the next 'a' -> return "".

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                             | Time            | Space | Mutates input `s`? |
|-----------------------------------------|-----------------|-------|------------------------|
| 0 · brute-force permutations (priced)   | exponential     | O(n)  | No                     |
| 1 · max-heap greedy, bench-1-slot ✅    | O(n log 26)     | O(n)  | No — strings are immutable in Python anyway |
| 2 · feasibility check + round-robin fill| O(n log 26)     | O(n)  | No                     |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single character, e.g. "a": trivially valid, no adjacency possible with
  only one character; both approaches return "a" immediately.
- Impossible cases, e.g. "aaab", "aaaaabc" where one letter's count exceeds
  `(len(s)+1)//2`: must return "" exactly (not raise, not partially build).
- Exactly at the feasibility boundary, e.g. "aabb" (max_count=2,
  (4+1)//2=2): must succeed — off-by-one here (`<` instead of `<=`) would
  wrongly reject a valid input.
- All characters identical, e.g. "aaaa": max_count=4 > (4+1)//2=2 ->
  infeasible, correctly rejected.
- All characters distinct, e.g. "abcde": trivially feasible in any order,
  every count is 1.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Benching the previous character for the WRONG number of slots — this
   problem's adjacency rule (distance exactly 1) means "push back after
   exactly one other placement," not after `n` placements as in the general
   Task Scheduler (n=1 is the correct specialization, but it's easy to
   copy-paste problem 005's cooldown logic with an off-by-one).
2. Checking feasibility with `max_count > len(s) // 2` (missing the `+1`)
   — this incorrectly rejects valid odd-length inputs where the most
   frequent character can legitimately occupy `ceil(len(s)/2)` slots (e.g.
   "aab": max_count=2, len=3, `(3+1)//2=2` is fine, but plain `3//2=1` would
   wrongly reject it).
3. Forgetting `heapq` is a min-heap (see _TOPIC_GUIDE.md §2.1) and comparing
   raw (non-negated) counts, silently placing the LEAST frequent character
   first — this can still coincidentally "succeed" on tiny test strings
   while being the wrong algorithm, since inverting the greedy priority
   removes the guarantee that separates the truly dominant character early.
4. Using string concatenation (`result += ch`) in a tight loop instead of a
   list + `''.join(...)` at the end — Python strings are immutable, so
   repeated `+=` in the worst case (no refcount-1 optimization applying) is
   O(n) per append, O(n^2) total; building a list and joining once is O(n).
5. Not validating the OUTPUT length matches the input length before
   returning success — a subtle heap-bookkeeping bug (e.g. losing track of
   a benched character) could silently produce a shorter-than-expected
   string that still "looks" adjacency-valid.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "Generalize to 'no two of the same character within distance k'?" — this
  is exactly problem 005 (Task Scheduler) with n=k-1; the bench-for-one-slot
  logic generalizes to bench-for-k-1-slots via a cooldown queue.
- "How many DIFFERENT valid rearrangements exist?" — a much harder counting
  problem (combinatorics on multiset permutations with adjacency
  constraints), not solvable by this greedy approach, which only produces
  ONE valid answer.
- "What if the alphabet is much larger than 26 (e.g. arbitrary Unicode)?"
  — the heap approach is unaffected (heap size scales with the number of
  DISTINCT characters actually present, not a fixed alphabet size); the
  feasibility bound `max_count <= (len(s)+1)//2` still holds unchanged.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 12/005 Task Scheduler — the general form of this problem (n cooldown
  instead of always-adjacent).
- 12/002 Last Stone Weight — repeatedly consume the current max via a
  max-heap, same mechanical shape, different rule for what gets pushed back.
- LC 358 Rearrange String k Distance Apart (not in this curriculum) — the
  direct generalization referenced in the first follow-up above.
================================================================================
"""

import heapq
import random
import time
from collections import Counter


class Solution:
    def reorganizeString(self, s: str) -> str:
        counts = Counter(s)
        max_count = max(counts.values())
        if max_count > (len(s) + 1) // 2:
            return ""

        heap = [(-c, ch) for ch, c in counts.items()]
        heapq.heapify(heap)

        result = []
        prev_count, prev_char = 0, ""
        while heap:
            count, ch = heapq.heappop(heap)
            result.append(ch)
            count += 1  # one fewer remaining (count is negative)
            if prev_count < 0:
                heapq.heappush(heap, (prev_count, prev_char))
            prev_count, prev_char = count, ch

        return "".join(result)

    def reorganizeString_no_heap(self, s: str) -> str:
        # Alternative: feasibility check + round-robin even/odd placement.
        counts = Counter(s)
        max_count = max(counts.values())
        n = len(s)
        if max_count > (n + 1) // 2:
            return ""

        order = sorted(counts.items(), key=lambda kv: -kv[1])
        result = [""] * n
        idx = 0
        for ch, cnt in order:
            for _ in range(cnt):
                if idx >= n:
                    idx = 1  # ran out of even slots, continue on odd slots
                result[idx] = ch
                idx += 2
        return "".join(result)


def run_tests():
    sol = Solution()

    def is_valid(result: str, original: str) -> bool:
        if result == "":
            return False
        if Counter(result) != Counter(original):
            return False
        return all(result[i] != result[i + 1] for i in range(len(result) - 1))

    cases_valid = ["aab", "aabb", "a", "vvvlo", "aabbcc"]
    for s in cases_valid:
        r1 = sol.reorganizeString(s)
        r2 = sol.reorganizeString_no_heap(s)
        assert is_valid(r1, s), f"heap approach failed on {s!r}: {r1!r}"
        assert is_valid(r2, s), f"no-heap approach failed on {s!r}: {r2!r}"

    cases_infeasible = ["aaab", "aaaaabc", "aaaa", "aaaabb"]
    for s in cases_infeasible:
        assert sol.reorganizeString(s) == ""
        assert sol.reorganizeString_no_heap(s) == ""

    # exactly-at-boundary feasibility
    assert is_valid(sol.reorganizeString("aabb"), "aabb")

    # cross-check on randomized strings
    random.seed(5)
    for _ in range(300):
        s = "".join(random.choice("abc") for _ in range(random.randint(1, 12)))
        r1 = sol.reorganizeString(s)
        r2 = sol.reorganizeString_no_heap(s)
        assert (r1 == "") == (r2 == ""), f"feasibility disagreement on {s!r}: {r1!r} vs {r2!r}"
        if r1:
            assert is_valid(r1, s)
        if r2:
            assert is_valid(r2, s)

    # --- measured runtime demo: max-heap greedy vs round-robin (no heap) ---
    random.seed(42)
    n = 500  # LeetCode's max constraint for this problem
    s = "".join(random.choice("abcdefghij") for _ in range(n))
    reps = 2000

    t0 = time.perf_counter()
    for _ in range(reps):
        heap_result = sol.reorganizeString(s)
    heap_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(reps):
        rr_result = sol.reorganizeString_no_heap(s)
    rr_time = time.perf_counter() - t0

    assert is_valid(heap_result, s) and is_valid(rr_result, s)

    print(f"n={n} chars, {reps} calls (this machine, CPython):")
    print(f"  max-heap greedy:      {heap_time*1000:8.2f} ms")
    print(f"  round-robin (no heap):{rr_time*1000:8.2f} ms")
    print(f"  round-robin is {heap_time / rr_time:.1f}x faster (avoids repeated heap push/pop overhead)")
    assert rr_time < heap_time, (
        "expected the heap-free round-robin construction to beat repeated heap churn"
    )

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
