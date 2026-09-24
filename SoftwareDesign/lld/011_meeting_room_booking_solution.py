"""
================================================================================
SOLUTION · LLD 011 · Meeting Room Booking (Calendar / Hotel Rooms)  [Tier 1]
================================================================================

THE CORE IDEA
--------------
Every "book a resource for a time range" problem — meeting rooms, hotel rooms,
tennis courts, doctor appointments — reduces to three decisions:

    1. TIME as HALF-OPEN intervals [start, end). A 10:00-11:00 meeting and an
       11:00-12:00 meeting do NOT conflict, and durations are just end - start.
       Two intervals overlap iff  a.start < b.end  and  b.start < a.end.

    2. CONFLICT CHECK per room in O(log n): keep each room's bookings sorted by
       start. A new interval can only collide with its two neighbours in that
       order, so bisect for the insertion point and check just those two.
       (Scanning every booking is O(n) — demo 2.)

    3. WHICH ROOM when the user doesn't pick one -> RoomSelector strategy.
       SmallestFit keeps big rooms free for big meetings; FirstById is simple.

Concurrency is the parking-lot shape again: each RoomCalendar owns its lock
and does check-and-insert atomically; the scheduler tries candidate rooms in
the selector's order until one accepts.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. Rooms have an id, a capacity, and features (projector, video...).
  2. book(organizer, interval, attendees, needs, room_id=None) -> Booking.
     With room_id: that room or RoomConflict. Without: best room by selector,
     or NoRoomAvailable.
  3. cancel(booking_id).
  4. available_rooms(interval, attendees, needs) -> rooms free and suitable.
  5. earliest_slot(duration, attendees, not_before, not_after, needs)
     -> (room_id, Interval) or None.
  6. Observers notified on book / cancel.
  7. Many threads book concurrently; no room is ever double-booked.
  Out of scope: recurring meetings, time zones, invitations/RSVP.


================================================================================
ENTITIES, VALUE OBJECTS, INVARIANTS
================================================================================
    Interval        value object [start, end), start < end (minutes or epoch s)
    Room            value object: id, capacity, features
    Booking         value object: id, room_id, organizer, interval, attendees
    RoomCalendar    owns one room's sorted bookings + lock
                    INVARIANT: bookings sorted by start and pairwise non-overlapping
    RoomSelector    order(candidate rooms, request) -> rooms to try
    Scheduler       facade: room registry, booking index, observers


================================================================================
CONFLICT CHECK · bisect trace
================================================================================
    room bookings (sorted):  [9,10)  [11,12)  [14,16)
    starts:                   9       11       14
    request [12,14):  i = bisect_left(starts, 12) = 2
        previous  [11,12): 12 < 12? no  -> no overlap
        next      [14,16): 14 < 14? no  -> no overlap          => accepted, insert at 2
    request [15,17):  i = bisect_left(starts, 15) = 3
        previous  [14,16): 16 > 15      -> overlap              => rejected
    Only two neighbours ever need checking because the existing bookings are
    already non-overlapping and sorted.


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Sorted Python list + bisect: O(log n) search, O(n) insert (memmove, very
    fast in practice). A balanced BST / sortedcontainers / interval tree gives
    O(log n) insert; say so if n per room is large (hotel over years).
  * Interval tree is needed only for "which bookings overlap [a,b)" queries
    over MANY rooms at once; per-room sorted lists suffice for booking.
  * Lock per room; the scheduler holds at most one room lock at a time.
  * Hotel variant: rooms of a TYPE are interchangeable until check-in, so book
    against per-type, per-night inventory counters, assign a physical room at
    check-in. Mentioning this distinction is a strong signal.
  * Times are integers (minutes since epoch) — no datetime arithmetic in the core.


================================================================================
COMPLEXITY
================================================================================
    Operation          Time                          Space
    book (room given)  O(log n + n) insert           O(1)
    book (auto)        O(R log R + R log n)
    cancel             O(log n + n)
    available_rooms    O(R log n)
    earliest_slot      O(R * n) worst case
    R rooms, n bookings per room


================================================================================
EDGE CASES
================================================================================
  * Back-to-back meetings [10,11) and [11,12) are fine.
  * Identical start times conflict.
  * A booking entirely containing another conflicts (caught by the next-neighbour check).
  * start >= end -> InvalidInterval.
  * attendees > every room's capacity -> NoRoomAvailable.
  * Cancel unknown / already-cancelled booking -> UnknownBooking.
  * earliest_slot with a window shorter than the duration -> None.


================================================================================
COMMON MISTAKES
================================================================================
  1. Closed intervals: [10,11] and [11,12] reported as a conflict.
  2. Overlap test written as four cases instead of one inequality pair.
  3. Scanning all bookings of all rooms for every request.
  4. Choosing the room, then checking availability in a separate unlocked step.
  5. A Room class that stores bookings AND selects rooms AND sends emails.
  6. datetime objects with time zones inside the conflict math.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Recurring meetings -> expand occurrences within a horizon; book all
    atomically (lock rooms in id order) or report per-occurrence conflicts.
  * Minimum rooms needed for a day's meetings -> sweep line / min-heap of end
    times (LC 253), a capacity-planning report.
  * Hotel booking -> type inventory per night + overbooking policy.
  * Distributed -> bookings table with an exclusion constraint
    (PostgreSQL: EXCLUDE USING gist (room WITH =, during WITH &&)).
  * Waitlist -> Observer on cancel offers the slot to the next requester.


================================================================================
RELATED
================================================================================
  PyDSA intervals (merge intervals, meeting rooms II, my calendar I/II)
  lld/001_parking_lot (atomic claim, selection strategy)
  lld/004_movie_ticket_booking (holds with expiry)
  SoftwareDesign/02_oop_and_domain_modeling.md §7 value objects
"""

from __future__ import annotations

import bisect
import itertools
import random
import threading
import time
from dataclasses import dataclass, field
from typing import Callable, Protocol


# ----------------------------------------------------------------------------
# Value objects and errors
# ----------------------------------------------------------------------------
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
        if self.start >= self.end:
            raise InvalidInterval(f"[{self.start}, {self.end}) is empty")

    def overlaps(self, other: Interval) -> bool:
        return self.start < other.end and other.start < self.end

    @property
    def duration(self) -> int:
        return self.end - self.start


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


# ----------------------------------------------------------------------------
# RoomCalendar — one room's sorted, non-overlapping bookings
# ----------------------------------------------------------------------------
@dataclass
class RoomCalendar:
    room: Room
    _starts: list[int] = field(default_factory=list)
    _bookings: list[Booking] = field(default_factory=list)
    lock: threading.Lock = field(default_factory=threading.Lock)

    def _conflict_index(self, iv: Interval) -> tuple[int, bool]:
        i = bisect.bisect_left(self._starts, iv.start)
        clash = (i > 0 and self._bookings[i - 1].interval.end > iv.start) or \
                (i < len(self._bookings) and self._bookings[i].interval.start < iv.end)
        return i, clash

    def is_free(self, iv: Interval) -> bool:
        with self.lock:
            return not self._conflict_index(iv)[1]

    def try_add(self, booking: Booking) -> bool:
        with self.lock:
            i, clash = self._conflict_index(booking.interval)
            if clash:
                return False
            self._starts.insert(i, booking.interval.start)
            self._bookings.insert(i, booking)
            return True

    def remove(self, booking: Booking) -> None:
        with self.lock:
            i = bisect.bisect_left(self._starts, booking.interval.start)
            if i < len(self._bookings) and self._bookings[i].id == booking.id:
                del self._starts[i]
                del self._bookings[i]

    def bookings(self) -> list[Booking]:
        with self.lock:
            return list(self._bookings)

    def first_gap(self, duration: int, not_before: int, not_after: int) -> Interval | None:
        with self.lock:
            cursor = not_before
            i = bisect.bisect_left(self._starts, not_before)
            if i > 0:
                cursor = max(cursor, self._bookings[i - 1].interval.end)
            for b in self._bookings[i:]:
                if b.interval.start - cursor >= duration:
                    break
                cursor = max(cursor, b.interval.end)
            if cursor + duration <= not_after:
                return Interval(cursor, cursor + duration)
            return None


# ----------------------------------------------------------------------------
# Room selection strategies
# ----------------------------------------------------------------------------
class RoomSelector(Protocol):
    def order(self, rooms: list[Room], attendees: int) -> list[Room]: ...


class SmallestFit:
    """Smallest room that fits; keeps big rooms for big meetings."""

    def order(self, rooms, attendees):
        return sorted(rooms, key=lambda r: (r.capacity, r.id))


class FirstById:
    def order(self, rooms, attendees):
        return sorted(rooms, key=lambda r: r.id)


# ----------------------------------------------------------------------------
# Scheduler — facade
# ----------------------------------------------------------------------------
Listener = Callable[[str, Booking], None]


class Scheduler:
    def __init__(self, rooms: list[Room], selector: RoomSelector | None = None) -> None:
        self._calendars = {r.id: RoomCalendar(r) for r in rooms}
        if len(self._calendars) != len(rooms):
            raise ValueError("duplicate room id")
        self._selector = selector or SmallestFit()
        self._bookings: dict[int, Booking] = {}
        self._registry = threading.Lock()
        self._ids = itertools.count(1)
        self._listeners: list[Listener] = []

    def subscribe(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def book(self, organizer: str, interval: Interval, attendees: int = 1,
             needs: frozenset[str] = frozenset(), room_id: str | None = None) -> Booking:
        if room_id is not None:
            cal = self._calendar(room_id)
            if not self._suitable(cal.room, attendees, needs):
                raise RoomConflict(f"{room_id} can't host {attendees} with {sorted(needs)}")
            candidates = [cal.room]
        else:
            rooms = [c.room for c in self._calendars.values() if self._suitable(c.room, attendees, needs)]
            candidates = self._selector.order(rooms, attendees)
        with self._registry:
            booking_id = next(self._ids)
        for room in candidates:
            booking = Booking(booking_id, room.id, organizer, interval, attendees)
            if self._calendars[room.id].try_add(booking):
                with self._registry:
                    self._bookings[booking_id] = booking
                self._notify("booked", booking)
                return booking
        if room_id is not None:
            raise RoomConflict(f"{room_id} is busy during [{interval.start}, {interval.end})")
        raise NoRoomAvailable(f"no room for {attendees} during [{interval.start}, {interval.end})")

    def cancel(self, booking_id: int) -> None:
        with self._registry:
            booking = self._bookings.pop(booking_id, None)
        if booking is None:
            raise UnknownBooking(booking_id)
        self._calendars[booking.room_id].remove(booking)
        self._notify("cancelled", booking)

    def available_rooms(self, interval: Interval, attendees: int = 1,
                        needs: frozenset[str] = frozenset()) -> list[Room]:
        rooms = [c.room for c in self._calendars.values()
                 if self._suitable(c.room, attendees, needs) and c.is_free(interval)]
        return self._selector.order(rooms, attendees)

    def schedule(self, room_id: str) -> list[Booking]:
        return self._calendar(room_id).bookings()

    def earliest_slot(self, duration: int, attendees: int, not_before: int, not_after: int,
                      needs: frozenset[str] = frozenset()) -> tuple[str, Interval] | None:
        best: tuple[str, Interval] | None = None
        rooms = [c.room for c in self._calendars.values() if self._suitable(c.room, attendees, needs)]
        for room in self._selector.order(rooms, attendees):          # selector order breaks ties
            gap = self._calendars[room.id].first_gap(duration, not_before, not_after)
            if gap is not None and (best is None or gap.start < best[1].start):
                best = (room.id, gap)
        return best

    @staticmethod
    def _suitable(room: Room, attendees: int, needs: frozenset[str]) -> bool:
        return room.capacity >= attendees and needs <= room.features

    def _calendar(self, room_id: str) -> RoomCalendar:
        if room_id not in self._calendars:
            raise UnknownRoom(room_id)
        return self._calendars[room_id]

    def _notify(self, event: str, booking: Booking) -> None:
        for listener in list(self._listeners):
            try:
                listener(event, booking)
            except Exception:
                pass


# ===================================================================== TESTS ==
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


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 40,000 random requests, bisect calendar vs brute-force scan ---")
    rng = random.Random(8)
    cal = RoomCalendar(Room("r", 10))
    brute: list[Interval] = []
    mismatches = 0
    live: list[Booking] = []
    for i in range(40_000):
        if live and rng.random() < 0.3:
            b = live.pop(rng.randrange(len(live)))
            cal.remove(b)
            brute.remove(b.interval)
            continue
        start = rng.randrange(0, 10_000)
        iv = Interval(start, start + rng.randrange(1, 60))
        b = Booking(i, "r", "u", iv, 1)
        expected = not any(iv.overlaps(x) for x in brute)
        got = cal.try_add(b)
        mismatches += got != expected
        if got:
            brute.append(iv)
            live.append(b)
    all_ok &= _check(f"identical accept/reject decisions ({mismatches} mismatches)", mismatches == 0)

    print("\n--- DEMO 2: conflict check cost with 20,000 bookings in one room ---")
    cal = RoomCalendar(Room("r", 10))
    for k in range(20_000):
        cal.try_add(Booking(k, "r", "u", Interval(k * 10, k * 10 + 5), 1))
    bookings = cal.bookings()
    probes = [Interval(s, s + 3) for s in rng.sample(range(0, 200_000), 2000)]
    start = time.perf_counter()
    fast = [cal.is_free(p) for p in probes]
    bisect_ms = (time.perf_counter() - start) * 1000
    start = time.perf_counter()
    slow = [not any(p.overlaps(b.interval) for b in bookings) for p in probes]
    scan_ms = (time.perf_counter() - start) * 1000
    print(f"      2,000 checks: bisect {bisect_ms:.1f} ms, full scan {scan_ms:.0f} ms ({scan_ms / bisect_ms:.0f}x)")
    all_ok &= _check("same answers, bisect far faster", fast == slow and bisect_ms * 20 < scan_ms)

    print("\n--- DEMO 3: 16 threads auto-book 3,200 random meetings across 3 rooms ---")
    s = Scheduler(ROOMS)
    ok_count = [0]
    guard = threading.Lock()

    def worker(seed: int) -> None:
        r = random.Random(seed)
        for _ in range(200):
            start = r.randrange(0, 2000)
            try:
                s.book("u", Interval(start, start + r.randrange(5, 40)), attendees=r.randint(1, 3))
                with guard:
                    ok_count[0] += 1
            except NoRoomAvailable:
                pass

    ts = [threading.Thread(target=worker, args=(i,)) for i in range(16)]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    overlaps = 0
    total = 0
    for room in ROOMS:
        sched = s.schedule(room.id)
        total += len(sched)
        overlaps += sum(1 for a, b in zip(sched, sched[1:]) if a.interval.overlaps(b.interval))
    print(f"      {ok_count[0]} bookings accepted, {total} on calendars, {overlaps} overlaps")
    all_ok &= _check("no room double-booked; every accepted booking is on a calendar",
                     overlaps == 0 and total == ok_count[0])
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
