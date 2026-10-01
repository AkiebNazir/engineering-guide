"""
LEVEL 06 (advanced) - MEASURED: Path.rglob() vs a hand-rolled os.walk search
================================================================================
You will learn
  * .glob() is NOT recursive by default; .rglob() (or glob("**/pattern")) is
  * building a real nested tree and timing two ways to find every match:
    Path.rglob(pattern) vs manually walking with os.walk + fnmatch
  * this file prints REAL numbers from THIS run -- it reports whichever
    approach actually won, not whichever "should" win

Run: python level_06_glob_vs_manual_walk_speed.py
"""
import fnmatch
import os
import shutil
import tempfile
import time
from pathlib import Path

DEPTH = 4
DIRS_PER_LEVEL = 4
FILES_PER_DIR = 15
REPEATS = 5


def build_tree(root: Path, depth: int) -> None:
    for i in range(FILES_PER_DIR):
        (root / f"item_{i}.txt").write_text("x")
    (root / "note.md").write_text("not a match")   # a non-matching file at every level
    if depth == 0:
        return
    for d in range(DIRS_PER_LEVEL):
        sub = root / f"level{depth}_dir{d}"
        sub.mkdir()
        build_tree(sub, depth - 1)


def find_with_rglob(root: Path) -> list[str]:
    return sorted(str(p) for p in root.rglob("*.txt"))


def find_with_os_walk(root: Path) -> list[str]:
    matches = []
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in fnmatch.filter(filenames, "*.txt"):
            matches.append(os.path.join(dirpath, name))
    return sorted(matches)


def best_time(fn, root: Path) -> tuple[float, list[str]]:
    best = float("inf")
    result: list[str] = []
    for _ in range(REPEATS):
        start = time.perf_counter()
        result = fn(root)
        best = min(best, time.perf_counter() - start)
    return best, result


if __name__ == "__main__":
    tmp_dir = Path(tempfile.mkdtemp(prefix="pystdlib_pathlib_lvl06_"))

    try:
        build_tree(tmp_dir, DEPTH)

        # .glob (non-recursive) only ever sees the top level -- proving the
        # "not recursive by default" gotcha concretely before measuring anything
        top_level_only = sorted(str(p) for p in tmp_dir.glob("*.txt"))
        assert len(top_level_only) == FILES_PER_DIR

        rglob_time, rglob_result = best_time(find_with_rglob, tmp_dir)
        walk_time, walk_result = best_time(find_with_os_walk, tmp_dir)

        expected_count = FILES_PER_DIR * sum(DIRS_PER_LEVEL ** d for d in range(DEPTH + 1))
        assert len(rglob_result) == len(walk_result) == expected_count

        print(f"tree: depth={DEPTH}, {DIRS_PER_LEVEL} subdirs/level, {FILES_PER_DIR} matching files/dir")
        print(f"total matching files: {expected_count}, best of {REPEATS} runs")
        print(f"Path.rglob('*.txt')          : {rglob_time * 1000:.2f} ms")
        print(f"os.walk + fnmatch.filter     : {walk_time * 1000:.2f} ms")
        if walk_time > 0:
            print(f"ratio (rglob / os.walk): {rglob_time / walk_time:.2f}x")
        faster = "Path.rglob" if rglob_time < walk_time else "os.walk + fnmatch"
        print(f"-> on this run, {faster} was faster")

        # unconditional correctness: both approaches must find the identical
        # set of files, regardless of which one ran faster
        assert rglob_result == walk_result
        assert rglob_time > 0 and walk_time > 0

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
