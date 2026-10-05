"""
================================================================================
SOLUTION · LeetCode 238 · Product of Array Except Self                 [Medium]
https://leetcode.com/problems/product-of-array-except-self/
================================================================================

THE CORE IDEA
-------------
Stop thinking "remove nums[i] from the total". Think:

    answer[i] = (product of everything LEFT of i) × (product of everything RIGHT of i)

nums[i] never appears in that formula. It is excluded BY CONSTRUCTION, not by
dividing it back out — which is why the no-division rule stops being a
restriction and becomes a hint.

                     i
    nums = [ a,  b,  c,  d,  e ]
             └──────┘   └──────┘
              prefix     suffix
             (a×b)        (d×e)

             answer[i] = (a×b) × (d×e)

Computing each prefix from scratch is O(n²). But consecutive prefixes differ by
one multiply:

    prefix[i+1] = prefix[i] × nums[i]

So one left-to-right pass builds every prefix, and one right-to-left pass
builds every suffix. Two passes, O(n).

The final move — the one the follow-up is fishing for — is realising you never
need both arrays in memory at once. Store the prefixes IN THE OUTPUT ARRAY,
then fold the suffixes in on the way back using a single scalar. O(1) extra.

    "Two-pass prefix/suffix, accumulate in the output" is a reusable pattern:
    LC 42 (Trapping Rain Water), LC 135 (Candy), LC 152 (Max Product Subarray)
    are all the same shape.


================================================================================
APPROACH 0 · Division (state it, then explain why it is banned)
================================================================================
    total = 1
    for v in nums: total *= v
    return [total // v for v in nums]

    Time: O(n)   Space: O(1)

It is the first thing anyone thinks of, so say it — then break it yourself:

    nums = [1, 2, 0, 4]  ->  total = 0  ->  0 // 0  ->  ZeroDivisionError

Zeros are the reason for the ban. You CAN rescue it by counting zeros:

    0 zeros  -> answer[i] = total / nums[i]
    1 zero   -> only the zero's slot is nonzero (= product of all others),
                every other slot is 0
    2+ zeros -> every slot is 0

That is correct and O(n)/O(1) — worth saying out loud, because it shows you
reasoned about zeros rather than just obeying a rule. But it is three branches,
it needs exact integer division, and it is fragile with floats. The
prefix/suffix answer has zero special cases. Prefer it.


================================================================================
APPROACH 1 · Two explicit arrays ✅ (write this first — it is clearer)
================================================================================
    n = len(nums)
    prefix = [1] * n
    suffix = [1] * n

    for i in range(1, n):
        prefix[i] = prefix[i-1] * nums[i-1]
    for i in range(n-2, -1, -1):
        suffix[i] = suffix[i+1] * nums[i+1]

    return [prefix[i] * suffix[i] for i in range(n)]

    Time: O(n)   Space: O(n) extra

STEP BY STEP for nums = [1, 2, 3, 4]:

    index        0     1     2     3
    nums         1     2     3     4

    prefix   →   1     1     2     6
                 ↑     ↑     ↑     ↑
              nothing  1    1×2  1×2×3
              to left

    suffix   ←  24    12     4     1
                 ↑     ↑     ↑     ↑
             2×3×4   3×4     4   nothing
                                 to right

    answer    1×24  1×12   2×4   6×1
            =   24    12     8     6      ✓

⚠️  THE EMPTY PRODUCT IS 1, NOT 0
    prefix[0] = 1 because there is nothing to the left of index 0, and the
    identity element for multiplication is 1. Initialising to 0 makes every
    answer 0. This is the single most common bug here; the tests demonstrate it.

⚠️  THE INDEX SHIFT IS THE OTHER BUG
    `prefix[i] = prefix[i-1] * nums[i-1]` uses nums[i-1], NOT nums[i]. prefix[i]
    means "everything strictly before i", so nums[i] must not be in it. Writing
    `* nums[i]` gives you an inclusive prefix and every answer is wrong by a
    factor of nums[i]. Same on the suffix side: `nums[i+1]`, not `nums[i]`.


================================================================================
APPROACH 2 · Output array + one scalar ✅✅ (the O(1)-space answer)
================================================================================
The problem says the output does not count toward space. So use it as scratch.

    n = len(nums)
    answer = [1] * n

    # Pass 1 — left to right: answer[i] holds the prefix product.
    running = 1
    for i in range(n):
        answer[i] = running          # WRITE first...
        running *= nums[i]           # ...THEN update

    # Pass 2 — right to left: fold the suffix in with one scalar.
    running = 1
    for i in range(n - 1, -1, -1):
        answer[i] *= running         # WRITE first...
        running *= nums[i]           # ...THEN update

    return answer

    Time: O(n)   Space: O(1) extra

STEP BY STEP for nums = [1, 2, 3, 4]:

    PASS 1 (left to right)                 running starts at 1

    i=0   answer[0] = 1        running -> 1×1 = 1     answer = [1, 1, 1, 1]
    i=1   answer[1] = 1        running -> 1×2 = 2     answer = [1, 1, 1, 1]
    i=2   answer[2] = 2        running -> 2×3 = 6     answer = [1, 1, 2, 1]
    i=3   answer[3] = 6        running -> 6×4 = 24    answer = [1, 1, 2, 6]

          answer now holds the PREFIX products.

    PASS 2 (right to left)                 running resets to 1

    i=3   answer[3] = 6×1  = 6     running -> 1×4 = 4    answer = [1, 1, 2, 6]
    i=2   answer[2] = 2×4  = 8     running -> 4×3 = 12   answer = [1, 1, 8, 6]
    i=1   answer[1] = 1×12 = 12    running -> 12×2 = 24  answer = [1,12, 8, 6]
    i=0   answer[0] = 1×24 = 24    running -> 24×1 = 24  answer = [24,12,8,6]

    return [24, 12, 8, 6]      ✓

⚠️  WRITE BEFORE YOU UPDATE — IN BOTH PASSES
    If you do `running *= nums[i]` first and then `answer[i] = running`, the
    running product INCLUDES nums[i] and you have computed the inclusive
    prefix. Every answer comes out multiplied by nums[i]. The two statements
    are one line apart and swapping them is the classic failure. The tests
    below run the swapped version so you can see it.

⚠️  WHY IS THIS "O(1) SPACE" WHEN answer IS SIZE n?
    Because the problem explicitly exempts the output. That exemption is
    standard for "return an array" problems — you cannot produce n values in
    less than n space, so counting it would make the follow-up impossible.
    Beyond `answer` you use exactly one integer. Say that precisely; hand-waving
    "it's O(1) because they said so" sounds like you did not think about it.


================================================================================
WHY ZEROS NEED NO SPECIAL CASE
================================================================================
This is worth checking explicitly, because it is the thing that killed
division. Take nums = [-1, 1, 0, -3, 3]:

    prefix  =  1   -1   -1    0    0        (once a 0 enters, it propagates)
    suffix  =  0    0    9    3    1
    answer  =  0    0    9    0    0        ✓

    index 2 is the only nonzero: its prefix (-1×1) and suffix (-3×3) both skip
    the zero, because the zero IS nums[2] and neither side includes it.

    Every other index has the zero on one side or the other, so one of its two
    factors is 0.

The algorithm never asks "is this a zero?" — the structure handles it. That is
what "no special cases" buys you, and it is the strongest argument for this
approach over patched division.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time    Extra space   Mutates input?
    ------------------------  ------  ------------  --------------
    Brute force (n per cell)  O(n²)   O(1)          no
    Division + zero counting  O(n)    O(1)          no  (but banned here)
    Two arrays            ✅  O(n)    O(n)          no
    Output + scalar     ✅✅  O(n)    O(1)          no

    None of these mutate `nums`. Approach 2 mutates only the array it returns.


================================================================================
EDGE CASES
================================================================================
    [2, 3]          -> [3, 2]
                       n = 2, the minimum. Each answer is just the other
                       element. Catches loops written as `range(1, n-1)`.

    [1, 0]          -> [0, 1]
                       EXACTLY ONE ZERO. The zero's own slot is the product of
                       everything else (1); every other slot is 0. This is the
                       case that breaks naive division.

    [0, 0]          -> [0, 0]
                       TWO ZEROS. Every slot is 0, because each index still has
                       a zero on one side. Breaks zero-counting code that
                       assumes at most one.

    [0, 4, 0]       -> [0, 0, 0]
                       Two zeros with something between them. Index 1 has a
                       zero on BOTH sides.

    [-1, -1, -1]    -> [1, 1, 1]
                       Sign bookkeeping — two negatives multiply to a positive.

    [1, 1, 1, 1]    -> [1, 1, 1, 1]
                       All ones. Distinguishes "correct" from "returned the
                       initialiser untouched" — a solution that never writes
                       anything also returns all ones. Pair it with another
                       case; alone it proves nothing.


================================================================================
COMMON MISTAKES
================================================================================
1. Initialising the running product (or prefix[0]) to 0. The empty product is
   1. Everything becomes 0.

2. Updating the runner BEFORE writing, so the prefix includes nums[i] itself.
   Off by a factor of nums[i] everywhere.

3. Using nums[i] instead of nums[i-1] when building prefix (or nums[i] instead
   of nums[i+1] for suffix). Same inclusive-vs-exclusive error.

4. Using division because "it passes" — it does not, on any input with a zero,
   and the problem forbids it explicitly.

5. Reaching for `math.prod(nums[:i] + nums[i+1:])` per index. Elegant-looking,
   O(n²) time AND O(n) slicing garbage per iteration. This is the brute force
   wearing a nice hat.

6. Claiming O(1) space while allocating both a prefix and a suffix array.

7. Iterating pass 2 with `range(n-1, 0, -1)` and never touching index 0.

8. Resetting `running = 1` between the two passes — forgetting to do this
   carries the total product into pass 2 and inflates everything.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Now you ARE allowed to use division. Is it better?
A: It is one pass instead of two, but it needs zero-counting branches and, in
   a language with fixed-width ints, the total product can overflow even when
   every individual answer fits. Prefix/suffix never forms the total. In this
   problem the constraints guarantee prefixes and suffixes fit in 32 bits —
   note they guarantee that about PREFIXES, not about the full product. That
   wording is deliberate.

Q: Handle it if the array can contain a very large number of elements and the
   product overflows.
A: Python ints are arbitrary precision so it is a non-issue here; in Go/Java
   you would either use big.Int, or work in log-space (sum of logs, then
   exponentiate) accepting float error, or return the answer modulo something.
   Log-space also silently breaks on zeros and negatives — mention that.

Q: What if you get queries for "product except range [l, r]"?
A: Precompute a prefix-product array once, then any range product is
   prefix[r+1] / prefix[l] — which needs division and dies on zeros. The
   robust version stores (count of zeros, product of nonzeros) per prefix.
   That generalisation is a genuinely good follow-up answer.

Q: Do it for SUM except self instead of product.
A: total - nums[i], one line. Sums have an inverse that always exists;
   products do not, which is precisely why this problem is interesting.


================================================================================
RELATED PROBLEMS — the prefix/suffix accumulation family
================================================================================
    LC 42   Trapping Rain Water     — maxLeft[i] and maxRight[i]; same two-pass
                                       shape, then the same O(1) space collapse
    LC 152  Maximum Product Subarray— running max AND min, because a negative
                                       flips them
    LC 135  Candy                   — left-to-right pass then right-to-left,
                                       taking the max of the two
    LC 303  Range Sum Query         — the additive version of prefix arrays
    LC 560  Subarray Sum Equals K   — prefix sums + a hash map
    LC 724  Find Pivot Index        — left sum vs right sum, one pass
    LC 2270 Number of Ways to Split — the same left/right split idea
================================================================================
"""

import time
from typing import List


class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        """Output array + one scalar. Time O(n), O(1) extra. nums untouched."""
        n = len(nums)
        answer = [1] * n

        running = 1                      # empty product == 1, never 0
        for i in range(n):               # left to right: prefixes
            answer[i] = running          # write BEFORE updating
            running *= nums[i]

        running = 1                      # reset between passes
        for i in range(n - 1, -1, -1):   # right to left: fold in suffixes
            answer[i] *= running         # write BEFORE updating
            running *= nums[i]

        return answer

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def productExceptSelf_two_arrays(self, nums: List[int]) -> List[int]:
        """Explicit prefix and suffix arrays. O(n) space — clearer to read."""
        n = len(nums)
        prefix = [1] * n
        suffix = [1] * n
        for i in range(1, n):
            prefix[i] = prefix[i - 1] * nums[i - 1]      # nums[i-1], not nums[i]
        for i in range(n - 2, -1, -1):
            suffix[i] = suffix[i + 1] * nums[i + 1]      # nums[i+1], not nums[i]
        return [prefix[i] * suffix[i] for i in range(n)]

    def productExceptSelf_division(self, nums: List[int]) -> List[int]:
        """Division + zero counting. Banned here, but correct — know why."""
        zeros = nums.count(0)
        if zeros > 1:
            return [0] * len(nums)
        if zeros == 1:
            prod = 1
            for v in nums:
                if v != 0:
                    prod *= v
            return [prod if v == 0 else 0 for v in nums]
        total = 1
        for v in nums:
            total *= v
        return [total // v for v in nums]

    def productExceptSelf_bruteforce(self, nums: List[int]) -> List[int]:
        """O(n^2) baseline, for the benchmark only."""
        n = len(nums)
        out = []
        for i in range(n):
            p = 1
            for j in range(n):
                if j != i:
                    p *= nums[j]
            out.append(p)
        return out


# ==============================================================================
# TESTS — run:  python 010_product_of_array_except_self_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 2, 3, 4], [24, 12, 8, 6]),
        ([-1, 1, 0, -3, 3], [0, 0, 9, 0, 0]),
        ([2, 3], [3, 2]),
        ([0, 0], [0, 0]),
        ([1, 0], [0, 1]),
        ([0, 4, 0], [0, 0, 0]),
        ([-1, -1, -1], [1, 1, 1]),
        ([1, 1, 1, 1], [1, 1, 1, 1]),
        ([5, 2, 1, 3], [6, 15, 30, 10]),
        ([-30, 30, -30], [-900, 900, -900]),
    ]
    impls = [
        ("output+scalar", sol.productExceptSelf),
        ("two arrays   ", sol.productExceptSelf_two_arrays),
        ("division     ", sol.productExceptSelf_division),
        ("brute force  ", sol.productExceptSelf_bruteforce),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(nums)) == exp for nums, exp in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # ----------------------------------------------------------------------
    # Watch the output array get used twice.
    # ----------------------------------------------------------------------
    print("\n--- the output array as scratch space, nums = [1,2,3,4] ---")
    nums = [1, 2, 3, 4]
    n = len(nums)
    answer = [1] * n
    print("  PASS 1 (left to right) — answer[i] becomes the PREFIX product")
    running = 1
    for i in range(n):
        answer[i] = running
        running *= nums[i]
        print(f"    i={i}  wrote {answer[i]:>2}   running -> {running:>2}"
              f"   answer = {answer}")
    print("  PASS 2 (right to left) — fold the SUFFIX in with one scalar")
    running = 1
    for i in range(n - 1, -1, -1):
        answer[i] *= running
        running *= nums[i]
        print(f"    i={i}  answer[{i}] -> {answer[i]:>2}  running -> {running:>2}"
              f"   answer = {answer}")

    # ----------------------------------------------------------------------
    # ⚠️  The empty product is 1. Start at 0 and everything dies.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  initialising the running product to 0 ---")

    def with_seed(nums, seed):
        n = len(nums)
        answer = [1] * n
        running = seed
        for i in range(n):
            answer[i] = running
            running *= nums[i]
        running = seed
        for i in range(n - 1, -1, -1):
            answer[i] *= running
            running *= nums[i]
        return answer

    print(f"  running = 1 (correct) -> {with_seed([1, 2, 3, 4], 1)}")
    print(f"  running = 0 (bug)     -> {with_seed([1, 2, 3, 4], 0)}")
    print("  0 is the ANNIHILATOR for multiplication; 1 is the identity.")

    # ----------------------------------------------------------------------
    # ⚠️  Update-before-write makes the prefix inclusive.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  swapping the two lines inside the loop ---")

    def swapped(nums):
        n = len(nums)
        answer = [1] * n
        running = 1
        for i in range(n):
            running *= nums[i]           # updated FIRST — now includes nums[i]
            answer[i] = running
        running = 1
        for i in range(n - 1, -1, -1):
            running *= nums[i]
            answer[i] *= running
        return answer

    nums = [1, 2, 3, 4]
    print(f"  nums               {nums}")
    print(f"  write-then-update  {sol.productExceptSelf(list(nums))}   ✓")
    print(f"  update-then-write  {swapped(list(nums))}   ✗")
    got = swapped(list(nums))
    want = sol.productExceptSelf(list(nums))
    print(f"  ratio per index    {[g // w for g, w in zip(got, want)]}"
          f"  <- exactly nums[i]^2: nums[i] leaked into BOTH passes")

    # ----------------------------------------------------------------------
    # ⚠️  Division really does explode.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the division shortcut, unguarded ---")
    nums = [1, 2, 0, 4]
    total = 1
    for v in nums:
        total *= v
    print(f"  nums = {nums}   total = {total}")
    try:
        print([total // v for v in nums])
    except ZeroDivisionError as e:
        print(f"  [total // v for v in nums] -> ZeroDivisionError: {e}")
    print(f"  guarded division           -> {sol.productExceptSelf_division(list(nums))}")
    print(f"  prefix/suffix (no branches)-> {sol.productExceptSelf(list(nums))}")

    # ----------------------------------------------------------------------
    # Zeros need no special case — see the two halves.
    # ----------------------------------------------------------------------
    print("\n--- why zeros are free, nums = [-1,1,0,-3,3] ---")
    nums = [-1, 1, 0, -3, 3]
    n = len(nums)
    prefix, suffix = [1] * n, [1] * n
    for i in range(1, n):
        prefix[i] = prefix[i - 1] * nums[i - 1]
    for i in range(n - 2, -1, -1):
        suffix[i] = suffix[i + 1] * nums[i + 1]
    print(f"  nums     {nums}")
    print(f"  prefix   {prefix}")
    print(f"  suffix   {suffix}")
    print(f"  answer   {[prefix[i] * suffix[i] for i in range(n)]}")
    print("  Index 2 is the only survivor: the 0 IS nums[2], so neither its")
    print("  prefix nor its suffix contains it. No branch ever tested for 0.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n^2).
    # ----------------------------------------------------------------------
    print("\n--- O(n) vs O(n^2) ---")
    prev = None
    for n in (500, 1000, 2000):
        data = [(i % 7) + 1 for i in range(n)]
        t0 = time.perf_counter(); sol.productExceptSelf(data)
        t_lin = time.perf_counter() - t0
        t0 = time.perf_counter(); sol.productExceptSelf_bruteforce(data)
        t_quad = time.perf_counter() - t0
        growth = f"{t_quad / prev:4.1f}x" if prev else "  -  "
        prev = t_quad
        print(f"  n={n:<6} prefix/suffix {t_lin*1000:7.2f}ms   "
              f"brute {t_quad*1000:8.2f}ms ({growth})   "
              f"{t_quad / max(t_lin, 1e-9):5.0f}x slower")
    print("  Doubling n roughly quadruples the brute force. That is the n^2.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
