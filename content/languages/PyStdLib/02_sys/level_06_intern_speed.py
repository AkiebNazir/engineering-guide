"""
LEVEL 06 (advanced) - MEASURED: sys.intern() and string comparison speed
============================================================================
You will learn
  * sys.intern() makes equal strings share exactly one object in memory
  * CPython's string equality has a fast path: if two operands are the SAME
    object (identity), it skips the character-by-character comparison
  * this file actually measures many repeated `==` comparisons on interned
    vs non-interned (but content-equal) strings, and prints THIS run's numbers
  * this repo's rule: report what was actually measured, even if it surprises

Run: python level_06_intern_speed.py
"""
import sys
import time

ITERATIONS = 2_000_000
STRING_LENGTH = 4000


def build_distinct_equal_strings(length: int) -> tuple[str, str]:
    """Two strings with IDENTICAL content but guaranteed to be different
    objects (built via str.join at runtime, never coalesced by the compiler
    the way two identical literals in the same file sometimes are)."""
    a = "".join(["q"] * length)
    b = "".join(["q"] * length)
    assert a == b and a is not b
    return a, b


def time_equality_checks(a: str, b: str, iterations: int) -> float:
    start = time.perf_counter()
    for _ in range(iterations):
        _ = a == b
    return time.perf_counter() - start


if __name__ == "__main__":
    non_interned_a, non_interned_b = build_distinct_equal_strings(STRING_LENGTH)
    assert non_interned_a is not non_interned_b

    interned_a = sys.intern(non_interned_a)
    interned_b = sys.intern(non_interned_b)
    # after interning both, they now point at the SAME object
    assert interned_a is interned_b

    # warm up (avoid first-call overhead skewing the measurement)
    time_equality_checks(non_interned_a, non_interned_b, 10_000)
    time_equality_checks(interned_a, interned_b, 10_000)

    non_interned_time = time_equality_checks(non_interned_a, non_interned_b, ITERATIONS)
    interned_time = time_equality_checks(interned_a, interned_b, ITERATIONS)

    print(f"{ITERATIONS:,} equality checks on {STRING_LENGTH}-char strings:")
    print(f"  non-interned (distinct objects, equal content): {non_interned_time * 1000:.1f} ms")
    print(f"  interned (same object after sys.intern)        : {interned_time * 1000:.1f} ms")
    if interned_time > 0:
        print(f"  ratio (non-interned / interned): {non_interned_time / interned_time:.2f}x")
    faster = "interned (identity fast-path)" if interned_time < non_interned_time else "non-interned"
    print(f"-> on this run, {faster} comparisons were faster")

    # Unconditional facts we can actually prove, regardless of which was
    # faster on this machine/run: interning really does unify identity,
    # and both measurements are real, positive durations.
    assert interned_a is interned_b
    assert non_interned_a == non_interned_b == interned_a
    assert non_interned_time > 0 and interned_time > 0

    print("OK")
