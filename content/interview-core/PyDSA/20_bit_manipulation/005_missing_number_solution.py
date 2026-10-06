"""
================================================================================
SOLUTION · LeetCode 268 · Missing Number                             [Easy]
https://leetcode.com/problems/missing-number/
================================================================================

THE CORE IDEA
--------------
There are n+1 possible values (0..n) but only n numbers in nums, so
exactly one value is missing. XOR every index 0..n-1, every value 0..n
(via starting the accumulator at n), and every nums[i] together: every
number that IS present gets XOR'd exactly twice (once as an index-ish
"expected" value, once as the actual array value) and cancels to 0; the
missing number is XOR'd only once and survives.

    result = n
    for i, x in enumerate(nums):
        result ^= i ^ x
    return result

O(n) time, O(1) space, no overflow risk (XOR never widens beyond the
input's own bit width, unlike a running sum).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): build a set of nums,
scan range(n+1) for the value not in the set. O(n) time, O(n) space --
correct, violates the O(1) space follow-up.

Approach 1 (Gauss sum) -- expected = n*(n+1)//2 (sum of 0..n), actual =
sum(nums), return expected - actual. O(n) time, O(1) space. Simple and
fast in practice (Python's built-in `sum` is C-implemented), but the
"expected minus actual" subtraction can overflow in fixed-width-int
languages for large n (not a concern for Python's arbitrary-precision
ints, worth naming as a portability difference).

Approach 2 (XOR) [chosen] -- same complexity class as Gauss sum, but
overflow-proof by construction: XOR-ing two n-bit values never produces
more than n bits, so there's no "sum got too big" failure mode at all,
in ANY language. This is the property that makes it the canonical answer
in this topic.

Approach 3 (sort, then scan for a gap) -- sort nums, walk and compare
`nums[i]` against expected index i, return the first mismatch (or n if
no mismatch is found, meaning n itself is missing). O(n log n) time,
O(1) extra if sorted in place (but mutates input) -- strictly worse than
approaches 1/2 on this problem's exact constraints.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [3, 0, 1]   (n = 3, range [0,3], missing value is 2)

    result = n = 3                    (0b011)

    i=0, x=3:  result ^= 0 ^ 3  ->  result = 0b011 ^ 0b000 ^ 0b011 = 0b000
    i=1, x=0:  result ^= 1 ^ 0  ->  result = 0b000 ^ 0b001 = 0b001
    i=2, x=1:  result ^= 2 ^ 1  ->  result = 0b001 ^ 0b011 = 0b010

    Final result = 0b010 = 2   <- matches: 2 is the missing number

    (Sanity: every value 0,1,3 got XOR'd exactly twice across the whole
    walk -- once as an index i or the initial n, once as a nums[i] value
    -- and cancelled. Only 2 was XOR'd once, as index i=2's "expected"
    contribution, and survived.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time          Space   Mutates input?
    -----------------------  ------------  ------  --------------
    Set difference           O(n)          O(n)    no
    Gauss sum [alternative]  O(n)          O(1)    no
    XOR fold [chosen]        O(n)          O(1)    no
    Sort + scan for gap      O(n log n)    O(1)*   yes (in-place sort)

    * O(1) extra beyond Timsort's own working space.


================================================================================
EDGE CASES
================================================================================
    n == 1, nums == [0]  -> missing value is 1 (the largest possible).
                              result starts at n=1, XORs with i=0,x=0 ->
                              stays 1. Correct.
    n == 1, nums == [1]  -> missing value is 0 (the smallest possible).
    missing value is 0    -> 0 XORs as a no-op everywhere it would have
                              appeared, so its "absence" shows up as
                              simply never being cancelled -- still
                              correctly isolated, no special case needed.
    missing value is n    -> this is exactly why the accumulator starts
                              at n instead of 0 -- there is no array
                              index n to pair it against (indices only go
                              0..n-1), so seeding the accumulator with n
                              supplies that missing pairing slot.


================================================================================
COMMON MISTAKES
================================================================================
1. Starting `result = 0` instead of `result = n`. Off by exactly one
   XOR term -- the range [0, n] has n+1 values but indices only cover
   0..n-1, so n itself needs to be injected into the fold some other way.
   Forgetting this silently breaks the case where n itself is the
   missing value.

2. Using Gauss sum with `n * (n + 1) // 2` but computing `n` as
   `len(nums) - 1` instead of `len(nums)` -- the array has n ELEMENTS
   for a range of n+1 POSSIBLE values, so n IS `len(nums)`, not
   `len(nums) - 1`.

3. Assuming XOR requires nums to be SORTED first. It doesn't -- like
   001 Single Number, XOR is commutative and associative, so any
   visitation order cancels correctly.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why prefer XOR over the Gauss sum approach?
A: Both are O(n)/O(1) in Python. XOR is preferred in languages with
   fixed-width integers because summing up to n*(n+1)/2 can overflow a
   32-bit accumulator for large n, while XOR never exceeds the input's
   own bit width. In Python this is a moot point (ints are arbitrary
   precision) but interviewers often want you to name it anyway.

Q: What if the array could contain duplicates or values outside [0, n]?
A: Both XOR and Gauss-sum assume the problem's guarantee (distinct
   values, all within [0, n]) -- violate either guarantee and both
   approaches silently return a wrong answer with no error. A defensive
   version would validate with a set first (O(n) extra space).

Q: How does this generalize to "find the TWO missing numbers"?
A: XOR-fold everything to get `a ^ b` for the two missing values, then
   split on the lowest set bit of `a ^ b` to separate them into two
   groups (LC 260-style reasoning) -- same technique as 009 Single
   Number III, applied to a different setup.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 136  Single Number        (001 -- same XOR self-cancellation idea)
    LC 448  Find All Numbers Disappeared in an Array (index-marking, a
             different trick for a similar-sounding problem)
    LC 41   First Missing Positive (harder variant, in-place index-placement)
    LC 260  Single Number III    (009 -- same "split by lowest set bit" move)
================================================================================
"""

import time
from typing import List


class Solution:
    def missingNumber(self, nums: List[int]) -> int:
        """✅ XOR fold. O(n) time, O(1) space."""
        result = len(nums)
        for i, x in enumerate(nums):
            result ^= i ^ x
        return result

    def missingNumber_gauss(self, nums: List[int]) -> int:
        """Alternative: Gauss sum. O(n) time, O(1) space."""
        n = len(nums)
        expected = n * (n + 1) // 2
        return expected - sum(nums)

    def missingNumber_set(self, nums: List[int]) -> int:
        """Brute force: set difference. O(n) time, O(n) space."""
        full = set(range(len(nums) + 1))
        return next(iter(full - set(nums)))


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([3, 0, 1], 2),
        ([0, 1], 2),
        ([9, 6, 4, 2, 3, 5, 7, 0, 1], 8),
        ([0], 1),
        ([1], 0),
    ]
    print("--- correctness: all three approaches agree ---")
    for nums, want in cases:
        g1 = sol.missingNumber(nums[:])
        g2 = sol.missingNumber_gauss(nums[:])
        g3 = sol.missingNumber_set(nums[:])
        ok = g1 == g2 == g3 == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  -> {g1}  (want {want})")

    # ------------------------------------------------------------------
    # RUNTIME DEMO: XOR fold vs set-difference over a large array. Both
    # are O(n); measured on this machine the set-difference approach is
    # actually slightly faster (Python's set/`-` operator is C-implemented
    # and the array here is small enough that hashing overhead doesn't
    # dominate) -- but XOR still wins on SPACE (O(1) vs O(n) for the two
    # sets it builds), which is what the follow-up actually asks for.
    # ------------------------------------------------------------------
    print("\n--- DEMO: XOR fold (O(1) space) vs set difference (O(n) space), n=1,000,000 ---")
    import random
    n = 1_000_000
    missing_value = 424242
    nums = [x for x in range(n + 1) if x != missing_value]
    random.seed(11)
    random.shuffle(nums)

    t0 = time.perf_counter()
    r1 = sol.missingNumber(nums)
    t_xor = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = sol.missingNumber_set(nums)
    t_set = time.perf_counter() - t0

    print(f"  XOR fold (O(1) space):        {t_xor * 1000:8.2f} ms  -> {r1}")
    print(f"  Set difference (O(n) space):  {t_set * 1000:8.2f} ms  -> {r2}")
    faster = "XOR fold" if t_xor < t_set else "Set difference"
    print(f"  On THIS run, {faster} was faster -- but only XOR fold meets "
          f"the O(1) extra-space follow-up regardless of which is faster.")
    all_ok &= (r1 == r2 == missing_value)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
