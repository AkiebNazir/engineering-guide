"""
Topic 33: Concurrency Models & IPC

================================================================================
EXPLANATION
================================================================================

Python offers three distinct concurrency models:
1. `asyncio`: Cooperative multitasking in a single thread (best for high-volume Network I/O).
2. `threading`: Preemptive OS threads (best for blocking I/O like file reads or requests.get).
3. `multiprocessing`: True parallel OS processes, bypassing the GIL (best for CPU bound work).

Because `multiprocessing` spawns entirely separate memory spaces, sharing state
between processes requires Inter-Process Communication (IPC) like Pipes, Queues,
or shared memory Managers.

---
DIAGRAM: Multiprocessing IPC (Pipes)
---
```mermaid
graph LR
    A[Main Process] -- "pipe_parent.send()" --> B((Pipe))
    B -- "pipe_child.recv()" --> C[Worker Process]
```

================================================================================
YOUR TASK
================================================================================
1. Create a worker function that takes a multiprocessing Pipe connection.
2. In the main block, create a Pipe, spawn a `multiprocessing.Process`, and
   send a message to the worker. Receive the worker's response and print it.
"""

import multiprocessing
import time

# ============================================================================
# Inter-Process Communication (IPC) via Pipes
# ============================================================================

def worker_process(conn):
    """
    TODO: 
    1. Receive a message from the connection using conn.recv().
    2. Print the received message.
    3. Simulate 1 second of heavy CPU work.
    4. Send a response back using conn.send().
    5. Close the connection.
    """
    pass

if __name__ == "__main__":
    print("Run the solution file to see the working implementation!")
