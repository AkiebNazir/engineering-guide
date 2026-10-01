"""
================================================================================
LeetCode 881 · Boats to Save People                                     [Medium]
https://leetcode.com/problems/boats-to-save-people/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
You are given an array `people` where people[i] is the weight of the i-th
person, and an infinite number of boats where each boat can carry a maximum
weight of `limit`. Each boat carries AT MOST TWO people at the same time,
provided the sum of their weights is at most `limit`.

Return the minimum number of boats to carry every given person.


EXAMPLES
--------
Example 1:   people = [1, 2],       limit = 3  ->  1    (1, 2)
Example 2:   people = [3, 2, 2, 1], limit = 3  ->  3    (1, 2), (2), (3)
Example 3:   people = [3, 5, 3, 4], limit = 5  ->  4    (3), (3), (4), (5)


CONSTRAINTS
-----------
    1 <= people.length <= 5 * 10^4
    1 <= people[i] <= limit <= 3 * 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Every boat holds one or two people. So the number of boats is

    n - (number of pairs you manage to form)

and minimizing boats means MAXIMIZING the number of valid pairs.

Think about the heaviest person. They need a boat no matter what. If anyone
can share it with them, the lightest person can (lightest is the easiest
fit). If even the lightest doesn't fit, nobody does, and the heaviest person
goes alone.


WHAT TO THINK ABOUT
--------------------
1. Why does sorting help?

2. If the heaviest person CAN pair with the lightest, is it ever worse to do
   so than to pair them with someone heavier? (Exchange argument.)

3. Why is "pair the two lightest people" a bad greedy?


PROGRESSIVE HINTS
------------------
Hint 1: Sort. lo = 0 (lightest), hi = n - 1 (heaviest).

Hint 2: Each iteration launches one boat carrying people[hi]. If
        people[lo] + people[hi] <= limit, lo also gets on.

Hint 3: Loop while lo <= hi (when lo == hi, one person is left and takes a boat).


COMPLEXITY TARGET
------------------
    Time:  O(n log n) for the sort, O(n) for the scan
    Space: O(1) extra beyond the sort
================================================================================
"""

from typing import List


class Solution:
    def numRescueBoats(self, people: List[int], limit: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 011_boats_to_save_people_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ([1, 2], 3, 1),
        ([3, 2, 2, 1], 3, 3),
        ([3, 5, 3, 4], 5, 4),
        ([5], 5, 1),
        ([1, 1, 2, 2], 3, 2),
        ([2, 2, 2, 2], 4, 2),
        ([1, 5, 3, 5], 7, 3),
    ]
    all_ok = True
    for people, limit, want in cases:
        got = Solution().numRescueBoats(list(people), limit)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  people={people} limit={limit}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
