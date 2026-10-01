"""
LEVEL 03 (core) - Idiom: build a small dataset, then derive sibling paths from it
=====================================================================================
You will learn
  * .mkdir(parents=True, exist_ok=True) to set up nested directories
  * .read_bytes()/.write_text() together in a realistic "process a file" flow
  * .with_suffix() to derive a related output path (same name, new extension)
  * .with_name() to derive a sibling path (same directory, different filename)

Run: python level_03_build_and_derive_idiom.py
"""
import shutil
import tempfile
from pathlib import Path

if __name__ == "__main__":
    tmp_dir = Path(tempfile.mkdtemp(prefix="pystdlib_pathlib_lvl03_"))

    try:
        # parents=True makes every missing intermediate directory;
        # exist_ok=True means calling it again on the same path is a no-op
        dataset_dir = tmp_dir / "pipeline" / "input"
        dataset_dir.mkdir(parents=True, exist_ok=True)
        dataset_dir.mkdir(parents=True, exist_ok=True)   # safe to repeat

        raw_path = dataset_dir / "measurements.raw"
        raw_path.write_text("10,20,30\n40,50,60\n")

        # a realistic tiny "process a file" step: read the raw bytes, compute
        # something, write the result next to it with a DIFFERENT extension
        raw_bytes = raw_path.read_bytes()
        total = sum(int(n) for n in raw_bytes.decode().replace("\n", ",").split(",") if n)

        # with_suffix swaps just the extension, keeping the same stem and dir
        summary_path = raw_path.with_suffix(".summary")
        assert summary_path.parent == raw_path.parent
        assert summary_path.name == "measurements.summary"
        summary_path.write_text(f"total={total}\n")
        assert summary_path.read_text() == "total=210\n"

        # with_name swaps the ENTIRE filename, keeping the same directory --
        # useful for "same folder, different file" derivations like a backup
        backup_path = raw_path.with_name("measurements.raw.bak")
        assert backup_path.parent == raw_path.parent
        backup_path.write_bytes(raw_bytes)
        assert backup_path.read_bytes() == raw_path.read_bytes()

        # with_suffix/with_name never mutate the original -- Path is immutable
        # (level 9 explores the trap this creates when people forget it)
        assert raw_path.name == "measurements.raw"

        # sanity: everything we built is really there, nothing else is
        names = sorted(p.name for p in dataset_dir.iterdir())
        assert names == ["measurements.raw", "measurements.raw.bak", "measurements.summary"]

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
