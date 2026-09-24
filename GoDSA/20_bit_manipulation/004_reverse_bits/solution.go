package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 190 · Reverse Bits                               [Easy]
https://leetcode.com/problems/reverse-bits/
================================================================================

PROBLEM
-------
Reverse bits of a given 32 bits unsigned integer.

Note:
    - Note that in some languages, such as Java, there is no unsigned
      integer type. In this case, both input and output will be given as a
      signed integer type. They should not affect your implementation, as
      the integer's internal binary representation is the same, whether it
      is signed or unsigned.
    - In Java, the compiler represents the signed integers using 2's
      complement notation. Therefore, in the example above, the input
      represents the signed integer -3 and the output represents the
      signed integer -1073741825.


EXAMPLES
--------
Example 1:
    Input:  n = 00000010100101000001111010011100
    Output: 964176192 (00111001011110000010100101000000)
    Explanation: the input binary string represents the unsigned integer
    43261596, so return 964176192 which its binary representation is the
    input string reversed.

Example 2:
    Input:  n = 11111111111111111111111111111101
    Output: 3221225471 (10111111111111111111111111111111)
    Explanation: the input binary string represents the unsigned integer
    4294967293, so return 3221225471 which its binary representation is
    the input string reversed.


CONSTRAINTS
-----------
    The input must be a binary string of length 32.

Follow up: if this function is called many times, how would you optimize
it?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is a WIDTH-FIXED problem: "32 bits" is load-bearing, not decoration.
LeetCode hands the input as a Python int that's already the correct
non-negative 32-bit value, so no masking is needed on the WAY IN. But the
OUTPUT must also be reported as exactly 32 bits reversed -- if you build
the result by shifting bits into a Python int, that int is unbounded, and
nothing stops it from silently accepting a 33rd bit if you mis-index. The
discipline that matters here is ALWAYS extracting exactly 32 input bits
(bit i via `(n >> i) & 1`, i in 0..31) and placing each at its mirrored
output position (31 - i) -- get the loop bound wrong and you get a value
that "looks like a number" but is the wrong width.

PROGRESSIVE HINTS
------------------
Hint 1: For each of the 32 bit positions i (0..31), extract bit i of n.
Hint 2: Place that bit at position (31 - i) in the result -- that's the
        "reverse" part.
Hint 3: `result |= ((n >> i) & 1) << (31 - i)` for i in range(32).

COMPLEXITY TARGET
------------------
    Time:  O(32) = O(1) -- fixed width
    Space: O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for Reverse Bits not implemented yet")
}
