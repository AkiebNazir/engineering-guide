"""
LEVEL 06 (advanced) - MEASURED: @contextmanager generator vs hand-written class
====================================================================================
You will learn
  * the exact same context manager written two ways: @contextmanager generator,
    and a class with __enter__/__exit__
  * both are asserted to behave identically (enter value, exit-on-exception)
  * the per-use overhead of each is measured with time.perf_counter() on THIS run
  * the numbers below are whatever this run actually produced -- not assumed

Run: python level_06_generator_vs_class.py
"""
import time
from contextlib import contextmanager


EVENTS: list[str] = []


# ---- version A: generator-based, via @contextmanager -----------------------
@contextmanager
def timer_cm_generator(label: str):
    EVENTS.append(f"enter:{label}")
    try:
        yield label
    finally:
        EVENTS.append(f"exit:{label}")


# ---- version B: hand-written class, doing the identical job ----------------
class TimerCMClass:
    def __init__(self, label: str):
        self.label = label

    def __enter__(self):
        EVENTS.append(f"enter:{self.label}")
        return self.label

    def __exit__(self, exc_type, exc_val, exc_tb):
        EVENTS.append(f"exit:{self.label}")
        return False   # never suppress exceptions


if __name__ == "__main__":
    # ---- both produce identical enter/exit behavior on the happy path -----
    EVENTS.clear()
    with timer_cm_generator("A") as value_a:
        assert value_a == "A"
    with TimerCMClass("B") as value_b:
        assert value_b == "B"
    assert EVENTS == ["enter:A", "exit:A", "enter:B", "exit:B"]

    # ---- both propagate exceptions identically, cleanup still runs --------
    EVENTS.clear()
    for label, cm_factory in (("gen", lambda: timer_cm_generator("gen")),
                               ("cls", lambda: TimerCMClass("cls"))):
        raised = None
        try:
            with cm_factory():
                raise ValueError("boom")
        except ValueError as e:
            raised = e
        assert raised is not None
    assert EVENTS == ["enter:gen", "exit:gen", "enter:cls", "exit:cls"]

    # ---- now measure real per-use overhead of each approach ----------------
    N = 200_000

    start = time.perf_counter()
    for i in range(N):
        with timer_cm_generator(i):
            pass
    generator_elapsed = time.perf_counter() - start

    start = time.perf_counter()
    for i in range(N):
        with TimerCMClass(i):
            pass
    class_elapsed = time.perf_counter() - start

    print(f"{N} enter/exit cycles each:")
    print(f"  @contextmanager generator : {generator_elapsed:.4f}s ({generator_elapsed / N * 1e9:.1f} ns/use)")
    print(f"  hand-written class        : {class_elapsed:.4f}s ({class_elapsed / N * 1e9:.1f} ns/use)")

    # ---- report what THIS run measured, without assuming the direction ----
    assert generator_elapsed >= 0.0 and class_elapsed >= 0.0
    slower = "@contextmanager generator" if generator_elapsed > class_elapsed else "hand-written class"
    ratio = max(generator_elapsed, class_elapsed) / max(min(generator_elapsed, class_elapsed), 1e-9)
    print(f"  measured slower on this run: {slower} (~{ratio:.2f}x)")
    # We do NOT assert which one wins -- @contextmanager wraps a generator, which
    # carries some real overhead, but exactly how much varies by interpreter and
    # machine. The honest result is whatever was printed above.

    print("OK")
