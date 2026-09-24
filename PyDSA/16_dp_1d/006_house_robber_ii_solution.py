"""
================================================================================
SOLUTION · LeetCode 213 · House Robber II                            [Medium]
https://leetcode.com/problems/house-robber-ii/
================================================================================

THE CORE IDEA
--------------
The circular constraint only ever bites on ONE pair: (house 0, house n-1).
Every valid selection either excludes house 0 or excludes house n-1 (both
excluded is a subcase of either). So run the plain House Robber DP
(problem 005) on two linear slices -- nums[0:n-1] and nums[1:n] -- and take
the max. This is Part 4 point 4 of `_TOPIC_GUIDE.md`: a constraint that
LOOKS like it needs a second dimension of state ("is the first house
robbed?") actually decomposes into two independent 1D passes instead.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive: track a "first house robbed" boolean as extra state) --
technically works but turns a clean 1D recurrence into 2D state
(dp[i][robbed_first]) for a constraint that doesn't need it. Same O(n)
time asymptotically but more state to manage and more bug surface (which
combinations of robbed_first are valid at the boundary).

Approach 1 (two linear passes) [chosen] -- reuse House Robber's O(n)
O(1)-space helper on nums[0:n-1] and nums[1:n], return the max. O(n) time
(two passes, still linear), O(1) extra space.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [200, 3, 140, 20, 10]     (circular: house 4 is adjacent to house 0)

Run A -- exclude house 4 (last), rob linearly over [200, 3, 140, 20]:
     i     : 0    1    2     3
    nums[i]: 200  3    140   20
    dp[i]  : 200  200  340   340     <- runA = 340

Run B -- exclude house 0 (first), rob linearly over [3, 140, 20, 10]:
     i     : 0   1    2    3
    nums[i]: 3   140  20   10
    dp[i]  : 3   140  140  150      <- runB = 150

answer = max(runA, runB) = max(340, 150) = 340

(Compare: the LINEAR House Robber on the full array would give 350 by
taking houses 0, 2, 4 -- but houses 0 and 4 are adjacent here, which is
exactly the plan the circular constraint forbids. Run A and Run B never
even consider that combination because each drops one endpoint entirely.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time    Space   Mutates input?
    -------------------------------  ------  ------  --------------
    2D state (robbed_first boolean)  O(n)    O(n)    no
    Two linear passes [chosen]       O(n)    O(1)    no


================================================================================
EDGE CASES
================================================================================
    len(nums) == 1        -> a "circle" of one house is degenerate (house 0
                              would be its own neighbor); must special-case
                              and return nums[0] directly before slicing,
                              since both nums[0:0] and nums[1:1] are empty.
    len(nums) == 2         -> houses 0 and 1 are adjacent BOTH ways around
                              the circle (it's a 2-cycle); answer is
                              max(nums[0], nums[1]), which the two-slice
                              approach gives automatically (each slice has
                              exactly one house).
    all equal values         -> forces genuine tie-breaking between the two
                              runs; both must be computed, not shortcut.
    the optimal linear answer uses BOTH endpoints -> exactly the case the
                              circular constraint must block (traced above).


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the len(nums) == 1 special case and slicing into two empty
   arrays, which a naive linear-rob helper might mishandle (returning 0
   for both, silently losing the only house's money).
2. Running the linear helper on the FULL array by mistake instead of the
   two n-1-length slices -- that reduces to problem 005 and ignores the
   circular constraint entirely, giving a too-high answer.
3. Assuming excluding BOTH endpoints needs a third explicit run -- it
   doesn't, because "exclude both" is always dominated by (or equal to)
   whichever of Run A / Run B doesn't rob the excluded endpoint anyway.
4. Off-by-one in the slicing: nums[0:n-1] and nums[1:n] must each have
   length n-1, not n or n-2.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if it's a circle AND you must also skip at least one full
  'quadrant'?" -> a hint that the state really has grown a second
  dimension; re-derive from scratch rather than forcing this trick.
- "Can you avoid slicing (copying) the array?" -> pass start/end index
  bounds into the House Robber helper instead of nums[a:b], avoiding the
  O(n) copy -- purely a constant-factor / mutates-input consideration
  since the algorithmic complexity is unchanged.
- "House Robber III?" (LC 337) -- houses form a BINARY TREE, not a line or
  circle; that's tree DP (postorder, per-node "rob me or not" pair),
  outside this topic's 1D scope.


================================================================================
RELATED PROBLEMS
================================================================================
- 005 House Robber (LC 198) -- the linear building block reused twice here.
- House Robber III (LC 337) -- tree-shaped version, not 1D.
- 014 Partition Equal Subset Sum -- another problem where a constraint
  that looks like it needs extra dimensions collapses via a clever
  reformulation (there: iteration direction; here: two independent runs).
================================================================================
"""

import time
from typing import List


def _rob_linear(nums: List[int]) -> int:
    prev2, prev1 = 0, 0
    for x in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + x)
    return prev1


class Solution:
    def rob(self, nums: List[int]) -> int:
        n = len(nums)
        if n == 1:
            return nums[0]
        return max(_rob_linear(nums[:-1]), _rob_linear(nums[1:]))


def rob_2d_state(nums: List[int]) -> int:
    """Alternative: explicit (index, robbed_first) 2D state, for comparison.
    Demonstrates that forcing a second dimension onto this problem still
    works but is strictly more bookkeeping than the two-pass decomposition.
    """
    n = len(nums)
    if n == 1:
        return nums[0]

    def solve(skip_last: bool) -> int:
        arr = nums[: n - 1] if skip_last else nums[1:]
        return _rob_linear(arr)

    return max(solve(True), solve(False))


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([2, 3, 2], 3),
        ([1, 2, 3, 1], 4),
        ([1, 2, 3], 3),
        ([1], 1),
        ([1, 2], 2),
        ([5, 5, 5, 5], 10),
        ([200, 3, 140, 20, 10], 340),
    ]
    for nums, want in cases:
        got = sol.rob(nums[:])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  -> {got}  (want {want})")
        assert rob_2d_state(nums[:]) == want

    print()
    print("DEMO -- linear House Robber vs circular House Robber II on the SAME array")
    print("-" * 72)
    demo = [200, 3, 140, 20, 10]
    linear_answer = _rob_linear(demo)
    circular_answer = sol.rob(demo[:])
    print(f"nums={demo}")
    print(f"  linear (005) answer:   {linear_answer}   (robs houses 0, 2, 4 -- the two endpoints)")
    print(f"  circular (006) answer: {circular_answer}   (forbidden to rob both endpoints -- must drop one)")
    assert linear_answer > circular_answer, "circular constraint should strictly cost something here"

    print()
    print("RUNTIME DEMO -- two O(n) linear passes stay linear as n grows")
    print("-" * 72)
    import random
    random.seed(0)
    for n in (1000, 10000, 100000):
        arr = [random.randint(0, 1000) for _ in range(n)]
        t0 = time.perf_counter()
        sol.rob(arr)
        ms = (time.perf_counter() - t0) * 1000
        print(f"n={n:7d}  time={ms:8.3f} ms")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
