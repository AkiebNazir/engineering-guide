"""
Topic 34: The GIL & Subinterpreters

================================================================================
SOLUTION & WALKTHROUGH
================================================================================
"""

import time
import threading

# ============================================================================
# Releasing the GIL
# ============================================================================

def cpu_bound_task(name: str):
    """
    A purely Python CPU-bound task.
    Because it only executes Python bytecode, it holds the GIL the entire time.
    If you run two of these in threads, they will NOT run in parallel.
    """
    print(f"[{name}] Starting CPU bound task...")
    count = 0
    for _ in range(20_000_000):
        count += 1
    print(f"[{name}] Finished CPU bound task.")

def io_bound_task(name: str):
    """
    An I/O bound task using time.sleep.
    Under the hood, the C implementation of time.sleep calls Py_BEGIN_ALLOW_THREADS,
    releasing the GIL, sleeping, and then reacquiring it.
    If you run two of these in threads, they WILL run in parallel!
    """
    print(f"[{name}] Starting IO bound task (releasing GIL)...")
    time.sleep(0.5)
    print(f"[{name}] Finished IO bound task.")

def run_in_threads(target):
    start = time.time()
    t1 = threading.Thread(target=target, args=("Thread-1",))
    t2 = threading.Thread(target=target, args=("Thread-2",))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    print(f"Total time: {time.time() - start:.2f} seconds\n")

if __name__ == "__main__":
    print("--- Testing CPU Bound (Held GIL) ---")
    # This will take roughly 2x the time of a single run because Thread 1 and
    # Thread 2 have to constantly fight for the GIL and take turns.
    run_in_threads(cpu_bound_task)
    
    print("--- Testing I/O Bound (Released GIL) ---")
    # This will take exactly 0.5 seconds because both threads release the GIL
    # and sleep concurrently in the OS.
    run_in_threads(io_bound_task)
