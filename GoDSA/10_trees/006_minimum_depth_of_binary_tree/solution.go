package main

import (
	"fmt"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 111 · Minimum Depth of Binary Tree                   [Easy]
https://leetcode.com/problems/minimum-depth-of-binary-tree/
================================================================================

THE CORE IDEA
-------------
"Nearest LEAF" is not "nearest node with a missing child." A node with
exactly one child is not a leaf — its minimum depth must be measured
through its ONE real child, never through the nil side. Naively mirroring
005's `1 + min(depth(Left), depth(Right))` is WRONG the moment a node is
one-sided, because the nil side contributes 0 and produces a false minimum
of 1.

    func minDepth(root *TreeNode) int {
        if root == nil {
            return 0
        }
        if root.Left == nil && root.Right != nil {
            return 1 + minDepth(root.Right)   // only real child counts
        }
        if root.Right == nil && root.Left != nil {
            return 1 + minDepth(root.Left)
        }
        // leaf (both nil) or two real children: min over what's real
        return 1 + min(minDepth(root.Left), minDepth(root.Right))
    }

O(n) time worst case, O(h) space. This is the trap problem of the
depth/height family — it reads like a five-minute rename of 005 and is
actually testing whether you notice the one-sided-node case.

================================================================================
APPROACHES
================================================================================
Approach 0 (WRONG, don't ship it): `1 + min(minDepth(Left), minDepth(Right))`
   with no case split. Fails on any one-sided chain — a completely
   right-skewed tree of n nodes reports minDepth == 1 instead of n, because
   every node's nil left child contributes a phantom 0. Demoed live below.

Approach 1 (recursion with the one-sided case split) ✅ — shown above.
   O(n) worst case (a skewed tree still visits every node), O(h) space.

Approach 2 (iterative BFS, return at first leaf) ✅ — BFS gets a genuine
   EARLY-EXIT advantage here that it doesn't get in 005 (which must visit
   every node regardless): the instant you pop a node with no children,
   its level number IS the answer.

    depth := 0
    queue := []*TreeNode{root}
    for len(queue) > 0 {
        depth++
        levelSize := len(queue)
        for i := 0; i < levelSize; i++ {
            node := queue[0]
            queue = queue[1:]
            if node.Left == nil && node.Right == nil {
                return depth              // first leaf found — done
            }
            if node.Left != nil  { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
    }

   Best case O(shallowest leaf's subtree) instead of O(n) — measured below
   on a tree where the shallow leaf sits far from most of the tree's mass.

================================================================================
STEP BY STEP TRACE — root = [2,null,3,null,4,null,5,null,6]  (a one-sided chain)
================================================================================
    2
     \
      3
       \
        4
         \
          5
           \
            6

    Every node has exactly one child until 6, the only leaf.
    minDepth(2): Left nil, Right=3 real -> 1 + minDepth(3)
    minDepth(3): Left nil, Right=4 real -> 1 + minDepth(4)
    minDepth(4): Left nil, Right=5 real -> 1 + minDepth(5)
    minDepth(5): Left nil, Right=6 real -> 1 + minDepth(6)
    minDepth(6): leaf (both nil)        -> 1 + min(0,0) = 1

    unwinding: 1 -> 2 -> 3 -> 4 -> 5

    result: 5   (there is only one path to any leaf: straight down)

    THE WRONG VERSION on the same tree:
    wrongMinDepth(2) = 1 + min(minDepth(nil)=0, minDepth(3)=...) = 1 + 0 = 1
    It reports 1 immediately because the nil LEFT child of every node looks
    like a zero-depth "leaf" to the naive recurrence — but nil is not a
    node, let alone the nearest one.

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time         Space  Mutates?  Note
    ---------------------------------  -----------  -----  --------  ------------------
    Naive min(Left,Right), no split   O(n)         O(h)   no        WRONG ANSWER
    Recursion, one-sided split ✅     O(n)         O(h)   no        the answer
    Iterative BFS, early exit ✅      O(shallowest  O(w)   no        can beat O(n) in
                                       leaf's subtree)               practice

================================================================================
EDGE CASES
================================================================================
    root == nil                -> 0. Empty tree, no leaves at all.
    single node                  -> 1 (it's a leaf: both children nil).
    completely one-sided chain    -> minDepth == n, NOT 1. THE test case for
                                   this problem — a right-only or left-only
                                   chain of n nodes has exactly one leaf, at
                                   the bottom.
    balanced tree, both subtrees   -> genuinely takes the shallower branch;
      have leaves                   this is the case where naive min(L,R)
                                   would have coincidentally worked, which
                                   is why it's easy to ship the bug undetected.
    shallow leaf far from most      -> the case where BFS early-exit wins
      of the tree's mass             big; measured below.

================================================================================
COMMON MISTAKES
================================================================================
1. THE bug: `1 + min(minDepth(Left), minDepth(Right))` with no check for a
   nil child. Reports 1 on any one-sided node's subtree, because the empty
   side's depth-0 base case gets treated as a valid leaf. Demoed live below
   on a tree where the bug returns 1 while the true answer is 5.
2. Treating "leaf" as "node whose depth() would be 1" without checking that
   BOTH children are actually nil.
3. For the BFS version: returning as soon as `node.Left == nil` (checking
   only one side) instead of `node.Left == nil && node.Right == nil` —
   stops at a one-sided node, not a true leaf.
4. Off-by-one on the base case: `root == nil` must return 0 (no nodes), not
   1 — the same fencepost issue as 005, mirrored here.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why doesn't `min` work the way `max` did in 005?
A: Because `max` never needs to distinguish "no subtree here" from "a real
   but short subtree" — the empty side just loses the max comparison
   harmlessly. `min` actively PREFERS the empty side's phantom 0, which is
   wrong the moment "leaf" means something more specific than "recursion
   bottomed out."

Q: Can BFS beat O(n) here?
A: Yes in practice — it returns as soon as it discovers ANY leaf, so on a
   tree with a shallow leaf but many deep nodes elsewhere, BFS visits far
   fewer than n nodes. Worst case (the shallowest leaf is also the deepest
   node, e.g. a single skewed chain) it's still O(n). Measured below.

Q: What if "leaf" meant "node with at least one nil child" instead of
   LeetCode's "both nil"?
A: Then the naive `min(Left, Right)` recurrence (Approach 0) would be
   CORRECT — this problem's difficulty is entirely a consequence of
   LeetCode's specific leaf definition. Worth stating explicitly: the bug
   is not a coding error in isolation, it's a mismatch between the
   recurrence and the definition.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    LC 104  Maximum Depth of Binary Tree   — the "easier" twin (005), no one-
                                              sided trap because max is safe
    LC 112  Path Sum                       — same one-sided-node trap, for a
                                              root-to-leaf SUM instead of depth
    LC 543  Diameter of Binary Tree        — height combined across all nodes (010)
================================================================================
*/

// minDepth is the interview answer: recursion with the one-sided case split.
func minDepth(root *TreeNode) int {
	if root == nil {
		return 0
	}
	if root.Left == nil && root.Right != nil {
		return 1 + minDepth(root.Right) // only real child counts
	}
	if root.Right == nil && root.Left != nil {
		return 1 + minDepth(root.Left)
	}
	// leaf (both nil) or two real children
	return 1 + min(minDepth(root.Left), minDepth(root.Right))
}

// minDepthWrong is the naive, BROKEN version kept for the demo: it treats a
// nil child's depth-0 base case as if it were a valid leaf.
func minDepthWrong(root *TreeNode) int {
	if root == nil {
		return 0
	}
	return 1 + min(minDepthWrong(root.Left), minDepthWrong(root.Right))
}

// minDepthBFS returns as soon as the first (shallowest) leaf is found.
func minDepthBFS(root *TreeNode) int {
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
			if node.Left == nil && node.Right == nil {
				return depth // first true leaf — done
			}
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

// buildOneSidedChain builds n nodes all chained through Right (no leaves
// until the very last node).
func buildOneSidedChain(n int) *TreeNode {
	if n == 0 {
		return nil
	}
	root := &TreeNode{Val: 0}
	curr := root
	for i := 1; i < n; i++ {
		node := &TreeNode{Val: i}
		curr.Right = node
		curr = node
	}
	return root
}

// buildShallowLeafDeepMass builds a tree with one very shallow leaf hanging
// off the root's left, and a large deep right subtree with no leaf until
// the bottom — so BFS can find the answer without touching most of the tree.
func buildShallowLeafDeepMass(deepChainLen int) *TreeNode {
	root := &TreeNode{Val: -1}
	root.Left = &TreeNode{Val: -2} // shallow leaf at depth 2
	root.Right = buildOneSidedChain(deepChainLen)
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
		want   int
	}
	cases := []testCase{
		{[]interface{}{3, 9, 20, nil, nil, 15, 7}, 2},
		{[]interface{}{2, nil, 3, nil, nil}, 2},
		{[]interface{}{}, 0},
		{[]interface{}{1}, 1},
		{[]interface{}{1, 2}, 2}, // one-sided: 1 has only left child 2
	}

	allOK := true

	fmt.Println("--- correctness: recursion and BFS ---")
	impls := []struct {
		name string
		fn   func(*TreeNode) int
	}{
		{"recursion (split)", minDepth},
		{"BFS early-exit   ", minDepthBFS},
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

	// The core bug, proven on a one-sided chain: naive min gives 1, truth is n.
	fmt.Println("\n--- the naive-min bug, proven on a one-sided chain of 9 nodes ---")
	chain := buildOneSidedChain(9)
	wrong := minDepthWrong(chain)
	correct := minDepth(chain)
	fmt.Printf("  chain of 9 nodes, all chained through .Right, ONE leaf at the bottom\n")
	fmt.Printf("  minDepthWrong (naive min)   -> %d   <- WRONG, treats the nil left child as a leaf\n", wrong)
	fmt.Printf("  minDepth (one-sided split)  -> %d   <- correct: the only leaf is 9 nodes down\n", correct)
	bugProven := wrong == 1 && correct == 9
	allOK = allOK && bugProven
	fmt.Printf("  bug confirmed (naive==1, correct==9): %v\n", bugProven)

	// BFS early-exit: measured runtime advantage when the shallow leaf is
	// far from most of the tree's mass.
	fmt.Println("\n--- measured: BFS early-exit vs full recursion on a lopsided tree ---")
	deepLen := 2_000_000
	tree := buildShallowLeafDeepMass(deepLen)

	reps := 20
	t0 := time.Now()
	var recResult int
	for i := 0; i < reps; i++ {
		recResult = minDepth(tree)
	}
	recElapsed := time.Since(t0) / time.Duration(reps)

	t0 = time.Now()
	var bfsResult int
	for i := 0; i < reps; i++ {
		bfsResult = minDepthBFS(tree)
	}
	bfsElapsed := time.Since(t0) / time.Duration(reps)

	fmt.Printf("  tree: root with a leaf at depth 2 on the left, a %d-node deep chain on the right\n", deepLen)
	fmt.Printf("  recursion  -> %d   avg time %v  (must still visit the whole right chain)\n", recResult, recElapsed)
	fmt.Printf("  BFS        -> %d   avg time %v  (stops at the shallow leaf on level 2)\n", bfsResult, bfsElapsed)
	if bfsElapsed > 0 {
		fmt.Printf("  recursion / BFS = %.0fx slower for the full-tree walk\n",
			float64(recElapsed)/float64(bfsElapsed))
	}
	resultsMatch := recResult == bfsResult && recResult == 2
	allOK = allOK && resultsMatch
	fmt.Printf("  both report the same minimum depth: %v\n", resultsMatch)

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
