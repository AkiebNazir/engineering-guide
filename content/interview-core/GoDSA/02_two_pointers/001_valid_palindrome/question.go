package main

/*
================================================================================
LeetCode 125 · Valid Palindrome                                          [Easy]
https://leetcode.com/problems/valid-palindrome/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
A phrase is a PALINDROME if, after converting all uppercase letters into
lowercase letters and REMOVING ALL NON-ALPHANUMERIC CHARACTERS, it reads the
same forward and backward. Alphanumeric characters include letters and numbers.

Given a string `s`, return true if it is a palindrome, or false otherwise.


EXAMPLES
--------
Example 1:
    Input:  s = "A man, a plan, a canal: Panama"
    Output: true
    Explanation: "amanaplanacanalpanama" is a palindrome.

Example 2:
    Input:  s = "race a car"
    Output: false
    Explanation: "raceacar" is not a palindrome.

Example 3:
    Input:  s = " "
    Output: true
    Explanation: s becomes "" after removing non-alphanumeric characters.
                 Since an empty string reads the same forward and backward,
                 it is a palindrome.


CONSTRAINTS
-----------
    1 <= s.length <= 2 * 10^5
    s consists only of printable ASCII characters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Two separate requirements hide in the word "palindrome" here:

    1. NORMALISE — lowercase, and drop everything that is not a letter or digit.
    2. COMPARE   — does the normalised string read the same both ways?

The easy version does step 1 eagerly, building a new cleaned string, then does
step 2 with a reversal:

    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]

That is correct, it is two lines, and you should say it immediately. It costs
O(n) EXTRA SPACE — one new string for the cleaned text, another for its
reverse.

The interesting version does both steps lazily, in one pass, with no allocation
at all:

    "A man, a plan, a canal: Panama"
     ↑                            ↑
     l                            r      compare s[l] and s[r] directly,
                                         skipping junk as you meet it

    l walks right, r walks left, they meet in the middle. Nothing is built.
    O(1) space.

That is the CONVERGING TWO POINTERS pattern, and this is the cleanest possible
introduction to it — the elimination argument is trivial (a matched pair is
done; move both inward), so you can focus on the mechanics.


WHAT TO THINK ABOUT
-------------------
1. If s[l] is a comma and s[r] is a letter, you cannot compare them. What do
   you do — and which pointer moves?

2. Your skip loops advance pointers. What stops them from running off the end
   of the string on an input like ".,;:!"? (Python will NOT raise here — think
   about what s[-1] does.)

3. Should the loop be `while l < r` or `while l <= r`? Consider a string with
   an odd number of characters: does the middle one need comparing?

4. `.lower()` on every comparison, or normalise once? Does it matter for
   correctness? For speed?

5. What is the answer for a string with no alphanumeric characters at all?


PROGRESSIVE HINTS
-----------------
Hint 1: Two indices, `l = 0` and `r = len(s) - 1`. Loop while `l < r`.

Hint 2: Before comparing, advance each pointer past any non-alphanumeric
        character:
            while l < r and not s[l].isalnum(): l += 1
            while l < r and not s[r].isalnum(): r -= 1
        The `l < r` inside each inner loop is MANDATORY, not decoration.

Hint 3: Now compare `s[l].lower() != s[r].lower()` — if they differ, return
        False immediately. Otherwise step both pointers inward and continue.
        Surviving the whole loop means it is a palindrome.


COMPLEXITY TARGET
-----------------
    Time:  O(n)  — each pointer moves at most n positions total
    Space: O(1)  — no new string is built
================================================================================
*/

// TODO: Implement the stub
