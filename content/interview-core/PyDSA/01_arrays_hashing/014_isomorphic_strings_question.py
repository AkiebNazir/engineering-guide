"""
================================================================================
LeetCode 205 · Isomorphic Strings                                         [Easy]
https://leetcode.com/problems/isomorphic-strings/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given two strings `s` and `t`, determine if they are isomorphic.

Two strings are isomorphic if the characters in `s` can be replaced to get
`t`. Every occurrence of a character must be replaced with the same
character, keeping the order. No two characters may map to the same
character, but a character may map to itself.


EXAMPLES
--------
Example 1:   s = "egg",   t = "add"    ->  true    (e->a, g->d)
Example 2:   s = "foo",   t = "bar"    ->  false   (o would need to map to a AND r)
Example 3:   s = "paper", t = "title"  ->  true    (p->t, a->i, e->l, r->e)
Example 4:   s = "badc",  t = "baba"   ->  false   (b->b and d->b: two chars map to b)


CONSTRAINTS
-----------
    1 <= s.length <= 5 * 10^4
    t.length == s.length
    s and t consist of any valid ASCII characters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Isomorphic" means a ONE-TO-ONE mapping (a bijection) between the characters
used. There are two separate rules, and each one catches different failures:

    1. Consistency: the same s-char always maps to the same t-char.
       "foo" / "bar" fails this rule.
    2. Injectivity: two different s-chars never map to the same t-char.
       "badc" / "baba" passes rule 1 and fails only this one.

Most wrong answers check only rule 1.


WHAT TO THINK ABOUT
--------------------
1. One dict s->t enforces rule 1. What enforces rule 2?

2. Another way to see it: replace each character with the index of its FIRST
   occurrence. "paper" -> [0,1,0,3,4], "title" -> [0,1,0,3,4]. When are two
   strings isomorphic in terms of these patterns?


PROGRESSIVE HINTS
------------------
Hint 1: Walk both strings together with zip.

Hint 2: Keep s_to_t and t_to_s. For each pair (a, b), if a is already mapped
        to something other than b, fail; if b is already mapped from something
        other than a, fail.

Hint 3: Otherwise record both directions and continue.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(alphabet) — at most 128 ASCII characters per map
================================================================================
"""


class Solution:
    def isIsomorphic(self, s: str, t: str) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 014_isomorphic_strings_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ("egg", "add", True),
        ("foo", "bar", False),
        ("paper", "title", True),
        ("badc", "baba", False),
        ("a", "a", True),
        ("ab", "aa", False),
        ("aa", "ab", False),
        ("13", "42", True),
    ]
    all_ok = True
    for s, t, want in cases:
        got = Solution().isIsomorphic(s, t)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r} t={t!r}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
