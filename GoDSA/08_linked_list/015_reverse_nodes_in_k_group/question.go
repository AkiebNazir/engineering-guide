package main

/*
================================================================================
LeetCode 25 · Reverse Nodes in k-Group                                   [Hard]
https://leetcode.com/problems/reverse-nodes-in-k-group/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a linked list, reverse the nodes of the list k at a time,
and return the modified list.

k is a positive integer and is less than or equal to the length of the
linked list. If the number of nodes is not a multiple of k then LEFT-OUT
nodes, in the end, should remain AS IS.

You may not alter the values in the list's nodes, only nodes themselves may
be changed.

EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4,5], k = 2
    Output: [2,1,4,3,5]

Example 2:
    Input:  head = [1,2,3,4,5], k = 3
    Output: [3,2,1,4,5]

CONSTRAINTS
-----------
    The number of nodes is n.
    1 <= k <= n <= 5000
    0 <= Node.Val <= 1000

FOLLOW UP
---------
    Could you solve the problem in O(1) extra memory space?
    You may not reorder the values in the list — only nodes may be changed.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is problem 001's iterative reversal (prev/curr/next), applied to a
SLICE of the list k nodes at a time, glued back together group by group. The
sharp edge is the LAST group: if fewer than k nodes remain, leave them
unreversed — which means you must COUNT ahead (or otherwise check) before
committing to reverse a group, since reversing first and "undoing" it is
wasted work and error-prone.


PROGRESSIVE HINTS
------------------
Hint 1: Use a dummy head (topic guide §2) so the very first group's
        reversal isn't a special case at the list head.
Hint 2: Before reversing a group, check whether k nodes actually remain —
        if not, stop and leave the rest as-is.
Hint 3: After reversing a group, the ORIGINAL first node of that group is
        now its tail — it must be relinked to the (recursively/iteratively
        processed) rest of the list, and the previous group's tail must be
        relinked to point at the new group head.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1) iterative (O(n/k) recursion stack if solved recursively)
================================================================================
*/

// ListNode is the standard singly linked list node.
type ListNode struct {
	Val  int
	Next *ListNode
}

// YourReverseKGroup is your attempt.
// Implement it, then run: cd GoDSA && go run ./08_linked_list/015_reverse_nodes_in_k_group
func YourReverseKGroup(head *ListNode, k int) *ListNode {
	// YOUR CODE HERE
	return nil
}
