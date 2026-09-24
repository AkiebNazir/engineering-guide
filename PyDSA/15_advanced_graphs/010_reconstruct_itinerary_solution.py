"""
================================================================================
SOLUTION · LeetCode 332 · Reconstruct Itinerary                         [Hard]
https://leetcode.com/problems/reconstruct-itinerary/
================================================================================

THE CORE IDEA
--------------
Using every ticket EXACTLY once is an EULERIAN PATH (visit every EDGE once),
not a topological order over nodes (topic guide Part 7's closing note).
Hierholzer's algorithm builds it: repeatedly follow the LEXICALLY SMALLEST
unused edge from the current city until stuck (no unused edges remain from
here); a "stuck" city gets APPENDED to the result. Doing this iteratively
with an explicit stack (never recursively -- see "why iterative" below)
and reversing the result at the end produces the correct itinerary.

    graph[src] = min-heap of destinations (heapq gives lexicographic pops)
    stack = ["JFK"]; route = []
    while stack:
        while graph[stack[-1]]:            # keep going while an edge remains
            stack.append(heapq.heappop(graph[stack[-1]]))
        route.append(stack.pop())          # dead end: commit it
    return route[::-1]

O(E log E) time (E tickets, dominated by heap operations), O(E) space.


================================================================================
WHY NAIVE GREEDY DFS (WITHOUT THE STACK-AND-COMMIT-AT-DEAD-END STRUCTURE)
FAILS
================================================================================
tickets = [["JFK","KUL"], ["JFK","NRT"], ["NRT","JFK"]]

A naive greedy walk -- "always go to the lexically smallest unused
destination, stop when there's nowhere left to go" -- does this:
    at JFK: smallest unused destination is KUL (K < N) -> go to KUL.
    at KUL: no outgoing tickets -> STUCK. Return ["JFK", "KUL"].

That uses only ONE of the three tickets and is not a valid answer -- the
problem guarantees all tickets must be used. The greedy choice (KUL first)
was locally correct (K really is alphabetically smaller) but globally a
trap: taking it first strands the OTHER two tickets (JFK->NRT->JFK)
forever unreachable, since nothing ever returns to JFK.

The true answer is ["JFK","NRT","JFK","KUL"] -- it takes NRT first (the
"wrong" local choice) specifically so it can loop back through JFK and
still reach KUL afterward, using every ticket.

Hierholzer's algorithm handles this correctly not because it makes a
different greedy choice, but because of WHEN it commits a city to the
result: only once that city has been proven to be a genuine dead end
(traced via the DFS stack), never eagerly. A city that turns out not to
be a "true" dead end gets revisited later via the stack and its remaining
edges get walked THEN -- see the trace below, where KUL (the naive
greedy's premature stopping point) is still the FIRST city committed to
`route`, but because the whole thing is reversed at the end, it correctly
lands LAST in the final itinerary, not first.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): try every permutation of
using the tickets, check if it forms a valid path starting at JFK using
each ticket exactly once, keep the lexicographically smallest. O(E!) --
useless past a handful of tickets.

Approach 1 (Hierholzer's, iterative stack) [checked] -- the answer above.

Approach 2 (Hierholzer's, RECURSIVE) -- textbook-elegant, and WRONG for
this problem's own stated bounds: up to 300 tickets can form a chain-
shaped Eulerian path 300 edges deep, and Python's default recursion limit
is 1000 -- close enough that other stack frames in a real program (or a
slightly deeper structure) can blow it, and the topic guide flags this
exact failure mode generally (Part 6). The iterative version sidesteps it
entirely. Demoed live below with a genuinely deep chain.


================================================================================
STEP BY STEP TRACE
================================================================================
tickets = [["JFK","KUL"], ["JFK","NRT"], ["NRT","JFK"]]
graph (as min-heaps): JFK: [KUL, NRT]   NRT: [JFK]

stack=["JFK"], route=[]

outer iteration 1:
    inner: graph["JFK"] not empty -> pop smallest = "KUL" -> stack=["JFK","KUL"]
    inner: graph["KUL"] empty -> stop
    route.append(stack.pop()) -> route=["KUL"], stack=["JFK"]

outer iteration 2:
    inner: graph["JFK"] = ["NRT"] (KUL already consumed) -> pop "NRT"
           -> stack=["JFK","NRT"]
    inner: graph["NRT"] = ["JFK"] -> pop "JFK" -> stack=["JFK","NRT","JFK"]
    inner: graph["JFK"] now empty (both KUL and NRT consumed) -> stop
    route.append(stack.pop()) -> route=["KUL","JFK"], stack=["JFK","NRT"]

outer iteration 3:
    inner: graph["NRT"] empty -> stop immediately
    route.append(stack.pop()) -> route=["KUL","JFK","NRT"], stack=["JFK"]

outer iteration 4:
    inner: graph["JFK"] empty -> stop immediately
    route.append(stack.pop()) -> route=["KUL","JFK","NRT","JFK"], stack=[]

stack empty -> loop ends. Reverse route:
    ["JFK","NRT","JFK","KUL"]   MATCHES the true answer, uses all 3 tickets.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                             Time         Space  Mutates input?
    ------------------------------------  -----------  -----  --------------
    Brute-force permutation search        O(E!)        O(E)   no
    Hierholzer's, iterative stack [chos.] O(E log E)   O(E)   no
    Hierholzer's, recursive               O(E log E)   O(E)   no -- but can
                                                                RecursionError


================================================================================
EDGE CASES
================================================================================
    a single ticket              -> trivial 2-city itinerary; the DFS
                                    immediately hits a dead end.
    a city visited MULTIPLE       -> Example 2: JFK appears twice in the
    times in the itinerary          final route -- perfectly legal, cities
                                    can repeat, only TICKETS (edges) are
                                    used exactly once, not cities (nodes).
    multiple tickets between the   -> heapq naturally handles duplicate
    SAME pair of cities              destination strings; each is a
                                    separate entry in that city's heap and
                                    gets consumed independently.
    the itinerary that must         -> the case worked through above --
    "detour and come back" to        the entire reason Hierholzer's
    use every ticket                  commits at dead ends rather than
                                    greedily stopping.
    a long CHAIN-shaped itinerary   -> exactly where the recursive version
    (near the 300-ticket bound)       risks RecursionError; demoed below.
    the problem GUARANTEES a        -> stated in the constraints; this
    valid itinerary exists            solution does not need to detect
                                    "no valid itinerary" as a distinct
                                    outcome (some variants of this problem
                                    do, and would need an Eulerian-path
                                    EXISTENCE check first: at most one node
                                    with outdegree - indegree == 1, the
                                    rest balanced).


================================================================================
COMMON MISTAKES
================================================================================
1. Greedily walking to the lexically smallest destination and STOPPING at
   the first dead end, instead of using the stack-and-commit-at-dead-end
   structure. Silently returns a valid-LOOKING but incomplete itinerary
   that doesn't use every ticket. Demoed live above and in code below.

2. Forgetting to REVERSE the `route` list at the end. Hierholzer's commits
   cities in the ORDER THEY BECOME DEAD ENDS, which is the reverse of
   travel order (the very first city committed is typically the true
   FINAL destination, as seen in the trace: "KUL" is route[0] but ends up
   LAST in the answer).

3. Using recursion for Hierholzer's on a chain-shaped Eulerian path near
   this problem's own 300-ticket bound -- risks RecursionError. The
   iterative stack-based form has no such ceiling.

4. Using a plain sorted LIST per city and calling `.pop(0)` (or worse,
   re-sorting) on every edge consumption instead of a heap -- `.pop(0)` on
   a Python list is O(n) (it shifts every remaining element), silently
   degrading an O(E log E) algorithm toward O(E^2) on cities with many
   outgoing tickets.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the itinerary might not use EVERY ticket -- could no valid
   itinerary exist at all?
A: Then you'd first need to verify an Eulerian path actually exists: the
   underlying graph (restricted to edges with nonzero ticket count) must
   be connected among nodes with edges, and either every node has
   indegree == outdegree (an Eulerian CIRCUIT, can start anywhere) or
   exactly one node has outdegree - indegree == 1 (must be the start,
   here forced to be "JFK" already) and exactly one has indegree -
   outdegree == 1 (the end), with every other node balanced.

Q: How would you find the itinerary using the FEWEST distinct cities
   visited, rather than lexicographically smallest?
A: A fundamentally different objective -- that's no longer a fixed
   Eulerian path question, it becomes closer to a Hamiltonian-path-style
   search (visit fewest NODES, not use every EDGE), generally NP-hard in
   its general form; worth explicitly flagging the complexity jump if
   asked.

Q: Why is a min-heap the right structure for `graph[city]` instead of a
   sorted list?
A: We need REPEATED "give me the smallest remaining item, and remove it"
   operations as edges get consumed one at a time during the DFS --
   exactly what a heap is built for, O(log n) per pop instead of an O(n)
   shift (mistake #4) or an O(n log n) full re-sort after every single
   removal.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 753  Cracking the Safe (De Bruijn sequence construction -- also an
            Eulerian-circuit problem underneath, on a different graph)
    LC 2097 Valid Arrangement of Pairs (Eulerian path existence +
            Hierholzer's, with the start node NOT fixed in advance)
    LC 1192 Critical Connections in a Network (012 -- a different DFS-with-
            careful-bookkeeping graph algorithm, Tarjan's bridges)
================================================================================
"""

import heapq
import sys
from collections import defaultdict
from typing import List


class Solution:
    def findItinerary(self, tickets: List[List[str]]) -> List[str]:
        """✅ Hierholzer's algorithm, iterative stack, lexicographically
        smallest edge first via a per-city min-heap.
        O(E log E) time, O(E) space."""
        graph = defaultdict(list)
        for src, dst in tickets:
            heapq.heappush(graph[src], dst)

        stack = ["JFK"]
        route = []
        while stack:
            while graph[stack[-1]]:
                stack.append(heapq.heappop(graph[stack[-1]]))
            route.append(stack.pop())

        return route[::-1]

    def findItinerary_recursive(self, tickets: List[List[str]]) -> List[str]:
        """Alternative: the textbook RECURSIVE form of Hierholzer's.
        Elegant, but can raise RecursionError on a long chain -- demoed
        below."""
        graph = defaultdict(list)
        for src, dst in tickets:
            heapq.heappush(graph[src], dst)

        route = []

        def visit(city: str) -> None:
            while graph[city]:
                visit(heapq.heappop(graph[city]))
            route.append(city)

        visit("JFK")
        return route[::-1]

    def findItinerary_naive_greedy_BROKEN(self, tickets: List[List[str]]) -> List[str]:
        """✗ BROKEN ON PURPOSE -- mistake #1. Greedily walks to the
        smallest unused destination and stops the moment there is nowhere
        left to go, without the commit-at-dead-end/backtrack structure.
        Demoed live below."""
        graph = defaultdict(list)
        for src, dst in tickets:
            heapq.heappush(graph[src], dst)

        route = ["JFK"]
        city = "JFK"
        while graph[city]:
            city = heapq.heappop(graph[city])
            route.append(city)
        return route


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([["MUC", "LHR"], ["JFK", "MUC"], ["SFO", "SJC"], ["LHR", "SFO"]],
         ["JFK", "MUC", "LHR", "SFO", "SJC"]),
        ([["JFK", "SFO"], ["JFK", "ATL"], ["SFO", "ATL"], ["ATL", "JFK"], ["ATL", "SFO"]],
         ["JFK", "ATL", "JFK", "SFO", "ATL", "SFO"]),
        ([["JFK", "AAA"], ["AAA", "JFK"]], ["JFK", "AAA", "JFK"]),
        ([["JFK", "KUL"], ["JFK", "NRT"], ["NRT", "JFK"]],
         ["JFK", "NRT", "JFK", "KUL"]),
    ]

    print("--- correctness: iterative vs recursive Hierholzer's agree ---")
    for tickets, want in cases:
        got_iter = sol.findItinerary([t[:] for t in tickets])
        got_rec = sol.findItinerary_recursive([t[:] for t in tickets])
        ok = got_iter == want and got_rec == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {tickets!r:<58} -> {got_iter}"
              f"  (want {want})")

    # --------------------------------------------------------------------
    # ⚠️ LIVE DEMO: naive greedy DFS strands two-thirds of the tickets.
    # --------------------------------------------------------------------
    print("\n--- ⚠️  live demo: mistake #1, naive greedy with no backtrack ---")
    tickets = [["JFK", "KUL"], ["JFK", "NRT"], ["NRT", "JFK"]]
    correct = sol.findItinerary([t[:] for t in tickets])
    broken = sol.findItinerary_naive_greedy_BROKEN([t[:] for t in tickets])
    print(f"  tickets = {tickets}")
    print(f"  correct (Hierholzer's):        {correct}  "
          f"(uses all {len(tickets)} tickets)")
    print(f"  broken (naive greedy, no backtrack): {broken}  "
          f"(uses only {len(broken) - 1} ticket(s))")
    exposed = len(broken) - 1 < len(tickets)
    print(f"  the naive version silently STRANDS unused tickets: {exposed}"
          f"  (no exception raised, it just stops early)")
    all_ok &= exposed and correct == ["JFK", "NRT", "JFK", "KUL"]

    # --------------------------------------------------------------------
    # ⚠️ LIVE DEMO: recursion depth on a long chain-shaped itinerary.
    # --------------------------------------------------------------------
    print("\n--- ⚠️  live demo: recursive Hierholzer's on a deep chain ---")
    n = 3000
    chain_tickets = [["JFK" if i == 0 else f"A{i:04d}",
                      "JFK" if i + 1 == n else f"A{i + 1:04d}"]
                     for i in range(n)]
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}, "
          f"chain length = {n} tickets")
    it_result = sol.findItinerary(chain_tickets)
    it_ok = len(it_result) == n + 1
    print(f"  iterative: reconstructed all {len(it_result) - 1} tickets "
          f"successfully -> {it_ok}")
    raised = False
    try:
        sol.findItinerary_recursive(chain_tickets)
        print("  recursive: did NOT raise this run "
              "(depends on interpreter/limit configuration)")
    except RecursionError as e:
        raised = True
        print(f"  recursive: RecursionError -> {e!r}")
    print(f"  iterative succeeded where recursive failed: {it_ok and raised}")
    all_ok &= it_ok and raised

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
