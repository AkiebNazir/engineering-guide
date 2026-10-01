package main

import "fmt"

/*
================================================================================
LeetCode 677 · Map Sum Pairs                                            [Medium]
https://leetcode.com/problems/map-sum-pairs/
Topic: 13 · Trie
================================================================================

PROBLEM
-------
Design a map that allows insertion of key-value string/int pairs, and querying
the sum of all values whose keys start with a given prefix.

Implement the MapSum class:

    MapSum()                         initializes the object.
    void insert(String key, int val) inserts key -> val into the map. If key
                                      already existed, the previous value is
                                      OVERWRITTEN with val (not added to it).
    int sum(String prefix)           returns the sum of all pairs' values
                                      whose key starts with prefix.

EXAMPLE
-------
    Input:
        ["MapSum", "insert", "sum", "insert", "sum"]
        [[], ["apple", 3], ["ap"], ["app", 2], ["ap"]]
    Output:
        [None, None, 3, None, 5]

    Explanation:
        mapSum = MapSum()
        mapSum.insert("apple", 3)
        mapSum.sum("ap")           -> 3     (only "apple" starts with "ap")
        mapSum.insert("app", 2)
        mapSum.sum("ap")           -> 5     ("apple"=3 + "app"=2)

CONSTRAINTS
-----------
    1 <= key.length, prefix.length <= 50
    key and prefix consist of only lowercase English letters.
    1 <= val <= 1000
    At most 50 calls will be made to insert and sum.

See PyDSA/13_trie/_TOPIC_GUIDE.md Part 6 (augmenting trie nodes) before writing
this. Watch out for the re-insert-overwrites-not-adds trap in the EXAMPLE below.
================================================================================
*/

func main() {
	fmt.Println("Solution for Map Sum Pairs not implemented yet")
}
