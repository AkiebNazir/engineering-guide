package main

/*
================================================================================
LeetCode 143 · Reorder List                                            [Medium]
https://leetcode.com/problems/reorder-list/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
You are given the head of a singly linked list. The list can be represented
as:

    L0 -> L1 -> ... -> Ln-1 -> Ln

Reorder the list to be on the following form:

    L0 -> Ln -> L1 -> Ln-1 -> L2 -> Ln-2 -> ...

You may not modify the values in the list's nodes. Only nodes themselves may
be changed. Do it IN PLACE (no return value).

EXAMPLES
--------
Example 1:
    Input:  head = [1,2,3,4]
    Output: [1,4,2,3]

Example 2:
    Input:  head = [1,2,3,4,5]
    Output: [1,5,2,4,3]

CONSTRAINTS
-----------
    The number of nodes is in the range [1, 5 * 10^4]
    1 <= Node.Val <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is a composition of three techniques already in this topic's toolbox:
find the middle (fast/slow), reverse a sublist, and merge two lists by
alternating nodes. No new algorithm is needed — just wire the three together
in the right order.


PROGRESSIVE HINTS
------------------
Hint 1: Find the middle of the list with fast/slow pointers.
Hint 2: Reverse the second half (from the middle to the end).
Hint 3: Merge the first half and reversed second half, alternating one node
        from each. The loop should stop when the (shorter-or-equal) second
        half runs out.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

// ListNode is the standard singly linked list node.
type ListNode struct {
	Val  int
	Next *ListNode
}

// YourReorderList is your attempt.
// Implement it, then run: cd GoDSA && go run ./08_linked_list/008_reorder_list
func YourReorderList(head *ListNode) {
	// YOUR CODE HERE
}
