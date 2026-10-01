"""
LEVEL 10 (advanced) - Capstone: a small structured-log parser
=================================================================
You will learn
  * combining a compiled VERBOSE pattern with named groups to parse a log format
  * re.error handling for malformed lines that don't fit the schema
  * re.sub() with a function to redact sensitive fields before reporting
  * collections.Counter to summarize parsed results

Run: python level_10_log_parser_capstone.py
"""
import re
from collections import Counter

LOG_LINE_PATTERN = re.compile(r"""
    ^
    (?P<timestamp>\d{4}-\d{2}-\d{2}\ \d{2}:\d{2}:\d{2})
    \s+
    (?P<level>DEBUG|INFO|WARNING|ERROR)
    \s+
    (?P<message>.*)
    $
""", re.VERBOSE)

RAW_LOG = """\
2024-03-15 08:01:02 INFO user 42 logged in from card 4111-1111-1111-1111
2024-03-15 08:02:10 ERROR payment failed for card 4222-2222-2222-2222
this line does not match the schema at all
2024-03-15 08:03:44 WARNING retrying request, attempt 2
2024-03-15 08:04:00 INFO user 42 logged out
"""


def parse_log(raw: str):
    """Parse each line; return (records, unparseable_lines)."""
    records, bad_lines = [], []
    for line in raw.splitlines():
        if not line.strip():
            continue
        m = LOG_LINE_PATTERN.fullmatch(line)   # fullmatch: the ENTIRE line must fit the schema
        if m is None:
            bad_lines.append(line)
            continue
        records.append(m.groupdict())
    return records, bad_lines


def redact_card_numbers(message: str) -> str:
    """Replace any 16-digit-with-dashes card number with a masked version."""
    def mask(match: re.Match) -> str:
        digits = match.group().replace("-", "")
        return f"XXXX-XXXX-XXXX-{digits[-4:]}"
    return re.sub(r"\d{4}-\d{4}-\d{4}-\d{4}", mask, message)


if __name__ == "__main__":
    records, bad_lines = parse_log(RAW_LOG)

    # 4 well-formed lines, 1 malformed one, exactly as authored above
    assert len(records) == 4
    assert len(bad_lines) == 1
    assert bad_lines[0] == "this line does not match the schema at all"

    # named groups made every field directly addressable, no positional guessing
    first = records[0]
    assert first["timestamp"] == "2024-03-15 08:01:02"
    assert first["level"] == "INFO"
    assert "logged in" in first["message"]

    # summarize levels with Counter -- interop with the collections module
    level_counts = Counter(r["level"] for r in records)
    assert level_counts["INFO"] == 2
    assert level_counts["ERROR"] == 1
    assert level_counts["WARNING"] == 1

    # redact sensitive data in messages before, say, writing them to a shared report
    redacted = [redact_card_numbers(r["message"]) for r in records]
    assert redacted[0] == "user 42 logged in from card XXXX-XXXX-XXXX-1111"
    assert redacted[1] == "payment failed for card XXXX-XXXX-XXXX-2222"
    assert "4111" not in redacted[0] and "4222" not in redacted[1]

    # a bad pattern in a hypothetical "user-supplied" filter is still a real re.error
    try:
        re.compile("(unterminated")
        raise AssertionError("expected re.error")
    except re.error:
        pass

    print(f"parsed {len(records)} lines, {len(bad_lines)} malformed")
    print(f"level counts: {dict(level_counts)}")
    print("OK")
