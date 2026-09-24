"""
================================================================================
SOLUTION · LeetCode 279 · Perfect Squares                             [Medium]
https://leetcode.com/problems/perfect-squares/
================================================================================

THE CORE IDEA
--------------
dp[i] MEANS "the minimum count of perfect squares summing to EXACTLY i" --
value-indexed unbounded-knapsack DP, identical in shape to Coin Change
(010) with the coin denominations replaced by the perfect squares <= n:

    dp[0] = 0
    dp[i] = 1 + min(dp[i - k*k] for k in 1.. while k*k <= i)

Reusable "coins" (any square can be used any number of times), so iterate
the target axis low to high, exactly like Coin Change.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion, price it, don't ship it): try every square
<= remaining as the next square used, recurse on the remainder. O(exponential)
-- the same remainder gets reached via many different square sequences.

Approach 1 (BFS over remainders) -- treat each value 0..n as a node, each
perfect square as an edge; BFS from n finds the shortest path (=fewest
squares) to 0. O(n * sqrt(n)) time, same complexity as DP, a valid
alternative framing (exactly like Coin Change's BFS alternative).

Approach 2 (memoized top-down) [`num_squares_memo`] -- cache dp[i] the
first time it's computed. O(n * sqrt(n)) time, O(n) space + recursion depth.

Approach 3 (tabulated bottom-up) [chosen] -- fill dp[0..n] left to right,
trying every square <= i at each step. O(n * sqrt(n)) time, O(n) space,
no recursion depth risk.

(A number-theoretic O(sqrt(n)) approach exists via Lagrange's four-square
theorem and Legendre's three-square theorem, checking whether n is a
perfect square, a sum of two squares, or of the specific 4^a(8b+7) form
that requires exactly four -- correct and much faster, but a specialized
result most interviewers don't expect derived from scratch; worth NAMING.)


================================================================================
STEP BY STEP TRACE
================================================================================
n = 12    (perfect squares <= 12: 1, 4, 9)

dp[0] = 0
dp[1] = 1 + min(dp[0]) = 1                              (1)
dp[2] = 1 + min(dp[1]) = 2                                (1+1)
dp[3] = 1 + min(dp[2]) = 3                                (1+1+1)
dp[4] = 1 + min(dp[3], dp[0]) = 1 + min(3,0) = 1           (4)
dp[5] = 1 + min(dp[4], dp[1]) = 1 + min(1,1) = 2           (4+1)
dp[6] = 1 + min(dp[5], dp[2]) = 1 + min(2,2) = 3           (4+1+1)
dp[7] = 1 + min(dp[6], dp[3]) = 1 + min(3,3) = 4           (4+1+1+1)
dp[8] = 1 + min(dp[7], dp[4]) = 1 + min(4,1) = 2           (4+4)
dp[9] = 1 + min(dp[8], dp[5], dp[0]) = 1 + min(2,2,0) = 1  (9)
dp[10]= 1 + min(dp[9], dp[6], dp[1]) = 1 + min(1,3,1) = 2  (9+1)
dp[11]= 1 + min(dp[10],dp[7], dp[2]) = 1 + min(2,4,2) = 3  (9+1+1)
dp[12]= 1 + min(dp[11],dp[8], dp[3]) = 1 + min(3,2,3) = 3  (4+4+4)  <- answer

 i    : 0  1  2  3  4  5  6  7  8  9  10 11 12
dp[i] : 0  1  2  3  1  2  3  4  2  1  2  3  3


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time            Space           Mutates input?
    ------------------------------  --------------  --------------  --------------
    Naive recursion                  exponential     O(n) depth      n/a (no input array)
    BFS over remainders               O(n * sqrt(n)) O(n)            n/a
    Memoized top-down                 O(n * sqrt(n)) O(n)            n/a
    Tabulated bottom-up [chosen]      O(n * sqrt(n)) O(n)            n/a
    Number-theoretic (Lagrange/Legendre) O(sqrt(n))  O(1)            n/a


================================================================================
EDGE CASES
================================================================================
    n is itself a perfect square (4, 9, 100) -> answer 1 -- confirms the
                              k*k == i candidate is correctly included in
                              the min() (not accidentally excluded by an
                              off-by-one in the `k*k <= i` bound).
    n == 1                    -> dp[1] = 1 (just "1", itself a perfect
                              square); smallest nontrivial input.
    n requires exactly 4 squares
    (Legendre's theorem: numbers
    of the form 4^a(8b+7), e.g. 7)
                              -> the worst case for this problem; every
                              positive integer needs at most 4 (Lagrange's
                              four-square theorem guarantees this upper
                              bound), so dp[i] is always in {1,2,3,4}.


================================================================================
COMMON MISTAKES
================================================================================
1. Regenerating `k*k` inside the innermost loop via `int(k**0.5)**2==i`
   floating-point checks instead of a clean integer `k*k <= i` loop --
   floating point sqrt can be off by one ULP near perfect squares and
   silently misclassify a square as non-square (or vice versa).
2. Copying Coin Change's structure but forgetting that "1" is ALWAYS a
   valid perfect square (1*1=1) -- omitting it from the candidate set
   would make some amounts falsely unreachable.
3. Believing greedy ("always take the largest square that fits") is
   optimal -- it is NOT in general for this style of problem (though it
   happens to work for many small n, it can fail; DP is required for a
   provably correct answer, similar to why Coin Change needs DP rather
   than greedy for arbitrary coin sets).
4. Off-by-one in the outer loop bound: `range(1, n+1)` is required to
   compute dp[n] itself, not stopping at n-1.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you do this in O(sqrt(n)) or better?" -> yes, via Legendre's
  three-square theorem: check n is a perfect square (1), else check if
  n is expressible as a sum of two squares (2, via trial over k*k<=n/2),
  else check the 4^a(8b+7) exclusion form for "must be 4" (4), else it's 3
  by Legendre's theorem. Worth NAMING even if not derived live.
- "How does this compare to Coin Change (010)?" -> identical unbounded
  1D DP shape; the "coin set" here is generated (perfect squares) instead
  of given directly -- good moment to point out the pattern transfers.
- "What if you needed the actual squares used, not just the count?" ->
  track `last_square[i]` alongside dp during tabulation, then walk it
  backwards from n.


================================================================================
RELATED PROBLEMS
================================================================================
- 010 Coin Change (LC 322) -- the direct template this problem reuses,
  "coins" replaced by perfect squares.
- 015 Combination Sum IV (LC 377) -- same value-indexed unbounded DP
  family, counting ORDERED ways instead of minimizing count.
- Numbers with an equal count of divisors etc. -- broader number-theory
  DP family where "generate the candidate set, then Coin-Change it" recurs.
================================================================================
"""

import math
import time
from collections import deque

INF = float("inf")


class Solution:
    def numSquares(self, n: int) -> int:
        squares = []
        k = 1
        while k * k <= n:
            squares.append(k * k)
            k += 1

        dp = [0] + [INF] * n
        for i in range(1, n + 1):
            for sq in squares:
                if sq > i:
                    break
                if dp[i - sq] + 1 < dp[i]:
                    dp[i] = dp[i - sq] + 1
        return dp[n]


def num_squares_naive(n: int) -> int:
    def solve(remaining: int) -> float:
        if remaining == 0:
            return 0
        if remaining < 0:
            return INF
        best = INF
        k = 1
        while k * k <= remaining:
            best = min(best, 1 + solve(remaining - k * k))
            k += 1
        return best

    return int(solve(n))


def num_squares_memo(n: int) -> int:
    memo = {0: 0}

    def solve(remaining: int) -> int:
        if remaining in memo:
            return memo[remaining]
        best = INF
        k = 1
        while k * k <= remaining:
            best = min(best, 1 + solve(remaining - k * k))
            k += 1
        memo[remaining] = best
        return best

    return solve(n)


def num_squares_bfs(n: int) -> int:
    if n == 0:
        return 0
    squares = []
    k = 1
    while k * k <= n:
        squares.append(k * k)
        k += 1

    visited = {n}
    queue = deque([n])
    steps = 0
    while queue:
        steps += 1
        for _ in range(len(queue)):
            remaining = queue.popleft()
            for sq in squares:
                nxt = remaining - sq
                if nxt == 0:
                    return steps
                if nxt > 0 and nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
    return -1


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (12, 3),
        (13, 2),
        (1, 1),
        (2, 2),
        (4, 1),
        (7, 4),
        (100, 1),
    ]
    for n, want in cases:
        got = sol.numSquares(n)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:3d}  -> {got}  (want {want})")
        assert num_squares_memo(n) == want
        assert num_squares_bfs(n) == want

    print()
    print("RUNTIME DEMO -- naive exponential recursion vs tabulated DP, measured live")
    print("-" * 72)
    import sys
    sys.setrecursionlimit(10000)
    for n in (26, 30, 34):
        t0 = time.perf_counter()
        naive_result = num_squares_naive(n)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        dp_result = sol.numSquares(n)
        dp_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == dp_result
        print(f"n={n:3d}  naive={naive_ms:9.3f} ms   tabulated_dp={dp_ms:7.4f} ms   "
              f"ratio={naive_ms / max(dp_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
