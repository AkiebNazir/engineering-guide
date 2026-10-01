package main

/*
================================================================================
LeetCode 1268 · Search Suggestions System                               [Medium]
https://leetcode.com/problems/search-suggestions-system/
Topic: 13 · Trie (Prefix Tree)
================================================================================

PROBLEM
-------
You are given an array of strings `products` and a string `searchWord`.

Design a system that suggests at most three product names from `products`
after each character of `searchWord` is typed. Suggested products should have
a common prefix with searchWord. If there are more than three products with a
common prefix, return the three LEXICOGRAPHICALLY smallest.

Return a list of lists of the suggested products after each character of
searchWord is typed.


EXAMPLES
--------
Example 1:
    Input:  products = ["mobile","mouse","moneypot","monitor","mousepad"],
            searchWord = "mouse"
    Output: [["mobile","moneypot","monitor"],
             ["mobile","moneypot","monitor"],
             ["mouse","mousepad"],
             ["mouse","mousepad"],
             ["mouse","mousepad"]]
    Explanation: sorted products = ["mobile","moneypot","monitor","mouse","mousepad"].
                 "m" and "mo" match all five -> first three.
                 "mou", "mous", "mouse" match only "mouse" and "mousepad".

Example 2:
    Input:  products = ["havana"], searchWord = "tatiana"
    Output: [[],[],[],[],[],[],[]]


CONSTRAINTS
-----------
    1 <= products.length <= 1000
    1 <= products[i].length <= 3000
    1 <= sum(products[i].length) <= 2 * 10^4
    All the strings of products are unique.
    products[i] consists of lowercase English letters.
    1 <= searchWord.length <= 1000
    searchWord consists of lowercase English letters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is a tiny autocomplete. Two classic designs, both worth knowing:

    1. SORT + BINARY SEARCH. In a sorted list, all words with a given prefix
       sit in one contiguous block, and the block starts at
       bisect_left(products, prefix). Take up to three from there, checking
       each really starts with the prefix.

    2. TRIE with the top three words stored at every node. Walking one
       character down the trie per typed character gives the suggestions in
       O(1) per keystroke.

The trie version is what a real autocomplete service does (precomputed
top-k per prefix). The sorted-list version is less code for a one-off query.


WHAT TO THINK ABOUT
--------------------
1. Why are all words sharing a prefix contiguous in sorted order?

2. bisect_left(products, prefix) lands at the first word >= prefix. Is that
   word guaranteed to start with the prefix?

3. In the trie approach, if you insert words in sorted order, how do you keep
   only the three smallest at each node?

4. Once a prefix has no matches, can a longer prefix have any?


PROGRESSIVE HINTS
------------------
Hint 1: products.sort(). For each prefix, i = bisect_left(products, prefix).

Hint 2: Take products[i:i+3] but keep only those that startswith(prefix).

Hint 3 (trie): insert sorted words; at each node append the word to
        node.top if len(node.top) < 3.


COMPLEXITY TARGET
------------------
    Sort + binary search: O(n log n * L + m * (log n * L))
    Trie: O(total characters) build, O(m) to answer (plus output size)
================================================================================
*/

// TODO: Implement the stub
