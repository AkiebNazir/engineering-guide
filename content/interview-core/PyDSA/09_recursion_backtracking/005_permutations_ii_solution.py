"""
================================================================================
SOLUTION · LeetCode 47 · Permutations II                               [Medium]
https://leetcode.com/problems/permutations-ii/
================================================================================

THE CORE IDEA
--------------
Same used[]-array backtracking as 004, plus a dedupe guard adapted to the
permutations tree shape: sort first, then at each node skip a value if an
IDENTICAL value was already tried as a SIBLING at this node and its subtree
has already finished (`not used[i-1]`).

    nums.sort()
    def backtrack():
        if len(path) == n:
            results.append(path[:]); return
        for i in range(n):
            if used[i]:
                continue
            if i > 0 and nums[i] == nums[i-1] and not used[i-1]:
                continue                       # skip duplicate SIBLING
            used[i] = True; path.append(nums[i])
            backtrack()
            path.pop(); used[i] = False

The `not used[i-1]` clause is the piece that doesn't exist in problem 003's
guard, because permutations has no `start` index — the SAME value can appear
at multiple DEPTHS of the tree (once placed, once still waiting), and the
guard must distinguish "sibling not yet tried" (used[i-1] == False, meaning
the earlier identical value finished ITS whole subtree and returned back up
to be unused again — SKIP, it would rebuild the same subtree) from "ancestor
currently placed higher in the path" (used[i-1] == True — a completely
different, legal branch).


================================================================================
MULTIPLE APPROACHES
================================================================================
1. GENERATE-ALL (004's algorithm) + SET DEDUPE — treats all n elements as
   distinct, generates all n! raw permutations, then dedupes via
   `set(tuple(p) for p in results)`. Priced, not the answer: correct, wasteful.
2. SORT + used[]-AWARE SIBLING SKIP (backtracking) — the answer. Prunes
   duplicate branches at generation time.
3. COUNTER-BASED (choose from a multiset of REMAINING counts) — instead of an
   index-based `used[]` array, maintain a `Counter` of how many of each
   DISTINCT value remain; at each node, try each distinct value with count >
   0. This sidesteps the sibling-skip logic entirely because there is only
   ONE way to "choose a 1" — no index-level duplicates to distinguish.
   Genuinely elegant; implemented below.


================================================================================
STEP BY STEP TRACE — nums = [1, 1, 2] (sorted)
================================================================================
    backtrack(), path=[], used=[F,F,F]   (indices 0,1 hold value 1; index 2 holds 2)
      i=0: nums[0]=1, unused, i==0 -> ALWAYS allowed (no i-1 to compare).
        choose -> used=[T,F,F], path=[1]
        backtrack(), path=[1]
          i=0: used -> skip
          i=1: nums[1]=1, unused, i>0, nums[1]==nums[0](1==1), used[0]=TRUE
               -> guard says "not used[0]" is FALSE -> ALLOWED (the earlier 1
                  is an ANCESTOR currently in the path, not a finished sibling)
            choose -> used=[T,T,F], path=[1,1]
            backtrack(), path=[1,1]
              i=2: nums[2]=2, unused -> choose -> path=[1,1,2] -> len==3 ->
                   record [1,1,2]; return; unchoose
            unchoose -> used=[T,F,F], path=[1]
          i=2: nums[2]=2, unused -> choose -> path=[1,2]
            backtrack(), path=[1,2]
              i=1: nums[1]=1, unused, i>0, nums[1]==nums[0](1==1), used[0]=TRUE
                   -> allowed (ancestor, not finished sibling)
                choose -> path=[1,2,1] -> record [1,2,1]; return; unchoose
            unchoose -> path=[1]
        unchoose -> used=[F,F,F], path=[]
      i=1: nums[1]=1, unused, i>0, nums[1]==nums[0](1==1), used[0]=FALSE
           -> guard says "not used[0]" is TRUE -> SKIP (index 0's value-1
              subtree already finished and returned to unused — retrying the
              SAME value as a fresh sibling here would rebuild it identically)
      i=2: nums[2]=2, unused -> choose -> path=[2]
        backtrack(), path=[2]
          i=0: nums[0]=1, unused, i==0 -> allowed. choose -> path=[2,1]
            backtrack(): i=1: nums[1]=1, unused, i>0, equal, used[0]=TRUE
                 -> allowed (ancestor). choose -> path=[2,1,1] -> record; return
          unchoose -> path=[2]
          i=1: nums[1]=1, unused, i>0, equal, used[0]=FALSE -> SKIP (index 0's
               subtree already covered this exact continuation via i=0 above)
    done. results = [[1,1,2],[1,2,1],[2,1,1]]   (3 distinct, not 3! = 6)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                             Time              Space   Mutates?  Note
    ------------------------------------  ----------------  ------  --------  --------------------
    Generate-all (004) + set dedupe       O(n * n!) always   O(n!)   no        builds every raw
                                                                                permutation, THEN
                                                                                discards duplicates
    Sort + used[]-aware sibling skip ✅   O(n log n) sort +  O(n)    no        prunes duplicate
                                          up to O(n * n!),                    branches at
                                          FEWER nodes with                    generation time
                                          duplicates
    Counter-based (multiset choose)       O(n * n!) worst,   O(n)    no       naturally correct,
                                          fewer with dups                     no sibling-skip logic

    WHERE the savings comes from: same argument as 003 — the guard prevents
    re-exploring a subtree that would produce EXACTLY the same set of
    permutations as one already fully explored under an earlier identical
    sibling. On an input with k copies of one value among n elements, the
    number of DISTINCT permutations is n! / k! (fewer still if multiple
    values repeat), and the pruned tree tracks that number instead of the
    full n!.


================================================================================
EDGE CASES
================================================================================
    [1, 1, 1]            -> [[1,1,1]]                    every element the
                                                          same: guard prunes
                                                          down to exactly 1
                                                          permutation, not 3!
                                                          = 6.
    [2, 2]                -> [[2,2]]                       2!/2! = 1.
    all distinct            -> identical output/behavior to problem 004; the
                              guard never fires.
    negative + duplicate values, e.g. [-1,-1,0] -> sorting/guard work the
                              same regardless of sign.
    len(nums) == 8 (max)     -> up to 8! = 40320 raw permutations if all
                              distinct; fewer with any duplication.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting `not used[i-1]` and using problem 003's plain `i > start`-style
   guard — permutations has no `start`, so a naive `i > 0 and nums[i] ==
   nums[i-1]` check (without the used[i-1] condition) INCORRECTLY forbids
   placing the second copy of a repeated value even when it's legal (e.g. it
   would wrongly reject [1,1,2] entirely). Demonstrated live below.
2. Forgetting to sort first — duplicates not adjacent break the `nums[i] ==
   nums[i-1]` comparison, same failure mode as problem 003.
3. Confusing this guard's direction: it is checking whether the PREVIOUS
   identical value's entire subtree has already been explored (not used[i-1]
   -> skip) versus is currently an ancestor in the live path (used[i-1] ->
   allow) — getting this backwards either produces duplicates or
   under-counts.
4. Using the generate-all + dedupe approach without recognizing the
   asymptotic cost difference on heavily duplicated inputs (measured below).
5. Forgetting the unchoose steps (`path.pop()`, `used[i] = False`) — same
   consequence as every backtracking problem: corrupts sibling branches.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why not just maintain a Counter of remaining values instead of this
   used[]+sort+skip machinery?
A: You can — see `permuteUnique_counter` below. It sidesteps the sibling-skip
   guard entirely because there's only one way to "choose a 1" when values
   are grouped by count rather than indexed individually. Often considered
   the more elegant answer once you've seen both.

Q: Combination Sum II (008) uses `i > start` (no `used[]` needed) — why does
   THIS problem need the extra `not used[i-1]` check?
A: Combinations only ever move FORWARD through indices (never revisit an
   earlier one), so "already tried as a sibling at this exact call" and
   "index range not yet exhausted" are the same condition — `start`
   captures it directly. Permutations revisit ALL not-yet-used indices at
   EVERY node, so the same value can legitimately reappear at a different
   tree depth; `not used[i-1]` is what disambiguates that from an exhausted
   sibling.

Q: How many distinct permutations does an input with k copies of one value
   (out of n total, all else distinct) have, without generating them?
A: n! / k! — the multinomial coefficient. Generalizes to n! / (k1! * k2! *
   ...) when multiple values repeat with multiplicities k1, k2, ....


================================================================================
RELATED PROBLEMS
================================================================================
    LC 46   Permutations                   — no duplicates (004 here)
    LC 90   Subsets II                      — same dedupe FAMILY, different
                                             tree shape (003 here)
    LC 40   Combination Sum II              — dedupe + sum target, combinations
                                             shape (008 here)
    LC 31   Next Permutation                — generate the NEXT one directly,
                                             no tree at all
================================================================================
"""

import time
from collections import Counter
from typing import List


class Solution:
    def permuteUnique(self, nums: List[int]) -> List[List[int]]:
        """Sort + used[]-aware sibling-skip backtracking. O(n log n) sort +
        up to O(n * n!) tree walk, fewer nodes with duplicates. The answer."""
        nums = sorted(nums)
        n = len(nums)
        results: List[List[int]] = []
        path: List[int] = []
        used = [False] * n

        def backtrack() -> None:
            if len(path) == n:
                results.append(path[:])
                return
            for i in range(n):
                if used[i]:
                    continue
                if i > 0 and nums[i] == nums[i - 1] and not used[i - 1]:
                    continue                        # skip duplicate SIBLING
                used[i] = True
                path.append(nums[i])
                backtrack()
                path.pop()
                used[i] = False

        backtrack()
        return results

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def permuteUnique_generate_all_then_dedupe(self, nums: List[int]) -> List[List[int]]:
        """004's algorithm (treats all elements as distinct by index), then
        dedupe via a set of tuples. Correct, but visits every raw n!
        permutation before discarding duplicates."""
        n = len(nums)
        results: List[List[int]] = []
        path: List[int] = []
        used = [False] * n

        def backtrack() -> None:
            if len(path) == n:
                results.append(path[:])
                return
            for i in range(n):
                if used[i]:
                    continue
                used[i] = True
                path.append(nums[i])
                backtrack()
                path.pop()
                used[i] = False

        backtrack()
        seen = set()
        out = []
        for p in results:
            key = tuple(p)
            if key not in seen:
                seen.add(key)
                out.append(p)
        return out

    def permuteUnique_counter(self, nums: List[int]) -> List[List[int]]:
        """Multiset-based: choose from DISTINCT remaining values (with a
        remaining count), rather than indexing individual elements. Never
        needs a sibling-skip guard at all, since there's only one way to
        'choose a 1'."""
        n = len(nums)
        count = Counter(nums)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack() -> None:
            if len(path) == n:
                results.append(path[:])
                return
            for val in list(count.keys()):
                if count[val] == 0:
                    continue
                count[val] -= 1
                path.append(val)
                backtrack()
                path.pop()
                count[val] += 1

        backtrack()
        return results

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def permuteUnique_wrong_guard(self, nums: List[int]) -> List[List[int]]:
        """✗ BROKEN ON PURPOSE — uses problem 003's `start`-based-style guard
        (no `used[i-1]` check), which is wrong here: it incorrectly forbids
        placing a repeated value even when it's an ancestor further up the
        path, not an exhausted sibling."""
        nums = sorted(nums)
        n = len(nums)
        results: List[List[int]] = []
        path: List[int] = []
        used = [False] * n

        def backtrack() -> None:
            if len(path) == n:
                results.append(path[:])
                return
            for i in range(n):
                if used[i]:
                    continue
                if i > 0 and nums[i] == nums[i - 1]:   # MISSING `not used[i-1]`
                    continue
                used[i] = True
                path.append(nums[i])
                backtrack()
                path.pop()
                used[i] = False

        backtrack()
        return results


# ==============================================================================
# TESTS — run:  python 005_permutations_ii_solution.py
# ==============================================================================
def _normalize(perms):
    return sorted(tuple(p) for p in perms)


CASES = [
    [1, 1, 2], [1, 2, 3], [1, 1, 1], [2, 2], [1, 2, 2, 3], [-1, -1, 0],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    def oracle(nums):
        """Independent oracle: itertools.permutations + dedupe via a set."""
        import itertools
        return list({tuple(p) for p in itertools.permutations(nums)})

    impls = [
        ("sort + used-aware skip", sol.permuteUnique),
        ("generate-all + dedupe ", sol.permuteUnique_generate_all_then_dedupe),
        ("counter-based          ", sol.permuteUnique_counter),
    ]
    for name, fn in impls:
        ok = all(_normalize(fn(nums)) == sorted(oracle(nums)) for nums in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # ⚠️ The wrong-guard bug, live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  missing `not used[i-1]`: the wrong-guard bug ---")
    print(f"  {'input':<14} {'correct':>8} {'wrong guard':>12}  ok?")
    guard_mismatch = False
    for nums in ([1, 1, 2], [1, 2, 2], [1, 1, 1], [2, 2, 3, 3]):
        good = len(sol.permuteUnique(nums))
        bad = len(sol.permuteUnique_wrong_guard(nums))
        mismatch = good != bad
        guard_mismatch |= mismatch
        print(f"  {str(nums):<14} {good:>8} {bad:>12}  "
              f"{'yes' if not mismatch else 'NO  <- undercounted'}")
    print(f"  wrong-guard bug reproduced: {guard_mismatch}")
    all_ok &= guard_mismatch

    # ----------------------------------------------------------------------
    # Distinct-permutation count matches n! / k! (multinomial).
    # ----------------------------------------------------------------------
    print("\n--- distinct count vs n!/(k1! * k2! * ...), measured ---")
    import math
    print(f"  {'input':<20} {'produced':>9} {'formula':>9}  match?")
    for nums in ([1, 1, 2], [1, 1, 1], [2, 2], [1, 2, 2, 3], [1, 1, 2, 2]):
        produced = len(sol.permuteUnique(nums))
        counts = Counter(nums)
        formula = math.factorial(len(nums))
        for c in counts.values():
            formula //= math.factorial(c)
        match = produced == formula
        all_ok &= match
        print(f"  {str(nums):<20} {produced:>9} {formula:>9}  {'yes' if match else 'NO'}")

    # ----------------------------------------------------------------------
    # Measured: sort+skip vs generate-all+dedupe on heavy duplication.
    # ----------------------------------------------------------------------
    print("\n--- measured: sort+skip pruning vs generate-all+dedupe waste ---")
    print(f"  {'input':<28} {'sort+skip (ms)':>15} {'gen-all+dedupe (ms)':>21} {'ratio':>7}")
    for n in (6, 7, 8):
        nums = [1] * n
        t0 = time.perf_counter(); sol.permuteUnique(nums)
        t1 = time.perf_counter(); sol.permuteUnique_generate_all_then_dedupe(nums)
        t2 = time.perf_counter()
        a_ms = (t1 - t0) * 1000
        b_ms = (t2 - t1) * 1000
        ratio = b_ms / a_ms if a_ms > 0 else float("inf")
        print(f"  {f'[1]*{n}':<28} {a_ms:>13.4f}ms {b_ms:>19.3f}ms {ratio:>6.1f}x")
    print("  With every element equal, sort+skip's tree has exactly 1 leaf;")
    print("  generate-all still builds and discards all n! raw permutations.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
