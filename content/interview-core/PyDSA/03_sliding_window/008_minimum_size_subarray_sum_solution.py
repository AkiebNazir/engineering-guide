"""
================================================================================
SOLUTION · LeetCode 209 · Minimum Size Subarray Sum                     [Medium]
https://leetcode.com/problems/minimum-size-subarray-sum/
================================================================================

THE CORE IDEA
-------------
Shape C — the SHORTEST-window template. Grow on the right; while the window is
still valid, record its length and shrink from the left:

    l = 0
    total = 0
    best = float('inf')
    for r, x in enumerate(nums):
        total += x                              # ENTER
        while total >= target:                  # while STILL VALID
            best = min(best, r - l + 1)         # RECORD first
            total -= nums[l]                    # then SHRINK
            l += 1
    return 0 if best == float('inf') else best

O(n) time, O(1) space.


THE SHAPE FLIP — memorise this table
------------------------------------
    LONGEST (Shape B, problems 005-007)   SHORTEST (Shape C, this one)
    -----------------------------------   ----------------------------------
    while INVALID:  shrink                while VALID:  record, then shrink
    record AFTER the shrink loop          record INSIDE the shrink loop
    best = max(...)                       best = min(...)
    best starts at 0                      best starts at INFINITY
    the answer is a width you reached     the answer is a width you escaped

The intuition: a valid LONG window may improve by growing, so you repair and
keep going. A valid SHORT window may improve by shrinking, so you shrink while
you can and stop the instant it breaks.

⚠️  RECORD BEFORE SHRINKING. If you shrink first, `l` has already moved, so
    you measure a window one element SHORTER than the one that was actually
    valid — and the reported answer comes out one too SMALL. Trace target=4,
    nums=[1,4,4]: the correct order gives 1, the wrong order gives 0, which is
    not even a legal length (and here collides with the "not found" sentinel).

⚠️  `best = float('inf')`, never 0. `min(0, anything)` is 0 forever. Then
    translate the sentinel back to whatever the problem calls "not found" —
    here 0, in other problems -1. Two different zeros; keep them straight.


================================================================================
⚠️  THE SIGN CONSTRAINT — THE MOST IMPORTANT PARAGRAPH ON THIS PAGE
================================================================================
The constraint `1 <= nums[i]` is not decoration. The window is correct ONLY
because all values are positive:

    growing the window   ->  the sum can only INCREASE
    shrinking the window ->  the sum can only DECREASE

That monotonicity is what makes `l += 1` a permanent, safe decision: once the
window's sum has fallen below `target`, no further shrinking can rescue it, so
the only way forward is to grow. Equivalently, in topic-guide language, "sum >=
target" is UPWARD-CLOSED under growth — which is precisely the precondition for
a shortest-window search.

    NOW REMOVE THE CONSTRAINT.

LC 862, "Shortest Subarray with Sum at Least K", is the SAME SENTENCE with
`-10^5 <= nums[i]`. With negatives:

    * growing a window can DECREASE its sum, so an invalid window may become
      valid by extending — the upward-closure is gone;
    * a window whose sum is already >= target may contain a negative prefix
      whose removal makes a SHORTER valid window, but shrinking past it first
      makes the sum smaller, so the greedy `while` exits early.

Both failure modes lose real answers. The sliding window on LC 862 is not slow;
it is WRONG. The demo at the bottom of this file runs exactly this code on
random arrays containing negatives and shows it disagreeing with brute force on
a large fraction of them, with concrete counterexamples printed.

    LC 862 needs PREFIX SUMS + A MONOTONIC DEQUE, and it is rated Hard for
    that reason alone. `shortestSubarray_with_negatives` below implements it,
    so you can see what the correct algorithm looks like when the window dies.

    BEFORE WRITING ANY SUM-BASED WINDOW: READ THE SIGN CONSTRAINT.

The same fork appears elsewhere and is worth having ready:

    LC 209  positives, "sum >= target", shortest    -> sliding window   O(n)
    LC 862  negatives allowed, same question        -> prefix + deque   O(n)
    LC 560  negatives allowed, "sum == k", count    -> prefix + hashmap O(n)
    LC 325  negatives allowed, "sum == k", longest  -> prefix + hashmap O(n)

Notice that the moment negatives appear, the answer is always PREFIX SUMS
(topic 04) rather than a window. That is not a coincidence — prefix sums do not
care about monotonicity, because they never make an irreversible decision about
`l`.


================================================================================
THE O(n log n) FOLLOW-UP
================================================================================
The problem explicitly asks for it, so have it ready.

Because every value is positive, the prefix-sum array is STRICTLY INCREASING:

    pre[0] = 0,  pre[i+1] = pre[i] + nums[i],   pre strictly ascending

A subarray `nums[l..r]` sums to `pre[r+1] - pre[l]`. For a fixed right end
`r+1`, we want the LARGEST `l` with

    pre[r+1] - pre[l] >= target      <=>      pre[l] <= pre[r+1] - target

and since `pre` is sorted, that `l` is found by binary search — `bisect_right`
for the insertion point of `pre[r+1] - target`, minus one.

    O(n) prefix construction + O(n) searches x O(log n) = O(n log n),
    O(n) space.

WHY WOULD ANYONE WANT THE SLOWER ONE? Two honest reasons:

  1. It is the version that GENERALISES: if the array were fixed and you had to
     answer many different `target` queries, the prefix array is built once and
     each query is O(n log n) — or O(log n) per right end. The window has to
     restart from scratch every time.
  2. The sortedness of `pre` is itself a consequence of positivity. Saying "the
     binary search works because the prefix sums are increasing, which is the
     same property the window relies on" shows you understand that BOTH
     solutions rest on the same constraint. That is the insight the follow-up
     is fishing for.

⚠️  A common wrong answer: "binary search on the ANSWER LENGTH". That also
    works here (feasibility is monotone in the length) and is also O(n log n) —
    but it is a different algorithm from the one the follow-up intends, and it
    needs its own justification. `minSubArrayLen_bsearch_width` implements it.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(nums)

    Approach                            Time        Space  Note
    ----------------------------------  ----------  -----  --------------------
    Every subarray, recompute the sum   O(n^3)      O(1)
    Every start, running sum, break     O(n^2)      O(1)   the natural brute
    Prefix + binary search on `l`       O(n log n)  O(n)   the stated follow-up
    Prefix + binary search on the width O(n log n)  O(n)   a different route
    Sliding window ✅                   O(n)        O(1)   optimal

    ⚠️  The O(n^2) brute force can `break` out of the inner loop as soon as the
        sum reaches the target — extending further only makes the subarray
        longer. That prune is what makes it usable as a test oracle, and it is
        also a hint towards the window: it is the same "once valid, stop
        growing" observation, applied one start at a time.


================================================================================
EDGE CASES
================================================================================
    no subarray works    target=11, [1]*8 -> 0. `best` stays at infinity and
                         must be translated to 0. The single most common
                         failure: returning `inf`, or crashing on int(inf).

    the whole array      target=15, [1,2,3,4,5] -> 5. The window never shrinks
                         to anything smaller; the answer is found on the very
                         last iteration.

    one short of enough  target=16, [1,2,3,4,5] -> 0. Sits right next to the
                         case above; together they pin the `>=` vs `>` choice.

    single element hits  target=5, [1,1,1,1,10] -> 1 (the answer is the LAST
                         element)  and  target=5, [10,1,1,1,1] -> 1 (the
                         FIRST). Both are needed: one catches a loop that
                         stops early, the other a loop that starts late.

    n == 1               target=1, [1] -> 1;  target=2, [1] -> 0.

    exact equality       target=100, [10]*10 -> 10. `sum >= target` must accept
                         equality. Using `>` returns 0 here.

    huge target          target=10^9 with ten 10^4s -> 0. No overflow concern
                         in Python, but the sentinel path must still work.


================================================================================
COMMON MISTAKES
================================================================================
1. `best = 0` instead of `float('inf')`. `min` never moves off 0.

2. Returning `float('inf')` (or `int(inf)`, which raises) when nothing is
   found. The problem wants 0.

3. Shrinking before recording, so every recorded length is one too SMALL —
   and on [1,4,4] with target 4 it returns 0, colliding with the sentinel that
   means "no subarray exists".

4. `while total > target` instead of `>=`. Equality counts.

5. Using `if` instead of `while` for the shrink. Unlike problems 006/007, here
   the shrink genuinely must run many times in one iteration — a single large
   element can make many left positions valid at once. `if` silently returns
   answers that are too long.

6. Applying this template to a problem whose values can be negative. It is not
   a performance bug, it is a WRONG ANSWER. See the demo.

7. Recomputing `sum(nums[l:r+1])` in the loop. O(n^2), and it re-introduces the
   exact cost the window exists to remove.

8. Claiming O(n^2) because of the nested `while`. `l` advances at most n times
   in total: O(n).

9. For the follow-up, binary searching a prefix array WITHOUT noting that it is
   sorted only because the values are positive. That is the whole point of the
   follow-up.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: The O(n log n) version.
A: Prefix sums are strictly increasing (positivity), so for each right end
   binary search the furthest left end that still clears the target. Say WHY
   the array is sorted; that is the graded part.

Q: What if the values can be negative? (LC 862)
A: The window breaks — growing can shrink the sum, so `l += 1` discards live
   answers. Use prefix sums with a MONOTONIC DEQUE of increasing prefix values:
   pop from the front while `pre[r] - pre[dq[0]] >= target` (record and discard,
   since that left end can never be beaten by a later, longer one), and pop from
   the back while `pre[dq[-1]] >= pre[r]` (a larger-or-equal earlier prefix is
   dominated — it is both further away and less useful). O(n).

Q: Sum EXACTLY equal to target, shortest?
A: With positives, a window still works (shrink while `total > target`, check
   equality). With negatives, prefix sums + a hash map of first/last occurrence
   — LC 560 / LC 325.

Q: Return the subarray, not its length.
A: Track `best_l` when you record. Slice once at the end.

Q: Minimum size subarray with sum >= target in a CIRCULAR array?
A: Duplicate the array (length 2n) and cap the window width at n.

Q: The array is a stream and target is fixed.
A: The window is already online — it holds O(1) state — but you must buffer the
   window itself to subtract `nums[l]`, so O(window) memory.

Q: Many queries with different targets on a fixed array?
A: Build the prefix array once; each query is then O(n log n) with binary
   search, or O(log n) per right end. This is the honest reason to know the
   slower algorithm.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 862  Shortest Subarray with Sum ≥ K  — NEGATIVES: prefix + monotonic deque
    LC 560  Subarray Sum Equals K           — negatives, count: prefix + hashmap
    LC 325  Max Size Subarray Sum Equals k  — negatives, longest: prefix + hashmap
    LC 713  Subarray Product Less Than K    — the same shape over a PRODUCT
    LC 1004 Max Consecutive Ones III        — problem 006; the LONGEST mirror
    LC 76   Minimum Window Substring        — problem 015; shortest + have/need
    LC 1658 Minimum Operations to Reduce X  — this problem, complemented
================================================================================
"""

import random
import time
from bisect import bisect_right
from collections import deque
from typing import List


class Solution:
    def minSubArrayLen(self, target: int, nums: List[int]) -> int:
        """Shape C: shortest window with sum >= target. O(n) time, O(1) space.

        REQUIRES all values non-negative — see the module docstring.
        """
        l = 0
        total = 0
        best = float('inf')
        for r, x in enumerate(nums):
            total += x                                  # ENTER
            while total >= target:                      # while STILL VALID
                best = min(best, r - l + 1)             # RECORD, then
                total -= nums[l]                        # SHRINK
                l += 1
        return 0 if best == float('inf') else best

    # ------------------------------------------------------------------
    # The O(n log n) follow-ups.
    # ------------------------------------------------------------------
    def minSubArrayLen_bsearch(self, target: int, nums: List[int]) -> int:
        """Prefix sums + binary search for the left end. O(n log n), O(n).

        `pre` is STRICTLY INCREASING because every value is positive — that is
        the only reason a binary search is legal here.
        """
        n = len(nums)
        pre = [0] * (n + 1)
        for i, x in enumerate(nums):
            pre[i + 1] = pre[i] + x

        best = float('inf')
        for r in range(1, n + 1):
            # largest l with pre[l] <= pre[r] - target
            idx = bisect_right(pre, pre[r] - target, 0, r) - 1
            if idx >= 0:
                best = min(best, r - idx)
        return 0 if best == float('inf') else best

    def minSubArrayLen_bsearch_width(self, target: int, nums: List[int]) -> int:
        """Binary search on the ANSWER WIDTH. Also O(n log n).

        Feasibility is monotone in the width: if some window of width w reaches
        the target, so does some window of width w+1 (extend it — positivity
        again).
        """
        n = len(nums)
        pre = [0] * (n + 1)
        for i, x in enumerate(nums):
            pre[i + 1] = pre[i] + x

        def feasible(w: int) -> bool:
            return any(pre[i + w] - pre[i] >= target for i in range(n - w + 1))

        lo, hi, ans = 1, n, 0
        while lo <= hi:
            mid = (lo + hi) // 2
            if feasible(mid):
                ans, hi = mid, mid - 1
            else:
                lo = mid + 1
        return ans

    def minSubArrayLen_brute(self, target: int, nums: List[int]) -> int:
        """O(n^2) oracle. Breaks early: once valid, extending only lengthens."""
        best = float('inf')
        for i in range(len(nums)):
            total = 0
            for j in range(i, len(nums)):
                total += nums[j]
                if total >= target:
                    best = min(best, j - i + 1)
                    break
        return 0 if best == float('inf') else best

    # ------------------------------------------------------------------
    # LC 862 — what you must write instead when negatives are allowed.
    # ------------------------------------------------------------------
    def shortestSubarray_with_negatives(self, target: int, nums: List[int]) -> int:
        """LC 862: shortest subarray with sum >= target, NEGATIVES ALLOWED.

        Prefix sums + a monotonic deque of INCREASING prefix values. O(n).

        Two pops, each with its own reason:
          * front: if pre[r] - pre[dq[0]] >= target, that left end is used and
            then DISCARDED — any later right end paired with it would only be
            longer.
          * back: if pre[dq[-1]] >= pre[r], the older prefix is DOMINATED — it
            is both further left (longer subarrays) and no smaller (weaker
            sums), so it can never win.
        """
        n = len(nums)
        pre = [0] * (n + 1)
        for i, x in enumerate(nums):
            pre[i + 1] = pre[i] + x

        best = float('inf')
        dq = deque()                       # indices into pre, pre values increasing
        for r in range(n + 1):
            while dq and pre[r] - pre[dq[0]] >= target:
                best = min(best, r - dq.popleft())
            while dq and pre[dq[-1]] >= pre[r]:
                dq.pop()
            dq.append(r)
        return 0 if best == float('inf') else best

    # ------------------------------------------------------------------
    # Deliberate breakages.
    # ------------------------------------------------------------------
    def minSubArrayLen_shrink_first(self, target: int, nums: List[int]) -> int:
        """✗ BROKEN — shrinks before recording. `l` has already advanced, so
        every recorded length is one too SMALL."""
        l = 0
        total = 0
        best = float('inf')
        for r, x in enumerate(nums):
            total += x
            while total >= target:
                total -= nums[l]
                l += 1
                best = min(best, r - l + 1)      # measured AFTER shrinking
        return 0 if best == float('inf') else best

    def minSubArrayLen_if_not_while(self, target: int, nums: List[int]) -> int:
        """✗ BROKEN — shrinks at most once per step, so it never reaches the
        shortest window when one big element makes many left ends valid."""
        l = 0
        total = 0
        best = float('inf')
        for r, x in enumerate(nums):
            total += x
            if total >= target:
                best = min(best, r - l + 1)
                total -= nums[l]
                l += 1
        return 0 if best == float('inf') else best


# ==============================================================================
# TESTS — run:  python 008_minimum_size_subarray_sum_solution.py
# ==============================================================================
CASES = [
    (7, [2, 3, 1, 2, 4, 3]), (4, [1, 4, 4]), (11, [1] * 8),
    (11, [1, 2, 3, 4, 5]), (15, [1, 2, 3, 4, 5]), (16, [1, 2, 3, 4, 5]),
    (1, [1]), (2, [1]), (5, [5]), (5, [1, 1, 1, 1, 10]), (5, [10, 1, 1, 1, 1]),
    (100, [10] * 10), (3, [1, 1, 1, 1, 1]),
    (213, [12, 28, 83, 4, 25, 26, 25, 2, 25, 6]), (10 ** 9, [10 ** 4] * 10),
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("sliding window O(n)     ", sol.minSubArrayLen),
        ("prefix + bsearch on l   ", sol.minSubArrayLen_bsearch),
        ("prefix + bsearch on width", sol.minSubArrayLen_bsearch_width),
        ("LC862 prefix + deque    ", sol.shortestSubarray_with_negatives),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(t, list(a)) == sol.minSubArrayLen_brute(t, a) for t, a in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Randomised cross-check on POSITIVE input.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle (positives) ---")
    random.seed(209)
    trials, mismatches = 5000, 0
    for _ in range(trials):
        a = [random.randint(1, 12) for _ in range(random.randint(1, 14))]
        t = random.randint(1, 40)
        want = sol.minSubArrayLen_brute(t, a)
        for _, fn in impls:
            if fn(t, list(a)) != want:
                mismatches += 1
    print(f"  {trials} random (target, array) x {len(impls)} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The window, traced.
    # ----------------------------------------------------------------------
    target, nums = 7, [2, 3, 1, 2, 4, 3]
    print(f"\n--- Shape C on target={target}, {nums} ---")
    print(f"  {'r':>2} {'x':>2} {'total':>6} {'l':>2} {'window':>18}"
          f" {'len':>4} {'best':>5}  action")
    l, total, best = 0, 0, float('inf')
    for r, x in enumerate(nums):
        total += x
        if total < target:
            print(f"  {r:>2} {x:>2} {total:>6} {l:>2} {str(nums[l:r+1]):>18} "
                  f"{r-l+1:>4} {str(best):>5}  grow (sum < target)")
        while total >= target:
            best = min(best, r - l + 1)
            print(f"  {r:>2} {x:>2} {total:>6} {l:>2} {str(nums[l:r+1]):>18} "
                  f"{r-l+1:>4} {best:>5}  RECORD then shrink")
            total -= nums[l]
            l += 1
    print(f"  answer = {best}")

    # ----------------------------------------------------------------------
    # ⚠️  THE SIGN CONSTRAINT — the window is WRONG with negatives.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the SAME code on arrays containing NEGATIVES (LC 862) ---")

    def brute_neg(target, nums):
        best = float('inf')
        for i in range(len(nums)):
            total = 0
            for j in range(i, len(nums)):
                total += nums[j]
                if total >= target:
                    best = min(best, j - i + 1)
        return 0 if best == float('inf') else best

    random.seed(862)
    trials, wrong, examples = 4000, 0, []
    for _ in range(trials):
        a = [random.randint(-6, 6) for _ in range(random.randint(1, 10))]
        t = random.randint(1, 12)
        want = brute_neg(t, a)
        got = sol.minSubArrayLen(t, list(a))
        if got != want:
            wrong += 1
            if len(examples) < 4:
                examples.append((t, a, want, got))
    print(f"  sliding window vs brute force on {trials} arrays WITH negatives:")
    print(f"    {wrong} wrong answers ({100 * wrong / trials:.1f}%)")
    print(f"  {'target':>7} {'array':<34} {'correct':>8} {'window':>7}")
    for t, a, want, got in examples:
        print(f"  {t:>7} {str(a):<34} {want:>8} {got:>7}")
    print("  Not slow — WRONG. Growing a window can now DECREASE its sum, so")
    print("  `l += 1` throws away subarrays that were still reachable.")

    print("\n  The correct O(n) algorithm for negatives (prefix + monotonic deque):")
    ok_neg = True
    for _ in range(4000):
        a = [random.randint(-6, 6) for _ in range(random.randint(1, 10))]
        t = random.randint(1, 12)
        if sol.shortestSubarray_with_negatives(t, list(a)) != brute_neg(t, a):
            ok_neg = False
    print(f"    {'PASS' if ok_neg else 'FAIL'} — agrees with brute force on "
          f"4000 arrays containing negatives")
    all_ok &= ok_neg
    print("  Note it needs NO sign assumption: prefix sums never make an")
    print("  irreversible decision about `l`, which is exactly what the window")
    print("  does and cannot justify once monotonicity is gone.")

    # ----------------------------------------------------------------------
    # ⚠️  Order of record and shrink; `if` vs `while`.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  record-then-shrink, and why the shrink must be a `while` ---")
    print(f"  {'target':>7} {'array':<44} {'correct':>8} {'shrink 1st':>11}"
          f" {'if not while':>13}")
    for t, a in (4, [1, 4, 4]), (7, [2, 3, 1, 2, 4, 3]), (5, [1, 1, 1, 1, 10]), \
                (11, [1, 2, 3, 4, 5]), (100, [10] * 10):
        print(f"  {t:>7} {str(a):<44} {sol.minSubArrayLen(t, list(a)):>8} "
              f"{sol.minSubArrayLen_shrink_first(t, list(a)):>11} "
              f"{sol.minSubArrayLen_if_not_while(t, list(a)):>13}")
    print("  shrink-first records AFTER `l` moved, so every length is one too")
    print("  SMALL — note it even returns 0, which is the 'not found' sentinel.")
    print("  `if` stops after one eviction, so when a single big element makes")
    print("  many left ends valid at once it never reaches the shortest.")

    # ----------------------------------------------------------------------
    # Why the prefix array is searchable: positivity again.
    # ----------------------------------------------------------------------
    print("\n--- why the O(n log n) follow-up is legal ---")
    pos = [2, 3, 1, 2, 4, 3]
    neg = [2, -3, 1, 2, -4, 3]
    for label, arr in (("all positive", pos), ("with negatives", neg)):
        pre = [0]
        for x in arr:
            pre.append(pre[-1] + x)
        sorted_ok = all(pre[i] < pre[i + 1] for i in range(len(pre) - 1))
        print(f"  {label:<16} nums={str(arr):<26} pre={pre}")
        print(f"  {'':<16} strictly increasing? {sorted_ok}"
              f"{'' if sorted_ok else '   <- binary search is ILLEGAL here'}")
    print("  The binary search and the sliding window rest on the SAME property.")
    print("  When positivity goes, both go — which is why LC 862 is a Hard.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n log n) vs O(n^2).
    # ----------------------------------------------------------------------
    print("\n--- window vs binary search vs brute force ---")
    print(f"  {'n':>7} {'window O(n)':>13} {'bsearch O(nlogn)':>17} "
          f"{'brute O(n^2)':>14}")
    random.seed(0)
    for n in (5_000, 10_000, 20_000):
        a = [random.randint(1, 100) for _ in range(n)]
        t = 50 * 40
        t0 = time.perf_counter(); sol.minSubArrayLen(t, a)
        t1 = time.perf_counter(); sol.minSubArrayLen_bsearch(t, a)
        t2 = time.perf_counter(); sol.minSubArrayLen_brute(t, a)
        t3 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>11.1f}ms {(t2 - t1) * 1000:>15.1f}ms "
              f"{(t3 - t2) * 1000:>12.1f}ms")
    print("  The brute force looks fast here only because it BREAKS as soon as")
    print("  the target is met; on data where the target is barely reachable it")
    print("  degrades to the full O(n^2).")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
