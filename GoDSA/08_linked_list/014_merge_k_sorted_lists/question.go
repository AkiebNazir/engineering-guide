package main

/*
================================================================================
LeetCode 23 · Merge k Sorted Lists                                       [Hard]
https://leetcode.com/problems/merge-k-sorted-lists/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
You are given an array of k linked-lists lists, each linked-list is sorted
in ascending order. Merge all the linked-lists into one sorted linked list
and return it.

EXAMPLES
--------
Example 1:
    Input:  lists = [[1,4,5],[1,3,4],[2,6]]
    Output: [1,1,2,3,4,4,5,6]

Example 2:
    Input:  lists = []
    Output: []

Example 3:
    Input:  lists = [[]]
    Output: []

CONSTRAINTS
-----------
    k == len(lists)
    0 <= k <= 10^4
    0 <= len(lists[i]) <= 500
    -10^4 <= lists[i][j] <= 10^4
    lists[i] is sorted in ascending order.
    The sum of len(lists[i]) will not exceed 10^4.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Merging TWO sorted lists (LC 21) is O(n+m) with a dummy head and two
pointers. Merging k lists is the same idea scaled up: the question is HOW to
pick the next-smallest head among k candidates efficiently. A brute-force
sequential merge (fold the lists together one at a time) does that pick in
O(k) each time; a min-heap does it in O(log k); divide-and-conquer pairwise
merging does it without a heap at all, still O(log k) per element overall.


PROGRESSIVE HINTS
------------------
Hint 1: You already know how to merge TWO sorted lists — can you fold that
        over the k lists one at a time?
Hint 2: What data structure gives you the minimum of k candidates in
        O(log k) instead of O(k)?
Hint 3: Merging in PAIRS (list 0 with list 1, list 2 with list 3, ...) and
        repeating halves the number of lists each round — how many rounds,
        and what's the total work?


COMPLEXITY TARGET
------------------
    Time:  O(N log k), where N is the total number of nodes across all lists
    Space: O(k) or O(log k) depending on approach
================================================================================
*/

// ListNode is the standard singly linked list node.
type ListNode struct {
	Val  int
	Next *ListNode
}

// YourMergeKLists is your attempt.
// Implement it, then run: cd GoDSA && go run ./08_linked_list/014_merge_k_sorted_lists
func YourMergeKLists(lists []*ListNode) *ListNode {
	// YOUR CODE HERE
	return nil
}
