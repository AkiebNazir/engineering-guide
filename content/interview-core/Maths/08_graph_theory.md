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

> **Notebook example:** Seven people meet and some of them shake hands. Afterwards they
> say how many hands each of them shook: 3, 3, 2, 2, 2, 1 and 1. How many handshakes
> happened?
>
> **What you need:** Model it as a graph: each person is a **vertex** (a dot) and each
> handshake is an **edge** (a line joining two dots). A person's handshake count is their
> **degree**: the number of edges touching their dot. The **handshake lemma**: adding up
> every vertex's degree gives exactly twice the number of edges,
> $\sum \deg(v) = 2\lvert E \rvert$, where $\lvert E \rvert$ means "the number of edges".
>
> **Plan:** add up the counts, then halve the total.
>
> 1. **Translate into a graph.** 7 vertices with degrees 3, 3, 2, 2, 2, 1 and 1. We want
>    $\lvert E \rvert$, the number of edges.
> 2. **Add the degrees.** Keep a running total: $3 + 3 = 6$, $6 + 2 = 8$, $8 + 2 = 10$,
>    $10 + 2 = 12$, $12 + 1 = 13$, $13 + 1 = 14$.
> 3. **Spot the double counting.** Each handshake involves two people, so it appears in
>    two people's counts.
>    *Why:* this is the handshake lemma: every edge has two ends, and each end adds 1 to
>    one person's degree.
> 4. **Halve the total.** $14 \div 2 = 7$.
>
> **Answer:** **7** handshakes. You never needed to know who shook whose hand.
>
> **Check:** sketch one graph with these counts: people 1 to 7 and handshakes 1–2, 1–3,
> 1–4, 2–5, 2–6, 3–4 and 5–7. People 1 and 2 have degree 3; people 3, 4 and 5 have 2;
> people 6 and 7 have 1. Count the lines: 7. ✓

> **Your turn:** Five people shook 4, 2, 2, 1 and 1 hands. How many handshakes happened?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Translate into a graph.** 5 vertices with degrees 4, 2, 2, 1 and 1.
> 2. **Add the degrees.** $4 + 2 = 6$, $6 + 2 = 8$, $8 + 1 = 9$, $9 + 1 = 10$.
> 3. **Halve the total.** $10 \div 2 = 5$.
>
> **Answer:** 5 handshakes (for example, person 1 shakes hands with all four others, and
> persons 2 and 3 shake hands with each other).
>
> </details>

> **Notebook example:** Can 5 people each shake hands with exactly 3 of the others?
>
> **What you need:** As before: people are vertices, handshakes are edges, a person's count
> is their degree, and the handshake lemma says the degrees always add up to
> $2\lvert E \rvert$. Twice a whole number is always **even**, so the degree total of any
> graph must be even.
>
> **Plan:** work out what the degree total would have to be, and see whether it is even.
>
> 1. **Translate into a graph.** 5 vertices, each of degree 3.
> 2. **Add the degrees.** $5 \times 3 = 15$.
> 3. **Ask whether it is even.** $15 = 7 \cdot 2 + 1$: remainder 1, so 15 is **odd**.
> 4. **Compare with the lemma.** The total must equal $2\lvert E \rvert$, which is even. An
>    odd number cannot equal an even one.
>    *Why:* in plain words, there would have to be $15 \div 2 = 7.5$ handshakes, and half a
>    handshake is impossible.
>
> **Answer:** **no**, it is impossible, and you don't need to try drawing it: the odd/even
> (parity) argument settles it in one line.
>
> **Check:** the other form of the lemma says the number of odd-degree vertices is always
> even; here all 5 people would have odd degree, and 5 is odd, so it agrees. With 6 people
> it *is* possible: the total is $6 \times 3 = 18$, so 9 handshakes. Sketch a hexagon
> 1–2–3–4–5–6–1 plus the three long diagonals 1–4, 2–5 and 3–6: everyone has degree 3. ✓

> **Your turn:** Can 7 people each shake hands with exactly 5 of the others?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Translate into a graph.** 7 vertices, each of degree 5.
> 2. **Add the degrees.** $7 \times 5 = 35$.
> 3. **Ask whether it is even.** $35 = 17 \cdot 2 + 1$: odd.
> 4. **Compare with the lemma.** The total must be $2\lvert E \rvert$, which is even.
>
> **Answer:** no, it is impossible.
>
> </details>

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

> **Notebook example:** Store the graph with edges A–B, A–C, B–C and C–D as an adjacency
> list.
>
> **What you need:** Two vertices are **neighbours** (or **adjacent**) when an edge joins
> them. An **adjacency list** stores, for each vertex, the list of its neighbours (in
> Python, a dict of lists). This graph is **undirected** (edges have no direction), so
> each edge u–v is stored twice: v goes in u's list and u goes in v's list.
>
> **Plan:** start with an empty list for each vertex, then go through the edges one at a
> time, writing each edge into the lists at both of its ends.
>
> 1. **Sketch the graph.** Draw dots A, B and C as a triangle and D off to the side of C.
>    Join A–B, A–C, B–C and C–D. You get a triangle with a tail.
> 2. **Start with empty lists.** A: (none). B: (none). C: (none). D: (none).
> 3. **Store edge A–B.** Add B to A's list and A to B's list. Now A: B and B: A.
> 4. **Store edge A–C.** A: B, C. C: A.
> 5. **Store edge B–C.** B: A, C. C: A, B.
> 6. **Store edge C–D.** C: A, B, D. D: C.
>    *Why:* every edge is written at both ends, because you can walk it in either
>    direction.
>
> **Answer:** A: B, C. B: A, C. C: A, B, D. D: C. Listing a vertex's neighbours is just
> reading its list, which is why this is the default way to store sparse graphs.
>
> **Check:** the lists hold $2 + 2 + 3 + 1 = 8$ entries, and 4 edges × 2 ends = 8: the
> handshake lemma again. The two `append` lines in the code above do exactly steps 3
> to 6. ✓

> **Your turn:** Store the graph with edges P–Q, P–R, P–S and R–S as an adjacency list.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sketch the graph.** A triangle P, R, S with a tail P–Q.
> 2. **Store edge P–Q.** P: Q. Q: P.
> 3. **Store edge P–R.** P: Q, R. R: P.
> 4. **Store edge P–S.** P: Q, R, S. S: P.
> 5. **Store edge R–S.** R: P, S. S: P, R.
>
> **Answer:** P: Q, R, S. Q: P. R: P, S. S: P, R. That is $3 + 1 + 2 + 2 = 8$ entries, twice
> the 4 edges.
>
> </details>

> **Notebook example:** Store the same graph (edges A–B, A–C, B–C and C–D) as an adjacency
> matrix.
>
> **What you need:** An **adjacency matrix** is a square grid with one row and one column
> per vertex, in a fixed order. The cell in row u, column v holds 1 if there is an edge
> u–v and 0 if not. In an undirected graph each edge sets **two** cells: (u, v) and
> (v, u). The **diagonal** (row A column A, row B column B, …) stays 0, because no vertex
> has an edge to itself.
>
> **Plan:** fix the order A, B, C, D, start from a 4 × 4 grid of zeros, and write a pair
> of 1s for each edge.
>
> 1. **Sketch the graph.** The same triangle A, B, C with a tail C–D.
> 2. **Fix the order and start with zeros.** Rows and columns in the order A, B, C, D;
>    all 16 cells are 0.
> 3. **Store edge A–B.** Row A, column B becomes 1, and row B, column A becomes 1.
> 4. **Store edge A–C.** Row A, column C and row C, column A become 1.
> 5. **Store edge B–C.** Row B, column C and row C, column B become 1.
> 6. **Store edge C–D.** Row C, column D and row D, column C become 1. The finished grid:
>    | | A | B | C | D |
>    |---|---|---|---|---|
>    | **A** | 0 | 1 | 1 | 0 |
>    | **B** | 1 | 0 | 1 | 0 |
>    | **C** | 1 | 1 | 0 | 1 |
>    | **D** | 0 | 0 | 1 | 0 |
>
> **Answer:** the grid above. "Is there an edge C–D?" is a single cell lookup, but the grid
> always has $V^2$ cells however few edges there are: at a million vertices that is
> $10^{12}$ cells, while the list still needs only 2E entries.
>
> **Check:** the grid is **symmetric** (row C reads the same as column C, and so on), as an
> undirected graph's must be. It has 8 ones, which is 2 × 4 edges. And row C, read
> along, gives C's neighbours A, B and D, matching the adjacency list. ✓

> **Your turn:** Write the adjacency matrix of the path X–Y–Z (edges X–Y and Y–Z), in the
> order X, Y, Z.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sketch the graph.** Three dots in a row: X, Y, Z.
> 2. **Fix the order and start with zeros.** A 3 × 3 grid, all 0.
> 3. **Store edge X–Y.** Row X, column Y and row Y, column X become 1.
> 4. **Store edge Y–Z.** Row Y, column Z and row Z, column Y become 1. The finished grid:
>    | | X | Y | Z |
>    |---|---|---|---|
>    | **X** | 0 | 1 | 0 |
>    | **Y** | 1 | 0 | 1 |
>    | **Z** | 0 | 1 | 0 |
>
> **Answer:** rows X = 0 1 0, Y = 1 0 1, Z = 0 1 0: symmetric, with 4 ones for 2 edges.
>
> </details>

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

> **Notebook example:** 10 routers are joined by 12 cables into one connected network. At
> best, how many cables could fail without splitting the network?
>
> **What you need:** A network is **connected** when every router can reach every other
> along cables. A **cycle** is a route that comes back to its start without reusing a
> cable. A **tree** is a connected graph with no cycles, and a tree on V vertices always
> has exactly $V - 1$ edges: the fewest that can keep V vertices connected. A **spanning
> tree** is a tree inside the network that still reaches every vertex. A cable that lies
> on a cycle can be cut safely, because the rest of the cycle is a detour.
>
> **Plan:** work out how many cables a spanning tree needs; every cable beyond that is
> spare.
>
> 1. **Read off V and E.** $V = 10$ routers (vertices) and $E = 12$ cables (edges).
> 2. **Find the minimum that stays connected.** A spanning tree on 10 vertices has
>    $10 - 1 = 9$ edges.
> 3. **Count the spare cables.** $12 - 9 = 3$.
> 4. **See why the spares can go.** Adding any one of those 3 cables to the spanning tree
>    closes a cycle. So if exactly those 3 fail, the 9 tree cables still connect
>    everything.
> 5. **Explain "at best".** If the wrong cable fails, for example the only cable to some
>    router, the network splits after a single failure.
>    *Why:* the count says how many cables *can* go if they are the right ones, not that
>    any 3 can.
>
> **Answer:** **3** cables, if they are the right ones. After that only a spanning tree of
> 9 cables is left, and any further failure splits the network.
>
> **Check:** a small version to sketch: 4 routers A, B, C, D in a square A–B–C–D–A plus
> the diagonal A–C, so 5 cables. The rule predicts $5 - (4 - 1) = 2$ spares. Cut A–C and
> D–A: the path A–B–C–D still connects everyone, and cutting any third cable cuts
> someone off. ✓

> **Your turn:** 6 servers are joined by 7 cables into one connected network. At best, how
> many cables could fail without splitting it?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Read off V and E.** $V = 6$, $E = 7$.
> 2. **Find the minimum that stays connected.** A spanning tree has $6 - 1 = 5$ edges.
> 3. **Count the spare cables.** $7 - 5 = 2$.
>
> **Answer:** at best 2 cables (if they are the right ones).
>
> </details>

> **Notebook example:** A forest has 20 vertices and is made of 3 separate trees. How many
> edges does it have?
>
> **What you need:** A **forest** is a graph whose separate pieces (**components**) are
> all trees. Each tree has one edge fewer than it has vertices: a tree with k vertices has
> $k - 1$ edges.
>
> **Plan:** write each tree's edge count as "its vertices minus 1", then add the three
> trees together.
>
> 1. **Name the tree sizes.** Call the three trees' vertex counts a, b and c. Together
>    they hold every vertex, so $a + b + c = 20$.
>    *Why:* we don't know the sizes, but we are about to see that they don't matter.
> 2. **Write each tree's edges.** $a - 1$, $b - 1$ and $c - 1$.
> 3. **Add them up.** $(a - 1) + (b - 1) + (c - 1) = (a + b + c) - 3$.
> 4. **Substitute the total.** $20 - 3 = 17$.
>
> **Answer:** **17** edges, whatever the sizes of the three trees. In general a forest has
> $E = V - (\text{number of trees})$.
>
> **Check:** pick sizes, say 10, 6 and 4 vertices: $9 + 5 + 3 = 17$ edges. Or sketch a
> tiny forest: a path 1–2–3 and a single edge 4–5 has 5 vertices, 2 trees and
> $5 - 2 = 3$ edges. ✓

> **Your turn:** A forest has 12 vertices and 4 trees. How many edges does it have?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Name the tree sizes.** a, b, c and d, with $a + b + c + d = 12$.
> 2. **Write each tree's edges.** $a - 1$, $b - 1$, $c - 1$ and $d - 1$.
> 3. **Add them up.** $(a + b + c + d) - 4$.
> 4. **Substitute the total.** $12 - 4 = 8$.
>
> **Answer:** 8 edges (for example, four trees of 3 vertices with 2 edges each).
>
> </details>

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

> **Notebook example:** Run breadth-first search (BFS) from A on the graph with edges A–B,
> A–C, B–D, C–D, C–E, D–F and E–F. How far is each vertex from A?
>
> **What you need:** The **distance** from A to a vertex is the fewest edges on any route
> between them. BFS finds every distance using a **queue**: a waiting line where you
> always take from the front and join at the back (first in, first out). The rule: take
> the vertex at the front; each of its neighbours that has no distance yet gets
> (the taken vertex's distance + 1) and joins the back of the queue. A vertex that already
> has a distance is **seen**: skip it. When several neighbours are new, add them in
> alphabetical order.
>
> **Plan:** sketch the graph and list neighbours, then repeat "take the front vertex,
> label its unseen neighbours" until the queue is empty.
>
> 1. **Sketch the graph.** Put A on the left, B above-right of it and C below-right, D to
>    the right of B, E to the right of C, and F on the far right. Draw the 7 edges.
> 2. **List each vertex's neighbours.** A: B, C. B: A, D. C: A, D, E. D: B, C, F. E: C, F.
>    F: D, E.
> 3. **Start at A.** A gets distance 0. Queue: A.
> 4. **Take A.** B and C are unseen: B = 0 + 1 = 1 and C = 0 + 1 = 1. Queue: B, C.
> 5. **Take B.** A is seen; D is new: D = 1 + 1 = 2. Queue: C, D.
> 6. **Take C.** A and D are seen; E is new: E = 1 + 1 = 2. Queue: D, E.
>    *Why:* D already got 2 via B. The first time BFS reaches a vertex is along a shortest
>    route, so a distance never needs changing once it is set.
> 7. **Take D.** B and C are seen; F is new: F = 2 + 1 = 3. Queue: E, F.
> 8. **Take E.** C and F are both seen, so nothing is added. Queue: F.
> 9. **Take F.** D and E are seen. The queue is now empty, so stop.
>
> **Answer:** A 0, B 1, C 1, D 2, E 2, F 3. So F is 3 hops from A, and no route does it in
> fewer.
>
> **Check:** a 2-edge route from A to F would need a neighbour of A (B or C) that touches
> F, and neither does, so 3 is right. `bfs_distances` in the code above gives the same
> labels on this graph. ✓

> **Your turn:** Run BFS from 1 on the graph with edges 1–2, 1–3, 2–4, 3–4 and 4–5.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sketch the graph.** A square 1–2–4–3–1 with a tail 4–5. Neighbours: 1: 2, 3.
>    2: 1, 4. 3: 1, 4. 4: 2, 3, 5. 5: 4.
> 2. **Start at 1.** 1 gets 0. Queue: 1.
> 3. **Take 1.** 2 = 1 and 3 = 1. Queue: 2, 3.
> 4. **Take 2.** 4 is new: 4 = 1 + 1 = 2. Queue: 3, 4.
> 5. **Take 3.** 1 and 4 are seen. Queue: 4.
> 6. **Take 4.** 5 is new: 5 = 2 + 1 = 3. Queue: 5. Taking 5 adds nothing, and the queue
>    empties.
>
> **Answer:** 1 is 0, 2 is 1, 3 is 1, 4 is 2, 5 is 3.
>
> </details>

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

> **Notebook example:** Two-colour the 6-cycle: vertices 1 to 6 with edges 1–2, 2–3, 3–4,
> 4–5, 5–6 and 6–1.
>
> **What you need:** To **two-colour** a graph is to paint every vertex red or blue so that
> no edge joins two vertices of the same colour. A graph that can be two-coloured is
> **bipartite**: the reds form one group, the blues the other, and every edge goes between
> the groups. A **cycle** is a ring of vertices, each joined to the next and the last
> joined back to the first. Once one vertex has a colour, each of its neighbours is
> **forced** to take the other colour.
>
> **Plan:** colour vertex 1 red, walk round the ring forcing each next colour, then test
> the edge that closes the ring.
>
> 1. **Sketch the graph.** Six dots in a ring (a hexagon) numbered 1 to 6, each joined to
>    the next, and 6 joined back to 1.
> 2. **Colour vertex 1 red.**
>    *Why:* the first choice is free; starting with blue would just swap every colour.
> 3. **Force vertex 2.** It is joined to 1, which is red, so 2 is blue.
> 4. **Force vertices 3 to 6.** Keep alternating round the ring: 3 red, 4 blue, 5 red,
>    6 blue.
> 5. **Test the closing edge.** 6–1 joins blue to red. No clash.
>
> **Answer:** it works: red {1, 3, 5} and blue {2, 4, 6}. The 6-cycle is bipartite.
>
> **Check:** go through all 6 edges: 1–2 red–blue, 2–3 blue–red, 3–4 red–blue, 4–5
> blue–red, 5–6 red–blue, 6–1 blue–red. Every edge joins two different colours. ✓

> **Your turn:** Two-colour the square with a tail: edges 1–2, 2–3, 3–4, 4–1 and 4–5.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sketch the graph.** A square 1–2–3–4 with an extra dot 5 hanging off 4.
> 2. **Colour vertex 1 red.**
> 3. **Force round the square.** 2 blue, 3 red, 4 blue.
> 4. **Test the closing edge.** 4–1 joins blue to red. No clash.
> 5. **Force the tail.** 5 is joined to 4 (blue), so 5 is red.
>
> **Answer:** it works: red {1, 3, 5} and blue {2, 4}, so the graph is bipartite.
>
> </details>

> **Notebook example:** Try to two-colour the 5-cycle: edges 1–2, 2–3, 3–4, 4–5 and 5–1.
>
> **What you need:** The same rules as the previous example: red or blue, no edge may join
> two vertices of the same colour, and colouring a vertex forces its neighbours. If a
> forced colour clashes, the graph is **not** bipartite. No other choice could have
> worked, because every colour after the first was forced, and the first choice only
> decides which group is called red.
>
> **Plan:** colour 1 red, force the colours round the ring, then test the closing edge.
>
> 1. **Sketch the graph.** Five dots in a ring (a pentagon), each joined to the next, and
>    5 joined back to 1.
> 2. **Colour vertex 1 red.**
> 3. **Force vertex 2.** It is joined to red 1, so 2 is blue.
> 4. **Force vertices 3 to 5.** Keep alternating: 3 red, 4 blue, 5 red.
> 5. **Test the closing edge.** 5–1 joins **red to red**: a clash.
>    *Why:* every step round the ring flips the colour, and going all the way round is 5
>    steps. After an odd number of flips, vertex 1 would need to be blue, but it is red.
>
> **Answer:** impossible: the 5-cycle is **not** bipartite. An odd cycle is exactly what
> makes two-colouring fail; the 6-cycle worked because 6 is even.
>
> **Check:** starting with 1 blue instead just swaps every colour, and 5–1 becomes
> blue–blue: still a clash. In the code above, `two_colour` returns `None` for the
> triangle (a 3-cycle) for the same reason. ✓

> **Your turn:** Take the 6-cycle from before and add one extra edge, 1–3. Can it still be
> two-coloured?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sketch the graph.** The hexagon 1 to 6, plus a line from 1 to 3.
> 2. **Colour vertex 1 red.**
> 3. **Force round the ring.** 2 blue, 3 red, 4 blue, 5 red, 6 blue; the closing edge 6–1
>    is blue–red, fine.
> 4. **Test the extra edge.** 1–3 joins **red to red**: a clash.
>
> **Answer:** no. The new edge makes the triangle 1–2–3, an odd cycle, so the graph is not
> bipartite.
>
> </details>

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

> **Notebook example:** Can you draw the "house" without lifting your pen or going over
> any line twice? The house is a square A, B, C, D (A bottom-left, B bottom-right, C
> top-right, D top-left), a roof peak E joined to D and C, and both diagonals A–C and B–D.
>
> **What you need:** An **Euler path** is a route that uses every edge exactly once, which
> is what "drawing without lifting the pen" means. A vertex's **degree** is the number of
> edges touching it. **Euler's rule** for a connected graph: count the vertices of **odd**
> degree. If there are 0, it can be done and you finish where you started; if there are
> exactly 2, it can be done but you must start at one odd vertex and finish at the other;
> otherwise it is impossible.
>
> **Plan:** sketch, count each vertex's degree, apply the rule, then trace a route from an
> odd vertex, crossing edges off as you use them.
>
> 1. **Sketch the house.** Edges: A–B, B–C, C–D and D–A (the square), A–C and B–D (the
>    diagonals), D–E and E–C (the roof). That is 8 edges.
> 2. **Count the degrees.** A touches B, C, D: 3. B touches A, C, D: 3. C touches A, B, D,
>    E: 4. D touches A, B, C, E: 4. E touches C, D: 2.
> 3. **Find the odd vertices.** A (3) and B (3): exactly two.
> 4. **Apply Euler's rule.** Two odd vertices, so an Euler path exists, and it must start
>    at A and end at B (or the other way round).
>    *Why:* each time the route passes through a vertex it uses one edge in and one edge
>    out, so vertices in the middle of the route use their edges up in pairs. Only the
>    start and the end can have an odd count.
> 5. **Trace the first half.** Start at A: A → B → D → E → C. Crossed off: AB, BD, DE, EC.
>    Still unused: BC, CD, DA, AC.
>    *Why:* at each vertex any unused edge will do, as long as it doesn't leave other
>    unused edges cut off from you.
> 6. **Trace the second half.** From C: C → D → A → C → B. Crossed off: CD, DA, AC, CB.
>    Nothing is left, and we finish at B as predicted.
>
> **Answer:** **yes**: A → B → D → E → C → D → A → C → B. Start at A or B. Start at C, D or
> E and you will get stuck, just as the degree rule predicts.
>
> **Check:** the route has 8 moves (AB, BD, DE, EC, CD, DA, AC, CB), all different, and
> the house has exactly 8 edges. The degree sum $3 + 3 + 4 + 4 + 2 = 16 = 2 \times 8$
> agrees with the handshake lemma. ✓

> **Your turn:** A square A, B, C, D (edges A–B, B–C, C–D, D–A) has one diagonal, A–C. Can
> you draw it without lifting your pen?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sketch the shape.** 4 square sides plus the diagonal A–C: 5 edges.
> 2. **Count the degrees.** A 3 (B, D, C), B 2, C 3 (B, D, A), D 2.
> 3. **Find the odd vertices.** A and C: exactly two.
> 4. **Apply Euler's rule.** An Euler path exists, from A to C (or C to A).
> 5. **Trace a route.** A → B → C → D → A → C uses AB, BC, CD, DA, AC: all 5 edges once.
>
> **Answer:** yes, for example A → B → C → D → A → C, starting at A or C.
>
> </details>

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

> **Notebook example:** Courses have these prerequisites, where X → Y means "take X before
> Y": Maths → Algorithms, Programming → Algorithms, Programming → Databases,
> Algorithms → ML and Databases → ML. Find an order to take all five, using Kahn's
> algorithm.
>
> **What you need:** This is a **directed graph**: each edge is an arrow with a direction.
> A course's **in-degree** is the number of arrows pointing **into** it, which is how many
> of its prerequisites are still not taken. A course with in-degree 0 is **ready**.
> **Kahn's algorithm:** take a ready course, then remove its outgoing arrows (subtract 1
> from the in-degree of every course it points to), and repeat. The order you take them
> in is a **topological order**: every arrow points forward. When several courses are
> ready, take them in the order they were listed (any choice gives a valid order).
>
> **Plan:** sketch, count the in-degrees, then repeat "take a ready course, subtract 1 from
> what it points to" until all five are taken.
>
> 1. **Sketch the graph.** Put Maths and Programming on the left, Algorithms and Databases
>    in the middle and ML on the right, then draw the 5 arrows.
> 2. **Count the in-degrees.** Maths 0, Programming 0, Algorithms 2 (from Maths and
>    Programming), Databases 1 (from Programming), ML 2 (from Algorithms and Databases).
> 3. **Take Maths.** Ready: Maths and Programming; take Maths, the first listed. It points
>    to Algorithms, whose in-degree drops 2 → 1.
>    *Why:* one of Algorithms' two prerequisites is now done.
> 4. **Take Programming.** It is the only ready course. It points to Algorithms (1 → 0) and
>    Databases (1 → 0).
> 5. **Take Algorithms.** Ready: Algorithms and Databases; take Algorithms. ML drops
>    2 → 1.
> 6. **Take Databases.** ML drops 1 → 0.
> 7. **Take ML.** It points to nothing, and all five courses are taken, so stop.
>
> **Answer:** Maths, Programming, Algorithms, Databases, ML. If "ready" were ever empty
> with courses left over, those courses would contain a cycle and no order would exist.
>
> **Check:** number the courses by position (Maths 1, Programming 2, Algorithms 3,
> Databases 4, ML 5) and test that every arrow points forward: 1 → 3, 2 → 3, 2 → 4,
> 3 → 5 and 4 → 5. The `topo_order` code above does these same steps with a queue. ✓

> **Your turn:** Build steps with dependencies Install → Build, Configure → Build and
> Build → Test. Find an order with Kahn's algorithm.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sketch the graph.** Install and Configure both point to Build; Build points to
>    Test.
> 2. **Count the in-degrees.** Install 0, Configure 0, Build 2, Test 1.
> 3. **Take Install.** Build drops 2 → 1.
> 4. **Take Configure.** Build drops 1 → 0.
> 5. **Take Build.** Test drops 1 → 0.
> 6. **Take Test.** Everything is taken.
>
> **Answer:** Install, Configure, Build, Test.
>
> </details>

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

> **Notebook example:** Run Dijkstra's algorithm from A on the roads in the code above:
> one-way roads A→B of length 4, A→C 1, C→B 2, C→D 7 and B→D 1. What is the shortest
> distance from A to D, and which route gives it?
>
> **What you need:** Each road (a directed edge) has a **weight**, its length, and a
> route's length is the sum of its weights. **Dijkstra's algorithm** keeps a best-known
> distance for every vertex; ∞ ("infinity") means no route found yet. Repeat: **finalise**
> the unfinished vertex with the smallest best-known distance (it can no longer improve),
> then look along each road u → v leaving it, and if $\text{dist}(u) + \text{weight}$ is
> smaller than v's best-known distance, replace it. Replacing a distance like this is
> called **relaxing** the edge.
>
> **Plan:** start with A = 0 and everything else ∞, then finalise one vertex per step and
> update the vertices its roads lead to, until all are final.
>
> 1. **Sketch the graph.** Dots A, B, C, D with arrows A→B (4), A→C (1), C→B (2), C→D (7)
>    and B→D (1). Write 0 beside A and ∞ beside B, C and D.
> 2. **Finalise A (distance 0).** Road A→B: $0 + 4 = 4$, better than ∞, so B = 4. Road
>    A→C: $0 + 1 = 1$, so C = 1.
> 3. **Pick the closest unfinished vertex.** B = 4, C = 1, D = ∞. The smallest is C.
> 4. **Finalise C (distance 1).** Road C→B: $1 + 2 = 3$, better than 4, so B = 3. Road
>    C→D: $1 + 7 = 8$, better than ∞, so D = 8.
>    *Why:* going round through C beats the direct road A→B, even though it uses more
>    roads.
> 5. **Pick the closest unfinished vertex.** B = 3, D = 8. The smallest is B.
> 6. **Finalise B (distance 3).** Road B→D: $3 + 1 = 4$, better than 8, so D = 4.
> 7. **Finalise D (distance 4).** It is the only one left, and no roads leave it. Done.
> 8. **Trace the route backwards.** D's 4 came from B, B's 3 came from C, and C's 1 came
>    from A. So the route is A → C → B → D.
>
> **Answer:** the shortest distance from A to D is **4**, along A → C → B → D. The
> "obvious" route A → B → D costs 5.
>
> **Check:** add up the route: $1 + 2 + 1 = 4$. The other routes are A → B → D
> ($4 + 1 = 5$) and A → C → D ($1 + 7 = 8$), both longer. The code above prints `'D': 4`. ✓

> **Your turn:** Run Dijkstra from S on the one-way roads S→X 2, S→Y 5, X→Y 1, Y→T 1 and
> X→T 4. What is the shortest distance from S to T?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sketch the graph.** Dots S, X, Y, T with the five arrows. S = 0; X, Y, T = ∞.
> 2. **Finalise S (distance 0).** X = 0 + 2 = 2 and Y = 0 + 5 = 5.
> 3. **Finalise X (distance 2), the closest.** Y: $2 + 1 = 3$, better than 5, so Y = 3.
>    T: $2 + 4 = 6$, so T = 6.
> 4. **Finalise Y (distance 3), the closest.** T: $3 + 1 = 4$, better than 6, so T = 4.
> 5. **Finalise T (distance 4).** Done.
> 6. **Trace the route backwards.** T came from Y, Y from X, X from S.
>
> **Answer:** 4, along S → X → Y → T.
>
> </details>

> **Notebook example:** Find a minimum spanning tree of the graph with edges AB weight 1,
> BC 2, AC 3, CD 4 and BD 5, using Kruskal's algorithm.
>
> **What you need:** A **spanning tree** connects all the vertices with no cycles, so it
> has exactly $V - 1$ edges. A **minimum spanning tree** (MST) is one with the smallest
> possible total weight: the cheapest cable network that still links everyone.
> **Kruskal's algorithm:** go through the edges from cheapest to most expensive; take an
> edge unless its two ends are already connected (then it would close a cycle, so skip
> it); stop once you have $V - 1$ edges.
>
> **Plan:** sort the edges, then take or skip each one in turn, keeping track of which
> vertices are already joined into groups.
>
> 1. **Sketch the graph.** Dots A, B, C, D and undirected lines A–B (1), B–C (2), A–C (3),
>    C–D (4) and B–D (5).
> 2. **Sort the edges by weight.** AB 1, BC 2, AC 3, CD 4, BD 5 (already in order).
> 3. **Take AB (1).** A and B were separate. Groups: {A, B}, {C}, {D}.
> 4. **Take BC (2).** C was on its own. Groups: {A, B, C}, {D}.
> 5. **Skip AC (3).** A and C are already in the same group, so A–C would close the cycle
>    A–B–C–A.
>    *Why:* a cycle never helps: one of its edges can always be dropped without
>    disconnecting anything, which saves its weight.
> 6. **Take CD (4).** D was on its own. Groups: {A, B, C, D}.
> 7. **Stop.** We have 3 edges, which is $V - 1 = 4 - 1$. BD (5) is never needed.
> 8. **Add the weights.** $1 + 2 + 4 = 7$.
>
> **Answer:** the MST is {AB, BC, CD} with total weight **7**: the cheapest way to link all
> four vertices.
>
> **Check:** D must be reached by CD (4) or BD (5), so that costs at least 4. Linking A,
> B and C needs 2 more edges costing at least $1 + 2 = 3$. So no spanning tree can weigh
> less than $4 + 3 = 7$. ✓

> **Your turn:** Find a minimum spanning tree of the edges PQ 2, QR 1, PR 3, RS 5 and QS 6.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sort the edges by weight.** QR 1, PQ 2, PR 3, RS 5, QS 6.
> 2. **Take QR (1).** Groups: {Q, R}, {P}, {S}.
> 3. **Take PQ (2).** Groups: {P, Q, R}, {S}.
> 4. **Skip PR (3).** P and R are already in the same group.
> 5. **Take RS (5).** Groups: {P, Q, R, S}. That is 3 edges $= 4 - 1$, so stop.
> 6. **Add the weights.** $1 + 2 + 5 = 8$.
>
> **Answer:** the MST is {QR, PQ, RS}, total weight 8.
>
> </details>

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

> **Notebook example:** For the triangle-with-a-tail in the code above (vertices 0, 1, 2,
> 3 and edges 0–1, 0–2, 1–2, 2–3), work out row 0 of $A^2$ by hand and read off what it
> counts.
>
> **What you need:** A is the adjacency matrix: $A_{uv}$ (row u, column v) is 1 if u and v
> are joined and 0 if not. $A^2$ means $A \cdot A$, and its entry in row 0, column v is
> $(A^2)_{0v} = A_{00}A_{0v} + A_{01}A_{1v} + A_{02}A_{2v} + A_{03}A_{3v}$: go along row 0
> of A and down column v of A, multiply the pairs and add. The entry in row u, column v
> of $A^2$ counts the **walks of length 2** from u to v: routes of exactly 2 edges, where
> coming back to a vertex is allowed.
>
> **Plan:** write A out, notice that most terms are multiplied by 0, and turn row 0 of
> $A^2$ into a sum of two rows of A.
>
> 1. **Sketch the graph.** Dots 0, 1 and 2 in a triangle, plus dot 3 joined only to 2.
> 2. **Write A row by row.** Row 0: [0, 1, 1, 0]. Row 1: [1, 0, 1, 0]. Row 2:
>    [1, 1, 0, 1]. Row 3: [0, 0, 1, 0].
> 3. **Plug in row 0 of A.** $A_{00} = 0$, $A_{01} = 1$, $A_{02} = 1$ and $A_{03} = 0$, so
>    $(A^2)_{0v} = 0 \cdot A_{0v} + 1 \cdot A_{1v} + 1 \cdot A_{2v} + 0 \cdot A_{3v}$.
> 4. **Drop the zero terms.** $(A^2)_{0v} = A_{1v} + A_{2v}$. So row 0 of $A^2$ is row 1
>    of A plus row 2 of A.
>    *Why:* only 0's neighbours, 1 and 2, survive. A walk 0 → w → v has to step to a
>    neighbour w first.
> 5. **Add the two rows entry by entry.** $[1, 0, 1, 0] + [1, 1, 0, 1] = [1 + 1, 0 + 1, 1 + 0, 0 + 1] = [2, 1, 1, 1]$.
> 6. **Read it as walks.** 2 walks from 0 back to 0 (0→1→0 and 0→2→0); 1 to vertex 1
>    (0→2→1); 1 to vertex 2 (0→1→2); 1 to vertex 3 (0→2→3).
>
> **Answer:** row 0 of $A^2$ is $[2, 1, 1, 1]$. The shortcut to remember: **a row of
> $A^2$ is the sum of the neighbours' rows.**
>
> **Check:** the code above prints `A2[0][0]` as 2 and `A2[0][3]` as 1, the first and last
> entries. The row also adds up to 5, the total number of 2-step walks from 0: step to 1
> (then 2 ways on) or step to 2 (then 3 ways on), and $2 + 3 = 5$. ✓

> **Your turn:** In the same graph, work out row 1 of $A^2$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find vertex 1's neighbours.** Row 1 of A is [1, 0, 1, 0], so the neighbours are 0
>    and 2.
> 2. **Add their rows.** $[0, 1, 1, 0] + [1, 1, 0, 1] = [1, 2, 1, 1]$.
> 3. **Read it as walks.** 1 to vertex 0 (1→2→0); 2 back to 1 (1→0→1 and 1→2→1); 1 to
>    vertex 2 (1→0→2); 1 to vertex 3 (1→2→3).
>
> **Answer:** row 1 of $A^2$ is $[1, 2, 1, 1]$.
>
> </details>

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

> **Notebook example:** Exams A to E need time slots. These pairs share a student, so they
> must not be in the same slot: A–B, A–C, B–C, C–D and D–E. Assign slots greedily in the
> order A, B, C, D, E.
>
> **What you need:** Draw a **conflict graph**: each exam is a vertex, and an edge joins
> two exams that share a student. Giving out slots is then **graph colouring**: each
> vertex gets a colour (here a slot number 1, 2, 3, …) and joined vertices must get
> different ones. The **greedy** rule: go through the vertices in the given order and give
> each one the **smallest** slot number not already used by one of its coloured
> neighbours.
>
> **Plan:** sketch the conflict graph, give each exam its slot one at a time, then check
> whether fewer slots were possible.
>
> 1. **Sketch the graph.** Dots A, B, C in a triangle (A–B, A–C, B–C), then a tail
>    C–D–E.
> 2. **Slot A.** None of its neighbours has a slot yet, so A gets slot 1.
> 3. **Slot B.** Its neighbour A has 1, so the smallest free slot is 2.
> 4. **Slot C.** Its neighbours A and B have 1 and 2, so C gets 3.
> 5. **Slot D.** Its only slotted neighbour, C, has 3, so slot 1 is free: D gets 1.
>    *Why:* D does not clash with A, so it can share A's slot.
> 6. **Slot E.** Its neighbour D has 1, so E gets 2.
> 7. **Count the slots.** Slots 1, 2 and 3 were used: 3 slots.
> 8. **Ask whether fewer would do.** A, B and C all clash with each other (a triangle), so
>    they need 3 different slots. 3 is the minimum.
>
> **Answer:** 3 slots (A 1, B 2, C 3, D 1, E 2), and that is the best possible here.
> Greedy is not always the best possible, but it never uses more than (largest degree + 1)
> slots.
>
> **Check:** test every edge: A–B 1–2, A–C 1–3, B–C 2–3, C–D 3–1, D–E 1–2. No edge joins
> two equal slots. The largest degree is 3 (vertex C), so greedy promised at most
> $3 + 1 = 4$ slots, and it used 3. ✓

> **Your turn:** Exams P, Q, R, S clash in the pairs P–Q, Q–R, R–S and S–P. Assign slots
> greedily in the order P, Q, R, S.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sketch the graph.** A square P–Q–R–S–P.
> 2. **Slot P.** Slot 1.
> 3. **Slot Q.** Its neighbour P has 1, so Q gets 2.
> 4. **Slot R.** Its only slotted neighbour, Q, has 2, so R gets 1.
> 5. **Slot S.** Its neighbours R and P both have 1, so S gets 2.
> 6. **Ask whether fewer would do.** P and Q clash, so at least 2 slots are needed.
>
> **Answer:** 2 slots (P 1, Q 2, R 1, S 2), which is the minimum.
>
> </details>

> **Notebook example:** Check Euler's formula $V - E + F = 2$ on the graph of a cube.
>
> **What you need:** A graph is **planar** if you can draw it on paper with no edges
> crossing. Such a drawing splits the paper into regions called **faces**, and the
> unbounded region outside the drawing counts as a face too. **Euler's formula:** for a
> connected planar drawing, $V - E + F = 2$, where V counts the vertices, E the edges and
> F the faces.
>
> **Plan:** draw the cube flat with no crossings, count V, E and F, then substitute.
>
> 1. **Sketch the cube flat.** Draw a small square inside a big square, then join each
>    corner of the small square to the nearest corner of the big one. No lines cross.
>    *Why:* this is what you see looking down into an open box; it has the same corners
>    and edges as the cube.
> 2. **Count the vertices.** 4 on the big square + 4 on the small square: $V = 8$.
> 3. **Count the edges.** 4 on the big square + 4 on the small square + 4 joining lines:
>    $E = 12$.
> 4. **Count the faces.** The inside of the small square (1), the 4 four-sided regions
>    between the squares (4) and the outside (1): $F = 6$, one for each side of the cube.
> 5. **Substitute into the formula.** $V - E + F = 8 - 12 + 6$.
> 6. **Do the arithmetic.** $8 - 12 = -4$, and $-4 + 6 = 2$.
>
> **Answer:** $8 - 12 + 6 = 2$, so Euler's formula holds for the cube.
>
> **Check:** the bound $E \le 3V - 6$ that follows from the formula gives
> $12 \le 3 \cdot 8 - 6 = 18$, as it must for a planar graph. A tetrahedron agrees too:
> $4 - 6 + 4 = 2$. ✓

> **Your turn:** Check Euler's formula on a square pyramid: draw it flat as a square with
> one dot in the middle joined to all 4 corners.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sketch the pyramid flat.** A square, a dot in the middle, and 4 lines from the dot
>    to the corners.
> 2. **Count the vertices.** 4 corners + 1 middle dot: $V = 5$.
> 3. **Count the edges.** 4 square sides + 4 lines to the middle: $E = 8$.
> 4. **Count the faces.** 4 triangles inside + the outside: $F = 5$.
> 5. **Substitute into the formula.** $5 - 8 + 5 = -3 + 5 = 2$.
>
> **Answer:** $V - E + F = 2$, so the formula holds.
>
> </details>

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
