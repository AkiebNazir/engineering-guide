"""
LEVEL 07 (advanced) - flush(), close(), and fsync(): the durability lifecycle
===============================================================================
You will learn
  * write() may only reach an internal buffer -- flush() pushes it to the OS
  * flush() is NOT durability: the OS can still cache it in memory
  * os.fsync(fileobj.fileno()) is what actually forces bytes onto storage
  * the context manager guarantees close() (and therefore flush()) even on an exception

Run: python level_07_flush_and_close.py
"""
import os
import shutil
import tempfile


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "durable.txt")
    try:
        # Before flush(), a buffered write may not be visible to a second, independent
        # read of the same file on some platforms/buffering configurations. We can't
        # portably assert the *pre-flush* invisibility (buffering size varies), but we
        # CAN prove the mechanism: an explicit flush() makes the write visible without
        # having to close() the handle first.
        f = open(path, "w", encoding="utf-8")
        f.write("committed\n")
        f.flush()                          # push from Python's buffer to the OS
        os.fsync(f.fileno())               # push from the OS cache to actual storage
        with open(path, encoding="utf-8") as reader:
            assert reader.read() == "committed\n"
        f.close()

        # flush() vs close(): close() always flushes first, then releases the OS handle.
        f2 = open(path, "a", encoding="utf-8")
        f2.write("more\n")
        f2.close()
        assert f2.closed is True
        try:
            f2.write("after close")
            raise AssertionError("expected ValueError writing to a closed file")
        except ValueError:
            pass

        # The context manager's real job: close() runs even when the block raises.
        class Boom(Exception):
            pass

        handle_ref = {}
        try:
            with open(path, "a", encoding="utf-8") as f3:
                handle_ref["f3"] = f3
                f3.write("before boom\n")
                raise Boom("something went wrong mid-write")
        except Boom:
            pass
        assert handle_ref["f3"].closed is True   # closed despite the exception

        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "committed\n" in content
        assert "more\n" in content
        assert "before boom\n" in content   # the write before the exception was still flushed
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
