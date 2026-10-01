"""
================================================================================
SOLUTION · LeetCode 752 · Open the Lock                                 [Medium]
https://leetcode.com/problems/open-the-lock/
================================================================================

THE CORE IDEA
--------------
Model the lock as an IMPLICIT GRAPH: each of the 10^4 codes is a node, each
single-wheel turn is an edge (8 per node), deadends are removed nodes. The
minimum number of moves is the unweighted shortest path, so BFS. Neighbors
are generated on demand; the graph is never built.


================================================================================
APPROACH 1 · BFS from "0000" ✅ (the answer)
================================================================================
    if "0000" in dead: return -1
    queue, seen, steps = deque(["0000"]), dead | {"0000"}, 0
    while queue:
        for _ in range(len(queue)):
            code = queue.popleft()
            if code == target:
                return steps
            for nxt in neighbors(code):
                if nxt not in seen:
                    seen.add(nxt)            # mark on ENQUEUE
                    queue.append(nxt)
        steps += 1
    return -1

Putting deadends into `seen` up front means they're never enqueued. One set,
one membership test.

    Time: O(N * W * D) with N = 10^4 codes, W = 4 wheels, D = 2 directions
          (plus O(W) to build each neighbor string)
    Space: O(N)


================================================================================
APPROACH 2 · Bidirectional BFS
================================================================================
Grow two frontiers, one from "0000" and one from target, always expanding the
smaller. Stop when a newly generated code is in the other frontier.

With branching factor b and distance d, one-sided BFS explores about b^d
nodes; two half-depth searches explore about 2 * b^(d/2). Here the state space
is only 10^4, so both finish quickly; the demo counts how many codes each
actually expands.


================================================================================
APPROACH 3 · A* with a wheel-distance heuristic
================================================================================
h(code) = sum over wheels of min(|a - b|, 10 - |a - b|). It never overestimates
(each move changes one wheel by one), so A* stays optimal. Worth naming; the
BFS is what the interviewer expects.


================================================================================
STEP BY STEP TRACE · deadends = ["8888"], target = "0009"
================================================================================
    level 0: ["0000"]                  target? no
    level 1: generate 8 neighbours of 0000:
             1000 9000 0100 0900 0010 0090 0001 0009
             none are dead -> all enqueued
             dequeue ... 0009 == target -> return 1


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                 Time (worst)           Space   Mutates input?
    -----------------------  ---------------------  ------  --------------
    BFS ✅                   O(10^4 * 8 * 4)        O(10^4) No
    Bidirectional BFS        same bound, fewer      O(10^4) No
                             expansions in practice
    A*                       O(10^4 log 10^4)       O(10^4) No


================================================================================
EDGE CASES
================================================================================
    "0000" is a deadend       -1 immediately (you can't even start).
    target == "0000"          0 moves.
    Target walled in          All 8 neighbours dead -> -1.
    Start walled in           All 8 neighbours of 0000 dead -> -1.
    Wrap-around               0 -> 9 is one move: (d - 1) % 10 in Python.
                              In Java/C++/Go, % of a negative is negative:
                              use (d + 9) % 10.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to check "0000" against deadends. Demo below: returns a number
   instead of -1.

2. Marking visited on DEQUEUE. Still correct for unweighted BFS, but a code
   can be enqueued many times from different neighbors before it's processed.
   Demo below counts the extra queue pushes.

3. Using (d - 1) % 10 in a language where % can return negatives.

4. Returning when you ENQUEUE target but counting steps inconsistently. Pick
   one convention (check on dequeue, or on generate with steps + 1).

5. DFS. Finds A path, not the SHORTEST path.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Wheels have different sizes, or n wheels?
A: Same BFS; state space is the product of wheel sizes, so watch out for
   explosion. Bidirectional BFS or A* start to matter a lot.

Q: Some moves cost more (turning wheel 1 costs 2)?
A: Weighted edges -> Dijkstra. If costs are only 0 or 1, 0-1 BFS with a deque
   (15_advanced_graphs/015).

Q: Return the actual sequence of codes?
A: Store parent[code] when enqueuing; walk back from target.

Q: Minimum Genetic Mutation / Word Ladder?
A: Same pattern: implicit graph, nodes are strings, edges are single edits.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 127   Word Ladder (016)                  — implicit graph over words
    LC 433   Minimum Genetic Mutation
    LC 773   Sliding Puzzle                     — board states as nodes
    LC 1368  Min Cost Valid Path (15/015)       — 0-1 BFS when edges cost 0 or 1
================================================================================
"""

import random
import time
from collections import deque
from typing import Iterator, List, Tuple


def neighbors(code: str) -> Iterator[str]:
    for i in range(4):
        d = ord(code[i]) - 48
        for step in (1, 9):                        # +1 and -1 mod 10
            yield code[:i] + chr(48 + (d + step) % 10) + code[i + 1:]


class Solution:
    def openLock(self, deadends: List[str], target: str) -> int:
        seen = set(deadends)
        if "0000" in seen:
            return -1
        seen.add("0000")
        queue = deque(["0000"])
        steps = 0
        while queue:
            for _ in range(len(queue)):
                code = queue.popleft()
                if code == target:
                    return steps
                for nxt in neighbors(code):
                    if nxt not in seen:
                        seen.add(nxt)
                        queue.append(nxt)
            steps += 1
        return -1


# ------------------------------------------------------------------------
# Alternatives / broken versions / instrumented versions for the demos.
# ------------------------------------------------------------------------
def open_lock_bidirectional(deadends: List[str], target: str) -> Tuple[int, int]:
    """Returns (moves, codes expanded)."""
    dead = set(deadends)
    if "0000" in dead:
        return -1, 0
    if target == "0000":
        return 0, 0
    front, back = {"0000"}, {target}
    seen = {"0000", target}
    steps = expanded = 0
    while front and back:
        if len(front) > len(back):
            front, back = back, front
        steps += 1
        nxt_front = set()
        for code in front:
            expanded += 1
            for nxt in neighbors(code):
                if nxt in back:
                    return steps, expanded
                if nxt not in seen and nxt not in dead:
                    seen.add(nxt)
                    nxt_front.add(nxt)
        front = nxt_front
    return -1, expanded


def open_lock_counting(deadends: List[str], target: str, mark_on_enqueue: bool) -> Tuple[int, int, int]:
    """Returns (moves, codes expanded, queue pushes)."""
    dead = set(deadends)
    if "0000" in dead:
        return -1, 0, 0
    seen = set(dead)
    queue = deque(["0000"])
    if mark_on_enqueue:
        seen.add("0000")
    steps = expanded = pushes = 0
    while queue:
        for _ in range(len(queue)):
            code = queue.popleft()
            if not mark_on_enqueue:
                if code in seen:
                    continue
                seen.add(code)
            expanded += 1
            if code == target:
                return steps, expanded, pushes
            for nxt in neighbors(code):
                if nxt not in seen:
                    if mark_on_enqueue:
                        seen.add(nxt)
                    queue.append(nxt)
                    pushes += 1
        steps += 1
    return -1, expanded, pushes


def open_lock_no_start_check_bug(deadends: List[str], target: str) -> int:
    """Mistake 1: never checks whether "0000" is itself a deadend."""
    seen = set(deadends) | {"0000"}
    queue = deque(["0000"])
    steps = 0
    while queue:
        for _ in range(len(queue)):
            code = queue.popleft()
            if code == target:
                return steps
            for nxt in neighbors(code):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(nxt)
        steps += 1
    return -1


def wheel_distance(a: str, b: str) -> int:
    return sum(min(abs(int(x) - int(y)), 10 - abs(int(x) - int(y))) for x, y in zip(a, b))


# ==============================================================================
# TESTS — run:  python 018_open_the_lock_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: BFS vs bidirectional BFS ---")
    cases = [
        (["0201", "0101", "0102", "1212", "2002"], "0202", 6),
        (["8888"], "0009", 1),
        (["8887", "8889", "8878", "8898", "8788", "8988", "7888", "9888"], "8888", -1),
        (["0000"], "8888", -1),
        (["1111"], "0000", 0),
        ([], "5555", 20),
        (["0001", "0010", "0100", "1000", "0009", "0090", "0900", "9000"], "1111", -1),
    ]
    for deadends, target, want in cases:
        a = sol.openLock(deadends, target)
        b, _ = open_lock_bidirectional(deadends, target)
        ok = a == b == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  target={target}  bfs={a}  bidirectional={b}  want={want}")

    print("\n--- with no deadends, BFS distance == per-wheel circular distance (300 targets) ---")
    rng = random.Random(752)
    bad = 0
    for _ in range(300):
        target = "".join(rng.choice("0123456789") for _ in range(4))
        if sol.openLock([], target) != wheel_distance("0000", target):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  BFS matches the closed-form distance on 300 random targets")

    print("\n--- randomized: BFS == bidirectional with random deadends (200 cases) ---")
    bad = 0
    for _ in range(200):
        dead = list({"".join(rng.choice("0123456789") for _ in range(4)) for _ in range(rng.randint(0, 400))})
        target = "".join(rng.choice("0123456789") for _ in range(4))
        if target in dead:
            dead.remove(target)
        if sol.openLock(dead, target) != open_lock_bidirectional(dead, target)[0]:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  200 random deadend sets agree")

    print("\n--- mistake 1 LIVE: '0000' is a deadend ---")
    wrong, right = open_lock_no_start_check_bug(["0000"], "8888"), sol.openLock(["0000"], "8888")
    ok = wrong != -1 and right == -1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  deadends=['0000']: unchecked version returns {wrong}, correct -1")

    print("\n--- mistake 2 LIVE: mark visited on dequeue vs on enqueue ---")
    target = "5555"
    a = open_lock_counting([], target, mark_on_enqueue=True)
    b = open_lock_counting([], target, mark_on_enqueue=False)
    ok = a[0] == b[0] == 20 and b[2] > a[2]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  target 5555: both answer {a[0]} moves")
    print(f"      mark on enqueue: {a[2]:>7,} queue pushes")
    print(f"      mark on dequeue: {b[2]:>7,} queue pushes ({b[2] / a[2]:.1f}x — same answer, far more work)")

    print("\n--- bidirectional BFS: codes expanded ---")
    for target in ("0202", "5555", "3737"):
        moves, exp_one, _ = open_lock_counting(["0201", "0101", "0102", "1212", "2002"], target, True)
        moves2, exp_two = open_lock_bidirectional(["0201", "0101", "0102", "1212", "2002"], target)
        print(f"      target {target}: {moves} moves; one-sided expands {exp_one:>5,} codes, bidirectional {exp_two:>5,}")
        all_ok &= moves == moves2

    t0 = time.perf_counter()
    for _ in range(20):
        sol.openLock([], "5555")
    t1 = time.perf_counter()
    for _ in range(20):
        open_lock_bidirectional([], "5555")
    t2 = time.perf_counter()
    print(f"      time for target 5555: one-sided {(t1 - t0) / 20 * 1000:.1f} ms, bidirectional {(t2 - t1) / 20 * 1000:.1f} ms")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
