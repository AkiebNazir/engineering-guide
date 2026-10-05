"""
LEVEL 06 (advanced) - measured: buffering=0 vs default (-1) for many small writes
===================================================================================
You will learn
  * buffering=0 (binary only) means every write() is a real, unbuffered syscall
  * buffering=-1 (the default) batches writes through an internal buffer
  * how to measure this honestly with time.perf_counter() instead of assuming

Run: python level_06_buffering_measured.py
"""
import os
import shutil
import tempfile
import time

WRITE_COUNT = 20_000
CHUNK = b"x"


def write_many(path: str, buffering: int) -> float:
    start = time.perf_counter()
    with open(path, "wb", buffering=buffering) as f:
        for _ in range(WRITE_COUNT):
            f.write(CHUNK)
    return time.perf_counter() - start


def main() -> None:
    tmpdir = tempfile.mkdtemp()
    try:
        unbuffered_path = os.path.join(tmpdir, "unbuffered.bin")
        buffered_path = os.path.join(tmpdir, "buffered.bin")

        # buffering=0 is a binary-only concept -- text mode rejects it outright.
        try:
            open(os.path.join(tmpdir, "x.txt"), "w", encoding="utf-8", buffering=0)
            raise AssertionError("expected ValueError for unbuffered text mode")
        except ValueError:
            pass

        unbuffered_time = write_many(unbuffered_path, buffering=0)
        buffered_time = write_many(buffered_path, buffering=-1)

        print(f"{WRITE_COUNT} single-byte writes, buffering=0  (unbuffered): {unbuffered_time:.4f}s")
        print(f"{WRITE_COUNT} single-byte writes, buffering=-1 (default):    {buffered_time:.4f}s")
        if buffered_time > 0:
            print(f"unbuffered was {unbuffered_time / buffered_time:.1f}x the time of buffered")

        # Both produce identical file content -- buffering changes speed, not correctness.
        with open(unbuffered_path, "rb") as f:
            unbuffered_content = f.read()
        with open(buffered_path, "rb") as f:
            buffered_content = f.read()
        assert unbuffered_content == buffered_content == CHUNK * WRITE_COUNT

        # This is the real, measured claim this module makes -- report it as it came out,
        # not as intuition says it "should" be.
        assert unbuffered_time > 0 and buffered_time > 0
        assert unbuffered_time >= buffered_time, (
            f"unexpected: unbuffered ({unbuffered_time:.4f}s) was not slower than "
            f"buffered ({buffered_time:.4f}s) on this run"
        )
    finally:
        shutil.rmtree(tmpdir)

    print("OK")


if __name__ == "__main__":
    main()
