"""
================================================================================
QUESTION · LeetCode 269 · Alien Dictionary                              [Hard]
https://leetcode.com/problems/alien-dictionary/
================================================================================

PROBLEM
-------
There is a new alien language that uses the English alphabet. However, the
order among the letters is unknown to you.

You are given a list of strings `words` from the alien language's
dictionary, where the strings in `words` are SORTED LEXICOGRAPHICALLY by
the rules of this new language.

Derive the order of letters in this language, and return it. If the given
information is not enough to determine the order, return "". If the given
information is contradictory (invalid), return "".


EXAMPLES
--------
Example 1:
    Input:  words = ["wrt","wrf","er","ett","rftt"]
    Output: "wertf"

Example 2:
    Input:  words = ["z","x"]
    Output: "zx"

Example 3:
    Input:  words = ["z","x","z"]
    Output: ""
    Explanation: The order is invalid: z comes before x, but z should also
    come after x according to another pair -- a contradiction (cycle).


CONSTRAINTS
-----------
    1 <= words.length <= 100
    1 <= words[i].length <= 100
    words[i] consists of only lowercase English letters.

(NOTE: LeetCode's official constraints additionally guarantee a total input
size bound; the classic gotcha below -- one word being a strict PREFIX
EXTENSION of the previous word in the WRONG order -- is still testable and
must be handled.)


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Compare each pair of ADJACENT words to find the FIRST position where they
differ -- that single character pair tells you one ordering constraint
(the earlier word's character must come before the later word's character
in the alien alphabet). Collect all such constraints as directed edges,
then topologically sort them (topic guide Part 7). Two ways this can fail:

    1. A CYCLE in the derived constraints -- contradictory ordering, no
       valid alphabet exists.
    2. A word is a STRICT PREFIX of the PREVIOUS word (e.g. ["abc","ab"])
       -- for two words to be validly sorted where one is a prefix of the
       other, the SHORTER one must come first (like "ab" < "abc" in normal
       dictionary order). If the longer one appears first, it's invalid --
       there is no character-level difference to derive a constraint from,
       and no valid alien ordering can produce that sequence.

PROGRESSIVE HINTS
------------------
Hint 1: For each adjacent pair of words, walk both simultaneously until
        the first index where the characters differ; that gives you one
        directed edge (earlier char -> later char).
Hint 2: If no such index exists (one word is a full prefix of the other),
        check: is the FIRST word longer than the second? If so, invalid.
Hint 3: Build an indegree count for every letter that actually APPEARS
        anywhere in the input words (not just the 26-letter alphabet).
Hint 4: Kahn's BFS topological sort (topic guide Part 7). If the resulting
        order doesn't include every letter that appeared, there's a cycle
        -- return "".

COMPLEXITY TARGET
------------------
    Time:  O(C) where C is the total length of all words (building edges)
           + O(V + E) for the topological sort, V,E bounded by the alphabet
    Space: O(1) effectively (at most 26 letters and their edges)
================================================================================
"""

from typing import List


class Solution:
    def alienOrder(self, words: List[str]) -> str:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    def valid_order(words: List[str], order) -> bool:
        """Check `order` is a topological order consistent with `words`."""
        if not order:
            return False
        pos = {ch: i for i, ch in enumerate(order)}
        if len(pos) != len(order):
            return False
        for a, b in zip(words, words[1:]):
            m = min(len(a), len(b))
            i = 0
            while i < m and a[i] == b[i]:
                i += 1
            if i == m:
                if len(a) > len(b):
                    return False
                continue
            if a[i] not in pos or b[i] not in pos or pos[a[i]] >= pos[b[i]]:
                return False
        return True

    cases = [
        (["wrt", "wrf", "er", "ett", "rftt"], True),
        (["z", "x"], True),
        (["z", "x", "z"], False),       # cycle -> invalid, expect ""
        (["abc", "ab"], False),         # invalid prefix order
        (["ab", "abc"], True),
        (["a", "b", "ca", "cc"], True),
    ]
    for words, should_be_valid in cases:
        got = sol.alienOrder(list(words))
        if should_be_valid:
            ok = valid_order(words, got) and set(got) == set("".join(words))
        else:
            ok = got == ""
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {words!r:<32} -> {got!r}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
