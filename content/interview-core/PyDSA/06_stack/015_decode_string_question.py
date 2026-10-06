"""
================================================================================
LeetCode 394 · Decode String                                            [Medium]
https://leetcode.com/problems/decode-string/
Topic: 06 · Stack & Monotonic Stack
================================================================================

PROBLEM
-------
Given an encoded string, return its decoded string.

The encoding rule is k[encoded_string]: the encoded_string inside the square
brackets is repeated exactly k times. k is a positive integer. Brackets can be
nested.

The input is always valid: no extra spaces, brackets are well formed, digits
appear only as repeat counts (never inside the plain text).


EXAMPLES
--------
Example 1:   s = "3[a]2[bc]"       ->  "aaabcbc"
Example 2:   s = "3[a2[c]]"        ->  "accaccacc"
Example 3:   s = "2[abc]3[cd]ef"   ->  "abcabccdcdcdef"


CONSTRAINTS
-----------
    1 <= s.length <= 30
    s consists of lowercase letters, digits and '[' ']'.
    1 <= k <= 300
    The output length never exceeds 10^5.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Nested brackets are a sign of a STACK (or recursion, which uses the call
stack). Read left to right while building the current string:

    letter   -> append to the current string
    digit    -> build the repeat count (it can have several digits!)
    '['      -> SAVE (the string so far, the count) and start fresh inside
    ']'      -> the inside is finished: pop (outer string, count) and
                continue with outer + inside * count

The stack holds exactly the context you need to resume the outer level when
an inner one closes — the same shape as evaluating nested parentheses in a
calculator (Basic Calculator, LC 224).


WHAT TO THINK ABOUT
--------------------
1. "10[a]" — what goes wrong if you read one digit at a time as the count?

2. After '[', what must the "current string" become? After ']', what does it
   become?

3. Can you write it recursively instead: a function that decodes until the
   matching ']' and returns where it stopped?


PROGRESSIVE HINTS
------------------
Hint 1: count = count * 10 + int(ch) accumulates multi-digit numbers.

Hint 2: On '[': push (current, count); current = "", count = 0.
        On ']': prev, k = pop(); current = prev + current * k.

Hint 3: Build pieces in a list and join at the end if you worry about
        repeated string concatenation.


COMPLEXITY TARGET
------------------
    Time:  O(output length)
    Space: O(output length)
================================================================================
"""


class Solution:
    def decodeString(self, s: str) -> str:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 015_decode_string_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ("3[a]2[bc]", "aaabcbc"),
        ("3[a2[c]]", "accaccacc"),
        ("2[abc]3[cd]ef", "abcabccdcdcdef"),
        ("abc", "abc"),
        ("10[a]", "aaaaaaaaaa"),
        ("2[b3[a]]c", "baaabaaac"),
        ("3[z]2[2[y]pq4[2[jk]e1[f]]]ef",
         "zzzyypqjkjkefjkjkefjkjkefjkjkefyypqjkjkefjkjkefjkjkefjkjkefef"),
    ]
    all_ok = True
    for s, want in cases:
        got = Solution().decodeString(s)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r}  got={got!r}  want={want!r}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
