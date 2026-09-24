package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 398 · Random Pick Index                         [Medium]
https://leetcode.com/problems/random-pick-index/
================================================================================

PROBLEM
-------
Given an integer array `nums` with possible DUPLICATES, randomly output the
index of a given `target` number. You can assume the given target number
must exist in the array.

Implement the `Solution` class:
    Solution(nums)     Initializes the object with the array nums.
    pick(target)       Picks a random index i from nums where nums[i] == target.
                       If there are multiple valid i's, then each index
                       should have an EQUAL probability of returning.


EXAMPLES
--------
Example 1:
    Input:
        ["Solution", "pick", "pick", "pick"]
        [[[1, 2, 3, 3, 3]], [3], [1], [3]]
    Output:
        [null, 4, 0, 2]
    Explanation:
        Solution solution = new Solution([1, 2, 3, 3, 3]);
        solution.pick(3);  // returns 2, 3, or 4, each with probability 1/3
        solution.pick(1);  // returns 0, the only index where nums[i] == 1
        solution.pick(3);  // returns 2, 3, or 4, each with probability 1/3


CONSTRAINTS
-----------
    1 <= nums.length <= 2 * 10^4
    -2^31 <= nums[i] <= 2^31 - 1
    target is an integer from nums.
    At most 10^4 calls will be made to pick.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The obvious approach -- precompute a dict {value: [indices]} in __init__,
then pick() does random.choice(indices) -- is O(1) per pick after O(n)
preprocessing and is perfectly valid here (constraints are small). But this
problem exists in the curriculum to teach RESERVOIR SAMPLING: pick a single
uniformly random match in ONE pass over the array with O(1) extra space,
without ever storing the list of matching indices. That technique is what
generalizes to problem 003 (a linked list you can only scan once, with
unknown length) -- so implement pick() the reservoir-sampling way here,
not with a precomputed index dict, to build the technique before it becomes
the only way that will work at all.

PROGRESSIVE HINTS
------------------
Hint 1: Reservoir sampling for k=1: walk the array left to right,
        maintaining a running count of matches seen so far. When you see
        the m-th match (1-indexed), replace your current answer with this
        index with probability 1/m.
Hint 2: Why does this end up uniform over ALL matches, not biased toward
        later or earlier ones? Prove it for the last-seen match (kept with
        probability 1/count_total) and then by induction for every earlier
        match (kept, then never later evicted, with probability that
        telescopes to the same 1/count_total).
Hint 3: `random.randint(1, m) == 1` is a clean way to express "keep this
        one with probability 1/m".

COMPLEXITY TARGET
------------------
    Time:  O(n) per pick() call, O(1) extra space (excluding input)
    Space: O(1) additional state stored in __init__ (just the reference to nums)
================================================================================
*/

func main() {
	fmt.Println("Solution for Random Pick Index not implemented yet")
}
