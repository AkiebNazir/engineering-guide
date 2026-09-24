"""
================================================================================
SOLUTION · LeetCode 739 · Daily Temperatures                           [Medium]
https://leetcode.com/problems/daily-temperatures/
================================================================================

THE CORE IDEA
--------------
Exactly problem 003's monotonic-stack template (topic guide §2.0-2.3) with
one substitution: the resolve step records a DISTANCE (`i - j`) instead of
a VALUE. The stack holds indices of days still waiting for a warmer day,
in decreasing-temperature order bottom-to-top:

    answer = [0] * n
    stack = []                       # indices, temperatures DECREASING top-down
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            answer[j] = i - j        # DISTANCE, not temperatures[i]
        stack.append(i)
    return answer

O(n) time, O(n) space. `answer` is pre-filled with 0, so any index that
never gets resolved (never finds a warmer future day) correctly keeps its
default — no separate "unresolved" pass needed at the end, unlike problem
003 where -1 had to be supplied via `.get(v, -1)` at query time.


================================================================================
WHY THE STACK MUST HOLD INDICES, NOT TEMPERATURES
================================================================================
Problem 003 could push raw values because the answer it needed WAS a
value. Here the answer is `i - j` — a computation that needs BOTH the
current index and the waiting day's index. Pushing temperatures alone
would throw away exactly the information the resolve step needs; you
cannot recover "how many days ago" from a temperature value alone,
especially since temperatures can repeat (multiple days at the same
temperature, and this problem's constraint 30 <= t <= 100 guarantees
repeats are common with n up to 10^5).


================================================================================
WHY DAY 2's 75° DOES NOT RESOLVE AGAINST DAY 5's 72°
================================================================================
temperatures = [73, 74, 75, 71, 69, 72, 76, 73], focus on index 2 (75°).

75° is warmer than 71° (day 3), 69° (day 4), and 72° (day 5) — none of
those pop it off the stack, because the CONDITION is `temperatures[top] < t`,
i.e. the stack only pops when the INCOMING day is warmer than what's
waiting, not the other way around. Index 2 (75°) stays on the stack
through days 3, 4, 5 because none of THEM are warmer than 75° — they get
pushed on top of it instead, each waiting for their own future day. Index
2 only resolves when day 6 (76°) arrives, four days later:
`answer[2] = 6 - 2 = 4`. The monotonic stack only ever compares an
incoming value against what is CURRENTLY EXPOSED on top — days 3, 4, 5
each get compared against whatever was on top when THEY arrived (each
other, then eventually day 2), never skipped over.


================================================================================
STEP BY STEP TRACE
================================================================================
temperatures = [73, 74, 75, 71, 69, 72, 76, 73]

    i  t    stack before        action                                  stack after    answer so far
    -  -    ------------        ------                                  -----------    --------------
    0  73   []                  nothing to compare, push 0               [0]            [0,0,0,0,0,0,0,0]
    1  74   [0]                 74>73: pop 0, ans[0]=1-0=1; push 1        [1]            [1,0,0,0,0,0,0,0]
    2  75   [1]                 75>74: pop 1, ans[1]=2-1=1; push 2        [2]            [1,1,0,0,0,0,0,0]
    3  71   [2]                 71<75, no pop; push 3                    [2,3]          [1,1,0,0,0,0,0,0]
    4  69   [2,3]               69<71, no pop; push 4                    [2,3,4]        [1,1,0,0,0,0,0,0]
    5  72   [2,3,4]             72>69: pop 4, ans[4]=5-4=1
                                 72>71: pop 3, ans[3]=5-3=2
                                 72<75, stop; push 5                     [2,5]          [1,1,0,2,1,0,0,0]
    6  76   [2,5]               76>72: pop 5, ans[5]=6-5=1
                                 76>75: pop 2, ans[2]=6-2=4
                                 stack empty; push 6                     [6]            [1,1,4,2,1,1,0,0]
    7  73   [6]                 73<76, no pop; push 7                    [6,7]          [1,1,4,2,1,1,0,0]

    end: indices 6, 7 never resolved -> answer[6]=answer[7]=0 (pre-filled default)

    final answer = [1,1,4,2,1,1,0,0]   ✓ matches example 1


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                                Time    Space   Mutates input?  Note
    ---------------------------------------  ------  ------  ---------------  ----------------------
    Brute: for each day, scan forward        O(n^2)  O(n)    no               worst case: strictly
           until a warmer day appears                                        decreasing temps —
                                                                               every scan runs to end
    Monotonic stack ✅                      O(n)    O(n)    no               the answer


================================================================================
EDGE CASES
================================================================================
    Strictly decreasing temps [90,60,30] -> every answer is 0; nothing
        ever resolves, but the stack still processes in O(n) — the WORST
        case for stack SPACE (holds every index) but not for time.
    Strictly increasing temps [30,40,50,60] -> every day except the last
        resolves in exactly 1 step; the stack never holds more than a
        couple of entries at once, but the while loop fires on almost
        every iteration — still O(n) total per the amortized argument.
    All equal temperatures [50,50,50] -> the strict `<` comparison means
        NOTHING ever pops (equal is not "warmer") — every answer is 0,
        and this exercises that the condition really is strict, not `<=`.
    Single day [50] -> [0], trivially — no future day exists at all.
    A single hot day resolves a long cold streak, [100,30,100] -> index 0
        (100°) never resolves (nothing beats it); index 1 (30°) resolves
        immediately against index 2.


================================================================================
COMMON MISTAKES
================================================================================
1. Pushing temperatures instead of indices — loses the information needed
   to compute `i - j`, and can't disambiguate repeated temperature values
   at different days. See the explanation above.

2. Using `<=` instead of `<` in the stack condition — treats an EQUAL
   temperature as "warmer," incorrectly resolving days that saw no actual
   increase. All-equal input is the test that catches this.

3. Forgetting to pre-fill `answer` with 0 (or writing an explicit
   "unresolved" pass at the end instead) — a plain `answer = []` with
   `.append()` doesn't naturally leave room for indices that never get
   resolved out of order (they resolve LATER than earlier indices, not in
   position order), so pre-filling by index is the simplest correct
   approach.

4. Computing `answer[j] = temperatures[i] - temperatures[j]` (a
   temperature DIFFERENCE) instead of `i - j` (a day COUNT) — conflates
   this problem with problem 003's "next greater VALUE" shape instead of
   this problem's "next greater DISTANCE" shape.

5. Off-by-one on the distance formula: `i - j` is correct (days elapsed
   from day j to day i); `i - j - 1` or `i - j + 1` silently shifts every
   answer by one day.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if you needed the FIRST day (not the wait count) that is warmer?
A: Record `i` itself instead of `i - j` at resolve time — same template,
   answer becomes "which day" instead of "how many days."

Q: What if temperatures could be floating point instead of bounded
   integers 30-100?
A: No change at all — the algorithm never uses the bounded-integer
   constraint; it works for any comparable type.

Q: The constraint bounds temperatures to [30, 100] — does that let you do
   anything faster than O(n)?
A: Not asymptotically faster, but it enables a different O(n) approach:
   track, for each of the 71 possible temperature VALUES, the most recent
   day index seen at or above that value, then for each day look up the
   nearest recorded day among values > current. This trades the stack for
   a small fixed-size array scan (O(71) per day), which is still O(n)
   overall but with different constants — a legitimate follow-up, not an
   improvement in big-O.

Q: How is this different from Next Greater Element (problem 003)?
A: Same monotonic-stack skeleton; the only difference is the payload
   recorded at resolve time (a distance here vs. a value there) — see
   topic guide §2.3's table for the full family.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 496  Next Greater Element I     — problem 003 here: the template
                                          this problem specializes
    LC 503  Next Greater Element II    — circular variant of 003
    LC 901  Online Stock Span          — problem 009 here: same template,
                                          streaming/online instead of a
                                          fixed array
    LC 84   Largest Rectangle in
            Histogram                  — problem 010 here: same template,
                                          payload is an area
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def dailyTemperatures(self, temperatures: List[int]) -> List[int]:
        """Monotonic decreasing stack of indices. O(n) time, O(n) space.
        The answer. See THE CORE IDEA above."""
        n = len(temperatures)
        answer = [0] * n
        stack: List[int] = []
        for i, t in enumerate(temperatures):
            while stack and temperatures[stack[-1]] < t:
                j = stack.pop()
                answer[j] = i - j
            stack.append(i)
        return answer

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def dailyTemperatures_brute(self, temperatures: List[int]) -> List[int]:
        """O(n^2) reference: for each day, scan forward until a warmer
        day appears (or the array ends)."""
        n = len(temperatures)
        answer = [0] * n
        for i in range(n):
            for j in range(i + 1, n):
                if temperatures[j] > temperatures[i]:
                    answer[i] = j - i
                    break
        return answer


# ==============================================================================
# TESTS — run:  python 007_daily_temperatures_solution.py
# ==============================================================================
CASES = [
    ([73, 74, 75, 71, 69, 72, 76, 73], [1, 1, 4, 2, 1, 1, 0, 0]),
    ([30, 40, 50, 60], [1, 1, 1, 0]),
    ([30, 60, 90], [1, 1, 0]),
    ([90, 60, 30], [0, 0, 0]),
    ([50], [0]),
    ([50, 50, 50], [0, 0, 0]),
    ([50, 51], [1, 0]),
    ([100, 30, 100], [0, 1, 0]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: monotonic stack vs O(n^2) brute force ---")
    for temps, expected in CASES:
        want = sol.dailyTemperatures_brute(list(temps))
        got = sol.dailyTemperatures(list(temps))
        ok = got == expected and want == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  temps={temps!r:<40} -> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: temperatures = [73,74,75,71,69,72,76,73] ---")
    temps = [73, 74, 75, 71, 69, 72, 76, 73]
    n = len(temps)
    answer = [0] * n
    stack: List[int] = []
    for i, t in enumerate(temps):
        popped = []
        while stack and temps[stack[-1]] < t:
            j = stack.pop()
            answer[j] = i - j
            popped.append(j)
        stack.append(i)
        popped_str = str(popped) if popped else "-"
        print(f"  i={i} t={t:<3} resolved indices: {popped_str:<10} stack: {stack!s:<14} "
              f"answer so far: {answer}")

    # ----------------------------------------------------------------------
    # Randomised cross-check vs the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(7)
    trials, mismatches = 2000, 0
    for _ in range(trials):
        n_days = random.randint(1, 20)
        temps = [random.randint(30, 100) for _ in range(n_days)]
        if sol.dailyTemperatures(temps) != sol.dailyTemperatures_brute(temps):
            mismatches += 1
    print(f"  {trials} random temperature arrays (len 1-20, values 30-100): {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # O(n) monotonic stack vs O(n^2) brute-force scan: measured runtime.
    # ----------------------------------------------------------------------
    print("\n--- O(n) monotonic stack vs O(n^2) brute-force scan: measured runtime ---")
    print("  (worst case: strictly decreasing temperatures — every brute scan")
    print("   runs to the end, and the stack only ever grows)")
    print(f"  {'n':>7} {'stack O(n)':>14} {'brute O(n^2)':>14} {'ratio':>8}")
    for n in (500, 2_000, 4_000):
        temps = [100 - (i % 71) for i in range(n)]   # roughly decreasing within [30,100] bound
        temps = sorted(temps, reverse=True)          # force the true worst case
        t0 = time.perf_counter(); sol.dailyTemperatures(temps)
        t1 = time.perf_counter(); sol.dailyTemperatures_brute(temps)
        t2 = time.perf_counter()
        st_ms = (t1 - t0) * 1000
        br_ms = (t2 - t1) * 1000
        ratio = br_ms / st_ms if st_ms > 0 else float("inf")
        print(f"  {n:>7} {st_ms:>12.2f}ms {br_ms:>12.2f}ms {ratio:>7.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
