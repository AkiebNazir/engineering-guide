"""
Topic 34: The GIL & Subinterpreters

================================================================================
EXPLANATION
================================================================================

The Global Interpreter Lock (GIL) is a mutex that protects access to Python
objects, preventing multiple threads from executing Python bytecodes at once.
This is why `threading` in Python doesn't provide true parallelism for CPU-bound tasks.

However, starting in Python 3.12 (PEP 684), Python introduced Per-Interpreter GILs.
Using the `_xxsubinterpreters` module (which will become public in the future),
we can spawn subinterpreters in the same process that DO NOT share a GIL, 
achieving true multi-core parallelism without the overhead of `multiprocessing`.

---
DIAGRAM: The GIL vs Subinterpreters
---
```mermaid
graph TD
    subgraph Single Interpreter (Pre-3.12)
        A[The GIL]
        A --- B[Thread 1]
        A --- C[Thread 2]
    end

    subgraph Per-Interpreter GILs (3.12+)
        D[Interpreter 1] --- E[GIL 1] --- F[Thread 1]
        G[Interpreter 2] --- H[GIL 2] --- I[Thread 2]
    end
```

================================================================================
YOUR TASK
================================================================================
Since `_xxsubinterpreters` is highly experimental and C-API dependent, we will
instead write a mock demonstration of how to release the GIL using `ctypes`
in a C-extension context.

1. Create a Python function `sleep_with_gil` that uses `time.sleep()`.
2. (Mental Exercise): Understand that when a C extension (like `time.sleep`, or
   a heavy numpy operation) is called, it drops the GIL using `Py_BEGIN_ALLOW_THREADS`.
"""

import time
import threading

# ============================================================================
# Releasing the GIL
# ============================================================================

def cpu_bound_task(name: str):
    """
    TODO: Simulate a CPU bound task. Write a busy-wait loop that runs for
    20 million iterations.
    """
    pass

def io_bound_task(name: str):
    """
    TODO: Simulate an IO bound task. Use time.sleep(0.5).
    time.sleep is written in C and explicitly releases the GIL!
    """
    pass

if __name__ == "__main__":
    print("Run the solution file to see the working implementation!")
