"""
================================================================================
SOLUTION · LeetCode 76 · Minimum Window Substring                         [Hard]
https://leetcode.com/problems/minimum-window-substring/
================================================================================

THE CORE IDEA
--------------
Variable sliding window with a need-counter and ONE integer, `missing`, that
says how many required characters the window still lacks. `missing` changes
only when a character's count crosses the need/surplus boundary, so "is the
window valid?" becomes `missing == 0`, an O(1) check. Expand right until
valid, then shrink left as far as possible while staying valid, recording the
shortest window each time.


================================================================================
APPROACH 1 · Brute force (priced, used only as an oracle)
================================================================================
For every start l, extend r until the window covers t, and keep the shortest.
With an incremental counter per start that's O(m^2); re-counting every
substring from scratch is O(m^3).

    Time: O(m^2) at best    Space: O(52)


================================================================================
APPROACH 2 · Sliding window comparing full count maps at each step
================================================================================
Same expand/shrink loop, but test validity with
`all(window[c] >= need[c] for c in need)` every time.

    Time: O(m * |distinct chars in t|) — up to 52 checks per step
    Space: O(52)

Correct and still linear in m, but the constant matters at m = 10^5. The
benchmark below measures the difference.


================================================================================
APPROACH 3 · Sliding window with a `missing` counter ✅ (the answer)
================================================================================
    need = Counter(t)
    missing = len(t)
    best_len, best_l = inf, 0
    l = 0
    for r, ch in enumerate(s):
        if need[ch] > 0:
            missing -= 1          # this copy was actually needed
        need[ch] -= 1             # may go negative: surplus copy
        while missing == 0:       # window [l..r] is valid
            if r - l + 1 < best_len:
                best_len, best_l = r - l + 1, l
            need[s[l]] += 1
            if need[s[l]] > 0:
                missing += 1      # removed a copy we needed
            l += 1
    return "" if best_len == inf else s[best_l:best_l + best_len]

WHY NEGATIVE COUNTS ARE THE TRICK. Characters not in t start at 0 and go
negative when added; adding them back never pushes them above 0, so they
never touch `missing`. Surplus copies of a needed character behave the same
way. Only the copies that move a count from 1 to 0 (or 0 to 1) matter.

WHY IT'S O(m). r moves m times. l only moves forward, so across the whole run
it also moves at most m times. Each move does O(1) work.

    Time: O(m + n)    Space: O(52)


================================================================================
STEP BY STEP TRACE · s = "ADOBECODEBANC", t = "ABC"
================================================================================
    need starts {A:1, B:1, C:1}, missing = 3

    r  ch  missing after add   window valid?   shrink steps
    -  --  -----------------   -------------   ---------------------------------
    0  A   2
    1  D   2
    2  O   2
    3  B   1
    4  E   1
    5  C   0                   yes [0..5]      record "ADOBEC" (6)
                                               drop A: need[A]=1 -> missing=1, l=1
    6  O   1
    7  D   1
    8  E   1
    9  B   1   (need[B] was 0 -> surplus, -1)
   10  A   0                   yes [1..10]     "DOBECODEBA" (10) not shorter
                                               drop D,O: still valid, l=3
                                               drop B: need[B]=0, still valid, l=4
                                               "ECODEBA" (7) not shorter
                                               drop E: l=5; drop C: need[C]=1 ->
                                               missing=1, l=6
   11  N   1
   12  C   0                   yes [6..12]     "ODEBANC" (7) not shorter
                                               drop O,D,E -> l=9 "BANC" (4) RECORD
                                               drop B: need[B]=1 -> missing=1, l=10

    answer: "BANC"


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                             Time              Space   Mutates input?
    -----------------------------------  ----------------  ------  --------------
    Brute force per start                O(m^2)            O(52)   No (strings immutable)
    Window + full-map check each step    O(m * 52)         O(52)   No
    Window + `missing` counter ✅        O(m + n)          O(52)   No


================================================================================
EDGE CASES
================================================================================
    len(t) > len(s)            Impossible; return "". The loop never reaches
                                missing == 0, so no special case is needed.
    t has duplicates ("aa")     Counter handles multiplicity. A set would not.
    t char absent from s        missing never hits 0 -> "".
    s == t                      Whole string.
    Case sensitivity            'A' and 'a' are different characters.
    Answer at the very end       Recorded inside the while before l moves.


================================================================================
COMMON MISTAKES
================================================================================
1. Treating t as a SET. "a" vs "aa" should be "" but a set-based check says
   "a". The demo below runs it.

2. Decrementing `missing` for every character in t, including surplus
   copies. Then missing goes below zero and validity checks break. Only
   decrement when need[ch] > 0 BEFORE the decrement.

3. Recording the window AFTER moving l. You record a window one character too
   short (and invalid).

4. Building the answer with `s[l:r+1]` inside the loop every time. That's an
   O(window) copy per record and can make the loop quadratic. Store
   (best_len, best_l) and slice once at the end.

5. Using `if missing == 0` instead of `while`. You shrink by one character per
   expansion and miss shorter windows.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the COUNT of minimal windows, or all of them?
A: Record every window whose length equals the running best; reset the list
   when a strictly shorter one appears.

Q: t is huge but has few distinct letters, s is huge?
A: Filter s first to (index, char) pairs whose char is in t, then slide over
   that shorter list. Same algorithm, fewer steps when most of s is noise.

Q: Characters are arbitrary Unicode, not letters?
A: Use a dict/Counter instead of a fixed 52-slot array. Complexity stays
   O(m + n) with O(distinct chars) space.

Q: s arrives as a stream?
A: The window algorithm is already streaming on the right edge, but shrinking
   needs s[l], so you must buffer the current window (a deque). Memory is
   O(current window), not O(m).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 3    Longest Substring Without Repeating Characters (005) — longest valid
    LC 567  Permutation in String (010)       — fixed-size window, exact counts
    LC 438  Find All Anagrams in a String (011)
    LC 209  Minimum Size Subarray Sum (008)   — shortest valid, numeric
    LC 632  Smallest Range Covering Elements from K Lists — same idea over k lists
================================================================================
"""

import random
import time
from collections import Counter


class Solution:
    def minWindow(self, s: str, t: str) -> str:
        need = Counter(t)
        missing = len(t)
        best_len, best_l = len(s) + 1, 0
        l = 0
        for r, ch in enumerate(s):
            if need[ch] > 0:
                missing -= 1
            need[ch] -= 1
            while missing == 0:
                if r - l + 1 < best_len:
                    best_len, best_l = r - l + 1, l
                left_ch = s[l]
                need[left_ch] += 1
                if need[left_ch] > 0:
                    missing += 1
                l += 1
        return "" if best_len > len(s) else s[best_l:best_l + best_len]


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
def min_window_brute(s: str, t: str) -> str:
    need = Counter(t)
    best = ""
    for l in range(len(s)):
        window = Counter()
        for r in range(l, len(s)):
            window[s[r]] += 1
            if all(window[c] >= k for c, k in need.items()):
                if not best or r - l + 1 < len(best):
                    best = s[l:r + 1]
                break
    return best


def min_window_full_check(s: str, t: str) -> str:
    """Approach 2: same window, but validity compares whole maps each step."""
    need = Counter(t)
    window = Counter()
    best_len, best_l = len(s) + 1, 0
    l = 0
    for r, ch in enumerate(s):
        window[ch] += 1
        while all(window[c] >= k for c, k in need.items()):
            if r - l + 1 < best_len:
                best_len, best_l = r - l + 1, l
            window[s[l]] -= 1
            l += 1
    return "" if best_len > len(s) else s[best_l:best_l + best_len]


def min_window_set_bug(s: str, t: str) -> str:
    """Mistake 1: needs each DISTINCT char once, ignoring duplicates in t."""
    need = set(t)
    window = Counter()
    best_len, best_l = len(s) + 1, 0
    l = 0
    for r, ch in enumerate(s):
        window[ch] += 1
        while all(window[c] >= 1 for c in need):
            if r - l + 1 < best_len:
                best_len, best_l = r - l + 1, l
            window[s[l]] -= 1
            l += 1
    return "" if best_len > len(s) else s[best_l:best_l + best_len]


# ==============================================================================
# TESTS — run:  python 014_minimum_window_substring_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: examples and edge cases ---")
    cases = [
        ("ADOBECODEBANC", "ABC", "BANC"),
        ("a", "a", "a"),
        ("a", "aa", ""),
        ("aa", "aa", "aa"),
        ("ab", "b", "b"),
        ("bba", "ab", "ba"),
        ("abc", "d", ""),
        ("aaflslflsldkalskaaa", "aaa", "aaa"),
    ]
    for s, t, want in cases:
        got = sol.minWindow(s, t)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r} t={t!r}  got={got!r}  want={want!r}")

    print("\n--- randomized cross-check vs brute force (500 inputs) ---")
    rng = random.Random(76)
    bad = 0
    for _ in range(500):
        s = "".join(rng.choice("abcA") for _ in range(rng.randint(1, 20)))
        t = "".join(rng.choice("abcA") for _ in range(rng.randint(1, 4)))
        a, b = sol.minWindow(s, t), min_window_brute(s, t)
        # Several windows can tie in random data; lengths must match and
        # ours must itself be valid.
        valid = (a == "" and b == "") or (len(a) == len(b) and not (Counter(t) - Counter(a)))
        if not valid:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  500 random inputs: same minimal length as brute force, window valid")

    print("\n--- mistake 1 LIVE: t treated as a set ---")
    wrong = min_window_set_bug("a", "aa")
    right = sol.minWindow("a", "aa")
    ok = wrong == "a" and right == ""
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  s='a', t='aa': set version returns {wrong!r}, counter version returns {right!r}")
    wrong2 = min_window_set_bug("baab", "abb")
    right2 = sol.minWindow("baab", "abb")
    ok = wrong2 != right2 and right2 == "baab"
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  s='baab', t='abb': set version returns {wrong2!r}, correct is {right2!r}")

    print("\n--- benchmark: full-map check vs `missing` counter, m = 100,000 ---")
    rng = random.Random(5)
    letters = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    s = "".join(rng.choice(letters) for _ in range(100_000))
    t = letters  # all 52 distinct letters -> full check costs up to 52 per step
    t0 = time.perf_counter(); a = min_window_full_check(s, t); tf = time.perf_counter() - t0
    t0 = time.perf_counter(); b = sol.minWindow(s, t); tm = time.perf_counter() - t0
    ok = len(a) == len(b)
    all_ok &= ok
    print(f"      full-map check {tf * 1000:8.1f} ms")
    print(f"      missing count  {tm * 1000:8.1f} ms   ({tf / tm:.1f}x faster, same window length {len(b)})")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
