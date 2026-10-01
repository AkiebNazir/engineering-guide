"""
================================================================================
SOLUTION · LeetCode 55 · Jump Game                                     [Medium]
https://leetcode.com/problems/jump-game/
================================================================================

THE CORE IDEA
--------------
Track a single running value: `farthest`, the farthest index reachable using
only information seen so far. Scan left to right; at each index `i`, if `i`
is beyond `farthest` you can never get here — fail immediately. Otherwise
update `farthest = max(farthest, i + nums[i])`. If `farthest` ever reaches or
passes the last index, you can reach it.

EXCHANGE ARGUMENT (why tracking only "farthest reachable" is enough)
-------------------------------------------------------------------
Claim: to determine reachability of the last index, you never need to know
WHICH specific sequence of jumps got you to a given farthest point — only
the single number "the farthest index reachable so far" is sufficient
state. Proof: suppose two different jump sequences both reach index `j` (or
farther) using indices <= i. From reachability's perspective they are
completely interchangeable going forward — any index reachable from one is
reachable from the other, since both can "stand at" index j (or beyond) and
jump onward. So the future never depends on HOW you got to the farthest
point, only on the farthest point itself — collapsing all live jump
sequences into one scalar loses no information. That is the exchange
argument: any optimal (reaching) sequence can be replaced by "just track
the running farthest," with identical reachability outcome, so committing
to the scalar summary is safe. This is also exactly why this is greedy and
not DP — DP would explore each reachable index as a separate state; here
all reachable-so-far states collapse into one number.

================================================================================
APPROACH 0 · Brute force — backtracking / try every jump length
================================================================================
From each index, recursively try every jump length from 1 to `nums[i]`, and
see if any path reaches the end. Exponential — O(2^n) worst case (every
index with `nums[i] >= 2` branches). Correct but useless past tiny n; can
be memoized into a DP over index -> reachable, which is Approach 2 below.

================================================================================
APPROACH 1 · Greedy farthest-reachable scan ✅ (the answer)
================================================================================
    def canJump(nums):
        farthest = 0
        for i, step in enumerate(nums):
            if i > farthest:
                return False
            farthest = max(farthest, i + step)
        return True

    Time:  O(n) — single pass
    Space: O(1)

================================================================================
APPROACH 2 · DP — dp[i] = can we ever stand at index i?
================================================================================
    dp[0] = True
    for i in range(n):
        if not dp[i]:
            continue
        for j in range(i + 1, min(i + nums[i], n - 1) + 1):
            dp[j] = True
    return dp[n - 1]

O(n^2) worst case (each index can mark up to n others reachable) and O(n)
space for the table. Correct, but explores every individually-reachable
index as its own state where the greedy scan proves a single running
maximum already captures everything needed — the direct DP-vs-greedy
contrast the topic guide calls out in §3: here the "local state" IS just
one number (farthest), so the table collapses to a scalar and you get the
greedy algorithm for free once you notice that.

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
nums = [2, 3, 1, 1, 4]   (n = 5, last index = 4)

  farthest = 0
  i=0, step=2: i(0) <= farthest(0)? yes. farthest = max(0, 0+2) = 2
  i=1, step=3: i(1) <= farthest(2)? yes. farthest = max(2, 1+3) = 4
  i=2, step=1: i(2) <= farthest(4)? yes. farthest = max(4, 2+1) = 4
  i=3, step=1: i(3) <= farthest(4)? yes. farthest = max(4, 3+1) = 4
  i=4, step=4: i(4) <= farthest(4)? yes. farthest = max(4, 4+4) = 8
  loop ends, no index ever exceeded farthest -> return True

nums = [3, 2, 1, 0, 4]   (n = 5, last index = 4)

  farthest = 0
  i=0, step=3: farthest = max(0, 3) = 3
  i=1, step=2: farthest = max(3, 3) = 3
  i=2, step=1: farthest = max(3, 3) = 3
  i=3, step=0: farthest = max(3, 3) = 3
  i=4: i(4) > farthest(3) -> return False    (can never reach index 4)

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                       | Time      | Space | Mutates input? |
|-----------------------------------|----------|-------|------------------|
| 0 · brute force backtracking     | O(2^n)   | O(n) recursion stack | No |
| 1 · greedy farthest-reachable ✅  | O(n)     | O(1)  | No               |
| 2 · DP reachability table         | O(n^2)   | O(n)  | No               |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single-element array: index 0 IS the last index, loop body runs once,
  `i(0) <= farthest(0)`, returns True without ever needing to jump.
- A 0 at index 0 with n > 1: `farthest` stays 0, the very next index (1)
  exceeds it -> correctly returns False.
- A 0 in the middle that's already "jumped over" by an earlier big step
  (like the True example: index 2 has step 1, but farthest is already 4
  from index 1) — correctly does NOT fail, since you never need to actually
  LAND on the index with the 0.
- All zeros except index 0 in a length > 1 array: only reachable if
  `nums[0] >= n - 1`; otherwise fails at the first unreachable index.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Looks-greedy-but-wrong: "always take the biggest jump available at
   each step"** — a step-count-maximizing greedy, not a reachability one;
   it can walk itself into a 0 unnecessarily when a smaller jump would have
   kept more options open. This problem does NOT need per-step jump
   choices at all — only the running farthest bound — so don't overthink it
   into simulating actual jumps.
2. Checking `farthest >= n - 1` and exiting early INSIDE the loop without
   also guarding `i > farthest` for indices before that point — both
   checks are needed: the early-success check is an optimization, the
   `i > farthest` check is the correctness-critical one.
3. Off-by-one on "last index" — comparing against `n` instead of `n - 1`.
4. Assuming you must be able to jump EXACTLY onto the last index using some
   `nums[i]` step, rather than realizing `farthest` passing `n - 1` is
   sufficient (a jump can overshoot).

--------------------------------------------------------------------------------
RUNTIME DEMO — O(n) greedy vs. O(n²) DP, measured on this machine
--------------------------------------------------------------------------------
See the code below.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What is the MINIMUM number of jumps to reach the end (not just
  can-you)?" — this topic's next problem, 18/004 Jump Game II.
- "What if negative jump lengths (going backward) were allowed?" — the
  farthest-reachable argument breaks (a backward jump can't help forward
  reachability, but changes what state you need to track); typically
  becomes a graph/BFS problem instead.
- "Return the actual sequence of jumps, not just True/False" — greedy
  reachability alone doesn't reconstruct a path; you'd track, for each
  index, which prior index extended `farthest` to include it (parent
  pointers), or switch to the level-based greedy in 18/004.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 18/004 Jump Game II — same array, but minimize the number of jumps
  instead of asking reachability; still greedy but tracks jump "levels."
- 18/005 Gas Station — another running-frontier / feasibility greedy.
- LC 1345 Jump Game IV — same shape but with a graph/BFS twist (jumps to
  equal values), reachability is no longer monotone in index so the
  farthest-scan trick alone doesn't apply.
================================================================================
"""

import random
import time


class Solution:
    def canJump(self, nums: list[int]) -> bool:
        farthest = 0
        for i, step in enumerate(nums):
            if i > farthest:
                return False
            farthest = max(farthest, i + step)
        return True


def can_jump_dp(nums: list[int]) -> bool:
    n = len(nums)
    dp = [False] * n
    dp[0] = True
    for i in range(n):
        if not dp[i]:
            continue
        for j in range(i + 1, min(i + nums[i], n - 1) + 1):
            dp[j] = True
    return dp[n - 1]


def run_tests():
    sol = Solution()
    assert sol.canJump([2, 3, 1, 1, 4]) is True
    assert sol.canJump([3, 2, 1, 0, 4]) is False
    assert sol.canJump([0]) is True
    assert sol.canJump([0, 1]) is False
    assert sol.canJump([1, 0, 1, 0]) is False
    assert sol.canJump([2, 0, 0]) is True
    assert sol.canJump([1, 1, 1, 1]) is True

    # cross-check against DP on random arrays
    random.seed(5)
    for _ in range(300):
        n = random.randint(1, 12)
        arr = [random.randint(0, 4) for _ in range(n)]
        assert sol.canJump(arr) == can_jump_dp(arr), f"mismatch on {arr}"

    original = [2, 3, 1, 1, 4]
    sol.canJump(original)
    assert original == [2, 3, 1, 1, 4]

    # --- Runtime demo: O(n) greedy vs O(n^2) DP, measured -------------------
    n = 2000
    big = [n] * n  # every index can jump anywhere -> DP's inner loop is O(n) each time
    t0 = time.perf_counter()
    fast_result = sol.canJump(big)
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    slow_result = can_jump_dp(big)
    slow_time = time.perf_counter() - t0

    assert fast_result == slow_result is True
    print(f"n={n}: greedy O(n) took {fast_time*1000:.3f} ms")
    print(f"n={n}: DP O(n^2) took {slow_time*1000:.2f} ms")
    print(f"greedy is {slow_time / fast_time:.1f}x faster on this run")
    assert fast_time < slow_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
