package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 199 · Binary Tree Right Side View                  [Medium]
https://leetcode.com/problems/binary-tree-right-side-view/
================================================================================

THE CORE IDEA
--------------
"What you'd see standing on the right" is "the rightmost node at each depth."
Two independent ways to compute that:

    BFS: walk level by level (problem 013's skeleton), keep the LAST value
         popped in each level's inner loop.

    DFS: visit RIGHT before LEFT, and record a node's value the FIRST time
         its depth is reached. Because right is visited first, the first
         node ever seen at a given depth is guaranteed to be the rightmost
         one — everything reached at that same depth afterward arrived via
         a left branch and must be skipped.

    func dfs(node *TreeNode, depth int) {
        if node == nil { return }
        if depth == len(result) {          // first time at this depth
            result = append(result, node.Val)
        }
        dfs(node.Right, depth+1)            // RIGHT FIRST
        dfs(node.Left, depth+1)
    }


================================================================================
APPROACH 1 · BFS, keep the last value per level ✅
================================================================================
    queue := []*TreeNode{root}
    for len(queue) > 0 {
        levelSize := len(queue)
        var last int
        for i := 0; i < levelSize; i++ {
            node := queue[0]
            queue = queue[1:]
            last = node.Val
            if node.Left  != nil { queue = append(queue, node.Left) }
            if node.Right != nil { queue = append(queue, node.Right) }
        }
        result = append(result, last)
    }

    Time: O(n)   Space: O(w) — same queue-width bound as problem 013.


================================================================================
APPROACH 2 · DFS, right-before-left, first-seen-per-depth ✅
================================================================================
Shown above. Time O(n), Space O(h) — the call stack, not a queue. This is
the approach where DFS wins the space comparison outright (unlike problem
013, where DFS matched BFS's answer but the two differ on which one is
"cheaper" only by tree shape) — here DFS is O(h) unconditionally, vs BFS's
O(w), and a right-side-view query is naturally phrased depth-first.


================================================================================
STEP BY STEP · root = [1,2,3,null,5,null,4]
================================================================================
              1
            ┌─┴─┐
            2   3
             ┴─┐  ┴─┐
               5     4

    BFS:
      level 0: pop 1              -> last=1   result=[1]
      level 1: pop 2, pop 3        -> last=3   result=[1,3]
      level 2: pop 5, pop 4        -> last=4   result=[1,3,4]
      -> [1,3,4]

    DFS (right first):
      dfs(1, depth=0): depth 0 unseen -> record 1.  result=[1]
        dfs(3, depth=1): depth 1 unseen -> record 3. result=[1,3]
          dfs(4, depth=2): depth 2 unseen -> record 4. result=[1,3,4]
          dfs(nil, depth=2): stop
        dfs(2, depth=1): depth 1 ALREADY SEEN -> skip recording
          dfs(nil, depth=2): stop (2's right is nil)
          dfs(5, depth=2): depth 2 ALREADY SEEN (recorded via 4) -> skip
      -> [1,3,4]

    Same answer, opposite traversal order — proven identical live below,
    including a version instrumented to print exactly which calls RECORD
    vs which ones SKIP.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time    Space   Mutates input?
    ---------------------------  ------  ------  ---------------
    BFS, last value per level✅  O(n)    O(w)    No
    DFS, right-first, first-seen✅ O(n)  O(h)    No


================================================================================
EDGE CASES
================================================================================
    nil root                -> nil (no view).
    single node [1]         -> [1].
    only-left-children chain (e.g. 1->2->3, all Left) -> [1,2,3]; every
                                level has exactly one node, so it IS the
                                right side view even though every edge goes
                                left — "rightmost at each depth" degenerates
                                to "the only node at each depth."
    a node visible only because a DEEPER sibling subtree is shallower, e.g.
                                LC example 1's node 5 (2's left-side descendant
                                at depth 2) is correctly EXCLUDED because 3's
                                subtree (4, also at depth 2) is visited first
                                under right-first DFS — exactly the scenario a
                                naive "walk root.Right chain" approach gets
                                wrong, since 5 is not reachable via any
                                all-right path from the root at all.
    duplicate values across levels -> view returns VALUES, not identities;
                                duplicates are simply repeated in the output
                                if that's what's genuinely visible.


================================================================================
COMMON MISTAKES
================================================================================
1. Assuming "right side view" means "walk root.Right.Right.Right..." — wrong
   whenever a left subtree is deeper than the right subtree at some level;
   the true rightmost node at a given depth can live under a LEFT branch.

2. DFS visiting Left before Right, then "record only if depth is unseen" —
   silently returns the LEFTMOST node per depth instead of rightmost. The
   right-first traversal order is not optional, it's the entire trick.

3. BFS keeping the FIRST value of each level instead of the last — that
   would produce the LEFT side view (a valid, related, but different
   problem).

4. Off-by-one on the "depth == len(result)" first-seen check — using
   `depth >= len(result)` also works, but `>` alone is a bug (skips
   recording a deeper level that should append, since result never grows).


================================================================================
FOLLOW-UPS
================================================================================
    - Left side view: same two approaches, swap "last" for "first" in BFS,
      or swap traversal order to Left-before-Right in DFS.
    - Return the FULL level order and let the caller slice the last element
      of each row — valid but wastes memory building rows you only need the
      tail of; fine to mention as a "correct but not optimal" alternative.
    - Vertical order traversal (LC 987) generalizes "what column can you
      see" beyond just leftmost/rightmost.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 102  Binary Tree Level Order Traversal (problem 013, this topic)
    LC 103  Binary Tree Zigzag Level Order Traversal
    LC 987  Vertical Order Traversal of a Binary Tree
================================================================================
*/

// rightSideView is the interview answer: BFS keeping the last value per level.
func rightSideView(root *TreeNode) []int {
	if root == nil {
		return nil
	}
	var result []int
	queue := []*TreeNode{root}
	for len(queue) > 0 {
		levelSize := len(queue)
		var last int
		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]
			last = node.Val
			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
		result = append(result, last)
	}
	return result
}

// rightSideViewDFS reaches the same answer via right-first DFS, recording a
// value only the first time its depth is reached.
func rightSideViewDFS(root *TreeNode) []int {
	var result []int
	var dfs func(node *TreeNode, depth int)
	dfs = func(node *TreeNode, depth int) {
		if node == nil {
			return
		}
		if depth == len(result) {
			result = append(result, node.Val)
		}
		dfs(node.Right, depth+1) // right first: guarantees first-seen == rightmost
		dfs(node.Left, depth+1)
	}
	dfs(root, 0)
	return result
}

// rightSideViewDFSTraced is rightSideViewDFS instrumented to print every
// call's RECORD/skip decision, proving right-first traversal finds the
// rightmost node at each depth before any left-branch node at that depth.
func rightSideViewDFSTraced(root *TreeNode) []int {
	var result []int
	var dfs func(node *TreeNode, depth int)
	dfs = func(node *TreeNode, depth int) {
		if node == nil {
			return
		}
		if depth == len(result) {
			result = append(result, node.Val)
			fmt.Printf("    depth %d: visiting %d -> RECORD (first seen at this depth)\n", depth, node.Val)
		} else {
			fmt.Printf("    depth %d: visiting %d -> skip (depth already has %d)\n", depth, node.Val, result[depth])
		}
		dfs(node.Right, depth+1)
		dfs(node.Left, depth+1)
	}
	dfs(root, 0)
	return result
}

func equalInts(a, b []int) bool {
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

func main() {
	// [1,2,3,null,5,null,4]
	t1 := &TreeNode{
		Val:   1,
		Left:  &TreeNode{Val: 2, Right: &TreeNode{Val: 5}},
		Right: &TreeNode{Val: 3, Right: &TreeNode{Val: 4}},
	}

	// [1,null,3]
	t2 := &TreeNode{Val: 1, Right: &TreeNode{Val: 3}}

	// Left-only chain: 1 -> 2 -> 3, every level has exactly one node.
	leftChain := &TreeNode{Val: 1, Left: &TreeNode{Val: 2, Left: &TreeNode{Val: 3}}}

	type testCase struct {
		name string
		root *TreeNode
		want []int
	}
	cases := []testCase{
		{"LC example 1", t1, []int{1, 3, 4}},
		{"LC example 2", t2, []int{1, 3}},
		{"nil root", nil, nil},
		{"single node [1]", &TreeNode{Val: 1}, []int{1}},
		{"left-only chain", leftChain, []int{1, 2, 3}},
	}

	allOK := true
	for _, tc := range cases {
		gotBFS := rightSideView(tc.root)
		gotDFS := rightSideViewDFS(tc.root)
		ok := equalInts(gotBFS, tc.want) && equalInts(gotDFS, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  %-18s BFS=%v  DFS=%v  want=%v\n", status(ok), tc.name, gotBFS, gotDFS, tc.want)
	}

	fmt.Println("\n--- live trace: right-first DFS finds rightmost-per-depth, [1,2,3,null,5,null,4] ---")
	traced := rightSideViewDFSTraced(t1)
	fmt.Printf("    final result: %v\n", traced)
	fmt.Println("    note node 5 (2's right child, depth 2) is correctly SKIPPED: node 4 already claimed depth 2")

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
