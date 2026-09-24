package main

import (
	"fmt"
)

/*
================================================================================
SOLUTION · LeetCode 700 · Search in a Binary Search Tree                 [Easy]
https://leetcode.com/problems/search-in-a-binary-search-tree/
================================================================================

THE CORE IDEA
-------------
At every node, the BST invariant already tells you which side val could be
on — you never need to check both. Compare val to node.Val: smaller, go
left; larger, go right; equal, you're done. This is a single comparison-
guided descent, not a general tree search.

Contrast with a general BINARY TREE (no ordering): searching for a value
there has no way to prune a branch, so you must visit both children at every
node — worst case O(n). A BST search never revisits the "wrong" half; the
invariant proves the wrong half can't contain val.

================================================================================
APPROACHES
================================================================================
Approach 0 (naive general-tree search, don't code the real answer this way):
   visit every node, check node.Val == val, recurse into BOTH children
   regardless of comparison. O(n) time always — ignores the ordering
   entirely. Correct but wasteful; demoed below to measure the difference.

Approach 1 (iterative descent) ✅ — the answer. O(h) time, O(1) space.

Approach 2 (recursive descent) — same logic, O(h) call-stack space instead
   of O(1). Prefer iterative when space matters; recursive reads slightly
   cleaner and is fine at LeetCode's n <= 5000 constraint.

================================================================================
STEP BY STEP TRACE — search(root=[4,2,7,1,3], val=3)
================================================================================
            4
          /   \
         2     7
        / \
       1   3

    node=4: 3 < 4 -> go left
    node=2: 3 > 2 -> go right
    node=3: 3 == 3 -> FOUND, return subtree rooted at 3 (a leaf here: [3])

    3 comparisons, 3 nodes visited out of 5 -- never touched node 7 or its
    subtree, because 3 < 4 already proved node 7's entire right subtree
    (everything > 4) can't contain 3.

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                      Time     Space  Mutates input?  Note
    ------------------------------ -------  -----  ---------------  ------------
    Naive general-tree (both sides) O(n)    O(h)   no                ignores order
    Iterative BST descent ✅        O(h)    O(1)   no                the answer
    Recursive BST descent           O(h)    O(h)   no                same logic

    h = O(log n) balanced, O(n) skewed (topic guide Part 4).

================================================================================
EDGE CASES
================================================================================
    val not present     -> descend until node == nil, return nil. A nil
                            *TreeNode is itself the valid, well-typed answer
                            in Go — no sentinel value needed, unlike languages
                            without a distinct pointer nil.
    val == root.Val      -> return root immediately (subtree of everything).
    empty tree (root nil) -> loop/recursion base case returns nil straight
                            away; must not dereference a nil root.
    val equals a value that only exists off the path implied by comparisons
                          -> CANNOT happen in a valid BST; that's precisely
                            the invariant this algorithm exploits.

================================================================================
COMMON MISTAKES
================================================================================
1. Checking both children unconditionally (the Approach 0 habit carried over
   from general binary tree problems) — correct but throws away the O(h)
   speedup that's the entire point of this problem existing separately from
   the topic-10 "search a binary tree" exercise.
2. Comparing with `<=`/`>=` inconsistently with how the tree was built,
   silently walking the wrong side on a tree that allows duplicates.
3. Forgetting recursion needs an explicit `return` on each branch in Go —
   an accidentally-unreachable branch that never returns produces a nil
   subtree/compile complaint about a missing return, not a wrong answer.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the tree isn't guaranteed to be a valid BST?
A: This algorithm silently gives WRONG answers (it trusts the invariant to
   prune). You'd have to fall back to the O(n) general-tree search.

Q: Insert a value with the same logic?
A: Yes — 003 in this topic descends identically and attaches at the first
   nil it hits instead of stopping at equality.

Q: What's the worst case, and when does it happen?
A: O(n), when the tree is a degenerate chain (topic guide Part 4) — e.g.
   built by inserting 1..n in already-sorted order.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    LC 701   Insert into a BST                  — same descent, attach at nil (003)
    LC 450   Delete Node in a BST                — descent + splice (004)
    LC 235   LCA of a BST                        — descent, branch on straddling
    LC 270   Closest Binary Search Tree Value    — descent, track best-so-far
================================================================================
*/

// searchBSTIterative: descend by comparison, O(1) auxiliary space.
func searchBSTIterative(root *TreeNode, val int) *TreeNode {
	n := root
	for n != nil && n.Val != val {
		if val < n.Val {
			n = n.Left
		} else {
			n = n.Right
		}
	}
	return n
}

// searchBSTRecursive: same descent, O(h) call-stack space.
func searchBSTRecursive(root *TreeNode, val int) *TreeNode {
	if root == nil || root.Val == val {
		return root
	}
	if val < root.Val {
		return searchBSTRecursive(root.Left, val)
	}
	return searchBSTRecursive(root.Right, val)
}

// ---------------------------------------------------------------------------
// Naive general-tree search: checks BOTH children regardless of ordering.
// Used only to measure how many nodes it visits vs the BST-aware version.
// ---------------------------------------------------------------------------

func searchGeneralTree(root *TreeNode, val int, visits *int) *TreeNode {
	if root == nil {
		return nil
	}
	*visits++
	if root.Val == val {
		return root
	}
	if found := searchGeneralTree(root.Left, val, visits); found != nil {
		return found
	}
	return searchGeneralTree(root.Right, val, visits)
}

func searchBSTCountVisits(root *TreeNode, val int, visits *int) *TreeNode {
	n := root
	for n != nil {
		*visits++
		if n.Val == val {
			return n
		}
		if val < n.Val {
			n = n.Left
		} else {
			n = n.Right
		}
	}
	return n
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

func toLevelOrder(root *TreeNode) []interface{} {
	if root == nil {
		return nil
	}
	var out []interface{}
	queue := []*TreeNode{root}
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]
		if node == nil {
			out = append(out, nil)
			continue
		}
		out = append(out, node.Val)
		queue = append(queue, node.Left, node.Right)
	}
	for len(out) > 0 && out[len(out)-1] == nil {
		out = out[:len(out)-1]
	}
	return out
}

func levelOrderEqual(a, b []interface{}) bool {
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

// buildBalancedChain builds a balanced BST over 0..n-1 via repeated midpoint
// (same idea as 002), used to give the visit-count demo a tall-ish tree.
func buildBalancedBST(lo, hi int) *TreeNode {
	if lo > hi {
		return nil
	}
	mid := lo + (hi-lo)/2
	return &TreeNode{
		Val:   mid,
		Left:  buildBalancedBST(lo, mid-1),
		Right: buildBalancedBST(mid+1, hi),
	}
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
		val    int
		want   []interface{}
	}
	cases := []testCase{
		{[]interface{}{4, 2, 7, 1, 3}, 2, []interface{}{2, 1, 3}},
		{[]interface{}{4, 2, 7, 1, 3}, 5, nil},
		{[]interface{}{4, 2, 7, 1, 3}, 4, []interface{}{4, 2, 7, 1, 3}},
		{[]interface{}{1}, 1, []interface{}{1}},
	}

	allOK := true

	fmt.Println("--- correctness: iterative ---")
	for _, tc := range cases {
		got := toLevelOrder(searchBSTIterative(buildTree(tc.values), tc.val))
		ok := levelOrderEqual(got, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  search(%v, %d) -> %v (want %v)\n", status(ok), tc.values, tc.val, got, tc.want)
	}

	fmt.Println("\n--- correctness: recursive ---")
	for _, tc := range cases {
		got := toLevelOrder(searchBSTRecursive(buildTree(tc.values), tc.val))
		ok := levelOrderEqual(got, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  search(%v, %d) -> %v (want %v)\n", status(ok), tc.values, tc.val, got, tc.want)
	}

	// ------------------------------------------------------------------
	// Live proof: BST-aware descent visits far fewer nodes than a naive
	// both-sides general-tree search, on the SAME balanced tree.
	// ------------------------------------------------------------------
	fmt.Println("\n--- live proof: BST descent vs naive both-sides search, node visits ---")
	n := 1023 // balanced tree, height ~10 (2^10 - 1)
	tree := buildBalancedBST(0, n-1)
	target := n - 1 // rightmost leaf: naive search exhausts the ENTIRE left
	// subtree first (its left-then-right recursion order) before it ever
	// looks right, so this target is the worst case for the naive search
	// while still being a short, direct O(h) descent for the BST-aware one.

	bstVisits := 0
	bstFound := searchBSTCountVisits(tree, target, &bstVisits)

	generalVisits := 0
	generalFound := searchGeneralTree(tree, target, &generalVisits)

	foundMatch := bstFound != nil && generalFound != nil && bstFound.Val == generalFound.Val && bstFound.Val == target
	fmt.Printf("  tree size: %d nodes, height ~%d\n", n, 10)
	fmt.Printf("  BST-aware descent visited     : %d nodes\n", bstVisits)
	fmt.Printf("  naive both-sides search visited: %d nodes\n", generalVisits)
	fmt.Printf("  both found target %d: %v\n", target, foundMatch)
	fmt.Printf("  BST descent visited fewer nodes than naive search: %v (%dx fewer)\n",
		bstVisits < generalVisits, generalVisits/bstVisits)
	allOK = allOK && foundMatch && bstVisits < generalVisits

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
