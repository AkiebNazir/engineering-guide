"""
LEVEL 01 (basic) - Path construction, the / operator, and read/write text
=============================================================================
You will learn
  * building a Path from a string, and joining segments with the / operator
  * .write_text()/.read_text() -- open+write+close in one call, each way
  * a Path prints and compares like the path it represents

Run: python level_01_construct_and_readwrite.py
"""
import tempfile
import shutil
from pathlib import Path

if __name__ == "__main__":
    tmp_dir = Path(tempfile.mkdtemp(prefix="pystdlib_pathlib_lvl01_"))

    try:
        # the / operator joins path segments -- this is THE thing that makes
        # pathlib nicer to read than os.path.join(a, b, c)
        file_path = tmp_dir / "notes.txt"
        assert isinstance(file_path, Path)
        assert str(file_path) == str(tmp_dir) + "/notes.txt" or str(file_path).endswith("notes.txt")

        # write_text(): the single most common use -- no manual open()/close()
        file_path.write_text("hello pathlib\n")

        # read_text(): the matching read -- returns the whole file as one str
        content = file_path.read_text()
        assert content == "hello pathlib\n"

        # two Path objects naming the same location compare equal, even
        # though they're different objects
        same_path = tmp_dir / "notes.txt"
        assert file_path == same_path
        assert file_path is not same_path

        # Path also supports the plain constructor with multiple segments,
        # equivalent to chaining /
        via_constructor = Path(str(tmp_dir), "notes.txt")
        assert via_constructor == file_path

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
