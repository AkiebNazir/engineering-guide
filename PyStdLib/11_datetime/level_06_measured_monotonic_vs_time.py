"""
LEVEL 06 (advanced) - MEASURED: time.monotonic() vs time.time() for elapsed duration
========================================================================================
You will learn
  * time.time() reports wall-clock time, which the OS can step forward or
    backward (NTP sync, manual adjustment) -- unsafe for measuring elapsed durations
  * time.monotonic() is guaranteed non-decreasing, making it the correct
    choice for "how long did this take"
  * this run's ACTUAL measured elapsed times for a short sleep, from both
    clocks, printed honestly rather than assumed identical

Run: python level_06_measured_monotonic_vs_time.py
"""
import time


def main() -> None:
    sleep_seconds = 0.05  # keep the demo fast

    # --- measure the SAME sleep with both clocks -----------------------------
    wall_start = time.time()
    mono_start = time.monotonic()

    time.sleep(sleep_seconds)

    wall_end = time.time()
    mono_end = time.monotonic()

    wall_elapsed = wall_end - wall_start
    mono_elapsed = mono_end - mono_start

    print(f"requested sleep:  {sleep_seconds * 1000:.1f} ms")
    print(f"time.time() elapsed:      {wall_elapsed * 1000:.2f} ms")
    print(f"time.monotonic() elapsed: {mono_elapsed * 1000:.2f} ms")

    # --- under normal conditions (no clock step during this run), both -----
    # clocks measured elapsed time close to the requested sleep. We assert
    # the ACTUAL measured relationship: both are within a generous tolerance
    # of the requested duration, and both are non-negative (they moved
    # forward), not a hard-coded exact number.
    assert wall_elapsed >= 0
    assert mono_elapsed >= 0
    assert wall_elapsed >= sleep_seconds * 0.5  # slept at least roughly as long
    assert mono_elapsed >= sleep_seconds * 0.5

    # --- monotonic() is, BY DOCUMENTED GUARANTEE, non-decreasing -------------
    # We demonstrate this with many rapid back-to-back reads: every next
    # reading must be >= the previous one. time.time() carries no such
    # guarantee (though it will typically also be monotonic on a quiet
    # machine with no clock adjustment happening -- the CONTRACT is what
    # differs, not necessarily what you observe in one short run).
    readings = [time.monotonic() for _ in range(1000)]
    assert all(b >= a for a, b in zip(readings, readings[1:])), (
        "time.monotonic() must never go backwards"
    )

    # --- why this matters: a wall-clock step would corrupt a duration --------
    # We SIMULATE a clock step (we cannot actually change the system clock
    # here) to show the failure mode a real NTP adjustment would cause.
    simulated_wall_before = 1000.0
    simulated_wall_after_ntp_stepped_back = 998.5  # clock jumped back 1.5s
    simulated_bad_duration = simulated_wall_after_ntp_stepped_back - simulated_wall_before
    assert simulated_bad_duration < 0, "a stepped-back wall clock yields a negative duration"

    simulated_mono_before = 500.0
    simulated_mono_after = 501.5  # monotonic clocks cannot step backward
    simulated_good_duration = simulated_mono_after - simulated_mono_before
    assert simulated_good_duration >= 0

    print("OK")


if __name__ == "__main__":
    main()
