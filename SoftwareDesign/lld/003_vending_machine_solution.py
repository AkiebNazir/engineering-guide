"""
================================================================================
SOLUTION · LLD 003 · Vending Machine                               [Tier 1]
================================================================================

THE CORE IDEA
--------------
A vending machine answers the same three buttons (insert, select, cancel)
differently depending on where it is in a session. That is the textbook force
for the STATE pattern: each state is an object that implements every
operation, and illegal operations fail in one obvious place instead of in an
`if self.state == ...` scattered through every method.

The part candidates get wrong is not the states — it's the MONEY:

    1. Money is integer cents, never floats.
    2. The customer's inserted coins are kept as a SESSION, separate from the
       machine's cash box, until a sale commits. Cancel returns exactly those
       coins — always possible, never needs change-making.
    3. A sale is ATOMIC: compute change first, and only if change can be made
       decrement stock, move coins, and dispense. Otherwise nothing changes.
    4. Change-making with a LIMITED number of each coin is not greedy. With one
       quarter and three dimes, 30 cents of change is 10+10+10; greedy grabs the
       quarter, needs a nickel it doesn't have, and refuses a sale the machine
       could have made (demo 2 measures how often).


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. Accepts NICKEL (5), DIME (10), QUARTER (25), DOLLAR (100) coins.
  2. Products live in slots (code -> product, price, quantity).
  3. insert(coin) -> balance; select(code) -> Vend(product, change);
     cancel() -> refunded coins.
  4. One product per session; after a sale the machine returns to Idle.
  5. Failure cases keep the session intact: SoldOut, InsufficientFunds,
     CannotMakeChange, UnknownProduct.
  6. Maintenance mode for restocking and collecting cash; no sales in it.
  7. Change-making algorithm is pluggable.
  Out of scope: card payments, displays, temperature, multi-item baskets.


================================================================================
ENTITIES, VALUE OBJECTS, INVARIANTS
================================================================================
    Coin                 IntEnum, value = cents
    Product              value object (code, name, price_cents)
    Vend                 value object returned by a sale
    VendingMachine       context; INVARIANT (conservation of money):
                           cash box + session coins + all coins ever returned
                           == initial cash + all coins ever inserted
                         INVARIANT: stock never negative; a failed select
                           changes nothing
    State                Idle / HasMoney / Maintenance (stateless, shared)
    ChangeMaker          protocol: make(amount, cash_box) -> coins | None
       GreedyChange      largest coin first (wrong with limited coins)
       BoundedChange     min-coin bounded knapsack (correct)


================================================================================
STATE DIAGRAM
================================================================================
                 insert                         insert (adds)
        ┌──────────────────────────┐         ┌──────┐
        │                          ▼         │      ▼
    ┌────────┐   cancel / sale  ┌─────────────────┐
    │  Idle  │◀─────────────────│    HasMoney     │ select fails -> stays
    └────────┘                  └─────────────────┘
      │    ▲
      │    │ exit_maintenance
      ▼    │
    ┌─────────────┐   restock / collect_cash allowed; insert/select refused
    │ Maintenance │
    └─────────────┘
    enter_maintenance from HasMoney -> InvalidOperation (refund first)


================================================================================
KEY FLOW · select(code) in HasMoney
================================================================================
    slot = stock[code]                    UnknownProduct if missing
    slot.qty == 0                         SoldOut            (nothing changed)
    balance < price                       InsufficientFunds  (nothing changed)
    pool  = cash box + session coins      coins the machine could hand back
    change = maker.make(balance - price, pool)
    change is None                        CannotMakeChange   (nothing changed)
    ---- commit (no failure possible past this line) ----
    cash box += session coins; cash box -= change; qty -= 1; session = []
    state = Idle; return Vend(product, change)


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * State pattern with shared, STATELESS state objects (IDLE, HAS_MONEY,
    MAINTENANCE). All data lives on the machine, so states can be singletons.
    A transition table is the alternative when states differ only in
    "allowed or not"; here HasMoney.select has real logic, so classes earn it.
  * Session coins kept apart from the cash box -> cancel is trivially exact
    and a mid-session power loss can refund precisely.
  * Inserted coins ARE usable as change for the same sale (pay 4 quarters for
    a 75-cent item into an empty machine: one quarter comes back).
  * Change-making as a strategy. BoundedChange is O(amount x coins in box),
    tiny for vending amounts.
  * Errors are exceptions carrying the reason; the session survives them.


================================================================================
COMPLEXITY
================================================================================
    Operation     Time                                   Space
    insert        O(1)                                   O(1)
    select        O(A * K)  A = change amount / 5, K = coin types x count  O(A)
    cancel        O(coins in session)                    O(1)


================================================================================
EDGE CASES
================================================================================
  * Exact payment -> empty change.
  * Machine has no coins at all -> sale works only if exact or payable from
    the session's own coins.
  * Select a sold-out item, then a different one -> second succeeds.
  * Cancel with no money -> {} (not an error).
  * Enter maintenance with money inserted -> refused (would swallow money).
  * Restock outside maintenance -> refused.


================================================================================
COMMON MISTAKES
================================================================================
  1. Floats for money (0.1 + 0.2 != 0.3).
  2. Greedy change-making with limited coins.
  3. Decrementing stock, THEN discovering change can't be made.
  4. Mixing inserted coins into the cash box immediately -> cancel needs
     change-making and can fail.
  5. State checks duplicated in every method instead of State objects.
  6. Storing mutable per-session data inside shared state singletons.
  7. Returning None/False for failures without saying why.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Card payments          -> PaymentMethod strategy; the session holds a
                              pre-authorisation instead of coins; capture on commit.
  * Multiple items         -> basket in the session; one atomic commit.
  * "Exact change only"    -> light on when BoundedChange can't make every
                              amount up to max(price) - min(price) + max coin.
  * Dispense motor fails   -> Dispensing state; on failure, roll back the
                              commit (refund balance) — compensation.
  * Remote telemetry       -> Observer on sale / sold-out / low-change events.
  * Audit                  -> append-only event log of every commit (Command).


================================================================================
RELATED
================================================================================
  SoftwareDesign/04_design_patterns_in_practice.md  §9 State, §3 Strategy
  SoftwareDesign/02_oop_and_domain_modeling.md      §3 Invariants, §10 Lifecycles
  PyDSA 17_dp (coin change) — the unbounded version of BoundedChange
  lld/002_elevator_system (state as an enum, when classes aren't needed)
"""

from __future__ import annotations

import itertools
import random
from collections import Counter
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Protocol


# ----------------------------------------------------------------------------
# Value objects and errors
# ----------------------------------------------------------------------------
class Coin(IntEnum):
    NICKEL = 5
    DIME = 10
    QUARTER = 25
    DOLLAR = 100


@dataclass(frozen=True, slots=True)
class Product:
    code: str
    name: str
    price_cents: int


@dataclass(frozen=True, slots=True)
class Vend:
    product: Product
    change: dict[Coin, int]


class VendingError(Exception): ...
class InvalidOperation(VendingError): ...
class UnknownProduct(VendingError): ...
class SoldOut(VendingError): ...
class InsufficientFunds(VendingError): ...
class CannotMakeChange(VendingError): ...


def _total(coins: dict[Coin, int]) -> int:
    return sum(c * n for c, n in coins.items())


# ----------------------------------------------------------------------------
# Change-making strategies
# ----------------------------------------------------------------------------
class ChangeMaker(Protocol):
    def make(self, amount: int, available: dict[Coin, int]) -> dict[Coin, int] | None: ...


class GreedyChange:
    """Largest coin first. Optimal for unlimited US coins; fails with limited stock."""

    def make(self, amount, available):
        out: dict[Coin, int] = {}
        for coin in sorted(Coin, reverse=True):
            n = min(available.get(coin, 0), amount // coin)
            if n:
                out[coin] = n
                amount -= n * coin
        return out if amount == 0 else None


class BoundedChange:
    """Fewest coins using at most available[c] of each coin (bounded knapsack)."""

    def make(self, amount, available):
        if amount == 0:
            return {}
        INF = float("inf")
        best: list[float] = [0] + [INF] * amount
        used: list[dict[Coin, int]] = [{}] + [{} for _ in range(amount)]
        for coin in Coin:
            limit = available.get(coin, 0)
            if not limit:
                continue
            new_best, new_used = best[:], [u for u in used]
            for a in range(coin, amount + 1):
                for k in range(1, min(limit, a // coin) + 1):
                    prev = a - k * coin
                    if best[prev] + k < new_best[a]:
                        new_best[a] = best[prev] + k
                        new_used[a] = {**used[prev], coin: k}
            best, used = new_best, new_used
        return dict(used[amount]) if best[amount] != INF else None


# ----------------------------------------------------------------------------
# States — stateless, shared
# ----------------------------------------------------------------------------
class State:
    name = "state"

    def insert(self, m: VendingMachine, coin: Coin) -> int:
        raise InvalidOperation(f"cannot insert coins while {self.name}")

    def select(self, m: VendingMachine, code: str) -> Vend:
        raise InvalidOperation(f"cannot select while {self.name}")

    def cancel(self, m: VendingMachine) -> dict[Coin, int]:
        return {}


class Idle(State):
    name = "idle"

    def insert(self, m, coin):
        m._session.append(coin)
        m._state = HAS_MONEY
        return m.balance

    def select(self, m, code):
        raise InsufficientFunds("insert money first")


class HasMoney(State):
    name = "has_money"

    def insert(self, m, coin):
        m._session.append(coin)
        return m.balance

    def select(self, m, code):
        if code not in m._slots:
            raise UnknownProduct(code)
        product, qty = m._slots[code]
        if qty == 0:
            raise SoldOut(code)
        balance = m.balance
        if balance < product.price_cents:
            raise InsufficientFunds(f"need {product.price_cents}, have {balance}")
        pool = Counter(m._cash)
        pool.update(m._session)
        change = m._change_maker.make(balance - product.price_cents, dict(pool))
        if change is None:
            raise CannotMakeChange(f"cannot return {balance - product.price_cents}")
        # ---- commit: nothing below can fail ----
        m._cash = pool
        m._cash.subtract(change)
        m._slots[code] = (product, qty - 1)
        m._session = []
        m._state = IDLE
        return Vend(product, change)

    def cancel(self, m):
        refund = dict(Counter(m._session))
        m._session = []
        m._state = IDLE
        return refund


class Maintenance(State):
    name = "maintenance"


IDLE, HAS_MONEY, MAINTENANCE = Idle(), HasMoney(), Maintenance()


# ----------------------------------------------------------------------------
# VendingMachine — the context
# ----------------------------------------------------------------------------
class VendingMachine:
    def __init__(self, cash: dict[Coin, int] | None = None,
                 change_maker: ChangeMaker | None = None) -> None:
        self._cash: Counter[Coin] = Counter(cash or {})
        self._slots: dict[str, tuple[Product, int]] = {}
        self._session: list[Coin] = []
        self._state: State = IDLE
        self._change_maker = change_maker or BoundedChange()

    # -- customer operations delegate to the state --------------------------------
    def insert(self, coin: Coin) -> int:
        if not isinstance(coin, Coin):
            raise InvalidOperation(f"rejected coin {coin!r}")
        return self._state.insert(self, coin)

    def select(self, code: str) -> Vend:
        return self._state.select(self, code)

    def cancel(self) -> dict[Coin, int]:
        return self._state.cancel(self)

    # -- operator operations -----------------------------------------------------
    def enter_maintenance(self) -> None:
        if self._state is not IDLE:
            raise InvalidOperation(f"cannot enter maintenance while {self._state.name}")
        self._state = MAINTENANCE

    def exit_maintenance(self) -> None:
        if self._state is not MAINTENANCE:
            raise InvalidOperation("not in maintenance")
        self._state = IDLE

    def restock(self, product: Product, qty: int) -> None:
        self._require_maintenance()
        if qty < 0:
            raise ValueError("qty must be >= 0")
        current = self._slots.get(product.code, (product, 0))[1]
        self._slots[product.code] = (product, current + qty)

    def add_cash(self, coins: dict[Coin, int]) -> None:
        self._require_maintenance()
        self._cash.update(coins)

    def collect_cash(self) -> dict[Coin, int]:
        self._require_maintenance()
        out = {c: n for c, n in self._cash.items() if n}
        self._cash = Counter()
        return out

    # -- queries -------------------------------------------------------------------
    @property
    def balance(self) -> int:
        return sum(self._session)

    @property
    def state_name(self) -> str:
        return self._state.name

    def quantity(self, code: str) -> int:
        return self._slots[code][1] if code in self._slots else 0

    def cash_total(self) -> int:
        return _total(self._cash)

    def _require_maintenance(self) -> None:
        if self._state is not MAINTENANCE:
            raise InvalidOperation("operator actions need maintenance mode")


# ===================================================================== TESTS ==
def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc: type[BaseException], fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


COLA = Product("A1", "Cola", 125)
CHIPS = Product("B2", "Chips", 70)
GUM = Product("C3", "Gum", 75)


def _machine(cash=None, maker=None, stock=((COLA, 5), (CHIPS, 1), (GUM, 3))) -> VendingMachine:
    m = VendingMachine(cash, maker)
    m.enter_maintenance()
    for product, qty in stock:
        m.restock(product, qty)
    m.exit_maintenance()
    return m


def run_tests() -> bool:
    all_ok = True
    print("--- happy path ---")
    m = _machine({Coin.QUARTER: 4, Coin.DIME: 5, Coin.NICKEL: 5})
    m.insert(Coin.DOLLAR)
    all_ok &= _check("state moves idle -> has_money", m.state_name == "has_money" and m.balance == 100)
    m.insert(Coin.DOLLAR)
    vend = m.select("A1")
    all_ok &= _check("200 for a 125 cola -> 75 change in fewest coins (3 quarters)",
                     vend.product == COLA and vend.change == {Coin.QUARTER: 3})
    all_ok &= _check("back to idle, stock 4, cash box +200 -75",
                     m.state_name == "idle" and m.quantity("A1") == 4 and m.cash_total() == 175 + 125)
    exact = (m.insert(Coin.QUARTER), m.insert(Coin.QUARTER), m.insert(Coin.QUARTER), m.select("C3"))[-1]
    all_ok &= _check("exact payment -> empty change", exact.change == {})

    print("\n--- failures keep the session intact ---")
    m = _machine({Coin.DIME: 10})
    m.insert(Coin.QUARTER)
    all_ok &= _check("insufficient funds", _raises(InsufficientFunds, lambda: m.select("A1")))
    all_ok &= _check("unknown product", _raises(UnknownProduct, lambda: m.select("Z9")))
    all_ok &= _check("balance and state unchanged", m.balance == 25 and m.state_name == "has_money")
    m.insert(Coin.DOLLAR)
    m.select("B2")                                   # buys the only chips
    m.insert(Coin.DOLLAR)
    all_ok &= _check("sold out", _raises(SoldOut, lambda: m.select("B2")))
    all_ok &= _check("cancel returns exactly the inserted coins", m.cancel() == {Coin.DOLLAR: 1})
    all_ok &= _check("cancel with nothing inserted -> {}", m.cancel() == {} and m.state_name == "idle")
    all_ok &= _check("select with no money -> InsufficientFunds", _raises(InsufficientFunds, lambda: m.select("A1")))

    print("\n--- change-making ---")
    empty = _machine()
    empty.insert(Coin.DOLLAR)
    all_ok &= _check("empty cash box, dollar for 75 gum -> CannotMakeChange",
                     _raises(CannotMakeChange, lambda: empty.select("C3")))
    all_ok &= _check("...and the dollar is still refundable", empty.cancel() == {Coin.DOLLAR: 1})
    for _ in range(4):
        empty.insert(Coin.QUARTER)
    all_ok &= _check("4 quarters for 75 gum in an empty machine -> one of YOUR quarters back",
                     empty.select("C3").change == {Coin.QUARTER: 1})
    tricky = {Coin.QUARTER: 1, Coin.DIME: 3}
    g = _machine(dict(tricky), GreedyChange())
    b = _machine(dict(tricky), BoundedChange())
    for mm in (g, b):
        mm.insert(Coin.DOLLAR)
    all_ok &= _check("greedy: 30 change from {25x1, 10x3} fails (takes the quarter first)",
                     _raises(CannotMakeChange, lambda: g.select("B2")))
    all_ok &= _check("bounded: 30 change = three dimes", b.select("B2").change == {Coin.DIME: 3})

    print("\n--- maintenance ---")
    m = _machine()
    all_ok &= _check("restock outside maintenance refused",
                     _raises(InvalidOperation, lambda: m.restock(COLA, 1)))
    m.insert(Coin.DIME)
    all_ok &= _check("cannot enter maintenance with money inserted",
                     _raises(InvalidOperation, m.enter_maintenance))
    m.cancel()
    m.enter_maintenance()
    all_ok &= _check("no coins accepted in maintenance",
                     _raises(InvalidOperation, lambda: m.insert(Coin.DIME)))
    m.add_cash({Coin.NICKEL: 2})
    all_ok &= _check("collect_cash empties the box", m.collect_cash() == {Coin.NICKEL: 2} and m.cash_total() == 0)
    all_ok &= _check("fake coin rejected", _raises(InvalidOperation, lambda: VendingMachine().insert(3)))
    return all_ok
# ================================================================= END TESTS ==


def _brute_min_coins(amount: int, available: dict[Coin, int]) -> int | None:
    coins = [c for c in Coin if available.get(c)]
    best = None
    for counts in itertools.product(*(range(available[c] + 1) for c in coins)):
        if sum(c * k for c, k in zip(coins, counts)) == amount:
            n = sum(counts)
            best = n if best is None or n < best else best
    return best


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 20,000 random operations never create or destroy money ---")
    rng = random.Random(3)
    m = _machine({Coin.QUARTER: 3, Coin.DIME: 3, Coin.NICKEL: 2},
                 stock=((COLA, 5000), (CHIPS, 5000), (GUM, 5000)))
    initial, inserted, returned, revenue = m.cash_total(), 0, 0, 0
    counts = Counter()
    violations = 0
    for _ in range(20_000):
        op = rng.random()
        try:
            if op < 0.6:
                coin = rng.choice(list(Coin))
                m.insert(coin)
                inserted += coin
            elif op < 0.9:
                v = m.select(rng.choice(["A1", "B2", "C3"]))
                returned += _total(v.change)
                revenue += v.product.price_cents
                counts["sale"] += 1
            else:
                returned += _total(m.cancel())
        except VendingError as e:
            counts[type(e).__name__] += 1
        if m.cash_total() + m.balance + returned != initial + inserted:
            violations += 1
    print(f"      outcomes: {dict(counts)}")
    all_ok &= _check("cash box + session + returned == initial + inserted after every op",
                     violations == 0)
    all_ok &= _check(f"revenue {revenue} cents == net cash gained by the machine",
                     m.cash_total() - initial == revenue)

    print("\n--- DEMO 2: greedy vs bounded change-making on random limited cash boxes ---")
    rng = random.Random(11)
    greedy, bounded = GreedyChange(), BoundedChange()
    trials, greedy_refused, not_optimal = 3000, 0, 0
    for _ in range(trials):
        box = {c: rng.randint(0, 3) for c in Coin if c != Coin.DOLLAR}
        amount = rng.randrange(5, 100, 5)
        gb, bb = greedy.make(amount, box), bounded.make(amount, box)
        truth = _brute_min_coins(amount, box)
        if (bb is None) != (truth is None) or (bb is not None and sum(bb.values()) != truth):
            not_optimal += 1
        if gb is None and bb is not None:
            greedy_refused += 1
    print(f"      {trials} random (amount, cash box) cases: greedy refused {greedy_refused} "
          f"sales that bounded change made ({100 * greedy_refused / trials:.1f}%)")
    all_ok &= _check("bounded change matches brute force on every case", not_optimal == 0)
    all_ok &= _check("greedy loses real sales", greedy_refused > 0)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
