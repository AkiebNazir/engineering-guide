"""
================================================================================
SOLUTION · LeetCode 641 · Design Circular Deque                       [Medium]
https://leetcode.com/problems/design-circular-deque/
================================================================================

THE CORE IDEA
--------------
Problem 004's ring buffer (fixed array + `head` + explicit `size`),
generalised so `head` can move backward as well as forward. `insertFront`
decrements head first (wrapping via Python's sign-correct `%`), then
writes; `insertLast` and `deleteFront` are unchanged from 004; `deleteLast`
needs no index movement at all — just shrink `size` by one.

    class MyCircularDeque:
        def __init__(self, k):
            self.buf = [0] * k
            self.cap = k
            self.head = 0
            self.size = 0

        def insertFront(self, value):
            if self.size == self.cap: return False
            self.head = (self.head - 1) % self.cap
            self.buf[self.head] = value
            self.size += 1
            return True

        def insertLast(self, value):
            if self.size == self.cap: return False
            tail = (self.head + self.size) % self.cap
            self.buf[tail] = value
            self.size += 1
            return True

        def deleteFront(self):
            if self.size == 0: return False
            self.head = (self.head + 1) % self.cap
            self.size -= 1
            return True

        def deleteLast(self):
            if self.size == 0: return False
            self.size -= 1                  # tail slot just falls out of range
            return True


================================================================================
WHY `(head - 1) % cap` "JUST WORKS" IN PYTHON — and wouldn't in C/Java/Go
================================================================================
Topic 04 §1.5 established this fact for a different problem (mod-K prefix
sums); it applies verbatim here. Python's `%` always returns a result with
the SAME SIGN AS THE DIVISOR. Since `cap > 0`, `(-1) % cap` is `cap - 1` in
Python — exactly the wraparound you want, with zero extra code:

    >>> (-1) % 4
    3
    >>> (0 - 1) % 4
    3

In C, Java, or Go, `-1 % 4` evaluates to `-1` (truncated toward zero, sign
follows the DIVIDEND), which is not a valid array index — you'd need
`((head - 1) % cap + cap) % cap` or an explicit `if head == 0: head = cap - 1`
guard. Say this out loud if you have that background: it's a genuine
language difference, not folklore, and it's one less bug surface in Python.


================================================================================
WHY deleteLast NEEDS NO INDEX MOVEMENT
================================================================================
The valid region of the buffer is always exactly the `size` slots starting
at `head`: `[head, head+1, ..., head+size-1]`, all mod cap. The rear is by
definition the LAST of those, at `(head + size - 1) % cap`. Decrementing
`size` by one shrinks that valid region by exactly one slot FROM THE END —
the old rear index is simply no longer included in `[head, head+size)`, so
it's "deleted" in every sense that matters (never read, and will be
overwritten by the next insertLast at that same freed position). No index
needs to physically move for this to be correct — this is the same
"abandon, don't erase" idea from 004's deQueue, just applied to the other
end.


================================================================================
STEP BY STEP TRACE
================================================================================
capacity = 3.  buf = [_, _, _]

    op                 head  size  action                          buf              result
    insertLast(1)       0     0    tail=(0+0)%3=0                   [1, _, _]  sz=1   True
    insertLast(2)        0     1    tail=(0+1)%3=1                   [1, 2, _]  sz=2   True
    insertFront(3)        0     2    head=(0-1)%3=2, write buf[2]     [1, 2, 3]  sz=3   True
                                                                       (head is now 2!)
    insertFront(4) full   2     3    size==cap -> reject                                False
    getRear()             2     3    (head+size-1)%3=(2+3-1)%3=1 -> buf[1]=2             2
    deleteLast()           2     3    size -=1 -> 2                   [1,2,3] sz=2       True
    insertFront(4)          2     2    head=(2-1)%3=1, write buf[1]    [1, 4, 3] sz=3     True
                                                                        (buf[1]'s old '2'
                                                                         overwritten)
    getFront()               1     3    buf[head]=buf[1]                                  4

Logical deque contents throughout, front-to-back: [3,1,2] -> [3,1] (after
deleteLast) -> [4,3,1] (after insertFront(4)) — matches the worked example
in the problem statement exactly.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                                  All 4 ops   Space   Mutates input?
    -----------------------------------------  ----------  ------  ---------------
    Python list, insert(0,...)/pop(0) both ends  O(n)         O(n)    n/a (self-contained)
    collections.deque (real one, unbounded)       O(1)         O(n)    n/a  — but no
                                                                             capacity limit
                                                                             enforced natively
    Fixed circular array (answer) ✅               O(1)         O(k)    n/a  — worst-case O(1),
                                                                             true capacity limit


================================================================================
EDGE CASES
================================================================================
    capacity = 1                          -> getFront() == getRear() always;
                                            insertFront and insertLast are
                                            interchangeable when there's
                                            only one slot.
    Insert only from one end repeatedly    -> degenerates to problem 004's
                                            circular queue exactly; head only
                                            ever advances forward.
    Insert only from the front repeatedly   -> head only ever moves
                                            backward; exercises the negative-
                                            modulo wraparound heavily.
    Alternating insertFront/insertLast       -> head moves both directions
                                            across the run; exercises BOTH
                                            wraparound directions in the
                                            same buffer lifetime.
    Full, then deleteFront, insertLast        -> classic "advance head, fill
                                            behind it" wrap, mirrors 004's
                                            trace exactly.
    Full, then deleteLast, insertFront         -> the NEW direction this
                                            problem adds over 004 — the
                                            trace above exercises exactly
                                            this.
    getFront/getRear on empty                   -> both -1, never raise.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting that inserting at the front must move `head` BACKWARD, not
   just write to `head` and then decide where the "old" head goes —
   `head = (head - 1) % cap` must happen BEFORE the write, not after.

2. In a non-Python translation of this solution, forgetting to normalise a
   negative index from `(head - 1) % cap` — Python doesn't need this, but
   the habit of assuming other languages don't either is a real portability
   bug (see the sign-correct `%` section above).

3. Trying to make deleteLast() move an index (e.g. decrementing a nonexistent
   `tail` variable) instead of just decrementing `size` — unnecessary and
   easy to get backward under time pressure; the simpler formulation
   (shrink size, don't move head) is both correct and less error-prone.

4. Recomputing getRear()'s formula as `(head + size) % cap` (off by one) —
   that's the NEXT free insert slot, not the current rear; the actual rear
   is `(head + size - 1) % cap`.

5. Not guarding insertFront/insertLast/deleteFront/deleteLast/getFront/
   getRear against the empty or full boundary — e.g. calling getFront() on
   an empty deque and returning `buf[head]` (stale garbage) instead of -1.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How is this different from just using `collections.deque` directly?
A: `collections.deque` gives you O(1) at both ends but no ENFORCED fixed
   capacity with a checkable isFull()/false-returning-insert contract
   (`maxlen` silently evicts from the opposite end instead of rejecting) —
   and this exercise, like 004, is about building the ring-buffer mechanism
   yourself, which is exactly what a real `deque` implementation does
   internally (as a doubly-linked list of fixed-size blocks, not a single
   flat array, but same amortized-O(1)-both-ends spirit).

Q: What if capacity needs to grow or shrink at runtime?
A: Same answer as 004's resize follow-up: allocate a new array, copy the
   `size` logically-ordered elements starting from `head` into the new
   array from index 0, reset head to 0.

Q: Could you implement this as a doubly linked list instead of an array?
A: Yes — a doubly linked list with head/tail pointers gives O(1) insert/
   delete at both ends without a hard capacity (unless you add a manual
   counter and check), and avoids fixed pre-allocation. The array version
   here trades that flexibility for better cache locality and no per-node
   pointer overhead — the classic array-vs-linked-list trade discussed in
   topic 08.

Q: What's the relationship between this and problem 006's monotonic deque?
A: Purely mechanical — 006 uses a real `collections.deque` (unbounded,
   Python-native) as its underlying container because the interesting part
   there is the PRUNING RULE for what to keep, not fixed-capacity storage
   mechanics. This problem is entirely about the storage mechanics with a
   real capacity limit; 006 doesn't need or want a limit.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 622  Design Circular Queue         — problem 004 here, this
                                            problem's single-ended special
                                            case
    LC 232  Implement Queue using Stacks  — problem 001 here, a queue with
                                            no fixed capacity, different
                                            trade-offs entirely
    LC 239  Sliding Window Maximum        — topic 03 problem 014, real-world
                                            payoff of a genuinely unbounded
                                            deque used as a monotonic
                                            structure
================================================================================
"""

import time
import random
from collections import deque
from typing import List


class MyCircularDeque:
    """Fixed-size array + head + explicit size, extended to both ends.
    O(1) worst-case for every operation. See THE CORE IDEA above."""

    def __init__(self, k: int):
        self.buf: List[int] = [0] * k
        self.cap = k
        self.head = 0
        self.size = 0

    def insertFront(self, value: int) -> bool:
        if self.size == self.cap:
            return False
        self.head = (self.head - 1) % self.cap
        self.buf[self.head] = value
        self.size += 1
        return True

    def insertLast(self, value: int) -> bool:
        if self.size == self.cap:
            return False
        tail = (self.head + self.size) % self.cap
        self.buf[tail] = value
        self.size += 1
        return True

    def deleteFront(self) -> bool:
        if self.size == 0:
            return False
        self.head = (self.head + 1) % self.cap
        self.size -= 1
        return True

    def deleteLast(self) -> bool:
        if self.size == 0:
            return False
        self.size -= 1
        return True

    def getFront(self) -> int:
        if self.size == 0:
            return -1
        return self.buf[self.head]

    def getRear(self) -> int:
        if self.size == 0:
            return -1
        return self.buf[(self.head + self.size - 1) % self.cap]

    def isEmpty(self) -> bool:
        return self.size == 0

    def isFull(self) -> bool:
        return self.size == self.cap

    def _contents(self) -> List[int]:
        """Debug helper: logical contents front-to-back. Not part of the
        LeetCode interface; used only by the trace printer below."""
        return [self.buf[(self.head + i) % self.cap] for i in range(self.size)]


class ListDequeBothEnds:
    """Baseline for the benchmark: plain Python list, insert(0, x)/pop(0)
    for the front, append/pop for the rear. Correct, but O(n) at the front
    for both insert and delete."""

    def __init__(self, k: int):
        self.buf: List[int] = []
        self.cap = k

    def insertFront(self, value: int) -> bool:
        if len(self.buf) == self.cap:
            return False
        self.buf.insert(0, value)          # O(n)
        return True

    def insertLast(self, value: int) -> bool:
        if len(self.buf) == self.cap:
            return False
        self.buf.append(value)
        return True

    def deleteFront(self) -> bool:
        if not self.buf:
            return False
        self.buf.pop(0)                     # O(n)
        return True

    def deleteLast(self) -> bool:
        if not self.buf:
            return False
        self.buf.pop()
        return True

    def getFront(self) -> int:
        return self.buf[0] if self.buf else -1

    def getRear(self) -> int:
        return self.buf[-1] if self.buf else -1

    def isEmpty(self) -> bool:
        return not self.buf

    def isFull(self) -> bool:
        return len(self.buf) == self.cap


# ==============================================================================
# TESTS — run:  python 005_design_circular_deque_solution.py
# ==============================================================================
def run_tests() -> None:
    passed = 0
    total = 0

    def check(name, got, want):
        nonlocal passed, total
        total += 1
        ok = got == want
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {name:<48} got={got!r}  want={want!r}")

    print("--- correctness (problem statement example) ---")
    dq = MyCircularDeque(3)
    check("insertLast(1)", dq.insertLast(1), True)
    check("insertLast(2)", dq.insertLast(2), True)
    check("insertFront(3)", dq.insertFront(3), True)
    check("insertFront(4) when full", dq.insertFront(4), False)
    check("getRear()", dq.getRear(), 2)
    check("isFull()", dq.isFull(), True)
    check("deleteLast()", dq.deleteLast(), True)
    check("insertFront(4) after deleteLast", dq.insertFront(4), True)
    check("getFront()", dq.getFront(), 4)

    dq2 = MyCircularDeque(1)
    check("empty getFront", dq2.getFront(), -1)
    check("empty getRear", dq2.getRear(), -1)
    check("empty deleteFront", dq2.deleteFront(), False)
    check("cap1 insertFront", dq2.insertFront(7), True)
    check("cap1 isFull", dq2.isFull(), True)
    check("cap1 front==rear", dq2.getFront() == dq2.getRear(), True)

    # ----------------------------------------------------------------------
    # Full trace, printed (matches STEP BY STEP TRACE above).
    # ----------------------------------------------------------------------
    print("\n--- full trace ---")
    dq = MyCircularDeque(3)
    steps = [("insertLast", 1), ("insertLast", 2), ("insertFront", 3),
              ("insertFront", 4), ("getRear", None), ("deleteLast", None),
              ("insertFront", 4), ("getFront", None)]
    for op, val in steps:
        fn = getattr(dq, op)
        r = fn(val) if val is not None else fn()
        print(f"  {op}({'' if val is None else val}) -> head={dq.head} "
              f"size={dq.size} contents={dq._contents()}  returned {r}")

    # ----------------------------------------------------------------------
    # Randomised cross-check vs a deque-backed capacity oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs deque-backed capacity oracle ---")
    random.seed(9)
    mismatches = 0
    trials = 400
    for _ in range(trials):
        cap = random.randint(1, 8)
        d = MyCircularDeque(cap)
        oracle: deque = deque()
        for _ in range(random.randint(5, 60)):
            op = random.choice(["if", "il", "df", "dl", "gf", "gr"])
            if op == "if":
                val = random.randint(0, 999)
                want_ok = len(oracle) < cap
                got = d.insertFront(val)
                if got != want_ok:
                    mismatches += 1
                elif got:
                    oracle.appendleft(val)
            elif op == "il":
                val = random.randint(0, 999)
                want_ok = len(oracle) < cap
                got = d.insertLast(val)
                if got != want_ok:
                    mismatches += 1
                elif got:
                    oracle.append(val)
            elif op == "df":
                want_ok = len(oracle) > 0
                got = d.deleteFront()
                if got != want_ok:
                    mismatches += 1
                elif got:
                    oracle.popleft()
            elif op == "dl":
                want_ok = len(oracle) > 0
                got = d.deleteLast()
                if got != want_ok:
                    mismatches += 1
                elif got:
                    oracle.pop()
            elif op == "gf":
                want = oracle[0] if oracle else -1
                if d.getFront() != want:
                    mismatches += 1
            else:
                want = oracle[-1] if oracle else -1
                if d.getRear() != want:
                    mismatches += 1
    print(f"  {trials} randomised sequences: {mismatches} mismatches")
    all_ok = passed == total and mismatches == 0

    # ----------------------------------------------------------------------
    # Runtime demo: circular array vs list-both-ends, growing n.
    # ----------------------------------------------------------------------
    print("\n--- circular array vs list insert(0,.)/pop(0) at the front: measured ---")
    print(f"  {'capacity n':>10} {'circular ms':>12} {'list ms':>10} {'ratio':>8}")
    for n in (1_000, 3_000, 7_000):
        cd = MyCircularDeque(n)
        t0 = time.perf_counter()
        for i in range(n):
            cd.insertFront(i)
        for _ in range(n):
            cd.deleteFront()
        t1 = time.perf_counter()

        ld = ListDequeBothEnds(n)
        t2 = time.perf_counter()
        for i in range(n):
            ld.insertFront(i)
        for _ in range(n):
            ld.deleteFront()
        t3 = time.perf_counter()

        c_ms = (t1 - t0) * 1000
        l_ms = (t3 - t2) * 1000
        ratio = l_ms / c_ms if c_ms > 0 else float("inf")
        print(f"  {n:>10} {c_ms:>11.2f}  {l_ms:>9.2f}  {ratio:>7.1f}x")
    print("  insertFront/deleteFront on a plain list means insert(0,.)/pop(0)")
    print("  — both O(current length) — vs the circular array's O(1) always.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
