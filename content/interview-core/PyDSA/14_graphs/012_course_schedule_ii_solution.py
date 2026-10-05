r"""
================================================================================
SOLUTION · LeetCode 210 · Course Schedule II                         [Medium]
https://leetcode.com/problems/course-schedule-ii/
================================================================================

THE CORE IDEA
--------------
Same graph as problem 011: `prerequisites[i] = [a, b]` ("a needs b first")
becomes a directed edge `b -> a`. Problem 011 asked "does a valid order
exist" (a cycle check). This problem asks for the order ITSELF — which is
exactly topic guide §4.3's point: **a topological order exists iff the
graph is a DAG**, and Part 5 gives two ways to actually construct one:

    - Kahn's (BFS on in-degree zero, §5.1): the sequence nodes are POPPED
      from the queue, in order, IS a valid topological order. No extra
      work needed beyond recording it.
    - DFS-based (postorder-reversed, §5.2): a node is appended to the
      result only after every one of its descendants has already finished
      — so the finishing order is the topological order BACKWARDS; reverse
      once at the end.

Both need the exact same trap avoidance as problem 011: **directed cycle
detection needs 3-color DFS or Kahn's in-degree-zero seeding, never a
single `visited` set** (topic guide §4.2) — demoed live below on the same
diamond-shaped shared-dependency graph, because getting the cycle check
wrong here doesn't just return the wrong boolean, it makes you return `[]`
for a perfectly schedulable set of courses.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): generate every permutation of
`range(numCourses)` and keep the first one that satisfies every
prerequisite pair. O(n! * E) — astronomically worse than either real
approach, never coded.

Approach 1 (Kahn's algorithm) ✅ — the primary answer. Seed a queue with
every course that has zero prerequisites; each time you pop a course,
append it to `order` and decrement the in-degree of everything that
depends on it, enqueueing any course that just hit zero. `len(order) ==
numCourses` at the end means every course got taken -> return `order`;
otherwise a cycle blocked the rest -> return `[]`. O(V + E) time, O(V + E)
space, fully ITERATIVE (no recursion depth risk — matters at this
problem's own numCourses <= 2000 ceiling, demoed below).

Approach 2 (DFS-based, postorder reversed) — also correct, offered as the
alternate approach per the topic guide's own comparison (§5.3: "012's
primary solution [is Kahn's]... offered as the alternative approach").
3-color DFS; append each node to `order` in postorder (after all its
neighbors finish); a cycle is detected the same way as problem 011 (DFS
reaches a GRAY node) -> return `[]` immediately. Otherwise reverse `order`
once at the very end. O(V + E) time, O(V + E) space; RISKY on a long
prerequisite chain, demoed below.

Approach 3 (naive single-`visited`-set DFS) — ✗ BROKEN, kept only to
demonstrate the trap live, identical shape to problem 011's broken
checker: treats "node already visited" as "found a cycle," which is wrong
the moment two different prerequisite chains share a downstream course
(a diamond). Wrongly returns `[]` for graphs that ARE schedulable.


================================================================================
⚠️  THE SAME #1 TRAP, NOW WITH A WRONG *ANSWER* INSTEAD OF A WRONG BOOLEAN
================================================================================
Reuse the diamond from problem 011 and the question file's Example 2:

    numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]
    edges (b -> a): 0->1, 0->2, 1->3, 2->3

               0
              / \
             1   2
              \ /
               3

This is schedulable — [0,1,2,3] and [0,2,1,3] are both valid. A naive
single-`visited`-set DFS reaches node 3 twice (once via 1, once via 2),
mistakes the second arrival for a cycle, and returns `[]` — silently
telling you these four courses can never all be finished, which is false.
The cost of this bug in problem 011 was a wrong boolean; here it's the
same wrong boolean PLUS a discarded, perfectly valid schedule. The
measured demo in run_tests() below runs Kahn's, DFS-3-color, and the naive
checker on this exact graph side by side.


================================================================================
STEP BY STEP TRACE — KAHN'S, RECORDING THE ORDER
================================================================================
numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]
graph: 0->[1,2], 1->[3], 2->[3], 3->[]
indegree: [0]=0, [1]=1, [2]=1, [3]=2

    queue=[0], order=[]

    pop 0 -> order=[0]
        graph[0]=[1,2]: indegree[1] 1->0 -> queue=[1]; indegree[2] 1->0 -> queue=[1,2]
    pop 1 -> order=[0,1]
        graph[1]=[3]: indegree[3] 2->1 (not yet 0)
    pop 2 -> order=[0,1,2]
        graph[2]=[3]: indegree[3] 1->0 -> queue=[3]
    pop 3 -> order=[0,1,2,3]
        graph[3]=[]: nothing to decrement

    len(order) == 4 == numCourses  ->  return [0,1,2,3]

Indegree table, matching problem 011's trace exactly (same graph, same
mechanism — the only difference is we now KEEP the pop sequence):

    step        [0]  [1]  [2]  [3]   queue    order so far
    start        0    1    1    2    [0]      []
    after pop 0  -    0    0    2    [1,2]    [0]
    after pop 1  -    -    0    1    [2]      [0,1]
    after pop 2  -    -    -    0    [3]      [0,1,2]
    after pop 3  -    -    -    -    []       [0,1,2,3]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time       Space   Mutates input?  Note
    ----------------------------  ---------  ------  --------------  --------------------------
    Brute force (permutations)    O(n! * E)  O(n)    no              never coded
    Kahn's BFS ✅                  O(V + E)   O(V+E)  no              answer; iterative, no
                                                                     recursion risk, order is
                                                                     the pop sequence itself
    DFS postorder-reversed         O(V + E)   O(V+E)  no              alternate; one list reversal,
                                                                     recursion depth risk
    Naive single-visited DFS ✗    O(V + E)   O(V+E)  no              WRONG on diamond graphs,
                                                                     returns [] incorrectly

    Neither correct approach mutates `prerequisites` or `numCourses`;
    the graph, in-degree/color arrays, and the result list are all built
    fresh inside the method.


================================================================================
EDGE CASES
================================================================================
    numCourses = 1, prerequisites = [] -> [0]. One course, nothing to
                                          order it against.
    prerequisites = []                  -> any permutation of
                                          range(numCourses) is valid since
                                          nothing constrains the order;
                                          both algorithms happen to return
                                          [0,1,...,n-1] because every
                                          course starts at in-degree 0 /
                                          WHITE simultaneously.
    a cycle anywhere                    -> return [] EXACTLY, not a
                                          partial order. Kahn's: some
                                          courses never reach indegree 0,
                                          so `len(order) < numCourses`
                                          triggers the empty return before
                                          any partial list leaks out. DFS:
                                          the cycle is detected mid-
                                          traversal and must abort the
                                          whole postorder, not return
                                          whatever was collected so far.
    multiple valid orders               -> the diamond case: 1 and 2 have
                                          no dependency on each other, so
                                          either relative order is
                                          accepted. `is_valid_order()`
                                          below checks the CONSTRAINT
                                          (every prerequisite appears
                                          before its dependent), not
                                          equality against one fixed list
                                          — matching LC's own "return ANY
                                          valid order" grading.
    self-loop [a, a]                    -> excluded by this problem's own
                                          constraints (`ai != bi`), unlike
                                          011's more permissive statement;
                                          if it slipped through anyway,
                                          both algorithms would still
                                          correctly detect it as a 1-node
                                          cycle and return [].


================================================================================
COMMON MISTAKES
================================================================================
1. Using a single `visited` set for directed cycle detection — same #1
   trap as problem 011, but here it silently discards a VALID schedule
   instead of just returning the wrong boolean. Demoed live below.

2. In Kahn's algorithm, returning `order` unconditionally instead of
   checking `len(order) == numCourses` first. A cycle leaves some courses
   permanently stuck at nonzero in-degree; returning the partial `order`
   anyway silently presents an INCOMPLETE schedule as if it were valid —
   LC explicitly requires the empty list on failure, not a partial one.

3. In the DFS approach, forgetting to REVERSE the postorder list before
   returning. The raw finishing order is backwards — course A finishing
   before course B means B is closer to being a "root" of the DAG, the
   opposite of what a topological order (prerequisites first) requires.

4. Appending to the DFS result list on ENTRY to the recursive call instead
   of on exit (after the `for` loop over neighbors). Appending on entry
   produces a completely different, generally invalid ordering — it's the
   difference between preorder and postorder traversal, and only postorder
   (reversed) gives a valid topological sort.

5. Choosing recursive DFS without checking recursion depth against
   `numCourses <= 2000` — a long prerequisite chain recurses that many
   frames deep and can raise RecursionError well inside the constraints.
   Demoed live below; Kahn's sidesteps this by being iterative.

6. Comparing a computed order against ONE hardcoded "expected" list in
   tests. Multiple valid orders usually exist (any two courses with no
   dependency relationship can go in either relative order) — tests must
   verify the CONSTRAINT, not exact equality to a single example output
   (see `is_valid_order()` below).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: You already solved 011 (yes/no). Why not just call that first, then
   compute the order separately?
A: You'd do the cycle-detection work twice for no reason — Kahn's and
   3-color DFS both produce the order AS A SIDE EFFECT of the exact same
   traversal that proves acyclicity. Detect-then-order is O(2*(V+E));
   detect-while-ordering is O(V+E).

Q: What's the minimum number of "semesters" to finish everything, if you
   can take unlimited courses per semester as long as prerequisites are
   satisfied?
A: Count Kahn's BFS "waves" instead of flattening to one list: process
   every course currently in the queue (one semester) before enqueuing any
   newly-unblocked course for the next wave (LC 1136, Parallel Courses).

Q: If several valid orders exist, how would you return a specific
   preferred one, e.g. lexicographically smallest?
A: Swap the queue in Kahn's for a min-heap (`heapq`) keyed on course
   number instead of a plain FIFO deque — always pop the smallest
   available course whose prerequisites are satisfied. Same O((V+E) log V)
   complexity, deterministic output.

Q: What if `prerequisites` could contain DUPLICATE pairs?
A: Excluded by this problem's constraints, but if it happened: building
   the adjacency list would add a duplicate edge, inflating one course's
   in-degree count beyond its true number of DISTINCT prerequisites.
   Dedup pairs into a `set` before building in-degrees, or the in-degree
   for that course would never correctly reach zero.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Part 5 (topological sort), directly.

    LC 207  Course Schedule            — the yes/no half of this exact problem (011)
    LC 269  Alien Dictionary            — build the DAG from string comparisons,
                                          then this same topological sort
    LC 1136 Parallel Courses            — Kahn's "wave count" = minimum semesters
    LC 2050 Parallel Courses III        — weighted version, longest path in a DAG
    LC 444  Sequence Reconstruction     — "is the topological order UNIQUE"
================================================================================
"""

import sys
import time
from collections import deque
from typing import List


class Solution:
    def findOrder(self, numCourses: int, prerequisites: List[List[int]]) -> List[int]:
        """✅ THE ANSWER — Kahn's algorithm (BFS on in-degree zero).
        O(V + E) time/space, fully iterative, the pop sequence IS the
        topological order."""
        graph = {i: [] for i in range(numCourses)}
        indegree = [0] * numCourses
        for a, b in prerequisites:               # a needs b first: b -> a
            graph[b].append(a)
            indegree[a] += 1

        queue = deque(i for i in range(numCourses) if indegree[i] == 0)
        order = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for nxt in graph[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        return order if len(order) == numCourses else []

    def findOrder_dfs(self, numCourses: int,
                       prerequisites: List[List[int]]) -> List[int]:
        """Alternate approach — 3-color DFS, postorder then reversed
        (topic guide §5.2). O(V + E) time/space; recursion depth risk on
        long chains (demoed below)."""
        graph = {i: [] for i in range(numCourses)}
        for a, b in prerequisites:
            graph[b].append(a)

        WHITE, GRAY, BLACK = 0, 1, 2
        color = [WHITE] * numCourses
        order = []

        def dfs(node):
            color[node] = GRAY
            for nxt in graph[node]:
                if color[nxt] == GRAY:
                    return False           # back edge -> cycle, no valid order
                if color[nxt] == WHITE and not dfs(nxt):
                    return False
            color[node] = BLACK
            order.append(node)             # postorder: finished after all descendants
            return True

        for start in range(numCourses):
            if color[start] == WHITE and not dfs(start):
                return []
        return order[::-1]

    def _findOrder_naive_single_visited(self, numCourses: int,
                                         prerequisites: List[List[int]]) -> List[int]:
        """✗ BROKEN ON PURPOSE — the same #1 directed-graph trap as
        problem 011, now silently discarding a VALID schedule. A single
        `visited` set can't distinguish "still on my current path" from
        "fully explored on a different branch." Kept only for the live
        demo below — never ship this."""
        graph = {i: [] for i in range(numCourses)}
        for a, b in prerequisites:
            graph[b].append(a)

        visited = set()
        order = []

        def dfs(node):
            if node in visited:
                return False               # WRONG: treats "seen before" as a cycle
            visited.add(node)
            for nxt in graph[node]:
                if not dfs(nxt):
                    return False
            order.append(node)
            return True

        for start in range(numCourses):
            if start not in visited:
                if not dfs(start):
                    return []
        return order[::-1]


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def is_valid_order(order, numCourses, prerequisites):
    """Any order satisfying every prerequisite is accepted — LC's own
    grading rule ("if there are many valid answers, return any")."""
    if len(order) != numCourses:
        return False
    if sorted(order) != list(range(numCourses)):
        return False
    position = {course: i for i, course in enumerate(order)}
    return all(position[b] < position[a] for a, b in prerequisites)


def build_chain_prereqs(n):
    """Course k requires course k-1, for all k = 1..n-1 — one long chain.
    Worst case for recursion depth."""
    return [[k, k - 1] for k in range(1, n)]


# ==============================================================================
# TESTS — run:  python 012_course_schedule_ii_solution.py
# ==============================================================================
CASES = [
    (2, [[1, 0]], True),
    (4, [[1, 0], [2, 0], [3, 1], [3, 2]], True),
    (1, [], True),
    (2, [[1, 0], [0, 1]], False),
    (3, [[0, 1], [1, 2], [2, 0]], False),
    (5, [[1, 0], [2, 1], [3, 2], [4, 3]], True),
    (3, [], True),
    (6, [[1, 0], [2, 0], [3, 1], [3, 2], [4, 3], [5, 3]], True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: Kahn's algorithm, validated against constraints ---")
    for n, prereqs, should_exist in CASES:
        got = sol.findOrder(n, [r[:] for r in prereqs])
        ok = is_valid_order(got, n, prereqs) if should_exist else got == []
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  numCourses={n} prereqs={prereqs!r:<40} "
              f"-> {got}")

    print("\n--- Kahn's and DFS-postorder-reversed both produce VALID orders ---")
    for n, prereqs, should_exist in CASES:
        a = sol.findOrder(n, [r[:] for r in prereqs])
        b = sol.findOrder_dfs(n, [r[:] for r in prereqs])
        ok_a = is_valid_order(a, n, prereqs) if should_exist else a == []
        ok_b = is_valid_order(b, n, prereqs) if should_exist else b == []
        ok = ok_a and ok_b
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  numCourses={n:<3} kahn={a} dfs={b}")

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO: naive single-visited-set DFS vs correct, on a diamond.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: the #1 directed-graph trap, now on an ORDER ---")
    n_d, prereqs_d = 4, [[1, 0], [2, 0], [3, 1], [3, 2]]
    print(f"  diamond graph: numCourses={n_d}, prerequisites={prereqs_d}")
    kahn_order = sol.findOrder(n_d, prereqs_d)
    dfs_order = sol.findOrder_dfs(n_d, prereqs_d)
    naive_order = sol._findOrder_naive_single_visited(n_d, prereqs_d)
    kahn_valid = is_valid_order(kahn_order, n_d, prereqs_d)
    dfs_valid = is_valid_order(dfs_order, n_d, prereqs_d)
    print(f"  Kahn's algorithm      -> {kahn_order}   (valid: {kahn_valid})")
    print(f"  DFS postorder-reversed -> {dfs_order}   (valid: {dfs_valid})")
    print(f"  naive single-visited   -> {naive_order}   "
          f"({'WRONG — discarded a valid schedule!' if naive_order == [] else 'unexpectedly non-empty this run'})")
    trap_confirmed = kahn_valid and dfs_valid and naive_order == []
    print(f"  naive checker wrongly returned [] for a schedulable graph: "
          f"{trap_confirmed}")
    all_ok &= trap_confirmed

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: Kahn's (iterative) vs DFS (recursive) on a long chain.
    # ----------------------------------------------------------------------
    print("\n--- DEMO: Kahn's (iterative) vs DFS (recursive) on a long chain ---")
    limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() = {limit}")
    for n in (500, 1500, 2000):
        chain = build_chain_prereqs(n)
        t0 = time.perf_counter()
        kahn_result = sol.findOrder(n, chain)
        t1 = time.perf_counter()
        print(f"  n={n:<5} Kahn's    -> order length {len(kahn_result)} "
              f"in {(t1 - t0) * 1000:.2f} ms")

        t2 = time.perf_counter()
        try:
            dfs_result = sol.findOrder_dfs(n, chain)
            t3 = time.perf_counter()
            print(f"  n={n:<5} DFS       -> order length {len(dfs_result)} "
                  f"in {(t3 - t2) * 1000:.2f} ms  (did NOT raise)")
        except RecursionError as e:
            print(f"  n={n:<5} DFS       -> RecursionError: {e!r}")

    n_big = 2000
    chain = build_chain_prereqs(n_big)
    kahn_ok = is_valid_order(sol.findOrder(n_big, chain), n_big, chain)
    dfs_failed = False
    try:
        sol.findOrder_dfs(n_big, chain)
    except RecursionError:
        dfs_failed = True
    print(f"\n  n={n_big} (this problem's own ceiling): Kahn's produced a "
          f"valid order -> {kahn_ok}; recursive DFS raised RecursionError -> "
          f"{dfs_failed}")
    print("  Same legal input, same algorithm family — only the iterative")
    print("  vs recursive call mechanism differs.")
    all_ok &= kahn_ok and dfs_failed

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
