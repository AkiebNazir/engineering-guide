package main

/*
================================================================================
LeetCode 242 · Valid Anagram                                             [Easy]
https://leetcode.com/problems/valid-anagram/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given two strings `s` and `t`, return true if `t` is an anagram of `s`, and
false otherwise.

An Anagram is a word or phrase formed by rearranging the letters of a different
word or phrase, typically using all the original letters exactly once.


EXAMPLES
--------
Example 1:
    Input:  s = "anagram", t = "nagaram"
    Output: true

Example 2:
    Input:  s = "rat", t = "car"
    Output: false


CONSTRAINTS
-----------
    1 <= len(s), len(t) <= 5 * 10^4
    s and t consist of lowercase English letters.

FOLLOW UP
---------
    What if the inputs contain Unicode characters? How would you adapt your
    solution to such a case?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

"Anagram" means: same character MULTISET. Order is irrelevant, but counts
matter — "aacc" and "ccac" use the same letter set yet are not anagrams. A set
is the wrong tool; you need frequencies.

    s = "anagram"  ->  {a:3, n:1, g:1, r:1, m:1}
    t = "nagaram"  ->  {a:3, n:1, g:1, r:1, m:1}   equal -> true

The cheapest disqualifier is length. Check it first and bail.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. ⚠️ `len(s)` returns BYTES, not characters. For the stated constraint
   (lowercase ASCII) byte length == character length, so it is fine here.
   For the Unicode follow-up it is NOT — "é" is 2 bytes, 1 rune. You would
   need utf8.RuneCountInString(s).

2. Indexing `s[i]` yields a `byte` (uint8), not a character. For ASCII that is
   exactly what you want: `s[i] - 'a'` gives 0..25 directly, no conversion.

3. A `[26]int` ARRAY (not a slice) is the ideal counter here. It is a value
   type, stack-allocated, zero-initialised, with no hashing and no allocation.
   This is meaningfully faster than a map.

4. Ranging a string (`for _, r := range s`) decodes UTF-8 and yields RUNES.
   That is the tool for the follow-up, not for the ASCII fast path.


PROGRESSIVE HINTS
-----------------
Hint 1: If len(s) != len(t), return false immediately.

Hint 2: Declare `var counts [26]int`. Walk both strings together, incrementing
        for s and decrementing for t.

Hint 3: They are anagrams exactly when every counter ends at zero.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(1) — 26 ints regardless of input size.
================================================================================
*/

// YourIsAnagram is your attempt.
// Implement it, then run:  cd GoDSA && go run ./01_arrays_hashing/003_valid_anagram
func YourIsAnagram(s string, t string) bool {
	// YOUR CODE HERE
	return false
}
