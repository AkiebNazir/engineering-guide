"""
LEVEL 04 (core) - Triggering the real exceptions Path methods raise
======================================================================
You will learn
  * FileNotFoundError from .read_text() on a missing file
  * FileExistsError from .mkdir() on a path that already exists (no exist_ok)
  * FileNotFoundError from .unlink() on a missing file (no missing_ok)
  * NotADirectoryError from .iterdir() on a file, not a directory

Run: python level_04_real_exceptions.py
"""
import shutil
import tempfile
from pathlib import Path

if __name__ == "__main__":
    tmp_dir = Path(tempfile.mkdtemp(prefix="pystdlib_pathlib_lvl04_"))

    try:
        # 1. FileNotFoundError -- reading a file that was never created
        ghost = tmp_dir / "ghost.txt"
        try:
            ghost.read_text()
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError:
            pass

        # 2. FileExistsError -- mkdir() without exist_ok refuses a duplicate
        existing_dir = tmp_dir / "already_here"
        existing_dir.mkdir()
        try:
            existing_dir.mkdir()
            raise AssertionError("expected FileExistsError")
        except FileExistsError:
            pass
        # the exist_ok=True escape hatch makes the identical call a no-op
        existing_dir.mkdir(exist_ok=True)   # does not raise

        # 3. FileNotFoundError -- unlink() without missing_ok on a missing file
        missing_file = tmp_dir / "was_never_written.txt"
        try:
            missing_file.unlink()
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError:
            pass
        missing_file.unlink(missing_ok=True)   # the idempotent version: does not raise

        # 4. NotADirectoryError -- iterdir() on a plain file
        plain_file = tmp_dir / "plain.txt"
        plain_file.write_text("just a file")
        try:
            list(plain_file.iterdir())
            raise AssertionError("expected NotADirectoryError")
        except NotADirectoryError:
            pass

        # all of these are OSError subclasses, same as the raw os module --
        # pathlib doesn't invent a parallel exception hierarchy
        assert issubclass(FileNotFoundError, OSError)
        assert issubclass(FileExistsError, OSError)
        assert issubclass(NotADirectoryError, OSError)

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
