"""
LEVEL 06 (advanced) - MEASURED speedup from lru_cache on recursive fib
=========================================================================
You will learn
  * a naive recursive Fibonacci recomputes the same sub-calls exponentially
    many times; @lru_cache turns it into linear time by memoizing
  * cache_info() reports real hits/misses -- not an estimate
  * this run's ACTUAL wall-clock numbers via time.perf_counter(), printed
    honestly (this repo's rule: report what was measured, not what "should"
    be true)

Run: python level_06_measured_cache_speedup.py
"""
import time
from functools import lru_cache


def fib_uncached(n: int) -> int:
    if n < 2:
        return n
    return fib_uncached(n - 1) + fib_uncached(n - 2)


@lru_cache(maxsize=None)
def fib_cached(n: int) -> int:
    if n < 2:
        return n
    return fib_cached(n - 1) + fib_cached(n - 2)


def main() -> None:
    n = 30  # big enough for a real, visible gap; small enough to stay fast

    # --- time the uncached version -----------------------------------------
    start = time.perf_counter()
    uncached_result = fib_uncached(n)
    uncached_seconds = time.perf_counter() - start

    # --- time the cached version (cold cache first) -------------------------
    fib_cached.cache_clear()
    start = time.perf_counter()
    cached_result = fib_cached(n)
    cached_seconds = time.perf_counter() - start

    assert uncached_result == cached_result  # both compute the same value
    assert uncached_result == 832040  # fib(30), known constant, sanity check

    print(f"fib({n}) uncached: {uncached_seconds * 1000:.3f} ms")
    print(f"fib({n}) cached (cold):  {cached_seconds * 1000:.3f} ms")

    # --- cache_info gives real hit/miss counts -----------------------------
    info_after_cold_run = fib_cached.cache_info()
    # A cold run of fib_cached(30) computes each distinct n in 0..30 exactly
    # once -> n+1 misses. But the recursive calls also naturally re-request
    # already-solved sub-problems along the way (fib(28) is asked for both
    # from fib(29) and from fib(30)'s side of the tree) -> real cache hits
    # happen even within this single top-level call, not just across calls.
    assert info_after_cold_run.misses == n + 1
    print(f"cache hits/misses within the single cold call: "
          f"{info_after_cold_run.hits}/{info_after_cold_run.misses}")
    assert info_after_cold_run.hits > 0  # real, measured: hits occur even on the first call

    # --- calling again hits the warm cache entirely -------------------------
    start = time.perf_counter()
    warm_result = fib_cached(n)
    warm_seconds = time.perf_counter() - start
    print(f"fib({n}) cached (warm):  {warm_seconds * 1000:.5f} ms")

    assert warm_result == uncached_result
    info_after_warm_call = fib_cached.cache_info()
    assert info_after_warm_call.hits == info_after_cold_run.hits + 1  # exactly one new hit
    assert info_after_warm_call.misses == n + 1  # no new misses

    # --- the actual, measured claim: caching is dramatically faster here --
    # We assert the DIRECTION (cached beats uncached), which is guaranteed
    # by the algorithmic difference (O(2^n) vs O(n)); the exact ratio is
    # whatever this run measured, printed above rather than hard-coded.
    assert cached_seconds < uncached_seconds
    speedup = uncached_seconds / cached_seconds if cached_seconds > 0 else float("inf")
    print(f"measured speedup (cold cache): {speedup:.1f}x")

    print("OK")


if __name__ == "__main__":
    main()
