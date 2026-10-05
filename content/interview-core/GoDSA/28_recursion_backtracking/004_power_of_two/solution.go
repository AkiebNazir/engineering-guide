package main

import "fmt"

/*
================================================================================
LeetCode 231 · Power of Two                                               [Easy]
https://leetcode.com/problems/power-of-two/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given an integer `n`, return `true` if it is a power of two. Otherwise,
return `false`.

An integer `n` is a power of two if there exists an integer `x` such that
`n == 2^x`.

EXAMPLES
--------
Example 1:
    Input:  n = 1
    Output: true
    Explanation: 2^0 = 1

Example 2:
    Input:  n = 16
    Output: true
    Explanation: 2^4 = 16

Example 3:
    Input:  n = 3
    Output: false

CONSTRAINTS
-----------
    -2^31 <= n <= 2^31 - 1

FOLLOW-UP (stated on LeetCode)
-------------------------------
Could you solve it without loops/recursion?

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is 001's halving idea, repurposed into a yes/no predicate instead of a
step counter. A power of two, repeatedly halved, always eventually reaches
exactly 1 WITHOUT ever landing on an odd number along the way (except 1
itself). Any non-power-of-two either isn't even divisible by 2 cleanly at
some point, or is <= 0 to begin with.

    isPowerOfTwo(n):
        if n <= 0: return False                        <- base case: impossible
        if n == 1: return True                          <- base case: 2^0
        if n % 2 != 0: return False                     <- base case: odd, not 1 -> dead end
        return isPowerOfTwo(n // 2)                      <- keep halving

Three base cases here, not one — this is the first problem in the folder
where "am I done?" splits into multiple distinct terminating conditions
(success, and two different flavors of failure) rather than a single
clean stopping point.

WHAT TO THINK ABOUT
--------------------
1. List the THREE base cases separately before writing any code: n <= 0,
   n == 1, and "n is even but not divisible cleanly" — wait, re-examine:
   what actually makes a number FAIL to be a power of two mid-recursion?
2. Why must `n <= 0` be checked, given the constraint allows negative n?
   (Negative numbers and 0 are never powers of two; `2^x` is always
   positive for integer x.)
3. Is there a bit-trick shortcut? (`n > 0 and (n & (n - 1)) == 0` — a power
   of two has exactly one set bit, and `n - 1` flips it and everything
   below it, so `n & (n-1)` is 0 only for powers of two, given n > 0.)
4. How does this recursion's "multiple ways to fail" shape connect to
   005 (Power of Three), where you can't use the bit trick at all?

PROGRESSIVE HINTS
------------------
Hint 1: `n <= 0` is never a power of two — return False immediately.
Hint 2: `n == 1` (2^0) is the success base case — return True.
Hint 3: If `n` is odd and not 1, it can never become 1 by halving — return
        False. Otherwise recurse on `n // 2`.
Hint 4: The O(1) bit trick: `n > 0 and (n & (n - 1)) == 0`.

COMPLEXITY TARGET
------------------
    Recursive halving: O(log n) time, O(log n) space (call stack)
    Bit trick:          O(1) time, O(1) space
================================================================================
*/

func main() {
	fmt.Println("Solution for Power of Two not implemented yet")
}
