"""
================================================================================
QUESTION · LeetCode 374 · Guess Number Higher or Lower                  [Easy]
https://leetcode.com/problems/guess-number-higher-or-lower/
================================================================================
We are playing the Guess Game. The game is as follows:

I pick a number from 1 to n. You have to guess which number I picked.

Every time you guess wrong, I tell you whether the number I picked is higher
or lower than your guess.

You call a pre-defined API `int guess(int num)`, which returns three
possible results:
    -1: your guess is higher than the number I picked (num > pick)
     1: your guess is lower than the number I picked (num < pick)
     0: your guess is equal to the number I picked (num == pick)

Return the number that I picked.

Example 1:
    Input:  n = 10, pick = 6
    Output: 6

Example 2:
    Input:  n = 1, pick = 1
    Output: 1

Example 3:
    Input:  n = 2, pick = 1
    Output: 1

Constraints:
    1 <= n <= 2^31 - 1
    1 <= pick <= n
================================================================================
"""

import sys


def guess(num: int) -> int:
    raise NotImplementedError  # replaced per-test-case below


class Solution:
    def guessNumber(self, n: int) -> int:
        # YOUR CODE HERE
        # Call the *module-level* guess(num) — do not reimplement it.
        pass


# ==============================================================================
# TESTS — run:  python 004_guess_number_higher_or_lower_question.py
# ==============================================================================
CASES = [
    (10, 6),
    (1, 1),
    (2, 1),
    (2, 2),
    (2126753390, 1702766719),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    module = sys.modules[__name__]
    for n, pick in CASES:
        def make_guess(_pick):
            def _guess(num):
                if num > _pick:
                    return -1
                if num < _pick:
                    return 1
                return 0
            return _guess
        module.guess = make_guess(pick)
        got = sol.guessNumber(n)
        ok = got == pick
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:<12} pick={pick:<12} -> {got}  (want {pick})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
