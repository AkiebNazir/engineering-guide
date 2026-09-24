package main

import "fmt"

/*
================================================================================
LeetCode 219 · Contains Duplicate II                                      [Easy]
https://leetcode.com/problems/contains-duplicate-ii/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
Given an integer array `nums` and an integer `k`, return `true` if there are
two DISTINCT indices `i` and `j` in the array such that

    nums[i] == nums[j]   and   abs(i - j) <= k

Otherwise return `false`.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,3,1], k = 3
    Output: true
    Explanation: nums[0] == nums[3] == 1 and abs(0 - 3) = 3 <= 3.

Example 2:
    Input:  nums = [1,0,1,1], k = 1
    Output: true
    Explanation: nums[2] == nums[3] == 1 and abs(2 - 3) = 1 <= 1.

Example 3:
    Input:  nums = [1,2,3,1,2,3], k = 2
    Output: false
    Explanation: The two 1s are 3 apart, the two 2s are 3 apart, and the two
                 3s are 3 apart. None of them is within k = 2.


CONSTRAINTS
-----------
    1 <= nums.length <= 10^5
    -10^9 <= nums[i] <= 10^9
    0 <= k <= 10^5              <- NOTE: k may be 0, and k may EXCEED the length


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Third fixed-size window in a row, third kind of aggregate:

    LC 643  aggregate = a running SUM
    LC 1456 aggregate = a running COUNT of a predicate
    LC 219  aggregate = a running SET of the values currently in the window

The requirement never changes: the aggregate must update in O(1) when an
element ENTERS and in O(1) when one LEAVES. A `set` does both — `add` and
`discard` are O(1) average — so it is a legal window aggregate.

THE REFRAME. "Two equal values at most k apart" means: as you walk to index r,
ask whether `nums[r]` already appears among the previous `k` elements. That is
exactly a membership query against a window:

    nums = [1, 2, 3, 1],  k = 3

      r=0  window before = {}          1 in {}? no    -> window {1}
      r=1  window before = {1}         2 in {1}? no   -> window {1,2}
      r=2  window before = {1,2}       3 ...? no      -> window {1,2,3}
      r=3  window before = {1,2,3}     1 in it? YES   -> return True


THE OFF-BY-ONE THAT DEFINES THIS PROBLEM
----------------------------------------
How many elements does the window hold?

    We need  abs(i - j) <= k  with  i != j.
    Fixing j = r, the legal partners are i in [r-k, r-1] — that is k indices.
    So the set holds the previous k elements, and INCLUDING r itself the
    window spans k+1 indices.

        k = 2, r = 5:   legal partners are indices 3 and 4
                        window of indices = {3, 4, 5}  -> size k+1 = 3
                        set BEFORE inserting r         -> size k   = 2

    Which means the element to evict when r arrives is index `r - k - 1`,
    NOT `r - k`. Get this wrong by one and you either miss valid pairs or
    report pairs that are k+1 apart. Derive it; do not guess.


WHAT TO THINK ABOUT
-------------------
1. What happens when k == 0? Work out what your code returns, and what it
   SHOULD return, before you run it. (Two distinct indices cannot be 0 apart.)

2. What happens when k >= len(nums)? The window never evicts anything, so the
   problem degenerates into a simpler one you already know. Which one?

3. A set cannot hold duplicates. Does that break the eviction — if the value
   being evicted still appears elsewhere in the window, you would be removing
   it wrongly. Think carefully about WHY this cannot actually happen here.
   (The answer is a one-liner, and it is the nicest observation in the
   problem.)

4. There is a completely different O(n) solution: remember the LAST INDEX at
   which each value was seen, in a dict. Write both. Which uses less memory,
   and under what condition?

5. `set.remove(x)` raises KeyError when x is absent; `set.discard(x)` does not.
   Which do you want, and does it matter given your loop bounds?


PROGRESSIVE HINTS
-----------------
Hint 1: Maintain `window`, a set of the values at indices [r-k, r-1].

Hint 2: At each r: if `nums[r] in window` -> return True. Then add nums[r].

Hint 3: Before (or after — decide which, and be consistent) adding, evict the
        element that has fallen out of range:
            if r >= k + 1:  window.discard(nums[r - k - 1])
        Equivalently: `if len(window) > k: window.discard(nums[r - k - 1])`.

Hint 4: The alternative: `last = {}` mapping value -> most recent index.
            if x in last and r - last[x] <= k: return True
            last[x] = r
        Note that overwriting `last[x]` unconditionally is correct — convince
        yourself why keeping only the MOST RECENT index never loses an answer.


COMPLEXITY TARGET
-----------------
    Time:  O(n)          — one pass, O(1) average set operations
    Space: O(min(n, k))  — the window holds at most k+1 values
                           (the last-seen-index map is O(n) instead)
================================================================================
*/

func main() {
	fmt.Println("Solution for Contains Duplicate II not implemented yet")
}
