package main

import (
	"fmt"
)

/*
================================================================================
SOLUTION · LeetCode 226 · Invert Binary Tree                             [Easy]
https://leetcode.com/problems/invert-binary-tree/
================================================================================

THE CORE IDEA
-------------
At every node, swap the two CHILD POINTERS. Nothing else.

    func invertTree(root *TreeNode) *TreeNode {
        if root == nil {
            return nil
        }
        root.Left, root.Right = root.Right, root.Left   // the whole algorithm
        invertTree(root.Left)
        invertTree(root.Right)
        return root
    }

O(n) time, O(h) space, and it mutates the tree the caller handed in — after
this call returns, every `*TreeNode` anyone else is holding into the same
tree sees the new, inverted shape too, because there was never a copy.

The traversal order is FREE here: the swap at a node depends on no other
node's result, so preorder, postorder, and even level order all produce
the identical final tree. That is unusual — 005 onward, a parent needs its
children's answers first, and the order stops being optional.

================================================================================
⚠️  THE GO TRAP — swapping in two statements instead of one
================================================================================
    node.Left = node.Right         // Left is now the OLD Right
    node.Right = node.Left         // Right is now node.Left, which IS OLD RIGHT

The original left subtree is gone; both fields end up pointing at the same
subtree. Go's `a, b = b, a` form evaluates the ENTIRE right-hand side to
temporaries before writing either field, so the one-line swap is safe —
exactly like Python's tuple-unpacking swap. This is demoed live below with
real pointer addresses so the aliasing is unambiguous, not just "the values
looked wrong."

================================================================================
APPROACHES
================================================================================
Approach 0 (naive, don't code it): serialize to level-order, reverse each
   level, rebuild the tree. O(n) time but O(n) EXTRA space and it allocates
   n new nodes to do what n pointer swaps do in place. Name it, price it,
   move on.

Approach 1 (recursion, swap then descend) ✅ — the shape above. O(n) time,
   O(h) space, MUTATES in place.

Approach 2 (recursion, descend then swap) — postorder instead of preorder.
   Identical result; demonstrates the order-independence claim.

Approach 3 (iterative BFS, slice-as-queue) — pop a node, swap, push both
   children. O(n) time, O(w) space where w is the widest level — WIDER than
   the recursive form's O(h) on the same tree, so "iterative" is not
   automatically "cheaper."

Approach 4 (iterative DFS, explicit stack) ✅ — same loop with a stack
   instead of a queue. O(n) time, O(h) space — the version to reach for on
   an adversarially deep tree, since it never touches the call stack.

Approach 5 (pure function, no mutation) — allocate a brand-new tree instead
   of swapping in place:
       return &TreeNode{root.Val, invertPure(root.Right), invertPure(root.Left)}
   O(n) time, O(n) space, and the CALLER'S original tree is left completely
   untouched — worth offering whenever the interviewer says the input is
   shared or must stay immutable. Measured against the in-place version
   below, by pointer identity.

================================================================================
STEP BY STEP TRACE — preorder invert of [4,2,7,1,3,6,9]
================================================================================
            4                          4
          /   \                      /   \
         2     7                    7     2
        / \   / \                  / \   / \
       1   3 6   9                9   6 3   1

    visit 4: swap children      -> 4.Left=7, 4.Right=2
      visit 7 (now the left):    swap -> 7.Left=9, 7.Right=6
        visit 9, visit 6: leaves, nothing to swap
      visit 2 (now the right):   swap -> 2.Left=3, 2.Right=1
        visit 3, visit 1: leaves, nothing to swap

    Level order after each swap:
        start                 [4, 2, 7, 1, 3, 6, 9]
        after swapping at 4   [4, 7, 2, 6, 9, 1, 3]   <- whole subtrees moved
        after swapping at 7   [4, 7, 2, 9, 6, 1, 3]
        after swapping at 2   [4, 7, 2, 9, 6, 3, 1]   <- the answer

    The swap at node 4 moves node 7 AND EVERYTHING BENEATH IT to the left
    in a single assignment — pointers move subtrees; values inside are
    never touched.

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                      Time  Space  Mutates input?  Note
    ------------------------------ ----  -----  ---------------  --------------------
    Serialize, reverse, rebuild   O(n)  O(n)   no                allocates n nodes
    Recursion, swap-then-descend ✅ O(n) O(h)   YES               the answer
    Recursion, descend-then-swap  O(n)  O(h)   YES               same result
    Iterative BFS (queue)         O(n)  O(w)   YES               w up to ~n/2
    Iterative DFS (stack) ✅      O(n)  O(h)   YES               no call-stack risk
    Pure copy (no mutation)       O(n)  O(n)   no                for shared trees

================================================================================
EDGE CASES
================================================================================
    root == nil            -> nil, must not crash; the base case doubles as
                               the answer.
    single node              -> unchanged; both children nil, swap is a no-op.
    one-sided node            -> [1,2] becomes [1,nil,2]: nil PARTICIPATES in
                               the swap. Code that only swaps "if both
                               children non-nil" leaves these un-mirrored.
    perfectly symmetric tree  -> comes back IDENTICAL — makes symmetric
                               trees a useless test case for THIS problem
                               (it's the basis of LC 101, Symmetric Tree).
    very deep skewed chain    -> Go's goroutine stack GROWS (default cap up
                               to 1GB on 64-bit), so this rarely crashes the
                               recursive version at realistic sizes — but
                               the iterative stack form has no ceiling to
                               think about at all. Measured below.

================================================================================
COMMON MISTAKES
================================================================================
1. Swapping in two statements instead of one — see the GO TRAP section
   above. Demoed live with pointer identities below.
2. Swapping VALUES instead of child pointers (`a.Val, b.Val = b.Val, a.Val`
   across the two subtrees). Only mirrors a perfectly-shaped tree; on any
   asymmetric shape it produces something that isn't a mirror at all,
   because the structure never moved.
3. Forgetting to `return root` — Go's signature returns the tree; returning
   nil unconditionally makes every non-empty test fail even though the
   mutation happened correctly.
4. Guarding the swap with `if node.Left != nil && node.Right != nil`. One-
   sided nodes then keep their orientation. Swap unconditionally; nil swaps
   fine.
5. Doing this in place when the interviewer says the tree is shared or
   read-only. Say "this mutates the input" out loud and offer Approach 5.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Now do it iteratively.
A: Approach 3/4 — one worklist, swap on pop, push both children. Volunteer
   that the stack (DFS) version needs O(h) and the queue (BFS) version O(w),
   and that those differ enormously on a wide tree.

Q: Does traversal order matter?
A: No — the swap at a node is independent of every other node's result.
   Contrast with 005/009/010, where the parent needs its children's answers
   FIRST, forcing postorder.

Q: Do it without mutating the input.
A: Approach 5 — build new nodes with children crossed over. O(n) space, and
   proven below to leave the original tree's node objects untouched.

Q: How would you check whether a tree is symmetric?
A: Compare the tree with its own mirror pairwise, without mutating anything
   — pair (a.Left, b.Right) and (a.Right, b.Left) recursively. That's LC 101.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    LC 101   Symmetric Tree                — mirror-compare, no mutation
    LC 100   Same Tree                     — the un-mirrored twin (007)
    LC 951   Flip Equivalent Binary Trees  — invert only where it helps
    LC 617   Merge Two Binary Trees        — two trees, mutate in place
================================================================================
*/

// invertTree: recursion, swap then descend. O(n) time, O(h) space, in place.
func invertTree(root *TreeNode) *TreeNode {
	if root == nil {
		return nil
	}
	root.Left, root.Right = root.Right, root.Left // simultaneous swap
	invertTree(root.Left)
	invertTree(root.Right)
	return root
}

// invertTreePostorder: descend then swap. Same result — order is free here.
func invertTreePostorder(root *TreeNode) *TreeNode {
	if root == nil {
		return nil
	}
	invertTreePostorder(root.Left)
	invertTreePostorder(root.Right)
	root.Left, root.Right = root.Right, root.Left
	return root
}

// invertTreeBFS: iterative, slice-as-queue. O(n) time, O(w) space.
func invertTreeBFS(root *TreeNode) *TreeNode {
	if root == nil {
		return nil
	}
	queue := []*TreeNode{root}
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]
		node.Left, node.Right = node.Right, node.Left
		if node.Left != nil {
			queue = append(queue, node.Left)
		}
		if node.Right != nil {
			queue = append(queue, node.Right)
		}
	}
	return root
}

// invertTreeDFSStack: iterative, explicit stack. O(n) time, O(h) space, no
// recursion involved at all.
func invertTreeDFSStack(root *TreeNode) *TreeNode {
	if root == nil {
		return nil
	}
	stack := []*TreeNode{root}
	for len(stack) > 0 {
		node := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		node.Left, node.Right = node.Right, node.Left
		if node.Left != nil {
			stack = append(stack, node.Left)
		}
		if node.Right != nil {
			stack = append(stack, node.Right)
		}
	}
	return root
}

// invertTreePure builds a brand-new mirrored tree; the input is untouched.
// O(n) time, O(n) space.
func invertTreePure(root *TreeNode) *TreeNode {
	if root == nil {
		return nil
	}
	return &TreeNode{
		Val:   root.Val,
		Left:  invertTreePure(root.Right),
		Right: invertTreePure(root.Left),
	}
}

// ---------------------------------------------------------------------------
// Deliberate breakage, kept for the demo.
// ---------------------------------------------------------------------------

// invertTreeBrokenTwoStatements swaps in two statements: the second line
// reads the field the first line just overwrote.
func invertTreeBrokenTwoStatements(root *TreeNode) *TreeNode {
	if root == nil {
		return nil
	}
	root.Left = root.Right
	root.Right = root.Left // <-- already the new Left; original left is lost
	invertTreeBrokenTwoStatements(root.Left)
	invertTreeBrokenTwoStatements(root.Right)
	return root
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

func buildSkewed(n int, left bool) *TreeNode {
	if n == 0 {
		return nil
	}
	root := &TreeNode{Val: 0}
	curr := root
	for i := 1; i < n; i++ {
		node := &TreeNode{Val: i}
		if left {
			curr.Left = node
		} else {
			curr.Right = node
		}
		curr = node
	}
	return root
}

// allNodes returns every distinct *TreeNode reachable, by pointer identity.
func allNodes(root *TreeNode) map[*TreeNode]bool {
	seen := map[*TreeNode]bool{}
	var walk func(*TreeNode)
	walk = func(n *TreeNode) {
		if n == nil || seen[n] {
			return
		}
		seen[n] = true
		walk(n.Left)
		walk(n.Right)
	}
	walk(root)
	return seen
}

// countSlots counts total filled child slots via a plain traversal — if it
// exceeds len(allNodes(root)), some node is referenced from more than one
// parent slot (aliased), since allNodes dedupes by pointer identity.
func countSlots(root *TreeNode) int {
	if root == nil {
		return 0
	}
	total := 0
	stack := []*TreeNode{root}
	steps := 0
	for len(stack) > 0 && steps < 100_000 {
		steps++
		n := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if n == nil {
			continue
		}
		total++
		stack = append(stack, n.Left, n.Right)
	}
	return total
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

func status(ok bool) string {
	if ok {
		return "PASS"
	}
	return "FAIL"
}

func main() {
	type testCase struct {
		values []interface{}
		want   []interface{}
	}
	cases := []testCase{
		{[]interface{}{4, 2, 7, 1, 3, 6, 9}, []interface{}{4, 7, 2, 9, 6, 3, 1}},
		{[]interface{}{2, 1, 3}, []interface{}{2, 3, 1}},
		{[]interface{}{}, nil},
		{[]interface{}{1}, []interface{}{1}},
		{[]interface{}{1, 2}, []interface{}{1, nil, 2}},
	}

	allOK := true

	fmt.Println("--- correctness: recursion (swap then descend) ---")
	for _, tc := range cases {
		got := toLevelOrder(invertTree(buildTree(tc.values)))
		ok := levelOrderEqual(got, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  %v -> %v (want %v)\n", status(ok), tc.values, got, tc.want)
	}

	fmt.Println("\n--- correctness: the other implementations ---")
	impls := []struct {
		name string
		fn   func(*TreeNode) *TreeNode
	}{
		{"postorder (descend then swap)", invertTreePostorder},
		{"iterative BFS                ", invertTreeBFS},
		{"iterative DFS (stack)        ", invertTreeDFSStack},
		{"pure copy                    ", invertTreePure},
	}
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			if !levelOrderEqual(toLevelOrder(impl.fn(buildTree(tc.values))), tc.want) {
				ok = false
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases)\n", status(ok), impl.name, len(cases))
	}

	// ------------------------------------------------------------------
	// Live proof: in-place mutation vs pure copy, by ADDRESS.
	// ------------------------------------------------------------------
	fmt.Println("\n--- live proof: in-place mutation vs a pure (non-mutating) copy ---")
	original := buildTree([]interface{}{4, 2, 7, 1, 3, 6, 9})
	rootAddrBefore := fmt.Sprintf("%p", original)
	leftAddrBefore := fmt.Sprintf("%p", original.Left) // node valued 2

	mutated := invertTree(original)
	fmt.Printf("  in-place: root address before == after invert: %v (%s)\n",
		fmt.Sprintf("%p", mutated) == rootAddrBefore, rootAddrBefore)
	fmt.Printf("  in-place: original 'left child' node (addr %s) is now the RIGHT child: %v\n",
		leftAddrBefore, fmt.Sprintf("%p", mutated.Right) == leftAddrBefore)

	pureInput := buildTree([]interface{}{4, 2, 7, 1, 3, 6, 9})
	pureInputBefore := toLevelOrder(pureInput)
	pureResult := invertTreePure(pureInput)
	pureInputAfter := toLevelOrder(pureInput)
	untouched := levelOrderEqual(pureInputBefore, pureInputAfter)
	sameNodes := allNodes(pureInput)
	newNodes := allNodes(pureResult)
	disjoint := true
	for n := range newNodes {
		if sameNodes[n] {
			disjoint = false
		}
	}
	fmt.Printf("  pure copy: caller's original tree unchanged after invertTreePure: %v (%v -> %v)\n",
		untouched, pureInputBefore, pureInputAfter)
	fmt.Printf("  pure copy: result tree shares ZERO node pointers with the input: %v\n", disjoint)
	allOK = allOK && untouched && disjoint

	// ------------------------------------------------------------------
	// The two-statement swap bug, proven by aliasing.
	// ------------------------------------------------------------------
	fmt.Println("\n--- Go trap: swapping in two statements aliases a subtree ---")
	good := toLevelOrder(invertTree(buildTree([]interface{}{4, 2, 7, 1, 3, 6, 9})))
	brokenRoot := buildTree([]interface{}{4, 2, 7, 1, 3, 6, 9})
	bad := invertTreeBrokenTwoStatements(brokenRoot)
	badLevel := toLevelOrder(bad)
	fmt.Printf("  one-line simultaneous swap : %v  <- correct\n", good)
	fmt.Printf("  two-statement swap         : %v  <- WRONG\n", badLevel)
	// Count DISTINCT node objects reachable vs total child SLOTS filled. If
	// slots > distinct nodes, some node object is referenced from more than
	// one place in the "tree" — it is aliased, not just wrong-valued.
	distinct := len(allNodes(bad))
	slots := countSlots(bad)
	fmt.Printf("  distinct node OBJECTS reachable: %d\n", distinct)
	fmt.Printf("  child slots filled              : %d\n", slots)
	fmt.Printf("  slots exceed distinct nodes -> some node is aliased into two parents: %v\n",
		slots > distinct)
	allOK = allOK && !levelOrderEqual(good, badLevel) && slots > distinct

	// ------------------------------------------------------------------
	// Deep skewed chain: Go's growable stack keeps recursion fine, but the
	// iterative form never has to think about it at all.
	// ------------------------------------------------------------------
	fmt.Println("\n--- deep skewed chain, n=100000: recursion vs iterative agree ---")
	n := 100_000
	chainRec := buildSkewed(n, true)
	invertTree(chainRec)
	// a left chain, inverted, becomes a right chain
	node, seenRec := chainRec, 0
	for node != nil {
		seenRec++
		node = node.Right
	}
	chainIter := buildSkewed(n, true)
	invertTreeDFSStack(chainIter)
	node, seenIter := chainIter, 0
	for node != nil {
		seenIter++
		node = node.Right
	}
	ok := seenRec == n && seenIter == n
	allOK = allOK && ok
	fmt.Printf("  recursion : left chain of %d became a right chain of %d nodes -> %v\n", n, seenRec, seenRec == n)
	fmt.Printf("  iterative : left chain of %d became a right chain of %d nodes -> %v\n", n, seenIter, seenIter == n)
	fmt.Println("  Go's goroutine stack grows (default cap up to 1GB), so recursion")
	fmt.Println("  survives this depth comfortably. The iterative stack form still")
	fmt.Println("  wins the argument for an ADVERSARIALLY larger or truly pathological")
	fmt.Println("  input, since it never touches the call stack at all.")

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
