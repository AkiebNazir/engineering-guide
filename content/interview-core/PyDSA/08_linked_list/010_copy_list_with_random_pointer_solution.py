"""
================================================================================
SOLUTION · LeetCode 138 · Copy List with Random Pointer                [Medium]
https://leetcode.com/problems/copy-list-with-random-pointer/
================================================================================

THE CORE IDEA
--------------
Note the class is `Node`, not `ListNode` — an extra `random` pointer can point
ANYWHERE in the list, including forward to a node not yet copied. That
"forward reference" is the entire difficulty of this problem: you cannot
safely wire up `copy.random` while walking `.next` in order, because the
original node `X.random` points at might not have a copy yet.

Two ways to solve the ordering problem — both map "the copy of node X" in
O(1):

    1. HASHMAP: old node -> new node, built in a first pass, then a second
       pass wires up `.next`/`.random` by looking up `mapping[old.random]`.
       O(n) time, O(n) EXTRA space (the map holds n entries).

    2. INTERLEAVE-AND-SPLIT (topic guide §5, Part 5 pattern 5): splice a
       copy of each node directly AFTER its original in the SAME list. Now
       "the copy of X" is always reachable as `X.next` — no map required.
       Fix up `.random` pointers using that property, then split the two
       lists apart. O(n) time, O(1) EXTRA space.

Both are O(n) time. The difference that matters is auxiliary SPACE, which is
the actual subject of the follow-up question — see the measured comparison
below.


================================================================================
APPROACH 1 · Hashmap (old -> new)
================================================================================
    if not head:
        return None
    mapping = {}
    node = head
    while node:                          # pass 1: create every copy, unwired
        mapping[node] = Node(node.val)
        node = node.next
    node = head
    while node:                          # pass 2: wire .next and .random
        mapping[node].next = mapping.get(node.next)
        mapping[node].random = mapping.get(node.random)
        node = node.next
    return mapping[head]

The map sidesteps the ordering problem directly: by the time pass 2 runs,
EVERY node already has a copy in the map, so `mapping.get(node.random)`
works regardless of which direction `random` points. `mapping.get(None)`
returns `None`, which conveniently handles "random is null" for free.

Time O(n), Space O(n) — n dict entries, each holding two object references.


================================================================================
APPROACH 2 · Interleave-and-split ✅ (O(1) extra space — the answer to the
follow-up)
================================================================================
Three passes, each O(n), each doing one job:

STEP 1 — INTERLEAVE: for every original node X, splice a new copy X' directly
after it: `X -> X' -> (X's old next) -> ...`. This is the key structural
move: after this step, "the copy of ANY node Y" is always `Y.next` — no
lookup needed, because the copy is physically adjacent to the original.

STEP 2 — FIX RANDOM POINTERS ON THE COPIES: walk the interleaved list in
strides of 2 (always landing on an original). For each original X with a
copy X' = X.next:
    X'.random = X.random.next if X.random else None
`X.random` is the ORIGINAL node that X's random pointer targets; `.next` on
that ORIGINAL node is exactly ITS copy, by construction from step 1. This is
the entire trick in one line.

STEP 3 — SPLIT: walk the interleaved list again, unweaving it back into two
separate lists — original nodes keep only their original `.next` chain
(restoring the input, since the problem says do not mutate structurally
visible state beyond the copy — see edge cases), and copy nodes are chained
together into the new list.

Time O(n) (three linear passes), Space O(1) extra (a few pointer variables;
the O(n) new nodes are the required OUTPUT, not auxiliary space).


================================================================================
STEP BY STEP TRACE — interleave-and-split on a concrete list
================================================================================
Original list, 4 nodes, random pointers mixed forward/backward/self/None:

    index:   0      1      2      3
    val:     A      B      C      D
    random:  ->C   ->A    ->C    ->None
             (fwd)  (back) (self) (none)

    A ──next──► B ──next──► C ──next──► D ──next──► None
    │random             │random   │random
    └──────────────────►│         └──►│ (self)
    A.random = C          B.random = A   C.random = C   D.random = None

STEP 1 — INTERLEAVE (splice a raw copy after each original):

    A ─► A' ─► B ─► B' ─► C ─► C' ─► D ─► D' ─► None
    (A'.random, B'.random, ... are all still None/unset at this point)

    Every "copy of X" is now literally X.next.

STEP 2 — FIX RANDOM ON THE COPIES (walk the originals, stride 2):

    A.random = C   -> A'.random = A.random.next = C.next = C'
    B.random = A   -> B'.random = B.random.next = A.next = A'
    C.random = C   -> C'.random = C.random.next = C.next = C'   (copy points
                                                                   to itself,
                                                                   correctly
                                                                   mirroring
                                                                   the original
                                                                   self-loop)
    D.random = None -> D'.random = None

    A ─► A'(rand=C') ─► B ─► B'(rand=A') ─► C ─► C'(rand=C') ─► D ─► D'(rand=None)

STEP 3 — SPLIT (unweave into original chain and copy chain):

    walk pairs (X, X'):
        X.next    = X.next.next      (skip over the copy, restore original)
        X'.next   = X'.next.next if X'.next else None   (skip over the NEXT
                                                            original, chain
                                                            copies together)

    original: A ─► B ─► C ─► D ─► None      (unchanged from input — restored)
    copy:     A' ─► B' ─► C' ─► D' ─► None
              random: A'->C'  B'->A'  C'->C'(self)  D'->None

    The copy's random pointers exactly mirror the original's structure
    (forward, backward, self-loop, None) — all four cases the topic guide
    flags as the ones to stress-test, and all four are covered by this one
    example. The demo below builds exactly this list and runs both
    algorithms on it live.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time    Space (extra)   Mutates input?
    -----------------------  ------  ---------------  -----------------------------
    Hashmap (old -> new) ✅  O(n)    O(n)             no (builds new list; input
                                                          list's nodes/pointers
                                                          never touched)
    Interleave-and-split ✅  O(n)    O(1)             TEMPORARILY yes — the
                                                          original list is
                                                          physically interleaved
                                                          with copies mid-algorithm,
                                                          then fully RESTORED by
                                                          step 3. Final state:
                                                          original list unchanged.


================================================================================
EDGE CASES
================================================================================
    head = None              -> return None immediately. Both approaches must
                                 guard this before touching `head.val`.
    Single node, random=None -> smallest real case; interleave produces
                                 exactly one pair (X, X'), split trivially.
    Single node, random=self -> X.random = X. After interleave, X.next = X'.
                                 X'.random = X.random.next = X.next = X' —
                                 the copy also self-loops. Traced above (node C).
    random points BACKWARD    -> the ordering problem this whole topic exists
                                 to solve (node B above, pointing back to A).
                                 A naive single-pass build-as-you-go approach
                                 fails here if A's copy isn't wired up before
                                 B needs to reference it — but interleave
                                 doesn't care about direction at all, since
                                 X.random.next is O(1) regardless of whether
                                 X.random is earlier or later in the list.
    random points FORWARD      -> the case that breaks naive single-pass
                                 copying outright (node A above, pointing to
                                 C, not yet visited in list order).
    All randoms None            -> degenerates to a plain deep copy of .next
                                 only; both algorithms handle it with no
                                 special-casing.
    Duplicate values across nodes -> values are NOT unique identifiers; the
                                 test harness in this file must recover
                                 correctness via object IDENTITY (which
                                 physical node), never by comparing `.val`,
                                 or it would silently accept a wrong wiring
                                 that happens to have matching values.


================================================================================
COMMON MISTAKES
================================================================================
1. Building copies and wiring `.random` in the SAME single pass over
   `.next`, assuming `random` only ever points backward/already-visited.
   Breaks the instant `random` points forward (topic guide Part 8, mistake 6).

2. Hashmap approach: forgetting `mapping.get(...)` (which returns None for a
   missing/None key) and using `mapping[...]` instead — crashes with a
   KeyError the moment `node.next` or `node.random` is None, since None was
   never inserted as a map key.

3. Interleave approach: performing step 3 (split) BEFORE step 2 (fix random).
   Once split, "the copy of X" is no longer `X.next` — the whole trick
   depends on doing fix-random strictly between interleave and split.

4. Interleave approach: forgetting to guard `X'.next = X'.next.next if
   X'.next else None` in the split step — the LAST copy's "next original" is
   None, and `None.next` crashes without the guard.

5. Comparing nodes by value instead of identity when writing test harnesses
   for this problem — duplicate values are legal and a value-based check can
   silently accept incorrectly-wired randoms (edge case above).

6. Not restoring the original list's `.next` chain after the interleave
   trick — LeetCode's checker (and most real callers) expect the ORIGINAL
   list to still be a valid, unmodified structure after the function
   returns, even though it was temporarily woven together with the copy
   mid-algorithm.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do it in O(1) extra space?
A: Yes — the interleave-and-split trick above. State the hashmap version
   first (simpler to reason about, easier to get right under pressure), then
   offer the interleave version as the space-optimal follow-up.

Q: Why does interleaving work — what specifically breaks if random can point
   to ANY node, not just earlier ones?
A: The map-free trick works precisely BECAUSE it doesn't care about
   direction: "the copy of node Y" is defined structurally (Y.next, once
   interleaved) rather than by traversal order, so forward/backward/self are
   all the same case. A naive single-pass approach without a map or
   interleave has no way to answer "what's the copy of a node I haven't
   reached yet" at all.

Q: What if the list could be very large (millions of nodes) — does the
   O(1)-space version actually matter?
A: Yes, concretely: the hashmap holds n entries of (old-node-ref,
   new-node-ref) pairs — real, measurable memory on top of the n copy nodes
   you must produce anyway. The interleave version's peak extra memory is a
   constant handful of pointer variables regardless of n. See the measured
   estimate in the demo below.

Q: What if the input could ALSO have a `prev`/back pointer, forming a doubly
   linked list, in addition to `random`?
A: Interleaving still works for the SAME reason: once interleaved, `.next`
   still reaches "the copy of X" as `X.next`, so `random` and `prev` are
   fixed up identically in step 2, orthogonal to each other.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 133  Clone Graph                     — same "map every node before
                                                wiring any edge" ordering
                                                problem, generalized to a
                                                graph (no interleave trick;
                                                arbitrary graphs have no
                                                linear structure to exploit)
    LC 1490 Clone N-ary Tree                — same shape, tree instead of
                                                list/graph
    LC 146  LRU Cache                       — different problem, but the
                                                SAME "map holds node
                                                references, not values" idiom
                                                (topic guide Part 6)
================================================================================
"""

import random as pyrandom
import sys
import time
from typing import Optional


class Node:
    def __init__(self, x: int, next: "Optional[Node]" = None, random: "Optional[Node]" = None):
        self.val = int(x)
        self.next = next
        self.random = random


class Solution:
    def copyRandomList(self, head: "Optional[Node]") -> "Optional[Node]":
        """Interleave-and-split. O(n) time, O(1) extra space. The answer to
        the follow-up. See THE CORE IDEA / Approach 2 above."""
        if not head:
            return None

        # Step 1: interleave — splice a raw copy after each original.
        node = head
        while node:
            copy = Node(node.val)
            copy.next = node.next
            node.next = copy
            node = copy.next

        # Step 2: fix random pointers on the copies.
        node = head
        while node:
            copy = node.next
            copy.random = node.random.next if node.random else None
            node = copy.next

        # Step 3: split back into original and copy lists.
        node = head
        copy_head = head.next
        while node:
            copy = node.next
            node.next = copy.next
            copy.next = copy.next.next if copy.next else None
            node = node.next

        return copy_head

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def copyRandomList_hashmap(self, head: "Optional[Node]") -> "Optional[Node]":
        """Hashmap old-node -> new-node. O(n) time, O(n) EXTRA space.
        Simpler to write correctly under pressure; state this first."""
        if not head:
            return None
        mapping = {}
        node = head
        while node:
            mapping[node] = Node(node.val)
            node = node.next
        node = head
        while node:
            mapping[node].next = mapping.get(node.next)
            mapping[node].random = mapping.get(node.random)
            node = node.next
        return mapping[head]

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def copyRandomList_naive_single_pass(self, head: "Optional[Node]") -> "Optional[Node]":
        """✗ BROKEN ON PURPOSE — builds copies and wires .random in a SINGLE
        pass over .next, assuming random never points forward. Silently
        produces wrong .random links (pointing at ORIGINAL nodes, or None)
        whenever random points to a not-yet-copied node. See mistake #1."""
        if not head:
            return None
        old_to_new = {}
        dummy = Node(0)
        copy_prev = dummy
        node = head
        while node:
            copy = Node(node.val)
            old_to_new[node] = copy
            copy_prev.next = copy
            copy_prev = copy
            # BUG: looks up old_to_new for node.random RIGHT NOW, but if
            # node.random is a node further along the list, it hasn't been
            # copied yet — old_to_new.get() silently returns None instead
            # of the real copy.
            copy.random = old_to_new.get(node.random)
            node = node.next
        return dummy.next


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build(pairs):
    if not pairs:
        return None
    nodes = [Node(v) for v, _ in pairs]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    for node, (_, ridx) in zip(nodes, pairs):
        node.random = nodes[ridx] if ridx is not None else None
    return nodes[0]


def to_pairs(head):
    nodes = []
    node = head
    while node:
        nodes.append(node)
        node = node.next
    index_of = {id(n): i for i, n in enumerate(nodes)}
    return [(n.val, index_of[id(n.random)] if n.random else None) for n in nodes]


def next_chain(head):
    out = []
    node = head
    while node:
        out.append(node.val)
        node = node.next
    return out


CASES = [
    [(7, None), (13, 0), (11, 4), (10, 2), (1, 0)],
    [(1, 1), (2, 1)],
    [(3, None), (3, 0), (3, None)],
    [],
    [(5, 0)],                    # single node, self-loop random
    [(5, None)],                 # single node, no random
    [(65, 2), (12, 1), (7, 0)],  # A->C forward, B->B self, C->A backward
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: interleave-split vs hashmap, against expected pairs ---")
    for pairs in CASES:
        h1 = build(pairs)
        got1 = to_pairs(sol.copyRandomList(h1))
        # original list must be UNMODIFIED after the interleave trick
        orig_ok = next_chain(h1) == [v for v, _ in pairs]

        h2 = build(pairs)
        got2 = to_pairs(sol.copyRandomList_hashmap(h2))

        ok = got1 == pairs and got2 == pairs and orig_ok
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  input={pairs!r}\n"
              f"      interleave -> {got1}  (orig restored: {orig_ok})\n"
              f"      hashmap    -> {got2}")

    # ----------------------------------------------------------------------
    # Full step-by-step trace on the 4-node example from the prose.
    # ----------------------------------------------------------------------
    print("\n--- trace: 4 nodes A,B,C,D with forward/backward/self/None random ---")
    # A(0)->C(2), B(1)->A(0), C(2)->C(2) self, D(3)->None
    pairs = [(ord('A'), 2), (ord('B'), 0), (ord('C'), 2), (ord('D'), None)]
    labels = ['A', 'B', 'C', 'D']
    head = build(pairs)
    print(f"  original: {[labels[i] for i in range(4)]}  "
          f"random -> {[labels[r] if r is not None else None for _, r in pairs]}")

    # Step 1: interleave, shown explicitly.
    node = head
    while node:
        copy = Node(node.val)
        copy.next = node.next
        node.next = copy
        node = copy.next
    chain = []
    n = head
    while n:
        chain.append(chr(n.val))
        n = n.next
    print(f"  interleaved chain values: {chain}  (each original followed by its copy)")

    # Step 2: fix random on copies.
    node = head
    while node:
        copy = node.next
        copy.random = node.random.next if node.random else None
        node = copy.next
    n = head
    trace = []
    while n:
        r = chr(n.random.val) if n.random else None
        trace.append((chr(n.val), r))
        n = n.next
    print(f"  after STEP 2 fix-random: (val, random.val) pairs = {trace}")

    # Step 3: split.
    node = head
    copy_head = head.next
    while node:
        copy = node.next
        node.next = copy.next
        copy.next = copy.next.next if copy.next else None
        node = node.next
    got = to_pairs(copy_head)
    expected = pairs
    step3_ok = got == expected
    all_ok &= step3_ok
    print(f"  after STEP 3 split: copy list = {got}  (want {expected})  ok={step3_ok}")
    print(f"  original restored: {next_chain(head) == [ord(l) for l in labels]}")

    # ----------------------------------------------------------------------
    # ⚠️ Naive single-pass approach fails on FORWARD random pointers.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ naive single-pass build (no map-first, no interleave): "
          "breaks on forward random ---")
    print(f"  {'input':<45} {'correct':<35} {'naive':<35} ok?")
    naive_mismatch = False
    for pairs in ([(7, None), (13, 0), (11, 4), (10, 2), (1, 0)],
                   [(65, 2), (12, 1), (7, 0)]):
        good = to_pairs(sol.copyRandomList(build(pairs)))
        bad = to_pairs(sol.copyRandomList_naive_single_pass(build(pairs)))
        mismatch = good != bad
        naive_mismatch |= mismatch
        print(f"  {str(pairs):<45} {str(good):<35} {str(bad):<35} "
              f"{'yes' if not mismatch else 'NO  <- forward random silently dropped to None'}")
    print(f"  naive single-pass bug reproduced: {naive_mismatch}")
    all_ok &= naive_mismatch

    # ----------------------------------------------------------------------
    # Randomised cross-check: interleave vs hashmap on many random lists.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check: interleave vs hashmap ---")
    pyrandom.seed(42)
    trials, mismatches = 500, 0
    for _ in range(trials):
        n = pyrandom.randint(0, 15)
        vals = [pyrandom.randint(-100, 100) for _ in range(n)]
        randoms = [pyrandom.choice(list(range(n)) + [None]) if n else None for _ in range(n)]
        pairs = list(zip(vals, randoms))
        h1 = build(pairs)
        h2 = build(pairs)
        r1 = to_pairs(sol.copyRandomList(h1))
        r2 = to_pairs(sol.copyRandomList_hashmap(h2))
        if r1 != r2:
            mismatches += 1
    print(f"  {trials} random lists (0-15 nodes, random pointers incl. self/None): "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Measured space comparison: hashmap O(n) extra vs interleave O(1) extra.
    # ----------------------------------------------------------------------
    print("\n--- measured auxiliary space: hashmap dict vs interleave pointers ---")
    for n in (1_000, 5_000, 20_000):
        vals = list(range(n))
        randoms = [pyrandom.randrange(n) for _ in range(n)]
        pairs = list(zip(vals, randoms))
        head = build(pairs)

        # Measure the actual dict the hashmap approach builds (old->new).
        mapping = {}
        node = head
        while node:
            mapping[node] = Node(node.val)
            node = node.next
        map_bytes = sys.getsizeof(mapping)
        # Each dict entry also costs the two references it stores, but the
        # underlying Node objects themselves are required OUTPUT either way
        # (both approaches must allocate n copy nodes) — the dict's own
        # table (sys.getsizeof(mapping)) is the EXTRA structure the hashmap
        # approach pays for that the interleave approach does not.

        interleave_extra_vars = 3  # node, copy, copy_head -- a fixed handful
        interleave_bytes = sys.getsizeof(None) * interleave_extra_vars  # order-of-magnitude stand-in

        print(f"  n={n:>6}   hashmap dict table: {map_bytes:>8} bytes   "
              f"interleave extra vars: ~{interleave_bytes} bytes (O(1), does not grow with n)")

    # ----------------------------------------------------------------------
    # Measured runtime: interleave vs hashmap on larger lists.
    # ----------------------------------------------------------------------
    print("\n--- measured runtime: interleave vs hashmap ---")
    print(f"  {'n':>7} {'interleave':>14} {'hashmap':>14} {'ratio':>8}")
    pyrandom.seed(0)
    for n in (2_000, 8_000, 32_000):
        vals = list(range(n))
        randoms = [pyrandom.randrange(n) for _ in range(n)]
        pairs = list(zip(vals, randoms))

        h1 = build(pairs)
        t0 = time.perf_counter()
        sol.copyRandomList(h1)
        t1 = time.perf_counter()

        h2 = build(pairs)
        t2 = time.perf_counter()
        sol.copyRandomList_hashmap(h2)
        t3 = time.perf_counter()

        il_ms = (t1 - t0) * 1000
        hm_ms = (t3 - t2) * 1000
        ratio = hm_ms / il_ms if il_ms > 0 else float("inf")
        print(f"  {n:>7} {il_ms:>12.2f}ms {hm_ms:>12.2f}ms {ratio:>7.2f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
