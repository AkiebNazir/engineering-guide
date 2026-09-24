"""
================================================================================
LeetCode 26 · Remove Duplicates from Sorted Array                        [Easy]
https://leetcode.com/problems/remove-duplicates-from-sorted-array/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
Given an integer array `nums` sorted in NON-DECREASING order, remove the
duplicates IN PLACE such that each unique element appears only once. The
relative order of the elements should be kept the same. Then return the number
of unique elements in `nums`.

Consider the number of unique elements of `nums` to be `k`. To get accepted,
you need to do the following things:

    - Change the array `nums` such that the first `k` elements of `nums`
      contain the unique elements in the order they were present in `nums`
      initially.
    - The remaining elements of `nums` are NOT IMPORTANT, as well as the size
      of `nums`.
    - Return `k`.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,1,2]
    Output: 2, nums = [1,2,_]
    Explanation: Your function should return k = 2, with the first two elements
                 being 1 and 2. It does not matter what you leave beyond the
                 returned k.

Example 2:
    Input:  nums = [0,0,1,1,1,2,2,3,3,4]
    Output: 5, nums = [0,1,2,3,4,_,_,_,_,_]


CONSTRAINTS
-----------
    1 <= nums.length <= 3 * 10^4
    -100 <= nums[i] <= 100
    nums is sorted in NON-DECREASING order.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Two constraints do all the work here, and you should say both out loud before
writing code:

    1. THE ARRAY IS SORTED.  So duplicates are ADJACENT. You never need to
       remember everything you have seen — only the previous kept value. No
       set, no dict. O(1) space instead of O(n).

    2. IN PLACE, RETURN k.   You cannot resize the array. So "removing" means
       COMPACTING the survivors into the front and reporting how many there
       are. Whatever sits past index k-1 is garbage the caller ignores.

That second contract looks strange until you remember the problem is written
for C, where an array has a fixed size and you genuinely cannot shrink it. The
"return the length" convention is how C APIs have always done this.

    nums = [0,0,1,1,1,2,2,3,3,4]
            ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑ ↑
            keep the FIRST of each run, discard the rest

    result: [0,1,2,3,4, ?,?,?,?,?]   return 5
             └── the part that matters ──┘


THE PATTERN: a READ pointer and a WRITE pointer, both moving forward.

    r  scans every element
    w  marks the next slot to fill

    The invariant is `w <= r` at all times — you never write ahead of what you
    have already read. That is why overwriting the array you are iterating is
    safe and needs no temporary buffer.


WHAT TO THINK ABOUT
-------------------
1. Since duplicates are adjacent, what single value do you compare against to
   decide whether nums[r] is new? (Not "everything so far" — one value.)

2. Should you compare `nums[r]` to `nums[r-1]` (the previous READ) or to
   `nums[w-1]` (the last value you KEPT)? On this problem both work. Try to
   see why, and then think about which one still works if you had to allow
   at most TWO copies of each value.

3. Where should `w` start? If you initialise `w = 0`, the first element gets
   compared against `nums[-1]` — what does Python do with that?

4. What does the function return, and what does the caller check? What are you
   allowed to leave in `nums[k:]`?


PROGRESSIVE HINTS
-----------------
Hint 1: The first element is always unique — there is nothing before it. So
        start with `w = 1` and begin reading at `r = 1`.

Hint 2: For each `r`, if `nums[r] != nums[w - 1]`, it is a new value: write it
        at `nums[w]` and advance `w`. Otherwise skip it — `w` stays put.

Hint 3: Return `w`. It is both the count of unique values and the index just
        past the last one you wrote.


COMPLEXITY TARGET
-----------------
    Time:  O(n)  — one pass
    Space: O(1)  — two indices, no set
================================================================================
"""

from typing import List


class Solution:
    def removeDuplicates(self, nums: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 003_remove_duplicates_from_sorted_array_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 1, 2], 2, [1, 2]),
        ([0, 0, 1, 1, 1, 2, 2, 3, 3, 4], 5, [0, 1, 2, 3, 4]),
        ([1], 1, [1]),                          # single element
        ([1, 1, 1, 1], 1, [1]),                 # all identical
        ([1, 2, 3], 3, [1, 2, 3]),              # no duplicates
        ([-100, -100, 0, 100], 3, [-100, 0, 100]),   # negatives
        ([1, 2, 2], 2, [1, 2]),
        ([2, 2, 3], 2, [2, 3]),
    ]
    passed = 0
    for nums, want_k, want_prefix in cases:
        arr = list(nums)
        k = sol.removeDuplicates(arr)
        ok = k == want_k and arr[:want_k] == want_prefix
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {nums}\n"
              f"      k={k} (want {want_k})  prefix={arr[:k] if k else []} "
              f"(want {want_prefix})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
