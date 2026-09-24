package main

import (
	"fmt"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 25 · Reverse Nodes in k-Group                        [Hard]
https://leetcode.com/problems/reverse-nodes-in-k-group/
================================================================================

THE CORE IDEA
--------------
This is topic problem 001's iterative reversal (prev/curr/next) applied
repeatedly to consecutive GROUPS of k nodes, with the groups relinked to
each other afterward. The sharp edge, and the entire reason this is rated
Hard rather than Medium: the LAST group may have fewer than k nodes, and
the spec says leave it AS IS, unreversed — so you must know whether k nodes
remain BEFORE committing to reverse them.


================================================================================
APPROACH 1 · Copy values into a slice, rewrite in k-reversed chunks (priced,
not coded — violates "only nodes may be changed", named to rule it out)
================================================================================
Walk the list once collecting .Val into a slice, reverse each k-length
chunk of the slice, walk the list again writing values back. This produces
the correct VALUE sequence but rewrites .Val on the ORIGINAL node objects
instead of relinking .Next — the problem explicitly forbids this ("only
nodes themselves may be changed"), and it defeats the point of a
linked-list topic (pointer rewiring, not value shuffling). Named here only
to rule it out, exactly like reorder list's common mistake #6.

    Time: O(n)     Space: O(n) for the slice — and disallowed by the
                    problem's own constraint regardless of space.


================================================================================
APPROACH 2 · Iterative, group by group, with a look-ahead count ✅ (the answer)
================================================================================
Use a dummy head so the first group is not a special case (topic guide §2).
Maintain `groupPrev`, the node just before the current group (initially the
dummy). For each group:

    1. COUNT AHEAD: walk k steps from groupPrev.Next; if you run off the
       end before counting k nodes, STOP — fewer than k nodes remain, leave
       them as-is, return dummy.Next.
    2. REVERSE exactly those k nodes with the standard prev/curr/next
       three-pointer dance (topic guide §4.1), stopping after k iterations
       (not when curr == nil, since curr continues past the group).
    3. RELINK: groupPrev.Next must now point at the new group head (what
       was the group's LAST node before reversal); the group's ORIGINAL
       first node (now the group's TAIL after reversal) must point at
       whatever comes next — either the start of the next group, or the
       untouched remainder.
    4. Advance groupPrev to the (former-first, now-tail) node and repeat.

    Time: O(n)     Space: O(1) extra


================================================================================
APPROACH 3 · Recursive ✅ (variant — matches the topic guide's Part 4.2 note
that recursion is worth reaching for specifically HERE, reversing in groups
of k, where recursive structure is genuinely clearer)
================================================================================
    func reverseKGroupRecursive(head *ListNode, k int) *ListNode {
        node := head
        for i := 0; i < k; i++ {
            if node == nil {
                return head          // fewer than k remain: leave as-is
            }
            node = node.Next
        }
        // node is now the first node AFTER this group (nil if none) --
        // recursively process the rest FIRST, then reverse this group and
        // splice its tail (the original head) onto the recursive result.
        newRest := reverseKGroupRecursive(node, k)
        prev := newRest
        curr := head
        for i := 0; i < k; i++ {
            next := curr.Next
            curr.Next = prev
            prev = curr
            curr = next
        }
        return prev
    }

Recurses once per group, so O(n/k) stack frames — per topic guide §4.2,
this is a real memory cost in Go (no TCO), acceptable here because n/k is
typically small, but the iterative version is still the safer default for
adversarial inputs (small k, huge n).

    Time: O(n)     Space: O(n/k) recursion stack


================================================================================
STEP BY STEP — head = 1->2->3->4->5, k=2
================================================================================
    dummy -> 1 -> 2 -> 3 -> 4 -> 5 -> nil
    groupPrev = dummy

    Group 1: count ahead from node 1 -> 1,2 (2 nodes, k satisfied)
        reverse [1,2]: prev=nil,curr=1
          i=0: next=2; 1.Next=nil; prev=1; curr=2
          i=1: next=3; 2.Next=1;   prev=2; curr=3
        new group head = 2, new group tail = 1 (curr now sits at 3, the
        node AFTER the group -- this becomes the relink target)
        relink: groupPrev(dummy).Next = 2;  1.Next = 3 (curr, first node
        after the group)
        dummy -> 2 -> 1 -> 3 -> 4 -> 5 -> nil
        groupPrev = 1 (the former head, now the group's tail)

    Group 2: count ahead from node 3 -> 3,4 (2 nodes, k satisfied)
        reverse [3,4]: prev=nil,curr=3
          i=0: next=4; 3.Next=nil; prev=3; curr=4
          i=1: next=5; 4.Next=3;   prev=4; curr=5
        relink: groupPrev(1).Next = 4;  3.Next = 5
        dummy -> 2 -> 1 -> 4 -> 3 -> 5 -> nil
        groupPrev = 3

    Group 3: count ahead from node 5 -> only 1 node before hitting nil
        (5 -> nil after one step) -- fewer than k=2 remain, STOP.

    result: 2 -> 1 -> 4 -> 3 -> 5 -> nil     ✓ matches [2,1,4,3,5]


================================================================================
STEP BY STEP — head = 1->2->3->4->5, k=3  (leftover-group edge case)
================================================================================
    Group 1: count ahead 1,2,3 (k satisfied) -> reverse -> 3,2,1
        dummy -> 3 -> 2 -> 1 -> 4 -> 5 -> nil
        groupPrev = 1

    Group 2: count ahead from node 4 -> 4,5, then nil -- only 2 nodes,
        fewer than k=3, STOP. Nodes 4,5 remain AS IS (still 4 -> 5).

    result: 3 -> 2 -> 1 -> 4 -> 5 -> nil     ✓ matches [3,2,1,4,5]
    (this is the live demo's headline case for the "leftover < k stays
    unreversed" rule -- printed before/after below)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time   Space       Mutates input?
    --------------------------------  -----  ----------  --------------------
    Value-copy, rewrite (disallowed)  O(n)   O(n)        yes (.Val rewrite —
                                                            forbidden by spec)
    Iterative, group by group ✅      O(n)   O(1)        yes (relinks .Next,
                                                            reuses nodes)
    Recursive (variant) ✅            O(n)   O(n/k)       yes (relinks .Next,
                                                            reuses nodes)


================================================================================
EDGE CASES
================================================================================
    k == 1                    -> every "group" of 1 is trivially already
                                  reversed; the list is unchanged. Verify
                                  the loop degenerates cleanly rather than
                                  special-casing k==1.
    k == length of list        -> exactly one group, the WHOLE list is
                                  reversed once, and there is no leftover.
    length not a multiple of k -> the tail leftover group (size < k) is
                                  left AS IS — the headline behavior this
                                  problem exists to test. Demonstrated live
                                  in the demo below.
    length IS a multiple of k  -> no leftover; every group gets reversed,
                                  including the last one.
    single node, any k         -> k must be 1 (constraint: k <= n), trivial
                                  no-op.
    k > length of list          -> ruled out by the constraint 1 <= k <= n,
                                  but a defensive implementation should
                                  still leave the list unreversed rather
                                  than panicking if this constraint were
                                  ever violated by a caller.


================================================================================
COMMON MISTAKES
================================================================================
1. Reversing a group BEFORE confirming k nodes actually remain, then trying
   to "reverse it back" if not — wasteful and easy to get wrong. Always
   count-ahead first (or, in the recursive version, let the base case do
   the counting via the same k-step loop).
2. After reversing a group, relinking groupPrev.Next to the WRONG end —
   the new group head is the group's ORIGINAL LAST node (what curr's loop
   ended on as prev), not the original first node.
3. Forgetting that the group's original FIRST node is now its TAIL, and
   must be pointed at whatever comes after the group (the next group's new
   head, or the untouched leftover) — omitting this relink leaves that
   node's `.Next` dangling into whatever it was mid-reversal.
4. Using `curr != nil` as the reversal loop's stop condition instead of a
   fixed k-count — inside a single group's reversal, curr must stop
   EXACTLY after k steps, or it consumes nodes belonging to the next group.
5. Mutating `.Val` instead of relinking `.Next` (Approach 1) — produces the
   right output sequence but violates the explicit "only nodes may be
   changed" constraint, and is exactly the kind of shortcut this topic
   exists to discourage.
6. Off-by-one in the count-ahead step: counting k-1 or k+1 nodes instead of
   exactly k before deciding whether to reverse.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do it in O(1) extra space?
A: Yes — the iterative version above already is O(1) extra (Approach 2);
   it's the one to lead with. The recursive version is O(n/k) stack space,
   worth mentioning as a cleaner-to-write alternative but not the O(1)
   answer.

Q: What if k does not evenly divide the list length?
A: The trailing group with fewer than k nodes is left unreversed — this is
   the count-ahead check's entire job. Demonstrated live below.

Q: How would you test that the leftover-group behavior is correct, not just
   the reversal itself?
A: Build a list whose length is NOT a multiple of k, print it before and
   after, and assert the tail segment's values AND identity are unchanged
   — see the live demo below, which does exactly this.

Q: Recursive vs iterative here — which would you lead with?
A: Iterative, per the topic guide's general default (§4.2) — but this is
   one of the problems the guide calls out as a case where the recursive
   form is genuinely clearer to explain (reverse the rest first, then
   splice this group's reversed nodes in front), so mentioning both,
   coding the iterative one, is a strong answer.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 206  Reverse Linked List        — the atomic reversal (problem 001
                                          here), applied once here per group
    LC 24   Swap Nodes in Pairs        — the k=2 special case of this exact
                                          problem
    LC 143  Reorder List               — a different composition of the
                                          same reversal primitive (problem
                                          008 here)
================================================================================
*/

// reverseKGroup is the interview answer: iterative, group by group, with a
// look-ahead count. O(n) time, O(1) extra space.
func reverseKGroup(head *ListNode, k int) *ListNode {
	dummy := &ListNode{Next: head}
	groupPrev := dummy

	for {
		// Count ahead: do k nodes remain from groupPrev.Next?
		node := groupPrev.Next
		count := 0
		for count < k && node != nil {
			node = node.Next
			count++
		}
		if count < k {
			break // fewer than k remain: leave as-is
		}

		// Reverse exactly k nodes.
		var prev *ListNode
		curr := groupPrev.Next
		groupHeadOld := curr // will become this group's tail
		for i := 0; i < k; i++ {
			next := curr.Next
			curr.Next = prev
			prev = curr
			curr = next
		}

		// Relink: groupPrev -> new group head (prev); old head -> curr
		// (first node after the group, possibly nil).
		groupPrev.Next = prev
		groupHeadOld.Next = curr
		groupPrev = groupHeadOld
	}

	return dummy.Next
}

// reverseKGroupRecursive is a variant: reverse the rest of the list first,
// then reverse this group and splice its tail onto the recursive result.
// O(n) time, O(n/k) recursion stack.
func reverseKGroupRecursive(head *ListNode, k int) *ListNode {
	node := head
	for i := 0; i < k; i++ {
		if node == nil {
			return head // fewer than k remain: leave as-is
		}
		node = node.Next
	}
	newRest := reverseKGroupRecursive(node, k)
	var prev *ListNode = newRest
	curr := head
	for i := 0; i < k; i++ {
		next := curr.Next
		curr.Next = prev
		prev = curr
		curr = next
	}
	return prev
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
	cases := []struct {
		vals []int
		k    int
		want []int
	}{
		{[]int{1, 2, 3, 4, 5}, 2, []int{2, 1, 4, 3, 5}},
		{[]int{1, 2, 3, 4, 5}, 3, []int{3, 2, 1, 4, 5}},
		{[]int{1, 2, 3, 4, 5}, 1, []int{1, 2, 3, 4, 5}},
		{[]int{1, 2, 3, 4, 5}, 5, []int{5, 4, 3, 2, 1}},
		{[]int{1}, 1, []int{1}},
		{[]int{1, 2, 3, 4, 5, 6}, 2, []int{2, 1, 4, 3, 6, 5}},
		{[]int{1, 2, 3, 4, 5, 6}, 3, []int{3, 2, 1, 6, 5, 4}},
		{[]int{1, 2}, 2, []int{2, 1}},
	}

	allOK := true
	fmt.Println("--- correctness: iterative vs recursive ---")
	for _, tc := range cases {
		h1 := sliceToList(tc.vals)
		got1 := listToSlice(reverseKGroup(h1, tc.k))

		h2 := sliceToList(tc.vals)
		got2 := listToSlice(reverseKGroupRecursive(h2, tc.k))

		ok := equalInts(got1, tc.want) && equalInts(got2, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  vals=%-20v k=%d -> %v  (want %v)\n", status(ok), tc.vals, tc.k, got1, tc.want)
	}

	// ------------------------------------------------------------------
	// The headline behavior: leftover group (size < k) stays unreversed.
	// Demonstrated live, before and after, with node IDENTITY on the
	// leftover segment (not just values) to catch an accidental touch.
	// ------------------------------------------------------------------
	fmt.Println("\n--- leftover-group edge case, demonstrated live: leftover < k stays AS IS ---")
	vals := []int{1, 2, 3, 4, 5, 6, 7}
	k := 3
	head := sliceToList(vals)
	fmt.Printf("  before: %v   k=%d  (7 nodes, 7 %% 3 = 1 leftover)\n", listToSlice(head), k)

	// Capture the leftover node's identity before reversing (node with
	// value 7, the sole node in the trailing partial group).
	var leftoverNodeBefore *ListNode
	for n := head; n != nil; n = n.Next {
		if n.Val == 7 {
			leftoverNodeBefore = n
		}
	}

	result := reverseKGroup(head, k)
	after := listToSlice(result)
	fmt.Printf("  after:  %v\n", after)
	wantAfter := []int{3, 2, 1, 6, 5, 4, 7}
	afterOK := equalInts(after, wantAfter)
	fmt.Printf("  full groups [1,2,3] and [4,5,6] reversed; leftover [7] untouched: %v (want %v)\n",
		afterOK, wantAfter)
	allOK = allOK && afterOK

	// Verify the leftover node is the SAME object (identity), not a
	// recreated one with the same value.
	var leftoverNodeAfter *ListNode
	for n := result; n != nil; n = n.Next {
		if n.Val == 7 {
			leftoverNodeAfter = n
		}
	}
	identityOK := leftoverNodeBefore == leftoverNodeAfter
	fmt.Printf("  leftover node [7] is the SAME object before/after (identity): %v\n", identityOK)
	allOK = allOK && identityOK

	// ------------------------------------------------------------------
	// Trace of k=2 on [1,2,3,4,5], group by group.
	// ------------------------------------------------------------------
	fmt.Println("\n--- trace: reverseKGroup([1,2,3,4,5], k=2), group by group ---")
	dummy := &ListNode{Next: sliceToList([]int{1, 2, 3, 4, 5})}
	groupPrev := dummy
	group := 0
	for {
		node := groupPrev.Next
		count := 0
		for count < 2 && node != nil {
			node = node.Next
			count++
		}
		if count < 2 {
			fmt.Printf("  fewer than k=2 nodes remain (%d found) -> stop, leave as-is\n", count)
			break
		}
		group++
		var prev *ListNode
		curr := groupPrev.Next
		groupHeadOld := curr
		for i := 0; i < 2; i++ {
			next := curr.Next
			curr.Next = prev
			prev = curr
			curr = next
		}
		groupPrev.Next = prev
		groupHeadOld.Next = curr
		groupPrev = groupHeadOld
		fmt.Printf("  group %d reversed -> list so far: %v\n", group, listToSlice(dummy.Next))
	}
	fmt.Printf("  final: %v\n", listToSlice(dummy.Next))

	// ------------------------------------------------------------------
	// Measured: iterative O(1) space vs recursive O(n/k) stack.
	// ------------------------------------------------------------------
	fmt.Println("\n--- measured runtime: iterative vs recursive ---")
	fmt.Printf("  %8s %6s %14s %14s\n", "n", "k", "iterative", "recursive")
	for _, tc := range []struct{ n, k int }{{10_000, 2}, {100_000, 5}, {200_000, 100}} {
		vals := make([]int, tc.n)
		for i := range vals {
			vals[i] = i
		}
		h1 := sliceToList(vals)
		t0 := time.Now()
		reverseKGroup(h1, tc.k)
		t1 := time.Now()
		h2 := sliceToList(vals)
		t2 := time.Now()
		reverseKGroupRecursive(h2, tc.k)
		t3 := time.Now()
		itMs := float64(t1.Sub(t0).Microseconds()) / 1000.0
		recMs := float64(t3.Sub(t2).Microseconds()) / 1000.0
		fmt.Printf("  %8d %6d %12.2fms %12.2fms\n", tc.n, tc.k, itMs, recMs)
	}
	fmt.Println("  Both are O(n) time; the recursive version additionally costs O(n/k)")
	fmt.Println("  stack frames, which the iterative version avoids entirely — the point")
	fmt.Println("  of the follow-up's O(1)-space ask.")

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
