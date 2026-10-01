"""
================================================================================
SOLUTION · LeetCode 622 · Design Circular Queue                       [Medium]
https://leetcode.com/problems/design-circular-queue/
================================================================================

THE CORE IDEA
--------------
A fixed-size array plus a `head` index and an explicit `size` counter.
`head` marks the current front; the position to insert the next element is
derived, never tracked separately, as `(head + size) % capacity`. Neither
enQueue nor deQueue ever shifts array contents — they only move indices,
wrapping with modulo when they run off the end (topic guide §3.1).

    class MyCircularQueue:
        def __init__(self, k):
            self.buf = [0] * k
            self.cap = k
            self.head = 0
            self.size = 0

        def enQueue(self, value):
            if self.size == self.cap:
                return False
            tail = (self.head + self.size) % self.cap
            self.buf[tail] = value
            self.size += 1
            return True

        def deQueue(self):
            if self.size == 0:
                return False
            self.head = (self.head + 1) % self.cap
            self.size -= 1
            return True


================================================================================
WHY AN EXPLICIT `size` INSTEAD OF COMPARING head/tail
================================================================================
A common circular-buffer design uses only `head` and `tail` indices,
without a size counter, and calls the buffer empty when `head == tail`.
That works right up until the buffer becomes completely FULL — at which
point `head == tail` AGAIN (the tail has wrapped all the way around to meet
the head). Both empty and full look identical under that scheme, and
distinguishing them requires either wasting one array slot (never fully
filling the array) or tracking a `full` flag anyway. Tracking `size`
explicitly sidesteps the ambiguity entirely — `size == 0` unambiguously
means empty, `size == cap` unambiguously means full, and `head`/`tail`
never need to be compared to each other at all.


================================================================================
STEP BY STEP TRACE
================================================================================
capacity = 3.  buf = [_, _, _]  (underscores are stale/unused slots)

    op            head  size  tail=(head+size)%3   buf after           result
    enQueue(1)    0     0     0                     [1, _, _]  size=1   True
    enQueue(2)    0     1     1                     [1, 2, _]  size=2   True
    enQueue(3)    0     2     2                     [1, 2, 3]  size=3   True
    enQueue(4)    0     3     -                      (size==cap, full)  False
    deQueue()     0->1  3->2  -                      [1, 2, 3]  head=1  True
                                                       (slot 0 abandoned, not erased)
    enQueue(4)    1     2     (1+2)%3=0               [4, 2, 3]  size=3  True
                                                       (WROTE OVER slot 0 — the wrap)
    Rear()        (1+3-1)%3 = 0  -> buf[0] = 4                          4

The wraparound is the whole exercise: after the first deQueue, slot 0 holds
a stale '1' that is never read again — enqueue(4) safely overwrites it,
because the ring has genuinely cycled back around to a free slot.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                                enQueue   deQueue   Space   Mutates input?
    ---------------------------------------  --------  --------  ------  ---------------
    Python list, append + pop(0)               O(1)*     O(n)      O(n)    n/a (self-contained)
    Python list, append + insert(0) reversed    O(n)      O(1)*     O(n)    n/a
    Fixed circular array (answer) ✅            O(1)      O(1)      O(k)    n/a — WORST-CASE
                                                                                 O(1), not
                                                                                 amortized

    * "O(1)*" marks the cheap end of an unbalanced list-based queue; the
      OTHER end is always O(n) for a plain list, no matter which end you
      pick to be the "cheap" one, because a list is a flat array — see the
      measured benchmark below.


================================================================================
EDGE CASES
================================================================================
    capacity = 1                        -> enQueue then isFull immediately;
                                            deQueue then isEmpty immediately;
                                            exercises head/tail coinciding
                                            at cap=1 specifically.
    enQueue until full, then enQueue     -> must return False and leave the
                                            queue UNCHANGED (no partial
                                            write, no corrupted state).
    deQueue on empty                     -> must return False, not raise.
    Front()/Rear() on empty               -> must return -1, not raise or
                                            read stale/garbage data.
    Repeated enqueue/dequeue past         -> exercises the modulo wraparound
    capacity many times                    ("index runs past array end and
                                            comes back to 0") many times over
                                            — the demo below runs thousands
                                            of cycles specifically for this.
    Full queue, dequeue one, enqueue one   -> the classic "wrap by exactly
                                            one slot" case shown in the trace.


================================================================================
COMMON MISTAKES
================================================================================
1. Using plain `+1` instead of `(x + 1) % cap` for head/tail advancement —
   runs the index off the end of the backing array (IndexError) or silently
   reads/writes the wrong slot once past capacity.

2. Distinguishing empty vs full using only `head == tail` without an
   explicit size (or a "wasted slot" convention) — both states look
   identical and the queue reports itself full when actually empty, or vice
   versa.

3. Physically shifting elements on deQueue (e.g. `buf = buf[1:] + [0]`) —
   defeats the entire point of the exercise and silently reintroduces the
   O(n) cost the circular buffer exists to avoid.

4. Computing Rear()'s index as just `head + size` without the `% cap` wrap
   — indexes past the array's end whenever the queue currently straddles
   the wraparound point.

5. Forgetting to reject enQueue when full (writing into `buf[tail]` anyway)
   — silently overwrites a still-valid, not-yet-dequeued element and
   corrupts FIFO order without raising any error.

6. Not resetting/ignoring stale data left in an abandoned slot after
   deQueue — harmless if you always guard reads with `size`, but a bug if
   any code path reads `buf[some_index]` directly without checking it's
   within the currently valid `size` elements.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why not just use `collections.deque`? It already gives O(1) both ends.
A: `deque` is the right real-world answer (topic guide §4) but doesn't
   enforce a FIXED capacity with a checkable isFull()/enQueue-returns-False
   contract the way this problem asks for (deque(maxlen=k) auto-EVICTS
   instead of rejecting, a different semantic) — and the exercise explicitly
   forbids built-in queue collections to force you to build the mechanism.

Q: How would you resize the circular queue if it needed to grow?
A: Allocate a new, larger array; copy the `size` currently-valid elements
   out starting from `head`, in order (not by copying the raw array
   layout, which may itself be wrapped) into the new array from index 0;
   reset `head = 0`. This is the same idea as Python list's own amortized
   growth, done manually.

Q: What if two threads enqueue/dequeue concurrently?
A: This implementation isn't thread-safe — `head`/`size` updates aren't
   atomic. You'd need a lock around each operation, or a lock-free ring
   buffer design (single-producer/single-consumer ring buffers can often
   avoid locks entirely using atomic index updates, a classic systems
   topic beyond this problem's scope).

Q: Circular DEQUE instead of circular queue?
A: Problem 005 in this folder — same ring buffer, but `head` can also move
   backward (`(head - 1) % cap`, and Python's `%` is already sign-correct
   for a positive modulus, see topic 04 §1.5) to support inserting at the
   front.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 641  Design Circular Deque       — problem 005 here, the two-ended
                                          generalisation of this exact ring
                                          buffer
    LC 232  Implement Queue using Stacks — problem 001 here, a DIFFERENT
                                          way to build a queue (no fixed
                                          capacity, amortized cost instead
                                          of worst-case O(1))
    LC 146  LRU Cache                     — a different fixed-capacity
                                          structure with O(1) operations,
                                          built from a doubly linked list +
                                          hashmap rather than an array
================================================================================
"""

import time
from collections import deque
from typing import List


class MyCircularQueue:
    """Fixed-size array + head index + explicit size. O(1) worst-case for
    every operation. See THE CORE IDEA above."""

    def __init__(self, k: int):
        self.buf: List[int] = [0] * k
        self.cap = k
        self.head = 0
        self.size = 0

    def enQueue(self, value: int) -> bool:
        if self.size == self.cap:
            return False
        tail = (self.head + self.size) % self.cap
        self.buf[tail] = value
        self.size += 1
        return True

    def deQueue(self) -> bool:
        if self.size == 0:
            return False
        self.head = (self.head + 1) % self.cap
        self.size -= 1
        return True

    def Front(self) -> int:
        if self.size == 0:
            return -1
        return self.buf[self.head]

    def Rear(self) -> int:
        if self.size == 0:
            return -1
        return self.buf[(self.head + self.size - 1) % self.cap]

    def isEmpty(self) -> bool:
        return self.size == 0

    def isFull(self) -> bool:
        return self.size == self.cap


class ListQueuePop0:
    """Baseline for the benchmark: a plain Python list, append at the back,
    pop(0) from the front. Same external behavior, O(n) dequeue."""

    def __init__(self, k: int):
        self.buf: List[int] = []
        self.cap = k

    def enQueue(self, value: int) -> bool:
        if len(self.buf) == self.cap:
            return False
        self.buf.append(value)
        return True

    def deQueue(self) -> bool:
        if not self.buf:
            return False
        self.buf.pop(0)                    # O(n) shift
        return True

    def Front(self) -> int:
        return self.buf[0] if self.buf else -1

    def Rear(self) -> int:
        return self.buf[-1] if self.buf else -1

    def isEmpty(self) -> bool:
        return not self.buf

    def isFull(self) -> bool:
        return len(self.buf) == self.cap


# ==============================================================================
# TESTS — run:  python 004_design_circular_queue_solution.py
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

    print("--- correctness ---")
    q = MyCircularQueue(3)
    check("enQueue(1)", q.enQueue(1), True)
    check("enQueue(2)", q.enQueue(2), True)
    check("enQueue(3)", q.enQueue(3), True)
    check("enQueue(4) when full", q.enQueue(4), False)
    check("Rear()", q.Rear(), 3)
    check("isFull()", q.isFull(), True)
    check("deQueue()", q.deQueue(), True)
    check("enQueue(4) after dequeue", q.enQueue(4), True)
    check("Rear() after wraparound", q.Rear(), 4)
    check("Front() after wraparound", q.Front(), 2)

    q2 = MyCircularQueue(2)
    check("empty Front()", q2.Front(), -1)
    check("empty Rear()", q2.Rear(), -1)
    check("empty deQueue()", q2.deQueue(), False)
    check("isEmpty() fresh", q2.isEmpty(), True)

    q3 = MyCircularQueue(1)
    check("cap=1 enQueue", q3.enQueue(9), True)
    check("cap=1 isFull", q3.isFull(), True)
    check("cap=1 enQueue when full", q3.enQueue(10), False)
    check("cap=1 deQueue", q3.deQueue(), True)
    check("cap=1 isEmpty after deQueue", q3.isEmpty(), True)

    # ----------------------------------------------------------------------
    # Randomised cross-check against a deque-backed oracle with capacity.
    # ----------------------------------------------------------------------
    import random
    print("\n--- randomised cross-check vs deque-backed capacity oracle ---")
    random.seed(2)
    mismatches = 0
    trials = 300
    for _ in range(trials):
        cap = random.randint(1, 8)
        q = MyCircularQueue(cap)
        oracle: deque = deque()
        for _ in range(random.randint(5, 60)):
            op = random.choice(["en", "de", "front", "rear"])
            if op == "en":
                val = random.randint(0, 999)
                ok_expected = len(oracle) < cap
                got = q.enQueue(val)
                if got != ok_expected:
                    mismatches += 1
                elif got:
                    oracle.append(val)
            elif op == "de":
                ok_expected = len(oracle) > 0
                got = q.deQueue()
                if got != ok_expected:
                    mismatches += 1
                elif got:
                    oracle.popleft()
            elif op == "front":
                want = oracle[0] if oracle else -1
                if q.Front() != want:
                    mismatches += 1
            else:
                want = oracle[-1] if oracle else -1
                if q.Rear() != want:
                    mismatches += 1
    print(f"  {trials} randomised sequences: {mismatches} mismatches")
    all_ok = passed == total and mismatches == 0

    # ----------------------------------------------------------------------
    # Wraparound stress: thousands of cycles past capacity.
    # ----------------------------------------------------------------------
    print("\n--- wraparound stress: 10,000 enqueue/dequeue cycles at capacity 4 ---")
    q = MyCircularQueue(4)
    for i in range(4):
        q.enQueue(i)
    ok = True
    for i in range(4, 10_004):
        q.deQueue()
        q.enQueue(i)
        if q.Rear() != i:
            ok = False
            break
    print(f"  10,000 wraparound cycles, Rear() correct every time: {ok}")
    all_ok &= ok

    # ----------------------------------------------------------------------
    # Runtime demo: circular array vs list.pop(0)-based queue, growing n.
    # ----------------------------------------------------------------------
    print("\n--- circular array vs list.pop(0) queue: measured (fill-then-drain) ---")
    print(f"  {'capacity n':>10} {'circular ms':>12} {'list ms':>10} {'ratio':>8}")
    for n in (1_000, 4_000, 10_000):
        cq = MyCircularQueue(n)
        t0 = time.perf_counter()
        for i in range(n):
            cq.enQueue(i)
        for _ in range(n):
            cq.deQueue()
        t1 = time.perf_counter()

        lq = ListQueuePop0(n)
        t2 = time.perf_counter()
        for i in range(n):
            lq.enQueue(i)
        for _ in range(n):
            lq.deQueue()
        t3 = time.perf_counter()

        c_ms = (t1 - t0) * 1000
        l_ms = (t3 - t2) * 1000
        ratio = l_ms / c_ms if c_ms > 0 else float("inf")
        print(f"  {n:>10} {c_ms:>11.2f}  {l_ms:>9.2f}  {ratio:>7.1f}x")
    print("  Fill-then-drain: n enqueues then n dequeues. list.pop(0) is")
    print("  O(current length) per call, summing to O(n^2) over n dequeues;")
    print("  the circular array's dequeue is O(1) EVERY call, no exceptions.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
