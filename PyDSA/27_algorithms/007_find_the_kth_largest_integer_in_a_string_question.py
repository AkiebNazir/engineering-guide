"""
================================================================================
QUESTION · LeetCode 1985 · Find the Kth Largest Integer in a String   [Medium]
https://leetcode.com/problems/find-the-kth-largest-integer-in-a-string/
================================================================================

PROBLEM
-------
You are given an array of strings `nums` and an integer `k`. Each string in
`nums` represents an integer WITHOUT leading zeros (except the string "0"
itself). Return the string that represents the `k`-th largest integer in
`nums`.

NOTE: Duplicate numbers should be counted distinctly. For example, if `nums`
is `["1", "2", "2"]`, `"2"` is the first largest integer, `"2"` is the second
largest integer, and `"1"` is the third largest integer.


EXAMPLES
--------
Example 1:
    Input:  nums = ["3","6","7","10"], k = 4
    Output: "3"
    Explanation: The numbers in nums sorted in descending order are
    ["10","7","6","3"]. The 4th largest integer is "3".

Example 2:
    Input:  nums = ["2","21","12","1"], k = 3
    Output: "2"
    Explanation: The numbers in nums sorted in descending order are
    ["21","12","2","1"]. The 3rd largest integer is "2".


CONSTRAINTS
-----------
    1 <= k <= nums.length <= 10^4
    1 <= nums[i].length <= 100
    nums[i] consists of only digits.
    nums[i] will not have any leading zeros.

FOLLOW-UP: Can you answer without sorting the entire array?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The trap is right there in the name: these are STRINGS, and Python's default
string comparison is lexicographic (character by character), which does NOT
match numeric order once lengths differ -- `"9" < "10"` numerically, but
`"9" > "10"` lexicographically because `'9' > '1'` at the very first
character. Every comparison you write here (whether inside a sort key, a
heap, or a Quickselect partition) MUST first compare by LENGTH, and only
fall back to lexicographic order when lengths are equal (equal-length numeric
strings DO compare correctly as plain strings, since digit-by-digit is the
same as place-by-place). Get the comparator right and the rest is just "find
the k-th largest" -- a Quickselect (or a heap of size k) applied with that
comparator instead of `<`.

PROGRESSIVE HINTS
------------------
Hint 1: Converting every string to `int` and sorting numerically always
        works and sidesteps the trap entirely -- but costs an O(n) conversion
        pass plus O(n log n) sort. State it as the baseline.
Hint 2: You don't need ALL of them sorted -- only the k-th largest. That's
        exactly the shape Quickselect (or a size-k heap) solves in better
        than O(n log n).
Hint 3: Define your own "greater than" for two numeric strings a, b: if
        `len(a) != len(b)`, the longer one is numerically larger; if lengths
        are equal, plain string comparison already agrees with numeric order.
Hint 4: Plug that comparator into Quickselect's partition step (or into a
        heap's ordering) instead of relying on `<`/`>` doing the right thing
        on strings by default.

COMPLEXITY TARGET
------------------
    Time:  O(n) expected (Quickselect with a custom comparator)
    Space: O(n) (Quickselect on a copy) or O(1) extra beyond a working copy
================================================================================
"""


class Solution:
    def kthLargestNumber(self, nums: list[str], k: int) -> str:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        (["3", "6", "7", "10"], 4, "3"),
        (["2", "21", "12", "1"], 3, "2"),
        (["1", "1", "1"], 2, "1"),
        (["0"], 1, "0"),
        (["9", "10"], 1, "10"),
        (["9", "10"], 2, "9"),
    ]
    for nums, k, expected in cases:
        result = sol.kthLargestNumber(list(nums), k)
        ok = result == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  kthLargestNumber({nums}, {k}) "
              f"-> {result!r} (expected {expected!r})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
