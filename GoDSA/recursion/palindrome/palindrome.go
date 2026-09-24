package main

import "fmt"

/*
================================================================================
PROBLEM 3: Valid Palindrome (Recursive with Pointers)
================================================================================

A string is a palindrome if it reads the same forward and backward.
Example: "racecar", "madam", "a"

Example 1:
Input: s = "racecar"
Output: true

Example 2:
Input: s = "hello"
Output: false

Constraints:
1 <= s.length <= 1000
s consists of only lowercase English letters.

================================================================================
YOUR TASK:
Implement `isPalindrome` recursively.
HINT: Create a helper function that takes a `left` index and a `right` index.
Base case: What happens when `left` meets or passes `right`?
================================================================================
CALL STACK VISUALIZATION for "racecar"
================================================================================

THE DIVE (Building the stack):
------------------------------
| Box 1: check(0, 6)                   |
| s[0]='r', s[6]='r'                   |
| Paused at: return check(1, 5)        | <-- Waiting for Box 2
------------------------------

| Box 2: check(1, 5)                   |
| s[1]='a', s[5]='a'                   |
| Paused at: return check(2, 4)        | <-- Waiting for Box 3
------------------------------

| Box 3: check(2, 4)                   |
| s[2]='c', s[4]='c'                   |
| Paused at: return check(3, 3)        | <-- Waiting for Box 4
------------------------------

| Box 4: check(3, 3)    [BASE CASE!]   |
| left == right (3 == 3)               |
| Returns: true (Box is destroyed)     |
------------------------------

BUBBLING UP (Unwinding the stack):
----------------------------------
1. Box 3 unpauses: return true
2. Box 2 unpauses: return true
3. Box 1 unpauses: return true (Final Answer)
================================================================================
*/

// func check(s string, l, r int) bool {
// 	if l >= r {
// 		return true
// 	}
// 	if s[l] != s[r] {
// 		return false
// 	}
// 	return check(s, l+1, l-1)
// }

func isPalindrome(s string) bool {
	var check func(l, r int) bool
	check = func(l, r int) bool {
		if l >= r {
			return true
		}
		if s[l] != s[r] {
			return false
		}
		return check(l+1, r-1)
	}
	return check(0, len(s)-1)
}

func main() {
	fmt.Println("--- Test Case 1 ---")
	fmt.Println("Input: \"racecar\"")
	fmt.Printf("Output: %t\n", isPalindrome("racecar"))
	fmt.Println("Expected: true\n")

	fmt.Println("--- Test Case 2 ---")
	fmt.Println("Input: \"hello\"")
	fmt.Printf("Output: %t\n", isPalindrome("hello"))
	fmt.Println("Expected: false\n")

	fmt.Println("--- Test Case 3 ---")
	fmt.Println("Input: \"a\"")
	fmt.Printf("Output: %t\n", isPalindrome("a"))
	fmt.Println("Expected: true\n")
}
