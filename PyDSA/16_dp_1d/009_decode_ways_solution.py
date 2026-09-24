"""
================================================================================
SOLUTION · LeetCode 91 · Decode Ways                                  [Medium]
https://leetcode.com/problems/decode-ways/
================================================================================

THE CORE IDEA
--------------
dp[i] MEANS "the number of ways to decode the prefix s[:i]". The last
decoded token was either the single digit s[i-1] (valid iff not '0') or
the pair s[i-2:i] (valid iff its numeric value is 10..26). Add whichever
options are valid:

    dp[0] = 1
    dp[i] = dp[i-1] * [s[i-1] != '0']
          + dp[i-2] * [10 <= int(s[i-2:i]) <= 26]     (only if i >= 2)


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion, price it, don't ship it): recurse from index
i, trying a 1-digit token then a 2-digit token, `ways(i) = ways(i+1) if
valid1 + ways(i+2) if valid2`. O(2^n) worst case (e.g. a string of all
'1's and '2's where both branches are almost always valid) -- same
repeated-subproblem blowup as every earlier problem here.

Approach 1 (memoized top-down) [`decode_memo`] -- cache each index. O(n)
time, O(n) space.

Approach 2 (tabulated bottom-up) [`decode_tab`] -- fill dp[0..n] left to
right. O(n) time, O(n) space.

Approach 3 (space-optimized) [chosen] -- dp[i] only reads dp[i-1], dp[i-2],
roll two variables. O(n) time, O(1) space.


================================================================================
STEP BY STEP TRACE
================================================================================
s = "226"    (n = 3)

dp[0] = 1                                          (empty prefix)
dp[1]: s[0]='2' != '0'  -> dp[1] = dp[0] = 1
dp[2]: s[1]='2' != '0'  -> +dp[1] = 1
       pair s[0:2]="22", 10<=22<=26  -> +dp[0] = 1
       dp[2] = 1 + 1 = 2
dp[3]: s[2]='6' != '0'  -> +dp[2] = 2
       pair s[1:3]="26", 10<=26<=26  -> +dp[1] = 1
       dp[3] = 2 + 1 = 3                            <- answer

 i     : 0  1  2  3
dp[i]  : 1  1  2  3

Matches the three groupings from the problem statement: (2 2 6), (2 26),
(22 6).

Rolling trace (prev2, prev1) = (dp[i-2], dp[i-1]) before computing dp[i]:
    start:            prev2=1 (dp0), prev1=1 (dp1)
    i=2: single ok +prev1=1, pair "22" ok +prev2=1 -> dp2=2  -> prev2=1, prev1=2
    i=3: single ok +prev1=2, pair "26" ok +prev2=1 -> dp3=3  -> prev2=2, prev1=3
    return prev1 = 3


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time     Space   Mutates input?
    ---------------------------  -------  ------  --------------
    Naive recursion               O(2^n)  O(n)    no
    Memoized top-down             O(n)    O(n)    no
    Tabulated bottom-up           O(n)    O(n)    no
    Rolling variables [chosen]    O(n)    O(1)    no


================================================================================
EDGE CASES
================================================================================
    s starts with '0' ("06")  -> single-digit token invalid at i=1, and no
                              pair is possible yet (i<2) -> dp[1]=0, which
                              then propagates 0 through every later dp[i]
                              that depends on it -- confirms zero-propagation
                              works, not just the base case itself.
    s == "0"                  -> dp[1]=0 directly, answer 0.
    a lone '0' in the MIDDLE ("100") -> the '0' can only be decoded as
                              part of a two-digit pair with the digit
                              before it; "100" has no valid pair covering
                              the second '0' (pair "00" is invalid, and a
                              lone "0" is invalid) -> answer 0.
    pair value > 26 ("27")     -> single-digit contributions still count
                              (dp[1]=1 for '2', dp[2] adds dp[1] for '7'
                              but NOT dp[0] since "27">26) -> answer 1.
    len(s) == 1                -> only the single-digit case applies;
                              answer is 1 if s != "0" else 0.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the leading-zero rule for single digits: '0' alone is never
   decodable, but pairs like "10" and "20" ARE valid (the zero is the
   SECOND digit of a valid two-digit letter, J=10 and T=20).
2. Checking the pair range as 1-26 instead of 10-26 -- a pair like "05" is
   NOT a valid two-digit token (would double-count with the single-digit
   '5' path and represents a leading zero within the pair).
3. Not letting a "no valid decoding here" (both contributions zero) value
   propagate forward -- once dp[i] hits 0, every dp[j] for j>i that
   depends on it correctly stays 0 without any special-casing, as long as
   you don't accidentally treat 0 as "uncomputed" and skip it.
4. Off-by-one between "index into dp" (which counts CHARACTERS consumed,
   0..n) and "index into s" (0..n-1) -- s[i-1] is the CHARACTER at prefix
   position i, not s[i].


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if '*' can represent any digit 1-9 (or any pair 1-26)?" -> LC 639
  Decode Ways II -- same recurrence shape but each transition needs to
  count multiple matching digit values instead of a single 0/1 validity
  check; still 1D DP, more arithmetic per cell.
- "Can you decode without recomputing the whole count, just check
  validity (yes/no any decoding exists)?" -> same recurrence with boolean
  OR instead of integer addition.
- "Can you do it in O(1) space?" -> yes, shown above.


================================================================================
RELATED PROBLEMS
================================================================================
- 002 Climbing Stairs (LC 70) -- identical "fixed window of 2, sum the
  valid options" shape, without the validity conditions.
- Decode Ways II (LC 639) -- wildcard generalization noted above.
- 012 Word Break (LC 139) -- also "can the prefix be validly segmented,"
  but with a variable-length dictionary lookup instead of a fixed 1-or-2
  digit window.
================================================================================
"""

import sys
import time


class Solution:
    def numDecodings(self, s: str) -> int:
        n = len(s)
        prev2, prev1 = 1, 1 if s[0] != '0' else 0  # dp[0], dp[1]
        for i in range(2, n + 1):
            cur = 0
            if s[i - 1] != '0':
                cur += prev1
            two_digit = int(s[i - 2:i])
            if 10 <= two_digit <= 26:
                cur += prev2
            prev2, prev1 = prev1, cur
        return prev1


def decode_naive(s: str, i: int = 0) -> int:
    n = len(s)
    if i == n:
        return 1
    if s[i] == '0':
        return 0
    ways = decode_naive(s, i + 1)
    if i + 1 < n and 10 <= int(s[i:i + 2]) <= 26:
        ways += decode_naive(s, i + 2)
    return ways


def decode_memo(s: str) -> int:
    n = len(s)
    memo = {}

    def solve(i: int) -> int:
        if i == n:
            return 1
        if s[i] == '0':
            return 0
        if i in memo:
            return memo[i]
        ways = solve(i + 1)
        if i + 1 < n and 10 <= int(s[i:i + 2]) <= 26:
            ways += solve(i + 2)
        memo[i] = ways
        return ways

    return solve(0)


def decode_tab(s: str) -> int:
    n = len(s)
    dp = [0] * (n + 1)
    dp[0] = 1
    dp[1] = 1 if s[0] != '0' else 0
    for i in range(2, n + 1):
        if s[i - 1] != '0':
            dp[i] += dp[i - 1]
        if 10 <= int(s[i - 2:i]) <= 26:
            dp[i] += dp[i - 2]
    return dp[n]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ("12", 2),
        ("226", 3),
        ("06", 0),
        ("0", 0),
        ("10", 1),
        ("27", 1),
        ("1", 1),
        ("11106", 2),
        ("100", 0),
        ("2101", 1),
    ]
    for s, want in cases:
        got = sol.numDecodings(s)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r}  -> {got}  (want {want})")
        assert decode_memo(s) == want
        assert decode_tab(s) == want

    print()
    print("RUNTIME DEMO -- naive O(2^n) recursion vs memoized O(n), measured live")
    print("-" * 72)
    print("(using strings of all '1's/'2's -- every position has BOTH single")
    print(" and pair options valid, which is the worst case for the naive tree)")
    sys.setrecursionlimit(10000)
    for n in (15, 22, 28):
        s = "12" * (n // 2) + "1" * (n % 2)
        t0 = time.perf_counter()
        naive_result = decode_naive(s)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        memo_result = decode_memo(s)
        memo_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == memo_result
        print(f"n={n:3d}  naive={naive_ms:9.3f} ms   memo={memo_ms:7.4f} ms   "
              f"ratio={naive_ms / max(memo_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
