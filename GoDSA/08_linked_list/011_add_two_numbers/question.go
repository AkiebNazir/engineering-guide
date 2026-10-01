package main

/*
================================================================================
LeetCode 2 · Add Two Numbers                                          [Medium]
https://leetcode.com/problems/add-two-numbers/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
You are given two non-empty linked lists representing two non-negative
integers. The digits are stored in REVERSE order, and each node contains a
single digit. Add the two numbers and return the sum as a linked list, in
the same reverse-digit format.

You may assume the two numbers do not contain any leading zero, except the
number 0 itself.

EXAMPLES
--------
Example 1:
    Input:  l1 = [2,4,3], l2 = [5,6,4]
    Output: [7,0,8]           (342 + 465 = 807)

Example 2:
    Input:  l1 = [0], l2 = [0]
    Output: [0]

Example 3:
    Input:  l1 = [9,9,9,9,9,9,9], l2 = [9,9,9,9]
    Output: [8,9,9,9,0,0,0,1]  (9999999 + 9999 = 10009998)

CONSTRAINTS
-----------
    The number of nodes in each linked list is in the range [1, 100].
    0 <= Node.Val <= 9
    It is guaranteed that the list represents a number without leading zeros.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Reversed storage means you already walk least-significant-digit-first —
exactly the order grade-school column addition needs. Walk both lists
together, add digit + digit + carry at each position, emit one new node per
position. The two lists can have different lengths (treat a missing node as
digit 0), and a final leftover carry needs one MORE node past the end of
both inputs.

A dummy node avoids special-casing "the first node of a freshly built
result" — see the Go topic guide's Part 2 on the dummy node idiom.


WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. Go has no operator overloading and no arbitrary-precision integers by
   default — int overflow is a real risk in OTHER problems, but not here:
   each digit is 0-9 and the sum of two digits plus carry never exceeds 19,
   comfortably inside any Go int.

2. `l1.Next` on a nil `*ListNode` panics — guard with `if l1 != nil` before
   dereferencing, every time you advance.


PROGRESSIVE HINTS
------------------
Hint 1: Add digit by digit, carrying into the next position, same as
        grade-school addition — reversed storage is already the right order.

Hint 2: Missing digits (shorter list) count as 0, not "stop".

Hint 3: Loop while EITHER list still has nodes OR a carry remains.


COMPLEXITY TARGET
------------------
    Time:  O(max(m, n))
    Space: O(max(m, n)) for the required output
================================================================================
*/

type ListNode struct {
	Val  int
	Next *ListNode
}

// YourAddTwoNumbers is your attempt.
// Implement it, then run:  cd GoDSA && go run ./08_linked_list/011_add_two_numbers
func YourAddTwoNumbers(l1 *ListNode, l2 *ListNode) *ListNode {
	// YOUR CODE HERE
	return nil
}
