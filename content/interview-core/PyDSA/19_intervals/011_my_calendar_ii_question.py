"""
================================================================================
LeetCode 731 · My Calendar II                                           [Medium]
https://leetcode.com/problems/my-calendar-ii/
Topic: 19 · Intervals
================================================================================

PROBLEM
-------
You are implementing a program to use as your calendar. You can add a new
event if adding it will not cause a TRIPLE BOOKING.

A triple booking happens when three events have some non-empty intersection
(some moment is common to all three).

Events are half-open intervals [start, end).

Implement the MyCalendarTwo class:

    MyCalendarTwo()           Initializes the calendar object.
    book(start, end) -> bool  Returns True and adds the event if it doesn't
                              cause a triple booking. Otherwise returns False
                              and does not add it.


EXAMPLES
--------
    ["MyCalendarTwo","book","book","book","book","book","book"]
    [[],[10,20],[50,60],[10,40],[5,15],[5,10],[25,55]]
    Output: [null,true,true,true,false,true,true]

    book(10, 20) -> True
    book(50, 60) -> True
    book(10, 40) -> True    double booking on [10, 20)
    book(5, 15)  -> False   [10, 15) would be triple booked
    book(5, 10)  -> True    touches [10, 20) and [10, 40) only at 10
    book(25, 55) -> True    double booking on [25, 40) and [50, 55)


CONSTRAINTS
-----------
    0 <= start < end <= 10^9
    At most 1000 calls will be made to book.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Keep two lists:

    bookings   every accepted event
    overlaps   every region that is currently DOUBLE booked

A new event causes a triple booking exactly when it intersects some region in
`overlaps`. If it doesn't, accept it, and record its intersections with
existing bookings as new double-booked regions.

The intersection of [s1, e1) and [s2, e2) is [max(s1, s2), min(e1, e2)), and
it's non-empty when max(starts) < min(ends).

Alternative: a sweep line over a sorted "difference map" (+1 at start, -1 at
end). Running sum > 2 anywhere means triple booking. This generalizes to
"at most k bookings".


WHAT TO THINK ABOUT
--------------------
1. Why is it enough to check the new event against `overlaps` only?

2. What exactly do you store in `overlaps`: the whole booking, or just the
   intersection?

3. For the sweep-line version, how do you undo a rejected booking?


PROGRESSIVE HINTS
------------------
Hint 1: for (s, e) in overlaps: if start < e and s < end: return False.

Hint 2: for (s, e) in bookings: if start < e and s < end:
            overlaps.append((max(start, s), min(end, e))).

Hint 3: bookings.append((start, end)); return True.


COMPLEXITY TARGET
------------------
    Time:  O(n) per book
    Space: O(n)  (overlaps can hold up to O(n) regions... per booking, O(n^2)
                  worst case in total; fine for 1000 calls)
================================================================================
"""


class MyCalendarTwo:
    def __init__(self):
        # YOUR CODE HERE
        pass

    def book(self, start: int, end: int) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 011_my_calendar_ii_question.py
# ==============================================================================
def run_tests() -> None:
    scripts = [
        [((10, 20), True), ((50, 60), True), ((10, 40), True), ((5, 15), False), ((5, 10), True), ((25, 55), True)],
        [((10, 20), True), ((15, 25), True), ((20, 22), True), ((16, 18), False)],
        [((1, 5), True), ((1, 5), True), ((1, 5), False), ((5, 6), True)],
    ]
    all_ok = True
    for script in scripts:
        cal = MyCalendarTwo()
        got = [cal.book(s, e) for (s, e), _ in script]
        want = [w for _, w in script]
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {[iv for iv, _ in script]}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
