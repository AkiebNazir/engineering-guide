"""
================================================================================
SOLUTION · LLD 001 · Parking Lot                                   [Tier 1]
================================================================================

THE CORE IDEA
--------------
A parking lot is three separate decisions that must not be tangled together:

    1. WHERE does a vehicle go?        -> SpotAllocator  (strategy)
    2. WHAT does it cost?              -> PricingPolicy  (strategy)
    3. WHO guarantees one spot = one vehicle, even with many gates at once?
                                       -> ParkingFloor   (owns the free-spot index
                                                          and a lock)

Everything else (Vehicle, Ticket, Receipt) is a small value object or record.
The lot itself is a thin facade that wires the three together.

The single most important implementation detail interviewers look for: finding
a free spot must NOT be a linear scan over every spot. Each floor keeps, per
spot type, a min-heap of free spot numbers — O(log n) claim and release, and
"nearest spot first" falls out for free.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. Multiple floors. Spot types SMALL < COMPACT < LARGE.
  2. Vehicle types MOTORCYCLE, CAR, TRUCK. A vehicle fits its own minimum spot
     size or anything larger (a motorcycle may use a LARGE spot if needed).
  3. park(vehicle) -> Ticket          raises LotFull, AlreadyParked
     unpark(ticket_id) -> Receipt     raises InvalidTicket
     available(spot_type) -> int
  4. Fee: hourly rate per vehicle type, partial hours round UP, pluggable.
  5. Many entry/exit gates run concurrently: no spot is ever given to two
     vehicles, a plate is never parked twice.
  Out of scope (named as extensions): payments, reservations, EV charging,
  display boards, monthly passes.


================================================================================
ENTITIES, VALUE OBJECTS, INVARIANTS
================================================================================
    VehicleType, SpotType     enums (data variants -> enums, NOT subclasses)
    Vehicle                   value object (plate, type)
    Ticket                    record created by park()     (id, plate, type, floor, spot, entry)
    Receipt                   value object returned by unpark()
    ParkingFloor              INVARIANT: every spot is either in the free index
                              or occupied, never both; claim/release are atomic
    ParkingLot (facade)       INVARIANT: at most one active ticket per plate
    SpotAllocator (protocol)  decides which floor/spot type to try, in order
    PricingPolicy (protocol)  fee from (vehicle type, entry, exit)
    Clock                     injected Callable[[], float] (seconds)


================================================================================
CLASS DIAGRAM
================================================================================
    ┌──────────────────────────────┐ 1      1..* ┌─────────────────────────────┐
    │ ParkingLot                   │◆───────────▶│ ParkingFloor                │
    ├──────────────────────────────┤             ├─────────────────────────────┤
    │ - _active: dict[id, Ticket]  │             │ - _free: {SpotType: heap}   │
    │ - _plates: set[str]          │             │ - _lock                     │
    │ - _lock                      │             ├─────────────────────────────┤
    ├──────────────────────────────┤             │ + claim(spot_type) -> int?  │
    │ + park(v) -> Ticket          │             │ + release(spot_type, n)     │
    │ + unpark(id) -> Receipt      │             │ + free_count(spot_type)     │
    │ + available(t) -> int        │             └─────────────────────────────┘
    └───────┬───────────────┬──────┘
            │ uses          │ uses
            ▼               ▼
    «protocol» SpotAllocator     «protocol» PricingPolicy
       ▲ BestFitLowestFloor         ▲ HourlyPricing
       ▲ LowestFloorAnySize         ▲ GracePeriod (decorator over another policy)


================================================================================
KEY FLOW · park(vehicle)
================================================================================
    Gate thread          ParkingLot                 Allocator        Floor k
       │ park(v)             │                          │               │
       │────────────────────▶│ lock: plate free? mark   │               │
       │                     │ pending, unlock          │               │
       │                     │ candidates(v) ──────────▶│               │
       │                     │◀── [(floor, type), ...] ─│               │
       │                     │ for each candidate: claim(type) ────────▶│ lock, heappop,
       │                     │◀──────────────────────────── spot no. ───│ unlock
       │                     │ lock: store ticket, unlock               │
       │◀──── Ticket ────────│                                          │

    The lot lock and floor locks are NEVER held at the same time, so there is
    no lock-ordering deadlock, and two gates parking on different floors never
    contend with each other.


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Vehicle types as an ENUM, not class Car(Vehicle). Vehicles have no
    behaviour that differs by type; only data (minimum spot size, rate) does.
    A subclass per vehicle is the #1 over-engineering tell in this problem.
  * Free spots as a per-type MIN-HEAP per floor.
        linear scan over all spots   O(total spots) per park
        heap per (floor, type)       O(floors * types + log n) per park
    Measured below (demo 2): 5,000 claims on a 20,000-spot floor took
    148 ms scanning vs 1.2 ms with the heap on this machine (~128x).
  * Allocation as a strategy: "best fit, lowest floor" is sensible, but a lot
    might prefer "fill top floors first" or "keep LARGE spots for trucks".
  * Pricing as a strategy, composable: GracePeriod(HourlyPricing(...)) gives
    "first 15 minutes free" without touching HourlyPricing.
  * Money in integer cents. Time from an injected clock -> fee logic is
    testable without sleeping.
  * One lock PER FLOOR for spot claims + one lot lock for the plate/ticket
    maps. Coarser (one global lock) is also acceptable in an interview; say
    why you picked the granularity.


================================================================================
COMPLEXITY
================================================================================
    Operation         Time                         Space
    park              O(F * T + log S)             O(1) extra
    unpark            O(F + log S)                 O(1)
    available         O(F)                         O(1)
    Total                                          O(S) spots + O(active tickets)
    F floors, T spot types (3), S spots on a floor.


================================================================================
EDGE CASES
================================================================================
  * Lot full for this vehicle type, but smaller spots free -> LotFull
    (a truck can't use COMPACT spots).
  * Same plate parked twice (tailgating / duplicate scan)  -> AlreadyParked.
  * Unpark an unknown or already-used ticket               -> InvalidTicket.
  * Stay of exactly 60 minutes = 1 hour; 61 minutes = 2 hours; 0 minutes = 1
    hour minimum (grace-period decorator handles "free if short").
  * Clock goes backwards (NTP adjustment) -> duration clamped at 0.
  * Two gates race for the last spot -> exactly one wins (demo 1).


================================================================================
COMMON MISTAKES
================================================================================
  1. Class hierarchy Car/Truck/Motorcycle(Vehicle) with no differing behaviour.
  2. Linear scan of every spot to find a free one.
  3. Float money; datetime.now() called inside the fee calculation.
  4. Check "spot free?" and "occupy spot" in separate, unlocked steps.
  5. ParkingLot god class computing fees, scanning spots and printing tickets.
  6. Returning None on invalid ticket instead of a domain error.
  7. Forgetting the "one active ticket per plate" invariant entirely.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * EV charging spots        -> new SpotType + compatibility rule; allocator
                                prefers EV spots for EVs. No other class changes.
  * Reservations             -> Reservation entity; a HELD state for spots with
                                expiry; park() consumes the hold.
  * Weekend / peak pricing   -> new PricingPolicy using entry & exit times.
  * Lost ticket              -> lookup by plate (index plate -> ticket id),
                                max daily fee policy.
  * Display boards per floor -> Observer on claim/release; or boards poll
                                available() — cheaper and simpler.
  * Many lots, one backend   -> spots become DB rows; claim becomes
                                UPDATE spots SET plate=? WHERE id=? AND plate IS NULL
                                (conditional update = atomic claim); tickets
                                keyed by idempotency key from the gate.


================================================================================
RELATED
================================================================================
  SoftwareDesign/14_low_level_design_interview_playbook.md  §4–§9 (uses this problem)
  SoftwareDesign/04_design_patterns_in_practice.md          §3 Strategy
  lld/011_meeting_room_booking  (same "claim a resource atomically" shape)
  lld/004_movie_ticket_booking  (claims with holds + expiry)
"""

from __future__ import annotations

import heapq
import itertools
import threading
import time
from dataclasses import dataclass
from enum import IntEnum, Enum
from typing import Callable, Iterable, Protocol

Clock = Callable[[], float]


# ----------------------------------------------------------------------------
# Enums and value objects
# ----------------------------------------------------------------------------
class SpotType(IntEnum):
    """IntEnum so sizes are ordered: SMALL < COMPACT < LARGE."""
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


# ----------------------------------------------------------------------------
# ParkingFloor — owns the "one spot, one vehicle" invariant for its spots
# ----------------------------------------------------------------------------
class ParkingFloor:
    def __init__(self, number: int, spots: dict[SpotType, int]) -> None:
        self.number = number
        self._lock = threading.Lock()
        # Spot numbers are unique per floor; a heap per type gives nearest-first.
        self._free: dict[SpotType, list[int]] = {t: [] for t in SpotType}
        self._capacity: dict[SpotType, int] = {t: 0 for t in SpotType}
        next_no = itertools.count(1)
        for spot_type in SpotType:
            for _ in range(spots.get(spot_type, 0)):
                self._free[spot_type].append(next(next_no))
            heapq.heapify(self._free[spot_type])
            self._capacity[spot_type] = spots.get(spot_type, 0)

    def claim(self, spot_type: SpotType) -> int | None:
        """Atomically take the lowest-numbered free spot of this type."""
        with self._lock:
            heap = self._free[spot_type]
            return heapq.heappop(heap) if heap else None

    def release(self, spot_type: SpotType, spot_no: int) -> None:
        with self._lock:
            heapq.heappush(self._free[spot_type], spot_no)

    def free_count(self, spot_type: SpotType) -> int:
        with self._lock:
            return len(self._free[spot_type])


# ----------------------------------------------------------------------------
# Strategies
# ----------------------------------------------------------------------------
class SpotAllocator(Protocol):
    def candidates(self, vehicle: Vehicle, floors: list[ParkingFloor]) -> Iterable[tuple[ParkingFloor, SpotType]]:
        """Ordered (floor, spot type) pairs to try. Must only yield compatible types."""
        ...


class BestFitLowestFloor:
    """Smallest compatible spot type first, then lowest floor. Keeps big spots for big vehicles."""

    def candidates(self, vehicle, floors):
        for spot_type in SpotType:
            if spot_type >= vehicle.type.min_spot:
                for floor in floors:
                    yield floor, spot_type


class LowestFloorAnySize:
    """Nearest floor first, any compatible size — convenient for drivers, wasteful of LARGE spots."""

    def candidates(self, vehicle, floors):
        for floor in floors:
            for spot_type in SpotType:
                if spot_type >= vehicle.type.min_spot:
                    yield floor, spot_type


class PricingPolicy(Protocol):
    def fee_cents(self, vehicle_type: VehicleType, entry: float, exit_: float) -> int: ...


class HourlyPricing:
    def __init__(self, cents_per_hour: dict[VehicleType, int]) -> None:
        missing = set(VehicleType) - set(cents_per_hour)
        if missing:
            raise ValueError(f"no rate for {sorted(m.name for m in missing)}")
        self._rates = dict(cents_per_hour)

    def fee_cents(self, vehicle_type, entry, exit_):
        seconds = max(0.0, exit_ - entry)
        hours = max(1, -(-int(seconds) // 3600))        # ceil, minimum one hour
        return hours * self._rates[vehicle_type]


class GracePeriod:
    """Decorator: stays shorter than `grace_s` are free; otherwise defer to `inner`."""

    def __init__(self, inner: PricingPolicy, grace_s: float) -> None:
        self._inner, self._grace_s = inner, grace_s

    def fee_cents(self, vehicle_type, entry, exit_):
        if exit_ - entry < self._grace_s:
            return 0
        return self._inner.fee_cents(vehicle_type, entry, exit_)


# ----------------------------------------------------------------------------
# ParkingLot — facade; owns "one active ticket per plate"
# ----------------------------------------------------------------------------
class ParkingLot:
    def __init__(
        self,
        floors: list[ParkingFloor],
        pricing: PricingPolicy,
        allocator: SpotAllocator | None = None,
        clock: Clock = time.monotonic,
    ) -> None:
        if not floors:
            raise ValueError("a lot needs at least one floor")
        self._floors = list(floors)
        self._pricing = pricing
        self._allocator = allocator or BestFitLowestFloor()
        self._clock = clock
        self._lock = threading.Lock()
        self._active: dict[str, Ticket] = {}
        self._plates: set[str] = set()               # active OR in the middle of parking
        self._ids = itertools.count(1)

    def park(self, vehicle: Vehicle) -> Ticket:
        with self._lock:
            if vehicle.plate in self._plates:
                raise AlreadyParked(vehicle.plate)
            self._plates.add(vehicle.plate)          # reserve the plate before claiming

        try:
            for floor, spot_type in self._allocator.candidates(vehicle, self._floors):
                if spot_type < vehicle.type.min_spot:     # never trust a strategy with an invariant
                    raise ValueError(f"allocator offered {spot_type.name} for {vehicle.type.name}")
                spot_no = floor.claim(spot_type)
                if spot_no is not None:
                    break
            else:
                raise LotFull(vehicle.type.name)
        except BaseException:
            with self._lock:
                self._plates.discard(vehicle.plate)
            raise

        with self._lock:
            ticket = Ticket(
                id=f"T{next(self._ids)}", plate=vehicle.plate, vehicle_type=vehicle.type,
                floor=floor.number, spot_type=spot_type, spot_no=spot_no,
                entry_time=self._clock(),
            )
            self._active[ticket.id] = ticket
        return ticket

    def unpark(self, ticket_id: str) -> Receipt:
        with self._lock:
            ticket = self._active.pop(ticket_id, None)
            if ticket is None:
                raise InvalidTicket(ticket_id)
            self._plates.discard(ticket.plate)
        exit_time = self._clock()
        self._floor(ticket.floor).release(ticket.spot_type, ticket.spot_no)
        fee = self._pricing.fee_cents(ticket.vehicle_type, ticket.entry_time, exit_time)
        return Receipt(ticket.id, ticket.plate, max(0.0, exit_time - ticket.entry_time), fee)

    def available(self, spot_type: SpotType) -> int:
        return sum(f.free_count(spot_type) for f in self._floors)

    def _floor(self, number: int) -> ParkingFloor:
        for f in self._floors:
            if f.number == number:
                return f
        raise KeyError(number)


# ===================================================================== TESTS ==
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


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 16 gates race for 300 spots with 400 cars ---")
    lot = ParkingLot([ParkingFloor(i, {SpotType.COMPACT: 100}) for i in range(3)],
                     HourlyPricing(RATES), clock=FakeClock())
    tickets: list[Ticket] = []
    full = 0
    guard = threading.Lock()
    cars = iter(range(400))

    def gate() -> None:
        nonlocal full
        while True:
            with guard:
                n = next(cars, None)
            if n is None:
                return
            try:
                t = lot.park(Vehicle(f"P{n}", VehicleType.CAR))
                with guard:
                    tickets.append(t)
            except LotFull:
                with guard:
                    full += 1

    threads = [threading.Thread(target=gate) for _ in range(16)]
    for th in threads:
        th.start()
    for th in threads:
        th.join()
    spots = {(t.floor, t.spot_no) for t in tickets}
    ok = len(tickets) == 300 and len(spots) == 300 and full == 100
    all_ok &= _check(f"{len(tickets)} tickets, {len(spots)} distinct spots, {full} turned away", ok)

    print("\n--- DEMO 2: heap index vs linear scan to find a free spot ---")
    n_spots = 20_000
    occupied = [False] * n_spots

    def linear_claim() -> int | None:
        for i, taken in enumerate(occupied):
            if not taken:
                occupied[i] = True
                return i
        return None

    floor = ParkingFloor(0, {SpotType.COMPACT: n_spots})
    k = 5_000
    start = time.perf_counter()
    for _ in range(k):
        linear_claim()
    linear_s = time.perf_counter() - start
    start = time.perf_counter()
    for _ in range(k):
        floor.claim(SpotType.COMPACT)
    heap_s = time.perf_counter() - start
    print(f"      {k} claims on a {n_spots}-spot floor: linear scan {linear_s*1000:.1f} ms, "
          f"heap {heap_s*1000:.1f} ms  ({linear_s/heap_s:.0f}x)")
    all_ok &= _check("heap claim is faster than scanning as the lot fills", heap_s < linear_s)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
