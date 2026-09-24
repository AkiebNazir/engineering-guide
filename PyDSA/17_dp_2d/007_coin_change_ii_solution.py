"""
================================================================================
SOLUTION · LeetCode 518 · Coin Change II                              [Medium]
https://leetcode.com/problems/coin-change-ii/
================================================================================

THE CORE IDEA
--------------
Unbounded knapsack, counting COMBINATIONS (order doesn't matter -- [1,2,2]
and [2,1,2] are ONE combination, not two). dp[i][a] = number of ways to make
amount `a` using only the first i coin TYPES, each reusable unlimited times:

    dp[i][a] = dp[i-1][a]                # skip coin type i entirely
             + dp[i][a - coins[i-1]]     # use coin type i at least once
                                         #   (dp[i], not dp[i-1]: unbounded)

The coin-type axis is what prevents double-counting permutations as distinct
combinations -- "only coin types 1..i" fixes an ORDER IN WHICH COIN TYPES ARE
CONSIDERED (not spent), so [1,2] and [2,1] collapse into the same dp cell.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): recursively try, at each coin
type, every count 0, 1, 2, ... up to amount, sum branches that hit exactly
`amount`. O(exponential in amount / min(coins)) -- massively overlapping
subproblems (the same (coin_index, remaining_amount) pair reached many ways).

Approach 1 (memoized top-down, 2D cache) -- recurse on (coin_index,
remaining), cache each pair. O(len(coins) * amount) time and space.

Approach 2 (bottom-up tabulation, full 2D table) [checked] -- fill dp row by
row (each row = one more coin type made available), each cell built from a
skip term (row above) and a reuse term (same row, smaller amount).
O(len(coins) * amount) time and space.

Approach 3 (space-optimized, rolling 1D row) [checked, shipped] -- dp[i][a]
only ever reads the row above (dp[i-1][a], the "skip" term) and the SAME
row's own smaller amount (dp[i][a-coin], the "reuse" term, already updated
this pass). One array dp[0..amount]; for each coin, sweep amounts LOW to
HIGH so the in-place update naturally reads THIS coin's own contribution
(reuse), not last coin's. O(len(coins)*amount) time, O(amount) space.


================================================================================
STEP BY STEP TRACE
================================================================================
amount = 5, coins = [1, 2, 5]

Full 2D table (rows = coin types made available so far, cols = amount 0..5):

              a=0 a=1 a=2 a=3 a=4 a=5
    (none) :   1   0   0   0   0   0
    +coin1 :   1   1   1   1   1   1    <- only ever 1 way with just 1's
    +coin2 :   1   1   2   2   3   3    <- dp[2][2]=dp[1][2]+dp[2][0]=1+1=2
                                           dp[2][4]=dp[1][4]+dp[2][2]=1+2=3
    +coin5 :   1   1   2   2   3   4    <- dp[3][5]=dp[2][5]+dp[3][0]=3+1=4

Answer: dp[3][5] = 4.  MATCHES expected (5, 2+2+1, 2+1+1+1, 1+1+1+1+1).

Rolling-row version, same data, one array updated per coin (low to high):
    start:          dp = [1,0,0,0,0,0]
    after coin=1:   dp = [1,1,1,1,1,1]   (dp[a]+=dp[a-1] for a=1..5)
    after coin=2:   dp = [1,1,2,2,3,3]   (dp[a]+=dp[a-2] for a=2..5)
    after coin=5:   dp = [1,1,2,2,3,4]   (dp[a]+=dp[a-5] for a=5)
    return dp[5] = 4.  MATCHES.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time                 Space   Mutates input?
    ---------------------------------  -------------------  ------  --------------
    Brute force recursion (no memo)    exponential          O(n)    no
    Memoized top-down, 2D cache        O(coins*amount)      O(coins*amount)  no
    Bottom-up tabulation, full table   O(coins*amount)      O(coins*amount)  no
    Rolling row [chosen]               O(coins*amount)      O(amount)        no


================================================================================
EDGE CASES
================================================================================
    amount == 0             -> exactly 1 way (use no coins) -- base case
                                dp[0] = 1 handles this with no special-casing.
    No coin combination works -> dp[amount] stays 0 (e.g. amount=3, coins=[2]
                                -- 2 alone can never sum to an odd target).
    Single coin type         -> dp[amount] is 1 if coin divides amount evenly,
                                0 otherwise.
    Empty coins list          -> not in constraints (coins.length >= 1), but
                                defensively dp[amount>0] would correctly stay
                                0, dp[0] stays 1.


================================================================================
COMMON MISTAKES
================================================================================
1. Looping COINS as the inner loop and AMOUNTS as the outer loop (or,
   equivalently in the 1D version, updating with the wrong nesting) --
   this counts PERMUTATIONS (order matters: 1+2 and 2+1 counted separately)
   instead of combinations, giving a larger, wrong answer. The outer loop
   MUST be coins, inner loop amounts, for the 1D rolling version.

2. Confusing this with 0/1 knapsack (008, Target Sum) and iterating amounts
   HIGH to LOW -- that direction prevents a coin from being reused, which is
   wrong here: coins ARE reusable (unbounded), so amounts must go LOW to
   HIGH so a coin's own contribution can compound within its own pass.

3. Off-by-one on dp array size -- must be `amount + 1` slots (indices
   0..amount inclusive), not `amount`.

4. Returning dp[len(coins)][amount] correctly in the 2D version but, when
   space-optimizing, forgetting the FINAL row IS the array after all coins
   have been processed -- there's no separate "select last row" step needed
   if the rolling array is updated in place, but the update order (coin
   outer) must be correct or the "final" values reflect a corrupted mix.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How is this different from Coin Change I (LC 322, minimum coins)?
A: LC 322 asks for the MINIMUM NUMBER of coins (dp[a] = min coins to make a,
   combinator is min+1), this one asks for the NUMBER OF WAYS (combinator is
   sum). Same unbounded-knapsack shape, different objective/combinator.

Q: What if order DID matter (permutations, not combinations)?
A: Swap the loop nesting -- amount as the OUTER loop, coins as the INNER
   loop. Then for each amount, every coin is tried in every position,
   counting [1,2] and [2,1] as distinct. This is Combination Sum IV (topic
   16, misleadingly named -- it's actually counting permutations).

Q: Can amount or coin values be negative?
A: Not per these constraints (0 <= amount, 1 <= coins[i]) -- negative coins
   would allow infinite loops of +c then -c, breaking the DP's monotone
   "amount only decreases" assumption entirely.

Q: How would you reconstruct one actual combination, not just the count?
A: Keep the full 2D table and walk backwards: at (i, a), if dp[i][a] ==
   dp[i-1][a] a valid path exists WITHOUT coin i; if dp[i][a - coins[i-1]]
   contributed, coin i can be used (repeat this check at the same row i to
   allow reuse).


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 322  Coin Change I (minimum coins, not count of ways -- min+1 combinator)
    LC 494  Target Sum (008 -- 0/1 knapsack counting, amounts iterated HIGH
            to LOW instead of this problem's LOW to HIGH)
    LC 377  Combination Sum IV (same numbers, but counts PERMUTATIONS --
            amount as outer loop instead of coins)
    LC 416  Partition Equal Subset Sum (topic 16 -- 0/1 knapsack existence,
            not counting)
================================================================================
"""


class Solution:
    def change(self, amount: int, coins: list[int]) -> int:
        """✅ Unbounded knapsack, rolling 1D row over amounts, coins as the
        outer loop (combinations, not permutations). O(len(coins)*amount)
        time, O(amount) space."""
        dp = [0] * (amount + 1)
        dp[0] = 1
        for coin in coins:
            for a in range(coin, amount + 1):
                dp[a] += dp[a - coin]
        return dp[amount]

    def change_full_table(self, amount: int, coins: list[int]) -> int:
        """Alternative: full 2D tabulation, O(len(coins)*amount) time and
        space -- useful for tracing the skip/reuse decomposition explicitly."""
        n = len(coins)
        dp = [[0] * (amount + 1) for _ in range(n + 1)]
        for i in range(n + 1):
            dp[i][0] = 1
        for i in range(1, n + 1):
            coin = coins[i - 1]
            for a in range(amount + 1):
                dp[i][a] = dp[i - 1][a]
                if a >= coin:
                    dp[i][a] += dp[i][a - coin]
        return dp[n][amount]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (5, [1, 2, 5], 4),
        (3, [2], 0),
        (10, [10], 1),
        (0, [1, 2, 3], 1),
        (4, [1, 2, 3], 4),
        (500, [1, 2, 5], 12701),
    ]

    print("--- correctness: rolling row vs full table agree ---")
    for amount, coins, want in cases:
        got_roll = sol.change(amount, coins)
        got_full = sol.change_full_table(amount, coins)
        ok = got_roll == want and got_full == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  amount={amount} coins={coins} "
              f"roll={got_roll} full={got_full}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: prove combinations (coin-outer loop) diverges from
    # permutations (amount-outer loop) on the same input, live.
    # --------------------------------------------------------------------
    print("\n--- DEMO: combinations (coin-outer) vs permutations (amount-outer) ---")

    def count_permutations(amount, coins):
        dp = [0] * (amount + 1)
        dp[0] = 1
        for a in range(1, amount + 1):
            for coin in coins:
                if a >= coin:
                    dp[a] += dp[a - coin]
        return dp[amount]

    amount, coins = 5, [1, 2, 5]
    combos = sol.change(amount, coins)
    perms = count_permutations(amount, coins)
    print(f"  amount={amount}, coins={coins}")
    print(f"  combinations (coin outer, order doesn't matter): {combos}")
    print(f"  permutations (amount outer, order matters):      {perms}")
    print(f"  permutations > combinations: {perms > combos}  "
          f"(every combination is counted once per distinct ordering)")
    all_ok &= (combos == 4)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
