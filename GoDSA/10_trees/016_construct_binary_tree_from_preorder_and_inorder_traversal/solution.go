package main

import "fmt"

/*
================================================================================
SOLUTION · LeetCode 105 · Construct Binary Tree from Preorder and Inorder
                          Traversal                                    [Medium]
https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/
================================================================================

THE CORE IDEA
--------------
Each traversal contributes one fact, and together they're enough to split the
problem recursively:

    preorder = [ROOT] [.... left subtree ....] [.... right subtree ....]
    inorder  = [.... left subtree ....] [ROOT] [.... right subtree ....]

    preorder[0]        -> WHO the root is
    root's index in inorder -> HOW MANY nodes are in the left subtree

Once you know the root and the left-subtree SIZE, you can cut both traversals
at the same place and recurse on each half.

    func build(loIn, hiIn int) *TreeNode {         // bounds into INORDER
        if loIn > hiIn { return nil }
        val := preorder[cursor]; cursor++
        node := &TreeNode{Val: val}
        k := posInInorder[val]                     // O(1) via prebuilt map
        node.Left  = build(loIn, k-1)               // LEFT FIRST -- mandatory
        node.Right = build(k+1, hiIn)
        return node
    }

O(n) time: O(n) to build the value->index map, then O(1) work per node.


================================================================================
⚠️  THE GO-SPECIFIC WRINKLE — no tuple return, so the cursor needs a closure
================================================================================
Python threads a shared mutable index by capturing it in a nested function
(or an `itertools.islice`/pop trick) — the recursive calls all read AND
advance the same variable via closure captures, and there's no dict.pop or
tuple-unpack that makes this cleaner in Go; the direct translation is the
same idiom the topic guide's serialize/deserialize section uses:

    cursor := 0
    var build func(loIn, hiIn int) *TreeNode
    build = func(loIn, hiIn int) *TreeNode {
        ...
        val := preorder[cursor]
        cursor++                    // closure mutates the CAPTURED variable
        ...
    }

`var build func(...)` must be pre-declared before the assignment because a
self-referencing closure literal needs its own name already in scope — this
is the same requirement the topic guide's diameter closure (§3.2) explains.
The alternative — returning `(*TreeNode, int)` (node, newCursor) from every
call and threading the int by hand through every caller — works too and
avoids the closure, but is strictly more plumbing for the same result; both
are shown below so you can compare.


================================================================================
APPROACH 1 · Brute force — re-search inorder for the root's index every call
================================================================================
    k := -1
    for i, v := range inorderSlice { if v == rootVal { k = i; break } }

    Time:  O(n^2) worst case (a skewed tree searches an O(n) window n times)
    Space: O(n) for the recursion + any slice copies

Correct but slow — the search collapses to O(1) once you precompute the
value -> index map up front, since all values are guaranteed unique.


================================================================================
APPROACH 2 · Closure-captured cursor + index map ✅ (the answer)
================================================================================
Shown above.


================================================================================
APPROACH 3 · Explicit (node, newCursor) return — no closure
================================================================================
    func build(cursor, loIn, hiIn int) (*TreeNode, int) {
        if loIn > hiIn { return nil, cursor }
        val := preorder[cursor]
        cursor++
        node := &TreeNode{Val: val}
        k := posInInorder[val]
        node.Left, cursor = build(cursor, loIn, k-1)
        node.Right, cursor = build(cursor, k+1, hiIn)
        return node, cursor
    }

Same O(n) time and result; this is what you'd write in a language without
closures at all. Go supports both — knowing the closure version is idiomatic
here (and cheaper to read) is the point, not that the explicit version is
wrong.


================================================================================
STEP BY STEP · preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]
================================================================================
    posInInorder = {9:0, 3:1, 15:2, 20:3, 7:4}
    cursor = 0

    build(loIn=0, hiIn=4):
        val = preorder[0] = 3, cursor -> 1.  node = TreeNode(3)
        k = posInInorder[3] = 1
        node.Left  = build(loIn=0, hiIn=0)      -- left subtree: inorder[0..0] = [9]
            val = preorder[1] = 9, cursor -> 2.  node = TreeNode(9)
            k = posInInorder[9] = 0
            node.Left  = build(0, -1) = nil
            node.Right = build(1, 0) = nil
            -> TreeNode(9), leaf
        node.Right = build(loIn=2, hiIn=4)      -- right subtree: inorder[2..4] = [15,20,7]
            val = preorder[2] = 20, cursor -> 3.  node = TreeNode(20)
            k = posInInorder[20] = 3
            node.Left  = build(loIn=2, hiIn=2)  -- [15]
                val = preorder[3] = 15, cursor -> 4.  TreeNode(15), leaf
            node.Right = build(loIn=4, hiIn=4)  -- [7]
                val = preorder[4] = 7, cursor -> 5.  TreeNode(7), leaf
            -> TreeNode(20, left=15, right=7)

    Final tree:            3
                          /   \
                         9     20
                              /  \
                            15    7

    Matches [3,9,20,null,null,15,7]. ✓  Proven live below with a level-order
    dump of the reconstructed tree.


================================================================================
⚠️ WHY LEFT MUST BE BUILT BEFORE RIGHT — proven live, not just asserted
================================================================================
Preorder lists nodes in exactly the order this recursion CREATES them: root,
then the ENTIRE left subtree, then the ENTIRE right subtree. The cursor is a
single monotonically advancing pointer into that exact order. If you build
node.Right before node.Left, the cursor is still sitting at the start of the
LEFT subtree's values when the RIGHT-building call starts consuming them —
the right subtree gets built from values that belong to the left, and
everything downstream is corrupted. On this example, swapping the two lines
doesn't just produce a wrong tree — the cursor drifts far enough that it
runs off the end of preorder entirely and Go PANICS with an index-out-of-
-range, caught live with recover() below rather than crashing the demo.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time     Space   Mutates input?
    ---------------------------------  -------  ------  ---------------
    Brute force (re-search inorder)    O(n^2)   O(n)    No
    Closure cursor + index map     ✅  O(n)     O(n)    No
    Explicit (node, cursor) return     O(n)     O(n)    No


================================================================================
EDGE CASES
================================================================================
    single node: preorder=[-1], inorder=[-1] -> single TreeNode(-1).
    left-skewed only: preorder=[3,2,1], inorder=[1,2,3] -> every root's left
                               subtree is everything remaining, right is empty.
    right-skewed only: preorder=[1,2,3], inorder=[1,2,3] -> every root's
                               right subtree is everything remaining, left
                               empty; note preorder == inorder here, a
                               degenerate case worth recognizing by eye.
    two nodes, root then one child: preorder=[1,2], inorder=[1,2] (right
                               child) vs preorder=[1,2], inorder=[2,1] (left
                               child) — the ONLY thing that distinguishes
                               them is inorder's position relative to root.
    negative values           -> map keys and comparisons work identically;
                               nothing here depends on sign.
    all-unique-values guarantee -> the problem states this explicitly; the
                               index map would silently misbehave (last
                               value wins) on duplicates, which is why this
                               algorithm does NOT generalize to trees with
                               repeated values without extra disambiguation.


================================================================================
COMMON MISTAKES
================================================================================
1. Building node.Right before node.Left — corrupts the tree because the
   preorder cursor is order-dependent. Demonstrated live below.

2. Re-scanning inorder with a linear search per node instead of a prebuilt
   map — correct but silently degrades to O(n^2), invisible until tested on
   a large/skewed input.

3. Re-slicing preorder/inorder at every call (`preorder[1:]`,
   `inorder[:k]`) instead of passing index bounds — works but does needless
   extra bookkeeping and is easy to get off-by-one on repeatedly; bounds
   into a single shared map + a single shared preorder are more robust.

4. Forgetting `var build func(...)` pre-declaration before a self-recursive
   closure literal — `build := func(...) { ... build(...) ... }` does not
   compile: build doesn't exist yet on the right-hand side of `:=`.


================================================================================
FOLLOW-UPS
================================================================================
    - LC 106: Construct from INORDER + POSTORDER instead — same idea, but
      the cursor now advances from the END of postorder backward, and you
      build RIGHT before LEFT (postorder's root sits at the back: L, R, root).
    - Why doesn't PREORDER + POSTORDER work? Both only identify the root;
      neither gives the split point the way inorder's root-position does —
      see the topic guide Part 7 discussion of this exact ambiguity.
    - What if values aren't guaranteed unique? The index-map approach breaks
      (which occurrence does a value map to?); you'd need to carry index
      information through some other channel (e.g. wrap each value with its
      original preorder position).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 106  Construct Binary Tree from Inorder and Postorder Traversal
    LC 889  Construct Binary Tree from Preorder and Postorder Traversal
             (ambiguous in general; LC guarantees a valid full binary tree)
    LC 297  Serialize and Deserialize Binary Tree (problem 019, this topic)
             — the general-purpose version of "traversal -> unique tree"
================================================================================
*/

// buildTree is the interview answer: closure-captured preorder cursor +
// a prebuilt value -> inorder-index map.
func buildTree(preorder []int, inorder []int) *TreeNode {
	posInInorder := make(map[int]int, len(inorder))
	for i, v := range inorder {
		posInInorder[v] = i
	}

	cursor := 0
	var build func(loIn, hiIn int) *TreeNode
	build = func(loIn, hiIn int) *TreeNode {
		if loIn > hiIn {
			return nil
		}
		val := preorder[cursor]
		cursor++
		node := &TreeNode{Val: val}
		k := posInInorder[val]
		node.Left = build(loIn, k-1)  // LEFT FIRST -- mandatory, see prose above
		node.Right = build(k+1, hiIn) // built AFTER left has consumed its cursor range
		return node
	}
	return build(0, len(inorder)-1)
}

// buildTreeExplicitCursor avoids the closure by threading (node, newCursor)
// explicitly through every call -- what you'd write without closures at all.
func buildTreeExplicitCursor(preorder []int, inorder []int) *TreeNode {
	posInInorder := make(map[int]int, len(inorder))
	for i, v := range inorder {
		posInInorder[v] = i
	}
	node, _ := buildExplicit(preorder, posInInorder, 0, 0, len(inorder)-1)
	return node
}

func buildExplicit(preorder []int, posInInorder map[int]int, cursor, loIn, hiIn int) (*TreeNode, int) {
	if loIn > hiIn {
		return nil, cursor
	}
	val := preorder[cursor]
	cursor++
	node := &TreeNode{Val: val}
	k := posInInorder[val]
	node.Left, cursor = buildExplicit(preorder, posInInorder, cursor, loIn, k-1)
	node.Right, cursor = buildExplicit(preorder, posInInorder, cursor, k+1, hiIn)
	return node, cursor
}

// buildTreeSwappedOrder is the BUGGY version -- builds Right before Left.
// Kept only to prove live why order matters; never call this in production.
func buildTreeSwappedOrder(preorder []int, inorder []int) *TreeNode {
	posInInorder := make(map[int]int, len(inorder))
	for i, v := range inorder {
		posInInorder[v] = i
	}
	cursor := 0
	var build func(loIn, hiIn int) *TreeNode
	build = func(loIn, hiIn int) *TreeNode {
		if loIn > hiIn {
			return nil
		}
		val := preorder[cursor]
		cursor++
		node := &TreeNode{Val: val}
		k := posInInorder[val]
		node.Right = build(k+1, hiIn) // BUG: right before left
		node.Left = build(loIn, k-1)
		return node
	}
	return build(0, len(inorder)-1)
}

// levelOrderVals dumps a tree level by level for readable comparison in
// test output (reuses the BFS pattern from problem 013).
func levelOrderVals(root *TreeNode) [][]int {
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

func sameShape(a, b *TreeNode) bool {
	if a == nil || b == nil {
		return a == b
	}
	return a.Val == b.Val && sameShape(a.Left, b.Left) && sameShape(a.Right, b.Right)
}

func main() {
	type testCase struct {
		name     string
		preorder []int
		inorder  []int
		want     *TreeNode
	}

	// [3,9,20,null,null,15,7]
	want1 := &TreeNode{
		Val:  3,
		Left: &TreeNode{Val: 9},
		Right: &TreeNode{
			Val:   20,
			Left:  &TreeNode{Val: 15},
			Right: &TreeNode{Val: 7},
		},
	}

	cases := []testCase{
		{"LC example 1", []int{3, 9, 20, 15, 7}, []int{9, 3, 15, 20, 7}, want1},
		{"single node", []int{-1}, []int{-1}, &TreeNode{Val: -1}},
		{"left-skewed: preorder=[3,2,1] inorder=[1,2,3]",
			[]int{3, 2, 1}, []int{1, 2, 3},
			&TreeNode{Val: 3, Left: &TreeNode{Val: 2, Left: &TreeNode{Val: 1}}}},
		{"right-skewed: preorder=[1,2,3] inorder=[1,2,3]",
			[]int{1, 2, 3}, []int{1, 2, 3},
			&TreeNode{Val: 1, Right: &TreeNode{Val: 2, Right: &TreeNode{Val: 3}}}},
		{"two nodes, right child: pre=[1,2] in=[1,2]",
			[]int{1, 2}, []int{1, 2},
			&TreeNode{Val: 1, Right: &TreeNode{Val: 2}}},
		{"two nodes, left child: pre=[1,2] in=[2,1]",
			[]int{1, 2}, []int{2, 1},
			&TreeNode{Val: 1, Left: &TreeNode{Val: 2}}},
		{"negative values",
			[]int{-1, -2, -3}, []int{-2, -1, -3},
			&TreeNode{Val: -1, Left: &TreeNode{Val: -2}, Right: &TreeNode{Val: -3}}},
	}

	allOK := true
	for _, tc := range cases {
		got := buildTree(append([]int{}, tc.preorder...), tc.inorder)
		gotExplicit := buildTreeExplicitCursor(append([]int{}, tc.preorder...), tc.inorder)
		ok := sameShape(got, tc.want) && sameShape(gotExplicit, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  %-45s closure-levels=%v  explicit-levels=%v\n",
			status(ok), tc.name, levelOrderVals(got), levelOrderVals(gotExplicit))
	}

	fmt.Println("\n--- why left-before-right is mandatory, not stylistic ---")
	preorder := []int{3, 9, 20, 15, 7}
	inorder := []int{9, 3, 15, 20, 7}
	correct := buildTree(preorder, inorder)
	fmt.Printf("  correct (left-first)  level order: %v\n", levelOrderVals(correct))
	func() {
		defer func() {
			if r := recover(); r != nil {
				fmt.Printf("  buggy   (right-first) -> PANIC: %v\n", r)
				fmt.Println("  the cursor runs past the end of preorder entirely -- not just a wrong")
				fmt.Println("  tree, an out-of-bounds crash. Proves left-before-right is load-bearing.")
			}
		}()
		buggy := buildTreeSwappedOrder(preorder, inorder)
		fmt.Printf("  buggy   (right-first) level order: %v  <- corrupted, if it didn't panic first\n",
			levelOrderVals(buggy))
	}()

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
