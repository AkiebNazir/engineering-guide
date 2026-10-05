"""
================================================================================
SOLUTION · LeetCode 12 · Integer to Roman                          [Medium]
https://leetcode.com/problems/integer-to-roman/
================================================================================

THE CORE IDEA
--------------
Instead of handling the six subtractive pairs (CM, CD, XC, XL, IX, IV) as
special cases bolted onto a digit-by-digit conversion, BAKE them directly
into one ordered value->symbol lookup table, interleaved at their correct
magnitude alongside the seven standard symbols:

    1000:M, 900:CM, 500:D, 400:CD, 100:C, 90:XC, 50:L, 40:XL,
    10:X, 9:IX, 5:V, 4:IV, 1:I

Then the whole algorithm is one greedy loop: for each (value, symbol) pair
in this table, from LARGEST to smallest, while `num >= value`, append
`symbol` and subtract `value` from `num`. No conditional branching on
"is this digit 4 or 9" anywhere -- the table already encodes every special
case, so the loop logic is identical for standard and subtractive entries.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (digit-by-digit with per-digit if/elif, price it): split num
into thousands/hundreds/tens/ones, and for EACH place value write an
explicit lookup or if/elif chain handling that place's own subtractive
quirks (e.g. hundreds-place: 900->"CM", 400->"CD", else count C's and
handle 500/100 combos). Correct, but this needs FOUR separate blocks of
special-case logic (one per place value) that all repeat the same
"figure out the subtractive representation for this digit" shape --
verbose and error-prone to keep in sync across four copies.

Approach 1 (chosen) -- single greedy pass over one flat ordered table
with all 13 (value, symbol) pairs, subtractive pairs included. O(1)
iterations in practice (at most ~13 table entries times a few repeats per
entry -- see complexity note below), and there is exactly ONE piece of
logic (the greedy subtract-while-loop), not four near-duplicate ones.


================================================================================
STEP BY STEP TRACE
================================================================================
num = 1994

    table (largest to smallest): [(1000,'M'), (900,'CM'), (500,'D'),
    (400,'CD'), (100,'C'), (90,'XC'), (50,'L'), (40,'XL'), (10,'X'),
    (9,'IX'), (5,'V'), (4,'IV'), (1,'I')]

    result = ""

    value=1000, symbol='M': 1994>=1000 -> append 'M', num=994
                             994>=1000? no, move to next value
    value=900, symbol='CM': 994>=900  -> append 'CM', num=94
                             94>=900? no, move on
    value=500..100 all > 94, skipped
    value=90, symbol='XC':  94>=90   -> append 'XC', num=4
                             4>=90? no, move on
    value=50,40,10,9,5 all > 4, skipped
    value=4, symbol='IV':   4>=4    -> append 'IV', num=0
                             0>=4? no, move on
    value=1, symbol='I':    0>=1? no, skip

    result = "M" + "CM" + "XC" + "IV" = "MCMXCIV"   -- matches example 3.


num = 58

    value=50, symbol='L': 58>=50 -> append 'L', num=8
                          8>=50? no
    value=40..10 all > 8, skipped
    value=9: 8>=9? no
    value=5, symbol='V': 8>=5 -> append 'V', num=3
                          3>=5? no
    value=4: 3>=4? no
    value=1, symbol='I': 3>=1 -> 'I', num=2
                          2>=1 -> 'I', num=1
                          1>=1 -> 'I', num=0

    result = "L" + "V" + "I"+"I"+"I" = "LVIII" -- matches example 2.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time     Space    Mutates input?
    --------------------------------------------------------------
    Digit-by-digit if/elif [priced]  O(1)*    O(1)      no
    Greedy flat table [chosen]       O(1)*    O(1)      no

    *Both are technically O(1) because `num <= 3999` is fixed by the
    problem's constraints -- more precisely, the greedy loop appends at
    most ~15 symbols total (bounded by the worst case, e.g. 3888 = MMMDCC-
    CLXXXVIII), so it's O(1) work for O(1) output length, independent of
    which specific num in range is given.


================================================================================
EDGE CASES
================================================================================
    num == 1                -> "I", exercises only the very last table
                             entry, smallest possible input.
    num == 3999 (largest)    -> "MMMDCCCXCIX", the longest possible output
                             (3 M's + DCCC + XC + IX = 3+4+2+2 = 11
                             symbols) -- exercises every magnitude tier at
                             once and repeated use of the same entry
                             (M three times).
    num that is EXACTLY a
    subtractive value, e.g.
    num == 900, 400, 90,
    40, 9, 4                -> must produce the two-symbol subtractive
                             form ("CM", "CD", "XC", "XL", "IX", "IV")
                             directly from a SINGLE table entry, not by
                             composing standard symbols and then noticing
                             a pattern.
    a value needing the SAME
    symbol 3x in a row, e.g.
    3000 -> "MMM", 300 ->
    "CCC", 30 -> "XXX",
    3 -> "III"               -> exercises the "while num >= value" repeat
                             within one table entry (never 4 in a row --
                             Roman numeral rules cap repetition at 3,
                             which is exactly why 4 and 9 have their own
                             subtractive symbol instead of "IIII"/"VIIII").
    no zero or negative
    input                    -> constraint guarantees `1 <= num <= 3999`;
                             Roman numerals have no symbol for zero or
                             negative values, so this is out of scope by
                             construction, not an edge case to defend
                             against.


================================================================================
COMMON MISTAKES
================================================================================
1. Writing separate if/elif blocks per place value (thousands, hundreds,
   tens, ones) instead of one flat table -- works, but quadruples the
   surface area for a subtle typo (e.g. swapping CD and XC between the
   hundreds and tens blocks) and makes the subtractive-pair logic look
   different in four places when it's actually the same rule every time.
2. Forgetting a subtractive entry in the table (e.g. omitting `(40,'XL')`)
   -- silently produces the wrong, non-canonical numeral for any num
   whose tens digit is 4 (e.g. 1940 would emit "MCMXXXX" instead of
   "MCMXL", four X's in a row which isn't valid Roman numeral form).
3. Ordering the table smallest-to-largest instead of largest-to-smallest
   -- greedy subtraction MUST proceed from the biggest usable value down,
   otherwise small values get consumed first and the larger-value symbols
   can never be reached correctly.
4. Using `if` instead of `while` for the repeat-check on each table entry
   -- would only ever emit each symbol once, failing every num that needs
   a symbol two or three times in a row (e.g. 3000 needing three M's).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "How would you write the reverse (Roman to Integer, LC 13)?" -> Scan
  left to right; if a symbol's value is LESS than the value of the symbol
  immediately after it, subtract it, otherwise add it -- the subtractive
  pattern falls out naturally from a single comparison, no lookup table
  of pairs needed in that direction.
- "What if the range were larger, e.g. up to 100,000 with an extended
  numeral system?" -> Roman numerals historically don't have a standard
  symbol beyond M (1000) at scale; a vinculum (overline, x1000 multiplier)
  extension exists but isn't part of this problem's scope -- worth naming
  that the fixed `1..3999` constraint IS the numeral system's natural
  range with the standard seven symbols.
- "Could you build the table programmatically instead of hardcoding all
  13 entries?" -> Yes, by generating it from the 7 base (value, symbol)
  pairs and deriving each subtractive entry as (10x-multiple's value minus
  the smaller unit's value, concatenated symbols) -- but hardcoding the
  13 fixed entries is simpler, equally correct, and avoids a fragile
  "derive the pairs algorithmically" step for a fixed, small, exhaustively
  known set.


================================================================================
RELATED PROBLEMS
================================================================================
- Roman to Integer (LC 13) -- the inverse direction, solved by a
  different (simpler) single left-to-right scan.
- Plus One (LC 66, this topic, 002) -- unrelated numeral system, but the
  same "greedy table-driven mapping beats special-casing" lesson recurs
  broadly across number-formatting problems.
================================================================================
"""

import time

_VALUE_SYMBOL_TABLE = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


class Solution:
    def intToRoman(self, num: int) -> str:
        parts = []
        for value, symbol in _VALUE_SYMBOL_TABLE:
            if num == 0:
                break
            count, num = divmod(num, value)
            if count:
                parts.append(symbol * count)
        return "".join(parts)


def _digit_by_digit(num: int) -> str:
    """Priced-not-shipped alternative: explicit if/elif per place value,
    kept only for the cross-check demo below."""
    thousands = num // 1000
    hundreds = (num % 1000) // 100
    tens = (num % 100) // 10
    ones = num % 10

    def place(digit: int, one: str, five: str, ten: str) -> str:
        if digit <= 3:
            return one * digit
        elif digit == 4:
            return one + five
        elif digit <= 8:
            return five + one * (digit - 5)
        else:
            return one + ten

    return (
        "M" * thousands
        + place(hundreds, "C", "D", "M")
        + place(tens, "X", "L", "C")
        + place(ones, "I", "V", "X")
    )


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        (3749, "MMMDCCXLIX"),
        (58, "LVIII"),
        (1994, "MCMXCIV"),
        (1, "I"),
        (3999, "MMMCMXCIX"),
        (4, "IV"),
        (9, "IX"),
        (40, "XL"),
        (90, "XC"),
        (400, "CD"),
        (900, "CM"),
        (3000, "MMM"),
        (444, "CDXLIV"),
    ]
    for num, expected in cases:
        got = sol.intToRoman(num)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  intToRoman({num}) -> {got!r} (expected {expected!r})")

    print()
    print("CROSS-CHECK -- greedy table vs digit-by-digit if/elif, num = 1..3999")
    print("-" * 72)
    mismatch = 0
    for num in range(1, 4000):
        a = sol.intToRoman(num)
        b = _digit_by_digit(num)
        if a != b:
            mismatch += 1
            if mismatch <= 3:
                print(f"  FAIL example: num={num} -> table={a!r}, digit-by-digit={b!r}")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {3999 - mismatch}/3999 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- greedy table vs digit-by-digit if/elif, measured live")
    print("-" * 72)
    n_calls = 2_000_000
    nums = [(i % 3999) + 1 for i in range(n_calls)]

    t0 = time.perf_counter()
    for num in nums:
        sol.intToRoman(num)
    table_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for num in nums:
        _digit_by_digit(num)
    digit_ms = (time.perf_counter() - t0) * 1000

    print(f"n={n_calls} calls over num=1..3999 cycling:")
    print(f"  greedy flat table:      {table_ms:8.2f} ms")
    print(f"  digit-by-digit if/elif: {digit_ms:8.2f} ms")
    if table_ms < digit_ms:
        print(f"  measured: the flat table is {digit_ms / table_ms:.2f}x faster here -- fewer "
              f"Python-level function calls (`place()` invoked 3x per call in the digit-by-digit "
              f"version) and a tight single loop over a short fixed list wins in CPython.")
    else:
        print(f"  measured: digit-by-digit is {table_ms / digit_ms:.2f}x faster here.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
