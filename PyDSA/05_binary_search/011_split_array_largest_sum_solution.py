"""
================================================================================
SOLUTION · LeetCode 410 · Split Array Largest Sum                        [Hard]
https://leetcode.com/problems/split-array-largest-sum/
================================================================================

THE CORE IDEA
--------------
This is problem 006 (Koko) and problem 010 (Ship Packages) for the third
time: **Family B — binary search on the ANSWER** (topic guide §1.1). Same
skeleton, different `feasible()`. Nothing else changes.

The question "minimize the largest subarray sum over all k-way splits"
looks like an optimisation over an astronomical number of splits
(C(n-1, k-1) of them). Turn it upside down into a YES/NO question about a
candidate answer:

    feasible(cap) = "can I cut `nums` into AT MOST k contiguous pieces,
                     each with sum <= cap?"

Evaluate it greedily in one O(n) pass: walk left to right accumulating a
running sum; the moment adding the next element would exceed `cap`, close
the current piece and start a new one. Count the pieces. Feasible iff that
count is `<= k`.

`feasible` is **monotone**: raising `cap` can only let a piece hold as many
or more elements, never fewer, so the piece count is non-increasing in
`cap`. Therefore

    feasible(cap) = False, False, ..., False, True, True, ..., True
                                          ^
                                          the answer: the leftmost True

and the answer is exactly the leftmost `cap` where it flips — a boundary
search:

    lo, hi = max(nums), sum(nums)
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid          # mid might BE the answer, keep it
        else:
            lo = mid + 1      # mid proven too small, discard
    return lo

O(n · log(sum(nums))) time, O(1) space.


================================================================================
"SAME SKELETON, DIFFERENT feasible()" — 875 / 1011 / 410 SIDE BY SIDE
================================================================================
The three Family B problems in this folder are the SAME twelve lines of
binary search. Only the greedy simulation inside `feasible` differs — and
in 010 vs 011 not even that, only the name of the thing being counted:

    Problem            candidate x      feasible(x) simulates                  budget
    -----------------  ---------------  --------------------------------------  ---------------
    006 · LC 875       eating speed     sum(ceil(pile / x)) hours               <= h hours
      Koko Bananas
    010 · LC 1011      ship capacity    greedy load-in-order; count days        <= days days
      Ship Packages
    011 · LC 410       largest piece    greedy accumulate-in-order; count       <= k pieces
      Split Array        sum              pieces                                  (THIS FILE)

    010 and 011 are the SAME greedy loop. "Start a new day when the next
    package won't fit" and "start a new piece when the next element won't
    fit" are one algorithm; `days` and `k` are one budget. If you can write
    010 you have already written 011 — recognising that is the whole point
    of doing all three.

**THE GENERAL RECIPE (memorise this, not the problems)**

    1. IDENTIFY THE MONOTONE PREDICATE.
       Restate "minimise/maximise X" as "is candidate value x good enough?"
       — a boolean. Then prove the boolean is monotone in x: "if x works,
       does x+1 work?" If you cannot answer that in one sentence, you do
       not have a binary search (topic guide Part 4, mistake 6).

    2. BOUND lo AND hi with values you can JUSTIFY.
       lo = the smallest candidate that is not trivially impossible.
       hi = a candidate that is trivially possible (a witness the answer
       exists). Both bounds need a one-line proof — see the next section;
       getting either wrong is the #1 way this template silently returns a
       wrong answer, and the runtime demo below proves it.

    3. FIND THE BOUNDARY with the leftmost-True template.
       `while lo < hi` / `hi = mid` / `lo = mid + 1` / return `lo`.
       Say out loud what `lo == hi` means before returning it.

Steps 1 and 2 are the interview. Step 3 is muscle memory.


================================================================================
WHY lo = max(nums) AND hi = sum(nums)
================================================================================
**lo = max(nums)** — every element must live inside SOME piece, and a piece
is contiguous and non-splittable, so the largest piece sum is at least the
largest single element. No `cap < max(nums)` can ever be a valid answer.
This is not merely an optimisation to save iterations: the greedy
`feasible()` above is *only correct for cap >= max(nums)*. Look at it
again —

    if cur + x > cap:  pieces += 1;  cur = 0
    cur += x

— when a single `x > cap`, the loop dutifully opens a new piece and then
puts `x` in it anyway, producing a piece whose sum EXCEEDS `cap`. The
piece count it returns is a lie for such caps, and if `k >= n` that lie
reads as "feasible". Starting at `lo = max(nums)` makes the lie
unreachable. (The alternative is a guard — `if x > cap: return False` —
which lets `lo = 0` work; both are fine, but you must do exactly one of
them. The runtime demo shows `lo = 1` with the unguarded greedy returning
**1** instead of **5** for `nums=[1,2,3,4,5], k=5`.)

**hi = sum(nums)** — one single piece containing everything has sum
`sum(nums)`, and `1 <= k` always, so `feasible(sum(nums))` is
unconditionally True. That makes `hi` a *witness*: the answer provably
exists in `[lo, hi]`, which is what licenses the boundary search. Any
"tighter, smarter" upper bound needs its own proof, and the obvious
candidate does not have one: `hi = sum(nums) // k` (the perfect-balance
average) is WRONG whenever the data cannot be balanced —
`nums=[7,2,5,10,8], k=2` has `sum//k = 16` but the answer is **18**. The
demo below prints that too. When in doubt, use the loose provable bound;
`log2` of a big range is still tiny (`sum <= 10^9` → 30 iterations).


================================================================================
THE DP ALTERNATIVE — AND WHY BINARY SEARCH WINS
================================================================================
LC 410 is a textbook interval-partition DP, and it is worth being able to
state it, because an interviewer may ask "can you do it without binary
search?" (and because the DP is the ONLY option if the array can contain
negative numbers — see the follow-ups).

    dp[j][i] = the minimised largest-piece sum when the first `i` elements
               are split into exactly `j` pieces

    dp[1][i] = prefix[i]                              (one piece: the sum)
    dp[j][i] = min over t in [j-1, i-1] of
                   max( dp[j-1][t], prefix[i] - prefix[t] )
               ^ the last piece is nums[t..i-1]; its sum is prefix[i]-prefix[t]

    answer = dp[k][n]

Correct, and it needs no monotonicity argument at all. But price it:

    states:          k · n
    work per state:  O(n)   (the inner scan over the split point t)
    total:           O(n^2 · k)   time,   O(n) space with a rolling row

Against binary search's `O(n · log(sum(nums)))`. With the problem's own
constraints (`n <= 1000`, `k <= 50`, `nums[i] <= 10^6`) that is
50,000,000 versus 1000 · 30 = 30,000 — three orders of magnitude, and
CPython's constant factor is not forgiving. The runtime demo benchmarks
both implementations in this file and measures the real gap (measured
on this machine: roughly **20x at n=100, ~90x at n=200, ~230x at n=400
and ~480x at n=600** — the ratio GROWS because the DP is quadratic in n
while the binary search is linear).

The deeper point: the DP searches the SPACE OF SPLITS. Binary search
searches the SPACE OF ANSWERS and never enumerates a split at all. When
the answer's range is numeric and a feasibility check is cheap, searching
the answer is almost always the cheaper space.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [7, 2, 5, 10, 8], k = 2
lo = max(nums) = 10, hi = sum(nums) = 32

    lo=10 hi=32  mid=21
        greedy at cap 21:  7 | 7+2=9 | 9+5=14 | 14+10=24 > 21 -> CUT
                           piece 1 = [7,2,5] (14)
                           10 | 10+8=18 <= 21
                           piece 2 = [10,8] (18)
        pieces = 2   2 <= 2 -> feasible -> hi = 21

    lo=10 hi=21  mid=15
        greedy at cap 15:  7 | 9 | 14 | 14+10=24 > 15 -> CUT
                           piece 1 = [7,2,5] (14)
                           10 | 10+8=18 > 15 -> CUT
                           piece 2 = [10] (10)
                           piece 3 = [8] (8)
        pieces = 3   3 > 2  -> INFEASIBLE -> lo = 16

    lo=16 hi=21  mid=18
        greedy at cap 18:  7 | 9 | 14 | 24 > 18 -> CUT   piece 1 = [7,2,5]
                           10 | 10+8=18 <= 18            piece 2 = [10,8]
        pieces = 2   2 <= 2 -> feasible -> hi = 18

    lo=16 hi=18  mid=17
        greedy at cap 17:  7 | 9 | 14 | 24 > 17 -> CUT   piece 1 = [7,2,5]
                           10 | 18 > 17 -> CUT           piece 2 = [10]
                                                          piece 3 = [8]
        pieces = 3   3 > 2  -> INFEASIBLE -> lo = 18

    lo=18 hi=18  -> loop ends -> return 18

    18 means: "the smallest cap for which 2 pieces suffice" — the split is
    [7,2,5] | [10,8] with piece sums 14 and 18, largest = 18.   ✓


    The predicate's shape, printed as a strip (the runtime demo prints this):

        cap:  10 11 12 13 14 15 16 17 18 19 20 ...
        feas:  F  F  F  F  F  F  F  F  T  T  T ...
                                       ^ leftmost True = the answer


================================================================================
WHY "AT MOST k PIECES" IS THE SAME AS "EXACTLY k PIECES"
================================================================================
The problem says split into exactly `k` subarrays; `feasible()` counts the
pieces the greedy actually needed and accepts `<= k`. These agree, and the
reason is worth having ready:

If the greedy fits everything into `p < k` pieces at capacity `cap`, you
can always cut one of those pieces in two (possible while `p < n`, and
`k <= n` is guaranteed) — splitting a piece can only make piece sums
SMALLER, never larger, so all pieces still satisfy `<= cap`. Repeat until
you have exactly `k`. So "at most k" is achievable iff "exactly k" is, and
the greedy's `<= k` test is the right one. Using `== k` instead would be
both harder to compute and wrong.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time              Space  Mutates input?  Note
    ------------------------------------  ----------------  -----  --------------  ------------------------
    Enumerate every k-way split           O(C(n-1,k-1) · n) O(k)   no              exponential; state it,
                                                                                    price it, never code it
    Interval-partition DP                 O(n^2 · k)        O(n)   no              correct, no monotonicity
                                                                                    needed; the fallback for
                                                                                    negative numbers
    Binary search on the answer ✅        O(n · log S)      O(1)   no              the answer.
      (S = sum(nums))                                                               ~30 feasible() calls for
                                                                                    S <= 10^9, each O(n)

    Note the space column: the winner is also the only O(1)-space approach —
    binary search on the answer never allocates anything but a few ints.


================================================================================
EDGE CASES
================================================================================
    k == 1                  -> the whole array is one piece; the answer is
                                exactly sum(nums), and the search collapses
                                because hi is already the answer.
    k == len(nums)           -> every element is its own piece; the answer is
                                exactly max(nums), and the search collapses
                                because lo is already the answer. THIS is the
                                case that exposes a too-small `lo` (see the
                                demo): with lo=1 and the unguarded greedy,
                                feasible(1) wrongly reports True.
    len(nums) == 1           -> lo == hi == nums[0] immediately, loop body
                                never runs.
    zeros in nums (allowed:  -> a zero can be appended to any piece for free;
      0 <= nums[i])            harmless for the greedy, and the answer can be
                                0 only if every element is 0.
    all elements equal       -> the piece count is a clean step function of
                                cap; a good stress case for the boundary
                                arithmetic.
    k > number of distinct   -> irrelevant: pieces are positional, not
      values                    value-based. No dedupe anywhere.


================================================================================
COMMON MISTAKES
================================================================================
1. `lo = 0` or `lo = 1` with the unguarded greedy `feasible()`. The greedy
   silently produces pieces larger than `cap` when a single element exceeds
   `cap`, so `feasible()` lies, and the binary search happily converges on
   an impossible answer. Proven at runtime below: `[1,2,3,4,5], k=5`
   returns **1** instead of **5**. Fix: `lo = max(nums)` (or add
   `if x > cap: return False` to the greedy).

2. A "tighter" `hi`, most often `hi = sum(nums) // k`. There is no proof
   that a balanced split exists, and usually none does. Proven at runtime:
   `[7,2,5,10,8], k=2` returns **16** instead of **18**. `hi = sum(nums)`
   is provably feasible; use it.

3. `hi = mid - 1` instead of `hi = mid` on the feasible branch — discards a
   `mid` that may be the true minimum, so the returned value is one too
   large (or the loop overshoots entirely). Pair `while lo < hi` with
   `hi = mid` and `lo = mid + 1`, always (topic guide §1.2c/d).

4. Forgetting the greedy starts at `pieces = 1`, not `0`. The first piece
   is opened before the loop; the `pieces += 1` inside the loop counts
   CUTS, and n elements with c cuts make c+1 pieces. Starting at 0
   under-counts by one and reports infeasible caps as feasible.

5. Testing `pieces == k` instead of `pieces <= k`. The greedy minimises the
   piece count for a given cap; it cannot be asked to hit `k` exactly. See
   the "at most k" section above for why `<=` is not just easier but
   correct.

6. Reaching for the DP first. It is not wrong — it is O(n^2·k) and it is
   what the binary search replaces. Mentioning it and then explaining why
   you are not using it is a strictly better interview answer than either
   coding it or not knowing it.

7. Not saying the monotonicity sentence out loud before writing the loop.
   "Raising the cap can only reduce the number of pieces needed, so
   feasible flips false-to-true exactly once" is the entire justification
   for the algorithm; skipping it is what makes a candidate look like they
   pattern-matched rather than reasoned.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if `nums` may contain NEGATIVE numbers?
A: Binary search breaks. Two independent reasons: (a) `lo = max(nums)` and
   `hi = sum(nums)` stop being valid bounds — `sum` can be less than `max`;
   (b) more fundamentally the greedy is no longer monotone, because
   extending a piece with a negative number DECREASES its sum, so "would
   the next element overflow the cap?" is no longer a reason to cut. Fall
   back to the O(n^2·k) DP, which never assumes monotonicity. This is the
   single best reason to know the DP.

Q: Can you make the DP faster?
A: Yes, to O(n·k) with the divide-and-conquer-optimisation / SMAWK-style
   monotonicity of the optimal split point (the argmin `t` for `dp[j][i]`
   is non-decreasing in `i`). Worth naming; nobody expects you to code it
   in 40 minutes.

Q: The subarrays must be contiguous. What if they need not be — just
   partition the multiset into k groups minimising the largest group sum?
A: That is the multiway number-partitioning problem, NP-hard. The
   contiguity constraint is exactly what makes the greedy `feasible()` an
   O(n) pass instead of a search. (Same answer as 010's re-ordering
   follow-up — the constraint IS the algorithm.)

Q: How would you also RETURN the split, not just its largest sum?
A: Run the greedy once more at `cap = answer`, recording the cut indices.
   One extra O(n) pass, no change in complexity. If fewer than k pieces
   come out, split any piece of length >= 2 until you have k (safe, per the
   "at most k" argument above).

Q: What if `k` is huge — say k >= n?
A: The answer is `max(nums)` and the loop exits immediately since
   `feasible(lo)` is already true. No special case needed; the bounds
   handle it. (`k <= min(50, n)` here, but say it anyway.)

Q: Could you binary-search on a real-valued cap?
A: Pointless. All sums are integers, so the answer is an integer and every
   real cap in `[c, c+1)` yields the same piece count as `c`. Discrete
   binary search is exact and terminates; float bisection needs an epsilon
   and can only approximate. Naming this shows you know when NOT to use
   continuous bisection.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
"Binary search on the answer with a greedy feasibility predicate" — once
you see the shape, these are all the same problem:

    LC 875   Koko Eating Bananas            — 006 here. Family B debut;
                                               feasible() = ceil-division hours
    LC 1011  Capacity To Ship Packages       — 010 here. feasible() = greedy
             Within D Days                     load-in-order day count. The
                                               closest sibling of this problem
    LC 410   Split Array Largest Sum         — THIS FILE. feasible() = greedy
                                               piece count
    LC 1482  Minimum Number of Days to        — feasible(day) = count bloomed
             Make m Bouquets                    runs; same skeleton
    LC 1231  Divide Chocolate                 — the MAXIMISE mirror: largest
                                               minimum piece. Same greedy,
                                               flip the template to
                                               "rightmost True"
    LC 1552  Magnetic Force Between Two       — maximise the minimum gap;
             Balls                              feasible(gap) = greedy placement
    LC 774   Minimize Max Distance to Gas      — real-valued cap, so this one
             Station                            genuinely needs float bisection
                                                with an epsilon
    LC 1283  Find the Smallest Divisor         — feasible(d) = sum of
             Given a Threshold                   ceil(nums[i]/d) <= threshold
    LC 1891  Cutting Ribbons                  — maximise piece length;
                                               feasible(len) = total pieces >= k
    LC 2064  Minimized Maximum of Products     — minimise the max per store;
             Distributed to Any Store            identical to this problem's shape

    Same-DP family (if binary search is off the table):
    LC 1335  Minimum Difficulty of a Job       — O(n^2·k) interval-partition DP,
             Schedule                            the exact dp[j][i] recurrence
                                                 above, but NOT monotone, so
                                                 binary search does not apply
    LC 813   Largest Sum of Averages           — same dp shape, averages instead
                                                 of max
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def splitArray(self, nums: List[int], k: int) -> int:
        """Binary search on the answer (Family B), greedy feasibility.
        O(n log(sum(nums))) time, O(1) space. The answer.
        See THE CORE IDEA above."""
        def feasible(cap: int) -> bool:
            # How many contiguous pieces does a greedy left-to-right cut
            # need, if no piece may exceed `cap`?  (Correct only for
            # cap >= max(nums) — see WHY lo = max(nums).)
            pieces, cur = 1, 0
            for x in nums:
                if cur + x > cap:
                    pieces += 1     # CUT here: close this piece, open a new one
                    cur = 0
                cur += x
            return pieces <= k

        lo, hi = max(nums), sum(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if feasible(mid):
                hi = mid            # mid may BE the answer — keep it in range
            else:
                lo = mid + 1        # mid proven too small — discard it
        return lo                   # lo == hi == leftmost feasible cap

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def splitArray_dp(self, nums: List[int], k: int) -> int:
        """O(n^2 · k) time, O(n) space interval-partition DP. Correct with no
        monotonicity assumption — the fallback when nums may go negative."""
        n = len(nums)
        prefix = [0] * (n + 1)
        for i, x in enumerate(nums):
            prefix[i + 1] = prefix[i] + x

        INF = float("inf")
        # row for j == 1: one piece covering nums[0..i-1]
        row = [prefix[i] for i in range(n + 1)]
        for j in range(2, k + 1):
            nxt = [INF] * (n + 1)
            for i in range(j, n + 1):
                best = INF
                for t in range(j - 1, i):
                    # last piece is nums[t..i-1]
                    v = max(row[t], prefix[i] - prefix[t])
                    if v < best:
                        best = v
                nxt[i] = best
            row = nxt
        return int(row[n])

    def splitArray_bad_lo(self, nums: List[int], k: int) -> int:
        """✗ BUGGY on purpose: lo = 1 instead of max(nums). The unguarded
        greedy lies about caps smaller than a single element."""
        lo, hi = 1, sum(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.pieces_needed(nums, mid) <= k:
                hi = mid
            else:
                lo = mid + 1
        return lo

    def splitArray_bad_hi(self, nums: List[int], k: int) -> int:
        """✗ BUGGY on purpose: hi = sum(nums) // k, the 'balanced split'
        bound, which is unprovable and usually too small."""
        lo, hi = max(nums), max(max(nums), sum(nums) // k)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.pieces_needed(nums, mid) <= k:
                hi = mid
            else:
                lo = mid + 1
        return lo

    @staticmethod
    def pieces_needed(nums: List[int], cap: int) -> int:
        """The greedy piece count, exposed so the demos can print it."""
        pieces, cur = 1, 0
        for x in nums:
            if cur + x > cap:
                pieces += 1
                cur = 0
            cur += x
        return pieces


# ==============================================================================
# TESTS — run:  python 011_split_array_largest_sum_solution.py
# ==============================================================================
CASES = [
    ([7, 2, 5, 10, 8], 2, 18),
    ([1, 2, 3, 4, 5], 2, 9),
    ([1, 4, 4], 3, 4),
    ([1], 1, 1),
    ([1, 2, 3, 4, 5], 1, 15),
    ([1, 2, 3, 4, 5], 5, 5),
    ([2, 3, 1, 2, 4, 3], 3, 6),
    ([0, 0, 0, 0], 2, 0),
    ([5, 5, 5, 5], 2, 10),
    ([1000000, 1000000], 1, 2000000),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: binary search on the answer ---")
    for nums, k, expected in CASES:
        got = sol.splitArray(nums, k)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<26} k={k:<3} -> {got}  (want {expected})")

    print("\n--- cross-check vs the O(n^2 · k) interval-partition DP ---")
    for nums, k, expected in CASES:
        a = sol.splitArray(nums, k)
        b = sol.splitArray_dp(nums, k)
        ok = a == b == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<26} k={k:<3} bs={a:<8} dp={b}")

    # ----------------------------------------------------------------------
    # Prove feasible(cap) is monotone — print the predicate as a strip.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ proving feasible(cap) flips false->true exactly once ---")
    nums, k = [7, 2, 5, 10, 8], 2
    lo0, hi0 = max(nums), sum(nums)
    caps = list(range(lo0, hi0 + 1))
    flags = [sol.pieces_needed(nums, c) <= k for c in caps]
    print(f"  nums={nums} k={k}   lo=max={lo0}  hi=sum={hi0}")
    print("  cap :  " + " ".join(f"{c:>2}" for c in caps))
    print("  feas:  " + " ".join(f"{'T' if f else 'F':>2}" for f in flags))
    flips = sum(1 for a, b in zip(flags, flags[1:]) if a != b)
    first_true = caps[flags.index(True)]
    monotone_ok = flips == 1 and first_true == 18
    all_ok &= monotone_ok
    print(f"  transitions in the strip: {flips} (must be exactly 1)  "
          f"leftmost True = {first_true} = the answer -> {monotone_ok}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: nums=[7,2,5,10,8], k=2 ---")
    lo, hi = max(nums), sum(nums)
    print(f"  {'lo':>3} {'hi':>3} {'mid':>4} {'pieces':>7} {'feasible':>9}  action")
    while lo < hi:
        mid = (lo + hi) // 2
        p = sol.pieces_needed(nums, mid)
        f = p <= k
        action = f"feasible -> hi = {mid}" if f else f"infeasible -> lo = {mid + 1}"
        print(f"  {lo:>3} {hi:>3} {mid:>4} {p:>7} {str(f):>9}  {action}")
        if f:
            hi = mid
        else:
            lo = mid + 1
    print(f"  lo == hi == {lo}  ->  minimum largest-piece sum is {lo}")

    # ----------------------------------------------------------------------
    # ⚠️ RUNTIME DEMO 1: the bounds are not decoration.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ what BAD BOUNDS actually return (not a hypothetical) ---")
    print("  bad_lo:  lo = 1            instead of max(nums)")
    print("  bad_hi:  hi = sum(nums)//k instead of sum(nums)  ('balanced split')")
    print(f"  {'nums':<22} {'k':>2} {'correct':>8} {'bad_lo':>8} {'bad_hi':>8}   verdict")
    bound_demo_ok = False
    for nums_d, k_d, expected in CASES[:6]:
        good = sol.splitArray(nums_d, k_d)
        blo = sol.splitArray_bad_lo(nums_d, k_d)
        bhi = sol.splitArray_bad_hi(nums_d, k_d)
        marks = []
        if blo != good:
            marks.append("bad_lo WRONG")
        if bhi != good:
            marks.append("bad_hi WRONG")
        if marks:
            bound_demo_ok = True
        verdict = " + ".join(marks) if marks else "both happen to agree here"
        print(f"  {str(nums_d):<22} {k_d:>2} {good:>8} {blo:>8} {bhi:>8}   {verdict}")
    print("  Why bad_lo breaks: with cap < max(nums) the greedy still puts the")
    print("    oversized element into a fresh piece, so the piece count it")
    print("    reports is a LIE; when k >= n that lie reads as 'feasible'.")
    print("  Why bad_hi breaks: sum//k assumes a perfectly balanced split")
    print("    exists. [7,2,5,10,8] cannot be balanced — 16 is unreachable, the")
    print("    real answer 18 lies OUTSIDE the search range, so the loop")
    print("    converges on hi itself and returns it.")
    all_ok &= bound_demo_ok

    # ----------------------------------------------------------------------
    # Randomised cross-check: binary search vs DP.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check: binary search vs DP ---")
    random.seed(410)
    trials, mismatches = 400, 0
    for _ in range(trials):
        n = random.randint(1, 9)
        arr = [random.randint(0, 40) for _ in range(n)]
        kk = random.randint(1, n)
        if sol.splitArray(arr, kk) != sol.splitArray_dp(arr, kk):
            mismatches += 1
    print(f"  {trials} random (nums, k) pairs: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # ⚠️ RUNTIME DEMO 2: O(n log S) binary search vs O(n^2 k) DP.
    # ----------------------------------------------------------------------
    print("\n--- O(n·log S) binary search vs O(n^2·k) DP: measured runtime ---")
    print(f"  {'n':>5} {'k':>4} {'binary search':>15} {'DP':>13} {'speedup':>9} {'agree':>7}")
    random.seed(9)
    for n, kk in ((100, 10), (200, 20), (400, 25), (600, 30)):
        arr = [random.randint(1, 10 ** 6) for _ in range(n)]
        t0 = time.perf_counter()
        a = sol.splitArray(arr, kk)
        t1 = time.perf_counter()
        b = sol.splitArray_dp(arr, kk)
        t2 = time.perf_counter()
        bs_ms = (t1 - t0) * 1000
        dp_ms = (t2 - t1) * 1000
        ok = a == b
        all_ok &= ok
        print(f"  {n:>5} {kk:>4} {bs_ms:>13.2f}ms {dp_ms:>11.2f}ms "
              f"{dp_ms / bs_ms:>8.0f}x {str(ok):>7}")
    print("  The ratio GROWS with n because the DP is quadratic in n while the")
    print("  binary search is linear: doubling n roughly doubles the binary")
    print("  search's cost and roughly quadruples the DP's.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
