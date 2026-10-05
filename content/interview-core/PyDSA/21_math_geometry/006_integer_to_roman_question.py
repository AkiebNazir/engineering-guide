"""
================================================================================
QUESTION · LeetCode 12 · Integer to Roman                          [Medium]
https://leetcode.com/problems/integer-to-roman/
================================================================================

Roman numerals are represented by seven symbols:

    Symbol  Value
    I       1
    V       5
    X       10
    L       50
    C       100
    D       500
    M       1000

Symbols are usually written largest to smallest, left to right. However,
there are six special "subtractive" cases:
    - I before V or X: 4 = IV, 9 = IX
    - X before L or C: 40 = XL, 90 = XC
    - C before D or M: 400 = CD, 900 = CM

Given an integer `num`, convert it to a Roman numeral.

Example 1:
    Input:  num = 3749
    Output: "MMMDCCXLIX"
    Explanation: 3000 = MMM, 700 = DCC, 40 = XL, 9 = IX

Example 2:
    Input:  num = 58
    Output: "LVIII"
    Explanation: 50 = L, 8 = VIII

Example 3:
    Input:  num = 1994
    Output: "MCMXCIV"
    Explanation: 1000 = M, 900 = CM, 90 = XC, 4 = IV

Constraints:
    1 <= num <= 3999
================================================================================
"""


class Solution:
    def intToRoman(self, num: int) -> str:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    pass


if __name__ == "__main__":
    run_tests()
