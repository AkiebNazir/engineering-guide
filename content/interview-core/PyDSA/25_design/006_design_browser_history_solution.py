"""
================================================================================
SOLUTION · LeetCode 1472 · Design Browser History                       [Medium]
https://leetcode.com/problems/design-browser-history/
================================================================================

THE CORE IDEA
--------------
An array plus a cursor index models exactly how a real browser's history
works: `visit` TRUNCATES the array to the cursor before appending (forward
history is genuinely destroyed, not hidden), and `back`/`forward` just
move the cursor, clamped to `[0, len(history)-1]`. No node-reference
splicing is needed — index arithmetic does everything a doubly linked
list would, more simply, because there's exactly one "current position"
concept and no arbitrary-node access requirement.


================================================================================
APPROACH 1 · Two stacks (back-stack, forward-stack) (alternative, priced,
not coded)
================================================================================
A common textbook framing: a `back` stack (pages behind the current one)
and a `forward` stack (pages ahead). `visit` pushes the current page onto
`back` and CLEARS `forward` entirely. `back(steps)` pops up to `steps`
pages from `back` onto `forward` (or fewer if `back` runs out); `forward`
does the mirror operation.

    visit:            O(1)
    back(steps):      O(steps) — must pop one at a time to know exactly
                       how far it's possible to go and to correctly refill
                       the OTHER stack page-by-page
    forward(steps):   O(steps)

Correct and a legitimate way to think about it, but doing `steps` real
pops/pushes per call is asymptotically worse than the array+cursor
approach for large `steps` (bounded by 100 per constraints, so it would
still pass, but strictly more work for the same result) — not coded
separately since Approach 2 dominates it in both simplicity and speed.


================================================================================
APPROACH 2 · Array + cursor index ✅ (the answer)
================================================================================
    class BrowserHistory:
        def __init__(self, homepage):
            self.history = [homepage]
            self.cursor = 0

        def visit(self, url):
            del self.history[self.cursor + 1:]     # discard ALL forward history
            self.history.append(url)
            self.cursor += 1

        def back(self, steps):
            self.cursor = max(0, self.cursor - steps)
            return self.history[self.cursor]

        def forward(self, steps):
            self.cursor = min(len(self.history) - 1, self.cursor + steps)
            return self.history[self.cursor]

The clamping (`max(0, ...)` / `min(len-1, ...)`) IS the spec's "move only
x < steps steps if that's all that's possible" rule — no separate branch
needed, the arithmetic handles it directly.

    Time: O(1) per call (`del history[cursor+1:]` is O(discarded count),
          amortized against the visits that created those entries in the
          first place — never more total truncation work across the whole
          session than total appends).     Space: O(session length).


================================================================================
STEP BY STEP TRACE
================================================================================
    init("leetcode.com")   history=["leetcode.com"]                       cursor=0
    visit("google.com")    history=["leetcode.com","google.com"]          cursor=1
    visit("facebook.com")  history=[...,"facebook.com"]                   cursor=2
    visit("youtube.com")   history=[...,"youtube.com"]                    cursor=3
    back(1)                 cursor = max(0, 3-1) = 2  -> "facebook.com"
    back(1)                 cursor = max(0, 2-1) = 1  -> "google.com"
    forward(1)               cursor = min(3, 1+1) = 2  -> "facebook.com"
    visit("linkedin.com")   del history[3:]  -> drops "youtube.com"!
                             history=["leetcode.com","google.com","facebook.com","linkedin.com"]
                             cursor=3
    forward(2)               cursor = min(3, 3+2) = 3  -> "linkedin.com" (can't go further, clamped)
    back(2)                  cursor = max(0, 3-2) = 1  -> "google.com"
    back(7)                  cursor = max(0, 1-7) = 0  -> "leetcode.com" (clamped, not -6)

    ASCII, array state right before visit("linkedin.com") — cursor sits at
    "facebook.com" after the forward(1), with "youtube.com" still present
    but about to be destroyed:

        ["leetcode.com", "google.com", "facebook.com", "youtube.com"]
                                          ^cursor=2        ^about to be
                                                             truncated away
    after visit("linkedin.com"):
        ["leetcode.com", "google.com", "facebook.com", "linkedin.com"]
                                                            ^cursor=3


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    visit         back(steps)   forward(steps)   Space
    ----------------------------  ------------  ------------  ---------------  -----
    Two stacks (back/forward)   O(1)          O(steps)      O(steps)         O(session)
    Array + cursor ✅           O(1) amort.   O(1)          O(1)             O(session)
    Mutates input? n/a — design problem in every row.


================================================================================
EDGE CASES
================================================================================
    back/forward with steps
      exceeding available history  Must clamp to the first/last page, not
                                    raise or wrap around — `max(0, ...)`
                                    and `min(len-1, ...)` handle this.
    visit right after a back()      Must discard ALL forward pages, even
                                    if there were several — a common bug
                                    truncates only one instead of
                                    everything past the cursor.
    Repeated visit() with no
      intervening back()             Cursor always tracks `len(history)-1`
                                    — the truncation `del history[cursor+1:]`
                                    is a no-op when cursor is already at
                                    the end, so this degenerates cleanly to
                                    plain appends.
    back(steps) / forward(steps)
      when already at a boundary     Must return the SAME page, not error
                                    — an immediate `back(1)` at cursor=0
                                    stays at cursor=0.
    steps == exactly the remaining
      distance                       Must land EXACTLY on the boundary
                                    page, not overshoot by one (off-by-one
                                    the clamp arithmetic must get right).


================================================================================
COMMON MISTAKES
================================================================================
1. `visit` appending WITHOUT truncating first — leaves stale forward
   history that a subsequent `forward()` call would incorrectly resurrect;
   this is the single defining bug for this problem (it's the whole point
   of the "visit clears forward history" rule).

2. Truncating with an off-by-one (`del history[cursor:]` instead of
   `del history[cursor+1:]`) — accidentally deletes the CURRENT page too,
   not just the forward pages after it.

3. Not clamping `back`/`forward` and instead letting the cursor go
   negative or past the array's end — causes an `IndexError` (or, worse,
   silently wraps via Python's negative-indexing semantics, returning the
   WRONG page instead of crashing, which is harder to notice in testing).

4. Reaching for a doubly linked list out of habit ("this is topic 08's
   territory") when the problem's access pattern (one current position,
   index-relative movement, no arbitrary-node splicing) is a strictly
   better fit for a plain array — added pointer-management complexity
   with no corresponding benefit here.

5. Forgetting that `homepage` itself counts as the first history entry —
   `back(1)` immediately after construction with no `visit()` calls yet
   must return `homepage` (clamped, cursor stays 0), not error or return
   something else.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would you support MULTIPLE tabs, each with its own history?
A: One `BrowserHistory` instance per tab — the class already encapsulates
   exactly one tab's state; a browser-level manager would just hold a
   dict of `tab_id -> BrowserHistory`.

Q: What if visiting a page needed to be UNDONE (a true undo, not just
   "go back")?
A: "Back" already IS undo for navigation in this model — the distinction
   from a general undo/redo stack (LC 1146-style) is that `visit` here
   deliberately destroys forward history, where a general undo/redo system
   sometimes wants to preserve a "redo" branch even after a new action.
   This problem's spec is explicit that browsers do NOT preserve it.

Q: Could `visit` and truncation get expensive if the user navigates back
   deep into history and then visits repeatedly?
A: Each `del history[cursor+1:]` only ever discards entries that were
   themselves created by a PRIOR visit — summed across an entire session,
   total truncation work never exceeds total appends, so it's O(1)
   amortized over the whole session, not a per-call concern.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 1381 Design a Stack With Increment Operation — array-backed design, O(1) amortized ops
    LC 146  LRU Cache (topic 08)                     — another "two pointers/positions into a sequence" design
    LC 232  Implement Queue using Stacks             — two-stack modeling technique (cf. Approach 1 here)
    Topic 07 · Queue & Deque                         — array/deque-backed sequential-access structures generally
================================================================================
"""

import random
import time


class BrowserHistory:
    """Array + cursor index. See THE CORE IDEA above."""

    def __init__(self, homepage: str):
        self.history: list[str] = [homepage]
        self.cursor = 0

    def visit(self, url: str) -> None:
        del self.history[self.cursor + 1:]  # discard ALL forward history
        self.history.append(url)
        self.cursor += 1

    def back(self, steps: int) -> str:
        self.cursor = max(0, self.cursor - steps)
        return self.history[self.cursor]

    def forward(self, steps: int) -> str:
        self.cursor = min(len(self.history) - 1, self.cursor + steps)
        return self.history[self.cursor]


# ------------------------------------------------------------------------
# Alternatives / oracles.
# ------------------------------------------------------------------------
class BrowserHistoryTwoStacks:
    """Approach 1: back-stack + forward-stack, popped/pushed one page at a
    time. O(steps) per back/forward call. Used as a correctness oracle and
    for the benchmark."""

    def __init__(self, homepage: str):
        self.current = homepage
        self.back_stack: list[str] = []
        self.forward_stack: list[str] = []

    def visit(self, url: str) -> None:
        self.back_stack.append(self.current)
        self.current = url
        self.forward_stack.clear()

    def back(self, steps: int) -> str:
        while steps > 0 and self.back_stack:
            self.forward_stack.append(self.current)
            self.current = self.back_stack.pop()
            steps -= 1
        return self.current

    def forward(self, steps: int) -> str:
        while steps > 0 and self.forward_stack:
            self.back_stack.append(self.current)
            self.current = self.forward_stack.pop()
            steps -= 1
        return self.current


# ==============================================================================
# TESTS — run:  python 006_design_browser_history_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # Correctness: LeetCode's canonical example, cross-checked against the
    # two-stack alternative.
    # ------------------------------------------------------------------
    print("--- correctness: array+cursor vs two-stacks ---")
    def run_script(impl):
        impl.visit("google.com")
        impl.visit("facebook.com")
        impl.visit("youtube.com")
        out = [impl.back(1), impl.back(1), impl.forward(1)]
        impl.visit("linkedin.com")
        out += [impl.forward(2), impl.back(2), impl.back(7)]
        return out

    wants = ["facebook.com", "google.com", "facebook.com",
             "linkedin.com", "google.com", "leetcode.com"]
    impls = {
        "array+cursor": BrowserHistory("leetcode.com"),
        "two-stacks  ": BrowserHistoryTwoStacks("leetcode.com"),
    }
    for name, impl in impls.items():
        results = run_script(impl)
        ok = results == wants
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  results={results}")

    # ------------------------------------------------------------------
    # Boundary clamping with no visits at all.
    # ------------------------------------------------------------------
    print("\n--- clamping at the boundary, fresh instance ---")
    bh = BrowserHistory("a.com")
    ok = bh.back(100) == "a.com" and bh.forward(100) == "a.com"
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  back/forward beyond range clamp to the only page")

    # ------------------------------------------------------------------
    # visit() after back() must discard ALL forward pages, not just one.
    # ------------------------------------------------------------------
    print("\n--- visit() discards ALL forward history, not just one page ---")
    bh2 = BrowserHistory("h.com")
    for u in ("a.com", "b.com", "c.com", "d.com"):
        bh2.visit(u)
    bh2.back(3)  # cursor back at "a.com"
    bh2.visit("z.com")  # must wipe b.com, c.com, d.com entirely
    ok = bh2.history == ["h.com", "a.com", "z.com"]
    ok &= bh2.forward(5) == "z.com"  # nothing to go forward to
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  history={bh2.history}  forward(5) stays at z.com")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the two-stack oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check (2000 ops) ---")
    rng = random.Random(23)
    ours = BrowserHistory("start.com")
    oracle = BrowserHistoryTwoStacks("start.com")
    mismatch = False
    for i in range(2000):
        op = rng.choice(["visit", "back", "forward"])
        if op == "visit":
            url = f"page{rng.randint(0, 50)}.com"
            ours.visit(url)
            oracle.visit(url)
        else:
            steps = rng.randint(1, 10)
            r1 = getattr(ours, op)(steps)
            r2 = getattr(oracle, op)(steps)
            if r1 != r2:
                mismatch = True
    all_ok &= not mismatch
    print(f"{'PASS' if not mismatch else 'FAIL'}  2000 randomized ops, array+cursor matches two-stacks throughout")

    # ------------------------------------------------------------------
    # BENCHMARK — back(steps) with large steps: array+cursor O(1) vs
    # two-stacks O(steps). REAL measured numbers.
    # ------------------------------------------------------------------
    print("\n--- benchmark: back(steps) with steps=100, repeated N times ---")
    for n_calls in (500, 2000, 5000):
        fast = BrowserHistory("h.com")
        for i in range(200):
            fast.visit(f"p{i}.com")
        t0 = time.perf_counter()
        for _ in range(n_calls):
            fast.back(100)
            fast.forward(100)
        t1 = time.perf_counter()
        fast_ms = (t1 - t0) * 1000

        slow = BrowserHistoryTwoStacks("h.com")
        for i in range(200):
            slow.visit(f"p{i}.com")
        t0 = time.perf_counter()
        for _ in range(n_calls):
            slow.back(100)
            slow.forward(100)
        t1 = time.perf_counter()
        slow_ms = (t1 - t0) * 1000

        slowdown = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  n_calls={n_calls:>5}   array+cursor: {fast_ms:>8.2f}ms   two-stacks: {slow_ms:>8.2f}ms   {slowdown:>6.1f}x slower")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
