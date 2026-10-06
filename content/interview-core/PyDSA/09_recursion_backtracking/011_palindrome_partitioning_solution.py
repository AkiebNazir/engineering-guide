"""
================================================================================
SOLUTION · LeetCode 131 · Palindrome Partitioning                       [Medium]
https://leetcode.com/problems/palindrome-partitioning/
================================================================================

THE CORE IDEA
--------------
This is a standard backtracking problem mapping exactly to the Combinations 
shape. The state is tracked by a `start` index pointing to the first character 
of the remaining unpartitioned string.

At any `start` index, we iterate through all possible `end` indices to form a 
prefix substring. If that prefix is a palindrome, it represents a valid "cut". 
We add it to our path and recursively ask the algorithm to partition the rest 
of the string starting from `end`.

================================================================================
STEP BY STEP TRACE — s = "aab"
================================================================================
    call backtrack(start=0, path=[])
      
      i = 1: sub = "a" (palindrome? YES)
        CHOOSE: path = ["a"]
        call backtrack(start=1)
          
          i = 2: sub = "a" (palindrome? YES)
            CHOOSE: path = ["a", "a"]
            call backtrack(start=2)
              
              i = 3: sub = "b" (palindrome? YES)
                CHOOSE: path = ["a", "a", "b"]
                call backtrack(start=3)
                  start == 3 (LEAF) -> record ["a", "a", "b"]
                UNCHOOSE: path = ["a", "a"]
            
            UNCHOOSE: path = ["a"]
            
          i = 3: sub = "ab" (palindrome? NO) -> PRUNE
          
        UNCHOOSE: path = []
        
      i = 2: sub = "aa" (palindrome? YES)
        CHOOSE: path = ["aa"]
        call backtrack(start=2)
          
          i = 3: sub = "b" (palindrome? YES)
            CHOOSE: path = ["aa", "b"]
            call backtrack(start=3)
              start == 3 (LEAF) -> record ["aa", "b"]
            UNCHOOSE: path = ["aa"]
            
        UNCHOOSE: path = []
        
      i = 3: sub = "aab" (palindrome? NO) -> PRUNE


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach               Time           Space          Mutates input?
    ---------------------  -------------  -------------  ---------------
    Backtracking           O(n * 2^n)     O(n)           no
    Backtracking w/ DP     O(n * 2^n)     O(n^2)         no

    WHERE O(n * 2^n) comes from: 
    The worst-case input is a string of identical characters (e.g., "aaaaa"). 
    In this case, every possible substring is a palindrome, meaning every 
    possible cut combination is valid. A string of length n has n-1 possible 
    cut points, leading to 2^(n-1) possible partitions. For each valid partition 
    (leaf node), we spend O(n) time copying the substrings into the result list.
    
    Space is O(n) for the recursion stack and the `path` list.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to slice strings properly. `s[start:end]` is exclusive of `end`.
   If your loop is `for end in range(start, len(s))`, your slice needs to be 
   `s[start:end+1]`.
2. Using a manual `while` loop to check for palindromes. While correct, 
   Python's slice notation `sub == sub[::-1]` pushes the loop into C and is 
   dramatically faster for these small constraint lengths (n <= 16).
3. Appending `path` instead of `path[:]` or `list(path)` at the base case, 
   resulting in a list of empty arrays.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would you optimize the palindrome checking if the string was very long?
A: You could use a 2D Dynamic Programming table where `dp[i][j]` is True if 
   `s[i...j]` is a palindrome. You populate this table bottom-up in O(n^2) 
   time before starting the backtracking. This changes the palindrome check 
   from O(n) string slicing to an O(1) array lookup. (Implemented below for 
   completeness, though unnecessary for n=16).
================================================================================
"""

from typing import List


class Solution:
    def partition(self, s: str) -> List[List[str]]:
        """
        Standard Backtracking approach.
        Uses Python's highly optimized string slicing for palindrome checks.
        """
        results = []
        path = []
        n = len(s)

        def backtrack(start: int):
            # Base case: we've partitioned the whole string
            if start == n:
                results.append(path[:])  # Crucial: copy the path!
                return

            # Explore all possible end points for the next substring
            for end in range(start + 1, n + 1):
                sub = s[start:end]
                # Prune if the prefix is not a palindrome
                if sub == sub[::-1]:
                    path.append(sub)        # 1. CHOOSE
                    backtrack(end)          # 2. EXPLORE
                    path.pop()              # 3. UNCHOOSE

        backtrack(0)
        return results

    def partition_with_dp(self, s: str) -> List[List[str]]:
        """
        Optimized Approach (Follow-up).
        Pre-computes palindromes using DP to make the check O(1).
        """
        n = len(s)
        # dp[i][j] will be True if s[i:j+1] is a palindrome
        dp = [[False] * n for _ in range(n)]
        
        for length in range(1, n + 1):
            for i in range(n - length + 1):
                j = i + length - 1
                if s[i] == s[j]:
                    # True if length is 1 or 2, OR inner string is a palindrome
                    if length <= 2 or dp[i + 1][j - 1]:
                        dp[i][j] = True

        results = []
        path = []

        def backtrack(start: int):
            if start == n:
                results.append(path[:])
                return

            for end in range(start, n):
                if dp[start][end]:
                    path.append(s[start:end + 1])
                    backtrack(end + 1)
                    path.pop()

        backtrack(0)
        return results


# ==============================================================================
# TESTS — run:  python 011_palindrome_partitioning_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ("aab", [["a", "a", "b"], ["aa", "b"]]),
        ("a", [["a"]]),
        ("cdd", [["c", "d", "d"], ["c", "dd"]]),
        ("aaaa", [
            ["a", "a", "a", "a"],
            ["a", "a", "aa"],
            ["a", "aa", "a"],
            ["a", "aaa"],
            ["aa", "a", "a"],
            ["aa", "aa"],
            ["aaa", "a"],
            ["aaaa"]
        ])
    ]

    impls = [
        ("Standard Backtracking", sol.partition),
        ("DP + Backtracking    ", sol.partition_with_dp),
    ]

    all_ok = True
    for name, fn in impls:
        passed = 0
        for s_input, expected in cases:
            got = fn(s_input)
            
            # Sort for order-agnostic comparison
            got_sorted = sorted([sorted(p) for p in got]) if got else []
            exp_sorted = sorted([sorted(p) for p in expected])
            
            ok = got_sorted == exp_sorted
            passed += ok
            if not ok:
                all_ok = False
                print(f"FAIL in {name} for s={s_input!r}")
                print(f"  Expected: {expected}")
                print(f"  Got:      {got}")
        print(f"{'PASS' if passed == len(cases) else 'FAIL'}  {name} ({passed}/{len(cases)} cases)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()