package main

/*
================================================================================
LeetCode 761 · Special Binary String                                     [Hard]
https://leetcode.com/problems/special-binary-string/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
A binary string is SPECIAL if it has an equal quantity of '0's and '1's, and
every prefix has at least as many '1's as '0's.

You are given a special binary string `s`. You may perform this operation any
number of times: choose two consecutive, non-empty, special substrings of
`s`, and swap them. Two adjacent special substrings may be swapped even if
after the swap the two substrings are no longer adjacent to what they were
originally adjacent to.

Return the lexicographically largest resulting string possible after applying
the mentioned operations on the string.

EXAMPLES
--------
Example 1:
    Input:  s = "11011000"
    Output: "11100100"
    Explanation: The strings "10" [occurring at s[1:3]] and "1100"
    [at s[3:7]] are swapped... (equivalently: recursively "unfold and sort
    the top-level pieces descending" produces "11100100").

Example 2:
    Input:  s = "10"
    Output: "10"

CONSTRAINTS
-----------
    1 <= s.length <= 50
    s[i] is '0' or '1'
    s is a special binary string.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Every special binary string of length > 0 starts with '1' and ends with '0'
(a running "1"-count-minus-"0"-count balance that starts positive after the
first char and returns to exactly 0 only at the very end — the first dip to 0
happens at the LAST character, not before, otherwise the string would split
into two specials earlier). Strip that outer '1' ... '0' shell and what
remains between them is ITSELF a concatenation of one or more special binary
substrings, back to back — because the balance only touches 0 at the
positions where one special substring ends and (possibly) another begins.

That gives a clean recursive decomposition: split `s` into its TOP-LEVEL
special pieces (using a running balance counter that flags "balance == 0" as
a piece boundary), recursively make EACH piece its own lexicographically
largest special string, wrap each in `'1' + (that result) + '0'`, and then
SORT THE PIECES IN DESCENDING ORDER before concatenating them (because
swapping two adjacent special substrings is exactly the operation that lets
you reorder top-level pieces arbitrarily — so to be lexicographically
largest, greedily put the largest piece first).

WHAT TO THINK ABOUT
--------------------
1. Why must every non-empty special string start with '1' and end with '0'?
2. Given the top-level pieces of `s` (found via a balance counter that hits
   zero exactly at each piece boundary), why is sorting them in DESCENDING
   order and concatenating always achievable via legal swaps, and always
   optimal?
3. Once you've stripped a piece's outer '1' and '0', is the inside itself a
   single special string, or could it be MULTIPLE special strings back to
   back? Why does the answer matter for how you recurse?
4. What is the base case — the smallest special string that needs no further
   decomposition?

PROGRESSIVE HINTS
------------------
Hint 1: Base case: `s == ""` (empty) needs no work — return "".
Hint 2: Scan `s` with a running `count` (+1 for '1', -1 for '0'). Every index
        `i` where `count` returns to 0 marks the end of one top-level piece;
        the next piece (if any) starts right after.
Hint 3: For each top-level piece `s[start:i+1]`, its first and last chars are
        '1' and '0'; recursively solve the INSIDE (`s[start+1:i]`) and wrap:
        `'1' + recurse(inside) + '0'`.
Hint 4: Collect all wrapped top-level pieces into a list, `sort(reverse=True)`
        them (plain string comparison is enough — same-length strings from
        the same-length top-level split, and Python compares strings
        lexicographically by default), then `''.join(...)`.

COMPLEXITY TARGET
------------------
    O(n log n) time (each level does O(k) work to split into pieces plus an
    O(k log k) sort of k pieces; total work across all recursion levels sums
    to O(n log n) for n = len(s)), O(n) extra space for the recursion and the
    piece lists.
================================================================================
*/

// TODO: Implement the stub
