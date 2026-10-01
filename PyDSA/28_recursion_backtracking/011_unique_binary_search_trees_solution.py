"""
================================================================================
SOLUTION · LeetCode 96 · Unique Binary Search Trees                     [Medium]
https://leetcode.com/problems/unique-binary-search-trees/
================================================================================

THE CORE IDEA
--------------
Every choice of root value `r` in `1..n` forces a UNIQUE split: left
subtree gets exactly `{1,...,r-1}` (`r-1` values), right subtree gets
exactly `{r+1,...,n}` (`n-r` values) — the BST property leaves no other
option. So `numTrees(n)` sums, over every root choice, the product of
"ways to shape the left" and "ways to shape the right." This is BRANCHING
recursion with heavily OVERLAPPING subproblems (the same smaller `n`
values get needed over and over) — the exact shape that makes
memoization pay off, deliberately placed right after 009's tree recursion
to make the Fibonacci-style blowup and its fix concrete again.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. NAIVE RECURSION, NO MEMO — priced, not fully run: recomputes
   `numTrees(k)` for every smaller `k` exponentially many times, same
   growth pattern as naive Fibonacci. Demonstrated live below via a call
   counter, not just claimed.
2. MEMOIZED RECURSION — cache `numTrees(k)` the first time it's computed.
   O(n^2) time (n values, each summing over up to n root choices),
   O(n) space for the cache (plus O(n) call stack). The version taught
   here.
3. ITERATIVE DP (BOTTOM-UP) — build a table `dp[0..n]` from `dp[0]=1`
   upward, same recurrence, no recursion at all. O(n^2) time, O(n) space.
   What to write in an interview once the recursive idea is explained.
4. CLOSED FORM (CATALAN NUMBER) — `numTrees(n)` IS the n-th Catalan
   number, `C(2n, n) / (n + 1)`. O(n) time (computing one binomial
   coefficient), O(1) extra space beyond the big integer itself. Named
   as the mathematical fact this recurrence is secretly computing,
   verified below against the DP table rather than only asserted.


================================================================================
STEP BY STEP TRACE — numTrees(3)
================================================================================
    numTrees(3): try every root r in {1,2,3}
      r=1: left={}, right={2,3}       -> numTrees(0) * numTrees(2) = 1 * 2 = 2
      r=2: left={1}, right={3}        -> numTrees(1) * numTrees(1) = 1 * 1 = 1
      r=3: left={1,2}, right={}       -> numTrees(2) * numTrees(0) = 2 * 1 = 2
    numTrees(3) = 2 + 1 + 2 = 5

    numTrees(2) itself needed numTrees(0) and numTrees(1):
      r=1: left={}, right={2}  -> numTrees(0)*numTrees(1) = 1*1 = 1
      r=2: left={1}, right={}  -> numTrees(1)*numTrees(0) = 1*1 = 1
    numTrees(2) = 1 + 1 = 2

Note `numTrees(0)` and `numTrees(1)` were each needed multiple times
across just this one small trace — the overlap that memoization exploits.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time            Space           Mutates input?  Note
    -----------------------  --------------  --------------  ---------------  --------------------------------
    Naive recursion, no memo exponential     O(n) stack      no               same blowup shape as naive Fib
    Memoized recursion       O(n^2)          O(n) cache+stack no              the version taught here
    Iterative DP             O(n^2)          O(n)            no               no recursion, same recurrence
    Closed form (Catalan)    O(n)            O(1) extra       no               verified against DP below


================================================================================
EDGE CASES
================================================================================
    n = 0 (not in constraints, but the base case)  -> 1   the empty tree
                                is exactly one valid shape — this is
                                what makes multiplying by
                                `numTrees(r-1)` or `numTrees(n-r)` correct
                                when a subtree is empty, rather than
                                zeroing the whole product out.
    n = 1              -> 1    a single node, one trivial shape.
    n = 19             -> the upper constraint bound; the largest n
                                whose Catalan number still fits safely,
                                exercising real recursion depth and a
                                sizable memo table.


================================================================================
COMMON MISTAKES
================================================================================
1. Setting the base case to `numTrees(0) = 0` instead of `1` — this makes
   every product involving an empty subtree collapse to 0, silently
   producing 0 for every input instead of the correct count.
2. Iterating `r` (the root choice) but computing `numTrees(n - r)` for
   the WRONG side, e.g. swapping which factor is "left" and which is
   "right" — since multiplication is commutative this specific swap
   doesn't actually change the final sum's value, but it's a sign of not
   tracking which count represents which physical subtree, which DOES
   matter in 012 where actual tree shapes (not just counts) are built.
3. Memoizing on the wrong key — this problem's `numTrees(k)` result only
   depends on the COUNT `k`, never on which specific values are in the
   subtree, so memoizing on `n` alone (not on the actual set of values)
   is correct and sufficient; over-keying (e.g. trying to cache on a
   tuple of the actual value range) wastes memory without adding
   correctness.
4. Forgetting to memoize at all and being surprised numTrees(19) is slow
   — the naive version's call count grows roughly like the Catalan
   numbers themselves (exponential in n), demonstrated live below.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you avoid recursion entirely?
A: Yes — the iterative bottom-up DP: `dp[0] = 1`, then for each `k` from
   1 to n, `dp[k] = sum(dp[r-1] * dp[k-r] for r in 1..k)`.

Q: What sequence of numbers is this, mathematically?
A: The Catalan numbers — `numTrees(n) = C(n) = C(2n, n) / (n + 1)`. They
   also count balanced parenthesizations, non-crossing partitions, and
   several other classic combinatorial structures.

Q: How does this differ from 012 (Unique Binary Search Trees II)?
A: This counts shapes; 012 must actually BUILD and return every distinct
   tree. The recurrence is identical, but 012's "combine step" builds new
   TreeNode objects (a cross product of every left shape with every
   right shape) instead of just multiplying counts.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 012 Unique Binary Search Trees II — the harder version:
                                       build every actual tree, not just
                                       count them.
    Topic 09 Recursion & Backtracking (Fibonacci)  — the same naive-vs-
                                       memoized blowup pattern, minimal
                                       form.
    Topic 28, 015 All Possible Full Binary Trees — another "count/build
                                       via splitting into left+right"
                                       recursion.
================================================================================
"""

class Solution:
    def numTrees(self, n: int) -> int:
        """Memoized recursion. O(n^2) time, O(n) space."""
        memo = {0: 1, 1: 1}

        def count(k: int) -> int:
            if k in memo:
                return memo[k]
            total = 0
            for r in range(1, k + 1):
                total += count(r - 1) * count(k - r)
            memo[k] = total
            return total

        return count(n)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def numTrees_naive_no_memo(self, n: int, calls: list = None) -> int:
        """No memoization, exponential blowup. `calls` counts total calls made."""
        if calls is not None:
            calls[0] += 1
        if n <= 1:
            return 1
        total = 0
        for r in range(1, n + 1):
            total += (self.numTrees_naive_no_memo(r - 1, calls)
                      * self.numTrees_naive_no_memo(n - r, calls))
        return total

    def numTrees_iterative_dp(self, n: int) -> int:
        """Bottom-up DP, no recursion. O(n^2) time, O(n) space."""
        dp = [1] * (n + 1)
        for k in range(2, n + 1):
            dp[k] = sum(dp[r - 1] * dp[k - r] for r in range(1, k + 1))
        return dp[n]

    def numTrees_catalan_closed_form(self, n: int) -> int:
        """Closed form: the n-th Catalan number via a binomial coefficient."""
        from math import comb
        return comb(2 * n, n) // (n + 1)


# ==============================================================================
# TESTS — run:  python 011_unique_binary_search_trees_solution.py
# ==============================================================================
CASES = [
    (1, 1), (2, 2), (3, 5), (4, 14), (5, 42), (6, 132), (19, 1767263190),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("memoized recursion  ", sol.numTrees),
        ("iterative DP        ", sol.numTrees_iterative_dp),
        ("Catalan closed form ", sol.numTrees_catalan_closed_form),
    ]

    for name, fn in impls:
        ok = all(fn(n) == expected for n, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- naive-recursion call count blowup, measured live (not just claimed) ---")
    print(f"  {'n':>4} {'total calls (no memo)':>24} {'memoized version calls?':>26}")
    for n in (1, 5, 10, 15):
        calls = [0]
        sol.numTrees_naive_no_memo(n, calls)
        print(f"  {n:>4} {calls[0]:>24}     (grows exponentially in n)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
