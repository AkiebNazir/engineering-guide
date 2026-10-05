"""
LEVEL 01 (basic) - csv.writer() / csv.reader(): the round trip over a real file
==================================================================================
You will learn
  * csv.writer(file).writerow(list) writes one row from a list of fields
  * csv.reader(file) gives back an iterator of rows, each a list of strings
  * every field comes back as str -- csv never guesses types for you

Run: python level_01_reader_writer.py
"""
import csv
import os
import shutil
import tempfile


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "people.csv")
    try:
        rows = [
            ["name", "age", "city"],
            ["Ada", "36", "London"],
            ["Grace", "85", "New York"],
        ]

        # newline='' is required for correct csv behavior -- see level 9 for why.
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            for row in rows:
                writer.writerow(row)

        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            read_rows = list(reader)

        assert read_rows == rows

        # Every field is a plain string, even the numeric-looking ones.
        assert read_rows[1] == ["Ada", "36", "London"]
        assert isinstance(read_rows[1][1], str)
        assert read_rows[1][1] != 36    # "36" (str) != 36 (int)

        # writerows() writes several rows in one call -- equivalent to a loop.
        path2 = os.path.join(tmpdir, "people2.csv")
        with open(path2, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(rows)
        with open(path2, newline="", encoding="utf-8") as f:
            assert list(csv.reader(f)) == rows
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
