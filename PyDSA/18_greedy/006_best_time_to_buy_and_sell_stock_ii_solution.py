"""
================================================================================
SOLUTION · LeetCode 122 · Best Time to Buy and Sell Stock II            [Medium]
https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii/
================================================================================

THE CORE IDEA
--------------
Since you can buy and sell as many times as you like with no cooldown and no
fee, the maximum total profit equals the sum of EVERY positive day-to-day
price increase: `sum(max(0, prices[i] - prices[i-1]) for i in 1..n-1)`. You
never need to think about actual "buy day / sell day" pairs at all — just
walk the array once and add up every uphill step.

EXCHANGE ARGUMENT (why "capture every single uphill day" is optimal)
-------------------------------------------------------------------
Suppose an optimal trading plan buys on day `a` and sells on day `b` (a
single held interval spanning multiple days), skipping the chance to
sell-then-immediately-rebuy at some day `m` strictly between `a` and `b`.
Split that one trade into two back-to-back trades: buy `a`, sell `m`, buy
`m` (same day, allowed), sell `b`. The total profit of the two-trade version
is `(prices[m]-prices[a]) + (prices[b]-prices[m]) = prices[b] - prices[a]`
— algebraically IDENTICAL to the one-trade version, for ANY `m`. So
splitting at any point inside a held interval never loses money. Now apply
this splitting argument repeatedly at EVERY single day inside every held
interval, all the way down to single-day legs: the result is a plan that
buys at the start of every uphill run and sells at the end of every
consecutive up-day, contributing exactly `prices[i] - prices[i-1]` for each
day where price rose, and contributing (or simply not trading) 0 for every
day where price fell or stayed flat. Since splitting never decreases total
profit and this fully-split plan sums every single positive daily delta,
that sum is an upper bound achieved by an actual valid trading plan — hence
it IS the optimum. This is a complete exchange argument: the "sum of
positive deltas" isn't just a heuristic that happens to work, it's provably
equal to what any optimal multi-trade plan achieves.

================================================================================
APPROACH 0 · Brute force — try all valid buy/sell partitions (priced, not
coded as the answer)
================================================================================
Recursively decide, for each day, "hold / don't hold," branching over every
possible set of disjoint buy-sell intervals. Exponential — O(2^n) — without
memoization; with memoization on `(day, holding)` state it becomes the DP
in Approach 2. Never the final coded answer given constraints (n up to
3*10^4).

================================================================================
APPROACH 1 · Sum of positive deltas ✅ (the answer)
================================================================================
    def maxProfit(prices):
        return sum(
            max(0, prices[i] - prices[i - 1]) for i in range(1, len(prices))
        )

    Time:  O(n) — single pass
    Space: O(1)

================================================================================
APPROACH 2 · DP — dp[i][holding] = max profit through day i
================================================================================
    hold, cash = -prices[0], 0
    for p in prices[1:]:
        cash = max(cash, hold + p)
        hold = max(hold, cash - p)
    return cash

Two rolling states ("currently holding a share" vs "currently holding
cash") updated each day. O(n) time, O(1) space — asymptotically tied with
Approach 1 here, and it's worth knowing because THIS exact DP shape is the
one that generalizes correctly to the harder variants (cooldown,
transaction fee, at-most-k-transactions — see topic guide §3 and the
Follow-ups below) where the simple "sum of positive deltas" greedy
provably stops being correct. For THIS specific unlimited/no-fee variant,
Approach 1's exchange argument makes the extra state unnecessary — a clean
example of a DP that collapses to greedy for one variant of a problem
family but not its neighbors.

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
prices = [7, 1, 5, 3, 6, 4]

  day1->2: 1-7 = -6  -> max(0,-6) = 0    running total = 0
  day2->3: 5-1 = +4  -> max(0, 4) = 4    running total = 4
  day3->4: 3-5 = -2  -> max(0,-2) = 0    running total = 4
  day4->5: 6-3 = +3  -> max(0, 3) = 3    running total = 7
  day5->6: 4-6 = -2  -> max(0,-2) = 0    running total = 7

  return 7   (matches expected: 4 from the 1->5 uphill run, 3 from 3->6)

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                       | Time    | Space | Mutates input? |
|-----------------------------------|--------|-------|------------------|
| 0 · brute force (all partitions) | O(2^n) | O(n)  | No               |
| 1 · sum of positive deltas ✅     | O(n)   | O(1)  | No               |
| 2 · two-state DP (hold/cash)      | O(n)   | O(1)  | No               |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- `prices` of length 1: the sum is over `range(1, 1)`, empty — correctly
  returns 0 (no possible trade).
- Strictly decreasing prices: every delta is negative, `max(0, ...)` zeroes
  every term — correctly returns 0, matching the third example.
- Strictly increasing prices: every delta is positive and summed exactly —
  equivalent to one big buy-low-sell-high trade spanning the whole array
  (`prices[-1] - prices[0]`), matching the second example.
- Flat prices (all equal): every delta is 0 — correctly returns 0.
- Prices containing 0: no special handling needed, the delta-sum logic is
  agnostic to absolute price level.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Looks-greedy-but-wrong: trying to find the single best (buy day, sell
   day) pair** (as in LC 121, the single-transaction version) — that
   caps profit at ONE trade and undercounts here; this problem allows
   unlimited trades, and the correct greedy exploits that by summing every
   uphill segment instead of hunting for one global min-then-max.
2. Forgetting same-day buy-then-sell is allowed (net 0, harmless) and
   writing an off-by-one that skips a day, silently dropping one delta from
   the sum.
3. Assuming this same "sum of positive deltas" trick still works once a
   cooldown or transaction fee is introduced — it does NOT (see follow-ups
   below); reusing this greedy on those variants gives a wrong,
   over-optimistic answer since it ignores the cost/friction of extra
   trades.
4. Using `prices[i] - prices[i-1]` without `max(0, ...)`, i.e. summing ALL
   deltas including negative ones — this telescopes down to just
   `prices[-1] - prices[0]`, throwing away all the intermediate local
   peaks/valleys that the actual optimal multi-trade plan captures.

--------------------------------------------------------------------------------
RUNTIME DEMO — greedy sum-of-deltas vs. brute-force DP-over-partitions,
cross-checked for correctness (both are O(n)-ish here, so the interesting
demo is agreement, not a speed gap — see note below)
--------------------------------------------------------------------------------
Both Approach 1 and Approach 2 are O(n), so there's no meaningful runtime
race between them on this problem (that's the point: the greedy exchange
argument doesn't just win asymptotically, it produces the IDENTICAL
algorith: two-state DP already collapsed to O(1) rolling state). The
demonstration below instead cross-validates both against an exponential
brute-force-over-partitions oracle on small random arrays, and times the
brute force separately to show why it's infeasible at real scale.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if you can make at most ONE transaction?" (LC 121) — track a
  running minimum price seen so far and the max profit from selling today;
  a different (simpler) single-pass greedy, NOT sum-of-deltas.
- "What if you can make at most TWO / at most k transactions?" (LC 123,
  188) — the sum-of-deltas trick breaks (capping transaction count means
  you might have to skip a small uphill run to save "budget" for a bigger
  one later); needs genuine DP with transaction count as part of the state
  — topic 16/17 territory.
- "What if there's a transaction fee per trade, or a cooldown day after
  selling?" (LC 309, 714) — also breaks sum-of-deltas: a fee can make
  splitting a large uphill run into many small trades NET WORSE (each split
  costs the fee again), which directly violates this problem's "splitting
  never loses money" step of the exchange argument — needs the two-state
  DP (Approach 2) extended with a fee subtracted on sell, or a third
  "cooldown" state.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- LC 121 Best Time to Buy and Sell Stock (single transaction) — simpler
  single-pass greedy, different rule.
- LC 123 / 188 Best Time to Buy and Sell Stock III / IV (k transactions) —
  DP, topic 16/17.
- LC 309 / 714 (cooldown / transaction fee) — DP, topic 16/17; see
  topic guide §3 for the full greedy-vs-DP contrast table.
================================================================================
"""

import random
import time
from functools import lru_cache


class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        return sum(max(0, prices[i] - prices[i - 1]) for i in range(1, len(prices)))


def max_profit_two_state_dp(prices: list[int]) -> int:
    if not prices:
        return 0
    hold, cash = -prices[0], 0
    for p in prices[1:]:
        cash = max(cash, hold + p)
        hold = max(hold, cash - p)
    return cash


def max_profit_brute_force(prices: list[int]) -> int:
    """Exponential oracle: at each day, either hold (do nothing), or if not
    currently holding buy, or if currently holding sell. Memoized on
    (day, holding) -- used only to validate the greedy on tiny inputs."""

    @lru_cache(maxsize=None)
    def rec(day: int, holding: bool) -> int:
        if day == len(prices):
            return 0
        best = rec(day + 1, holding)  # do nothing today
        if holding:
            best = max(best, prices[day] + rec(day + 1, False))  # sell
        else:
            best = max(best, -prices[day] + rec(day + 1, True))  # buy
        return best

    result = rec(0, False)
    rec.cache_clear()
    return result


def run_tests():
    sol = Solution()
    assert sol.maxProfit([7, 1, 5, 3, 6, 4]) == 7
    assert sol.maxProfit([1, 2, 3, 4, 5]) == 4
    assert sol.maxProfit([7, 6, 4, 3, 1]) == 0
    assert sol.maxProfit([1]) == 0
    assert sol.maxProfit([]) == 0
    assert sol.maxProfit([5, 5, 5]) == 0

    # cross-check against DP and exponential brute force on random arrays
    random.seed(17)
    for _ in range(150):
        n = random.randint(0, 8)
        arr = [random.randint(0, 10) for _ in range(n)]
        expected = max_profit_brute_force(arr)
        assert sol.maxProfit(arr) == expected, f"greedy mismatch on {arr}"
        assert max_profit_two_state_dp(arr) == expected, f"DP mismatch on {arr}"

    original = [7, 1, 5, 3, 6, 4]
    sol.maxProfit(original)
    assert original == [7, 1, 5, 3, 6, 4]

    # --- Demo: brute-force-over-partitions is infeasible past tiny n -------
    random.seed(23)
    small_n = 18
    arr = [random.randint(0, 50) for _ in range(small_n)]

    t0 = time.perf_counter()
    greedy_result = sol.maxProfit(arr)
    greedy_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    brute_result = max_profit_brute_force(arr)
    brute_time = time.perf_counter() - t0

    assert greedy_result == brute_result
    print(f"n={small_n}: greedy sum-of-deltas O(n) took {greedy_time*1000:.4f} ms")
    print(f"n={small_n}: exponential brute force took {brute_time*1000:.2f} ms")
    print(f"greedy is {brute_time / greedy_time:.1f}x faster on this run")
    assert greedy_time < brute_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
