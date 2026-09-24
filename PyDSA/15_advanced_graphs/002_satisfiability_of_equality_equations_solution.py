"""
================================================================================
SOLUTION · LeetCode 990 · Satisfiability of Equality Equations        [Medium]
https://leetcode.com/problems/satisfiability-of-equality-equations/
================================================================================

THE CORE IDEA
--------------
"==" is transitive -- Union-Find IS the transitive closure of an equivalence
relation, for free. Union every "==" pair first. Then a "!=" pair is only a
genuine contradiction if the two variables ended up in the SAME set anyway.

    for eq in equations:
        if eq[1] == '=':                     # "a==b"
            uf.union(a, b)
    for eq in equations:
        if eq[1] == '!':                     # "a!=b"
            if uf.find(a) == uf.find(b):
                return False
    return True

O(n) time (n equations, each an amortized-O(1) Union-Find op), O(1) space
(only 26 possible variables).


================================================================================
WHY TWO SEPARATE PASSES -- NOT ONE INTERLEAVED PASS
================================================================================
The order "process every == first, THEN check every !=" is not a stylistic
choice -- doing it in one interleaved pass, in input order, is WRONG. Take
["a==b", "b!=c", "c==a"]:

    processed in input order, checking != as encountered:
        a==b  -> union(a,b).  {a,b} now one set.
        b!=c  -> find(b) != find(c) at THIS POINT -> looks fine, no contradiction (yet!)
        c==a  -> union(c,a).  Now {a,b,c} all one set.

    But b!=c was declared, and by the end b AND c are forced equal (both
    equal to a). Checking b!=c too early misses the contradiction that only
    exists once the LATER union runs. The correct two-pass version:

        pass 1 (all ==): union(a,b); union(c,a)  -> {a,b,c} one set
        pass 2 (all !=): find(b) == find(c)?  YES (both root to the same
                          set) -> contradiction -> return False   CORRECT

This is exactly Example 4 from the problem statement, and it is the single
most common way this problem is gotten wrong.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): build a graph where "=="
is an edge, then BFS/DFS from each variable to find its full equivalence
class, THEN check every "!=" pair against those classes. Same two-phase
shape as the Union-Find solution, just without the amortized-O(1) benefit
of path compression + union by rank -- O(n * 26) in the worst case instead
of O(n * alpha(26)). Legitimate, more code, no real upside here since the
alphabet is tiny; worth naming to show you know Union-Find is the specialized
tool for exactly this "merge equivalence classes incrementally" shape.

Approach 1 (Union-Find, two pass) [checked] -- the answer above.


================================================================================
STEP BY STEP TRACE
================================================================================
equations = ["a==b", "b==c", "a!=c"]

PASS 1 -- union every "==":
    "a==b": union(a,b). find(a)=a, find(b)=b, ranks equal -> parent[b]=a,
            rank[a]=1.        parent: {a:a, b:a}
    "b==c": union(b,c). find(b)=a (via parent[b]=a), find(c)=c, rank[a]=1
            > rank[c]=0 -> parent[c]=a.
            parent: {a:a, b:a, c:a}      one set: {a,b,c}

PASS 2 -- check every "!=":
    "a!=c": find(a)=a, find(c)=a (walks c->a directly, one hop).
            find(a) == find(c) -> CONTRADICTION -> return False

a, b, c are all forced equal by the two "==" equations (transitively), so
demanding a != c at the same time is unsatisfiable. Correct.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time                Space  Mutates input?
    -------------------------------  ------------------  -----  --------------
    Graph + BFS/DFS equivalence      O(n + 26) per check  O(26)  no
    classes
    Union-Find, two pass [chosen]    O(n * alpha(26))      O(26)  no


================================================================================
EDGE CASES
================================================================================
    "a!=a"                    -> a variable can never differ from itself;
                                  find(a)==find(a) is trivially true, so this
                                  falls out of the SAME code path as any other
                                  contradiction, no special case needed.
    "a==a"                    -> a no-op union (already the same set); safe.
    a variable that never       Union-Find initializes all 26 letters up
    appears in any equation     front, so an unmentioned letter is simply
                                 its own singleton set forever -- never
                                 collides with anything, harmless.
    all equations are "=="      no "!=" pass ever triggers a False -- answer
    (no "!=" at all)             is trivially True.
    contradiction only visible   the whole reason for the two-pass order --
    after a LATER "=="            see the "why two passes" section above.
    equation, e.g. Example 4
    self-consistent duplicate    "a==b","a==b" -- second union is a no-op
    equations                    (already same root), harmless.


================================================================================
COMMON MISTAKES
================================================================================
1. Interleaving the "==" and "!=" checks in input order instead of doing
   two full passes. Demonstrated as broken, live, in the runtime demo below
   using Example 4 from the problem statement.

2. Treating "a!=a" as needing a special-case check ("if a == b: return
   False" using CHARACTER equality). It doesn't -- Union-Find's own
   find(a) == find(a) already handles it correctly since a variable is
   always in its own set at minimum, no character-level special case needed.

3. Forgetting that the alphabet is FIXED at 26 lowercase letters and trying
   to build a dynamic Union-Find keyed by string -- unnecessary complexity;
   `ord(ch) - ord('a')` gives a dense 0..25 index directly.

4. Doing the "!=" pass BEFORE the "==" pass finishes (see the interleaving
   mistake above) -- the single most common bug in this problem.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if variables could be full words instead of single letters?
A: Union-Find keyed by a dict mapping string -> index (or storing parent as
   a dict directly) instead of a fixed 26-slot array; the algorithm is
   otherwise unchanged.

Q: What if there were also a "<" (less than) relation to satisfy jointly?
A: That is no longer pure equivalence -- Union-Find alone cannot express
   ordering constraints. That shape needs a difference-constraint graph and
   Bellman-Ford (detect a negative cycle among the "<" edges), a genuinely
   different tool from this topic (see the topic guide Part 2).

Q: Can you return WHICH equation causes the first contradiction, not just
   True/False?
A: Yes -- track the ORIGINAL "==" equation that most recently caused the
   union which created the offending pair's shared root, or simply report
   the specific "!=" equation whose find() check first failed; both are a
   small bookkeeping addition on top of the same two-pass skeleton.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 547  Number of Provinces (001 -- Union-Find used to COUNT groups,
            not check consistency)
    LC 1061 Lexicographically Smallest Equivalent String (Union-Find with a
            custom "keep the smaller representative" merge rule)
    LC 1101 The Earliest Moment When Everyone Become Friends (Union-Find
            merged incrementally, tracking WHEN the last merge happened)
    LC 399  Evaluate Division (equivalence + a numeric ratio attached to
            each union -- weighted Union-Find, one level up from this problem)
================================================================================
"""

from typing import List


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n

    def find(self, x: int) -> int:
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x: int, y: int) -> bool:
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        return True


class Solution:
    def equationsPossible(self, equations: List[str]) -> bool:
        """✅ Union-Find, two passes. O(n) time, O(1) space (26 variables)."""
        uf = UnionFind(26)

        def idx(ch: str) -> int:
            return ord(ch) - ord('a')

        # Pass 1: union every "==" pair FIRST, so transitivity is fully
        # resolved before any "!=" is checked.
        for eq in equations:
            if eq[1] == '=':
                uf.union(idx(eq[0]), idx(eq[3]))

        # Pass 2: a "!=" is a contradiction iff the two ended up connected.
        for eq in equations:
            if eq[1] == '!':
                if uf.find(idx(eq[0])) == uf.find(idx(eq[3])):
                    return False
        return True

    def equationsPossible_interleaved_BROKEN(self, equations: List[str]) -> bool:
        """✗ BROKEN ON PURPOSE -- mistake #1. Checks "!=" in input order
        instead of after all unions complete; misses contradictions that
        only become visible after a LATER "==" equation. Demoed live below."""
        uf = UnionFind(26)

        def idx(ch: str) -> int:
            return ord(ch) - ord('a')

        for eq in equations:
            a, b = idx(eq[0]), idx(eq[3])
            if eq[1] == '=':
                uf.union(a, b)
            else:
                if uf.find(a) == uf.find(b):
                    return False
        return True


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (["a==b", "b!=a"], False),
        (["b==a", "a==b"], True),
        (["a==b", "b==c", "a==c"], True),
        (["a==b", "b!=c", "c==a"], False),
        (["c==c", "b==d", "x!=z"], True),
        (["a==a"], True),
        (["a!=a"], False),
        (["a==b", "c==d", "b==c", "a!=d"], False),
        (["a==b", "c==d", "b==c"], True),
    ]

    print("--- correctness ---")
    for eqs, want in cases:
        got = sol.equationsPossible(eqs)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {eqs!r:<40} -> {got}  (want {want})")

    # --------------------------------------------------------------------
    # ⚠️ LIVE DEMO: the interleaved version fails EXACTLY the case the
    # topic guide/prose above says it fails -- Example 4 from LeetCode.
    # --------------------------------------------------------------------
    print("\n--- ⚠️  live demo: interleaved (wrong-order) checking ---")
    trap_cases = [
        (["a==b", "b!=c", "c==a"], False),
        (["a==b", "b==c", "c!=a", "d==a"], False),
    ]
    exposed = False
    for eqs, want in trap_cases:
        correct = sol.equationsPossible(eqs)
        broken = sol.equationsPossible_interleaved_BROKEN(eqs)
        print(f"  {eqs!r}")
        print(f"    two-pass (correct):        {correct}  (want {want})")
        print(f"    interleaved (input order):  {broken}")
        if broken != correct:
            exposed = True
        all_ok &= (correct == want)
    print(f"  interleaved order disagreed with the correct two-pass answer: "
          f"{exposed}")
    print("  The '!=' equation gets checked BEFORE the later '==' equation")
    print("  that would have proven it contradictory -- no exception is")
    print("  raised, it just silently returns the wrong boolean.")
    all_ok &= exposed   # we WANT to have proven the bug is real

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
