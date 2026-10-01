r"""
================================================================================
SOLUTION · LeetCode 207 · Course Schedule                            [Medium]
https://leetcode.com/problems/course-schedule/
================================================================================

THE CORE IDEA
--------------
Model `prerequisites[i] = [a, b]` ("a needs b first") as a DIRECTED edge
`b -> a`. "Can all courses be finished" is true if and only if this
directed graph has NO cycle (topic guide §4.3) — a course on a cycle would
need itself, indirectly, to be taken before itself, which is impossible.

The entire problem is: **detect a cycle in a directed graph.** And the
entire trap is: the undirected cycle-detection trick from problems 009/010
(a single `visited` set) is WRONG here. Topic guide §4.2, verbatim: "A
directed graph can revisit an already-fully-explored node legitimately" —
two different prerequisite CHAINS can both lead to the same downstream
course (a "diamond": 0 is a prereq of both 1 and 2, and both 1 and 2 are
prereqs of 3). Reaching node 3 twice is not a cycle, it's just two paths to
a shared dependency. A single boolean `visited` set cannot tell "I'm
currently walking through this node's ancestors" (a real cycle) apart from
"I already fully finished exploring this node earlier, on a different
branch" (fine). You need a THIRD state.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): for every course, try every possible
permutation of the remaining courses and check whether a prerequisite is
ever scheduled after its dependent. Factorial time. Never coded — the whole
point of modeling this as a graph is to avoid this.

Approach 1 (3-color DFS) ✅ — WHITE (unvisited) / GRAY (on the current DFS
path, i.e. an ANCESTOR of the node you're standing on) / BLACK (fully
explored, provably cycle-free below it). A cycle exists iff DFS reaches a
GRAY node — that means you walked back to one of your own ancestors (a
back edge). Reaching a BLACK node is fine: it's a shared descendant,
already proven safe. O(V + E) time, O(V + E) space (color array +
adjacency list + recursion stack).

Approach 2 (Kahn's algorithm, BFS on in-degree) ✅ — repeatedly take
courses whose remaining prerequisite count (in-degree) has hit zero; taking
a course decrements the in-degree of everything that depends on it. If you
can process all `numCourses` this way, no cycle blocked any of them; if you
get stuck with courses left over, every stuck course is part of (or
downstream of) a cycle. `len(order) == numCourses` is a FREE cycle check —
no separate detection pass needed (topic guide §5.1). O(V + E) time,
O(V + E) space, and — critically — fully ITERATIVE, no recursion depth risk.

Approach 3 (naive single-`visited`-set DFS) — ✗ BROKEN, implemented below
ONLY to demonstrate the trap live. Marks a node visited the first time DFS
reaches it and never un-marks it; treats "already visited" as "found a
cycle." This is EXACTLY the undirected cycle-detection shape from the
topic guide's §4.1 minus the parent-skip — and it gives a FALSE POSITIVE
on any diamond-shaped shared dependency, flagging perfectly schedulable
courses as impossible.


================================================================================
⚠️  THE #1 DIRECTED-GRAPH TRAP — LIVE, SIDE BY SIDE
================================================================================
Topic guide §4.2 names this explicitly as the trap most likely to cost an
interview. Take the diamond from Example 3 in the question file:

    numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]
    edges (b -> a): 0->1, 0->2, 1->3, 2->3

               0
              / \
             1   2
              \ /
               3

    This IS schedulable: 0, then 1, then 2, then 3 (or 0,2,1,3) — node 3 is
    reached by two DIFFERENT prerequisite chains, not a cycle.

Run the NAIVE single-`visited`-set checker on it:

    dfs(0): visited={0}, explore 1
      dfs(1): visited={0,1}, explore 3
        dfs(3): visited={0,1,3}, no outgoing edges, done
      back at 1, done
    back at 0, explore 2
      dfs(2): visited={0,1,2,3}, explore 3
        3 is ALREADY in visited  ->  naive checker shouts "CYCLE!"  ✗ WRONG

The naive checker sees node 3 a second time and concludes there's a loop.
There isn't — 3 was already fully explored and popped off the path by the
time 2 reaches it. The 3-color version tells the difference because it
KNOWS 3 turned BLACK (fully explored, safe) rather than staying GRAY
(still an open ancestor on the current path):

    dfs(0): color[0]=GRAY, explore 1
      dfs(1): color[1]=GRAY, explore 3
        dfs(3): color[3]=GRAY, no outgoing edges, color[3]=BLACK, return
      color[1]=BLACK, return
    color[0] still GRAY, explore 2
      dfs(2): color[2]=GRAY, explore 3
        3 is BLACK, not GRAY  ->  fine, it's a finished descendant, continue
      color[2]=BLACK, return
    color[0]=BLACK, return.  No GRAY node was ever re-reached -> no cycle ✅

The measured demo in run_tests() below runs BOTH checkers on this exact
diamond graph and shows the naive one printing a false "cycle detected"
while the 3-color version and Kahn's algorithm both correctly say `True`.


================================================================================
STEP BY STEP TRACE — KAHN'S ALGORITHM
================================================================================
numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]
edges (b -> a, "take b before a"): graph[0]=[1,2], graph[1]=[3], graph[2]=[3]
indegree: [0]=0, [1]=1, [2]=1, [3]=2

    queue = [0]                 (only course with 0 remaining prereqs)

    pop 0 -> order=[0]
        decrement indegree[1]: 1->0  -> queue=[1]
        decrement indegree[2]: 1->0  -> queue=[1,2]
    pop 1 -> order=[0,1]
        decrement indegree[3]: 2->1  (not yet 0, stays out of queue)
    pop 2 -> order=[0,1,2]
        decrement indegree[3]: 1->0  -> queue=[3]
    pop 3 -> order=[0,1,2,3]

    len(order) == 4 == numCourses  ->  no cycle  ->  canFinish = True

Indegree table at each step:

    step        [0]  [1]  [2]  [3]   queue
    start        0    1    1    2    [0]
    after pop 0  -    0    0    2    [1,2]
    after pop 1  -    -    0    1    [2]
    after pop 2  -    -    -    0    [3]
    after pop 3  -    -    -    -    []


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time       Space   Mutates input?  Note
    ----------------------------  ---------  ------  --------------  --------------------------
    Brute force (permutations)    O(n!)      O(n)    no              never coded
    3-color DFS ✅                 O(V + E)   O(V+E)  no              recursion depth risk
    Kahn's BFS ✅                  O(V + E)   O(V+E)  no              iterative, no recursion risk,
                                                                     free cycle check
    Naive single-visited DFS ✗    O(V + E)   O(V+E)  no              WRONG on diamond graphs

    Both correct approaches leave `prerequisites` and `numCourses`
    untouched; the graph, color array / in-degree array, and any
    stack/queue are all built fresh inside the method.


================================================================================
EDGE CASES
================================================================================
    numCourses = 1, prerequisites = []  -> trivially True: nothing to
                                            order, one course, no
                                            dependencies.
    prerequisites = []                   -> True regardless of numCourses:
                                            zero edges means zero
                                            possibility of a cycle.
    self-loop [a, a]                     -> a course that requires itself
                                            first — a 1-node cycle,
                                            immediately unsolvable; both
                                            3-color DFS (GRAY re-reached
                                            instantly) and Kahn's
                                            (indegree[a] never reaches 0)
                                            correctly return False.
    a 2-node cycle (A needs B, B needs   -> Example 2 in the question file;
    A)                                     neither course can ever be
                                            first.
    a diamond shared dependency          -> NOT a cycle — this is the
    (Example 3)                            entire point of the file; the
                                            naive checker gets this wrong,
                                            demoed live above.
    disconnected groups of courses       -> some courses with no
                                            prerequisite relationship to
                                            others at all; both algorithms
                                            handle this for free since the
                                            outer loop (DFS) / initial
                                            queue seeding (Kahn's) considers
                                            every node, not just one
                                            connected piece.


================================================================================
COMMON MISTAKES
================================================================================
1. Using a single `visited` set for directed cycle detection — the #1 trap
   this problem tests (topic guide §4.2). Gives a false positive the
   moment two different chains reach the same downstream course. Demoed
   live above: the naive checker wrongly rejects a perfectly schedulable
   diamond graph.

2. Building the adjacency list backwards — `graph[a].append(b)` instead of
   `graph[b].append(a)` for a pair `[a, b]` meaning "a needs b first."
   Get the direction wrong and you're detecting cycles in (and topologically
   sorting) the REVERSE dependency graph, which can silently change the
   answer on asymmetric graphs.

3. Forgetting to reset/track state correctly across DISCONNECTED groups of
   courses in 3-color DFS — the outer loop must start a fresh DFS from
   EVERY still-WHITE node, not just node 0, or an unreachable-from-0 cycle
   is missed entirely.

4. Choosing recursive 3-color DFS without checking recursion depth against
   `numCourses <= 2000` — a long prerequisite CHAIN (course k requires
   course k-1, for all k) recurses numCourses frames deep and can raise
   RecursionError well inside the stated constraints. Demoed live below;
   Kahn's algorithm sidesteps this entirely since it's iterative.

5. In Kahn's algorithm, decrementing in-degree and checking `== 0` AFTER
   already appending to `order`, or checking staleness incorrectly — get
   the sequence backwards (checking the queue before all decrements from
   the current pop are applied) and you can under- or over-count how many
   courses were actually processed, corrupting the free `len(order) ==
   numCourses` cycle check.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Now give me the actual order, not just yes/no.
A: Problem 012 (LC 210, Course Schedule II) — literally the same algorithm,
   just return `order` (Kahn's) or `order[::-1]` (DFS postorder) instead of
   a boolean, and return `[]` on a cycle instead of `False`.

Q: Which of Kahn's vs 3-color DFS would you actually pick in production
   code, and why?
A: Kahn's — it's iterative (no recursion-limit exposure on long chains,
   demoed below), the cycle check is free (`len(order) < numCourses`), and
   its "waves" of newly-unblocked courses are a natural fit for follow-ups
   like "minimum semesters to finish everything" (process one full wave
   per semester). DFS is fine and sometimes preferred when courses arrive
   with weights/priorities the recursion can respect more directly.

Q: What if a course could have MULTIPLE valid immediate prerequisites and
   you need the order with the fewest "semesters" (BFS layers)?
A: Kahn's algorithm already computes this for free — each full pass of the
   queue (process everything currently in it before enqueuing new
   zero-indegree nodes) is one semester; count the passes instead of
   flattening to one list.

Q: What if prerequisites could be WEIGHTED (course B takes some number of
   days, and A can't start until B finishes)?
A: Different problem — longest path in a DAG (critical path scheduling),
   computed via a topological order plus a DP pass accumulating the
   longest chain of durations ending at each node. Still needs the DAG
   check first.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 4 (directed cycle detection) / Part 5 (topological sort).

    LC 210  Course Schedule II       — produce the actual order (012, next)
    LC 802  Find Eventual Safe States — the BLACK/"safe" state generalized
    LC 269  Alien Dictionary          — build the DAG from string comparisons
                                        first, then topo sort
    LC 1136 Parallel Courses          — Kahn's "wave count" = min semesters
    LC 1462 Course Schedule IV         — reachability queries on the DAG
================================================================================
"""

import sys
import time
from collections import deque
from typing import List


class Solution:
    def canFinish(self, numCourses: int, prerequisites: List[List[int]]) -> bool:
        """✅ THE ANSWER — Kahn's algorithm (BFS on in-degree zero).
        O(V + E) time/space, fully iterative, free cycle check."""
        graph = {i: [] for i in range(numCourses)}
        indegree = [0] * numCourses
        for a, b in prerequisites:               # a needs b first: b -> a
            graph[b].append(a)
            indegree[a] += 1

        queue = deque(i for i in range(numCourses) if indegree[i] == 0)
        taken = 0
        while queue:
            node = queue.popleft()
            taken += 1
            for nxt in graph[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        return taken == numCourses

    def canFinish_dfs_3color(self, numCourses: int,
                              prerequisites: List[List[int]]) -> bool:
        """✅ Also correct — 3-color DFS (WHITE/GRAY/BLACK). Cycle iff DFS
        reaches a GRAY node (topic guide §4.2). O(V + E) time/space;
        recursion depth risk on long chains (demoed below)."""
        graph = {i: [] for i in range(numCourses)}
        for a, b in prerequisites:
            graph[b].append(a)

        WHITE, GRAY, BLACK = 0, 1, 2
        color = [WHITE] * numCourses

        def dfs(node):
            color[node] = GRAY
            for nxt in graph[node]:
                if color[nxt] == GRAY:
                    return False           # back edge to an ancestor -> cycle
                if color[nxt] == WHITE and not dfs(nxt):
                    return False
            color[node] = BLACK
            return True

        for start in range(numCourses):
            if color[start] == WHITE and not dfs(start):
                return False
        return True

    def _canFinish_naive_single_visited(self, numCourses: int,
                                         prerequisites: List[List[int]]) -> bool:
        """✗ BROKEN ON PURPOSE — the #1 directed-graph trap. A single
        `visited` set that never distinguishes "still on my current path"
        from "fully explored on a different branch." Gives FALSE POSITIVES
        on diamond-shaped shared dependencies. Kept only for the live
        demo below — never ship this."""
        graph = {i: [] for i in range(numCourses)}
        for a, b in prerequisites:
            graph[b].append(a)

        visited = set()

        def dfs(node):
            if node in visited:
                return False               # WRONG: treats "seen before" as a cycle
            visited.add(node)
            for nxt in graph[node]:
                if not dfs(nxt):
                    return False
            return True

        for start in range(numCourses):
            if not dfs(start):
                return False
        return True


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build_chain_prereqs(n):
    """Course k requires course k-1, for all k = 1..n-1 — one long chain.
    Worst case for recursion depth: DFS from the last course recurses n
    frames deep before it can unwind."""
    return [[k, k - 1] for k in range(1, n)]


# ==============================================================================
# TESTS — run:  python 011_course_schedule_solution.py
# ==============================================================================
CASES = [
    (2, [[1, 0]], True),
    (2, [[1, 0], [0, 1]], False),
    (4, [[1, 0], [2, 0], [3, 1], [3, 2]], True),
    (1, [], True),
    (3, [[0, 1], [1, 2], [2, 0]], False),
    (5, [[1, 0], [2, 1], [3, 2], [4, 3]], True),
    (3, [], True),
    (2, [[0, 0]], False),
    (6, [[1, 0], [2, 0], [3, 1], [3, 2], [4, 3], [5, 3]], True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: Kahn's algorithm ---")
    for n, prereqs, want in CASES:
        got = sol.canFinish(n, [r[:] for r in prereqs])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  numCourses={n} prereqs={prereqs!r:<40} "
              f"-> {got} (want {want})")

    print("\n--- Kahn's and 3-color DFS agree ---")
    for n, prereqs, want in CASES:
        a = sol.canFinish(n, [r[:] for r in prereqs])
        b = sol.canFinish_dfs_3color(n, [r[:] for r in prereqs])
        ok = a == b == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  numCourses={n:<3} kahn={a} dfs3color={b}")

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO: naive single-visited-set DFS vs 3-color on a diamond.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: the #1 directed-graph trap (topic guide §4.2) ---")
    n_d, prereqs_d = 4, [[1, 0], [2, 0], [3, 1], [3, 2]]
    print(f"  diamond graph: numCourses={n_d}, prerequisites={prereqs_d}")
    print(f"  (0 is a prereq of both 1 and 2; both 1 and 2 are prereqs of 3 —")
    print(f"   node 3 is reached by TWO different chains, which is NOT a cycle)")
    correct_kahn = sol.canFinish(n_d, prereqs_d)
    correct_3color = sol.canFinish_dfs_3color(n_d, prereqs_d)
    naive = sol._canFinish_naive_single_visited(n_d, prereqs_d)
    print(f"  Kahn's algorithm      -> {correct_kahn}   (correct: schedulable)")
    print(f"  3-color DFS            -> {correct_3color}   (correct: schedulable)")
    print(f"  naive single-visited   -> {naive}   "
          f"({'WRONG — false positive cycle!' if naive is False else 'unexpectedly correct this run'})")
    trap_confirmed = (correct_kahn is True and correct_3color is True
                       and naive is False)
    print(f"  naive checker wrongly reported a cycle on a schedulable graph: "
          f"{trap_confirmed}")
    all_ok &= trap_confirmed

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: Kahn's (iterative) vs 3-color DFS on a long chain.
    # ----------------------------------------------------------------------
    print("\n--- DEMO: Kahn's (iterative) vs DFS (recursive) on a long chain ---")
    limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() = {limit}")
    for n in (500, 1500, 2000):
        chain = build_chain_prereqs(n)
        t0 = time.perf_counter()
        kahn_result = sol.canFinish(n, chain)
        t1 = time.perf_counter()
        print(f"  n={n:<5} Kahn's    -> {kahn_result} in {(t1 - t0) * 1000:.2f} ms")

        t2 = time.perf_counter()
        try:
            dfs_result = sol.canFinish_dfs_3color(n, chain)
            t3 = time.perf_counter()
            print(f"  n={n:<5} DFS       -> {dfs_result} in "
                  f"{(t3 - t2) * 1000:.2f} ms  (did NOT raise)")
        except RecursionError as e:
            print(f"  n={n:<5} DFS       -> RecursionError: {e!r}")

    n_big = 2000
    chain = build_chain_prereqs(n_big)
    kahn_ok = sol.canFinish(n_big, chain) is True
    dfs_failed = False
    try:
        sol.canFinish_dfs_3color(n_big, chain)
    except RecursionError:
        dfs_failed = True
    print(f"\n  n={n_big} (this problem's own ceiling): Kahn's correct -> "
          f"{kahn_ok}; recursive 3-color DFS raised RecursionError -> "
          f"{dfs_failed}")
    print("  Same legal input, same algorithm family — only the iterative")
    print("  vs recursive call mechanism differs. This is why Kahn's is the")
    print("  safer default at this problem's own stated scale.")
    all_ok &= kahn_ok and dfs_failed

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
