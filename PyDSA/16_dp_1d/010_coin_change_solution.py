"""
================================================================================
SOLUTION · LeetCode 322 · Coin Change                                 [Medium]
https://leetcode.com/problems/coin-change/
================================================================================

THE CORE IDEA
--------------
dp[a] MEANS "the minimum number of coins to make EXACTLY amount a" --
value-indexed, not index-indexed. The last coin used to reach a could be
ANY coin c, as long as a-c is itself reachable:

    dp[0] = 0
    dp[a] = 1 + min(dp[a - c] for c in coins if c <= a)   (min over an
                                                             UNBOUNDED set
                                                             of candidates,
                                                             not a fixed
                                                             window)

Unbounded because coins are reusable -- iterate amounts low to high so
each coin can be used again within the same amount's own computation.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion, price it, don't ship it): try every coin as
the first pick, recurse on the remainder. `ways(a) = 1 + min(ways(a-c) for
c in coins)`. Exponential in the worst case -- amount can be reached via
many different coin sequences that all revisit the same smaller remainders.

Approach 1 (BFS over amounts) -- treat each amount 0..amount as a graph
node, each coin as an edge; BFS from 0 finds the shortest path (= fewest
coins) to `amount`. O(amount * len(coins)) time, same complexity as DP,
but frames it as shortest-path instead -- a valid and sometimes more
intuitive alternative, not the one shipped here.

Approach 2 (memoized top-down) [`coin_change_memo`] -- cache dp[a] the
first time it's computed. O(amount * len(coins)) time, O(amount) space +
recursion depth up to `amount`.

Approach 3 (tabulated bottom-up, unbounded knapsack over the amount axis)
[chosen] -- fill dp[0..amount] left to right; for each amount, scan every
coin. O(amount * len(coins)) time, O(amount) space, no recursion depth risk.


================================================================================
STEP BY STEP TRACE
================================================================================
coins = [1, 2, 5], amount = 11

dp[0] = 0
dp[1] = 1 + min(dp[0]) = 1                       (only coin 1 fits)
dp[2] = 1 + min(dp[1], dp[0]) = 1 + min(1,0) = 1  (coin 2 alone)
dp[3] = 1 + min(dp[2], dp[1]) = 1 + min(1,1) = 2  (coin1 not usable via
                                                    dp[3-5]<0; 1+1 or 2+1)
dp[4] = 1 + min(dp[3], dp[2]) = 1 + min(2,1) = 2  (2+2)
dp[5] = 1 + min(dp[4], dp[3], dp[0]) = 1 + min(2,2,0) = 1  (coin 5 alone)
dp[6] = 1 + min(dp[5], dp[4], dp[1]) = 1 + min(1,2,1) = 2  (5+1)
...
dp[10] = 1 + min(dp[9], dp[8], dp[5]) = 1 + min(?,?,1) = 2  (5+5)
dp[11] = 1 + min(dp[10], dp[9], dp[6]) = 1 + min(2,3,2) = 3  (5+5+1)

 a    : 0  1  2  3  4  5  6  7  8  9  10 11
dp[a] : 0  1  1  2  2  1  2  2  3  3  2  3      <- answer dp[11] = 3


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time                   Space   Mutates input?
    ------------------------------  ---------------------  ------  --------------
    Naive recursion                  exponential            O(amount) depth   no
    BFS over amounts                 O(amount * len(coins)) O(amount)  no
    Memoized top-down                O(amount * len(coins)) O(amount)  no
    Tabulated bottom-up [chosen]     O(amount * len(coins)) O(amount)  no


================================================================================
EDGE CASES
================================================================================
    amount == 0             -> zero coins needed regardless of coins;
                              dp[0]=0 is the base case, answer returned
                              immediately without entering the main loop
                              logic.
    amount unreachable
    (coins=[2], amount=3)    -> every odd amount stays at the sentinel
                              "infinity" forever since 2 never lands on an
                              odd total; must detect this and return -1,
                              not the sentinel value itself.
    a single coin of value 1 -> always reachable, dp[a] = a exactly (a
                              coins of value 1).
    coin value larger than
    amount                   -> that coin is simply never usable (skipped
                              by the `c <= a` guard); must not index
                              dp[a-c] with a negative index.


================================================================================
COMMON MISTAKES
================================================================================
1. Iterating coins in the OUTER loop and amounts in the inner loop --
   works fine for THIS problem (min-coins is order-independent, unlike
   014's exact-count-of-ways where outer/inner choice changes what's being
   counted), but the habit of not knowing WHY the order doesn't matter
   here (versus mattering enormously in 014/015) is worth being explicit
   about in an interview.
2. Using 0 as the "unreachable" sentinel instead of infinity -- 0 looks
   like a valid (and suspiciously great) answer, silently corrupting
   every later dp[a] that depends on an actually-unreachable amount.
3. Forgetting to check `dp[amount] == sentinel` at the end and returning
   the raw sentinel value instead of -1.
4. Off-by-one / negative indexing: using coin c without checking c <= a
   first, causing dp[a-c] to wrap around to a negative Python index
   instead of raising -- a silent correctness bug, not a crash.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "How many DISTINCT WAYS to make the amount (order doesn't matter)?" ->
  LC 518 Coin Change II -- same unbounded-knapsack shape, but the LOOP
  ORDER now matters: coins must be the OUTER loop to avoid counting
  permutations of the same combination multiple times (contrast with 015
  Combination Sum IV, where amount is the outer loop specifically because
  order DOES matter there).
- "What if you needed the actual coins used, not just the count?" -> track
  `last_coin[a]` alongside dp during tabulation, then walk backwards from
  `amount` reconstructing the sequence.
- "Can you bound this differently if `amount` is huge but `len(coins)` is
  tiny?" -> for very large amounts relative to coin count, BFS/DP is still
  the standard answer; number-theoretic shortcuts exist only for special
  coin sets (e.g. all multiples of a common base).


================================================================================
RELATED PROBLEMS
================================================================================
- 016 Perfect Squares (LC 279) -- identical unbounded-knapsack-over-a-value
  shape; "coins" are replaced by perfect squares.
- 015 Combination Sum IV (LC 377) -- same value-indexed DP, but counting
  ORDERED ways (loop order flips: amount outer, "coins" inner).
- 014 Partition Equal Subset Sum (LC 416) -- the BOUNDED (0/1) counterpart;
  contrast the required iteration direction against this unbounded version.
================================================================================
"""

import time
from collections import deque
from typing import List

INF = float("inf")


class Solution:
    def coinChange(self, coins: List[int], amount: int) -> int:
        dp = [0] + [INF] * amount
        for a in range(1, amount + 1):
            for c in coins:
                if c <= a and dp[a - c] + 1 < dp[a]:
                    dp[a] = dp[a - c] + 1
        return dp[amount] if dp[amount] != INF else -1


def coin_change_naive(coins: List[int], amount: int) -> int:
    if amount == 0:
        return 0

    def solve(a: int) -> float:
        if a == 0:
            return 0
        if a < 0:
            return INF
        return 1 + min((solve(a - c) for c in coins), default=INF)

    result = solve(amount)
    return result if result != INF else -1


def coin_change_memo(coins: List[int], amount: int) -> int:
    memo = {0: 0}

    def solve(a: int) -> float:
        if a < 0:
            return INF
        if a in memo:
            return memo[a]
        memo[a] = 1 + min((solve(a - c) for c in coins), default=INF)
        return memo[a]

    result = solve(amount)
    return result if result != INF else -1


def coin_change_bfs(coins: List[int], amount: int) -> int:
    if amount == 0:
        return 0
    visited = {0}
    queue = deque([(0, 0)])
    while queue:
        total, steps = queue.popleft()
        for c in coins:
            nxt = total + c
            if nxt == amount:
                return steps + 1
            if nxt < amount and nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, steps + 1))
    return -1


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([1, 2, 5], 11, 3),
        ([2], 3, -1),
        ([1], 0, 0),
        ([1], 1, 1),
        ([1], 2, 2),
        ([2, 5, 10, 1], 27, 4),
        ([186, 419, 83, 408], 6249, 20),
    ]
    for coins, amount, want in cases:
        got = sol.coinChange(coins[:], amount)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  coins={coins} amount={amount}  -> {got}  (want {want})")
        assert coin_change_memo(coins[:], amount) == want
        assert coin_change_bfs(coins[:], amount) == want

    print()
    print("RUNTIME DEMO -- naive exponential recursion vs tabulated DP, measured live")
    print("-" * 72)
    import sys
    sys.setrecursionlimit(10000)
    coins = [1, 3, 4]
    for amt in (16, 20, 24):
        t0 = time.perf_counter()
        naive_result = coin_change_naive(coins, amt)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        dp_result = sol.coinChange(coins, amt)
        dp_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == dp_result
        print(f"amount={amt:3d}  naive={naive_ms:9.3f} ms   tabulated_dp={dp_ms:7.4f} ms   "
              f"ratio={naive_ms / max(dp_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
