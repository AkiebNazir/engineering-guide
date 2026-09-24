"""
================================================================================
SOLUTION · LeetCode 241 · Different Ways to Add Parentheses         [Medium]
https://leetcode.com/problems/different-ways-to-add-parentheses/
================================================================================

THE CORE IDEA
--------------
For any (sub)expression, consider every operator character as the LAST
operation applied. Splitting at operator position i gives a left slice
and a right slice; recursively compute ALL possible values of each slice,
then combine every (left_value, right_value) pair with that operator to
produce candidate results for the whole (sub)expression. Union the results
from every possible split point. Base case: a slice with no operators is
just a number, with exactly one possible value -- itself.

The recursion overlaps across DIFFERENT top-level splits: e.g. computing
"2*3-4*5" tries a split at '-' (left="2*3", right="4*5") AND a split at
the first '*' (left="2", right="3-4*5") AND a split at the second '*'
(left="2*3-4", right="5") -- and the SAME substring can recur nested
inside more than one of these (most visibly when the expression has
repeated structure, e.g. "1+1+1+1"). Memoize by the substring itself (a
dict from string -> list of possible values) so each distinct substring's
full result list is computed exactly once.

THIS IS DIVIDE & CONQUER WITH MEMOIZATION, NOT DP-1D/2D (contrast with
topics 16/17): DP's `dp[i]` or `dp[i][j]` state is a FIXED INDEX (or index
pair) into the ORIGINAL array, and the recursion's job is to decide how
far back to look among already-solved SMALLER indices. Here the state is
"which slice of the expression" (a start/end pair, or equivalently the
substring text), and the recursion's job is to decide WHERE TO SPLIT the
current slice -- the split point is chosen from scratch at every level,
not looked up from a table of smaller sub-indices in a fixed direction.
Both approaches exploit "the same subproblem gets asked for more than
once," but the AXIS along which subproblems overlap differs: DP overlaps
along array position; this problem overlaps along expression substring.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion, no memo, price it): implement exactly the
above recursive split-and-combine with no caching. Correct, but the same
substring computed by different top-level splits gets fully re-derived
from scratch every time it recurs -- for expressions with repeated
structure (e.g. "1+1+1+1+1+1+1+1"), this blows up badly. See the runtime
demo below for the measured slowdown.

Approach 1 (chosen) -- same recursion, memoized by substring (a plain
dict from the exact substring text to its list of possible results). Each
distinct substring's full result list is computed exactly once, however
many different splits ask for it.


================================================================================
STEP BY STEP TRACE
================================================================================
expression = "2-1-1"

Operators at positions 1 ('-') and 3 ('-').

Split at position 1: left="2", right="1-1"
    left results: [2]           (no operators, base case)
    right="1-1" recurses:
        split at its only '-' (position 1 of "1-1"): left="1", right="1"
        left results: [1], right results: [1]
        combine with '-': 1 - 1 = 0
        right results overall: [0]
    combine left(2) with right([0]) using '-': 2 - 0 = 2

Split at position 3: left="2-1", right="1"
    left="2-1" recurses:
        split at its '-': left="2", right="1" -> combine: 2 - 1 = 1
        left results overall: [1]
    right results: [1]           (base case)
    combine left([1]) with right(1) using '-': 1 - 1 = 0

Union of results from both splits: {2, 0} -> [0, 2]  (matches expected)

Memoization payoff: if "2-1-1" appeared as a substring in multiple places
in a LARGER expression (it can't literally recur inside itself here, but
"1-1" DOES get asked for only once even though nothing here required it
twice -- the payoff is most visible on expressions with real repeated
structure, e.g. "1+1+1+1", which the runtime demo below uses).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time                          Space   Mutates input?
    ------------------------  ----------------------------  ------  --------------
    Naive recursion, no memo   grows explosively on repeated  O(depth) n/a (string
                               structure -- see measured demo         input, never
                               below                                  mutated)
    Memoized by substring      bounded by # distinct           O(#distinct
    [chosen]                   substrings x results each       substrings x results)


================================================================================
EDGE CASES
================================================================================
    expression is a single number, no operators -> base case returns
                              [int(expression)] immediately, no recursion.
    expression has operators but they're all the same (e.g. "1+1+1+1") ->
                              exactly the case that makes memoization's
                              payoff visible: many splits ask for the SAME
                              substring's result list.
    leading/embedded multi-digit numbers (values up to 99 per constraints)
                            -> the recursion must parse full multi-digit
                              runs as one number in the base case, not
                              split on digit boundaries.
    subtraction is NOT commutative -> combining left/right values with '-'
                              must be `l - r`, never `r - l`; a transposed
                              combine silently produces the wrong answer
                              set (LC's own example 2 catches this bug).


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the base case entirely, or checking "no operators" with a
   regex/loop that misses that the ENTIRE remaining slice might be a
   multi-digit number, not a single digit.
2. Memoizing by (start, end) INDEX pair into the original string is
   equally correct and often more memory-efficient than memoizing by the
   substring TEXT itself -- but if you memoize by text, remember two
   DIFFERENT (start, end) slices with identical text (e.g. two separate
   "1+1" occurrences at different positions) legitimately share one cache
   entry, which is correct, not a bug -- don't "fix" this into per-position
   memoization unless space is the actual constraint.
3. Combining every left/right pair with only ONE operator type instead of
   re-reading which operator character was actually at the split
   position -- especially easy to get wrong if the split loop's index
   bookkeeping is off by one relative to where the operator character
   actually sits in the string.
4. Assuming this generalizes to DP with a fixed dp[i][j] table sized by
   string length -- it can be reframed that way (interval DP), but doing
   so obscures the "choose where to split" recursion that makes this
   problem's teaching point clear; memoized top-down recursion is the
   natural fit here, not a fixed 2D table filled bottom-up.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What's the actual complexity?" -> bounded by the nth Catalan number in
  the number of operators for the WORST case (all substrings distinct,
  memoization buys nothing) -- exponential in operator count regardless,
  but memoization strictly helps whenever substrings repeat, and never
  hurts.
- "Could you solve this with a fixed 2D dp table instead?" -> yes --
  interval DP, `dp[i][j]` = list of results for the operator-token slice
  [i, j]; it's mechanically similar but framed around ARRAY indices into a
  tokenized expression rather than raw substrings, which is a valid
  alternative representation once you've split the expression into tokens.
- "How would you extend this to parentheses or division in the input?"
  -> parentheses would need to be respected as hard split boundaries
  (or pre-resolved before recursing); division introduces a `right == 0`
  guard the current operators don't need.


================================================================================
RELATED PROBLEMS
================================================================================
- Unique Binary Search Trees (LC 96) -- same Catalan-number recursive
  structure (choose a "root" split point), classic interval D&C.
- Burst Balloons (LC 312) -- interval DP where dp[i][j] genuinely needs a
  fixed 2D array table, the point where this technique crosses into
  topic 17's territory.
- 16_dp_1d / 17_dp_2d topic guides -- contrast this substring-keyed
  memoization against array-indexed DP state directly.
================================================================================
"""

import time


class Solution:
    def diffWaysToCompute(self, expression: str) -> list[int]:
        memo: dict[str, list[int]] = {}
        return self._solve(expression, memo)

    def _solve(self, expr: str, memo: dict[str, list[int]]) -> list[int]:
        if expr in memo:
            return memo[expr]

        if expr.lstrip("-").isdigit():
            # entire slice is a single (possibly negative in principle,
            # though inputs here are non-negative per constraints) number
            result = [int(expr)]
            memo[expr] = result
            return result

        results = []
        for i, ch in enumerate(expr):
            if ch in "+-*":
                left_vals = self._solve(expr[:i], memo)
                right_vals = self._solve(expr[i + 1:], memo)
                for lv in left_vals:
                    for rv in right_vals:
                        if ch == "+":
                            results.append(lv + rv)
                        elif ch == "-":
                            results.append(lv - rv)
                        else:
                            results.append(lv * rv)

        memo[expr] = results
        return results


def diff_ways_naive(expr: str) -> list[int]:
    """No memoization -- re-derives every recurring substring from scratch."""
    if expr.lstrip("-").isdigit():
        return [int(expr)]

    results = []
    for i, ch in enumerate(expr):
        if ch in "+-*":
            left_vals = diff_ways_naive(expr[:i])
            right_vals = diff_ways_naive(expr[i + 1:])
            for lv in left_vals:
                for rv in right_vals:
                    if ch == "+":
                        results.append(lv + rv)
                    elif ch == "-":
                        results.append(lv - rv)
                    else:
                        results.append(lv * rv)
    return results


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ("2-1-1", [0, 2]),
        ("2*3-4*5", [-34, -14, -10, -10, 10]),
        ("0", [0]),
        ("11", [11]),
    ]
    for expr, want in cases:
        got = sol.diffWaysToCompute(expr)
        ok = sorted(got) == sorted(want)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  diffWaysToCompute({expr!r}) "
              f"-> {sorted(got)}  (want {sorted(want)})")
        assert sorted(diff_ways_naive(expr)) == sorted(want)

    print()
    print("RUNTIME DEMO -- memoized vs naive recursion on repeated-structure "
          "expressions, measured live")
    print("-" * 72)
    for num_ops in (8, 10, 12):
        expr = "+".join(["1"] * (num_ops + 1))  # e.g. "1+1+1+...+1"

        t0 = time.perf_counter()
        naive_result = diff_ways_naive(expr)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        memo_result = sol.diffWaysToCompute(expr)
        memo_ms = (time.perf_counter() - t0) * 1000

        assert sorted(naive_result) == sorted(memo_result)
        ratio = naive_ms / max(memo_ms, 1e-6)
        print(f"ops={num_ops:2d}  naive={naive_ms:9.3f} ms   "
              f"memo={memo_ms:7.4f} ms   ratio={ratio:8.1f}x   "
              f"(#results={len(memo_result)})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
