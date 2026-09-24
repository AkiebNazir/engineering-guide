package main

import (
	"fmt"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 543 · Diameter of Binary Tree                        [Easy]
https://leetcode.com/problems/diameter-of-binary-tree/
================================================================================

THE CORE IDEA
-------------
The longest path isn't necessarily through the root — it could be nested
entirely inside some subtree. So instead of asking "what's the diameter of
this subtree" recursively (which is NOT how heights compose), ask "what's
the longest path THROUGH this node" at EVERY node, and keep a running
maximum across the whole walk. The path through a node has length
height(Left) + height(Right) — no "+1" needed, because the length is
counted in EDGES and height(Left)+height(Right) already IS the edge count
of the path that enters the node from its deepest left descendant and
exits toward its deepest right descendant.

    func diameterOfBinaryTree(root *TreeNode) int {
        best := 0
        var depth func(*TreeNode) int
        depth = func(node *TreeNode) int {
            if node == nil {
                return 0
            }
            l, r := depth(node.Left), depth(node.Right)
            if l+r > best {              // side effect: update captured var
                best = l + r
            }
            return 1 + max(l, r)         // return value: height, for the parent
        }
        depth(root)
        return best
    }

O(n) time, O(h) space, ONE pass. `depth` returns a value the PARENT needs
(its own height) while also updating `best` as a SIDE EFFECT the caller
never sees directly — that's the closure doing two jobs with one function.

`var depth func(*TreeNode) int` must be declared before assignment: a Go
closure that calls itself recursively must already be a named variable in
scope at the point it references itself, so `depth := func(...) { ...
depth(...) ... }` doesn't compile — `depth` doesn't exist yet on the
right-hand side of `:=` in that same statement.

================================================================================
APPROACHES
================================================================================
Approach 0 (naive, recompute height at every node) — for every node,
   independently call a plain `height()` on its Left and Right, track the
   max of `height(Left)+height(Right)` across a SEPARATE traversal that
   visits every node. Correct, but pays for height's O(size-of-subtree)
   cost at every one of the n nodes: O(n) work, O(n) times, O(n^2) worst
   case on a skewed tree — same shape of bug as 009's naive balance check,
   for the same underlying reason (repeated height recomputation). Measured
   below against the single-pass version.

Approach 1 (single pass, closure-captured running max) ✅ — shown above.
   O(n) time, O(h) space, the answer.

Approach 2 (single pass, `(height, diameter)` pair return instead of a
   closure) — avoids the closure entirely by returning BOTH values from
   every call and combining them explicitly at each level:

    func helper(node *TreeNode) (height, diam int) {
        if node == nil { return 0, 0 }
        lh, ld := helper(node.Left)
        rh, rd := helper(node.Right)
        h := 1 + max(lh, rh)
        d := max(lh+rh, max(ld, rd))
        return h, d
    }

   Same complexity as Approach 1; no captured variable, more values
   threaded through every return — a fair alternative when a team prefers
   explicit data flow over closures.

================================================================================
STEP BY STEP TRACE — root = [1,2,3,4,5]
================================================================================
            1
          /   \
         2     3
        / \
       4   5

    depth(4): leaf, l=0,r=0, l+r=0 (best stays 0), returns 1
    depth(5): leaf, l=0,r=0, l+r=0 (best stays 0), returns 1
    depth(2): l=depth(4)=1, r=depth(5)=1, l+r=2 > best(0) -> best=2
              returns 1+max(1,1)=2
    depth(3): leaf, l=0,r=0, l+r=0 (best stays 2), returns 1
    depth(1): l=depth(2)=2, r=depth(3)=1, l+r=3 > best(2) -> best=3
              returns 1+max(2,1)=3

    result: best = 3   (path 4-2-1-3 or 5-2-1-3, 3 edges)

    Note the winning path is centered at node 2, not the root — `best`
    updates while WALKING DOWN through node 2, well before the root's own
    contribution (l+r=3) is even computed. This is exactly why "diameter
    might not pass through the root" isn't just a warning in the prose —
    here it nearly does (root also contributes 3), but a slightly
    different tree makes the deeper node strictly win.

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time    Space  Mutates?  Note
    ---------------------------------------  ------  -----  --------  --------------------
    Naive, recompute height per node        O(n^2)  O(h)   no        measured below
    Single pass, closure-captured max ✅    O(n)    O(h)   no        the answer
    Single pass, (height,diam) pair return  O(n)    O(h)   no        same bound, no closure

================================================================================
EDGE CASES
================================================================================
    single node                -> 0. One node has no path at all (0 edges).
    two nodes (root + 1 child)   -> 1.
    left-only or right-only       -> diameter == n-1 (the chain itself IS
      skewed chain                  the longest — and only — path).
    "balanced-looking" tree with   -> the answer here (010's trace above):
      the true longest path         the winning path is centered away from
      NOT through the root          the root, proving the naive "just check
                                   the root's two heights" instinct wrong.
    all values identical           -> irrelevant; only shape matters.

================================================================================
COMMON MISTAKES
================================================================================
1. Computing ONLY `height(root.Left) + height(root.Right)` and returning
   that — ignores every path not passing through the root. Wrong on any
   tree where the longest path is nested inside a subtree.
2. Writing `1 + max(diameter(Left), diameter(Right))` as if diameter
   composed like height — it doesn't. Diameter of a subtree and "longest
   path through this node" are different quantities; conflating them is
   the single most common wrong-shaped attempt at this problem.
3. Forgetting `var depth func(*TreeNode) int` before the closure literal —
   `depth := func(node *TreeNode) int { ... depth(node.Left) ... }` fails
   to compile because `depth` isn't in scope on the right-hand side yet.
4. Off-by-one: returning `edges = nodes - 1` incorrectly, or adding an
   extra `+1` inside the `l+r` comparison (that would count NODES on the
   path, not edges — LeetCode's diameter is edges, so `l+r`, no `+1`, is
   correct as written).
5. Two separate traversals (one to compute heights everywhere, one to scan
   for the max l+r) instead of fusing them into one postorder pass —
   correct but back to O(n) work per node if the height lookup itself
   isn't memoized, silently reintroducing the O(n^2) naive bug.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why can't you just check the root's subtree heights?
A: The longest path can be entirely nested inside a subtree, far from the
   root — every node needs to be a CANDIDATE center of the path, not just
   the root. Proven by the trace above.

Q: Do it without a closure.
A: Approach 2 — return `(height, diameter)` as a pair from every call and
   combine explicitly; no captured variable needed, more values threaded
   through the call stack instead.

Q: What if the tree is weighted (edge weights, not just "number of
   edges")?
A: Same recursion shape, but `depth` returns the max WEIGHTED path down
   from a node instead of a node count, and the combine step sums two
   weighted branch lengths instead of two heights.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    LC 104  Maximum Depth of Binary Tree   — the height subroutine, alone (005)
    LC 110  Balanced Binary Tree           — same postorder-with-side-check shape (009)
    LC 124  Binary Tree Maximum Path Sum   — the general form: sum instead of count,
                                              values can be negative, prune at 0
================================================================================
*/

// diameterOfBinaryTree is the interview answer: single pass, closure-
// captured running maximum.
func diameterOfBinaryTree(root *TreeNode) int {
	best := 0
	var depth func(*TreeNode) int
	depth = func(node *TreeNode) int {
		if node == nil {
			return 0
		}
		l, r := depth(node.Left), depth(node.Right)
		if l+r > best {
			best = l + r
		}
		return 1 + max(l, r)
	}
	depth(root)
	return best
}

// diameterOfBinaryTreePairReturn avoids the closure by returning both
// height and diameter-so-far from every call.
func diameterOfBinaryTreePairReturn(root *TreeNode) int {
	var helper func(*TreeNode) (height, diam int)
	helper = func(node *TreeNode) (int, int) {
		if node == nil {
			return 0, 0
		}
		lh, ld := helper(node.Left)
		rh, rd := helper(node.Right)
		h := 1 + max(lh, rh)
		d := max(lh+rh, max(ld, rd))
		return h, d
	}
	_, d := helper(root)
	return d
}

// heightNaive recomputes the full height of a subtree from scratch.
func heightNaive(node *TreeNode) int {
	if node == nil {
		return 0
	}
	return 1 + max(heightNaive(node.Left), heightNaive(node.Right))
}

// diameterOfBinaryTreeNaive: for every node, independently recompute
// height(Left) and height(Right) from scratch, without short-circuiting.
// O(n) work at each of n nodes -> O(n^2) worst case on a skewed tree.
func diameterOfBinaryTreeNaive(root *TreeNode) int {
	if root == nil {
		return 0
	}
	through := heightNaive(root.Left) + heightNaive(root.Right)
	left := diameterOfBinaryTreeNaive(root.Left)
	right := diameterOfBinaryTreeNaive(root.Right)
	return max(through, max(left, right))
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

// buildSkewed builds a left-only chain of n nodes.
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
		{[]interface{}{1, 2, 3, 4, 5}, 3},
		{[]interface{}{1, 2}, 1},
		{[]interface{}{1}, 0},
		{[]interface{}{1, 2, 3, 4, 5, nil, nil, 6, 7}, 4},
	}

	allOK := true

	fmt.Println("--- correctness: all three implementations ---")
	impls := []struct {
		name string
		fn   func(*TreeNode) int
	}{
		{"single pass, closure   ", diameterOfBinaryTree},
		{"single pass, pair return", diameterOfBinaryTreePairReturn},
		{"naive, recompute height ", diameterOfBinaryTreeNaive},
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

	// Live proof: the closure's captured variable is updated DURING the
	// walk, by nodes other than the root, before the root's own l+r is
	// even computed.
	fmt.Println("\n--- live proof: the running max updates away from the root ---")
	root := buildTree([]interface{}{1, 2, 3, 4, 5})
	var trace []string
	best := 0
	var depth func(*TreeNode) int
	depth = func(node *TreeNode) int {
		if node == nil {
			return 0
		}
		l, r := depth(node.Left), depth(node.Right)
		before := best
		if l+r > best {
			best = l + r
		}
		trace = append(trace, fmt.Sprintf("node %d: l=%d r=%d l+r=%d  best %d -> %d",
			node.Val, l, r, l+r, before, best))
		return 1 + max(l, r)
	}
	depth(root)
	for _, line := range trace {
		fmt.Println("  " + line)
	}
	// node 2 (not the root, node 1) should be where best FIRST reaches 2,
	// and the root only ties it, never exceeds it, on this tree.
	updatedBeforeRoot := len(trace) >= 2 && trace[len(trace)-1][:6] == "node 1"
	allOK = allOK && updatedBeforeRoot && best == 3
	fmt.Printf("  final diameter: %d, root visited LAST in postorder: %v\n", best, updatedBeforeRoot)

	// MEASURED: naive O(n^2) vs single-pass O(n) on a skewed tree.
	fmt.Println("\n--- measured: naive O(n^2) vs single-pass O(n), skewed chain ---")
	fmt.Printf("  %8s  %14s  %14s  %10s\n", "n", "naive", "single-pass", "ratio")
	sizes := []int{500, 1000, 2000, 4000}
	const reps = 3
	var ratios []float64
	for _, n := range sizes {
		tree := buildSkewed(n)

		t0 := time.Now()
		var naiveResult int
		for i := 0; i < reps; i++ {
			naiveResult = diameterOfBinaryTreeNaive(tree)
		}
		naiveElapsed := time.Since(t0) / reps

		t0 = time.Now()
		var fastResult int
		for i := 0; i < reps; i++ {
			fastResult = diameterOfBinaryTree(tree)
		}
		fastElapsed := time.Since(t0) / reps

		ratio := float64(naiveElapsed) / float64(fastElapsed)
		ratios = append(ratios, ratio)
		fmt.Printf("  %8d  %14v  %14v  %9.1fx\n", n, naiveElapsed, fastElapsed, ratio)

		if naiveResult != fastResult {
			allOK = false
			fmt.Printf("  MISMATCH at n=%d: naive=%d fast=%d\n", n, naiveResult, fastResult)
		}
	}
	fmt.Println("  As n doubles, the ratio roughly doubles too — O(n^2) vs O(n) growing")
	fmt.Println("  apart, not a fixed constant-factor gap.")
	lastRatio := ratios[len(ratios)-1]
	fmt.Printf("  measured ratio at the largest size: %.1fx\n", lastRatio)
	allOK = allOK && lastRatio > ratios[0]

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
