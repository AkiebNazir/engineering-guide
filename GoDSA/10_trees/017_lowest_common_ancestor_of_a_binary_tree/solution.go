package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 236 · Lowest Common Ancestor of a Binary Tree       [Medium]
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/
================================================================================

THE CORE IDEA
--------------
A postorder recursion whose return value means THREE different things
depending on what comes back, and that overloading is deliberate:

    func lca(node, p, q *TreeNode) *TreeNode {
        if node == nil || node == p || node == q {
            return node                        // found one, or ran off the tree
        }
        left := lca(node.Left, p, q)
        right := lca(node.Right, p, q)
        if left != nil && right != nil {
            return node                         // p and q split HERE -- the LCA
        }
        if left != nil {
            return left
        }
        return right                            // pass up whatever was found (maybe nil)
    }

    return value reads as:
        nil       -> neither p nor q is anywhere in this subtree
        p or q    -> exactly ONE of them is in this subtree (and this IS it)
        anything else -> the LCA has already been decided inside this
                          subtree; keep passing it up unchanged

Once `left != nil && right != nil` fires at some node, that node is returned
upward and every ancestor above it sees "exactly one thing found on this
side" — so the same value propagates unchanged all the way to the root. The
answer is decided exactly once and never revised.

WHY `node == p` RETURNS IMMEDIATELY, WITHOUT RECURSING FURTHER: a node is
defined as a descendant of itself, so if the current node IS p, then p is
already the lowest common ancestor of the pair WITHIN this subtree — whether
or not q also happens to live somewhere below it. Cutting the recursion
there is not an optimization, it is what implements "self-ancestry." Delete
that check and LC's own Example 2 (p=5, q=4, where 4 is 5's grandchild)
returns the wrong node — demonstrated live below.


================================================================================
APPROACH 0 · Brute force — for every node, test "both in my subtree?"
================================================================================
For each node, run a helper that checks whether p is anywhere in its subtree
AND q is anywhere in its subtree; the DEEPEST node passing both checks is
the LCA.

    Time:  O(n^2) worst case (each of n nodes re-scans its own subtree)
    Space: O(h) per contains-check

Correct, but re-scans the same subtrees repeatedly. The postorder version
computes "found here?" for every subtree exactly ONCE and reuses it via the
return value, collapsing to O(n).


================================================================================
APPROACH 1 · Postorder split-point recursion ✅ (the answer)
================================================================================
Shown above. Pointer identity comparisons (`node == p`) are O(1), and the
whole tree is visited at most once.


================================================================================
APPROACH 2 · Parent-pointer + path-to-root (an alternative worth naming)
================================================================================
Build a `child -> parent` map via one traversal, walk up from p collecting
its ancestor set, then walk up from q until you hit a node already in that
set.

    Time:  O(n) to build the map + O(h) for each walk    Space: O(n)

Uses MORE memory than approach 1 for the same O(n) time — worth mentioning
because it generalizes better to "find LCA of k nodes, queried repeatedly"
where the map amortizes across many queries; the pure recursion in approach
1 is the right answer for a single one-off query, which is what this
problem asks.


================================================================================
STEP BY STEP · root=[3,5,1,6,2,0,8,null,null,7,4], p=5, q=1
================================================================================
                3
              ┌─┴─┐
              5    1
            ┌─┴┐  ┌┴─┐
            6  2  0  8
              ┌┴┐
              7 4

    lca(3, p=5, q=1):
        3 != nil, 3 != 5, 3 != 1 -> recurse both sides
        left  = lca(5, ...) -> 5 == p -> returns 5 immediately (no deeper recursion)
        right = lca(1, ...) -> 1 == q -> returns 1 immediately
        left=5 (non-nil) AND right=1 (non-nil) -> SPLIT HERE -> return 3

    -> LCA = 3.  Matches LC. p and q are on genuinely different sides of the
    root, so the split fires at the very top.


STEP BY STEP · root=[3,5,1,6,2,0,8,null,null,7,4], p=5, q=4  (self-ancestry case)
================================================================================
    q=4 is 5's grandchild (5 -> 2 -> 4).

    lca(3, p=5, q=4):
        recurse both sides
        left  = lca(5, p=5, q=4):
            5 == p -> return 5 IMMEDIATELY, without ever checking whether 4
            is also somewhere below 5.
        right = lca(1, p=5, q=4): neither 5 nor 4 anywhere under 1 -> nil

        left=5 (non-nil), right=nil -> "exactly one side found something"
        -> return left = 5, unchanged

    -> LCA = 5.  Correct, and it hinged entirely on the early-return at
    `node == p` — that's the self-ancestry rule earning its keep, proven by
    a broken variant that removes it and gets this wrong, live below.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time     Space   Mutates input?
    ---------------------------------  -------  ------  ---------------
    Brute force (repeat subtree scan)  O(n^2)   O(h)    No
    Postorder split-point          ✅  O(n)     O(h)    No
    Parent-map + path-to-root          O(n)     O(n)    No


================================================================================
EDGE CASES
================================================================================
    p is an ancestor of q (or vice versa) -> LCA is p (or q) itself, per the
                               self-ancestry rule — LC example 2.
    two-node tree [1,2], p=1, q=2 -> LCA = 1 (the root, also p itself).
    p and q are the tree's two DEEPEST leaves on opposite sides -> LCA is
                               near the root; recursion still only visits
                               each node once.
    values that could look BST-ordered but the tree ISN'T a BST -> this
                               algorithm still works (it never compares
                               values), unlike the O(h) BST-specific LCA in
                               topic 11 which WOULD silently give a wrong
                               answer if applied to a non-BST tree of the
                               same shape.
    skewed (linked-list-shaped) tree -> O(h)=O(n) stack depth, same
                               degenerate-tree risk any recursive DFS has.


================================================================================
COMMON MISTAKES
================================================================================
1. Deleting or misplacing the `node == p || node == q` early return —
   breaks the self-ancestry case (LC example 2). Proven live below with a
   broken variant.

2. Comparing by VALUE (`node.Val == p.Val`) instead of by POINTER IDENTITY
   — works only if values are guaranteed unique (LC 236 guarantees this),
   but it's the wrong habit to build; p and q are given as actual node
   pointers, compare them as such.

3. Assuming this is a BST and trying to compare values to pick a side —
   LC 236 is explicitly the GENERAL tree version; the BST shortcut belongs
   to topic 11 and is wrong here even when it happens to produce the right
   answer on a particular input.

4. Returning `left` unconditionally when both are non-nil, instead of
   returning `node` itself — loses the actual split point.


================================================================================
FOLLOW-UPS
================================================================================
    - LCA of a BINARY SEARCH TREE (topic 11): use value comparisons to pick
      one side, O(h) without ever visiting both subtrees.
    - LCA of k nodes, not just two: extend the "found count" check from
      "both non-nil" to "count of non-nil children responses == k remaining
      targets" style bookkeeping, or use the parent-map approach queried
      repeatedly.
    - What if p or q might NOT be in the tree? This problem guarantees both
      exist; without that guarantee you'd need a separate existence check
      before trusting the result (a node could be "found" by mistake if the
      early-return fires on the wrong assumption).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 235  Lowest Common Ancestor of a Binary Search Tree — the O(h) value-
             comparison shortcut, topic 11
    LC 1650 Lowest Common Ancestor III (with parent pointers given directly)
    LC 1676 Lowest Common Ancestor IV (generalizes to a SET of target nodes)
================================================================================
*/

// lowestCommonAncestor is the interview answer: postorder split-point
// recursion with an intentionally overloaded return value.
func lowestCommonAncestor(root, p, q *TreeNode) *TreeNode {
	if root == nil || root == p || root == q {
		return root
	}
	left := lowestCommonAncestor(root.Left, p, q)
	right := lowestCommonAncestor(root.Right, p, q)
	if left != nil && right != nil {
		return root
	}
	if left != nil {
		return left
	}
	return right
}

// lowestCommonAncestorBrute checks, for every node, whether both p and q lie
// in its subtree, and returns the deepest such node. O(n^2) worst case.
func lowestCommonAncestorBrute(root, p, q *TreeNode) *TreeNode {
	var find func(*TreeNode) *TreeNode
	find = func(node *TreeNode) *TreeNode {
		if node == nil {
			return nil
		}
		if contains(node, p) && contains(node, q) {
			if l := find(node.Left); l != nil {
				return l
			}
			if r := find(node.Right); r != nil {
				return r
			}
			return node
		}
		return nil
	}
	return find(root)
}

func contains(root, target *TreeNode) bool {
	if root == nil {
		return false
	}
	if root == target {
		return true
	}
	return contains(root.Left, target) || contains(root.Right, target)
}

// lowestCommonAncestorParentMap builds child->parent links, then walks the
// ancestor chain from p and finds the first shared node with q's chain.
func lowestCommonAncestorParentMap(root, p, q *TreeNode) *TreeNode {
	parent := make(map[*TreeNode]*TreeNode)
	queue := []*TreeNode{root}
	parent[root] = nil
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]
		if node.Left != nil {
			parent[node.Left] = node
			queue = append(queue, node.Left)
		}
		if node.Right != nil {
			parent[node.Right] = node
			queue = append(queue, node.Right)
		}
	}
	ancestors := map[*TreeNode]bool{}
	for n := p; n != nil; n = parent[n] {
		ancestors[n] = true
	}
	for n := q; n != nil; n = parent[n] {
		if ancestors[n] {
			return n
		}
	}
	return nil
}

// lowestCommonAncestorNoSelfCheck is the BUGGY variant that removes the
// `node == p || node == q` early return, replacing it with a plain
// contains-style search. Kept only to prove why self-ancestry matters.
func lowestCommonAncestorNoSelfCheck(root, p, q *TreeNode) *TreeNode {
	var find func(*TreeNode) (foundP, foundQ bool, ancestor *TreeNode)
	find = func(node *TreeNode) (bool, bool, *TreeNode) {
		if node == nil {
			return false, false, nil
		}
		lp, lq, la := find(node.Left)
		rp, rq, ra := find(node.Right)
		hasP := lp || rp || node == p
		hasQ := lq || rq || node == q
		if la != nil {
			return hasP, hasQ, la
		}
		if ra != nil {
			return hasP, hasQ, ra
		}
		// BUG: only declares an ancestor once BOTH are found strictly BELOW
		// this node's own identity match, requiring node to not equal p or q
		// for the "both here" case to be considered valid on itself.
		if hasP && hasQ && node != p && node != q {
			return hasP, hasQ, node
		}
		return hasP, hasQ, nil
	}
	_, _, ancestor := find(root)
	return ancestor
}

func main() {
	// root=[3,5,1,6,2,0,8,null,null,7,4]
	n7 := &TreeNode{Val: 7}
	n4 := &TreeNode{Val: 4}
	n6 := &TreeNode{Val: 6}
	n2 := &TreeNode{Val: 2, Left: n7, Right: n4}
	n5 := &TreeNode{Val: 5, Left: n6, Right: n2}
	n0 := &TreeNode{Val: 0}
	n8 := &TreeNode{Val: 8}
	n1 := &TreeNode{Val: 1, Left: n0, Right: n8}
	root := &TreeNode{Val: 3, Left: n5, Right: n1}

	type testCase struct {
		name string
		p, q *TreeNode
		want *TreeNode
	}
	cases := []testCase{
		{"LC example 1: LCA(5,1) -> 3", n5, n1, root},
		{"LC example 2: LCA(5,4) -> 5 (self-ancestry)", n5, n4, n5},
		{"LCA(7,4) -> 2 (siblings under 2)", n7, n4, n2},
		{"LCA(6,2) -> 5 (siblings under 5)", n6, n2, n5},
		{"LCA(0,8) -> 1 (siblings under 1)", n0, n8, n1},
	}

	allOK := true
	for _, tc := range cases {
		gotRec := lowestCommonAncestor(root, tc.p, tc.q)
		gotBrute := lowestCommonAncestorBrute(root, tc.p, tc.q)
		gotMap := lowestCommonAncestorParentMap(root, tc.p, tc.q)
		ok := gotRec == tc.want && gotBrute == tc.want && gotMap == tc.want
		allOK = allOK && ok
		fmt.Printf("%s  %-42s want=%d  recursion=%d  brute=%d  parent-map=%d\n",
			status(ok), tc.name, tc.want.Val, gotRec.Val, gotBrute.Val, gotMap.Val)
	}

	// Two-node tree.
	{
		p, q := &TreeNode{Val: 1}, &TreeNode{Val: 2}
		p.Right = q
		got := lowestCommonAncestor(p, p, q)
		ok := got == p
		allOK = allOK && ok
		fmt.Printf("%s  %-42s want=%d  recursion=%d\n", status(ok), "two-node tree [1,2] LCA(1,2) -> 1", 1, got.Val)
	}

	fmt.Println("\n--- why the self-ancestry early return is load-bearing, not optional ---")
	correct := lowestCommonAncestor(root, n5, n4)
	broken := lowestCommonAncestorNoSelfCheck(root, n5, n4)
	fmt.Printf("  correct (early return on node==p)    -> LCA(5,4) = %d\n", correct.Val)
	if broken == nil {
		fmt.Println("  broken  (no self-ancestry shortcut)  -> LCA(5,4) = <nil>  <- WRONG, misses the case entirely")
	} else {
		fmt.Printf("  broken  (no self-ancestry shortcut)  -> LCA(5,4) = %d  <- WRONG if != 5\n", broken.Val)
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
