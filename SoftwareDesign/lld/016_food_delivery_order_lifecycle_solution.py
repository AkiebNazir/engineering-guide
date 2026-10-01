"""
================================================================================
SOLUTION · LLD 016 · Food Delivery Order Lifecycle (DoorDash / Uber Eats)  [Tier 2]
================================================================================

THE CORE IDEA
--------------
An order moves through states, and DIFFERENT ACTORS drive different
transitions: the restaurant accepts, the courier picks up, the customer can
cancel — but only early. Put all of that in ONE TRANSITION TABLE:

    (state, event) -> (next state, actors allowed)

    PLACED    --accept-------(restaurant)------------> ACCEPTED
    PLACED    --reject-------(restaurant)------------> REJECTED
    ACCEPTED  --start_prep---(restaurant)------------> PREPARING
    PREPARING --mark_ready---(restaurant)------------> READY
    READY     --pick_up------(assigned courier)------> PICKED_UP
    PICKED_UP --deliver------(assigned courier)------> DELIVERED
    PLACED, ACCEPTED        --cancel--(customer, restaurant, system)--> CANCELLED
    PREPARING, READY        --cancel--(restaurant, system)-----------> CANCELLED

One generic apply() checks the table, the actor, and the guards, then records
an event. No `if state == ... and role == ...` scattered across methods, and
the table itself prints as documentation (demo 3).

Three production concerns turn a textbook State answer into a senior one:

    1. OPTIMISTIC CONCURRENCY. The restaurant tablet and the customer's phone
       both read version 3 and act. Each command carries expected_version;
       the second one gets VersionConflict instead of silently overwriting
       (demo 1: "cancelled and refunded, but the kitchen is cooking it").
    2. IDEMPOTENCY. The courier app times out and retries "deliver". A repeated
       idempotency key returns the first result instead of failing or
       double-applying.
    3. AUDIT / EVENT LOG. Every transition is an event; replaying the log
       rebuilds the state exactly (demo 2) — support tickets, analytics and
       disputes all read it.

Side effects (refunds, freeing the courier, notifications) hang off
transitions: RefundPolicy is a strategy; notifications are observers.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. place(customer, restaurant, items) -> Order in PLACED, total in cents.
  2. apply(order_id, event, actor, expected_version=None, idempotency_key=None)
     -> Order, following the table above.
  3. Courier-only events require the order's ASSIGNED courier.
  4. assign_courier(order_id) picks the nearest available courier (strategy)
     once the restaurant has accepted and before pickup.
  5. Cancel computes a refund with a pluggable policy; the courier is freed.
  6. history(order_id) lists every event; subscribers see each event.
  Out of scope: payments integration, maps/ETAs, ratings, promotions.


================================================================================
ENTITIES, VALUE OBJECTS, INVARIANTS
================================================================================
    State, Event, Role     enums
    Actor                  value object (role, id)
    LineItem               value object (name, unit cents, qty)
    Order (aggregate root) id, customer, restaurant, courier, state, version,
                           total, refund
       INVARIANT: version increases by exactly 1 per applied event
       INVARIANT: refund_cents > 0 only if state == CANCELLED
       INVARIANT: courier set => that courier is busy until DELIVERED/CANCELLED
    OrderEvent             immutable log record
    TRANSITIONS            the table (data, not code)
    RefundPolicy           refund(state_at_cancel, actor, total) -> cents
    CourierAssigner        choose(couriers, restaurant location) -> courier
    OrderService           lock per order; idempotency store; observers


================================================================================
KEY FLOW · apply()
================================================================================
    lock(order)
      idempotency_key seen?            -> return the stored result
      expected_version != version?     -> VersionConflict
      rule = TRANSITIONS[(state, event)] -> else InvalidTransition
      actor.role in rule.roles?        -> else NotAllowed
      courier event and actor.id != order.courier -> NotAllowed
      side effects of leaving/entering (refund, free courier)
      state = rule.to; version += 1; append OrderEvent; remember idempotency key
    unlock
    notify observers (outside the lock)


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Transition TABLE over the State pattern: states here differ only in
    "which events are legal, for whom" — data, not behaviour. (Contrast
    lld/003 where HasMoney.select has real logic.)
  * Actor is passed in and checked in the domain; authentication happened
    upstream, authorisation of state changes is a DOMAIN rule.
  * Optimistic concurrency (version) is what you'd do with a DB row:
    UPDATE orders SET state=?, version=version+1 WHERE id=? AND version=?.
    The in-memory lock just makes check-and-write atomic in this process.
  * Idempotency results stored per order (bounded by order lifetime).
  * Event log per order enables replay; the Order object is a cached
    projection of it.


================================================================================
EDGE CASES
================================================================================
  * Customer cancels after the kitchen started -> NotAllowed (only restaurant
    or system can; different refund).
  * Courier who isn't assigned tries to pick up -> NotAllowed.
  * Pick up before READY -> InvalidTransition.
  * Any event on a terminal state -> InvalidTransition.
  * Stale expected_version -> VersionConflict, nothing changes.
  * Same idempotency key replayed -> same result, version unchanged.
  * No available courier -> NoCourier, order unchanged.


================================================================================
COMMON MISTAKES
================================================================================
  1. setState(any) public setter — every rule bypassed.
  2. Role checks and state checks scattered in 8 methods.
  3. No concurrency story: last write wins between tablet and phone.
  4. Retries that fail ("already delivered") or double-apply side effects.
  5. Refund logic inside the Order entity's cancel() with if/else by state.
  6. Losing history: only the current state is stored.
  7. Notifying observers inside the lock.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Courier declines / times out -> ASSIGNED sub-state with an offer expiry;
    reassign via the scheduler (lld/014).
  * Split orders from two restaurants -> parent order with child orders; the
    parent's state is derived from children.
  * Distributed services (orders, payments, dispatch) -> saga with
    compensations; outbox pattern so events and state commit together.
  * Real-time tracking -> location stream separate from the order aggregate.
  * SLA breaches -> timers on states (READY for 20 min -> escalate).


================================================================================
RELATED
================================================================================
  SoftwareDesign/02_oop_and_domain_modeling.md  §8 aggregates, §10 state & lifecycles
  SoftwareDesign/04_design_patterns_in_practice.md  §9 State, §7 Observer, §8 Command
  SystemDesign/problems/008_checkout (idempotency, sagas)
  lld/003_vending_machine (State pattern where it earns its keep)
"""

from __future__ import annotations

import itertools
import random
import threading
import time
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Callable, Protocol


# ----------------------------------------------------------------------------
# Enums, value objects, errors
# ----------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------
# The transition table — data, not code
# ----------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class Rule:
    to: State
    roles: frozenset[Role]


R, C, S, K = Role.RESTAURANT, Role.CUSTOMER, Role.SYSTEM, Role.COURIER
TRANSITIONS: dict[tuple[State, Event], Rule] = {
    (State.PLACED, Event.ACCEPT): Rule(State.ACCEPTED, frozenset({R})),
    (State.PLACED, Event.REJECT): Rule(State.REJECTED, frozenset({R})),
    (State.ACCEPTED, Event.START_PREP): Rule(State.PREPARING, frozenset({R})),
    (State.PREPARING, Event.MARK_READY): Rule(State.READY, frozenset({R})),
    (State.READY, Event.PICK_UP): Rule(State.PICKED_UP, frozenset({K})),
    (State.PICKED_UP, Event.DELIVER): Rule(State.DELIVERED, frozenset({K})),
    (State.PLACED, Event.CANCEL): Rule(State.CANCELLED, frozenset({C, R, S})),
    (State.ACCEPTED, Event.CANCEL): Rule(State.CANCELLED, frozenset({C, R, S})),
    (State.PREPARING, Event.CANCEL): Rule(State.CANCELLED, frozenset({R, S})),
    (State.READY, Event.CANCEL): Rule(State.CANCELLED, frozenset({R, S})),
}
COURIER_ASSIGNABLE = {State.ACCEPTED, State.PREPARING, State.READY}
TERMINAL = {State.DELIVERED, State.CANCELLED, State.REJECTED}


# ----------------------------------------------------------------------------
# Strategies
# ----------------------------------------------------------------------------
class RefundPolicy(Protocol):
    def refund(self, state: State, actor: Actor, total_cents: int) -> int: ...


class StandardRefunds:
    """Full refund before the kitchen starts or when the restaurant/system cancels."""

    def refund(self, state, actor, total_cents):
        if state in (State.PLACED, State.ACCEPTED) or actor.role in (Role.RESTAURANT, Role.SYSTEM):
            return total_cents
        return 0


class CourierAssigner(Protocol):
    def choose(self, available: list[Courier], x: int, y: int) -> Courier | None: ...


class NearestCourier:
    def choose(self, available, x, y):
        return min(available, key=lambda c: (abs(c.x - x) + abs(c.y - y), c.id), default=None)


# ----------------------------------------------------------------------------
# OrderService
# ----------------------------------------------------------------------------
@dataclass
class _Slot:
    order: Order
    lock: threading.Lock = field(default_factory=threading.Lock)
    log: list[OrderEvent] = field(default_factory=list)
    idempotent: dict[str, Order] = field(default_factory=dict)


class OrderService:
    def __init__(self, refunds: RefundPolicy | None = None, assigner: CourierAssigner | None = None) -> None:
        self._refunds = refunds or StandardRefunds()
        self._assigner = assigner or NearestCourier()
        self._slots: dict[int, _Slot] = {}
        self._restaurants: dict[str, tuple[int, int]] = {}
        self._couriers: dict[str, Courier] = {}
        self._busy: set[str] = set()
        self._registry = threading.Lock()
        self._ids = itertools.count(1)
        self._listeners: list[Callable[[OrderEvent], None]] = []

    # -- setup -----------------------------------------------------------------------
    def add_restaurant(self, restaurant_id: str, x: int, y: int) -> None:
        self._restaurants[restaurant_id] = (x, y)

    def add_courier(self, courier: Courier) -> None:
        with self._registry:
            self._couriers[courier.id] = courier

    def subscribe(self, listener: Callable[[OrderEvent], None]) -> None:
        self._listeners.append(listener)

    # -- commands --------------------------------------------------------------------
    def place(self, customer_id: str, restaurant_id: str, items: list[LineItem]) -> Order:
        if restaurant_id not in self._restaurants:
            raise OrderError(f"unknown restaurant {restaurant_id}")
        if not items or any(i.qty <= 0 or i.unit_cents < 0 for i in items):
            raise OrderError("order needs items with positive quantity")
        total = sum(i.unit_cents * i.qty for i in items)
        with self._registry:
            order = Order(next(self._ids), customer_id, restaurant_id, total)
            self._slots[order.id] = _Slot(order)
        return order

    def apply(self, order_id: int, event: Event, actor: Actor,
              expected_version: int | None = None, idempotency_key: str | None = None) -> Order:
        slot = self._slot(order_id)
        with slot.lock:
            if idempotency_key is not None and idempotency_key in slot.idempotent:
                return slot.idempotent[idempotency_key]
            order = slot.order
            if expected_version is not None and expected_version != order.version:
                raise VersionConflict(f"order {order_id} is at v{order.version}, not v{expected_version}")
            rule = TRANSITIONS.get((order.state, event))
            if rule is None:
                raise InvalidTransition(f"{event.value} not allowed in {order.state.value}")
            if actor.role not in rule.roles:
                raise NotAllowed(f"{actor.role.value} can't {event.value} in {order.state.value}")
            if actor.role is Role.COURIER and actor.id != order.courier_id:
                raise NotAllowed(f"courier {actor.id} is not assigned to order {order_id}")
            if actor.role is Role.RESTAURANT and actor.id != order.restaurant_id:
                raise NotAllowed(f"restaurant {actor.id} doesn't own order {order_id}")
            if actor.role is Role.CUSTOMER and actor.id != order.customer_id:
                raise NotAllowed(f"customer {actor.id} doesn't own order {order_id}")

            refund = self._refunds.refund(order.state, actor, order.total_cents) if rule.to is State.CANCELLED else 0
            if rule.to in TERMINAL and order.courier_id:
                with self._registry:
                    self._busy.discard(order.courier_id)
            record = OrderEvent(order_id, order.version + 1, event, actor, order.state, rule.to)
            slot.order = replace(order, state=rule.to, version=order.version + 1, refund_cents=refund)
            slot.log.append(record)
            if idempotency_key is not None:
                slot.idempotent[idempotency_key] = slot.order
            result = slot.order
        for listener in list(self._listeners):
            listener(record)
        return result

    def assign_courier(self, order_id: int) -> Order:
        slot = self._slot(order_id)
        with slot.lock:
            order = slot.order
            if order.state not in COURIER_ASSIGNABLE:
                raise InvalidTransition(f"can't assign a courier in {order.state.value}")
            if order.courier_id is not None:
                return order
            x, y = self._restaurants[order.restaurant_id]
            with self._registry:
                free = [c for cid, c in self._couriers.items() if cid not in self._busy]
                courier = self._assigner.choose(free, x, y)
                if courier is None:
                    raise NoCourier(f"no courier for order {order_id}")
                self._busy.add(courier.id)
            slot.order = replace(order, courier_id=courier.id)
            return slot.order

    # -- queries ---------------------------------------------------------------------
    def get(self, order_id: int) -> Order:
        slot = self._slot(order_id)
        with slot.lock:
            return slot.order

    def history(self, order_id: int) -> list[OrderEvent]:
        slot = self._slot(order_id)
        with slot.lock:
            return list(slot.log)

    def courier_busy(self, courier_id: str) -> bool:
        with self._registry:
            return courier_id in self._busy

    def _slot(self, order_id: int) -> _Slot:
        with self._registry:
            if order_id not in self._slots:
                raise UnknownOrder(order_id)
            return self._slots[order_id]


def replay(events: list[OrderEvent]) -> State:
    """Rebuild the state from the event log alone."""
    state = State.PLACED
    for e in events:
        rule = TRANSITIONS[(state, e.event)]
        state = rule.to
    return state


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


class NaiveOrder:
    """No lock, no version: read state, do slow work, write state."""

    def __init__(self) -> None:
        self.state = State.PLACED
        self.refunded = False
        self.kitchen_started = False

    def accept(self) -> None:
        if self.state is State.PLACED:
            time.sleep(0.0005)                      # tablet round trip
            self.state = State.ACCEPTED
            self.kitchen_started = True

    def cancel(self) -> None:
        if self.state in (State.PLACED, State.ACCEPTED):
            time.sleep(0.0005)                      # phone round trip
            self.state = State.CANCELLED
            self.refunded = True


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: restaurant accepts while the customer cancels, 300 orders ---")
    naive_bad = 0
    for _ in range(300):
        o = NaiveOrder()
        ts = [threading.Thread(target=o.accept), threading.Thread(target=o.cancel)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        naive_bad += (o.refunded and o.kitchen_started) or (o.refunded and o.state is not State.CANCELLED)

    svc = _service()
    safe_bad = conflicts = 0
    for _ in range(300):
        order = _place(svc)
        v = order.version
        outcomes = []

        def act(event: Event, actor: Actor) -> None:
            try:
                svc.apply(order.id, event, actor, expected_version=v)
                outcomes.append(event)
            except VersionConflict:
                outcomes.append("conflict")

        ts = [threading.Thread(target=act, args=(Event.ACCEPT, REST)),
              threading.Thread(target=act, args=(Event.CANCEL, CUST))]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        final = svc.get(order.id)
        conflicts += outcomes.count("conflict")
        safe_bad += (final.refund_cents > 0) != (final.state is State.CANCELLED) or outcomes.count("conflict") != 1
    print(f"      no version check : {naive_bad} orders refunded AND cooking (or refunded but not cancelled)")
    print(f"      expected_version : {safe_bad} inconsistent orders; {conflicts} losers told VersionConflict")
    all_ok &= _check("versioned commands keep every order consistent; naive ones don't",
                     safe_bad == 0 and naive_bad > 0)

    print("\n--- DEMO 2: 3,000 random commands, then rebuild every order from its log ---")
    rng = random.Random(16)
    svc = _service()
    for i in range(20):
        svc.add_courier(Courier(f"k{i}", rng.randint(-20, 20), rng.randint(-20, 20)))
    ids = [_place(svc).id for _ in range(200)]
    applied = 0
    for _ in range(3000):
        oid = rng.choice(ids)
        order = svc.get(oid)
        legal = [e for (s, e) in TRANSITIONS if s is order.state and e is not Event.CANCEL]
        if legal and rng.random() < 0.8:
            event = rng.choice(legal)                   # mostly plausible commands...
            role = rng.choice(sorted(TRANSITIONS[(order.state, event)].roles, key=lambda r: r.value))
        else:
            event, role = rng.choice(list(Event)), rng.choice(list(Role))   # ...plus garbage
        actor_id = {Role.CUSTOMER: "ann", Role.RESTAURANT: "pizzeria", Role.SYSTEM: "ops",
                    Role.COURIER: order.courier_id or "nobody"}[role]
        try:
            if rng.random() < 0.2:
                svc.assign_courier(oid)
            svc.apply(oid, event, Actor(role, actor_id))
            applied += 1
        except OrderError:
            pass
    mismatched = sum(replay(svc.history(oid)) is not svc.get(oid).state for oid in ids)
    versions_ok = all(svc.get(oid).version == 1 + len(svc.history(oid)) for oid in ids)
    states = {}
    for oid in ids:
        states[svc.get(oid).state.value] = states.get(svc.get(oid).state.value, 0) + 1
    print(f"      {applied} commands applied; final states {states}")
    all_ok &= _check(f"replaying each log reproduces the state ({mismatched} mismatches); version == 1 + events",
                     mismatched == 0 and versions_ok)

    print("\n--- DEMO 3: the transition table IS the documentation ---")
    LETTER = {Role.CUSTOMER: "C", Role.RESTAURANT: "R", Role.COURIER: "K", Role.SYSTEM: "S"}
    states = [s for s in State if s not in TERMINAL]
    events = list(Event)
    print("      " + "state".ljust(11) + "".join(e.value[:10].ljust(12) for e in events))
    for s in states:
        cells = []
        for e in events:
            rule = TRANSITIONS.get((s, e))
            cells.append(("-" if rule is None else "/".join(sorted(LETTER[r] for r in rule.roles))).ljust(12))
        print("      " + s.value.ljust(11) + "".join(cells))
    print("      (C customer, R restaurant, K courier, S system)")
    all_ok &= _check("every non-terminal state has at least one way out",
                     all(any((s, e) in TRANSITIONS for e in events) for s in states))
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
