package main

import (
	"fmt"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 876 · Middle of the Linked List                      [Easy]
https://leetcode.com/problems/middle-of-the-linked-list/
================================================================================

THE CORE IDEA
--------------
"The middle" needs n/2, but a linked list has no index -- computing n means
one full walk. Floyd's slow/fast pointers (topic guide §3.1) collapse this to
a SINGLE pass: slow advances one node per iteration, fast advances two.
Because fast always covers exactly twice the distance slow does, the moment
fast falls off the end, slow has covered exactly half the list -- no length
precomputation needed.

    slow, fast := head, head
    for fast != nil && fast.Next != nil {
        slow = slow.Next
        fast = fast.Next.Next
    }
    return slow

O(n) time, O(1) space, one pass. The loop condition fast != nil &&
fast.Next != nil (rather than just fast != nil) is what makes this land on
the SECOND of the two middles for even-length lists -- exactly what LC 876
specifies.


================================================================================
APPROACH 0 · Collect into a slice, index len/2 (naive, priced not coded)
================================================================================
Correct, but O(n) EXTRA space for something the one-pass pointer approach
does in O(1) -- never the answer once the O(1) constraint is understood.

================================================================================
APPROACH 1 · Two-pass: count n, then walk n/2 steps (priced, coded below)
================================================================================
Also O(n) time and O(1) space -- asymptotically tied with the one-pass
version -- but it touches every node TWICE instead of once. Benchmarked below.

================================================================================
APPROACH 2 · Slow/fast, one pass ✅ (the answer)
================================================================================
    Time: O(n)     Space: O(1)


================================================================================
STEP BY STEP TRACE -- odd length: 1 -> 2 -> 3 -> 4 -> 5 -> nil
================================================================================
    slow=1 fast=1
    slow=2 fast=3
    slow=3 fast=5
    fast.Next is nil -> loop ends. slow = 3 (the true middle). ✓

STEP BY STEP TRACE -- even length: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> nil
    slow=1 fast=1
    slow=2 fast=3
    slow=3 fast=5
    fast (=5) is not nil but fast.Next(=6).Next is nil, so this iteration
    still runs: slow=4  fast=nil (5.Next.Next steps past the end)
    loop condition fast != nil -> false -> ends. slow = 4.
    That's the SECOND of the two middles (3, 4) -- exactly what LC 876 wants.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time   Space   Mutates input?  Note
    ---------------------------  -----  ------  ---------------  ----------------
    Collect into slice, index    O(n)   O(n)    no               wastes space
    Two-pass: count then walk    O(n)   O(1)    no               touches nodes TWICE
    Slow/fast, one pass ✅       O(n)   O(1)    no               the answer, ONE pass


================================================================================
EDGE CASES
================================================================================
    [1]      -> [1]     single node: fast.Next is nil immediately, loop body
                         never runs, slow stays at head.
    [1,2]    -> [2]     two nodes: exercises the even-length "second middle"
                         rule on the smallest possible case.
    [1,2,3]  -> [2,3]   smallest odd case beyond a single node.
    long list  -> the one-pass vs two-pass timing gap is measured below.


================================================================================
COMMON MISTAKES
================================================================================
1. Looping on `for fast != nil` instead of `for fast != nil && fast.Next !=
   nil` -- panics the moment fast.Next is nil and the code tries to read
   fast.Next.Next anyway. Same class of bug as 003's cycle detection.
2. Returning the FIRST of the two middles on an even-length list instead of
   the second -- happens if fast starts one step ahead of slow.
3. Precomputing n with one pass, then walking n/2 with a SECOND separate pass
   when a single-pass approach exists and is no more code.
4. Off-by-one translating "walk n/2 steps" into a loop bound in the two-pass
   approach.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the FIRST middle instead of the second, for even-length lists.
A: Start fast one node ahead of slow (fast = head.Next) before the loop.

Q: What if you needed the node just BEFORE the middle (to split the list)?
A: Track one extra pointer, prev, trailing slow by one step -- exactly what
   Reorder List (problem 008) needs.

Q: Could binary search find the middle faster?
A: No -- binary search needs O(1) random access to a midpoint, which a
   linked list never has.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 141  Linked List Cycle              -- same slow/fast SHAPE, different
                                             stopping condition
    LC 143  Reorder List                    -- needs the middle as step 1
    LC 234  Palindrome Linked List          -- needs the middle as step 1 (007)
    LC 19   Remove Nth Node From End         -- a different two-pointer GAP
                                             pattern, not slow/fast
================================================================================
*/

// middleNode is the interview answer: slow/fast pointers, one pass.
// O(n) time, O(1) space.
func middleNode(head *ListNode) *ListNode {
	slow, fast := head, head
	for fast != nil && fast.Next != nil {
		slow = slow.Next
		fast = fast.Next.Next
	}
	return slow
}

// middleNodeTwoPass counts n, then walks n/2 steps. Same O(n)/O(1)
// complexity class, but touches every node TWICE.
func middleNodeTwoPass(head *ListNode) *ListNode {
	n := 0
	for node := head; node != nil; node = node.Next {
		n++
	}
	node := head
	for i := 0; i < n/2; i++ {
		node = node.Next
	}
	return node
}

// middleNodeCollect is the naive baseline: collect every node into a slice,
// O(n) extra space.
func middleNodeCollect(head *ListNode) *ListNode {
	var nodes []*ListNode
	for node := head; node != nil; node = node.Next {
		nodes = append(nodes, node)
	}
	return nodes[len(nodes)/2]
}

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
	var out []int
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

func main() {
	type tc struct {
		values []int
		want   []int
	}
	cases := []tc{
		{[]int{1, 2, 3, 4, 5}, []int{3, 4, 5}},
		{[]int{1, 2, 3, 4, 5, 6}, []int{4, 5, 6}},
		{[]int{1}, []int{1}},
		{[]int{1, 2}, []int{2}},
		{[]int{1, 2, 3}, []int{2, 3}},
	}
	rangeCase := make([]int, 20)
	for i := range rangeCase {
		rangeCase[i] = i + 1
	}
	cases = append(cases, tc{rangeCase, rangeCase[10:]})

	allOK := true
	fmt.Println("--- correctness: slow/fast, one pass ---")
	for _, c := range cases {
		got := toSlice(middleNode(buildList(c.values)))
		ok := equalSlices(got, c.want)
		allOK = allOK && ok
		fmt.Printf("%s  n=%-3d -> %v  (want %v)\n", status(ok), len(c.values), got, c.want)
	}

	fmt.Println("\n--- correctness: two-pass count-then-walk, cross-checked ---")
	for _, c := range cases {
		got := toSlice(middleNodeTwoPass(buildList(c.values)))
		ok := equalSlices(got, c.want)
		allOK = allOK && ok
		fmt.Printf("%s  n=%-3d -> %v  (want %v)\n", status(ok), len(c.values), got, c.want)
	}

	fmt.Println("\n--- correctness: naive collect-into-slice, cross-checked ---")
	for _, c := range cases {
		got := toSlice(middleNodeCollect(buildList(c.values)))
		ok := equalSlices(got, c.want)
		allOK = allOK && ok
		fmt.Printf("%s  n=%-3d -> %v  (want %v)\n", status(ok), len(c.values), got, c.want)
	}

	// ------------------------------------------------------------------
	// Step-by-step trace, odd and even.
	// ------------------------------------------------------------------
	for _, values := range [][]int{{1, 2, 3, 4, 5}, {1, 2, 3, 4, 5, 6}} {
		parity := "odd"
		if len(values)%2 == 0 {
			parity = "even"
		}
		fmt.Printf("\n--- trace: %v (%s length) ---\n", values, parity)
		slow, fast := buildList(values), buildList(values)
		step := 0
		for fast != nil && fast.Next != nil {
			slow = slow.Next
			fast = fast.Next.Next
			fastVal := "nil"
			if fast != nil {
				fastVal = fmt.Sprintf("%d", fast.Val)
			}
			fmt.Printf("  step %d: slow=%d  fast=%s\n", step, slow.Val, fastVal)
			step++
		}
		fmt.Printf("  middle: %d\n", slow.Val)
	}

	// ------------------------------------------------------------------
	// Benchmark: one pass vs two passes over the same list, measured.
	// ------------------------------------------------------------------
	fmt.Println("\n--- one-pass slow/fast vs two-pass count-then-walk: measured runtime ---")
	fmt.Printf("  %9s %12s %12s %8s\n", "n", "one-pass", "two-pass", "ratio")
	for _, n := range []int{50_000, 200_000, 800_000} {
		values := make([]int, n)
		for i := range values {
			values[i] = i
		}
		head := buildList(values)
		t0 := time.Now()
		middleNode(head)
		t1 := time.Now()
		head2 := buildList(values)
		middleNodeTwoPass(head2)
		t2 := time.Now()
		oneDur := t1.Sub(t0)
		twoDur := t2.Sub(t1)
		ratio := float64(twoDur) / float64(oneDur)
		fmt.Printf("  %9d %11v %11v %7.2fx\n", n, oneDur, twoDur, ratio)
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
