package main

import "fmt"

/*
================================================================================
PROBLEM: Reverse a Linked List (MAANG Classic)
================================================================================

Given the head of a singly linked list, reverse the list, and return the reversed list.

Example 1:
Input: head = [1,2,3,4,5]
Output: [5,4,3,2,1]

Example 2:
Input: head = [1,2]
Output: [2,1]

Example 3:
Input: head = []
Output: []

Constraints:
- The number of nodes in the list is the range [0, 5000].
- -5000 <= Node.val <= 5000

================================================================================
YOUR TASK:
Implement the `reverseList` function.
Try to do this iteratively first. If you finish quickly, try the recursive approach!
================================================================================
*/

// Definition for singly-linked list.
type ListNode struct {
	Val  int
	Next *ListNode
}

func reverseList(head *ListNode) *ListNode {
	// TODO: Your code here
	return nil
}

func printList(node *ListNode) {
	if node == nil {
		fmt.Println("Empty")
		return
	}
	for node != nil {
		fmt.Printf("%d ", node.Val)
		if node.Next != nil {
			fmt.Print("-> ")
		}
		node = node.Next
	}
	fmt.Println()
}

func createList(arr []int) *ListNode {
	if len(arr) == 0 {
		return nil
	}
	head := &ListNode{Val: arr[0]}
	curr := head
	for i := 1; i < len(arr); i++ {
		curr.Next = &ListNode{Val: arr[i]}
		curr = curr.Next
	}
	return head
}

func main() {
	// Test Case 1
	l1 := createList([]int{1, 2, 3, 4, 5})
	fmt.Print("Input:  ")
	printList(l1)
	fmt.Print("Output: ")
	printList(reverseList(l1))
	fmt.Println()

	// Test Case 2
	l2 := createList([]int{1, 2})
	fmt.Print("Input:  ")
	printList(l2)
	fmt.Print("Output: ")
	printList(reverseList(l2))
	fmt.Println()

	// Test Case 3
	l3 := createList([]int{})
	fmt.Print("Input:  ")
	printList(l3)
	fmt.Print("Output: ")
	printList(reverseList(l3))
}
