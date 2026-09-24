"""
Topic 27: Asyncio Deep Dive (Event Loop, Contextvars, run_in_executor)

================================================================================
EXPLANATION
================================================================================

A senior Python engineer knows that simply sprinkling `async` and `await`
everywhere is a recipe for disaster. Asyncio is single-threaded (cooperative
multitasking). If one coroutine blocks (e.g., waiting for an API response
without using an async library, or doing heavy CPU work), the entire event
loop freezes.

In this lesson, we will cover three advanced concepts:
1. Identifying and mitigating blocking calls using `run_in_executor`.
2. Utilizing `contextvars` to maintain state (like request IDs) across
   concurrently executing coroutines, without passing them down explicitly.
3. Managing Event Loop lifecycles safely.

---
DIAGRAM: Cooperative Multitasking vs Thread Pools
---
```mermaid
graph TD
    subgraph Asyncio Event Loop
        A[Event Loop Thread]
        A -->|Execute| B(Coroutine 1)
        A -->|Execute| C(Coroutine 2)
        A -.->|Oops! Blocked on| D(Blocking CPU/IO Task)
        D -.-x|Freezes| A
    end

    subgraph Thread Pool Executor
        E[Worker Thread 1]
        F[Worker Thread 2]
    end

    A -->|run_in_executor| E
    E -->|Returns Result| A
```

================================================================================
YOUR TASK
================================================================================
1. We have a CPU-intensive function `heavy_computation`. You need to integrate
   it into an async workflow `process_data` WITHOUT blocking the event loop.
2. We have a web-like setup where multiple requests come in concurrently. We want
   to attach a unique `request_id` to each log message. Implement this using
   the `contextvars` module so that we don't have to pass `request_id` explicitly
   to every logging function.
"""

import asyncio
import time
import uuid
import contextvars
from concurrent.futures import ProcessPoolExecutor

# ============================================================================
# 1. ThreadPools / ProcessPools for Blocking Tasks
# ============================================================================
def heavy_computation(x: int) -> int:
    """A blocking, CPU-bound task. DO NOT CHANGE THIS FUNCTION."""
    # Simulate heavy work
    time.sleep(1)
    return x * x

async def process_data(x: int) -> int:
    """
    TODO: Call `heavy_computation(x)` safely without blocking the event loop.
    Hint: Use asyncio.get_running_loop() and loop.run_in_executor().
    Since this is CPU bound, a ProcessPoolExecutor is better than ThreadPool.
    """
    pass

# ============================================================================
# 2. ContextVars for Implicit State
# ============================================================================
# TODO: Define a ContextVar named 'request_id_var' with a default of 'N/A'
request_id_var: contextvars.ContextVar[str] = None # type: ignore

def log(msg: str):
    """
    TODO: Read the current request ID from request_id_var and print the message.
    Format: [req-id] msg
    """
    pass

async def handle_request(req_id: str):
    """
    TODO: Set the request_id_var to the provided req_id for the current context.
    Then call `do_work()` which will eventually call `log()`.
    """
    pass

async def do_work():
    # Simulate some async work
    await asyncio.sleep(0.1)
    log("Work started")
    await asyncio.sleep(0.1)
    log("Work finished")

if __name__ == "__main__":
    print("Run the solution file to see the working implementation!")
