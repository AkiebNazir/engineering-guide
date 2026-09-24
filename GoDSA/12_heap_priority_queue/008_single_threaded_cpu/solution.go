package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 1834 · Single-Threaded CPU                        [Medium]
https://leetcode.com/problems/single-threaded-cpu/
================================================================================

You are given `tasks`, a 2D integer array where tasks[i] = [enqueueTime_i,
processingTime_i] means the i-th task will be available to process at
`enqueueTime_i` and needs `processingTime_i` to finish.

You have a single-threaded CPU that:
    - Can process at most one task at a time.
    - If idle and no task is available, it stays idle until one becomes
      available.
    - If idle and multiple tasks are available, it picks the task with the
      SHORTEST processing time. Ties broken by the SMALLEST original index.
    - Once started, a task runs to completion without preemption.

Return the order in which the CPU processes the tasks, given as an array of
the original indices.

Example 1:
    Input:  tasks = [[1,2],[2,4],[3,2],[4,1]]
    Output: [0,2,3,1]
    Explanation:
        t=1: task 0 available, only option -> start task 0 (runs 1..3)
        t=2: task 1 available, but CPU busy until t=3
        t=3: tasks 1,2 available; task 2 has shorter time -> start task 2 (3..5)
        t=4: task 3 available, but CPU busy until t=5
        t=5: tasks 1,3 available; task 3 shorter -> start task 3 (5..6)
        t=6: only task 1 left -> start task 1 (6..10)

Example 2:
    Input:  tasks = [[7,10],[7,12],[7,5],[7,4],[7,2]]
    Output: [4,3,2,0,1]

Constraints:
    tasks.length == n
    1 <= n <= 10^5
    1 <= enqueueTime_i, processingTime_i <= 10^9
*/

func main() {
	fmt.Println("Solution for Single-Threaded CPU not implemented yet")
}
