package main

/*
================================================================================
LeetCode 83 · Remove Duplicates from Sorted List                         [Easy]
https://leetcode.com/problems/remove-duplicates-from-sorted-list/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a SORTED linked list, delete all duplicates such that each
element appears only once. Return the linked list, still sorted.


EXAMPLES
--------
Example 1:
    Input:  head = [1,1,2]
    Output: [1,2]

Example 2:
    Input:  head = [1,1,2,3,3]
    Output: [1,2,3]


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [0, 300].
    -100 <= Node.Val <= 100
    The list is guaranteed to be sorted in ascending order.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Because the input is SORTED, duplicates of any value are always physically
ADJACENT -- never scattered. So "remove duplicates" collapses from a general
membership problem into a one-pointer adjacent scan: compare curr.Val with
curr.Next.Val; splice out a match; otherwise advance.

    curr := head
    for curr != nil && curr.Next != nil {
        if curr.Val == curr.Next.Val {
            curr.Next = curr.Next.Next   // skip the duplicate; curr stays put
        } else {
            curr = curr.Next             // advance only past a KEPT node
        }
    }
    return head

No dummy head needed: the head node is never itself a deletion candidate
here, only its later duplicates are -- head as a value is always returned
unchanged.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. `curr.Next = curr.Next.Next` reroutes the pointer directly -- no separate
   node needs to be allocated or freed; Go's GC reclaims the skipped node
   once nothing references it.

2. The loop condition needs BOTH `curr != nil` and `curr.Next != nil`, same
   nil-guard discipline as problems 003 and 004.

3. `curr` deliberately does NOT advance after a deletion -- this is what
   makes a run of 3+ identical values collapse to one, not just drop from
   3 down to 2.


PROGRESSIVE HINTS
------------------
Hint 1: Sorted input means duplicates are always neighbors -- you never need
        to remember anything beyond "am I equal to the node right after me."

Hint 2: On a match, rewire curr.Next past the duplicate and leave curr where
        it is -- advancing curr on a match only removes ONE of a longer run.

Hint 3: No dummy head is needed here (contrast problem 005) -- the head is
        never itself deleted in THIS problem.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

type ListNode struct {
	Val  int
	Next *ListNode
}

// YourDeleteDuplicates is your attempt.
// Implement it, then run:  cd GoDSA && go run ./08_linked_list/006_remove_duplicates_from_sorted_list
func YourDeleteDuplicates(head *ListNode) *ListNode {
	// YOUR CODE HERE
	return nil
}
