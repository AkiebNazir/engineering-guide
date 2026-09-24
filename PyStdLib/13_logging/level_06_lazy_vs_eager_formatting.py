"""
LEVEL 06 (advanced) - MEASURED: isEnabledFor() guards vs "lazy" %-args
=========================================================================
You will learn
  * a common belief: logger.debug("%s", expensive()) skips expensive() when DEBUG
    is disabled. This is FALSE -- Python evaluates call arguments BEFORE the call,
    so expensive() runs regardless of the logger's level
  * logger.isEnabledFor(level) is what actually lets you skip the expensive work
  * this is measured with time.perf_counter() on THIS run -- not asserted from theory
  * the numbers below are whatever this run actually produced

Run: python level_06_lazy_vs_eager_formatting.py
"""
import io
import logging
import time


CALLS = {"count": 0}


def expensive_computation() -> str:
    """Simulates real cost: building a string nobody will ever see when the
    logger is set above DEBUG."""
    CALLS["count"] += 1
    return "-".join(str(i * i) for i in range(200))


if __name__ == "__main__":
    stream = io.StringIO()
    logger = logging.getLogger("level06.perf")
    logger.handlers.clear()
    logger.propagate = False
    logger.addHandler(logging.StreamHandler(stream))
    logger.setLevel(logging.WARNING)      # DEBUG is disabled

    N = 20_000

    # ---- the common belief: "%s + args" is lazy -- it is NOT ----------------
    # expensive_computation() is a plain function-call ARGUMENT to logger.debug().
    # Python must evaluate every argument before it can even call logger.debug(),
    # so this runs expensive_computation() N times no matter the logger's level.
    CALLS["count"] = 0
    start = time.perf_counter()
    for _ in range(N):
        logger.debug("value=%s", expensive_computation())
    naive_elapsed = time.perf_counter() - start
    naive_calls = CALLS["count"]
    assert naive_calls == N   # proves the "it's lazy" belief wrong: it still ran every time

    # ---- what actually skips the work: isEnabledFor() as an explicit guard --
    CALLS["count"] = 0
    start = time.perf_counter()
    for _ in range(N):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("value=%s", expensive_computation())
    guarded_elapsed = time.perf_counter() - start
    guarded_calls = CALLS["count"]
    assert guarded_calls == 0   # the guard clause skipped the call entirely

    print(f"DEBUG disabled, {N} calls each:")
    print(f"  bare %-style args      : {naive_elapsed:.4f}s, expensive_computation() ran {naive_calls} times")
    print(f"  isEnabledFor()-guarded : {guarded_elapsed:.4f}s, expensive_computation() ran {guarded_calls} times")

    # ---- measured claim: report what THIS run found, don't assume ----------
    assert naive_elapsed >= 0.0
    assert guarded_elapsed >= 0.0
    faster = "isEnabledFor()-guarded" if guarded_elapsed < naive_elapsed else "bare %-style args"
    print(f"  measured faster on this run: {faster}")
    # the guard avoids 20_000 real string-building calls, so it should measure
    # faster on essentially any machine -- but we print the real numbers above
    # rather than hardcoding an assumption about the gap's size.
    assert guarded_elapsed < naive_elapsed, "guarding skipped real work and should measure faster"

    # ---- once the level is actually enabled, both approaches do equal work --
    logger.setLevel(logging.DEBUG)
    CALLS["count"] = 0
    for _ in range(10):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("value=%s", expensive_computation())
    assert CALLS["count"] == 10   # the guard is a no-op once DEBUG is actually enabled

    print("OK")
