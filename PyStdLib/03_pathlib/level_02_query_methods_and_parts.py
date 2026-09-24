"""
LEVEL 02 (core) - Core surface: exists/is_file/is_dir, resolve/absolute, name parts
=======================================================================================
You will learn
  * .exists()/.is_file()/.is_dir() -- the questions you ask before acting on a path
  * .resolve() (follows symlinks, normalizes) vs .absolute() (purely syntactic)
  * .iterdir() to list a directory's direct children as Path objects
  * .name/.stem/.suffix/.parent/.parts -- pulling a path apart without string slicing

Run: python level_02_query_methods_and_parts.py
"""
import os
import shutil
import tempfile
from pathlib import Path

if __name__ == "__main__":
    tmp_dir = Path(tempfile.mkdtemp(prefix="pystdlib_pathlib_lvl02_"))

    try:
        sub_dir = tmp_dir / "reports"
        sub_dir.mkdir()
        report = sub_dir / "quarterly.report.csv"
        report.write_text("id,total\n1,100\n")

        # --- exists / is_file / is_dir ---------------------------------------
        assert report.exists() is True
        assert report.is_file() is True
        assert report.is_dir() is False
        assert sub_dir.is_dir() is True
        missing = sub_dir / "ghost.csv"
        assert missing.exists() is False

        # --- resolve vs absolute -----------------------------------------------
        # .absolute() is purely syntactic: cwd + path, no symlink following,
        # and it does NOT require the path to exist.
        relative_missing = Path("does/not/exist.txt")
        assert relative_missing.absolute() == Path.cwd() / relative_missing

        # .resolve() normalizes ".." segments and follows symlinks -- compare
        # through realpath since macOS's /tmp is itself a symlink to /private/tmp
        messy = tmp_dir / "reports" / ".." / "reports" / "quarterly.report.csv"
        assert os.path.realpath(str(messy.resolve())) == os.path.realpath(str(report))

        # --- iterdir: direct children only, as Path objects ---------------------
        (tmp_dir / "top_level.txt").write_text("x")
        children = sorted(p.name for p in tmp_dir.iterdir())
        assert children == ["reports", "top_level.txt"]   # not report's own children

        # --- pulling a path apart -----------------------------------------------
        assert report.name == "quarterly.report.csv"
        assert report.suffix == ".csv"          # only the LAST extension
        assert report.stem == "quarterly.report"   # name minus the last suffix only
        assert report.parent == sub_dir
        assert report.parent.parent == tmp_dir
        assert report.parts[-2:] == ("reports", "quarterly.report.csv")

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
