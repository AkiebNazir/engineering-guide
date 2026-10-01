"""
================================================================================
SOLUTION · LeetCode 486 · Predict the Winner                            [Medium]
https://leetcode.com/problems/predict-the-winner/
================================================================================

THE CORE IDEA
--------------
Track ONE number per window instead of two scores:

    diff(i, j) = (mover's total) - (other player's total) on nums[i..j],
                 both playing optimally

The mover takes an end; then the other player becomes "the mover" on the rest,
and their advantage counts against us:

    diff(i, j) = max(nums[i] - diff(i+1, j),  nums[j] - diff(i, j-1))
    diff(i, i) = nums[i]

Player 1 wins (ties count) iff diff(0, n-1) >= 0. This is minimax written as
interval DP: max for "me", and the minus sign is the opponent's min.


================================================================================
APPROACH 1 · Plain minimax recursion (priced, used as oracle)
================================================================================
Try both ends at every turn, recursively, with no memory.

    Time: O(2^n)    Space: O(n) recursion depth

n <= 20 means up to ~10^6 leaves, which is survivable in C and painful in
Python. The demo counts the calls: they double with each extra number.


================================================================================
APPROACH 2 · Memoized diff(i, j)
================================================================================
    @cache
    def diff(i, j):
        if i == j:
            return nums[i]
        return max(nums[i] - diff(i + 1, j), nums[j] - diff(i, j - 1))
    return diff(0, n - 1) >= 0

Only n(n+1)/2 distinct windows exist, so each is solved once.

    Time: O(n^2)    Space: O(n^2)


================================================================================
APPROACH 3 · Bottom-up with one row ✅ (the answer)
================================================================================
diff(i, j) needs diff(i+1, j) (row below) and diff(i, j-1) (same row, left).
Loop i from n-1 down to 0 and j from i+1 up; one array holds "the row below"
until it is overwritten left to right:

    dp = nums[:]                         # dp[j] = diff(j, j) initially
    for i in range(n - 2, -1, -1):
        for j in range(i + 1, n):
            dp[j] = max(nums[i] - dp[j],       # dp[j] is still diff(i+1, j)
                        nums[j] - dp[j - 1])   # dp[j-1] is already diff(i, j-1)
    return dp[n - 1] >= 0

    Time: O(n^2)    Space: O(n)


================================================================================
APPROACH 4 · Even length: player 1 always wins (follow-up insight)
================================================================================
Colour the positions odd and even. With an even count, player 1 can take ALL
even-indexed numbers or ALL odd-indexed ones: after player 1 takes one colour
from an end, both ends show the other colour to player 2, and whatever player 2
takes re-exposes player 1's colour. So player 1 picks the larger colour sum and
cannot lose. (It doesn't say HOW MUCH player 1 wins by — DP still needed for
that.) The demo checks the claim on 2,000 random even-length arrays.


================================================================================
STEP BY STEP TRACE · nums = [1, 5, 233, 7]
================================================================================
    diff for windows of length 1:   [1] [5] [233] [7]  -> 1, 5, 233, 7

    length 2:
      [1,5]    max(1 - 5,   5 - 1)   =   4
      [5,233]  max(5 - 233, 233 - 5) = 228
      [233,7]  max(233 - 7, 7 - 233) = 226

    length 3:
      [1,5,233]  max(1 - 228, 233 - 4)     = 229
      [5,233,7]  max(5 - 226, 7 - 228)     = -221

    length 4:
      [1,5,233,7]  max(1 - (-221), 7 - 229) = 222   >= 0 -> true

    Taking 1 leaves player 2 the window [5,233,7], where the mover is 221
    behind — which is player 1's gain.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time     Space    Mutates input?
    ------------------------  -------  -------  --------------
    Plain minimax             O(2^n)   O(n)     No
    Memoized diff(i, j)       O(n^2)   O(n^2)   No
    Bottom-up, one row ✅     O(n^2)   O(n)     No
    Even-length shortcut      O(1)     O(1)     No (answers only even n)


================================================================================
EDGE CASES
================================================================================
    One number            Player 1 takes it: true (even if it is 0).
    Two numbers           Player 1 takes the larger: always true.
    All zeros             Tie: true — ties go to player 1.
    Equal ends            Both choices can matter differently deeper in.


================================================================================
COMMON MISTAKES
================================================================================
1. Greedy "take the larger end". [1, 5, 233, 7]: greedy takes 7, player 2
   takes 233, player 1 loses — but taking 1 first wins. Demo.

2. Maximising player 1's score at EVERY level (forgetting that player 2
   minimises it). [1, 5, 2] then looks winnable. Demo.

3. Treating a tie as a loss (diff > 0 instead of >= 0). [1, 1] -> false. Demo.

4. In the one-row version, looping j DOWNWARD: dp[j-1] still holds the row
   below, not diff(i, j-1). Demo.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return player 1's actual score, or the margin?
A: The margin is diff(0, n-1). Scores: (total + margin) / 2 and (total - margin) / 2.

Q: Stone Game (LC 877): even length, odd total, no ties. Answer?
A: Always true, by the parity argument (Approach 4).

Q: Players may take 1, 2 or 3 numbers from the FRONT only (Stone Game III)?
A: Same "mover's advantage" trick on suffixes: diff(i) = max over k of
   sum(nums[i:i+k]) - diff(i+k). 1D DP.

Q: How would you show the optimal move at each turn?
A: Store which branch achieved the max in diff(i, j) and replay from (0, n-1).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 877   Stone Game                 — parity makes it trivially true
    LC 1140  Stone Game II              — minimax with a growing move limit
    LC 1406  Stone Game III             — the same trick on suffixes
    LC 312   Burst Balloons (013)       — interval DP
    LC 516   Longest Palindromic Subsequence (015) — interval DP fill order
================================================================================
"""

import random
import time
from functools import cache
from typing import List


class Solution:
    def predictTheWinner(self, nums: List[int]) -> bool:
        n = len(nums)
        dp = nums[:]                                    # dp[j] = diff(j, j)
        for i in range(n - 2, -1, -1):
            left = nums[i]
            for j in range(i + 1, n):
                take_left = left - dp[j]                # dp[j] is diff(i+1, j)
                take_right = nums[j] - dp[j - 1]        # dp[j-1] is diff(i, j-1)
                dp[j] = take_left if take_left > take_right else take_right
        return dp[n - 1] >= 0


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
CALLS = 0


def minimax_brute(nums: List[int]) -> bool:
    """Approach 1: scores for both players, no memo. Counts its calls."""
    global CALLS

    def play(i: int, j: int, p1_turn: bool) -> int:        # returns p1 - p2
        global CALLS
        CALLS += 1
        if i > j:
            return 0
        if p1_turn:
            return max(nums[i] + play(i + 1, j, False), nums[j] + play(i, j - 1, False))
        return min(-nums[i] + play(i + 1, j, True), -nums[j] + play(i, j - 1, True))

    return play(0, len(nums) - 1, True) >= 0


def winner_memo(nums: List[int]) -> bool:
    @cache
    def diff(i: int, j: int) -> int:
        if i == j:
            return nums[i]
        return max(nums[i] - diff(i + 1, j), nums[j] - diff(i, j - 1))
    return diff(0, len(nums) - 1) >= 0


def margin(nums: List[int]) -> int:
    n = len(nums)
    dp = nums[:]
    for i in range(n - 2, -1, -1):
        for j in range(i + 1, n):
            dp[j] = max(nums[i] - dp[j], nums[j] - dp[j - 1])
    return dp[n - 1]


def greedy_larger_end(nums: List[int]) -> bool:
    """Mistake 1: both players grab the larger end."""
    a, i, j, p1_turn, p1, p2 = nums, 0, len(nums) - 1, True, 0, 0
    while i <= j:
        if a[i] >= a[j]:
            take, i = a[i], i + 1
        else:
            take, j = a[j], j - 1
        if p1_turn:
            p1 += take
        else:
            p2 += take
        p1_turn = not p1_turn
    return p1 >= p2


def both_maximise_bug(nums: List[int]) -> bool:
    """Mistake 2: player 1's score maximised at every level, as if player 2 helped."""
    @cache
    def best(i: int, j: int, p1_turn: bool) -> int:        # returns p1 - p2
        if i > j:
            return 0
        sign = 1 if p1_turn else -1
        return max(sign * nums[i] + best(i + 1, j, not p1_turn),
                   sign * nums[j] + best(i, j - 1, not p1_turn))
    return best(0, len(nums) - 1, True) >= 0


def tie_is_loss_bug(nums: List[int]) -> bool:
    """Mistake 3: strict > 0."""
    return margin(nums) > 0


def downward_j_bug(nums: List[int]) -> bool:
    """Mistake 4: j loops downward, so dp[j-1] is still the row below."""
    n = len(nums)
    dp = nums[:]
    for i in range(n - 2, -1, -1):
        for j in range(n - 1, i, -1):                    # BUG: must go i+1 .. n-1
            dp[j] = max(nums[i] - dp[j], nums[j] - dp[j - 1])
    return dp[n - 1] >= 0


# ==============================================================================
# TESTS — run:  python 019_predict_the_winner_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: one-row DP vs memo vs brute-force minimax ---")
    cases = [([1, 5, 2], False), ([1, 5, 233, 7], True), ([7], True), ([1, 1], True),
             ([0, 0, 7, 6, 5, 6, 1], False), ([2, 4, 55, 6, 8], False), ([3, 9, 1, 2], True)]
    for nums, want in cases:
        results = (sol.predictTheWinner(nums), winner_memo(nums), minimax_brute(nums))
        ok = all(r == want for r in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!s:<24} got={results}  want={want}")

    print("\n--- randomized cross-check vs brute force (1,000 arrays, n <= 12) ---")
    rng = random.Random(486)
    bad = 0
    for _ in range(1000):
        nums = [rng.randint(0, 20) for _ in range(rng.randint(1, 12))]
        if sol.predictTheWinner(nums) != minimax_brute(nums) or winner_memo(nums) != minimax_brute(nums):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  1,000 random arrays agree with brute-force minimax")

    print("\n--- even length: player 1 never loses (2,000 random arrays) ---")
    ok = all(sol.predictTheWinner([rng.randint(0, 50) for _ in range(2 * rng.randint(1, 10))])
             for _ in range(2000))
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  every even-length array is a win for player 1")

    print("\n--- mistakes LIVE ---")
    g = greedy_larger_end([1, 5, 233, 7])
    ok = g is False and sol.predictTheWinner([1, 5, 233, 7])
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  greedy larger end on [1,5,233,7] -> {g}, want True (take 1 first)")
    b = both_maximise_bug([1, 5, 2])
    ok = b is True and not sol.predictTheWinner([1, 5, 2])
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  both players maximise p1 on [1,5,2] -> {b}, want False")
    t = tie_is_loss_bug([1, 1])
    ok = t is False and sol.predictTheWinner([1, 1])
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  tie counted as a loss on [1,1] -> {t}, want True")
    wrong = sum(downward_j_bug(nums) != sol.predictTheWinner(nums)
                for nums in ([rng.randint(0, 20) for _ in range(rng.randint(3, 12))] for _ in range(1000)))
    ok = wrong > 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  j looped downward: wrong on {wrong} of 1,000 random arrays")

    print("\n--- why memoise: calls made by plain minimax ---")
    global CALLS
    for n in (10, 14, 18):
        CALLS = 0
        minimax_brute([rng.randint(0, 9) for _ in range(n)])
        print(f"      n={n}: {CALLS:>9,} calls  vs  {n * (n + 1) // 2} distinct windows")
    nums = [rng.randint(0, 10**7) for _ in range(20)]
    t0 = time.perf_counter(); r1 = sol.predictTheWinner(nums); t1 = time.perf_counter()
    CALLS = 0; r2 = minimax_brute(nums); t2 = time.perf_counter()
    ok = r1 == r2
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  n=20: one-row DP {1000 * (t1 - t0):.2f} ms vs "
          f"brute force {1000 * (t2 - t1):.0f} ms ({CALLS:,} calls), same answer")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
