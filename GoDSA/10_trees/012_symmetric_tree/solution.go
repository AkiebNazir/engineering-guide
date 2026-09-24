package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 101 · Symmetric Tree                                 [Easy]
https://leetcode.com/problems/symmetric-tree/
================================================================================

THE CORE IDEA
--------------
Symmetric means the left subtree mirrors the right subtree: at every pair of
positions, left's-left must match right's-right, and left's-right must match
right's-left. So compare two subtrees at once with a CROSSED recursion:

    func isMirror(a, b *TreeNode) bool {
        if a == nil && b == nil {
            return true
        }
        if a == nil || b == nil {
            return false
        }
        return a.Val == b.Val &&
            isMirror(a.Left, b.Right) &&   // CROSS: a's left vs b's right
            isMirror(a.Right, b.Left)      // CROSS: a's right vs b's left
    }

Contrast this with problem 007 (Same Tree), whose recursion is STRAIGHT:
isSame(a.Left, b.Left) && isSame(a.Right, b.Right). Symmetric Tree is Same
Tree's crossed twin — call isMirror(root.Left, root.Right) once at the top.


================================================================================
APPROACH 1 · Brute force — serialize both halves, reverse one, compare
================================================================================
Flatten the left subtree and a "mirrored" right subtree (in-order, but
visiting Right-then-Left for the right side so nil markers line up), then
compare the two string/slice serializations for equality.

    Time:  O(n)      Space: O(n) for both serializations

Correct, but it is strictly more bookkeeping than the direct crossed
recursion for the same O(n) time — a warm-up, not the answer.


================================================================================
APPROACH 2 · Recursive crossed comparison ✅ (the answer)
================================================================================
Shown above. Four nil cases per call:
    both nil          -> true  (symmetric emptiness)
    exactly one nil    -> false (shapes differ)
    both non-nil, Val differs -> false
    both non-nil, Val equal   -> recurse crossed


================================================================================
APPROACH 3 · Iterative with an explicit pair-queue
================================================================================
A flat BFS queue of individual nodes throws away which node pairs with
which — you need a queue of PAIRS:

    queue := [][2]*TreeNode{{root.Left, root.Right}}
    for len(queue) > 0 {
        a, b := queue[0][0], queue[0][1]
        queue = queue[1:]
        if a == nil && b == nil { continue }
        if a == nil || b == nil || a.Val != b.Val { return false }
        queue = append(queue, [2]*TreeNode{a.Left, b.Right}, [2]*TreeNode{a.Right, b.Left})
    }
    return true

Same O(n) time; trades O(h) recursion-stack space for O(w) queue space
(topic guide §2.3 — BFS space is width-bound, not height-bound), and avoids
any recursion-depth risk on a skewed-but-symmetric-shaped input.


================================================================================
STEP BY STEP · root = [1,2,2,3,4,4,3]  (symmetric)
================================================================================
            1
          ┌─┴─┐
          2   2
        ┌─┴┐ ┌┴─┐
        3  4 4  3

    isMirror(2L, 2R):  Val 2==2 ✓
        isMirror(2L.Left=3, 2R.Right=3):  Val 3==3 ✓, both children nil -> true
        isMirror(2L.Right=4, 2R.Left=4):  Val 4==4 ✓, both children nil -> true
        -> true
    Overall: true

STEP BY STEP · root = [1,2,2,null,3,null,3]  (NOT symmetric)
================================================================================
            1
          ┌─┴─┐
          2   2
           ┴─┐  └─┐
             3     3        (left 2 has ONLY a right child 3;
                              right 2 has ONLY a right child 3)

    isMirror(2L, 2R): Val 2==2 ✓
        isMirror(2L.Left=nil, 2R.Right=3):  one nil, one non-nil -> FALSE

    Overall: false — both 3's hang on the same SIDE (both "right children"),
    which is a mirror-breaking asymmetry even though the values match.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time    Space   Mutates input?
    -------------------------  ------  ------  ---------------
    Serialize + compare        O(n)    O(n)    No
    Recursive crossed      ✅  O(n)    O(h)    No
    Iterative pair-queue       O(n)    O(w)    No


================================================================================
EDGE CASES
================================================================================
    single node [1]         -> true (root.Left and root.Right both nil).
    two children, equal Val, e.g. [1,2,2] -> true.
    [1,2,2,null,3,null,3]   -> false, the classic "values match, shape
                                doesn't" trap (see trace above).
    all same value, e.g. [1,1,1,1,1,1,1] -> true; equal values everywhere
                                do NOT guarantee symmetry in general, but a
                                perfectly mirrored shape with equal values
                                does — don't confuse "all equal" with
                                "symmetric", they're independent properties.
    [1,2,2,null,2,2,null]   -> false; both inner 2's hang on the SAME side
                                (both right children) instead of crossed
                                positions -- equal Vals alone never
                                substitute for the crossed structural check.


================================================================================
COMMON MISTAKES
================================================================================
1. Writing the STRAIGHT recursion (a.Left vs b.Left) instead of CROSSED —
   that reimplements Same Tree, which happens to pass symmetric cases only
   by accident when the tree is also literally identical on both sides.

2. Checking only `a.Val == b.Val` at the top level without ever descending —
   passes trees where only the root's immediate children match by luck.

3. Treating "one side nil, other side non-nil" as equal because you forgot
   to check nil BEFORE dereferencing .Val — panics with a nil pointer
   dereference in Go, unlike Python's catchable AttributeError.

4. Building the iterative version with a plain `[]*TreeNode` queue instead
   of pairs — loses which node must mirror which, and produces false
   positives on asymmetric-but-same-multiset trees.


================================================================================
FOLLOW-UPS
================================================================================
    - Do both recursively and iteratively (explicitly asked in the LC
      follow-up) — shown as approaches 2 and 3 above.
    - Check if an N-ary tree is symmetric — same crossed idea, but you must
      reverse one side's children slice before pairing them up.
    - What if node values could repeat with different meanings (e.g. tied to
      identity, not just Val)? Mirror check would then also need to compare
      pointer identity in a different way — clarify with the interviewer.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 100  Same Tree              — the straight-recursion sibling
    LC 951  Flip Equivalent Binary Trees — mirror check allowed at EVERY node
    LC 226  Invert Binary Tree     — inverting then comparing to original is
                                       an alternate (costlier) way to frame
                                       the same "mirror" concept
================================================================================
*/

// isSymmetric is the interview answer: crossed recursive mirror check.
func isSymmetric(root *TreeNode) bool {
	if root == nil {
		return true
	}
	return isMirror(root.Left, root.Right)
}

func isMirror(a, b *TreeNode) bool {
	if a == nil && b == nil {
		return true
	}
	if a == nil || b == nil {
		return false
	}
	return a.Val == b.Val && isMirror(a.Left, b.Right) && isMirror(a.Right, b.Left)
}

// isSymmetricIterative uses an explicit queue of NODE PAIRS — a flat queue
// of single nodes would lose the pairing information the mirror check needs.
func isSymmetricIterative(root *TreeNode) bool {
	if root == nil {
		return true
	}
	type pair struct{ a, b *TreeNode }
	queue := []pair{{root.Left, root.Right}}
	for len(queue) > 0 {
		p := queue[0]
		queue = queue[1:]
		if p.a == nil && p.b == nil {
			continue
		}
		if p.a == nil || p.b == nil || p.a.Val != p.b.Val {
			return false
		}
		queue = append(queue, pair{p.a.Left, p.b.Right}, pair{p.a.Right, p.b.Left})
	}
	return true
}

// isSymmetricSerialize is the brute-force approach: serialize both halves
// mirror-fashion and compare, only for contrast against the direct check.
func isSymmetricSerialize(root *TreeNode) bool {
	if root == nil {
		return true
	}
	var left, right []int
	var walkLeft func(*TreeNode)
	walkLeft = func(n *TreeNode) {
		if n == nil {
			left = append(left, -999999)
			return
		}
		left = append(left, n.Val)
		walkLeft(n.Left)
		walkLeft(n.Right)
	}
	var walkRight func(*TreeNode)
	walkRight = func(n *TreeNode) {
		if n == nil {
			right = append(right, -999999)
			return
		}
		right = append(right, n.Val)
		walkRight(n.Right) // mirror order: right first
		walkRight(n.Left)
	}
	walkLeft(root.Left)
	walkRight(root.Right)
	if len(left) != len(right) {
		return false
	}
	for i := range left {
		if left[i] != right[i] {
			return false
		}
	}
	return true
}

func main() {
	type testCase struct {
		name string
		root *TreeNode
		want bool
	}

	// [1,2,2,3,4,4,3] symmetric
	sym := &TreeNode{
		Val: 1,
		Left: &TreeNode{Val: 2,
			Left:  &TreeNode{Val: 3},
			Right: &TreeNode{Val: 4},
		},
		Right: &TreeNode{Val: 2,
			Left:  &TreeNode{Val: 4},
			Right: &TreeNode{Val: 3},
		},
	}

	// [1,2,2,null,3,null,3] not symmetric — same values, wrong side
	asym := &TreeNode{
		Val: 1,
		Left: &TreeNode{Val: 2,
			Right: &TreeNode{Val: 3},
		},
		Right: &TreeNode{Val: 2,
			Right: &TreeNode{Val: 3},
		},
	}

	// [1,2,2,2,null,null,2]: left.Left=2 mirrors right.Right=2 -- this IS
	// symmetric (the crossed positions line up), which is exactly why the
	// STRAIGHT recursion (left.Left vs right.Left) would wrongly reject it.
	crossedMirror := &TreeNode{
		Val: 1,
		Left: &TreeNode{Val: 2,
			Left: &TreeNode{Val: 2},
		},
		Right: &TreeNode{Val: 2,
			Right: &TreeNode{Val: 2},
		},
	}

	// [1,2,2,null,2,2,null]: values match but sit on the SAME side on both
	// halves (both left children carry the inner 2s) -- crossed check fails.
	sameSideAsym := &TreeNode{
		Val: 1,
		Left: &TreeNode{Val: 2,
			Right: &TreeNode{Val: 2},
		},
		Right: &TreeNode{Val: 2,
			Right: &TreeNode{Val: 2},
		},
	}

	cases := []testCase{
		{"LC example 1 -> true", sym, true},
		{"LC example 2 -> false", asym, false},
		{"single node -> true", &TreeNode{Val: 1}, true},
		{"crossed positions line up -> true", crossedMirror, true},
		{"same-side positions, values match -> false", sameSideAsym, false},
		{"all equal values, mirrored shape -> true",
			&TreeNode{Val: 7, Left: &TreeNode{Val: 7}, Right: &TreeNode{Val: 7}}, true},
	}

	allOK := true
	for _, tc := range cases {
		gotRec := isSymmetric(tc.root)
		gotIter := isSymmetricIterative(tc.root)
		gotSer := isSymmetricSerialize(tc.root)
		ok := gotRec == tc.want && gotIter == tc.want && gotSer == tc.want
		allOK = allOK && ok
		fmt.Printf("%s  %-40s want=%-5v recursive=%-5v iterative=%-5v serialize=%v\n",
			status(ok), tc.name, tc.want, gotRec, gotIter, gotSer)
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
