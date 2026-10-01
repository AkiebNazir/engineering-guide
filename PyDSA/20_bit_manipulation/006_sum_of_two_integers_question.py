"""
================================================================================
QUESTION · LeetCode 371 · Sum of Two Integers                        [Medium]
https://leetcode.com/problems/sum-of-two-integers/
================================================================================

PROBLEM
-------
Given two integers a and b, return the sum of the two integers without
using the operators `+` and `-`.


EXAMPLES
--------
Example 1:
    Input:  a = 1, b = 2
    Output: 3

Example 2:
    Input:  a = 2, b = 3
    Output: 5


CONSTRAINTS
-----------
    -1000 <= a, b <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Addition without `+` means building it from bitwise primitives: XOR gives
the sum of two bits IGNORING carry (`1^1=0`, `1^0=1`, `0^0=0` -- exactly
what addition-mod-2 looks like per bit), and AND-then-shift-left-by-1
gives the CARRY that addition would have produced at each position. Add
those two partial results together the same way, repeatedly, until there
is no carry left.

    while b != 0:
        carry = (a & b) << 1
        a = a ^ b
        b = carry
    return a

THIS PROBLEM IS THE TOPIC'S DEFINING PYTHON GOTCHA. Python ints are
arbitrary precision -- there is no 32-bit wraparound, and negative numbers
are conceptually an INFINITE string of leading 1-bits, not a fixed 32-bit
pattern. Run the loop above on two negative numbers, or on numbers whose
sum should be negative, and it can literally never terminate (carry keeps
producing new 1-bits forever in an unbounded negative direction) or
produce a value that "looks like" the right magnitude but has the wrong
sign, because nothing ever wraps back into a 32-bit two's-complement box.
The fix: mask EVERY intermediate value to exactly 32 bits with
`& 0xFFFFFFFF`, then at the very end, if bit 31 is set (meaning the
32-bit pattern represents a negative number), convert back to Python's
native negative-int representation by subtracting `1 << 32`.

PROGRESSIVE HINTS
------------------
Hint 1: XOR gives bitwise sum without carry; AND-and-shift gives the
        carry. Repeat until carry is 0.
Hint 2: Without a width limit, this loop can run forever on negative
        inputs in Python (unlike C/Java, where 32-bit overflow just wraps
        and the loop is guaranteed to terminate). Mask every value to
        32 bits with `& 0xFFFFFFFF` after every operation.
Hint 3: At the end, `a` is a 32-bit UNSIGNED pattern. If bit 31 is set
        (`a >= 0x80000000`), reinterpret it as negative:
        `a = ~(a ^ 0xFFFFFFFF)`, equivalently `a - (1 << 32)`.

COMPLEXITY TARGET
------------------
    Time:  O(1) -- bounded by the fixed 32-bit width
    Space: O(1)
================================================================================
"""


class Solution:
    def getSum(self, a: int, b: int) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (1, 2, 3),
        (2, 3, 5),
        (-1, 1, 0),
        (-2, -3, -5),
        (0, 0, 0),
        (-1000, 1000, 0),
        (1000, 1000, 2000),
        (-5, -7, -12),
    ]
    for a, b, want in cases:
        got = sol.getSum(a, b)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  a={a:>6} b={b:>6}  -> {got:>6}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
