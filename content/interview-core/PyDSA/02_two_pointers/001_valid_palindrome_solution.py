"""
================================================================================
SOLUTION · LeetCode 125 · Valid Palindrome                               [Easy]
https://leetcode.com/problems/valid-palindrome/
================================================================================

THE CORE IDEA
-------------
Do not build a cleaned string. Walk the ORIGINAL string from both ends and skip
the junk as you meet it.

    l = 0, r = len(s) - 1
    while l < r:
        skip s[l] forward  while it is not alphanumeric
        skip s[r] backward while it is not alphanumeric
        if s[l].lower() != s[r].lower(): return False
        l += 1; r -= 1
    return True

    "A man, a plan, a canal: Panama"
     ↑                            ↑
     l                            r      'A' vs 'a'  -> match, move both
        ↑                       ↑
        l                       r        ' ' is junk -> l skips to 'm'
                                         'm' vs 'm'  -> match ...

Every character is visited at most once by exactly one pointer, so the total
work is O(n) even though there are two nested-looking `while`s. No allocation
happens at all — that is the O(1) space the problem is really asking for.

THE PATTERN: CONVERGING TWO POINTERS. The general form is "compare the two
ends, then discard at least one of them." Here both ends are discarded on a
match, which is the simplest possible instance — which makes this the right
problem to learn the mechanics on before 3Sum and Trapping Rain Water, where
the *elimination argument* gets genuinely subtle.


================================================================================
APPROACH 1 · Clean, then reverse ✅ (say this first — it is not wrong)
================================================================================
    cleaned = "".join(c.lower() for c in s if c.isalnum())
    return cleaned == cleaned[::-1]

    Time:  O(n)      Space: O(n)

Two lines, obviously correct, and genuinely FAST — `str.join` and slice-reversal
are C loops, so this often beats the "optimal" pointer version in CPython (the
benchmark at the bottom measures it).

Lead with it. Then say: *"this allocates two extra strings; if space matters I
can do it in place with two pointers."* That sentence is the whole interview.

⚠️  `cleaned == cleaned[::-1]` compares the full string. You could instead
    compare only the first half — `cleaned[:n//2] == cleaned[:(n+1)//2-1:-1]` —
    but it is unreadable and saves nothing asymptotically. Don't.


================================================================================
APPROACH 2 · Two pointers in place ✅✅ (the O(1)-space answer)
================================================================================

    l, r = 0, len(s) - 1
    while l < r:
        while l < r and not s[l].isalnum():
            l += 1
        while l < r and not s[r].isalnum():
            r -= 1
        if s[l].lower() != s[r].lower():
            return False
        l += 1
        r -= 1
    return True

    Time:  O(n)      Space: O(1)

STEP BY STEP for s = "A man, a plan, a canal: Panama":

    index:  0         1         2 ...
            A  ' '  m  a  n  ,  ' '  a ...                    ... P a n a m a
            ↑                                                             ↑
            l                                                             r

    l   r    s[l]  s[r]   action
    --  ---  ----  -----  --------------------------------------------------
     0   29  'A'   'a'    both alnum, 'a' == 'a'          -> match, l=1  r=28
     1   28  ' '   'm'    s[l] junk                       -> l=2
     2   27  'm'   'm'    match                           -> l=3  r=26
     3   26  'a'   'a'    match                           -> l=4  r=25
     4   25  'n'   'n'    match                           -> l=5  r=24
     5   24  ','   'a'    s[l] junk                       -> l=6
     6   24  ' '   'a'    s[l] junk                       -> l=7
     7   24  'a'   'a'    match                           -> l=8  r=23
    ...
    pointers cross -> True                                                ✓

AND A FAILING CASE, s = "race a car":

    l   r    s[l]  s[r]   action
    --  ---  ----  -----  -----------------------------
     0    9  'r'   'r'    match          -> l=1  r=8
     1    8  'a'   'a'    match          -> l=2  r=7
     2    7  'c'   'c'    match          -> l=3  r=6
     3    6  'e'   ' '    s[r] junk      -> r=5
     3    5  'e'   'a'    'e' != 'a'     -> return False       ✓

⚠️  `l < r` INSIDE EVERY INNER LOOP — THIS IS THE BUG THAT DEFINES THIS PROBLEM
    Consider s = ".,;:!" — no alphanumeric characters at all.

        while not s[l].isalnum(): l += 1        # ✗ no bound

    l runs 0,1,2,3,4,5 and then `s[5]` raises IndexError.

    Now flip which skip loop you write first:

        while not s[r].isalnum(): r -= 1        # ✗ no bound, and runs FIRST

    r goes 4,3,2,1,0 and then to -1 — and `s[-1]` DOES NOT RAISE. Python
    silently hands back the LAST character, so the pointer wraps around and
    re-scans the entire string from the end:

        visits: 4, 3, 2, 1, 0, -1, -2, -3, -4, -5, then IndexError at -6

    So it does still crash on this input, but only after doing a second full
    pass over data it already rejected. The crash is DEFERRED and the stack
    trace points at an index of -6, which tells you nothing about the real
    cause.

    ⚠️  The honest summary, since it is easy to overstate this:
        left skip first  -> IndexError immediately at index n
        right skip first -> wraps through negative indices, re-scans, then
                            IndexError at -(n+1)

    Both crash HERE, because every wrapped character is also junk. The reason
    to care is that `s[-1]` not raising is a general hazard: in any variant
    where a wrapped index lands on a character that PASSES your skip test, the
    loop stops and you compare the wrong characters — no exception, wrong
    answer. Do not rely on Python throwing to find this bug for you.

    Both inner loops need `l < r and ...`. The tests below run both orderings
    side by side.

⚠️  WHY `while l < r` AND NOT `l <= r`
    When l == r you are looking at a single middle character. A character always
    equals itself, so comparing it is a guaranteed no-op. `l < r` skips it.
    Using `l <= r` is not WRONG here — it just does one pointless comparison.
    (In binary search the same choice IS load-bearing; know the difference.)

⚠️  CALL `.lower()` ON THE CHARACTERS, NOT THE STRING
    `s = s.lower()` up front allocates a whole new string — O(n) space, which
    is exactly what you were avoiding. Lowercasing two characters per iteration
    is O(1) space. (It is also slightly slower in wall-clock; see the
    benchmark. The point is the space, not the speed.)


================================================================================
APPROACH 3 · Two pointers with a normalising generator
================================================================================
    import itertools
    fwd = (c.lower() for c in s if c.isalnum())
    rev = (c.lower() for c in reversed(s) if c.isalnum())
    return all(a == b for a, b in zip(fwd, rev))

Lazy, allocates nothing beyond the generators, and reads nicely. Two caveats:
  - It does 2n character visits instead of n (each generator walks the whole
    string), so it is ~2x the work of approach 2 despite the same O(n).
  - `zip` stops at the shorter generator — fine here since both yield the same
    count, but if you ever filter them differently, `zip` silently truncates.
    `itertools.zip_longest` is the safe version when counts might differ.

Worth showing as a "Python fluency" answer. Not the one to lead with.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time    Extra space   Mutates input?
    ----------------------  ------  ------------  --------------
    Clean + reverse     ✅  O(n)    O(n)          no (strings immutable)
    Two pointers      ✅✅  O(n)    O(1)          no
    Generator + zip         O(n)    O(1)          no
    Recursive on slices     O(n²)   O(n²)         no  ← never do this

    On the last row: `is_pal(s[1:-1])` allocates a fresh string at every level
    of recursion. n levels × O(n) copies = O(n²) time and allocation. It LOOKS
    like two pointers and is the opposite of it. See the topic guide, §2.1.


================================================================================
EDGE CASES
================================================================================
    ""            -> True
                     Empty string. `l = 0`, `r = -1`, so `l < r` is False and
                     the loop never runs. Correct with no special case — but
                     note r starts NEGATIVE here, which is fine only because
                     the loop guard catches it before any indexing happens.

    " "           -> True
                     One space. Cleans to "", which is a palindrome. This is
                     LeetCode's own example 3 and it catches code that returns
                     False for empty.

    ".,;:!"       -> True
                     ALL non-alphanumeric. This is the case that crashes or
                     infinite-loops an unguarded skip. The single most important
                     test on this problem.

    "a"           -> True
                     Single character. `l = 0, r = 0`, loop never entered.

    "0P"          -> False
                     THE ORD() TRAP. '0' is 0x30 and 'P' is 0x50 — they differ
                     by exactly 0x20, which is the same bit that separates
                     'p' (0x70) from 'P'. So a "lowercase by OR-ing 0x20"
                     shortcut maps 'P' -> 'p' AND '0' -> '0' | 0x20 = 0x10
                     (a control character), or with a naive `c | 32` compare,
                     makes '0' and 'P' collide. Use `.lower()`.

    "aba"         -> True   odd length; the middle 'b' is never compared
    "abba"        -> True   even length; pointers cross cleanly
    "12321"       -> True   DIGITS are alphanumeric and must be kept


================================================================================
COMMON MISTAKES
================================================================================
1. Omitting `l < r` from the inner skip loops. IndexError on the left side,
   silent wraparound via negative indexing on the right. Test with ".,;:!".

2. `s = s.lower()` before the loop — correct, but allocates O(n) and throws
   away the reason you chose two pointers.

3. Using `c.isalpha()` instead of `c.isalnum()`, so digits get discarded.
   "12321" then cleans to "" and every numeric palindrome returns True by
   accident.

4. Bitwise lowercasing (`ord(c) | 32`) instead of `.lower()`. Breaks on digits
   and punctuation — see the "0P" edge case.

5. Recursing on slices. O(n²) wearing a two-pointer costume.

6. Only advancing one pointer after a successful match. The loop still
   terminates but you compare misaligned characters and get wrong answers.

7. `while l <= r` combined with skip loops that can push l past r — you then
   compare a character with itself from the wrong side. `l < r` everywhere is
   simpler and always right here.

8. Forgetting that the problem's "empty is a palindrome" rule means you must
   NOT special-case the empty string to False.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Allow ONE character to be deleted (LC 680, Valid Palindrome II).
A: Same walk; on the first mismatch, try skipping the left OR the right
   character and test whether either remainder is a plain palindrome. That is
   two O(n) checks in the worst case, so still O(n) overall — not O(n²),
   because the branch happens at most once. This is problem 002 in this folder.

Q: Handle full Unicode, not just ASCII.
A: `.isalnum()` and `.lower()` are already Unicode-aware, so it mostly works.
   The traps: (a) `'ß'.upper()` is `'SS'` — case folding can change LENGTH, so
   use `.casefold()` rather than `.lower()` for real linguistic comparison;
   (b) combining characters mean "é" can be one code point or two, so
   normalise with `unicodedata.normalize('NFC', s)` first; (c) `'²'.isdigit()`
   is True. State (a) — it is the one that actually breaks the algorithm,
   because a two-pointer walk assumes one unit per position.

Q: The input is a linked list instead of a string.
A: You cannot index backwards. Either find the middle with fast/slow pointers
   and reverse the second half in place (O(1) space, mutates), or push
   everything to a stack/array (O(n) space). LC 234.

Q: The input is a stream you can only read once.
A: Impossible in O(1) space in general — you cannot know the end without
   reading it. You must buffer, or know the length up front.

Q: Longest palindromic SUBSTRING instead of a yes/no check?
A: Different problem entirely — expand-around-centre O(n²), or Manacher's
   O(n). LC 5. The two-pointer walk here does not extend to it.


================================================================================
RELATED PROBLEMS — the converging-pointer family
================================================================================
    LC 680  Valid Palindrome II      — allow one deletion; problem 002 here
    LC 234  Palindrome Linked List   — same idea, no random access
    LC 344  Reverse String           — the in-place swap version; note the
                                        input is List[str] because `str` is
                                        immutable
    LC 345  Reverse Vowels of a String — converging pointers with a skip
                                        condition; almost this exact code
    LC 5    Longest Palindromic Substring — expand around centre, NOT this
    LC 9    Palindrome Number        — same check without converting to a
                                        string (reverse half the digits)
    LC 167  Two Sum II               — converging pointers where the
                                        elimination argument is non-trivial
================================================================================
"""

import time


class Solution:
    def isPalindrome(self, s: str) -> bool:
        """Two pointers in place. Time O(n), space O(1). Input untouched."""
        l, r = 0, len(s) - 1
        while l < r:
            # `l < r` in BOTH inner guards: without it, l runs past the end and
            # r goes negative (which Python silently accepts — see the demo).
            while l < r and not s[l].isalnum():
                l += 1
            while l < r and not s[r].isalnum():
                r -= 1
            if s[l].lower() != s[r].lower():
                return False
            l += 1
            r -= 1
        return True

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def isPalindrome_clean(self, s: str) -> bool:
        """Build the cleaned string, compare with its reverse. O(n) space."""
        cleaned = "".join(c.lower() for c in s if c.isalnum())
        return cleaned == cleaned[::-1]

    def isPalindrome_generators(self, s: str) -> bool:
        """Lazy normalisation from both directions. O(1) space, 2n visits."""
        fwd = (c.lower() for c in s if c.isalnum())
        rev = (c.lower() for c in reversed(s) if c.isalnum())
        return all(a == b for a, b in zip(fwd, rev))

    def isPalindrome_unguarded(self, s: str) -> bool:
        """✗ BROKEN ON PURPOSE — no `l < r` bound, LEFT skip first."""
        l, r = 0, len(s) - 1
        while l < r:
            while not s[l].isalnum():          # no bound: runs past the end
                l += 1
            while not s[r].isalnum():
                r -= 1
            if s[l].lower() != s[r].lower():
                return False
            l += 1
            r -= 1
        return True

    def isPalindrome_unguarded_right_first(self, s: str) -> bool:
        """✗ BROKEN ON PURPOSE — no bound, RIGHT skip first.

        Ordering matters for WHICH failure you get. With the left skip first
        the left pointer runs off the end and raises IndexError before the
        right pointer can ever go negative. Flip the order and the right
        pointer reaches -1 first — where Python does NOT raise.
        """
        l, r = 0, len(s) - 1
        while l < r:
            while not s[r].isalnum():          # no bound: goes negative, wraps
                r -= 1
            while not s[l].isalnum():
                l += 1
            if s[l].lower() != s[r].lower():
                return False
            l += 1
            r -= 1
        return True


# ==============================================================================
# TESTS — run:  python 001_valid_palindrome_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ("A man, a plan, a canal: Panama", True),
        ("race a car", False),
        (" ", True),
        ("", True),
        (".,;:!", True),
        ("a", True),
        ("ab", False),
        ("aa", True),
        ("0P", False),
        ("aba", True),
        ("abba", True),
        ("1a2", False),
        ("12321", True),
        ("Ab,a", True),
        ("!@#a#@!", True),
        ("Madam, I'm Adam", True),
    ]
    impls = [
        ("two pointers", sol.isPalindrome),
        ("clean+revers", sol.isPalindrome_clean),
        ("generators  ", sol.isPalindrome_generators),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(fn(s) == exp for s, exp in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # ----------------------------------------------------------------------
    # Watch the pointers converge.
    # ----------------------------------------------------------------------
    print("\n--- pointer walk for 'Ab,a' ---")
    s = "Ab,a"
    l, r = 0, len(s) - 1
    print(f"  s = {s!r}")
    print(f"  {'l':>2} {'r':>2}  {'s[l]':>5} {'s[r]':>5}  action")
    while l < r:
        while l < r and not s[l].isalnum():
            print(f"  {l:>2} {r:>2}  {s[l]!r:>5} {s[r]!r:>5}  s[l] junk -> l+=1")
            l += 1
        while l < r and not s[r].isalnum():
            print(f"  {l:>2} {r:>2}  {s[l]!r:>5} {s[r]!r:>5}  s[r] junk -> r-=1")
            r -= 1
        if l >= r:
            break
        same = s[l].lower() == s[r].lower()
        print(f"  {l:>2} {r:>2}  {s[l]!r:>5} {s[r]!r:>5}  "
              f"{'match' if same else 'MISMATCH -> False'}")
        if not same:
            break
        l += 1
        r -= 1
    print(f"  result: {sol.isPalindrome(s)}")

    # ----------------------------------------------------------------------
    # ⚠️  The unguarded skip loop — two different failure modes.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  inner skip loops without `l < r` ---")

    def outcome_of(fn, probe):
        try:
            return f"returned {fn(probe)}"
        except IndexError as e:
            return f"IndexError: {e}"

    print(f"  {'input':<10} {'correct':<9} {'unguarded, left-first':<32} "
          f"unguarded, right-first")
    for probe in (".,;:!", "!!a", "a!!", ".a.", "!"):
        print(f"  {probe!r:<10} {str(sol.isPalindrome(probe)):<9} "
              f"{outcome_of(sol.isPalindrome_unguarded, probe):<32} "
              f"{outcome_of(sol.isPalindrome_unguarded_right_first, probe)}")
    print("  Both orderings crash on the all-junk input — but not at the same")
    print("  place. Trace the right pointer on '.,;:!' with no bound:")
    probe = ".,;:!"
    r, visits = len(probe) - 1, []
    try:
        while not probe[r].isalnum():
            visits.append(r)
            r -= 1
            if len(visits) > 14:
                break
    except IndexError:
        visits.append("IndexError")
    print(f"    visits {visits}")
    print(f"    len(s) is {len(probe)}, so indices 0..-5 all resolve to real")
    print("    characters. It re-scans the whole string before finally dying at")
    print("    -6, and the traceback blames an index you never wrote.")
    print("  Here both happen to crash. The hazard is that s[-1] does NOT raise:")
    print("  if a wrapped index lands on a character that passes the skip test,")
    print("  the loop just stops and compares the WRONG pair — silently.")
    print("  Guard both loops and neither failure is reachable.")

    # ----------------------------------------------------------------------
    # ⚠️  Why the right-side bug is worse: s[-1] does not raise.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  Python's negative indexing hides the out-of-bounds ---")
    s = "abc"
    print(f"  s = {s!r}")
    for i in (2, 1, 0, -1, -2, -3):
        print(f"    s[{i:>2}] = {s[i]!r}"
              + ("   <- ran off the LEFT end, but no exception" if i < 0 else ""))
    print("  A left pointer running past the end raises IndexError immediately.")
    print("  A right pointer running below 0 wraps and returns WRONG ANSWERS.")
    print("  Silent is worse than loud. Guard both sides.")

    # ----------------------------------------------------------------------
    # ⚠️  The '0P' trap: bitwise lowercasing.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  why `.lower()` and not `ord(c) | 32` ---")
    print(f"  {'char':>5} {'ord':>5} {'hex':>6} {'| 32':>6} {'chr(|32)':>10} "
          f"{'.lower()':>10}")
    for c in "0P p A a":
        if c == " ":
            continue
        o = ord(c)
        print(f"  {c!r:>5} {o:>5} {hex(o):>6} {o | 32:>6} "
              f"{chr(o | 32)!r:>10} {c.lower()!r:>10}")
    print(f"  '0' | 32 = {ord('0') | 32} = {chr(ord('0') | 32)!r}  "
          f"and 'P' | 32 = {ord('P') | 32} = {chr(ord('P') | 32)!r}")
    print(f"  isPalindrome('0P') -> {sol.isPalindrome('0P')}   (correct: False)")
    naive = (ord("0") | 32) == (ord("P") | 32)
    print(f"  bitwise compare says they match? {naive}")
    print("  The 0x20 bit means 'lowercase' only for LETTERS. On digits and")
    print("  punctuation it means something else entirely.")

    # ----------------------------------------------------------------------
    # ⚠️  Recursion on slices is O(n^2) pretending to be two pointers.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the fake two-pointer: recursion on slices ---")

    def is_pal_slices(t: str) -> bool:
        if len(t) < 2:
            return True
        return t[0] == t[-1] and is_pal_slices(t[1:-1])

    # Timing at these sizes is noise-dominated (the recursion limit caps n at
    # ~2000), so count the CHARACTERS COPIED instead — that is deterministic
    # and it is the thing that is actually quadratic.
    def chars_copied(n: int) -> int:
        total, k = 0, n
        while k >= 2:
            k -= 2
            total += k                   # each level allocates a string of len k
        return total

    print(f"  {'n':>6} {'depth':>7} {'chars copied':>14} {'growth':>8}   two-ptr visits")
    prev = None
    for n in (400, 800, 1600):          # n/2 frames deep; 2000 blows the limit
        probe = "a" * n
        is_pal_slices(probe)             # confirm it still runs
        cc = chars_copied(n)
        growth = f"{cc / prev:5.2f}x" if prev else "    -  "
        prev = cc
        print(f"  {n:>6} {n // 2:>7} {cc:>14,} {growth:>8}   {n // 2:>13,}")
    print("  Doubling n QUADRUPLES the characters copied (~4.0x) while the")
    print("  two-pointer version just doubles its visits. That is O(n^2) vs")
    print("  O(n), measured without a stopwatch.")
    print()
    print("  ⚠️  It also runs out of STACK before it runs out of patience:")
    import sys as _sys
    print(f"     sys.getrecursionlimit() = {_sys.getrecursionlimit()}, and this")
    print(f"     strips 2 chars per level, so it dies around n = "
          f"{_sys.getrecursionlimit() * 2}.")
    try:
        is_pal_slices("a" * 4000)
        print("     n=4000 survived?! (should never print)")
    except RecursionError:
        print("     n=4000 -> RecursionError. The constraint allows n = 2*10^5,")
        print("     so this approach cannot solve the problem AT ALL — it is not")
        print("     merely slow. Python has no tail-call elimination.")

    # ----------------------------------------------------------------------
    # The honest benchmark.
    # ----------------------------------------------------------------------
    print("\n--- O(1) space vs O(n) space, at the constraint size ---")
    base = "A man, a plan, a canal: Panama"
    big = base * 6000                                  # ~180k chars
    print(f"  len = {len(big)}")
    for name, fn in (("two pointers", sol.isPalindrome),
                     ("clean+revers", sol.isPalindrome_clean),
                     ("generators  ", sol.isPalindrome_generators)):
        t0 = time.perf_counter()
        fn(big)
        print(f"  {name} {(time.perf_counter() - t0) * 1000:8.1f}ms")
    print("  'clean + reverse' usually WINS on wall clock: join and [::-1] are")
    print("  C loops, while the two-pointer version runs interpreted bytecode")
    print("  per character. It costs O(n) memory to do it.")
    print("  Lead with the two-liner, offer the pointer version for space, and")
    print("  be honest that the two-liner is faster in CPython. That trade —")
    print("  not a memorised 'optimal' — is the actual engineering answer.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
