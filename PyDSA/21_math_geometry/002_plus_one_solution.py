"""
================================================================================
SOLUTION · LeetCode 66 · Plus One                                    [Easy]
https://leetcode.com/problems/plus-one/
================================================================================

THE CORE IDEA
--------------
This is grade-school addition, one digit at a time, right to left, exactly
how you'd add 1 to a number on paper: walk from the last digit backwards,
add the carry (1, initially, since we're adding exactly one), if the digit
becomes 10 write 0 and carry 1 into the next position to the left,
otherwise write the incremented digit and STOP -- no more carry to
propagate. If the carry is still alive after walking off the front of the
array (every digit was a 9), the number needed one MORE digit than it
started with: prepend a 1 (equivalently: the answer is `[1] + [0]*len(digits)`,
since an all-9s number of length n becomes `10...0` with n zeros).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (convert to int, price it): join digits into an integer, add 1,
convert back to a list of digits. Correct and short in Python specifically
(arbitrary-precision ints), but relies on the language having bignums --
the same trick fails in a fixed-width-integer language, and the problem is
explicitly testing the manual-carry technique that generalizes to ANY
digit-array arithmetic (this is also exactly what 005 Multiply Strings
requires, where there's no bignum shortcut available by definition).

Approach 1 (chosen) -- manual right-to-left carry propagation in place,
with an explicit branch for the "carry survives past the front" case.
O(n) time, O(1) EXTRA space in the common case (in-place), O(n) only when
the array must grow by one digit.


================================================================================
STEP BY STEP TRACE
================================================================================
digits = [1, 2, 9]                     ("129", adding 1 -> should be 130)

    i=2: digits[2]=9 -> becomes 10 -> write 0, carry to i=1
         digits = [1, 2, 0]
    i=1: digits[1]=2 -> becomes 3 -> write 3, NO carry -> return immediately
         digits = [1, 3, 0]

    result: [1, 3, 0]  (130 = 129 + 1, correct, loop exited early at i=1)


digits = [9, 9, 9]                     ("999", adding 1 -> should be 1000)

    i=2: 9 -> 10 -> write 0, carry.      digits = [9, 9, 0]
    i=1: 9 -> 10 -> write 0, carry.      digits = [9, 0, 0]
    i=0: 9 -> 10 -> write 0, carry.      digits = [0, 0, 0]
    loop exhausted (i walked past index 0), carry STILL alive

    -> prepend a 1: [1, 0, 0, 0]   ("1000" -- the array GREW by one digit,
       from length 3 to length 4. This is the case almost everyone misses:
       it is tempting to assume the array length never changes.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time    Space               Mutates input?
    ------------------------------------------------------------------------
    int-convert-and-back [priced]  O(n)   O(n) new list        no
    Carry propagation [chosen]     O(n)   O(1) extra (usual case,
                                            O(n) new list only when the
                                            all-9s case forces growth)
                                                                yes, in place
                                                                (except the
                                                                 growth case,
                                                                 which must
                                                                 build a new
                                                                 list)

    n = len(digits). Worst case for the carry approach is still O(n) time
    even in the growth case: at most one full pass plus building an (n+1)
    length list.


================================================================================
EDGE CASES
================================================================================
    all 9's, e.g. [9], [9,9,9]  -> the array GROWS by one digit; the loop
                             exits WITHOUT an early return, so the "carry
                             still alive" branch after the loop must exist
                             and must prepend, not append.
    single element [0]       -> becomes [1], simplest case, exercises the
                             early-return path on the very first digit.
    single element [9]       -> becomes [1, 0], simplest case that still
                             exercises the array-growth path.
    a 9 in the middle but not
    at the very front, e.g.
    [1,9,9]                  -> carries propagate through the 9's and stop
                             cleanly at the leading 1 -> 9, no growth needed
                             ([2,0,0]); growth ONLY happens when literally
                             every digit is a 9.
    no negative numbers      -> the problem guarantees digits are 0-9 and
                             the number is non-negative by construction
                             (no sign digit exists in this representation).


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the post-loop "carry still alive" branch entirely -- an
   all-9s input silently returns a full array of 0's with no leading 1,
   which is wrong (`[9,9,9]` -> `[0,0,0]` instead of `[1,0,0,0]`).
2. Appending the extra 1 at the wrong end (`digits + [1]` instead of
   `[1] + digits`) -- this reverses the number's value entirely (`[0,0,0,1]`
   reads as 1, not 1000).
3. Converting to int for "speed" or "simplicity" without acknowledging that
   this sidesteps the actual point of the exercise (manual carry
   arithmetic), which becomes a hard requirement in follow-up problems
   like 005 Multiply Strings where no bignum conversion is allowed.
4. Not stopping the loop early when a carry resolves (looping through
   every remaining digit unconditionally) -- functionally harmless here
   since adding 0 to an unaffected digit is a no-op, but it's needlessly
   doing O(n) work in the common case where the carry dies after one
   digit, and the same sloppy pattern breaks addition of two ARBITRARY
   numbers (005) where a stale carry variable must be tracked precisely.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if we were adding two arbitrary digit arrays instead of always
  adding exactly 1?" -> Same carry-propagation shape, but the carry can
  now be more than 1 in intermediate steps if you're also multiplying (see
  005 Multiply Strings) -- for pure addition of two numbers it's still a
  single 0-or-1 carry, walked from both arrays' ends simultaneously.
- "Can you avoid allocating a new array in the growth case?" -> Not fully --
  Python lists (like most languages' fixed arrays) can't grow the FRONT
  in place for free; you either build a new list or, if allowed, use a
  structure with O(1) prepend (e.g. a deque) and convert once at the end.
- "Why does the carry only ever need to look ONE digit ahead?" -> Because
  we're adding at most 1 at the units place initially, and 9+1=10 produces
  a carry of exactly 1 at each subsequent position too -- the carry never
  exceeds 1 when the only thing being added is a single unit.


================================================================================
RELATED PROBLEMS
================================================================================
- Multiply Strings (LC 43, this topic, 005) -- same manual-digit-arithmetic
  discipline, but the carry can exceed 1 mid-computation and the result
  array size is `len(num1) + len(num2)`.
- Add Binary (LC 67) -- identical shape in base 2 instead of base 10.
- Add Two Numbers (LC 2, linked lists) -- same carry-propagation idea, but
  the digits are stored least-significant-first in a linked list instead
  of most-significant-first in an array.
================================================================================
"""

import random
import time


class Solution:
    def plusOne(self, digits: list[int]) -> list[int]:
        for i in range(len(digits) - 1, -1, -1):
            if digits[i] < 9:
                digits[i] += 1
                return digits
            digits[i] = 0
        # every digit was a 9 and got reset to 0; carry survived past the
        # front of the array -- the number needs one more leading digit.
        return [1] + digits


def _via_int_conversion(digits: list[int]) -> list[int]:
    """Priced-not-shipped alternative, used only for the cross-check demo."""
    n = int("".join(map(str, digits))) + 1
    return [int(c) for c in str(n)]


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ([1, 2, 3], [1, 2, 4]),
        ([4, 3, 2, 1], [4, 3, 2, 2]),
        ([9], [1, 0]),
        ([0], [1]),
        ([9, 9, 9], [1, 0, 0, 0]),
        ([1, 9, 9], [2, 0, 0]),
        ([8, 9, 9, 9], [9, 0, 0, 0]),
        ([2, 9], [3, 0]),
    ]
    for digits, expected in cases:
        original = list(digits)
        got = sol.plusOne(list(digits))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  plusOne({original}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- carry propagation vs int conversion, 2000 random numbers")
    print("-" * 72)
    random.seed(11)
    mismatch = 0
    for _ in range(2000):
        length = random.randint(1, 12)
        digits = [random.randint(1, 9)] + [random.randint(0, 9) for _ in range(length - 1)]
        a = sol.plusOne(list(digits))
        b = _via_int_conversion(digits)
        if a != b:
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {2000 - mismatch}/2000 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- carry propagation vs int conversion, measured live")
    print("-" * 72)
    n = 300_000
    big_digits_list = [([9] * 30) for _ in range(n)]  # worst case: forces growth every time

    t0 = time.perf_counter()
    for d in big_digits_list:
        sol.plusOne(list(d))
    carry_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for d in big_digits_list:
        _via_int_conversion(d)
    int_ms = (time.perf_counter() - t0) * 1000

    print(f"n={n} calls on 30-digit all-9's input (worst case, forces array growth):")
    print(f"  carry propagation:  {carry_ms:8.2f} ms")
    print(f"  int conversion:     {int_ms:8.2f} ms")
    if int_ms < carry_ms:
        print(f"  measured: int conversion is {carry_ms / int_ms:.2f}x FASTER here -- CPython's "
              f"C-level bignum arithmetic and str() formatting beat a pure-Python digit loop. "
              f"The carry-propagation approach is still the intended answer: it generalizes to "
              f"languages without bignums and is what 005 Multiply Strings requires outright.")
    else:
        print(f"  measured: carry propagation is {int_ms / carry_ms:.2f}x faster here.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
