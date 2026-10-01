"""
================================================================================
SOLUTION · LeetCode 121 · Best Time to Buy and Sell Stock                 [Easy]
https://leetcode.com/problems/best-time-to-buy-and-sell-stock/
================================================================================

THE CORE IDEA
-------------
Sweep once, treating every day as the SELL day, and carry the cheapest price
seen so far:

    min_price = prices[0]
    best = 0
    for p in prices[1:]:
        best = max(best, p - min_price)     # sell today
        min_price = min(min_price, p)       # or buy today, for tomorrow

    O(n) time, O(1) space.

The whole insight is one sentence:

    THE ONLY FACT ABOUT THE PAST THAT CAN EVER MATTER IS THE MINIMUM PRICE.

Not the second-cheapest, not where it was, not how many cheap days there were.
A single scalar summarises an unbounded history, which is exactly why the inner
loop disappears.


WHY THAT SCALAR IS SUFFICIENT — the elimination argument
--------------------------------------------------------
Suppose day `j` is cheaper than day `i`, and `i < j`. Then for ANY future sell
day `s > j`:

    prices[s] - prices[j]  >  prices[s] - prices[i]

so buying on `j` beats buying on `i` for every possible sale. Day `i` is
permanently, unconditionally eliminated. It does not need to be remembered,
compared against, or stored.

That is the same argument that makes converging two-pointers O(n) in topic 02:
each step must let you throw something away FOREVER, not just for now. Here one
comparison retires an entire column of the O(n^2) pair matrix.


================================================================================
IS THIS REALLY A SLIDING WINDOW?
================================================================================
Three descriptions, one algorithm. Being able to give all three, and say they
are the same, is worth more than defending any one of them.

1. RUNNING MINIMUM (what the code literally does)
       Carry min-so-far; answer = max over r of prices[r] - min_before_r.

2. SLIDING WINDOW (why it lives in this folder)
       Window [l, r], l = buy day, r = sell day, aggregate = prices[r]-prices[l].

           r += 1                       every iteration          (expand)
           if prices[r] < prices[l]:    l = r                     (contract)

       This is the DEGENERATE window: `l` does not creep forward one step at a
       time restoring a predicate, it SNAPS to `r`. But it obeys the property
       that defines the topic — l is monotone non-decreasing, so l and r each
       move at most n times and the pass is O(n) by amortization.

3. ONE-STATE DP (Kadane in disguise)
       Let f(r) = best profit for a sale on day r. Then

           f(r) = max(0, f(r-1) + prices[r] - prices[r-1])

       which is literally Kadane's algorithm on the DIFFERENCE array
       `d[i] = prices[i] - prices[i-1]`: the maximum subarray sum of the daily
       deltas IS the maximum profit, because a subarray of deltas telescopes:

           d[i+1] + d[i+2] + ... + d[j]  =  prices[j] - prices[i]

       Say that out loud if the interviewer asks for a different angle. It also
       explains why LC 53 (Maximum Subarray) and this problem feel identical:
       they ARE, up to one transformation.

`maxProfit_kadane` and `maxProfit_window` below implement 2 and 3 explicitly.


================================================================================
THE ORDER-OF-OPERATIONS BUG — the one thing to actually learn here
================================================================================
These two loop bodies are NOT the same:

    # CORRECT                             # SUSPICIOUS
    best = max(best, p - min_price)       min_price = min(min_price, p)
    min_price = min(min_price, p)         best = max(best, p - min_price)

The right-hand version updates the minimum first, so on the iteration where `p`
IS the new minimum it computes `p - p = 0` — it lets you buy and sell on the
SAME DAY, which the problem forbids ("a different day in the future").

Now the twist, and it is worth sitting with: **on this problem the bug is
invisible.** Buying and selling on the same day yields a profit of exactly 0,
and `best` is initialised to 0 and never goes below it, so the phantom
transaction can never become the answer. Both versions return the same number
on every input. `maxProfit_same_day` below is that version, and the test suite
cross-checks it on 3000 random arrays to demonstrate it never disagrees.

Two lessons, and the second one is the real one:

  * DO NOT rely on that. It survives only because a same-day trade is worth 0
    and 0 is the floor. Change the problem — "you must sell", allow a
    transaction fee, ask for the buy/sell INDICES rather than the profit — and
    the same-day version starts returning wrong answers. `maxProfit_indices`
    is the variant where it visibly breaks.
  * An interviewer who sees the second ordering will ask "can you buy and sell
    on the same day here?". The right answer is not "it doesn't matter", it is
    "it would be allowed by this ordering, and it happens to be harmless
    because that trade profits 0 — but I'll compute the profit before updating
    the minimum so the code says what I mean."


================================================================================
INITIALISATION
================================================================================
    min_price = prices[0]      and iterate from index 1.
    min_price = float('inf')   and iterate from index 0.

Both are correct. The second is more robust — it needs no `prices[0]`, so an
empty list does not raise, and it handles the n == 1 case without a special
branch. The constraint guarantees `n >= 1`, so either is defensible; prefer
`inf` and say why: *"it makes the empty case fall out instead of raising."*

    best = 0     NOT float('-inf').
    The problem defines "no profitable transaction" as 0, so the floor IS the
    answer for a monotonically falling array. Starting at -inf and returning it
    would emit a negative profit, which the problem forbids.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time        Space   Notes
    ---------------------------  ----------  ------  --------------------------
    Every (buy, sell) pair       O(n^2)      O(1)    5e9 ops at n=1e5. TLE.
    Suffix-max array             O(n)        O(n)    max profit = max(suf[r]-p)
    Kadane on the delta array    O(n)        O(1)    same numbers, different story
    Running minimum ✅           O(n)        O(1)    one pass, two scalars

    All the O(n) variants do ONE pass and hold O(1) state. There is no faster
    answer: you must read every price at least once, so O(n) is a lower bound.


================================================================================
EDGE CASES
================================================================================
    [1]              -> 0    Single day. You cannot buy and sell on distinct
                             days, so no transaction exists. The loop body
                             never runs; the initialisation IS the answer.

    [7,6,4,3,1]      -> 0    Strictly decreasing. Every candidate profit is
                             negative; `best` must stay at its 0 floor. This is
                             the test that catches `best = float('-inf')`.

    [2,2,2]          -> 0    Flat. Profit 0 everywhere; must not return a
                             negative, must not crash.

    [2,4,1]          -> 2    THE GLOBAL MINIMUM IS THE LAST DAY and is useless.
                             Catches anyone who computes
                             `max(prices) - min(prices)` and ignores ordering.

    [3,2,6,5,0,3]    -> 4    The best pair (2 -> 6) involves NEITHER the global
                             minimum (0) NOR the global maximum... which is 6,
                             so it uses the max but not the min. Pairs like
                             this are why the order constraint is the problem.

    [5,4,3,2,1,100]  -> 99   Long descent then a spike: `min_price` must still
                             be tracking correctly after many updates.

    [0, 0]           -> 0    Zero prices are legal (constraint allows 0).
                             Guard against anyone dividing or using 0 as a
                             sentinel for "unset".


================================================================================
COMMON MISTAKES
================================================================================
1. `max(prices) - min(prices)` — ignores that the buy must come FIRST.
   [2,4,1] returns 3 instead of 2. The most common wrong answer.

2. Initialising `best = float('-inf')` and returning it on a falling array.
   The problem says 0, not "the least-bad loss".

3. Updating `min_price` before computing the profit. Harmless HERE (see above),
   but wrong in spirit and wrong in every variant of the problem.

4. Tracking the buy INDEX and recomputing `prices[buy]` each step. Not wrong,
   just noise — you only ever need the value.

5. Sorting. Destroys the chronology, which IS the constraint. (Same trap as
   LC 1 vs LC 167 in topic 02: sorting is only free when order is irrelevant.)

6. Building a suffix-maximum array when a scalar suffices. O(n) space for
   nothing. It is a fine intermediate step to mention, but say you can drop it.

7. Reading `prices[0]` without checking the list is non-empty, in code intended
   to be robust outside LeetCode's guarantees.

8. Answering "O(n log n)" out of habit. There is no sort and no divide and
   conquer here. It is O(n), and the lower bound is O(n) too.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the BUY and SELL DAYS, not just the profit.
A: Track three things: `min_idx`, and on an improvement record
   `(best_buy, best_sell) = (min_idx, r)`. This is where the same-day ordering
   bug becomes visible — it can report `(r, r)`, a transaction that does not
   exist. `maxProfit_indices` below.

Q: As many transactions as you like (LC 122).
A: Collapse to greed: sum every positive daily delta,
   `sum(max(0, p[i] - p[i-1]))`. Every upward run can be decomposed into
   consecutive one-day trades with the same total, so you never need to find
   the runs. One line, O(n).

Q: At most TWO transactions (LC 123)? At most k (LC 188)?
A: DP over (day, transactions used, holding or not). For k=2, four rolling
   scalars: `buy1, sell1, buy2, sell2`, each updated from the previous. For
   general k it is O(nk) — and when k >= n/2 the constraint is not binding, so
   it degenerates to the unlimited greedy above.

Q: With a cooldown (LC 309) or a transaction fee (LC 714)?
A: Same state machine, one more state (cooldown) or a constant subtracted on
   sale. This problem is the k = 1 base case of that whole family, which is
   why it is worth knowing as a DP as well as a scan.

Q: The prices arrive as a STREAM and you must answer at any moment.
A: The algorithm is already online — it holds O(1) state and each new price is
   O(1) to absorb. Say that; "it's already streaming" is a strong answer.

Q: Why can't this be faster than O(n)?
A: Any correct algorithm must inspect every price: flip a single unseen price
   to 10^9 and the answer changes. So O(n) reads is a lower bound, and we match
   it with O(1) space.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 53   Maximum Subarray          — Kadane; this problem IS Kadane on deltas
    LC 122  Best Time II              — unlimited transactions, greedy sum of gains
    LC 123  Best Time III             — at most 2 transactions, 4-scalar DP
    LC 188  Best Time IV              — at most k, O(nk) DP
    LC 309  With Cooldown             — one more state
    LC 714  With Transaction Fee      — subtract the fee on sale
    LC 2016 Max Difference Between    — same scan, i < j, strictly increasing
            Increasing Elements         (returns -1 instead of 0 when none)
================================================================================
"""

import random
import time
from typing import List, Optional, Tuple


class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        """Running minimum. O(n) time, O(1) space.

        Profit is computed BEFORE the minimum is updated, so a buy and a sale
        can never land on the same day.
        """
        min_price = float('inf')
        best = 0
        for p in prices:
            best = max(best, p - min_price)   # sell today, buy at the old min
            min_price = min(min_price, p)     # only now may today become the min
        return best

    # ------------------------------------------------------------------
    # The same algorithm told three ways.
    # ------------------------------------------------------------------
    def maxProfit_window(self, prices: List[int]) -> int:
        """Explicit two-pointer window: l = buy day, r = sell day.

        Identical work, but it makes the topic membership visible: `l` is
        monotone non-decreasing, so l and r each move <= n times -> O(n).
        """
        if not prices:
            return 0
        l, best = 0, 0
        for r in range(1, len(prices)):
            if prices[r] < prices[l]:
                l = r                                  # contract: l SNAPS to r
            else:
                best = max(best, prices[r] - prices[l])  # expand and record
        return best

    def maxProfit_kadane(self, prices: List[int]) -> int:
        """Kadane's maximum-subarray on the daily-delta array. O(n)/O(1).

        d[i] = prices[i] - prices[i-1]; a subarray of d telescopes to
        prices[j] - prices[i], so max subarray sum == max profit.
        """
        best = cur = 0
        for i in range(1, len(prices)):
            cur = max(0, cur + prices[i] - prices[i - 1])
            best = max(best, cur)
        return best

    def maxProfit_suffix(self, prices: List[int]) -> int:
        """Suffix-max array. O(n) time but O(n) space — the version to mention
        and then improve away."""
        n = len(prices)
        if n < 2:
            return 0
        suf = [0] * n
        suf[-1] = prices[-1]
        for i in range(n - 2, -1, -1):
            suf[i] = max(prices[i], suf[i + 1])
        best = 0                                    # floor at 0, never negative
        for i in range(n - 1):
            best = max(best, suf[i + 1] - prices[i])
        return best

    def maxProfit_brute(self, prices: List[int]) -> int:
        """O(n^2) oracle: every ordered pair."""
        best = 0
        for i in range(len(prices)):
            for j in range(i + 1, len(prices)):
                best = max(best, prices[j] - prices[i])
        return best

    # ------------------------------------------------------------------
    # The ordering variant, and where it actually breaks.
    # ------------------------------------------------------------------
    def maxProfit_same_day(self, prices: List[int]) -> int:
        """Updates the minimum BEFORE computing profit — permits a same-day
        trade. Returns the right answer anyway, because that trade is worth 0
        and 0 is the floor. Correct by accident; see the demo below."""
        min_price = float('inf')
        best = 0
        for p in prices:
            min_price = min(min_price, p)     # today can be the buy day...
            best = max(best, p - min_price)   # ...and the sell day. Profit 0.
        return best

    def maxProfit_indices(
        self, prices: List[int], same_day_bug: bool = False
    ) -> Tuple[int, Optional[int], Optional[int]]:
        """Returns (profit, buy_day, sell_day) — the follow-up where the
        ordering genuinely matters. With same_day_bug=True it can report
        buy == sell, a transaction that does not exist."""
        best, buy, sell = 0, None, None
        min_price, min_idx = float('inf'), None
        for r, p in enumerate(prices):
            if same_day_bug and p < min_price:
                min_price, min_idx = p, r
            if min_idx is not None and p - min_price >= best:
                best, buy, sell = p - min_price, min_idx, r
            if not same_day_bug and p < min_price:
                min_price, min_idx = p, r
        return best, buy, sell


# ==============================================================================
# TESTS — run:  python 001_best_time_to_buy_and_sell_stock_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        [7, 1, 5, 3, 6, 4],
        [7, 6, 4, 3, 1],
        [1],
        [2, 2, 2],
        [1, 2],
        [2, 1],
        [3, 2, 6, 5, 0, 3],
        [2, 4, 1],
        [1, 4, 2],
        [0, 0],
        [5, 4, 3, 2, 1, 100],
        [100, 1, 2, 3],
        [],
    ]
    impls = [
        ("running minimum ", sol.maxProfit),
        ("explicit window ", sol.maxProfit_window),
        ("kadane on deltas", sol.maxProfit_kadane),
        ("suffix-max array", sol.maxProfit_suffix),
        ("same-day variant", sol.maxProfit_same_day),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(c)) == sol.maxProfit_brute(c) for c in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(121)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        arr = [random.randint(0, 20) for _ in range(random.randint(1, 14))]
        want = sol.maxProfit_brute(arr)
        for _, fn in impls:
            if fn(list(arr)) != want:
                mismatches += 1
    print(f"  {trials} random arrays x {len(impls)} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The window, traced.
    # ----------------------------------------------------------------------
    print("\n--- the degenerate window on [7,1,5,3,6,4] ---")
    prices = [7, 1, 5, 3, 6, 4]
    print(f"  {'r':>2} {'price':>6} {'l (buy)':>8} {'p[r]-p[l]':>10} {'best':>5}"
          f"   action")
    l, best = 0, 0
    print(f"  {0:>2} {prices[0]:>6} {0:>8} {'-':>10} {0:>5}   initialise")
    for r in range(1, len(prices)):
        if prices[r] < prices[l]:
            l = r
            act = f"CONTRACT: cheaper buy, l snaps to {r}"
            gain = "-"
        else:
            gain = prices[r] - prices[l]
            best = max(best, gain)
            act = "expand: sell today"
            gain = f"{gain}"
        print(f"  {r:>2} {prices[r]:>6} {l:>8} {gain:>10} {best:>5}   {act}")
    print("  `l` only ever moves RIGHT — that is the amortization argument, and")
    print("  the only reason this is one pass instead of n^2 pairs.")

    # ----------------------------------------------------------------------
    # Why a scalar is enough: the elimination argument, made concrete.
    # ----------------------------------------------------------------------
    print("\n--- why only the MINIMUM of the past matters ---")
    prices = [7, 3, 9, 1, 8]
    print(f"  prices = {prices}")
    print(f"  {'sell day r':>10} {'candidates before r':>26} {'best buy':>9}")
    for r in range(1, len(prices)):
        before = prices[:r]
        print(f"  {r:>10} {str(before):>26} {min(before):>9}")
    print("  Day 0 (price 7) is dead the moment day 1 (price 3) appears: 3 beats")
    print("  7 against EVERY future sale, not just some. One comparison retires")
    print("  a whole column of the n^2 pair matrix permanently.")

    # ----------------------------------------------------------------------
    # The classic wrong answer.
    # ----------------------------------------------------------------------
    print("\n--- why max(prices) - min(prices) is wrong ---")
    print(f"  {'input':<20} {'correct':>8} {'max-min':>8}  ok?")
    for arr in ([7, 1, 5, 3, 6, 4], [2, 4, 1], [5, 1], [1, 5], [3, 2, 6, 5, 0, 3]):
        good = sol.maxProfit(arr)
        naive = max(arr) - min(arr)
        print(f"  {str(arr):<20} {good:>8} {naive:>8}  "
              f"{'yes' if good == naive else 'NO  <- min comes after max'}")

    # ----------------------------------------------------------------------
    # The same-day ordering: harmless here, visible in the index variant.
    # ----------------------------------------------------------------------
    print("\n--- the same-day ordering bug, made visible ---")
    print("  As a PROFIT it never disagrees (a same-day trade earns 0, and 0 is")
    print("  the floor). Asking for the DAYS exposes it:")
    print(f"  {'input':<22} {'correct (buy,sell)':>20} {'same-day ordering':>20}")
    for arr in ([2, 2, 2], [5, 4, 3], [1], [7, 1, 5, 3, 6, 4], [3, 3, 3, 3]):
        good = sol.maxProfit_indices(arr)
        bug = sol.maxProfit_indices(arr, same_day_bug=True)
        flag = "  <- buy == sell!" if bug[1] is not None and bug[1] == bug[2] else ""
        print(f"  {str(arr):<22} {str(good):>20} {str(bug):>20}{flag}")

    print("\n--- ...and as a profit, it never disagrees (3000 random arrays) ---")
    random.seed(3)
    diff = 0
    for _ in range(3000):
        arr = [random.randint(0, 12) for _ in range(random.randint(1, 10))]
        if sol.maxProfit(arr) != sol.maxProfit_same_day(arr):
            diff += 1
    print(f"  disagreements: {diff} / 3000 — correct BY ACCIDENT, not by design.")

    # ----------------------------------------------------------------------
    # The Kadane equivalence, shown numerically.
    # ----------------------------------------------------------------------
    print("\n--- this problem IS Kadane on the delta array ---")
    prices = [7, 1, 5, 3, 6, 4]
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    print(f"  prices = {prices}")
    print(f"  deltas = {deltas}")
    print("  Best contiguous run of deltas = [4, -2, 3] = 5, spanning days 1..4,")
    print(f"  and prices[4] - prices[1] = {prices[4]} - {prices[1]} = "
          f"{prices[4] - prices[1]}.  A subarray of deltas telescopes.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n^2), measured.
    # ----------------------------------------------------------------------
    print("\n--- one pass vs every pair ---")
    print(f"  {'n':>7} {'O(n) scan':>12} {'O(n^2) pairs':>14}")
    for n in (500, 1000, 2000, 4000):
        arr = [random.randint(0, 10_000) for _ in range(n)]
        t0 = time.perf_counter(); sol.maxProfit(arr)
        t1 = time.perf_counter(); sol.maxProfit_brute(arr)
        t2 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>10.2f}ms {(t2 - t1) * 1000:>12.1f}ms")
    print("  Doubling n doubles the scan and QUADRUPLES the pair search. At the")
    print("  real constraint n = 100000 the pair version is ~5e9 operations.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
