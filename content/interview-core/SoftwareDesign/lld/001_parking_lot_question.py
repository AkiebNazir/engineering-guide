"""
================================================================================
LLD 001 · Parking Lot                                              [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement the software for a multi-floor parking lot.

The interviewer's opening line is just: "Design a parking lot." Everything
below is what a good candidate would pin down in the first five minutes —
read it as the agreed requirements. Before looking, try writing your own
list of clarifying questions and compare.

REQUIREMENTS
------------
  1. The lot has one or more floors. Each floor has some number of spots of
     each type: SMALL, COMPACT, LARGE (ordered by size).
  2. Vehicles are MOTORCYCLE (needs SMALL+), CAR (needs COMPACT+),
     TRUCK (needs LARGE). A vehicle may use any spot at least as large as
     its minimum.
  3. Operations:
        park(vehicle)       -> Ticket    raises LotFull / AlreadyParked
        unpark(ticket_id)   -> Receipt   raises InvalidTicket
        available(spot_type)-> int       free spots of that type, all floors
  4. Fee = hourly rate by vehicle type; partial hours round UP; minimum one
     hour. The pricing rule must be swappable (e.g. "first 15 minutes free").
  5. Which spot a vehicle gets must be swappable too. Default: the smallest
     compatible spot type, lowest floor first, lowest spot number first.
  6. Several gates call park/unpark concurrently from different threads.
     A spot must never be assigned twice; a plate must never be parked twice.
  7. Time comes from an injected clock (a zero-arg callable returning
     seconds) so fees can be tested without sleeping.

  Out of scope: payment processing, reservations, displays.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * Do vehicle types need to be classes?  (Think about whether behaviour or
    only data differs.)
  * How do you find a free spot without scanning every spot?
  * Which object owns "one spot, one vehicle"? Which owns "one ticket per
    plate"?
  * Where exactly is the check-then-act race, and what lock covers it?

FOLLOW-UPS TO PREPARE
---------------------
  EV charging spots · reservations · peak pricing · lost ticket ·
  a display board per floor · 50 lots sharing one backend database.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Everything inside the classes is yours to design. Add any helper classes you
want. Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Callable, Protocol

Clock = Callable[[], float]


class SpotType(IntEnum):
    SMALL = 1
    COMPACT = 2
    LARGE = 3


class VehicleType(Enum):
    MOTORCYCLE = SpotType.SMALL
    CAR = SpotType.COMPACT
    TRUCK = SpotType.LARGE

    @property
    def min_spot(self) -> SpotType:
        return self.value


@dataclass(frozen=True, slots=True)
class Vehicle:
    plate: str
    type: VehicleType


@dataclass(frozen=True, slots=True)
class Ticket:
    id: str
    plate: str
    vehicle_type: VehicleType
    floor: int
    spot_type: SpotType
    spot_no: int
    entry_time: float


@dataclass(frozen=True, slots=True)
class Receipt:
    ticket_id: str
    plate: str
    duration_s: float
    fee_cents: int


class ParkingError(Exception): ...
class LotFull(ParkingError): ...
class AlreadyParked(ParkingError): ...
class InvalidTicket(ParkingError): ...


class ParkingFloor:
    def __init__(self, number: int, spots: dict[SpotType, int]) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def claim(self, spot_type: SpotType) -> int | None:
        """Atomically take a free spot of this type; return its number or None."""
        raise NotImplementedError

    def release(self, spot_type: SpotType, spot_no: int) -> None:
        raise NotImplementedError

    def free_count(self, spot_type: SpotType) -> int:
        raise NotImplementedError


class BestFitLowestFloor:
    """Smallest compatible spot type first, then lowest floor."""
    # YOUR CODE HERE


class LowestFloorAnySize:
    """Lowest floor first, then any compatible spot type (smallest first)."""
    # YOUR CODE HERE


class HourlyPricing:
    def __init__(self, cents_per_hour: dict[VehicleType, int]) -> None:
        raise NotImplementedError

    def fee_cents(self, vehicle_type: VehicleType, entry: float, exit_: float) -> int:
        raise NotImplementedError


class GracePeriod:
    """Stays shorter than grace_s are free; otherwise defer to the wrapped policy."""

    def __init__(self, inner, grace_s: float) -> None:
        raise NotImplementedError

    def fee_cents(self, vehicle_type: VehicleType, entry: float, exit_: float) -> int:
        raise NotImplementedError


class ParkingLot:
    def __init__(self, floors: list[ParkingFloor], pricing, allocator=None,
                 clock: Clock = time.monotonic) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def park(self, vehicle: Vehicle) -> Ticket:
        raise NotImplementedError

    def unpark(self, ticket_id: str) -> Receipt:
        raise NotImplementedError

    def available(self, spot_type: SpotType) -> int:
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


RATES = {VehicleType.MOTORCYCLE: 100, VehicleType.CAR: 250, VehicleType.TRUCK: 600}


def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def run_tests() -> bool:
    all_ok = True
    print("--- basic park / unpark ---")
    clock = FakeClock()
    lot = ParkingLot(
        [ParkingFloor(0, {SpotType.SMALL: 1, SpotType.COMPACT: 2, SpotType.LARGE: 1}),
         ParkingFloor(1, {SpotType.COMPACT: 1})],
        HourlyPricing(RATES), clock=clock)
    t1 = lot.park(Vehicle("CAR-1", VehicleType.CAR))
    all_ok &= _check("car gets a COMPACT spot on floor 0", (t1.floor, t1.spot_type) == (0, SpotType.COMPACT))
    all_ok &= _check("available(COMPACT) drops to 2", lot.available(SpotType.COMPACT) == 2)
    clock.advance(61 * 60)
    r1 = lot.unpark(t1.id)
    all_ok &= _check("61 minutes rounds up to 2 hours = 500 cents", r1.fee_cents == 500)
    all_ok &= _check("spot returned to the pool", lot.available(SpotType.COMPACT) == 3)

    print("\n--- invariants and errors ---")
    t2 = lot.park(Vehicle("CAR-2", VehicleType.CAR))
    try:
        lot.park(Vehicle("CAR-2", VehicleType.CAR))
        ok = False
    except AlreadyParked:
        ok = True
    all_ok &= _check("same plate cannot park twice", ok)
    lot.unpark(t2.id)
    try:
        lot.unpark(t2.id)
        ok = False
    except InvalidTicket:
        ok = True
    all_ok &= _check("a ticket cannot be used twice", ok)

    print("\n--- size compatibility ---")
    small_lot = ParkingLot([ParkingFloor(0, {SpotType.SMALL: 2, SpotType.LARGE: 1})],
                           HourlyPricing(RATES), clock=FakeClock())
    truck_ticket = small_lot.park(Vehicle("TRUCK-1", VehicleType.TRUCK))
    try:
        small_lot.park(Vehicle("TRUCK-2", VehicleType.TRUCK))
        ok = False
    except LotFull:
        ok = True
    all_ok &= _check("truck can't use SMALL spots -> LotFull although SMALL spots are free",
                     ok and small_lot.available(SpotType.SMALL) == 2)
    m1 = small_lot.park(Vehicle("MOTO-1", VehicleType.MOTORCYCLE))
    all_ok &= _check("motorcycle takes smallest fitting spot", m1.spot_type == SpotType.SMALL)
    try:
        small_lot.park(Vehicle("CAR-9", VehicleType.CAR))
        ok = False
    except LotFull:
        ok = True
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  car can't fit: SMALL spots only, LARGE taken")


    small_lot.unpark(truck_ticket.id)
    t9 = small_lot.park(Vehicle("CAR-9", VehicleType.CAR))
    all_ok &= _check("failed park released the plate: same car parks once a spot frees up",
                     t9.spot_type == SpotType.LARGE)

    print("\n--- allocation strategy is pluggable ---")
    floors = lambda: [ParkingFloor(0, {SpotType.LARGE: 1}), ParkingFloor(1, {SpotType.COMPACT: 1})]
    best = ParkingLot(floors(), HourlyPricing(RATES), BestFitLowestFloor(), FakeClock())
    near = ParkingLot(floors(), HourlyPricing(RATES), LowestFloorAnySize(), FakeClock())
    tb = best.park(Vehicle("C", VehicleType.CAR))
    tn = near.park(Vehicle("C", VehicleType.CAR))
    all_ok &= _check("BestFit walks up to floor 1 COMPACT; LowestFloor takes floor 0 LARGE",
                     (tb.floor, tb.spot_type, tn.floor, tn.spot_type)
                     == (1, SpotType.COMPACT, 0, SpotType.LARGE))

    print("\n--- pricing strategies compose ---")
    graced = GracePeriod(HourlyPricing(RATES), grace_s=15 * 60)
    all_ok &= _check("10-minute stay free with grace period", graced.fee_cents(VehicleType.CAR, 0, 600) == 0)
    all_ok &= _check("exactly 60 minutes = 1 hour", graced.fee_cents(VehicleType.CAR, 0, 3600) == 250)
    all_ok &= _check("clock going backwards never yields a negative fee",
                     HourlyPricing(RATES).fee_cents(VehicleType.TRUCK, 100, 50) == 600)
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
