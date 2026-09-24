package main

/*
================================================================================
LeetCode 46 · Permutations                                             [Medium]
https://leetcode.com/problems/permutations/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given an array `nums` of DISTINCT integers, return ALL possible permutations.
Return the answer in any order.

EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,3]
    Output: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]

Example 2:
    Input:  nums = [0,1]
    Output: [[0,1],[1,0]]

Example 3:
    Input:  nums = [1]
    Output: [[1]]

CONSTRAINTS
-----------
    1 <= nums.length <= 6
    -10 <= nums[i] <= 10
    All the integers of nums are UNIQUE.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The second base shape from the topic guide's Part 2. Unlike subsets (include/
skip PER ELEMENT) or combinations (which elements, in increasing order), a
permutation's choice at each node is: "which UNUSED element goes in THIS slot
next?" Every element must appear exactly once, in every possible order — so
the branching factor SHRINKS by one at each level (n choices, then n-1, then
n-2, ...), giving n! leaves.

    nums = [1, 2, 3]

                                   []
                choose 1  /   choose 2  |   choose 3 \
             [1]              [2]                [3]
          2/    \3          1/   \3            1/   \2
       [1,2]   [1,3]     [2,1]   [2,3]      [3,1]   [3,2]
         |3      |2         |3     |1          |2     |1
      [1,2,3] [1,3,2]   [2,1,3] [2,3,1]    [3,1,2] [3,2,1]

6 = 3! leaves, one per full ordering. Only leaves are valid answers here —
unlike subsets, an incomplete path (e.g. [1,2]) is NOT itself an answer.

WHAT TO THINK ABOUT
--------------------
1. How do you track which elements are "already used" in the current path so
   you don't repeat one? Two options: a boolean array parallel to `nums`, or
   checking `elem in path` (which is O(n) per check — slower, but simpler).
2. What is the leaf condition? (Hint: it's about the LENGTH of the path, not
   about reaching the end of an index range like subsets/combinations.)
3. What happens to the "used" marker after a recursive call returns — what
   must you undo?
4. Alternative without recursion: can you generate permutations by repeatedly
   SWAPPING elements in place, rather than building a separate `path` list?
5. Why doesn't the sort+skip-sibling trick from subsets/combinations apply
   here directly? (It does, but the tree shape is different — see problem 005.)

PROGRESSIVE HINTS
------------------
Hint 1: Keep `used = [False] * n` alongside `path = []`. At each node, loop
        over ALL indices; skip any already `used`.
Hint 2: Leaf condition: `len(path) == len(nums)` — record path[:] and return.
Hint 3: choose: `used[i] = True; path.append(nums[i])`.
        unchoose: `path.pop(); used[i] = False` (reverse order of choose).
Hint 4: The in-place swap approach: recursively fix nums[0], then nums[1],
        etc., by swapping the current position with each candidate in turn,
        recursing, then swapping BACK — avoids a separate `used` array
        entirely, at the cost of mutating (and having to restore) the input.

COMPLEXITY TARGET
------------------
    Time:  O(n * n!)   — n! leaves, O(n) to copy each into the results list
    Space: O(n) auxiliary (path + used array + recursion depth),
           O(n * n!) for the output
================================================================================
*/

// TODO: Implement the stub
