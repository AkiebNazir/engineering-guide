"""
================================================================================
SOLUTION · LeetCode 402 · Remove K Digits                               [Medium]
https://leetcode.com/problems/remove-k-digits/
================================================================================

THE CORE IDEA
--------------
Greedy with a monotonic non-decreasing stack. Every time the incoming digit is
SMALLER than the stack top, the top is a "peak": deleting it puts a smaller
digit in a more significant position. Pop while you still have deletions.
Whatever deletions remain after the scan come off the END (the stack is
non-decreasing, so the end holds the largest digits). Then strip leading
zeros, and return "0" if nothing is left.


================================================================================
APPROACH 1 · Try every set of k positions (priced, used only as an oracle)
================================================================================
Choose which k digits to delete, build each result, take the minimum.

    Time: O(C(n, k) * n)    Space: O(n)


================================================================================
APPROACH 2 · Delete the leftmost peak, k times
================================================================================
Scan for the first i with num[i] > num[i + 1] (or the last digit if none),
delete it, repeat.

    Time: O(n * k)    Space: O(n)

Correct (same greedy as the stack), but rescans from the start after each
deletion. At n = k = 10^5 it's ~10^10 steps in the worst case.


================================================================================
APPROACH 3 · Monotonic stack ✅ (the answer)
================================================================================
    stack = []
    for d in num:
        while k and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    if k:
        stack = stack[:-k]              # remaining deletions come off the end
    return "".join(stack).lstrip("0") or "0"

WHY THE GREEDY IS CORRECT. Consider the first position p where the stack top
is bigger than the next digit. Any result that KEEPS that bigger digit at its
position while there's a smaller digit available right after it can be
improved by deleting the bigger one instead: the prefix is the same and the
digit at the first differing position gets smaller. So an optimal answer
never keeps a peak while deletions remain. The stack simply performs these
leftmost-peak deletions in amortized O(1) each.

WHY `stack[-1] > d` (STRICT). Popping an EQUAL digit spends a deletion
without making the number smaller at that position. "112", k = 1: with `>=`,
the second '1' pops the first (k becomes 0), then '2' is pushed, giving "12".
The strict version pops nothing, chops the trailing '2', and returns "11".
The demo runs both.

    Time: O(n) — each digit pushed and popped at most once    Space: O(n)


================================================================================
STEP BY STEP TRACE · num = "1432219", k = 3
================================================================================
    d  stack before   pops (while top > d, k > 0)        k after  stack after
    -  ------------   --------------------------------  -------  -----------
    1  []             —                                  3        [1]
    4  [1]            —                                  3        [1,4]
    3  [1,4]          pop 4                              2        [1,3]
    2  [1,3]          pop 3                              1        [1,2]
    2  [1,2]          — (2 is not > 2)                   1        [1,2,2]
    1  [1,2,2]        pop 2 (k -> 0, stop)               0        [1,2,1]
    9  [1,2,1]        — (k == 0)                         0        [1,2,1,9]

    k == 0, no tail chop, no leading zeros -> "1219"


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time            Space   Mutates input?
    ------------------------------  --------------  ------  --------------
    Try every deletion set          O(C(n,k) * n)   O(n)    No
    Leftmost peak, k rescans        O(n * k)        O(n)    No
    Monotonic stack ✅              O(n)            O(n)    No


================================================================================
EDGE CASES
================================================================================
    k == n                   Everything removed -> "0".
    Non-decreasing digits     Nothing popped; chop k from the end.
    Leading zeros after pops  "10200", k=1 -> stack "0200" -> "200".
    All zeros result          "100", k=1 -> "00" -> "" -> "0".
    Equal runs                "112", k=1 -> "11".


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the leftover-k chop. "12345", k=2 returns "12345". Demo below.

2. Forgetting to strip leading zeros. "10200", k=1 returns "0200". Demo below.

3. Returning "" instead of "0" when everything is removed.

4. Removing the LARGEST digits instead of the leftmost peaks.
   "1432219", k=1: removing 9 gives 143221; removing the first peak (4) gives
   132219, which is smaller.

5. Stripping zeros INSIDE the loop (skipping zero pushes onto an empty stack)
   and then miscounting length. Stripping once at the end is simpler.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: LARGEST number after removing k digits?
A: Flip the comparison: pop while stack[-1] < d.

Q: Smallest subsequence of length exactly m from a digit string?
A: Same problem with k = n - m.

Q: Create Maximum Number from two arrays (LC 321)?
A: For each split i + j = k, take the best length-i subsequence of one array
   and length-j of the other (this stack routine), then merge greedily.

Q: Remove Duplicate Letters (LC 316)?
A: Same monotonic stack, but a character can only be popped if it appears
   again later, and each character is kept once.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 316   Remove Duplicate Letters       — monotonic stack with "seen later" guard
    LC 321   Create Maximum Number          — this routine twice + merge
    LC 1673  Find the Most Competitive Subsequence — identical with k = n - m
    LC 739   Daily Temperatures (007)        — monotonic stack, next-greater form
================================================================================
"""

import random
import time
from itertools import combinations
from typing import List


class Solution:
    def removeKdigits(self, num: str, k: int) -> str:
        stack: List[str] = []
        for d in num:
            while k and stack and stack[-1] > d:
                stack.pop()
                k -= 1
            stack.append(d)
        if k:
            stack = stack[:-k]
        return "".join(stack).lstrip("0") or "0"


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def remove_brute(num: str, k: int) -> str:
    n = len(num)
    best = None
    for keep in combinations(range(n), n - k):
        candidate = "".join(num[i] for i in keep).lstrip("0") or "0"
        if best is None or (len(candidate), candidate) < (len(best), best):
            best = candidate
    return best


def remove_peak_rescan(num: str, k: int) -> str:
    digits = list(num)
    for _ in range(k):
        i = 0
        while i + 1 < len(digits) and digits[i] <= digits[i + 1]:
            i += 1
        del digits[i]
    return "".join(digits).lstrip("0") or "0"


def remove_no_tail_chop_bug(num: str, k: int) -> str:
    stack: List[str] = []
    for d in num:
        while k and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    return "".join(stack).lstrip("0") or "0"          # BUG: leftover k ignored


def remove_non_strict_bug(num: str, k: int) -> str:
    stack: List[str] = []
    for d in num:
        while k and stack and stack[-1] >= d:           # BUG: pops equal digits
            stack.pop()
            k -= 1
        stack.append(d)
    if k:
        stack = stack[:-k]
    return "".join(stack).lstrip("0") or "0"


def remove_no_strip_bug(num: str, k: int) -> str:
    stack: List[str] = []
    for d in num:
        while k and stack and stack[-1] > d:
            stack.pop()
            k -= 1
        stack.append(d)
    if k:
        stack = stack[:-k]
    return "".join(stack) or "0"                        # BUG: leading zeros kept


# ==============================================================================
# TESTS — run:  python 013_remove_k_digits_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: examples and edge cases ---")
    cases = [
        ("1432219", 3, "1219"),
        ("10200", 1, "200"),
        ("10", 2, "0"),
        ("12345", 2, "123"),
        ("54321", 2, "321"),
        ("112", 1, "11"),
        ("100", 1, "0"),
        ("9", 1, "0"),
    ]
    for num, k, want in cases:
        got = sol.removeKdigits(num, k)
        ok = got == want == remove_peak_rescan(num, k)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  num={num!r:<10} k={k}  got={got!r}  want={want!r}")

    print("\n--- greedy proven on data: stack == exhaustive search (600 inputs, repeated digits) ---")
    rng = random.Random(402)
    bad = 0
    for _ in range(600):
        n = rng.randint(1, 9)
        num = str(rng.randint(1, 9)) + "".join(rng.choice("0112") for _ in range(n - 1))
        k = rng.randint(1, n)
        if sol.removeKdigits(num, k) != remove_brute(num, k):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  600 random inputs match brute force")

    print("\n--- mistakes LIVE ---")
    w1 = remove_no_tail_chop_bug("12345", 2)
    ok = w1 == "12345" and sol.removeKdigits("12345", 2) == "123"
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no tail chop:   '12345', k=2 -> {w1!r} (nothing was removed; want '123')")
    w2 = remove_no_strip_bug("10200", 1)
    ok = w2 == "0200" and sol.removeKdigits("10200", 1) == "200"
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no zero strip:  '10200', k=1 -> {w2!r} (want '200')")
    w3 = remove_non_strict_bug("112", 1)
    ok = w3 == "12" and sol.removeKdigits("112", 1) == "11"
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  pop on >=:      '112', k=1 -> {w3!r} (want '11')")

    print("\n--- benchmark: leftmost-peak rescans O(n*k) vs stack O(n) ---")
    for n in (2_000, 4_000, 8_000):
        num = "".join(str(9 - (i % 10)) for i in range(n))  # sawtooth: peaks everywhere
        k = n // 2
        t0 = time.perf_counter(); a = remove_peak_rescan(num, k); tr = time.perf_counter() - t0
        t0 = time.perf_counter(); b = sol.removeKdigits(num, k); ts = time.perf_counter() - t0
        all_ok &= a == b
        print(f"      n={n:>5} k={k:>5}  rescan {tr * 1000:8.1f} ms   stack {ts * 1000:6.2f} ms   ratio {tr / ts:6.0f}x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
