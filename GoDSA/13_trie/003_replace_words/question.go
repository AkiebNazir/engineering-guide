package main

/*
================================================================================
LeetCode 648 · Replace Words                                            [Medium]
https://leetcode.com/problems/replace-words/
Topic: 13 · Trie
================================================================================

PROBLEM
-------
In English, we have a concept called "root", which can be followed by some
other word to form another longer word - let's call this word "derivative".
For example, when the root "help" is followed by the word "ful", we can
form a derivative "helpful".

Given a `dictionary` consisting of many roots and a `sentence` consisting of
words separated by spaces, replace all the derivatives in the sentence with
the ROOT forming it. If a derivative can be replaced by more than one root,
replace it with the root that has the SHORTEST length.

Return the sentence after the replacement.

EXAMPLE
-------
    Input:
        dictionary = ["cat","bat","rat"]
        sentence = "the cattle was rattled by the battery"
    Output:
        "the cat was rat by the bat"

    Input:
        dictionary = ["a","b","c"]
        sentence = "aadsfasf absbs bbab cadsfafs"
    Output:
        "a a b c"

    Explanation of a tie: dictionary = ["cat", "cattle"], word "cattle" ->
    both "cat" and "cattle" are roots of it; the SHORTER one, "cat", wins.

CONSTRAINTS
-----------
    1 <= dictionary.length <= 1000
    1 <= dictionary[i].length <= 100
    dictionary[i] consists of only lowercase letters.
    1 <= sentence.length <= 10^6
    sentence consists of only lowercase letters and spaces.
    The number of words in sentence is in the range [1, 1000]
    The length of each word in sentence is in the range [1, 1000]
    Every two consecutive words in sentence will be separated by exactly
    one space.
    sentence does not have leading or trailing spaces.

See PyDSA/13_trie/_TOPIC_GUIDE.md Part 3 point 5 (shortest-prefix matching)
before writing this: walk a trie character by character and stop at the
FIRST is_word you hit — that first hit is guaranteed to be the shortest
root, because you haven't gone any deeper yet.
================================================================================
*/

// TODO: Implement the stub
