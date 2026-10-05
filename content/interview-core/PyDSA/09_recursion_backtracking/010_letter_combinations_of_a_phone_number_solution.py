"""
================================================================================
SOLUTION · LeetCode 17 · Letter Combinations of a Phone Number           [Medium]
https://leetcode.com/problems/letter-combinations-of-a-phone-number/
================================================================================

THE CORE IDEA
--------------
Every prior problem in this folder picks repeatedly from ONE shared pool
(nums, or 1..n) with restrictions (start index, used[], dedupe). This is the
first problem where the pool CHANGES with depth: at recursion depth `i` the
only legal choices are the letters mapped to `digits[i]`. That turns the
result into a CARTESIAN PRODUCT of per-position pools rather than a
combinatorial subset/permutation of one set:

    result = pool(digits[0]) x pool(digits[1]) x ... x pool(digits[n-1])

The choose/explore/unchoose skeleton is identical to every other file here;
only the SOURCE of the choices at each level is new (`mapping[digits[i]]`
instead of `nums[start:]`).

================================================================================
MULTIPLE APPROACHES
================================================================================

1. BACKTRACKING (DFS over positions)                        <- the answer
   `path` holds one char per digit so far; `dfs(i)` branches over
   `mapping[digits[i]]`. Base case: `i == len(digits)`, join and record.
   O(4^n) leaves, O(n) stack.

2. `itertools.product(*pools)`
   Build the list of per-digit letter pools, then take their Cartesian
   product directly. Same output, C-coded iteration — the "in production"
   answer, and used below as the correctness oracle.

3. ITERATIVE LEVEL-BY-LEVEL (BFS-style) EXPANSION
   Start with `[""]`. For each digit, replace the frontier with every
   (prefix + new_letter) combination:
       result = [prefix + ch for prefix in result for ch in mapping[digit]]
   No recursion at all. This is what `itertools.product` does internally,
   spelled out by hand — worth being able to write cold.

4. RECURSION WITHOUT A PATH LIST (STRING-BUILDING)
   Pass the partial string by value instead of mutating a shared list:
   `dfs(i, current)` where `current` is a new string each call. No
   choose/unchoose needed because strings are immutable — but every call
   allocates a new string. Priced against approach 1 below.

================================================================================
STEP BY STEP  ·  digits = "23"
================================================================================
mapping['2'] = "abc"     mapping['3'] = "def"

    dfs(i=0, path=[])
    +-- CHOOSE 'a'  path=['a']
    |     dfs(i=1, path=['a'])
    |     +-- CHOOSE 'd'  path=['a','d']
    |     |     dfs(i=2) -> i == len(digits) -> EMIT "ad"
    |     |   UNCHOOSE -> path=['a']
    |     +-- CHOOSE 'e'  -> EMIT "ae"  -> UNCHOOSE
    |     +-- CHOOSE 'f'  -> EMIT "af"  -> UNCHOOSE
    |   UNCHOOSE -> path=[]
    +-- CHOOSE 'b'  -> "bd","be","bf"  (same shape under 'b')
    +-- CHOOSE 'c'  -> "cd","ce","cf"  (same shape under 'c')

    Result: ["ad","ae","af","bd","be","bf","cd","ce","cf"]   (3 x 3 = 9)

    Tree shape: depth == len(digits) == 2, branching factor == len(pool at
    that depth) (3, then 3). Total leaves = product of pool sizes, NOT a
    C(n,k) or n! formula — that is the tell that this is a cross-product
    problem, not a combinatorial-subset problem.

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time            Space (excl. output)  Mutates input?
    ---------------------------  --------------  ---------------------  ---------------
    Backtracking (path list)     O(4^n * n)      O(n) stack + path      No (digits
                                                                          untouched;
                                                                          path is
                                                                          local)
    itertools.product            O(4^n * n)      O(n) for pools list    No
    Iterative level-by-level     O(4^n * n)      O(4^n) frontier list   No
    String-building recursion    O(4^n * n)      O(n) stack, no path    No

    n = len(digits) <= 4 per the constraints, and each digit maps to at most
    4 letters ('7' and '9'). Every approach is asymptotically O(4^n * n): the
    4^n leaves, each costing O(n) to materialise as a string. The differences
    below are constant-factor, and are exactly the kind of thing that matters
    at n <= 4 but would not change which approach you pick.

    "Mutates input?" is "No" everywhere here for the same reason as 009: the
    input is two small values (well, one string) with no output-array
    aliasing risk the way arrays have in earlier topics.

================================================================================
EDGE CASES
================================================================================
    digits = ""       -> MUST return [], not [""]. The empty-product default
                          of "one way to do nothing" is a real trap here
                          because it exactly matches the correct answer for
                          Subsets/Combinations (C(n,0) = 1, the empty
                          subset) but is WRONG for this problem. Demonstrated
                          live below.

    digits = "2"       -> ["a","b","c"]. Single-digit case exercises the
                          base case with only one level of recursion.

    digits with '7' or '9' -> the only digits mapping to 4 letters, so these
                          are the worst-case branching factor. "7779" has
                          4^4 = 256 leaves, the maximum for n <= 4.

    digits = "22"      -> repeated digit is fine; each position still reads
                          its own copy of the pool, independent of the other
                          position's choice (unlike Combination Sum's shared
                          candidates, there is no cross-position state here
                          at all).

    '0' or '1' in digits -> outside the stated constraints (digits[i] is
                          '2'-'9') but interviewers sometimes ask what
                          happens. A dict-based mapping raises KeyError; a
                          10-slot list mapping with empty strings at index
                          0/1 silently produces zero combinations for that
                          input (the pool is empty, so the branch never
                          fires) — mention which behavior you chose.

================================================================================
COMMON MISTAKES
================================================================================
    1. Returning [""] for digits = "". Base-case pattern-matched from
       Subsets/Combinations, where "no more choices to make" legitimately
       means "the empty combination is a valid answer." Here, no digits
       pressed means NO valid phone combinations exist, full stop — the
       problem statement's own example (Example 2) exists specifically to
       test this. Must special-case `if not digits: return []` (or return an
       empty base-case list explicitly, never [""]).

    2. `results.append(path)` instead of `"".join(path)` or `path[:]`.
       Same copy-on-append trap as every other file here, except that with
       *characters* it is easy to think "well I'm about to `.pop()` it back
       to empty anyway, so it doesn't matter" — it does: `path` is one
       mutable object referenced by every entry in `results` until you
       materialise a string (or copy the list) at record time.

    3. Off-by-one in the base case: `i == len(digits) - 1` instead of
       `i == len(digits)`. Emits combinations one character short — for
       "23" you would silently get ["a","a","a","b","b","b","c","c","c"]
       (stopping after the first digit's choice) rather than the 9 two-
       character strings. Demonstrated live below.

    4. Hardcoding letters as a giant if/elif chain on each digit instead of
       one dict/list lookup. Works, but O(1) dict lookup vs O(10) elif chain
       is the kind of unforced complexity an interviewer will ask you to
       clean up — and the mapping is exactly the kind of static data that
       belongs at module scope, not rebuilt inside the function.

    5. Forgetting the "up to 4^n * n" bound includes the cost of building
       each string. Some candidates say "O(4^n)" and stop, missing the `n`
       factor for materialising each result — small here (n <= 4) but the
       kind of gap an interviewer will probe on a general "how would this
       scale" follow-up.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do it without recursion?
A: Yes — approach 3, level-by-level expansion, or `itertools.product`
   directly. Both are shown and timed below.

Q: What if the phone keypad mapping changes at runtime (not the fixed T9
   layout)?
A: Pass the mapping in as a parameter instead of a module constant; nothing
   else about the algorithm changes — it was never hardcoded past the one
   dict.

Q: Generalize: given `n` lists of strings, produce their Cartesian product.
A: This problem IS that, specialized to n <= 4 lists of size <= 4. The
   iterative level-by-level version (approach 3) is already the general
   solution — swap `mapping[digits[i]]` for `pools[i]`.

Q: How would you generate them lazily instead of building the whole list?
A: Turn `dfs` into a generator: `yield "".join(path)` at the base case
   instead of appending to a results list, and change the caller to iterate.
   Useful if n were large enough that 4^n would not fit in memory (not the
   case here, but the interviewer is testing whether you default to
   "materialise everything" out of habit).

Q: Relate this to Subsets/Permutations/Combinations — same family or not?
A: Different family. Subsets/Permutations/Combinations all draw repeatedly
   from ONE pool with a structural restriction (index order, used-set,
   dedupe). This problem draws from a DIFFERENT pool at each depth and has
   no restriction at all beyond "one choice per position" — it is a
   Cartesian product, not a combinatorial selection.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    CARTESIAN-PRODUCT-SHAPED BACKTRACKING (pool depends on depth/position):
      LC 17   Letter Combinations       - HERE. Pool = mapping[digits[i]].
      LC 22   Generate Parentheses      - pool = {'(', ')'}, filtered by a
                                          feasibility rule instead of a
                                          per-depth mapping.
      LC 1079 Letter Tile Possibilities - Cartesian-ish but WITH a shared
                                          multiset and dedupe (closer to 008).

    THE COMBINATION/SUBSET FAMILY THIS IS *NOT* (contrast, not membership):
      LC 78/90   Subsets / Subsets II    - one pool, index-order restriction.
      LC 46/47   Permutations I/II       - one pool, used[] restriction.
      LC 77/216  Combinations family     - one pool, count/sum restriction.

    The tell for "this is a cross-product problem": the choices at depth d
    depend only on d itself (or on some external structure indexed by d),
    never on which choices were made at other depths. If you find yourself
    reasoning about "what's still available from the shared pool," you are
    back in Subsets/Permutations/Combinations territory, not here.
================================================================================
"""

import time
from itertools import product
from typing import List, Dict


DIGIT_MAP: Dict[str, str] = {
    "2": "abc", "3": "def", "4": "ghi", "5": "jkl",
    "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz",
}


class Solution:
    def letterCombinations(self, digits: str) -> List[str]:
        """Backtracking with a per-depth pool. The answer."""
        if not digits:
            return []

        results: List[str] = []
        path: List[str] = []

        def dfs(i: int) -> None:
            if i == len(digits):
                results.append("".join(path))       # materialise a real copy
                return
            for ch in DIGIT_MAP[digits[i]]:
                path.append(ch)                      # CHOOSE
                dfs(i + 1)                            # EXPLORE
                path.pop()                            # UNCHOOSE

        dfs(0)
        return results

    # ------------------------------------------------------------------
    # Alternatives, kept for the comparisons the tests run.
    # ------------------------------------------------------------------
    def letterCombinations_itertools(self, digits: str) -> List[str]:
        """The production one-liner: build per-digit pools, take their
        Cartesian product."""
        if not digits:
            return []
        pools = [DIGIT_MAP[d] for d in digits]
        return ["".join(combo) for combo in product(*pools)]

    def letterCombinations_iterative(self, digits: str) -> List[str]:
        """Level-by-level (BFS-style) expansion, no recursion at all."""
        if not digits:
            return []
        result = [""]
        for d in digits:
            result = [prefix + ch for prefix in result for ch in DIGIT_MAP[d]]
        return result

    def letterCombinations_string_build(self, digits: str) -> List[str]:
        """Recursion that passes a new string down instead of mutating a
        shared path list. No choose/unchoose needed (strings are immutable)
        but every call allocates."""
        if not digits:
            return []
        results: List[str] = []

        def dfs(i: int, current: str) -> None:
            if i == len(digits):
                results.append(current)
                return
            for ch in DIGIT_MAP[digits[i]]:
                dfs(i + 1, current + ch)

        dfs(0, "")
        return results

    # ------------------------------------------------------------------
    # Deliberately broken — the tests prove these are wrong at runtime.
    # ------------------------------------------------------------------
    def letterCombinations_empty_bug(self, digits: str) -> List[str]:
        """✗ BROKEN — MISTAKE 1: no special-case for digits == "", so the
        base case fires immediately and emits the empty string as if it
        were a valid combination."""
        results: List[str] = []
        path: List[str] = []

        def dfs(i: int) -> None:
            if i == len(digits):
                results.append("".join(path))        # fires with path=[] too
                return
            for ch in DIGIT_MAP[digits[i]]:
                path.append(ch)
                dfs(i + 1)
                path.pop()

        dfs(0)                                        # BUG: no `if not digits`
        return results

    def letterCombinations_off_by_one(self, digits: str) -> List[str]:
        """✗ BROKEN — MISTAKE 3: base case one level too early, so the last
        digit's choices are never applied."""
        if not digits:
            return []
        results: List[str] = []
        path: List[str] = []

        def dfs(i: int) -> None:
            if i == len(digits) - 1:                  # BUG: should be len(digits)
                results.append("".join(path))
                return
            for ch in DIGIT_MAP[digits[i]]:
                path.append(ch)
                dfs(i + 1)
                path.pop()

        dfs(0)
        return results

    def letterCombinations_shared_ref_bug(self, digits: str) -> List[str]:
        """✗ BROKEN — the classic copy-on-append trap, spelled out for
        characters: appends the SAME list object every time instead of a
        joined string or a copy."""
        if not digits:
            return []
        results: List[List[str]] = []                 # will hold aliases
        path: List[str] = []

        def dfs(i: int) -> None:
            if i == len(digits):
                results.append(path)                  # BUG: no copy, no join
                return
            for ch in DIGIT_MAP[digits[i]]:
                path.append(ch)
                dfs(i + 1)
                path.pop()

        dfs(0)
        return ["".join(p) for p in results]           # too late: all aliases
                                                        # already collapsed to []


def _norm(results: List[str]) -> List[str]:
    return sorted(results)


CASES = ["23", "", "2", "7", "22", "79", "234", "7777", "9999", "2345"]


# ==============================================================================
# TESTS — run:  python 010_letter_combinations_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True

    # ----------------------------------------------------------------------
    # 1. Correctness: backtracking vs itertools vs iterative vs string-build.
    # ----------------------------------------------------------------------
    print(f"--- correctness across {len(CASES)} inputs, four independent "
          f"implementations ---")
    impls = [
        ("backtracking (path)  ", sol.letterCombinations),
        ("itertools.product    ", sol.letterCombinations_itertools),
        ("iterative level-by-lv", sol.letterCombinations_iterative),
        ("string-build recurse ", sol.letterCombinations_string_build),
    ]
    oracle = {d: _norm(sol.letterCombinations_itertools(d)) for d in CASES}
    for name, fn in impls:
        bad = [d for d in CASES if _norm(fn(d)) != oracle[d]]
        ok = not bad
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} "
              f"({len(CASES)} inputs{'' if ok else f', failed {bad}'})")

    for d in ["23", "7", "7777"]:
        n = len(sol.letterCombinations(d))
        expected = 1
        for ch in d:
            expected *= len(DIGIT_MAP[ch])
        print(f"      digits={d!r:8} -> {n:>3} results "
              f"(product of pool sizes = {expected})  "
              f"{'match' if n == expected else 'MISMATCH'}")
        all_ok &= (n == expected)

    # ----------------------------------------------------------------------
    # 2. ⚠️ THE EMPTY-STRING TRAP: [] vs [""].
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  digits = \"\": must return [], not [\"\"] ---")
    correct = sol.letterCombinations("")
    buggy = sol.letterCombinations_empty_bug("")
    print(f"  correct implementation -> {correct!r}")
    print(f"  missing-guard implementation -> {buggy!r}")
    trap_demonstrated = (correct == [] and buggy == [""])
    print(f"  trap reproduced (expected [] vs [\"\"])? {trap_demonstrated}")
    all_ok &= trap_demonstrated
    print("  Note this is the OPPOSITE of Subsets: there, 'no more elements to")
    print("  choose from' correctly means 'the empty subset is a valid answer,'")
    print("  i.e. C(n,0)=1. Here it means 'zero valid phone combinations exist.'")
    print("  Pattern-matching the base case from one problem to the other is")
    print("  exactly how this bug gets written.")

    # ----------------------------------------------------------------------
    # 3. ⚠️ THE OFF-BY-ONE BASE CASE.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  base case: i == len(digits) vs i == len(digits) - 1 ---")
    d = "23"
    correct = sorted(sol.letterCombinations(d))
    off = sorted(sol.letterCombinations_off_by_one(d))
    print(f"  digits={d!r}")
    print(f"  correct base case      -> {len(correct)} results: {correct}")
    print(f"  off-by-one base case   -> {len(off)} results: {off}")
    print(f"  off-by-one stops one digit early: every result is missing "
          f"digits[-1]'s contribution ({off == ['a', 'b', 'c']})")
    off_by_one_demonstrated = (correct != off and off == ["a", "b", "c"])
    all_ok &= off_by_one_demonstrated
    print(f"  bug reproduced? {off_by_one_demonstrated}")

    # ----------------------------------------------------------------------
    # 4. ⚠️ THE COPY-ON-APPEND TRAP, for characters.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  copy-on-append trap: appending the live path object ---")
    d = "23"
    correct = sorted(sol.letterCombinations(d))
    aliased = sorted(sol.letterCombinations_shared_ref_bug(d))
    print(f"  digits={d!r}")
    print(f"  correct (join at record time) -> {correct}")
    print(f"  buggy   (append live list)    -> {aliased}")
    alias_bug = (aliased == [""] * len(correct) or all(x == "" for x in aliased))
    print(f"  every entry collapsed to the final (emptied) path -> {alias_bug}")
    all_ok &= alias_bug
    print("  Every entry in `results` was a reference to the SAME `path` list.")
    print("  By the time we join them at the end, every UNCHOOSE step had")
    print("  already popped `path` back down to []. Nine results, nine")
    print("  references to one already-empty list.")

    # ----------------------------------------------------------------------
    # 5. Performance: backtracking vs itertools vs iterative, measured.
    # ----------------------------------------------------------------------
    print("\n--- wall clock: worst case digits='7777' (256 results), "
          "20000 runs ---")
    d = "7777"
    N = 20_000
    timings = []
    for name, fn in (("backtracking (path)  ", sol.letterCombinations),
                      ("itertools.product    ", sol.letterCombinations_itertools),
                      ("iterative level-by-lv", sol.letterCombinations_iterative),
                      ("string-build recurse ", sol.letterCombinations_string_build)):
        t0 = time.perf_counter()
        for _ in range(N):
            fn(d)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        timings.append((name, elapsed_ms))
        print(f"  {name} {elapsed_ms:>9.1f} ms")

    fastest = min(timings, key=lambda t: t[1])
    backtrack_ms = dict(timings)["backtracking (path)  "]
    print(f"  Fastest measured on this machine: {fastest[0].strip()} "
          f"({fastest[1]:.1f} ms), {backtrack_ms / fastest[1]:.1f}x faster "
          f"than the backtracking version.")
    print("  Backtracking pays Python function-call overhead on every one of")
    print("  the ~340 recursive calls per invocation (4+16+64+256); the")
    print("  C-coded iterators avoid that. All are O(4^n * n) — this is a")
    print("  constant-factor difference, not an algorithmic one, and at")
    print("  n <= 4 it will never matter in an interview. Measured, not")
    print("  assumed: do not state this as fact without re-running it.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
