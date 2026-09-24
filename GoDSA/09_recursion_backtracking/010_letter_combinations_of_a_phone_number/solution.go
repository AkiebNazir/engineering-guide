package main

import "fmt"

/*
================================================================================
LeetCode 17 · Letter Combinations of a Phone Number                     [Medium]
https://leetcode.com/problems/letter-combinations-of-a-phone-number/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given a string containing digits from 2-9 inclusive, return all possible
letter combinations that the number could represent. Return the answer in
any order.

A mapping of digits to letters (just like on the telephone buttons):

    2 -> "abc"    3 -> "def"    4 -> "ghi"    5 -> "jkl"
    6 -> "mno"    7 -> "pqrs"   8 -> "tuv"    9 -> "wxyz"

Note that 1 does not map to any letters.

EXAMPLES
--------
Example 1:
    Input:  digits = "23"
    Output: ["ad","ae","af","bd","be","bf","cd","ce","cf"]

Example 2:
    Input:  digits = ""
    Output: []

Example 3:
    Input:  digits = "2"
    Output: ["a","b","c"]

CONSTRAINTS
-----------
    0 <= digits.length <= 4
    digits[i] is a digit in the range ['2', '9'].

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the FIRST problem in the folder where choices at successive depths
come from DIFFERENT pools.

In Subsets, Permutations, and Combinations the pool of choices is always one
array (nums, or 1..n). Here, each depth d in the recursion has its own pool:
the letters mapped to `digits[d]`. The tree is not "pick from the same set
with restrictions" but "at level 0 pick from {'a','b','c'}, at level 1 pick
from {'d','e','f'}, ..."

This makes it a CROSS-PRODUCT / CARTESIAN-PRODUCT problem:

    result = pool[0] × pool[1] × ... × pool[len(digits)-1]

The total number of outputs is the product of the pool sizes, not a
combinatorial (C, P) formula. For digits = "23": 3 × 3 = 9 results.

WHY THIS IS STILL BACKTRACKING
-------------------------------
The recursion template is identical to the one you already know:
    - state: a `path` (list of characters chosen so far)
    - is_leaf: len(path) == len(digits)
    - choices: the letters of the digit at position len(path)
    - choose / explore / unchoose

The only twist: `choices` depend on which depth you are at, not on a `start`
index. There is no `start` parameter, no `used[]` array, no dedupe —
just a different pool per level.

WHAT TO THINK ABOUT
--------------------
1. What data structure maps digit -> letters? A dictionary, a list indexed
   by digit value, or even a string array of length 10 (indices 0-9, with
   0 and 1 unused). All work; pick whichever you can type fastest.

2. What does the recursion tree look like for "23"? Draw it. At the root
   you branch into 'a', 'b', 'c' (digit '2'). Under each, you branch into
   'd', 'e', 'f' (digit '3'). The leaves are the 9 results.

3. Can you implement this iteratively by building the result list
   level-by-level (BFS-style)? Yes — start with [""], and for each digit,
   extend every partial result with each of that digit's letters. This is
   the itertools.product approach.

4. What happens with an empty input? You must return [] (not [""]). This is
   a common edge-case trap: C(n,0) = 1 (the empty subset), but "no digits
   pressed" means NO combinations exist.

PROGRESSIVE HINTS
------------------
Hint 1: Build the digit -> letters mapping first.
Hint 2: Write the backtracking function with `index` (which digit are we
        currently processing).
Hint 3: Base case: when `index == len(digits)`, join path and add to results.
Hint 4: Loop over `mapping[digits[index]]` and do choose/explore/unchoose.
Hint 5: Handle digits = "" as a special case at the start: return [].

COMPLEXITY TARGET
------------------
    Time:  O(4^n * n) where n = len(digits). Worst case each digit maps to
           4 letters ('7' and '9'). We produce up to 4^n strings, each of
           length n.
    Space: O(n) for the recursion stack and path, excluding output.
================================================================================
*/

func main() {
	fmt.Println("Solution for Letter Combinations of a Phone Number not implemented yet")
}
