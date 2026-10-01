package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 206 · Reverse Linked List                            [Easy]
https://leetcode.com/problems/reverse-linked-list/
================================================================================

THE CORE IDEA
-------------
Reversal is a walk that rewires each node's Next to point BACKWARD instead
of forward, one node at a time. The whole difficulty is bookkeeping, not
algorithm: the instant `curr.Next = prev` runs, the only pointer this
program held onto "the rest of the original list" is gone — so it must be
saved into a local variable FIRST.

    var prev *ListNode          // nil — becomes the new tail's Next
    curr := head
    for curr != nil {
        next := curr.Next       // 1. SAVE first
        curr.Next = prev        // 2. REWIRE (destroys the original Next)
        prev = curr              // 3. ADVANCE prev
        curr = next                // 4. ADVANCE curr using the SAVED reference
    }
    return prev

O(n) time, O(1) space — no recursion frame, no auxiliary structure.


================================================================================
APPROACH 1 · Iterative three-pointer ✅ (the answer)
================================================================================
Shown above. O(n) time, O(1) space, in place.


================================================================================
APPROACH 2 · Recursive
================================================================================
    func reverseListRecursive(head *ListNode) *ListNode {
        if head == nil || head.Next == nil {
            return head
        }
        newHead := reverseListRecursive(head.Next)
        head.Next.Next = head   // the node after head now points BACK at head
        head.Next = nil         // sever head's old forward link
        return newHead
    }

Same O(n) time, but O(n) STACK FRAMES — one per node. Go has no tail-call
optimization (this isn't even tail-recursive: work happens AFTER the
recursive call returns), so every frame genuinely stays on the stack.
Goroutine stacks grow dynamically (starting around 8KB, expanding as
needed), which is far more forgiving than a language with a fixed 1MB
thread stack — but it is still O(n) memory for an O(n)-length list, strictly
worse than the iterative O(1) version, and an adversarially long list can
still exhaust it. Default to iterative for linked-list problems in Go.


================================================================================
STEP BY STEP TRACE
================================================================================
head = 1 -> 2 -> 3 -> nil

Before:  nil <- prev   curr
                         [1] -> [2] -> [3] -> nil

step 1:  next = [2]
step 2:  [1].Next = nil       prev=nil  curr=[1]
         nil <- [1]                     [1].Next is now nil (severed)
step 3:  prev = [1]
step 4:  curr = [2]

Repeat:  nil <- [1] <- [2]          [3] -> nil
                         prev=[1] curr=[2]
         next=[3]; [2].Next=[1]; prev=[2]; curr=[3]

Repeat:  nil <- [1] <- [2] <- [3]         nil
                                prev=[3] curr=nil (loop ends, next=nil)

return prev = [3] -> [2] -> [1] -> nil


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time    Space   Mutates input?  Note
    -------------------------  ------  ------  ---------------  ----------------------
    Copy to slice, rebuild     O(n)    O(n)    no               throws away the point
    Iterative (3-pointer) ✅   O(n)    O(1)    yes (rewires Next)  the answer
    Recursive                  O(n)    O(n)    yes              stack depth = list length


================================================================================
EDGE CASES
================================================================================
    nil (empty list)  -> nil     head is nil; loop body never runs, returns nil.
    single node         -> unchanged, only Next=nil confirmed (already was).
    two nodes            -> smallest case that actually exercises the swap.
    long list             -> exercises the stack-depth gap between iterative
                            and recursive; demoed below.


================================================================================
COMMON MISTAKES
================================================================================
1. Overwriting `curr.Next` BEFORE saving it (`next := curr.Next` must be the
   FIRST line of the loop body) — silently truncates the list instead of
   crashing, exactly like the Python guide's mistake #1.

2. Returning `head` instead of `prev` — `head` still refers to the OLD
   first node, which after reversal is the new TAIL.

3. Forgetting `head.Next = nil` in the recursive version — leaves a stray
   forward pointer that turns the result into a CYCLE, and keeps the old
   suffix reachable via a link nothing else expects (topic guide Part 1.2's
   "leak via reachability").

4. Choosing recursion by default for long lists without naming the O(n)
   stack-frame cost out loud — Go's growable stacks make this more forgiving
   than a fixed-stack language, but it is still real memory, demoed below.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Implement it recursively too.
A: See Approach 2 above; name the O(n) stack cost explicitly.

Q: Reverse only nodes between positions left and right (LC 92).
A: Walk to the node before `left`, run this exact loop for
   `right - left + 1` iterations starting there, splice back in using a
   dummy head so `left == 1` isn't a special case.

Q: Reverse in groups of k (LC 25).
A: Run this exact loop on bounded windows of length k, repeatedly, with
   bookkeeping to reconnect each reversed group to its neighbors.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 92   Reverse Linked List II       — reverse a bounded sub-range
    LC 25   Reverse Nodes in k-Group      — this loop applied repeatedly
    LC 143  Reorder List                  — this + find-middle + merge
    LC 234  Palindrome Linked List        — this + find-middle + compare
================================================================================
*/

// reverseList is the interview answer: iterative three-pointer reversal.
// Time O(n), space O(1).
func reverseList(head *ListNode) *ListNode {
	var prev *ListNode
	curr := head
	for curr != nil {
		next := curr.Next // 1. SAVE first
		curr.Next = prev  // 2. REWIRE
		prev = curr       // 3. ADVANCE prev
		curr = next       // 4. ADVANCE curr
	}
	return prev
}

// reverseListRecursive reverses everything after head, then splices head
// onto the back. Time O(n), space O(n) — one stack frame per node.
func reverseListRecursive(head *ListNode) *ListNode {
	if head == nil || head.Next == nil {
		return head
	}
	newHead := reverseListRecursive(head.Next)
	head.Next.Next = head // the node after head now points BACK at head
	head.Next = nil       // sever head's old forward link
	return newHead
}

// reverseBroken is BROKEN ON PURPOSE — overwrites curr.Next before saving
// it. Silently truncates the list instead of crashing.
func reverseBroken(head *ListNode) *ListNode {
	var prev *ListNode
	curr := head
	for curr != nil {
		curr.Next = prev // <-- destroys our only reference onward
		prev = curr
		curr = curr.Next // <-- reads the value JUST written above
	}
	return prev
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
	seen := map[*ListNode]bool{}
	for head != nil && !seen[head] { // guard against an accidental cycle
		seen[head] = true
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

func reversedSlice(values []int) []int {
	out := make([]int, len(values))
	for i, v := range values {
		out[len(values)-1-i] = v
	}
	return out
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}

func main() {
	cases := [][]int{
		{1, 2, 3, 4, 5},
		{1, 2},
		{},
		{1},
		{1, 2, 3},
	}

	allOK := true

	fmt.Println("--- correctness: iterative reversal ---")
	for _, values := range cases {
		want := reversedSlice(values)
		got := toSlice(reverseList(buildList(values)))
		ok := equalSlices(got, want)
		allOK = allOK && ok
		fmt.Printf("%s  %-20v -> %v  (want %v)\n", status(ok), values, got, want)
	}

	fmt.Println("\n--- correctness: recursive reversal, cross-checked against iterative ---")
	for _, values := range cases {
		want := toSlice(reverseList(buildList(values)))
		got := toSlice(reverseListRecursive(buildList(values)))
		ok := equalSlices(got, want)
		allOK = allOK && ok
		fmt.Printf("%s  %-20v -> %v  (want %v)\n", status(ok), values, got, want)
	}

	// -------------------------------------------------------------------
	// The #1 mistake, demonstrated LIVE on a real list.
	// -------------------------------------------------------------------
	fmt.Println("\n--- the #1 mistake — overwrite-before-save ---")
	original := []int{1, 2, 3, 4, 5}
	brokenResult := toSlice(reverseBroken(buildList(original))) // fresh, independent copy
	fmt.Printf("  input:          %v\n", original)
	fmt.Printf("  reverseBroken -> %v   <- WRONG: truncated, not a real reversal\n", brokenResult)

	correctResult := toSlice(reverseList(buildList(original))) // second, untouched copy
	fmt.Printf("  reverseList   -> %v   <- correct\n", correctResult)

	truncated := !equalSlices(brokenResult, reversedSlice(original)) && len(brokenResult) < len(original)
	fmt.Printf("  broken version actually truncated the list: %v\n", truncated)
	allOK = allOK && truncated

	// -------------------------------------------------------------------
	// Step-by-step trace, small list.
	// -------------------------------------------------------------------
	fmt.Println("\n--- trace: head = 1 -> 2 -> 3 -> nil ---")
	var prev *ListNode
	curr := buildList([]int{1, 2, 3})
	step := 0
	for curr != nil {
		next := curr.Next
		nextVal := "nil"
		if next != nil {
			nextVal = fmt.Sprintf("%d", next.Val)
		}
		prevVal := "nil"
		if prev != nil {
			prevVal = fmt.Sprintf("%d", prev.Val)
		}
		fmt.Printf("  step %d: next=%s  before-rewire curr=%d  prev=%s\n", step, nextVal, curr.Val, prevVal)
		curr.Next = prev
		prev = curr
		curr = next
		step++
	}
	fmt.Printf("  final: %v\n", toSlice(prev))

	// -------------------------------------------------------------------
	// Iterative vs recursive: stack depth on a long list.
	// -------------------------------------------------------------------
	fmt.Println("\n--- iterative vs recursive: stack depth on a long list ---")
	longN := 500_000
	longValues := make([]int, longN)
	for i := range longValues {
		longValues[i] = i
	}
	iterResult := toSlice(reverseList(buildList(longValues)))
	iterOK := equalSlices(iterResult, reversedSlice(longValues))
	fmt.Printf("  iterative on n=%d: succeeded, correct=%v (O(1) space, no stack growth)\n", longN, iterOK)

	recResult := toSlice(reverseListRecursive(buildList(longValues)))
	recOK := equalSlices(recResult, reversedSlice(longValues))
	fmt.Printf("  recursive on n=%d: succeeded, correct=%v (O(n) stack frames — Go's\n", longN, recOK)
	fmt.Println("    growable goroutine stack absorbs this, but it is real memory the")
	fmt.Println("    iterative version never touches; an adversarially larger n can still")
	fmt.Println("    exceed the runtime's maximum stack size and crash the program)")
	allOK = allOK && iterOK && recOK

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
