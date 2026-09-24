"""
================================================================================
SOLUTION · LeetCode 40 · Combination Sum II                             [Medium]
https://leetcode.com/problems/combination-sum-ii/
================================================================================

THE CORE IDEA
--------------
Two changes to problem 007, and you need BOTH. Neither alone is correct.

    007 (LC 39)                          008 (LC 40)  <- HERE
    -----------------------------------  -----------------------------------
    candidates are distinct              candidates may REPEAT
    unlimited reuse   -> backtrack(i)    each used once -> backtrack(i + 1)
    no dedupe needed                     skip duplicate SIBLINGS

The skip is the dedupe idiom from problem 003 (Subsets II), unchanged:

    cands = sorted(candidates)
    def backtrack(start, remaining):
        if remaining == 0: results.append(path[:]); return
        for i in range(start, n):
            if i > start and cands[i] == cands[i - 1]:   # duplicate SIBLING
                continue
            if cands[i] > remaining:                     # sorted: tail hopeless
                break
            path.append(cands[i])
            backtrack(i + 1, remaining - cands[i])
            path.pop()

`i > start` — not `i > 0` — is the whole trick, and the reason is worth being
able to say in one sentence: **the first time a value is offered as a choice AT
THIS NODE it must be allowed; only a repeat of it AS A SIBLING at the same node
is redundant.** A value that recurs at a DEEPER node is a different element of
the input being consumed, and is not only legal but required — `[1,1,6]` is a
real answer for `[10,1,2,7,6,1,5]`, target 8.

THE THREE FILES SIDE BY SIDE — read this, then never confuse them again
------------------------------------------------------------------------
Same skeleton, three lines of difference. This is the entire "II" family.

    LC 39  Combination Sum      LC 40  Combination Sum II   LC 90  Subsets II
    ------------------------    -------------------------   ------------------
    sorted(candidates)          sorted(candidates)          sorted(nums)
    -- no sibling skip --       if i > start and             if i > start and
                                   c[i] == c[i-1]: continue     n[i]==n[i-1]:
                                                                 continue
    if c[i] > rem: break        if c[i] > rem: break        -- no sum, no break
    backtrack(i,   rem-c[i])    backtrack(i+1, rem-c[i])    backtrack(i+1)
    record when rem == 0        record when rem == 0        record at EVERY node

    reuse: YES                  reuse: no                   reuse: no
    dupes in input: forbidden   dupes in input: expected     dupes in input: yes
    leaf test: sum == target    leaf test: sum == target     leaf test: none

Three axes, three problems: (reuse?) × (duplicates in input?) × (what is a
leaf?). Every other problem in this folder is another point in that space.

WHY SORTING IS A PREREQUISITE, TWICE OVER
------------------------------------------
1. The skip test only knows `cands[i] == cands[i - 1]`, i.e. ADJACENCY. On
   `[2,5,2,1,2]` the 2s are not adjacent, nothing is caught, and duplicate
   combinations come out. Sorting is what gives the guard meaning. Measured
   live below.
2. The `break` needs ascending order to be sound (see 007's mistake 6 — with
   an unsorted array `break` throws away viable candidates and loses real
   answers).

Two independent reasons, one `sort()`. Say both.

================================================================================
MULTIPLE APPROACHES
================================================================================

1. ENUMERATE EVERY SUBSET, FILTER BY SUM, DEDUPE WITH A SET   (brute force)
   `2^n` index subsets, keep those summing to target, dedupe by sorted tuple.
   Correct, and the tests use it as the independent oracle on small inputs.
   At n = 100 (the constraint) it is 2^100 — impossible. Priced, and coded
   only as an oracle.

2. BACKTRACKING + SET DEDUPE AT THE END
   007's tree with `backtrack(i + 1)`, then `set(tuple(c) for c in results)`.
   Correct. It BUILDS every duplicate branch and throws it away afterwards.
   On `[1]*18` with target 9 that is C(18,9) = 48,620 leaves collapsing to
   ONE answer — and the benchmark below shows the real cost.

3. BACKTRACKING + SORT + DUPLICATE-SIBLING SKIP                 <- the answer
   Prunes duplicate branches at GENERATION time. Plus the `break` from 007.

4. COUNT THE MULTIPLICITIES FIRST, THEN CHOOSE A COUNT PER DISTINCT VALUE
   `Counter(candidates)`, then for each distinct value choose how many copies
   (0..count) to take. Same result set, and it is the formulation that makes
   the dedupe structural rather than a guard: you never have two ways to pick
   "two 1s". Genuinely nice, slightly more code, and the right answer if the
   interviewer asks "what if a value appears 10,000 times?" — the sibling-skip
   version walks 10,000 loop iterations per node just to skip them, while this
   one walks one. Both are below; both are measured.

5. DP OVER TARGETS
   Same idea as 007's DP oracle but with each element usable once — this is
   the 0/1 knapsack shape rather than unbounded. For LISTING it allocates
   every intermediate list; for COUNTING it is the right tool (LC 494-ish
   territory).

================================================================================
STEP BY STEP  ·  candidates = [10,1,2,7,6,1,5] -> sorted [1,1,2,5,6,7,10],  target = 8
================================================================================

    s= is the `start` of the call. `rem` is what is left of the target.
    The two 1s are at indices 0 and 1.

    backtrack(s=0, rem=8, path=[])
    |
    +-- i=0  cands[0]=1  i == start -> ALWAYS allowed. path=[1], rem=7
    |   backtrack(s=1, rem=7)
    |   |
    |   +-- i=1  cands[1]=1  i > start? 1 > 1 is FALSE -> ALLOWED.
    |   |        (This is the same VALUE as index 0, but it is the first
    |   |         choice at THIS node, so it is a different element being
    |   |         consumed, not a repeated sibling.)
    |   |   path=[1,1], rem=6   backtrack(s=2, rem=6)
    |   |   +-- i=2  2 <= 6 -> path=[1,1,2] rem=4  backtrack(s=3, rem=4)
    |   |   |       i=3: 5 > 4 -> BREAK.  dead end.
    |   |   +-- i=3  5 <= 6 -> path=[1,1,5] rem=1  backtrack(s=4, rem=1)
    |   |   |       i=4: 6 > 1 -> BREAK.  dead end.
    |   |   +-- i=4  6 <= 6 -> path=[1,1,6] rem=0  ==> EMIT [1,1,6]
    |   |   +-- i=5  7 > 6 -> BREAK
    |   |   pop
    |   +-- i=2  2, i>start(1) and 2 != 1 -> allowed. path=[1,2] rem=5
    |   |   +-- i=3  5 <= 5 -> path=[1,2,5] rem=0  ==> EMIT [1,2,5]
    |   |   +-- i=4  6 > 5 -> BREAK
    |   +-- i=3  5 -> path=[1,5] rem=2   backtrack(s=4, rem=2): 6 > 2 BREAK
    |   +-- i=4  6 -> path=[1,6] rem=1   backtrack(s=5, rem=1): 7 > 1 BREAK
    |   +-- i=5  7 -> path=[1,7] rem=0   ==> EMIT [1,7]
    |   +-- i=6  10 > 7 -> BREAK
    |   pop
    |
    +-- i=1  cands[1]=1.  i > start? 1 > 0 is TRUE, and cands[1]==cands[0].
    |        ==> SKIP.  <-- THE ENTIRE POINT OF THE FILE.
    |        Without this skip the whole i=0 subtree is rebuilt here with the
    |        other 1, re-emitting [1,1,6]? no — [1,1,6] needs BOTH 1s and
    |        only index >1 is reachable now — but it does re-emit [1,2,5],
    |        [1,7] and [1,5]... i.e. every answer that used exactly ONE 1.
    |        Those are the duplicates, and the demo below prints them.
    |
    +-- i=2  2 -> path=[2] rem=6
    |   +-- i=3  5 <= 6 -> [2,5] rem=1 -> backtrack: 6 > 1 BREAK
    |   +-- i=4  6 <= 6 -> [2,6] rem=0  ==> EMIT [2,6]
    |   +-- i=5  7 > 6 -> BREAK
    |
    +-- i=3  5 -> [5] rem=3  -> i=4: 6 > 3 BREAK
    +-- i=4  6 -> [6] rem=2  -> i=5: 7 > 2 BREAK
    +-- i=5  7 -> [7] rem=1  -> i=6: 10 > 1 BREAK
    +-- i=6  10 > 8 -> BREAK at the root

    Result: [[1,1,6], [1,2,5], [1,7], [2,6]]   correct, and in lexicographic
    order for free (a consequence of sorting + increasing index).

READ THE i=0 / i=1 CONTRAST ONE MORE TIME. Index 1 is ALLOWED at depth 1
(where start == 1) and SKIPPED at depth 0 (where start == 0). Same index, same
value, opposite decisions — and that is precisely what `i > start` encodes.
`i > 0` would skip index 1 in both places and [1,1,6] would vanish.

================================================================================
COMPLEXITY SUMMARY
================================================================================

    n = len(candidates), T = target.

    Approach                              Time              Space   Mutates input?
    ------------------------------------  ----------------  ------  --------------
    All 2^n subsets + filter + set        O(n * 2^n)        O(2^n)  no
    Backtracking + set dedupe at the end  O(n * 2^n)        O(#res) no
    Sort + sibling skip + break  ✅        O(n log n) then   O(n)    no*
                                          O(2^n) worst,
                                          far fewer nodes
                                          when values repeat
    Counter + per-value count loop        same worst case,  O(n)    no
                                          O(distinct) per
                                          node instead of
                                          O(n)
    0/1-knapsack DP (listing)             O(n * T * #res)   O(T * #res)  no

    * `sorted(candidates)` builds a copy, so the caller's list is untouched.
      `candidates.sort()` would mutate it — a free point to mention.

    WHERE THE SAVING IS: the sibling skip turns a run of k equal values from
    `2^k` branches (each subset of the run) into `k + 1` branches (take 0, 1,
    ..., k of them). That is an exponential-to-linear collapse ON THAT RUN,
    which is why `[1]*18` goes from 48,620 explored leaves to a single chain.
    The tests measure exactly this.

    The `break` is a separate, smaller saving (it prunes the too-big tail).
    The two prunings are independent and both are cheap; keep both.

================================================================================
EDGE CASES
================================================================================

    [1,1], target 1  -> [[1]] exactly ONCE. The minimal duplicate test. A
                        solution with no skip returns [[1],[1]].

    [1,1], target 2  -> [[1,1]]. The minimal test that the skip does NOT
                        forbid using both copies. A solution with the `i > 0`
                        guard returns [] here — it is the counterexample to
                        the wrong guard.

    [2], target 1    -> []. Nothing fits; the `break` fires at the root.

    [4,4,4,4], target 8 -> [[4,4]] once, not C(4,2)=6 times.

    unsorted with non-adjacent duplicates, e.g. [2,5,2,1,2], target 5 ->
                        [[1,2,2],[5]]. This is the input that catches a
                        solution which applies the skip without sorting.

    all values > target, e.g. [50], target 30 -> []. Root `break`.

    target reachable only by using every element, e.g. [1,1,1], target 3 ->
                        [[1,1,1]]. Confirms the skip prunes SIBLINGS, not
                        depth.

    100 copies of 1 with target 30 -> exactly one answer ([1]*30). The
                        sibling skip makes this a single chain of 30 calls;
                        without it, C(100,30) ≈ 3e25 leaves — the difference
                        between instant and never.

================================================================================
COMMON MISTAKES
================================================================================

1. Keeping 007's `backtrack(i)`.
   Now an element can be reused, so [1,1,1,...] appears for an input with one
   1. Two changes are needed from 007, and this is the one people remember
   second.

2. Dropping the sibling skip.
   Duplicate combinations in the output. Printed side by side below on the
   problem's own example: 4 correct answers become 6 results with 2 dupes.

3. `i > 0` instead of `i > start`.
   Forbids the SECOND copy of a value even at a deeper node, so [1,1,6]
   disappears. The same wrong-guard bug as problem 003, and it UNDERCOUNTS
   (the previous mistake OVERCOUNTS). Demonstrated live.

4. Applying the skip without sorting.
   The guard tests adjacency; unsorted equal values are not adjacent, so
   nothing is skipped on inputs like [2,5,2,1,2]. Demonstrated live.

5. `break` instead of `continue` on the duplicate-sibling test.
   `break` abandons the whole loop on hitting a duplicate, so every LARGER
   candidate at that node is lost. Silently drops answers. Demonstrated live
   — this is the most subtle of the four, because on many inputs the two
   behave identically.

6. `results.append(path)` instead of `path[:]`.
   The copy-on-append trap; every entry ends up the same empty list.

7. Deduping with a set at the end and calling it done.
   Correct output, exponentially more work on duplicate-heavy input, and it
   tells the interviewer you did not internalise why 003 exists. Benchmarked
   below.

8. Believing `remaining < 0` needs its own base case when you have the
   `break`.
   With sorting + `break` you never recurse into a negative remainder, so the
   check is dead code. Harmless, but know why it is redundant rather than
   copying it around out of habit.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================

Q: What if a value appears 10,000 times?
A: The sibling skip still gives the right answer, but the loop at each node
   walks all 10,000 equal entries just to `continue` past 9,999 of them.
   Switch to the Counter formulation (approach 4): iterate over DISTINCT
   values and choose a count 0..multiplicity. Node cost drops from O(n) to
   O(distinct). Measured below on 3,000 copies of 1.

Q: How many unique combinations are there — don't list them?
A: 0/1-knapsack counting DP: `dp[0] = 1`, for each element c (outer), for
   t from target down to c (inner, DESCENDING so each element is used once),
   `dp[t] += dp[t-c]`. O(n * target). The descending inner loop is the whole
   0/1-vs-unbounded distinction — ascending gives LC 39's unlimited reuse.
   That one-line difference is a very common interview question.

Q: Can you avoid sorting?
A: Yes, at a cost: keep a `seen = set()` LOCAL TO EACH NODE and skip a value
   already tried at that node. That is O(n) extra space per level and hashing
   instead of an integer compare, and you lose the `break`. Sorting is
   strictly better when the output order is unconstrained. Worth naming
   because it is the answer if the input arrives as a stream you cannot sort.

Q: Return the combinations in a specific order?
A: Sorting the input gives lexicographic output for free, as in 006/007.

Q: What if the same combination reachable via different elements should count
   as different answers?
A: Then drop the skip entirely — that is just `backtrack(i + 1)` with a sum
   test, and the "duplicates" become the point. Make sure you have asked which
   one the interviewer wants; the problem statement's "unique combinations" is
   doing real work.

Q: Negative numbers in the input?
A: The `break` dies immediately (a bigger value no longer means a worse
   branch) and so does the `remaining < 0` pruning — with negatives you can
   overshoot and come back. You would need to keep exploring and only test
   the sum at the leaves, i.e. the full 2^n subsets tree. This is the same
   "negatives destroy monotone pruning" lesson as topic 07's LC 862.

Q: Parallelise?
A: Fan out on the root's distinct values. Independent subtrees, no shared
   state; distribute dynamically because the smallest value owns the biggest
   subtree.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================

    THE DEDUPE IDIOM `if i > start and a[i] == a[i-1]: continue`, one per shape:
      LC 90   Subsets II            - problem 003. Subsets shape.
      LC 40   Combination Sum II    - HERE. Combinations shape + sum target.
      LC 47   Permutations II       - problem 005. Permutations shape, so the
                                      guard becomes "previous equal value not
                                      currently used" instead of `i > start`.

    THE SUM-TARGET FAMILY:
      LC 39   Combination Sum       - problem 007. Reuse allowed, distinct input.
      LC 40   Combination Sum II    - HERE. No reuse, duplicate input.
      LC 216  Combination Sum III   - problem 009. Fixed k AND fixed sum, digits
                                      1..9, so no duplicates possible at all.
      LC 377  Combination Sum IV    - NOT this shape: it counts PERMUTATIONS and
                                      is a DP. The name is a trap.

    THE COUNTING TWINS (DP, not backtracking):
      LC 494  Target Sum            - 0/1 knapsack with +/- signs
      LC 416  Partition Equal Subset Sum - 0/1 knapsack, target = sum/2
      LC 518  Coin Change II        - the UNBOUNDED counting twin of LC 39

    The tell: "each element used at most once" + "unique combinations" + small
    n = this exact template. If reuse is allowed instead, it is LC 39. If the
    question is "how many", stop and write a DP.
================================================================================
"""

import time
from collections import Counter
from typing import Dict, List


class Solution:
    def combinationSum2(self, candidates: List[int], target: int) -> List[List[int]]:
        """Sort + duplicate-sibling skip + `break`. The answer.
        Sorts a COPY, so the caller's list is untouched."""
        cands = sorted(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])              # COPY
                return
            for i in range(start, n):
                if i > start and cands[i] == cands[i - 1]:
                    continue                         # duplicate SIBLING
                if cands[i] > remaining:
                    break                            # sorted: tail is hopeless
                path.append(cands[i])                # CHOOSE
                backtrack(i + 1, remaining - cands[i])   # EXPLORE — i + 1
                path.pop()                           # UNCHOOSE

        backtrack(0, target)
        return results

    # ------------------------------------------------------------------
    # Alternatives, kept for the comparisons the tests run.
    # ------------------------------------------------------------------
    def combinationSum2_set_dedupe(self, candidates: List[int], target: int) -> List[List[int]]:
        """No skip: build every branch, dedupe with a set at the end.
        Correct, and it constructs every duplicate subtree first."""
        cands = sorted(candidates)
        n = len(cands)
        raw: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                raw.append(path[:])
                return
            for i in range(start, n):
                if cands[i] > remaining:
                    break
                path.append(cands[i])
                backtrack(i + 1, remaining - cands[i])
                path.pop()

        backtrack(0, target)
        seen = set()
        out: List[List[int]] = []
        for c in raw:
            key = tuple(c)
            if key not in seen:
                seen.add(key)
                out.append(c)
        return out

    def combinationSum2_counter(self, candidates: List[int], target: int) -> List[List[int]]:
        """Counter formulation: iterate DISTINCT values, choose how many copies.
        Dedupe becomes structural — there is no second way to pick 'two 1s'.
        O(distinct) work per node instead of O(n)."""
        counts: List[tuple] = sorted(Counter(candidates).items())
        m = len(counts)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(i: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])
                return
            if i == m or counts[i][0] > remaining:
                return
            value, avail = counts[i]
            max_take = min(avail, remaining // value)
            # take 0 first, then 1, 2, ... so output stays lexicographic-ish
            backtrack(i + 1, remaining)
            for taken in range(1, max_take + 1):
                path.append(value)
                backtrack(i + 1, remaining - value * taken)
            for _ in range(max_take):
                path.pop()

        backtrack(0, target)
        return results

    def combinationSum2_dp(self, candidates: List[int], target: int) -> List[List[int]]:
        """0/1-knapsack listing DP over targets, one element at a time.
        Shares no code with the recursion — used as a second oracle."""
        combos: List[List[tuple]] = [[] for _ in range(target + 1)]
        combos[0] = [()]
        for c in sorted(candidates):
            for t in range(target, c - 1, -1):       # DESCENDING: each element once
                for prev in combos[t - c]:
                    combos[t].append(prev + (c,))
        return [list(t) for t in dict.fromkeys(combos[target])]

    # ------------------------------------------------------------------
    # Deliberately broken — the tests prove these are wrong at runtime.
    # ------------------------------------------------------------------
    def combinationSum2_no_skip(self, candidates: List[int], target: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 2: no duplicate-sibling skip. Emits duplicates."""
        cands = sorted(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])
                return
            for i in range(start, n):
                if cands[i] > remaining:
                    break
                path.append(cands[i])
                backtrack(i + 1, remaining - cands[i])
                path.pop()

        backtrack(0, target)
        return results

    def combinationSum2_reuse(self, candidates: List[int], target: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 1: kept 007's `backtrack(i)`, so elements are
        reused even though each may be used only once."""
        cands = sorted(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])
                return
            for i in range(start, n):
                if i > start and cands[i] == cands[i - 1]:
                    continue
                if cands[i] > remaining:
                    break
                path.append(cands[i])
                backtrack(i, remaining - cands[i])       # BUG: i, not i + 1
                path.pop()

        backtrack(0, target)
        return results

    def combinationSum2_wrong_guard(self, candidates: List[int], target: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 3: `i > 0` instead of `i > start`. Forbids the
        second copy of a value even at a deeper node, so [1,1,6] vanishes."""
        cands = sorted(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])
                return
            for i in range(start, n):
                if i > 0 and cands[i] == cands[i - 1]:    # BUG: i > 0
                    continue
                if cands[i] > remaining:
                    break
                path.append(cands[i])
                backtrack(i + 1, remaining - cands[i])
                path.pop()

        backtrack(0, target)
        return results

    def combinationSum2_no_sort(self, candidates: List[int], target: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 4: the skip (and the break) applied without
        sorting. Non-adjacent duplicates are never caught."""
        cands = list(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])
                return
            for i in range(start, n):
                if i > start and cands[i] == cands[i - 1]:
                    continue
                if cands[i] > remaining:
                    break
                path.append(cands[i])
                backtrack(i + 1, remaining - cands[i])
                path.pop()

        backtrack(0, target)
        return results

    def combinationSum2_skip_breaks(self, candidates: List[int], target: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 5: `break` instead of `continue` on the
        duplicate-sibling test, abandoning every larger candidate too."""
        cands = sorted(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])
                return
            for i in range(start, n):
                if i > start and cands[i] == cands[i - 1]:
                    break                                 # BUG: break
                if cands[i] > remaining:
                    break
                path.append(cands[i])
                backtrack(i + 1, remaining - cands[i])
                path.pop()

        backtrack(0, target)
        return results


def _oracle(candidates: List[int], target: int) -> List[List[int]]:
    """Independent bitmask oracle over index subsets. O(2^n) — small inputs."""
    n = len(candidates)
    seen = set()
    for mask in range(1 << n):
        chosen = [candidates[i] for i in range(n) if mask & (1 << i)]
        if sum(chosen) == target:
            seen.add(tuple(sorted(chosen)))
    return [list(t) for t in seen]


def _norm(results):
    return sorted(tuple(sorted(r)) for r in results)


def _count_nodes(candidates: List[int], target: int, skip: bool) -> int:
    """Recursive-call count with and without the duplicate-sibling skip."""
    cands = sorted(candidates)
    n = len(cands)
    count = [0]

    def backtrack(start: int, remaining: int) -> None:
        count[0] += 1
        if remaining == 0:
            return
        for i in range(start, n):
            if skip and i > start and cands[i] == cands[i - 1]:
                continue
            if cands[i] > remaining:
                break
            backtrack(i + 1, remaining - cands[i])

    backtrack(0, target)
    return count[0]


CASES = [
    ([10, 1, 2, 7, 6, 1, 5], 8),
    ([2, 5, 2, 1, 2], 5),
    ([1, 1], 1),
    ([1, 1], 2),
    ([2], 1),
    ([1, 2, 3, 4, 5], 5),
    ([4, 4, 4, 4], 8),
    ([1, 1, 1, 1, 1], 3),
    ([3, 1, 3, 5, 1, 1], 8),
    ([50], 30),
    ([1, 1, 1, 2, 2, 3], 5),
    ([6, 6, 6, 6, 6], 12),
]


# ==============================================================================
# TESTS — run:  python 008_combination_sum_ii_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True

    # ----------------------------------------------------------------------
    # 1. Correctness vs the bitmask oracle.
    # ----------------------------------------------------------------------
    print("--- correctness vs the 2^n bitmask oracle ---")
    impls = [
        ("sort + sibling skip   ", sol.combinationSum2),
        ("backtrack + set dedupe", sol.combinationSum2_set_dedupe),
        ("Counter + count loop  ", sol.combinationSum2_counter),
        ("0/1-knapsack DP       ", sol.combinationSum2_dp),
    ]
    for name, fn in impls:
        ok = True
        for cands, target in CASES:
            want = _norm(_oracle(cands, target))
            got = _norm(fn(list(cands), target))
            if got != want:
                ok = False
                print(f"      {cands} target={target}: got {got} want {want}")
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    no_dupes = all(
        len(sol.combinationSum2(c, t)) == len(_norm(sol.combinationSum2(c, t)))
        and len(_norm(sol.combinationSum2(c, t))) == len(set(_norm(sol.combinationSum2(c, t))))
        for c, t in CASES
    )
    print(f"{'PASS' if no_dupes else 'FAIL'}  output contains no duplicate "
          f"combinations on any case")
    all_ok &= no_dupes

    original = [10, 1, 2, 7, 6, 1, 5]
    sol.combinationSum2(original, 8)
    untouched = original == [10, 1, 2, 7, 6, 1, 5]
    print(f"{'PASS' if untouched else 'FAIL'}  input list not mutated: {original}")
    all_ok &= untouched

    # ----------------------------------------------------------------------
    # 2. ⚠️ THE DEMO — the same input, with and without the sibling skip.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the duplicate-sibling skip, removed: same input, both ways ---")
    cands, target = [10, 1, 2, 7, 6, 1, 5], 8
    good = sol.combinationSum2(cands, target)
    bad = sol.combinationSum2_no_skip(cands, target)
    print(f"  candidates={cands}, target={target}   (sorted: {sorted(cands)})")
    print(f"  WITH the skip    -> {len(good)} results  {sorted(good)}")
    print(f"  WITHOUT the skip -> {len(bad)} results  {sorted(bad)}")
    from collections import Counter as _C
    dupes = [k for k, v in _C(tuple(b) for b in bad).items() if v > 1]
    print(f"  emitted twice: {[list(d) for d in dupes]}")
    print("  Both 1s can start a combination that uses exactly ONE 1, so every")
    print("  such answer arrives twice — once via index 0, once via index 1.")
    print("  Note [1,1,6] is NOT duplicated: it needs both 1s, and there is")
    print("  only one way to take both. That asymmetry is the clearest proof")
    print("  that the rule is about SIBLINGS, not about values.")
    all_ok &= len(dupes) > 0 and len(bad) > len(good)

    print("\n  Same comparison across inputs:")
    print(f"  {'candidates':<26} {'tgt':>4} {'with skip':>10} {'no skip':>8} "
          f"{'duplicate results':>18}")
    for cands, target in ([10, 1, 2, 7, 6, 1, 5], 8), ([1, 1, 1, 1, 1], 3), \
                         ([4, 4, 4, 4], 8), ([1, 1, 1, 2, 2, 3], 5), \
                         ([6, 6, 6, 6, 6], 12):
        g = len(sol.combinationSum2(cands, target))
        b = len(sol.combinationSum2_no_skip(cands, target))
        print(f"  {str(cands):<26} {target:>4} {g:>10} {b:>8} {b - g:>18}")
    print("  [1,1,1,1,1] target 3: ONE answer, but C(5,3) = 10 index-subsets")
    print("  produce it. The skip is what turns 10 branches into 1.")

    # ----------------------------------------------------------------------
    # 3. ⚠️ MISTAKE 1 — keeping 007's backtrack(i).
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  backtrack(i + 1) vs 007's backtrack(i) ---")
    print(f"  {'candidates':<20} {'tgt':>4} {'i+1 (right)':>12} {'i (reuse bug)':>14}")
    reuse_bug = False
    for cands, target in ([1, 2, 5], 5), ([10, 1, 2, 7, 6, 1, 5], 8), \
                         ([2, 3], 6):
        g = sol.combinationSum2(cands, target)
        b = sol.combinationSum2_reuse(cands, target)
        reuse_bug |= _norm(g) != _norm(b)
        print(f"  {str(cands):<20} {target:>4} {len(g):>12} {len(b):>14}")
    print(f"  On [1,2,5] target 5 the reuse bug emits {sorted(sol.combinationSum2_reuse([1, 2, 5], 5))}")
    print(f"  where the truth is {sorted(sol.combinationSum2([1, 2, 5], 5))} — it")
    print("  used the single 1 five times and the single 2 twice.")
    all_ok &= reuse_bug

    # ----------------------------------------------------------------------
    # 4. ⚠️ MISTAKE 3 — `i > 0` instead of `i > start` (the opposite bug).
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `i > start` vs `i > 0`: over- vs under-counting ---")
    print(f"  {'candidates':<26} {'tgt':>4} {'i>start':>8} {'i>0':>6} "
          f"{'no skip':>8}  lost by i>0")
    guard_bug = False
    for cands, target in ([1, 1], 2), ([10, 1, 2, 7, 6, 1, 5], 8), \
                         ([1, 1, 1, 1, 1], 3), ([4, 4, 4, 4], 8):
        a = len(sol.combinationSum2(cands, target))
        b = len(sol.combinationSum2_wrong_guard(cands, target))
        c = len(sol.combinationSum2_no_skip(cands, target))
        guard_bug |= b < a
        print(f"  {str(cands):<26} {target:>4} {a:>8} {b:>6} {c:>8}  {a - b}")
    print("  Three columns, three behaviours: `i > start` is right, `i > 0`")
    print("  UNDERCOUNTS (it forbids reusing a VALUE at a deeper node, which is")
    print("  legal), no skip OVERCOUNTS. [1,1] target 2 is the minimal case:")
    print(f"  correct {sol.combinationSum2([1, 1], 2)}, "
          f"`i > 0` gives {sol.combinationSum2_wrong_guard([1, 1], 2)}.")
    all_ok &= guard_bug

    # ----------------------------------------------------------------------
    # 5. ⚠️ MISTAKE 4 — the skip without sorting.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the skip WITHOUT sorting first ---")
    print(f"  {'candidates':<26} {'tgt':>4} {'sorted':>7} {'unsorted':>9}  ok?")
    sort_bug = False
    for cands, target in ([2, 5, 2, 1, 2], 5), ([3, 1, 3, 5, 1, 1], 8), \
                         ([1, 2, 1], 2), ([1, 1, 2], 2):
        a = _norm(sol.combinationSum2(cands, target))
        b = _norm(sol.combinationSum2_no_sort(cands, target))
        mism = a != b
        sort_bug |= mism
        print(f"  {str(cands):<26} {target:>4} {len(a):>7} {len(b):>9}  "
              f"{'yes' if not mism else 'NO  <- wrong'}")
    print("  Unsorted input breaks the code in TWO independent ways, and which")
    print("  one shows up depends on the input — some inputs (like [2,5,2,1,2]")
    print("  at target 5) happen to survive both:")
    print("    (a) the skip test compares ADJACENT entries, so non-adjacent")
    print("        equal values are never caught and duplicates come out —")
    print("        that is [3,1,3,5,1,1] above;")
    print("    (b) the `break` needs ascending order, so a big value sitting in")
    print("        front of a small one kills real answers — that is [1,2,1]")
    print("        target 2: the root picks the 1 at index 0, the child sees")
    print("        cands[1]=2 > remaining=1, BREAKS, and never reaches the 1 at")
    print("        index 2, so [1,1] is lost.")
    print("  One `sort()` fixes both, which is why it is a prerequisite rather")
    print("  than a tweak — and why 'it passed my tests' proves nothing here.")
    all_ok &= sort_bug

    # ----------------------------------------------------------------------
    # 6. ⚠️ MISTAKE 5 — `break` instead of `continue` on the skip.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  duplicate-sibling test: `continue` vs `break` ---")
    print(f"  {'candidates':<26} {'tgt':>4} {'continue':>9} {'break':>6}  lost")
    cb_bug = False
    for cands, target in ([1, 1, 2, 5], 7), ([1, 1, 6], 7), ([2, 2, 3], 5), \
                         ([1, 1, 1, 5], 6):
        a = sol.combinationSum2(cands, target)
        b = sol.combinationSum2_skip_breaks(cands, target)
        mism = _norm(a) != _norm(b)
        cb_bug |= mism
        print(f"  {str(cands):<26} {target:>4} {len(a):>9} {len(b):>6}  "
              f"{len(a) - len(b)}{'  <- answers lost' if mism else ''}")
    print("  `break` on a duplicate sibling throws away every LARGER candidate")
    print("  at that node too. On [1,1,2,5] target 7 it loses [1,1,5]: it hits")
    print("  the second 1 at the root, breaks, and never reaches 2 or 5.")
    all_ok &= cb_bug

    # ----------------------------------------------------------------------
    # 7. Nodes visited: the skip vs generate-then-dedupe. MEASURED.
    # ----------------------------------------------------------------------
    print("\n--- nodes visited: sibling skip vs build-everything-then-dedupe ---")
    print(f"  {'input':<22} {'tgt':>4} {'answers':>8} {'with skip':>10} "
          f"{'no skip':>9} {'ratio':>8}")
    prune_ok = True
    for label, cands, target in (("[1]*10", [1] * 10, 5),
                                 ("[1]*14", [1] * 14, 7),
                                 ("[1]*18", [1] * 18, 9),
                                 ("[2]*16+[1]*4", [2] * 16 + [1] * 4, 10),
                                 ("[1,2,3]*6", [1, 2, 3] * 6, 9)):
        answers = len(sol.combinationSum2(cands, target))
        a = _count_nodes(cands, target, True)
        b = _count_nodes(cands, target, False)
        prune_ok &= a <= b
        print(f"  {label:<22} {target:>4} {answers:>8} {a:>10} {b:>9} "
              f"{b / a:>7.1f}x")
    print("  [1]*18 with target 9: C(18,9) = 48,620 index-subsets all sum to 9")
    print("  and all describe the SAME answer. The skip collapses a run of k")
    print("  equal values from 2^k branches to k+1 — exponential to linear on")
    print("  that run. This is the measurement that justifies the whole idiom.")
    all_ok &= prune_ok

    print("\n--- wall clock (ms) on the same inputs ---")
    print(f"  {'input':<22} {'tgt':>4} {'skip':>9} {'set dedupe':>12} "
          f"{'Counter':>9} {'ratio':>8}")
    for label, cands, target in (("[1]*14", [1] * 14, 7),
                                 ("[1]*18", [1] * 18, 9),
                                 ("[1]*20", [1] * 20, 10),
                                 ("[1,2,3]*6", [1, 2, 3] * 6, 9)):
        t0 = time.perf_counter(); sol.combinationSum2(cands, target)
        t1 = time.perf_counter(); sol.combinationSum2_set_dedupe(cands, target)
        t2 = time.perf_counter(); sol.combinationSum2_counter(cands, target)
        t3 = time.perf_counter()
        a, b, c = (t1 - t0) * 1e3, (t2 - t1) * 1e3, (t3 - t2) * 1e3
        print(f"  {label:<22} {target:>4} {a:>8.3f}ms {b:>11.3f}ms "
              f"{c:>8.3f}ms {b / a:>7.1f}x")

    # ----------------------------------------------------------------------
    # 8. The follow-up, measured: what if a value repeats thousands of times?
    # ----------------------------------------------------------------------
    print("\n--- follow-up measured: 3,000 copies of one value ---")
    heavy = [1] * 3000 + [2, 3, 5]
    t0 = time.perf_counter(); r1 = sol.combinationSum2(heavy, 8)
    t1 = time.perf_counter(); r2 = sol.combinationSum2_counter(heavy, 8)
    t2 = time.perf_counter()
    a, b = (t1 - t0) * 1e3, (t2 - t1) * 1e3
    print(f"  candidates = [1]*3000 + [2,3,5], target = 8")
    print(f"  sibling skip : {len(r1):>3} answers in {a:>8.2f} ms")
    print(f"  Counter      : {len(r2):>3} answers in {b:>8.2f} ms   "
          f"({a / b:.0f}x faster)")
    print("  Both are correct. The sibling-skip loop still ITERATES over all")
    print("  3,000 equal entries at every node just to `continue` past 2,999")
    print("  of them; the Counter version iterates over 4 DISTINCT values. If")
    print("  an interviewer raises multiplicity, this is the answer to give.")
    all_ok &= _norm(r1) == _norm(r2)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
