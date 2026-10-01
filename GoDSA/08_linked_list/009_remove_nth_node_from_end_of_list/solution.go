package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 19 · Remove Nth Node From End of List              [Medium]
https://leetcode.com/problems/remove-nth-node-from-end-of-list/
================================================================================

THE CORE IDEA
-------------
Fixed-gap two pointers: open a gap of n nodes between `fast` and `slow`
first, then walk both together. When `fast` reaches the LAST node, `slow` is
exactly n nodes behind it — i.e. right before the target. A dummy node lets
"remove the head" (n == length) use the exact same one-line rewire as every
other case:

    dummy := &ListNode{Next: head}
    fast, slow := dummy, dummy
    for i := 0; i < n; i++ {
        fast = fast.Next
    }
    for fast.Next != nil {
        fast = fast.Next
        slow = slow.Next
    }
    slow.Next = slow.Next.Next
    return dummy.Next


================================================================================
APPROACH 1 · Two-pass (state it, price it)
================================================================================
Count the length in one pass, then walk `length-n` steps from a dummy in a
second pass to reach the predecessor. Same O(L) time complexity, O(1) space,
but TWO traversals instead of one — the follow-up wants one pass.


================================================================================
APPROACH 2 · Fixed-gap two pointers ✅ (the answer, one pass)
================================================================================
See THE CORE IDEA. O(L) time, ONE traversal, O(1) space.


================================================================================
STEP BY STEP TRACE
================================================================================
head = [1,2,3,4,5], n = 2

    dummy -> [1] -> [2] -> [3] -> [4] -> [5] -> nil
      ^
    fast = slow = dummy

Phase 1 — open gap of 2:
    fast=[1], fast=[2]

    dummy -> [1] -> [2] -> [3] -> [4] -> [5] -> nil
                      ^fast
      ^slow

Phase 2 — walk together while fast.Next != nil:
    fast.Next=[3]!=nil -> fast=[3], slow=[1]
    fast.Next=[4]!=nil -> fast=[4], slow=[2]
    fast.Next=[5]!=nil -> fast=[5], slow=[3]
    fast.Next=nil -> STOP

    dummy -> [1] -> [2] -> [3] -> [4] -> [5] -> nil
                              ^slow           ^fast(last)

Phase 3 — unlink: slow.Next = slow.Next.Next  (skip over [4])
    dummy -> [1] -> [2] -> [3] -> [5] -> nil

return dummy.Next = [1,2,3,5]   correct


HEAD-REMOVAL TRACE — n == length
------------------------------------------------------------------------------
head = [1,2,3], n = 3

    dummy -> [1] -> [2] -> [3] -> nil
      ^fast=slow

Phase 1 — open gap of 3: fast=[1], fast=[2], fast=[3]
    dummy -> [1] -> [2] -> [3] -> nil
                              ^fast
      ^slow (still dummy)

Phase 2 — fast.Next is already nil -> loop body never runs.

Phase 3 — unlink: dummy.Next = dummy.Next.Next  ([1].Next = [2])
    dummy -> [2] -> [3] -> nil

return [2,3]   the real head (1) removed with zero special-case branching.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time    Space   Mutates input?   Passes
    ---------------------------  ------  ------  ---------------  -------
    Two-pass (count then walk)   O(L)    O(1)    yes (rewires)    2
    Fixed-gap two pointers  ✅   O(L)    O(1)    yes (rewires)    1


================================================================================
EDGE CASES
================================================================================
    [1], n=1               -> nil.        Single node, remove the only node.
    n == length              -> target IS the head; dummy handles it with no
                                special-case branch (traced above).
    n == 1                    -> removes the LAST node.
    Constraints guarantee 1 <= n <= sz, so out-of-range n is out of scope.


================================================================================
COMMON MISTAKES
================================================================================
1. Opening the gap n-1 steps instead of n (off-by-one) — removes the wrong
   node, or panics dereferencing a nil `fast.Next` in phase 2.
2. Forgetting the dummy node and special-casing n == length separately.
3. `for fast != nil` instead of `for fast.Next != nil` in phase 2 — walks
   one node too far, deleting the wrong node.
4. Returning `head` instead of `dummy.Next` — wrong when the original head
   was itself removed.
5. Not guarding a nil `*ListNode` before calling `.Next` on it — Go panics
   immediately on that dereference (see the Go topic guide Part 1.3), unlike
   silently producing wrong output.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Could you do this in one pass?
A: Yes — the fixed-gap two-pointer trick. State two-pass first, then show
   the gap trick removes the second traversal.

Q: What if n could be invalid (larger than the list length)?
A: Guard `fast` for nil while opening the gap and return an error or the
   unmodified list, since Go has no exceptions to rely on implicitly.

Q: Can you do it recursively?
A: Yes, recursing to the tail and counting depth on the way back — but that
   costs O(L) stack frames instead of O(1), and Go's default goroutine stack
   grows dynamically, so it won't overflow like C's fixed stack would, but
   it's still worse asymptotically in space.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 876  Middle of the Linked List   — slow/fast SAME start, not a gap
    LC 141  Linked List Cycle           — slow/fast, identity/pointer compare
    LC 2    Add Two Numbers             — dummy head, different shape (011)
================================================================================
*/

// removeNthFromEnd is the interview answer: fixed-gap two pointers with a
// dummy head. O(L) time, ONE pass, O(1) space.
func removeNthFromEnd(head *ListNode, n int) *ListNode {
	dummy := &ListNode{Next: head}
	fast, slow := dummy, dummy
	for i := 0; i < n; i++ {
		fast = fast.Next
	}
	for fast.Next != nil {
		fast = fast.Next
		slow = slow.Next
	}
	slow.Next = slow.Next.Next
	return dummy.Next
}

// removeNthFromEndTwoPass is the two-pass oracle: count length, then walk to
// the predecessor. O(L) time (two traversals), O(1) space.
func removeNthFromEndTwoPass(head *ListNode, n int) *ListNode {
	length := 0
	for node := head; node != nil; node = node.Next {
		length++
	}
	dummy := &ListNode{Next: head}
	node := dummy
	for i := 0; i < length-n; i++ {
		node = node.Next
	}
	node.Next = node.Next.Next
	return dummy.Next
}

// removeNthFromEndOffByOne is ✗ BROKEN ON PURPOSE — opens the gap with n-1
// steps instead of n. Deletes the wrong node (or panics). See mistake #1.
func removeNthFromEndOffByOne(head *ListNode, n int) *ListNode {
	dummy := &ListNode{Next: head}
	fast, slow := dummy, dummy
	for i := 0; i < n-1; i++ { // WRONG: should be n
		fast = fast.Next
	}
	for fast.Next != nil {
		fast = fast.Next
		slow = slow.Next
	}
	slow.Next = slow.Next.Next
	return dummy.Next
}

// --- test helpers ---

func buildList(values []int) *ListNode {
	dummy := &ListNode{}
	curr := dummy
	for _, v := range values {
		curr.Next = &ListNode{Val: v}
		curr = curr.Next
	}
	return dummy.Next
}

func toSlice(head *ListNode) []int {
	out := []int{}
	for node := head; node != nil; node = node.Next {
		out = append(out, node.Val)
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

type testCase struct {
	values   []int
	n        int
	expected []int
}

func main() {
	cases := []testCase{
		{[]int{1, 2, 3, 4, 5}, 2, []int{1, 2, 3, 5}},
		{[]int{1}, 1, []int{}},
		{[]int{1, 2}, 1, []int{1}},
		{[]int{1, 2}, 2, []int{2}},
		{[]int{1, 2, 3, 4, 5}, 5, []int{2, 3, 4, 5}},
		{[]int{1, 2, 3}, 3, []int{2, 3}},
		{[]int{1, 2, 3}, 1, []int{1, 2}},
	}

	allOK := true

	fmt.Println("--- correctness: one-pass gap-trick vs two-pass oracle ---")
	for _, tc := range cases {
		got1 := toSlice(removeNthFromEnd(buildList(tc.values), tc.n))
		got2 := toSlice(removeNthFromEndTwoPass(buildList(tc.values), tc.n))
		ok := equalSlices(got1, tc.expected) && equalSlices(got2, tc.expected)
		allOK = allOK && ok
		fmt.Printf("%s  values=%v n=%d -> one-pass=%v two-pass=%v (want %v)\n",
			status(ok), tc.values, tc.n, got1, got2, tc.expected)
	}

	fmt.Println("\n--- trace: head = [1,2,3], n=3 (removing the HEAD via the dummy) ---")
	head := buildList([]int{1, 2, 3})
	dummy := &ListNode{Next: head}
	fast, slow := dummy, dummy
	fmt.Printf("  dummy -> %v\n", toSlice(dummy.Next))
	for i := 0; i < 3; i++ {
		fast = fast.Next
		fmt.Printf("  gap-open step %d: fast now at val=%d\n", i+1, fast.Val)
	}
	fmt.Printf("  fast.Next == nil: %v -> phase-2 loop body never runs\n", fast.Next == nil)
	slow.Next = slow.Next.Next
	fmt.Printf("  after unlink: dummy.Next -> %v\n", toSlice(dummy.Next))
	traceOK := equalSlices(toSlice(dummy.Next), []int{2, 3})
	allOK = allOK && traceOK
	fmt.Printf("  matches expected [2,3]: %v\n", traceOK)

	fmt.Println("\n--- off-by-one on gap size: n vs n-1 steps (common mistake #1) ---")
	offByOneMismatch := false
	offCases := []testCase{
		{[]int{1, 2, 3, 4, 5}, 2, []int{1, 2, 3, 5}},
		{[]int{1, 2, 3}, 1, []int{1, 2}},
	}
	for _, tc := range offCases {
		good := toSlice(removeNthFromEnd(buildList(tc.values), tc.n))
		bad := runSafely(func() []int {
			return toSlice(removeNthFromEndOffByOne(buildList(tc.values), tc.n))
		})
		mismatch := !equalSlices(good, bad)
		offByOneMismatch = offByOneMismatch || mismatch
		verdict := "NO  <- wrong node removed"
		if !mismatch {
			verdict = "yes"
		}
		fmt.Printf("  values=%-16v n=%d correct=%-12v broken=%-16v  %s\n",
			tc.values, tc.n, good, bad, verdict)
	}
	fmt.Printf("  off-by-one bug reproduced: %v\n", offByOneMismatch)
	allOK = allOK && offByOneMismatch

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}

// runSafely recovers from a nil-pointer panic in the deliberately broken
// off-by-one variant (which can walk fast.Next off the end) and reports it
// as a distinguishable sentinel slice instead of crashing the whole test run.
func runSafely(f func() []int) (result []int) {
	defer func() {
		if r := recover(); r != nil {
			result = []int{-999999} // sentinel: panicked
		}
	}()
	return f()
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}
