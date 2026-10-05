"""
================================================================================
SOLUTION · LeetCode 19 · Remove Nth Node From End of List              [Medium]
https://leetcode.com/problems/remove-nth-node-from-end-of-list/
================================================================================

THE CORE IDEA
--------------
"Nth from the end" is awkward on a singly linked list because you cannot walk
backward and you don't know the length until you've already walked the whole
thing once. The fixed-gap two-pointer trick (topic guide §3.3) converts "from
the end" into "from the front" in a single pass:

    dummy = ListNode(next=head)
    fast = slow = dummy
    for _ in range(n):          # open a gap of exactly n nodes
        fast = fast.next
    while fast.next:            # slide the gap to the end, together
        fast = fast.next
        slow = slow.next
    slow.next = slow.next.next  # slow is the node BEFORE the target
    return dummy.next

Once `fast` has taken `n` steps, the distance between `fast` and `slow` is
fixed at `n` for the rest of the walk (they move in lockstep). When `fast`
reaches the LAST node (`fast.next is None`), `slow` is exactly `n` nodes
behind the last node — i.e. sitting right before the node that is n-th from
the end. `slow.next` IS that target node, and `slow.next = slow.next.next`
unlinks it in O(1) once found.

The dummy head (topic guide Part 2) exists for exactly one reason here: when
n == length, the target IS the real head, and `slow` needs a "node before
head" to stand on so the same one-liner rewires the head-removal case
identically to every other case — no `if target is head: ...` branch needed.


================================================================================
APPROACH 1 · Two-pass (state it, price it)
================================================================================
    length = 0
    node = head
    while node:
        length += 1
        node = node.next

    dummy = ListNode(next=head)
    node = dummy
    for _ in range(length - n):     # walk to the node BEFORE the target
        node = node.next
    node.next = node.next.next
    return dummy.next

Time O(L), Space O(1) — same complexity class as the one-pass version, but
TWO full traversals of the list (or at least, one full + one partial covering
the same ground again in the worst case). Correct, and often what people
write first; the one-pass version is what the follow-up is fishing for.


================================================================================
APPROACH 2 · Fixed-gap two pointers ✅ (the answer, one pass)
================================================================================
See THE CORE IDEA above. O(L) time, ONE traversal, O(1) space.


================================================================================
APPROACH 3 · Stack (alternative one-pass-ish, more space)
================================================================================
Push every node onto a stack while walking once; pop `n` times to land on the
target node; the node now on top of the stack is its predecessor. Same O(L)
time, but O(L) auxiliary space — strictly worse than the two-pointer version,
though it generalises easily to "remove the node such that <some backward
condition>" for problems where the two-pointer trick doesn't apply as cleanly.


================================================================================
STEP BY STEP TRACE
================================================================================
head = [1,2,3,4,5], n = 2   (topic guide §3.3, worked through with real nodes)

    dummy -> [1] -> [2] -> [3] -> [4] -> [5] -> None
      ^
    fast = slow = dummy

Phase 1 — open the gap (n = 2 steps of fast):
    step 1: fast = [1]
    step 2: fast = [2]

    dummy -> [1] -> [2] -> [3] -> [4] -> [5] -> None
                      ^
                     fast
      ^
    slow (still at dummy) — gap between slow and fast is exactly 2 nodes

Phase 2 — slide the gap to the end (advance both until fast.next is None):
    fast.next = [3] is not None -> fast=[3], slow=[1]
    fast.next = [4] is not None -> fast=[4], slow=[2]
    fast.next = [5] is not None -> fast=[5], slow=[3]
    fast.next = None -> STOP

    dummy -> [1] -> [2] -> [3] -> [4] -> [5] -> None
                              ^slow                ^fast (last node)

Phase 3 — unlink:
    slow.next = slow.next.next     # [3].next = [4].next = [5]
    dummy -> [1] -> [2] -> [3] -> [5] -> None
                                          (4 is unreachable, GC'd)

return dummy.next = [1,2,3,5]   ✓ matches expected output


HEAD-REMOVAL TRACE — n == length (the case the dummy exists for)
------------------------------------------------------------------------------
head = [1,2,3], n = 3

    dummy -> [1] -> [2] -> [3] -> None
      ^
    fast = slow = dummy

Phase 1 — open gap of 3:
    fast = [1], fast = [2], fast = [3]

    dummy -> [1] -> [2] -> [3] -> None
      ^                      ^fast
    slow

Phase 2 — fast.next is already None -> loop body never runs. slow stays at dummy.

Phase 3 — unlink:
    slow.next = slow.next.next     # dummy.next = [1].next = [2]
    dummy -> [2] -> [3] -> None

return dummy.next = [2,3]   ✓ — the real head (1) was removed, with ZERO
special-case branching, because `slow` (= dummy) IS "the node before the
target" even when the target is the original head.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time    Space   Mutates input?   Passes
    ---------------------------  ------  ------  ---------------  -------
    Two-pass (count then walk)   O(L)    O(1)    yes (rewires)    2
    Fixed-gap two pointers  ✅   O(L)    O(1)    yes (rewires)    1
    Stack                        O(L)    O(L)    yes (rewires)    1 (+O(L) space)


================================================================================
EDGE CASES
================================================================================
    [1], n=1               -> []    Single node, remove the only node —
                                     dummy.next after removal is None.
    n == length             -> the target IS the head; dummy handles it with
                                     no special-case branch (traced above).
    n == 1                   -> remove the LAST node; fast ends up exactly one
                                     step ahead of "last", slow lands on the
                                     second-to-last node.
    Two-node list, n=2        -> removes the head, returns the single
                                     remaining node — smallest head-removal case.
    Constraints guarantee 1 <= n <= sz, so "n larger than length" and "empty
    list" are both out of scope per LeetCode's constraints — no need to guard
    against them, but say so if asked.


================================================================================
COMMON MISTAKES
================================================================================
1. Opening the gap `n - 1` steps instead of `n` (or vice versa) — off-by-one
   on the fixed-gap two-pointer (topic guide Part 8, mistake 4). Always
   re-derive from the dummy-head picture rather than recalling the number:
   after `n` steps, the physical gap between fast and slow is `n` nodes, and
   when fast is on the LAST node, slow must be n nodes behind it = right
   before the target.

2. Forgetting the dummy head and special-casing "n == length" separately.
   Doubles the code for no benefit — the entire point of the dummy is that it
   makes head-removal identical to every other removal.

3. Using `while fast:` instead of `while fast.next:` in phase 2 — walks one
   node too far, leaving `slow` ONE PAST the true predecessor and deleting
   the wrong node.

4. Two-pass version: computing `length - n` and off-by-one on how many steps
   to walk from the dummy (it's `length - n` steps from `dummy`, landing on
   the predecessor — not `length - n - 1` or `length - n + 1`).

5. Returning `head` instead of `dummy.next` — wrong when the head itself was
   removed, since `head` still points at the (now detached) original first
   node.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Could you do this in one pass? (asked directly in the LeetCode prompt)
A: Yes — the fixed-gap two-pointer trick above. State the two-pass version
   first as the obvious baseline, then show the gap trick removes the second
   traversal.

Q: What if n could be invalid (larger than the list length)?
A: Guard `fast` for `None` while opening the gap and return early (or raise),
   since LeetCode guarantees validity but real-world callers might not.

Q: What if you needed to remove the Nth node from the FRONT instead?
A: Trivial — just walk n-1 steps from a dummy head directly, no gap trick
   needed; "from the front" doesn't have the "don't know where the end is
   yet" problem this trick solves.

Q: Can you do it recursively?
A: Yes — recurse to the end of the list, and on the way back up count depth;
   when depth == n, you're at the target and can unlink via the return value.
   Costs O(L) stack frames instead of O(1) space, same CPython recursion-limit
   caveat as topic guide Part 4.1's reversal — usually not the answer to lead
   with.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 876  Middle of the Linked List        — slow/fast SAME start (§3.1),
                                                 not a fixed gap
    LC 141  Linked List Cycle                — slow/fast, identity compare
                                                 (§3.2)
    LC 2    Add Two Numbers                  — dummy head, different problem
                                                 shape (problem 011 here)
    LC 24   Swap Nodes in Pairs               — dummy head + local rewiring,
                                                 same "operate one node ahead"
                                                 shape
================================================================================
"""

from typing import Optional


class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next


class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        """Fixed-gap two pointers with a dummy head. O(L) time, O(1) space,
        ONE pass. See THE CORE IDEA above."""
        dummy = ListNode(next=head)
        fast = slow = dummy
        for _ in range(n):
            fast = fast.next
        while fast.next:
            fast = fast.next
            slow = slow.next
        slow.next = slow.next.next
        return dummy.next

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def removeNthFromEnd_two_pass(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        """Two-pass oracle: count length, then walk to the predecessor.
        O(L) time (two traversals), O(1) space. Used to cross-check the
        one-pass answer."""
        length = 0
        node = head
        while node:
            length += 1
            node = node.next

        dummy = ListNode(next=head)
        node = dummy
        for _ in range(length - n):
            node = node.next
        node.next = node.next.next
        return dummy.next

    def removeNthFromEnd_stack(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        """Stack-based alternative: O(L) time, O(L) space. Generalises to
        problems where the two-pointer trick doesn't apply as cleanly."""
        dummy = ListNode(next=head)
        stack = []
        node = dummy
        while node:
            stack.append(node)
            node = node.next
        for _ in range(n):
            stack.pop()
        predecessor = stack[-1]
        predecessor.next = predecessor.next.next
        return dummy.next

    # ------------------------------------------------------------------
    # Deliberate breakage — off-by-one on the gap size.
    # ------------------------------------------------------------------
    def removeNthFromEnd_off_by_one(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        """✗ BROKEN ON PURPOSE — opens the gap with `n - 1` steps instead of
        `n`. Deletes the WRONG node (one too early) whenever it doesn't
        crash outright. See common mistake #1."""
        dummy = ListNode(next=head)
        fast = slow = dummy
        for _ in range(n - 1):        # WRONG: should be n
            fast = fast.next
        while fast.next:
            fast = fast.next
            slow = slow.next
        slow.next = slow.next.next
        return dummy.next


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build(values):
    dummy = ListNode()
    curr = dummy
    for v in values:
        curr.next = ListNode(v)
        curr = curr.next
    return dummy.next


def to_list(head):
    out = []
    while head:
        out.append(head.val)
        head = head.next
    return out


CASES = [
    ([1, 2, 3, 4, 5], 2, [1, 2, 3, 5]),
    ([1], 1, []),
    ([1, 2], 1, [1]),
    ([1, 2], 2, [2]),
    ([1, 2, 3, 4, 5], 5, [2, 3, 4, 5]),
    ([1, 2, 3], 3, [2, 3]),
    ([1, 2, 3], 1, [1, 2]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: one-pass gap-trick vs two-pass oracle vs stack ---")
    for values, n, expected in CASES:
        h1 = build(values)
        got1 = to_list(sol.removeNthFromEnd(h1, n))
        h2 = build(values)
        got2 = to_list(sol.removeNthFromEnd_two_pass(h2, n))
        h3 = build(values)
        got3 = to_list(sol.removeNthFromEnd_stack(h3, n))
        ok = got1 == expected and got2 == expected and got3 == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  values={values!r:<20} n={n} -> "
              f"one-pass={got1} two-pass={got2} stack={got3}  (want {expected})")

    # ----------------------------------------------------------------------
    # Trace: head removal (n == length), traced live.
    # ----------------------------------------------------------------------
    print("\n--- trace: head = [1,2,3], n=3 (removing the HEAD via the dummy) ---")
    head = build([1, 2, 3])
    dummy = ListNode(next=head)
    fast = slow = dummy
    print(f"  dummy -> {to_list(dummy.next)}")
    for i in range(3):
        fast = fast.next
        print(f"  gap-open step {i + 1}: fast now at val={fast.val}")
    print(f"  fast.next is None: {fast.next is None} -> phase-2 loop body never runs")
    slow.next = slow.next.next
    print(f"  after unlink: dummy.next -> {to_list(dummy.next)}")
    result_ok = to_list(dummy.next) == [2, 3]
    all_ok &= result_ok
    print(f"  matches expected [2,3]: {result_ok}")

    # ----------------------------------------------------------------------
    # ⚠️ Off-by-one demo: n-1 gap steps deletes the wrong node.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ off-by-one on gap size: n vs n-1 steps (common mistake #1) ---")
    print(f"  {'values':<20} {'n':>3} {'correct':>10} {'off-by-one':>12}  ok?")
    off_by_one_mismatch = False
    for values, n, expected in [([1, 2, 3, 4, 5], 2, [1, 2, 3, 5]), ([1, 2, 3], 1, [1, 2])]:
        good = to_list(sol.removeNthFromEnd(build(values), n))
        try:
            bad = to_list(sol.removeNthFromEnd_off_by_one(build(values), n))
        except AttributeError:
            bad = "CRASH (NoneType.next)"
        mismatch = good != bad
        off_by_one_mismatch |= mismatch
        print(f"  {str(values):<20} {n:>3} {str(good):>10} {str(bad):>12}  "
              f"{'yes' if not mismatch else 'NO  <- wrong node removed'}")
    print(f"  off-by-one bug reproduced: {off_by_one_mismatch}")
    all_ok &= off_by_one_mismatch

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
