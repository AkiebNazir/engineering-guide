"""
================================================================================
LeetCode 904 · Fruit Into Baskets                                       [Medium]
https://leetcode.com/problems/fruit-into-baskets/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
You are visiting a farm that has a single row of fruit trees arranged from left
to right. The trees are represented by an integer array `fruits` where
`fruits[i]` is the TYPE of fruit the i-th tree produces.

You want to collect as much fruit as possible. However, the owner has some
strict rules that you must follow:

    * You only have TWO BASKETS, and each basket can only hold a SINGLE TYPE
      of fruit. There is no limit on the amount of fruit each basket can hold.
    * Starting from any tree of your choice, you must pick EXACTLY ONE FRUIT
      from every tree (including the start tree) while moving to the right.
      The picked fruits must fit in one of your baskets.
    * Once you reach a tree with fruit that cannot fit in your baskets, you
      must stop.

Given the integer array `fruits`, return the MAXIMUM NUMBER OF FRUITS you can
pick.


EXAMPLES
--------
Example 1:
    Input:  fruits = [1,2,1]
    Output: 3
    Explanation: We can pick from all 3 trees.

Example 2:
    Input:  fruits = [0,1,2,2]
    Output: 3
    Explanation: We can pick from trees [1,2,2].
                 If we had started at the first tree, we would only pick from
                 trees [0,1].

Example 3:
    Input:  fruits = [1,2,3,2,2]
    Output: 4
    Explanation: We can pick from trees [2,3,2,2].
                 If we had started at the first tree, we would only pick from
                 trees [1,2].


CONSTRAINTS
-----------
    1 <= fruits.length <= 10^5
    0 <= fruits[i] < fruits.length


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The story is elaborate; the problem is one line. Strip it:

    * "pick from every tree while moving right, stop when you cannot"
        -> the fruits you collect are a CONTIGUOUS SUBARRAY.
    * "two baskets, each holding a single type"
        -> that subarray contains AT MOST 2 DISTINCT VALUES.
    * "maximum number of fruits"
        -> maximise its LENGTH.

    FIND THE LONGEST SUBARRAY WITH AT MOST 2 DISTINCT VALUES.

That is LC 340 ("at most K distinct") with K = 2, and it is the Shape-B
template again, with a new aggregate: a frequency map whose SIZE is the number
of distinct values in the window.

    fruits = [1,2,3,2,2]

    [1]              {1:1}              1 distinct   ok    len 1
    [1 2]            {1:1, 2:1}         2 distinct   ok    len 2
    [1 2 3]          {1:1, 2:1, 3:1}    3 distinct   BROKEN -> shrink
     [2 3]           {2:1, 3:1}         2 distinct   ok    len 2
     [2 3 2]         {2:2, 3:1}         2 distinct   ok    len 3
     [2 3 2 2]       {2:3, 3:1}         2 distinct   ok    len 4   <- answer


⚠️  THE PYTHON TRAP THAT DEFINES THIS PROBLEM
---------------------------------------------
Your validity test is `len(count) > 2`. That is only meaningful if the map
contains exactly the values currently in the window. When you shrink:

    count[fruits[l]] -= 1

the key does NOT disappear when its value hits zero. It stays, with value 0,
and `len(count)` keeps counting it. A map that has seen types {1,2,3} reports
`len == 3` forever, even after 3 has left the window.

Work out what that does to the loop before you look it up. (Two things happen,
and the second one is worse than a wrong answer.)

The fix is one line, and you must not forget it:

    count[fruits[l]] -= 1
    if count[fruits[l]] == 0:
        del count[fruits[l]]          # <- keeps len() == distinct-in-window
    l += 1


WHAT TO THINK ABOUT
-------------------
1. What exactly is your aggregate, and what does `len()` of it mean? Can you
   state the invariant it must satisfy?

2. Trace what happens on [3,0,2,3,3,2,3] if you never delete zero-valued keys.
   Does the loop terminate? What does `l` do?

3. `Counter` or `defaultdict(int)`? There is a real difference in this exact
   situation, and it is not about speed. (Hint: what does READING a missing key
   do to each of them?)

4. The general version takes K as a parameter. Write it that way — K=2 is a
   special case, not a special algorithm.

5. There is an O(1)-space solution that tracks only the two current types and
   the length of the trailing run. Can you find it? Is it worth the complexity?

6. Constraint check: `0 <= fruits[i] < fruits.length`. Does that let you use a
   list instead of a dict?


PROGRESSIVE HINTS
-----------------
Hint 1: Longest window with at most 2 distinct values. Forget the baskets.

Hint 2: Maintain `count = Counter()` over the window. Validity is
        `len(count) <= 2`.

Hint 3: The template:
            l = best = 0
            count = Counter()
            for r, f in enumerate(fruits):
                count[f] += 1                       # ENTER
                while len(count) > 2:               # RESTORE
                    count[fruits[l]] -= 1
                    if count[fruits[l]] == 0:
                        del count[fruits[l]]
                    l += 1
                best = max(best, r - l + 1)         # RECORD

Hint 4: Without the `del`, `len(count)` never shrinks, so the `while` loop
        cannot exit — `l` runs off the end of the array and you get an
        IndexError, not merely a wrong answer.


COMPLEXITY TARGET
-----------------
    Time:  O(n)   — each index enters and leaves the window once
    Space: O(1)   — the map holds at most 3 keys at any moment
================================================================================
"""

from typing import List


class Solution:
    def totalFruit(self, fruits: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 009_fruit_into_baskets_question.py
# ==============================================================================
def _brute(fruits, k=2):
    """O(n^2) reference: extend from every start until a 3rd type appears."""
    best = 0
    for i in range(len(fruits)):
        seen = set()
        for j in range(i, len(fruits)):
            seen.add(fruits[j])
            if len(seen) > k:
                break
            best = max(best, j - i + 1)
    return best


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 2, 1], 3),
        ([0, 1, 2, 2], 3),
        ([1, 2, 3, 2, 2], 4),
        ([3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 4], 5),
        ([1], 1),                        # single tree
        ([1, 1, 1, 1], 4),               # one type only
        ([1, 2], 2),                     # exactly two types
        ([1, 2, 3], 2),                  # three types, all distinct
        ([0, 1, 2, 3, 4, 5], 2),         # every tree a new type
        ([1, 2, 1, 2, 1, 2], 6),         # two types alternating -> everything
        ([3, 0, 2, 3, 3, 2, 3], 5),      # THE no-`del` detector
        ([1, 1, 2, 2, 3, 3], 4),
        ([1, 2, 2, 2, 3], 4),            # best window at the FRONT-middle
        ([3, 1, 2, 2, 2], 4),            # best window at the END
        ([0, 0, 0, 0], 4),               # type 0 is a legal type, not a sentinel
    ]

    passed = 0
    for fruits, expected in cases:
        assert _brute(fruits) == expected, (
            f"bad test expectation for {fruits}: "
            f"oracle says {_brute(fruits)}, test says {expected}")
        got = sol.totalFruit(list(fruits))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(fruits):<38} -> {got}  "
              f"(want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
