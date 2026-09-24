package main

/*
================================================================================
LeetCode 326 · Power of Three                                             [Easy]
https://leetcode.com/problems/power-of-three/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given an integer `n`, return `true` if it is a power of three. Otherwise,
return `false`.

An integer `n` is a power of three if there exists an integer `x` such
that `n == 3^x`.

EXAMPLES
--------
Example 1:
    Input:  n = 27
    Output: true
    Explanation: 27 = 3^3

Example 2:
    Input:  n = 0
    Output: false

Example 3:
    Input:  n = 9
    Output: true

CONSTRAINTS
-----------
    -2^31 <= n <= 2^31 - 1

FOLLOW-UP (stated on LeetCode)
-------------------------------
Could you do it without using any loop / recursion?

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Same shape as 004 (repeatedly divide, check for exact division, three base
cases), but base 3 is deliberately chosen to remove the shortcut: there is
NO bit-trick equivalent for base 3 the way `n & (n-1)` works for base 2,
because 3 doesn't divide evenly into any power of 2 in a way that produces
a clean bitmask pattern. This forces you to feel the difference between
"a problem with a neat bit hack" and "a problem that genuinely needs
division/modulo," which is exactly the point of placing it right after 004.

    isPowerOfThree(n):
        if n <= 0: return False                        <- base case: impossible
        if n == 1: return True                          <- base case: 3^0
        if n % 3 != 0: return False                     <- base case: not divisible -> dead end
        return isPowerOfThree(n // 3)                    <- keep dividing by 3

WHAT TO THINK ABOUT
--------------------
1. Map each of 004's three base cases onto this problem directly — what
   changes, and what stays exactly the same in structure?
2. Why doesn't a bit trick exist here? (Powers of 3 don't align with
   binary representation the way powers of 2 do — there's no fixed bit
   pattern that "3^x" produces.)
3. The O(1) follow-up here is different in KIND from 004's: instead of a
   bit trick, it exploits that 3 is PRIME and int32 has a known largest
   power of 3 that fits — `n > 0 and (3**19) % n == 0` (3^19 is the
   largest power of 3 <= 2^31-1; any smaller power of 3 divides it evenly,
   and nothing else does, since 3 is prime). Name it, but recursion is
   the point of this file.
4. Why must you check `n % 3 != 0` and return False rather than assume
   the recursion always reaches n == 1 eventually?

PROGRESSIVE HINTS
------------------
Hint 1: `n <= 0` is never a power of three — return False immediately.
Hint 2: `n == 1` (3^0) is the success base case — return True.
Hint 3: If `n % 3 != 0`, it can never become 1 by dividing by 3 — return
        False. Otherwise recurse on `n // 3`.
Hint 4: The O(1) trick: the largest power of 3 representable in a signed
        32-bit int is `3**19 = 1162261467`. Any power of 3 divides it
        evenly; nothing else does (3 is prime). So: `n > 0 and
        1162261467 % n == 0`.

COMPLEXITY TARGET
------------------
    Recursive division: O(log_3 n) time, O(log_3 n) space (call stack)
    Largest-power trick: O(1) time, O(1) space
================================================================================
*/

// TODO: Implement the stub
