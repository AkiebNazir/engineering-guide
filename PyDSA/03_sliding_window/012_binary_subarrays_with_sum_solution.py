"""
================================================================================
SOLUTION · LeetCode 930 · Binary Subarrays With Sum                     [Medium]
https://leetcode.com/problems/binary-subarrays-with-sum/
================================================================================

THE CORE IDEA
-------------
Two moves, each reusable far beyond this problem.

    1. COUNT with a window:      count += r - l + 1     (instead of a max)
    2. EXACTLY from AT-MOST:     exactly(g) = atMost(g) - atMost(g - 1)

    def atMost(k):
        if k < 0: return 0                      # <- the goal == 0 guard
        l = total = count = 0
        for r, x in enumerate(nums):
            total += x                          # ENTER
            while total > k:                    # RESTORE  (sum <= k)
                total -= nums[l]; l += 1
            count += r - l + 1                  # RECORD: subarrays ending at r
        return count

    return atMost(goal) - atMost(goal - 1)

O(n) time (two linear passes), O(1) space.


================================================================================
MOVE 1 · THE COUNTING SUBSTITUTION — why `r - l + 1` is the right number
================================================================================
After the restore step, `l` is the SMALLEST index such that `nums[l..r]` is
valid. Consider the subarrays that END at r:

    nums[l..r], nums[l+1..r], ..., nums[r..r]        <- r - l + 1 of them
    nums[l-1..r], nums[l-2..r], ...                  <- all INVALID

Why is the first group entirely valid? Because the property is HEREDITARY:
`nums[l..r]` is valid, and every one of those subarrays is a suffix of it, so
each has a sum no larger. Why is the second group entirely invalid? Because `l`
was minimal — anything starting earlier includes `nums[l-1..r]`, whose sum is
already over k.

So the count of valid subarrays ending at r is exactly `r - l + 1`, and summing
that over all r counts every valid subarray exactly once (each is counted at
its own right endpoint).

    THIS IS THE SAME `r - l + 1` AS THE LENGTH FORMULA.
    In a longest-window problem it is a WIDTH; here it is a COUNT of suffixes.
    They coincide because a window of width w has exactly w suffixes.

Every Shape-B window in this folder becomes a counter by that one substitution.


================================================================================
MOVE 2 · WHY "EXACTLY" NEEDS TWO WINDOWS
================================================================================
    "sum <= k"      HEREDITARY ✅    dropping a 0/1 element cannot raise a sum
    "sum == goal"   NOT hereditary ✗ shrink a window summing to 2 and you land
                                     on 1 — valid, then invalid, then valid...

Heredity is what guarantees the set of valid left endpoints for a fixed r is a
contiguous SUFFIX of [0, r] — a single boundary `l`. For "exactly", the valid
left endpoints are scattered, so there is no boundary to maintain and the
window has nothing to slide.

Inclusion-exclusion repairs it:

    {sum == goal}  =  {sum <= goal}  MINUS  {sum <= goal - 1}
    exactly(goal)  =  atMost(goal)    -      atMost(goal - 1)

Both halves are hereditary, so both are ordinary counting windows.

    nums = [1,0,1,0,1], goal = 2
        atMost(2) = 14,  atMost(1) = 10,  exactly = 4  ✓

⚠️  THE goal == 0 TRAP. You need `atMost(-1)`, which must be 0. Without the
    `if k < 0: return 0` guard, the `while total > k` loop can never be
    satisfied once any 1 enters (a sum is never < 0... in fact `total > -1` is
    true even for total = 0), so `l` runs off the end and you get an IndexError
    or a garbage count. Test [0,0,0,0,0] with goal 0 -> 15.

⚠️  This identity is a TEMPLATE, not a fact about binary arrays:
        exactly K distinct       = atMost(K) - atMost(K-1)      (LC 992)
        exactly K odd numbers    = atMost(K) - atMost(K-1)      (LC 1248)
        exactly K ones           = this problem
    Anything of the form "exactly K of something countable and monotone".


================================================================================
THE OTHER SOLUTION: PREFIX SUMS + HASH MAP
================================================================================
    seen = {0: 1}                    # one empty prefix, sum 0
    p = ans = 0
    for x in nums:
        p += x
        ans += seen.get(p - goal, 0) # how many earlier prefixes make the gap
        seen[p] = seen.get(p, 0) + 1
    return ans

One pass, O(n) time, O(n) space. This is the LC 560 technique.

WHICH IS BETTER? They are both O(n), so the comparison is about robustness:

    window     O(1) space, but REQUIRES non-negative values (heredity)
    prefix map O(n) space, works with NEGATIVE values too

For a binary array either is fine. The moment the array can contain negatives,
`atMost` stops being hereditary and the window dies — exactly the LC 209 / LC
862 fork from problem 008. The prefix map does not care, because it never makes
an irreversible decision about `l`.

    Rule of thumb: NON-NEGATIVE -> window (O(1) space).
                   NEGATIVES    -> prefix sums + hash map.

⚠️  `seen = {0: 1}` is not decoration. It counts the EMPTY prefix, which is what
    makes subarrays starting at index 0 findable. Omit it and you undercount by
    exactly the number of valid prefixes of the whole array.


================================================================================
THE ONE-PASS VARIANT (three pointers)
================================================================================
You can fuse the two passes by tracking two left pointers at once:

    l_lo  = smallest l with sum(nums[l..r]) <= goal
    l_hi  = smallest l with sum(nums[l..r]) <= goal - 1  (i.e. < goal)
    count += l_hi - l_lo

which is the same subtraction, done pointwise. It is one pass and still O(n),
and it is a good answer to "can you avoid running the window twice?" — but it
is easier to get wrong under pressure. Write the two-pass version first; offer
this as the refinement.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(nums)

    Approach                          Time      Space  Note
    --------------------------------  --------  -----  ---------------------
    Every subarray, running sum       O(n^2)    O(1)   9e8 ops at n=3e4
    atMost(g) - atMost(g-1) ✅        O(n)      O(1)   two passes
    Three-pointer one pass ✅         O(n)      O(1)   one pass, fiddlier
    Prefix sums + hash map ✅         O(n)      O(n)   survives negatives

    ⚠️  "Two passes" is still O(n). Do not let anyone tell you the two-pass
        version is asymptotically worse — it is 2n, and the constant is the
        price of a much simpler correctness argument.


================================================================================
EDGE CASES
================================================================================
    goal = 0            [0,0,0,0,0] -> 15. THE atMost(-1) TEST. Every one of
                        the n(n+1)/2 = 15 subarrays sums to 0. Without the
                        `k < 0` guard this crashes or returns nonsense.

    goal = 0, no zeros  [1]*10 -> 0. The other side of the same case.

    goal > total sum    [1,1,1] with goal 4 -> 0. Impossible; must not be
                        negative (a subtraction bug can produce negatives).

    goal == total sum   [1,1,1] with goal 3 -> 1. Only the whole array.

    zeros around a one  [0,1,0] with goal 1 -> 4. The zeros MULTIPLY the count:
                        2 choices on the left x 2 on the right. A good check
                        that you are counting subarrays, not just runs.

    [0,0,1,0,0], goal=1 -> 9. Three left choices x three right choices. If you
                        get 1 or 5 here, you are counting occurrences of the
                        pattern rather than subarrays.

    n == 1              [0] goal 0 -> 1;  [1] goal 0 -> 0;  [1] goal 1 -> 1.

    ⚠️  The answer can be Θ(n²) as a NUMBER (15 for n=5, ~4.5e8 for n=3e4). It
        does not overflow in Python, but in C++/Java you need a 64-bit
        accumulator. Worth mentioning.


================================================================================
COMMON MISTAKES
================================================================================
1. No `if k < 0: return 0` in `atMost`. goal=0 then crashes or lies.

2. Trying to write a single direct window for "sum == goal". It is not
   hereditary; there is no boundary to maintain. Recognising this quickly is
   the skill being tested.

3. `count += 1` instead of `count += r - l + 1`. That counts one subarray per
   right endpoint, i.e. it counts right endpoints, not subarrays.

4. `count += r - l` (missing the +1). Undercounts by one per position.

5. Forgetting `seen = {0: 1}` in the prefix-map version. Undercounts every
   subarray that starts at index 0.

6. Using `while total >= k` instead of `> k` in `atMost`. That computes
   "at most k-1" and shifts every answer.

7. Applying the window to an array with negative values. `atMost` is no longer
   hereditary; use the prefix map.

8. Reporting O(n^2) because two windows are run. It is 2 * O(n).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: The array can contain negative numbers.
A: The window breaks — `atMost` stops being hereditary because growing can
   lower the sum. Use prefix sums + a hash map (LC 560), which never assumes
   monotonicity. This is the same fork as LC 209 vs LC 862.

Q: Exactly K DISTINCT integers instead of a sum (LC 992)?
A: Identical structure: `atMost(K) - atMost(K-1)`, with the inner window being
   "at most K distinct" (problem 009's machinery, with the `del` on zero). That
   is problem 013 in this folder.

Q: One pass instead of two?
A: Track two left pointers, `l_lo` for `<= goal` and `l_hi` for `<= goal-1`,
   and add `l_hi - l_lo` per step. Same subtraction, done pointwise.

Q: Count subarrays with sum in a RANGE [lo, hi]?
A: `atMost(hi) - atMost(lo - 1)`. The identity generalises immediately, which
   is a good sign you have the right abstraction.

Q: Values are arbitrary non-negative integers, not just 0/1?
A: Nothing changes. `atMost` never used binarity — only non-negativity. Say
   that; it shows you know which hypothesis is load-bearing.

Q: The longest/shortest subarray with sum exactly goal, rather than the count?
A: The at-most trick does not transfer (you cannot subtract lengths). Use
   prefix sums with a hash map of FIRST occurrence (longest, LC 325) or LAST
   occurrence (shortest).

Q: How large can the answer get?
A: Θ(n²) — about 4.5 x 10^8 at n = 3 x 10^4. Fine in Python; use `long long`
   elsewhere.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 992  Subarrays with K Different Integers — problem 013; the same trick
    LC 560  Subarray Sum Equals K               — prefix map; allows negatives
    LC 1248 Count Number of Nice Subarrays      — "exactly K odd" = same trick
    LC 713  Subarray Product Less Than K        — atMost over a PRODUCT
    LC 1358 Number of Substrings Containing     — atMost's complement
            All Three Characters
    LC 2261 K Divisible Elements Subarrays      — counting with a twist
    LC 209  Minimum Size Subarray Sum           — problem 008; the sign fork
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def numSubarraysWithSum(self, nums: List[int], goal: int) -> int:
        """exactly(goal) = atMost(goal) - atMost(goal-1). O(n) time, O(1) space."""
        return self._at_most(nums, goal) - self._at_most(nums, goal - 1)

    @staticmethod
    def _at_most(nums: List[int], k: int) -> int:
        """Number of subarrays with sum <= k. The counting window."""
        if k < 0:
            return 0                                # <- the goal == 0 guard
        l = total = count = 0
        for r, x in enumerate(nums):
            total += x                              # ENTER
            while total > k:                        # RESTORE: sum <= k
                total -= nums[l]
                l += 1
            count += r - l + 1                      # subarrays ENDING at r
        return count

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def numSubarraysWithSum_prefix(self, nums: List[int], goal: int) -> int:
        """Prefix sums + hash map (the LC 560 technique). O(n) time, O(n) space.

        Works with NEGATIVE values too, unlike the window.
        """
        seen = {0: 1}                               # the empty prefix
        p = ans = 0
        for x in nums:
            p += x
            ans += seen.get(p - goal, 0)
            seen[p] = seen.get(p, 0) + 1
        return ans

    def numSubarraysWithSum_one_pass(self, nums: List[int], goal: int) -> int:
        """One pass with TWO left pointers — the same subtraction, pointwise.

        l_lo = smallest l with sum(l..r) <= goal
        l_hi = smallest l with sum(l..r) <= goal - 1
        The subarrays ending at r with sum EXACTLY goal number l_hi - l_lo.
        """
        l_lo = l_hi = 0
        sum_lo = sum_hi = 0
        ans = 0
        for r, x in enumerate(nums):
            sum_lo += x
            while l_lo <= r and sum_lo > goal:
                sum_lo -= nums[l_lo]
                l_lo += 1
            sum_hi += x
            while l_hi <= r and sum_hi >= goal:      # note: >=, i.e. <= goal-1
                sum_hi -= nums[l_hi]
                l_hi += 1
            ans += l_hi - l_lo
        return ans

    def numSubarraysWithSum_brute(self, nums: List[int], goal: int) -> int:
        """O(n^2) oracle."""
        count = 0
        for i in range(len(nums)):
            total = 0
            for j in range(i, len(nums)):
                total += nums[j]
                if total == goal:
                    count += 1
        return count

    # ------------------------------------------------------------------
    # Deliberate breakages.
    # ------------------------------------------------------------------
    @staticmethod
    def _at_most_no_guard(nums: List[int], k: int) -> int:
        """✗ BROKEN — no `k < 0` guard. With k = -1 the `while` can never be
        satisfied, so `l` runs past the end of the array."""
        l = total = count = 0
        for r, x in enumerate(nums):
            total += x
            while total > k:
                total -= nums[l]
                l += 1
            count += r - l + 1
        return count

    def numSubarraysWithSum_no_guard(self, nums: List[int], goal: int) -> int:
        """✗ BROKEN when goal == 0 — see above."""
        return (self._at_most_no_guard(nums, goal)
                - self._at_most_no_guard(nums, goal - 1))

    def numSubarraysWithSum_count_one(self, nums: List[int], goal: int) -> int:
        """✗ BROKEN — `count += 1` instead of `count += r - l + 1`, so it
        counts right ENDPOINTS rather than subarrays."""
        def at_most(k):
            if k < 0:
                return 0
            l = total = count = 0
            for r, x in enumerate(nums):
                total += x
                while total > k:
                    total -= nums[l]
                    l += 1
                count += 1                          # should be r - l + 1
            return count
        return at_most(goal) - at_most(goal - 1)

    def numSubarraysWithSum_no_empty_prefix(self, nums: List[int], goal: int) -> int:
        """✗ BROKEN — prefix map without `seen = {0: 1}`; loses every subarray
        that starts at index 0."""
        seen = {}
        p = ans = 0
        for x in nums:
            p += x
            ans += seen.get(p - goal, 0)
            seen[p] = seen.get(p, 0) + 1
        return ans


# ==============================================================================
# TESTS — run:  python 012_binary_subarrays_with_sum_solution.py
# ==============================================================================
CASES = [
    ([1, 0, 1, 0, 1], 2), ([0, 0, 0, 0, 0], 0), ([1, 1, 1, 1], 2), ([0], 0),
    ([1], 0), ([1], 1), ([0, 0, 0], 0), ([1, 1, 1], 3), ([1, 1, 1], 4),
    ([0, 1, 0], 1), ([1, 0, 0, 0, 1], 2), ([0, 1, 1, 0], 2), ([1, 0, 1], 0),
    ([0, 0, 1, 0, 0], 1), ([1] * 10, 0),
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("atMost(g) - atMost(g-1)", sol.numSubarraysWithSum),
        ("prefix sums + hash map ", sol.numSubarraysWithSum_prefix),
        ("one pass, two pointers ", sol.numSubarraysWithSum_one_pass),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(a), g) == sol.numSubarraysWithSum_brute(a, g)
                 for a, g in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(930)
    trials, mismatches = 6000, 0
    for _ in range(trials):
        a = [random.randint(0, 1) for _ in range(random.randint(1, 14))]
        g = random.randint(0, len(a))
        want = sol.numSubarraysWithSum_brute(a, g)
        for _, fn in impls:
            if fn(list(a), g) != want:
                mismatches += 1
    print(f"  {trials} random (array, goal) x {len(impls)} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The counting identity, spelled out.
    # ----------------------------------------------------------------------
    nums, k = [1, 0, 1, 0, 1], 2
    print(f"\n--- atMost({k}) on {nums}: why `count += r - l + 1` ---")
    print(f"  {'r':>2} {'x':>2} {'l':>2} {'window':>16} {'r-l+1':>6}"
          f" {'running':>8}   subarrays ending at r with sum <= {k}")
    l = total = count = 0
    for r, x in enumerate(nums):
        total += x
        while total > k:
            total -= nums[l]
            l += 1
        count += r - l + 1
        subs = [str(nums[i:r + 1]) for i in range(l, r + 1)]
        print(f"  {r:>2} {x:>2} {l:>2} {str(nums[l:r+1]):>16} {r-l+1:>6} "
              f"{count:>8}   {', '.join(subs)}")
    print(f"  atMost({k}) = {count}")
    print("  Each subarray is counted exactly once — at its own RIGHT endpoint.")

    # ----------------------------------------------------------------------
    # The subtraction.
    # ----------------------------------------------------------------------
    print(f"\n--- exactly(goal) = atMost(goal) - atMost(goal-1) ---")
    print(f"  {'goal':>5} {'atMost(goal)':>13} {'atMost(goal-1)':>15} "
          f"{'difference':>11} {'brute':>7}")
    for g in range(0, 4):
        a1 = sol._at_most(nums, g)
        a0 = sol._at_most(nums, g - 1)
        print(f"  {g:>5} {a1:>13} {a0:>15} {a1 - a0:>11} "
              f"{sol.numSubarraysWithSum_brute(nums, g):>7}")
    print("  'sum <= k' is hereditary so each column is a window; 'sum == goal'")
    print("  is not, which is why it can only be reached by subtraction.")

    # ----------------------------------------------------------------------
    # ⚠️  goal = 0 and the atMost(-1) guard.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  goal = 0 needs atMost(-1) = 0 ---")
    try:
        sol.numSubarraysWithSum_no_guard([0, 0, 0, 0, 0], 0)
        print("  (no exception — unexpected)")
    except IndexError as e:
        print(f"  without `if k < 0: return 0`  ->  IndexError: {e}")
    print(f"  with the guard: numSubarraysWithSum([0,0,0,0,0], 0) = "
          f"{sol.numSubarraysWithSum([0, 0, 0, 0, 0], 0)}  "
          f"(= 5*6/2, every subarray)")
    print(f"                  numSubarraysWithSum([1]*10, 0)      = "
          f"{sol.numSubarraysWithSum([1] * 10, 0)}   (no zeros at all)")

    # ----------------------------------------------------------------------
    # ⚠️  The two counting bugs.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `count += 1`, and a prefix map without the empty prefix ---")
    print(f"  {'input':<26} {'goal':>4} {'correct':>8} {'count += 1':>11}"
          f" {'no {0:1}':>9}")
    for a, g in ([1, 0, 1, 0, 1], 2), ([0, 0, 0, 0, 0], 0), ([0, 1, 0], 1), \
                ([0, 0, 1, 0, 0], 1), ([1, 1, 1], 3):
        print(f"  {str(a):<26} {g:>4} {sol.numSubarraysWithSum(list(a), g):>8} "
              f"{sol.numSubarraysWithSum_count_one(list(a), g):>11} "
              f"{sol.numSubarraysWithSum_no_empty_prefix(list(a), g):>9}")
    print("  `count += 1` counts RIGHT ENDPOINTS, not subarrays.")
    print("  A prefix map without {0:1} loses every subarray starting at index 0.")

    # ----------------------------------------------------------------------
    # Why "exactly" has no direct window.
    # ----------------------------------------------------------------------
    print("\n--- why 'sum == goal' is not hereditary ---")
    probe, g = [1, 0, 1, 0, 1], 2
    r = 4
    print(f"  nums = {probe}, goal = {g}, fix the right end at r = {r}:")
    print(f"  {'l':>3} {'subarray':>18} {'sum':>4} {'== goal?':>9} "
          f"{'<= goal?':>9}")
    for l in range(r + 1):
        sub = probe[l:r + 1]
        print(f"  {l:>3} {str(sub):>18} {sum(sub):>4} "
              f"{str(sum(sub) == g):>9} {str(sum(sub) <= g):>9}")
    print("  The '<= goal' column is FALSE then TRUE — one clean boundary, so a")
    print("  single pointer `l` describes it. The '== goal' column switches on")
    print("  and off, so no single boundary exists and no window can track it.")

    # ----------------------------------------------------------------------
    # Window vs prefix map: the negative-numbers fork.
    # ----------------------------------------------------------------------
    print("\n--- the window assumes NON-NEGATIVE values; the prefix map does not ---")

    def brute_neg(a, g):
        c = 0
        for i in range(len(a)):
            t = 0
            for j in range(i, len(a)):
                t += a[j]
                if t == g:
                    c += 1
        return c

    random.seed(5)
    win_wrong = pre_wrong = 0
    for _ in range(3000):
        a = [random.randint(-2, 2) for _ in range(random.randint(1, 9))]
        g = random.randint(-2, 3)
        want = brute_neg(a, g)
        if sol.numSubarraysWithSum(list(a), g) != want:
            win_wrong += 1
        if sol.numSubarraysWithSum_prefix(list(a), g) != want:
            pre_wrong += 1
    print(f"  on 3000 arrays containing NEGATIVES:")
    print(f"    atMost window  : {win_wrong} wrong")
    print(f"    prefix + map   : {pre_wrong} wrong")
    print("  Same fork as LC 209 vs LC 862: the window needs monotonicity to")
    print("  justify moving `l`; prefix sums never make that commitment.")
    all_ok &= (pre_wrong == 0)

    # ----------------------------------------------------------------------
    # Answer magnitude.
    # ----------------------------------------------------------------------
    print("\n--- the ANSWER itself can be quadratic ---")
    print(f"  {'n':>7} {'zeros only, goal=0':>20} {'= n(n+1)/2':>12}")
    for n in (5, 100, 30_000):
        a = [0] * n
        got = sol.numSubarraysWithSum(a, 0)
        print(f"  {n:>7} {got:>20} {n * (n + 1) // 2:>12}")
    print("  ~4.5e8 at the constraint limit. Fine in Python; use a 64-bit")
    print("  accumulator in C++/Java.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n^2).
    # ----------------------------------------------------------------------
    print("\n--- two windows vs every subarray ---")
    print(f"  {'n':>7} {'atMost x2':>11} {'prefix map':>12} {'one pass':>10} "
          f"{'brute O(n^2)':>14}")
    random.seed(0)
    for n in (2_000, 4_000, 8_000):
        a = [random.randint(0, 1) for _ in range(n)]
        g = n // 4
        t0 = time.perf_counter(); sol.numSubarraysWithSum(a, g)
        t1 = time.perf_counter(); sol.numSubarraysWithSum_prefix(a, g)
        t2 = time.perf_counter(); sol.numSubarraysWithSum_one_pass(a, g)
        t3 = time.perf_counter(); sol.numSubarraysWithSum_brute(a, g)
        t4 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>9.1f}ms {(t2 - t1) * 1000:>10.1f}ms "
              f"{(t3 - t2) * 1000:>8.1f}ms {(t4 - t3) * 1000:>12.1f}ms")
    print("  Two linear passes is still linear — do not let the '2' worry you.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
