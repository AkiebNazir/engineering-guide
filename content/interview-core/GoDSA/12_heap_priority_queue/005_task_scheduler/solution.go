package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 621 · Task Scheduler                              [Medium]
https://leetcode.com/problems/task-scheduler/
================================================================================

You are given an array of CPU `tasks`, each labeled with a letter 'A' to 'Z',
and a non-negative integer `n` that represents the cooldown period between two
SAME tasks (the same letter must be at least n units apart).

Each unit of time, the CPU could:
  - complete one task, or
  - stay idle.

Return the LEAST number of units of time the CPU will take to finish all the
given tasks.

Example 1:
    Input:  tasks = ["A","A","A","B","B","B"], n = 2
    Output: 8
    Explanation: A -> B -> idle -> A -> B -> idle -> A -> B
                 There is at least a gap of 2 units between any two same tasks.

Example 2:
    Input:  tasks = ["A","A","A","B","B","B"], n = 0
    Output: 6
    Explanation: On this case any permutation works since n = 0.

Example 3:
    Input:  tasks = ["A","A","A","A","A","A","B","C","D","E","F","G"], n = 2
    Output: 16
    Explanation: One possible solution is
      A -> B -> C -> A -> D -> E -> A -> F -> G -> A -> idle -> idle -> A ->
      idle -> idle -> A

Constraints:
    1 <= tasks.length <= 10^4
    tasks[i] is an uppercase English letter.
    0 <= n <= 100
*/

func main() {
	fmt.Println("Solution for Task Scheduler not implemented yet")
}
