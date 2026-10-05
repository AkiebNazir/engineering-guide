"""
LEVEL 02 (core) - the read/write API surface, on real files and in-memory ones
===============================================================================
You will learn
  * read(), write(), readline(), readlines(), and line-by-line iteration
  * io.StringIO / io.BytesIO: in-memory streams with the exact same API as real files
  * why a file iterator is a one-shot resource (exhausted after one pass)

Run: python level_02_core_api.py
"""
import io
import os
import shutil
import tempfile


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "poem.txt")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("roses are red\nviolets are blue\nio is useful\n")

        # read(n): pull exactly n characters (or all, if n omitted / negative).
        with open(path, encoding="utf-8") as f:
            assert f.read(5) == "roses"
            rest = f.read()
            assert rest.startswith(" are red\n")

        # readline(): one line at a time, newline included.
        with open(path, encoding="utf-8") as f:
            assert f.readline() == "roses are red\n"
            assert f.readline() == "violets are blue\n"

        # readlines(): the whole file as a list of lines -- loads it all into memory.
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
        assert lines == ["roses are red\n", "violets are blue\n", "io is useful\n"]

        # Iterating a file object directly is the idiomatic, memory-friendly way
        # to go line by line (it doesn't require readlines()'s full-file list).
        with open(path, encoding="utf-8") as f:
            seen = [line.rstrip("\n") for line in f]
            # the iterator is exhausted after one pass -- a second loop yields nothing
            second_pass = list(f)
        assert seen == ["roses are red", "violets are blue", "io is useful"]
        assert second_pass == []

        # --- io.StringIO: an in-memory text stream with the identical API ---
        buf = io.StringIO()
        buf.write("hello ")
        buf.write("world")
        assert buf.getvalue() == "hello world"
        buf.seek(0)                       # rewind before reading, same as a real file
        assert buf.read() == "hello world"

        # Anything written expecting "a file" happily accepts a StringIO instead --
        # useful for testing code without touching disk.
        report = io.StringIO()
        for n in range(3):
            print(f"item {n}", file=report)
        assert report.getvalue() == "item 0\nitem 1\nitem 2\n"

        # --- io.BytesIO: the binary counterpart ---
        bbuf = io.BytesIO()
        bbuf.write(b"\x01\x02")
        bbuf.write(b"\x03")
        assert bbuf.getvalue() == b"\x01\x02\x03"
        bbuf.seek(0)
        assert bbuf.read(2) == b"\x01\x02"
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
