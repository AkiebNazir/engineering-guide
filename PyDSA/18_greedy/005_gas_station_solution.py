"""
================================================================================
SOLUTION · LeetCode 134 · Gas Station                                  [Medium]
https://leetcode.com/problems/gas-station/
================================================================================

THE CORE IDEA
--------------
Two facts collapse this into one O(n) scan:

1. **A solution exists at all iff `sum(gas) >= sum(cost)`.** If total gas is
   less than total cost, no starting point can ever work (the whole circuit
   is a net deficit). If total gas >= total cost, a valid starting point is
   GUARANTEED to exist (proof below) — you never need to check "does station
   X work" for every X individually.
2. **The valid start (when one exists) is the station right after the point
   where your running tank total hits its all-time low.** Walk the circuit
   once from any fixed point (say index 0), keeping a running `tank = tank +
   gas[i] - cost[i]`. Whenever `tank` goes negative, NONE of the stations you
   just walked through (from the last reset point to here) can be a valid
   start — reset the candidate start to `i + 1` and reset `tank` to 0.

EXCHANGE ARGUMENT (why "reset to i+1 the moment tank goes negative" is safe)
-------------------------------------------------------------------
Claim: if the running tank starting from candidate `s` goes negative for the
first time upon reaching station `i`, then no station `j` with `s <= j <=
i` can be a valid start either. Proof: for any such `j`, the tank starting
from `j` at station `i` would be `tank_from_s(i) - tank_from_s(j-1)` (you'd
have accumulated strictly LESS net gas than starting from `s`, because
`tank_from_s(j-1) >= 0` for every prefix before the first negative dip —
that's exactly why the dip happens at `i` and not earlier: everything from
`s` up to `j-1` was non-negative, so subtracting a non-negative prefix from
an already-negative total keeps it negative or makes it more negative).
So `tank_from_j(i) <= tank_from_s(i) < 0` — starting from `j` fails at `i`
too. This proves every station between the last reset and the failure point
is provably unable to be a valid answer, so skipping straight to `i + 1` as
the new candidate loses no valid solutions — a complete exchange argument,
not just an assumption.

**Why a solution is guaranteed when total gas >= total cost**: think of the
running tank (extended if needed, starting from 0) as a function on the
circuit; running it around the FULL loop returns you to a running sum equal
to `sum(gas) - sum(cost) >= 0`. The station immediately after the GLOBAL
minimum of that running sum is a valid start, because from there onward the
running total (relative to that low point) never dips below zero again
before completing the loop back to the low point — a standard "prefix sum
minimum" argument (same shape as topic 04's prefix-sum reasoning, but used
here to justify a greedy pick instead of a hashmap lookup).

================================================================================
APPROACH 0 · Brute force — try every starting station (priced, not coded)
================================================================================
For each candidate start `s` (n choices), simulate the full circuit (O(n)
each): O(n^2) total. Correct, and the natural first idea, but quadratic —
too slow for n up to 10^5.

================================================================================
APPROACH 1 · Single-pass greedy ✅ (the answer)
================================================================================
    def canCompleteCircuit(gas, cost):
        if sum(gas) < sum(cost):
            return -1
        start = 0
        tank = 0
        for i in range(len(gas)):
            tank += gas[i] - cost[i]
            if tank < 0:
                start = i + 1
                tank = 0
        return start

    Time:  O(n) — one pass for the sum check (or fold into the same loop),
           one pass for the scan
    Space: O(1)

================================================================================
APPROACH 2 · DP framing (for contrast, not worth coding)
================================================================================
You could imagine a DP over "is station i a feasible start" as a function of
"is station i+1 a feasible start plus the local deficit/surplus," but this
doesn't actually reduce work versus the O(n^2) brute force UNLESS you notice
the same prefix-sum-minimum structure Approach 1 exploits — at which point
you've rediscovered Approach 1. This problem doesn't have a genuine "look
two ways, remember both, pick the best later" DP shape; once you find the
exchange argument, the greedy collapse is total. Worth saying out loud in an
interview ("I don't think this needs a DP table because ...") to show you
considered and ruled it out, not just guessed greedy.

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
gas  = [1, 2, 3, 4, 5]
cost = [3, 4, 5, 1, 2]
sum(gas)=15, sum(cost)=15 -> 15 >= 15, a solution exists

  start=0, tank=0
  i=0: tank += 1-3 = -2   -> tank=-2 < 0: start=1, tank=0
  i=1: tank += 2-4 = -2   -> tank=-2 < 0: start=2, tank=0
  i=2: tank += 3-5 = -2   -> tank=-2 < 0: start=3, tank=0
  i=3: tank += 4-1 = +3   -> tank=3, no reset
  i=4: tank += 5-2 = +3   -> tank=6, no reset

  loop ends, return start = 3   (matches expected output)

gas  = [2, 3, 4]
cost = [3, 4, 3]
sum(gas)=9, sum(cost)=10 -> 9 < 10: return -1 immediately, no scan needed

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                  | Time    | Space | Mutates input? |
|------------------------------|--------|-------|------------------|
| 0 · brute force (all starts) | O(n^2) | O(1)  | No              |
| 1 · single-pass greedy ✅     | O(n)   | O(1)  | No              |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- n == 1: only one station; feasible iff `gas[0] >= cost[0]`, and the loop
  correctly returns 0 in that case (start never resets past index 0), or
  the upfront sum check already returns -1 otherwise.
- `sum(gas) == sum(cost)` exactly (zero surplus): still guaranteed feasible
  — the guarantee only needs `>=`, not strict `>`; the trace above is
  exactly this case (15 == 15) and it succeeds.
- All stations individually deficient (`gas[i] < cost[i]` everywhere) but
  total sums equal: still works — no single station needs to be
  individually sufficient, only the CUMULATIVE running tank from the
  correct start needs to stay non-negative.
- The reset happens on the very last index: `start` becomes `n`, which
  would be out of bounds as an index — but this can only happen when
  `tank` is negative at the end of the full loop, which contradicts
  `sum(gas) >= sum(cost)` (the upfront check), so this never actually
  occurs when the function proceeds past that check.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Looks-greedy-but-wrong: checking each station "does its own gas cover
   its own cost" (`gas[i] >= cost[i]`) as the selection rule** — that's a
   purely local check and ignores the ACCUMULATED tank from earlier
   stations; a station can be individually deficient yet still be reachable
   with surplus tank carried in from before, and a station that's
   individually fine can still be an invalid start if what follows drains
   it. The correct rule only cares about the running cumulative sum, not
   any single station in isolation.
2. Forgetting the upfront `sum(gas) < sum(cost)` feasibility check and
   instead assuming the single-pass scan alone always finds an answer or
   correctly signals -1 — without the O(1) sum check, you'd need to also
   verify the CANDIDATE start actually makes it all the way around (i.e. do
   a second wrap-around pass), which technically works but is more code
   for no benefit once you know the total-sum shortcut.
3. Not resetting `tank = 0` (only resetting `start`) after a negative dip —
   leaves stale negative carry-over that corrupts the next candidate's
   running total.
4. Off-by-one on the reset target — resetting to `i` instead of `i + 1`
   (station `i` itself is one of the stations proven infeasible, per the
   exchange argument, since the tank became negative AT i).

--------------------------------------------------------------------------------
RUNTIME DEMO — O(n) single pass vs. O(n²) brute force, measured on this machine
--------------------------------------------------------------------------------
See the code below.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if multiple valid starting stations could exist — find all of
  them?" — the problem guarantees uniqueness when feasible; without that
  guarantee you'd need to re-derive whether the prefix-sum-minimum argument
  still pins down a unique answer (it does, for a single circular pass with
  no ties in achieving the global minimum — ties would need explicit
  handling).
- "What if the car had a limited tank capacity?" — breaks the "unlimited
  tank" assumption baked into the greedy argument; becomes a much harder
  problem needing to track capped tank state, likely no longer cleanly
  greedy.
- "Prove why checking every station individually is unnecessary" — this
  is exactly the exchange argument above; be ready to state it out loud.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 18/003 Jump Game, 18/004 Jump Game II — same "running frontier, reset
  point" pattern family (topic guide §2.1).
- 04/003 Find Pivot Index — same prefix-sum-minimum-style reasoning applied
  to a simpler (non-circular) array.
================================================================================
"""

import random
import time


class Solution:
    def canCompleteCircuit(self, gas: list[int], cost: list[int]) -> int:
        if sum(gas) < sum(cost):
            return -1
        start = 0
        tank = 0
        for i in range(len(gas)):
            tank += gas[i] - cost[i]
            if tank < 0:
                start = i + 1
                tank = 0
        return start


def can_complete_circuit_brute_force(gas: list[int], cost: list[int]) -> int:
    n = len(gas)
    for s in range(n):
        tank = 0
        ok = True
        for step in range(n):
            i = (s + step) % n
            tank += gas[i] - cost[i]
            if tank < 0:
                ok = False
                break
        if ok:
            return s
    return -1


def run_tests():
    sol = Solution()
    assert sol.canCompleteCircuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]) == 3
    assert sol.canCompleteCircuit([2, 3, 4], [3, 4, 3]) == -1
    assert sol.canCompleteCircuit([5], [4]) == 0
    assert sol.canCompleteCircuit([3], [4]) == -1
    assert sol.canCompleteCircuit([3, 3, 4], [3, 4, 4]) == -1

    # cross-check against brute force on random circuits
    random.seed(13)
    for _ in range(300):
        n = random.randint(1, 8)
        gas = [random.randint(0, 6) for _ in range(n)]
        cost = [random.randint(0, 6) for _ in range(n)]
        assert sol.canCompleteCircuit(gas, cost) == can_complete_circuit_brute_force(
            gas, cost
        ), f"mismatch on gas={gas} cost={cost}"

    orig_gas, orig_cost = [1, 2, 3, 4, 5], [3, 4, 5, 1, 2]
    sol.canCompleteCircuit(orig_gas, orig_cost)
    assert orig_gas == [1, 2, 3, 4, 5] and orig_cost == [3, 4, 5, 1, 2]

    # --- Runtime demo: O(n) single pass vs O(n^2) brute force, measured ----
    random.seed(21)
    n = 3000
    gas_big = [random.randint(0, 100) for _ in range(n)]
    cost_big = [random.randint(0, 100) for _ in range(n)]
    # force feasibility with the valid start near the END, so brute force
    # must try nearly every candidate before succeeding (its true worst case)
    gas_big[-1] += sum(cost_big) - sum(gas_big) + 50

    t0 = time.perf_counter()
    fast_result = sol.canCompleteCircuit(gas_big, cost_big)
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    slow_result = can_complete_circuit_brute_force(gas_big, cost_big)
    slow_time = time.perf_counter() - t0

    assert fast_result == slow_result
    print(f"n={n}: single-pass greedy O(n) took {fast_time*1000:.2f} ms")
    print(f"n={n}: brute force O(n^2) took {slow_time*1000:.2f} ms")
    print(f"greedy is {slow_time / fast_time:.1f}x faster on this run")
    assert fast_time < slow_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
