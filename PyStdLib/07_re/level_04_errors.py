"""
LEVEL 04 (core) - Real re exceptions: re.error and the None-match trap
=========================================================================
You will learn
  * a malformed pattern raises re.error at compile time, not a generic ValueError
  * re.search/match/fullmatch return None on no match -- calling .group() on
    None raises AttributeError, which is the #1 real-world re bug
  * how to guard against both for real

Run: python level_04_errors.py
"""
import re

if __name__ == "__main__":
    # ---- a broken pattern raises re.error (a subclass of ValueError) ------
    try:
        re.compile(r"(unclosed group")
        raise AssertionError("expected re.error for an unbalanced parenthesis")
    except re.error as exc:
        assert "missing" in str(exc).lower() or "unbalanced" in str(exc).lower() or "parenthes" in str(exc).lower()
        assert isinstance(exc, re.error)   # re.error (aka re.PatternError) is the dedicated exception type

    # bad repetition target is also a compile-time re.error
    try:
        re.compile(r"*abc")
        raise AssertionError("expected re.error for a dangling '*' with nothing to repeat")
    except re.error:
        pass

    # ---- the real #1 bug: forgetting a match can fail -----------------------
    match = re.search(r"\d+", "no digits at all")
    assert match is None
    try:
        match.group()   # calling a method on None
        raise AssertionError("expected AttributeError from calling .group() on None")
    except AttributeError as exc:
        assert "'NoneType' object has no attribute 'group'" in str(exc)

    # the fix: always check the match (or use the walrus operator) before using it
    def safe_extract(text: str):
        if (m := re.search(r"\d+", text)) is not None:
            return m.group()
        return None

    assert safe_extract("id 42") == "42"
    assert safe_extract("no id here") is None   # no crash

    print("OK")
