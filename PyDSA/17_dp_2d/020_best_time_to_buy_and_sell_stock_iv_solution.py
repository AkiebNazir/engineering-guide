"""
================================================================================
SOLUTION · LeetCode 188 · Best Time to Buy and Sell Stock IV              [Hard]
https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iv/
================================================================================

THE CORE IDEA
--------------
A state machine with 2k states, advanced one price at a time:

    hold[j] = best profit while HOLDING, in the j-th transaction
    free[j] = best profit while NOT holding, after completing j transactions

    for p in prices:
        for j in 1..k:
            hold[j] = max(hold[j], free[j-1] - p)     # keep holding, or buy today
            free[j] = max(free[j], hold[j] + p)       # stay out, or sell today

    answer = free[k]

And one shortcut: n days contain at most n // 2 profitable transactions, so if
k >= n // 2 the limit never binds — take every upward step.


================================================================================
APPROACH 1 · Recursion over (day, transactions left, holding?) (priced, oracle)
================================================================================
At each day choose: do nothing, or buy (if not holding), or sell (if holding).
Without memoisation this branches twice per day.

    Time: O(2^n)    With memo on (i, j, holding): O(n * k) states


================================================================================
APPROACH 2 · Table over (transactions, day) with an inner scan
================================================================================
    dp[j][i] = best profit using at most j transactions within prices[0..i]
    dp[j][i] = max(dp[j][i-1],                                  # no sale on day i
                   max over m < i of prices[i] - prices[m] + dp[j-1][m])

The inner max makes it O(k * n^2). Carrying best = max(dp[j-1][m] - prices[m])
as i advances removes the inner loop: O(k * n).


================================================================================
APPROACH 3 · State machine in O(k) space ✅ (the answer)
================================================================================
    if k >= n // 2:
        return sum(max(0, b - a) for a, b in zip(prices, prices[1:]))
    hold = [-inf] * (k + 1)
    free = [0] * (k + 1)
    for p in prices:
        for j in range(1, k + 1):
            hold[j] = max(hold[j], free[j - 1] - p)
            free[j] = max(free[j], hold[j] + p)
    return free[k]

Updating hold[j] and then free[j] with the same price lets a share be bought
and sold on the same day; that is a zero-profit transaction, so it never
changes the maximum.

    Time: O(n * k)    Space: O(k)


================================================================================
STEP BY STEP TRACE · k = 2, prices = [3, 2, 6, 5, 0, 3]
================================================================================
    day  p   hold[1]  free[1]  hold[2]  free[2]
    ---  --  -------  -------  -------  -------
    0    3     -3       0        -3       0
    1    2     -2       0        -2       0
    2    6     -2       4        -2       4
    3    5     -2       4        -1       4       hold[2] = free[1] - 5 = -1
    4    0      0       4         4       4       hold[2] = free[1] - 0 = 4
    5    3      0       4         4       7       free[2] = hold[2] + 3 = 7

    answer free[2] = 7   (buy 2 sell 6, buy 0 sell 3)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time        Space    Mutates input?
    ------------------------------  ----------  -------  --------------
    Plain recursion                 O(2^n)      O(n)     No
    Memo (day, j, holding)          O(n * k)    O(n * k) No
    Table with inner scan           O(k * n^2)  O(k * n) No
    State machine ✅                O(n * k)    O(k)     No
    ... with the k >= n/2 shortcut  O(n)        O(1)     No


================================================================================
EDGE CASES
================================================================================
    One price             No sale possible: 0.
    Prices only fall      Best is to never buy: 0.
    k larger than n // 2  Unlimited in effect: sum of the rises.
    Flat prices           0 — a same-day buy/sell earns nothing.


================================================================================
COMMON MISTAKES
================================================================================
1. Initialising hold[j] = 0 instead of -infinity. That means "already holding
   a free share", so k=1, [5] reports 5 instead of 0. Demo.

2. Summing every rise when k is small (treating "at most k" as unlimited).
   k=1, [1, 3, 2, 8] -> 8, but one transaction can only make 7. Demo.

3. Greedily taking the k largest upward runs. Merging runs can beat that:
   k=3, [1,3,2,8,4,9,2,5] -> 14 greedily, but 15 is possible (1->8, 4->9,
   2->5). Demo.

4. No k >= n // 2 shortcut: correct, but it allocates k states and does n*k
   work for a k that can't bind. Demo times k = 5,000 on 1,000 prices.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Add a transaction fee (LC 714) or a cooldown (LC 309)?
A: Same machine. Fee: subtract it when selling. Cooldown: buying reads the
   "free" value from two days ago (17_dp_2d/006).

Q: Return the actual trades?
A: Record, per state, the day of the last buy/sell that improved it, or keep
   the full O(n * k) table and walk it backwards.

Q: k up to 10^9 and n up to 10^5?
A: The shortcut covers large k. For large k < n/2 there is an O(n log n)
   approach: merge the price's valley/peak pairs and repeatedly drop the
   cheapest "merge or skip" option with a heap — a known hard variant.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 121  Best Time to Buy and Sell Stock (03_sliding_window/001)  — k = 1
    LC 122  Best Time to Buy and Sell Stock II (18_greedy/006)       — k = inf
    LC 123  Best Time to Buy and Sell Stock III                      — k = 2
    LC 309  ... with Cooldown (006)                                  — extra state
    LC 714  ... with Transaction Fee                                 — same machine
================================================================================
"""

import random
import time
from functools import cache
from typing import List


class Solution:
    def maxProfit(self, k: int, prices: List[int]) -> int:
        n = len(prices)
        if k >= n // 2:                                  # the limit can't bind
            return sum(b - a for a, b in zip(prices, prices[1:]) if b > a)
        hold = [float("-inf")] * (k + 1)
        free = [0] * (k + 1)
        for p in prices:
            for j in range(1, k + 1):
                if free[j - 1] - p > hold[j]:
                    hold[j] = free[j - 1] - p            # buy today (j-th transaction)
                if hold[j] + p > free[j]:
                    free[j] = hold[j] + p                # sell today
        return free[k]


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def profit_memo(k: int, prices: List[int]) -> int:
    """Oracle: memoised recursion over (day, transactions left, holding)."""
    n = len(prices)

    @cache
    def go(i: int, left: int, holding: bool) -> int:
        if i == n:
            return 0
        best = go(i + 1, left, holding)                         # do nothing
        if holding:
            best = max(best, prices[i] + go(i + 1, left, False))  # sell
        elif left > 0:
            best = max(best, -prices[i] + go(i + 1, left - 1, True))  # buy
        return best

    return go(0, k, False)


def profit_table(k: int, prices: List[int]) -> int:
    """Approach 2 with the running max: O(k * n)."""
    n = len(prices)
    if n < 2:
        return 0
    prev = [0] * n
    for _ in range(k):
        cur = [0] * n
        best = -prices[0]                                  # max(prev[m] - prices[m])
        for i in range(1, n):
            cur[i] = max(cur[i - 1], prices[i] + best)
            best = max(best, prev[i] - prices[i])
        prev = cur
    return prev[-1]


def zero_init_bug(k: int, prices: List[int]) -> int:
    """Mistake 1: hold starts at 0, i.e. a free share."""
    hold, free = [0] * (k + 1), [0] * (k + 1)
    for p in prices:
        for j in range(1, k + 1):
            hold[j] = max(hold[j], free[j - 1] - p)
            free[j] = max(free[j], hold[j] + p)
    return free[k]


def all_rises_bug(k: int, prices: List[int]) -> int:
    """Mistake 2: ignores k entirely."""
    return sum(b - a for a, b in zip(prices, prices[1:]) if b > a)


def largest_runs_bug(k: int, prices: List[int]) -> int:
    """Mistake 3: take the k most profitable maximal upward runs."""
    runs, i, n = [], 0, len(prices)
    while i < n - 1:
        while i < n - 1 and prices[i + 1] <= prices[i]:
            i += 1
        lo = prices[i]
        while i < n - 1 and prices[i + 1] > prices[i]:
            i += 1
        if prices[i] > lo:
            runs.append(prices[i] - lo)
    return sum(sorted(runs, reverse=True)[:k])


def no_shortcut(k: int, prices: List[int]) -> int:
    """Mistake 4: correct, but always pays for k states."""
    hold, free = [float("-inf")] * (k + 1), [0] * (k + 1)
    for p in prices:
        for j in range(1, k + 1):
            hold[j] = max(hold[j], free[j - 1] - p)
            free[j] = max(free[j], hold[j] + p)
    return free[k]


# ==============================================================================
# TESTS — run:  python 020_best_time_to_buy_and_sell_stock_iv_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: state machine vs O(kn) table vs memoised recursion ---")
    cases = [(2, [2, 4, 1], 2), (2, [3, 2, 6, 5, 0, 3], 7), (1, [7, 1, 5, 3, 6, 4], 5),
             (2, [3, 3, 5, 0, 0, 3, 1, 4], 6), (100, [1, 2, 3, 4, 5], 4), (2, [7, 6, 4, 3, 1], 0),
             (1, [5], 0), (3, [1, 3, 2, 8, 4, 9, 2, 5], 15)]
    for k, prices, want in cases:
        results = (sol.maxProfit(k, prices), profit_table(k, prices), profit_memo(k, prices))
        ok = all(r == want for r in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  k={k:<3} prices={prices!s:<26} got={results}  want={want}")

    print("\n--- randomized cross-check vs the memoised oracle (2,000 cases) ---")
    rng = random.Random(188)
    bad = 0
    for _ in range(2000):
        prices = [rng.randint(0, 20) for _ in range(rng.randint(1, 14))]
        k = rng.randint(1, 8)
        want = profit_memo(k, prices)
        if sol.maxProfit(k, prices) != want or profit_table(k, prices) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  2,000 random (k, prices) agree with the oracle")

    print("\n--- mistakes LIVE ---")
    w1 = zero_init_bug(1, [5])
    ok = w1 == 5 and sol.maxProfit(1, [5]) == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  hold initialised to 0: k=1, [5] -> {w1}, want 0")
    w2 = all_rises_bug(1, [1, 3, 2, 8])
    ok = w2 == 8 and sol.maxProfit(1, [1, 3, 2, 8]) == 7
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  sum of every rise: k=1, [1,3,2,8] -> {w2}, want 7")
    p3 = [1, 3, 2, 8, 4, 9, 2, 5]
    w3 = largest_runs_bug(3, p3)
    ok = w3 == 14 and sol.maxProfit(3, p3) == 15
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  k largest upward runs: k=3 -> {w3}, want 15 (1->8, 4->9, 2->5)")

    print("\n--- the k >= n // 2 shortcut, timed (n = 1,000, k = 5,000) ---")
    prices = [rng.randint(0, 1000) for _ in range(1000)]
    t0 = time.perf_counter(); a = sol.maxProfit(5_000, prices); t1 = time.perf_counter()
    b = no_shortcut(5_000, prices); t2 = time.perf_counter()
    ok = a == b
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  with shortcut {1000 * (t1 - t0):.2f} ms, "
          f"without {1000 * (t2 - t1):,.0f} ms, same answer {a}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
