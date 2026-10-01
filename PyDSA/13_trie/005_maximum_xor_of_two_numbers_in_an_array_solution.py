"""
================================================================================
SOLUTION · LeetCode 421 · Maximum XOR of Two Numbers in an Array         [Medium]
https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/
================================================================================

THE CORE IDEA
--------------
XOR maximizes bit-by-bit, MOST significant bit first: a 1 in a high bit of
the result is worth more than any combination of lower bits, so the
greedy choice at each level is provably safe (never needs to be undone).
Build a trie of fixed depth 32 (one level per bit, MSB first) where every
node has exactly two children -- bit 0 and bit 1. Insert every number's
bit pattern. Then, for each number `x`, walk the trie trying at every
level to go the OPPOSITE of `x`'s bit there (opposite bits XOR to 1); if
that branch doesn't exist, fall back to the SAME bit (XOR contributes 0 at
that level, unavoidable). The number reconstructed by this walk is the
best XOR partner for `x` among everything inserted so far. Track the max
over all `x`. This turns the pairwise O(n^2) scan into O(32*n) -- a
FIXED-depth trie walk per number instead of comparing every pair (topic
guide Part 7).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it, don't ship it): try every pair
`nums[i] XOR nums[j]` for `i < j`, keep the max. O(n^2) time, O(1) space.
With n up to 2*10^5, that's up to ~2*10^10 pair evaluations -- completely
infeasible at the stated bound; the demo below prices this honestly on a
much smaller n and shows the growth curve, it does not run it at the real
scale.

Approach 1 (bit trie, insert-all-then-query-all) ✅ — the answer. Insert
every number into the bit trie: O(32*n). For each number, greedily walk
for its best XOR partner: O(32*n). Total O(32*n) = O(n), since 32 is a
fixed constant (the bit width). Two full passes over `nums`.

Approach 2 (prefix-based bucket, no trie object) — same greedy bit-by-bit
idea, implemented iteratively without an explicit tree: build the answer
bit by bit from MSB down, at each step checking (via a HASH SET of
number-prefixes truncated to the current bit count) whether some pair of
already-seen prefixes could achieve the candidate answer with this bit
set to 1; if yes keep it, else settle for 0 at this bit. Same O(32*n)
complexity, avoids allocating trie node objects — often faster in
practice in Python because it trades object/pointer overhead for set
membership tests. The demo below measures both on this machine.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [3, 10, 5, 25, 2, 8], using just 5 bits for readability
    3  = 00011
    10 = 01010
    5  = 00101
    25 = 11001
    2  = 00010
    8  = 01000

Insert all six 5-bit patterns into the trie (each node has a 0-child and/or
a 1-child; only the paths that exist are drawn):

    root
    ├─0 (numbers starting with bit 0: 3,10,5,2,8)
    │  ├─0 (3,5,2 start 00)
    │  │  ├─0 (3,2 -> 000..)
    │  │  │  └─1─1 -> 3 (00011)
    │  │  │  └─1─0 -> 2 (00010)
    │  │  └─1─0─1 -> 5 (00101)
    │  └─1 (10,8 start 01)
    │     ├─0─1─0 -> 10 (01010)
    │     └─0─0─0 -> 8  (01000)
    └─1─1─0─0─1 -> 25 (11001)

query x = 5 = 00101, want the OPPOSITE bit at every level when possible:
    bit4 (MSB) of 5 is 0 -> want a 1-child at root -> EXISTS (the 25 branch)
                            -> go there, contributes 1<<4 = 16 to the xor
    bit3 of 5 is 0 -> want a 1-child -> 25's branch only has bit3=1 (25 is
                      11001) -> EXISTS -> go there, contributes 1<<3 = 8
    bit2 of 5 is 1 -> want a 0-child -> 25's remaining path has bit2=0
                      (11001) -> EXISTS -> contributes 0 this bit is same
                      as wanted-opposite so it DOES flip: 1 XOR 0 = 1 ->
                      contributes 1<<2 = 4
    bit1 of 5 is 0 -> want a 1-child -> 25 has bit1=0 -> NOT the opposite,
                      but 25 is the only number left on this path (25 =
                      11001) so the trie has no choice: forced to bit 0,
                      contributes 0 << 1 = 0
    bit0 of 5 is 1 -> want a 0-child -> 25's bit0 is 1 -> forced, 0
                      contributed at this bit too
    walked to leaf = 25.  5 XOR 25 = 00101 ^ 11001 = 11100 = 28

This matches: LeetCode's own expected answer is 28 (5 XOR 25).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time      Space    Mutates input?  Note
    -------------------------------  --------  -------  --------------  -----------------
    Brute force, all pairs           O(n^2)    O(1)     no              infeasible at n=2*10^5
    Bit trie, insert + greedy walk ✅ O(32*n)  O(32*n)  no              == O(n), 32 fixed
    Prefix-set bit-by-bit (no trie)  O(32*n)  O(n)      no              same complexity class,
                                                                         different constants

    32 comes from `nums[i] <= 2^31 - 1` fitting in 32 bits; this constant
    is why the O(32*n) is written as O(n) in casual conversation, but say
    the "32" out loud in an interview — it's where the 32 comes from.


================================================================================
EDGE CASES
================================================================================
    single-element array           -> only i==j pairs exist, but the
                                       problem defines i<=j, and XOR of a
                                       number with itself is always 0 ->
                                       answer is 0. (LeetCode's own example
                                       nums=[0] confirms this.)
    all elements equal              -> every pairwise XOR is 0 -> answer 0.
    array containing 0               -> 0 XOR x == x for any x, so 0 can
                                       still be the winning "partner" for
                                       the number with the highest bit set.
    numbers spanning very different -> forces the trie to actually branch
    bit-lengths (e.g. 1 and 2^30)      early at a high bit — exercises the
                                       full 32-level depth, not a shortcut.
    leading zero bits                -> ALL numbers must be treated as
                                       fixed-width 32-bit values (pad with
                                       leading 0s), or the trie can't align
                                       bit positions across numbers of
                                       different magnitudes -- this is the
                                       single most common bug (see below).


================================================================================
COMMON MISTAKES
================================================================================
1. Not padding to a FIXED bit width (e.g. iterating `bin(x)[2:]` directly)
   -- two numbers of different magnitudes then have their bits misaligned
   in the trie, corrupting every XOR computed through a shared node. Always
   iterate a fixed range like `range(31, -1, -1)` and extract each bit
   with `(x >> i) & 1`, independent of the number's own natural length.

2. Walking LSB-first instead of MSB-first -- XOR maximization is a greedy
   argument that ONLY works most-significant-bit-first, because a decision
   at a higher bit is worth more than any possible combination of all
   lower bits combined; getting the bit order backwards breaks the
   greedy's correctness silently (it still runs, it just doesn't find the
   true max).

3. In the greedy walk, forgetting the FALLBACK when the opposite-bit child
   doesn't exist -- must fall through to the same-bit child (which is
   guaranteed to exist, since the current number itself was inserted along
   that exact path).

4. Building a NEW trie per query number instead of inserting ALL numbers
   once up front, then querying each -- turns O(32*n) into O(32*n^2),
   silently reintroducing the brute-force's asymptotic class through the
   back door.

5. Forgetting to handle `n == 1`: with only one number in `nums`, i<=j
   still allows i==j, so the trie-based algorithm must return 0 (querying
   a number against itself finds itself, XOR 0) rather than crashing on
   "no valid pair".


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Numbers can be up to 64-bit / arbitrary precision -- does this still
   work?
A: Yes, just change the fixed bit-width constant (32 -> 64, or to
   `x.bit_length()` of the max element) — the algorithm's shape is
   unchanged, only the loop bound.

Q: Find the maximum XOR of any PAIR within a bounded time window (like a
   streaming variant)?
A: Insert into the trie as elements arrive; to answer "max XOR so far"
   incrementally, query each newly inserted element against everything
   already in the trie BEFORE inserting it (so you never pair an element
   with itself), keeping a running max — O(32) extra work per arrival.

Q: How does this compare to sorting-based approaches?
A: There is no useful sort-based shortcut for XOR (unlike sum or
   difference) — XOR does not respect numeric ordering (a bigger number
   can XOR SMALLER with its neighbor than with a much smaller number), so
   sorting doesn't let you prune the way it does for, say, 2Sum on a
   sorted array. The bit trie remains the standard technique.

Q: Extend to "maximum XOR of an element with a value in [restricted
   set]" or with a value <= some limit?
A: LC 1707 (Maximum XOR With an Element From Array) is exactly this
   extension — offline queries sorted by limit, inserting into the trie
   incrementally as the limit grows, so each query only sees eligible
   elements.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 208  Implement Trie (this topic, 001)          — same node/child
            structure, characters instead of bits
    LC 1707 Maximum XOR With an Element From Array     — offline variant
            with a value ceiling per query
    LC 1803 Count Pairs With XOR in a Range             — bit trie counting
            matches in a range instead of finding a single max
    LC 1938 Maximum Genetic Difference Query            — bit trie over a
            TREE's root-to-node paths instead of a flat array
================================================================================
"""

import random
import time


class TrieNode:
    __slots__ = ("children",)

    def __init__(self):
        self.children = [None, None]   # index 0 / 1 = that bit's child


class Solution:
    BITS = 30   # nums[i] <= 2^31 - 1, so bit indices 30..0 cover it (30 -> MSB)

    def findMaximumXOR(self, nums: list[int]) -> int:
        if len(nums) < 2:
            return 0

        root = TrieNode()
        for num in nums:
            node = root
            for i in range(self.BITS, -1, -1):
                bit = (num >> i) & 1
                if node.children[bit] is None:
                    node.children[bit] = TrieNode()
                node = node.children[bit]

        best = 0
        for num in nums:
            node = root
            xor_val = 0
            for i in range(self.BITS, -1, -1):
                bit = (num >> i) & 1
                want = 1 - bit
                if node.children[want] is not None:
                    xor_val |= (1 << i)
                    node = node.children[want]
                else:
                    node = node.children[bit]
            best = max(best, xor_val)
        return best


# ==============================================================================
# Variants used only by the runtime demos below.
# ==============================================================================
def max_xor_brute_force(nums: list[int]) -> int:
    best = 0
    n = len(nums)
    for i in range(n):
        for j in range(i, n):
            best = max(best, nums[i] ^ nums[j])
    return best


def max_xor_prefix_set(nums: list[int]) -> int:
    """Approach 2: bit-by-bit greedy using hash sets of bit-prefixes,
    no explicit trie node objects."""
    BITS = 30
    answer = 0
    for i in range(BITS, -1, -1):
        answer <<= 1
        candidate = answer | 1
        prefixes = {num >> i for num in nums}
        # candidate is achievable iff some pair of prefixes XORs to it
        if any((candidate ^ p) in prefixes for p in prefixes):
            answer = candidate
    return answer


# ==============================================================================
# TESTS — run:  python 005_maximum_xor_of_two_numbers_in_an_array_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness ---")
    sol = Solution()
    cases = [
        ([3, 10, 5, 25, 2, 8], 28),
        ([0], 0),
        ([2, 4], 6),
        ([8, 10, 2], 10),
        ([0, 0, 0], 0),
        ([1], 0),
        ([1, 2**30], (1 ^ 2**30)),
    ]
    for nums, want in cases:
        got = sol.findMaximumXOR(list(nums))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<24} -> {got}  (want {want})")

    # --------------------------------------------------------------------
    # Trace, printed explicitly, matching the docstring's example.
    # --------------------------------------------------------------------
    print("\n--- trace: nums=[3,10,5,25,2,8], query x=5 ---")
    root = TrieNode()
    for num in (3, 10, 5, 25, 2, 8):
        node = root
        for i in range(4, -1, -1):    # 5 bits is enough for this example
            bit = (num >> i) & 1
            if node.children[bit] is None:
                node.children[bit] = TrieNode()
            node = node.children[bit]
    x, node, xor_val = 5, root, 0
    for i in range(4, -1, -1):
        bit = (x >> i) & 1
        want = 1 - bit
        if node.children[want] is not None:
            xor_val |= (1 << i)
            node = node.children[want]
            print(f"  bit{i}: x's bit={bit}, opposite EXISTS -> take it, "
                  f"xor so far = {xor_val:05b}")
        else:
            node = node.children[bit]
            print(f"  bit{i}: x's bit={bit}, opposite MISSING -> forced same bit, "
                  f"xor so far = {xor_val:05b}")
    print(f"  final: 5 XOR {xor_val} = {5 ^ xor_val}  (walked-to number is {xor_val})")

    # --------------------------------------------------------------------
    # Randomised cross-check: trie, brute force, and prefix-set all agree.
    # --------------------------------------------------------------------
    print("\n--- randomised cross-check: trie vs brute force vs prefix-set ---")
    random.seed(421)
    mismatches = 0
    for _ in range(300):
        nums = [random.randint(0, 2**20) for _ in range(random.randint(1, 40))]
        a = sol.findMaximumXOR(list(nums))
        b = max_xor_brute_force(nums)
        c = max_xor_prefix_set(nums)
        if not (a == b == c):
            mismatches += 1
    ok = mismatches == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  300 random arrays, {mismatches} mismatches "
          f"(trie / brute-force / prefix-set)")

    # --------------------------------------------------------------------
    # DEMO 1: brute force O(n^2) vs trie O(n) growth curve.
    # --------------------------------------------------------------------
    print("\n--- DEMO 1: brute-force O(n^2) vs bit-trie O(n) growth ---")
    random.seed(5)
    print(f"  {'n':>7} {'brute (ms)':>12} {'trie (ms)':>11} {'speedup':>9}")
    for n in (200, 800, 3200):
        nums = [random.randint(0, 2**31 - 1) for _ in range(n)]
        t0 = time.perf_counter()
        b = max_xor_brute_force(nums)
        t1 = time.perf_counter()
        t = sol.findMaximumXOR(nums)
        t2 = time.perf_counter()
        assert b == t
        brute_ms, trie_ms = (t1 - t0) * 1000, (t2 - t1) * 1000
        print(f"  {n:>7} {brute_ms:>12.2f} {trie_ms:>11.2f} "
              f"{brute_ms / trie_ms:>8.1f}x")
    print("  n doubling roughly QUADRUPLES brute force's cost (O(n^2)) while")
    print("  the trie's cost grows only LINEARLY (O(32*n)) -- the gap widens.")

    # --------------------------------------------------------------------
    # DEMO 2: trie-object walk vs prefix-set-of-ints, same complexity class.
    # --------------------------------------------------------------------
    print("\n--- DEMO 2: trie-node objects vs hash-set-of-int-prefixes (same O(n)) ---")
    random.seed(6)
    nums = [random.randint(0, 2**31 - 1) for _ in range(50_000)]
    t0 = time.perf_counter()
    r1 = sol.findMaximumXOR(nums)
    t1 = time.perf_counter()
    r2 = max_xor_prefix_set(nums)
    t2 = time.perf_counter()
    assert r1 == r2
    trie_t, set_t = (t1 - t0) * 1000, (t2 - t1) * 1000
    print(f"  n = {len(nums)}")
    print(f"  bit-trie (node objects):     {trie_t:8.1f} ms")
    print(f"  prefix-set (hash sets):      {set_t:8.1f} ms")
    faster = "prefix-set" if set_t < trie_t else "bit-trie"
    print(f"  faster on THIS run: {faster} "
          f"({abs(trie_t - set_t):.1f} ms apart) -- both are O(32*n); the gap")
    print("  is constant-factor Python object/attribute overhead, not asymptotics.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
