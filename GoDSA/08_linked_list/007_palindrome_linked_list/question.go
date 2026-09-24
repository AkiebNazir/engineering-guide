package main

/*
================================================================================
LeetCode 234 · Palindrome Linked List                                    [Easy]
https://leetcode.com/problems/palindrome-linked-list/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given the head of a singly linked list, return true if it is a palindrome.


EXAMPLES
--------
Example 1:
    Input:  head = [1,2,2,1]
    Output: true

Example 2:
    Input:  head = [1,2]
    Output: false


CONSTRAINTS
-----------
    The number of nodes in the list is in the range [1, 10^5].
    0 <= Node.Val <= 9

FOLLOW UP
---------
    Could you do it in O(n) time and O(1) space?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

A palindrome check wants both ends at once; a singly linked list only walks
forward. The O(1)-space trick: find the middle (problem 004's slow/fast),
reverse the second half in place (problem 001's reversal), then walk the
first half and the reversed second half TOGETHER as if they were two
independent forward lists meeting in the middle.

    1. slow/fast to the middle
    2. reverse everything from the middle onward
    3. walk head and the reversed second half together, comparing Val;
       stop when either pointer runs out

O(n) time (three linear passes, still O(n) total), O(1) EXTRA space.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. Reversing the second half PERMANENTLY mutates the caller's list unless
   you explicitly reverse it back afterward -- a real side-effect risk if
   the list is reused after the call.

2. The compare loop must stop when EITHER pointer runs out, not both -- for
   odd length, the first half's pointer still has the (irrelevant) middle
   node left after the second half's pointer is exhausted.

3. `slow == fast` style pointer identity is not what's being compared here --
   this problem compares `.Val` fields, since the two halves are genuinely
   different node sequences (except the shared middle node on odd length).


PROGRESSIVE HINTS
------------------
Hint 1: You need a "backward" pointer on a structure that only walks
        forward. Either copy into a slice, or reverse half of it in place.

Hint 2: Find the middle with slow/fast (problem 004), then reverse from the
        middle onward using the reversal template (problem 001).

Hint 3: Compare head-forward against reversed-second-half-forward, node by
        node, stopping when either side runs out.


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

// YourIsPalindrome is your attempt.
// Implement it, then run:  cd GoDSA && go run ./08_linked_list/007_palindrome_linked_list
func YourIsPalindrome(head *ListNode) bool {
	// YOUR CODE HERE
	return false
}
