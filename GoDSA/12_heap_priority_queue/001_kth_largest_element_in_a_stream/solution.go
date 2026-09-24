package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 703 · Kth Largest Element in a Stream               [Easy]
https://leetcode.com/problems/kth-largest-element-in-a-stream/
================================================================================

Design a class to find the kth largest element in a stream. Note that it is
the kth largest element in the sorted order, not the kth distinct element.

Implement `KthLargest`:

- `KthLargest(k, nums)` — initializes the object with the integer k and the
  initial stream of integers `nums`.
- `add(val)` — appends `val` to the stream and returns the element
  representing the kth largest element in the stream.

--------------------------------------------------------------------------------
EXAMPLES
--------------------------------------------------------------------------------
Input:
["KthLargest", "add", "add", "add", "add", "add"]
[[3, [4, 5, 8, 2]], [3], [5], [10], [9], [4]]

Output:
[null, 4, 5, 5, 8, 8]

Explanation:
KthLargest kthLargest = new KthLargest(3, [4, 5, 8, 2]);
kthLargest.add(3);   // return 4
kthLargest.add(5);   // return 5
kthLargest.add(10);  // return 5
kthLargest.add(9);   // return 8
kthLargest.add(4);   // return 8

--------------------------------------------------------------------------------
CONSTRAINTS
--------------------------------------------------------------------------------
- 1 <= k <= 10^4
- 0 <= nums.length <= 10^4
- -10^4 <= nums[i] <= 10^4
- -10^4 <= val <= 10^4
- At most 10^4 calls will be made to add.
- It is guaranteed that there will be at least k elements in the array when
  you search for the kth element.
*/

func main() {
	fmt.Println("Solution for Kth Largest Element in a Stream not implemented yet")
}
