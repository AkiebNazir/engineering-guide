package main

import "fmt"

/*
================================================================================
PROBLEM 1: Factorial of N (The "Hello World" of Recursion)
================================================================================

Write a recursive function that returns the factorial of a given number N.
Factorial of N (denoted as N!) is the product of all positive integers less than or equal to N.
Example: 5! = 5 * 4 * 3 * 2 * 1 = 120

Base Case Hint: 0! is mathematically defined as 1.

Example 1:
Input: n = 5
Output: 120

Example 2:
Input: n = 0
Output: 1

Constraints:
0 <= n <= 12

================================================================================
YOUR TASK:
Implement the `factorial` function recursively. 
Do NOT use a loop (for/while).
================================================================================
CALL STACK VISUALIZATION for factorial(3)
================================================================================

THE DIVE (Building the stack):
------------------------------
| Box 1: factorial(3)                  |
| n = 3                                |
| Paused at: return 3 * factorial(2)   | <-- Waiting for Box 2
------------------------------

| Box 2: factorial(2)                  |
| n = 2                                |
| Paused at: return 2 * factorial(1)   | <-- Waiting for Box 3
------------------------------

| Box 3: factorial(1)                  |
| n = 1                                |
| Paused at: return 1 * factorial(0)   | <-- Waiting for Box 4
------------------------------

| Box 4: factorial(0)   [BASE CASE!]   |
| n = 0                                |
| Returns: 1 (Box is destroyed)        |
------------------------------

BUBBLING UP (Unwinding the stack):
----------------------------------
1. Box 3 unpauses: return 1 * (1) -> returns 1
2. Box 2 unpauses: return 2 * (1) -> returns 2
3. Box 1 unpauses: return 3 * (2) -> returns 6 (Final Answer)
================================================================================
*/

func factorial(n int) int {
	// TODO: Your recursive code here
	return 0
}

func main() {
	fmt.Println("--- Test Case 1 ---")
	fmt.Println("Input: n = 5")
	fmt.Printf("Output: %d\n", factorial(5))
	fmt.Println("Expected: 120\n")

	fmt.Println("--- Test Case 2 ---")
	fmt.Println("Input: n = 0")
	fmt.Printf("Output: %d\n", factorial(0))
	fmt.Println("Expected: 1\n")

	fmt.Println("--- Test Case 3 ---")
	fmt.Println("Input: n = 3")
	fmt.Printf("Output: %d\n", factorial(3))
	fmt.Println("Expected: 6\n")
}
