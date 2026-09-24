package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 145 · Binary Tree Postorder Traversal                [Easy]
https://leetcode.com/problems/binary-tree-postorder-traversal/
================================================================================

THE CORE IDEA
-------------
Visit the node LAST, after both children:

    func postorder(node *TreeNode, out *[]int) {
        if node == nil {
            return
        }
        postorder(node.Left, out)
        postorder(node.Right, out)
        *out = append(*out, node.Val)   // visit — now last
    }

O(n) time, O(h) space. Postorder is the traversal every "compute a node's
answer from its children's answers" algorithm actually performs: height
(005), balance (009), diameter (010) are all postorder recursion with the
visit step replaced by "combine the two child results." Recognizing "this
needs children's answers before the parent's" as "this is a postorder
problem" is the transferable skill.

================================================================================
APPROACHES
================================================================================
Approach 1 (recursion, pointer accumulator) ✅ — shown above.

Approach 2 (iterative, reverse of a root-right-left "preorder") ✅ — the
   standard trick. Build root, right, left (mirror of normal preorder:
   push LEFT before RIGHT so RIGHT pops first), then reverse the output:

    stack := []*TreeNode{root}
    for len(stack) > 0 {
        node := pop(stack)
        out = append(out, node.Val)             // build root-right-left
        stack = append(stack, node.Left, node.Right)  // left pushed first, right pops first
    }
    reverse(out)                                 // -> left-right-root

Approach 3 (iterative, single stack with a "last visited" tracker) — walk
   down the left spine like inorder, but before popping a node check
   whether its right child exists AND hasn't been visited yet; if so,
   descend right first. More faithful to "true" postorder mechanics, more
   code, more edge cases to get wrong — the reverse trick is preferred
   under time pressure and is what's benchmarked below.

================================================================================
STEP BY STEP TRACE — root = [1,null,2,3]  (1 -> right 2 -> left 3)
================================================================================
            1
             \
              2
             /
            3

    Recursive:
    postorder(1)
      postorder(nil left of 1)                 no-op
      postorder(2)
        postorder(3)
          postorder(nil), postorder(nil)
          visit 3                                out=[3]
        postorder(nil right of 2)
        visit 2                                  out=[3,2]
      visit 1                                    out=[3,2,1]

    result: [3, 2, 1]

    Iterative (root-right-left, then reverse), stack top-first:
    push 1                                stack=[1]
    pop 1, append -> build=[1]            push left(nil), right(2)   stack=[nil,2]
    pop 2, append -> build=[1,2]          push left(3),   right(nil) stack=[nil,3,nil]
    pop nil -> skip                       stack=[nil,3]
    pop 3, append -> build=[1,2,3]        push left(nil), right(nil) stack=[nil,3,nil,nil]
    remaining pops are all nil, skipped
    build = [1, 2, 3]  ->  reverse  ->  [3, 2, 1]   <- matches

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time  Space   Mutates input?  Note
    ------------------------------- ----  ------  ---------------  --------------------
    Recursion, pointer accum ✅    O(n)  O(h)    no                shape every bottom-
                                                                     up algorithm reuses
    Iterative, reverse trick ✅    O(n)  O(h)    no                simplest iterative
    Iterative, "last visited"      O(n)  O(h)    no                no reverse needed,
                                                                     more bookkeeping

================================================================================
EDGE CASES
================================================================================
    root == nil                -> nil slice.
    single node                 -> [val] (reversing a 1-element slice is a
                                   no-op — easy to forget to test).
    left-only skewed chain      -> postorder visits DEEPEST node first, root
                                   last; recursion depth n either way.
    right-only skewed chain     -> same visit order (deepest first, root
                                   last), different physical path.
    duplicate values             -> irrelevant; only structure matters.

================================================================================
COMMON MISTAKES
================================================================================
1. Visiting between the two recursive calls (`postorder(left); visit(node);
   postorder(right)`) — that's inorder (002), not postorder.
2. Building root-LEFT-right and reversing (instead of root-RIGHT-left) —
   reverses to root-right-left backwards, i.e. NOT left-right-root. The
   push order in Approach 2 must put LEFT on the stack first so RIGHT pops
   (and gets appended) first, since the final reverse flips everything.
3. Forgetting the final reverse entirely — this is far and away the most
   common bug reported for this exact LeetCode problem.
4. Confusing this with "process children before parent, but output in the
   order visited" — postorder's OUTPUT order and its VISIT order are the
   same thing here; there's no separate collection phase.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Do it iteratively.
A: Approach 2 — root-right-left, then reverse. Say the trick out loud:
   reversing "root-right-left" gives "left-right-root."

Q: Without reversing?
A: Approach 3 — single stack, peek instead of pop, descend right first if
   it exists and hasn't been visited, otherwise pop-visit.

Q: Where does postorder show up beyond this problem?
A: Anywhere a parent's answer needs both children's answers first: height
   (005), diameter (010, with a closure-captured running max), balance
   check (009), tree deletion in languages without GC, expression-tree
   evaluation.

================================================================================
RELATED PROBLEMS — the traversal family
================================================================================
    LC 144  Binary Tree Preorder Traversal  — visit before children (001)
    LC 94   Binary Tree Inorder Traversal   — visit between children (002)
    LC 104  Maximum Depth of Binary Tree    — postorder, visit = combine heights (005)
    LC 543  Diameter of Binary Tree         — postorder + closure-captured max (010)
================================================================================
*/

// postorderTraversal is the interview answer: recursion, pointer accumulator.
func postorderTraversal(root *TreeNode) []int {
	var out []int
	var walk func(*TreeNode)
	walk = func(node *TreeNode) {
		if node == nil {
			return
		}
		walk(node.Left)
		walk(node.Right)
		out = append(out, node.Val) // visit — last
	}
	walk(root)
	return out
}

// postorderTraversalIterative builds root-right-left then reverses.
func postorderTraversalIterative(root *TreeNode) []int {
	if root == nil {
		return nil
	}
	var build []int
	stack := []*TreeNode{root}
	for len(stack) > 0 {
		node := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if node == nil {
			continue
		}
		build = append(build, node.Val)
		stack = append(stack, node.Left, node.Right) // left first: right pops first
	}
	// reverse in place: root-right-left -> left-right-root
	for i, j := 0, len(build)-1; i < j; i, j = i+1, j-1 {
		build[i], build[j] = build[j], build[i]
	}
	return build
}

// postorderTraversalLastVisited avoids the reverse with a single stack and a
// "last node visited" tracker.
func postorderTraversalLastVisited(root *TreeNode) []int {
	var out []int
	stack := []*TreeNode{}
	curr := root
	var lastVisited *TreeNode
	for curr != nil || len(stack) > 0 {
		for curr != nil {
			stack = append(stack, curr)
			curr = curr.Left
		}
		peek := stack[len(stack)-1]
		if peek.Right != nil && lastVisited != peek.Right {
			curr = peek.Right
		} else {
			out = append(out, peek.Val)
			lastVisited = peek
			stack = stack[:len(stack)-1]
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
		{[]interface{}{1, nil, 2, 3}, []int{3, 2, 1}},
		{[]interface{}{}, nil},
		{[]interface{}{1}, []int{1}},
		{[]interface{}{1, 2, 3, 4, 5}, []int{4, 5, 2, 3, 1}},
	}

	allOK := true

	fmt.Println("--- correctness: recursion, pointer accumulator ---")
	for _, tc := range cases {
		got := postorderTraversal(buildTree(tc.values))
		ok := intsEqual(got, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  %v -> %v (want %v)\n", status(ok), tc.values, got, tc.want)
	}

	fmt.Println("\n--- correctness: iterative variants ---")
	impls := []struct {
		name string
		fn   func(*TreeNode) []int
	}{
		{"reverse trick    ", postorderTraversalIterative},
		{"last-visited     ", postorderTraversalLastVisited},
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

	// Prove the reverse is not optional: show the raw root-right-left build.
	fmt.Println("\n--- why the reverse is mandatory ---")
	tree := buildTree([]interface{}{1, nil, 2, 3})
	var rawBuild []int
	stack := []*TreeNode{tree}
	for len(stack) > 0 {
		n := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if n == nil {
			continue
		}
		rawBuild = append(rawBuild, n.Val)
		stack = append(stack, n.Left, n.Right)
	}
	want := []int{3, 2, 1}
	fmt.Printf("  root-right-left, UNREVERSED : %v\n", rawBuild)
	fmt.Printf("  actual postorder answer      : %v\n", want)
	unreversedWrong := !intsEqual(rawBuild, want)
	fmt.Printf("  they differ (reverse is required): %v\n", unreversedWrong)
	allOK = allOK && unreversedWrong

	// Skewed trees, both directions, both iterative forms agree with recursion.
	fmt.Println("\n--- skewed trees: all three implementations agree, n=3000 ---")
	for _, left := range []bool{true, false} {
		chain := buildSkewed(3000, left)
		rec := postorderTraversal(chain)
		rev := postorderTraversalIterative(chain)
		lv := postorderTraversalLastVisited(chain)
		ok := intsEqual(rec, rev) && intsEqual(rec, lv) && len(rec) == 3000
		allOK = allOK && ok
		dir := "left"
		if !left {
			dir = "right"
		}
		fmt.Printf("  %s-skewed n=3000: all agree, len=3000 -> %v\n", dir, ok)
	}

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
