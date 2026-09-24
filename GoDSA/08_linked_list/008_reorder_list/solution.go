package main

import (
	"fmt"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 143 · Reorder List                                [Medium]
https://leetcode.com/problems/reorder-list/
================================================================================

THE CORE IDEA
--------------
Reorder List = topic guide §3.1 (find the middle) + §4.1 (reversal) + one
merge/interleave step. Not a new algorithm — a composition of two techniques
already proven correct elsewhere in this topic.

    1 -> 2 -> 3 -> 4 -> 5
    split at middle:      1 -> 2 -> 3        4 -> 5
    reverse second half:  1 -> 2 -> 3        5 -> 4
    merge alternating:    1 -> 5 -> 2 -> 4 -> 3


================================================================================
APPROACH 1 · Copy nodes into a slice, index-based rebuild (priced, not coded)
================================================================================
Walk the list once, append every *ListNode into a slice; then use lo/hi
index pointers into the slice to rewire .Next directly (nodes[lo].Next =
nodes[hi], nodes[hi].Next = nodes[lo], shrinking the window). Correct and
easier to reason about under pressure — random access via the slice
sidesteps every pointer-chasing subtlety — but O(n) EXTRA space for the
slice of node pointers, when the problem invites an O(1) in-place solution.
Name it, then deliver Approach 2.

    Time: O(n)     Space: O(n) — a []*ListNode of length n


================================================================================
APPROACH 2 · Find middle + reverse + merge ✅ (O(1) space — the answer)
================================================================================
Three phases, each a technique already proven correct elsewhere in this topic:

PHASE 1 — find the middle (guide §3.1):
    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }
    // slow is now the start of the second half

PHASE 2 — cut the list in two, then reverse the second half (guide §4.1):
    second := slow.Next
    slow.Next = nil            // sever — first half now ends cleanly
    var prev *ListNode
    for second != nil {
        next := second.Next
        second.Next = prev
        prev = second
        second = next
    }
    second = prev               // head of the reversed second half

PHASE 3 — merge, alternating one node from each half:
    first := head
    for second != nil {
        firstNext := first.Next    // SAVE before overwriting (guide Part 1.3)
        secondNext := second.Next  // SAVE before overwriting
        first.Next = second
        second.Next = firstNext
        first = firstNext
        second = secondNext
    }

The loop condition `second != nil` (not `first != nil && second != nil`) is
deliberate: the first half is always the same length as the second half or
exactly ONE node longer (when total length is odd), so the first half never
runs out before the second half does — the loop naturally stops when the
(shorter-or-equal) second half is exhausted, leaving any odd-one-out
first-half node as the correct final tail, its .Next already nil from Phase
2's cut.

    Time: O(n)     Space: O(1), the list is reordered in place


================================================================================
STEP BY STEP — head = 1 -> 2 -> 3 -> 4 -> 5 (odd length)
================================================================================
    Phase 1 — find the middle:
        1 -> 2 -> 3 -> 4 -> 5 -> nil
        slow ends at node 3 (fast fell off the end after 2 hops of 2)

    Phase 2 — cut at slow, reverse the second half:
        first half:                    1 -> 2 -> 3 -> nil
        second half (before reverse):  4 -> 5 -> nil
        second half (after reverse):   5 -> 4 -> nil

    Phase 3 — merge, alternating:
        first=1, second=5
          save firstNext=2, secondNext=4
          1.Next = 5;  5.Next = 2
          first=2, second=4
        first=2, second=4
          save firstNext=3, secondNext=nil
          2.Next = 4;  4.Next = 3
          first=3, second=nil
        second is nil -> loop ends

    result: 1 -> 5 -> 2 -> 4 -> 3 -> nil     (3.Next already nil from Phase 2)


================================================================================
STEP BY STEP — head = 1 -> 2 -> 3 -> 4 (even length)
================================================================================
    Phase 1: slow ends at node 2 (start of the second half, for even length)
    Phase 2: first half 1->2->nil, second half reversed: 4->3->nil
    Phase 3:
        first=1, second=4: save firstNext=2, secondNext=3;
                            1.Next=4; 4.Next=2; first=2, second=3
        first=2, second=3: save firstNext=nil, secondNext=nil;
                            2.Next=3; 3.Next=nil; first=nil, second=nil
        loop ends (second is nil)
    result: 1 -> 4 -> 2 -> 3 -> nil


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time   Space  Mutates input?  Note
    --------------------------------  -----  ------ ---------------  ----------------
    Slice of node pointers, rebuild   O(n)   O(n)   yes              simpler, more space
    Find middle + reverse + merge ✅  O(n)   O(1)   yes (in place)   the answer


================================================================================
EDGE CASES
================================================================================
    single node    -> unchanged. fast/slow never advances past head; the
                       "second half" is empty; merge loop never runs.
    two nodes       -> unchanged. [1,2] -> [1,2]: Ln is already the second
                       node, so the reorder is the identity.
    three nodes     -> [1,2,3] -> [1,3,2]. Smallest case that actually
                       changes anything.
    odd length      -> the middle node (found by slow/fast) ends up as the
                       first half's leftover tail — see the odd-length trace.
    even length     -> both halves are equal length; merge exhausts both
                       pointers on the same step.
    all identical values -> reorder still reshuffles POSITIONS even though
                       every value looks the same; the demo below verifies
                       by node IDENTITY, not just values, to catch a merge
                       that silently no-ops.


================================================================================
COMMON MISTAKES
================================================================================
1. Reversing the second half BEFORE finding the correct split point, or
   reversing the WRONG portion — corrupts the list before the merge even
   starts. Always find the middle first (Phase 1), only then reverse
   (Phase 2).
2. Forgetting `slow.Next = nil` after finding the middle — the "first half"
   then still trails into the second half's original (now partially
   reversed) structure, corrupting the merge.
3. THE classic bug from topic guide Part 1.3, in a new shape: overwriting
   `first.Next` or `second.Next` during the merge BEFORE saving the node
   each pointer needs to advance to next. Both `firstNext` and `secondNext`
   must be captured before either assignment in the merge loop body.
4. Using `first != nil && second != nil` instead of just `second != nil` —
   usually harmless since first never actually runs out first, but relying
   on the wrong invariant makes correctness accidental rather than reasoned;
   state explicitly why `second` is guaranteed shorter-or-equal.
5. Testing only with VALUES and never verifying with node IDENTITY — a
   reorder implementation that leaves the list untouched can still "pass" a
   palindromic-values test input, masking a merge that does nothing.
6. Trying to reorder by rewriting `.Val` fields instead of `.Next`
   pointers — technically produces the right value sequence but violates the
   problem's explicit "only nodes may be changed" constraint and defeats the
   point of the exercise (this topic is about pointer rewiring).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you avoid reversing the second half?
A: Yes, with an auxiliary structure (e.g. a slice or deque of node pointers)
   to get O(1) access from both ends — but that trades the in-place reversal
   for O(n) extra space, so it's Approach 1's trade-off restated, not a free
   win.

Q: What if this needed to be done for a DOUBLY linked list?
A: The reversal step becomes unnecessary — walk the second half backward
   directly via .Prev, so the merge can interleave head-forward and
   tail-backward pointers without ever rewriting the second half's direction.

Q: How would you verify a merge implementation doesn't just leave the list
   unchanged for a palindromic-values case?
A: Compare node IDENTITY (pointer equality), not just .Val sequences, in
   tests — see Common Mistakes #5 and this file's demo, which checks
   identity to catch a no-op merge.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 206  Reverse Linked List        — Phase 2's reversal template
                                          (problem 001 here)
    LC 876  Middle of the Linked List  — Phase 1's slow/fast split
                                          (problem 004 here)
    LC 21   Merge Two Sorted Lists     — a different merge (by VALUE order,
                                          not strict alternation) using the
                                          same dummy-head + two-pointer shape
    LC 234  Palindrome Linked List     — the SAME find-middle + reverse
                                          composition, used for comparison
                                          instead of reordering (problem 007
                                          here)
================================================================================
*/

// reorderList is the interview answer: find middle + reverse + merge.
// O(n) time, O(1) extra space, mutates in place.
func reorderList(head *ListNode) {
	if head == nil || head.Next == nil {
		return
	}

	// Phase 1: find the middle.
	slow, fast := head, head
	for fast != nil && fast.Next != nil {
		slow = slow.Next
		fast = fast.Next.Next
	}

	// Phase 2: cut, then reverse the second half.
	second := slow.Next
	slow.Next = nil
	var prev *ListNode
	for second != nil {
		next := second.Next
		second.Next = prev
		prev = second
		second = next
	}
	second = prev

	// Phase 3: merge, alternating one node from each half.
	first := head
	for second != nil {
		firstNext := first.Next
		secondNext := second.Next
		first.Next = second
		second.Next = firstNext
		first = firstNext
		second = secondNext
	}
}

// reorderListSlice is O(n) time, O(n) space — slice of node pointers,
// rebuilt via lo/hi index arithmetic. Simpler, more auxiliary memory.
func reorderListSlice(head *ListNode) {
	if head == nil {
		return
	}
	var nodes []*ListNode
	for n := head; n != nil; n = n.Next {
		nodes = append(nodes, n)
	}
	lo, hi := 0, len(nodes)-1
	for lo < hi {
		nodes[lo].Next = nodes[hi]
		lo++
		if lo == hi {
			break
		}
		nodes[hi].Next = nodes[lo]
		hi--
	}
	nodes[lo].Next = nil
}

// ---- test helpers -----------------------------------------------------

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

func main() {
	cases := []struct {
		vals []int
		want []int
	}{
		{[]int{1, 2, 3, 4}, []int{1, 4, 2, 3}},
		{[]int{1, 2, 3, 4, 5}, []int{1, 5, 2, 4, 3}},
		{[]int{1}, []int{1}},
		{[]int{1, 2}, []int{1, 2}},
		{[]int{1, 2, 3}, []int{1, 3, 2}},
		{[]int{1, 2, 3, 4, 5, 6}, []int{1, 6, 2, 5, 3, 4}},
		{[]int{7}, []int{7}},
		{[]int{5, 5, 5, 5}, []int{5, 5, 5, 5}},
	}

	allOK := true
	fmt.Println("--- correctness: find-middle+reverse+merge vs slice-rebuild (values) ---")
	for _, tc := range cases {
		h1 := sliceToList(tc.vals)
		reorderList(h1)
		got1 := listToSlice(h1)

		h2 := sliceToList(tc.vals)
		reorderListSlice(h2)
		got2 := listToSlice(h2)

		ok := equalSlices(got1, tc.want) && equalSlices(got2, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  input=%-18v -> %v  (want %v)\n", status(ok), tc.vals, got1, tc.want)
	}

	// ------------------------------------------------------------------
	// Identity check: a no-op "merge" would still pass a palindromic
	// values-only test. Verify actual NODE ORDER changed by identity.
	// ------------------------------------------------------------------
	fmt.Println("\n--- verifying by node IDENTITY, not just values (common mistake #5) ---")
	vals := []int{5, 5, 5, 5}
	head := sliceToList(vals)
	var original []*ListNode
	for n := head; n != nil; n = n.Next {
		original = append(original, n)
	}
	reorderList(head)
	var reordered []*ListNode
	for n := head; n != nil; n = n.Next {
		reordered = append(reordered, n)
	}
	expectedOrder := []*ListNode{original[0], original[3], original[1], original[2]}
	identityOK := len(reordered) == len(expectedOrder)
	if identityOK {
		for i := range reordered {
			if reordered[i] != expectedOrder[i] {
				identityOK = false
			}
		}
	}
	fmt.Printf("  values look identical before/after: %v -> %v\n", vals, listToSlice(head))
	fmt.Printf("  but node OBJECT order is [0,3,1,2] of the original chain: %v\n", identityOK)
	allOK = allOK && identityOK

	// ------------------------------------------------------------------
	// Trace, phase by phase.
	// ------------------------------------------------------------------
	fmt.Println("\n--- trace: reorderList([1,2,3,4,5]), phase by phase ---")
	head = sliceToList([]int{1, 2, 3, 4, 5})
	fmt.Printf("  input: %v\n", listToSlice(head))

	slow, fast := head, head
	for fast != nil && fast.Next != nil {
		slow = slow.Next
		fast = fast.Next.Next
	}
	fmt.Printf("  Phase 1 (find middle): slow.Val=%d\n", slow.Val)

	second := slow.Next
	slow.Next = nil
	fmt.Printf("  Phase 2a (cut): first half=%v  second half (pre-reverse)=%v\n",
		listToSlice(head), listToSlice(second))
	var prev *ListNode
	for second != nil {
		next := second.Next
		second.Next = prev
		prev = second
		second = next
	}
	second = prev
	fmt.Printf("  Phase 2b (reverse 2nd half): second half (reversed)=%v\n", listToSlice(second))

	first := head
	step := 0
	for second != nil {
		step++
		firstNext := first.Next
		secondNext := second.Next
		first.Next = second
		second.Next = firstNext
		fnVal := -1
		if firstNext != nil {
			fnVal = firstNext.Val
		}
		fmt.Printf("  Phase 3 step %d: link %d->%d, then %d->%v\n",
			step, first.Val, second.Val, second.Val, fnVal)
		first = firstNext
		second = secondNext
	}
	fmt.Printf("  final: %v\n", listToSlice(head))

	// ------------------------------------------------------------------
	// In-place O(1) space vs slice-rebuild O(n) space: measured runtime.
	// ------------------------------------------------------------------
	fmt.Println("\n--- in-place O(1) space vs slice-rebuild O(n) space: measured runtime ---")
	fmt.Printf("  %8s %16s %14s %8s\n", "n", "in-place O(1)", "slice O(n)", "ratio")
	for _, n := range []int{10_000, 100_000, 500_000} {
		vals := make([]int, n)
		for i := range vals {
			vals[i] = i
		}
		h1 := sliceToList(vals)
		t0 := time.Now()
		reorderList(h1)
		t1 := time.Now()
		h2 := sliceToList(vals)
		t2 := time.Now()
		reorderListSlice(h2)
		t3 := time.Now()
		ipMs := float64(t1.Sub(t0).Microseconds()) / 1000.0
		arrMs := float64(t3.Sub(t2).Microseconds()) / 1000.0
		ratio := 0.0
		if ipMs > 0 {
			ratio = arrMs / ipMs
		}
		fmt.Printf("  %8d %14.2fms %12.2fms %7.2fx\n", n, ipMs, arrMs, ratio)
	}
	fmt.Println("  Both are O(n) time in practice; the slice version's extra")
	fmt.Println("  allocation shows up as somewhat higher cost, and — the real point —")
	fmt.Println("  O(n) extra memory that the in-place three-phase version avoids.")

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
