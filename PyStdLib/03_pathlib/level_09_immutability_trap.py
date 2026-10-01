"""
LEVEL 09 (advanced) - Production trap: Path is immutable, and with_suffix() never touches disk
====================================================================================================
You will learn
  * .with_suffix()/.with_name() return a NEW Path -- calling them and
    ignoring the result is a silent no-op, not an error
  * the realistic version of this bug: assuming .with_suffix(".bak") RENAMES
    the file on disk -- it does not touch the filesystem at all, it only
    computes a path string
  * demonstrated as a real failure first, then fixed with an explicit
    .rename()/.replace() call

Run: python level_09_immutability_trap.py
"""
import shutil
import tempfile
from pathlib import Path

if __name__ == "__main__":
    tmp_dir = Path(tempfile.mkdtemp(prefix="pystdlib_pathlib_lvl09_"))

    try:
        # --- the basic trap: ignoring the return value does nothing --------
        original = tmp_dir / "report.txt"
        original.with_suffix(".md")   # BUG: return value discarded
        assert original.name == "report.txt"   # unchanged -- Path objects never mutate in place

        renamed_in_memory = original.with_suffix(".md")   # FIX: capture the new Path
        assert renamed_in_memory.name == "report.md"
        assert original.name == "report.txt"   # the original is still untouched, as designed

        # --- the realistic trap: with_suffix() never touches the filesystem ---
        source = tmp_dir / "data.csv"
        source.write_text("id,value\n1,10\n")

        def buggy_backup(path: Path) -> None:
            # looks plausible: "give it a .bak extension" -- but with_suffix
            # only COMPUTES a new path, it never renames or copies anything
            path.with_suffix(".bak")

        buggy_backup(source)
        backup_path = source.with_suffix(".bak")
        assert source.exists() is True          # original still exactly where it was
        assert backup_path.exists() is False    # the "backup" was never actually created -- the bug

        def correct_backup(path: Path) -> Path:
            target = path.with_suffix(".bak")
            path.rename(target)   # the ACTUAL filesystem operation, using the computed path
            return target

        result_path = correct_backup(source)
        assert result_path.exists() is True
        assert result_path.read_text() == "id,value\n1,10\n"
        assert source.exists() is False   # rename() moves it -- the old name is genuinely gone

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
