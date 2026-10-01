"""
LEVEL 03 (core) - a realistic idiom: commas, quotes, and newlines round-trip
==============================================================================
You will learn
  * csv automatically quotes any field containing the delimiter, the quote
    character, or a newline -- you never have to escape these yourself
  * an embedded quote character is escaped by doubling it ("" inside a quoted field)
  * writing and reading such fields gives back byte-for-byte identical strings

Run: python level_03_embedded_special_chars.py
"""
import csv
import os
import shutil
import tempfile


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "messy.csv")
    tricky_rows = [
        ["id", "note"],
        ["1", "contains, a comma"],
        ["2", 'contains "a quote"'],
        ["3", "contains\na newline"],
        ["4", 'comma, "quote", and\nnewline all at once'],
    ]
    try:
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(tricky_rows)

        # Look at the raw bytes: the writer added quotes and doubled the embedded quote.
        with open(path, encoding="utf-8") as f:
            raw = f.read()
        assert '"contains, a comma"' in raw
        assert '"contains ""a quote"""' in raw   # doubled "" is how a literal quote is escaped

        with open(path, newline="", encoding="utf-8") as f:
            read_back = list(csv.reader(f))

        assert read_back == tricky_rows   # every field survives exactly, quirks and all

        # DictWriter/DictReader handle exactly the same tricky content the same way.
        dict_path = os.path.join(tmpdir, "messy_dict.csv")
        record = {"id": "5", "note": 'a "quoted", multi\nline value'}
        with open(dict_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "note"])
            writer.writeheader()
            writer.writerow(record)
        with open(dict_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert rows == [record]
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
