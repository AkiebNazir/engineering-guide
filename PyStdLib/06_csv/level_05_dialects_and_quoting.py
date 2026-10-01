"""
LEVEL 05 (advanced) - dialects (excel vs unix), quoting modes, custom delimiters
===================================================================================
You will learn
  * the built-in 'excel' dialect (default: \\r\\n endings, minimal quoting) vs
    'unix' (\\n endings, every field quoted)
  * the four quoting modes: QUOTE_MINIMAL, QUOTE_ALL, QUOTE_NONNUMERIC, QUOTE_NONE
  * delimiter= and quotechar= for non-comma, non-double-quote formats (e.g. TSV)

Run: python level_05_dialects_and_quoting.py
"""
import csv
import io


def main() -> None:
    row = ["1", "plain", "has,comma"]

    # --- excel (default) vs unix dialect ---
    excel_buf = io.StringIO()
    csv.writer(excel_buf, dialect="excel").writerow(row)
    assert excel_buf.getvalue() == '1,plain,"has,comma"\r\n'   # CRLF, only the risky field quoted

    unix_buf = io.StringIO()
    csv.writer(unix_buf, dialect="unix").writerow(row)
    assert unix_buf.getvalue() == '"1","plain","has,comma"\n'   # LF, EVERY field quoted

    # --- QUOTE_MINIMAL: only quote fields that need it (the default) ---
    minimal = io.StringIO()
    csv.writer(minimal, quoting=csv.QUOTE_MINIMAL).writerow(["plain", "has,comma"])
    assert minimal.getvalue() == "plain,\"has,comma\"\r\n"

    # --- QUOTE_ALL: quote every field, regardless of content ---
    all_quoted = io.StringIO()
    csv.writer(all_quoted, quoting=csv.QUOTE_ALL).writerow(["plain", "42"])
    assert all_quoted.getvalue() == '"plain","42"\r\n'

    # --- QUOTE_NONNUMERIC: quote everything that isn't a number; reader converts
    #     every UNQUOTED field to float automatically ---
    nonnumeric = io.StringIO()
    csv.writer(nonnumeric, quoting=csv.QUOTE_NONNUMERIC).writerow(["plain", 42, 3.5])
    assert nonnumeric.getvalue() == '"plain",42,3.5\r\n'
    nonnumeric.seek(0)
    parsed = next(csv.reader(nonnumeric, quoting=csv.QUOTE_NONNUMERIC))
    assert parsed == ["plain", 42.0, 3.5]
    assert all(isinstance(v, float) for v in parsed[1:])   # reader coerced these to float

    # --- QUOTE_NONE: never quote -- the writer instead escapes the delimiter
    #     with escapechar=, and refuses to write unescapable content ---
    none_buf = io.StringIO()
    writer = csv.writer(none_buf, quoting=csv.QUOTE_NONE, escapechar="\\")
    writer.writerow(["plain", "has,comma"])
    assert none_buf.getvalue() == "plain,has\\,comma\r\n"    # comma escaped, not quoted

    # --- custom delimiter/quotechar: e.g. a pipe-delimited, single-quoted format ---
    custom = io.StringIO()
    csv.writer(custom, delimiter="|", quotechar="'").writerow(["a|b", "plain"])
    assert custom.getvalue() == "'a|b'|plain\r\n"
    custom.seek(0)
    assert next(csv.reader(custom, delimiter="|", quotechar="'")) == ["a|b", "plain"]

    print("OK")


if __name__ == "__main__":
    main()
