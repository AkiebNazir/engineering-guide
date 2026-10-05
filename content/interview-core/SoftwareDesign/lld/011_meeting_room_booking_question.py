"""
================================================================================
LLD 011 · Meeting Room Booking (Calendar / Hotel Rooms)            [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement a meeting-room booking system for an office.

The interviewer says: "Design a meeting room scheduler." These are the agreed
requirements.

REQUIREMENTS
------------
  1. Time is an integer (minutes). Interval(start, end) is HALF-OPEN
     [start, end); start >= end raises InvalidInterval. interval.overlaps(other).
  2. Room(id, capacity, features=frozenset()). A room is suitable for a request
     if capacity >= attendees and it has every needed feature.
  3. Scheduler(rooms, selector=None) — default selector SmallestFit.
  4. book(organizer, interval, attendees=1, needs=frozenset(), room_id=None)
       -> Booking(id, room_id, organizer, interval, attendees)
     * room_id given: book that room, or raise RoomConflict if it is busy or
       unsuitable. UnknownRoom if the id doesn't exist.
     * room_id None: try suitable rooms in the selector's order; the first free
       one wins. None free -> NoRoomAvailable.
     * Checking a room's calendar must be O(log n) in its number of bookings.
  5. Selectors — order(rooms, attendees) -> rooms in preference order:
        SmallestFit  by (capacity, id)
        FirstById    by id
  6. cancel(booking_id); UnknownBooking if unknown or already cancelled.
  7. available_rooms(interval, attendees=1, needs=frozenset()) -> suitable free
     rooms in selector order. schedule(room_id) -> bookings sorted by start.
  8. earliest_slot(duration, attendees, not_before, not_after, needs=frozenset())
     -> (room_id, Interval) with the earliest possible start such that the
     slot lies within [not_before, not_after]; ties go to selector order.
     None if impossible.
  9. subscribe(listener): listener(event, booking) with event "booked" or
     "cancelled".
 10. Many threads may book at once; a room is never double-booked.

  Out of scope: recurring meetings, time zones, invitations.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * Open or closed intervals? Why?
  * The overlap condition in one line.
  * How to check a room's calendar without scanning every booking.
  * Which object owns "no overlaps in this room", and where is its lock?
  * How would a HOTEL differ (room types vs physical rooms)?

FOLLOW-UPS TO PREPARE
---------------------
  recurring meetings · minimum rooms for a day (sweep line) · hotel inventory
  per night · database exclusion constraints · waitlists.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass


class SchedulingError(Exception): ...
class InvalidInterval(SchedulingError): ...
class UnknownRoom(SchedulingError): ...
class UnknownBooking(SchedulingError): ...
class RoomConflict(SchedulingError): ...
class NoRoomAvailable(SchedulingError): ...


@dataclass(frozen=True, slots=True, order=True)
class Interval:
    start: int
    end: int

    def __post_init__(self) -> None:
        # YOUR CODE HERE
        pass

    def overlaps(self, other: Interval) -> bool:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class Room:
    id: str
    capacity: int
    features: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class Booking:
    id: int
    room_id: str
    organizer: str
    interval: Interval
    attendees: int


class SmallestFit:
    def order(self, rooms: list[Room], attendees: int) -> list[Room]:
        raise NotImplementedError


class FirstById:
    def order(self, rooms: list[Room], attendees: int) -> list[Room]:
        raise NotImplementedError


class Scheduler:
    def __init__(self, rooms: list[Room], selector=None) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def subscribe(self, listener) -> None: raise NotImplementedError

    def book(self, organizer: str, interval: Interval, attendees: int = 1,
             needs: frozenset[str] = frozenset(), room_id: str | None = None) -> Booking:
        raise NotImplementedError

    def cancel(self, booking_id: int) -> None: raise NotImplementedError

    def available_rooms(self, interval: Interval, attendees: int = 1,
                        needs: frozenset[str] = frozenset()) -> list[Room]:
        raise NotImplementedError

    def schedule(self, room_id: str) -> list[Booking]: raise NotImplementedError

    def earliest_slot(self, duration: int, attendees: int, not_before: int, not_after: int,
                      needs: frozenset[str] = frozenset()) -> tuple[str, Interval] | None:
        raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc, fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


ROOMS = [Room("big", 20, frozenset({"video", "projector"})),
         Room("mid", 8, frozenset({"projector"})),
         Room("tiny", 3)]


def run_tests() -> bool:
    all_ok = True
    print("--- intervals ---")
    all_ok &= _check("half-open: [10,11) and [11,12) don't overlap",
                     not Interval(10, 11).overlaps(Interval(11, 12)))
    all_ok &= _check("containment overlaps", Interval(10, 20).overlaps(Interval(12, 13)))
    all_ok &= _check("empty interval rejected", _raises(InvalidInterval, lambda: Interval(5, 5)))

    print("\n--- the bisect trace ---")
    s = Scheduler(ROOMS)
    for a, b in ((9, 10), (11, 12), (14, 16)):
        s.book("ann", Interval(a, b), room_id="tiny")
    ok_mid = s.book("bob", Interval(12, 14), room_id="tiny")
    all_ok &= _check("[12,14) fits between [11,12) and [14,16)", ok_mid.room_id == "tiny")
    all_ok &= _check("[15,17) clashes with [14,16)",
                     _raises(RoomConflict, lambda: s.book("cat", Interval(15, 17), room_id="tiny")))
    all_ok &= _check("same start clashes", _raises(RoomConflict, lambda: s.book("cat", Interval(9, 9 + 1), room_id="tiny")))
    all_ok &= _check("request containing a booking clashes",
                     _raises(RoomConflict, lambda: s.book("cat", Interval(8, 20), room_id="tiny")))
    all_ok &= _check("schedule is sorted",
                     [b.interval.start for b in s.schedule("tiny")] == [9, 11, 12, 14])

    print("\n--- automatic room selection ---")
    s = Scheduler(ROOMS)
    b1 = s.book("ann", Interval(100, 160), attendees=2)
    all_ok &= _check("SmallestFit picks tiny for 2 people", b1.room_id == "tiny")
    b2 = s.book("bob", Interval(120, 180), attendees=2)
    all_ok &= _check("tiny busy -> next smallest (mid)", b2.room_id == "mid")
    b3 = s.book("cat", Interval(120, 180), attendees=2, needs=frozenset({"video"}))
    all_ok &= _check("feature requirement -> big", b3.room_id == "big")
    all_ok &= _check("nothing left for an overlapping 2-person meeting",
                     _raises(NoRoomAvailable, lambda: s.book("dan", Interval(150, 170), attendees=2)))
    all_ok &= _check("too many attendees for any room",
                     _raises(NoRoomAvailable, lambda: s.book("eve", Interval(0, 10), attendees=50)))
    all_ok &= _check("room too small when requested explicitly",
                     _raises(RoomConflict, lambda: s.book("eve", Interval(0, 10), attendees=5, room_id="tiny")))
    first = Scheduler(ROOMS, FirstById()).book("ann", Interval(0, 10), attendees=2)
    all_ok &= _check("FirstById picks 'big'", first.room_id == "big")

    print("\n--- cancel, availability, observers ---")
    events = []
    s.subscribe(lambda e, b: events.append((e, b.id)))
    s.cancel(b2.id)
    all_ok &= _check("cancel frees mid", [r.id for r in s.available_rooms(Interval(150, 170), 2)] == ["mid"])
    all_ok &= _check("cancel twice -> UnknownBooking", _raises(UnknownBooking, lambda: s.cancel(b2.id)))
    all_ok &= _check("observer saw the cancel", events == [("cancelled", b2.id)])
    all_ok &= _check("unknown room", _raises(UnknownRoom, lambda: s.schedule("nope")))

    print("\n--- earliest slot ---")
    s = Scheduler(ROOMS)
    s.book("x", Interval(540, 600), room_id="tiny")      # 9:00-10:00
    s.book("x", Interval(610, 660), room_id="tiny")      # 10:10-11:00
    s.book("x", Interval(540, 630), room_id="mid")       # 9:00-10:30
    s.book("x", Interval(0, 1440), room_id="big")
    all_ok &= _check("30 min for 2 from 9:00: tiny's 10-min gap too small; tiny at 11:00 vs mid at 10:30 -> mid",
                     s.earliest_slot(30, 2, 540, 1020) == ("mid", Interval(630, 660)))
    all_ok &= _check("10 min fits tiny's gap at 10:00", s.earliest_slot(10, 2, 540, 1020) == ("tiny", Interval(600, 610)))
    all_ok &= _check("window too short -> None", s.earliest_slot(90, 2, 540, 600) is None)
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
