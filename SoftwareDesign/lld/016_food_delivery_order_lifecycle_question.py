"""
================================================================================
LLD 016 · Food Delivery Order Lifecycle (DoorDash / Uber Eats)     [Tier 2]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement the order lifecycle for a food delivery app: states,
who may move an order between them, courier assignment, cancellation refunds,
and what happens when two apps act on the same order at once.

These are the agreed requirements.

REQUIREMENTS
------------
  1. OrderService(refunds=None, assigner=None); add_restaurant(id, x, y);
     add_courier(Courier(id, x, y)); subscribe(listener) -> listener(OrderEvent)
     is called after each applied event.
  2. place(customer_id, restaurant_id, [LineItem(name, unit_cents, qty)]) ->
     Order(id, customer_id, restaurant_id, total_cents, state=PLACED, version=1,
     courier_id=None, refund_cents=0). Unknown restaurant, no items, or
     qty <= 0 -> OrderError.
  3. apply(order_id, event, actor, expected_version=None, idempotency_key=None)
     -> updated Order. Legal transitions (and the roles allowed):
        PLACED    accept     -> ACCEPTED   restaurant
        PLACED    reject     -> REJECTED   restaurant
        ACCEPTED  start_prep -> PREPARING  restaurant
        PREPARING mark_ready -> READY      restaurant
        READY     pick_up    -> PICKED_UP  courier
        PICKED_UP deliver    -> DELIVERED  courier
        PLACED or ACCEPTED   cancel -> CANCELLED   customer, restaurant, system
        PREPARING or READY   cancel -> CANCELLED   restaurant, system
     * Not in the table -> InvalidTransition.
     * Role not allowed -> NotAllowed. Also NotAllowed if a courier isn't the
       order's assigned courier, a restaurant isn't the order's restaurant, or
       a customer isn't the order's customer.
     * expected_version given and != order.version -> VersionConflict, nothing
       changes.
     * An applied event increments version by 1 and is appended to history.
     * idempotency_key already used on this order -> return the Order that the
       first call returned; apply nothing.
     * Entering CANCELLED sets refund_cents = refunds.refund(state_before,
       actor, total). Entering any terminal state frees the courier.
  4. StandardRefunds: full refund if cancelled in PLACED/ACCEPTED or by the
     restaurant/system; otherwise 0.
  5. assign_courier(order_id) -> Order: only in ACCEPTED, PREPARING or READY
     (else InvalidTransition); if a courier is already set, return unchanged;
     otherwise the NearestCourier (Manhattan distance to the restaurant, ties
     by id) among couriers not busy; none -> NoCourier. The courier is busy
     until the order is delivered or cancelled. courier_busy(id) -> bool.
  6. get(order_id), history(order_id) -> [OrderEvent]; UnknownOrder if missing.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * State pattern or transition table? Why?
  * Where are actor permissions checked?
  * The restaurant accepts while the customer cancels — what happens?
  * The courier app retries "delivered" after a timeout — what happens?
  * How would you audit or rebuild an order's history?

FOLLOW-UPS TO PREPARE
---------------------
  courier offer timeouts · multi-restaurant orders · sagas across services ·
  live tracking · SLA timers.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class State(Enum):
    PLACED = "placed"
    ACCEPTED = "accepted"
    PREPARING = "preparing"
    READY = "ready"
    PICKED_UP = "picked_up"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class Event(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    START_PREP = "start_prep"
    MARK_READY = "mark_ready"
    PICK_UP = "pick_up"
    DELIVER = "deliver"
    CANCEL = "cancel"


class Role(Enum):
    CUSTOMER = "customer"
    RESTAURANT = "restaurant"
    COURIER = "courier"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class Actor:
    role: Role
    id: str


@dataclass(frozen=True, slots=True)
class LineItem:
    name: str
    unit_cents: int
    qty: int


@dataclass(frozen=True, slots=True)
class Order:
    id: int
    customer_id: str
    restaurant_id: str
    total_cents: int
    state: State = State.PLACED
    version: int = 1
    courier_id: str | None = None
    refund_cents: int = 0


@dataclass(frozen=True, slots=True)
class OrderEvent:
    order_id: int
    version: int
    event: Event
    actor: Actor
    from_state: State
    to_state: State


@dataclass(frozen=True, slots=True)
class Courier:
    id: str
    x: int
    y: int


class OrderError(Exception): ...
class UnknownOrder(OrderError): ...
class InvalidTransition(OrderError): ...
class NotAllowed(OrderError): ...
class VersionConflict(OrderError): ...
class NoCourier(OrderError): ...


class StandardRefunds:
    def refund(self, state: State, actor: Actor, total_cents: int) -> int:
        raise NotImplementedError


class OrderService:
    def __init__(self, refunds=None, assigner=None) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def add_restaurant(self, restaurant_id: str, x: int, y: int) -> None: raise NotImplementedError
    def add_courier(self, courier: Courier) -> None: raise NotImplementedError
    def subscribe(self, listener: Callable[[OrderEvent], None]) -> None: raise NotImplementedError
    def place(self, customer_id: str, restaurant_id: str, items: list[LineItem]) -> Order: raise NotImplementedError

    def apply(self, order_id: int, event: Event, actor: Actor,
              expected_version: int | None = None, idempotency_key: str | None = None) -> Order:
        raise NotImplementedError

    def assign_courier(self, order_id: int) -> Order: raise NotImplementedError
    def get(self, order_id: int) -> Order: raise NotImplementedError
    def history(self, order_id: int) -> list[OrderEvent]: raise NotImplementedError
    def courier_busy(self, courier_id: str) -> bool: raise NotImplementedError


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


CUST = Actor(Role.CUSTOMER, "ann")
REST = Actor(Role.RESTAURANT, "pizzeria")
SYS = Actor(Role.SYSTEM, "ops")


def _service() -> OrderService:
    svc = OrderService()
    svc.add_restaurant("pizzeria", 0, 0)
    svc.add_courier(Courier("far", 10, 10))
    svc.add_courier(Courier("near", 1, 1))
    return svc


def _place(svc: OrderService) -> Order:
    return svc.place("ann", "pizzeria", [LineItem("margherita", 1200, 2), LineItem("cola", 300, 1)])


def run_tests() -> bool:
    all_ok = True
    print("--- happy path ---")
    svc = _service()
    seen: list[Event] = []
    svc.subscribe(lambda e: seen.append(e.event))
    o = _place(svc)
    all_ok &= _check("placed with total 2700 at version 1", (o.state, o.total_cents, o.version) == (State.PLACED, 2700, 1))
    svc.apply(o.id, Event.ACCEPT, REST)
    o = svc.assign_courier(o.id)
    all_ok &= _check("nearest available courier assigned", o.courier_id == "near" and svc.courier_busy("near"))
    svc.apply(o.id, Event.START_PREP, REST)
    svc.apply(o.id, Event.MARK_READY, REST)
    courier = Actor(Role.COURIER, "near")
    svc.apply(o.id, Event.PICK_UP, courier)
    done = svc.apply(o.id, Event.DELIVER, courier)
    all_ok &= _check("delivered at version 6 (1 + five events); courier freed",
                     done.state is State.DELIVERED and done.version == 6 and not svc.courier_busy("near"))
    all_ok &= _check("history and observers saw the five events in order",
                     [e.event for e in svc.history(o.id)] == seen
                     == [Event.ACCEPT, Event.START_PREP, Event.MARK_READY, Event.PICK_UP, Event.DELIVER])

    print("\n--- the table enforces state and actor ---")
    svc = _service()
    o = _place(svc)
    all_ok &= _check("customer can't accept", _raises(NotAllowed, lambda: svc.apply(o.id, Event.ACCEPT, CUST)))
    all_ok &= _check("another restaurant can't accept",
                     _raises(NotAllowed, lambda: svc.apply(o.id, Event.ACCEPT, Actor(Role.RESTAURANT, "burger"))))
    all_ok &= _check("can't pick up a PLACED order",
                     _raises(InvalidTransition, lambda: svc.apply(o.id, Event.PICK_UP, Actor(Role.COURIER, "near"))))
    svc.apply(o.id, Event.ACCEPT, REST)
    svc.assign_courier(o.id)
    svc.apply(o.id, Event.START_PREP, REST)
    svc.apply(o.id, Event.MARK_READY, REST)
    all_ok &= _check("unassigned courier can't pick up",
                     _raises(NotAllowed, lambda: svc.apply(o.id, Event.PICK_UP, Actor(Role.COURIER, "far"))))
    all_ok &= _check("customer can't cancel once READY", _raises(NotAllowed, lambda: svc.apply(o.id, Event.CANCEL, CUST)))

    print("\n--- cancellation and refunds ---")
    svc = _service()
    early = _place(svc)
    svc.apply(early.id, Event.ACCEPT, REST)
    svc.assign_courier(early.id)
    cancelled = svc.apply(early.id, Event.CANCEL, CUST)
    all_ok &= _check("customer cancel before prep: full refund, courier freed",
                     cancelled.refund_cents == 2700 and not svc.courier_busy("near"))
    all_ok &= _check("terminal state accepts nothing", _raises(InvalidTransition, lambda: svc.apply(early.id, Event.ACCEPT, REST)))
    late = _place(svc)
    svc.apply(late.id, Event.ACCEPT, REST)
    svc.apply(late.id, Event.START_PREP, REST)
    all_ok &= _check("restaurant cancelling while preparing refunds in full",
                     svc.apply(late.id, Event.CANCEL, REST).refund_cents == 2700)
    all_ok &= _check("StandardRefunds: customer cancelling during prep would get 0",
                     StandardRefunds().refund(State.PREPARING, CUST, 2700) == 0)

    print("\n--- concurrency and retries ---")
    svc = _service()
    o = _place(svc)
    v = svc.get(o.id).version                      # both apps read v1
    svc.apply(o.id, Event.ACCEPT, REST, expected_version=v)
    all_ok &= _check("second writer with the stale version -> VersionConflict, state unchanged",
                     _raises(VersionConflict, lambda: svc.apply(o.id, Event.CANCEL, CUST, expected_version=v))
                     and svc.get(o.id).state is State.ACCEPTED)
    svc.apply(o.id, Event.START_PREP, REST)
    svc.apply(o.id, Event.MARK_READY, REST)
    svc.assign_courier(o.id)
    k = Actor(Role.COURIER, "near")
    svc.apply(o.id, Event.PICK_UP, k)
    first = svc.apply(o.id, Event.DELIVER, k, idempotency_key="deliver-123")
    retry = svc.apply(o.id, Event.DELIVER, k, idempotency_key="deliver-123")
    all_ok &= _check("retried deliver with the same key returns the same result",
                     first == retry and len(svc.history(o.id)) == 5)
    all_ok &= _check("a NEW deliver without the key is an invalid transition",
                     _raises(InvalidTransition, lambda: svc.apply(o.id, Event.DELIVER, k)))

    print("\n--- courier supply and validation ---")
    svc = OrderService()
    svc.add_restaurant("pizzeria", 0, 0)
    o = _place(svc)
    all_ok &= _check("can't assign before accept", _raises(InvalidTransition, lambda: svc.assign_courier(o.id)))
    svc.apply(o.id, Event.ACCEPT, REST)
    all_ok &= _check("no couriers -> NoCourier", _raises(NoCourier, lambda: svc.assign_courier(o.id)))
    all_ok &= _check("empty order rejected", _raises(OrderError, lambda: svc.place("ann", "pizzeria", [])))
    all_ok &= _check("unknown order", _raises(UnknownOrder, lambda: svc.get(999)))
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
