package main

/*
================================================================================
LeetCode 680 · Valid Palindrome II                                       [Easy]
https://leetcode.com/problems/valid-palindrome-ii/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
Given a string `s`, return true if the `s` can be a palindrome after deleting
AT MOST ONE character from it.


EXAMPLES
--------
Example 1:
    Input:  s = "aba"
    Output: true
    Explanation: Already a palindrome; delete nothing.

Example 2:
    Input:  s = "abca"
    Output: true
    Explanation: You could delete the character 'c' (or 'b').

Example 3:
    Input:  s = "abc"
    Output: false


CONSTRAINTS
-----------
    1 <= s.length <= 10^5
    s consists of lowercase English letters.

Note: unlike LC 125, there is NO cleaning step here. The input is already
lowercase letters only. The whole difficulty is the deletion.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

"At most one deletion" sounds like it might multiply the work by n — try
deleting each of the n characters and test each result, n × O(n) = O(n²).

It does not, and seeing why is the entire lesson.

Walk the string with converging pointers exactly as in LC 125. As long as
s[l] == s[r], nothing interesting is happening — those characters are already
matched and no deletion could improve them.

    "a b c a"
     ↑     ↑     'a' == 'a'  -> matched, move inward
       ↑ ↑
       l r       'b' != 'c'  -> THE DECISION POINT

The first mismatch is the ONLY place a deletion can possibly help. And at that
point there are exactly TWO candidates:

    delete s[l]  ->  is s[l+1 .. r] a palindrome?
    delete s[r]  ->  is s[l   .. r-1] a palindrome?

Nothing else is worth trying. Deleting a character outside [l, r] cannot fix a
mismatch inside it, and deleting some other character inside [l, r] leaves
s[l] and s[r] still facing each other, still unequal, and now with one deletion
already spent.

So: one O(n) walk to find the mismatch, then at most two O(n) palindrome checks.
Total O(n) — the branch happens at most once, not once per character.


WHAT TO THINK ABOUT
-------------------
1. Write a helper that answers "is s[i..j] a palindrome?" using two pointers
   and NO slicing. Why no slicing? (See the topic guide, §2.1.)

2. At the first mismatch you must try both deletions. Is `or` the right
   combinator? What does short-circuiting buy you?

3. Why is it safe to only consider the FIRST mismatch? Convince yourself that
   an earlier matched pair can be ignored forever.

4. Common wrong instinct: "delete the smaller character" or "delete whichever
   side matches the next one". Find an input that defeats a greedy rule like
   that. (Try "cbbcc" or "ebcbbececabbacecbbcbe" and reason it through.)

5. What is the answer for a string that is already a palindrome? For a single
   character? For "ab"?


PROGRESSIVE HINTS
-----------------
Hint 1: Write `is_pal(i, j)` — a plain two-pointer palindrome check over the
        INDEX RANGE [i, j], no substring creation.

Hint 2: Main loop: converge `l` and `r` while `s[l] == s[r]`. If you get all
        the way through, return True — it was already a palindrome.

Hint 3: On the first mismatch, return `is_pal(l + 1, r) or is_pal(l, r - 1)`.
        That single line is the whole "at most one deletion" rule.


COMPLEXITY TARGET
-----------------
    Time:  O(n)  — one scan, plus at most two more scans that together cover
                   less than n characters
    Space: O(1)  — indices only, no substrings
================================================================================
*/

// TODO: Implement the stub
