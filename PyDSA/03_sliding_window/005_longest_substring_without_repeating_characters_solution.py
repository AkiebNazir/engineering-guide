"""
================================================================================
SOLUTION · LeetCode 3 · Longest Substring Without Repeating Characters  [Medium]
https://leetcode.com/problems/longest-substring-without-repeating-characters/
================================================================================

THE CORE IDEA
-------------
Maintain a window `[l, r]` whose characters are all distinct. Expand `r` every
step; when the incoming character is already inside, shrink from the left until
it is not.

    window = set()
    l = best = 0
    for r, ch in enumerate(s):
        while ch in window:            # RESTORE the invariant
            window.remove(s[l]); l += 1
        window.add(ch)                 # ENTER
        best = max(best, r - l + 1)    # RECORD
    return best

O(n) time, O(min(n, Σ)) space.

This is the template every other variable window in this folder is a variation
of. Memorise the three-step body — **enter, restore, record** — and note that
here the restore happens *before* the enter, because the test is "would adding
this break the invariant?" Both orderings appear in the wild; what matters is
that when you RECORD, the window is valid.


================================================================================
WHY THE INNER `while` DOES NOT MAKE IT QUADRATIC
================================================================================
The loop looks like O(n) inside O(n). It is not, and the argument is
amortization, not case analysis:

        r increases n times over the whole run, then stops.
        l only ever increases, and l <= r <= n.
        => l also advances at most n times over the WHOLE run.
        Total pointer movement <= 2n, each step O(1)  =>  O(n).

The inner `while` may run 6 times on one iteration and 0 times on the next
fifty. You do not bound it per-iteration; you bound the total. Equivalently:
**every character enters the window exactly once and leaves at most once.**

The demo at the bottom counts the actual operations and confirms the total is
under 2n on every input shape, including the worst case ("aaaa...").


================================================================================
WHY SHRINKING FROM THE LEFT IS PROVABLY CORRECT
================================================================================
The property "all characters distinct" is HEREDITARY: every substring of a
distinct string is distinct. Its contrapositive is the licence for `l += 1`:

    If s[l..r] contains a duplicate, then s[l'..r] for every l' < l contains
    that same duplicate. A WIDER window can never repair a broken one.

So when the window breaks there is exactly one legal repair — move `l` right —
and every left endpoint you pass is permanently eliminated. No answer is lost,
`l` never needs to backtrack, and the pass stays linear.

This is the same shape of argument as the elimination step in converging two
pointers (topic 02) and the running minimum in problem 001. Whenever you claim
a pointer only moves one way, you owe this proof.


================================================================================
THE TWO IMPLEMENTATIONS
================================================================================

VERSION 1 · SET + STEP-BY-STEP SHRINK  (above)

    Simple, obviously correct, no index arithmetic. `l` creeps forward one
    character at a time. Prefer it when you are unsure — it is much harder to
    get wrong, and it is the same O(n).

VERSION 2 · LAST-INDEX MAP + JUMP

    last = {}                       # character -> index of its last occurrence
    l = best = 0
    for r, ch in enumerate(s):
        if ch in last and last[ch] >= l:
            l = last[ch] + 1        # JUMP the whole way past the old copy
        last[ch] = r
        best = max(best, r - l + 1)

    Instead of creeping, `l` teleports past the previous occurrence in one
    step. Fewer operations (no repeated set deletes), same O(n), and it is the
    version most people write from memory — which is precisely why it is the
    version most people get wrong.


================================================================================
⚠️  THE BUG IN VERSION 2 — the single most important thing on this page
================================================================================
The map `last` remembers EVERY character ever seen, including characters that
have already fallen out of the window. If you jump without checking, a stale
index drags `l` BACKWARDS:

    ✗  l = last[ch] + 1                        # no guard
    ✅ l = max(l, last[ch] + 1)                 # or: if last[ch] >= l: ...

Trace "abba":

    r=0 'a'  last={a:0}                   l=0   window "a"     len 1
    r=1 'b'  last={a:0, b:1}              l=0   window "ab"    len 2  <- best
    r=2 'b'  seen at 1, 1 >= l=0 -> l=2   l=2   window "b"     len 1
    r=3 'a'  seen at 0 ...
             ✗ unguarded: l = 0 + 1 = 1         window "bba"   len 3  WRONG
                          `l` moved from 2 BACK to 1, and "bba" has two b's.
             ✅ guarded:   l = max(2, 1) = 2     window "ba"    len 2  correct

The unguarded version returns 3 for "abba" — a window that is not even valid.
And it is worse than a wrong answer: moving `l` backwards destroys the
monotonicity that the O(n) proof depends on, so the complexity argument
collapses too.

"tmmzuxt" is the other classic (correct answer 5, "mzuxt"), and "dvdf" is the
third (correct answer 3, "vdf", not 2). The test suite runs all three against
both versions and prints the disagreement.

    THE RULE: `l` MUST BE MONOTONE NON-DECREASING. Any assignment to `l` that
    is not of the form `l = max(l, ...)` — or guarded by an equivalent test —
    is a bug waiting for the right input.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(s), Σ = alphabet size

    Approach                        Time        Space      Note
    ------------------------------  ----------  ---------  --------------------
    Every substring, re-check       O(n^3)      O(n)       n^2 substrings x O(n)
    Every start, extend with a set  O(n^2)      O(Σ)       the natural brute force
    Window + set ✅                 O(n)        O(min(n,Σ)) each char in/out once
    Window + last-index jump ✅     O(n)        O(min(n,Σ)) fewer ops, easier to
                                                            get wrong
    Window + 128-slot array         O(n)        O(1)       ASCII only

    SPACE, stated precisely: the window can never hold more than Σ distinct
    characters, so it is O(min(n, Σ)). For this problem Σ is bounded (English
    letters, digits, symbols, spaces — at most 128 printable ASCII), so
    **O(1) auxiliary space** is a fair claim. Say "O(min(n, Σ)), which is O(1)
    for a bounded alphabet" — it shows you know why.

    ⚠️  The jump version's `last` map is NOT bounded by the window: it keeps
        every character ever seen. Still O(Σ), but the constant differs, and
        for an unbounded alphabet (arbitrary Unicode) it is O(n) while the set
        version stays O(window).


================================================================================
EDGE CASES
================================================================================
    ""            -> 0    EMPTY STRING IS LEGAL (`0 <= s.length`). The loop
                          never runs; `best = 0` must already be the answer.
                          Anything that reads s[0] up front crashes here.

    "a"           -> 1    Single character. Exercises `r - l + 1` at r = l = 0;
                          returns 0 if you wrote `r - l`.

    "bbbbb"       -> 1    Every character repeats. The window is permanently
                          width 1 and the inner `while` fires on every step —
                          the worst case for the shrink loop, and still O(n)
                          because `l` moves n times TOTAL.

    "abba"        -> 2    THE STALE-INDEX DETECTOR. The unguarded jump returns
                          3. Every implementation must be run against this.

    "tmmzuxt"     -> 5    Same bug, different shape ("mzuxt"). The 't' at the
                          end was last seen at index 0, long before `l`.

    "dvdf"        -> 3    The answer is "vdf" — it does NOT start at index 0.
                          Catches anyone anchoring the window at the start.

    "abcdefg"     -> 7    All distinct: the window never shrinks, best == n.

    " "           -> 1    A space is a character. So are '!' and '@'.

    "aA"          -> 2    CASE SENSITIVE. 'a' and 'A' are different characters.
                          Do not lowercase the input.


================================================================================
COMMON MISTAKES
================================================================================
1. The unguarded jump `l = last[ch] + 1`. Returns 3 on "abba". If you remember
   one thing from this problem, remember `max(l, ...)`.

2. `r - l` instead of `r - l + 1`. Off by one on every single answer.

3. Recording the answer BEFORE restoring the invariant, so you measure a window
   that still contains a duplicate.

4. Using `if` instead of `while` in the set version. One eviction is not enough
   when the duplicate is several characters deep — "abcda" needs `l` to move
   past index 0 only, but "abcbd"-style inputs need multi-step shrinks. The
   `while` is doing real work here (unlike LC 424, where `if` IS correct for a
   different reason — see problem 007).

5. Clearing the whole set and restarting from `r` when a duplicate appears.
   That is O(n^2) in the worst case and also just wrong: it discards the valid
   tail of the window.

6. `window.remove(ch)` (the incoming character) instead of `window.remove(s[l])`
   (the leftmost one) inside the shrink loop.

7. Returning the substring when the problem asked for its LENGTH — or slicing
   inside the loop to build it, which reintroduces O(n^2).

8. Assuming lowercase a-z and using a 26-slot array. The constraints say
   "English letters, digits, symbols and spaces" — 26 slots is a buffer
   overrun waiting to happen. 128 is the safe ASCII bound.

9. Claiming O(n^2) because of the nested loop, or O(n) without being able to
   explain why the nesting is not real. The amortization argument is the whole
   interview question here.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the substring itself.
A: Track `best_l` alongside `best`, then slice ONCE after the loop. Slicing
   inside the loop is O(n^2). Also decide the tie-break: `>` keeps the earliest
   longest, `>=` keeps the latest.

Q: At most K repeats allowed / at most K distinct characters (LC 340, LC 159)?
A: Same template, different invariant and a Counter instead of a set:
   `while len(count) > K: evict`. That is problem 009 in this folder. Note the
   `del count[ch]` when it hits zero, or `len()` counts zombie keys.

Q: Longest substring with at most k replacements (LC 424)?
A: Also this template, but the validity test becomes
   `window_len - max_freq <= k`. Problem 007.

Q: What if the alphabet is huge — full Unicode?
A: The set version's space stays O(window size). The last-index map version
   grows to O(distinct characters seen) = O(n). That is a real reason to prefer
   the set version at scale, and a good thing to volunteer.

Q: Can you do it in one pass with O(1) space?
A: With a bounded alphabet, yes — a 128-slot integer array of last-seen indices
   is O(1) by definition. For an unbounded alphabet, no: you must remember
   which characters are in the window, and that is Ω(window size).

Q: Count how many substrings have all-distinct characters, instead of the
   longest?
A: The counting substitution from the topic guide: `count += r - l + 1` in
   place of the `max`. The property is hereditary, so every suffix of the
   current window that ends at r is valid.

Q: Longest SUBSEQUENCE without repeating characters?
A: Trivial — it is the number of distinct characters, `len(set(s))`. Order and
   contiguity are what make the substring version interesting. If an
   interviewer asks this, they are checking that you noticed the difference.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 159  Longest Substring with At Most Two Distinct  — same shape, Counter
    LC 340  Longest Substring with At Most K Distinct    — the generalisation
    LC 424  Longest Repeating Character Replacement      — problem 007 here
    LC 904  Fruit Into Baskets                           — LC 159 in disguise
    LC 1004 Max Consecutive Ones III                     — problem 006 here
    LC 1695 Maximum Erasure Value                        — this problem, but
                                                           maximise the SUM
    LC 76   Minimum Window Substring                     — the shortest-window
                                                           counterpart (015)
================================================================================
"""

import random
import time


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        """Window + set, shrinking one character at a time. O(n) time,
        O(min(n, alphabet)) space. The version to write when unsure."""
        window = set()
        l = best = 0
        for r, ch in enumerate(s):
            while ch in window:                 # RESTORE: evict until distinct
                window.remove(s[l])
                l += 1
            window.add(ch)                      # ENTER
            best = max(best, r - l + 1)         # RECORD  (+1: l==r is length 1)
        return best

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def lengthOfLongestSubstring_jump(self, s: str) -> int:
        """Last-index map, jumping `l` past the previous occurrence.

        `max(l, ...)` is MANDATORY — see the unguarded version below.
        """
        last = {}
        l = best = 0
        for r, ch in enumerate(s):
            l = max(l, last.get(ch, -1) + 1)    # never move l BACKWARDS
            last[ch] = r
            best = max(best, r - l + 1)
        return best

    def lengthOfLongestSubstring_jump_guarded(self, s: str) -> int:
        """The same jump written with an explicit guard instead of max()."""
        last = {}
        l = best = 0
        for r, ch in enumerate(s):
            if ch in last and last[ch] >= l:    # only jump if it is IN the window
                l = last[ch] + 1
            last[ch] = r
            best = max(best, r - l + 1)
        return best

    def lengthOfLongestSubstring_array(self, s: str) -> int:
        """128-slot ASCII table of last-seen indices. O(1) space, no hashing."""
        last = [-1] * 128
        l = best = 0
        for r, ch in enumerate(s):
            c = ord(ch)
            if last[c] >= l:
                l = last[c] + 1
            last[c] = r
            best = max(best, r - l + 1)
        return best

    def lengthOfLongestSubstring_counter(self, s: str) -> int:
        """Counter-based, in the exact shape used by problems 006/007/009 —
        so the family resemblance is visible."""
        from collections import Counter
        count = Counter()
        l = best = 0
        for r, ch in enumerate(s):
            count[ch] += 1                       # ENTER
            while count[ch] > 1:                 # RESTORE: no character twice
                count[s[l]] -= 1
                if count[s[l]] == 0:
                    del count[s[l]]              # keep len() meaningful
                l += 1
            best = max(best, r - l + 1)          # RECORD
        return best

    def lengthOfLongestSubstring_brute(self, s: str) -> int:
        """O(n^2) oracle: extend from every start until a repeat appears."""
        best = 0
        for i in range(len(s)):
            seen = set()
            for j in range(i, len(s)):
                if s[j] in seen:
                    break
                seen.add(s[j])
                best = max(best, j - i + 1)
        return best

    def lengthOfLongestSubstring_substring(self, s: str) -> str:
        """Follow-up: return the substring, not the length. Slice ONCE."""
        window = set()
        l = best_len = best_l = 0
        for r, ch in enumerate(s):
            while ch in window:
                window.remove(s[l])
                l += 1
            window.add(ch)
            if r - l + 1 > best_len:             # `>` keeps the EARLIEST longest
                best_len, best_l = r - l + 1, l
        return s[best_l:best_l + best_len]       # one slice, after the loop

    def countDistinctSubstrings(self, s: str) -> int:
        """Follow-up: COUNT substrings with all-distinct characters.
        The counting substitution: `count += r - l + 1`."""
        window = set()
        l = total = 0
        for r, ch in enumerate(s):
            while ch in window:
                window.remove(s[l])
                l += 1
            window.add(ch)
            total += r - l + 1                   # every suffix ending at r
        return total

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def lengthOfLongestSubstring_unguarded(self, s: str) -> int:
        """✗ BROKEN ON PURPOSE — jumps without max(), so a STALE index from
        outside the window drags `l` backwards. Returns 3 on "abba"."""
        last = {}
        l = best = 0
        for r, ch in enumerate(s):
            if ch in last:
                l = last[ch] + 1                 # no max(), no guard
            last[ch] = r
            best = max(best, r - l + 1)
        return best

    def lengthOfLongestSubstring_if_not_while(self, s: str) -> int:
        """✗ BROKEN ON PURPOSE — shrinks only ONE character per step, so a
        duplicate several characters deep is never fully evicted."""
        window = set()
        l = best = 0
        for r, ch in enumerate(s):
            if ch in window:                     # should be `while`
                window.discard(s[l])
                l += 1
            window.add(ch)
            best = max(best, r - l + 1)
        return best


# ==============================================================================
# TESTS — run:  python 005_longest_substring_without_repeating_characters_solution.py
# ==============================================================================
CASES = [
    "abcabcbb", "bbbbb", "pwwkew", "", "a", "au", "abba", "tmmzuxt", "dvdf",
    "abcdefg", "aab", "cdd", "abcb", " ", "a b c a", "!@#!@#", "0123401234",
    "aA", "abcabcabc", "aaabbbccc", "nfpdmpi", "ohvhjdml", "wobgrovw",
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("set + shrink   ", sol.lengthOfLongestSubstring),
        ("jump + max()   ", sol.lengthOfLongestSubstring_jump),
        ("jump + guard   ", sol.lengthOfLongestSubstring_jump_guarded),
        ("128-slot array ", sol.lengthOfLongestSubstring_array),
        ("Counter form   ", sol.lengthOfLongestSubstring_counter),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(t) == sol.lengthOfLongestSubstring_brute(t) for t in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # the follow-up variants
    ok = all(len(sol.lengthOfLongestSubstring_substring(t))
             == sol.lengthOfLongestSubstring_brute(t) for t in CASES)
    ok &= all(len(set(sol.lengthOfLongestSubstring_substring(t)))
              == len(sol.lengthOfLongestSubstring_substring(t)) for t in CASES)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  substring variant (right length AND "
          f"actually distinct)")

    def brute_count(t):
        return sum(1
                   for i in range(len(t))
                   for j in range(i, len(t))
                   if len(set(t[i:j + 1])) == j - i + 1)
    ok = all(sol.countDistinctSubstrings(t) == brute_count(t) for t in CASES)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  counting variant (count += r - l + 1)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(3)
    trials, mismatches = 5000, 0
    for _ in range(trials):
        t = "".join(random.choice("abcd") for _ in range(random.randint(0, 14)))
        want = sol.lengthOfLongestSubstring_brute(t)
        for _, fn in impls:
            if fn(t) != want:
                mismatches += 1
    print(f"  {trials} random strings (tiny alphabet, dense repeats) x "
          f"{len(impls)} implementations: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The window, traced.
    # ----------------------------------------------------------------------
    text = "abcabcbb"
    print(f"\n--- the window over {text!r} ---")
    print(f"  {'r':>2} {'ch':>4} {'evicted':>10} {'l':>2} {'window':>10}"
          f" {'len':>4} {'best':>5}")
    window, l, best = set(), 0, 0
    for r, ch in enumerate(text):
        evicted = []
        while ch in window:
            evicted.append(s_ := text[l])
            window.remove(s_)
            l += 1
        window.add(ch)
        best = max(best, r - l + 1)
        print(f"  {r:>2} {ch!r:>4} {''.join(evicted) or '-':>10} {l:>2} "
              f"{text[l:r+1]!r:>10} {r - l + 1:>4} {best:>5}")

    # ----------------------------------------------------------------------
    # ⚠️  The stale-index bug.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  jumping without max(): the stale-index bug ---")
    print(f"  {'input':<12} {'correct':>8} {'unguarded jump':>15}  ok?")
    for t in ("abba", "tmmzuxt", "dvdf", "abcabcbb", "abcda", "abac", "aab"):
        good = sol.lengthOfLongestSubstring(t)
        bad = sol.lengthOfLongestSubstring_unguarded(t)
        print(f"  {t!r:<12} {good:>8} {bad:>15}  "
              f"{'yes' if good == bad else 'NO  <- l moved BACKWARDS'}")

    print("\n  'abba' step by step:")
    text = "abba"
    last, l_ok, l_bad = {}, 0, 0
    print(f"  {'r':>2} {'ch':>4} {'last[ch]':>9} {'l (max)':>8} {'l (no max)':>11}"
          f" {'window (no max)':>17}")
    for r, ch in enumerate(text):
        prev = last.get(ch, -1)
        l_ok = max(l_ok, prev + 1)
        if ch in last:
            l_bad = prev + 1
        last[ch] = r
        flag = "  <- INVALID" if len(set(text[l_bad:r+1])) != r - l_bad + 1 else ""
        print(f"  {r:>2} {ch!r:>4} {prev:>9} {l_ok:>8} {l_bad:>11} "
              f"{text[l_bad:r+1]!r:>17}{flag}")
    print("  At r=3 the unguarded version pulls l from 2 back to 1, producing")
    print("  'bba' — a window with two b's. Wrong answer AND a broken O(n) proof.")

    # ----------------------------------------------------------------------
    # ⚠️  `if` instead of `while`.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `if` instead of `while` in the shrink ---")
    print(f"  {'input':<14} {'correct':>8} {'single-step shrink':>19}  ok?")
    for t in ("abcabcbb", "abba", "pwwkew", "abcdea", "aabaab", "dvdf"):
        good = sol.lengthOfLongestSubstring(t)
        bad = sol.lengthOfLongestSubstring_if_not_while(t)
        print(f"  {t!r:<14} {good:>8} {bad:>19}  "
              f"{'yes' if good == bad else 'NO  <- duplicate still inside'}")

    # ----------------------------------------------------------------------
    # The amortization argument, counted.
    # ----------------------------------------------------------------------
    print("\n--- the inner `while` is NOT nested work ---")

    def moves(t):
        window, l, adds, removes = set(), 0, 0, 0
        for r, ch in enumerate(t):
            while ch in window:
                window.remove(t[l]); l += 1; removes += 1
            window.add(ch); adds += 1
        return adds, removes

    print(f"  {'input shape':<32} {'n':>7} {'enters':>8} {'leaves':>8} {'total':>8}")
    random.seed(11)
    for label, t in (
        ("all distinct (NEVER shrinks)", "".join(chr(0x100 + i) for i in range(5000))),
        ("all identical (shrinks always)", "a" * 5000),
        ("random over 4 letters", "".join(random.choice("abcd") for _ in range(5000))),
        ("random over 90 symbols", "".join(chr(33 + random.randrange(90)) for _ in range(5000))),
    ):
        a, rm = moves(t)
        print(f"  {label:<32} {len(t):>7} {a:>8} {rm:>8} {a + rm:>8}")
    print("  Total work is <= 2n on EVERY shape: each character enters once and")
    print("  leaves at most once. That is the whole O(n) proof.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n^2).
    # ----------------------------------------------------------------------
    print("\n--- window vs re-scanning from every start ---")
    print("  (a LARGE alphabet is the brute force's worst case: the inner scan")
    print("   runs a long way before it finds a repeat and breaks)")
    print(f"  {'n':>7} {'window O(n)':>13} {'brute O(n^2)':>14}")
    random.seed(0)
    for n in (2_000, 4_000, 8_000):
        t = "".join(chr(0x100 + random.randrange(3000)) for _ in range(n))
        t0 = time.perf_counter(); sol.lengthOfLongestSubstring(t)
        t1 = time.perf_counter(); sol.lengthOfLongestSubstring_brute(t)
        t2 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>11.1f}ms {(t2 - t1) * 1000:>12.1f}ms")
    print("  Note the brute force is only O(n^2) because it BREAKS at the first")
    print("  repeat; the naive 'check every substring' version is O(n^3).")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
