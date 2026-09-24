package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 2 · Add Two Numbers                                [Medium]
https://leetcode.com/problems/add-two-numbers/
================================================================================

THE CORE IDEA
-------------
Digits are stored least-significant-first, so walking both lists together IS
grade-school column addition:

    dummy := &ListNode{}
    curr := dummy
    carry := 0
    for l1 != nil || l2 != nil || carry != 0 {
        d1, d2 := 0, 0
        if l1 != nil { d1 = l1.Val }
        if l2 != nil { d2 = l2.Val }
        total := d1 + d2 + carry
        carry, digit := total/10, total%10
        curr.Next = &ListNode{Val: digit}
        curr = curr.Next
        if l1 != nil { l1 = l1.Next }
        if l2 != nil { l2 = l2.Next }
    }
    return dummy.Next

`for l1 != nil || l2 != nil || carry != 0` is the whole problem in one
condition: keep going while either list has a digit left, OR a leftover
carry needs one more node. The dummy node means "build a result list from
nothing" needs no special case for the first node.


================================================================================
APPROACH 1 · Convert digits to a native int, add, convert back (price it)
================================================================================
Go's int is fixed-width (64-bit on virtually all modern platforms), and the
constraint allows up to 100 digits per list — a 100-digit number vastly
exceeds what int64 can hold (max ~19 digits). This approach genuinely
OVERFLOWS in Go for large inputs, unlike Python's arbitrary-precision ints —
name this explicitly if the "convert to int" shortcut comes up, since it is
a real correctness bug here, not just an inefficiency.


================================================================================
APPROACH 2 · Digit-by-digit with carry ✅ (the answer)
================================================================================
See THE CORE IDEA. O(max(m,n)) time, O(max(m,n)) space for the required
output.


================================================================================
STEP BY STEP TRACE
================================================================================
l1 = [2,4,3] (=342), l2 = [5,6,4] (=465)  ->  342+465 = 807

    pos 0: d1=2 d2=5 carry=0  total=7   digit=7 carry=0   emit 7
    pos 1: d1=4 d2=6 carry=0  total=10  digit=0 carry=1   emit 0
    pos 2: d1=3 d2=4 carry=1  total=8   digit=8 carry=0   emit 8
    both exhausted, carry=0 -> STOP
    result: [7,0,8]  (=807)  correct


CARRY-PAST-THE-END TRACE — 999 + 1
------------------------------------------------------------------------------
l1 = [9,9,9] (=999), l2 = [1] (=1)

    pos 0: d1=9 d2=1 carry=0  total=10  digit=0 carry=1
    pos 1: d1=9 d2=0 carry=1  total=10  digit=0 carry=1   (l2 exhausted, d2=0)
    pos 2: d1=9 d2=0 carry=1  total=10  digit=0 carry=1   (l1 now also exhausted)
    both exhausted but carry=1 -> LOOP CONTINUES
    pos 3: d1=0 d2=0 carry=1  total=1   digit=1 carry=0   emit 1
    carry=0, both exhausted -> STOP
    result: [0,0,0,1]  (=1000)  4 nodes from inputs of length 3 and 1 — the
    trailing carry is exactly the case `|| carry != 0` exists for.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time          Space          Mutates input?
    -------------------------------  ------------  -------------  ---------------
    Convert to native int, add back  O(max(m,n))   O(max(m,n))    ✗ WRONG in Go —
                                                                     overflows past
                                                                     ~19 digits
    Digit-by-digit with carry  ✅    O(max(m,n))   O(max(m,n))    no (new list)


================================================================================
EDGE CASES
================================================================================
    [0] + [0]              -> [0]. Smallest legal input.
    Different lengths        -> shorter list's missing digits default to 0.
    Final carry needs an EXTRA node -> traced above (999+1=1000).
    Same length, no final carry -> traced above (342+465=807).


================================================================================
COMMON MISTAKES
================================================================================
1. `for l1 != nil && l2 != nil` — stops at the shorter list, silently
   dropping the longer list's remaining digits.
2. `for l1 != nil || l2 != nil` (missing `|| carry != 0`) — drops the FINAL
   carry digit, e.g. 999+1 comes out as 000 instead of 0001.
3. Dereferencing `l1.Val` without checking `l1 != nil` first — panics.
4. Forgetting the dummy node and hand-writing the first result node as a
   special case.
5. Reaching for the "convert to int" shortcut as the primary answer without
   naming the int64 overflow risk for the stated 100-digit constraint.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if digits were stored forward (most-significant first), as in
   LC 445 (Add Two Numbers II)?
A: Reverse both lists first (the reversal template from problem 001), add,
   then reverse the result — or use two stacks and pop from the end.

Q: Can you mutate one of the inputs in place instead of allocating a new
   list?
A: Yes — reuse the longer list's nodes, updating Val in place and only
   allocating for the trailing carry node (if any). Saves allocations, not
   complexity class.

Q: What about negative numbers?
A: Out of scope per the non-negative constraint; would need explicit sign
   tracking and borrow-based subtraction when signs differ.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 445  Add Two Numbers II   — forward-order digits, needs reversal/stack
    LC 67   Add Binary           — same carry-propagation shape, base 2
    LC 19   Remove Nth From End  — different technique, same dummy-node idiom
================================================================================
*/

// addTwoNumbers is the interview answer: digit-by-digit with carry, dummy
// node. O(max(m,n)) time, O(max(m,n)) space for the required output.
func addTwoNumbers(l1 *ListNode, l2 *ListNode) *ListNode {
	dummy := &ListNode{}
	curr := dummy
	carry := 0
	for l1 != nil || l2 != nil || carry != 0 {
		d1, d2 := 0, 0
		if l1 != nil {
			d1 = l1.Val
		}
		if l2 != nil {
			d2 = l2.Val
		}
		total := d1 + d2 + carry
		carry, total = total/10, total%10
		curr.Next = &ListNode{Val: total}
		curr = curr.Next
		if l1 != nil {
			l1 = l1.Next
		}
		if l2 != nil {
			l2 = l2.Next
		}
	}
	return dummy.Next
}

// addTwoNumbersDropsFinalCarry is ✗ BROKEN ON PURPOSE — the loop condition
// omits `|| carry != 0`, so a trailing carry digit is silently dropped.
// See common mistake #2.
func addTwoNumbersDropsFinalCarry(l1 *ListNode, l2 *ListNode) *ListNode {
	dummy := &ListNode{}
	curr := dummy
	carry := 0
	for l1 != nil || l2 != nil { // BUG: missing || carry != 0
		d1, d2 := 0, 0
		if l1 != nil {
			d1 = l1.Val
		}
		if l2 != nil {
			d2 = l2.Val
		}
		total := d1 + d2 + carry
		carry, total = total/10, total%10
		curr.Next = &ListNode{Val: total}
		curr = curr.Next
		if l1 != nil {
			l1 = l1.Next
		}
		if l2 != nil {
			l2 = l2.Next
		}
	}
	return dummy.Next
}

// --- test helpers ---

func buildList(digits []int) *ListNode {
	dummy := &ListNode{}
	curr := dummy
	for _, d := range digits {
		curr.Next = &ListNode{Val: d}
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

type addCase struct {
	d1, d2, want []int
}

func main() {
	cases := []addCase{
		{[]int{2, 4, 3}, []int{5, 6, 4}, []int{7, 0, 8}},
		{[]int{0}, []int{0}, []int{0}},
		{[]int{9, 9, 9, 9, 9, 9, 9}, []int{9, 9, 9, 9}, []int{8, 9, 9, 9, 0, 0, 0, 1}},
		{[]int{9, 9}, []int{1}, []int{0, 0, 1}},
		{[]int{5}, []int{5}, []int{0, 1}},
		{[]int{1, 2, 3}, []int{4, 5, 6, 7}, []int{5, 7, 9, 7}},
	}

	allOK := true

	fmt.Println("--- correctness ---")
	for _, tc := range cases {
		got := toSlice(addTwoNumbers(buildList(tc.d1), buildList(tc.d2)))
		ok := equalSlices(got, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  %v + %v -> %v (want %v)\n", status(ok), tc.d1, tc.d2, got, tc.want)
	}

	fmt.Println("\n--- trace: 999 + 1 (carry produces an EXTRA node) ---")
	l1, l2 := buildList([]int{9, 9, 9}), buildList([]int{1})
	carry := 0
	pos := 0
	var digitsOut []int
	for l1 != nil || l2 != nil || carry != 0 {
		d1, d2 := 0, 0
		if l1 != nil {
			d1 = l1.Val
		}
		if l2 != nil {
			d2 = l2.Val
		}
		carryIn := carry
		total := d1 + d2 + carry
		carry, digit := total/10, total%10
		digitsOut = append(digitsOut, digit)
		fmt.Printf("  pos %d: d1=%d d2=%d carry_in=%d total=%d -> digit=%d carry_out=%d\n",
			pos, d1, d2, carryIn, total, digit, carry)
		if l1 != nil {
			l1 = l1.Next
		}
		if l2 != nil {
			l2 = l2.Next
		}
		pos++
	}
	fmt.Printf("  result digits (reverse order) = %v\n", digitsOut)
	traceOK := equalSlices(digitsOut, []int{0, 0, 0, 1})
	allOK = allOK && traceOK
	fmt.Printf("  matches expected [0,0,0,1]: %v\n", traceOK)

	fmt.Println("\n--- dropped-final-carry bug (common mistake #2) ---")
	dropCases := []addCase{
		{[]int{9, 9, 9}, []int{1}, []int{0, 0, 0, 1}},
		{[]int{5}, []int{5}, []int{0, 1}},
		{[]int{9}, []int{9}, []int{8, 1}},
	}
	droppedMismatch := false
	for _, tc := range dropCases {
		good := toSlice(addTwoNumbers(buildList(tc.d1), buildList(tc.d2)))
		bad := toSlice(addTwoNumbersDropsFinalCarry(buildList(tc.d1), buildList(tc.d2)))
		mismatch := !equalSlices(good, bad)
		droppedMismatch = droppedMismatch || mismatch
		verdict := "NO  <- final carry digit missing"
		if !mismatch {
			verdict = "yes"
		}
		fmt.Printf("  %v + %v -> correct=%v broken=%v  %s\n", tc.d1, tc.d2, good, bad, verdict)
	}
	fmt.Printf("  dropped-carry bug reproduced: %v\n", droppedMismatch)
	allOK = allOK && droppedMismatch

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
