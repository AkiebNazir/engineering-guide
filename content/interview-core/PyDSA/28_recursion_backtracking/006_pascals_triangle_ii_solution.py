"""
================================================================================
SOLUTION · LeetCode 119 · Pascal's Triangle II                            [Easy]
https://leetcode.com/problems/pascals-triangle-ii/
================================================================================

THE CORE IDEA
--------------
`row(n)` is built entirely from `row(n-1)`: slide a window of two over the
smaller row and sum, bookended by 1s. The base case `row(0) = [1]` needs no
derivation. This is the first problem in the folder where the value flowing
back UP the call stack is a whole list, not a scalar — the "combine" step
constructs a new list from the previous level's list instead of just adding
a number to it.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, ONE NEW LIST PER LEVEL — `row(n) = combine(row(n-1))`.
   O(n^2) time (row k costs O(k) to build, summed over n rows), O(n^2) space
   because every intermediate row list is kept alive simultaneously on the
   call stack (not reused/discarded) — this is the version below.
2. ITERATIVE, IN-PLACE RIGHT-TO-LEFT — start `row = [1]`; for each new row
   index, walk the CURRENT row from the right end backward, doing
   `row[i] += row[i-1]`, then append a trailing 1... actually the standard
   trick inserts a leading placeholder and updates right-to-left so no value
   needed later gets overwritten early. O(n^2) time, O(n) space — the
   intended interview answer.
3. MATH (binomial coefficients) — `row(n)[k] = C(n, k) = n! / (k!(n-k)!)`,
   computable iteratively as `C(n,k) = C(n,k-1) * (n-k+1) / k`. O(n) time,
   O(n) space, no recursion. Priced as a follow-up.


================================================================================
STEP BY STEP TRACE — row(4)
================================================================================
    call row(4)
      call row(3)
        call row(2)
          call row(1)
            call row(0) -> base case, return [1]
          row(1): combine([1]) -> [1, 1]
        row(2): combine([1,1]) -> [1, 2, 1]
      row(3): combine([1,2,1]) -> [1, 3, 3, 1]
    row(4): combine([1,3,3,1]) -> [1, 4, 6, 4, 1]

Combine step for row(4): prev = [1,3,3,1]
    result[0]   = 1                      (left bookend)
    result[i]   = prev[i-1] + prev[i]     for i in 1..len(prev)-1
                = 1+3, 3+3, 3+1 = 4, 6, 4
    result[-1]  = 1                      (right bookend)
    -> [1, 4, 6, 4, 1]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time      Space     Mutates input?  Note
    ------------------------------  --------  --------  ---------------  --------------------------------
    Recursive (new list/level)     O(n^2)    O(n^2)    no               every row kept alive on call stack
    Iterative in-place              O(n^2)    O(n)      no (new row)     the standard interview answer
    Math (binomial coefficients)   O(n)      O(n)      no               no recursion at all


================================================================================
EDGE CASES
================================================================================
    rowIndex = 0  -> [1]              the base case itself; must not recurse
                                       further or index out of range.
    rowIndex = 1  -> [1, 1]           smallest case that actually exercises
                                       the combine step (one call above base).
    rowIndex = 33 -> upper constraint bound; values grow but stay in Python's
                                       arbitrary-precision int range (unlike
                                       a fixed-width language, no overflow risk).


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the bookending 1s and only summing adjacent pairs — produces a
   row that's 2 elements too short.
2. Off-by-one in the pair-summing range: iterating `range(len(prev))` instead
   of `range(1, len(prev))` for the middle elements double-counts or
   index-errors at the ends.
3. Mutating and returning the SAME list object across recursive levels
   (e.g. building `row(n)` by appending onto `row(n-1)` in place) — corrupts
   the sub-answer a different branch or a later print might still reference.
4. Confusing rowIndex (0-indexed) with "row number" (1-indexed) from math
   textbooks — `getRow(3)` is `[1,3,3,1]`, the 4th row if counting from 1.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do this with O(rowIndex) extra space instead of O(rowIndex^2)?
A: Yes — the iterative in-place version only ever keeps one row alive,
   updating it right-to-left so a value isn't overwritten before it's read.

Q: Why right-to-left and not left-to-right for the in-place update?
A: `row[i] += row[i-1]` needs `row[i-1]`'s OLD (pre-update) value. Going
   left-to-right would have already overwritten `row[i-1]` by the time
   `row[i]` reads it. Going right-to-left, `row[i-1]` hasn't been touched yet.

Q: Is there a closed-form way to get any single entry without building the
   whole row?
A: Yes, `C(rowIndex, k)` directly via the binomial coefficient formula —
   useful if only one entry is needed, not asymptotically better for the
   whole row.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 118  Pascal's Triangle           — build all rows 0..n, not just one.
    Topic 09 Combinations               — same C(n,k) values, framed as a
                                          counting/backtracking problem.
    Topic 28, 011 Unique BST count      — another "list built level-by-level
                                          from combining smaller results".
================================================================================
"""

from typing import List


class Solution:
    def getRow(self, rowIndex: int) -> List[int]:
        """Recursive, one new list per level. O(n^2) time/space."""
        if rowIndex == 0:
            return [1]
        prev = self.getRow(rowIndex - 1)
        row = [1] * (rowIndex + 1)
        for i in range(1, rowIndex):
            row[i] = prev[i - 1] + prev[i]
        return row

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def getRow_iterative_inplace(self, rowIndex: int) -> List[int]:
        """Iterative, right-to-left in place. O(n^2) time, O(n) space."""
        row = [1]
        for _ in range(rowIndex):
            row.append(1)
            for i in range(len(row) - 2, 0, -1):
                row[i] += row[i - 1]
        return row

    def getRow_math(self, rowIndex: int) -> List[int]:
        """Binomial coefficients built iteratively. O(n) time/space."""
        row = [1] * (rowIndex + 1)
        for k in range(1, rowIndex + 1):
            row[k] = row[k - 1] * (rowIndex - k + 1) // k
        return row


# ==============================================================================
# TESTS — run:  python 006_pascals_triangle_ii_solution.py
# ==============================================================================
CASES = [
    (0, [1]),
    (1, [1, 1]),
    (2, [1, 2, 1]),
    (3, [1, 3, 3, 1]),
    (4, [1, 4, 6, 4, 1]),
    (5, [1, 5, 10, 10, 5, 1]),
    (6, [1, 6, 15, 20, 15, 6, 1]),
    (33, None),  # upper bound: just confirm it runs and has the right length/symmetry
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive          ", sol.getRow),
        ("iterative in-place ", sol.getRow_iterative_inplace),
        ("math (binomial)    ", sol.getRow_math),
    ]

    for name, fn in impls:
        ok = True
        for rowIndex, expected in CASES:
            got = fn(rowIndex)
            if expected is not None:
                ok &= got == expected
            else:
                ok &= len(got) == rowIndex + 1 and got == got[::-1] and got[0] == got[-1] == 1
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- symmetry check: every row is a palindrome (measured live) ---")
    for rowIndex in (3, 4, 10, 20):
        row = sol.getRow(rowIndex)
        is_palindrome = row == row[::-1]
        print(f"  row({rowIndex:>2}) palindrome? {is_palindrome}  len={len(row)}")
        all_ok &= is_palindrome

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
