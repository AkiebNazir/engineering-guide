package main

/*
================================================================================
LeetCode 49 · Group Anagrams                                           [Medium]
https://leetcode.com/problems/group-anagrams/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an array of strings `strs`, group the anagrams together. You can return
the answer in any order.

An anagram is a word formed by rearranging the letters of another, using all
the original letters exactly once.


EXAMPLES
--------
Example 1:
    Input:  strs = ["eat","tea","tan","ate","nat","bat"]
    Output: [["bat"],["nat","tan"],["ate","eat","tea"]]

Example 2:
    Input:  strs = [""]
    Output: [[""]]

Example 3:
    Input:  strs = ["a"]
    Output: [["a"]]


CONSTRAINTS
-----------
    1 <= strs.length <= 10^4
    0 <= strs[i].length <= 100
    strs[i] consists of lowercase English letters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

"Group these things by a property" is a hash-map problem, always. The only
question is: WHAT IS THE KEY?

You cannot key on the string itself — "eat" and "tea" are different strings but
belong in the same bucket. You need a function f such that:

    f(s1) == f(s2)   if and only if   s1 and s2 are anagrams

That function is called a CANONICAL FORM. It maps every member of a group to
one identical representative:

        "eat" ─┐
        "tea" ─┼──► f ──► "aet"  ─── one bucket
        "ate" ─┘

        "tan" ─┐
        "nat" ─┴──► f ──► "ant"  ─── another bucket

        "bat" ────► f ──► "abt"  ─── another bucket

Once you have f, the whole problem is three lines: for each string, compute the
key, append the string to `buckets[key]`, return the values.

The interesting part — and the part interviewers push on — is that there is
MORE THAN ONE valid canonical form, and they have different complexities.


WHAT TO THINK ABOUT
-------------------
1. What is the simplest function that gives two anagrams the same output?
   (Hint: an anagram is a permutation. What is the canonical permutation?)

2. That function costs O(k log k) per string of length k. The constraint says
   the alphabet is only lowercase a–z. Can you build a key in O(k) instead,
   without sorting?

3. Whatever key you choose, it has to be usable as a dict key — so it must be
   HASHABLE. In Python, `list` is not; `tuple` and `str` are. This bites people.

4. `collections.defaultdict(list)` removes the "is this key present yet?"
   branch entirely. Know why that is safe here.


PROGRESSIVE HINTS
-----------------
Hint 1: Two strings are anagrams exactly when their sorted characters are
        identical. `sorted("eat")` and `sorted("tea")` both give
        ['a','e','t'].

Hint 2: Use a dict from key -> list of strings. Iterate once, computing the key
        and appending. Return `list(buckets.values())`.

Hint 3: For the O(k) key: count the 26 letters into a fixed-size list and turn
        that count vector into a tuple. `tuple([1,0,...,1])` is hashable and two
        anagrams always produce the same count vector.


COMPLEXITY TARGET
-----------------
    n = number of strings, k = max string length

    Time:  O(n * k log k) with the sorted key  —  acceptable
           O(n * k)       with the count key   —  optimal
    Space: O(n * k) for the output
================================================================================
*/

// TODO: Implement the stub
