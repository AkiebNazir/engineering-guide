"""
LEVEL 09 (advanced) - production gotcha: opening CSV files without newline=''
================================================================================
You will learn
  * the Python docs' own warning: without newline='', embedded newlines inside
    quoted fields are not interpreted correctly by the platform's universal-newline
    text translation, happening BEFORE csv ever sees the bytes
  * this demonstrates the actual, measured corruption on this machine: reading
    without newline='' silently turns an embedded \\r into \\n, losing information
  * the fix is one keyword argument, on both the write side and the read side

Run: python level_09_newline_gotcha.py
"""
import csv
import os
import shutil
import tempfile


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "gotcha.csv")
    try:
        # A field with an embedded carriage return, e.g. text pasted from an
        # old Mac-style or mixed-line-ending source.
        original_value = "line1\rline2"

        with open(path, "w", newline="", encoding="utf-8") as f:   # correct on the write side
            writer = csv.writer(f)
            writer.writerow(["id", "note"])
            writer.writerow([1, original_value])

        with open(path, "rb") as f:
            raw = f.read()
        assert b"line1\rline2" in raw   # the exact bytes are on disk, untouched

        # --- the bug: read WITHOUT newline='' ---
        # Universal-newline translation (the default for text mode) rewrites any
        # lone \r or \r\n it sees -- including ones sitting inside a quoted field --
        # to \n, before csv's own parser ever runs.
        with open(path, "r", encoding="utf-8") as f:   # BUG: missing newline=''
            broken_rows = list(csv.reader(f))
        broken_value = broken_rows[1][1]
        assert broken_value != original_value, (
            "if this fails, universal-newline translation no longer corrupts this "
            "case on this platform -- re-verify the lesson still demonstrates a bug"
        )
        assert broken_value == "line1\nline2"   # the \r silently became \n -- data changed

        # --- the fix: read WITH newline='' ---
        with open(path, "r", newline="", encoding="utf-8") as f:
            fixed_rows = list(csv.reader(f))
        fixed_value = fixed_rows[1][1]
        assert fixed_value == original_value    # exact round trip, \r preserved
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
