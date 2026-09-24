package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 100 · Same Tree                                      [Easy]
https://leetcode.com/problems/same-tree/
================================================================================

THE CORE IDEA
-------------
Walk two trees in LOCK-STEP. At every pair of positions:
  - both nil            -> match at this position, nothing more to check
  - exactly one nil       -> shapes differ, done, false
  - both real, values differ -> done, false
  - both real, values match  -> recurse into (Left,Left) AND (Right,Right)

    func isSameTree(p, q *TreeNode) bool {
        if p == nil && q == nil {
            return true
        }
        if p == nil || q == nil {
            return false
        }
        if p.Val != q.Val {
            return false
        }
        return isSameTree(p.Left, q.Left) && isSameTree(p.Right, q.Right)
    }

O(min(n, m)) time — recursion stops at the first mismatch. O(min(h_p, h_q))
space. This four-line recursion is the SUBROUTINE every later problem in
this topic composes: 008 calls it at every node of a bigger tree, 012 calls
a crossed variant of it for symmetry.

================================================================================
APPROACHES
================================================================================
Approach 1 (recursion, parallel walk) ✅ — shown above. The answer.

Approach 2 (iterative, paired stack) ✅ — push pairs `(p, q)` instead of
   single nodes; pop, compare, push children pairs:

    stack := [][2]*TreeNode{{p, q}}
    for len(stack) > 0 {
        pair := stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        a, b := pair[0], pair[1]
        if a == nil && b == nil { continue }
        if a == nil || b == nil || a.Val != b.Val { return false }
        stack = append(stack, [2]*TreeNode{a.Left, b.Left}, [2]*TreeNode{a.Right, b.Right})
    }
    return true

   Same complexity, no call-stack risk — useful if either tree could be
   adversarially deep.

Approach 3 (serialize both, compare strings) — correct but strictly worse:
   O(n+m) time AND space to build both encodings, when the recursive walk
   can bail out on the FIRST mismatch and never touches the rest of either
   tree. Name it only to reject it: paying O(n+m) space to avoid nothing
   is a downgrade here, unlike 008 where the serialized form buys a real
   algorithmic improvement (O(n+m) vs O(n*m)).

================================================================================
STEP BY STEP TRACE — p = [1,2,3], q = [1,2,3]  (equal), then p = [1,2], q = [1,null,2] (not equal)
================================================================================
    p:      1        q:      1
           / \               / \
          2   3             2   3

    isSameTree(1,1): both real, vals equal (1==1)
      isSameTree(2,2): both real, vals equal, both leaves -> True
      isSameTree(3,3): both real, vals equal, both leaves -> True
    -> True

    p:    1          q:    1
         /                  \
        2                    2

    isSameTree(1,1): vals equal
      isSameTree(p.Left=2, q.Left=nil): one nil, one real -> False
    -> False   (short-circuits immediately; p.Right/q.Right never compared)

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time            Space            Mutates?  Note
    ----------------------------  --------------  ---------------  --------  ------------------
    Recursion, parallel walk ✅  O(min(n,m))     O(min(h_p,h_q))  no        the answer
    Iterative, paired stack ✅   O(min(n,m))     O(min(h_p,h_q))  no        no call-stack risk
    Serialize + compare strings  O(n+m)          O(n+m)           no        strictly worse here

================================================================================
EDGE CASES
================================================================================
    both nil                   -> true. Two empty trees are the same tree.
    one nil, one not             -> false, immediately.
    same shape, different values -> false at the first differing node;
                                   everything below it is never visited.
    same values, different shape  -> [1,2] vs [1,null,2]: false, THE
                                   canonical test case (see trace above).
    identical trees, huge         -> O(n) full walk, no shortcut possible
                                   when everything actually matches.
    p and q are the SAME pointer   -> true trivially; the recursion still
                                   works correctly (though a `p == q` fast
                                   path is a valid, cheap optimization to
                                   mention, not required).

================================================================================
COMMON MISTAKES
================================================================================
1. Using `p == q` (pointer/address equality) as a stand-in for "same
   values" — two structurally-identical-but-distinct trees have DIFFERENT
   addresses at every node. `==` on `*TreeNode` is Go's `is`, not `==` on
   values. Demoed live below.
2. Checking `p.Val == q.Val` before checking either is nil — panics with a
   nil pointer dereference the moment one side is nil and the other isn't.
   The nil checks MUST come first.
3. Using `p == nil || q == nil` where BOTH could be nil, without first
   checking `p == nil && q == nil` — that ordering is required, or the
   both-nil case incorrectly falls through to "one nil" and returns false
   for two empty trees.
4. Forgetting the `&&` between the two recursive calls (using `||`
   instead), which would report trees as "same" if EITHER subtree matched,
   ignoring the other entirely.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Do it iteratively.
A: Approach 2 — a stack of node PAIRS instead of single nodes.

Q: What's the relationship to LC 101 (Symmetric Tree)?
A: Symmetric checks a tree against ITS OWN MIRROR using a CROSSED pairing:
   compare (a.Left, b.Right) and (a.Right, b.Left) instead of the parallel
   (a.Left, b.Left) and (a.Right, b.Right) used here. Same skeleton, one
   pairing swapped.

Q: What's the relationship to LC 572 (Subtree of Another Tree)?
A: 008 calls THIS function at every node of a bigger tree — "is `subRoot` a
   subtree of `root`" reduces to "does `isSameTree` succeed starting from
   some node of `root`."

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    LC 101   Symmetric Tree                — crossed pairing, not parallel
    LC 572   Subtree of Another Tree       — isSameTree called at every node (008)
    LC 951   Flip Equivalent Binary Trees  — same OR mirrored at each node
================================================================================
*/

// isSameTree is the interview answer: recursion, parallel walk.
func isSameTree(p, q *TreeNode) bool {
	if p == nil && q == nil {
		return true
	}
	if p == nil || q == nil {
		return false
	}
	if p.Val != q.Val {
		return false
	}
	return isSameTree(p.Left, q.Left) && isSameTree(p.Right, q.Right)
}

// isSameTreeIterative walks paired stacks instead of recursing.
func isSameTreeIterative(p, q *TreeNode) bool {
	type pair struct{ a, b *TreeNode }
	stack := []pair{{p, q}}
	for len(stack) > 0 {
		top := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		a, b := top.a, top.b
		if a == nil && b == nil {
			continue
		}
		if a == nil || b == nil || a.Val != b.Val {
			return false
		}
		stack = append(stack, pair{a.Left, b.Left}, pair{a.Right, b.Right})
	}
	return true
}

// ---------------------------------------------------------------------------
// Test helpers (duplicated per package on purpose; see CONTEXT.md §4).
// ---------------------------------------------------------------------------

func buildTree(values []interface{}) *TreeNode {
	if len(values) == 0 || values[0] == nil {
		return nil
	}
	root := &TreeNode{Val: values[0].(int)}
	queue := []*TreeNode{root}
	i := 1
	for len(queue) > 0 && i < len(values) {
		node := queue[0]
		queue = queue[1:]
		if i < len(values) {
			if v := values[i]; v != nil {
				node.Left = &TreeNode{Val: v.(int)}
				queue = append(queue, node.Left)
			}
			i++
		}
		if i < len(values) {
			if v := values[i]; v != nil {
				node.Right = &TreeNode{Val: v.(int)}
				queue = append(queue, node.Right)
			}
			i++
		}
	}
	return root
}

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}

func main() {
	type testCase struct {
		p, q []interface{}
		want bool
	}
	cases := []testCase{
		{[]interface{}{1, 2, 3}, []interface{}{1, 2, 3}, true},
		{[]interface{}{1, 2}, []interface{}{1, nil, 2}, false},
		{[]interface{}{1, 2, 1}, []interface{}{1, 1, 2}, false},
		{[]interface{}{}, []interface{}{}, true},
		{[]interface{}{1}, []interface{}{}, false},
	}

	allOK := true

	fmt.Println("--- correctness: recursion, parallel walk ---")
	for _, tc := range cases {
		got := isSameTree(buildTree(tc.p), buildTree(tc.q))
		ok := got == tc.want
		allOK = allOK && ok
		fmt.Printf("%s  p=%v q=%v -> %v (want %v)\n", status(ok), tc.p, tc.q, got, tc.want)
	}

	fmt.Println("\n--- correctness: iterative paired stack ---")
	ok := true
	for _, tc := range cases {
		if isSameTreeIterative(buildTree(tc.p), buildTree(tc.q)) != tc.want {
			ok = false
		}
	}
	allOK = allOK && ok
	fmt.Printf("%s  iterative (%d cases)\n", status(ok), len(cases))

	// The pointer-equality trap: two structurally identical trees have
	// different addresses at every node, so p == q (as *TreeNode) is false
	// even though isSameTree(p, q) is true.
	fmt.Println("\n--- Go trap: pointer equality (==) is NOT value equality ---")
	p := buildTree([]interface{}{1, 2, 3})
	q := buildTree([]interface{}{1, 2, 3})
	pointerEqual := p == q
	valueEqual := isSameTree(p, q)
	fmt.Printf("  p and q built from the same values, but are DISTINCT allocations\n")
	fmt.Printf("  p == q (address comparison)   -> %v\n", pointerEqual)
	fmt.Printf("  isSameTree(p, q) (value walk) -> %v\n", valueEqual)
	trapProven := !pointerEqual && valueEqual
	allOK = allOK && trapProven
	fmt.Printf("  confirms == is Go's 'is', not a structural equals: %v\n", trapProven)

	// Same *pointer* passed twice: p == p is trivially true, and isSameTree
	// agrees for the (uninteresting) right reason.
	fmt.Println("\n--- same pointer passed twice: trivially both equal ---")
	samePtrOK := (p == p) && isSameTree(p, p)
	allOK = allOK && samePtrOK
	fmt.Printf("  p == p -> %v, isSameTree(p, p) -> %v\n", p == p, isSameTree(p, p))

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
