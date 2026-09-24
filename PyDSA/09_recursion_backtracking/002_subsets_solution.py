"""
================================================================================
SOLUTION · LeetCode 78 · Subsets                                       [Medium]
https://leetcode.com/problems/subsets/
================================================================================

THE CORE IDEA
--------------
Backtracking over the "combinations" template (topic guide Part 1), where
EVERY node — not just leaves — is a valid answer: at each node, record the
current path, then try extending it with each remaining index in turn.

    def backtrack(start, path):
        results.append(path[:])            # every node is valid, record NOW
        for i in range(start, n):
            path.append(nums[i])           # CHOOSE
            backtrack(i + 1, path)          # EXPLORE
            path.pop()                      # UNCHOOSE

O(n * 2^n) time (2^n subsets, O(n) to copy each), O(n) auxiliary space (path +
recursion depth) plus O(n * 2^n) for the output itself.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. BITMASK (iterative) — O(n * 2^n) time, O(1) extra space beyond output. For
   each of the 2^n integers 0..2^n-1, its binary representation IS an
   include/exclude decision per element: bit i set -> include nums[i]. No
   recursion, no call stack. Priced and implemented below — genuinely
   competitive, sometimes the "cleaner" answer to give first.
2. ITERATIVE DOUBLING — O(n * 2^n) time. Start with `[[]]`; for each new
   number, take every existing subset and add a COPY of it with the new
   number appended. After processing all n numbers, you have all 2^n subsets.
   No recursion either.
3. BACKTRACKING (include/skip PER ELEMENT) — the binary-tree framing from the
   question file's docstring: a `for` isn't needed, each level has exactly 2
   branches (include nums[i], or don't), decided in element order.
4. BACKTRACKING (combinations-style, extend-by-index) — the version above,
   and the one used here as the answer since it generalizes directly into
   006 (Combinations) and 009 (Combination Sum III) later in this topic.

All four are the same O(n * 2^n) order; the choice between them is about
which shape best matches the family of problems it plugs into, not raw speed
(the runtime demo below measures them and finds them close).


================================================================================
STEP BY STEP TRACE — nums = [1, 2, 3]
================================================================================
    backtrack(start=0, path=[])
      record []                                  results = [[]]
      i=0: choose 1 -> path=[1]
        backtrack(start=1, path=[1])
          record [1]                             results = [[], [1]]
          i=1: choose 2 -> path=[1,2]
            backtrack(start=2, path=[1,2])
              record [1,2]                       results += [[1,2]]
              i=2: choose 3 -> path=[1,2,3]
                backtrack(start=3, path=[1,2,3])
                  record [1,2,3]                  results += [[1,2,3]]
                  (no i left, i.e. start=3 == n) return
              unchoose 3 -> path=[1,2]
          unchoose 2 -> path=[1]
          i=2: choose 3 -> path=[1,3]
            backtrack(start=3, path=[1,3])
              record [1,3]                        results += [[1,3]]
              return
          unchoose 3 -> path=[1]
      unchoose 1 -> path=[]
      i=1: choose 2 -> path=[2]
        ... (record [2], then [2,3]) ...
      unchoose 2 -> path=[]
      i=2: choose 3 -> path=[3]
        ... (record [3]) ...
      unchoose 3 -> path=[]
    done. results = [[], [1], [1,2], [1,2,3], [1,3], [2], [2,3], [3]]  (8 = 2^3)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time         Space (aux)   Mutates input?  Note
    -------------------------------  -----------  ------------  ---------------  --------------------
    Backtracking, mutate + copy ✅   O(n * 2^n)    O(n)          no               path in place
    Backtracking, copy per call      O(n * 2^n)    O(n^2 * 2^n)  no               copies at every NODE,
                                                                                    not just leaf-record
    Bitmask (iterative)              O(n * 2^n)    O(1)          no               no recursion
    Iterative doubling               O(n * 2^n)    O(n * 2^n)    no               builds full lists at
                                                                                    each step

    WHERE O(n * 2^n) comes from: the search tree here has exactly 2^n nodes in
    total (every node is a distinct subset — a full binary tree of depth n has
    2^(n+1) - 1 = O(2^n) nodes overall), and recording each one is an O(n)-size
    copy into the results list. 2^n nodes x O(n) copy = O(n * 2^n).

    "Backtracking, copy per call" prices what happens if you pass a NEW list
    object to every recursive call instead of mutating one shared list: each
    of the O(2^n) calls does an O(n) copy just to CONSTRUCT its local `path`,
    on top of the O(n) copy already needed to record a leaf — same asymptotic
    order here since both factors are already O(n), but the constant roughly
    doubles, and for deeper/more branching search trees (permutations,
    combination-sum) this stacks up. Benchmark is below.


================================================================================
EDGE CASES
================================================================================
    nums = [1]           -> [[], [1]]                smallest non-trivial input;
                                                       2^1 = 2 subsets.
    nums = [0]            -> [[], [0]]                 0 is a normal, valid element
                                                       (not "falsy" special-cased).
    nums with negatives    -> works unchanged; there is no ordering/sign
                              assumption anywhere in the algorithm.
    len(nums) == 10 (max)  -> 2^10 = 1024 subsets; exercises the upper bound
                              without timing out.
    The EMPTY subset []     -> always present, always first if you record-then
                              -extend; must not be forgotten as "not a real
                              subset."


================================================================================
COMMON MISTAKES
================================================================================
1. `results.append(path)` instead of `results.append(path[:])`. THE classic
   copy-on-append trap (see CONTEXT.md §1) applied to backtracking: `path` is
   one shared list object mutated throughout the ENTIRE recursion via
   `append`/`pop`. Appending a bare reference means every entry in `results`
   points at that SAME object — by the time the recursion finishes and `path`
   is back to `[]`, every recorded "subset" is `[]` too. The demo below
   constructs this bug live and shows the corrupted output.
2. Recording only at LEAVES (`start == n`) instead of at every node. Subsets
   is unusual among this topic's problems in that every node — not just
   leaves — is a valid, complete answer; missing the record-at-every-node
   step returns only the n subsets of maximum extension from each start, not
   all 2^n.
3. Forgetting `path.pop()` (the unchoose step) after the recursive call —
   corrupts every subsequent sibling's `path`, producing subsets with
   leftover elements that were never legitimately re-chosen.
4. Using `i > start` as if it were the "II" dedupe guard from problem 003 —
   this problem has UNIQUE elements by constraint, so no dedupe logic is
   needed here; adding it anyway is harmless but a sign of pattern-matching
   without understanding why the guard exists.
5. Off-by-one in the bitmask approach: checking `mask & (1 << i)` against the
   wrong bit position, or iterating `range(2**n - 1)` and silently dropping
   the mask that represents the full set / empty set.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: The input may contain duplicate values — avoid duplicate subsets.
A: Problem 003 (Subsets II): sort first, then skip adjacent equal siblings at
   the same tree depth — topic guide Part 3.

Q: Generate subsets iteratively, no recursion, no bitmask.
A: The "iterative doubling" approach above: start with `[[]]`, and for each
   new number double the current result list by appending a copy of every
   existing subset with the new number added.

Q: What if n is large enough that 2^n itself is impractical (n > ~25)?
A: Then you cannot enumerate every subset at all — the problem shape needs to
   change (e.g. count/query subsets with a property via DP or meet-in-the-
   middle, rather than materialize all of them).

Q: Return subsets of a SPECIFIC size k only.
A: Prune: only extend `path` while `len(path) < k`, and only record when
   `len(path) == k`. This is exactly problem 006 (Combinations).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 90   Subsets II                    — duplicates, sort+skip (003 here)
    LC 77   Combinations                  — subsets fixed at size k (006 here)
    LC 216  Combination Sum III           — 006 + a sum target (009 here)
    LC 320  Generalized Abbreviation      — same include/skip binary shape
    LC 784  Letter Case Permutation       — same include/skip shape, on cases
================================================================================
"""

import time
from typing import List


class Solution:
    def subsets(self, nums: List[int]) -> List[List[int]]:
        """Backtracking, extend-by-index, ONE shared path list mutated in
        place. O(n * 2^n) time, O(n) auxiliary space. The answer — this shape
        generalizes directly into 006/009."""
        results: List[List[int]] = []
        path: List[int] = []
        n = len(nums)

        def backtrack(start: int) -> None:
            results.append(path[:])             # record at EVERY node, not just leaves
            for i in range(start, n):
                path.append(nums[i])             # CHOOSE
                backtrack(i + 1)                  # EXPLORE
                path.pop()                        # UNCHOOSE

        backtrack(0)
        return results

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def subsets_include_skip(self, nums: List[int]) -> List[List[int]]:
        """Backtracking, binary include/skip decision PER ELEMENT (the
        picture drawn in the question file's docstring). Records only at
        leaves (index == n), since every element has been decided by then."""
        results: List[List[int]] = []
        path: List[int] = []
        n = len(nums)

        def backtrack(i: int) -> None:
            if i == n:
                results.append(path[:])
                return
            path.append(nums[i])                 # CHOOSE: include
            backtrack(i + 1)
            path.pop()                            # UNCHOOSE
            backtrack(i + 1)                      # CHOOSE: skip (no path mutation)

        backtrack(0)
        return results

    def subsets_bitmask(self, nums: List[int]) -> List[List[int]]:
        """Iterative, no recursion: each of 2^n integers is an include/
        exclude mask. O(n * 2^n) time, O(1) extra space beyond the output."""
        n = len(nums)
        results = []
        for mask in range(1 << n):
            subset = [nums[i] for i in range(n) if mask & (1 << i)]
            results.append(subset)
        return results

    def subsets_iterative_doubling(self, nums: List[int]) -> List[List[int]]:
        """Iterative, no recursion, no bitmask: double the result list once
        per input number."""
        results = [[]]
        for x in nums:
            results += [subset + [x] for subset in results]
        return results

    # ------------------------------------------------------------------
    # Deliberate breakage — the copy-on-append trap.
    # ------------------------------------------------------------------
    def subsets_broken_no_copy(self, nums: List[int]) -> List[List[int]]:
        """✗ BROKEN ON PURPOSE — appends the shared `path` object itself,
        never a copy. Every recorded "subset" ends up pointing at the SAME
        list, which is mutated for the rest of the recursion."""
        results: List[List[int]] = []
        path: List[int] = []
        n = len(nums)

        def backtrack(start: int) -> None:
            results.append(path)                 # NO [:] — the bug
            for i in range(start, n):
                path.append(nums[i])
                backtrack(i + 1)
                path.pop()

        backtrack(0)
        return results


# ==============================================================================
# TESTS — run:  python 002_subsets_solution.py
# ==============================================================================
def _normalize(subsets_list):
    return sorted(sorted(s) for s in subsets_list)


CASES = [
    [1, 2, 3], [0], [1], [1, 2], [-2, -1], [4, 5, 6, 7], list(range(1, 6)),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    def brute(nums):
        # bitmask "oracle" as well, but written independently (list comp vs loop)
        n = len(nums)
        out = []
        for mask in range(1 << n):
            out.append([nums[i] for i in range(n) if (mask >> i) & 1])
        return out

    impls = [
        ("backtrack extend-by-idx", sol.subsets),
        ("backtrack include/skip ", sol.subsets_include_skip),
        ("bitmask iterative      ", sol.subsets_bitmask),
        ("iterative doubling     ", sol.subsets_iterative_doubling),
    ]
    for name, fn in impls:
        ok = all(_normalize(fn(nums)) == _normalize(brute(nums)) for nums in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Confirm the tree size matches the theoretical 2^n bound.
    # ----------------------------------------------------------------------
    print("\n--- node count vs theoretical 2^n, measured ---")

    def count_nodes(nums):
        count = [0]
        path = []
        n = len(nums)

        def backtrack(start):
            count[0] += 1
            for i in range(start, n):
                path.append(nums[i])
                backtrack(i + 1)
                path.pop()

        backtrack(0)
        return count[0]

    print(f"  {'n':>3} {'nodes visited':>14} {'2^n':>8}  match?")
    for n in (1, 2, 3, 5, 8, 10):
        nums = list(range(n))
        nodes = count_nodes(nums)
        theoretical = 2 ** n
        match = nodes == theoretical
        all_ok &= match
        print(f"  {n:>3} {nodes:>14} {theoretical:>8}  {'yes' if match else 'NO'}")

    # ----------------------------------------------------------------------
    # ⚠️ The copy-on-append trap, demonstrated live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  results.append(path) vs results.append(path[:]) ---")
    nums = [1, 2, 3]
    good = sol.subsets(nums)
    bad = sol.subsets_broken_no_copy(nums)
    print(f"  correct (append path[:]): {len(good)} subsets, "
          f"{len(set(tuple(s) for s in good))} DISTINCT: {sorted(good, key=len)}")
    print(f"  broken  (append path)   : {len(bad)} subsets, "
          f"{len(set(tuple(s) for s in bad))} DISTINCT: {bad}")
    corrupted = len(set(tuple(s) for s in bad)) == 1
    print(f"  every entry in the broken result is IDENTICAL "
          f"(all point at the same mutated list): {corrupted}")
    all_ok &= corrupted   # we WANT to have proven the bug is real

    # ----------------------------------------------------------------------
    # Timing: mutate-in-place vs copy-at-every-call.
    # ----------------------------------------------------------------------
    print("\n--- mutate-in-place vs a fresh list COPY at every recursive call ---")

    def subsets_copy_every_call(nums):
        results = []
        n = len(nums)

        def backtrack(start, path):
            results.append(path[:])
            for i in range(start, n):
                backtrack(i + 1, path + [nums[i]])   # NEW list every call

        backtrack(0, [])
        return results

    print(f"  {'n':>3} {'mutate in place (ms)':>21} {'copy every call (ms)':>21} {'ratio':>7}")
    for n in (12, 15, 18):
        nums = list(range(n))
        t0 = time.perf_counter(); sol.subsets(nums)
        t1 = time.perf_counter(); subsets_copy_every_call(nums)
        t2 = time.perf_counter()
        mut_ms = (t1 - t0) * 1000
        copy_ms = (t2 - t1) * 1000
        ratio = copy_ms / mut_ms if mut_ms > 0 else float("inf")
        print(f"  {n:>3} {mut_ms:>19.2f}ms {copy_ms:>19.2f}ms {ratio:>6.2f}x")
    print("  Mutating one shared list with append/pop avoids allocating a new")
    print("  O(depth)-sized list at every one of the O(2^n) recursive calls.")
    print("  The gap is modest at small n (CPython's allocator is fast) but")
    print("  grows with n, since 'copy every call' pays that allocation on")
    print("  EVERY node of the O(2^n)-node tree, not just at the leaves.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
