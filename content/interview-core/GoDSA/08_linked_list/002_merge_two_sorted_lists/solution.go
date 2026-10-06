package main

import (
	"fmt"
	"math/rand"
	"sort"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 21 · Merge Two Sorted Lists                          [Easy]
https://leetcode.com/problems/merge-two-sorted-lists/
================================================================================

THE CORE IDEA
-------------
Merge sort's merge step, minus the slice-allocation cost: because both
inputs are already sorted, you never need to compare more than the two
current front nodes, and "inserting" the winner costs one pointer rewrite,
not a slice write. A dummy/sentinel head (topic guide Part 2) means the
first node of the result needs no special case — `tail` starts ONE STEP
BEFORE the real merged list.

    dummy := &ListNode{}
    tail := dummy
    for list1 != nil && list2 != nil {
        if list1.Val <= list2.Val {
            tail.Next = list1
            list1 = list1.Next
        } else {
            tail.Next = list2
            list2 = list2.Next
        }
        tail = tail.Next
    }
    if list1 != nil {
        tail.Next = list1
    } else {
        tail.Next = list2
    }
    return dummy.Next

O(n+m) time, O(1) space — every node is REUSED, not copied.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code as the answer): collect every value from both
lists into a []int, sort.Ints it, then build a brand-new chain of new
ListNode structs from the sorted values. Correct, but pays
O((n+m) log(n+m)) for a sort you don't need (both inputs are ALREADY sorted)
and O(n+m) extra space for new nodes when the existing ones could just be
rewired. Priced and benchmarked below.

Approach 1 (dummy head + two-pointer merge) ✅ — the answer, shown above.
O(n+m) time, O(1) space, reuses existing nodes in place.

Approach 2 (recursive) — pick the smaller head, recurse on the rest:

    func mergeRecursive(l1, l2 *ListNode) *ListNode {
        if l1 == nil { return l2 }
        if l2 == nil { return l1 }
        if l1.Val <= l2.Val {
            l1.Next = mergeRecursive(l1.Next, l2)
            return l1
        }
        l2.Next = mergeRecursive(l1, l2.Next)
        return l2
    }

Same O(n+m) time, O(n+m) stack frames — same stack-depth concern as
problem 001's recursive reversal. Default to iterative for long lists.


================================================================================
STEP BY STEP TRACE
================================================================================
list1 = 1 -> 2 -> 4 -> nil
list2 = 1 -> 3 -> 4 -> nil

    dummy -> nil              tail = dummy
    1 vs 1: tie, take list1   dummy -> 1(L1)                 tail=1(L1)  list1=2->4
    2 vs 1: take list2        dummy -> 1(L1) -> 1(L2)         tail=1(L2)  list2=3->4
    2 vs 3: take list1        dummy -> ... -> 1(L2) -> 2      tail=2      list1=4
    4 vs 3: take list2        dummy -> ... -> 2 -> 3          tail=3      list2=4
    4 vs 4: tie, take list1   dummy -> ... -> 3 -> 4(L1)      tail=4(L1)  list1=nil
    list1 exhausted -> splice list2's remainder (4) directly:
    dummy -> ... -> 4(L1) -> 4(L2) -> nil

result: 1 -> 1 -> 2 -> 3 -> 4 -> 4 -> nil


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time             Space   Mutates input?  Note
    -------------------------------  ---------------  ------  ---------------  ----------------------
    Collect + sort + rebuild         O((n+m)log(n+m))  O(n+m)  no               wasted sort, new nodes
    Dummy head + 2-pointer merge ✅  O(n+m)           O(1)    yes (rewires Next)  the answer
    Recursive                        O(n+m)           O(n+m)  yes              stack depth risk


================================================================================
EDGE CASES
================================================================================
    nil, nil               -> nil       both empty; dummy.Next stays nil throughout.
    nil, [0]                 -> [0]      one empty; the loop never runs, the
                                       "splice remainder" branch does all the work.
    [1,2,3], nil               -> [1,2,3]  the mirror of the above.
    equal values                -> tie-breaking must pick ONE list consistently
                                 (<=, not <) so ties resolve without dropping
                                 a node.
    lists of very different lengths -> exercises the "splice the remainder"
                                 branch heavily.


================================================================================
COMMON MISTAKES
================================================================================
1. Not using a dummy head — forces special-casing "is this the first node of
   the result yet?" every iteration.

2. Forgetting the final splice (`tail.Next = list1` or `list2`, whichever is
   non-nil) — silently drops the remainder, truncating the result exactly
   like problem 001's broken reversal.

3. Allocating NEW *ListNode structs for the merged result instead of
   rewiring the existing ones — wastes O(n+m) space the problem doesn't
   require.

4. `*b = *a` style struct-copy mistakes when adapting node fields (topic
   guide Part 5) — always rewire `.Next` field by field, never blanket-copy
   a struct you only meant to read a value from.

5. Comparing with `<` in one place and assuming `<=` semantics elsewhere —
   pick one operator, keep every branch consistent with it.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Merge k sorted lists instead of 2.
A: LC 23 — merge pairwise (this function called log2(k) times, O(N log k))
   or use a min-heap of the k current front nodes, O(N log k), where N is
   the total node count across all lists.

Q: Do it without mutating either input list.
A: Build entirely new nodes as you walk (copy .Val, don't reuse the
   pointer) — O(n+m) time, O(n+m) space, "mutates input?" flips to no.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 23   Merge k Sorted Lists         — this generalised via a heap
    LC 88   Merge Sorted Array            — the array analogue, merge from the back
    LC 148  Sort List                     — merge sort ON a linked list, this IS the merge step
    LC 143  Reorder List                  — a different kind of "merge" (alternating)
================================================================================
*/

// mergeTwoLists is the interview answer: dummy head + two-pointer merge.
// Time O(n+m), space O(1).
func mergeTwoLists(list1 *ListNode, list2 *ListNode) *ListNode {
	dummy := &ListNode{}
	tail := dummy
	for list1 != nil && list2 != nil {
		if list1.Val <= list2.Val {
			tail.Next = list1
			list1 = list1.Next
		} else {
			tail.Next = list2
			list2 = list2.Next
		}
		tail = tail.Next
	}
	if list1 != nil {
		tail.Next = list1
	} else {
		tail.Next = list2
	}
	return dummy.Next
}

// mergeTwoListsRecursive is the recursive variant. Time O(n+m), space O(n+m).
func mergeTwoListsRecursive(list1, list2 *ListNode) *ListNode {
	if list1 == nil {
		return list2
	}
	if list2 == nil {
		return list1
	}
	if list1.Val <= list2.Val {
		list1.Next = mergeTwoListsRecursive(list1.Next, list2)
		return list1
	}
	list2.Next = mergeTwoListsRecursive(list1, list2.Next)
	return list2
}

// mergeTwoListsCollectSort is NAIVE — collect all values, sort, rebuild
// fresh nodes. O((n+m)log(n+m)) time, O(n+m) space.
func mergeTwoListsCollectSort(list1, list2 *ListNode) *ListNode {
	var values []int
	for n := list1; n != nil; n = n.Next {
		values = append(values, n.Val)
	}
	for n := list2; n != nil; n = n.Next {
		values = append(values, n.Val)
	}
	sort.Ints(values)

	dummy := &ListNode{}
	tail := dummy
	for _, v := range values {
		tail.Next = &ListNode{Val: v}
		tail = tail.Next
	}
	return dummy.Next
}

// ---------------------------------------------------------------------------
// Test helpers.
// ---------------------------------------------------------------------------

func buildList(values []int) *ListNode {
	dummy := &ListNode{}
	tail := dummy
	for _, v := range values {
		tail.Next = &ListNode{Val: v}
		tail = tail.Next
	}
	return dummy.Next
}

func toSlice(head *ListNode) []int {
	var out []int
	for head != nil {
		out = append(out, head.Val)
		head = head.Next
	}
	return out
}

func equalSlices(a, b []int) bool {
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

func sortedMerge(a, b []int) []int {
	out := append(append([]int{}, a...), b...)
	sort.Ints(out)
	return out
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}

type pairCase struct{ a, b []int }

func main() {
	cases := []pairCase{
		{[]int{1, 2, 4}, []int{1, 3, 4}},
		{nil, nil},
		{nil, []int{0}},
		{[]int{1, 2, 3}, nil},
		{[]int{5}, []int{1, 2, 3}},
		{[]int{1, 1, 1}, []int{1, 1}},
		{[]int{-3, 0, 5}, []int{-2, -1, 4}},
	}

	allOK := true

	fmt.Println("--- correctness: dummy-head merge ---")
	for _, c := range cases {
		want := sortedMerge(c.a, c.b)
		got := toSlice(mergeTwoLists(buildList(c.a), buildList(c.b)))
		ok := equalSlices(got, want)
		allOK = allOK && ok
		fmt.Printf("%s  %v + %v -> %v  (want %v)\n", status(ok), c.a, c.b, got, want)
	}

	fmt.Println("\n--- correctness: recursive merge, cross-checked ---")
	for _, c := range cases {
		want := toSlice(mergeTwoLists(buildList(c.a), buildList(c.b)))
		got := toSlice(mergeTwoListsRecursive(buildList(c.a), buildList(c.b)))
		ok := equalSlices(got, want)
		allOK = allOK && ok
		fmt.Printf("%s  %v + %v -> %v  (want %v)\n", status(ok), c.a, c.b, got, want)
	}

	fmt.Println("\n--- correctness: naive collect+sort, cross-checked ---")
	for _, c := range cases {
		want := toSlice(mergeTwoLists(buildList(c.a), buildList(c.b)))
		got := toSlice(mergeTwoListsCollectSort(buildList(c.a), buildList(c.b)))
		ok := equalSlices(got, want)
		allOK = allOK && ok
		fmt.Printf("%s  %v + %v -> %v  (want %v)\n", status(ok), c.a, c.b, got, want)
	}

	// -------------------------------------------------------------------
	// Step-by-step trace.
	// -------------------------------------------------------------------
	fmt.Println("\n--- trace: list1=[1,2,4], list2=[1,3,4] ---")
	l1, l2 := buildList([]int{1, 2, 4}), buildList([]int{1, 3, 4})
	dummy := &ListNode{}
	tail := dummy
	step := 0
	for l1 != nil && l2 != nil {
		if l1.Val <= l2.Val {
			fmt.Printf("  step %d: %d <= %d -> take list1's %d\n", step, l1.Val, l2.Val, l1.Val)
			tail.Next = l1
			l1 = l1.Next
		} else {
			fmt.Printf("  step %d: %d < %d -> take list2's %d\n", step, l2.Val, l1.Val, l2.Val)
			tail.Next = l2
			l2 = l2.Next
		}
		tail = tail.Next
		step++
	}
	remainder := "neither"
	if l1 != nil {
		tail.Next = l1
		remainder = "list1"
	} else if l2 != nil {
		tail.Next = l2
		remainder = "list2"
	}
	fmt.Printf("  loop ends; splice remainder from %s\n", remainder)
	fmt.Printf("  final: %v\n", toSlice(dummy.Next))

	// -------------------------------------------------------------------
	// Randomised cross-check.
	// -------------------------------------------------------------------
	fmt.Println("\n--- randomised cross-check (dummy-head vs recursive vs collect+sort) ---")
	rng := rand.New(rand.NewSource(11))
	trials, mismatches := 2000, 0
	for i := 0; i < trials; i++ {
		a := randomSorted(rng, rng.Intn(11))
		b := randomSorted(rng, rng.Intn(11))
		r1 := toSlice(mergeTwoLists(buildList(a), buildList(b)))
		r2 := toSlice(mergeTwoListsRecursive(buildList(a), buildList(b)))
		r3 := toSlice(mergeTwoListsCollectSort(buildList(a), buildList(b)))
		want := sortedMerge(a, b)
		if !equalSlices(r1, want) || !equalSlices(r2, want) || !equalSlices(r3, want) {
			mismatches++
		}
	}
	fmt.Printf("  %d random pairs of sorted lists: %d mismatches\n", trials, mismatches)
	allOK = allOK && mismatches == 0

	// -------------------------------------------------------------------
	// Benchmark: dummy-head O(n) reuse vs collect+sort O(n log n) rebuild.
	// -------------------------------------------------------------------
	fmt.Println("\n--- dummy-head O(n) merge vs collect+sort O(n log n) rebuild: measured runtime ---")
	fmt.Printf("  %14s %14s %14s %8s\n", "n (each list)", "dummy-head", "collect+sort", "ratio")
	rng2 := rand.New(rand.NewSource(0))
	for _, n := range []int{2_000, 8_000, 32_000} {
		a := randomSorted(rng2, n)
		b := randomSorted(rng2, n)

		h1, h2 := buildList(a), buildList(b)
		t0 := time.Now()
		mergeTwoLists(h1, h2)
		dhMs := float64(time.Since(t0).Microseconds()) / 1000.0

		h1, h2 = buildList(a), buildList(b)
		t1 := time.Now()
		mergeTwoListsCollectSort(h1, h2)
		csMs := float64(time.Since(t1).Microseconds()) / 1000.0

		ratio := csMs / dhMs
		fmt.Printf("  %14d %12.2fms %12.2fms %7.2fx\n", n, dhMs, csMs, ratio)
	}

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}

func randomSorted(rng *rand.Rand, n int) []int {
	vals := make([]int, n)
	for i := range vals {
		vals[i] = rng.Intn(2_000_001) - 1_000_000
	}
	sort.Ints(vals)
	return vals
}
