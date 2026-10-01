"""
================================================================================
SOLUTION · LeetCode 164 · Maximum Gap                                  [Hard]
https://leetcode.com/problems/maximum-gap/
================================================================================

THE CORE IDEA
--------------
"Sort, then scan adjacent differences" solves this problem trivially --
but any COMPARISON sort is O(n log n), and the problem explicitly demands
linear time and space. The way out is a pigeonhole argument that avoids
comparison sorting entirely: with `n` numbers spanning a range of
`hi - lo`, if you split that range into `n - 1` equal-width buckets, then
BY PIGEONHOLE at least one bucket must be EMPTY (there are `n` numbers to
place, but only `n - 2` "gaps between buckets" if every bucket were
non-empty... more precisely: `n` numbers into `n-1` buckets guarantees the
average bucket gets close to 1 item, and the width of each bucket,
`(hi-lo)/(n-1)`, is a LOWER BOUND on the true maximum gap -- because if
you spread `n` numbers as evenly as possible across the full range
`[lo, hi]`, the smallest possible "maximum gap" you could ever achieve is
exactly that width). The critical consequence: the number that ACTUALLY
achieves the maximum gap can never be found INSIDE a single bucket (any
two numbers sharing a bucket are closer together than the bucket width,
which is itself a lower bound on the true max gap) -- it must occur
BETWEEN a bucket's max and the NEXT non-empty bucket's min. So you never
need to sort within buckets at all: track only each bucket's min and max,
then sweep buckets left to right comparing `this_bucket.min - prev_bucket.max`.

    lo, hi = min(nums), max(nums)
    bucket_size = max(1, (hi - lo) // (n - 1))
    bucket_count = (hi - lo) // bucket_size + 1
    # one pass: drop each number into bucket (x - lo) // bucket_size,
    # tracking only that bucket's running min and max
    # second pass: sweep buckets left to right, max_gap = max over
    # (this_bucket.min - prev_nonempty_bucket.max)


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (sort + scan, banned by the problem's own constraint): sort
`nums`, then take the max of `nums[i+1] - nums[i]` over the sorted array.
Trivially correct, O(n log n) time -- the problem explicitly forbids this
complexity class via the "must run in linear time" requirement, so it's
priced here purely as the oracle for cross-checking, never the answer.

Approach 1 (chosen) -- bucket sort / pigeonhole, min/max per bucket only.
O(n) time, O(n) space (the buckets). The answer; shown above and coded
below. This is the CANONICAL linear-space, linear-time solution and the
one interviewers expect.

Approach 2 -- LSD radix sort, then scan adjacent differences. Sort the
array by least-significant digit first, using a stable counting sort per
digit, sweeping through all digit positions up to the largest number's
digit count. O(d * (n + k)) time where `d` = number of digits (bounded,
~10 for values up to 10^9) and `k` = digit base (10, or a power of 2 for a
bitwise variant) -- effectively O(n) since `d` and `k` are both constants
independent of `n`. O(n) space for the output buffer per pass. A second,
genuinely different way to reach O(n) overall: it fully sorts the array
(unlike the bucket approach, which never sorts within a bucket) and then
just scans, trading "cleverness in the gap argument" for "a real
non-comparison sort you already know." Coded below and cross-checked.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [3, 6, 9, 1], n = 4

    lo = 1, hi = 9
    bucket_size = max(1, (9-1) // (4-1)) = max(1, 8//3) = max(1, 2) = 2
    bucket_count = (9-1)//2 + 1 = 4 + 1 = 5   (buckets indexed 0..4)

    place each number, idx = (x - lo) // bucket_size:
        3 -> idx (3-1)//2 = 1   bucket[1] min=3 max=3
        6 -> idx (6-1)//2 = 2   bucket[2] min=6 max=6
        9 -> idx (9-1)//2 = 4   bucket[4] min=9 max=9
        1 -> idx (1-1)//2 = 0   bucket[0] min=1 max=1

    buckets:  [0]:(1,1)  [1]:(3,3)  [2]:(6,6)  [3]: EMPTY  [4]:(9,9)

    sweep, prev_max starts at lo=1:
        bucket 0 (1,1):  gap = 1 - 1 = 0    max_gap=0   prev_max=1
        bucket 1 (3,3):  gap = 3 - 1 = 2    max_gap=2   prev_max=3
        bucket 2 (6,6):  gap = 6 - 3 = 3    max_gap=3   prev_max=6
        bucket 3: EMPTY, skipped
        bucket 4 (9,9):  gap = 9 - 6 = 3    max_gap=3   prev_max=9

    final max_gap = 3  ✓ (sorted form is [1,3,6,9]; true adjacent gaps are
    2, 3, 3 -- the algorithm never had to sort within any bucket to find
    this, only track bucket-level min/max.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time              Space   Mutates input?
    -----------------------------------------------------------------------
    Sort + scan [priced/banned] O(n log n)        O(n)*    no
    Bucket sort / pigeonhole ✅ O(n)              O(n)     no
    LSD radix sort + scan       O(d * (n + k))     O(n)     no

    d = digit count of the largest value (constant, ~10 for values up to
    10^9); k = digit base (10). Both bucket and radix are O(n) for this
    problem's fixed-width integer constraints.
    * or the sort algorithm's own space, e.g. O(log n)/O(n) for Timsort.


================================================================================
EDGE CASES
================================================================================
    n < 2               -> return 0 immediately per the problem statement
                            (no pair exists to take a gap between).
    all elements equal   -> lo == hi; every number lands in bucket 0, and
                            the answer must be 0 -- checked as an explicit
                            early return before computing `bucket_size`
                            (otherwise `(hi-lo)//(n-1)` is 0, and dividing
                            by a zero bucket_size later would crash).
    two elements only     -> n=2 -> bucket_count = (hi-lo)//bucket_size + 1
                            where bucket_size = max(1, hi-lo) -- collapses
                            to essentially 2 buckets, correctly returns
                            `hi - lo`, the only possible gap.
    numbers already evenly
    spaced                -> every bucket ends up with exactly one element
                            and NO bucket is empty -- the pigeonhole
                            argument's "at least one empty bucket"
                            guarantee only holds because there are n-1
                            buckets for n numbers; the max gap is then
                            uniform across all adjacent bucket pairs.
    one huge outlier       -> e.g. [1, 2, 3, 1000000]: bucket_size becomes
                            large (dominated by the outlier's range), most
                            "normal" numbers collapse into very few
                            buckets, and the true max gap (to the outlier)
                            is still correctly found between the last
                            normal bucket's max and the outlier's bucket.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `bucket_size = (hi - lo) // (n - 1)` WITHOUT the `max(1, ...)`
   floor -- when `n` is large relative to the range (e.g. many duplicate
   or near-duplicate values), this can compute to 0, causing a
   division-by-zero when placing elements into buckets.
2. Sorting WITHIN each bucket "just to be safe" -- defeats the entire
   point of the pigeonhole argument, which guarantees the max gap is never
   found within a bucket; doing so adds unnecessary work without changing
   correctness, but signals the underlying proof wasn't understood.
3. Forgetting to skip EMPTY buckets during the sweep, or mishandling
   `prev_max` when a bucket is empty (must carry forward the PREVIOUS
   non-empty bucket's max, not reset to something bucket-index-based) --
   silently produces wrong gaps or crashes on `None` comparisons.
4. Off-by-one in `bucket_count` (using `(hi-lo)//bucket_size` instead of
   `(hi-lo)//bucket_size + 1`) -- can index one bucket short and either
   crash placing the maximum value or silently corrupt the last bucket.
5. Reaching for `sorted(nums)` out of habit without registering that the
   problem's linear-time/space constraint is the entire point being
   tested -- same category of miss as problem 002's "don't use the
   built-in sort" follow-up.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Prove the maximum gap can never occur strictly inside one bucket." ->
  Bucket width is `(hi-lo)//(n-1)`, a LOWER BOUND on the true max gap by
  the pigeonhole principle applied to spreading n numbers across n-1
  buckets: at least one bucket is guaranteed empty, so consecutive
  non-empty buckets' boundary values are where the "stretch" the empty
  bucket represents actually shows up. Any two numbers sharing a bucket
  are, by construction, closer together than the bucket width itself --
  which is already less than or equal to the eventual answer.
- "What if you can't assume the values are non-negative integers?" -> The
  bucket-min/max approach works unchanged for any totally-ordered numeric
  type (floats included) as long as `min`/`max`/subtraction are defined;
  the radix-sort variant specifically needs integer (or fixed-point)
  representable digits and would need adaptation (e.g. bias negative
  values by an offset, or radix-sort the IEEE-754 bit pattern) for signed
  or floating-point input.
- "Could you solve it with O(1) EXTRA space (beyond output)?" -> Not in
  general while staying O(n) time and correct for arbitrary integer
  ranges -- the bucket approach's O(n) space is what buys the O(n) time;
  trading space back down generally reintroduces an O(n log n) sort.


================================================================================
RELATED PROBLEMS
================================================================================
- Sort an Array (LC 912, this topic, 002) -- the counting-sort idea for a
  BOUNDED, small value range; here the range can be huge (up to 10^9) so a
  bucket-per-gap-estimate (not a bucket-per-value) is used instead.
- H-Index (LC 274, this topic, 006) -- another pigeonhole/bounded-range
  bucket argument, there bounding the answer by n instead of bounding a
  gap width by n-1.
- Contains Duplicate III / sliding window with buckets -- the same
  bucket-by-estimated-width idea applied to a windowed nearest-neighbor
  query instead of a global max gap.
- Missing Number / Sieve of Eratosthenes (topic 21, 008) -- other
  "exploit a bounded, known domain to beat comparison-based work" problems.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def maximumGap(self, nums: List[int]) -> int:
        """Bucket sort / pigeonhole: track only min/max per bucket, never
        sort within a bucket. O(n) time, O(n) space. The answer. See THE
        CORE IDEA above."""
        n = len(nums)
        if n < 2:
            return 0

        lo, hi = min(nums), max(nums)
        if lo == hi:
            return 0

        bucket_size = max(1, (hi - lo) // (n - 1))
        bucket_count = (hi - lo) // bucket_size + 1

        bucket_min = [None] * bucket_count
        bucket_max = [None] * bucket_count

        for x in nums:
            idx = (x - lo) // bucket_size
            if bucket_min[idx] is None or x < bucket_min[idx]:
                bucket_min[idx] = x
            if bucket_max[idx] is None or x > bucket_max[idx]:
                bucket_max[idx] = x

        max_gap = 0
        prev_max = lo
        for i in range(bucket_count):
            if bucket_min[i] is None:
                continue
            max_gap = max(max_gap, bucket_min[i] - prev_max)
            prev_max = bucket_max[i]

        return max_gap

    # ------------------------------------------------------------------
    # Variant: LSD radix sort, then scan adjacent differences. Also
    # O(n)-effective (digit count is a constant for this problem's fixed
    # integer range), but via a genuinely different route -- fully
    # sorting via non-comparison counting passes, rather than the
    # pigeonhole bucket-min/max trick.
    # ------------------------------------------------------------------
    def maximumGap_radix(self, nums: List[int]) -> int:
        n = len(nums)
        if n < 2:
            return 0

        arr = list(nums)
        max_val = max(arr)
        exp = 1
        while max_val // exp > 0:
            arr = self._counting_sort_by_digit(arr, exp)
            exp *= 10

        return max(b - a for a, b in zip(arr, arr[1:]))

    @staticmethod
    def _counting_sort_by_digit(arr: List[int], exp: int) -> List[int]:
        n = len(arr)
        output = [0] * n
        count = [0] * 10
        for x in arr:
            digit = (x // exp) % 10
            count[digit] += 1
        for d in range(1, 10):
            count[d] += count[d - 1]
        for i in range(n - 1, -1, -1):
            digit = (arr[i] // exp) % 10
            count[digit] -= 1
            output[count[digit]] = arr[i]
        return output

    # ------------------------------------------------------------------
    # Naive baseline -- priced, not the answer (violates the problem's
    # explicit linear-time requirement).
    # ------------------------------------------------------------------
    def maximumGap_sort_and_scan(self, nums: List[int]) -> int:
        """✗ O(n log n) -- forbidden by the problem's own constraint.
        Used only as an oracle for cross-checking."""
        if len(nums) < 2:
            return 0
        s = sorted(nums)
        return max(b - a for a, b in zip(s, s[1:]))


# ==============================================================================
# TESTS -- run:  python 007_maximum_gap_solution.py
# ==============================================================================
CASES = [
    ([3, 6, 9, 1], 3),
    ([10], 0),
    ([], 0),
    ([1, 1], 0),
    ([1, 10000000], 9999999),
    ([1, 3, 6, 9, 12], 3),
    ([5, 5, 5, 5], 0),
    ([0, 5], 5),
    ([1, 2, 3, 1000000], 999997),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: bucket sort / pigeonhole ---")
    for nums, expected in CASES:
        got = sol.maximumGap(list(nums))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  maximumGap({nums}) -> {got} (expected {expected})")

    print("\n--- correctness: LSD radix sort, cross-checked ---")
    for nums, expected in CASES:
        got = sol.maximumGap_radix(list(nums))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  radix({nums}) -> {got} (expected {expected})")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: [3, 6, 9, 1] ---")
    nums = [3, 6, 9, 1]
    n = len(nums)
    lo, hi = min(nums), max(nums)
    bucket_size = max(1, (hi - lo) // (n - 1))
    bucket_count = (hi - lo) // bucket_size + 1
    print(f"  lo={lo} hi={hi} bucket_size={bucket_size} bucket_count={bucket_count}")
    bmin = [None] * bucket_count
    bmax = [None] * bucket_count
    for x in nums:
        idx = (x - lo) // bucket_size
        bmin[idx] = x if bmin[idx] is None else min(bmin[idx], x)
        bmax[idx] = x if bmax[idx] is None else max(bmax[idx], x)
        print(f"  place {x} -> bucket {idx}")
    print(f"  buckets: {list(zip(bmin, bmax))}")
    max_gap, prev_max = 0, lo
    for i in range(bucket_count):
        if bmin[i] is None:
            print(f"  bucket {i}: EMPTY, skip")
            continue
        gap = bmin[i] - prev_max
        max_gap = max(max_gap, gap)
        print(f"  bucket {i}: gap = {bmin[i]} - {prev_max} = {gap}, max_gap={max_gap}")
        prev_max = bmax[i]
    print(f"  final max_gap = {max_gap}")

    # ----------------------------------------------------------------------
    # Randomised cross-check, all three implementations.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (bucket vs radix vs sort-and-scan), 1000 trials ---")
    random.seed(164)
    mismatches = 0
    for _ in range(1000):
        n = random.randint(0, 30)
        nums = [random.randint(0, 10**6) for _ in range(n)]
        r1 = sol.maximumGap(list(nums))
        r2 = sol.maximumGap_radix(list(nums))
        r3 = sol.maximumGap_sort_and_scan(list(nums))
        if not (r1 == r2 == r3):
            mismatches += 1
    print(f"  1000 random arrays: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Benchmark: O(n) bucket approach vs O(n log n) sort-and-scan.
    # ----------------------------------------------------------------------
    print("\n--- O(n) bucket sort vs O(n log n) sort-and-scan: measured runtime ---")
    print(f"  {'n':>10} {'bucket':>12} {'sort+scan':>12} {'ratio':>8}")
    random.seed(6)
    for n in (50_000, 200_000, 800_000):
        nums = [random.randint(0, 10**9) for _ in range(n)]
        t0 = time.perf_counter(); sol.maximumGap(list(nums)); t1 = time.perf_counter()
        sol.maximumGap_sort_and_scan(list(nums)); t2 = time.perf_counter()
        bk_ms = (t1 - t0) * 1000
        ss_ms = (t2 - t1) * 1000
        ratio = ss_ms / bk_ms if bk_ms > 0 else float("inf")
        print(f"  {n:>10} {bk_ms:>10.2f}ms {ss_ms:>10.2f}ms {ratio:>7.2f}x")
    print("  (report whatever this machine actually measures -- CPython's C-level")
    print("   Timsort is extremely well-tuned and may still be competitive despite")
    print("   doing asymptotically more comparisons at these sizes; the bucket")
    print("   approach's real justification is the problem's HARD linear-space/")
    print("   time requirement, not necessarily raw wall-clock speed in CPython.)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
