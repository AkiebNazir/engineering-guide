"""
================================================================================
SOLUTION · LeetCode 470 · Implement Rand10() Using Rand7()          [Medium]
https://leetcode.com/problems/implement-rand10-using-rand7/
================================================================================

THE CORE IDEA
--------------
Rejection Sampling. 
If we want a random number between 1 and 10 uniformly, we can generate a random
number in a larger uniform range (like 1 to 49), map the first 40 outcomes 
uniformly to 1..10, and simply "reject" and try again if we hit an outcome 
above 40. 

To generate a uniform number between 1 and 49 using rand7(), we can conceptualize
it as a 7x7 grid. The row is chosen by `rand7()` and the column is chosen by 
another `rand7()`. The formula `idx = (row - 1) * 7 + col` maps every unique 
pair `(row, col)` to a unique integer from 1 to 49. Since both row and col 
are uniform, every number from 1 to 49 is equally likely.

If `idx` is between 1 and 40, we map it to 1..10 by doing `(idx - 1) % 10 + 1`.
If `idx` is 41..49, we reject it and loop again. 

EXPECTED CALLS (MATH)
---------------------
The probability of a success (an index <= 40) is 40/49.
The number of attempts follows a geometric distribution where p = 40/49.
The expected number of attempts E(x) is 1/p = 49/40 = 1.225.
Since each attempt costs two calls to rand7(), the expected calls is 2.45.
"""

import random

def rand7() -> int:
    return random.randint(1, 7)

class Solution:
    def rand10(self) -> int:
        while True:
            row = rand7()
            col = rand7()
            
            # This generates a uniform random integer from 1 to 49
            idx = (row - 1) * 7 + col
            
            # If the number is within our desired 1 to 40 uniform range, map it!
            if idx <= 40:
                return (idx - 1) % 10 + 1


# ---------------------------------------------------------------------------
# Tests. Randomness can't be checked with fixed expected outputs, so these
# check the two properties that matter, on a seeded generator:
#   1. uniformity  - a chi-square test over 200,000 draws;
#   2. cost        - the average number of rand7() calls is close to 2.45.
# A naive answer is run through the same test to show it fails it.
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
            print(f"FAIL  rand10 returned {v}, outside 1..10")
            break
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

    # The tempting shortcut: add two rand7() results and take the sum mod 10.
    # Sums of two dice are not uniform (7 is common, 2 and 14 are rare).
    naive = [0] * 10
    for _ in range(draws):
        naive[(counted_rand7() + counted_rand7()) % 10] += 1
    chi2_naive = _chi_square(naive, draws)
    ok = chi2_naive > CHI2_CRITICAL_9DF
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  the naive (rand7() + rand7()) % 10 is rejected: "
          f"chi-square {chi2_naive:,.0f}, far above {CHI2_CRITICAL_9DF}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
