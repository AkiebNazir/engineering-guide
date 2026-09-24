"""
LEVEL 02 (core) - match vs search vs fullmatch, and named groups
===================================================================
You will learn
  * re.match anchors at the START only; re.search scans anywhere;
    re.fullmatch requires the ENTIRE string to match
  * re.compile() to build a reusable Pattern object
  * groups() for positional captures, groupdict() for named (?P<name>...) captures

Run: python level_02_match_search_fullmatch_groups.py
"""
import re

TEXT = "  hello world"
PATTERN = re.compile(r"hello")

if __name__ == "__main__":
    # match() only cares about the START of the string.
    assert PATTERN.match(TEXT) is None            # TEXT starts with spaces, not "hello"
    assert PATTERN.match(TEXT.strip()) is not None  # "hello world" starts with "hello"

    # search() scans the whole string for a match anywhere.
    assert PATTERN.search(TEXT) is not None       # finds "hello" after the leading spaces

    # fullmatch() requires the WHOLE string to be consumed by the pattern.
    assert PATTERN.fullmatch(TEXT.strip()) is None      # "hello world" != "hello" entirely
    assert PATTERN.fullmatch("hello") is not None       # exact whole-string match

    # ---- groups(): positional captures -----------------------------------
    date_pattern = re.compile(r"(\d{4})-(\d{2})-(\d{2})")
    m = date_pattern.search("created: 2024-03-15")
    assert m is not None
    assert m.groups() == ("2024", "03", "15")
    assert m.group(1) == "2024"   # group(0) is the whole match, group(1) the first capture

    # ---- groupdict(): named captures via (?P<name>...) --------------------
    named_pattern = re.compile(r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})")
    m2 = named_pattern.search("created: 2024-03-15")
    assert m2 is not None
    assert m2.groupdict() == {"year": "2024", "month": "03", "day": "15"}
    assert m2.group("year") == "2024"   # named groups are also accessible by name

    print("OK")
