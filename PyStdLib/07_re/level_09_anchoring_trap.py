"""
LEVEL 09 (advanced) - Production trap: an unanchored pattern "validates" garbage
===================================================================================
You will learn
  * re.match / re.search only need to find a match SOMEWHERE (match: at the start);
    they do NOT require the whole string to conform
  * a "validator" built on match()/search() silently accepts trailing junk
  * the fix: anchor with ^...$ (with MULTILINE off) or, simpler, use fullmatch()

Run: python level_09_anchoring_trap.py
"""
import re

# Looks like a reasonable "is this a valid 3-digit product code?" check.
BROKEN_CODE_PATTERN = re.compile(r"\d{3}")

if __name__ == "__main__":
    # This LOOKS right for real inputs...
    assert BROKEN_CODE_PATTERN.match("123") is not None

    # ...but it silently "validates" garbage too, because match() only requires
    # the pattern to match starting at position 0 -- it never has to reach the end.
    bogus = "123-this-is-not-a-product-code-at-all"
    accepted = BROKEN_CODE_PATTERN.match(bogus) is not None
    assert accepted is True   # BUG: a validator that says this is a fine product code

    # Also true of an unanchored search() for a "starts and ends with" check.
    assert BROKEN_CODE_PATTERN.search("999999") is not None   # matches the first 3 digits of 6

    # ---- the fix: fullmatch() requires the ENTIRE string to match -----------
    FIXED_CODE_PATTERN = re.compile(r"\d{3}")
    assert FIXED_CODE_PATTERN.fullmatch("123") is not None
    assert FIXED_CODE_PATTERN.fullmatch(bogus) is None          # now correctly rejected
    assert FIXED_CODE_PATTERN.fullmatch("999999") is None        # 6 digits != exactly 3

    # equivalent fix using explicit anchors instead of fullmatch()
    ANCHORED_PATTERN = re.compile(r"^\d{3}$")
    assert ANCHORED_PATTERN.match(bogus) is None
    assert ANCHORED_PATTERN.match("123") is not None

    # NOTE: with re.MULTILINE, '$' matches before ANY '\n', so anchors alone can
    # still leak on multi-line input -- fullmatch() has no such caveat, which is
    # why it's the safer default for "is this whole string valid?" checks.
    multiline_bogus = "123\nmore junk after a newline"
    assert ANCHORED_PATTERN.match(multiline_bogus) is None        # correctly rejected: no MULTILINE, '$' needs the true end
    leaky_pattern = re.compile(r"^\d{3}$", re.MULTILINE)
    assert leaky_pattern.match(multiline_bogus) is not None       # leaks: MULTILINE lets '$' match at the \n
    assert FIXED_CODE_PATTERN.fullmatch(multiline_bogus) is None  # fullmatch is unaffected by MULTILINE

    print("OK")
