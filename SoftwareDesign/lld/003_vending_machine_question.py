"""
================================================================================
LLD 003 · Vending Machine                                          [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement a coin-operated vending machine.

The interviewer says: "Design a vending machine." Below are the requirements a
good candidate would agree in the first five minutes.

REQUIREMENTS
------------
  1. Coins: NICKEL 5, DIME 10, QUARTER 25, DOLLAR 100 (cents). Anything that is
     not a Coin is rejected with InvalidOperation.
  2. Products sit in slots by code, each with a price and a quantity.
  3. Customer operations:
        insert(coin)  -> balance in cents
        select(code)  -> Vend(product, change: {Coin: count})
        cancel()      -> {Coin: count}  exactly the coins inserted this session
  4. One product per session. After a sale the machine is idle again.
  5. A failed select changes NOTHING (stock, cash, balance, state) and raises:
        UnknownProduct, SoldOut, InsufficientFunds, CannotMakeChange.
     select() with no money inserted raises InsufficientFunds.
  6. Change must be made from coins the machine really has — including the
     coins inserted for this sale. The machine holds a LIMITED number of
     each coin. Give change in the fewest coins possible.
  7. Two pluggable change makers:
        GreedyChange   largest coin first
        BoundedChange  correct fewest-coins with limited stock (default)
     make(amount, available: {Coin: count}) -> {Coin: count} or None
  8. Operator actions — only in maintenance mode, else InvalidOperation:
        restock(product, qty) · add_cash(coins) · collect_cash() -> coins
     enter_maintenance() is refused while a customer has money inserted.
     No coins accepted while in maintenance.
  9. state_name is "idle", "has_money" or "maintenance".

  Out of scope: cards, displays, multi-item baskets.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * States: which operations are legal in each? Where does that knowledge live?
  * How do you guarantee a failed purchase changes nothing?
  * Why keep the customer's coins separate from the cash box?
  * Is greedy change-making correct with a limited number of coins?

FOLLOW-UPS TO PREPARE
---------------------
  card payments · multi-item basket · "exact change only" light ·
  dispense motor failure after payment · telemetry · audit log.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum


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


class GreedyChange:
    def make(self, amount: int, available: dict[Coin, int]) -> dict[Coin, int] | None:
        raise NotImplementedError


class BoundedChange:
    def make(self, amount: int, available: dict[Coin, int]) -> dict[Coin, int] | None:
        raise NotImplementedError


class VendingMachine:
    def __init__(self, cash: dict[Coin, int] | None = None, change_maker=None) -> None:
        # YOUR CODE HERE (consider State objects)
        raise NotImplementedError

    def insert(self, coin: Coin) -> int:
        raise NotImplementedError

    def select(self, code: str) -> Vend:
        raise NotImplementedError

    def cancel(self) -> dict[Coin, int]:
        raise NotImplementedError

    def enter_maintenance(self) -> None:
        raise NotImplementedError

    def exit_maintenance(self) -> None:
        raise NotImplementedError

    def restock(self, product: Product, qty: int) -> None:
        raise NotImplementedError

    def add_cash(self, coins: dict[Coin, int]) -> None:
        raise NotImplementedError

    def collect_cash(self) -> dict[Coin, int]:
        raise NotImplementedError

    @property
    def balance(self) -> int:
        raise NotImplementedError

    @property
    def state_name(self) -> str:
        raise NotImplementedError

    def quantity(self, code: str) -> int:
        raise NotImplementedError

    def cash_total(self) -> int:
        """Cents in the cash box (not counting the current session's coins)."""
        raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
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


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
