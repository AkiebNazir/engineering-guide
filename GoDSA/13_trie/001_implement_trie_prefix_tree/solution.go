package main

import "fmt"

/*
================================================================================
LeetCode 208 · Implement Trie (Prefix Tree)                             [Medium]
https://leetcode.com/problems/implement-trie-prefix-tree/
Topic: 13 · Trie
================================================================================

PROBLEM
-------
A trie (pronounced "try") is a tree data structure used to efficiently store
and retrieve keys in a dataset of strings. Implement the Trie class:

    Trie()                       initializes the trie object.
    void insert(String word)     inserts the string word into the trie.
    boolean search(String word)  returns True if word is in the trie
                                  (i.e. was inserted), False otherwise.
    boolean startsWith(String prefix)
                                  returns True if a previously inserted word
                                  has prefix as a prefix, False otherwise.

EXAMPLE
-------
    Input:
        ["Trie", "insert", "search", "search", "startsWith", "insert", "search"]
        [[], ["apple"], ["apple"], ["app"], ["app"], ["app"], ["app"]]
    Output:
        [None, None, True, False, True, None, True]

    Explanation:
        trie = Trie()
        trie.insert("apple")
        trie.search("apple")     -> True
        trie.search("app")       -> False   ("app" was never inserted whole)
        trie.startsWith("app")   -> True    ("apple" starts with "app")
        trie.insert("app")
        trie.search("app")       -> True

CONSTRAINTS
-----------
    1 <= word.length, prefix.length <= 2000
    word and prefix consist only of lowercase English letters.
    At most 3 * 10^4 calls in total will be made to insert, search, startsWith.

See PyDSA/13_trie/_TOPIC_GUIDE.md Part 1-2 for the dict-vs-array node
representation trade-off and the search-vs-startsWith is_word bug before
writing this.
================================================================================
*/

func main() {
	fmt.Println("Solution for Implement Trie (Prefix Tree) not implemented yet")
}
