"""
================================================================================
SOLUTION · LeetCode 282 · Expression Add Operators                       [Hard]
https://leetcode.com/problems/expression-add-operators/
================================================================================

THE CORE IDEA
--------------
Backtrack left to right, at each position trying every possible next operand
length, and — for every operator except at the very first operand — trying
all three of '+', '-', '*'. To handle '*' correctly despite it binding
tighter than +/-, carry TWO pieces of state instead of one: `eval_so_far`
(the running total) and `prev` (the SIGNED value the previous operand
contributed to that total). A '*' step undoes `prev`'s old contribution,
recomputes it as `prev * new_operand`, and adds that back in — everything
else about the running total stays untouched.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. NAIVE "JUST TRACK eval_so_far" — tries to skip carrying `prev` and handle
   '*' by directly multiplying into the running total. Priced, not written:
   this is WRONG, not just slower — `1+2*3` would compute `(1+2)*3=9`
   instead of the correct `1+(2*3)=7`, because the running total already
   baked in the '+' before the '*' arrives. The undo/redo trick exists
   specifically to fix this.
2. BACKTRACKING WITH (eval_so_far, prev) STATE (the intended answer) —
   O(4^n) worst case, written below as the primary solution.


================================================================================
STEP BY STEP TRACE — num = "105", target = 5 (finding "10-5")
================================================================================
    backtrack(index=0, path="", eval=0, prev=0)      [sentinel start state]
      operand "1" (L=1): first operand, no operator yet
        -> recurse(index=1, path="1", eval=1, prev=1)
           operand "0" (L=1): try '+': eval=1+0=1, prev=0
             -> recurse(index=2, path="1+0", eval=1, prev=0)
                operand "5" (L=1): try '+': eval=1+0+5=6 != target, no match
                              try '-': eval=1+0-5=-4 != target
                              try '*': eval = eval-prev+prev*5 = 1-0+0=1, no match
           try '-': eval=1-0=1, prev=0  (same numbers, different path string "1-0")
             ... similarly no match at index=3
           try '*': eval = eval-prev+prev*0 = 1-1+1*0=0, prev=0
             -> recurse(index=2, path="1*0", eval=0, prev=0)
                operand "5": '+' -> eval=5, no; '-' -> eval=-5, no;
                             '*' -> eval=0-0+0*5=0, no
        operand "10" (L=2, num[1]!='0' as the SECOND digit here so "10" has
                     no leading-zero problem — the guard only blocks a
                     MULTI-digit chunk whose FIRST character is '0'):
        -> recurse(index=2, path="10", eval=10, prev=10)
           operand "5" (L=1): try '-': eval = 10 - 5 = 5 == target!
             -> path="10-5" recorded as an answer.
           try '+': eval=15, no.  try '*': eval=10-10+10*5=50, no.

Two answers found overall for target=5: "1*0+5" (from a different branch
not fully expanded above) and "10-5" — matching the expected output.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time    Space          Mutates input?  Note
    --------------------------------  ------  -------------  ---------------  --------------------------------
    Backtracking w/ eval+prev state   O(4^n)  O(n) per path  no               n <= 10 keeps this fast in practice
    Naive eval-only (no prev)         N/A     N/A            no               INCORRECT for '*', not just slow


================================================================================
EDGE CASES
================================================================================
    num = "00", target = 0     -> "00" as ONE two-digit operand is invalid
                                  (leading zero), but "0" then "0" as two
                                  separate single-digit operands is valid —
                                  exercises the leading-zero guard directly.
    Single character, e.g. "5" -> no operator possible at all; the only
                                  candidate expression is "5" itself, valid
                                  iff target == 5.
    Very large intermediate values -> e.g. "999999999" with all '*' chosen
                                  produces a value far outside int32 range;
                                  Python ints don't overflow, so this is
                                  purely a "does it match target" filter, not
                                  a correctness risk — but note LeetCode's
                                  real constraint bounds target to int32
                                  range specifically because other languages
                                  DO need to guard overflow here.
    No valid expression exists  -> the search must exhaust every branch and
                                  return an empty list, not raise or hang;
                                  exercised below with a target unreachable
                                  by any operator placement.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the leading-zero guard entirely — this generates "05", "00",
   "0105" etc. as if they were valid multi-digit operands, producing answers
   the problem explicitly disallows.
2. Applying the leading-zero guard to the FIRST operand only, not to every
   operand chosen throughout the recursion — the guard is a property of
   ANY chunk of digits being turned into an operand, checked fresh at every
   position, not a one-time check at the start.
3. Storing `prev` UNSIGNED (always positive) instead of signed — the
   undo/redo trick for '*' needs `prev` to already carry whatever sign the
   PRECEDING operator gave it (e.g. after a '-', `prev` must be negative),
   otherwise a `*` immediately following a `-` computes the wrong result.
4. Building the path string by re-scanning `num` at the end instead of
   incrementally appending the operator + chunk at each recursive step —
   works, but is needless extra string work repeated on every leaf; the
   incremental version (append once, pass down, no rebuild) is simpler and
   the natural fit for backtracking's append/recurse/undo shape.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why is a single running total not enough — walk me through a concrete
   failure?
A: For "1+2*3": tracking only `eval_so_far` gives eval=1 after "1+", then
   applying '*' directly to the running total gives (1+2)*3=9 wrong,
   erasing the fact that '+' and '*' have different precedence, whereas
   "correct" is 1+(2*3)=7. Carrying `prev` separately lets '*' operate on
   just the last operand, then re-fold that corrected value back into the
   running total — that's the `eval - prev + prev*val` formula.

Q: How would you prune the search to avoid trying every operand length at
   every position when target is far out of reach?
A: A rough magnitude prune (comparing remaining digit count / max possible
   remaining contribution against how far `eval_so_far` still is from
   `target`) can cut branches early, but for n <= 10 this problem doesn't
   need it — brute-force backtracking already finishes fast enough,
   demonstrated below.

Q: What changes if the allowed operators also included, say, integer
   division?
A: Division reintroduces the SAME precedence problem as multiplication (it
   binds to the immediately preceding operand, not the running total), so
   it would fold into the same `prev`-based undo/redo mechanism — plus a new
   correctness question of what to do with non-integer or divide-by-zero
   results, which the current problem sidesteps entirely.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 224  Basic Calculator — evaluates a fixed +/-/*// expression with a
            similar precedence-aware running-state trick, no backtracking.
    LC 241  Different Ways to Add Parentheses — Topic 27's own divide &
            conquer problem: also explores every operator placement, but
            for COUNTING evaluations rather than generating strings.
    Topic 09 (this folder), 007-009 Combination Sum family — same
            "try every choice at this position, recurse, undo" backtracking
            shape without the arithmetic precedence wrinkle.
================================================================================
"""

from typing import List


class Solution:
    def addOperators(self, num: str, target: int) -> List[str]:
        """Backtracking with (eval_so_far, prev) state. O(4^n) worst case."""
        results: List[str] = []
        n = len(num)

        def backtrack(index: int, path: str, eval_so_far: int, prev: int) -> None:
            if index == n:
                if eval_so_far == target:
                    results.append(path)
                return
            for length in range(1, n - index + 1):
                chunk = num[index : index + length]
                if length > 1 and chunk[0] == "0":
                    break  # no valid longer operand starts with '0' either
                val = int(chunk)
                if index == 0:
                    backtrack(length, chunk, val, val)
                    continue
                backtrack(index + length, path + "+" + chunk, eval_so_far + val, val)
                backtrack(index + length, path + "-" + chunk, eval_so_far - val, -val)
                backtrack(
                    index + length,
                    path + "*" + chunk,
                    eval_so_far - prev + prev * val,
                    prev * val,
                )

        backtrack(0, "", 0, 0)
        return results


# ==============================================================================
# TESTS — run:  python 024_expression_add_operators_solution.py
# ==============================================================================
CASES = [
    ("123", 6, {"1*2*3", "1+2+3"}),
    ("232", 8, {"2*3+2", "2+3*2"}),
    ("105", 5, {"1*0+5", "10-5"}),
    ("00", 0, {"0+0", "0-0", "0*0"}),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    for num, target, expected in CASES:
        got = set(sol.addOperators(num, target))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  addOperators({num!r}, {target}) -> {sorted(got)}  (want {sorted(expected)})")

    # ----------------------------------------------------------------------
    # Every generated expression is independently RE-EVALUATED with Python's
    # own eval() (safe here: input is only digits and +-* by construction) to
    # prove the string actually equals target, not merely that it "looks
    # right."
    # ----------------------------------------------------------------------
    print("\n--- independently re-evaluating every generated expression ---")
    for num, target, _ in CASES:
        exprs = sol.addOperators(num, target)
        all_match = all(eval(e) == target for e in exprs)  # noqa: S307 - trusted digit/op-only strings
        all_ok &= all_match
        print(f"  {'PASS' if all_match else 'FAIL'}  all {len(exprs)} expressions for "
              f"({num!r}, {target}) evaluate to {target} via eval().")

    # ----------------------------------------------------------------------
    # No-solution case: must terminate and return an empty list, not hang.
    # ----------------------------------------------------------------------
    print("\n--- unreachable target: must return [] cleanly ---")
    num, target = "9", 100  # single digit "9" can never reach 100
    got = sol.addOperators(num, target)
    ok = got == []
    all_ok &= ok
    print(f"  {'PASS' if ok else 'FAIL'}  addOperators({num!r}, {target}) -> {got}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
