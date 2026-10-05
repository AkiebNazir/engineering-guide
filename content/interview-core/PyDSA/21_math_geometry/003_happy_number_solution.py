"""
================================================================================
SOLUTION · LeetCode 202 · Happy Number                               [Easy]
https://leetcode.com/problems/happy-number/
================================================================================

THE CORE IDEA
--------------
Repeatedly applying `f(x) = sum of squares of x's digits` defines a
deterministic sequence: x0 -> x1 -> x2 -> ... where `f` is just a plain
function call, not a data structure pointer. Because the digit-square-sum
of any number with d digits is bounded (at most `d * 81`, and this bound
shrinks fast once x has more than 3 digits, since `9999 * 81` still has
far fewer digits than 9999), the sequence is eventually confined to a
small finite range of values -- which means by the pigeonhole principle it
MUST either reach 1 (and then stay there, since f(1) = 1) or fall into a
repeating cycle that never touches 1. This is EXACTLY the shape of
**topic 08's linked-list cycle detection** (`003_linked_list_cycle`,
`012_find_the_duplicate_number`) with "follow `.next`" replaced by
"evaluate `f(x)`" -- the same two techniques apply unchanged:

  (a) a `seen` SET: keep applying f, and if you ever see a value you've
      seen before (and it isn't 1), you're in a cycle -- not happy. O(n)
      extra space for the set of visited values.
  (b) FLOYD'S slow/fast pointer (tortoise and hare): advance `slow` by one
      application of f per step, `fast` by two; if `fast` ever hits 1,
      happy; if `slow == fast` before that (and neither is 1), a cycle
      exists that doesn't include 1 -- not happy. O(1) extra space.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (price it): run the process forever with no cycle detection at
all -- WRONG, because unhappy numbers loop forever and this never
terminates. Not a real approach, but it's worth stating explicitly why
"just keep iterating" fails: you need SOME mechanism to recognize you've
returned to a state you've already visited.

Approach 1 (seen-set) -- O(n) extra space, straightforward, easy to get
right first try. Implemented as `_is_happy_seen_set` below and used as the
default/simple choice.

Approach 2 (chosen for the main solution) -- Floyd's cycle detection,
O(1) extra space, directly parallel to the linked-list version in topic 08.
Both are correct and O(1) time per "step" of f; the seen-set is O(1)
amortized total extra work per number checked while Floyd's does a bit
more arithmetic (two `f` calls per outer step) but needs zero extra
memory. In an interview either is a fully acceptable answer -- Floyd's is
the one worth having ready because it demonstrates the cross-domain
technique transfer explicitly.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 19 (happy) -- seen-set version:

    seen = {}, x = 19
    x=19  -> f(19) = 1^2+9^2 = 1+81 = 82           seen={19}, x=82
    x=82  -> f(82) = 8^2+2^2 = 64+4 = 68           seen={19,82}, x=68
    x=68  -> f(68) = 6^2+8^2 = 36+64 = 100         seen={19,82,68}, x=100
    x=100 -> f(100) = 1^2+0^2+0^2 = 1              seen={19,82,68,100}, x=1
    x == 1 -> HAPPY, return True


n = 2 (not happy) -- Floyd's version:

    slow = 2, fast = 2
    step 1: slow = f(2) = 4
            fast = f(f(2)) = f(4) = 16
            slow(4) != fast(16), neither is 1, continue
    step 2: slow = f(4) = 16
            fast = f(f(16)) = f(37) = 3^2+7^2=9+49=58
            slow(16) != fast(58), continue
    step 3: slow = f(16) = 37
            fast = f(f(58)) = f(89) = 8^2+9^2=64+81=145
            slow(37) != fast(145), continue
    step 4: slow = f(37) = 58
            fast = f(f(145)) = f(42) = 16+4=20
            slow(58) != fast(20), continue
    step 5: slow = f(58) = 89
            fast = f(f(20)) = f(4) = 16
            slow(89) != fast(16), continue
    step 6: slow = f(89) = 145
            fast = f(f(16)) = f(37) = 58
            slow(145) != fast(58), continue
    step 7: slow = f(145) = 42
            fast = f(f(58)) = f(89) = 145
            slow(42) != fast(145), continue
    step 8: slow = f(42) = 20
            fast = f(f(145)) = f(42) = 20
            slow(20) == fast(20), and neither is 1 -> CYCLE, not happy ->
            return False

    (the actual cycle for unhappy numbers is the well-known 8-number loop
     4 -> 16 -> 37 -> 58 -> 89 -> 145 -> 42 -> 20 -> 4 -> ...)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time         Space    Mutates input?
    ------------------------------------------------------------
    Seen-set                O(1)*        O(1)*      no
    Floyd's (chosen)        O(1)*        O(1)       no

    *Both are technically bounded by a constant because the digit-square-
    sum function confines any input into the range [1, 243] within one
    application (a 3-digit number's max digit-square-sum is 3*81=243,
    and it only takes one step to get any n down to at most a handful of
    digits), so the number of distinct states -- and therefore the number
    of steps before a repeat -- is bounded by a fixed constant independent
    of how large n starts. Framed relative to the number of DIGITS d in
    the starting n, both are O(d) for the very first step (digit
    extraction) and O(1) for everything after.


================================================================================
EDGE CASES
================================================================================
    n == 1               -> happy immediately, by definition (f(1) = 1,
                             the loop's base case); must not be misread as
                             "hasn't been checked yet" and treated as a
                             cycle.
    n is already a cycle
    member, e.g. n == 4   -> not happy; enters the 8-number cycle
                             immediately without ever visiting 1.
    n == 7                -> happy (a real single-digit happy number,
                             worth testing since most single-digit numbers
                             are NOT happy -- easy to over-generalize from
                             "small numbers are usually not happy").
    large n (up to 2^31-1) -> digit-square-sum collapses it to a small
                             number within the FIRST application of f, so
                             large starting values are not actually a
                             performance concern.
    no negative numbers   -> constraint guarantees n >= 1; squares of
                             digits are always non-negative regardless.


================================================================================
COMMON MISTAKES
================================================================================
1. No cycle detection at all -- naively looping "while n != 1" on an
   unhappy number runs forever; you MUST detect the cycle to terminate.
2. Off-by-one in Floyd's: comparing `slow == fast` BEFORE ever advancing
   either pointer (both start equal to n, trivially "equal" with zero
   information) -- must advance at least once before the first comparison.
3. In the seen-set version, checking `x in seen` AFTER already computing
   `f(x)` and overwriting x, losing the ability to correctly report which
   value repeated (functionally survivable here since only membership
   matters, but a common source of confusion when adapting this pattern).
4. Confusing "sum of digits" with "sum of squares of digits" -- the
   digit-SQUARING is what confines the sequence into a bounded range and
   makes termination provable; plain digit-summing converges to a
   single-digit value by a different (also true, but unrelated) fact.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you do this without extra memory?" -> Yes, Floyd's slow/fast
  pointer, O(1) space -- exactly the technique from linked-list cycle
  detection (topic 08), applied to the function `f` instead of `.next`.
- "How do you know the process always terminates (either at 1 or a
  cycle) instead of growing without bound?" -> The digit-square-sum of any
  number is bounded by `9^2 * (number of digits)`, and for numbers beyond
  3 digits this bound is smaller than the number itself, so the sequence
  is squeezed into a finite range after the first step or two -- pigeonhole
  then guarantees a repeat.
- "What's the actual unhappy cycle?" -> `4 -> 16 -> 37 -> 58 -> 89 -> 145
  -> 42 -> 20 -> 4`, the same 8 numbers every unhappy chain eventually
  reaches.


================================================================================
RELATED PROBLEMS
================================================================================
- Linked List Cycle (LC 141, topic 08, 003) -- identical cycle-detection
  technique (seen-set or Floyd's), over `.next` pointers instead of `f(x)`.
- Find the Duplicate Number (LC 287, topic 08, 012) -- Floyd's applied to
  an array treated as an implicit linked list via value-as-index.
- Ugly Number (LC 263) -- another "repeatedly apply an operation and check
  a terminating condition" digit/number-theory problem.
================================================================================
"""

import time


def _digit_square_sum(x: int) -> int:
    total = 0
    while x > 0:
        x, digit = divmod(x, 10)
        total += digit * digit
    return total


class Solution:
    def isHappy(self, n: int) -> bool:
        # Floyd's slow/fast pointer over the function f = digit-square-sum,
        # exactly parallel to linked-list cycle detection (topic 08).
        slow = n
        fast = _digit_square_sum(n)
        while fast != 1 and slow != fast:
            slow = _digit_square_sum(slow)
            fast = _digit_square_sum(_digit_square_sum(fast))
        return fast == 1


def _is_happy_seen_set(n: int) -> bool:
    """The O(n)-extra-space alternative, kept for the cross-check demo."""
    seen = set()
    while n != 1 and n not in seen:
        seen.add(n)
        n = _digit_square_sum(n)
    return n == 1


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        (19, True),
        (2, False),
        (1, True),
        (7, True),
        (4, False),
        (100, True),
        (116, False),
        (58, False),
        (2147483647, False),
    ]
    for n, expected in cases:
        got = sol.isHappy(n)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  isHappy({n}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- Floyd's vs seen-set, n = 1..20000")
    print("-" * 72)
    mismatch = 0
    for n in range(1, 20_001):
        a = sol.isHappy(n)
        b = _is_happy_seen_set(n)
        if a != b:
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {20000 - mismatch}/20000 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- Floyd's (O(1) space) vs seen-set (O(n) space), measured live")
    print("-" * 72)
    trials = list(range(1, 100_001))

    t0 = time.perf_counter()
    for n in trials:
        sol.isHappy(n)
    floyd_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for n in trials:
        _is_happy_seen_set(n)
    seenset_ms = (time.perf_counter() - t0) * 1000

    print(f"n=1..100000, isHappy called once per value:")
    print(f"  Floyd's (O(1) extra space):   {floyd_ms:8.2f} ms")
    print(f"  seen-set (O(cycle) space):    {seenset_ms:8.2f} ms")
    if seenset_ms < floyd_ms:
        print(f"  measured: seen-set is {floyd_ms / seenset_ms:.2f}x FASTER here -- Floyd's does "
              f"roughly 3 calls to f() per outer step (one for slow, two for fast) versus the "
              f"seen-set's 1 call per step plus a hash-set lookup; the set approach wins on wall "
              f"clock at this scale despite using more memory. Floyd's O(1)-space guarantee is "
              f"still the right answer when memory is the binding constraint.")
    else:
        print(f"  measured: Floyd's is {seenset_ms / floyd_ms:.2f}x faster here.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
