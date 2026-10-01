package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 118 · Pascal's Triangle                          [Easy]
https://leetcode.com/problems/pascals-triangle/
================================================================================

PROBLEM
-------
Given an integer numRows, return the first numRows of Pascal's triangle.

In Pascal's triangle, each number is the sum of the two numbers directly
above it.


EXAMPLES
--------
Example 1:
    Input:  numRows = 5
    Output: [[1],[1,1],[1,2,1],[1,3,3,1],[1,4,6,4,1]]

Example 2:
    Input:  numRows = 1
    Output: [[1]]


CONSTRAINTS
-----------
    1 <= numRows <= 30


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Row i has i+1 entries. The first and last entry of every row are always 1;
every interior entry is the sum of the two entries directly above it in
the PREVIOUS row -- `row[j] = prev_row[j-1] + prev_row[j]`. That's a 1D
recurrence applied one row at a time: to build row i you only ever need
row i-1 (never anything older), so this is 1D DP where the "index" is the
row number and each "cell" is itself a small array.

PROGRESSIVE HINTS
------------------
Hint 1: Row 0 is always [1]. Every row starts and ends with 1.
Hint 2: To build row i from row i-1: new_row[0] = 1, new_row[-1] = 1, and
        for every position j in between, new_row[j] = prev[j-1] + prev[j].
Hint 3: You never need any row older than the immediately previous one --
        this is exactly the "fixed window of 1 row back" 1D pattern.

COMPLEXITY TARGET
------------------
    Time:  O(numRows^2)   -- total entries across all rows
    Space: O(numRows^2)   -- required by the output shape itself
================================================================================
*/

func main() {
	fmt.Println("Solution for Pascal's Triangle not implemented yet")
}
