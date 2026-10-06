"""
================================================================================
SOLUTION · LeetCode 39 · Combination Sum                                [Medium]
https://leetcode.com/problems/combination-sum/
================================================================================

THE CORE IDEA
--------------
This is problem 006 (Combinations) with ONE CHARACTER changed:

    backtrack(i + 1)     ->     backtrack(i)

That is the entire problem. `i + 1` means "only elements strictly after me",
which is "each element at most once". `i` means "you may pick me again", which
is "each element unlimited times". Everything else — the `start` index, the
choose/explore/unchoose skeleton, the `path[:]` copy at the leaf — is identical
to 006.

    backtrack(i + 1)   each element at most once     LC 77, LC 40, LC 90
    backtrack(i)       each element unlimited        LC 39  <- HERE
    backtrack(0)       WRONG: every ORDERING of every answer

The third line is the mistake to understand rather than memorise. If the loop
restarts at 0 on every call, [2,2,3], [2,3,2] and [3,2,2] all get emitted — the
same combination three times. `start` is what makes each multiset reachable by
exactly ONE path in the tree, and that is the only reason no dedupe pass is
needed at the end.

The leaf test also changes: 006 stopped at `len(path) == k`, here it is
`remaining == 0`. Carry `remaining` DOWN as a parameter instead of re-summing
`path` at each node — re-summing turns an O(1) test into O(depth) and, since it
runs at every node of the tree, it multiplies the whole algorithm by the depth.
Measured below.

THE SECOND IDEA — sort, then `break` instead of `continue`
-----------------------------------------------------------
The answer does not depend on the order of `candidates`, so you are free to
sort. Do it: once the array is ascending, the moment `candidates[i] > remaining`
every LATER candidate is also too big, so you can leave the loop entirely.

    for i in range(start, n):
        if candidates[i] > remaining:
            break            # not `continue` — everything after is worse too
        ...

`continue` is correct and tests each remaining candidate one at a time.
`break` abandons the whole tail of the loop at once. On top of that, sorting
makes the SMALL candidates get tried first, which reaches the deep leaves
earlier and keeps the surviving subtrees narrow. The node-count table in the
tests measures both effects separately — sorting alone, and sorting plus
`break` — because they are two different savings and it is worth seeing which
one carries the weight.

WHY THE RECURSION TERMINATES AT ALL
------------------------------------
"Reuse an element unlimited times" plus `backtrack(i)` is an infinite loop
waiting to happen, and the ONLY thing preventing it is the constraint
`2 <= candidates[i]`. Every chosen element strictly decreases `remaining`, so
the depth is bounded by `target // min(candidates)`. Put a 0 in `candidates`
and the same code recurses forever. The tests do exactly that and catch the
`RecursionError`, because "why is this guaranteed to terminate?" is a standard
follow-up and the answer lives in the constraints, not in the code.

================================================================================
MULTIPLE APPROACHES
================================================================================

1. ENUMERATE EVERY MULTISET, THEN FILTER          (brute force — priced only)
   For each candidate, choose a count from 0 to `target // candidate`, take the
   cross product, keep the ones summing to target. That is
   `prod(target/c_i + 1)` combinations — for candidates [2,3,5,7] and
   target 40 it is 21*14*9*6 = 15,876 (fine), but the product blows up with n
   and the work is spent on candidates that already overshot at the first pick.
   Backtracking is the same enumeration with the overshooting branches cut at
   their root instead of at the leaf.

2. BACKTRACKING, `backtrack(i)`                                <- the baseline
   The template above with no pruning beyond `remaining < 0` at entry.
   Correct, and the version to get on the board first.

3. BACKTRACKING + SORT + `break`                             <- the answer
   Same output, strictly fewer nodes. What you write once the basic version
   works. Cost: O(n log n) once, which is free next to an exponential tree.

4. COUNT-BASED RECURSION ("how many of candidate i do I take?")
   Instead of "pick one and recurse on the same index", loop over the COUNT
   `c` from 0 to `remaining // candidates[i]` and recurse on `i + 1`. Same
   result set, a bushier and shallower tree (depth n instead of
   target/min). Worth knowing: it is the shape that turns into the coin-change
   DP, and it is the natural formulation if the interviewer asks for counts
   per candidate rather than a flat list.

5. DP OVER TARGETS (`combos[t]` = list of combinations summing to t)
   Build bottom-up: for t in 1..target, for each candidate c <= t, extend every
   combination in `combos[t-c]` whose largest element is <= c. Correct, and it
   is the right tool if you are asked "HOW MANY combinations" (LC 518) rather
   than "list them", because then you store counts instead of lists. For
   listing, it allocates every intermediate list for every intermediate target
   and loses to backtracking. Used below as the independent oracle precisely
   because it shares no code with the recursion.

================================================================================
STEP BY STEP  ·  candidates = [2, 3, 6, 7]  (sorted),  target = 7
================================================================================

`rem` is what is left of the target. The `start` index of each call is shown as
`s=`. Note every recursive call passes `i`, NOT `i + 1`.

    backtrack(s=0, rem=7, path=[])
    |
    +-- i=0 pick 2 -> path=[2]   backtrack(s=0, rem=5)
    |   |                         (s stays 0: 2 is reusable)
    |   +-- i=0 pick 2 -> [2,2]  backtrack(s=0, rem=3)
    |   |   +-- i=0 pick 2 -> [2,2,2] backtrack(s=0, rem=1)
    |   |   |     i=0: 2 > 1 -> BREAK (sorted, so 3, 6, 7 are hopeless too)
    |   |   |     dead end, return
    |   |   +-- i=1 pick 3 -> [2,2,3] rem=0  ==> EMIT [2,2,3]
    |   |   +-- i=2: 6 > 3 -> BREAK
    |   |   pop
    |   +-- i=1 pick 3 -> [2,3]  backtrack(s=1, rem=2)
    |   |     i=1: 3 > 2 -> BREAK        (cannot go back to the 2 at index 0:
    |   |     dead end                    s=1 forbids it, which is what stops
    |   |                                 [2,3,2] from being generated)
    |   +-- i=2: 6 > 5 -> BREAK
    |   pop
    |
    +-- i=1 pick 3 -> path=[3]  backtrack(s=1, rem=4)
    |   +-- i=1 pick 3 -> [3,3] backtrack(s=1, rem=1)
    |   |     i=1: 3 > 1 -> BREAK, dead end
    |   +-- i=2: 6 > 4 -> BREAK
    |   pop
    |
    +-- i=2 pick 6 -> path=[6]  backtrack(s=2, rem=1)
    |   |   i=2: 6 > 1 -> BREAK, dead end
    |   pop
    |
    +-- i=3 pick 7 -> path=[7]  rem=0  ==> EMIT [7]
        pop

    Result: [[2,2,3], [7]]   correct.

TWO THINGS TO READ OFF THAT TREE:

  (a) [2,2,3] exists only because the call passes `i`. With `i + 1` the whole
      `[2,2,...]` branch is unreachable and the answer collapses to [[7]].

  (b) [2,3,2] is never generated, even though 2 is reusable, because the branch
      that picked 3 recurses with `s=1` and can no longer reach index 0. That
      is the `start` index doing its one job: canonicalising each multiset to
      its non-decreasing ordering.

The state of `path` over time — one shared list, mutated in place:

    [] [2] [2,2] [2,2,2] [2,2] [2,2,3] [2,2] [2] [2,3] [2] [] [3] [3,3] ...

Every EMIT must copy (`path[:]`); `path` is about to be mutated back.

================================================================================
COMPLEXITY SUMMARY
================================================================================

    Let  T = target,  m = min(candidates),  n = len(candidates),
         D = T // m  (the maximum depth).

    Approach                      Time              Space         Mutates input?
    ----------------------------  ----------------  ------------  --------------
    Enumerate multisets + filter  O(prod(T/c_i+1))  O(n)          no
    Backtracking, no pruning      O(n^D)            O(D) stack    no
    Backtracking + sort + break   O(n^D) worst      O(D) stack    no*  (see below)
    Count-based recursion         O(n^D)            O(n + D)      no
    DP over targets (listing)     O(T * n * out)    O(T * out)    no

    * The `sort` question: `candidates.sort()` mutates the caller's list, which
      LeetCode does not care about and an interviewer might. `candidates =
      sorted(candidates)` rebinds a new list and leaves the input untouched for
      O(n) extra space. This solution does the non-mutating version and says so
      — "I'd sort a copy unless you tell me in-place is fine" is a free point.

    The honest statement about the exponent: this problem has NO polynomial
    algorithm, because the OUTPUT can be exponentially large — you cannot list
    2^k things in polynomial time. So O(n^D) is not a weakness of backtracking;
    it is the size of the answer. The right thing to say in an interview is
    "time is O(number of nodes in the tree), the tree is bounded by branching n
    and depth target/min, and the output-size lower bound means no algorithm
    beats it asymptotically." Then add that sorting + `break` cuts the CONSTANT
    hard, and give the measured factor rather than a guess.

    Pruning does not change the class. The node-count table below shows what it
    actually changes.

================================================================================
EDGE CASES
================================================================================

    candidates=[2], target=1   -> []. Target smaller than every candidate; the
                                  loop breaks immediately at depth 0. A
                                  solution that only checks `remaining == 0`
                                  after appending (rather than before
                                  recursing) still works but wastes a level.

    candidates=[8], target=8   -> [[8]]. Single element, single use. Catches an
                                  off-by-one where `remaining == 0` is tested
                                  before the append instead of after.

    unsorted input [7,3,2]     -> must still return [[2,2,3],[7]]. The answer
                                  is order-independent; if you rely on `break`
                                  you MUST sort first, or `break` cuts off
                                  candidates that were still viable. This is in
                                  the question file's test cases on purpose.

    target divisible by min    -> the deepest possible path, e.g. [2], target
                                  40 gives one answer of length 20. Confirms
                                  the depth bound target//min is real and that
                                  recursion depth is not a problem at
                                  LeetCode's limits (40 // 2 = 20 frames).

    duplicates in candidates   -> NOT in this problem's constraints ("all
                                  elements are distinct"), and worth flagging
                                  out loud, because if they were allowed this
                                  exact code emits duplicate combinations. The
                                  fix is LC 40 (problem 008): sort, no reuse,
                                  and skip duplicate siblings. Demonstrated
                                  live below.

    a 0 or a negative in candidates -> NOT in the constraints, and it is the
                                  reason the constraints exist: `backtrack(i)`
                                  on a 0 never decreases `remaining` and
                                  recurses until the interpreter stops it. The
                                  tests trigger the RecursionError on purpose.

================================================================================
COMMON MISTAKES
================================================================================

1. `backtrack(i + 1)` — copying problem 006 verbatim.
   Silently forbids reuse, so [2,2,3] disappears and only [[7]] comes back. It
   never crashes, and the output is a strict SUBSET of the right answer, which
   makes it easy to miss on a small test. Printed side by side below.

2. `backtrack(0)` or `backtrack(start)` where `start` never advances.
   Emits every ORDERING of every combination: [2,2,3], [2,3,2], [3,2,2]. The
   count blows up by a factor of the multinomial coefficient. Also printed
   below.

3. `results.append(path)` instead of `results.append(path[:])`.
   The copy-on-append trap. Every entry ends up being the same list object,
   which is empty by the time the recursion unwinds.

4. Re-summing `path` at every node (`if sum(path) == target`).
   Correct, and it makes every node O(depth) instead of O(1). Benchmarked
   below — the cost is real, not theoretical.

5. `continue` instead of `break` after sorting.
   Correct but leaves the pruning half-done: it rejects one candidate at a
   time instead of the whole ascending tail. Node counts below.

6. `break` WITHOUT sorting.
   Now it is a correctness bug, not just a lost optimisation: on [7,3,2] with
   target 7, `7 > remaining` is false at first but the moment a large
   candidate appears before a small viable one, `break` discards the small
   one. Sorting is a PREREQUISITE for `break`, not a companion optimisation.
   Demonstrated live.

7. Checking `remaining < 0` only at the top of the call instead of before
   recursing.
   Works, wastes one whole level of the tree (you allocate a frame, append,
   then immediately fail). With sorting you can avoid ever making the call.

8. Deduping the output with a set at the end.
   Produces the right answer while doing multinomial-factor extra work, and
   reads to an interviewer as not knowing what `start` is for.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================

Q: How many combinations are there — don't list them?
A: Completely different problem: DP, not backtracking. `dp[0] = 1`, then for
   each candidate c (outer loop) for t in c..target (inner loop)
   `dp[t] += dp[t-c]`. O(n * target) time, O(target) space. That is LC 518
   (Coin Change II). The loop ORDER is the whole subtlety: candidates outer
   counts COMBINATIONS, target outer counts PERMUTATIONS (LC 377). Being able
   to say which order gives which is the point of the question.

Q: Minimum number of elements summing to target?
A: LC 322 Coin Change, again DP: `dp[t] = 1 + min(dp[t-c])`. O(n * target).
   Do not backtrack for an optimum when the subproblems overlap — that is
   exactly the Fibonacci-vs-Subsets fork from problem 001 and the topic guide
   Part 6.

Q: What if candidates can contain duplicates?
A: Then this code emits duplicate combinations. Sort, switch to
   `backtrack(i + 1)`, and skip duplicate siblings with
   `if i > start and candidates[i] == candidates[i-1]: continue`. That is
   LC 40, problem 008 — and note that BOTH changes are needed, not just one.

Q: What if each candidate has a limited supply (say, at most 3 of each)?
A: The count-based formulation (approach 4) handles it directly: cap the count
   loop at `min(supply[i], remaining // candidates[i])`. This is the "bounded
   knapsack" shape.

Q: Cap the combination length at k as well?
A: Add `len(path) == k` as a second leaf condition and prune when
   `len(path) + ceil(remaining / max_candidate) > k`. With a fixed k and a
   fixed digit set that is LC 216 (problem 009), which does exactly this
   two-sided pruning.

Q: Can memoization help?
A: Not for LISTING. Two different paths reaching the same `(start, remaining)`
   have different prefixes, so the cached suffix-lists would have to be
   concatenated onto every prefix — you can do it (cache the list of suffix
   combinations per `(start, remaining)`), and it saves real work when many
   prefixes share a suffix, at the cost of O(states * output) memory. For
   COUNTING it is the DP above and it is a pure win. Knowing which of the two
   memoization helps is the actual answer here.

Q: Return combinations in sorted order?
A: Sort `candidates` first (you already did) and the output is
   lexicographically ordered for free, exactly as in problem 006.

Q: Parallelise?
A: Fan out on the first level — subtree i handles all combinations whose
   smallest element is `candidates[i]`. No shared state. The subtrees are
   wildly unbalanced (the smallest candidate owns the deepest tree), so
   distribute dynamically.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================

    THE FOUR AXES that generate this whole topic. Combination Sum is one point
    in the space; every neighbour is one axis flipped:

      shape:      subsets / permutations / combinations
      reuse:      allowed (recurse i) / not (recurse i+1)
      duplicates: in the input / not
      length:     fixed k / any

    recurse i,   distinct input, any length   -> Combination Sum      LC 39 HERE
    recurse i+1, DUPLICATE input, any length  -> Combination Sum II   LC 40 (008)
    recurse i+1, distinct 1..9, FIXED k       -> Combination Sum III  LC 216 (009)
    recurse i+1, distinct input, any length   -> Subsets              LC 78 (002)
    recurse i+1, DUPLICATE input, any length  -> Subsets II           LC 90 (003)
    recurse i+1, distinct input, FIXED k      -> Combinations         LC 77 (006)
    used[] instead of start                   -> Permutations         LC 46 (004)

    THE COUNTING / OPTIMISING TWINS — these are DP, not backtracking:
      LC 518  Coin Change II          - how MANY combinations (candidates outer)
      LC 377  Combination Sum IV      - how many PERMUTATIONS (target outer)
      LC 322  Coin Change             - FEWEST elements summing to target
      LC 279  Perfect Squares         - LC 322 with candidates = squares
      LC 139  Word Break              - same shape over strings, memoized

    The tell for backtracking rather than DP: the problem says "return all" /
    "list every". The tell for DP: "how many", "minimum", "is it possible".
    Same tree, different question, completely different tool.
================================================================================
"""

import sys
import time
from typing import List


class Solution:
    def combinationSum(self, candidates: List[int], target: int) -> List[List[int]]:
        """Sorted candidates + backtrack(i) + `break` pruning. The answer.
        Sorts a COPY, so the caller's list is untouched."""
        cands = sorted(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])          # COPY — path is about to change
                return
            for i in range(start, n):
                if cands[i] > remaining:
                    break                        # sorted: the whole tail is hopeless
                path.append(cands[i])            # CHOOSE
                backtrack(i, remaining - cands[i])  # EXPLORE — `i`, not `i + 1`
                path.pop()                       # UNCHOOSE

        backtrack(0, target)
        return results

    # ------------------------------------------------------------------
    # Alternatives, kept for the comparisons the tests run.
    # ------------------------------------------------------------------
    def combinationSum_unpruned(self, candidates: List[int], target: int) -> List[List[int]]:
        """No sort, no break: reject only after overshooting. Correct."""
        n = len(candidates)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])
                return
            if remaining < 0:
                return
            for i in range(start, n):
                path.append(candidates[i])
                backtrack(i, remaining - candidates[i])
                path.pop()

        backtrack(0, target)
        return results

    def combinationSum_sorted_continue(self, candidates: List[int], target: int) -> List[List[int]]:
        """Sorted, but `continue` instead of `break`: rejects one candidate at
        a time rather than the whole ascending tail."""
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
                    continue                     # correct, but keeps looping
                path.append(cands[i])
                backtrack(i, remaining - cands[i])
                path.pop()

        backtrack(0, target)
        return results

    def combinationSum_counts(self, candidates: List[int], target: int) -> List[List[int]]:
        """Count-based: 'how many of candidate i do I take?', then i + 1.
        Same results, bushier and shallower tree (depth n, not target/min).
        This is the shape that becomes the coin-change DP."""
        cands = sorted(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(i: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])
                return
            if i == n or cands[i] > remaining:
                return
            max_count = remaining // cands[i]
            for c in range(max_count + 1):
                path.extend([cands[i]] * c) if c else None
                backtrack(i + 1, remaining - cands[i] * c)
                for _ in range(c):
                    path.pop()

        backtrack(0, target)
        return results

    def combinationSum_dp(self, candidates: List[int], target: int) -> List[List[int]]:
        """Bottom-up DP over targets. Shares no code with the recursion, which
        is why the tests use it as the independent oracle. Only extends with
        candidates >= the combination's current maximum, which is the
        non-decreasing canonical form the `start` index enforces."""
        cands = sorted(set(candidates))
        combos: List[List[List[int]]] = [[] for _ in range(target + 1)]
        combos[0] = [[]]
        for t in range(1, target + 1):
            for c in cands:
                if c > t:
                    break
                for prev in combos[t - c]:
                    if not prev or prev[-1] <= c:
                        combos[t].append(prev + [c])
        return combos[target]

    # ------------------------------------------------------------------
    # Deliberately broken — the tests prove these are wrong at runtime.
    # ------------------------------------------------------------------
    def combinationSum_no_reuse(self, candidates: List[int], target: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 1: `backtrack(i + 1)`, copied from LC 77. Forbids
        reuse, so the answer is a strict subset of the truth."""
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
                backtrack(i + 1, remaining - cands[i])     # BUG: i + 1
                path.pop()

        backtrack(0, target)
        return results

    def combinationSum_restart(self, candidates: List[int], target: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 2: the loop restarts at 0 every call, so every
        ORDERING of every combination is emitted."""
        cands = sorted(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])
                return
            for i in range(n):                              # BUG: ignores start
                if cands[i] > remaining:
                    break
                path.append(cands[i])
                backtrack(remaining - cands[i])
                path.pop()

        backtrack(target)
        return results

    def combinationSum_break_unsorted(self, candidates: List[int], target: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 6: `break` without sorting first. Discards
        viable small candidates sitting behind a large one."""
        n = len(candidates)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path[:])
                return
            for i in range(start, n):
                if candidates[i] > remaining:
                    break                                   # BUG: not sorted
                path.append(candidates[i])
                backtrack(i, remaining - candidates[i])
                path.pop()

        backtrack(0, target)
        return results

    def combinationSum_resum(self, candidates: List[int], target: int) -> List[List[int]]:
        """MISTAKE 4: recomputes sum(path) at every node instead of carrying
        `remaining` down. Correct, and O(depth) per node instead of O(1)."""
        cands = sorted(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int) -> None:
            total = sum(path)                               # O(depth), every node
            if total == target:
                results.append(path[:])
                return
            for i in range(start, n):
                if cands[i] > target - total:
                    break
                path.append(cands[i])
                backtrack(i)
                path.pop()

        backtrack(0)
        return results

    def combinationSum_no_copy(self, candidates: List[int], target: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 3: appends the live list instead of a copy."""
        cands = sorted(candidates)
        n = len(cands)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, remaining: int) -> None:
            if remaining == 0:
                results.append(path)                        # BUG: no [:]
                return
            for i in range(start, n):
                if cands[i] > remaining:
                    break
                path.append(cands[i])
                backtrack(i, remaining - cands[i])
                path.pop()

        backtrack(0, target)
        return results


def _norm(results: List[List[int]]):
    return sorted(tuple(sorted(r)) for r in results)


def _count_nodes(candidates: List[int], target: int, do_sort: bool, do_break: bool) -> int:
    """Count recursive calls for a given pruning configuration."""
    cands = sorted(candidates) if do_sort else list(candidates)
    n = len(cands)
    count = [0]
    path: List[int] = []

    def backtrack(start: int, remaining: int) -> None:
        count[0] += 1
        if remaining == 0:
            return
        if remaining < 0:
            return
        for i in range(start, n):
            if do_break and cands[i] > remaining:
                break
            path.append(cands[i])
            backtrack(i, remaining - cands[i])
            path.pop()

    backtrack(0, target)
    return count[0]


CASES = [
    ([2, 3, 6, 7], 7),
    ([2, 3, 5], 8),
    ([2], 1),
    ([7, 3, 2], 7),
    ([8], 8),
    ([2], 40),
    ([3, 5, 8], 11),
    ([2, 3, 5, 7, 11], 20),
    ([9, 4, 6, 2, 3], 15),
    ([40], 40),
    ([2, 4, 6, 8], 9),
]


# ==============================================================================
# TESTS — run:  python 007_combination_sum_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True

    # ----------------------------------------------------------------------
    # 1. Correctness of every CORRECT implementation vs the DP oracle.
    # ----------------------------------------------------------------------
    print("--- correctness vs the bottom-up DP oracle (shares no code) ---")
    impls = [
        ("sorted + break        ", sol.combinationSum),
        ("unpruned, unsorted    ", sol.combinationSum_unpruned),
        ("sorted + continue     ", sol.combinationSum_sorted_continue),
        ("count-based           ", sol.combinationSum_counts),
        ("re-sums path (slow)   ", sol.combinationSum_resum),
    ]
    for name, fn in impls:
        ok = True
        for cands, target in CASES:
            want = _norm(sol.combinationSum_dp(cands, target))
            got = _norm(fn(list(cands), target))
            if got != want:
                ok = False
                print(f"      {cands} target={target}: got {got} want {want}")
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # Sum check: every emitted combination really sums to target.
    sums_ok = all(
        sum(c) == t for cands, t in CASES for c in sol.combinationSum(cands, t)
    )
    print(f"{'PASS' if sums_ok else 'FAIL'}  every emitted combination sums to target")
    all_ok &= sums_ok

    # The caller's list must not be mutated (we sorted a copy).
    original = [7, 3, 2]
    sol.combinationSum(original, 7)
    untouched = original == [7, 3, 2]
    print(f"{'PASS' if untouched else 'FAIL'}  input list not mutated "
          f"(sorted a copy): {original}")
    all_ok &= untouched

    # ----------------------------------------------------------------------
    # 2. ⚠️ THE ONE-CHARACTER DIFFERENCE — backtrack(i) vs (i+1) vs (0).
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  backtrack(i)  vs  backtrack(i+1)  vs  backtrack(0) ---")
    cands, target = [2, 3, 6, 7], 7
    right = sol.combinationSum(cands, target)
    no_reuse = sol.combinationSum_no_reuse(cands, target)
    restart = sol.combinationSum_restart(cands, target)
    print(f"  candidates={cands}, target={target}")
    print(f"  backtrack(i)     -> {len(right):>2} results  {sorted(right)}"
          f"   <- correct")
    print(f"  backtrack(i + 1) -> {len(no_reuse):>2} results  {sorted(no_reuse)}"
          f"   <- lost [2,2,3]: reuse forbidden")
    print(f"  backtrack(0)     -> {len(restart):>2} results  {sorted(restart)}")
    dup_free = len(restart) - len({tuple(sorted(r)) for r in restart})
    print(f"                      {dup_free} of those are re-orderings of a")
    print("                      combination already listed. `start` is the only")
    print("                      thing that canonicalises each multiset.")
    demo_ok = (len(no_reuse) < len(right)) and dup_free > 0
    all_ok &= demo_ok

    print("\n  The same three, on a bigger input:")
    print(f"  {'candidates':<20} {'target':>7} {'i (right)':>10} "
          f"{'i+1 (subset)':>13} {'0 (dups)':>10}")
    for cands, target in ([2, 3, 5], 12), ([2, 3, 5, 7], 15), ([2, 3, 4], 10):
        a = len(sol.combinationSum(cands, target))
        b = len(sol.combinationSum_no_reuse(cands, target))
        c = len(sol.combinationSum_restart(cands, target))
        print(f"  {str(cands):<20} {target:>7} {a:>10} {b:>13} {c:>10}")
    print("  `i+1` always UNDERCOUNTS (a subset of the truth), `0` always")
    print("  OVERCOUNTS (permutations of the truth). Two opposite bugs from")
    print("  the same line of code.")

    # ----------------------------------------------------------------------
    # 3. ⚠️ MISTAKE 6 — `break` requires sorting. Correctness, not speed.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `break` WITHOUT sorting first: a correctness bug ---")
    print(f"  {'candidates':<20} {'target':>7} {'sorted+break':>13} "
          f"{'break, unsorted':>16}  ok?")
    unsorted_bug = False
    for cands, target in ([7, 3, 2], 7), ([9, 2, 3], 11), ([6, 2, 4], 8), \
                         ([2, 3, 6, 7], 7):
        good = len(sol.combinationSum(cands, target))
        bad = len(sol.combinationSum_break_unsorted(cands, target))
        mism = good != bad
        unsorted_bug |= mism
        print(f"  {str(cands):<20} {target:>7} {good:>13} {bad:>16}  "
              f"{'yes' if not mism else 'NO  <- answers lost'}")
    print("  Note [7,3,2] target 7 AGREES — the bug needs a large candidate to")
    print("  sit in front of a small one at a node where the small one still")
    print("  fits. [9,2,3] target 11 is such a case: the root picks 9, and in")
    print("  the child (remaining=2) the loop tests candidates[0]=9 first, 9>2,")
    print("  BREAKS, and never tries the 2 that would have completed [9,2]. One")
    print("  real answer silently gone. An unsorted `break` is not a weaker")
    print("  optimisation, it is a wrong answer — which is why sorting is a")
    print("  PREREQUISITE and not a companion tweak.")
    all_ok &= unsorted_bug

    # ----------------------------------------------------------------------
    # 4. ⚠️ MISTAKE 3 — the copy-on-append trap.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  results.append(path[:]) vs results.append(path) ---")
    good = sol.combinationSum([2, 3, 6, 7], 7)
    bad = sol.combinationSum_no_copy([2, 3, 6, 7], 7)
    corrupted = all(b == [] for b in bad) and len(bad) == len(good)
    print(f"  correct: {sorted(good)}")
    print(f"  broken : {bad}   (all {len(bad)} entries are the SAME now-empty "
          f"list: {corrupted})")
    all_ok &= corrupted

    # ----------------------------------------------------------------------
    # 5. Pruning, measured: nodes visited in four configurations.
    # ----------------------------------------------------------------------
    print("\n--- nodes visited: sorting and `break` measured separately ---")
    print(f"  {'candidates':<24} {'tgt':>4} {'answers':>8} {'plain':>9} "
          f"{'sort only':>10} {'break only':>11} {'sort+break':>11} {'saved':>7}")
    prune_ok = True
    for cands, target in (([2, 3, 5, 7, 11], 25),
                          ([5, 7, 11, 13, 2], 30),
                          ([11, 13, 17, 19, 2, 3], 32),
                          ([2, 3, 4, 5, 6, 7, 8, 9], 24)):
        answers = len(sol.combinationSum(cands, target))
        plain = _count_nodes(cands, target, False, False)
        s_only = _count_nodes(cands, target, True, False)
        b_only = _count_nodes(cands, target, False, True)
        both = _count_nodes(cands, target, True, True)
        prune_ok &= both <= plain
        print(f"  {str(cands):<24} {target:>4} {answers:>8} {plain:>9} "
              f"{s_only:>10} {b_only:>11} {both:>11} {plain / both:>6.1f}x")
    print("  READ THE 'sort only' COLUMN: it is sometimes WORSE than plain")
    print("  (538 vs 288 on [5,7,11,13,2]). Sorting alone does not prune")
    print("  anything — it only reorders the children — and ascending order")
    print("  tries the SMALL candidates first, which builds deeper subtrees and")
    print("  therefore MORE nodes. Sorting only pays when it is what makes")
    print("  `break` legal. The two are one optimisation, not two.")
    print("  'break only' is the UNSORTED break, i.e. the broken variant from")
    print("  demo 3: its low node count is bought by skipping real answers, so")
    print("  it is in the table as a warning, not as a candidate. The honest")
    print("  saving is 'sort+break' vs 'plain', and it is a constant-factor")
    print("  win, not a change of complexity class.")
    all_ok &= prune_ok

    # ----------------------------------------------------------------------
    # 6. Carrying `remaining` vs re-summing `path` at every node.
    # ----------------------------------------------------------------------
    print("\n--- carry `remaining` down vs re-sum path at every node (ms) ---")
    print(f"  {'candidates':<24} {'tgt':>4} {'carry':>9} {'re-sum':>9} {'ratio':>7}")
    for cands, target in (([2, 3, 5, 7], 30), ([2, 3, 5, 7], 40),
                          ([2, 3, 5, 7], 60), ([2, 3], 80)):
        t0 = time.perf_counter(); sol.combinationSum(cands, target)
        t1 = time.perf_counter(); sol.combinationSum_resum(cands, target)
        t2 = time.perf_counter()
        a, b = (t1 - t0) * 1e3, (t2 - t1) * 1e3
        print(f"  {str(cands):<24} {target:>4} {a:>8.2f}ms {b:>8.2f}ms "
              f"{b / a:>6.2f}x")
    print("  `sum(path)` is O(depth) and runs at EVERY node, so the penalty is")
    print("  a factor of the DEPTH — and the measured ratio does climb with it")
    print("  (~1.4x at target 30, ~1.8x at [2,3] target 80, i.e. depth 40).")
    print("  It stays a small constant rather than a 20x disaster because")
    print("  CPython's `sum` is C-coded and the depth here is only tens of")
    print("  elements. The last two rows exceed LeetCode's target <= 40 on")
    print("  purpose: at the real constraint the penalty is ~1.4x, which is")
    print("  the number to quote if asked. Carry `remaining` anyway — it is")
    print("  free and it makes the leaf test O(1) by construction.")

    # ----------------------------------------------------------------------
    # 7. Wall clock: all four correct implementations.
    # ----------------------------------------------------------------------
    print("\n--- wall clock (ms), correct implementations ---")
    print(f"  {'candidates':<24} {'tgt':>4} {'answers':>8} {'sort+break':>11} "
          f"{'unpruned':>10} {'continue':>10} {'counts':>9} {'DP':>9}")
    for cands, target in (([2, 3, 5, 7], 30), ([2, 3, 5, 7, 11], 32),
                          ([3, 5, 7, 11, 13], 40)):
        ts = []
        for fn in (sol.combinationSum, sol.combinationSum_unpruned,
                   sol.combinationSum_sorted_continue, sol.combinationSum_counts,
                   sol.combinationSum_dp):
            t0 = time.perf_counter()
            out = fn(list(cands), target)
            ts.append((time.perf_counter() - t0) * 1e3)
        print(f"  {str(cands):<24} {target:>4} {len(out):>8} {ts[0]:>10.2f}ms "
              f"{ts[1]:>9.2f}ms {ts[2]:>9.2f}ms {ts[3]:>8.2f}ms {ts[4]:>8.2f}ms")

    # ----------------------------------------------------------------------
    # 8. Why the constraint `candidates[i] >= 2` exists: a 0 never terminates.
    # ----------------------------------------------------------------------
    print("\n--- why the constraints forbid 0: `backtrack(i)` cannot terminate ---")
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(400)
    try:
        sol.combinationSum([0, 3], 7)
        blew_up = False
        note = "returned without error (unexpected)"
    except RecursionError:
        blew_up = True
        note = "RecursionError, as predicted"
    finally:
        sys.setrecursionlimit(old_limit)
    print(f"  candidates=[0, 3], target=7 -> {note}")
    print("  Picking 0 leaves `remaining` unchanged, and `backtrack(i)` lets you")
    print("  pick it again forever. Nothing in the CODE prevents this — the")
    print("  guarantee comes from the CONSTRAINT `2 <= candidates[i]`, which")
    print("  makes `remaining` strictly decrease on every call and bounds the")
    print("  depth at target // min(candidates). That is the answer to 'why does")
    print("  your recursion terminate?', and it is a real interview question.")
    all_ok &= blew_up

    # ----------------------------------------------------------------------
    # 9. What happens with duplicates in the input — the bridge to LC 40.
    # ----------------------------------------------------------------------
    print("\n--- duplicates in `candidates`: why LC 40 (008) has to exist ---")
    dupes = [2, 2, 3]
    out = sol.combinationSum(dupes, 7)
    distinct = {tuple(sorted(c)) for c in out}
    print(f"  candidates={dupes} (outside LC 39's constraints), target=7")
    print(f"  this solution emits {len(out)} results: {sorted(out)}")
    print(f"  but only {len(distinct)} are distinct: {sorted(distinct)}")
    print("  The two 2s are different INDICES, so the increasing-index rule")
    print("  happily uses both and the same multiset arrives twice. LC 39's")
    print("  constraints simply forbid the input; LC 40 (problem 008) fixes it")
    print("  properly with sort + `i > start and c[i] == c[i-1]: continue`.")
    all_ok &= len(out) > len(distinct)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
