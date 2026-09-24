"""
================================================================================
LLD 002 · Elevator System                                          [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement the controller for a bank of elevators.

The interviewer says: "Design an elevator system." Below are the requirements a
good candidate would agree in the first five minutes. Write your own list of
clarifying questions first, then compare.

REQUIREMENTS
------------
  1. N cars serve floors 0..F-1. Every car starts idle on floor 0.
  2. HALL CALL: someone on a floor presses UP or DOWN.
        request_hall(floor, direction) -> car_id
     The system assigns it to exactly one car using a PLUGGABLE dispatcher.
     Pressing the same button again returns the same car.
     There is no UP button on the top floor and no DOWN button on floor 0.
  3. CAR CALL: someone inside car c presses a floor button.
        request_car(car_id, floor)
  4. Time is discrete. step() advances one tick. In a tick each car does ONE of:
        * opens its doors at the current floor, serving calls there, or
        * moves one floor, or
        * nothing (idle).
     step() returns the list of Arrival(tick, car_id, floor, served_calls).
  5. Each car schedules with LOOK:
        * keep moving in the current direction while any stop lies ahead;
        * stop at a floor with a CAR call, or a hall call in the SAME direction
          the car is travelling;
        * do NOT stop for an opposite-direction hall call while stops remain
          ahead — unless nothing is ahead, then serve everything there and
          turn around;
        * an idle car first serves calls on its own floor, otherwise heads
          toward the nearest pending floor (ties -> the lower floor).
  6. Two dispatchers:
        NearestCar -> smallest |car.floor - floor| (ties -> lower car id)
        LookCost   -> fewest floors the car must travel before it can serve
                      the call, counting the rest of its current sweep if it
                      is heading away (ties -> lower car id). This is the default.
  7. take_out_of_service(car_id): the car gets no new hall calls; its pending
     hall calls are re-dispatched. Returns [(floor, direction, new_car_id)].
     Removing the last in-service car raises InvalidRequest.
  8. subscribe(listener): listener(arrival) is called for every arrival. A
     listener that raises must not break the system or other listeners;
     count such failures in `listener_errors`.
  9. Requests can arrive from many threads while another thread calls step().

  Out of scope: capacity, door timing, acceleration, fire mode.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * Which object decides WHICH car, and which decides the ORDER of stops?
  * Does a hall call's direction matter? When?
  * Why might "nearest car" be the wrong car?
  * State machine: what are a car's states, and do they need classes?
  * Where does the lock go, and are observers called while holding it?

FOLLOW-UPS TO PREPARE
---------------------
  capacity limits · zoned/express cars · lobby parking at rush hour ·
  destination dispatch · fire mode · real-time doors.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Everything inside the classes is yours to design. Run this file: all checks
should print PASS, then ALL PASSED.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Callable, Protocol


class Direction(IntEnum):
    DOWN = -1
    IDLE = 0
    UP = 1


class CallKind(Enum):
    CAR = "car"
    HALL_UP = "hall_up"
    HALL_DOWN = "hall_down"


@dataclass(frozen=True, slots=True)
class Arrival:
    tick: int
    car_id: int
    floor: int
    served: frozenset[CallKind]


class InvalidRequest(ValueError): ...


class ElevatorCar:
    def __init__(self, car_id: int, floor: int = 0) -> None:
        # YOUR CODE HERE
        raise NotImplementedError


class Dispatcher(Protocol):
    def choose(self, cars: list[ElevatorCar], floor: int, direction: Direction) -> ElevatorCar: ...


class NearestCar:
    def choose(self, cars: list[ElevatorCar], floor: int, direction: Direction) -> ElevatorCar:
        raise NotImplementedError


class LookCost:
    def choose(self, cars: list[ElevatorCar], floor: int, direction: Direction) -> ElevatorCar:
        raise NotImplementedError


class ElevatorSystem:
    def __init__(self, n_cars: int, n_floors: int, dispatcher=None) -> None:
        self.listener_errors = 0
        # YOUR CODE HERE
        raise NotImplementedError

    def request_hall(self, floor: int, direction: Direction) -> int:
        raise NotImplementedError

    def request_car(self, car_id: int, floor: int) -> None:
        raise NotImplementedError

    def take_out_of_service(self, car_id: int) -> list[tuple[int, Direction, int]]:
        raise NotImplementedError

    def subscribe(self, listener: Callable[[Arrival], None]) -> None:
        raise NotImplementedError

    def step(self) -> list[Arrival]:
        raise NotImplementedError

    def run_until_idle(self, max_ticks: int = 100_000) -> list[Arrival]:
        """Call step() until no car has pending calls; return all arrivals."""
        raise NotImplementedError

    def status(self) -> list[tuple[int, int, Direction]]:
        """[(car_id, floor, direction)] for every car, in id order."""
        raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
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


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
