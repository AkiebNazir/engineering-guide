"""
================================================================================
SOLUTION · LeetCode 46 · Permutations                                  [Medium]
https://leetcode.com/problems/permutations/
================================================================================

THE CORE IDEA
--------------
The "permutations" shape from the topic guide's Part 2: at each node, the
choice is "which UNUSED element fills this slot next?" A `used[]` boolean
array (or an in-place swap, see below) tracks what's already in the path.
Leaves are reached at `len(path) == len(nums)`.

    def backtrack():
        if len(path) == len(nums):
            results.append(path[:])
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True; path.append(nums[i])     # CHOOSE
            backtrack()                                # EXPLORE
            path.pop(); used[i] = False                # UNCHOOSE

O(n * n!) time (n! leaves, O(n) copy each), O(n) auxiliary space.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. IN-PLACE SWAP — O(n * n!) time, O(1) EXTRA space beyond output (no `used`
   array, no separate `path` — nums IS the path, fixed one position at a
   time). Mutates the input array during recursion but always restores it.
   Priced and implemented — a real, commonly-expected alternative.
2. BACKTRACKING with `used[]` array — the answer. Clean, doesn't mutate the
   caller's `nums`, generalizes directly to Permutations II (005).
3. BACKTRACKING with `elem in path` membership check instead of `used[]`
   — O(n) per check instead of O(1), so O(n^2 * n!) overall. Simpler to
   write, asymptotically worse; priced for comparison.
4. ITERTOOLS — `itertools.permutations(nums)`, the standard library's C-
   implemented version. Same O(n * n!), typically the fastest constant
   factor in practice; the "I'd use this in production, here's how I'd
   write it myself" answer.


================================================================================
STEP BY STEP TRACE — nums = [1, 2, 3]  (used[] version)
================================================================================
    backtrack(), path=[], used=[F,F,F]
      i=0: nums[0]=1 unused -> choose. path=[1], used=[T,F,F]
        backtrack(), path=[1]
          i=0: used -> skip
          i=1: nums[1]=2 unused -> choose. path=[1,2], used=[T,T,F]
            backtrack(), path=[1,2]
              i=0,1: used -> skip
              i=2: nums[2]=3 unused -> choose. path=[1,2,3], used=[T,T,T]
                backtrack(), len==3 -> record [1,2,3]; return
              unchoose -> path=[1,2], used=[T,T,F]
          unchoose -> path=[1], used=[T,F,F]
          i=2: nums[2]=3 unused -> choose. path=[1,3], used=[T,F,T]
            ... records [1,3,2] ...
          unchoose -> path=[1], used=[T,F,F]
      unchoose -> path=[], used=[F,F,F]
      i=1: choose 2 -> ... records [2,1,3], [2,3,1] ...
      i=2: choose 3 -> ... records [3,1,2], [3,2,1] ...
    done. 6 = 3! permutations, every ordering exactly once.

Notice the branching factor: 3 choices at the root, 2 at depth 1 (one used),
1 at depth 2 (two used) — 3 x 2 x 1 = 3! total leaves, exactly as claimed.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time         Space (aux)  Mutates input?  Note
    -------------------------------  -----------  -----------  ---------------  --------------------
    Backtracking, used[] array ✅   O(n * n!)     O(n)         no               the answer
    Backtracking, `in path` check   O(n^2 * n!)   O(n)         no               simpler, slower
    In-place swap                   O(n * n!)     O(1) extra   YES (restored)   no used[] array at all
    itertools.permutations          O(n * n!)     O(n)         no               C-implemented, fastest

    WHERE O(n * n!) comes from: the tree has n! leaves (n choices at depth 0,
    n-1 at depth 1, ..., 1 at depth n-1: n x (n-1) x ... x 1 = n!), and every
    leaf costs O(n) to copy into results. The `used[]` check is O(1), so the
    non-leaf traversal cost (visiting every INTERNAL node too, of which there
    are also O(n!) at each of n levels) does not change the overall order.

    `in path` MEMBERSHIP CHECK COSTS: `elem in path` scans the list, O(len
    (path)) worst case, so replacing `used[i]` with `nums[i] in path` adds an
    O(n) factor to EVERY choice-check at every node, turning O(n * n!) into
    O(n^2 * n!) — priced, not the answer, but demonstrated below.


================================================================================
EDGE CASES
================================================================================
    nums = [1]            -> [[1]]                 1! = 1 permutation, trivial.
    nums = [1, 2]           -> [[1,2],[2,1]]          2! = 2, smallest non-
                                                     trivial branching.
    negative values          -> works unchanged; no sign assumption anywhere.
    len(nums) == 6 (max)     -> 720 permutations; exercises the upper bound
                                without timing out.
    all values same MAGNITUDE, different sign, e.g. [-1, 1] -> still just 2
                                distinct elements, 2! = 2 permutations —
                                distinctness is by VALUE, not by magnitude.


================================================================================
COMMON MISTAKES
================================================================================
1. `results.append(path)` instead of `results.append(path[:])` — the SAME
   copy-on-append trap as 002, applied here: `path` is one shared list
   mutated by append/pop across the whole recursion. The demo below
   constructs this live: every permutation in the corrupted output ends up
   IDENTICAL (whatever `path` happened to be — usually empty — when the
   recursion finally unwound).
2. Forgetting to reset `used[i] = False` (or forgetting `path.pop()`) in the
   unchoose step — corrupts every subsequent sibling branch, either skipping
   an index that should be available again, or leaving stale elements in the
   path.
3. Using `elem in path` for the "already used" check without realizing it
   changes the complexity from O(n * n!) to O(n^2 * n!) — not wrong, but a
   different price than the used[] version, and worth naming explicitly if
   asked.
4. In the in-place SWAP variant: forgetting to swap BACK after the recursive
   call, or swapping using indices that drift after a previous swap already
   happened at this level — the restore step is easy to get backwards.
5. Assuming the input can have duplicates and getting duplicate permutations
   in the output — problem 046's constraint guarantees UNIQUE elements;
   duplicates need problem 005's extra dedupe guard.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: The input may contain duplicates — avoid duplicate permutations.
A: Problem 005 (Permutations II): sort first, then at each node skip a
   candidate value if an IDENTICAL value was already tried as a sibling at
   this same node (and is not currently "in use" from a shallower call) —
   the permutations-shape version of topic guide Part 3's dedupe rule.

Q: Generate the k-th permutation directly, without generating all of them.
A: LC 60 (Permutation Sequence) — factorial number system: divide by (n-1)!
   to pick the first element, recurse on the remainder. O(n^2) or O(n log n),
   no backtracking tree at all.

Q: Do it without recursion.
A: Heap's algorithm (in-place swap, iterative form) or next_permutation-style
   lexicographic generation (repeatedly compute the next permutation in
   sorted order until you cycle back) both avoid explicit recursion.

Q: What if you only need permutations of a subset of size k, not all n
   elements?
A: Same used[] template, leaf condition becomes `len(path) == k` instead of
   `== len(nums)` — this is the "permutations of size k" variant, sometimes
   called partial permutations, P(n, k) = n! / (n-k)!.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 47   Permutations II                — duplicates, sort+skip (005 here)
    LC 31   Next Permutation                — one step of lexicographic order,
                                             no backtracking
    LC 60   Permutation Sequence            — k-th permutation directly, no
                                             full enumeration
    LC 267  Palindrome Permutation II       — permutations + a validity
                                             constraint (must be a palindrome)
================================================================================
"""

import itertools
import time
from typing import List


class Solution:
    def permute(self, nums: List[int]) -> List[List[int]]:
        """Backtracking with a used[] boolean array, ONE shared path list.
        O(n * n!) time, O(n) auxiliary space. The answer."""
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
                used[i] = True                        # CHOOSE
                path.append(nums[i])
                backtrack()                             # EXPLORE
                path.pop()                               # UNCHOOSE
                used[i] = False

        backtrack()
        return results

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def permute_in_place_swap(self, nums: List[int]) -> List[List[int]]:
        """In-place swap: fix nums[0], then nums[1], etc., by swapping the
        current position with each candidate, recursing, then swapping back.
        O(n * n!) time, O(1) EXTRA space (mutates+restores the input list)."""
        nums = list(nums)             # don't mutate the caller's original list
        n = len(nums)
        results: List[List[int]] = []

        def backtrack(first: int) -> None:
            if first == n:
                results.append(nums[:])
                return
            for i in range(first, n):
                nums[first], nums[i] = nums[i], nums[first]     # CHOOSE
                backtrack(first + 1)                              # EXPLORE
                nums[first], nums[i] = nums[i], nums[first]      # UNCHOOSE

        backtrack(0)
        return results

    def permute_membership_check(self, nums: List[int]) -> List[List[int]]:
        """Same as the answer, but tests `nums[i] in path` instead of a
        used[] array. O(n^2 * n!) — the membership test is O(n) per call."""
        n = len(nums)
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack() -> None:
            if len(path) == n:
                results.append(path[:])
                return
            for i in range(n):
                if nums[i] in path:            # O(n) scan, the slow part
                    continue
                path.append(nums[i])
                backtrack()
                path.pop()

        backtrack()
        return results

    def permute_itertools(self, nums: List[int]) -> List[List[int]]:
        """Standard library, C-implemented. O(n * n!)."""
        return [list(p) for p in itertools.permutations(nums)]

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def permute_broken_no_copy(self, nums: List[int]) -> List[List[int]]:
        """✗ BROKEN ON PURPOSE — appends the shared `path` object itself,
        never a copy. Every recorded "permutation" ends up pointing at the
        SAME list."""
        n = len(nums)
        results: List[List[int]] = []
        path: List[int] = []
        used = [False] * n

        def backtrack() -> None:
            if len(path) == n:
                results.append(path)             # NO [:] — the bug
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
        return results


# ==============================================================================
# TESTS — run:  python 004_permutations_solution.py
# ==============================================================================
def _normalize(perms):
    return sorted(tuple(p) for p in perms)


CASES = [[1, 2, 3], [0, 1], [1], [1, 2], [-1, 1, 2], [1, 2, 3, 4]]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    def oracle(nums):
        return [list(p) for p in itertools.permutations(nums)]

    impls = [
        ("used[] backtrack   ", sol.permute),
        ("in-place swap      ", sol.permute_in_place_swap),
        ("membership check   ", sol.permute_membership_check),
        ("itertools          ", sol.permute_itertools),
    ]
    for name, fn in impls:
        ok = all(_normalize(fn(nums)) == _normalize(oracle(nums)) for nums in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Confirm the tree's leaf count matches the theoretical n! bound.
    # ----------------------------------------------------------------------
    print("\n--- leaf count vs theoretical n!, measured ---")
    print(f"  {'n':>3} {'leaves produced':>16} {'n!':>8}  match?")
    for n in (1, 2, 3, 4, 5, 6):
        nums = list(range(n))
        leaves = len(sol.permute(nums))
        import math
        theoretical = math.factorial(n)
        match = leaves == theoretical
        all_ok &= match
        print(f"  {n:>3} {leaves:>16} {theoretical:>8}  {'yes' if match else 'NO'}")

    # ----------------------------------------------------------------------
    # ⚠️ The copy-on-append trap, demonstrated live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  results.append(path) vs results.append(path[:]) ---")
    nums = [1, 2, 3]
    good = sol.permute(nums)
    bad = sol.permute_broken_no_copy(nums)
    distinct_good = len(set(map(tuple, good)))
    distinct_bad = len(set(map(tuple, bad)))
    print(f"  correct (append path[:]): {len(good)} perms, {distinct_good} DISTINCT")
    print(f"  broken  (append path)   : {len(bad)} perms, {distinct_bad} DISTINCT: {bad}")
    corrupted = distinct_bad == 1
    print(f"  every entry in the broken result is IDENTICAL: {corrupted}")
    all_ok &= corrupted

    # ----------------------------------------------------------------------
    # Timing: used[] array vs `in path` membership check.
    # ----------------------------------------------------------------------
    print("\n--- measured: used[] array (O(1) check) vs `in path` (O(n) check) ---")
    print(f"  {'n':>3} {'used[] (ms)':>13} {'in path (ms)':>14} {'ratio':>7}")
    for n in (6, 7, 8):
        nums = list(range(n))
        t0 = time.perf_counter(); sol.permute(nums)
        t1 = time.perf_counter(); sol.permute_membership_check(nums)
        t2 = time.perf_counter()
        a_ms = (t1 - t0) * 1000
        b_ms = (t2 - t1) * 1000
        ratio = b_ms / a_ms if a_ms > 0 else float("inf")
        print(f"  {n:>3} {a_ms:>11.2f}ms {b_ms:>12.2f}ms {ratio:>6.2f}x")
    print("  The `in path` version does strictly more work per node (an O(n)")
    print("  scan instead of an O(1) array read), and the gap grows with n.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
