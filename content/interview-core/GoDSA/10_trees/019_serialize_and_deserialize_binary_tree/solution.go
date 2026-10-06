package main

import (
	"fmt"
	"strconv"
	"strings"
)

/*
================================================================================
SOLUTION · LeetCode 297 · Serialize and Deserialize Binary Tree           [Hard]
https://leetcode.com/problems/serialize-and-deserialize-binary-tree/
================================================================================

THE CORE IDEA
--------------
Preorder traversal, with an explicit marker written for every nil child,
uniquely determines the tree's shape:

    preorder = [ROOT] [.... left subtree ....] [.... right subtree ....]

If every nil child ALSO writes a token (instead of being skipped), the
decoder always knows exactly where one subtree ends: it ends the instant a
nil marker is consumed for a branch, with no ambiguity about how many more
tokens belong to the left side versus the right side. Without null markers,
preorder alone cannot distinguish, say, "a right-only chain of 3 nodes" from
"a left-only chain of 3 nodes" — both serialize to the same three values in
the same order.

    serialize: preorder(node), writing "#" for every nil.
    deserialize: consume tokens in the exact order they were written, using
                 a SINGLE SHARED CURSOR that advances with every token read.


================================================================================
⚠️  THE GO-SPECIFIC WRINKLE — no tuple return, so decode needs a closure
================================================================================
Python threads the shared index either via a class attribute, a mutable
default argument trick, or (most simply) a nested function closing over an
`itertools`/iterator object that advances as you call next() on it — there's
no dict.pop / tuple-unpack idiom that hands you "value AND updated position"
in one expression the way Go might make you reach for otherwise. The
idiomatic Go answer is the SAME closure pattern the topic guide's own Part 7
demonstrates and problem 016 reuses:

    tokens := strings.Split(strings.TrimRight(data, ","), ",")
    i := 0
    var decode func() *TreeNode
    decode = func() *TreeNode {
        if tokens[i] == nullMarker {
            i++
            return nil
        }
        val, _ := strconv.Atoi(tokens[i])
        i++
        node := &TreeNode{Val: val}
        node.Left = decode()   // consumes the next run of tokens...
        node.Right = decode()  // ...before this call starts consuming
        return node
    }

`var decode func() *TreeNode` must be pre-declared before the assignment —
a closure literal that calls itself needs its own name already in scope,
same requirement as the topic guide §3.2 diameter closure and problem 016's
cursor closure. The closure captures `i` and `tokens` BY REFERENCE, so
`decode()`'s two recursive calls (Left then Right) see and advance the same
shared index without any parameter threading.


================================================================================
APPROACH 1 · BFS-based level-order serialization (an alternative worth naming)
================================================================================
Serialize via BFS (problem 013's skeleton), writing "#" for nil children
without expanding them further; deserialize by rebuilding level by level
with a queue of "pending parent slots" to fill.

    Time:  O(n)    Space: O(n) for the token list + O(w) for the queue

Produces a DIFFERENT (but equally valid) serialized format from preorder —
this is what LeetCode's own reference solution and most production codecs
(e.g. a JSON tree dump) actually use, since it's easier to read by eye
level-by-level. The preorder+cursor version below is the one interviewers
expect you to derive from scratch, because it reuses the same closure/cursor
idiom as several other tree problems and needs no auxiliary queue.


================================================================================
APPROACH 2 · Preorder + null markers + shared-cursor decode ✅ (the answer)
================================================================================
Shown above.


================================================================================
STEP BY STEP · root = [1,2,3,null,null,4,5]
================================================================================
              1
            ┌─┴─┐
            2    3
                ┌─┴─┐
               4     5

    SERIALIZE (preorder, "#" for every nil):
        visit 1 -> write "1,"
          visit 2 -> write "2,"
            visit nil (2.Left)  -> write "#,"
            visit nil (2.Right) -> write "#,"
          visit 3 -> write "3,"
            visit 4 -> write "4,"
              visit nil, nil -> write "#,#,"
            visit 5 -> write "5,"
              visit nil, nil -> write "#,#,"

        result: "1,2,#,#,3,4,#,#,5,#,#,"

    DESERIALIZE (tokens = ["1","2","#","#","3","4","#","#","5","#","#"], i=0):
        decode(): tokens[0]="1" -> node(1), i=1
            node.Left  = decode(): tokens[1]="2" -> node(2), i=2
                .Left  = decode(): tokens[2]="#" -> nil, i=3
                .Right = decode(): tokens[3]="#" -> nil, i=4
                -> node(2), leaf
            node.Right = decode(): tokens[4]="3" -> node(3), i=5
                .Left  = decode(): tokens[5]="4" -> node(4), i=6
                    .Left=decode()="#" nil i=7, .Right=decode()="#" nil i=8
                .Right = decode(): tokens[8]="5" -> node(5), i=9
                    .Left=decode()="#" nil i=10, .Right=decode()="#" nil i=11
                -> node(3, left=4, right=5)
        -> full tree reconstructed, matching the original exactly.

    Both halves proven live below with the exact string produced and a
    structural equality check against the original tree.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time    Space   Mutates input?
    -------------------------------------  ------  ------  ---------------
    BFS level-order serialization          O(n)    O(n)    No
    Preorder + shared-cursor decode    ✅  O(n)    O(n)    No


================================================================================
EDGE CASES
================================================================================
    nil root                -> serializes to "#," alone; deserialize must
                                return nil, not panic on an "empty" input.
    single node [1]          -> "1,#,#,"; round-trips to a lone node.
    left-skewed chain (no right children anywhere) -> still round-trips
                                correctly precisely BECAUSE every nil is
                                marked — without markers this shape would
                                be ambiguous against a right-skewed chain
                                of the same values.
    negative values          -> "-5" parses fine with strconv.Atoi; the
                                separator is "," not "-", so no collision
                                with a leading minus sign.
    values that could collide with the marker as a substring, e.g. a node
                                valued literally 23 vs the marker "#" — no
                                collision possible since "#" is not a valid
                                strconv.Atoi input and is never a legal
                                Node.Val per the constraints; still worth
                                explicitly choosing a marker that can NEVER
                                appear as a legitimate serialized value.


================================================================================
COMMON MISTAKES
================================================================================
1. Splitting on "," without trimming the trailing separator first —
   `strings.Split("1,2,#,#,", ",")` yields a spurious empty string as the
   LAST token, which then fails strconv.Atoi or is mistaken for a real
   token. Trim with strings.TrimRight(data, ",") before splitting, or use
   strings.Fields if the format allows switching to whitespace-separated
   tokens (which sidesteps the empty-trailing-token issue entirely).

2. Skipping nil children instead of writing a marker for them — the classic
   ambiguity: a plain preorder listing of [1,2,3] cannot distinguish "2 is
   1's left child, 3 is 2's right child" from other shapes without markers.

3. Building the serialized string with repeated `+=` instead of
   strings.Builder — correctness is unaffected, but it's O(n^2) time on a
   large tree instead of amortized O(n), and grows the topic 1-style
   allocation cost silently.

4. Forgetting `var decode func() *TreeNode` pre-declaration — attempting
   `decode := func() *TreeNode { ...; decode() ...}` does not compile,
   since `decode` doesn't exist yet on the right-hand side of `:=`.

5. Decoding Right before Left — breaks the cursor exactly the way problem
   016 demonstrates for construct-from-traversal: the shared index is only
   valid if consumption order matches write order exactly.


================================================================================
FOLLOW-UPS
================================================================================
    - Could you serialize with FEWER bytes than one marker per nil? Yes —
      e.g. write only NON-nil node counts per subtree, or use a bitmask of
      structure separately from a compact value stream; a real interview
      follow-up on efficiency, not correctness.
    - Would this work for an N-ary tree? Same idea, but each node needs its
      CHILD COUNT written explicitly (not just left/right presence), since
      fan-out is no longer fixed at 2.
    - Thread-safety / concurrent use of one Codec value: this implementation
      is stateless per call (all state is local to serialize/deserialize),
      so a single Codec value is safe to reuse across goroutines calling it
      concurrently — worth stating explicitly if asked.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 105  Construct Binary Tree from Preorder and Inorder Traversal
             (problem 016, this topic) — same shared-cursor closure idiom
    LC 449  Serialize and Deserialize BST — can drop null markers entirely
             by exploiting BST ordering instead (topic 11)
    LC 428  Serialize and Deserialize N-ary Tree — same idea, child COUNT
             replaces the fixed left/right structure
================================================================================
*/

const nullMarker = "#"

// serialize is the interview answer: preorder traversal, "#" for every nil
// child, built with strings.Builder for amortized O(n) string construction.
func serialize(root *TreeNode) string {
	var sb strings.Builder
	var encode func(*TreeNode)
	encode = func(node *TreeNode) {
		if node == nil {
			sb.WriteString(nullMarker)
			sb.WriteByte(',')
			return
		}
		sb.WriteString(strconv.Itoa(node.Val))
		sb.WriteByte(',')
		encode(node.Left)
		encode(node.Right)
	}
	encode(root)
	return sb.String()
}

// deserialize walks the token stream in the exact order it was written,
// using a single shared cursor closure -- same idiom as problem 016.
func deserialize(data string) *TreeNode {
	trimmed := strings.TrimRight(data, ",")
	if trimmed == "" {
		return nil
	}
	tokens := strings.Split(trimmed, ",")
	i := 0
	var decode func() *TreeNode
	decode = func() *TreeNode {
		if tokens[i] == nullMarker {
			i++
			return nil
		}
		val, _ := strconv.Atoi(tokens[i])
		i++
		node := &TreeNode{Val: val}
		node.Left = decode()
		node.Right = decode()
		return node
	}
	return decode()
}

// serializeBFS is the alternative level-order format most real codecs use.
func serializeBFS(root *TreeNode) string {
	if root == nil {
		return nullMarker + ","
	}
	var sb strings.Builder
	queue := []*TreeNode{root}
	for len(queue) > 0 {
		node := queue[0]
		queue = queue[1:]
		if node == nil {
			sb.WriteString(nullMarker)
			sb.WriteByte(',')
			continue
		}
		sb.WriteString(strconv.Itoa(node.Val))
		sb.WriteByte(',')
		queue = append(queue, node.Left, node.Right)
	}
	return sb.String()
}

// deserializeBFS reconstructs from serializeBFS's level-order format using a
// queue of "pending parent slots" to fill left-to-right.
func deserializeBFS(data string) *TreeNode {
	trimmed := strings.TrimRight(data, ",")
	if trimmed == "" || trimmed == nullMarker {
		return nil
	}
	tokens := strings.Split(trimmed, ",")
	rootVal, _ := strconv.Atoi(tokens[0])
	root := &TreeNode{Val: rootVal}
	queue := []*TreeNode{root}
	i := 1
	for len(queue) > 0 && i < len(tokens) {
		node := queue[0]
		queue = queue[1:]
		if tokens[i] != nullMarker {
			v, _ := strconv.Atoi(tokens[i])
			node.Left = &TreeNode{Val: v}
			queue = append(queue, node.Left)
		}
		i++
		if i >= len(tokens) {
			break
		}
		if tokens[i] != nullMarker {
			v, _ := strconv.Atoi(tokens[i])
			node.Right = &TreeNode{Val: v}
			queue = append(queue, node.Right)
		}
		i++
	}
	return root
}

func sameShape(a, b *TreeNode) bool {
	if a == nil || b == nil {
		return a == b
	}
	return a.Val == b.Val && sameShape(a.Left, b.Left) && sameShape(a.Right, b.Right)
}

func main() {
	// [1,2,3,null,null,4,5]
	t1 := &TreeNode{
		Val:  1,
		Left: &TreeNode{Val: 2},
		Right: &TreeNode{
			Val:   3,
			Left:  &TreeNode{Val: 4},
			Right: &TreeNode{Val: 5},
		},
	}

	// left-skewed chain: 1 -> 2 -> 3, no right children at all
	skewed := &TreeNode{Val: 1, Left: &TreeNode{Val: 2, Left: &TreeNode{Val: 3}}}

	// negative values
	neg := &TreeNode{Val: -5, Left: &TreeNode{Val: -3}, Right: &TreeNode{Val: -10}}

	type testCase struct {
		name string
		root *TreeNode
	}
	cases := []testCase{
		{"LC example 1", t1},
		{"nil root", nil},
		{"single node [1]", &TreeNode{Val: 1}},
		{"left-skewed chain (no right children)", skewed},
		{"negative values", neg},
	}

	allOK := true
	for _, tc := range cases {
		s := serialize(tc.root)
		reconstructed := deserialize(s)
		ok := sameShape(tc.root, reconstructed)

		sBFS := serializeBFS(tc.root)
		reconstructedBFS := deserializeBFS(sBFS)
		okBFS := sameShape(tc.root, reconstructedBFS)

		ok = ok && okBFS
		allOK = allOK && ok
		fmt.Printf("%s  %-40s preorder=%-24q BFS=%q\n", status(ok), tc.name, s, sBFS)
	}

	fmt.Println("\n--- live trace: LC example 1, [1,2,3,null,null,4,5] ---")
	s := serialize(t1)
	fmt.Printf("    serialize(root)   -> %q\n", s)
	back := deserialize(s)
	fmt.Printf("    deserialize(data) round-trips to structurally identical tree: %v\n", sameShape(t1, back))

	fmt.Println("\n--- why the trailing-comma trim matters ---")
	raw := "1,2,#,#,"
	naive := strings.Split(raw, ",")
	trimmedTokens := strings.Split(strings.TrimRight(raw, ","), ",")
	fmt.Printf("    strings.Split(%q, \",\")                -> %q  (len=%d, spurious empty tail)\n", raw, naive, len(naive))
	fmt.Printf("    strings.Split(TrimRight(%q,\",\"), \",\") -> %q  (len=%d, clean)\n", raw, trimmedTokens, len(trimmedTokens))

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
