"""
================================================================================
SOLUTION · LeetCode 219 · Contains Duplicate II                           [Easy]
https://leetcode.com/problems/contains-duplicate-ii/
================================================================================

THE CORE IDEA
-------------
Slide a window of the previous `k` values, held in a SET, and ask one question
per element:

    window = set()
    for r, x in enumerate(nums):
        if r > k:
            window.discard(nums[r - k - 1])   # index fell out of range
        if x in window:                       # a partner within k exists
            return True
        window.add(x)
    return False

O(n) time, O(min(n, k)) space.

The aggregate is a set instead of a number, and that is the only new idea. The
window contract is unchanged: **update in O(1) on enter, O(1) on leave.**
`set.add` and `set.discard` are both O(1) average (topic 01 — open addressing),
so a set qualifies.


THE OFF-BY-ONE — derive it, never guess it
------------------------------------------
The condition is `abs(i - j) <= k` with `i != j`. Fix `j = r`. The legal
partners are the indices

        r-k, r-k+1, ..., r-1          <- exactly k indices

so the set must contain precisely those k values when we test `nums[r]`. The
oldest one still legal is `r - k`; therefore the one that has JUST become
illegal, and must be evicted as we arrive at r, is

        r - k - 1

    k = 2, arriving at r = 5:
        legal partners : indices 3, 4          set should be {nums[3], nums[4]}
        just expired   : index 2 = r - k - 1   <- evict this one

    ⚠️  `nums[r - k]` is the classic wrong eviction. It throws away a partner
        that is still legal (exactly k away), so you miss answers whose
        distance is exactly k — the boundary case the tests are built around.

An equivalent, harder-to-get-wrong formulation:

        if len(window) > k:
            window.discard(nums[r - k - 1])

Both say the same thing. The size test makes the invariant explicit — *the set
holds at most k values at the moment of the query* — which is the sentence you
want to be able to say out loud.


================================================================================
WHY A SET IS SAFE EVEN THOUGH IT CANNOT HOLD DUPLICATES
================================================================================
This is the nicest observation in the problem, and it is a real objection an
interviewer may raise.

The worry: suppose the value 7 sits at indices 3 and 6, both inside the window.
A set stores 7 ONCE. When index 3 expires we `discard(7)` — and now the set has
lost the 7 that is still at index 6. The window is wrong.

The resolution: **that state is unreachable.** If two equal values were ever in
the window simultaneously, we would have returned `True` at the moment the
second one arrived — because the test `x in window` runs BEFORE the insert. So
along any execution that is still running, the window's values are all
DISTINCT, and a set loses nothing.

    Invariant: whenever control reaches the top of the loop, the values at
    indices [r-k, r-1] are pairwise distinct.

That invariant is what licenses the cheaper data structure. If the problem had
asked you to COUNT such pairs instead of detect one, the early return would be
gone, duplicates would coexist in the window, and you would need a
`Counter` with `del` on zero (topic guide §3.2) instead of a set.

    ✅ "Does a duplicate exist?"  -> early return -> set is enough
    ✗ "How many pairs?"           -> no early return -> need a multiset

`containsNearbyDuplicate_count_pairs` below is that variant, written with a
Counter, so the difference is concrete.


================================================================================
THE SECOND SOLUTION: LAST-SEEN INDEX
================================================================================
    last = {}                       # value -> the most recent index holding it
    for r, x in enumerate(nums):
        if x in last and r - last[x] <= k:
            return True
        last[x] = r                 # overwrite unconditionally
    return False

WHY OVERWRITING IS CORRECT, AND NOT A BUG. It looks like we are throwing away
information — the earlier positions of `x`. We are, and it is safe:

    For any future index r' > r, the best possible partner for value x is the
    LATEST occurrence, because it is the closest. If the most recent index
    fails the `<= k` test, every older one fails it too (they are strictly
    further away).

That is an elimination argument, exactly like the "cheapest day so far" in
problem 001 of this folder: an unbounded history collapses to one number
because only the extreme can ever matter.

WHICH SOLUTION IS BETTER? They are both O(n) time. They differ in SPACE:

    window set          O(min(n, k))    bounded by the window width
    last-seen map       O(n)            grows with the number of DISTINCT values

    With n = 10^5 and k = 3, the set holds 4 elements and the map may hold
    100000. That is a real difference, and it is the answer to "can you do
    better on memory?"

    With k >= n, they are the same, and both degenerate to LC 217
    (Contains Duplicate).

Lead with the window; mention the map as the alternative and name the space
tradeoff. That ordering shows you chose rather than recalled.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(nums)

    Approach                     Time       Space           Note
    ---------------------------  ---------  --------------  --------------------
    All pairs                    O(n^2)     O(1)            1e10 ops. TLE.
    Pairs within k               O(n*k)     O(1)            still 1e10 at k=1e5
    Sort with original indices   O(n log n) O(n)            works, needlessly slow
    Last-seen index map          O(n)       O(n)            simple, more memory
    Sliding window set ✅        O(n)       O(min(n, k))    best memory

    Set operations are O(1) AVERAGE, not worst case — a pathological hash
    collision pattern degrades them. For Python ints the hash is the value
    itself (for small ints), and adversarial input is not a concern on
    LeetCode, but say "average" rather than "guaranteed" if pushed.


================================================================================
EDGE CASES
================================================================================
    k == 0            ALWAYS False. Two DISTINCT indices cannot be 0 apart.
                      Check your code returns False on [1,1] with k=0 — the
                      eviction `if r > k` fires at r=1 and empties the window
                      before the query, which is exactly right. If you wrote
                      `if r >= k`, trace it and see what happens.

    k >= n            The window never evicts; the problem becomes "does the
                      array contain any duplicate at all" (LC 217).

    [1,2,3,1], k=2    False — the two 1s are 3 apart. THE BOUNDARY TEST: the
                      wrong eviction index (`r - k`) reports True here.

    [1,2,3,1], k=3    True — distance exactly k. The other side of the same
                      boundary. You need BOTH to pin the off-by-one down;
                      either alone can pass with the wrong code.

    [1,1], k=1        Adjacent duplicates. The smallest possible True.

    n == 1            No pair exists. Must return False without crashing, and
                      without reading nums[-1] during eviction.

    huge values       -10^9 .. 10^9 are fine as dict/set keys — Python ints
                      are arbitrary precision and hash to themselves for small
                      magnitudes. No overflow concerns, unlike C++/Java.


================================================================================
COMMON MISTAKES
================================================================================
1. Evicting `nums[r - k]` instead of `nums[r - k - 1]`. Discards a partner that
   is still exactly k away. Detected by ([1,2,3,1], k=3) returning False.

2. Testing membership AFTER inserting. Then `x in window` is trivially true for
   every element and you always return True at r = 0.

3. Using `window.remove(...)` instead of `discard`. `remove` raises KeyError.
   Here it happens to be safe (the value being evicted really is present,
   because we only evict indices we previously inserted) — but `discard`
   states the intent "remove if present" and cannot fail. Use it unless you
   want the KeyError as an assertion.

4. Believing the set is unsound because it cannot hold duplicates. It is sound;
   the early return guarantees the window's values are distinct. Be able to
   say WHY rather than just asserting it.

5. Sorting the array. It destroys the indices, which ARE the constraint. You
   can sort (value, index) pairs and compare adjacent equal values — that
   works, in O(n log n) — but it is strictly worse and shows you did not see
   the window.

6. `if r >= k: evict` — off by one in the guard rather than the index. At k=0
   this evicts nothing useful and can return True. Test k=0 explicitly.

7. O(n*k) "windowing" by re-scanning `nums[r-k:r]` each step. A slice plus a
   scan, inside a loop: the same trap as problems 002 and 003.

8. Reporting the space as O(n) when it is O(min(n, k)). The bound on the window
   is the whole point of choosing it over the map.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: COUNT the pairs instead of detecting one.
A: The early return disappears, so duplicates can now coexist in the window and
   a set is no longer sufficient. Use a `Counter`, add `cnt[x]` to the running
   total BEFORE inserting x (that many partners are in range), and `del` the
   key when it reaches 0 on eviction. See `containsNearbyDuplicate_count_pairs`.

Q: Nearly-equal values, not exactly equal — `abs(nums[i]-nums[j]) <= t` and
   `abs(i-j) <= k` (LC 220, Contains Duplicate III).
A: The window is the same; the QUERY changes from "is x present" to "is there
   anything within t of x", which a hash set cannot answer. Two standard fixes:
   BUCKETING (bucket width t+1, so a partner is in the same bucket or an
   adjacent one — O(n)), or an ordered structure over the window (`SortedList`,
   O(n log k)). Naming the bucket trick is the strong answer.

Q: k is enormous but the array is mostly distinct.
A: The set's size is bounded by min(n, k+1) either way. If memory is the
   binding constraint and duplicates are rare, the window is already optimal;
   the last-seen map is the one that blows up.

Q: Streaming input, unbounded length.
A: The window version is already online: it holds O(k) state and never looks
   back beyond k. The last-seen map is NOT — it grows without bound. This is
   the cleanest argument for preferring the window.

Q: Why not just sort?
A: Sorting destroys the index constraint. You would have to sort (value, index)
   pairs and then compare index distances within each equal-value run — O(n log n)
   for something a single O(n) pass already answers.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 217  Contains Duplicate        — this problem with k = infinity
    LC 220  Contains Duplicate III    — |values| within t too; bucketing
    LC 121  Best Time to Buy/Sell     — the same "only the latest matters" trick
    LC 3    Longest Substring No Rep  — a set/map window, but VARIABLE size
    LC 2200 Find All K-Distant Indices— fixed distance window, different query
    LC 1876 Substrings of Size Three  — fixed window + distinctness
            with Distinct Characters
================================================================================
"""

import random
import time
from collections import Counter
from typing import List


class Solution:
    def containsNearbyDuplicate(self, nums: List[int], k: int) -> bool:
        """Sliding window of the previous k values, held in a set.

        O(n) time, O(min(n, k)) space.
        """
        window = set()
        for r, x in enumerate(nums):
            if r > k:                                  # index r-k-1 expired
                window.discard(nums[r - k - 1])
            if x in window:                            # test BEFORE inserting
                return True
            window.add(x)
        return False

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def containsNearbyDuplicate_size(self, nums: List[int], k: int) -> bool:
        """Same window, but the eviction is driven by the SIZE invariant:
        'the set holds at most k values when the query runs'."""
        window = set()
        for r, x in enumerate(nums):
            if len(window) > k:
                window.discard(nums[r - k - 1])
            if x in window:
                return True
            window.add(x)
        return False

    def containsNearbyDuplicate_lastseen(self, nums: List[int], k: int) -> bool:
        """Last-seen index map. O(n) time but O(n) space.

        Overwriting last[x] is safe: the most recent occurrence is the closest
        possible partner for anything in the future.
        """
        last = {}
        for r, x in enumerate(nums):
            if x in last and r - last[x] <= k:
                return True
            last[x] = r
        return False

    def containsNearbyDuplicate_brute(self, nums: List[int], k: int) -> bool:
        """O(n*k) oracle: every pair within distance k."""
        for i in range(len(nums)):
            for j in range(i + 1, min(i + k + 1, len(nums))):
                if nums[i] == nums[j]:
                    return True
        return False

    # ------------------------------------------------------------------
    # The counting variant — where a SET stops being sufficient.
    # ------------------------------------------------------------------
    def containsNearbyDuplicate_count_pairs(self, nums: List[int], k: int) -> int:
        """COUNT the pairs (i, j), i < j, with nums[i]==nums[j] and j-i <= k.

        No early return, so equal values DO coexist in the window and a set
        would lose multiplicity. A Counter with `del` on zero is required.
        """
        window = Counter()
        total = 0
        for r, x in enumerate(nums):
            if r > k:
                out = nums[r - k - 1]
                window[out] -= 1
                if window[out] == 0:
                    del window[out]              # keep the map honest
            total += window[x]                   # every copy in range pairs with x
            window[x] += 1
        return total

    # ------------------------------------------------------------------
    # Deliberate breakages.
    # ------------------------------------------------------------------
    def containsNearbyDuplicate_off_by_one(self, nums: List[int], k: int) -> bool:
        """✗ BROKEN — evicts nums[r-k], which is still a LEGAL partner."""
        window = set()
        for r, x in enumerate(nums):
            if r >= k:
                window.discard(nums[r - k])
            if x in window:
                return True
            window.add(x)
        return False

    def containsNearbyDuplicate_late_query(self, nums: List[int], k: int) -> bool:
        """✗ BROKEN — inserts before querying, so every element finds itself."""
        window = set()
        for r, x in enumerate(nums):
            if r > k:
                window.discard(nums[r - k - 1])
            window.add(x)
            if x in window:
                return True
        return False


# ==============================================================================
# TESTS — run:  python 004_contains_duplicate_ii_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 3, 1], 3), ([1, 0, 1, 1], 1), ([1, 2, 3, 1, 2, 3], 2),
    ([1, 2, 3, 1], 2), ([1, 1], 1), ([1, 1], 0), ([1, 2, 3], 0),
    ([99], 5), ([1, 2, 3, 4, 5], 100), ([1, 2, 3, 4, 1], 100),
    ([0, 1, 2, 3, 2, 5], 3), ([4, 1, 2, 3, 1, 5], 3), ([1, 2, 1, 2, 1], 2),
    ([-1_000_000_000, 1_000_000_000, -1_000_000_000], 2),
]


def _brute_count(nums, k):
    return sum(1
               for i in range(len(nums))
               for j in range(i + 1, min(i + k + 1, len(nums)))
               if nums[i] == nums[j])


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("window set     ", sol.containsNearbyDuplicate),
        ("window by size ", sol.containsNearbyDuplicate_size),
        ("last-seen map  ", sol.containsNearbyDuplicate_lastseen),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(a), k) == sol.containsNearbyDuplicate_brute(a, k)
                 for a, k in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    ok = all(sol.containsNearbyDuplicate_count_pairs(list(a), k)
             == _brute_count(a, k) for a, k in CASES)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  pair COUNT variant ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n*k) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n*k) oracle ---")
    random.seed(219)
    trials, mismatches = 5000, 0
    for _ in range(trials):
        n = random.randint(1, 14)
        arr = [random.randint(0, 6) for _ in range(n)]      # dense duplicates
        k = random.randint(0, n + 2)
        want = sol.containsNearbyDuplicate_brute(arr, k)
        for _, fn in impls:
            if fn(list(arr), k) != want:
                mismatches += 1
        if sol.containsNearbyDuplicate_count_pairs(list(arr), k) != _brute_count(arr, k):
            mismatches += 1
    print(f"  {trials} random (array, k) x {len(impls) + 1} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The window, traced.
    # ----------------------------------------------------------------------
    nums, k = [1, 2, 3, 1, 2, 3], 2
    print(f"\n--- the window over {nums}, k={k} ---")
    print(f"  legal partners for index r are indices [r-{k}, r-1] "
          f"({k} of them)")
    print(f"  {'r':>2} {'x':>3} {'evict idx':>10} {'set before query':>18}"
          f"  hit?")
    window = set()
    for r, x in enumerate(nums):
        ev = "-"
        if r > k:
            ev = f"{r - k - 1} (={nums[r-k-1]})"
            window.discard(nums[r - k - 1])
        hit = x in window
        print(f"  {r:>2} {x:>3} {ev:>10} {str(sorted(window)):>18}"
              f"  {'YES -> True' if hit else 'no'}")
        if hit:
            break
        window.add(x)
    else:
        print("  no hit -> False")

    # ----------------------------------------------------------------------
    # ⚠️  The off-by-one, on both sides of the boundary.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  evicting nums[r-k] instead of nums[r-k-1] ---")
    print(f"  {'input':<20} {'k':>2} {'correct':>8} {'evicts r-k':>11}  ok?")
    for arr, k in ([1, 2, 3, 1], 3), ([1, 2, 3, 1], 2), ([1, 1], 1), \
                  ([1, 1], 0), ([1, 2, 1], 2), ([1, 2, 1], 1):
        good = sol.containsNearbyDuplicate(list(arr), k)
        bad = sol.containsNearbyDuplicate_off_by_one(list(arr), k)
        print(f"  {str(arr):<20} {k:>2} {str(good):>8} {str(bad):>11}  "
              f"{'yes' if good == bad else 'NO  <- lost a partner exactly k away'}")
    print("  You need BOTH ([1,2,3,1],k=3) and ([1,2,3,1],k=2) to pin this down:")
    print("  either one alone can pass with the wrong eviction index.")

    # ----------------------------------------------------------------------
    # ⚠️  Query before insert.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  inserting before querying ---")
    for arr, k in ([1, 2, 3], 1), ([5], 3), ([1, 2, 3, 1], 2):
        print(f"  {str(arr):<14} k={k}  correct="
              f"{str(sol.containsNearbyDuplicate(list(arr), k)):<5}  "
              f"insert-first={sol.containsNearbyDuplicate_late_query(list(arr), k)}")
    print("  Every element finds ITSELF, so it returns True at r=0 always.")

    # ----------------------------------------------------------------------
    # Why a set is sound: the window's values are always distinct.
    # ----------------------------------------------------------------------
    print("\n--- why a SET (not a multiset) is enough ---")
    print("  Claim: whenever the loop reaches its top, the values in the window")
    print("  are pairwise DISTINCT — because a second copy would have returned")
    print("  True on arrival. Verified over 20000 random runs:")
    random.seed(2)
    violations = 0
    for _ in range(20_000):
        n = random.randint(1, 12)
        arr = [random.randint(0, 4) for _ in range(n)]
        k = random.randint(0, 5)
        seen = []
        for r, x in enumerate(arr):
            lo = max(0, r - k)
            win = arr[lo:r]
            if len(win) != len(set(win)):
                violations += 1
                break
            if x in win:
                break
    print(f"  windows containing a duplicate at the top of the loop: {violations}")
    print("  Zero. Drop the early return and the invariant dies — which is")
    print("  exactly why the pair-COUNTING variant needs a Counter instead.")

    # ----------------------------------------------------------------------
    # Memory: window vs last-seen map.
    # ----------------------------------------------------------------------
    print("\n--- memory: O(min(n,k)) window vs O(n) last-seen map ---")
    print(f"  {'n':>8} {'k':>8} {'window peak':>12} {'map peak':>10}")
    random.seed(5)
    for n, k in ((100_000, 3), (100_000, 100), (100_000, 100_000)):
        arr = [random.randint(0, 10 ** 9) for _ in range(n)]
        window, wpeak = set(), 0
        for r, x in enumerate(arr):
            if r > k:
                window.discard(arr[r - k - 1])
            window.add(x)
            wpeak = max(wpeak, len(window))
        last = {}
        for r, x in enumerate(arr):
            last[x] = r
        print(f"  {n:>8} {k:>8} {wpeak:>12} {len(last):>10}")
    print("  At k=3 the window holds 4 values while the map holds ~100000.")
    print("  Same time complexity, four orders of magnitude less memory — and")
    print("  the window works on an unbounded STREAM, where the map cannot.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n*k).
    # ----------------------------------------------------------------------
    print("\n--- window vs re-scanning the previous k elements ---")
    print(f"  {'n':>7} {'k':>7} {'window O(n)':>13} {'rescan O(nk)':>14}")
    for n, k in ((20_000, 10), (20_000, 500), (20_000, 4_000)):
        arr = list(range(n))                       # no duplicates: worst case
        t0 = time.perf_counter(); sol.containsNearbyDuplicate(arr, k)
        t1 = time.perf_counter(); sol.containsNearbyDuplicate_brute(arr, k)
        t2 = time.perf_counter()
        print(f"  {n:>7} {k:>7} {(t1 - t0) * 1000:>11.1f}ms "
              f"{(t2 - t1) * 1000:>12.1f}ms")
    print("  A duplicate-free array is the worst case: nothing returns early.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
