"""
LEVEL 02 (core) - csv.DictReader / csv.DictWriter: rows as dicts, not lists
==============================================================================
You will learn
  * DictWriter needs an explicit fieldnames= list and writes a header via writeheader()
  * DictReader uses the file's first row as fieldnames automatically
  * accessing columns by name instead of brittle positional indexing

Run: python level_02_dictreader_dictwriter.py
"""
import csv
import os
import shutil
import tempfile


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "inventory.csv")
    fieldnames = ["sku", "qty", "warehouse"]
    records = [
        {"sku": "A100", "qty": "5", "warehouse": "north"},
        {"sku": "B200", "qty": "12", "warehouse": "south"},
    ]
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()          # DictWriter does NOT write the header for you
            writer.writerows(records)

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == fieldnames   # read straight from the header row
            rows = list(reader)

        assert rows == records
        assert rows[0]["sku"] == "A100"              # named access, not rows[0][0]

        # DictReader can be given fieldnames= explicitly, for headerless files --
        # every row (including what would have been the header) is then data.
        headerless_path = os.path.join(tmpdir, "headerless.csv")
        with open(headerless_path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows([["A100", "5", "north"], ["B200", "12", "south"]])
        with open(headerless_path, newline="", encoding="utf-8") as f:
            reader2 = csv.DictReader(f, fieldnames=fieldnames)
            rows2 = list(reader2)
        assert rows2 == records

        # A row missing a trailing column gets None for the missing field (restval).
        short_path = os.path.join(tmpdir, "short.csv")
        with open(short_path, "w", newline="", encoding="utf-8") as f:
            f.write("sku,qty,warehouse\nC300,3\n")   # missing 'warehouse'
        with open(short_path, newline="", encoding="utf-8") as f:
            short_rows = list(csv.DictReader(f))
        assert short_rows[0]["warehouse"] is None
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
