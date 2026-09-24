"""
Topic 33: Concurrency Models & IPC

================================================================================
SOLUTION & WALKTHROUGH
================================================================================
"""

import multiprocessing
import time

# ============================================================================
# Inter-Process Communication (IPC) via Pipes
# ============================================================================

def worker_process(conn):
    """Runs in an entirely separate OS process, with its own GIL and memory."""
    print("[Worker] Waiting for message...")
    
    # Blocks until a message is received from the parent
    message = conn.recv()
    print(f"[Worker] Received from parent: '{message}'")
    
    print("[Worker] Doing heavy CPU work for 1 second...")
    # Because this is a separate process, time.sleep (or heavy math) here
    # does NOT block the main process.
    time.sleep(1)
    
    response = f"Processed '{message}' successfully!"
    print("[Worker] Sending response back to parent...")
    conn.send(response)
    
    conn.close()
    print("[Worker] Exiting.")

if __name__ == "__main__":
    print("--- Testing Multiprocessing IPC ---")
    
    # Create a bidirectional pipe. Returns two connection objects.
    parent_conn, child_conn = multiprocessing.Pipe()
    
    # Create the process, passing the child's end of the pipe as an argument
    p = multiprocessing.Process(target=worker_process, args=(child_conn,))
    
    # Start the process
    print("[Main] Starting worker process...")
    p.start()
    
    # Send data to the child
    print("[Main] Sending data to worker...")
    parent_conn.send("Hello from Main!")
    
    # Block and wait for the child's response
    print("[Main] Waiting for worker response...")
    response = parent_conn.recv()
    print(f"[Main] Received from worker: '{response}'")
    
    # Wait for the process to fully exit
    p.join()
    print("[Main] Process finished cleanly.")
