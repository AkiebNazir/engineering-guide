"""
================================================================================
SOLUTION · LeetCode 45 · Jump Game II                                  [Medium]
https://leetcode.com/problems/jump-game-ii/
================================================================================

THE CORE IDEA
--------------
Think in "levels," like BFS on an implicit graph where each index is a node
and `nums[i]` defines edges to every index in `[i+1, i+nums[i]]`. Level 0 is
just index 0; level 1 is every index reachable in one jump from level 0;
level 2 is every NEW index reachable in one more jump from anything in level
1; and so on. The answer is the level number that first includes the last
index. You don't need to build the graph or do real BFS with a queue,
though — because jump RANGES are contiguous intervals of indices, you can
track "the current level's range" as just two numbers, `[level_start,
level_end]`, and a running `farthest` (the best reach achievable from
anywhere still inside the current level). When the scan index passes
`level_end`, you've exhausted the current level — increment the jump count
and advance `level_end` to `farthest`.

EXCHANGE ARGUMENT (why greedily maximizing reach *within* a level is safe)
-------------------------------------------------------------------
Claim: among all indices in the current BFS level, the level-count-minimal
strategy never needs to know WHICH specific index in the level you jump
from next — only the single number "farthest reachable from anywhere in
this level" matters for determining the NEXT level's boundary. Proof: BFS
level structure means every index in the current level is reachable in the
same number of jumps (that's the definition of a level). From the
perspective of "how far can level k+1 extend," it is exactly
`max over all i in level k of (i + nums[i])` — a pure aggregate, order- and
identity-independent. Any jump SEQUENCE that ends inside level k, followed
by one more jump to the farthest point achievable from level k, is optimal
by definition of "level" (BFS visits nodes in strictly non-decreasing
distance order, and greedily extending the frontier as far as possible each
level is exactly what makes BFS distance-optimal in an unweighted graph).
This is the standard "BFS finds shortest paths in unweighted graphs" proof,
specialized to this problem's implicit interval-graph structure — collapsing
each level to a single `farthest` scalar loses no information because all
indices in a level are answer-equivalent for the purpose of extending to
the next level.

================================================================================
APPROACH 0 · Brute-force / backtracking — try every jump length recursively
================================================================================
From each index, recursively try every jump length up to `nums[i]`, take the
minimum jumps over all paths that reach the end. O(2^n) worst case. Useless
past tiny n but easy to state as the naive baseline before optimizing.

================================================================================
APPROACH 1 · Greedy BFS-by-levels ✅ (the answer)
================================================================================
    def jump(nums):
        n = len(nums)
        jumps = 0
        level_end = 0
        farthest = 0
        for i in range(n - 1):
            farthest = max(farthest, i + nums[i])
            if i == level_end:
                jumps += 1
                level_end = farthest
        return jumps

    Time:  O(n) — single pass, each index visited once
    Space: O(1)

================================================================================
APPROACH 2 · DP — dp[i] = min jumps to reach index i
================================================================================
    dp = [inf] * n
    dp[0] = 0
    for i in range(n):
        for j in range(i + 1, min(i + nums[i], n - 1) + 1):
            dp[j] = min(dp[j], dp[i] + 1)
    return dp[n - 1]

O(n^2) worst case (each index can update up to n later indices) and O(n)
space. Correct — same contrast as 18/003: the DP explores dp[i] for every
individually reachable index as a separate state, where the greedy level
scan proves the whole frontier collapses to two scalars (`level_end`,
`farthest`) per level, so the O(n^2) exploration is provably unnecessary
here.

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
nums = [2, 3, 1, 1, 4]   (n = 5, loop runs i = 0..3, skips the last index)

  jumps=0, level_end=0, farthest=0

  i=0: farthest = max(0, 0+2) = 2
       i(0) == level_end(0)? yes -> jumps=1, level_end=2
       (level 1 = indices {1, 2}: everything reachable in 1 jump from index 0)

  i=1: farthest = max(2, 1+3) = 4
       i(1) == level_end(2)? no

  i=2: farthest = max(4, 2+1) = 4
       i(2) == level_end(2)? yes -> jumps=2, level_end=4
       (level 2 extends the frontier to index 4, which IS the last index)

  i=3: farthest = max(4, 3+1) = 4
       i(3) == level_end(4)? no

  loop ends (range stops before i=4, the last index)
  return jumps = 2   (matches expected output: jump 0->1, then 1->4)

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                     | Time      | Space | Mutates input? |
|--------------------------------|----------|-------|------------------|
| 0 · brute force backtracking   | O(2^n)   | O(n)  | No               |
| 1 · greedy BFS-by-levels ✅     | O(n)     | O(1)  | No               |
| 2 · DP min-jumps table          | O(n^2)   | O(n)  | No               |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single-element array (`n == 1`): the loop range `range(n - 1)` is empty,
  `jumps` stays 0 — correct, you're already at the last index with zero
  jumps needed.
- `nums[0]` alone reaches the end: the very first iteration sets `farthest`
  past `n - 1`; `level_end` becomes that value, but the loop still only
  runs over `range(n - 1)`, so `jumps` correctly ends at 1 without
  overcounting extra levels that were never actually needed.
- Guaranteed-reachable input (per constraints) — the algorithm does not
  need to handle "impossible" the way 18/003 does, so there's no
  `i > farthest` guard here; that check would be needed if reachability
  weren't guaranteed.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Looks-greedy-but-wrong: "always jump exactly `nums[i]` steps"** (the
   literal-maximum-jump-every-time rule) — can overshoot past a better
   staging index and land somewhere with a worse `nums[i]`, producing MORE
   total jumps than the level-based approach. The level scan doesn't
   simulate actual jump choices at all; it only tracks aggregate reach.
2. Looping `for i in range(n)` instead of `range(n - 1)` — updating
   `farthest`/`level_end` using the LAST index's own `nums[n-1]` is
   harmless-but-wasted work at best, and at worst causes an extra
   spurious `jumps += 1` if `i == level_end` triggers exactly at the last
   index after you've already effectively arrived — the `n - 1` bound
   avoids ever "jumping from" the destination itself.
3. Incrementing `jumps` every time `farthest` changes, instead of only when
   the scan index `i` reaches `level_end` — conflates "found a better
   reach" with "exhausted the current level"; these are different events.
4. Confusing this with 18/003 (Jump Game) and returning a boolean or reusing
   that problem's `i > farthest` early-exit — Jump Game II assumes
   reachability is guaranteed and asks for a COUNT, not a boolean.

--------------------------------------------------------------------------------
RUNTIME DEMO — O(n) greedy levels vs. O(n²) DP, measured on this machine
--------------------------------------------------------------------------------
See the code below.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "Return the actual sequence of indices jumped through, not just the
  count" — track, for each level transition, WHICH index achieved the new
  `farthest` (parent pointers), then reconstruct backward from the end.
- "What if reachability isn't guaranteed?" — add the `i > farthest` bail
  from 18/003's Approach 1 (return -1 or similar sentinel on failure).
- "Minimum jumps where some indices are blocked/forbidden to land on?" —
  breaks the simple interval-union argument; more likely needs real BFS
  over the explicit graph rather than the collapsed two-scalar trick.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 18/003 Jump Game — same array, reachability-only (boolean) version; the
  `farthest` idea is shared, but this problem adds the BFS-level counting
  on top.
- Plain BFS shortest-path problems (topic 14) — this is literally BFS with
  an implicit, interval-shaped adjacency list instead of an explicit graph.
================================================================================
"""

import random
import time
from collections import deque


class Solution:
    def jump(self, nums: list[int]) -> int:
        n = len(nums)
        jumps = 0
        level_end = 0
        farthest = 0
        for i in range(n - 1):
            farthest = max(farthest, i + nums[i])
            if i == level_end:
                jumps += 1
                level_end = farthest
        return jumps


def jump_dp(nums: list[int]) -> int:
    n = len(nums)
    dp = [float("inf")] * n
    dp[0] = 0
    for i in range(n):
        limit = min(i + nums[i], n - 1)
        for j in range(i + 1, limit + 1):
            if dp[i] + 1 < dp[j]:
                dp[j] = dp[i] + 1
    return dp[n - 1]


def jump_bfs_explicit(nums: list[int]) -> int:
    """Real BFS over the explicit graph -- used only to cross-check the
    greedy level-scan's correctness (ground truth, not the answer)."""
    n = len(nums)
    if n == 1:
        return 0
    dist = [-1] * n
    dist[0] = 0
    q = deque([0])
    while q:
        i = q.popleft()
        for j in range(i + 1, min(i + nums[i], n - 1) + 1):
            if dist[j] == -1:
                dist[j] = dist[i] + 1
                if j == n - 1:
                    return dist[j]
                q.append(j)
    return dist[n - 1]


def run_tests():
    sol = Solution()
    assert sol.jump([2, 3, 1, 1, 4]) == 2
    assert sol.jump([2, 3, 0, 1, 4]) == 2
    assert sol.jump([0]) == 0
    assert sol.jump([1, 1, 1, 1]) == 3
    assert sol.jump([1, 2]) == 1

    # cross-check against explicit BFS and DP on random (always-reachable) arrays
    random.seed(9)
    trials = 0
    while trials < 200:
        n = random.randint(1, 10)
        arr = [random.randint(1, 4) for _ in range(n)]
        arr[-1] = 0
        # ensure reachability guarantee holds
        if not any(True for _ in [0]):
            continue
        # quick reachability check reusing 18/003's greedy farthest scan
        farthest = 0
        reachable = True
        for i, step in enumerate(arr):
            if i > farthest:
                reachable = False
                break
            farthest = max(farthest, i + step)
        if not reachable:
            continue
        trials += 1
        expected = jump_bfs_explicit(arr)
        assert sol.jump(arr) == expected, f"mismatch on {arr}"
        assert jump_dp(arr) == expected, f"DP mismatch on {arr}"

    original = [2, 3, 1, 1, 4]
    sol.jump(original)
    assert original == [2, 3, 1, 1, 4]

    # --- Runtime demo: O(n) greedy levels vs O(n^2) DP, measured -----------
    n = 2000
    big = [n] * n
    t0 = time.perf_counter()
    fast_result = sol.jump(big)
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    slow_result = jump_dp(big)
    slow_time = time.perf_counter() - t0

    assert fast_result == slow_result == 1
    print(f"n={n}: greedy O(n) levels took {fast_time*1000:.3f} ms")
    print(f"n={n}: DP O(n^2) took {slow_time*1000:.2f} ms")
    print(f"greedy is {slow_time / fast_time:.1f}x faster on this run")
    assert fast_time < slow_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
