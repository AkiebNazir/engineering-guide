"""
================================================================================
LeetCode 362 · Design Hit Counter                                       [Medium]
https://leetcode.com/problems/design-hit-counter/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Design a hit counter which counts the number of hits received in the PAST 5
MINUTES (i.e., the past 300 seconds).

Your system should accept a `timestamp` parameter (in seconds granularity), and
you may assume that calls are being made in chronological order (timestamp is
monotonically non-decreasing). Several hits may arrive roughly at the same time.

Implement the HitCounter class:

    HitCounter()                 Initializes the object.
    hit(timestamp) -> None       Records a hit at timestamp.
    getHits(timestamp) -> int    Returns the number of hits in the past 5
                                 minutes from timestamp, i.e. hits in
                                 (timestamp - 300, timestamp].


EXAMPLES
--------
    ["HitCounter","hit","hit","hit","getHits","hit","getHits","getHits"]
    [[],[1],[2],[3],[4],[300],[300],[301]]
    Output: [null,null,null,null,3,null,4,3]

    getHits(4)   -> 3   hits at 1, 2, 3
    getHits(300) -> 4   hits at 1, 2, 3, 300 (window (0, 300])
    getHits(301) -> 3   window (1, 301]: the hit at 1 has expired


CONSTRAINTS
-----------
    1 <= timestamp <= 2 * 10^9
    All calls are made in chronological order.
    At most 300 calls will be made to hit and getHits.

    Follow up: what if the number of hits per second could be huge? Does your
    design scale?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
A sliding time window. Two natural designs:

    1. QUEUE of timestamps. Append on hit; on getHits, pop from the front while
       the front is <= timestamp - 300. The queue length is the answer.
       Memory grows with the number of HITS in the window.

    2. CIRCULAR BUCKETS: 300 slots, one per second. Slot i = timestamp % 300
       holds (time, count). On hit, if the slot's time is stale, reset it.
       getHits sums slots whose time is inside the window.
       Memory is fixed at 300 slots no matter how many hits arrive.

The follow-up is the point of the question: design 1 stores a million entries
for a million hits per second; design 2 stores 300 numbers.


WHAT TO THINK ABOUT
--------------------
1. The window is (timestamp - 300, timestamp]. Is a hit at exactly
   timestamp - 300 inside?

2. In the bucket design, how do you know a slot's count is from 300+ seconds
   ago and must not be counted?

3. What if calls are NOT in chronological order, or many threads call hit()?


PROGRESSIVE HINTS
------------------
Hint 1 (queue): while queue and queue[0] <= timestamp - 300: popleft().

Hint 2 (buckets): times = [0] * 300, counts = [0] * 300. hit(t): i = t % 300;
        if times[i] != t: times[i] = t; counts[i] = 0. counts[i] += 1.

Hint 3 (buckets): getHits(t) = sum(counts[i] for i in range(300)
        if t - times[i] < 300).


COMPLEXITY TARGET
------------------
    Queue:    hit O(1), getHits O(1) amortized, memory O(hits in window)
    Buckets:  hit O(1), getHits O(300), memory O(300)
================================================================================
"""


class HitCounter:
    def __init__(self):
        # YOUR CODE HERE
        pass

    def hit(self, timestamp: int) -> None:
        # YOUR CODE HERE
        pass

    def getHits(self, timestamp: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 011_design_hit_counter_question.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    hc = HitCounter()
    hc.hit(1); hc.hit(2); hc.hit(3)
    checks = [(hc.getHits(4), 3)]
    hc.hit(300)
    checks += [(hc.getHits(300), 4), (hc.getHits(301), 3)]
    for got, want in checks:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  got={got}  want={want}")

    hc2 = HitCounter()
    for _ in range(5):
        hc2.hit(100)
    checks = [(hc2.getHits(100), 5), (hc2.getHits(399), 5), (hc2.getHits(400), 0), (hc2.getHits(10_000), 0)]
    for got, want in checks:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  burst at t=100  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
