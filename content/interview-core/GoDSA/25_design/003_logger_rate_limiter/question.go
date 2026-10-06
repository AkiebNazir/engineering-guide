package main

/*
================================================================================
LeetCode 359 · Logger Rate Limiter                                        [Easy]
https://leetcode.com/problems/logger-rate-limiter/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Design a logger system that receives a stream of messages along with their
timestamps. Each UNIQUE message should be printed AT MOST ONCE every 10
seconds (i.e. if a message was printed at timestamp `t`, the SAME message
is suppressed until `t + 10`).

All messages arrive in NON-DECREASING order of timestamp — several
messages may arrive at the same timestamp.

Implement the `Logger` class:

    Logger()                              Initializes the object.
    shouldPrintMessage(timestamp,
                        message) -> bool  Returns True if `message` should
                                          be printed in the given
                                          `timestamp`, otherwise returns
                                          False.


EXAMPLES
--------
Example 1:
    Input:
        ["Logger", "shouldPrintMessage", "shouldPrintMessage",
         "shouldPrintMessage", "shouldPrintMessage", "shouldPrintMessage",
         "shouldPrintMessage"]
        [[], [1, "foo"], [2, "bar"], [3, "foo"], [8, "bar"], [10, "foo"], [11, "foo"]]
    Output:
        [null, true, true, false, false, false, true]

    Explanation:
        logger = Logger()
        logger.shouldPrintMessage(1, "foo")   # True,  next allowed: foo @ 11
        logger.shouldPrintMessage(2, "bar")   # True,  next allowed: bar @ 12
        logger.shouldPrintMessage(3, "foo")   # False, 3 < 11
        logger.shouldPrintMessage(8, "bar")   # False, 8 < 12
        logger.shouldPrintMessage(10, "foo")  # False, 10 < 11
        logger.shouldPrintMessage(11, "foo")  # True,  11 >= 11, next: foo @ 21


CONSTRAINTS
-----------
    0 <= timestamp <= 10^9
    1 <= message.length <= 30
    At most 10^4 calls will be made to shouldPrintMessage.
    Timestamps for successive calls are NON-DECREASING.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is a small design problem built on a single hashmap: `message ->
timestamp at which it becomes eligible again`. The "timestamps arrive
non-decreasing" constraint is the load-bearing simplification — it means
you never need to reason about out-of-order arrivals, and it also means
you could in principle EVICT stale entries as time moves forward (a follow-
up direction; not required for correctness here since the map never grows
past "one entry per distinct message ever seen").


WHAT TO THINK ABOUT
--------------------
1. Store `message -> next_allowed_timestamp` (the FIRST timestamp at which
   this message may print again), not `message -> last_printed_timestamp`
   — storing "next allowed" turns every check into a single comparison
   (`timestamp >= next_allowed`) instead of a comparison plus an addition
   on every check.

2. A message never seen before must be allowed immediately and only THEN
   recorded — the dict lookup for a first-time message should behave like
   "eligible" (comparable to `-inf` / not present), not accidentally
   suppress it.

3. On ANY allowed print (first-time or re-eligible), update the map to
   `timestamp + 10` — this is the only place the map is ever written.


PROGRESSIVE HINTS
------------------
Hint 1: One dict is enough: `message -> next_allowed_timestamp`.

Hint 2: `shouldPrintMessage` is: "if message not in the dict, or
        `timestamp >= dict[message]`, allow it and set
        `dict[message] = timestamp + 10`; otherwise return False."

Hint 3: Because timestamps only move forward, you don't need to actively
        expire old entries for correctness — the comparison against the
        stored "next allowed" value already does the right thing no matter
        how much time has passed.


COMPLEXITY TARGET
------------------
    shouldPrintMessage:  O(1) average time
    Space: O(number of distinct messages ever seen)
================================================================================
*/

// TODO: Implement the stub
