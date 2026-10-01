"""
================================================================================
SOLUTION · LeetCode 2 · Add Two Numbers                                [Medium]
https://leetcode.com/problems/add-two-numbers/
================================================================================

THE CORE IDEA
--------------
Digits are stored least-significant-first — exactly the order grade-school
column addition processes them in. Walk both lists together, at each
position add `d1 + d2 + carry`, emit `(sum % 10)` as the new digit, and
carry `sum // 10` into the next position:

    dummy = ListNode()
    curr = dummy
    carry = 0
    while l1 or l2 or carry:
        d1 = l1.val if l1 else 0
        d2 = l2.val if l2 else 0
        total = d1 + d2 + carry
        carry, digit = divmod(total, 10)
        curr.next = ListNode(digit)
        curr = curr.next
        l1 = l1.next if l1 else None
        l2 = l2.next if l2 else None
    return dummy.next

The loop condition `l1 or l2 or carry` is the whole problem in one
expression: keep going while there's a digit left in EITHER list, OR a
leftover carry needs one more node. A dummy head (topic guide Part 2) means
"build a brand-new result list from nothing" needs no special case for the
first node — exactly the fourth use case the topic guide lists for the
dummy-head idiom.


================================================================================
APPROACH 1 · Convert to integers, add, convert back (state it, price it)
================================================================================
    n1 = int(''.join(str(d) for d in reversed(digits(l1))))
    n2 = int(''.join(str(d) for d in reversed(digits(l2))))
    return build(str(n1 + n2)[::-1])

Correct in Python (arbitrary-precision ints), and O(m+n) time/space just like
the digit-by-digit version — but it doesn't generalize: in a language with
fixed-width integers (Go's int64, Java's long), lists up to 100 digits
(constraint) would OVERFLOW any native integer type. This is a real trap to
name out loud: Python's big-int convenience can hide a bug that would crash
in Go/Java/C++, so the digit-by-digit approach is the one to lead with even
though the integer-conversion trick "looks" simpler in Python specifically.


================================================================================
APPROACH 2 · Digit-by-digit with carry ✅ (the answer)
================================================================================
See THE CORE IDEA above. O(max(m, n)) time, O(max(m, n)) space for the
required output list (not extra beyond what the answer needs).


================================================================================
STEP BY STEP TRACE
================================================================================
l1 = [2,4,3] (= 342), l2 = [5,6,4] (= 465)   ->   342 + 465 = 807

    dummy -> None
    curr = dummy, carry = 0

    pos 0: d1=2 d2=5 carry=0   total=7    digit=7 carry=0   emit 7
           dummy -> [7]
    pos 1: d1=4 d2=6 carry=0   total=10   digit=0 carry=1   emit 0
           dummy -> [7] -> [0]
    pos 2: d1=3 d2=4 carry=1   total=8    digit=8 carry=0   emit 8
           dummy -> [7] -> [0] -> [8]
    l1 and l2 both exhausted, carry=0 -> STOP

    return [7,0,8]   (= 807)   ✓


CARRY-PROPAGATES-PAST-THE-END TRACE — 999 + 1 (the case with an EXTRA node)
------------------------------------------------------------------------------
l1 = [9,9,9] (= 999), l2 = [1] (= 1)   ->   999 + 1 = 1000

    pos 0: d1=9 d2=1 carry=0   total=10   digit=0 carry=1   emit 0
           dummy -> [0]
    pos 1: d1=9 d2=0 carry=1   total=10   digit=0 carry=1   emit 0
           (l2 exhausted after pos 0 -> d2 defaults to 0)
           dummy -> [0] -> [0]
    pos 2: d1=9 d2=0 carry=1   total=10   digit=0 carry=1   emit 0
           (l1 also now exhausted after this digit)
           dummy -> [0] -> [0] -> [0]
    l1 and l2 both exhausted, but carry=1 is still nonzero -> LOOP CONTINUES
    pos 3: d1=0 d2=0 carry=1   total=1    digit=1 carry=0   emit 1
           dummy -> [0] -> [0] -> [0] -> [1]
    carry=0, l1 and l2 exhausted -> STOP

    return [0,0,0,1]   (= 1000, reversed)   ✓
    Note the result has 4 nodes even though the longer input had only 3 —
    the trailing carry is exactly the case `while ... or carry:` exists for.
    Forgetting the `or carry` clause drops this final digit entirely.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time          Space           Mutates input?
    --------------------------------  ------------  --------------  -----------------
    Convert to int, add, convert back O(max(m,n))   O(max(m,n))     no (Python-only;
                                                                        overflows in
                                                                        fixed-width
                                                                        languages)
    Digit-by-digit with carry ✅      O(max(m,n))   O(max(m,n))     no (builds new list;
                                                                        l1/l2 untouched)


================================================================================
EDGE CASES
================================================================================
    [0] + [0]                -> [0]. Smallest legal input per constraints
                                 (each list has >= 1 node); the "no leading
                                 zeros except zero itself" rule permits this
                                 single-zero case explicitly.
    Different lengths          -> shorter list's missing digits default to 0
                                 via `d1 = l1.val if l1 else 0`; traced above
                                 (999 + 1).
    Final carry needs an EXTRA node -> `while l1 or l2 or carry` (not `while
                                 l1 or l2`) is what catches this; traced
                                 above. Classic failure mode: 5+5=10 needs a
                                 second node even though both inputs are
                                 single-digit.
    Both lists the same length, no final carry -> traced above (342+465=807,
                                 exactly 3 digits in, 3 digits out).
    Result requires MORE digits than either input -> e.g. 99+1=100 (3 nodes
                                 from 2- and 1-node inputs), the general case
                                 of the "extra node" edge case above.


================================================================================
COMMON MISTAKES
================================================================================
1. `while l1 and l2:` instead of `while l1 or l2 or carry:` — stops at the
   SHORTER list's end, silently dropping the longer list's remaining digits
   entirely (not even carrying them through as "digit + 0").

2. `while l1 or l2:` (dropping `or carry`) — handles different lengths
   correctly but drops the FINAL carry digit, e.g. turns 999+1=1000 into
   999+1=000 (missing the leading 1). See the traced example above.

3. Forgetting a dummy head and hand-writing the first node as a special case
   — unnecessary branching for exactly the situation Part 2 of the topic
   guide exists to eliminate.

4. Advancing `l1 = l1.next` unconditionally without checking `l1 is not
   None` first — crashes with `AttributeError: 'NoneType' object has no
   attribute 'next'` the moment one list is shorter than the other.

5. Using the "convert to int" shortcut as the PRIMARY answer without naming
   its fixed-width-integer overflow risk in other languages — technically
   correct in Python only, and interviewers often follow up by asking "what
   if you couldn't rely on big integers?"

6. Computing `digit, carry = total % 10, total // 10` in the WRONG order
   into a two-value unpack, or reversing which is which — always sanity
   check against `divmod(total, 10)` returning `(quotient, remainder)` =
   `(carry, digit)`, not `(digit, carry)`.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the digits were stored in FORWARD order instead (most-significant
   first), as in LC 445 (Add Two Numbers II)?
A: You can no longer add from the head outward, since you need the ones
   place first. Either reverse both lists first (topic guide §4.1's
   reversal template, add, then reverse the result back), or push both
   lists onto stacks and pop from the end — same effect, O(n) extra space
   either way.

Q: Can you avoid creating a new list and mutate one of the inputs in place?
A: Yes — reuse the longer list's nodes as the result spine, only allocating
   a new node for the final carry-driven extra digit (if any) and for any
   position past the shorter list's end where the longer list's node can
   simply have its `.val` updated in place. Saves allocations, not
   complexity class; complicates the code for the shorter list's early-exit
   case. Trade-off to name if asked, not necessarily to code by default.

Q: What if one or both numbers could be negative?
A: The problem's non-negative constraint keeps this simple; supporting sign
   would require tracking sign separately and possibly doing subtraction
   with borrow instead of addition with carry when signs differ — a
   meaningfully different algorithm, not a small tweak.

Q: How would you validate there are no leading zeros in the input, per the
   stated guarantee?
A: You wouldn't need to for LeetCode's guaranteed-valid input, but if
   asked: since digits are LSB-first, "leading zero" means the LAST node's
   val is 0 while the list has more than one node — check the tail.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 445  Add Two Numbers II              — forward-order digits; needs
                                                reversal or a stack first
    LC 43   Multiply Strings                 — same digit-by-digit-with-carry
                                                idea, generalized to
                                                multiplication (carries
                                                propagate differently)
    LC 67   Add Binary                       — identical carry-propagation
                                                shape, base 2 on strings
                                                instead of base 10 on a
                                                linked list
    LC 19   Remove Nth From End              — different technique, same
                                                dummy-head idiom (problem 009
                                                here)
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        """Digit-by-digit with carry, dummy head. O(max(m,n)) time,
        O(max(m,n)) space for the required output. See THE CORE IDEA above."""
        dummy = ListNode()
        curr = dummy
        carry = 0
        while l1 or l2 or carry:
            d1 = l1.val if l1 else 0
            d2 = l2.val if l2 else 0
            total = d1 + d2 + carry
            carry, digit = divmod(total, 10)
            curr.next = ListNode(digit)
            curr = curr.next
            l1 = l1.next if l1 else None
            l2 = l2.next if l2 else None
        return dummy.next

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def addTwoNumbers_via_int(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        """Convert both lists to Python big-ints, add, convert back. Correct
        ONLY because Python has arbitrary-precision integers — would
        overflow fixed-width integers in Go/Java/C++. See Approach 1."""
        def to_int(node):
            digits = []
            while node:
                digits.append(str(node.val))
                node = node.next
            return int(''.join(reversed(digits)) or '0')

        total = to_int(l1) + to_int(l2)
        s = str(total)
        dummy = ListNode()
        curr = dummy
        for ch in reversed(s):
            curr.next = ListNode(int(ch))
            curr = curr.next
        return dummy.next

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def addTwoNumbers_drops_final_carry(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        """✗ BROKEN ON PURPOSE — `while l1 or l2:` without `or carry`. Drops
        the trailing carry digit, e.g. turns 999+1=1000 into 000. See
        common mistake #2."""
        dummy = ListNode()
        curr = dummy
        carry = 0
        while l1 or l2:            # BUG: missing `or carry`
            d1 = l1.val if l1 else 0
            d2 = l2.val if l2 else 0
            total = d1 + d2 + carry
            carry, digit = divmod(total, 10)
            curr.next = ListNode(digit)
            curr = curr.next
            l1 = l1.next if l1 else None
            l2 = l2.next if l2 else None
        return dummy.next


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build(digits):
    dummy = ListNode()
    curr = dummy
    for d in digits:
        curr.next = ListNode(d)
        curr = curr.next
    return dummy.next


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


CASES = [
    ([2, 4, 3], [5, 6, 4], [7, 0, 8]),
    ([0], [0], [0]),
    ([9, 9, 9, 9, 9, 9, 9], [9, 9, 9, 9], [8, 9, 9, 9, 0, 0, 0, 1]),
    ([9, 9], [1], [0, 0, 1]),
    ([5], [5], [0, 1]),
    ([1, 2, 3], [4, 5, 6, 7], [5, 7, 9, 7]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: digit-by-digit vs int-conversion oracle ---")
    for d1, d2, expected in CASES:
        got1 = to_list(sol.addTwoNumbers(build(d1), build(d2)))
        got2 = to_list(sol.addTwoNumbers_via_int(build(d1), build(d2)))
        ok = got1 == expected and got2 == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {d1!r} + {d2!r} -> digit-by-digit={got1} "
              f"int-conv={got2}  (want {expected})")

    # ----------------------------------------------------------------------
    # Trace: carry propagates past the end (999 + 1).
    # ----------------------------------------------------------------------
    print("\n--- trace: 999 + 1 (carry produces an EXTRA node) ---")
    l1, l2 = build([9, 9, 9]), build([1])
    curr_l1, curr_l2 = l1, l2
    carry = 0
    pos = 0
    digits_out = []
    while curr_l1 or curr_l2 or carry:
        d1 = curr_l1.val if curr_l1 else 0
        d2 = curr_l2.val if curr_l2 else 0
        total = d1 + d2 + carry
        carry, digit = divmod(total, 10)
        digits_out.append(digit)
        print(f"  pos {pos}: d1={d1} d2={d2} carry_in={carry if False else (total - d1 - d2)}  "
              f"total={total}  -> digit={digit} carry_out={carry}")
        curr_l1 = curr_l1.next if curr_l1 else None
        curr_l2 = curr_l2.next if curr_l2 else None
        pos += 1
    print(f"  result digits (reverse order) = {digits_out}  (represents {int(''.join(map(str, reversed(digits_out))))})")
    trace_ok = digits_out == [0, 0, 0, 1]
    all_ok &= trace_ok
    print(f"  matches expected [0,0,0,1]: {trace_ok}")

    # ----------------------------------------------------------------------
    # ⚠️ Dropped final carry demo.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ `while l1 or l2` (missing `or carry`): drops the final digit ---")
    print(f"  {'l1':<12} {'l2':<8} {'correct':<14} {'broken':<14}  ok?")
    dropped_mismatch = False
    for d1, d2, expected in [([9, 9, 9], [1], [0, 0, 0, 1]), ([5], [5], [0, 1]), ([9], [9], [8, 1])]:
        good = to_list(sol.addTwoNumbers(build(d1), build(d2)))
        bad = to_list(sol.addTwoNumbers_drops_final_carry(build(d1), build(d2)))
        mismatch = good != bad
        dropped_mismatch |= mismatch
        print(f"  {str(d1):<12} {str(d2):<8} {str(good):<14} {str(bad):<14}  "
              f"{'yes' if not mismatch else 'NO  <- final carry digit missing'}")
    print(f"  dropped-carry bug reproduced: {dropped_mismatch}")
    all_ok &= dropped_mismatch

    # ----------------------------------------------------------------------
    # Randomised cross-check against Python big-int addition.
    # ----------------------------------------------------------------------
    import random as pyrandom
    print("\n--- randomised cross-check vs int-conversion oracle ---")
    pyrandom.seed(11)
    trials, mismatches = 2000, 0
    for _ in range(trials):
        len1 = pyrandom.randint(1, 20)
        len2 = pyrandom.randint(1, 20)
        d1 = [pyrandom.randint(0, 9) for _ in range(len1)]
        d2 = [pyrandom.randint(0, 9) for _ in range(len2)]
        # avoid leading zeros unless the number is exactly [0], matching constraints
        if len1 > 1:
            d1[-1] = d1[-1] or 1
        if len2 > 1:
            d2[-1] = d2[-1] or 1
        got = to_list(sol.addTwoNumbers(build(d1), build(d2)))
        want = to_list(sol.addTwoNumbers_via_int(build(d1), build(d2)))
        if got != want:
            mismatches += 1
    print(f"  {trials} random lists (1-20 digits each): {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
