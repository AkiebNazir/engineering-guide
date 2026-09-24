package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 144 · Binary Tree Preorder Traversal                 [Easy]
https://leetcode.com/problems/binary-tree-preorder-traversal/
================================================================================

THE CORE IDEA
-------------
Visit the node BEFORE its children: node, then left, then right. The
recursive shape is a direct transcription of that sentence:

    func preorder(node *TreeNode, out *[]int) {
        if node == nil {
            return
        }
        *out = append(*out, node.Val)   // visit
        preorder(node.Left, out)
        preorder(node.Right, out)
    }

O(n) time — every node visited once. O(h) space for the call stack, h =
height (O(log n) balanced, O(n) skewed).

================================================================================
APPROACHES
================================================================================
Approach 1 (recursion, pointer accumulator) ✅ — thread `*[]int` through the
   calls so every frame appends into the SAME backing slice. One allocation
   growth pattern, no concatenation.

Approach 2 (recursion, return-and-concat) — each call returns its own
   `[]int` and the caller `append`s the children's results. Easier to read,
   costs more small slice allocations for a deep tree — shown for contrast.

Approach 3 (iterative, explicit stack) ✅ — Go has no tail-call optimization,
   so a genuinely huge skewed tree can threaten the goroutine stack under
   recursion. Push right THEN left so left pops first (visit order: node,
   left, right).

    stack := []*TreeNode{root}
    for len(stack) > 0 {
        node := stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        if node == nil { continue }
        out = append(out, node.Val)
        stack = append(stack, node.Right, node.Left)  // right first, left pops first
    }

================================================================================
STEP BY STEP TRACE — root = [1,null,2,3]  (1 with only a right child 2, which has left child 3)
================================================================================
            1
             \
              2
             /
            3

    preorder(1): visit 1            out=[1]
      preorder(nil left)            no-op
      preorder(2):  visit 2         out=[1,2]
        preorder(3): visit 3        out=[1,2,3]
          preorder(nil), preorder(nil)
        preorder(nil right of 2)

    result: [1, 2, 3]

Iterative trace, same tree, stack shown top-first:
    push 1                          stack=[1]
    pop 1, visit               out=[1]   push right(2), left(nil)   stack=[2,nil]
    pop nil -> skip                 stack=[2]
    pop 2, visit                out=[1,2]  push right(nil), left(3) stack=[nil,3]
    pop 3, visit                out=[1,2,3] push right(nil) left(nil) stack=[nil,nil,nil]
    remaining pops are all nil, skipped

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time   Space   Mutates input?   Note
    ---------------------------  -----  ------  ---------------  ------------------
    Recursion, pointer accum ✅  O(n)   O(h)    no                fewest allocations
    Recursion, return+concat     O(n)   O(h+n)  no                extra slice copies
    Iterative, explicit stack ✅ O(n)   O(h)    no                no call-stack risk

================================================================================
EDGE CASES
================================================================================
    root == nil                -> [] (nil slice), not a panic. This is the
                                   base case doing double duty as the answer.
    single node                 -> [val].
    left-only chain (skewed)    -> tests recursion depth; iterative version
                                   never risks the goroutine stack limit.
    right-only chain (skewed)   -> same, other direction.
    negative / duplicate values -> irrelevant, only structure matters.

================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the nil check and calling `node.Val` on a nil pointer —
   PANICS with "invalid memory address or nil pointer dereference", not a
   catchable exception the way Python's AttributeError is.
2. Visiting AFTER recursing into children instead of before — that's
   postorder (003), a different traversal entirely.
3. In the iterative version, pushing left before right — pops in the wrong
   order and visits right-before-left.
4. Returning `[]int{}` vs `nil` for the empty case — LeetCode accepts both,
   but be consistent; this file returns nil for "no nodes."

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Do it iteratively.
A: Approach 3 — explicit `[]*TreeNode` stack, push right then left.

Q: Why would the iterative form ever matter here?
A: A skewed (effectively linked-list) tree recurses n frames deep. Go's
   goroutine stack grows (default cap up to 1GB on 64-bit) so this rarely
   crashes in practice for interview-sized inputs, but on an adversarially
   deep or huge tree the iterative form has no such ceiling to worry about.

Q: Morris traversal — O(1) space?
A: Yes, by temporarily threading nil right-children to their inorder
   successor and undoing the threads as you go. It changes the tree
   structure DURING the walk (and restores it), so it's a real mutate-then-
   unmutate trick — worth naming, rarely required to implement live.

================================================================================
RELATED PROBLEMS — the traversal family
================================================================================
    LC 94   Binary Tree Inorder Traversal   — visit between children (002)
    LC 145  Binary Tree Postorder Traversal — visit after children (003)
    LC 102  Binary Tree Level Order Traversal — BFS, not DFS
    LC 297  Serialize and Deserialize Binary Tree — preorder + null markers
================================================================================
*/

// preorderTraversal is the interview answer: recursion, pointer accumulator.
// Time O(n), space O(h).
func preorderTraversal(root *TreeNode) []int {
	var out []int
	var walk func(*TreeNode)
	walk = func(node *TreeNode) {
		if node == nil {
			return
		}
		out = append(out, node.Val) // visit
		walk(node.Left)
		walk(node.Right)
	}
	walk(root)
	return out
}

// preorderTraversalConcat returns-and-concats instead of threading a pointer.
func preorderTraversalConcat(root *TreeNode) []int {
	if root == nil {
		return nil
	}
	out := []int{root.Val}
	out = append(out, preorderTraversalConcat(root.Left)...)
	out = append(out, preorderTraversalConcat(root.Right)...)
	return out
}

// preorderTraversalIterative uses an explicit stack. No call-stack risk.
func preorderTraversalIterative(root *TreeNode) []int {
	if root == nil {
		return nil
	}
	var out []int
	stack := []*TreeNode{root}
	for len(stack) > 0 {
		node := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if node == nil {
			continue
		}
		out = append(out, node.Val)
		stack = append(stack, node.Right, node.Left) // right first: left pops first
	}
	return out
}

// ---------------------------------------------------------------------------
// Test helpers — level-order tree builder, reused (duplicated per package on
// purpose; see CONTEXT.md §4).
// ---------------------------------------------------------------------------

// buildTree builds a tree from a level-order slice; a nil entry means "no
// node here." Mirrors LeetCode's array representation.
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

// buildSkewed builds a left- or right-only chain of n nodes valued 0..n-1.
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
		{[]interface{}{1, nil, 2, 3}, []int{1, 2, 3}},
		{[]interface{}{}, nil},
		{[]interface{}{1}, []int{1}},
		{[]interface{}{1, 2, 3, 4, 5}, []int{1, 2, 4, 5, 3}},
	}

	allOK := true

	fmt.Println("--- correctness: recursion, pointer accumulator ---")
	for _, tc := range cases {
		got := preorderTraversal(buildTree(tc.values))
		ok := intsEqual(got, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  %v -> %v (want %v)\n", status(ok), tc.values, got, tc.want)
	}

	fmt.Println("\n--- correctness: return+concat and iterative variants ---")
	impls := []struct {
		name string
		fn   func(*TreeNode) []int
	}{
		{"return+concat", preorderTraversalConcat},
		{"iterative    ", preorderTraversalIterative},
	}
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			got := impl.fn(buildTree(tc.values))
			if !intsEqual(got, tc.want) {
				ok = false
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases)\n", status(ok), impl.name, len(cases))
	}

	// Nil-dereference demo: prove the panic is real, and recover from it.
	fmt.Println("\n--- Go-specific: nil pointer dereference panics, unlike Python's AttributeError ---")
	func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Printf("  recovered from panic: %v\n", r)
			}
		}()
		var n *TreeNode // nil
		fmt.Println("  about to read n.Val on a nil *TreeNode...")
		_ = n.Val // this line panics
		fmt.Println("  unreachable")
	}()

	// Skewed-tree depth: recursion still fine at interview-sized n thanks to
	// the growable goroutine stack, but the iterative form has no ceiling to
	// think about at all.
	fmt.Println("\n--- skewed tree, n = 5000: recursion vs iterative agree ---")
	deep := buildSkewed(5000, true)
	rec := preorderTraversal(deep)
	itr := preorderTraversalIterative(deep)
	agree := intsEqual(rec, itr) && len(rec) == 5000
	allOK = allOK && agree
	fmt.Printf("  lengths equal and match n=5000: %v\n", agree)

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
