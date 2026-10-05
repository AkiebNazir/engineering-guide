package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 112 · Path Sum                                       [Easy]
https://leetcode.com/problems/path-sum/
================================================================================

THE CORE IDEA
--------------
Push the remaining budget DOWN as you recurse, and only ask "did it land on
exactly 0?" at a genuine leaf:

    func hasPathSum(node *TreeNode, remaining int) bool {
        if node == nil {
            return false                          // nil is never a success
        }
        remaining -= node.Val
        if node.Left == nil && node.Right == nil { // a real leaf
            return remaining == 0
        }
        return hasPathSum(node.Left, remaining) || hasPathSum(node.Right, remaining)
    }

This is a top-down (preorder-flavored) recursion: the "state" (remaining
budget) is a function of everything ABOVE the current node, so it must be
threaded down as a parameter — the mirror image of problem 018's postorder
aggregate, where information flows up instead.


================================================================================
APPROACH 1 · Brute force — collect every root-to-leaf path, then check
================================================================================
Build every full path as a []int (or track a running sum in a slice you
backtrack), then scan all paths for one that sums to targetSum.

    Time:  O(n) nodes visited, but O(n) extra space to store every path
           (worst case a skewed tree has one path of length n)
    Space: O(n)

Correct, but wasteful: you never need the WHOLE path, only whether the
leaf-level running sum matches. State it, then collapse to approach 2.


================================================================================
APPROACH 2 · Shrinking-target recursion ✅ (the answer)
================================================================================
Shown above. Subtract as you descend; check equality only at a leaf.


================================================================================
STEP BY STEP · root = [5,4,8,11,null,13,4,7,2,null,null,null,1], target = 22
================================================================================
                5
              ┌─┴─┐
              4    8
            ┌─┴┐  ┌─┴─┐
           11  ·  13   4
          ┌─┴┐         ┌─┴┐
          7  2          ·  1

    remaining starts at 22.

    5 -> remaining = 22-5  = 17
    4 -> remaining = 17-4  = 13
    11-> remaining = 13-11 = 2
    2 -> remaining = 2-2   = 0, and 2 IS a leaf  -> MATCH, return true

    Path 5 -> 4 -> 11 -> 2 sums to 5+4+11+2 = 22.  ✓

    The OTHER branch under 11 (the 7 leaf) would give remaining = 2-7 = -5,
    a leaf, not zero -> false for that branch. `||` short-circuits once the
    2-branch returns true, so 7's branch may not even be visited depending on
    child order — demonstrated live below with a visit counter.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time    Space   Mutates input?
    ---------------------------  ------  ------  ---------------
    Collect all paths            O(n)    O(n)    No
    Shrinking-target recursion✅ O(n)    O(h)    No


================================================================================
EDGE CASES
================================================================================
    nil root               -> false, even if targetSum == 0 (no leaf exists;
                               this is explicitly called out in the problem).
    single node [5], sum=5 -> true (root is also the leaf).
    single node [5], sum=4 -> false.
    skewed tree (all Left, or all Right) -> depth n, O(h)=O(n) stack space,
                               same "degenerate tree" risk the topic guide
                               flags for any recursive DFS.
    negative values         -> remaining can legitimately go negative and
                               later come back to exactly 0 lower in the
                               tree; do NOT prune early on remaining < 0.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking `remaining == 0` at a nil node instead of a leaf — a node with
   exactly one child would then look like a leaf via its nil side, silently
   accepting non-leaf "paths".

2. Checking `node.Val == remaining` BEFORE subtracting, then also
   subtracting — double-counts or off-by-one's the root's own value.

3. Returning true on ANY node summing to target (subtree-sum, not
   root-to-leaf) — that is a different, related problem (LC 437, Path Sum
   III), not this one.

4. Pruning when remaining goes negative, assuming values are non-negative.
   The constraints explicitly allow negative node values.


================================================================================
FOLLOW-UPS
================================================================================
    - Return the actual path, not just true/false (LC 113, Path Sum II).
    - Count ALL paths (not just root-to-leaf) that sum to target — needs a
      prefix-sum hash map, not this recursion (LC 437, Path Sum III).
    - What if the tree is a general N-ary tree? Same recursion, `for _, c :=
      range node.Children` in place of the two child calls.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 113  Path Sum II            — same idea, collect the paths
    LC 437  Path Sum III           — prefix-sum hashmap, any-to-any path
    LC 129  Sum Root to Leaf Numbers — same top-down shape, digit accumulation
================================================================================
*/

// hasPathSum is the interview answer: shrinking-target top-down recursion.
func hasPathSum(root *TreeNode, targetSum int) bool {
	if root == nil {
		return false
	}
	remaining := targetSum - root.Val
	if root.Left == nil && root.Right == nil {
		return remaining == 0
	}
	return hasPathSum(root.Left, remaining) || hasPathSum(root.Right, remaining)
}

// hasPathSumCollectAll is the brute-force approach: gather every root-to-leaf
// path, then scan. O(n) space beyond the recursion, only for contrast.
func hasPathSumCollectAll(root *TreeNode, targetSum int) bool {
	var paths [][]int
	var path []int
	var walk func(*TreeNode)
	walk = func(node *TreeNode) {
		if node == nil {
			return
		}
		path = append(path, node.Val)
		if node.Left == nil && node.Right == nil {
			cp := make([]int, len(path))
			copy(cp, path)
			paths = append(paths, cp)
		}
		walk(node.Left)
		walk(node.Right)
		path = path[:len(path)-1] // backtrack
	}
	walk(root)
	for _, p := range paths {
		sum := 0
		for _, v := range p {
			sum += v
		}
		if sum == targetSum {
			return true
		}
	}
	return false
}

// visitCount instruments hasPathSum to prove the || short-circuit live.
func hasPathSumCounting(root *TreeNode, targetSum int, visits *int) bool {
	if root == nil {
		return false
	}
	*visits++
	remaining := targetSum - root.Val
	if root.Left == nil && root.Right == nil {
		return remaining == 0
	}
	return hasPathSumCounting(root.Left, remaining, visits) ||
		hasPathSumCounting(root.Right, remaining, visits)
}

func main() {
	type testCase struct {
		name   string
		root   *TreeNode
		target int
		want   bool
	}

	// LC example 1: [5,4,8,11,null,13,4,7,2,null,null,null,1]
	//         5
	//       /   \
	//      4     8
	//     /     / \
	//    11    13  4
	//   /  \         \
	//  7    2         1
	t1 := &TreeNode{
		Val: 5,
		Left: &TreeNode{
			Val: 4,
			Left: &TreeNode{
				Val:   11,
				Left:  &TreeNode{Val: 7},
				Right: &TreeNode{Val: 2},
			},
		},
		Right: &TreeNode{
			Val:  8,
			Left: &TreeNode{Val: 13},
			Right: &TreeNode{
				Val:   4,
				Right: &TreeNode{Val: 1},
			},
		},
	}

	cases := []testCase{
		{"LC example 1 -> true", t1, 22, true},
		{"[1,2,3] target 5 -> false",
			&TreeNode{Val: 1, Left: &TreeNode{Val: 2}, Right: &TreeNode{Val: 3}}, 5, false},
		{"nil root, target 0 -> false", nil, 0, false},
		{"single node [5] target 5 -> true", &TreeNode{Val: 5}, 5, true},
		{"single node [5] target 4 -> false", &TreeNode{Val: 5}, 4, false},
		{"skewed left, sums to target -> true",
			&TreeNode{Val: 1, Left: &TreeNode{Val: 2, Left: &TreeNode{Val: 3}}}, 6, true},
		{"negative values, path dips then recovers -> true",
			&TreeNode{Val: 1, Left: &TreeNode{Val: -2, Right: &TreeNode{Val: 5}}}, 4, true},
	}

	allOK := true
	for _, tc := range cases {
		got := hasPathSum(tc.root, tc.target)
		gotBrute := hasPathSumCollectAll(tc.root, tc.target)
		ok := got == tc.want && gotBrute == tc.want
		allOK = allOK && ok
		fmt.Printf("%s  %-42s want=%-5v got(recursive)=%-5v got(collect-all)=%v\n",
			status(ok), tc.name, tc.want, got, gotBrute)
	}

	fmt.Println("\n--- short-circuit proof: recursion stops once a match is found ---")
	visits := 0
	got := hasPathSumCounting(t1, 22, &visits)
	fmt.Printf("  target 22 -> %v, nodes visited = %d (13-node tree, not all 13 touched)\n", got, visits)

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
