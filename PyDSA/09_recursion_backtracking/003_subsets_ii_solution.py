"""
================================================================================
SOLUTION · LeetCode 90 · Subsets II                                    [Medium]
https://leetcode.com/problems/subsets-ii/
================================================================================

THE CORE IDEA
--------------
Same backtracking template as 002 (subsets, extend-by-index), plus ONE guard:
sort the input, then at each tree depth skip a choice if it repeats the
PREVIOUS SIBLING already tried at that exact node.

    nums.sort()
    def backtrack(start, path):
        results.append(path[:])
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i - 1]:   # skip duplicate SIBLING
                continue
            path.append(nums[i]); backtrack(i + 1, path); path.pop()

This prunes duplicate BRANCHES at generation time — see topic guide Part 3 for
the full argument. `i > start` (not `i > 0`) is what makes the first
occurrence of a value at any depth always legal, while only later repeats
AS A SIBLING CHOICE at that same node get skipped.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. GENERATE-ALL + SET DEDUPE — build every subset as if elements were unique
   (002's algorithm, unmodified), then dedupe the final list with
   `set(tuple(sorted(s)) for s in results)`. Priced, not the answer: correct,
   but visits every duplicate branch before discarding it — see the
   measurement below for how wasteful this actually is.
2. SORT + SKIP-ADJACENT-SIBLING (backtracking) — the answer. Prunes duplicate
   branches AT GENERATION TIME, before they are ever built.
3. BITMASK + SET DEDUPE — 002's bitmask approach, with results deduped via a
   set of tuples. Same wastefulness as approach 1, just without recursion.


================================================================================
STEP BY STEP TRACE — nums = [1, 1, 2] (already sorted)
================================================================================
    backtrack(start=0, path=[])
      record []                                    results = [[]]
      i=0: nums[0]=1, i==start -> ALWAYS allowed. choose -> path=[1]
        backtrack(start=1, path=[1])
          record [1]                                results += [[1]]
          i=1: nums[1]=1, i==start -> allowed. choose -> path=[1,1]
            backtrack(start=2, path=[1,1])
              record [1,1]                           results += [[1,1]]
              i=2: nums[2]=2, i==start -> allowed. choose -> path=[1,1,2]
                backtrack(start=3, ...) -> record [1,1,2]; return
              unchoose -> path=[1,1]
          unchoose -> path=[1]
          i=2: nums[2]=2, i>start(1) and nums[2]!=nums[1] -> allowed.
            choose -> path=[1,2] -> record [1,2]; return; unchoose
      unchoose -> path=[]
      i=1: nums[1]=1, i>start(0) AND nums[1]==nums[0] -> SKIP (this whole
           subtree would rebuild [1],[1,1],[1,1,2],[1,2] again, byte-for-byte)
      i=2: nums[2]=2, i>start(0) and nums[2]!=nums[1] -> allowed.
        choose -> path=[2] -> record [2]
        i=... (nothing left) -> return; unchoose
    done. results = [[], [1], [1,1], [1,1,2], [1,2], [2]]   (6 subsets, correct)

The i=1 skip at the ROOT is the entire savings: without it, a second, fully
redundant copy of the i=0 subtree would be explored and then discarded.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                            Time              Space    Mutates?  Note
    -----------------------------------  ----------------  -------  --------  --------------------
    Generate-all (dup) + set dedupe      O(n * 2^n) always  O(2^n)   no        builds EVERY branch,
                                                                                including duplicates,
                                                                                THEN discards them
    Sort + skip-adjacent-sibling ✅      O(n log n) sort +  O(n)     no        prunes duplicate
                                          up to O(n * 2^n),                    branches at
                                          FEWER nodes when                     generation time
                                          duplicates exist
    Bitmask + set dedupe                 O(n * 2^n) always  O(2^n)   no        same waste as
                                                                                approach 1

    WHERE the savings comes from: sort+skip visits exactly as many tree nodes
    as there are DISTINCT subsets (plus the pruned-at-the-root skip checks,
    O(1) each) — it never descends into a subtree it already knows is a
    duplicate of one just finished. Generate-all always visits the full
    2^n-node tree regardless of duplicates, then pays an extra O(2^n) (up to
    O(n * 2^n) with tuple hashing) to dedupe at the end. On an input with k
    copies of the same value, generate-all does 2^n work; sort+skip's tree
    shrinks toward the number of DISTINCT subsets, which can be far smaller.


================================================================================
EDGE CASES
================================================================================
    [1, 1, 1]           -> [[],[1],[1,1],[1,1,1]]     ALL duplicates: the
                                                        skip rule prunes
                                                        every sibling after
                                                        the first at every
                                                        depth; still gets
                                                        n+1 = 4 subsets, not
                                                        2^3 = 8.
    [0]                  -> [[],[0]]                    no duplicates present;
                                                        behaves like 002.
    unsorted input, e.g. [2,1,2] -> must be sorted INTERNALLY before the skip
                                    rule is applied — the guard assumes
                                    duplicates are ADJACENT.
    all elements distinct -> identical behavior/output to problem 002; the
                             skip condition never fires.
    negative + duplicate values, e.g. [-1,-1,0] -> sorting handles sign
                             correctly; duplicates of ANY value (not just
                             positive) are caught.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to sort `nums` first. Without sorting, equal values are not
   necessarily adjacent, so `nums[i] == nums[i-1]` fails to catch them (e.g.
   [2, 1, 2] — the two 2's are not adjacent) and duplicate subsets slip
   through.
2. Using `i > 0` instead of `i > start` as the guard. `i > 0` incorrectly
   skips the FIRST occurrence of a repeated value at a DEEPER node just
   because it also appeared earlier in the array overall — this wrongly
   forbids legitimate subsets like [1,1,2] that use a value at two different
   depths. Demonstrated live below.
3. Confusing "skip duplicate CHOICES at the same tree depth" with "skip
   duplicate VALUES overall" — the second interpretation would forbid using
   the same value twice in one subset at all, which is wrong: [1,1,2] is a
   valid, necessary subset when the input has two 1's.
4. Deduping the final result with a `set` of tuples instead of pruning at
   generation time — correct, but does asymptotically more work; see the
   measured comparison below.
5. Forgetting `path.pop()` after the recursive call (same as every
   backtracking problem — corrupts sibling branches).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Do it without sorting — inputs must be processed in original order.
A: Then you cannot rely on "duplicates are adjacent" and must track seen
   values PER TREE LEVEL with a local `set()` reset at each recursive call
   (allowed but uses extra O(n) space per level instead of an O(1) index
   comparison); sorting is strictly preferable when order doesn't matter.

Q: How does this generalize to Permutations II (problem 005)?
A: Same guard, different tree shape: permutations track a `used[]` array
   instead of a `start` index, so the "same depth" check becomes "this value
   was just tried and un-chosen at THIS exact recursive call, and its
   previous identical copy is not currently in use" — see 005's solution.

Q: What if the problem asked for subsets summing to a target, with
   duplicates?
A: Combination Sum II (problem 008) — the same sort+skip guard, combined with
   a running-sum leaf test instead of "every node is valid."


================================================================================
RELATED PROBLEMS
================================================================================
    LC 78   Subsets                       — no duplicates (002 here)
    LC 47   Permutations II                — same dedupe idea, different
                                             tree shape (005 here)
    LC 40   Combination Sum II             — dedupe + sum target (008 here)
    LC 916  Word Subsets                   — a different "subset" (multiset
                                             containment), unrelated shape
================================================================================
"""

import time
from typing import List


class Solution:
    def subsetsWithDup(self, nums: List[int]) -> List[List[int]]:
        """Sort, then backtrack with the skip-adjacent-sibling guard.
        O(n log n) sort + up to O(n * 2^n) tree walk, fewer nodes visited
        whenever duplicates exist. The answer."""
        nums = sorted(nums)
        results: List[List[int]] = []
        path: List[int] = []
        n = len(nums)

        def backtrack(start: int) -> None:
            results.append(path[:])
            for i in range(start, n):
                if i > start and nums[i] == nums[i - 1]:   # skip duplicate SIBLING
                    continue
                path.append(nums[i])
                backtrack(i + 1)
                path.pop()

        backtrack(0)
        return results

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def subsetsWithDup_generate_all_then_dedupe(self, nums: List[int]) -> List[List[int]]:
        """Generate every subset as if all values were distinct (002's
        algorithm, unmodified), then dedupe with a set of sorted tuples.
        Correct, but visits every duplicate branch before discarding it."""
        results: List[List[int]] = []
        path: List[int] = []
        n = len(nums)

        def backtrack(start: int) -> None:
            results.append(path[:])
            for i in range(start, n):
                path.append(nums[i])
                backtrack(i + 1)
                path.pop()

        backtrack(0)
        seen = set()
        out = []
        for s in results:
            key = tuple(sorted(s))
            if key not in seen:
                seen.add(key)
                out.append(s)
        return out

    def subsetsWithDup_bitmask_dedupe(self, nums: List[int]) -> List[List[int]]:
        """Bitmask enumeration (002's approach), deduped via a set of
        tuples. Same asymptotic waste as generate-all + dedupe."""
        n = len(nums)
        seen = set()
        out = []
        for mask in range(1 << n):
            subset = [nums[i] for i in range(n) if mask & (1 << i)]
            key = tuple(sorted(subset))
            if key not in seen:
                seen.add(key)
                out.append(subset)
        return out

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def subsetsWithDup_wrong_guard(self, nums: List[int]) -> List[List[int]]:
        """✗ BROKEN ON PURPOSE — uses `i > 0` instead of `i > start`, which
        incorrectly forbids using a repeated value at a DEEPER node just
        because it also occurs earlier in the array. Undercounts subsets
        like [1,1,2]."""
        nums = sorted(nums)
        results: List[List[int]] = []
        path: List[int] = []
        n = len(nums)

        def backtrack(start: int) -> None:
            results.append(path[:])
            for i in range(start, n):
                if i > 0 and nums[i] == nums[i - 1]:   # WRONG guard: ignores `start`
                    continue
                path.append(nums[i])
                backtrack(i + 1)
                path.pop()

        backtrack(0)
        return results

    def subsetsWithDup_no_sort(self, nums: List[int]) -> List[List[int]]:
        """✗ BROKEN ON PURPOSE — applies the skip rule WITHOUT sorting first.
        Duplicates that are not adjacent are not caught."""
        results: List[List[int]] = []
        path: List[int] = []
        n = len(nums)

        def backtrack(start: int) -> None:
            results.append(path[:])
            for i in range(start, n):
                if i > start and nums[i] == nums[i - 1]:
                    continue
                path.append(nums[i])
                backtrack(i + 1)
                path.pop()

        backtrack(0)
        return results


# ==============================================================================
# TESTS — run:  python 003_subsets_ii_solution.py
# ==============================================================================
def _normalize(subsets_list):
    return sorted(sorted(s) for s in subsets_list)


CASES = [
    [1, 2, 2], [0], [1, 1, 1], [1, 2, 3], [4, 4, 4, 1, 4], [-1, -1, 0], [1, 1],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    def oracle(nums):
        """Independent oracle: bitmask enumerate + dedupe via sorted-tuple set."""
        n = len(nums)
        seen = set()
        for mask in range(1 << n):
            seen.add(tuple(sorted(nums[i] for i in range(n) if mask & (1 << i))))
        return [list(t) for t in seen]

    impls = [
        ("sort + skip-sibling  ", sol.subsetsWithDup),
        ("generate-all + dedupe", sol.subsetsWithDup_generate_all_then_dedupe),
        ("bitmask + dedupe     ", sol.subsetsWithDup_bitmask_dedupe),
    ]
    for name, fn in impls:
        ok = all(_normalize(fn(nums)) == _normalize(oracle(nums)) for nums in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # ⚠️ The wrong-guard bug, live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  i > 0 vs i > start: the wrong-guard bug ---")
    print(f"  {'input':<14} {'correct':>8} {'wrong guard':>12}  ok?")
    guard_mismatch = False
    for nums in ([1, 1, 2], [1, 1, 1], [2, 2, 3, 3], [1, 2, 2, 3]):
        good = len(sol.subsetsWithDup(nums))
        bad = len(sol.subsetsWithDup_wrong_guard(nums))
        mismatch = good != bad
        guard_mismatch |= mismatch
        print(f"  {str(nums):<14} {good:>8} {bad:>12}  "
              f"{'yes' if not mismatch else 'NO  <- undercounted'}")
    print(f"  wrong-guard bug reproduced: {guard_mismatch}")
    all_ok &= guard_mismatch

    # ----------------------------------------------------------------------
    # ⚠️ The no-sort bug, live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  skip rule WITHOUT sorting first ---")
    print(f"  {'input':<14} {'correct':>8} {'no sort':>8}  ok?")
    sort_mismatch = False
    for nums in ([2, 1, 2], [3, 1, 3, 2], [1, 2, 1]):
        good = _normalize(sol.subsetsWithDup(nums))
        bad = _normalize(sol.subsetsWithDup_no_sort(nums))
        mismatch = good != bad
        sort_mismatch |= mismatch
        print(f"  {str(nums):<14} {len(good):>8} {len(bad):>8}  "
              f"{'yes' if not mismatch else 'NO  <- duplicates slipped through'}")
    print(f"  no-sort bug reproduced: {sort_mismatch}")
    all_ok &= sort_mismatch

    # ----------------------------------------------------------------------
    # Measured: sort+skip vs generate-all+dedupe on heavy duplication.
    # ----------------------------------------------------------------------
    print("\n--- measured: sort+skip pruning vs generate-all+dedupe waste ---")
    print(f"  {'input':<28} {'sort+skip (ms)':>15} {'gen-all+dedupe (ms)':>21} {'ratio':>7}")
    for n in (10, 14, 18):
        nums = [1] * n           # maximal duplication: worst case for generate-all
        t0 = time.perf_counter(); sol.subsetsWithDup(nums)
        t1 = time.perf_counter(); sol.subsetsWithDup_generate_all_then_dedupe(nums)
        t2 = time.perf_counter()
        a_ms = (t1 - t0) * 1000
        b_ms = (t2 - t1) * 1000
        ratio = b_ms / a_ms if a_ms > 0 else float("inf")
        print(f"  {f'[1]*{n}':<28} {a_ms:>13.3f}ms {b_ms:>19.3f}ms {ratio:>6.1f}x")
    print("  With every element equal, sort+skip's tree has only n+1 nodes")
    print("  (one subset per length); generate-all still builds all 2^n branches")
    print("  and dedupes afterward — the gap widens sharply as n grows.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
