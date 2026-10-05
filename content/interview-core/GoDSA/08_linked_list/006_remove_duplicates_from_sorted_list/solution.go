package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 83 · Remove Duplicates from Sorted List               [Easy]
https://leetcode.com/problems/remove-duplicates-from-sorted-list/
================================================================================

THE CORE IDEA
--------------
Because the input is SORTED, duplicates of any value are always physically
ADJACENT -- never scattered. So "remove duplicates" collapses from a general
membership problem into a one-pointer adjacent scan: compare curr.Val with
curr.Next.Val; splice out a match; otherwise advance.

    curr := head
    for curr != nil && curr.Next != nil {
        if curr.Val == curr.Next.Val {
            curr.Next = curr.Next.Next   // skip the duplicate; curr stays put
        } else {
            curr = curr.Next             // advance only past a KEPT node
        }
    }
    return head

No dummy head needed (contrast problem 005): the head node is never itself a
deletion candidate here, only its later duplicates are -- head as a value is
always returned unchanged.


================================================================================
APPROACH 1 · Hashset of seen values (works on ANY list, priced not needed)
================================================================================
    seen := map[int]bool{}
    dummy := &ListNode{Next: head}
    curr := dummy
    for curr.Next != nil {
        if seen[curr.Next.Val] {
            curr.Next = curr.Next.Next
        } else {
            seen[curr.Next.Val] = true
            curr = curr.Next
        }
    }
    return dummy.Next

Correct on unsorted input too. O(n) time, but O(n) EXTRA space for the map --
the sorted precondition specifically means we never need to remember anything
beyond "am I equal to the node right before me," so this generality is
wasted here. Priced, coded below only as a cross-check oracle.


================================================================================
APPROACH 2 · Adjacent-pointer scan ✅ (the answer -- sorted input required)
================================================================================
As in THE CORE IDEA. O(n) time, O(1) space, one pointer, no dummy. This ONLY
works because the input is sorted -- see the live demo below for what happens
if it's applied to an unsorted list anyway.


================================================================================
STEP BY STEP -- head = [1, 1, 2, 3, 3]
================================================================================
    curr
    [1] -> 1 -> 2 -> 3 -> 3 -> nil

    curr.Val=1, curr.Next.Val=1  MATCH -> curr.Next = curr.Next.Next
    curr
    [1] -> 2 -> 3 -> 3 -> nil                (curr stays at the first 1)

    curr.Val=1, curr.Next.Val=2  no match -> curr = curr.Next
              curr
    1 -> [2] -> 3 -> 3 -> nil

    curr.Val=2, curr.Next.Val=3  no match -> curr = curr.Next
                   curr
    1 -> 2 -> [3] -> 3 -> nil

    curr.Val=3, curr.Next.Val=3  MATCH -> curr.Next = curr.Next.Next
                   curr
    1 -> 2 -> [3] -> nil

    curr.Next is nil -> loop ends
    return head = 1 -> 2 -> 3 -> nil    ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time   Space   Mutates input?  Precondition
    ------------------------------ ------ ------  ---------------  ---------------
    Hashset of seen values          O(n)   O(n)    yes              none (any list)
    Adjacent-pointer scan ✅        O(n)   O(1)    yes              SORTED input
    Adjacent scan on unsorted data  O(n)   O(1)    yes              WRONG -- misses
                                                                     non-adjacent dupes


================================================================================
EDGE CASES
================================================================================
    head = nil              -> nil.  `curr != nil && curr.Next != nil` is
                                    false immediately; nothing to do.
    single node               -> unchanged. curr.Next is nil from the start.
    all identical values       -> collapses to ONE node. [1,1,1,1] -> [1]; the
                                    "curr does not advance on a match" rule is
                                    what makes a run of any length collapse.
    no duplicates at all        -> unchanged; curr walks straight through.
    duplicates at the very END   -> [.., 3, 3] still collapses; the loop
                                    condition `curr.Next != nil` (not
                                    `curr.Next.Next`) correctly reaches the
                                    last pair.
    negative values              -> equality comparison doesn't care about
                                    sign; -3 == -3 works the same as 3 == 3.


================================================================================
COMMON MISTAKES
================================================================================
1. Applying this adjacent-scan directly to an UNSORTED list and expecting it
   to dedupe -- it silently only catches duplicates that happen to already
   be next to each other, and leaves non-adjacent duplicates untouched. Live
   demo below on [1, 2, 1].
2. Advancing curr unconditionally even after a deletion -- breaks a run of
   3+ identical values; only the FIRST duplicate in the run gets removed.
3. Using `for curr.Next != nil` without also checking `curr != nil` first --
   panics immediately on an empty list (curr is nil, nil.Next panics). Guard
   both, in that order.
4. Reaching for a dummy head out of habit (problem 005's pattern) when it
   isn't needed here -- harmless but adds an unnecessary allocation; the head
   is never a deletion target in THIS problem.
5. Confusing this with LC 82 (Remove Duplicates from Sorted List II), which
   removes ALL nodes that have ANY duplicate (including the first copy) --
   that variant genuinely needs a dummy head, because the original head
   itself might need deleting if it's part of a duplicate run.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the list were NOT guaranteed sorted?
A: Either sort it first (O(n log n)) or use the hashset approach (Approach
   1), O(n) time / O(n) space, unconditionally correct regardless of order.

Q: LC 82 -- remove nodes that have ANY duplicate entirely (not keep one copy).
A: Needs a dummy head (the original head might be part of a duplicate run
   that gets fully deleted) and a look-ahead: count how many consecutive
   nodes share a value, and if more than 1, skip the WHOLE run.

Q: Can you do this without mutating the input list?
A: Yes -- build a brand new list, appending a node only when its value
   differs from the last value appended. O(n) time, O(n) space (new nodes),
   leaves the original list untouched.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 82   Remove Duplicates from Sorted List II -- deletes ALL copies of any
                                                      duplicated value; needs
                                                      a dummy head + look-ahead
    LC 26   Remove Duplicates from Sorted Array     -- same adjacent-scan idea,
                                                      applied to an array with
                                                      an in-place write index
                                                      instead of pointer rewiring
    LC 203  Remove Linked List Elements              -- deletes by VALUE match,
                                                      needs a dummy head
                                                      (problem 005 here)
================================================================================
*/

// deleteDuplicates is the interview answer: adjacent-pointer scan.
// O(n) time, O(1) space. Requires SORTED input.
func deleteDuplicates(head *ListNode) *ListNode {
	curr := head
	for curr != nil && curr.Next != nil {
		if curr.Val == curr.Next.Val {
			curr.Next = curr.Next.Next
		} else {
			curr = curr.Next
		}
	}
	return head
}

// deleteDuplicatesHashset is correct regardless of sort order.
// O(n) time, O(n) space.
func deleteDuplicatesHashset(head *ListNode) *ListNode {
	seen := make(map[int]bool)
	dummy := &ListNode{Next: head}
	curr := dummy
	for curr.Next != nil {
		if seen[curr.Next.Val] {
			curr.Next = curr.Next.Next
		} else {
			seen[curr.Next.Val] = true
			curr = curr.Next
		}
	}
	return dummy.Next
}

func listToLinked(values []int) *ListNode {
	dummy := &ListNode{}
	curr := dummy
	for _, v := range values {
		curr.Next = &ListNode{Val: v}
		curr = curr.Next
	}
	return dummy.Next
}

func linkedToList(head *ListNode) []int {
	var out []int
	for node := head; node != nil; node = node.Next {
		out = append(out, node.Val)
	}
	return out
}

func equalIntSlices(a, b []int) bool {
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
	type tc struct {
		values []int
		want   []int
	}
	cases := []tc{
		{[]int{1, 1, 2}, []int{1, 2}},
		{[]int{1, 1, 2, 3, 3}, []int{1, 2, 3}},
		{[]int{}, []int{}},
		{[]int{1}, []int{1}},
		{[]int{1, 1, 1, 1}, []int{1}},
		{[]int{1, 2, 3}, []int{1, 2, 3}},
		{[]int{-3, -3, -1, 0, 0, 0, 5}, []int{-3, -1, 0, 5}},
	}

	allOK := true
	fmt.Println("--- correctness: adjacent-scan answer vs hashset oracle (sorted input) ---")
	for _, c := range cases {
		got := linkedToList(deleteDuplicates(listToLinked(c.values)))
		gotHS := linkedToList(deleteDuplicatesHashset(listToLinked(c.values)))
		ok := equalIntSlices(got, c.want) && equalIntSlices(gotHS, c.want)
		allOK = allOK && ok
		fmt.Printf("%s  head=%-28v -> %v  (want %v)\n", status(ok), c.values, got, c.want)
	}

	// ------------------------------------------------------------------
	// Live bug: the precondition. Adjacent scan on UNSORTED data.
	// ------------------------------------------------------------------
	fmt.Println("\n--- adjacent scan on UNSORTED data: the precondition, demonstrated live ---")
	unsortedCases := [][]int{
		{1, 2, 1}, // the classic: duplicate 1's are NOT adjacent
		{3, 1, 3, 2, 1},
		{5, 5, 1, 5}, // some duplicates adjacent, one is not
	}
	fmt.Printf("  %-18s %14s %18s  ok?\n", "input", "adjacent-scan", "hashset (correct)")
	precondMismatch := false
	for _, values := range unsortedCases {
		scanResult := linkedToList(deleteDuplicates(listToLinked(values)))
		hashsetResult := linkedToList(deleteDuplicatesHashset(listToLinked(values)))
		mismatch := !equalIntSlices(scanResult, hashsetResult)
		precondMismatch = precondMismatch || mismatch
		verdict := "yes"
		if mismatch {
			verdict = "NO  <- non-adjacent dupes survive"
		}
		fmt.Printf("  %-18v %14v %18v  %s\n", values, scanResult, hashsetResult, verdict)
	}
	fmt.Printf("  unsorted-precondition violation reproduced: %v\n", precondMismatch)
	allOK = allOK && precondMismatch // we WANT to have proven the precondition matters

	fmt.Println("\n  [1, 2, 1] traced through the adjacent-scan algorithm:")
	fmt.Println("    curr=1, curr.Next=2: no match  -> curr advances to 2")
	fmt.Println("    curr=2, curr.Next=1: no match  -> curr advances to 1 (the SECOND 1)")
	fmt.Println("    curr.Next is nil               -> loop ends")
	result121 := linkedToList(deleteDuplicates(listToLinked([]int{1, 2, 1})))
	fmt.Printf("    result: %v   <- WRONG if the intent was 'dedupe regardless of\n", result121)
	fmt.Println("    position': both 1's survive because they were never ADJACENT to compare.")
	fmt.Println("    This is not a bug in the algorithm -- it is the algorithm correctly")
	fmt.Println("    doing exactly what it promises (adjacent-only), on an input that")
	fmt.Println("    violates the precondition it was built for.")

	// ------------------------------------------------------------------
	// Step-by-step trace.
	// ------------------------------------------------------------------
	fmt.Println("\n--- trace: deleteDuplicates([1,1,2,3,3]) ---")
	curr := listToLinked([]int{1, 1, 2, 3, 3})
	step := 0
	for curr != nil && curr.Next != nil {
		step++
		if curr.Val == curr.Next.Val {
			fmt.Printf("  step %d: curr.Val=%d == curr.Next.Val=%d -> SKIP duplicate, curr stays\n", step, curr.Val, curr.Next.Val)
			curr.Next = curr.Next.Next
		} else {
			fmt.Printf("  step %d: curr.Val=%d != curr.Next.Val=%d -> advance\n", step, curr.Val, curr.Next.Val)
			curr = curr.Next
		}
	}

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
