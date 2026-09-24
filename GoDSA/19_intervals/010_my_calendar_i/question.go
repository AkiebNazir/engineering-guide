package main

/*
================================================================================
LeetCode 729 · My Calendar I                                            [Medium]
https://leetcode.com/problems/my-calendar-i/
Topic: 19 · Intervals
================================================================================

PROBLEM
-------
You are implementing a program to use as your calendar. You can add a new
event if adding it will not cause a DOUBLE BOOKING.

A double booking happens when two events have some non-empty intersection.

An event is a pair of integers [start, end) — a HALF-OPEN interval: it
includes start and excludes end, so it covers start <= x < end.

Implement the MyCalendar class:

    MyCalendar()              Initializes the calendar object.
    book(start, end) -> bool  Returns True and adds the event if it doesn't
                              overlap an existing one. Otherwise returns False
                              and does not add it.


EXAMPLES
--------
    ["MyCalendar", "book", "book", "book"]
    [[], [10, 20], [15, 25], [20, 30]]
    Output: [null, true, false, true]

    book(10, 20) -> True
    book(15, 25) -> False   (15..19 overlaps [10, 20))
    book(20, 30) -> True    (touches [10, 20) at 20, but 20 isn't in [10, 20))


CONSTRAINTS
-----------
    0 <= start < end <= 10^9
    At most 1000 calls will be made to book.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Two half-open intervals [s1, e1) and [s2, e2) overlap exactly when

    s1 < e2  and  s2 < e1

Memorize this. It covers every arrangement (partial overlap either side,
containment, identical) in one line, and it correctly says that [10, 20) and
[20, 30) do NOT overlap.

Checking the new event against every booked event is O(n) per call. Booked
events never overlap each other, so if you keep them SORTED by start, only two
neighbors can possibly conflict: the event just before the new start and the
event just after it. Binary search finds them.


WHAT TO THINK ABOUT
--------------------
1. Why is `s1 < e2 and s2 < e1` the complete overlap test?

2. If booked intervals are disjoint and sorted, which existing intervals can
   overlap a new [s, e)?

3. Python has no built-in balanced BST. What does a sorted list + bisect cost
   per insert? Is that acceptable for 1000 calls?


PROGRESSIVE HINTS
------------------
Hint 1: Simple version: keep a list; for each (s2, e2), if start < e2 and
        s2 < end, return False. Otherwise append and return True.

Hint 2: Faster: keep starts and ends in sorted order. i = bisect_right(starts,
        start). Check the previous event (i - 1): its end must be <= start.
        Check the next event (i): its start must be >= end.

Hint 3: Insert at position i.


COMPLEXITY TARGET
------------------
    Linear scan:        O(n) per book
    Sorted + bisect:    O(log n) search + O(n) list insert (memmove);
                        O(log n) with a balanced BST
================================================================================
*/

// TODO: Implement the stub
