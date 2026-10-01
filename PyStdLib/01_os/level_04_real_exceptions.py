"""
LEVEL 04 (core) - Triggering the real exceptions os calls raise
==================================================================
You will learn
  * FileNotFoundError from removing/opening something that isn't there
  * FileExistsError from os.mkdir on a path that already exists
  * OSError "Directory not empty" from os.rmdir on a non-empty directory
  * NotADirectoryError from treating a file like a directory
  * IsADirectoryError/PermissionError from os.remove on a directory (the
    exact type is platform-dependent -- both are OSError subclasses)
  * inspecting the low-level .errno on any of these (they're all OSError)

Run: python level_04_real_exceptions.py
"""
import errno
import os
import shutil
import tempfile

if __name__ == "__main__":
    root = tempfile.mkdtemp(prefix="pystdlib_os_lvl04_")

    try:
        # 1. FileNotFoundError -- remove something that was never created
        missing = os.path.join(root, "ghost.txt")
        try:
            os.remove(missing)
            raise AssertionError("expected FileNotFoundError")
        except FileNotFoundError as e:
            assert e.errno == errno.ENOENT   # "No such file or directory"

        # 2. FileExistsError -- os.mkdir refuses to overwrite an existing dir
        existing = os.path.join(root, "already_here")
        os.mkdir(existing)
        try:
            os.mkdir(existing)
            raise AssertionError("expected FileExistsError")
        except FileExistsError as e:
            assert e.errno == errno.EEXIST

        # 3. OSError "directory not empty" -- os.rmdir only removes EMPTY dirs
        with open(os.path.join(existing, "inside.txt"), "w") as f:
            f.write("x")
        try:
            os.rmdir(existing)
            raise AssertionError("expected OSError (ENOTEMPTY)")
        except OSError as e:
            # FileExistsError/FileNotFoundError are themselves OSError subclasses;
            # "not empty" has no dedicated subclass, so this stays a plain OSError.
            assert e.errno == errno.ENOTEMPTY
            assert not isinstance(e, FileExistsError)

        # 4. NotADirectoryError -- os.listdir on a file, not a directory
        file_path = os.path.join(root, "just_a_file.txt")
        with open(file_path, "w") as f:
            f.write("data")
        try:
            os.listdir(file_path)
            raise AssertionError("expected NotADirectoryError")
        except NotADirectoryError as e:
            assert e.errno == errno.ENOTDIR

        # 5. The opposite mistake: os.remove on a directory. POSIX specifies
        # this should be IsADirectoryError (EISDIR), and Linux does exactly
        # that -- but macOS's remove(2) reports EPERM ("Operation not
        # permitted") for the same call, which Python surfaces as
        # PermissionError instead. Both are OSError subclasses either way, so
        # accept whichever this platform actually raises.
        try:
            os.remove(existing)
            raise AssertionError("expected IsADirectoryError or PermissionError")
        except (IsADirectoryError, PermissionError) as e:
            assert e.errno in (errno.EISDIR, errno.EPERM)

        # every one of the above is-a OSError, which is why a broad "except
        # OSError:" around filesystem code is the idiomatic catch-all
        assert issubclass(FileNotFoundError, OSError)
        assert issubclass(FileExistsError, OSError)
        assert issubclass(NotADirectoryError, OSError)
        assert issubclass(IsADirectoryError, OSError)

        print("OK")
    finally:
        shutil.rmtree(root, ignore_errors=True)
