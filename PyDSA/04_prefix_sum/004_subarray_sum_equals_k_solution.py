"""
================================================================================
SOLUTION · LeetCode 560 · Subarray Sum Equals K                        [Medium]
https://leetcode.com/problems/subarray-sum-equals-k/
================================================================================

THE CORE IDEA
--------------
This is the flagship problem of topic 04 — see the topic guide's §1.1 for the
full argument, restated here: a subarray nums[l..r] sums to k exactly when

    prefix[r+1] - prefix[l] == k   <=>   prefix[l] == prefix[r+1] - k

Walk the array keeping a running prefix sum and a hashmap `seen` that counts
how many times each prefix value has occurred. At each step, the number of
subarrays ENDING at this index with sum k is exactly `seen.get(running - k, 0)`
— every prior index whose prefix equals `running - k` pairs with the current
index to bracket a k-sum subarray.

    seen = {0: 1}                 # the empty-prefix sentinel — see below
    running = count = 0
    for x in nums:
        running += x
        count += seen.get(running - k, 0)      # LOOKUP first
        seen[running] = seen.get(running, 0) + 1  # THEN record

O(n) time, O(n) space. This is Variant A ("counting map") from the topic
guide §1.4: the map stores *how many times* each prefix value has been seen,
because every earlier occurrence is a SEPARATE valid subarray ending here —
that is precisely what [1,1,1], k=2 demonstrates (two different subarrays,
both length 2, from two different left endpoints).


================================================================================
WHY THIS IS NOT A SLIDING WINDOW — numbers can be negative
================================================================================
Topic guide §1.1: sliding window requires a MONOTONE validity condition —
growing the window can only push the sum in one direction. That needs
non-negative data. LC 560's constraints allow `nums[i]` as low as -1000, so
there is no such monotonicity: extending the window can make the running sum
go up or down, and there is no principled rule for "should l advance?"

This is the direct negative-numbers sibling of topic 03's LC 209 (Minimum
Size Subarray Sum) — same shape of question ("does some contiguous range
have property X"), but LC 209's non-negative constraint makes it a window,
and LC 560's unrestricted sign makes it a hashmap lookup instead. Same
English question, different sign constraint, completely different tool.


================================================================================
LOOKUP-BEFORE-RECORD — why the order matters
================================================================================
The lookup for `running - k` happens BEFORE `running` itself is inserted into
`seen`. This ordering matters most when k == 0: if you recorded first, the
just-inserted `running` value would immediately match itself in the very same
step's lookup, incorrectly counting a "subarray" that starts and ends before
any new element has been added — i.e., counting the empty suffix as a
zero-sum subarray of the real array, which is not a valid (non-empty)
subarray. Lookup-then-record keeps every match strictly using PRIOR indices,
which is exactly what `prefix[l]` with `l <= r` requires.


================================================================================
⚠️  THE SEED BUG — seen = {0: 1} is not optional (topic guide §1.3)
================================================================================
Initialise `seen = {0: 1}` before the loop: the empty prefix (sum of zero
elements, conceptually "before index 0") has been seen once. Without this
sentinel, any subarray that itself STARTS AT INDEX 0 is silently
undercounted, because there is no recorded prefix of 0 to pair with it.

Trace nums = [1, 1, 1], k = 2 with the BROKEN `seen = {}` (no sentinel):

    i=0  x=1   running=1   lookup(1-2=-1) -> 0 (nothing)      seen={1:1}
    i=1  x=1   running=2   lookup(2-2=0)  -> 0 MISSED!        seen={1:1, 2:1}
                             (nums[0..1] = [1,1] sums to 2 — this is a REAL
                              answer, and it is silently dropped because
                              prefix 0 was never recorded)
    i=2  x=1   running=3   lookup(3-2=1)  -> 1 (nums[1..2])   seen={1:1,2:1,3:1}

    Broken total: 1.  Correct total: 2.  The subarray starting at index 0
    ([1,1], indices 0-1) is the one the missing sentinel drops.

The demo below runs both versions on this exact input live and prints the
mismatch.


================================================================================
THE TWO MAP VARIANTS — and why this problem needs the counting one
================================================================================
Topic guide §1.4 draws the line between two shapes of "prefix seen before" map:

    Variant A (this problem): COUNT occurrences. Every prior index sharing a
    prefix value contributes a SEPARATE valid subarray ending here, so the
    map value is a running count, and the answer accumulates `seen.get(...)`
    every step.

    Variant B (problem 005, LC 525): record only the FIRST index a prefix
    value was seen, because that problem wants the longest span, and the
    widest span always comes from the earliest occurrence.

Using Variant B's "first index only" map here would silently cap every
bucket at "seen or not seen" and lose the count — [1,1,1], k=2 would report
1 valid subarray started, not 2 counted. The demo below shows this live too.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [3, 4, 7, 2, -3, 1, 4, 2], k = 7

    seen starts at {0: 1}

    i  x    running  lookup(running-7)  found  count  seen (after recording)
    -  -    0        -                  -      0      {0:1}
    0  3    3        lookup(-4)=0       0      0      {0:1, 3:1}
    1  4    7        lookup(0)=1        1      1      {0:1, 3:1, 7:1}
    2  7    14       lookup(7)=1        1      2      {0:1, 3:1, 7:1, 14:1}
    3  2    16       lookup(9)=0        0      2      {..., 16:1}
    4  -3   13       lookup(6)=0        0      2      {..., 13:1}
    5  1    14       lookup(7)=1        1      3      {..., 14:2}   <- DUPLICATE prefix!
    6  4    18       lookup(11)=0       0      3      {..., 18:1}
    7  2    20       lookup(13)=1       1      4      {..., 20:1}

    Final count: 4. The four subarrays: [3,4] (0-1), [7] (2), [4,-3,1,4] or
    the pair via the repeated running=14 (2-5, prefix 14 appearing twice
    means TWO different l's pair validly with it later), and [4,2] (6-7).
    The repeated prefix value 14 at i=2 and i=5 is exactly why the map must
    COUNT, not just remember "seen": both occurrences are valid left
    endpoints for later matches.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time    Space   Mutates input?  Note
    ---------------------------------  ------  ------  ---------------  ----------------------
    Every subarray, sum from scratch   O(n^3)  O(1)    no               3 nested loops
    Every start, running inner sum     O(n^2)  O(1)    no               brute force here
    Prefix array + nested lookup       O(n^2)  O(n)    no               array doesn't help alone
    Prefix sum + hashmap (count) ✅    O(n)    O(n)    no               the answer
    Prefix sum + hashmap, no sentinel  O(n)    O(n)    no               ✗ WRONG — undercounts


================================================================================
EDGE CASES
================================================================================
    [1], k=1              -> 1   Single element equal to k. Simplest sentinel case.
    [1], k=0               -> 0   No zero-length subarray counts; k=0 needs an
                                   actual zero-sum subarray.
    [0,0,0], k=0            -> 6   EVERY subarray of zeros sums to 0: (3 choose 2)
                                   + 3 = 6 total contiguous subarrays. Exercises
                                   the counting map heavily — the SAME prefix
                                   value (0) recurs constantly.
    [-1,-1,-1], k=-2         -> 2   All-negative input; the algorithm does not
                                   care about sign, only equality.
    [1,2,3], k=6             -> 1   The WHOLE array sums to k, and the subarray
                                   starts at index 0 — this is the sentinel
                                   case: without seen={0:1}, this is missed.
    [1,2,3], k=100           -> 0   No valid subarray exists; count stays 0.
    [1,1,1,1], k=2            -> 3   Duplicate prefix sums (1,2,3,4) still each
                                   occur once here, but overlapping windows of
                                   length 2 each match — demonstrates multiple
                                   counted subarrays from a repeating pattern.
    nums with negative numbers -> the entire reason this is a hashmap problem
                                   and not a sliding window (topic guide §1.1).


================================================================================
COMMON MISTAKES
================================================================================
1. `seen = {}` instead of `seen = {0: 1}`. Undercounts every subarray that
   starts at index 0. See the seed-bug section above.

2. Recording `running` into `seen` BEFORE doing the lookup for `running - k`.
   Breaks the k == 0 case in particular by letting a step match itself.

3. Reaching for a sliding window because "it's a subarray sum problem" without
   checking that `nums[i]` can be negative. Topic guide §1.1 — check sign
   first.

4. Using a "seen or not" boolean / first-index map (Variant B, problem 005's
   tool) instead of a counting map. Silently caps every prefix bucket at 1
   and returns too small an answer whenever a prefix value repeats.

5. Building the full `prefix` array and then doing an O(n) or O(n log n)
   nested search per index instead of the O(1) hashmap lookup — technically
   correct but throws away the whole point of the map.

6. Forgetting that `k` itself can be negative (constraints allow it) — the
   algorithm needs no special-casing for this, but a solution that assumes
   `k >= 0` (e.g. clamping negative lookups) is wrong.

7. Off-by-one confusion about whether `seen[running]` should be incremented
   before or after using it to answer a DIFFERENT query later — the running
   value for THIS index must only ever answer lookups from FUTURE indices,
   never itself.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the actual subarrays, not just the count.
A: Store `seen[value]` as a list of INDICES instead of a count; for each hit,
   emit `nums[idx:i+1]` for every recorded idx. Note this can be O(n^2) output
   in the worst case (e.g. all zeros), which is unavoidable if every one must
   be materialized.

Q: What if you needed the LONGEST subarray summing to k, not the count?
A: Switch to Variant B (problem 005's tool): `seen` maps prefix value to its
   FIRST index only, and you take `max(best, i - seen[running - k])` instead
   of counting. Never overwrite an already-recorded first index.

Q: Subarray sum divisible by K instead of equal to K?
A: LC 974 (problem 007 in this folder) — key the map on `running % K` instead
   of the raw prefix value. See topic guide §1.5.

Q: Can you do it in O(1) extra space?
A: Not in general for this exact problem — the map can legitimately need to
   remember up to n distinct prefix values. O(n) space is the accepted
   answer.

Q: What if nums is a stream and k can change per query?
A: Precompute the prefix array once (O(n)); for a FIXED k, you'd still need
   a fresh O(n) hashmap pass per k (the count depends on which sentinel value
   you're matching against), or you'd batch multiple k's using the same
   prefix array with per-k processing.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 209  Minimum Size Subarray Sum       — the non-negative sibling; a
                                              sliding window, not this topic
                                              (topic 03, problem 008)
    LC 525  Contiguous Array                — Variant B, first-index map
                                              (problem 005 here)
    LC 974  Subarray Sums Divisible by K    — mod-K keys (problem 007 here)
    LC 523  Continuous Subarray Sum         — mod-K + first-index + length-2
                                              trap (problem 008 here)
    LC 325  Maximum Size Subarray Sum Equals k — Variant B applied to THIS
                                              problem's exact sign constraint
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def subarraySum(self, nums: List[int], k: int) -> int:
        """Prefix sum + counting hashmap. O(n) time, O(n) space.
        The answer. See THE CORE IDEA above."""
        seen = {0: 1}                              # sentinel: empty prefix seen once
        running = count = 0
        for x in nums:
            running += x
            count += seen.get(running - k, 0)       # LOOKUP first
            seen[running] = seen.get(running, 0) + 1  # THEN record
        return count

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def subarraySum_brute_cubic(self, nums: List[int], k: int) -> int:
        """O(n^3) reference: re-sum every subarray from scratch. Too slow to
        run at scale; kept only to name the naive baseline explicitly."""
        n = len(nums)
        count = 0
        for i in range(n):
            for j in range(i, n):
                if sum(nums[i:j + 1]) == k:
                    count += 1
        return count

    def subarraySum_brute(self, nums: List[int], k: int) -> int:
        """O(n^2) oracle: running inner sum from every start (no re-summing
        from scratch). Used to cross-check the O(n) answer."""
        n = len(nums)
        count = 0
        for i in range(n):
            s = 0
            for j in range(i, n):
                s += nums[j]
                if s == k:
                    count += 1
        return count

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def subarraySum_no_sentinel(self, nums: List[int], k: int) -> int:
        """✗ BROKEN ON PURPOSE — seen = {} instead of {0: 1}. Undercounts
        every subarray that starts at index 0. See the seed-bug trace above."""
        seen = {}                                    # NO sentinel
        running = count = 0
        for x in nums:
            running += x
            count += seen.get(running - k, 0)
            seen[running] = seen.get(running, 0) + 1
        return count

    def subarraySum_wrong_variant(self, nums: List[int], k: int) -> int:
        """✗ BROKEN ON PURPOSE — uses a "seen or not" boolean map (Variant B,
        problem 005's tool) instead of a counting map (Variant A). Caps every
        prefix bucket at 1 and undercounts when a prefix value repeats."""
        seen = {0}                                    # a SET, not a counting dict
        running = count = 0
        for x in nums:
            running += x
            if (running - k) in seen:
                count += 1                            # counts AT MOST once per prefix value
            seen.add(running)
        return count


# ==============================================================================
# TESTS — run:  python 004_subarray_sum_equals_k_solution.py
# ==============================================================================
CASES = [
    ([1, 1, 1], 2),
    ([1, 2, 3], 3),
    ([1, -1, 0], 0),
    ([1], 1),
    ([1], 0),
    ([-1, -1, 1], 0),
    ([0, 0, 0], 0),
    ([-1, -1, -1], -2),
    ([3, 4, 7, 2, -3, 1, 4, 2], 7),
    ([1, 2, 3], 100),
    ([1, 2, 3], 6),
    ([1, 1, 1, 1], 2),
    ([5], 5),
    ([-5], -5),
    ([1, -1, 1, -1, 1], 0),
    ([100, -100, 100, -100], 0),
    ([], 0),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: O(n) hashmap vs O(n^2) running-inner-sum oracle ---")
    for nums, k in CASES:
        want = sol.subarraySum_brute(nums, k)
        got = sol.subarraySum(nums, k)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<32} k={k:<6} -> {got}  "
              f"(want {want})")

    # ----------------------------------------------------------------------
    # ⚠️  The seed-sentinel bug, demonstrated live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  seen={} vs seen={0:1}: the sentinel bug (topic guide §1.3) ---")
    print(f"  {'input':<20} {'k':>4} {'correct':>8} {'no sentinel':>12}  ok?")
    sentinel_mismatch = False
    for nums, k in ([1, 1, 1], 2), ([1, 2, 3], 6), ([1, -1, 0], 0), ([5], 5), ([1, 2, 3], 100):
        good = sol.subarraySum(nums, k)
        bad = sol.subarraySum_no_sentinel(nums, k)
        mismatch = good != bad
        sentinel_mismatch |= mismatch
        print(f"  {str(nums):<20} {k:>4} {good:>8} {bad:>12}  "
              f"{'yes' if not mismatch else 'NO  <- undercounted, missing sentinel'}")
    print(f"  sentinel bug reproduced: {sentinel_mismatch}")
    all_ok &= sentinel_mismatch  # we WANT to have proven the bug exists

    print("\n  [1,1,1], k=2 traced with NO sentinel:")
    nums, k = [1, 1, 1], 2
    seen, running, count = {}, 0, 0
    print(f"  {'i':>2} {'x':>3} {'running':>8} {'lookup(running-k)':>18} {'found':>6} {'count':>6}")
    for i, x in enumerate(nums):
        running += x
        found = seen.get(running - k, 0)
        count += found
        print(f"  {i:>2} {x:>3} {running:>8} {running - k:>18} {found:>6} {count:>6}")
        seen[running] = seen.get(running, 0) + 1
    print(f"  no-sentinel total: {count}  (correct answer: {sol.subarraySum(nums, k)})")
    print("  The subarray [1,1] starting at index 0 is dropped: there was never")
    print("  a recorded prefix of 0 to match against.")

    # ----------------------------------------------------------------------
    # ⚠️  Variant confusion: counting map vs first-index/seen-set map.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  counting map (Variant A) vs seen-set (Variant B tool): "
          "topic guide §1.4 ---")
    print(f"  {'input':<20} {'k':>4} {'correct':>8} {'wrong variant':>14}  ok?")
    variant_mismatch = False
    for nums, k in ([1, 1, 1], 2), ([1, 1, 1, 1], 2), ([0, 0, 0], 0), ([3, 4, 7, 2, -3, 1, 4, 2], 7):
        good = sol.subarraySum(nums, k)
        bad = sol.subarraySum_wrong_variant(nums, k)
        mismatch = good != bad
        variant_mismatch |= mismatch
        print(f"  {str(nums):<20} {k:>4} {good:>8} {bad:>14}  "
              f"{'yes' if not mismatch else 'NO  <- capped at 1 per prefix value'}")
    print(f"  variant-confusion bug reproduced: {variant_mismatch}")
    all_ok &= variant_mismatch

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: nums=[3,4,7,2,-3,1,4,2], k=7 ---")
    nums, k = [3, 4, 7, 2, -3, 1, 4, 2], 7
    seen, running, count = {0: 1}, 0, 0
    print(f"  {'i':>2} {'x':>3} {'running':>8} {'lookup':>7} {'found':>6} {'count':>6}")
    for i, x in enumerate(nums):
        running += x
        found = seen.get(running - k, 0)
        count += found
        print(f"  {i:>2} {x:>3} {running:>8} {running - k:>7} {found:>6} {count:>6}")
        seen[running] = seen.get(running, 0) + 1
    print(f"  final count: {count}")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(7)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        n = random.randint(0, 12)
        nums = [random.randint(-5, 5) for _ in range(n)]
        k = random.randint(-10, 10)
        if sol.subarraySum(nums, k) != sol.subarraySum_brute(nums, k):
            mismatches += 1
    print(f"  {trials} random small arrays (values in [-5,5], k in [-10,10]): "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # O(n) vs O(n^2) runtime demo.
    # ----------------------------------------------------------------------
    print("\n--- O(n) hashmap vs O(n^2) running-inner-sum: measured runtime ---")
    print(f"  {'n':>7} {'hashmap O(n)':>14} {'brute O(n^2)':>14} {'ratio':>8}")
    random.seed(0)
    for n in (500, 2_000, 8_000):
        nums = [random.randint(-1000, 1000) for _ in range(n)]
        k = 0  # k=0 with random data gives the brute force real matches to find, not a trivial early-out
        t0 = time.perf_counter(); sol.subarraySum(nums, k)
        t1 = time.perf_counter(); sol.subarraySum_brute(nums, k)
        t2 = time.perf_counter()
        hm_ms = (t1 - t0) * 1000
        br_ms = (t2 - t1) * 1000
        ratio = br_ms / hm_ms if hm_ms > 0 else float("inf")
        print(f"  {n:>7} {hm_ms:>12.2f}ms {br_ms:>12.2f}ms {ratio:>7.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
