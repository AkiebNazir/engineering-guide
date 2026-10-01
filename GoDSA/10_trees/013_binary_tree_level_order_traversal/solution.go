package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 102 · Binary Tree Level Order Traversal             [Medium]
https://leetcode.com/problems/binary-tree-level-order-traversal/
================================================================================

THE CORE IDEA
--------------
BFS with an explicit slice-as-queue, where `levelSize := len(queue)` snapshot
BEFORE the inner loop is what separates levels — without it, a level's
freshly-enqueued children get consumed in the SAME pass as their parents and
the level boundaries disappear entirely.

    queue := []*TreeNode{root}
    for len(queue) > 0 {
        levelSize := len(queue)              // <- the whole trick
        level := make([]int, 0, levelSize)
        for i := 0; i < levelSize; i++ {
            node := queue[0]
            queue = queue[1:]
            level = append(level, node.Val)
            if node.Left  != nil { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
        result = append(result, level)
    }

This is topic 7's queue pattern (FIFO) applied to a tree instead of a linear
structure — "process everything currently in the queue, but not anything
added during this pass" is the general level-by-level BFS idiom, useful
whenever you need to know where one "wave" ends and the next begins (shortest
path in an unweighted graph, multi-source flood fill, etc.).


================================================================================
APPROACH 1 · DFS with an explicit depth parameter
================================================================================
Recursive preorder, but instead of a queue, thread the current depth down and
append into result[depth], growing result as needed:

    func dfs(node *TreeNode, depth int) {
        if node == nil { return }
        if depth == len(result) { result = append(result, nil) }
        result[depth] = append(result[depth], node.Val)
        dfs(node.Left, depth+1)
        dfs(node.Right, depth+1)
    }

Produces IDENTICAL output to BFS (proven live below) because appending
left-then-right at each depth preserves left-to-right order within a level
even though the traversal itself is depth-first, not breadth-first.

    Time:  O(n)     Space: O(h) call stack + O(n) result

This is the one case where DFS space (O(h)) genuinely BEATS BFS space (O(w))
for the auxiliary structure — see the complexity table below and the topic
guide §2.3's "BFS space is O(width), can exceed O(height)" warning.


================================================================================
APPROACH 2 · BFS with a slice-as-queue ✅ (the standard answer)
================================================================================
Shown above. Space is O(w), width-bound — worse than DFS's O(h) for a wide,
shallow tree, but this is still the version interviewers expect first because
it makes "which level am I on" explicit and trivially extends to per-level
work (right-side view, zigzag order, level averages).


================================================================================
STEP BY STEP · root = [3,9,20,null,null,15,7]
================================================================================
              3
            ┌─┴─┐
            9   20
               ┌─┴─┐
              15    7

    queue = [3]
    --- pass 1: levelSize = 1 ---
        pop 3, level=[3], enqueue 9, enqueue 20 -> queue=[9,20]
        result = [[3]]
    --- pass 2: levelSize = 2 (snapshot BEFORE this pass's enqueues) ---
        pop 9,  level=[9],    9 has no children
        pop 20, level=[9,20], enqueue 15, enqueue 7 -> queue=[15,7]
        result = [[3],[9,20]]
    --- pass 3: levelSize = 2 ---
        pop 15, level=[15]
        pop 7,  level=[15,7]
        result = [[3],[9,20],[15,7]]
    queue empty -> done

    This EXACT trace is reproduced with real printed output in main() below,
    including the queue's length at the top of each pass, proving the
    snapshot is what keeps 15 and 7 out of the [9,20] level.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time    Space    Mutates input?
    -----------------------  ------  -------  ---------------
    DFS + depth parameter    O(n)    O(h)*    No
    BFS slice-as-queue   ✅  O(n)    O(w)     No

    * plus O(n) for the result itself either way; the O(h) vs O(w) split is
      about the AUXILIARY structure (call stack vs queue), which is the
      thing that actually differs between the two approaches.


================================================================================
EDGE CASES
================================================================================
    nil root                -> nil / [] (no levels at all, not [[]]).
    single node [1]         -> [[1]].
    left-skewed chain       -> each level has exactly 1 node; w=1, so BFS
                                and DFS use the same O(h)==O(w) space here —
                                the divergence only shows up on WIDE trees.
    a "wide" perfect tree of depth 4 (15 nodes) -> last level alone holds 8
                                nodes; proven live below that BFS's queue
                                peaks at that width, not at the tree's depth.
    negative and duplicate values -> level order doesn't care about value
                                identity at all, only structural position.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to snapshot `levelSize` before the inner loop and instead
   writing `for i := 0; i < len(queue); i++` directly — `len(queue)` changes
   as children get appended mid-loop, silently merging levels.

2. Enqueuing nil children — every `queue = append(queue, node.Left)` needs
   its own `if node.Left != nil` guard, or the queue fills with nil pointers
   that panic on `.Val` access.

3. Returning `[][]int{{}}` for a nil root instead of nil/empty — LC expects
   no levels, not one empty level.

4. Slicing `queue[1:]` and assuming it's O(n) like a Python list pop(0) —
   it's O(1) in Go (a slice header move), which is exactly why the
   slice-as-queue is idiomatic here without reaching for container/list.


================================================================================
FOLLOW-UPS
================================================================================
    - Zigzag level order (LC 103): alternate left-to-right / right-to-left
      per level — same BFS skeleton, reverse alternating levels.
    - Average of each level (LC 637): sum during the inner loop, divide by
      levelSize.
    - Right side view (problem 014 in this topic): keep only the LAST value
      popped per level.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 103  Binary Tree Zigzag Level Order Traversal
    LC 107  Binary Tree Level Order Traversal II (bottom-up)
    LC 199  Binary Tree Right Side View (problem 014, this topic)
    LC 637  Average of Levels in Binary Tree
================================================================================
*/

// levelOrder is the interview answer: BFS with a slice-as-queue, levelSize
// snapshotted before each pass.
func levelOrder(root *TreeNode) [][]int {
	if root == nil {
		return nil
	}
	var result [][]int
	queue := []*TreeNode{root}
	for len(queue) > 0 {
		levelSize := len(queue)
		level := make([]int, 0, levelSize)
		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]
			level = append(level, node.Val)
			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
		result = append(result, level)
	}
	return result
}

// levelOrderDFS reaches the identical result via depth-first recursion with
// an explicit depth parameter, trading O(w) queue space for O(h) stack space.
func levelOrderDFS(root *TreeNode) [][]int {
	var result [][]int
	var dfs func(node *TreeNode, depth int)
	dfs = func(node *TreeNode, depth int) {
		if node == nil {
			return
		}
		if depth == len(result) {
			result = append(result, nil)
		}
		result[depth] = append(result[depth], node.Val)
		dfs(node.Left, depth+1)
		dfs(node.Right, depth+1)
	}
	dfs(root, 0)
	return result
}

// levelOrderTraced is levelOrder instrumented to print the queue snapshot at
// the top of every pass -- proves the level-boundary trick live.
func levelOrderTraced(root *TreeNode) [][]int {
	if root == nil {
		return nil
	}
	var result [][]int
	queue := []*TreeNode{root}
	pass := 1
	for len(queue) > 0 {
		levelSize := len(queue)
		vals := make([]int, levelSize)
		for i, n := range queue {
			vals[i] = n.Val
		}
		fmt.Printf("    pass %d: queue snapshot at levelSize=%d -> %v\n", pass, levelSize, vals)
		level := make([]int, 0, levelSize)
		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]
			level = append(level, node.Val)
			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
		result = append(result, level)
		pass++
	}
	return result
}

func equal2D(a, b [][]int) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if len(a[i]) != len(b[i]) {
			return false
		}
		for j := range a[i] {
			if a[i][j] != b[i][j] {
				return false
			}
		}
	}
	return true
}

func main() {
	// [3,9,20,null,null,15,7]
	t1 := &TreeNode{
		Val:  3,
		Left: &TreeNode{Val: 9},
		Right: &TreeNode{
			Val:   20,
			Left:  &TreeNode{Val: 15},
			Right: &TreeNode{Val: 7},
		},
	}

	// Left-skewed chain: 1 -> 2 -> 3 -> 4, width 1 throughout.
	skewed := &TreeNode{Val: 1, Left: &TreeNode{Val: 2, Left: &TreeNode{Val: 3, Left: &TreeNode{Val: 4}}}}

	// Perfect tree of depth 4 (15 nodes): width peaks at 8 on the last level.
	var buildPerfect func(depth, val int) *TreeNode
	buildPerfect = func(depth, val int) *TreeNode {
		if depth == 0 {
			return nil
		}
		n := &TreeNode{Val: val}
		n.Left = buildPerfect(depth-1, val*2)
		n.Right = buildPerfect(depth-1, val*2+1)
		return n
	}
	wide := buildPerfect(4, 1)

	type testCase struct {
		name string
		root *TreeNode
		want [][]int
	}
	cases := []testCase{
		{"LC example 1", t1, [][]int{{3}, {9, 20}, {15, 7}}},
		{"single node [1]", &TreeNode{Val: 1}, [][]int{{1}}},
		{"nil root", nil, nil},
		{"left-skewed chain", skewed, [][]int{{1}, {2}, {3}, {4}}},
	}

	allOK := true
	for _, tc := range cases {
		gotBFS := levelOrder(tc.root)
		gotDFS := levelOrderDFS(tc.root)
		ok := equal2D(gotBFS, tc.want) && equal2D(gotDFS, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  %-24s BFS=%v  DFS=%v  want=%v\n", status(ok), tc.name, gotBFS, gotDFS, tc.want)
	}

	fmt.Println("\n--- live trace: queue snapshot proves level boundaries, [3,9,20,null,null,15,7] ---")
	traced := levelOrderTraced(t1)
	fmt.Printf("    final result: %v\n", traced)

	fmt.Println("\n--- BFS queue width vs DFS stack depth, perfect tree of depth 4 (15 nodes) ---")
	maxQueueWidth := 0
	{
		queue := []*TreeNode{wide}
		for len(queue) > 0 {
			if len(queue) > maxQueueWidth {
				maxQueueWidth = len(queue)
			}
			n := queue[0]
			queue = queue[1:]
			if n.Left != nil {
				queue = append(queue, n.Left)
			}
			if n.Right != nil {
				queue = append(queue, n.Right)
			}
		}
	}
	maxStackDepth := 0
	{
		var dfs func(*TreeNode, int)
		dfs = func(n *TreeNode, depth int) {
			if n == nil {
				return
			}
			if depth > maxStackDepth {
				maxStackDepth = depth
			}
			dfs(n.Left, depth+1)
			dfs(n.Right, depth+1)
		}
		dfs(wide, 1)
	}
	fmt.Printf("    tree has 15 nodes, height 4 -> BFS peak queue width = %d, DFS peak stack depth = %d\n",
		maxQueueWidth, maxStackDepth)
	fmt.Println("    width (8) exceeds height (4): BFS space is genuinely worse here, as the topic guide predicts")

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
