"""
================================================================================
LLD 013 · Stock Exchange Order Book / Matching Engine              [Tier 2]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement the limit order book and matching engine for one
instrument on an exchange.

Asked at trading firms, Bloomberg, Coinbase/Robinhood and sometimes at Google
as a "stateful system" coding round. These are the agreed requirements.

REQUIREMENTS
------------
  1. Prices are positive integer ticks; quantities positive integers.
  2. Order(id, trader, side, qty, price=None, type=LIMIT, tif=GTC). The engine
     sets order.remaining, order.seq and order.status.
  3. submit(order) -> [Trade(buy_id, sell_id, price, qty, aggressor)]
       * PRICE-TIME PRIORITY: an incoming order matches the opposite side while
         prices cross — best price first; within a price, earliest first.
       * Trades execute at the RESTING order's price.
       * After matching, the unfilled remainder:
            LIMIT + GTC -> rests on the book
            IOC         -> cancelled
            FOK         -> the order trades only if its WHOLE quantity can fill
                           immediately; otherwise nothing trades and it's
                           cancelled with the book untouched
            MARKET      -> never rests (MARKET must be IOC or FOK)
       * Status: FILLED if nothing remains; resting orders are NEW (no trades)
         or PARTIALLY_FILLED; otherwise CANCELLED.
       * REJECTED (no trades) for qty <= 0, a LIMIT without a positive price,
         or a MARKET order with a price or with GTC.
  4. cancel(order_id) -> True if a resting order was cancelled; False for
     unknown, filled, or already-cancelled orders. Must be O(1) — no removing
     from the middle of a list.
  5. best_bid(), best_ask() -> price or None.
     depth(n=5) -> {"bids": [(price, total_qty), ...], "asks": [...]}, best
     first, only levels with quantity.
     order(order_id) -> the Order.
  6. subscribe(listener): listener(trade) for every trade.

  Out of scope: several instruments, self-trade prevention, stop/iceberg orders.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * The data structure for each side (and why not a sorted list).
  * How cancel stays O(1).
  * Which price a trade executes at.
  * FOK without rollback.
  * Why real matching engines are single-threaded per instrument.

FOLLOW-UPS TO PREPARE
---------------------
  self-trade prevention · stop orders · iceberg orders · modify order ·
  many instruments · crash recovery by replaying the order log · market data feeds.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Side(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(Enum):
    LIMIT = "limit"
    MARKET = "market"


class TimeInForce(Enum):
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


class Status(Enum):
    NEW = "new"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass(slots=True, eq=False)
class Order:
    id: str
    trader: str
    side: Side
    qty: int
    price: int | None = None
    type: OrderType = OrderType.LIMIT
    tif: TimeInForce = TimeInForce.GTC
    remaining: int = 0
    seq: int = 0
    status: Status = Status.NEW


@dataclass(frozen=True, slots=True)
class Trade:
    buy_id: str
    sell_id: str
    price: int
    qty: int
    aggressor: Side


class MatchingEngine:
    def __init__(self) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def subscribe(self, listener: Callable[[Trade], None]) -> None: raise NotImplementedError
    def submit(self, order: Order) -> list[Trade]: raise NotImplementedError
    def cancel(self, order_id: str) -> bool: raise NotImplementedError
    def best_bid(self) -> int | None: raise NotImplementedError
    def best_ask(self) -> int | None: raise NotImplementedError
    def depth(self, n: int = 5) -> dict[str, list[tuple[int, int]]]: raise NotImplementedError
    def order(self, order_id: str) -> Order: raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _buy(oid, qty, price=None, **kw) -> Order:
    return Order(oid, "t", Side.BUY, qty, price, OrderType.LIMIT if price else OrderType.MARKET, **kw)


def _sell(oid, qty, price=None, **kw) -> Order:
    return Order(oid, "t", Side.SELL, qty, price, OrderType.LIMIT if price else OrderType.MARKET, **kw)


def _t(trades) -> list[tuple]:
    return [(t.buy_id, t.sell_id, t.price, t.qty) for t in trades]


def run_tests() -> bool:
    all_ok = True
    print("--- the matching trace ---")
    e = MatchingEngine()
    e.submit(_sell("s1", 5, 101))
    e.submit(_sell("s2", 5, 101))
    e.submit(_sell("s3", 10, 102))
    trades = e.submit(_buy("b1", 12, 102))
    all_ok &= _check("sweeps 101 in time order, then 102, at maker prices",
                     _t(trades) == [("b1", "s1", 101, 5), ("b1", "s2", 101, 5), ("b1", "s3", 102, 2)])
    all_ok &= _check("statuses: b1 FILLED, s2 FILLED, s3 PARTIALLY_FILLED with 8 left",
                     e.order("b1").status is Status.FILLED and e.order("s2").status is Status.FILLED
                     and e.order("s3").status is Status.PARTIALLY_FILLED and e.order("s3").remaining == 8)
    e.submit(_buy("b2", 3, 100))
    all_ok &= _check("non-crossing order rests; book not crossed",
                     (e.best_bid(), e.best_ask()) == (100, 102) and e.order("b2").status is Status.NEW)
    all_ok &= _check("depth aggregates levels, best first",
                     e.depth() == {"bids": [(100, 3)], "asks": [(102, 8)]})

    print("\n--- price priority beats time priority ---")
    e = MatchingEngine()
    e.submit(_buy("early_low", 5, 99))
    e.submit(_buy("late_high", 5, 100))
    all_ok &= _check("incoming sell hits the higher bid first even though it arrived later",
                     _t(e.submit(_sell("s", 5, 98))) == [("late_high", "s", 100, 5)])

    print("\n--- cancel ---")
    e = MatchingEngine()
    e.submit(_sell("a", 5, 101))
    e.submit(_sell("b", 5, 101))
    all_ok &= _check("cancel resting order -> True; twice -> False; unknown -> False",
                     e.cancel("a") and not e.cancel("a") and not e.cancel("zzz"))
    all_ok &= _check("cancelled order is skipped; b fills", _t(e.submit(_buy("x", 5, 101))) == [("x", "b", 101, 5)])
    all_ok &= _check("filled order can't be cancelled; empty level disappears",
                     not e.cancel("b") and e.best_ask() is None)
    e.submit(_sell("c", 10, 105))
    e.submit(_buy("y", 4, 105))
    e.cancel("c")
    all_ok &= _check("cancel after partial fill keeps the trade, removes the rest",
                     e.order("c").status is Status.CANCELLED and e.best_ask() is None)

    print("\n--- time in force and market orders ---")
    e = MatchingEngine()
    e.submit(_sell("s1", 5, 101))
    e.submit(_sell("s2", 5, 103))
    ioc = _buy("ioc", 8, 102, tif=TimeInForce.IOC)
    all_ok &= _check("IOC fills what crosses (5 @101) and cancels the rest",
                     _t(e.submit(ioc)) == [("ioc", "s1", 101, 5)] and ioc.status is Status.CANCELLED
                     and e.best_bid() is None)
    fok = _buy("fok", 6, 103, tif=TimeInForce.FOK)
    all_ok &= _check("FOK for 6 with only 5 available -> nothing trades, book untouched",
                     e.submit(fok) == [] and fok.status is Status.CANCELLED and e.depth()["asks"] == [(103, 5)])
    fok2 = _buy("fok2", 5, 103, tif=TimeInForce.FOK)
    all_ok &= _check("FOK for exactly the available 5 -> fills", len(e.submit(fok2)) == 1 and fok2.status is Status.FILLED)
    e.submit(_buy("b1", 2, 90))
    e.submit(_buy("b2", 2, 80))
    mkt = _sell("m", 10, tif=TimeInForce.IOC)
    all_ok &= _check("MARKET sell sweeps every bid level, remainder cancelled",
                     _t(e.submit(mkt)) == [("b1", "m", 90, 2), ("b2", "m", 80, 2)] and mkt.status is Status.CANCELLED)

    print("\n--- validation and observers ---")
    e = MatchingEngine()
    seen = []
    e.subscribe(seen.append)
    bad = [_buy("q0", 0, 100), _buy("p0", 5, 0), Order("mg", "t", Side.BUY, 5, None, OrderType.MARKET, TimeInForce.GTC)]
    all_ok &= _check("zero qty, zero price, GTC market -> REJECTED",
                     all(e.submit(o) == [] and o.status is Status.REJECTED for o in bad))
    e.submit(_sell("s", 1, 50))
    e.submit(_buy("b", 1, 60))
    all_ok &= _check("trade feed observer notified with the maker price", [(t.price, t.aggressor) for t in seen] == [(50, Side.BUY)])
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
