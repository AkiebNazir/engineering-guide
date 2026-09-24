"""
LEVEL 06 (advanced) - MEASURED: process-per-item vs one batch process
========================================================================
You will learn
  * spawning a new OS process has real, measurable overhead
  * this run's ACTUAL timing, via time.perf_counter(), comparing "one
    subprocess per unit of work" against "one subprocess doing all the
    work internally, in a loop"
  * the numbers below are printed honestly from THIS run -- not a claimed
    ratio -- though process-spawn overhead dominating small tasks is one
    of the more reliably reproducible measurements in this whole module

Run: python level_06_measured_spawn_overhead.py
"""
import subprocess
import sys
import time

N = 15  # keep this small: it's the per-item approach that's expensive


def compute_squares_one_process_per_item(n: int) -> list[int]:
    results = []
    for i in range(n):
        result = subprocess.run(
            [sys.executable, "-c", f"print({i} * {i})"],
            capture_output=True,
            text=True,
        )
        results.append(int(result.stdout.strip()))
    return results


def compute_squares_one_batch_process(n: int) -> list[int]:
    code = f"print(' '.join(str(i * i) for i in range({n})))"
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    return [int(x) for x in result.stdout.split()]


def main() -> None:
    expected = [i * i for i in range(N)]

    start = time.perf_counter()
    per_item_result = compute_squares_one_process_per_item(N)
    per_item_seconds = time.perf_counter() - start

    start = time.perf_counter()
    batch_result = compute_squares_one_batch_process(N)
    batch_seconds = time.perf_counter() - start

    assert per_item_result == expected
    assert batch_result == expected

    print(f"computing {N} squares:")
    print(f"  {N} processes (one per item): {per_item_seconds * 1000:.2f} ms")
    print(f"  1 process (batch loop):       {batch_seconds * 1000:.2f} ms")
    if batch_seconds > 0:
        print(f"  measured ratio: {per_item_seconds / batch_seconds:.1f}x slower per-item")

    # --- the real, measured claim -------------------------------------------
    # Spawning N processes must cost at least as much as spawning 1, for the
    # SAME unit of work each -- process creation overhead does not disappear.
    # We assert the measured direction from this run, matching the honest
    # numbers printed above (not a hard-coded ratio).
    assert per_item_seconds >= batch_seconds, (
        "spawning one process per item was NOT slower than one batch process "
        "in this run -- reporting the surprise rather than assuming it"
    )

    print("OK")


if __name__ == "__main__":
    main()
