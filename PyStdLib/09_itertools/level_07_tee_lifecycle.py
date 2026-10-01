"""
LEVEL 07 (advanced) - tee(): independent parallel iterators, and their lifecycle cost
=========================================================================================
You will learn
  * tee() splits ONE iterator into several independent ones over the same data
  * once you tee() a source, stop using the ORIGINAL -- its items would be skipped
    for whichever branch already advanced past them
  * a branch that lags behind forces tee() to buffer everything the other branches
    already consumed -- it is not free memory-wise if the branches drift apart

Run: python level_07_tee_lifecycle.py
"""
from itertools import islice, tee

if __name__ == "__main__":
    source = iter(range(6))
    branch_a, branch_b = tee(source, 2)

    # each branch is independently, fully consumable
    assert list(branch_a) == [0, 1, 2, 3, 4, 5]
    assert list(branch_b) == [0, 1, 2, 3, 4, 5]   # branch_b was NOT affected by draining branch_a

    # ---- the lifecycle trap: using the ORIGINAL iterator after tee() -------
    original = iter(range(6))
    left, right = tee(original, 2)
    first_from_original = next(original, "exhausted")   # advances the shared underlying source
    # left/right no longer see that item -- tee() only guarantees independence
    # BETWEEN the branches it gave you, not between a branch and the leftover original
    assert first_from_original == 0
    assert list(left) == [1, 2, 3, 4, 5]    # item 0 is gone: the original already took it
    assert list(right) == [1, 2, 3, 4, 5]

    # ---- branches CAN drift apart, but tee() buffers what the slower one needs ----
    fast, slow = tee(iter(range(1000)), 2)
    fast_head = list(islice(fast, 10))          # fast branch races ahead by 10 items
    assert fast_head == list(range(10))
    # the slow branch can still see everything from the start -- tee() kept it buffered
    slow_head = list(islice(slow, 5))
    assert slow_head == [0, 1, 2, 3, 4]
    # draining both fully still produces the full, correct, independent sequences
    assert list(fast) == list(range(10, 1000))
    assert list(slow) == list(range(5, 1000))

    print("OK")
