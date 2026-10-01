"""
LEVEL 02 (core) - deque's core API: both-ends operations, rotate, maxlen
============================================================================
You will learn
  * append/appendleft and pop/popleft -- the handful of methods covering most deque usage
  * rotate() to cycle elements without rebuilding the sequence
  * maxlen turns a deque into a fixed-size ring buffer that evicts automatically

Run: python level_02_deque_core.py
"""
from collections import deque

if __name__ == "__main__":
    # ---- both ends are first-class operations ------------------------------
    dq = deque([2, 3, 4])
    dq.append(5)         # add to the right
    dq.appendleft(1)      # add to the left
    assert list(dq) == [1, 2, 3, 4, 5]

    assert dq.pop() == 5       # remove from the right
    assert dq.popleft() == 1   # remove from the left
    assert list(dq) == [2, 3, 4]

    # ---- rotate(): shift elements circularly without rebuilding -----------
    dq = deque([1, 2, 3, 4, 5])
    dq.rotate(2)                       # positive: rotate right
    assert list(dq) == [4, 5, 1, 2, 3]
    dq.rotate(-2)                      # negative: rotate left (undo it)
    assert list(dq) == [1, 2, 3, 4, 5]

    # ---- maxlen: a ring buffer that auto-evicts the oldest item ------------
    recent_events = deque(maxlen=3)
    for event in ["login", "click", "click", "purchase", "logout"]:
        recent_events.append(event)
    # only the LAST 3 events survive -- older ones were silently evicted
    assert list(recent_events) == ["click", "purchase", "logout"]
    assert len(recent_events) == 3

    # appendleft on a full ring buffer evicts from the OTHER end
    ring = deque([1, 2, 3], maxlen=3)
    ring.appendleft(0)
    assert list(ring) == [0, 1, 2]   # the 3 fell off the right

    print("OK")
