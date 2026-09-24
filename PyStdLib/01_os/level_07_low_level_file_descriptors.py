"""
LEVEL 07 (advanced) - Resource management: raw file descriptors
===================================================================
You will learn
  * os.open()/os.read()/os.write()/os.close() -- the syscalls underneath
    Python's built-in open()
  * the O_RDONLY / O_WRONLY / O_CREAT / O_TRUNC flag constants
  * why a raw fd leaks on an exception unless you wrap it in try/finally
  * os.fdopen() to turn a raw fd into a normal Python file object that DOES
    support "with" (a context manager closes it for you automatically)

Run: python level_07_low_level_file_descriptors.py
"""
import os
import shutil
import tempfile

if __name__ == "__main__":
    tmp_dir = tempfile.mkdtemp(prefix="pystdlib_os_lvl07_")
    path = os.path.join(tmp_dir, "raw.bin")

    try:
        # os.open returns an integer file descriptor, not a Python file object.
        # O_WRONLY | O_CREAT | O_TRUNC == "write, create if missing, empty it
        # first" -- the same intent as Python's open(path, "w"), spelled out
        # at the syscall level. 0o644 is the permission mode for a NEW file.
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
        try:
            written = os.write(fd, b"hello raw world")
            assert written == len(b"hello raw world")
        finally:
            os.close(fd)   # MUST close manually -- a raw fd has no __del__ safety net

        # closing twice is a programming error, not a safe no-op like it is
        # for some Python objects -- os.close on an already-closed fd raises
        try:
            os.close(fd)
            raise AssertionError("expected OSError on double-close")
        except OSError:
            pass

        # read it back with the raw API too
        fd = os.open(path, os.O_RDONLY)
        try:
            data = os.read(fd, 1024)   # must give a max-bytes size, unlike file.read()
            assert data == b"hello raw world"
        finally:
            os.close(fd)

        # THE LEAK, demonstrated: if the code between open() and close() raises
        # and there's no try/finally, close() is simply never reached.
        leaked_fd = os.open(path, os.O_RDONLY)
        leaked = False
        try:
            raise RuntimeError("pretend something goes wrong mid-read")
        except RuntimeError:
            leaked = True   # os.close(leaked_fd) was skipped -- the fd is now leaked
        assert leaked
        os.close(leaked_fd)   # clean up manually since this demo intentionally skipped the try/finally

        # THE FIX: os.fdopen wraps a raw fd in a real Python file object, which
        # supports "with" -- the fd is closed automatically even if the body
        # raises, no manual try/finally bookkeeping required.
        fd = os.open(path, os.O_RDONLY)
        with os.fdopen(fd, "rb") as f:
            assert f.read() == b"hello raw world"
        # fd is now closed by the context manager -- using it again fails
        try:
            os.read(fd, 1)
            raise AssertionError("expected OSError: fd closed by os.fdopen's context manager")
        except OSError:
            pass

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
