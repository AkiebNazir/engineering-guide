package main

/*
================================================================================
LeetCode 304 · Range Sum Query 2D - Immutable                          [Medium]
https://leetcode.com/problems/range-sum-query-2d-immutable/
Topic: 04 · Prefix Sum
================================================================================

PROBLEM
-------
Given a 2D matrix `matrix`, design a data structure that efficiently answers
MANY queries for the sum of the elements inside a rectangle, where the
rectangle is defined by its upper-left corner `(row1, col1)` and lower-right
corner `(row2, col2)`, both inclusive.

Implement the `NumMatrix` class:
    NumMatrix(matrix)                                     - constructor
    sumRegion(row1, col1, row2, col2) -> int               - the query

You must answer `sumRegion` calls efficiently, in the same spirit as the 1D
version (problem 002 in this folder, LC 303): pay a one-time preprocessing
cost in the constructor, then answer every query fast, since `sumRegion` may
be called thousands of times against the same immutable matrix.


EXAMPLES
--------
Example 1:
    Input:
        ["NumMatrix", "sumRegion", "sumRegion", "sumRegion"]
        [[[[3,0,1,4,2],[5,6,3,2,1],[1,2,0,1,5],[4,1,0,1,7],[1,0,3,0,5]]],
         [2,1,4,3], [1,1,2,2], [1,2,2,4]]
    Output:
        [null, 8, 11, 12]

    Explanation:
        NumMatrix numMatrix = new NumMatrix(
            [[3,0,1,4,2],
             [5,6,3,2,1],
             [1,2,0,1,5],
             [4,1,0,1,7],
             [1,0,3,0,5]]);
        numMatrix.sumRegion(2, 1, 4, 3);  // return 8
            (rows 2..4, cols 1..3):
                2 0 1
                1 0 1
                0 3 0    -> 2+0+1 + 1+0+1 + 0+3+0 = 8
        numMatrix.sumRegion(1, 1, 2, 2);  // return 11
        numMatrix.sumRegion(1, 2, 2, 4);  // return 12


CONSTRAINTS
-----------
    m == matrix.length
    n == matrix[i].length
    1 <= m, n <= 200
    -10^4 <= matrix[i][j] <= 10^4
    0 <= row1 <= row2 < m
    0 <= col1 <= col2 < n
    At most 10^4 calls will be made to sumRegion.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is the 2D generalisation of problem 002 (LC 303, Range Sum Query -
Immutable). The 1D trick was: build a `prefix` array once, then every range
sum is `prefix[r+1] - prefix[l]`, O(1). Here we do the same thing one
dimension up.

THE NAIVE APPROACH: store the matrix as-is, and for every `sumRegion` call,
loop over every cell in the requested rectangle and add it up:

    for i in range(row1, row2 + 1):
        for j in range(col1, col2 + 1):
            total += matrix[i][j]

This is O(rows * cols) PER QUERY — up to O(m*n) if the rectangle is the whole
matrix. With up to 10^4 queries against a 200x200 matrix, that is up to
4*10^8 cell reads in the worst case. Too slow, and it defeats the entire
point of a class whose constructor runs once and whose query method is
called many times.

THE FIX: precompute a 2D PREFIX SUM matrix in the constructor — pay O(m*n)
once — so every `sumRegion` call becomes 4 array lookups and 3 arithmetic
operations, O(1), regardless of how big the rectangle is.

Define, for a matrix `M` with `rows` rows and `cols` columns, a prefix matrix
`P` with ONE EXTRA ROW AND COLUMN (exactly like the 1D version's `n+1`
trick):

    P[i][j] = sum of every cell M[a][b] with 0 <= a < i and 0 <= b < j
            = the sum of the rectangle from (0,0) to (i-1, j-1), inclusive

    P has shape (rows+1) x (cols+1). P[0][*] = 0 and P[*][0] = 0 — "the sum
    of zero rows" or "the sum of zero columns" is 0, the 2D sentinel.

BUILDING P — inclusion-exclusion, one cell at a time:

    P[i][j] = M[i-1][j-1]      (the new cell being added)
            + P[i-1][j]        (everything above, rows 0..i-1, cols 0..j-1)
            + P[i][j-1]        (everything to the left, rows 0..i-1... )

    Careful — P[i-1][j] and P[i][j-1] BOTH include the top-left rectangle
    P[i-1][j-1], so adding them double-counts it. Subtract it back once:

    P[i][j] = M[i-1][j-1] + P[i-1][j] + P[i][j-1] - P[i-1][j-1]

    Picture (each letter is a REGION, not a single cell):
            j-1   j
       i-1 [ A ] [ B ]      B = "above" = P[i-1][j]  (includes A)
       i   [ C ] [ x ]      C = "left"  = P[i][j-1]  (includes A)
                             B + C counts A twice -> subtract P[i-1][j-1] once
                             x = M[i-1][j-1], the single new cell

QUERYING — the same inclusion-exclusion, run once to carve out an arbitrary
rectangle (row1, col1) to (row2, col2), inclusive:

    sumRegion(row1, col1, row2, col2)
        = P[row2+1][col2+1]        (everything from (0,0) to (row2,col2))
        - P[row1][col2+1]          (subtract the part ABOVE the query)
        - P[row2+1][col1]          (subtract the part LEFT of the query)
        + P[row1][col1]            (add back the corner, subtracted twice)

Full derivation, ASCII picture, and the exact same idea stated in prose is in
`PyDSA/04_prefix_sum/_TOPIC_GUIDE.md`, Part 2 ("2D Prefix Sums (LC 304)") —
read it if the formula above doesn't click from the code alone.


WHAT TO THINK ABOUT
--------------------
1. Why is `P` sized `(rows+1) x (cols+1)` instead of `rows x cols`? What
   would break at the matrix's top row / left column without the extra
   row/column of zeros? (Same reason as the 1D `prefix[0] = 0` sentinel.)

2. `sumRegion` takes INCLUSIVE bounds (`row2`, `col2` are themselves inside
   the rectangle). Where in the 4-term formula does the "+1" that converts
   an inclusive index into an exclusive one appear, and why twice (once per
   dimension)?

3. Walk through the "add back the corner" step with an actual small example
   until subtracting-then-adding-back stops feeling like a trick and starts
   feeling obviously necessary.

4. What is the WORST rectangle for the naive per-query loop — and is it
   possible that `sumRegion` is called with `row1==row2` and `col1==col2`
   (a single cell)? Does your formula still work then?

5. This is a DESIGN problem. Where does the O(m*n) work belong — in
   `__init__`, or in `sumRegion`? Getting this backwards (building P inside
   `sumRegion`) makes every single query slow again and defeats the purpose
   of the class existing.


PROGRESSIVE HINTS
------------------
Hint 1: Build `P` as a `(rows+1) x (cols+1)` list of lists, all zero, inside
        `__init__`. Fill it row by row with the inclusion-exclusion formula.

Hint 2: `P[i][j] = matrix[i-1][j-1] + P[i-1][j] + P[i][j-1] - P[i-1][j-1]`
        — every index on the right is either `i-1` or `j-1` in some
        combination; there is no `P[i][j]` on the right (it's the one you're
        computing).

Hint 3: `sumRegion` is a straight port of the four-term formula above. No
        loops, no recomputation. If your `sumRegion` has a loop in it, the
        precomputation didn't actually happen.

Hint 4: Sanity check on a 1x1 matrix: P should be a 2x2 grid of zeros except
        `P[1][1] = matrix[0][0]`, and `sumRegion(0,0,0,0)` should return
        exactly `matrix[0][0]`.


COMPLEXITY TARGET
------------------
    __init__:    O(rows * cols) time, O(rows * cols) space  (build P once)
    sumRegion:   O(1) time                                  (4 lookups)
================================================================================
*/

// TODO: Implement the stub
