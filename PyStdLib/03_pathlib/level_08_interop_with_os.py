"""
LEVEL 08 (advanced) - Interop: Path objects work directly with raw os calls
==============================================================================
You will learn
  * Path implements the os.PathLike protocol (__fspath__), so os functions
    accept a Path directly -- no str(path) conversion needed anywhere
  * Path.stat() returns the exact same os.stat_result as os.stat()
  * combining Path for navigation with os.chmod/os.stat for permission bits
    (the same bits explored in PyStdLib/01_os/level_08_stat_module_and_chmod.py)

Run: python level_08_interop_with_os.py
"""
import os
import shutil
import stat
import tempfile
from pathlib import Path

if __name__ == "__main__":
    tmp_dir = Path(tempfile.mkdtemp(prefix="pystdlib_pathlib_lvl08_"))
    file_path = tmp_dir / "shared.txt"

    try:
        file_path.write_text("interop demo")

        # os.PathLike: raw os functions accept a Path object directly
        assert isinstance(file_path, os.PathLike)
        assert os.fspath(file_path) == str(file_path)

        # os.stat(Path) works with no conversion, and returns the SAME type
        # as Path.stat() -- they are not two different APIs, just two
        # entry points to the identical underlying syscall
        os_info = os.stat(file_path)
        path_info = file_path.stat()
        assert type(os_info) is type(path_info)
        assert os_info.st_size == path_info.st_size == len("interop demo")
        assert os_info.st_mtime == path_info.st_mtime

        # os.chmod also accepts the Path directly
        os.chmod(file_path, 0o600)
        refreshed = file_path.stat()
        assert stat.S_IMODE(refreshed.st_mode) == 0o600

        # os.path functions accept a Path too, returning plain strings back
        assert os.path.isfile(file_path) is True
        assert os.path.dirname(file_path) == str(tmp_dir)

        # and the raw low-level fd API (PyStdLib/01_os/level_07) also accepts
        # a Path directly for the path argument
        fd = os.open(file_path, os.O_RDONLY)
        try:
            assert os.read(fd, 1024) == b"interop demo"
        finally:
            os.close(fd)

        # restore a permissive mode so cleanup can always delete it
        os.chmod(file_path, 0o644)

        print("OK")
    finally:
        os.chmod(file_path, 0o644)
        shutil.rmtree(tmp_dir, ignore_errors=True)
