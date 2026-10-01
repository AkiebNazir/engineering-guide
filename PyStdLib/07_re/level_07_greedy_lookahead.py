"""
LEVEL 07 (advanced) - Greedy vs non-greedy quantifiers, and lookahead
========================================================================
You will learn
  * '*' and '+' are GREEDY by default: they grab as much as possible, then backtrack
  * '*?' and '+?' are non-greedy: they grab as little as possible
  * (?=...) is a positive lookahead: assert what follows WITHOUT consuming it
  * (?!...) is a negative lookahead: assert what does NOT follow

Run: python level_07_greedy_lookahead.py
"""
import re

HTML = "<b>bold</b> and <i>italic</i>"

if __name__ == "__main__":
    # ---- greedy vs non-greedy on the exact same string and pattern shape ----
    greedy = re.search(r"<.*>", HTML)
    assert greedy is not None
    assert greedy.group() == "<b>bold</b> and <i>italic</i>"   # grabbed from the FIRST '<' to the LAST '>'

    non_greedy = re.search(r"<.*?>", HTML)
    assert non_greedy is not None
    assert non_greedy.group() == "<b>"   # stops at the FIRST '>' it can

    # same story with '+' vs '+?'
    assert re.search(r"a+", "aaa").group() == "aaa"          # greedy: all three a's
    assert re.search(r"a+?", "aaa").group() == "a"           # non-greedy: just one is enough to match

    # ---- positive lookahead (?=...): assert without consuming ---------------
    # find a word only if it's immediately followed by ": " (but don't capture the ": ")
    text = "name: Alice, age: 30, city: Paris"
    keys = re.findall(r"\b\w+(?=:)", text)
    assert keys == ["name", "age", "city"]
    # the colon itself is NOT part of any match -- lookahead doesn't consume
    assert all(":" not in k for k in keys)

    # ---- negative lookahead (?!...): assert what must NOT follow ------------
    # match "foo" only when it's NOT followed by "bar"
    samples = ["foobar", "foobaz", "foo"]
    matches = [bool(re.search(r"foo(?!bar)", s)) for s in samples]
    assert matches == [False, True, True]   # only "foobar" is excluded

    print("OK")
