"""
LEVEL 04 (advanced) - json.JSONDecodeError: a real parse failure, inspected
=============================================================================
You will learn
  * malformed JSON raises json.JSONDecodeError (a subclass of ValueError)
  * .msg, .lineno, .colno, .pos pinpoint exactly where parsing failed
  * this is real enough to build a "show me the bad line" error reporter with

Run: python level_04_decode_error.py
"""
import json


def main() -> None:
    # Trailing comma -- one of the most common hand-written-JSON mistakes.
    bad_json = '{\n  "a": 1,\n  "b": 2,\n}\n'

    try:
        json.loads(bad_json)
        raise AssertionError("expected JSONDecodeError")
    except json.JSONDecodeError as e:
        assert isinstance(e, ValueError)     # JSONDecodeError IS a ValueError
        assert e.lineno == 3                 # the line holding the trailing comma (1-indexed)
        assert e.colno == 9                  # the comma's column on that line
        assert e.pos == bad_json.index(",\n}")   # absolute offset of the offending comma
        assert "trailing comma" in e.msg.lower()

    # A completely empty string is also invalid JSON (not even `null`).
    try:
        json.loads("")
        raise AssertionError("expected JSONDecodeError")
    except json.JSONDecodeError as e:
        assert e.pos == 0
        assert e.msg == "Expecting value"

    # Single quotes are not valid JSON string delimiters (a very common mistake
    # for people coming from Python literals).
    try:
        json.loads("{'a': 1}")
        raise AssertionError("expected JSONDecodeError")
    except json.JSONDecodeError as e:
        assert e.pos == 1   # fails right where the single quote appears
        assert "double quotes" in e.msg

    # Using the error to build a human-friendly report -- a realistic use of
    # the structured fields instead of just printing the exception.
    def describe_error(text: str, err: json.JSONDecodeError) -> str:
        bad_line = text.splitlines()[err.lineno - 1]
        pointer = " " * (err.colno - 1) + "^"
        return f"line {err.lineno}: {err.msg}\n{bad_line}\n{pointer}"

    try:
        json.loads(bad_json)
    except json.JSONDecodeError as e:
        report = describe_error(bad_json, e)
        assert report.startswith("line 3:")
        assert "^" in report

    print("OK")


if __name__ == "__main__":
    main()
