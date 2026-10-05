package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 124 · Binary Tree Maximum Path Sum                   [Hard]
https://leetcode.com/problems/binary-tree-maximum-path-sum/
================================================================================

THE CORE IDEA
--------------
A legal path is a "V": it climbs from somewhere, TURNS AROUND at exactly one
node — its highest point — and descends. It cannot fork twice. So:

    every path has exactly ONE turning point
    => maximize over turning points
    => for each node, compute the best path that TURNS THERE, and take the
       max over all n nodes

At a node, that requires knowing the best straight-DOWN path sum from each
child. Which gives the recursion its shape — and its one genuinely hard
idea: the value you RECORD and the value you RETURN are two different
numbers.

    func gain(node *TreeNode) int {              // returns best DOWNWARD sum
        if node == nil { return 0 }
        left  := max(gain(node.Left),  0)          // a negative branch is DROPPED
        right := max(gain(node.Right), 0)
        best = max(best, node.Val+left+right)       // RECORD: path TURNING here
        return node.Val + max(left, right)           // RETURN: path CONTINUING up
    }
    best := math.MinInt
    gain(root)
    return best

    RECORDED (the "through" value): node.Val + left + right
        uses BOTH children — a complete V, a candidate for the final answer.
        It can NEVER be extended upward: a parent joining it would give the
        node three path-neighbours (parent, left child, right child), which
        is a fork, not a path.

    RETURNED (the "gain"): node.Val + max(left, right)
        uses AT MOST ONE child — a path with a loose end at `node`, exactly
        the thing the parent CAN attach to.


================================================================================
⚠️ THE GO-SPECIFIC WRINKLE — no tuple return, so "best" needs its own channel
================================================================================
gain() already has a return type (int, the value to hand the parent); the
running best needs a genuinely separate channel. Three idiomatic options,
all shown below:

    1. Closure over a captured variable (used in the answer):
           best := math.MinInt
           var gain func(*TreeNode) int
           gain = func(node *TreeNode) int { ...; best = max(best, ...); ... }
       Same mechanism as the topic guide §3.2 diameter pattern: `var gain
       func(...)` must be pre-declared before the assignment because a
       self-referencing closure literal needs its own name in scope already.

    2. A pointer to an int, threaded as an explicit parameter:
           func gain(node *TreeNode, best *int) int { ...; *best = max(*best, ...); ... }
       No closure needed, but every call site must remember to pass &best.

    3. A tiny struct field:
           type solver struct{ best int }
           func (s *solver) gain(node *TreeNode) int { ...; s.best = max(...); ... }
       Idiomatic when the recursion needs MULTIPLE pieces of running state,
       not just one — overkill for a single int, shown only for contrast.

Python would just close over `best` with `nonlocal` — Go's closures capture
variables by reference automatically (no `nonlocal` keyword needed), so the
mechanism is actually SIMPLER here than Python makes it look, once you
already know pre-declaration is required for the self-reference.


================================================================================
APPROACH 1 · Brute force — for every node, walk every downward path from it
================================================================================
For every node as a candidate turning point, separately compute (via its own
recursive walk) the best straight-down sum into each child, without caching
anything between different turning-point candidates.

    Time:  O(n^2) worst case (each of n nodes re-walks its own subtree)
    Space: O(h) per walk

The wasted work is recomputing "best downward sum from X" once per ancestor
that considers X as part of a candidate path, when it only needs computing
ONCE per node via a single postorder pass.


================================================================================
APPROACH 2 · Postorder gain + closure-captured running max ✅ (the answer)
================================================================================
Shown above. Single pass, O(n).


================================================================================
STEP BY STEP · root = [-10,9,20,null,null,15,7]  (best path skips the root)
================================================================================
                -10
              ┌──┴──┐
              9     20
                   ┌─┴─┐
                  15    7

    gain(9):   no children -> left=0, right=0.  best = max(best, 9+0+0)=9
               returns 9 + max(0,0) = 9

    gain(15):  no children -> best = max(9, 15+0+0) = 15
               returns 15

    gain(7):   no children -> best = max(15, 7+0+0) = 15   (7 alone doesn't beat 15)
               returns 7

    gain(20):  left=max(gain(15),0)=15, right=max(gain(7),0)=7
               best = max(15, 20+15+7) = max(15, 42) = 42        <- the winner
               returns 20 + max(15,7) = 35

    gain(-10): left=max(gain(9),0)=9, right=max(gain(20),0)=35
               best = max(42, -10+9+35) = max(42, 34) = 42       <- root does NOT improve it
               returns -10 + max(9,35) = 25   (irrelevant, nothing above -10)

    FINAL best = 42, achieved entirely inside node 20's subtree (15 -> 20 -> 7),
    never touching the root at all. Verified live below, including the
    intermediate best-so-far after each node the traversal visits.


================================================================================
⚠️ THE #1 FAILURE MODE: RETURNING THE "THROUGH" VALUE INSTEAD OF THE "GAIN"
================================================================================
Change one line — return `node.Val + left + right` instead of
`node.Val + max(left, right)` — and the function still compiles, still
returns *an* integer, and still passes some tests. What it computes stops
being a valid path sum, because it lets a parent "extend" a value that
already used both children, silently forking the path into a Y instead of a
V. Demonstrated live below on a small tree where the bug changes the answer
from the true best (11) to an inflated, invalid one.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time     Space   Mutates input?
    -------------------------------------  -------  ------  ---------------
    Brute force (re-walk per turning pt)   O(n^2)   O(h)    No
    Postorder gain + closure max       ✅  O(n)     O(h)    No


================================================================================
EDGE CASES
================================================================================
    single node [5]           -> 5 (a path of length 1 is legal and required
                                  by "non-empty path" — no edges needed).
    single node [-3]           -> -3; the answer can be negative if every
                                  node is negative — never clamp to 0.
    all values negative, e.g. [-2,-5,-3] -> the LEAST negative single node
                                  (-2, the root) alone, since combining any
                                  two negatives only makes the sum worse.
    best path skips the root entirely -> LC example 2, traced above.
    left-skewed chain with one very negative node partway down -> the
                                  negative node's branch gets dropped
                                  (clamped to 0) rather than dragging the
                                  running total down; proven live.


================================================================================
COMMON MISTAKES
================================================================================
1. Returning the "through" (both-children) value up to the parent instead
   of the "gain" (one-child) value — creates a Y-shaped fork, not a path.
   Demonstrated live: turns the answer for a small tree from 11 into 13.

2. Not clamping negative child gains to 0 before adding — a single very
   negative node deep in an otherwise-strong subtree can wrongly drag the
   whole candidate sum down instead of simply being excluded from the path.

3. Seeding the running best at 0 instead of negative infinity — silently
   wrong on an all-negative tree, since 0 is not achievable (the path must
   be non-empty and use real node values).

4. Assuming the answer always passes through the root — LC example 2 exists
   specifically to break that assumption; the recursion must consider every
   node as a candidate turning point, not just the root.


================================================================================
FOLLOW-UPS
================================================================================
    - Return the actual PATH (not just its sum) — track the argmax turning
      node alongside `best`, then reconstruct via the same left/right gain
      comparisons used to compute it.
    - What if edges (not just nodes) carried costs? Same recursion shape,
      fold the edge cost into `left`/`right` before comparing to 0.
    - Constrain the path to a maximum length k — turns this into a DP over
      (node, remaining length), no longer a pure postorder single pass.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 543  Diameter of Binary Tree — topic guide §3.2, identical closure
             pattern, "record vs return" split (edge COUNT instead of VALUE
             SUM, and no negative-clamping since counts can't be negative)
    LC 687  Longest Univalue Path    — same shape, constrained to same-value
             runs instead of arbitrary sums
    LC 968  Binary Tree Cameras      — another postorder-with-global-state
             problem, different aggregation rule
================================================================================
*/

func maxInt(a, b int) int {
	if a > b {
		return a
	}
	return b
}

// maxPathSum is the interview answer: postorder gain + closure-captured
// running best.
func maxPathSum(root *TreeNode) int {
	best := -1 << 62
	var gain func(*TreeNode) int
	gain = func(node *TreeNode) int {
		if node == nil {
			return 0
		}
		left := maxInt(gain(node.Left), 0)
		right := maxInt(gain(node.Right), 0)
		if through := node.Val + left + right; through > best {
			best = through
		}
		return node.Val + maxInt(left, right)
	}
	gain(root)
	return best
}

// maxPathSumTraced is maxPathSum instrumented to print the running best
// after every node is processed, proving live where the winning path forms.
func maxPathSumTraced(root *TreeNode) int {
	best := -1 << 62
	var gain func(*TreeNode) int
	gain = func(node *TreeNode) int {
		if node == nil {
			return 0
		}
		left := maxInt(gain(node.Left), 0)
		right := maxInt(gain(node.Right), 0)
		through := node.Val + left + right
		if through > best {
			best = through
		}
		fmt.Printf("    node %-4d left-gain=%-4d right-gain=%-4d through=%-5d running-best=%d\n",
			node.Val, left, right, through, best)
		return node.Val + maxInt(left, right)
	}
	gain(root)
	return best
}

// maxPathSumPointerState is the same algorithm using a *int instead of a
// closure capture -- shown only to demonstrate the alternative Go idiom.
func maxPathSumPointerState(root *TreeNode) int {
	best := -1 << 62
	gainPtr(root, &best)
	return best
}

func gainPtr(node *TreeNode, best *int) int {
	if node == nil {
		return 0
	}
	left := maxInt(gainPtr(node.Left, best), 0)
	right := maxInt(gainPtr(node.Right, best), 0)
	if through := node.Val + left + right; through > *best {
		*best = through
	}
	return node.Val + maxInt(left, right)
}

// maxPathSumBuggyThroughReturn returns the "through" value instead of the
// "gain" value -- the #1 real-world bug for this problem. Kept only to
// prove, at runtime, how it corrupts the answer.
func maxPathSumBuggyThroughReturn(root *TreeNode) int {
	best := -1 << 62
	var gain func(*TreeNode) int
	gain = func(node *TreeNode) int {
		if node == nil {
			return 0
		}
		left := maxInt(gain(node.Left), 0)
		right := maxInt(gain(node.Right), 0)
		if through := node.Val + left + right; through > best {
			best = through
		}
		return node.Val + left + right // BUG: should be node.Val + max(left, right)
	}
	gain(root)
	return best
}

// maxPathSumBruteForce recomputes each node's best downward gain from
// scratch for every candidate turning point -- O(n^2), only for contrast.
func maxPathSumBruteForce(root *TreeNode) int {
	best := -1 << 62
	var downward func(*TreeNode) int
	downward = func(node *TreeNode) int {
		if node == nil {
			return 0
		}
		l := maxInt(downward(node.Left), 0)
		r := maxInt(downward(node.Right), 0)
		return node.Val + maxInt(l, r)
	}
	var visitAll func(*TreeNode)
	visitAll = func(node *TreeNode) {
		if node == nil {
			return
		}
		l := maxInt(downward(node.Left), 0)
		r := maxInt(downward(node.Right), 0)
		if through := node.Val + l + r; through > best {
			best = through
		}
		visitAll(node.Left)
		visitAll(node.Right)
	}
	visitAll(root)
	return best
}

func main() {
	type testCase struct {
		name string
		root *TreeNode
		want int
	}

	// [1,2,3]
	t1 := &TreeNode{Val: 1, Left: &TreeNode{Val: 2}, Right: &TreeNode{Val: 3}}

	// [-10,9,20,null,null,15,7] -- best path skips the root entirely
	t2 := &TreeNode{
		Val:  -10,
		Left: &TreeNode{Val: 9},
		Right: &TreeNode{
			Val:   20,
			Left:  &TreeNode{Val: 15},
			Right: &TreeNode{Val: 7},
		},
	}

	// all-negative tree
	allNeg := &TreeNode{Val: -2, Left: &TreeNode{Val: -5}, Right: &TreeNode{Val: -3}}

	// small tree for the buggy-return demo: root=-1, left=2(children 4,5), right=3
	//         -1
	//        /   \
	//       2     3
	//     /  \
	//    4    5
	bugTree := &TreeNode{
		Val: -1,
		Left: &TreeNode{
			Val:   2,
			Left:  &TreeNode{Val: 4},
			Right: &TreeNode{Val: 5},
		},
		Right: &TreeNode{Val: 3},
	}

	cases := []testCase{
		{"LC example 1: [1,2,3] -> 6", t1, 6},
		{"LC example 2: skips root -> 42", t2, 42},
		{"single node [5] -> 5", &TreeNode{Val: 5}, 5},
		{"single node [-3] -> -3", &TreeNode{Val: -3}, -3},
		{"all negative [-2,-5,-3] -> -2", allNeg, -2},
		{"4 -> 2 -> 5 gives 11 (root -1 not included)", bugTree, 11},
	}

	allOK := true
	for _, tc := range cases {
		gotClosure := maxPathSum(tc.root)
		gotPointer := maxPathSumPointerState(tc.root)
		gotBrute := maxPathSumBruteForce(tc.root)
		ok := gotClosure == tc.want && gotPointer == tc.want && gotBrute == tc.want
		allOK = allOK && ok
		fmt.Printf("%s  %-42s want=%-4d closure=%-4d pointer=%-4d brute=%d\n",
			status(ok), tc.name, tc.want, gotClosure, gotPointer, gotBrute)
	}

	fmt.Println("\n--- live trace: best path forms entirely inside node 20's subtree, root -10 doesn't help ---")
	traced := maxPathSumTraced(t2)
	fmt.Printf("    final answer: %d (never improved once the root -10 was processed last)\n", traced)

	fmt.Println("\n--- why returning \"through\" instead of \"gain\" corrupts the answer ---")
	correct := maxPathSum(bugTree)
	buggy := maxPathSumBuggyThroughReturn(bugTree)
	fmt.Printf("  correct (return node.Val+max(left,right)) -> %d  (path 4 -> 2 -> 5)\n", correct)
	fmt.Printf("  buggy   (return node.Val+left+right)       -> %d  <- invalid, forks the path at 2\n", buggy)

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
