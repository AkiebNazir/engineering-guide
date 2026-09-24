package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 1851 · Minimum Interval to Include Each Query       [Hard]
https://leetcode.com/problems/minimum-interval-to-include-each-query/
================================================================================

You are given a 2D integer array `intervals`, where intervals[i] = [left_i,
right_i] describes the i-th interval starting at left_i and ending at
right_i (inclusive). The SIZE of an interval is defined as right_i - left_i + 1.

You are also given an integer array `queries`. The answer to the j-th query
is the SIZE of the SMALLEST interval i such that left_i <= queries[j] <=
right_i. If no such interval exists, the answer is -1.

Return an array `ans` where ans[j] is the answer to the j-th query.

Example 1:
    Input:  intervals = [[1,4],[2,4],[3,6],[4,4]], queries = [2,3,4,5]
    Output: [3,3,1,4]
    Explanation:
        query=2: intervals [1,4],[2,4] contain 2, smaller is [2,4] size 3.
        query=3: intervals [1,4],[2,4],[3,6] contain 3, smallest [2,4] size 3.
        query=4: all four intervals contain 4, smallest is [4,4] size 1.
        query=5: only [3,6] contains 5, size 4.

Example 2:
    Input:  intervals = [[2,3],[2,5],[1,8],[20,25]], queries = [2,19,5,22]
    Output: [2,-1,4,6]

Constraints:
    1 <= intervals.length <= 10^5
    1 <= queries.length <= 10^5
    intervals[i].length == 2
    1 <= left_i <= right_i <= 10^7
    1 <= queries[j] <= 10^7
*/

func main() {
	fmt.Println("Solution for Minimum Interval to Include Each Query not implemented yet")
}
