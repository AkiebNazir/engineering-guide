"""
================================================================================
LeetCode 721 · Accounts Merge                                           [Medium]
https://leetcode.com/problems/accounts-merge/
Topic: 15 · Advanced Graphs
================================================================================

PROBLEM
-------
Given a list of `accounts` where each element accounts[i] is a list of
strings, the first element accounts[i][0] is a name, and the rest are emails
belonging to that account.

Two accounts definitely belong to the same person if they share at least one
common email. Two accounts with the same NAME may belong to different people;
names are not identifiers. A person can have any number of accounts, but all
their accounts share the same name.

After merging, return the accounts in this format: the first element is the
name, the rest are the emails IN SORTED ORDER. The accounts themselves can be
returned in any order.


EXAMPLES
--------
Example 1:
    Input:
        [["John","johnsmith@mail.com","john_newyork@mail.com"],
         ["John","johnsmith@mail.com","john00@mail.com"],
         ["Mary","mary@mail.com"],
         ["John","johnnybravo@mail.com"]]
    Output:
        [["John","john00@mail.com","john_newyork@mail.com","johnsmith@mail.com"],
         ["Mary","mary@mail.com"],
         ["John","johnnybravo@mail.com"]]
    Explanation: The first two Johns share johnsmith@mail.com. The third John
                 shares nothing, so he's a different person.

Example 2:
    Input:
        [["Gabe","Gabe0@m.co","Gabe3@m.co","Gabe1@m.co"],
         ["Kevin","Kevin3@m.co","Kevin5@m.co","Kevin0@m.co"],
         ["Ethan","Ethan5@m.co","Ethan4@m.co","Ethan0@m.co"],
         ["Hanzo","Hanzo3@m.co","Hanzo1@m.co","Hanzo0@m.co"],
         ["Fern","Fern5@m.co","Fern1@m.co","Fern0@m.co"]]
    Output: each account unchanged except emails sorted.


CONSTRAINTS
-----------
    1 <= accounts.length <= 1000
    2 <= accounts[i].length <= 10
    1 <= accounts[i][j].length <= 30
    accounts[i][0] consists of English letters.
    accounts[i][j] (for j > 0) is a valid email.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is CONNECTED COMPONENTS in disguise. Emails are nodes. Every account says
"all of these emails are connected". Merging is transitive: if A shares an
email with B and B shares one with C, all three are one person even if A and C
share nothing.

Union-Find is the natural tool: union every email in an account with the
account's first email, then group emails by their root.


WHAT TO THINK ABOUT
--------------------
1. What are the nodes: accounts or emails? Either works; which is simpler?

2. How do you remember which name belongs to a component?

3. Why is merging by NAME wrong?


PROGRESSIVE HINTS
------------------
Hint 1: Map each email to an integer id (or use the email string as the key)
        and remember email -> name.

Hint 2: For each account, union(email[1], email[j]) for every j >= 2.

Hint 3: Group emails by find(email), sort each group, prepend the name.


COMPLEXITY TARGET
------------------
    Time:  O(E * α(E) + E log E), E = total emails (log term from sorting)
    Space: O(E)
================================================================================
"""

from typing import List


class Solution:
    def accountsMerge(self, accounts: List[List[str]]) -> List[List[str]]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 013_accounts_merge_question.py
# ==============================================================================
def normalize(result: List[List[str]]) -> List[List[str]]:
    return sorted(result or [])


def run_tests() -> None:
    cases = [
        ([["John", "johnsmith@mail.com", "john_newyork@mail.com"],
          ["John", "johnsmith@mail.com", "john00@mail.com"],
          ["Mary", "mary@mail.com"],
          ["John", "johnnybravo@mail.com"]],
         [["John", "john00@mail.com", "john_newyork@mail.com", "johnsmith@mail.com"],
          ["John", "johnnybravo@mail.com"],
          ["Mary", "mary@mail.com"]]),
        ([["A", "a@x", "b@x"], ["A", "c@x"], ["A", "b@x", "c@x"]],
         [["A", "a@x", "b@x", "c@x"]]),
        ([["A", "a@x", "a@x"]], [["A", "a@x"]]),
        ([["A", "a@x"], ["B", "b@x"]], [["A", "a@x"], ["B", "b@x"]]),
    ]
    all_ok = True
    for accounts, want in cases:
        got = Solution().accountsMerge([list(a) for a in accounts])
        ok = got is not None and normalize(got) == normalize(want)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  got={normalize(got) if got else got}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
