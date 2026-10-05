"""
================================================================================
SOLUTION · LeetCode 647 · Palindromic Substrings                     [Medium]
https://leetcode.com/problems/palindromic-substrings/
================================================================================

THE CORE IDEA
--------------
Identical structure to problem 007: dp[i][j] MEANS "is s[i..j] a
palindrome", true iff the ends match and the smaller interior is also a
palindrome. Here the aggregation is a COUNT instead of a longest-length
tracker: every center (2n-1 of them: n single-character centers, n-1
between-character gaps) contributes exactly one count for every
successful expansion step, because each successful step IS a distinct
palindromic substring.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it, don't ship it): check every one of the
O(n^2) substrings for being a palindrome, O(n) each -> O(n^3) total.
Correct but far slower than needed, exactly like 007's brute force.

Approach 1 (tabulated dp[i][j], count True cells) [`count_dp_table`] --
fill the same table as 007 by increasing length, sum up every True cell.
O(n^2) time, O(n^2) space.

Approach 2 (expand around center) [chosen] -- for each of the 2n-1
centers, expand outward while both sides match; every successful
expansion increments the count by exactly one (it's a newly confirmed
palindromic substring, one character wider than the last). O(n^2) time,
O(1) extra space -- ships instead of the table for the same reason as 007.


================================================================================
STEP BY STEP TRACE
================================================================================
s = "aaa"   (indices: a=0 a=1 a=2)

Expand-around-center, counting every successful step:

    center i=0 (odd): "a" (len1) count+1 -> total=1
                       left=-1 stop, no more expansion
    gap(0,1) (even):  s[0]==s[1] ('a'=='a') "aa" (len2) count+1 -> total=2
                       left=-1 stop
    center i=1 (odd): "a" (len1) count+1 -> total=3
                       expand left=0,right=2: s[0]=='a'==s[2] -> "aaa" (len3)
                       count+1 -> total=4
                       expand left=-1 stop
    gap(1,2) (even):  s[1]==s[2] 'a'=='a' "aa" (len2) count+1 -> total=5
                       left=0,right=3(oob) stop
    center i=2 (odd): "a" (len1) count+1 -> total=6
                       left=1,right=3(oob) stop

Total = 6, matching "a","a","a","aa","aa","aaa".


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time    Space    Mutates input?
    -------------------------------  ------  -------  --------------
    Brute force (check every substring) O(n^3) O(n)   no
    Tabulated dp[i][j], count True      O(n^2) O(n^2)  no
    Expand around center [chosen]       O(n^2) O(1)    no


================================================================================
EDGE CASES
================================================================================
    len(s) == 1            -> exactly one palindromic substring (the
                              character itself); expansion loops run but
                              immediately hit the boundary.
    all identical characters ("aaa")  -> EVERY substring is a palindrome;
                              count should equal n*(n+1)/2 (traced above:
                              3*4/2=6, matches).
    no repeated characters ("abc")     -> only the n single characters
                              count; every 2+ length window fails
                              immediately at the center check.
    even-length-only matches ("abba") -> forces counting via an EVEN
                              center ("bb", "abba"), same trap as 007.


================================================================================
COMMON MISTAKES
================================================================================
1. Only counting the LONGEST palindrome per center instead of every
   successful expansion step -- this problem wants every OCCURRENCE
   counted, not just the longest one per center.
2. Forgetting even centers again (same trap as 007) -- undercounts by
   missing every even-length palindrome.
3. Double-counting by iterating both "for each substring" AND "for each
   center" -- pick exactly one technique; mixing them (e.g. counting from
   centers AND then separately checking all substrings) double-counts.
4. Confusing "count of palindromic substrings" (this problem, counts
   occurrences/positions) with "count of DISTINCT palindromic substrings"
   (a different, harder problem needing deduplication, e.g. via a set or
   suffix structure) -- re-read the problem statement's own example 2 to
   confirm duplicates count separately.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if you need the count of DISTINCT palindromic substrings instead?"
  -> dedupe with a set of the actual substrings (or a suffix automaton /
  palindromic tree for large n to avoid the O(n^2) substring storage).
- "Can you do it in O(n)?" -> yes, Manacher's algorithm computes the
  palindrome radius at every center in O(n) total; the count falls out as
  the sum of radii+1 (each radius r center contributes r palindromes for
  odd, similar accounting for even).
- "How does this relate to Longest Palindromic Substring (007)?" -> same
  underlying dp[i][j]/center-expansion structure, different aggregation
  (count-all vs track-max) -- a good moment to point out the two problems
  share 90% of their code.


================================================================================
RELATED PROBLEMS
================================================================================
- 007 Longest Palindromic Substring (LC 5) -- same technique, find-max
  instead of count-all.
- Palindrome Partitioning (LC 131) -- uses this same dp[i][j] table as a
  precomputed lookup for a further partition-point DP.
================================================================================
"""

import time


class Solution:
    def countSubstrings(self, s: str) -> int:
        n = len(s)
        count = 0

        def expand(left: int, right: int) -> None:
            nonlocal count
            while left >= 0 and right < n and s[left] == s[right]:
                count += 1
                left -= 1
                right += 1

        for center in range(n):
            expand(center, center)      # odd length, center is a character
            expand(center, center + 1)  # even length, center is a gap
        return count


def count_brute_force(s: str) -> int:
    n = len(s)
    count = 0
    for i in range(n):
        for j in range(i, n):
            sub = s[i:j + 1]
            if sub == sub[::-1]:
                count += 1
    return count


def count_dp_table(s: str) -> int:
    n = len(s)
    dp = [[False] * n for _ in range(n)]
    count = 0
    for i in range(n):
        dp[i][i] = True
        count += 1
    for length in range(2, n + 1):
        for i in range(0, n - length + 1):
            j = i + length - 1
            if s[i] == s[j] and (length == 2 or dp[i + 1][j - 1]):
                dp[i][j] = True
                count += 1
    return count


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ("abc", 3),
        ("aaa", 6),
        ("a", 1),
        ("aa", 3),
        ("racecar", 10),
        ("abba", 6),
    ]
    for s, want in cases:
        got = sol.countSubstrings(s)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r}  -> {got}  (want {want})")
        assert count_dp_table(s) == want
        assert count_brute_force(s) == want

    print()
    print("RUNTIME DEMO -- brute force O(n^3) vs expand-around-center O(n^2)")
    print("-" * 72)
    import random
    random.seed(0)
    for n in (50, 150, 400):
        s = "".join(random.choice("ab") for _ in range(n))
        t0 = time.perf_counter()
        count_brute_force(s)
        brute_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        sol.countSubstrings(s)
        fast_ms = (time.perf_counter() - t0) * 1000

        print(f"n={n:4d}  brute={brute_ms:9.3f} ms   expand_center={fast_ms:7.3f} ms   "
              f"ratio={brute_ms / max(fast_ms, 1e-6):7.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
