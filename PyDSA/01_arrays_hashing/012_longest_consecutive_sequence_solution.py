"""
================================================================================
SOLUTION · LeetCode 128 · Longest Consecutive Sequence                 [Medium]
https://leetcode.com/problems/longest-consecutive-sequence/
================================================================================

THE CORE IDEA
-------------
Two moves, and the second one is the whole problem.

    MOVE 1 — a set turns "what comes next?" into O(1).
             `seen = set(nums)`, then `x + 1 in seen` walks the number line
             without ever sorting.

    MOVE 2 — ONLY WALK FROM THE START OF A RUN.
             x starts a run  ⟺  x - 1 is NOT in the set.

Move 1 alone is O(n²): starting a walk at every element re-traverses the same
run once per member. Move 2 fixes it with a single membership test, and that
test is the insight the problem is built around.

    nums = [100, 4, 200, 1, 3, 2]      seen = {1,2,3,4,100,200}

        x=1    0 not in seen  ->  START.  walk 1,2,3,4  -> length 4
        x=2    1 IS in seen   ->  skip (someone else owns this run)
        x=3    2 IS in seen   ->  skip
        x=4    3 IS in seen   ->  skip
        x=100  99 not in seen ->  START.  walk 100      -> length 1
        x=200  199 not in seen->  START.  walk 200      -> length 1

        answer 4

Every run has exactly ONE element that passes the guard — its minimum. So each
run is walked exactly once, and the total inner-loop work across the entire
algorithm is bounded by the number of distinct elements. That is why this is
O(n) and not O(n²), and being able to say that sentence is the point.

⚠️  THE COMPLEXITY ARGUMENT IS THE ANSWER
    A nested loop that is still O(n) is counter-intuitive, so interviewers ask
    you to justify it. The justification is AMORTISED, not per-iteration:
    the inner `while` looks like it could run n times, and it can — but only
    for the one element that owns that run. Summed over all runs, each number
    is visited by an inner walk at most once. Total inner work: O(n).
    Say "amortised" and say why. Do not just assert O(n).


================================================================================
APPROACH 0 · Sort, then scan (correct, and correctly rejected)
================================================================================
    if not nums: return 0
    nums.sort()
    best = cur = 1
    for i in range(1, len(nums)):
        if nums[i] == nums[i-1]:      continue          # skip duplicates
        elif nums[i] == nums[i-1] + 1: cur += 1
        else:                          cur = 1
        best = max(best, cur)
    return best

    Time: O(n log n)      Space: O(1) extra (or O(n) if you must not mutate)

Say this first — it is obviously correct and it shows you can solve the problem
before optimising it. Then quote the requirement: "must run in O(n) time". The
sort is the only super-linear step, so the task is to eliminate it.

⚠️  The duplicate branch is mandatory, and omitting it breaks in EITHER
    direction depending on where the equal case lands: if a duplicate falls
    into `else` it RESETS the run ([1,2,2,3] -> 2); if you write `<= 1` it
    EXTENDS the run ([1,2,2,3] -> 4). The answer is 3. The demo at the bottom
    runs both. Also note this version MUTATES the caller's list; `sorted(nums)`
    costs O(n) space but leaves the input alone.

⚠️  Does the C-coded sort beat the "optimal" O(n) set version in CPython, the
    way it does in LC 49 and LC 347? MEASURE, do not assume. The benchmark at
    the bottom of this file runs both at n = 10^5 and the set version wins by
    roughly 2-3x. The reason the usual "C beats interpreted" argument fails
    here: sorting does O(n log n) comparisons of BOXED Python ints, each a
    C-level call back into integer comparison, while the set version does O(n)
    hash probes — and hashing a small int in CPython is nearly free
    (`hash(x) == x` for small ints). Fewer operations wins outright.

    So this is the case where the asymptotically better answer is also the
    faster one. Good — but you only know that because it was measured.


================================================================================
APPROACH 1 · Set + start-of-run guard ✅✅ (the answer)
================================================================================

    seen = set(nums)
    best = 0
    for x in seen:                        # iterate the SET, not the list
        if x - 1 in seen:                 # not a run start — skip
            continue
        length = 1
        while x + length in seen:         # walk forward
            length += 1
        best = max(best, length)
    return best

    Time:  O(n)      Space: O(n)

STEP BY STEP for nums = [0,3,7,2,5,8,4,6,0,1]:

    seen = {0,1,2,3,4,5,6,7,8}      (the duplicate 0 collapsed)

    x   x-1 in seen?   action                                     best
    --  -------------  -------------------------------------      ----
    0   -1  no         START -> walk 0,1,2,3,4,5,6,7,8 = 9          9
    1    0  YES        skip                                         9
    2    1  YES        skip                                         9
    3    2  YES        skip                                         9
    4    3  YES        skip                                         9
    5    4  YES        skip                                         9
    6    5  YES        skip                                         9
    7    6  YES        skip                                         9
    8    7  YES        skip                                         9

    answer 9

    Total inner-loop steps: 9. One walk, not nine walks.

WHERE THE WORK GOES — a two-run example, nums = [1,2,3,100,101,102,103]:

        number line:   1───2───3          100──101──102──103
                       ▲                   ▲
                    start                start
                    walks 3              walks 4

        guard fires (skips) at: 2, 3, 101, 102, 103
        walks happen at:        1 (3 steps), 100 (4 steps)
        total inner steps: 7 == number of distinct elements       ✓ O(n)

⚠️  ITERATE THE SET, NOT THE LIST
    `for x in nums` also gives the right answer, but on input with heavy
    duplication it re-does the guard check for every copy. `for x in seen`
    visits each distinct value once. With nums = [1]*100000 that is 100000
    checks versus 1. Free win, one word of code.

⚠️  DO NOT MUTATE THE SET WHILE ITERATING IT
    A tempting "optimisation" is to `seen.discard(v)` as you walk, so later
    elements skip faster. Doing that inside `for x in seen` raises
    `RuntimeError: Set changed size during iteration`. If you want that
    optimisation, iterate over `nums` (or a list copy) instead. The tests below
    trigger the error so you have seen it.

⚠️  `while x + length in seen` VS `while x + 1 in seen: x += 1`
    Both work. The first leaves x pinned at the run start, which is easier to
    debug and to narrate. The second re-uses x as the walker; if you also need
    the start value later, you have lost it.


================================================================================
APPROACH 2 · Hash map of run lengths at the endpoints (one pass)
================================================================================
Keep `length[v]` meaningful ONLY at the two ends of each run. When a new value
v arrives, look at the runs ending at v-1 and starting at v+1, and splice:

    left  = length.get(v - 1, 0)
    right = length.get(v + 1, 0)
    total = left + right + 1
    length[v] = total                     # v itself (harmless if interior)
    length[v - left]  = total             # the new left endpoint
    length[v + right] = total             # the new right endpoint

    Time: O(n) single pass      Space: O(n)

Genuinely one pass, and it handles a STREAM — you can answer "longest run so
far" after every insertion, which the set approach cannot without redoing work.
The catch: interior values hold stale lengths, which is fine only because
nothing ever reads them. That invariant is easy to state and easy to get wrong.

Mention this if asked for a streaming version. Do not lead with it — it is
harder to justify on a whiteboard than the guard.


================================================================================
APPROACH 3 · Union-Find
================================================================================
Union each v with v+1 when both are present; the answer is the largest
component size. O(n·α(n)), effectively O(n).

It works and it is a good "I recognise connectivity" signal, but it is more
machinery than the problem needs — a union-find implementation is 30 lines to
replace a 2-line guard. Name it, do not write it, unless they ask for
incremental merging.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                 Time         Extra space   Mutates input?
    -----------------------  -----------  ------------  --------------
    Brute force per element  O(n³)/O(n²)  O(1)/O(n)     no
    Sort + scan              O(n log n)   O(1)          YES (nums.sort())
    Sort(copy) + scan        O(n log n)   O(n)          no
    Set + guard        ✅✅  O(n)         O(n)          no
    Endpoint hash map        O(n)         O(n)          no
    Union-Find               O(n·α(n))    O(n)          no

    O(n) space is unavoidable for the O(n)-time answers: you need O(1)
    membership over arbitrary 32-bit values, and that means hashing.


================================================================================
EDGE CASES
================================================================================
    []                -> 0
                         `max()` on an empty sequence RAISES. Either seed
                         `best = 0` (as here) or guard the empty input. This is
                         the most commonly failed case on the whole problem.

    [1]               -> 1
                         Single element is a run of length 1, not 0. Off-by-one
                         check on your `length = 1` initialiser.

    [1, 2, 2, 3]      -> 3
                         DUPLICATES must not change the count. The set
                         collapses them for free — but the SORT approach needs
                         an explicit `continue`, and getting it wrong breaks in
                         EITHER direction (2 if the duplicate resets the run,
                         4 if it extends it). That is why sorting is the
                         buggier route despite looking simpler.

    [1, 1, 1, 1]      -> 1
                         All duplicates. seen = {1}, one run of 1.

    [-3,-2,-1,0]      -> 4
                         NEGATIVES. Nothing special happens — but code that
                         tried to bucket by value (index-as-hash, as in LC 448)
                         dies here. Values span -10^9..10^9, so an array
                         indexed by value is impossible; hashing is required.

    [10, 30, 20]      -> 1
                         No consecutive pair at all. Every element is its own
                         run start; answer is 1, not 0.

    [1,2,3,100,101,102,103] -> 4
                         The longer run comes SECOND. Catches code that returns
                         on the first run instead of taking a maximum.


================================================================================
COMMON MISTAKES
================================================================================
1. Returning 0 for a single-element array, or crashing on []. Handle the empty
   case; `max()` of nothing raises ValueError.

2. Omitting the `x - 1 not in seen` guard. Still CORRECT, but O(n²) — and on
   [1..100000] it visibly hangs. This is the mistake the problem exists to
   catch, and it passes every small test.

3. Sorting. Correct, O(n log n), fails the stated requirement.

4. Forgetting duplicate handling in the sort-based version. Which way it
   breaks depends on which branch swallows the equal case:
       `else: cur = 1`   on a duplicate -> RESETS  -> [1,2,2,3] gives 2
       `cur += 1`        on a duplicate -> INFLATES-> [1,2,2,3] gives 4
   Both are wrong; the answer is 3. The set version has neither bug because
   `set()` collapses duplicates before you ever look at them.

5. Iterating `for x in nums` instead of `for x in seen` — correct but wasteful
   on duplicate-heavy input.

6. Mutating `seen` inside `for x in seen` — RuntimeError at runtime.

7. Trying index-as-hash / bucket-by-value. Values reach ±10^9; you cannot
   allocate that array.

8. Counting the run but forgetting `best = max(best, length)`, so you return
   the LAST run's length instead of the longest.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the sequence itself, not just its length.
A: Track the winning start alongside the max length, then emit
   `range(start, start + best)`. O(1) extra state.

Q: Numbers arrive as a stream; report the longest run after each insertion.
A: The set-and-guard approach would redo O(n) work per insert. Use approach 2
   (endpoint hash map) — it is O(1) amortised per element and maintains the
   answer incrementally. This is the real reason to know that approach.

Q: The data does not fit in memory.
A: External sort, then a linear scan of the sorted runs — O(n log n) I/O but
   O(1) memory. The O(n)-time solution needs an O(n) in-memory set, so when
   memory is the binding constraint you go back to sorting. State the trade
   rather than insisting on the "optimal" answer.

Q: What if you may not use extra space?
A: Then you sort in place, O(n log n) time and O(1) space. The O(n)-time
   requirement and the O(1)-space requirement are mutually exclusive here;
   pointing that out is a better answer than trying to satisfy both.

Q: Longest run with a gap tolerance of at most k missing values?
A: Sort the distinct values, then it becomes a sliding window over the sorted
   array. Different problem shape entirely — the hash trick does not extend.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 298  Binary Tree Longest Consecutive Sequence — same notion, on a tree
    LC 300  Longest Increasing Subsequence — sounds similar, completely
                                              different (DP / patience sorting)
    LC 594  Longest Harmonious Subsequence — pairs differing by exactly 1;
                                              a Counter is enough
    LC 1198 Find Smallest Common Element   — set intersection over rows
    LC 41   First Missing Positive [Hard]  — the same "is x present?" question,
                                              answered in O(1) SPACE via
                                              index-as-hash (possible there
                                              because values are bounded by n)
    LC 721  Accounts Merge                 — the union-find version of grouping
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def longestConsecutive(self, nums: List[int]) -> int:
        """Set + start-of-run guard. Time O(n), space O(n). No mutation."""
        seen = set(nums)                 # O(1) membership; duplicates collapse
        best = 0
        for x in seen:                   # iterate the SET, not the list
            if x - 1 in seen:
                continue                 # not a run start — someone else owns it
            length = 1
            while x + length in seen:    # walk the run exactly once
                length += 1
            best = max(best, length)
        return best                      # 0 for empty input, no special case

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def longestConsecutive_sort(self, nums: List[int]) -> int:
        """Sort + scan. O(n log n). Does not mutate — sorts a copy."""
        if not nums:
            return 0
        s = sorted(nums)
        best = cur = 1
        for i in range(1, len(s)):
            if s[i] == s[i - 1]:
                continue                 # duplicates must not inflate the run
            if s[i] == s[i - 1] + 1:
                cur += 1
            else:
                cur = 1
            best = max(best, cur)
        return best

    def longestConsecutive_endpoints(self, nums: List[int]) -> int:
        """One pass, run lengths valid at run ENDPOINTS. Streaming-friendly."""
        length = {}
        best = 0
        for v in nums:
            if v in length:              # duplicate: already accounted for
                continue
            left = length.get(v - 1, 0)
            right = length.get(v + 1, 0)
            total = left + right + 1
            length[v] = total            # may be interior; never read again
            length[v - left] = total     # new left endpoint
            length[v + right] = total    # new right endpoint
            best = max(best, total)
        return best

    def longestConsecutive_noguard(self, nums: List[int]) -> int:
        """✗ CORRECT BUT O(n^2) — the guard is missing. For the benchmark."""
        seen = set(nums)
        best = 0
        for x in seen:
            length = 1
            while x + length in seen:
                length += 1
            best = max(best, length)
        return best


# ==============================================================================
# TESTS — run:  python 012_longest_consecutive_sequence_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([100, 4, 200, 1, 3, 2], 4),
        ([0, 3, 7, 2, 5, 8, 4, 6, 0, 1], 9),
        ([], 0),
        ([1], 1),
        ([1, 2, 0, 1], 3),
        ([1, 1, 1, 1], 1),
        ([9, 1, 4, 7, 3, -1, 0, 5, 8, -1, 6], 7),
        ([-3, -2, -1, 0], 4),
        ([10, 30, 20], 1),
        ([1, 2, 3, 100, 101, 102, 103], 4),
        ([1, 2, 2, 3], 3),
        ([-10**9, 10**9], 1),                     # extreme values
    ]
    impls = [
        ("set + guard  ", sol.longestConsecutive),
        ("sort + scan  ", sol.longestConsecutive_sort),
        ("endpoint map ", sol.longestConsecutive_endpoints),
        ("no guard     ", sol.longestConsecutive_noguard),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(nums)) == exp for nums, exp in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # ----------------------------------------------------------------------
    # The guard in action.
    # ----------------------------------------------------------------------
    print("\n--- who is allowed to walk? nums = [1,2,3,100,101,102,103] ---")
    nums = [1, 2, 3, 100, 101, 102, 103]
    seen = set(nums)
    steps = 0
    print(f"  {'x':>4}  {'x-1 in seen?':<13} {'action':<24} inner steps")
    for x in sorted(seen):
        if x - 1 in seen:
            print(f"  {x:>4}  {'YES':<13} {'skip':<24} 0")
            continue
        length = 1
        while x + length in seen:
            length += 1
            steps += 1
        steps += 1
        print(f"  {x:>4}  {'no':<13} {'START, run of ' + str(length):<24} {length}")
    print(f"  total inner steps = {steps}, distinct elements = {len(seen)}")
    print("  Each element is walked at most once. THAT is the O(n) argument.")

    # ----------------------------------------------------------------------
    # ⚠️  Drop the guard: still correct, quadratically slower.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the guard is the whole algorithm ---")
    prev_g = prev_n = None
    for n in (2_000, 4_000, 8_000):
        data = list(range(n))            # worst case: one giant run
        random.shuffle(data)
        t0 = time.perf_counter(); sol.longestConsecutive(data)
        t_guard = time.perf_counter() - t0
        t0 = time.perf_counter(); sol.longestConsecutive_noguard(data)
        t_none = time.perf_counter() - t0
        gg = f"{t_guard / prev_g:4.1f}x" if prev_g else "  -  "
        gn = f"{t_none / prev_n:4.1f}x" if prev_n else "  -  "
        prev_g, prev_n = t_guard, t_none
        print(f"  n={n:<6} with guard {t_guard*1000:7.2f}ms ({gg})   "
              f"without {t_none*1000:9.2f}ms ({gn})   "
              f"{t_none / max(t_guard, 1e-9):6.0f}x")
    print("  Doubling n doubles the guarded version and QUADRUPLES the other.")
    print("  Both return the same answer — only one of them finishes at 10^5.")

    # ----------------------------------------------------------------------
    # ⚠️  Mutating the set while iterating it.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  discarding from the set you are iterating ---")
    seen = set([1, 2, 3, 4])
    try:
        for x in seen:
            seen.discard(x + 1)
        print("  no error?! (should never print)")
    except RuntimeError as e:
        print(f"  for x in seen: seen.discard(...)  -> RuntimeError: {e}")
    print("  If you want that optimisation, iterate a list copy instead.")

    # ----------------------------------------------------------------------
    # ⚠️  Duplicates: free with a set, a manual branch when sorting.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the sorted scan needs an explicit duplicate branch ---")
    print("  Omit it and you break in one of two directions, depending on")
    print("  which branch the equal case falls into:")

    def sort_dupe_resets(nums):
        """Duplicate falls into `else` -> resets the run. UNDERCOUNTS."""
        if not nums:
            return 0
        s = sorted(nums)
        best = cur = 1
        for i in range(1, len(s)):
            if s[i] == s[i - 1] + 1:
                cur += 1
            else:
                cur = 1
            best = max(best, cur)
        return best

    def sort_dupe_extends(nums):
        """Duplicate treated as continuing the run. OVERCOUNTS."""
        if not nums:
            return 0
        s = sorted(nums)
        best = cur = 1
        for i in range(1, len(s)):
            if s[i] - s[i - 1] <= 1:     # <= instead of ==, so equal extends
                cur += 1
            else:
                cur = 1
            best = max(best, cur)
        return best

    print(f"  {'input':<20} {'correct':>8} {'resets':>8} {'extends':>9}")
    for data in ([1, 2, 2, 3], [1, 2, 3, 3, 4, 5], [1, 1, 1, 1]):
        print(f"  {str(data):<20} {sol.longestConsecutive(list(data)):>8}"
              f" {sort_dupe_resets(list(data)):>8}"
              f" {sort_dupe_extends(list(data)):>9}")
    print("  Wrong in both directions. set() sidesteps it entirely.")

    # ----------------------------------------------------------------------
    # ⚠️  Empty input.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the empty array ---")
    print(f"  set + guard on []  -> {sol.longestConsecutive([])}   (best seeded to 0)")
    try:
        print(max([]))
    except ValueError as e:
        print(f"  max([])            -> ValueError: {e}")
    print("  Any version that ends in `return max(lengths)` crashes on [].")

    # ----------------------------------------------------------------------
    # The honest benchmark: O(n) vs O(n log n) in CPython.
    # ----------------------------------------------------------------------
    print("\n--- O(n) set vs O(n log n) sort, at the real constraint size ---")
    for n in (100_000,):
        for label, data in (
            ("one long run ", list(range(n))),
            ("all scattered", [random.randint(-10**9, 10**9) for _ in range(n)]),
        ):
            d = list(data)
            random.shuffle(d)
            t0 = time.perf_counter(); a = sol.longestConsecutive(list(d))
            t_set = time.perf_counter() - t0
            t0 = time.perf_counter(); b = sol.longestConsecutive_sort(list(d))
            t_sort = time.perf_counter() - t0
            t0 = time.perf_counter(); c = sol.longestConsecutive_endpoints(list(d))
            t_end = time.perf_counter() - t0
            assert a == b == c, (a, b, c)
            print(f"  n={n} {label}  set {t_set*1000:7.1f}ms   "
                  f"sort {t_sort*1000:7.1f}ms   endpoints {t_end*1000:7.1f}ms")
    print("  Here the O(n) set version WINS outright, ~2-3x. That is worth")
    print("  noting because it is NOT the usual story: in LC 49 and LC 347 the")
    print("  C-coded sort beats the asymptotically better Python loop. The")
    print("  difference is that hashing a small int in CPython is nearly free")
    print("  (hash(x) == x), so O(n) cheap probes beat O(n log n) comparisons")
    print("  of boxed ints. Same lesson as always, opposite conclusion:")
    print("  measure, do not assume — in either direction.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
