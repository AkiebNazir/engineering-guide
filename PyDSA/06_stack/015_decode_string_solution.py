"""
================================================================================
SOLUTION · LeetCode 394 · Decode String                                 [Medium]
https://leetcode.com/problems/decode-string/
================================================================================

THE CORE IDEA
--------------
A stack of saved contexts. Each '[' saves "what I had built outside, and how
many times the inside repeats"; each ']' restores it:

    for ch in s:
        digit:  count = count * 10 + int(ch)
        '[':    stack.append((current, count)); current, count = "", 0
        ']':    outer, k = stack.pop(); current = outer + current * k
        letter: current += ch

The stack depth equals the bracket nesting depth.


================================================================================
APPROACH 1 · Repeatedly expand the innermost bracket (priced)
================================================================================
Find a "k[letters]" with no brackets inside, replace it by its expansion, and
rescan until no brackets remain. Simple, but each pass copies the whole
string: O(passes * output length).


================================================================================
APPROACH 2 · Recursion (the call stack as the stack)
================================================================================
    def decode(i):                    # returns (decoded, index after it)
        out, count = [], 0
        while i < len(s) and s[i] != ']':
            if s[i].isdigit(): count = count * 10 + int(s[i]); i += 1
            elif s[i] == '[':
                inner, i = decode(i + 1)
                out.append(inner * count); count = 0
                i += 1                # skip ']'
            else: out.append(s[i]); i += 1
        return "".join(out), i

    Time: O(output)    Space: O(output + nesting depth)


================================================================================
APPROACH 3 · Explicit stack ✅ (the answer)
================================================================================
Identical logic to the recursion, with the saved contexts in a list instead
of frames. Current pieces are kept in a list and joined when a bracket closes,
so no string is rebuilt character by character.

    Time: O(output length)    Space: O(output length)


================================================================================
STEP BY STEP TRACE · s = "3[a2[c]]"
================================================================================
    ch   action                          stack                  current
    --   ------------------------------  ---------------------  -------
    3    count = 3                       []                     ""
    [    push ("", 3); reset             [("", 3)]              ""
    a    append                          [("", 3)]              "a"
    2    count = 2                       [("", 3)]              "a"
    [    push ("a", 2); reset            [("", 3), ("a", 2)]    ""
    c    append                          [("", 3), ("a", 2)]    "c"
    ]    pop ("a", 2): "a" + "c"*2       [("", 3)]              "acc"
    ]    pop ("", 3): "" + "acc"*3       []                     "accaccacc"


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time                  Space     Mutates input?
    ---------------------------  --------------------  --------  --------------
    Expand innermost repeatedly  O(passes * output)    O(output) No
    Recursion                    O(output)             O(output) No
    Explicit stack ✅            O(output)             O(output) No


================================================================================
EDGE CASES
================================================================================
    No brackets at all        Return s unchanged.
    Multi-digit counts        "10[a]", "100[ab]".
    Letters after a bracket   "2[a]bc" — the tail belongs to the outer level.
    Deep nesting              "2[2[2[a]]]" — the stack grows with depth.


================================================================================
COMMON MISTAKES
================================================================================
1. Reading the count one digit at a time. "10[a]" becomes "1" then "0[a]",
   so the count used is 0 and the answer is "". Demo.

2. Forgetting to reset `count` after '[' — the next level starts with the
   outer count still in it ("3[a2[c]]" multiplies 32 instead of 2). Demo.

3. Forgetting to reset `current` after '[' — the outer text gets repeated as
   part of the inner string. Demo.

4. Assuming counts are single digits because the examples are. The
   constraints allow k up to 300.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: The decoded string is too large to build (k up to 10^9)?
A: Don't build it. Compute lengths per bracket, then answer queries like
   "character at index i" by walking down with i % len (LC 880, Decoded
   String at Index).

Q: Encode a string as short as possible (LC 471)?
A: Interval DP over substrings, trying every split and every repeated
   pattern — a much harder problem.

Q: Validate the input as well?
A: Check brackets balance, digits only before '[', and the stack is empty at
   the end.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 20   Valid Parentheses (001)                — the stack of openers
    LC 224  Basic Calculator                       — push context at '(' and pop at ')'
    LC 880  Decoded String at Index                — lengths instead of strings
    LC 726  Number of Atoms                        — the same shape with counts after ')'
================================================================================
"""

import random
import re
import time


class Solution:
    def decodeString(self, s: str) -> str:
        stack = []                                   # (outer pieces, repeat count)
        current, count = [], 0
        for ch in s:
            if ch.isdigit():
                count = count * 10 + ord(ch) - 48
            elif ch == "[":
                stack.append((current, count))
                current, count = [], 0
            elif ch == "]":
                outer, k = stack.pop()
                outer.append("".join(current) * k)
                current = outer
            else:
                current.append(ch)
        return "".join(current)


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
INNER = re.compile(r"(\d+)\[([a-z]*)\]")


def expand_innermost(s: str) -> str:
    """Approach 1 and the oracle: rewrite the innermost k[...] until none remain."""
    while "[" in s:
        s = INNER.sub(lambda m: m.group(2) * int(m.group(1)), s)
    return s


def decode_recursive(s: str) -> str:
    def decode(i: int):
        out, count = [], 0
        while i < len(s) and s[i] != "]":
            ch = s[i]
            if ch.isdigit():
                count = count * 10 + int(ch)
                i += 1
            elif ch == "[":
                inner, i = decode(i + 1)
                out.append(inner * count)
                count = 0
                i += 1                               # skip the matching ']'
            else:
                out.append(ch)
                i += 1
        return "".join(out), i
    return decode(0)[0]


def single_digit_bug(s: str) -> str:
    """Mistake 1: count = int(ch) instead of accumulating."""
    stack, current, count = [], "", 0
    for ch in s:
        if ch.isdigit():
            count = int(ch)                          # BUG
        elif ch == "[":
            stack.append((current, count)); current, count = "", 0
        elif ch == "]":
            outer, k = stack.pop(); current = outer + current * k
        else:
            current += ch
    return current


def no_count_reset_bug(s: str) -> str:
    """Mistake 2: count carries into the inner level."""
    stack, current, count = [], "", 0
    for ch in s:
        if ch.isdigit():
            count = count * 10 + int(ch)
        elif ch == "[":
            stack.append((current, count)); current = ""          # BUG: count not reset
        elif ch == "]":
            outer, k = stack.pop(); current = outer + current * k; count = 0
        else:
            current += ch
    return current


def no_current_reset_bug(s: str) -> str:
    """Mistake 3: current keeps the outer text inside the bracket."""
    stack, current, count = [], "", 0
    for ch in s:
        if ch.isdigit():
            count = count * 10 + int(ch)
        elif ch == "[":
            stack.append((current, count)); count = 0              # BUG: current not reset
        elif ch == "]":
            outer, k = stack.pop(); current = outer + current * k
        else:
            current += ch
    return current


def random_encoded(rng: random.Random, depth: int = 0) -> str:
    parts = []
    for _ in range(rng.randint(1, 3)):
        if depth < 3 and rng.random() < 0.5:
            parts.append(f"{rng.randint(1, 12)}[{random_encoded(rng, depth + 1)}]")
        else:
            parts.append("".join(rng.choice("abcxyz") for _ in range(rng.randint(1, 3))))
    return "".join(parts)


# ==============================================================================
# TESTS — run:  python 015_decode_string_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: stack vs recursion vs innermost-first rewriting ---")
    cases = [("3[a]2[bc]", "aaabcbc"), ("3[a2[c]]", "accaccacc"), ("2[abc]3[cd]ef", "abcabccdcdcdef"),
             ("abc", "abc"), ("10[a]", "aaaaaaaaaa"), ("2[b3[a]]c", "baaabaaac"),
             ("3[z]2[2[y]pq4[2[jk]e1[f]]]ef",
              "zzzyypqjkjkefjkjkefjkjkefjkjkefyypqjkjkefjkjkefjkjkefjkjkefef")]
    for s, want in cases:
        results = (sol.decodeString(s), decode_recursive(s), expand_innermost(s))
        ok = all(r == want for r in results)
        all_ok &= ok
        shown = want if len(want) <= 20 else want[:17] + "..."
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r:<32} -> {shown!r}")

    print("\n--- randomized cross-check (2,000 random nested encodings) ---")
    rng = random.Random(394)
    bad = 0
    for _ in range(2000):
        s = random_encoded(rng)
        want = expand_innermost(s)
        if sol.decodeString(s) != want or decode_recursive(s) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  2,000 random encodings agree across all three methods")

    print("\n--- mistakes LIVE ---")
    w1 = single_digit_bug("10[a]")
    ok = w1 == "" and sol.decodeString("10[a]") == "a" * 10
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  one digit at a time: '10[a]' -> {w1!r}, want 'aaaaaaaaaa'")
    w2 = no_count_reset_bug("3[a2[c]]")
    ok = w2 != "accaccacc"
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  count not reset at '[': '3[a2[c]]' -> {len(w2)} chars "
          f"(inner count read as 32), want 'accaccacc'")
    w3 = no_current_reset_bug("ab2[c]")
    ok = w3 != "abcc"
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  current not reset at '[': 'ab2[c]' -> {w3!r}, want 'abcc'")

    print("\n--- output-sized work: a 10^5-character result ---")
    s = "100[" + "10[" + "100[a]" + "]" + "]"
    t0 = time.perf_counter(); out = sol.decodeString(s); dt = time.perf_counter() - t0
    ok = len(out) == 100_000
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {s!r} -> {len(out):,} characters in {dt * 1000:.2f} ms")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
