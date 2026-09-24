"""
================================================================================
SOLUTION · LeetCode 216 · Combination Sum III                           [Medium]
https://leetcode.com/problems/combination-sum-iii/
================================================================================

THE CORE IDEA
--------------
Problem 006 (Combinations) with the range fixed at 1..9 and a SUM condition
added at the leaf. Two constraints must hold simultaneously — exactly k digits
AND exactly sum n — and that is the whole reason this problem is worth doing:
each constraint gives an independent way to prove a branch is hopeless, and
together they cut the tree from both sides.

    need = k - len(path)        digits still required
    rem  = n - sum(path)        sum still required

    (a) COUNT bound   digits i..9 number 9 - i + 1; need at least `need` of
                      them        =>   i <= 9 - need + 1
    (b) SUM bound     the smallest sum reachable with `need` digits all >= i is
                          lo = need*i + need*(need-1)//2      (i, i+1, ...)
                      the largest with `need` digits all <= 9 is
                          hi = need*(19-need)//2              (9, 8, ...)
                      =>   prune unless   lo <= rem <= hi

Both directions of (b) matter and they fail on different inputs:

    rem < lo   you have already overshot; every completion is too big
    rem > hi   you can never catch up; every completion is too small

The `rem > hi` test is the one people forget. On k=2, n=45 it kills the entire
tree at the root — 45 is unreachable with two digits (max 9+8=17) — so the
answer comes back after ONE node instead of 45. Measured below.

THE LEAF TEST MUST CHECK BOTH CONDITIONS
-----------------------------------------
    if need == 0:
        if rem == 0: record
        return

Checking only `rem == 0` emits combinations of the wrong LENGTH. Checking only
`need == 0` emits combinations with the wrong SUM. Both bugs are silent and
both are demonstrated at runtime below. This is the same "two constraints, two
base-case terms" shape you will see again in LC 22 (Generate Parentheses).

WHAT THIS PROBLEM DOES *NOT* NEED — and why that is worth noticing
-------------------------------------------------------------------
No `sort()`. No duplicate-sibling skip. No `used[]` array. The input is the
fixed set 1..9: already ascending, already distinct. The increasing-index rule
alone guarantees each combination is produced exactly once, and there are no
equal values for a sibling skip to catch. Being able to say "008's idiom is
unnecessary here, and here is why" is worth more than reproducing it from
habit.

AN HONEST NOTE ON WHY WE PRUNE AT ALL
--------------------------------------
The entire search space is the subsets of {1..9}: 2^9 = 512. Every one of those
512 subsets has exactly one size and one sum, so summed over all (k, n) inputs
there are only 512 answers in the whole problem. Brute force passes LeetCode
instantly. So the pruning here is NOT what makes the solution viable — it is
the demonstration that you can bound a search space, which is exactly what
N-Queens (013) and Sudoku (014) will require for real. Say that distinction out
loud in an interview: "this input is small enough that it does not matter, and
here is the pruning anyway, because on a bigger digit range it would."

================================================================================
MULTIPLE APPROACHES
================================================================================

1. ALL 2^9 SUBSETS OF 1..9, FILTER BY SIZE AND SUM         (brute force)
   512 masks, `popcount == k`, `sum == n`. Genuinely fine for this problem and
   worth mentioning as the "the space is 512, I could enumerate it" answer.
   It does not generalise (change 9 to 40 and it dies), which is the reason it
   is not the answer given.

2. `itertools.combinations(range(1,10), k)` + sum filter
   The one-liner. C-coded, correct, and the honest "in production" answer. The
   tests use it as the independent oracle.

3. BACKTRACKING, NO PRUNING
   006's tree with a leaf test on both k and the sum. Correct baseline; the
   node counts below show what it costs.

4. BACKTRACKING + COUNT BOUND ONLY (006's pruning, unchanged)
   Cuts branches that cannot reach length k.

5. BACKTRACKING + BOTH BOUNDS                               <- the answer
   Count feasibility and sum feasibility, both checked before recursing.

6. DP / MEET IN THE MIDDLE
   Overkill and worth naming only to dismiss: for "how many combinations"
   (rather than listing) it is a small knapsack DP over (digit, count, sum).
   The counting twin, as always.

================================================================================
STEP BY STEP  ·  k = 3, n = 9
================================================================================

    Notation: `s=` start digit, `need` digits still required, `rem` sum still
    required. lo/hi are the sum bounds for that node.

    backtrack(s=1, need=3, rem=9)
      count bound: i <= 9 - 3 + 1 = 7
      hi for need=3: 9+8+7 = 24 >= 9, ok
    |
    +-- i=1  lo(need=2, from 2) = 2+3 = 5 <= rem-1=8 <= hi(need=2)=17  ok
    |   path=[1]  backtrack(s=2, need=2, rem=8)
    |   |  count bound: i <= 9 - 2 + 1 = 8
    |   +-- i=2  need=1 rem=6: lo=3 <= 6 <= hi=9   ok
    |   |        path=[1,2] backtrack(s=3, need=1, rem=6)
    |   |          i=3: rem-3 = 3 != 0, need becomes 0 -> not a leaf, prune
    |   |          i=4: 2 left over -> prune ... i=6: rem-6 = 0 ==> EMIT [1,2,6]
    |   |          i=7,8,9: 7,8,9 > 6 -> BREAK at i=7
    |   +-- i=3  path=[1,3] rem=5  -> i=5 gives 0 ==> EMIT [1,3,5]
    |   +-- i=4  path=[1,4] rem=4  -> need=1, lo = 5 > rem = 4 -> PRUNE
    |   |        (the smallest digit we may still pick is 5, already too big)
    |   +-- i=5  path=[1,5] rem=3  -> lo = 6 > 3 -> PRUNE
    |   +-- i=6,7,8: same, PRUNED by the lo test
    |   pop
    |
    +-- i=2  path=[2] rem=7  backtrack(s=3, need=2, rem=7)
    |   +-- i=3  path=[2,3] rem=4 -> i=4 gives 0 ==> EMIT [2,3,4]
    |   +-- i=4  path=[2,4] rem=3 -> lo = 5 > 3 -> PRUNE
    |   +-- i=5+ PRUNED
    |   pop
    |
    +-- i=3  need=2 rem=6: lo (two digits from 4) = 4+5 = 9 > 6 -> PRUNE
    +-- i=4  lo = 5+6 = 11 > 5 -> PRUNE
    +-- i=5,6,7: PRUNED the same way
        (and i=8, i=9 were never even in range: the count bound stopped at 7)

    Result: [[1,2,6], [1,3,5], [2,3,4]]   correct, lexicographic for free.

Now the same input WITHOUT the sum bounds: every one of i=1..7 at the root is
expanded, each into up to 8 children, each of those checking every remaining
digit. The tests count the exact nodes for both, and for the count-bound-only
and sum-bound-only variants separately, so you can see which bound carries the
weight on which input. Spoiler: it depends on the input, and the interesting
extremes are k=2, n=45 (the `hi` test alone collapses everything) and
k=9, n=45 (the count bound alone collapses everything).

================================================================================
COMPLEXITY SUMMARY
================================================================================

    Approach                       Time              Space      Mutates input?
    -----------------------------  ----------------  ---------  --------------
    All 2^9 subsets + filter       O(9 * 2^9) = O(1) O(1)       n/a (no input)
    itertools.combinations + sum   O(k * C(9,k))     O(k)       n/a
    Backtracking, no pruning       O(k * 2^9)        O(k) stack n/a
    Backtracking + count bound     fewer nodes       O(k) stack n/a
    Backtracking + both bounds ✅   fewest nodes      O(k) stack n/a

    Everything here is O(1) in the strict sense: the input is two small
    integers and the search space is a fixed 512 subsets. The right way to
    state the complexity in an interview is therefore in terms of the
    GENERALISED problem — digits 1..D, choose k:

        O(k * C(D,k)) to emit the answers, which is optimal (output-bound),
        and O(k) stack.

    "It's O(1) because the input is bounded" is technically true and reads as
    dodging the question. Give the generalised bound, then note that D = 9
    here so the whole thing is constant.

    Mutates input? There is no input array to mutate — a rare "n/a" row, and
    worth saying, because it is the reason no `sort()` and no defensive copy
    appear anywhere in this solution.

================================================================================
EDGE CASES
================================================================================

    k=4, n=1   -> []. The minimum sum of 4 distinct digits is 1+2+3+4 = 10,
                  so nothing works. With the `lo` bound this is pruned at the
                  ROOT (one node). Without it, the whole tree is walked to
                  find nothing. This is the problem statement's own example
                  and it exists to test exactly this.

    k=2, n=45  -> []. The maximum with 2 digits is 9+8 = 17. The `hi` bound
                  kills it at the root; the `lo` bound alone does not. This is
                  the input that proves you need BOTH directions.

    k=9, n=45  -> [[1,2,3,4,5,6,7,8,9]]. The unique maximal answer. The count
                  bound collapses the tree to a single chain (at every depth
                  `i <= 9 - need + 1` leaves exactly one legal digit), so the
                  answer is found in 10 nodes with no search at all.

    k=9, n=44  -> []. One less than the only achievable sum for k=9. Catches
                  an off-by-one in the `hi` formula: hi(9) = 9*(19-9)/2 = 45,
                  so 44 < 45 passes the `hi` test and must be rejected deeper
                  by the exact leaf test. A solution that tries to answer
                  purely from the bounds gets this wrong.

    k=2, n=3   -> [[1,2]]. The smallest legal input (k >= 2 per constraints).

    n > 45     -> [] for every k. The constraint allows n up to 60 precisely
                  so this is reachable; the `hi` bound handles all of it at
                  the root.

    k=1        -> outside the constraints (k >= 2), but interviewers ask.
                  Answer: [[n]] if 1 <= n <= 9 else []. The code handles it
                  correctly with no special case, which is a good sign the
                  bounds were derived rather than tuned.

================================================================================
COMMON MISTAKES
================================================================================

1. Leaf test on the sum only (`if rem == 0: record`).
   Emits combinations of every length that happens to sum to n — e.g. for
   k=3, n=9 it also emits [9] and [4,5]. Silent, and the output looks
   plausible. Demonstrated live below.

2. Leaf test on the length only (`if need == 0: record`).
   Emits every k-subset regardless of sum: C(9,k) results. Also silent.
   Demonstrated live.

3. Only pruning "too big" and forgetting "too small" (or vice versa).
   `rem < lo` and `rem > hi` are different tests that fire on different
   inputs. The node-count table below has a column for each, and the k=2,
   n=45 / k=4, n=1 rows show each one carrying the whole load alone.

4. Off-by-one in the count bound: `range(start, 9 - need + 1)` instead of
   `range(start, 9 - need + 2)`.
   Silently drops the last valid digit at every level; k=9, n=45 returns []
   instead of the one true answer. Same bug as problem 006's mistake 5, same
   detection trick: check the k == n-of-digits case.

5. `results.append(path)` instead of `path[:]`.
   The copy-on-append trap, unchanged from every other file in this topic.

6. Re-summing `path` to get the remaining sum at every node.
   Carry `rem` down. Same argument as 007, and here it also keeps the bound
   arithmetic readable.

7. Writing 008's duplicate-sibling skip out of habit.
   Harmless — the digits 1..9 contain no duplicates, so the guard never fires
   — but it tells the interviewer you are pattern-matching rather than
   reasoning. Know why it is unnecessary.

8. Allowing 0 as a digit.
   The problem says 1 through 9. A range starting at 0 lets [0,1,2] be a
   "3-digit" answer summing to 3 and, worse, admits leading-zero style
   duplicates in the general case. Start the range at 1.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================

Q: Generalise to digits 1..D. How does your pruning change?
A: Only the constants: the count bound becomes `i <= D - need + 1` and
   `hi = need*(2D - need + 1)//2` (the top `need` values of 1..D). Deriving
   `hi` from "sum of the largest `need` terms of an arithmetic run" rather
   than memorising `19` is the point of the question — 19 is just 2*9+1.

Q: How many combinations are there, without listing them?
A: A small DP over (digit index, count used, sum so far): O(D * k * n) states.
   The counting twin of every problem in this family.

Q: What if numbers can repeat?
A: Then it is LC 39 with candidates 1..9 and an extra length constraint: use
   `backtrack(i)` instead of `backtrack(i + 1)` and keep both bounds (the
   `lo` bound becomes `need * i`, since all `need` digits could equal i).

Q: What if k is not fixed — "any number of digits summing to n"?
A: Drop the count bound and the `need == 0` leaf test; record whenever
   `rem == 0`. That is the subsets-with-a-sum-target shape, i.e. LC 40 over
   the digits 1..9.

Q: Return the combinations in reverse lexicographic order?
A: Iterate the loop from 9 down to `start` and the output reverses. Do not
   generate and sort — the tree order is already a total order, and being able
   to control it is the point of the increasing-index rule.

Q: Can you do it iteratively / with bitmasks?
A: Yes, and here it is genuinely reasonable: loop over the 512 masks, keep
   those with `bin(mask).count('1') == k` and the right sum. That is the
   brute force from approach 1, and at D = 9 it is arguably the best answer.
   Say so — recognising when the "clever" solution is unnecessary is a
   signal, not a weakness.

Q: What is the largest k for which an answer exists at all?
A: 9, and only for n = 45. More usefully: for each k the achievable sums form
   the contiguous range [k(k+1)/2, k(19-k)/2], which is precisely the `lo`/`hi`
   pair at the root. Answering with the closed-form range shows you understood
   the bounds instead of copying them.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================

    THE COMBINATION SUM FAMILY — one axis flipped per problem:
      LC 77   Combinations        - problem 006. Fixed k, no sum.
      LC 39   Combination Sum     - problem 007. Sum, reuse, no length.
      LC 40   Combination Sum II  - problem 008. Sum, no reuse, duplicate input.
      LC 216  Combination Sum III - HERE. Sum AND fixed length, digits 1..9.
      LC 377  Combination Sum IV  - a DP that counts PERMUTATIONS. Named to
                                    mislead; it is not in this family at all.

    TWO-CONSTRAINT LEAF TESTS AND FEASIBILITY PRUNING elsewhere:
      LC 22   Generate Parentheses  - two counters (open, close), and the
                                      pruning IS the validity rule
      LC 967  Numbers With Same     - digits + a difference constraint, same
              Consecutive Diff        bounded-digit tree
      LC 1291 Sequential Digits     - the digits 1..9 tree with a range filter
      LC 51   N-Queens              - problem 013. Feasibility pruning where
                                      the constraint is geometric, not numeric.
      LC 37   Sudoku Solver         - problem 014. Same idea, taken to its
                                      limit: prune before every placement.

    The tell for this exact problem: a FIXED number of items AND a fixed sum,
    over a small fixed alphabet. Two constraints means two prunings; if you can
    only see one, you have not finished reading the problem.
================================================================================
"""

import time
from itertools import combinations
from typing import List


class Solution:
    def combinationSum3(self, k: int, n: int) -> List[List[int]]:
        """Backtracking with two-sided pruning (count feasibility + sum
        feasibility). The answer."""
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, need: int, rem: int) -> None:
            if need == 0:
                if rem == 0:
                    results.append(path[:])      # COPY
                return
            # SUM bound, "can never catch up": largest sum from `need` digits
            # taken from the top of 1..9.
            if rem > need * (19 - need) // 2:
                return
            # COUNT bound: digits start..9 must number at least `need`.
            for digit in range(start, 9 - need + 2):
                # SUM bound, "already overshot": smallest sum from `need`
                # digits all >= digit is digit + (digit+1) + ...
                if need * digit + need * (need - 1) // 2 > rem:
                    break                        # ascending, so the tail is worse
                path.append(digit)               # CHOOSE
                backtrack(digit + 1, need - 1, rem - digit)   # EXPLORE
                path.pop()                       # UNCHOOSE

        backtrack(1, k, n)
        return results

    # ------------------------------------------------------------------
    # Alternatives, kept for the comparisons the tests run.
    # ------------------------------------------------------------------
    def combinationSum3_no_pruning(self, k: int, n: int) -> List[List[int]]:
        """Plain 006 tree plus a two-part leaf test. Correct baseline."""
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, need: int, rem: int) -> None:
            if need == 0:
                if rem == 0:
                    results.append(path[:])
                return
            for digit in range(start, 10):
                path.append(digit)
                backtrack(digit + 1, need - 1, rem - digit)
                path.pop()

        backtrack(1, k, n)
        return results

    def combinationSum3_count_bound_only(self, k: int, n: int) -> List[List[int]]:
        """006's count bound, no sum reasoning."""
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, need: int, rem: int) -> None:
            if need == 0:
                if rem == 0:
                    results.append(path[:])
                return
            for digit in range(start, 9 - need + 2):
                path.append(digit)
                backtrack(digit + 1, need - 1, rem - digit)
                path.pop()

        backtrack(1, k, n)
        return results

    def combinationSum3_bitmask(self, k: int, n: int) -> List[List[int]]:
        """All 2^9 subsets of 1..9, filtered. 512 masks — genuinely a fine
        answer for this input size, and it shares no code with the recursion."""
        out: List[List[int]] = []
        for mask in range(1 << 9):
            if bin(mask).count("1") != k:
                continue
            chosen = [d for d in range(1, 10) if mask & (1 << (d - 1))]
            if sum(chosen) == n:
                out.append(chosen)
        return out

    def combinationSum3_itertools(self, k: int, n: int) -> List[List[int]]:
        """The production one-liner."""
        return [list(c) for c in combinations(range(1, 10), k) if sum(c) == n]

    # ------------------------------------------------------------------
    # Deliberately broken — the tests prove these are wrong at runtime.
    # ------------------------------------------------------------------
    def combinationSum3_sum_only_leaf(self, k: int, n: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 1: records whenever the sum hits n, ignoring k."""
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, rem: int) -> None:
            if rem == 0:
                results.append(path[:])          # BUG: no length check
                return
            for digit in range(start, 10):
                if digit > rem:
                    break
                path.append(digit)
                backtrack(digit + 1, rem - digit)
                path.pop()

        backtrack(1, n)
        return results

    def combinationSum3_length_only_leaf(self, k: int, n: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 2: records every k-subset, ignoring the sum."""
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, need: int) -> None:
            if need == 0:
                results.append(path[:])          # BUG: no sum check
                return
            for digit in range(start, 9 - need + 2):
                path.append(digit)
                backtrack(digit + 1, need - 1)
                path.pop()

        backtrack(1, k)
        return results

    def combinationSum3_bad_bound(self, k: int, n: int) -> List[List[int]]:
        """✗ BROKEN — MISTAKE 4: count bound missing the +1 in the range end."""
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int, need: int, rem: int) -> None:
            if need == 0:
                if rem == 0:
                    results.append(path[:])
                return
            for digit in range(start, 9 - need + 1):     # BUG: should be + 2
                path.append(digit)
                backtrack(digit + 1, need - 1, rem - digit)
                path.pop()

        backtrack(1, k, n)
        return results


def _count_nodes(k: int, n: int, count_bound: bool, sum_lo: bool,
                 sum_hi: bool) -> int:
    """Recursive-call count for any combination of the three prunings."""
    calls = [0]

    def backtrack(start: int, need: int, rem: int) -> None:
        calls[0] += 1
        if need == 0:
            return
        if sum_hi and rem > need * (19 - need) // 2:
            return
        end = (9 - need + 2) if count_bound else 10
        for digit in range(start, end):
            if sum_lo and need * digit + need * (need - 1) // 2 > rem:
                break
            backtrack(digit + 1, need - 1, rem - digit)

    backtrack(1, k, n)
    return calls[0]


def _norm(results):
    return sorted(tuple(sorted(r)) for r in results)


CASES = [(k, n) for k in range(1, 10) for n in range(1, 61)]
SPOTLIGHT = [(3, 7), (3, 9), (4, 1), (2, 18), (9, 45), (9, 44), (2, 3),
             (5, 15), (4, 30), (3, 60), (2, 45), (8, 40)]


# ==============================================================================
# TESTS — run:  python 009_combination_sum_iii_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True

    # ----------------------------------------------------------------------
    # 1. Correctness on EVERY (k, n) pair in and around the constraints.
    # ----------------------------------------------------------------------
    print(f"--- correctness vs itertools on all {len(CASES)} (k, n) pairs, "
          f"k=1..9, n=1..60 ---")
    impls = [
        ("two-sided pruning    ", sol.combinationSum3),
        ("no pruning           ", sol.combinationSum3_no_pruning),
        ("count bound only     ", sol.combinationSum3_count_bound_only),
        ("bitmask over 2^9     ", sol.combinationSum3_bitmask),
        ("itertools one-liner  ", sol.combinationSum3_itertools),
    ]
    for name, fn in impls:
        bad = [(k, n) for k, n in CASES
               if _norm(fn(k, n)) != _norm(
                   [list(c) for c in combinations(range(1, 10), k) if sum(c) == n])]
        ok = not bad
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} "
              f"({len(CASES)} pairs{'' if ok else f', failed {bad[:5]}'})")

    total_answers = sum(len(sol.combinationSum3(k, n)) for k, n in CASES)
    print(f"PASS  total answers over all (k, n) = {total_answers}, which is "
          f"2^9 - 1 = 511")
    print("      (every non-empty subset of 1..9 is the answer to exactly one")
    print("       (k, n) pair — a nice global sanity check that nothing is")
    print("       double-counted or missing)")
    all_ok &= total_answers == 511

    # ----------------------------------------------------------------------
    # 2. ⚠️ THE LEAF TEST NEEDS BOTH CONDITIONS.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  leaf test: both conditions vs one ---")
    k, n = 3, 9
    good = sol.combinationSum3(k, n)
    sum_only = sol.combinationSum3_sum_only_leaf(k, n)
    len_only = sol.combinationSum3_length_only_leaf(k, n)
    print(f"  k={k}, n={n}")
    print(f"  need == 0 AND rem == 0 -> {len(good):>2}  {sorted(good)}")
    print(f"  rem == 0 only          -> {len(sum_only):>2}  {sorted(sum_only)}")
    print(f"      wrong lengths: "
          f"{sorted(c for c in sum_only if len(c) != k)}")
    print(f"  need == 0 only         -> {len(len_only):>2}  every 3-subset, "
          f"C(9,3) = 84")
    print(f"      wrong sums: {len([c for c in len_only if sum(c) != n])} of "
          f"{len(len_only)}")
    print("  Neither bug raises anything. The first returns extra answers of the")
    print("  wrong length, the second returns C(9,k) answers with arbitrary")
    print("  sums. Two constraints, two terms in the base case — always.")
    all_ok &= (len(sum_only) > len(good) and len(len_only) == 84)

    # ----------------------------------------------------------------------
    # 3. ⚠️ MISTAKE 4 — the off-by-one count bound.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  count bound: `9 - need + 2` vs `9 - need + 1` ---")
    print(f"  {'k':>3} {'n':>4} {'correct':>8} {'off-by-one':>11}  lost")
    bound_bug = False
    for k, n in ((9, 45), (3, 24), (4, 30), (2, 17), (5, 35)):
        a = len(sol.combinationSum3(k, n))
        b = len(sol.combinationSum3_bad_bound(k, n))
        bound_bug |= b < a
        print(f"  {k:>3} {n:>4} {a:>8} {b:>11}  {a - b}")
    print("  k=9, n=45 is the detector: the only answer is [1..9], which needs")
    print("  the last digit at every level. Drop the +1 and it disappears.")
    all_ok &= bound_bug

    # ----------------------------------------------------------------------
    # 4. THE MAIN EVENT — recursive calls with and without each pruning.
    # ----------------------------------------------------------------------
    print("\n--- recursive calls: each pruning measured separately ---")
    print(f"  {'k':>3} {'n':>4} {'answers':>8} {'none':>8} {'count':>8} "
          f"{'sum lo':>8} {'sum hi':>8} {'all three':>10} {'saved':>8}")
    prune_ok = True
    for k, n in SPOTLIGHT:
        ans = len(sol.combinationSum3(k, n))
        none = _count_nodes(k, n, False, False, False)
        cnt = _count_nodes(k, n, True, False, False)
        lo = _count_nodes(k, n, False, True, False)
        hi = _count_nodes(k, n, False, False, True)
        both = _count_nodes(k, n, True, True, True)
        prune_ok &= both <= none
        print(f"  {k:>3} {n:>4} {ans:>8} {none:>8} {cnt:>8} {lo:>8} {hi:>8} "
              f"{both:>10} {none / both:>7.1f}x")
    all_ok &= prune_ok
    print("  READ THE ROWS INDIVIDUALLY — this is why 'add pruning' is not one")
    print("  piece of advice:")
    print("    k=2, n=45 : impossible (max is 9+8=17). The `sum hi` test alone")
    print("                ends it at the root; the count bound alone does")
    print("                nothing at all.")
    print("    k=4, n=1  : impossible (min is 1+2+3+4=10). Now it is `sum lo`")
    print("                that ends it immediately and `sum hi` that is idle.")
    print("    k=9, n=45 : the count bound alone collapses the tree to a single")
    print("                chain — there is never more than one legal digit.")
    print("    k=3, n=9  : all three contribute a little; no single one wins.")
    print("  That is the whole lesson: each bound is a different proof of")
    print("  hopelessness, and which one fires depends on the input. Ship both.")

    # ----------------------------------------------------------------------
    # 5. Totals across the whole input space.
    # ----------------------------------------------------------------------
    print("\n--- totals over all 540 (k, n) pairs, k=1..9, n=1..60 ---")
    tot = {}
    for label, cb, lo_, hi_ in (("no pruning", False, False, False),
                                ("count bound only", True, False, False),
                                ("sum lo only", False, True, False),
                                ("sum hi only", False, False, True),
                                ("count + sum lo", True, True, False),
                                ("all three", True, True, True)):
        tot[label] = sum(_count_nodes(k, n, cb, lo_, hi_) for k, n in CASES)
    base = tot["no pruning"]
    print(f"  {'configuration':<20} {'total calls':>12} {'vs none':>9}")
    for label in ("no pruning", "count bound only", "sum lo only",
                  "sum hi only", "count + sum lo", "all three"):
        print(f"  {label:<20} {tot[label]:>12} {base / tot[label]:>8.1f}x")
    print(f"  Summed over the entire input space the two-sided version does")
    print(f"  {base / tot['all three']:.1f}x less work than the unpruned tree,")
    print("  and it produces exactly the same 511 answers. Note `sum lo only`")
    print("  is already most of the win: it is the test that notices you have")
    print("  overshot, which is the common case across this input space.")
    all_ok &= tot["all three"] <= tot["no pruning"]

    # ----------------------------------------------------------------------
    # 6. Wall clock over the whole input space.
    # ----------------------------------------------------------------------
    print("\n--- wall clock: solving ALL 540 (k, n) pairs, once each (ms) ---")
    for label, fn in (("two-sided pruning", sol.combinationSum3),
                      ("count bound only", sol.combinationSum3_count_bound_only),
                      ("no pruning", sol.combinationSum3_no_pruning),
                      ("bitmask over 2^9", sol.combinationSum3_bitmask),
                      ("itertools", sol.combinationSum3_itertools)):
        t0 = time.perf_counter()
        for k, n in CASES:
            fn(k, n)
        print(f"  {label:<20} {(time.perf_counter() - t0) * 1e3:>9.2f} ms")
    print("  itertools wins because it is C-coded and C(9,k) is tiny; the")
    print("  bitmask version is the slowest because it pays 512 masks and a")
    print("  `bin().count('1')` for EVERY (k, n) pair regardless of how")
    print("  hopeless the pair is — no early exit at all. The pruned")
    print("  backtracker is the only one whose cost tracks the difficulty of")
    print("  the individual input, which is the property that matters when the")
    print("  digit range is not 9.")

    # ----------------------------------------------------------------------
    # 7. The closed-form achievable range, checked against the search.
    # ----------------------------------------------------------------------
    print("\n--- the `lo`/`hi` bounds at the root ARE the achievable range ---")
    print(f"  {'k':>3} {'lo = k(k+1)/2':>14} {'hi = k(19-k)/2':>15} "
          f"{'n with answers':>16}  match?")
    range_ok = True
    for k in range(1, 10):
        lo = k * (k + 1) // 2
        hi = k * (19 - k) // 2
        ns = [n for n in range(1, 61) if sol.combinationSum3(k, n)]
        match = ns == list(range(lo, hi + 1))
        range_ok &= match
        print(f"  {k:>3} {lo:>14} {hi:>15} {f'{ns[0]}..{ns[-1]}':>16}  "
              f"{'yes' if match else 'NO'}")
    print("  Every achievable sum in [lo, hi] is achievable and nothing outside")
    print("  it is — so the root bounds are TIGHT, not merely valid. That is")
    print("  the answer to 'what is the largest k for which an answer exists?'")
    print("  and it is derived, not memorised.")
    all_ok &= range_ok

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
