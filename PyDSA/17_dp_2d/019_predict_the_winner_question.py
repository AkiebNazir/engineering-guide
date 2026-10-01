"""
================================================================================
LeetCode 486 · Predict the Winner                                       [Medium]
https://leetcode.com/problems/predict-the-winner/
Topic: 17 · Dynamic Programming (2D)
================================================================================

PROBLEM
-------
You are given an integer array nums. Two players, player 1 and player 2, play a
game with it. Player 1 moves first. On each turn, the current player takes the
number at EITHER end of the array (nums[0] or nums[-1]), removes it, and adds it
to their score. The game ends when the array is empty.

Return true if player 1 can win the game. If the scores are equal, player 1 is
still the winner. Assume both players play optimally.


EXAMPLES
--------
Example 1:   nums = [1, 5, 2]         ->  false
    Player 1 takes 1 or 2. Either way player 2 takes 5 and wins 5 vs 3.

Example 2:   nums = [1, 5, 233, 7]    ->  true
    Player 1 takes 1. Whatever player 2 takes (5 or 7), player 1 takes 233.


CONSTRAINTS
-----------
    1 <= nums.length <= 20
    0 <= nums[i] <= 10^7


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is a two-player, zero-sum, perfect-information game: the family of
problems solved with MINIMAX. "Optimally" means each player assumes the other
will also play their best.

The state of the game is just the remaining window nums[i..j]; whose turn it
is follows from how many numbers have been taken. The trick that turns this
into clean interval DP is to stop tracking two scores and track ONE number:

    diff(i, j) = (my total) - (opponent's total) from nums[i..j],
                 when it is MY turn and both of us play optimally

Whoever moves takes an end, and then the OTHER player faces the rest with
the same definition — so their diff counts against me.


WHAT TO THINK ABOUT
--------------------
1. Why does "always take the larger end" fail? Try Example 2.

2. If it's my turn on nums[i..j] and I take nums[i], what is my best
   difference, in terms of a smaller subproblem?

3. There are only O(n^2) windows. How many times does plain recursion
   revisit each one?

4. (Follow-up) When the length is even, player 1 can never lose. Why?


PROGRESSIVE HINTS
------------------
Hint 1: diff(i, j) = max(nums[i] - diff(i+1, j), nums[j] - diff(i, j-1)).

Hint 2: Base case: diff(i, i) = nums[i]. Player 1 wins iff diff(0, n-1) >= 0.

Hint 3: Bottom-up, fill by increasing window length, or i from n-1 down to 0
        with j from i+1 up — then one row of length n is enough.


COMPLEXITY TARGET
------------------
    Time:  O(n^2)
    Space: O(n^2), or O(n) with a rolling row
================================================================================
"""
from typing import List


class Solution:
    def predictTheWinner(self, nums: List[int]) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 019_predict_the_winner_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ([1, 5, 2], False),
        ([1, 5, 233, 7], True),
        ([7], True),
        ([1, 1], True),
        ([0, 0, 7, 6, 5, 6, 1], False),
        ([2, 4, 55, 6, 8], False),
        ([3, 9, 1, 2], True),
    ]
    all_ok = True
    for nums, want in cases:
        got = Solution().predictTheWinner(list(nums))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
