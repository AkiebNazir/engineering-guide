"""
================================================================================
SOLUTION · LeetCode 232 · Implement Queue using Stacks                  [Easy]
https://leetcode.com/problems/implement-queue-using-stacks/
================================================================================

THE CORE IDEA
--------------
Two stacks, one direction of flow each:

    in_stack   receives every push(), always O(1) — just append.
    out_stack  is what pop()/peek() read from. When it's empty, drain
               in_stack into it completely (pop from in_stack, push onto
               out_stack) — this REVERSES the order, turning "most recently
               pushed on top" into "least recently pushed on top," which is
               exactly FIFO.

    def push(x):
        in_stack.append(x)

    def pop():
        _fill_out_stack_if_needed()
        return out_stack.pop()

The critical rule: only refill out_stack when it is EMPTY. See the topic
guide §2.0 for the full amortization argument; the short version is below.


================================================================================
THE AMORTIZATION ARGUMENT — why dequeue is O(1) AMORTIZED, not O(1) always
================================================================================
A single pop() call CAN cost O(n) — if out_stack is empty and in_stack holds
n elements, that one call drains all n. That is a genuinely expensive call.
But it can only happen when out_stack is empty, and once the drain
completes, EVERY element it moved sits in out_stack ready for O(1) pops
until out_stack empties again — at which point another drain becomes
possible, but only after that many more pushes have refilled in_stack.

Track total work per element across its whole lifetime:
    1 push onto in_stack           (in push())
    1 pop off in_stack             (during a drain, at most once)
    1 push onto out_stack          (during that same drain, at most once)
    1 pop off out_stack            (in pop(), when it's finally returned)

That's AT MOST 4 stack operations per element, ever — regardless of how
enqueue/dequeue calls are interleaved. n elements -> at most 4n total
operations across the whole run -> O(1) amortized per queue operation. Any
one dequeue call might be expensive, but the AVERAGE cost over a long
sequence is O(1). This is the same style of argument as topic 03's
"monotone pointer, bounded total movement" — cost is bounded over the whole
run, not per call.

⚠️ This argument DEPENDS on refilling out_stack only when empty. Refill it
unconditionally on every pop() (a common overzealous "just in case" bug) and
you break nothing about CORRECTNESS but you re-pay the O(current in_stack
size) transfer cost far more often than necessary — see the benchmark below,
which measures a deliberately-broken "eager transfer" variant against the
lazy one.


================================================================================
STEP BY STEP TRACE
================================================================================
push(1), push(2), push(3), pop(), push(4), pop(), pop(), pop()

    op        in_stack     out_stack    action                        returns
    push(1)   [1]          []           append to in_stack             -
    push(2)   [1,2]        []           append to in_stack             -
    push(3)   [1,2,3]      []           append to in_stack             -
    pop()     [1,2,3]->[]  [3,2,1]      out empty -> DRAIN all of in    1
              []           [3,2]        then pop out_stack.pop()->1
    push(4)   [4]          [3,2]        append to in_stack             -
    pop()     [4]          [3,2]->[3]   out NOT empty -> no drain      2
    pop()     [4]          [3]->[]      out NOT empty -> no drain      3
    pop()     [4]->[]      [4]          out EMPTY -> DRAIN in (=[4])   4
              []           []           then pop -> 4

Final popped sequence: 1, 2, 3, 4 — exactly FIFO / arrival order.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                             Time (push)   Time (pop)         Space   Mutates input?
    -----------------------------------  ------------  ------------------  ------  ---------------
    Naive: Python list, insert(0, x)     O(n)           O(1) (pop(0)->x)*   O(n)    n/a (self-contained)
    Naive: Python list, append + pop(0)   O(1)           O(n)                O(n)    n/a
    Two stacks, LAZY transfer (answer)    O(1)           O(1) amortized      O(n)    n/a
    Two stacks, EAGER transfer (broken)   O(1)           O(n) EVERY call     O(n)    n/a  ✗ defeats the point

    * "naive" here means literally using a Python list as if it already
      were the answer — it's not implementing a queue FROM STACKS, so it
      doesn't satisfy the problem, but it's the baseline the exercise exists
      to beat conceptually. The two-stack solution matches its FIFO
      behavior using ONLY stack primitives.


================================================================================
EDGE CASES
================================================================================
    push then immediately pop           -> pop drains a 1-element in_stack;
                                            trivial but exercises the drain path.
    interleaved push/pop mid-drain      -> pushing while out_stack is
                                            non-empty must NOT trigger a
                                            drain (the "only when empty"
                                            rule) — tested explicitly below.
    many pushes, then many pops         -> one big drain, then all O(1) pops;
                                            the worst-case-cost call.
    alternating push/pop one at a time  -> forces a drain roughly every
                                            other call; still amortized O(1)
                                            per call across the whole run.
    peek() without popping              -> must not consume the front
                                            element; implemented via
                                            "ensure out_stack non-empty,
                                            then read out_stack[-1]".
    empty() on a fresh queue            -> True; both stacks empty.


================================================================================
COMMON MISTAKES
================================================================================
1. Draining in_stack into out_stack on EVERY pop(), not just when
   out_stack is empty. Still correct, but O(n) per pop instead of amortized
   O(1) — defeats the entire point of the exercise. Benchmarked below.

2. Implementing peek() by popping and forgetting to push the value back
   (or pushing it back onto the wrong stack) — corrupts FIFO order for
   subsequent calls.

3. Forgetting the drain must POP from in_stack and PUSH onto out_stack in
   the SAME loop iteration pair — draining into a temporary list and then
   copying it in the same order doesn't reverse anything.

4. Assuming pop() is worst-case O(1) and using this structure somewhere
   real-time/worst-case-latency-sensitive matters (e.g. a hard real-time
   scheduler) — amortized O(1) is not the same guarantee as worst-case
   O(1); a single call can still spike.

5. Treating this as "just use collections.deque as one of the stacks" —
   the exercise's point is implementing FIFO using ONLY LIFO primitives;
   defeating that with a different container misses the lesson (fine to
   mention as the practical real-world answer, wrong as a solution to
   THIS exercise).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What's the worst-case cost of a single dequeue call, not amortized?
A: O(n) — if out_stack is empty and in_stack holds everything, one pop()
   drains it all. Amortized O(1) does not mean every call is fast.

Q: Could you make push() O(1) worst-case AND pop() O(1) worst-case
   simultaneously, using only two stacks?
A: Not with this trick — one direction always pays. Here dequeue absorbs
   the (amortized-away) cost. See 002 for the mirror: implementing a stack
   from queues, where PUSH is the one that pays every single call, with no
   amortization available to hide it (topic guide §2.1).

Q: How would you implement this with three stacks, or with a max-tracking
   variant (like a queue that also supports getMax in O(1))?
A: A third "helper" stack can track auxiliary info (e.g. a running max)
   alongside in_stack the way topic 06's min-stack tracks a running min;
   the FIFO mechanism itself doesn't change.

Q: Is `collections.deque` not simpler for a real queue?
A: Yes, trivially — `deque.append`/`deque.popleft` are both O(1), no
   amortization needed, no second stack. This exercise's entire value is
   practicing the amortization argument, not finding the fastest real
   queue in Python (see the topic guide §4 for when to just use deque).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 225  Implement Stack using Queues     — the mirror trick (problem 002
                                                here); push pays instead of pop
    LC 155  Min Stack                         — topic 06, same "second stack
                                                tracks an invariant" idea
    LC 622  Design Circular Queue             — a from-scratch fixed-capacity
                                                queue, no amortization needed
                                                (problem 004 here)
================================================================================
"""

import time
from typing import List


class MyQueue:
    """Two-stack queue. push() O(1); pop()/peek() O(1) amortized.
    See THE CORE IDEA and the amortization argument above."""

    def __init__(self):
        self.in_stack: List[int] = []
        self.out_stack: List[int] = []

    def push(self, x: int) -> None:
        self.in_stack.append(x)

    def _fill_out(self) -> None:
        if not self.out_stack:                      # ONLY refill when empty
            while self.in_stack:
                self.out_stack.append(self.in_stack.pop())

    def pop(self) -> int:
        self._fill_out()
        return self.out_stack.pop()

    def peek(self) -> int:
        self._fill_out()
        return self.out_stack[-1]

    def empty(self) -> bool:
        return not self.in_stack and not self.out_stack


class MyQueueEagerBroken:
    """✗ BROKEN (in cost, not correctness) ON PURPOSE — drains in_stack into
    out_stack on EVERY pop() call, not just when out_stack is empty. Still
    returns correct FIFO order, but destroys the amortization argument:
    O(n) work per pop() instead of amortized O(1). Used only in the
    benchmark below."""

    def __init__(self):
        self.in_stack: List[int] = []
        self.out_stack: List[int] = []

    def push(self, x: int) -> None:
        self.in_stack.append(x)

    def _fill_out_ALWAYS(self) -> None:              # the bug: no emptiness check
        temp = []
        while self.out_stack:
            temp.append(self.out_stack.pop())
        while self.in_stack:
            self.out_stack.append(self.in_stack.pop())
        while temp:
            self.out_stack.append(temp.pop())

    def pop(self) -> int:
        self._fill_out_ALWAYS()
        return self.out_stack.pop()

    def peek(self) -> int:
        self._fill_out_ALWAYS()
        return self.out_stack[-1]

    def empty(self) -> bool:
        return not self.in_stack and not self.out_stack


# ==============================================================================
# TESTS — run:  python 001_implement_queue_using_stacks_solution.py
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
    q = MyQueue()
    q.push(1)
    q.push(2)
    check("peek after push(1), push(2)", q.peek(), 1)
    check("pop after push(1), push(2)", q.pop(), 1)
    check("empty after one pop", q.empty(), False)
    check("pop remaining", q.pop(), 2)
    check("empty after both popped", q.empty(), True)

    q2 = MyQueue()
    for x in (5, 6, 7, 8):
        q2.push(x)
    check("basic FIFO order", [q2.pop() for _ in range(4)], [5, 6, 7, 8])

    q3 = MyQueue()
    q3.push(1)
    q3.push(2)
    check("pop mid-sequence", q3.pop(), 1)
    q3.push(3)                                       # push while out_stack non-empty
    check("push during non-empty out_stack, pop next", q3.pop(), 2)
    check("pop final", q3.pop(), 3)
    check("empty at end", q3.empty(), True)

    # ----------------------------------------------------------------------
    # Cross-check against Python's own list-based FIFO oracle, randomised.
    # ----------------------------------------------------------------------
    import random
    print("\n--- randomised cross-check vs list-based FIFO oracle ---")
    random.seed(11)
    mismatches = 0
    trials = 500
    for _ in range(trials):
        q = MyQueue()
        oracle = []
        ops = random.randint(5, 40)
        for _ in range(ops):
            if oracle and random.random() < 0.4:
                got = q.pop()
                want = oracle.pop(0)
                if got != want:
                    mismatches += 1
            else:
                x = random.randint(1, 9)
                q.push(x)
                oracle.append(x)
    print(f"  {trials} randomised sequences: {mismatches} mismatches")
    all_ok = passed == total and mismatches == 0

    # ----------------------------------------------------------------------
    # ⚠️ Amortized (lazy) vs O(n)-per-call (eager) transfer: measured.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ lazy (amortized O(1)) vs eager (O(n) every call) transfer: measured ---")
    print(f"  {'n ops':>8} {'lazy ms':>10} {'eager ms':>10} {'ratio':>8}")
    for n in (2_000, 6_000, 12_000):
        # Workload: push n items, then pop n items (worst case for "eager":
        # every pop triggers a full drain because out_stack never refills
        # from a fresh in_stack in between — this is the classic pattern
        # that makes the O(n)-per-call cost visible).
        q_lazy = MyQueue()
        for i in range(n):
            q_lazy.push(i)
        t0 = time.perf_counter()
        for _ in range(n):
            q_lazy.pop()
        t1 = time.perf_counter()

        q_eager = MyQueueEagerBroken()
        for i in range(n):
            q_eager.push(i)
        t2 = time.perf_counter()
        for _ in range(n):
            q_eager.pop()
        t3 = time.perf_counter()

        lazy_ms = (t1 - t0) * 1000
        eager_ms = (t3 - t2) * 1000
        ratio = eager_ms / lazy_ms if lazy_ms > 0 else float("inf")
        print(f"  {n:>8} {lazy_ms:>9.2f}  {eager_ms:>9.2f}  {ratio:>7.1f}x")

    print("\n  Note: for this exact pop-after-all-pushes pattern, the LAZY")
    print("  version does ONE big drain (like the eager one always does),")
    print("  so the interesting comparison is an INTERLEAVED workload —")
    print("  measured next.")

    print("\n--- interleaved push/pop workload (this is where lazy really wins) ---")
    print(f"  {'n ops':>8} {'lazy ms':>10} {'eager ms':>10} {'ratio':>8}")
    for n in (2_000, 6_000, 12_000):
        q_lazy = MyQueue()
        t0 = time.perf_counter()
        for i in range(n):
            q_lazy.push(i)
            q_lazy.push(i)
            q_lazy.pop()
        t1 = time.perf_counter()

        q_eager = MyQueueEagerBroken()
        t2 = time.perf_counter()
        for i in range(n):
            q_eager.push(i)
            q_eager.push(i)
            q_eager.pop()
        t3 = time.perf_counter()

        lazy_ms = (t1 - t0) * 1000
        eager_ms = (t3 - t2) * 1000
        ratio = eager_ms / lazy_ms if lazy_ms > 0 else float("inf")
        print(f"  {n:>8} {lazy_ms:>9.2f}  {eager_ms:>9.2f}  {ratio:>7.1f}x")
    print("  Eager re-drains out_stack (reversing it out, then back in) on")
    print("  EVERY pop even though it already held ready elements — pure")
    print("  wasted work the lazy version skips entirely.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
