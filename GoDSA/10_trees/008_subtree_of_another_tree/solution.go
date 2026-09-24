package main

import (
	"fmt"
	"strconv"
	"strings"
	"time"
)

/*
================================================================================
SOLUTION · LeetCode 572 · Subtree of Another Tree                        [Easy]
https://leetcode.com/problems/subtree-of-another-tree/
================================================================================

THE CORE IDEA
-------------
"Subtree" means a node plus ALL its descendants, so the question is "is
there a node of `root` from which the two trees are IDENTICAL" — that's
007's `isSameTree`, called at every node of `root`:

    func isSubtree(root, subRoot *TreeNode) bool {
        if root == nil {
            return subRoot == nil
        }
        if isSameTree(root, subRoot) {
            return true
        }
        return isSubtree(root.Left, subRoot) || isSubtree(root.Right, subRoot)
    }

O(n*m) worst case — one O(m) isSameTree call at (up to) every one of `root`'s
n nodes. O(h) space. This is COMPOSITION: the whole content of the problem
is recognizing you already built the hard half in 007.

The alternative is to make it a STRING problem: serialize both trees and
ask whether one string contains the other.

    return strings.Contains(encode(root), encode(subRoot))

O(n+m)-ish with Go's stdlib substring search — but it is a false-positive
factory if the encoding is careless. Two real failures, both measured live
below:

    (a) NO NULL MARKERS. Encode preorder values only:
            root = [1,2]        (1 with a LEFT child 2)   -> "1,2"
            sub  = [1,null,2]   (1 with a RIGHT child 2)  -> "1,2"
        "1,2" contains "1,2" — true, but sub is NOT a subtree of root.
        Without markers the encoding isn't injective.

    (b) MARKERS BUT NO DELIMITER BEFORE EACH VALUE. Encode with "#" for nil
        and nothing between values:
            root = [12]  -> "12##"
            sub  = [2]   -> "2##"
        "12##" contains "2##" — the match starts INSIDE the digits of 12.

    Fix both: a null marker for every empty child AND a delimiter in front
    of every value, so no token can begin mid-token:
            encode(nil)  = ",#"
            encode(node) = ",{val}" + encode(left) + encode(right)
    Now root=[12] gives ",12,#,#" and sub=[2] gives ",2,#,#", not a
    substring of it.

================================================================================
APPROACHES
================================================================================
Approach 0 (WRONG): check that every value of `subRoot` appears somewhere
   in `root`, or that `subRoot`'s preorder is a sub-LIST of `root`'s
   preorder. Both ignore "and all its descendants" and the shape. Fails on
   Example 2, where node 4's subtree merely has one extra descendant.

Approach 1 (composition: isSameTree at every node) ✅ — the shape above.
   O(n*m) worst case, O(h) space. Lead with this: short, obviously correct,
   reuses 007.

Approach 2 (serialize + `strings.Contains`) ✅ — O(n+m)-ish time and space
   with `strings.Builder` (no O(n^2) concatenation) and a proper encoding.
   Give it when asked to beat O(n*m); volunteer the delimiter/marker
   pitfall — that's what distinguishes "implemented it" from "heard of it."

Approach 3 (prune by value before comparing) — only call isSameTree at
   nodes whose value equals subRoot.Val. Same O(n*m) worst case (a tree of
   identical values defeats it), but a large constant-factor win on real
   inputs. Measured below.

Approach 4 (Merkle-style subtree hashing) — hash each subtree bottom-up as
   hash(val, leftHash, rightHash), compare subRoot's hash against every
   node's. O(n+m) expected, no string building — but it's a probabilistic
   answer unless a hit is verified with a real isSameTree call (hash
   collisions are possible, if rare).

================================================================================
STEP BY STEP TRACE — root = [3,4,5,1,2], subRoot = [4,1,2]
================================================================================
            3                      4
          /   \                  /   \
         4     5                1     2
        / \
       1   2

    isSubtree(3, sub)
      isSameTree(3, 4) -> false (3 != 4)
      isSubtree(4, sub)
        isSameTree(4, 4): vals equal
          isSameTree(1,1) -> true
          isSameTree(2,2) -> true
          -> true                       <- found it, || short-circuits
      -> true

    Example 2, node 2 has an extra child 0:
    isSubtree(4, sub)
      isSameTree(4, 4)
        isSameTree(1, 1) -> true
        isSameTree(2, 2)
          vals equal, isSameTree(0, nil) -> false (one side empty)
          -> false
        -> false
      isSubtree(1, sub) -> ... false
      isSubtree(2, sub) -> ... false
      -> false

    The line that makes Example 2 come out false is the nil-mismatch check
    inside isSameTree — "all its descendants" is enforced by STRUCTURE, not
    by anything special in this file.

    String route on [12] vs [2]:
        markers only    : "12##" contains "2##"     -> true  (WRONG)
        markers+delim   : ",12,#,#" contains ",2,#,#" -> false (correct)

================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time         Space   Mutates?  Note
    -------------------------------  -----------  ------  --------  ---------------------
    Values/sublist matching         O(n+m)       O(n+m)  no        WRONG ANSWER
    isSameTree at every node ✅    O(n*m)       O(h)    no        the answer
    + prune on root.Val==sub.Val    O(n*m)       O(h)    no        same bound, big
                                                                     constant-factor win
    Serialize + strings.Contains ✅ O(n+m)-ish   O(n+m)  no        needs markers AND
                                                                     delimiters
    Merkle / subtree hashing        O(n+m)       O(n)    no        probabilistic unless
                                                                     verified

    The O(n*m) worst case is real: `root` a chain of 2000 nodes all valued
    1, `subRoot` a chain of 1000 nodes all valued 1 plus one extra child at
    the bottom. Every node of `root` looks like a match for 999 comparisons
    before failing. Measured below.

================================================================================
EDGE CASES
================================================================================
    subRoot == nil            -> true by convention (empty tree is a
                               subtree of anything); LeetCode guarantees
                               subRoot has >= 1 node, so this never fires on
                               the judge, but the code must not crash if it
                               does. `if root == nil { return subRoot ==
                               nil }` covers both ends.
    root == nil, subRoot != nil -> false.
    root == subRoot (same tree)  -> true; a tree is a subtree of itself.
    [1,1] with subRoot [1]        -> true, matched at the CHILD, not the
                               root. Only checking the root misses this;
                               forgetting to check the root at all also
                               fails ([1,1] IS also a subtree match on root).
    [12] with subRoot [2]         -> false. THE test case for the string
                               route without a delimiter.
    [1,2] vs [1,null,2]           -> false. The other string-route test case.
    all values identical           -> the O(n*m) worst case; value pruning
                               stops helping here too.
    subtree present twice          -> true; the || returns at the first hit.

================================================================================
COMMON MISTAKES
================================================================================
1. Matching a PATTERN rather than a whole subtree — accepting Example 2
   because "[4,1,2] is in there somewhere." "Subtree" includes every
   descendant.
2. Writing `isSameTree(root, subRoot) || isSubtree(...)` but forgetting the
   `root == nil` base case first — a nil root then reaches isSameTree and
   isSubtree's recursive calls read `root.Left`/`root.Right`, PANICKING on
   the nil pointer dereference.
3. `if root == nil { return false }` instead of `return subRoot == nil` —
   technically survives LeetCode's constraint that subRoot has >= 1 node,
   but is wrong in general; say the convention out loud.
4. Serializing WITHOUT null markers and using substring search — false
   positives (demo (a) below).
5. Serializing with markers but WITHOUT a delimiter before each value —
   "2" matches inside "12" (demo (b) below); multi-digit and negative
   values make this fire on ordinary inputs.
6. Building the serialization with `s += ...` inside the recursion in a
   loop over many nodes — O(n^2) string copying, silently destroying the
   O(n+m) claim. Use `strings.Builder` and write once.
7. Claiming O(n+m) for the string route without acknowledging Go's
   `strings.Contains` implementation detail — it's fast in the standard
   library (not a naive O(n*m) scan), but naming the underlying algorithm
   (Rabin-Karp / a tuned variant) if pressed shows real understanding.

================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do better than O(n*m)?
A: Yes — serialize both trees with null markers and delimiters, then
   `strings.Contains`. O(n+m)-ish. Immediately mention the false-positive
   pitfalls, since that's the part that goes wrong in practice.

Q: Why does the naive serialization fail?
A: It isn't injective: two different trees can encode identically ([1,2]
   vs [1,null,2]), and a token can start mid-token ([2] inside [12]).
   Markers fix the first, delimiters the second.

Q: Avoid building strings entirely?
A: Merkle-style subtree hashing: hash each subtree bottom-up, compare
   subRoot's hash against every node's. O(n+m) expected; verify a hit with
   a real isSameTree call to make the answer exact rather than probabilistic.

Q: What if you must answer many queries against the same `root`?
A: Precompute the serialization (or a hash-to-nodes map) once in O(n), then
   each query costs O(m) — the case where the string route clearly wins.

================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    LC 100   Same Tree                    — the subroutine (007)
    LC 101   Symmetric Tree               — crossed pairing, not this problem's shape
    LC 297   Serialize and Deserialize    — the lossless encoding, standalone (019)
    LC 652   Find Duplicate Subtrees      — serialize every subtree into a map
================================================================================
*/

// isSameTree is problem 007's answer, reused verbatim as the subroutine.
func isSameTree(p, q *TreeNode) bool {
	if p == nil && q == nil {
		return true
	}
	if p == nil || q == nil {
		return false
	}
	if p.Val != q.Val {
		return false
	}
	return isSameTree(p.Left, q.Left) && isSameTree(p.Right, q.Right)
}

// isSubtree is the interview answer: isSameTree at every node of root.
func isSubtree(root, subRoot *TreeNode) bool {
	if root == nil {
		return subRoot == nil
	}
	if isSameTree(root, subRoot) {
		return true
	}
	return isSubtree(root.Left, subRoot) || isSubtree(root.Right, subRoot)
}

// isSubtreePruned only compares where the root values already agree.
func isSubtreePruned(root, subRoot *TreeNode) bool {
	if subRoot == nil {
		return true
	}
	if root == nil {
		return false
	}
	if root.Val == subRoot.Val && isSameTree(root, subRoot) {
		return true
	}
	return isSubtreePruned(root.Left, subRoot) || isSubtreePruned(root.Right, subRoot)
}

// encode serializes preorder with a "#" null marker and a "," delimiter
// BEFORE every value, using strings.Builder to avoid O(n^2) concatenation.
func encode(node *TreeNode) string {
	var sb strings.Builder
	var walk func(*TreeNode)
	walk = func(n *TreeNode) {
		if n == nil {
			sb.WriteString(",#")
			return
		}
		sb.WriteByte(',')
		sb.WriteString(strconv.Itoa(n.Val))
		walk(n.Left)
		walk(n.Right)
	}
	walk(node)
	return sb.String()
}

// isSubtreeSerialized: encode both, substring search. O(n+m)-ish.
func isSubtreeSerialized(root, subRoot *TreeNode) bool {
	return strings.Contains(encode(root), encode(subRoot))
}

// encodeNoMarkers is BROKEN ON PURPOSE — no null marker, so the encoding is
// not injective.
func encodeNoMarkers(node *TreeNode) string {
	var sb strings.Builder
	var walk func(*TreeNode)
	walk = func(n *TreeNode) {
		if n == nil {
			return
		}
		sb.WriteByte(',')
		sb.WriteString(strconv.Itoa(n.Val))
		walk(n.Left)
		walk(n.Right)
	}
	walk(node)
	return sb.String()
}

// encodeNoDelimiter is BROKEN ON PURPOSE — markers but no delimiter before
// each value, so a match can begin mid-digit.
func encodeNoDelimiter(node *TreeNode) string {
	var sb strings.Builder
	var walk func(*TreeNode)
	walk = func(n *TreeNode) {
		if n == nil {
			sb.WriteString("#")
			return
		}
		sb.WriteString(strconv.Itoa(n.Val))
		walk(n.Left)
		walk(n.Right)
	}
	walk(node)
	return sb.String()
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

// buildChain builds a chain of n nodes all valued `val`, linked through
// .Left, so every node's subtree "looks the same" until the very bottom.
func buildChain(n, val int, poison bool) *TreeNode {
	if n == 0 {
		return nil
	}
	root := &TreeNode{Val: val}
	curr := root
	for i := 1; i < n; i++ {
		node := &TreeNode{Val: val}
		curr.Left = node
		curr = node
	}
	if poison {
		curr.Right = &TreeNode{Val: val} // extra node so it never matches
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
		root, sub []interface{}
		want      bool
	}
	cases := []testCase{
		{[]interface{}{3, 4, 5, 1, 2}, []interface{}{4, 1, 2}, true},
		{[]interface{}{3, 4, 5, 1, 2, nil, nil, nil, nil, 0}, []interface{}{4, 1, 2}, false},
		{[]interface{}{1, 1}, []interface{}{1}, true},
		{[]interface{}{1}, []interface{}{1}, true},
		{[]interface{}{1, 2}, []interface{}{1, nil, 2}, false},
		{[]interface{}{12}, []interface{}{2}, false},
	}

	allOK := true

	fmt.Println("--- correctness: composition (isSameTree at every node) ---")
	for _, tc := range cases {
		got := isSubtree(buildTree(tc.root), buildTree(tc.sub))
		ok := got == tc.want
		allOK = allOK && ok
		fmt.Printf("%s  root=%v sub=%v -> %v (want %v)\n", status(ok), tc.root, tc.sub, got, tc.want)
	}

	fmt.Println("\n--- correctness: pruned and serialized variants ---")
	impls := []struct {
		name string
		fn   func(*TreeNode, *TreeNode) bool
	}{
		{"pruned on root.Val", isSubtreePruned},
		{"serialized+Contains", isSubtreeSerialized},
	}
	for _, impl := range impls {
		ok := true
		for _, tc := range cases {
			if impl.fn(buildTree(tc.root), buildTree(tc.sub)) != tc.want {
				ok = false
			}
		}
		allOK = allOK && ok
		fmt.Printf("%s  %s (%d cases)\n", status(ok), impl.name, len(cases))
	}

	// False positive (a): no null markers.
	fmt.Println("\n--- live demo (a): serializing WITHOUT null markers ---")
	root, sub := buildTree([]interface{}{1, 2}), buildTree([]interface{}{1, nil, 2})
	fmt.Printf("  root = [1,2] (1 with a LEFT child 2)   sub = [1,null,2] (1 with a RIGHT child 2)\n")
	fmt.Printf("  encodeNoMarkers(root) = %q\n", encodeNoMarkers(root))
	fmt.Printf("  encodeNoMarkers(sub)  = %q\n", encodeNoMarkers(sub))
	fpA := strings.Contains(encodeNoMarkers(root), encodeNoMarkers(sub))
	truthA := isSubtree(root, sub)
	fmt.Printf("  substring test -> %v   <- FALSE POSITIVE\n", fpA)
	fmt.Printf("  the truth      -> %v\n", truthA)
	fmt.Printf("  with markers+delimiters -> %v\n", isSubtreeSerialized(root, sub))
	allOK = allOK && fpA && !truthA && !isSubtreeSerialized(root, sub)

	// False positive (b): markers but no delimiter.
	fmt.Println("\n--- live demo (b): null markers but NO delimiter before values ---")
	root, sub = buildTree([]interface{}{12}), buildTree([]interface{}{2})
	fmt.Printf("  root = [12]   sub = [2]\n")
	fmt.Printf("  encodeNoDelimiter(root) = %q\n", encodeNoDelimiter(root))
	fmt.Printf("  encodeNoDelimiter(sub)  = %q\n", encodeNoDelimiter(sub))
	fpB := strings.Contains(encodeNoDelimiter(root), encodeNoDelimiter(sub))
	truthB := isSubtree(root, sub)
	fmt.Printf("  substring test -> %v   <- FALSE POSITIVE (match starts inside '12')\n", fpB)
	fmt.Printf("  the truth      -> %v\n", truthB)
	fmt.Printf("  with a delimiter -> %v\n", isSubtreeSerialized(root, sub))
	allOK = allOK && fpB && !truthB && !isSubtreeSerialized(root, sub)

	// Measured: the O(n*m) worst case, built on purpose.
	fmt.Println("\n--- measured: the O(n*m) worst case (composition) vs O(n+m) (serialized) ---")
	root = buildChain(2000, 1, false)
	sub = buildChain(1000, 1, true) // poisoned: never actually matches
	t0 := time.Now()
	compResult := isSubtree(root, sub)
	compElapsed := time.Since(t0)
	t0 = time.Now()
	serResult := isSubtreeSerialized(root, sub)
	serElapsed := time.Since(t0)
	fmt.Printf("  root = chain of 2000 nodes, all valued 1\n")
	fmt.Printf("  sub  = chain of 1000 nodes, all valued 1, plus one extra child (never matches)\n")
	fmt.Printf("  composition  -> %-5v  %v\n", compResult, compElapsed)
	fmt.Printf("  serialized   -> %-5v  %v\n", serResult, serElapsed)
	if serElapsed > 0 {
		fmt.Printf("  composition / serialized = %.0fx\n", float64(compElapsed)/float64(serElapsed))
	}
	fmt.Println("  Every value is 1, so pruning on root.Val==sub.Val would prune nothing here —")
	fmt.Println("  the string route is the real fix for this adversarial shape.")
	allOK = allOK && !compResult && !serResult

	if allOK {
		fmt.Println("\nALL PASSED")
	} else {
		fmt.Println("\nFAILURES PRESENT")
	}
}
