"""
================================================================================
SOLUTION · LeetCode 974 · Subarray Sums Divisible by K                  [Medium]
https://leetcode.com/problems/subarray-sums-divisible-by-k/
================================================================================

THE CORE IDEA
--------------
Problem 004's hashmap trick (topic guide §1.1), keyed on `prefix % k` instead
of the raw prefix value. Two prefixes with the SAME remainder mod k bracket a
subarray whose sum is a multiple of k:

    (prefix[r+1] - prefix[l]) % k == 0   <=>   prefix[r+1] % k == prefix[l] % k

    seen = {0: 1}                  # remainder -> how many times seen (sentinel!)
    running = count = 0
    for x in nums:
        running += x
        r = running % k            # Python: already in [0, k) for k > 0
        count += seen.get(r, 0)
        seen[r] = seen.get(r, 0) + 1
    return count

O(n) time, O(min(n, k)) space — the map holds at most k distinct remainders,
tighter than problem 004's O(n) (topic guide §1.5).


================================================================================
WHY "SAME REMAINDER" IS EXACTLY "DIFFERENCE DIVISIBLE BY K"
================================================================================
This is modular arithmetic's defining fact, not a trick specific to this
problem: for any integers A, B and k > 0,

    (A - B) % k == 0   <=>   A % k == B % k

Intuition via clock arithmetic: 9:00 and 21:00 are "the same time" on a
12-hour clock because they differ by 12 (a multiple of 12) — same remainder
mod 12. Substituting A = prefix[r+1], B = prefix[l]:

    sum(nums[l..r]) % k == 0
    (prefix[r+1] - prefix[l]) % k == 0
    prefix[r+1] % k == prefix[l] % k

So "does an earlier prefix pair with this one to form a good subarray" is
"have I seen this exact remainder before" — an O(1) dictionary lookup,
regardless of how large the actual prefix sums get. This is why the map
never grows past k entries: there are only k possible remainders, versus
up to n possible raw prefix values in problem 004.


================================================================================
⚠️  PYTHON'S SIGN-CORRECT `%` — the headline fact of this problem
================================================================================
`nums` may contain NEGATIVE values (constraints: -10^4 <= nums[i] <= 10^4),
so `running` can go negative. In C, Java, and Go, the `%` operator's result
takes the SIGN OF THE DIVIDEND, so a negative dividend can produce a
NEGATIVE remainder:

    C / Java / Go:   -5 % 7  ==  -5      (sign of the LEFT operand)
    Python:          -5 % 7  ==   2      (sign of the RIGHT operand / divisor)

Run it live below — the demo prints `-5 % 7` and confirms it is `2`, not
`-5`. Because k > 0 always in this problem, Python's `%` is ALREADY the
canonical non-negative remainder in `[0, k)`. Someone translating this
algorithm from C/Java/Go experience will often write:

    r = ((running % k) + k) % k        # "just in case" normalization

This is HARMLESS here (it's a no-op once the value is already in [0, k)),
but it is dead code that signals the author doesn't know WHY it's
unnecessary in Python — and worse, some candidates, unsure whether Python's
`%` is "safe," reach for `abs(running) % k` instead, which is NOT the same
operation and silently produces wrong answers by conflating a negative
running sum with its positive mirror (e.g. running = -3 and running = 3 give
different remainders mod most k, but abs() throws that distinction away).
The demo below constructs a case where `abs(running) % k` disagrees with the
correct `running % k` to make this concrete.

    THE RULE: in Python, for k > 0, `x % k` is ALWAYS in `[0, k)` — no
    normalization needed, and `abs(x) % k` is NOT a substitute for it.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [4, 5, 0, -2, -3, 1], k = 5           (LeetCode's own example, answer 7)

    seen = {0: 1}, running = 0, count = 0

    x=4   running=4    r=4 % 5=4   seen.get(4,0)=0  count=0   seen={0:1,4:1}
    x=5   running=9    r=9 % 5=4   seen.get(4,0)=1  count=1   seen={0:1,4:2}
    x=0   running=9    r=9 % 5=4   seen.get(4,0)=2  count=3   seen={0:1,4:3}
    x=-2  running=7    r=7 % 5=2   seen.get(2,0)=0  count=3   seen={0:1,4:3,2:1}
    x=-3  running=4    r=4 % 5=4   seen.get(4,0)=3  count=6   seen={0:1,4:4,2:1}
    x=1   running=5    r=5 % 5=0   seen.get(0,0)=1  count=7   seen={0:2,4:4,2:1}

    Final count = 7  ✓  matches LeetCode's expected answer.

Each hit against remainder 4 corresponds to one of the good subarrays ending
at that index; the final hit against remainder 0 (the sentinel!) is the
whole-array prefix [4,5,0,-2,-3,1] itself, sum 5, divisible by 5 — this is
exactly the subarray the `{0: 1}` sentinel exists to catch (topic guide §1.3).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                             Time      Space          Mutates input?
    ------------------------------------ --------  -------------- --------------
    Every subarray, sum + check % k      O(n^2)    O(1)           No
    Remainder hashmap ✅                 O(n)      O(min(n, k))   No

    The benchmark at the bottom of this file measures the real crossover
    between these two as n grows.


================================================================================
EDGE CASES
================================================================================
    k = 1               -> EVERY subarray is divisible by 1: answer must be
                            n*(n+1)/2, the count of all possible subarrays.
                            Exercises that the remainder-0 bucket correctly
                            absorbs every single prefix when k=1 (there's
                            only one possible remainder).
    negative numbers     -> running can go negative; Python's % must stay
                            sign-correct through the whole scan, not just on
                            the first negative value.
    single element,
      divisible by k     -> nums=[5], k=5: one subarray, itself, count 1.
    single element,
      not divisible      -> nums=[5], k=9: count 0. Tests that a "miss" does
                            not accidentally increment via a bad sentinel.
    all same remainder   -> maximizes the count: with m elements sharing one
                            remainder bucket, C(m+1, 2) subarrays qualify
                            (the +1 for the sentinel's own bucket entry).
    k larger than any
      individual element  -> no single element is divisible, but combinations
                            can still sum to a multiple of k; tests that the
                            algorithm doesn't shortcut on "no element alone
                            works."
    zeros in the array    -> 0 % k == 0 always; a zero element alone is
                            always divisible by k, and contributes multiple
                            subarrays when adjacent to other zeros.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the `seen = {0: 1}` sentinel (topic guide §1.3) — silently
   drops every good subarray that starts at index 0.
2. Using `abs(running) % k` instead of `running % k` "to be safe" about
   negatives — these are DIFFERENT operations and disagree whenever
   `running` is negative and not already a multiple of k. See the demo.
3. Manually adding `((running % k) + k) % k` out of C/Java/Go habit. Not
   wrong (it's a no-op once already in [0, k)), but signals the candidate
   hasn't verified Python's actual `%` semantics — say the one-liner out
   loud in an interview instead of defensively coding around a non-problem.
4. Confusing this with problem 004's Variant A key (raw prefix value) —
   using the raw `running` as the dict key still WORKS here (multiples of k
   still collide correctly is false in general... actually keying on the
   raw value undercounts nothing but wastes space: two different raw sums
   with the same remainder are now separate keys, so subarrays that SHOULD
   be counted together are missed). Concretely: `prefix=4` and `prefix=9`
   both have remainder 4 mod 5 and must be treated as "the same bucket" —
   keying on the raw prefix value fails to merge them and undercounts.
5. Off-by-one on which map variant to use: this problem wants a COUNT
   (Variant A), not a first-index map (Variant B) — using `if r not in seen`
   instead of accumulating a count silently caps every bucket at 1.
6. Not handling `k` divisibility for negative individual elements correctly
   because of a hand-rolled normalization bug (e.g. subtracting k instead of
   adding it) — trust `running % k` in Python, don't hand-roll it.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the interviewer asks for the actual subarrays, not just a count?
A: Store lists of indices instead of counts in the map: `seen[r]` becomes a
   list of prefix-end indices with that remainder, and for each new index
   pair it with every stored index. Time becomes O(n + answer_count) in the
   worst case (can be O(n^2) if the answer count is quadratic).

Q: Same problem, but the modulus is not a compile-time constant — it changes
   per query against a fixed array?
A: The map is built per array; if k varies per query and the array is fixed,
   rebuilding the O(n) remainder map for every new k costs O(n) per query —
   no way around recomputation without extra structure since the "bucket"
   assignment depends entirely on k.

Q: How is this different from LC 523 (Continuous Subarray Sum), problem 008
   in this folder?
A: LC 523 asks EXISTENCE (does any qualifying subarray of length >= 2 exist)
   rather than a COUNT, so it uses Variant B (first-index map) instead of
   Variant A (counting map), and it has an extra length >= 2 constraint plus
   special handling when k == 0. Same remainder trick, different map
   semantics — see problem 008's solution for the full contrast.

Q: Can k be 0 or negative here?
A: Not per LC 974's constraints (2 <= k <= 10^4) — k is always a positive
   integer >= 2, so `running % k` is always well-defined and Python's sign
   convention applies cleanly. Contrast with problem 008, where k CAN be 0.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 560  Subarray Sum Equals K              — problem 004, the base pattern
    LC 523  Continuous Subarray Sum            — problem 008, same remainder
                                                  trick + first-index map + a
                                                  length-2 trap + k=0 handling
    LC 1590 Make Sum Divisible by P            — the "remove one subarray so
                                                  the REST is divisible by k"
                                                  variant of this exact idea
    LC 1524 Number of Sub-arrays With Odd Sum  — k=2 special case in disguise
                                                  (odd/even is mod 2)
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def subarraysDivByK(self, nums: List[int], k: int) -> int:
        """Prefix-sum remainder hashmap. O(n) time, O(min(n, k)) space."""
        seen = {0: 1}                      # remainder -> count, sentinel included
        running = count = 0
        for x in nums:
            running += x
            r = running % k                # Python: sign-correct, already in [0, k)
            count += seen.get(r, 0)
            seen[r] = seen.get(r, 0) + 1
        return count

    # ------------------------------------------------------------------
    # Alternatives / oracle.
    # ------------------------------------------------------------------
    def subarraysDivByK_brute(self, nums: List[int], k: int) -> int:
        """O(n^2) oracle: every subarray, sum it, test % k == 0."""
        n = len(nums)
        count = 0
        for i in range(n):
            total = 0
            for j in range(i, n):
                total += nums[j]
                if total % k == 0:
                    count += 1
        return count

    def subarraysDivByK_list_impl(self, nums: List[int], k: int) -> int:
        """Same idea, using a list of size k instead of a dict — valid
        because remainders are always in [0, k). Demonstrates that the
        'hashmap' here can just as well be a fixed-size array."""
        buckets = [0] * k
        buckets[0] = 1
        running = count = 0
        for x in nums:
            running += x
            r = running % k
            count += buckets[r]
            buckets[r] += 1
        return count

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def subarraysDivByK_no_sentinel(self, nums: List[int], k: int) -> int:
        """✗ BROKEN ON PURPOSE — no {0: 1} sentinel. Misses every good
        subarray that starts at index 0."""
        seen = {}
        running = count = 0
        for x in nums:
            running += x
            r = running % k
            count += seen.get(r, 0)
            seen[r] = seen.get(r, 0) + 1
        return count

    def subarraysDivByK_abs_bug(self, nums: List[int], k: int) -> int:
        """✗ BROKEN ON PURPOSE — uses abs(running) % k, conflating a
        negative running sum with its positive mirror. NOT the same
        operation as running % k."""
        seen = {0: 1}
        running = count = 0
        for x in nums:
            running += x
            r = abs(running) % k           # WRONG: not equivalent to running % k
            count += seen.get(r, 0)
            seen[r] = seen.get(r, 0) + 1
        return count


# ==============================================================================
# TESTS — run:  python 007_subarray_sums_divisible_by_k_solution.py
# ==============================================================================
CASES = [
    ([4, 5, 0, -2, -3, 1], 5, 7),
    ([5], 9, 0),
    ([5], 5, 1),
    ([1, 2, 3], 1, 6),
    ([-1, -2, -3], 3, 3),
    ([2, 2, 2, 2, 2], 2, 15),
    ([1, 2, 3, 4, 5, 6], 100, 0),
    ([0, 0, 0], 5, 6),
    ([7], 7, 1),
    ([-5], 5, 1),
    ([1, -1, 1, -1], 2, 4),
    ([-4, -4, -4], 4, 6),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("remainder hashmap ", sol.subarraysDivByK),
        ("remainder array    ", sol.subarraysDivByK_list_impl),
    ]
    for name, fn in impls:
        ok = all(fn(nums, k) == expected for nums, k, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    ok = all(sol.subarraysDivByK_brute(nums, k) == expected
              for nums, k, expected in CASES)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  brute oracle self-check")

    # ----------------------------------------------------------------------
    # LIVE: Python's sign-correct %.
    # ----------------------------------------------------------------------
    print("\n--- Python's `%` is sign-correct for a positive divisor ---")
    print(f"  -5 % 7  = {-5 % 7}   (Python; C/Java/Go would give -5)")
    print(f"  -1 % 5  = {-1 % 5}   (Python; C/Java/Go would give -1)")
    print(f"  -12 % 5 = {-12 % 5}  (Python; C/Java/Go would give -2)")
    normalized = ((-5 % 7) + 7) % 7
    print(f"  ((-5 % 7) + 7) % 7 = {normalized}  <- the C-style 'fix', a no-op in Python")

    # ----------------------------------------------------------------------
    # ⚠️ no-sentinel bug.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  missing the {0: 1} sentinel ---")
    print(f"  {'input':<28} {'k':>3} {'correct':>8} {'no-sentinel':>12}  ok?")
    for nums, k, _ in CASES[:6]:
        good = sol.subarraysDivByK(nums, k)
        bad = sol.subarraysDivByK_no_sentinel(nums, k)
        print(f"  {str(nums):<28} {k:>3} {good:>8} {bad:>12}  "
              f"{'yes' if good == bad else 'NO  <- prefix-from-start subarrays missed'}")

    # ----------------------------------------------------------------------
    # ⚠️ abs() bug.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  abs(running) % k is NOT running % k ---")
    print(f"  {'input':<28} {'k':>3} {'correct':>8} {'abs() bug':>10}  ok?")
    abs_bug_cases = [
        ([-1, -2, -3], 3, 3),
        ([1, -4, 1, -4], 4, 6),
        ([-5, -5, -5], 5, 6),
        ([4, 5, 0, -2, -3, 1], 5, 7),
    ]
    for nums, k, _ in abs_bug_cases:
        good = sol.subarraysDivByK(nums, k)
        bad = sol.subarraysDivByK_abs_bug(nums, k)
        print(f"  {str(nums):<28} {k:>3} {good:>8} {bad:>10}  "
              f"{'yes' if good == bad else 'NO  <- abs() conflated distinct remainders'}")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(4)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        n = random.randint(1, 12)
        nums = [random.randint(-15, 15) for _ in range(n)]
        k = random.randint(2, 9)
        want = sol.subarraysDivByK_brute(nums, k)
        if sol.subarraysDivByK(nums, k) != want:
            mismatches += 1
        if sol.subarraysDivByK_list_impl(nums, k) != want:
            mismatches += 1
    print(f"  {trials} random (nums, k) pairs x 2 implementations: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The scan, traced.
    # ----------------------------------------------------------------------
    nums, k = [4, 5, 0, -2, -3, 1], 5
    print(f"\n--- the scan over {nums}, k={k} ---")
    print(f"  {'x':>3} {'running':>8} {'r=running%k':>12} {'hits':>5} {'count':>6}")
    seen, running, count = {0: 1}, 0, 0
    for x in nums:
        running += x
        r = running % k
        hits = seen.get(r, 0)
        count += hits
        seen[r] = seen.get(r, 0) + 1
        print(f"  {x:>3} {running:>8} {r:>12} {hits:>5} {count:>6}")
    print(f"  final count = {count}  (want 7)")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: O(n) vs O(n^2), real crossover.
    # ----------------------------------------------------------------------
    print("\n--- O(n) remainder hashmap vs O(n^2) brute force ---")
    print(f"  {'n':>7} {'hashmap O(n)':>13} {'brute O(n^2)':>14} {'speedup':>10}")
    random.seed(2)
    for n in (200, 800, 3200, 6400):
        nums = [random.randint(-1000, 1000) for _ in range(n)]
        k = 97
        t0 = time.perf_counter()
        sol.subarraysDivByK(nums, k)
        t1 = time.perf_counter()
        sol.subarraysDivByK_brute(nums, k)
        t2 = time.perf_counter()
        fast_ms = (t1 - t0) * 1000
        slow_ms = (t2 - t1) * 1000
        speedup = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  {n:>7} {fast_ms:>12.2f}ms {slow_ms:>13.2f}ms {speedup:>9.1f}x")
    print("  The O(n) hashmap barely moves as n grows; the O(n^2) brute force")
    print("  grows quadratically -- the gap widens exactly as predicted.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
