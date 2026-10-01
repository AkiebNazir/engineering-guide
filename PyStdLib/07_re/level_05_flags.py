"""
LEVEL 05 (advanced) - Flags: IGNORECASE, MULTILINE, DOTALL, VERBOSE
======================================================================
You will learn
  * re.IGNORECASE for case-insensitive matching
  * re.MULTILINE makes ^ and $ match at every line boundary, not just string edges
  * re.DOTALL makes '.' match newlines too (by default it doesn't)
  * re.VERBOSE lets you write a pattern spread over lines with comments

Run: python level_05_flags.py
"""
import re

if __name__ == "__main__":
    # ---- IGNORECASE ---------------------------------------------------------
    assert re.search(r"hello", "HELLO world") is None                 # case-sensitive by default
    assert re.search(r"hello", "HELLO world", re.IGNORECASE) is not None

    # ---- MULTILINE: ^ and $ normally only match string start/end -----------
    text = "first line\nsecond line\nthird line"
    assert re.findall(r"^\w+", text) == ["first"]                       # only the very start, by default
    assert re.findall(r"^\w+", text, re.MULTILINE) == ["first", "second", "third"]

    # $ behaves the same way: without MULTILINE it's just the string's end
    assert re.findall(r"\w+$", text) == ["line"]
    assert re.findall(r"\w+$", text, re.MULTILINE) == ["line", "line", "line"]

    # ---- DOTALL: '.' normally does NOT match a newline ----------------------
    block = "start\nmiddle\nend"
    assert re.search(r"start.middle", block) is None                    # '.' can't cross the \n by default
    assert re.search(r"start.middle", block, re.DOTALL) is not None      # now it can

    # ---- VERBOSE: whitespace and comments in the pattern are ignored --------
    # equivalent to r"(\d{3})-(\d{3})-(\d{4})" but self-documenting
    phone_pattern = re.compile(r"""
        (\d{3})   # area code
        -
        (\d{3})   # exchange
        -
        (\d{4})   # subscriber number
    """, re.VERBOSE)
    m = phone_pattern.search("call 415-555-0132 now")
    assert m is not None
    assert m.groups() == ("415", "555", "0132")

    # a literal space in VERBOSE mode must be escaped or in a class, since bare
    # whitespace is ignored -- this is the one gotcha VERBOSE introduces
    loose = re.compile(r"a b c", re.VERBOSE)           # spaces ignored -> means "abc"
    assert loose.fullmatch("abc") is not None
    assert loose.fullmatch("a b c") is None            # literal spaces are NOT matched here

    # flags combine with the | operator
    combined = re.compile(r"^end", re.IGNORECASE | re.MULTILINE)
    assert combined.search("start\nEND") is not None

    print("OK")
