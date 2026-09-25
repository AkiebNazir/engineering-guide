"""
15 · Rate Limiter
=================

WHAT WE'RE BUILDING
--------------------
A Token Bucket or Leaky Bucket rate limiter implemented in Python, using threading
locks (or asyncio locks) to remain thread-safe.

WHY THIS MATTERS
----------------
Before distributing a rate limiter to Redis, you must understand how to build one
in memory. This protects your endpoints from being overwhelmed by burst traffic.
"""

import time
import threading

class TokenBucket:
    def __init__(self, capacity: int, refill_rate_per_sec: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate_per_sec
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()

    def allow_request(self) -> bool:
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True
            return False
