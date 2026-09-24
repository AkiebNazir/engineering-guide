"""
LEVEL 09 (advanced) - production gotcha: 'w+' leaves you at EOF after writing
===============================================================================
You will learn
  * 'w+' opens a file for both reading and writing -- but the cursor tracks
    wherever the last operation left it, just like any other stream
  * writing then immediately reading (without seek(0)) silently returns '' --
    no exception, just data that looks "missing"
  * the one-line fix: seek(0) before reading what you just wrote

Run: python level_09_w_plus_seek_gotcha.py
"""
import os
import shutil
import tempfile


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "scratch.txt")
    try:
        # --- the bug ---
        with open(path, "w+", encoding="utf-8") as f:
            f.write("important data\n")
            broken_read = f.read()          # looks reasonable -- it is NOT
        # The write left the cursor at end-of-file. Reading from EOF yields ''.
        # This is the trap: no exception is raised, so it's easy to ship a
        # "read-after-write" bug that only shows up as silently empty data.
        assert broken_read == "", (
            "if this fails, seek() semantics changed -- re-check this lesson"
        )

        # The data IS actually in the file -- reopening proves it wasn't lost.
        with open(path, encoding="utf-8") as f:
            assert f.read() == "important data\n"

        # --- the fix ---
        with open(path, "w+", encoding="utf-8") as f:
            f.write("important data\n")
            f.seek(0)                       # rewind the cursor to the start
            fixed_read = f.read()
        assert fixed_read == "important data\n"

        # The same trap, avoided differently: track how many bytes/chars you wrote
        # and seek relative to that, instead of assuming position 0.
        with open(path, "w+", encoding="utf-8") as f:
            f.write("abc")
            f.write("def")
            f.seek(0, 1)                    # whence=1, offset=0 -- "where am I?" without moving
            here = f.tell()
            assert here == 6                # cursor sits after "abcdef", not at start
            f.seek(0)
            assert f.read() == "abcdef"
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
