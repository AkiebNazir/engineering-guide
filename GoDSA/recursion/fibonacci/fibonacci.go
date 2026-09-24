package main

import "fmt"

/*
================================================================================
PROBLEM 2: Nth Fibonacci Number (Branching Recursion)
================================================================================

The Fibonacci sequence is a series of numbers where each number is the sum of
the two preceding ones, usually starting with 0 and 1.
Sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34...

F(0) = 0, F(1) = 1
F(n) = F(n - 1) + F(n - 2), for n > 1.

Example 1:
Input: n = 2
Output: 1 (Explanation: F(2) = F(1) + F(0) = 1 + 0 = 1)

Example 2:
Input: n = 4
Output: 3 (Explanation: F(4) = F(3) + F(2) = 2 + 1 = 3)

Constraints:
0 <= n <= 30
================================================================================
YOUR TASK:
Implement the `fibonacci` function recursively.
Think about the base cases (there are TWO!).
================================================================================
CALL TREE VISUALIZATION for fibonacci(6)
================================================================================

Unlike Factorial which is a straight line, Fibonacci branches out like a tree!
Every node splits into TWO recursive calls until it hits the base cases (1 or 0).

                               fib(6)
                             /        \
                      fib(5)            fib(4)
                     /      \           /      \
                fib(4)      fib(3)   fib(3)    fib(2)
               /     \       /    \    /   \     /   \
           fib(3)  fib(2) fib(2) f(1) f(2) f(1) f(1) f(0)
           /   \    /   \  /   \      /   \
       f(2) f(1) f(1) f(0)f(1)f(0)   f(1) f(0)
       /  \
     f(1) f(0)

Notice how `fib(4)` is calculated TWO separate times?
And `fib(3)` is calculated THREE separate times?
This is why standard recursive Fibonacci is very slow for large numbers.
It recalculates the same problems over and over again!
================================================================================
*/

func fibonacci(n int) int {
	if n == 0 || n == 1 {
		return n
	}
	return fibonacci(n-1) + fibonacci(n-2)
}

func main() {
	fmt.Println("--- Test Case 1 ---")
	fmt.Println("Input: n = 2")
	fmt.Printf("Output: %d\n", fibonacci(2))
	fmt.Println("Expected: 1\n")

	fmt.Println("--- Test Case 2 ---")
	fmt.Println("Input: n = 4")
	fmt.Printf("Output: %d\n", fibonacci(4))
	fmt.Println("Expected: 3\n")

	fmt.Println("--- Test Case 3 ---")
	fmt.Println("Input: n = 0")
	fmt.Printf("Output: %d\n", fibonacci(0))
	fmt.Println("Expected: 0\n")
}
