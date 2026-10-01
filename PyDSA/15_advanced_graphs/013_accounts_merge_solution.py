"""
================================================================================
SOLUTION · LeetCode 721 · Accounts Merge                                [Medium]
https://leetcode.com/problems/accounts-merge/
================================================================================

THE CORE IDEA
--------------
Emails are nodes; each account connects all of its emails. People are the
CONNECTED COMPONENTS. Union-Find: union every email in an account with that
account's first email, then group all emails by their root, sort each group,
and attach the name recorded for any email in the group.


================================================================================
APPROACH 1 · Repeatedly merge overlapping sets (priced, used as oracle)
================================================================================
Keep a list of email sets. Loop: find any two sets that intersect, merge them,
restart. Stop when no pair intersects.

    Time: O(A^2 * L) per pass, up to A passes -> O(A^3 * L)
    Space: O(E)


================================================================================
APPROACH 2 · Union-Find over emails ✅ (the answer)
================================================================================
    parent = {}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]       # path halving
            x = parent[x]
        return x

    owner = {}
    for name, *emails in accounts:
        for e in emails:
            parent.setdefault(e, e)
            owner[e] = name
            union(emails[0], e)

    groups = defaultdict(list)
    for e in parent:
        groups[find(e)].append(e)
    return [[owner[root]] + sorted(es) for root, es in groups.items()]

WHY UNION WITH THE FIRST EMAIL IS ENOUGH. Connecting each email to one anchor
makes all of the account's emails one component (a star instead of a clique).
Connectivity is all that matters, so L - 1 unions per account suffice.

    Time: O(E * α(E)) unions/finds + O(E log E) sorting
    Space: O(E)


================================================================================
APPROACH 3 · Build the email graph, DFS components
================================================================================
Adjacency: edge between the first email and every other email of an account.
DFS from each unvisited email collects a component.

    Time: O(E log E)    Space: O(E) — and recursion depth up to E; use an
    explicit stack in Python.


================================================================================
STEP BY STEP TRACE · Example 1
================================================================================
    account 0 John: johnsmith, john_newyork   union(johnsmith, john_newyork)
    account 1 John: johnsmith, john00         union(johnsmith, john00)
    account 2 Mary: mary                      (singleton)
    account 3 John: johnnybravo               (singleton)

    components (by root):
        {johnsmith, john_newyork, john00} -> sorted, name John
        {mary}                            -> Mary
        {johnnybravo}                     -> John

    Two separate "John" results: same name, no shared email, different people.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time                  Space   Mutates input?
    ------------------------------  --------------------  ------  --------------
    Merge overlapping sets          O(A^3 * L)            O(E)    No
    Union-Find over emails ✅       O(E α(E) + E log E)   O(E)    No
    Graph + iterative DFS           O(E log E)            O(E)    No


================================================================================
EDGE CASES
================================================================================
    Same email listed twice in one account   Deduplicated by the parent map.
    Same name, disjoint emails               Stay separate.
    Chain of overlaps A-B, B-C               All merge (transitivity).
    One account                              Returned with sorted emails.


================================================================================
COMMON MISTAKES
================================================================================
1. Merging by NAME. Two different Johns become one person. Demo below.

2. Only merging accounts that overlap DIRECTLY with each other in one pass.
   A-B and B-C overlap, A-C don't: a single pass that compares only pairs
   misses the transitive merge unless it repeats. Union-Find handles it for
   free. Demo below.

3. Forgetting to dedupe emails (returning "a@x" twice).

4. Returning emails unsorted.

5. Recursive DFS on a component of 10,000 emails -> RecursionError in CPython.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Accounts arrive as a stream; answer "same person?" online?
A: Union-Find is already incremental: union on arrival, compare roots on query.

Q: Billions of accounts (entity resolution at scale)?
A: Connected components on a distributed graph: iterative label propagation
   (each node takes the min label of its neighbors) in MapReduce/Spark/Pregel,
   or union-find per shard with a merge step. Plan for giant components caused
   by shared junk identifiers like "noreply@..." and filter them.

Q: Emails AND phone numbers can link accounts?
A: Same algorithm; nodes are any identifiers. Prefix them ("e:", "p:") so
   values don't collide.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 547   Number of Provinces (001)          — components via union-find
    LC 990   Satisfiability of Equality Equations (002)
    LC 684   Redundant Connection (14_graphs/013)
    LC 1202  Smallest String With Swaps         — union-find then sort each group
================================================================================
"""

import random
from collections import defaultdict
from typing import Dict, List


class Solution:
    def accountsMerge(self, accounts: List[List[str]]) -> List[List[str]]:
        parent: Dict[str, str] = {}
        owner: Dict[str, str] = {}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for account in accounts:
            name, first = account[0], account[1]
            for email in account[1:]:
                parent.setdefault(email, email)
                owner[email] = name
                ra, rb = find(first), find(email)
                if ra != rb:
                    parent[rb] = ra

        groups: Dict[str, List[str]] = defaultdict(list)
        for email in parent:
            groups[find(email)].append(email)
        return [[owner[root]] + sorted(emails) for root, emails in groups.items()]


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def merge_dfs(accounts: List[List[str]]) -> List[List[str]]:
    graph: Dict[str, List[str]] = defaultdict(list)
    owner: Dict[str, str] = {}
    for account in accounts:
        first = account[1]
        for email in account[1:]:
            graph[first].append(email)
            graph[email].append(first)
            owner[email] = account[0]
    seen = set()
    out = []
    for email in graph:
        if email in seen:
            continue
        seen.add(email)
        stack, comp = [email], []
        while stack:
            e = stack.pop()
            comp.append(e)
            for nb in graph[e]:
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        out.append([owner[email]] + sorted(comp))
    return out


def merge_oracle(accounts: List[List[str]]) -> List[List[str]]:
    groups = [(a[0], set(a[1:])) for a in accounts]
    changed = True
    while changed:
        changed = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                if groups[i][1] & groups[j][1]:
                    groups[i] = (groups[i][0], groups[i][1] | groups[j][1])
                    groups.pop(j)
                    changed = True
                    break
            if changed:
                break
    return [[name] + sorted(emails) for name, emails in groups]


def merge_by_name_bug(accounts: List[List[str]]) -> List[List[str]]:
    """Mistake 1: treats the name as the identity."""
    by_name: Dict[str, set] = defaultdict(set)
    for account in accounts:
        by_name[account[0]].update(account[1:])
    return [[name] + sorted(emails) for name, emails in by_name.items()]


def merge_single_pass_bug(accounts: List[List[str]]) -> List[List[str]]:
    """Mistake 2: merges each account into the FIRST earlier group it overlaps, once."""
    groups: List[tuple] = []
    for account in accounts:
        emails = set(account[1:])
        for i, (name, g) in enumerate(groups):
            if g & emails:
                groups[i] = (name, g | emails)
                break
        else:
            groups.append((account[0], emails))
    return [[name] + sorted(g) for name, g in groups]


def norm(result: List[List[str]]) -> List[List[str]]:
    return sorted(result)


# ==============================================================================
# TESTS — run:  python 013_accounts_merge_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    example1 = [["John", "johnsmith@mail.com", "john_newyork@mail.com"],
                ["John", "johnsmith@mail.com", "john00@mail.com"],
                ["Mary", "mary@mail.com"],
                ["John", "johnnybravo@mail.com"]]

    print("--- correctness: union-find vs DFS vs repeated-merge oracle ---")
    cases = [
        (example1,
         [["John", "john00@mail.com", "john_newyork@mail.com", "johnsmith@mail.com"],
          ["John", "johnnybravo@mail.com"],
          ["Mary", "mary@mail.com"]]),
        ([["A", "a@x", "b@x"], ["A", "c@x"], ["A", "b@x", "c@x"]], [["A", "a@x", "b@x", "c@x"]]),
        ([["A", "a@x", "a@x"]], [["A", "a@x"]]),
        ([["A", "a@x"], ["B", "b@x"]], [["A", "a@x"], ["B", "b@x"]]),
    ]
    for accounts, want in cases:
        a, b, c = norm(sol.accountsMerge(accounts)), norm(merge_dfs(accounts)), norm(merge_oracle(accounts))
        ok = a == b == c == norm(want)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {a}")

    print("\n--- randomized cross-check (300 inputs) ---")
    rng = random.Random(721)
    bad = 0
    for _ in range(300):
        pool = [f"e{i}@x" for i in range(rng.randint(2, 25))]
        people = {}
        accounts = []
        for _ in range(rng.randint(1, 12)):
            emails = rng.sample(pool, rng.randint(1, min(4, len(pool))))
            # All accounts in one component must share a name, per the problem.
            name = "P"
            accounts.append([name] + emails)
        want = norm(merge_oracle(accounts))
        if norm(sol.accountsMerge(accounts)) != want or norm(merge_dfs(accounts)) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  300 random inputs agree with the repeated-merge oracle")

    print("\n--- mistake 1 LIVE: merging by name ---")
    wrong = norm(merge_by_name_bug(example1))
    right = norm(sol.accountsMerge(example1))
    ok = len(wrong) == 2 and len(right) == 3
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  example 1: by-name gives {len(wrong)} people, correct is {len(right)}")
    print("      johnnybravo@mail.com was folded into the other John's account")

    print("\n--- mistake 2 LIVE: one-pass merge misses transitive links ---")
    chain = [["A", "a@x"], ["A", "c@x"], ["A", "a@x", "c@x"]]   # third account bridges the first two
    wrong = norm(merge_single_pass_bug(chain))
    right = norm(sol.accountsMerge(chain))
    ok = len(wrong) == 2 and right == [["A", "a@x", "c@x"]]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {chain}")
    print(f"      single pass -> {wrong}")
    print(f"      union-find  -> {right}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
