"""
================================================================================
SOLUTION · LeetCode 309 · Best Time to Buy and Sell Stock with Cooldown
                                                                        [Medium]
https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/
================================================================================

THE CORE IDEA
--------------
STATE-MACHINE DP: the "2D" state is (day, which of 3 states you're in), not
(day, day) like the two-string family (005/009/010). Every day you're in
exactly one of:

    held  -- currently holding a share
    sold  -- just sold TODAY (triggers tomorrow's cooldown)
    rest  -- not holding, and NOT the day right after a sale

Transitions ask "what state COULD have led here":

    held[i] = max(held[i-1], rest[i-1] - prices[i])
              (keep holding, OR buy today -- but buying requires yesterday
               was `rest`, never `sold`, because of the cooldown rule)
    sold[i] = held[i-1] + prices[i]
              (the only way to be `sold` today is having held yesterday)
    rest[i] = max(rest[i-1], sold[i-1])
              (was already resting, or cooldown from yesterday's sale just
               ended)

This graph of three states with restricted edges IS the state machine --
draw it once and every "stock with a twist" LeetCode problem (buy/sell II,
III, IV, with fee, with cooldown) is the same three-ish-state machine with
one edge added, removed, or re-weighted.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): recursively try every
buy/sell/cooldown/hold decision at each day. O(3^n) time (three choices at
most days) -- catastrophic, and the SAME (day, state) pair is re-explored
from many different decision paths.

Approach 1 (memoized top-down, state = (day, holding?, cooldown?)) --
recurse with a cache keyed by (day, state). O(n * states) = O(n) time,
O(n) space (memo + recursion depth n).

Approach 2 (bottom-up tabulation, three full-length arrays) [checked] --
fill held[], sold[], rest[] day by day using the transitions above.
O(n) time, O(n) space.

Approach 3 (space-optimized, three rolling scalars) [checked, shipped] --
each day's three values only ever read YESTERDAY's three values. Keep three
scalars, updated together (read all three old values before overwriting
any of them -- classic simultaneous-update trap). O(n) time, O(1) space.


================================================================================
STEP BY STEP TRACE
================================================================================
prices = [1, 2, 3, 0, 2]

Full tables (held / sold / rest), day by day:

    day:      0    1    2    3    4
    price:    1    2    3    0    2
    held:    -1    0    1    1    1     held[1]=max(held[0]=-1, rest[0]-2=-2)=-1?
    sold:     0   -1    0    3    1     wait -- trace carefully below.
    rest:     0    0    0    0    3

Careful column-by-column trace:
    day 0 (price=1):  held=-1 (bought)      sold=0 (n/a)         rest=0
    day 1 (price=2):  held=max(-1, 0-2)=-1  sold=held0+2=-1+2=1  rest=max(0,0)=0
    day 2 (price=3):  held=max(-1, 0-3)=-1  sold=held1+3=-1+3=2  rest=max(0,1)=1
    day 3 (price=0):  held=max(-1, 1-0)=1   sold=held2+0=-1+0=-1 rest=max(1,2)=2
    day 4 (price=2):  held=max(1, 2-2)=1    sold=held3+2=1+2=3   rest=max(2,-1)=2

Answer: max(sold[4], rest[4]) = max(3, 2) = 3.  MATCHES expected.

Reading the winning path back: buy day0 (price1) -> sell day1 (price2,
profit1) -> cooldown day2 -> buy day3 (price0) -> sell day4 (price2,
profit2) -> total profit 1+2=3.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time     Space   Mutates input?
    ---------------------------------  -------  ------  --------------
    Brute force recursion (no memo)    O(3^n)   O(n)    no
    Memoized top-down                  O(n)     O(n)    no
    Bottom-up tabulation, 3 arrays     O(n)     O(n)    no
    3 rolling scalars [chosen]         O(n)     O(1)    no


================================================================================
EDGE CASES
================================================================================
    Single day              -> can't complete any transaction, answer 0 --
                                sold/rest base cases are both 0, held is
                                irrelevant since it's never realized as profit.
    Strictly decreasing prices -> never profitable to buy, answer 0 --
                                held stays deeply negative, sold/rest track 0.
    Strictly increasing prices -> counterintuitively NOT "buy once, sell at
                                the peak" -- the cooldown only matters
                                between separate transactions, so one long
                                hold beats multiple buy/sell cycles here;
                                the DP finds this without special-casing it.
    All identical prices    -> no profit from any transaction, answer 0.


================================================================================
COMMON MISTAKES
================================================================================
1. Letting `held[i]` transition from `sold[i-1] - prices[i]` (buying right
   after yesterday's sale) -- violates the cooldown rule. The buy transition
   must come from `rest[i-1]`, never `sold[i-1]`.

2. Updating the three rolling scalars in place, in the wrong order -- e.g.
   computing the new `held` using the ALREADY-UPDATED `rest` instead of
   yesterday's `rest`. Must read all three OLD values first (into locals),
   THEN assign all three new values -- a simultaneous update, not sequential.

3. Forgetting the final answer is max(sold[n-1], rest[n-1]), not just
   sold[n-1] -- if the optimal strategy is "do nothing" or "cooldown on the
   last day," `rest` may beat `sold`.

4. Initializing `held[0]` to 0 instead of `-prices[0]` -- day 0's only way
   to be holding is having bought on day 0 itself, which costs prices[0].


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if there were a fixed transaction fee instead of a cooldown?
A: LC 714 -- drop the cooldown restriction (buy CAN follow a sale
   immediately: held[i] = max(held[i-1], rest_or_sold[i-1] - prices[i])) and
   subtract `fee` once per completed sale instead.

Q: What if only k transactions were allowed total?
A: LC 188 -- adds a THIRD dimension, the transaction count, making the state
   (day, transactions_used, holding?) -- genuinely 3D, not 2D, though for
   large k it degenerates back to the unlimited-transactions case (this
   problem).

Q: Could you solve this without explicit state names, just index math?
A: Yes -- many solutions use two rolling variables (`hold`, `cash`) and a
   third `prev_cash` snapshot to emulate the cooldown lookback by one extra
   day; the three-named-states version here is chosen for clarity over
   micro-optimizing away one scalar.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 121  Best Time to Buy/Sell Stock I (single transaction, simplest
            member of the state-machine family, no cooldown/fee needed)
    LC 122  Best Time to Buy/Sell Stock II (unlimited transactions, no
            cooldown -- held[i] can transition from sold[i-1] directly)
    LC 714  Best Time to Buy/Sell Stock with Transaction Fee (fee instead
            of cooldown)
    LC 188  Best Time to Buy/Sell Stock IV (k-transaction limit, adds a
            third state dimension)
================================================================================
"""


class Solution:
    def maxProfit(self, prices: list[int]) -> int:
        """✅ 3 rolling scalars (state machine). O(n) time, O(1) space."""
        if not prices:
            return 0
        held = -prices[0]
        sold = 0
        rest = 0
        for price in prices[1:]:
            prev_held, prev_sold, prev_rest = held, sold, rest
            held = max(prev_held, prev_rest - price)
            sold = prev_held + price
            rest = max(prev_rest, prev_sold)
        return max(sold, rest)

    def maxProfit_full_tables(self, prices: list[int]) -> int:
        """Alternative: full-length held/sold/rest arrays, O(n) time and
        space -- useful for tracing the state machine day by day."""
        n = len(prices)
        if n == 0:
            return 0
        held = [0] * n
        sold = [0] * n
        rest = [0] * n
        held[0] = -prices[0]
        for i in range(1, n):
            held[i] = max(held[i - 1], rest[i - 1] - prices[i])
            sold[i] = held[i - 1] + prices[i]
            rest[i] = max(rest[i - 1], sold[i - 1])
        return max(sold[-1], rest[-1])


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([1, 2, 3, 0, 2], 3),
        ([1], 0),
        ([1, 2], 1),
        ([2, 1], 0),
        ([1, 2, 4], 3),
        ([6, 1, 3, 2, 4, 7], 6),
    ]

    print("--- correctness: rolling scalars vs full tables agree ---")
    for prices, want in cases:
        got_roll = sol.maxProfit(prices)
        got_full = sol.maxProfit_full_tables(prices)
        ok = got_roll == want and got_full == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  prices={prices}  roll={got_roll} "
              f"full={got_full}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: prove mistake #2 (updating scalars sequentially instead
    # of simultaneously) actually produces a wrong answer, live.
    # --------------------------------------------------------------------
    print("\n--- DEMO: simultaneous update (correct) vs sequential (buggy) ---")

    def max_profit_buggy_sequential(prices):
        if not prices:
            return 0
        held = -prices[0]
        sold = 0
        rest = 0
        for price in prices[1:]:
            held = max(held, rest - price)   # BUG: uses rest AFTER it may
            sold = held + price              #      already reflect this day
            rest = max(rest, sold)
        return max(sold, rest)

    tricky = [1, 2, 3, 0, 2]
    correct = sol.maxProfit(tricky)
    buggy = max_profit_buggy_sequential(tricky)
    print(f"  prices: {tricky}")
    print(f"  correct (simultaneous update): {correct}")
    print(f"  buggy   (sequential update):   {buggy}")
    print(f"  buggy diverges from correct: {buggy != correct}")
    all_ok &= (correct == 3)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
