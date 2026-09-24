"""
================================================================================
SOLUTION · LeetCode 8 · String to Integer (atoi)                    [Medium]
https://leetcode.com/problems/string-to-integer-atoi/
================================================================================

THE CORE IDEA
--------------
This problem has almost no algorithmic depth (no clever data structure, no
divide and conquer) -- it's a test of whether you can implement a careful,
linear, STATE-MACHINE-shaped parser without off-by-one errors or missed
edge cases, exactly like a hand-rolled lexer. There are exactly four
sequential phases, each of which either consumes zero or more characters
and then hands off to the next phase -- never backtracks:

    1. skip leading whitespace
    2. read an optional single sign character ('+' or '-')
    3. read as many consecutive digit characters as exist, accumulating a
       number left-to-right (`num = num * 10 + digit`)
    4. clamp the signed result into the 32-bit signed range
       `[-2^31, 2^31 - 1]`

Crucially, ANY character that doesn't fit the phase you're currently in
ends parsing immediately -- it does NOT restart, does NOT look further
ahead, and does NOT raise an error. `"4193 with words"` reads `4193` and
stops cold at the space; `"words and 987"` reads no digits at all
(whitespace/sign/digit phases all fail on `'w'`) and returns 0, even
though a valid-looking number appears later in the string. This
"parse-then-stop-immediately-on-failure" behavior is the single most
commonly mis-implemented detail.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (regex, priced, coded only for the cross-check demo below):
`re.match(r'\\s*([+-]?\\d+)', s)`, then clamp. O(n) time (regex engines
scan linearly here), O(n) space for the match object machinery. Compact,
but an interviewer asking THIS problem specifically wants to see you
implement the state machine by hand, not delegate it to a library --
using regex answers "can you use a tool" instead of "can you write a
parser," which is the actual thing being tested.

Approach 1 (chosen) -- manual four-phase linear scan: a single pass with
one index pointer, three small loops (skip whitespace, read one optional
sign, read digits), accumulating the number as you go and clamping at the
very end. O(n) time, O(1) extra space. This is the direct, correct,
expected answer.

Approach 2 (variant, same complexity, different style) -- explicit finite
state machine (formal DFA) with named states `{START, SIGNED, IN_NUMBER,
END}` and a transition table keyed by character class (whitespace / sign
/ digit / other). Functionally identical to Approach 1's control flow, but
structured as an explicit table -- some interviewers specifically ask for
this shape because it generalizes better to more complex tokenizers (e.g.
a JSON number parser). Not separately coded here since it's a strict
generalization of Approach 1's logic with identical output; the transition
table is described in FOLLOW-UPS.


================================================================================
STEP BY STEP TRACE
================================================================================
s = " -042"

    Phase 1 (skip whitespace): i=0 is ' ', skip -> i=1
    Phase 2 (sign): s[1] = '-' -> sign = -1, i=2
    Phase 3 (digits):
        i=2: '0' -> num = 0*10+0 = 0, i=3
        i=3: '4' -> num = 0*10+4 = 4, i=4
        i=4: '2' -> num = 4*10+2 = 42, i=5 (end of string)
    Phase 4 (apply sign, clamp): num = -1 * 42 = -42
        -2^31 <= -42 <= 2^31-1 -> no clamping needed
    Return -42.

s = "1337c0d3"

    Phase 1: no leading whitespace, i=0
    Phase 2: s[0]='1', not a sign character -> sign stays +1, i unchanged
    Phase 3 (digits):
        '1'->1, '3'->13, '3'->133, '7'->1337, then s[4]='c' is NOT a
        digit -> STOP immediately, i=4
    Phase 4: num = +1337, in range.
    Return 1337.  ("c0d3" is never looked at again -- parsing stopped the
    instant a non-digit appeared, it does not skip 'c' and resume at '0'.)

s = "words and 987" (no leading digits at all)

    Phase 1: no leading whitespace.
    Phase 2: s[0]='w' is not a sign -> sign stays +1, i unchanged (0).
    Phase 3 (digits): s[0]='w' is not a digit -> loop body never
        executes even once -> num stays 0.
    Phase 4: num = 0, in range.
    Return 0.   (The "987" later in the string is never reached because
    phase 3 already stopped at the very first character.)

s = "91283472332" (overflow)

    Digits accumulate to 91283472332, which is > 2^31 - 1 = 2147483647.
    Phase 4 clamps: return 2147483647.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                   Time    Space    Mutates input?
    -----------------------------------------------------------
    Regex [priced]             O(n)    O(n)*     no
    Manual 4-phase [chosen]    O(n)    O(1)      no
    Explicit DFA [variant]     O(n)    O(1)      no

    n = len(s). *Regex engines allocate match objects and internal
    backtracking state; for this simple a pattern it's effectively O(n)
    time but not O(1) space the way the hand-rolled scan is.


================================================================================
EDGE CASES
================================================================================
    empty string ""          -> no whitespace, no sign, no digits -> 0.
    only whitespace "   "    -> whitespace phase consumes everything,
                                 sign/digit phases see end-of-string -> 0.
    only a sign, no digits
    ("+", "-", "   +")       -> sign is read, but the digit phase finds
                                 nothing -> num stays 0 -> return 0 (the
                                 sign is discarded since 0 has no sign).
    double sign ("+-12",
    "--2")                   -> only ONE sign character is ever consumed;
                                 the second '+'/'-' is not a digit, so the
                                 digit phase reads zero digits -> 0. A
                                 common bug is looping to consume multiple
                                 sign characters, which is wrong per spec.
    leading zeros ("0032")   -> accumulate normally; `num*10+digit`
                                 naturally treats leading zeros as no-ops
                                 (0*10+0=0, 0*10+3=3, ...) with no special
                                 stripping code needed.
    overflow beyond int64
    even (huge digit strings,
    e.g. 40+ digit string)   -> Python ints never overflow mid-computation
                                 (unlike C/Java), so accumulate freely as
                                 an arbitrary-precision int and clamp ONLY
                                 at the very end -- no need for the
                                 "check-before-multiply" overflow guard a
                                 fixed-width language would require, but
                                 STILL must clamp because the exact
                                 accumulated value is being returned, not
                                 undefined-behavior wraparound.
    decimal point ("3.14")   -> digit phase reads "3", then stops at '.'
                                 (not a digit) -> returns 3, "14" is
                                 discarded entirely. `.` is never treated
                                 as part of a number in this problem
                                 despite appearing in the constraints'
                                 allowed character set.
    " -42kk" (whitespace,
    sign, digits, garbage)   -> full four-phase pipeline, returns -42,
                                 "kk" ignored.


================================================================================
COMMON MISTAKES
================================================================================
1. Allowing whitespace, a sign, AND more whitespace all to be skipped, or
   skipping whitespace AFTER the sign -- the spec allows leading whitespace
   ONLY before the sign, not between sign and digits ("- 42" is NOT valid,
   the digit phase sees a space and reads zero digits -> returns 0).
2. Consuming more than one sign character, or a sign after digits have
   already started ("12-3" should stop digit-reading at '-' and return 12,
   not treat it as a second number).
3. Forgetting to clamp AFTER applying the sign, or clamping the unsigned
   magnitude and then negating -- clamping must happen on the final signed
   value (`-91283472332` clamps to `-2147483648`, not to
   `-(clamp(91283472332))` which would coincidentally work here but is the
   wrong order of operations to reason about).
4. In a fixed-width language, multiplying by 10 and adding a digit BEFORE
   checking for overflow -- must check `num > (INT_MAX - digit) // 10`
   style bounds before the multiply, or use a wider intermediate type.
   Python sidesteps this since ints don't overflow, but it's the #1
   language-specific gotcha interviewers probe for on this problem.
5. Treating '.' as a valid part of the number (reading "3.14" as 3.14 or
   stopping incorrectly) -- the problem is explicitly integer-only; a '.'
   is just another "stop parsing" character, identical to a letter.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you formalize this as a finite state machine?" -> Yes: states
  `START -> (whitespace loops on START) -> SIGNED (on '+'/'-') ->
  IN_NUMBER (on digit) -> END (on anything else, from any state)`. A
  transition table `table[state][char_class]` looked up per character is
  the "textbook" structure this problem is often used to teach, even
  though the linear 3-loop version above computes the identical result.
- "What if input can be UTF-8 with full-width digits or locale-specific
  thousands separators (e.g. '1,234')?" -> Out of scope for LC 8, but in
  a real `atoi`/`strtol` you'd need locale-aware digit classification and
  explicit separator handling -- worth naming that this problem's digit
  test (`s[i].isdigit()` or `'0' <= s[i] <= '9'`) is deliberately narrow
  to ASCII 0-9.
- "Why does Python not need an overflow guard mid-parse the way C does?"
  -> Python `int` is arbitrary precision; the numeric accumulation itself
  can never overflow. The clamp is still required because the PROBLEM
  defines 32-bit signed semantics, not because Python's arithmetic would
  break without it.


================================================================================
RELATED PROBLEMS
================================================================================
- Valid Number (LC 65) -- a much stricter, full-grammar version of this
  same "parse a numeric token character by character" family, including
  decimals and exponents; same state-machine mindset, more states.
- Basic Calculator (LC 224/227) -- also a hand-rolled linear parser/state
  machine over a string, one level up in complexity (operators and
  precedence instead of just a single number token).
- Find the Index of the First Occurrence in a String (LC 28, this topic,
  001) -- unrelated algorithmically, but the same discipline of "one
  index pointer, never move it backwards, handle every character class
  explicitly" applies to both.
================================================================================
"""

import re
import time


class Solution:
    def myAtoi(self, s: str) -> int:
        INT_MIN, INT_MAX = -2 ** 31, 2 ** 31 - 1
        i, n = 0, len(s)

        # Phase 1: skip leading whitespace.
        while i < n and s[i] == ' ':
            i += 1

        # Phase 2: optional single sign character.
        sign = 1
        if i < n and s[i] in '+-':
            if s[i] == '-':
                sign = -1
            i += 1

        # Phase 3: consume consecutive digits.
        num = 0
        while i < n and s[i].isdigit():
            num = num * 10 + (ord(s[i]) - ord('0'))
            i += 1

        # Phase 4: apply sign, clamp to 32-bit signed range.
        num *= sign
        if num < INT_MIN:
            return INT_MIN
        if num > INT_MAX:
            return INT_MAX
        return num


_ATOI_RE = re.compile(r'\s*([+-]?\d+)')


def _regex_atoi(s: str) -> int:
    """Priced regex variant, used only for the cross-check demo below."""
    INT_MIN, INT_MAX = -2 ** 31, 2 ** 31 - 1
    m = _ATOI_RE.match(s)
    if not m:
        return 0
    num = int(m.group(1))
    return max(INT_MIN, min(INT_MAX, num))


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ("42", 42),
        (" -042", -42),
        ("1337c0d3", 1337),
        ("0-1", 0),
        ("words and 987", 0),
        ("", 0),
        ("   ", 0),
        ("+", 0),
        ("-", 0),
        ("+-12", 0),
        ("  +0 123", 0),
        ("91283472332", 2147483647),
        ("-91283472332", -2147483648),
        ("2147483648", 2147483647),   # exactly one over INT_MAX
        ("-2147483648", -2147483648),  # exactly INT_MIN
        ("3.14159", 3),
        ("  -42kk", -42),
        ("00000-42a1234", 0),         # digits "00000" read then '-' stops it
        ("9223372036854775808", 2147483647),  # bigger than 64-bit too
    ]
    for s, expected in cases:
        got = sol.myAtoi(s)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  myAtoi({s!r}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- manual parser vs regex parser, 3000 random inputs")
    print("-" * 72)
    import random
    random.seed(19)
    charset = "0123456789+- .abc"
    mismatch = 0
    for _ in range(3000):
        length = random.randint(0, 15)
        s = "".join(random.choice(charset) for _ in range(length))
        r1 = sol.myAtoi(s)
        r2 = _regex_atoi(s)
        if r1 != r2:
            mismatch += 1
            print(f"  MISMATCH on {s!r}: manual={r1} regex={r2}")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {3000 - mismatch}/3000 agree "
          f"({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- manual scan vs regex, 500k calls on a fixed input")
    print("-" * 72)
    sample = "   -0012345 residual text"
    n_calls = 500_000

    t0 = time.perf_counter()
    for _ in range(n_calls):
        sol.myAtoi(sample)
    manual_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(n_calls):
        _regex_atoi(sample)
    regex_ms = (time.perf_counter() - t0) * 1000

    print(f"{n_calls} calls on {sample!r}:")
    print(f"  manual 4-phase scan: {manual_ms:9.2f} ms")
    print(f"  regex:               {regex_ms:9.2f} ms")
    faster = "manual scan" if manual_ms < regex_ms else "regex"
    ratio = max(manual_ms, regex_ms) / max(min(manual_ms, regex_ms), 1e-6)
    print(f"  measured: {faster} is {ratio:.2f}x faster on this machine. "
          f"Either is O(n); this is a constant-factor observation, not a "
          f"complexity difference, and the manual scan remains the answer "
          f"the interview question is actually testing for.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
