"""
LEVEL 06 (advanced) - MEASURED: itertools.chain vs repeated list concatenation
==================================================================================
You will learn
  * repeatedly doing big_list = big_list + chunk copies the ENTIRE list every time -> O(n^2)
  * itertools.chain never copies -- it just remembers where to look next -> O(n) to consume
  * both measured with time.perf_counter() on THIS run

Run: python level_06_chain_vs_concat_timing.py
"""
import time
from itertools import chain

NUM_CHUNKS = 400
CHUNK_SIZE = 200


def make_chunks():
    return [list(range(CHUNK_SIZE)) for _ in range(NUM_CHUNKS)]


def time_concat_then_sum(chunks: list[list[int]]) -> float:
    start = time.perf_counter()
    combined: list[int] = []
    for chunk in chunks:
        combined = combined + chunk   # rebuilds the WHOLE list every iteration
    total = sum(combined)
    elapsed = time.perf_counter() - start
    assert total == NUM_CHUNKS * sum(range(CHUNK_SIZE))
    return elapsed


def time_chain_then_sum(chunks: list[list[int]]) -> float:
    start = time.perf_counter()
    total = sum(chain.from_iterable(chunks))   # streams through every element once, no copies
    elapsed = time.perf_counter() - start
    assert total == NUM_CHUNKS * sum(range(CHUNK_SIZE))
    return elapsed


if __name__ == "__main__":
    chunks = make_chunks()
    concat_time = time_concat_then_sum(chunks)
    chain_time = time_chain_then_sum(chunks)

    print(f"repeated '+' concatenation ({NUM_CHUNKS} chunks of {CHUNK_SIZE}): {concat_time*1000:.2f} ms")
    print(f"itertools.chain.from_iterable                       : {chain_time*1000:.2f} ms")
    print(f"speedup: {concat_time / chain_time:,.1f}x")

    # This is a real measurement of THIS run. Repeated '+' concatenation is
    # O(n^2) in the total element count because each '+' copies everything
    # accumulated so far; chain.from_iterable is O(n) since it never copies.
    assert chain_time < concat_time
    assert concat_time / chain_time > 2   # conservative floor; real gap is usually much larger

    print("OK")
