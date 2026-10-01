"""
================================================================================
SOLUTION · LeetCode 344 · Reverse String                                  [Easy]
https://leetcode.com/problems/reverse-string/
================================================================================

THE CORE IDEA
--------------
Two pointers, `lo` and `hi`, start at opposite ends of the array and swap
inward. The recursive call is the SAME idea as a `while` loop's next
iteration: "swap once, then hand off a strictly smaller range." Progress is
measured by the RANGE shrinking (both pointers moving inward by one), not by
transforming a value — the first index-range recursion in this folder.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, TWO-POINTER INDEX RANGE — swap `s[lo], s[hi]`, recurse on
   `(lo+1, hi-1)`. O(n) time, O(n) space (call stack, one frame per swap).
   Priced as unsafe for the stated constraint (n up to 10^5): recursion
   depth is n//2, blowing Python's default recursion limit — demonstrated
   live below with a real RecursionError.
2. ITERATIVE TWO-POINTER — identical logic, a `while lo < hi` loop instead
   of recursion. O(n) time, O(1) space. The correct answer for the stated
   constraints, and what to actually write in an interview.
3. PYTHONIC one-liner `s[:] = s[::-1]` — O(n) time, O(n) space for the
   reversed copy (violates the "O(1) extra space" requirement as stated,
   since slicing builds a new list, but worth naming as the non-recursive
   idiom).


================================================================================
STEP BY STEP TRACE — reverse(['h','e','l','l','o'], 0, 4)
================================================================================
    call reverse(lo=0, hi=4)   swap s[0],s[4] -> ['o','e','l','l','h']
      call reverse(lo=1, hi=3)   swap s[1],s[3] -> ['o','l','l','e','h']
        call reverse(lo=2, hi=2)   lo == hi -> base case, return (no swap)

Final array: ['o','l','l','e','h']. Three frames total for a 5-element array
(ceil(5/2) = 3 calls including the base case) — depth scales as n/2, not n.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time   Space         Mutates input?  Note
    -------------------------------  -----  ------------  ---------------  --------------------------------
    Recursive two-pointer            O(n)   O(n) stack    yes              overflows for n ~ 10^5
    Iterative two-pointer            O(n)   O(1)          yes              the intended answer
    s[:] = s[::-1]                   O(n)   O(n) new list yes (via slice)  simplest, but not O(1) extra space


================================================================================
EDGE CASES
================================================================================
    len(s) == 1     -> lo == hi immediately; base case fires with zero swaps.
    len(s) == 2     -> one swap, then lo > hi (pointers crossed, not equal) —
                       confirms the base case condition must be `lo >= hi`,
                       not `lo == hi`, or an even-length array's final call
                       would never terminate.
    len(s) == 10**5 -> upper constraint bound; this is exactly the case that
                       overflows the recursive version's call stack,
                       demonstrated below.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `if lo == hi: return` as the base case instead of `if lo >= hi:` —
   fails on even-length input, where the pointers CROSS (`lo > hi`) rather
   than land on the same index, causing an extra recursive call that swaps
   the same pair back or indexes out of bounds depending on how the range
   was built.
2. Returning a new list instead of mutating `s` in place — LeetCode (and
   the tests here) check the caller's original list object, so
   `return s[::-1]` without also writing back into `s` fails the in-place
   requirement even though the "answer" is arithmetically correct.
3. Recursing on the whole string by SLICING (`reverse(s[1:-1])`) instead of
   passing index bounds — this both breaks the in-place mutation (slicing a
   list creates a new one) and adds hidden O(n) copy cost per call, turning
   the whole algorithm into O(n^2).
4. Not noticing the stated O(n) constraint makes the plain recursive
   version unsafe in Python specifically (no TCO) — this would be a
   reasonable approach in a language with tail-call optimization.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why is the recursive version risky here specifically, when it wasn't for
   001 (which also recursed up to depth ~40 for num=10**6)?
A: 001's rule (halve-or-subtract) keeps depth at O(log num). Here, depth is
   O(n) — linear in input size — because each call only advances by one
   pair, no halving. For n up to 10^5, O(n) depth exceeds Python's default
   ~1000-frame limit; O(log n) depth never would.

Q: Can you reverse the string without any extra pointer state — e.g. purely
   from `s` and `s[1:]`?
A: Not in place — you'd need to build a new string/list (`reverse(s[1:]) +
   [s[0]]`), which is O(n) extra space per call for the slice, O(n^2) total
   space across all calls. The two-pointer index-range version is the
   in-place-compatible shape.

Q: What's the iterative equivalent and why would you actually write that?
A: A `while lo < hi: swap; lo += 1; hi -= 1` loop — same O(n) time, O(1)
   space, no recursion-limit risk. This is what ships in production code.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 008 Reverse Linked List II — same "reverse a range" idea, but
                                           on a linked list instead of an
                                           array (no random access, so the
                                           mechanics differ).
    Topic 02 Two Pointers                — the general index-range-closing-
                                           inward pattern, without the
                                           recursion angle.
    Topic 28, 023 Scramble String        — index-range recursion taken to
                                           its hardest form in this folder.
================================================================================
"""

import sys
from typing import List


class Solution:
    def reverseString(self, s: List[str]) -> None:
        """Recursive, two-pointer index range. O(n) time, O(n) stack."""
        self._reverse(s, 0, len(s) - 1)

    def _reverse(self, s: List[str], lo: int, hi: int) -> None:
        if lo >= hi:
            return
        s[lo], s[hi] = s[hi], s[lo]
        self._reverse(s, lo + 1, hi - 1)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def reverseString_iterative(self, s: List[str]) -> None:
        """Iterative two-pointer. O(n) time, O(1) space."""
        lo, hi = 0, len(s) - 1
        while lo < hi:
            s[lo], s[hi] = s[hi], s[lo]
            lo += 1
            hi -= 1

    def reverseString_slice(self, s: List[str]) -> None:
        """Pythonic slice reversal. O(n) time, O(n) space (not O(1))."""
        s[:] = s[::-1]


# ==============================================================================
# TESTS — run:  python 002_reverse_string_solution.py
# ==============================================================================
CASES = [
    (["h", "e", "l", "l", "o"], ["o", "l", "l", "e", "h"]),
    (["H", "a", "n", "n", "a", "h"], ["h", "a", "n", "n", "a", "H"]),
    (["a"], ["a"]),
    (["a", "b"], ["b", "a"]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive two-pointer", sol.reverseString),
        ("iterative two-pointer", sol.reverseString_iterative),
        ("slice reversal        ", sol.reverseString_slice),
    ]

    for name, fn in impls:
        ok = True
        for s, expected in CASES:
            working = list(s)
            fn(working)
            ok &= working == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- pushing recursion depth past the limit, measured live ---")
    limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() = {limit}")
    big_len = 2 * limit + 500  # guaranteed depth (big_len // 2) exceeds the limit
    big = list(range(big_len))
    try:
        sol.reverseString(big)
        print(f"  FAIL — expected RecursionError for len(s)={big_len}")
        all_ok = False
    except RecursionError:
        print(f"  CONFIRMED: recursive reverseString(len={big_len}) raised RecursionError.")
    # the iterative version handles the same size trivially
    big2 = list(range(big_len))
    sol.reverseString_iterative(big2)
    print(f"  Meanwhile the iterative version succeeds on the same len={big_len}, "
          f"O(1) space, no stack risk.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
