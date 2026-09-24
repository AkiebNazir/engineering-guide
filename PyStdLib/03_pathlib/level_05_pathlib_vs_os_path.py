"""
LEVEL 05 (advanced) - Side by side: pathlib vs the equivalent os.path calls
==============================================================================
You will learn
  * every pathlib method used here has a direct os.path/os equivalent
  * proving, with asserts, that both approaches agree on the same paths
  * WHY pathlib is generally preferred for new code: chaining and readability,
    not new capability -- see PyStdLib/01_os/GUIDE.md for when raw os still wins

Run: python level_05_pathlib_vs_os_path.py
"""
import os
import shutil
import tempfile
from pathlib import Path

if __name__ == "__main__":
    tmp_dir_str = tempfile.mkdtemp(prefix="pystdlib_pathlib_lvl05_")
    tmp_dir_path = Path(tmp_dir_str)

    try:
        # --- joining -------------------------------------------------------
        os_joined = os.path.join(tmp_dir_str, "sub", "file.txt")
        pathlib_joined = tmp_dir_path / "sub" / "file.txt"
        assert os_joined == str(pathlib_joined)

        # --- splitting: os.path.split(head, tail) vs .parent / .name ------
        os_head, os_tail = os.path.split(os_joined)
        assert os_head == str(pathlib_joined.parent)
        assert os_tail == pathlib_joined.name

        # --- splitext vs .suffix / .stem -----------------------------------
        os_root, os_ext = os.path.splitext(os_joined)
        assert os_ext == pathlib_joined.suffix
        assert os.path.basename(os_root) == pathlib_joined.stem

        # --- exists / isfile / isdir -----------------------------------------
        os.makedirs(os.path.join(tmp_dir_str, "sub"), exist_ok=True)
        with open(os_joined, "w") as f:
            f.write("data")

        assert os.path.exists(os_joined) == pathlib_joined.exists() == True
        assert os.path.isfile(os_joined) == pathlib_joined.is_file() == True
        assert os.path.isdir(os_joined) == pathlib_joined.is_dir() == False
        assert os.path.isdir(os_head) == pathlib_joined.parent.is_dir() == True

        # --- abspath vs .absolute() -------------------------------------------
        os.chdir(tmp_dir_str)   # restored in the outer finally block below
        relative = "sub/file.txt"
        assert os.path.abspath(relative) == str(Path(relative).absolute())

        # --- reading a whole file: open()+read() vs .read_text() --------------
        with open(os_joined) as f:
            os_content = f.read()
        pathlib_content = pathlib_joined.read_text()
        assert os_content == pathlib_content == "data"

        # --- listing a directory: os.listdir vs .iterdir -----------------------
        os_names = sorted(os.listdir(os_head))
        pathlib_names = sorted(p.name for p in pathlib_joined.parent.iterdir())
        assert os_names == pathlib_names == ["file.txt"]

        # --- stat: os.stat(path) vs Path.stat() return the SAME result type --
        os_stat = os.stat(os_joined)
        pathlib_stat = pathlib_joined.stat()
        assert type(os_stat) is type(pathlib_stat)
        assert os_stat.st_size == pathlib_stat.st_size == 4   # len("data")

        print("OK")
    finally:
        os.chdir(tempfile.gettempdir())
        shutil.rmtree(tmp_dir_str, ignore_errors=True)
