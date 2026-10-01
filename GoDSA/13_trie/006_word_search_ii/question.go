package main

/*
================================================================================
LeetCode 212 · Word Search II                                             [Hard]
https://leetcode.com/problems/word-search-ii/
Topic: 13 · Trie
================================================================================

PROBLEM
-------
Given an `m x n` grid of characters `board` and a list of strings `words`,
return ALL words on the board.

Each word must be constructed from letters of sequentially adjacent cells,
where adjacent cells are horizontally or vertically neighboring. The same
letter cell may NOT be used more than once in a single word.

EXAMPLE
-------
    Input:
        board = [["o","a","a","n"],
                 ["e","t","a","e"],
                 ["i","h","k","r"],
                 ["i","f","l","v"]]
        words = ["oath","pea","eat","rain"]
    Output:
        ["eat","oath"]

    Input:
        board = [["a","b"],["c","d"]]
        words = ["abcb"]
    Output:
        []
        (no path can revisit a cell, so "abcb" is unreachable even though
         it "looks" traceable ignoring the no-reuse rule)

CONSTRAINTS
-----------
    m == board.length
    n == board[i].length
    1 <= m, n <= 12
    board[i][j] is a lowercase English letter.
    1 <= words.length <= 3 * 10^4
    1 <= words[i].length <= 10
    words[i] consists of lowercase English letters.
    All words[i] are unique.

See PyDSA/13_trie/_TOPIC_GUIDE.md Part 3 point 3 before writing this: build
ONE trie from the whole word list, then run a SINGLE DFS/backtracking pass
over the grid, walking the trie in lockstep with the grid path. Checking
each word independently against the grid (topic 09's plain Word Search,
called once per word) would repeat shared prefix work across words that
start the same way.
================================================================================
*/

// TODO: Implement the stub
