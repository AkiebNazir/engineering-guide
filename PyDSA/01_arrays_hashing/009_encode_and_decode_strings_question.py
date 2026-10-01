"""
================================================================================
LeetCode 271 · Encode and Decode Strings                               [Medium]
https://leetcode.com/problems/encode-and-decode-strings/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Design an algorithm to encode a LIST OF STRINGS into a SINGLE STRING. The
encoded string is then sent over the network and decoded back to the original
list of strings.

Implement:

    encode(strs: List[str]) -> str
    decode(s: str)          -> List[str]

You are not allowed to solve the problem using any serialize/deserialize
library (no pickle, no json).


EXAMPLES
--------
Example 1:
    Input:  ["neet","code","love","you"]
    Output: ["neet","code","love","you"]
            (encode then decode must round-trip exactly)

Example 2:
    Input:  ["we","say",":","yes"]
    Output: ["we","say",":","yes"]


CONSTRAINTS
-----------
    0 <= strs.length < 100
    0 <= strs[i].length < 200
    strs[i] contains ANY possible characters out of 256 valid ASCII characters.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is not an algorithms problem — it is a PROTOCOL DESIGN problem. There is
no clever trick and no complexity to optimise. There is exactly one question:

    HOW DOES THE DECODER KNOW WHERE ONE STRING ENDS AND THE NEXT BEGINS?

The obvious idea is a separator:

    ["neet","code"]  ->  "neet#code"  ->  split on "#"  ->  ["neet","code"]  ✓

Now read the constraint again, because it is the entire problem:

    strs[i] contains ANY possible characters out of 256 valid ASCII

So the input may legitimately contain your separator:

    ["ne#et","code"] ->  "ne#et#code"  -> split("#") -> ["ne","et","code"]  ✗
                                                          3 strings, not 2

Every separator you pick, the adversary can put inside the data. Picking a
"weird" character does not fix it — it only makes the bug rarer, which is
worse, because now it ships. There is no safe delimiter when the alphabet is
unrestricted.

That is the realisation the problem exists to produce. The fix is to stop
searching for a magic character and change the SHAPE of the encoding.


WHAT TO THINK ABOUT
-------------------
1. If you cannot mark where a string ENDS, can you instead say up front how
   long it is? What would the decoder do with that number?

2. If you write the length as text ("12"), how does the decoder know where the
   NUMBER ends and the payload begins? You have recreated the delimiter
   problem one level down — but this time you control the alphabet. Why does
   that make it solvable?

3. Two families of correct answers exist:
       - length-prefix ("4#neet")   — the standard one
       - escaping (rewrite the separator inside the data so it cannot be
         confused with a real one)
   Know both. The first is simpler and faster.

4. Empty cases: does your scheme survive `[]`? What about `[""]`? Are those
   two distinguishable in your encoding? They must be — one is a list of zero
   strings, the other a list of one empty string.


PROGRESSIVE HINTS
-----------------
Hint 1: Prefix each string with its length: `f"{len(s)}#{s}"`.
        ["neet","code"] -> "4#neet4#code"

Hint 2: The "#" here is NOT a separator between strings — it only terminates
        the LENGTH FIELD. Lengths are digits, so "#" can never appear inside a
        length, and the decoder can always find it. What comes after it is read
        by COUNT, never by searching, so the payload may contain anything —
        including "#".

Hint 3: To decode: keep a pointer i at 0. Find the next "#" from i, parse the
        digits between as the length L, take the next L characters as the
        string, then jump i past them. Repeat until i reaches the end.


COMPLEXITY TARGET
-----------------
    n = total number of characters across all strings

    encode:  O(n) time, O(n) space
    decode:  O(n) time, O(n) space
================================================================================
"""

from typing import List


class Codec:
    def encode(self, strs: List[str]) -> str:
        """Encodes a list of strings to a single string."""
        # YOUR CODE HERE
        pass

    def decode(self, s: str) -> List[str]:
        """Decodes a single string back to a list of strings."""
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 009_encode_and_decode_strings_question.py
# ==============================================================================
def run_tests() -> None:
    codec = Codec()
    cases = [
        ["neet", "code", "love", "you"],
        ["we", "say", ":", "yes"],
        [],                              # empty list
        [""],                            # ONE empty string — not the same as []
        ["", "", ""],                    # three empty strings
        ["#", "##", "###"],              # the separator, inside the data
        ["4#neet"],                      # looks like an encoded payload
        ["a" * 199],                     # max length
        ["hello world", " leading", "trailing "],
        ["\n", "\t", "\\", "\x00"],      # control characters are legal ASCII
    ]
    passed = 0
    for strs in cases:
        try:
            got = codec.decode(codec.encode(list(strs)))
        except Exception as e:                       # noqa: BLE001
            got = f"<raised {type(e).__name__}: {e}>"
        ok = got == strs
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {strs!r}\n      -> {got!r}")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
