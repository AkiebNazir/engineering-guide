# Topic 11 · Binary Search Tree — Go Deep Dive

> Every other language you might come from hands you a balanced ordered
> container for free — C++ `std::map`, Java `TreeMap`, Python's third-party
> `sortedcontainers.SortedList`. Go hands you nothing. The standard library has
> no ordered map, no built-in BST, no balanced tree of any kind. If a problem
> wants "sorted order plus O(log n) insert/delete/search," you are building it
> yourself. This document is that build, plus the traversal and invariant
> reasoning that makes it correct.

---

## Part 1 · The Gap: Go Has No Ordered Container

### 1.1 State it plainly, because it will surprise you mid-interview

```
C++     std::map, std::set              → red-black tree, O(log n), sorted iteration
Java    TreeMap, TreeSet                → red-black tree, O(log n), sorted iteration
Python  sortedcontainers.SortedList     → list-of-sqrt(n)-blocks, O(log n) amortized
Go      ???                             → nothing in the standard library
```

Go's `container/` package ships a doubly linked list (`container/list`), a
heap interface (`container/heap`), and a ring buffer (`container/ring`) —
**no ordered tree**. `map[K]V` gives you O(1) average lookup but **zero
ordering guarantees** (topic 1, Part 2.3: iteration order is randomized).
There is no `sortedcontainers` equivalent in std, either.

> ⚠️ **This is the single most common "wait, what?" moment for engineers
> moving from Python/C++/Java to Go on tree problems.** If you need
> predecessor/successor/rank/sorted-range queries, you either hand-roll a BST
> (this document), reach for a third-party B-tree package
> (`github.com/google/btree`, `github.com/tidwall/btree`), or fall back to sorting a slice
> from scratch every time you need order — which is O(n log n) per rebuild,
> not O(log n) per operation. Know this gap exists before you're in a live
> interview reaching for a `TreeMap` that doesn't exist.

### 1.2 What you get instead

You get pointers and structs — which is actually enough, because a BST is
just a binary tree with an ordering invariant enforced on insert. Go's struct
+ pointer model (topic 8) makes hand-rolling one direct and fast:

```go
type TreeNode struct {
    Val         int
    Left, Right *TreeNode
}
```

No generics headache required for `int`-keyed problems (which is most of
LeetCode); a real production BST would parametrize on `cmp func(a, b K) int`
the way `slices.SortFunc` does (Go 1.21+ generics), but LeetCode-style
problems almost always fix the key type, so this guide does too, then notes
the generic variant at the end.

---

## Part 2 · The BST Invariant and What It Buys You

### 2.1 The invariant

For every node `n`: every value in `n.Left`'s subtree is `< n.Val`, and every
value in `n.Right`'s subtree is `> n.Val` (or `>=` if you allow duplicates —
pick a convention and hold it consistently, since insert/delete must agree).

```
          8
        /   \
       3     10
      / \      \
     1   6      14
        / \     /
       4   7   13
```

### 2.2 In-order traversal yields sorted output — this is not a coincidence

In-order = (visit left subtree, visit node, visit right subtree). Because the
invariant guarantees everything in `Left` is smaller and everything in
`Right` is larger, recursively applying that guarantee at every node means
in-order visits values in strictly increasing sequence:

```go
func inOrder(n *TreeNode, out *[]int) {
    if n == nil {
        return
    }
    inOrder(n.Left, out)
    *out = append(*out, n.Val)   // visit AFTER left, BEFORE right
    inOrder(n.Right, out)
}
```

For the tree above: `1 3 4 6 7 8 10 13 14`. This single fact underlies half
the BST problems on LeetCode: "kth smallest," "validate BST," "BST to sorted
list," "closest value" — all reduce to walking, or reasoning about, in-order
sequence.

### 2.3 Validating a BST: the range trap

The naive, **wrong** approach: check only `node.Left.Val < node.Val <
node.Right.Val` at each node. This misses violations from grandchildren:

```
       5
      / \
     1   8
        / \
       4   9      ← 4 < 8 passes locally, but 4 must be > 5. INVALID tree.
```

The correct approach threads a valid `(low, high)` range down through
recursion, tightening it at every step:

```go
func isValidBST(root *TreeNode) bool {
    var valid func(n *TreeNode, low, high *int) bool
    valid = func(n *TreeNode, low, high *int) bool {
        if n == nil {
            return true
        }
        if low != nil && n.Val <= *low {
            return false
        }
        if high != nil && n.Val >= *high {
            return false
        }
        return valid(n.Left, low, &n.Val) && valid(n.Right, &n.Val, high)
    }
    return valid(root, nil, nil)
}
```

> ⚠️ Using `*int` for `low`/`high` (rather than sentinel values like
> `math.MinInt`/`math.MaxInt`) sidesteps the edge case where the tree
> legitimately contains `math.MinInt64` or `math.MaxInt64` — a sentinel value
> collision is a real bug LeetCode's test cases will catch. Nil-able pointers
> for "no bound yet" are the robust idiom here.

The equivalent "check in-order is strictly increasing" approach works too and
is arguably simpler to reason about — track `prev *TreeNode` across in-order
recursion and compare each visited value against it. Either is acceptable;
know both because interviewers sometimes ask for the second after you give
the first.

---

## Part 3 · Insert, Search, Delete

### 3.1 Search and insert — recursive and iterative, both idiomatic in Go

```go
func search(n *TreeNode, target int) *TreeNode {
    for n != nil && n.Val != target {
        if target < n.Val {
            n = n.Left
        } else {
            n = n.Right
        }
    }
    return n   // nil if not found
}

func insert(n *TreeNode, val int) *TreeNode {
    if n == nil {
        return &TreeNode{Val: val}
    }
    if val < n.Val {
        n.Left = insert(n.Left, val)
    } else if val > n.Val {
        n.Right = insert(n.Right, val)
    }
    return n   // duplicates: no-op; adjust if your problem allows them
}
```

The recursive insert's "return the (possibly new) subtree root and reassign
it into the parent's child pointer" pattern is the idiomatic Go way to
mutate a tree by value-of-pointer without needing `**TreeNode` — it reads
cleanly and is what you'll reach for 90% of the time.

### 3.2 Delete — the three cases

Deleting node `n` with value `target`:

1. **Leaf** (no children): detach it — parent's pointer to it becomes `nil`.
2. **One child**: splice it out — parent points directly to `n`'s single child.
3. **Two children**: cannot just detach — you'd orphan a whole subtree. Find
   `n`'s **in-order successor** (the smallest value in `n.Right`, i.e. walk
   `Right` then `Left` all the way down), copy that value into `n`, then
   recursively delete the successor from `n.Right` (which is now guaranteed
   to be a case-1-or-2 delete, since the successor has no left child by
   construction).

```
Delete 8:                    successor = 9 (min of right subtree)
       8                          9
      / \                        / \
     3   10        becomes      3   10
        /  \                       /  \
       9    14                   nil   14
```

```go
func deleteNode(n *TreeNode, target int) *TreeNode {
    if n == nil {
        return nil
    }
    switch {
    case target < n.Val:
        n.Left = deleteNode(n.Left, target)
    case target > n.Val:
        n.Right = deleteNode(n.Right, target)
    default:
        // found it — handle the three cases
        if n.Left == nil {
            return n.Right   // covers "leaf" (both nil) and "one right child"
        }
        if n.Right == nil {
            return n.Left    // "one left child"
        }
        // two children: splice in the in-order successor's value
        succ := n.Right
        for succ.Left != nil {
            succ = succ.Left
        }
        n.Val = succ.Val
        n.Right = deleteNode(n.Right, succ.Val)   // remove the now-duplicated successor
    }
    return n
}
```

> ✅ Using the in-order **predecessor** (max of `Left`) instead of the
> successor is equally correct — pick either, but be consistent, and say out
> loud in an interview which one you're using and why it's safe (it has at
> most one child, so its own deletion is trivially case 1 or 2).

---

## Part 4 · Balance — Why This All Falls Apart Without It

### 4.1 The degenerate case

Insert `1, 2, 3, 4, 5, 6, 7` in order into an empty BST using the insert
above. Every value is larger than the last, so every node becomes the
previous node's right child:

```
1
 \
  2
   \
    3
     \
      4     ← this is just a linked list wearing a tree costume
```

Search/insert/delete degrade from the hoped-for O(log n) to **O(n)** — you've
built an expensive linked list. This is precisely why real-world ordered
containers (C++ `std::map`, Java `TreeMap`) are red-black trees, not plain
BSTs: they perform **rotations** after insert/delete to bound height at
O(log n) regardless of insertion order.

### 4.2 Self-balancing, conceptually

A rotation re-parents a small number of nodes to reduce height while
preserving the BST invariant:

```
Right rotation around y:        Left rotation around x:
    y                x               x                    y
   / \              / \             / \                  / \
  x   C    ──►     A   y           A   y      ──►        x   C
 / \                  / \             / \                / \
A   B                B   C           B   C              A   B
```

AVL trees rotate to keep left/right subtree heights within 1 of each other
at every node; red-black trees use a color invariant plus rotations to keep
the longest root-to-leaf path at most 2x the shortest. Both guarantee
**O(log n)** worst case, not just average.

> ⚠️ Go's `container/` package deliberately ships none of this. If your
> production code genuinely needs a balanced ordered map, use
> `github.com/google/btree` (a B-tree, not a binary tree, but same asymptotic
> guarantees and better cache behavior) rather than hand-rolling AVL
> rotations — reserve rotation logic for interview prep, not production.

For interview purposes: know that a plain BST is only O(log n) **if the
input happens to arrive in a reasonably balanced order** (or you explicitly
balance it, e.g. building from a sorted array via repeated midpoint — see
"Convert Sorted Array to BST," LC 108), and say so when asked about worst
case.

### 4.3 Red-black rebalancing, in full — the mechanism behind those rotations

§4.2 shows *that* rotations fix height; here is the actual invariant set
and case analysis that `github.com/google/btree`-style libraries (and
C++'s `std::map`, Java's `TreeMap`) implement under the hood.

**Five invariants:** every node red or black · root is black · every nil
leaf is black · a red node never has a red child (no two reds in a row on
any path) · every root-to-leaf path has the same black-node count
("black-height"). Invariants 4+5 together force the longest path ≤ `2×`
the shortest (alternating red/black at best case), so height is
**provably O(log n)** — this is the proof behind "red-black trees
guarantee O(log n)," not just the assertion of it.

**Insertion fixup**, bottom-up from the newly-inserted red node `z`:

- **Uncle red** → recolor parent+uncle black, grandparent red, move `z` up
  to grandparent, repeat. Propagates up to `O(log n)` times but only
  recolors — no rotation.
- **Uncle black, `z` a "triangle"** (z is a right child, parent is a left
  child, or the mirror) → rotate `parent` to straighten into a line, fall
  through to the next case.
- **Uncle black, "line"** → recolor parent black / grandparent red,
  rotate grandparent the other way. **Terminates the loop** — this is why
  insertion costs at most 2 rotations total, no matter how large the
  tree, plus O(log n) recolorings.

```go
type Color bool

const (
	Red   Color = true
	Black Color = false
)

type RBNode struct {
	Val                 int
	Color               Color
	Left, Right, Parent *RBNode
}

type RedBlackTree struct {
	nilNode *RBNode // sentinel: every leaf points here, always black
	root    *RBNode
}

func NewRedBlackTree() *RedBlackTree {
	sentinel := &RBNode{Color: Black}
	return &RedBlackTree{nilNode: sentinel, root: sentinel}
}

func (t *RedBlackTree) leftRotate(x *RBNode) {
	y := x.Right
	x.Right = y.Left
	if y.Left != t.nilNode {
		y.Left.Parent = x
	}
	y.Parent = x.Parent
	switch {
	case x.Parent == nil:
		t.root = y
	case x == x.Parent.Left:
		x.Parent.Left = y
	default:
		x.Parent.Right = y
	}
	y.Left = x
	x.Parent = y
}

func (t *RedBlackTree) rightRotate(y *RBNode) {
	x := y.Left
	y.Left = x.Right
	if x.Right != t.nilNode {
		x.Right.Parent = y
	}
	x.Parent = y.Parent
	switch {
	case y.Parent == nil:
		t.root = x
	case y == y.Parent.Left:
		y.Parent.Left = x
	default:
		y.Parent.Right = x
	}
	x.Right = y
	y.Parent = x
}

func (t *RedBlackTree) Insert(val int) {
	z := &RBNode{Val: val, Color: Red, Left: t.nilNode, Right: t.nilNode}
	var y *RBNode
	x := t.root
	for x != t.nilNode {
		y = x
		if z.Val < x.Val {
			x = x.Left
		} else {
			x = x.Right
		}
	}
	z.Parent = y
	switch {
	case y == nil:
		t.root = z
	case z.Val < y.Val:
		y.Left = z
	default:
		y.Right = z
	}
	t.insertFixup(z)
}

func (t *RedBlackTree) insertFixup(z *RBNode) {
	for z.Parent != nil && z.Parent.Color == Red {
		grandparent := z.Parent.Parent
		if z.Parent == grandparent.Left {
			uncle := grandparent.Right
			if uncle.Color == Red { // Case 1
				z.Parent.Color = Black
				uncle.Color = Black
				grandparent.Color = Red
				z = grandparent
			} else {
				if z == z.Parent.Right { // Case 2
					z = z.Parent
					t.leftRotate(z)
				}
				z.Parent.Color = Black // Case 3
				z.Parent.Parent.Color = Red
				t.rightRotate(z.Parent.Parent)
			}
		} else { // mirror image
			uncle := grandparent.Left
			if uncle.Color == Red {
				z.Parent.Color = Black
				uncle.Color = Black
				grandparent.Color = Red
				z = grandparent
			} else {
				if z == z.Parent.Left {
					z = z.Parent
					t.rightRotate(z)
				}
				z.Parent.Color = Black
				z.Parent.Parent.Color = Red
				t.leftRotate(z.Parent.Parent)
			}
		}
	}
	t.root.Color = Black // invariant 2
}
```

**Deletion fixup** is the same three-case shape applied to a conceptual
"double-black" token (removing a black node leaves that path one
black-node short of invariant 5): sibling red → recolor + rotate and
recurse up; sibling black with a red "far" nephew → terminal rotation;
sibling black with only a "near" red nephew → rotate into the far case.
Same bound as insertion in the case count, but **at most 3 rotations**
(vs. insertion's 2) — still O(1) rotations, O(log n) recolorings.

| | AVL | Red-Black |
|---|---|---|
| Balance invariant | subtree heights differ by ≤1 | longest path ≤ 2× shortest |
| Lookup | faster (tighter balance) | slightly slower |
| Insert rotations | O(log n) worst case | O(1) worst case |
| Delete rotations | O(log n) worst case | O(1) (≤3) worst case |
| Go production choice | — | `github.com/google/btree` uses a B-tree instead of either, for cache locality (§ below) |

---

## Part 5 · BST-Specific Algorithms That Beat the General-Tree Version

The BST invariant lets you do strictly less work than the general-binary-tree
algorithm for several classic problems:

### 5.1 Kth smallest — in-order with early exit

```go
func kthSmallest(root *TreeNode, k int) int {
    stack := []*TreeNode{}
    n := root
    for n != nil || len(stack) > 0 {
        for n != nil {
            stack = append(stack, n)
            n = n.Left
        }
        n = stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        k--
        if k == 0 {
            return n.Val
        }
        n = n.Right
    }
    return -1
}
```

Iterative in-order with an explicit stack (topic 6) lets you **stop the
instant you hit the kth element** — O(h + k) instead of O(n) for a full
traversal followed by indexing, which matters when `k` is small and the
tree is large.

### 5.2 LCA in a BST — pure comparison, no subtree search

In a general binary tree, LCA requires searching both subtrees (topic 10) —
O(n). In a BST, the invariant tells you which side to go without searching
either:

```go
func lowestCommonAncestor(root, p, q *TreeNode) *TreeNode {
    n := root
    for n != nil {
        switch {
        case p.Val < n.Val && q.Val < n.Val:
            n = n.Left
        case p.Val > n.Val && q.Val > n.Val:
            n = n.Right
        default:
            return n   // p, q split here (or one equals n) — this IS the LCA
        }
    }
    return nil
}
```

O(h) instead of O(n) — a direct payoff of the ordering invariant.

### 5.3 Floor / ceiling / predecessor / successor

Rather than an O(n) full traversal, walk down from the root, narrowing:

```go
func floor(n *TreeNode, target int) *TreeNode {
    var best *TreeNode
    for n != nil {
        if n.Val == target {
            return n
        }
        if n.Val < target {
            best = n          // candidate: could still improve going right
            n = n.Right
        } else {
            n = n.Left
        }
    }
    return best
}
```

O(h) — same shape as search, just tracking the best-so-far candidate on the
way down.

---

## Part 6 · Complexity Table

| Operation | Balanced (average) | Skewed (worst) |
|---|:--:|:--:|
| Search | **O(log n)** | O(n) |
| Insert | **O(log n)** | O(n) |
| Delete | **O(log n)** | O(n) |
| In-order traversal | O(n) | O(n) |
| Kth smallest | O(h + k) | O(n) |
| Floor / ceiling / predecessor / successor | O(h) | O(n) |
| Build from sorted array (balanced) | O(n) | — |

`h` = tree height; `h = O(log n)` only when balanced, `h = O(n)` when
degenerate — this row-to-row dependency is the whole point of Part 4.

---

## Part 7 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Ordered container | `sortedcontainers.SortedList` (3rd-party, but ubiquitous) | **Nothing in std** — hand-roll or `google/btree` |
| Balanced tree in std | No (needs 3rd-party too) | No |
| Tree node | Class with `self.left`/`self.right` | Struct with pointer fields |
| Mutating via return value | Reassign `self.left = insert(self.left, v)` — same pattern | Identical: `n.Left = insert(n.Left, v)` |
| Recursion depth limit | ~1000 (`sys.setrecursionlimit` to raise) | Governed by goroutine stack growth (starts at 2 KB, grows by copy-and-double to a 1 GB default ceiling) — practically much more headroom |
| Generic key comparison | Duck-typed `<` | Needs an explicit `cmp` function pre-generics; Go 1.21+ generics + `cmp.Ordered` close this gap |

The recursion-limit row matters concretely: a Python solution to a
deeply-skewed-BST problem can hit `RecursionError` on inputs that Go's
recursive equivalent handles without complaint, purely because of how each
runtime manages call stacks (topic 6, Part on stack growth).

---

## Part 8 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| BST search / insert / delete | O(log n) avg | O(1) iterative / O(h) recursive | Core operations |
| In-order traversal validity check | O(n) | O(h) | LC 98 Validate BST |
| In-order with early exit | O(h + k) | O(h) | LC 230 Kth Smallest in a BST |
| Comparison-based LCA | O(h) | O(1) | LC 235 LCA of a BST |
| Floor / ceiling walk | O(h) | O(1) | LC 270-style closest-value problems |
| Sorted array → balanced BST (midpoint recursion) | O(n) | O(log n) | LC 108 |
| Two-pointer via in-order + set | O(n) | O(n) | LC 653 Two Sum IV — Input is a BST |
| Successor-splice delete | O(log n) avg | O(h) | LC 450 Delete Node in a BST |

---

## Part 9 · Building a BST From Scratch

```go
package main

type BSTNode struct {
    Val         int
    Left, Right *BSTNode
}

type BST struct {
    root *BSTNode
}

func (t *BST) Insert(val int) {
    t.root = insertNode(t.root, val)
}

func insertNode(n *BSTNode, val int) *BSTNode {
    if n == nil {
        return &BSTNode{Val: val}
    }
    if val < n.Val {
        n.Left = insertNode(n.Left, val)
    } else if val > n.Val {
        n.Right = insertNode(n.Right, val)
    }
    return n // duplicate values are silently ignored
}

func (t *BST) Search(val int) bool {
    n := t.root
    for n != nil {
        switch {
        case val == n.Val:
            return true
        case val < n.Val:
            n = n.Left
        default:
            n = n.Right
        }
    }
    return false
}

func (t *BST) Delete(val int) {
    t.root = deleteNode(t.root, val)
}

func deleteNode(n *BSTNode, val int) *BSTNode {
    if n == nil {
        return nil
    }
    switch {
    case val < n.Val:
        n.Left = deleteNode(n.Left, val)
    case val > n.Val:
        n.Right = deleteNode(n.Right, val)
    default:
        if n.Left == nil {
            return n.Right
        }
        if n.Right == nil {
            return n.Left
        }
        // two children: splice in the in-order successor (min of right subtree)
        succ := n.Right
        for succ.Left != nil {
            succ = succ.Left
        }
        n.Val = succ.Val
        n.Right = deleteNode(n.Right, succ.Val)
    }
    return n
}

// InOrder returns values in sorted order — a direct consequence of the BST invariant.
func (t *BST) InOrder() []int {
    out := make([]int, 0)
    var walk func(n *BSTNode)
    walk = func(n *BSTNode) {
        if n == nil {
            return
        }
        walk(n.Left)
        out = append(out, n.Val)
        walk(n.Right)
    }
    walk(t.root)
    return out
}
```

**Talk track while writing:** insert/delete both follow "recurse to the
right subtree, then reassign the return value into the parent's child
pointer" — this is the one pattern that makes Go tree mutation clean without
double pointers. The delete's two-children branch is the only non-obvious
part: copy the successor's value up, then delete the successor from the
right subtree, which is now guaranteed to be a simple case since a
leftmost node can never have a left child.

**Generic version, for completeness:** a production-grade BST would replace
`int` with `K cmp.Ordered` (Go 1.21+) and take a `cmp func(a, b K) int` for
custom key types — the shape of the algorithm above is identical; only the
comparisons change from `<`/`>` to `cmp(a, b) < 0`/`> 0`.

---

<!-- block:11_go_1_problems -->
## Part 10 · The Eleven Problems in Go, Plus the Pointer-to-Pointer Idiom

All code below ran on Go 1.24.5 against LeetCode's own examples.

```arch
%% caption: The three delete cases. Say all three before writing a line — skipping one is how this problem is failed. A missing left child covers the leaf and the right-only cases in one line.
grid 210x90
node d "Found the node to delete" at 0,0 shape=pill w=200
node a "n.Left == nil?" at 0,1 shape=diamond color=amber
node r1 "Replace n with n.Right" at 1,1 color=green w=220 sub="covers a leaf AND right-only"
node b "n.Right == nil?" at 0,2 shape=diamond color=amber
node r2 "Replace n with n.Left" at 1,2 color=green w=220
node c "Find the inorder successor" at 0,3 color=amber w=220 sub="the leftmost node of n.Right"
node e "Copy its value up" at 0,4 color=amber w=220 sub="then delete the successor from n.Right (an easy case)"
d -> a
a -> r1 : "yes"
a -> b : "no"
b -> r2 : "yes"
b -> c : "no: two children"
c -> e
```

### Insert and delete through a pointer-to-pointer — something Python cannot do

The recursive form reassigns the returned child (`n.Left = insert(n.Left, v)`). Go also lets you keep a **`**TreeNode`**
— the address of the *slot* that points at the current node — which removes the parent-tracking and the empty-tree
special case entirely:

```go
func insert(root **TreeNode, val int) {
    for *root != nil {
        if val < (*root).Val { root = &(*root).Left } else { root = &(*root).Right }
    }
    *root = &TreeNode{Val: val}                     // the nil slot we fell into IS where the node goes
}
```

`*root = &TreeNode{...}` writes into the *parent's* field (or the caller's variable, for the first insert) — exactly what a
Python local assignment (`root = TreeNode(val)`) cannot do. Delete works the same way and collapses the three cases:

```go
func remove(root **TreeNode, val int) {
    for *root != nil && (*root).Val != val { /* descend, root = &(*root).Left or .Right */ }
    if *root == nil { return }                       // absent
    n := *root
    switch {
    case n.Left == nil:  *root = n.Right             // leaf and right-only in one line
    case n.Right == nil: *root = n.Left
    default:
        succ := &n.Right                              // the pointer TO the leftmost node of the right subtree
        for (*succ).Left != nil { succ = &(*succ).Left }
        s := *succ
        *succ = s.Right                               // unlink the successor
        s.Left, s.Right = n.Left, n.Right
        *root = s                                     // and put it where n was
    }
}
```

Call it as `insert(&root, v)` / `remove(&root, v)`. (Move the *node*, not its value, when other code may hold pointers to
the successor.) `[5 3 8 1 4 7 9]`: removing 3 → `[1 4 5 7 8 9]`; removing the root 5 → `[1 4 7 8 9]`.

### Sorted array → balanced BST (LC 108): indices, not slices

A sorted array *is* the target's inorder sequence: the middle becomes the root. Recurse on **index ranges** — slicing
makes O(n log n) copies in Python but only header copies in Go, so both are fine here; prefer indices anyway and keep one
range convention:

```go
var build func(lo, hi int) *TreeNode                 // closed range [lo, hi]
build = func(lo, hi int) *TreeNode {
    if lo > hi { return nil }
    mid := lo + (hi-lo)/2
    return &TreeNode{nums[mid], build(lo, mid-1), build(mid+1, hi)}
}
```

Mixing the closed range with a `lo >= hi` base case drops the last element of every range.

### BST Iterator (LC 173): the explicit stack *is* the state

```go
type BSTIterator struct{ st []*TreeNode }

func (it *BSTIterator) pushLeft(n *TreeNode) { for ; n != nil; n = n.Left { it.st = append(it.st, n) } }
func (it *BSTIterator) Next() int {
    n := it.st[len(it.st)-1]
    it.st = it.st[:len(it.st)-1]
    it.pushLeft(n.Right)                              // the WHOLE left spine of the right child, not just n.Right
    return n.Val
}
func (it *BSTIterator) HasNext() bool { return len(it.st) > 0 }
```

`New` calls `pushLeft(root)`. O(h) memory and amortised O(1) `Next` (each node is pushed and popped once). Pushing only
`n.Right` returns values out of order. Precomputing the sorted slice is a valid first answer that fails the O(h) follow-up.

### Recover BST (LC 99): the dips in inorder

Scan inorder tracking `prev`. The **first** dip (`prev.Val > n.Val`) gives `first = prev`; **every** dip sets
`second = n` — a far-apart swap makes two dips, an adjacent swap makes one:

```go
if prev != nil && prev.Val > n.Val {
    if first == nil { first = prev }                  // only the FIRST dip sets first
    second = n                                         // EVERY dip updates second
}
prev = n
...
first.Val, second.Val = second.Val, first.Val
```

Setting `first` on every dip, or `second` only once, passes the adjacent-swap cases and fails the far-apart ones.
`[1 3 _ _ 2]` → inorder `[1 2 3]`; `[3 1 4 _ _ 2]` → `[1 2 3 4]`.

### Inorder Successor (LC 285) and Minimum Absolute Difference (LC 530)

```go
// Successor: one descent, no parent pointer. Every time we turn LEFT, that node is a candidate.
var succ *TreeNode
for n := root; n != nil; {
    if p.Val < n.Val { succ = n; n = n.Left } else { n = n.Right }
}
return succ                                            // nil when p is the maximum

// Min difference: the minimum is between ADJACENT inorder values, so remember only the previous one.
best, havePrev, prev := math.MaxInt, false, 0
walk = func(n *TreeNode) {
    if n == nil { return }
    walk(n.Left)
    if havePrev { best = min(best, n.Val-prev) }
    prev, havePrev = n.Val, true
    walk(n.Right)
}
```

Use a `havePrev` flag (or a `*int`) rather than a sentinel `prev` — with values that can be any `int`, no sentinel is safe.
The all-pairs O(n²) loop is the trap; the list-then-scan version costs O(n) space.

### Beyond the eleven

**Preorder → BST in O(n)** (LC 1008): carry an upper bound and consume through a shared cursor; a value above the bound
belongs to an ancestor, so return `nil` *without* consuming it:

```go
var go_ func(bound int) *TreeNode
go_ = func(bound int) *TreeNode {
    if i == len(pre) || pre[i] > bound { return nil }
    n := &TreeNode{Val: pre[i]}; i++
    n.Left = go_(n.Val)
    n.Right = go_(bound)
    return n
}                                                       // go_(math.MaxInt): [8 5 1 7 10 12] -> inorder [1 5 7 8 10 12]
```

**Greater Tree** (LC 538) is *reverse* inorder with a running total: `dfs(n.Right); total += n.Val; n.Val = total;
dfs(n.Left)`. **Range Sum** (LC 938) and **Trim** (LC 669) prune on the bounds: a node below `lo` discards itself *and its
left subtree*. **Closest value** (LC 270) is a descent remembering the best seen. **Balance a BST** (LC 1382) is inorder
+ the midpoint rebuild. **Unique BSTs** (LC 96) is the Catalan recurrence `C(n) = Σ C(i)·C(n-1-i)` →
`1, 2, 5, 14, 42, 132, 429` for `n = 1..7`.

---
<!-- /block:11_go_1_problems -->

<!-- block:11_go_2_augment -->
## Part 11 · Augmentation, a Generic Ordered Map, and the Landscape

### Order statistics: store subtree sizes, recompute on the way up

Add a `Size` to every node and **recompute it as the recursion unwinds** from every insert and delete. Then `select(k)`
and `rank(key)` are O(h) descents — the answer to the classic Kth Smallest follow-up *"the tree changes often and `k`
varies"*:

```go
type OSNode struct { Key int; Left, Right *OSNode; Size int }

func size(n *OSNode) int { if n == nil { return 0 }; return n.Size }

func insert(n *OSNode, key int) *OSNode {
    if n == nil { return &OSNode{Key: key, Size: 1} }
    switch {
    case key < n.Key: n.Left = insert(n.Left, key)
    case key > n.Key: n.Right = insert(n.Right, key)
    default: return n                                   // duplicate: rejected (a stated policy)
    }
    n.Size = 1 + size(n.Left) + size(n.Right)           // AUGMENTATION: recompute on the way back up
    return n
}

func selectK(n *OSNode, k int) int {                    // k-th smallest, 1-based
    l := size(n.Left)
    switch {
    case k <= l:     return selectK(n.Left, k)
    case k == l+1:   return n.Key
    default:         return selectK(n.Right, k-l-1)
    }
}
```

`rank(key)` counts keys `< key` by walking down and adding `size(n.Left) + 1` each time it goes right. Inserting
`5 3 8 1 4 7 9 2 6` gives `selectK(4) = 4`, `selectK(9) = 9`, `rank(6) = 5`, root size 9. Any subtree aggregate you can
recompute from the children (size, sum, min, max, height) can ride along like this — the mechanism behind interval trees,
segment trees (topic 26) and AVL/red-black balance information.

### A generic ordered map with `cmp.Ordered`

Go has no ordered map in the standard library (Part 1), but generics make a small one direct. `cmp.Compare` returns
`-1 / 0 / +1` and handles floats' NaN ordering consistently:

```go
type GNode[K cmp.Ordered, V any] struct { key K; val V; left, right *GNode[K, V] }
type OrderedMap[K cmp.Ordered, V any] struct{ root *GNode[K, V] }

func put[K cmp.Ordered, V any](n *GNode[K, V], k K, v V) *GNode[K, V] {
    if n == nil { return &GNode[K, V]{key: k, val: v} }
    switch c := cmp.Compare(k, n.key); {
    case c < 0: n.left = put(n.left, k, v)
    case c > 0: n.right = put(n.right, k, v)
    default:    n.val = v                                // update in place
    }
    return n
}
```

`Each(func(K, V))` is an inorder walk, so it visits keys in sorted order — `apple=1 fig=2 pear=0` for puts of
`pear, apple, fig`. For a custom ordering take a `cmp func(a, b K) int` instead of `cmp.Ordered`, as `slices.SortFunc` does.
Go 1.23's range-over-func iterators let `Each` become a `func(yield func(K, V) bool)` you can `for range` over.

### The ordered-container landscape

| Structure | Guarantee | Notes |
|---|---|---|
| Plain BST | O(h): O(log n) on random input, **O(n)** on sorted input | Simplest; no rebalancing code. |
| AVL tree | Height ≤ ~1.44 log₂ n | Strictly balanced → fastest lookups; more rotations on update. |
| Red-black tree | Height ≤ 2 log₂(n + 1) | Looser → fewer rotations; C++ `std::map` / Java `TreeMap`. Part 4.3. |
| Treap / skip list | O(log n) *expected* | Random priorities / tower heights: far less code than red-black; skip lists are easy to make concurrent. |
| **B-tree / B+ tree** | O(log_B n), fan-out `B` in the hundreds | Built for **disks and databases**: one node = one page, so a lookup touches ~3–4 pages even for hundreds of millions of keys (`100³ = 10⁶`, `100⁴ = 10⁸`); B+ trees link the leaves for range scans. |

In Go, when you need this *in production*, reach for a B-tree package (`github.com/google/btree`,
`github.com/tidwall/btree`) rather than hand-rolling. In an interview, name the operations you need — insert, delete, rank,
range query — and the structure that provides them.

```arch
%% caption: Choosing an ordered structure. What you need to do with the keys — and where they live — decides it.
grid 210x90
node q "Keys that must stay sorted" at 0,0 shape=pill w=200
node a "Where do they live?" at 0,1 shape=diamond color=amber
node b "B-tree or B+ tree" at 1,1 color=green w=230 sub="on disk / very large · fan-out is the lever"
node c "What operations?" at 0,2 shape=diamond color=amber
node h "map[K]V, O(1) average" at 1,2 color=green w=230 sub="only lookup, order does not matter"
node o "Augment with subtree sizes" at 1,3 color=amber w=230 sub="rank / select / k-th"
node d "Adversarial or sorted input?" at 0,4 shape=diamond color=amber sub="insert, delete, predecessor, range"
node p "Plain BST" at 1,4 color=green w=230 sub="O(log n) expected"
node s "Balanced tree, treap or skip list" at 0,5 color=amber w=230 sub="guaranteed or expected O(log n)"
q -> a
a -> b : "on disk"
a -> c : "in memory"
c:R -> h:L
c:R -> o:L
c -> d
d -> p : "no: random-ish"
d -> s : "yes"
```

### Duplicates are a policy, not an accident

Reject them (a set), keep a **count** in the node (a multiset — rank/select become weighted), or send equal keys
consistently to **one side**. Validation must use the *same* rule: LC 98's strict `<` / `>` treats duplicates as invalid.

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| Reaching for a `TreeMap` | There is no ordered map in the standard library. | Hand-roll, or a B-tree package; say so early. |
| `n.Left = deleteNode(n.Left, v)` without the assignment | The rebuilt subtree is discarded; silent wrong answer. | Always assign the recursive result back — or use `**TreeNode`. |
| `prev := math.MinInt` as a "no previous" sentinel | Fails when a value equals the sentinel. | A `havePrev` flag or `*int`. |
| `mid := (lo + hi) / 2` | Overflows only on absurd indices — but write `lo + (hi-lo)/2` by habit. | The safe form. |
| Comparing `n.Val < lo` after a subtraction | `int` arithmetic on extreme values wraps silently. | Compare directly; don't subtract to compare. |
| Map keyed by `*TreeNode` after copying nodes | A copied struct is a different pointer key. | Never copy a node by value. |
| Deep recursion on a sorted-input BST | Depth `n`; fatal `stack overflow` at 1 GB, unrecoverable. | Iterate (Morris / explicit stack), or balance the tree. |

### Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "The tree is modified often; `k` varies." | Subtree sizes: `selectK` in O(h). |
| "It might be skewed." | AVL / red-black / treap; say a plain BST degrades to a linked list. |
| "Range queries?" | Prune on the bounds; or a B+ tree's linked leaves. |
| "On disk?" | A B-tree / B+ tree — fan-out is the lever, not height. |
| "Concurrent access?" | Hand-over-hand locking, or a lock-free skip list; `sync.RWMutex` around the whole tree is the simple answer. |
| "Successor in O(1)?" | A threaded BST (Morris made permanent), or a parent pointer plus a linked list of nodes. |

---
<!-- /block:11_go_2_augment -->

<!-- problem-map:start -->
## Part 12 · Every Problem in This Topic, by Pattern

Eleven problems, five moves (compare-and-discard · construction from inorder · deletion · use the ordering · inorder as a sequence) — the Python guide's map in Go, with the Go-only traps. Topic 11 has one full Go solution in the folder; the rest is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Search in a Binary Search Tree](GoDSA/11_binary_search_tree/001_search_in_a_binary_search_tree/solution.go) <br>LC 700 · Easy | Compare and discard | A `for n != nil` loop comparing with `n.Val`; O(h), O(1) space. **Trap:** recursing into both children (O(n)); comparing against the child values. |
| [002 · Convert Sorted Array to Binary Search Tree](GoDSA/11_binary_search_tree/002_convert_sorted_array_to_binary_search_tree/solution.go) <br>LC 108 · Easy | Sorted array = inorder | Closed-range midpoint recursion `build(lo, hi)`; slicing is cheap in Go but keep indices. **Trap:** mixing `[lo, hi]` with a `lo >= hi` base case. |
| [003 · Insert into a Binary Search Tree](GoDSA/11_binary_search_tree/003_insert_into_a_binary_search_tree/solution.go) <br>LC 701 · Medium | Insertion is a failed search | Recursive `n.Left = insert(n.Left, v)`, or iterative through a **`**TreeNode`** (write into the slot you fell into). **Trap:** not returning / not assigning the child; parent tracking for the empty tree. |
| [004 · Delete Node in a BST](GoDSA/11_binary_search_tree/004_delete_node_in_a_bst/solution.go) <br>LC 450 · Medium | Three delete cases | `n.Left == nil → n.Right`, `n.Right == nil → n.Left`, else splice the inorder successor — recursive, or via `**TreeNode`. **Trap:** dropping the assignment of the recursive result; forgetting the one-child case. |
| [005 · Lowest Common Ancestor of a Binary Search Tree](GoDSA/11_binary_search_tree/005_lowest_common_ancestor_of_a_binary_search_tree/solution.go) <br>LC 235 · Medium | The split point | `for { if p.Val < n.Val && q.Val < n.Val { n = n.Left } else if … }` — O(h), no recursion. **Trap:** LC 236's O(n) recursion; comparing values when identity is needed. |
| [006 · Validate Binary Search Tree](GoDSA/11_binary_search_tree/006_validate_binary_search_tree/solution.go) <br>LC 98 · Medium | Bounds, not local checks | `valid(n, lo, hi *int)` with pointer bounds (nil = unbounded), or `math.MinInt`/`MaxInt` bounds with strict `<`. **Trap:** a sentinel that a real value equals; `<=` accepting duplicates. |
| [007 · Kth Smallest Element in a BST](GoDSA/11_binary_search_tree/007_kth_smallest_element_in_a_bst/solution.go) <br>LC 230 · Medium | Inorder with an early exit | Iterative stack, stop at the `k`-th pop: O(h + k). **Trap:** building the full slice; an off-by-one on `k`. |
| [008 · Binary Search Tree Iterator](GoDSA/11_binary_search_tree/008_binary_search_tree_iterator/solution.go) <br>LC 173 · Medium | A paused inorder | `st []*TreeNode`; `Next` pops then `pushLeft(n.Right)`. **Trap:** pushing only `n.Right`; precomputing the list (fails the O(h) follow-up). |
| [009 · Recover Binary Search Tree](GoDSA/11_binary_search_tree/009_recover_binary_search_tree/solution.go) <br>LC 99 · Hard | The dips in inorder | `first` set once, `second` updated on every dip, then swap the values. **Trap:** overwriting `first`; setting `second` once. |
| [010 · Inorder Successor in BST](GoDSA/11_binary_search_tree/010_inorder_successor_in_bst/solution.go) <br>LC 285 · Medium | Turn-left candidate | One `for` descent: `if p.Val < n.Val { succ = n; n = n.Left } else { n = n.Right }`. **Trap:** assuming a parent pointer; forgetting the has-right-child case. |
| [011 · Minimum Absolute Difference in BST](GoDSA/11_binary_search_tree/011_minimum_absolute_difference_in_bst/solution.go) <br>LC 530 · Easy | Adjacent in sorted order | Inorder with a `havePrev` flag; `best = min(best, n.Val-prev)`. **Trap:** the all-pairs O(n²) loop; a sentinel `prev`. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] State clearly that Go's standard library has no ordered map/BST/set
- [ ] Explain why in-order traversal of a BST yields sorted output
- [ ] Validate a BST using the `(low, high)` range technique, not local checks
- [ ] Write insert, search, and all three delete cases from memory
- [ ] Explain why an unbalanced BST degrades to O(n), and what rotations fix
- [ ] Use the BST invariant to answer LCA in O(h), not O(n)
- [ ] Implement kth-smallest with an early-exit iterative in-order traversal
- [ ] Know when to reach for `google/btree` instead of hand-rolling AVL/red-black
- [ ] State red-black's five invariants and derive the O(log n) height bound
      from invariants 4+5 (no two reds in a row, equal black-height)
- [ ] Walk through insertion's three fixup cases (uncle red / triangle /
      line) and explain why insertion costs at most 2 rotations total
- [ ] Write insert and delete through a `**TreeNode` and explain what the pointer-to-pointer buys you <!--ca-->
- [ ] Augment a BST with subtree sizes and write `selectK` / `rank` in O(h) <!--ca-->
- [ ] Build a BST from preorder in O(n) with an upper bound <!--ca-->
- [ ] Write a generic ordered map with `cmp.Ordered`, and say what the standard library lacks <!--ca-->
- [ ] Name the ordered-container options and when a B+ tree is the answer <!--ca-->
