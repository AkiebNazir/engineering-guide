package main

import "fmt"

/*
================================================================================
LeetCode 933 · Number of Recent Calls                                    [Easy]
https://leetcode.com/problems/number-of-recent-calls/
Topic: 07 · Queue / Deque
================================================================================

PROBLEM
-------
Implement the `RecentCounter` class, which counts the number of recent
requests within a certain time frame.

    RecentCounter()          Initializes with zero requests.
    int ping(int t)           Adds a new request at time t (milliseconds),
                              and returns the number of requests that have
                              happened in the inclusive range
                              [t - 3000, t].

It is guaranteed every call to ping uses a strictly larger value of t than
the previous call.


EXAMPLES
--------
Example 1:
    Input:
        ["RecentCounter", "ping", "ping", "ping", "ping"]
        [[], [1], [100], [3001], [3002]]
    Output:
        [null, 1, 2, 3, 3]
    Explanation:
        RecentCounter recentCounter = new RecentCounter();
        recentCounter.ping(1);     // requests = [1],               range is [-2999,1],   return 1
        recentCounter.ping(100);   // requests = [1,100],            range is [-2900,100], return 2
        recentCounter.ping(3001);  // requests = [1,100,3001],        range is [1,3001],    return 3
        recentCounter.ping(3002);  // requests = [1,100,3001,3002],    range is [2,3002],    return 3
                                    // (1 falls out: 1 < 2)


CONSTRAINTS
-----------
    1 <= t <= 10^9
    Each test case calls ping with STRICTLY INCREASING values of t.
    At most 10^4 calls will be made to ping.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is the FIFO-window pattern from the topic guide §5: a queue used as a
sliding COUNT. Every call to ping() enqueues the new timestamp; before
answering, evict (dequeue) everything from the FRONT that has fallen out of
the window (i.e., every timestamp strictly less than `t - 3000`).

Because timestamps arrive in strictly increasing order, the queue's front
is always the OLDEST timestamp still present, and eviction is monotone —
the same amortized argument as topic 03's sliding window and this topic's
own two-stack queue (001): each timestamp is enqueued exactly once and
dequeued at MOST once across the entire run, so the total eviction work
over n calls is O(n), not O(n) per call.

    q = deque()

    def ping(t):
        q.append(t)
        while q[0] < t - 3000:
            q.popleft()
        return len(q)

A naive alternative — store every timestamp in a list and, on each call,
COUNT how many satisfy the range by scanning the whole list — is O(n) per
call, O(n^2) total. The queue's eviction is cheaper because it never
re-examines a timestamp it has already determined is out of range.


WHAT TO THINK ABOUT
--------------------
1. Why is it safe to only check the FRONT of the queue for eviction,
   rather than scanning the whole thing? What property of the input
   (guaranteed by the constraints) makes this safe?

2. What is the correct comparison for eviction — `< t - 3000` or
   `<= t - 3000`? The window is described as INCLUSIVE of `t - 3000`.
   Get this boundary right; it's the classic off-by-one for this problem.

3. What is the total number of enqueue and dequeue operations across n
   calls to ping(), in the worst case? Is this bound tighter than "O(n)
   per call, so O(n^2) total"?

4. Why would a plain Python list with `list.pop(0)` for eviction still be
   correct but strictly worse than `collections.deque.popleft()`?

5. `collections.deque(maxlen=...)` auto-evicts from the opposite end when
   you push past capacity. Does that fit this problem directly, or does
   the WINDOW SIZE here depend on time (3000ms), not on a fixed COUNT of
   elements? Explain why maxlen isn't the right tool here.


PROGRESSIVE HINTS
------------------
Hint 1: Use `collections.deque`. Append every new call's timestamp to the
        back.

Hint 2: Before returning, evict from the FRONT any timestamp less than
        `t - 3000` — the window is [t - 3000, t], inclusive, so anything
        strictly less than the lower bound is out.

Hint 3:
    q = deque()

    def ping(t):
        q.append(t)
        while q and q[0] < t - 3000:
            q.popleft()
        return len(q)

Hint 4: The `while` (not `if`) matters — multiple stale timestamps can need
        eviction in one call if pings are sparse (e.g. a long gap between
        two calls).

Hint 5: The answer to ping() is always just `len(q)` after eviction — the
        queue AT ALL TIMES holds exactly the requests currently in window.


COMPLEXITY TARGET
------------------
    Time:  O(1) amortized per call (each timestamp enqueued & dequeued once)
    Space: O(n) worst case (all calls within one 3000ms window)
================================================================================
*/

func main() {
	fmt.Println("Solution for Number of Recent Calls not implemented yet")
}
