"""
LEVEL 07 (advanced) - streaming a large CSV file without loading it into memory
==================================================================================
You will learn
  * csv.reader(f) is already a lazy iterator -- it pulls one row at a time
  * list(csv.reader(f)) defeats that: it materializes every row up front
  * a streaming aggregation (sum, filter) never needs more than one row in memory

Run: python level_07_streaming_large_file.py
"""
import csv
import os
import shutil
import sys
import tempfile

ROW_COUNT = 100_000


def write_large_csv(path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "amount"])
        for i in range(ROW_COUNT):
            writer.writerow([i, i % 100])


def sum_amounts_streaming(path: str) -> int:
    """Never holds more than one row in memory at a time."""
    total = 0
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)                     # skip header
        for row in reader:                # one row alive at a time -- this IS the streaming
            total += int(row[1])
    return total


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "big.csv")
    try:
        write_large_csv(path)

        expected_total = sum(i % 100 for i in range(ROW_COUNT))
        streaming_total = sum_amounts_streaming(path)
        assert streaming_total == expected_total

        # Prove the reader really is a one-pass iterator, not a hidden list: peek
        # at the type, and confirm it has no length/indexing (unlike a list).
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            assert not hasattr(reader, "__len__")
            assert not hasattr(reader, "__getitem__")
            first_row = next(reader)
            assert first_row == ["id", "amount"]
            # only ONE row has been pulled from the file so far -- the rest is
            # still sitting unread on disk, not in Python memory
            second_row = next(reader)
            assert second_row == ["0", "0"]

        # By contrast, list(reader) pulls the whole file into memory at once --
        # useful when you truly need random access, wasteful otherwise.
        with open(path, newline="", encoding="utf-8") as f:
            materialized = list(csv.reader(f))
        assert len(materialized) == ROW_COUNT + 1
        approx_bytes = sys.getsizeof(materialized) + sum(sys.getsizeof(r) for r in materialized)
        assert approx_bytes > 1_000_000   # a real, non-trivial amount of memory held at once
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
