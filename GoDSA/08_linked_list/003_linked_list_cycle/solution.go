package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 141 · Linked List Cycle                              [Easy]
https://leetcode.com/problems/linked-list-cycle/
================================================================================

THE CORE IDEA
--------------
Floyd's tortoise-and-hare: walk the list with two pointers at different
speeds, slow one step per iteration and fast two. If there's no cycle, fast
simply reaches nil (or a node whose Next is nil) and the walk ends normally.
If there IS a cycle, once slow enters it, fast is moving twice as fast around
the SAME finite loop, so the gap between them (measured forward, around the
cycle) shrinks by exactly 1 every step -- g, g-1, g-2, ..., 1, 0 -- and cannot
skip past 0 (topic guide §3.2). slow == fast becoming true is therefore
GUARANTEED inside a cycle, and IMPOSSIBLE without one.

    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
        if slow == fast {   // pointer identity, not value equality
            return true
        }
    }
    return false

O(n) time, O(1) space -- no visited-set needed.


================================================================================
APPROACH 0 · Visited set of node identity (baseline, priced not coded here)
================================================================================
Walk with a single pointer, remembering every visited node's pointer value in
a map[*ListNode]bool. The moment a node is about to be revisited, there's a
cycle. Correct, O(n) time, but O(n) SPACE -- exactly what the follow-up asks
to avoid.

================================================================================
APPROACH 1 · Floyd's slow/fast ✅ (the answer)
================================================================================
    Time: O(n)     Space: O(1)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time   Space   Mutates input?   Note
    -------------------------  -----  ------  ---------------  ----------------
    Visited set of identity    O(n)   O(n)    no               simple, extra memory
    Floyd's slow/fast ✅       O(n)   O(1)    no               the answer


================================================================================
EDGE CASES
================================================================================
    nil                    -> false   head is nil; loop body never runs.
    [1], no cycle           -> false   single node, fast.Next is nil immediately.
    [1], self-loop            -> true    tail.Next points at itself; fast catches
                                        up to slow within one lap.
    [1,2], cycle at 0          -> true    smallest real cycle: two nodes, tail
                                        points back at the first.
    long list, cycle near end    -> exercises many iterations before slow
                                        enters the cycle at all -- still meets.


================================================================================
COMMON MISTAKES
================================================================================
1. Guarding only fast (not fast.Next), or checking in the wrong order, before
   computing fast.Next.Next -- Go panics with "runtime error: invalid memory
   address or nil pointer dereference" the instant fast lands on a node whose
   Next is nil. Demonstrated live below (recovered via defer/recover).
2. Comparing slow.Val == fast.Val instead of slow == fast -- two DIFFERENT
   nodes can legitimately hold equal Val fields; only pointer identity proves
   they're the same node.
3. Starting fast one step ahead of slow "to save an iteration" -- still works
   for yes/no detection, but changes the exact meeting point needed by the
   cycle-START algorithm (LC 142). Start both at head.
4. Using a set of node.Val instead of node identity for the O(n)-space
   alternative -- two different nodes with the same value would falsely
   register as "already visited."


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Not just whether there's a cycle -- find the node where it BEGINS (LC 142).
A: After slow/fast first meet, restart one pointer at head, move both one
   step at a time; they meet again exactly at the cycle's entry node.

Q: What's the length of the cycle?
A: Once slow/fast meet, keep one pointer fixed and walk the other around the
   cycle, counting steps until it returns to the fixed pointer's node.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 142  Linked List Cycle II         -- find the cycle's start node
    LC 202  Happy Number                  -- same algorithm on an implicit list
                                           formed by digit-square-sum
    LC 287  Find the Duplicate Number     -- array-as-implicit-linked-list,
                                           Floyd's reused (problem 012)
================================================================================
*/

// hasCycle is the interview answer: Floyd's tortoise-and-hare.
// O(n) time, O(1) space.
func hasCycle(head *ListNode) bool {
	slow, fast := head, head
	for fast != nil && fast.Next != nil {
		slow = slow.Next
		fast = fast.Next.Next
		if slow == fast {
			return true
		}
	}
	return false
}

// hasCycleVisitedSet is the O(n)-space alternative: remember every visited
// node's identity in a map.
func hasCycleVisitedSet(head *ListNode) bool {
	seen := make(map[*ListNode]bool)
	node := head
	for node != nil {
		if seen[node] {
			return true
		}
		seen[node] = true
		node = node.Next
	}
	return false
}

// hasCycleUnguarded is BROKEN ON PURPOSE -- missing the fast.Next guard
// before fast.Next.Next. Panics on any acyclic list whose length has the
// wrong parity relative to where fast lands.
func hasCycleUnguarded(head *ListNode) bool {
	slow, fast := head, head
	for fast != nil { // <-- missing `&& fast.Next != nil`
		slow = slow.Next
		fast = fast.Next.Next // <-- panics when fast.Next is nil
		if slow == fast {
			return true
		}
	}
	return false
}

// buildCyclicList builds a list from values; pos == -1 means no cycle,
// otherwise the tail's Next points at the node at index pos.
func buildCyclicList(values []int, pos int) *ListNode {
	if len(values) == 0 {
		return nil
	}
	nodes := make([]*ListNode, len(values))
	for i, v := range values {
		nodes[i] = &ListNode{Val: v}
	}
	for i := 0; i < len(nodes)-1; i++ {
		nodes[i].Next = nodes[i+1]
	}
	if pos != -1 {
		nodes[len(nodes)-1].Next = nodes[pos]
	}
	return nodes[0]
}

func main() {
	type tc struct {
		values []int
		pos    int
		want   bool
	}
	cases := []tc{
		{[]int{3, 2, 0, -4}, 1, true},
		{[]int{1, 2}, 0, true},
		{[]int{1}, -1, false},
		{[]int{}, -1, false},
		{[]int{1}, 0, true},
		{[]int{1, 2, 3, 4}, -1, false},
		{[]int{1, 2, 3, 4, 5}, 4, true}, // self-loop on tail
	}

	allOK := true
	fmt.Println("--- correctness: Floyd's slow/fast ---")
	for _, c := range cases {
		got := hasCycle(buildCyclicList(c.values, c.pos))
		ok := got == c.want
		allOK = allOK && ok
		fmt.Printf("%s  values=%-20v pos=%-3d -> %v  (want %v)\n", status(ok), c.values, c.pos, got, c.want)
	}

	fmt.Println("\n--- correctness: visited-set O(n)-space alternative, cross-checked ---")
	for _, c := range cases {
		got := hasCycleVisitedSet(buildCyclicList(c.values, c.pos))
		ok := got == c.want
		allOK = allOK && ok
		fmt.Printf("%s  values=%-20v pos=%-3d -> %v  (want %v)\n", status(ok), c.values, c.pos, got, c.want)
	}

	// ------------------------------------------------------------------
	// Live panic demo: unguarded fast.Next.Next, recovered.
	// ------------------------------------------------------------------
	fmt.Println("\n--- live demo: unguarded fast.Next.Next panics (recovered) ---")
	noCycleList := buildCyclicList([]int{1, 2, 3, 4, 5}, -1) // odd length, no cycle
	fmt.Println("  input: 1 -> 2 -> 3 -> 4 -> 5 -> nil  (no cycle, odd length)")
	panicked := false
	var panicMsg interface{}
	func() {
		defer func() {
			if r := recover(); r != nil {
				panicked = true
				panicMsg = r
			}
		}()
		hasCycleUnguarded(noCycleList)
	}()
	if panicked {
		fmt.Printf("  hasCycleUnguarded PANICKED (caught live): %v\n", panicMsg)
	} else {
		fmt.Println("  hasCycleUnguarded did NOT panic -- unexpected")
	}

	correctList := buildCyclicList([]int{1, 2, 3, 4, 5}, -1)
	correctResult := hasCycle(correctList)
	fmt.Printf("  hasCycle (guarded)          -> %v   <- correct, no panic\n", correctResult)
	allOK = allOK && panicked && correctResult == false

	// ------------------------------------------------------------------
	// Step-by-step trace.
	// ------------------------------------------------------------------
	fmt.Println("\n--- trace: 3 -> 2 -> 0 -> -4 -> (back to 2) ---")
	head := buildCyclicList([]int{3, 2, 0, -4}, 1)
	slow, fast := head, head
	step := 0
	for fast != nil && fast.Next != nil {
		slow = slow.Next
		fast = fast.Next.Next
		fastVal := "nil"
		if fast != nil {
			fastVal = fmt.Sprintf("%d", fast.Val)
		}
		fmt.Printf("  step %d: slow=%d  fast=%s  same node? %v\n", step, slow.Val, fastVal, slow == fast)
		if slow == fast {
			break
		}
		step++
	}
	fmt.Printf("  cycle detected: %v\n", slow == fast)

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
