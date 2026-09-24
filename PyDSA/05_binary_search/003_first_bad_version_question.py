"""
================================================================================
QUESTION · LeetCode 278 · First Bad Version                             [Easy]
https://leetcode.com/problems/first-bad-version/
================================================================================
You are a product manager and currently leading a team to develop a new
product. Since each version is developed based on the previous version, all
the versions after a bad version are also bad.

Suppose you have `n` versions [1, 2, ..., n] and you want to find out the
first bad one, which causes all the following ones to be bad.

You are given an API `bool isBadVersion(version)` which returns whether
`version` is bad. Implement a function to find the first bad version. You
should minimize the number of calls to the API.

Example 1:
    Input:  n = 5, bad = 4
    Output: 4
    (calls: isBadVersion(3) -> false, isBadVersion(5) -> true,
     isBadVersion(4) -> true, so 4 is the first bad version)

Example 2:
    Input:  n = 1, bad = 1
    Output: 1

Constraints:
    1 <= bad <= n <= 2^31 - 1
================================================================================
"""


# The isBadVersion API is provided in this module as a module-level function
# (in a real interview, it is provided externally / pre-defined).
def isBadVersion(version: int) -> bool:
    raise NotImplementedError  # replaced per-test-case below


class Solution:
    def firstBadVersion(self, n: int) -> int:
        # YOUR CODE HERE
        # Call the *module-level* isBadVersion(version) — do not reimplement it.
        pass


# ==============================================================================
# TESTS — run:  python 003_first_bad_version_question.py
# ==============================================================================
import sys

CASES = [
    (5, 4),
    (1, 1),
    (2, 1),
    (2, 2),
    (10, 1),
    (10, 10),
    (2000000000, 1500000000),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    module = sys.modules[__name__]
    for n, bad in CASES:
        module.isBadVersion = lambda v, _bad=bad: v >= _bad
        got = sol.firstBadVersion(n)
        ok = got == bad
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:<12} bad={bad:<12} -> {got}  (want {bad})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
