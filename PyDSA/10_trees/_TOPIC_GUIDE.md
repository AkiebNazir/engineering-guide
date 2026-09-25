# Topic 10 · Trees — Python Deep Dive

> Every list/array topic so far (01, 03, 04) leaned on one fact: the data is
> laid out in a line, so "next" means "index + 1". A tree throws that away —
> "next" means "follow a reference", and there are TWO of them at every node.
> That single change is why trees need their own vocabulary: preorder vs
> inorder vs postorder (which reference do you follow, and when do you look
> at the current node?), <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> vs <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> (do you go deep before wide, or wide
> before deep?), and a whole family of "return something up the call stack
> while a side channel tracks something else" patterns that arrays never
> needed. This guide is the mechanism; see the Go guide
> (`GoDSA/10_trees/_TOPIC_GUIDE.md`) for what changes when nodes are real heap
> allocations with no garbage collector safety net for `nil` — Python's
> version of that story is in Part 5 below, kept short on purpose since the
> Go guide already covers the pointer/memory side in full.

---

## Part 1 · The Node, and the Two Recursive Floors

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
```

`None` is the empty subtree. Every recursive tree function has the same
shape: check `None` first (the base case), then combine the answers from
`node.left` and `node.right` (the recursive case). This is the whole grammar;
everything below is what you do with it.

```
        1
      ╱   ╲
     2      3
   ╱  ╲       ╲
  4    5       6
```

---

## Part 2 · <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> — Three Orders, Two Implementations Each

<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> commits to one branch and goes all the way down before backing up. The
three "orders" differ only in WHEN, relative to the two recursive calls, you
visit the current node.

```arch
%% caption: Preorder 1 2 4 5 3 · Inorder 4 2 5 1 3 · Postorder 4 5 2 3 1 · Level order 1 2 3 4 5.
route straight
grid 80x90
node n1 "1" at 1.5,0 shape=circle color=blue
node n2 "2" at 0.5,1 shape=circle color=blue
node n3 "3" at 2.5,1 shape=circle color=blue
node n4 "4" at 0,2 shape=circle color=blue
node n5 "5" at 1,2 shape=circle color=blue
n1 -> n2
n1 -> n3
n2 -> n4
n2 -> n5
```


### 2.1 The three orders, recursive

```python
def preorder(node, out):     # ROOT, left, right — "visit on the way down"
    if node is None:
        return
    out.append(node.val)
    preorder(node.left, out)
    preorder(node.right, out)

def inorder(node, out):      # left, ROOT, right — "visit on the way through"
    if node is None:
        return
    inorder(node.left, out)
    out.append(node.val)
    inorder(node.right, out)

def postorder(node, out):    # left, right, ROOT — "visit on the way up"
    if node is None:
        return
    postorder(node.left, out)
    postorder(node.right, out)
    out.append(node.val)
```

On the tree above:

```
preorder  : 1 2 4 5 3 6      (root first, always)
inorder   : 4 2 5 1 3 6      (root strictly between its children)
postorder : 4 5 2 6 3 1      (root last, always)
```

**Why the name matches a real use, not just a memory drill:**
- *Preorder* reproduces a tree from a stream top-down (LC 297, problem 019
  here — the root must be read before you know where its subtrees start).
- *Inorder* on a **binary search tree** yields sorted order — the one order
  worth memorizing cold, and it is why topic 11 (<abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr>) exists as its own
  topic.
- *Postorder* is "children before parent" — the shape every bottom-up
  aggregate needs (height, diameter, balance, max path sum — Part 3).

### 2.2 The recursion-limit fact that makes "just recurse" not always safe

Python's default recursion limit is ~1000 frames (`sys.getrecursionlimit()`).
A **balanced** tree of `n` nodes has depth `O(log n)` — a million-node
balanced tree is only ~20 frames deep, no problem. A **skewed** tree (every
node has only a left child, say) has depth `O(n)` — a tree built from
already-sorted input inserted into a naive structure, or an adversarial test
case, can blow the limit at a few thousand nodes. This is not
theoretical — 018 (`018_binary_tree_maximum_path_sum_solution.py`, already in
this folder) measures a `RecursionError` on a real 30,000-node chain and
shows the iterative fix. **Recognize the shape "chain-like tree, N up to
10^4-10^5" as a cue to reach for an iterative traversal**, not because
recursion is "slow", but because it can crash outright.

### 2.3 Iterative <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> with an explicit stack

The call stack IS a stack — an iterative traversal just makes that stack a
Python list you control, so its size lives on the heap instead of counting
against the interpreter's C recursion limit.

**Preorder iterative — the easy one** (root visited immediately, so push
right before left to pop left first):

```python
def preorder_iterative(root):
    if root is None:
        return []
    out, stack = [], [root]
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.right:            # push right FIRST
            stack.append(node.right)
        if node.left:              # so left pops FIRST
            stack.append(node.left)
    return out
```

**Inorder iterative — the one to know cold** (walk the whole left spine
before visiting anything):

```python
def inorder_iterative(root):
    out, stack = [], []
    curr = root
    while curr or stack:
        while curr:                     # push the entire left spine
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()               # backtrack to the last unvisited root
        out.append(curr.val)
        curr = curr.right                # then descend into its right subtree
    return out
```

```
Tree:        2
            ╱ ╲
           1    3

curr=2 -> push 2, curr=1 -> push 1, curr=None (left exhausted)
pop 1 -> visit 1 -> curr = 1.right = None
pop 2 -> visit 2 -> curr = 2.right = 3
push 3, curr = None
pop 3 -> visit 3 -> curr = None
stack empty, curr None -> done.   out = [1, 2, 3]   (sorted, if this were a BST)
```

**Postorder iterative — the awkward one.** Two standard tricks:
1. Do a *modified preorder* that visits ROOT, RIGHT, LEFT (swap the push
   order from §2.3's preorder), then reverse the output at the end. Reversing
   `root, right, left` gives `left, right, root` — postorder, for free.
2. Track a "last visited node" and only emit the current node once BOTH
   children have been visited (more code, no reversal, useful when you can't
   afford to build then reverse a whole output list).

```python
def postorder_iterative(root):          # trick 1: reversed modified-preorder
    if root is None:
        return []
    out, stack = [], [root]
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.left:                   # push LEFT first this time
            stack.append(node.left)
        if node.right:                  # so RIGHT pops first -> root,right,left
            stack.append(node.right)
    return out[::-1]                    # reverse -> left,right,root
```

---

## Part 3 · <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> — Level Order, Built on `collections.deque`

<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> goes deep first; <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> goes wide first — it visits every node at distance
`k` from the root before any node at distance `k+1`. This needs a **queue**,
not a stack: the whole reason <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>/<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> produce different orders is that one
structure is <abbr title="Last-In, First-Out. A method for processing data where the last items entered are the first to be removed, characteristic of stack data structures.">LIFO</abbr> and the other is <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr>. Topic 07's guide
(`PyDSA/07_queue_deque/_TOPIC_GUIDE.md`) covers the container in full — this
is the specific way trees use it.

```arch
%% caption: Level-order BFS: taking len(queue) up front is what separates one level from the next.
grid 220x100
node A "queue = deque([root])" at 1,0 shape=pill
node B "queue not empty?" at 1,1 shape=diamond color=amber
node Z "done" at 0,1 shape=pill color=green
node C "size = len(queue)" at 1,2 color=amber sub="exactly one whole level"
node D "pop size nodes" at 1,3 sub="push each one's children"
node E "level finished" at 2,3 sub="append it to the result"
A -> B
B -> Z : "no"
B -> C : "yes"
C -> D -> E
E:T -> B:R
```


```python
from collections import deque

def level_order(root):
    if root is None:
        return []
    result, queue = [], deque([root])
    while queue:
        level_size = len(queue)          # snapshot: exactly this level's nodes
        level = []
        for _ in range(level_size):
            node = queue.popleft()        # O(1) — this is WHY it's a deque,
            level.append(node.val)        # not a plain list (list.pop(0) is O(n),
            if node.left:                  # see topic 07 §3.0)
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        result.append(level)
    return result
```

The `level_size = len(queue)` snapshot **before** the inner loop is the whole
trick: it freezes "how many nodes belong to this level" before the loop
starts appending next-level children onto the same queue, so the inner `for`
consumes exactly one level and no more.

```
        1
      ╱   ╲
     2      3
   ╱  ╲       ╲
  4    5       6

queue=[1]                                     result=[]
level_size=1: pop 1, push 2,3                 result=[[1]]
queue=[2,3]
level_size=2: pop 2 (push 4,5), pop 3 (push 6) result=[[1],[2,3]]
queue=[4,5,6]
level_size=3: pop 4, pop 5, pop 6              result=[[1],[2,3],[4,5,6]]
queue=[]  -> done
```

### 3.1 <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> space is O(height); <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> space is O(width) — and these differ a lot

```
DFS (recursive or iterative-with-stack): the stack holds at most one path
from root to the current leaf -> O(h) space.

BFS: the queue holds an entire level at once. A perfect binary tree's
bottom level has ceil(n/2) nodes -> O(n) space in the worst case, which can
be far larger than O(h) = O(log n) for that same tree.
```

For a WIDE, shallow tree (e.g. a nearly-complete tree), <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>'s queue can hold
almost the whole tree at once while <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>'s stack never exceeds `O(log n)`.
For a NARROW, deep tree (a chain), <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>'s stack is `O(n)` too — so <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> is
never worse than <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> on space, but it can tie it. **When memory is the
binding constraint and the tree may be wide, prefer <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> with an explicit
stack.** When you need "process level by level" as the actual requirement
(shortest path in an unweighted structure, right-side view, level averages),
<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> is not optional — it is the only order that groups nodes by depth.

---

## Part 4 · The Recursion Design Pattern: Down via Parameters, Up via Return

This is the single most useful sentence in this guide, and it resolves most
"how do I even start" confusion on tree problems:

```arch
%% caption: Information flows down through parameters and up through return values. Decide which one each problem needs.
grid 200x160
node P "parent call" at 1,0 shape=pill color=blue
node C "child call" at 1,1 shape=pill color=blue
P:L -> C:L : "DOWN: parameters\ndepth, lo/hi bounds,\npath so far"
C:R -> P:R : "UP: return value\nheight, sum,\nis-valid"
```


> **A parameter carries information DOWN the call stack** (from parent to
> child — "here is what you need to know about your ancestors").
> **A return value carries information UP the call stack** (from child to
> parent — "here is what I discovered about my whole subtree").

### 4.1 Information flowing DOWN — carry state as a parameter

"Does any root-to-leaf path sum to `target`?" (LC 112, problem 011 here)
needs each node to know how much of the target its ancestors already
consumed. That is naturally a **parameter**, decremented on the way down:

```python
def hasPathSum(node, remaining):
    if node is None:
        return False
    remaining -= node.val
    if node.left is None and node.right is None:      # a leaf
        return remaining == 0
    return hasPathSum(node.left, remaining) or hasPathSum(node.right, remaining)
```

Nothing needs to come back UP except the boolean answer itself — no
aggregation across siblings, no combining left and right into anything more
than `or`. This is the "top-down" family: max depth carried as
`depth + 1`, "good nodes" carrying the running max-so-far (problem 015 in
this folder), root-to-leaf path building.

### 4.2 Information flowing UP — return a value the parent needs

"What is this tree's height?" cannot be answered by a parameter, because the
parent doesn't know the answer until BOTH children have reported theirs. That
is a **return value**, computed on the way back up (postorder, Part 2):

```python
def height(node):
    if node is None:
        return 0
    return 1 + max(height(node.left), height(node.right))
```

This is the "bottom-up" family: height, balance, diameter, subtree sums, max
path sum — anything where a node's answer is a function of its CHILDREN's
answers, not its ancestors'.

### 4.3 The decision in one question

> **Does computing this node's answer require knowing something about its
> ANCESTORS (pass it down as a parameter), or does it require knowing
> something about its DESCENDANTS (return it up from the children)?**

Some problems need both directions at once (<abbr title="Lowest Common Ancestor. In a tree or directed acyclic graph, the lowest node that has both given nodes as descendants.">LCA</abbr>-with-values, or "maximum
difference between a node and an ancestor") — that is the advanced case, not
the default one. Start every new tree problem by asking this question before
writing a line of code.

---

## Part 5 · When Postorder Needs a SECOND Answer: the Closure / `nonlocal` Idiom

Diameter of a Binary Tree (LC 543, problem 010 here) and Binary Tree Maximum
Path Sum (LC 124, problem 018, already in this folder) look like ordinary
postorder aggregates — until you notice the value each node needs to RETURN
to its parent (a one-sided "gain", for continuing a path upward) is a
**different number** from the value that could be the FINAL ANSWER (a
two-sided "through" value, which can never be extended further and so is
never returned — recording it is a dead end for the recursion, but exactly
what the caller ultimately wants).

This is a **graph/<abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> problem wearing a tree costume**: it is really "find
the best value over all possible split points", computed with a bottom-up
<abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> where each node's <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> table has exactly one useful entry (`height`, or
`best downward gain`) but the ANSWER draws from a different, larger
quantity (`left_height + right_height`, or `left_gain + right_gain +
node.val`) that never gets carried forward. Recognizing that split — "the
recurrence's return value and the recurrence's answer are not the same
variable" — is the actual skill this section teaches.

### 5.1 The problem: Python has no cheap "return two things"

Go's answer (see the Go guide §3.2) is a closure capturing a variable by
**reference automatically** — no keyword needed, because Go's escape
analysis promotes a captured local to the heap. Python closures are
**read-only by default**: a nested function can READ an enclosing variable,
but assigning to it inside the nested function creates a new LOCAL variable
instead (silently shadowing the outer one) — unless you say `nonlocal`.

```python
def diameterOfBinaryTree(root):
    best = 0
    def depth(node):
        nonlocal best                    # REQUIRED — without this line,
        if node is None:                 # `best = ...` below raises
            return 0                     # UnboundLocalError, because Python
        l = depth(node.left)             # sees an assignment to `best`
        r = depth(node.right)            # anywhere in the function and
        best = max(best, l + r)          # decides it must be local for the
        return 1 + max(l, r)             # WHOLE function body — even on
    depth(root)                          # the line BEFORE the assignment.
    return best
```

Forgetting `nonlocal` is the single most common bug in this pattern, and the
error (`UnboundLocalError: local variable 'best' referenced before
assignment`) fires on the FIRST recursive call, not where you'd expect.

### 5.2 The idiom, spelled out

```
RETURN value  = what a node reports UPWARD to its parent
                (height, or one-sided "gain" — usable by the caller
                 to extend a path/subtree further)

nonlocal var  = a SEPARATE running answer, mutated as a SIDE EFFECT
                during the same postorder walk
                (diameter-so-far, or the best two-sided "through" value —
                 NEVER usable by a caller, because it represents something
                 that turns around at this node and can't be extended)
```

```python
def diameterOfBinaryTree(root):
    best = 0                              # the running max, closed over
    def depth(node):
        nonlocal best
        if node is None:
            return 0
        l, r = depth(node.left), depth(node.right)
        best = max(best, l + r)           # RECORD: a path THROUGH this node
        return 1 + max(l, r)              # RETURN: height, for the PARENT
    depth(root)
    return best
```

Diameter needs no `max(x, 0)` clamp (unlike max path sum) because a height
is never negative — an empty subtree contributes `0`, never a penalty. That
single difference — can the aggregated quantity be negative? — is why LC 543
is Easy and LC 124 is Hard; the recursive *shape* is otherwise identical.
See problem 018's file (`018_binary_tree_maximum_path_sum_solution.py`) for
the full max-path-sum writeup, including the exact three ways this pattern
breaks (returning the through-value by mistake is the #1 failure there).

### 5.3 The alternative to `nonlocal`: a mutable single-element container

Some codebases avoid `nonlocal` (older Python 2 compatibility, or personal
style) with a one-item list or a tiny mutable object instead — mutating a
CONTENTS doesn't require declaring anything, only rebinding a NAME does:

```python
def diameterOfBinaryTree(root):
    best = [0]                            # a box; best[0] is mutated, not
    def depth(node):                      # `best` itself, so no nonlocal
        if node is None:                  # is needed — Python only requires
            return 0                      # nonlocal/global for REBINDING a
        l, r = depth(node.left), depth(node.right)
        best[0] = max(best[0], l + r)     # name, never for mutating what
        return 1 + max(l, r)              # it already points to
    depth(root)
    return best[0]
```

Both are correct and O(n) time, O(h) space. `nonlocal` is the more Pythonic,
more readable choice for new code (Python 3 exists specifically to make this
clean) — know the box-list version because you WILL see it in the wild, and
because it generalizes trivially to needing several running values at once
(`best = [0, None]` for "best value AND the node that achieved it").

### 5.4 Returning a tuple instead — no mutable state at all

A third option sidesteps closures entirely: return BOTH quantities from
every call and let the caller combine them.

```python
def diameterOfBinaryTree(root):
    def depth(node):                       # returns (height, best_diameter_here)
        if node is None:
            return (0, 0)
        lh, ld = depth(node.left)
        rh, rd = depth(node.right)
        through = lh + rh
        return (1 + max(lh, rh), max(ld, rd, through))
    return depth(root)[1]
```

No `nonlocal`, no box — but every call now allocates a 2-tuple, and the
"two different quantities" fact is easy to lose track of once the tuple has
more than two slots. Useful to know as a variant; the closure/`nonlocal`
form is what to reach for by default, and it is what the solution files in
this folder lead with.

---

## Part 6 · Recognizing a Tree Problem in Disguise

Trees are also the surface where several OTHER topics' techniques first show
up wearing tree syntax:

- **It's really <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> with a postorder recurrence** whenever a node's answer is
  a function of its children's answers computed bottom-up and there's no
  cross-subtree combination beyond addition/max (height, diameter, balance,
  subtree sum, max path sum — Part 5). The "state" is implicit in the call
  stack instead of a table.
- **It's really a graph problem** whenever the structure loses the strict
  "one parent" property — a tree with parent pointers added, or a problem
  that needs to move UPWARD as well as downward (<abbr title="Lowest Common Ancestor. In a tree or directed acyclic graph, the lowest node that has both given nodes as descendants.">LCA</abbr> via parent chains,
  "distance between two nodes" without a designated root) is better modeled
  as an undirected graph and solved with graph <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> (topic 14), not
  tree-specific recursion.
- **It's really topic 04 (prefix sum) with a hashmap**, applied along
  root-to-leaf paths: "count downward paths summing to target, not
  necessarily from the root" (LC 437) is exactly topic 04's "subarray sum
  equals K" hashmap trick, replacing "subarray" with "downward path" and
  "index" with "node". The `seen = {0: 1}` sentinel plays the identical
  role.
- **It's really topic 09 (backtracking)** whenever the problem wants every
  ROOT-TO-LEAF PATH enumerated, not just one boolean/aggregate answer (LC
  113 Path Sum II) — the recursion needs to build a list, append when it
  reaches a leaf, and pop (backtrack) when returning, exactly like
  combinatorial backtracking over a decision tree — except the "decision
  tree" here already IS the input.

The tell in all four cases: strip away the `TreeNode` class and ask what the
recursion is actually computing. If it's "best answer over all split
points, built from children's answers" → <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>. If it needs to walk to a
non-descendant → graph. If it's "does some contiguous stretch sum to K" →
prefix sum + hashmap. If it enumerates every path → backtracking.

---

## Part 7 · Decision Table

```arch
%% caption: Choosing between BFS, postorder and preorder.
grid 250x100
node Q "Tree problem" at 0,0 shape=pill
node A "Answer per LEVEL, or shortest depth?" at 0,1 shape=diamond color=amber
node A1 "BFS with a level size" at 1,1 color=green
node B "Parent needs info from its children?" at 0,2 shape=diamond color=amber
node B1 "Postorder: return values UP" at 1,2 color=green
node C "Children need info from ancestors?" at 0,3 shape=diamond color=amber
node C1 "Preorder: pass parameters DOWN" at 1,3 color=green
node D "Inorder" at 0,4 color=green sub="on a BST: sorted order"
Q -> A
A -> A1 : "yes"
A -> B : "no"
B -> B1 : "yes"
B -> C : "no"
C -> C1 : "yes"
C -> D : "no"
```


| Question | Tool |
|---|---|
| Need every node's value in root/left/right visit order? | Preorder (recursive or iterative, §2.1/§2.3) |
| Need sorted order out of a <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr>? | Inorder (§2.1) — the one order worth memorizing |
| Need children's answers before the parent's? | Postorder (§2.1/§2.3) |
| Need "level by level" grouping, or shortest-path-in-unweighted-tree? | <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> with `collections.deque` (Part 3) |
| Tree might be a long chain / N up to 10^4-10^5? | Iterative, not recursive — Python's recursion limit is real (§2.2) |
| Memory-constrained AND tree could be wide? | <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> (O(h) space) over <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> (O(w) space) — §3.1 |
| Node's answer depends on its ANCESTORS? | Carry state DOWN as a parameter (§4.1) |
| Node's answer depends on its DESCENDANTS? | Return the value UP the call stack (§4.2) |
| Need a running max/best that ISN'T what gets returned? | `nonlocal` closure (§5.2) or a mutable box (§5.3) |
| Need EVERY root-to-leaf path listed? | Backtracking: build, append at leaf, pop on return (Part 6) |
| "Count paths summing to K, not from the root"? | Prefix sum + hashmap along the <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> path (Part 6, LC 437) |
| Need to move to a NON-descendant (uncle, sibling's subtree)? | This is a graph problem now — topic 14 |

---

## Part 8 · Complexity Reference

| Operation | Time | Space | Note |
|---|:--:|:--:|---|
| Recursive <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> (any order) | O(n) | O(h) | h = height; O(log n) balanced, **O(n)** skewed |
| Iterative <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>, explicit stack | O(n) | O(h) | Same space bound, immune to `RecursionError` |
| <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> / level order | O(n) | **O(w)** | w = max width; can far exceed O(h) — §3.1 |
| Postorder aggregate + `nonlocal` | O(n) | O(h) | one pass, one closure variable |
| Top-down with a parameter | O(n) | O(h) | no aggregation needed beyond the boolean/value itself |
| `collections.deque.popleft()` | O(1) | — | vs. `list.pop(0)`'s O(n) — topic 07 §3.0 |

---

## Part 9 · Common Mistakes Across This Topic

1. Using `list.pop(0)` instead of `collections.deque.popleft()` for <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> —
   correct answer, quadratic in practice on wide trees (topic 07 §3.0).
2. Forgetting `level_size = len(queue)` before the inner loop, so levels
   bleed into each other instead of staying separate (§3, Part 3).
3. Forgetting `nonlocal` (or the box-list alternative) when a postorder walk
   needs a running best that differs from its return value —
   `UnboundLocalError` on the first recursive assignment (§5.1).
4. Returning the "through"/two-sided value from a postorder helper instead of
   the one-sided value the parent actually needs — the parent then thinks a
   path forks through a node twice, producing an impossible answer that is
   often LARGER than the truth and so looks like a better result, not a bug
   (full writeup: problem 018's solution file, mistake 1).
5. Recursing on a tree that might be a long chain without checking `n`'s
   upper bound against Python's recursion limit (§2.2).
6. Confusing "carry down" and "return up" — trying to thread ancestor state
   through a return value, or trying to aggregate descendant state through a
   parameter. Ask the §4.3 question before writing code.
7. Treating a problem that needs to move to a non-descendant node (parent
   pointers, sibling access) as ordinary tree recursion instead of
   recognizing it as a graph problem (Part 6).

---

## Part 10 · The Progression in This Folder

```
  001  LC 144  Binary Tree Preorder Traversal    the mechanism, recursive + iterative
  002  LC 94   Binary Tree Inorder Traversal     the one order to know cold (BSTs)
  003  LC 145  Binary Tree Postorder Traversal   children-before-parent, sets up Part 3/5
  004  LC 226  Invert Binary Tree                simplest possible recursive rewrite
  005  LC 104  Maximum Depth of Binary Tree      postorder aggregate, bare (§4.2)
  006  LC 111  Minimum Depth of Binary Tree      the leaf-only trap on an asymmetric tree
  007  LC 100  Same Tree                         two-tree recursion, paired base cases
  008  LC 572  Subtree of Another Tree           composition on 007 + a serialization trap
  009  LC 110  Balanced Binary Tree              postorder + early bailout (this batch)
  010  LC 543  Diameter of Binary Tree           the nonlocal-closure idiom, bare (this batch)
  011  LC 112  Path Sum                          top-down, carry the remaining target (this batch)
  012  LC 101  Symmetric Tree                    two-pointer recursion, CROSSED pairing (this batch)
  013  LC 102  Binary Tree Level Order Traversal BFS with deque, the mechanism (Part 3)
  014  LC 199  Binary Tree Right Side View       BFS variant: last node per level
  015  LC 1448 Count Good Nodes in Binary Tree   top-down, carry the running max (§4.1)
  016  LC 105  Construct Binary Tree from ...    preorder+inorder -> reconstruction
  017  LC 236  Lowest Common Ancestor             recursion returning "found" up the stack
  018  LC 124  Binary Tree Maximum Path Sum      the nonlocal-closure idiom, at full difficulty
  019  LC 297  Serialize and Deserialize         preorder + null markers (this batch)
```

009 → 010 → 011 → 012 form this batch's arc: 009 is postorder-with-early-exit
(§4.2, no closure needed — the answer is a plain bool), 010 is the bare
closure idiom (§5.2), 011 is the top-down parameter idiom's other half
(§4.1), 012 is two-pointer recursion across ONE tree's mirrored halves
(compare 007's two-tree version), and 019 is the reconstruction problem this
whole part-2 <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> discussion was building toward — preorder plus null markers
is exactly enough information to rebuild the tree, and inorder alone is not
(see 019's solution file for why).

---

<!-- block:10_py_1_beyond -->
## Part 11 · Shapes Beyond the Twenty: O(1)-Space Traversal, Tree <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> and Level Variants

The twenty problems teach the recursion design pattern (down via parameters, up via returns). These are the shapes
interviews ask next. Every snippet below was run against LeetCode's own examples while writing this section.

### 11.1 Morris traversal — inorder in O(1) extra space

Recursion costs O(h) stack and an explicit stack costs O(h) heap. Morris removes both by **temporarily threading** the
tree: before descending left, make the rightmost node of the left subtree point back to the current node; when you
arrive at that thread a second time you know the left subtree is finished, so you cut the thread and visit.

```python
def morris_inorder(root):
    out, cur = [], root
    while cur:
        if not cur.left:
            out.append(cur.val); cur = cur.right              # no left subtree: visit, go right
        else:
            pred = cur.left
            while pred.right and pred.right is not cur:        # find the inorder predecessor
                pred = pred.right
            if pred.right is None:
                pred.right = cur; cur = cur.left               # first arrival: THREAD back, descend
            else:
                pred.right = None; out.append(cur.val); cur = cur.right    # second arrival: unthread, visit
    return out
```

O(n) time (each edge is walked at most twice), **O(1) extra space**, and the tree is restored by the end. The catches
to say out loud: it mutates the tree while running (not safe with concurrent readers, and a crash mid-way leaves
threads behind), and it is inorder-shaped — preorder is a one-line change (visit on the *first* arrival), postorder is
awkward.

### 11.2 Iterative postorder, done properly

The "reversed preorder" trick (Part 2.3) yields the postorder *list* but **visits nodes parent-first**, so any work that
must happen bottom-up (freeing nodes, writing `node.sum`) is wrong. The honest iterative form remembers the last node
it *finished*:

```python
def postorder_iter(root):
    out, st, last, cur = [], [], None, root
    while cur or st:
        while cur: st.append(cur); cur = cur.left             # dive left
        top = st[-1]
        if top.right and top.right is not last:
            cur = top.right                                     # right subtree not done yet: go there first
        else:
            out.append(top.val); last = st.pop()               # both subtrees done: visit
    return out       # [1,None,2,3] -> [3,2,1]      [4,2,6,1,3,5,7] -> [1,3,2,5,7,6,4]
```

### 11.3 Path Sum III (LC 437): topic 04 wearing a tree costume

Paths that need not start at the root, and go downward only, are the *subarray-sum-equals-K* problem along each
root-to-node path. Keep a running prefix sum and a count map, and — the tree-specific step — **undo the increment on the
way back up**, because a sibling subtree must not see this branch's prefixes:

```python
def path_sum_iii(root, target):
    seen = defaultdict(int); seen[0] = 1; count = 0
    def dfs(n, running):
        nonlocal count
        if not n: return
        running += n.val
        count += seen[running - target]
        seen[running] += 1
        dfs(n.left, running); dfs(n.right, running)
        seen[running] -= 1                                     # BACKTRACK: this prefix leaves the path
    dfs(root, 0)
    return count      # [10,5,-3,3,2,None,11,3,-2,None,1], 8 -> 3
```

O(n) instead of the O(n·h) of "start a fresh path search at every node". The seed `{0: 1}` and the un-increment are the
two places this goes wrong.

### 11.4 Tree <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>: return a *pair* (House Robber III, LC 337)

When a node's best answer depends on a *choice* that constrains its children, return a tuple of "best if I take this"
and "best if I skip this". No `nonlocal` needed — the parent combines two numbers per child:

```python
def rob(root):
    def dfs(n):
        if not n: return (0, 0)                     # (rob this node, skip this node)
        l, r = dfs(n.left), dfs(n.right)
        return (n.val + l[1] + r[1],                # take n: both children must be skipped
                max(l) + max(r))                    # skip n: each child is free to do its best
    return max(dfs(root))          # [3,2,3,None,3,None,1] -> 7      [3,4,5,1,3,None,1] -> 9
```

The same "return a small state tuple" idea solves Binary Tree Cameras (states: uncovered / covered / has camera) and
Longest Univalue Path. It is the tree version of the <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> topics (16/17): the recursion *is* the table.

### 11.5 Rewiring in place: Flatten (LC 114) and Next Pointers (LC 116/117)

**Flatten to a linked list** in preorder — process **right, left, node** (reverse postorder) while carrying a `prev`
pointer, so each node's `right` can point at the node already flattened after it:

```python
prev = None
def dfs(n):
    nonlocal prev
    if not n: return
    dfs(n.right); dfs(n.left)
    n.right, n.left = prev, None
    prev = n
# [1,2,5,3,4,None,6] -> 1 -> 2 -> 3 -> 4 -> 5 -> 6 down the right pointers
```

**Populating Next Right Pointers** in O(1) extra space: walk one level using the `next` pointers *that level already
has*, and use them to link the level below — no queue needed:

```python
head = root
while head:
    dummy = tail = Node(); cur = head
    while cur:                                   # traverse this level through its own next pointers
        for ch in (cur.left, cur.right):
            if ch: tail.next = ch; tail = ch     # link the next level as we go
        cur = cur.next
    head = dummy.next                            # first node of the next level
```

### 11.6 Level-order variants

| Problem | The change to the <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> template |
|---|---|
| Zigzag Level Order (LC 103) | Collect the level normally; reverse every other level (`[::-1]`) — do not mutate the queue. `[3,9,20,None,None,15,7]` → `[[3],[20,9],[15,7]]`. |
| Vertical Order (LC 314) | Carry a **column index** with each node (`left: c-1`, `right: c+1`); group by column, read columns left to right. `[3,9,20,None,None,15,7]` → `[[9],[3,15],[20],[7]]`. (LC 987 adds a row-then-value sort within a cell.) |
| Average / max / last per level | The same `for _ in range(len(q))` loop with a different aggregate; Right Side View is "last of each level". |
| Boundary / diagonal traversals | Combinations of a left-edge walk, a leaf collection and a right-edge walk; state which edge cases (single child, leaf that is also on an edge) you handle. |

### 11.7 Counting a complete tree in O(log² n) (LC 222)

In a *complete* tree, if the leftmost and rightmost depths of a subtree are equal it is **perfect**, so it has
`2ᵈ − 1` nodes and you never look inside; otherwise recurse. Only one side of each recursion is not perfect, so the
work is `O(h)` per level over `O(h)` levels:

```python
l, r = depth_left(root), depth_right(root)
if l == r: return (1 << l) - 1
return 1 + count_nodes(root.left) + count_nodes(root.right)      # [1,2,3,4,5,6] -> 6
```

### 11.8 The mirror of 016: inorder + postorder (LC 106)

The root is the **last** element of postorder. Because postorder is *left, right, root*, popping from the end meets the
**right** subtree first — so build the right child before the left, or every subtree is swapped:

```python
root = TreeNode(post.pop())
k = idx[root.val]                                # inorder position of the root
root.right = go(k + 1, hi)                       # RIGHT first
root.left  = go(lo, k - 1)
```

Preorder + postorder cannot determine a tree uniquely unless every internal node has two children — the reason LeetCode
gives only the two inorder-based forms (and 889 states its ambiguity).

### 11.9 Arrays and trees

A **complete** tree needs no pointers: node `i` has children `2i + 1` and `2i + 2` and parent `(i - 1) // 2` (this is a
heap's layout, topic 12). A general tree stored the same way wastes `O(2^h)` slots on a skewed shape — the reason
LeetCode's level-order input format includes explicit `null`s. Serialization (019) uses preorder-with-markers instead,
because it needs no padding.

### 11.10 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Do it without recursion." | Explicit stack (Part 2.3); for O(1) space, Morris (11.1). |
| "What if the tree is a straight line?" | Depth `n`: CPython raises `RecursionError` near 1000 frames; convert to an explicit stack. |
| "It is not binary." | Replace `left`/`right` by a `children` list; every pattern carries over (<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> returns aggregate over children). |
| "There are parent pointers." | Then it is a graph: walk up and down (<abbr title="Lowest Common Ancestor. In a tree or directed acyclic graph, the lowest node that has both given nodes as descendants.">LCA</abbr> via two pointers, distance-K without a parent map). |
| "The tree is huge / on disk." | Streaming serialization in preorder; recursion-free traversals; B-trees for disk (topic 11 / SD). |
| "Concurrent modification?" | Traversal needs a snapshot or a lock; Morris is unsafe under concurrency. |
| "Return the *path*, not the sum." | Carry the path list down with push/pop (backtracking), copy at the leaf. |

---
<!-- /block:10_py_1_beyond -->

<!-- problem-map:start -->
## Part 12 · Every Problem in This Topic, by Pattern

Twenty problems, six moves (traversal orders · postorder aggregates · two-tree recursion · level order · down via parameters · tree-as-graph). Each **Trap** is one the tests in that problem's solution file actually trigger.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Binary Tree Preorder Traversal](PyDSA/10_trees/001_binary_tree_preorder_traversal_solution.py) <br>LC 144 · Easy | Preorder | "Preorder" is only the position of the record step relative to the two descents (node, left, right). Iteratively: pop, record, push **right then left**. **Trap:** pushing left first yields a *mirror* traversal that passes `[1]` and `[]` and fails everything else. |
| [002 · Binary Tree Inorder Traversal](PyDSA/10_trees/002_binary_tree_inorder_traversal_solution.py) <br>LC 94 · Easy | Inorder | Record between the descents. Iterative: dive left pushing, pop, record, go right. **Trap:** `while stack:` or `while curr:` instead of `while curr or stack:` (exits too early or misses the right subtree). |
| [003 · Binary Tree Postorder Traversal](PyDSA/10_trees/003_binary_tree_postorder_traversal_solution.py) <br>LC 145 · Easy | Postorder | Record after both descents — children before parent. **Trap:** using the reversed-preorder trick when the *work* must happen bottom-up (the list is right; the visit order is parent-first). |
| [004 · Invert Binary Tree](PyDSA/10_trees/004_invert_binary_tree_solution.py) <br>LC 226 · Easy | Swap the child references | At every node swap the two child pointers, then recurse. **Trap:** two assignments (`left = right; right = left`) — both end up on the original right subtree; use one tuple assignment. |
| [005 · Maximum Depth of Binary Tree](PyDSA/10_trees/005_maximum_depth_of_binary_tree_solution.py) <br>LC 104 · Easy | Postorder height | `1 + max(depth(left), depth(right))`, with `0` for an empty tree. **Trap:** returning `1` for `None`, or forgetting the `1 +` (both off by one). |
| [006 · Minimum Depth of Binary Tree](PyDSA/10_trees/006_minimum_depth_of_binary_tree_solution.py) <br>LC 111 · Easy | Postorder, with a catch | A node with **one** child is not a leaf, so the missing side must not win the `min`. **Trap:** `1 + min(left, right)` treats every one-child node as a leaf (`[1,2]` returns 1, not 2). |
| [007 · Same Tree](PyDSA/10_trees/007_same_tree_solution.py) <br>LC 100 · Easy | Walk two trees at once | Both empty → equal; exactly one empty → not; else compare values and recurse pairwise. **Trap:** comparing traversals (`[1,2]` vs `[1,null,2]`); reading `.val` before the `None` checks. |
| [008 · Subtree of Another Tree](PyDSA/10_trees/008_subtree_of_another_tree_solution.py) <br>LC 572 · Easy | Same Tree at every node | "Subtree" means a node with *all* its descendants: is there a node from which the two trees are identical? **Trap:** matching a pattern instead of a whole subtree; forgetting the `if not root` base case. |
| [009 · Balanced Binary Tree](PyDSA/10_trees/009_balanced_binary_tree_solution.py) <br>LC 110 · Easy | Height with an early exit | Balance is a property of **every** node: compute heights bottom-up and return a sentinel (`-1`) the moment any node is unbalanced. **Trap:** checking only the root's two children. |
| [010 · Diameter of Binary Tree](PyDSA/10_trees/010_diameter_of_binary_tree_solution.py) <br>LC 543 · Easy | Postorder with a side channel | Every path has exactly one turning point, so at each node candidate = `hL + hR`; return `1 + max(hL, hR)` to the parent. **Trap:** returning the candidate instead of the height; mixing edge-count and node-count conventions. |
| [011 · Path Sum](PyDSA/10_trees/011_path_sum_solution.py) <br>LC 112 · Easy | Down via a parameter | Carry `remaining` *down* (return values only go up); test at **leaves**, after subtracting the node's value. **Trap:** checking `remaining == 0` at any node; subtracting after the leaf test. |
| [012 · Symmetric Tree](PyDSA/10_trees/012_symmetric_tree_solution.py) <br>LC 101 · Easy | Crossed two-tree recursion | Symmetric = left and right subtrees are *mirrors*: compare `left.left` with `right.right` and `left.right` with `right.left`. **Trap:** reusing 007 (`same(left, right)`) — same-side pairing is stricter than mirroring. |
| [013 · Binary Tree Level Order Traversal](PyDSA/10_trees/013_binary_tree_level_order_traversal_solution.py) <br>LC 102 · Medium | Level-size loop | A queue already visits in level order; the invariant is "at the top of each outer iteration the queue holds exactly one level". **Trap:** an inner `while q:` (children are drained into the same level); re-reading `len(q)` inside the loop. |
| [014 · Binary Tree Right Side View](PyDSA/10_trees/014_binary_tree_right_side_view_solution.py) <br>LC 199 · Medium | Last node per level | The answer is a *level* property, not a pointer property: the last node of each level (<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>), or <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> right-first recording the first arrival per depth. **Trap:** following `.right` from the root (fails `[1,2,3,4]`); left-first <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> gives the *left* view. |
| [015 · Count Good Nodes in Binary Tree](PyDSA/10_trees/015_count_good_nodes_in_binary_tree_solution.py) <br>LC 1448 · Medium | Max-so-far down the path | "Good" is a property of a node's ancestors, so pass the path maximum down as a parameter. **Trap:** `>` instead of `>=` (an equal value is still good); comparing with the *parent* instead of the path maximum. |
| [016 · Construct Binary Tree from Preorder and Inorder Traversal](PyDSA/10_trees/016_construct_binary_tree_from_preorder_and_inorder_traversal_solution.py) <br>LC 105 · Medium | Split by the root | Preorder's first element is the root; its position in inorder splits the two subtrees; use an index map for O(n). **Trap:** `preorder[1:k]` instead of `[1:k+1]`; using the inorder index `k` to slice preorder without re-basing. |
| [017 · Lowest Common Ancestor of a Binary Tree](PyDSA/10_trees/017_lowest_common_ancestor_of_a_binary_tree_solution.py) <br>LC 236 · Medium | Overloaded return value | The recursion returns "p or q found below me", and the first node that sees both sides is the <abbr title="Lowest Common Ancestor. In a tree or directed acyclic graph, the lowest node that has both given nodes as descendants.">LCA</abbr>. **Trap:** only handling p and q in *different* subtrees (fails when one is the other's ancestor); comparing values instead of identity. |
| [018 · Binary Tree Maximum Path Sum](PyDSA/10_trees/018_binary_tree_maximum_path_sum_solution.py) <br>LC 124 · Hard | Gain vs through-value | A path is a "V" with one turning point: **record** `val + left + right`, **return** `val + max(left, right)`, and clamp negative gains to 0. **Trap:** returning the through-value (a fork that does not exist); recording the gain (never sees a V — `[1,2,3]` gives 3, not 6). |
| [019 · Serialize and Deserialize Binary Tree](PyDSA/10_trees/019_serialize_and_deserialize_binary_tree_solution.py) <br>LC 297 · Hard | Preorder with null markers | Preorder plus explicit nulls is unambiguous; deserialize by consuming tokens from an iterator. **Trap:** no null markers (`[1,2]` and `[1,null,2]` collide); a delimiter that can appear in the data. |
| [020 · All Nodes Distance K in Binary Tree](PyDSA/10_trees/020_all_nodes_distance_k_in_binary_tree_solution.py) <br>LC 863 · Medium | Tree as an undirected graph | Add the upward edges with a parent map, then <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> from the target for exactly `k` levels. **Trap:** <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> without a `visited` set (walks target → child → parent back to target); draining all nodes in one loop and losing the distance. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] I can write all three <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> orders recursively from memory, and state in
      one sentence what distinguishes each (§2.1).
- [ ] I can write inorder traversal iteratively with an explicit stack,
      without looking it up (§2.3).
- [ ] I know Python's recursion limit is a real, hittable constraint on
      skewed trees, and I know the iterative fix (§2.2).
- [ ] I can write level-order <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> using `collections.deque`, including the
      `level_size` snapshot trick (Part 3).
- [ ] I can state why <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> space is O(width) while <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> space is O(height),
      and that these can differ by orders of magnitude (§3.1).
- [ ] Before writing any tree recursion, I ask: does this node's answer
      depend on ancestors (parameter, down) or descendants (return value,
      up)? (§4.3)
- [ ] I can write the `nonlocal`-closure idiom for diameter/max-path-sum
      from scratch, and I know why forgetting `nonlocal` raises
      `UnboundLocalError` specifically (§5.1-§5.2).
- [ ] I can name the two alternatives to `nonlocal` (mutable box, tuple
      return) and state one tradeoff each (§5.3-§5.4).
- [ ] I can recognize when a "tree" problem is secretly <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>, a graph problem,
      a prefix-sum problem, or a backtracking problem, from the shape of
      what the recursion computes (Part 6).
</content>
- [ ] Write Morris inorder and say what it costs (temporary mutation, not concurrency-safe) <!--ca-->
- [ ] Write a genuinely bottom-up iterative postorder with a `last` pointer <!--ca-->
- [ ] Solve Path Sum III with a prefix-sum map, including the un-increment on the way up <!--ca-->
- [ ] Return a *pair* for a tree <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> (House Robber III) and explain the two states <!--ca-->
- [ ] Build from inorder + postorder, and say why the **right** child is built first <!--ca-->

---

## Part 13 · Added Problem (020) — When a Tree Must Be Treated as a Graph

**020 All Nodes Distance K in Binary Tree** (added 16 Sep 2026, Python + Go).

Every other problem in this folder moves DOWN (children) or passes information UP through return
values. Distance K needs to walk UP through parents as a path step. A tree node doesn't store that edge,
so add it:

```
parent = {child: node}          # one traversal
BFS from target over (left, right, parent[node]) with a visited set, for exactly k levels
```

The visited set is new for this topic: plain tree traversals never revisit a node, but once parent
edges exist, `target -> child -> parent` returns to target. Without it the example returns the target
itself at "distance 2".

The Go version keys the map by `*TreeNode` (pointer identity) and reads a missing parent as `nil` for
free (zero values). The recursive <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> alternative runs fine on a 200,000-deep path in Go (growable
goroutine stacks) — the same recursion raises RecursionError in CPython past ~1000 frames.

### Checklist additions

- [ ] I can convert a tree to an undirected graph with a parent map and <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> by levels.
- [ ] I can explain why visited is required once parent edges are added.
