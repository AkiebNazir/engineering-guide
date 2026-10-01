"""
================================================================================
SOLUTION · LeetCode 1456 · Maximum Number of Vowels in a Substring        [Easy]
https://leetcode.com/problems/maximum-number-of-vowels-in-a-substring-of-given-length/
================================================================================

THE CORE IDEA
-------------
LC 643's fixed window with the aggregate swapped from "sum of values" to
"count of elements satisfying a predicate":

    VOWELS = frozenset("aeiou")
    count = best = 0
    for r, ch in enumerate(s):
        count += ch in VOWELS                       # enter
        if r >= k:      count -= s[r - k] in VOWELS  # leave
        if r >= k - 1:  best = max(best, count)
        if best == k:   return k                     # ceiling reached
    return best

O(n) time, O(1) space. The window mechanics are identical to LC 643; only the
question "what enters and what leaves" changed its answer type from an int to a
0/1 indicator.


THE GENERALISATION — this is the shape to remember
--------------------------------------------------
    "Maximum number of X in any window of size k"

is ALWAYS this, for any O(1) predicate P:

        count += P(entering)
        count -= P(leaving)

Because P's output is 0 or 1, the aggregate is an integer with an exact
inverse, which is the one and only requirement a sliding window imposes
(topic guide §1.0). You are not doing string processing; you are summing an
indicator array you never actually build:

    "leetcode"  ->  [0, 1, 1, 0, 0, 0, 0, 1]      l e e t c o d e
                                                     ^ ^       ^  (o at idx 5)

    (careful: 'o' at index 5 is a vowel too — the indicator is
     l=0 e=1 e=1 t=0 c=0 o=1 d=0 e=1)

Once you see that, LC 1456, LC 643, LC 1004 and LC 2269 are one problem.


================================================================================
`True` IS AN `int` — AND THAT IS OFFICIAL, NOT A HACK
================================================================================
`bool` is a SUBCLASS of `int` in Python, with `True == 1` and `False == 0`.
So `count += ch in VOWELS` is not a trick; it is documented arithmetic:

    >>> True + True + False
    2
    >>> sum(c in "aeiou" for c in "leetcode")
    4

It is idiomatic and it removes a branch. The alternative reads:

    if ch in VOWELS:
        count += 1

Both are fine. Use the arithmetic form when the predicate is short and obvious,
the `if` form when the predicate needs a name. What you must NOT do is write
`count += 1 if ch in VOWELS else 0` — that is the same thing with extra words.

⚠️  The one place this bites: `sum()` over booleans gives an `int`, but
`numpy.bool_` and pandas types do not always behave the same way. In plain
Python you are safe.


================================================================================
HOW TO TEST MEMBERSHIP — the constant factor
================================================================================
All four are O(1) per character. The folklore about which is fastest is mostly
wrong, so the benchmark at the bottom of this file measures them on 400k
characters. Typical result:

    ch in "aeiou"                 ~8.0ms   linear scan of 5 chars, but entirely
                                           in C — the FASTEST here
    ch in VOWELS                  ~9.5ms   hoisted frozenset
    ch in {'a','e','i','o','u'}   ~9.3ms   set literal written inside the loop
    is_vowel[ord(ch) - 97]        ~10.0ms  26-slot list — the SLOWEST

Three things worth taking from that:

  * A 26-slot lookup table is NOT faster for this. `ord()` is a Python-level
    function call, and it costs more than the hash it saves. The array's real
    advantage shows up elsewhere — comparing two whole frequency maps (LC 567,
    LC 438), where `list == list` beats `Counter == Counter` by ~70x.
  * The set literal inside the loop is not the disaster it looks like: CPython's
    peephole optimiser constant-folds a set literal used as the right operand of
    `in` into a `frozenset` stored with the code object, so it is NOT rebuilt per
    iteration. Do not RELY on that — hoisting it is clearer and portable — but do
    not claim it is O(n) allocations either, because it measurably is not.
  * For five characters, scanning a short string in C wins. Reach for a set when
    the collection is large enough that the linear scan stops being trivial.

This is a CONSTANT-FACTOR discussion. Say that, rather than claiming any of them
changes the complexity.


================================================================================
THE EARLY EXIT
================================================================================
    A window of length k contains AT MOST k vowels.

So `k` is a hard ceiling on the answer, and once `best == k` no later window
can beat it:

    if best == k:
        return k

⚠️  This does NOT improve the worst case. On "bbbb...b" the exit never fires
and you read every character. State the bound honestly:

    Worst case  O(n)   (few vowels — the exit never triggers)
    Best case   O(k)   (the first window is all vowels)

The reason to mention it in an interview is not the speed. It is that you
noticed the answer has a known maximum — the same reasoning that produces the
`if nums[i] > 0: break` prune in 3Sum, and the `if best == n: break` prune in
many others. Recognising a ceiling is a transferable habit.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(s)

    Approach                              Time      Space  Note
    ------------------------------------  --------  -----  --------------------
    Count vowels in every substring       O(n*k)    O(k)   slice + scan per step
    s.count() per substring               O(n*k*5)  O(k)   5 passes per window!
    Prefix count array                    O(n)      O(n)   pre[r] - pre[l]
    Sliding count ✅                      O(n)      O(1)   one enter, one leave

    ⚠️  `sum(c in "aeiou" for c in s[i:i+k])` inside a loop is the O(n*k) trap
        in its natural habitat. The slice copies k characters AND the genexp
        walks them.

    ⚠️  Prefix counts also give O(n) and answer arbitrary ranges, at O(n)
        memory. Worth naming as the generalisation (topic 04) and then
        discarding: we only need consecutive windows.


================================================================================
EDGE CASES
================================================================================
    "rhythms", k=4  -> 0    NO VOWELS. `best` must be able to stay 0, and the
                            early exit must not fire on `best == k` when k > 0
                            and best is 0. (It cannot — 0 != 4.)

    "a", k=1        -> 1    n == k == 1. The window is complete at r = 0, which
                            exercises `r >= k - 1` at its very first value.

    "aeiou", k=5    -> 5    k == n, all vowels: the answer IS the ceiling, and
                            the early exit fires on the last character.

    "aaaaaaaaaa",k=1-> 1    k == 1: enter and leave are the same index one step
                            apart; the count must never drift above 1.

    "uuuuxxxx", k=4 -> 4    Best window at the FRONT. Detects `r >= k` used as
                            the record condition (which skips window 0), and
                            the early exit fires immediately.

    "xxxxuuuu", k=4 -> 4    Best window at the END. Detects a loop that stops
                            one iteration short.

    "xuxuxuxu", k=3 -> 2    Alternating — no window is uniform, so the answer
                            comes from genuine sliding rather than a lucky run.

    ⚠️  k > len(s) cannot happen (constraint `1 <= k <= s.length`). If you want
        the code robust outside LeetCode, decide between returning 0 and
        raising, and say which.


================================================================================
COMMON MISTAKES
================================================================================
1. Re-counting the whole window each step (`s[i:i+k].count(...)`). O(n*k).
   The defining mistake of this topic.

2. Building the vowel set inside the loop. Allocation on every iteration.

3. `r >= k` as the record condition, skipping the first window. "uuuuxxxx"
   catches it.

4. Forgetting to DECREMENT when a vowel leaves. The count then only ever grows
   and you effectively count vowels in every PREFIX, not every window — which
   returns the total vowel count of the string.

5. Decrementing unconditionally (`count -= 1` without testing the leaving
   character). The count goes negative and the answer collapses.

6. Using `s[r-k]` when the window has not filled yet (r < k), reading a
   NEGATIVE index. Python does not raise — `s[-1]` is the LAST character — so
   you silently subtract the wrong character's indicator. Same negative-index
   hazard as 3Sum's missing `i > 0` guard.

7. Treating 'y' as a vowel. The problem lists exactly five. Read the statement.

8. Claiming the early exit makes it O(k). It does not; the worst case is
   unchanged at O(n).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the substring itself, not the count.
A: Track `best_end` alongside `best` and slice ONCE after the loop:
   `s[best_end - k + 1 : best_end + 1]`. Slicing inside the loop is the O(n*k)
   trap all over again.

Q: Answer many different k values on the same string.
A: Build a prefix count array once: `pre[i] = vowels in s[:i]`. Then the count
   for any window is `pre[i+k] - pre[i]`, so each k costs O(n) — or O(1) per
   individual query. That is topic 04, and it is the right answer the moment
   the queries are arbitrary.

Q: Maximum vowels in a substring of length AT MOST k?
A: The count is monotone in length here (adding characters can only add
   vowels), so the answer is just the length-k answer. Say why: the predicate
   is upward-closed, so the largest allowed window is always at least as good.

Q: Longest substring with at most k CONSONANTS?
A: That is a VARIABLE window — Shape B — not this one. "At most k violations"
   is LC 1004 later in this folder. Notice the difference: here k bounds the
   WINDOW SIZE, there k bounds the VIOLATION COUNT.

Q: Unicode / arbitrary alphabets rather than lowercase ASCII?
A: The `frozenset` version is unchanged. The `ord(ch) - 97` lookup table breaks
   — it assumes a 26-letter contiguous alphabet. That is exactly the tradeoff
   to name when you reach for an array instead of a hash set.

Q: The string arrives as a stream and you cannot index backwards.
A: `collections.deque(maxlen=k)`: append the new character, and if the deque
   was full the eviction is automatic — but you must read the element about to
   fall off (`dq[0]`) BEFORE appending, to decrement the count.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 643  Maximum Average Subarray I    — the same window over a SUM
    LC 219  Contains Duplicate II         — the same window over a SET
    LC 1343 Subarrays of Size K With Avg  — the COUNTING version of LC 643
            >= Threshold
    LC 2269 Find the K-Beauty of a Number — fixed window over digits
    LC 1052 Grumpy Bookstore Owner        — fixed window over a conditional gain
    LC 1004 Max Consecutive Ones III      — k bounds VIOLATIONS, not the window
    LC 567  Permutation in String         — fixed window over a full frequency map
================================================================================
"""

import random
import time

VOWELS = frozenset("aeiou")


class Solution:
    def maxVowels(self, s: str, k: int) -> int:
        """Fixed window over a 0/1 indicator, with the ceiling early exit.

        O(n) worst case, O(1) space.
        """
        count = best = 0
        for r, ch in enumerate(s):
            count += ch in VOWELS                       # enter
            if r >= k:                                  # window would be k+1
                count -= s[r - k] in VOWELS             # leave
            if r >= k - 1:                              # window is exactly k
                best = max(best, count)
                if best == k:                           # ceiling: cannot improve
                    return k
        return best

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def maxVowels_no_early_exit(self, s: str, k: int) -> int:
        """Same, without the ceiling exit. Identical answers, always O(n)."""
        count = best = 0
        for r, ch in enumerate(s):
            count += ch in VOWELS
            if r >= k:
                count -= s[r - k] in VOWELS
            if r >= k - 1:
                best = max(best, count)
        return best

    def maxVowels_table(self, s: str, k: int) -> int:
        """26-slot lookup table — no hashing at all. Assumes lowercase ASCII."""
        is_vowel = [0] * 26
        for c in "aeiou":
            is_vowel[ord(c) - 97] = 1
        count = best = 0
        for r in range(len(s)):
            count += is_vowel[ord(s[r]) - 97]
            if r >= k:
                count -= is_vowel[ord(s[r - k]) - 97]
            if r >= k - 1 and count > best:
                best = count
        return best

    def maxVowels_prefix(self, s: str, k: int) -> int:
        """Prefix counts. O(n) time, O(n) space; answers ARBITRARY ranges."""
        pre = [0] * (len(s) + 1)
        for i, ch in enumerate(s):
            pre[i + 1] = pre[i] + (ch in VOWELS)
        return max(pre[i + k] - pre[i] for i in range(len(s) - k + 1))

    def maxVowels_brute(self, s: str, k: int) -> int:
        """O(n*k) oracle."""
        return max(sum(c in VOWELS for c in s[i:i + k])
                   for i in range(len(s) - k + 1))

    # ------------------------------------------------------------------
    # Deliberate breakages.
    # ------------------------------------------------------------------
    def maxVowels_no_decrement(self, s: str, k: int) -> int:
        """✗ BROKEN — never removes the leaving character, so it counts vowels
        in every PREFIX and returns the whole string's vowel count."""
        count = best = 0
        for r, ch in enumerate(s):
            count += ch in VOWELS
            if r >= k - 1:
                best = max(best, count)
        return best

    def maxVowels_unguarded_leave(self, s: str, k: int) -> int:
        """✗ BROKEN — drops the `r >= k` guard, so while the window is still
        filling it subtracts s[NEGATIVE index]: the END of the string."""
        count = best = 0
        for r, ch in enumerate(s):
            count += ch in VOWELS
            count -= s[r - k] in VOWELS          # r - k is negative when r < k
            if r >= k - 1:
                best = max(best, count)
        return best


# ==============================================================================
# TESTS — run:  python 003_maximum_number_of_vowels_in_a_substring_solution.py
# ==============================================================================
CASES = [
    ("abciiidef", 3), ("aeiou", 2), ("leetcode", 3), ("rhythms", 4),
    ("tryhard", 4), ("a", 1), ("b", 1), ("aeiou", 5), ("weallloveyou", 7),
    ("aaaaaaaaaa", 1), ("novowelshere", 12), ("uuuuxxxx", 4),
    ("xxxxuuuu", 4), ("xuxuxuxu", 3),
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("window + early exit", sol.maxVowels),
        ("window, no exit    ", sol.maxVowels_no_early_exit),
        ("26-slot table      ", sol.maxVowels_table),
        ("prefix counts      ", sol.maxVowels_prefix),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(t, k) == sol.maxVowels_brute(t, k) for t, k in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n*k) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n*k) oracle ---")
    random.seed(1456)
    trials, mismatches = 4000, 0
    for _ in range(trials):
        n = random.randint(1, 16)
        text = "".join(random.choice("aeioubcdxyz") for _ in range(n))
        k = random.randint(1, n)
        want = sol.maxVowels_brute(text, k)
        for _, fn in impls:
            if fn(text, k) != want:
                mismatches += 1
    print(f"  {trials} random (string, k) x {len(impls)} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The window, traced — and the 0/1 indicator it is really summing.
    # ----------------------------------------------------------------------
    text, k = "abciiidef", 3
    print(f"\n--- the window over {text!r}, k={k} ---")
    print(f"  string    : {' '.join(text)}")
    print(f"  indicator : {' '.join(str(int(c in VOWELS)) for c in text)}")
    print(f"  {'r':>2} {'enters':>7} {'leaves':>7} {'window':>9} {'count':>6}"
          f" {'best':>5}")
    count = best = 0
    for r, ch in enumerate(text):
        count += ch in VOWELS
        leaves = f"{text[r - k]!r}" if r >= k else "-"
        if r >= k:
            count -= text[r - k] in VOWELS
        if r >= k - 1:
            best = max(best, count)
            print(f"  {r:>2} {ch!r:>7} {leaves:>7} {text[r-k+1:r+1]!r:>9} "
                  f"{count:>6} {best:>5}")
        else:
            print(f"  {r:>2} {ch!r:>7} {leaves:>7} {'(filling)':>9} "
                  f"{count:>6} {'-':>5}")
    print("  The window is summing an indicator array it never builds.")

    # ----------------------------------------------------------------------
    # ⚠️  Forgetting the decrement / the guard.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the two ways the leave step goes wrong ---")
    print(f"  {'input':<16} {'k':>2} {'correct':>8} {'no decrement':>13}"
          f" {'unguarded':>10}")
    for text, k in ("abciiidef", 3), ("leetcode", 3), ("aeioubcd", 2), \
                    ("xxxxuuuu", 4), ("uuuuxxxx", 4):
        print(f"  {text!r:<16} {k:>2} {sol.maxVowels(text, k):>8} "
              f"{sol.maxVowels_no_decrement(text, k):>13} "
              f"{sol.maxVowels_unguarded_leave(text, k):>10}")
    print("  no decrement -> counts vowels in every PREFIX (i.e. the whole")
    print("  string's total).  unguarded -> while r < k it subtracts s[r-k],")
    print("  a NEGATIVE index, silently removing characters from the END.")

    # ----------------------------------------------------------------------
    # `True` is an int.
    # ----------------------------------------------------------------------
    print("\n--- `bool` is a subclass of `int`, so the predicate IS the count ---")
    print(f"  True + True + False        = {True + True + False}")
    print(f"  isinstance(True, int)      = {isinstance(True, int)}")
    print(f"  sum(c in VOWELS for c in 'leetcode') = "
          f"{sum(c in VOWELS for c in 'leetcode')}")
    print("  So `count += ch in VOWELS` is documented arithmetic, not a hack.")

    # ----------------------------------------------------------------------
    # What the early exit buys.
    # ----------------------------------------------------------------------
    print("\n--- what the ceiling early exit prunes ---")

    def chars_read(text, k, early):
        count = best = seen = 0
        for r, ch in enumerate(text):
            seen += 1
            count += ch in VOWELS
            if r >= k:
                count -= text[r - k] in VOWELS
            if r >= k - 1:
                best = max(best, count)
                if early and best == k:
                    break
        return seen

    random.seed(7)
    print(f"  {'input shape':<28} {'chars read, no exit':>20} {'with exit':>11}")
    for label, text in (
        ("all vowels", "aeiou" * 4000),
        ("vowel-rich (50%)", "".join(random.choice("aeioubcdf")
                                     for _ in range(20_000))),
        ("no vowels at all", "bcdfg" * 4000),
    ):
        print(f"  {label:<28} {chars_read(text, 4, False):>20} "
              f"{chars_read(text, 4, True):>11}")
    print("  On vowel-free input the exit NEVER fires — the worst case is still")
    print("  O(n), and you should say so rather than claiming a speedup.")

    # ----------------------------------------------------------------------
    # Membership testing: the constant factor.
    # ----------------------------------------------------------------------
    print("\n--- how to test membership (constant factors, not complexity) ---")
    random.seed(0)
    text = "".join(random.choice("abcdefghijklmnopqrstuvwxyz")
                   for _ in range(400_000))
    is_vowel = [0] * 26
    for c in "aeiou":
        is_vowel[ord(c) - 97] = 1

    def timeit(fn):
        t0 = time.perf_counter()
        fn()
        return (time.perf_counter() - t0) * 1000

    rows = [
        ("ch in VOWELS (hoisted frozenset)",
         lambda: sum(c in VOWELS for c in text)),
        ("ch in 'aeiou' (literal str)",
         lambda: sum(c in "aeiou" for c in text)),
        ("ch in {..} literal INSIDE loop",
         lambda: sum(c in {'a', 'e', 'i', 'o', 'u'} for c in text)),
        ("is_vowel[ord(ch) - 97]",
         lambda: sum(is_vowel[ord(c) - 97] for c in text)),
    ]
    for label, fn in rows:
        print(f"  {label:<34} {timeit(fn):>8.1f}ms")
    print("  All O(1) per character. The gaps are constant factors — say that,")
    print("  and do not claim a complexity improvement from a lookup table.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n*k).
    # ----------------------------------------------------------------------
    print("\n--- sliding vs recounting each substring ---")
    print(f"  {'n':>7} {'k':>7} {'slide O(n)':>12} {'recount O(nk)':>15}")
    for n, k in ((20_000, 10), (20_000, 500), (20_000, 5_000)):
        text = "".join(random.choice("aeioubcdfg") for _ in range(n))
        t0 = time.perf_counter(); sol.maxVowels_no_early_exit(text, k)
        t1 = time.perf_counter(); sol.maxVowels_brute(text, k)
        t2 = time.perf_counter()
        print(f"  {n:>7} {k:>7} {(t1 - t0) * 1000:>10.1f}ms "
              f"{(t2 - t1) * 1000:>13.1f}ms")
    print("  Flat in k versus linear in k — the same shape as LC 643.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
