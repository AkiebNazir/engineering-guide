"""
================================================================================
SOLUTION · LeetCode 678 · Valid Parenthesis String                     [Medium]
https://leetcode.com/problems/valid-parenthesis-string/
================================================================================

THE CORE IDEA
--------------
Instead of tracking one running "unmatched open-paren count" (impossible
here, since a `*` could resolve to three different things), track a RANGE
`[lo, hi]`: the minimum and maximum possible count of unmatched `(` after
processing each character, treating every `*` as optimistically as possible
for `hi` and as pessimistically as possible for `lo`, simultaneously, in one
pass. `(` increments both bounds. `)` decrements both bounds. `*` decrements
`lo` (pretend it's `)`) and increments `hi` (pretend it's `(`) — since a
single pass can't know in advance which interpretation of `*` will be
needed, tracking the FULL achievable range at each step captures every live
possibility without branching. If `hi` ever drops below 0, no interpretation
of any `*` so far can save it — fail immediately. Clamp `lo` at 0 (an
unmatched-open count can't be negative — a `)` that isn't yet matched by a
prior real or starred `(` just doesn't reduce `lo` below "already at zero
open parens," since `lo` represents the BEST possible reading, and treating
one more `*` as `(` is always an option going forward). At the end, `s` is
valid iff `lo == 0` is achievable, i.e. `lo` reached 0 at some point that
survives to the end — concretely, valid iff `lo == 0` after the full scan.

EXCHANGE ARGUMENT (why tracking `[lo, hi]` instead of branching on every `*`
is safe and sufficient)
-------------------------------------------------------------------
Claim: at every prefix, the SET of achievable "unmatched open count" values
across all 3^(number of stars so far) interpretations of the stars seen so
far is always exactly the contiguous integer range `[lo, hi]` (not some
scattered subset) — so tracking only the two endpoints loses no information
about which values are reachable. Proof by induction: the base case (no
characters) is the range `[0, 0]`. Inductive step: suppose after processing
some prefix the achievable set is exactly `[lo, hi]` (contiguous). Consider
the next character:
- `(`: every achievable value shifts up by 1 -> new range `[lo+1, hi+1]`,
  still contiguous.
- `)`: every achievable value shifts down by 1 -> `[lo-1, hi-1]`, clamped
  at 0 since counts can't go negative (any interpretation that WOULD go
  negative is simply invalid/discarded, not still "achievable" — and the
  remaining achievable values still form a contiguous range because
  clamping a contiguous range at a floor keeps it contiguous).
- `*`: for each value `v` currently achievable, BOTH `v-1` (treat as `)`)
  and `v+1` (treat as `(`) become achievable (as does staying at `v`, via
  the empty-string interpretation, but that's already covered since `v-1,
  v, v+1` union across a contiguous range collapses to `[lo-1, hi+1]`
  after clamping) -> new range `[max(0, lo-1), hi+1]`, still contiguous.

Since contiguity is preserved at every step, `[lo, hi]` fully and exactly
characterizes reachability at every prefix — no case is ever lost by
summarizing with just two numbers instead of exploring all 3^k star
interpretations explicitly. That is the complete justification for why this
greedy range-tracking is not an approximation but an EXACT algorithm.

================================================================================
APPROACH 0 · Brute force — try every interpretation of every '*' (priced,
not coded as the answer)
================================================================================
For each `*`, try substituting `(`, `)`, or `""`, recursively check
validity of the resulting string with a standard balance counter. 3^k
interpretations for k stars — exponential; never the coded answer given
`s.length` up to 100 (up to 100 stars possible).

================================================================================
APPROACH 1 · Greedy [lo, hi] range tracking ✅ (the answer)
================================================================================
    def checkValidString(s):
        lo = hi = 0
        for c in s:
            if c == '(':
                lo += 1; hi += 1
            elif c == ')':
                lo -= 1; hi -= 1
            else:  # '*'
                lo -= 1; hi += 1
            if hi < 0:
                return False
            lo = max(lo, 0)
        return lo == 0

    Time:  O(n) — single pass
    Space: O(1)

================================================================================
APPROACH 2 · DP over (index, balance) — dp[i][bal] = is this state reachable
================================================================================
    dp = {0}                       # set of currently-achievable balances
    for c in s:
        nxt = set()
        for bal in dp:
            if c in '(*':
                nxt.add(bal + 1)
            if c in ')*':
                if bal - 1 >= 0:
                    nxt.add(bal - 1)
        dp = nxt
    return 0 in dp

O(n^2) worst case (the achievable-balance set can have up to n distinct
values, updated n times) and O(n) space. This is the EXPLICIT version of
exactly what Approach 1's `[lo, hi]` proves is always a contiguous range —
Approach 2 tracks every individual reachable balance as a full set/table,
where Approach 1 proves (by the induction above) that the set is ALWAYS an
interval, so two integers suffice instead of an up-to-n-sized set. This is
the topic guide §2.3 canonical illustration of "DP explores, greedy
collapses."

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
s = "(*))"

  lo=0, hi=0
  c='(': lo=1, hi=1.  hi>=0 ok. lo=max(1,0)=1
  c='*': lo=0, hi=2.  hi>=0 ok. lo=max(0,0)=0
  c=')': lo=-1, hi=1. hi>=0 ok. lo=max(-1,0)=0
  c=')': lo=-1, hi=0. hi>=0 ok. lo=max(-1,0)=0

  end of string: lo == 0 -> True
  (one valid reading: treat '*' as empty -> "())" is NOT valid; treat '*'
   as ')' -> "()))" is NOT valid; treat '*' as '(' -> "(())" IS valid, and
   dropping the trailing structure is not needed since "(())" has length 4
   matching len(s)=4 with '*' consuming one slot as '(' -- the point of
   this trace is the MECHANICAL bound tracking, not manual re-derivation;
   `lo == 0` at the end certifies SOME valid reading exists, and the
   brute-force cross-check in run_tests() verifies this exhaustively.)

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                          | Time     | Space | Mutates input? |
|--------------------------------------|---------|-------|------------------|
| 0 · brute force (3^k star readings)  | O(3^k)  | O(n)  | No             |
| 1 · greedy [lo, hi] range ✅          | O(n)    | O(1)  | No             |
| 2 · DP over reachable balances        | O(n^2)  | O(n)  | No             |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Empty-equivalent all-stars string, e.g. "***": every `*` can be treated
  as empty, `lo` and `hi` track `[-1,1] -> clamp lo to 0 -> [0,1] -> [-1,2]
  clamp -> [0,2] -> ...`; ends with `lo == 0` reachable -> True.
- A lone ")" with no preceding '(' or '*': `hi` goes negative immediately
  (`hi = -1 < 0`) -> correctly returns False right away, no way to recover.
- A lone "(" with nothing after: ends with `lo == 1` (never reached 0) ->
  correctly False (an unmatched open paren with nothing to close it, and no
  `*` available to erase it).
- String of only '(' and ')' with no stars at all: `lo == hi` throughout
  (both bounds move identically), degenerating exactly into the classic
  single-counter balanced-parens check — a nice sanity check that this
  algorithm subsumes the simpler one.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Looks-greedy-but-wrong: treating every '*' as '(' first and only
   converting to ')' when a later ')' has nothing to match** — a single
   fixed-strategy greedy (committing to one interpretation per '*' instead
   of tracking the full achievable range) can lock in a choice that turns
   out to be wrong later with no way to backtrack, unlike the range
   approach which keeps every live possibility open until it's proven
   impossible.
2. Forgetting to clamp `lo` at 0 after every step — without the clamp,
   `lo` can go spuriously negative and never correctly reach exactly 0 at
   the end even when a valid reading exists, because a negative `lo` is
   claiming "there could be an excess of closes we haven't matched yet,"
   which isn't a real, valid intermediate state (you can't have a
   negative count of unmatched opens; that would mean an invalid prefix,
   which the `hi < 0` check — not `lo` — is responsible for catching).
3. Checking `hi == 0` instead of `lo == 0` at the end — `hi` reaching 0 only
   means the BEST-CASE interpretation could close everything; the string is
   only guaranteed valid if 0 is actually contained in the achievable range
   `[lo, hi]`, and since `lo` is the floor of that range, `lo == 0` (after
   proper clamping at every step) is exactly the correct final check —
   `hi == 0` alone would wrongly reject strings where 0 is achievable but
   isn't the tightest upper bound.
4. Returning early as soon as `lo == 0` mid-string, instead of continuing
   to scan the rest of `s` — reaching 0 unmatched opens at some middle
   point doesn't mean the string is valid; characters after that point
   still need to be processed (e.g. a trailing lone ')' after a balanced
   prefix would still need to fail).

--------------------------------------------------------------------------------
RUNTIME DEMO — O(n) greedy range vs. O(n²) DP-over-balances, measured on
this machine
--------------------------------------------------------------------------------
See the code below.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if there were multiple bracket TYPES mixed with wildcards (e.g.
  '(', '[', '*')?" — the contiguous-range argument breaks (different
  bracket types aren't interchangeable the way all '(' are), typically
  needs real backtracking or a more general DP over stack states.
- "Can you also RETURN one valid assignment of the stars, not just
  True/False?" — track, alongside `lo`/`hi`, which choice was taken at
  each step (harder to do cleanly with just two scalars; often easier via
  the DP-over-balances version with parent pointers, or a second pass
  reconstructing a specific valid reading once you know one exists).
- "Prove the contiguous-range invariant" — be ready to give the induction
  argument above; interviewers sometimes push on exactly why two numbers
  suffice instead of a full reachable-set.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 06 Stack & Monotonic Stack topic · Valid Parentheses (no wildcards) —
  the simple single-counter/stack version this problem generalizes.
- 18/005 Gas Station — another "single running scalar summarizes an entire
  set of live possibilities" greedy, though there it's a single number, not
  a range.
================================================================================
"""

import random
import time
from functools import lru_cache


class Solution:
    def checkValidString(self, s: str) -> bool:
        lo = hi = 0
        for c in s:
            if c == "(":
                lo += 1
                hi += 1
            elif c == ")":
                lo -= 1
                hi -= 1
            else:  # '*'
                lo -= 1
                hi += 1
            if hi < 0:
                return False
            lo = max(lo, 0)
        return lo == 0


def check_valid_string_dp(s: str) -> bool:
    reachable = {0}
    for c in s:
        nxt = set()
        for bal in reachable:
            if c in "(*":
                nxt.add(bal + 1)
            if c in ")*":
                if bal - 1 >= 0:
                    nxt.add(bal - 1)
            if c == "*":
                nxt.add(bal)  # '*' as the empty string: balance unchanged
        reachable = nxt
        if not reachable:
            return False
    return 0 in reachable


def check_valid_string_brute_force(s: str) -> bool:
    """Try every interpretation of every '*' explicitly. Exponential --
    oracle only, for tiny inputs."""

    @lru_cache(maxsize=None)
    def rec(i: int, bal: int) -> bool:
        if bal < 0:
            return False
        if i == len(s):
            return bal == 0
        c = s[i]
        if c == "(":
            return rec(i + 1, bal + 1)
        if c == ")":
            return rec(i + 1, bal - 1)
        # '*': try all three interpretations
        return rec(i + 1, bal + 1) or rec(i + 1, bal - 1) or rec(i + 1, bal)

    result = rec(0, 0)
    rec.cache_clear()
    return result


def run_tests():
    sol = Solution()
    assert sol.checkValidString("()") is True
    assert sol.checkValidString("(*)") is True
    assert sol.checkValidString("(*))") is True
    assert sol.checkValidString(")") is False
    assert sol.checkValidString("(") is False
    assert sol.checkValidString("***") is True
    assert sol.checkValidString("(*") is True
    assert sol.checkValidString(")*(") is False

    # cross-check against both DP and exponential brute force
    random.seed(47)
    for _ in range(300):
        n = random.randint(1, 10)
        s = "".join(random.choice("()*") for _ in range(n))
        expected = check_valid_string_brute_force(s)
        assert sol.checkValidString(s) == expected, f"greedy mismatch on {s!r}"
        assert check_valid_string_dp(s) == expected, f"DP mismatch on {s!r}"

    # --- Runtime demo: O(n) greedy vs O(n^2) DP-over-balances, measured -----
    random.seed(53)
    n = 6000
    big = "".join(random.choice("()*") for _ in range(n))

    t0 = time.perf_counter()
    fast_result = sol.checkValidString(big)
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    slow_result = check_valid_string_dp(big)
    slow_time = time.perf_counter() - t0

    assert fast_result == slow_result
    print(f"n={n}: greedy [lo,hi] range O(n) took {fast_time*1000:.3f} ms")
    print(f"n={n}: DP over reachable balances took {slow_time*1000:.2f} ms")
    print(f"greedy is {slow_time / fast_time:.1f}x faster on this run")
    assert fast_time < slow_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
