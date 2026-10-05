"""
================================================================================
SOLUTION · LeetCode 278 · First Bad Version                             [Easy]
https://leetcode.com/problems/first-bad-version/
================================================================================

THE CORE IDEA
--------------
There is no array here — `isBadVersion(v)` IS the monotone predicate directly
(topic guide §1.6, the interactive-oracle pattern): false for every good
version, true from the first bad version onward, by the problem's own
guarantee ("all versions after a bad one are also bad"). This is exactly
002's leftmost-True template, with `nums[mid] >= target` replaced by
`isBadVersion(mid)`:

    lo, hi = 1, n
    while lo < hi:
        mid = (lo + hi) // 2
        if isBadVersion(mid):
            hi = mid              # mid might BE the first bad version
        else:
            lo = mid + 1          # mid is good, rule it out
    return lo                     # the first bad version

"Minimize the number of calls to the API" is the tell: a linear scan calling
isBadVersion(1), isBadVersion(2), ... would work but makes up to n calls;
binary search makes O(log n) calls. The array is replaced by a function, but
the mechanism — and the reason to prefer it — is identical.


================================================================================
WHY VERSIONS START AT 1, NOT 0
================================================================================
The problem numbers versions [1 .. n], not [0 .. n-1]. `lo = 1` (not 0)
matters: version 0 doesn't exist, and calling `isBadVersion(0)` would be
calling the oracle outside its defined domain. This is a small but real trap
— candidates used to 0-indexed array problems sometimes default to `lo = 0`
out of habit without checking the problem's actual numbering.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 5, first bad version = 4

    lo=1 hi=5   mid=3   isBadVersion(3)=False -> lo = 4
    lo=4 hi=5   mid=4   isBadVersion(4)=True  -> hi = 4
    lo=4 hi=4   loop ends -> return 4   ✓

    versions:  1     2     3     4     5
               good  good  good  BAD   BAD
                           mid1        (first check: 3, good)
                                 mid2  (second check: 4, bad -> this is it)

Only 2 calls to isBadVersion for n=5. A linear scan would need up to 4 calls
(check 1, 2, 3, 4) in the worst case shown here, and the gap widens sharply
as n grows — the runtime demo below measures actual call counts.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time      Space   Mutates input?  Note
    ---------------------------  --------  ------  ---------------  --------------------
    Linear scan (call 1..n)      O(n)      O(1)    no               correct, too many calls
    Binary search (leftmost) ✅  O(log n)  O(1)    no               the answer;
                                                                    minimizes API calls


================================================================================
EDGE CASES
================================================================================
    n == 1, version 1 is bad    -> lo == hi == 1 immediately, 0 iterations needed.
    bad == 1 (every version bad) -> the very first check already returns True;
                                    loop still correctly narrows down to 1.
    bad == n (only the last is bad) -> loop must not stop early; every check
                                        before n must return False, narrowing
                                        lo all the way up to n.
    n very large (near 2^31 - 1) -> `lo + hi` in Python has no overflow risk
                                    (topic guide §1.2b); the loop still only
                                    takes ~31 iterations.


================================================================================
COMMON MISTAKES
================================================================================
1. `lo = 0` instead of `lo = 1` — versions are 1-indexed by the problem
   statement; calling isBadVersion(0) is out of the API's defined domain.
2. `hi = mid - 1` instead of `hi = mid` when `isBadVersion(mid)` is True —
   discards a `mid` that might BE the first bad version.
3. Calling `isBadVersion` more than once per iteration (e.g. once to check,
   once to log) — the whole point of the problem is minimizing calls; this
   doubles the call count for no benefit.
4. Linear-scanning "because the oracle is simple" — technically correct but
   throws away the entire point (minimize calls) that the problem is testing.
5. Not recognising this as the SAME template as 002 just because there's no
   visible array — see topic guide §1.6: the oracle IS the predicate.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if isBadVersion() were expensive (e.g. a network call with real
   latency)?
A: Binary search's O(log n) call count becomes even more valuable — this is
   exactly the scenario the "minimize API calls" constraint is simulating.

Q: What if you don't know n in advance (versions are effectively unbounded)?
A: "Exponential/galloping search": start hi=1 and double it (isBadVersion(1),
   isBadVersion(2), isBadVersion(4), isBadVersion(8), ...) until a bad version
   is found, establishing a valid [lo, hi] bracket in O(log(bad)) calls, then
   binary search within that bracket — still O(log(bad)) total, without ever
   needing to know n up front.

Q: How is this different from problem 004 (Guess Number Higher or Lower)?
A: 004's oracle returns three states (-1/0/1) instead of a boolean, but
   collapsing it to `guess(mid) <= 0` reduces it to this exact same
   leftmost-True search — see 004's solution file for the direct mapping.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 35   Search Insert Position   — the array-backed sibling (002 here)
    LC 374  Guess Number Higher/Lower — 3-way oracle collapsed to 2-way (004)
    LC 981  Time Based Key-Value Store — bisect over a naturally sorted list
                                          (009 here), no oracle needed
================================================================================
"""

import time


# The isBadVersion API is provided in this module as a module-level function
# (in a real interview, it is provided externally / pre-defined). Tests
# monkeypatch this name to install different scenarios.
def isBadVersion(version: int) -> bool:
    raise NotImplementedError


class Solution:
    def firstBadVersion(self, n: int) -> int:
        """Leftmost-True binary search over the oracle. O(log n) API calls,
        O(1) space. See THE CORE IDEA above."""
        lo, hi = 1, n
        while lo < hi:
            mid = (lo + hi) // 2
            if isBadVersion(mid):
                hi = mid
            else:
                lo = mid + 1
        return lo

    def firstBadVersion_linear(self, n: int) -> int:
        """O(n) oracle: check every version from 1 upward. Used only to
        cross-check correctness and to count/compare API calls."""
        for v in range(1, n + 1):
            if isBadVersion(v):
                return v
        return -1  # not reached under this problem's guarantees


# ==============================================================================
# Instrumented oracle — counts calls so the demo can measure them for real.
# ==============================================================================
class CountingOracle:
    def __init__(self, bad: int):
        self.bad = bad
        self.calls = 0

    def __call__(self, version: int) -> bool:
        self.calls += 1
        return version >= self.bad


# ==============================================================================
# TESTS — run:  python 003_first_bad_version_solution.py
# ==============================================================================
import sys

CASES = [
    (5, 4),
    (1, 1),
    (2, 1),
    (2, 2),
    (10, 1),
    (10, 10),
    (2000000000, 1500000000),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    module = sys.modules[__name__]

    print("--- correctness ---")
    for n, bad in CASES:
        module.isBadVersion = lambda v, _bad=bad: v >= _bad
        got = sol.firstBadVersion(n)
        ok = got == bad
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:<12} bad={bad:<12} -> {got}  (want {bad})")

    print("\n--- cross-check vs. linear-scan oracle (small n only) ---")
    for n, bad in [(5, 4), (1, 1), (10, 1), (10, 10), (25, 13)]:
        module.isBadVersion = lambda v, _bad=bad: v >= _bad
        a = sol.firstBadVersion(n)
        b = sol.firstBadVersion_linear(n)
        ok = a == b == bad
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:<6} bad={bad:<6} binary={a} linear={b}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: n=5, bad=4 ---")
    n, bad = 5, 4
    module.isBadVersion = lambda v, _bad=bad: v >= _bad
    lo, hi = 1, n
    print(f"  {'lo':>3} {'hi':>3} {'mid':>4} {'isBadVersion(mid)':>18}")
    while lo < hi:
        mid = (lo + hi) // 2
        b = module.isBadVersion(mid)
        print(f"  {lo:>3} {hi:>3} {mid:>4} {str(b):>18}")
        if b:
            hi = mid
        else:
            lo = mid + 1
    print(f"  final lo == hi == {lo} -> first bad version is {lo}")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: actual API-call counts, binary search vs linear scan.
    # ----------------------------------------------------------------------
    print("\n--- API call count: binary search vs linear scan ---")
    print(f"  {'n':>12} {'bad':>12} {'binary calls':>13} {'linear calls':>13} {'ratio':>8}")
    for n, bad in ((100, 87), (10_000, 9_999), (1_000_000, 1), (2_000_000_000, 1_500_000_000)):
        oracle_bin = CountingOracle(bad)
        module.isBadVersion = oracle_bin
        sol.firstBadVersion(n)

        # Linear scan is only feasible to actually run for small n; for large
        # n we compute its call count analytically (it's exactly `bad`, by
        # construction: it must check every version from 1 up to and
        # including the first bad one).
        if n <= 20_000:
            oracle_lin = CountingOracle(bad)
            module.isBadVersion = oracle_lin
            sol.firstBadVersion_linear(n)
            lin_calls = oracle_lin.calls
        else:
            lin_calls = bad  # linear scan must call isBadVersion(1..bad)

        ratio = lin_calls / oracle_bin.calls if oracle_bin.calls else float("inf")
        print(f"  {n:>12} {bad:>12} {oracle_bin.calls:>13} {lin_calls:>13} {ratio:>7.1f}x")
    print("  Binary search's call count grows with log(n); linear scan's call")
    print("  count grows with `bad` itself — for a huge n with the bad version")
    print("  deep in the range, the gap becomes enormous, which is exactly what")
    print("  'minimize the number of calls to the API' is testing.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
