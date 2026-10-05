"""
================================================================================
SOLUTION · LeetCode 136 · Single Number                              [Easy]
https://leetcode.com/problems/single-number/
================================================================================

THE CORE IDEA
--------------
XOR every element together. `x ^ x == 0` and `x ^ 0 == x`, and XOR is
commutative + associative, so every value that appears twice cancels to 0
in whatever order they're visited, leaving only the singleton.

    result = 0
    for x in nums: result ^= x
    return result

O(n) time, O(1) space -- exactly what the problem demands.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): for each element, scan the
rest of the array counting occurrences; return the one with count 1.
O(n^2) time, O(1) space. Correct but quadratic for no reason.

Approach 1 (hash map / Counter): count frequencies, return the key with
count 1. O(n) time, O(n) space. Correct, but the problem explicitly asks
for constant space, which rules this out as the "answer."

Approach 2 (sort, then scan pairs) -- sort nums, walk in steps of 2 looking
for a break in pairing (handle the last element specially). O(n log n)
time, O(1) extra space (or O(n) if sort isn't in-place) -- beats the hash
map on space but loses on time, and mutates the input by sorting it.

Approach 3 (XOR) [chosen] -- O(n) time, O(1) space, doesn't mutate input.
Strictly dominates every other approach on this problem's exact
constraints.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [4, 1, 2, 1, 2]

    result = 0b000
    ^= 4 (0b100)  -> result = 0b100
    ^= 1 (0b001)  -> result = 0b101
    ^= 2 (0b010)  -> result = 0b111
    ^= 1 (0b001)  -> result = 0b110   (the first 1 pairs off with this one)
    ^= 2 (0b010)  -> result = 0b100   (the first 2 pairs off with this one)

    result = 0b100 = 4   <- matches the singleton


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach              Time         Space   Mutates input?
    ---------------------  -----------  ------  --------------
    Brute force (nested)   O(n^2)       O(1)    no
    Hash map / Counter     O(n)         O(n)    no
    Sort + scan pairs      O(n log n)   O(1)*   yes (in-place sort)
    XOR fold [chosen]      O(n)         O(1)    no

    * O(1) extra beyond Python's Timsort internals; O(n) if using sorted().


================================================================================
EDGE CASES
================================================================================
    single-element array     -> XOR of one value against the initial 0 is
                                 itself. Correctly returns nums[0].
    negative numbers          -> XOR operates on Python's two's-complement
                                 bit pattern for negatives too; cancellation
                                 still works (`-1 ^ -1 == 0`).
    zero present as a pair    -> `0 ^ 0 == 0`, contributes nothing, exactly
                                 as intended (it cancels like any other pair).
    the singleton itself is 0 -> still correctly isolated; XOR doesn't
                                 special-case zero as a value, only as the
                                 identity element for the operation.


================================================================================
COMMON MISTAKES
================================================================================
1. Reaching for a Counter/set first out of habit -- correct, but violates
   the stated O(1) space constraint; interviewers watching for the XOR
   trick will flag this even if it "passes."

2. Assuming XOR only cancels ADJACENT duplicates. It doesn't need order at
   all -- commutative + associative means EVERY occurrence of a value
   cancels regardless of position, which is what makes the one-pass fold
   correct without sorting first.

3. Confusing this with Single Number II/III (008/009 in this folder), where
   values appear THREE times or there are TWO singletons -- plain XOR-fold
   silently gives a wrong (nonsensical) answer on those variants; it only
   works when exactly one value is unpaired and everything else appears an
   EVEN number of times.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if every other value appeared THREE times instead of twice?
A: Plain XOR breaks (three cancels to the value itself, not to 0). Need to
   count bits per position mod 3 -- see 008 Single Number II.

Q: What if there were exactly two singleton values instead of one?
A: XOR-folding the whole array gives `a ^ b`, not `a` or `b` individually.
   Split by the lowest set bit of `a ^ b` to separate the two groups --
   see 009 Single Number III.

Q: Does this work if the array can be empty?
A: The problem guarantees non-empty; an empty array would fold to 0, which
   is ambiguous (could mean "no elements" or "the singleton is 0").


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 137  Single Number II    (appears 3x except one -- bit-count mod 3)
    LC 260  Single Number III   (two singletons -- XOR + partition)
    LC 268  Missing Number      (005 -- XOR against index range)
    LC 389  Find the Difference (XOR two strings' char codes)
================================================================================
"""

import time
from typing import List


class Solution:
    def singleNumber(self, nums: List[int]) -> int:
        """✅ XOR fold. O(n) time, O(1) space."""
        result = 0
        for x in nums:
            result ^= x
        return result

    def singleNumber_counter(self, nums: List[int]) -> int:
        """Alternative: hash map. O(n) time, O(n) space -- violates the
        stated space constraint, kept only for the runtime comparison."""
        from collections import Counter
        counts = Counter(nums)
        for value, c in counts.items():
            if c == 1:
                return value
        raise ValueError("no singleton found")


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([2, 2, 1], 1),
        ([4, 1, 2, 1, 2], 4),
        ([1], 1),
        ([-1, -1, -2], -2),
        ([0, 0, 5], 5),
    ]
    print("--- correctness ---")
    for nums, want in cases:
        got = sol.singleNumber(nums[:])
        got2 = sol.singleNumber_counter(nums[:])
        ok = got == want and got2 == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  -> {got}  (want {want})")

    # ------------------------------------------------------------------
    # RUNTIME DEMO: XOR fold vs Counter over a large array. Both are O(n)
    # asymptotically -- the point is to show XOR still wins in practice
    # (no hashing, no dict allocation) while using O(1) space.
    # ------------------------------------------------------------------
    print("\n--- DEMO: XOR fold vs Counter, 2,000,001-element array ---")
    n = 1_000_000
    big = list(range(n)) * 2 + [n]  # every value paired except n
    import random
    random.seed(42)
    random.shuffle(big)

    t0 = time.perf_counter()
    r1 = sol.singleNumber(big)
    t_xor = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = sol.singleNumber_counter(big)
    t_counter = time.perf_counter() - t0

    print(f"  XOR fold:  {t_xor * 1000:8.2f} ms  -> {r1}")
    print(f"  Counter:   {t_counter * 1000:8.2f} ms  -> {r2}")
    print(f"  XOR uses O(1) extra memory; Counter allocates a dict with "
          f"~{n:,} entries.")
    all_ok &= (r1 == r2 == n)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
