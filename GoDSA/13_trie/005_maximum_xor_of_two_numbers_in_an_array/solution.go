package main

import "fmt"

/*
================================================================================
LeetCode 421 · Maximum XOR of Two Numbers in an Array                   [Medium]
https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/
Topic: 13 · Trie
================================================================================

PROBLEM
-------
Given an integer array `nums`, return the maximum result of
`nums[i] XOR nums[j]`, where `0 <= i <= j < nums.length`.

EXAMPLE
-------
    Input:  nums = [3, 10, 5, 25, 2, 8]
    Output: 28
    Explanation: The maximum result is 5 XOR 25 = 28.

    Input:  nums = [0]
    Output: 0

CONSTRAINTS
-----------
    1 <= nums.length <= 2 * 10^5
    0 <= nums[i] <= 2^31 - 1

See PyDSA/13_trie/_TOPIC_GUIDE.md Part 7 (bit trie) before writing this.
Insert every number's bits (most-significant-bit first) into a trie of
depth 32 where each node has exactly 2 children (bit 0 / bit 1). For each
number, greedily try to walk the OPPOSITE bit at every level -- that greedy
walk is what turns an O(n^2) pairwise scan into O(32*n).
================================================================================
*/

func main() {
	fmt.Println("Solution for Maximum XOR of Two Numbers in an Array not implemented yet")
}
