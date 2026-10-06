"""
================================================================================
SOLUTION · LeetCode 155 · Min Stack                                    [Medium]
https://leetcode.com/problems/min-stack/
================================================================================

THE CORE IDEA
--------------
This is topic 06's different pattern (topic guide Part 3) — not a monotonic
stack, but an AUXILIARY STACK maintained in lockstep with the main one,
where each entry records the running minimum AT THAT DEPTH. Pushing and
popping both stacks together keeps `min_stack[-1]` correct in O(1), with no
rescanning:

    class MinStack:
        def __init__(self):
            self.stack = []
            self.min_stack = []

        def push(self, val):
            self.stack.append(val)
            m = val if not self.min_stack else min(val, self.min_stack[-1])
            self.min_stack.append(m)      # ALWAYS push, even if not a new min

        def pop(self):
            self.stack.pop()
            self.min_stack.pop()          # pop in lockstep

        def top(self):
            return self.stack[-1]

        def getMin(self):
            return self.min_stack[-1]     # O(1), no scan

O(1) for every operation. O(n) space (two parallel stacks).


================================================================================
WHY min_stack MUST GET AN ENTRY ON EVERY PUSH, NOT JUST NEW MINIMUMS
================================================================================
The tempting shortcut is "only push to min_stack when val is smaller than
the current min" — this breaks POP. If min_stack only records new record
minimums, popping past one of those records leaves min_stack with no way
to know what the minimum was BEFORE that record was set, because the
"minimum at every depth" information was never stored for the depths that
weren't records.

Concretely: push 5 (min=5), push 3 (min=3, new record), pop (removes 3).
getMin() must now report 5 again. If min_stack only held [5, 3] and popped
to [5], that's actually fine here — but push 5, push 3, push 4, pop, pop:
after both pops the min should be 5, and min_stack must have recorded the
min at EVERY depth (5, 3, 3) so that popping twice correctly lands back on
5. If min_stack had only recorded [5, 3] (skipping the push of 4 because
4 > 3, no new record), it would desync in LENGTH from `stack`, and
`min_stack[-1]` after one pop would read the wrong depth entirely. Keeping
min_stack the SAME LENGTH as stack — one entry per push, always — is what
makes popping in lockstep correct.


================================================================================
THE NAIVE ALTERNATIVE: min(self.stack) INSIDE getMin()
================================================================================
Without the auxiliary stack, `getMin()` could just do `return min(self.stack)`
— push/pop stay O(1), but getMin() becomes O(n), because Python's `min()`
has to scan every element every single call. For a workload with MANY
interleaved getMin() calls (exactly what this problem's "at most 3*10^4
calls" constraint implies), that is O(n) per query instead of O(1) — the
same "pay a little extra space up front to make every future query O(1)"
trade topic 04's prefix sums made for range-sum queries. The runtime demo
below benchmarks this directly over many calls and measures the real gap.


================================================================================
STEP BY STEP TRACE
================================================================================
push(-2), push(0), push(-3), getMin(), pop(), top(), getMin()

    op          stack (after)     min_stack (after)     result
    ----------  ----------------  ---------------------  ------
    push(-2)    [-2]               [-2]                   -
    push(0)     [-2, 0]            [-2, -2]               -      (min(0,-2)=-2)
    push(-3)    [-2, 0, -3]        [-2, -2, -3]            -      (min(-3,-2)=-3)
    getMin()    [-2, 0, -3]        [-2, -2, -3]           -3      reads min_stack[-1]
    pop()       [-2, 0]            [-2, -2]                -      both stacks pop together
    top()       [-2, 0]            [-2, -2]                0      reads stack[-1]
    getMin()    [-2, 0]            [-2, -2]               -2      reads min_stack[-1] — correctly
                                                                    REVERTED to the min before -3
                                                                    was ever pushed


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                            push   pop    top   getMin   Space   Mutates input?
    -----------------------------------  -----  -----  ----  -------  ------  ---------------
    Single stack, min(stack) in getMin   O(1)   O(1)   O(1)  O(n)     O(n)    n/a (own structure)
    Auxiliary min-stack, lockstep ✅     O(1)   O(1)   O(1)  O(1)     O(n)    n/a (own structure)


================================================================================
EDGE CASES
================================================================================
    Push then immediately getMin() with one element -> the min IS that
        element; min_stack's first entry always equals stack's first.
    Duplicate minimums, e.g. push(1), push(1), push(2), pop(), pop() ->
        getMin() must stay 1 after each pop, because 1 was pushed TWICE —
        exercises that min_stack correctly tracks repeats, not just a
        single "record" value that could be invalidated by one pop.
    Strictly decreasing pushes, e.g. 5, 4, 3, 2, 1 -> min_stack becomes an
        exact copy of stack (every push is a new record) — the worst case
        for how "tight" the two stacks track each other.
    Strictly increasing pushes, e.g. 1, 2, 3, 4, 5 -> min_stack becomes all
        1s — every entry after the first is a repeat of the same minimum,
        confirming values are pushed even when they are NOT new records.
    Negative and boundary values (-2^31, 2^31-1) -> the algorithm does no
        arithmetic beyond `min()`, so sign and magnitude don't matter.


================================================================================
COMMON MISTAKES
================================================================================
1. Only pushing to min_stack when the new value IS a new minimum — desyncs
   the two stacks' lengths and produces wrong answers after a pop. See the
   explanation above.

2. Popping only from `stack` and forgetting to pop `min_stack` too (or vice
   versa) — same desync, different cause. They must always be the same
   length.

3. Implementing getMin() as `min(self.stack)` to "save space" — technically
   correct, but violates the O(1) requirement for getMin specifically; only
   acceptable if the interviewer explicitly relaxes that constraint.

4. Storing a single running `self.min` variable instead of a full parallel
   stack — this can't be reverted correctly on pop, because a single
   variable has no memory of what the minimum was at each earlier depth.

5. Comparing `val < min_stack[-1]` instead of computing
   `min(val, min_stack[-1])` when `min_stack` is empty (first push) — an
   empty-list index causes an IndexError; always guard the first push as a
   special case (or use `float('inf')` as a sentinel "current min" before
   any push).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you reduce the space used by the auxiliary stack?
A: Yes — instead of storing the full running min at every depth, store only
   when a NEW record is set, paired with a count of how many times that
   record value has been pushed consecutively without a smaller value
   appearing. On pop, only decrement/remove the top record when its count
   hits zero. This trades a little pop-time bookkeeping for O(k) auxiliary
   space where k = number of distinct running-minimum "regimes," which can
   be much less than n for data that trends upward with occasional dips.

Q: How would you also support getMax() in O(1)?
A: A third parallel stack, same lockstep discipline, tracking the running
   maximum instead of minimum. Independent of the min-stack.

Q: What if `push`/`pop`/`getMin` needed to be thread-safe?
A: Wrap each method body in a lock (e.g. `threading.Lock`) so the two
   stacks are always mutated atomically together — a partial update (main
   stack pushed but min_stack not yet) would desync them under concurrent
   access.

Q: Could you implement this with ONE stack instead of two, storing deltas?
A: Yes — push `val - current_min` instead of `val`, and update
   `current_min` before or after depending on sign; popping negative deltas
   signals "this pop is restoring an older minimum." It saves the second
   stack's memory at the cost of noticeably trickier arithmetic and is a
   good follow-up answer, but the two-stack version is simpler to get
   right under interview time pressure and is what most interviewers
   expect first.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 716  Max Stack                  — same idea, tracks max instead of
                                          min, plus a popMax operation
    LC 232  Implement Queue using
            Stacks                     — a different structural trick: two
                                          plain stacks simulate a queue
    LC 155 variants (getMin + count)   — extending this to also report HOW
                                          MANY times the current min occurs
================================================================================
"""

import random
import time
from typing import List


class MinStack:
    """Two parallel stacks: `stack` holds real values, `min_stack[i]` holds
    the running minimum of stack[0..i]. O(1) for every operation.
    The answer. See THE CORE IDEA above."""

    def __init__(self):
        self.stack: List[int] = []
        self.min_stack: List[int] = []

    def push(self, val: int) -> None:
        self.stack.append(val)
        m = val if not self.min_stack else min(val, self.min_stack[-1])
        self.min_stack.append(m)   # pushed EVERY time, even if not a new record

    def pop(self) -> None:
        self.stack.pop()
        self.min_stack.pop()       # pop in lockstep

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return self.min_stack[-1]  # O(1), no scan


class MinStackNaive:
    """✗ Correctness-preserving but violates the O(1)-getMin requirement —
    kept only to benchmark against. Single stack, getMin() rescans it."""

    def __init__(self):
        self.stack: List[int] = []

    def push(self, val: int) -> None:
        self.stack.append(val)

    def pop(self) -> None:
        self.stack.pop()

    def top(self) -> int:
        return self.stack[-1]

    def getMin(self) -> int:
        return min(self.stack)     # O(n) EVERY call


# ==============================================================================
# TESTS — run:  python 004_min_stack_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness: worked example from the problem statement ---")
    ms = MinStack()
    ops = [
        ("push", -2), ("push", 0), ("push", -3),
        ("getMin", None), ("pop", None), ("top", None), ("getMin", None),
    ]
    expected = [None, None, None, -3, None, 0, -2]
    for (name, arg), want in zip(ops, expected):
        method = getattr(ms, name)
        got = method(arg) if arg is not None else method()
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}({'' if arg is None else arg}) -> {got}  (want {want})")

    # ----------------------------------------------------------------------
    # Duplicate minimums.
    # ----------------------------------------------------------------------
    print("\n--- correctness: duplicate minimums must survive repeated pops ---")
    ms2 = MinStack()
    seq = [
        ("push", 1, None), ("push", 1, None), ("push", 2, None),
        ("getMin", None, 1), ("pop", None, None), ("getMin", None, 1),
        ("pop", None, None), ("getMin", None, 1),
    ]
    for name, arg, want in seq:
        method = getattr(ms2, name)
        got = method(arg) if arg is not None else method()
        if want is not None:
            ok = got == want
            all_ok &= ok
            print(f"{'PASS' if ok else 'FAIL'}  {name}({'' if arg is None else arg}) -> {got}  (want {want})")

    # ----------------------------------------------------------------------
    # Randomised cross-check vs the naive O(n)-getMin implementation.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check: MinStack vs MinStackNaive ---")
    random.seed(4)
    mismatches = 0
    trials = 500
    for _ in range(trials):
        a, b = MinStack(), MinStackNaive()
        n_ops = random.randint(1, 40)
        depth = 0
        for _ in range(n_ops):
            choice = random.random()
            if choice < 0.6 or depth == 0:
                val = random.randint(-1000, 1000)
                a.push(val)
                b.push(val)
                depth += 1
            elif choice < 0.8:
                a.pop()
                b.pop()
                depth -= 1
            elif choice < 0.9:
                if a.top() != b.top():
                    mismatches += 1
            else:
                if a.getMin() != b.getMin():
                    mismatches += 1
    print(f"  {trials} randomised operation sequences: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: push(-2), push(0), push(-3), getMin(), pop(), top(), getMin() ---")
    ms3 = MinStack()
    trace_ops = [("push", -2), ("push", 0), ("push", -3), ("getMin", None),
                 ("pop", None), ("top", None), ("getMin", None)]
    for name, arg in trace_ops:
        method = getattr(ms3, name)
        result = method(arg) if arg is not None else method()
        label = f"{name}({arg})" if arg is not None else f"{name}()"
        result_str = f" -> {result}" if result is not None else ""
        print(f"  {label:<12}{result_str:<8} stack: {ms3.stack!s:<16} min_stack: {ms3.min_stack}")

    # ----------------------------------------------------------------------
    # O(1) getMin (auxiliary stack) vs O(n) getMin (min(stack)): measured.
    # ----------------------------------------------------------------------
    print("\n--- O(1) auxiliary-stack getMin vs O(n) min(stack) getMin: measured runtime ---")
    print("  (fill the stack to size n, then time many interleaved getMin() calls)")
    print(f"  {'n':>7} {'calls':>7} {'aux O(1) total':>16} {'naive O(n) total':>18} {'ratio':>8}")
    random.seed(1)
    for n in (1_000, 5_000, 20_000):
        fill = [random.randint(-10_000, 10_000) for _ in range(n)]
        n_calls = 5_000

        aux = MinStack()
        for v in fill:
            aux.push(v)
        t0 = time.perf_counter()
        for _ in range(n_calls):
            aux.getMin()
        t1 = time.perf_counter()
        aux_ms = (t1 - t0) * 1000

        naive = MinStackNaive()
        for v in fill:
            naive.push(v)
        t2 = time.perf_counter()
        for _ in range(n_calls):
            naive.getMin()
        t3 = time.perf_counter()
        naive_ms = (t3 - t2) * 1000

        ratio = naive_ms / aux_ms if aux_ms > 0 else float("inf")
        print(f"  {n:>7} {n_calls:>7} {aux_ms:>14.2f}ms {naive_ms:>16.2f}ms {ratio:>7.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
