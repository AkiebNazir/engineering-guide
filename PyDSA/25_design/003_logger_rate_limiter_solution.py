"""
================================================================================
SOLUTION · LeetCode 359 · Logger Rate Limiter                             [Easy]
https://leetcode.com/problems/logger-rate-limiter/
================================================================================

THE CORE IDEA
--------------
One hashmap, `message -> next_allowed_timestamp`. Storing the NEXT allowed
time (not the last-printed time) turns every check into a single
comparison (`timestamp >= next_allowed`) instead of a comparison plus an
addition per check. Because timestamps arrive non-decreasing, the map
never needs active eviction for correctness — a stale entry just compares
`True` against any later timestamp naturally.


================================================================================
APPROACH 1 · Store every printed (message, timestamp) in a list (brute
force, priced, not coded)
================================================================================
Keep a list of all `(message, timestamp)` pairs ever printed; on each call,
scan the list for the same message and check whether the most recent print
is `< 10` seconds ago.

    Time: O(n) per call, n = number of prior prints. Space: O(n) — grows
    unboundedly, one entry per PRINT, not per distinct message.

This is what naive logging without a dedicated per-message index costs;
the O(1) dict below makes the scan and the unbounded growth unnecessary
simultaneously.


================================================================================
APPROACH 2 · dict[message] -> next_allowed_timestamp ✅ (the answer)
================================================================================
    class Logger:
        def __init__(self):
            self.next_allowed = {}   # message -> earliest timestamp it may print again

        def shouldPrintMessage(self, timestamp, message):
            if timestamp < self.next_allowed.get(message, timestamp):
                return False
            self.next_allowed[message] = timestamp + 10
            return True

`self.next_allowed.get(message, timestamp)` is the key trick: for a
NEVER-SEEN message, the default returned is `timestamp` itself, so
`timestamp < timestamp` is False — the message is allowed immediately,
with zero special-casing for "first time seen."

    Time: O(1) average per call.     Space: O(distinct messages ever seen).


================================================================================
VARIANT · Active eviction with a min-heap of (next_allowed, message)
================================================================================
If the interviewer pushes on "the dict grows forever, can you bound
memory?" — since timestamps are non-decreasing, maintain a min-heap keyed
by `next_allowed_timestamp` alongside the dict. Before each check, pop and
delete from the dict every heap entry whose `next_allowed <= timestamp`
(it's now globally stale AND, since time only moves forward, will never
become relevant again as "still suppressing" — though the dict entry
itself, if the message reappears, gets naturally overwritten anyway).

This trades O(1) per call for O(log n) per call (heap push/pop) in
exchange for bounding memory to "messages active within roughly the last
10 seconds" instead of "every distinct message ever seen." Whether that
trade is worth it is a real interview follow-up (see below) — not coded
as the primary answer because the base problem's constraints (at most
10^4 calls total) never make unbounded dict growth an actual problem.


================================================================================
STEP BY STEP TRACE
================================================================================
    shouldPrintMessage(1, "foo")
        next_allowed.get("foo", 1) = 1  (not seen -> default is timestamp itself)
        1 < 1 is False -> ALLOW. next_allowed["foo"] = 1 + 10 = 11

    shouldPrintMessage(2, "bar")
        next_allowed.get("bar", 2) = 2 (not seen)
        2 < 2 is False -> ALLOW. next_allowed["bar"] = 12

    shouldPrintMessage(3, "foo")
        next_allowed.get("foo", 3) = 11 (seen, stored value wins over default)
        3 < 11 is True -> SUPPRESS. map unchanged.

    shouldPrintMessage(8, "bar")
        next_allowed.get("bar", 8) = 12
        8 < 12 is True -> SUPPRESS.

    shouldPrintMessage(10, "foo")
        next_allowed.get("foo", 10) = 11
        10 < 11 is True -> SUPPRESS.

    shouldPrintMessage(11, "foo")
        next_allowed.get("foo", 11) = 11
        11 < 11 is False -> ALLOW. next_allowed["foo"] = 11 + 10 = 21

    Map state after all six calls:   {"foo": 21, "bar": 12}


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time (per call)   Space              Mutates input?
    ---------------------------------  ----------------  -----------------  ---------------
    List of all past prints (brute)   O(n)              O(n), unbounded    n/a — design problem
    dict[message] -> next_allowed ✅  O(1) average       O(distinct msgs)  n/a — design problem
    dict + min-heap eviction          O(log n)          O(active msgs)     n/a — design problem


================================================================================
EDGE CASES
================================================================================
    Message never seen before          Must be allowed immediately — the
                                        `.get(message, timestamp)` default
                                        handles this without an `if
                                        message not in dict` branch.
    Exactly `timestamp == next_allowed`  Must be ALLOWED (the boundary is
                                        inclusive: "at most once every 10
                                        seconds" means exactly 10 seconds
                                        later is fine), not suppressed —
                                        an off-by-one that `<` vs `<=`
                                        flips easily.
    Two different messages at the
      SAME timestamp                   Independent — both allowed, since
                                        the map is keyed per-message.
    Same message, same timestamp,
      called twice in a row            Second call must be suppressed
                                        (the first call already advanced
                                        `next_allowed` past this timestamp).
    timestamp == 0                     Valid per constraints; must not be
                                        treated as "no timestamp given."


================================================================================
COMMON MISTAKES
================================================================================
1. Storing `last_printed_timestamp` and computing `timestamp -
   last_printed < 10` inline — functionally equivalent but couples the
   comparison to an addition/subtraction on every single call instead of
   once (on write only); also easy to get the inequality direction wrong
   when refactored under pressure.

2. Using `<=` instead of `<` in the suppress check (or equivalently
   getting the ALLOW boundary backwards) — the problem is explicit that
   exactly `t + 10` must be ALLOWED, not suppressed; this is the single
   most common off-by-one in this problem.

3. `if message not in self.next_allowed: return True` as a separate
   branch, THEN forgetting to also write `next_allowed[message] =
   timestamp + 10` in that branch — the dict-default trick (`.get(...,
   timestamp)`) avoids this whole class of bug by not needing a separate
   branch at all.

4. Assuming timestamps are UNIQUE per call — they are not; multiple
   messages (or the same message from different callers) can share a
   timestamp, and non-decreasing does not mean strictly increasing.

5. Trying to actively evict "old" entries for a problem whose constraints
   (`<= 10^4` total calls) never make an unbounded dict a real issue —
   solving a problem the interviewer didn't ask, at the cost of code
   complexity, unless they explicitly raise memory as a follow-up.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if timestamps could arrive OUT OF ORDER (not guaranteed
   non-decreasing)?
A: The `next_allowed` dict trick still works for the ALLOW/SUPPRESS
   decision at each call in isolation, but "next_allowed = timestamp + 10"
   could then move BACKWARDS if a later call has an earlier timestamp than
   a previous one for the same message — you'd need `next_allowed[message]
   = max(next_allowed.get(message, timestamp), timestamp) + 10`-style
   reasoning, or reject out-of-order calls as invalid input, depending on
   the intended semantics.

Q: How would you bound memory if messages are unbounded and mostly never
   repeat?
A: The min-heap eviction variant above — periodically purge entries whose
   `next_allowed` has passed, at the cost of O(log n) instead of O(1) per
   call. Whether it's worth it depends on whether distinct-message count
   is actually unbounded in practice.

Q: How would this change for a DISTRIBUTED logging system (multiple
   servers sharing rate limits)?
A: The single in-process dict becomes a shared store (e.g. Redis) with
   `SET message next_allowed EX 10 NX`-style atomic check-and-set to avoid
   race conditions between servers checking and updating the same message
   concurrently — the core "next allowed time" idea is unchanged, only the
   storage and atomicity guarantees move to a shared system.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 981  Time Based Key-Value Store       — dict of message -> sorted (timestamp, value) list
    LC 1146 Snapshot Array                   — versioned per-index history, same "time" axis idea
    Topic 01 · Arrays & Hashing              — the underlying "hashmap as a small state machine" pattern
================================================================================
"""

import heapq
import random


class Logger:
    """dict[message] -> next_allowed_timestamp. See THE CORE IDEA above."""

    def __init__(self):
        self.next_allowed: dict[str, int] = {}

    def shouldPrintMessage(self, timestamp: int, message: str) -> bool:
        if timestamp < self.next_allowed.get(message, timestamp):
            return False
        self.next_allowed[message] = timestamp + 10
        return True


# ------------------------------------------------------------------------
# Alternatives / oracles.
# ------------------------------------------------------------------------
class LoggerBruteForce:
    """Approach 1: scan every past print for this message. O(n) per call,
    unbounded space (one entry per PRINT). Used as a correctness oracle."""

    def __init__(self):
        self.history: list[tuple[str, int]] = []  # (message, timestamp) of every allowed print

    def shouldPrintMessage(self, timestamp: int, message: str) -> bool:
        last = None
        for m, t in self.history:
            if m == message:
                last = t  # history is append-ordered by non-decreasing timestamp
        if last is not None and timestamp < last + 10:
            return False
        self.history.append((message, timestamp))
        return True


class LoggerHeapEviction:
    """Variant: dict + min-heap, actively evicting entries whose
    next_allowed has passed so the dict doesn't hold every message ever
    seen forever. O(log n) per call instead of O(1)."""

    def __init__(self):
        self.next_allowed: dict[str, int] = {}
        self.heap: list[tuple[int, str]] = []  # (next_allowed, message)

    def _evict_stale(self, timestamp: int) -> None:
        while self.heap and self.heap[0][0] <= timestamp:
            expiry, message = heapq.heappop(self.heap)
            # Only delete if this heap entry is still the message's CURRENT
            # expiry (it may have been re-pushed with a newer expiry since).
            if self.next_allowed.get(message) == expiry:
                del self.next_allowed[message]

    def shouldPrintMessage(self, timestamp: int, message: str) -> bool:
        self._evict_stale(timestamp)
        if timestamp < self.next_allowed.get(message, timestamp):
            return False
        expiry = timestamp + 10
        self.next_allowed[message] = expiry
        heapq.heappush(self.heap, (expiry, message))
        return True


# ==============================================================================
# TESTS — run:  python 003_logger_rate_limiter_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # Correctness: LeetCode's canonical example, cross-checked against
    # both alternates.
    # ------------------------------------------------------------------
    print("--- correctness: dict vs brute-force vs heap-eviction ---")
    script = [
        (1, "foo", True), (2, "bar", True), (3, "foo", False),
        (8, "bar", False), (10, "foo", False), (11, "foo", True),
    ]
    impls = {
        "dict          ": Logger(),
        "brute-force   ": LoggerBruteForce(),
        "heap-eviction ": LoggerHeapEviction(),
    }
    for name, impl in impls.items():
        results = [impl.shouldPrintMessage(t, m) for t, m, _ in script]
        wants = [w for _, _, w in script]
        ok = results == wants
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  results={results}  (want {wants})")

    # ------------------------------------------------------------------
    # Boundary: exactly timestamp == next_allowed must ALLOW, not suppress.
    # ------------------------------------------------------------------
    print("\n--- boundary: t == next_allowed is ALLOWED (inclusive) ---")
    lg = Logger()
    lg.shouldPrintMessage(0, "x")           # next_allowed["x"] = 10
    ok = lg.shouldPrintMessage(9, "x") is False
    ok &= lg.shouldPrintMessage(10, "x") is True  # exactly at boundary
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  t=9 suppressed, t=10 (exact boundary) allowed")

    # ------------------------------------------------------------------
    # Different messages at the same timestamp are independent.
    # ------------------------------------------------------------------
    print("\n--- independent messages ---")
    lg2 = Logger()
    ok = lg2.shouldPrintMessage(5, "a") is True and lg2.shouldPrintMessage(5, "b") is True
    ok &= lg2.shouldPrintMessage(5, "a") is False  # same message, same timestamp again
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  distinct messages independent; repeat same-timestamp call suppressed")

    # ------------------------------------------------------------------
    # Randomized cross-check vs brute force on a non-decreasing timestamp
    # stream (matches the problem's guarantee).
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check (1500 calls, non-decreasing timestamps) ---")
    rng = random.Random(9)
    ours = Logger()
    oracle = LoggerBruteForce()
    heap_impl = LoggerHeapEviction()
    t = 0
    mismatch = False
    messages = [f"msg{i}" for i in range(15)]
    for _ in range(1500):
        t += rng.randint(0, 3)  # non-decreasing
        msg = rng.choice(messages)
        r1 = ours.shouldPrintMessage(t, msg)
        r2 = oracle.shouldPrintMessage(t, msg)
        r3 = heap_impl.shouldPrintMessage(t, msg)
        if not (r1 == r2 == r3):
            mismatch = True
    all_ok &= not mismatch
    print(f"{'PASS' if not mismatch else 'FAIL'}  1500 calls, dict/brute/heap all agree")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
