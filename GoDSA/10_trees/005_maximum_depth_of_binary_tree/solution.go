package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 104 · Maximum Depth of Binary Tree                   [Easy]
https://leetcode.com/problems/maximum-depth-of-binary-tree/
================================================================================

THE CORE IDEA
-------------
A node's depth is 1 + the deeper of its two children's depths. An empty
subtree has depth 0 — that's the base case that makes the recurrence work
for leaves too (1 + max(0, 0) = 1).

    func maxDepth(root *TreeNode) int {
        if root == nil {
            return 0
        }
        return 1 + max(maxDepth(root.Left), maxDepth(root.Right))
    }

O(n) time (every node visited once), O(h) space (the call stack, h =
height). This IS postorder (003): both children's answers are needed
before the parent's, so the combine step happens after both recursive
calls return.

================================================================================
APPROACHES
================================================================================
Approach 1 (recursion, postorder) ✅ — shown above. Three lines. This is
   the answer to lead with.

Approach 2 (iterative BFS, count levels) ✅ — a fundamentally different
   space profile:

    depth := 0
    queue := []*TreeNode{root}
    for len(queue) > 0 {
        depth++
        levelSize := len(queue)
        for i := 0; i < levelSize; i++ {
            node := queue[0]
            queue = queue[1:]
            if node.Left != nil  { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
    }
    return depth

   O(n) time, O(w) space (w = widest level, up to ~n/2 on a complete tree)
   — recursion's O(h) can be MUCH smaller than this on a wide, shallow tree,
   and MUCH larger on a narrow, deep one. Neither approach is "iterative,
   therefore cheaper" — the shape of the tree decides.

Approach 3 (iterative DFS, explicit stack of (node, depth) pairs) — avoids
   the call stack entirely while keeping O(h) space, at the cost of
   threading a depth value alongside every stack entry instead of getting
   it for free from the call stack's own depth.

================================================================================
STEP BY STEP TRACE — root = [3,9,20,null,null,15,7]
================================================================================
            3
          /   \
         9     20
              /  \
             15   7

    maxDepth(3)
      maxDepth(9)
        maxDepth(nil) -> 0,  maxDepth(nil) -> 0
        -> 1 + max(0,0) = 1
      maxDepth(20)
        maxDepth(15) -> 1 + max(0,0) = 1
        maxDepth(7)  -> 1 + max(0,0) = 1
        -> 1 + max(1,1) = 2
      -> 1 + max(1, 2) = 3

    result: 3   (path 3 -> 20 -> 15, or 3 -> 20 -> 7)

    BFS level-count trace, same tree:
    level 1: [3]              depth=1
    level 2: [9, 20]          depth=2
    level 3: [15, 7]          depth=3
    queue empty -> return 3

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time  Space   Mutates input?  Note
    ---------------------------- ----  ------  ---------------  --------------------
    Recursion, postorder ✅     O(n)  O(h)    no                simplest, the answer
    Iterative BFS, count levels O(n)  O(w)    no                O(w) can exceed O(h)
    Iterative DFS, explicit stack O(n) O(h)   no                no call-stack risk

================================================================================
EDGE CASES
================================================================================
    root == nil            -> 0, not 1. The empty tree has no nodes, and the
                               base case must return 0, not panic on root.Val.
    single node              -> 1.
    left-only skewed chain    -> depth == n; recursion goes n frames deep,
                               same as BFS's queue never holding more than 1
                               node at a time (w=1, h=n — opposite extremes).
    complete/perfect tree     -> depth == log2(n+1); BFS's widest level holds
                               ~n/2 nodes (w >> h here — the opposite case).
    all values identical       -> irrelevant; only shape matters.

================================================================================
COMMON MISTAKES
================================================================================
1. Returning 1 instead of 0 for `root == nil` — off-by-one that breaks every
   answer by exactly 1 (fencepost error at the recursion's floor).
2. Computing `max(depth(Left), depth(Right))` WITHOUT the `+1` — reports the
   depth of the deeper child, not of the node itself.
3. Confusing "depth" (root to farthest leaf) with "the number of EDGES on
   that path" — LeetCode counts NODES, so a single node has depth 1, not 0.
   Some other conventions (and some interviewers) mean edges; clarify which
   one is wanted before coding.
4. For the BFS version: forgetting to snapshot `levelSize := len(queue)`
   before the inner loop, so newly-appended children get counted as part of
   the CURRENT level instead of the next one, corrupting the level count.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Do it iteratively.
A: Approach 2 (BFS, count levels) is the natural iterative match for "depth"
   since depth IS "how many levels." Approach 3 (DFS stack) also works and
   keeps the O(h) space bound.

Q: Which has less memory overhead, BFS or DFS, for THIS specific tree?
A: Depends on shape: BFS is O(w), DFS/recursion is O(h). A wide, shallow
   tree favors DFS; a narrow, deep one favors BFS. Say both bounds and which
   wins on the tree at hand rather than picking one universally.

Q: What if the tree is so deep the recursion is a concern?
A: Approach 3 — iterative DFS with an explicit stack sidesteps the call
   stack (and Go's lack of tail-call optimization) entirely; it's the
   version to reach for on an adversarially deep, skewed input.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    LC 111  Minimum Depth of Binary Tree     — the trickier twin (006)
    LC 543  Diameter of Binary Tree          — height combined across ALL nodes (010)
    LC 110  Balanced Binary Tree             — height check fused with balance (009)
    LC 559  Maximum Depth of N-ary Tree      — same recurrence, variable fan-out
================================================================================
*/

// maxDepth is the interview answer: postorder recursion.
func maxDepth(root *TreeNode) int {
	if root == nil {
		return 0
	}
	return 1 + max(maxDepth(root.Left), maxDepth(root.Right))
}

// maxDepthBFS counts levels with a slice-as-queue. O(n) time, O(w) space.
func maxDepthBFS(root *TreeNode) int {
	if root == nil {
		return 0
	}
	depth := 0
	queue := []*TreeNode{root}
	for len(queue) > 0 {
		depth++
		levelSize := len(queue)
		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]
			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
	}
	return depth
}

// maxDepthDFSStack: iterative DFS, (node, depth) pairs. O(n) time, O(h) space.
func maxDepthDFSStack(root *TreeNode) int {
	if root == nil {
		return 0
	}
	type frame struct {
		node  *TreeNode
		depth int
	}
	best := 0
	stack := []frame{{root, 1}}
	for len(stack) > 0 {
		f := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if f.depth > best {
			best = f.depth
		}
		if f.node.Left != nil {
			stack = append(stack, frame{f.node.Left, f.depth + 1})
		}
		if f.node.Right != nil {
			stack = append(stack, frame{f.node.Right, f.depth + 1})
		}
	}
	return best
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

// buildComplete builds a complete tree of n nodes via the array-heap
// child-index formula (2i+1, 2i+2), so its width is ~n/2 and height ~log n.
func buildComplete(n int) *TreeNode {
	if n == 0 {
		return nil
	}
	nodes := make([]*TreeNode, n)
	for i := range nodes {
		nodes[i] = &TreeNode{Val: i}
	}
	for i := 0; i < n; i++ {
		if 2*i+1 < n {
			nodes[i].Left = nodes[2*i+1]
		}
		if 2*i+2 < n {
			nodes[i].Right = nodes[2*i+2]
		}
	}
	return nodes[0]
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
		want   int
	}
	cases := []testCase{
		{[]interface{}{3, 9, 20, nil, nil, 15, 7}, 3},
		{[]interface{}{1, nil, 2}, 2},
		{[]interface{}{}, 0},
		{[]interface{}{1}, 1},
	}

	allOK := true

	fmt.Println("--- correctness: recursion, BFS, DFS-stack ---")
	impls := []struct {
		name string
		fn   func(*TreeNode) int
	}{
		{"recursion  ", maxDepth},
		{"BFS levels ", maxDepthBFS},
		{"DFS stack  ", maxDepthDFSStack},
	}
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			got := impl.fn(buildTree(tc.values))
			if got != tc.want {
				ok = false
				fmt.Printf("  MISMATCH %s: %v -> %d (want %d)\n", impl.name, tc.values, got, tc.want)
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases)\n", status(ok), impl.name, len(cases))
	}

	// O(h) vs O(w): measure PEAK worklist size on two very differently
	// shaped trees of the same node count.
	fmt.Println("\n--- measured: recursion depth (O(h)) vs BFS peak queue (O(w)) ---")
	n := 8191 // 2^13 - 1: a perfect complete tree
	complete := buildComplete(n)
	skewed := buildSkewed(n)

	peakQueue := func(root *TreeNode) int {
		peak := 0
		queue := []*TreeNode{root}
		for len(queue) > 0 {
			if len(queue) > peak {
				peak = len(queue)
			}
			node := queue[0]
			queue = queue[1:]
			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
		return peak
	}

	completeDepth := maxDepth(complete)
	completePeakW := peakQueue(complete)
	skewedDepth := maxDepth(skewed)
	skewedPeakW := peakQueue(skewed)

	fmt.Printf("  n=%d, COMPLETE tree : height h=%d,  BFS peak width w=%d  (w >> h)\n",
		n, completeDepth, completePeakW)
	fmt.Printf("  n=%d, SKEWED   tree : height h=%d,  BFS peak width w=%d  (h >> w)\n",
		n, skewedDepth, skewedPeakW)
	fmt.Println("  Neither DFS nor BFS is universally cheaper — the tree's shape decides")
	fmt.Println("  which bound, O(h) or O(w), is the smaller one.")
	shapeOK := completePeakW > completeDepth && skewedDepth > skewedPeakW
	allOK = allOK && shapeOK

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
