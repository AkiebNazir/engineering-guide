"""
================================================================================
QUESTION · LeetCode 470 · Implement Rand10() Using Rand7()          [Medium]
https://leetcode.com/problems/implement-rand10-using-rand7/
================================================================================

PROBLEM
-------
Given the API `rand7()` that generates a uniform random integer in the range
`[1, 7]`, write a function `rand10()` that generates a uniform random integer
in the range `[1, 10]`. You can only call the API `rand7()`, and you
shouldn't call any other API. Please do not use a language's built-in
random API.

Each integer should have equal probability of returning.

Follow up:
- What is the expected value for the number of calls to `rand7()`?
- Could you minimize the number of calls to `rand7()`?

EXAMPLE
-------
Input: n = 1
Output: [2]
Explanation: Calling rand10() once returns a random integer between 1 and 10.
"""

import random

def rand7() -> int:
    return random.randint(1, 7)

class Solution:
    def rand10(self) -> int:
        pass


# ---------------------------------------------------------------------------
# Tests. Randomness can't be checked with fixed expected outputs, so these
# check the two properties that matter, on a seeded generator:
#   1. uniformity  - a chi-square test over 200,000 draws;
#   2. cost        - the average number of rand7() calls is close to 2.45.
# ---------------------------------------------------------------------------
CHI2_CRITICAL_9DF = 21.67        # 1% significance, 9 degrees of freedom


def _chi_square(counts, draws):
    expected = draws / 10
    return sum((c - expected) ** 2 / expected for c in counts)


def run_tests():
    global rand7
    all_ok = True
    calls = 0
    rng = random.Random(470)

    def counted_rand7():
        nonlocal calls
        calls += 1
        return rng.randint(1, 7)

    rand7 = counted_rand7            # Solution.rand10 looks rand7 up at call time
    sol, draws = Solution(), 200_000
    counts = [0] * 10
    for _ in range(draws):
        v = sol.rand10()
        if not isinstance(v, int) or not 1 <= v <= 10:
            all_ok = False
            print(f"FAIL  rand10 returned {v!r}, outside 1..10")
            print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")
            return
        counts[v - 1] += 1
    chi2 = _chi_square(counts, draws)
    ok = chi2 < CHI2_CRITICAL_9DF
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  uniform: chi-square {chi2:.2f} < {CHI2_CRITICAL_9DF} "
          f"(counts from {min(counts):,} to {max(counts):,} per value)")

    per_call = calls / draws
    ok = abs(per_call - 2.45) < 0.02
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  cost: {per_call:.3f} rand7() calls per rand10() "
          f"(expected 49/40 x 2 = 2.45)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
