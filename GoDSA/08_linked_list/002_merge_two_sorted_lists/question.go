package main

/*
================================================================================
LeetCode 21 · Merge Two Sorted Lists                                     [Easy]
https://leetcode.com/problems/merge-two-sorted-lists/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
You are given the heads of two sorted linked lists list1 and list2. Merge
the two lists into one SORTED list. The list should be made by splicing
together the nodes of the first two lists.

Return the head of the merged linked list.


EXAMPLES
--------
Example 1:
    Input:  list1 = [1,2,4], list2 = [1,3,4]
    Output: [1,1,2,3,4,4]

Example 2:
    Input:  list1 = [], list2 = []
    Output: []

Example 3:
    Input:  list1 = [], list2 = [0]
    Output: [0]


CONSTRAINTS
-----------
    The number of nodes in both lists is in the range [0, 50].
    -100 <= Node.Val <= 100
    Both list1 and list2 are sorted in non-decreasing order.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is the merge step of merge sort, minus the array-allocation cost — both
inputs are already sorted, so at any moment you only ever need to compare
the two current FRONT nodes, and "inserting" the winner is a pointer rewrite,
not an array write.

The catch is the standard one for this topic: either list could be empty, or
run out first, so use a dummy/sentinel head (Part 2 of the topic guide) —
`tail` starts ONE STEP BEFORE the real merged list, so attaching the first
real node needs no special case.

    dummy := &ListNode{}
    tail := dummy
    for list1 != nil && list2 != nil {
        if list1.Val <= list2.Val {
            tail.Next = list1
            list1 = list1.Next
        } else {
            tail.Next = list2
            list2 = list2.Next
        }
        tail = tail.Next
    }
    if list1 != nil {
        tail.Next = list1
    } else {
        tail.Next = list2
    }
    return dummy.Next


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. `dummy := &ListNode{}` — one allocation buys you a loop body with zero
   head-of-list special casing.

2. Don't allocate NEW nodes for the merged result — reuse the existing ones
   by rewiring `Next`. Allocating fresh `&ListNode{Val: ...}` for each
   element works but wastes O(n+m) space the problem doesn't need.

3. `tail.Next = list1` when list2 is exhausted (or vice versa) splices the
   ENTIRE remainder in O(1) — no need to walk it node by node, it's already
   sorted.


PROGRESSIVE HINTS
------------------
Hint 1: Use a dummy head so "the merged list has no nodes yet" needs no
        special-case branch.

Hint 2: Advance whichever list has the smaller current value, and move
        `tail` along with it.

Hint 3: When one list runs out, attach the ENTIRE remainder of the other in
        one line — it's already sorted, no need to loop further.


COMPLEXITY TARGET
------------------
    Time:  O(n + m)
    Space: O(1) — reuse existing nodes, do not allocate new ones
================================================================================
*/

type ListNode struct {
	Val  int
	Next *ListNode
}

// YourMergeTwoLists is your attempt.
// Implement it, then run:  cd GoDSA && go run ./08_linked_list/002_merge_two_sorted_lists
func YourMergeTwoLists(list1 *ListNode, list2 *ListNode) *ListNode {
	// YOUR CODE HERE
	return nil
}
