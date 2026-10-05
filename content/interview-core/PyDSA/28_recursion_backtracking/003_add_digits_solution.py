"""
================================================================================
SOLUTION · LeetCode 258 · Add Digits                                      [Easy]
https://leetcode.com/problems/add-digits/
================================================================================

THE CORE IDEA
--------------
Two independent recursions stacked: `digitSum` peels digits off a single
number with `n % 10` / `n // 10` until one digit remains, and `addDigits`
re-applies `digitSum` to its own output until a single digit sticks. Naming
these as two separate functions with two separate base cases avoids the
single most common bug in this problem: writing one recursion that
accidentally conflates "peel a digit" with "repeat until single-digit."


================================================================================
MULTIPLE APPROACHES
================================================================================
1. TWO-LAYER RECURSION (inner digitSum + outer addDigits) — O(log num) time
   for one digitSum pass, and empirically very few outer applications
   (digit sums shrink fast: any number under 10^10 collapses to a single
   digit in at most 2 outer applications). The version taught here.
2. ITERATIVE TWIN — a `while num >= 10` loop computing the digit sum via
   a nested loop or `sum(int(c) for c in str(num))`. Same complexity, no
   recursion.
3. DIGITAL ROOT (O(1), the stated follow-up) —
   `0 if num == 0 else 1 + (num - 1) % 9`. This is a real number-theory
   fact (a number's repeated digit sum, i.e. its "digital root," always
   equals `1 + (n-1) mod 9` for n > 0) rather than a coincidence — proven
   below by exhaustively cross-checking against the recursive version for
   every num in a large range, not merely asserted.


================================================================================
STEP BY STEP TRACE — addDigits(38)
================================================================================
    call addDigits(38)          38 >= 10, need digitSum(38) first
      call digitSum(38)           38 >= 10 -> 38%10 + digitSum(3)
        call digitSum(3)            3 < 10 -> base case, return 3
      digitSum(38) = 8 + 3 = 11
    call addDigits(11)          11 >= 10, need digitSum(11)
      call digitSum(11)           11 >= 10 -> 11%10 + digitSum(1)
        call digitSum(1)            1 < 10 -> base case, return 1
      digitSum(11) = 1 + 1 = 2
    call addDigits(2)           2 < 10 -> base case, return 2

Result: 2. Two outer applications of addDigits, each triggering its own
independent digitSum recursion of depth equal to the digit count.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time         Space          Mutates input?  Note
    ------------------------------  -----------  -------------  ---------------  --------------------------------
    Two-layer recursion             O(log num)   O(log num)     no               few outer applications in practice
    Iterative twin                  O(log num)   O(1)           no               same logic, no call stack
    Digital root (O(1) formula)     O(1)         O(1)           no               proven, not just asserted, below


================================================================================
EDGE CASES
================================================================================
    num = 0    -> 0    the ONLY case the digital-root formula special-cases;
                        `1 + (0-1) % 9` would give a wrong answer if not
                        handled separately (Python's `%` on negative numbers
                        returns a non-negative result, so `(0-1) % 9 = 8`,
                        giving `1 + 8 = 9` — wrong; 0's digit sum is 0, not 9).
    num = 1..9 -> num  already single digit; `addDigits`'s base case must
                        fire with ZERO calls to `digitSum` at all.
    num = 10   -> 1    smallest case that actually exercises `digitSum`
                        (1 + 0 = 1) followed by one more addDigits base-case
                        check.
    num = 9    -> 9    a multiple of 9 that ISN'T 0 — the digital root of any
                        positive multiple of 9 is 9, never 0; this is exactly
                        why the formula needs `(num - 1) % 9 + 1` rather than
                        a plain `num % 9`.


================================================================================
COMMON MISTAKES
================================================================================
1. Writing a single function that does both jobs and getting the base case
   wrong — e.g. `if num < 10: return digitSum(num)` (still calls digitSum
   on an already-single-digit number, which is harmless here since
   digitSum(n) = n for n < 10, but reveals a conflated mental model that
   breaks on trickier two-layer recursions elsewhere in this folder).
2. `num % 9` instead of `1 + (num - 1) % 9` for the O(1) formula — fails for
   every positive multiple of 9 (returns 0 instead of 9).
3. Forgetting the `num == 0` special case in the O(1) formula — Python's
   `%` never returns negative, so this doesn't crash, it just silently
   returns the wrong (nonzero) answer for exactly one input.
4. Using `str(num)` and summing character-to-int conversions inside the
   RECURSIVE version (mixing string and arithmetic approaches) — works, but
   defeats the point of practicing `% 10` / `// 10` digit extraction, which
   recurs constantly elsewhere (topic 21, Palindrome Number; this folder's
   general "peel a digit" idiom).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do this in O(1) with no loop or recursion?
A: Yes: `0 if num == 0 else 1 + (num - 1) % 9` — the digital root formula,
   verified below by cross-checking every value 0..99999 against the
   recursive version.

Q: Why does the digital root formula work — what's the actual math?
A: Because `10 ≡ 1 (mod 9)`, every power of 10 is also `≡ 1 (mod 9)`, so a
   number's value mod 9 equals the sum of its digits mod 9 — the digit-sum
   operation preserves `mod 9` congruence. Repeating it converges to the
   unique digit in [1,9] congruent to num mod 9 (or 0 itself, the one
   exception).

Q: Does the outer `addDigits` recursion ever run more than a couple of
   times in practice?
A: For any realistic 32-bit int, at most 2 outer applications: one full
   digit sum brings any 10-digit number down to at most 2 digits, and one
   more brings 2 digits down to 1.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 21, 003 Happy Number       — another "repeatedly apply a digit
                                       transform until a fixed condition"
                                       problem, there using cycle detection
                                       instead of guaranteed convergence.
    Topic 21, 001 Palindrome Number  — the `% 10` / `// 10` digit-peeling
                                       idiom on its own.
    LC 191 Number of 1 Bits          — same peeling idiom, base 2 instead
                                       of base 10.
================================================================================
"""


class Solution:
    def addDigits(self, num: int) -> int:
        """Two-layer recursion: outer addDigits re-applies inner digitSum."""
        if num < 10:
            return num
        return self.addDigits(self._digit_sum(num))

    def _digit_sum(self, n: int) -> int:
        if n < 10:
            return n
        return n % 10 + self._digit_sum(n // 10)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def addDigits_iterative(self, num: int) -> int:
        """Iterative twin. O(log num) time, O(1) space."""
        while num >= 10:
            total = 0
            n = num
            while n > 0:
                total += n % 10
                n //= 10
            num = total
        return num

    def addDigits_digital_root(self, num: int) -> int:
        """O(1) closed form via the digital-root identity."""
        if num == 0:
            return 0
        return 1 + (num - 1) % 9


# ==============================================================================
# TESTS — run:  python 003_add_digits_solution.py
# ==============================================================================
CASES = [
    (0, 0), (1, 1), (9, 9), (10, 1), (38, 2), (12345, 6), (2**31 - 1, 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("two-layer recursion ", sol.addDigits),
        ("iterative twin      ", sol.addDigits_iterative),
        ("digital root O(1)   ", sol.addDigits_digital_root),
    ]

    for name, fn in impls:
        ok = all(fn(n) == expected for n, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- proving the O(1) digital-root formula against the recursive version ---")
    print("  (cross-checking every num in 0..99999, not just asserting the formula)")
    mismatches = [n for n in range(100000)
                  if sol.addDigits(n) != sol.addDigits_digital_root(n)]
    if mismatches:
        print(f"  FAIL — {len(mismatches)} mismatches, e.g. {mismatches[:5]}")
        all_ok = False
    else:
        print("  CONFIRMED: digital-root formula matches recursion on all 100,000 cases.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
