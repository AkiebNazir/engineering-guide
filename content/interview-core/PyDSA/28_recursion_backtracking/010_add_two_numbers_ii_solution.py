"""
================================================================================
SOLUTION · LeetCode 445 · Add Two Numbers II                            [Medium]
https://leetcode.com/problems/add-two-numbers-ii/
================================================================================

THE CORE IDEA
--------------
Pad both lists to equal length with leading zeros, then recurse all the
way to the END (the ones place) before doing any addition — the carry has
to flow from the ones place back toward the most-significant digit, which
in a most-significant-digit-first list means it flows UP the return
values of the recursion. Each call returns a PAIR: `(carry, node)` — the
first "return two pieces of information" recursion in this folder, as
called out in the topic guide.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, PAD-TO-EQUAL-LENGTH — the (carry, node) pair-returning
   recursion above. O(max(m,n)) time, O(max(m,n)) space (call stack).
   The version taught here.
2. TWO STACKS — push every digit of both lists onto two stacks (this
   naturally reverses them to least-significant-first), then pop and add
   with a running carry, building the result list by PREPENDING each new
   node to the front. O(m+n) time, O(m+n) space. What most interviewers
   actually want, and the direct answer to the stated "don't modify /
   don't reverse the input" follow-up (reversal never touches the
   original list objects).
3. CONVERT TO INT, ADD, CONVERT BACK — walk each list to build an integer
   directly (`n = n*10 + digit`), add the two integers, convert the sum
   back to a list of digits. O(m+n) time, O(m+n) space; simplest code,
   but relies on Python's arbitrary-precision ints — priced as a
   language-specific shortcut, not the general technique.


================================================================================
STEP BY STEP TRACE — addTwoNumbers([7,2,4,3], [5,6,4])
================================================================================
Padding: [5,6,4] is shorter -> pad to [0,5,6,4] so both have length 4.

    call addSameLength([7,2,4,3], [0,5,6,4])
      call addSameLength([2,4,3], [5,6,4])
        call addSameLength([4,3], [6,4])
          call addSameLength([3], [4])
            call addSameLength([], [])   base case -> return (0, None)
            total = 3+4+0 = 7 -> node(7, None), return (0, node(7))
          total = 4+6+0 = 10 -> node(0, ->7), return (1, node(0, ->7))
        total = 2+5+1 = 8 -> node(8, ->0->7), return (0, node(8, ->0->7))
      total = 7+0+0 = 7 -> node(7, ->8->0->7), return (0, node(7, ->8->0->7))
    top-level carry = 0, so no extra digit prepended.

Result: 7 -> 8 -> 0 -> 7  i.e. [7, 8, 0, 7] = 7243 + 564 = 7807. Correct.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time        Space          Mutates input?  Note
    ------------------------------  ----------  -------------  ---------------  --------------------------------
    Recursive, pad-to-equal-length O(max(m,n)) O(max(m,n))    no (padding      returns (carry, node) pairs
                                                                only)
    Two stacks                     O(m+n)      O(m+n)         no               answers the "no reversal" follow-up
    Convert to int and back        O(m+n)      O(m+n)         no               relies on bignum ints (Python-specific)


================================================================================
EDGE CASES
================================================================================
    [0] + [0]        -> [0]    both single-digit zero; must not produce a
                                spurious extra leading zero node.
    [9,9] + [1]       -> [1,0,0]  carry propagates all the way through
                                every digit AND produces one final
                                leftover carry that must be PREPENDED
                                after the recursion fully returns (99+1
                                =100, one extra digit).
    lists of different lengths -> padding the shorter one with leading
                                zero nodes is what makes the equal-length
                                recursion correct; skipping this step
                                misaligns which digits get added together.
    a carry that propagates through EVERY digit (e.g. 999+1) -> exercises
                                the pair-return mechanism at every single
                                level of recursion, not just the last one.


================================================================================
COMMON MISTAKES
================================================================================
1. Calling the equal-length recursion on the ORIGINAL lists without
   padding first — misaligns digit positions whenever the two numbers
   have different lengths, silently adding the wrong digits together
   (e.g. treating [7,2,4,3]'s leading 7 as if it lined up with [5,6,4]'s
   leading 5, when it should line up with an implicit leading 0).
2. Returning only the built node from each call and tracking carry via a
   shared mutable variable (e.g. an instance attribute) instead of
   returning it explicitly as part of a pair — works, but reintroduces
   exactly the kind of implicit shared state the topic guide warns
   against; the pair-return keeps each call's contract explicit and
   self-contained.
3. Forgetting the FINAL leftover carry check after the top-level call
   returns — if the two most-significant digits sum with a carry to 10+
   (e.g. 5+7=12), one more digit must be prepended to the result that the
   equal-length recursion itself has no way to produce (there's no
   "digit before the first one" for it to attach to).
4. Building the result list by APPENDING at each level instead of
   letting `restNode` be the tail and constructing the new node with it
   as `.next` — since digits must come out most-significant-first and
   the recursion resolves least-significant-first (deepest call first),
   the node for the CURRENT (more significant) digit must be built with
   the deeper result as its `.next`, not the other way around.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: The problem forbids reversing the input lists — does your recursive
   solution violate that?
A: No — it never mutates l1 or l2, and never reverses them; it only reads
   `.val`/`.next` and builds an entirely new result list. Padding creates
   NEW zero nodes prepended to (logical, not literal) equal-length views,
   or can be done via a length-difference offset without touching the
   originals at all.

Q: Can you do this without recursion, still without reversing the input?
A: Yes — push every digit onto two stacks (this doesn't reverse the
   INPUT lists, just captures their digits in reverse order), then pop
   and add with a carry, prepending each result digit to build the
   answer most-significant-first automatically.

Q: How does this connect to LC 2 (Add Two Numbers, least-significant-
   first)?
A: LC 2 needs NO padding-and-recurse-to-the-end trick — you can add
   straight from the heads with a running carry going FORWARD, since the
   ones place is already at the front. This problem's added twist (digit
   order reversed) is exactly why it needs recursion (or a stack) to
   reach the ones place before adding.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 2    Add Two Numbers            — the least-significant-first
                                        version; no padding/recursion
                                        needed, straight iteration works.
    Topic 28, 007/008 (linked list)    — more pointer-rewiring recursion
                                        on linked lists, without a second
                                        "carry" piece of state to track.
    Topic 28, 019 LCA of Deepest Leaves — another "return a pair, not
                                        just one value" recursion later
                                        in this folder.
================================================================================
"""

from typing import Optional, Tuple


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def addTwoNumbers(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        """Recursive, pad to equal length, (carry, node) pair returned. O(max(m,n))."""
        len1, len2 = self._length(l1), self._length(l2)
        if len1 < len2:
            l1 = self._pad(l1, len2 - len1)
        elif len2 < len1:
            l2 = self._pad(l2, len1 - len2)

        carry, head = self._add_same_length(l1, l2)
        if carry:
            head = ListNode(carry, head)
        return head

    def _length(self, node: Optional[ListNode]) -> int:
        n = 0
        while node:
            n += 1
            node = node.next
        return n

    def _pad(self, node: Optional[ListNode], zeros: int) -> Optional[ListNode]:
        for _ in range(zeros):
            node = ListNode(0, node)
        return node

    def _add_same_length(self, l1, l2) -> Tuple[int, Optional[ListNode]]:
        if l1 is None:
            return 0, None
        carry, rest = self._add_same_length(l1.next, l2.next)
        total = l1.val + l2.val + carry
        node = ListNode(total % 10, rest)
        return total // 10, node

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def addTwoNumbers_two_stacks(self, l1: Optional[ListNode], l2: Optional[ListNode]) -> Optional[ListNode]:
        """Two stacks, no recursion, doesn't touch original lists. O(m+n)."""
        s1, s2 = [], []
        while l1:
            s1.append(l1.val)
            l1 = l1.next
        while l2:
            s2.append(l2.val)
            l2 = l2.next

        head = None
        carry = 0
        while s1 or s2 or carry:
            total = carry
            if s1:
                total += s1.pop()
            if s2:
                total += s2.pop()
            carry, digit = divmod(total, 10)
            head = ListNode(digit, head)
        return head


# ==============================================================================
# TESTS — run:  python 010_add_two_numbers_ii_solution.py
# ==============================================================================
def build(values):
    head = None
    for v in reversed(values):
        head = ListNode(v, head)
    return head


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


CASES = [
    ([7, 2, 4, 3], [5, 6, 4], [7, 8, 0, 7]),
    ([2, 4, 3], [5, 6, 4], [8, 0, 7]),
    ([0], [0], [0]),
    ([9, 9], [1], [1, 0, 0]),
    ([1], [9, 9], [1, 0, 0]),
    ([9, 9, 9], [1], [1, 0, 0, 0]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    impls = [
        ("recursive, pad-to-equal", sol.addTwoNumbers),
        ("two stacks             ", sol.addTwoNumbers_two_stacks),
    ]

    for name, fn in impls:
        ok = True
        for a, b, expected in CASES:
            l1, l2 = build(a), build(b)
            got = to_list(fn(l1, l2))
            ok &= got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- confirming the two-stacks version never mutates the input lists ---")
    l1, l2 = build([9, 9]), build([1])
    before1, before2 = to_list(l1), to_list(l2)
    sol.addTwoNumbers_two_stacks(l1, l2)
    after1, after2 = to_list(l1), to_list(l2)
    unmutated = before1 == after1 and before2 == after2
    all_ok &= unmutated
    print(f"  {'PASS' if unmutated else 'FAIL'}  l1 stayed {after1}, l2 stayed {after2}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
