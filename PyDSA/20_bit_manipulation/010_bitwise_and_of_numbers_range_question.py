"""
================================================================================
QUESTION · LeetCode 201 · Bitwise AND of Numbers Range                [Medium]
https://leetcode.com/problems/bitwise-and-of-numbers-range/
================================================================================

PROBLEM
-------
Given two integers `left` and `right` that represent the range
[left, right], return the bitwise AND of all numbers in this range,
inclusive.


EXAMPLES
--------
Example 1:
    Input:  left = 5, right = 7
    Output: 4
    (5 & 6 & 7 = 0b101 & 0b110 & 0b111 = 0b100 = 4)

Example 2:
    Input:  left = 0, right = 0
    Output: 0

Example 3:
    Input:  left = 1, right = 2147483647
    Output: 0


CONSTRAINTS
-----------
    0 <= left <= right <= 2^31 - 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Brute-force AND-ing every number from left to right is correct but can be
O(right - left), up to 2^31 iterations -- far too slow. The key insight:
AND-ing a whole RANGE of consecutive integers together zeroes out any bit
position where the numbers in the range DISAGREE (any 0 anywhere kills
that bit for the whole AND). As soon as left != right, the numbers in the
range are guaranteed to disagree on every bit BELOW the highest bit at
which left and right first differ (because counting from left to right
necessarily flips through every combination of those lower bits at some
point, including at least one 0). So the answer is exactly the COMMON
PREFIX of left and right's binary representations, with all lower
(disagreeing) bits zeroed out.

Find that common prefix by right-shifting both left and right together
until they become equal (that's the point at which they agree on every
remaining bit), counting the shifts, then shifting the common value back
left by that same count to restore the zeroed lower bits.

PROGRESSIVE HINTS
------------------
Hint 1: Once left != right, at least one number in [left, right] will
        have a 0 in every bit position below where left and right first
        differ -- those bits are guaranteed to AND to 0.
Hint 2: Keep right-shifting both left and right by 1, in lockstep,
        until they're equal -- that's their common binary prefix.
Hint 3: Count how many shifts it took, then shift the (now-equal) value
        back left by that count to restore the prefix's original bit
        positions (with everything below it correctly zeroed).

COMPLEXITY TARGET
------------------
    Time:  O(log(right)) -- at most 32 shifts
    Space: O(1)
================================================================================
"""


class Solution:
    def rangeBitwiseAnd(self, left: int, right: int) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (5, 7, 4),
        (0, 0, 0),
        (1, 2147483647, 0),
        (5, 5, 5),
        (26, 30, 24),   # 11010,11011,11100,11101,11110 -> common prefix 11000=24
        (1, 1, 1),
        (0, 1, 0),
    ]
    for left, right, want in cases:
        got = sol.rangeBitwiseAnd(left, right)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  [{left},{right}]  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
