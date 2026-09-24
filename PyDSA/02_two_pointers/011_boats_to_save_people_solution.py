"""
================================================================================
SOLUTION · LeetCode 881 · Boats to Save People                          [Medium]
https://leetcode.com/problems/boats-to-save-people/
================================================================================

THE CORE IDEA
--------------
Sort, then let the HEAVIEST remaining person board a boat each round. If the
LIGHTEST remaining person fits alongside, they board too. The heaviest person
is the hardest to pair; the lightest is the most flexible partner. Pairing
them never costs a later pair, which an exchange argument proves.


================================================================================
APPROACH 1 · Try every pairing (priced, used only as an oracle)
================================================================================
Recursively pick the first unassigned person and try them alone or with each
other unassigned person who fits.

    Time: exponential (roughly the number of matchings, ~n!! for n people)
    Space: O(n) recursion

Fine for n <= 10 in tests, useless at n = 5 * 10^4.


================================================================================
APPROACH 2 · Greedy: pair the two LIGHTEST (a WRONG greedy)
================================================================================
Sort ascending and pair people[0] with people[1], people[2] with people[3],
and so on whenever they fit. It feels efficient ("light people pair easily")
but it uses up the flexible light people on each other and strands the heavy
ones. [1, 1, 2, 2] with limit 3 needs 2 boats; this greedy uses 3. Demo below.


================================================================================
APPROACH 3 · Heaviest with lightest, two pointers ✅ (the answer)
================================================================================
    people.sort()
    lo, hi = 0, len(people) - 1
    boats = 0
    while lo <= hi:
        if people[lo] + people[hi] <= limit:
            lo += 1                  # lightest rides along
        hi -= 1                      # heaviest always leaves
        boats += 1

EXCHANGE ARGUMENT. Let H be the heaviest and L the lightest person, with
H + L <= limit. Take any optimal plan.
  - If H is paired with L already: done.
  - If H is alone: move L into H's boat. L's old boat loses a passenger, so
    the boat count doesn't go up.
  - If H is paired with X, and L is paired with Y: swap X and L, giving boats
    (H, L) and (X, Y). (H, L) is valid by assumption. For (X, Y): X was H's
    partner, so X + H <= limit, and Y <= H because H is the heaviest, so
    X + Y <= X + H <= limit. Valid, same number of boats.
  - If H is paired with X and L is alone: swap them, giving (H, L) and (X).
    Same number of boats.
  Every case yields an optimal plan that pairs H with L, so the greedy choice
  is safe. If H + L > limit, H can't pair with anyone and must go alone.
  Repeat on the remaining people.

    Time: O(n log n)    Space: O(1) extra (Timsort uses O(n) internally)


================================================================================
VARIANT · Counting sort
================================================================================
Weights are bounded by limit <= 3 * 10^4, so a counting sort makes the sort
O(n + limit). The benchmark below measures whether that actually helps in
CPython.


================================================================================
STEP BY STEP TRACE · people = [3, 2, 2, 1], limit = 3
================================================================================
    sorted: [1, 2, 2, 3]

    lo hi  people[lo] people[hi]  sum  fits?  boat contents  boats
    -- --  ---------- ----------  ---  -----  -------------  -----
     0  3           1          3    4  no     (3)                1
     0  2           1          2    3  yes    (1, 2)             2
     1  1           2          2    -  lo==hi (2)                3

    answer: 3


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time           Space   Mutates input?
    ------------------------------  -------------  ------  --------------------
    Try every pairing               exponential    O(n)    No
    Pair two lightest (WRONG)       O(n log n)     O(1)    —
    Heaviest + lightest ✅          O(n log n)     O(1)    YES if you sort in
                                                            place (we copy)
    Counting sort variant           O(n + limit)   O(limit) No


================================================================================
EDGE CASES
================================================================================
    One person               1 boat (loop runs with lo == hi).
    Everyone weighs limit    Nobody pairs; n boats.
    Everyone weighs limit/2  Perfect pairs; ceil(n / 2) boats.
    Odd n                    The last single person gets a boat via lo == hi.


================================================================================
COMMON MISTAKES
================================================================================
1. Pairing the two lightest people. Demo below.

2. `while lo < hi` — forgets the final single person when n is odd (or when
   everyone else paired off). Undercounts by one.

3. Thinking a boat can take THREE light people. The constraint is at most two
   per boat regardless of weight.

4. Advancing lo when the pair doesn't fit. The lightest person hasn't boarded;
   only hi leaves.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Boats carry up to k people?
A: Now it's bin packing, which is NP-hard in general. Exact answers need
   search/DP over subsets for small n; in practice use heuristics like
   first-fit decreasing (at most about 11/9 OPT + 6/9 bins).

Q: Return the actual boat assignments?
A: Append (people[lo], people[hi]) or (people[hi],) each round.

Q: Weights arrive in a stream and boats must leave immediately?
A: Online version: you can't wait for the best partner, so no algorithm is
   always optimal. Keep a sorted structure of waiting people if limited waiting
   is allowed.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 167  Two Sum II (006)                   — same pointer walk on sorted data
    LC 2037 Minimum Moves to Seat Everyone     — sort both, pair in order
    LC 455  Assign Cookies (18_greedy)         — sorted greedy matching
    LC 1996 The Number of Weak Characters      — sort + exchange argument
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def numRescueBoats(self, people: List[int], limit: int) -> int:
        people = sorted(people)
        lo, hi = 0, len(people) - 1
        boats = 0
        while lo <= hi:
            if people[lo] + people[hi] <= limit:
                lo += 1
            hi -= 1
            boats += 1
        return boats


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
def boats_brute(people: List[int], limit: int) -> int:
    """Exact: try every way to pair people up."""
    def solve(rest: tuple) -> int:
        if not rest:
            return 0
        first, others = rest[0], rest[1:]
        best = 1 + solve(others)                     # first goes alone
        for i, p in enumerate(others):
            if first + p <= limit:
                best = min(best, 1 + solve(others[:i] + others[i + 1:]))
        return best
    return solve(tuple(people))


def boats_pair_lightest_bug(people: List[int], limit: int) -> int:
    """WRONG greedy: pair adjacent lightest people."""
    people = sorted(people)
    boats = 0
    i = 0
    while i < len(people):
        if i + 1 < len(people) and people[i] + people[i + 1] <= limit:
            i += 2
        else:
            i += 1
        boats += 1
    return boats


def boats_counting_sort(people: List[int], limit: int) -> int:
    counts = [0] * (limit + 1)
    for p in people:
        counts[p] += 1
    ordered = [w for w in range(limit + 1) for _ in range(counts[w])]
    lo, hi = 0, len(ordered) - 1
    boats = 0
    while lo <= hi:
        if ordered[lo] + ordered[hi] <= limit:
            lo += 1
        hi -= 1
        boats += 1
    return boats


# ==============================================================================
# TESTS — run:  python 011_boats_to_save_people_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: examples and edge cases ---")
    cases = [
        ([1, 2], 3, 1),
        ([3, 2, 2, 1], 3, 3),
        ([3, 5, 3, 4], 5, 4),
        ([5], 5, 1),
        ([1, 1, 2, 2], 3, 2),
        ([2, 2, 2, 2], 4, 2),
        ([1, 5, 3, 5], 7, 3),
    ]
    for people, limit, want in cases:
        got = sol.numRescueBoats(people, limit)
        ok = got == want and boats_counting_sort(people, limit) == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  people={people} limit={limit}  got={got}  want={want}")

    print("\n--- exchange argument checked: greedy == exhaustive search (500 inputs) ---")
    rng = random.Random(881)
    bad = 0
    for _ in range(500):
        limit = rng.randint(3, 12)
        people = [rng.randint(1, limit) for _ in range(rng.randint(1, 9))]
        if sol.numRescueBoats(people, limit) != boats_brute(people, limit):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  500 random inputs: heaviest+lightest is optimal every time")

    print("\n--- wrong greedy LIVE: pairing the two lightest ---")
    wrong = boats_pair_lightest_bug([1, 1, 2, 2], 3)
    right = sol.numRescueBoats([1, 1, 2, 2], 3)
    ok = wrong == 3 and right == 2
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  [1,1,2,2] limit=3: lightest-pairs uses {wrong} boats, optimal is {right}")
    fails = sum(
        boats_pair_lightest_bug(p, lim) != boats_brute(p, lim)
        for lim, p in ((l, [rng.randint(1, l) for _ in range(rng.randint(1, 9))])
                       for l in (rng.randint(3, 12) for _ in range(300)))
    )
    print(f"      on 300 random inputs the lightest-pairs greedy is suboptimal {fails} times")

    print("\n--- benchmark: comparison sort vs counting sort, n = 50,000 ---")
    limit = 30_000
    people = [rng.randint(1, limit) for _ in range(50_000)]
    for name, fn in (("sorted() + two pointers ", sol.numRescueBoats),
                     ("counting sort + pointers", boats_counting_sort)):
        t0 = time.perf_counter()
        for _ in range(5):
            r = fn(people, limit)
        dt = (time.perf_counter() - t0) / 5
        print(f"      {name}  {dt * 1000:7.2f} ms   boats={r}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
