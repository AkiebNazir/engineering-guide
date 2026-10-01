"""
Topic 27: Asyncio Deep Dive (Event Loop, Contextvars, run_in_executor)

================================================================================
SOLUTION & WALKTHROUGH
================================================================================

This file contains the complete, idiomatic solution for the asyncio challenges.
"""

import asyncio
import time
import uuid
import contextvars
from concurrent.futures import ProcessPoolExecutor

# ============================================================================
# 1. ProcessPools for Blocking CPU Tasks
# ============================================================================
def heavy_computation(x: int) -> int:
    """A blocking, CPU-bound task."""
    print(f"[{time.strftime('%X')}] Starting heavy computation for {x}...")
    time.sleep(1)
    return x * x

# We create the executor globally (or manage it via a context manager)
# CPU bound tasks should use ProcessPoolExecutor.
# IO bound blocking tasks (like `requests.get`) should use ThreadPoolExecutor.
_executor = ProcessPoolExecutor(max_workers=4)

async def process_data(x: int) -> int:
    """
    Calls `heavy_computation(x)` safely without blocking the event loop.
    """
    loop = asyncio.get_running_loop()
    # By passing the executor, asyncio runs the blocking function in a separate
    # thread or process, returning an awaitable Future.
    result = await loop.run_in_executor(_executor, heavy_computation, x)
    return result

async def monitor_event_loop():
    """A background task to prove the event loop isn't blocked."""
    for _ in range(5):
        print(f"[{time.strftime('%X')}] Event loop is still spinning!")
        await asyncio.sleep(0.3)

# ============================================================================
# 2. ContextVars for Implicit State
# ============================================================================
# ContextVars allow us to store state that is local to an asyncio Task.
# This is the async equivalent of threading.local().
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar('request_id_var', default='N/A')

def log(msg: str):
    """Reads the context var without needing it passed as an argument."""
    req_id = request_id_var.get()
    print(f"[{req_id}] {msg}")

async def do_work():
    """Does some work, calling log() deep down the call stack."""
    await asyncio.sleep(0.1)
    log("Work started")
    await asyncio.sleep(0.1)
    log("Work finished")

async def handle_request(req_id: str):
    """
    Sets the context var. Any coroutine spawned within this task (or awaited)
    will inherit this context var value.
    """
    # .set() returns a Token which can be used to reset() the value if needed.
    request_id_var.set(req_id)
    log("Handling new request")
    await do_work()

async def main():
    print("--- Testing run_in_executor ---")
    # We run the background monitor and 3 heavy computations concurrently.
    # Because we use run_in_executor, the monitor will continue to print while
    # the heavy computations are running in other processes!
    await asyncio.gather(
        monitor_event_loop(),
        process_data(10),
        process_data(20),
        process_data(30),
    )
    
    print("\n--- Testing ContextVars ---")
    # We handle 3 requests concurrently. Each has its own context var isolation.
    await asyncio.gather(
        handle_request("req-1234"),
        handle_request("req-5678"),
        handle_request("req-9abc"),
    )
    
    _executor.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
