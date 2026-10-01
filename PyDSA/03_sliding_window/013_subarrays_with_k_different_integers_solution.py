"""
================================================================================
SOLUTION · LeetCode 992 · Subarrays with K Different Integers             [Hard]
https://leetcode.com/problems/subarrays-with-k-different-integers/
================================================================================

THE CORE IDEA
-------------
This Hard is a COMPOSITION of two Mediums you have already done:

    problem 009 (Fruit Into Baskets)  ->  the "at most K distinct" window,
                                          with `del count[x]` on zero
    problem 012 (Binary Subarrays)    ->  `count += r - l + 1`, and
                                          exactly(k) = atMost(k) - atMost(k-1)

    def atMostK(k):
        if k < 0: return 0
        count = Counter()
        l = res = 0
        for r, x in enumerate(nums):
            count[x] += 1                       # ENTER
            while len(count) > k:               # RESTORE
                out = nums[l]
                count[out] -= 1
                if count[out] == 0:
                    del count[out]              # or len() lies and this hangs
                l += 1
            res += r - l + 1                    # RECORD: subarrays ending at r
        return res

    return atMostK(k) - atMostK(k - 1)

O(n) time (two linear passes), O(k) space.

Nothing here is new. The difficulty is entirely in SEEING the decomposition —
which is why it is worth doing 009 and 012 first, and why the right thing to
say in an interview is *"exactly-k isn't a window, but at-most-k is, and
exactly = atMost(k) − atMost(k−1)"* before writing a single line.


================================================================================
WHY "EXACTLY k" IS NOT A WINDOW — the band argument
================================================================================
A sliding window can only track a property whose valid left endpoints, for a
fixed right endpoint, form a SUFFIX of [0, r] — one boundary, one pointer.

Fix r = 4 in nums = [1,2,1,2,3], k = 2:

        l=0  [1,2,1,2,3]   3 distinct   invalid
        l=1    [2,1,2,3]   3 distinct   invalid
        l=2      [1,2,3]   3 distinct   invalid
        l=3        [2,3]   2 distinct   VALID    <-+
        l=4          [3]   1 distinct   invalid    |  a BAND, not a suffix

    "at most 2":  invalid invalid invalid VALID VALID    <- one boundary ✅
    "exactly 2":  invalid invalid invalid VALID invalid  <- two boundaries ✗

One pointer cannot describe a band. Two at-most counts can:

        {exactly k}  =  {at most k}  MINUS  {at most k-1}

and each side of that subtraction is a single-boundary window.

    [1,2,1,2,3], k = 2:   atMostK(2) = 12,  atMostK(1) = 5,  12 - 5 = 7  ✓

⚠️  `atMostK(0)` must be 0 — there are no non-empty subarrays with zero
    distinct values. The code above gets this right without a special case:
    with k = 0 the `while len(count) > 0` loop empties the window entirely, so
    `l` ends at `r + 1` and `r - l + 1` is 0. Verify it rather than trusting
    it; the `if k < 0: return 0` guard is still worth keeping for symmetry with
    problem 012 and to make the intent explicit.


================================================================================
⚠️  `del` ON ZERO — the line that makes the loop terminate
================================================================================
`len(count)` gates the `while`. A Counter retains keys whose value has fallen
to 0:

    >>> c = Counter([1, 2]); c[2] -= 1; len(c)
    2                     # 2 is gone from the window but still a key

Without the `del`, `len(count)` never decreases, `while len(count) > k` never
becomes false, and `l` marches past the end of the array — IndexError. This is
not a subtle wrongness; the program crashes. Problem 009 has the full
demonstration; the test suite here reproduces it.

And the companion rule: use `Counter`, not `defaultdict(int)`, whenever `len()`
of the map is part of a loop condition. Reading a missing key from a
`defaultdict` INSERTS it, silently inflating `len()`.


================================================================================
THE ONE-PASS VARIANT
================================================================================
As in problem 012, the two passes fuse into one by carrying two left pointers:

    l_lo = smallest l with (distinct in nums[l..r]) <= k
    l_hi = smallest l with (distinct in nums[l..r]) <= k-1
    ans += l_hi - l_lo

Each needs its own Counter. It is one pass, still O(n), and it is a good answer
to "can you avoid two passes?" — but it doubles the bookkeeping, and the
two-pass version is the one to write first.

An equivalent and often-cited formulation keeps ONE counter plus a `left_far`
pointer that counts how many left positions can be trimmed while the window
still has exactly k distinct values. Same idea, same result; the two-pointer
framing is easier to justify because each pointer is just an `atMostK` window
you already trust.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(nums)

    Approach                          Time      Space   Note
    --------------------------------  --------  ------  --------------------
    Every subarray, growing a set     O(n^2)    O(k)    4e8 ops at n=2e4
    atMostK(k) - atMostK(k-1) ✅      O(n)      O(k)    two passes
    One pass, two Counters ✅         O(n)      O(k)    same O, fiddlier

    SPACE IS O(k), NOT O(n). The `while` restores `len(count) <= k` before each
    record, so the Counter holds at most k+1 keys at any instant — regardless
    of how many distinct values the array contains. Saying O(n) here suggests
    you have not noticed the bound the loop maintains.

    ⚠️  The ANSWER can be Θ(n²) — [1,1,...,1] with k=1 gives n(n+1)/2, about
        2 x 10^8 at the constraint limit. Python integers handle it; C++/Java
        need 64-bit.


================================================================================
EDGE CASES
================================================================================
    k = 1             [1,1,1,1] -> 10 = 4*5/2. Every subarray of a constant
                      array is good. Tests the counting substitution at its
                      most extreme.

    k = 1, all distinct  [1,2,3,4] -> 4. One per element, nothing longer.

    k = n distinct    [1,2,3,4] with k=4 -> 1. Only the whole array.

    k > distinct      [1,2,3,4] with k=5 -> 0, and [5,5,5] with k=2 -> 0.
                      atMostK(k) and atMostK(k-1) are then EQUAL (both count
                      every subarray), so the difference is 0. A nice check
                      that the identity degrades gracefully.

    n == 1            [1] with k=1 -> 1.

    only two values   [1,2,1,2,1] with k=2 -> 10: every subarray of length >= 2.
                      Total subarrays 15, minus the 5 singletons.

    ⚠️  There is no k = 0 case (constraint `1 <= k`), but `atMostK(0)` is
        exercised internally whenever k = 1. It must return 0.


================================================================================
COMMON MISTAKES
================================================================================
1. Trying to slide a window for "exactly k" directly. It is a band, not a
   suffix. Recognising this in the first minute is the whole problem.

2. Omitting `del count[x]` when the count hits 0. Infinite shrink -> IndexError.

3. `defaultdict(int)` where `len()` gates the loop — a read of a missing key
   inserts a phantom.

4. `res += 1` instead of `res += r - l + 1`. Counts right endpoints, not
   subarrays.

5. `atMostK(k) - atMostK(k+1)`, or subtracting in the wrong order. The result
   goes negative, which is an immediate signal you have it backwards.

6. Trying to adapt the trick to the LONGEST subarray with exactly k distinct.
   You cannot subtract lengths — `longest(≤k) − longest(≤k−1)` is meaningless.
   Counts subtract; extrema do not. This is the most instructive trap in the
   problem.

7. Reporting O(n) space for the Counter. It is O(k).

8. Recomputing `len(set(nums[l:r+1]))` inside the loop. O(n^2) and it discards
   the incremental structure entirely.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: One pass instead of two?
A: Two left pointers, `l_lo` for `<= k` and `l_hi` for `<= k-1`; add
   `l_hi - l_lo` per step. Same subtraction done pointwise.

Q: The LONGEST subarray with exactly k distinct integers?
A: The at-most trick does NOT transfer — you cannot subtract maxima. Instead
   note that for each right end r, the longest exactly-k window ending at r
   starts at `l_lo` (the smallest l with <= k distinct) PROVIDED the window
   there has exactly k distinct; take the max over r. One pass, one Counter.
   Being able to explain why the subtraction fails here is worth more than the
   code.

Q: Exactly k distinct in a STREAM?
A: Both windows are online in O(k) state, but you must buffer the window itself
   to evict from the left, so O(window) memory.

Q: At most k distinct with the added rule that each value may appear at most
   m times (LC 2958)?
A: Two hereditary conditions on the same window — restore both in the same
   `while`: `while len(count) > k or count[x] > m:`. Heredity is closed under
   conjunction, which is why this composes so cleanly.

Q: Why is the space O(k) and not O(number of distinct values)?
A: Because the `while` restores `len(count) <= k` before each record, so the
   map is bounded by k+1 entries at every observable moment.

Q: How big can the answer be?
A: Θ(n²) — n(n+1)/2 for a constant array with k=1.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 930  Binary Subarrays With Sum        — problem 012; the same identity
    LC 904  Fruit Into Baskets               — problem 009; atMost(2) distinct
    LC 340  Longest Substring with At Most   — the LENGTH version of atMostK
            K Distinct Characters
    LC 1248 Count Number of Nice Subarrays   — "exactly k odd" = same trick
    LC 2062 Count Vowel Substrings           — exactly 5 distinct vowels
    LC 2958 Length of Longest Subarray With  — two hereditary conditions
            at Most K Frequency
    LC 560  Subarray Sum Equals K            — the prefix-map cousin
================================================================================
"""

import random
import time
from collections import Counter
from typing import List


class Solution:
    def subarraysWithKDistinct(self, nums: List[int], k: int) -> int:
        """exactly(k) = atMost(k) - atMost(k-1). O(n) time, O(k) space."""
        return self._at_most_k(nums, k) - self._at_most_k(nums, k - 1)

    @staticmethod
    def _at_most_k(nums: List[int], k: int) -> int:
        """Number of subarrays with AT MOST k distinct values."""
        if k < 0:
            return 0
        count = Counter()
        l = res = 0
        for r, x in enumerate(nums):
            count[x] += 1                          # ENTER
            while len(count) > k:                  # RESTORE
                out = nums[l]
                count[out] -= 1
                if count[out] == 0:
                    del count[out]                 # keep len() == distinct
                l += 1
            res += r - l + 1                       # subarrays ENDING at r
        return res

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def subarraysWithKDistinct_one_pass(self, nums: List[int], k: int) -> int:
        """One pass with two left pointers and two Counters.

        l_lo = smallest l with distinct(nums[l..r]) <= k
        l_hi = smallest l with distinct(nums[l..r]) <= k-1
        The subarrays ending at r with EXACTLY k distinct number l_hi - l_lo.
        """
        c_lo, c_hi = Counter(), Counter()
        l_lo = l_hi = ans = 0
        for r, x in enumerate(nums):
            c_lo[x] += 1
            while len(c_lo) > k:
                out = nums[l_lo]
                c_lo[out] -= 1
                if c_lo[out] == 0:
                    del c_lo[out]
                l_lo += 1

            c_hi[x] += 1
            while len(c_hi) > k - 1:
                out = nums[l_hi]
                c_hi[out] -= 1
                if c_hi[out] == 0:
                    del c_hi[out]
                l_hi += 1

            ans += l_hi - l_lo
        return ans

    def longestWithKDistinct(self, nums: List[int], k: int) -> int:
        """Follow-up: the LONGEST subarray with EXACTLY k distinct.

        The at-most SUBTRACTION does not transfer — you cannot subtract
        maxima. But `l_lo` (the smallest l with <= k distinct) already gives
        the longest candidate ending at r; just check it really has k.
        """
        count = Counter()
        l = best = 0
        for r, x in enumerate(nums):
            count[x] += 1
            while len(count) > k:
                out = nums[l]
                count[out] -= 1
                if count[out] == 0:
                    del count[out]
                l += 1
            if len(count) == k:                    # only then is it a witness
                best = max(best, r - l + 1)
        return best

    def subarraysWithKDistinct_brute(self, nums: List[int], k: int) -> int:
        """O(n^2) oracle."""
        count = 0
        for i in range(len(nums)):
            seen = set()
            for j in range(i, len(nums)):
                seen.add(nums[j])
                if len(seen) == k:
                    count += 1
                elif len(seen) > k:
                    break
        return count

    # ------------------------------------------------------------------
    # Deliberate breakages.
    # ------------------------------------------------------------------
    @staticmethod
    def _at_most_k_no_del(nums: List[int], k: int) -> int:
        """✗ BROKEN — no `del`, so `len(count)` never falls and the `while`
        cannot exit. `l` runs off the end -> IndexError."""
        count = Counter()
        l = res = 0
        for r, x in enumerate(nums):
            count[x] += 1
            while len(count) > k:
                count[nums[l]] -= 1                # nothing is ever deleted
                l += 1
            res += r - l + 1
        return res

    def subarraysWithKDistinct_no_del(self, nums: List[int], k: int) -> int:
        """✗ BROKEN — see above."""
        return (self._at_most_k_no_del(nums, k)
                - self._at_most_k_no_del(nums, k - 1))

    def subarraysWithKDistinct_count_one(self, nums: List[int], k: int) -> int:
        """✗ BROKEN — `res += 1` counts right ENDPOINTS, not subarrays."""
        def at_most(kk):
            if kk < 0:
                return 0
            count = Counter()
            l = res = 0
            for r, x in enumerate(nums):
                count[x] += 1
                while len(count) > kk:
                    out = nums[l]
                    count[out] -= 1
                    if count[out] == 0:
                        del count[out]
                    l += 1
                res += 1                           # should be r - l + 1
            return res
        return at_most(k) - at_most(k - 1)

    def subarraysWithKDistinct_wrong_order(self, nums: List[int], k: int) -> int:
        """✗ BROKEN — subtracts the wrong way round; the result goes negative."""
        return self._at_most_k(nums, k - 1) - self._at_most_k(nums, k)


# ==============================================================================
# TESTS — run:  python 013_subarrays_with_k_different_integers_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 1, 2, 3], 2), ([1, 2, 1, 3, 4], 3), ([1], 1), ([1, 1, 1, 1], 1),
    ([1, 2, 3, 4], 1), ([1, 2, 3, 4], 4), ([1, 2, 3, 4], 5), ([1, 1, 2, 2], 2),
    ([2, 1, 1, 1, 2], 2), ([1, 2, 1, 2, 1], 2), ([5, 5, 5], 2), ([1, 2], 2),
    ([1, 2, 3, 1, 2, 3], 3), ([4, 4, 4, 4], 1),
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("atMost(k) - atMost(k-1)", sol.subarraysWithKDistinct),
        ("one pass, two pointers ", sol.subarraysWithKDistinct_one_pass),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(a), k) == sol.subarraysWithKDistinct_brute(a, k)
                 for a, k in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    def brute_longest(a, k):
        best = 0
        for i in range(len(a)):
            seen = set()
            for j in range(i, len(a)):
                seen.add(a[j])
                if len(seen) == k:
                    best = max(best, j - i + 1)
                elif len(seen) > k:
                    break
        return best
    ok = all(sol.longestWithKDistinct(list(a), k) == brute_longest(a, k)
             for a, k in CASES)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  LONGEST-with-exactly-k follow-up")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(992)
    trials, mismatches = 6000, 0
    for _ in range(trials):
        a = [random.randint(1, 4) for _ in range(random.randint(1, 14))]
        k = random.randint(1, 5)
        want = sol.subarraysWithKDistinct_brute(a, k)
        for _, fn in impls:
            if fn(list(a), k) != want:
                mismatches += 1
        if sol.longestWithKDistinct(list(a), k) != brute_longest(a, k):
            mismatches += 1
    print(f"  {trials} random (array, k) x {len(impls) + 1} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Why "exactly k" is a BAND, not a suffix.
    # ----------------------------------------------------------------------
    nums, k = [1, 2, 1, 2, 3], 2
    r = 4
    print(f"\n--- why 'exactly {k} distinct' is not a window ---")
    print(f"  nums = {nums}, fix the right end at r = {r}:")
    print(f"  {'l':>3} {'subarray':>18} {'distinct':>9} {'== k?':>7} {'<= k?':>7}")
    for l in range(r + 1):
        sub = nums[l:r + 1]
        d = len(set(sub))
        print(f"  {l:>3} {str(sub):>18} {d:>9} {str(d == k):>7} "
              f"{str(d <= k):>7}")
    print("  '<= k' is False...False,True,True  — ONE boundary, one pointer ✅")
    print("  '== k' is False...False,True,False — a BAND. No single `l` can")
    print("  describe it, which is exactly why the subtraction exists.")

    # ----------------------------------------------------------------------
    # The subtraction.
    # ----------------------------------------------------------------------
    print(f"\n--- exactly(k) = atMostK(k) - atMostK(k-1) on {nums} ---")
    print(f"  {'k':>3} {'atMostK(k)':>11} {'atMostK(k-1)':>13} "
          f"{'difference':>11} {'brute':>7}")
    for kk in range(1, 5):
        a1 = sol._at_most_k(nums, kk)
        a0 = sol._at_most_k(nums, kk - 1)
        print(f"  {kk:>3} {a1:>11} {a0:>13} {a1 - a0:>11} "
              f"{sol.subarraysWithKDistinct_brute(nums, kk):>7}")
    print(f"  and atMostK(0) = {sol._at_most_k(nums, 0)} — no non-empty subarray")
    print("  has zero distinct values, and the code gets that with no special")
    print("  case: the while-loop empties the window, so r - l + 1 is 0.")

    # ----------------------------------------------------------------------
    # ⚠️  The `del`.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  without `del count[x]` the loop cannot terminate ---")
    c = Counter([1, 2])
    c[2] -= 1
    print(f"  Counter([1,2]) after c[2] -= 1  ->  {dict(c)}, len = {len(c)}")
    print("  The key survives at value 0, so `len(count) > k` stays true.")
    try:
        sol.subarraysWithKDistinct_no_del([1, 2, 1, 2, 3], 2)
        print("  (no exception — unexpected)")
    except IndexError as e:
        print(f"  subarraysWithKDistinct_no_del([1,2,1,2,3], 2) -> IndexError: {e}")
    print(f"  with the del: {sol.subarraysWithKDistinct([1, 2, 1, 2, 3], 2)}")

    # ----------------------------------------------------------------------
    # ⚠️  The two counting bugs.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `res += 1`, and subtracting the wrong way round ---")
    print(f"  {'input':<24} {'k':>2} {'correct':>8} {'res += 1':>9} "
          f"{'reversed':>9}")
    for a, kk in ([1, 2, 1, 2, 3], 2), ([1, 1, 1, 1], 1), ([1, 2, 1, 3, 4], 3), \
                 ([1, 2, 1, 2, 1], 2):
        print(f"  {str(a):<24} {kk:>2} "
              f"{sol.subarraysWithKDistinct(list(a), kk):>8} "
              f"{sol.subarraysWithKDistinct_count_one(list(a), kk):>9} "
              f"{sol.subarraysWithKDistinct_wrong_order(list(a), kk):>9}")
    print("  `res += 1` counts RIGHT ENDPOINTS. A reversed subtraction goes")
    print("  NEGATIVE — an immediate tell that the order is wrong.")

    # ----------------------------------------------------------------------
    # ⚠️  Why the trick does NOT transfer to lengths.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  counts subtract; MAXIMA do not ---")

    def longest_at_most(a, kk):
        if kk < 0:
            return 0
        count = Counter()
        l = best = 0
        for r, x in enumerate(a):
            count[x] += 1
            while len(count) > kk:
                out = a[l]
                count[out] -= 1
                if count[out] == 0:
                    del count[out]
                l += 1
            best = max(best, r - l + 1)
        return best

    print(f"  {'input':<24} {'k':>2} {'true longest':>13} "
          f"{'Lmax(k)-Lmax(k-1)':>19}")
    for a, kk in ([1, 2, 1, 2, 3], 2), ([1, 1, 1, 1], 1), ([1, 2, 3, 1, 2, 3], 3), \
                 ([1, 2, 1, 2, 1], 2):
        naive = longest_at_most(a, kk) - longest_at_most(a, kk - 1)
        print(f"  {str(a):<24} {kk:>2} {brute_longest(a, kk):>13} {naive:>19}")
    print("  Subtracting maxima is meaningless. For lengths, take the window at")
    print("  l_lo and check `len(count) == k` before recording — that is what")
    print("  `longestWithKDistinct` does, and it agrees with brute force.")

    # ----------------------------------------------------------------------
    # The Counter is bounded by k+1.
    # ----------------------------------------------------------------------
    print("\n--- the Counter holds at most k+1 keys, whatever n is ---")
    print(f"  {'k':>3} {'n':>8} {'distinct in array':>19} {'peak len(count)':>17}")
    random.seed(3)
    for kk in (1, 2, 5):
        a = [random.randint(1, 500) for _ in range(30_000)]
        count = Counter()
        l = peak = 0
        for r, x in enumerate(a):
            count[x] += 1
            peak = max(peak, len(count))
            while len(count) > kk:
                out = a[l]
                count[out] -= 1
                if count[out] == 0:
                    del count[out]
                l += 1
        print(f"  {kk:>3} {len(a):>8} {len(set(a)):>19} {peak:>17}")
    print("  So the space is O(k), NOT O(n) and not O(distinct values).")

    # ----------------------------------------------------------------------
    # The answer can be quadratic.
    # ----------------------------------------------------------------------
    print("\n--- the ANSWER can be quadratic ---")
    print(f"  {'n':>7} {'[x]*n with k=1':>17} {'= n(n+1)/2':>12}")
    for n in (4, 100, 20_000):
        print(f"  {n:>7} {sol.subarraysWithKDistinct([7] * n, 1):>17} "
              f"{n * (n + 1) // 2:>12}")

    # ----------------------------------------------------------------------
    # O(n) vs O(n^2).
    # ----------------------------------------------------------------------
    print("\n--- two windows vs every subarray ---")
    print(f"  {'n':>7} {'atMost x2':>11} {'one pass':>10} {'brute O(n^2)':>14}")
    random.seed(0)
    for n in (2_000, 4_000, 8_000):
        a = [random.randint(1, 10) for _ in range(n)]
        kk = 5
        t0 = time.perf_counter(); sol.subarraysWithKDistinct(a, kk)
        t1 = time.perf_counter(); sol.subarraysWithKDistinct_one_pass(a, kk)
        t2 = time.perf_counter(); sol.subarraysWithKDistinct_brute(a, kk)
        t3 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>9.1f}ms {(t2 - t1) * 1000:>8.1f}ms "
              f"{(t3 - t2) * 1000:>12.1f}ms")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
