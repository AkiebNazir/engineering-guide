"""
================================================================================
SOLUTION · LeetCode 77 · Combinations                                    [Medium]
https://leetcode.com/problems/combinations/
================================================================================

THE CORE IDEA
--------------
Combinations are the third base shape of backtracking, and the one that finally
separates "which elements" from "in what order".

    Subsets       every size,  order irrelevant   -> 2^n results
    Permutations  size n,      order matters      -> n! results
    Combinations  size k,      order irrelevant   -> C(n,k) results

Order-irrelevance is the whole problem. [1,2] and [2,1] are the SAME combination,
so a generator that is free to pick any unused element will emit each answer k!
times. The fix is not a de-duplicating set at the end — it is to make duplicates
unreachable in the first place:

    ONLY EVER PICK AN ELEMENT LARGER THAN THE ONE YOU JUST PICKED.

That single rule forces every path to be strictly increasing. A strictly
increasing sequence has exactly one ordering, so each combination is generated
exactly once. This is the `start` parameter, and it is why `backtrack(i + 1)`
appears instead of `backtrack(start)` or a `used[]` array.

    choose:  pick i from [start .. n]
    explore: recurse with start = i + 1   <- "larger than what I just picked"
    unchoose: pop

THE SECOND IDEA — pruning the hopeless branches
------------------------------------------------
The naive loop runs `for i in range(start, n + 1)`. But if we still need
`k - len(path)` more elements and only `n - i + 1` remain available, a branch
starting at `i` is mathematically incapable of ever reaching size k. It will
recurse all the way down and return nothing.

    need      = k - len(path)
    available = n - i + 1
    keep only while  available >= need   =>   i <= n - need + 1

So the loop bound tightens from `n` to `n - (k - len(path)) + 1`.

This prunes DEAD SUBTREES, not results — the output is identical. How much it
buys you depends entirely on k/n, and the runtime demo below measures exactly
that. Spoiler, because it is the non-obvious part: pruning is nearly worthless
for small k and enormous for k near n. See the table the tests print.

================================================================================
MULTIPLE APPROACHES
================================================================================

1. GENERATE ALL PERMUTATIONS, SORT EACH, DEDUPE  (brute force — priced, not coded)
   Emit all n!/(n-k)! ordered k-tuples, sort each into canonical form, drop
   duplicates with a set. Correct, and hopeless: it does k! times more work than
   necessary and needs O(k * C(n,k)) extra memory just for the set. For n=20,
   k=10 that is 670 billion tuples to produce 184,756 answers. Never do this.

2. BACKTRACKING WITH A `start` INDEX                              <- the answer
   The strictly-increasing rule above. O(k * C(n,k)) time, O(k) stack.

3. BACKTRACKING + THE PRUNING BOUND                       <- the answer, tuned
   Same output, strictly fewer nodes visited. This is what you write in an
   interview once the basic version is on the board and working.

4. INCLUDE / EXCLUDE (binary recursion)
   At each element decide take-it or skip-it, instead of looping. Same tree
   re-shaped into a binary one; depth becomes n rather than k, so the stack is
   O(n). Worth knowing because it is the shape that generalises to DP.

5. ITERATIVE / LIBRARY
   `itertools.combinations(range(1, n+1), k)` is a C-coded version of exactly
   approach 3. Correct answer in an interview: "in production I'd call
   itertools; here is the backtracking it implements."

================================================================================
STEP BY STEP  ·  n = 4, k = 2
================================================================================

Loop bound with pruning: i <= n - (k - len(path)) + 1.
At depth 0 we need 2 more, so i <= 4 - 2 + 1 = 3. Note i = 4 is never tried at
the root: starting at 4 leaves only one element, and you cannot build a pair.

    backtrack(start=1)  path=[]        need 2, bound 3, so i in 1..3
    |
    +-- i=1  path=[1]   backtrack(2)   need 1, bound 4, so i in 2..4
    |   |
    |   +-- i=2  path=[1,2]  len==k  -> EMIT [1,2]   pop
    |   +-- i=3  path=[1,3]  len==k  -> EMIT [1,3]   pop
    |   +-- i=4  path=[1,4]  len==k  -> EMIT [1,4]   pop
    |   pop 1
    |
    +-- i=2  path=[2]   backtrack(3)   need 1, bound 4, so i in 3..4
    |   |
    |   +-- i=3  path=[2,3]  len==k  -> EMIT [2,3]   pop
    |   +-- i=4  path=[2,4]  len==k  -> EMIT [2,4]   pop
    |   pop 2
    |
    +-- i=3  path=[3]   backtrack(4)   need 1, bound 4, so i in 4..4
        |
        +-- i=4  path=[3,4]  len==k  -> EMIT [3,4]   pop
        pop 3

    (i=4 at the root: PRUNED. backtrack(5) could only ever return empty.)

    Result: [1,2] [1,3] [1,4] [2,3] [2,4] [3,4]   = 6 = C(4,2)  correct.

Notice the emitted lists are in lexicographic order for free. That is a
consequence of the increasing-index rule, not an extra sort, and interviewers
sometimes ask for it explicitly.

The state of `path` over time — one shared list, mutated:

    []  [1]  [1,2]  [1]  [1,3]  [1]  [1,4]  [1]  []  [2]  [2,3]  ...

Every EMIT must copy (`path[:]`). `path` itself is about to be mutated back.

================================================================================
COMPLEXITY SUMMARY
================================================================================

    Approach                     Time            Space          Mutates input?
    ---------------------------  --------------  -------------  ---------------
    Permute + sort + dedupe      O(k! * C(n,k))  O(k * C(n,k))  no
    Backtracking (plain)         O(k * C(n,k))   O(k) stack     no
    Backtracking + pruning       O(k * C(n,k))   O(k) stack     no
    Include / exclude            O(k * C(n,k))   O(n) stack     no
    itertools.combinations       O(k * C(n,k))   O(k)           no

    Output size alone is C(n,k) lists of k ints, so O(k * C(n,k)) is a LOWER
    bound for any algorithm that materialises the answer. Backtracking hits it.
    Say this out loud in an interview: it proves the solution is optimal rather
    than merely fast.

    "Space O(k) stack" deliberately excludes the output list. If the interviewer
    counts the output, it is O(k * C(n,k)) and no algorithm can do better.

    Pruning does NOT change the asymptotic class — both versions are
    O(k * C(n,k)) — it changes the constant, sometimes by 800x. The tests
    measure this rather than asserting it.

================================================================================
EDGE CASES
================================================================================

    k == 0     -> exactly one combination, the empty one: [[]].
                  The `len(path) == k` base case fires immediately at the root.
                  A solution that starts by looping instead of checking the base
                  case returns [] here, which is wrong: C(n,0) = 1, not 0.

    k == n     -> exactly one combination, [1..n]. With pruning the tree
                  collapses to a single chain: at every depth the bound equals
                  `start`, so there is never a choice. Good sanity check that
                  the bound arithmetic is right.

    k == 1     -> n combinations, each a singleton. Catches an off-by-one in the
                  loop bound (a wrong bound typically drops n or emits n+1).

    k > n      -> impossible; must return []. Not in LeetCode's constraints
                  (1 <= k <= n <= 20) but interviewers ask. The pruning bound
                  handles it for free: bound = n - k + 1 < 1, so the range is
                  empty and nothing is emitted.

    n == 1, k == 1 -> [[1]]. The smallest non-trivial input.

================================================================================
COMMON MISTAKES
================================================================================

1. `results.append(path)` instead of `results.append(path[:])`.
   Appends a REFERENCE to the one list that is about to be popped. Every entry
   in the output ends up being the same (empty) list. This is the single most
   common backtracking bug in any language with reference semantics.

2. Looping `for i in range(1, n + 1)` instead of `range(start, n + 1)`.
   Drops the increasing-index rule. Note this is WORSE than it first looks: the
   rule was buying two things at once, and both are lost. You no longer get a
   canonical ordering ([1,2] and [2,1] both appear), AND you no longer get
   "each element at most once" ([1,1] appears). The result is the full n^k
   cross product — for n=4,k=2 that is 16 tuples instead of 6. Passing
   `i + 1` down does not save you: a loop that starts at 1 ignores its
   argument. The tests below print both outputs side by side.

3. Recursing `backtrack(i)` instead of `backtrack(i + 1)`.
   Allows re-picking the same element, so you get combinations WITH repetition
   (multisets): [1,1], [2,2] appear. That is actually the right call for
   Combination Sum (LC 39) — which is why knowing the difference matters more
   than memorising one of them.

4. Forgetting `path.pop()`.
   The path grows forever, `len(path) == k` stops matching correctly, and the
   output is garbage. Every `append` needs its matching `pop`, on every path out
   of the function.

5. Off-by-one in the pruning bound.
   `n - (k - len(path))` without the `+ 1` silently drops the last valid
   combination. The k == n case catches this instantly: you get [] instead of
   [[1..n]]. Derive the bound from "available >= need" rather than memorising.

6. `return` after emitting, or forgetting it.
   Once len(path) == k the branch is complete; continuing to loop wastes work
   and, without pruning, can emit oversized paths.

7. Deduping with a set at the end instead of preventing duplicates structurally.
   It produces the right answer while doing k! times too much work, and an
   interviewer will read it as not understanding why `start` exists.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================

Q: Return the combinations in lexicographic order.
A: Already are. The increasing-index rule gives it for free. No sort needed.

Q: What if the input is an arbitrary array, not 1..n?
A: Identical code over indices instead of values: pick nums[i], recurse i+1. If
   the array may contain duplicates and you want distinct combinations, sort it
   first and skip `i > start and nums[i] == nums[i-1]` — that is Subsets II /
   Combination Sum II, the same trick.

Q: Can you do it without recursion?
A: Yes, and it is worth having. Keep the current combination as an array,
   repeatedly find the rightmost element that can be incremented, increment it,
   and refill everything to its right with consecutive values. That is exactly
   how itertools.combinations works internally. O(k) worst case per step,
   amortised O(1).

Q: The k-th combination directly, without generating the earlier ones?
A: Combinatorial number system / "unranking". At each position, count how many
   combinations start with each candidate (C(remaining, need-1)); skip whole
   blocks while the rank exceeds the block size. O(n) instead of O(C(n,k)).
   This comes up as "Permutation Sequence" (LC 60) for the permutation version.

Q: Space is O(k) for the stack — can you avoid recursion depth entirely?
A: The iterative version above uses O(k) for the combination itself and no
   stack. For k <= 20 (LeetCode's constraint) recursion depth is a non-issue;
   for large k in a language with a small stack, it matters.

Q: How would you parallelise it?
A: The subtrees under each root choice are independent. Fan out on the first
   level: worker j handles all combinations starting with j. No shared state,
   no locks — each worker owns its own `path`. Note the subtrees are very
   unbalanced (the i=1 subtree is far bigger than i=n-k+1), so hand out work
   dynamically rather than statically.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================

    THIS IS THE "PICK k, ORDER IRRELEVANT" TEMPLATE. It generalises by changing
    exactly one line — which is the thing worth memorising:

    recurse i+1, each element once      -> Combinations           (LC 77, here)
    recurse i+1, no size limit          -> Subsets                (LC 78)
    recurse i+1, skip dup siblings      -> Subsets II             (LC 90)
    recurse i,   each element reusable  -> Combination Sum        (LC 39)
    recurse i+1, skip dup siblings      -> Combination Sum II     (LC 40)
    recurse i+1, k elements + sum target-> Combination Sum III    (LC 216)
    used[] instead of start             -> Permutations           (LC 46)
    used[] + skip dup siblings          -> Permutations II        (LC 47)

    Also downstream of this exact tree shape:
      LC 22  Generate Parentheses       - same tree, validity-based pruning
      LC 17  Letter Combinations        - cross-product instead of a start index
      LC 131 Palindrome Partitioning    - "start" is a string cut point
      LC 51  N-Queens                   - same skeleton, expensive validity check

    The tell in a problem statement: "all possible", "how many ways", "return
    every ..." plus a size or sum constraint, with n small (n <= 20 or so).
    Small n plus "enumerate everything" is backtracking, essentially always.
================================================================================
"""

import math
import time
from typing import List


class Solution:
    def combine(self, n: int, k: int) -> List[List[int]]:
        """
        Backtracking with the pruning bound. This is the version to write.
        Time O(k * C(n,k)), space O(k) stack excluding output.
        """
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int) -> None:
            if len(path) == k:
                results.append(path[:])          # COPY — path is about to change
                return

            # PRUNE: we need `need` more elements; starting at i leaves
            # `n - i + 1` available. Require available >= need.
            need = k - len(path)
            bound = n - need + 1

            for i in range(start, bound + 1):
                path.append(i)                   # CHOOSE
                backtrack(i + 1)                 # EXPLORE (strictly larger only)
                path.pop()                       # UNCHOOSE

        backtrack(1)
        return results

    # ------------------------------------------------------------------
    # Alternatives, kept for the comparisons the tests run
    # ------------------------------------------------------------------
    def combine_unpruned(self, n: int, k: int) -> List[List[int]]:
        """Correct, but explores subtrees that cannot possibly reach size k."""
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int) -> None:
            if len(path) == k:
                results.append(path[:])
                return
            for i in range(start, n + 1):
                path.append(i)
                backtrack(i + 1)
                path.pop()

        backtrack(1)
        return results

    def combine_include_exclude(self, n: int, k: int) -> List[List[int]]:
        """
        Binary recursion: at each value, take it or skip it.
        Same result set; depth becomes n instead of k, so O(n) stack.
        """
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(i: int) -> None:
            if len(path) == k:
                results.append(path[:])
                return
            if i > n:
                return
            # not enough left to finish, whatever we do
            if k - len(path) > n - i + 1:
                return

            path.append(i)          # include i
            backtrack(i + 1)
            path.pop()

            backtrack(i + 1)        # exclude i

        backtrack(1)
        return results

    def combine_iterative(self, n: int, k: int) -> List[List[int]]:
        """
        No recursion. This is (a readable version of) what itertools does:
        hold the current combination, advance the rightmost element that can
        still move, then refill everything to its right consecutively.
        """
        if k == 0:
            return [[]]
        if k > n:
            return []

        results: List[List[int]] = []
        comb = list(range(1, k + 1))
        while True:
            results.append(comb[:])
            # find rightmost position that can be incremented
            i = k - 1
            while i >= 0 and comb[i] == n - (k - 1 - i):
                i -= 1
            if i < 0:
                return results
            comb[i] += 1
            for j in range(i + 1, k):
                comb[j] = comb[j - 1] + 1

    # ------------------------------------------------------------------
    # Deliberately broken — the tests prove these are wrong at runtime
    # ------------------------------------------------------------------
    def combine_broken_no_start(self, n: int, k: int) -> List[List[int]]:
        """MISTAKE 2: loops from 1 every time. Emits ordered tuples, not combos."""
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(_start: int) -> None:
            if len(path) == k:
                results.append(path[:])
                return
            for i in range(1, n + 1):
                path.append(i)
                backtrack(i + 1)
                path.pop()

        backtrack(1)
        return results

    def combine_broken_no_copy(self, n: int, k: int) -> List[List[int]]:
        """MISTAKE 1: appends the live list instead of a copy."""
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int) -> None:
            if len(path) == k:
                results.append(path)             # BUG: no [:]
                return
            for i in range(start, n + 1):
                path.append(i)
                backtrack(i + 1)
                path.pop()

        backtrack(1)
        return results

    def combine_broken_bound(self, n: int, k: int) -> List[List[int]]:
        """MISTAKE 5: pruning bound missing the +1. Silently drops answers."""
        results: List[List[int]] = []
        path: List[int] = []

        def backtrack(start: int) -> None:
            if len(path) == k:
                results.append(path[:])
                return
            bound = n - (k - len(path))          # BUG: should be ... + 1
            for i in range(start, bound + 1):
                path.append(i)
                backtrack(i + 1)
                path.pop()

        backtrack(1)
        return results


def _norm(results: List[List[int]]):
    return sorted(tuple(r) for r in results)


# ==============================================================================
# TESTS — run:  python 006_combinations_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True

    # ----------------------------------------------------------------------
    # 1. Correctness against itertools as an independent oracle.
    # ----------------------------------------------------------------------
    import itertools

    CASES = [(1, 1), (4, 2), (5, 5), (5, 1), (5, 0), (6, 3), (10, 2), (10, 8), (3, 4)]

    impls = [
        ("backtracking + pruning ", sol.combine),
        ("backtracking, unpruned ", sol.combine_unpruned),
        ("include / exclude      ", sol.combine_include_exclude),
        ("iterative (no stack)   ", sol.combine_iterative),
    ]
    print("--- correctness vs itertools.combinations ---")
    for name, fn in impls:
        ok = True
        for n, k in CASES:
            want = _norm([list(c) for c in itertools.combinations(range(1, n + 1), k)])
            got = _norm(fn(n, k))
            if got != want:
                ok = False
                print(f"      n={n} k={k}: got {len(got)} want {len(want)}")
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # 2. The count is exactly C(n,k) — including the edge cases.
    # ----------------------------------------------------------------------
    print("\n--- result count == C(n,k), including k=0, k=n, k>n ---")
    print(f"  {'n':>3} {'k':>3} {'produced':>10} {'C(n,k)':>10}  match?")
    for n, k in [(4, 2), (5, 0), (5, 5), (5, 1), (10, 3), (3, 4), (20, 20)]:
        produced = len(sol.combine(n, k))
        expected = math.comb(n, k) if k <= n else 0
        match = produced == expected
        all_ok &= match
        print(f"  {n:>3} {k:>3} {produced:>10} {expected:>10}  {'yes' if match else 'NO'}")

    # ----------------------------------------------------------------------
    # 3. ⚠️ MISTAKE 2 — dropping `start` generates permutations, not combos.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  range(start, n+1)  vs  range(1, n+1) ---")
    n, k = 4, 2
    good = sol.combine(n, k)
    bad = sol.combine_broken_no_start(n, k)
    print(f"  correct (start):  {len(good):>2} results  {sorted(good)}")
    print(f"  broken  (from 1): {len(bad):>2} results  {sorted(bad)}")
    distinct_bad = len(set(tuple(sorted(b)) for b in bad))
    with_repeats = sum(1 for b in bad if len(set(b)) < k)
    print(f"  The broken run emits {len(bad)} = n^k = {n}^{k} tuples: the FULL")
    print(f"  cross product. Ignoring `start` costs two separate guarantees, not one:")
    print(f"    - ordering  : [1,2] and [2,1] both appear (k! orderings each)")
    print(f"    - no repeats: {with_repeats} of them repeat an element, e.g. [1,1]")
    print(f"  So it covers {distinct_bad} distinct MULTISETS where only {len(good)} are")
    print(f"  valid combinations. Note `backtrack(i + 1)` is still there and is")
    print(f"  powerless — a loop that restarts at 1 discards the argument entirely.")
    proved = (len(bad) == n ** k) and with_repeats > 0 and distinct_bad > len(good)
    all_ok &= proved

    # ----------------------------------------------------------------------
    # 4. ⚠️ MISTAKE 1 — the copy-on-append trap, live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  results.append(path[:])  vs  results.append(path) ---")
    good = sol.combine(4, 2)
    bad = sol.combine_broken_no_copy(4, 2)
    print(f"  correct: {sorted(good)}")
    print(f"  broken : {bad}")
    corrupted = len(set(tuple(b) for b in bad)) == 1 and bad[0] == []
    print(f"  all {len(bad)} entries are the SAME list object, now empty "
          f"(every append was undone by its pop): {corrupted}")
    all_ok &= corrupted

    # ----------------------------------------------------------------------
    # 5. ⚠️ MISTAKE 5 — the off-by-one bound drops real answers silently.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  pruning bound  n-need+1  vs  n-need  (the missing +1) ---")
    print(f"  {'n':>3} {'k':>3} {'correct':>9} {'off-by-one':>11}  lost")
    bound_bug_seen = False
    for n, k in [(4, 2), (5, 5), (6, 3), (10, 8)]:
        c = len(sol.combine(n, k))
        b = len(sol.combine_broken_bound(n, k))
        if b < c:
            bound_bug_seen = True
        print(f"  {n:>3} {k:>3} {c:>9} {b:>11}  {c - b}")
    print("  The bug never crashes and never emits a WRONG combination —")
    print("  it just silently returns fewer of them. Hardest kind to spot.")
    all_ok &= bound_bug_seen

    # ----------------------------------------------------------------------
    # 6. How much does pruning actually buy? Measured, not asserted.
    # ----------------------------------------------------------------------
    print("\n--- nodes visited: pruned vs unpruned (the real payoff of pruning) ---")

    def count_nodes(n: int, k: int, pruned: bool) -> int:
        count = [0]
        path: List[int] = []

        def backtrack(start: int) -> None:
            count[0] += 1
            if len(path) == k:
                return
            hi = n - (k - len(path)) + 1 if pruned else n
            for i in range(start, hi + 1):
                path.append(i)
                backtrack(i + 1)
                path.pop()

        backtrack(1)
        return count[0]

    print(f"  {'n':>3} {'k':>3} {'C(n,k)':>9} {'pruned':>10} {'unpruned':>10} {'saved':>9}")
    for n, k in [(10, 2), (16, 8), (20, 10), (20, 15), (20, 18), (20, 20)]:
        p = count_nodes(n, k, True)
        u = count_nodes(n, k, False)
        print(f"  {n:>3} {k:>3} {math.comb(n, k):>9} {p:>10} {u:>10} {u / p:>8.1f}x")
    print("  READ THIS TABLE. Pruning is nearly worthless when k is small")
    print("  (k=2: barely 1x — almost every branch can still reach size k) and")
    print("  overwhelming when k approaches n (k=18 of 20: ~800x). At k=n the")
    print("  tree collapses to one chain. 'Add pruning' is not free advice —")
    print("  it pays in proportion to how many branches are actually hopeless.")

    # ----------------------------------------------------------------------
    # 7. The pruned node count is EXACTLY C(n+1, k). Verified, not asserted.
    # ----------------------------------------------------------------------
    print("\n--- the pruned tree visits exactly C(n+1, k) nodes ---")
    identity_ok = True
    print(f"  {'n':>3} {'k':>3} {'nodes':>10} {'C(n+1,k)':>10}  match?")
    for n, k in [(4, 2), (5, 5), (10, 2), (12, 6), (16, 8), (20, 18)]:
        nodes = count_nodes(n, k, True)
        pred = math.comb(n + 1, k)
        m = nodes == pred
        identity_ok &= m
        print(f"  {n:>3} {k:>3} {nodes:>10} {pred:>10}  {'yes' if m else 'NO'}")
    print("  Why: each node is identified by the path taken to reach it, and the")
    print("  pruned tree's nodes biject with the k-subsets of {1..n+1} (the extra")
    print("  element encodes 'stopped early'). Useful as a self-check that your")
    print("  bound is exactly right — an off-by-one breaks the identity at once.")
    all_ok &= identity_ok

    # ----------------------------------------------------------------------
    # 8. Wall-clock, all four correct implementations.
    # ----------------------------------------------------------------------
    print("\n--- wall clock (ms), n=20 ---")
    print(f"  {'n':>3} {'k':>3} {'pruned':>10} {'unpruned':>10} "
          f"{'inc/exc':>10} {'iterative':>10}")
    for n, k in [(20, 4), (18, 9), (20, 16), (20, 18)]:
        ts = []
        for fn in (sol.combine, sol.combine_unpruned,
                   sol.combine_include_exclude, sol.combine_iterative):
            t0 = time.perf_counter()
            fn(n, k)
            ts.append((time.perf_counter() - t0) * 1000)
        print(f"  {n:>3} {k:>3} {ts[0]:>9.2f}ms {ts[1]:>9.2f}ms "
              f"{ts[2]:>9.2f}ms {ts[3]:>9.2f}ms")
    print("  The iterative version wins consistently: no call frames, no")
    print("  append/pop churn — just one array advanced in place. It is also")
    print("  the one you are least likely to get right under pressure, which is")
    print("  why the recursive pruned version is the interview answer.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
