package main

import (
	"fmt"
	"math/rand"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 138 · Copy List with Random Pointer                [Medium]
https://leetcode.com/problems/copy-list-with-random-pointer/
================================================================================

THE CORE IDEA
--------------
The struct is `Node`, not `ListNode` — an extra `Random` pointer can point
ANYWHERE in the list, including forward to a node not yet copied. That
"forward reference" is the entire difficulty of this problem: you cannot
safely wire up copy.Random while walking .Next in order, because the
original node .Random points at might not have a copy yet.

Two ways to solve the ordering problem — both answer "what is the copy of
node X" in O(1):

    1. HASHMAP: old node -> new node, built in a first pass, then a second
       pass wires up .Next/.Random by looking up mapping[old.Random].
       O(n) time, O(n) EXTRA space (the map holds n entries).

    2. INTERLEAVE-AND-SPLIT (topic guide Part 9, LRU-adjacent pattern):
       splice a copy of each node directly AFTER its original in the SAME
       list. Now "the copy of X" is always reachable as X.Next — no map
       required. Fix .Random pointers using that property, then split the
       two lists apart. O(n) time, O(1) EXTRA space.

Both are O(n) time. The difference that matters is auxiliary SPACE, which
is the actual subject of the follow-up question — see the measured
comparison in the demo below.

WHY A NAIVE SINGLE-PASS APPROACH BREAKS
-----------------------------------------
It is tempting to write:

    copy := &Node{Val: node.Val}
    copy.Random = mapping[node.Random]   // look up RIGHT NOW, same pass

while walking .Next and creating copies as you go. This is broken: if
node.Random points to a node LATER in the list, that node hasn't been
copied yet, so mapping[node.Random] is a zero-value/missing entry — the
copy's Random ends up nil (or, in a from-scratch attempt with
`copy2 := &Node{Val: node.Val}` and a naive "walk again and set Random by
re-reading the ORIGINAL list", pointing back into the ORIGINAL list, not
the copy — a dangling reference across the two structures that violates
"none of the pointers in the new list should point to nodes in the
original list"). Whether the bug manifests as a nil random or a
cross-structure pointer, the root cause is the same: you cannot resolve
"the copy of a not-yet-visited node" without either (a) a completed map, or
(b) the interleave trick's structural guarantee. See the demo below, which
runs this exact broken version and prints a caught mismatch.


================================================================================
APPROACH 1 · Hashmap (old -> new)
================================================================================
    if head == nil { return nil }
    mapping := map[*Node]*Node{}
    for n := head; n != nil; n = n.Next {          // pass 1: create every copy, unwired
        mapping[n] = &Node{Val: n.Val}
    }
    for n := head; n != nil; n = n.Next {           // pass 2: wire Next and Random
        mapping[n].Next = mapping[n.Next]           // mapping[nil] == nil, comma-ok not needed
        mapping[n].Random = mapping[n.Random]
        n = n.Next
    }
    return mapping[head]

The map sidesteps the ordering problem directly: by the time pass 2 runs,
EVERY node already has a copy in the map, so mapping[n.Random] works
regardless of which direction Random points. In Go, indexing a nil map key
(mapping[nil]) returns the zero value (nil *Node) — this conveniently
handles "Random is nil" for free, same as Python's dict.get(None).

    Time O(n), Space O(n) — n map entries, each holding two pointers.


================================================================================
APPROACH 2 · Interleave-and-split ✅ (O(1) extra space — the answer to the
follow-up)
================================================================================
Three passes, each O(n), each doing one job:

STEP 1 — INTERLEAVE: for every original node X, splice a new copy X' directly
after it: X -> X' -> (X's old next) -> ... This is the key structural move:
after this step, "the copy of ANY node Y" is always Y.Next — no lookup
needed, because the copy is physically adjacent to the original.

STEP 2 — FIX RANDOM POINTERS ON THE COPIES: walk the interleaved list in
strides of 2 (always landing on an original). For each original X with a
copy X' = X.Next:
    X'.Random = X.Random.Next  (if X.Random != nil, else nil)
X.Random is the ORIGINAL node that X's random pointer targets; .Next on
that ORIGINAL node is exactly ITS copy, by construction from step 1. This is
the entire trick in one line.

STEP 3 — SPLIT: walk the interleaved list again, unweaving it back into two
separate lists — original nodes keep only their original .Next chain
(restoring the input, since the problem's contract implies the caller's
list should remain valid afterward), and copy nodes are chained together
into the new list.

    Time O(n) (three linear passes), Space O(1) extra (a few pointer
    variables; the O(n) new nodes are the required OUTPUT, not auxiliary
    space).


================================================================================
STEP BY STEP TRACE — interleave-and-split on a concrete list
================================================================================
Original list, 4 nodes, random pointers mixed forward/backward/self/nil:

    index:   0      1      2      3
    val:     A      B      C      D
    random:  ->C   ->A    ->C    ->nil
             (fwd)  (back) (self) (none)

    A --Next--> B --Next--> C --Next--> D --Next--> nil
    A.Random = C   B.Random = A   C.Random = C (self)   D.Random = nil

STEP 1 — INTERLEAVE (splice a raw copy after each original):

    A -> A' -> B -> B' -> C -> C' -> D -> D' -> nil
    (A'.Random, B'.Random, ... are all still nil/unset at this point)

    Every "copy of X" is now literally X.Next.

STEP 2 — FIX RANDOM ON THE COPIES (walk the originals, stride 2):

    A.Random = C    -> A'.Random = A.Random.Next = C.Next = C'
    B.Random = A    -> B'.Random = B.Random.Next = A.Next = A'
    C.Random = C    -> C'.Random = C.Random.Next = C.Next = C'  (self-loop
                                                                   mirrored)
    D.Random = nil  -> D'.Random = nil

    A -> A'(rand=C') -> B -> B'(rand=A') -> C -> C'(rand=C') -> D -> D'(rand=nil)

STEP 3 — SPLIT (unweave into original chain and copy chain):

    walk pairs (X, X'):
        X.Next  = X.Next.Next                          (skip the copy)
        X'.Next = X'.Next.Next  (if X'.Next != nil, else nil)  (skip the
                                  next original, chain copies together)

    original: A -> B -> C -> D -> nil     (unchanged from input — restored)
    copy:     A' -> B' -> C' -> D' -> nil
              random: A'->C'  B'->A'  C'->C' (self)  D'->nil

    The copy's random pointers exactly mirror the original's structure
    (forward, backward, self-loop, nil) — all four cases the topic guide
    flags as the ones to stress-test. The demo below builds exactly this
    list and runs both algorithms on it live.


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
    head == nil               -> return nil immediately. Both approaches must
                                  guard this before touching head.Val.
    single node, Random=nil   -> smallest real case; interleave produces
                                  exactly one pair (X, X'), split trivially.
    single node, Random=self  -> X.Random = X. After interleave, X.Next = X'.
                                  X'.Random = X.Random.Next = X.Next = X' —
                                  the copy also self-loops. Traced above
                                  (node C).
    Random points BACKWARD    -> the ordering problem this whole topic
                                  exists to solve (node B above, pointing
                                  back to A). A naive single-pass
                                  build-as-you-go approach fails here if A's
                                  copy isn't wired up before B needs to
                                  reference it — but interleave doesn't care
                                  about direction at all, since X.Random.Next
                                  is O(1) regardless of whether X.Random is
                                  earlier or later in the list.
    Random points FORWARD     -> the case that breaks naive single-pass
                                  copying outright (node A above, pointing
                                  to C, not yet visited in list order).
    All Randoms nil            -> degenerates to a plain deep copy of .Next
                                  only; both algorithms handle it with no
                                  special-casing.
    Duplicate values across nodes -> values are NOT unique identifiers; the
                                  test harness in this file recovers
                                  correctness via object IDENTITY (which
                                  physical node, via index position), never
                                  by comparing .Val, or it would silently
                                  accept a wrong wiring that happens to have
                                  matching values.


================================================================================
COMMON MISTAKES
================================================================================
1. Building copies and wiring .Random in the SAME single pass over .Next,
   assuming Random only ever points backward/already-visited. Breaks the
   instant Random points forward. See the "WHY A NAIVE SINGLE-PASS APPROACH
   BREAKS" note above and the demo, which reproduces this live.

2. Hashmap approach: forgetting that Go's map indexing on a missing key
   returns the ZERO VALUE, and instead writing code that assumes it must
   check `v, ok := mapping[key]` before using v — for *Node this is
   harmless (mapping[nilOrMissing] == nil already), but the confusion leads
   people to write more complex code than necessary, or to introduce a bug
   trying to "handle" the nil case that was already handled.

3. Interleave approach: performing step 3 (split) BEFORE step 2 (fix
   random). Once split, "the copy of X" is no longer X.Next — the whole
   trick depends on doing fix-random strictly between interleave and split.

4. Interleave approach: forgetting to guard `X'.Next = X'.Next.Next` when
   X'.Next is nil — the LAST copy's "next original" is nil, and
   nil.Next panics without the guard.

5. Comparing nodes by value instead of identity when writing test harnesses
   for this problem — duplicate values are legal and a value-based check
   can silently accept incorrectly-wired randoms (edge case above).

6. Not restoring the original list's .Next chain after the interleave
   trick — callers expect the ORIGINAL list to still be a valid,
   unmodified structure after the function returns, even though it was
   temporarily woven together with the copy mid-algorithm.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do it in O(1) extra space?
A: Yes — the interleave-and-split trick above. State the hashmap version
   first (simpler to reason about, easier to get right under pressure), then
   offer the interleave version as the space-optimal follow-up.

Q: Why does interleaving work — what specifically breaks if Random can
   point to ANY node, not just earlier ones?
A: The map-free trick works precisely BECAUSE it doesn't care about
   direction: "the copy of node Y" is defined structurally (Y.Next, once
   interleaved) rather than by traversal order, so forward/backward/self
   are all the same case. A naive single-pass approach without a map or
   interleave has no way to answer "what's the copy of a node I haven't
   reached yet" at all.

Q: What if the input could be very large (millions of nodes) — does the
   O(1)-space version actually matter?
A: Yes, concretely: the hashmap holds n entries of (old-node-pointer,
   new-node-pointer) pairs — real, measurable memory on top of the n copy
   nodes you must produce anyway. The interleave version's peak extra
   memory is a constant handful of pointer variables regardless of n. See
   the measured comparison in the demo below.

Q: What if the input could ALSO have a Prev/back pointer, forming a doubly
   linked list, in addition to Random?
A: Interleaving still works for the SAME reason: once interleaved, .Next
   still reaches "the copy of X" as X.Next, so Random and Prev are fixed up
   identically in step 2, orthogonal to each other.


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
                                                pointers, not values" idiom
                                                (topic guide Part 10)
================================================================================
*/

// copyRandomList is the answer to the follow-up: interleave-and-split.
// O(n) time, O(1) extra space.
func copyRandomList(head *Node) *Node {
	if head == nil {
		return nil
	}

	// Step 1: interleave — splice a raw copy after each original.
	for n := head; n != nil; {
		copy := &Node{Val: n.Val}
		copy.Next = n.Next
		n.Next = copy
		n = copy.Next
	}

	// Step 2: fix random pointers on the copies.
	for n := head; n != nil; {
		copy := n.Next
		if n.Random != nil {
			copy.Random = n.Random.Next
		}
		n = copy.Next
	}

	// Step 3: split back into original and copy lists.
	copyHead := head.Next
	for n := head; n != nil; {
		copy := n.Next
		n.Next = copy.Next
		if copy.Next != nil {
			copy.Next = copy.Next.Next
		}
		n = n.Next
	}

	return copyHead
}

// copyRandomListHashmap is a simpler O(n) time, O(n) EXTRA space approach:
// map old node -> new node, built in a first pass, wired up in a second.
func copyRandomListHashmap(head *Node) *Node {
	if head == nil {
		return nil
	}
	mapping := make(map[*Node]*Node, 16)
	for n := head; n != nil; n = n.Next {
		mapping[n] = &Node{Val: n.Val}
	}
	for n := head; n != nil; n = n.Next {
		mapping[n].Next = mapping[n.Next]     // mapping[nil] is the zero value: nil
		mapping[n].Random = mapping[n.Random] // same
	}
	return mapping[head]
}

// copyRandomListNaiveSinglePass is BROKEN ON PURPOSE — builds copies and
// wires .Random in a SINGLE pass over .Next, assuming Random never points
// forward. Silently produces wrong .Random links whenever Random points to
// a not-yet-copied node. See Common Mistakes #1.
func copyRandomListNaiveSinglePass(head *Node) *Node {
	if head == nil {
		return nil
	}
	oldToNew := make(map[*Node]*Node)
	dummy := &Node{}
	copyPrev := dummy
	for n := head; n != nil; n = n.Next {
		copy := &Node{Val: n.Val}
		oldToNew[n] = copy
		copyPrev.Next = copy
		copyPrev = copy
		// BUG: looks up oldToNew for n.Random RIGHT NOW, but if n.Random is
		// a node further along the list, it hasn't been copied yet —
		// map lookup silently returns nil instead of the real copy.
		copy.Random = oldToNew[n.Random]
	}
	return dummy.Next
}

// ---- test helpers -----------------------------------------------------

type pair struct {
	val    int
	random int // index, or -1 for nil
}

func buildFromPairs(pairs []pair) *Node {
	if len(pairs) == 0 {
		return nil
	}
	nodes := make([]*Node, len(pairs))
	for i, p := range pairs {
		nodes[i] = &Node{Val: p.val}
	}
	for i := 0; i < len(nodes)-1; i++ {
		nodes[i].Next = nodes[i+1]
	}
	for i, p := range pairs {
		if p.random != -1 {
			nodes[i].Random = nodes[p.random]
		}
	}
	return nodes[0]
}

func toPairs(head *Node) []pair {
	var nodes []*Node
	for n := head; n != nil; n = n.Next {
		nodes = append(nodes, n)
	}
	index := make(map[*Node]int, len(nodes))
	for i, n := range nodes {
		index[n] = i
	}
	out := make([]pair, len(nodes))
	for i, n := range nodes {
		r := -1
		if n.Random != nil {
			r = index[n.Random]
		}
		out[i] = pair{val: n.Val, random: r}
	}
	return out
}

func nextChain(head *Node) []int {
	var out []int
	for n := head; n != nil; n = n.Next {
		out = append(out, n.Val)
	}
	return out
}

func equalPairs(a, b []pair) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func equalInts(a, b []int) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func main() {
	cases := [][]pair{
		{{7, -1}, {13, 0}, {11, 4}, {10, 2}, {1, 0}},
		{{1, 1}, {2, 1}},
		{{3, -1}, {3, 0}, {3, -1}},
		{},
		{{5, 0}},                   // single node, self-loop random
		{{5, -1}},                  // single node, no random
		{{65, 2}, {12, 1}, {7, 0}}, // A->C forward, B->B self, C->A backward
	}

	allOK := true
	fmt.Println("--- correctness: interleave-split vs hashmap, against expected pairs ---")
	for _, pairs := range cases {
		h1 := buildFromPairs(pairs)
		got1 := toPairs(copyRandomList(h1))
		want := make([]pair, len(pairs))
		for i, p := range pairs {
			want[i] = p
		}
		origVals := make([]int, len(pairs))
		for i, p := range pairs {
			origVals[i] = p.val
		}
		origOK := equalInts(nextChain(h1), origVals)

		h2 := buildFromPairs(pairs)
		got2 := toPairs(copyRandomListHashmap(h2))

		ok := equalPairs(got1, want) && equalPairs(got2, want) && origOK
		allOK = allOK && ok
		fmt.Printf("%s  input=%v\n      interleave -> %v  (orig restored: %v)\n      hashmap    -> %v\n",
			status(ok), pairs, got1, origOK, got2)
	}

	// ------------------------------------------------------------------
	// Full step-by-step trace on the 4-node example from the prose.
	// ------------------------------------------------------------------
	fmt.Println("\n--- trace: 4 nodes A,B,C,D with forward/backward/self/nil random ---")
	// A(0)->C(2), B(1)->A(0), C(2)->C(2) self, D(3)->nil
	pairs := []pair{{'A', 2}, {'B', 0}, {'C', 2}, {'D', -1}}
	labels := []string{"A", "B", "C", "D"}
	head := buildFromPairs(pairs)
	randLabels := make([]string, len(pairs))
	for i, p := range pairs {
		if p.random == -1 {
			randLabels[i] = "nil"
		} else {
			randLabels[i] = labels[p.random]
		}
	}
	fmt.Printf("  original: %v  random -> %v\n", labels, randLabels)

	// Step 1: interleave, shown explicitly.
	for n := head; n != nil; {
		copy := &Node{Val: n.Val}
		copy.Next = n.Next
		n.Next = copy
		n = copy.Next
	}
	var chain []string
	for n := head; n != nil; n = n.Next {
		chain = append(chain, string(rune(n.Val)))
	}
	fmt.Printf("  interleaved chain values: %v  (each original followed by its copy)\n", chain)

	// Step 2: fix random on copies.
	for n := head; n != nil; {
		copy := n.Next
		if n.Random != nil {
			copy.Random = n.Random.Next
		}
		n = copy.Next
	}
	var trace [][2]string
	for n := head; n != nil; n = n.Next {
		r := "nil"
		if n.Random != nil {
			r = string(rune(n.Random.Val))
		}
		trace = append(trace, [2]string{string(rune(n.Val)), r})
	}
	fmt.Printf("  after STEP 2 fix-random: (val, random.val) pairs = %v\n", trace)

	// Step 3: split.
	copyHead := head.Next
	for n := head; n != nil; {
		copy := n.Next
		n.Next = copy.Next
		if copy.Next != nil {
			copy.Next = copy.Next.Next
		}
		n = n.Next
	}
	got := toPairs(copyHead)
	want := pairs
	step3OK := equalPairs(got, want)
	allOK = allOK && step3OK
	fmt.Printf("  after STEP 3 split: copy list = %v  (want %v)  ok=%v\n", got, want, step3OK)
	origRestored := equalInts(nextChain(head), []int{'A', 'B', 'C', 'D'})
	fmt.Printf("  original restored: %v\n", origRestored)
	allOK = allOK && origRestored

	// ------------------------------------------------------------------
	// Naive single-pass approach fails on FORWARD random pointers.
	// ------------------------------------------------------------------
	fmt.Println("\n--- naive single-pass build (no map-first, no interleave): breaks on forward random ---")
	naiveMismatch := false
	naiveCases := [][]pair{
		{{7, -1}, {13, 0}, {11, 4}, {10, 2}, {1, 0}},
		{{65, 2}, {12, 1}, {7, 0}},
	}
	for _, p := range naiveCases {
		good := toPairs(copyRandomList(buildFromPairs(p)))
		bad := toPairs(copyRandomListNaiveSinglePass(buildFromPairs(p)))
		mismatch := !equalPairs(good, bad)
		naiveMismatch = naiveMismatch || mismatch
		verdict := "yes"
		if !mismatch {
			verdict = "NO  <- expected a mismatch but naive matched"
		}
		fmt.Printf("  input=%v\n      correct -> %v\n      naive   -> %v\n      mismatch reproduced: %s\n",
			p, good, bad, verdict)
	}
	allOK = allOK && naiveMismatch

	// ------------------------------------------------------------------
	// Randomised cross-check: interleave vs hashmap on many random lists.
	// ------------------------------------------------------------------
	fmt.Println("\n--- randomised cross-check: interleave vs hashmap ---")
	rng := rand.New(rand.NewSource(42))
	trials, mismatches := 500, 0
	for t := 0; t < trials; t++ {
		n := rng.Intn(16)
		ps := make([]pair, n)
		for i := 0; i < n; i++ {
			r := -1
			if n > 0 {
				choice := rng.Intn(n + 1)
				if choice < n {
					r = choice
				}
			}
			ps[i] = pair{val: rng.Intn(201) - 100, random: r}
		}
		h1 := buildFromPairs(ps)
		h2 := buildFromPairs(ps)
		r1 := toPairs(copyRandomList(h1))
		r2 := toPairs(copyRandomListHashmap(h2))
		if !equalPairs(r1, r2) {
			mismatches++
		}
	}
	fmt.Printf("  %d random lists (0-15 nodes, random pointers incl. self/nil): %d mismatches\n", trials, mismatches)
	allOK = allOK && mismatches == 0

	// ------------------------------------------------------------------
	// Identity check: copies' Random pointers point into the COPY, never
	// back into the original — verified by pointer comparison.
	// ------------------------------------------------------------------
	fmt.Println("\n--- verifying copy.Random points into the COPY, not the original (identity) ---")
	origHead := buildFromPairs([]pair{{1, 1}, {2, 0}, {3, 1}})
	var origNodes []*Node
	for n := origHead; n != nil; n = n.Next {
		origNodes = append(origNodes, n)
	}
	origSet := make(map[*Node]bool, len(origNodes))
	for _, n := range origNodes {
		origSet[n] = true
	}
	copyH := copyRandomList(origHead)
	var copyNodes []*Node
	for n := copyH; n != nil; n = n.Next {
		copyNodes = append(copyNodes, n)
	}
	identityClean := true
	for i, cn := range copyNodes {
		if cn == origNodes[i] {
			identityClean = false // copy node is literally the original node
		}
		if cn.Random != nil && origSet[cn.Random] {
			identityClean = false // copy's Random dangles into the ORIGINAL list
		}
	}
	fmt.Printf("  copy nodes are distinct objects AND every copy.Random points only at\n")
	fmt.Printf("  other copy nodes (never at an original node): %v\n", identityClean)
	allOK = allOK && identityClean

	// ------------------------------------------------------------------
	// Measured runtime + space: interleave vs hashmap on larger lists.
	// ------------------------------------------------------------------
	fmt.Println("\n--- measured runtime: interleave vs hashmap ---")
	fmt.Printf("  %7s %14s %14s %8s\n", "n", "interleave", "hashmap", "ratio")
	rng2 := rand.New(rand.NewSource(0))
	for _, n := range []int{2_000, 8_000, 32_000} {
		ps := make([]pair, n)
		for i := 0; i < n; i++ {
			ps[i] = pair{val: i, random: rng2.Intn(n)}
		}
		h1 := buildFromPairs(ps)
		t0 := time.Now()
		copyRandomList(h1)
		t1 := time.Now()

		h2 := buildFromPairs(ps)
		t2 := time.Now()
		copyRandomListHashmap(h2)
		t3 := time.Now()

		ilMs := float64(t1.Sub(t0).Microseconds()) / 1000.0
		hmMs := float64(t3.Sub(t2).Microseconds()) / 1000.0
		ratio := 0.0
		if ilMs > 0 {
			ratio = hmMs / ilMs
		}
		fmt.Printf("  %7d %12.2fms %12.2fms %7.2fx\n", n, ilMs, hmMs, ratio)
	}
	fmt.Println("  The hashmap allocates n map entries of (old-ptr, new-ptr) on top of the")
	fmt.Println("  n required output nodes; interleave's extra state is a fixed handful of")
	fmt.Println("  pointer variables regardless of n — the O(1) vs O(n) space claim the")
	fmt.Println("  follow-up is testing for, independent of which one wins the wall clock.")

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}
