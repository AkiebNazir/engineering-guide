"""
================================================================================
SOLUTION · LeetCode 118 · Pascal's Triangle                          [Easy]
https://leetcode.com/problems/pascals-triangle/
================================================================================

THE CORE IDEA
--------------
row[i][j] MEANS "the value at row i, column j of Pascal's triangle". Every
row's first and last entry is 1; every interior entry is the sum of the two
entries directly above it in the PREVIOUS row:

    row[i][0] = row[i][i] = 1
    row[i][j] = row[i-1][j-1] + row[i-1][j]     for 0 < j < i

Building row i only ever reads row i-1 -- a 1D "fixed window of 1" DP
applied once per row, exactly like problems 002/003 reach back a fixed
number of INDICES, this reaches back a fixed number of ROWS.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion via the binomial-coefficient formula, price it,
don't ship it): row[i][j] = C(i, j) = i! / (j! * (i-j)!), computed via
recursive Pascal's identity C(n,k) = C(n-1,k-1) + C(n-1,k) without caching.
Same repeated-subproblem blowup as every problem in this folder -- C(n-1,k)
is recomputed from scratch by multiple parent calls. O(2^n) in the worst
case for a single entry, and numRows^2 entries needed overall.

Approach 1 (memoized binomial coefficient) [`generate_memo`] -- cache
C(n, k) the first time it's computed via the recursive identity. Collapses
to O(numRows^2) distinct (n, k) pairs.

Approach 2 (row-by-row build) [chosen] -- build each row directly from the
previous row with a simple left-to-right scan; no recursion, no
coefficient math needed at all. O(numRows^2) time and space (unavoidable,
that's the size of the output), and it is simpler AND faster than the
binomial-coefficient approaches because Python's factorial/big-int
arithmetic in C(n,k) is more expensive per cell than one integer add.


================================================================================
STEP BY STEP TRACE
================================================================================
numRows = 5

row 0:                 [1]
row 1:                [1,1]
row 2:              [1, (1+1)=2, 1]           = [1,2,1]
row 3:            [1, (1+2)=3, (2+1)=3, 1]    = [1,3,3,1]
row 4:         [1, (1+3)=4, (3+3)=6, (3+1)=4, 1] = [1,4,6,4,1]

Building row 4 from row 3 = [1,3,3,1]:
    new_row = [1]
    j=1: new_row.append(row3[0] + row3[1]) = 1+3 = 4  -> [1,4]
    j=2: new_row.append(row3[1] + row3[2]) = 3+3 = 6  -> [1,4,6]
    j=3: new_row.append(row3[2] + row3[3]) = 3+1 = 4  -> [1,4,6,4]
    new_row.append(1)                                  -> [1,4,6,4,1]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time         Space       Mutates input?
    ------------------------------  -----------  ----------  --------------
    Naive recursive binomial coef.  O(2^numRows) O(numRows)  n/a (no input array)
    Memoized binomial coefficient   O(numRows^2) O(numRows^2) n/a
    Row-by-row build [chosen]       O(numRows^2) O(numRows^2) n/a


================================================================================
EDGE CASES
================================================================================
    numRows == 1        -> output is just [[1]], the loop that builds
                            subsequent rows never runs.
    numRows == 2         -> exercises exactly one "build row from previous
                            row" step with zero interior entries (row 1 is
                            entirely two 1s, no j-loop iterations happen).
    numRows == 30 (max)   -> largest input; confirms performance is fine at
                            the given bound (900 total entries, trivial).


================================================================================
COMMON MISTAKES
================================================================================
1. Off-by-one in the interior loop: iterating `range(1, i)` when the row
   has length i+1 misses the correct interior range, or iterating one too
   far and indexing past the previous row.
2. Aliasing rows: appending the SAME list object into multiple rows (e.g.
   reusing `prev_row` as `row[i]` directly instead of building a fresh
   list) causes later mutations to corrupt earlier rows.
3. Recomputing every row from scratch via the binomial coefficient formula
   instead of reusing the previous row -- correct, but needlessly slow and
   prone to factorial-overflow-style bugs in languages without big ints
   (not a concern in Python, but worth naming as the wrong instinct).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you return just row k without building the whole triangle?" -> yes
  (LC 119, Pascal's Triangle II) -- either roll a single array in place,
  updating right-to-left so you don't overwrite values you still need, or
  use the closed-form C(k, j) directly.
- "Can you build a row in O(1) extra space beyond the row itself?" -> yes,
  update in place from right to left: row[j] += row[j-1].
- "How would you compute a single entry C(n, k) for huge n without
  building the triangle?" -> multiplicative formula for the binomial
  coefficient, O(k) time, O(1) extra space.


================================================================================
RELATED PROBLEMS
================================================================================
- Pascal's Triangle II (LC 119) -- single-row variant, in-place O(1) extra
  space version of the same recurrence.
- 013 Longest Increasing Subsequence -- another problem where "1D" hides a
  row-by-row / index-by-index structure.
================================================================================
"""

import time
from math import comb
from typing import List


class Solution:
    def generate(self, numRows: int) -> List[List[int]]:
        triangle: List[List[int]] = []
        for i in range(numRows):
            row = [1] * (i + 1)
            for j in range(1, i):
                row[j] = triangle[i - 1][j - 1] + triangle[i - 1][j]
            triangle.append(row)
        return triangle


def generate_memo(numRows: int) -> List[List[int]]:
    memo = {}

    def c(n: int, k: int) -> int:
        if k == 0 or k == n:
            return 1
        if (n, k) in memo:
            return memo[(n, k)]
        memo[(n, k)] = c(n - 1, k - 1) + c(n - 1, k)
        return memo[(n, k)]

    return [[c(i, j) for j in range(i + 1)] for i in range(numRows)]


def generate_naive_binomial(numRows: int) -> List[List[int]]:
    def c(n: int, k: int) -> int:
        if k == 0 or k == n:
            return 1
        return c(n - 1, k - 1) + c(n - 1, k)

    return [[c(i, j) for j in range(i + 1)] for i in range(numRows)]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (5, [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]),
        (1, [[1]]),
        (2, [[1], [1, 1]]),
        (3, [[1], [1, 1], [1, 2, 1]]),
    ]
    for numRows, want in cases:
        got = sol.generate(numRows)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  numRows={numRows}  -> {got}  (want {want})")
        assert generate_memo(numRows) == want
        # cross-check against math.comb as an independent oracle
        for i, row in enumerate(got):
            for j, v in enumerate(row):
                assert v == comb(i, j)

    print()
    print("RUNTIME DEMO -- naive recursive binomial coefficient vs row-by-row build")
    print("-" * 72)
    for n in (10, 18, 24):
        t0 = time.perf_counter()
        naive_result = generate_naive_binomial(n)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        fast_result = sol.generate(n)
        fast_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == fast_result
        print(f"numRows={n:3d}  naive_binomial={naive_ms:9.3f} ms   "
              f"row_by_row={fast_ms:7.4f} ms   ratio={naive_ms / max(fast_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
