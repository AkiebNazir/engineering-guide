package main

import "fmt"

/*
================================================================================
PROBLEM 4: Subsets (The Include/Exclude Pattern)
================================================================================

Given an integer array `nums` of unique elements, return all possible subsets
(the power set). The solution must not contain duplicate subsets.

Example 1:
Input: nums = [1,2,3]
Output: [[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]

Example 2:
Input: nums = [0]
Output: [[],[0]]

Constraints:
1 <= nums.length <= 10
All elements of nums are unique.

================================================================================
YOUR TASK:
This is your first Backtracking problem!
Think about the "Include/Exclude" decision tree. At every number in the array,
you have exactly two choices:
1. INCLUDE the number in your current subset.
2. EXCLUDE the number from your current subset.

HINT: In Go, passing slices around in recursion can be tricky.
Append creates a new slice if capacity is exceeded, otherwise it modifies the underlying array.
Always make a copy of your subset before adding it to the final result!
================================================================================
CALL TREE VISUALIZATION for nums = [1, 2]
================================================================================
At each index 'i', we make a choice: INCLUDE nums[i] or EXCLUDE nums[i].
The variable 'i' tells us how deep we are in the tree.

                            backtrack(0, [])
                              /          \
                  INCLUDE 1 /              \ EXCLUDE 1
                           /                \
              backtrack(1, [1])            backtrack(1, [])
                /           \                /           \
      INCLUDE 2/      EXCLUDE\ 2   INCLUDE 2/      EXCLUDE\ 2
              /               \            /               \
backtrack(2, [1, 2]) backtrack(2, [1]) backtrack(2, [2]) backtrack(2, [])
        |                    |                 |                 |
   BASE CASE (i=2)      BASE CASE (i=2)   BASE CASE (i=2)   BASE CASE (i=2)
   Append [1,2]         Append [1]        Append [2]        Append []


HOW "POPPING" WORKS IN GO:
Notice how we got from `[1, 2]` back to `[1]`?
After the far-left branch finishes, it returns back up to `backtrack(1, [1])`.
At this point, `subset` is `[1, 2]`.
To "pop" in Go, we do `subset = subset[:len(subset)-1]`, changing it back to `[1]`.
Then we dive down the EXCLUDE branch!
This is why it's called "Backtracking" - we undo our choice before going down the other path!
================================================================================
*/

func subsets(nums []int) [][]int {
	// TODO: Your recursive backtracking code here]
	res := make([][]int, 0)
	var backtrack func(int, []int)
	backtrack = func(n int, subset []int) {
		if n == len(nums) {
			temp := make([]int, len(subset))
			// 2. Copy the numbers from the current subset into the new temp slice
			copy(temp, subset)
			// 3. Append the fresh copy to your results!
			res = append(res, temp)
			return
		}
		subset = append(subset, nums[n])
		backtrack(n+1, subset)
		subset = subset[:len(subset)-1]
		backtrack(n+1, subset)

	}
	backtrack(0, []int{})
	return res
}

func main() {
	fmt.Println("--- Test Case 1 ---")
	fmt.Println("Input: [1, 2, 3]")
	fmt.Printf("Output: %v\n", subsets([]int{1, 2, 3}))
	fmt.Println("Expected: [[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]] (Order doesn't matter)\n")

	fmt.Println("--- Test Case 2 ---")
	fmt.Println("Input: [0]")
	fmt.Printf("Output: %v\n", subsets([]int{0}))
	fmt.Println("Expected: [[], [0]]\n")

}
