package main

import "fmt"

/*
================================================================================
LeetCode 438 · Find All Anagrams in a String                            [Medium]
https://leetcode.com/problems/find-all-anagrams-in-a-string/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
Given two strings `s` and `p`, return an array of ALL THE START INDICES of
`p`'s anagrams in `s`. You may return the answer in any order.


EXAMPLES
--------
Example 1:
    Input:  s = "cbaebabacd", p = "abc"
    Output: [0,6]
    Explanation:
        The substring with start index = 0 is "cba", which is an anagram of "abc".
        The substring with start index = 6 is "bac", which is an anagram of "abc".

Example 2:
    Input:  s = "abab", p = "ab"
    Output: [0,1,2]
    Explanation:
        The substring with start index = 0 is "ab", which is an anagram of "ab".
        The substring with start index = 1 is "ba", which is an anagram of "ab".
        The substring with start index = 2 is "ab", which is an anagram of "ab".


CONSTRAINTS
-----------
    1 <= s.length, p.length <= 3 * 10^4
    s and p consist of lowercase English letters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is problem 010 (LC 567) with ONE line changed. There you returned `True`
on the first matching window; here you append the index and keep going.

    LC 567:  if matches: return True
    LC 438:  if matches: out.append(r - k + 1)

Everything else — the fixed window of width k = len(p), the frequency
comparison, the match counter, the guard for `len(p) > len(s)` — is identical.
If you solved 010, write 011 from memory and spend your time on the two things
that are genuinely different:

  1. THE INDEX YOU APPEND. The window currently spans `[r-k+1, r]`, so the
     START index is `r - k + 1`, not `r` and not `l`. Off-by-one here is the
     most common error in this problem, and unlike 010 it cannot hide behind a
     boolean.

  2. NO EARLY EXIT. You must scan the entire string. That changes the honest
     complexity discussion: 010's best case could be O(k), this one is always
     Θ(n).


HOW BIG CAN THE OUTPUT BE?
--------------------------
Worth asking before you claim a complexity. With s = "aaaa...a" (n copies) and
p = "aa", every position matches:

    number of results = n - k + 1

So the output alone can be Θ(n). Your algorithm is O(n) time and O(n) output —
say both. Claiming "O(1) extra space" is only true if you do not count the
answer array, which is the usual convention; state the convention you are
using.


THE OVERLAP POINT
-----------------
Notice in Example 2 that the answers 0, 1 and 2 OVERLAP. Anagram occurrences
are not disjoint, so you cannot "skip ahead by k" after a hit — a tempting
optimisation that is simply wrong. Every position must be tested.


WHAT TO THINK ABOUT
-------------------
1. What index do you append, given that `r` is the index that just entered?
   Derive it from the window's span rather than guessing.

2. What must you check before priming the first window?

3. Do you check the FIRST window (the one built while priming), or only the
   slid ones? Which example catches you if you forget?

4. Can occurrences overlap? What does that rule out?

5. How large can the output be, and does that change your stated complexity?

6. If you use a match counter (from problem 010), what is the only thing you
   need to change?


PROGRESSIVE HINTS
-----------------
Hint 1: k = len(p). If k > len(s), return []. Build `need` from p and `window`
        from s[:k].

Hint 2: Check the primed window BEFORE the loop: `if window == need:
        out.append(0)`.

Hint 3: Then for r in range(k, len(s)): add s[r], remove s[r-k], and test.
        The start index of the window ending at r is `r - k + 1`.

Hint 4: To get strict O(n) rather than O(26n), carry the `matches` counter from
        problem 010 unchanged — only the "what to do on a match" line differs.


COMPLEXITY TARGET
-----------------
    Time:  O(n)          with a match counter; O(26n) comparing arrays
    Space: O(26) = O(1) auxiliary, plus O(number of answers) for the output
================================================================================
*/

func main() {
	fmt.Println("Solution for Find All Anagrams in a String not implemented yet")
}
