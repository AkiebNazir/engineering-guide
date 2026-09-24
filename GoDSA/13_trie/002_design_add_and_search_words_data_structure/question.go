package main

/*
================================================================================
LeetCode 211 · Design Add and Search Words Data Structure               [Medium]
https://leetcode.com/problems/design-add-and-search-words-data-structure/
Topic: 13 · Trie
================================================================================

PROBLEM
-------
Design a data structure that supports adding new words and finding if a
string matches any previously added string.

Implement the WordDictionary class:

    WordDictionary()              initializes the object.
    void addWord(word)            adds `word` to the data structure, it can
                                   be matched later.
    bool search(word)             returns True if there is any string in the
                                   data structure that matches `word`.
                                   `word` may contain '.' characters, where
                                   '.' can match ANY single letter.

EXAMPLE
-------
    Input:
        ["WordDictionary", "addWord", "addWord", "addWord", "search",
         "search", "search", "search"]
        [[], ["bad"], ["dad"], ["mad"], ["pad"], ["bad"], [".ad"], ["b.."]]
    Output:
        [None, None, None, None, False, True, True, True]

    Explanation:
        wd = WordDictionary()
        wd.addWord("bad")
        wd.addWord("dad")
        wd.addWord("mad")
        wd.search("pad")   -> False   ("pad" was never added)
        wd.search("bad")   -> True    (added exactly)
        wd.search(".ad")   -> True    ('.' matches 'b', 'd', or 'm')
        wd.search("b..")   -> True    (both '.' match 'a' and 'd')

CONSTRAINTS
-----------
    1 <= word.length <= 25
    word in addWord consists of lowercase English letters.
    word in search consists of '.' or lowercase English letters.
    There will be at most 2 dots in word for search queries.
    At most 10^4 calls will be made to addWord and search.

See PyDSA/13_trie/_TOPIC_GUIDE.md Part 4 (wildcard search via DFS over the
trie) before writing this. The key difference from 001: search can no
longer be a straight-line walk, because '.' means "try every live child".
================================================================================
*/

// TODO: Implement the stub
