package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 1899 · Merge Triplets to Form Target Triplet        [Medium]
https://leetcode.com/problems/merge-triplets-to-form-target-triplet/
================================================================================

A triplet is an array of three integers. You are given a 2D integer array
`triplets`, where `triplets[i] = [ai, bi, ci]` describes the ith triplet.
You are also given an integer array `target = [x, y, z]` that describes the
triplet you want to obtain.

To obtain `target`, you may apply the following operation on `triplets` any
number of times (possibly zero):

- Choose two indices (0-indexed) `i` and `j` and UPDATE `triplets[j]` to
  become `[max(ai, aj), max(bi, bj), max(ci, cj)]`.
  (e.g. if `triplets[i] = [2,5,3]` and `triplets[j] = [1,7,5]`, the result
  of choosing i and j is `triplets[j] = [max(2,1), max(5,7), max(3,5)] =
  [2,7,5]`.)

Return `True` if it is possible to obtain `target` as an element of
`triplets`, or `False` otherwise.

--------------------------------------------------------------------------------
EXAMPLES
--------------------------------------------------------------------------------
Input: triplets = [[2,5,3],[1,8,4],[1,7,5]], target = [2,7,5]
Output: True
Explanation: Perform the operation on i=0, j=2: triplets[2] = [max(2,1),
max(5,7), max(3,5)] = [2,7,5]. triplets = [[2,5,3],[1,8,4],[2,7,5]]. The
target triplet [2,7,5] is now an element of triplets.

Input: triplets = [[3,4,5],[4,5,6]], target = [3,2,5]
Output: False
Explanation: It is impossible to have [3,2,5] as an element because there
is no 2 in any of the triplets.

Input: triplets = [[2,5,3],[2,3,4],[1,2,5],[5,2,3]], target = [5,5,5]
Output: True

--------------------------------------------------------------------------------
CONSTRAINTS
--------------------------------------------------------------------------------
- 1 <= triplets.length <= 10^5
- triplets[i].length == target.length == 3
- 1 <= ai, bi, ci, x, y, z <= 1000
*/

func main() {
	fmt.Println("Solution for Merge Triplets to Form Target Triplet not implemented yet")
}
