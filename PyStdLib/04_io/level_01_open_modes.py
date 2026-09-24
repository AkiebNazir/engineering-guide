"""
LEVEL 01 (basic) - open() and its mode characters
==================================================
You will learn
  * what open() actually does: it hands you a stream object, not the file's bytes
  * the mode characters: 'r' read, 'w' write (truncates!), 'a' append, 'x' exclusive-create,
    'b' binary suffix, '+' read-and-write suffix
  * why 'w' silently destroys existing content and 'x' refuses to

Run: python level_01_open_modes.py
"""
import os
import tempfile


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "notes.txt")
    try:
        # 'w' (write, text): creates the file if missing, TRUNCATES if it exists.
        with open(path, "w", encoding="utf-8") as f:
            f.write("first line\n")
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == "first line\n"

        # 'w' again on the same path throws away what was there before.
        with open(path, "w", encoding="utf-8") as f:
            f.write("overwritten\n")
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == "overwritten\n"   # "first line" is gone

        # 'a' (append) never truncates: new writes land after existing content.
        with open(path, "a", encoding="utf-8") as f:
            f.write("appended\n")
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == "overwritten\nappended\n"

        # 'x' (exclusive create) succeeds only if the file does NOT already exist.
        fresh_path = os.path.join(tmpdir, "fresh.txt")
        with open(fresh_path, "x", encoding="utf-8") as f:
            f.write("brand new\n")
        try:
            open(fresh_path, "x", encoding="utf-8")
            raise AssertionError("expected FileExistsError")
        except FileExistsError:
            pass   # 'x' refuses to clobber -- exactly the safety 'w' does not give you

        # 'b' suffix: binary mode. No text decoding, no newline translation -- raw bytes in/out.
        bin_path = os.path.join(tmpdir, "data.bin")
        with open(bin_path, "wb") as f:
            f.write(b"\x00\x01\x02\xff")
        with open(bin_path, "rb") as f:
            raw = f.read()
        assert raw == b"\x00\x01\x02\xff"
        assert isinstance(raw, bytes)   # binary mode gives bytes, never str

        # '+' suffix: read AND write through the same handle.
        with open(path, "r+", encoding="utf-8") as f:
            first_char = f.read(1)
            assert first_char == "o"          # "overwritten..." -- read didn't truncate
            f.seek(0)
            f.write("O")                      # overwrite just the first byte in place
        with open(path, "r", encoding="utf-8") as f:
            assert f.read().startswith("Overwritten")
    finally:
        import shutil
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
