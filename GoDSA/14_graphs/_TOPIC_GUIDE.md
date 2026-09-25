# Topic 14 · Graphs — Go Deep Dive

> A graph is just nodes and edges, but *how you represent them* dictates every
> constant factor that follows. Go gives you three honest choices — a map, a
> slice of slices, or a matrix — with no framework hiding the tradeoff. Pick
> wrong and a <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> that should run in milliseconds spends its time hashing
> integers. This is the document that makes the choice deliberate.

---

## Part 1 · Representing the Graph

### 1.1 Three representations, three tradeoffs

```go
// 1. Adjacency list, map-backed — flexible, handles sparse/non-contiguous IDs
adj := make(map[int][]int)
adj[u] = append(adj[u], v)

// 2. Adjacency list, slice-backed — fast, requires dense 0..n-1 node IDs
adj := make([][]int, n)
adj[u] = append(adj[u], v)

// 3. Adjacency matrix — O(1) edge lookup, O(V²) space
adj := make([][]bool, n)
for i := range adj {
    adj[i] = make([]bool, n)
}
adj[u][v] = true
```

| Representation | Edge lookup | Space | Iterate neighbors | When |
|---|:--:|:--:|:--:|---|
| `map[int][]int` | O(1) avg, hashing cost | O(V+E) | O(deg) | Node IDs sparse, non-integer, or unknown up front |
| `[][]int` | — (no direct lookup) | O(V+E) | O(deg) | Node IDs are dense `0..n-1` — **default choice for LeetCode graph problems** |
| `[][]bool` matrix | **O(1)** | **O(V²)** | O(V) — must scan a row | Dense graphs, or when "is there an edge?" dominates over "list all edges" |

> ✅ **Default to `[][]int`.** Almost every LeetCode graph problem hands you
> `n` and a 0-indexed node range. A slice-of-slices avoids Go's map hashing
> overhead entirely (recall Topic 1 §2.1: every map access walks bucket +
> tophash machinery) and gives you direct index access. Reach for
> `map[int][]int` only when node identities are sparse or non-numeric (e.g.
> string-keyed graphs, or node IDs that aren't contiguous).

### 1.2 Building the list from an edge list

```go
func buildGraph(n int, edges [][]int, directed bool) [][]int {
    adj := make([][]int, n)
    for _, e := range edges {
        u, v := e[0], e[1]
        adj[u] = append(adj[u], v)
        if !directed {
            adj[v] = append(adj[v], u)
        }
    }
    return adj
}
```

`make([][]int, n)` allocates `n` nil slices — each is a valid, appendable
empty slice (Topic 1 §1.5), so no per-node initialization loop is needed
before the `append` calls above.

---

## Part 2 · Breadth-First Search

### 2.1 The template

```go
func bfs(adj [][]int, start int) []int {
    n := len(adj)
    visited := make([]bool, n)   // dense integer IDs → array, not map
    order := make([]int, 0, n)

    queue := []int{start}
    visited[start] = true        // ⚠️ mark on enqueue, not on dequeue

    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]        // O(1) header-only pop; fine for a one-shot BFS
        order = append(order, node)

        for _, next := range adj[node] {
            if !visited[next] {
                visited[next] = true   // mark here
                queue = append(queue, next)
            }
        }
    }
    return order
}
```

`visited []bool` over `visited map[int]bool` is the same tradeoff as Topic
1's `[26]int` frequency array vs `map[byte]int`: with dense integer node IDs,
an array index is a memory offset — a map lookup is a hash, a bucket walk,
and a `tophash` byte-compare (Topic 1 §2.1). Use a map only when node IDs
aren't small dense integers.

> ⚠️ **Mark visited at enqueue time, not dequeue time.** If you instead check
> `visited` only when a node is *dequeued* and processed, the same node can be
> pushed onto the queue multiple times by different neighbors before it's
> ever processed — each duplicate wastes a full neighbor-scan, and on a dense
> graph this degrades <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> from O(V+E) toward O(E·V) in the worst case. Marking
> at enqueue guarantees each node enters the queue exactly once.

Regarding the queue itself: `queue = queue[1:]` leaks backing-array capacity
the way Topic 7 describes, but a <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> runs to completion in one call and the
whole slice is garbage the moment the function returns — the leak never has
time to matter. Reach for a ring buffer only if you're running <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>
repeatedly inside a long-lived process.

---

```arch
%% caption: From A: BFS visits by distance (A, B, C, D, E, F) using a queue. DFS dives first (A, B, D, F, E, C) using a stack or recursion. Both need a visited set, or the cycle A-B-D-F-E-C loops forever.
route straight
grid 100x80
node a "A" at 0,1 shape=circle color=blue
node b "B" at 1,0 shape=circle color=blue
node c "C" at 1,2 shape=circle color=blue
node d "D" at 2,0 shape=circle color=blue
node e "E" at 2,2 shape=circle color=blue
node f "F" at 3,1 shape=circle color=blue
a -- b
a -- c
b -- d
c -- e
d -- f
e -- f
```

## Part 3 · Depth-First Search

### 3.1 Recursive — natural, but bounded by stack depth

```go
func dfs(adj [][]int, node int, visited []bool, order *[]int) {
    visited[node] = true
    *order = append(*order, node)
    for _, next := range adj[node] {
        if !visited[next] {
            dfs(adj, next, visited, order)
        }
    }
}
```

Recursive <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> is the idiomatic first reach in Go — but recall Topic 9's
warning: **Go performs no tail-call optimization**, and a goroutine's stack,
while growable (starts at 2 KB, grows by copy-and-double to a configurable max — 1 GB by
default on 64-bit), is not unbounded. A <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> on a graph containing a long
simple path (in the worst case, V nodes chained in a line) recurses V deep.
For V in the tens of thousands this is usually fine; for adversarial or
very large inputs, prefer the iterative form below.

### 3.2 Iterative — an explicit stack, and a subtle ordering difference

```go
func dfsIterative(adj [][]int, start int) []int {
    n := len(adj)
    visited := make([]bool, n)
    order := make([]int, 0, n)

    stack := []int{start}
    for len(stack) > 0 {
        node := stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        if visited[node] {
            continue
        }
        visited[node] = true
        order = append(order, node)

        for _, next := range adj[node] {
            if !visited[next] {
                stack = append(stack, next)
            }
        }
    }
    return order
}
```

> ⚠️ **Recursive and iterative <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> don't visit neighbors in the same order.**
> Recursive <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> fully explores `adj[node][0]` before ever looking at
> `adj[node][1]`. The stack version pushes all neighbors first, then pops the
> *last* one pushed — so it explores `adj[node][len-1]` first. Both are valid
> <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> orderings, but if a problem's expected output depends on traversal
> order (rare, but it happens with "print the path" style problems), pick the
> form that matches, or reverse the neighbor slice before pushing.

Note also the iterative version checks `visited` *after* popping, not before
pushing — a node can be pushed multiple times (once per incoming edge) before
it's first popped; the post-pop check discards the duplicates. This is the
opposite convention from <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>'s enqueue-time marking, and mixing the two up
is an easy way to introduce a bug when porting a <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> solution to <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>.

---

## Part 4 · Union-Find (Disjoint Set Union)

### 4.1 Why it exists

Union-Find answers "are these two nodes in the same connected component?" and
"merge these two components" — both in near-constant time, without ever
walking a full <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> per query. It is the tool of choice whenever edges
arrive one at a time and you need running connectivity (Kruskal's <abbr title="Minimum Spanning Tree. A subset of the edges of a connected, edge-weighted undirected graph that connects all vertices with the minimum possible total edge weight.">MST</abbr>,
redundant-connection problems, accounts-merge, cycle detection below).

### 4.2 Two optimizations, stacked

```go
type UnionFind struct {
    parent []int
    rank   []int // approximate tree height, for union by rank
}

func NewUnionFind(n int) *UnionFind {
    parent := make([]int, n)
    for i := range parent {
        parent[i] = i // each node starts as its own root
    }
    return &UnionFind{parent: parent, rank: make([]int, n)}
}

// Find returns the root of x's component, flattening the path as it goes.
func (uf *UnionFind) Find(x int) int {
    if uf.parent[x] != x {
        uf.parent[x] = uf.Find(uf.parent[x]) // path compression
    }
    return uf.parent[x]
}

// Union merges the components containing x and y. Returns false if they
// were already connected (i.e. this edge would create a cycle).
func (uf *UnionFind) Union(x, y int) bool {
    rootX, rootY := uf.Find(x), uf.Find(y)
    if rootX == rootY {
        return false
    }
    // union by rank: attach the shorter tree under the taller one's root
    if uf.rank[rootX] < uf.rank[rootY] {
        rootX, rootY = rootY, rootX
    }
    uf.parent[rootY] = rootX
    if uf.rank[rootX] == uf.rank[rootY] {
        uf.rank[rootX]++
    }
    return true
}

func (uf *UnionFind) Connected(x, y int) bool {
    return uf.Find(x) == uf.Find(y)
}
```

**Path compression**, visualized — `Find(4)` on a chain `4→3→2→1→0` rewires
every visited node to point straight at the root:

```
Before Find(4):        4 → 3 → 2 → 1 → 0

During the recursive unwind, each node's parent is reassigned to the root:

After Find(4):         4 ─┐
                        3 ─┼→ 0
                        2 ─┤
                        1 ─┘
```

Every future `Find` on 1, 2, 3, or 4 is now O(1). **Union by rank** prevents
the chain from forming in the first place, by always hanging the shorter
tree under the taller one's root rather than arbitrarily. Together, the two
optimizations give amortized **O(α(n))** per operation — α is the inverse
Ackermann function, which is ≤ 4 for any n that fits in the universe. In
practice: treat Union-Find as O(1).

> ⚡ Either optimization alone already gives good performance (path
> compression alone is O(log n) amortized); using **both together** is what
> produces the α(n) bound. Always implement both — it's the same amount of
> code either way.

---

## Part 5 · Cycle Detection

### 5.1 Undirected graphs

Two approaches:

1. **Union-Find**: process edges one at a time; if `Union(u, v)` returns
   `false`, `u` and `v` were already connected — this edge closes a cycle.
2. **<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> with parent tracking**: a visited neighbor that *isn't* the node you
   just came from indicates a cycle.

```go
func hasCycleUndirected(adj [][]int, node, parent int, visited []bool) bool {
    visited[node] = true
    for _, next := range adj[node] {
        if !visited[next] {
            if hasCycleUndirected(adj, next, node, visited) {
                return true
            }
        } else if next != parent {
            return true // reached an already-visited node that isn't our parent
        }
    }
    return false
}
```

> ⚠️ **The parent check is mandatory for undirected graphs.** An undirected
> edge `u↔v` is stored as `v` in `adj[u]` *and* `u` in `adj[v]`. Without
> excluding `parent`, <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> immediately "rediscovers" the edge it just walked
> and reports a false cycle on every single edge.

### 5.2 Directed graphs — parent-tracking isn't enough

A directed graph needs three states, not two, because a node can be
"finished" (fully explored, safe to revisit via a different path) without
that being a cycle — only revisiting a node **still on the current recursion
stack** is a cycle:

```go
const (
    white = 0 // unvisited
    gray  = 1 // on the current DFS path (recursion stack)
    black = 2 // fully explored
)

func hasCycleDirected(adj [][]int, node int, color []int) bool {
    color[node] = gray
    for _, next := range adj[node] {
        if color[next] == gray {
            return true // back-edge to a node on the current stack: cycle
        }
        if color[next] == white && hasCycleDirected(adj, next, color) {
            return true
        }
    }
    color[node] = black
    return false
}
```

> This is the point that trips people up: in an undirected graph, "visited
> and not my parent" is sufficient because every non-tree edge you encounter
> that isn't the reverse of the one you arrived on closes a cycle. In a
> directed graph, an edge to an already-**black** node is a perfectly normal
> cross-edge or forward-edge — not a cycle — because the graph's edges are
> one-directional. Only gray (currently-on-the-stack) targets indicate a
> cycle. Conflating the two schemes is the single most common graph-<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> bug.

---

## Part 6 · Bipartite Check

Two-color the graph during <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> or <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>; a conflict (a neighbor already colored
the *same* color) means the graph isn't bipartite:

```go
func isBipartite(adj [][]int) bool {
    n := len(adj)
    color := make([]int, n) // 0 = uncolored, 1 or -1 = the two colors
    for start := 0; start < n; start++ {
        if color[start] != 0 {
            continue // already colored via an earlier component
        }
        color[start] = 1
        queue := []int{start}
        for len(queue) > 0 {
            node := queue[0]
            queue = queue[1:]
            for _, next := range adj[node] {
                if color[next] == 0 {
                    color[next] = -color[node]
                    queue = append(queue, next)
                } else if color[next] == color[node] {
                    return false
                }
            }
        }
    }
    return true
}
```

The outer `for start := range` loop matters: the graph may be disconnected,
and each component must be colored independently.

---

## Part 7 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Adjacency list | `defaultdict(list)` — always map-backed | `[][]int` preferred for dense IDs — no hashing |
| Visited set | `set()` | `[]bool` for dense IDs, `map[int]bool` for sparse |
| Queue for <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> | `collections.deque` — true O(1) both ends | Slice with `s[1:]` (fine for one-shot <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>) or a ring buffer (Topic 7) |
| Recursion depth | `sys.setrecursionlimit`, fixed C-stack ceiling | Growable goroutine stack (starts at 2 KB, grows to ~1 GB default) |
| Union-Find | Hand-rolled (no stdlib) | Hand-rolled (no stdlib) — parity here, unusually |
| Graph library | `networkx` for prototyping | None in stdlib — everything is hand-rolled |

Both languages lack a standard graph library, but Python's dynamic `dict`
and `set` make ad-hoc sparse graphs slightly more convenient to bang out;
Go's payoff is a faster, allocation-lighter traversal once you commit to
dense integer IDs and slices.

---

## Part 8 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> (shortest path, unweighted) | O(V+E) | O(V) | LC 200 Number of Islands, LC 133 Clone Graph |
| <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> (recursive or iterative) | O(V+E) | O(V) | LC 200, LC 695 Max Area of Island |
| Union-Find with path compression + union by rank | O(α(n)) amortized/op | O(V) | LC 547 Number of Provinces, LC 684 Redundant Connection |
| Cycle detection (undirected, Union-Find or <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>+parent) | O(V+E) | O(V) | LC 684 |
| Cycle detection (directed, 3-color <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>) | O(V+E) | O(V) | LC 207 Course Schedule (cycle-free check) |
| Bipartite check (2-coloring) | O(V+E) | O(V) | LC 785 Is Graph Bipartite? |

Dijkstra, topological sort (Kahn's/<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>-based), Bellman-Ford, Floyd-Warshall,
and <abbr title="Minimum Spanning Tree. A subset of the edges of a connected, edge-weighted undirected graph that connects all vertices with the minimum possible total edge weight.">MST</abbr> (Kruskal/Prim) build directly on the representations and Union-Find
structure here — see `15_advanced_graphs`.

---

## Part 9 · Building Union-Find + Grid <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> From Scratch

```go
package main

// UnionFind — see Part 4 for full annotated version.
type UnionFind struct {
    parent []int
    rank   []int
}

func NewUnionFind(n int) *UnionFind {
    parent := make([]int, n)
    for i := range parent {
        parent[i] = i
    }
    return &UnionFind{parent: parent, rank: make([]int, n)}
}

func (uf *UnionFind) Find(x int) int {
    if uf.parent[x] != x {
        uf.parent[x] = uf.Find(uf.parent[x])
    }
    return uf.parent[x]
}

func (uf *UnionFind) Union(x, y int) bool {
    rootX, rootY := uf.Find(x), uf.Find(y)
    if rootX == rootY {
        return false
    }
    if uf.rank[rootX] < uf.rank[rootY] {
        rootX, rootY = rootY, rootX
    }
    uf.parent[rootY] = rootX
    if uf.rank[rootX] == uf.rank[rootY] {
        uf.rank[rootX]++
    }
    return true
}

// numIslands (LC 200): grid BFS reusing the visited-on-enqueue pattern
// from Part 2, adapted to 2D coordinates flattened to a single int ID
// (row*cols+col) so a plain []bool works instead of a map[[2]int]bool.
func numIslands(grid [][]byte) int {
    rows, cols := len(grid), len(grid[0])
    visited := make([]bool, rows*cols)
    dirs := [4][2]int{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}

    bfs := func(r, c int) {
        queue := [][2]int{{r, c}}
        visited[r*cols+c] = true
        for len(queue) > 0 {
            cell := queue[0]
            queue = queue[1:]
            for _, d := range dirs {
                nr, nc := cell[0]+d[0], cell[1]+d[1]
                if nr < 0 || nr >= rows || nc < 0 || nc >= cols {
                    continue
                }
                idx := nr*cols + nc
                if !visited[idx] && grid[nr][nc] == '1' {
                    visited[idx] = true
                    queue = append(queue, [2]int{nr, nc})
                }
            }
        }
    }

    count := 0
    for r := 0; r < rows; r++ {
        for c := 0; c < cols; c++ {
            if grid[r][c] == '1' && !visited[r*cols+c] {
                count++
                bfs(r, c)
            }
        }
    }
    return count
}
```

**Talk track while writing:** flatten `(row, col)` to `row*cols+col` so
`visited` can be a `[]bool` instead of a `map[[2]int]bool` — same
array-over-map tradeoff as everywhere else in this guide; mark visited at
enqueue time to avoid double-queuing a cell; Union-Find's `Find` recurses
but path-compresses on the way back up, so subsequent calls on the same
subtree are O(1).

---

<!-- block:14_go_1_topo -->
## Part 10 · Directed Graphs in Go: Cycle Detection and Topological Order

The Go guide so far covers representation, <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>, undirected cycles and bipartite checks. **Directed** graphs — course
schedules, build orders, dependency resolution — need two more tools, and they are the same question asked twice: *is
there a cycle?* and *what order respects every edge?* All code below ran on Go 1.24.5 against LeetCode's own examples.

```arch
%% caption: Cycle detection and topological sort are one question. Kahn's algorithm peels off nodes with no unmet dependency; if it cannot peel them all, a cycle is holding the rest.
grid 200x90
node a "Build adj and indegree" at 0,0 shape=pill w=260 sub="edge [a, b] = b must come before a: b -> a"
node b "Queue all nodes with indegree 0" at 0,1 w=230
node c "Queue empty?" at 0,2 shape=diamond color=amber
node d "Pop u, append to order" at 0,3 w=230
node e "For each v in adj[u]: indegree[v]--" at 0,4 color=amber w=240 sub="if it hits 0, enqueue v"
node f "len(order) == n?" at 1,2 shape=diamond color=amber
node g "Valid order: no cycle" at 2,2 color=green w=170
node h "A cycle left nodes stuck" at 1,3 color=red w=200 sub="at indegree > 0: NOT schedulable"
a -> b -> c
c -> d : "no"
d -> e
e:L -> c:L
c -> f : "yes"
f -> g : "yes"
f -> h : "no"
```

### Kahn's algorithm — <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> on in-degree

```go
func topoOrder(n int, prereq [][]int) ([]int, bool) {
    adj := make([][]int, n)
    indeg := make([]int, n)
    for _, p := range prereq {                     // [a, b]: b must come BEFORE a  =>  the edge is b -> a
        adj[p[1]] = append(adj[p[1]], p[0])
        indeg[p[0]]++
    }
    queue := make([]int, 0, n)
    for i, d := range indeg { if d == 0 { queue = append(queue, i) } }
    order := make([]int, 0, n)
    for len(queue) > 0 {
        u := queue[0]; queue = queue[1:]
        order = append(order, u)
        for _, v := range adj[u] {
            if indeg[v]--; indeg[v] == 0 { queue = append(queue, v) }     // decrement, then test, in one statement
        }
    }
    return order, len(order) == n                  // fewer than n: a cycle left some nodes stuck
}                                                  // (4, [[1 0] [2 0] [3 1] [3 2]]) -> [0 1 2 3] true   (2, [[1 0] [0 1]]) -> [] false
```

Two bugs recur. **Building the edges backwards** — `[a, b]` means *b before a*, so the edge is `b → a`; reversed, you
detect cycles in (and order) the wrong graph. And **returning `order` without checking `len(order) == n`** hands back a
partial order for a cyclic graph. `if indeg[v]--; indeg[v] == 0` uses Go's `if` *init statement* — the decrement happens,
then the condition tests the new value.

### Three-colour <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> — why one `visited` is not enough

In a *directed* graph, reaching an already-visited node is **not** a cycle: two different chains can converge on the same
downstream node. You need to know whether it is on the **current path**:

```go
const ( white = iota; gray; black )                // unvisited / on the current DFS path / fully explored
state := make([]int, n)
var dfs func(u int) bool                           // true if a cycle is reachable from u
dfs = func(u int) bool {
    state[u] = gray
    for _, v := range adj[u] {
        if state[v] == gray || (state[v] == white && dfs(v)) { return true }   // gray: a BACK edge = a cycle
    }
    state[u] = black
    return false
}
```

`black` means "explored, no cycle through me" — reaching one again is fine. A single `visited []bool` reports a false cycle
on `1→2, 1→3, 2→4, 3→4` (a diamond). The <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> finish order, **reversed**, is also a valid topological order — the <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>-based
alternative to Kahn's.

### Reachability and degree puzzles

- **Eventual Safe States (LC 802):** reverse the graph and run Kahn's algorithm on **out-degrees** — terminals
  (out-degree 0) are safe; when a node's last outgoing neighbour becomes safe, so does it. `[[1 2] [2 3] [5] [0] [5] [] []]`
  → `[2 4 5 6]`.
- **Course Schedule I / II:** `topoOrder` is Course Schedule II; `_, ok := topoOrder(...)` is Course Schedule I.
- **Find the Town Judge:** no traversal — the judge has `in-degree − out-degree == n − 1`.
- **Alien Dictionary (topic 15):** derive edges from adjacent words, then Kahn's — with an explicit check for the invalid
  prefix case (`"abc"` before `"ab"`).

---
<!-- /block:14_go_1_topo -->

<!-- block:14_go_2_grids -->
## Part 11 · Grids, Copies and Implicit Graphs in Go

### The grid as a graph: flatten, direction arrays, mark on enqueue

Every grid problem is a graph problem with four (or eight) implicit edges per cell. Three Go idioms make them short:

- a direction table as a **value array** — `[4][2]int{{1, 0}, {-1, 0}, {0, 1}, {0, -1}}` — allocated on the stack, ranged
  over with no `make`;
- a **flat index** `r*cols + c` so `visited` is a `[]bool` instead of a `map[[2]int]bool` (Part 9);
- **mark visited when you enqueue**, never when you dequeue — otherwise a cell is queued once per neighbour.

### Multi-source <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>: seed *everything* at once (01 Matrix, Walls and Gates, Rotting Oranges)

"Distance to the *nearest* X" is one <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> started from **all** the X's simultaneously: the first time a cell is reached is
its nearest source. O(R·C) total — one <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> per source is O(sources · R · C):

```go
for r := range dist {
    for c := range dist[r] {
        if mat[r][c] == 0 { q = append(q, [2]int{r, c}) } else { dist[r][c] = -1 }   // -1 = "not reached yet"
    }
}
for len(q) > 0 {
    cur := q[0]; q = q[1:]
    for _, d := range [4][2]int{{1, 0}, {-1, 0}, {0, 1}, {0, -1}} {
        nr, nc := cur[0]+d[0], cur[1]+d[1]
        if nr >= 0 && nr < R && nc >= 0 && nc < C && dist[nr][nc] == -1 {
            dist[nr][nc] = dist[cur[0]][cur[1]] + 1
            q = append(q, [2]int{nr, nc})
        }
    }
}                                                  // [[0 0 0] [0 1 0] [1 1 1]] -> [[0 0 0] [0 1 0] [1 2 1]]
```

For "minutes until everything rots", count **levels**, not cells: `for size := len(q); size > 0; size--` freezes the level
before you enqueue the next one. Incrementing the answer on every dequeue turns "minutes" into "cells processed".

### Clone Graph: pointers are identity keys

`map[*Node]*Node` maps each original to its clone — pointer equality is exactly the identity you need. Register the clone
**before** recursing into its neighbours, or a cycle recurses forever:

```go
clones := map[*Node]*Node{}
var dfs func(*Node) *Node
dfs = func(n *Node) *Node {
    if c, ok := clones[n]; ok { return c }         // already cloned: reuse THE clone, not a new one
    c := &Node{Val: n.Val}
    clones[n] = c                                  // register BEFORE the neighbours
    for _, nb := range n.Neighbors { c.Neighbors = append(c.Neighbors, dfs(nb)) }
    return c
}
```

A `set` of visited originals cannot say *which* clone to reuse; that is why it must be a map.

### Word Ladder: group by wildcard pattern

Comparing every pair of words is O(n²·L). Instead bucket words by pattern — `hot` → `*ot`, `h*t`, `ho*` — so a word's
neighbours are the union of three bucket lookups, O(L) per word. Deleting a bucket after it is expanded once keeps the
<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> linear:

```go
for i := range w {
    p := w[:i] + "*" + w[i+1:]                     // string slices are free headers; the concatenation allocates
    for _, nb := range patterns[p] { if !seen[nb] { seen[nb] = true; q = append(q, nb) } }
    delete(patterns, p)                            // each bucket needs expanding only once
}                                                  // hit → cog: 5     (without "cog" in the list: 0)
```

### Open the Lock: an implicit graph, and bidirectional <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>

The graph is never built: a state is a 4-digit number and `neighbors(state)` generates the eight moves. With states as
`int`s, `visited` and `dead` are `[10000]bool` value arrays; digit `pos` is `cur / p % 10` with `p = 10^pos`:

```go
for pos, p := 0, 1; pos < 4; pos, p = pos+1, p*10 {
    digit := cur / p % 10
    for _, delta := range [2]int{1, 9} {           // +1 and -1 (mod 10) — 9 avoids a negative modulus
        next := cur - digit*p + (digit+delta)%10*p
        if !seen[next] && !dead[next] { seen[next] = true; q = append(q, next) }
    }
}
```

Check that `"0000"` itself is not a dead end, or <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> returns a number instead of `-1`. **Bidirectional <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>** expands from
both start and goal and stops when the frontiers touch; each round expand the **smaller** frontier. Nodes expanded on
this 10,000-state graph (plain <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> vs bidirectional; the bidirectional count can vary by one with Go's random map
iteration order):

| Case | Plain <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> | Bidirectional |
|---|---:|---:|
| the LeetCode example (`0202`, 5 deadends, answer 6) | 822 | 45–46 |
| `5555`, no deadends (answer 20) | 10,000 | 7,491 |
| `8888` walled in by its 8 neighbours (answer −1) | 9,991 | **2** |

It needs reversible moves and unweighted edges; the saving is large when either side is constrained and enormous when the
goal is unreachable.

### Shortest Path in Binary Matrix: eight directions

```go
for dr := -1; dr <= 1; dr++ {
    for dc := -1; dc <= 1; dc++ {                  // (0,0) is harmless: the cell is already marked
        nr, nc := cur.r+dr, cur.c+dc
        if nr >= 0 && nr < n && nc >= 0 && nc < n && grid[nr][nc] == 0 { grid[nr][nc] = 1; q = append(q, cell{nr, nc, cur.d + 1}) }
    }
}
```

Copying the 4-direction list from an earlier problem is the classic bug, and both corners must be `0` up front. Marking by
overwriting the input (`grid[nr][nc] = 1`) mutates the caller's grid — acceptable when stated, or clone first.

### Pacific Atlantic: flood from the *oceans*, uphill

Flowing *down* from every cell is O(R·C) searches. Reverse it: flood **uphill** from each ocean's border cells (rule
`neighbour >= current` — the *reverse* of the flow rule `<=`) and intersect the two reachable sets. Using the forward rule
in the reverse flood computes the wrong question. The 5×5 LeetCode example yields
`[[0 4] [1 3] [1 4] [2 2] [3 0] [3 1] [4 0]]`. **Surrounded Regions** is the same trick — flood from the *border* and flip
what the border cannot reach.

### Graph Valid Tree, and Distinct Islands

A tree has **exactly `n − 1` edges *and* is connected** — each alone is insufficient (`n − 1` edges can be two pieces; a
connected graph can hold a cycle):

```go
if len(edges) != n-1 { return false }
... DFS from 0 ...
return count == n                                  // (5, [[0 1] [0 2] [0 3] [1 4]]) true   a cycle → false   two pieces → false
```

**Distinct Islands** keys each island by its shape with coordinates *relative to its first cell* — a `strings.Builder`
turned into a `map[string]bool` key — so identical shapes at different places collapse to one:

```go
fmt.Fprintf(&sb, "%d,%d;", r-r0, c-c0)             // relative coordinates
shapes[sb.String()] = true                          // example 1 -> 1 shape, example 2 -> 3
```

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| `visited` as a `map[[2]int]bool` on a big grid | Hashing on every cell — measurably slower. | Flatten to `r*cols + c` and use `[]bool`. |
| Marking visited on dequeue | A cell is queued once per neighbour. | Mark on enqueue. |
| A single `visited []bool` for *directed* cycles | A diamond is reported as a cycle. | Three states (white/gray/black), or Kahn. |
| Edge direction reversed (`[a, b]`) | Orders the wrong graph. | `[a, b]` means `b → a`; write it in a comment. |
| Recursive <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> on a `10⁶`-cell island | Deep recursion — Go's stack grows (1 GB ceiling) but overflow is fatal and unrecoverable. | An explicit stack, or <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>. |
| Mutating the input grid as `visited` | The caller's data is changed. | State it, clone, or use a separate `[]bool`. |
| Ranging a `map[string][]string` while deleting keys | Legal in Go, but the iteration is random. | Fine here (Word Ladder deletes by key, not while ranging). |
| `strings.Builder` shared across islands | Stale shape from the previous island. | `sb.Reset()` before each island. |

### Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Print the path." | Keep `parent []int` (<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>) and walk it back from the target; reverse with `slices.Reverse`. |
| "Doesn't fit in memory." | Distributed <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> by frontier, partition by node id, or an implicit graph generated on the fly. |
| "Weighted edges." | 0/1 → 0-1 <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> (deque); non-negative → Dijkstra (`container/heap`, topic 15); negative → Bellman-Ford. |
| "Count the paths." | <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> in topological order on a <abbr title="Directed Acyclic Graph. A directed graph with no directed cycles, consisting of vertices and edges where each edge is directed from one vertex to another.">DAG</abbr>, or memoised <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>. |
| "Why <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> for shortest paths?" | Level order: every node is first reached by a fewest-edges path (unweighted only). |
| "Concurrent traversal." | Expand a frontier in parallel chunks with a shared visited set using atomic test-and-set. |

---
<!-- /block:14_go_2_grids -->

<!-- problem-map:start -->
## Part 12 · Every Problem in This Topic, by Pattern

Eighteen problems, seven moves (flood fill · components · clone/copy · multi-source <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> · directed cycles and topological order · tree/bipartite tests · implicit graphs) — the Python guide's map in Go, with the Go-only traps. Topic 14's solutions are Python-first; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Flood Fill](GoDSA/14_graphs/001_flood_fill/solution.go) <br>LC 733 · Easy | Flood fill | Capture `old := image[sr][sc]` once; return early if `old == color`; recurse or <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> on `[4][2]int` directions. **Trap:** re-reading the pixel inside the helper; no `old == color` guard (infinite recursion). |
| [002 · Number of Islands](GoDSA/14_graphs/002_number_of_islands/solution.go) <br>LC 200 · Medium | Count components on a grid | Loop over cells, one traversal per unvisited `'1'` (a `byte`, not an `int`); flat `visited []bool`. **Trap:** comparing to `1` instead of `'1'`; marking on dequeue. |
| [003 · Max Area of Island](GoDSA/14_graphs/003_max_area_of_island/solution.go) <br>LC 695 · Medium | Flood that returns a size | The <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> returns `1 + dfs(4 neighbours)`; take the max. **Trap:** a boolean result; not marking the cell before recursing. |
| [004 · Clone Graph](GoDSA/14_graphs/004_clone_graph/solution.go) <br>LC 133 · Medium | Clone with a `map[*Node]*Node` | Pointers are identity keys; register the clone **before** recursing. **Trap:** a `map[*Node]bool` (cannot say which clone); registering afterwards. |
| [005 · Walls and Gates](GoDSA/14_graphs/005_walls_and_gates/solution.go) <br>LC 286 · Medium | Multi-source <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> from the gates | Every gate seeds the queue; `dist == -1` marks unreached. **Trap:** one <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> per gate. |
| [006 · Rotting Oranges](GoDSA/14_graphs/006_rotting_oranges/solution.go) <br>LC 994 · Medium | Level-by-level <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> | `for size := len(q); size > 0; size--`; increment minutes per level. **Trap:** incrementing per dequeue. |
| [007 · Pacific Atlantic Water Flow](GoDSA/14_graphs/007_pacific_atlantic_water_flow/solution.go) <br>LC 417 · Medium | Reverse flood fill | Two <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>'s from the ocean borders with rule `>=`; intersect. **Trap:** the forward rule in the reverse flood. |
| [008 · Surrounded Regions](GoDSA/14_graphs/008_surrounded_regions/solution.go) <br>LC 130 · Medium | Flood from the border | Mark border-reachable `'O'` as safe, flip the rest, restore the marks. **Trap:** flipping first and undoing. |
| [009 · Number of Connected Components in an Undirected Graph](GoDSA/14_graphs/009_number_of_connected_components_in_an_undirected_graph/solution.go) <br>LC 323 · Medium | Components by <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> | One `visited []bool` across the outer loop; adjacency built in *both* directions. **Trap:** a one-directional list; resetting `visited` per node. |
| [010 · Graph Valid Tree](GoDSA/14_graphs/010_graph_valid_tree/solution.go) <br>LC 261 · Medium | Connected *and* n−1 edges | `len(edges) == n-1` then traverse and `count == n`. **Trap:** only one of the two checks. |
| [011 · Course Schedule](GoDSA/14_graphs/011_course_schedule/solution.go) <br>LC 207 · Medium | Directed cycle detection | `const ( white = iota; gray; black )`; a `gray` neighbour is a back edge. **Trap:** one `visited` (a diamond looks cyclic); edge direction reversed. |
| [012 · Course Schedule II](GoDSA/14_graphs/012_course_schedule_ii/solution.go) <br>LC 210 · Medium | Topological order (Kahn) | `indeg` array, queue of zeros, `if indeg[v]--; indeg[v] == 0`; check `len(order) == n`. **Trap:** returning a partial order for a cyclic graph. |
| [013 · Redundant Connection](GoDSA/14_graphs/013_redundant_connection/solution.go) <br>LC 684 · Medium | Redundant connection | The first edge whose endpoints are already connected (traversal here; union-find in topic 15). **Trap:** asking "is it an edge?" instead of "is it reachable?". |
| [014 · 01 Matrix](GoDSA/14_graphs/014_01_matrix/solution.go) <br>LC 542 · Medium | Multi-source <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> from the zeros | All zeros seed the queue; `-1` = unreached. **Trap:** one <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> per `1`; marking on dequeue. |
| [015 · Shortest Path in Binary Matrix](GoDSA/14_graphs/015_shortest_path_in_binary_matrix/solution.go) <br>LC 1091 · Medium | <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> with 8 directions | Double `for dr`/`dc` loop; check both corners up front. **Trap:** the 4-direction list; mutating the caller's grid unannounced. |
| [016 · Word Ladder](GoDSA/14_graphs/016_word_ladder/solution.go) <br>LC 127 · Hard | Word ladder | `patterns map[string][]string` (`h*t`); `delete(patterns, p)` after expanding. **Trap:** O(n²·L) pairwise adjacency. |
| [017 · Is Graph Bipartite?](GoDSA/14_graphs/017_is_graph_bipartite/solution.go) <br>LC 785 · Medium | Bipartite = 2-colourable | `color []int` (0, 1, −1); an outer loop over every start node. **Trap:** only node 0; colouring on dequeue. |
| [018 · Open the Lock](GoDSA/14_graphs/018_open_the_lock/solution.go) <br>LC 752 · Medium | An implicit graph | `[10000]bool` value arrays for `seen`/`dead`; digits via `cur / p % 10`. **Trap:** `"0000"` in the deadends; marking on dequeue. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Justify `[][]int` vs `map[int][]int` vs adjacency matrix for a given input shape
- [ ] Explain why visited must be marked at <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> enqueue time, not dequeue time
- [ ] State why recursive <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> depth is bounded by Go's goroutine stack, not unbounded
- [ ] Explain the ordering difference between recursive and iterative <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>
- [ ] Implement Union-Find with both path compression and union by rank
- [ ] Explain why undirected cycle detection needs a parent check but directed needs 3-color
- [ ] Two-color a graph to check bipartiteness, handling disconnected components
- [ ] Flatten a 2D grid coordinate to a 1D index to use `[]bool` instead of a map
- [ ] Write <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>, <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>, and Union-Find from memory in under 15 minutes each
- [ ] Write Kahn's algorithm with the edge direction stated (`[a, b]` means `b → a`) and the `len(order) == n` check <!--ca-->
- [ ] Write three-colour <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> with `iota` constants, and say why one `visited` gives false cycles in a diamond <!--ca-->
- [ ] Flatten a grid to `r*cols + c` and mark visited on *enqueue* <!--ca-->
- [ ] Use `map[*Node]*Node` for Clone Graph and register the clone before recursing <!--ca-->
- [ ] Explain bidirectional <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> and give the measured saving (822 → ~46 on the Open the Lock example) <!--ca-->
