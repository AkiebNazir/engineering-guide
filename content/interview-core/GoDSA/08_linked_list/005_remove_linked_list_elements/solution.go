package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 203 · Remove Linked List Elements                   [Easy]
https://leetcode.com/problems/remove-linked-list-elements/
================================================================================

THE CORE IDEA
--------------
Deleting a node whose Val equals val is normally `curr.Next = curr.Next.Next`
— one line. The catch is the HEAD: if the head itself matches, there is no
"node before it" to hold curr, so the rewire can't express "delete the
head" without reassigning head directly, a different code path from every
other position. A dummy node standing one slot before the real head erases
that difference: dummy.Next IS the head, so deleting the head and deleting a
middle node become the exact same rewire.

    dummy := &ListNode{Next: head}
    curr := dummy
    for curr.Next != nil {
        if curr.Next.Val == val {
            curr.Next = curr.Next.Next
        } else {
            curr = curr.Next
        }
    }
    return dummy.Next


================================================================================
APPROACH 1 · Without a dummy — special-case the head (priced, then shown broken)
================================================================================
    func removeNaive(head *ListNode, val int) *ListNode {
        for head != nil && head.Val == val {   // strip the front
            head = head.Next
        }
        if head == nil {
            return nil
        }
        curr := head
        for curr.Next != nil {
            if curr.Next.Val == val {
                curr.Next = curr.Next.Next
            } else {
                curr = curr.Next
            }
        }
        return head
    }

O(n) / O(1), and CORRECT if written carefully with a `for` loop stripping
the front — but it is easy to write an `if` instead of a `for` there and
only strip ONE matching head node instead of a whole run. The live demo
below builds exactly that broken variant and runs it on [6,6,6,1].


================================================================================
APPROACH 2 · Dummy head ✅ (the answer)
================================================================================
As in THE CORE IDEA. O(n) time, O(1) extra space (one allocation), a single
code path for every position including the head.


================================================================================
STEP BY STEP — nums = [1, 2, 6, 3, 4, 5, 6], val = 6
================================================================================
    dummy -> 1 -> 2 -> 6 -> 3 -> 4 -> 5 -> 6 -> nil
     ^curr

    curr.Next=1, no match  -> curr = 1
    curr.Next=2, no match  -> curr = 2
    curr.Next=6, MATCH     -> curr.Next = curr.Next.Next (skip the 6); curr stays at 2
    curr.Next=3, no match  -> curr = 3
    curr.Next=4, no match  -> curr = 4
    curr.Next=5, no match  -> curr = 5
    curr.Next=6, MATCH     -> curr.Next = curr.Next.Next (skip the trailing 6)
    curr.Next == nil -> loop ends

    return dummy.Next = 1 -> 2 -> 3 -> 4 -> 5 -> nil    ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time   Space   Mutates input?  Note
    --------------------------  -----  ------  ---------------  ----------------
    Without dummy (careful)     O(n)   O(1)    yes              two code paths
    Without dummy (naive/buggy) O(n)   O(1)    yes              WRONG on head runs
    Dummy head ✅               O(n)   O(1)    yes              one code path


================================================================================
EDGE CASES
================================================================================
    head = nil            -> nil.  `for curr.Next != nil` never runs; dummy.Next
                                    stays nil. No special check needed.
    every node matches      -> nil.  [7,7,7,7] must collapse to nothing — "curr
                                    does not advance on a match" is what makes a
                                    whole run collapse in one pass.
    val matches nothing       -> unchanged.
    matches ONLY at the head    -> the case that breaks a careless non-dummy
                                    version; demonstrated live below.


================================================================================
COMMON MISTAKES
================================================================================
1. Advancing curr unconditionally, even after a deletion — leaves a stray
   match behind on runs of 2+ consecutive matches.
2. Without a dummy: stripping only ONE matching node off the front with an
   `if` instead of a `for`, so a run of matches at the head is not fully
   removed. Demonstrated live below.
3. Returning dummy instead of dummy.Next.
4. Forgetting that a struct literal `&ListNode{Next: head}` allocates a REAL
   node — this is not free, but it is O(1), a fine trade for the simplicity
   it buys.
5. In Go specifically: calling a method on a nil *ListNode without a guard
   is fine right up until a field is dereferenced (Go guide Part 1.3) — this
   solution never risks it because curr.Next is always checked before use.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Could you do this recursively?
A: Yes — `head.Next = removeElements(head.Next, val)`, then decide whether to
   keep or skip head — but Go has no TCO (Go guide Part 4.2), so this is
   O(n) real stack frames; Go's growable goroutine stack is more forgiving
   than a fixed thread stack but still strictly worse than the O(1)-space
   iterative version. Default to iterative.

Q: What if you needed to remove nodes matching ANY of several values?
A: Same dummy-head skeleton; swap `curr.Next.Val == val` for membership in a
   `map[int]struct{}` — O(1) per node regardless of how many values.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 19   Remove Nth From End      — fixed-gap two pointers, same dummy-head
                                        motivation
    LC 83   Remove Duplicates        — adjacent-scan deletion, sorted input
            from Sorted List          only (problem 006 here)
    LC 21   Merge Two Sorted Lists   — dummy head for building a NEW list
================================================================================
*/

// removeElements is the interview answer: dummy head, one code path.
// Time O(n), space O(1).
func removeElements(head *ListNode, val int) *ListNode {
	dummy := &ListNode{Next: head}
	curr := dummy
	for curr.Next != nil {
		if curr.Next.Val == val {
			curr.Next = curr.Next.Next
		} else {
			curr = curr.Next
		}
	}
	return dummy.Next
}

// removeElementsNoDummyCareful strips matches off the front with a for loop
// (correctly handling a RUN of matching heads), then walks the rest.
// Correct, but two code paths instead of one.
func removeElementsNoDummyCareful(head *ListNode, val int) *ListNode {
	for head != nil && head.Val == val {
		head = head.Next
	}
	if head == nil {
		return nil
	}
	curr := head
	for curr.Next != nil {
		if curr.Next.Val == val {
			curr.Next = curr.Next.Next
		} else {
			curr = curr.Next
		}
	}
	return head
}

// removeElementsNaiveBroken is BROKEN ON PURPOSE — strips only ONE matching
// node off the front (an `if`, not a `for`), so a RUN of matching values at
// the head is not fully removed.
func removeElementsNaiveBroken(head *ListNode, val int) *ListNode {
	if head != nil && head.Val == val { // only strips ONE, not a run
		head = head.Next
	}
	if head == nil {
		return nil
	}
	curr := head
	for curr.Next != nil {
		if curr.Next.Val == val {
			curr.Next = curr.Next.Next
		} else {
			curr = curr.Next
		}
	}
	return head
}

// --- test scaffolding -------------------------------------------------------

func sliceToList(values []int) *ListNode {
	dummy := &ListNode{}
	curr := dummy
	for _, v := range values {
		curr.Next = &ListNode{Val: v}
		curr = curr.Next
	}
	return dummy.Next
}

func listToSlice(head *ListNode) []int {
	out := []int{}
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

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}

func main() {
	type testCase struct {
		values   []int
		val      int
		expected []int
	}
	cases := []testCase{
		{[]int{1, 2, 6, 3, 4, 5, 6}, 6, []int{1, 2, 3, 4, 5}},
		{[]int{}, 1, []int{}},
		{[]int{7, 7, 7, 7}, 7, []int{}},
		{[]int{1, 1, 1, 2}, 1, []int{2}},
		{[]int{2, 1, 1, 1}, 1, []int{2}},
		{[]int{1}, 1, []int{}},
		{[]int{1}, 2, []int{1}},
		{[]int{1, 2, 3}, 4, []int{1, 2, 3}},
		{[]int{6, 6, 6, 1}, 6, []int{1}},
	}

	allOK := true

	fmt.Println("--- correctness: dummy-head answer vs careful no-dummy variant ---")
	for _, tc := range cases {
		got := listToSlice(removeElements(sliceToList(tc.values), tc.val))
		got2 := listToSlice(removeElementsNoDummyCareful(sliceToList(tc.values), tc.val))
		ok := equalSlices(got, tc.expected) && equalSlices(got2, tc.expected)
		allOK = allOK && ok
		fmt.Printf("%s  head=%-24v val=%-3d -> %v  (want %v)\n",
			status(ok), tc.values, tc.val, got, tc.expected)
	}

	// --------------------------------------------------------------------
	// Live bug: naive (if, not for) front-strip on a run of head matches.
	// --------------------------------------------------------------------
	fmt.Println("\n--- naive (if, not for) front-strip vs dummy-head: live bug ---")
	type bugCase struct {
		values []int
		val    int
	}
	bugCases := []bugCase{
		{[]int{6, 6, 6, 1}, 6}, // THREE matching nodes at the head, in a row
		{[]int{9, 9, 2, 9}, 9}, // two matching at the head, one matching later
		{[]int{5}, 5},          // single matching node — still a "run of 1"
	}
	fmt.Printf("  %-16s %4s %12s %14s  ok?\n", "input", "val", "dummy-head", "naive (buggy)")
	bugReproduced := false
	for _, bc := range bugCases {
		correct := listToSlice(removeElements(sliceToList(bc.values), bc.val))
		broken := listToSlice(removeElementsNaiveBroken(sliceToList(bc.values), bc.val))
		mismatch := !equalSlices(correct, broken)
		bugReproduced = bugReproduced || mismatch
		note := "yes"
		if mismatch {
			note = "NO  <- naive leaves matches behind"
		}
		fmt.Printf("  %-16v %4d %12v %14v  %s\n", bc.values, bc.val, correct, broken, note)
	}
	fmt.Printf("  naive front-strip bug reproduced on a multi-match run: %v\n", bugReproduced)
	allOK = allOK && bugReproduced // we WANT to have proven the bug is real

	fmt.Println("\n  [6,6,6,1], val=6 traced through the naive (if, not for) version:")
	naiveResult := listToSlice(removeElementsNaiveBroken(sliceToList([]int{6, 6, 6, 1}), 6))
	dummyResult := listToSlice(removeElements(sliceToList([]int{6, 6, 6, 1}), 6))
	fmt.Printf("    naive result:      %v   <- WRONG, want [1]\n", naiveResult)
	fmt.Printf("    dummy-head result: %v   <- correct\n", dummyResult)

	// --------------------------------------------------------------------
	// Step-by-step trace, dummy-head version.
	// --------------------------------------------------------------------
	fmt.Println("\n--- trace: dummy-head removeElements([1,2,6,3,4,5,6], val=6) ---")
	head := sliceToList([]int{1, 2, 6, 3, 4, 5, 6})
	dummy := &ListNode{Next: head}
	curr := dummy
	step := 0
	for curr.Next != nil {
		step++
		target := curr.Next.Val
		action := "advance"
		if target == 6 {
			action = "SKIP (match)"
			curr.Next = curr.Next.Next
		} else {
			curr = curr.Next
		}
		fmt.Printf("  step %d: looked at %d -> %s\n", step, target, action)
	}
	fmt.Printf("  result: %v\n", listToSlice(dummy.Next))

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
