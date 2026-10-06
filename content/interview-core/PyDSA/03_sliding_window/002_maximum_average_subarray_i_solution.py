"""
================================================================================
SOLUTION · LeetCode 643 · Maximum Average Subarray I                      [Easy]
https://leetcode.com/problems/maximum-average-subarray-i/
================================================================================

THE CORE IDEA
-------------
Prime the first window in O(k), then slide it with two operations per step:

    s = sum(nums[:k])
    best = s
    for r in range(k, len(nums)):
        s += nums[r] - nums[r - k]        # nums[r] ENTERS, nums[r-k] LEAVES
        best = max(best, s)
    return best / k

O(n) time, O(1) space. Two ideas are doing all the work:

    1. CONSECUTIVE WINDOWS OVERLAP IN k-1 ELEMENTS, so the shared part never
       needs re-adding. Only the difference matters.
    2. EVERY WINDOW HAS THE SAME DIVISOR, so maximise the SUM and divide once.


================================================================================
WHY MAXIMISE THE SUM, NOT THE AVERAGE
================================================================================
Because `k` is a positive constant, `x -> x / k` is strictly increasing, so it
preserves order:

        sum(A) > sum(B)   <=>   sum(A)/k > sum(B)/k

Comparing sums is therefore EXACTLY as correct as comparing averages, and it is
better in two ways:

  * One division instead of n.
  * The comparison is done in EXACT INTEGER ARITHMETIC. Python's ints are
    arbitrary precision, so no rounding happens at all.

That second point is not academic. If you carry the window value as a FLOAT and
do `s += x; s -= y` a hundred thousand times, error accumulates: floats are not
associative, so the running value drifts from the true sum. Two windows with
genuinely different sums can then compare equal, and a window can even appear
to beat one that is truly larger. The demo at the bottom of this file
constructs exactly that: an array where the float-accumulating version drifts
and picks the WRONG window, while the integer version is exact.

The general principle, worth stating in an interview:

    KEEP THE RUNNING AGGREGATE IN THE MOST EXACT TYPE AVAILABLE, AND CONVERT
    ONCE AT THE BOUNDARY.


================================================================================
THE TWO OFF-BY-ONES
================================================================================
Both loop forms are fine. Know exactly why each bound is what it is.

FORM 1 · Prime, then slide (`r` = the entering index, starting at k)

    s = sum(nums[:k])           # window is nums[0..k-1]
    for r in range(k, n):       # r = k, k+1, ..., n-1
        s += nums[r] - nums[r - k]

    * `range(k, n)` — the first ENTERING element is index k, because indices
      0..k-1 are already inside.
    * `nums[r - k]` is the leaving element: when nums[r] joins, the window
      becomes [r-k+1 .. r], so the one that dropped out is r-k.

FORM 2 · Single loop (`r` = the entering index, starting at 0)

    s = 0
    for r in range(n):
        s += nums[r]                       # always enter
        if r >= k:                         # window would be k+1 wide
            s -= nums[r - k]               # so evict the oldest
        if r >= k - 1:                     # window is exactly k wide
            best = max(best, s)

    * `r >= k` for the EVICTION.  At r = k-1 the window is exactly k, nothing
      should leave yet. The first eviction happens at r = k.
    * `r >= k - 1` for the ANSWER. The first complete window ends at index
      k-1. Using `r >= k` here silently skips the first window — the classic
      failure, and it only shows up when the answer IS that first window
      (test case [8,9,1,1,1,1], k=2).

    The two thresholds differ by exactly one and they are NOT interchangeable.

Prefer FORM 2. It needs no priming slice, it handles k == n without a special
case, and it is the shape every other problem in this folder uses.

    HOW MANY WINDOWS ARE THERE?  n - k + 1.
    If your loop produces a different count, one of the two bounds is wrong.
    Counting them is the fastest way to check yourself.


================================================================================
NEGATIVES ARE HARMLESS HERE — AND THAT IS WORTH UNDERSTANDING
================================================================================
The constraints allow `nums[i] < 0`. Later in this folder (LC 209) negative
values would DESTROY the algorithm. Here they are irrelevant. Why?

    A fixed-size window never makes a decision about where `l` goes.

`l` is always `r - k + 1`. There is no "shrink while invalid" step, so there is
no moment where the code reasons "removing this element can only decrease the
sum" — which is the step that needs non-negativity (topic guide, Part 1.2).

    Fixed window (Shape A)     -> sign-agnostic. l is a formula, not a decision.
    Variable window (B/C/E)    -> needs the hereditary property, hence the
                                  sign constraint on sum-based predicates.

The one thing negatives DO break is a lazy initialisation:

    best = 0        # ✗ WRONG on [-5,-3,-8,-2], k=2: returns 0/2 = 0.0
    best = -inf     # ✓ or, better, seed with the first window's actual sum

`findMaxAverage_zero_init` below is the broken version, kept so the test suite
can show it failing on all-negative input.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(nums)

    Approach                       Time      Space   Note
    -----------------------------  --------  ------  ------------------------
    sum(nums[i:i+k]) per window    O(n*k)    O(k)    slices copy, too
    Prefix sums, then n-k+1 reads  O(n)      O(n)    correct, wastes space
    Slide with enter/leave ✅      O(n)      O(1)    each element touched twice

    O(n) is optimal: the answer can depend on any element, so all must be read.

    ⚠️  `sum(nums[i:i+k])` is doubly bad — the slice ALLOCATES a k-element list
        and then `sum` walks it. Two O(k) costs per iteration.

    ⚠️  Prefix sums (topic 04) solve this in O(n) too — window sum is
        `pre[i+k] - pre[i]` — but need O(n) memory. Mention it as the
        generalisation that answers ARBITRARY ranges, then say the window is
        better here because we only ever need consecutive ones.


================================================================================
EDGE CASES
================================================================================
    k == n            Exactly ONE window. The loop body may never execute
                      (Form 1) — the answer must already be correct from the
                      priming step. Test: [4,0,4,3,3], k=5.

    k == 1            n windows, each a single element; the answer is
                      max(nums). Exercises `r >= k - 1` at r = 0.

    n == 1, k == 1    Both degenerate at once: [5] -> 5.0.

    all negative      [-5,-3,-8,-2], k=2 -> -4.0. THE `best = 0` DETECTOR.

    all equal         [3,3,3,3,3], k=3 -> 3.0. Every window ties; make sure a
                      strict `>` vs `>=` choice does not matter (it does not,
                      since you return a value, not an index).

    best at the front [8,9,1,1,1,1], k=2 -> 8.5. THE `r >= k` (instead of
                      `r >= k-1`) DETECTOR: that bug skips the first window,
                      and the first window is the answer.

    best at the end   [1,1,1,1,9,8], k=2 -> 8.5. Catches a loop that stops one
                      iteration early.

    ⚠️  There is no "k > n" case — the constraints forbid it. If you want the
        code robust anyway, `if k > n: return 0.0` or raise; say which and why.


================================================================================
COMMON MISTAKES
================================================================================
1. `sum(nums[i:i+k])` inside the loop. The single most common way to write an
   "O(n) sliding window" that is actually O(n*k). If your code contains `sum(`
   or a slice INSIDE the loop, it is not a sliding window.

2. `best = 0`. Fails on all-negative input. Seed with the first window's sum,
   or `float('-inf')`.

3. Using `r >= k` as the record condition, skipping the first window.

4. Carrying the running value as a float and letting error accumulate. Track
   an integer sum; divide once at the end.

5. Dividing inside the loop (`best = max(best, s / k)`). Correct, but it does
   n divisions for no reason and reintroduces float comparison.

6. Off-by-one in the eviction index: `nums[r - k + 1]` instead of `nums[r - k]`.
   Check it on k=1, where the element entering and the element leaving are the
   same index and the sum must always equal `nums[r]`.

7. Returning an int. `sum // k` truncates; [1,2] with k=2 must give 1.5.

8. Building a prefix-sum array and calling it a sliding window. It is a fine
   solution, it is just a different technique with O(n) space — name it
   honestly.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Maximum average of a subarray of length AT LEAST k (LC 644)?
A: Much harder — the fixed-divisor trick dies, because different lengths mean
   different divisors and you can no longer just compare sums. The standard
   answer is BINARY SEARCH ON THE ANSWER: guess an average `x`, subtract it
   from every element, and ask "is there a subarray of length >= k with
   non-negative sum?" — which is a prefix-sum + running-minimum scan in O(n).
   O(n log(range/eps)) overall. Being able to name that pivot is the point of
   the follow-up.

Q: Return the starting INDEX of the best window instead of the average.
A: Track `best_start` alongside `best`. Then `>` vs `>=` starts to matter: `>`
   keeps the earliest maximal window, `>=` keeps the latest. State which
   tie-break you chose.

Q: The array is a STREAM; report the moving average of the last k values
   (LC 346).
A: Same arithmetic, but you cannot index `nums[r-k]` because the past is gone —
   hold the last k values in a `collections.deque(maxlen=k)`. Appending past
   the maxlen evicts the oldest automatically; subtract it before it goes.

Q: k is not fixed — answer many (l, k) queries after the fact.
A: Prefix sums (topic 04). O(n) preprocessing, O(1) per query. A window is a
   single left-to-right pass; prefix sums are the random-access version.

Q: Minimum average instead of maximum?
A: Identical code with `min`, seeded at `+inf`. The symmetry is a good check
   that your bounds are not accidentally tuned to `max`.

Q: 2-D — maximum average k x k submatrix?
A: Same idea twice: a 2-D prefix sum, or slide a row-window then a column
   window. O(m*n) either way. (Topic 24.)


================================================================================
RELATED PROBLEMS
================================================================================
    LC 644  Maximum Average Subarray II  — length >= k; binary search the answer
    LC 346  Moving Average from Stream   — the deque(maxlen=k) version
    LC 1456 Max Vowels in a Substring    — fixed window over a PREDICATE (next)
    LC 219  Contains Duplicate II        — fixed window over a SET
    LC 1052 Grumpy Bookstore Owner       — fixed window over the DELTA it buys
    LC 1343 Subarrays of Size K With Avg >= Threshold — the counting version
    LC 209  Minimum Size Subarray Sum    — the VARIABLE-size contrast
================================================================================
"""

import math
import random
import time
from typing import List


class Solution:
    def findMaxAverage(self, nums: List[int], k: int) -> float:
        """Single-loop fixed window over an exact integer sum. O(n)/O(1)."""
        s = 0
        best = float('-inf')
        for r, x in enumerate(nums):
            s += x                          # enter
            if r >= k:                      # window would be k+1 wide
                s -= nums[r - k]            # leave
            if r >= k - 1:                  # window is exactly k wide
                best = max(best, s)
            # NOTE: `r >= k` and `r >= k - 1` differ by one and are NOT the same
        return best / k

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def findMaxAverage_primed(self, nums: List[int], k: int) -> float:
        """Prime-then-slide form. Same work; needs the O(k) priming slice."""
        s = sum(nums[:k])
        best = s
        for r in range(k, len(nums)):
            s += nums[r] - nums[r - k]
            best = max(best, s)
        return best / k

    def findMaxAverage_prefix(self, nums: List[int], k: int) -> float:
        """Prefix sums: window [i, i+k) is pre[i+k] - pre[i]. O(n) time, O(n)
        space — the random-access generalisation (topic 04)."""
        pre = [0] * (len(nums) + 1)
        for i, x in enumerate(nums):
            pre[i + 1] = pre[i] + x
        return max(pre[i + k] - pre[i]
                   for i in range(len(nums) - k + 1)) / k

    def findMaxAverage_brute(self, nums: List[int], k: int) -> float:
        """O(n*k) oracle: recompute each window from scratch."""
        return max(sum(nums[i:i + k])
                   for i in range(len(nums) - k + 1)) / k

    # ------------------------------------------------------------------
    # Deliberate breakages.
    # ------------------------------------------------------------------
    def findMaxAverage_zero_init(self, nums: List[int], k: int) -> float:
        """✗ BROKEN ON PURPOSE — `best = 0` fails when every window is negative."""
        s, best = 0, 0
        for r, x in enumerate(nums):
            s += x
            if r >= k:
                s -= nums[r - k]
            if r >= k - 1:
                best = max(best, s)
        return best / k

    def findMaxAverage_late_record(self, nums: List[int], k: int) -> float:
        """✗ BROKEN ON PURPOSE — records on `r >= k`, skipping the FIRST window."""
        s, best = 0, float('-inf')
        for r, x in enumerate(nums):
            s += x
            if r >= k:
                s -= nums[r - k]
            if r >= k:                       # should be k - 1
                best = max(best, s)
        return best / k if best != float('-inf') else 0.0

    def findMaxAverage_float_accum(self, nums: List[int], k: int) -> float:
        """Accumulates in a FLOAT. Correct on integer input, but the pattern is
        unsafe the moment the values are non-integral — see the demo."""
        s = 0.0
        best = float('-inf')
        for r, x in enumerate(nums):
            s += x
            if r >= k:
                s -= nums[r - k]
            if r >= k - 1:
                best = max(best, s)
        return best / k


# ==============================================================================
# TESTS — run:  python 002_maximum_average_subarray_i_solution.py
# ==============================================================================
CASES = [
    ([1, 12, -5, -6, 50, 3], 4),
    ([5], 1),
    ([0, 1, 1, 3, 3], 4),
    ([-1], 1),
    ([-5, -3, -8, -2], 2),
    ([4, 0, 4, 3, 3], 5),
    ([1, 2, 3, 4, 5], 1),
    ([1, 2, 3, 4, 5], 2),
    ([8, 9, 1, 1, 1, 1], 2),
    ([1, 1, 1, 1, 9, 8], 2),
    ([-10000] * 5, 3),
    ([10000, -10000, 10000], 2),
    ([3, 3, 3, 3, 3], 3),
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("single loop    ", sol.findMaxAverage),
        ("prime-and-slide", sol.findMaxAverage_primed),
        ("prefix sums    ", sol.findMaxAverage_prefix),
        ("float accumulate", sol.findMaxAverage_float_accum),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(abs(fn(list(a), k) - sol.findMaxAverage_brute(a, k)) < 1e-9
                 for a, k in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n*k) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n*k) oracle ---")
    random.seed(643)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        n = random.randint(1, 14)
        arr = [random.randint(-30, 30) for _ in range(n)]
        k = random.randint(1, n)
        want = sol.findMaxAverage_brute(arr, k)
        for _, fn in impls:
            if abs(fn(list(arr), k) - want) > 1e-9:
                mismatches += 1
    print(f"  {trials} random (array, k) x {len(impls)} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The slide, traced.
    # ----------------------------------------------------------------------
    print("\n--- the window sliding over [1,12,-5,-6,50,3], k=4 ---")
    nums, k = [1, 12, -5, -6, 50, 3], 4
    print(f"  {'r':>2} {'enters':>7} {'leaves':>12} {'window':<20} {'sum':>5}"
          f" {'best':>5}")
    s, best = 0, float('-inf')
    for r, x in enumerate(nums):
        s += x
        left = f"nums[{r-k}]={nums[r-k]}" if r >= k else "-"
        if r >= k:
            s -= nums[r - k]
        if r >= k - 1:
            best = max(best, s)
            win = str(nums[r - k + 1:r + 1])
            print(f"  {r:>2} {x:>7} {left:>12} {win:<20} {s:>5} {best:>5.0f}")
        else:
            print(f"  {r:>2} {x:>7} {left:>12} {'(filling)':<20} {s:>5} {'-':>5}")
    print(f"  windows examined: {len(nums) - k + 1} = n - k + 1  ✓")
    print(f"  answer = {best}/{k} = {best / k}")

    # ----------------------------------------------------------------------
    # ⚠️  The two off-by-ones.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `r >= k - 1` vs `r >= k` for the RECORD step ---")
    print(f"  {'input':<26} {'k':>2} {'correct':>9} {'records on r>=k':>16}  ok?")
    for arr, k in ([8, 9, 1, 1, 1, 1], 2), ([1, 1, 1, 1, 9, 8], 2), \
                  ([5], 1), ([4, 0, 4, 3, 3], 5), ([1, 2, 3], 1):
        good = sol.findMaxAverage(list(arr), k)
        bad = sol.findMaxAverage_late_record(list(arr), k)
        same = abs(good - bad) < 1e-9
        note = "yes" if same else "NO  <- skipped the first window"
        print(f"  {str(arr):<26} {k:>2} {good:>9.2f} {bad:>16.2f}  {note}")

    # ----------------------------------------------------------------------
    # ⚠️  best = 0 on all-negative input.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `best = 0` vs `best = -inf` ---")
    print(f"  {'input':<26} {'k':>2} {'correct':>9} {'best=0':>9}  ok?")
    for arr, k in ([-5, -3, -8, -2], 2), ([-1], 1), ([-10000] * 3, 3), \
                  ([1, 2, 3], 2), ([-1, 5, -1], 1):
        good = sol.findMaxAverage(list(arr), k)
        bad = sol.findMaxAverage_zero_init(list(arr), k)
        same = abs(good - bad) < 1e-9
        print(f"  {str(arr):<26} {k:>2} {good:>9.2f} {bad:>9.2f}  "
              f"{'yes' if same else 'NO  <- every window is negative'}")

    # ----------------------------------------------------------------------
    # Why the running sum should not be a float.
    # ----------------------------------------------------------------------
    print("\n--- why you accumulate in EXACT arithmetic, not float ---")
    print("  This problem guarantees INTEGERS with |nums[i]| <= 10^4, so every")
    print("  window sum is well under 2^53 and float accumulation happens to be")
    print("  exact. The habit still matters — the moment the values are not")
    print("  integral, `s += x; s -= y` DRIFTS, and the drift grows with n:")
    print(f"  {'slides':>9} {'max drift vs exact':>20} {'final drift':>14}")
    random.seed(1)
    for n in (1_000, 10_000, 100_000):
        k = 100
        vals = [random.uniform(0, 1e6) for _ in range(n)]
        s, slid = 0.0, []
        for r, x in enumerate(vals):
            s += x
            if r >= k:
                s -= vals[r - k]
            if r >= k - 1:
                slid.append(s)
        exact = [math.fsum(vals[i:i + k]) for i in range(n - k + 1)]
        drift = [abs(a - b) for a, b in zip(slid, exact)]
        print(f"  {n:>9} {max(drift):>20.3e} {drift[-1]:>14.3e}")
    print("  Each slide rounds twice, and the error never cancels back out — it")
    print("  RANDOM-WALKS away from the truth. Two windows whose sums differ by")
    print("  less than the accumulated drift then compare backwards. An integer")
    print("  running sum cannot drift at all: carry the sum exact, divide once.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n*k), measured.
    # ----------------------------------------------------------------------
    print("\n--- sliding vs recomputing each window ---")
    print(f"  {'n':>7} {'k':>7} {'slide O(n)':>12} {'sum() O(nk)':>13}")
    for n, k in ((20_000, 10), (20_000, 500), (20_000, 5_000)):
        arr = [random.randint(-10_000, 10_000) for _ in range(n)]
        t0 = time.perf_counter(); sol.findMaxAverage(arr, k)
        t1 = time.perf_counter(); sol.findMaxAverage_brute(arr, k)
        t2 = time.perf_counter()
        print(f"  {n:>7} {k:>7} {(t1 - t0) * 1000:>10.1f}ms "
              f"{(t2 - t1) * 1000:>11.1f}ms")
    print("  The slide is FLAT in k — it does two operations per step no matter")
    print("  how wide the window is. The recompute grows linearly in k, and")
    print("  `sum(nums[i:i+k])` pays TWICE: the slice allocates, then sum walks.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
