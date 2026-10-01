"""
================================================================================
LeetCode 27 · Remove Element                                             [Easy]
https://leetcode.com/problems/remove-element/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
Given an integer array `nums` and an integer `val`, remove all occurrences of
`val` in `nums` IN PLACE. The ORDER OF THE ELEMENTS MAY BE CHANGED. Then return
the number of elements in `nums` which are not equal to `val`.

Consider the number of elements in `nums` which are not equal to `val` to be
`k`. To get accepted, you need to do the following things:

    - Change the array `nums` such that the first `k` elements of `nums`
      contain the elements which are not equal to `val`.
    - The remaining elements of `nums` are not important, as well as the size
      of `nums`.
    - Return `k`.


EXAMPLES
--------
Example 1:
    Input:  nums = [3,2,2,3], val = 3
    Output: 2, nums = [2,2,_,_]

Example 2:
    Input:  nums = [0,1,2,2,3,0,4,2], val = 2
    Output: 5, nums = [0,1,4,0,3,_,_,_]
    Explanation: Note that the five elements can be returned in ANY order.


CONSTRAINTS
-----------
    0 <= nums.length <= 100
    0 <= nums[i] <= 50
    0 <= val <= 100


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is LC 26 with a different predicate. Same skeleton:

    w = 0
    for r in range(len(nums)):
        if KEEP(nums[r]):
            nums[w] = nums[r]
            w += 1
    return w

For LC 26, KEEP was "differs from the last kept value". Here it is simply
`nums[r] != val`. That is the entire difference, and recognising that the
skeleton is shared is worth more than either individual solution.

    nums = [0,1,2,2,3,0,4,2]   val = 2

    keep everything that is not a 2, compacted to the front:
    [0,1,3,0,4, ?,?,?]   return 5

BUT there is one new sentence in the statement, and it changes what the OPTIMAL
answer looks like:

    "The order of the elements MAY BE CHANGED."

LC 26 required preserved order. This one does not. That freedom buys you a
second, better algorithm — one that does FEWER WRITES when the value being
removed is rare. Finding it is the actual point of this problem.


WHAT TO THINK ABOUT
-------------------
1. Write the order-preserving version first. How many writes does it perform on
   an array with NO occurrences of `val` at all? Are those writes doing
   anything useful?

2. Since order does not matter, you do not have to SHIFT survivors leftward.
   What if, instead, you took an element from the END of the array and dropped
   it into the hole left by a removed element?

3. With that idea: how many writes happen per removal? What is the total number
   of writes across the whole array, in terms of the number of occurrences of
   `val` rather than the length of the array?

4. Careful with the swap-from-the-end idea: after you pull an element in from
   the back, can you advance your left pointer immediately? What if the element
   you just pulled in is ALSO equal to `val`?

5. What is the answer when the array is empty? When every element equals `val`?


PROGRESSIVE HINTS
-----------------
Hint 1: Order-preserving — a write pointer `w` starting at 0. For each element,
        if it is not `val`, write it at `nums[w]` and advance `w`. Return `w`.

Hint 2: Order-agnostic — keep `l = 0` and `n = len(nums)`. While `l < n`: if
        `nums[l] == val`, overwrite it with `nums[n-1]` and shrink `n` by one
        (do NOT advance `l`); otherwise advance `l`. Return `n`.

Hint 3: The reason you must not advance `l` after pulling from the back: the
        value you just moved in has never been examined. It might be `val`
        itself. Re-test the same index.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(1)
    Bonus: minimise the number of WRITES, not just the asymptotic time.
================================================================================
"""

from typing import List


class Solution:
    def removeElement(self, nums: List[int], val: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 004_remove_element_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([3, 2, 2, 3], 3, [2, 2]),
        ([0, 1, 2, 2, 3, 0, 4, 2], 2, [0, 0, 1, 3, 4]),
        ([], 0, []),                          # empty array
        ([1], 1, []),                         # remove the only element
        ([1], 2, [1]),                        # nothing to remove
        ([2, 2, 2], 2, []),                   # remove everything
        ([4, 5], 5, [4]),
        ([5, 4], 5, [4]),                     # target at the FRONT
        ([1, 2, 3, 4, 5], 9, [1, 2, 3, 4, 5]),  # absent value
        ([2, 1, 2, 1, 2], 2, [1, 1]),
        ([2, 1, 2, 2, 2], 2, [1]),            # RUN of val at the END
        ([1, 2, 2, 2, 2], 2, [1]),            # ... and with val absent up front
    ]
    passed = 0
    for nums, val, want_sorted in cases:
        arr = list(nums)
        k = sol.removeElement(arr, val)
        # Order may be anything, so compare as multisets.
        ok = k == len(want_sorted) and sorted(arr[:k]) == want_sorted
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} val={val} -> k={k}, "
              f"prefix={sorted(arr[:k]) if k else []} (want {want_sorted})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
