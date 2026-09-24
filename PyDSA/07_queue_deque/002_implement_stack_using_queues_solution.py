"""
================================================================================
SOLUTION · LeetCode 225 · Implement Stack using Queues                  [Easy]
https://leetcode.com/problems/implement-stack-using-queues/
================================================================================

THE CORE IDEA
--------------
A single queue, plus a rotation on every push: append the new element to
the back, then rotate every OLDER element around it (pop from front, push
to back, repeated `len(q) - 1` times) so the new element ends up at the
FRONT — where a queue's O(1) `popleft` can serve it as "top of stack."

    from collections import deque
    q = deque()

    def push(x):
        q.append(x)
        for _ in range(len(q) - 1):
            q.append(q.popleft())

    def pop():
        return q.popleft()      # front is ALWAYS the most recently pushed

    def top():
        return q[0]

This is the mirror of problem 001 (topic guide §2.1): there, the trick made
`enqueue` free and `dequeue` amortized O(1). Here, `pop`/`top` are always
O(1), and the cost is pushed entirely onto `push`, EVERY call, with no
amortization available — see below for why.


================================================================================
WHY PUSH CANNOT BE MADE LAZY THE WAY 001's DEQUEUE WAS
================================================================================
001's queue-from-stacks trick could defer work: dequeue only transfers when
out_stack is empty, because a stale ordering in out_stack stays valid until
it's fully drained — nothing about a later push() invalidates an
already-correct out_stack.

Here, the situation is different: EVERY push must be resolved before the
very next pop/top call, because that call needs to see the NEW element at
the front immediately. There's no safe way to defer "rotate the new element
into place" — if you skip the rotation, the next `top()` returns the WRONG
(oldest, not newest) element. So the O(current size) cost of the rotation
is paid on every single push, not amortized away. Trace it:

    push(1): q=[1]                             rotate 0 times
    push(2): q=[1,2] -> rotate 1x -> q=[2,1]     (2 now at front, correctly "top")
    push(3): q=[2,1,3] -> rotate 2x -> q=[1,3,2] -> q=[3,2,1]
    pop() -> 3   (front = most recently pushed, LIFO ✓)


================================================================================
THE ASYMMETRY WITH PROBLEM 001 — say this out loud in an interview
================================================================================
    Problem 001 (queue from stacks):  enqueue O(1) always, dequeue amortized O(1)
    Problem 002 (stack from queues):  push O(current size) EVERY call, pop/top O(1) always

There's no way to make BOTH operations O(1) worst-case using only the
mirror structure's primitives in either direction — one side always pays.
001 gets to hide the cost via amortization (spread over many cheap calls).
002 cannot hide it, because correctness demands the reordering happen
immediately, every time. This is a genuinely different trade-off, not the
same idea restated — the runtime demo below makes the O(n)-per-push cost
concrete, growing with the count.


================================================================================
STEP BY STEP TRACE
================================================================================
push(1), push(2), push(3), pop(), push(4), pop(), pop(), pop()

    op        queue (deque, front..back)     returns
    push(1)   [1]                             -
    push(2)   [2, 1]                          -
    push(3)   [3, 2, 1]                       -
    pop()     [2, 1]                          3
    push(4)   [4, 2, 1]                       -
    pop()     [2, 1]                          4
    pop()     [1]                             2
    pop()     []                              1

Matches the runtime trace printed by the test suite below exactly — the
front of the deque is always the most recently pushed element still
present, by construction.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              push        pop/top    Space   Mutates input?
    -------------------------------------  ----------  ---------  ------  ---------------
    Single queue + rotate-on-push (answer)  O(n)         O(1)       O(n)    n/a (self-contained)
    Two queues, push to fresh + drain old    O(n)         O(1)       O(n)    n/a  — same total
                                                                                    element moves
    Naive: Python list as if already a stack  O(1)         O(1)       O(n)    n/a  — doesn't use
                                                                                    only queue ops,
                                                                                    doesn't solve
                                                                                    the exercise


================================================================================
EDGE CASES
================================================================================
    push then immediately pop/top        -> single-element rotation loop
                                            runs 0 times; trivial.
    interleaved push/pop                  -> each push independently
                                            re-establishes correct order;
                                            no cross-call state assumptions.
    many pushes then many pops             -> push cost GROWS with each call
                                            (O(1), O(2), O(3), ... O(n)) —
                                            quadratic total for n pushes,
                                            unlike 001's linear total.
    empty() on a fresh stack                -> True.
    single element push/pop repeatedly       -> exercises the "rotate 0
                                            times" branch every time.


================================================================================
COMMON MISTAKES
================================================================================
1. Rotating BEFORE appending the new element instead of after — puts the
   new element in the wrong position; `top()` returns a stale value.

2. Using `len(q)` instead of `len(q) - 1` for the rotation count — rotates
   one time too many, cycling the new element back to the rear.

3. Believing this can be made amortized O(1) like problem 001. It cannot:
   001's trick works because staleness in out_stack is SAFE until drained;
   here, an un-rotated queue gives an immediately WRONG answer to the very
   next top()/pop() call, so there is no safe deferral.

4. Using `list.pop(0)` instead of `deque.popleft()` for the "queue"
   primitive — technically produces the right answer but reintroduces an
   O(n) cost on an operation that's supposed to be the queue's cheap
   primitive, silently changing this from O(n) push / O(1) pop to O(n) on
   both.

5. Forgetting `empty()` needs to check the queue's length, not some
   separate counter that can drift out of sync with actual pushes/pops.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you avoid the rotation and instead track "top" as the LAST pushed
   element in a separate variable?
A: You can track top() in O(1) trivially with a variable updated on every
   push, but pop() still needs to physically reorder the queue to expose
   the SECOND-to-last element as the new top — the rotation cost doesn't
   go away, it just gets deferred from push to pop. Total work is the
   same either way.

Q: What's the two-queue version and is it actually different in cost?
A: Push into a fresh second queue, then drain the old queue into it (so
   the new element ends up first), then treat the second queue as primary.
   Same O(n) total element moves per push as the single-queue rotation —
   different bookkeeping, identical complexity.

Q: Compare this to problem 001's amortized argument directly.
A: 001 defers the expensive step and proves the deferred cost still sums
   to O(n) total over n operations (amortized O(1) per op). Here, the
   expensive step CANNOT be deferred — correctness requires it happen
   synchronously on every push — so there is no amortization to invoke;
   push is simply O(current size) worst-case, every time.

Q: Is this the practical way to build a stack in Python?
A: No — Python's list is already an O(1)-both-ends-enough stack
   (`append`/`pop`). This exercise, like 001, exists to practice
   simulating one discipline with the other's primitives, not to produce
   a faster real stack.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 232  Implement Queue using Stacks    — the mirror trick (problem 001
                                              here); dequeue pays instead,
                                              amortized away
    LC 155  Min Stack                        — topic 06, a genuine stack with
                                              an augmented invariant
    LC 641  Design Circular Deque             — problem 005 here, a from-
                                              scratch container needing
                                              neither trick
================================================================================
"""

import time
from collections import deque
from typing import List


class MyStack:
    """Single queue + rotate-on-push. push() O(n); pop()/top() O(1).
    See THE CORE IDEA above."""

    def __init__(self):
        self.q: deque = deque()

    def push(self, x: int) -> None:
        self.q.append(x)
        for _ in range(len(self.q) - 1):
            self.q.append(self.q.popleft())

    def pop(self) -> int:
        return self.q.popleft()

    def top(self) -> int:
        return self.q[0]

    def empty(self) -> bool:
        return not self.q


class MyStackTwoQueue:
    """Alternative: two queues, push into the fresh one then drain the old
    one behind it. Same total element-move cost as the single-queue
    rotation — kept to demonstrate they're asymptotically identical, not to
    claim an improvement."""

    def __init__(self):
        self.q1: deque = deque()
        self.q2: deque = deque()

    def push(self, x: int) -> None:
        self.q2.append(x)
        while self.q1:
            self.q2.append(self.q1.popleft())
        self.q1, self.q2 = self.q2, self.q1

    def pop(self) -> int:
        return self.q1.popleft()

    def top(self) -> int:
        return self.q1[0]

    def empty(self) -> bool:
        return not self.q1


class MyStackListSlowQueue:
    """✗ COMMON MISTAKE, DEMONSTRATED ON PURPOSE — uses a Python list with
    pop(0) as the "queue" primitive instead of collections.deque. Still
    correct, but turns the already-O(n) push into something worse (O(n) per
    ROTATION STEP, since pop(0) itself is O(n)) — see the benchmark below."""

    def __init__(self):
        self.q: List[int] = []

    def push(self, x: int) -> None:
        self.q.append(x)
        for _ in range(len(self.q) - 1):
            self.q.append(self.q.pop(0))          # pop(0) on a list: O(n) itself

    def pop(self) -> int:
        return self.q.pop(0)

    def top(self) -> int:
        return self.q[0]

    def empty(self) -> bool:
        return not self.q


# ==============================================================================
# TESTS — run:  python 002_implement_stack_using_queues_solution.py
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
    for impl_name, Impl in (("single-queue rotate", MyStack), ("two-queue", MyStackTwoQueue)):
        s = Impl()
        s.push(1)
        s.push(2)
        check(f"[{impl_name}] top after push(1),push(2)", s.top(), 2)
        check(f"[{impl_name}] pop", s.pop(), 2)
        check(f"[{impl_name}] empty after one pop", s.empty(), False)
        check(f"[{impl_name}] pop remaining", s.pop(), 1)
        check(f"[{impl_name}] empty after both popped", s.empty(), True)

        s2 = Impl()
        for x in (5, 6, 7, 8):
            s2.push(x)
        check(f"[{impl_name}] LIFO order", [s2.pop() for _ in range(4)], [8, 7, 6, 5])

    # ----------------------------------------------------------------------
    # Full trace, printed (referenced by "STEP BY STEP TRACE" above).
    # ----------------------------------------------------------------------
    print("\n--- full trace: push(1) push(2) push(3) pop() push(4) pop() pop() pop() ---")
    s = MyStack()
    ops = [("push", 1), ("push", 2), ("push", 3), ("pop", None),
           ("push", 4), ("pop", None), ("pop", None), ("pop", None)]
    for op, val in ops:
        if op == "push":
            s.push(val)
            print(f"  push({val}) -> q = {list(s.q)}")
        else:
            r = s.pop()
            print(f"  pop()    -> q = {list(s.q)}   returned {r}")

    # ----------------------------------------------------------------------
    # Randomised cross-check vs a plain list-based LIFO oracle.
    # ----------------------------------------------------------------------
    import random
    print("\n--- randomised cross-check vs list-based LIFO oracle ---")
    random.seed(3)
    mismatches = 0
    trials = 500
    for _ in range(trials):
        s = MyStack()
        oracle = []
        for _ in range(random.randint(5, 40)):
            if oracle and random.random() < 0.4:
                got = s.pop()
                want = oracle.pop()
                if got != want:
                    mismatches += 1
            else:
                x = random.randint(1, 9)
                s.push(x)
                oracle.append(x)
    print(f"  {trials} randomised sequences: {mismatches} mismatches")
    all_ok = passed == total and mismatches == 0

    # ----------------------------------------------------------------------
    # Runtime demo: push cost GROWS with size — O(n) per push, O(n^2) total
    # for n pushes. Contrast this against 001's O(n) TOTAL for n enqueues.
    # ----------------------------------------------------------------------
    print("\n--- measured: push cost grows with current size (O(n) per push) ---")
    print(f"  {'n pushes':>10} {'total ms':>10} {'ms/push (last 10%)':>22}")
    for n in (500, 1_500, 4_000):
        s = MyStack()
        t0 = time.perf_counter()
        for i in range(n):
            s.push(i)
        t1 = time.perf_counter()
        total_ms = (t1 - t0) * 1000

        # Time just the LAST 10% of pushes, where the queue is near its
        # largest — this isolates the per-push cost at high n from the
        # cheap early pushes.
        s2 = MyStack()
        warmup = int(n * 0.9)
        for i in range(warmup):
            s2.push(i)
        t2 = time.perf_counter()
        tail = max(1, n - warmup)
        for i in range(tail):
            s2.push(i)
        t3 = time.perf_counter()
        per_push_late = (t3 - t2) * 1000 / tail
        print(f"  {n:>10} {total_ms:>9.2f}  {per_push_late:>21.4f}")
    print("  Per-push cost near the end (~n) is visibly larger than near the")
    print("  start — confirms push is O(current size), not O(1), each call.")

    # ----------------------------------------------------------------------
    # deque-backed rotation vs list.pop(0)-backed rotation.
    # ----------------------------------------------------------------------
    print("\n--- deque rotation vs list.pop(0) rotation (compounding the O(n) cost) ---")
    print(f"  {'n pushes':>10} {'deque ms':>10} {'list ms':>10} {'ratio':>8}")
    for n in (400, 900, 1_600):
        s_deque = MyStack()
        t0 = time.perf_counter()
        for i in range(n):
            s_deque.push(i)
        t1 = time.perf_counter()

        s_list = MyStackListSlowQueue()
        t2 = time.perf_counter()
        for i in range(n):
            s_list.push(i)
        t3 = time.perf_counter()

        d_ms = (t1 - t0) * 1000
        l_ms = (t3 - t2) * 1000
        ratio = l_ms / d_ms if d_ms > 0 else float("inf")
        print(f"  {n:>10} {d_ms:>9.2f}  {l_ms:>9.2f}  {ratio:>7.1f}x")
    print("  list.pop(0) is itself O(n), so using a list as the underlying")
    print("  'queue' compounds the already-O(n) rotation into something worse.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
