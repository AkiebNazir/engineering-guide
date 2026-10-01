# Graph Theory — The Maths of Connections

A graph is dots joined by lines: cities and roads, people and friendships, web pages
and links, tasks and dependencies, states and transitions. Once a problem is drawn as
a graph, centuries of theorems apply to it — about paths, cycles, colourings,
connectivity and flow — and a small family of algorithms (BFS, DFS, topological sort,
Dijkstra, spanning trees) solves most of it. This chapter builds the vocabulary from
zero, proves the handful of facts engineers rely on, and shows which graph questions
are easy and which are famously hard.

**Where this fits:** Part 2 · Discrete maths, chapter 8 of 15. **Builds on:** [04 Sets, relations and functions](04_sets_relations_functions.md) (relations). **Used again in:** 09, 15. **Next in order:** [09 Linear algebra](09_linear_algebra.md).

## Where You Will Use This

| System | Vertices | Edges | Typical question |
|---|---|---|---|
| Maps and routing | intersections | roads (weighted by time) | shortest path |
| Package managers, build tools, schedulers | tasks / packages | "depends on" | topological order, cycle detection |
| Social networks | people | friendships / follows | degrees of separation (BFS), communities |
| The web, citation graphs | pages | links | PageRank (chapter 09) |
| Networks, power grids | routers | cables | connectivity, spanning trees, cut edges |
| Compilers | variables | "alive at the same time" | graph colouring for register allocation |
| Assignment problems | workers and jobs | "can do" | bipartite matching |

## Foundations — Dots and Lines

In 1736 the city of Königsberg had seven bridges linking two islands and two river
banks. Its citizens asked: can you walk through the city crossing every bridge exactly
once? Leonhard Euler answered by throwing away everything irrelevant — the shapes of
the land, the lengths of the bridges — and keeping only **which land masses are
connected by how many bridges**. That abstraction is a graph, and his answer (no: see
§6) founded graph theory.

> **Definition:** A **graph** $G = (V, E)$ is a set of **vertices** (nodes) V and a set
> of **edges** E, each edge joining two vertices. In a **directed** graph edges have a
> direction ($u \to v$); in an **undirected** graph they do not. Edges may carry a
> **weight** (a length, cost or capacity).

> **Analogy:** A metro map is a graph drawn by people who understood this perfectly:
> stations are vertices, track segments are edges, and the geography is distorted
> freely because only the connections matter for planning a trip.

### Vocabulary

| Term | Meaning |
|---|---|
| **Adjacent** | joined by an edge |
| **Degree** $\deg(v)$ | number of edges at v (in a directed graph: in-degree and out-degree) |
| **Path** | a sequence of vertices, each adjacent to the next, with no repeated vertex |
| **Cycle** | a path that returns to its start |
| **Connected** | there is a path between every pair of vertices |
| **Component** | a maximal connected piece |
| **Simple graph** | no self-loops, at most one edge between two vertices |
| **Complete graph** $K_n$ | every pair joined: $\binom{n}{2}$ edges |
| **Sparse / dense** | E is closer to V / to $V^2$ |

A simple undirected graph has at most $\binom{V}{2} = V(V-1)/2$ edges. Real graphs
(roads, social networks, the web) are overwhelmingly **sparse**: the average degree is
small even when V is in the billions. That one fact decides the data structure.

## 1 · The Handshake Lemma

> **Key idea:** In any undirected graph, $\sum_{v} \deg(v) = 2\lvert E \rvert$. Every
> edge has two ends and contributes 1 to the degree of each.

A consequence that looks like a puzzle: **the number of odd-degree vertices is always
even** (the sum of all degrees is even, so the odd ones must pair up). At a party, the
number of people who shook an odd number of hands is even.

**Try it: build graphs and read the numbers.** Click empty space to add vertices; click
one vertex and then another to add or remove an edge; drag to rearrange. The chips show
V, E, the degree sum (always 2E), components, and whether the graph is a tree, has a
cycle, is bipartite, or has an Euler path. Switch *colour by* to see each property
drawn — we will use every view in this chapter.

<div class="lab" data-viz="math-graph"></div>

> **Notebook example:** (a) Seven people shake hands. Their handshake counts are 3, 3, 2,
> 2, 2, 1 and 1. How many handshakes happened? (b) Can 5 people each shake exactly 3
> hands?
>
> 1. (a) Add the degrees: $3 + 3 + 2 + 2 + 2 + 1 + 1 = 14$.
> 2. Every handshake is counted twice, once for each hand, so there were $14 / 2 = 7$.
> 3. (b) The degree sum would be $5 \times 3 = 15$, which is odd. But a degree sum is
>    always $2|E|$, which is even.
>
> **Answer:** 7 handshakes, and no, it is impossible. You don't need to try to draw it:
> the parity argument settles it in one line.

## 2 · Representing a Graph in Code

| | Adjacency matrix | Adjacency list |
|---|---|---|
| Storage | $V \times V$ grid, `M[u][v] = 1` if edge | for each vertex, a list of neighbours |
| Space | $\Theta(V^2)$ | $\Theta(V + E)$ |
| Is (u, v) an edge? | O(1) | O(deg u), or O(1) with a set per vertex |
| List u's neighbours | O(V) | O(deg u) |
| Best for | dense graphs, matrix maths (§9) | sparse graphs — almost always |

```python
from collections import defaultdict

edges = [(0, 1), (0, 2), (1, 2), (2, 3), (3, 4)]
adj = defaultdict(list)
for u, v in edges:
    adj[u].append(v)
    adj[v].append(u)            # undirected: store both directions

V = 5
matrix = [[0] * V for _ in range(V)]
for u, v in edges:
    matrix[u][v] = matrix[v][u] = 1

print(dict(adj))                                   # → {0: [1, 2], 1: [0, 2], 2: [0, 1, 3], 3: [2, 4], 4: [3]}
print(sum(len(n) for n in adj.values()), 2 * len(edges))   # → 10 10
```

The second line is the handshake lemma, checked. For a social network with $10^9$ users
and 200 friends each, a matrix needs $10^{18}$ cells; a list needs about $2 \times 10^{11}$
entries.

> **Notebook example:** Store the graph with edges A–B, A–C, B–C and C–D both ways.
>
> 1. **Adjacency list:** A: B, C. B: A, C. C: A, B, D. D: C.
> 2. **Matrix,** with rows and columns in the order A, B, C, D:
>
> |  | A | B | C | D |
> |---|---|---|---|---|
> | **A** | 0 | 1 | 1 | 0 |
> | **B** | 1 | 0 | 1 | 0 |
> | **C** | 1 | 1 | 0 | 1 |
> | **D** | 0 | 0 | 1 | 0 |
>
> 3. Count: the lists hold $2 + 2 + 3 + 1 = 8$ entries, which is $2E$ for 4 edges. The
>    matrix has 16 cells, of which 8 are ones. It is symmetric, because the graph is
>    undirected.
>
> **Answer:** at 4 vertices both are small. At a million vertices the matrix needs
> $10^{12}$ cells while the list still needs only $2E$ entries.

## 3 · Trees

> **Definition:** A **tree** is a connected graph with no cycles. For a graph with V
> vertices, these are all equivalent:
> 1. it is connected and has no cycle;
> 2. it is connected and has exactly $V - 1$ edges;
> 3. it has no cycle and has exactly $V - 1$ edges;
> 4. there is exactly one path between any two vertices.

Why $V - 1$? Start with V isolated vertices (V components). Each edge that joins two
different components reduces the count by one; reaching one component takes exactly
$V - 1$ such edges. An edge inside a component would close a cycle instead.

Consequences you use without noticing: adding any edge to a tree creates exactly one
cycle; removing any edge disconnects it; a graph with V vertices and at least V edges
must contain a cycle. A **forest** is a graph whose components are trees:
$E = V - (\text{number of components})$.

A **spanning tree** of a connected graph is a tree using all its vertices and some of
its edges — the minimum set of links that keeps a network connected. Every connected
graph has one (keep deleting edges that lie on cycles). **Cayley's formula** says the
complete graph $K_n$ has $n^{n-2}$ spanning trees: 16 for $K_4$, 125 for $K_5$.

> **Notebook example:** 10 routers are joined by 12 cables into one connected network.
> How many cables could fail without splitting it, at best? And how many edges does a
> forest with 20 vertices and 3 trees have?
>
> 1. A tree on 10 vertices has exactly $10 - 1 = 9$ edges, and a connected network needs
>    at least that many.
> 2. $12 - 9 = 3$ cables are "extra". Each one closes a cycle, so up to 3 cables can go
>    (if they are the right ones) and a spanning tree remains.
> 3. Forest: each tree has one edge fewer than its vertices, so
>    $E = V - (\text{trees}) = 20 - 3 = 17$.
>
> **Answer:** 3 cables, and 17 edges.

## 4 · Distance and Traversal: BFS and DFS

The **distance** between two vertices is the number of edges on a shortest path.
**Breadth-first search** computes it for every vertex: visit the start, then all its
neighbours (distance 1), then all *their* unvisited neighbours (distance 2), and so on,
using a queue.

> **Key idea:** BFS explores in rings of increasing distance, so the first time it
> reaches a vertex is along a shortest path. Proof by induction on the distance: every
> vertex at distance k + 1 is adjacent to one at distance k, which BFS finished before
> starting ring k + 1.

```python
from collections import deque

def bfs_distances(adj, start):
    dist = {start: 0}
    q = deque([start])
    while q:
        u = q.popleft()
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return dist

g = {0: [1, 2], 1: [0, 3], 2: [0, 3], 3: [1, 2, 4], 4: [3], 5: []}
print(bfs_distances(g, 0))   # → {0: 0, 1: 1, 2: 1, 3: 2, 4: 3}
```

Vertex 5 is missing: it is in another component, at distance ∞. BFS is $O(V + E)$.
**Depth-first search** (a stack or recursion) explores as far as possible before
backing up; it finds components, cycles, topological orders and bridges. Both are
covered algorithm-first in the DSA topic guides; here the point is *why* they work.

In the lab, choose *BFS distance* and click a vertex to make it the source: the colours
are the rings.

> **Notebook example:** Run BFS from A on this graph: A–B, A–C, B–D, C–D, C–E, D–F, E–F.
>
> | Step | Take from queue | New neighbours (with distance) | Queue after |
> |---|---|---|---|
> | 0 | — | A = 0 | A |
> | 1 | A | B = 1, C = 1 | B, C |
> | 2 | B | D = 2 | C, D |
> | 3 | C | E = 2 (D is already seen) | D, E |
> | 4 | D | F = 3 | E, F |
> | 5 | E | none (F is already seen) | F |
> | 6 | F | none | empty |
>
> **Answer:** A 0, B 1, C 1, D 2, E 2, F 3. **Check** one answer: the only route from A
> to F with 2 edges would need a neighbour of A that touches F, and neither B nor C
> does. So 3 is right.

## 5 · Bipartite Graphs and Two-Colouring

A graph is **bipartite** if its vertices split into two groups with every edge going
between the groups — workers and jobs, students and courses, users and items. Equivalently,
you can colour the vertices with two colours so no edge joins two vertices of the same
colour.

> **Key idea:** **A graph is bipartite if and only if it has no cycle of odd length.**
> Going around a cycle alternates colours, so it returns to the starting colour only
> after an even number of steps. BFS finds the colouring (colour by distance parity)
> or an edge between two same-coloured vertices — evidence of an odd cycle.

```python
from collections import deque

def two_colour(adj):
    colour = {}
    for s in adj:
        if s in colour:
            continue
        colour[s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v in adj[u]:
                if v not in colour:
                    colour[v] = 1 - colour[u]
                    q.append(v)
                elif colour[v] == colour[u]:
                    return None                  # odd cycle found
    return colour

square = {0: [1, 3], 1: [0, 2], 2: [1, 3], 3: [2, 0]}
triangle = {0: [1, 2], 1: [0, 2], 2: [0, 1]}
print(two_colour(square), two_colour(triangle))   # → {0: 0, 1: 1, 3: 1, 2: 0} None
```

Load *bipartite K₃,₃* and *cycle C₆* in the lab with *2-colouring*; then add one edge
that creates a triangle and watch a red conflict edge appear.

> **Notebook example:** Try to 2-colour the 5-cycle 1–2–3–4–5–1, then the 6-cycle.
>
> 1. Colour 1 red. Its neighbour 2 must be blue, then 3 red, 4 blue, 5 red.
> 2. The last edge is 5–1: **red–red**. That is a conflict, so the 5-cycle is not
>    bipartite.
> 3. On the 6-cycle the colours go red, blue, red, blue, red, blue, and the closing edge
>    6–1 is blue–red. It works.
>
> **Answer:** colours alternate around a cycle, so you get back to the start with the
> right colour only after an **even** number of steps. An odd cycle is exactly what
> makes a graph non-bipartite.

## 6 · Euler and Hamilton: an Easy Question and a Hard One

**Euler path:** a walk that uses **every edge** exactly once. Euler's theorem:

> **Key idea:** A connected graph has an Euler **circuit** (ending where it starts) iff
> every vertex has even degree, and an Euler **path** iff exactly 0 or 2 vertices have
> odd degree (the path must start and end at those two). Each pass through a vertex
> uses one edge in and one edge out, so only the endpoints can have odd degree.

Königsberg's four land masses had degrees 5, 3, 3, 3 — four odd vertices, so no such
walk exists. In the lab, *house* has exactly two odd vertices: you can draw it without
lifting the pen, if you start at one of them. Checking the condition takes O(V + E), and
Hierholzer's algorithm builds the path in O(E).

> **Notebook example:** Draw the "house" (a square A, B, C, D with a roof peak E over
> D–C, plus both diagonals A–C and B–D) without lifting the pen.
>
> 1. List the degrees: A has 3 (B, D, C), B has 3 (A, C, D), C has 4, D has 4 and E has 2.
> 2. Exactly two vertices are odd, A and B, so an Euler path exists. It must start at
>    one of them and end at the other.
> 3. Start at A and use every edge once: A → B → D → E → C → D → A → C → B.
> 4. Check: that is 8 edges (AB, BD, DE, EC, CD, DA, AC, CB), all different, and the
>    house has exactly 8. ✓
>
> **Answer:** yes, starting at A (or B). Start at C and you will get stuck, just as the
> degree rule predicts.

**Hamiltonian path:** a path that visits **every vertex** exactly once. It sounds like
the same question — and it is one of the hardest problems known. No efficient algorithm
is known; it is **NP-complete** (chapter 14), and the travelling salesman problem is
its weighted cousin.

> **Interview angle:** "Every edge once" (Euler: degree parity, linear time) versus
> "every vertex once" (Hamilton: NP-complete) is the classic example of two problems
> that look alike and sit on opposite sides of the P vs NP divide. Reconstructing a
> travel itinerary from tickets, or a DNA sequence from overlapping fragments, is an
> Euler-path problem in disguise — which is why it is solvable.

## 7 · Directed Acyclic Graphs and Topological Order

A **DAG** is a directed graph with no directed cycle. Dependencies are DAGs: if A needs
B and B needs A, nothing can ever build. A **topological order** lists the vertices so
every edge points forward — a valid build order. Chapter 04 saw this as extending a
partial order.

**Kahn's algorithm:** repeatedly output a vertex with in-degree 0 (nothing left that it
waits for) and delete its outgoing edges. If vertices remain but none has in-degree 0,
there is a cycle.

```python
from collections import deque

def topo_order(n, deps):                       # deps: (a, b) means a must come before b
    indeg = [0] * n
    out = [[] for _ in range(n)]
    for a, b in deps:
        out[a].append(b)
        indeg[b] += 1
    q = deque(v for v in range(n) if indeg[v] == 0)
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in out[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return order if len(order) == n else None   # None: a cycle blocked some vertices

print(topo_order(5, [(0, 1), (0, 2), (1, 3), (2, 3), (3, 4)]))   # → [0, 1, 2, 3, 4]
print(topo_order(3, [(0, 1), (1, 2), (2, 0)]))                   # → None
```

> **Notebook example:** Courses with prerequisites: Maths → Algorithms,
> Programming → Algorithms, Programming → Databases, Algorithms → ML and
> Databases → ML. Find an order with Kahn's algorithm.
>
> | Step | In-degrees (Ma, Pr, Al, Db, ML) | Ready | Take |
> |---|---|---|---|
> | 1 | 0, 0, 2, 1, 2 | Ma, Pr | Ma |
> | 2 | –, 0, 1, 1, 2 | Pr | Pr |
> | 3 | –, –, 0, 0, 2 | Al, Db | Al |
> | 4 | –, –, –, 0, 1 | Db | Db |
> | 5 | –, –, –, –, 0 | ML | ML |
>
> **Answer:** Maths, Programming, Algorithms, Databases, ML. Taking a course subtracts 1
> from the in-degree of every course it points to. If "Ready" were ever empty with
> courses left over, those courses would contain a cycle.

Why must a finite DAG have a vertex of in-degree 0? Walk backwards along incoming edges;
if every vertex had one, the walk would go on forever through finitely many vertices and
must repeat one (pigeonhole) — a cycle.

## 8 · Weighted Graphs: Shortest Paths and Spanning Trees

With weights, "shortest" means least total weight, and BFS no longer works (three light
edges can beat one heavy edge).

**Dijkstra's algorithm** grows a set of vertices whose shortest distance is final,
always finalising the closest unfinished vertex next (using a priority queue):
$O((V + E)\log V)$.

> **Key idea:** Dijkstra is correct because **weights are non-negative**: once the
> closest unfinished vertex u is chosen, any other route to u would go through some
> unfinished vertex that is at least as far, then add non-negative edges — it cannot
> be shorter. One negative edge breaks this argument, and the algorithm; Bellman–Ford
> handles negative weights in O(VE).

```python
import heapq

def dijkstra(adj, src):
    dist = {src: 0}
    pq = [(0, src)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue                          # stale queue entry
        for v, w in adj.get(u, []):
            nd = d + w
            if nd < dist.get(v, float("inf")):
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    return dist

roads = {"A": [("B", 4), ("C", 1)], "C": [("B", 2), ("D", 7)], "B": [("D", 1)]}
print(dijkstra(roads, "A"))   # → {'A': 0, 'B': 3, 'C': 1, 'D': 4}
```

A → C → B → D costs 1 + 2 + 1 = 4, beating the direct-looking A → B → D (5).

A **minimum spanning tree** (MST) connects all vertices with the least total edge
weight — the cheapest cable network. Both classic algorithms (Kruskal: add the cheapest
edge that does not make a cycle, using union-find; Prim: grow one tree by its cheapest
outgoing edge) rest on the **cut property**: for any split of the vertices into two
sides, the cheapest edge crossing the split belongs to some MST.

> **Notebook example:** Run Dijkstra from A on the roads above (A→B 4, A→C 1, C→B 2,
> C→D 7, B→D 1). Then find a minimum spanning tree of the edges AB 1, BC 2, AC 3, CD 4,
> BD 5.
>
> | Finalise | Its distance | Update the others | Distances now (B, C, D) |
> |---|---|---|---|
> | A | 0 | B = 4, C = 1 | 4, 1, ∞ |
> | C (closest) | 1 | B = min(4, 1 + 2) = 3, D = 1 + 7 = 8 | 3, –, 8 |
> | B | 3 | D = min(8, 3 + 1) = 4 | –, –, 4 |
> | D | 4 | — | done |
>
> 1. Shortest A → D is **4**, along A → C → B → D.
> 2. **Kruskal**, cheapest edges first: take AB (1), then BC (2). Skip AC (3), because
>    A and C are already connected and it would close a cycle. Take CD (4). Now all 4
>    vertices are joined, so stop.
>
> **Answer:** distance 4, and an MST {AB, BC, CD} of weight 7.

## 9 · Graphs Meet Linear Algebra: Counting Walks

The adjacency matrix is more than storage. **The (u, v) entry of $A^k$ counts the walks
of length exactly k from u to v.** Why: a walk of length 2 from u to v goes through some
middle vertex w, and $(A^2)_{uv} = \sum_w A_{uw} A_{wv}$ counts exactly those.

```python
def mat_mult(A, B):
    n = len(A)
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]

# a triangle 0-1-2 with a tail 2-3
A = [[0, 1, 1, 0],
     [1, 0, 1, 0],
     [1, 1, 0, 1],
     [0, 0, 1, 0]]
A2 = mat_mult(A, A)
A3 = mat_mult(A2, A)
print(A2[0][0], A2[0][3])                 # → 2 1
print(sum(A3[i][i] for i in range(4)) // 6)   # → 1
```

> **Notebook example:** Work out row 0 of $A^2$ for the triangle-with-a-tail above by
> hand.
>
> 1. $(A^2)_{0v} = \sum_w A_{0w} A_{wv}$. The only w with $A_{0w} = 1$ are 0's
>    neighbours, 1 and 2.
> 2. So row 0 of $A^2$ is row 1 of A plus row 2 of A: $[1, 0, 1, 0] + [1, 1, 0, 1] = [2, 1, 1, 1]$.
> 3. Read it as walks of length 2 from 0: two back to 0 (via 1 and via 2), one to 1
>    (0→2→1), one to 2 (0→1→2) and one to 3 (0→2→3).
>
> **Answer:** $[2, 1, 1, 1]$. The shortcut to remember: **a row of $A^2$ is the sum of
> the neighbours' rows.**

$(A^2)_{00} = 2$ (0→1→0 and 0→2→0); $(A^2)_{03} = 1$ (0→2→3). The trace of $A^3$ counts
closed walks of length 3; each triangle is counted 6 times (3 starting points × 2
directions), so this graph has exactly one triangle. This bridge between graphs and
matrices powers PageRank and spectral clustering (chapter 09).

## 10 · Colouring and Planarity

**Graph colouring**: give every vertex a colour so adjacent vertices differ, using as
few colours as possible (the **chromatic number**). Exam timetabling (exams sharing a
student cannot share a slot), frequency assignment and **register allocation** in
compilers (variables alive at the same time cannot share a register) are colouring
problems.

- Two colours: easy (bipartite test above).
- Three or more: NP-complete in general.
- The **greedy** algorithm (colour vertices in some order, each with the smallest colour
  not used by a neighbour) never uses more than $\Delta + 1$ colours, where Δ is the
  maximum degree — a guarantee compilers rely on.

A graph is **planar** if it can be drawn with no crossing edges. **Euler's formula**
for a connected planar drawing: $V - E + F = 2$ (F counts faces, including the outer
one). With every face bounded by at least 3 edges, it follows that a simple planar graph
has $E \le 3V - 6$ — so **$K_5$ (10 edges, 3·5 − 6 = 9) is not planar**, and planar
graphs are sparse. The famous **four colour theorem** (1976, the first major theorem
proved with a computer) says every planar map can be coloured with 4 colours.

```python
V, E = 5, 10
print(E <= 3 * V - 6)   # → False
```

> **Notebook example:** Exams A to E, where these pairs share a student: A–B, A–C, B–C,
> C–D and D–E. Assign time slots greedily in the order A, B, C, D, E. Then check Euler's
> formula on a cube.
>
> 1. A gets slot 1.
> 2. B clashes with A (slot 1), so it gets slot 2.
> 3. C clashes with A (1) and B (2), so it gets slot 3.
> 4. D clashes only with C (3), so it gets slot 1.
> 5. E clashes only with D (1), so it gets slot 2.
> 6. 3 slots were used. A, B and C all clash with each other (a triangle), so at least 3
>    are needed: greedy found the optimum here.
> 7. A cube has $V = 8$ corners, $E = 12$ edges and $F = 6$ faces:
>    $8 - 12 + 6 = 2$. ✓
>
> **Answer:** 3 slots (A 1, B 2, C 3, D 1, E 2), and Euler's formula holds.

## Common Mistakes

1. **Using BFS for weighted shortest paths** (or Dijkstra with negative weights).
2. **One `visited` set for cycle detection in a directed graph.** A vertex seen on a
   different, finished branch is not a cycle; you need "on the current path" vs
   "finished" states (or Kahn's in-degree method).
3. **Forgetting disconnected graphs**: loop over every vertex as a possible start.
4. **Adjacency matrices for sparse graphs** — $V^2$ memory.
5. **Confusing Euler (edges) with Hamilton (vertices).**
6. **Recursion depth**: recursive DFS on a long path of $10^5$ vertices overflows the
   stack in Python; use an explicit stack.

## Check Yourself

**1.** A graph has 10 vertices, each of degree 3. How many edges? What about 9
vertices of degree 3?

<details>
<summary>Open the answer</summary>

Degree sum 30 = 2E, so 15 edges. With 9 vertices the degree sum would be 27, which is
odd — impossible, so no such graph exists (handshake lemma).

</details>

**2.** A connected graph has 12 vertices and 11 edges. What is it? What if it has 12
edges?

<details>
<summary>Open the answer</summary>

Connected with V − 1 edges: a tree. With 12 edges it is connected with exactly one
extra edge: exactly one cycle (a tree plus one edge).

</details>

**3.** Can you schedule courses whose prerequisites are A→B, B→C, C→A?

<details>
<summary>Open the answer</summary>

No: the prerequisite graph has a directed cycle, so no topological order exists. Kahn's
algorithm finds no vertex of in-degree 0 and returns None.

</details>

**4.** Why does BFS give shortest paths in an unweighted graph but not a weighted one?

<details>
<summary>Open the answer</summary>

BFS orders vertices by number of edges. With weights, a path with more edges can be
lighter, so "fewest edges" is not "least weight". Dijkstra orders by total weight
instead (and needs non-negative weights to be correct).

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Vertices, edges, degree, paths, cycles, components; directed vs undirected; adjacency list vs matrix |
| **Interview-ready** | Handshake lemma; tree characterisations (V − 1 edges); BFS distances and why they are shortest; bipartite ⇔ no odd cycle; Euler path condition; DAGs and topological sort with cycle detection; Dijkstra and why it needs non-negative weights |
| **Going deeper** | Cut property and MSTs; $A^k$ counts walks; colouring bounds and NP-completeness; planarity and Euler's formula; matchings and flows |

## Checklist

- [ ] I can choose between an adjacency list and a matrix, and justify it with V and E.
- [ ] I can state and use the handshake lemma.
- [ ] I know four equivalent definitions of a tree.
- [ ] I can prove BFS finds shortest unweighted paths and test bipartiteness with it.
- [ ] I can decide whether an Euler path exists by counting odd vertices.
- [ ] I can topologically sort a DAG and detect a cycle.
- [ ] I can explain why Dijkstra fails on negative edges.
