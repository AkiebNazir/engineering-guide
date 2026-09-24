"""
================================================================================
LeetCode 1342 · Number of Steps to Reduce a Number to Zero                [Easy]
https://leetcode.com/problems/number-of-steps-to-reduce-a-number-to-zero/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given an integer `num`, return the number of steps to reduce it to zero.

In one step, if the current number is even, you have to divide it by 2,
otherwise, you have to subtract 1 from it.

EXAMPLES
--------
Example 1:
    Input:  num = 14
    Output: 6
    Explanation: 14 -> 7 -> 6 -> 3 -> 2 -> 1 -> 0
        step 1) 14 is even; 14 / 2 = 7
        step 2) 7 is odd; 7 - 1 = 6
        step 3) 6 is even; 6 / 2 = 3
        step 4) 3 is odd; 3 - 1 = 2
        step 5) 2 is even; 2 / 2 = 1
        step 6) 1 is odd; 1 - 1 = 0

Example 2:
    Input:  num = 8
    Output: 4
    Explanation: 8 -> 4 -> 2 -> 1 -> 0

Example 3:
    Input:  num = 123
    Output: 12

CONSTRAINTS
-----------
    0 <= num <= 10^6

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the absolute floor of the recursion ladder in this folder: ONE
recursive call, ONE base case, and an accumulator that counts steps as it goes
down. There is no branching, no combine step beyond "add 1," and no structure
to build — just: "am I at the base case? If not, take exactly one step and ask
a strictly smaller version of myself for the rest of the answer."

The recursive shape falls straight out of the problem statement:

    steps(0) = 0                                  <- base case
    steps(n) = 1 + steps(n // 2)      if n even    <- one step, then recurse
    steps(n) = 1 + steps(n - 1)       if n odd     <- one step, then recurse

Every call does exactly one of two things to `n` before recursing (halve it,
or subtract 1), and both moves strictly shrink `n` toward 0. That is the
entire correctness argument — there's no need to "trust" anything more
complicated than "n gets smaller every single call, and 0 is reachable."

WHAT TO THINK ABOUT
--------------------
1. What is the minimal input where the answer is obviously and trivially
   known without doing any work? (Not "small" — the exact smallest.)
2. Each recursive call returns "steps needed for the rest of the journey."
   What does the CURRENT call need to add to that, to answer for itself?
3. Does the recursion depth track the number of steps 1-for-1, or could it
   be smaller/larger? (Hint: every recursive call corresponds to exactly one
   step taken — depth == answer here, unlike topics 04/005 where dividing
   collapses depth below the raw step count.)
4. This problem admits an O(1) bit-trick solution using `num.bit_length()`
   and `bin(num).count('1')` — interesting as a follow-up, but the point of
   this file is the plain recursive translation, not the bit trick.

PROGRESSIVE HINTS
------------------
Hint 1: Base case: `num == 0` needs 0 steps.
Hint 2: At each call, check `num % 2`. Even -> next call is on `num // 2`.
        Odd -> next call is on `num - 1`. Either way, add 1 for the step
        just taken.
Hint 3: `return 1 + steps(num // 2 if num % 2 == 0 else num - 1)` is the
        entire recursive step in one line.
Hint 4: Recursion depth here equals the final answer exactly (no calls are
        "skipped" or "batched") — for `num` up to 10^6 that is at most
        ~20 (halvings) + up to 1 (subtraction) per halving, so depth is
        bounded by roughly 2 * log2(num), nowhere near Python's recursion
        limit. Contrast this with a hypothetical version that only ever
        subtracted 1 — that would need up to 10^6 stack frames and blow the
        default recursion limit; the halving is what keeps this safe.

COMPLEXITY TARGET
------------------
    Recursive (halve/subtract): O(log num) time, O(log num) space (call stack)
    Iterative twin:              O(log num) time, O(1) space
================================================================================
"""


class Solution:
    def numberOfSteps(self, num: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 001_number_of_steps_to_reduce_a_number_to_zero_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        (0, 0), (1, 1), (2, 2), (3, 3), (4, 3), (8, 4), (14, 6),
        (123, 12), (1000000, 25),
    ]
    passed = 0
    for num, expected in cases:
        got = sol.numberOfSteps(num)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  numberOfSteps({num}) -> {got}  (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
