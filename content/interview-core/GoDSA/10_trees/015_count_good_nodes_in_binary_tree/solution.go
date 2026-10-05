package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 1448 · Count Good Nodes in Binary Tree              [Medium]
https://leetcode.com/problems/count-good-nodes-in-binary-tree/
================================================================================

THE CORE IDEA
--------------
"Good" is defined entirely by the path ABOVE a node — its ancestors — so the
state a node needs (the max value seen so far on the root-to-here path) must
be threaded DOWN as a recursion parameter. This is a top-down problem, the
mirror of problem 018 (Max Path Sum), which is bottom-up because its answer
depends on DESCENDANTS instead.

    func dfs(node *TreeNode, maxSoFar int) int {
        if node == nil {
            return 0
        }
        count := 0
        if node.Val >= maxSoFar {              // path INCLUDES this node
            count = 1
        }
        newMax := max(maxSoFar, node.Val)
        return count + dfs(node.Left, newMax) + dfs(node.Right, newMax)
    }
    goodNodes(root) = dfs(root, math.MinInt)


================================================================================
APPROACH 1 · Brute force — for each node, walk its full root path
================================================================================
For every node, retrace the path from root down to it (or store the whole
path during a DFS) and scan for any ancestor exceeding its value.

    Time:  O(n^2) worst case (each of n nodes re-scans up to n ancestors on
           a skewed tree)   Space: O(h) for the path being retraced

Wasteful: each recursive call already KNOWS the running max from its
ancestors if you thread it down instead of recomputing it. State this, then
collapse to approach 2.


================================================================================
APPROACH 2 · Top-down DFS with a threaded maxSoFar ✅ (the answer)
================================================================================
Shown above. `math.MinInt` (or -1<<63) safely seeds the threshold below any
possible node value (-10^4..10^4), guaranteeing the root always counts.


================================================================================
STEP BY STEP · root = [3,1,4,3,null,1,5]
================================================================================
              3
            ┌─┴─┐
            1   4
           ┴   ┌─┴─┐
          3     1   5

    dfs(3, maxSoFar=-inf): 3 >= -inf -> GOOD (count root). newMax = 3
        dfs(1, maxSoFar=3): 1 >= 3? NO -> not good. newMax = max(3,1) = 3
            dfs(3(left-left), maxSoFar=3): 3 >= 3? YES (ties count!) -> GOOD
        dfs(4, maxSoFar=3): 4 >= 3? YES -> GOOD. newMax = max(3,4) = 4
            dfs(1(right-left), maxSoFar=4): 1 >= 4? NO -> not good
            dfs(5, maxSoFar=4): 5 >= 4? YES -> GOOD

    Good nodes: 3(root), 3(left-left, tie), 4, 5  -> total 4.  Matches LC.

    The left-left 3 is the case that proves `>=` (not `>`) is required: it
    ties the running max exactly and MUST count, per the problem's own
    example. Flip to strict `>` and this test breaks — demonstrated live.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time     Space   Mutates input?
    -------------------------------  -------  ------  ---------------
    Brute force (re-walk each path)  O(n^2)   O(h)    No
    Top-down threaded maxSoFar   ✅  O(n)     O(h)    No


================================================================================
EDGE CASES
================================================================================
    single node [1]          -> 1 (root is always good).
    all values equal, e.g. [2,2,2,2]  -> every node good, since `>=` treats
                               ties as good — this is the "off by strictness"
                               case the >= vs > choice must handle correctly.
    strictly decreasing chain (root largest, e.g. [5,4,3,2,1] all Left)
                              -> only the ROOT is good: node 5 sets max=5,
                                 then every descendant is strictly smaller
                                 than 5, so none of them clear the threshold.
                                 The opposite extreme from the equal-values
                                 case, demonstrated live.
    strictly increasing chain (root smallest, e.g. [1,2,3,4,5] all Left)
                              -> every node good; each exceeds or ties every
                                 ancestor's max.
    negative values           -> maxSoFar seeding must be BELOW the value
                                 range's true minimum (-10^4), not 0 —
                                 seeding with 0 would wrongly mark a root of
                                 value -5 as "not good."


================================================================================
COMMON MISTAKES
================================================================================
1. Using strict `>` instead of `>=` when comparing node.Val to maxSoFar —
   fails on the tie case (LC's own example 1 has one: the left-left 3).

2. Seeding maxSoFar with 0 instead of a true negative sentinel — breaks on
   trees whose root or early nodes are negative.

3. Updating maxSoFar with the CHILD's value before computing whether the
   CURRENT node is good — order matters: check current node against the
   ancestor-only maxSoFar first, THEN fold the current node's value in for
   the recursive calls into children.

4. Forgetting that "good" is defined per PATH from root, not "global max
   anywhere in the tree" — a node deep on one branch is unaffected by a
   larger value sitting on a sibling branch it shares no path with.


================================================================================
FOLLOW-UPS
================================================================================
    - Return the good nodes themselves (values or pointers), not just a
      count — trivial extension, append instead of increment.
    - What changes for an N-ary tree? Same recursion, loop over
      node.Children instead of two fixed calls.
    - Could this be solved bottom-up instead? No natural way — "good"
      genuinely requires ancestor information, which only exists on the way
      down, unlike problem 018 where the answer is a pure function of
      descendants.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 112  Path Sum (problem 011, this topic) — same top-down threaded-state
                                                   shape (remaining budget vs.
                                                   maxSoFar)
    LC 987  Vertical Order Traversal — top-down column tracking
    LC 129  Sum Root to Leaf Numbers — top-down digit accumulation
================================================================================
*/

// goodNodes is the interview answer: top-down DFS threading the max value
// seen so far on the root-to-here path.
func goodNodes(root *TreeNode) int {
	const negInf = -1 << 62
	return goodNodesDFS(root, negInf)
}

func goodNodesDFS(node *TreeNode, maxSoFar int) int {
	if node == nil {
		return 0
	}
	count := 0
	if node.Val >= maxSoFar {
		count = 1
	}
	newMax := maxSoFar
	if node.Val > newMax {
		newMax = node.Val
	}
	return count + goodNodesDFS(node.Left, newMax) + goodNodesDFS(node.Right, newMax)
}

// goodNodesBruteForce retraces the full root-to-node path for every node.
// O(n^2) worst case, only for contrast.
func goodNodesBruteForce(root *TreeNode) int {
	var path []int
	count := 0
	var walk func(*TreeNode)
	walk = func(node *TreeNode) {
		if node == nil {
			return
		}
		path = append(path, node.Val)
		isGood := true
		for _, v := range path[:len(path)-1] {
			if v > node.Val {
				isGood = false
				break
			}
		}
		if isGood {
			count++
		}
		walk(node.Left)
		walk(node.Right)
		path = path[:len(path)-1]
	}
	walk(root)
	return count
}

// goodNodesStrictGT is the buggy `>` version -- kept to prove the tie case
// matters, never call this in production code.
func goodNodesStrictGT(node *TreeNode, maxSoFar int) int {
	if node == nil {
		return 0
	}
	count := 0
	if node.Val > maxSoFar { // BUG: should be >=
		count = 1
	}
	newMax := maxSoFar
	if node.Val > newMax {
		newMax = node.Val
	}
	return count + goodNodesStrictGT(node.Left, newMax) + goodNodesStrictGT(node.Right, newMax)
}

func main() {
	// [3,1,4,3,null,1,5]
	t1 := &TreeNode{
		Val: 3,
		Left: &TreeNode{
			Val:  1,
			Left: &TreeNode{Val: 3},
		},
		Right: &TreeNode{
			Val:   4,
			Left:  &TreeNode{Val: 1},
			Right: &TreeNode{Val: 5},
		},
	}

	// [3,3,null,4,2]
	t2 := &TreeNode{
		Val: 3,
		Left: &TreeNode{
			Val:   3,
			Left:  &TreeNode{Val: 4},
			Right: &TreeNode{Val: 2},
		},
	}

	// strictly decreasing all-left chain: only the root is good
	decreasing := &TreeNode{Val: 5, Left: &TreeNode{Val: 4, Left: &TreeNode{Val: 3, Left: &TreeNode{Val: 2, Left: &TreeNode{Val: 1}}}}}

	// strictly increasing all-left chain: every node is good
	increasing := &TreeNode{Val: 1, Left: &TreeNode{Val: 2, Left: &TreeNode{Val: 3, Left: &TreeNode{Val: 4, Left: &TreeNode{Val: 5}}}}}

	// all equal values: every node good via the tie rule
	allEqual := &TreeNode{Val: 2, Left: &TreeNode{Val: 2, Left: &TreeNode{Val: 2}}, Right: &TreeNode{Val: 2}}

	// negative root and descendants
	negatives := &TreeNode{Val: -5, Left: &TreeNode{Val: -3}, Right: &TreeNode{Val: -10}}

	type testCase struct {
		name string
		root *TreeNode
		want int
	}
	cases := []testCase{
		{"LC example 1", t1, 4},
		{"LC example 2", t2, 3},
		{"single node [1]", &TreeNode{Val: 1}, 1},
		{"strictly decreasing chain -> only root", decreasing, 1},
		{"strictly increasing chain -> all good", increasing, 5},
		{"all equal values -> all good (ties count)", allEqual, 4},
		{"negative values", negatives, 2}, // -5 good, -3 good (>=-5), -10 not good
	}

	allOK := true
	for _, tc := range cases {
		gotDFS := goodNodes(tc.root)
		gotBrute := goodNodesBruteForce(tc.root)
		ok := gotDFS == tc.want && gotBrute == tc.want
		allOK = allOK && ok
		fmt.Printf("%s  %-38s want=%-3d top-down=%-3d brute-force=%d\n",
			status(ok), tc.name, tc.want, gotDFS, gotBrute)
	}

	fmt.Println("\n--- why >= (not >) is mandatory: LC example 1's tied left-left 3 ---")
	correctCount := goodNodes(t1)
	buggyCount := goodNodesStrictGT(t1, -1<<62)
	fmt.Printf("  correct (>=) -> %d good nodes (includes the tied 3)\n", correctCount)
	fmt.Printf("  buggy   (>)  -> %d good nodes (drops the tied 3)\n", buggyCount)

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
