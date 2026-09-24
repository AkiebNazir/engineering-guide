package main

/*
================================================================================
LeetCode 131 · Palindrome Partitioning                                  [Medium]
https://leetcode.com/problems/palindrome-partitioning/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given a string `s`, partition `s` such that every substring of the partition 
is a palindrome. Return all possible palindrome partitioning of `s`.

A palindrome string is a string that reads the same backward as forward.

EXAMPLES
--------
Example 1:
    Input:  s = "aab"
    Output: [["a","a","b"], ["aa","b"]]
    Explanation: 
        - "a", "a", "b" are all palindromes.
        - "aa", "b" are all palindromes.

Example 2:
    Input:  s = "a"
    Output: [["a"]]

CONSTRAINTS
-----------
    1 <= s.length <= 16
    s contains only lowercase English letters.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
At first glance, partitioning a string feels different from picking elements
out of an array (like Subsets or Combinations). However, structurally, this 
is exactly the Combinations shape. 

Instead of choosing "which element goes next", your choice at each step is:
"Where do I place the next cut?"

Think of a string of length `n` having `n-1` possible places to cut it. 
Every time you are at a starting index `start`, you look forward for a valid 
ending index `end`. If the substring `s[start:end]` is a palindrome, you have 
found a valid piece! You "choose" that piece, add it to your path, and then 
"explore" by recursing from `end`.

THE DECISION TREE
------------------
For s = "aab":
- start at index 0
- Look at "a" (index 0 to 1). It's a palindrome. 
    -> CHOOSE "a", recurse to index 1.
- Look at "aa" (index 0 to 2). It's a palindrome.
    -> CHOOSE "aa", recurse to index 2.
- Look at "aab" (index 0 to 3). Not a palindrome.
    -> PRUNE (skip this choice).

WHAT TO THINK ABOUT
--------------------
1. What represents the `state` in your recursion? (A list of substrings).
2. What represents your current progress through the input? (An integer `start` 
   representing where the unpartitioned remainder of the string begins).
3. What is the base case (leaf node)? (When `start` reaches the end of the 
   string, `len(s)`, meaning the entire string has been successfully partitioned).
4. How do you check if a substring is a palindrome efficiently in Python? 
   (`sub == sub[::-1]` is highly optimized in C and perfect for lengths <= 16).

PROGRESSIVE HINTS
------------------
Hint 1: Write a helper `backtrack(start)` and initialize an empty `path`.
Hint 2: Inside `backtrack`, loop `end` from `start + 1` up to `len(s) + 1`. 
        This isolates the substring `s[start:end]`.
Hint 3: If `s[start:end]` is a palindrome, append it to `path`, call 
        `backtrack(end)`, and then pop it from `path` (unchoose).
Hint 4: When `start == len(s)`, make a copy of `path` (`path[:]`) and append 
        it to your results list.

COMPLEXITY TARGET
------------------
    Time:  O(n * 2^n) in the worst case (e.g., "aaaaa...").
    Space: O(n) for the recursion stack and path array.
================================================================================
*/

// TODO: Implement the stub
