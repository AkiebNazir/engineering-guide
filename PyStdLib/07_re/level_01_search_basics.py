"""
LEVEL 01 (basic) - Finding a pattern in text with re.search
=============================================================
You will learn
  * the problem re solves: finding text that matches a *shape*, not a literal value
  * re.search() scans the whole string and returns a Match object (or None)
  * pulling the matched text out with Match.group() and its span with .span()

Run: python level_01_search_basics.py
"""
import re


def find_first_number(text: str):
    """Return the first run of digits in text, or None if there isn't one."""
    match = re.search(r"\d+", text)
    return match.group() if match else None


if __name__ == "__main__":
    text = "Order #4821 shipped on day 12 of the month"

    match = re.search(r"\d+", text)
    assert match is not None                 # a plain str.find can't say "any digits"
    assert match.group() == "4821"            # the first run of digits
    assert match.span() == (7, 11)            # (start, end) index into `text`
    assert text[match.start():match.end()] == "4821"

    assert find_first_number("no digits here") is None   # no match -> None, not an exception

    # search() looks ANYWHERE in the string, unlike a fixed-position check.
    assert re.search(r"\d+", "abc123") is not None
    assert re.search(r"\d+", "abc123").group() == "123"

    print("OK")
