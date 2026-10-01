"""
================================================================================
SOLUTION · LeetCode 201 · Bitwise AND of Numbers Range                [Medium]
https://leetcode.com/problems/bitwise-and-of-numbers-range/
================================================================================

THE CORE IDEA
--------------
AND-ing every number in [left, right] together zeroes out every bit
position below the highest bit where left and right first differ,
because counting through the range necessarily visits both a 0 and a 1
at every such lower position for SOME number in between. What survives
is exactly the COMMON BINARY PREFIX of left and right. Find it by
right-shifting both in lockstep until they're equal, then shift that
common value back left by the same amount:

    shift = 0
    while left != right:
        left >>= 1
        right >>= 1
        shift += 1
    return left << shift

O(log(right)) time (at most 31 shifts, since right < 2^31), O(1) space.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): AND every number from
left to right in a loop. O(right - left) time -- correct but can be up
to ~2^31 iterations (e.g. left=1, right=2147483647), far too slow; the
problem's constraints exist specifically to make this approach time out.

Approach 1 (common-prefix via lockstep right-shift) [chosen] --
O(log(right)) = O(31) time, O(1) space. Directly derives the answer from
the structural insight, no lookup tables or precomputation.

Approach 2 (Brian Kernighan's n & (n-1), applied to `right`) -- repeatedly
clear right's LOWEST set bit (`right &= right - 1`) as long as the result
is still >= left; once it drops below left, the value just before that
final clear is the answer. Same O(log(right)) bound, different framing:
instead of shrinking BOTH endpoints toward each other, it shrinks `right`
downward one set bit at a time until it can no longer stay >= left,
which turns out to land on exactly the same common prefix.


================================================================================
STEP BY STEP TRACE
================================================================================
left = 26 (0b11010), right = 30 (0b11110)

    Iteration 1: left=26 (11010), right=30 (11110) -- not equal
        left >>= 1 -> 13 (01101), right >>= 1 -> 15 (01111), shift=1
    Iteration 2: left=13 (01101), right=15 (01111) -- not equal
        left >>= 1 -> 6 (00110), right >>= 1 -> 7 (00111), shift=2
    Iteration 3: left=6 (00110), right=7 (00111) -- not equal
        left >>= 1 -> 3 (00011), right >>= 1 -> 3 (00011), shift=3
    left == right == 3 (0b00011) -- loop ends

    result = left << shift = 3 << 3 = 24 (0b11000)

    Verify directly: 26&27&28&29&30
        26=11010  27=11011  28=11100  29=11101  30=11110
        bit4: 1,1,1,1,1 -> 1     bit3: 1,1,1,1,1 -> 1
        bit2: 0,0,1,1,1 -> 0     bit1: 1,1,0,0,1 -> 0     bit0: 0,1,0,1,0 -> 0
        AND = 0b11000 = 24   <- matches


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time             Space   Mutates input?
    -------------------------------------  ---------------  ------  --------------
    Brute-force AND every number           O(right-left)    O(1)    no
    Common-prefix lockstep shift [chosen]  O(log(right))    O(1)    no
    Kernighan clear-lowest-bit on `right`  O(log(right))    O(1)    no


================================================================================
EDGE CASES
================================================================================
    left == right                -> loop never runs (already equal),
                                     shift stays 0, result = left
                                     unchanged. Correct: AND of a single
                                     number with itself is itself.
    left == 0                     -> the moment right > 0, the loop will
                                     shift down to left=right=0 (since 0
                                     shifted right stays 0), and any
                                     nonzero right eventually reaches 0
                                     too -- result is 0. Makes sense: the
                                     range includes 0, and ANDing with 0
                                     annihilates every bit.
    left=1, right=2^31-1          -> huge range; the common prefix is
                                     empty (they share no leading 1-bit
                                     pattern once you look closely -- 1 is
                                     0...001, 2^31-1 is 1...111), so
                                     result is 0. This is exactly why the
                                     brute-force approach is disqualified
                                     -- shift-based reaches this instantly
                                     while brute force would need ~2^31
                                     iterations.
    right == 2^31 - 1 (max input) -> exercises the full 31-bit width;
                                     the lockstep shift still terminates
                                     in at most 31 iterations, safely
                                     within the O(log(right)) bound.


================================================================================
COMMON MISTAKES
================================================================================
1. Reaching for the brute-force loop without checking the constraint
   range first -- `right - left` can be up to ~2^31, which times out
   even though the code is "correct." The range size, not just
   correctness, is the whole point of this problem.

2. Shifting only ONE of left/right instead of both in lockstep -- the
   algorithm depends on shrinking BOTH endpoints together until they
   coincide; shifting just one drifts them apart instead of converging.

3. Forgetting to shift the final common value BACK LEFT by `shift` at
   the end. Returning the shifted-down `left` (or `right`) directly gives
   a value that's numerically far too small -- e.g. in the trace above,
   forgetting the final `<< shift` would return 3 instead of 24.

4. Off-by-one in the shift COUNT -- incrementing `shift` before vs after
   the comparison, or starting it at 1 instead of 0, throws off the final
   `<< shift` by one bit position, corrupting the answer even though the
   "common prefix value" itself (pre-shift) was computed correctly.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would this change for a bitwise OR of the range instead of AND?
A: OR of a range with left != right is almost always "all bits set up to
   the highest bit of right" (the complement intuition -- ORing tends to
   SET bits, not clear them, so consecutive integers quickly fill in
   every lower bit). A different closed form, not a simple adaptation of
   this AND solution.

Q: Can you avoid the loop and compute this in true O(1)?
A: Effectively yes in practice -- `(right).bit_length()` and comparing
   against `left`'s bit length, combined with checking whether left and
   right share the same top bits via a mask, can shortcut some cases,
   but the general solution still needs to locate the first differing
   bit, which is inherently an O(log(right))-ish operation (the loop
   here is already effectively O(1) in practice, since 31 is a small
   constant).

Q: Why does "common prefix" specifically capture the answer, rather than
   some other combination of bits?
A: Because ANY bit below the first differing position is GUARANTEED to
   take both values 0 and 1 somewhere in [left, right] (since left !=
   right forces the range to span across at least one "carry" through
   that lower region), and a single 0 anywhere kills that bit under AND.
   Bits at or above the first difference, by definition, are identical
   across the WHOLE range (that's what "first differing bit" means for
   everything below it), so they survive untouched.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 191  Number of 1 Bits            (002 -- n & (n-1) as the core
                                          primitive, reused here in Approach 2)
    LC 231  Power of Two                (n & (n-1) == 0 check)
    LC 762  Prime Number of Set Bits in Binary Range (range + bit-counting,
                                          different combination)
    LC 137  Single Number II            (008 -- another "reduce a range/multi-
                                          set to one surviving bit pattern"
                                          problem, different mechanism)
================================================================================
"""

import time


class Solution:
    def rangeBitwiseAnd(self, left: int, right: int) -> int:
        """✅ Common-prefix via lockstep right-shift. O(log(right)) time,
        O(1) space."""
        shift = 0
        while left != right:
            left >>= 1
            right >>= 1
            shift += 1
        return left << shift

    def rangeBitwiseAnd_kernighan(self, left: int, right: int) -> int:
        """Alternative: repeatedly clear right's lowest set bit until it
        drops within [left, right] trivially (right <= left).
        O(log(right)) time, O(1) space."""
        while left < right:
            right &= right - 1  # clear right's lowest set bit
        return right

    def rangeBitwiseAnd_brute(self, left: int, right: int) -> int:
        """Brute force: AND every number in the range. O(right-left) time
        -- only safe for small ranges, used here as a correctness oracle."""
        result = left
        for x in range(left, right + 1):
            result &= x
        return result


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (5, 7, 4),
        (0, 0, 0),
        (1, 2147483647, 0),
        (5, 5, 5),
        (26, 30, 24),
        (1, 1, 1),
        (0, 1, 0),
    ]
    print("--- correctness: lockstep-shift vs Kernighan agree ---")
    for left, right, want in cases:
        g1 = sol.rangeBitwiseAnd(left, right)
        g2 = sol.rangeBitwiseAnd_kernighan(left, right)
        ok = g1 == g2 == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  [{left},{right}]  shift={g1} "
              f"kernighan={g2}  (want {want})")

    print("\n--- cross-check against brute force on small ranges ---")
    small_cases = [(5, 7), (0, 0), (5, 5), (26, 30), (1, 100), (12345, 12999)]
    for left, right in small_cases:
        g1 = sol.rangeBitwiseAnd(left, right)
        g3 = sol.rangeBitwiseAnd_brute(left, right)
        ok = g1 == g3
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  [{left},{right}]  shift={g1} brute={g3}")

    # ------------------------------------------------------------------
    # RUNTIME DEMO: shift-based O(log n) vs brute force O(n), showing WHY
    # brute force is disqualified for large ranges near the constraint's
    # upper bound.
    # ------------------------------------------------------------------
    print("\n--- DEMO: O(log n) shift vs O(n) brute force, range width 5,000,000 ---")
    left, right = 100_000_000, 105_000_000

    t0 = time.perf_counter()
    r1 = sol.rangeBitwiseAnd(left, right)
    t_shift = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = sol.rangeBitwiseAnd_brute(left, right)
    t_brute = time.perf_counter() - t0

    print(f"  Shift-based (~31 iterations): {t_shift * 1000:8.3f} ms  -> {r1}")
    print(f"  Brute force (5,000,001 iterations): {t_brute * 1000:8.2f} ms  -> {r2}")
    speedup = t_brute / t_shift if t_shift > 0 else float("inf")
    print(f"  speedup: {speedup:,.0f}x -- and this range is 400x smaller than "
          f"the worst case the constraints actually allow (right up to 2^31-1)")
    all_ok &= (r1 == r2)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
