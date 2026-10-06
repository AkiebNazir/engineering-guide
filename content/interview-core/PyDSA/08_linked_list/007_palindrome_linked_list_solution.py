"""
================================================================================
SOLUTION · LeetCode 234 · Palindrome Linked List                        [Easy]
https://leetcode.com/problems/palindrome-linked-list/
================================================================================

THE CORE IDEA
--------------
A palindrome check wants both ends at once; a singly linked list only walks
forward. Two ways to manufacture "the other end":

    O(n) space: copy values into an array — arrays support backward
                indexing, so run the ordinary two-pointer check there.
    O(1) space: find the middle (§3.1), reverse the second half in place
                (§4.1), then walk the first half and the reversed second
                half TOGETHER as if they were two independent forward lists
                meeting in the middle.

Both are O(n) time. The follow-up explicitly asks for O(1) space, so know
both, lead with the array version to show you have a baseline, then deliver
the in-place version as the answer.


================================================================================
APPROACH 1 · Copy to array, two-pointer check (O(n) space)
================================================================================
    vals = []
    node = head
    while node:
        vals.append(node.val)
        node = node.next
    return vals == vals[::-1]

Simple, obviously correct, never mutates the list. Costs O(n) extra space —
exactly the array/list-of-values buffer. `vals[::-1]` itself allocates a
second O(n) buffer in Python; a tighter version uses topic 02's two-pointer
scan (`lo, hi = 0, len(vals)-1`) to avoid that second allocation, though the
overall space class stays O(n) either way (the buffer of values IS the cost,
not the comparison strategy).


================================================================================
APPROACH 2 · Find middle + reverse second half + compare ✅ (O(1) space)
================================================================================
This is 004 (find the middle) and 001 (reversal), composed — the same
composition idea the topic guide's §4.2 uses for Reorder List (problem 008).

    1. slow/fast to the middle (§3.1)
    2. reverse everything from the middle onward (§4.1)
    3. walk `head` and the reversed second-half's new head together,
       comparing `.val`; stop when either pointer runs out
    4. (nice touch) reverse the second half back and re-attach, so the
       caller's list is exactly as it was before the call — LeetCode does
       not require this, but a function whose signature looks read-only
       ideally shouldn't leave the input structurally altered

O(n) time (three linear passes: find middle, reverse, compare — still O(n)
total, not O(n^2)), O(1) EXTRA space (a handful of pointers, no buffer sized
by input length).


================================================================================
STEP BY STEP — head = [1, 2, 3, 2, 1]  (odd length)
================================================================================
    1 -> 2 -> 3 -> 2 -> 1 -> None

    slow/fast to the middle (§3.1):
      slow ends on the node valued 3 (the true middle of an odd-length list)

    split conceptually:        1 -> 2 -> 3          2 -> 1 -> None
                                first half           second half (from middle)

    reverse the second half (§4.1):   2 -> 1 -> None   becomes   1 -> 2 -> None

    compare, two forward pointers:
      p1 (from original head)     1 -> 2 -> 3
      p2 (from reversed 2nd half) 1 -> 2 -> None

      p1.val=1 vs p2.val=1  match
      p1.val=2 vs p2.val=2  match
      p1.val=3 vs p2.val=3  match   <- SAME physical node compared with itself
      p2 runs out (None)    -> stop; all compared pairs matched -> True

    Reversing starting AT `slow` (rather than `slow.next`) means the middle
    node ends up as the LAST element of the reversed second half too — so on
    an odd-length list, `p1` and `p2` converge on that exact same node object
    for the final comparison, a harmless self-comparison (a value always
    equals itself). This is not a bug: it costs one redundant comparison,
    never a wrong answer, and it's simpler than special-casing "skip the
    middle" separately for odd vs. even length.


================================================================================
STEP BY STEP — head = [1, 2, 2, 1]  (even length)
================================================================================
    1 -> 2 -> 2 -> 1 -> None

    slow/fast to the middle: slow ends on the SECOND 2 (first node of the
    second half, for even length — see the trap in COMMON MISTAKES #2)

    split:           1 -> 2          2 -> 1 -> None
    reverse 2nd half:                1 -> 2 -> None

    compare:
      p1: 1 -> 2       p2: 1 -> 2
      1 vs 1 match, 2 vs 2 match, both run out together -> True


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time   Space   Mutates input?  Note
    --------------------------------  -----  ------  ---------------  ------------------
    Copy to array + two-pointer ✅    O(n)   O(n)    no               baseline, simplest
    Middle + reverse + compare (raw)  O(n)   O(1)    yes (permanently) follow-up answer
    Middle + reverse + compare +     O(n)   O(1)    no (restored)    nice touch, same
      restore second half                                            asymptotics


================================================================================
EDGE CASES
================================================================================
    single node          -> True.  Trivially a palindrome; slow/fast never
                                   moves, "second half" is empty, compare
                                   loop runs zero times.
    two equal values       -> True.  [1,1] — even length, smallest nontrivial
                                   even case.
    two different values    -> False. [1,2] — smallest case that fails.
    odd length              -> the true middle node is excluded from
                                   comparison (see the trace above) — this is
                                   correct, not an off-by-one to "fix."
    all same value            -> always True regardless of length ([5,5,5]).
    long list (10^5 nodes)      -> the O(1)-space approach avoids allocating
                                   a 10^5-element buffer; matters at scale.


================================================================================
COMMON MISTAKES
================================================================================
1. Trying to use a two-pointer scan DIRECTLY on the linked list without
   copying or reversing anything — there is no way to move backward from the
   tail on a singly linked list, so this is not expressible at all without
   one of the two transformations above.
2. Getting the middle split wrong for EVEN-length lists — slow/fast
   (`while fast and fast.next`) lands `slow` on the FIRST node of the second
   half for even length, but on the TRUE middle for odd length. Reversing
   from the wrong node either double-counts or drops a comparison.
3. Forgetting that the compare loop must stop when EITHER pointer runs out,
   not both — for odd length, `p1` still has the (irrelevant) middle node
   left after `p2` is exhausted; continuing to dereference `p1.next` off a
   `None` `p2` crashes.
4. Losing the reference to the first half's tail before reversing the second
   half — if you reverse starting from the wrong node, or reuse a variable
   that still pointed at "the node before the split" for something else,
   the seam between the two halves gets corrupted (topic guide Part 1.3:
   save before you destroy).
5. Claiming the O(1)-space version is "no side effects" without restoring
   the list — it silently reverses the second half of the CALLER's list
   unless you explicitly reverse it back. Fine for LeetCode's grading
   (checked once, list discarded), a real correctness bug if this function
   is called from code that reuses the list afterward.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do it in O(1) space AND leave the list completely unchanged
   afterward?
A: Yes — after comparing, reverse the (still-reversed) second half back to
   its original direction and re-attach it to the first half's tail. Same
   O(n) time, same O(1) extra space; costs one more full pass over the
   second half. Included in this solution's `isPalindrome_restore` variant.

Q: What if the list were doubly linked?
A: Then two pointers — one from `head` walking `.next`, one from the tail
   walking `.prev` — solve it directly in O(n) time, O(1) space, with no
   reversal step needed at all; the backward pointer IS the missing piece
   that forced the reversal trick on a singly linked list.

Q: How would you check if an ARRAY (not a linked list) is a palindrome?
A: Directly with topic 02's converging two-pointer scan — `lo, hi = 0,
   len(a)-1`; that's the technique this problem's O(n)-space approach
   effectively simulates by first copying into an array.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 206  Reverse Linked List        — the reversal template reused here
                                          (problem 001)
    LC 876  Middle of the Linked List  — the slow/fast half-finder reused
                                          here (problem 004)
    LC 143  Reorder List               — same two techniques, composed
                                          differently, plus a merge/interleave
                                          (problem 008 here — see topic guide
                                          §4.2)
    LC 9    Palindrome Number           — same idea (reverse half, compare),
                                          applied to digits of an int instead
                                          of linked-list nodes
================================================================================
"""

import time
from typing import List, Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def isPalindrome(self, head: Optional[ListNode]) -> bool:
        """Find middle (§3.1) + reverse second half (§4.1) + compare.
        O(n) time, O(1) extra space. PERMANENTLY reverses the second half of
        the caller's list as a side effect — see isPalindrome_restore for the
        version that undoes that. The answer for the O(1)-space follow-up."""
        if not head or not head.next:
            return True

        # 1. find the middle
        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next

        # 2. reverse the second half, starting at `slow`
        prev = None
        curr = slow
        while curr:
            nxt = curr.next
            curr.next = prev
            prev = curr
            curr = nxt
        second_head = prev

        # 3. compare the first half against the reversed second half
        p1, p2 = head, second_head
        result = True
        while p1 and p2:
            if p1.val != p2.val:
                result = False
                break
            p1 = p1.next
            p2 = p2.next
        return result

    def isPalindrome_restore(self, head: Optional[ListNode]) -> bool:
        """Same as isPalindrome, but reverses the second half BACK and
        re-attaches it afterward, so the caller's list is unchanged. Same
        O(n) time / O(1) space, one extra pass. The 'nice touch' variant."""
        if not head or not head.next:
            return True

        slow = fast = head
        while fast and fast.next:
            slow = slow.next
            fast = fast.next.next

        # remember the node right before the split, to re-attach later
        first_tail = head
        while first_tail.next is not slow:
            first_tail = first_tail.next

        prev = None
        curr = slow
        while curr:
            nxt = curr.next
            curr.next = prev
            prev = curr
            curr = nxt
        second_head = prev

        p1, p2 = head, second_head
        result = True
        while p1 and p2:
            if p1.val != p2.val:
                result = False
            p1 = p1.next
            p2 = p2.next

        # reverse the second half back to its original direction
        prev2 = None
        curr2 = second_head
        while curr2:
            nxt = curr2.next
            curr2.next = prev2
            prev2 = curr2
            curr2 = nxt
        first_tail.next = prev2   # re-attach in original order

        return result

    # ------------------------------------------------------------------
    # Baseline: copy to array, two-pointer check. O(n) space.
    # ------------------------------------------------------------------
    def isPalindrome_array(self, head: Optional[ListNode]) -> bool:
        vals = []
        node = head
        while node:
            vals.append(node.val)
            node = node.next
        lo, hi = 0, len(vals) - 1
        while lo < hi:
            if vals[lo] != vals[hi]:
                return False
            lo += 1
            hi -= 1
        return True


# ==============================================================================
# TESTS — run:  python 007_palindrome_linked_list_solution.py
# ==============================================================================
def list_to_linked(values: List[int]) -> Optional[ListNode]:
    dummy = ListNode()
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next


def linked_to_list(head: Optional[ListNode]) -> List[int]:
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


CASES = [
    ([1, 2, 2, 1], True),
    ([1, 2], False),
    ([1], True),
    ([1, 2, 3, 2, 1], True),
    ([1, 2, 3, 4], False),
    ([1, 1], True),
    ([1, 2, 1, 1], False),
    ([0], True),
    ([1, 2, 3, 3, 2, 1], True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: array O(n)-space vs in-place O(1)-space vs restoring version ---")
    for values, expected in CASES:
        r1 = sol.isPalindrome_array(list_to_linked(values))
        r2 = sol.isPalindrome(list_to_linked(values))
        r3 = sol.isPalindrome_restore(list_to_linked(values))
        ok = r1 == expected and r2 == expected and r3 == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  head={values!r:<20} -> array={r1} inplace={r2} "
              f"restore={r3}  (want {expected})")

    # ----------------------------------------------------------------------
    # Live demo: isPalindrome (raw) mutates the caller's list; _restore does not.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  side effect: raw isPalindrome mutates the list; _restore doesn't ---")
    values = [1, 2, 3, 2, 1]
    head_raw = list_to_linked(values)
    sol.isPalindrome(head_raw)
    after_raw = linked_to_list(head_raw)
    print(f"  original values: {values}")
    print(f"  after isPalindrome(raw):    {after_raw}   "
          f"{'<- STRUCTURE CHANGED (second half left reversed)' if after_raw != values else '(unchanged)'}")

    head_restore = list_to_linked(values)
    sol.isPalindrome_restore(head_restore)
    after_restore = linked_to_list(head_restore)
    print(f"  after isPalindrome_restore: {after_restore}   "
          f"{'<- unchanged, as expected' if after_restore == values else 'CHANGED (bug)'}")
    side_effect_shown = after_raw != values and after_restore == values
    all_ok &= side_effect_shown

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: isPalindrome([1,2,3,2,1]) (odd length) ---")
    head = list_to_linked([1, 2, 3, 2, 1])
    slow = fast = head
    while fast and fast.next:
        slow = slow.next
        fast = fast.next.next
    print(f"  middle found at node with val={slow.val}")
    prev, curr = None, slow
    while curr:
        nxt = curr.next
        curr.next = prev
        prev, curr = curr, nxt
    second_head = prev
    print(f"  reversed second half starts at val={second_head.val}: "
          f"{linked_to_list(second_head)}")
    p1, p2 = head, second_head
    i = 0
    while p1 and p2:
        print(f"  compare[{i}]: p1.val={p1.val} vs p2.val={p2.val} "
              f"{'match' if p1.val == p2.val else 'MISMATCH'}")
        p1, p2 = p1.next, p2.next
        i += 1
    print("  result: True")

    # ----------------------------------------------------------------------
    # O(n) space vs O(1) space: measured memory-relevant cost via timing at scale.
    # ----------------------------------------------------------------------
    print("\n--- array O(n)-space vs in-place O(1)-space: measured runtime at scale ---")
    print(f"  {'n':>8} {'array O(n) space':>18} {'in-place O(1) space':>20} {'ratio':>8}")
    for n in (10_000, 100_000, 500_000):
        vals = list(range(n // 2)) + list(range(n // 2 - 1, -1, -1))  # true palindrome
        head = list_to_linked(vals)
        t0 = time.perf_counter()
        sol.isPalindrome_array(head)
        t1 = time.perf_counter()
        sol.isPalindrome(head)   # note: head's second half is now reversed, fine for timing only
        t2 = time.perf_counter()
        arr_ms = (t1 - t0) * 1000
        ip_ms = (t2 - t1) * 1000
        ratio = arr_ms / ip_ms if ip_ms > 0 else float("inf")
        print(f"  {n:>8} {arr_ms:>16.2f}ms {ip_ms:>18.2f}ms {ratio:>7.2f}x")
    print("  Both are O(n) TIME, so runtime is close either way in CPython — the")
    print("  real win of the in-place approach is SPACE: no n-sized buffer is")
    print("  allocated, which matters when n is large enough to pressure memory,")
    print("  not when it's large enough to pressure the clock.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
