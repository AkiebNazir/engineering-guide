"""
================================================================================
LeetCode 258 · Add Digits                                                 [Easy]
https://leetcode.com/problems/add-digits/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given an integer `num`, repeatedly add all its digits until the result has
only one digit, and return it.

EXAMPLES
--------
Example 1:
    Input:  num = 38
    Output: 2
    Explanation: 3 + 8 = 11.  1 + 1 = 2.  Since 2 has only one digit, return it.

Example 2:
    Input:  num = 0
    Output: 0

CONSTRAINTS
-----------
    0 <= num <= 2^31 - 1

FOLLOW-UP (stated on LeetCode)
-------------------------------
Could you do it without any loop/recursion in O(1) runtime?

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is TWO recursions stacked: an inner recursion (or loop) that sums the
digits of a single number, and an outer recursion that re-applies the digit
sum until only one digit remains.

    digitSum(n):
        if n < 10: return n                        <- base case: single digit
        return n % 10 + digitSum(n // 10)           <- peel off the last digit

    addDigits(num):
        if num < 10: return num                     <- base case: already 1 digit
        return addDigits(digitSum(num))              <- re-apply until it sticks

Both recursions shrink their input: `digitSum` peels a digit off with
`// 10` each call (a NEW way to shrink a number vs. 001's halve/subtract),
and `addDigits` re-applies `digitSum` until the result is a single digit —
each application strictly reduces the number of digits (for any num >= 10,
its digit sum is always < num), so this terminates.

WHAT TO THINK ABOUT
--------------------
1. What is the exact base case for "already a single digit"? (`n < 10`
   covers 0-9, all single digits including 0.)
2. `digitSum` and `addDigits` are two SEPARATE recursions with two SEPARATE
   base cases — can you state each one without confusing them?
3. Why does repeatedly taking the digit sum always eventually reach a
   single digit, and never loop forever? (Every application strictly
   shrinks the number, once it has 2+ digits.)
4. The O(1) follow-up uses modular arithmetic on 9 (the "digital root")
   — this is the mathematical fact that a number's repeated digit sum
   always equals `1 + (num - 1) % 9` for num > 0, and 0 for num == 0. Name
   it as a follow-up; the point of this file is the two-layer recursion.

PROGRESSIVE HINTS
------------------
Hint 1: Write `digitSum(n)` first, independently: base case `n < 10`,
        recursive case `n % 10 + digitSum(n // 10)`.
Hint 2: `addDigits(num)`'s base case is also `num < 10`; otherwise call
        `addDigits(digitSum(num))` — passing the SUM back into the SAME
        function, not into `digitSum` directly.
Hint 3: Trace `addDigits(38)`: `digitSum(38) = 11`, `addDigits(11)`:
        `digitSum(11) = 2`, `addDigits(2)`: base case, return 2.
Hint 4: The O(1) closed form: `0 if num == 0 else 1 + (num - 1) % 9`.

COMPLEXITY TARGET
------------------
    Two-layer recursion: O(log num) per digitSum call, O(log(log num))-ish
                          outer applications (digit sums shrink fast) — in
                          practice O(log num) total, O(log num) stack depth
    O(1) digital root:   O(1) time, O(1) space
================================================================================
"""


class Solution:
    def addDigits(self, num: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 003_add_digits_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        (0, 0), (1, 1), (9, 9), (10, 1), (38, 2), (12345, 6), (2**31 - 1, 1),
    ]
    passed = 0
    for num, expected in cases:
        got = sol.addDigits(num)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  addDigits({num}) -> {got}  (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
