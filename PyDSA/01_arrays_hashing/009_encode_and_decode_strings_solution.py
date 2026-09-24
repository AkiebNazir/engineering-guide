"""
================================================================================
SOLUTION · LeetCode 271 · Encode and Decode Strings                    [Medium]
https://leetcode.com/problems/encode-and-decode-strings/
================================================================================

THE CORE IDEA
-------------
There is no safe delimiter. The constraint says strings may contain ANY of the
256 ASCII characters, so whatever byte you choose as a separator, the data can
contain it. Searching harder for a "rare" character makes the bug rarer, not
absent — which is strictly worse, because rare bugs ship.

So stop delimiting and start COUNTING:

    LENGTH-PREFIX THE PAYLOAD. Say how long it is, then say it.

    "neet"  ->  "4#neet"
                 ^ ^
                 | +-- terminates the LENGTH FIELD (not the payload)
                 +---- how many characters to read next

The decoder never searches inside a payload. It reads a number, then consumes
exactly that many characters blindly. The payload becomes OPAQUE — it can
contain "#", newlines, NUL bytes, an entire nested encoded message, anything.

Why is the "#" safe here when it was not safe as a separator? Because it lives
in a field whose alphabet YOU control. A length is digits only, so "#" cannot
occur inside one. You have not eliminated the delimiter problem; you have
moved it into a place where the alphabet is restricted and it is solvable.

    self-delimiting field   +   opaque counted payload   =   unambiguous

That pattern is not a LeetCode trick. It is how HTTP does `Content-Length`, how
Redis does RESP (`$4\r\nneet\r\n`), how netstrings work, and how nearly every
binary wire format frames a variable-length blob. Say that in the interview.


================================================================================
APPROACH 0 · Naive separator (state it, then break it yourself)
================================================================================
    return "#".join(strs)               # encode
    return s.split("#")                 # decode

    ["neet","code"]  ->  "neet#code"  ->  ["neet","code"]     ✓ looks fine

Then feed it the adversarial case:

    ["ne#et","code"] ->  "ne#et#code" ->  ["ne","et","code"]  ✗ 3 != 2

Do this DEMOLITION YOURSELF in the interview before they do. Proposing the
naive scheme and then attacking it is exactly the behaviour they are scoring.

"Just use a rarer character like \\x1f" is not a fix — the constraint permits
all 256 bytes, so \\x1f is in the input's alphabet too. There is no escape via
character choice.


================================================================================
APPROACH 1 · Length prefix ✅✅ (the answer)
================================================================================

    def encode(strs):
        return "".join(f"{len(s)}#{s}" for s in strs)

    def decode(s):
        out, i = [], 0
        while i < len(s):
            j = s.index("#", i)          # end of the length field
            length = int(s[i:j])
            out.append(s[j + 1: j + 1 + length])
            i = j + 1 + length           # jump PAST the payload — never scan it
        return out

    encode: O(n) time, O(n) space
    decode: O(n) time, O(n) space

STEP BY STEP encoding ["neet","code","love","you"]:

    "neet" -> len 4 -> "4#neet"
    "code" -> len 4 -> "4#code"
    "love" -> len 4 -> "4#love"
    "you"  -> len 3 -> "3#you"

    encoded = "4#neet4#code4#love3#you"

STEP BY STEP decoding it — track the pointer:

    "4#neet4#code4#love3#you"
     0123456789...

    i=0   find '#' from 0 -> j=1    len = int(s[0:1]) = 4
          payload = s[2:6] = "neet"           i -> 2+4 = 6
          ┌─┬─┬────────┐
          │4│#│ n e e t│
          └─┴─┴────────┘
           0 1  2 3 4 5

    i=6   find '#' from 6 -> j=7    len = int(s[6:7]) = 4
          payload = s[8:12] = "code"          i -> 8+4 = 12

    i=12  find '#' from 12 -> j=13  len = 4
          payload = s[14:18] = "love"         i -> 18

    i=18  find '#' from 18 -> j=19  len = 3
          payload = s[20:23] = "you"          i -> 23

    i=23 == len(s)  ->  stop.  ["neet","code","love","you"]     ✓

WHY THE ADVERSARIAL INPUT NOW WORKS — ["ne#et","code"]:

    encoded = "5#ne#et4#code"
                ^ the '#' at index 4 is INSIDE the payload

    i=0   j = index('#', 0) = 1        len = 5
          payload = s[2:7] = "ne#et"   <- taken BY COUNT, so the inner '#'
                                          is just a character
          i -> 7
    i=7   j = index('#', 7) = 8        len = 4
          payload = s[9:13] = "code"
          i -> 13 == len(s)            ->  ["ne#et","code"]     ✓

    The decoder never looked for a '#' inside a payload, so there was nothing
    to confuse it. Counting beats searching.

⚠️  `s.index("#", i)` MUST TAKE THE START ARGUMENT
    `s.index("#")` with no start always finds the FIRST '#' in the whole
    string, so after the first record you re-read record 0 forever. Infinite
    loop or garbage. The pointer is the state; every search must respect it.

⚠️  THE JUMP MUST BE `j + 1 + length`, NOT `i + 1 + length`
    i points at the first DIGIT; j points at the '#'. Since j = i + (number of
    digits), using i under-jumps by exactly the digit count — so this is wrong
    even for single-digit lengths, and it derails on the very next record.
    Loud, immediate, easy to catch.

⚠️  THE SUBTLE ONE: `int(s[i])` INSTEAD OF `int(s[i:j])`
    Parsing a single character as the length is correct for every string
    shorter than 10 and silently corrupt for everything else — "12#aaaa..."
    reads a length of 1, takes "2", and every subsequent record is garbage.

    This is the dangerous class of bug: it passes every small hand-written
    test and fails on real data. The constraint allows lengths up to 199, so
    3-digit lengths are reachable. ALWAYS put a 10+ character string in your
    own test cases. The demo at the bottom shows both bugs side by side.


================================================================================
APPROACH 2 · Escaping (the other correct family)
================================================================================
Keep a separator, but guarantee it can never appear "for real" inside a
payload by rewriting it in the data first:

    encode:  s.replace("\\", "\\\\").replace("#", "\\#")   then join on "#"
    decode:  split on UNESCAPED "#", then reverse the replacements

    ["ne#et","code"]  ->  "ne\\#et#code"

Correct, and it is how CSV quoting and shell escaping work. But it has three
sharp edges, and the implementation below hit all three:

  - You must escape the ESCAPE CHARACTER first, or "\\#" in the input becomes
    ambiguous. Getting the order wrong is the classic escaping bug.
  - Decode needs a character-by-character scan with a "was the last char a
    backslash?" state machine — `split("#")` is not enough.
  - ⚠️  You must TERMINATE each record, not JOIN between them. `"#".join(...)`
    inherits the naive scheme's fatal flaw: [] and [""] both encode to "", so
    decode cannot tell them apart. Emitting `escaped + "#"` per record gives
    "" and "#" respectively, which is unambiguous. This is easy to miss —
    the round-trip tests in this file caught it.

  - Encoded size can DOUBLE in the worst case (all separators).

Length-prefix is strictly simpler and has no pathological expansion. Name
escaping to show you know the alternative, then implement the prefix.


================================================================================
APPROACH 3 · Fixed-width length header
================================================================================
Instead of a variable-length number plus '#', use a fixed field:

    header = str(len(s)).zfill(4)       # "0004neet", always 4 digits

No delimiter at all — the decoder reads exactly 4 characters, converts, then
reads that many more. Even simpler to decode, and it is what most binary
protocols do (a 4-byte big-endian length).

The cost: you must cap the string length at 9999, which the constraints here
happen to allow (< 200). Bring this up when the interviewer asks about a
binary/network setting — "in a real protocol I'd use a fixed 4-byte length in
network byte order, not ASCII digits."


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = total characters across all strings, k = number of strings

    Approach            encode      decode      Blowup        Correct?
    ------------------  ----------  ----------  ------------  --------------
    Naive separator     O(n)        O(n)        +k            NO — ambiguous
    Length prefix ✅✅  O(n)        O(n)        +k·(d+1)      yes
    Escaping            O(n)        O(n)        up to 2n      yes
    Fixed-width header  O(n)        O(n)        +4k           yes, len < 10^4

    d = digits in a length. Neither encode nor decode mutates its input;
    strings are immutable in Python, so this is free.

    ⚠️  Build the encoding with "".join(parts), not `out += part` in a loop.
        Repeated += on an immutable str is O(n²) — CPython has an in-place
        optimisation that hides it sometimes, which makes it worse, not better,
        because it hides the bug until it matters. The benchmark below measures
        the real gap.


================================================================================
EDGE CASES
================================================================================
    []           -> ""       -> []
                 Zero records. `while i < len(s)` never runs. No special case
                 needed — but verify it, because a do-while shape would emit a
                 spurious empty string.

    [""]         -> "0#"     -> [""]
                 ONE empty string, which is NOT the same list as []. This is
                 the case that kills `"#".join(...)` + `split("#")`: that
                 scheme encodes both [] and [""] to "", so decode cannot tell
                 them apart. Length-prefix distinguishes them: "" vs "0#".

    ["","",""]   -> "0#0#0#" -> ["","",""]
                 Zero-length payloads back to back. Confirms the pointer
                 advances by j+1+0 and does not stall — a stall here is an
                 infinite loop, not a wrong answer.

    ["#","##"]   -> "1##2###" -> ["#","##"]
                 The separator as data. Read "1##": length 1, payload "#".
                 This is the whole point of the problem.

    ["4#neet"]   -> "6#4#neet" -> ["4#neet"]
                 A payload that is itself a valid-looking encoded record. The
                 decoder must not "helpfully" re-parse it. Counting means it
                 cannot.

    ["a"*199]    -> "199#aaa…" -> ["a"*199]
                 3-DIGIT LENGTH. Catches the `i` vs `j` jump bug, which is
                 invisible for lengths 0–9.

    ["\\n","\\x00"] -> control characters, including NUL, are legal ASCII here
                 and must survive. They do, because payloads are opaque.


================================================================================
COMMON MISTAKES
================================================================================
1. `"#".join(strs)` / `s.split("#")`. Ambiguous the moment data contains '#',
   and it cannot distinguish [] from [""].

2. Choosing an "unlikely" delimiter and calling it done. The constraint says
   all 256 ASCII characters are possible. Unlikely is not impossible.

3. `s.index("#")` without the start offset — re-finds the first '#' forever.

4. Jumping `i + 1 + length` instead of `j + 1 + length` — under-jumps by the
   digit count, wrong even for 1-digit lengths.

4b. `int(s[i])` instead of `int(s[i:j])` — reads only the FIRST digit. Passes
   every test where strings are under 10 characters, corrupts everything
   after the first long one. The nastiest bug in this problem.

5. Using `s.split("#")` inside decode to grab the length. Same ambiguity, one
   level down.

6. Treating the '#' as a separator BETWEEN strings rather than a TERMINATOR of
   the length field. It changes where you expect it and produces off-by-ones.

7. Building the output with `res += ...` instead of `"".join(...)`.

8. Reaching for `json.dumps` / `pickle`. Explicitly banned, and the point of
   the exercise is that you can design the framing yourself.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Make it work for arbitrary Unicode, not just ASCII.
A: `len(s)` in Python counts CODE POINTS, and slicing is by code point too, so
   the algorithm is already correct for `str`. The danger is if you encode to
   BYTES: then the length must be the BYTE length (`len(s.encode())`) and the
   payload must be sliced as bytes. Mixing the two truncates multi-byte
   characters mid-sequence. State which unit your length is in — that is the
   real answer.

Q: The receiver gets the stream in chunks and may not have the whole message.
A: Length-prefix is designed for exactly this. Buffer; read the header; if
   fewer than L bytes are available, wait for more. This is why real protocols
   use it — it is INCREMENTALLY DECODABLE, which a separator scheme is not
   (you cannot know a separator is the last one until the stream ends).

Q: What if the length field itself could be corrupted?
A: Add a checksum, or use a self-describing format with framing markers and
   resynchronisation (like HDLC flag bytes + bit stuffing). Now you are in
   error-correcting territory rather than framing.

Q: Minimise the encoded size.
A: Use a varint (7 bits payload + 1 continuation bit per byte, as in Protocol
   Buffers) instead of ASCII digits. One byte covers lengths up to 127 instead
   of three characters for "199".


================================================================================
RELATED PROBLEMS — the serialisation family
================================================================================
    LC 297  Serialize and Deserialize Binary Tree  — same framing question with
                                                      a null marker for shape
    LC 449  Serialize and Deserialize BST          — BST order lets you skip
                                                      the null markers
    LC 428  Serialize N-ary Tree                   — length-prefix the CHILD
                                                      COUNT: exactly this idea
    LC 535  Encode and Decode TinyURL              — the other kind of "encode"
                                                      (a bijection, not framing)
    LC 443  String Compression                     — run-length, i.e. counts as
                                                      payload rather than framing
================================================================================
"""

import time
from typing import List


class Codec:
    def encode(self, strs: List[str]) -> str:
        """Length-prefix each string: "<len>#<payload>". O(n) time and space."""
        return "".join(f"{len(s)}#{s}" for s in strs)

    def decode(self, s: str) -> List[str]:
        """Read a length, then consume exactly that many chars. O(n)."""
        out: List[str] = []
        i = 0
        while i < len(s):
            j = s.index("#", i)                  # start arg is mandatory
            length = int(s[i:j])
            out.append(s[j + 1: j + 1 + length])  # taken BY COUNT, never scanned
            i = j + 1 + length                    # jump past the payload
        return out


class CodecFixedWidth:
    """Approach 3 — a 4-digit zero-padded header, no delimiter at all."""

    WIDTH = 4

    def encode(self, strs: List[str]) -> str:
        return "".join(f"{len(s):0{self.WIDTH}d}{s}" for s in strs)

    def decode(self, s: str) -> List[str]:
        out: List[str] = []
        i = 0
        while i < len(s):
            length = int(s[i: i + self.WIDTH])
            i += self.WIDTH
            out.append(s[i: i + length])
            i += length
        return out


class CodecEscaping:
    """Approach 2 — escape the separator inside the data, then join on it."""

    def encode(self, strs: List[str]) -> str:
        # Escape the ESCAPE CHARACTER first, or "\#" in the input is ambiguous.
        # TERMINATE each record rather than JOIN between them — joining cannot
        # distinguish [] from [""] (both give ""), exactly like the naive scheme.
        return "".join(
            s.replace("\\", "\\\\").replace("#", "\\#") + "#" for s in strs
        )

    def decode(self, s: str) -> List[str]:
        out, cur, i = [], [], 0
        while i < len(s):
            c = s[i]
            if c == "\\":                # escaped: take the next char literally
                cur.append(s[i + 1])
                i += 2
            elif c == "#":               # a real, unescaped TERMINATOR
                out.append("".join(cur))
                cur = []
                i += 1
            else:
                cur.append(c)
                i += 1
        return out                       # no trailing flush: every record ended


class CodecNaive:
    """✗ BROKEN ON PURPOSE — the separator scheme, kept to demonstrate failure."""

    def encode(self, strs: List[str]) -> str:
        return "#".join(strs)

    def decode(self, s: str) -> List[str]:
        return s.split("#")


# ==============================================================================
# TESTS — run:  python 009_encode_and_decode_strings_solution.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ["neet", "code", "love", "you"],
        ["we", "say", ":", "yes"],
        [],
        [""],
        ["", "", ""],
        ["#", "##", "###"],
        ["4#neet"],
        ["a" * 199],                                  # 3-digit length
        ["hello world", " leading", "trailing "],
        ["\n", "\t", "\\", "\x00"],
        ["ne#et", "code"],
        ["\\#", "\\\\", "a\\#b"],                     # escaping's hard cases
    ]
    impls = [
        ("length prefix", Codec()),
        ("fixed width  ", CodecFixedWidth()),
        ("escaping     ", CodecEscaping()),
    ]
    all_ok = True
    for name, codec in impls:
        ok = all(codec.decode(codec.encode(list(c))) == c for c in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} round trips)")

    codec = Codec()

    # ----------------------------------------------------------------------
    # ⚠️  The naive separator, broken on real input.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  why there is no safe delimiter ---")
    naive = CodecNaive()
    for strs in (["ne#et", "code"], ["#", "##"], [""], []):
        enc = naive.encode(list(strs))
        dec = naive.decode(enc)
        mark = "ok " if dec == strs else "✗ BROKEN"
        print(f"  {mark}  {str(strs):<22} -> {enc!r:<14} -> {dec!r}")
    print("  Note [] and [''] BOTH encode to '' — the scheme cannot tell a list")
    print("  of zero strings from a list of one empty string. Unfixable by")
    print("  choosing a different character.")

    # ----------------------------------------------------------------------
    # The same inputs, length-prefixed.
    # ----------------------------------------------------------------------
    print("\n--- the same inputs, length-prefixed ---")
    for strs in (["ne#et", "code"], ["#", "##"], [""], []):
        enc = codec.encode(list(strs))
        dec = codec.decode(enc)
        mark = "ok " if dec == strs else "✗"
        print(f"  {mark}  {str(strs):<22} -> {enc!r:<14} -> {dec!r}")

    # ----------------------------------------------------------------------
    # Walk the decode pointer.
    # ----------------------------------------------------------------------
    print("\n--- decode pointer walk for ['neet','code','love','you'] ---")
    s = codec.encode(["neet", "code", "love", "you"])
    print(f"  encoded = {s!r}   (len {len(s)})")
    print(f"  {'i':>3}  {'j':>3}  {'len':>3}  payload      next i")
    i = 0
    while i < len(s):
        j = s.index("#", i)
        length = int(s[i:j])
        payload = s[j + 1: j + 1 + length]
        nxt = j + 1 + length
        print(f"  {i:>3}  {j:>3}  {length:>3}  {payload!r:<12} {nxt}")
        i = nxt

    # ----------------------------------------------------------------------
    # ⚠️  index() without the start offset never advances.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  s.index('#') without a start offset ---")
    s = codec.encode(["neet", "code"])
    print(f"  encoded = {s!r}")
    print(f"  s.index('#')      = {s.index('#')}   <- always 1, forever")
    print(f"  s.index('#', 6)   = {s.index('#', 6)}   <- correct: record 2")
    print("  Without the offset the loop re-reads record 0 and never terminates.")

    # ----------------------------------------------------------------------
    # ⚠️  i vs j in the jump — invisible until a length has 2+ digits.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  two decode bugs: one always fails, one only on long input ---")

    def decode_bug_jump(s):
        """i + 1 + length — under-jumps by the digit count."""
        out, i = [], 0
        while i < len(s) and len(out) < 6:
            j = s.index("#", i)
            length = int(s[i:j])
            out.append(s[j + 1: j + 1 + length])
            i = i + 1 + length
        return out

    def decode_bug_onedigit(s):
        """int(s[i]) — reads only the FIRST digit of the length."""
        out, i = [], 0
        while i < len(s) and len(out) < 6:
            j = s.index("#", i)
            length = int(s[i])              # <- the bug
            out.append(s[j + 1: j + 1 + length])
            i = j + 1 + length
        return out

    print(f"  {'input':<26} {'bug: i+1+len':<26} {'bug: int(s[i])'}")
    for strs in (["abcd", "ef"], ["a" * 12, "ef"]):
        enc = codec.encode(list(strs))
        res = []
        for fn in (decode_bug_jump, decode_bug_onedigit):
            try:
                r = repr(fn(enc))
            except (ValueError, IndexError) as e:
                r = f"<{type(e).__name__}>"
            res.append(r)
        print(f"  {str(strs):<26} {res[0]:<26} {res[1]}")
    print("  i+1+len breaks on BOTH rows — j = i + digits, so it always")
    print("  under-jumps. Any test at all catches it.")
    print("  int(s[i]) is CORRECT on row 1 and breaks on row 2. It passes every")
    print("  short test you write by hand and only fails once a string reaches")
    print("  10 characters. THAT is the one to fear — not because it is quiet")
    print("  (here it throws) but because your test suite never reaches it.")

    # ----------------------------------------------------------------------
    # A payload that looks like an encoded record.
    # ----------------------------------------------------------------------
    print("\n--- payload that impersonates the protocol ---")
    tricky = ["4#neet", "0#", "99#x"]
    enc = codec.encode(list(tricky))
    print(f"  input   {tricky}")
    print(f"  encoded {enc!r}")
    print(f"  decoded {codec.decode(enc)}")
    print("  Counted reads cannot be fooled by content that looks like framing.")

    # ----------------------------------------------------------------------
    # join() vs += — the O(n) / O(n²) difference.
    # ----------------------------------------------------------------------
    print("\n--- building the output: join O(n) vs concatenation O(n^2) ---")
    print("  NOTE: plain `acc += p` is NOT a fair demo — CPython has an")
    print("  in-place optimisation that makes it near-linear when acc's")
    print("  refcount is 1. Holding a second reference defeats it and exposes")
    print("  the real copy-every-time cost.")
    prev_join = prev_cat = None
    for n in (4_000, 8_000, 16_000):
        parts = [f"{i}#{'x' * 50}" for i in range(n)]

        t0 = time.perf_counter()
        "".join(parts)
        t_join = time.perf_counter() - t0

        t0 = time.perf_counter()
        acc = ""
        for part in parts:
            keep = acc                  # 2nd reference blocks the optimisation
            acc = acc + part            # so this must allocate and copy
            del keep
        t_cat = time.perf_counter() - t0

        jg = f"{t_join / prev_join:4.1f}x" if prev_join else "  -  "
        cg = f"{t_cat / prev_cat:4.1f}x" if prev_cat else "  -  "
        prev_join, prev_cat = t_join, t_cat
        print(f"  n={n:<7} join {t_join*1000:7.2f}ms ({jg})   "
              f"concat {t_cat*1000:8.2f}ms ({cg})   "
              f"ratio {t_cat / max(t_join, 1e-9):6.0f}x")
    print("  Doubling n doubles join (~2.0x) but roughly QUADRUPLES concat")
    print("  (~4.0x) — that is O(n) against O(n^2), measured.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
