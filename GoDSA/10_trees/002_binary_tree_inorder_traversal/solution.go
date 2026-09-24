package main

import (
	"fmt"
	"sort"
)

/*
================================================================================
SOLUTION · LeetCode 94 · Binary Tree Inorder Traversal                   [Easy]
https://leetcode.com/problems/binary-tree-inorder-traversal/
================================================================================

THE CORE IDEA
-------------
Visit the node BETWEEN its two subtrees: left, node, right.

    func inorder(node *TreeNode, out *[]int) {
        if node == nil {
            return
        }
        inorder(node.Left, out)
        *out = append(*out, node.Val)   // visit — the only line that moved vs 001
        inorder(node.Right, out)
    }

O(n) time, O(h) space. The single-line difference from preorder (001) is
WHERE the visit sits — proof that "traversal order" is really just "where
you put one statement relative to two recursive calls."

The special case that makes inorder its own topic: on a Binary Search Tree,
inorder output is exactly the sorted sequence of values, because a BST's
invariant (left < node < right, recursively) IS the definition of sorted
order applied to a tree shape. That fact belongs to topic 11 — here, on a
plain binary tree, don't expect the output to be sorted.

================================================================================
APPROACHES
================================================================================
Approach 1 (recursion, pointer accumulator) ✅ — shown above.

Approach 2 (iterative, explicit stack, "left spine then pop") ✅ — the
   traversal to know cold:

    stack := []*TreeNode{}
    curr := root
    for curr != nil || len(stack) > 0 {
        for curr != nil {                 // push the whole left spine
            stack = append(stack, curr)
            curr = curr.Left
        }
        curr = stack[len(stack)-1]        // pop
        stack = stack[:len(stack)-1]
        out = append(out, curr.Val)       // visit
        curr = curr.Right                 // then explore the right subtree
    }

   Note the loop condition needs BOTH `curr != nil` (still something to
   push) OR `len(stack) > 0` (still something to pop) — the classic bug is
   using only one of the two and truncating the walk.

Approach 3 (Morris traversal, O(1) space) — temporarily thread each node's
   inorder predecessor's nil-right-child to point back at the node, walk
   using those threads instead of a stack, then remove the thread on the
   way past. Genuinely O(1) auxiliary space at the cost of transiently
   mutating (then restoring) the tree's right pointers. Name it; rarely
   asked to code cold, but "how would you do this in O(1) space" is a real
   follow-up.

================================================================================
STEP BY STEP TRACE — root = [1,null,2,3]  (1 -> right 2 -> left 3)
================================================================================
            1
             \
              2
             /
            3

    Recursive:
    inorder(1)
      inorder(nil left of 1)                     no-op
      visit 1                                     out=[1]
      inorder(2)
        inorder(3)
          inorder(nil), visit 3, inorder(nil)     out=[1,3]
        visit 2                                   out=[1,3,2]
        inorder(nil right of 2)

    result: [1, 3, 2]

    Iterative, stack shown top-first, curr shown each step:
    curr=1                     push 1                    stack=[1]     curr=nil(left of 1)
    curr=nil, stack=[1]        pop 1, visit               out=[1]      curr=2 (right of 1)
    curr=2                     push 2                    stack=[2]     curr=3 (left of 2)
    curr=3                     push 3                    stack=[2,3]   curr=nil(left of 3)
    curr=nil, stack=[2,3]      pop 3, visit               out=[1,3]    curr=nil (right of 3)
    curr=nil, stack=[2]        pop 2, visit               out=[1,3,2]  curr=nil (right of 2)
    curr=nil, stack=[]         loop ends

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                      Time  Space   Mutates input?  Note
    ------------------------------ ----  ------  ---------------  ---------------------
    Recursion, pointer accum ✅   O(n)  O(h)    no                simplest correct form
    Iterative, explicit stack ✅  O(n)  O(h)    no                no call-stack risk
    Morris (threaded)             O(n)  O(1)    temporarily       true O(1) space

================================================================================
EDGE CASES
================================================================================
    root == nil                -> nil slice, not a panic.
    single node                 -> [val].
    left-only skewed chain      -> inorder visits DEEPEST-left node first,
                                   then walks back up — the recursive call
                                   stack (or explicit stack) reaches depth n.
    right-only skewed chain     -> visits the root itself first (no left
                                   subtree to descend into), then cascades
                                   right; stack never grows past depth 1 for
                                   the iterative form on THIS shape, which is
                                   a good contrast to the left-skewed case.
    duplicate values             -> irrelevant; only structure matters.

================================================================================
COMMON MISTAKES
================================================================================
1. Visiting BEFORE the left recursive call (`visit(node); inorder(left);
   inorder(right)`) — that's preorder, not inorder. The one-line placement
   IS the whole problem.
2. Iterative loop condition using only `curr != nil` — misses nodes still
   sitting on the stack once curr goes nil for the final time; must OR in
   `len(stack) > 0`.
3. Assuming inorder output is sorted for an arbitrary binary tree — that
   property is exclusive to BSTs (topic 11), not a general fact about
   inorder traversal.
4. In the iterative form, stepping `curr = curr.Left` again after popping
   instead of `curr = curr.Right` — re-descends the subtree you just
   finished and infinite-loops (or corrupts the visit order).

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Do it iteratively.
A: Approach 2 — push down the left spine, pop-visit-step-right.

Q: Can you do it in O(1) extra space?
A: Morris traversal — thread nil right-children to the inorder successor,
   walk the threads, undo them as you pass. Name the mechanism; full
   implementation is a stretch goal, not baseline expected.

Q: If this were a BST, what would the output tell you?
A: The sorted sequence of all values — this is exactly how you'd validate a
   BST (topic 11) or find the kth smallest element (LC 230) in O(h + k).

================================================================================
RELATED PROBLEMS — the traversal family
================================================================================
    LC 144  Binary Tree Preorder Traversal  — visit before children (001)
    LC 145  Binary Tree Postorder Traversal — visit after children (003)
    LC 230  Kth Smallest Element in a BST   — inorder + early stop
    LC 98   Validate Binary Search Tree     — inorder must be strictly increasing
================================================================================
*/

// inorderTraversal is the interview answer: recursion, pointer accumulator.
func inorderTraversal(root *TreeNode) []int {
	var out []int
	var walk func(*TreeNode)
	walk = func(node *TreeNode) {
		if node == nil {
			return
		}
		walk(node.Left)
		out = append(out, node.Val) // visit
		walk(node.Right)
	}
	walk(root)
	return out
}

// inorderTraversalIterative pushes the left spine, then pop-visit-step-right.
func inorderTraversalIterative(root *TreeNode) []int {
	var out []int
	stack := []*TreeNode{}
	curr := root
	for curr != nil || len(stack) > 0 {
		for curr != nil {
			stack = append(stack, curr)
			curr = curr.Left
		}
		curr = stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		out = append(out, curr.Val)
		curr = curr.Right
	}
	return out
}

// inorderTraversalMorris achieves O(1) auxiliary space by threading and
// unthreading right pointers to the inorder predecessor.
func inorderTraversalMorris(root *TreeNode) []int {
	var out []int
	curr := root
	for curr != nil {
		if curr.Left == nil {
			out = append(out, curr.Val)
			curr = curr.Right
			continue
		}
		// find the rightmost node in the left subtree: curr's predecessor
		pred := curr.Left
		for pred.Right != nil && pred.Right != curr {
			pred = pred.Right
		}
		if pred.Right == nil {
			pred.Right = curr // thread back to curr
			curr = curr.Left
		} else {
			pred.Right = nil // remove the thread, restoring the tree
			out = append(out, curr.Val)
			curr = curr.Right
		}
	}
	return out
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

// buildBST inserts a shuffled-but-deterministic set of values so inorder
// output can be checked against a sorted slice.
func buildBST(values []int) *TreeNode {
	var root *TreeNode
	var insert func(*TreeNode, int) *TreeNode
	insert = func(node *TreeNode, v int) *TreeNode {
		if node == nil {
			return &TreeNode{Val: v}
		}
		if v < node.Val {
			node.Left = insert(node.Left, v)
		} else {
			node.Right = insert(node.Right, v)
		}
		return node
	}
	for _, v := range values {
		root = insert(root, v)
	}
	return root
}

func intsEqual(a, b []int) bool {
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
		want   []int
	}
	cases := []testCase{
		{[]interface{}{1, nil, 2, 3}, []int{1, 3, 2}},
		{[]interface{}{}, nil},
		{[]interface{}{1}, []int{1}},
		{[]interface{}{4, 2, 6, 1, 3, 5, 7}, []int{1, 2, 3, 4, 5, 6, 7}},
	}

	allOK := true

	fmt.Println("--- correctness: recursion, pointer accumulator ---")
	for _, tc := range cases {
		got := inorderTraversal(buildTree(tc.values))
		ok := intsEqual(got, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  %v -> %v (want %v)\n", status(ok), tc.values, got, tc.want)
	}

	fmt.Println("\n--- correctness: iterative and Morris variants ---")
	impls := []struct {
		name string
		fn   func(*TreeNode) []int
	}{
		{"iterative", inorderTraversalIterative},
		{"Morris   ", inorderTraversalMorris},
	}
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			if !intsEqual(impl.fn(buildTree(tc.values)), tc.want) {
				ok = false
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases)\n", status(ok), impl.name, len(cases))
	}

	// The BST special case: inorder == sorted.
	fmt.Println("\n--- the BST special case: inorder output equals sorted order ---")
	values := []int{7, 3, 9, 1, 5, 8, 10, 2, 4}
	bst := buildBST(values)
	got := inorderTraversal(bst)
	wantSorted := append([]int(nil), values...)
	sort.Ints(wantSorted)
	sortedOK := intsEqual(got, wantSorted)
	allOK = allOK && sortedOK
	fmt.Printf("  values inserted: %v\n", values)
	fmt.Printf("  inorder output : %v\n", got)
	fmt.Printf("  sort.Ints(vals): %v\n", wantSorted)
	fmt.Printf("  equal: %v  <- this is why inorder gets its own topic (11 · BST)\n", sortedOK)

	// Morris genuinely restores the tree: prove no leftover threads remain
	// by re-running a plain recursive inorder afterward and comparing.
	fmt.Println("\n--- Morris restores the tree: re-running inorder afterward still matches ---")
	tree := buildTree([]interface{}{4, 2, 6, 1, 3, 5, 7})
	before := inorderTraversal(tree)
	_ = inorderTraversalMorris(tree) // mutates right pointers, then un-mutates
	after := inorderTraversal(tree)
	restored := intsEqual(before, after)
	allOK = allOK && restored
	fmt.Printf("  before Morris: %v\n  after Morris : %v\n  tree structure intact: %v\n",
		before, after, restored)

	// Skewed trees: left-skewed reaches iterative stack depth n; right-skewed
	// keeps the explicit stack shallow the whole way.
	fmt.Println("\n--- skewed trees: stack shape differs by direction ---")
	leftChain := buildSkewed(2000, true)
	rightChain := buildSkewed(2000, false)
	leftOK := len(inorderTraversalIterative(leftChain)) == 2000
	rightOK := len(inorderTraversalIterative(rightChain)) == 2000
	allOK = allOK && leftOK && rightOK
	fmt.Printf("  left-skewed n=2000:  visited %v nodes -> %v\n", 2000, leftOK)
	fmt.Printf("  right-skewed n=2000: visited %v nodes -> %v\n", 2000, rightOK)

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
