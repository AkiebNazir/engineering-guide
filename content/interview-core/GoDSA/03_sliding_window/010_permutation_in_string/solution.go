package main

import "fmt"

/*
================================================================================
LeetCode 567 · Permutation in String                                    [Medium]
https://leetcode.com/problems/permutation-in-string/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
Given two strings `s1` and `s2`, return `true` if `s2` contains a PERMUTATION
of `s1`, or `false` otherwise.

In other words, return `true` if one of `s1`'s permutations is a SUBSTRING of
`s2`.


EXAMPLES
--------
Example 1:
    Input:  s1 = "ab", s2 = "eidbaooo"
    Output: true
    Explanation: s2 contains one permutation of s1 ("ba").

Example 2:
    Input:  s1 = "ab", s2 = "eidboaoo"
    Output: false


CONSTRAINTS
-----------
    1 <= s1.length, s2.length <= 10^4
    s1 and s2 consist of lowercase English letters.
                                     <- a BOUNDED, KNOWN alphabet. Use it.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Two observations turn this into a fixed-size window.

FIRST: a permutation of `s1` has EXACTLY the same length as `s1`. So you are
not searching for a variable-length window at all — every candidate substring
of `s2` has length exactly `len(s1)`. This is Shape A.

SECOND: "is a permutation of" means "has the same character frequencies as".
Order is irrelevant by definition. So the question per window is:

    does this window's frequency map equal s1's frequency map?

    s1 = "ab"   -> need = {a:1, b:1}
    s2 = "eidbaooo"

        [e i]      {e:1, i:1}   no
         [i d]     {i:1, d:1}   no
          [d b]    {d:1, b:1}   no
           [b a]   {a:1, b:1}   YES -> true

That is the whole algorithm. What makes the problem interesting is the COST of
the comparison, which is the next section.


HOW EXPENSIVE IS "SAME FREQUENCIES"?
------------------------------------
The obvious implementation compares two maps on every step:

    if Counter(window) == need:  return True     # ✗ O(k) to BUILD, O(26) to compare

Building `Counter(window)` from scratch is O(k) per step where k = len(s1), so
that is O(n*k) — the classic trap this whole folder is about. Slide the counts
instead, and the build cost disappears.

But even with slid counts, `window == need` is an O(26) dict comparison on
every one of n steps. That is O(26n), which IS O(n) for a fixed alphabet — a
perfectly good answer. Measured, though, `Counter == Counter` is roughly 70x
slower than comparing two 26-element lists, so the data structure choice
matters a lot here even though the complexity does not.

The O(1)-per-step version keeps a single integer:

    matches = how many of the 26 letters currently have window_count == need_count

The window is a permutation exactly when `matches == 26`. Each slide changes
the count of exactly two letters, so at most two of the 26 equalities can
change — updating `matches` is O(1). Working out the update rule correctly is
the real exercise here, and it transfers directly to problems 011 and 015.


WHAT TO THINK ABOUT
-------------------
1. What is the window's size, and why is it fixed? What must you check before
   the loop even starts?

2. Three ways to test "the window matches": rebuild and compare, slide and
   compare, slide and maintain `matches`. What is the complexity of each?

3. For the `matches` counter: when a letter's count changes by exactly 1, how
   can the equality `window[c] == need[c]` change? Enumerate the cases — there
   are only two that matter, and getting them backwards is the whole bug.

4. Why must you compare with `==` (exact equality) rather than `>=` when
   updating `matches`? Construct a case where `>=` gives the wrong answer.

5. Letters that appear in NEITHER string have count 0 in both. Are they
   "matching"? What does that mean for how you initialise `matches`?

6. What if `len(s1) > len(s2)`?


PROGRESSIVE HINTS
-----------------
Hint 1: The window has fixed length `len(s1)`. If `len(s1) > len(s2)`, return
        False immediately.

Hint 2: Use two 26-slot lists, `need` and `window`, indexed by `ord(c) - 97`.
        Prime the first window, then slide: one letter in, one letter out.

Hint 3: Simplest correct version — compare the two lists each step:
            if need == window: return True
        `list == list` on 26 ints is fast and obviously correct. Ship this
        first.

Hint 4: For the O(1) comparison, maintain `matches = sum(need[i] == window[i]
        for i in range(26))` and update it on each change:

            window[i] += 1
            if window[i] == need[i]:      matches += 1   # just became equal
            elif window[i] == need[i] + 1: matches -= 1  # just left equality

        and symmetrically for the decrement. Answer is `matches == 26`.


COMPLEXITY TARGET
-----------------
    Time:  O(n)        with the `matches` counter (n = len(s2))
           O(26n)      comparing the two arrays each step — also fine
    Space: O(26) = O(1)
================================================================================
*/

func main() {
	fmt.Println("Solution for Permutation in String not implemented yet")
}
