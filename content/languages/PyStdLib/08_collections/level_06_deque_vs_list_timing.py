"""
LEVEL 06 (advanced) - MEASURED: deque.popleft() vs list.pop(0)
==================================================================
You will learn
  * list.pop(0) must shift every remaining element left -> O(n) per call
  * deque.popleft() is O(1) regardless of size, since deque is a block-linked structure
  * both measured with time.perf_counter() on THIS run, not asserted from memory

Run: python level_06_deque_vs_list_timing.py
"""
import time
from collections import deque

N = 20_000


def time_list_pop_front(n: int) -> float:
    data = list(range(n))
    start = time.perf_counter()
    while data:
        data.pop(0)   # O(n): every remaining element shifts left by one
    return time.perf_counter() - start


def time_deque_popleft(n: int) -> float:
    data = deque(range(n))
    start = time.perf_counter()
    while data:
        data.popleft()   # O(1): no shifting, just moves an internal pointer
    return time.perf_counter() - start


if __name__ == "__main__":
    list_time = time_list_pop_front(N)
    deque_time = time_deque_popleft(N)

    print(f"list.pop(0)      x{N}: {list_time*1000:.2f} ms")
    print(f"deque.popleft()  x{N}: {deque_time*1000:.2f} ms")
    print(f"speedup: {list_time / deque_time:,.1f}x")

    # This is a real measurement of THIS run, not a hardcoded expectation.
    # list.pop(0) repeated N times is O(n^2) total; deque.popleft() is O(n) total.
    # The gap is large and grows with N, but we only assert the direction and a
    # conservative margin so this holds on slow CI machines too.
    assert deque_time < list_time
    assert list_time / deque_time > 5   # conservative: real speedup is usually 10x-100x+ at this N

    print("OK")
