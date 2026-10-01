"""
================================================================================
QUESTION · LeetCode 191 · Number of 1 Bits                           [Easy]
https://leetcode.com/problems/number-of-1-bits/
================================================================================

PROBLEM
-------
Write a function that takes the binary representation of an unsigned
integer and returns the number of '1' bits it has (the Hamming weight).

Note: in some languages, such as Java, there is no unsigned integer type.
In this case, the input is given as a signed integer type and should be
treated as if it were unsigned (all 32 bits participate).


EXAMPLES
--------
Example 1:
    Input:  n = 00000000000000000000000000001011  (11)
    Output: 3
    (the input has binary representation 00000000000000000000000000001011)

Example 2:
    Input:  n = 00000000000000000000000010000000  (128)
    Output: 1

Example 3:
    Input:  n = 11111111111111111111111111111101  (4294967293, unsigned)
    Output: 31


CONSTRAINTS
-----------
    The input must be a binary string of length 32.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the canonical use of `n & (n - 1)`: it clears the LOWEST set bit
and leaves everything else untouched. Repeating that operation and counting
how many times you can do it before n becomes 0 gives the Hamming weight in
O(popcount) iterations instead of O(32) fixed shifts.

Python has no unsigned-int type, and `n` here is given as a non-negative
integer (LeetCode passes it as an `int` already interpreted as unsigned),
so no 32-bit masking is needed for THIS problem specifically -- contrast
with 004 Reverse Bits and 006/007, where masking is mandatory. Treat that
contrast as part of the lesson: know when masking is and isn't needed.

PROGRESSIVE HINTS
------------------
Hint 1: Right-shifting and checking `& 1` 32 times always works but does
        wasted work when most bits are 0.
Hint 2: `n & (n - 1)` clears exactly the lowest set bit. How many times can
        you apply that before n is 0?
Hint 3: Loop `count = 0; while n: n &= n - 1; count += 1`.

COMPLEXITY TARGET
------------------
    Time:  O(k) where k = number of set bits (O(32) worst case either way)
    Space: O(1)
================================================================================
"""


class Solution:
    def hammingWeight(self, n: int) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (0b1011, 3),
        (0b10000000, 1),
        (4294967293, 31),  # 11111111111111111111111111111101
        (0, 0),
        (1, 1),
        ((1 << 32) - 1, 32),  # all 32 bits set
    ]
    for n, want in cases:
        got = sol.hammingWeight(n)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:>12} (0b{n:b})  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
