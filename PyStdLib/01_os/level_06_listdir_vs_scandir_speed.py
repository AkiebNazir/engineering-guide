"""
LEVEL 06 (advanced) - MEASURED: os.listdir+stat vs os.scandir
=================================================================
You will learn
  * how to time filesystem code honestly with time.perf_counter()
  * that os.listdir() gives you names only -- getting each size costs a
    SEPARATE os.stat() syscall per file
  * that os.scandir()'s DirEntry objects typically cache that info from the
    directory read itself, avoiding the extra syscall
  * this file prints REAL numbers from THIS run -- it does not assume which
    approach wins, it measures and reports whatever actually happened

Run: python level_06_listdir_vs_scandir_speed.py
"""
import os
import shutil
import tempfile
import time

FILE_COUNT = 3000
REPEATS = 5   # take the best of several runs to reduce noise from OS caching


def total_size_via_listdir(directory: str) -> int:
    total = 0
    for name in os.listdir(directory):
        total += os.stat(os.path.join(directory, name)).st_size   # extra syscall per file
    return total


def total_size_via_scandir(directory: str) -> int:
    total = 0
    with os.scandir(directory) as entries:
        for entry in entries:
            total += entry.stat().st_size   # often served from the readdir buffer, no extra syscall
    return total


def best_time(fn, directory: str) -> tuple[float, int]:
    best = float("inf")
    result = -1
    for _ in range(REPEATS):
        start = time.perf_counter()
        result = fn(directory)
        best = min(best, time.perf_counter() - start)
    return best, result


if __name__ == "__main__":
    tmp_dir = tempfile.mkdtemp(prefix="pystdlib_os_lvl06_")

    try:
        for i in range(FILE_COUNT):
            with open(os.path.join(tmp_dir, f"file_{i}.txt"), "w") as f:
                f.write(str(i))

        listdir_time, listdir_total = best_time(total_size_via_listdir, tmp_dir)
        scandir_time, scandir_total = best_time(total_size_via_scandir, tmp_dir)

        print(f"files: {FILE_COUNT}, best of {REPEATS} runs")
        print(f"os.listdir()+os.stat(): {listdir_time * 1000:.2f} ms  (total size={listdir_total})")
        print(f"os.scandir()          : {scandir_time * 1000:.2f} ms  (total size={scandir_total})")
        if scandir_time > 0:
            print(f"ratio (listdir / scandir): {listdir_time / scandir_time:.2f}x")
        faster = "scandir" if scandir_time < listdir_time else "listdir+stat"
        print(f"-> on this run, {faster} was faster")

        # Correctness is what we assert unconditionally: both approaches must
        # compute the exact same total size over the exact same files. Each
        # file_i.txt holds str(i), so its size is len(str(i)) bytes, not i.
        expected_total = sum(len(str(i)) for i in range(FILE_COUNT))
        assert listdir_total == scandir_total == expected_total

        # We do NOT hard-assert "scandir is always faster" -- that is a claim
        # about performance, and this repo's rule is to only assert what THIS
        # run actually measured. Both numbers must simply be real, positive
        # durations, which is the only unconditional performance fact here.
        assert listdir_time > 0 and scandir_time > 0

        print("OK")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
