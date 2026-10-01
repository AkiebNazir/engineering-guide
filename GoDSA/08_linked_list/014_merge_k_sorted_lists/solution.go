package main

import (
	"container/heap"
	"fmt"
	"math/rand"
	"sort"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 23 · Merge k Sorted Lists                            [Hard]
https://leetcode.com/problems/merge-k-sorted-lists/
================================================================================

THE CORE IDEA
--------------
Merging TWO sorted lists (LC 21, this topic's dummy-head + two-pointer
merge) is the atomic operation. Merging k lists is entirely about HOW you
pick "the smallest of the k current heads" efficiently, over and over, N
times total. Four ways to answer that, in increasing sophistication:

    1. Dump every value into a slice, sort it, rebuild — ignores the fact
       the inputs are ALREADY sorted, pure brute force.
    2. Sequential pairwise fold — merge list 0 into an accumulator, then
       list 1, then list 2, ... — correct, but the accumulator grows, so
       the k-th merge costs O(total nodes so far), giving O(N*k) overall.
    3. Min-heap of k candidates ("the smallest of k current heads" is
       LITERALLY what a heap answers in O(log k)) — pop the min, push its
       successor, repeat N times: O(N log k).
    4. Divide-and-conquer pairwise merging — merge lists in pairs, halving
       the list count each round; O(log k) rounds, O(N) work per round:
       O(N log k), same bound as the heap, no heap needed.

Approaches 3 and 4 share the same asymptotic bound; the demo below measures
which one actually wins on this machine and by how much.


================================================================================
APPROACH 1 · Collect all values, sort, rebuild (brute force, priced not coded
as the "answer" — coded here as an oracle for cross-checking, never call it
the solution in an interview without naming its trade-off first)
================================================================================
    Time:  O(N log N)     Space: O(N) — ignores that inputs are pre-sorted


================================================================================
APPROACH 2 · Sequential pairwise merge (baseline, priced)
================================================================================
Fold mergeTwoLists over the k lists: acc = merge(acc, lists[0]),
acc = merge(acc, lists[1]), .... Each merge of the growing accumulator
against list i costs O(len(acc) + len(lists[i])); summed across k lists this
is O(N*k) in the worst case (imagine k lists of near-equal size — the
accumulator grows roughly linearly with each fold).

    Time:  O(N*k)     Space: O(1) extra (beyond output)


================================================================================
APPROACH 3 · Min-heap of k candidates ✅ (O(N log k) — a standard answer)
================================================================================
Push the head of every non-empty list into a min-heap keyed by Val (k
entries). Repeat N times: pop the minimum, append it to the output, and if
that node had a Next, push the Next. container/heap requires implementing
heap.Interface (Len/Less/Swap/Push/Pop) over a slice of *ListNode.

    Time:  O(N log k)     Space: O(k) for the heap


================================================================================
APPROACH 4 · Divide-and-conquer pairwise merge ✅ (O(N log k) — no heap)
================================================================================
Merge lists[0] with lists[1], lists[2] with lists[3], ..., producing k/2
lists; repeat on the result until one list remains. Each round does O(N)
total work across all its merges (every node is touched exactly once per
round), and halving k takes log2(k) rounds.

    Time:  O(N log k)     Space: O(log k) recursion stack (or O(k) if done
                            iteratively with an explicit queue)


================================================================================
STEP BY STEP — lists = [[1,4,5], [1,3,4], [2,6]]  (heap approach)
================================================================================
    Initial heap (min-heap by Val), one node per non-empty list:
        heap: [1(list0), 1(list1), 2(list2)]

    pop 1(list0) -> output=[1]; push list0's next, 4(list0)
        heap: [1(list1), 2(list2), 4(list0)]
    pop 1(list1) -> output=[1,1]; push list1's next, 3(list1)
        heap: [2(list2), 3(list1), 4(list0)]
    pop 2(list2) -> output=[1,1,2]; push list2's next, 6(list2)
        heap: [3(list1), 4(list0), 6(list2)]
    pop 3(list1) -> output=[1,1,2,3]; push list1's next, 4(list1)
        heap: [4(list0), 4(list1), 6(list2)]
    pop 4(list0) -> output=[1,1,2,3,4]; list0 exhausted, nothing pushed
        heap: [4(list1), 6(list2)]
    pop 4(list1) -> output=[1,1,2,3,4,4]; list1 exhausted, nothing pushed
        heap: [6(list2)]
    pop 5? -- wait, list0's remaining node 5 was never pushed since list0
        was already exhausted after popping 4(list0). Re-trace: list0 =
        [1,4,5], so after popping 1 we push 4, after popping 4 we push 5
        (list0 is NOT exhausted until 5 is popped too).
        heap after popping 4(list0): [4(list1), 5(list0), 6(list2)]
    pop 4(list1) -> output=[1,1,2,3,4,4]; list1 exhausted
        heap: [5(list0), 6(list2)]
    pop 5(list0) -> output=[1,1,2,3,4,4,5]; list0 now exhausted
        heap: [6(list2)]
    pop 6(list2) -> output=[1,1,2,3,4,4,5,6]; list2 exhausted
        heap: []
    result: 1 -> 1 -> 2 -> 3 -> 4 -> 4 -> 5 -> 6 -> nil

    (The corrected trace above matches the code and the runtime demo's
    printed trace below — this file's demo prints the REAL trace live so
    there is no ambiguity.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time        Space        Mutates input?
    ------------------------------  ----------  -----------  -----------------
    Collect+sort, rebuild            O(N log N)  O(N)         no
    Sequential pairwise merge        O(N*k)      O(1) extra   yes (reuses nodes)
    Min-heap of k candidates ✅      O(N log k)  O(k)         yes (reuses nodes)
    Divide-and-conquer merge ✅      O(N log k)  O(log k)     yes (reuses nodes)

"Mutates input?" here means: the algorithms all reuse and relink the
EXISTING ListNode structs from the input lists (no new nodes allocated) —
so the k original list HEADS passed in are no longer valid standalone
lists after merging; their nodes have been spliced into the single output
chain. This mirrors LC 21's own contract and is standard for this family.


================================================================================
EDGE CASES
================================================================================
    lists == nil or empty slice   -> return nil immediately, nothing to merge.
    lists == [nil]                -> a slice containing one nil list -> nil.
    Some lists nil, some non-nil  -> skip nil lists when seeding the heap /
                                      pairwise merge; do not push nil into
                                      the heap (Val on a nil pointer panics).
    All lists empty                -> same as above, result is nil.
    k == 1                          -> heap/divide-and-conquer degrade to a
                                      single pass, still correct (heap of
                                      size 1 always pops that one list; D&C's
                                      single round is trivial).
    Lists of wildly different lengths -> stresses the heap approach's
                                      re-fill logic (a short list is
                                      exhausted early, its heap slot must
                                      not be re-populated).
    Duplicate values across different lists -> heap tie-breaking must still
                                      produce a valid overall sort (any tie
                                      order is acceptable since merge output
                                      is stable-enough for LeetCode's
                                      checker, but the demo's cross-check
                                      compares against a full sort to catch
                                      genuine ordering bugs, not just tie
                                      order).


================================================================================
COMMON MISTAKES
================================================================================
1. Pushing a nil *ListNode into the heap for an empty input list — Less()
   or any Val access on it panics. Always skip nil lists during heap seed.
2. Forgetting to push a popped node's .Next back into the heap when it is
   non-nil — silently drops the rest of that list from the output.
3. container/heap requires calling heap.Init after populating the backing
   slice directly (bypassing heap.Push) — otherwise the heap invariant
   isn't established and Pop returns wrong results. This file uses
   heap.Push throughout to sidestep that, but it's a common bug to know.
4. Implementing Less() to compare by node pointer or list index instead of
   .Val — the heap then doesn't order by value at all.
5. In the divide-and-conquer version, merging lists[i] with lists[i+1] but
   forgetting the ODD leftover list when len(lists) is odd on a given
   round — it must be carried through to the next round unmerged, not
   dropped.
6. Assuming the sequential-fold approach (Approach 2) is "fine" for large
   k without stating its O(N*k) cost — it is asymptotically worse than
   heap/D&C and the difference is measured live in the demo below.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why is the heap O(N log k) and not O(N log N)?
A: The heap never holds more than k elements at once (one per input list),
   so each push/pop is O(log k), not O(log N) — k is the number of LISTS,
   N is the total number of NODES, and k <= N always.

Q: Heap vs divide-and-conquer — which would you pick in an interview?
A: Both hit O(N log k); D&C needs no extra data structure (just recursive
   merge-two-lists) and is often considered more elegant to code from
   scratch, while the heap is more directly "obvious" once you frame the
   problem as repeated k-way minimum selection. State the trade-off, then
   pick one and code it cleanly — see the measured comparison below for
   which wins on THIS machine (do not assume the answer without measuring).

Q: What if the lists could be extremely long, or this had to stream from
   disk/network?
A: The heap approach only ever holds O(k) node references in memory
   regardless of N, making it naturally streaming-friendly — you never need
   all N nodes in memory at once, just the current head of each source.

Q: Can this be done in O(1) extra space?
A: Not really, if you need genuine k-way selection each step — you need at
   least O(k) state to know which of the k lists to advance next. The
   sequential fold (Approach 2) gets closer to O(1) EXTRA space (beyond the
   nodes themselves) at the cost of O(N*k) time — space/time trade-off, not
   a free win.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 21   Merge Two Sorted Lists  — the atomic merge operation reused by
                                       every approach here (this topic's
                                       problem 002)
    LC 378  Kth Smallest Element in a Sorted Matrix — same "k sorted
                                       sequences, min-heap picks next"
                                       pattern, rows instead of lists
    LC 295  Find Median from Data Stream — a different heap use (two heaps
                                       for a running median), same family
                                       (topic 12 · Heap)
================================================================================
*/

// mergeTwoLists is the LC 21 primitive every approach here builds on.
// O(n+m) time, O(1) extra space, reuses existing nodes.
func mergeTwoLists(a, b *ListNode) *ListNode {
	dummy := &ListNode{}
	tail := dummy
	for a != nil && b != nil {
		if a.Val <= b.Val {
			tail.Next = a
			a = a.Next
		} else {
			tail.Next = b
			b = b.Next
		}
		tail = tail.Next
	}
	if a != nil {
		tail.Next = a
	} else {
		tail.Next = b
	}
	return dummy.Next
}

// ---- Approach 3: min-heap ----------------------------------------------

// nodeHeap implements container/heap.Interface over *ListNode, ordered by
// Val.
type nodeHeap []*ListNode

func (h nodeHeap) Len() int            { return len(h) }
func (h nodeHeap) Less(i, j int) bool  { return h[i].Val < h[j].Val }
func (h nodeHeap) Swap(i, j int)       { h[i], h[j] = h[j], h[i] }
func (h *nodeHeap) Push(x interface{}) { *h = append(*h, x.(*ListNode)) }
func (h *nodeHeap) Pop() interface{} {
	old := *h
	n := len(old)
	item := old[n-1]
	*h = old[:n-1]
	return item
}

// mergeKListsHeap is the interview answer via a min-heap of k candidates.
// O(N log k) time, O(k) space, reuses existing nodes.
func mergeKListsHeap(lists []*ListNode) *ListNode {
	h := &nodeHeap{}
	heap.Init(h)
	for _, l := range lists {
		if l != nil {
			heap.Push(h, l)
		}
	}
	dummy := &ListNode{}
	tail := dummy
	for h.Len() > 0 {
		n := heap.Pop(h).(*ListNode)
		tail.Next = n
		tail = tail.Next
		if n.Next != nil {
			heap.Push(h, n.Next)
		}
	}
	tail.Next = nil
	return dummy.Next
}

// ---- Approach 4: divide-and-conquer -------------------------------------

// mergeKListsDivideConquer is the interview answer via pairwise merging.
// O(N log k) time, O(log k) recursion depth, reuses existing nodes.
func mergeKListsDivideConquer(lists []*ListNode) *ListNode {
	if len(lists) == 0 {
		return nil
	}
	if len(lists) == 1 {
		return lists[0]
	}
	mid := len(lists) / 2
	left := mergeKListsDivideConquer(lists[:mid])
	right := mergeKListsDivideConquer(lists[mid:])
	return mergeTwoLists(left, right)
}

// ---- Approach 2: sequential pairwise fold (baseline) --------------------

// mergeKListsSequential folds mergeTwoLists over the k lists one at a
// time. O(N*k) time worst case, O(1) extra space, reuses existing nodes.
func mergeKListsSequential(lists []*ListNode) *ListNode {
	var acc *ListNode
	for _, l := range lists {
		acc = mergeTwoLists(acc, l)
	}
	return acc
}

// ---- Approach 1: collect, sort, rebuild (oracle / brute force) ---------

// mergeKListsSort ignores that inputs are pre-sorted: collect every value,
// sort, rebuild fresh nodes. O(N log N) time, O(N) space. Used here as a
// correctness oracle, never as the delivered answer.
func mergeKListsSort(lists []*ListNode) *ListNode {
	var vals []int
	for _, l := range lists {
		for n := l; n != nil; n = n.Next {
			vals = append(vals, n.Val)
		}
	}
	sort.Ints(vals)
	dummy := &ListNode{}
	tail := dummy
	for _, v := range vals {
		tail.Next = &ListNode{Val: v}
		tail = tail.Next
	}
	return dummy.Next
}

// ---- test helpers --------------------------------------------------------

func slicesToLists(rows [][]int) []*ListNode {
	out := make([]*ListNode, len(rows))
	for i, r := range rows {
		out[i] = sliceToList(r)
	}
	return out
}

func sliceToList(vals []int) *ListNode {
	dummy := &ListNode{}
	curr := dummy
	for _, v := range vals {
		curr.Next = &ListNode{Val: v}
		curr = curr.Next
	}
	return dummy.Next
}

func listToSlice(head *ListNode) []int {
	var out []int
	for n := head; n != nil; n = n.Next {
		out = append(out, n.Val)
	}
	return out
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
	cases := [][][]int{
		{{1, 4, 5}, {1, 3, 4}, {2, 6}},
		{},
		{{}},
		{{}, {}, {}},
		{{1}},
		{{}, {1, 2, 3}},
		{{5, 5, 5}, {5, 5}, {5}},
		{{-10, -5, 0}, {-3, -1, 2}, {-100}},
	}

	allOK := true
	fmt.Println("--- correctness: heap vs divide-conquer vs sequential vs sort-oracle ---")
	for _, rows := range cases {
		want := mergeKListsSort(slicesToLists(rows))
		wantVals := listToSlice(want)

		gotHeap := listToSlice(mergeKListsHeap(slicesToLists(rows)))
		gotDC := listToSlice(mergeKListsDivideConquer(slicesToLists(rows)))
		gotSeq := listToSlice(mergeKListsSequential(slicesToLists(rows)))

		ok := equalInts(gotHeap, wantVals) && equalInts(gotDC, wantVals) && equalInts(gotSeq, wantVals)
		allOK = allOK && ok
		fmt.Printf("%s  lists=%-40v -> %v\n", status(ok), rows, gotHeap)
	}

	// ------------------------------------------------------------------
	// Live trace of the heap approach on [[1,4,5],[1,3,4],[2,6]].
	// ------------------------------------------------------------------
	fmt.Println("\n--- trace: heap approach on [[1,4,5],[1,3,4],[2,6]] ---")
	rows := [][]int{{1, 4, 5}, {1, 3, 4}, {2, 6}}
	lists := slicesToLists(rows)
	h := &nodeHeap{}
	heap.Init(h)
	labels := map[*ListNode]string{}
	names := []string{"list0", "list1", "list2"}
	for i, l := range lists {
		for n := l; n != nil; n = n.Next {
			// label by originating list, val stays attached to node
			_ = n
		}
		if l != nil {
			labels[l] = names[i]
		}
		// propagate a label per node so the trace can say "1(list0)"
		src := names[i]
		for n := l; n != nil; n = n.Next {
			labels[n] = src
		}
		if l != nil {
			heap.Push(h, l)
		}
	}
	dummy := &ListNode{}
	tail := dummy
	step := 0
	for h.Len() > 0 {
		step++
		n := heap.Pop(h).(*ListNode)
		fmt.Printf("  step %d: pop %d(%s)", step, n.Val, labels[n])
		tail.Next = n
		tail = tail.Next
		if n.Next != nil {
			heap.Push(h, n.Next)
			fmt.Printf(" -> push %d(%s)\n", n.Next.Val, labels[n.Next])
		} else {
			fmt.Printf(" -> %s exhausted\n", labels[n])
		}
	}
	tail.Next = nil
	fmt.Printf("  result: %v\n", listToSlice(dummy.Next))

	// ------------------------------------------------------------------
	// Empty and nil-list edge cases, explicitly.
	// ------------------------------------------------------------------
	fmt.Println("\n--- edge cases: nil lists mixed with real ones ---")
	mixed := []*ListNode{nil, sliceToList([]int{2, 4}), nil, sliceToList([]int{1, 3})}
	gotMixed := listToSlice(mergeKListsHeap(mixed))
	wantMixed := []int{1, 2, 3, 4}
	mixedOK := equalInts(gotMixed, wantMixed)
	fmt.Printf("  %s  mixed nil/non-nil lists -> %v (want %v)\n", status(mixedOK), gotMixed, wantMixed)
	allOK = allOK && mixedOK

	// ------------------------------------------------------------------
	// Randomised cross-check against the sort oracle.
	// ------------------------------------------------------------------
	fmt.Println("\n--- randomised cross-check: heap & divide-conquer vs sort oracle ---")
	rng := rand.New(rand.NewSource(7))
	trials, mismatches := 200, 0
	for t := 0; t < trials; t++ {
		k := rng.Intn(10)
		rows := make([][]int, k)
		for i := 0; i < k; i++ {
			n := rng.Intn(8)
			vals := make([]int, n)
			cur := rng.Intn(5) - 2
			for j := 0; j < n; j++ {
				cur += rng.Intn(4)
				vals[j] = cur
			}
			rows[i] = vals
		}
		want := listToSlice(mergeKListsSort(slicesToLists(rows)))
		gotH := listToSlice(mergeKListsHeap(slicesToLists(rows)))
		gotD := listToSlice(mergeKListsDivideConquer(slicesToLists(rows)))
		if !equalInts(gotH, want) || !equalInts(gotD, want) {
			mismatches++
		}
	}
	fmt.Printf("  %d random k-list inputs: %d mismatches\n", trials, mismatches)
	allOK = allOK && mismatches == 0

	// ------------------------------------------------------------------
	// Measured runtime: heap vs divide-conquer vs sequential vs sort.
	// ------------------------------------------------------------------
	fmt.Println("\n--- measured runtime: heap vs divide-conquer vs sequential fold vs sort ---")
	fmt.Printf("  %6s %6s %12s %12s %14s %10s\n", "k", "N", "heap", "div-conq", "sequential", "sort")
	rng2 := rand.New(rand.NewSource(1))
	for _, k := range []int{50, 200, 800} {
		perList := 100
		rows := make([][]int, k)
		for i := 0; i < k; i++ {
			vals := make([]int, perList)
			cur := 0
			for j := 0; j < perList; j++ {
				cur += rng2.Intn(5)
				vals[j] = cur
			}
			rows[i] = vals
		}
		n := k * perList

		t0 := time.Now()
		mergeKListsHeap(slicesToLists(rows))
		t1 := time.Now()
		mergeKListsDivideConquer(slicesToLists(rows))
		t2 := time.Now()
		mergeKListsSequential(slicesToLists(rows))
		t3 := time.Now()
		mergeKListsSort(slicesToLists(rows))
		t4 := time.Now()

		fmt.Printf("  %6d %6d %10.2fms %10.2fms %12.2fms %8.2fms\n",
			k, n,
			float64(t1.Sub(t0).Microseconds())/1000.0,
			float64(t2.Sub(t1).Microseconds())/1000.0,
			float64(t3.Sub(t2).Microseconds())/1000.0,
			float64(t4.Sub(t3).Microseconds())/1000.0)
	}
	fmt.Println("  Numbers above are measured on this run, this machine — read the ratios,")
	fmt.Println("  not the absolute values, and note the sequential fold's cost growing")
	fmt.Println("  fastest as k increases (its O(N*k) bound, vs O(N log k) for the others).")

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
