"""
LEVEL 07 (advanced) - lifecycle: writing a JSON file atomically
==================================================================
You will learn
  * writing json.dump() straight into the real target file is NOT crash-safe --
    a crash mid-write leaves a truncated, corrupt file
  * the fix: write to a temp file in the same directory, flush+fsync, then
    os.replace() it over the target -- an atomic swap on POSIX and Windows both

Run: python level_07_atomic_write.py
"""
import json
import os
import shutil
import tempfile


def naive_save(path: str, data: dict) -> None:
    """NOT crash-safe: if the process dies mid-dump, `path` is left half-written."""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def atomic_save(path: str, data: dict) -> None:
    """Crash-safe: the target file is either the old complete version or the new one."""
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)   # atomic rename -- no in-between state is observable
    except BaseException:
        os.remove(tmp_path)
        raise


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    path = os.path.join(tmpdir, "state.json")
    try:
        naive_save(path, {"count": 1})
        with open(path, encoding="utf-8") as f:
            assert json.load(f) == {"count": 1}

        # Simulate a crash mid-write with the naive approach: truncate manually
        # to model what a partial write looks like on disk.
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"count": 2, "next')   # process "dies" here -- incomplete JSON
        with open(path, encoding="utf-8") as f:
            try:
                json.load(f)
                raise AssertionError("expected the truncated write to fail to parse")
            except json.JSONDecodeError:
                pass   # exactly the corruption atomic_save is designed to prevent

        # atomic_save leaves either the fully-old or fully-new content -- never partial.
        atomic_save(path, {"count": 1})
        atomic_save(path, {"count": 2})
        with open(path, encoding="utf-8") as f:
            assert json.load(f) == {"count": 2}

        # No leftover temp files after a successful save.
        leftovers = [n for n in os.listdir(tmpdir) if n.startswith(".tmp-")]
        assert leftovers == []
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
