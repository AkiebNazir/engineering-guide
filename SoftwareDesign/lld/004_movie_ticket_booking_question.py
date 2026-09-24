"""
================================================================================
LLD 004 · Movie Ticket Booking (BookMyShow / Ticketmaster)         [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement the seat-booking core of a movie ticketing service.

The interviewer says: "Design BookMyShow" and, when you ask, "focus on seat
selection and booking, not search." These are the agreed requirements.

REQUIREMENTS
------------
  1. A Show has a fixed tuple of Seats; each seat is REGULAR or PREMIUM.
     Price per seat comes from a pluggable pricing policy
     (CategoryPricing({category: cents}) is the one you must write).
  2. hold(user, show_id, seat_ids) -> HoldView
       * ALL-OR-NOTHING. If any seat is unavailable raise
         SeatsUnavailable(seat_ids=[the taken ones, in request order]) and
         hold nothing.
       * Duplicate ids in the request count once.
       * Errors: UnknownShow, UnknownSeat, TooManySeats (> max_seats),
         BookingError (empty request).
       * The hold expires hold_ttl_s after creation. At now >= expires_at the
         seats are free again. No background threads.
  3. confirm(hold_id) -> Booking
       * Charges gateway.charge(user, total_cents, idempotency_key=hold_id).
       * Calling confirm again on a confirmed hold returns the SAME booking and
         does not charge again.
       * Expired / released hold -> HoldExpired. Unknown hold -> HoldNotFound.
       * gateway raises PaymentDeclined -> raise PaymentFailed; the hold goes
         back to HELD (seats stay reserved until the original expiry).
       * A hold must not expire while its payment is in flight.
  4. release(hold_id): frees a HELD hold. Releasing a confirmed hold raises
     BookingError.
  5. cancel(booking_id): frees the seats and calls gateway.refund(payment_ref).
     BookingError if already cancelled or the show has started
     (clock() >= show.starts_at).
  6. available(show_id) -> set of seat ids free now.
     hold_status(hold_id) -> HoldStatus (reports EXPIRED once past expiry).
  7. Many threads call hold/confirm concurrently. A seat is never in two live
     holds or bookings.

  Out of scope: search, seat-map UI, discounts, waitlists.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * Where is the check-then-act race and what makes it atomic?
  * Lock granularity: global, per show, per seat? Why?
  * How do holds expire without a thread per hold?
  * What happens if the hold expires while the payment call is in flight?
  * Do you hold a lock across the payment call?
  * How does confirm stay idempotent under client retries?

FOLLOW-UPS TO PREPARE
---------------------
  a hot show with a million users · best-available adjacent seats ·
  dynamic pricing · waitlist on release · payment succeeded but commit crashed.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Protocol

Clock = Callable[[], float]


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
class PaymentDeclined(Exception): ...        # raised by the gateway


class SeatsUnavailable(BookingError):
    def __init__(self, seat_ids: list[str]) -> None:
        super().__init__(f"taken: {seat_ids}")
        self.seat_ids = seat_ids


class PaymentGateway(Protocol):
    def charge(self, user: str, cents: int, idempotency_key: str) -> str: ...
    def refund(self, payment_ref: str) -> None: ...


class CategoryPricing:
    def __init__(self, cents: dict[SeatCategory, int]) -> None:
        raise NotImplementedError

    def price(self, show: Show, seat: Seat) -> int:
        raise NotImplementedError


class BookingService:
    def __init__(self, pricing, gateway: PaymentGateway, clock: Clock = time.monotonic,
                 hold_ttl_s: float = 600, max_seats: int = 10) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def add_show(self, show: Show) -> None:
        raise NotImplementedError

    def hold(self, user: str, show_id: str, seat_ids: list[str]) -> HoldView:
        raise NotImplementedError

    def confirm(self, hold_id: str) -> Booking:
        raise NotImplementedError

    def release(self, hold_id: str) -> None:
        raise NotImplementedError

    def cancel(self, booking_id: str) -> None:
        raise NotImplementedError

    def available(self, show_id: str) -> set[str]:
        raise NotImplementedError

    def hold_status(self, hold_id: str) -> HoldStatus:
        raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
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


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
