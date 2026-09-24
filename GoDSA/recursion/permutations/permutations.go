package main

import (
	"fmt"
	"sort"
)

/*
================================================================================
PROBLEM 5: Permutations (Backtracking Level 2 — The "Choose From Available" Pattern)
================================================================================

Given an array `nums` of distinct integers, return all the possible
permutations. You can return the answer in any order.

Example 1:
Input: nums = [1,2,3]
Output: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]

Example 2:
Input: nums = [0,1]
Output: [[0,1],[1,0]]

Example 3:
Input: nums = [1]
Output: [[1]]

Constraints:
1 <= len(nums) <= 6
All elements of nums are unique.

================================================================================

WHY THIS IS A LEVEL UP FROM SUBSETS:
================================================================================
In Subsets, at each index you made a BINARY choice:
  → "Include nums[i]?" YES or NO. That's it. Two branches per node.

In Permutations, at each position you ask a DIFFERENT question:
  → "Which of the REMAINING numbers should I place here?"
  → The number of branches SHRINKS as you go deeper!
    Level 0: 3 choices → Level 1: 2 choices → Level 2: 1 choice

KEY DIFFERENCE:
  Subsets  = "Which items to pick?"     (binary decision tree, 2^n leaves)
  Perms   = "What ORDER to arrange?"    (branching decision tree, n! leaves)

================================================================================
YOUR TASK:
Implement `permute` using backtracking.

HINT: You need a way to track which elements have already been used.
Option A: Use a `used` map[int]bool to mark used elements.
Option B: Swap elements in-place (more advanced, try Option A first).

Create a helper closure: `var backtrack func(currentPerm []int)`
  - Base case: When len(currentPerm) == len(nums), you
    have a complete permutation — append a copy to results.
  - Recursive case: Loop through ALL elements in `nums`. For each one,
    if it hasn't been used yet:
      1. Mark it as used, append it to currentPerm
      2. Recurse
      3. BACKTRACK: unmark it, shrink currentPerm

GO-SPECIFIC NOTE:
  In Python you used `subset.pop()` to backtrack. In Go, you shrink
  a slice with `currentPerm = currentPerm[:len(currentPerm)-1]`.
  Also, when appending to results, you MUST copy the slice:
      cp := make([]int, len(currentPerm))
      copy(cp, currentPerm)
  Because Go slices share underlying arrays!
================================================================================

CALL TREE VISUALIZATION for nums = [1, 2, 3]
================================================================================
At each level, we pick one of the REMAINING (unused) numbers.
"used" tracks which numbers are already in our current permutation.

                                 backtrack([])
                              used = {}
                         /         |         \
                  pick 1/     pick 2|    pick 3\
                       /            |           \
             bt([1])            bt([2])          bt([3])
           used={1}           used={2}          used={3}
            /    \             /    \             /    \
       pick 2  pick 3    pick 1  pick 3    pick 1  pick 2
          /       \        /       \        /        \
    bt([1,2])  bt([1,3]) bt([2,1]) bt([2,3]) bt([3,1]) bt([3,2])
       |          |          |          |          |          |
    pick 3     pick 2     pick 3     pick 1     pick 2     pick 1
       |          |          |          |          |          |
  bt([1,2,3]) bt([1,3,2]) bt([2,1,3]) bt([2,3,1]) bt([3,1,2]) bt([3,2,1])
      |           |           |           |           |           |
  BASE CASE   BASE CASE   BASE CASE   BASE CASE   BASE CASE   BASE CASE
  len=3 ✓     len=3 ✓     len=3 ✓     len=3 ✓     len=3 ✓     len=3 ✓

Total permutations: 3! = 6  ✓
================================================================================
*/

func permute(nums []int) [][]int {
	// YOUR CODE HERE
	return nil
}

func main() {
	fmt.Println("--- Test Case 1 ---")
	fmt.Println("Input: [1, 2, 3]")
	result := permute([]int{1, 2, 3})
	fmt.Printf("Output: %v\n", result)
	fmt.Printf("Count: %d (Expected: 6)\n", len(result))
	// Sort for consistent comparison
	for _, r := range result {
		sort.Ints(r)
	}
	fmt.Println("Expected: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]")
	fmt.Println()

	fmt.Println("--- Test Case 2 ---")
	fmt.Println("Input: [0, 1]")
	result2 := permute([]int{0, 1})
	fmt.Printf("Output: %v\n", result2)
	fmt.Printf("Count: %d (Expected: 2)\n", len(result2))
	fmt.Println("Expected: [[0,1],[1,0]]")
	fmt.Println()

	fmt.Println("--- Test Case 3 ---")
	fmt.Println("Input: [1]")
	result3 := permute([]int{1})
	fmt.Printf("Output: %v\n", result3)
	fmt.Printf("Count: %d (Expected: 1)\n", len(result3))
	fmt.Println("Expected: [[1]]")
	fmt.Println()
}
