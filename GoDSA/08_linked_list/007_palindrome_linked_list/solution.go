package main

import (
	"fmt"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 234 · Palindrome Linked List                          [Easy]
https://leetcode.com/problems/palindrome-linked-list/
================================================================================

THE CORE IDEA
--------------
A palindrome check wants both ends at once; a singly linked list only walks
forward. Two ways to manufacture "the other end":

    O(n) space: copy values into a slice -- slices support backward
                indexing, so run the ordinary two-pointer check there.
    O(1) space: find the middle (§3.1), reverse the second half in place
                (§4.1), then walk the first half and the reversed second
                half TOGETHER as if they were two independent forward lists
                meeting in the middle.

Both are O(n) time. The follow-up explicitly asks for O(1) space, so know
both, lead with the slice version to show a baseline, then deliver the
in-place version as the answer.


================================================================================
APPROACH 1 · Copy to slice, two-pointer check (O(n) space)
================================================================================
    var vals []int
    for node := head; node != nil; node = node.Next {
        vals = append(vals, node.Val)
    }
    lo, hi := 0, len(vals)-1
    for lo < hi {
        if vals[lo] != vals[hi] { return false }
        lo++; hi--
    }
    return true

Simple, obviously correct, never mutates the list. Costs O(n) extra space --
exactly the value buffer.


================================================================================
APPROACH 2 · Find middle + reverse second half + compare ✅ (O(1) space)
================================================================================
This is 004 (find the middle) and 001 (reversal), composed.

    1. slow/fast to the middle (§3.1)
    2. reverse everything from the middle onward (§4.1)
    3. walk head and the reversed second half's new head together, comparing
       .Val; stop when either pointer runs out
    4. (nice touch) reverse the second half back and re-attach, so the
       caller's list is exactly as it was before the call

O(n) time (three linear passes -- find middle, reverse, compare -- still
O(n) total, not O(n^2)), O(1) EXTRA space (a handful of pointers, no buffer
sized by input length).


================================================================================
STEP BY STEP -- head = [1, 2, 3, 2, 1]  (odd length)
================================================================================
    1 -> 2 -> 3 -> 2 -> 1 -> nil

    slow/fast to the middle: slow ends on the node valued 3 (the true middle
    of an odd-length list)

    split conceptually:        1 -> 2 -> 3          2 -> 1 -> nil
                                first half           second half (from middle)

    reverse the second half:   2 -> 1 -> nil   becomes   1 -> 2 -> nil

    compare, two forward pointers:
      p1 (from original head)     1 -> 2 -> 3
      p2 (from reversed 2nd half) 1 -> 2 -> nil

      p1.Val=1 vs p2.Val=1  match
      p1.Val=2 vs p2.Val=2  match
      p1.Val=3 vs p2.Val=3  match   <- SAME physical node compared with itself
      p2 runs out (nil)     -> stop; all compared pairs matched -> true

    Reversing starting AT slow (rather than slow.Next) means the middle node
    ends up as the LAST element of the reversed second half too -- so on an
    odd-length list, p1 and p2 converge on that exact same node object for
    the final comparison, a harmless self-comparison. Not a bug: one
    redundant comparison, never a wrong answer, simpler than special-casing
    "skip the middle" for odd vs even.


================================================================================
STEP BY STEP -- head = [1, 2, 2, 1]  (even length)
================================================================================
    1 -> 2 -> 2 -> 1 -> nil

    slow/fast to the middle: slow ends on the SECOND 2 (first node of the
    second half, for even length)

    split:            1 -> 2          2 -> 1 -> nil
    reverse 2nd half:                 1 -> 2 -> nil

    compare:
      p1: 1 -> 2       p2: 1 -> 2
      1 vs 1 match, 2 vs 2 match, both run out together -> true


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time   Space   Mutates input?  Note
    --------------------------------  -----  ------  ---------------  ------------------
    Copy to slice + two-pointer ✅    O(n)   O(n)    no               baseline, simplest
    Middle + reverse + compare (raw)  O(n)   O(1)    yes (permanently) follow-up answer
    Middle + reverse + compare +     O(n)   O(1)    no (restored)    nice touch, same
      restore second half                                            asymptotics


================================================================================
EDGE CASES
================================================================================
    single node        -> true.  slow/fast never moves, "second half" is
                                empty, compare loop runs zero times.
    two equal values     -> true.  [1,1] -- even length, smallest nontrivial
                                even case.
    two different values  -> false. [1,2] -- smallest case that fails.
    odd length            -> the true middle node is excluded from
                                comparison (see the trace above) -- correct,
                                not an off-by-one to "fix."
    all same value          -> always true regardless of length ([5,5,5]).
    long list (10^5 nodes)    -> the O(1)-space approach avoids allocating a
                                10^5-element buffer; matters at scale.


================================================================================
COMMON MISTAKES
================================================================================
1. Trying a two-pointer scan DIRECTLY on the linked list without copying or
   reversing anything -- there is no way to move backward from the tail on
   a singly linked list, so this is not expressible without one of the two
   transformations above.
2. Getting the middle split wrong for EVEN-length lists -- slow/fast (`for
   fast != nil && fast.Next != nil`) lands slow on the FIRST node of the
   second half for even length, but on the TRUE middle for odd length.
3. Forgetting the compare loop must stop when EITHER pointer runs out, not
   both -- for odd length, p1 still has the (irrelevant) middle node left
   after p2 is exhausted; continuing to dereference p1.Next off a nil p2
   panics.
4. Losing the reference to the first half's tail before reversing the
   second half -- corrupts the seam between the two halves.
5. Claiming the O(1)-space version has "no side effects" without restoring
   the list -- it silently reverses the second half of the CALLER's list
   unless explicitly reversed back. Fine for LeetCode's grading (checked
   once, list discarded), a real correctness bug if the list is reused.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do it in O(1) space AND leave the list completely unchanged
   afterward?
A: Yes -- after comparing, reverse the (still-reversed) second half back to
   its original direction and re-attach it to the first half's tail. Same
   O(n) time, same O(1) extra space; costs one more full pass. Included as
   isPalindromeRestore below.

Q: What if the list were doubly linked?
A: Then two pointers -- one from head walking .Next, one from the tail
   walking .Prev -- solve it directly in O(n) time, O(1) space, with no
   reversal step needed at all.

Q: How would you check if a SLICE (not a linked list) is a palindrome?
A: Directly with topic 02's converging two-pointer scan -- lo, hi := 0,
   len(a)-1; that's the technique this problem's O(n)-space approach
   effectively simulates by first copying into a slice.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 206  Reverse Linked List        -- the reversal template reused here
                                          (problem 001)
    LC 876  Middle of the Linked List  -- the slow/fast half-finder reused
                                          here (problem 004)
    LC 143  Reorder List               -- same two techniques, composed
                                          differently, plus a merge/interleave
                                          (problem 008 here)
    LC 9    Palindrome Number           -- same idea (reverse half, compare),
                                          applied to digits of an int instead
                                          of linked-list nodes
================================================================================
*/

// isPalindrome is the interview answer for the O(1)-space follow-up: find
// middle (§3.1) + reverse second half (§4.1) + compare. O(n) time, O(1)
// extra space. PERMANENTLY reverses the second half of the caller's list as
// a side effect -- see isPalindromeRestore for the version that undoes that.
func isPalindrome(head *ListNode) bool {
	if head == nil || head.Next == nil {
		return true
	}

	// 1. find the middle
	slow, fast := head, head
	for fast != nil && fast.Next != nil {
		slow = slow.Next
		fast = fast.Next.Next
	}

	// 2. reverse the second half, starting at slow
	var prev *ListNode
	curr := slow
	for curr != nil {
		next := curr.Next
		curr.Next = prev
		prev = curr
		curr = next
	}
	secondHead := prev

	// 3. compare the first half against the reversed second half
	p1, p2 := head, secondHead
	result := true
	for p1 != nil && p2 != nil {
		if p1.Val != p2.Val {
			result = false
			break
		}
		p1 = p1.Next
		p2 = p2.Next
	}
	return result
}

// isPalindromeRestore is the same as isPalindrome, but reverses the second
// half BACK and re-attaches it afterward, so the caller's list is
// unchanged. Same O(n) time / O(1) space, one extra pass.
func isPalindromeRestore(head *ListNode) bool {
	if head == nil || head.Next == nil {
		return true
	}

	slow, fast := head, head
	for fast != nil && fast.Next != nil {
		slow = slow.Next
		fast = fast.Next.Next
	}

	// remember the node right before the split, to re-attach later
	firstTail := head
	for firstTail.Next != slow {
		firstTail = firstTail.Next
	}

	var prev *ListNode
	curr := slow
	for curr != nil {
		next := curr.Next
		curr.Next = prev
		prev = curr
		curr = next
	}
	secondHead := prev

	p1, p2 := head, secondHead
	result := true
	for p1 != nil && p2 != nil {
		if p1.Val != p2.Val {
			result = false
		}
		p1 = p1.Next
		p2 = p2.Next
	}

	// reverse the second half back to its original direction
	var prev2 *ListNode
	curr2 := secondHead
	for curr2 != nil {
		next := curr2.Next
		curr2.Next = prev2
		prev2 = curr2
		curr2 = next
	}
	firstTail.Next = prev2 // re-attach in original order

	return result
}

// isPalindromeSlice is the baseline: copy to a slice, two-pointer check.
// O(n) time, O(n) space, never mutates the list.
func isPalindromeSlice(head *ListNode) bool {
	var vals []int
	for node := head; node != nil; node = node.Next {
		vals = append(vals, node.Val)
	}
	lo, hi := 0, len(vals)-1
	for lo < hi {
		if vals[lo] != vals[hi] {
			return false
		}
		lo++
		hi--
	}
	return true
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

func equalIntSlicesPal(a, b []int) bool {
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
		want   bool
	}
	cases := []tc{
		{[]int{1, 2, 2, 1}, true},
		{[]int{1, 2}, false},
		{[]int{1}, true},
		{[]int{1, 2, 3, 2, 1}, true},
		{[]int{1, 2, 3, 4}, false},
		{[]int{1, 1}, true},
		{[]int{1, 2, 1, 1}, false},
		{[]int{0}, true},
		{[]int{1, 2, 3, 3, 2, 1}, true},
	}

	allOK := true
	fmt.Println("--- correctness: slice O(n)-space vs in-place O(1)-space vs restoring version ---")
	for _, c := range cases {
		r1 := isPalindromeSlice(listToLinked(c.values))
		r2 := isPalindrome(listToLinked(c.values))
		r3 := isPalindromeRestore(listToLinked(c.values))
		ok := r1 == c.want && r2 == c.want && r3 == c.want
		allOK = allOK && ok
		fmt.Printf("%s  head=%-20v -> slice=%v inplace=%v restore=%v  (want %v)\n",
			status(ok), c.values, r1, r2, r3, c.want)
	}

	// ------------------------------------------------------------------
	// Live demo: isPalindrome (raw) mutates the caller's list; restore doesn't.
	// ------------------------------------------------------------------
	fmt.Println("\n--- side effect: raw isPalindrome mutates the list; restore doesn't ---")
	values := []int{1, 2, 3, 2, 1}
	headRaw := listToLinked(values)
	isPalindrome(headRaw)
	afterRaw := linkedToList(headRaw)
	fmt.Printf("  original values: %v\n", values)
	changedMsg := "(unchanged)"
	if !equalIntSlicesPal(afterRaw, values) {
		changedMsg = "<- STRUCTURE CHANGED (second half left reversed)"
	}
	fmt.Printf("  after isPalindrome(raw):    %v   %s\n", afterRaw, changedMsg)

	headRestore := listToLinked(values)
	isPalindromeRestore(headRestore)
	afterRestore := linkedToList(headRestore)
	restoreMsg := "CHANGED (bug)"
	if equalIntSlicesPal(afterRestore, values) {
		restoreMsg = "<- unchanged, as expected"
	}
	fmt.Printf("  after isPalindromeRestore:  %v   %s\n", afterRestore, restoreMsg)
	sideEffectShown := !equalIntSlicesPal(afterRaw, values) && equalIntSlicesPal(afterRestore, values)
	allOK = allOK && sideEffectShown

	// ------------------------------------------------------------------
	// Step-by-step trace.
	// ------------------------------------------------------------------
	fmt.Println("\n--- trace: isPalindrome([1,2,3,2,1]) (odd length) ---")
	head := listToLinked([]int{1, 2, 3, 2, 1})
	slow, fast := head, head
	for fast != nil && fast.Next != nil {
		slow = slow.Next
		fast = fast.Next.Next
	}
	fmt.Printf("  middle found at node with val=%d\n", slow.Val)
	var prev *ListNode
	curr := slow
	for curr != nil {
		next := curr.Next
		curr.Next = prev
		prev = curr
		curr = next
	}
	secondHead := prev
	fmt.Printf("  reversed second half starts at val=%d: %v\n", secondHead.Val, linkedToList(secondHead))
	p1, p2 := head, secondHead
	i := 0
	for p1 != nil && p2 != nil {
		verdict := "match"
		if p1.Val != p2.Val {
			verdict = "MISMATCH"
		}
		fmt.Printf("  compare[%d]: p1.Val=%d vs p2.Val=%d %s\n", i, p1.Val, p2.Val, verdict)
		p1, p2 = p1.Next, p2.Next
		i++
	}
	fmt.Println("  result: true")

	// ------------------------------------------------------------------
	// Slice O(n) space vs in-place O(1) space: measured runtime at scale.
	// ------------------------------------------------------------------
	fmt.Println("\n--- slice O(n)-space vs in-place O(1)-space: measured runtime at scale ---")
	fmt.Printf("  %8s %18s %20s %8s\n", "n", "slice O(n) space", "in-place O(1) space", "ratio")
	for _, n := range []int{10_000, 100_000, 500_000} {
		half := n / 2
		vals := make([]int, 0, n)
		for i := 0; i < half; i++ {
			vals = append(vals, i)
		}
		for i := half - 1; i >= 0; i-- {
			vals = append(vals, i)
		}
		h1 := listToLinked(vals)
		t0 := time.Now()
		isPalindromeSlice(h1)
		t1 := time.Now()
		h2 := listToLinked(vals)
		isPalindrome(h2) // note: h2's second half is now reversed, fine for timing only
		t2 := time.Now()
		sliceDur := t1.Sub(t0)
		ipDur := t2.Sub(t1)
		ratio := float64(sliceDur) / float64(ipDur)
		fmt.Printf("  %8d %17v %19v %7.2fx\n", n, sliceDur, ipDur, ratio)
	}
	fmt.Println("  Both are O(n) TIME, so runtime is close either way -- the real win of")
	fmt.Println("  the in-place approach is SPACE: no n-sized buffer is allocated, which")
	fmt.Println("  matters when n is large enough to pressure memory, not the clock.")

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
