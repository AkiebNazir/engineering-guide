"""
================================================================================
SOLUTION · LeetCode 260 · Single Number III                          [Medium]
https://leetcode.com/problems/single-number-iii/
================================================================================

THE CORE IDEA
--------------
XOR-fold the whole array to get `diff = a ^ b` (every paired value
cancels, leaving the XOR of the two singletons). `diff` is nonzero since
a != b, so it has a set bit somewhere -- isolate its LOWEST set bit with
`diff & -diff` (the topic guide's isolate-lowest-set-bit identity). a and
b must differ at that bit (that's precisely why it's set in their XOR),
so splitting nums into two groups by "is this bit set" puts a and b in
DIFFERENT groups while keeping every pair together (a pair's two
identical copies always land in the same group). XOR-fold each group
independently to recover a and b.

    diff = 0
    for x in nums: diff ^= x
    lowbit = diff & -diff
    a = b = 0
    for x in nums:
        if x & lowbit:
            a ^= x
        else:
            b ^= x
    return [a, b]

O(n) time (two linear passes), O(1) space.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): Counter, collect keys
with count 1. O(n) time, O(n) space -- correct, violates the O(1) space
constraint.

Approach 1 (XOR-fold + partition by lowest differing bit) [chosen] --
two O(n) passes, O(1) space. The canonical answer; directly builds on
001's single-XOR-fold trick by adding one partitioning step.

Approach 2 (partition by ANY set bit of diff, not necessarily the
lowest) -- equally correct; `diff & -diff` is just a convenient,
deterministic way to pick ONE set bit without extra branching. Any bit
where a and b differ works identically. Worth naming so it's clear the
"lowest" choice isn't load-bearing, just convenient.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [1, 2, 1, 3, 2, 5]   (singletons are 3 and 5; 1 and 2 are pairs)

Pass 1 -- XOR-fold everything:
    diff = 1^2^1^3^2^5 = (1^1) ^ (2^2) ^ 3 ^ 5 = 0 ^ 0 ^ 3 ^ 5 = 3^5
    3 = 0b011, 5 = 0b101 -> diff = 0b110 = 6

Isolate lowest set bit of diff:
    diff = 0b110, -diff = ...11111010 (two's complement)
    diff & -diff = 0b010 = 2   <- bit position 1 is the split bit

Pass 2 -- partition nums by "does x have bit 1 set (x & 2)?":
    1 = 0b001: bit1 clear -> group B (b ^= 1)
    2 = 0b010: bit1 set   -> group A (a ^= 2)
    1 = 0b001: bit1 clear -> group B (b ^= 1)
    3 = 0b011: bit1 set   -> group A (a ^= 3)
    2 = 0b010: bit1 set   -> group A (a ^= 2)
    5 = 0b101: bit1 clear -> group B (b ^= 5)

    Group A: 2 ^ 3 ^ 2 = 3   (the two 2's cancel, leaving 3)
    Group B: 1 ^ 1 ^ 5 = 5   (the two 1's cancel, leaving 5)

    Result: [3, 5]   <- matches expected output (order-independent)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time    Space   Mutates input?
    -------------------------------------  ------  ------  --------------
    Counter / hash map                     O(n)    O(n)    no
    XOR-fold + partition (lowest bit)      O(n)    O(1)    no
    XOR-fold + partition (any set bit)     O(n)    O(1)    no


================================================================================
EDGE CASES
================================================================================
    array of exactly 2 elements  -> both are singletons by definition
                                     (no pairs at all); diff = a^b covers
                                     the whole array, partition trivially
                                     splits into {a} and {b}.
    one singleton is 0            -> XOR-folding a group that reduces to
                                     0 is correct and expected -- 0 isn't
                                     special to XOR beyond being the
                                     identity element; it still partitions
                                     and folds correctly.
    both singletons negative      -> `diff & -diff` and the per-bit
                                     partition test `x & lowbit` both work
                                     correctly on negative Python ints,
                                     since they only inspect a SINGLE
                                     fixed, already-known-in-range bit
                                     position -- no 32-bit masking of the
                                     final result is needed here (contrast
                                     with 006/007/008, which reconstruct a
                                     brand-new value bit by bit and DO
                                     need a sign fix-up at the end). Here,
                                     `a` and `b` are each built purely
                                     from XOR-ing ACTUAL input values
                                     together, so they inherit Python's
                                     correct native sign automatically.
    singletons differ in the sign
    bit (one negative, one not)   -> still handled correctly -- if bit 31
                                     happens to be the (or a) differing
                                     bit, the partition still separates
                                     them cleanly; no special case needed.


================================================================================
COMMON MISTAKES
================================================================================
1. Stopping after the first XOR-fold and returning `[diff, 0]` or trying
   to "split diff in half" numerically -- diff is a^b, a single combined
   value; there is no way to recover a and b from it without the
   bit-partition step.

2. Partitioning nums into the two groups but then XOR-folding BOTH groups
   together at the end instead of keeping two SEPARATE accumulators --
   collapses right back to computing `a ^ b` again, losing all the work
   the partition step did.

3. Using `diff & -diff` without confirming diff != 0 first, e.g. if the
   problem's guarantee were violated and all values actually paired up
   evenly -- `0 & -0` is `0`, so `lowbit` would be 0 and every number
   would land in the SAME partition (the `x & 0` test is always false),
   silently degenerating into a single-group XOR fold. The problem
   guarantees this can't happen (exactly two singletons), but it's worth
   knowing why the algorithm would break if that guarantee were violated.

4. Assuming this needs the same 32-bit masking/sign-fixup as 008 --
   it doesn't, for the reason in the Edge Cases entry above: a and b are
   assembled purely by XOR-ing real input values, never by constructing
   a result bit-by-bit from scratch.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How does this generalize to a DIFFERENT number of singletons?
A: It doesn't generalize cleanly past two -- three or more singletons
   can't be separated by a single bit-partition in general (multiple
   singletons could share every bit where they differ from the pack in
   complex ways). Three-singleton variants typically need a different
   approach (e.g. counting or hashing) unless extra structure is given.

Q: Why pick the LOWEST set bit of diff specifically?
A: No deep reason beyond convenience and determinism -- `diff & -diff`
   is a cheap, branch-free way to isolate ONE set bit. Any set bit of
   diff works identically for the partition step.

Q: What if the problem asked for the two singletons in a SPECIFIC order
   (e.g. smaller first)?
A: Compare a and b after computing them and swap if needed -- O(1) extra
   work, doesn't change the overall complexity.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 136  Single Number         (001 -- one singleton, plain XOR-fold)
    LC 137  Single Number II      (008 -- one singleton appearing amid
                                    triples, bit-count mod 3)
    LC 268  Missing Number        (005 -- XOR against an index range)
    LC 645  Set Mismatch          (a different "find the odd one(s) out"
                                    shape, hash-based rather than bitwise)
================================================================================
"""

import time
from typing import List


class Solution:
    def singleNumber(self, nums: List[int]) -> List[int]:
        """✅ XOR-fold + partition by lowest differing bit. O(n) time,
        O(1) space."""
        diff = 0
        for x in nums:
            diff ^= x
        lowbit = diff & -diff

        a = b = 0
        for x in nums:
            if x & lowbit:
                a ^= x
            else:
                b ^= x
        return [a, b]

    def singleNumber_counter(self, nums: List[int]) -> List[int]:
        """Brute force: Counter. O(n) time, O(n) space."""
        from collections import Counter
        counts = Counter(nums)
        return [value for value, c in counts.items() if c == 1]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([1, 2, 1, 3, 2, 5], {3, 5}),
        ([-1, 0], {-1, 0}),
        ([0, 1], {0, 1}),
        ([4, 1, 4, 2], {1, 2}),
        ([-5, 7, -5, 3], {7, 3}),
    ]
    print("--- correctness: XOR-partition vs Counter agree ---")
    for nums, want_set in cases:
        g1 = sol.singleNumber(nums[:])
        g2 = sol.singleNumber_counter(nums[:])
        ok = set(g1) == want_set and set(g2) == want_set
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  -> {g1}  (want set {want_set})")

    # ------------------------------------------------------------------
    # RUNTIME DEMO: XOR-partition (O(1) space) vs Counter (O(n) space)
    # over a large array.
    # ------------------------------------------------------------------
    print("\n--- DEMO: XOR-partition vs Counter, n~600,000 (300k pairs + 2 singles) ---")
    import random
    random.seed(21)
    n_pairs = 300_000
    values = random.sample(range(-2_000_000, 2_000_000), n_pairs)
    big = values * 2
    singletons = [1_999_999, -1_999_999]
    big.extend(singletons)
    random.shuffle(big)

    t0 = time.perf_counter()
    r1 = sol.singleNumber(big)
    t_xor = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = sol.singleNumber_counter(big)
    t_counter = time.perf_counter() - t0

    print(f"  XOR-partition (O(1) space): {t_xor * 1000:8.2f} ms  -> {sorted(r1)}")
    print(f"  Counter (O(n) space):       {t_counter * 1000:8.2f} ms  -> {sorted(r2)}")
    all_ok &= (set(r1) == set(singletons) == set(r2))

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
