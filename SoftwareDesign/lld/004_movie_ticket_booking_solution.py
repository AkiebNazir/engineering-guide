"""
================================================================================
SOLUTION · LLD 004 · Movie Ticket Booking (BookMyShow / Ticketmaster)  [Tier 1]
================================================================================

THE CORE IDEA
--------------
Booking a seat is a TWO-PHASE flow, because payment is slow and can fail:

    hold(seats)  ->  pay  ->  confirm

    1. HOLD is atomic and all-or-nothing: either every requested seat becomes
       yours for a few minutes, or none do and you're told which were taken.
    2. A hold EXPIRES. Nobody runs a timer per hold: a seat's owner is checked
       lazily — "held by a hold whose expires_at is in the past" means free.
    3. CONFIRM moves the hold to PAYING under the lock (so it can't expire
       mid-payment), calls the payment gateway OUTSIDE the lock, then commits
       or rolls back under the lock again. Never hold a lock across a network call.

The check-then-act race is the whole interview. "Is seat A5 free? Yes -> mark
it mine" in two steps lets two users both see "free". Demo 1 shows it happen
with a simulated database round-trip between check and act, and shows the
per-show lock preventing it.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. Shows have a fixed seat map; seats have a category (REGULAR, PREMIUM).
  2. hold(user, show, seat_ids) -> Hold    all-or-nothing, max 10 seats,
     expires after a TTL (default 10 minutes).
  3. confirm(hold_id) -> Booking           charges payment; idempotent.
  4. release(hold_id)                       user abandons checkout.
  5. cancel(booking_id)                     refunds; not after the show starts.
  6. available(show) -> seat ids free right now.
  7. Price per seat is a pluggable policy.
  8. Many users book concurrently. A seat is never in two live holds/bookings.
  Out of scope: search/browse, seat-map rendering, discounts, waitlists.


================================================================================
ENTITIES, VALUE OBJECTS, INVARIANTS
================================================================================
    Seat, Show                  value objects (the catalogue)
    Hold (entity, internal)     id, user, show, seats, total, expires_at, status
    HoldStatus                  HELD -> PAYING -> CONFIRMED
                                HELD -> RELEASED | EXPIRED;  PAYING -> HELD (declined)
    HoldView / Booking          immutable snapshots handed to callers
    _ShowInventory              owns ONE show's seat -> hold map and its lock.
                                INVARIANT: a seat maps to at most one hold whose
                                status is HELD (unexpired), PAYING or CONFIRMED
    BookingService              facade; routes each call to one show's inventory
    PricingPolicy               price(show, seat) -> cents
    PaymentGateway (port)       charge(user, cents, idempotency_key) / refund(ref)


================================================================================
CLASS DIAGRAM
================================================================================
    ┌────────────────────────────┐ 1     * ┌─────────────────────────────────┐
    │ BookingService             │◆───────▶│ _ShowInventory                  │
    ├────────────────────────────┤         ├─────────────────────────────────┤
    │ - _hold_show: {hold: show} │         │ - show: Show                    │
    │ - _bookings                │         │ - owner: {seat_id: Hold}        │
    │ + hold / confirm / release │         │ - lock    (one per show)        │
    │ + cancel / available       │         │ + is_free(seat, now) lazy expiry│
    └──────┬──────────────┬──────┘         └─────────────────────────────────┘
           │ uses         │ uses
           ▼              ▼
    «protocol» PricingPolicy   «port» PaymentGateway


================================================================================
KEY FLOW · confirm(hold_id)
================================================================================
    lock(show)
      CONFIRMED already?          -> return the same Booking (idempotent)
      PAYING?                     -> BookingError (another request is paying)
      HELD but expires_at <= now  -> mark EXPIRED, raise HoldExpired
      status = PAYING             (expiry no longer applies)
    unlock
    gateway.charge(user, total, idempotency_key=hold_id)      <- slow, may fail
      declined -> lock: status = HELD (retry allowed until expiry); PaymentFailed
    lock: status = CONFIRMED; create Booking; unlock


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Lazy expiry instead of a sweeper thread. Correct with zero timers; a
    background sweeper can still exist purely to free memory.
  * One lock PER SHOW. Two users booking different shows never contend; a hold
    touches exactly one show, so there is never a second lock and no deadlock.
  * PAYING state protects a hold during payment. Without it: hold expires at
    9:59.9, user B grabs the seat, A's payment succeeds -> double sale.
    (Follow-up: a PAYING timeout plus a reconciliation job for stuck payments.)
  * Payment idempotency key = hold id, so a client retry of confirm() can't
    charge twice even if our process crashed between charge and commit.
  * Snapshots (HoldView, Booking) are returned instead of the mutable Hold, so
    callers can't change state behind the lock's back.
  * At scale the lock becomes the database:
        UPDATE seats SET hold_id=?, expires_at=?
         WHERE show_id=? AND seat_id IN (...) AND (hold_id IS NULL OR expires_at < now)
    and succeed only if rowcount == number of seats (else roll back).


================================================================================
COMPLEXITY
================================================================================
    Operation     Time             Space
    hold          O(k)  k seats    O(k)
    confirm       O(k) + payment   O(k)
    release       O(k)             O(1)
    available     O(S)  S seats in the show


================================================================================
EDGE CASES
================================================================================
  * Some requested seats taken -> nothing held; error lists the taken ones.
  * Duplicate seat ids in one request -> deduplicated, not double-priced.
  * Unknown show / unknown seat / zero seats / more than max -> errors.
  * Confirm exactly at expires_at -> expired (half-open [created, expires_at)).
  * Confirm twice -> same booking, charged once.
  * Payment declined -> hold stays HELD until its original expiry.
  * Release after confirm -> refused (use cancel).
  * Cancel after the show started -> refused.


================================================================================
COMMON MISTAKES
================================================================================
  1. Check availability, then book, as two unlocked steps.
  2. Holding the lock while calling the payment gateway.
  3. One global lock for every show in the system.
  4. A timer thread per hold.
  5. Partial holds ("got 2 of your 3 seats").
  6. No state between HELD and CONFIRMED -> expiry during payment double-sells.
  7. Non-idempotent confirm -> double charge on client retry.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Millions of users on a hot show -> virtual waiting room (queue tokens),
    seats as DB rows with conditional UPDATE, or Redis SET NX PX per seat.
  * "Best available N seats together" -> per-row free runs; Strategy.
  * Dynamic pricing -> PricingPolicy reads demand; price frozen into the hold.
  * Waitlist -> Observer on release/expiry notifies the next user.
  * Group booking split payment -> hold owned by group; confirm when all paid.
  * Payment succeeded but our commit crashed -> reconciliation job matches
    gateway charges by idempotency key and confirms or refunds.


================================================================================
RELATED
================================================================================
  SoftwareDesign/14_low_level_design_interview_playbook.md  §9 concurrency toolkit
  SoftwareDesign/04_design_patterns_in_practice.md          §3 Strategy, §16 Repository
  SystemDesign/problems (ticketing / flash sale)           the distributed version
  lld/001_parking_lot  (atomic claim, no expiry)
  lld/011_meeting_room_booking  (intervals instead of seats)
"""

from __future__ import annotations

import itertools
import random
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Protocol

Clock = Callable[[], float]


# ----------------------------------------------------------------------------
# Catalogue value objects
# ----------------------------------------------------------------------------
class SeatCategory(Enum):
    REGULAR = "regular"
    PREMIUM = "premium"


@dataclass(frozen=True, slots=True)
class Seat:
    id: str
    category: SeatCategory = SeatCategory.REGULAR


@dataclass(frozen=True, slots=True)
class Show:
    id: str
    movie: str
    starts_at: float
    seats: tuple[Seat, ...]


class HoldStatus(Enum):
    HELD = "held"
    PAYING = "paying"
    CONFIRMED = "confirmed"
    RELEASED = "released"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class HoldView:
    id: str
    user: str
    show_id: str
    seat_ids: tuple[str, ...]
    total_cents: int
    expires_at: float
    status: HoldStatus


@dataclass(frozen=True, slots=True)
class Booking:
    id: str
    user: str
    show_id: str
    seat_ids: tuple[str, ...]
    total_cents: int
    payment_ref: str


class BookingError(Exception): ...
class UnknownShow(BookingError): ...
class UnknownSeat(BookingError): ...
class TooManySeats(BookingError): ...
class HoldNotFound(BookingError): ...
class HoldExpired(BookingError): ...
class PaymentFailed(BookingError): ...
class PaymentDeclined(Exception): ...


class SeatsUnavailable(BookingError):
    def __init__(self, seat_ids: list[str]) -> None:
        super().__init__(f"taken: {seat_ids}")
        self.seat_ids = seat_ids


# ----------------------------------------------------------------------------
# Ports and strategies
# ----------------------------------------------------------------------------
class PricingPolicy(Protocol):
    def price(self, show: Show, seat: Seat) -> int: ...


class CategoryPricing:
    def __init__(self, cents: dict[SeatCategory, int]) -> None:
        self._cents = dict(cents)

    def price(self, show, seat):
        return self._cents[seat.category]


class PaymentGateway(Protocol):
    def charge(self, user: str, cents: int, idempotency_key: str) -> str: ...
    def refund(self, payment_ref: str) -> None: ...


# ----------------------------------------------------------------------------
# Internal entity + per-show inventory
# ----------------------------------------------------------------------------
@dataclass(slots=True)
class _Hold:
    id: str
    user: str
    show_id: str
    seat_ids: tuple[str, ...]
    total_cents: int
    expires_at: float
    status: HoldStatus = HoldStatus.HELD
    booking: Booking | None = None

    def live(self, now: float) -> bool:
        if self.status is HoldStatus.HELD:
            return now < self.expires_at
        return self.status in (HoldStatus.PAYING, HoldStatus.CONFIRMED)

    def view(self) -> HoldView:
        return HoldView(self.id, self.user, self.show_id, self.seat_ids,
                        self.total_cents, self.expires_at, self.status)


@dataclass(slots=True)
class _ShowInventory:
    show: Show
    seats: dict[str, Seat]
    lock: threading.Lock = field(default_factory=threading.Lock)
    owner: dict[str, _Hold] = field(default_factory=dict)
    holds: dict[str, _Hold] = field(default_factory=dict)

    def is_free(self, seat_id: str, now: float) -> bool:
        h = self.owner.get(seat_id)
        if h is None:
            return True
        if not h.live(now):
            if h.status is HoldStatus.HELD:
                h.status = HoldStatus.EXPIRED        # lazy expiry
            del self.owner[seat_id]
            return True
        return False


# ----------------------------------------------------------------------------
# BookingService — facade
# ----------------------------------------------------------------------------
class BookingService:
    def __init__(self, pricing: PricingPolicy, gateway: PaymentGateway,
                 clock: Clock = time.monotonic, hold_ttl_s: float = 600,
                 max_seats: int = 10) -> None:
        self._pricing = pricing
        self._gateway = gateway
        self._clock = clock
        self._ttl = hold_ttl_s
        self._max_seats = max_seats
        self._shows: dict[str, _ShowInventory] = {}
        self._hold_show: dict[str, str] = {}
        self._bookings: dict[str, tuple[str, str]] = {}      # booking id -> (show, hold)
        self._registry = threading.Lock()                    # guards the three dicts above
        self._ids = itertools.count(1)
        self._id_lock = threading.Lock()

    def add_show(self, show: Show) -> None:
        with self._registry:
            self._shows[show.id] = _ShowInventory(show, {s.id: s for s in show.seats})

    # -- phase 1 -------------------------------------------------------------------
    def hold(self, user: str, show_id: str, seat_ids: list[str]) -> HoldView:
        inv = self._inventory(show_id)
        wanted = tuple(dict.fromkeys(seat_ids))              # dedupe, keep order
        if not wanted:
            raise BookingError("no seats requested")
        if len(wanted) > self._max_seats:
            raise TooManySeats(f"max {self._max_seats}")
        unknown = [s for s in wanted if s not in inv.seats]
        if unknown:
            raise UnknownSeat(unknown)
        total = sum(self._pricing.price(inv.show, inv.seats[s]) for s in wanted)
        with inv.lock:
            now = self._clock()
            taken = [s for s in wanted if not inv.is_free(s, now)]
            if taken:
                raise SeatsUnavailable(taken)
            h = _Hold(self._next_id("H"), user, show_id, wanted, total, now + self._ttl)
            for s in wanted:
                inv.owner[s] = h
            inv.holds[h.id] = h
        with self._registry:
            self._hold_show[h.id] = show_id
        return h.view()

    # -- phase 2 -------------------------------------------------------------------
    def confirm(self, hold_id: str) -> Booking:
        inv, h = self._find_hold(hold_id)
        with inv.lock:
            if h.status is HoldStatus.CONFIRMED:
                return h.booking                              # idempotent
            if h.status is HoldStatus.PAYING:
                raise BookingError("payment already in progress")
            if h.status is HoldStatus.HELD and not h.live(self._clock()):
                self._free(inv, h, HoldStatus.EXPIRED)
            if h.status is not HoldStatus.HELD:
                raise HoldExpired(f"{hold_id} is {h.status.value}")
            h.status = HoldStatus.PAYING

        try:                                                  # no lock across the network
            ref = self._gateway.charge(h.user, h.total_cents, idempotency_key=h.id)
        except PaymentDeclined as e:
            with inv.lock:
                h.status = HoldStatus.HELD
            raise PaymentFailed(str(e)) from e

        with inv.lock:
            h.status = HoldStatus.CONFIRMED
            h.booking = Booking(self._next_id("B"), h.user, h.show_id, h.seat_ids,
                                h.total_cents, ref)
        with self._registry:
            self._bookings[h.booking.id] = (h.show_id, h.id)
        return h.booking

    def release(self, hold_id: str) -> None:
        inv, h = self._find_hold(hold_id)
        with inv.lock:
            if h.status in (HoldStatus.PAYING, HoldStatus.CONFIRMED):
                raise BookingError(f"cannot release a {h.status.value} hold")
            if h.status is HoldStatus.HELD:
                self._free(inv, h, HoldStatus.RELEASED)

    def cancel(self, booking_id: str) -> None:
        with self._registry:
            if booking_id not in self._bookings:
                raise BookingError(f"no booking {booking_id}")
            show_id, hold_id = self._bookings[booking_id]
        inv = self._inventory(show_id)
        with inv.lock:
            h = inv.holds[hold_id]
            if h.status is not HoldStatus.CONFIRMED:
                raise BookingError("booking already cancelled")
            if self._clock() >= inv.show.starts_at:
                raise BookingError("show already started")
            self._free(inv, h, HoldStatus.RELEASED)
            ref = h.booking.payment_ref
        self._gateway.refund(ref)

    # -- queries -------------------------------------------------------------------
    def available(self, show_id: str) -> set[str]:
        inv = self._inventory(show_id)
        with inv.lock:
            now = self._clock()
            return {s for s in inv.seats if inv.is_free(s, now)}

    def hold_status(self, hold_id: str) -> HoldStatus:
        inv, h = self._find_hold(hold_id)
        with inv.lock:
            if h.status is HoldStatus.HELD and not h.live(self._clock()):
                self._free(inv, h, HoldStatus.EXPIRED)
            return h.status

    # -- helpers -------------------------------------------------------------------
    @staticmethod
    def _free(inv: _ShowInventory, h: _Hold, status: HoldStatus) -> None:
        h.status = status
        for s in h.seat_ids:
            if inv.owner.get(s) is h:
                del inv.owner[s]

    def _inventory(self, show_id: str) -> _ShowInventory:
        with self._registry:
            if show_id not in self._shows:
                raise UnknownShow(show_id)
            return self._shows[show_id]

    def _find_hold(self, hold_id: str) -> tuple[_ShowInventory, _Hold]:
        with self._registry:
            show_id = self._hold_show.get(hold_id)
        if show_id is None:
            raise HoldNotFound(hold_id)
        inv = self._inventory(show_id)
        return inv, inv.holds[hold_id]

    def _next_id(self, prefix: str) -> str:
        with self._id_lock:
            return f"{prefix}{next(self._ids)}"


# ===================================================================== TESTS ==
class FakeClock:
    def __init__(self, t: float = 0.0) -> None:
        self.t = t

    def __call__(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class FakeGateway:
    def __init__(self) -> None:
        self.charges: dict[str, int] = {}        # idempotency key -> cents
        self.refunds: list[str] = []
        self.decline_next = False

    def charge(self, user: str, cents: int, idempotency_key: str) -> str:
        if self.decline_next:
            self.decline_next = False
            raise PaymentDeclined("card declined")
        self.charges.setdefault(idempotency_key, cents)
        return f"pay-{idempotency_key}"

    def refund(self, payment_ref: str) -> None:
        self.refunds.append(payment_ref)


PRICES = {SeatCategory.REGULAR: 1200, SeatCategory.PREMIUM: 2000}


def _show(show_id: str = "S1", n: int = 10, starts_at: float = 10_000) -> Show:
    seats = tuple(Seat(f"A{i}", SeatCategory.PREMIUM if i <= 2 else SeatCategory.REGULAR)
                  for i in range(1, n + 1))
    return Show(show_id, "Dune", starts_at, seats)


def _service(clock=None, gateway=None, **kw) -> BookingService:
    svc = BookingService(CategoryPricing(PRICES), gateway or FakeGateway(), clock or FakeClock(), **kw)
    svc.add_show(_show())
    return svc


def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc, fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def run_tests() -> bool:
    all_ok = True
    print("--- hold -> confirm ---")
    clock, gw = FakeClock(), FakeGateway()
    svc = _service(clock, gw)
    h = svc.hold("ann", "S1", ["A1", "A3", "A3"])
    all_ok &= _check("duplicate seat ids deduped; premium 2000 + regular 1200",
                     h.seat_ids == ("A1", "A3") and h.total_cents == 3200)
    all_ok &= _check("held seats are not available", {"A1", "A3"}.isdisjoint(svc.available("S1")))
    b = svc.confirm(h.id)
    all_ok &= _check("confirm charges once and returns a booking",
                     b.seat_ids == ("A1", "A3") and gw.charges == {h.id: 3200})
    all_ok &= _check("confirm again is idempotent (same booking)", svc.confirm(h.id) == b)

    print("\n--- all-or-nothing ---")
    try:
        svc.hold("bob", "S1", ["A2", "A3", "A4"])
        ok = False
    except SeatsUnavailable as e:
        ok = e.seat_ids == ["A3"]
    all_ok &= _check("request overlapping a booked seat fails, naming A3", ok)
    all_ok &= _check("...and A2, A4 were NOT partially held", {"A2", "A4"} <= svc.available("S1"))

    print("\n--- expiry is lazy ---")
    h2 = svc.hold("bob", "S1", ["A5"])
    clock.advance(599)
    all_ok &= _check("still held at 599 s", "A5" not in svc.available("S1"))
    clock.advance(1)
    all_ok &= _check("free exactly at expires_at (600 s)", "A5" in svc.available("S1"))
    all_ok &= _check("confirming an expired hold fails", _raises(HoldExpired, lambda: svc.confirm(h2.id)))
    h3 = svc.hold("cat", "S1", ["A5"])
    all_ok &= _check("someone else can hold the seat after expiry",
                     svc.hold_status(h2.id) is HoldStatus.EXPIRED and h3.seat_ids == ("A5",))

    print("\n--- payment declined, release, cancel ---")
    gw.decline_next = True
    all_ok &= _check("declined payment -> PaymentFailed", _raises(PaymentFailed, lambda: svc.confirm(h3.id)))
    all_ok &= _check("hold is back to HELD, seat still reserved",
                     svc.hold_status(h3.id) is HoldStatus.HELD and "A5" not in svc.available("S1"))
    b3 = svc.confirm(h3.id)
    all_ok &= _check("retry succeeds", b3.seat_ids == ("A5",))
    all_ok &= _check("release after confirm refused", _raises(BookingError, lambda: svc.release(h3.id)))
    svc.cancel(b3.id)
    all_ok &= _check("cancel frees the seat and refunds",
                     "A5" in svc.available("S1") and gw.refunds == [b3.payment_ref])
    all_ok &= _check("cancel twice refused", _raises(BookingError, lambda: svc.cancel(b3.id)))
    h4 = svc.hold("dan", "S1", ["A6"])
    svc.release(h4.id)
    all_ok &= _check("release frees immediately", "A6" in svc.available("S1"))
    clock.t = 10_000
    all_ok &= _check("cannot cancel after the show starts", _raises(BookingError, lambda: svc.cancel(b.id)))

    print("\n--- validation ---")
    svc = _service(max_seats=3)
    all_ok &= _check("unknown show", _raises(UnknownShow, lambda: svc.hold("u", "NOPE", ["A1"])))
    all_ok &= _check("unknown seat", _raises(UnknownSeat, lambda: svc.hold("u", "S1", ["Z9"])))
    all_ok &= _check("too many seats", _raises(TooManySeats, lambda: svc.hold("u", "S1", ["A1", "A2", "A3", "A4"])))
    all_ok &= _check("empty request", _raises(BookingError, lambda: svc.hold("u", "S1", [])))
    all_ok &= _check("unknown hold", _raises(HoldNotFound, lambda: svc.confirm("H999")))
    return all_ok
# ================================================================= END TESTS ==


class NaiveBooking:
    """Check-then-act without a lock; the 1 ms sleep stands in for a DB round trip."""

    def __init__(self, n: int) -> None:
        self.owner: dict[str, str] = {}
        self.seats = [f"A{i}" for i in range(n)]

    def hold(self, user: str, seat_ids: list[str]) -> bool:
        if any(s in self.owner for s in seat_ids):
            return False
        time.sleep(0.001)
        for s in seat_ids:
            self.owner[s] = user
        return True


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 40 users race for 60 seats, 3 seats per request ---")

    def race(hold_fn, n_seats: int) -> tuple[int, int]:
        """Returns (successful holds, seats claimed by more than one success)."""
        wins: list[tuple[str, tuple[str, ...]]] = []
        guard = threading.Lock()
        barrier = threading.Barrier(40)

        def user(uid: int) -> None:
            rng = random.Random(uid)
            barrier.wait()
            for _ in range(30):
                start = rng.randrange(n_seats - 2)
                seats = [f"A{start + i}" for i in range(3)]
                if hold_fn(f"u{uid}", seats):
                    with guard:
                        wins.append((f"u{uid}", tuple(seats)))

        threads = [threading.Thread(target=user, args=(i,)) for i in range(40)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        claimed: dict[str, int] = {}
        for _, seats in wins:
            for s in seats:
                claimed[s] = claimed.get(s, 0) + 1
        return len(wins), sum(1 for c in claimed.values() if c > 1)

    naive = NaiveBooking(60)
    n_wins, doubled = race(naive.hold, 60)
    print(f"      naive check-then-act: {n_wins} successful holds, {doubled} seats sold twice")

    svc = BookingService(CategoryPricing(PRICES), FakeGateway(), FakeClock())
    svc.add_show(Show("BIG", "Dune", 1e9, tuple(Seat(f"A{i}") for i in range(60))))

    def locked_hold(user, seats):
        try:
            svc.hold(user, "BIG", seats)
            return True
        except SeatsUnavailable:
            return False

    s_wins, s_doubled = race(locked_hold, 60)
    print(f"      per-show lock:        {s_wins} successful holds, {s_doubled} seats sold twice")
    all_ok &= _check("the lock never double-sells", s_doubled == 0 and 0 < s_wins <= 20)
    all_ok &= _check("the naive version double-sold at least one seat", doubled > 0)

    print("\n--- DEMO 2: 50,000 abandoned holds expire with no timer threads ---")
    clock = FakeClock()
    svc = BookingService(CategoryPricing(PRICES), FakeGateway(), clock, hold_ttl_s=600)
    for k in range(5):
        svc.add_show(Show(f"S{k}", "Dune", 1e9, tuple(Seat(f"A{i}") for i in range(10_000))))
    for k in range(5):
        for i in range(0, 10_000, 10):
            svc.hold(f"u{i}", f"S{k}", [f"A{i + j}" for j in range(10)])
    before = sum(len(svc.available(f"S{k}")) for k in range(5))
    clock.advance(600)
    start = time.perf_counter()
    after = sum(len(svc.available(f"S{k}")) for k in range(5))
    ms = (time.perf_counter() - start) * 1000
    print(f"      free seats: {before} while held -> {after} after TTL "
          f"(reclaimed lazily in {ms:.0f} ms, threads alive: {threading.active_count()})")
    all_ok &= _check("every seat is free again, no sweeper needed", before == 0 and after == 50_000)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
