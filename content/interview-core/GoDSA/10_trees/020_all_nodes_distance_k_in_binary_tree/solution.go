package main

import (
	"fmt"
	"math/rand"
	"slices"
)

/*
================================================================================
SOLUTION · LeetCode 863 · All Nodes Distance K in Binary Tree           [Medium]
https://leetcode.com/problems/all-nodes-distance-k-in-binary-tree/
================================================================================

THE CORE IDEA
--------------
A binary tree is an undirected graph that only stores its downward edges.
Record parents in a map[*TreeNode]*TreeNode and it becomes a normal graph.
BFS from target for exactly k levels; what's left in the frontier is the
answer. The visited set is mandatory now, because parent edges let you walk
straight back to where you came from.


================================================================================
APPROACH 1 · Parent map + level-by-level BFS ✅ (the answer)
================================================================================
    parent := map[*TreeNode]*TreeNode{}
    // fill by DFS
    level := []*TreeNode{target}
    seen := map[*TreeNode]bool{target: true}
    for d := 0; d < k && len(level) > 0; d++ {
        var next []*TreeNode
        for _, node := range level {
            for _, nb := range [3]*TreeNode{node.Left, node.Right, parent[node]} {
                if nb != nil && !seen[nb] {
                    seen[nb] = true
                    next = append(next, nb)
                }
            }
        }
        level = next
    }

`parent[root]` is never written: the missing key reads as nil, which is exactly
"no parent". `[3]*TreeNode{...}` is a fixed-size array on the stack, so the
inner loop doesn't allocate.

    Time: O(n)    Space: O(n)


================================================================================
APPROACH 2 · DFS returning distance to target (no map)
================================================================================
dfs(node) returns the edge distance from node down to target, or -1. At each
ancestor at distance d, either the ancestor itself is an answer (d == k) or
you collect nodes k - d - 1 levels down its OTHER child.

    Time: O(n)    Space: O(h) recursion — Go's growable goroutine stacks
    handle deep trees far better than CPython's recursion limit (demo below).


================================================================================
STEP BY STEP TRACE · Example 1, target = 5, k = 2
================================================================================
    parent: 5->3, 1->3, 6->5, 2->5, 0->1, 8->1, 7->2, 4->2

    level 0  [5]
    level 1  from 5: Left 6, Right 2, parent 3          -> [6 2 3]
    level 2  from 6: parent 5 seen
             from 2: Left 7, Right 4, parent 5 seen
             from 3: Left 5 seen, Right 1, parent nil   -> [7 4 1]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time   Space   Mutates input?
    ---------------------------  -----  ------  --------------
    Parent map + BFS ✅          O(n)   O(n)    No
    DFS returning distance       O(n)   O(h)    No


================================================================================
EDGE CASES
================================================================================
    k == 0                   [target.Val]
    k > height               Frontier empties; return an empty slice.
    target is the root       parent[root] reads as nil.
    target is a leaf         Everything comes through parent edges.


================================================================================
COMMON MISTAKES
================================================================================
1. No visited map. The walk returns to target and counts it at distance 2.
   Demo below.

2. Keying by Val instead of *TreeNode. Fine when values are unique, broken
   the moment they aren't. Pointer keys are always correct.

3. Returning a nil slice vs an empty slice. Both have len 0 and range fine;
   they differ only if the caller compares to nil or JSON-encodes ("null" vs
   "[]").

4. Reusing one `next` slice across levels with `next = next[:0]` while
   `level` still aliases it. You'd overwrite the level you're iterating.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Many (target, k) queries?
A: Build the parent map once; each query BFSes only nodes within distance k.
   For pairwise distances use depth + LCA with binary lifting.

Q: Distance <= k?
A: Collect every node seen during the first k levels, plus target.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 236   Lowest Common Ancestor (017)
    LC 2385  Amount of Time for Binary Tree to Be Infected
    LC 1740  Find Distance in a Binary Tree
================================================================================
*/

func distanceK(root, target *TreeNode, k int) []int {
	parent := map[*TreeNode]*TreeNode{}
	stack := []*TreeNode{root}
	for len(stack) > 0 {
		node := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		for _, child := range [2]*TreeNode{node.Left, node.Right} {
			if child != nil {
				parent[child] = node
				stack = append(stack, child)
			}
		}
	}

	level := []*TreeNode{target}
	seen := map[*TreeNode]bool{target: true}
	for d := 0; d < k && len(level) > 0; d++ {
		var next []*TreeNode
		for _, node := range level {
			for _, nb := range [3]*TreeNode{node.Left, node.Right, parent[node]} {
				if nb != nil && !seen[nb] {
					seen[nb] = true
					next = append(next, nb)
				}
			}
		}
		level = next
	}
	out := make([]int, 0, len(level))
	for _, node := range level {
		out = append(out, node.Val)
	}
	return out
}

// distanceKDFS is Approach 2: no parent map, distance returned up the recursion.
func distanceKDFS(root, target *TreeNode, k int) []int {
	out := []int{}
	var collectDown func(node *TreeNode, depth int)
	collectDown = func(node *TreeNode, depth int) {
		if node == nil || depth < 0 {
			return
		}
		if depth == 0 {
			out = append(out, node.Val)
			return
		}
		collectDown(node.Left, depth-1)
		collectDown(node.Right, depth-1)
	}
	var dfs func(node *TreeNode) int
	dfs = func(node *TreeNode) int {
		if node == nil {
			return -1
		}
		if node == target {
			collectDown(node, k)
			return 0
		}
		sides := [2][2]*TreeNode{{node.Left, node.Right}, {node.Right, node.Left}}
		for _, s := range sides {
			if d := dfs(s[0]); d >= 0 {
				dist := d + 1
				if dist == k {
					out = append(out, node.Val)
				} else {
					collectDown(s[1], k-dist-1)
				}
				return dist
			}
		}
		return -1
	}
	dfs(root)
	return out
}

// distanceKNoVisited is mistake 1: BFS over parent edges without a visited set.
func distanceKNoVisited(root, target *TreeNode, k int) []int {
	parent := map[*TreeNode]*TreeNode{}
	stack := []*TreeNode{root}
	for len(stack) > 0 {
		node := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		for _, child := range [2]*TreeNode{node.Left, node.Right} {
			if child != nil {
				parent[child] = node
				stack = append(stack, child)
			}
		}
	}
	level := []*TreeNode{target}
	for d := 0; d < k; d++ {
		var next []*TreeNode
		for _, node := range level {
			for _, nb := range [3]*TreeNode{node.Left, node.Right, parent[node]} {
				if nb != nil {
					next = append(next, nb) // BUG: can walk straight back
				}
			}
		}
		level = next
	}
	out := []int{}
	for _, node := range level {
		out = append(out, node.Val)
	}
	return out
}

// oracleDistances computes distances from target by value over an undirected adjacency list.
func oracleDistances(root, target *TreeNode, k int) []int {
	adj := map[int][]int{}
	stack := []*TreeNode{root}
	for len(stack) > 0 {
		node := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if _, ok := adj[node.Val]; !ok {
			adj[node.Val] = nil
		}
		for _, child := range [2]*TreeNode{node.Left, node.Right} {
			if child != nil {
				adj[node.Val] = append(adj[node.Val], child.Val)
				adj[child.Val] = append(adj[child.Val], node.Val)
				stack = append(stack, child)
			}
		}
	}
	dist := map[int]int{target.Val: 0}
	q := []int{target.Val}
	for len(q) > 0 {
		v := q[0]
		q = q[1:]
		for _, w := range adj[v] {
			if _, ok := dist[w]; !ok {
				dist[w] = dist[v] + 1
				q = append(q, w)
			}
		}
	}
	out := []int{}
	for v, d := range dist {
		if d == k {
			out = append(out, v)
		}
	}
	return out
}

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
		if i < len(values) && values[i] != nil {
			node.Left = &TreeNode{Val: values[i].(int)}
			queue = append(queue, node.Left)
		}
		i++
		if i < len(values) && values[i] != nil {
			node.Right = &TreeNode{Val: values[i].(int)}
			queue = append(queue, node.Right)
		}
		i++
	}
	return root
}

func findNode(root *TreeNode, val int) *TreeNode {
	stack := []*TreeNode{root}
	for len(stack) > 0 {
		node := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		if node == nil {
			continue
		}
		if node.Val == val {
			return node
		}
		stack = append(stack, node.Left, node.Right)
	}
	return nil
}

func randomTree(rng *rand.Rand, n int) []*TreeNode {
	nodes := make([]*TreeNode, n)
	for i := range nodes {
		nodes[i] = &TreeNode{Val: i}
	}
	for i := 1; i < n; i++ {
		for {
			p := nodes[rng.Intn(i)]
			if rng.Intn(2) == 0 {
				if p.Left == nil {
					p.Left = nodes[i]
					break
				}
			} else if p.Right == nil {
				p.Right = nodes[i]
				break
			}
		}
	}
	return nodes
}

func sortedCopy(xs []int) []int {
	c := slices.Clone(xs)
	slices.Sort(c)
	if c == nil {
		c = []int{}
	}
	return c
}

func main() {
	allOK := true
	ex := []interface{}{3, 5, 1, 6, 2, 0, 8, nil, nil, 7, 4}

	fmt.Println("--- correctness: BFS vs DFS ---")
	type testCase struct {
		vals   []interface{}
		target int
		k      int
		want   []int
	}
	cases := []testCase{
		{ex, 5, 2, []int{1, 4, 7}},
		{[]interface{}{1}, 1, 3, []int{}},
		{ex, 5, 0, []int{5}},
		{ex, 7, 3, []int{3, 6}},
		{ex, 3, 1, []int{1, 5}},
		{ex, 8, 4, []int{2, 6}},
		{[]interface{}{0, 1, nil, 3, 2}, 2, 1, []int{1}},
		{ex, 3, 10, []int{}},
	}
	for _, tc := range cases {
		root := buildTree(tc.vals)
		target := findNode(root, tc.target)
		a := sortedCopy(distanceK(root, target, tc.k))
		b := sortedCopy(distanceKDFS(root, target, tc.k))
		ok := slices.Equal(a, tc.want) && slices.Equal(b, tc.want)
		allOK = allOK && ok
		fmt.Printf("%s  target=%d k=%-2d  bfs=%v  dfs=%v  want=%v\n", status(ok), tc.target, tc.k, a, b, tc.want)
	}

	fmt.Println("\n--- randomized cross-check vs adjacency-list oracle (300 trees) ---")
	rng := rand.New(rand.NewSource(863))
	bad := 0
	for trial := 0; trial < 300; trial++ {
		n := 1 + rng.Intn(60)
		nodes := randomTree(rng, n)
		target := nodes[rng.Intn(n)]
		k := rng.Intn(9)
		want := sortedCopy(oracleDistances(nodes[0], target, k))
		if !slices.Equal(sortedCopy(distanceK(nodes[0], target, k)), want) ||
			!slices.Equal(sortedCopy(distanceKDFS(nodes[0], target, k)), want) {
			bad++
		}
	}
	ok := bad == 0
	allOK = allOK && ok
	fmt.Printf("%s  300 random trees: BFS and DFS match the oracle\n", status(ok))

	fmt.Println("\n--- mistake 1 LIVE: no visited set ---")
	root := buildTree(ex)
	target := findNode(root, 5)
	wrong := sortedCopy(distanceKNoVisited(root, target, 2))
	right := sortedCopy(distanceK(root, target, 2))
	ok = !slices.Equal(wrong, right) && slices.Equal(right, []int{1, 4, 7})
	allOK = allOK && ok
	fmt.Printf("%s  target=5 k=2: no-visited returns %v, correct %v\n", status(ok), wrong, right)

	fmt.Println("\n--- deep tree: Go's growable stacks let the recursive DFS finish ---")
	const depth = 200_000
	path := make([]*TreeNode, depth)
	for i := range path {
		path[i] = &TreeNode{Val: i}
	}
	for i := 0; i < depth-1; i++ {
		path[i].Left = path[i+1]
	}
	mid := depth / 2
	a := sortedCopy(distanceK(path[0], path[mid], 5))
	b := sortedCopy(distanceKDFS(path[0], path[mid], 5))
	ok = slices.Equal(a, []int{mid - 5, mid + 5}) && slices.Equal(a, b)
	allOK = allOK && ok
	fmt.Printf("%s  path of %d nodes: BFS %v, recursive DFS %v (CPython's default limit is 1000 frames)\n",
		status(ok), depth, a, b)

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
