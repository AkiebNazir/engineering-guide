package main

import "fmt"

/*
================================================================================
LeetCode 77 · Combinations                                               [Medium]
https://leetcode.com/problems/combinations/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given two integers `n` and `k`, return all possible combinations of `k` numbers
chosen from the range `[1, n]`.

You may return the answer in any order.

EXAMPLES
--------
Example 1:
    Input:  n = 4, k = 2
    Output: [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
    Explanation: There are 4 choose 2 = 6 combinations.

Example 2:
    Input:  n = 1, k = 1
    Output: [[1]]

CONSTRAINTS
-----------
    1 <= n <= 20
    1 <= k <= n

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This introduces the third base shape of backtracking: COMBINATIONS.
Unlike Subsets (where you decide in/out for each element sequentially) or 
Permutations (where order matters and you track `used` elements), 
Combinations focus on fixed-size sets where order does NOT matter.

To prevent generating duplicate combinations (e.g., [1, 2] and [2, 1]),
we impose a strict index-ordering constraint: the next element chosen
MUST be strictly greater than the last element chosen.

WHAT TO THINK ABOUT
--------------------
1. What does a partial `state` look like? A list of numbers chosen so far.
2. What is the `is_leaf` condition? When `len(path) == k`.
3. What are the `choices` at a given node? Any number from `[start, n]` 
   where `start` is `last_chosen + 1`. This strict increasing order is what
   prevents [2, 1] from being generated after [1, 2].
4. Can we PRUNE the search space? Yes! If we need `k - len(path)` more elements,
   but there aren't that many left in `[start, n]`, we can stop immediately.

PROGRESSIVE HINTS
------------------
Hint 1: Write the standard choose/explore/unchoose template.
Hint 2: Your backtracking function needs a `start` parameter. In the `for` loop,
        iterate from `start` to `n + 1`.
Hint 3: In the recursive call, pass `choice + 1` as the new `start`.
Hint 4: For optimization, if `len(path) + (n - i + 1) < k`, you don't have enough
        numbers left to form a combination of size `k`. Prune it!

COMPLEXITY TARGET
------------------
    Time:  O(k * C(n, k))  — C(n, k) leaves, copying `k` elements at each leaf.
    Space: O(k)            — depth of the recursion tree and space for `path`.
================================================================================
*/

func main() {
	fmt.Println("Solution for Combinations not implemented yet")
}
