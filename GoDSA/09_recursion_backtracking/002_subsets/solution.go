package main

import "fmt"

/*
================================================================================
LeetCode 78 · Subsets                                                  [Medium]
https://leetcode.com/problems/subsets/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given an integer array `nums` of UNIQUE elements, return all possible subsets
(the power set). The solution set must not contain duplicate subsets. Return
the solution in any order.

EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,3]
    Output: [[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]

Example 2:
    Input:  nums = [0]
    Output: [[],[0]]

CONSTRAINTS
-----------
    1 <= nums.length <= 10
    -10 <= nums[i] <= 10
    All the numbers of nums are UNIQUE.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the archetype of the "subsets" shape from the topic guide's Part 2: at
each element, in order, you make exactly one binary decision — INCLUDE it in
the current subset, or SKIP it. There is no other choice at any node. Every
one of the 2^n leaves of that binary decision tree is a distinct, valid subset
— there is no "is this a valid leaf?" test beyond "we've decided about every
element," because every combination of include/skip decisions is legal.

    nums = [1, 2]

                              []
                choose 1 /        \ skip 1
              [1]                    []
         choose 2/ \skip2      choose 2/ \skip 2
        [1,2]      [1]        [2]         []

Four leaves = 2^2 subsets, one per node in the bottom row.

An equivalent way to generate the same set: build subsets INCREMENTALLY by
choosing which index to add next (never revisiting an earlier index) — instead
of an include/skip decision per element, decide "should I stop here (record
the current path as a subset), or extend by picking the next available index."
Both templates produce the same 2^n subsets; the second is closer to how
combinations (006) will be built, so it's worth knowing both shapes.

WHAT TO THINK ABOUT
--------------------
1. What are the two choices at any given element? Name them.
2. Where in the recursion do you record a subset — is it only at "leaves," or
   at every node?
3. When you append the current path to your results list, are you appending
   the SAME list object that keeps getting mutated by later recursive calls,
   or a snapshot/copy of it at this exact moment? What would happen to already
   -recorded subsets if you appended a reference and then kept mutating that
   same list afterward?
4. What is the exact "unchoose" step after the recursive call returns?
5. Can you generate the power set WITHOUT recursion at all, using binary
   representations of numbers 0..2^n-1?

PROGRESSIVE HINTS
------------------
Hint 1: `path = []`; at each index, EITHER append nums[i] and recurse on i+1,
        OR skip nums[i] and recurse on i+1. Record `path[:]` (a COPY) at
        every node — every node is a valid subset, not just leaves at the end.
Hint 2: Structure it as: record path[:], then loop over remaining indices,
        choose/recurse/unchoose (the combinations-style shape). This
        naturally handles "record at every node" without special-casing.
Hint 3: `results.append(path)` (no `[:]`) is a live bug: `path` is the SAME
        list object mutated throughout the whole recursion. By the time the
        recursion finishes, every entry in `results` points at the same
        (now empty, or wrong) list.
Hint 4: Bitmask alternative: for mask in range(2**n), include nums[i] if bit i
        of mask is set. No recursion, same 2^n subsets.

COMPLEXITY TARGET
------------------
    Time:  O(n * 2^n)   — 2^n subsets, O(n) to copy each into the results list
    Space: O(n) auxiliary (recursion depth + path), O(n * 2^n) for the output
================================================================================
*/

func main() {
	fmt.Println("Solution for Subsets not implemented yet")
}
