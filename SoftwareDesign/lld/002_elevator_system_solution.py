"""
================================================================================
SOLUTION · LLD 002 · Elevator System                               [Tier 1]
================================================================================

THE CORE IDEA
--------------
An elevator bank is two decisions made by two different owners:

    1. WHICH CAR answers a hall call ("someone on floor 7 pressed UP")?
                                  -> Dispatcher (strategy, owned by the system)
    2. IN WHAT ORDER does one car visit its stops?
                                  -> ElevatorCar (state machine running LOOK)

A car call ("I'm inside, take me to 3") never goes through the dispatcher —
it already belongs to one car. Mixing the two is the classic muddle.

LOOK is the disk-arm algorithm applied to floors: keep going in the current
direction while there is anything ahead; then reverse. It never starves a
request and travels at most ~2 x (floors) per sweep, where serving requests
in arrival order (FCFS) zig-zags across the building (demo 2).

A hall call carries a DIRECTION. A car going down does not stop for someone
who pressed UP — unless nothing is left below, in which case it turns around
there. Getting this one rule right is what separates a strong answer.

Time is a discrete tick (`step()`), so the whole simulation is deterministic
and testable without sleeping. One lock makes the controller single-writer.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. N cars, floors 0..F-1.
  2. Hall calls (floor, UP/DOWN) are assigned to exactly one car by a
     pluggable dispatcher; the chosen car id is returned.
  3. Car calls (car id, floor) go straight to that car.
  4. Each car serves stops with LOOK and respects hall-call direction.
  5. step() advances time one tick: every car either moves one floor, or opens
     its doors at a stop (serving it), or stays idle.
  6. Observers are told about every arrival (displays, logging, metrics).
  7. A car can be taken out of service; its hall calls are re-dispatched.
  8. Requests may come from many threads while the simulation is stepping.
  Out of scope: weight/capacity, door timing, acceleration, fire mode.


================================================================================
ENTITIES, VALUE OBJECTS, INVARIANTS
================================================================================
    Direction          enum DOWN=-1, IDLE=0, UP=1 (value doubles as a floor delta)
    CallKind           enum CAR, HALL_UP, HALL_DOWN
    Arrival            value object (tick, car_id, floor, served calls)
    ElevatorCar        INVARIANT: moves at most one floor per tick; never passes a
                       floor holding a CAR call or a same-direction hall call;
                       direction is IDLE iff it has no pending stops
    ElevatorSystem     INVARIANT: every pending hall call (floor, dir) is owned by
                       exactly one in-service car
    Dispatcher         protocol: choose(cars, floor, direction) -> car
       NearestCar      distance only (simple, wrong when the car is heading away)
       LookCost        estimated floors-to-arrival under LOOK (default)


================================================================================
CLASS DIAGRAM
================================================================================
    ┌──────────────────────────────────┐ 1   1..* ┌───────────────────────────────┐
    │ ElevatorSystem                   │◆────────▶│ ElevatorCar                   │
    ├──────────────────────────────────┤          ├───────────────────────────────┤
    │ - _hall_owner: {(floor,dir): id} │          │ - floor, direction            │
    │ - _listeners: [callable]         │          │ - _pending: {floor: {CallKind}}│
    │ - _lock                          │          ├───────────────────────────────┤
    ├──────────────────────────────────┤          │ + add_call(floor, kind)       │
    │ + request_hall(floor, dir) -> id │          │ + step() -> served calls?     │
    │ + request_car(car_id, floor)     │          │ + eta(floor, dir) -> int      │
    │ + step() -> [Arrival]            │          └───────────────────────────────┘
    │ + take_out_of_service(car_id)    │
    │ + subscribe(listener)            │───uses──▶ «protocol» Dispatcher
    └──────────────────────────────────┘              ▲ NearestCar  ▲ LookCost


================================================================================
KEY FLOW · one car, one tick (LOOK)
================================================================================
    pending empty? ────────────────────────────▶ direction = IDLE, done
    IDLE?  calls on this floor ─▶ serve them all, done
           else head toward the nearest pending floor
    calls here that match   { CAR, HALL in my direction } ─▶ serve (doors open)
    nothing ahead of me     ─▶ serve every call here (turnaround)
    served?  ─▶ keep direction if work ahead, else reverse if work behind, else IDLE
    not served ─▶ floor += direction

    Trace: car at 0, calls: CAR 5, HALL_DOWN 3, HALL_UP 2
      t1..t2  move 0→2          t3  open at 2 (HALL_UP matches UP)
      t4      move 2→3          t5  pass? HALL_DOWN at 3 while going UP and
                                    5 is ahead -> do NOT stop, move 3→4
      t6      move 4→5          t7  open at 5 (CAR); nothing above, 3 below
                                    -> direction DOWN
      t8..t9  move 5→3          t10 open at 3 (HALL_DOWN matches DOWN) -> IDLE


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Discrete ticks instead of threads-per-car with sleep(). Deterministic,
    replayable, testable. A real controller runs the same step() on a timer.
  * State = (floor, direction, pending). A full State-pattern class hierarchy
    (Idle/MovingUp/MovingDown/DoorsOpen) is defensible but here each state's
    behaviour is one branch of the same LOOK rule — an enum is enough. Say so.
  * Dispatcher as strategy. NearestCar is the naive answer; LookCost estimates
    real arrival distance, including the detour a car must finish before it can
    turn around. Tests show where they disagree.
  * Hall-call ownership lives in the SYSTEM (one owner per (floor, direction)),
    so duplicate presses return the same car and out-of-service reassignment is
    a dictionary scan, not a search through every car.
  * Observers are called AFTER the lock is released, and an exception in one
    listener never breaks the controller or the other listeners.
  * One controller lock (single writer). Contention is irrelevant at elevator
    request rates; correctness is not.


================================================================================
COMPLEXITY
================================================================================
    Operation             Time                     Space
    request_hall          O(C * P)  (eta per car)  O(1)
    request_car           O(1)                     O(1)
    step                  O(C * P)                 O(1)
    C cars, P pending floors per car (bounded by F).


================================================================================
EDGE CASES
================================================================================
  * Hall call at the idle car's own floor -> doors open next tick, no movement.
  * Same hall button pressed twice -> same car, no duplicate stop.
  * HALL_UP on the top floor / HALL_DOWN on floor 0 -> InvalidRequest.
  * Car heading away from the caller -> LookCost prefers a farther idle car.
  * Opposite-direction call with nothing beyond it -> car turns around there.
  * Car taken out of service with assigned hall calls -> re-dispatched.
  * Listener raises -> logged and ignored; simulation continues.


================================================================================
COMMON MISTAKES
================================================================================
  1. One global queue served FCFS: starvation-free but travels many times farther.
  2. Ignoring hall-call direction: a down-bound car picks up an UP passenger
     and takes them the wrong way.
  3. Routing car calls through the dispatcher (they belong to one car already).
  4. A thread per car with time.sleep(): untestable and racy.
  5. Dispatch by distance only.
  6. Calling observers while holding the controller lock (a slow display
     stalls every elevator; a re-entrant call deadlocks).
  7. Separate classes per direction with duplicated movement logic.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Capacity / weight sensor  -> car reports FULL; LookCost returns infinity
                                 for full cars on hall calls.
  * Express / zoned cars      -> car has a set of served floors; dispatcher
                                 filters by it. No change to LOOK.
  * Peak-hour lobby mode      -> new Dispatcher that parks idle cars at floor 0.
  * Destination dispatch      -> hall panel takes the destination; the request
                                 becomes (from, to) and the dispatcher groups
                                 passengers by destination.
  * Fire / emergency mode     -> system-level mode that clears all calls and
                                 sends every car to the lobby (Command).
  * Real time + doors         -> DOORS_OPEN state lasting k ticks; door-hold
                                 button extends it.


================================================================================
RELATED
================================================================================
  SoftwareDesign/04_design_patterns_in_practice.md   §3 Strategy, §7 Observer, §9 State
  SoftwareDesign/02_oop_and_domain_modeling.md       §10 Modeling state and lifecycles
  SoftwareDesign/14_low_level_design_interview_playbook.md  §9 concurrency
  lld/003_vending_machine  (explicit State pattern, contrast with this enum)
"""

from __future__ import annotations

import random
import threading
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Callable, Protocol


# ----------------------------------------------------------------------------
# Enums, value objects, errors
# ----------------------------------------------------------------------------
class Direction(IntEnum):
    DOWN = -1
    IDLE = 0
    UP = 1


class CallKind(Enum):
    CAR = "car"
    HALL_UP = "hall_up"
    HALL_DOWN = "hall_down"

    @staticmethod
    def hall(direction: Direction) -> CallKind:
        return CallKind.HALL_UP if direction is Direction.UP else CallKind.HALL_DOWN


@dataclass(frozen=True, slots=True)
class Arrival:
    tick: int
    car_id: int
    floor: int
    served: frozenset[CallKind]


class InvalidRequest(ValueError): ...


# ----------------------------------------------------------------------------
# ElevatorCar — one car, LOOK scheduling
# ----------------------------------------------------------------------------
class ElevatorCar:
    def __init__(self, car_id: int, floor: int = 0) -> None:
        self.id = car_id
        self.floor = floor
        self.direction = Direction.IDLE
        self._pending: dict[int, set[CallKind]] = {}

    # -- queries ---------------------------------------------------------------
    @property
    def pending_floors(self) -> list[int]:
        return sorted(self._pending)

    def has_pending(self) -> bool:
        return bool(self._pending)

    def _ahead(self, direction: Direction) -> bool:
        return any((f - self.floor) * direction > 0 for f in self._pending)

    def eta(self, floor: int, direction: Direction) -> int:
        """Floors the car travels before it could open at `floor` for `direction`."""
        if self.direction is Direction.IDLE:
            return abs(floor - self.floor)
        d = self.direction
        heading_to_it = (floor - self.floor) * d >= 0
        if heading_to_it and direction in (d, Direction.IDLE):
            return abs(floor - self.floor)
        # Finish the sweep to the farthest stop ahead, then come back.
        ahead = [f for f in self._pending if (f - self.floor) * d > 0]
        turn = max(ahead, key=lambda f: abs(f - self.floor)) if ahead else self.floor
        return abs(turn - self.floor) + abs(turn - floor)

    # -- commands --------------------------------------------------------------
    def add_call(self, floor: int, kind: CallKind) -> None:
        self._pending.setdefault(floor, set()).add(kind)

    def remove_hall_calls(self) -> list[tuple[int, CallKind]]:
        taken = []
        for floor in list(self._pending):
            calls = self._pending[floor]
            for kind in (CallKind.HALL_UP, CallKind.HALL_DOWN):
                if kind in calls:
                    calls.discard(kind)
                    taken.append((floor, kind))
            if not calls:
                del self._pending[floor]
        return taken

    def step(self) -> frozenset[CallKind] | None:
        """Advance one tick. Returns the calls served if the doors opened, else None."""
        if not self._pending:
            self.direction = Direction.IDLE
            return None
        if self.direction is Direction.IDLE:
            if self.floor in self._pending:
                return self._serve(set(self._pending[self.floor]))
            nearest = min(self._pending, key=lambda f: (abs(f - self.floor), f))
            self.direction = Direction.UP if nearest > self.floor else Direction.DOWN

        calls = self._pending.get(self.floor, set())
        take = calls & {CallKind.CAR, CallKind.hall(self.direction)}
        if calls and not self._ahead(self.direction):
            take = set(calls)                     # nothing beyond: turn around here
        if take:
            return self._serve(take)
        self.floor += self.direction
        return None

    def _serve(self, take: set[CallKind]) -> frozenset[CallKind]:
        calls = self._pending[self.floor]
        calls -= take
        if not calls:
            del self._pending[self.floor]
        if self.direction is not Direction.IDLE and not self._ahead(self.direction):
            back = Direction(-self.direction)
            self.direction = back if self._ahead(back) else Direction.IDLE
        if not self._pending:
            self.direction = Direction.IDLE
        return frozenset(take)


# ----------------------------------------------------------------------------
# Dispatch strategies
# ----------------------------------------------------------------------------
class Dispatcher(Protocol):
    def choose(self, cars: list[ElevatorCar], floor: int, direction: Direction) -> ElevatorCar: ...


class NearestCar:
    """Closest car by distance. Ignores where the car is going."""

    def choose(self, cars, floor, direction):
        return min(cars, key=lambda c: (abs(c.floor - floor), c.id))


class LookCost:
    """Car with the fewest floors to travel before it can serve the call."""

    def choose(self, cars, floor, direction):
        return min(cars, key=lambda c: (c.eta(floor, direction), c.id))


# ----------------------------------------------------------------------------
# ElevatorSystem — single-writer controller
# ----------------------------------------------------------------------------
Listener = Callable[[Arrival], None]


class ElevatorSystem:
    def __init__(self, n_cars: int, n_floors: int, dispatcher: Dispatcher | None = None) -> None:
        if n_cars < 1 or n_floors < 2:
            raise ValueError("need at least one car and two floors")
        self.n_floors = n_floors
        self._cars = [ElevatorCar(i) for i in range(n_cars)]
        self._in_service = set(range(n_cars))
        self._dispatcher = dispatcher or LookCost()
        self._hall_owner: dict[tuple[int, Direction], int] = {}
        self._listeners: list[Listener] = []
        self._lock = threading.Lock()
        self._tick = 0
        self.listener_errors = 0

    # -- requests --------------------------------------------------------------
    def request_hall(self, floor: int, direction: Direction) -> int:
        self._check_floor(floor)
        if direction is Direction.IDLE:
            raise InvalidRequest("hall call needs UP or DOWN")
        if (direction is Direction.UP and floor == self.n_floors - 1) or \
           (direction is Direction.DOWN and floor == 0):
            raise InvalidRequest(f"no {direction.name} button on floor {floor}")
        with self._lock:
            return self._assign_hall(floor, direction)

    def request_car(self, car_id: int, floor: int) -> None:
        self._check_floor(floor)
        with self._lock:
            self._car(car_id).add_call(floor, CallKind.CAR)

    def take_out_of_service(self, car_id: int) -> list[tuple[int, Direction, int]]:
        """Remove a car from dispatch. Returns (floor, direction, new_car_id) reassignments."""
        with self._lock:
            car = self._car(car_id)
            if len(self._in_service) == 1:
                raise InvalidRequest("cannot take the last car out of service")
            self._in_service.discard(car_id)
            moved = []
            for floor, kind in car.remove_hall_calls():
                direction = Direction.UP if kind is CallKind.HALL_UP else Direction.DOWN
                del self._hall_owner[(floor, direction)]
                moved.append((floor, direction, self._assign_hall(floor, direction)))
            return moved

    def subscribe(self, listener: Listener) -> None:
        with self._lock:
            self._listeners.append(listener)

    # -- time --------------------------------------------------------------------
    def step(self) -> list[Arrival]:
        with self._lock:
            self._tick += 1
            arrivals = []
            for car in self._cars:
                served = car.step()
                if served is None:
                    continue
                for kind in served:
                    if kind is not CallKind.CAR:
                        d = Direction.UP if kind is CallKind.HALL_UP else Direction.DOWN
                        self._hall_owner.pop((car.floor, d), None)
                arrivals.append(Arrival(self._tick, car.id, car.floor, served))
            listeners = list(self._listeners)
        for arrival in arrivals:                  # outside the lock
            for listener in listeners:
                try:
                    listener(arrival)
                except Exception:
                    self.listener_errors += 1
        return arrivals

    def run_until_idle(self, max_ticks: int = 100_000) -> list[Arrival]:
        out: list[Arrival] = []
        for _ in range(max_ticks):
            with self._lock:
                busy = any(c.has_pending() for c in self._cars)
            if not busy:
                return out
            out.extend(self.step())
        raise RuntimeError("did not become idle")

    def status(self) -> list[tuple[int, int, Direction]]:
        with self._lock:
            return [(c.id, c.floor, c.direction) for c in self._cars]

    # -- helpers ---------------------------------------------------------------
    def _assign_hall(self, floor: int, direction: Direction) -> int:
        key = (floor, direction)
        if key in self._hall_owner:
            return self._hall_owner[key]
        candidates = [c for c in self._cars if c.id in self._in_service]
        car = self._dispatcher.choose(candidates, floor, direction)
        car.add_call(floor, CallKind.hall(direction))
        self._hall_owner[key] = car.id
        return car.id

    def _car(self, car_id: int) -> ElevatorCar:
        if not 0 <= car_id < len(self._cars):
            raise InvalidRequest(f"no car {car_id}")
        return self._cars[car_id]

    def _check_floor(self, floor: int) -> None:
        if not 0 <= floor < self.n_floors:
            raise InvalidRequest(f"floor {floor} outside 0..{self.n_floors - 1}")


# ===================================================================== TESTS ==
def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc: type[BaseException], fn: Callable[[], object]) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def _place(system: ElevatorSystem, car_id: int, floor: int) -> None:
    """Test helper: drive an idle car to `floor` with a car call."""
    system.request_car(car_id, floor)
    system.run_until_idle()


def run_tests() -> bool:
    all_ok = True
    print("--- LOOK order and hall-call direction (the trace in the docstring) ---")
    s = ElevatorSystem(1, 10)
    s.request_car(0, 5)
    s.request_hall(3, Direction.DOWN)
    s.request_hall(2, Direction.UP)
    arrivals = s.run_until_idle()
    all_ok &= _check("visits 2 (UP), 5 (car), then 3 (DOWN) — skips 3 on the way up",
                     [a.floor for a in arrivals] == [2, 5, 3])
    all_ok &= _check("arrival ticks are 3, 7, 10", [a.tick for a in arrivals] == [3, 7, 10])
    all_ok &= _check("idle afterwards", s.status() == [(0, 3, Direction.IDLE)])

    print("\n--- turnaround at an opposite-direction call with nothing beyond ---")
    s = ElevatorSystem(1, 10)
    s.request_hall(6, Direction.DOWN)
    arrivals = s.run_until_idle()
    all_ok &= _check("idle car goes up to serve a DOWN call at 6",
                     [(a.floor, a.served) for a in arrivals] == [(6, frozenset({CallKind.HALL_DOWN}))])

    print("\n--- same-floor call and duplicate presses ---")
    s = ElevatorSystem(2, 10)
    first = s.request_hall(0, Direction.UP)
    again = s.request_hall(0, Direction.UP)
    arrivals = s.step()
    all_ok &= _check("duplicate press returns the same car", first == again)
    all_ok &= _check("doors open on the first tick, no movement",
                     [(a.floor, a.tick) for a in arrivals] == [(0, 1)])
    all_ok &= _check("served hall call can be pressed again and is re-dispatched",
                     s.request_hall(0, Direction.UP) in (0, 1))

    print("\n--- validation ---")
    s = ElevatorSystem(1, 5)
    all_ok &= _check("floor out of range", _raises(InvalidRequest, lambda: s.request_car(0, 5)))
    all_ok &= _check("no UP button on the top floor", _raises(InvalidRequest, lambda: s.request_hall(4, Direction.UP)))
    all_ok &= _check("no DOWN button on floor 0", _raises(InvalidRequest, lambda: s.request_hall(0, Direction.DOWN)))
    all_ok &= _check("unknown car", _raises(InvalidRequest, lambda: s.request_car(3, 1)))

    print("\n--- dispatch strategies disagree when a car is heading away ---")
    def scenario(dispatcher: Dispatcher) -> int:
        sys_ = ElevatorSystem(2, 10, dispatcher)
        _place(sys_, 1, 6)                        # car 1 parked at 6, car 0 at 0
        sys_.request_car(1, 0)                    # car 1 now heading DOWN to 0
        sys_.step()                               # car 1 moves 6 -> 5
        return sys_.request_hall(4, Direction.UP)
    all_ok &= _check("NearestCar picks car 1 (1 floor away, but going down to 0)", scenario(NearestCar()) == 1)
    all_ok &= _check("LookCost picks idle car 0 (4 floors) over car 1 (5 down + 4 up)", scenario(LookCost()) == 0)

    print("\n--- out of service re-dispatches hall calls ---")
    s = ElevatorSystem(2, 10, NearestCar())
    _place(s, 1, 9)
    owner = s.request_hall(8, Direction.DOWN)
    moved = s.take_out_of_service(1)
    arrivals = s.run_until_idle()
    all_ok &= _check("call first went to car 1, then moved to car 0",
                     owner == 1 and moved == [(8, Direction.DOWN, 0)])
    all_ok &= _check("car 0 serves floor 8", [(a.car_id, a.floor) for a in arrivals] == [(0, 8)])
    all_ok &= _check("new hall calls never go to the out-of-service car",
                     all(s.request_hall(f, Direction.UP) == 0 for f in range(1, 9)))
    all_ok &= _check("cannot remove the last car", _raises(InvalidRequest, lambda: s.take_out_of_service(0)))

    print("\n--- observers ---")
    s = ElevatorSystem(1, 10)
    seen: list[int] = []
    s.subscribe(lambda a: 1 / 0)                  # broken display
    s.subscribe(lambda a: seen.append(a.floor))
    s.request_car(0, 2)
    s.run_until_idle()
    all_ok &= _check("a raising listener doesn't stop the others", seen == [2] and s.listener_errors == 1)
    return all_ok
# ================================================================= END TESTS ==


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 8 threads press buttons while the controller steps ---")
    s = ElevatorSystem(4, 30)
    expected: set[tuple[int, int]] = set()     # (car_id, floor) that must be visited
    served: set[tuple[int, int]] = set()
    guard = threading.Lock()
    s.subscribe(lambda a: served.add((a.car_id, a.floor)))
    stop = threading.Event()

    def presser(seed: int) -> None:
        rng = random.Random(seed)
        for _ in range(250):
            floor = rng.randrange(1, 29)
            if rng.random() < 0.5:
                car = s.request_hall(floor, rng.choice([Direction.UP, Direction.DOWN]))
            else:
                car = rng.randrange(4)
                s.request_car(car, floor)
            with guard:
                expected.add((car, floor))

    def stepper() -> None:
        while not stop.is_set():
            s.step()

    ticker = threading.Thread(target=stepper)
    ticker.start()
    workers = [threading.Thread(target=presser, args=(i,)) for i in range(8)]
    for w in workers:
        w.start()
    for w in workers:
        w.join()
    stop.set()
    ticker.join()
    s.run_until_idle()
    all_ok &= _check(f"2000 presses -> {len(expected)} distinct (car, floor) stops, all served, "
                     f"all cars idle", expected <= served
                     and all(d is Direction.IDLE for _, _, d in s.status()))

    print("\n--- DEMO 2: LOOK vs first-come-first-served travel distance ---")
    rng = random.Random(7)
    floors = 50
    requests = [rng.randrange(floors) for _ in range(300)]
    fcfs, pos = 0, 0
    for r in requests:
        fcfs += abs(r - pos)
        pos = r
    car = ElevatorCar(0)
    for r in requests:
        car.add_call(r, CallKind.CAR)
    moves = 0
    while car.has_pending():
        before = car.floor
        car.step()
        moves += abs(car.floor - before)
    print(f"      300 requests over {floors} floors: FCFS {fcfs} floors, LOOK {moves} floors "
          f"({fcfs / moves:.0f}x less travel)")
    all_ok &= _check("LOOK travels at most one sweep up and one down", moves <= 2 * floors)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
