"""
LEVEL 03 (core) - seek()/tell() and whence: a "tail the last N bytes" idiom
============================================================================
You will learn
  * tell() reports the current byte offset; seek(offset, whence) moves it
  * whence=0 (default, from start), whence=1 (from current position), whence=2 (from end)
  * combining seek(whence=2) with a negative offset to read a file's tail without
    loading the whole thing into memory -- a real, common idiom for log files

Run: python level_03_seek_tail_idiom.py
"""
import os
import shutil
import tempfile


def tail_bytes(path: str, n: int) -> bytes:
    """Return the last n bytes of a file without reading the whole file."""
    with open(path, "rb") as f:
        f.seek(0, 2)              # whence=2: jump to end-of-file
        size = f.tell()           # tell() -- current offset -- now equals file size
        back = min(n, size)
        f.seek(-back, 2)          # whence=2 + negative offset: 'back' bytes before EOF
        return f.read()


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "log.txt")
    try:
        lines = [f"line-{i:03d}\n" for i in range(1000)]
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(lines)

        with open(path, "rb") as f:
            assert f.tell() == 0                # fresh handle starts at offset 0
            f.seek(0, 2)                          # whence=2 = end of file
            end = f.tell()
            expected_size = sum(len(line) for line in lines)
            assert end == expected_size

            f.seek(0)                             # whence=0 (default) = absolute from start
            assert f.tell() == 0
            f.seek(20, 1)                         # whence=1 = relative to current position
            f.seek(10, 1)
            assert f.tell() == 30

        # The tail idiom: get the last 3 lines' worth of bytes without reading the file.
        last_lines_text = "".join(lines[-3:])
        tail = tail_bytes(path, len(last_lines_text.encode("utf-8")))
        assert tail.decode("utf-8") == last_lines_text

        # Asking for more bytes than the file has just returns the whole file.
        whole = tail_bytes(path, 10 ** 9)
        assert whole == "".join(lines).encode("utf-8")
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
