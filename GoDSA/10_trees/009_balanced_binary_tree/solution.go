package main

import (
	"fmt"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 110 · Balanced Binary Tree                           [Easy]
https://leetcode.com/problems/balanced-binary-tree/
================================================================================

THE CORE IDEA
-------------
Naive: for every node, compute height(Left) and height(Right) from scratch
and compare. Height itself is an O(size-of-subtree) walk, so doing it at
EVERY node is O(n) work repeated O(n) times — O(n^2) overall on a skewed
tree, even though the final answer only needed O(n) work in total.

The fix: compute height AND check balance in the SAME single postorder
pass. A node's height depends only on its children's heights, and its
balance depends only on its children's heights too — so compute both at
once, bottom-up, and stop early the moment anything below is already
broken.

    func isBalanced(root *TreeNode) bool {
        var height func(*TreeNode) (int, bool)
        height = func(node *TreeNode) (int, bool) {
            if node == nil {
                return 0, true
            }
            lh, lok := height(node.Left)
            if !lok {
                return 0, false          // already broken below — stop early
            }
            rh, rok := height(node.Right)
            if !rok {
                return 0, false
            }
            balanced := abs(lh-rh) <= 1
            return 1 + max(lh, rh), balanced
        }
        _, ok := height(root)
        return ok
    }

O(n) time (every node visited once), O(h) space. This is 005's height
recurrence with a SECOND value threaded alongside it — the two-return-value
form is the idiomatic Go way to do that; a Python tuple return does the
same job.

================================================================================
APPROACHES
================================================================================
Approach 0 (naive, top-down, recompute height at every node) — measured
   below, O(n^2) worst case on a skewed tree. Name it, price it, replace it.

Approach 1 (bottom-up, two return values) ✅ — shown above. O(n) time,
   O(h) space, the answer.

Approach 2 (bottom-up, -1 sentinel) ✅ — the version people reach for under
   time pressure: fold "height" and "still balanced" into ONE int, using -1
   to mean "already broken, don't bother computing further":

    var height func(*TreeNode) int
    height = func(node *TreeNode) int {
        if node == nil {
            return 0
        }
        lh := height(node.Left)
        if lh == -1 { return -1 }
        rh := height(node.Right)
        if rh == -1 { return -1 }
        if abs(lh-rh) > 1 { return -1 }
        return 1 + max(lh, rh)
    }
    return height(root) != -1

   Same complexity as Approach 1; more compact, slightly less self-
   documenting (a caller has to know -1 is a sentinel, not a real height).

================================================================================
STEP BY STEP TRACE — root = [1,2,2,3,3,null,null,4,4]  (unbalanced)
================================================================================
                1
              /   \
             2     2
            / \
           3   3
          / \
         4   4

    height(4) [leftmost] = 1, balanced
    height(4) [its sibling] = 1, balanced
    height(3) [left child of upper 3]: lh=1, rh=... wait — walk bottom-up:
      height(4)=1 (leaf)      height(4)=1 (leaf, sibling under the SAME 3)
      height(3, with two depth-1 children) = 1 + max(1,1) = 2, |1-1|<=1 OK
    height(3) [the OTHER 3, a leaf, sibling of the first 3 under node 2]
      = 1, balanced
    height(2) [upper-left]: lh=height(3 with grandchildren)=2,
                             rh=height(3, leaf)=1
                             |2-1| = 1 <= 1 -> still OK, height = 3
    height(2) [upper-right, a leaf] = 1, balanced
    height(1) [root]: lh = height(2 upper-left) = 3
                       rh = height(2 upper-right) = 1
                       |3-1| = 2 > 1  -> UNBALANCED, propagate false

    result: false — the imbalance is detected at the ROOT, but only because
    every level below it faithfully reported a real height first (postorder:
    children's answers before the parent's).

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time     Space  Mutates?  Note
    ----------------------------------  -------  -----  --------  ---------------------
    Naive, recompute height per node   O(n^2)   O(h)   no        measured below
    Bottom-up, two return values ✅    O(n)     O(h)   no        the answer
    Bottom-up, -1 sentinel ✅          O(n)     O(h)   no        same bound, more compact

================================================================================
EDGE CASES
================================================================================
    root == nil               -> true. An empty tree is trivially balanced
                                (the recursion's base case).
    single node                 -> true.
    perfectly balanced tree      -> true, every node's children heights
                                differ by 0.
    unbalance ONLY at the root    -> both subtrees individually balanced,
                                but their heights differ by more than 1 —
                                the case in the trace above.
    unbalance deep in a leaf       -> a single node 2+ levels down with
                                mismatched child heights makes the WHOLE
                                tree report false, even if everything above
                                it looks fine locally. Early-exit propagates
                                this up without extra work.
    skewed (linked-list-shaped)     -> technically "balanced" is impossible
      chain of n>=3 nodes            past n=2 (every node beyond the first
                                has one subtree of height k and the other of
                                height 0), so isBalanced returns false almost
                                immediately once n is large enough — AND
                                it's the shape that exposes the O(n^2) naive
                                bug most severely, since height() there costs
                                O(depth) at every one of O(depth) nodes.

================================================================================
COMMON MISTAKES
================================================================================
1. Computing height and checking balance in TWO separate passes (or a
   height() helper called fresh inside a separate isBalanced recursion) —
   correct, but O(n^2) worst case. This is not a subtle bug, it's a
   subtle PERFORMANCE bug — ships a right answer, fails on large skewed
   inputs under a time limit.
2. Forgetting the early-exit: computing BOTH children's heights even after
   the left one already reports "broken." Correct but wastes work — still
   technically O(n) in the worst case for a SINGLE call since early exit
   only saves a constant factor per call, not the asymptotic bound, but
   it's the difference between "clean" and "sloppy" in review.
3. Checking `|height(Left) - height(Right)| <= 1` at the root only, instead
   of at EVERY node — the definition is "every node," not "the root." The
   trace above is deliberately built so the imbalance is invisible if you
   only inspect immediate subtree heights without recursing the check.
4. Off-by-one in the sentinel version: returning `-1` for a genuinely valid
   height of `-1`... which can't happen (heights are non-negative), but
   returning 0 instead of -1 for "broken" IS a real bug, since 0 is a valid
   height for an empty subtree and collapses the two meanings.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What's wrong with the "obvious" top-down solution?
A: It recomputes height(subtree) from scratch at every node — O(n) work,
   O(n) times, O(n^2) total on a skewed tree. Fuse the height computation
   and the balance check into one postorder pass.

Q: Prove it.
A: Time both on a real skewed tree — the gap is measured live below, not
   just claimed.

Q: What's an AVL tree?
A: A self-balancing BST that maintains EXACTLY this invariant (subtree
   heights differ by <= 1 at every node) after every insert/delete, via
   rotations — this problem is literally "is this tree currently a valid
   AVL shape," minus the BST ordering requirement.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    LC 104  Maximum Depth of Binary Tree  — the height subroutine, alone (005)
    LC 543  Diameter of Binary Tree       — same postorder-with-side-effect shape (010)
    LC 1382 Balance a Binary Search Tree  — rebuild instead of just checking
================================================================================
*/

func abs(x int) int {
	if x < 0 {
		return -x
	}
	return x
}

// isBalanced is the interview answer: bottom-up, two return values.
func isBalanced(root *TreeNode) bool {
	var height func(*TreeNode) (int, bool)
	height = func(node *TreeNode) (int, bool) {
		if node == nil {
			return 0, true
		}
		lh, lok := height(node.Left)
		if !lok {
			return 0, false
		}
		rh, rok := height(node.Right)
		if !rok {
			return 0, false
		}
		balanced := abs(lh-rh) <= 1
		return 1 + max(lh, rh), balanced
	}
	_, ok := height(root)
	return ok
}

// isBalancedSentinel folds height and "still balanced" into one int, using
// -1 as the "already broken" sentinel.
func isBalancedSentinel(root *TreeNode) bool {
	var height func(*TreeNode) int
	height = func(node *TreeNode) int {
		if node == nil {
			return 0
		}
		lh := height(node.Left)
		if lh == -1 {
			return -1
		}
		rh := height(node.Right)
		if rh == -1 {
			return -1
		}
		if abs(lh-rh) > 1 {
			return -1
		}
		return 1 + max(lh, rh)
	}
	return height(root) != -1
}

// heightNaive recomputes the full height of a subtree from scratch — the
// O(size-of-subtree) building block the naive O(n^2) approach calls at
// every node.
func heightNaive(node *TreeNode) int {
	if node == nil {
		return 0
	}
	return 1 + max(heightNaive(node.Left), heightNaive(node.Right))
}

// isBalancedNaive: top-down, recompute height at every node, WITHOUT
// short-circuiting on failure (recurses into both children unconditionally,
// the way this is commonly first written). On a skewed tree this is the
// real O(n^2) case: node i's heightNaive(Left) call walks the remaining
// n-i nodes, and that happens once per node down the whole chain, so total
// work is n + (n-1) + (n-2) + ... = O(n^2). (A version that short-circuits
// the moment abs(lh-rh) > 1 is exposed is actually O(n) on a plain skewed
// chain, because it fails and returns after the very first height check —
// see isBalancedNaiveShortCircuit below for that contrast.)
func isBalancedNaive(root *TreeNode) bool {
	if root == nil {
		return true
	}
	lh, rh := heightNaive(root.Left), heightNaive(root.Right)
	balancedHere := abs(lh-rh) <= 1
	leftOK := isBalancedNaive(root.Left)
	rightOK := isBalancedNaive(root.Right)
	return balancedHere && leftOK && rightOK
}

// isBalancedNaiveShortCircuit is the same idea but bails out the instant a
// local check fails. On a plain skewed chain this alone is enough to be
// fast (O(n): one height() call at the root already proves it's imbalanced)
// — but it is fast for the WRONG reason (a lucky early exit), not because
// the underlying per-node recomputation was fixed. A tree that stays
// "balanced-looking" for a while before the imbalance surfaces near the
// bottom would still cost this version much more than a single pass; the
// only real fix is fusing height computation and the balance check into
// one postorder walk (Approach 1/2 above), which is fast unconditionally.
func isBalancedNaiveShortCircuit(root *TreeNode) bool {
	if root == nil {
		return true
	}
	lh, rh := heightNaive(root.Left), heightNaive(root.Right)
	if abs(lh-rh) > 1 {
		return false
	}
	return isBalancedNaiveShortCircuit(root.Left) && isBalancedNaiveShortCircuit(root.Right)
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

// buildSkewed builds a left-only chain of n nodes — the shape that exposes
// the O(n^2) cost of a naive isBalanced that does NOT short-circuit: node i
// re-walks the remaining n-i nodes via heightNaive, once per node down the
// whole chain.
func buildSkewed(n int) *TreeNode {
	if n == 0 {
		return nil
	}
	root := &TreeNode{Val: 0}
	curr := root
	for i := 1; i < n; i++ {
		node := &TreeNode{Val: i}
		curr.Left = node
		curr = node
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
		values []interface{}
		want   bool
	}
	cases := []testCase{
		{[]interface{}{3, 9, 20, nil, nil, 15, 7}, true},
		{[]interface{}{1, 2, 2, 3, 3, nil, nil, 4, 4}, false},
		{[]interface{}{}, true},
		{[]interface{}{1}, true},
	}

	allOK := true

	fmt.Println("--- correctness: all three implementations ---")
	impls := []struct {
		name string
		fn   func(*TreeNode) bool
	}{
		{"bottom-up, two returns", isBalanced},
		{"bottom-up, -1 sentinel", isBalancedSentinel},
		{"naive, top-down        ", isBalancedNaive},
	}
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			got := impl.fn(buildTree(tc.values))
			if got != tc.want {
				ok = false
				fmt.Printf("  MISMATCH %s: %v -> %v (want %v)\n", impl.name, tc.values, got, tc.want)
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases)\n", status(ok), impl.name, len(cases))
	}

	// MEASURED: naive O(n^2) (no short-circuit) vs single-pass O(n) on a
	// skewed tree. Real timing — printed numbers come straight from
	// time.Since, not guessed at.
	fmt.Println("\n--- measured: naive O(n^2) (no short-circuit) vs single-pass O(n), skewed chain ---")
	fmt.Println("  (both correctly report 'unbalanced' — this measures the COST of getting there)")
	fmt.Printf("  %8s  %14s  %14s  %10s\n", "n", "naive", "single-pass", "ratio")
	sizes := []int{2000, 4000, 8000, 16000}
	const reps = 3
	var ratios []float64
	for _, n := range sizes {
		tree := buildSkewed(n)

		t0 := time.Now()
		var naiveResult bool
		for i := 0; i < reps; i++ {
			naiveResult = isBalancedNaive(tree)
		}
		naiveElapsed := time.Since(t0) / reps

		t0 = time.Now()
		var fastResult bool
		for i := 0; i < reps; i++ {
			fastResult = isBalanced(tree)
		}
		fastElapsed := time.Since(t0) / reps

		ratio := float64(naiveElapsed) / float64(fastElapsed)
		ratios = append(ratios, ratio)
		fmt.Printf("  %8d  %14v  %14v  %9.1fx\n", n, naiveElapsed, fastElapsed, ratio)

		if naiveResult != fastResult {
			allOK = false
			fmt.Printf("  MISMATCH at n=%d: naive=%v fast=%v\n", n, naiveResult, fastResult)
		}
	}
	fmt.Println("  As n doubles, the naive/single-pass ratio roughly doubles too (O(n^2) vs")
	fmt.Println("  O(n) growing apart), not a fixed constant-factor gap.")
	lastRatio := ratios[len(ratios)-1]
	fmt.Printf("  measured ratio at the largest size: %.1fx\n", lastRatio)
	allOK = allOK && lastRatio > ratios[0]

	// A short-circuiting naive version is fast on THIS particular tree — but
	// for the wrong reason (the root's imbalance is obvious in one height()
	// call), not because the per-node recomputation was actually fixed.
	fmt.Println("\n--- short-circuit alone is not the fix: it's just lucky here ---")
	bigChain := buildSkewed(16000)
	t0 := time.Now()
	scResult := isBalancedNaiveShortCircuit(bigChain)
	scElapsed := time.Since(t0)
	fmt.Printf("  isBalancedNaiveShortCircuit on the same n=16000 skewed chain: %v  %v\n", scResult, scElapsed)
	fmt.Println("  Fast here because the root itself is already unbalanced (one height() call")
	fmt.Println("  proves it). It does NOT fix the per-node recomputation — a tree where the")
	fmt.Println("  imbalance only surfaces near the bottom still forces the expensive path.")
	allOK = allOK && scResult == false

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
