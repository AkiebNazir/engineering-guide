package main

/*
================================================================================
LeetCode 297 · Serialize and Deserialize Binary Tree                     [Hard]
https://leetcode.com/problems/serialize-and-deserialize-binary-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Design an algorithm to serialize and deserialize a binary tree. There is no
restriction on how your serialization/deserialization algorithm should work;
you just need to ensure that a binary tree can be serialized to a string, and
this string can be deserialized back to the original tree structure.


EXAMPLES
--------
Example 1:
    Input:  root = [1,2,3,null,null,4,5]
    Output: [1,2,3,null,null,4,5]
    (deserialize(serialize(root)) reconstructs an identical tree)

Example 2:
    Input:  root = []
    Output: []


CONSTRAINTS
-----------
    The number of nodes is in the range [0, 10^4].
    -1000 <= Node.Val <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Preorder traversal, with an explicit marker written for every nil child,
uniquely determines the tree's shape. Without null markers, preorder alone
is ambiguous — you can't tell where one subtree ends and the next begins.
With them, decoding is a straightforward recursive consume: the FIRST
unconsumed token is always "what comes next," because preorder visits a
node before either of its subtrees.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. String building: use strings.Builder (topic 1 Part 2.6), not repeated
   string concatenation with `+=` — the latter reallocates on every append
   for a string of growing length, O(n^2) total instead of amortized O(n).

2. Decoding needs a single SHARED CURSOR into the token stream that every
   recursive call both reads and advances — Go has no dict.pop / tuple-
   return-of-many-things idiom to lean on here, so (same as problem 016) the
   idiomatic answer is a closure capturing an index variable by reference,
   pre-declared with `var decode func() *TreeNode` before assignment.

3. `strings.Split(data, ",")` on a trailing-comma-terminated string produces
   a spurious empty final token — trim the trailing separator first, or
   filter it out, or you'll try to strconv.Atoi("") and get an error you
   have to handle.


PROGRESSIVE HINTS
-----------------
Hint 1: Serialize: preorder traversal (root, left, right), writing a
        sentinel string (e.g. "#") for every nil child instead of skipping it.

Hint 2: Deserialize: split the string back into tokens, then walk them with
        a single shared index — read the current token, advance the index,
        recurse into left THEN right (mirroring the write order exactly).

Hint 3: A token equal to the sentinel means "this subtree is empty" — return
        nil and let the caller continue from the advanced index.


COMPLEXITY TARGET
-----------------
    Time:  O(n) for both serialize and deserialize
    Space: O(n) for the string / token slice
================================================================================
*/

// TreeNode mirrors the topic guide's shape; each package redeclares it.
type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// Codec is the stub type you attempt. YourSerialize / YourDeserialize are
// its methods (LeetCode names this class Codec with serialize/deserialize).
type Codec struct{}

// YourConstructor is your attempt's constructor.
func YourConstructor() Codec {
	return Codec{}
}

// YourSerialize is your attempt.
// Implement it, then run:
//
//	cd GoDSA && go run ./10_trees/019_serialize_and_deserialize_binary_tree
func (c *Codec) YourSerialize(root *TreeNode) string {
	// YOUR CODE HERE
	return ""
}

// YourDeserialize is your attempt.
func (c *Codec) YourDeserialize(data string) *TreeNode {
	// YOUR CODE HERE
	return nil
}
